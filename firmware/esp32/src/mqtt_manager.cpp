#include "mqtt_manager.h"
#include <WiFi.h>
#include <PubSubClient.h>
#include "wifi_manager.h"
#include "config_manager.h"
#include "app_config.h"
#include "secrets.h"

namespace mqtt_manager {

namespace {
WiFiClient wifiClient;
PubSubClient mqttClient(wifiClient);
uint32_t lastMqttRetryAt = 0;
CommandCallback onCommandReceived = nullptr;
String currentBroker;
uint16_t currentPort = 0;
String currentCommandTopic;
String currentStatusTopic;
String currentBroadcastTopic;
uint32_t firstDisconnectAt = 0;
const uint32_t kHardResetTimeoutMs = 600000; // 10 minutes

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
    if (!wifi_manager::isConnected()) {
        return;
    }

    String machineId = config_manager::getMachineId();
    String broker = config_manager::getMqttBroker();
    uint16_t port = config_manager::getMqttPort();

    if (machineId.length() == 0) {
        Serial.println("[MQTT] Waiting for backend profile to provide machine_id");
        return;
    }

    if (broker.length() == 0 || broker == "0.0.0.0") {
        Serial.println("[MQTT] Waiting for valid MQTT broker configuration");
        return;
    }

    // Build dynamic topics
    String cmdTopic = config_manager::getMqttCommandTopic();
    String statusTopic = config_manager::getMqttStatusTopic();
    String broadcastTopic = config_manager::getMqttBroadcastTopic();

    if (cmdTopic.length() == 0 || statusTopic.length() == 0) {
        Serial.println("[MQTT] Waiting for valid MQTT topics from backend profile");
        return;
    }

    if (mqttClient.connected()) {
        if (cmdTopic != currentCommandTopic || statusTopic != currentStatusTopic || broadcastTopic != currentBroadcastTopic) {
            Serial.println("[MQTT] Topic profile changed, reconnecting");
            mqttClient.disconnect();
        } else {
            return;
        }
    }

    const uint32_t now = millis();
    if (now - lastMqttRetryAt < 5000) {
        return;
    }
    lastMqttRetryAt = now;

    if (broker != currentBroker || port != currentPort) {
        currentBroker = broker;
        currentPort = port;
        mqttClient.setServer(currentBroker.c_str(), currentPort);
        Serial.printf("[MQTT] Updated broker to %s:%u\n", currentBroker.c_str(), currentPort);
    }

    Serial.printf("[MQTT] Connecting to broker %s:%u ... ", currentBroker.c_str(), currentPort);
    String clientId = "ESP32_V3_" + machineId;

    if (mqttClient.connect(clientId.c_str(), MQTT_USER, MQTT_PASS)) {
        Serial.println("connected");
        mqttClient.subscribe(cmdTopic.c_str());
        currentCommandTopic = cmdTopic;
        currentStatusTopic = statusTopic;
        currentBroadcastTopic = broadcastTopic;
        Serial.printf("[MQTT] Subscribed cmd=%s status=%s broadcast=%s\n",
                      currentCommandTopic.c_str(),
                      currentStatusTopic.c_str(),
                      currentBroadcastTopic.c_str());
        mqttClient.publish(currentStatusTopic.c_str(), "online");
        mqttClient.publish(currentBroadcastTopic.c_str(), (machineId + ":online").c_str());
        firstDisconnectAt = 0; // Reset recovery timer
    } else {
        Serial.print("failed, rc=");
        Serial.println(mqttClient.state());
        
        if (firstDisconnectAt == 0) {
            firstDisconnectAt = now;
        } else if (now - firstDisconnectAt > kHardResetTimeoutMs) {
            Serial.println("[MQTT] CRITICAL: Reconnection failed for too long. Rebooting ESP32...");
            delay(1000);
            ESP.restart();
        }
    }
}
}

void init(CommandCallback callback) {
    onCommandReceived = callback;
    mqttClient.setCallback(mqtt_manager::callback);
}

void loop() {
    if (mqttClient.connected()) {
        if (!mqttClient.loop()) {
            Serial.printf("[MQTT] Connection lost, state=%d\n", mqttClient.state());
        }
    }
    ensureConnected();
}

bool isConnected() {
    return mqttClient.connected();
}

void publishStatus(const String& status) {
    if (mqttClient.connected()) {
        String machineId = config_manager::getMachineId();
        String statusTopic = currentStatusTopic.length() > 0 ? currentStatusTopic : config_manager::getMqttStatusTopic();
        String broadcastTopic = currentBroadcastTopic.length() > 0 ? currentBroadcastTopic : config_manager::getMqttBroadcastTopic();
        Serial.printf("[MQTT] Publish status=%s topic=%s broadcast=%s\n",
                      status.c_str(), statusTopic.c_str(), broadcastTopic.c_str());
        mqttClient.publish(statusTopic.c_str(), status.c_str());
        
        // Also publish to a global status topic if needed, but per-machine is better
        mqttClient.publish(broadcastTopic.c_str(), (machineId + ":" + status).c_str());
    }
}

}  // namespace mqtt_manager
