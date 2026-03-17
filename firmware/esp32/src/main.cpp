#include <Arduino.h>

#include "api_client.h"
#include "app_config.h"
#include "display_ui.h"
#include "mqtt_manager.h"
#include "uno_comm.h"
#include "usb_console.h"
#include "wifi_manager.h"

namespace {

uint32_t lastHeartbeatAt = 0;
uint32_t lastPaymentPollAt = 0;
uint32_t lastBackendPollAt = 0;
uint32_t lastUnoPingAt = 0;
uint32_t paymentStartedAt = 0;
bool deviceRegistered = false;
bool lastWifiConnected = false;

constexpr uint32_t kUnoPingIntervalMs = 10000;

int currentOrderId = 0;
int currentPaymentCode = 0;
bool waitingForPayment = false;
bool dispensingInProgress = false;
String currentSlotCode = esp32cfg::kDefaultSlotCode;
String currentAmountText;

void logState(const String& tag, const String& detail) {
    Serial.printf("[STATE] %s | %s | order=%d payment=%d slot=%s waiting=%d dispensing=%d\n",
                  tag.c_str(),
                  detail.c_str(),
                  currentOrderId,
                  currentPaymentCode,
                  currentSlotCode.c_str(),
                  waitingForPayment,
                  dispensingInProgress);
}

void resetPaymentState() {
    currentOrderId = 0;
    currentPaymentCode = 0;
    paymentStartedAt = 0;
    waitingForPayment = false;
    dispensingInProgress = false;
}

void finalizeSuccess() {
    logState("SUCCESS", "Dispense synced to backend");
    displayui::showPaymentResult("PAYMENT SUCCESS", "Complete", true);
    resetPaymentState();
    delay(2500);
    displayui::showIdle();
}

void finalizeFailure(const String& detail) {
    logState("FAILURE", detail);
    displayui::showPaymentResult("PAYMENT FAILED", detail, false);
    resetPaymentState();
    delay(2500);
    displayui::showIdle();
}

void startDispenseFlow() {
    logState("DISPENSE_START", "Payment confirmed, command sent to UNO");
    displayui::showPaymentResult("PAYMENT SUCCESS", "Dispensing...", true);
    waitingForPayment = false;
    dispensingInProgress = true;
    uno_comm::sendCommand(protocol::CommandType::Dispense, currentSlotCode);
}

bool splitUnoFrame(const String& frame, String& eventName, String& payload) {
    if (!frame.startsWith("EVT:")) {
        return false;
    }

    const int separator = frame.indexOf(':', 4);
    if (separator < 0) {
        eventName = frame.substring(4);
        payload = "";
        return true;
    }

    eventName = frame.substring(4, separator);
    payload = frame.substring(separator + 1);
    return true;
}

void finalizeDispenseResult(bool success, const String& detail) {
    if (currentOrderId <= 0) {
        displayui::showError("DISPENSE STATE", "Missing order id");
        resetPaymentState();
        return;
    }

    Serial.printf("[BACKEND] Reporting dispense result success=%d detail=%s\n", success, detail.c_str());
    if (!api_client::reportDispenseResult(currentOrderId, currentSlotCode, success, detail)) {
        displayui::showError("BACKEND ERROR", "Dispense sync failed");
        return;
    }

    if (success) {
        finalizeSuccess();
    } else {
        finalizeFailure(detail);
    }
}

void pollPaymentStatus() {
    if (!waitingForPayment || currentPaymentCode <= 0) {
        return;
    }

    if (paymentStartedAt > 0 && millis() - paymentStartedAt >= esp32cfg::kPaymentSessionTimeoutMs) {
        finalizeFailure("Payment timeout");
        return;
    }

    api_client::PaymentStatus status;
    if (!api_client::getPaymentStatus(currentPaymentCode, status)) {
        return;
    }

    Serial.printf("[PAYMENT] status=%s amount_paid=%d remaining=%d\n",
                  status.status.c_str(),
                  status.amountPaid,
                  status.amountRemaining);

    const bool isPaid =
        status.status.equalsIgnoreCase("PAID") ||
        status.status.equalsIgnoreCase("SUCCESS") ||
        status.status.equalsIgnoreCase("COMPLETED") ||
        (status.amountPaid > 0 && status.amountRemaining == 0);

    const bool isFailed =
        status.status.equalsIgnoreCase("FAILED") ||
        status.status.equalsIgnoreCase("CANCELLED") ||
        status.status.equalsIgnoreCase("CANCELED") ||
        status.status.equalsIgnoreCase("EXPIRED");

    if (isPaid) {
        startDispenseFlow();
        return;
    }

    if (isFailed) {
        finalizeFailure(status.status);
    }
}

void processPendingOrders() {
    if (waitingForPayment || dispensingInProgress) {
        return;
    }

    JsonDocument doc;
    if (!api_client::fetchPendingOrders(doc)) {
        return;
    }

    JsonArray orders = doc["data"].as<JsonArray>();
    if (orders.size() == 0) {
        return;
    }

    // Process first pending order
    JsonObject order = orders[0];
    int orderId = order["order_id"];
    String slotCode = order["slot_code"] | esp32cfg::kDefaultSlotCode;

    Serial.printf("[POLL] Found pending order %d for slot %s\n", orderId, slotCode.c_str());
    
    currentOrderId = orderId;
    currentSlotCode = slotCode;
    startDispenseFlow();
}

void ensureBackendSession() {
    if (!wifi_manager::isConnected()) {
        return;
    }

    if (!deviceRegistered) {
        Serial.println("[BACKEND] Registering device...");
        deviceRegistered = api_client::registerDevice();
        if (deviceRegistered) {
            Serial.println("[BACKEND] Device registered");
            api_client::sendHeartbeat();
        } else {
            Serial.println("[BACKEND] Device registration failed");
        }
    }
}

void startOnlinePaymentForSlot(const String& slotCode) {
    if (!wifi_manager::isConnected()) {
        displayui::showError("NO WIFI", "Cannot start payment");
        return;
    }

    if (waitingForPayment || dispensingInProgress) {
        displayui::showError("BUSY", "Finish current order");
        return;
    }

    currentSlotCode = slotCode;
    logState("PAYMENT_BEGIN", "Creating order");
    displayui::showLoading("Creating order", slotCode);

    api_client::OrderInfo order;
    if (!api_client::createOrder(slotCode, order)) {
        displayui::showError("ORDER ERROR", "Create order failed");
        return;
    }

    Serial.printf("[ORDER] created id=%d product=%s amount=%d\n",
                  order.id,
                  order.productName.c_str(),
                  order.amount);

    displayui::showLoading("Creating QR", order.productName);

    int paymentCode = 0;
    String qrPayload;
    if (!api_client::createPayment(order.id, order.productName, order.amount, paymentCode, qrPayload)) {
        displayui::showError("PAYMENT ERROR", "Create QR failed");
        return;
    }

    currentOrderId = order.id;
    currentPaymentCode = paymentCode;
    waitingForPayment = true;
    dispensingInProgress = false;
    paymentStartedAt = millis();
    currentAmountText = String(order.amount) + " VND";

    displayui::showPaymentQr(String(order.id), currentAmountText, qrPayload);

    Serial.printf("[PAYMENT] order=%d payment_code=%d slot=%s\n",
                  currentOrderId, currentPaymentCode, currentSlotCode.c_str());
    Serial.printf("[PAYMENT] QR payload length=%u\n", qrPayload.length());
}

void handleUnoEvent(const String& frame) {
    String eventName;
    String payload;

    if (!splitUnoFrame(frame, eventName, payload)) {
        Serial.print("[UNO] ");
        Serial.println(frame);
        return;
    }

    if (eventName == "PONG") {
        Serial.println("[COMM] Uno Connection: OK (PONG received)");
        return;
    }

    if (eventName == "READY") {
        Serial.printf("[COMM] Uno ready: %s\n", payload.c_str());
        return;
    }

    if (eventName == "ACK") {
        Serial.printf("[COMM] Uno ACK: %s\n", payload.c_str());
        return;
    }

    Serial.print("[UNO] ");
    Serial.println(frame);

    if (eventName == "DISPENSE_OK" && dispensingInProgress) {
        Serial.println("[COMM] UNO confirmed dispense success");
        finalizeDispenseResult(true, payload.length() > 0 ? payload : "Dispensed successfully");
        return;
    }

    if (eventName == "DISPENSE_FAIL" && dispensingInProgress) {
        Serial.println("[COMM] UNO reported dispense failure");
        finalizeDispenseResult(false, payload.length() > 0 ? payload : "Dispense failed");
        return;
    }

    if (eventName == "ERROR" && dispensingInProgress) {
        Serial.println("[COMM] UNO reported error during dispense");
        finalizeDispenseResult(false, payload.length() > 0 ? payload : "UNO error");
    }
}

void handleMqttCommand(const String& cmd, const String& val) {
    if (!esp32cfg::kEnableRemoteDispense) {
        return;
    }

    if (!cmd.equalsIgnoreCase("DISPENSE")) {
        return;
    }

    if (waitingForPayment || dispensingInProgress) {
        Serial.println("[MQTT] Ignored remote dispense while busy");
        return;
    }

    Serial.printf("[MQTT] Remote dispense: %s\n", val.c_str());
    uno_comm::sendCommand(protocol::CommandType::Dispense, val);
}

void handleConsoleCommand(const String& cmdRaw) {
    String command = cmdRaw;
    command.toUpperCase();

    if (command.equalsIgnoreCase("PING")) {
        Serial.println("PONG");
    } else if (command.equalsIgnoreCase("UNO PING")) {
        Serial.println("[COMM] Send PING to Uno");
        uno_comm::sendCommand(protocol::CommandType::Ping, "ESP32");
    } else if (command.equalsIgnoreCase("UNO TEST")) {
        Serial.println("[COMM] Send TEST_MOTOR to Uno");
        uno_comm::sendCommand(protocol::CommandType::TestMotor, "LOCAL_TEST");
    } else if (command.equalsIgnoreCase("DISPENSE")) {
        Serial.printf("[COMM] Send DISPENSE to Uno: %s\n", esp32cfg::kDefaultSlotCode);
        uno_comm::sendCommand(protocol::CommandType::Dispense, esp32cfg::kDefaultSlotCode);
    } else if (command.startsWith("DISPENSE ")) {
        String slotCode = cmdRaw.substring(9);
        slotCode.trim();
        if (slotCode.length() == 0) {
            slotCode = esp32cfg::kDefaultSlotCode;
        }
        Serial.printf("[COMM] Send DISPENSE to Uno: %s\n", slotCode.c_str());
        uno_comm::sendCommand(protocol::CommandType::Dispense, slotCode);
    } else if (command.equalsIgnoreCase("PAY")) {
        startOnlinePaymentForSlot(esp32cfg::kDefaultSlotCode);
    } else if (command.startsWith("PAY ")) {
        String slotCode = cmdRaw.substring(4);
        slotCode.trim();
        startOnlinePaymentForSlot(slotCode);
    } else if (command.equalsIgnoreCase("IDLE")) {
        resetPaymentState();
        displayui::showIdle();
    } else {
        Serial.printf("Unknown command: '%s'\n", cmdRaw.c_str());
        Serial.println("Commands: PING, UNO PING, UNO TEST, DISPENSE, DISPENSE A1, PAY, PAY A1, IDLE");
    }
}

void handleWifiStateChange(bool connected) {
    if (connected && !lastWifiConnected) {
        Serial.printf("[WIFI] Connected, IP=%s\n", wifi_manager::getLocalIP().toString().c_str());
        deviceRegistered = false;
        displayui::showWifiReady(wifi_manager::getLocalIP());
        delay(1000);
        displayui::showIdle();
    } else if (!connected && lastWifiConnected) {
        Serial.println("[WIFI] Connection lost");
        deviceRegistered = false;
    }

    lastWifiConnected = connected;
}

}  // namespace

void setup() {
    Serial.begin(protocol::kBaudRate);

    displayui::init();
    displayui::showBooting();

    Serial.println("\nESP32 V3 Modular Controller Booting");

    wifi_manager::init();
    uno_comm::init(handleUnoEvent);
    mqtt_manager::init(handleMqttCommand);
    usb_console::init(handleConsoleCommand);
    api_client::init();

    handleWifiStateChange(wifi_manager::isConnected());
    ensureBackendSession();
}

void loop() {
    const uint32_t now = millis();

    wifi_manager::loop();
    handleWifiStateChange(wifi_manager::isConnected());
    uno_comm::loop();
    mqtt_manager::loop();
    usb_console::loop();

    if (wifi_manager::isConnected()) {
        ensureBackendSession();

        if (now - lastHeartbeatAt >= esp32cfg::kHeartbeatIntervalMs) {
            lastHeartbeatAt = now;
            if (!api_client::sendHeartbeat()) {
                deviceRegistered = false;
            }
        }

        if (waitingForPayment && now - lastPaymentPollAt >= esp32cfg::kPaymentPollIntervalMs) {
            lastPaymentPollAt = now;
            pollPaymentStatus();
        }

        if (now - lastBackendPollAt >= esp32cfg::kBackendPollIntervalMs) {
            lastBackendPollAt = now;
            processPendingOrders();
        }
    }

    if (now - lastUnoPingAt >= kUnoPingIntervalMs) {
        lastUnoPingAt = now;
        Serial.println("[COMM] Pinging Uno...");
        uno_comm::sendCommand(protocol::CommandType::Ping, "ESP32");
    }
}
