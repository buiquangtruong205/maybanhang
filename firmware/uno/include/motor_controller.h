#pragma once

#include <Arduino.h>

namespace uno {

class MotorController {
public:
    MotorController(uint8_t in1, uint8_t in2, uint8_t in3, uint8_t in4);
    
    void begin();
    
    // Non-blocking control
    void move(int steps, int delayMs = 5);
    void tick();
    bool isMoving() const { return moving; }
    void stop();

    // Blocking versions (for convenience)
    void rotateClockwise(int steps, int delayMs = 5);
    void rotateCounterClockwise(int steps, int delayMs = 5);
    
    void release();

private:
    void writeStep(uint8_t stepIndex);
    
    uint8_t pins[4];
    static const uint8_t kHalfSteps[8][4];
    
    int currentStep;
    int targetSteps;
    int stepCount;
    uint32_t stepDelay;
    uint32_t lastStepAt;
    bool moving;
    bool clockwise;
};

} // namespace uno
