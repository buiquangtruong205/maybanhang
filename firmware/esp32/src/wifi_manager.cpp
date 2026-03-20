#include "wifi_manager.h"
#include <WiFi.h>
#include <WiFiManager.h>
#include <WebServer.h>
#include "app_config.h"
#include "config_manager.h"
#include "display_ui.h"

namespace wifi_manager {

namespace {
WiFiManager wm;
bool shouldSaveConfig = false;
bool forceConfigPortal = false;

// Custom parameters pointers
WiFiManagerParameter* custom_machine_key;
WiFiManagerParameter* custom_api_url;
WiFiManagerParameter* custom_mqtt_ip;

uint32_t disconnectedAt = 0;
bool isApModeActive = false;
constexpr uint32_t kApTimeoutMs = 120000; // 2 minutes
bool isInitialConfiguring = false;

void saveConfigCallback() {
    Serial.println("[WIFI] Configuration change detected");
    shouldSaveConfig = true;
}

void webServerCallback() {
    if (wm.server) {
        // Silencing rogue requests to save CPU and avoid noise
        wm.server->onNotFound([]() {
            if (wm.server) {
                wm.server->send(200, "text/plain", "OK");
            }
        });
    }
}


void persistCustomConfig(const config_manager::Config& baseCfg) {
    if (!shouldSaveConfig) {
        return;
    }

    config_manager::Config newCfg = baseCfg;
    newCfg.machineKey = custom_machine_key->getValue();
    newCfg.apiBaseUrl = custom_api_url->getValue();
    newCfg.mqttBroker = custom_mqtt_ip->getValue();

    // machine_id, MQTT topics, UI layout, and profile are backend-managed.
    // Clear them when the target backend or broker changes to avoid stale routing.
    if (newCfg.machineKey != baseCfg.machineKey ||
        newCfg.apiBaseUrl != baseCfg.apiBaseUrl ||
        newCfg.mqttBroker != baseCfg.mqttBroker) {
        newCfg.machineId = "";
        newCfg.machineName = "";
        newCfg.mqttCommandTopic = "";
        newCfg.mqttStatusTopic = "";
        newCfg.mqttBroadcastTopic = "";
        newCfg.uiLayoutJson = "";
        newCfg.deviceProfileJson = "";
    }

    config_manager::saveConfig(newCfg);
    shouldSaveConfig = false;
}

bool bootButtonPressed() {
    return digitalRead(esp32cfg::kBootButtonPin) == LOW;
}

bool detectResetRequest() {
    pinMode(esp32cfg::kBootButtonPin, INPUT_PULLUP);

    if (!bootButtonPressed()) {
        return false;
    }

    const uint32_t startAt = millis();
    Serial.println("[WIFI] BOOT button detected, hold to reset WiFi/profile...");
    displayui::showLoading("GIU NUT BOOT", "De reset cau hinh");

    while (millis() - startAt < esp32cfg::kBootResetHoldMs) {
        if (!bootButtonPressed()) {
            Serial.println("[WIFI] BOOT released before timeout, skip reset");
            return false;
        }
        delay(50);
    }

    return true;
}

void checkBootButtonRuntime() {
    static uint32_t pressStart = 0;
    static bool isPressing = false;

    if (bootButtonPressed()) {
        if (!isPressing) {
            isPressing = true;
            pressStart = millis();
            Serial.println("[WIFI] BOOT button pressed, holding to reset...");
            displayui::showLoading("GIU NUT BOOT", "De reset cau hinh");
        } else if (millis() - pressStart >= esp32cfg::kBootResetHoldMs) {
            Serial.println("[WIFI] BOOT button held for 4s, resetting config and restarting...");
            wm.resetSettings();
            config_manager::clearConfig();
            delay(500);
            ESP.restart();
        }
    } else {
        if (isPressing) {
            isPressing = false;
            Serial.println("[WIFI] BOOT button released before timeout, resuming...");
            // Cap nhat lai man hinh chinh ngay khi tha tay
            displayui::showHome(0, true);
        }
    }
}
}

void init() {
    shouldSaveConfig = false;
    forceConfigPortal = detectResetRequest();

    // 1. Load existing config
    config_manager::Config cfg = config_manager::getConfig();

    // 2. Prepare custom parameters for Web UI
    custom_machine_key = new WiFiManagerParameter("m_key", "Secret Key (from Admin)", cfg.machineKey.c_str(), 40);
    custom_api_url = new WiFiManagerParameter("api", "API URL (http://ip:5000/api)", cfg.apiBaseUrl.c_str(), 100);
    custom_mqtt_ip = new WiFiManagerParameter("mqtt", "MQTT Broker IP (optional)", cfg.mqttBroker.c_str(), 40);

    wm.addParameter(custom_machine_key);
    wm.addParameter(custom_api_url);
    wm.addParameter(custom_mqtt_ip);

    wm.setSaveConfigCallback(saveConfigCallback);
    wm.setWebServerCallback(webServerCallback);
    wm.setParamsPage(true); // Show params on first page
    wm.setBreakAfterConfig(true);
    wm.setConfigPortalBlocking(false);

    if (forceConfigPortal) {
        Serial.println("[WIFI] Manual portal requested via BOOT button");
        wm.startConfigPortal("Vending-Setup", "12345678");
        isInitialConfiguring = true;
    } else {
        Serial.println("[WIFI] Attempting AutoConnect (Non-blocking)...");
        wm.autoConnect("Vending-Setup", "12345678");
        if (WiFi.status() != WL_CONNECTED) {
            isInitialConfiguring = true;
        }
    }

    Serial.println("[WIFI] Init finished, returning to core setup (Async Mode)");
}

bool isConnected() {
    return WiFi.status() == WL_CONNECTED;
}

void loop() {
    checkBootButtonRuntime();

    // Luôn xử lý WiFiManager nếu đang trong trạng thái Config hoặc AP
    if (isInitialConfiguring || isApModeActive) {
        wm.process();
        delay(1); 
    }

    if (shouldSaveConfig) {
        persistCustomConfig(config_manager::getConfig());
        Serial.println("[WIFI] Configuration saved, restarting...");
        delay(1000);
        ESP.restart();
    }

    if (WiFi.status() == WL_CONNECTED) {
        disconnectedAt = 0;
        if (isInitialConfiguring) {
            Serial.println("[WIFI] Initial configuration/connection complete");
            isInitialConfiguring = false;
            displayui::showHome(config_manager::getAccumulatedCash(), true);
        }
        if (isApModeActive) {
            Serial.println("[WIFI] Reconnected, closing AP...");
            wm.stopConfigPortal();
            isApModeActive = false;
        }
    } else {
        if (disconnectedAt == 0) disconnectedAt = millis();
        
        if (!isInitialConfiguring && !isApModeActive && (millis() - disconnectedAt > kApTimeoutMs)) {
            Serial.println("[WIFI] Connection lost for > 2 mins. Starting Config Portal...");
            displayui::showError("MAT KET NOI", "Bat dau AP Mode...");
            isApModeActive = true;
            wm.setConfigPortalBlocking(false);
            wm.startConfigPortal("Vending-Setup", "12345678");
            disconnectedAt = millis();
        }
    }
}

IPAddress getLocalIP() {
    return WiFi.localIP();
}

} // namespace wifi_manager
