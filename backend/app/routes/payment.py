"""
Payment Routes - PayOS integration endpoints
"""
from flask import Blueprint, request, jsonify
from pydantic import ValidationError
from decimal import Decimal, InvalidOperation
import hashlib
import json
import time
from services.payos_service import (
    create_payment_link, 
    get_payment_status, 
    cancel_payment,
    verify_webhook_signature
)
from app.schemas.payment import (
    PaymentCreate,
    WebhookPayload
)
from app.websocket import emit_payment_success, emit_payment_cancelled, emit_admin_order_new
from app.utils.mqtt import send_dispense_command
from app.utils.machine_auth import multi_auth_required
import os

def debug_log(msg):
    log_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'debug_payment.log')
    try:
        with open(log_path, 'a', encoding='utf-8') as f:
            f.write(msg + '\n')
    except:
        pass

payment_bp = Blueprint('payment', __name__)


PAID_STATUSES = {'PAID', 'SUCCESS', 'COMPLETED'}


def _parse_order_id(order_code: int) -> int:
    return order_code // 10000 if order_code > 10000 else order_code


def _normalize_amount(value):
    if value is None:
        return None

    try:
        return Decimal(str(value)).quantize(Decimal('1'))
    except (InvalidOperation, ValueError, TypeError):
        return None


def _settle_paid_order(real_order_id: int, payment_code: int, amount=None, transactions=None, source='payment'):
    """
    Settle a paid order once. This path is shared by webhook, polling and manual sync
    so stock deduction and transaction creation stay idempotent.
    """
    from app import db
    from app.models import Order, Slot, Transaction, Product

    transactions = transactions or []
    locked_order = Order.query.filter_by(order_id=real_order_id).with_for_update().first()
    if not locked_order:
        db.session.rollback()
        return {
            'ok': False,
            'http_status': 404,
            'message': f'Không tìm thấy đơn hàng #{real_order_id}'
        }

    if locked_order.status_payment == 'completed':
        return {
            'ok': True,
            'settled': False,
            'message': f'Đơn hàng #{real_order_id} đã được thanh toán trước đó',
            'order': locked_order
        }

    if locked_order.status_payment == 'cancelled':
        db.session.rollback()
        return {
            'ok': False,
            'http_status': 409,
            'message': f'Đơn hàng #{real_order_id} đã bị hủy trước khi đồng bộ thanh toán'
        }

    locked_order.status_payment = 'completed'
    locked_order.status_slots = 'pending'

    qty = getattr(locked_order, 'quantity', 1)
    slot = None
    if locked_order.slot_id:
        slot = Slot.query.filter_by(slot_id=locked_order.slot_id).with_for_update().first()
    else:
        # Tự động tìm Slot phù hợp TRÊN CÙNG MÁY của đơn hàng
        slot = Slot.query.filter(
            Slot.machine_id == locked_order.machine_id,
            Slot.product_id == locked_order.product_id,
            Slot.stock >= qty
        ).with_for_update().first()
        if not slot:
            db.session.rollback()
            return {
                'ok': False,
                'http_status': 409,
                'message': f'Không có khay đủ tồn kho cho đơn hàng #{real_order_id}'
            }
        locked_order.slot_id = slot.slot_id

    if not slot:
        db.session.rollback()
        return {
            'ok': False,
            'http_status': 409,
            'message': f'Không tìm thấy khay hàng cho đơn hàng #{real_order_id}'
        }

    if slot.stock < qty:
        db.session.rollback()
        return {
            'ok': False,
            'http_status': 409,
            'message': (
                f'Tồn kho không đủ cho đơn hàng #{real_order_id}: '
                f'cần {qty}, hiện còn {slot.stock}'
            )
        }

    old_stock = slot.stock
    slot.stock -= qty
    print(f"📦 Stock reduced for slot {slot.slot_id}: {old_stock} -> {slot.stock}")

    if slot.stock == 0:
        product = Product.query.filter_by(product_id=slot.product_id).with_for_update().first()
        if product and product.stock == 0:
            product.active = False
            debug_log(f"{source.upper()}: Product {product.product_id} deactivated")
            print(f"⚠️ Product '{product.product_name}' marked as INACTIVE (total stock=0)")

    existing_transaction = Transaction.query.filter_by(order_id=real_order_id).first()
    if not existing_transaction:
        reference = None
        if transactions and isinstance(transactions, list):
            for transaction_data in transactions:
                if isinstance(transaction_data, dict) and transaction_data.get('reference'):
                    reference = transaction_data.get('reference')
                    break

        transaction_amount = _normalize_amount(amount) or _normalize_amount(locked_order.price_snapshot)
        transaction = Transaction(
            order_id=locked_order.order_id,
            amount=float(transaction_amount),
            bank_trans_id=reference,
            description=f"Thanh toán đơn hàng #{locked_order.order_id} (payment: {payment_code})",
            status='success'
        )
        db.session.add(transaction)
        print(f"💳 Transaction created for order #{locked_order.order_id}")
    else:
        print(f"ℹ️ Transaction already exists for order #{locked_order.order_id}")

    db.session.commit()

    try:
        send_dispense_command(slot.machine_id, slot.slot_code)
    except Exception as exc:
        debug_log(
            f"{source.upper()}: Failed to send dispense command for order {real_order_id}, "
            f"slot {slot.slot_code}: {exc}"
        )

    try:
        emit_payment_success(real_order_id, {
            'amount': float(_normalize_amount(amount) or _normalize_amount(locked_order.price_snapshot)),
            'payment_code': payment_code,
            'synced': source != 'webhook'
        })
    except Exception as exc:
        debug_log(f"{source.upper()}: Failed to emit payment success for order {real_order_id}: {exc}")

    try:
        emit_admin_order_new({
            'order_id': real_order_id,
            'machine_id': slot.machine_id,
            'amount': float(_normalize_amount(amount) or _normalize_amount(locked_order.price_snapshot)),
            'status': 'completed',
            'timestamp': datetime.utcnow().isoformat()
        })
    except Exception as exc:
        pass

    return {
        'ok': True,
        'settled': True,
        'message': f'Đơn hàng #{real_order_id} đã được ghi nhận thanh toán thành công',
        'order': locked_order
    }


def _is_paid_result(result: dict) -> bool:
    payos_status = str(result.get('status', '')).upper()
    amount = result.get('amount', 0)
    amount_paid = result.get('amount_paid', 0) or 0
    amount_remaining = result.get('amount_remaining', amount)
    if amount_remaining is None:
        amount_remaining = amount

    is_paid_by_status = payos_status in PAID_STATUSES
    is_paid_by_amount = amount_paid > 0 and amount_remaining == 0
    is_paid_by_transactions = False

    transactions = result.get('transactions', [])
    if transactions and isinstance(transactions, list):
        for trans in transactions:
            if isinstance(trans, dict) and str(trans.get('status', '')).upper() in PAID_STATUSES:
                is_paid_by_transactions = True
                break

    print(f"🔍 Payment check - Status: {payos_status}, Amount paid: {amount_paid}, Remaining: {amount_remaining}")
    print(f"🔍 Payment check - By status: {is_paid_by_status}, By amount: {is_paid_by_amount}, By transactions: {is_paid_by_transactions}")
    print(f"✅ Is paid: {is_paid_by_status or is_paid_by_amount or is_paid_by_transactions}")

    return is_paid_by_status or is_paid_by_amount or is_paid_by_transactions


def _cancel_order_in_db(order_code: int):
    from app import db
    from app.models import Order

    real_order_id = _parse_order_id(order_code)
    order = Order.query.filter_by(order_id=real_order_id).with_for_update().first()
    if not order:
        return {
            'ok': False,
            'http_status': 404,
            'message': f'Không tìm thấy đơn hàng #{real_order_id}'
        }

    if order.status_payment == 'completed':
        return {
            'ok': False,
            'http_status': 409,
            'message': f'Đơn hàng #{real_order_id} đã hoàn tất thanh toán'
        }

    if order.status_payment == 'cancelled':
        return {
            'ok': True,
            'cancelled': False,
            'message': f'Đơn hàng #{real_order_id} đã được hủy trước đó',
            'order': order
        }

    order.status_payment = 'cancelled'
    order.status_slots = 'cancelled'
    db.session.commit()
    
    emit_payment_cancelled(real_order_id)
    try:
        emit_admin_order_new({
            'order_id': real_order_id,
            'machine_id': order.slot.machine_id if order.slot else None,
            'status': 'cancelled',
            'timestamp': datetime.utcnow().isoformat()
        })
    except Exception as exc:
        pass
        
    print(f"✅ Order #{real_order_id} marked as cancelled in DB")

    return {
        'ok': True,
        'cancelled': True,
        'message': f'Đơn hàng #{real_order_id} đã được hủy',
        'order': order
    }


def _record_payment_callback(payload: dict, signature_ok: bool, order_id=None, bank_trans_id=None):
    from app import db
    from app.models import PaymentCallback

    payload_raw = payload or {}
    payload_hash = hashlib.sha256(
        json.dumps(payload_raw, sort_keys=True, separators=(',', ':'), ensure_ascii=False).encode('utf-8')
    ).hexdigest()

    existing = PaymentCallback.query.filter_by(payload_hash=payload_hash).first()
    if existing:
        return {
            'duplicate': True,
            'callback': existing,
            'payload_hash': payload_hash
        }

    callback = PaymentCallback(
        callback_id=time.time_ns(),
        bank_trans_id=bank_trans_id,
        order_id=order_id,
        payload_raw=payload_raw,
        payload_hash=payload_hash,
        signature_ok=signature_ok,
        ip_source=request.remote_addr
    )
    db.session.add(callback)
    db.session.commit()

    return {
        'duplicate': False,
        'callback': callback,
        'payload_hash': payload_hash
    }


@payment_bp.route('/payment/create', methods=['POST'])
@multi_auth_required
def create_payment(current_auth):
    """
    Create a PayOS payment link.
    """
    try:
        print("💳 POST /api/payment/create received")
        json_data = request.get_json(force=True, silent=True)
        print(f"📦 Data: {json_data}")
        if not json_data:
            return jsonify({
                'success': False,
                'message': 'Body request phải là JSON hợp lệ'
            }), 400
        
        data = PaymentCreate(**json_data)

        from app.models import Order

        order = Order.query.get(data.order_code)
        if not order:
            return jsonify({
                'success': False,
                'message': f'Không tìm thấy đơn hàng #{data.order_code}'
            }), 404

        if order.status_payment != 'pending':
            return jsonify({
                'success': False,
                'message': f'Đơn hàng #{data.order_code} không ở trạng thái chờ thanh toán'
            }), 409

        expected_amount = _normalize_amount(order.price_snapshot)
        requested_amount = _normalize_amount(data.amount)
        if expected_amount is None or requested_amount is None:
            return jsonify({
                'success': False,
                'message': 'Số tiền thanh toán không hợp lệ'
            }), 400

        if requested_amount != expected_amount:
            return jsonify({
                'success': False,
                'message': (
                    f'Số tiền thanh toán không khớp với đơn hàng #{data.order_code}. '
                    f'Mong đợi {int(expected_amount)}, nhận được {int(requested_amount)}'
                )
            }), 400
        
        # Convert items to dict format for PayOS (ensure price is int)
        items = []
        items_total = 0
        for item in data.items:
            line_price = int(item.price)
            items_total += line_price * int(item.quantity)
            items.append({
                'name': item.name,
                'quantity': item.quantity,
                'price': line_price  # PayOS requires int
            })

        if items and items_total != int(expected_amount):
            return jsonify({
                'success': False,
                'message': (
                    f'Tổng tiền sản phẩm không khớp với đơn hàng #{data.order_code}. '
                    f'Mong đợi {int(expected_amount)}, nhận được {items_total}'
                )
            }), 400
        
        result = create_payment_link(
            order_code=data.order_code,
            amount=int(expected_amount),  # PayOS requires int
            description=data.description,
            items=items,
            buyer_name=data.buyer_name,
            buyer_email=data.buyer_email,
            buyer_phone=data.buyer_phone,
            buyer_address=data.buyer_address
        )
        
        if result.get('success'):
            return jsonify({
                'success': True,
                'message': 'Tạo liên kết thanh toán thành công',
                'data': {
                    'checkout_url': result.get('checkout_url'),
                    'qr_code': result.get('qr_code'),
                    'order_code': data.order_code,
                    'payment_code': result.get('payment_code')  # Unique code cho PayOS
                }
            }), 201
        else:
            return jsonify({
                'success': False,
                'message': result.get('error', 'Không thể tạo liên kết thanh toán')
            }), 400
            
    except ValidationError as e:
        print(f"❌ Validation error: {e.errors()}")
        print(f"📦 Received data was: {json_data}")
        return jsonify({
            'success': False,
            'message': 'Dữ liệu gửi lên không hợp lệ',
            'errors': e.errors()
        }), 422
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Lỗi máy chủ: {str(e)}'
        }), 500


@payment_bp.route('/payment/webhook', methods=['POST'])
def payment_webhook():
    """
    Handle PayOS webhook callback.
    
    PayOS sẽ gửi thông báo khi có thanh toán thành công.
    """
    try:
        json_data = request.get_json(force=True, silent=True)
        if not json_data:
            return jsonify({'success': False, 'message': 'Payload webhook không hợp lệ'}), 400
        
        print(f"📥 Webhook received: {json_data}")
        
        # Verify webhook signature (optional but recommended)
        signature = json_data.get('signature')
        signature_ok = True
        if signature:
            signature_ok = verify_webhook_signature(json_data, signature)
            if not signature_ok:
                callback_log = _record_payment_callback(
                    payload=json_data,
                    signature_ok=False
                )
                if callback_log.get('duplicate'):
                    return jsonify({
                        'success': False,
                        'message': 'Chữ ký webhook không hợp lệ cho payload bị gửi lặp'
                    }), 401

                print("⚠️ Invalid webhook signature")
                return jsonify({'success': False, 'message': 'Chữ ký webhook không hợp lệ'}), 401
        
        # Parse webhook data
        webhook = WebhookPayload(**json_data)
        
        if webhook.success and webhook.data:
            payment_code = webhook.data.orderCode  # Đây là payment_code unique (VD: 31234)
            amount = webhook.data.amount
            
            # Parse order_id gốc từ payment_code
            # Format: payment_code = order_id * 10000 + suffix
            # Nên: order_id = payment_code // 10000
            order_id = payment_code // 10000
            callback_log = _record_payment_callback(
                payload=json_data,
                signature_ok=signature_ok,
                order_id=order_id,
                bank_trans_id=getattr(webhook.data, 'reference', None)
            )
            if callback_log.get('duplicate'):
                print(f"ℹ️ Duplicate webhook ignored for payment_code={payment_code}")
                return jsonify({
                    'success': True,
                    'message': 'Webhook này đã được xử lý trước đó'
                }), 200
            
            print(f"✅ Payment successful: payment_code={payment_code}, order_id={order_id}, amount={amount}")
            settlement = _settle_paid_order(
                real_order_id=order_id,
                payment_code=payment_code,
                amount=amount,
                transactions=[{
                    'reference': getattr(webhook.data, 'reference', None),
                    'status': 'SUCCESS'
                }],
                source='webhook'
            )
            if not settlement.get('ok'):
                return jsonify({
                    'success': False,
                    'message': settlement['message']
                }), settlement.get('http_status', 400)
            
            return jsonify({
                'success': True,
                'message': 'Đã xử lý webhook thành công'
            }), 200
        else:
            _record_payment_callback(
                payload=json_data,
                signature_ok=signature_ok
            )
            print(f"❌ Payment failed or pending: {webhook.desc}")
            return jsonify({
                'success': True,
                'message': 'Đã nhận webhook, thanh toán chưa hoàn tất'
            }), 200
            
    except Exception as e:
        print(f"❌ Webhook error: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'Lỗi xử lý webhook: {str(e)}'
        }), 500


@payment_bp.route('/payment/status/<int:order_code>', methods=['GET'])
@multi_auth_required
def check_payment_status(current_auth, order_code):
    """
    Check payment status by order code and sync to database if paid.
    """
    try:
        result = get_payment_status(order_code)
        
        if result.get('success'):
            # Log chi tiết để debug
            print(f"🔍 Checking payment status for order #{order_code}")
            print(f"📊 PayOS response: {result}")
            is_paid = _is_paid_result(result)
            
            # Nếu PayOS báo đã thanh toán, sync về database
            if is_paid:
                real_order_id = _parse_order_id(order_code)
                settlement = _settle_paid_order(
                    real_order_id=real_order_id,
                    payment_code=order_code,
                    amount=result.get('amount_paid') or result.get('amount'),
                    transactions=result.get('transactions', []),
                    source='poll'
                )
                if not settlement.get('ok'):
                    return jsonify({
                        'success': False,
                        'message': settlement['message'],
                        'data': result
                    }), settlement.get('http_status', 400)
            
            return jsonify({
                'success': True,
                'message': 'Đã lấy trạng thái và đồng bộ thanh toán thành công' if is_paid else 'Đã lấy trạng thái thanh toán',
                'data': result
            }), 200
        else:
            return jsonify({
                'success': False,
                'message': result.get('error', 'Không thể lấy trạng thái thanh toán')
            }), 400
            
    except Exception as e:
        import traceback
        print(f"❌ Error checking payment status: {str(e)}")
        traceback.print_exc()
        return jsonify({
            'success': False,
            'message': f'Lỗi máy chủ: {str(e)}'
        }), 500


@payment_bp.route('/payment/sync/<int:order_code>', methods=['POST'])
@multi_auth_required
def sync_payment_status(current_auth, order_code):
    """
    Manually sync payment status from PayOS to database.
    Useful for debugging or when webhook fails.
    """
    try:
        from app.models import Order
        
        # Kiểm tra order có tồn tại không
        # Attempt to find order. Logic fix: if order_code is large (payment_code), parse it.
        real_order_id = _parse_order_id(order_code)
        order = Order.query.get(real_order_id)
            
        if not order:
            return jsonify({
                'success': False,
                'message': f'Không tìm thấy đơn hàng #{real_order_id}'
            }), 404
        
        # Lấy status từ PayOS
        result = get_payment_status(order_code)
        
        if not result.get('success'):
            return jsonify({
                'success': False,
                'message': result.get('error', 'Không thể lấy trạng thái thanh toán từ PayOS')
            }), 400
        
        # Kiểm tra trạng thái thanh toán
        payos_status = result.get('status', '').upper()
        amount_paid = result.get('amount_paid', 0) or 0
        amount_remaining = result.get('amount_remaining', result.get('amount'))
        is_paid = _is_paid_result(result)
        
        if not is_paid:
            return jsonify({
                'success': False,
                'message': (
                    f'Thanh toán chưa hoàn tất. Trạng thái PayOS: {payos_status}, '
                    f'đã thanh toán: {amount_paid}, còn lại: {amount_remaining}'
                ),
                'data': {
                    'payos_status': payos_status,
                    'amount_paid': amount_paid,
                    'amount_remaining': amount_remaining,
                    'order_status': order.status_payment
                }
            }), 400
        
        # Nếu đã thanh toán, sync về database
        if order.status_payment == 'pending':
            settlement = _settle_paid_order(
                real_order_id=real_order_id,
                payment_code=order_code,
                amount=result.get('amount_paid') or result.get('amount'),
                transactions=result.get('transactions', []),
                source='manual_sync'
            )
            if not settlement.get('ok'):
                return jsonify({
                    'success': False,
                    'message': settlement['message']
                }), settlement.get('http_status', 400)

            return jsonify({
                'success': True,
                'message': f'Đã đồng bộ thanh toán thành công cho đơn hàng #{order_code}',
                'data': {
                    'order_id': real_order_id,
                    'order_status': 'completed',
                    'payos_status': payos_status
                }
            }), 200
        else:
            return jsonify({
                'success': True,
                'message': f'Đơn hàng #{order_code} hiện có trạng thái: {order.status_payment}',
                'data': {
                    'order_id': order.order_id,
                    'order_status': order.status_payment,
                    'payos_status': payos_status
                }
            }), 200
            
    except Exception as e:
        import traceback
        print(f"❌ Error syncing payment: {str(e)}")
        traceback.print_exc()
        return jsonify({
            'success': False,
            'message': f'Lỗi đồng bộ thanh toán: {str(e)}'
        }), 500


@payment_bp.route('/payment/cancel/<int:order_code>', methods=['POST', 'PUT'])
@multi_auth_required
def cancel_payment_link(current_auth, order_code):
    """
    Cancel a pending payment by order code.
    """
    try:
        result = cancel_payment(order_code)
        
        if result.get('success'):
            cancelled = _cancel_order_in_db(order_code)
            if not cancelled.get('ok'):
                return jsonify({
                    'success': False,
                    'message': cancelled['message']
                }), cancelled.get('http_status', 400)

            return jsonify({
                'success': True,
                'message': cancelled['message'],
                'data': {
                    'order_code': order_code,
                    'order_id': _parse_order_id(order_code)
                }
            }), 200
        else:
            return jsonify({
                'success': False,
                'message': result.get('error', 'Không thể hủy thanh toán')
            }), 400
            
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Lỗi máy chủ: {str(e)}'
        }), 500


@payment_bp.route('/payment/success', methods=['GET'])
def payment_success_page():
    """
    Return URL after successful payment.
    """
    order_code = request.args.get('orderCode')
    real_order_id = _parse_order_id(int(order_code)) if order_code and order_code.isdigit() else None
    return jsonify({
        'success': True,
        'message': 'Thanh toán đã hoàn tất, đang chờ máy bán hàng xuất sản phẩm.',
        'order_code': order_code,
        'order_id': real_order_id
    })


@payment_bp.route('/payment/cancel', methods=['GET'])
def payment_cancel_page():
    """
    Cancel URL when user cancels payment.
    """
    order_code = request.args.get('orderCode')
    if not order_code or not order_code.isdigit():
        return jsonify({
            'success': False,
            'message': 'Đã hủy thanh toán nhưng thiếu hoặc sai mã đơn hàng',
            'order_code': order_code
        }), 400

    cancelled = _cancel_order_in_db(int(order_code))
    if not cancelled.get('ok'):
        return jsonify({
            'success': False,
            'message': cancelled['message'],
            'order_code': order_code
        }), cancelled.get('http_status', 400)

    return jsonify({
        'success': True,
        'message': cancelled['message'],
        'order_code': order_code,
        'order_id': _parse_order_id(int(order_code))
    }), 200

@payment_bp.route('/debug-db', methods=['GET'])
@multi_auth_required
def debug_db(current_auth):
    from app.models import Order, Slot
    orders = Order.query.order_by(Order.order_id.desc()).limit(5).all()
    slots = Slot.query.order_by(Slot.slot_id.asc()).limit(15).all()
    
    logs = ""
    log_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'debug_payment.log')
    if os.path.exists(log_path):
        with open(log_path, 'r', encoding='utf-8') as f:
            logs = f.read()
            
    return jsonify({
        "orders": [{
            "id": o.order_id,
            "product": o.product_id,
            "slot": o.slot_id,
            "qty": o.quantity,
            "pay": o.status_payment,
            "slots_status": o.status_slots
        } for o in orders],
        "slots": [{
            "id": s.slot_id,
            "code": s.slot_code,
            "product": s.product_id,
            "stock": s.stock,
            "capacity": s.capacity
        } for s in slots],
        "logs": logs
    })
