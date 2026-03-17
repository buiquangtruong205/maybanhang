# Tài Liệu API

> Base URL mặc định: `http://localhost:5000/api`
>
> Cập nhật theo code hiện tại: `2026-03-16`

## Quy ước

- `🔒`: yêu cầu JWT token `Authorization: Bearer <token>`
- `🔑`: yêu cầu `X-Machine-Key`
- `✅`: public

Response chung:

```json
{
  "success": true,
  "message": "...",
  "data": {}
}
```

## 1. Xác thực và người dùng

- `POST /register` ✅
  - Tạo tài khoản quản trị đầu tiên.
  - Hệ thống chỉ cho phép `1` tài khoản.
- `POST /login` ✅
  - Đăng nhập bằng `username/password`, trả về JWT.
- `GET /users/me` 🔒
  - Lấy thông tin tài khoản hiện tại.
- `GET /users/count` ✅
  - Kiểm tra số lượng user hiện có.
- `GET /users` 🔒
- `GET /users/<user_id>` 🔒
- `PUT /users/<user_id>` 🔒
- `DELETE /users/<user_id>` 🔒

Lưu ý:
- Passkey/WebAuthn vẫn còn trong backend nhưng đang ẩn khỏi màn hình đăng nhập admin.

## 2. Sản phẩm, máy và slot

- `GET /products` ✅
- `GET /products/<product_id>` ✅
- `POST /products` 🔒
- `PUT /products/<product_id>` 🔒
- `DELETE /products/<product_id>` 🔒
- `POST /upload` 🔒
  - Upload ảnh sản phẩm.

- `GET /machines` ✅
- `GET /machines/<machine_id>` ✅
- `POST /machines` 🔒
- `PUT /machines/<machine_id>` 🔒
- `DELETE /machines/<machine_id>` 🔒

- `GET /slots` ✅
  - Hỗ trợ query `machine_id`.
- `GET /slots/<slot_id>` ✅
- `POST /slots` 🔒
- `PUT /slots/<slot_id>` 🔒
- `DELETE /slots/<slot_id>` 🔒

## 3. Đơn hàng và giao dịch

- `GET /orders` 🔒
- `GET /orders/<order_id>` 🔒
- `POST /orders` ✅
  - Legacy flow, tạo đơn hoàn tất luôn.
- `POST /orders/pending` ✅
  - Tạo đơn chờ thanh toán.
- `PUT /orders/<order_id>/complete` ✅
- `PUT /orders/<order_id>/cancel` ✅
- `GET /orders/<order_id>/status` ✅

- `GET /transactions` 🔒
- `GET /transactions/<transaction_id>` 🔒
- `POST /transactions` ✅

Lưu ý vận hành:
- Một số endpoint ở nhóm này đang public và đã được ghi chú trong `docs/cong_viec_can_lam.md`.

## 4. Thanh toán

- `POST /payment/create` ✅
  - Tạo link thanh toán PayOS.
- `POST /payment/webhook` ✅
  - Nhận callback từ PayOS.
- `GET /payment/status/<order_code>` ✅
  - Kiểm tra trạng thái thanh toán từ PayOS và có thể sync về DB.
- `POST /payment/sync/<order_code>` ✅
  - Đồng bộ thủ công trạng thái thanh toán.
- `POST /payment/cancel/<order_code>` ✅
  - Hủy link thanh toán.
- `GET /payment/success` ✅
- `GET /payment/cancel` ✅
- `GET /debug-db` ✅
  - Endpoint debug trạng thái đơn/giao dịch.

## 5. IoT

- `POST /iot/ping` 🔑
- `POST /iot/frontend-heartbeat` 🔑
- `POST /iot/dispense-complete` 🔑
- `GET /iot/pending-orders` 🔑
- `POST /iot/stock-update` 🔑
- `POST /iot/create-order` 🔑
- `GET /iot/check-payment/<order_id>` 🔑
- `POST /iot/logs` 🔑
- `POST /iot/register-device` 🔑
- `POST /iot/heartbeat` 🔑
- `POST /iot/cash-insert` 🔑
- `GET /iot/cash-status/<order_id>` 🔑

Header mẫu:

```http
X-Machine-Key: maybanhang-v3
```

Mọi endpoint trong nhóm này đều có thể nhận `machine_key` qua:
- Header `X-Machine-Key`
- JSON body `{"machine_key":"maybanhang-v3"}`
- Query string `?machine_key=maybanhang-v3`

Khuyến nghị cho firmware:
- Luôn gửi qua header `X-Machine-Key`
- Parse cả `success` và HTTP status code
- Khi nhận `401/403` thì coi như lỗi xác thực máy

### 5.1. Đăng ký và heartbeat thiết bị

#### `POST /iot/register-device` 🔑

Mục đích:
- Thiết bị tự đăng ký hoặc cập nhật nhận diện khi boot lần đầu.
- Nếu `machine_id` tương ứng chưa có bản ghi `Machine`, backend sẽ tự tạo.

Request mẫu:

```json
{
  "mac_address": "AA:BB:CC:DD:EE:FF",
  "fingerprint": "abc123def456",
  "firmware_version": "1.0.0"
}
```

Response mẫu:

```json
{
  "success": true,
  "message": "Device registered successfully",
  "data": {
    "machine_id": 3,
    "mac_address": "AA:BB:CC:DD:EE:FF",
    "status": "active"
  }
}
```

Ghi chú:
- Backend hiện nhận `firmware_version` nhưng chưa lưu xuống DB.
- Sau khi đăng ký, trạng thái máy được đặt thành `online`.

#### `POST /iot/heartbeat` 🔑

Mục đích:
- Gửi heartbeat định kỳ để backend ghi nhận thiết bị còn online.
- Backend tạo hoặc cập nhật `DeviceSession`.

Request mẫu:

```json
{
  "uptime": 3600,
  "free_memory": 50000,
  "wifi_rssi": -65
}
```

Response mẫu:

```json
{
  "success": true,
  "message": "Heartbeat received",
  "data": {
    "machine_id": 3,
    "session_id": 12,
    "server_time": "2026-03-17T10:00:00.000000"
  }
}
```

Khuyến nghị:
- Gọi mỗi `15-60s` tùy độ ổn định mạng.
- Lưu `session_id` để log/debug, nhưng hiện tại firmware không cần gửi lại session này ở endpoint khác.

#### `POST /iot/ping` 🔑

Mục đích:
- Ping đơn giản để kiểm tra kết nối backend.

Request mẫu:

```json
{
  "status": "online",
  "temperature": 25.5
}
```

Response mẫu:

```json
{
  "success": true,
  "message": "Pong",
  "machine_id": 3,
  "server_time": "2026-03-17T10:00:00.000000"
}
```

### 5.2. Điều phối frontend tại máy

#### `POST /iot/frontend-heartbeat` 🔑

Mục đích:
- Chỉ cho phép một frontend điều khiển máy tại một thời điểm.
- Phù hợp khi máy có kiosk/webview và muốn chặn truy cập đồng thời.

Request mẫu:

```json
{
  "session_id": "frontend-session-001"
}
```

Response được chấp nhận:

```json
{
  "success": true,
  "message": "Heartbeat accepted",
  "rejected": false
}
```

Response bị từ chối:

```json
{
  "success": false,
  "message": "System in use by another device",
  "rejected": true
}
```

Ghi chú:
- Timeout session hiện tại trong code là `5 giây`.
- Nếu frontend ngừng heartbeat quá lâu, session khác có thể giành quyền.

### 5.3. Tạo đơn tại máy

#### `POST /iot/create-order` 🔑

Mục đích:
- Máy tạo đơn khi khách chọn sản phẩm trực tiếp trên máy.
- Đơn được tạo với `status_payment=pending`, `status_slots=pending`.

Request mẫu theo `slot_code`:

```json
{
  "slot_code": "A1",
  "quantity": 1
}
```

Request mẫu theo `product_id`:

```json
{
  "product_id": 5,
  "quantity": 1
}
```

Response mẫu:

```json
{
  "success": true,
  "message": "Order created successfully",
  "data": {
    "order_id": 123,
    "product_id": 5,
    "product_name": "Coca Cola",
    "price": 15000.0,
    "slot_code": "A1",
    "status_payment": "pending",
    "status_slots": "pending"
  }
}
```

Logic backend hiện tại:
- Nếu truyền `slot_code`, backend tìm slot theo `machine_id + slot_code`
- Nếu không truyền `product_id` mà slot đã gán sản phẩm, backend tự suy ra `product_id`
- Có check tồn kho khả dụng theo công thức:
  `available_stock = total_stock_in_machine - pending_orders_trong_15_phut`

Lưu ý:
- Nếu sản phẩm đang được người khác giữ đơn chờ thanh toán, endpoint có thể trả lỗi hết hàng tạm thời.
- Firmware nên hiển thị chính xác thông báo trả về từ backend.

### 5.4. Kiểm tra thanh toán

#### `GET /iot/check-payment/<order_id>` 🔑

Mục đích:
- Máy kiểm tra một đơn cụ thể đã thanh toán chưa.

Response mẫu:

```json
{
  "success": true,
  "message": "Order status retrieved",
  "data": {
    "order_id": 123,
    "status_payment": "completed",
    "status_slots": "pending",
    "paid": true,
    "price": 15000.0
  }
}
```

Ý nghĩa:
- `status_payment=completed`: thanh toán xong
- `status_slots=pending`: chưa nhả hàng
- `paid=true`: firmware có thể chuyển sang chờ xuất hàng hoặc gọi motor tùy luồng của bạn

#### `GET /iot/pending-orders` 🔑

Mục đích:
- Lấy danh sách các đơn của máy đã thanh toán xong nhưng chưa xuất hàng.
- Đây là endpoint quan trọng nhất để firmware poll trước khi quay motor.

Response mẫu:

```json
{
  "success": true,
  "message": "Found 1 pending orders",
  "data": [
    {
      "order_id": 123,
      "slot_id": 10,
      "product_id": 5,
      "price": 15000.0,
      "created_at": "2026-03-17T10:00:00"
    }
  ]
}
```

Khuyến nghị:
- Poll mỗi `1-3s` trong lúc máy đang chờ thanh toán/xuất hàng.
- Khi lấy được đơn, firmware nên lock cơ cấu cơ khí để tránh xử lý trùng.

### 5.5. Báo kết quả nhả hàng

#### `POST /iot/dispense-complete` 🔑

Mục đích:
- Sau khi motor/cơ cấu cơ khí chạy xong, máy báo kết quả cho backend.

Request mẫu thành công:

```json
{
  "order_id": 123,
  "slot_code": "A1",
  "success": true,
  "message": "Dispensed successfully"
}
```

Request mẫu thất bại:

```json
{
  "order_id": 123,
  "slot_code": "A1",
  "success": false,
  "message": "Motor timeout"
}
```

Response mẫu:

```json
{
  "success": true,
  "message": "Dispense completed",
  "order_id": 123
}
```

Logic trạng thái:
- Nếu `success=true` thì backend set `status_slots=dispensed`
- Nếu `success=false` thì backend set `status_slots=failed`

Lưu ý quan trọng:
- Stock hiện bị trừ ngay lúc thanh toán thành công, chưa đợi `dispense-complete`.
- Nếu nhả hàng thất bại, backend hiện chỉ đổi trạng thái đơn sang `failed`, không tự hoàn stock.

### 5.6. Đồng bộ tồn kho

#### `POST /iot/stock-update` 🔑

Mục đích:
- Máy chủ động cập nhật tồn kho của một slot.

Request mẫu:

```json
{
  "slot_code": "A1",
  "stock": 5
}
```

Response mẫu:

```json
{
  "success": true,
  "message": "Stock updated",
  "slot_code": "A1",
  "old_stock": 6,
  "new_stock": 5
}
```

Dùng khi:
- Có cảm biến nhận biết còn hàng
- Có thao tác refill tại máy
- Cần đồng bộ lại stock sau lỗi cơ khí

### 5.7. Log thiết bị

#### `POST /iot/logs` 🔑

Mục đích:
- Gửi log chủ động từ MCU/Raspberry Pi lên server để đội vận hành xem lại.

Request mẫu:

```json
{
  "level": "error",
  "message": "Sensor malfunction",
  "data": {
    "sensor": "temp",
    "code": 500
  }
}
```

Response mẫu:

```json
{
  "success": true,
  "message": "Log saved successfully"
}
```

Mức log phù hợp:
- `info`
- `warning`
- `error`
- `critical`

### 5.8. Thanh toán tiền mặt

#### `POST /iot/cash-insert` 🔑

Mục đích:
- Mỗi lần bill acceptor nhận một tờ tiền, firmware gọi endpoint này một lần.

Request mẫu:

```json
{
  "order_id": 123,
  "denomination": 50000
}
```

Mệnh giá hợp lệ:
- `1000`
- `2000`
- `5000`
- `10000`
- `20000`
- `50000`
- `100000`
- `200000`
- `500000`

Response khi chưa đủ tiền:

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

Response khi đủ tiền:

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

Logic backend khi đủ tiền:
- Set `status_payment=completed`
- Set `status_slots=pending`
- Giảm stock slot
- Tạo `Transaction`
- Phát sự kiện WebSocket `payment_success`

Việc firmware cần làm:
- Nếu `paid=false`: tiếp tục nhận tiền
- Nếu `paid=true`: nếu có module trả tiền thừa thì dùng giá trị `change`
- Sau đó máy tiếp tục poll `pending-orders` hoặc gọi thẳng luồng xuất hàng

#### `GET /iot/cash-status/<order_id>` 🔑

Mục đích:
- Kiểm tra tổng tiền đã nhét cho một đơn.

Response mẫu:

```json
{
  "success": true,
  "message": "Cash status retrieved",
  "data": {
    "order_id": 123,
    "price": 75000,
    "total_inserted": 50000,
    "remaining": 25000,
    "change": 0,
    "is_paid": false,
    "status_payment": "pending",
    "deposits": [
      {
        "deposit_id": 1,
        "denomination": 50000,
        "inserted_at": "2026-03-17T10:00:00"
      }
    ]
  }
}
```

### 5.9. Luồng tích hợp phần cứng khuyến nghị

#### Luồng QR

1. Thiết bị boot, gọi `register-device`
2. Gọi `heartbeat` định kỳ
3. Khách chọn hàng, máy gọi `create-order`
4. Frontend/backend tạo QR qua nhóm `/payment/*`
5. Thiết bị poll `check-payment/<order_id>` hoặc `pending-orders`
6. Khi đơn đã thanh toán và đang chờ xuất hàng, firmware điều khiển motor
7. Gọi `dispense-complete`
8. Nếu cần, gọi `stock-update` để đối soát lại số lượng thực tế

#### Luồng tiền mặt

1. Thiết bị boot, gọi `register-device`
2. Tạo đơn bằng `create-order`
3. Mỗi lần nhận tờ tiền, gọi `cash-insert`
4. Khi `paid=true`, lấy `change` để xử lý trả tiền thừa
5. Poll `pending-orders`
6. Xuất hàng xong, gọi `dispense-complete`

#### Luồng kiosk/webview tại máy

1. Frontend tại máy tạo `session_id`
2. Gửi `frontend-heartbeat` liên tục
3. Nếu backend trả `rejected=true`, chặn giao diện và báo máy đang được dùng ở thiết bị khác

## 6. Thiết bị, firmware và log bảo mật

- `GET /devices/identity` 🔒
- `GET /devices/identity/<machine_id>` 🔒
- `POST /devices/identity` 🔒
- `PUT /devices/identity/<machine_id>/revoke` 🔒

- `GET /devices/sessions` 🔒
- `GET /devices/sessions/machine/<machine_id>` 🔒
- `POST /devices/sessions` 🔒
- `PUT /devices/sessions/<session_id>/revoke` 🔒

- `GET /devices/logs` 🔒

- `GET /firmware/updates` 🔒
- `POST /firmware/updates` 🔒
- `DELETE /firmware/updates/<update_id>` 🔒

- `GET /audit-logs` 🔒
- `GET /audit-logs/stats` 🔒
- `GET /staff-access` 🔒
- `GET /staff-access/<access_id>` 🔒
- `POST /staff-access` 🔒
- `PUT /staff-access/<access_id>/close` 🔒
- `GET /admin-logs` 🔒
- `GET /admin-logs/stats` 🔒

## 7. WebAuthn / Passkey

Các route sau vẫn còn hoạt động trong backend, nhưng đang không hiển thị trên màn hình đăng nhập admin:

- `POST /webauthn/register/begin` 🔒
- `POST /webauthn/register/complete` 🔒
- `POST /webauthn/login/begin` ✅
- `POST /webauthn/login/complete` ✅
- `GET /webauthn/status` 🔒
- `DELETE /webauthn/remove` 🔒

## 8. WebSocket

Namespace đang dùng:

- `/payment`

Event chính:

- `subscribe`
- `unsubscribe`
- `payment_success`
- `payment_failed`
- `payment_cancelled`

## Ghi chú

- Tài liệu này mô tả route đang tồn tại theo code hiện tại, không đồng nghĩa toàn bộ route đều an toàn cho production.
- Các điểm cần siết lại đã được ghi trong [`cong_viec_can_lam.md`](./cong_viec_can_lam.md).
