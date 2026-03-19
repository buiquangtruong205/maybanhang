#include "motor_controller.h"

namespace uno {

const uint8_t MotorController::kHalfSteps[8][4] = {
    {1, 0, 0, 0},
    {1, 1, 0, 0},
    {0, 1, 0, 0},
    {0, 1, 1, 0},
    {0, 0, 1, 0},
    {0, 0, 1, 1},
    {0, 0, 0, 1},
    {1, 0, 0, 1},
};

MotorController::MotorController(uint8_t in1, uint8_t in2, uint8_t in3, uint8_t in4) {
    pins[0] = in1;
    pins[1] = in2;
    pins[2] = in3;
    pins[3] = in4;
    currentStep = 0;
    targetSteps = 0;
    stepCount = 0;
    stepDelay = 5;
    lastStepAt = 0;
    moving = false;
    clockwise = true;
}

void MotorController::begin() {
    for (int i = 0; i < 4; i++) {
        pinMode(pins[i], OUTPUT);
        digitalWrite(pins[i], LOW);
    }
}

void MotorController::move(int steps, int delayMs) {
    targetSteps = abs(steps);
    stepCount = 0;
    stepDelay = delayMs;
    lastStepAt = millis();
    moving = true;
    clockwise = steps > 0;
}

void MotorController::tick() {
    if (!moving) return;

    uint32_t now = millis();
    if (now - lastStepAt >= stepDelay) {
        lastStepAt = now;
        
        if (clockwise) {
            currentStep = (currentStep + 1) % 8;
        } else {
            currentStep = (currentStep > 0) ? (currentStep - 1) : 7;
        }
        
        writeStep(currentStep);
        stepCount++;
        
        if (stepCount >= targetSteps) {
            stop();
        }
    }
}

void MotorController::stop() {
    moving = false;
    release();
}

void MotorController::writeStep(uint8_t stepIndex) {
    for (int i = 0; i < 4; i++) {
        digitalWrite(pins[i], kHalfSteps[stepIndex][i]);
    }
}

void MotorController::rotateClockwise(int steps, int delayMs) {
    move(steps, delayMs);
    while (moving) {
        tick();
    }
}

void MotorController::rotateCounterClockwise(int steps, int delayMs) {
    move(-steps, delayMs);
    while (moving) {
        tick();
    }
}

void MotorController::release() {
    for (int i = 0; i < 4; i++) {
        digitalWrite(pins[i], LOW);
    }
}

} // namespace uno
