import json
from flask import Blueprint, request, jsonify
from pydantic import ValidationError
from app import db
from app.models import Machine
from app.schemas import MachineCreate, MachineOut
from app.utils import token_required, multi_auth_required
from app.utils.admin_logger import log_admin_action

machine_bp = Blueprint('machine', __name__)


def _normalize_optional_string(value):
    if value is None:
        return None
    value = str(value).strip()
    return value or None


def _parse_optional_json(value, field_name):
    if value in (None, '', {}):
        return None
    if isinstance(value, dict):
        return value
    if isinstance(value, list):
        raise ValueError(f'{field_name} must be a JSON object')

    try:
        parsed = json.loads(value)
    except json.JSONDecodeError as exc:
        raise ValueError(f'{field_name} must be valid JSON') from exc

    if parsed is None:
        return None
    if not isinstance(parsed, dict):
        raise ValueError(f'{field_name} must be a JSON object')
    return parsed


def _apply_machine_payload(machine, data):
    machine.name = data.name
    machine.location = _normalize_optional_string(data.location)
    machine.status = data.status
    machine.secret_key = data.secret_key.strip()
    machine.mqtt_command_topic = _normalize_optional_string(data.mqtt_command_topic)
    machine.mqtt_status_topic = _normalize_optional_string(data.mqtt_status_topic)
    machine.mqtt_broadcast_status_topic = _normalize_optional_string(data.mqtt_broadcast_status_topic)
    machine.ui_layout = _parse_optional_json(data.ui_layout, 'ui_layout')
    machine.device_profile = _parse_optional_json(data.device_profile, 'device_profile')
    machine.config_notes = _normalize_optional_string(data.config_notes)

@machine_bp.route('/machines', methods=['GET'])
@token_required
def get_machines(current_user):
    machines = Machine.query.all()
    return jsonify({
        'success': True,
        'message': 'Machines retrieved successfully',
        'data': [MachineOut.model_validate(m).model_dump() for m in machines]
    })

@machine_bp.route('/machines/<int:machine_id>', methods=['GET'])
@multi_auth_required
def get_machine(current_auth, machine_id):
    machine = Machine.query.filter_by(machine_id=machine_id).first()
    if not machine:
        return jsonify({
            'success': False,
            'message': 'Machine not found'
        }), 404
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
        secret_key = data.secret_key.strip()
        if not secret_key:
            return jsonify({
                'success': False,
                'message': 'secret_key is required'
            }), 400

        existing_key = Machine.query.filter_by(secret_key=secret_key).first()
        if existing_key:
            return jsonify({
                'success': False,
                'message': 'Secret key already exists'
            }), 400

        new_machine = Machine()
        _apply_machine_payload(new_machine, data)
        
        db.session.add(new_machine)
        db.session.commit()
        
        log_admin_action(
            user_id=current_user.user_id,
            action='create_machine',
            detail=f"Tạo máy '{new_machine.name}' tại {new_machine.location or 'N/A'}",
            target_type='machine',
            target_id=new_machine.machine_id
        )
        
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
    except ValueError as e:
        return jsonify({
            'success': False,
            'message': str(e)
        }), 400

@machine_bp.route('/machines/<int:machine_id>', methods=['PUT'])
@token_required
def update_machine(current_user, machine_id):
    try:
        machine = Machine.query.filter_by(machine_id=machine_id).first()
        if not machine:
            return jsonify({
                'success': False,
                'message': 'Machine not found'
            }), 404
        json_data = request.get_json(force=True, silent=True)
        if not json_data:
            return jsonify({
                'success': False,
                'message': 'Request body must be valid JSON'
            }), 400
        data = MachineCreate(**json_data)
        secret_key = data.secret_key.strip()
        if not secret_key:
            return jsonify({
                'success': False,
                'message': 'secret_key is required'
            }), 400

        existing_key = Machine.query.filter(
            Machine.secret_key == secret_key,
            Machine.machine_id != machine_id
        ).first()
        if existing_key:
            return jsonify({
                'success': False,
                'message': 'Secret key already exists'
            }), 400
        
        _apply_machine_payload(machine, data)
        
        db.session.commit()
        
        log_admin_action(
            user_id=current_user.user_id,
            action='update_machine',
            detail=f"Cập nhật máy '{machine.name}'",
            target_type='machine',
            target_id=machine_id
        )
        
        machine_out = MachineOut.model_validate(machine)
        return jsonify({
            'success': True,
            'message': 'Machine updated successfully',
            'data': machine_out.model_dump()
        })
    
        
        log_admin_action(
            user_id=current_user.user_id,
            action='update_machine',
            detail=f"Cập nhật máy '{machine.name}'",
            target_type='machine',
            target_id=machine_id
        )
        
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
    except ValueError as e:
        return jsonify({
            'success': False,
            'message': str(e)
        }), 400

@machine_bp.route('/machines/<int:machine_id>', methods=['DELETE'])
@token_required
def delete_machine(current_user, machine_id):
    machine = Machine.query.filter_by(machine_id=machine_id).first()
    if not machine:
        return jsonify({
            'success': False,
            'message': 'Machine not found'
        }), 404
    machine_name = machine.name
    
    # Import locally to avoid circular dependencies
    from app.models import (
        DeviceIdentity, DeviceSession, DeviceLog, StaffAccessLog,
        FirmwareUpdate, ApiAuditLog, CashDeposit, Slot, Order
    )
    
    try:
        # Pre-emptive Nullification to preserve Audit History
        db.session.query(ApiAuditLog).filter_by(machine_id=machine_id).update({'machine_id': None})
        
        # Hard Deletion for ephemeral operational data linked to the Machine
        db.session.query(DeviceIdentity).filter_by(machine_id=machine_id).delete()
        db.session.query(DeviceSession).filter_by(machine_id=machine_id).delete()
        db.session.query(DeviceLog).filter_by(machine_id=machine_id).delete()
        db.session.query(StaffAccessLog).filter_by(machine_id=machine_id).delete()
        db.session.query(FirmwareUpdate).filter_by(machine_id=machine_id).delete()
        db.session.query(CashDeposit).filter_by(machine_id=machine_id).delete()
        
        # Cascade Slots gracefully
        slots = Slot.query.filter_by(machine_id=machine_id).all()
        for s in slots:
            db.session.query(Order).filter_by(slot_id=s.slot_id).update({'slot_id': None})
            db.session.delete(s)
            
        # Hard Delete the Machine itself
        db.session.delete(machine)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': f"Failed to cascade delete dependencies: {str(e)}"
        }), 500

    log_admin_action(
        user_id=current_user.user_id,
        action='delete_machine',
        detail=f"Xóa máy '{machine_name}'",
        target_type='machine',
        target_id=machine_id
    )
    
    return jsonify({
        'success': True,
        'message': 'Machine deleted successfully'
    }), 200
