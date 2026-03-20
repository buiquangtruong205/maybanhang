#pragma once

#include <Arduino.h>

namespace unopins {

    // --- Stepper Motor (28BYJ-48) ---
    static constexpr uint8_t kStepperIn1 = 2;
    static constexpr uint8_t kStepperIn2 = 3;
    static constexpr uint8_t kStepperIn3 = 4;
    static constexpr uint8_t kStepperIn4 = 5;

    // --- Stepper Motor 2 (Slot A2 / Button 2) ---
    // Using Analog pins as Digital (A0=14, A1=15, A2=16, A3=17)
    static constexpr uint8_t kStepper2In1 = A0;
    static constexpr uint8_t kStepper2In2 = A1;
    static constexpr uint8_t kStepper2In3 = A2;
    static constexpr uint8_t kStepper2In4 = A3;

    // --- TCS3200 Color Sensor ---
    static constexpr uint8_t kColorS0 = 6;
    static constexpr uint8_t kColorS1 = 7;
    static constexpr uint8_t kColorS2 = 8;
    static constexpr uint8_t kColorS3 = 9;
    static constexpr uint8_t kColorOut = 10;

    // --- Servo Motor (Gate) ---
    static constexpr uint8_t kServoPin = 11;

    // --- Drop Sensor (Vibration/IR) ---
    static constexpr uint8_t kDropSensorPin = 12;

    // --- Status LED ---
    static constexpr uint8_t kStatusLedPin = 13;

}  // namespace unopins
