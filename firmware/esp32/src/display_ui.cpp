#include "display_ui.h"

#include <Adafruit_GFX.h>
#include <Adafruit_ST7789.h>
#include <SPI.h>
#include <qrcode.h>

#include "app_config.h"

namespace {

constexpr uint16_t kScreenWidth = 240;
constexpr uint16_t kScreenHeight = 320;
constexpr uint8_t kQrVersion = 9;
constexpr uint8_t kQrEcc = 0;

SPIClass tftSpi(VSPI);
Adafruit_ST7789 tft(&tftSpi, esp32cfg::kTftCsPin, esp32cfg::kTftDcPin, esp32cfg::kTftResetPin);

void drawCenteredText(const String& text, int16_t y, uint8_t size, uint16_t color) {
    int16_t x1;
    int16_t y1;
    uint16_t width;
    uint16_t height;

    tft.setTextSize(size);
    tft.getTextBounds(text, 0, y, &x1, &y1, &width, &height);
    int16_t x = (kScreenWidth - static_cast<int16_t>(width)) / 2;
    if (x < 0) {
        x = 0;
    }

    tft.setCursor(x, y);
    tft.setTextColor(color);
    tft.print(text);
}

void prepareCanvas(uint16_t color = ST77XX_BLACK) {
    tft.fillScreen(color);
    tft.setTextWrap(false);
}

void drawQr(const String& payload) {
    uint8_t buffer[qrcode_getBufferSize(kQrVersion)];
    QRCode qrcode;
    qrcode_initText(&qrcode, buffer, kQrVersion, kQrEcc, payload.c_str());

    const uint8_t moduleCount = qrcode.size;
    const uint8_t scale = 4;
    const int16_t qrPixelSize = moduleCount * scale;
    const int16_t xOffset = (kScreenWidth - qrPixelSize) / 2;
    const int16_t yOffset = 84;

    tft.fillRoundRect(18, 72, 204, 204, 10, ST77XX_WHITE);

    for (uint8_t y = 0; y < moduleCount; ++y) {
        for (uint8_t x = 0; x < moduleCount; ++x) {
            const uint16_t color = qrcode_getModule(&qrcode, x, y) ? ST77XX_BLACK : ST77XX_WHITE;
            tft.fillRect(xOffset + (x * scale), yOffset + (y * scale), scale, scale, color);
        }
    }
}

}  // namespace

namespace displayui {

void init() {
    tftSpi.begin(esp32cfg::kTftSckPin, -1, esp32cfg::kTftMosiPin, esp32cfg::kTftCsPin);
    tft.init(kScreenWidth, kScreenHeight);
    tft.setRotation(0);

    if (esp32cfg::kTftBacklightPin >= 0) {
        pinMode(esp32cfg::kTftBacklightPin, OUTPUT);
        digitalWrite(esp32cfg::kTftBacklightPin, HIGH);
    }

    prepareCanvas();
}

void showBooting() {
    prepareCanvas();
    drawCenteredText("ESP32 CONTROLLER", 92, 2, ST77XX_CYAN);
    drawCenteredText("Booting...", 136, 2, ST77XX_WHITE);
}

void showWifiConnecting(const char* ssid) {
    prepareCanvas();
    drawCenteredText("CONNECTING WIFI", 92, 2, ST77XX_YELLOW);
    drawCenteredText(ssid, 136, 2, ST77XX_WHITE);
}

void showWifiReady(const IPAddress& ip) {
    prepareCanvas();
    drawCenteredText("WIFI CONNECTED", 88, 2, ST77XX_GREEN);
    drawCenteredText(ip.toString(), 132, 2, ST77XX_WHITE);
}

void showIdle() {
    prepareCanvas();
    drawCenteredText("VENDING READY", 72, 2, ST77XX_CYAN);
    drawCenteredText("Select product", 116, 2, ST77XX_WHITE);
    drawCenteredText("Then choose online pay", 152, 2, ST77XX_YELLOW);
}

void showLoading(const String& line1, const String& line2) {
    prepareCanvas();
    drawCenteredText(line1, 100, 2, ST77XX_CYAN);
    drawCenteredText(line2, 144, 2, ST77XX_WHITE);
}

void showPaymentQr(const String& orderId, const String& amountText, const String& qrPayload) {
    prepareCanvas();
    drawCenteredText("ONLINE PAYMENT", 18, 2, ST77XX_CYAN);
    drawCenteredText("Order #" + orderId, 42, 2, ST77XX_WHITE);
    drawQr(qrPayload);
    drawCenteredText(amountText, 290, 2, ST77XX_YELLOW);
}

void showPaymentResult(const String& title, const String& detail, bool success) {
    prepareCanvas();
    drawCenteredText(title, 96, 2, success ? ST77XX_GREEN : ST77XX_RED);
    drawCenteredText(detail, 144, 2, ST77XX_WHITE);
}

void showError(const String& title, const String& detail) {
    prepareCanvas();
    drawCenteredText(title, 88, 2, ST77XX_RED);
    drawCenteredText(detail, 132, 2, ST77XX_WHITE);
}

}  // namespace displayui
