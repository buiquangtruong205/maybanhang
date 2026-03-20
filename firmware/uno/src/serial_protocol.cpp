#include "serial_protocol.h"

#include "protocol.h"
#include "hardware_manager.h"

namespace uno {
namespace serial_protocol {

namespace {

ActionCallback dispenseCallback = nullptr;
ActionCallback testMotorCallback = nullptr;
ActionCallback testServoCallback = nullptr;
ActionCallback statusCallback = nullptr;
const int kMaxFrameLen = 64;
char inboundBuffer[kMaxFrameLen];
int inboundPos = 0;

void printFormatted(const char* prefix, const char* value) {
    Serial.print(prefix);
    Serial.println(value);
}

void printFormatted(const char* prefix, const char* first, const char* second) {
    Serial.print(prefix);
    Serial.print(first);
    Serial.print(":");
    Serial.println(second);
}

void handleCommand(char* frame) {
    // Basic normalization: trim right
    int len = strlen(frame);
    while (len > 0 && isspace(frame[len-1])) {
        frame[--len] = '\0';
    }

    // Convert to uppercase for comparison
    char upper[kMaxFrameLen];
    strncpy(upper, frame, kMaxFrameLen);
    for (int i = 0; upper[i]; i++) upper[i] = toupper(upper[i]);

    // 1. Protocol Commands (CMD:...)
    if (strncmp(upper, "CMD:PING:", 9) == 0) {
        Serial.println(F("[SERIAL] PING received"));
        sendEvent("PONG", "UNO");
        return;
    }

    if (strncmp(upper, "CMD:DISPENSE:", 13) == 0) {
        printFormatted("[SERIAL] RX DISPENSE: ", frame + 13);
        if (dispenseCallback != nullptr) dispenseCallback(frame + 13);
        return;
    }

    if (strncmp(upper, "CMD:TEST_MOTOR:", 15) == 0) {
        printFormatted("[SERIAL] RX TEST_MOTOR: ", frame + 15);
        if (testMotorCallback != nullptr) testMotorCallback(frame + 15);
        return;
    }

    if (strncmp(upper, "CMD:TEST_SERVO:", 15) == 0) {
        printFormatted("[SERIAL] RX TEST_SERVO: ", frame + 15);
        if (testServoCallback != nullptr) testServoCallback(frame + 15);
        return;
    }

    // 2. Direct / Debug Commands
    if (strcmp(upper, "HELP") == 0) {
        Serial.println(F("[UNO] Commands: HELP | STATUS | PING | IDLE | MOTOR | SERVO | PAY"));
        return;
    }

    if (strcmp(upper, "STATUS") == 0) {
        if (statusCallback != nullptr) statusCallback("");
        return;
    }

    if (strcmp(upper, "PING") == 0) {
        sendEvent("PONG", "DIRECT");
        return;
    }

    if (strncmp(upper, "MOTOR", 5) == 0) {
        if (testMotorCallback != nullptr) {
            char* payload = frame + 5;
            while (*payload && isspace(*payload)) payload++;
            testMotorCallback(payload);
        }
        return;
    }

    if (strncmp(upper, "SERVO", 5) == 0) {
        if (testServoCallback != nullptr) testServoCallback("DIRECT");
        return;
    }

    if (strncmp(upper, "PAY", 3) == 0 || strncmp(upper, "DISPENSE", 8) == 0) {
        if (dispenseCallback != nullptr) {
            char* payload = frame + (strncmp(upper, "PAY", 3) == 0 ? 3 : 8);
            while (*payload && isspace(*payload)) payload++;
            dispenseCallback(payload);
        }
        return;
    }

    if (strcmp(upper, "IDLE") == 0) {
        uno::hardware_manager::resetProcessingState();
        return;
    }

    sendEvent("ERROR", "UNKNOWN");
}

}  // namespace

void init(ActionCallback onDispense, ActionCallback onTestMotor, ActionCallback onTestServo, ActionCallback onStatus) {
    dispenseCallback = onDispense;
    testMotorCallback = onTestMotor;
    testServoCallback = onTestServo;
    statusCallback = onStatus;
    inboundPos = 0;
}

void sendEvent(const char* eventName, const char* payload) {
    printFormatted("[SERIAL] TX -> EVT:", eventName, payload);
    Serial.print(F("EVT:"));
    Serial.print(eventName);
    Serial.print(F(":"));
    Serial.println(payload);
}

void pump() {
    static uint32_t lastIdleLog = 0;
    static uint32_t lastCharReceivedAt = 0;
    const uint32_t kInboundTimeoutMs = 500;

    if (millis() - lastIdleLog > 30000) {
        lastIdleLog = millis();
        Serial.println(F("[SYSTEM] Uno is idle and waiting..."));
    }

    while (Serial.available() > 0) {
        const char ch = static_cast<char>(Serial.read());
        lastCharReceivedAt = millis();

        if (ch == protocol::kFrameTerminator || ch == '\r') {
            if (inboundPos > 0) {
                inboundBuffer[inboundPos] = '\0';
                printFormatted("[SERIAL] RX line: ", inboundBuffer);
                handleCommand(inboundBuffer);
                inboundPos = 0;
            }
            continue;
        }

        if (inboundPos < kMaxFrameLen - 1) {
            inboundBuffer[inboundPos++] = ch;
        }
    }

    if (inboundPos > 0 && (millis() - lastCharReceivedAt > kInboundTimeoutMs)) {
        inboundBuffer[inboundPos] = '\0';
        printFormatted("[SERIAL] RX timeout: ", inboundBuffer);
        handleCommand(inboundBuffer);
        inboundPos = 0;
    }
}

}  // namespace serial_protocol
}  // namespace uno
