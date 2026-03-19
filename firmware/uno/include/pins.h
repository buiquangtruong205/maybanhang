#pragma once

#include <Arduino.h>

namespace unopins {

static constexpr uint8_t kDropSensorPin = 2;
    static constexpr uint8_t kStepperIn1 = 4;
    static constexpr uint8_t kStepperIn2 = 5;
    static constexpr uint8_t kStepperIn3 = 6;
    static constexpr uint8_t kStepperIn4 = 7;
    static constexpr uint8_t kStatusLedPin = LED_BUILTIN;

    // TCS3200 Color Sensor
    static constexpr uint8_t kColorS0 = A0;
    static constexpr uint8_t kColorS1 = A1;
    static constexpr uint8_t kColorS2 = A2;
    static constexpr uint8_t kColorS3 = A3;
    static constexpr uint8_t kColorOut = 9;

    // Servo Motor
    static constexpr uint8_t kServoPin = 10;

}  // namespace unopins
