#include "wifi_manager.h"
#include <WiFiManager.h>
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

void saveConfigCallback() {
    Serial.println("[WIFI] Should save config");
    shouldSaveConfig = true;
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
    wm.setParamsPage(true); // Show params on first page
    wm.setBreakAfterConfig(true);

    if (forceConfigPortal) {
        Serial.println("[WIFI] Reset requested from BOOT button");
        wm.resetSettings();
        config_manager::clearConfig();
    }

    Serial.println(forceConfigPortal ? "[WIFI] Starting Config Portal..." : "[WIFI] Starting AutoConnect...");
    Serial.printf("[WIFI] Config | api=%s mqtt=%s key_len=%u\n",
                  cfg.apiBaseUrl.c_str(),
                  cfg.mqttBroker.c_str(),
                  (unsigned int)cfg.machineKey.length());
    displayui::showWifiConnecting("Captive Portal");

    bool wifiReady = false;
    if (forceConfigPortal) {
        wifiReady = wm.startConfigPortal("Vending-Setup");
    } else {
        wifiReady = wm.autoConnect("Vending-Setup");
    }

    if (!wifiReady) {
        Serial.println("[WIFI] Failed to connect or config portal timed out");
        delay(3000);
        ESP.restart();
    }

    // 3. Save parameters if changed
    if (shouldSaveConfig) {
        persistCustomConfig(cfg);
        Serial.println("[WIFI] Configuration updated, restarting...");
        delay(1000);
        ESP.restart();
    }

    Serial.println("[WIFI] Connected successfully!");
    Serial.printf("[WIFI] IP=%s SSID=%s\n", WiFi.localIP().toString().c_str(), WiFi.SSID().c_str());
    displayui::showWifiReady(WiFi.localIP());
    delay(1000);
    displayui::showHome(config_manager::getAccumulatedCash(), true);
}

bool isConnected() {
    return WiFi.status() == WL_CONNECTED;
}

void loop() {
    if (WiFi.status() == WL_CONNECTED) {
        disconnectedAt = 0;
        if (isApModeActive) {
            Serial.println("[WIFI] Reconnected, closing AP...");
            isApModeActive = false;
        }
    } else {
        if (disconnectedAt == 0) disconnectedAt = millis();
        
        if (!isApModeActive && (millis() - disconnectedAt > kApTimeoutMs)) {
            Serial.println("[WIFI] Connection lost for > 2 mins. Starting Config Portal...");
            displayui::showError("MAT KET NOI", "Bat dau AP Mode...");
            isApModeActive = true;
            wm.setConfigPortalTimeout(300); // 5 mins
            shouldSaveConfig = false;
            wm.startConfigPortal("Vending-Setup", "12345678");
            isApModeActive = false; // Reset if portal finishes
            if (shouldSaveConfig) {
                persistCustomConfig(config_manager::getConfig());
                Serial.println("[WIFI] Configuration updated from AP mode, restarting...");
                delay(1000);
                ESP.restart();
            }
            disconnectedAt = millis(); // Reset timer
        }
    }
}

IPAddress getLocalIP() {
    return WiFi.localIP();
}

} // namespace wifi_manager
