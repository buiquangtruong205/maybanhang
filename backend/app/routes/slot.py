from flask import Blueprint, request, jsonify
from pydantic import ValidationError
from app import db
from app.models import Slot
from app.schemas import SlotCreate, SlotOut
from app.utils import token_required, multi_auth_required
from app.websocket import emit_stock_update
from app.utils.admin_logger import log_admin_action

slot_bp = Blueprint('slot', __name__)

@slot_bp.route('/slots', methods=['GET'])
@multi_auth_required
def get_slots(current_auth):
    machine_id = request.args.get('machine_id', type=int)
    if machine_id:
        slots = Slot.query.filter_by(machine_id=machine_id).all()
    else:
        slots = Slot.query.all()
    return jsonify({
        'success': True,
        'message': 'Slots retrieved successfully',
        'data': [SlotOut.model_validate(s).model_dump() for s in slots]
    })

@slot_bp.route('/slots/<int:slot_id>', methods=['GET'])
@multi_auth_required
def get_slot(current_auth, slot_id):
    slot = Slot.query.filter_by(slot_id=slot_id).first()
    if not slot:
        return jsonify({
            'success': False,
            'message': 'Slot not found'
        }), 404
    return jsonify({
        'success': True,
        'message': 'Slot retrieved successfully',
        'data': SlotOut.model_validate(slot).model_dump()
    })

@slot_bp.route('/slots', methods=['POST'])
@token_required
def create_slot(current_user):
    try:
        json_data = request.get_json(force=True, silent=True)
        if not json_data:
            return jsonify({
                'success': False,
                'message': 'Request body must be valid JSON'
            }), 400
        data = SlotCreate(**json_data)
        
        # Kiểm tra trùng mã khe trên cùng một máy
        existing = Slot.query.filter_by(machine_id=data.machine_id, slot_code=data.slot_code).first()
        if existing:
            return jsonify({
                'success': False,
                'message': 'Khe đã có sản phẩm'
            }), 400
            
        new_slot = Slot(**data.model_dump())
        
        db.session.add(new_slot)
        db.session.commit()
        
        # Real-time update
        emit_stock_update(new_slot.machine_id, {
            'slot_code': new_slot.slot_code,
            'new_stock': new_slot.stock,
            'product_id': new_slot.product_id
        })
        
        log_admin_action(
            user_id=current_user.user_id,
            action='create_slot',
            detail=f"Tạo slot '{new_slot.slot_code}' cho máy {new_slot.machine_id}",
            target_type='slot',
            target_id=new_slot.slot_id
        )
        
        slot_out = SlotOut.model_validate(new_slot)
        return jsonify({
            'success': True,
            'message': 'Slot created successfully',
            'data': slot_out.model_dump()
        }), 201
    
    except ValidationError as e:
        return jsonify({
            'success': False,
            'message': 'Validation error',
            'errors': e.errors()
        }), 422

@slot_bp.route('/slots/<int:slot_id>', methods=['PUT'])
@token_required
def update_slot(current_user, slot_id):
    try:
        slot = Slot.query.filter_by(slot_id=slot_id).first()
        if not slot:
            return jsonify({
                'success': False,
                'message': 'Slot not found'
            }), 404
        json_data = request.get_json(force=True, silent=True)
        if not json_data:
            return jsonify({
                'success': False,
                'message': 'Request body must be valid JSON'
            }), 400
        data = SlotCreate(**json_data)
        
        # Kiểm tra trùng mã khe trên cùng một máy (loại trừ slot hiện tại)
        existing = Slot.query.filter(
            Slot.machine_id == data.machine_id,
            Slot.slot_code == data.slot_code,
            Slot.slot_id != slot_id
        ).first()
        if existing:
            return jsonify({
                'success': False,
                'message': 'Khe đã có sản phẩm'
            }), 400
            
        slot.machine_id = data.machine_id
        slot.slot_code = data.slot_code
        slot.product_id = data.product_id
        slot.stock = data.stock
        slot.capacity = data.capacity
        
        db.session.commit()
        
        # Real-time update
        emit_stock_update(slot.machine_id, {
            'slot_code': slot.slot_code,
            'new_stock': slot.stock,
            'product_id': slot.product_id
        })
        
        log_admin_action(
            user_id=current_user.user_id,
            action='update_slot',
            detail=f"Cập nhật slot '{slot.slot_code}' máy {slot.machine_id}",
            target_type='slot',
            target_id=slot_id
        )
        
        slot_out = SlotOut.model_validate(slot)
        return jsonify({
            'success': True,
            'message': 'Slot updated successfully',
            'data': slot_out.model_dump()
        })
    
    except ValidationError as e:
        return jsonify({
            'success': False,
            'message': 'Validation error',
            'errors': e.errors()
        }), 422

@slot_bp.route('/slots/<int:slot_id>', methods=['DELETE'])
@token_required
def delete_slot(current_user, slot_id):
    slot = Slot.query.filter_by(slot_id=slot_id).first()
    if not slot:
        return jsonify({
            'success': False,
            'message': 'Slot not found'
        }), 404
    
    # Import locally to avoid circular dependencies
    from app.models import Order
    
    try:
        # Trước khi xóa khe hàng, ta gỡ liên kết với các Đơn hàng liên quan
        # (Đặt slot_id về NULL trong bảng orders)
        db.session.query(Order).filter_by(slot_id=slot_id).update({'slot_id': None})
        
        db.session.delete(slot)
        db.session.commit()
        
        log_admin_action(
            user_id=current_user.user_id,
            action='delete_slot',
            detail=f"Xóa khe '{slot.slot_code}' máy {slot.machine_id}",
            target_type='slot',
            target_id=slot_id
        )
        
        return jsonify({
            'success': True,
            'message': 'Slot deleted successfully'
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': f'Error deleting slot: {str(e)}'
        }), 500
