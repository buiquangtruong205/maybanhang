from flask import Blueprint, request, jsonify
from werkzeug.security import generate_password_hash
from pydantic import ValidationError
from app import db
from app.models import User
from app.schemas import UserOut
from app.utils import token_required

user_bp = Blueprint('user', __name__)

@user_bp.route('/users', methods=['GET'])
@token_required
def get_users(current_user):
    users = User.query.all()
    return jsonify({
        'success': True,
        'message': 'Users retrieved successfully',
        'data': [UserOut.model_validate(u).model_dump() for u in users]
    })

@user_bp.route('/users/<int:user_id>', methods=['GET'])
@token_required
def get_user(current_user, user_id):
    user = User.query.get_or_404(user_id)
    return jsonify({
        'success': True,
        'message': 'User retrieved successfully',
        'data': UserOut.model_validate(user).model_dump()
    })

@user_bp.route('/users/<int:user_id>', methods=['PUT'])
@token_required
def update_user(current_user, user_id):
    try:
        user = User.query.get_or_404(user_id)
        json_data = request.get_json(force=True, silent=True)
        if not json_data:
            return jsonify({
                'success': False,
                'message': 'Request body must be valid JSON'
            }), 400
        
        if 'username' in json_data:
            user.username = json_data['username']
        if 'password' in json_data:
            user.password = generate_password_hash(json_data['password'])
        if 'is_active' in json_data:
            user.is_active = json_data['is_active']
        
        db.session.commit()
        
        user_out = UserOut.model_validate(user)
        return jsonify({
            'success': True,
            'message': 'User updated successfully',
            'data': user_out.model_dump()
        })
    
    except Exception as e:
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

@user_bp.route('/users/<int:user_id>', methods=['DELETE'])
@token_required
def delete_user(current_user, user_id):
    user = User.query.get_or_404(user_id)
    db.session.delete(user)
    db.session.commit()
    return jsonify({
        'success': True,
        'message': 'User deleted successfully'
    }), 200
