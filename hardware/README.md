# Phần Cứng

Thư mục này chứa tài liệu phần cứng của hệ thống máy bán hàng tự động V3.

## Nội dung hiện có

- [pin_mapping.md](E:\IoT\Du_An\Vending_Machine\Vesion_3\hardware\pin_mapping.md)
  Tài liệu ánh xạ chân giữa ESP32, Arduino Uno và các ngoại vi chính.

## Mục đích

- Làm tài liệu tham chiếu khi đấu nối ESP32, Uno, TFT, keypad, cảm biến và cơ cấu chấp hành.
- Giữ đồng bộ giữa phần cứng thực tế và cấu hình trong firmware.

## Khi thay đổi phần cứng

Cần cập nhật đồng thời:

- [pin_mapping.md](E:\IoT\Du_An\Vending_Machine\Vesion_3\hardware\pin_mapping.md)
- [firmware/esp32/include/app_config.h](E:\IoT\Du_An\Vending_Machine\Vesion_3\firmware\esp32\include\app_config.h)
- [firmware/uno/include/pins.h](E:\IoT\Du_An\Vending_Machine\Vesion_3\firmware\uno\include\pins.h)

## Lưu ý

- Không cấp nguồn tải động cơ trực tiếp từ cổng USB của MCU.
- Nên kiểm tra mass chung giữa ESP32, Uno và nguồn ngoại vi trước khi test UART hoặc sensor.
