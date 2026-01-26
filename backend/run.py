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
import argparse

# Add backend directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app
from app.websocket import socketio

app = create_app()

def parse_args():
    parser = argparse.ArgumentParser(description='Run Flask backend server with WebSocket')
    parser.add_argument('--host', type=str, default='0.0.0.0',
                        help='Host to bind to (default: 0.0.0.0)')
    parser.add_argument('--port', type=int, default=5000,
                        help='Port to bind to (default: 5000)')
    return parser.parse_args()


if __name__ == '__main__':
    args = parse_args()
    
    print(f"\n🚀 Starting server (HTTP + WebSocket mode)")
    print(f"   HTTP URL: http://{args.host}:{args.port}")
    print(f"   WebSocket: ws://{args.host}:{args.port}/payment")
    
    print()
    # Use socketio.run() instead of app.run() for WebSocket support
    socketio.run(
        app, 
        debug=True, 
        host=args.host, 
        port=args.port,
        allow_unsafe_werkzeug=True  # Allow debug mode with eventlet
    )

