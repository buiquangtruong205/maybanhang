#include "hardware_manager.h"

#include <avr/wdt.h>
#include "bill_detector.h"
#include "gate_manager.h"
#include "motor_controller.h"
#include "pins.h"
#include "serial_protocol.h"

namespace uno {
namespace hardware_manager {

namespace {

MotorController* stepper1 = nullptr;
MotorController* stepper2 = nullptr;
BillDetector* billScanner = nullptr;
GateManager* billGate = nullptr;

bool billProcessing = false;
uint32_t billDetectionStartedAt = 0;
const uint32_t kBillDebounceMs = 2000;

void printInitStatus() {
    // Debug removed — Serial shared with ESP32
}

void printBillDetected(const BillDetector::Color& color) {
    (void)color; // Debug removed — Serial shared with ESP32
}

void printHardwareStatus(bool gateOpen, const BillDetector::Color& color) {
    (void)gateOpen; (void)color; // Debug removed — Serial shared with ESP32
}

}  // namespace

void init(MotorController* motor1, MotorController* motor2, BillDetector* detector, GateManager* gate) {
    stepper1 = motor1;
    stepper2 = motor2;
    billScanner = detector;
    billGate = gate;

    // pinMode(unopins::kDropSensorPin, INPUT_PULLUP); // DISABLED
    pinMode(unopins::kStatusLedPin, OUTPUT);
    digitalWrite(unopins::kStatusLedPin, HIGH);

    if (stepper1 != nullptr) stepper1->begin();
    if (stepper2 != nullptr) stepper2->begin();
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
            // Debouncing bill detection
        } else if (now - billDetectionStartedAt > 500) { // Slightly longer debounce for stability
            BillDetector::Color color = billScanner->getCurrentColor();
            printBillDetected(color);
            billGate->trigger();
            serial_protocol::sendEvent("CASH_INSERTED", "10000");
            billProcessing = true;
            billDetectionStartedAt = now;
        }
    } else if (!detected && billProcessing) {
        if (now - billDetectionStartedAt > kBillDebounceMs) {
            // Bill slot clear, ready for next
            billProcessing = false;
            billDetectionStartedAt = 0;
        }
    } else if (!detected) {
        billDetectionStartedAt = 0;
    }

    billGate->update();
}

void testMotor(const char* payload) {
    if (stepper1 == nullptr) {
        serial_protocol::sendEvent("ERROR", "MOTOR_NULL");
        return;
    }

    MotorController* target = nullptr;
    
    if (strcmp(payload, "1") == 0) {
        target = stepper1;
    } 
    else if (strcmp(payload, "2") == 0) {
        if (stepper2 != nullptr) {
            target = stepper2;
        } else {
            serial_protocol::sendEvent("ERROR", "STEPPER2_NULL");
            return;
        }
    }
    else {
        // Test both sequentially
        stepper1->move(2048, 5);
        while (stepper1->isMoving()) { wdt_reset(); stepper1->tick(); delay(1); }
        stepper1->stop();
        delay(500);
        if (stepper2 != nullptr) {
            stepper2->move(2048, 5);
            while (stepper2->isMoving()) { wdt_reset(); stepper2->tick(); delay(1); }
            stepper2->stop();
        }
        serial_protocol::sendEvent("ACK", "MOTOR_TEST_OK");
        return;
    }
    
    // Single motor test
    target->move(2048, 5);
    while (target->isMoving()) { wdt_reset(); target->tick(); delay(1); }
    target->stop();
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
    // Debug removed — Serial shared with ESP32
}

}  // namespace hardware_manager
}  // namespace uno
