from flask import Blueprint, request, jsonify
from datetime import datetime
from pydantic import ValidationError
from app import db
from app.models import DeviceIdentity, DeviceSession
from app.schemas import (
    DeviceIdentityCreate, DeviceIdentityOut,
    DeviceSessionCreate, DeviceSessionOut
)
from app.utils import token_required

device_bp = Blueprint('device', __name__)


# ==================== DeviceIdentity ====================

@device_bp.route('/devices/identity', methods=['GET'])
@token_required
def get_all_identities(current_user):
    """Get all device identities"""
    identities = DeviceIdentity.query.all()
    return jsonify({
        'success': True,
        'message': 'Device identities retrieved successfully',
        'data': [DeviceIdentityOut.model_validate(i).model_dump() for i in identities]
    })


@device_bp.route('/devices/identity/<int:machine_id>', methods=['GET'])
@token_required
def get_identity(current_user, machine_id):
    """Get device identity for a machine"""
    identity = DeviceIdentity.query.get_or_404(machine_id)
    return jsonify({
        'success': True,
        'message': 'Device identity retrieved successfully',
        'data': DeviceIdentityOut.model_validate(identity).model_dump()
    })


@device_bp.route('/devices/identity', methods=['POST'])
@token_required
def create_identity(current_user):
    """Create or update device identity"""
    try:
        json_data = request.get_json(force=True, silent=True)
        if not json_data:
            return jsonify({
                'success': False,
                'message': 'Request body must be valid JSON'
            }), 400

        data = DeviceIdentityCreate(**json_data)
        
        # Check if identity exists
        identity = DeviceIdentity.query.get(data.machine_id)
        if identity:
            # Update existing
            identity.device_public_key = data.device_public_key
            identity.cert_fingerprint = data.cert_fingerprint
            identity.secure_element_id = data.secure_element_id
            identity.mac_address = data.mac_address
            identity.status = data.status
        else:
            # Create new
            identity = DeviceIdentity(**data.model_dump())
            db.session.add(identity)
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Device identity saved successfully',
            'data': DeviceIdentityOut.model_validate(identity).model_dump()
        }), 201

    except ValidationError as e:
        return jsonify({
            'success': False,
            'message': 'Validation error',
            'errors': e.errors()
        }), 422


@device_bp.route('/devices/identity/<int:machine_id>/revoke', methods=['PUT'])
@token_required
def revoke_identity(current_user, machine_id):
    """Revoke a device identity"""
    identity = DeviceIdentity.query.get_or_404(machine_id)
    identity.status = 'revoked'
    identity.revoked_at = datetime.utcnow()
    db.session.commit()
    
    return jsonify({
        'success': True,
        'message': 'Device identity revoked successfully'
    })


# ==================== DeviceSession ====================

@device_bp.route('/devices/sessions', methods=['GET'])
@token_required
def get_all_sessions(current_user):
    """Get all device sessions"""
    sessions = DeviceSession.query.order_by(DeviceSession.issued_at.desc()).all()
    return jsonify({
        'success': True,
        'message': 'Device sessions retrieved successfully',
        'data': [DeviceSessionOut.model_validate(s).model_dump() for s in sessions]
    })


@device_bp.route('/devices/sessions/machine/<int:machine_id>', methods=['GET'])
@token_required
def get_sessions_by_machine(current_user, machine_id):
    """Get all sessions for a machine"""
    sessions = DeviceSession.query.filter_by(machine_id=machine_id).order_by(DeviceSession.issued_at.desc()).all()
    return jsonify({
        'success': True,
        'message': 'Device sessions retrieved successfully',
        'data': [DeviceSessionOut.model_validate(s).model_dump() for s in sessions]
    })


@device_bp.route('/devices/sessions', methods=['POST'])
@token_required
def create_session(current_user):
    """Create a new device session"""
    try:
        json_data = request.get_json(force=True, silent=True)
        if not json_data:
            return jsonify({
                'success': False,
                'message': 'Request body must be valid JSON'
            }), 400

        data = DeviceSessionCreate(**json_data)
        new_session = DeviceSession(**data.model_dump())
        
        db.session.add(new_session)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Device session created successfully',
            'data': DeviceSessionOut.model_validate(new_session).model_dump()
        }), 201

    except ValidationError as e:
        return jsonify({
            'success': False,
            'message': 'Validation error',
            'errors': e.errors()
        }), 422


@device_bp.route('/devices/sessions/<int:session_id>/revoke', methods=['PUT'])
@token_required
def revoke_session(current_user, session_id):
    """Revoke a device session"""
    session = DeviceSession.query.get_or_404(session_id)
    session.is_revoked = True
    db.session.commit()
    
    return jsonify({
        'success': True,
        'message': 'Device session revoked successfully'
    })



