#include "bill_detector.h"

namespace uno {

BillDetector::BillDetector(uint8_t s0, uint8_t s1, uint8_t s2, uint8_t s3, uint8_t out) {
    pins[0] = s0;
    pins[1] = s1;
    pins[2] = s2;
    pins[3] = s3;
    pins[4] = out;
}

void BillDetector::begin() {
    for (int i = 0; i < 4; i++) {
        pinMode(pins[i], OUTPUT);
    }
    pinMode(pins[4], INPUT);

    // Set frequency scaling to 20%
    digitalWrite(pins[0], HIGH);
    digitalWrite(pins[1], LOW);
}

bool BillDetector::update() {
    if (millis() - lastSampleTime < kSampleIntervalMs) {
        return lastDetected;
    }
    lastSampleTime = millis();

    // Sample Red
    digitalWrite(pins[2], LOW);
    digitalWrite(pins[3], LOW);
    current.r = pulseIn(pins[4], LOW, 20000); // 20ms timeout

    // Sample Green
    digitalWrite(pins[2], HIGH);
    digitalWrite(pins[3], HIGH);
    current.g = pulseIn(pins[4], LOW, 20000);

    // Sample Blue
    digitalWrite(pins[2], LOW);
    digitalWrite(pins[3], HIGH);
    current.b = pulseIn(pins[4], LOW, 20000);

    // Logic for 10k VND (based on user provided ranges)
    // R: 95-115, G: 105-225, B: 85-110
    lastDetected = ((current.r >= 95 && current.r <= 115) && 
                    (current.g >= 105 && current.g <= 225) && 
                    (current.b >= 85 && current.b <= 110));

    return lastDetected;
}

} // namespace uno
