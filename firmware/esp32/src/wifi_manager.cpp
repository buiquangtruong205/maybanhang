#include "wifi_manager.h"
#include "secrets.h"
#include "display_ui.h"

namespace wifi_manager {

namespace {
uint32_t lastWifiRetryAt = 0;
}

void init() {
    WiFi.mode(WIFI_STA);
    ensureConnected();
}

bool isConnected() {
    return WiFi.status() == WL_CONNECTED;
}

void ensureConnected() {
    if (isConnected()) {
        return;
    }

    const uint32_t now = millis();
    if (now - lastWifiRetryAt < 5000) {
        return;
    }
    lastWifiRetryAt = now;

    Serial.printf("[WIFI] Connecting to %s\n", WIFI_SSID);
    displayui::showWifiConnecting(WIFI_SSID);
    
    WiFi.begin(WIFI_SSID, WIFI_PASSWORD);

    // Note: We don't block here in the loop, but in the first connection attempt during setup we might
}

void loop() {
    ensureConnected();
    
    static bool lastState = false;
    bool currentState = isConnected();
    
    if (currentState && !lastState) {
        Serial.printf("[WIFI] Connected. IP=%s\n", WiFi.localIP().toString().c_str());
        displayui::showWifiReady(WiFi.localIP());
        delay(1000);
        displayui::showIdle();
    } else if (!currentState && lastState) {
        Serial.println("[WIFI] Connection lost");
    }
    
    lastState = currentState;
}

IPAddress getLocalIP() {
    return WiFi.localIP();
}

}  // namespace wifi_manager
