#include "hardware_manager.h"

#include "bill_detector.h"
#include "gate_manager.h"
#include "motor_controller.h"
#include "pins.h"
#include "serial_protocol.h"

namespace uno {
namespace hardware_manager {

namespace {

MotorController* stepper = nullptr;
BillDetector* billScanner = nullptr;
GateManager* billGate = nullptr;

bool billProcessing = false;
uint32_t billDetectionStartedAt = 0;
const uint32_t kBillDebounceMs = 2000;

void printInitStatus() {
    char buffer[96];
    snprintf(buffer, sizeof(buffer), "[HW] Init complete | led=%d servo=%d",
             unopins::kStatusLedPin, unopins::kServoPin);
    Serial.println(buffer);
}

void printBillDetected(const BillDetector::Color& color) {
    char buffer[96];
    snprintf(buffer, sizeof(buffer), "[BILL] *** 10,000 VND *** | R=%d G=%d B=%d", color.r, color.g, color.b);
    Serial.println(buffer);
}

void printHardwareStatus(bool gateOpen, const BillDetector::Color& color) {
    char buffer[112];
    snprintf(buffer, sizeof(buffer), "[HW STATUS] gate=%s bill_processing=%d rgb=(%d,%d,%d)",
             gateOpen ? "OPEN" : "CLOSED",
             billProcessing ? 1 : 0,
             color.r, color.g, color.b);
    Serial.println(buffer);
}

}  // namespace

void init(MotorController* motor, BillDetector* detector, GateManager* gate) {
    stepper = motor;
    billScanner = detector;
    billGate = gate;

    // pinMode(unopins::kDropSensorPin, INPUT_PULLUP); // DISABLED
    pinMode(unopins::kStatusLedPin, OUTPUT);
    digitalWrite(unopins::kStatusLedPin, HIGH);

    if (stepper != nullptr) stepper->begin();
    if (billScanner != nullptr) billScanner->begin();
    if (billGate != nullptr) billGate->begin();

    printInitStatus();
}

void update() {
    if (billScanner == nullptr || billGate == nullptr) {
        return;
    }

    bool detected = billScanner->update();
    uint32_t now = millis();

    if (detected && !billProcessing) {
        if (billDetectionStartedAt == 0) {
            billDetectionStartedAt = now;
            Serial.println(F("[BILL] Potential bill detected, debouncing..."));
        } else if (now - billDetectionStartedAt > 500) { // Slightly longer debounce for stability
            BillDetector::Color color = billScanner->getCurrentColor();
            printBillDetected(color);
            billGate->trigger();
            Serial.println(F("[GATE] Triggered (5s OPEN) for bill insertion."));
            serial_protocol::sendEvent("CASH_INSERTED", "10000");
            billProcessing = true;
            billDetectionStartedAt = now;
        }
    } else if (!detected && billProcessing) {
        if (now - billDetectionStartedAt > kBillDebounceMs) {
            Serial.println(F("[BILL] Slot clear. Ready for next."));
            billProcessing = false;
            billDetectionStartedAt = 0;
        }
    } else if (!detected) {
        billDetectionStartedAt = 0;
    }

    billGate->update();
}

void testMotor(const char* payload) {
    if (stepper == nullptr) {
        serial_protocol::sendEvent("ERROR", "MOTOR_NULL");
        return;
    }

    Serial.print(F("[MOTOR] START TEST | Payload: "));
    Serial.println(payload);
    
    // Rotate 1 full revolution (4096 steps for 28BYJ-48)
    stepper->rotateClockwise(4096, 5); 
    delay(500);
    stepper->rotateCounterClockwise(4096, 5);
    
    Serial.println(F("[MOTOR] TEST DONE"));
    serial_protocol::sendEvent("ACK", "MOTOR_TEST_OK");
}

void testServo(const char* payload) {
    (void)payload;

    if (billGate == nullptr) {
        serial_protocol::sendEvent("ERROR", "GATE_NOT_INITIALIZED");
        return;
    }

    billGate->trigger();
    serial_protocol::sendEvent("ACK", "TEST_SERVO_STARTED");
}

void printStatus(const char* payload) {
    (void)payload;

    // int dropState = digitalRead(unopins::kDropSensorPin); // DISABLED
    BillDetector::Color color = billScanner != nullptr ? billScanner->getCurrentColor() : BillDetector::Color{0, 0, 0};
    bool gateOpen = billGate != nullptr ? billGate->isOpen() : false;

    printHardwareStatus(gateOpen, color);
}

void resetProcessingState() {
    billProcessing = false;
    billDetectionStartedAt = 0;
    if (billScanner != nullptr) billScanner->begin(); // Realignment
    Serial.println(F("[HW] State reset to IDLE."));
}

}  // namespace hardware_manager
}  // namespace uno
