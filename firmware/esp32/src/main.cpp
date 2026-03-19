#include <Arduino.h>
#include <esp_task_wdt.h>
#include "app_runtime.h"

// 30 seconds watchdog
#define WDT_TIMEOUT 30

void setup() {
    esp_task_wdt_init(WDT_TIMEOUT, true); // enable panic so it resets
    esp_task_wdt_add(NULL); // add current thread to WDT watch
    app_runtime::setup();
}

void loop() {
    esp_task_wdt_reset();
    app_runtime::loop();
}
