"""
IoT Security Master Decorator

Layer 5: Authorization (Session + Device Binding)
Layer 6: Fail-Closed Error Handling

Combines all security layers into a single decorator for IoT endpoints.
"""

from functools import wraps
from flask import request, jsonify, g
from typing import Optional, Callable
import logging

from app.utils.security import (
    validate_timestamp, 
    validate_nonce, 
    hmac_verify,
    canonicalize_payload
)

# Configure logging
logger = logging.getLogger('iot_security')


# =============================================================================
# Error Codes (for client debugging without leaking details)
# =============================================================================

class SecurityError:
    """Security error codes - don't leak sensitive details"""
    MISSING_BODY = "E001"
    MISSING_FIELDS = "E002"
    DEVICE_NOT_FOUND = "E003"
    DEVICE_REVOKED = "E004"
    INVALID_SIGNATURE = "E005"
    TIMESTAMP_ERROR = "E006"
    NONCE_ERROR = "E007"
    SESSION_INVALID = "E008"
    CERT_REQUIRED = "E009"
    CERT_INVALID = "E010"
    UNAUTHORIZED = "E011"


def _reject(code: str, reason: str, log_details: str = None):
    """
    Fail-closed response
    
    - Returns generic error to client (don't leak details)
    - Logs detailed reason for debugging
    """
    if log_details:
        logger.warning(f"Security rejected [{code}]: {log_details}")
    else:
        logger.warning(f"Security rejected [{code}]: {reason}")
    
    return jsonify({
        'success': False,
        'error': 'SECURITY_REJECTED',
        'code': code,
        'message': reason  # Generic message only
    }), 403


# =============================================================================
# Certificate-Based Authentication Decorator
# =============================================================================

def machine_cert_required(f: Callable) -> Callable:
    """
    Decorator: Require valid X-Machine-Key
    
    Extracts device_id from machine key
    Passes device_id as first argument to wrapped function
    """
    @wraps(f)
    def decorated(*args, **kwargs):
        # Fall back to X-Machine-Key (Standard for HTTP)
        from app.utils.machine_auth import get_machine_id_from_key
        
        machine_key = request.headers.get('X-Machine-Key')
        if not machine_key:
            json_data = request.get_json(force=True, silent=True)
            if json_data:
                machine_key = json_data.get('machine_key')
        
        if not machine_key:
            return _reject(
                SecurityError.CERT_REQUIRED,
                "Authentication required",
                "Missing machine_key"
            )
        
        client_device_id = get_machine_id_from_key(machine_key)
        if client_device_id is None:
            return _reject(
                SecurityError.CERT_INVALID,
                "Authentication failed",
                f"Invalid machine_key: {machine_key}"
            )
        
        # Store in g for later access
        g.verified_device_id = client_device_id
        
        return f(client_device_id, *args, **kwargs)
    
    return decorated


# =============================================================================
# Master Security Decorator (All Layers)
# =============================================================================

def iot_secure_endpoint(f: Callable) -> Callable:
    """
    Master security decorator for IoT endpoints
    
    Enforces ALL security layers in order:
    1. Machine identity (from machine_key)
    2. Timestamp validation
    3. Nonce validation (anti-replay)
    4. HMAC signature verification
    5. Session verification (optional)
    6. Fail-closed on any error
    
    Request format expected:
    {
        "data": { ... actual payload ... },
        "meta": {
            "timestamp": 1705491082,
            "nonce": "random_hex_string",
            "session_id": "optional_session"
        },
        "signature": "hmac_sha256_hex"
    }
    
    Passes (device_id, data) to wrapped function
    """
    @wraps(f)
    def decorated(device_id: int, *args, **kwargs):
        try:
            # =========================================================
            # Step 1: Parse request body
            # =========================================================
            json_data = request.get_json(force=True, silent=True)
            if not json_data:
                return _reject(
                    SecurityError.MISSING_BODY,
                    "Invalid request",
                    "Missing or invalid JSON body"
                )
            
            data = json_data.get('data')
            meta = json_data.get('meta', {})
            signature = json_data.get('signature')
            
            if not data:
                return _reject(
                    SecurityError.MISSING_FIELDS,
                    "Invalid request format",
                    "Missing 'data' field"
                )
            
            if not signature:
                return _reject(
                    SecurityError.MISSING_FIELDS,
                    "Invalid request format",
                    "Missing 'signature' field"
                )
            
            # =========================================================
            # Step 2: Get device secret key
            # =========================================================
            from app.models import DeviceIdentity, DeviceSession
            
            identity = DeviceIdentity.query.get(device_id)
            if not identity:
                return _reject(
                    SecurityError.DEVICE_NOT_FOUND,
                    "Device not registered",
                    f"No DeviceIdentity for device_id={device_id}"
                )
            
            if identity.status != 'active':
                return _reject(
                    SecurityError.DEVICE_REVOKED,
                    "Device access revoked",
                    f"Device {device_id} status={identity.status}"
                )
            
            # Use device_public_key or dedicated HMAC key
            secret_key = identity.device_public_key
            if not secret_key:
                return _reject(
                    SecurityError.DEVICE_NOT_FOUND,
                    "Device not provisioned",
                    f"Device {device_id} has no secret key"
                )
            
            # =========================================================
            # Step 3: Validate timestamp (cheapest check first)
            # =========================================================
            timestamp = meta.get('timestamp')
            if not timestamp:
                return _reject(
                    SecurityError.MISSING_FIELDS,
                    "Invalid request format",
                    "Missing 'timestamp' in meta"
                )
            
            try:
                timestamp = int(timestamp)
            except (ValueError, TypeError):
                return _reject(
                    SecurityError.TIMESTAMP_ERROR,
                    "Invalid timestamp",
                    f"Timestamp not integer: {timestamp}"
                )
            
            valid, error = validate_timestamp(timestamp)
            if not valid:
                return _reject(
                    SecurityError.TIMESTAMP_ERROR,
                    "Request expired",
                    error
                )
            
            # =========================================================
            # Step 4: Validate nonce (anti-replay)
            # =========================================================
            nonce = meta.get('nonce')
            if not nonce:
                return _reject(
                    SecurityError.MISSING_FIELDS,
                    "Invalid request format",
                    "Missing 'nonce' in meta"
                )
            
            valid, error = validate_nonce(device_id, nonce)
            if not valid:
                return _reject(
                    SecurityError.NONCE_ERROR,
                    "Request rejected",
                    error
                )
            
            # =========================================================
            # Step 5: Validate HMAC signature (most expensive)
            # =========================================================
            payload_to_verify = {
                'data': data,
                'meta': {
                    'timestamp': timestamp,
                    'nonce': nonce
                }
            }
            
            if not hmac_verify(secret_key, payload_to_verify, signature):
                return _reject(
                    SecurityError.INVALID_SIGNATURE,
                    "Authentication failed",
                    f"HMAC mismatch for device {device_id}"
                )
            
            # =========================================================
            # Step 6: Validate session (optional)
            # =========================================================
            session_id = meta.get('session_id')
            if session_id:
                session = DeviceSession.query.filter_by(
                    machine_id=device_id,
                    session_id=session_id,
                    is_revoked=False
                ).first()
                
                if not session:
                    return _reject(
                        SecurityError.SESSION_INVALID,
                        "Session invalid",
                        f"Session {session_id} not found or revoked"
                    )
                
                # Optional: Check session not expired
                from datetime import datetime
                if session.expires_at and session.expires_at < datetime.utcnow():
                    return _reject(
                        SecurityError.SESSION_INVALID,
                        "Session expired",
                        f"Session {session_id} expired"
                    )
            
            # =========================================================
            # All checks passed - call the actual handler
            # =========================================================
            logger.info(f"✅ Request authorized: device={device_id}, endpoint={request.path}")
            
            return f(device_id, data, *args, **kwargs)
            
        except Exception as e:
            # Fail-closed: any unexpected exception = reject
            logger.exception(f"Security error for device {device_id}: {e}")
            return _reject(
                SecurityError.UNAUTHORIZED,
                "Internal security error",
                f"Exception: {type(e).__name__}: {str(e)}"
            )
    
    return decorated


# =============================================================================
# Audit Logging Decorator
# =============================================================================

def audit_iot_request(f: Callable) -> Callable:
    """
    Decorator: Log IoT requests for audit trail
    
    Logs (without sensitive data):
    - device_id
    - endpoint
    - result (success/fail)
    - reason_code
    - cert serial (if available)
    - request_id (if provided)
    """
    @wraps(f)
    def decorated(*args, **kwargs):
        from app.models import ApiAuditLog
        from app import db
        import hashlib
        
        device_id = g.get('verified_device_id')
        request_id = request.headers.get('X-Request-ID', '')
        
        # Hash payload for audit (don't store raw)
        json_data = request.get_json(force=True, silent=True) or {}
        payload_hash = hashlib.sha256(
            str(json_data).encode()
        ).hexdigest()[:32]
        
        try:
            response = f(*args, **kwargs)
            
            # Extract response code
            if isinstance(response, tuple):
                response_code = response[1]
            else:
                response_code = 200
            
            # Log to database
            try:
                audit = ApiAuditLog(
                    machine_id=device_id,
                    endpoint=request.path,
                    method=request.method,
                    ip_address=request.remote_addr,
                    response_code=response_code,
                    payload_hash=payload_hash,
                    signature_ok=(response_code == 200)
                )
                db.session.add(audit)
                db.session.commit()
            except Exception as e:
                logger.error(f"Failed to write audit log: {e}")
            
            return response
            
        except Exception as e:
            # Log failed request
            try:
                audit = ApiAuditLog(
                    machine_id=device_id,
                    endpoint=request.path,
                    method=request.method,
                    ip_address=request.remote_addr,
                    response_code=500,
                    payload_hash=payload_hash,
                    signature_ok=False
                )
                db.session.add(audit)
                db.session.commit()
            except Exception:
                pass
            raise
    
    return decorated


# =============================================================================
# Combined Decorator for Maximum Security
# =============================================================================

def secure_iot_route(f: Callable) -> Callable:
    """
    All-in-one decorator for secure IoT routes
    
    Combines:
    1. machine_cert_required (machine_key)
    2. iot_secure_endpoint (HMAC, timestamp, nonce)
    3. audit_iot_request (logging)
    
    Usage:
        @iot_bp.route('/iot/secure-endpoint', methods=['POST'])
        @secure_iot_route
        def my_endpoint(device_id, data):
            # device_id is verified
            # data is the validated payload
            return jsonify({'success': True})
    """
    @machine_cert_required
    @iot_secure_endpoint
    @audit_iot_request
    @wraps(f)
    def decorated(*args, **kwargs):
        return f(*args, **kwargs)
    
    return decorated
