import random
import time
from datetime import datetime

def generate_order_code() -> int:
    """
    Tạo mã đơn hàng ngẫu nhiên (dạng số nguyên) để tương thích với PayOS.
    Duy nhất tương đối dựa trên timestamp + số ngẫu nhiên.
    """
    timestamp = int(time.time()) % 1000000
    random_part = random.randint(1000, 9999)
    return int(f"{timestamp}{random_part}")

def format_db_time(dt: datetime) -> str:
    """Định dạng thời gian từ database ra chuỗi hiển thị."""
    if not dt:
        return ""
    return dt.strftime("%Y-%m-%d %H:%M:%S")

def calculate_total_amount(price: int, quantity: int = 1) -> int:
    """Tính tổng tiền (có thể mở rộng thêm giảm giá/thuế)."""
    return price * quantity
