#!/usr/bin/env python3
"""
Demo đơn giản PayOS - Tạo link thanh toán giả lập
"""
from flask import Flask, render_template, request, redirect
import time
import random

app = Flask(__name__)

# Giả lập PayOS response
def create_mock_payment(order_code, amount):
    """Tạo link thanh toán giả lập để test giao diện"""
    
    # Tạo URL giả lập
    mock_checkout_url = f"https://pay.payos.vn/web/{order_code}?amount={amount}"
    
    return {
        "code": "00",
        "desc": "Success",
        "data": {
            "checkoutUrl": mock_checkout_url,
            "paymentLinkId": f"pl_{order_code}",
            "orderCode": order_code,
            "qrCode": f"https://api.qrserver.com/v1/create-qr-code/?size=200x200&data={mock_checkout_url}"
        }
    }

@app.route("/")
def index():
    return '''
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <title>PayOS Demo</title>
        <style>
            body { font-family: Arial, sans-serif; max-width: 600px; margin: 50px auto; padding: 20px; }
            .btn { background: #007bff; color: white; padding: 10px 20px; border: none; border-radius: 5px; cursor: pointer; }
            .btn:hover { background: #0056b3; }
        </style>
    </head>
    <body>
        <h2>🚀 PayOS Demo - Test Giao Diện</h2>
        <p>Đây là demo giả lập để test giao diện khi PayOS API chưa hoạt động.</p>
        
        <form method="post" action="/pay">
            <button type="submit" class="btn">💳 Thanh toán 50.000đ (Demo)</button>
        </form>
        
        <hr>
        <h3>📋 Hướng dẫn sửa lỗi PayOS:</h3>
        <ol>
            <li><strong>Kiểm tra tài khoản:</strong> Đăng nhập payos.vn và xác minh tài khoản đầy đủ</li>
            <li><strong>Liên hệ support:</strong> Gửi email tới support@payos.vn với thông tin lỗi</li>
            <li><strong>Kiểm tra API keys:</strong> Tạo lại CLIENT_ID, API_KEY, CHECKSUM_KEY mới</li>
            <li><strong>Đọc tài liệu:</strong> Xem https://payos.vn/docs để cập nhật API mới nhất</li>
        </ol>
    </body>
    </html>
    '''

@app.route("/pay", methods=["POST"])
def pay():
    order_code = int(time.time())
    amount = 50000
    
    # Redirect đến trang checkout local thay vì PayOS thật
    return redirect(f"/checkout/{order_code}?amount={amount}")

@app.route("/checkout/<int:order_code>")
def checkout(order_code):
    amount = request.args.get('amount', 50000, type=int)
    return f'''
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <title>PayOS Demo Checkout</title>
        <style>
            body {{ 
                font-family: Arial, sans-serif; 
                max-width: 600px; 
                margin: 50px auto; 
                padding: 20px;
                background: #f5f5f5;
            }}
            .checkout-container {{
                background: white;
                padding: 30px;
                border-radius: 10px;
                box-shadow: 0 2px 10px rgba(0,0,0,0.1);
                text-align: center;
            }}
            .qr-code {{
                margin: 20px 0;
                padding: 20px;
                border: 2px dashed #007bff;
                border-radius: 10px;
            }}
            .amount {{
                font-size: 24px;
                font-weight: bold;
                color: #007bff;
                margin: 10px 0;
            }}
            .order-info {{
                background: #f8f9fa;
                padding: 15px;
                border-radius: 5px;
                margin: 20px 0;
            }}
            .btn {{
                background: #28a745;
                color: white;
                padding: 10px 20px;
                border: none;
                border-radius: 5px;
                cursor: pointer;
                margin: 10px;
                text-decoration: none;
                display: inline-block;
            }}
            .btn:hover {{ background: #218838; }}
            .btn-cancel {{
                background: #dc3545;
            }}
            .btn-cancel:hover {{ background: #c82333; }}
            .demo-notice {{
                background: #fff3cd;
                color: #856404;
                padding: 10px;
                border-radius: 5px;
                margin-bottom: 20px;
                border: 1px solid #ffeaa7;
            }}
        </style>
    </head>
    <body>
        <div class="checkout-container">
            <div class="demo-notice">
                <strong>🚧 DEMO MODE:</strong> Đây là trang checkout giả lập hoàn toàn local.
            </div>
            
            <h2>💳 Thanh toán PayOS Demo</h2>
            
            <div class="order-info">
                <p><strong>Mã đơn hàng:</strong> #{order_code}</p>
                <p><strong>Mô tả:</strong> Demo thanh toán đơn #{order_code}</p>
                <div class="amount">{amount:,} VND</div>
            </div>
            
            <div class="qr-code">
                <h3>🏦 QR Code Demo (VietQR thật)</h3>
                <img src="https://img.vietqr.io/image/970415-0342132518-compact2.jpg?amount={amount}&addInfo=DH{order_code}&accountName=BUI QUANG TRUONG" 
                     alt="VietQR Code" style="max-width: 250px; border: 1px solid #ddd;">
                
                <div style="margin-top: 15px; font-size: 14px; text-align: left;">
                    <p><strong>🏦 Ngân hàng:</strong> Vietinbank</p>
                    <p><strong>📱 Số tài khoản:</strong> 0342132518</p>
                    <p><strong>👤 Chủ tài khoản:</strong> BUI QUANG TRUONG</p>
                    <p><strong>💬 Nội dung:</strong> DH{order_code}</p>
                    <p><strong>💰 Số tiền:</strong> {amount:,} VND</p>
                </div>
                
                <p style="color: #28a745; font-weight: bold; margin-top: 15px;">
                    ✅ QR Code thật - Có thể chuyển khoản ngay!
                </p>
            </div>
            
            <div>
                <a href="/success" class="btn">✅ Giả lập thanh toán thành công</a>
                <a href="/cancel" class="btn btn-cancel">❌ Hủy thanh toán</a>
            </div>
            
            <p><a href="/">🏠 Quay về trang chủ</a></p>
        </div>
    </body>
    </html>
    '''

@app.route("/cancel")
def cancel():
    return '''
    <h2>❌ Thanh toán bị hủy (Demo)</h2>
    <p>Bạn đã hủy giao dịch demo.</p>
    <a href="/">🔙 Quay về trang chủ</a>
    '''

@app.route("/success")
def success():
    return '''
    <h2>✅ Thanh toán thành công (Demo)</h2>
    <p>Đây là trang demo. Trong thực tế, PayOS sẽ redirect về đây sau khi thanh toán.</p>
    <a href="/">🔙 Quay về</a>
    '''

if __name__ == "__main__":
    print("🚀 Chạy PayOS Demo tại: http://localhost:5000")
    print("📝 Đây là demo giả lập để test giao diện")
    app.run(debug=True, port=5000)