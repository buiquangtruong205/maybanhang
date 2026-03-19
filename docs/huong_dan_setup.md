# Hướng Dẫn Setup Từ A-Z (Vending Machine V3)

Tài liệu này hướng dẫn setup toàn bộ hệ thống từ đầu, theo đúng trạng thái code hiện tại:

- Backend chạy bằng Docker
- Database khởi tạo trắng hoàn toàn
- Toàn bộ `Machine`, `DeviceIdentity`, `Product`, `Slot` được provision bởi admin
- ESP32 và Arduino Uno được nạp firmware thủ công bằng PlatformIO

Tài liệu phù hợp nhất cho môi trường Windows + Docker Desktop + VS Code + PlatformIO.

---

## 1. Tổng quan hệ thống

Hệ thống gồm 4 phần chính:

1. `backend/`
   - Flask API + admin dashboard + database schema
2. `infra/`
   - Docker Compose cho PostgreSQL, backend, nginx, MQTT
3. `firmware/esp32/`
   - ESP32 xử lý Wi-Fi, API, MQTT, màn hình TFT, keypad, logic bán hàng
4. `firmware/uno/`
   - Arduino Uno xử lý động cơ, cảm biến rơi hàng, cửa, cảm biến tiền

Luồng chuẩn khi triển khai máy mới:

1. Chạy Docker
2. Tạo tài khoản admin đầu tiên
3. Tạo `Machine`
4. Tạo `DeviceIdentity`
5. Tạo `Product`
6. Tạo `Slot`
7. Nạp firmware cho Uno và ESP32
8. Boot máy và kiểm thử

---

## 2. Yêu cầu trước khi bắt đầu

### 2.1. Phần mềm

- Docker Desktop
- Git
- VS Code
- VS Code extension: `PlatformIO IDE`
- Driver USB cho ESP32 và Arduino Uno

### 2.2. Phần cứng

- ESP32 DevKit / ESP32-WROOM
- Arduino Uno R3
- Màn hình TFT ILI9341
- Keypad 4x3
- Động cơ bước + driver
- Cảm biến rơi hàng
- Cảm biến màu / bill detector
- Servo
- Nguồn ngoài phù hợp cho động cơ

### 2.3. Mạng

- Máy tính chạy Docker và ESP32 phải cùng mạng LAN/Wi-Fi
- Bạn cần biết địa chỉ IPv4 của máy tính chạy Docker

Lấy IP trên Windows:

```powershell
ipconfig
```

Tìm dòng `IPv4 Address` của card Wi-Fi hoặc Ethernet đang dùng. Ví dụ: `192.168.1.100`.

---

## 3. Các file quan trọng cần biết

- `infra/docker-compose.yml`
- `infra/.env.example`
- `infra/nginx.conf`
- `firmware/esp32/include/secrets.example.h`
- `firmware/esp32/include/secrets.h`
- `firmware/esp32/include/app_config.h`
- `firmware/uno/include/pins.h`
- `hardware/pin_mapping.md`

---

## 4. Setup backend bằng Docker

### 4.1. Mở đúng thư mục

```powershell
cd E:\IoT\Du_An\Vending_Machine\Vesion_3\infra
```

### 4.2. Tạo file môi trường

Nếu chưa có `infra/.env`, tạo từ file mẫu:

```powershell
Copy-Item .env.example .env
```

Nếu bạn dùng Git Bash:

```bash
cp .env.example .env
```

### 4.3. Sửa `infra/.env`

Ít nhất cần kiểm tra các biến sau:

- `PAYOS_CLIENT_ID`
- `PAYOS_API_KEY`
- `PAYOS_CHECKSUM_KEY`
- `SECRET_KEY`
- `PORT`
- `DATABASE_URL`

Gợi ý:

- Nếu bạn chưa dùng QR PayOS ngay, có thể để placeholder tạm thời.
- Luồng QR sẽ không hoạt động đúng nếu bộ key PayOS sai.
- Luồng tiền mặt vẫn cần backend hoạt động bình thường.

### 4.4. Khởi tạo DB trắng hoàn toàn

Nếu bạn muốn toàn bộ dữ liệu sạch từ đầu:

```powershell
docker compose down -v --remove-orphans
```

Lệnh này sẽ xóa:

- dữ liệu PostgreSQL
- đơn hàng cũ
- giao dịch cũ
- logs cũ
- machine / slot / product / identity cũ

Lưu ý quan trọng:

- Backend hiện dùng `db.create_all()`
- Schema cũ sẽ không tự migrate
- Nếu bạn dùng volume DB cũ, có thể gặp lệch schema
- Khi cần chắc chắn sạch hoàn toàn, luôn dùng lại `docker compose down -v`

### 4.5. Build và chạy Docker

```powershell
docker compose up -d --build
```

Kiểm tra container:

```powershell
docker compose ps
```

Xem log:

```powershell
docker compose logs -f backend
docker compose logs -f nginx
docker compose logs -f db
docker compose logs -f mqtt
```

### 4.6. Truy cập dịch vụ sau khi chạy

| Dịch vụ | URL / Port |
|--------|-------------|
| Admin UI qua nginx | `http://localhost` |
| Backend API trực tiếp | `http://localhost:5000/api` |
| PostgreSQL từ host | `localhost:5433` |
| MQTT broker | `localhost:1883` |

Lưu ý:

- Admin UI nên dùng `http://localhost`
- API để test thủ công có thể dùng `http://localhost:5000/api`

---

## 5. Tạo tài khoản admin đầu tiên

### 5.1. Mở admin dashboard

Truy cập:

- `http://localhost`

Nếu cần đi thẳng backend:

- `http://localhost:5000/admin`

### 5.2. Đăng ký tài khoản đầu tiên

Ở lần chạy đầu, giao diện sẽ cho phép `Đăng ký`.

Lưu ý:

- Hệ thống hiện chỉ cho phép đúng `1` tài khoản admin
- Sau khi đã có tài khoản đầu tiên, route đăng ký sẽ bị khóa

Khuyến nghị:

- Dùng tài khoản dễ nhớ, ví dụ `admin`
- Mật khẩu đủ mạnh vì tài khoản này quản trị toàn bộ máy, sản phẩm và slot

---

## 6. Provision dữ liệu quản trị

Mục tiêu của phần này là biến DB trắng thành một hệ thống có thể chạy thực tế.

Thứ tự bắt buộc:

1. Tạo `Machine`
2. Tạo `DeviceIdentity`
3. Tạo `Product`
4. Tạo `Slot`

### 6.1. Tạo Machine trong giao diện admin

Vào tab `Máy bán hàng` và bấm `+ Thêm máy`.

Ví dụ:

- `Tên máy`: `VM-01`
- `Vị trí`: `Tang 1 - Khu A`
- `Trạng thái`: `active`
- `Secret Key`: `vm01-secret-2026`

Ý nghĩa:

- `secret_key` là khóa xác thực thiết bị
- ESP32 sẽ gửi khóa này qua header `X-Machine-Key`
- Khóa này phải trùng với `DEVICE_MACHINE_KEY` trong firmware

Lưu ý rất quan trọng:

- Hãy lưu `secret_key` lại ngay khi tạo
- Bảng admin hiện chỉ hiển thị dạng mask, không hiện nguyên văn
- Nếu quên khóa, bạn cần sửa lại máy và đặt khóa mới, sau đó nạp lại firmware với khóa mới

### 6.2. Quy ước trạng thái Machine

Trạng thái máy ảnh hưởng trực tiếp đến xác thực thiết bị:

- `active`: máy được phép hoạt động
- `online`: máy đang hoạt động và backend chấp nhận
- `inactive`: backend sẽ từ chối xác thực thiết bị
- `maintenance`: backend sẽ từ chối xác thực thiết bị

Khuyến nghị:

- Khi provision máy mới, đặt `active`

### 6.3. Tạo Product trong giao diện admin

Vào tab `Sản phẩm` và bấm `+ Thêm sản phẩm`.

Ví dụ:

- `Tên sản phẩm`: `Nuoc suoi`
- `Giá`: `10000`
- `Ảnh`: có thể để trống lúc đầu
- `Trạng thái`: `active`

Bạn có thể tạo nhiều sản phẩm trước rồi gán vào slot sau.

### 6.4. Tạo Slot trong giao diện admin

Vào tab `Khe hàng` và bấm `+ Thêm khe`.

Ví dụ:

- `Machine`: `VM-01`
- `Mã khe`: `A1`
- `Sản phẩm`: `Nuoc suoi`
- `Tồn kho`: `5`
- `Sức chứa`: `10`

Lưu ý:

- `stock` không được vượt quá `capacity`
- `slot_code` phải unique trong cùng một `machine_id`

### 6.5. Quy ước `slot_code` khi dùng keypad

Firmware ESP32 hiện map số nhập trên keypad sang `slot_code` dạng chữ-số.

Ví dụ:

| Số nhập | Slot thực tế |
|--------|---------------|
| `1`    | `A1` |
| `2`    | `A2` |
| `10`   | `A10` |
| `11`   | `B1` |
| `12`   | `B2` |
| `20`   | `B10` |
| `21`   | `C1` |

Khuyến nghị:

- Nếu máy dùng keypad theo firmware hiện tại, hãy đặt `slot_code` theo kiểu `A1`, `A2`, `B1`, `C3`...
- Nếu admin đặt mã khe khác hẳn, keypad sẽ không khớp

### 6.6. Tạo DeviceIdentity

Hiện tại giao diện admin có màn hình xem và revoke `DeviceIdentity`, nhưng chưa có form tạo mới rõ ràng trên UI.

Vì vậy bước tạo `DeviceIdentity` nên làm qua API.

#### Cách nhanh để lấy token admin

Đăng nhập vào `http://localhost`, sau đó mở trình duyệt:

1. Nhấn `F12`
2. Mở tab `Console`
3. Chạy:

```javascript
localStorage.getItem('token')
```

Copy giá trị token vừa trả về.

#### Tạo DeviceIdentity tối thiểu

Ví dụ với `machine_id = 1`:

```powershell
curl.exe -X POST http://localhost:5000/api/devices/identity `
  -H "Content-Type: application/json" `
  -H "Authorization: Bearer YOUR_ADMIN_TOKEN" `
  -d "{\"machine_id\":1,\"status\":\"active\"}"
```

Ý nghĩa:

- `machine_id` phải là ID của máy vừa tạo
- `status` nên là `active`
- Khi để trống `mac_address` và `cert_fingerprint`, backend sẽ cho ESP32 điền vào lần boot đầu tiên

#### Khi nào nên điền sẵn MAC / fingerprint

Chỉ điền trước nếu bạn thật sự muốn khóa cứng identity vào đúng một board cụ thể.

Nếu điền sẵn sai:

- `MAC address mismatch`
- hoặc `Fingerprint mismatch`

thì `register-device` sẽ bị backend từ chối.

---

## 7. Cấu hình firmware trước khi nạp

### 7.1. Cấu hình ESP32 secrets

Mở file:

- `firmware/esp32/include/secrets.h`

Nếu file chưa tồn tại, tạo từ mẫu:

- copy `firmware/esp32/include/secrets.example.h`
- đổi tên thành `firmware/esp32/include/secrets.h`

Sửa các giá trị sau:

```cpp
#define WIFI_SSID "Ten_WiFi"
#define WIFI_PASSWORD "Mat_khau_WiFi"
#define API_BASE_URL "http://192.168.1.100:5000/api"
#define DEVICE_MACHINE_KEY "vm01-secret-2026"
#define MQTT_BROKER "192.168.1.100"
#define MQTT_USER ""
#define MQTT_PASS ""
```

Giải thích:

- `API_BASE_URL` phải là IP của máy tính đang chạy Docker
- `MQTT_BROKER` cũng phải là IP của máy tính đó
- `DEVICE_MACHINE_KEY` phải trùng đúng `secret_key` của `Machine`

Không dùng:

- `http://localhost:5000/api`
- `http://backend:5000/api`
- tên service Docker

vì ESP32 không chạy bên trong mạng Docker.

### 7.2. Các giá trị còn nằm trong code

Ngoài `secrets.h`, firmware ESP32 hiện vẫn còn vài giá trị tĩnh trong:

- `firmware/esp32/include/app_config.h`

Các giá trị cần kiểm tra:

- `kMachineId`
- `kMqttCommandTopic`
- `kMqttStatusTopic`
- `kDefaultSlotCode`
- chân UART, TFT, keypad

Đặc biệt:

- `kMachineId` và `kMqttCommandTopic` vẫn chưa lấy động từ DB
- Nếu bạn triển khai nhiều máy và dùng MQTT command riêng cho từng máy, cần sửa cho đúng máy đang nạp

### 7.3. Cấu hình chân Arduino Uno

Nếu phần cứng thực tế khác mặc định, kiểm tra:

- `firmware/uno/include/pins.h`

Và đối chiếu với:

- `hardware/pin_mapping.md`

---

## 8. Nạp firmware cho Arduino Uno

### 8.1. Mở đúng project

`firmware/uno` là một project PlatformIO riêng.

Trong VS Code:

1. `File -> Open Folder`
2. Chọn thư mục `firmware/uno`

### 8.2. Kết nối board

1. Cắm Arduino Uno vào máy tính
2. Chọn đúng cổng COM trong PlatformIO nếu cần

### 8.3. Build và upload

Trong VS Code PlatformIO:

1. `Build`
2. `Upload`
3. `Monitor`

Nếu bạn có `pio` CLI:

```bash
cd firmware/uno
pio run
pio run -t upload
pio device monitor -b 115200
```

Log mong đợi:

- `[BOOT] UNO Modular ready`

---

## 9. Nạp firmware cho ESP32

### 9.1. Mở đúng project

`firmware/esp32` là một project PlatformIO riêng.

Trong VS Code:

1. `File -> Open Folder`
2. Chọn thư mục `firmware/esp32`

### 9.2. Kết nối board

1. Cắm ESP32 vào máy tính
2. Chọn đúng COM port nếu PlatformIO không tự nhận

### 9.3. Build và upload

Trong VS Code PlatformIO:

1. `Build`
2. `Upload`
3. `Monitor`

Nếu bạn có `pio` CLI:

```bash
cd firmware/esp32
pio run
pio run -t upload
pio device monitor -b 115200
```

Nếu upload lỗi do path dài trên Windows:

- ưu tiên upload trực tiếp bằng PlatformIO trong VS Code
- dùng đường dẫn dự án ngắn hơn nếu cần

---

## 10. Lắp ráp phần cứng

Đối chiếu:

- `hardware/pin_mapping.md`
- `firmware/esp32/include/app_config.h`
- `firmware/uno/include/pins.h`

Các lưu ý bắt buộc:

- Đấu chung GND của ESP32, Uno và nguồn ngoài
- Không cấp nguồn động cơ trực tiếp từ cổng 5V của board
- Dùng nguồn ngoài đủ dòng cho động cơ
- Kiểm tra kỹ dây UART giữa ESP32 và Uno
- Kiểm tra chiều quay động cơ trước khi lắp thật vào trục nhả hàng

---

## 11. Trình tự boot đúng sau khi nạp xong

### 11.1. Backend phải chạy trước

Trước khi bật máy, xác nhận Docker đang chạy:

```powershell
cd E:\IoT\Du_An\Vending_Machine\Vesion_3\infra
docker compose ps
```

### 11.2. Bật Uno và ESP32

Log mong đợi:

#### Uno

- `[BOOT] UNO Modular ready`

#### ESP32

- kết nối Wi-Fi thành công
- gọi `register-device`
- gửi heartbeat định kỳ
- kết nối MQTT nếu broker đang chạy

Nếu mọi thứ đúng, thiết bị sẽ vào màn hình chờ thao tác.

---

## 12. Kiểm thử lần đầu

### 12.1. Bài test tối thiểu

1. Tạo `Machine`
2. Tạo `DeviceIdentity`
3. Tạo `Product`
4. Tạo `Slot A1`
5. Nạp `secret_key` đúng vào `DEVICE_MACHINE_KEY`
6. Boot máy
7. Nhập `1` trên keypad

Kết quả mong đợi:

- firmware map `1 -> A1`
- backend tạo order theo `slot_code = A1`
- nếu thanh toán đủ, máy nhả hàng

### 12.2. Test QR

Điều kiện:

- `PAYOS_CLIENT_ID`
- `PAYOS_API_KEY`
- `PAYOS_CHECKSUM_KEY`

phải đúng.

Kết quả mong đợi:

- tạo QR thành công
- thanh toán xong thì backend cập nhật trạng thái
- ESP32 chuyển sang nhả hàng

### 12.3. Test tiền mặt

Kết quả mong đợi:

- Uno phát hiện tiền
- ESP32 report mệnh giá lên backend
- nếu thanh toán đủ tiền thì nhả hàng

---

## 13. Troubleshooting

### 13.1. Docker báo container name conflict

Ví dụ:

- `vending-mqtt is already in use`

Khắc phục:

```powershell
cd E:\IoT\Du_An\Vending_Machine\Vesion_3\infra
docker compose down -v --remove-orphans
docker rm -f vending-mqtt vending-db vending-backend vending-nginx 2>$null
docker compose up -d --build
```

### 13.2. ESP32 báo sai machine key

Triệu chứng:

- backend trả `403`
- log có `Invalid machine key`

Kiểm tra:

- `DEVICE_MACHINE_KEY` trong `secrets.h`
- `secret_key` của `Machine` trong admin

Hai giá trị này phải giống hệt nhau.

### 13.3. Backend báo machine chưa được provision

Thông báo thường gặp:

- `Machine X is not provisioned`

Khắc phục:

- tạo `Machine` trước trong admin

### 13.4. Backend báo device identity chưa được provision

Thông báo thường gặp:

- `Device identity for machine X is not provisioned`

Khắc phục:

- gọi `POST /api/devices/identity` trước khi boot ESP32

### 13.5. ESP32 không gọi được backend dù Docker vẫn chạy

Nguyên nhân hay gặp:

- dùng `localhost` trong `API_BASE_URL`
- dùng `backend` làm hostname trong firmware
- Windows Firewall chặn kết nối từ mạng nội bộ

Khắc phục:

- đổi `API_BASE_URL` sang IP LAN thật của máy chạy Docker
- kiểm tra firewall cho port `5000`

### 13.6. MQTT không hoạt động

Kiểm tra:

- `MQTT_BROKER` có đúng IP LAN không
- port `1883` có mở không
- `kMqttCommandTopic` có đúng machine đang chạy không

### 13.7. Dữ liệu admin bị mất sau khi khởi động lại

Chỉ xảy ra khi bạn đã chạy:

```powershell
docker compose down -v
```

Đây là hành vi đúng vì lệnh đó xóa volume DB.

### 13.8. DB cũ gây lỗi schema lạ

Do backend hiện chưa có migration tự động.

Khắc phục an toàn nhất:

```powershell
docker compose down -v --remove-orphans
docker compose up -d --build
```

### 13.9. Keypad nhập số nhưng không ra đúng khe

Kiểm tra:

- `slot_code` trong admin có theo chuẩn `A1`, `A2`, `B1`...
- firmware có đúng mapping keypad không

Nếu admin đặt `slot_code` kiểu khác, keypad sẽ không khớp.

---

## 14. Checklist triển khai máy mới

Khi lắp một máy mới từ đầu, chỉ cần đi theo checklist này:

1. Chạy Docker trong thư mục `infra/`
2. Tạo tài khoản admin đầu tiên
3. Tạo `Machine`
4. Ghi lại `secret_key`
5. Tạo `DeviceIdentity`
6. Tạo `Product`
7. Tạo `Slot`
8. Sửa `firmware/esp32/include/secrets.h`
9. Kiểm tra `firmware/esp32/include/app_config.h`
10. Kiểm tra `firmware/uno/include/pins.h`
11. Nạp Uno
12. Nạp ESP32
13. Cấp nguồn và mở Serial Monitor
14. Test tạo order, thanh toán, nhả hàng

---

## 15. Ghi chú vận hành

- Admin có thể tạo động `Machine`, `Product`, `Slot`
- `DeviceIdentity` hiện nên provision bằng API
- `secret_key` là dữ liệu quản trị quan trọng, cần lưu an toàn
- Với repo hiện tại, một số giá trị MQTT/ID máy vẫn còn nằm trong firmware, chưa kéo động hoàn toàn từ DB

Nếu cần, bạn có thể bổ sung tiếp một tài liệu riêng cho:

- quy trình tạo nhiều máy cùng lúc
- checklist test phần cứng trước khi giao máy
- checklist bảo trì định kỳ
