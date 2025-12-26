from flask import Blueprint, request, jsonify
from pydantic import ValidationError
from app import db
from app.models import Order, Slot
from app.schemas import OrderCreate, OrderOut
from app.utils import token_required

order_bp = Blueprint('order', __name__)

@order_bp.route('/orders', methods=['GET'])
@token_required
def get_orders(current_user):
    orders = Order.query.all()
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
    try:
        json_data = request.get_json(force=True, silent=True)
        if not json_data:
            return jsonify({
                'success': False,
                'message': 'Request body must be valid JSON'
            }), 400
        data = OrderCreate(**json_data)
        
        # Tìm slot và kiểm tra quantity
        slot = Slot.query.filter_by(
            machine_id=data.machine_id,
            slot_no=data.slot_no
        ).first()
        
        if not slot:
            return jsonify({
                'success': False,
                'message': 'Slot not found'
            }), 404
        
        if slot.quantity < data.quantity:
            return jsonify({
                'success': False,
                'message': 'Insufficient quantity'
            }), 400
        
        if not slot.product:
            return jsonify({
                'success': False,
                'message': 'Product not found in slot'
            }), 404
        
        # Tạo order
        total_price = slot.product.price * data.quantity
        new_order = Order(
            machine_id=data.machine_id,
            slot_no=data.slot_no,
            quantity=data.quantity,
            total_price=total_price,
            payment_method=data.payment_method,
            status='completed'
        )
        
        # Giảm quantity trong slot
        slot.quantity -= data.quantity
        
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