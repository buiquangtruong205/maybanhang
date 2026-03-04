# 🐳 Hướng Dẫn Triển Khai Docker

Hướng dẫn chi tiết cách đóng gói và chạy Vending Machine System bằng Docker.

## 📋 Yêu Cầu Hệ Thống

- **Docker Desktop** phiên bản 20.10 trở lên
- **Docker Compose** phiên bản 2.0 trở lên
- **RAM**: Tối thiểu 4GB
- **Disk**: Tối thiểu 2GB trống

### Cài đặt Docker Desktop (Windows)

1. Tải Docker Desktop từ: https://www.docker.com/products/docker-desktop
2. Chạy file cài đặt và làm theo hướng dẫn
3. Khởi động lại máy tính
4. Mở Docker Desktop và đợi cho đến khi hiển thị "Docker is running"

---

## 🚀 Khởi Động Nhanh

### Bước 1: Mở Terminal/PowerShell

```powershell
cd e:\Arduino\vending-machine-project
```

### Bước 2: Build và khởi động tất cả services

```powershell
docker-compose up -d --build
```

### Bước 3: Kiểm tra trạng thái

```powershell
docker-compose ps
```

**Kết quả mong đợi:**
```
NAME                IMAGE                  STATUS
vending-db          postgres:15-alpine     Up (healthy)
vending-backend     vending-machine...     Up
vending-frontend    nginx:alpine           Up
```

---

## 🌐 Truy Cập Ứng Dụng

| Service | URL | Mô tả |
|---------|-----|-------|
| 🖥️ **Frontend** | http://localhost | Giao diện khách hàng |
| 🔧 **Backend API** | http://localhost:5000/api | REST API |
| 🔌 **WebSocket** | ws://localhost:5000/socket.io | Real-time updates |
| 🗄️ **PostgreSQL** | localhost:5433 | Database (user: postgres, pass: 123456) |

---

## 📝 Các Lệnh Thường Dùng

### Xem logs của tất cả services
```powershell
docker-compose logs -f
```

### Xem logs của một service cụ thể
```powershell
# Backend logs
docker-compose logs -f backend

# Database logs
docker-compose logs -f db

# Frontend logs
docker-compose logs -f frontend
```

### Dừng tất cả services
```powershell
docker-compose down
```

### Dừng và xóa toàn bộ dữ liệu (bao gồm database)
```powershell
docker-compose down -v
```

### Khởi động lại một service
```powershell
docker-compose restart backend
```

### Rebuild một service sau khi thay đổi code
```powershell
docker-compose up -d --build backend
```

---

## ⚙️ Cấu Hình Environment Variables

### Sử dụng file .env

Tạo hoặc chỉnh sửa file `.env` trong thư mục gốc:

```env
# PayOS Configuration
PAYOS_CLIENT_ID=your_client_id
PAYOS_API_KEY=your_api_key
PAYOS_CHECKSUM_KEY=your_checksum_key

# Database (tùy chọn - mặc định đã cấu hình trong docker-compose)
DATABASE_URL=postgresql://postgres:123456@db:5432/vending
```

---

## 🗄️ Quản Lý Database

### Truy cập PostgreSQL CLI
```powershell
docker-compose exec db psql -U postgres -d vending
```

### Backup database
```powershell
docker-compose exec db pg_dump -U postgres vending > backup.sql
```

### Restore database
```powershell
docker-compose exec -T db psql -U postgres vending < backup.sql
```

### Xem các bảng trong database
```powershell
docker-compose exec db psql -U postgres -d vending -c "\dt"
```

---

## 🔧 Troubleshooting

### ❌ Lỗi: Port đã được sử dụng

**Triệu chứng:** `Error: bind: address already in use`

**Giải pháp:**
1. Kiểm tra process đang sử dụng port:
   ```powershell
   netstat -ano | findstr :5000
   ```
2. Dừng process hoặc thay đổi port trong `docker-compose.yml`

---

### ❌ Lỗi: Database connection failed

**Triệu chứng:** Backend không thể kết nối database

**Giải pháp:**
1. Kiểm tra trạng thái database:
   ```powershell
   docker-compose ps db
   ```
2. Xem logs database:
   ```powershell
   docker-compose logs db
   ```
3. Đợi database khởi động hoàn tất (khoảng 10-20 giây)

---

### ❌ Lỗi: Image build failed

**Triệu chứng:** Lỗi khi build Docker image

**Giải pháp:**
1. Xóa cache và build lại:
   ```powershell
   docker-compose build --no-cache
   ```
2. Xóa tất cả containers và images cũ:
   ```powershell
   docker system prune -a
   ```

---

## 🏭 Triển Khai Production

### 1. Tạo file docker-compose.prod.yml

```yaml
version: '3.8'
services:
  backend:
    environment:
      - FLASK_ENV=production
    volumes: []  # Không mount volume trong production
    
  frontend:
    # Thêm SSL nếu cần
```

### 2. Chạy với file production

```powershell
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d
```

---

## 📊 Monitoring

### Xem resource usage
```powershell
docker stats
```

### Xem chi tiết container
```powershell
docker inspect vending-backend
```

---

## 🏗️ Cấu Trúc Docker

```
vending-machine-project/
├── docker-compose.yml      # Orchestration file
├── nginx.conf              # Nginx reverse proxy config
├── .env                    # Environment variables
├── backend/
│   ├── Dockerfile          # Backend Docker image
│   ├── .dockerignore       # Files to exclude
│   └── ...
└── frontend/
    └── ...                 # Static files served by Nginx
```

---

## 📞 Hỗ Trợ

Nếu gặp vấn đề, hãy:
1. Kiểm tra logs: `docker-compose logs -f`
2. Kiểm tra trạng thái: `docker-compose ps`
3. Thử restart: `docker-compose restart`
