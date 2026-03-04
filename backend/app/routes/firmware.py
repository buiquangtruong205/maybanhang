from flask import Blueprint, request, jsonify
from app import db
from app.models import FirmwareUpdate
from app.utils import token_required

firmware_bp = Blueprint('firmware', __name__)

@firmware_bp.route('/firmware/updates', methods=['GET'])
@token_required
def get_firmware_updates(current_user):
    """Get all firmware update history"""
    updates = FirmwareUpdate.query.order_by(FirmwareUpdate.deployed_at.desc()).all()
    
    data = []
    for u in updates:
        data.append({
            'update_id': u.update_id,
            'machine_id': u.machine_id,
            'from_version': u.from_version,
            'to_version': u.to_version,
            'status': u.status,
            'deployed_at': u.deployed_at.isoformat() if u.deployed_at else None,
            'completed_at': u.completed_at.isoformat() if u.completed_at else None
        })
        
    return jsonify({
        'success': True,
        'message': 'Firmware updates retrieved successfully',
        'data': data
    })

@firmware_bp.route('/firmware/updates', methods=['POST'])
@token_required
def create_firmware_update(current_user):
    """Schedule a new firmware update (Stub for UI)"""
    try:
        json_data = request.get_json()
        machine_id = json_data.get('machine_id')
        to_version = json_data.get('to_version')
        
        new_update = FirmwareUpdate(
            machine_id=machine_id,
            from_version=json_data.get('from_version', '1.0.0'),
            to_version=to_version,
            status='pending',
            file_url='http://stub-url/firmware.bin',
            checksum=json_data.get('checksum', 'stub-checksum')
        )
        
        db.session.add(new_update)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Firmware update scheduled',
            'data': {'update_id': new_update.update_id}
        })
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@firmware_bp.route('/firmware/updates/<int:update_id>', methods=['DELETE'])
@token_required
def delete_firmware_update(current_user, update_id):
    """Delete a firmware update record"""
    update = FirmwareUpdate.query.get_or_404(update_id)
    db.session.delete(update)
    db.session.commit()
    return jsonify({'success': True, 'message': 'Deleted successfully'})
