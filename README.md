# Vending Machine Project

Dự án **máy bán hàng tự động tích hợp IoT** cho phép quản lý và vận hành máy bán hàng thông minh từ xa. Hệ thống hiện gồm:

- 🤖 **Phần cứng:** Firmware ESP32, điều khiển cơ cấu xuất hàng, đọc cảm biến và giao tiếp với server qua mạng.
- 🖥️ **Backend (Flask + PostgreSQL):** Quản lý sản phẩm, slot hàng, giao dịch, người dùng và bảo mật thiết bị IoT.
- 🌐 **Giao diện Web:** Giao diện quản trị trong `backend/app/static` và giao diện máy bán hàng trong `CLIENT_machine/`.
- 🔒 **Bảo mật:** Xác thực thiết bị bằng API key, phân quyền người dùng (admin/user), ghi log hoạt động.

---

Xem poster của dự án tại đây:

👉 [**Xem Poster (PDF)**](./docs/poster.pdf)

> Nếu trình duyệt hỗ trợ, bạn có thể nhúng poster trực tiếp:

<object data="./docs/poster.pdf" type="application/pdf" width="100%" height="800px">
  <p>Trình duyệt của bạn không hỗ trợ hiển thị PDF. Vui lòng <a href="./docs/poster.pdf">tải về tại đây</a>.</p>
</object>

---

## 📚 Tài Liệu

- [Tài Liệu API](./docs/tai_lieu_api.md)
- [Cấu Trúc Cơ Sở Dữ Liệu](./docs/cau_truc_co_so_du_lieu.md)
- [Hướng Dẫn Docker](./docs/huong_dan_docker.md)
- [Ghi Chú Bảo Mật](./docs/ghi_chu_bao_mat.md)
- [Công Việc Cần Làm](./docs/cong_viec_can_lam.md)

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

### Phần Cứng
- Nhận lệnh xuất hàng từ server qua HTTP/WebSocket
- Điều khiển cơ cấu nhả hàng từ ESP32
- Báo cáo trạng thái máy (nhiệt độ, tồn kho) về server

---

## 🛠️ Công Nghệ Sử Dụng

| Thành phần | Công nghệ |
|------------|-----------|
| **Phần cứng** | ESP32-WROOM, TFT 2.8", cảm biến, cơ cấu nhả hàng |
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
├── CLIENT_machine/        # Giao diện máy bán hàng
├── firmware/              # Firmware ESP32 / PlatformIO
├── docs/                  # Tài liệu chi tiết
├── nginx.conf             # Cấu hình Nginx
└── README.md
```

---

## Hướng Dẫn Cài Đặt

### Hướng Dẫn Chạy Nhanh (Docker)
1. Copy file môi trường: `cp .env.example .env` (và điền KEY)
2. Chạy hệ thống: `docker compose up -d --build`
3. Nạp data mẫu: `cmd /c "docker compose exec -T db psql -U postgres -d vending_machine < seed.sql"`
4. Truy cập: `http://localhost`

Chi tiết xem tại: [**Hướng Dẫn Docker**](./docs/huong_dan_docker.md)

### Yêu cầu
- Docker / Docker Compose (khuyến nghị)
- Trình duyệt Chrome/Edge

### Yêu cầu
- Python 3.9+
- PostgreSQL
- Docker / Docker Compose (khuyến nghị)

### Backend
```bash
cd backend
pip install -r ../requirements.txt
# tạo hoặc chỉnh sửa file .env ở thư mục gốc
python run.py
```

### Client Machine
Mở `CLIENT_machine/index.html` trực tiếp trên trình duyệt hoặc phục vụ qua web server cục bộ.

### Firmware
Dùng PlatformIO để nạp code trong thư mục `firmware/` lên ESP32, sau đó cập nhật thông tin Wi-Fi và server trong file cấu hình.

---


## 👥 Thành Viên Nhóm

| STT | Họ và Tên | Mã Sinh Viên | Phần Trăm Thực Hiện | Chi Tiết |
|:---:|-----------|:------------:|:-------------------:|----------|
| 1 | Bùi Quang Trường| 1771020700 | 0% | hoàn thành sau |
| 2 | Nguyễn Phúc Bằng | .... | 0% | hoàn thành sau |
| 3 | Ngô Tất Thắng | .... | 0% | hoàn thành sau |

