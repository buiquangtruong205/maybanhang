from flask import Blueprint, request, jsonify
from pydantic import ValidationError
from app import db
from app.models import Machine
from app.schemas import MachineCreate, MachineOut
from app.utils import token_required

machine_bp = Blueprint('machine', __name__)

@machine_bp.route('/machines', methods=['GET'])
def get_machines():
    machines = Machine.query.all()
    return jsonify({
        'success': True,
        'message': 'Machines retrieved successfully',
        'data': [MachineOut.model_validate(m).model_dump() for m in machines]
    })

@machine_bp.route('/machines/<int:machine_id>', methods=['GET'])
def get_machine(machine_id):
    machine = Machine.query.get_or_404(machine_id)
    return jsonify({
        'success': True,
        'message': 'Machine retrieved successfully',
        'data': MachineOut.model_validate(machine).model_dump()
    })

@machine_bp.route('/machines', methods=['POST'])
@token_required
def create_machine(current_user):
    try:
        json_data = request.get_json(force=True, silent=True)
        if not json_data:
            return jsonify({
                'success': False,
                'message': 'Request body must be valid JSON'
            }), 400
        data = MachineCreate(**json_data)
        new_machine = Machine(**data.model_dump())
        
        db.session.add(new_machine)
        db.session.commit()
        
        machine_out = MachineOut.model_validate(new_machine)
        return jsonify({
            'success': True,
            'message': 'Machine created successfully',
            'data': machine_out.model_dump()
        }), 201
    
    except ValidationError as e:
        return jsonify({
            'success': False,
            'message': 'Validation error',
            'errors': e.errors()
        }), 422

@machine_bp.route('/machines/<int:machine_id>', methods=['PUT'])
@token_required
def update_machine(current_user, machine_id):
    try:
        machine = Machine.query.get_or_404(machine_id)
        json_data = request.get_json(force=True, silent=True)
        if not json_data:
            return jsonify({
                'success': False,
                'message': 'Request body must be valid JSON'
            }), 400
        data = MachineCreate(**json_data)
        
        machine.name = data.name
        machine.location = data.location
        machine.status = data.status
        
        db.session.commit()
        
        machine_out = MachineOut.model_validate(machine)
        return jsonify({
            'success': True,
            'message': 'Machine updated successfully',
            'data': machine_out.model_dump()
        })
    
    except ValidationError as e:
        return jsonify({
            'success': False,
            'message': 'Validation error',
            'errors': e.errors()
        }), 422

@machine_bp.route('/machines/<int:machine_id>', methods=['DELETE'])
@token_required
def delete_machine(current_user, machine_id):
    machine = Machine.query.get_or_404(machine_id)
    db.session.delete(machine)
    db.session.commit()
    return jsonify({
        'success': True,
        'message': 'Machine deleted successfully'
    }), 200
