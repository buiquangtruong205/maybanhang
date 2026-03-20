#include "usb_console.h"
#include "protocol.h"

namespace usb_console {

namespace {
String usbConsoleBuffer;
ConsoleCommandCallback onCommandReceived = nullptr;
}

void init(ConsoleCommandCallback callback) {
    onCommandReceived = callback;
    Serial.println("[USB] Console ready. Type HELP for commands.");
}

void loop() {
    while (Serial.available() > 0) {
        const char ch = static_cast<char>(Serial.read());
        // Echo for debug
        Serial.printf("[DEBUG USB] char: '%c' (0x%02x)\n", ch, ch);
        
        if (ch == '\n' || ch == '\r') {
            String command = protocol::normalizeFrame(usbConsoleBuffer);
            usbConsoleBuffer = "";
            if (command.length() > 0 && onCommandReceived) {
                Serial.printf("[USB] RX command: %s\n", command.c_str());
                onCommandReceived(command);
            }
            continue;
        }
        usbConsoleBuffer += ch;
    }
}

}  // namespace usb_console
