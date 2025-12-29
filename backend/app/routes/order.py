from flask import Blueprint, request, jsonify
from pydantic import ValidationError
from app import db
from app.models import Order, Slot, Product
from app.schemas import OrderCreate, OrderOut
from app.utils import token_required

order_bp = Blueprint('order', __name__)

@order_bp.route('/orders', methods=['GET'])
@token_required
def get_orders(current_user):
    # Sắp xếp theo thời gian tạo giảm dần (đơn hàng mới nhất lên đầu)
    orders = Order.query.order_by(Order.create_at.desc()).all()
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
        
        # Tìm slot và kiểm tra stock
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
        
        # Tạo order
        new_order = Order(
            product_id=data.product_id,
            price_snapshot=data.price_snapshot,
            slot_id=data.slot_id,
            status='completed'
        )
        
        # Giảm stock trong slot
        slot.stock -= 1
        
        db.session.add(new_order)
        db.session.commit()
        
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


@order_bp.route('/orders/pending', methods=['POST'])
def create_pending_order():
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
        price_snapshot = json_data.get('price_snapshot')
        slot_id = json_data.get('slot_id', 1)  # Default to slot 1
        
        if not product_id or not price_snapshot:
            return jsonify({
                'success': False,
                'message': 'product_id and price_snapshot are required'
            }), 400
        
        # Kiểm tra product tồn tại
        product = Product.query.get(product_id)
        if not product:
            return jsonify({
                'success': False,
                'message': 'Product not found'
            }), 404
        
        # Tạo order với status pending (chưa thanh toán)
        new_order = Order(
            product_id=product_id,
            price_snapshot=price_snapshot,
            slot_id=slot_id,
            status='pending'
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
        return jsonify({
            'success': False,
            'message': f'Error creating order: {str(e)}'
        }), 500


@order_bp.route('/orders/<int:order_id>/complete', methods=['PUT'])
def complete_order(order_id):
    """Mark order as completed after successful payment"""
    try:
        order = Order.query.get(order_id)
        if not order:
            return jsonify({
                'success': False,
                'message': 'Order not found'
            }), 404
        
        if order.status == 'completed':
            return jsonify({
                'success': True,
                'message': 'Order already completed',
                'data': OrderOut.model_validate(order).model_dump()
            })
        
        # Cập nhật status
        order.status = 'completed'
        
        # Giảm stock trong slot
        slot = Slot.query.get(order.slot_id)
        if slot and slot.stock > 0:
            slot.stock -= 1
        
        db.session.commit()
        
        order_out = OrderOut.model_validate(order)
        return jsonify({
            'success': True,
            'message': 'Order completed successfully',
            'data': order_out.model_dump()
        })
    
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error completing order: {str(e)}'
        }), 500


@order_bp.route('/orders/<int:order_id>/cancel', methods=['PUT'])
def cancel_order(order_id):
    """Cancel a pending order"""
    try:
        order = Order.query.get(order_id)
        if not order:
            return jsonify({
                'success': False,
                'message': 'Order not found'
            }), 404
        
        if order.status != 'pending':
            return jsonify({
                'success': False,
                'message': 'Only pending orders can be cancelled'
            }), 400
        
        order.status = 'cancelled'
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Order cancelled successfully'
        })
    
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error cancelling order: {str(e)}'
        }), 500


@order_bp.route('/orders/<int:order_id>/status', methods=['GET'])
def get_order_status(order_id):
    """Get order status from database (public endpoint for polling)"""
    try:
        order = Order.query.get(order_id)
        if not order:
            return jsonify({
                'success': False,
                'message': 'Order not found'
            }), 404
        
        return jsonify({
            'success': True,
            'message': 'Order status retrieved',
            'data': {
                'order_id': order.order_id,
                'status': order.status,
                'created_at': order.create_at.isoformat() if order.create_at else None
            }
        })
    
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error getting order status: {str(e)}'
        }), 500