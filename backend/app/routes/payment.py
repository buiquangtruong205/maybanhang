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
        
        # Convert items to dict format for PayOS
        items = [item.model_dump() for item in data.items]
        
        result = create_payment_link(
            order_code=data.order_code,
            amount=data.amount,
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
                    'order_code': data.order_code
                }
            }), 201
        else:
            return jsonify({
                'success': False,
                'message': result.get('error', 'Failed to create payment link')
            }), 400
            
    except ValidationError as e:
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
            order_code = webhook.data.orderCode
            amount = webhook.data.amount
            
            print(f"✅ Payment successful: Order #{order_code}, Amount: {amount}")
            
            # Import models for database operations
            from app.models import Order, Slot, Transaction
            from app import db
            
            # Tìm order theo order_id (order_code chính là order_id)
            order = Order.query.get(order_code)
            if order:
                # Chỉ cập nhật nếu order đang ở trạng thái pending
                if order.status == 'pending':
                    # Cập nhật status thành completed
                    order.status = 'completed'
                    
                    # Giảm stock trong slot
                    slot = Slot.query.get(order.slot_id)
                    if slot and slot.stock > 0:
                        slot.stock -= 1
                        print(f"📦 Stock reduced for slot {order.slot_id}: {slot.stock + 1} -> {slot.stock}")
                    
                    # Kiểm tra xem đã có transaction chưa (tránh duplicate)
                    existing_transaction = Transaction.query.filter_by(order_id=order_code).first()
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
                            description=f"Thanh toán đơn hàng #{order_code}",
                            status='success'
                        )
                        db.session.add(transaction)
                        print(f"💳 Transaction created for order #{order_code}")
                    else:
                        print(f"ℹ️ Transaction already exists for order #{order_code}")
                    
                    db.session.commit()
                    print(f"✅ Order #{order_code} completed and transaction created")
                else:
                    print(f"ℹ️ Order #{order_code} already has status: {order.status}")
            else:
                print(f"⚠️ Order #{order_code} not found in database")
            
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
                from app.models import Order, Slot, Transaction
                from app import db
                
                order = Order.query.get(order_code)
                if not order:
                    print(f"⚠️ Order #{order_code} not found in database")
                elif order.status != 'pending':
                    print(f"ℹ️ Order #{order_code} already has status: {order.status}, skipping sync")
                else:
                    print(f"🔄 Syncing payment status for order #{order_code} from PayOS to database")
                    
                    try:
                        # Cập nhật order status
                        order.status = 'completed'
                        
                        # Giảm stock trong slot
                        slot = Slot.query.get(order.slot_id)
                        if slot and slot.stock > 0:
                            slot.stock -= 1
                            print(f"📦 Stock reduced for slot {order.slot_id}: {slot.stock + 1} -> {slot.stock}")
                        
                        # Kiểm tra xem đã có transaction chưa
                        existing_transaction = Transaction.query.filter_by(order_id=order_code).first()
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
        from app.models import Order, Slot, Transaction
        from app import db
        
        # Kiểm tra order có tồn tại không
        order = Order.query.get(order_code)
        if not order:
            return jsonify({
                'success': False,
                'message': f'Order #{order_code} not found'
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
                    'order_status': order.status
                }
            }), 400
        
        # Nếu đã thanh toán, sync về database
        if order.status == 'pending':
            order.status = 'completed'
            
            # Giảm stock
            slot = Slot.query.get(order.slot_id)
            if slot and slot.stock > 0:
                slot.stock -= 1
            
            # Tạo transaction nếu chưa có
            existing_transaction = Transaction.query.filter_by(order_id=order_code).first()
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
                    'order_status': order.status,
                    'payos_status': payos_status
                }
            }), 200
        else:
            return jsonify({
                'success': True,
                'message': f'Order #{order_code} already has status: {order.status}',
                'data': {
                    'order_id': order.order_id,
                    'order_status': order.status,
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
