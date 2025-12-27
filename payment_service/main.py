"""
Payment Service - Điểm khởi động ứng dụng
"""
import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import PORT
from app.routers import payment, products

# Khởi tạo FastAPI app
app = FastAPI(
    title="Vending Machine API",
    description="API cho máy bán hàng tự động với PayOS",
    version="1.0.0"
)

# Cấu hình CORS - cho phép frontend truy cập API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Cho phép tất cả origins (có thể giới hạn sau)
    allow_credentials=True,
    allow_methods=["*"],  # GET, POST, PUT, DELETE, etc.
    allow_headers=["*"],  # Cho phép tất cả headers
)

# Đăng ký router
app.include_router(payment.router)
app.include_router(products.router)

if __name__ == "__main__":
    print(f"🚀 Server đang chạy tại http://localhost:{PORT}")
    uvicorn.run(app, host="0.0.0.0", port=PORT)