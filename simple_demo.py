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
    
    # Sử dụng mock payment thay vì PayOS API
    res = create_mock_payment(order_code, amount)
    
    if res and "data" in res and "checkoutUrl" in res["data"]:
        return redirect(res["data"]["checkoutUrl"])
    else:
        return "Lỗi tạo thanh toán demo", 500

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