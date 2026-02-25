#ifndef CONFIG_H
#define CONFIG_H

#include <Arduino.h>

/**
 * Tệp cấu hình hệ thống Vending Machine V2
 */

// --- Cấu hình WiFi ---
const char* WIFI_SSID = "YOUR_SSID";
const char* WIFI_PASSWORD = "YOUR_PASSWORD";

// --- Cấu hình MQTT ---
const char* MQTT_SERVER = "your_mqtt_broker_address";
const uint16_t MQTT_PORT = 1883;
const char* MQTT_USER = "your_username";
const char* MQTT_PASS = "your_password";

// TOPIC MQTT
const char* TOPIC_COMMAND = "vending/machine/command"; // Nhận lệnh nhả hàng
const char* TOPIC_STATUS  = "vending/machine/status";  // Gửi trạng thái máy

// --- Cấu hình Phần cứng (Pinout) ---

// Màn hình OLED I2C
#define OLED_SDA 8
#define OLED_SCL 9
#define SCREEN_WIDTH 128
#define SCREEN_HEIGHT 64

// Đèn LED thông báo (Dùng thay cho Motor để test)
const uint8_t LED_PINS[] = {1, 2, 4, 5}; 
#define NUM_LEDS 4

// LED trạng thái hệ thống
#define LED_MQTT 3
#define LED_WIFI 43 // Built-in LED

#endif
