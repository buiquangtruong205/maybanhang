#include "app_runtime.h"

#include <Arduino.h>

#include "config_manager.h"
#include "display_ui.h"
#include "input_manager.h"
#include "mqtt_manager.h"
#include "ota_manager.h"
#include "uno_comm.h"
#include "usb_console.h"
#include "vending_controller.h"
#include "wifi_manager.h"

namespace app_runtime {

namespace {

void onUnoEvent(const String& frame) {
    String eventName, payload;
    
    // Primary: Standard EVT: prefix
    if (frame.startsWith("EVT:")) {
        const int separator = frame.indexOf(':', 4);
        if (separator < 0) {
            eventName = frame.substring(4);
            payload = "";
        } else {
            eventName = frame.substring(4, separator);
            payload = frame.substring(separator + 1);
        }
        Serial.printf("[UNO PARSED] event=%s payload=%s\n", eventName.c_str(), payload.c_str());
        vending_controller::handleUnoEvent(eventName, payload);
    } 
    // Fallback: Search for EVT: anywhere in the frame (in case of leftover garbage)
    else if (frame.indexOf("EVT:") > 0) {
        int evtStart = frame.indexOf("EVT:");
        String cleanFrame = frame.substring(evtStart);
        Serial.printf("[UNO RECOVERED] cleaned=%s from raw=%s\n", cleanFrame.c_str(), frame.c_str());
        // Recursively parse the cleaned frame
        onUnoEvent(cleanFrame);
    }
    else if (frame.indexOf("PONG") >= 0) {
        vending_controller::handleUnoEvent("PONG", "UNO");
    } else {
        Serial.printf("[UNO IGNORED] %s\n", frame.c_str());
    }
}

void onMqttCommand(const String& cmd, const String& val) {
    vending_controller::handleMqttCommand(cmd, val);
}

void onConsoleCommand(const String& cmd) {
    vending_controller::handleConsoleCommand(cmd);
}

void handleWifiStateChange(bool connected) {
    vending_controller::handleWifiStateChange(connected);
}

}  // namespace

void setup() {
    Serial.begin(115200);
    Serial.println("\n[BOOT] ESP32 Vending Machine V3 Starting...");

    config_manager::init();

    displayui::init();
    displayui::showBooting();
    ota_manager::init();

    Serial.println("\nESP32 V3 Modular Controller Booting");

    wifi_manager::init();
    input_manager::init();
    uno_comm::init(onUnoEvent);
    mqtt_manager::init(onMqttCommand);
    usb_console::init(onConsoleCommand);
    vending_controller::init();

    Serial.println("[BOOT] ESP32 Logic ready");
}

void loop() {
    wifi_manager::loop();
    handleWifiStateChange(wifi_manager::isConnected());
    uno_comm::loop();
    mqtt_manager::loop();
    usb_console::loop();

    vending_controller::update();

    char key = input_manager::getKey();
    if (key) {
        vending_controller::handleKey(key);
    }

    delay(1);
}

}  // namespace app_runtime
