# 🏭 Vending Machine API — Version 2

API backend cho máy bán hàng tự động với tích hợp **PayOS**, **Socket.IO** real-time, và giao tiếp **ESP32**.

## 🛠️ Công nghệ

| Thành phần | Công nghệ |
| :--- | :--- |
| **Framework** | FastAPI (Python 3.10+) |
| **Database** | PostgreSQL + SQLAlchemy Async |
| **Auth** | JWT (python-jose) + bcrypt |
| **Thanh toán** | PayOS SDK |
| **Real-time** | Socket.IO (python-socketio) |
| **Migration** | Alembic |
| **Server** | Uvicorn (ASGI) |

---

## 🚀 Cài đặt và Chạy

### 1. Tạo môi trường ảo
```bash
cd Version_2/backend
python -m venv .venv
.venv\Scripts\activate   # Windows
```

### 2. Cài dependencies
```bash
pip install -r requirements.txt
```

### 3. Cấu hình `.env`
```bash
cp .env.example .env
# Sửa các giá trị trong .env theo hệ thống của bạn
```

### 4. Khởi tạo Database
```bash
python scripts/init_db.py       # Tạo bảng
python scripts/seed_data.py     # Thêm dữ liệu mẫu
python scripts/reset_admin.py   # Tạo tài khoản admin
```

### 5. Chạy server
```bash
uvicorn app.main:app --host 0.0.0.0 --port 5001 --reload
```

Server sẽ chạy tại: `http://127.0.0.1:5001`  
Swagger UI: `http://127.0.0.1:5001/docs`

---

## 📋 API Endpoints

### 🔐 Auth (`/api/v1/auth`)
| Method | Path | Mô tả |
| :--- | :--- | :--- |
| `POST` | `/login` | Đăng nhập, nhận JWT token |

### 👤 Users (`/api/v1/users`)
| Method | Path | Mô tả |
| :--- | :--- | :--- |
| `GET` | `/` | Danh sách người dùng |
| `POST` | `/` | Tạo user mới |
| `PUT` | `/{id}` | Cập nhật user |
| `DELETE` | `/{id}` | Xóa user |

### 📦 Products (`/api/v1/products`)
| Method | Path | Mô tả |
| :--- | :--- | :--- |
| `GET` | `/` | Danh sách sản phẩm |
| `POST` | `/` | Tạo sản phẩm mới |
| `PUT` | `/{id}` | Cập nhật sản phẩm |
| `DELETE` | `/{id}` | Xóa sản phẩm |

### 🏭 Machines (`/api/v1/machines`)
| Method | Path | Mô tả |
| :--- | :--- | :--- |
| `GET` | `/` | Danh sách máy bán hàng |
| `POST` | `/` | Tạo máy mới |
| `PUT` | `/{id}` | Cập nhật thông tin máy |
| `DELETE` | `/{id}` | Xóa máy |

### 🎰 Slots (`/api/v1/slots`)
| Method | Path | Mô tả |
| :--- | :--- | :--- |
| `GET` | `/` | Danh sách vị trí hàng |
| `POST` | `/` | Tạo slot mới |
| `PUT` | `/{id}` | Cập nhật slot |
| `POST` | `/{id}/refill` | Nạp hàng vào slot |
| `DELETE` | `/{id}` | Xóa slot |

### 📄 Orders (`/api/v1/orders`)
| Method | Path | Mô tả |
| :--- | :--- | :--- |
| `GET` | `/` | Danh sách đơn hàng |
| `POST` | `/{order_code}/confirm` | Xác nhận đơn thủ công |
| `POST` | `/{order_code}/cancel` | Hủy đơn hàng |

### 💳 Payments (`/api/v1/`)
| Method | Path | Mô tả |
| :--- | :--- | :--- |
| `POST` | `/create-payment` | Tạo link thanh toán PayOS |
| `GET` | `/order-status/{code}` | Kiểm tra trạng thái đơn |
| `POST` | `/payos-webhook` | Webhook callback từ PayOS |

### 📊 Stats (`/api/v1/stats`)
| Method | Path | Mô tả |
| :--- | :--- | :--- |
| `GET` | `/dashboard` | Dữ liệu tổng quan dashboard |

### 🤖 IoT (`/api/v1/iot`)
| Method | Path | Mô tả |
| :--- | :--- | :--- |
| `GET` | `/check-order/{code}` | ESP32 kiểm tra đơn đã thanh toán |
| `POST` | `/dispense-complete` | ESP32 xác nhận nhả hàng xong |

### ⚠️ Issues (`/api/v1/issues`)
| Method | Path | Mô tả |
| :--- | :--- | :--- |
| `GET` | `/` | Danh sách sự cố |
| `POST` | `/` | Báo cáo sự cố mới |
| `PUT` | `/{id}/resolve` | Đánh dấu đã xử lý |

### ⚙️ Settings (`/api/v1/settings`)
| Method | Path | Mô tả |
| :--- | :--- | :--- |
| `GET` | `/` | Lấy cấu hình hệ thống |
| `PUT` | `/{key}` | Cập nhật cấu hình |

### 📋 Logs (`/api/v1/logs`)
| Method | Path | Mô tả |
| :--- | :--- | :--- |
| `GET` | `/refill` | Nhật ký nạp hàng |

---

## 🔄 Workflow Thanh Toán

```
1. User chọn sản phẩm trên Web (hoặc ESP32 LCD)
2. Frontend gọi POST /create-payment
3. Backend tạo đơn hàng (PENDING) + gọi PayOS
4. PayOS trả về QR code + checkout URL
5. User quét QR → thanh toán qua ngân hàng
6. PayOS gửi webhook → Backend cập nhật đơn (PAID)
7. Socket.IO broadcast → Frontend hiển thị thành công
8. ESP32 polling /iot/check-order → nhận should_dispense=True
9. ESP32 nhả hàng → gọi /iot/dispense-complete
10. Backend cập nhật đơn (COMPLETED)
```

---

## 📁 Cấu trúc Thư mục

```
backend/
├── .env / .env.example         # Cấu hình môi trường
├── .gitignore
├── requirements.txt            # Python dependencies
├── alembic.ini                 # Cấu hình migration
├── BACKEND_ROADMAP.md          # Kế hoạch phát triển
├── README.md                   # Tài liệu này
├── app/
│   ├── main.py                 # FastAPI + Socket.IO entry point
│   ├── core/
│   │   ├── config.py           # Đọc .env, settings
│   │   ├── security.py         # JWT, bcrypt, OAuth2
│   │   └── socket_manager.py   # Socket.IO server
│   ├── db/
│   │   └── database.py         # SQLAlchemy Async engine
│   ├── models/                 # SQLAlchemy ORM models
│   │   ├── user.py, product.py, machine.py, slot.py
│   │   ├── order.py, issue.py, log.py, setting.py
│   │   └── __init__.py         # Export tất cả models
│   ├── schemas/                # Pydantic validation
│   │   ├── product.py, machine.py, slot.py, user.py
│   │   ├── order.py, payment.py, issue.py, setting.py
│   │   └── __init__.py
│   ├── services/               # Business logic
│   │   ├── product_service.py, order_service.py
│   │   ├── payos_service.py, machine_service.py
│   │   ├── slot_service.py, user_service.py
│   │   ├── iot_service.py, stats_service.py
│   │   ├── issue_service.py, log_service.py
│   │   └── setting_service.py
│   ├── api/v1/
│   │   ├── router.py           # Đăng ký tất cả endpoints
│   │   └── endpoints/          # 12 nhóm API routes
│   └── utils/
│       └── helpers.py          # Hàm tiện ích
├── scripts/                    # Scripts quản trị
│   ├── init_db.py              # Khởi tạo database
│   ├── seed_data.py            # Dữ liệu mẫu
│   ├── reset_admin.py          # Reset tài khoản admin
│   └── run_dev.py              # Chạy dev server
├── tests/                      # Test suite
│   ├── integration/
│   └── unit/
└── migrations/                 # Alembic migrations
```

---

## 🔧 Biến Môi Trường (.env)

| Biến | Mô tả | Ví dụ |
| :--- | :--- | :--- |
| `PAYOS_CLIENT_ID` | PayOS Client ID | `abc123` |
| `PAYOS_API_KEY` | PayOS API Key | `xyz789` |
| `PAYOS_CHECKSUM_KEY` | PayOS Checksum Key | `key123` |
| `PORT` | Port server | `5001` |
| `DOMAIN` | Domain cho callback URL | `http://localhost:5001` |
| `DATABASE_URL` | PostgreSQL connection string | `postgresql+asyncpg://...` |
| `SECRET_KEY` | JWT secret key | `your_secret` |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | Thời hạn JWT (phút) | `60` |
| `MACHINE_KEYS` | Danh sách machine keys | `may1,may2` |