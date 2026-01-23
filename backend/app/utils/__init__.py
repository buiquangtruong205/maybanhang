from app.utils.auth import token_required, generate_token
from app.utils.machine_auth import machine_key_required, get_machine_id_from_key
from app.utils.security import (
    hmac_sign, hmac_verify, canonicalize_payload,
    validate_timestamp, validate_nonce, generate_nonce,
    validate_request_security, create_signed_request,
    parse_secure_request, DEFAULT_DEMO_SECRET
)
from app.utils.iot_security import (
    machine_cert_required, iot_secure_endpoint,
    secure_iot_route, audit_iot_request, SecurityError
)

__all__ = [
    # Auth
    'token_required', 'generate_token',
    'machine_key_required', 'get_machine_id_from_key',
    # Security Layer 3-4
    'hmac_sign', 'hmac_verify', 'canonicalize_payload',
    'validate_timestamp', 'validate_nonce', 'generate_nonce',
    'validate_request_security', 'create_signed_request',
    'parse_secure_request', 'DEFAULT_DEMO_SECRET',
    # IoT Security Layer 5-6
    'machine_cert_required', 'iot_secure_endpoint',
    'secure_iot_route', 'audit_iot_request', 'SecurityError'
]