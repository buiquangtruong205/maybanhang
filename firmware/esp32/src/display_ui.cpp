#include "display_ui.h"

#include <Adafruit_GFX.h>
#include <Adafruit_ILI9341.h>
#include <SPI.h>
#include <qrcode.h>

#include "app_config.h"
#include "config_manager.h"

namespace {

constexpr uint16_t kScreenWidth = 240;
constexpr uint16_t kScreenHeight = 320;
constexpr uint8_t kQrVersion = 9;
constexpr uint8_t kQrEcc = 0;
constexpr int16_t kDefaultMargin = 10;
constexpr int16_t kQrCardX = 18;
constexpr int16_t kQrCardY = 72;
constexpr int16_t kQrCardSize = 204;
constexpr size_t kMaxQrPayloadLength = 180;

SPIClass tftSpi(VSPI);
Adafruit_ILI9341 tft(&tftSpi, esp32cfg::kTftDcPin, esp32cfg::kTftCsPin, esp32cfg::kTftResetPin);

uint16_t resolveHeaderColor() {
    const String theme = config_manager::getUiTheme();
    if (theme.equalsIgnoreCase("factory")) return ILI9341_NAVY;
    if (theme.equalsIgnoreCase("sunset")) return ILI9341_MAROON;
    if (theme.equalsIgnoreCase("forest")) return ILI9341_DARKGREEN;
    return ILI9341_DARKCYAN;
}

uint16_t resolveAccentColor() {
    const String theme = config_manager::getUiTheme();
    if (theme.equalsIgnoreCase("factory")) return ILI9341_CYAN;
    if (theme.equalsIgnoreCase("sunset")) return ILI9341_ORANGE;
    if (theme.equalsIgnoreCase("forest")) return ILI9341_GREENYELLOW;
    return ILI9341_CYAN;
}

void drawCenteredText(const String& text, int16_t y, uint8_t size, uint16_t color) {
    int16_t x1;
    int16_t y1;
    uint16_t width;
    uint16_t height;

    tft.setTextSize(size);
    tft.getTextBounds(text, 0, y, &x1, &y1, &width, &height);
    int16_t x = (kScreenWidth - static_cast<int16_t>(width)) / 2;
    if (x < 0) x = 0;

    tft.setCursor(x, y);
    tft.setTextColor(color);
    tft.print(text);
}

String fitTextToWidth(const String& text, uint8_t size, int16_t maxWidth) {
    String fitted = text;
    int16_t x1;
    int16_t y1;
    uint16_t width;
    uint16_t height;

    tft.setTextSize(size);
    tft.getTextBounds(fitted, 0, 0, &x1, &y1, &width, &height);
    if (width <= static_cast<uint16_t>(maxWidth)) {
        return fitted;
    }

    while (fitted.length() > 1) {
        fitted.remove(fitted.length() - 1);
        String candidate = fitted + "...";
        tft.getTextBounds(candidate, 0, 0, &x1, &y1, &width, &height);
        if (width <= static_cast<uint16_t>(maxWidth)) {
            return candidate;
        }
    }

    return "...";
}

void drawCenteredTextFitted(const String& text, int16_t y, uint8_t size, uint16_t color, int16_t maxWidth) {
    drawCenteredText(fitTextToWidth(text, size, maxWidth), y, size, color);
}

void drawCenteredMultilineText(const String& text, int16_t startY, uint8_t size, uint16_t color, uint8_t maxLines, int16_t maxWidth, int16_t lineHeight) {
    String remaining = text;
    remaining.trim();

    for (uint8_t line = 0; line < maxLines && remaining.length() > 0; ++line) {
        String candidate = remaining;
        String bestFit = fitTextToWidth(candidate, size, maxWidth);

        if (bestFit == candidate || line == maxLines - 1) {
            drawCenteredText(bestFit, startY + (line * lineHeight), size, color);
            return;
        }

        int splitAt = remaining.length();
        while (splitAt > 0 && remaining.charAt(splitAt - 1) != ' ') {
            --splitAt;
        }

        if (splitAt <= 0) {
            drawCenteredText(bestFit, startY + (line * lineHeight), size, color);
            remaining.remove(0, bestFit.length());
        } else {
            String lineText = remaining.substring(0, splitAt);
            lineText.trim();
            lineText = fitTextToWidth(lineText, size, maxWidth);
            drawCenteredText(lineText, startY + (line * lineHeight), size, color);
            remaining = remaining.substring(splitAt);
            remaining.trim();
        }
    }
}

void prepareCanvas(uint16_t color = ILI9341_BLACK) {
    tft.fillScreen(color);
}

bool canRenderQrPayload(const String& payload) {
    return payload.length() > 0 && payload.length() <= kMaxQrPayloadLength;
}

void drawQrFallback(const String& message) {
    tft.fillRoundRect(kQrCardX, kQrCardY, kQrCardSize, kQrCardSize, 10, ILI9341_WHITE);
    tft.drawRoundRect(kQrCardX, kQrCardY, kQrCardSize, kQrCardSize, 10, ILI9341_RED);
    drawCenteredText("QR UNAVAILABLE", 135, 2, ILI9341_RED);
    drawCenteredMultilineText(message, 170, 1, ILI9341_BLACK, 3, 180, 18);
}

void drawQr(const String& payload) {
    if (!canRenderQrPayload(payload)) {
        drawQrFallback(payload.length() == 0 ? "No QR payload from backend" : "QR payload too long for local display");
        return;
    }

    uint8_t buffer[qrcode_getBufferSize(kQrVersion)];
    QRCode qrcode;
    qrcode_initText(&qrcode, buffer, kQrVersion, kQrEcc, payload.c_str());

    const uint8_t moduleCount = qrcode.size;
    const uint8_t scale = 4;
    const int16_t qrPixelSize = moduleCount * scale;
    const int16_t xOffset = (kScreenWidth - qrPixelSize) / 2;
    const int16_t yOffset = 84;

    tft.fillRoundRect(kQrCardX, kQrCardY, kQrCardSize, kQrCardSize, 10, ILI9341_WHITE);

    for (uint8_t y = 0; y < moduleCount; ++y) {
        for (uint8_t x = 0; x < moduleCount; ++x) {
            const uint16_t color = qrcode_getModule(&qrcode, x, y) ? ILI9341_BLACK : ILI9341_WHITE;
            tft.fillRect(xOffset + (x * scale), yOffset + (y * scale), scale, scale, color);
        }
    }
}

void drawCommonHeader() {
    tft.fillRect(0, 0, kScreenWidth, 50, resolveHeaderColor());
    drawCenteredTextFitted(config_manager::getUiTitle(), 15, 2, ILI9341_YELLOW, kScreenWidth - (kDefaultMargin * 2));

    const String machineName = config_manager::getMachineName();
    const String deviceLabel = config_manager::getDeviceLabel();
    String subLine = machineName;
    if (subLine.length() == 0 && deviceLabel.length() > 0) {
        subLine = deviceLabel;
    } else if (subLine.length() > 0 && deviceLabel.length() > 0) {
        subLine += " | " + deviceLabel;
    }

    if (subLine.length() > 0) {
        drawCenteredTextFitted(subLine, 38, 1, ILI9341_WHITE, kScreenWidth - (kDefaultMargin * 2));
    }
}

void drawBalance(uint32_t balance) {
    if (balance > 0) {
        tft.fillRoundRect(10, 240, 220, 45, 8, ILI9341_NAVY);
        tft.setTextColor(ILI9341_GREEN);
        tft.setTextSize(2);
        tft.setCursor(25, 255);
        tft.print("TIEN MAT: ");
        tft.print(balance);
        tft.print("d");
    }
}

}  // namespace

namespace displayui {

bool canRenderPaymentQr(const String& qrPayload) {
    return canRenderQrPayload(qrPayload);
}

void init() {
    tftSpi.begin(esp32cfg::kTftSckPin, -1, esp32cfg::kTftMosiPin);
    tft.begin();
    tft.setRotation(0);

    if (esp32cfg::kTftBacklightPin >= 0) {
        pinMode(esp32cfg::kTftBacklightPin, OUTPUT);
        digitalWrite(esp32cfg::kTftBacklightPin, HIGH);
    }

    prepareCanvas();
}

void showBooting() {
    prepareCanvas();
    drawCenteredText("SYSTEM BOOTING", 120, 2, resolveAccentColor());
    drawCenteredText("Please wait...", 150, 1, ILI9341_WHITE);
}

void showWifiConnecting(const char* ssid) {
    prepareCanvas();
    drawCenteredText("WIFI CONNECTING", 120, 2, ILI9341_YELLOW);
    drawCenteredTextFitted(ssid, 150, 1, ILI9341_WHITE, kScreenWidth - 20);
}

void showWifiReady(const IPAddress& ip) {
    prepareCanvas();
    drawCenteredText("WIFI CONNECTED", 120, 2, ILI9341_GREEN);
    drawCenteredTextFitted(ip.toString(), 150, 1, ILI9341_WHITE, kScreenWidth - 20);
}

void showHome(uint32_t balance, bool wifiOk) {
    prepareCanvas();
    drawCommonHeader();
    
    // Wifi status icon (simple dot)
    tft.fillCircle(225, 25, 5, wifiOk ? ILI9341_GREEN : ILI9341_RED);

    drawCenteredMultilineText(config_manager::getUiHomeLine1(), 78, 2, ILI9341_WHITE, 2, kScreenWidth - 20, 24);
    drawCenteredMultilineText(config_manager::getUiHomeLine2(), 122, 2, ILI9341_WHITE, 2, kScreenWidth - 20, 24);
    
    // Decoration
    tft.drawFastHLine(40, 140, 160, ILI9341_LIGHTGREY);
    
    drawCenteredText("Ma SP: 1-99", 180, 1, resolveAccentColor());
    drawCenteredText("Nut # : Xac nhan", 200, 1, resolveAccentColor());
    drawCenteredText("Nut * : Xoa", 220, 1, resolveAccentColor());

    if (!config_manager::isCashEnabled()) {
        drawCenteredText("Cash disabled by profile", 250, 1, ILI9341_ORANGE);
    }

    drawBalance(balance);
}

void showInputSlot(const String& currentInput, uint32_t balance) {
    prepareCanvas();
    drawCommonHeader();
    
    tft.setTextColor(ILI9341_WHITE);
    tft.setTextSize(2);
    tft.setCursor(20, 70);
    tft.println("Dang nhap ma SP:");
    
    tft.drawRect(18, 100, 204, 50, ILI9341_DARKGREY);
    
    tft.setTextColor(ILI9341_GREEN);
    tft.setTextSize(4);

    String fittedInput = fitTextToWidth(currentInput, 4, 180);
    int16_t x1, y1;
    uint16_t w, h;
    tft.getTextBounds(fittedInput, 0, 110, &x1, &y1, &w, &h);
    int16_t x = (kScreenWidth - static_cast<int16_t>(w)) / 2;
    if (x < 25) x = 25;

    tft.setCursor(x, 110);
    tft.print(fittedInput);
    
    drawBalance(balance);
}

void showLoading(const String& line1, const String& line2) {
    prepareCanvas();
    drawCenteredMultilineText(line1, 110, 2, ILI9341_CYAN, 2, kScreenWidth - 20, 24);
    drawCenteredMultilineText(line2, 165, 1, ILI9341_WHITE, 3, kScreenWidth - 20, 18);
}

void showPaymentQr(const String& orderId, const String& amountText, const String& qrPayload) {
    prepareCanvas();
    drawCenteredTextFitted("THANH TOAN QR", 18, 2, ILI9341_YELLOW, kScreenWidth - 20);
    drawCenteredTextFitted("Don hang #" + orderId, 45, 1, ILI9341_WHITE, kScreenWidth - 20);
    drawQr(qrPayload);
    drawCenteredMultilineText(amountText, 286, 2, ILI9341_GREEN, 2, kScreenWidth - 20, 20);
}

void showPaymentResult(const String& title, const String& detail, bool success) {
    prepareCanvas();
    drawCenteredMultilineText(title, 110, 2, success ? ILI9341_GREEN : ILI9341_RED, 2, kScreenWidth - 20, 24);
    drawCenteredMultilineText(detail, 165, 1, ILI9341_WHITE, 3, kScreenWidth - 20, 18);
}

void showError(const String& title, const String& detail) {
    prepareCanvas();
    drawCenteredMultilineText(title, 110, 2, ILI9341_RED, 2, kScreenWidth - 20, 24);
    drawCenteredMultilineText(detail, 165, 1, ILI9341_WHITE, 3, kScreenWidth - 20, 18);
}

}  // namespace displayui
