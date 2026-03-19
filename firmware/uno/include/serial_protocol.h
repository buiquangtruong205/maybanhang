#pragma once

#include <Arduino.h>

namespace uno {
namespace serial_protocol {

using ActionCallback = void (*)(const String& payload);

void init(ActionCallback onDispense, ActionCallback onTestMotor, ActionCallback onTestServo, ActionCallback onStatus);
void pump();
void sendEvent(const String& eventName, const String& payload = "");

}  // namespace serial_protocol
}  // namespace uno
