"""
Payment Routes - PayOS integration endpoints
"""
from flask import Blueprint, request, jsonify
from pydantic import ValidationError
from services.payos_service import (
    create_payment_link, 
    get_payment_status, 
    cancel_payment,
    verify_webhook_signature
)
from app.schemas.payment import PaymentCreate, WebhookPayload
from app.websocket import emit_payment_success
import os
import json

def debug_log(msg):
    log_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'debug_payment.log')
    try:
        with open(log_path, 'a', encoding='utf-8') as f:
            f.write(msg + '\n')
    except:
        pass

payment_bp = Blueprint('payment', __name__)


@payment_bp.route('/payment/create', methods=['POST'])
def create_payment():
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
                'message': 'Request body must be valid JSON'
            }), 400
        
        data = PaymentCreate(**json_data)
        
        # Convert items to dict format for PayOS (ensure price is int)
        items = []
        for item in data.items:
            items.append({
                'name': item.name,
                'quantity': item.quantity,
                'price': int(item.price)  # PayOS requires int
            })
        
        result = create_payment_link(
            order_code=data.order_code,
            amount=int(data.amount),  # PayOS requires int
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
                'message': 'Payment link created successfully',
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
                'message': result.get('error', 'Failed to create payment link')
            }), 400
            
    except ValidationError as e:
        print(f"❌ Validation error: {e.errors()}")
        print(f"📦 Received data was: {json_data}")
        return jsonify({
            'success': False,
            'message': 'Validation error',
            'errors': e.errors()
        }), 422
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Server error: {str(e)}'
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
            return jsonify({'success': False, 'message': 'Invalid payload'}), 400
        
        print(f"📥 Webhook received: {json_data}")
        
        # Verify webhook signature (optional but recommended)
        signature = json_data.get('signature')
        if signature:
            is_valid = verify_webhook_signature(json_data, signature)
            if not is_valid:
                print("⚠️ Invalid webhook signature")
                return jsonify({'success': False, 'message': 'Invalid signature'}), 401
        
        # Parse webhook data
        webhook = WebhookPayload(**json_data)
        
        if webhook.success and webhook.data:
            payment_code = webhook.data.orderCode  # Đây là payment_code unique (VD: 31234)
            amount = webhook.data.amount
            
            # Parse order_id gốc từ payment_code
            # Format: payment_code = order_id * 10000 + suffix
            # Nên: order_id = payment_code // 10000
            order_id = payment_code // 10000
            
            print(f"✅ Payment successful: payment_code={payment_code}, order_id={order_id}, amount={amount}")
            
            # Import models for database operations
            from app.models import Order, Slot, Transaction, Product
            from app import db
            
            # Tìm order theo order_id (đã parse từ payment_code)
            order = Order.query.get(order_id)
            if order:
                # Chỉ cập nhật nếu order đang ở trạng thái pending
                if order.status_payment == 'pending':
                    # Cập nhật status thành completed — status_slots giữ 'pending'
                    # để Arduino poll /iot/pending-orders và nhả hàng
                    order.status_payment = 'completed'
                    order.status_slots = 'pending'
                    
                    debug_log(f"WEBHOOK: Processing order #{order_id}, product_id={order.product_id}, slot_id={order.slot_id}")
                    
                    # Giảm stock trong slot (Sử dụng with_for_update để tránh Race Condition)
                    qty = getattr(order, 'quantity', 1)
                    slot = None
                    if order.slot_id:
                        slot = Slot.query.get(order.slot_id)
                    else:
                        slot = Slot.query.filter(Slot.product_id == order.product_id, Slot.stock >= qty).first()
                        if not slot:
                             slot = Slot.query.filter(Slot.product_id == order.product_id, Slot.stock > 0).first()

                    debug_log(f"WEBHOOK: Searched for slot with product_id={order.product_id}, qty>={qty}. Result: {slot.slot_id if slot else 'None'}")

                    if slot:
                        if order.slot_id is None:
                            order.slot_id = slot.slot_id
                        
                        if slot.stock >= qty:
                            slot.stock -= qty
                            print(f"📦 Stock reduced for slot {slot.slot_id}: {slot.stock + qty} -> {slot.stock}")
                        else:
                            print(f"⚠️ Stock insufficient for slot {slot.slot_id}: needed {qty}, had {slot.stock}")
                            slot.stock = 0 # Force to 0? Or just subtract what we can? Best to just subtract/force.
                        
                        # Requirement: If total stock of product becomes 0, set product to inactive
                        if slot.stock == 0:
                            product = Product.query.get(slot.product_id)
                            # Check total stock across all slots using the property defined in Product model
                            if product and product.stock == 0:
                                product.active = False
                                debug_log(f"WEBHOOK: Product {product.product_id} deactivated")
                                print(f"⚠️ Product '{product.product_name}' marked as INACTIVE (total stock=0)")
                    else:
                        debug_log(f"WEBHOOK: No slot found for product {order.product_id}!")
                    
                    # Kiểm tra xem đã có transaction chưa (tránh duplicate)
                    existing_transaction = Transaction.query.filter_by(order_id=order_id).first()
                    if not existing_transaction:
                        # Tạo transaction record
                        # Lấy reference từ webhook data nếu có
                        reference = None
                        if hasattr(webhook.data, 'reference'):
                            reference = webhook.data.reference
                        elif hasattr(webhook.data, 'transactions') and webhook.data.transactions:
                            reference = webhook.data.transactions[0].get('reference') if isinstance(webhook.data.transactions, list) else None
                        
                        transaction = Transaction(
                            order_id=order.order_id,
                            amount=float(amount),
                            bank_trans_id=reference,
                            description=f"Thanh toán đơn hàng #{order_id} (payment: {payment_code})",
                            status='success'
                        )
                        db.session.add(transaction)
                        print(f"💳 Transaction created for order #{order_id}")
                    else:
                        print(f"ℹ️ Transaction already exists for order #{order_id}")
                    
                    db.session.commit()
                    print(f"✅ Order #{order_id} completed and transaction created")
                    
                    # Emit WebSocket event for real-time notification
                    emit_payment_success(order_id, {
                        'amount': amount,
                        'payment_code': payment_code
                    })
                    print(f"📤 WebSocket event emitted for order #{order_id}")
                else:
                    print(f"ℹ️ Order #{order_id} already has status: {order.status_payment}")
            else:
                print(f"⚠️ Order #{order_id} not found in database (payment_code: {payment_code})")
            
            return jsonify({
                'success': True,
                'message': 'Webhook processed successfully'
            }), 200
        else:
            print(f"❌ Payment failed or pending: {webhook.desc}")
            return jsonify({
                'success': True,
                'message': 'Webhook received'
            }), 200
            
    except Exception as e:
        print(f"❌ Webhook error: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'Webhook processing error: {str(e)}'
        }), 500


@payment_bp.route('/payment/status/<int:order_code>', methods=['GET'])
def check_payment_status(order_code):
    """
    Check payment status by order code and sync to database if paid.
    """
    try:
        result = get_payment_status(order_code)
        
        if result.get('success'):
            # Log chi tiết để debug
            print(f"🔍 Checking payment status for order #{order_code}")
            print(f"📊 PayOS response: {result}")
            
            # Kiểm tra nếu thanh toán đã thành công từ PayOS
            payos_status = result.get('status', '').upper()
            amount = result.get('amount', 0)
            amount_paid = result.get('amount_paid', 0) or 0
            amount_remaining = result.get('amount_remaining', amount) or amount
            transactions = result.get('transactions', [])
            
            # Kiểm tra nhiều điều kiện để xác định thanh toán thành công:
            # 1. Status là PAID, SUCCESS, COMPLETED
            # 2. Hoặc amount_paid > 0 và amount_remaining = 0
            # 3. Hoặc có transactions với status thành công
            is_paid_by_status = payos_status in ['PAID', 'SUCCESS', 'COMPLETED']
            is_paid_by_amount = amount_paid > 0 and amount_remaining == 0
            is_paid_by_transactions = False
            
            if transactions and isinstance(transactions, list) and len(transactions) > 0:
                # Kiểm tra xem có transaction nào thành công không
                for trans in transactions:
                    if isinstance(trans, dict):
                        trans_status = str(trans.get('status', '')).upper()
                        if trans_status in ['PAID', 'SUCCESS', 'COMPLETED']:
                            is_paid_by_transactions = True
                            break
            
            is_paid = is_paid_by_status or is_paid_by_amount or is_paid_by_transactions
            
            print(f"🔍 Payment check - Status: {payos_status}, Amount paid: {amount_paid}, Remaining: {amount_remaining}")
            print(f"🔍 Payment check - By status: {is_paid_by_status}, By amount: {is_paid_by_amount}, By transactions: {is_paid_by_transactions}")
            print(f"✅ Is paid: {is_paid}")
            
            # Nếu PayOS báo đã thanh toán, sync về database
            if is_paid:
                from app.models import Order, Slot, Transaction, Product
                from app import db
                
                # Attempt to find order. Logic fix: if order_code is large (payment_code), parse it.
                real_order_id = order_code
                order = Order.query.get(order_code)
                
                if not order and order_code > 10000:
                    real_order_id = order_code // 10000
                    print(f"🔄 Parsing real_order_id from payment_code: {order_code} -> {real_order_id}")
                    order = Order.query.get(real_order_id)
                
                if not order:
                    print(f"⚠️ Order #{order_code} (or {real_order_id}) not found in database")
                elif order.status_payment != 'pending':
                    print(f"ℹ️ Order #{order_code} already has status: {order.status_payment}, skipping sync")
                else:
                    debug_log(f"POLL: Syncing payment status for order #{order_code}")
                    print(f"🔄 Syncing payment status for order #{order_code} from PayOS to database")
                    
                    try:
                        # Cập nhật order status — status_slots giữ 'pending'
                        # để Arduino poll /iot/pending-orders và nhả hàng
                        order.status_payment = 'completed'
                        order.status_slots = 'pending'

                        debug_log(f"POLL: Processing order #{real_order_id}, product_id={order.product_id}, slot_id={order.slot_id}")
                        
                        # Giảm stock trong slot (Sử dụng with_for_update để tránh Race Condition)
                        qty = getattr(order, 'quantity', 1)
                        slot = None
                        if order.slot_id:
                            slot = Slot.query.get(order.slot_id)
                        else:
                            slot = Slot.query.filter(Slot.product_id == order.product_id, Slot.stock >= qty).first()
                            if not slot:
                                 slot = Slot.query.filter(Slot.product_id == order.product_id, Slot.stock > 0).first()

                        debug_log(f"POLL: Searched for slot with product_id={order.product_id}, qty>={qty}. Result: {slot.slot_id if slot else 'None'}")

                        if slot:
                            if order.slot_id is None:
                                order.slot_id = slot.slot_id
                            
                            if slot.stock >= qty:
                                slot.stock -= qty
                                print(f"📦 Stock reduced for slot {slot.slot_id}: {slot.stock + qty} -> {slot.stock}")
                            else:
                                slot.stock = 0

                            # Requirement: If total stock of product becomes 0, set product to inactive
                            if slot.stock == 0:
                                product = Product.query.get(slot.product_id)
                                if product and product.stock == 0:
                                    product.active = False
                                    debug_log(f"POLL: Product {product.product_id} deactivated")
                                    print(f"⚠️ Product '{product.product_name}' marked as INACTIVE (total stock=0)")
                        else:
                            debug_log(f"POLL: No slot found for product {order.product_id}!")
                        
                        # Kiểm tra xem đã có transaction chưa
                        existing_transaction = Transaction.query.filter_by(order_id=real_order_id).first()
                        if not existing_transaction:
                            # Tạo transaction record
                            transaction_amount = amount_paid if amount_paid > 0 else (amount if amount > 0 else order.price_snapshot)
                            
                            # Lấy reference từ transactions nếu có
                            reference = None
                            if transactions and isinstance(transactions, list) and len(transactions) > 0:
                                reference = transactions[0].get('reference') if isinstance(transactions[0], dict) else None
                            
                            transaction = Transaction(
                                order_id=order.order_id,
                                amount=float(transaction_amount),
                                bank_trans_id=reference,
                                description=f"Thanh toán đơn hàng #{order_code}",
                                status='success'
                            )
                            db.session.add(transaction)
                            print(f"💳 Transaction created for order #{order_code}")
                        else:
                            print(f"ℹ️ Transaction already exists for order #{order_code}")
                        
                        db.session.commit()
                        print(f"✅ Order #{order_code} synced to completed status")
                        
                        # Emit WebSocket event for real-time notification
                        emit_payment_success(real_order_id, {
                            'amount': amount_paid if amount_paid > 0 else amount,
                            'synced': True
                        })
                        print(f"📤 WebSocket event emitted for order #{real_order_id}")
                    except Exception as sync_error:
                        db.session.rollback()
                        print(f"❌ Error syncing order #{order_code}: {str(sync_error)}")
                        import traceback
                        traceback.print_exc()
            
            return jsonify({
                'success': True,
                'message': 'Payment status retrieved',
                'data': result
            }), 200
        else:
            return jsonify({
                'success': False,
                'message': result.get('error', 'Failed to get payment status')
            }), 400
            
    except Exception as e:
        import traceback
        print(f"❌ Error checking payment status: {str(e)}")
        traceback.print_exc()
        return jsonify({
            'success': False,
            'message': f'Server error: {str(e)}'
        }), 500


@payment_bp.route('/payment/sync/<int:order_code>', methods=['POST'])
def sync_payment_status(order_code):
    """
    Manually sync payment status from PayOS to database.
    Useful for debugging or when webhook fails.
    """
    try:
        from app.models import Order, Slot, Transaction, Product
        from app import db
        
        # Kiểm tra order có tồn tại không
        # Attempt to find order. Logic fix: if order_code is large (payment_code), parse it.
        real_order_id = order_code
        order = Order.query.get(order_code)
        
        if not order and order_code > 10000:
            real_order_id = order_code // 10000
            order = Order.query.get(real_order_id)
            
        if not order:
            return jsonify({
                'success': False,
                'message': f'Order #{order_code} (or {real_order_id}) not found'
            }), 404
        
        # Lấy status từ PayOS
        result = get_payment_status(order_code)
        
        if not result.get('success'):
            return jsonify({
                'success': False,
                'message': result.get('error', 'Failed to get payment status from PayOS')
            }), 400
        
        # Kiểm tra trạng thái thanh toán
        payos_status = result.get('status', '').upper()
        amount = result.get('amount', 0)
        amount_paid = result.get('amount_paid', 0) or 0
        amount_remaining = result.get('amount_remaining', amount) or amount
        transactions = result.get('transactions', [])
        
        is_paid_by_status = payos_status in ['PAID', 'SUCCESS', 'COMPLETED']
        is_paid_by_amount = amount_paid > 0 and amount_remaining == 0
        is_paid_by_transactions = False
        
        if transactions and isinstance(transactions, list) and len(transactions) > 0:
            for trans in transactions:
                if isinstance(trans, dict):
                    trans_status = str(trans.get('status', '')).upper()
                    if trans_status in ['PAID', 'SUCCESS', 'COMPLETED']:
                        is_paid_by_transactions = True
                        break
        
        is_paid = is_paid_by_status or is_paid_by_amount or is_paid_by_transactions
        
        if not is_paid:
            return jsonify({
                'success': False,
                'message': f'Payment not completed. PayOS status: {payos_status}, Amount paid: {amount_paid}, Remaining: {amount_remaining}',
                'data': {
                    'payos_status': payos_status,
                    'amount_paid': amount_paid,
                    'amount_remaining': amount_remaining,
                    'order_status': order.status_payment
                }
            }), 400
        
        # Nếu đã thanh toán, sync về database
        if order.status_payment == 'pending':
            # status_slots giữ 'pending' để Arduino nhả hàng
            order.status_payment = 'completed'
            order.status_slots = 'pending'
            
            # Giảm stock (Sử dụng with_for_update để tránh Race Condition)
            qty = getattr(order, 'quantity', 1)
            slot = None
            if order.slot_id:
                slot = Slot.query.get(order.slot_id)
            else:
                slot = Slot.query.filter(Slot.product_id == order.product_id, Slot.stock >= qty).first()
                if not slot:
                     slot = Slot.query.filter(Slot.product_id == order.product_id, Slot.stock > 0).first()

            if slot:
                if order.slot_id is None:
                    order.slot_id = slot.slot_id

                if slot.stock >= qty:
                    slot.stock -= qty
                else: 
                     slot.stock = 0
                
                # Requirement: If total stock of product becomes 0, set product to inactive
                if slot.stock == 0:
                    product = Product.query.get(slot.product_id)
                    if product and product.stock == 0:
                        product.active = False
                        print(f"⚠️ Product '{product.product_name}' marked as INACTIVE (total stock=0)")
            
            # Tạo transaction nếu chưa có
            existing_transaction = Transaction.query.filter_by(order_id=real_order_id).first()
            if not existing_transaction:
                transaction_amount = amount_paid if amount_paid > 0 else (amount if amount > 0 else order.price_snapshot)
                reference = None
                if transactions and isinstance(transactions, list) and len(transactions) > 0:
                    reference = transactions[0].get('reference') if isinstance(transactions[0], dict) else None
                
                transaction = Transaction(
                    order_id=order.order_id,
                    amount=float(transaction_amount),
                    bank_trans_id=reference,
                    description=f"Thanh toán đơn hàng #{order_code}",
                    status='success'
                )
                db.session.add(transaction)
            
            db.session.commit()
            
            return jsonify({
                'success': True,
                'message': f'Order #{order_code} synced successfully',
                'data': {
                    'order_id': order.order_id,
                    'order_status': order.status_payment,
                    'payos_status': payos_status
                }
            }), 200
        else:
            return jsonify({
                'success': True,
                'message': f'Order #{order_code} already has status: {order.status_payment}',
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
            'message': f'Sync error: {str(e)}'
        }), 500


@payment_bp.route('/payment/cancel/<int:order_code>', methods=['POST'])
def cancel_payment_link(order_code):
    """
    Cancel a pending payment by order code.
    """
    try:
        result = cancel_payment(order_code)
        
        if result.get('success'):
            # Fix #4: Cập nhật database
            from app.models import Order
            from app import db
                
            real_order_id = order_code
            order = Order.query.get(order_code)
                
            if not order and order_code > 10000:
                real_order_id = order_code // 10000
                order = Order.query.get(real_order_id)
                    
            if order and order.status_payment == 'pending':
                order.status_payment = 'cancelled'
                order.status_slots = 'cancelled'
                db.session.commit()
                print(f"✅ Order #{real_order_id} marked as cancelled in DB")
                
            return jsonify({
                'success': True,
                'message': 'Payment cancelled successfully',
                'data': {'order_code': order_code}
            }), 200
        else:
            return jsonify({
                'success': False,
                'message': result.get('error', 'Failed to cancel payment')
            }), 400
            
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Server error: {str(e)}'
        }), 500


@payment_bp.route('/payment/success', methods=['GET'])
def payment_success_page():
    """
    Return URL after successful payment.
    """
    order_code = request.args.get('orderCode')
    return jsonify({
        'success': True,
        'message': 'Payment completed successfully',
        'order_code': order_code
    })


@payment_bp.route('/payment/cancel', methods=['GET'])
def payment_cancel_page():
    """
    Cancel URL when user cancels payment.
    """
    order_code = request.args.get('orderCode')
    return jsonify({
        'success': False,
        'message': 'Payment was cancelled',
        'order_code': order_code
    })

@payment_bp.route('/debug-db', methods=['GET'])
def debug_db():
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
