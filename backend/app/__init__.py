from flask import Flask, jsonify, send_from_directory, request, g
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import inspect, text
from app.config import Config, validate_startup_config
from app.websocket import socketio
from werkzeug.exceptions import HTTPException
import os
import hashlib

db = SQLAlchemy()


def ensure_machine_dynamic_config_columns():
    inspector = inspect(db.engine)
    if not inspector.has_table('machines'):
        return

    existing_columns = {column['name'] for column in inspector.get_columns('machines')}
    missing_columns = []

    for column_name, column_sql in (
        ('mqtt_command_topic', 'ALTER TABLE machines ADD COLUMN mqtt_command_topic VARCHAR(255)'),
        ('mqtt_status_topic', 'ALTER TABLE machines ADD COLUMN mqtt_status_topic VARCHAR(255)'),
        ('mqtt_broadcast_status_topic', 'ALTER TABLE machines ADD COLUMN mqtt_broadcast_status_topic VARCHAR(255)'),
        ('ui_layout', 'ALTER TABLE machines ADD COLUMN ui_layout JSON'),
        ('device_profile', 'ALTER TABLE machines ADD COLUMN device_profile JSON'),
        ('config_notes', 'ALTER TABLE machines ADD COLUMN config_notes TEXT'),
    ):
        if column_name not in existing_columns:
            missing_columns.append((column_name, column_sql))

    if not missing_columns:
        return

    for column_name, column_sql in missing_columns:
        print(f"Applying schema upgrade for machines.{column_name}")
        db.session.execute(text(column_sql))

    db.session.commit()

def ensure_order_machine_id_column():
    inspector = inspect(db.engine)
    if not inspector.has_table('orders'):
        return

    existing_columns = {column['name'] for column in inspector.get_columns('orders')}
    if 'machine_id' not in existing_columns:
        print("Applying schema upgrade for orders.machine_id")
        db.session.execute(text('ALTER TABLE orders ADD COLUMN machine_id INTEGER'))
        db.session.commit()

def ensure_device_identity_columns():
    inspector = inspect(db.engine)
    if not inspector.has_table('device_identity'):
        return

    existing_columns = {column['name'] for column in inspector.get_columns('device_identity')}
    if 'last_heartbeat' not in existing_columns:
        print("Applying schema upgrade for device_identity.last_heartbeat")
        db.session.execute(text('ALTER TABLE device_identity ADD COLUMN last_heartbeat TIMESTAMP'))
        db.session.commit()

def migrate_machine_secret_keys():
    from app.models import Machine
    from app.utils.machine_auth import hash_machine_key, is_hashed_machine_key

    machines = Machine.query.all()
    changed = False
    for machine in machines:
        if machine.secret_key and not is_hashed_machine_key(machine.secret_key):
            machine.secret_key = hash_machine_key(machine.secret_key)
            changed = True

    if changed:
        print("Applying security migration for machines.secret_key hashing")
        db.session.commit()

def start_offline_monitor(app):
    """Luồng chạy ngầm để phát hiện và báo máy offline real-time"""
    with app.app_context():
        while True:
            try:
                from app.models import DeviceIdentity
                from app.websocket import emit_admin_machine_status
                from datetime import datetime, timedelta
                
                # Ngưỡng 60 giây
                threshold = datetime.utcnow() - timedelta(seconds=60)
                
                # Query các thiết bị có heartbeat quá cũ HOẶC chưa bao giờ có heartbeat
                offline_identities = DeviceIdentity.query.filter(
                    (DeviceIdentity.last_heartbeat == None) | (DeviceIdentity.last_heartbeat < threshold)
                ).all()
                
                for identity in offline_identities:
                    # Gửi tin nhắn OFFLINE real-time
                    emit_admin_machine_status(identity.machine_id, {"status": "OFFLINE"})
                    
            except Exception as e:
                print(f"Monitor error: {e}")
            
            socketio.sleep(15) # Kiểm tra mỗi 15 giây

def create_app(config_class=Config):
    validate_startup_config()
    app = Flask(__name__, static_folder='static')
    app.config.from_object(config_class)
    
    # Initialize SocketIO with the app
    socketio.init_app(app)
    
    # Before request - capture machine_id if present
    @app.before_request
    def before_request():
        # Global request logging for debugging
        print(f"REQ: {request.method} {request.path}")
        
        g.machine_id = None
        g.machine_key = None
        
        # Check for machine key in headers
        machine_key = request.headers.get('X-Machine-Key')
        if not machine_key:
            # Check in JSON body
            json_data = request.get_json(force=True, silent=True)
            if json_data:
                machine_key = json_data.get('machine_key')
        if not machine_key:
            # Check in query params
            machine_key = request.args.get('machine_key')
        
        if machine_key:
            from app.utils.machine_auth import get_machine_id_from_key
            g.machine_key = machine_key
            g.machine_id = get_machine_id_from_key(machine_key)
    
    # Enable CORS for all routes and log API calls
    @app.after_request
    def after_request(response):
        # CORS headers
        # Allow specific origins from environment, default to * for backward compatibility
        cors_origins = os.environ.get('CORS_ORIGINS', '*')
        request_origin = request.headers.get('Origin')
        if cors_origins == '*':
            response.headers['Access-Control-Allow-Origin'] = '*'
        else:
            allowed_origins = [origin.strip() for origin in cors_origins.split(',') if origin.strip()]
            if request_origin and request_origin in allowed_origins:
                response.headers['Access-Control-Allow-Origin'] = request_origin
                response.headers['Vary'] = 'Origin'
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization,X-Machine-Key')
        response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE,OPTIONS')
        
        # Log IoT API calls to database (skip OPTIONS requests)
        if (request.path.startswith('/api/iot') or request.path.startswith('/api/devices')) and request.method != 'OPTIONS':
            try:
                from app.models import ApiAuditLog, allocate_bigint_pk
                
                # Get payload hash
                payload_hash = None
                if request.data:
                    payload_hash = hashlib.sha256(request.data).hexdigest()[:64]
                
                # Determine if signature/key is valid
                signature_ok = g.machine_id is not None if hasattr(g, 'machine_id') else False
                
                audit_log = ApiAuditLog(
                    request_id=allocate_bigint_pk(ApiAuditLog, ApiAuditLog.request_id),
                    machine_id=g.machine_id if hasattr(g, 'machine_id') else None,
                    endpoint=request.path,
                    method=request.method,
                    ip_address=request.remote_addr,
                    response_code=response.status_code,
                    payload_hash=payload_hash,
                    signature_ok=signature_ok
                )
                db.session.add(audit_log)
                db.session.commit()
            except Exception as e:
                # Don't fail the request if logging fails
                print(f"Audit log error: {e}")
                db.session.rollback()
        
        return response
    
    db.init_app(app)

    # Register blueprints
    from app.routes.auth import auth_bp
    from app.routes.product import product_bp
    from app.routes.slot import slot_bp
    from app.routes.order import order_bp
    from app.routes.machine import machine_bp
    from app.routes.user import user_bp
    from app.routes.device import device_bp
    from app.routes.iot import iot_bp
    from app.routes.transaction import transaction_bp
    from app.routes.stats import stats_bp
    from app.routes.payment import payment_bp
    from app.routes.webauthn import webauthn_bp
    from app.routes.firmware import firmware_bp
    from app.routes.security import security_bp
    
    app.register_blueprint(auth_bp, url_prefix='/api')
    app.register_blueprint(product_bp, url_prefix='/api')
    app.register_blueprint(slot_bp, url_prefix='/api')
    app.register_blueprint(order_bp, url_prefix='/api')
    app.register_blueprint(machine_bp, url_prefix='/api')
    app.register_blueprint(user_bp, url_prefix='/api')
    app.register_blueprint(transaction_bp, url_prefix='/api')
    app.register_blueprint(stats_bp, url_prefix='/api')
    app.register_blueprint(payment_bp, url_prefix='/api')
    app.register_blueprint(device_bp, url_prefix='/api')
    app.register_blueprint(iot_bp, url_prefix='/api')
    app.register_blueprint(webauthn_bp, url_prefix='/api')
    app.register_blueprint(firmware_bp, url_prefix='/api')
    app.register_blueprint(security_bp, url_prefix='/api')
    
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
        if app.config.get('TESTING'):
            app.logger.error("Unhandled application error: %s", e)
        else:
            app.logger.exception("Unhandled application error")
        return jsonify({
            'success': False,
            'error': 'Internal Server Error',
            'message': 'An internal server error occurred'
        }), 500
    
    with app.app_context():
        try:
            db.create_all()
            ensure_machine_dynamic_config_columns()
            ensure_device_identity_columns()
            ensure_order_machine_id_column()
            migrate_machine_secret_keys()
            
            # Khởi động luồng giám sát offline
            socketio.start_background_task(start_offline_monitor, app)
        except Exception as e:
            print(f"⚠️  Warning: Could not create database tables: {e}")
            print("   Make sure DATABASE_URL environment variable is set correctly.")
    
    return app
