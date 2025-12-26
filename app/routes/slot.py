from flask import Blueprint, request, jsonify
from pydantic import ValidationError
from app import db
from app.models import Slot
from app.schemas import SlotCreate, SlotOut
from app.utils import token_required

slot_bp = Blueprint('slot', __name__)

@slot_bp.route('/slots', methods=['GET'])
def get_slots():
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
def get_slot(slot_id):
    slot = Slot.query.get_or_404(slot_id)
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
        new_slot = Slot(**data.model_dump())
        
        db.session.add(new_slot)
        db.session.commit()
        
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
        slot = Slot.query.get_or_404(slot_id)
        json_data = request.get_json(force=True, silent=True)
        if not json_data:
            return jsonify({
                'success': False,
                'message': 'Request body must be valid JSON'
            }), 400
        data = SlotCreate(**json_data)
        
        slot.machine_id = data.machine_id
        slot.slot_no = data.slot_no
        slot.product_id = data.product_id
        slot.quantity = data.quantity
        
        db.session.commit()
        
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
    slot = Slot.query.get_or_404(slot_id)
    db.session.delete(slot)
    db.session.commit()
    return jsonify({
        'success': True,
        'message': 'Slot deleted successfully'
    }), 200
