#pragma once

#include <Arduino.h>

namespace displayui {

void init();
void showBooting();
void showWifiConnecting(const char* ssid);
void showWifiReady(const IPAddress& ip);
void showIdle();
void showLoading(const String& line1, const String& line2);
void showPaymentQr(const String& orderId, const String& amountText, const String& qrPayload);
void showPaymentResult(const String& title, const String& detail, bool success);
void showError(const String& title, const String& detail);

}  // namespace displayui
