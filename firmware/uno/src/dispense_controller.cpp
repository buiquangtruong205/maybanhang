#include "dispense_controller.h"

#include "motor_controller.h"
#include "pins.h"
#include "serial_protocol.h"
#include <avr/wdt.h>

namespace uno {
namespace dispense_controller {

namespace {

MotorController* stepper1 = nullptr;
MotorController* stepper2 = nullptr;
const uint32_t kDropDetectTimeoutMs = 3000;
const uint32_t kDropDetectDebounceMs = 50;

const char* extractPayloadValue(const char* payload) {
    const char* sep = strchr(payload, '|');
    if (!sep) return payload;
    return sep + 1;
}

}  // namespace

void init(MotorController* motor1, MotorController* motor2) {
    stepper1 = motor1;
    stepper2 = motor2;
}

void run(const char* payload) {
    const char* slotCode = extractPayloadValue(payload);
    MotorController* activeStepper = stepper1; // Default to motor 1

    // Simple routing logic based on slot code
    if (strcmp(slotCode, "02") == 0 || strcmp(slotCode, "A2") == 0) {
        activeStepper = stepper2;
    }

    if (activeStepper == nullptr) {
        serial_protocol::sendEvent("ERROR", "STEPPER_NULL");
        return;
    }

    // Use move() instead of rotateClockwise() because rotateClockwise()
    // runs a blocking loop WITHOUT wdt_reset() → causes watchdog reset!
    // The while loop below already has wdt_reset() and calls tick().
    activeStepper->move(4096, 3); // Optimized: 3ms per step (Total ~12.3s)

    const uint32_t startedAt = millis();
    const uint32_t hardTimeoutMs = 30000; // Increased to 30s to be safe
    bool dispenseSuccess = false;

    // Loop while motor is moving — this loop has wdt_reset()
    while (millis() - startedAt < hardTimeoutMs) {
        wdt_reset(); 
        
        if (activeStepper->isMoving()) {
            activeStepper->tick();
        } else {
            dispenseSuccess = true;
            break;
        }
        delay(1); 
    }

    activeStepper->stop(); // Ensure motor is off

    if (dispenseSuccess) {
        serial_protocol::sendEvent("DISPENSE_OK", slotCode[0] ? slotCode : "OK");
    } else {
        // Timeout — event sent below
        serial_protocol::sendEvent("DISPENSE_FAIL", slotCode[0] ? slotCode : "TIMEOUT");
    }
}

}  // namespace dispense_controller
}  // namespace uno
