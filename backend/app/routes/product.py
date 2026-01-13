from flask import Blueprint, request, jsonify, current_app
from pydantic import ValidationError
from werkzeug.utils import secure_filename
from app import db
from app.models import Product
from app.schemas import ProductCreate, ProductOut
from app.utils import token_required
import os
import uuid

product_bp = Blueprint('product', __name__)

# Allowed image extensions
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@product_bp.route('/upload', methods=['POST'])
@token_required
def upload_image(current_user):
    if 'file' not in request.files:
        return jsonify({
            'success': False,
            'message': 'No file provided'
        }), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({
            'success': False,
            'message': 'No file selected'
        }), 400
    
    if file and allowed_file(file.filename):
        # Create uploads directory if not exists
        upload_folder = os.path.join(current_app.static_folder, 'uploads')
        os.makedirs(upload_folder, exist_ok=True)
        
        # Generate unique filename
        ext = file.filename.rsplit('.', 1)[1].lower()
        filename = f"{uuid.uuid4().hex}.{ext}"
        filepath = os.path.join(upload_folder, filename)
        
        file.save(filepath)
        
        # Return the URL path
        image_url = f"/static/uploads/{filename}"
        return jsonify({
            'success': True,
            'message': 'File uploaded successfully',
            'data': {
                'url': image_url,
                'filename': filename
            }
        })
    
    return jsonify({
        'success': False,
        'message': 'File type not allowed. Allowed types: png, jpg, jpeg, gif, webp'
    }), 400

@product_bp.route('/products', methods=['GET'])
def get_products():
    products = Product.query.all()
    return jsonify({
        'success': True,
        'message': 'Products retrieved successfully',
        'data': [ProductOut.model_validate(p).model_dump() for p in products]
    })

@product_bp.route('/products/<int:product_id>', methods=['GET'])
def get_product(product_id):
    product = Product.query.filter_by(product_id=product_id).first()
    if not product:
        return jsonify({
            'success': False,
            'message': 'Product not found'
        }), 404
    return jsonify({
        'success': True,
        'message': 'Product retrieved successfully',
        'data': ProductOut.model_validate(product).model_dump()
    })

@product_bp.route('/products', methods=['POST'])
@token_required
def create_product(current_user):
    try:
        json_data = request.get_json(force=True, silent=True)
        if not json_data:
            return jsonify({
                'success': False,
                'message': 'Request body must be valid JSON'
            }), 400
        data = ProductCreate(**json_data)
        new_product = Product(**data.model_dump())
        
        db.session.add(new_product)
        db.session.commit()
        
        product_out = ProductOut.model_validate(new_product)
        return jsonify({
            'success': True,
            'message': 'Product created successfully',
            'data': product_out.model_dump()
        }), 201
    
    except ValidationError as e:
        return jsonify({
            'success': False,
            'message': 'Validation error',
            'errors': e.errors()
        }), 422

@product_bp.route('/products/<int:product_id>', methods=['PUT'])
@token_required
def update_product(current_user, product_id):
    try:
        product = Product.query.filter_by(product_id=product_id).first()
        if not product:
            return jsonify({
                'success': False,
                'message': 'Product not found'
            }), 404
        json_data = request.get_json(force=True, silent=True)
        if not json_data:
            return jsonify({
                'success': False,
                'message': 'Request body must be valid JSON'
            }), 400
        data = ProductCreate(**json_data)
        
        product.product_name = data.product_name
        product.price = data.price
        product.image = data.image
        product.active = data.active
        
        db.session.commit()
        
        product_out = ProductOut.model_validate(product)
        return jsonify({
            'success': True,
            'message': 'Product updated successfully',
            'data': product_out.model_dump()
        })
    
    except ValidationError as e:
        return jsonify({
            'success': False,
            'message': 'Validation error',
            'errors': e.errors()
        }), 422

@product_bp.route('/products/<int:product_id>', methods=['DELETE'])
@token_required
def delete_product(current_user, product_id):
    product = Product.query.filter_by(product_id=product_id).first()
    if not product:
        return jsonify({
            'success': False,
            'message': 'Product not found'
        }), 404
    db.session.delete(product)
    db.session.commit()
    return jsonify({
        'success': True,
        'message': 'Product deleted successfully'
    }), 200