#pragma once

#include <Arduino.h>

namespace uno {

class MotorController;
class BillDetector;
class GateManager;

namespace hardware_manager {

void init(MotorController* motor1, MotorController* motor2, BillDetector* detector, GateManager* gate);
void update();
void testMotor(const char* payload);
void testServo(const char* payload);
void printStatus(const char* payload = "");
void resetProcessingState();

}  // namespace hardware_manager
}  // namespace uno
