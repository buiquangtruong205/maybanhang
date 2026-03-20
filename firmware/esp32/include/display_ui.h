#pragma once

#include <Arduino.h>

namespace displayui {

void init();
void showBooting();
void showWifiConnecting(const char* ssid);
void showWifiReady(const IPAddress& ip);
bool canRenderPaymentQr(const String& qrPayload);
void showHome(uint32_t balance = 0, bool wifiOk = true);
void showInputSlot(const String& currentInput, uint32_t balance = 0);
void showLoading(const String& line1, const String& line2);
void showPaymentQr(const String& orderId, const String& amountText, const String& qrPayload);
void showCashPaymentProgress(const String& orderId, uint32_t total, uint32_t received);
void showPaymentResult(const String& title, const String& detail, bool success);
void showError(const String& title, const String& detail);
void showMaintenance(const String& reason);

}  // namespace displayui
