#pragma once

#include <Arduino.h>

namespace config_manager {

struct Config {
    String machineId;
    String machineName;
    String machineKey;
    String apiBaseUrl;
    String mqttBroker;
    uint16_t mqttPort;
    String mqttCommandTopic;
    String mqttStatusTopic;
    String mqttBroadcastTopic;
    String uiLayoutJson;
    String deviceProfileJson;
};

void init();
void saveConfig(const Config& newConfig);
Config getConfig();
void clearConfig();
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
);

// Helper specific getters
String getMachineId();
String getMachineName();
String getMachineKey();
String getApiBaseUrl();
String getMqttBroker();
uint16_t getMqttPort();
String getMqttCommandTopic();
String getMqttStatusTopic();
String getMqttBroadcastTopic();
String getUiLayoutJson();
String getDeviceProfileJson();

// Runtime helpers resolved from dynamic machine profile
String getUiTheme();
String getUiTitle();
String getUiHomeLine1();
String getUiHomeLine2();
String getDeviceLabel();
String getDeviceMode();
bool isCashEnabled();
bool isRemoteDispenseEnabled();
char getSlotRowBase();
uint8_t getSlotsPerRow();
String mapSelectionToSlotCode(const String& inputCode);

// Cash session persistence
uint32_t getAccumulatedCash();
void saveAccumulatedCash(uint32_t amount);
void saveMachineKey(const String& key);

} // namespace config_manager
