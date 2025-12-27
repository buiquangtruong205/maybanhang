"""
Dịch vụ PayOS - xử lý logic tạo link thanh toán
"""
import re
from payos import PayOS
from app.config import PAYOS_CLIENT_ID, PAYOS_API_KEY, PAYOS_CHECKSUM_KEY

# Khởi tạo instance PayOS
payos = PayOS(
    client_id=PAYOS_CLIENT_ID,
    api_key=PAYOS_API_KEY,
    checksum_key=PAYOS_CHECKSUM_KEY
)


def extract_checkout_url(response) -> str | None:
    """
    Trích xuất checkout URL từ response của PayOS.
    Thử nhiều cách khác nhau để đảm bảo lấy được link.
    """
    checkout_url = None

    # Cách 1: Lấy thuộc tính trực tiếp
    if hasattr(response, "checkout_url"):
        checkout_url = response.checkout_url
    elif hasattr(response, "checkoutUrl"):
        checkout_url = response.checkoutUrl
    elif isinstance(response, dict):
        checkout_url = response.get("checkout_url") or response.get("checkoutUrl")

    # Cách 2: Dùng Regex nếu cách 1 thất bại
    if not checkout_url:
        print("⚠️ Đang dùng Regex để tìm link...")
        response_str = str(response)
        match = re.search(r"checkout_url='([^']+)'", response_str)
        if match:
            checkout_url = match.group(1)

    return checkout_url


def create_payment_link(order_code: int, amount: int, description: str, items: list) -> dict:
    """
    Tạo link thanh toán PayOS.
    
    Args:
        order_code: Mã đơn hàng (unique)
        amount: Số tiền (VND)
        description: Mô tả đơn hàng
        items: Danh sách sản phẩm [{"name": str, "quantity": int, "price": int}]
    
    Returns:
        dict với checkout_url hoặc error
    """
    from app.config import DOMAIN
    
    try:
        payment_data = {
            "orderCode": order_code,
            "amount": amount,
            "description": description,
            "items": items,
            "returnUrl": f"{DOMAIN}/success",
            "cancelUrl": f"{DOMAIN}/cancel"
        }

        # Gọi API PayOS
        service = payos.payment_requests
        if hasattr(service, "create"):
            response = service.create(payment_data)
        else:
            response = service.create_payment_link(payment_data)

        checkout_url = extract_checkout_url(response)
        print(f"👉 Link thanh toán: {checkout_url}")

        if checkout_url:
            return {"success": True, "checkout_url": checkout_url}
        else:
            return {"success": False, "error": "Không lấy được link thanh toán", "raw": str(response)}

    except Exception as e:
        print(f"❌ LỖI: {str(e)}")
        return {"success": False, "error": str(e)}
