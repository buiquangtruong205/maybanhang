"""
Dịch vụ PayOS - xử lý logic tạo link thanh toán (không dùng thư viện PayOS)
"""
import hmac
import hashlib
import json
import requests
from app.config import PAYOS_CLIENT_ID, PAYOS_API_KEY, PAYOS_CHECKSUM_KEY, DOMAIN

# API endpoint PayOS
PAYOS_API_URL = "https://api-merchant.payos.vn/v2"

# Kiểm tra cấu hình PayOS
print(f"[PayOS] ID: {PAYOS_CLIENT_ID[:5] if PAYOS_CLIENT_ID else 'None'}... API: {PAYOS_API_KEY[:5] if PAYOS_API_KEY else 'None'}...")
if PAYOS_CLIENT_ID and PAYOS_API_KEY and PAYOS_CHECKSUM_KEY:
    print("[PayOS] Credentials configured")
else:
    print("[PayOS] WARNING: Credentials not configured or empty. Please check .env file.")


def _create_signature(data_to_sign: dict) -> str:
    """
    Tạo chữ ký HMAC_SHA256 cho PayOS.
    
    Args:
        data_to_sign: Dict chứa các field cần ký (sắp xếp theo alphabet)
    
    Returns:
        Signature hex string
    """
    # Sắp xếp theo alphabet và tạo chuỗi: key1=value1&key2=value2...
    sorted_data = sorted(data_to_sign.items())
    sign_str = "&".join([f"{k}={v}" for k, v in sorted_data])
    
    # Tạo chữ ký HMAC_SHA256
    signature = hmac.new(
        key=PAYOS_CHECKSUM_KEY.encode(),
        msg=sign_str.encode(),
        digestmod=hashlib.sha256
    ).hexdigest()
    
    return signature


def create_payment_link(
    order_code: int, 
    amount: int, 
    description: str, 
    items: list,
    buyer_name: str = None,
    buyer_email: str = None,
    buyer_phone: str = None,
    buyer_address: str = None
) -> dict:
    """
    Tạo link thanh toán PayOS (không dùng thư viện).
    Tự động tạo order_code duy nhất để tránh lỗi duplicate.
    
    Args:
        order_code: Mã đơn hàng gốc (order_id từ database)
        amount: Số tiền (VND)
        description: Mô tả đơn hàng
        items: Danh sách sản phẩm [{"name": str, "quantity": int, "price": int}]
        buyer_name: Tên người mua
        buyer_email: Email người mua
        buyer_phone: Số điện thoại người mua
        buyer_address: Địa chỉ người mua
    
    Returns:
        dict với checkout_url, qr_code hoặc error
    """
    if not PAYOS_CLIENT_ID or not PAYOS_API_KEY or not PAYOS_CHECKSUM_KEY:
        return {"success": False, "error": "PayOS not configured. Check credentials in .env file"}
    
    try:
        import time
        
        # Tạo unique payment_code bằng cách kết hợp order_id với timestamp
        # Format: order_id * 10000 + random suffix (để tránh trùng khi tạo nhiều lần)
        # VD: order_id=3 -> payment_code = 30000 + (seconds % 9999) = 30001, 30002, ...
        timestamp_suffix = int(time.time()) % 9999 + 1  # 1-9999
        unique_payment_code = order_code * 10000 + timestamp_suffix
        
        print(f"🔢 Generated unique payment_code: {unique_payment_code} (from order_id: {order_code})")
        
        return_url = f"{DOMAIN}/api/payment/success"
        cancel_url = f"{DOMAIN}/api/payment/cancel"
        
        # 1. Chuẩn bị dữ liệu để tạo chữ ký (Signature)
        # PayOS yêu cầu sắp xếp theo alphabet: amount, cancelUrl, description, orderCode, returnUrl
        # Sử dụng unique_payment_code để tránh lỗi duplicate
        data_to_sign = {
            "amount": amount,
            "cancelUrl": cancel_url,
            "description": description,
            "orderCode": unique_payment_code,  # Dùng unique code thay vì order_id
            "returnUrl": return_url
        }
        
        # 2. Tạo chữ ký HMAC_SHA256
        signature = _create_signature(data_to_sign)
        
        # 3. Tạo body gửi đi (Thêm signature và items)
        payload = {
            **data_to_sign,
            "signature": signature,
            "items": items if items else []
        }
        
        # Thêm thông tin người mua nếu có
        if buyer_name:
            payload["buyerName"] = buyer_name
        if buyer_email:
            payload["buyerEmail"] = buyer_email
        if buyer_phone:
            payload["buyerPhone"] = buyer_phone
        if buyer_address:
            payload["buyerAddress"] = buyer_address
        
        headers = {
            "x-client-id": PAYOS_CLIENT_ID,
            "x-api-key": PAYOS_API_KEY,
            "Content-Type": "application/json"
        }
        
        print(f"📤 Creating payment: payment_code={unique_payment_code}, order_id={order_code}, amount={amount}")
        
        # 4. Gửi request
        url = f"{PAYOS_API_URL}/payment-requests"
        response = requests.post(url, headers=headers, json=payload)
        resp_data = response.json()
        
        print(f"📥 PayOS response: {resp_data}")
        
        if resp_data.get("code") == "00" and resp_data.get("data"):
            checkout_url = resp_data["data"].get("checkoutUrl") or resp_data["data"].get("checkout_url")
            qr_code = resp_data["data"].get("qrCode") or resp_data["data"].get("qr_code")
            
            print(f"✅ Link thanh toán: {checkout_url}")
            print(f"✅ QR Code: {qr_code}")
            
            return {
                "success": True,
                "checkout_url": checkout_url,
                "qr_code": qr_code,
                "payment_code": unique_payment_code  # Trả về payment_code để tracking
            }
        else:
            error_msg = resp_data.get("desc") or resp_data.get("message") or "Unknown error"
            print(f"❌ PayOS error: {error_msg}")
            return {"success": False, "error": f"PayOS Error: {error_msg}"}
    
    except Exception as e:
        import traceback
        print(f"❌ LỖI PayOS API: {str(e)}")
        traceback.print_exc()
        return {"success": False, "error": f"PayOS Error: {str(e)}"}


def get_payment_status(order_code: int) -> dict:
    """
    Kiểm tra trạng thái thanh toán của đơn hàng.
    
    Args:
        order_code: Mã đơn hàng
        
    Returns:
        dict với thông tin trạng thái thanh toán
    """
    if not PAYOS_CLIENT_ID or not PAYOS_API_KEY or not PAYOS_CHECKSUM_KEY:
        return {"success": False, "error": "PayOS not configured"}
    
    try:
        url = f"{PAYOS_API_URL}/payment-requests/{order_code}"
        headers = {
            "x-client-id": PAYOS_CLIENT_ID,
            "x-api-key": PAYOS_API_KEY,
            "Content-Type": "application/json"
        }
        
        response = requests.get(url, headers=headers)
        resp_data = response.json()
        
        print(f"📊 Payment status response: {resp_data}")
        
        if resp_data.get("code") == "00" and resp_data.get("data"):
            data = resp_data["data"]
            
            # Parse response
            status = data.get("status", "unknown")
            amount = data.get("amount")
            amount_paid = data.get("amountPaid") or data.get("amount_paid")
            amount_remaining = data.get("amountRemaining") or data.get("amount_remaining")
            transactions = data.get("transactions", [])
            
            return {
                "success": True,
                "order_code": order_code,
                "status": status,
                "amount": amount,
                "amount_paid": amount_paid,
                "amount_remaining": amount_remaining,
                "transactions": transactions
            }
        else:
            error_msg = resp_data.get("desc") or resp_data.get("message") or "Unknown error"
            return {"success": False, "error": error_msg}
        
    except Exception as e:
        print(f"❌ Error getting payment status: {str(e)}")
        return {"success": False, "error": str(e)}


def cancel_payment(order_code: int) -> dict:
    """
    Hủy link thanh toán đang chờ.
    
    Args:
        order_code: Mã đơn hàng
        
    Returns:
        dict kết quả hủy
    """
    if not PAYOS_CLIENT_ID or not PAYOS_API_KEY or not PAYOS_CHECKSUM_KEY:
        return {"success": False, "error": "PayOS not configured"}
    
    try:
        url = f"{PAYOS_API_URL}/payment-requests/{order_code}/cancel"
        headers = {
            "x-client-id": PAYOS_CLIENT_ID,
            "x-api-key": PAYOS_API_KEY,
            "Content-Type": "application/json"
        }
        
        response = requests.post(url, headers=headers)
        resp_data = response.json()
        
        print(f"🚫 Cancel payment response: {resp_data}")
        
        if resp_data.get("code") == "00":
            return {"success": True, "message": "Payment cancelled"}
        else:
            error_msg = resp_data.get("desc") or resp_data.get("message") or "Unknown error"
            return {"success": False, "error": error_msg}
        
    except Exception as e:
        print(f"❌ Error cancelling payment: {str(e)}")
        return {"success": False, "error": str(e)}


def verify_webhook_signature(payload: dict, signature: str) -> bool:
    """
    Xác minh chữ ký webhook từ PayOS.
    
    Args:
        payload: Dữ liệu webhook
        signature: Chữ ký từ PayOS
        
    Returns:
        bool - True nếu signature hợp lệ
    """
    if not PAYOS_CHECKSUM_KEY:
        print("⚠️ Cannot verify signature - PAYOS_CHECKSUM_KEY not set")
        return True  # Skip verification if no key
    
    try:
        # Tạo chuỗi để verify (theo tài liệu PayOS)
        data_to_sign = json.dumps(payload.get("data", {}), separators=(',', ':'), ensure_ascii=False)
        
        expected_signature = hmac.new(
            PAYOS_CHECKSUM_KEY.encode('utf-8'),
            data_to_sign.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
        
        is_valid = hmac.compare_digest(expected_signature, signature)
        
        if not is_valid:
            print(f"⚠️ Signature mismatch: expected={expected_signature}, got={signature}")
        
        return is_valid
        
    except Exception as e:
        print(f"❌ Error verifying signature: {str(e)}")
        return False
