from flask import Blueprint, request, jsonify
from pydantic import ValidationError
from app import db
from app.models import Transaction
from app.schemas import TransactionCreate, TransactionOut
from app.utils import token_required

transaction_bp = Blueprint('transaction', __name__)

@transaction_bp.route('/transactions', methods=['GET'])
@token_required
def get_transactions(current_user):
    transactions = Transaction.query.order_by(Transaction.transaction_id.desc()).all()
    return jsonify({
        'success': True,
        'message': 'Transactions retrieved successfully',
        'data': [TransactionOut.model_validate(t).model_dump() for t in transactions]
    })

@transaction_bp.route('/transactions/<int:transaction_id>', methods=['GET'])
@token_required
def get_transaction(current_user, transaction_id):
    transaction = Transaction.query.filter_by(transaction_id=transaction_id).first()
    if not transaction:
        return jsonify({
            'success': False,
            'message': 'Transaction not found'
        }), 404
    return jsonify({
        'success': True,
        'message': 'Transaction retrieved successfully',
        'data': TransactionOut.model_validate(transaction).model_dump()
    })

@transaction_bp.route('/transactions', methods=['POST'])
def create_transaction():
    try:
        json_data = request.get_json(force=True, silent=True)
        if not json_data:
            return jsonify({
                'success': False,
                'message': 'Request body must be valid JSON'
            }), 400
        data = TransactionCreate(**json_data)
        new_transaction = Transaction(**data.model_dump())
        
        db.session.add(new_transaction)
        db.session.commit()
        
        transaction_out = TransactionOut.model_validate(new_transaction)
        return jsonify({
            'success': True,
            'message': 'Transaction created successfully',
            'data': transaction_out.model_dump()
        }), 201
    
    except ValidationError as e:
        return jsonify({
            'success': False,
            'message': 'Validation error',
            'errors': e.errors()
        }), 422
