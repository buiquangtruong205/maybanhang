#include <Arduino.h>
#include "config.h"
#include "WiFiManager.h"
#include "DisplayManager.h"
#include "PaymentHandler.h"

/**
 * Chương trình chính điều khiển ESP32-S3 Vending Machine V2
 */

void setup() {
    // Khởi tạo Serial để debug
    Serial.begin(115200);
    delay(1000);
    Serial.println("\n--- He thong bat dau ---");

    // 1. Khởi tạo Hiển thị
    DisplayManager::setup();
    DisplayManager::showMessage("KHOI DONG...");

    // 2. Khởi tạo WiFi
    WiFiManager::setup();

    // 3. Khởi tạo MQTT và các chân LED
    PaymentHandler::setup();

    Serial.println("--- Setup Hoan Tat ---");
}

void loop() {
    // Duy trì kết nối WiFi
    WiFiManager::loop();

    // Nếu WiFi đã kết nối, duy trì MQTT
    if (WiFiManager::isConnected()) {
        PaymentHandler::loop();
    } else {
        DisplayManager::showStatus("Mat", "Ngat");
    }

    // Một chút delay để tránh watchdog
    delay(10);
}