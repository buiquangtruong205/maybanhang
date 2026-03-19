#include "gate_manager.h"

namespace uno {

GateManager::GateManager(uint8_t servoPin) : pin(servoPin) {}

void GateManager::begin() {
    servo.attach(pin);
    servo.write(kClosedAngle);
    char buffer[64];
    snprintf(buffer, sizeof(buffer), "[GATE] Servo attached on pin %u, state=CLOSED", pin);
    Serial.println(buffer);
}

void GateManager::trigger() {
    if (state == State::CLOSED) {
        Serial.println("[GATE] Opening gate");
        servo.write(kOpenAngle);
        state = State::OPEN;
        openStartTime = millis();
    }
}

void GateManager::update() {
    if (state == State::OPEN) {
        if (millis() - openStartTime >= kOpenDurationMs) {
            Serial.println("[GATE] Closing gate");
            servo.write(kClosedAngle);
            state = State::CLOSED;
        }
    }
}

} // namespace uno
