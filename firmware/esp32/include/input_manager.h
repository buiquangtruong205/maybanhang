#pragma once

#include <Arduino.h>
#include <Keypad.h>

namespace input_manager {

void init();
char getKey();

} // namespace input_manager
