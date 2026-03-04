# API Documentation — Vending Machine System

> **Base URL:** `http://localhost:5000/api`  
> **Cập nhật lần cuối:** 2026-03-04

---

## Mục lục

1. [Xác thực (Auth)](#1-xác-thực-auth)
2. [Sản phẩm (Products)](#2-sản-phẩm-products)
3. [Slot (Ngăn máy)](#3-slot-ngăn-máy)
4. [Máy bán hàng (Machines)](#4-máy-bán-hàng-machines)
5. [Đơn hàng (Orders)](#5-đơn-hàng-orders)
6. [Thanh toán QR — PayOS (Payment)](#6-thanh-toán-qr--payos-payment)
7. [IoT — Máy bán hàng (Arduino/ESP)](#7-iot--máy-bán-hàng-arduinoesp)
8. [Thống kê (Stats)](#8-thống-kê-stats)
9. [Upload file](#9-upload-file)
10. [WebSocket](#10-websocket)
11. [Thiết bị — Tình trạng & Phiên làm việc (Devices)](#11-thiết-bị--tình-trạng--phiên-làm-việc-devices)
12. [Bảo mật & Nhật ký (Security Logs)](#12-bảo-mật--nhật-ký-security-logs)
13. [Giao dịch (Transactions)](#13-giao-dịch-transactions)

---

## Quy ước chung

| Ký hiệu | Ý nghĩa |
|---|---|
| 🔒 | Yêu cầu JWT token: `Authorization: Bearer <token>` |
| 🔑 | Yêu cầu Machine Key: `X-Machine-Key: <key>` |
| ✅ | Public — không cần xác thực |

**Response chung:**
```json
{
  "success": true | false,
  "message": "...",
  "data": { ... }
}
```

---

## 1. Xác thực (Auth)

### `POST /register` ✅
Đăng ký tài khoản admin *(chỉ cho phép 1 tài khoản duy nhất trong hệ thống)*.

**Request body:**
```json
{
  "username": "admin",
  "password": "secret123"
}
```

**Response `201`:**
```json
{
  "success": true,
  "data": { "user_id": 1, "username": "admin" }
}
```

**Lỗi `403`:** Nếu đã có tài khoản rồi.

---

### `POST /login` ✅
Đăng nhập, nhận JWT token.

**Request body:**
```json
{
  "username": "admin",
  "password": "secret123"
}
```

**Response `200`:**
```json
{
  "success": true,
  "data": {
    "access_token": "eyJ...",
    "token_type": "bearer"
  }
}
```

---

### `GET /users/me` 🔒
Lấy thông tin tài khoản hiện tại.

**Response `200`:**
```json
{
  "success": true,
  "data": { "user_id": 1, "username": "admin" }
}
```

---

## 2. Sản phẩm (Products)

### `GET /products` ✅
Lấy danh sách tất cả sản phẩm.

**Response `200`:**
```json
{
  "success": true,
  "data": [
    {
      "product_id": 1,
      "product_name": "Nước suối",
      "price": 10000,
      "image": "/static/uploads/abc.jpg",
      "active": true,
      "stock": 5
    }
  ]
}
```

---

### `GET /products/<product_id>` ✅
Lấy thông tin 1 sản phẩm.

---

### `POST /products` 🔒
Tạo sản phẩm mới.

**Request body:**
```json
{
  "product_name": "Nước suối",
  "price": 10000,
  "image": "/static/uploads/abc.jpg",
  "active": true
}
```

**Response `201`**

---

### `PUT /products/<product_id>` 🔒
Cập nhật sản phẩm (toàn bộ fields).

---

### `DELETE /products/<product_id>` 🔒
Xóa sản phẩm.

---

## 3. Slot (Ngăn máy)

### `GET /slots` ✅
Lấy danh sách slot. Có thể lọc theo máy.

**Query params:**
- `machine_id` *(optional)* — Lọc theo máy

**Ví dụ:** `GET /slots?machine_id=1`

---

### `GET /slots/<slot_id>` ✅
Lấy thông tin 1 slot.

---

### `POST /slots` 🔒
Tạo slot mới.

**Request body:**
```json
{
  "machine_id": 1,
  "slot_code": "A1",
  "product_id": 3,
  "stock": 10,
  "capacity": 15
}
```

---

### `PUT /slots/<slot_id>` 🔒
Cập nhật slot.

---

### `DELETE /slots/<slot_id>` 🔒
Xóa slot.

---

## 4. Máy bán hàng (Machines)

### `GET /machines` ✅
Lấy danh sách máy bán hàng.

**Response `200`:**
```json
{
  "success": true,
  "data": [
    { "machine_id": 1, "name": "Máy A", "location": "Tầng 1", "status": "active" }
  ]
}
```

---

### `GET /machines/<machine_id>` ✅
Lấy thông tin 1 máy.

---

### `POST /machines` 🔒
Tạo máy mới.

**Request body:**
```json
{
  "name": "Máy A",
  "location": "Tầng 1",
  "status": "active",
  "secret_key": "may1"
}
```

---

### `PUT /machines/<machine_id>` 🔒
Cập nhật thông tin máy.

---

### `DELETE /machines/<machine_id>` 🔒
Xóa máy.

---

## 5. Đơn hàng (Orders)

### `GET /orders` 🔒
Lấy danh sách đơn hàng (mới nhất lên đầu).

---

### `GET /orders/<order_id>` 🔒
Lấy chi tiết 1 đơn hàng.

---

### `GET /orders/<order_id>/status` ✅
Kiểm tra trạng thái thanh toán của đơn hàng *(dùng cho frontend polling)*.

**Response `200`:**
```json
{
  "success": true,
  "data": {
    "order_id": 123,
    "status_payment": "completed",
    "status_slots": "pending",
    "created_at": "2026-03-04T09:00:00"
  }
}
```

**Giá trị `status_payment`:** `pending` | `completed` | `cancelled`  
**Giá trị `status_slots`:** `pending` | `dispensed` | `failed` | `cancelled`

---

### `POST /orders` ✅
*(Legacy)* Tạo đơn hàng hoàn tất luôn (không qua thanh toán).

**Request body:**
```json
{
  "product_id": 1,
  "price_snapshot": 10000,
  "slot_id": 2
}
```

---

### `POST /orders/pending` ✅
Tạo đơn hàng trạng thái chờ thanh toán *(dùng cho luồng QR)*.

**Request body:**
```json
{
  "product_id": 1,
  "price_snapshot": 10000,
  "slot_id": 2
}
```

---

### `PUT /orders/<order_id>/complete` ✅
Đánh dấu đơn hàng hoàn tất (sau khi thanh toán).

---

### `PUT /orders/<order_id>/cancel` ✅
Hủy đơn hàng đang ở trạng thái `pending`.

---

## 6. Thanh toán QR — PayOS (Payment)

### `POST /payment/create` 🔑
Tạo link thanh toán QR PayOS.

**Request body:**
```json
{
  "order_code": 123,
  "amount": 50000,
  "description": "Thanh toán đơn hàng #123",
  "items": [
    { "name": "Nước suối", "quantity": 1, "price": 50000 }
  ],
  "buyer_name": "Nguyễn Văn A",
  "buyer_email": "a@gmail.com",
  "buyer_phone": "0901234567"
}
```

**Response `201`:**
```json
{
  "success": true,
  "data": {
    "checkout_url": "https://pay.payos.vn/...",
    "qr_code": "...",
    "order_code": 123,
    "payment_code": 1230001
  }
}
```

---

### `GET /payment/status/<order_code>` 🔑
Kiểm tra trạng thái thanh toán từ PayOS. Nếu đã thanh toán thì tự động sync về DB.

**Response `200`:**
```json
{
  "success": true,
  "data": {
    "status": "PAID",
    "amount": 50000,
    "amount_paid": 50000,
    "amount_remaining": 0
  }
}
```

---

### `POST /payment/webhook` ✅
Webhook nhận callback từ PayOS khi thanh toán thành công. *(Do PayOS gọi, không phải client)*.

---

### `POST /payment/sync/<order_code>` 🔑
Force sync trạng thái từ PayOS về DB *(dùng khi webhook bị lỡ)*.

---

### `POST /payment/cancel/<order_code>` 🔑
Hủy link thanh toán đang chờ.

---

### `GET /payment/success` ✅
Return URL sau khi thanh toán thành công *(PayOS redirect về)*.

### `GET /payment/cancel` ✅
Cancel URL khi khách hủy thanh toán *(PayOS redirect về)*.

---

## 7. IoT — Máy bán hàng (Arduino/ESP)

> **Tất cả endpoint IoT đều yêu cầu header:** `X-Machine-Key: <key>` 🔑

---

### Luồng hoạt động tổng quan

```
[Khởi động]
  POST /iot/register-device
  POST /iot/heartbeat (lặp mỗi 30s)

[Khách mua hàng — Thanh toán QR]
  POST /iot/create-order          → tạo order (pending)
  GET  /iot/check-payment/:id     → poll cho đến khi paid
  GET  /iot/pending-orders        → lấy order cần nhả
  POST /iot/dispense-complete     → báo đã nhả xong

[Khách mua hàng — Tiền mặt]
  POST /iot/create-order          → tạo order (pending)
  POST /iot/cash-insert           → lặp mỗi khi nhét tờ tiền
  GET  /iot/pending-orders        → khi đủ tiền → nhả hàng
  POST /iot/dispense-complete     → báo đã nhả xong

[Quản lý]
  POST /iot/stock-update          → cập nhật tồn kho
  POST /iot/logs                  → gửi log lên server
  POST /iot/ping                  → kiểm tra kết nối
```

---

### `POST /iot/ping` 🔑
Kiểm tra kết nối server còn hoạt động không.

**Response `200`:**
```json
{
  "success": true,
  "message": "Pong",
  "machine_id": 1,
  "server_time": "2026-03-04T09:00:00"
}
```

---

### `POST /iot/register-device` 🔑
Đăng ký thiết bị khi khởi động lần đầu.

**Request body:**
```json
{
  "mac_address": "AA:BB:CC:DD:EE:FF",
  "fingerprint": "abc123",
  "firmware_version": "1.0.0"
}
```

---

### `POST /iot/heartbeat` 🔑
Gửi heartbeat và cập nhật trạng thái phiên làm việc.

**Request body:**
```json
{
  "uptime": 3600,
  "free_memory": 50000,
  "wifi_rssi": -65
}
```

**Response `200`:**
```json
{
  "success": true,
  "data": {
    "machine_id": 1,
    "session_id": 5,
    "server_time": "2026-03-04T09:00:00"
  }
}
```

---

### `POST /iot/create-order` 🔑
Tạo đơn hàng khi khách chọn sản phẩm.

**Request body:**
```json
{
  "slot_code": "A1",
  "product_id": 3,
  "quantity": 1
}
```
> `slot_code` hoặc `product_id` cần ít nhất 1 cái.

**Response `201`:**
```json
{
  "success": true,
  "data": {
    "order_id": 123,
    "product_id": 3,
    "product_name": "Nước suối",
    "price": 10000,
    "slot_code": "A1",
    "status_payment": "pending",
    "status_slots": "pending"
  }
}
```

---

### `GET /iot/check-payment/<order_id>` 🔑
Kiểm tra trạng thái thanh toán của đơn hàng *(dùng khi thanh toán QR)*.

**Response `200`:**
```json
{
  "success": true,
  "data": {
    "order_id": 123,
    "status_payment": "completed",
    "status_slots": "pending",
    "paid": true,
    "price": 10000
  }
}
```

---

### `GET /iot/pending-orders` 🔑
Lấy danh sách đơn hàng đã thanh toán xong nhưng **chưa được nhả hàng** (cần xử lý).

> Đây là endpoint Arduino cần **poll liên tục** (ví dụ mỗi 2 giây) để biết khi nào cần nhả hàng.

**Response `200`:**
```json
{
  "success": true,
  "data": [
    {
      "order_id": 123,
      "slot_id": 2,
      "product_id": 3,
      "price": 10000,
      "created_at": "2026-03-04T09:00:00"
    }
  ]
}
```

> **Bộ lọc:** `status_payment = 'completed'` AND `status_slots = 'pending'`

---

### `POST /iot/dispense-complete` 🔑
**Báo kết quả nhả hàng** sau khi máy đã xử lý xong đơn hàng.

**Request body:**
```json
{
  "order_id": 123,
  "slot_code": "A1",
  "success": true,
  "message": "Dispensed successfully"
}
```

**Response `200`:**
```json
{
  "success": true,
  "message": "Dispense completed",
  "order_id": 123
}
```

> Cập nhật `status_slots` → `'dispensed'` (hoặc `'failed'` nếu `success: false`).

---

### `POST /iot/stock-update` 🔑
Cập nhật số lượng tồn kho của một slot.

**Request body:**
```json
{
  "slot_code": "A1",
  "stock": 8
}
```

---

### `POST /iot/logs` 🔑
Upload log từ thiết bị lên server.

**Request body:**
```json
{
  "level": "error",
  "message": "Sensor malfunction",
  "data": { "sensor": "bill_acceptor", "code": 500 }
}
```
> `level`: `info` | `warning` | `error` | `critical`

---

### `POST /iot/cash-insert` 🔑 *(Thanh toán tiền mặt)*
Arduino gửi mỗi khi cảm biến nhận diện được tờ tiền.

**Request body:**
```json
{
  "order_id": 123,
  "denomination": 50000
}
```

> **Mệnh giá hợp lệ (VNĐ):** `1000, 2000, 5000, 10000, 20000, 50000, 100000, 200000, 500000`

**Response — Chưa đủ tiền `200`:**
```json
{
  "success": true,
  "paid": false,
  "message": "Inserted 50,000đ. Still need 25,000đ more.",
  "data": {
    "order_id": 123,
    "total_inserted": 50000,
    "price": 75000,
    "remaining": 25000,
    "change": 0
  }
}
```

**Response — Đủ tiền (thanh toán thành công) `200`:**
```json
{
  "success": true,
  "paid": true,
  "message": "Payment completed! Change: 25,000đ",
  "data": {
    "order_id": 123,
    "total_inserted": 100000,
    "price": 75000,
    "remaining": 0,
    "change": 25000
  }
}
```

> Khi `paid: true`: order được cập nhật `status_payment = 'completed'`, `status_slots = 'pending'`, Transaction được tạo với `amount = price` (giá sản phẩm, không phải số tiền nhét vào), và WebSocket `payment_success` được emit.

---

### `GET /iot/cash-status/<order_id>` 🔑 *(Thanh toán tiền mặt)*
Kiểm tra tổng số tiền đã nhét và trạng thái thanh toán.

**Response `200`:**
```json
{
  "success": true,
  "data": {
    "order_id": 123,
    "price": 75000,
    "total_inserted": 50000,
    "remaining": 25000,
    "change": 0,
    "is_paid": false,
    "status_payment": "pending",
    "deposits": [
      { "deposit_id": 1, "denomination": 50000, "inserted_at": "2026-03-04T09:05:00" }
    ]
  }
}
```

---

## 8. Thống kê (Stats)

### `GET /stats` 🔒
Tổng quan thống kê hệ thống.

**Response `200`:**
```json
{
  "success": true,
  "data": {
    "monthly_revenue": 5000000,
    "best_product": {
      "product_id": 1,
      "product_name": "Nước suối",
      "total_sold": 120
    },
    "top_customer": {
      "sender_bank": "VCB",
      "sender_account": "0123456789",
      "transaction_count": 15,
      "total_amount": 750000
    },
    "total_orders": 250
  }
}
```

---

## 9. Upload file

### `POST /upload` 🔒
Upload ảnh sản phẩm.

**Request:** `multipart/form-data` với field `file`.

**Định dạng hỗ trợ:** `png, jpg, jpeg, gif, webp`

**Response `200`:**
```json
{
  "success": true,
  "data": {
    "url": "/static/uploads/abc123.jpg",
    "filename": "abc123.jpg"
  }
}
```

---

## 10. WebSocket

**URL:** `ws://localhost:5000/payment` (namespace `/payment`)

### Sự kiện từ client → server

| Event | Payload | Mô tả |
|---|---|---|
| `subscribe` | `{ "order_id": 123 }` | Đăng ký nhận thông báo cho đơn hàng |
| `unsubscribe` | `{ "order_id": 123 }` | Hủy đăng ký |

### Sự kiện từ server → client

| Event | Payload | Mô tả |
|---|---|---|
| `subscribed` | `{ "order_id": 123, "status": "subscribed" }` | Xác nhận đăng ký thành công |
| `payment_success` | `{ "order_id": 123, "status": "completed", "amount": 50000, "payment_method": "cash" \| "qr", "change": 25000 }` | Thanh toán thành công |
| `payment_failed` | `{ "order_id": 123, "status": "failed", "reason": "..." }` | Thanh toán thất bại |
| `payment_cancelled` | `{ "order_id": 123, "status": "cancelled" }` | Thanh toán bị hủy |

---

## Sơ đồ luồng thanh toán

### Thanh toán QR (PayOS)
```
Frontend          Backend              Arduino         PayOS
   │                  │                    │               │
   ├─POST /iot/create-order                │               │
   │                  │                    │               │
   ├─POST /payment/create                  │               │
   │◄─── checkout_url ┤                    │               │
   │                  │                    │               │
   │ (Khách quét QR)  │                    │               │
   │                  │◄────────────────────── webhook ────┤
   │                  ├─ order.status_payment = completed  │
   │                  ├─ order.status_slots  = pending     │
   │◄─ WebSocket ──── ┤                    │               │
   │                  │                    │               │
   │          Arduino poll pending-orders  │               │
   │                  ├────────────────────►               │
   │                  │        nhả hàng    │               │
   │                  │◄──dispense-complete┤               │
```

### Thanh toán tiền mặt
```
Arduino                   Backend                    Frontend
   │                          │                           │
   ├─POST /iot/create-order   │                           │
   │◄─── order_id ────────────┤                           │
   │                          │                  Hiển thị Cash Modal
   │ (Khách nhét tiền)        │                           │
   ├─POST /iot/cash-insert ──►│                           │
   │◄─ paid: false ───────────┤    GET /iot/cash-status ──┤
   │                          │◄──────────────────────────│
   │ (Nhét thêm tiền)         │                           │
   ├─POST /iot/cash-insert ──►│                           │
   │◄─ paid: true ────────────┤                           │
   │                          ├─ WebSocket payment_success►│
   │                          │                   Thành công!
   │   poll pending-orders    │                           │
   ├─GET /iot/pending-orders─►│                           │
   │◄─ order cần nhả ─────────┤                           │
   │   nhả hàng               │                           │
   ├─POST /iot/dispense-complete►                         │
```

---

## 11. Thiết bị — Tình trạng & Phiên làm việc (Devices)

> Các endpoint này dành cho **admin dashboard** để theo dõi tình trạng thiết bị.  
> Tất cả yêu cầu `Authorization: Bearer <token>` 🔒

---

### Định danh thiết bị (Device Identity)

#### `GET /devices/identity` 🔒
Lấy danh sách định danh của tất cả thiết bị *(chứa MAC, khóa công khai, trạng thái)*.

**Response `200`:**
```json
{
  "success": true,
  "data": [
    {
      "machine_id": 1,
      "mac_address": "AA:BB:CC:DD:EE:FF",
      "device_public_key": "-----BEGIN PUBLIC KEY-----...",
      "cert_fingerprint": "SHA256:abc...",
      "secure_element_id": "SE-001",
      "status": "active",
      "registered_at": "2026-03-01T08:00:00",
      "revoked_at": null
    }
  ]
}
```

**Giá trị `status`:** `pending` | `active` | `revoked`

---

#### `GET /devices/identity/<machine_id>` 🔒
Lấy thông tin định danh của 1 máy cụ thể.

---

#### `POST /devices/identity` 🔒
Tạo mới hoặc cập nhật định danh thiết bị.

**Request body:**
```json
{
  "machine_id": 1,
  "mac_address": "AA:BB:CC:DD:EE:FF",
  "device_public_key": "-----BEGIN PUBLIC KEY-----...",
  "cert_fingerprint": "SHA256:abc...",
  "secure_element_id": "SE-001",
  "status": "active"
}
```

---

#### `PUT /devices/identity/<machine_id>/revoke` 🔒
Thu hồi định danh thiết bị (đánh dấu bị xâm phạm hoặc thay thế).

**Response `200`:**
```json
{ "success": true, "message": "Device identity revoked successfully" }
```

> Sau khi revoke, thiết bị cần được đăng ký lại qua `POST /iot/register-device`.

---

### Phiên làm việc thiết bị (Device Sessions)

#### `GET /devices/sessions` 🔒
Lấy toàn bộ lịch sử phiên làm việc của các thiết bị (mới nhất lên đầu).

---

#### `GET /devices/sessions/machine/<machine_id>` 🔒
Lấy lịch sử phiên làm việc của 1 máy cụ thể.

**Response `200`:**
```json
{
  "success": true,
  "data": [
    {
      "session_id": 10,
      "machine_id": 1,
      "issued_at": "2026-03-04T08:00:00",
      "expires_at": "2026-03-05T08:00:00",
      "last_heartbeat": "2026-03-04T09:30:00",
      "is_revoked": false
    }
  ]
}
```

---

#### `POST /devices/sessions` 🔒
Tạo phiên mới thủ công cho thiết bị.

---

#### `PUT /devices/sessions/<session_id>/revoke` 🔒
Thu hồi phiên làm việc cụ thể (buộc thiết bị phải kết nối lại).

---

### Nhật ký thiết bị (Device Logs)

#### `GET /devices/logs` 🔒
Lấy nhật ký log từ thiết bị *(có phân trang, có thể lọc theo máy)*.

**Query params:**

| Param | Kiểu | Mô tả |
|---|---|---|
| `machine_id` | int | Lọc theo máy |
| `page` | int | Trang (mặc định 1) |
| `per_page` | int | Số bản ghi/trang (mặc định 50) |

**Response `200`:**
```json
{
  "success": true,
  "data": [
    {
      "log_id": 5,
      "machine_id": 1,
      "level": "error",
      "message": "Bill acceptor jammed",
      "data": { "sensor": "bill", "code": 503 },
      "created_at": "2026-03-04T09:00:00"
    }
  ],
  "meta": {
    "page": 1,
    "per_page": 50,
    "total": 120,
    "pages": 3
  }
}
```

---

## 12. Bảo mật & Nhật ký (Security Logs)

> Tất cả yêu cầu `Authorization: Bearer <token>` 🔒

---

### Lịch sử request API (API Audit Log)

#### `GET /audit-logs` 🔒
Lấy lịch sử toàn bộ các request API (có phân trang & nhiều bộ lọc).

**Query params:**

| Param | Kiểu | Mô tả |
|---|---|---|
| `machine_id` | int | Lọc theo máy |
| `endpoint` | string | Tìm theo endpoint (partial match) |
| `method` | string | Lọc theo HTTP method (`GET`, `POST`, ...) |
| `status_code` | int | Lọc theo HTTP response code |
| `sig_ok` | bool | Lọc theo signature hợp lệ (`true`/`false`) |
| `page` | int | Trang (mặc định 1) |
| `per_page` | int | Số bản ghi/trang (mặc định 50, tối đa 200) |

**Ví dụ:** `GET /audit-logs?machine_id=1&status_code=401&sig_ok=false`

**Response `200`:**
```json
{
  "success": true,
  "data": [
    {
      "request_id": 500,
      "machine_id": 1,
      "endpoint": "/api/iot/cash-insert",
      "method": "POST",
      "response_code": 200,
      "signature_ok": true,
      "created_at": "2026-03-04T09:05:00"
    }
  ],
  "meta": { "page": 1, "per_page": 50, "total": 1200, "pages": 24 }
}
```

---

#### `GET /audit-logs/stats` 🔒
Tổng hợp nhanh thống kê API: tổng request, tỉ lệ lỗi, chữ ký không hợp lệ.

**Response `200`:**
```json
{
  "success": true,
  "data": {
    "total_requests": 5000,
    "error_requests": 42,
    "bad_signature_requests": 3,
    "error_rate_pct": 0.84
  }
}
```

---

### Nhật ký nhân viên vận hành (Staff Access Log)

#### `GET /staff-access` 🔒
Lấy danh sách lịch sử nhân viên mở/vận hành máy.

**Query params:**

| Param | Kiểu | Mô tả |
|---|---|---|
| `machine_id` | int | Lọc theo máy |
| `user_id` | int | Lọc theo nhân viên |
| `action` | string | Lọc theo loại: `open`, `close`, `refill`, `maintenance` |
| `open_only` | bool | Nếu `true`, chỉ lấy phiên chưa đóng |
| `page` | int | Trang |
| `per_page` | int | Số bản ghi/trang |

**Ví dụ:** `GET /staff-access?open_only=true` — xem ai đang mở máy ngay lúc này

**Response `200`:**
```json
{
  "success": true,
  "data": [
    {
      "access_id": 12,
      "user_id": 1,
      "machine_id": 1,
      "action": "refill",
      "note": "Nạp thêm 50 chai nước",
      "started_at": "2026-03-04T09:00:00",
      "ended_at": "2026-03-04T09:15:00"
    }
  ]
}
```

---

#### `GET /staff-access/<access_id>` 🔒
Xem chi tiết 1 lần vào/ra máy.

---

#### `POST /staff-access` 🔒
Ghi nhận nhân viên bắt đầu vận hành máy.

**Request body:**
```json
{
  "machine_id": 1,
  "action": "refill",
  "note": "Nạp thêm 50 chai nước",
  "user_id": 1
}
```

> `action` hợp lệ: `open` | `close` | `refill` | `maintenance`  
> `user_id` nếu không truyền, mặc định là người đang đăng nhập.

**Response `201`:**
```json
{
  "success": true,
  "message": "Đã ghi nhận hành động \"refill\" cho máy 1",
  "data": { "access_id": 12, "started_at": "2026-03-04T09:00:00", "ended_at": null }
}
```

---

#### `PUT /staff-access/<access_id>/close` 🔒
Đóng phiên vận hành máy (ghi nhận đã xong việc).

**Request body** *(tùy chọn)*:
```json
{ "note": "Đã nạp đủ hàng và kiểm tra xong" }
```

**Response `200`:**
```json
{
  "success": true,
  "message": "Đã đóng phiên sau 15.0 phút",
  "data": { "access_id": 12, "started_at": "...", "ended_at": "..." }
}
```

---

## 13. Giao dịch (Transactions)

> Tất cả yêu cầu `Authorization: Bearer <token>` 🔒

---

### `GET /transactions` 🔒
Lấy danh sách giao dịch (mới nhất lên đầu).

**Response `200`:**
```json
{
  "success": true,
  "data": [
    {
      "transaction_id": 55,
      "order_id": 123,
      "amount": 50000,
      "status": "completed",
      "payment_method": "cash",
      "sender_bank": null,
      "sender_account": null,
      "transferred_at": "2026-03-04T09:06:00"
    },
    {
      "transaction_id": 54,
      "order_id": 120,
      "amount": 35000,
      "status": "completed",
      "payment_method": "qr",
      "sender_bank": "VCB",
      "sender_account": "0123456789",
      "transferred_at": "2026-03-04T08:00:00"
    }
  ]
}
```

**Giá trị `payment_method`:** `qr` | `cash`  
**Giá trị `status`:** `completed` | `failed` | `refunded`

---

### `GET /transactions/<transaction_id>` 🔒
Lấy chi tiết 1 giao dịch.

---

### `POST /transactions` ✅
*(Internal)* Tạo giao dịch thủ công. Thông thường được tạo tự động bởi server khi thanh toán thành công.

**Request body:**
```json
{
  "order_id": 123,
  "amount": 50000,
  "status": "completed",
  "payment_method": "cash"
}
```
