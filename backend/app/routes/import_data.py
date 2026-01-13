from flask import Blueprint, request, jsonify
from pydantic import ValidationError
from app import db
from app.models import ImportData, Slot
from app.schemas import ImportDataCreate, ImportDataOut
from app.utils import token_required

import_data_bp = Blueprint('import_data', __name__)


@import_data_bp.route('/imports', methods=['GET'])
@token_required
def get_imports(current_user):
    """Get all import records"""
    imports = ImportData.query.order_by(ImportData.created_at.desc()).all()
    return jsonify({
        'success': True,
        'message': 'Import records retrieved successfully',
        'data': [ImportDataOut.model_validate(i).model_dump() for i in imports]
    })


@import_data_bp.route('/imports/<int:import_id>', methods=['GET'])
@token_required
def get_import(current_user, import_id):
    """Get a specific import record"""
    import_record = ImportData.query.get_or_404(import_id)
    return jsonify({
        'success': True,
        'message': 'Import record retrieved successfully',
        'data': ImportDataOut.model_validate(import_record).model_dump()
    })


@import_data_bp.route('/imports', methods=['POST'])
@token_required
def create_import(current_user):
    """Create a new import record and update slot stock"""
    try:
        json_data = request.get_json(force=True, silent=True)
        if not json_data:
            return jsonify({
                'success': False,
                'message': 'Request body must be valid JSON'
            }), 400

        data = ImportDataCreate(**json_data)
        
        # Create import record
        new_import = ImportData(
            user_id=data.user_id,
            machine_id=data.machine_id,
            slot_id=data.slot_id,
            product_id=data.product_id,
            quantity=data.quantity
        )
        
        # Update slot stock
        slot = Slot.query.get(data.slot_id)
        if slot:
            slot.stock += data.quantity
            if slot.stock > slot.capacity:
                slot.stock = slot.capacity
        
        db.session.add(new_import)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Import record created successfully',
            'data': ImportDataOut.model_validate(new_import).model_dump()
        }), 201

    except ValidationError as e:
        return jsonify({
            'success': False,
            'message': 'Validation error',
            'errors': e.errors()
        }), 422


@import_data_bp.route('/imports/machine/<int:machine_id>', methods=['GET'])
@token_required
def get_imports_by_machine(current_user, machine_id):
    """Get all imports for a specific machine"""
    imports = ImportData.query.filter_by(machine_id=machine_id).order_by(ImportData.created_at.desc()).all()
    return jsonify({
        'success': True,
        'message': 'Import records retrieved successfully',
        'data': [ImportDataOut.model_validate(i).model_dump() for i in imports]
    })
