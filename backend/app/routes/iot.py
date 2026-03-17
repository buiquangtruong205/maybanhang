"""
IoT Machine Routes - API endpoints for ESP/Arduino vending machines
"""
from flask import Blueprint, request, jsonify
from datetime import datetime
import time
from app import db
from app.models import Machine, Order, Slot, Product
from app.utils import machine_key_required

iot_bp = Blueprint('iot', __name__)

# In-memory store for active frontend sessions
# Format: {machine_id: {'session_id': 'xyz', 'last_seen': 1234567.89}}
FRONTEND_SESSIONS = {}
FRONTEND_SESSION_TIMEOUT = 5.0  # seconds


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
@machine_key_required
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
            machine_id=machine_id,
            level=level,
            message=message,
            data=data
        )
        
        db.session.add(new_log)
        db.session.commit()
        
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


# ===========================
# Cash Payment (Tiền mặt)
# ===========================

# Mệnh giá hợp lệ (VNĐ)
VALID_DENOMINATIONS = {1000, 2000, 5000, 10000, 20000, 50000, 100000, 200000, 500000}


@iot_bp.route('/iot/cash-insert', methods=['POST'])
@machine_key_required
def cash_insert(machine_id):
    """
    Arduino báo nhận được tờ tiền (sau khi cảm biến nhận diện mệnh giá).

    Request:
        Header: X-Machine-Key: may1
        Body: {
            "order_id": 123,
            "denomination": 50000      # mệnh giá tờ tiền (VNĐ)
        }

    Response (chưa đủ tiền):
        {
            "success": true,
            "paid": false,
            "total_inserted": 50000,
            "price": 75000,
            "remaining": 25000,
            "change": 0
        }

    Response (đã đủ tiền):
        {
            "success": true,
            "paid": true,
            "total_inserted": 100000,
            "price": 75000,
            "remaining": 0,
            "change": 25000
        }
    """
    from app.models import CashDeposit, Transaction, Slot
    from app.websocket import emit_payment_success
    from sqlalchemy import func

    try:
        json_data = request.get_json(force=True, silent=True)
        if not json_data:
            return jsonify({'success': False, 'message': 'Request body must be valid JSON'}), 400

        order_id = json_data.get('order_id')
        denomination = json_data.get('denomination')

        # --- Validation ---
        if not order_id:
            return jsonify({'success': False, 'message': 'order_id is required'}), 400

        if denomination is None:
            return jsonify({'success': False, 'message': 'denomination is required'}), 400

        denomination = int(denomination)
        if denomination not in VALID_DENOMINATIONS:
            return jsonify({
                'success': False,
                'message': f'Invalid denomination: {denomination}. Valid values: {sorted(VALID_DENOMINATIONS)}'
            }), 400

        # --- Kiểm tra đơn hàng ---
        order = Order.query.get(order_id)
        if not order:
            return jsonify({'success': False, 'message': f'Order #{order_id} not found'}), 404

        if order.status_payment == 'completed':
            return jsonify({
                'success': False,
                'message': f'Order #{order_id} is already paid'
            }), 400

        if order.status_payment == 'cancelled':
            return jsonify({
                'success': False,
                'message': f'Order #{order_id} is cancelled'
            }), 400

        # --- Kiểm tra máy này sở hữu đơn hàng ---
        if order.slot_id:
            slot = Slot.query.get(order.slot_id)
            if slot and slot.machine_id != machine_id:
                return jsonify({
                    'success': False,
                    'message': f'Order #{order_id} does not belong to this machine'
                }), 403

        # --- Ghi nhận tờ tiền vừa nhét ---
        deposit = CashDeposit(
            order_id=order_id,
            machine_id=machine_id,
            denomination=denomination,
            change=0
        )
        db.session.add(deposit)
        db.session.flush()  # flush để có deposit_id, chưa commit

        # --- Tính tổng tiền đã nhét ---
        total_inserted = db.session.query(
            func.sum(CashDeposit.denomination)
        ).filter(CashDeposit.order_id == order_id).scalar() or 0

        price = float(order.price_snapshot)
        remaining = max(0, price - total_inserted)
        change = max(0, total_inserted - price)
        is_paid = total_inserted >= price

        print(f"💵 Cash insert: machine={machine_id}, order={order_id}, "
              f"denomination={denomination}, total={total_inserted}, price={price}, "
              f"remaining={remaining}, change={change}")

        if is_paid:
            # --- Đủ tiền: cập nhật order, trừ giá sản phẩm, ghi tiền thừa ---
            # status_slots giữ 'pending' → Arduino poll /iot/pending-orders rồi nhả hàng
            # Sau khi nhả xong, Arduino gọi /iot/dispense-complete → 'dispensed'
            order.status_payment = 'completed'
            order.status_slots = 'pending'

            # Ghi lại tiền thừa tại bản ghi vừa tạo
            deposit.change = int(change)

            # Giảm stock trong slot 
            if order.slot_id:
                slot = Slot.query.get(order.slot_id)
                if slot:
                    qty = getattr(order, 'quantity', 1)
                    if slot.stock >= qty:
                        slot.stock -= qty
                        print(f"📦 Stock reduced for slot {order.slot_id}: {slot.stock + qty} -> {slot.stock}")
                    else:
                        slot.stock = 0

                    if slot.stock == 0:
                        product = Product.query.get(slot.product_id)
                        # Check total stock across all slots using the property defined in Product model
                        if product and product.stock == 0:
                            product.active = False
                            print(f"⚠️ Product '{product.product_name}' marked INACTIVE (total stock=0)")

            # Tạo Transaction (tiền mặt)
            existing_tx = Transaction.query.filter_by(order_id=order_id).first()
            if not existing_tx:
                transaction = Transaction(
                    order_id=order_id,
                    amount=float(price),           # trừ đúng giá sản phẩm
                    bank_trans_id=None,
                    description=(
                        f"Thanh toán tiền mặt đơn #{order_id} "
                        f"(nhét: {int(total_inserted):,}đ, "
                        f"giá: {int(price):,}đ, "
                        f"tiền thừa: {int(change):,}đ)"
                    ),
                    status='success'
                )
                db.session.add(transaction)
                print(f"💳 Cash transaction created for order #{order_id}")

            db.session.commit()
            print(f"✅ Order #{order_id} paid by cash. Change: {change:,}đ")

            # Emit WebSocket để frontend nhận ngay
            emit_payment_success(order_id, {
                'amount': price,
                'payment_method': 'cash',
                'total_inserted': total_inserted,
                'change': change
            })

            return jsonify({
                'success': True,
                'paid': True,
                'message': f'Payment completed! Change: {int(change):,}đ',
                'data': {
                    'order_id': order_id,
                    'total_inserted': int(total_inserted),
                    'price': int(price),
                    'remaining': 0,
                    'change': int(change)
                }
            }), 200

        else:
            # Chưa đủ tiền
            db.session.commit()
            return jsonify({
                'success': True,
                'paid': False,
                'message': f'Inserted {int(denomination):,}đ. Still need {int(remaining):,}đ more.',
                'data': {
                    'order_id': order_id,
                    'total_inserted': int(total_inserted),
                    'price': int(price),
                    'remaining': int(remaining),
                    'change': 0
                }
            }), 200

    except Exception as e:
        db.session.rollback()
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'message': f'Error: {str(e)}'}), 500


@iot_bp.route('/iot/cash-status/<int:order_id>', methods=['GET'])
@machine_key_required
def cash_status(machine_id, order_id):
    """
    Kiểm tra tổng số tiền đã nhét cho một đơn hàng.

    Request:
        Header: X-Machine-Key: may1
        URL: /api/iot/cash-status/123

    Response:
        {
            "success": true,
            "data": {
                "order_id": 123,
                "price": 75000,
                "total_inserted": 50000,
                "remaining": 25000,
                "change": 0,
                "is_paid": false,
                "status_payment": "pending",
                "deposits": [
                    {"denomination": 50000, "inserted_at": "2026-03-04T09:00:00"}
                ]
            }
        }
    """
    from app.models import CashDeposit
    from sqlalchemy import func

    try:
        order = Order.query.get(order_id)
        if not order:
            return jsonify({'success': False, 'message': f'Order #{order_id} not found'}), 404

        # Tổng tiền đã nhét
        total_inserted = db.session.query(
            func.sum(CashDeposit.denomination)
        ).filter(CashDeposit.order_id == order_id).scalar() or 0

        price = float(order.price_snapshot)
        remaining = max(0, price - total_inserted)
        change = max(0, total_inserted - price)
        is_paid = order.status_payment == 'completed'

        # Chi tiết các lần nhét
        deposits = CashDeposit.query.filter_by(order_id=order_id).order_by(
            CashDeposit.inserted_at.asc()
        ).all()

        deposit_list = [{
            'deposit_id': d.deposit_id,
            'denomination': d.denomination,
            'inserted_at': d.inserted_at.isoformat() if d.inserted_at else None
        } for d in deposits]

        return jsonify({
            'success': True,
            'message': 'Cash status retrieved',
            'data': {
                'order_id': order_id,
                'price': int(price),
                'total_inserted': int(total_inserted),
                'remaining': int(remaining),
                'change': int(change),
                'is_paid': is_paid,
                'status_payment': order.status_payment,
                'deposits': deposit_list
            }
        })

    except Exception as e:
        return jsonify({'success': False, 'message': f'Error: {str(e)}'}), 500


