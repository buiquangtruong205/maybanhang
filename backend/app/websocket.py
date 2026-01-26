"""
WebSocket module for real-time payment notifications
Uses Flask-SocketIO for WebSocket support
"""
from flask_socketio import SocketIO, emit, join_room, leave_room

# Initialize SocketIO with CORS support
socketio = SocketIO(cors_allowed_origins="*", async_mode='eventlet')

# Track connected clients per order
connected_clients = {}


@socketio.on('connect', namespace='/payment')
def on_connect():
    """Handle new WebSocket connection"""
    print(f"🔌 WebSocket client connected")


@socketio.on('disconnect', namespace='/payment')
def on_disconnect():
    """Handle WebSocket disconnection"""
    print(f"🔌 WebSocket client disconnected")


@socketio.on('subscribe', namespace='/payment')
def on_subscribe(data):
    """Subscribe to payment updates for a specific order"""
    order_id = data.get('order_id')
    if order_id:
        room = f'order_{order_id}'
        join_room(room)
        print(f"📢 Client subscribed to room: {room}")
        emit('subscribed', {'order_id': order_id, 'status': 'subscribed'})


@socketio.on('unsubscribe', namespace='/payment')
def on_unsubscribe(data):
    """Unsubscribe from payment updates"""
    order_id = data.get('order_id')
    if order_id:
        room = f'order_{order_id}'
        leave_room(room)
        print(f"📢 Client unsubscribed from room: {room}")


def emit_payment_success(order_id, data=None):
    """
    Emit payment success event to all clients subscribed to the order
    
    Args:
        order_id: The order ID that was paid
        data: Additional data to include (amount, payment_code, etc.)
    """
    if data is None:
        data = {}
    
    room = f'order_{order_id}'
    payload = {
        'order_id': order_id,
        'status': 'completed',
        **data
    }
    
    print(f"📤 Emitting payment_success to room {room}: {payload}")
    socketio.emit('payment_success', payload, room=room, namespace='/payment')


def emit_payment_failed(order_id, reason=None):
    """
    Emit payment failed event to all clients subscribed to the order
    
    Args:
        order_id: The order ID that failed
        reason: Reason for failure
    """
    room = f'order_{order_id}'
    payload = {
        'order_id': order_id,
        'status': 'failed',
        'reason': reason or 'Payment failed'
    }
    
    print(f"📤 Emitting payment_failed to room {room}: {payload}")
    socketio.emit('payment_failed', payload, room=room, namespace='/payment')


def emit_payment_cancelled(order_id):
    """
    Emit payment cancelled event to all clients subscribed to the order
    
    Args:
        order_id: The order ID that was cancelled
    """
    room = f'order_{order_id}'
    payload = {
        'order_id': order_id,
        'status': 'cancelled'
    }
    
    print(f"📤 Emitting payment_cancelled to room {room}: {payload}")
    socketio.emit('payment_cancelled', payload, room=room, namespace='/payment')
