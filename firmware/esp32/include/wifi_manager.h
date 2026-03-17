#pragma once

#include <Arduino.h>
#include <WiFi.h>

namespace wifi_manager {

void init();
void loop();
bool isConnected();
void ensureConnected();
IPAddress getLocalIP();

}  // namespace wifi_manager
