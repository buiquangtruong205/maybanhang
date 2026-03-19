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

String extractPayloadValue(const String& payload) {
    const int separator = payload.indexOf('|');
    if (separator < 0) return payload;
    return payload.substring(separator + 1);
}

String extractDeviceMode(const String& payload) {
    const int separator = payload.indexOf('|');
    if (separator < 0) return "standard";
    return payload.substring(0, separator);
}

}  // namespace

void init(MotorController* motor) {
    stepper = motor;
}

void run(const String& payload) {
    if (stepper == nullptr) {
        serial_protocol::sendEvent("ERROR", "STEPPER_NOT_INITIALIZED");
        return;
    }

    const String deviceMode = extractDeviceMode(payload);
    const String slotCode = extractPayloadValue(payload);
    Serial.println("[DISPENSE] Motor starting (non-blocking)...");
    stepper->move(4096, 5); // Start motor

    const uint32_t startedAt = millis();
    const uint32_t hardTimeoutMs = 30000;
    uint32_t sensorLowAt = 0;
    bool sensorSeenLow = false;
    bool dispenseSuccess = false;

    // Loop while motor is moving OR waiting for drop (with hard timeout)
    while (millis() - startedAt < hardTimeoutMs) {
        wdt_reset(); // Reset watchdog to prevent reboot during dispense
        // 1. Tick the motor
        if (stepper->isMoving()) {
            stepper->tick();
        }

        // 2. Check drop sensor
        if (digitalRead(unopins::kDropSensorPin) == LOW) {
            if (!sensorSeenLow) {
                sensorSeenLow = true;
            }
            if (sensorLowAt == 0) {
                sensorLowAt = millis();
            } else if (millis() - sensorLowAt >= kDropDetectDebounceMs) {
                Serial.println("[SENSOR] Drop detected! Stopping motor early.");
                stepper->stop();
                dispenseSuccess = true;
                break;
            }
        } else {
            sensorLowAt = 0;
            sensorSeenLow = false;
        }

        // 3. If motor finished but no drop yet, just keep waiting for drop
        if (!stepper->isMoving()) {
            // If motor finished and we still haven't seen a drop after kDropDetectTimeoutMs from motor stop, fail.
            // But we already have the hardTimeoutMs for the whole thing.
        }

        delay(1); // Small delay to prevent tight loop, but enough for 5ms motor steps
    }

    stepper->stop(); // Ensure motor is off

    if (dispenseSuccess) {
        serial_protocol::sendEvent("DROP_DETECTED", slotCode);
        serial_protocol::sendEvent("DISPENSE_OK", slotCode.length() > 0 ? slotCode : "DROP_OK");
    } else {
        Serial.println("[DISPENSE] Timeout or fail");
        serial_protocol::sendEvent("DISPENSE_FAIL", slotCode.length() > 0 ? slotCode : "TIMEOUT");
    }
}

}  // namespace dispense_controller
}  // namespace uno
