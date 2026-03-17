# Ghi Chú Bảo Mật Hệ Thống Bán Hàng

Tài liệu này ghi chú các cấu hình bảo mật hiện có trong dự án, tập trung vào Nginx, CORS và WebSocket.

## 1. Cấu hình Nginx (Security Headers)

**File bị ảnh hưởng:** `nginx.conf`

**Mục đích:** Thêm các HTTP headers để trình duyệt của Client tự động phòng vệ trước các kiểu tấn công phổ biến trên không gian mạng như XSS (Cross-site Scripting), Clickjacking, và MIME-sniffing.

**Đoạn cấu hình đã áp dụng:**
```nginx
server {
    listen 80;
    server_name localhost;

    # --- ĐOẠN BẢO MẬT ĐÃ THÊM ---
    # Chống Clickjacking: Ngăn không cho website khác nhúng trang của bạn vào iFrame.
    add_header X-Frame-Options "SAMEORIGIN";
    
    # Chống XSS (Cross-Site Scripting): Yêu cầu trình duyệt khóa trang nếu phát hiện có mã độc XSS được chèn vào.
    add_header X-XSS-Protection "1; mode=block";
    
    # Chống MIME-sniffing: Yêu cầu trình duyệt tuân thủ chặt chẽ Content-Type do server trả về, không tự ý đoán.
    add_header X-Content-Type-Options "nosniff";
    
    # Referrer Policy: Tránh rò rỉ URL (có thể chứa thông tin nhạy cảm) khi request sang domain khác.
    add_header Referrer-Policy "strict-origin-when-cross-origin";
    # ----------------------------

    # (Các cấu hình Proxy và Static files vẫn giữ nguyên bên dưới)
}
```

## 2. Cấu hình API Backend Flask (CORS)

**File bị ảnh hưởng:** `backend/app/__init__.py`

**Mục đích:** Thay vì cho phép bất kỳ trang web nào (Origin `*`) cũng có thể gửi request đến API, hệ thống sẽ đọc danh sách domain cho phép từ biến môi trường `CORS_ORIGINS`.

**Đoạn code xử lý bảo mật:**
```python
    @app.after_request
    def after_request(response):
        # --- ĐOẠN BẢO MẬT ĐÃ THAY ĐỔI ---
        # Đọc danh sách Origin được phép từ biến môi trường (ví dụ: https://domain-frontend.com).
        # Nếu không có, mặc định trả về '*' để hệ thống cũ không bị lỗi (Backward Compatibility).
        cors_origins = os.environ.get('CORS_ORIGINS', '*')
        response.headers.add('Access-Control-Allow-Origin', cors_origins)
        # --------------------------------
        
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization,X-Machine-Key')
        response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE,OPTIONS')
        
        # ... logic logging tiếp tục ...
```

## 3. Cấu hình WebSockets (CORS)

**File bị ảnh hưởng:** `backend/app/websocket.py`

**Mục đích:** Ngăn chặn các trang web ngoài luồng mở kết nối WebSocket (real-time realtime socketio traffic) tới server. Cùng logic với API, SocketIO cũng sẽ dựa vào `CORS_ORIGINS`.

**Đoạn code xử lý bảo mật:**
```python
import os
from flask_socketio import SocketIO, emit, join_room, leave_room

# --- ĐOẠN BẢO MẬT ĐÃ THAY ĐỔI ---
# Khởi tạo SocketIO với tuỳ chọn CORS động từ biến môi trường.
cors_origins = os.environ.get('CORS_ORIGINS', '*')

# SocketIO yêu cầu truyền list ['url1', 'url2'] nếu không phải là '*'
if cors_origins != '*':
    cors_origins = cors_origins.split(',')
    
socketio = SocketIO(cors_allowed_origins=cors_origins, async_mode='threading')
# --------------------------------
```

## 4. Xác lập cấu hình Origin an toàn (Biến môi trường)

**File bị ảnh hưởng:** `.env`

**Mục đích:** Mọi cấu hình bảo mật động đều tập trung ở file `.env`, giúp bạn không cần phải sửa nội dung code gốc (Python) mỗi lần muốn thêm bớt domain frontend hợp lệ.

**Đoạn cấu hình đã thêm (Ở cuối file):**
```env
# Security (CORS)
# Uncomment (xoá dấu #) và set domain của các trang Frontend được phép kết nối đến API/Websocket.
# Chỉ cung cấp domain gốc, không có path phía sau (ví dụ: http://localhost:5173,https://myvending.com)
# Bỏ trống biến này thì hệ thống sẽ reset về '*' (Cho phép tất cả).
# CORS_ORIGINS=http://localhost,http://localhost:5173,https://your-domain.com
```

## Hướng dẫn Vận hành và Cập nhật Môi trường

Bất cứ khi nào bạn chỉnh sửa file `.env` (ví dụ bỏ comment và điền domain vào `CORS_ORIGINS`), bạn phải yêu cầu Docker lấy lại giá trị mới và build lại Container Backend và Nginx.

**Chạy các lệnh sau trong terminal tại thư mục gốc của server:**

```bash
# Tắt hệ thống hiện tại
docker-compose down

# Khởi chạy lại với các cấu hình mới
docker-compose build
docker-compose up -d
```
