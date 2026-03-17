#pragma once

#include <Arduino.h>
#include <ArduinoJson.h>

namespace api_client {

struct OrderInfo {
    int id;
    String productName;
    int amount;
};

struct PaymentStatus {
    bool success;
    String status;
    int amountPaid;
    int amountRemaining;
};

void init();
bool registerDevice();
bool sendHeartbeat();
bool createOrder(const String& slotCode, OrderInfo& outOrder);
bool createPayment(int orderId, const String& itemName, int amount, int& paymentCode, String& qrPayload);
bool getPaymentStatus(int paymentCode, PaymentStatus& outStatus);
bool fetchPendingOrders(JsonDocument& outDoc);
bool reportDispenseResult(int orderId, const String& slotCode, bool success, const String& message);

}  // namespace api_client
