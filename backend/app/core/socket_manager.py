import socketio

# Khởi tạo Socket.IO Server (Async)
# Khởi tạo Socket.IO Server (Async)
# cors_allowed_origins="*" cho phép mọi nguồn kết nối (Dev mode), hoặc list cụ thể
sio = socketio.AsyncServer(
    async_mode='asgi', 
    cors_allowed_origins='*',
    logger=True, # Bật log để debug
    engineio_logger=True
)

# Wrap bằng ASGIApp để mount vào FastAPI
socket_app = socketio.ASGIApp(sio)

@sio.event
async def connect(sid, environ):
    print(f"✅ Client connected: {sid}")

@sio.event
async def disconnect(sid):
    print(f"❌ Client disconnected: {sid}")

async def broadcast_order_update(order_data: dict):
    """Gửi sự kiện cập nhật đơn hàng tới tất cả client"""
    try:
        await sio.emit('order_update', order_data)
        # print(f"📡 Emitted order_update: {order_data.get('order_code')}") # Tắt log theo yêu cầu user
    except Exception as e:
        print(f"⚠️ Socket emit error: {e}")

async def broadcast_issue_update(issue_data: dict):
    """Gửi sự kiện báo cáo sự cố tới tất cả client"""
    try:
        await sio.emit('issue_update', issue_data)
    except Exception as e:
        print(f"⚠️ Socket emit error: {e}")
