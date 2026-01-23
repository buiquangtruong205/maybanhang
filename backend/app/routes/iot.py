"""
IoT Machine Routes - API endpoints for ESP/Arduino vending machines
"""
from flask import Blueprint, request, jsonify
from datetime import datetime
from app import db
from app.models import Machine, Order, Slot, Product
from app.utils import machine_key_required

iot_bp = Blueprint('iot', __name__)


@iot_bp.route('/iot/ping', methods=['POST'])
@machine_key_required
def machine_ping(machine_id):
    """
    Ping từ máy bán hàng để báo còn hoạt động
    
    Request:
        Header: X-Machine-Key: may1
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





@iot_bp.route('/iot/dispense-complete', methods=['POST'])
@machine_key_required
def dispense_complete(machine_id):
    """
    Báo hoàn thành xuất hàng từ máy bán hàng
    
    Request:
        Header: X-Machine-Key: may1
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
        order = Order.query.get(order_id)
        if not order:
            return jsonify({
                'success': False,
                'message': 'Order not found'
            }), 404
        
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
@machine_key_required
def get_pending_orders(machine_id):
    """
    Lấy danh sách đơn hàng đang chờ xuất cho máy này
    
    Request:
        Header: X-Machine-Key: may1
    
    Response:
        {
            "success": true,
            "data": [
                {"order_id": 123, "slot_id": 1, "product_id": 5, "status": "completed"}
            ]
        }
    """
    try:
        # Get slots belonging to this machine
        slots = Slot.query.filter_by(machine_id=machine_id).all()
        slot_ids = [s.slot_id for s in slots]
        
        # Get orders with status_payment=completed but status_slots=pending
        orders = Order.query.filter(
            Order.slot_id.in_(slot_ids) if slot_ids else False,
            Order.status_payment == 'completed',
            Order.status_slots == 'pending'
        ).all()
        
        order_list = [{
            'order_id': o.order_id,
            'slot_id': o.slot_id,
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
@machine_key_required
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
        
        # Kiểm tra stock
        if slot and slot.stock < quantity:
            return jsonify({
                'success': False,
                'message': f'Insufficient stock. Available: {slot.stock}'
            }), 400
        
        # Tính giá
        price_snapshot = float(product.price) * quantity
        
        # Tạo order với status pending (chờ thanh toán)
        new_order = Order(
            product_id=product_id,
            slot_id=slot.slot_id if slot else None,
            price_snapshot=price_snapshot,
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
@machine_key_required
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
        order = Order.query.get(order_id)
        if not order:
            return jsonify({
                'success': False,
                'message': 'Order not found'
            }), 404
        
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
        
        # Check if machine exists, create if not
        machine = Machine.query.get(machine_id)
        if not machine:
            machine = Machine(
                machine_id=machine_id,
                name=f'Machine {machine_id}',
                location='Auto-registered',
                status='online'
            )
            db.session.add(machine)
            db.session.flush()
        
        # Update machine status
        machine.status = 'online'
        
        # Check if device identity exists
        identity = DeviceIdentity.query.get(machine_id)
        
        if identity:
            # Update existing
            identity.mac_address = mac_address
            identity.cert_fingerprint = fingerprint
            identity.status = 'active'
            print(f"🔄 Device {machine_id} updated identity: MAC={mac_address}")
        else:
            # Create new identity
            identity = DeviceIdentity(
                machine_id=machine_id,
                mac_address=mac_address,
                cert_fingerprint=fingerprint,
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
                'mac_address': mac_address,
                'status': 'active'
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
        
        print(f"💓 Heartbeat from machine {machine_id}: uptime={uptime}s, mem={free_memory}, rssi={wifi_rssi}")
        
        return jsonify({
            'success': True,
            'message': 'Heartbeat received',
            'data': {
                'machine_id': machine_id,
                'session_id': session.session_id,
                'server_time': datetime.utcnow().isoformat()
            }
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': f'Error: {str(e)}'
        }), 500

