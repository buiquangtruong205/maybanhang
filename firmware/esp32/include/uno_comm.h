#pragma once

#include <Arduino.h>
#include "protocol.h"

namespace uno_comm {

typedef void (*EventCallback)(const String& frame);

void init(EventCallback callback);
void loop();
void sendCommand(protocol::CommandType type, const String& payload = "");

}  // namespace uno_comm
