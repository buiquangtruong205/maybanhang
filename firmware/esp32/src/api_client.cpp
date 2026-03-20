#include "api_client.h"
#include <WiFi.h>
#include <HTTPClient.h>
#include <ArduinoJson.h>
#include "wifi_manager.h"
#include "app_config.h"
#include "config_manager.h"
#include "secrets.h"

namespace api_client {

namespace {
int lastStatusCode = 200;

String maskMachineKey(const String& value) {
    if (value.length() == 0) return "<empty>";
    if (value.length() <= 4) return "****";
    return value.substring(0, 4) + "...(" + String(value.length()) + ")";
}

void syncServerProfile(const JsonDocument& responseDoc) {
    JsonVariantConst config = responseDoc["data"]["config"];
    if (config.isNull()) {
        return;
    }

    const String machineId = config["machine_id"] | "";
    const String machineName = config["machine_name"] | "";
    const String mqttBroker = config["mqtt"]["broker"] | "";
    const uint16_t mqttPort = config["mqtt"]["port"] | config_manager::getMqttPort();
    const String mqttCommandTopic = config["mqtt"]["topics"]["command"] | "";
    const String mqttStatusTopic = config["mqtt"]["topics"]["status"] | "";
    const String mqttBroadcastTopic = config["mqtt"]["topics"]["broadcast_status"] | "";
    const String machineKey = config["machine_key"] | "";
    
    String uiLayoutJson;
    String deviceProfileJson;
    if (!config["ui"]["layout"].isNull()) {
        serializeJson(config["ui"]["layout"], uiLayoutJson);
    }
    if (!config["device_profile"].isNull()) {
        serializeJson(config["device_profile"], deviceProfileJson);
    }

    if (machineKey.length() > 0) {
        config_manager::saveMachineKey(machineKey);
    }

    if (config_manager::applyServerProfile(
            machineId,
            machineName,
            mqttBroker,
            mqttPort,
            mqttCommandTopic,
            mqttStatusTopic,
            mqttBroadcastTopic,
            uiLayoutJson,
            deviceProfileJson)) {
        Serial.printf(
            "[CONFIG] Applied backend profile: machineId=%s, machineName=%s, mqtt=%s:%u, cmdTopic=%s, theme=%s, cash=%d\n",
            machineId.c_str(),
            machineName.c_str(),
            mqttBroker.c_str(),
            mqttPort,
            mqttCommandTopic.c_str(),
            config_manager::getUiTheme().c_str(),
            config_manager::isCashEnabled()
        );
    }
}

bool apiRequest(const String& method, const String& path, const String& payload, JsonDocument& outDoc, int& statusCode) {
    if (!wifi_manager::isConnected()) {
        statusCode = -1;
        return false;
    }

    HTTPClient http;
    const String apiBaseUrl = config_manager::getApiBaseUrl();
    const String machineKey = config_manager::getMachineKey();
    const String url = apiBaseUrl + path;

    if (machineKey.length() == 0) {
        Serial.printf("[HTTP] Warning: machine key is empty for %s\n", url.c_str());
    }

    http.begin(url);
    http.addHeader("Content-Type", "application/json");
    http.addHeader("X-Machine-Key", machineKey);

    if (method == "POST") {
        statusCode = http.POST(payload);
    } else if (method == "GET") {
        statusCode = http.GET();
    } else {
        statusCode = -2;
        http.end();
        return false;
    }

    const String response = http.getString();
    http.end();

    lastStatusCode = statusCode;
    Serial.printf("[HTTP] %s %s => %d\n", method.c_str(), url.c_str(), statusCode);
    if (statusCode >= 400 || statusCode <= 0) {
        Serial.printf(
            "[HTTP] Failure details: base=%s, key=%s, response=%s\n",
            apiBaseUrl.c_str(),
            maskMachineKey(machineKey).c_str(),
            response.c_str()
        );
    }
    if (statusCode <= 0) {
        return false;
    }

    const DeserializationError error = deserializeJson(outDoc, response);
    if (error) {
        Serial.printf("[HTTP] JSON parse failed for %s: %s\n", url.c_str(), error.c_str());
        Serial.printf("[HTTP] Raw response: %s\n", response.c_str());
    }
    return !error;
}
}

void init() {}

int getLastStatusCode() {
    return lastStatusCode;
}

bool registerDevice() {
    JsonDocument requestDoc;
    requestDoc["mac_address"] = WiFi.macAddress();
    requestDoc["fingerprint"] = WiFi.macAddress();
    requestDoc["firmware_version"] = "esp32-v3-modular";

    String payload;
    serializeJson(requestDoc, payload);

    JsonDocument responseDoc;
    int statusCode = 0;

    // Special request for registration: use MASTER_REGISTRATION_KEY
    if (wifi_manager::isConnected()) {
        HTTPClient http;
        String url = config_manager::getApiBaseUrl() + "/iot/register-device";
        http.begin(url);
        http.addHeader("Content-Type", "application/json");
        http.addHeader("X-Machine-Key", MASTER_REGISTRATION_KEY);
        
        statusCode = http.POST(payload);
        lastStatusCode = statusCode;
        String response = http.getString();
        http.end();
        
        Serial.printf("[HTTP] REGISTER %s => %d\n", url.c_str(), statusCode);
        if (statusCode > 0) {
            DeserializationError error = deserializeJson(responseDoc, response);
            if (error) {
                Serial.printf("[HTTP] REGISTER JSON parse failed: %s\n", error.c_str());
            }
        }

        if (statusCode >= 200 && statusCode < 300) {
            syncServerProfile(responseDoc);
            return true;
        }

        if (statusCode == 409) {
            Serial.println("[HTTP] Device already registered, continuing with current profile");
            syncServerProfile(responseDoc);
            return true;
        }
    }
    return false;
}

bool sendHeartbeat() {
    JsonDocument requestDoc;
    requestDoc["uptime"] = millis() / 1000;
    requestDoc["free_memory"] = ESP.getFreeHeap();
    requestDoc["wifi_rssi"] = WiFi.RSSI();
    requestDoc["wifi_ssid"] = WiFi.SSID();

    String payload;
    serializeJson(requestDoc, payload);

    JsonDocument responseDoc;
    int statusCode = 0;
    if (!apiRequest("POST", "/iot/heartbeat", payload, responseDoc, statusCode)) return false;
    if (statusCode >= 200 && statusCode < 300) {
        syncServerProfile(responseDoc);
    }
    return statusCode >= 200 && statusCode < 300 && (responseDoc["success"] | false);
}

bool createOrder(const String& slotCode, OrderInfo& outOrder) {
    JsonDocument requestDoc;
    requestDoc["slot_code"] = slotCode;
    requestDoc["quantity"] = esp32cfg::kDefaultQuantity;

    String payload;
    serializeJson(requestDoc, payload);

    JsonDocument responseDoc;
    int statusCode = 0;
    if (!apiRequest("POST", "/iot/create-order", payload, responseDoc, statusCode)) return false;

    if (statusCode < 200 || statusCode >= 300 || !responseDoc["success"].as<bool>()) return false;

    JsonVariant data = responseDoc["data"];
    outOrder.id = data["order_id"].as<int>();
    outOrder.productName = data["product_name"].as<String>();
    outOrder.amount = (int)(data["price"].as<float>());

    Serial.printf("[API] Order Created: ID=%d, Product=%s, Amount=%d\n", 
                  outOrder.id, outOrder.productName.c_str(), outOrder.amount);
    
    return outOrder.id > 0;
}

bool createPayment(int orderId, const String& itemName, int amount, int& paymentCode, String& qrPayload) {
    Serial.printf("[API] Creating Payment: Order=%d, Item=%s, Amount=%d\n", orderId, itemName.c_str(), amount);
    
    JsonDocument requestDoc;
    requestDoc["order_code"] = orderId;
    requestDoc["amount"] = amount;
    requestDoc["description"] = String("Don hang #") + orderId;
    requestDoc["buyer_name"] = esp32cfg::kDefaultBuyerName;

    JsonArray items = requestDoc["items"].to<JsonArray>();
    JsonObject item = items.add<JsonObject>();
    item["name"] = itemName;
    item["quantity"] = 1;
    item["price"] = amount;

    String payload;
    serializeJson(requestDoc, payload);

    JsonDocument responseDoc;
    int statusCode = 0;
    if (!apiRequest("POST", "/payment/create", payload, responseDoc, statusCode)) return false;

    if (statusCode < 200 || statusCode >= 300 || !responseDoc["success"].as<bool>()) return false;

    JsonVariant data = responseDoc["data"];
    paymentCode = data["payment_code"] | 0;
    qrPayload = data["qr_code"] | "";
    if (qrPayload.length() == 0) qrPayload = data["checkout_url"] | "";
    
    return paymentCode > 0 && qrPayload.length() > 0;
}

bool getPaymentStatus(int paymentCode, PaymentStatus& outStatus) {
    JsonDocument responseDoc;
    int statusCode = 0;
    if (!apiRequest("GET", String("/payment/status/") + paymentCode, "", responseDoc, statusCode)) return false;

    if (statusCode < 200 || statusCode >= 300 || !responseDoc["success"].as<bool>()) return false;

    JsonVariant data = responseDoc["data"];
    outStatus.success = responseDoc["success"] | false;
    outStatus.status = data["status"] | "";
    outStatus.amountPaid = data["amount_paid"] | 0;
    outStatus.amountRemaining = data["amount_remaining"] | 0;
    
    return true;
}

bool fetchPendingOrders(JsonDocument& outDoc) {
    int statusCode = 0;
    if (!apiRequest("GET", "/iot/pending-orders", "", outDoc, statusCode)) return false;
    return statusCode >= 200 && statusCode < 300 && (outDoc["success"] | false);
}

bool reportDispenseResult(int orderId, const String& slotCode, bool success, const String& message) {
    JsonDocument requestDoc;
    requestDoc["order_id"] = orderId;
    requestDoc["slot_code"] = slotCode;
    requestDoc["success"] = success;
    requestDoc["message"] = message;

    String payload;
    serializeJson(requestDoc, payload);

    JsonDocument responseDoc;
    int statusCode = 0;
    if (!apiRequest("POST", "/iot/dispense-complete", payload, responseDoc, statusCode)) return false;
    return statusCode >= 200 && statusCode < 300 && (responseDoc["success"] | false);
}

bool reportCashInsert(int orderId, int denomination, int& outRemaining) {
    JsonDocument requestDoc;
    requestDoc["order_id"] = orderId;
    requestDoc["denomination"] = denomination;

    String payload;
    serializeJson(requestDoc, payload);

    JsonDocument responseDoc;
    int statusCode = 0;
    outRemaining = -1; // Default
    if (!apiRequest("POST", "/iot/cash-insert", payload, responseDoc, statusCode)) return false;
    
    if (statusCode >= 200 && statusCode < 300 && responseDoc["success"].as<bool>()) {
        outRemaining = responseDoc["data"]["remaining"] | 0;
        return true;
    }
    return false;
}

bool reportLog(const String& level, const String& message) {
    JsonDocument requestDoc;
    requestDoc["level"] = level;
    requestDoc["message"] = message;

    String payload;
    serializeJson(requestDoc, payload);

    JsonDocument responseDoc;
    int statusCode = 0;
    if (!apiRequest("POST", "/iot/logs", payload, responseDoc, statusCode)) return false;
    return statusCode >= 200 && statusCode < 300 && (responseDoc["success"] | false);
}

bool reportOTAProgress(int updateId, int progress, const String& status) {
    JsonDocument requestDoc;
    requestDoc["update_id"] = updateId;
    requestDoc["progress"] = progress;
    if (status.length() > 0) requestDoc["status"] = status;

    String payload;
    serializeJson(requestDoc, payload);

    JsonDocument responseDoc;
    int statusCode = 0;
    if (!apiRequest("POST", "/firmware/report-progress", payload, responseDoc, statusCode)) return false;
    return statusCode >= 200 && statusCode < 300 && (responseDoc["success"] | false);
}

}  // namespace api_client
