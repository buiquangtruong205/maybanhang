#pragma once

#include <Arduino.h>

namespace mqtt_manager {

typedef void (*CommandCallback)(const String& command, const String& payload);

void init(CommandCallback callback);
void loop();
bool isConnected();
void publishStatus(const String& status);

}  // namespace mqtt_manager
