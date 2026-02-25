# 🗺️ Bản Kế Hoạch Hoàn Thiện Backend - Vending Machine V2

> Tài liệu này mô tả chi tiết các bước cần thực hiện để hoàn thiện backend,  
> sắp xếp theo **thứ tự ưu tiên** và **mức độ phụ thuộc** giữa các module.
>
> ⏱️ **Cập nhật lần cuối:** 25/02/2026

---

## 📊 Trạng Thái Hiện Tại

### ✅ Đã hoàn thiện (Sẵn sàng sử dụng)

| Module | File chính | Chức năng |
| :--- | :--- | :--- |
| **FastAPI App** | `app/main.py` | Khởi tạo server, CORS, Socket.IO |
| **Config** | `app/core/config.py` | Đọc `.env`, cấu hình PayOS/DB/JWT |
| **Database** | `app/db/database.py` | SQLAlchemy Async + PostgreSQL |
| **Auth/Security** | `app/core/security.py` | JWT token, bcrypt password, OAuth2 |
| **Socket.IO** | `app/core/socket_manager.py` | Real-time broadcast (order, issue) |
| **Models** (8 bảng) | `app/models/` | User, Machine, Product, Slot, Order, Issue, RefillLog, Setting |
| **Schemas** (8 file) | `app/schemas/` | Pydantic validation cho Product, Machine, Slot, User, Issue, Setting, **Order**, **Payment** |
| **Services** (11 file) | `app/services/` | CRUD + business logic đầy đủ |
| **API Endpoints** (12 nhóm) | `app/api/v1/endpoints/` | Auth, Users, Products, Machines, Orders, Payments, Slots, Stats, IoT, Issues, Settings, Logs |
| **PayOS** | `app/services/payos_service.py` | Tạo link thanh toán, kiểm tra trạng thái |
| **IoT API** | `app/api/v1/endpoints/iot.py` | Kiểm tra đơn hàng + xác nhận nhả hàng cho ESP32 (Dynamic Machine ID) |

### ✅ Đã sửa chữa (Giai đoạn 1 — Hoàn thành 25/02/2026)

| Hạng mục | Vấn đề cũ | Trạng thái |
| :--- | :--- | :--- |
| ~~**README.md**~~ | Lỗi thời, mô tả Version 1 | ✅ Đã viết lại hoàn toàn cho V2 |
| ~~**`.env.example`**~~ | `DATABASE_URL` dùng sqlite | ✅ Đã sửa sang `postgresql+asyncpg` |
| ~~**Schemas thiếu**~~ | `order.py`, `payment.py` trống | ✅ Đã tạo 5 schemas Order + 4 schemas Payment |
| ~~**IoT Endpoint cứng**~~ | `machine_id=1` hardcode | ✅ Đã sửa sang dynamic `get_by_secret_key()` |

### ⚠️ Còn cần bổ sung (Giai đoạn 2–6)

| Hạng mục | Vấn đề | Mức độ |
| :--- | :--- | :--- |
| **MQTT Integration** | Chưa có MQTT client kết nối ESP32 | 🔴 Cao (cho tích hợp phần cứng) |
| **Tests** | Chỉ có 2 file test có code, unit tests trống | 🟡 Trung bình |
| **Alembic Migrations** | Thư mục `versions/` trống, chưa có migration file | 🟡 Trung bình |
| **Bảo mật** | Chưa có rate limiting, request logging, webhook verification | 🟡 Trung bình |

---

## 📋 Kế Hoạch Chi Tiết Theo Giai Đoạn

---

### ✅ Giai Đoạn 1: Sửa lỗi & Chuẩn hóa — HOÀN THÀNH ✅

> **Hoàn thành ngày:** 25/02/2026

- [x] 1.1 Cập nhật `.env.example` — `DATABASE_URL` đã sửa sang `postgresql+asyncpg`
- [x] 1.2 Tạo lại Schemas — `schemas/order.py` (5 schemas) + `schemas/payment.py` (4 schemas)
- [x] 1.3 Cập nhật `README.md` — Viết lại hoàn toàn cho V2 (12 nhóm API, workflow, cấu trúc)
- [x] 1.4 Sửa IoT Endpoint — Thêm `get_by_secret_key()` vào `machine_service.py`, viết lại `iot.py` với dependency injection động

---

### 🔌 Giai Đoạn 2: Tích hợp MQTT (Cho ESP32)

> **Mục tiêu:** Backend có thể giao tiếp 2 chiều với ESP32 qua MQTT.

#### 2.1 Thêm MQTT Client vào Backend
- **Thư viện:** `asyncio-mqtt` hoặc `aiomqtt`
- **File mới:** `app/core/mqtt_client.py`
- **Chức năng:**
  - Subscribe topic: `vending/{machine_id}/status` (nhận trạng thái máy)
  - Subscribe topic: `vending/{machine_id}/dispense/result` (nhận kết quả nhả hàng)
  - Publish topic: `vending/{machine_id}/dispense/command` (ra lệnh nhả hàng)
  - Publish topic: `vending/{machine_id}/display/update` (cập nhật hiển thị)

#### 2.2 Cấu hình MQTT trong `.env`
```env
MQTT_BROKER=localhost
MQTT_PORT=1883
MQTT_USERNAME=
MQTT_PASSWORD=
MQTT_TOPIC_PREFIX=vending
```

#### 2.3 Cập nhật `config.py`
```python
MQTT_BROKER: str = "localhost"
MQTT_PORT: int = 1883
MQTT_USERNAME: str = ""
MQTT_PASSWORD: str = ""
MQTT_TOPIC_PREFIX: str = "vending"
```

#### 2.4 Tích hợp MQTT vào luồng thanh toán
```
Luồng hiện tại:  User → Web → API → PayOS → Webhook → DB
Luồng mới:       User → Web → API → PayOS → Webhook → DB → MQTT → ESP32 → Nhả hàng
                                                                    ESP32 → MQTT → API → DB (cập nhật COMPLETED)
```

#### 2.5 Cập nhật IoT Service
- **File:** `app/services/iot_service.py`
- **Thêm:** Hàm `send_dispense_command()` — Publish MQTT command tới ESP32
- **Thêm:** Handler khi nhận MQTT message từ ESP32 (kết quả nhả hàng)

---

### 🛡️ Giai Đoạn 3: Bảo mật & Middleware

> **Mục tiêu:** Tăng cường bảo mật và logging cho production.

#### 3.1 Rate Limiting
- **Thư viện:** `slowapi`
- **Áp dụng cho:** API tạo thanh toán (chống spam), Auth login (chống brute-force)
- **File mới:** `app/middleware/rate_limit.py`

#### 3.2 Request Logging Middleware
- **Chức năng:** Log tất cả request/response (method, path, status, duration)
- **File mới:** `app/middleware/logging.py`
- **Format:** `[2026-02-25 15:00:00] POST /api/v1/payments/create → 200 (150ms)`

#### 3.3 Error Handling Tập trung
- **File mới:** `app/core/exceptions.py`
- **Chức năng:** Custom exception classes + FastAPI exception handlers
- **Ví dụ:** `OrderNotFoundException`, `PaymentFailedException`, `MachineOfflineException`

#### 3.4 Webhook Verification
- **Vấn đề:** PayOS webhook cần verify checksum để đảm bảo request thật
- **File:** `app/api/v1/endpoints/payments.py`
- **Thêm:** Verify PayOS webhook signature trước khi xử lý

---

### 🧪 Giai Đoạn 4: Testing

> **Mục tiêu:** Đảm bảo API hoạt động đúng và ổn định.

#### 4.1 Setup Test Infrastructure
- **File:** `tests/conftest.py`
- **Chức năng:** Tạo test database (SQLite in-memory), test client, fixtures
- **Thư viện:** `pytest`, `pytest-asyncio`, `httpx`

#### 4.2 Unit Tests
- `tests/unit/test_orders.py` — Test OrderService CRUD
- `tests/unit/test_payments.py` — Test PayOS service (mock)
- `tests/unit/test_products.py` — Test ProductService CRUD

#### 4.3 Integration Tests 
- `tests/integration/test_api.py` — Test toàn bộ API flow (đã có khung)
- **Thêm:** Test luồng thanh toán end-to-end (mock PayOS)
- **Thêm:** Test luồng IoT (ESP32 check order → dispense)

---

### 📊 Giai Đoạn 5: Alembic Migrations

> **Mục tiêu:** Quản lý schema DB thay vì dùng script thủ công.

#### 5.1 Tạo Migration Đầu tiên
```bash
alembic revision --autogenerate -m "initial_schema"
alembic upgrade head
```

#### 5.2 Xóa các script tạo bảng thủ công (sau khi migration hoạt động)
- `scripts/create_users_table.py` → Không cần nữa (Alembic quản lý)
- `scripts/create_issues_table.py` → Không cần nữa
- `scripts/create_missing_tables.py` → Không cần nữa
- `scripts/add_user_cols.py` → Không cần nữa

---

### 📈 Giai Đoạn 6: Tối ưu & Mở rộng (Tùy chọn)

> **Mục tiêu:** Nâng cấp hiệu năng và tính năng sau khi core ổn định.

#### 6.1 Caching (Redis)
- Cache danh sách sản phẩm, thống kê dashboard
- Giảm tải database cho các query lặp lại

#### 6.2 Background Tasks
- Tự động hủy đơn hàng PENDING sau 10 phút
- Tự động check trạng thái PayOS cho đơn pending
- **Thư viện:** FastAPI `BackgroundTasks` hoặc `Celery`

#### 6.3 Xuất báo cáo (Excel)
- Đã có `xlsxwriter` trong dependencies
- Thêm endpoint: `GET /api/v1/stats/export` → Tải file Excel

#### 6.4 WebSocket cho IoT Dashboard
- Real-time hiển thị trạng thái máy trên Admin Dashboard
- Khi ESP32 gửi heartbeat → MQTT → Backend → Socket.IO → Admin Web

---

## 🎯 Lộ Trình Thực Hiện

```
Giai đoạn 1 (Sửa lỗi)     ██████████  HOÀN THÀNH ✅ (25/02/2026)
Giai đoạn 2 (MQTT)         ████████░░  ~4-6 giờ   ← TIẾP THEO: Khi tích hợp ESP32
Giai đoạn 3 (Bảo mật)      ██████░░░░  ~3-4 giờ   ← Trước khi deploy
Giai đoạn 4 (Testing)      ██████░░░░  ~3-4 giờ   ← Song song với GĐ 2-3
Giai đoạn 5 (Migrations)   ████░░░░░░  ~1-2 giờ   ← Khi DB schema ổn định
Giai đoạn 6 (Mở rộng)      ████░░░░░░  ~4-8 giờ   ← Tùy chọn, sau khi core ổn
```

---

## 📁 Cấu Trúc Dự Kiến Sau Hoàn Thiện

```
backend/
├── .env / .env.example
├── .gitignore
├── requirements.txt
├── alembic.ini
├── README.md                        ← Cập nhật V2
├── app/
│   ├── main.py                      ← FastAPI + Socket.IO
│   ├── core/
│   │   ├── config.py                ← + MQTT config
│   │   ├── security.py
│   │   ├── socket_manager.py
│   │   ├── mqtt_client.py           ← MỚI: MQTT integration
│   │   └── exceptions.py            ← MỚI: Custom exceptions
│   ├── db/
│   │   └── database.py
│   ├── middleware/
│   │   ├── rate_limit.py            ← MỚI: Rate limiting
│   │   └── logging.py              ← MỚI: Request logging
│   ├── models/        (8 file)
│   ├── schemas/       (8 file)      ← order.py, payment.py ĐÃ TẠO
│   ├── services/     (11 file)
│   ├── api/v1/endpoints/ (12 file)
│   └── utils/
├── scripts/           (15 file)
├── tests/
│   ├── conftest.py                  ← MỚI: Test setup
│   ├── unit/          (3 file)      ← MỚI: Unit tests
│   └── integration/   (2 file)
└── migrations/
    └── versions/      (N file)      ← MỚI: Alembic migrations
```
