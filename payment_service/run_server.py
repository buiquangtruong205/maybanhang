#!/usr/bin/env python3
"""
Script chạy server development
"""
import uvicorn
import sys
from pathlib import Path

# Add current directory to Python path
sys.path.append(str(Path(__file__).parent))

from main import app

if __name__ == "__main__":
    print("🚀 Starting Vending Machine API Server...")
    print("📡 Server sẽ chạy tại: http://0.0.0.0:5000")
    print("🌐 Truy cập từ mạng: http://172.16.1.217:5000")
    print("📋 API Documentation: http://172.16.1.217:5000/docs")
    print("📦 Products API: http://172.16.1.217:5000/api/products")
    print("\n⚡ Nhấn Ctrl+C để dừng server")
    
    uvicorn.run(
        app, 
        host="0.0.0.0", 
        port=5000,
        reload=True,
        log_level="info"
    )