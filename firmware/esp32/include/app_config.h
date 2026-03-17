#pragma once

namespace esp32cfg {

static constexpr uint8_t kUartRxPin = 16;
static constexpr uint8_t kUartTxPin = 17;

static constexpr uint8_t kTftMosiPin = 23;
static constexpr uint8_t kTftSckPin = 18;
static constexpr uint8_t kTftCsPin = 5;
static constexpr uint8_t kTftDcPin = 27;
static constexpr uint8_t kTftResetPin = 26;
static constexpr int8_t kTftBacklightPin = 25;

static constexpr uint32_t kBackendPollIntervalMs = 5000;
static constexpr uint32_t kHeartbeatIntervalMs = 15000;
static constexpr uint32_t kPaymentPollIntervalMs = 3000;
static constexpr uint32_t kPaymentSessionTimeoutMs = 300000;
static constexpr bool kEnableRemoteDispense = true;

static constexpr char kMachineId[] = "VM-03";
static constexpr char kMachineKey[] = "maybanhang-v3";

// Network parameters are defined in secrets.h
static constexpr uint16_t kMqttPort = 1883;
static constexpr char kMqttCommandTopic[] = "vending/v3/machine/3/cmd";
static constexpr char kMqttStatusTopic[] = "vending/v3/status";

static constexpr char kDefaultBuyerName[] = "Vending Customer";
static constexpr char kDefaultBuyerPhone[] = "0900000000";
static constexpr char kDefaultBuyerEmail[] = "customer@example.com";

static constexpr char kDefaultSlotCode[] = "A1";
static constexpr uint8_t kDefaultQuantity = 1;

}  // namespace esp32cfg
