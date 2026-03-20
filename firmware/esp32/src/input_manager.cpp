#include "input_manager.h"
#include "app_config.h"

namespace input_manager {

namespace {

const byte ROWS = 4;
const byte COLS = 3;

char keys[ROWS][COLS] = {
    {'1','2','3'},
    {'4','5','6'},
    {'7','8','9'},
    {'*','0','#'}
};

byte rowPins[ROWS] = {
    esp32cfg::kKeypadRow1, // 12
    esp32cfg::kKeypadRow2, // 33
    esp32cfg::kKeypadRow3, // 25
    esp32cfg::kKeypadRow4  // 27
};

byte colPins[COLS] = {
    esp32cfg::kKeypadCol1, // 14
    esp32cfg::kKeypadCol2, // 13
    esp32cfg::kKeypadCol3  // 26
};

Keypad keypad = Keypad(makeKeymap(keys), rowPins, colPins, ROWS, COLS);

} // namespace

void init() {
    // Keypad library handles pinMode
}

char getKey() {
    return keypad.getKey();
}

} // namespace input_manager
