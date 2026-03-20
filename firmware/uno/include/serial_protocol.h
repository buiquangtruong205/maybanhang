#pragma once

#include <Arduino.h>

namespace uno {
namespace serial_protocol {

using ActionCallback = void (*)(const char* payload);

void init(ActionCallback onDispense, ActionCallback onTestMotor, ActionCallback onTestServo, ActionCallback onStatus);
void pump();
void sendEvent(const char* eventName, const char* payload = "");

}  // namespace serial_protocol
}  // namespace uno
