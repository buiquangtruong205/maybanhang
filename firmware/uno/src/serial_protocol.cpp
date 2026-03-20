#include "serial_protocol.h"

#include "protocol.h"

namespace uno {
namespace serial_protocol {

namespace {

ActionCallback dispenseCallback = nullptr;
ActionCallback testMotorCallback = nullptr;
ActionCallback testServoCallback = nullptr;
ActionCallback statusCallback = nullptr;
String inboundFrame;

void printFormatted(const char* format, const String& value) {
    // char buffer[96];
    // snprintf(buffer, sizeof(buffer), format, value.c_str());
    // Serial.println(buffer);
}

void printFormatted(const char* format, const String& first, const String& second) {
    // char buffer[128];
    // snprintf(buffer, sizeof(buffer), format, first.c_str(), second.c_str());
    // Serial.println(buffer);
}

void handleCommand(const String& frame) {
    String normalized = frame;
    normalized.trim();
    String upper = normalized;
    upper.toUpperCase();

    if (frame.startsWith("CMD:PING:")) {
        Serial.println("[SYSTEM] Uno is ALIVE (responding to ESP32)");
        sendEvent("PONG", "UNO");
        return;
    }

    if (frame.startsWith("CMD:DISPENSE:")) {
        printFormatted("[SERIAL] RX protocol DISPENSE: %s", frame);
        if (dispenseCallback != nullptr) {
            dispenseCallback(frame.substring(String("CMD:DISPENSE:").length()));
        }
        return;
    }

    if (frame.startsWith("CMD:TEST_MOTOR:")) {
        printFormatted("[SERIAL] RX protocol TEST_MOTOR: %s", frame);
        if (testMotorCallback != nullptr) {
            testMotorCallback(frame.substring(String("CMD:TEST_MOTOR:").length()));
        }
        return;
    }

    if (frame.startsWith("CMD:TEST_SERVO:")) {
        printFormatted("[SERIAL] RX protocol TEST_SERVO: %s", frame);
        if (testServoCallback != nullptr) {
            testServoCallback(frame.substring(String("CMD:TEST_SERVO:").length()));
        }
        return;
    }

    if (upper == "HELP") {
        Serial.println("[UNO TEST] Commands:");
        Serial.println("  HELP");
        Serial.println("  STATUS");
        Serial.println("  PING");
        Serial.println("  DISPENSE A1");
        Serial.println("  TEST MOTOR");
        Serial.println("  TEST SERVO");
        return;
    }

    if (upper == "STATUS") {
        if (statusCallback != nullptr) {
            statusCallback("");
        }
        return;
    }

    if (upper == "PING") {
        Serial.println("[SERIAL] RX direct PING");
        sendEvent("PONG", "UNO_DIRECT");
        return;
    }

    if (upper.startsWith("DISPENSE")) {
        if (dispenseCallback != nullptr) {
            String payload = normalized.length() > 8 ? normalized.substring(8) : "";
            payload.trim();
            if (payload.length() == 0) payload = "standard|A1";
            else if (payload.indexOf('|') < 0) payload = "standard|" + payload;
            printFormatted("[SERIAL] RX direct DISPENSE: %s", payload);
            dispenseCallback(payload);
        }
        return;
    }

    if (upper.startsWith("TEST MOTOR")) {
        if (testMotorCallback != nullptr) {
            String payload = normalized.length() > 10 ? normalized.substring(10) : "";
            payload.trim();
            if (payload.length() == 0) payload = "standard|TEST";
            else if (payload.indexOf('|') < 0) payload = "standard|" + payload;
            printFormatted("[SERIAL] RX direct TEST MOTOR: %s", payload);
            testMotorCallback(payload);
        }
        return;
    }

    if (upper.startsWith("TEST SERVO")) {
        if (testServoCallback != nullptr) {
            Serial.println("[SERIAL] RX direct TEST SERVO");
            testServoCallback("DIRECT");
        }
        return;
    }

    sendEvent("ERROR", "UNKNOWN_COMMAND");
}

}  // namespace

void init(ActionCallback onDispense, ActionCallback onTestMotor, ActionCallback onTestServo, ActionCallback onStatus) {
    dispenseCallback = onDispense;
    testMotorCallback = onTestMotor;
    testServoCallback = onTestServo;
    statusCallback = onStatus;
    inboundFrame = "";
}

void sendEvent(const String& eventName, const String& payload) {
    // printFormatted("[SERIAL] TX EVT:%s:%s", eventName, payload);
    Serial.print("EVT:");
    Serial.print(eventName);
    Serial.print(":");
    Serial.println(payload);
}

void pump() {
    static uint32_t lastIdleLog = 0;
    if (millis() - lastIdleLog > 30000) {
        lastIdleLog = millis();
        Serial.println("[SYSTEM] Uno is idle and waiting for commands...");
    }
    while (Serial.available() > 0) {
        const char ch = static_cast<char>(Serial.read());
        if (ch == protocol::kFrameTerminator) {
            String frame = protocol::normalizeFrame(inboundFrame);
            inboundFrame = "";
            if (frame.length() > 0) {
                printFormatted("[SERIAL] RX line: %s", frame);
                handleCommand(frame);
            }
            continue;
        }
        inboundFrame += ch;
    }
}

}  // namespace serial_protocol
}  // namespace uno
