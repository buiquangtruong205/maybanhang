# Máy Bán Hàng Tự Động V3

Repository này chứa toàn bộ mã nguồn và tài liệu cho hệ thống máy bán hàng tự động V3.

## Thành phần chính

- `backend/`
  API Flask, dashboard admin, WebSocket, PayOS, MQTT, WebAuthn và các route cho thiết bị IoT.
- `CLIENT_machine/`
  Giao diện web phía máy bán hàng, viết bằng HTML/CSS/JavaScript thuần.
- `firmware/`
  Firmware cho ESP32 và Arduino Uno, kèm phần giao thức dùng chung.
- `hardware/`
  Tài liệu đấu nối và ánh xạ chân phần cứng.
- `docs/`
  Tài liệu setup, API, cơ sở dữ liệu, bảo mật và poster.
- `infra/`
  Docker Compose, Nginx, file môi trường mẫu và cấu hình deploy.
- `mosquitto/`
  Thư mục cấu hình, dữ liệu và log cho MQTT broker local.

## Cấu trúc thư mục

```text
Vesion_3/
  backend/
  CLIENT_machine/
  docs/
  firmware/
  hardware/
  infra/
  mosquitto/
  README.md
```

## Chạy backend

```powershell
cd backend
pip install -r requirements.txt
python run.py
```

## Chạy giao diện máy bán hàng

Mở [CLIENT_machine/index.html](E:\IoT\Du_An\Vending_Machine\Vesion_3\CLIENT_machine\index.html) trực tiếp hoặc phục vụ qua web server tĩnh.

## Build firmware

### ESP32

```powershell
cd firmware\esp32
.\build.ps1
.\upload.ps1 --upload-port COM5
```

### UNO

```powershell
cd firmware\uno
$env:PLATFORMIO_CORE_DIR='E:\IoT\Du_An\Vending_Machine\Vesion_3\firmware\.platformio-local'
pio run -e uno -t upload --upload-port COM4
```

## Tài liệu liên quan

- [docs/README.md](E:\IoT\Du_An\Vending_Machine\Vesion_3\docs\README.md)
- [hardware/README.md](E:\IoT\Du_An\Vending_Machine\Vesion_3\hardware\README.md)
- [firmware/README.md](E:\IoT\Du_An\Vending_Machine\Vesion_3\firmware\README.md)
- [CLIENT_machine/README.md](E:\IoT\Du_An\Vending_Machine\Vesion_3\CLIENT_machine\README.md)
- [infra/huong_dan_docker.md](E:\IoT\Du_An\Vending_Machine\Vesion_3\infra\huong_dan_docker.md)

## Ghi chú

- `f3/` là short-path workspace dùng để build ESP32 ổn định trên Windows.
- Artefact build của PlatformIO có thể được tạo lại sau khi build.
