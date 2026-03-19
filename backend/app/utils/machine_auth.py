"""
Machine authentication decorator for IoT devices (ESP/Arduino)
"""
from functools import wraps
from flask import request, jsonify, current_app
from app.models import Machine, User, DeviceIdentity
from app.utils.auth import get_jwt_signing_key
import jwt


def _mask_machine_key(machine_key):
    if not machine_key:
        return "<empty>"
    if len(machine_key) <= 4:
        return "****"
    return f"{machine_key[:4]}***"


def _validate_machine_key(machine_key):
    """
    Validate machine key and return (machine, error_message, status_code).
    """
    if not machine_key:
        return None, 'Machine key is missing. Provide via X-Machine-Key header, body, or query param.', 401
    if machine_key == current_app.config.get('MASTER_REGISTRATION_KEY'):
        # If it's a MASTER key, try to find the machine by MAC if provided in the body
        json_data = request.get_json(force=True, silent=True) or {}
        mac_address = json_data.get('mac_address')
        if mac_address:
             identity = DeviceIdentity.query.filter_by(mac_address=mac_address).first()
             if identity:
                 machine = Machine.query.get(identity.machine_id)
                 if machine:
                     return machine, None, None
        return "MASTER", None, None

    machine = Machine.query.filter_by(secret_key=machine_key).first()
    if not machine:
        return None, f'Invalid machine key: {_mask_machine_key(machine_key)}. Access denied.', 403

    if machine.status not in {"active", "online"}:
        return None, f'Machine {machine.machine_id} is inactive (status: {machine.status}). Access denied.', 403

    return machine, None, None


def get_machine_id_from_key(machine_key):
    """
    Get machine_id from machine key
    Returns machine_id if key is valid, None otherwise
    """
    machine, _, _ = _validate_machine_key(machine_key)
    if not machine or machine == "MASTER":
        return None
    return machine.machine_id


def machine_key_required(f):
    """
    Decorator để xác thực thiết bị IoT bằng machine_key
    
    Thiết bị gửi key qua:
    - Header: X-Machine-Key: maybanhang-v3
    - Hoặc trong body JSON: {"machine_key": "may1", ...}
    - Hoặc query param: ?machine_key=may1
    """
    @wraps(f)
    def decorated(*args, **kwargs):
        machine_key = None
        
        # Check header first
        machine_key = request.headers.get('X-Machine-Key')
        
        # Then check JSON body (force=True to handle content-type issues)
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
        
        # Validate key and status
        machine, error_message, status_code = _validate_machine_key(machine_key)
        if machine == "MASTER":
            # If it's the MASTER registration key, we need a machine_id from the URL
            url_machine_id = kwargs.get('machine_id')
            if url_machine_id:
                return f(url_machine_id, *args, **kwargs)

            json_data = request.get_json(force=True, silent=True) or {}
            body_machine_id = json_data.get('machine_id')
            if body_machine_id is None:
                return jsonify({
                    'success': False,
                    'message': 'MASTER_REGISTRATION_KEY requires machine_id in the request body or URL.'
                }), 400

            try:
                return f(int(body_machine_id), *args, **kwargs)
            except (TypeError, ValueError):
                return jsonify({
                    'success': False,
                    'message': 'machine_id must be an integer when using MASTER_REGISTRATION_KEY.'
                }), 400

        if not machine:
            current_app.logger.warning(
                "IoT auth failed for key=%s path=%s: %s",
                _mask_machine_key(machine_key),
                request.path,
                error_message
            )
            return jsonify({
                'success': False,
                'message': error_message
            }), status_code
        
        # Pass machine_id to the route function
        return f(machine.machine_id, *args, **kwargs)
    
    return decorated


def multi_auth_required(f):
    """
    Decorator cho phép xác thực bằng một trong hai cách:
    1. Machine Key (X-Machine-Key header) -> truyền machine_id vào hàm.
    2. Admin Token (Authorization Bearer header) -> lấy machine_id từ tham số URL hoặc mặc định.
    
    Sử dụng cho các route mà cả Admin và Máy bán hàng đều cần truy cập.
    """
    @wraps(f)
    def decorated(*args, **kwargs):
        # 1. Thử xác thực bằng Machine Key trước (Ưu tiên cho thiết bị IoT)
        machine_key = request.headers.get('X-Machine-Key')
        machine_error = None
        machine_status_code = None

        if not machine_key:
            json_data = request.get_json(force=True, silent=True)
            if json_data:
                machine_key = json_data.get('machine_key')
        if not machine_key:
            machine_key = request.args.get('machine_key')

        if machine_key:
            machine, machine_error, machine_status_code = _validate_machine_key(machine_key)
            if machine:
                # Nếu route có machine_id trong kwargs (từ URL pattern <int:machine_id>)
                # thì kiểm tra xem key có khớp với machine_id đó không
                url_machine_id = kwargs.get('machine_id')
                if url_machine_id and int(url_machine_id) != machine.machine_id:
                    return jsonify({'success': False, 'message': 'Machine key does not match Machine ID in URL'}), 403
                
                return f(machine.machine_id, *args, **kwargs)

        # 2. Nếu không có Machine Key, thử xác thực bằng Admin Token
        token = request.headers.get('Authorization')
        if token:
            try:
                if token.startswith('Bearer '):
                    token = token[7:]
                
                data = jwt.decode(token, get_jwt_signing_key(), algorithms=["HS256"])
                current_user = User.query.filter_by(username=data['username']).first()
                
                if current_user:
                    # Nếu là Admin, ta lấy machine_id từ URL hoặc mặc định
                    url_machine_id = kwargs.get('machine_id')
                    return f(url_machine_id, *args, **kwargs)
            except:
                pass # Token lỗi thì báo 401 bên dưới

        if machine_error:
            current_app.logger.warning(
                "Multi-auth machine validation failed for key=%s path=%s: %s",
                _mask_machine_key(machine_key),
                request.path,
                machine_error
            )
            return jsonify({
                'success': False,
                'message': machine_error
            }), machine_status_code

        return jsonify({
            'success': False,
            'message': 'Authentication required. Provide valid X-Machine-Key or Admin Token.'
        }), 401
    
    return decorated
