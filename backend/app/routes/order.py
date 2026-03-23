from flask import Blueprint, request, jsonify
from pydantic import ValidationError
from datetime import datetime
from app import db
from app.models import Order, Slot, Product
from app.schemas import OrderCreate, OrderOut
from app.utils import token_required
from app.utils.machine_auth import multi_auth_required
from app.websocket import emit_stock_update, emit_admin_order_new

order_bp = Blueprint('order', __name__)


def _get_order_for_access(order_id, current_auth):
    order = Order.query.get(order_id)
    if not order:
        return None, (jsonify({
            'success': False,
            'message': 'Order not found'
        }), 404)

    if current_auth is not None:
        order_machine_id = order.machine_id or (order.slot.machine_id if order.slot else None)
        if order_machine_id != current_auth:
            return None, (jsonify({
                'success': False,
                'message': 'Order does not belong to this machine'
            }), 403)

    return order, None

@order_bp.route('/orders', methods=['GET'])
@token_required
def get_orders(current_user):
    # Sắp xếp theo thời gian tạo giảm dần (đơn hàng mới nhất lên đầu)
    orders = Order.query.order_by(Order.created_at.desc()).all()
    return jsonify({
        'success': True,
        'message': 'Orders retrieved successfully',
        'data': [OrderOut.model_validate(o).model_dump() for o in orders]
    })

@order_bp.route('/orders/<int:order_id>', methods=['GET'])
@token_required
def get_order(current_user, order_id):
    order = Order.query.get_or_404(order_id)
    return jsonify({
        'success': True,
        'message': 'Order retrieved successfully',
        'data': OrderOut.model_validate(order).model_dump()
    })

@order_bp.route('/orders', methods=['POST'])
def create_order():
    """Create an order with completed status (legacy endpoint)"""
    try:
        print("📝 POST /api/orders received")
        json_data = request.get_json(force=True, silent=True)
        print(f"📦 Data: {json_data}")
        if not json_data:
            return jsonify({
                'success': False,
                'message': 'Request body must be valid JSON'
            }), 400
        data = OrderCreate(**json_data)
        
        # Tìm slot và kiểm tra stock (tránh block lock DB trong demo)
        slot = Slot.query.get(data.slot_id)
        
        if not slot:
            return jsonify({
                'success': False,
                'message': 'Slot not found'
            }), 404
        
        if slot.stock < 1:
            return jsonify({
                'success': False,
                'message': 'Insufficient stock'
            }), 400
        
        if not slot.product:
            return jsonify({
                'success': False,
                'message': 'Product not found in slot'
            }), 404

        if data.product_id != slot.product_id:
            return jsonify({
                'success': False,
                'message': 'product_id does not match the product assigned to the slot'
            }), 400

        expected_price = float(slot.product.price)
        if float(data.price_snapshot) != expected_price:
            return jsonify({
                'success': False,
                'message': (
                    f'price_snapshot does not match slot product price. '
                    f'Expected {expected_price}, got {float(data.price_snapshot)}'
                )
            }), 400
        
        # Tạo order
        new_order = Order(
            machine_id=slot.machine_id,
            product_id=data.product_id,
            price_snapshot=data.price_snapshot,
            slot_id=data.slot_id,
            status_payment='completed',
            status_slots='completed'
        )
        
        # Giảm stock trong slot
        slot.stock -= 1
        
        db.session.add(new_order)
        db.session.commit()

        # Real-time update
        emit_stock_update(slot.machine_id, {
            'slot_code': slot.slot_code,
            'new_stock': slot.stock,
            'product_id': slot.product_id
        })
        
        emit_admin_order_new({
            'order_id': new_order.order_id,
            'product_name': slot.product.product_name if slot.product else "Unknown",
            'amount': float(new_order.price_snapshot),
            'status': new_order.status_payment,
            'timestamp': datetime.utcnow().isoformat()
        })
        
        order_out = OrderOut.model_validate(new_order)
        return jsonify({
            'success': True,
            'message': 'Order created successfully',
            'data': order_out.model_dump()
        }), 201
    
    except ValidationError as e:
        return jsonify({
            'success': False,
            'message': 'Validation error',
            'errors': e.errors()
        }), 422
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': f'Error: {str(e)}'
        }), 500


@order_bp.route('/orders/pending', methods=['POST'])
@multi_auth_required
def create_pending_order(current_auth):
    """Create a pending order before payment (for QR payment flow)"""
    try:
        print("🕒 POST /api/orders/pending received")
        json_data = request.get_json(force=True, silent=True)
        print(f"📦 Data: {json_data}")
        if not json_data:
            return jsonify({
                'success': False,
                'message': 'Request body must be valid JSON'
            }), 400
        
        product_id = json_data.get('product_id')
        slot_id = json_data.get('slot_id')  # Optional - can be None for demo
        quantity = json_data.get('quantity', 1)

        if not product_id:
            return jsonify({
                'success': False,
                'message': 'product_id is required'
            }), 400

        try:
            quantity = int(quantity)
        except (TypeError, ValueError):
            return jsonify({
                'success': False,
                'message': 'quantity must be an integer'
            }), 400

        if quantity < 1:
            return jsonify({
                'success': False,
                'message': 'quantity must be greater than 0'
            }), 400
        
        # Kiểm tra product tồn tại
        product = Product.query.get(product_id)
        if not product:
            return jsonify({
                'success': False,
                'message': 'Product not found'
            }), 404
        
        # Tạo order với status pending (chưa thanh toán)
        from sqlalchemy import func
        from datetime import datetime, timedelta
        
        # Chỉ tính các pending order trong vòng 15 phút gần nhất (coi như timeout)
        timeout_threshold = datetime.utcnow() - timedelta(minutes=15)
        
        if slot_id is not None:
            slot = Slot.query.get(slot_id)
            if not slot:
                return jsonify({
                    'success': False,
                    'message': 'Slot not found'
                }), 404
            if slot.product_id != product_id:
                return jsonify({
                    'success': False,
                    'message': 'slot_id does not belong to the requested product'
                }), 400

            if current_auth is not None and slot.machine_id != current_auth:
                return jsonify({
                    'success': False,
                    'message': 'slot_id does not belong to this machine'
                }), 403

            pending_qty = db.session.query(func.sum(Order.quantity)).filter(
                Order.slot_id == slot_id,
                Order.status_payment == 'pending',
                Order.created_at >= timeout_threshold
            ).scalar() or 0
            available_stock = slot.stock - pending_qty
        else:
            pending_qty = db.session.query(func.sum(Order.quantity)).filter(
                Order.product_id == product_id,
                Order.machine_id == json_data.get('machine_id'),
                Order.status_payment == 'pending',
                Order.created_at >= timeout_threshold
            ).scalar() or 0
            available_stock = product.stock - pending_qty
        
        if available_stock < quantity:
            return jsonify({
                'success': False,
                'message': 'Sản phẩm tạm thời hết hàng hoặc đang có người khác đặt mua. Vui lòng thử lại sau.'
            }), 400

        price_snapshot = float(product.price) * quantity
        
        # Lấy machine_id từ slot hoặc nhận từ client
        final_machine_id = json_data.get('machine_id')
        if slot_id is not None and not final_machine_id:
            slot = Slot.query.get(slot_id)
            if slot:
                final_machine_id = slot.machine_id

        if current_auth is not None:
            if final_machine_id is None:
                final_machine_id = current_auth
            if final_machine_id != current_auth:
                return jsonify({
                    'success': False,
                    'message': 'machine_id does not match authenticated machine'
                }), 403

        new_order = Order(
            machine_id=final_machine_id,
            product_id=product_id,
            price_snapshot=price_snapshot,
            slot_id=slot_id,
            quantity=quantity,
            status_payment='pending',
            status_slots='pending'
        )
        
        db.session.add(new_order)
        db.session.commit()
        
        order_out = OrderOut.model_validate(new_order)
        return jsonify({
            'success': True,
            'message': 'Pending order created successfully',
            'data': order_out.model_dump()
        }), 201
    
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': f'Error creating order: {str(e)}'
        }), 500


@order_bp.route('/orders/<int:order_id>/complete', methods=['PUT', 'POST'])
@multi_auth_required
def complete_order(current_auth, order_id):
    """Mark order as completed after successful payment"""
    try:
        order, error_response = _get_order_for_access(order_id, current_auth)
        if error_response:
            return error_response
        
        if order.status_payment == 'completed':
            return jsonify({
                'success': True,
                'message': 'Order already completed',
                'data': OrderOut.model_validate(order).model_dump()
            })
        
        # Cập nhật status
        order.status_payment = 'completed'
        order.status_slots = 'completed'
        
        # Giảm stock trong slot
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
            
            # Real-time update
            emit_stock_update(slot.machine_id, {
                'slot_code': slot.slot_code,
                'new_stock': slot.stock,
                'product_id': slot.product_id
            })
        
        db.session.commit()

        emit_admin_order_new({
            'order_id': order.order_id,
            'product_name': order.product.product_name if order.product else "Unknown",
            'amount': float(order.price_snapshot),
            'status': order.status_payment,
            'timestamp': datetime.utcnow().isoformat()
        })
        
        order_out = OrderOut.model_validate(order)
        return jsonify({
            'success': True,
            'message': 'Order completed successfully',
            'data': order_out.model_dump()
        })
    
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': f'Error completing order: {str(e)}'
        }), 500


@order_bp.route('/orders/<int:order_id>/cancel', methods=['PUT', 'POST'])
@multi_auth_required
def cancel_order(current_auth, order_id):
    """Cancel a pending order"""
    try:
        order, error_response = _get_order_for_access(order_id, current_auth)
        if error_response:
            return error_response
        
        if order.status_payment != 'pending':
            return jsonify({
                'success': False,
                'message': 'Only pending orders can be cancelled'
            }), 400
        
        order.status_payment = 'cancelled'
        order.status_slots = 'cancelled'
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Order cancelled successfully'
        })
    
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': f'Error cancelling order: {str(e)}'
        }), 500


@order_bp.route('/orders/<int:order_id>/status', methods=['GET'])
@multi_auth_required
def get_order_status(current_auth, order_id):
    """Get order status from database (public endpoint for polling)"""
    try:
        order, error_response = _get_order_for_access(order_id, current_auth)
        if error_response:
            return error_response
        
        return jsonify({
            'success': True,
            'message': 'Order status retrieved',
            'data': {
                'order_id': order.order_id,
                'status_payment': order.status_payment,
                'status_slots': order.status_slots,
                'created_at': order.created_at.isoformat() if order.created_at else None
            }
        })
    
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error getting order status: {str(e)}'
        }), 500
