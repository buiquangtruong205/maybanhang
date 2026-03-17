"""
Dịch vụ PayOS - xử lý logic tạo link thanh toán (không dùng thư viện PayOS)
"""
import hmac
import hashlib
import secrets
import requests
from app.config import PAYOS_CLIENT_ID, PAYOS_API_KEY, PAYOS_CHECKSUM_KEY, DOMAIN

# API endpoint PayOS
PAYOS_API_URL = "https://api-merchant.payos.vn/v2"
PAYOS_TIMEOUT = 15

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
    sorted_data = sorted(
        (key, value)
        for key, value in data_to_sign.items()
        if value is not None and key != "signature"
    )
    sign_str = "&".join([f"{k}={v}" for k, v in sorted_data])
    
    # Tạo chữ ký HMAC_SHA256
    signature = hmac.new(
        key=PAYOS_CHECKSUM_KEY.encode(),
        msg=sign_str.encode(),
        digestmod=hashlib.sha256
    ).hexdigest()
    
    return signature


def _payos_headers() -> dict:
    return {
        "x-client-id": PAYOS_CLIENT_ID,
        "x-api-key": PAYOS_API_KEY,
        "Content-Type": "application/json"
    }


def _request_payos(method: str, path: str, json_body=None) -> dict:
    url = f"{PAYOS_API_URL}{path}"

    try:
        response = requests.request(
            method=method,
            url=url,
            headers=_payos_headers(),
            json=json_body,
            timeout=PAYOS_TIMEOUT
        )
    except requests.Timeout:
        return {"success": False, "error": "Yêu cầu tới PayOS bị quá thời gian chờ"}
    except requests.RequestException as exc:
        return {"success": False, "error": f"Yêu cầu tới PayOS thất bại: {exc}"}

    try:
        resp_data = response.json()
    except ValueError:
        return {
            "success": False,
            "error": f"PayOS trả về dữ liệu không phải JSON với HTTP {response.status_code}"
        }

    if response.ok:
        return {"success": True, "data": resp_data}

    error_msg = resp_data.get("desc") or resp_data.get("message") or f"HTTP {response.status_code}"
    return {"success": False, "error": error_msg, "data": resp_data}


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
        return {"success": False, "error": "PayOS chưa được cấu hình. Hãy kiểm tra biến môi trường trong .env"}
    
    try:
        # Tạo unique payment_code bằng cách kết hợp order_id với suffix ngẫu nhiên 4 chữ số.
        # Format: order_id * 10000 + suffix
        # suffix luôn nằm trong khoảng 1..9999 để vẫn parse lại được order_id bằng // 10000.
        random_suffix = secrets.randbelow(9999) + 1
        unique_payment_code = order_code * 10000 + random_suffix
        
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
        
        print(f"📤 Creating payment: payment_code={unique_payment_code}, order_id={order_code}, amount={amount}")
        
        # 4. Gửi request
        response = _request_payos("POST", "/payment-requests", json_body=payload)
        if not response.get("success"):
            print(f"❌ PayOS error: {response['error']}")
            return {"success": False, "error": f"Lỗi PayOS: {response['error']}"}

        resp_data = response["data"]
        
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
            error_msg = resp_data.get("desc") or resp_data.get("message") or "Lỗi không xác định"
            print(f"❌ PayOS error: {error_msg}")
            return {"success": False, "error": f"Lỗi PayOS: {error_msg}"}
    
    except Exception as e:
        import traceback
        print(f"❌ LỖI PayOS API: {str(e)}")
        traceback.print_exc()
        return {"success": False, "error": f"Lỗi PayOS: {str(e)}"}


def get_payment_status(order_code: int) -> dict:
    """
    Kiểm tra trạng thái thanh toán của đơn hàng.
    
    Args:
        order_code: Mã đơn hàng
        
    Returns:
        dict với thông tin trạng thái thanh toán
    """
    if not PAYOS_CLIENT_ID or not PAYOS_API_KEY or not PAYOS_CHECKSUM_KEY:
        return {"success": False, "error": "PayOS chưa được cấu hình"}
    
    try:
        response = _request_payos("GET", f"/payment-requests/{order_code}")
        if not response.get("success"):
            return {"success": False, "error": response["error"]}

        resp_data = response["data"]
        
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
            error_msg = resp_data.get("desc") or resp_data.get("message") or "Lỗi không xác định"
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
        return {"success": False, "error": "PayOS chưa được cấu hình"}
    
    try:
        response = _request_payos("POST", f"/payment-requests/{order_code}/cancel")
        if not response.get("success"):
            return {"success": False, "error": response["error"]}

        resp_data = response["data"]
        
        print(f"🚫 Cancel payment response: {resp_data}")
        
        if resp_data.get("code") == "00":
            return {"success": True, "message": "Đã hủy thanh toán"}
        else:
            error_msg = resp_data.get("desc") or resp_data.get("message") or "Lỗi không xác định"
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
        webhook_data = payload.get("data", {})
        if not isinstance(webhook_data, dict):
            print("⚠️ Webhook payload data is not a dict")
            return False

        expected_signature = _create_signature(webhook_data)
        
        is_valid = hmac.compare_digest(expected_signature, signature)
        
        if not is_valid:
            print(f"⚠️ Signature mismatch: expected={expected_signature}, got={signature}")
        
        return is_valid
        
    except Exception as e:
        print(f"❌ Error verifying signature: {str(e)}")
        return False
