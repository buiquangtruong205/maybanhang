#ifndef PAYMENT_HANDLER_H
#define PAYMENT_HANDLER_H

#include <PubSubClient.h>
#include <ArduinoJson.h>
#include "config.h"
#include "DisplayManager.h"

/**
 * Lớp quản lý MQTT (Tên cũ PaymentHandler được giữ lại theo cấu trúc thư mục)
 */
class PaymentHandler {
private:
    static WiFiClient espClient;
    static PubSubClient client;

    static void callback(char* topic, byte* payload, unsigned int length) {
        Serial.print("Tin nhan den [");
        Serial.print(topic);
        Serial.print("]: ");
        
        String message;
        for (int i = 0; i < length; i++) {
            message += (char)payload[i];
        }
        Serial.println(message);

        // Phân tích JSON
        StaticJsonDocument<200> doc;
        DeserializationError error = deserializeJson(doc, message);

        if (error) {
            Serial.print("Loi JSON: ");
            Serial.println(error.c_str());
            return;
        }

        // Xử lý lệnh điều khiển LED/OLED
        if (doc.containsKey("cmd")) {
            const char* cmd = doc["cmd"];
            
            if (strcmp(cmd, "led_on") == 0) {
                int pinIdx = doc["id"] | 0;
                if (pinIdx < NUM_LEDS) digitalWrite(LED_PINS[pinIdx], HIGH);
                DisplayManager::showMessage("LED BAT");
            } 
            else if (strcmp(cmd, "led_off") == 0) {
                int pinIdx = doc["id"] | 0;
                if (pinIdx < NUM_LEDS) digitalWrite(LED_PINS[pinIdx], LOW);
                DisplayManager::showMessage("LED TAT");
            }
            else if (strcmp(cmd, "display") == 0) {
                const char* text = doc["text"] | "Hello";
                DisplayManager::showMessage(text);
            }
        }
    }

public:
    static void setup() {
        client.setServer(MQTT_SERVER, MQTT_PORT);
        client.setCallback(callback);

        // Cấu hình chân LED
        for (int i = 0; i < NUM_LEDS; i++) {
            pinMode(LED_PINS[i], OUTPUT);
            digitalWrite(LED_PINS[i], LOW);
        }
        pinMode(LED_MQTT, OUTPUT);
    }

    static void loop() {
        if (!client.connected()) {
            reconnect();
        }
        client.loop();
    }

    static void reconnect() {
        while (!client.connected()) {
            Serial.print("Dang ket noi MQTT...");
            String clientId = "ESP32S3-Vending-";
            clientId += String(random(0xffff), HEX);

            if (client.connect(clientId.c_str(), MQTT_USER, MQTT_PASS)) {
                Serial.println("Thanh cong!");
                digitalWrite(LED_MQTT, HIGH);
                client.subscribe(TOPIC_COMMAND);
                DisplayManager::showStatus("OK", "OK");
            } else {
                digitalWrite(LED_MQTT, LOW);
                Serial.print("That bai, ma loi=");
                Serial.print(client.state());
                Serial.println(" Thu lai sau 5 giay...");
                delay(5000);
            }
        }
    }
};

// Khởi tạo các thành phần tĩnh
WiFiClient PaymentHandler::espClient;
PubSubClient PaymentHandler::client(PaymentHandler::espClient);

#endif
