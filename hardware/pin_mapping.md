# Sơ đồ Chân cắm (Pin Mapping) - Vending Machine V3

Bảng dưới đây liệt kê chính xác các chân cắm đang được sử dụng trong mã nguồn. Hãy đối chiếu kỹ khi đấu nối phần cứng.

---

## 1. ESP32 (Bộ điều khiển trung tâm)

| Thành phần | Chân (Pin) | Ghi chú |
| :--- | :--- | :--- |
| **Màn hình TFT ST7789V** | | Chip ST7789, 240×320, SPI |
| MOSI | 23 | |
| SCK (Clock) | 18 | |
| CS (Chip Select) | 5 | |
| DC (Data/Command) | 21 | ⚠️ Đã đổi từ GPIO 2 |
| RST (Reset) | 22 | ⚠️ Đã đổi từ GPIO 4 |
| BL (Backlight) | 3.3V trực tiếp | ⚠️ Nối thẳng, không qua GPIO |
| **Bàn phím (Keypad 4x3)** | | |
| Row 1 | 13 | |
| Row 2 | 12 | |
| Row 3 | 14 | |
| Row 4 | 27 | |
| Col 1 | 26 | |
| Col 2 | 25 | |
| Col 3 | 33 | |
| **Giao tiếp Serial (với Uno)** | | |
| TX (Gửi) | 17 | Nối vào RX của Uno |
| RX (Nhận) | 16 | Nối vào TX của Uno |

---

## 2. Arduino Uno (Điều khiển Driver)

| Thành phần | Chân (Pin) | Ghi chú |
| :--- | :--- | :--- |
| **Động cơ bước (Nhả hàng)** | | |
| IN1 | 4 | Nối vào Driver ULN2003 |
| IN2 | 5 | |
| IN3 | 6 | |
| IN4 | 7 | |
| **Cảm biến màu (TCS3200)** | | |
| S0 | A0 | |
| S1 | A1 | |
| S2 | A2 | |
| S3 | A3 | |
| OUT | 9 | |
| **Servo (Cửa nhận tiền)** | | |
| Signal | 10 | |
| **Nút nhấn / Cảm biến phụ** | | |
| Drop Sensor | 2 | Cảm biến hàng rơi |
| Status LED | 13 | Đèn báo trạng thái (Built-in) |
| **Giao tiếp Serial (với ESP32)** | | |
| RX | 0 | Nối vào TX của ESP32 |
| TX | 1 | Nối vào RX của ESP32 |

---

## 3. Lưu ý đấu nối quan trọng

1.  **Dây Serial (RX-TX):** Luôn đấu chéo (TX của board này vào RX của board kia).
2.  **Chung Ground (GND):** Bắt buộc phải nối tất cả chân GND của ESP32, Uno và Nguồn ngoài (Adapter) lại với nhau.
3.  **Nguồn cho Động cơ/Servo:** Tuyệt đối không lấy nguồn 5V trực tiếp từ chân 5V của Arduino Uno để chạy Động cơ bước và Servo. Hãy dùng nguồn 5V/12V rời bên ngoài và chỉ nối chung dây GND.
4.  **Màn hình TFT:** Nếu màn hình không sáng, kiểm tra chân BL (15) đã được nối hay chưa.
