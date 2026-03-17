#pragma once

#include <Arduino.h>

namespace protocol {

static constexpr uint32_t kBaudRate = 115200;
static constexpr char kFrameTerminator = '\n';

enum class CommandType : uint8_t {
    None,
    Ping,
    Dispense,
    TestMotor,
    Lock,
    Unlock,
    ResetAlarm,
};

enum class EventType : uint8_t {
    None,
    Ready,
    Pong,
    Ack,
    DispenseOk,
    DispenseFail,
    DropDetected,
    DoorOpened,
    DoorClosed,
    Error,
};

inline String toCommandFrame(CommandType type, const String& payload = "") {
    switch (type) {
        case CommandType::Ping:
            return "CMD:PING:" + payload;
        case CommandType::Dispense:
            return "CMD:DISPENSE:" + payload;
        case CommandType::TestMotor:
            return "CMD:TEST_MOTOR:" + payload;
        case CommandType::Lock:
            return "CMD:LOCK:" + payload;
        case CommandType::Unlock:
            return "CMD:UNLOCK:" + payload;
        case CommandType::ResetAlarm:
            return "CMD:RESET_ALARM:" + payload;
        default:
            return "CMD:NONE:";
    }
}

inline bool isCommandFrame(const String& frame) {
    return frame.startsWith("CMD:");
}

inline bool isEventFrame(const String& frame) {
    return frame.startsWith("EVT:");
}

inline String normalizeFrame(String frame) {
    frame.trim();
    return frame;
}

}  // namespace protocol
