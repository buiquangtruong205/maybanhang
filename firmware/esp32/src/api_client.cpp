#include "api_client.h"
#include <HTTPClient.h>
#include "wifi_manager.h"
#include "app_config.h"
#include "secrets.h"

namespace api_client {

namespace {
bool apiRequest(const String& method, const String& path, const String& payload, JsonDocument& outDoc, int& statusCode) {
    if (!wifi_manager::isConnected()) {
        statusCode = -1;
        return false;
    }

    HTTPClient http;
    const String url = String(API_BASE_URL) + path;
    http.begin(url);
    http.addHeader("Content-Type", "application/json");
    http.addHeader("X-Machine-Key", esp32cfg::kMachineKey);

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

    Serial.printf("[HTTP] %s %s => %d\n", method.c_str(), url.c_str(), statusCode);
    if (statusCode <= 0) {
        return false;
    }

    const DeserializationError error = deserializeJson(outDoc, response);
    return !error;
}
}

void init() {}

bool registerDevice() {
    JsonDocument requestDoc;
    requestDoc["mac_address"] = WiFi.macAddress();
    requestDoc["fingerprint"] = WiFi.macAddress();
    requestDoc["firmware_version"] = "esp32-v3-modular";

    String payload;
    serializeJson(requestDoc, payload);

    JsonDocument responseDoc;
    int statusCode = 0;
    if (!apiRequest("POST", "/iot/register-device", payload, responseDoc, statusCode)) return false;
    return statusCode >= 200 && statusCode < 300 && (responseDoc["success"] | false);
}

bool sendHeartbeat() {
    JsonDocument requestDoc;
    requestDoc["uptime"] = millis() / 1000;
    requestDoc["free_memory"] = ESP.getFreeHeap();
    requestDoc["wifi_rssi"] = WiFi.RSSI();

    String payload;
    serializeJson(requestDoc, payload);

    JsonDocument responseDoc;
    int statusCode = 0;
    if (!apiRequest("POST", "/iot/heartbeat", payload, responseDoc, statusCode)) return false;
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

}  // namespace api_client
