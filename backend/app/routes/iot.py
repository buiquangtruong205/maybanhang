"""
IoT Machine Routes - API endpoints for ESP/Arduino vending machines
"""
from flask import Blueprint, request, jsonify
from datetime import datetime
import os
import time
from app import db
from app.models import Machine, Order, Slot, Product, DeviceLog, allocate_bigint_pk
from app.utils.machine_auth import multi_auth_required, machine_key_required
from app.websocket import emit_stock_update, emit_machine_status_update, emit_admin_log, emit_admin_machine_status

iot_bp = Blueprint('iot', __name__)

# In-memory store for active frontend sessions
# Format: {machine_id: {'session_id': 'xyz', 'last_seen': 1234567.89}}
FRONTEND_SESSIONS = {}
FRONTEND_SESSION_TIMEOUT = 5.0  # seconds


def _get_order_for_machine(order_id, machine_id):
    order = Order.query.get(order_id)
    if not order:
        return None, (
            jsonify({
                'success': False,
                'message': 'Order not found'
            }),
            404
        )

    if machine_id is None:
        return order, None

    slot = order.slot
    if not slot or slot.machine_id != machine_id:
        return None, (
            jsonify({
                'success': False,
                'message': 'Order does not belong to this machine'
            }),
            403
        )

    return order, None


def _resolve_public_mqtt_broker():
    broker = os.environ.get('PUBLIC_MQTT_BROKER')
    if broker:
        return broker.strip()

    host = request.host.split(':', 1)[0].strip()
    return host or 'localhost'


def _resolve_public_mqtt_port():
    try:
        return int(os.environ.get('PUBLIC_MQTT_PORT', '1883'))
    except (TypeError, ValueError):
        return 1883


def _build_device_config(machine):
    broker = _resolve_public_mqtt_broker()
    port = _resolve_public_mqtt_port()
    command_topic = (machine.mqtt_command_topic or '').strip() or f'vending/v3/machine/{machine.machine_id}/cmd'
    status_topic = (machine.mqtt_status_topic or '').strip() or f'vending/v3/machine/{machine.machine_id}/status'
    broadcast_status_topic = (machine.mqtt_broadcast_status_topic or '').strip() or 'vending/v3/status'

    return {
        'machine_id': str(machine.machine_id),
        'machine_name': machine.name,
        'machine_key': machine.secret_key,
        'location': machine.location,
        'mqtt': {
            'broker': broker,
            'port': port,
            'topics': {
                'command': command_topic,
                'status': status_topic,
                'broadcast_status': broadcast_status_topic
            }
        },
        'ui': {
            'layout': machine.ui_layout or {}
        },
        'device_profile': machine.device_profile or {},
        'admin_notes': machine.config_notes
    }


@iot_bp.route('/iot/ping', methods=['POST'])
@machine_key_required
def machine_ping(machine_id):
    """
    Ping từ máy bán hàng để báo còn hoạt động
    
    Request:
        Header: X-Machine-Key: maybanhang-v3
        Body (optional): {"status": "online", "temperature": 25.5}
    
    Response:
        {"success": true, "message": "Pong", "machine_id": 1}
    """
    json_data = request.get_json(force=True, silent=True) or {}
    
    print(f"📡 Ping from machine {machine_id}: {json_data}")
    
    return jsonify({
        'success': True,
        'message': 'Pong',
        'machine_id': machine_id,
        'server_time': datetime.utcnow().isoformat()
    })


@iot_bp.route('/iot/frontend-heartbeat', methods=['POST'])
@multi_auth_required
def frontend_heartbeat(machine_id):
    """
    Heartbeat từ giao diện web (frontend) để đảm bảo chỉ 1 thiết bị truy cập tại 1 thời điểm.
    
    Request:
        Header: X-Machine-Key: maybanhang-v3
        Body: {"session_id": "abc-123"}
    
    Response:
        {"success": true, "rejected": false, "message": "Heartbeat accepted"}
    """
    try:
        json_data = request.get_json(force=True, silent=True) or {}
        session_id = json_data.get('session_id')
        
        if not session_id:
            return jsonify({
                'success': False,
                'message': 'session_id is required'
            }), 400
            
        current_time = time.time()
        
        # Lấy session hiện tại của machine
        active_session = FRONTEND_SESSIONS.get(machine_id)
        
        # Nếu đã có session và session khác với session hiện tại
        if active_session and active_session['session_id'] != session_id:
            # Kiểm tra xem session cũ còn active không (dựa vào khoảng cách thời gian)
            if current_time - active_session['last_seen'] < FRONTEND_SESSION_TIMEOUT:
                return jsonify({
                    'success': False,
                    'message': 'System in use by another device',
                    'rejected': True
                }), 403
                
        # Cấp quyền hoặc duy trì quyền cho session hiện tại
        FRONTEND_SESSIONS[machine_id] = {
            'session_id': session_id,
            'last_seen': current_time
        }
        
        return jsonify({
            'success': True,
            'message': 'Heartbeat accepted',
            'rejected': False
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error: {str(e)}'
        }), 500


@iot_bp.route('/iot/dispense-complete', methods=['POST'])
@machine_key_required
def dispense_complete(machine_id):
    """
    Báo hoàn thành xuất hàng từ máy bán hàng
    
    Request:
        Header: X-Machine-Key: maybanhang-v3
        Body: {
            "order_id": 123,
            "slot_code": "A1",
            "success": true,
            "message": "Dispensed successfully"
        }
    
    Response:
        {"success": true, "message": "Dispense status updated"}
    """
    try:
        json_data = request.get_json(force=True, silent=True)
        if not json_data:
            return jsonify({
                'success': False,
                'message': 'Request body must be valid JSON'
            }), 400
        
        order_id = json_data.get('order_id')
        dispense_success = json_data.get('success', False)
        
        if not order_id:
            return jsonify({
                'success': False,
                'message': 'order_id is required'
            }), 400
        
        # Update order status
        order, error_response = _get_order_for_machine(order_id, machine_id)
        if error_response:
            return error_response
        
        if dispense_success:
            order.status_slots = 'dispensed'
            message = 'Dispense completed'
        else:
            order.status_slots = 'failed'
            message = 'Dispense failed'
        
        db.session.commit()
        
        print(f"🎰 Dispense from machine {machine_id}: order={order_id}, success={dispense_success}")
        
        return jsonify({
            'success': True,
            'message': message,
            'order_id': order_id
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error: {str(e)}'
        }), 500


@iot_bp.route('/iot/pending-orders', methods=['GET'])
@multi_auth_required
def get_pending_orders(machine_id):
    """
    Lấy danh sách đơn hàng đang chờ xuất cho máy này
    
    Request:
        Header: X-Machine-Key: maybanhang-v3
    
    Response:
        {
            "success": true,
            "data": [
                {"order_id": 123, "slot_id": 1, "product_id": 5, "status": "completed"}
            ]
        }
    """
    try:
        # Join trực tiếp qua Slot để tránh bỏ sót order hợp lệ do bước lấy slot_ids riêng.
        orders = (
            Order.query
            .join(Slot, Order.slot_id == Slot.slot_id)
            .filter(
                Slot.machine_id == machine_id,
                Order.status_payment == 'completed',
                Order.status_slots == 'pending'
            )
            .order_by(Order.created_at.asc())
            .all()
        )

        print(
            f"📥 Pending orders for machine {machine_id}: "
            f"{[(o.order_id, o.slot_id, o.status_payment, o.status_slots) for o in orders]}"
        )
        
        order_list = [{
            'order_id': o.order_id,
            'slot_id': o.slot_id,
            'slot_code': o.slot.slot_code if o.slot else None,
            'product_id': o.product_id,
            'price': float(o.price_snapshot),
            'created_at': o.created_at.isoformat() if o.created_at else None
        } for o in orders]
        
        return jsonify({
            'success': True,
            'message': f'Found {len(order_list)} pending orders',
            'data': order_list
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error: {str(e)}'
        }), 500


@iot_bp.route('/iot/stock-update', methods=['POST'])
@machine_key_required
def update_stock(machine_id):
    """
    Cập nhật tồn kho từ máy bán hàng
    
    Request:
        Header: X-Machine-Key: may1
        Body: {
            "slot_code": "A1",
            "stock": 5
        }
    
    Response:
        {"success": true, "message": "Stock updated"}
    """
    try:
        json_data = request.get_json(force=True, silent=True)
        if not json_data:
            return jsonify({
                'success': False,
                'message': 'Request body must be valid JSON'
            }), 400
        
        slot_code = json_data.get('slot_code')
        new_stock = json_data.get('stock')
        
        if not slot_code or new_stock is None:
            return jsonify({
                'success': False,
                'message': 'slot_code and stock are required'
            }), 400
        
        # Find slot
        slot = Slot.query.filter_by(machine_id=machine_id, slot_code=slot_code).first()
        if not slot:
            return jsonify({
                'success': False,
                'message': f'Slot {slot_code} not found for machine {machine_id}'
            }), 404
        
        old_stock = slot.stock
        slot.stock = new_stock
        db.session.commit()
        
        # Real-time update
        emit_stock_update(machine_id, {
            'slot_code': slot_code,
            'new_stock': new_stock,
            'product_id': slot.product_id
        })
        
        print(f"📦 Stock update from machine {machine_id}: slot={slot_code}, {old_stock} -> {new_stock}")
        
        return jsonify({
            'success': True,
            'message': 'Stock updated',
            'slot_code': slot_code,
            'old_stock': old_stock,
            'new_stock': new_stock
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error: {str(e)}'
        }), 500


@iot_bp.route('/iot/create-order', methods=['POST'])
@multi_auth_required
def create_order_from_machine(machine_id):
    """
    ESP tạo đơn hàng khi khách mua hàng tại máy
    
    Request:
        Header: X-Machine-Key: may1
        Body: {
            "slot_code": "A1",        # Vị trí sản phẩm trong máy
            "product_id": 5,          # ID sản phẩm (optional nếu đã có trong slot)
            "quantity": 1             # Số lượng (default 1)
        }
    
    Response:
        {
            "success": true,
            "message": "Order created",
            "data": {
                "order_id": 123,
                "product_id": 5,
                "price": 15000,
                "status": "pending"
            }
        }
    """
    try:
        json_data = request.get_json(force=True, silent=True)
        if not json_data:
            return jsonify({
                'success': False,
                'message': 'Request body must be valid JSON'
            }), 400
        
        slot_code = json_data.get('slot_code')
        product_id = json_data.get('product_id')
        quantity = json_data.get('quantity', 1)
        
        # Tìm slot theo machine_id và slot_code
        slot = None
        if slot_code:
            slot = Slot.query.filter_by(machine_id=machine_id, slot_code=slot_code).first()
            if not slot:
                return jsonify({
                    'success': False,
                    'message': f'Slot {slot_code} not found for machine {machine_id}'
                }), 404
            
            # Lấy product_id từ slot nếu không được cung cấp
            if not product_id and slot.product_id:
                product_id = slot.product_id
        
        # Validate product
        if not product_id:
            return jsonify({
                'success': False,
                'message': 'product_id is required (or slot must have product assigned)'
            }), 400
        
        product = Product.query.get(product_id)
        if not product:
            return jsonify({
                'success': False,
                'message': 'Product not found'
            }), 404
        
        if not product.active:
            return jsonify({
                'success': False,
                'message': 'Product is not active'
            }), 400
            
        # If slot was not specified, find a slot with this product and sufficient stock
        if not slot:
            slot = Slot.query.filter_by(machine_id=machine_id, product_id=product_id)\
                             .filter(Slot.stock >= quantity)\
                             .first()
            if not slot:
                 # Check if any slot has this product (for better error message)
                 any_slot = Slot.query.filter_by(machine_id=machine_id, product_id=product_id).first()
                 if any_slot:
                     return jsonify({
                        'success': False, 
                        'message': f'Insufficient stock. Product available in slot {any_slot.slot_code} but stock too low.'
                     }), 400
                 else:
                     return jsonify({
                        'success': False, 
                        'message': 'Product is not assigned to any slot in this machine'
                     }), 400
        
        # Tính toán stock có sẵn thực tế (Available Stock = Stock - Pending Orders)
        from sqlalchemy import func
        from datetime import datetime, timedelta
        
        timeout_threshold = datetime.utcnow() - timedelta(minutes=15)
        
        # Chỉ tính Pending Order thuộc cùng machine này, cho cùng một product này
        # Nếu muốn chặt chẽ hơn, có thể tính cả slot_id.
        query = db.session.query(func.sum(Order.quantity)).filter(
            Order.product_id == product_id,
            Order.status_payment == 'pending',
            Order.created_at >= timeout_threshold
        )
        
        # Lấy danh sách slot_id của machine này
        machine_slot_ids = [s.slot_id for s in Slot.query.filter_by(machine_id=machine_id).all()]
        if machine_slot_ids:
            query = query.filter(Order.slot_id.in_(machine_slot_ids))
            
        pending_qty = query.scalar() or 0
        
        # Lấy tổng stock của product trong toàn bộ máy này
        machine_stock = sum(s.stock for s in Slot.query.filter_by(machine_id=machine_id, product_id=product_id).all())
        
        available_stock = machine_stock - pending_qty
        
        # Kiểm tra stock (có tính pending)
        if available_stock < quantity:
            return jsonify({
                'success': False,
                'message': f'Sản phẩm tạm thời hết hàng hoặc có người khác đang đặt lệnh. Khả dụng: {available_stock}'
            }), 400
        
        # Tính giá
        price_snapshot = float(product.price) * quantity
        
        # Tạo order với status pending (chờ thanh toán)
        new_order = Order(
            product_id=product_id,
            slot_id=slot.slot_id if slot else None,
            price_snapshot=price_snapshot,
            quantity=quantity,
            status_payment='pending',
            status_slots='pending'
        )
        
        db.session.add(new_order)
        db.session.commit()
        
        print(f"🛒 Order created from machine {machine_id}: order_id={new_order.order_id}, product={product_id}, price={price_snapshot}")
        
        return jsonify({
            'success': True,
            'message': 'Order created successfully',
            'data': {
                'order_id': new_order.order_id,
                'product_id': product_id,
                'product_name': product.product_name,
                'price': price_snapshot,
                'slot_code': slot_code,
                'status_payment': new_order.status_payment,
                'status_slots': new_order.status_slots
            }
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': f'Error: {str(e)}'
        }), 500


@iot_bp.route('/iot/check-payment/<int:order_id>', methods=['GET'])
@multi_auth_required
def check_order_payment(machine_id, order_id):
    """
    ESP kiểm tra trạng thái thanh toán của đơn hàng
    
    Request:
        Header: X-Machine-Key: may1
        URL: /api/iot/check-payment/123
    
    Response:
        {
            "success": true,
            "data": {
                "order_id": 123,
                "status_payment": "completed",
                "status_slots": "pending",
                "paid": true
            }
        }
    """
    try:
        order, error_response = _get_order_for_machine(order_id, machine_id)
        if error_response:
            return error_response
        
        is_paid = order.status_payment == 'completed'
        return jsonify({
            'success': True,
            'message': 'Order status retrieved',
            'data': {
                'order_id': order.order_id,
                'status_payment': order.status_payment,
                'status_slots': order.status_slots,
                'paid': is_paid,
                'price': float(order.price_snapshot)
            }
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error: {str(e)}'
        }), 500


@iot_bp.route('/iot/logs', methods=['POST'])
@machine_key_required
def upload_device_logs(machine_id):
    """
    Upload readable logs from device (errors, warnings, debug info)
    
    Request:
        Header: X-Machine-Key: may1
        Body: {
            "level": "error",           # info, warning, error
            "message": "Sensor malfunction",
            "data": {"sensor": "temp", "code": 500}
        }
    """
    from app.models import DeviceLog
    
    try:
        json_data = request.get_json(force=True, silent=True) or {}
        
        level = json_data.get('level', 'info')
        message = json_data.get('message', '')
        data = json_data.get('data')
        
        if not message:
            return jsonify({
                'success': False,
                'message': 'Log message is required'
            }), 400
            
        new_log = DeviceLog(
            log_id=allocate_bigint_pk(DeviceLog, DeviceLog.log_id),
            machine_id=machine_id,
            level=level,
            message=message,
            data=data
        )
        
        db.session.add(new_log)
        db.session.commit()
        
        # Real-time log to Admin
        emit_admin_log({
            'machine_id': machine_id,
            'level': level,
            'message': message,
            'data': data,
            'timestamp': datetime.utcnow().isoformat()
        })
        
        print(f"📝 Device Log [{level}] from machine {machine_id}: {message}")
        
        return jsonify({
            'success': True,
            'message': 'Log saved successfully'
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': f'Error: {str(e)}'
        }), 500


# ===========================
# Device Registration & Session
# ===========================

@iot_bp.route('/iot/register-device', methods=['POST'])
@machine_key_required
def register_device(machine_id):
    """
    ESP tự đăng ký device identity khi khởi động lần đầu
    
    Request:
        Header: X-Machine-Key: may1
        Body: {
            "mac_address": "AA:BB:CC:DD:EE:FF",
            "fingerprint": "abc123...",
            "firmware_version": "1.0.0"
        }
    
    Response:
        {"success": true, "message": "Device registered", "machine_id": 1}
    """
    from app.models import DeviceIdentity, Machine
    import hashlib
    
    try:
        json_data = request.get_json(force=True, silent=True) or {}
        
        mac_address = json_data.get('mac_address')
        fingerprint = json_data.get('fingerprint')
        firmware_version = json_data.get('firmware_version', '1.0.0')
        rssi = json_data.get('wifi_rssi')
        wifi_ssid = json_data.get('wifi_ssid')
        uptime = json_data.get('uptime', 0)
        
        if not machine_id:
            return jsonify({
                'success': False,
                'message': 'machine_id is required when using the master registration key'
            }), 400

        # Check if machine exists
        machine = Machine.query.get(machine_id)
        if not machine:
            return jsonify({
                'success': False,
                'message': f'Machine {machine_id} not found. Create the machine first.'
            }), 404
        
        # Update machine status
        machine.status = 'online'
        
        # Check if device identity exists
        identity = DeviceIdentity.query.get(machine_id)
        
        if identity:
            # Update existing
            identity.mac_address = mac_address
            identity.cert_fingerprint = fingerprint
            identity.rssi = rssi
            identity.wifi_ssid = wifi_ssid
            identity.uptime = uptime
            identity.status = 'active'
            print(f"🔄 Device {machine_id} updated identity: MAC={mac_address}")
        else:
            # Create new identity
            identity = DeviceIdentity(
                machine_id=machine_id,
                mac_address=mac_address,
                cert_fingerprint=fingerprint,
                rssi=rssi,
                wifi_ssid=wifi_ssid,
                uptime=uptime,
                device_public_key=hashlib.sha256(f"{machine_id}-{mac_address}".encode()).hexdigest()[:64],
                status='active'
            )
            db.session.add(identity)
            print(f"✅ Device {machine_id} registered: MAC={mac_address}")
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Device registered successfully',
            'data': {
                'machine_id': machine_id,
                'machine_name': machine.name,
                'mac_address': mac_address,
                'status': 'active',
                'config': _build_device_config(machine)
            }
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': f'Error: {str(e)}'
        }), 500


@iot_bp.route('/iot/heartbeat', methods=['POST'])
@machine_key_required
def device_heartbeat(machine_id):
    """
    ESP gửi heartbeat để cập nhật session và trạng thái online
    
    Request:
        Header: X-Machine-Key: may1
        Body: {
            "uptime": 3600,
            "free_memory": 50000,
            "wifi_rssi": -65
        }
    
    Response:
        {"success": true, "session_id": 123}
    """
    from app.models import DeviceSession, DeviceIdentity
    import hashlib
    
    try:
        json_data = request.get_json(force=True, silent=True) or {}
        
        uptime = json_data.get('uptime', 0)
        free_memory = json_data.get('free_memory', 0)
        wifi_rssi = json_data.get('wifi_rssi', 0)
        wifi_ssid = json_data.get('wifi_ssid')
        
        # Update device identity health info
        identity = DeviceIdentity.query.get(machine_id)
        if identity:
            identity.rssi = wifi_rssi
            identity.wifi_ssid = wifi_ssid
            identity.uptime = uptime
            db.session.flush()
        
        # Find or create session
        # Look for an active session for this machine
        session = DeviceSession.query.filter_by(
            machine_id=machine_id,
            is_revoked=False
        ).order_by(DeviceSession.issued_at.desc()).first()
        
        if session:
            # Update last seen
            session.last_seen_at = datetime.utcnow()
        else:
            # Create new session
            token_hash = hashlib.sha256(f"{machine_id}-{datetime.utcnow().isoformat()}".encode()).hexdigest()
            session = DeviceSession(
                machine_id=machine_id,
                token_hash=token_hash[:64],
                expires_at=datetime.utcnow().replace(year=datetime.utcnow().year + 1),
                ip_address=request.remote_addr,
                last_seen_at=datetime.utcnow()
            )
            db.session.add(session)
        
        db.session.commit()
        
        # Real-time update for Admin
        emit_admin_machine_status(machine_id, {
            'status': 'online',
            'last_seen': datetime.utcnow().isoformat(),
            'wifi_rssi': wifi_rssi,
            'uptime': uptime
        })
        
        print(f"💓 Heartbeat from machine {machine_id}: uptime={uptime}s, mem={free_memory}, rssi={wifi_rssi}")
        
        return jsonify({
            'success': True,
            'message': 'Heartbeat received',
            'data': {
                'machine_id': machine_id,
                'session_id': session.session_id,
                'server_time': datetime.utcnow().isoformat(),
                'config': _build_device_config(Machine.query.get(machine_id))
            }
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': f'Error: {str(e)}'
        }), 500
