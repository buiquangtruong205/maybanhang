"""
IoT Machine Routes - API endpoints for ESP/Arduino vending machines
"""
from flask import Blueprint, request, jsonify
from datetime import datetime
import os
import time
from app import db
from app.models import Machine, Order, Slot, Product, DeviceLog, DeviceIdentity, DeviceSession, allocate_bigint_pk
from app.utils.machine_auth import multi_auth_required, machine_key_required
from app.websocket import emit_stock_update, emit_machine_status_update, emit_admin_log, emit_admin_machine_status, emit_admin_device_auth_update

iot_bp = Blueprint('iot', __name__)

# In-memory store for active frontend sessions
# Format: {machine_id: {'session_id': 'xyz', 'last_seen': 1234567.89}}
FRONTEND_SESSIONS = {}
FRONTEND_SESSION_TIMEOUT = 5.0  # seconds

def _get_order_for_machine(order_id, machine_id):
    order = Order.query.get(order_id)
    if not order:
        return None, (jsonify({'success': False, 'message': 'Order not found'}), 404)

    if machine_id is None:
        return order, None

    slot = order.slot
    if not slot or slot.machine_id != machine_id:
        return None, (jsonify({'success': False, 'message': 'Order does not belong to this machine'}), 403)

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
    """Ping từ máy bán hàng để báo còn hoạt động"""
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
    """Heartbeat từ giao diện web (frontend) để giữ session"""
    try:
        json_data = request.get_json(force=True, silent=True) or {}
        session_id = json_data.get('session_id')
        if not session_id:
            return jsonify({'success': False, 'message': 'session_id is required'}), 400
            
        current_time = time.time()
        active_session = FRONTEND_SESSIONS.get(machine_id)
        
        if active_session and active_session['session_id'] != session_id:
            if current_time - active_session['last_seen'] < FRONTEND_SESSION_TIMEOUT:
                return jsonify({'success': False, 'message': 'System in use by another device', 'rejected': True}), 403
                
        FRONTEND_SESSIONS[machine_id] = {'session_id': session_id, 'last_seen': current_time}
        return jsonify({'success': True, 'message': 'Heartbeat accepted', 'rejected': False})
    except Exception as e:
        return jsonify({'success': False, 'message': f'Error: {str(e)}'}), 500

@iot_bp.route('/iot/dispense-complete', methods=['POST'])
@machine_key_required
def dispense_complete(machine_id):
    """Báo hoàn thành xuất hàng từ máy bán hàng"""
    try:
        json_data = request.get_json(force=True, silent=True)
        if not json_data:
            return jsonify({'success': False, 'message': 'Request body must be valid JSON'}), 400
        
        order_id = json_data.get('order_id')
        dispense_success = json_data.get('success', False)
        
        if not order_id:
            return jsonify({'success': False, 'message': 'order_id is required'}), 400
        
        order, error_response = _get_order_for_machine(order_id, machine_id)
        if error_response: return error_response
        
        order.status_slots = 'dispensed' if dispense_success else 'failed'
        db.session.commit()
        
        emit_admin_machine_status(machine_id, {
            "last_order_id": order_id,
            "last_dispense_status": "success" if dispense_success else "failed"
        })
        
        if dispense_success and order.slot:
            emit_admin_stock_update(machine_id, {
                'slot_code': order.slot.slot_code,
                'new_stock': order.slot.stock,
                'slot_id': order.slot.slot_id
            })
        
        print(f"🎰 Dispense from machine {machine_id}: order={order_id}, success={dispense_success}")
        return jsonify({'success': True, 'message': 'Dispense completed', 'order_id': order_id})
    except Exception as e:
        return jsonify({'success': False, 'message': f'Error: {str(e)}'}), 500

@iot_bp.route('/iot/pending-orders', methods=['GET'])
@multi_auth_required
def get_pending_orders(machine_id):
    """Lấy danh sách đơn hàng đang chờ xuất cho máy này"""
    try:
        orders = (
            Order.query
            .filter(
                Order.machine_id == machine_id,
                Order.status_payment == 'completed',
                Order.status_slots == 'pending'
            )
            .order_by(Order.created_at.asc())
            .all()
        )
        
        order_list = [{
            'order_id': o.order_id,
            'slot_id': o.slot_id,
            'slot_code': o.slot.slot_code if o.slot else None,
            'product_id': o.product_id,
            'price': float(o.price_snapshot),
            'created_at': o.created_at.isoformat() if o.created_at else None
        } for o in orders]
        
        return jsonify({'success': True, 'data': order_list})
    except Exception as e:
        return jsonify({'success': False, 'message': f'Error: {str(e)}'}), 500

@iot_bp.route('/iot/stock-update', methods=['POST'])
@machine_key_required
def update_stock(machine_id):
    """Cập nhật tồn kho từ máy bán hàng"""
    try:
        json_data = request.get_json(force=True, silent=True)
        slot_code = json_data.get('slot_code')
        new_stock = json_data.get('stock')
        
        if not slot_code or new_stock is None:
            return jsonify({'success': False, 'message': 'slot_code and stock are required'}), 400
        
        slot = Slot.query.filter_by(machine_id=machine_id, slot_code=slot_code).first()
        if not slot:
            return jsonify({'success': False, 'message': f'Slot {slot_code} not found'}), 404
        
        slot.stock = new_stock
        db.session.commit()
        
        emit_stock_update(machine_id, {'slot_code': slot_code, 'new_stock': new_stock, 'product_id': slot.product_id})
        emit_admin_stock_update(machine_id, {'slot_code': slot_code, 'new_stock': new_stock, 'slot_id': slot.slot_id})
        
        return jsonify({'success': True, 'message': 'Stock updated'})
    except Exception as e:
        return jsonify({'success': False, 'message': f'Error: {str(e)}'}), 500

@iot_bp.route('/iot/create-order', methods=['POST'])
@multi_auth_required
def create_order_from_machine(machine_id):
    """ESP tạo đơn hàng khi khách mua hàng tại máy"""
    try:
        json_data = request.get_json(force=True, silent=True)
        slot_code = json_data.get('slot_code')
        product_id = json_data.get('product_id')
        quantity = json_data.get('quantity', 1)
        
        slot = Slot.query.filter_by(machine_id=machine_id, slot_code=slot_code).first() if slot_code else None
        if slot_code and not slot:
            return jsonify({'success': False, 'message': f'Slot {slot_code} not found'}), 404
            
        product_id = product_id or (slot.product_id if slot else None)
        if not product_id:
            return jsonify({'success': False, 'message': 'product_id is required'}), 400
            
        product = Product.query.get(product_id)
        if not product or not product.active:
            return jsonify({'success': False, 'message': 'Product not found or inactive'}), 404

        new_order = Order(
            machine_id=machine_id,
            product_id=product_id,
            slot_id=slot.slot_id if slot else None,
            price_snapshot=float(product.price) * quantity,
            quantity=quantity,
            status_payment='pending',
            status_slots='pending'
        )
        db.session.add(new_order)
        db.session.commit()
        
        from app.websocket import emit_admin_order_new
        emit_admin_order_new({
            'order_id': new_order.order_id,
            'machine_id': machine_id,
            'product_name': product.product_name,
            'amount': float(new_order.price_snapshot),
            'status': 'pending',
            'timestamp': datetime.utcnow().isoformat()
        })
        
        return jsonify({
            'success': True, 
            'message': 'Order created', 
            'data': {
                'order_id': new_order.order_id,
                'product_name': product.product_name,
                'price': float(new_order.price_snapshot)
            }
        })
    except Exception as e:
        import traceback
        traceback.print_exc()
        db.session.rollback()
        return jsonify({'success': False, 'message': f'Internal Server Error: {str(e)}'}), 500

@iot_bp.route('/iot/register-device', methods=['POST'])
@machine_key_required
def register_device(machine_id):
    """ESP đăng ký thiết bị"""
    try:
        json_data = request.get_json(force=True, silent=True) or {}
        mac_address = json_data.get('mac_address')
        fingerprint = json_data.get('fingerprint')
        
        machine = Machine.query.get(machine_id)
        if not machine: return jsonify({'success': False, 'message': 'Machine not found'}), 404
        
        # Consistent status casing
        machine.status = 'ONLINE'
        
        identity = DeviceIdentity.query.get(machine_id)
        if identity:
            # Nếu thiết bị đã bị Thu hồi, không cho phép tự kích hoạt lại qua Register
            if identity.status == 'revoked':
                return jsonify({
                    'success': False, 
                    'message': f'Device {machine_id} is REVOKED and cannot re-register. Contact Admin.'
                }), 403
                
            identity.mac_address = mac_address
            identity.cert_fingerprint = fingerprint
            identity.status = 'active'
        else:
            import hashlib
            identity = DeviceIdentity(
                machine_id=machine_id,
                mac_address=mac_address,
                cert_fingerprint=fingerprint,
                device_public_key=hashlib.sha256(f"{machine_id}-{mac_address}".encode()).hexdigest()[:64],
                status='active'
            )
            db.session.add(identity)
        
        db.session.commit()
        
        # Báo cho Dashboard biết có thiết bị mới đăng ký hoặc cập nhật định danh
        emit_admin_device_auth_update(machine_id)
        
        return jsonify({'success': True, 'message': 'Registered', 'data': {'config': _build_device_config(machine)}})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': f'Error: {str(e)}'}), 500

@iot_bp.route('/iot/heartbeat', methods=['POST'])
@machine_key_required
def device_heartbeat(machine_id):
    """ESP gửi heartbeat (Single Source of Truth)"""
    import hashlib
    try:
        json_data = request.get_json(force=True, silent=True) or {}
        uptime = json_data.get('uptime', 0)
        wifi_rssi = json_data.get('wifi_rssi', 0)
        wifi_ssid = json_data.get('wifi_ssid')
        
        identity = DeviceIdentity.query.get(machine_id)
        if identity:
            identity.rssi = wifi_rssi
            identity.wifi_ssid = wifi_ssid
            identity.uptime = uptime
            identity.last_heartbeat = datetime.utcnow()
        
        is_new_session = False
        session = DeviceSession.query.filter_by(machine_id=machine_id, is_revoked=False).order_by(DeviceSession.issued_at.desc()).first()
        if session:
            session.last_seen_at = datetime.utcnow()
        else:
            token_hash = hashlib.sha256(f"{machine_id}-{datetime.utcnow().isoformat()}".encode()).hexdigest()
            session = DeviceSession(machine_id=machine_id, token_hash=token_hash[:64], expires_at=datetime.utcnow().replace(year=datetime.utcnow().year + 1), ip_address=request.remote_addr, last_seen_at=datetime.utcnow())
            db.session.add(session)
            is_new_session = True
        
        db.session.commit()
        
        if is_new_session:
            emit_admin_device_auth_update(machine_id)
            
        # Standardized Real-time Emit
        emit_admin_machine_status(machine_id, {
            'status': 'ONLINE',
            'uptime': uptime,
            'wifi_signal': wifi_ssid,
            'rssi': wifi_rssi,
            'last_seen': datetime.utcnow().isoformat()
        })
        
        print(f"💓 Heartbeat from machine {machine_id}: uptime={uptime}s, rssi={wifi_rssi}")
        return jsonify({'success': True, 'session_id': session.session_id})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': f'Error: {str(e)}'}), 500

@iot_bp.route('/iot/cash-insert', methods=['POST'])
@machine_key_required
def report_cash_insert(machine_id):
    """ESP báo nạp tiền mặt vào đơn hàng"""
    try:
        json_data = request.get_json(force=True, silent=True)
        order_id = json_data.get('order_id')
        denomination = json_data.get('denomination', 0)
        
        if not order_id or not denomination:
            return jsonify({'success': False, 'message': 'order_id and denomination are required'}), 400
            
        order = Order.query.get(order_id)
        if not order:
            return jsonify({'success': False, 'message': 'Order not found'}), 404
            
        # Logic cập nhật số tiền đã thanh toán (simulated via backend model helper if exists, or manual)
        # Vì model Order hiện tại không có trường 'amount_paid' trực tiếp mà dựa vào transaction, 
        # ta sẽ tạo một Transaction cho đơn hàng này.
        from app.models import Transaction, allocate_bigint_pk
        new_tx = Transaction(
            transaction_id=allocate_bigint_pk(Transaction, Transaction.transaction_id),
            order_id=order_id,
            amount=denomination,
            status='completed',
            description='Cash payment via local hardware'
        )
        db.session.add(new_tx)
        db.session.flush() # Đẩy dữ liệu xuống DB để sum chính xác

        # Tính toán lại tổng tiền đã nạp thực tế từ DB
        from sqlalchemy import func
        total_paid_dec = db.session.query(func.sum(Transaction.amount)).filter_by(order_id=order_id, status='completed').scalar() or 0
        total_paid = float(total_paid_dec)
        price = float(order.price_snapshot)
        remaining = max(0, int(price - total_paid))
        
        print(f"💰 [CASH INSERT] Order #{order_id}: Received {denomination} VNĐ. Total Paid: {total_paid}. Remaining: {remaining}")

        if remaining <= 0:
            order.status_payment = 'completed'
            print(f"✅ [CASH INSERT] Order #{order_id} is now FULLY PAID.")
            
        db.session.commit()
        
        # Thông báo cho Dashboard và Client Web
        emit_admin_log({
            'machine_id': machine_id,
            'level': 'info',
            'message': f'Cash Inserted: {denomination} VNĐ for Order #{order_id}',
            'timestamp': datetime.utcnow().isoformat()
        })
        
        # Emit event cho frontend máy qua namespace /machine
        from app.websocket import emit_payment_status_update
        emit_payment_status_update(machine_id, {
            'order_id': order_id,
            'status': order.status_payment,
            'paid': total_paid,
            'remaining': remaining,
            'denomination': denomination
        })

        return jsonify({
            'success': True, 
            'message': 'Cash inserted successfully',
            'data': {
                'remaining': remaining,
                'status': order.status_payment
            }
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': f'Error: {str(e)}'}), 500

@iot_bp.route('/iot/cash-status/<int:order_id>', methods=['GET'])
@multi_auth_required
def get_cash_status(machine_id, order_id):
    """Lấy trạng thái nạp tiền mặt của một đơn hàng"""
    try:
        order, error_response = _get_order_for_machine(order_id, machine_id)
        if error_response: return error_response
        
        from app.models import Transaction
        txs = Transaction.query.filter_by(order_id=order_id, status='completed').all()
        total_inserted = float(sum(tx.amount for tx in txs))
        price = float(order.price_snapshot)
        remaining = max(0, int(price - total_inserted))
        change = max(0, int(total_inserted - price))
        
        return jsonify({
            'success': True,
            'data': {
                'total_inserted': total_inserted,
                'price': price,
                'remaining': remaining,
                'change': change,
                'is_paid': order.status_payment == 'completed'
            }
        })
    except Exception as e:
        return jsonify({'success': False, 'message': f'Error: {str(e)}'}), 500

@iot_bp.route('/iot/logs', methods=['POST'])
@machine_key_required
def upload_device_logs(machine_id):
    """Upload logs từ thiết bị"""
    try:
        json_data = request.get_json(force=True, silent=True) or {}
        new_log = DeviceLog(
            log_id=allocate_bigint_pk(DeviceLog, DeviceLog.log_id),
            machine_id=machine_id,
            level=json_data.get('level', 'info'),
            message=json_data.get('message', ''),
            data=json_data.get('data')
        )
        db.session.add(new_log)
        db.session.commit()
        
        emit_admin_log({
            'machine_id': machine_id,
            'level': new_log.level,
            'message': new_log.message,
            'data': new_log.data,
            'timestamp': datetime.utcnow().isoformat()
        })
        return jsonify({'success': True})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': f'Error: {str(e)}'}), 500
