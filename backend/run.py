"""
Run script for the Flask backend with WebSocket support

Usage:
    python run.py                    # HTTP mode with WebSocket
    python run.py --host 0.0.0.0     # Bind to all interfaces
    python run.py --port 5000        # Specify port
    
Run from backend directory: python run.py
"""
import sys
import os
# hello
# Add backend directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app
from app.websocket import socketio

app = create_app()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))

