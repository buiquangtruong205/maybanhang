#ifndef WIFI_MANAGER_H
#define WIFI_MANAGER_H

#include <WiFi.h>
#include "config.h"

/**
 * Lớp quản lý kết nối WiFi
 */
class WiFiManager {
public:
    static void setup() {
        Serial.println("\n--- Khởi tạo WiFi ---");
        WiFi.mode(WIFI_STA);
        WiFi.begin(WIFI_SSID, WIFI_PASSWORD);

        Serial.print("Đang kết nối tới: ");
        Serial.println(WIFI_SSID);
    }

    static void loop() {
        if (WiFi.status() != WL_CONNECTED) {
            static unsigned long lastRetry = 0;
            if (millis() - lastRetry > 5000) {
                Serial.println("Mất kết nối WiFi. Đang thử lại...");
                WiFi.disconnect();
                WiFi.reconnect();
                lastRetry = millis();
            }
        }
    }

    static bool isConnected() {
        return WiFi.status() == WL_CONNECTED;
    }
};

#endif
