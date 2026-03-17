# Vending Machine Firmware V3

Firmware is organized as separate PlatformIO projects.

- `esp32`: ESP32-WROOM main controller for Wi-Fi, MQTT/API, and vending logic
- `uno`: Arduino Uno I/O controller for relays, sensors, locks, and low-level peripherals
- `shared`: communication contract between the two boards

## Structure

```text
firmware/
  esp32/
    src/
    include/
    lib/
    platformio.ini
  uno/
    src/
    include/
    lib/
    platformio.ini
  shared/
    protocol.h
```

## Build

```powershell
cd esp32
.\build.ps1

cd ..\uno
pio run
```

## Notes

- On this Windows machine, raw `pio run` for `esp32` can intermittently fail with `xtensa-esp32-elf-g++: CreateProcess`.
- The stable workaround is to build through a short mirrored path created under `E:\IoT\Du_An\Vending_Machine\f3`.
- Use `esp32\build.ps1` and `esp32\upload.ps1` so PlatformIO automatically switches to the short path and local core directory.

## Bench Test Checklist

Use two serial monitors when possible:

- `ESP32`: monitor payment flow, backend sync, Wi-Fi state
- `UNO`: monitor motor state, drop sensor, door sensor

### 1. Pre-check

- Verify `firmware/esp32/include/secrets.h` contains the correct Wi-Fi and backend IP
- Verify `firmware/esp32/include/app_config.h` matches the actual TFT and UART wiring
- Power ESP32 and UNO from a stable supply; do not power the stepper directly from the Uno USB rail
- Confirm UNO sends `EVT:READY:UNO_V3` at boot

### 2. Communication test

- Wait for ESP32 log showing Wi-Fi connected and device registration attempt
- Confirm ESP32 prints periodic `[COMM] Pinging Uno...`
- Confirm ESP32 receives `[COMM] Uno Connection: OK (PONG received)`

### 3. Online payment test

- Open ESP32 serial monitor
- Send `PAY` or `PAY A1`
- Confirm ESP32 logs:
  - `[STATE] PAYMENT_BEGIN`
  - `[ORDER] created ...`
  - `[PAYMENT] order=... payment_code=...`
- Confirm TFT displays QR code

### 4. Payment success test

- Complete payment using the displayed QR
- Confirm ESP32 logs payment status changing to `PAID` or `SUCCESS`
- Confirm ESP32 logs `[STATE] DISPENSE_START`
- Confirm UNO logs:
  - `[DISPENSE] Start slot payload: ...`
  - `[DISPENSE] Motor movement completed`
- Trigger the drop sensor
- Confirm UNO logs `[SENSOR] Drop detected during dispense`
- Confirm ESP32 logs backend report for dispense result

### 5. Payment failure / timeout test

- Start a payment and do not pay
- Wait for timeout or cancel the payment
- Confirm ESP32 leaves the QR screen and shows payment failed
- Confirm no `DISPENSE` command is sent to UNO

### 6. Dispense failure test

- Start a paid order
- Let the motor finish without triggering the drop sensor
- Confirm UNO logs `[DISPENSE] Drop timeout`
- Confirm ESP32 logs payment failed due to dispense failure
- Confirm backend receives `dispense-complete` with `success=false`

### 7. Wi-Fi reconnect test

- Boot ESP32 with Wi-Fi off
- Turn Wi-Fi on afterward
- Confirm ESP32 reconnects, re-registers the device, and resumes heartbeat

### Expected serial markers

- ESP32:
  - `[STATE]`
  - `[ORDER]`
  - `[PAYMENT]`
  - `[BACKEND]`
  - `[COMM]`
  - `[WIFI]`
- UNO:
  - `[BOOT]`
  - `[DISPENSE]`
  - `[SENSOR]`
