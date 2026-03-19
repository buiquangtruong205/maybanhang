#pragma once

#include <Arduino.h>

namespace uno {

class MotorController;
class BillDetector;
class GateManager;

namespace hardware_manager {

void init(MotorController* motor, BillDetector* detector, GateManager* gate);
void update();
void testMotor(const String& payload);
void testServo(const String& payload);
void printStatus(const String& payload = "");

}  // namespace hardware_manager
}  // namespace uno
