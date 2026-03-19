# Hardware Test Checklist

Tài liệu này dùng để test nhanh phần cứng sau khi nạp firmware cho `UNO` và `ESP32`.

## Mục tiêu

- Xác nhận `UNO` và `ESP32` khởi động đúng
- Xác nhận giao tiếp UART giữa hai board
- Xác nhận motor, servo, cảm biến rơi hoạt động đúng
- Xác nhận bill acceptor được đọc đúng
- Xác nhận `ESP32` vào được Wi‑Fi và MQTT

## Chuẩn bị

- Nạp firmware mới nhất cho:
  - `firmware/uno`
  - `firmware/esp32`
- Mở Serial Monitor hoặc terminal cho:
  - `UNO`
  - `ESP32`
- Cấu hình tốc độ baud đúng theo firmware hiện tại
- Đảm bảo đã đấu dây đầy đủ:
  - UART `ESP32 <-> UNO`
  - motor
  - servo gate
  - drop sensor
  - bill acceptor
  - Wi‑Fi antenna / nguồn ổn định

## Lệnh test trực tiếp

### UNO

Gõ trực tiếp trong Serial Monitor của `UNO`:

```text
HELP
STATUS
PING
DISPENSE A1
TEST MOTOR
TEST SERVO
```

### ESP32

Gõ trực tiếp trong USB console của `ESP32`:

```text
HELP
STATUS
PINGUNO
MOTOR A1
SERVO
DISPENSE A1
CASH 10000
PAY A1
IDLE
SETKEY <machine_key>
```

## Checklist 1: Boot Log

### UNO

Kỳ vọng:

- Có log boot cho biết firmware đã chạy
- Có dòng gợi ý command test:

```text
[UNO TEST] Type HELP for direct bench commands
```

- Có log init phần cứng kiểu:

```text
[HW] Init complete | drop_sensor=... led=... servo=...
[GATE] Servo attached on pin ..., state=CLOSED
```

Nếu lỗi:

- Không có log nào: kiểm tra cổng COM, baud rate, nguồn
- Servo giật bất thường ngay lúc boot: kiểm tra nguồn servo và mass chung

### ESP32

Kỳ vọng:

- Có log console sẵn sàng:

```text
[USB] Console ready. Type HELP for commands.
```

- Có log config, Wi‑Fi, MQTT, UART

Nếu lỗi:

- Không có log: kiểm tra cáp USB, driver, baud rate

## Checklist 2: UART ESP32 <-> UNO

Thực hiện trên `ESP32`:

```text
PINGUNO
```

Kỳ vọng:

- `ESP32` gửi frame UART
- `UNO` nhận `CMD:PING:`
- `UNO` trả `EVT:PONG:UNO`
- `ESP32` nhận lại `PONG`

Log mong đợi:

```text
[UNO UART] TX -> CMD:PING:
[SERIAL] RX protocol PING
[SERIAL] TX EVT:PONG:UNO
[UNO EVT] PONG | UNO
```

Nếu lỗi:

- Không có phản hồi: kiểm tra chéo dây TX/RX
- Có phản hồi rác: kiểm tra baud rate UART giữa hai board
- Chỉ một chiều hoạt động: kiểm tra mass chung

## Checklist 3: Motor

### Test từ UNO

Gõ:

```text
TEST MOTOR
```

Kỳ vọng:

- Motor quay thuận
- dừng ngắn
- quay ngược
- `UNO` gửi ACK hoàn tất

### Test từ ESP32

Gõ:

```text
MOTOR A1
```

Kỳ vọng:

- `ESP32` gửi lệnh `TEST_MOTOR`
- `UNO` log nhận lệnh
- Motor chạy

Log mong đợi:

```text
[SERIAL] RX direct TEST MOTOR: standard|TEST
[MOTOR] TEST_MOTOR payload: ...
EVT:ACK:TEST_MOTOR_DONE
```

Nếu lỗi:

- Motor không quay: kiểm tra driver motor, nguồn motor, dây coil
- Motor rung nhưng không quay: sai thứ tự coil hoặc dòng không đủ
- Quay sai chiều: kiểm tra mapping dây hoặc logic direction

## Checklist 4: Servo Gate

### Test từ UNO

Gõ:

```text
TEST SERVO
```

### Test từ ESP32

Gõ:

```text
SERVO
```

Kỳ vọng:

- Gate mở
- sau timeout gate tự đóng

Log mong đợi:

```text
[GATE] Opening gate
[GATE] Closing gate
EVT:ACK:TEST_SERVO_STARTED
```

Nếu lỗi:

- Servo không quay: kiểm tra nguồn 5V riêng cho servo
- Servo quay nhưng reset board: nguồn không đủ, nhiễu nguồn
- Servo mở nhưng không đóng: kiểm tra `update()` có đang chạy đều không

## Checklist 5: Sensor Rơi

Thực hiện:

- Gõ `STATUS` trên `UNO`
- tác động tay vào cảm biến rơi
- gõ `STATUS` lại
- sau đó test:

```text
DISPENSE A1
```

Kỳ vọng:

- Trạng thái `drop` đổi giữa `HIGH/LOW`
- Khi nhả hàng, có log debounce và phát hiện drop sensor

Log mong đợi:

```text
[HW STATUS] drop=HIGH ...
[HW STATUS] drop=LOW ...
```

Nếu lỗi:

- Trạng thái luôn `HIGH`: kiểm tra wiring cảm biến, pull-up, module sensor
- Trạng thái luôn `LOW`: chạm mass hoặc cảm biến đang active liên tục
- Có tín hiệu nhưng dispense không kết thúc đúng: kiểm tra debounce và cơ khí khe rơi

## Checklist 6: Bill Acceptor

Thực hiện:

- Bật hệ thống ở trạng thái sẵn sàng
- đưa tờ tiền đúng loại qua bill acceptor
- quan sát log trên `UNO` và `ESP32`

Kỳ vọng:

- `UNO` đọc được màu/tín hiệu bill
- gate xử lý đúng
- `UNO` phát event:

```text
EVT:CASH_INSERTED:10000
```

- `ESP32` nhận được sự kiện tiền mặt nếu UART đang chạy bình thường

Log mong đợi:

```text
[BILL] 10k detected | R=... G=... B=...
EVT:CASH_INSERTED:10000
```

Nếu lỗi:

- Không có log detect: kiểm tra dây tín hiệu từ bill acceptor
- Detect chập chờn: kiểm tra nhiễu nguồn, ngưỡng cảm biến, thời gian debounce
- Nhận sai mệnh giá: cần hiệu chuẩn lại logic nhận dạng

## Checklist 7: Wi‑Fi

Thực hiện trên `ESP32`:

- khởi động board
- quan sát log kết nối Wi‑Fi

Kỳ vọng:

- in ra SSID đang dùng
- kết nối thành công
- có IP

Log mong đợi:

```text
[WIFI] Config loaded ...
[WIFI] Connected to <ssid>
[WIFI] IP: <ip>
```

Nếu lỗi:

- không kết nối được: kiểm tra `secrets.h`, SSID, password
- reset liên tục khi kết nối: kiểm tra nguồn cấp cho ESP32

## Checklist 8: MQTT

Thực hiện trên `ESP32`:

- sau khi có Wi‑Fi, chờ MQTT connect
- kiểm tra log subscribe topic
- nếu có broker test, publish lệnh điều khiển tới đúng topic máy

Kỳ vọng:

- kết nối broker thành công
- subscribe đúng topic command
- publish status thành công

Log mong đợi:

```text
[MQTT] Subscribed: ...
[MQTT] Publish status: ...
[MQTT CMD] ...
```

Nếu lỗi:

- không connect broker: kiểm tra IP broker, port, username/password
- connect được nhưng không nhận lệnh: kiểm tra topic subscribe
- nhận lệnh nhưng không chạy: kiểm tra chuỗi xử lý `MQTT -> controller -> UNO`

## Checklist 9: Luồng Nhả Hàng End-to-End

Thực hiện trên `ESP32`:

```text
DISPENSE A1
```

Kỳ vọng:

- `ESP32` gửi lệnh xuống `UNO`
- `UNO` quay motor
- cảm biến rơi đổi trạng thái nếu có sản phẩm đi qua
- `UNO` phản hồi event tương ứng
- `ESP32` log lại event từ `UNO`

Nếu lỗi:

- `ESP32` có log nhưng `UNO` im lặng: lỗi UART
- `UNO` có log nhận lệnh nhưng motor không chạy: lỗi tầng driver/hardware
- motor chạy nhưng không có xác nhận rơi: lỗi cảm biến rơi hoặc cơ khí

## Mẫu chạy test nhanh đề xuất

Thứ tự nên test:

1. Boot log `UNO`
2. Boot log `ESP32`
3. `PINGUNO`
4. `STATUS`
5. `TEST SERVO` hoặc `SERVO`
6. `TEST MOTOR` hoặc `MOTOR A1`
7. test cảm biến rơi bằng `DISPENSE A1`
8. test bill acceptor bằng tiền thật hoặc tín hiệu mô phỏng
9. xác nhận Wi‑Fi
10. xác nhận MQTT

## Ghi chú

- Nếu test từng khối riêng, ưu tiên test `UNO` độc lập trước rồi mới ghép với `ESP32`
- Khi test motor/servo, nên dùng nguồn ngoài ổn định thay vì chỉ lấy từ cổng USB
- Nếu log quá nhiều, tập trung 3 nhóm trước:
  - `[SERIAL]` hoặc `[UNO UART]`
  - `[GATE]`, `[MOTOR]`, `[BILL]`, `[HW STATUS]`
  - `[WIFI]`, `[MQTT]`, `[UNO EVT]`
