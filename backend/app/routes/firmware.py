from flask import Blueprint, request, jsonify
from datetime import datetime
from app import db
from app.models import FirmwareUpdate, Machine
from app.utils import token_required
from app.utils.machine_auth import machine_key_required

firmware_bp = Blueprint('firmware', __name__)

@firmware_bp.route('/firmware/report-progress', methods=['POST'])
@machine_key_required
def report_ota_progress(machine_id):
    """
    Máy báo cáo tiến độ tải Firmware (0-100%)
    """
    try:
        json_data = request.get_json(force=True, silent=True) or {}
        update_id = json_data.get('update_id')
        progress = json_data.get('progress', 0)
        status = json_data.get('status') # downloading, installing, completed, failed

        if not update_id:
            return jsonify({'success': False, 'message': 'update_id is required'}), 400

        update = FirmwareUpdate.query.get(update_id)
        if not update or update.machine_id != machine_id:
            return jsonify({'success': False, 'message': 'Invalid update_id for this machine'}), 404

        update.progress = progress
        if status:
            update.status = status
            if status == 'completed':
                update.completed_at = datetime.utcnow()
        
        db.session.commit()
        return jsonify({'success': True})

    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

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
            'progress': u.progress or 0,
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
    """Schedule a new firmware update (Single or Batch)"""
    try:
        json_data = request.get_json()
        machine_ids = json_data.get('machine_ids', []) # List of IDs
        single_id = json_data.get('machine_id') # Single ID for backward compatibility
        to_version = json_data.get('to_version')
        from_version = json_data.get('from_version', '1.0.0')
        file_url = json_data.get('file_url', 'http://stub-url/firmware.bin')
        checksum = json_data.get('checksum', 'stub-checksum')
        
        # Combine into a unique set of IDs
        target_ids = set(machine_ids)
        if single_id:
            target_ids.add(single_id)
            
        if not target_ids:
            return jsonify({'success': False, 'message': 'No machine_id or machine_ids provided'}), 400
            
        from app.utils.mqtt import send_machine_command
        created_updates = []
        
        for mid in target_ids:
            # Check if machine exists
            machine = Machine.query.get(mid)
            if not machine:
                continue # Skip invalid machines
                
            new_update = FirmwareUpdate(
                machine_id=mid,
                from_version=from_version,
                to_version=to_version,
                status='pending',
                file_url=file_url,
                checksum=checksum
            )
            db.session.add(new_update)
            db.session.flush() # Get ID
            
            # Trigger OTA via MQTT
            # Command format: OTA_UPDATE:<update_id>:<url>:<checksum>
            ota_payload = f"{new_update.update_id}:{new_update.file_url}:{new_update.checksum}"
            send_machine_command(mid, "OTA_UPDATE", ota_payload)
            
            created_updates.append({'machine_id': mid, 'update_id': new_update.update_id})
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': f'Firmware update scheduled for {len(created_updates)} machines',
            'data': created_updates
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500

@firmware_bp.route('/firmware/updates/<int:update_id>', methods=['DELETE'])
@token_required
def delete_firmware_update(current_user, update_id):
    """Delete a firmware update record"""
    update = FirmwareUpdate.query.get_or_404(update_id)
    db.session.delete(update)
    db.session.commit()
    return jsonify({'success': True, 'message': 'Deleted successfully'})
