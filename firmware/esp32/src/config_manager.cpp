#include "config_manager.h"
#include <Preferences.h>
#include <ArduinoJson.h>
#include "app_config.h"
#include "secrets.h"

namespace config_manager {

namespace {
Preferences prefs;
const char* kNamespace = "vending_cfg";

// Keys for NVS
const char* kKeyId = "m_id";
const char* kKeyName = "m_name";
const char* kKeyKey = "m_key";
const char* kKeyApi = "api_url";
const char* kKeyMqtt = "mqtt_ip";
const char* kKeyMqttPort = "mqtt_port";
const char* kKeyMqttCmd = "mqtt_cmd";
const char* kKeyMqttStatus = "mqtt_stat";
const char* kKeyMqttBroadcast = "mqtt_bcast";
const char* kKeyUiLayout = "ui_layout";
const char* kKeyDevProfile = "dev_profile";
const char* kKeyCashAcc = "cash_acc";

String readJsonString(const char* key) {
    if (!prefs.isKey(key)) return "";
    return prefs.getString(key, "");
}

String getJsonStringValue(const String& rawJson, const char* key, const String& fallback = "") {
    if (rawJson.isEmpty()) return fallback;

    JsonDocument doc;
    if (deserializeJson(doc, rawJson) != DeserializationError::Ok) {
        return fallback;
    }

    const char* value = doc[key] | nullptr;
    return value ? String(value) : fallback;
}

bool getJsonBoolValue(const String& rawJson, const char* key, bool fallback) {
    if (rawJson.isEmpty()) return fallback;

    JsonDocument doc;
    if (deserializeJson(doc, rawJson) != DeserializationError::Ok) {
        return fallback;
    }

    if (doc[key].isNull()) return fallback;
    return doc[key].as<bool>();
}

int getJsonIntValue(const String& rawJson, const char* key, int fallback) {
    if (rawJson.isEmpty()) return fallback;

    JsonDocument doc;
    if (deserializeJson(doc, rawJson) != DeserializationError::Ok) {
        return fallback;
    }

    if (doc[key].isNull()) return fallback;
    return doc[key].as<int>();
}
}

void init() {
    prefs.begin(kNamespace, false);
}

void saveConfig(const Config& newConfig) {
    prefs.putString(kKeyId, newConfig.machineId);
    prefs.putString(kKeyName, newConfig.machineName);
    prefs.putString(kKeyKey, newConfig.machineKey);
    prefs.putString(kKeyApi, newConfig.apiBaseUrl);
    prefs.putString(kKeyMqtt, newConfig.mqttBroker);
    prefs.putUShort(kKeyMqttPort, newConfig.mqttPort);
    prefs.putString(kKeyMqttCmd, newConfig.mqttCommandTopic);
    prefs.putString(kKeyMqttStatus, newConfig.mqttStatusTopic);
    prefs.putString(kKeyMqttBroadcast, newConfig.mqttBroadcastTopic);
    prefs.putString(kKeyUiLayout, newConfig.uiLayoutJson);
    prefs.putString(kKeyDevProfile, newConfig.deviceProfileJson);
    Serial.println("[CONFIG] Saved new configuration to NVS");
}

void clearConfig() {
    prefs.clear();
    Serial.println("[CONFIG] Cleared NVS configuration");
}

Config getConfig() {
    Config cfg;
    cfg.machineId = prefs.isKey(kKeyId) ? prefs.getString(kKeyId, esp32cfg::kMachineId) : String(esp32cfg::kMachineId);
    cfg.machineName = prefs.isKey(kKeyName) ? prefs.getString(kKeyName, "") : String("");
    cfg.machineKey = prefs.isKey(kKeyKey) ? prefs.getString(kKeyKey, DEVICE_MACHINE_KEY) : String(DEVICE_MACHINE_KEY);
    cfg.apiBaseUrl = prefs.isKey(kKeyApi) ? prefs.getString(kKeyApi, API_BASE_URL) : String(API_BASE_URL);
    cfg.mqttBroker = prefs.isKey(kKeyMqtt) ? prefs.getString(kKeyMqtt, MQTT_BROKER) : String(MQTT_BROKER);
    cfg.mqttPort = prefs.isKey(kKeyMqttPort) ? prefs.getUShort(kKeyMqttPort, esp32cfg::kMqttPort) : esp32cfg::kMqttPort;
    cfg.mqttCommandTopic = prefs.isKey(kKeyMqttCmd) ? prefs.getString(kKeyMqttCmd, "") : String("");
    cfg.mqttStatusTopic = prefs.isKey(kKeyMqttStatus) ? prefs.getString(kKeyMqttStatus, "") : String("");
    cfg.mqttBroadcastTopic = prefs.isKey(kKeyMqttBroadcast) ? prefs.getString(kKeyMqttBroadcast, "") : String("");
    cfg.uiLayoutJson = prefs.isKey(kKeyUiLayout) ? prefs.getString(kKeyUiLayout, "") : String("");
    cfg.deviceProfileJson = prefs.isKey(kKeyDevProfile) ? prefs.getString(kKeyDevProfile, "") : String("");
    return cfg;
}

bool applyServerProfile(
    const String& machineId,
    const String& machineName,
    const String& mqttBroker,
    uint16_t mqttPort,
    const String& mqttCommandTopic,
    const String& mqttStatusTopic,
    const String& mqttBroadcastTopic,
    const String& uiLayoutJson,
    const String& deviceProfileJson
) {
    Config cfg = getConfig();
    bool changed = false;

    if (machineId.length() > 0 && cfg.machineId != machineId) {
        cfg.machineId = machineId;
        changed = true;
    }

    if (machineName.length() > 0 && cfg.machineName != machineName) {
        cfg.machineName = machineName;
        changed = true;
    }

    if (mqttBroker.length() > 0 && cfg.mqttBroker != mqttBroker) {
        cfg.mqttBroker = mqttBroker;
        changed = true;
    }

    if (mqttPort > 0 && cfg.mqttPort != mqttPort) {
        cfg.mqttPort = mqttPort;
        changed = true;
    }

    if (cfg.mqttCommandTopic != mqttCommandTopic) {
        cfg.mqttCommandTopic = mqttCommandTopic;
        changed = true;
    }

    if (cfg.mqttStatusTopic != mqttStatusTopic) {
        cfg.mqttStatusTopic = mqttStatusTopic;
        changed = true;
    }

    if (cfg.mqttBroadcastTopic != mqttBroadcastTopic) {
        cfg.mqttBroadcastTopic = mqttBroadcastTopic;
        changed = true;
    }

    if (cfg.uiLayoutJson != uiLayoutJson) {
        cfg.uiLayoutJson = uiLayoutJson;
        changed = true;
    }

    if (cfg.deviceProfileJson != deviceProfileJson) {
        cfg.deviceProfileJson = deviceProfileJson;
        changed = true;
    }

    if (changed) {
        saveConfig(cfg);
        Serial.printf(
            "[CONFIG] Synced server profile: machineId=%s, machineName=%s, mqtt=%s:%u, cmdTopic=%s, theme=%s, cash=%d\n",
            cfg.machineId.c_str(),
            cfg.machineName.c_str(),
            cfg.mqttBroker.c_str(),
            cfg.mqttPort,
            cfg.mqttCommandTopic.c_str(),
            getUiTheme().c_str(),
            isCashEnabled()
        );
    }

    return changed;
}

String getMachineId() {
    return prefs.isKey(kKeyId) ? prefs.getString(kKeyId, esp32cfg::kMachineId) : String(esp32cfg::kMachineId);
}

String getMachineName() {
    return prefs.isKey(kKeyName) ? prefs.getString(kKeyName, "") : String("");
}

String getMachineKey() {
    return prefs.isKey(kKeyKey) ? prefs.getString(kKeyKey, DEVICE_MACHINE_KEY) : String(DEVICE_MACHINE_KEY);
}

String getApiBaseUrl() {
    return prefs.isKey(kKeyApi) ? prefs.getString(kKeyApi, API_BASE_URL) : String(API_BASE_URL);
}

String getMqttBroker() {
    return prefs.isKey(kKeyMqtt) ? prefs.getString(kKeyMqtt, MQTT_BROKER) : String(MQTT_BROKER);
}

uint16_t getMqttPort() {
    return prefs.isKey(kKeyMqttPort) ? prefs.getUShort(kKeyMqttPort, esp32cfg::kMqttPort) : esp32cfg::kMqttPort;
}

String getMqttCommandTopic() {
    const String value = prefs.isKey(kKeyMqttCmd) ? prefs.getString(kKeyMqttCmd, "") : String("");
    if (value.length() > 0) return value;
    const String machineId = getMachineId();
    return machineId.length() > 0 ? "vending/v3/machine/" + machineId + "/cmd" : "";
}

String getMqttStatusTopic() {
    const String value = prefs.isKey(kKeyMqttStatus) ? prefs.getString(kKeyMqttStatus, "") : String("");
    if (value.length() > 0) return value;
    const String machineId = getMachineId();
    return machineId.length() > 0 ? "vending/v3/machine/" + machineId + "/status" : "";
}

String getMqttBroadcastTopic() {
    const String value = prefs.isKey(kKeyMqttBroadcast) ? prefs.getString(kKeyMqttBroadcast, "") : String("");
    if (value.length() > 0) return value;
    return "vending/v3/status";
}

String getUiLayoutJson() {
    return readJsonString(kKeyUiLayout);
}

String getDeviceProfileJson() {
    return readJsonString(kKeyDevProfile);
}

String getUiTheme() {
    return getJsonStringValue(getUiLayoutJson(), "theme", "default");
}

String getUiTitle() {
    return getJsonStringValue(getUiLayoutJson(), "title", "MAY BAN HANG TU DONG");
}

String getUiHomeLine1() {
    return getJsonStringValue(getUiLayoutJson(), "home_line_1", "MOI CHON MON");
}

String getUiHomeLine2() {
    const String fallback = isCashEnabled() ? "HOAC DUT TIEN MAT" : "THANH TOAN QR";
    return getJsonStringValue(getUiLayoutJson(), "home_line_2", fallback);
}

String getDeviceLabel() {
    return getJsonStringValue(getDeviceProfileJson(), "device_label", "");
}

String getDeviceMode() {
    return getJsonStringValue(getDeviceProfileJson(), "device_mode", "standard");
}

bool isCashEnabled() {
    return getJsonBoolValue(getDeviceProfileJson(), "cash_enabled", true);
}

bool isRemoteDispenseEnabled() {
    return getJsonBoolValue(getDeviceProfileJson(), "remote_dispense_enabled", esp32cfg::kEnableRemoteDispense);
}

char getSlotRowBase() {
    const String configured = getJsonStringValue(getDeviceProfileJson(), "slot_row_base", "A");
    if (configured.length() == 0) return 'A';
    return static_cast<char>(toupper(configured.charAt(0)));
}

uint8_t getSlotsPerRow() {
    const int configured = getJsonIntValue(getDeviceProfileJson(), "slots_per_row", 10);
    if (configured <= 0 || configured > 26) return 10;
    return static_cast<uint8_t>(configured);
}

String mapSelectionToSlotCode(const String& inputCode) {
    int val = inputCode.toInt();
    if (val <= 0) return inputCode;

    const uint8_t slotsPerRow = getSlotsPerRow();
    const char rowBase = getSlotRowBase();
    char row = static_cast<char>(rowBase + ((val - 1) / slotsPerRow));
    int col = ((val - 1) % slotsPerRow) + 1;

    char buf[6];
    sprintf(buf, "%c%d", row, col);
    return String(buf);
}

uint32_t getAccumulatedCash() {
    return prefs.isKey(kKeyCashAcc) ? prefs.getUInt(kKeyCashAcc, 0) : 0;
}

void saveAccumulatedCash(uint32_t amount) {
    prefs.putUInt(kKeyCashAcc, amount);
}

void saveMachineKey(const String& key) {
    prefs.putString(kKeyKey, key);
    Serial.println("[CONFIG] Machine Key updated in NVS");
}

} // namespace config_manager
