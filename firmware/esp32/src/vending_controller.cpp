#include "vending_controller.h"

#include <ArduinoJson.h>
#include "api_client.h"
#include "app_config.h"
#include "display_ui.h"
#include "uno_comm.h"
#include "wifi_manager.h"
#include "mqtt_manager.h"
#include "ota_manager.h"
#include "protocol.h"
#include "config_manager.h"

namespace vending_controller {

namespace {

// Internal State
uint32_t lastHeartbeatAt = 0;
uint32_t lastPaymentPollAt = 0;
uint32_t lastBackendPollAt = 0;
uint32_t lastUnoPingAt = 0;
uint32_t lastUnoResponseAt = 0;
bool unoAlive = true;
uint32_t paymentStartedAt = 0;
uint32_t dispenseStartedAt = 0;
uint32_t lastDispenseReportRetryAt = 0;
bool deviceRegistered = false;
bool deviceRevoked = false;
bool lastWifiConnected = false;

constexpr uint32_t kUnoPingIntervalMs = 20000;
constexpr uint32_t kDispenseTimeoutMs = 45000; // Increased from 30s to 45s for safety margin
constexpr uint32_t kDispenseReportRetryMs = 10000;

int currentOrderId = 0;
int currentPaymentCode = 0;
bool waitingForPayment = false;
bool dispensingInProgress = false;
String currentSlotCode = esp32cfg::kDefaultSlotCode;
String pendingSlotInput = "";
uint32_t accumulatedCash = 0;
uint32_t currentOrderTotal = 0;
String currentAmountText;
bool transactionHasBackendOrder = false;
bool shouldClearCashOnSuccess = false;
bool hasPendingDispenseReport = false;
int pendingDispenseOrderId = 0;
String pendingDispenseSlotCode;
bool pendingDispenseSuccess = false;
String pendingDispenseMessage;
bool resultScreenActive = false;
uint32_t resultScreenOpenedAt = 0;
const uint32_t kResultScreenTimeoutMs = 15000;

// Order History for Idempotency
constexpr int kHistorySize = 5;
int processedOrderHistory[kHistorySize] = {0, 0, 0, 0, 0};
int historyIndex = 0;

bool isOrderProcessed(int orderId) {
    if (orderId <= 0) return false;
    for (int i = 0; i < kHistorySize; i++) {
        if (processedOrderHistory[i] == orderId) return true;
    }
    return false;
}

void markOrderProcessed(int orderId) {
    if (orderId <= 0) return;
    processedOrderHistory[historyIndex] = orderId;
    historyIndex = (historyIndex + 1) % kHistorySize;
}

void logState(const String& tag, const String& detail) {
    Serial.printf("[STATE] %s | %s | order=%d cash=%u slot=%s waiting=%d disp=%d\n",
                  tag.c_str(), detail.c_str(), currentOrderId, accumulatedCash,
                  currentSlotCode.c_str(), waitingForPayment, dispensingInProgress);
}

void printConsoleHelp() {
    Serial.println("[USB HELP] Commands:");
    Serial.println("  HELP");
    Serial.println("  STATUS");
    Serial.println("  IDLE");
    Serial.println("  PAY");
    Serial.println("  PAY <slot>");
    Serial.println("  DISPENSE <slot>");
    Serial.println("  MOTOR <slot>");
    Serial.println("  SERVO");
    Serial.println("  CASH <amount>");
    Serial.println("  PINGUNO");
    Serial.println("  SETKEY <machine_key>");
}

void printConsoleStatus() {
    Serial.printf("[USB STATUS] wifi=%d mqtt=%d registered=%d waiting=%d dispensing=%d order=%d payment=%d slot=%s cash=%u pendingReport=%d\n",
                  wifi_manager::isConnected(),
                  mqtt_manager::isConnected(),
                  deviceRegistered,
                  waitingForPayment,
                  dispensingInProgress,
                  currentOrderId,
                  currentPaymentCode,
                  currentSlotCode.c_str(),
                  accumulatedCash,
                  hasPendingDispenseReport);

    if (wifi_manager::isConnected()) {
        Serial.printf("[USB STATUS] ip=%s\n", wifi_manager::getLocalIP().toString().c_str());
    }
}

void resetPaymentState() {
    currentOrderId = 0;
    currentPaymentCode = 0;
    paymentStartedAt = 0;
    dispenseStartedAt = 0;
    waitingForPayment = false;
    dispensingInProgress = false;
    transactionHasBackendOrder = false;
    shouldClearCashOnSuccess = false;
    currentOrderTotal = 0;
}

void updateAccumulatedCash(uint32_t amount, bool relative = true) {
    if (relative) accumulatedCash += amount;
    else accumulatedCash = amount;
    config_manager::saveAccumulatedCash(accumulatedCash);
}

void queueDispenseReport(bool success, const String& detail) {
    hasPendingDispenseReport = true;
    pendingDispenseOrderId = currentOrderId;
    pendingDispenseSlotCode = currentSlotCode;
    pendingDispenseSuccess = success;
    pendingDispenseMessage = detail;
    lastDispenseReportRetryAt = 0;
}

bool flushPendingDispenseReport() {
    if (!hasPendingDispenseReport || pendingDispenseOrderId <= 0) {
        return true;
    }

    if (!api_client::reportDispenseResult(
            pendingDispenseOrderId,
            pendingDispenseSlotCode,
            pendingDispenseSuccess,
            pendingDispenseMessage)) {
        return false;
    }

    markOrderProcessed(pendingDispenseOrderId);
    hasPendingDispenseReport = false;
    pendingDispenseOrderId = 0;
    pendingDispenseSlotCode = "";
    pendingDispenseSuccess = false;
    pendingDispenseMessage = "";
    return true;
}

void finalizeSuccess(bool clearCash) {
    logState("SUCCESS", "Order completed");
    
    // Always show result first
    displayui::showPaymentResult("GIAO DICH THANH CONG", "Cam on quy khach!", true);
    
    if (clearCash) {
        if (accumulatedCash >= currentOrderTotal) {
            uint32_t newBalance = accumulatedCash - currentOrderTotal;
            Serial.printf("[VENDING] Transaction success. Subtracting %u from %u. New balance: %u\n", 
                          currentOrderTotal, accumulatedCash, newBalance);
            updateAccumulatedCash(newBalance, false);
        } else {
            Serial.printf("[VENDING] Warning: Cash (%u) < Price (%u). Clearing all cash.\n", accumulatedCash, currentOrderTotal);
            updateAccumulatedCash(0, false);
        }
    } else {
        Serial.println("[VENDING] Note: Not a cash transaction, balance kept.");
    }
    
    resetPaymentState();
    pendingSlotInput = "";
    resultScreenActive = true;
    resultScreenOpenedAt = millis();
}

void finalizeFailure(const String& detail) {
    logState("FAILURE", detail);
    displayui::showPaymentResult("GIAO DICH THAT BAI", detail, false);
    resetPaymentState();
    pendingSlotInput = "";
    resultScreenActive = true;
    resultScreenOpenedAt = millis();
}

void startDispenseFlow() {
    logState("DISPENSE_START", "Command sent to UNO");
    displayui::showLoading("DANG XU LY...", "Vui long cho nhan hang"); 
    waitingForPayment = false;
    dispensingInProgress = true;
    dispenseStartedAt = millis();
    const String dispensePayload = config_manager::getDeviceMode() + "|" + currentSlotCode;
    uno_comm::sendCommand(protocol::CommandType::Dispense, dispensePayload);
    mqtt_manager::publishStatus("dispensing");
}

void finalizeDispenseResult(bool success, const String& detail) {
    // 1. Capture info needed for reporting before reset
    int orderToReport = currentOrderId;
    String slotToReport = currentSlotCode;
    bool hasOrder = transactionHasBackendOrder;
    bool clearCashFlag = shouldClearCashOnSuccess;

    Serial.printf("[VENDING] Finalizing result: %s (Detail: %s) | ClearCash: %d\n", 
                  success ? "SUCCESS" : "FAIL", detail.c_str(), clearCashFlag);

    // 2. Update UI IMMEDIATELY so user isn't stuck waiting for API
    if (success) {
        mqtt_manager::publishStatus("dispense_ok");
        finalizeSuccess(clearCashFlag);
    } else {
        mqtt_manager::publishStatus("dispense_fail");
        finalizeFailure(detail);
    }

    // 3. Post-UI Reporting (Blocking calls happen here)
    if (hasOrder && orderToReport > 0) {
        Serial.println("[API] Reporting dispense result to server...");
        if (!api_client::reportDispenseResult(orderToReport, slotToReport, success, detail)) {
            Serial.printf("[ERROR] API Report failed for order %d. Queuing retry.\n", orderToReport);
            // Manually re-populate needed vars for queue since reset happened
            hasPendingDispenseReport = true;
            pendingDispenseOrderId = orderToReport;
            pendingDispenseSlotCode = slotToReport;
            pendingDispenseSuccess = success;
            pendingDispenseMessage = detail;
        } else {
            Serial.println("[API] Report successful.");
            markOrderProcessed(orderToReport);
        }
    }
}

void pollPaymentStatus() {
    if (!waitingForPayment || currentPaymentCode <= 0) return;

    if (paymentStartedAt > 0 && millis() - paymentStartedAt >= esp32cfg::kPaymentSessionTimeoutMs) {
        finalizeFailure("Het thoi gian");
        return;
    }

    api_client::PaymentStatus status;
    if (!api_client::getPaymentStatus(currentPaymentCode, status)) return;

    bool isPaid = status.status.equalsIgnoreCase("PAID") || 
                  status.status.equalsIgnoreCase("SUCCESS") || 
                  status.status.equalsIgnoreCase("COMPLETED") ||
                  (status.amountPaid > 0 && status.amountRemaining == 0);

    if (isPaid) {
        startDispenseFlow();
    } else if (status.status.equalsIgnoreCase("CANCELLED") || 
               status.status.equalsIgnoreCase("CANCELED") || 
               status.status.equalsIgnoreCase("EXPIRED") ||
               status.status.equalsIgnoreCase("FAILED")) {
        finalizeFailure(status.status);
    }
}

void processPendingOrders() {
    // Chỉ chặn nếu đang thực sự nhả hàng hoặc đang bận báo cáo kết quả
    if (dispensingInProgress || hasPendingDispenseReport) return;

    JsonDocument doc;
    if (!api_client::fetchPendingOrders(doc)) return;

    JsonArray orders = doc["data"].as<JsonArray>();
    if (orders.size() == 0) return;

    JsonObject order = orders[0];
    int orderId = order["order_id"];
    
    if (isOrderProcessed(orderId)) {
        // Serial.printf("[POLL] Order %d already processed, skipping\n", orderId);
        return;
    }

    currentOrderId = orderId;
    currentSlotCode = order["slot_code"] | esp32cfg::kDefaultSlotCode;
    transactionHasBackendOrder = true;
    shouldClearCashOnSuccess = false;

    Serial.printf("[POLL] Remote pending order %d found for slot %s\n", currentOrderId, currentSlotCode.c_str());
    startDispenseFlow();
}

void startOnlinePaymentForSlot(const String& inputCode) {
    if (!wifi_manager::isConnected()) {
        displayui::showError("KHONG CO WIFI", "Vui long thu lai");
        return;
    }
    
    String slotCode = config_manager::mapSelectionToSlotCode(inputCode);
    displayui::showLoading("Dang tao don...", slotCode);

    api_client::OrderInfo order;
    if (!api_client::createOrder(slotCode, order)) {
        displayui::showError("LOI HE THONG", "Tao don that bai");
        delay(2000);
        displayui::showHome(accumulatedCash, true);
        return;
    }

    int paymentCode = 0;
    String qrPayload;
    if (!api_client::createPayment(order.id, order.productName, order.amount, paymentCode, qrPayload)) {
        displayui::showError("LOI THANH TOAN", "Khong tao duoc QR");
        return;
    }

    if (!displayui::canRenderPaymentQr(qrPayload)) {
        displayui::showError("QR KHONG HOP LE", "Payload QR qua dai");
        delay(2000);
        displayui::showHome(accumulatedCash, true);
        return;
    }

    currentOrderId = order.id;
    currentPaymentCode = paymentCode;
    currentSlotCode = slotCode;
    waitingForPayment = true;
    paymentStartedAt = millis();
    currentOrderTotal = order.amount;
    currentAmountText = String(order.amount) + " VND";
    transactionHasBackendOrder = true;
    shouldClearCashOnSuccess = false;

    displayui::showPaymentQr(String(order.id), currentAmountText, qrPayload);
}

void tryCashDispense(const String& inputCode) {
    if (!wifi_manager::isConnected()) {
        displayui::showError("KHONG CO WIFI", "Vui long thu lai");
        return;
    }

    String slotCode = config_manager::mapSelectionToSlotCode(inputCode);
    displayui::showLoading("Dang kiem tra...", slotCode);

    if (!config_manager::isCashEnabled()) {
        displayui::showError("CASH DISABLED", "Chi ho tro QR");
        delay(2000);
        displayui::showHome(accumulatedCash, true);
        return;
    }

    if (accumulatedCash == 0) {
        startOnlinePaymentForSlot(inputCode);
        return;
    }

    api_client::OrderInfo order;
    if (!api_client::createOrder(slotCode, order)) {
        displayui::showError("LOI ORDER", "Khong the tao don");
        delay(2000);
        displayui::showHome(accumulatedCash, true);
        return;
    }

    currentOrderId = order.id;
    currentSlotCode = slotCode;
    currentOrderTotal = order.amount;
    transactionHasBackendOrder = true;
    shouldClearCashOnSuccess = accumulatedCash > 0;

    uint32_t reported = 0;
    int remaining = -1;
    bool anyReportFailed = false;

    while (reported < accumulatedCash) {
        uint32_t toReport = 10000;
        if (reported + toReport > accumulatedCash) toReport = accumulatedCash - reported;
        
        if (!api_client::reportCashInsert(order.id, (int)toReport, remaining)) {
            Serial.printf("[CASH] Warning: Failed to report chunk %u to backend\n", toReport);
            anyReportFailed = true;
            // Không return ngay nếu đã đủ tiền cục bộ
            if (accumulatedCash < currentOrderTotal) {
                displayui::showError("LOI BACKEND", "Khong the luu don");
                delay(2000);
                displayui::showHome(accumulatedCash, true);
                return;
            }
        }
        reported += toReport;
    }

    // Ưu tiên nhả hàng nếu TIỀN CỤC BỘ ĐÃ ĐỦ
    if (accumulatedCash >= currentOrderTotal || remaining <= 0) {
         Serial.println("[CASH] Final check: Condition met! Dispensing...");
         startDispenseFlow();
    } else {
        // Still remaining, show QR
        uint32_t remainingDisplay = (uint32_t)remaining;
        int paymentCode = 0;
        String qrPayload;
        if (api_client::createPayment(order.id, order.productName, (int)remainingDisplay, paymentCode, qrPayload)) {
            if (!displayui::canRenderPaymentQr(qrPayload)) {
                displayui::showError("QR KHONG HOP LE", "Payload QR qua dai");
                delay(2000);
                displayui::showHome(accumulatedCash, true);
                return;
            }
            currentPaymentCode = paymentCode;
            waitingForPayment = true;
            paymentStartedAt = millis();
            currentAmountText = String(remainingDisplay) + " VND (Con lai)";
            displayui::showPaymentQr(String(order.id), currentAmountText, qrPayload);
        } else {
            displayui::showError("LOI THANH TOAN", "Khong tao duoc QR cho phan con lai");
            delay(2000);
            displayui::showHome(accumulatedCash, true);
        }
    }
}

} // namespace

void init() {
    api_client::init();
    lastWifiConnected = wifi_manager::isConnected();
    accumulatedCash = config_manager::getAccumulatedCash();
    lastUnoResponseAt = millis();
    if (accumulatedCash > 0) {
        Serial.printf("[VENDING] Restored %u cash from NVS\n", accumulatedCash);
    }
}

void update() {
    const uint32_t now = millis();

    if (wifi_manager::isConnected()) {
        if (hasPendingDispenseReport && now - lastDispenseReportRetryAt >= kDispenseReportRetryMs) {
            lastDispenseReportRetryAt = now;
            flushPendingDispenseReport();
        }

        if (!deviceRegistered) {
            deviceRegistered = api_client::registerDevice();
            if (deviceRegistered) api_client::sendHeartbeat();
        }

        if (api_client::getLastStatusCode() == 403) {
            if (!deviceRevoked) {
                deviceRevoked = true;
                deviceRegistered = false;
                Serial.println("[SECURITY] Device REVOKED by server (403). Locking interface.");
                displayui::showMaintenance("Thiet bi bi tam khoa\n(Revoked)");
            }
        } else if (deviceRevoked && api_client::getLastStatusCode() >= 200 && api_client::getLastStatusCode() < 300) {
            // If it was revoked but now we get a success, it must be restored
            deviceRevoked = false;
            Serial.println("[SECURITY] Device RESTORED by server. Unlocking.");
            displayui::showHome(accumulatedCash, true);
        }

        if (deviceRevoked) return; // Skip further processing if locked

        if (now - lastHeartbeatAt >= esp32cfg::kHeartbeatIntervalMs) {
            lastHeartbeatAt = now;
            if (!api_client::sendHeartbeat()) deviceRegistered = false;
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

    if (dispensingInProgress && dispenseStartedAt > 0 && now - dispenseStartedAt >= kDispenseTimeoutMs) {
        finalizeDispenseResult(false, "UNO timeout");
    }

    if (now - lastUnoPingAt >= kUnoPingIntervalMs) {
        lastUnoPingAt = now;
        uno_comm::sendCommand(protocol::CommandType::Ping, "ESP32");
    }

    // Auto-close result screen
    if (resultScreenActive && now - resultScreenOpenedAt >= kResultScreenTimeoutMs) {
        resultScreenActive = false;
        displayui::showHome(accumulatedCash, wifi_manager::isConnected());
    }

    // UNO Health Check
    if (unoAlive && (now - lastUnoResponseAt > 30000)) {
        unoAlive = false;
        Serial.println("[ERROR] UNO connection LOST (timeout 30s)!");
        api_client::reportLog("error", "ESP32-UNO Serial connection lost (timeout)");
    }
}

void handleKey(char key) {
    if (deviceRevoked) {
        Serial.printf("[SECURITY] Key %c ignored - Device is REVOKED\n", key);
        return;
    }

    if (resultScreenActive) {
        Serial.println("[VENDING] Dismissing result screen via key");
        resultScreenActive = false;
        displayui::showHome(accumulatedCash, wifi_manager::isConnected());
        return;
    }

    if (waitingForPayment || dispensingInProgress) return;

    Serial.printf("[VENDING] Key: %c\n", key);
    if (key == '*' || key == '#') {
        if (key == '#' && pendingSlotInput.length() > 0) {
            if (accumulatedCash > 0) tryCashDispense(pendingSlotInput);
            else startOnlinePaymentForSlot(pendingSlotInput);
        } else {
            pendingSlotInput = "";
            displayui::showHome(accumulatedCash, wifi_manager::isConnected());
        }
    } else {
        pendingSlotInput += key;
        if (pendingSlotInput.length() > 3) pendingSlotInput = String(key);
        displayui::showInputSlot(pendingSlotInput, accumulatedCash);
    }
}

void handleUnoEvent(const String& eventName, const String& payload) {
    if (eventName == "PONG") {
        if (!unoAlive) {
            unoAlive = true;
            Serial.println("[INFO] UNO connection RESTORED");
            api_client::reportLog("info", "ESP32-UNO Serial connection restored");
        }
        lastUnoResponseAt = millis();
        return;
    }

    // Log all OTHER important events
    Serial.printf("[UNO EVT] %s | payload=%s\n", eventName.c_str(), payload.c_str());

    if (eventName == "DISPENSE_OK" && dispensingInProgress) {
        finalizeDispenseResult(true, payload.length() > 0 ? payload : "OK");
    } else if ((eventName == "DISPENSE_FAIL" || eventName == "ERROR") && dispensingInProgress) {
        finalizeDispenseResult(false, payload.length() > 0 ? payload : "Hardware Error");
    } else if (eventName == "CASH_INSERTED") {
        if (!config_manager::isCashEnabled()) {
            Serial.println("[CASH] Ignored because cash is disabled by profile");
            return;
        }
        int amount = payload.toInt();
        updateAccumulatedCash(amount);
        Serial.printf("[VENDING] Cash received: %d, Total: %u\n", amount, accumulatedCash);

        if (waitingForPayment && currentOrderId > 0) {
            Serial.printf("[CASH] Reporting 10k to Backend for Order #%d...\n", currentOrderId);
            
            // Cập nhật màn hình nạp tiền mặt
            displayui::showCashPaymentProgress(String(currentOrderId), currentOrderTotal, accumulatedCash);

            int remaining = -1;
            bool apiSuccess = api_client::reportCashInsert(currentOrderId, amount, remaining);
            
            if (apiSuccess) {
                Serial.printf("[CASH] Backend Reported Remaining: %d\n", remaining);
                shouldClearCashOnSuccess = true;
            } else {
                Serial.printf("[CASH] ERROR: Failed to report %d to backend for order #%d\n", amount, currentOrderId);
            }

            // Local check làm fail-safe: Nếu tiền đã nạp đủ theo bộ nhớ ESP32, cho phép nhả hàng luôn
            if ((apiSuccess && remaining <= 0) || (accumulatedCash >= currentOrderTotal)) {
                Serial.println("[CASH] CONDITION MET: Fully paid (via API or Local Check)! Starting dispense flow...");
                startDispenseFlow();
            } else {
                Serial.printf("[CASH] Still missing money. Local: %u/%u, Backend: %d\n", 
                              accumulatedCash, currentOrderTotal, remaining);
                displayui::showCashPaymentProgress(String(currentOrderId), currentOrderTotal, accumulatedCash);
            }
        } else if (!waitingForPayment && !dispensingInProgress) {
            if (pendingSlotInput.length() > 0) displayui::showInputSlot(pendingSlotInput, accumulatedCash);
            else displayui::showHome(accumulatedCash, wifi_manager::isConnected());
        }
    }
}

void handleMqttCommand(const String& cmd, const String& val) {
    Serial.printf("[MQTT CMD] %s | %s\n", cmd.c_str(), val.c_str());
    if (config_manager::isRemoteDispenseEnabled() && cmd.equalsIgnoreCase("DISPENSE")) {
        // Cho phép nhả hàng ngay cả khi đang chờ thanh toán (vì Web đã báo xong)
        if (!dispensingInProgress) {
            // Support formats: "DISPENSE:<slot>" or "DISPENSE:<slot>:<order_id>"
            int secondColon = val.indexOf(':');
            if (secondColon != -1) {
                currentSlotCode = val.substring(0, secondColon);
                currentOrderId = val.substring(secondColon + 1).toInt();
                transactionHasBackendOrder = currentOrderId > 0;
            } else {
                currentSlotCode = val;
                currentOrderId = 0;
                transactionHasBackendOrder = false;
            }
            shouldClearCashOnSuccess = false;
            startDispenseFlow();
        }
    } else if (cmd.equalsIgnoreCase("REBOOT")) {
        mqtt_manager::publishStatus("rebooting");
        api_client::reportLog("warning", "Remote reboot command received via MQTT");
        delay(1000);
        ESP.restart();
    } else if (cmd.equalsIgnoreCase("RESET_CONFIG")) {
        mqtt_manager::publishStatus("resetting_config");
        api_client::reportLog("critical", "Remote RESET_CONFIG command received via MQTT! Clearing NVS...");
        config_manager::clearConfig();
        delay(1000);
        ESP.restart();
    } else if (cmd.equalsIgnoreCase("TEST_MOTOR")) {
        api_client::reportLog("info", "Remote TEST_MOTOR for slot: " + val);
        uno_comm::sendCommand(protocol::CommandType::TestMotor, config_manager::getDeviceMode() + "|" + val);
    } else if (cmd.equalsIgnoreCase("OTA_UPDATE")) {
        // Format: <update_id>:<url>:<checksum>
        int firstColon = val.indexOf(':');
        int lastColon = val.lastIndexOf(':');
        if (firstColon != -1 && lastColon != -1 && lastColon > firstColon) {
            int updateId = val.substring(0, firstColon).toInt();
            String url = val.substring(firstColon + 1, lastColon);
            String checksum = val.substring(lastColon + 1);
            ota_manager::startUpdate(updateId, url, checksum);
        }
    }
}

void handleWifiStateChange(bool connected) {
    if (connected && !lastWifiConnected) {
        deviceRegistered = false;
        displayui::showWifiReady(wifi_manager::getLocalIP());
        delay(1000);
        displayui::showHome(accumulatedCash, true);
    } else if (!connected && lastWifiConnected) {
        deviceRegistered = false;
        mqtt_manager::publishStatus("wifi_disconnected");
    }
    lastWifiConnected = connected;
}

void handleConsoleCommand(const String& cmdRaw) {
    String cmd = cmdRaw;
    cmd.toUpperCase();
    if (cmd == "HELP") {
        printConsoleHelp();
    } else if (cmd == "STATUS") {
        printConsoleStatus();
    } else if (cmd == "IDLE") {
        resetPaymentState();
        pendingSlotInput = "";
        displayui::showHome(accumulatedCash, wifi_manager::isConnected());
    } else if (cmd == "CLEAR_CASH") {
        Serial.println("[USB TEST] Manual CLEAR_CASH");
        updateAccumulatedCash(0, false);
        displayui::showHome(accumulatedCash, wifi_manager::isConnected());
    } else if (cmd == "PAY") {
        startOnlinePaymentForSlot(config_manager::mapSelectionToSlotCode(esp32cfg::kDefaultSlotCode));
    } else if (cmd.startsWith("PAY ")) {
        String slot = cmdRaw.substring(4);
        slot.trim();
        if (slot.length() > 0) {
            startOnlinePaymentForSlot(slot);
        }
    } else if (cmd.startsWith("DISPENSE ")) {
        String slot = cmdRaw.substring(9);
        slot.trim();
        if (slot.length() > 0 && !waitingForPayment && !dispensingInProgress) {
            currentOrderId = 0;
            currentPaymentCode = 0;
            currentSlotCode = slot;
            transactionHasBackendOrder = false;
            shouldClearCashOnSuccess = false;
            Serial.printf("[USB TEST] Manual dispense slot=%s\n", slot.c_str());
            startDispenseFlow();
        }
    } else if (cmd.startsWith("MOTOR ")) {
        String slot = cmdRaw.substring(6);
        slot.trim();
        if (slot.length() == 0) slot = "TEST";
        Serial.printf("[USB TEST] Manual TEST_MOTOR slot=%s\n", slot.c_str());
        uno_comm::sendCommand(protocol::CommandType::TestMotor, config_manager::getDeviceMode() + "|" + slot);
    } else if (cmd == "SERVO") {
        Serial.println("[USB TEST] Manual TEST_SERVO");
        uno_comm::sendCommand(protocol::CommandType::TestServo, "MANUAL");
    } else if (cmd == "PINGUNO") {
        Serial.println("[USB TEST] Manual PING UNO");
        uno_comm::sendCommand(protocol::CommandType::Ping, "USB");
    } else if (cmd.startsWith("CASH ")) {
        String amountRaw = cmdRaw.substring(5);
        amountRaw.trim();
        int amount = amountRaw.toInt();
        if (amount > 0) {
            Serial.printf("[USB TEST] Simulate cash insert=%d\n", amount);
            handleUnoEvent("CASH_INSERTED", String(amount));
        }
    } else if (cmd.startsWith("SETKEY ")) {
        String newKey = cmd.substring(7);
        newKey.trim();
        if (newKey.length() > 0) {
            config_manager::saveMachineKey(newKey);
            api_client::reportLog("warning", "Manual key change via USB to: " + newKey);
            deviceRegistered = false; // Force re-registration with new key
            Serial.printf("[VENDING] Key updated via console: %s\n", newKey.c_str());
        }
    } else if (cmd == "UNO TEST") {
        uno_comm::sendCommand(protocol::CommandType::TestMotor, config_manager::getDeviceMode() + "|TEST");
    } else {
        Serial.printf("[USB] Unknown command: %s\n", cmdRaw.c_str());
        printConsoleHelp();
    }
}

} // namespace vending_controller
