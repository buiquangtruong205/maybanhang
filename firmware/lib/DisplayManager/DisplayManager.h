#ifndef DISPLAY_MANAGER_H
#define DISPLAY_MANAGER_H

#include <Wire.h>
#include <Adafruit_GFX.h>
#include <Adafruit_SSD1306.h>
#include "config.h"

/**
 * Lớp quản lý hiển thị OLED
 */
class DisplayManager {
private:
    static Adafruit_SSD1306 display;

public:
    static void setup() {
        Wire.begin(OLED_SDA, OLED_SCL);
        
        // Khởi tạo OLED với địa chỉ 0x3C
        if(!display.begin(SSD1306_SWITCHCAPVCC, 0x3C)) {
            Serial.println(F("SSD1306 allocation failed"));
            return;
        }
        
        display.clearDisplay();
        display.setTextSize(1);
        display.setTextColor(SSD1306_WHITE);
        display.setCursor(0,0);
        display.println(F("VENDING MACHINE V2"));
        display.println(F("Khoi dong..."));
        display.display();
    }

    static void showStatus(const char* wifi, const char* mqtt) {
        display.clearDisplay();
        display.setCursor(0,0);
        display.setTextSize(1);
        display.println(F("TRANG THAI HE THONG:"));
        display.println(F("--------------------"));
        display.print(F("WiFi: ")); display.println(wifi);
        display.print(F("MQTT: ")); display.println(mqtt);
        display.display();
    }

    static void showMessage(const char* msg) {
        display.clearDisplay();
        display.setCursor(0,20);
        display.setTextSize(1);
        display.println(F("THONG BAO MOI:"));
        display.setTextSize(2);
        display.println(msg);
        display.display();
    }
};

// Khởi tạo đối tượng tĩnh
Adafruit_SSD1306 DisplayManager::display(SCREEN_WIDTH, SCREEN_HEIGHT, &Wire, -1);

#endif
