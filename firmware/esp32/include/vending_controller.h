#pragma once

#include <Arduino.h>

namespace vending_controller {

void init();
void update();

// Event Handlers (Called by main code when hardware events occur)
void handleKey(char key);
void handleUnoEvent(const String& eventName, const String& payload);
void handleMqttCommand(const String& cmd, const String& val);
void handleWifiStateChange(bool connected);
void handleConsoleCommand(const String& cmdRaw);

} // namespace vending_controller
