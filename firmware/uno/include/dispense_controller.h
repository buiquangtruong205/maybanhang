#pragma once

#include <Arduino.h>

namespace uno {

class MotorController;

namespace dispense_controller {

void init(MotorController* motor);
void run(const String& payload);

}  // namespace dispense_controller
}  // namespace uno
