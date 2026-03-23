# Firmware V3

Firmware được chia thành 2 project PlatformIO riêng:

- `esp32/`
  Bộ điều khiển chính: Wi‑Fi, MQTT, API backend, giao diện TFT, keypad, OTA và điều phối vending flow.
- `uno/`
  Bộ điều khiển I/O: motor, gate servo, bill detector, drop sensor và giao thức UART với ESP32.
- `shared/`
  Phần giao thức dùng chung giữa ESP32 và Uno.

## Cấu trúc

```text
firmware/
  esp32/
    include/
    lib/
    src/
    build.ps1
    upload.ps1
    platformio.ini
  uno/
    include/
    src/
    platformio.ini
  shared/
    protocol.h
  README.md
```

## Kiến trúc

### ESP32

[esp32/src/main.cpp](E:\IoT\Du_An\Vending_Machine\Vesion_3\firmware\esp32\src\main.cpp) hiện chỉ là entrypoint.

Module chính:

- `app_runtime.*`
  Điều phối `setup()` và `loop()`.
- `config_manager.*`
  Lưu và đọc cấu hình từ NVS.
- `display_ui.*`
  Điều khiển giao diện TFT.
- `input_manager.*`
  Đọc keypad.
- `wifi_manager.*`
  Quản lý Wi‑Fi và reconnect.
- `mqtt_manager.*`
  Nhận lệnh và publish trạng thái qua MQTT.
- `uno_comm.*`
  Giao tiếp UART với Uno.
- `usb_console.*`
  Debug command qua serial.
- `api_client.*`
  Gọi backend API.
- `vending_controller.*`
  Business logic của máy bán hàng.
- `ota_manager.*`
  Luồng OTA update.

### UNO

[uno/src/main.cpp](E:\IoT\Du_An\Vending_Machine\Vesion_3\firmware\uno\src\main.cpp) cũng chỉ còn entrypoint.

Module chính:

- `hardware_manager.*`
  Init phần cứng, update bill detector và gate.
- `serial_protocol.*`
  Parse command frame và gửi event frame.
- `dispense_controller.*`
  Điều khiển luồng nhả hàng và kiểm tra drop sensor.
- `motor_controller.*`
  Điều khiển motor.
- `bill_detector.*`
  Nhận diện bill.
- `gate_manager.*`
  Điều khiển servo gate.
- `pins.h`
  Ánh xạ chân.

### Shared

- [shared/protocol.h](E:\IoT\Du_An\Vending_Machine\Vesion_3\firmware\shared\protocol.h)
  Khai báo baud rate, frame terminator và các helper command/event dùng chung.

## Build và upload

### ESP32

Trên máy Windows này nên dùng helper script:

```powershell
cd E:\IoT\Du_An\Vending_Machine\Vesion_3\firmware\esp32
.\build.ps1
.\upload.ps1 --upload-port COM5
```

- đường dẫn gốc khá dài có thể gây lỗi khi biên dịch (ví dụ: lỗi `xtensa-esp32-elf-g++: CreateProcess`)
- Chúng ta dùng **Junction Directory** ở thư mục root để tạo lối tắt xây dựng dự án:
  - `E:\IoT\Du_An\Vending_Machine\vmesp` -> `E:\IoT\Du_An\Vending_Machine\Vesion_3\firmware\esp32`
  - Bạn có thể trực tiếp mở thư mục `vmesp` bằng VSCode và dùng PlatformIO extension để biên dịch mà không bao giờ gặp lỗi đường dẫn rắc rối.
- `build.ps1` có thể vẫn là cách cũ, nhưng VSCode + `vmesp` là cách tốt nhất hiện tại.

### UNO

```powershell
cd E:\IoT\Du_An\Vending_Machine\Vesion_3\firmware\uno
$env:PLATFORMIO_CORE_DIR='E:\IoT\Du_An\Vending_Machine\Vesion_3\firmware\.platformio-local'
pio run -e uno -t upload --upload-port COM4
```

## File cấu hình quan trọng

- [esp32/include/secrets.h](E:\IoT\Du_An\Vending_Machine\Vesion_3\firmware\esp32\include\secrets.h)
  Giá trị mặc định cho Wi‑Fi, API và MQTT fallback.
- [esp32/include/app_config.h](E:\IoT\Du_An\Vending_Machine\Vesion_3\firmware\esp32\include\app_config.h)
  Pin và hằng số runtime của ESP32.
- [uno/include/pins.h](E:\IoT\Du_An\Vending_Machine\Vesion_3\firmware\uno\include\pins.h)
  Pin map của Uno.

## Kiểm tra bench tối thiểu

1. ESP32 boot, kết nối Wi‑Fi và đăng ký device.
2. ESP32 gửi `PING`, Uno trả `PONG`.
3. Tạo payment QR.
4. Payment success dẫn tới `DISPENSE`.
5. Uno phát hiện drop sensor.
6. ESP32 báo kết quả dispense về backend.
