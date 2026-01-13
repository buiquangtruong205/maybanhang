from flask import Blueprint, request, jsonify
from datetime import datetime
from pydantic import ValidationError
from app import db
from app.models import FirmwareUpdate
from app.schemas import FirmwareUpdateCreate, FirmwareUpdateOut, FirmwareUpdateStatus
from app.utils import token_required

firmware_bp = Blueprint('firmware', __name__)


@firmware_bp.route('/firmware/updates', methods=['GET'])
@token_required
def get_firmware_updates(current_user):
    """Get all firmware updates"""
    updates = FirmwareUpdate.query.order_by(FirmwareUpdate.update_id.desc()).all()
    return jsonify({
        'success': True,
        'message': 'Firmware updates retrieved successfully',
        'data': [FirmwareUpdateOut.model_validate(u).model_dump() for u in updates]
    })


@firmware_bp.route('/firmware/updates/machine/<int:machine_id>', methods=['GET'])
@token_required
def get_updates_by_machine(current_user, machine_id):
    """Get firmware updates for a machine"""
    updates = FirmwareUpdate.query.filter_by(machine_id=machine_id).order_by(FirmwareUpdate.update_id.desc()).all()
    return jsonify({
        'success': True,
        'message': 'Firmware updates retrieved successfully',
        'data': [FirmwareUpdateOut.model_validate(u).model_dump() for u in updates]
    })


@firmware_bp.route('/firmware/updates/<int:update_id>', methods=['GET'])
@token_required
def get_firmware_update(current_user, update_id):
    """Get a specific firmware update"""
    update = FirmwareUpdate.query.get_or_404(update_id)
    return jsonify({
        'success': True,
        'message': 'Firmware update retrieved successfully',
        'data': FirmwareUpdateOut.model_validate(update).model_dump()
    })


@firmware_bp.route('/firmware/updates', methods=['POST'])
@token_required
def create_firmware_update(current_user):
    """Create a new firmware update"""
    try:
        json_data = request.get_json(force=True, silent=True)
        if not json_data:
            return jsonify({
                'success': False,
                'message': 'Request body must be valid JSON'
            }), 400

        data = FirmwareUpdateCreate(**json_data)
        new_update = FirmwareUpdate(**data.model_dump())
        
        db.session.add(new_update)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Firmware update created successfully',
            'data': FirmwareUpdateOut.model_validate(new_update).model_dump()
        }), 201

    except ValidationError as e:
        return jsonify({
            'success': False,
            'message': 'Validation error',
            'errors': e.errors()
        }), 422


@firmware_bp.route('/firmware/updates/<int:update_id>/status', methods=['PUT'])
@token_required
def update_firmware_status(current_user, update_id):
    """Update firmware update status"""
    try:
        update = FirmwareUpdate.query.get_or_404(update_id)
        
        json_data = request.get_json(force=True, silent=True)
        if not json_data:
            return jsonify({
                'success': False,
                'message': 'Request body must be valid JSON'
            }), 400

        data = FirmwareUpdateStatus(**json_data)
        
        old_status = update.status
        update.status = data.status
        
        if data.error_message:
            update.error_message = data.error_message
        
        # Set timestamps based on status
        if data.status == 'downloading' and old_status == 'pending':
            update.started_at = datetime.utcnow()
        elif data.status in ['success', 'failed']:
            update.finished_at = datetime.utcnow()
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Firmware status updated successfully',
            'data': FirmwareUpdateOut.model_validate(update).model_dump()
        })

    except ValidationError as e:
        return jsonify({
            'success': False,
            'message': 'Validation error',
            'errors': e.errors()
        }), 422


@firmware_bp.route('/firmware/updates/<int:update_id>', methods=['DELETE'])
@token_required
def delete_firmware_update(current_user, update_id):
    """Delete a firmware update (only if pending)"""
    update = FirmwareUpdate.query.get_or_404(update_id)
    
    if update.status != 'pending':
        return jsonify({
            'success': False,
            'message': 'Can only delete pending updates'
        }), 400
    
    db.session.delete(update)
    db.session.commit()
    
    return jsonify({
        'success': True,
        'message': 'Firmware update deleted successfully'
    })
