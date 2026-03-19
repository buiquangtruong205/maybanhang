#pragma once

namespace esp32cfg {

static constexpr uint8_t kUartRxPin = 16;
static constexpr uint8_t kUartTxPin = 17;

static constexpr uint8_t kTftMosiPin = 23;
static constexpr uint8_t kTftSckPin = 18;
static constexpr uint8_t kTftCsPin = 5;
static constexpr uint8_t kTftDcPin = 2;
static constexpr uint8_t kTftResetPin = 4;
static constexpr int8_t kTftBacklightPin = 15;

// Keypad Pins
static constexpr uint8_t kKeypadRow1 = 13;
static constexpr uint8_t kKeypadRow2 = 12;
static constexpr uint8_t kKeypadRow3 = 14;
static constexpr uint8_t kKeypadRow4 = 27;
static constexpr uint8_t kKeypadCol1 = 26;
static constexpr uint8_t kKeypadCol2 = 25;
static constexpr uint8_t kKeypadCol3 = 33;
static constexpr uint8_t kBootButtonPin = 0;
static constexpr uint32_t kBootResetHoldMs = 4000;

static constexpr uint32_t kBackendPollIntervalMs = 5000;
static constexpr uint32_t kHeartbeatIntervalMs = 15000;
static constexpr uint32_t kPaymentPollIntervalMs = 3000;
static constexpr uint32_t kPaymentSessionTimeoutMs = 300000;
static constexpr bool kEnableRemoteDispense = true;

// machine_id is synced dynamically from backend after register-device/heartbeat.
static constexpr char kMachineId[] = "";

// Network parameters are defined in secrets.h
static constexpr uint16_t kMqttPort = 1883;

static constexpr char kDefaultBuyerName[] = "Vending Customer";
static constexpr char kDefaultBuyerPhone[] = "0900000000";
static constexpr char kDefaultBuyerEmail[] = "customer@example.com";

static constexpr char kDefaultSlotCode[] = "A1";
static constexpr uint8_t kDefaultQuantity = 1;

}  // namespace esp32cfg
