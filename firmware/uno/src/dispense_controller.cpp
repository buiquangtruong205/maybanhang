#include "dispense_controller.h"

#include "motor_controller.h"
#include "pins.h"
#include "serial_protocol.h"
#include <avr/wdt.h>

namespace uno {
namespace dispense_controller {

namespace {

MotorController* stepper = nullptr;
const uint32_t kDropDetectTimeoutMs = 3000;
const uint32_t kDropDetectDebounceMs = 50;

const char* extractPayloadValue(const char* payload) {
    const char* sep = strchr(payload, '|');
    if (!sep) return payload;
    return sep + 1;
}

}  // namespace

void init(MotorController* motor) {
    stepper = motor;
}

void run(const char* payload) {
    if (stepper == nullptr) {
        serial_protocol::sendEvent("ERROR", "STEPPER_NULL");
        return;
    }

    const char* slotCode = extractPayloadValue(payload);
    Serial.println(F("[DISPENSE] Motor starting..."));
    stepper->rotateClockwise(4096, 5); // Start motor

    const uint32_t startedAt = millis();
    const uint32_t hardTimeoutMs = 15000;
    bool dispenseSuccess = false;

    // Loop while motor is moving
    while (millis() - startedAt < hardTimeoutMs) {
        wdt_reset(); 
        
        if (stepper->isMoving()) {
            stepper->tick();
        } else {
            dispenseSuccess = true;
            break;
        }
        delay(1); 
    }

    stepper->stop(); // Ensure motor is off

    if (dispenseSuccess) {
        serial_protocol::sendEvent("DISPENSE_OK", slotCode[0] ? slotCode : "OK");
    } else {
        Serial.println(F("[DISPENSE] Timeout"));
        serial_protocol::sendEvent("DISPENSE_FAIL", slotCode[0] ? slotCode : "TIMEOUT");
    }
}

}  // namespace dispense_controller
}  // namespace uno
