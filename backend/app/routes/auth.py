from flask import Blueprint, request, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
from pydantic import ValidationError
from app import db
from app.models import User
from app.schemas import UserCreate, UserOut, Token
from app.utils import token_required, generate_token

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/register', methods=['POST'])
def register():
    try:
        json_data = request.get_json(force=True, silent=True)
        if not json_data:
            return jsonify({
                'success': False,
                'message': 'Request body must be valid JSON'
            }), 400
        data = UserCreate(**json_data)
        
        if User.query.filter_by(username=data.username).first():
            return jsonify({
                'success': False,
                'message': 'Username already exists'
            }), 400
        
        hashed_password = generate_password_hash(data.password)
        new_user = User(username=data.username, password=hashed_password)
        
        db.session.add(new_user)
        db.session.commit()
        
        user_out = UserOut.model_validate(new_user)
        return jsonify({
            'success': True,
            'message': 'User created successfully',
            'data': user_out.model_dump()
        }), 201
    
    except ValidationError as e:
        return jsonify({
            'success': False,
            'message': 'Validation error',
            'errors': e.errors()
        }), 422
    except Exception as e:
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

@auth_bp.route('/login', methods=['POST'])
def login():
    try:
        json_data = request.get_json(force=True, silent=True)
        if not json_data:
            return jsonify({
                'success': False,
                'message': 'Request body must be valid JSON'
            }), 400
        user = User.query.filter_by(username=json_data.get('username')).first()
        
        if not user or not check_password_hash(user.password, json_data.get('password')):
            return jsonify({
                'success': False,
                'message': 'Invalid credentials'
            }), 401
        
        token = generate_token(user.username)
        token_out = Token(access_token=token, token_type='bearer')
        
        return jsonify({
            'success': True,
            'message': 'Login successful',
            'data': token_out.model_dump()
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

@auth_bp.route('/users/me', methods=['GET'])
@token_required
def get_current_user(current_user):
    try:
        user_out = UserOut.model_validate(current_user)
        return jsonify({
            'success': True,
            'data': user_out.model_dump()
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500