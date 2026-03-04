"""
WebAuthn/Passkey Authentication Routes
Giới hạn: Mỗi user chỉ được phép đăng ký 1 credential (1 Passkey).

LƯU Ý: Nếu user bật sync passkey (iCloud Keychain / Google Password Manager),
passkey có thể sync sang thiết bị khác. Đây là "1 credential" không phải "1 thiết bị vật lý".
"""
import base64
import secrets
import json
from datetime import datetime, timedelta
from flask import Blueprint, request, jsonify, current_app
from werkzeug.security import check_password_hash
from webauthn import (
    generate_registration_options,
    verify_registration_response,
    generate_authentication_options,
    verify_authentication_response,
    options_to_json
)
from webauthn.helpers.structs import (
    AuthenticatorSelectionCriteria,
    UserVerificationRequirement,
    ResidentKeyRequirement,
    PublicKeyCredentialDescriptor,
    AuthenticatorTransport
)
from webauthn.helpers.cose import COSEAlgorithmIdentifier
from app import db
from app.models import User, WebAuthnCredential
from app.utils import token_required, generate_token

webauthn_bp = Blueprint('webauthn', __name__)

# In-memory challenge storage với expiry (trong production nên dùng Redis)
# Format: { key: { 'challenge': bytes, 'user_id': int|None, 'created_at': datetime } }
_challenges = {}

# Challenge expiry time in seconds
CHALLENGE_EXPIRY_SECONDS = 120  # 2 phút


def cleanup_expired_challenges():
    """Xóa các challenge đã hết hạn"""
    now = datetime.utcnow()
    expired_keys = [
        key for key, data in _challenges.items()
        if now - data.get('created_at', now) > timedelta(seconds=CHALLENGE_EXPIRY_SECONDS)
    ]
    for key in expired_keys:
        del _challenges[key]


def get_rp_id():
    """
    Lấy Relying Party ID từ request hoặc config.
    RP ID là hostname (không bao gồm port).
    """
    # Ưu tiên lấy từ config nếu đã set
    config_rp_id = current_app.config.get('WEBAUTHN_RP_ID')
    if config_rp_id:
        return config_rp_id
    
    # Tự động detect từ request
    host = request.host.split(':')[0]  # Bỏ port
    return host


def get_rp_name():
    """Lấy Relying Party Name"""
    return current_app.config.get('WEBAUTHN_RP_NAME', 'Vending Machine Manager')


def get_origin():
    """
    Lấy expected origin từ request.
    Origin = scheme + host (bao gồm port).
    """
    # Ưu tiên lấy từ config nếu đã set
    config_origin = current_app.config.get('WEBAUTHN_ORIGIN')
    if config_origin:
        return config_origin
    
    # Tự động detect từ request
    # request.host_url trả về "http://192.168.0.107:5000/" 
    origin = request.host_url.rstrip('/')
    return origin



def parse_transports(transports_list):
    """Parse transports list to JSON string for storage"""
    if not transports_list:
        return None
    return json.dumps(transports_list)


# =======================
# REGISTRATION ENDPOINTS
# =======================

@webauthn_bp.route('/webauthn/register/begin', methods=['POST'])
@token_required
def webauthn_register_begin(current_user):
    """
    Bước 1: Khởi tạo đăng ký Passkey.
    Yêu cầu: User phải đăng nhập trước.
    """
    try:
        # Cleanup expired challenges
        cleanup_expired_challenges()
        
        # Kiểm tra user đã có Passkey chưa (chỉ cho phép 1 credential)
        existing_credential = WebAuthnCredential.query.filter_by(
            user_id=current_user.user_id
        ).first()
        
        if existing_credential:
            return jsonify({
                'success': False,
                'message': 'Bạn đã đăng ký Passkey. Mỗi tài khoản chỉ được phép 1 Passkey.'
            }), 400
        
        # Tạo registration options
        options = generate_registration_options(
            rp_id=get_rp_id(),
            rp_name=get_rp_name(),
            user_id=str(current_user.user_id).encode(),
            user_name=current_user.username,
            user_display_name=current_user.username,
            authenticator_selection=AuthenticatorSelectionCriteria(
                resident_key=ResidentKeyRequirement.PREFERRED,
                user_verification=UserVerificationRequirement.PREFERRED
            ),
            supported_pub_key_algs=[
                COSEAlgorithmIdentifier.ECDSA_SHA_256,
                COSEAlgorithmIdentifier.RSASSA_PKCS1_v1_5_SHA_256
            ]
        )
        
        # Lưu challenge với timestamp để expire
        _challenges[current_user.user_id] = {
            'challenge': options.challenge,
            'created_at': datetime.utcnow()
        }
        
        return jsonify({
            'success': True,
            'data': options_to_json(options)
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500


@webauthn_bp.route('/webauthn/register/complete', methods=['POST'])
@token_required
def webauthn_register_complete(current_user):
    """
    Bước 2: Hoàn thành đăng ký Passkey.
    Lưu credential vào database.
    """
    try:
        # Kiểm tra lại (double check)
        existing_credential = WebAuthnCredential.query.filter_by(
            user_id=current_user.user_id
        ).first()
        
        if existing_credential:
            return jsonify({
                'success': False,
                'message': 'Bạn đã đăng ký Passkey. Mỗi tài khoản chỉ được phép 1 Passkey.'
            }), 400
        
        # Lấy challenge đã lưu
        challenge_data = _challenges.get(current_user.user_id)
        if not challenge_data:
            return jsonify({
                'success': False,
                'message': 'Session đã hết hạn. Vui lòng thử lại.'
            }), 400
        
        # Kiểm tra challenge expiry
        if datetime.utcnow() - challenge_data['created_at'] > timedelta(seconds=CHALLENGE_EXPIRY_SECONDS):
            del _challenges[current_user.user_id]
            return jsonify({
                'success': False,
                'message': 'Challenge đã hết hạn. Vui lòng thử lại.'
            }), 400
        
        challenge = challenge_data['challenge']
        
        # Lấy response từ client
        json_data = request.get_json(force=True, silent=True)
        if not json_data:
            return jsonify({
                'success': False,
                'message': 'Request body must be valid JSON'
            }), 400
        
        # Verify registration response
        verification = verify_registration_response(
            credential=json_data,
            expected_challenge=challenge,
            expected_rp_id=get_rp_id(),
            expected_origin=get_origin()
        )
        
        # Lấy transports từ response (nếu có)
        transports = None
        if 'response' in json_data and 'transports' in json_data['response']:
            transports = parse_transports(json_data['response']['transports'])
        
        # Lưu credential vào database
        new_credential = WebAuthnCredential(
            user_id=current_user.user_id,
            credential_id=verification.credential_id,
            public_key=verification.credential_public_key,
            sign_count=verification.sign_count,
            transports=transports,
            aaguid=str(verification.aaguid) if verification.aaguid else None,
            device_name=json_data.get('device_name', 'Passkey Device')
        )
        
        db.session.add(new_credential)
        db.session.commit()
        
        # Xóa challenge
        del _challenges[current_user.user_id]
        
        return jsonify({
            'success': True,
            'message': 'Đăng ký Passkey thành công!'
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': f'Đăng ký thất bại: {str(e)}'
        }), 500


# =======================
# AUTHENTICATION ENDPOINTS
# =======================

@webauthn_bp.route('/webauthn/login/begin', methods=['POST'])
def webauthn_login_begin():
    """
    Bước 1: Khởi tạo đăng nhập bằng Passkey.
    Không yêu cầu đăng nhập trước.
    """
    try:
        # Cleanup expired challenges
        cleanup_expired_challenges()
        
        json_data = request.get_json(force=True, silent=True)
        username = json_data.get('username') if json_data else None
        
        # Nếu có username, tìm credential của user đó
        allow_credentials = []
        user_id_for_challenge = None
        credential_transports = None
        
        if username:
            user = User.query.filter_by(username=username).first()
            if user:
                credential = WebAuthnCredential.query.filter_by(
                    user_id=user.user_id
                ).first()
                
                if credential:
                    # Parse transports nếu có
                    transports = None
                    if credential.transports:
                        try:
                            transports_list = json.loads(credential.transports)
                            transports = [AuthenticatorTransport(t) for t in transports_list]
                        except (json.JSONDecodeError, ValueError):
                            pass
                    
                    allow_credentials.append(
                        PublicKeyCredentialDescriptor(
                            id=credential.credential_id,
                            transports=transports
                        )
                    )
                    user_id_for_challenge = user.user_id
                else:
                    return jsonify({
                        'success': False,
                        'message': 'Tài khoản này chưa đăng ký Passkey.'
                    }), 400
            else:
                return jsonify({
                    'success': False,
                    'message': 'Không tìm thấy tài khoản.'
                }), 404
        
        # Tạo authentication options
        options = generate_authentication_options(
            rp_id=get_rp_id(),
            allow_credentials=allow_credentials if allow_credentials else None,
            user_verification=UserVerificationRequirement.PREFERRED
        )
        
        # Lưu challenge với session key và timestamp
        session_key = f"login_{secrets.token_hex(16)}"
        _challenges[session_key] = {
            'challenge': options.challenge,
            'user_id': user_id_for_challenge,
            'created_at': datetime.utcnow()
        }
        
        return jsonify({
            'success': True,
            'data': options_to_json(options),
            'session_key': session_key
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500


@webauthn_bp.route('/webauthn/login/complete', methods=['POST'])
def webauthn_login_complete():
    """
    Bước 2: Hoàn thành đăng nhập bằng Passkey.
    Trả về JWT token nếu thành công.
    """
    try:
        json_data = request.get_json(force=True, silent=True)
        if not json_data:
            return jsonify({
                'success': False,
                'message': 'Request body must be valid JSON'
            }), 400
        
        session_key = json_data.get('session_key')
        if not session_key or session_key not in _challenges:
            return jsonify({
                'success': False,
                'message': 'Session đã hết hạn. Vui lòng thử lại.'
            }), 400
        
        challenge_data = _challenges[session_key]
        
        # Kiểm tra challenge expiry
        if datetime.utcnow() - challenge_data['created_at'] > timedelta(seconds=CHALLENGE_EXPIRY_SECONDS):
            del _challenges[session_key]
            return jsonify({
                'success': False,
                'message': 'Challenge đã hết hạn. Vui lòng thử lại.'
            }), 400
        
        challenge = challenge_data['challenge']
        
        # Tìm credential từ credential_id trong response
        raw_id = json_data.get('rawId')
        if not raw_id:
            return jsonify({
                'success': False,
                'message': 'Missing credential ID'
            }), 400
        
        # Decode credential_id (base64url)
        credential_id = base64.urlsafe_b64decode(raw_id + '==')
        
        # Tìm credential trong database
        credential = WebAuthnCredential.query.filter_by(
            credential_id=credential_id
        ).first()
        
        if not credential:
            return jsonify({
                'success': False,
                'message': 'Passkey không hợp lệ hoặc không tồn tại.'
            }), 401
        
        # Verify authentication response
        verification = verify_authentication_response(
            credential=json_data,
            expected_challenge=challenge,
            expected_rp_id=get_rp_id(),
            expected_origin=get_origin(),
            credential_public_key=credential.public_key,
            credential_current_sign_count=credential.sign_count
        )
        
        # Cập nhật sign_count VÀ last_used_at
        credential.sign_count = verification.new_sign_count
        credential.last_used_at = datetime.utcnow()
        db.session.commit()
        
        # Xóa challenge
        del _challenges[session_key]
        
        # Lấy user và tạo JWT token
        user = User.query.get(credential.user_id)
        if not user:
            return jsonify({
                'success': False,
                'message': 'User not found'
            }), 401
        
        token = generate_token(user.username)
        
        return jsonify({
            'success': True,
            'message': 'Đăng nhập thành công!',
            'data': {
                'access_token': token,
                'token_type': 'bearer',
                'username': user.username
            }
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': f'Đăng nhập thất bại: {str(e)}'
        }), 401


# =======================
# UTILITY ENDPOINTS
# =======================

@webauthn_bp.route('/webauthn/status', methods=['GET'])
@token_required
def webauthn_status(current_user):
    """Kiểm tra trạng thái Passkey của user hiện tại."""
    credential = WebAuthnCredential.query.filter_by(
        user_id=current_user.user_id
    ).first()
    
    return jsonify({
        'success': True,
        'data': {
            'has_passkey': credential is not None,
            'device_name': credential.device_name if credential else None,
            'created_at': credential.created_at.isoformat() if credential else None,
            'last_used_at': credential.last_used_at.isoformat() if credential and credential.last_used_at else None
        }
    })


@webauthn_bp.route('/webauthn/remove', methods=['DELETE'])
@token_required
def webauthn_remove(current_user):
    """
    Xóa Passkey của user hiện tại.
    YÊU CẦU: Password confirmation để bảo vệ việc xóa.
    """
    try:
        # Lấy password từ request để re-authenticate
        json_data = request.get_json(force=True, silent=True)
        password = json_data.get('password') if json_data else None
        
        if not password:
            return jsonify({
                'success': False,
                'message': 'Vui lòng nhập mật khẩu để xác nhận xóa Passkey.',
                'require_password': True
            }), 400
        
        # Verify password
        if not check_password_hash(current_user.password, password):
            return jsonify({
                'success': False,
                'message': 'Mật khẩu không chính xác.'
            }), 401
        
        # Tìm và xóa credential
        credential = WebAuthnCredential.query.filter_by(
            user_id=current_user.user_id
        ).first()
        
        if not credential:
            return jsonify({
                'success': False,
                'message': 'Bạn chưa đăng ký Passkey.'
            }), 404
        
        db.session.delete(credential)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Đã xóa Passkey thành công.'
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500
