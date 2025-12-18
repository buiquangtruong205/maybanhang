"""
Backend Main App - Flask Application cho máy bán hàng tự động
"""
from flask import Flask, render_template, request, redirect
import hmac
import hashlib
import json
import time

from services.payment_service import create_payment
from config import CHECKSUM_KEY
from models.order import init_db, create_order, update_order_status, get_orders

app = Flask(__name__, 
            template_folder='templates',
            static_folder='static')

# Khởi tạo database
init_db()


def verify_signature(data: dict, signature: str) -> bool:
    """Xác thực chữ ký từ PayOS webhook"""
    raw = json.dumps(data, separators=(",", ":"), ensure_ascii=False)
    check = hmac.new(
        CHECKSUM_KEY.encode(),
        raw.encode(),
        hashlib.sha256
    ).hexdigest()
    return check == signature


@app.route("/")
def index():
    """Trang chủ - Hiển thị danh sách đơn hàng"""
    orders = get_orders()
    return render_template("index.html", orders=orders)


@app.route("/pay", methods=["POST"])
def pay():
    """Tạo thanh toán mới"""
    order_code = int(time.time())
    amount = 2000

    create_order(order_code, amount)
    res = create_payment(order_code, amount)
    
    if res and "data" in res and res["data"] and "checkoutUrl" in res["data"]:
        return redirect(res["data"]["checkoutUrl"])
    else:
        print("PayOS API Error:", res)
        return f"Lỗi tạo thanh toán: {res}", 500


@app.route("/webhook", methods=["POST"])
def webhook():
    """Xử lý webhook callback từ PayOS"""
    payload = request.json
    signature = request.headers.get("x-payos-signature")

    if not verify_signature(payload, signature):
        return {"error": "invalid signature"}, 403

    data = payload["data"]
    if data["status"] == "PAID":
        update_order_status(data["orderCode"], "PAID")
        print("Đã thanh toán:", data["orderCode"])

    return {"success": True}


@app.route("/checkout/<int:order_code>")
def checkout(order_code):
    """Trang checkout cho đơn hàng"""
    return render_template("checkout.html", order_code=order_code, amount=1000)


@app.route("/success")
def success():
    """Trang thông báo thanh toán thành công"""
    return render_template("success.html")


@app.route("/cancel")
def cancel():
    """Trang thông báo thanh toán bị hủy"""
    return "Thanh toán bị hủy"


if __name__ == "__main__":
    app.run(debug=True)
