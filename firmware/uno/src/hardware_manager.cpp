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
    snprintf(buffer, sizeof(buffer), "[HW] Init complete | drop_sensor=%d led=%d servo=%d",
             unopins::kDropSensorPin, unopins::kStatusLedPin, unopins::kServoPin);
    Serial.println(buffer);
}

void printBillDetected(const BillDetector::Color& color) {
    char buffer[96];
    snprintf(buffer, sizeof(buffer), "[BILL] 10k detected | R=%d G=%d B=%d", color.r, color.g, color.b);
    Serial.println(buffer);
}

void printHardwareStatus(int dropState, bool gateOpen, const BillDetector::Color& color) {
    char buffer[112];
    snprintf(buffer, sizeof(buffer), "[HW STATUS] drop=%s gate=%s bill_processing=%d rgb=(%d,%d,%d)",
             dropState == LOW ? "LOW" : "HIGH",
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

    pinMode(unopins::kDropSensorPin, INPUT_PULLUP);
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
        } else if (now - billDetectionStartedAt > 100) {
            BillDetector::Color color = billScanner->getCurrentColor();
            printBillDetected(color);
            billGate->trigger();
            serial_protocol::sendEvent("CASH_INSERTED", "10000");
            billProcessing = true;
            billDetectionStartedAt = now;
        }
    } else if (!detected && billProcessing) {
        if (now - billDetectionStartedAt > kBillDebounceMs) {
            billProcessing = false;
            billDetectionStartedAt = 0;
        }
    } else if (!detected) {
        billDetectionStartedAt = 0;
    }

    billGate->update();
}

void testMotor(const String& payload) {
    if (stepper == nullptr) {
        serial_protocol::sendEvent("ERROR", "STEPPER_NOT_INITIALIZED");
        return;
    }

    Serial.print("[MOTOR] TEST_MOTOR payload: ");
    Serial.println(payload);
    stepper->rotateClockwise(4096, 5);
    delay(1000);
    stepper->rotateCounterClockwise(4096, 5);
    serial_protocol::sendEvent("ACK", "TEST_MOTOR_DONE");
}

void testServo(const String& payload) {
    (void)payload;

    if (billGate == nullptr) {
        serial_protocol::sendEvent("ERROR", "GATE_NOT_INITIALIZED");
        return;
    }

    billGate->trigger();
    serial_protocol::sendEvent("ACK", "TEST_SERVO_STARTED");
}

void printStatus(const String& payload) {
    (void)payload;

    int dropState = digitalRead(unopins::kDropSensorPin);
    BillDetector::Color color = billScanner != nullptr ? billScanner->getCurrentColor() : BillDetector::Color{0, 0, 0};
    bool gateOpen = billGate != nullptr ? billGate->isOpen() : false;

    printHardwareStatus(dropState, gateOpen, color);
}

}  // namespace hardware_manager
}  // namespace uno
