#pragma once

#include <Arduino.h>

namespace uno {

class BillDetector {
public:
    struct Color {
        int r, g, b;
    };

    BillDetector(uint8_t s0, uint8_t s1, uint8_t s2, uint8_t s3, uint8_t out);
    
    void begin();
    
    // Non-blocking update. Returns true if a 10k bill is detected.
    bool update();
    
    Color getCurrentColor() const { return current; }

private:
    uint8_t pins[5]; // S0, S1, S2, S3, Out
    Color current{0, 0, 0};
    
    unsigned long lastSampleTime = 0;
    static constexpr unsigned long kSampleIntervalMs = 50;
    bool lastDetected = false;
};

} // namespace uno
