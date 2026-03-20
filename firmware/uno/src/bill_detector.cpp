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
    uint32_t now = millis();
    if (now - lastSampleTime < kSampleIntervalMs) {
        return lastDetected;
    }
    lastSampleTime = now;

    long rSum = 0, gSum = 0, bSum = 0;
    const int samples = 5; // Reduced from 30 to avoid blocking loop for too long

    for (int i = 0; i < samples; i++) {
        // Sample Red
        digitalWrite(pins[2], LOW);
        digitalWrite(pins[3], LOW);
        rSum += pulseIn(pins[4], LOW, 20000);

        // Sample Green
        digitalWrite(pins[2], HIGH);
        digitalWrite(pins[3], HIGH);
        gSum += pulseIn(pins[4], LOW, 20000);

        // Sample Blue
        digitalWrite(pins[2], LOW);
        digitalWrite(pins[3], HIGH);
        bSum += pulseIn(pins[4], LOW, 20000);
        
        delay(2);
    }

    current.r = rSum / samples;
    current.g = gSum / samples;
    current.b = bSum / samples;

    // Logic for 10k VND (based on user provided ranges)
    // R: 90-120, G: 100-230, B: 80-115
    lastDetected = ((current.r >= 90 && current.r <= 120) && 
                    (current.g >= 100 && current.g <= 230) && 
                    (current.b >= 80 && current.b <= 115));

    static uint32_t lastHeartbeatLogAt = 0;
    static Color lastLoggedColor = {0, 0, 0};

    // Only log if detected, OR if heartbeat interval reached, OR if color changed significantly
    bool colorChanged = (abs(current.r - lastLoggedColor.r) > 15 || 
                         abs(current.g - lastLoggedColor.g) > 15 || 
                         abs(current.b - lastLoggedColor.b) > 15);

    if (lastDetected) {
        Serial.print(F("[BILL] *** 10,000 VND MATCH *** | R=")); Serial.print(current.r);
        Serial.print(F(" G=")); Serial.print(current.g);
        Serial.print(F(" B=")); Serial.println(current.b);
        lastHeartbeatLogAt = now;
        lastLoggedColor = current;
    } else if (colorChanged || (now - lastHeartbeatLogAt >= 30000)) {
        // Periodic heartbeat log or significant change to show sensor is alive
        Serial.print(F("[SENSOR] R=")); Serial.print(current.r);
        Serial.print(F(" G=")); Serial.print(current.g);
        Serial.print(F(" B=")); Serial.print(current.b);
        if (colorChanged) Serial.print(F(" (CHNG)"));
        else Serial.print(F(" (IDLE)"));
        Serial.println();
        
        lastHeartbeatLogAt = now;
        lastLoggedColor = current;
    }

    return lastDetected;
}

} // namespace uno
