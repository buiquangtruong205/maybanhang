from functools import wraps
from flask import request, jsonify, current_app
from datetime import datetime, timedelta
import hashlib
import jwt
from app.models import User


def get_jwt_signing_key():
    """
    Normalize SECRET_KEY to a minimum 32-byte HMAC key for HS256.
    """
    secret = current_app.config['SECRET_KEY']
    if isinstance(secret, str):
        secret = secret.encode('utf-8')
    if len(secret) < 32:
        return hashlib.sha256(secret).digest()
    return secret


def generate_token(username):
    """Generate JWT token"""
    payload = {
        'username': username,
        'exp': datetime.utcnow() + timedelta(hours=current_app.config['JWT_EXPIRATION_HOURS'])
    }
    return jwt.encode(payload, get_jwt_signing_key(), algorithm="HS256")

def token_required(f):
    """Decorator để bảo vệ routes cần authentication"""
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get('Authorization')
        
        if not token:
            return jsonify({
                'success': False,
                'message': 'Token is missing'
            }), 401
        
        try:
            if token.startswith('Bearer '):
                token = token[7:]
            
            data = jwt.decode(token, get_jwt_signing_key(), algorithms=["HS256"])
            current_user = User.query.filter_by(username=data['username']).first()
            
            if not current_user:
                return jsonify({
                    'success': False,
                    'message': 'User not found'
                }), 401
                
        except jwt.ExpiredSignatureError:
            return jsonify({
                'success': False,
                'message': 'Token has expired'
            }), 401
        except jwt.InvalidTokenError:
            return jsonify({
                'success': False,
                'message': 'Token is invalid'
            }), 401
        
        return f(current_user, *args, **kwargs)
    
    return decorated
