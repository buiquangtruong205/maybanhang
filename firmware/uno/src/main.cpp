#include <Arduino.h>

#include "pins.h"
#include "protocol.h"

namespace {

constexpr int kStepDelayMs = 5;
constexpr int kDispenseSteps = 4096;

const uint8_t kMotorSteps[8][4] = {
    {1, 0, 0, 0},
    {1, 1, 0, 0},
    {0, 1, 0, 0},
    {0, 1, 1, 0},
    {0, 0, 1, 0},
    {0, 0, 1, 1},
    {0, 0, 0, 1},
    {1, 0, 0, 1},
};

String inboundFrame;

void sendEvent(const String& eventName, const String& payload = "") {
    Serial.print("EVT:");
    Serial.print(eventName);
    Serial.print(":");
    Serial.println(payload);
}

void writeMotorStep(uint8_t stepIndex) {
    digitalWrite(unopins::kStepperIn1, kMotorSteps[stepIndex][0]);
    digitalWrite(unopins::kStepperIn2, kMotorSteps[stepIndex][1]);
    digitalWrite(unopins::kStepperIn3, kMotorSteps[stepIndex][2]);
    digitalWrite(unopins::kStepperIn4, kMotorSteps[stepIndex][3]);
}

void releaseMotor() {
    digitalWrite(unopins::kStepperIn1, LOW);
    digitalWrite(unopins::kStepperIn2, LOW);
    digitalWrite(unopins::kStepperIn3, LOW);
    digitalWrite(unopins::kStepperIn4, LOW);
}

void rotateClockwise(int totalSteps) {
    for (int i = 0; i < totalSteps; ++i) {
        writeMotorStep(i % 8);
        delay(kStepDelayMs);
    }
    releaseMotor();
}

void rotateCounterClockwise(int totalSteps) {
    for (int i = 0; i < totalSteps; ++i) {
        writeMotorStep((7 - (i % 8)));
        delay(kStepDelayMs);
    }
    releaseMotor();
}

void initializePins() {
    pinMode(unopins::kDropSensorPin, INPUT_PULLUP);
    pinMode(unopins::kDoorSwitchPin, INPUT_PULLUP);
    pinMode(unopins::kStepperIn1, OUTPUT);
    pinMode(unopins::kStepperIn2, OUTPUT);
    pinMode(unopins::kStepperIn3, OUTPUT);
    pinMode(unopins::kStepperIn4, OUTPUT);
    pinMode(unopins::kLockRelayPin, OUTPUT);
    pinMode(unopins::kStatusLedPin, OUTPUT);

    digitalWrite(unopins::kLockRelayPin, LOW);
    digitalWrite(unopins::kStatusLedPin, HIGH);
    releaseMotor();
}

void runDispense(const String& payload) {
    Serial.print("[MOTOR] DISPENSE payload: ");
    Serial.println(payload);
    rotateClockwise(kDispenseSteps);
    sendEvent("DISPENSE_OK", payload.length() > 0 ? payload : "MOTOR_DONE");
}

void handleCommand(const String& frame) {
    if (frame.startsWith("CMD:PING:")) {
        sendEvent("PONG", "UNO");
        return;
    }

    if (frame.startsWith("CMD:DISPENSE:")) {
        runDispense(frame.substring(String("CMD:DISPENSE:").length()));
        return;
    }

    if (frame.startsWith("CMD:TEST_MOTOR:")) {
        rotateClockwise(kDispenseSteps);
        delay(1000);
        rotateCounterClockwise(kDispenseSteps);
        sendEvent("ACK", "TEST_MOTOR_DONE");
        return;
    }

    if (frame.startsWith("CMD:LOCK:")) {
        digitalWrite(unopins::kLockRelayPin, HIGH);
        sendEvent("ACK", "LOCK");
        return;
    }

    if (frame.startsWith("CMD:UNLOCK:")) {
        digitalWrite(unopins::kLockRelayPin, LOW);
        sendEvent("ACK", "UNLOCK");
        return;
    }

    if (frame.startsWith("CMD:RESET_ALARM:")) {
        digitalWrite(unopins::kLockRelayPin, LOW);
        releaseMotor();
        sendEvent("ACK", "RESET_ALARM");
        return;
    }

    sendEvent("ERROR", "UNKNOWN_COMMAND");
}

void pumpMasterSerial() {
    while (Serial.available() > 0) {
        const char ch = static_cast<char>(Serial.read());
        if (ch == protocol::kFrameTerminator) {
            String frame = protocol::normalizeFrame(inboundFrame);
            inboundFrame = "";
            if (frame.length() > 0) {
                handleCommand(frame);
            }
            continue;
        }
        inboundFrame += ch;
    }
}

}  // namespace

void setup() {
    Serial.begin(protocol::kBaudRate);
    initializePins();
    Serial.println("[BOOT] UNO ready");
    sendEvent("READY", "UNO_V3");
}

void loop() {
    pumpMasterSerial();
    delay(2);
}
