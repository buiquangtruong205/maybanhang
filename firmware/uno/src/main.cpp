#include <Arduino.h>
#include <avr/wdt.h>

#include "bill_detector.h"
#include "dispense_controller.h"
#include "gate_manager.h"
#include "hardware_manager.h"
#include "motor_controller.h"
#include "pins.h"
#include "protocol.h"
#include "serial_protocol.h"

namespace {

uno::MotorController stepper(unopins::kStepperIn1, unopins::kStepperIn2, unopins::kStepperIn3, unopins::kStepperIn4);
uno::BillDetector billScanner(unopins::kColorS0, unopins::kColorS1, unopins::kColorS2, unopins::kColorS3, unopins::kColorOut);
uno::GateManager billGate(unopins::kServoPin);

void handleDispenseCommand(const char* payload) {
    uno::dispense_controller::run(payload);
}

void handleTestMotorCommand(const char* payload) {
    uno::hardware_manager::testMotor(payload);
}

void handleTestServoCommand(const char* payload) {
    uno::hardware_manager::testServo(payload);
}

void handleStatusCommand(const char* payload) {
    uno::hardware_manager::printStatus(payload);
}

}  // namespace

void setup() {
    Serial.begin(protocol::kBaudRate);
    
    // Enable AVR watchdog (8 seconds)
    wdt_enable(WDTO_8S);
    
    uno::dispense_controller::init(&stepper);
    uno::hardware_manager::init(&stepper, &billScanner, &billGate);
    uno::serial_protocol::init(
        handleDispenseCommand, 
        handleTestMotorCommand, 
        handleTestServoCommand, 
        handleStatusCommand
    );
    
    Serial.println("");
    Serial.println("================================");
    Serial.println("  VENDING MACHINE UNO V3 READY  ");
    Serial.println("================================");
    uno::serial_protocol::sendEvent("READY", "UNO_V3");
}

void loop() {
    // Feed the watchdog
    wdt_reset();
    
    // Pump communication and hardware updates
    uno::serial_protocol::pump();
    uno::hardware_manager::update();
    stepper.tick();
    
    delay(2);
}
