from flask import Blueprint, request, jsonify
from datetime import datetime
from pydantic import ValidationError
from app import db
from app.models import SecurityEvent, ApiAuditLog, StaffAccessLog
from app.schemas import (
    SecurityEventCreate, SecurityEventOut,
    ApiAuditLogCreate, ApiAuditLogOut,
    StaffAccessLogCreate, StaffAccessLogOut, StaffAccessLogEnd
)
from app.utils import token_required

security_bp = Blueprint('security', __name__)


# ==================== SecurityEvent ====================

@security_bp.route('/security/events', methods=['GET'])
@token_required
def get_security_events(current_user):
    """Get all security events"""
    events = SecurityEvent.query.order_by(SecurityEvent.created_at.desc()).all()
    return jsonify({
        'success': True,
        'message': 'Security events retrieved successfully',
        'data': [SecurityEventOut.model_validate(e).model_dump() for e in events]
    })


@security_bp.route('/security/events/unresolved', methods=['GET'])
@token_required
def get_unresolved_events(current_user):
    """Get unresolved security events"""
    events = SecurityEvent.query.filter_by(is_resolved=False).order_by(SecurityEvent.created_at.desc()).all()
    return jsonify({
        'success': True,
        'message': 'Unresolved events retrieved successfully',
        'data': [SecurityEventOut.model_validate(e).model_dump() for e in events]
    })


@security_bp.route('/security/events', methods=['POST'])
@token_required
def create_security_event(current_user):
    """Create a security event"""
    try:
        json_data = request.get_json(force=True, silent=True)
        if not json_data:
            return jsonify({
                'success': False,
                'message': 'Request body must be valid JSON'
            }), 400

        data = SecurityEventCreate(**json_data)
        new_event = SecurityEvent(**data.model_dump())
        
        db.session.add(new_event)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Security event created successfully',
            'data': SecurityEventOut.model_validate(new_event).model_dump()
        }), 201

    except ValidationError as e:
        return jsonify({
            'success': False,
            'message': 'Validation error',
            'errors': e.errors()
        }), 422


@security_bp.route('/security/events/<int:event_id>/resolve', methods=['PUT'])
@token_required
def resolve_event(current_user, event_id):
    """Mark a security event as resolved"""
    event = SecurityEvent.query.get_or_404(event_id)
    event.is_resolved = True
    event.resolved_at = datetime.utcnow()
    db.session.commit()
    
    return jsonify({
        'success': True,
        'message': 'Security event resolved successfully'
    })


# ==================== ApiAuditLog ====================

@security_bp.route('/security/audit-logs', methods=['GET'])
@token_required
def get_audit_logs(current_user):
    """Get API audit logs"""
    logs = ApiAuditLog.query.order_by(ApiAuditLog.created_at.desc()).limit(100).all()
    return jsonify({
        'success': True,
        'message': 'Audit logs retrieved successfully',
        'data': [ApiAuditLogOut.model_validate(l).model_dump() for l in logs]
    })


@security_bp.route('/security/audit-logs', methods=['POST'])
def create_audit_log():
    """Create an API audit log (internal use)"""
    try:
        json_data = request.get_json(force=True, silent=True)
        if not json_data:
            return jsonify({
                'success': False,
                'message': 'Request body must be valid JSON'
            }), 400

        data = ApiAuditLogCreate(**json_data)
        new_log = ApiAuditLog(**data.model_dump())
        
        db.session.add(new_log)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Audit log created successfully'
        }), 201

    except ValidationError as e:
        return jsonify({
            'success': False,
            'message': 'Validation error',
            'errors': e.errors()
        }), 422


# ==================== StaffAccessLog ====================

@security_bp.route('/security/access-logs', methods=['GET'])
@token_required
def get_access_logs(current_user):
    """Get staff access logs"""
    logs = StaffAccessLog.query.order_by(StaffAccessLog.started_at.desc()).all()
    return jsonify({
        'success': True,
        'message': 'Access logs retrieved successfully',
        'data': [StaffAccessLogOut.model_validate(l).model_dump() for l in logs]
    })


@security_bp.route('/security/access-logs/machine/<int:machine_id>', methods=['GET'])
@token_required
def get_access_logs_by_machine(current_user, machine_id):
    """Get access logs for a machine"""
    logs = StaffAccessLog.query.filter_by(machine_id=machine_id).order_by(StaffAccessLog.started_at.desc()).all()
    return jsonify({
        'success': True,
        'message': 'Access logs retrieved successfully',
        'data': [StaffAccessLogOut.model_validate(l).model_dump() for l in logs]
    })


@security_bp.route('/security/access-logs', methods=['POST'])
@token_required
def create_access_log(current_user):
    """Create a staff access log"""
    try:
        json_data = request.get_json(force=True, silent=True)
        if not json_data:
            return jsonify({
                'success': False,
                'message': 'Request body must be valid JSON'
            }), 400

        data = StaffAccessLogCreate(**json_data)
        new_log = StaffAccessLog(**data.model_dump())
        
        db.session.add(new_log)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Access log created successfully',
            'data': StaffAccessLogOut.model_validate(new_log).model_dump()
        }), 201

    except ValidationError as e:
        return jsonify({
            'success': False,
            'message': 'Validation error',
            'errors': e.errors()
        }), 422


@security_bp.route('/security/access-logs/<int:access_id>/end', methods=['PUT'])
@token_required
def end_access_log(current_user, access_id):
    """End a staff access session"""
    try:
        log = StaffAccessLog.query.get_or_404(access_id)
        
        json_data = request.get_json(force=True, silent=True) or {}
        data = StaffAccessLogEnd(**json_data)
        
        log.ended_at = datetime.utcnow()
        if data.note:
            log.note = data.note
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Access session ended successfully',
            'data': StaffAccessLogOut.model_validate(log).model_dump()
        })

    except ValidationError as e:
        return jsonify({
            'success': False,
            'message': 'Validation error',
            'errors': e.errors()
        }), 422
