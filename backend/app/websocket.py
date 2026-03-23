"""
WebSocket module for real-time payment notifications
Uses Flask-SocketIO for WebSocket support
"""
import os
from flask import request
from flask_socketio import SocketIO, emit, join_room
import jwt

# Initialize SocketIO with CORS support
# Allow specific origins from environment, default to * for backward compatibility
cors_origins = os.environ.get('CORS_ORIGINS', '*')
if cors_origins != '*':
    cors_origins = cors_origins.split(',')
socketio = SocketIO(cors_allowed_origins=cors_origins, async_mode='threading')

# Track connected clients per order
connected_clients = {}


def _extract_token_from_request(auth_data=None):
    auth_data = auth_data or {}
    token = auth_data.get('token') or request.args.get('token') or request.headers.get('Authorization')
    if token and token.startswith('Bearer '):
        token = token[7:]
    return token


def _get_admin_user(auth_data=None):
    from app.models import User
    from app.utils.auth import get_jwt_signing_key

    token = _extract_token_from_request(auth_data)
    if not token:
        return None

    try:
        payload = jwt.decode(token, get_jwt_signing_key(), algorithms=["HS256"])
    except jwt.InvalidTokenError:
        return None

    user = User.query.filter_by(username=payload.get('username')).first()
    if not user or not user.is_active:
        return None
    return user


def _extract_machine_key(auth_data=None):
    auth_data = auth_data or {}
    return auth_data.get('machine_key') or request.args.get('machine_key') or request.headers.get('X-Machine-Key')


def _get_machine(auth_data=None):
    from app.models import Machine
    from app.utils.machine_auth import hash_machine_key

    machine_key = _extract_machine_key(auth_data)
    if not machine_key:
        return None
    return Machine.query.filter_by(secret_key=hash_machine_key(machine_key)).first()


# ==========================================
# /payment Namespace (Existing)
# ==========================================

@socketio.on('connect', namespace='/payment')
def on_payment_connect(auth=None):
    """Handle new WebSocket connection for payments"""
    if not _get_admin_user(auth) and not _get_machine(auth):
        return False
    print(f"🔌 Payment WebSocket client connected")


@socketio.on('disconnect', namespace='/payment')
def on_payment_disconnect():
    """Handle WebSocket disconnection for payments"""
    print(f"🔌 Payment WebSocket client disconnected")


@socketio.on('subscribe', namespace='/payment')
def on_payment_subscribe(data):
    """Subscribe to payment updates for a specific order"""
    from app.models import Order

    order_id = data.get('order_id')
    if order_id:
        admin_user = _get_admin_user(data)
        machine = _get_machine(data)
        order = Order.query.get(order_id)
        if not order:
            emit('subscription_error', {'message': 'Order not found'})
            return

        order_machine_id = order.machine_id or (order.slot.machine_id if order.slot else None)
        if not admin_user and (not machine or machine.machine_id != order_machine_id):
            emit('subscription_error', {'message': 'Forbidden'})
            return

        room = f'order_{order_id}'
        join_room(room)
        print(f"📢 Client subscribed to payment room: {room}")
        emit('subscribed', {'order_id': order_id, 'status': 'subscribed'})


def emit_payment_success(order_id, data=None):
    if data is None: data = {}
    room = f'order_{order_id}'
    payload = {'order_id': order_id, 'status': 'completed', **data}
    socketio.emit('payment_success', payload, room=room, namespace='/payment')


def emit_payment_failed(order_id, reason=None):
    room = f'order_{order_id}'
    payload = {'order_id': order_id, 'status': 'failed', 'reason': reason or 'Payment failed'}
    socketio.emit('payment_failed', payload, room=room, namespace='/payment')


def emit_payment_cancelled(order_id):
    room = f'order_{order_id}'
    payload = {'order_id': order_id, 'status': 'cancelled'}
    socketio.emit('payment_cancelled', payload, room=room, namespace='/payment')


# ==========================================
# /machine Namespace (New)
# ==========================================

@socketio.on('connect', namespace='/machine')
def on_machine_connect(auth=None):
    if not _get_machine(auth):
        return False
    print(f"🔌 Machine WebSocket connected")


@socketio.on('subscribe_machine', namespace='/machine')
def on_machine_subscribe(data):
    """Máy bán hàng subscribe vào room của chính mình để nhận lệnh hoặc cập nhật"""
    machine_id = data.get('machine_id')
    if machine_id:
        machine = _get_machine(data)
        if not machine or int(machine_id) != machine.machine_id:
            emit('machine_subscription_error', {'message': 'Forbidden'})
            return

        room = f'machine_{machine_id}'
        join_room(room)
        print(f"📢 Machine {machine_id} subscribed to room: {room}")
        emit('machine_subscribed', {'machine_id': machine_id, 'status': 'active'})


def emit_stock_update(machine_id, data):
    """Thông báo cập nhật tồn kho cho máy cụ thể"""
    room = f'machine_{machine_id}'
    socketio.emit('stock_update', data, room=room, namespace='/machine')


def emit_machine_status_update(machine_id, status_data):
    """Thông báo cập nhật trạng thái máy (Busy, Maintenance, etc.)"""
    room = f'machine_{machine_id}'
    socketio.emit('status_update', status_data, room=room, namespace='/machine')


def emit_payment_status_update(machine_id, payment_data):
    """Thông báo cập nhật tiến trình thanh toán (ví dụ nạp tiền mặt)"""
    room = f'machine_{machine_id}'
    socketio.emit('payment_status_update', payment_data, room=room, namespace='/machine')


# ==========================================
# /admin Namespace (New)
# ==========================================

@socketio.on('connect', namespace='/admin')
def on_admin_connect(auth=None):
    if not _get_admin_user(auth):
        return False
    print(f"🔌 Admin WebSocket connected")


@socketio.on('subscribe_admin', namespace='/admin')
def on_admin_subscribe(data=None):
    """Admin subscribe vào room chung để nhận tất cả log/sự kiện"""
    if not _get_admin_user(data):
        emit('admin_subscription_error', {'message': 'Forbidden'})
        return
    join_room('admin_room')
    print(f"📢 Admin subscribed to global admin room")
    emit('admin_subscribed', {'status': 'active'})


def emit_admin_log(log_data):
    """Gửi log real-time lên Dashboard"""
    socketio.emit('admin_log', log_data, room='admin_room', namespace='/admin')


def emit_admin_order_new(order_data):
    """Thông báo khi có đơn hàng mới"""
    socketio.emit('admin_order_new', order_data, room='admin_room', namespace='/admin')


def emit_admin_machine_status(machine_id, status_data):
    """
    Thông báo trạng thái máy thay đổi cho Admin.
    """
    payload = {"machine_id": machine_id, **status_data}
    socketio.emit('admin_machine_status', payload, room='admin_room', namespace='/admin')


def emit_admin_stock_update(machine_id, stock_data):
    """
    Thông báo cập nhật tồn kho cho Admin.
    """
    payload = {"machine_id": machine_id, **stock_data}
    socketio.emit('admin_stock_update', payload, room='admin_room', namespace='/admin')


def emit_admin_device_auth_update(machine_id):
    """
    Thông báo khi trạng thái bảo mật của máy (Identity/Session) thay đổi.
    Để Admin UI tự động tải lại bảng hiển thị.
    """
    socketio.emit('admin_device_auth_update', {'machine_id': machine_id}, room='admin_room', namespace='/admin')



def emit_machine_command(machine_id, command, payload=None):
    """Gửi lệnh điều khiển trực tiếp tới máy cụ thể qua WebSocket"""
    if payload is None: payload = {}
    room = f'machine_{machine_id}'
    data = {'command': command, **payload}
    print(f"🚀 Sending command {command} to machine {machine_id}")
    socketio.emit('remote_command', data, room=room, namespace='/machine')
