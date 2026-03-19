#pragma once

#include <Arduino.h>
#include <Servo.h>

namespace uno {

class GateManager {
public:
    GateManager(uint8_t servoPin);
    
    void begin();
    
    // Starts the 5-second open cycle
    void trigger();
    
    // Non-blocking update. Handles the timing to close the gate.
    void update();
    
    bool isOpen() const { return state == State::OPEN; }

private:
    enum class State { CLOSED, OPEN };
    
    uint8_t pin;
    Servo servo;
    State state = State::CLOSED;
    unsigned long openStartTime = 0;
    
    static constexpr int kOpenAngle = 90;
    static constexpr int kClosedAngle = 180;
    static constexpr unsigned long kOpenDurationMs = 5000;
};

} // namespace uno
