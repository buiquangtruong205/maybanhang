#include "mqtt_manager.h"
#include <WiFi.h>
#include <PubSubClient.h>
#include "app_config.h"
#include "secrets.h"
#include "wifi_manager.h"

namespace mqtt_manager {

namespace {
WiFiClient wifiClient;
PubSubClient mqttClient(wifiClient);
uint32_t lastMqttRetryAt = 0;
CommandCallback onCommandReceived = nullptr;

void callback(char* topic, byte* payload, unsigned int length) {
    String message;
    for (unsigned int i = 0; i < length; i++) {
        message += (char)payload[i];
    }
    Serial.printf("[MQTT] Message arrived on %s: %s\n", topic, message.c_str());

    if (onCommandReceived) {
        int colonPos = message.indexOf(':');
        if (colonPos != -1) {
            String cmd = message.substring(0, colonPos);
            String val = message.substring(colonPos + 1);
            onCommandReceived(cmd, val);
        } else {
            onCommandReceived(message, "");
        }
    }
}

void ensureConnected() {
    if (!wifi_manager::isConnected() || mqttClient.connected()) {
        return;
    }

    const uint32_t now = millis();
    if (now - lastMqttRetryAt < 5000) {
        return;
    }
    lastMqttRetryAt = now;

    Serial.print("[MQTT] Connecting to broker... ");
    String clientId = "ESP32_V3_";
    clientId += String(esp32cfg::kMachineId);

    if (mqttClient.connect(clientId.c_str(), MQTT_USER, MQTT_PASS)) {
        Serial.println("connected");
        mqttClient.subscribe(esp32cfg::kMqttCommandTopic);
        mqttClient.publish(esp32cfg::kMqttStatusTopic, "online");
    } else {
        Serial.print("failed, rc=");
        Serial.println(mqttClient.state());
    }
}
}

void init(CommandCallback callback) {
    onCommandReceived = callback;
    mqttClient.setServer(MQTT_BROKER, esp32cfg::kMqttPort);
    mqttClient.setCallback(mqtt_manager::callback);
}

void loop() {
    ensureConnected();
    if (mqttClient.connected()) {
        mqttClient.loop();
    }
}

bool isConnected() {
    return mqttClient.connected();
}

void publishStatus(const String& status) {
    if (mqttClient.connected()) {
        mqttClient.publish(esp32cfg::kMqttStatusTopic, status.c_str());
    }
}

}  // namespace mqtt_manager
