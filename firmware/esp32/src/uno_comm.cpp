#include "uno_comm.h"
#include <HardwareSerial.h>
#include "app_config.h"

namespace uno_comm {

namespace {
HardwareSerial ioSerial(2);
String inboundFrame;
EventCallback onEventReceived = nullptr;
}

void init(EventCallback callback) {
    onEventReceived = callback;
    ioSerial.begin(protocol::kBaudRate, SERIAL_8N1, esp32cfg::kUartRxPin, esp32cfg::kUartTxPin);
    Serial.printf("[UNO] UART ready | baud=%lu rx=%d tx=%d\n",
                  (unsigned long)protocol::kBaudRate, esp32cfg::kUartRxPin, esp32cfg::kUartTxPin);
}

void sendCommand(protocol::CommandType type, const String& payload) {
    const String frame = protocol::toCommandFrame(type, payload);
    Serial.printf("[UNO] TX %s\n", frame.c_str());
    ioSerial.print(frame);
    ioSerial.print(protocol::kFrameTerminator);
}

void loop() {
    while (ioSerial.available() > 0) {
        char ch = static_cast<char>(ioSerial.read());
        if (ch == protocol::kFrameTerminator) {
            String frame = protocol::normalizeFrame(inboundFrame);
            inboundFrame = "";
            if (frame.length() > 0 && onEventReceived) {
                Serial.printf("[UNO] RX %s\n", frame.c_str());
                onEventReceived(frame);
            }
            continue;
        }
        inboundFrame += ch;
    }
}

}  // namespace uno_comm
