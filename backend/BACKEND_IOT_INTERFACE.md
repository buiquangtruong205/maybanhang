# 🔌 Đặc Tả Giao Diện Giao Tiếp Backend - IoT (ESP32)

> Tài liệu này dành riêng cho nhà phát triển phần cứng (Hardware/Firmware) để hiểu cách Backend cung cấp dữ liệu và nhận phản hồi từ máy bán hàng.

---

## 🏗️ Mô Hình Vận Hành: Hybrid (Kép)

| Kênh | Mô tả | ESP32 làm gì? |
| :--- | :--- | :--- |
| **🖐️ Kênh 1: Tại máy** | Khách nhìn sản phẩm trưng bày → Bấm số trên Keypad → QR hiện trên OLED | ESP32 gọi API tạo đơn hàng, hiển thị QR thanh toán, nhả hàng |
| **🌐 Kênh 2: Online** | Khách truy cập web → Xem ảnh sản phẩm → Chọn mua → Đến máy nhận hàng | ESP32 chỉ nhận lệnh nhả hàng từ Backend |

---

## 📝 Quy Tắc Chung
- **Ngôn ngữ:** Tiếng Việt 100% trong mọi trao đổi và tài liệu.
- **Xác thực:** Mọi yêu cầu từ thiết bị phải gửi kèm Header: `X-Machine-Key: <Secret_Key_Của_Máy>`.
- **Định dạng dữ liệu:** JSON (UTF-8).
- **Base URL API:** `http://<ip-server>:5001/api/v1/iot`

---

## 📡 1. Giao tiếp qua REST API (HTTP)

Đây là phương thức giao tiếp chính để kiểm tra trạng thái và báo cáo kết quả.

### 1.1 Kiểm tra Đơn hàng (Check Order)
Dùng để máy hỏi Backend: "Mã đơn hàng này đã được thanh toán để nhả sản phẩm chưa?"

- **Endpoint:** `GET /check-order/{order_code}`
- **Header:** `X-Machine-Key: <key>`
- **Phản hồi Thành công (200 OK):**
```json
{
    "order_code": 123456,
    "status": "paid",
    "should_dispense": true,
    "machine_id": 1
}
```
- **Lưu ý:** Nếu `should_dispense` là `false`, máy **KHÔNG ĐƯỢC** nhả hàng.

### 1.2 Báo cáo Kết quả Nhả hàng (Dispense Result)
Dùng để máy báo cho Backend biết việc đẩy hàng ra lò xo có thành công hay không.

- **Endpoint:** `POST /dispense-complete`
- **Header:** `X-Machine-Key: <key>`
- **Body:**
```json
{
    "order_code": 123456,
    "success": true
}
```
- **Phản hồi:** `{"success": true, "machine_id": 1}`

### 1.3 Tạo Đơn Hàng Từ Máy — *Dùng cho Kênh 1 (Keypad)*
Sau khi khách bấm số trên Keypad, ESP32 mapping số → slot sản phẩm → gọi API tạo đơn hàng → nhận lại QR code thanh toán để hiển thị trên OLED.

- **Endpoint:** `POST /api/v1/orders/`
- **Header:** `X-Machine-Key: <key>`
- **Body:**
```json
{
    "slot_number": 3,
    "machine_id": 1
}
```
- **Phản hồi:** Trả về `order_code`, `checkout_url`, `qr_code` (chuỗi VietQR)
- **Lưu ý:** ESP32 không cần lấy danh sách sản phẩm vì sản phẩm được trưng bày vật lý trong máy. Backend sẽ tự tra cứu sản phẩm dựa trên `slot_number` + `machine_id`.

### 1.4 Nhịp Tim (Heartbeat)
Dùng để máy báo cáo nó vẫn đang "Sống" (Online).

- **Endpoint:** `POST /heartbeat`
- **Header:** `X-Machine-Key: <key>`
- **Phản hồi:** `{"status": "online"}`

---

## 📟 2. Giao tiếp qua Broker MQTT (Real-time)

Backend sử dụng MQTT để gửi lệnh điều khiển tức thời cho máy (Push) thay vì máy phải đi hỏi (Pull).

| Topic | Hướng | Dữ liệu (JSON) | Mô tả |
| :--- | :--- | :--- | :--- |
| `vending/machine/{id}/cmd` | Backend → ESP32 | `{"cmd": "dispense", "slot": 5, "order_code": 123}` | Lệnh nhả hàng tức thì |
| `vending/machine/{id}/stat` | ESP32 → Backend | `{"status": "online", "temp": 25.5}` | Báo cáo trạng thái máy |
| `vending/machine/{id}/resp` | ESP32 → Backend | `{"order_code": 123, "success": true}` | Phản hồi lệnh đã thực hiện |

---

## 🛠️ 3. Các yêu cầu phía Backend cần đáp ứng

Để Phần cứng hoạt động tốt, Backend đã/đang được xây dựng các thành phần sau:

1.  **Quản lý Khóa Bí Mật (Secret Key):** Mỗi máy có một chuỗi ký tự duy nhất để định danh. Phần cứng phải được nạp chuỗi này vào bộ nhớ Flash (EEPROM/NVS).
2.  **Logic Logic Nhả Hàng (Anti-Double-Dispense):** Backend đảm bảo một mã đơn hàng chỉ được nhả hàng **duy nhất 1 lần**.
3.  **Tích hợp MQTT Broker:** Một server trung gian (như Mosquitto) để truyền nhận tin nhắn giữa Backend và ESP32 với độ trễ thấp (<100ms).
4.  **Cập nhật tồn kho tự động:** Khi nhận được `success: true` từ máy, Backend trừ tồn kho thực tế nếu các bước trước chưa trừ.

---

## 💡 4. Ví dụ Luồng Thực Tế (Workflow)

1.  **Kênh 1:** Khách nhìn Pepsi trưng bày ở vị trí 3 → Bấm phím `3` trên Keypad → ESP32 gọi `POST /orders/` (slot_number=3) → OLED hiển thị QR.
2.  **Kênh 2:** Hoặc khách truy cập web → Xem ảnh Pepsi → Nhấn "Mua" → Web hiển thị QR.
3.  **Cả 2 kênh:** Khách quét QR thanh toán bằng app ngân hàng.
4.  **Backend:** Nhận Webhook PayOS → Gửi MQTT tới `vending/machine/1/cmd` với `{"cmd": "dispense", "slot": 3}`.
5.  **ESP32:** Nhận MQTT → Quay motor tại Slot 3.
6.  **ESP32:** Motor quay xong → Gọi API `POST /iot/dispense-complete` với `{"order_code": xxx, "success": true}`.
7.  **Backend:** Cập nhật đơn hàng thành `COMPLETED` → OLED hiển thị "THÀNH CÔNG!" và/hoặc Web báo cho khách.

---
*Tài liệu này sẽ được cập nhật liên tục khi có thêm tính năng mới.*
