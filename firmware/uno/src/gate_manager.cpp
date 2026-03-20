#include "gate_manager.h"

namespace uno {

GateManager::GateManager(uint8_t servoPin) : pin(servoPin) {}

void GateManager::begin() {
    servo.attach(pin);
    servo.write(kClosedAngle);
    // Debug removed — Serial shared with ESP32
}

void GateManager::trigger() {
    if (state == State::CLOSED) {
        servo.write(kOpenAngle);
        state = State::OPEN;
        openStartTime = millis();
    }
}

void GateManager::update() {
    if (state == State::OPEN) {
        if (millis() - openStartTime >= kOpenDurationMs) {
            servo.write(kClosedAngle);
            state = State::CLOSED;
        }
    }
}

} // namespace uno
