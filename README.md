# Vending Machine Project

Dự án **máy bán hàng tự động tích hợp IoT** cho phép quản lý và vận hành máy bán hàng thông minh từ xa. Hệ thống bao gồm:

- 🤖 **Phần cứng (Arduino):** Điều khiển cơ cấu xuất hàng, đọc cảm biến và giao tiếp với server qua kết nối mạng.
- 🖥️ **Backend (Flask + PostgreSQL):** Quản lý sản phẩm, slot hàng, giao dịch, người dùng và bảo mật thiết bị IoT.
- 🌐 **Frontend (Web):** Giao diện người dùng để chọn sản phẩm, thanh toán; giao diện admin để giám sát và quản lý hệ thống.
- 🔒 **Bảo mật:** Xác thực thiết bị bằng API key, phân quyền người dùng (admin/user), ghi log hoạt động.

---

Xem poster của dự án tại đây:

👉 [**Xem Poster (PDF)**](./poster.pdf)

> Nếu trình duyệt hỗ trợ, bạn có thể nhúng poster trực tiếp:

<object data="./poster.pdf" type="application/pdf" width="100%" height="800px">
  <p>Trình duyệt của bạn không hỗ trợ hiển thị PDF. Vui lòng <a href="./poster.pdf">tải về tại đây</a>.</p>
</object>

---

## ✨ Tính Năng Chính

### Phía Người Dùng
- Xem danh sách sản phẩm theo slot máy bán hàng
- Chọn sản phẩm và thực hiện thanh toán
- Xem lịch sử giao dịch cá nhân
- Đăng ký / đăng nhập tài khoản, cập nhật hồ sơ

### Phía Admin
- Quản lý sản phẩm: thêm, sửa, xóa, phân slot
- Giám sát giao dịch và doanh thu theo thời gian thực
- Quản lý thiết bị IoT: đăng ký, theo dõi trạng thái, thu hồi
- Xem log bảo mật và cảnh báo bất thường

### Phần Cứng (Arduino)
- Nhận lệnh xuất hàng từ server qua HTTP/WebSocket
- Điều khiển động cơ bước để đẩy sản phẩm ra
- Báo cáo trạng thái máy (nhiệt độ, tồn kho) về server

---

## 🛠️ Công Nghệ Sử Dụng

| Thành phần | Công nghệ |
|------------|-----------|
| **Phần cứng** | Arduino, ESP8266/ESP32 |
| **Backend** | Python, Flask, SQLAlchemy |
| **Database** | PostgreSQL |
| **Frontend** | HTML, CSS, JavaScript |
| **Server** | Nginx (reverse proxy) |
| **Bảo mật** | JWT, API Key, bcrypt |

---

## 📁 Cấu Trúc Dự Án

```
vending-machine-project/
├── backend/               # Flask API server
│   ├── app/
│   │   ├── models/        # Database models
│   │   ├── routes/        # API endpoints
│   │   └── static/        # Static files
│   └── run.py
├── frontend/              # Giao diện web người dùng
│   ├── index.html
│   ├── css/
│   └── js/
├── arduino/               # Code phần cứng Arduino
├── nginx.conf             # Cấu hình Nginx
├── poster.pdf             # Poster dự án
└── README.md
```

---

## � Hướng Dẫn Cài Đặt

### Yêu cầu
- Python 3.9+
- PostgreSQL
- Node.js (tuỳ chọn, cho dev frontend)

### Backend
```bash
cd backend
pip install -r requirements.txt
cp .env.example .env      # Cấu hình biến môi trường
python run.py
```

### Frontend
Mở file `frontend/index.html` trực tiếp trên trình duyệt hoặc dùng Live Server.

### Arduino
Nạp code trong thư mục `arduino/` lên board bằng Arduino IDE, cập nhật địa chỉ IP server trong file config.

---


## 👥 Thành Viên Nhóm

| STT | Họ và Tên | Mã Sinh Viên | Phần Trăm Thực Hiện | Chi Tiết |
|:---:|-----------|:------------:|:-------------------:|----------|
| 1 | Bùi Quang Trường| 1771020700 | 0% | hoàn thành sau |
| 2 | Nguyễn Phúc Bằng | .... | 0% | hoàn thành sau |
| 3 | Ngô Tất Thắng | .... | 0% | hoàn thành sau |

