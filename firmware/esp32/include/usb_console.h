#pragma once

#include <Arduino.h>

namespace usb_console {

typedef void (*ConsoleCommandCallback)(const String& command);

void init(ConsoleCommandCallback callback);
void loop();

}  // namespace usb_console
