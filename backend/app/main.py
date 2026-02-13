from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.api.v1.router import api_router
from app.core.socket_manager import socket_app, sio
import socketio

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.api.v1.router import api_router
from app.core.socket_manager import socket_app, sio
import socketio

# 1. Khởi tạo FastAPI App
fastapi_app = FastAPI(
    title="Vending Machine API",
    description="API cho máy bán hàng tự động (Version 2)",
    version="2.0.0"
)

# 2. Cấu hình CORS cho FastAPI
fastapi_app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 3. Đăng ký Router
fastapi_app.include_router(api_router, prefix="/api/v1")

@fastapi_app.get("/")
async def root():
    return {
        "message": "API Máy Bán Hàng V2 đang hoạt động",
        "docs": "/docs",
        "db_status": "Đã kết nối"
    }

# 4. Wrap FastAPI bằng Socket.IO (Final App)
# Biến 'app' này sẽ được Uvicorn chạy
app = socketio.ASGIApp(sio, other_asgi_app=fastapi_app)
