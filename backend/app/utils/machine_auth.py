"""
Machine authentication decorator for IoT devices (ESP/Arduino)
"""
from functools import wraps
from flask import request, jsonify
from app.config import MACHINE_KEYS


def get_machine_id_from_key(machine_key):
    """
    Get machine_id from machine key
    Returns machine_id if key is valid, None otherwise
    """
    return MACHINE_KEYS.get(machine_key)


def machine_key_required(f):
    """
    Decorator để xác thực thiết bị IoT bằng machine_key
    
    Thiết bị gửi key qua:
    - Header: X-Machine-Key: may1
    - Hoặc trong body JSON: {"machine_key": "may1", ...}
    - Hoặc query param: ?machine_key=may1
    """
    @wraps(f)
    def decorated(*args, **kwargs):
        machine_key = None
        
        # Check header first
        machine_key = request.headers.get('X-Machine-Key')
        
        # Then check JSON body
        if not machine_key:
            json_data = request.get_json(force=True, silent=True)
            if json_data:
                machine_key = json_data.get('machine_key')
        
        # Finally check query params
        if not machine_key:
            machine_key = request.args.get('machine_key')
        
        if not machine_key:
            return jsonify({
                'success': False,
                'message': 'Machine key is missing. Provide via X-Machine-Key header, body, or query param.'
            }), 401
        
        # Validate key
        machine_id = get_machine_id_from_key(machine_key)
        if machine_id is None:
            return jsonify({
                'success': False,
                'message': 'Invalid machine key. Access denied.'
            }), 403
        
        # Pass machine_id to the route function
        return f(machine_id, *args, **kwargs)
    
    return decorated
