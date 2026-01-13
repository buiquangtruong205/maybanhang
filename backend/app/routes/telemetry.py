from flask import Blueprint, request, jsonify
from pydantic import ValidationError
from app import db
from app.models import TelemetryLog
from app.schemas import TelemetryLogCreate, TelemetryLogOut
from app.utils import token_required

telemetry_bp = Blueprint('telemetry', __name__)


@telemetry_bp.route('/telemetry', methods=['GET'])
@token_required
def get_telemetry_logs(current_user):
    """Get recent telemetry logs"""
    logs = TelemetryLog.query.order_by(TelemetryLog.ts.desc()).limit(100).all()
    return jsonify({
        'success': True,
        'message': 'Telemetry logs retrieved successfully',
        'data': [TelemetryLogOut.model_validate(l).model_dump() for l in logs]
    })


@telemetry_bp.route('/telemetry/machine/<int:machine_id>', methods=['GET'])
@token_required
def get_telemetry_by_machine(current_user, machine_id):
    """Get telemetry logs for a machine"""
    logs = TelemetryLog.query.filter_by(machine_id=machine_id).order_by(TelemetryLog.ts.desc()).limit(100).all()
    return jsonify({
        'success': True,
        'message': 'Telemetry logs retrieved successfully',
        'data': [TelemetryLogOut.model_validate(l).model_dump() for l in logs]
    })


@telemetry_bp.route('/telemetry/machine/<int:machine_id>/latest', methods=['GET'])
def get_latest_telemetry(machine_id):
    """Get latest telemetry for a machine (public for device)"""
    log = TelemetryLog.query.filter_by(machine_id=machine_id).order_by(TelemetryLog.ts.desc()).first()
    if not log:
        return jsonify({
            'success': False,
            'message': 'No telemetry data found'
        }), 404
    
    return jsonify({
        'success': True,
        'message': 'Latest telemetry retrieved successfully',
        'data': TelemetryLogOut.model_validate(log).model_dump()
    })


@telemetry_bp.route('/telemetry', methods=['POST'])
def create_telemetry_log():
    """Create a new telemetry log (called by IoT device)"""
    try:
        json_data = request.get_json(force=True, silent=True)
        if not json_data:
            return jsonify({
                'success': False,
                'message': 'Request body must be valid JSON'
            }), 400

        data = TelemetryLogCreate(**json_data)
        new_log = TelemetryLog(
            machine_id=data.machine_id,
            temperature=data.temperature,
            humidity=data.humidity,
            voltage=data.voltage,
            door_open=data.door_open,
            metrics_json=data.metrics_json
        )
        
        db.session.add(new_log)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Telemetry log created successfully',
            'data': TelemetryLogOut.model_validate(new_log).model_dump()
        }), 201

    except ValidationError as e:
        return jsonify({
            'success': False,
            'message': 'Validation error',
            'errors': e.errors()
        }), 422


@telemetry_bp.route('/telemetry/machine/<int:machine_id>/alerts', methods=['GET'])
@token_required
def get_telemetry_alerts(current_user, machine_id):
    """Get telemetry alerts (abnormal readings)"""
    # Example: door open or abnormal temperature
    logs = TelemetryLog.query.filter(
        TelemetryLog.machine_id == machine_id,
        db.or_(
            TelemetryLog.door_open == True,
            TelemetryLog.temperature > 35,
            TelemetryLog.temperature < 0
        )
    ).order_by(TelemetryLog.ts.desc()).limit(50).all()
    
    return jsonify({
        'success': True,
        'message': 'Telemetry alerts retrieved successfully',
        'data': [TelemetryLogOut.model_validate(l).model_dump() for l in logs]
    })
