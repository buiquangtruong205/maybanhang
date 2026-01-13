from flask import Flask, jsonify, send_from_directory
from flask_sqlalchemy import SQLAlchemy
from app.config import Config
from werkzeug.exceptions import HTTPException
import os

db = SQLAlchemy()

def create_app(config_class=Config):
    app = Flask(__name__, static_folder='static')
    app.config.from_object(config_class)
    
    # Enable CORS for all routes
    @app.after_request
    def after_request(response):
        response.headers.add('Access-Control-Allow-Origin', '*')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
        response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE,OPTIONS')
        return response
    
    db.init_app(app)
    
    # Register blueprints
    from app.routes.auth import auth_bp
    from app.routes.product import product_bp
    from app.routes.slot import slot_bp
    from app.routes.order import order_bp
    from app.routes.machine import machine_bp
    from app.routes.user import user_bp
    from app.routes.transaction import transaction_bp
    from app.routes.stats import stats_bp
    from app.routes.payment import payment_bp
    from app.routes.import_data import import_data_bp
    from app.routes.device import device_bp
    from app.routes.security import security_bp
    from app.routes.firmware import firmware_bp
    from app.routes.telemetry import telemetry_bp
    
    app.register_blueprint(auth_bp, url_prefix='/api')
    app.register_blueprint(product_bp, url_prefix='/api')
    app.register_blueprint(slot_bp, url_prefix='/api')
    app.register_blueprint(order_bp, url_prefix='/api')
    app.register_blueprint(machine_bp, url_prefix='/api')
    app.register_blueprint(user_bp, url_prefix='/api')
    app.register_blueprint(transaction_bp, url_prefix='/api')
    app.register_blueprint(stats_bp, url_prefix='/api')
    app.register_blueprint(payment_bp, url_prefix='/api')
    app.register_blueprint(import_data_bp, url_prefix='/api')
    app.register_blueprint(device_bp, url_prefix='/api')
    app.register_blueprint(security_bp, url_prefix='/api')
    app.register_blueprint(firmware_bp, url_prefix='/api')
    app.register_blueprint(telemetry_bp, url_prefix='/api')
    
    # Homepage
    @app.route('/')
    def index():
        return jsonify({
            'success': True,
            'message': 'Vending Machine API',
            'version': '1.0',
            'endpoints': {
                'auth': [
                    'POST /api/register',
                    'POST /api/login',
                    'GET /api/users/me (requires token)'
                ],
                'users': [
                    'GET /api/users (requires token)',
                    'GET /api/users/<id> (requires token)',
                    'PUT /api/users/<id> (requires token)',
                    'DELETE /api/users/<id> (requires token)'
                ],
                'machines': [
                    'GET /api/machines',
                    'GET /api/machines/<id>',
                    'POST /api/machines (requires token)',
                    'PUT /api/machines/<id> (requires token)',
                    'DELETE /api/machines/<id> (requires token)'
                ],
                'products': [
                    'GET /api/products',
                    'GET /api/products/<id>',
                    'POST /api/products (requires token)',
                    'PUT /api/products/<id> (requires token)',
                    'DELETE /api/products/<id> (requires token)'
                ],
                'slots': [
                    'GET /api/slots',
                    'GET /api/slots/<id>',
                    'POST /api/slots (requires token)',
                    'PUT /api/slots/<id> (requires token)',
                    'DELETE /api/slots/<id> (requires token)'
                ],
                'orders': [
                    'GET /api/orders (requires token)',
                    'GET /api/orders/<id> (requires token)',
                    'POST /api/orders'
                ],
                'admin': 'GET /admin - Web Management Dashboard'
            }
        })
    
    # Admin Dashboard
    @app.route('/admin')
    def admin():
        return send_from_directory(app.static_folder, 'index.html')
    
    # Error handlers - Convert all errors to JSON
    @app.errorhandler(404)
    def not_found(error):
        return jsonify({
            'success': False,
            'error': 'Not Found',
            'message': 'The requested resource was not found'
        }), 404
    
    @app.errorhandler(405)
    def method_not_allowed(error):
        return jsonify({
            'success': False,
            'error': 'Method Not Allowed',
            'message': 'The method is not allowed for the requested URL'
        }), 405
    
    @app.errorhandler(500)
    def internal_error(error):
        return jsonify({
            'success': False,
            'error': 'Internal Server Error',
            'message': 'An internal server error occurred'
        }), 500
    
    @app.errorhandler(HTTPException)
    def handle_exception(e):
        return jsonify({
            'success': False,
            'error': e.name,
            'message': e.description
        }), e.code
    
    @app.errorhandler(Exception)
    def handle_general_exception(e):
        return jsonify({
            'success': False,
            'error': 'Internal Server Error',
            'message': str(e)
        }), 500
    
    with app.app_context():
        db.create_all()
    
    return app