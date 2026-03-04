"""
Security utilities for IoT communication

Layer 3: Data Integrity (HMAC-SHA256)
Layer 4: Anti-Replay (Nonce + Timestamp)
"""

import hmac
import hashlib
import json
import time
import secrets
from typing import Tuple, Optional
from functools import lru_cache


# =============================================================================
# Layer 3: HMAC-SHA256 for Data Integrity
# =============================================================================

def canonicalize_payload(data: dict) -> str:
    """
    Serialize payload to canonical form for HMAC
    
    Rules:
    - Sort keys alphabetically (recursive)
    - No whitespace
    - UTF-8 encoding
    
    This ensures ESP32 and Server produce identical strings for same data.
    """
    return json.dumps(data, sort_keys=True, separators=(',', ':'), ensure_ascii=False)


def hmac_sign(key: str, data: dict) -> str:
    """
    Compute HMAC-SHA256 signature
    
    Args:
        key: Secret key (shared between server and device)
        data: Payload to sign (will be canonicalized)
    
    Returns:
        Hex-encoded HMAC signature
    """
    payload = canonicalize_payload(data)
    signature = hmac.new(
        key.encode('utf-8'),
        payload.encode('utf-8'),
        hashlib.sha256
    ).hexdigest()
    return signature


def hmac_verify(key: str, data: dict, signature: str) -> bool:
    """
    Verify HMAC-SHA256 signature (constant-time comparison)
    
    Args:
        key: Secret key
        data: Payload that was signed
        signature: Hex-encoded signature to verify
    
    Returns:
        True if signature is valid, False otherwise
    """
    expected = hmac_sign(key, data)
    return hmac.compare_digest(signature.lower(), expected.lower())


# =============================================================================
# Layer 4: Anti-Replay Protection
# =============================================================================

# Nonce storage - simple in-memory implementation
# Production: use Redis with TTL
_nonce_cache: dict[str, float] = {}

# Configuration
TIMESTAMP_TOLERANCE_SECONDS = 30  # Allow ±30 seconds clock drift
NONCE_TTL_SECONDS = 120  # Keep nonces for 2 minutes
MAX_CACHE_SIZE = 10000  # Maximum nonces to store


def validate_timestamp(timestamp: int, tolerance_seconds: int = None) -> Tuple[bool, str]:
    """
    Validate timestamp is within acceptable window
    
    Args:
        timestamp: Unix timestamp from request
        tolerance_seconds: Allowed clock drift (default: 30s)
    
    Returns:
        (is_valid, error_message)
    """
    if tolerance_seconds is None:
        tolerance_seconds = TIMESTAMP_TOLERANCE_SECONDS
    
    now = int(time.time())
    diff = now - timestamp
    
    if abs(diff) > tolerance_seconds:
        if diff > 0:
            return False, f"Timestamp too old (diff={diff}s, max={tolerance_seconds}s)"
        else:
            return False, f"Timestamp in future (diff={diff}s, max={tolerance_seconds}s)"
    
    return True, ""


def validate_nonce(device_id: int, nonce: str) -> Tuple[bool, str]:
    """
    Validate nonce has not been used before (anti-replay)
    
    Args:
        device_id: Device identifier
        nonce: Random nonce from request
    
    Returns:
        (is_valid, error_message)
    """
    if not nonce or len(nonce) < 16:
        return False, "Nonce too short (min 16 chars)"
    
    # Create unique key
    cache_key = f"{device_id}:{nonce}"
    
    # Check if already used
    if cache_key in _nonce_cache:
        return False, "Nonce already used (replay detected)"
    
    # Store with timestamp
    _nonce_cache[cache_key] = time.time()
    
    # Cleanup old entries if cache too large
    _cleanup_nonce_cache()
    
    return True, ""


def _cleanup_nonce_cache():
    """Remove expired nonces from cache"""
    global _nonce_cache
    
    if len(_nonce_cache) > MAX_CACHE_SIZE:
        now = time.time()
        cutoff = now - NONCE_TTL_SECONDS
        
        # Remove old entries
        _nonce_cache = {
            k: v for k, v in _nonce_cache.items()
            if v > cutoff
        }


def generate_nonce(length: int = 16) -> str:
    """
    Generate a cryptographically secure random nonce
    
    Args:
        length: Number of random bytes (default: 16 = 32 hex chars)
    
    Returns:
        Hex-encoded random string
    """
    return secrets.token_hex(length)


def generate_timestamp() -> int:
    """
    Generate current Unix timestamp
    
    Returns:
        Current time as Unix timestamp (seconds)
    """
    return int(time.time())


# =============================================================================
# Combined Validation
# =============================================================================

def validate_request_security(
    device_id: int,
    data: dict,
    timestamp: int,
    nonce: str,
    signature: str,
    secret_key: str
) -> Tuple[bool, str]:
    """
    Validate all security layers for a request
    
    Args:
        device_id: Device identifier
        data: Request payload
        timestamp: Unix timestamp
        nonce: Random nonce
        signature: HMAC signature
        secret_key: Device's secret key
    
    Returns:
        (is_valid, error_message)
    
    Order of checks (fail-fast):
        1. Timestamp (cheapest check)
        2. Nonce (cache lookup)
        3. HMAC (most expensive)
    """
    # 1. Validate timestamp first (cheapest)
    valid, error = validate_timestamp(timestamp)
    if not valid:
        return False, f"TIMESTAMP_ERROR: {error}"
    
    # 2. Validate nonce (cache lookup)
    valid, error = validate_nonce(device_id, nonce)
    if not valid:
        return False, f"NONCE_ERROR: {error}"
    
    # 3. Validate HMAC (most expensive - do last)
    payload_to_verify = {
        'data': data,
        'meta': {
            'timestamp': timestamp,
            'nonce': nonce
        }
    }
    
    if not hmac_verify(secret_key, payload_to_verify, signature):
        return False, "HMAC_ERROR: Invalid signature"
    
    return True, ""


# =============================================================================
# ESP32 Helper - Generate test request
# =============================================================================

def create_signed_request(device_id: int, data: dict, secret_key: str) -> dict:
    """
    Create a properly signed request (for testing)
    
    Args:
        device_id: Device identifier
        data: Payload data
        secret_key: Device's secret key
    
    Returns:
        Complete request structure with signature
    """
    timestamp = generate_timestamp()
    nonce = generate_nonce()
    
    payload_to_sign = {
        'data': data,
        'meta': {
            'timestamp': timestamp,
            'nonce': nonce
        }
    }
    
    signature = hmac_sign(secret_key, payload_to_sign)
    
    return {
        'data': data,
        'meta': {
            'timestamp': timestamp,
            'nonce': nonce,
            'device_id': device_id
        },
        'signature': signature
    }


# =============================================================================
# Backward Compatible Request Parser
# =============================================================================

def parse_secure_request(json_data: dict, device_id: int = None, secret_key: str = None) -> Tuple[dict, Optional[str]]:
    """
    Parse request body - supports both old and new secure format
    
    Old format (backward compatible):
        {"status": "online", "temperature": 25.5}
        
    New secure format:
        {
            "data": {"status": "online"},
            "meta": {"timestamp": ..., "nonce": ..., "device_id": ...},
            "signature": "hmac..."
        }
    
    Args:
        json_data: Raw JSON body from request
        device_id: Device ID from machine_key (for backward compat)
        secret_key: Optional secret key for HMAC validation
    
    Returns:
        (data, error_code)
        - data: The actual payload data
        - error_code: None if OK, error code string if failed
    """
    if not json_data:
        return {}, None
    
    # Check if this is new secure format
    if 'data' in json_data and 'signature' in json_data:
        # New secure format - validate if secret_key provided
        data = json_data.get('data', {})
        meta = json_data.get('meta', {})
        signature = json_data.get('signature', '')
        
        timestamp = meta.get('timestamp')
        nonce = meta.get('nonce')
        req_device_id = meta.get('device_id', device_id)
        
        # Validate security if secret_key provided
        if secret_key:
            # Validate timestamp
            if timestamp:
                try:
                    valid, error = validate_timestamp(int(timestamp))
                    if not valid:
                        return {}, 'E006'  # Timestamp error
                except (ValueError, TypeError):
                    return {}, 'E006'
            
            # Validate nonce
            if nonce:
                valid, error = validate_nonce(req_device_id or 0, nonce)
                if not valid:
                    return {}, 'E007'  # Nonce error (replay)
            
            # Validate HMAC
            if signature:
                payload_to_verify = {
                    'data': data,
                    'meta': {
                        'timestamp': timestamp,
                        'nonce': nonce
                    }
                }
                if not hmac_verify(secret_key, payload_to_verify, signature):
                    return {}, 'E005'  # HMAC error
        
        return data, None
    else:
        # Old format - return as-is (backward compatible)
        return json_data, None


# Default demo secret key for testing
DEFAULT_DEMO_SECRET = 'demo_secret_key_123'
