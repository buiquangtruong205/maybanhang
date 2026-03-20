#include "display_ui.h"

#include <Adafruit_GFX.h>
#include <Adafruit_ST7789.h>
#include <SPI.h>
#include <qrcode.h>

#include "app_config.h"
#include "config_manager.h"

// Professional GFX Fonts
#include <Fonts/FreeSansBold9pt7b.h>
#include <Fonts/FreeSans9pt7b.h>
#include <Fonts/FreeSansBold12pt7b.h>

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

// =============================================
// Modern Light Mode Color Palette (RGB565)
// =============================================

constexpr uint16_t COL_WHITE       = 0xFFFF;
constexpr uint16_t COL_BLACK       = 0x0000;
constexpr uint16_t COL_DARKGREY    = 0x4208;
constexpr uint16_t COL_LIGHTGREY   = 0xD6BA;
constexpr uint16_t COL_PLATINUM    = 0xEF7D; // Very light grey for cards

// --- Theme Colors (Light Mode) ---
constexpr uint16_t COL_PRIMARY     = 0x243F; // Modern Deep Blue
constexpr uint16_t COL_SECONDARY   = 0x5D9B; // Soft Sky Blue
constexpr uint16_t COL_ACCENT      = 0xFBE0; // Vibrant Orange
constexpr uint16_t COL_SUCCESS     = 0x2E66; // Soft Emerald
constexpr uint16_t COL_ERROR       = 0xD208; // Soft Red

// --- Functional Colors ---
constexpr uint16_t COL_BG          = 0xFFFF; // Pure White background
constexpr uint16_t COL_CARD_BG     = 0xFEF2; // Near white for card
constexpr uint16_t COL_SHADOW      = 0xCE79; // Soft shadow for light mode
constexpr uint16_t COL_DIVIDER     = 0xE71C;
constexpr uint16_t COL_TEXT_MAIN   = 0x2124; // Very dark blue-grey
constexpr uint16_t COL_TEXT_MUTED  = 0x8410; // Medium grey

// =============================================
// TFT Instance
// =============================================
SPIClass tftSpi(VSPI);
Adafruit_ST7789 tft(&tftSpi, esp32cfg::kTftCsPin, esp32cfg::kTftDcPin, esp32cfg::kTftResetPin);

// =============================================
// Theme Engine (Light Mode Optimized)
// =============================================

uint16_t resolveHeaderColorStart() {
    const String theme = config_manager::getUiTheme();
    if (theme.equalsIgnoreCase("sunset"))  return 0xFC00; // Bright Orange-Yellow
    if (theme.equalsIgnoreCase("forest"))  return 0x87E0; // Light Lime
    if (theme.equalsIgnoreCase("ocean"))   return 0x5D9B; // Sky Blue
    return 0x243F; // Default: Deep Blue
}

uint16_t resolveHeaderColorEnd() {
    const String theme = config_manager::getUiTheme();
    if (theme.equalsIgnoreCase("sunset"))  return 0xF960; // Deep Orange
    if (theme.equalsIgnoreCase("forest"))  return 0x2E66; // Emerald
    if (theme.equalsIgnoreCase("ocean"))   return 0x2124; // Navy
    return 0x5D9B; // Default: Sky Blue
}

// =============================================
// Drawing Helpers
// =============================================

void drawCenteredText(const String& text, int16_t y, uint8_t size, uint16_t color, bool customFont = false) {
    if (customFont) {
        tft.setFont(&FreeSansBold9pt7b);
        if (size > 1) tft.setFont(&FreeSansBold12pt7b);
    } else {
        tft.setFont(NULL);
        tft.setTextSize(size);
    }

    int16_t x1, y1;
    uint16_t width, height;
    tft.getTextBounds(text, 0, y, &x1, &y1, &width, &height);
    int16_t x = (kScreenWidth - static_cast<int16_t>(width)) / 2;
    if (x < 0) x = 0;
    
    // Premium shadow for custom fonts only
    if (customFont && color != COL_WHITE && color != COL_SHADOW) {
        tft.setTextColor(COL_SHADOW);
        tft.setCursor(x + 1, y + 1);
        tft.print(text);
    }
    
    tft.setCursor(x, y);
    tft.setTextColor(color);
    tft.print(text);
}

void drawLoadingDots(int16_t y, uint16_t activeColor, uint32_t intervalMs = 350) {
    constexpr int16_t kR = 5, kGap = 22;
    uint32_t t = millis() / intervalMs;
    for (int i = 0; i < 3; i++) {
        tft.fillCircle(109 - kGap + (i * kGap), y, kR, 
                       (t % 3 == i) ? activeColor : COL_LIGHTGREY);
    }
}

void drawWifiIcon(int16_t cx, int16_t cy, uint16_t color) {
    tft.fillCircle(cx, cy + 12, 3, color);
    tft.drawCircle(cx, cy + 12, 8, color);
    tft.drawCircle(cx, cy + 12, 9, color);
    tft.drawCircle(cx, cy + 12, 14, color);
    tft.drawCircle(cx, cy + 12, 15, color);
    // Mask bottom part to make it look like arcs
    tft.fillRect(cx - 20, cy + 13, 40, 20, COL_WHITE); 
}

void drawGearIcon(int16_t cx, int16_t cy, uint16_t color) {
    tft.drawCircle(cx, cy, 14, color);
    tft.drawCircle(cx, cy, 15, color);
    tft.drawCircle(cx, cy, 6, color);
    // Gear teeth
    for (int i = 0; i < 8; i++) {
        float angle = i * 45 * PI / 180.0;
        int16_t x1 = cx + cos(angle) * 14;
        int16_t y1 = cy + sin(angle) * 14;
        int16_t x2 = cx + cos(angle) * 20;
        int16_t y2 = cy + sin(angle) * 20;
        tft.drawLine(x1, y1, x2, y2, color);
        tft.drawLine(x1+1, y1, x2+1, y2, color);
    }
}

void drawGradientRect(int16_t x, int16_t y, int16_t w, int16_t h, uint16_t colorStart, uint16_t colorEnd) {
    for (int16_t i = 0; i < h; i++) {
        // Linear interpolation between colors (very simple version for RGB565)
        float factor = (float)i / (float)h;
        uint16_t r1 = (colorStart >> 11) & 0x1F, g1 = (colorStart >> 5) & 0x3F, b1 = colorStart & 0x1F;
        uint16_t r2 = (colorEnd >> 11) & 0x1F, g2 = (colorEnd >> 5) & 0x3F, b2 = colorEnd & 0x1F;
        uint16_t r = r1 + (r2 - r1) * factor;
        uint16_t g = g1 + (g2 - g1) * factor;
        uint16_t b = b1 + (b2 - b1) * factor;
        uint16_t color = (r << 11) | (g << 5) | b;
        tft.drawFastHLine(x, y + i, w, color);
    }
}

String fitTextToWidth(const String& text, uint8_t size, int16_t maxWidth) {
    String fitted = text;
    int16_t x1, y1;
    uint16_t width, height;
    tft.setTextSize(size);
    tft.getTextBounds(fitted, 0, 0, &x1, &y1, &width, &height);
    if (width <= static_cast<uint16_t>(maxWidth)) return fitted;

    while (fitted.length() > 1) {
        fitted.remove(fitted.length() - 1);
        String candidate = fitted + "...";
        tft.getTextBounds(candidate, 0, 0, &x1, &y1, &width, &height);
        if (width <= static_cast<uint16_t>(maxWidth)) return candidate;
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
        while (splitAt > 0 && remaining.charAt(splitAt - 1) != ' ') --splitAt;
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

// =============================================
// UI Components
// =============================================

void prepareCanvas(uint16_t color = COL_BG) {
    tft.fillScreen(color);
}

/** Draw a rounded card panel with soft shadow for Light Mode */
void drawCard(int16_t x, int16_t y, int16_t w, int16_t h, uint16_t bgColor = COL_CARD_BG, uint16_t borderColor = COL_DIVIDER) {
    // Multi-layered soft shadow
    tft.fillRoundRect(x + 2, y + 2, w + 1, h + 1, 10, COL_SHADOW);
    
    tft.fillRoundRect(x, y, w, h, 10, bgColor);
    if (borderColor != 0) {
        tft.drawRoundRect(x, y, w, h, 10, borderColor);
    }
}

/** Draw a horizontal divider line */
void drawDivider(int16_t y, uint16_t color = COL_DIVIDER) {
    tft.drawFastHLine(20, y, 200, color);
}

/** Improved status indicator icons */
void drawStatusIcon(int16_t x, int16_t y, bool ok, const char* label) {
    uint16_t bg = ok ? COL_SUCCESS : 0xC618;
    uint16_t dot = ok ? 0xA7E0 : COL_DARKGREY;
    uint16_t border = ok ? 0x2E66 : 0x8410;

    // Smaller, compact status badge (48x16)
    tft.fillRoundRect(x, y, 48, 16, 4, bg);
    tft.drawRoundRect(x, y, 48, 16, 4, border);

    tft.setFont(NULL); 
    tft.setTextColor(COL_WHITE);
    tft.setTextSize(1);
    tft.setCursor(x + 4, y + 4);
    tft.print(label);

    tft.fillCircle(x + 40, y + 8, 3, dot);
}

void drawCheckIcon(int16_t cx, int16_t cy, uint16_t color) {
    tft.drawLine(cx - 10, cy,     cx - 2, cy + 8,  color);
    tft.drawLine(cx - 10, cy + 1, cx - 2, cy + 9,  color); // ticker
    tft.drawLine(cx - 2,  cy + 8, cx + 12, cy - 6, color);
    tft.drawLine(cx - 2,  cy + 9, cx + 12, cy - 5, color);
}

void drawCrossIcon(int16_t cx, int16_t cy, uint16_t color) {
    tft.drawLine(cx - 9, cy - 9, cx + 9, cy + 9, color);
    tft.drawLine(cx - 9, cy - 8, cx + 9, cy + 10, color);
    tft.drawLine(cx + 9, cy - 9, cx - 9, cy + 9, color);
    tft.drawLine(cx + 9, cy - 8, cx - 9, cy + 10, color);
}

// =============================================
// QR Code Renderer
// =============================================

bool canRenderQrPayload(const String& payload) {
    return payload.length() > 0 && payload.length() <= kMaxQrPayloadLength;
}

void drawQrFallback(const String& message) {
    drawCard(kQrCardX, kQrCardY, kQrCardSize, kQrCardSize, COL_WHITE, COL_ERROR);
    
    // Warning Triangle
    tft.fillTriangle(120, 100, 90, 150, 150, 150, COL_ERROR);
    drawCenteredText("!", 138, 1, COL_WHITE, true);

    drawCenteredText("QR KHONG KHA DUNG", 168, 1, COL_ERROR, true);
    drawCenteredMultilineText(message, 190, 1, COL_TEXT_MUTED, 3, 180, 18);
}

void drawQr(const String& payload) {
    if (!canRenderQrPayload(payload)) {
        drawQrFallback(payload.length() == 0 ? "No QR payload from backend" : "QR payload too long for local display");
        return;
    }

    uint8_t buffer[qrcode_getBufferSize(kQrVersion)];
    QRCode qrcode;
    qrcode_initText(&qrcode, buffer, kQrVersion, kQrEcc, payload.c_str());

    const uint8_t modules = 53; // Version 9: 53x53 modules
    const uint8_t scale = 3; 
    const int16_t qrPixelSize = modules * scale; // 159x159
    const int16_t xOffset = (kScreenWidth - qrPixelSize) / 2;
    const int16_t yOffset = 65; // Moved up

    // White card background for QR with padding
    const int16_t cardPadding = 8;
    drawCard(xOffset - cardPadding, yOffset - cardPadding, qrPixelSize + (cardPadding * 2), qrPixelSize + (cardPadding * 2), COL_WHITE);

    for (uint8_t y = 0; y < modules; ++y) {
        for (uint8_t x = 0; x < modules; ++x) {
            const uint16_t color = qrcode_getModule(&qrcode, x, y) ? COL_BLACK : COL_WHITE;
            tft.fillRect(xOffset + (x * scale), yOffset + (y * scale), scale, scale, color);
        }
    }
}

// =============================================
// Header / Status Bar
// =============================================

void drawCommonHeader() {
    uint16_t start = resolveHeaderColorStart();
    uint16_t end = resolveHeaderColorEnd();
    
    // Premium Gradient Header
    drawGradientRect(0, 0, kScreenWidth, 48, start, end);
    tft.drawFastHLine(0, 48, kScreenWidth, COL_DIVIDER);

    // Title with high contrast (Custom Font)
    drawCenteredText(config_manager::getUiTitle(), 30, 1, COL_WHITE, true);

    const String machineName = config_manager::getMachineName();
    const String deviceLabel = config_manager::getDeviceLabel();
    String subLine = machineName;
    if (subLine.length() == 0 && deviceLabel.length() > 0) {
        subLine = deviceLabel;
    } else if (subLine.length() > 0 && deviceLabel.length() > 0) {
        subLine += " | " + deviceLabel;
    }
    
    if (subLine.length() > 0) {
        drawCenteredText(subLine, 45, 1, COL_PLATINUM, false);
    }
}

// =============================================
// Balance Display
// =============================================

void drawBalance(uint32_t balance) {
    if (balance > 0) {
        // Slimmer balance card at the very bottom
        drawCard(10, 240, 220, 38, COL_WHITE, COL_ACCENT);
        String balStr = "SO DU: " + String(balance) + " VND";
        drawCenteredText(balStr, 268, 1, COL_PRIMARY, true);
    }
}

}  // namespace

// =============================================
// Public API
// =============================================

namespace displayui {

bool canRenderPaymentQr(const String& qrPayload) {
    return canRenderQrPayload(qrPayload);
}

void init() {
    tftSpi.begin(esp32cfg::kTftSckPin, -1, esp32cfg::kTftMosiPin);
    tft.init(240, 320);
    tft.setRotation(0);
    tft.invertDisplay(false); // Disable inversion for true Light Mode

    if (esp32cfg::kTftBacklightPin >= 0) {
        pinMode(esp32cfg::kTftBacklightPin, OUTPUT);
        digitalWrite(esp32cfg::kTftBacklightPin, HIGH);
    }

    prepareCanvas();
}

void showBooting() {
    prepareCanvas(COL_BG);

    drawCard(20, 80, 200, 150, COL_WHITE, COL_SECONDARY);

    drawCenteredText("VENDING MACHINE", 100, 2, COL_PRIMARY);
    drawDivider(125);

    drawCenteredText("DANG KHOI DONG", 155, 1, COL_ACCENT, true);
    drawCenteredText("Vui long cho...", 185, 1, COL_TEXT_MUTED, false);

    // Premium centered loading dots
    constexpr int16_t kDotY = 220;
    constexpr int16_t kDotRadius = 5;
    constexpr int16_t kDotGap = 22;
    uint32_t t = millis() / 350;
    for (int i = 0; i < 3; i++) {
        uint16_t col = (t % 3 == i) ? COL_ACCENT : COL_LIGHTGREY;
        tft.fillCircle(109 - kDotGap + (i * kDotGap), kDotY, kDotRadius, col);
    }
}

void showWifiConnecting(const char* ssid) {
    prepareCanvas(COL_BG);
    drawCard(20, 80, 200, 160, COL_WHITE, COL_SECONDARY);
    drawWifiIcon(120, 110, COL_SECONDARY);
    drawCenteredText("WIFI CONNECTING", 150, 1, COL_ACCENT, true);
    drawDivider(170);
    drawCenteredTextFitted(ssid, 195, 1, COL_TEXT_MAIN, 180);
    drawLoadingDots(260, COL_SECONDARY);
}

void showWifiReady(const IPAddress& ip) {
    prepareCanvas(COL_BG);
    drawCard(20, 80, 200, 160, COL_WHITE, COL_SUCCESS);
    drawWifiIcon(120, 110, COL_SUCCESS);
    drawCenteredText("WIFI READY", 150, 1, COL_SUCCESS, true);
    drawDivider(170);
    drawCenteredTextFitted(ip.toString(), 195, 1, COL_TEXT_MAIN, 180);
    drawCheckIcon(120, 260, COL_SUCCESS);
}

void showHome(uint32_t balance, bool wifiOk) {
    prepareCanvas(COL_BG);
    drawCommonHeader();

    // Status Area (WiFi/Backend indicator cards - moved to corners)
    drawStatusIcon(5, 52, wifiOk, "WIFI");
    drawStatusIcon(187, 52, true, "SRV"); 

    // Main Greeting
    drawCenteredText("XIN CHAO", 95, 2, COL_PRIMARY, true);

    // Instructions Card
    drawCard(12, 120, 216, 95, COL_WHITE, COL_SECONDARY);
    
    drawCenteredText("MOI CHON MON", 140, 1, COL_TEXT_MUTED, true);
    drawCenteredMultilineText(config_manager::getUiHomeLine1(), 168, 1, COL_TEXT_MAIN, 2, 200, 22);
    drawCenteredMultilineText(config_manager::getUiHomeLine2(), 198, 1, COL_TEXT_MAIN, 2, 200, 18);

    // Footer Area
    int16_t footerY = 282;
    drawDivider(footerY - 5);
    
    drawCenteredText("CHON MA: 01 - 99", footerY + 12, 1, COL_TEXT_MUTED, true);
    drawCenteredText("[#] XAC NHAN   [*] XOA", footerY + 34, 1, COL_PRIMARY, false);

    drawBalance(balance);
}

void showInputSlot(const String& currentInput, uint32_t balance) {
    prepareCanvas(COL_BG);
    drawCommonHeader();

    drawCenteredText("NHAP MA SAN PHAM", 85, 1, COL_TEXT_MUTED, true);

    // Modern Input Box
    drawCard(18, 105, 204, 75, COL_WHITE, COL_SECONDARY);
    tft.drawRoundRect(19, 106, 202, 73, 9, COL_LIGHTGREY);

    tft.setFont(&FreeSansBold12pt7b);
    tft.setTextColor(COL_PRIMARY);
    tft.setTextSize(2);

    int16_t x1, y1;
    uint16_t w, h;
    tft.getTextBounds(currentInput, 0, 150, &x1, &y1, &w, &h);
    int16_t x = (kScreenWidth - static_cast<int16_t>(w)) / 2;
    if (x < 30) x = 30;

    tft.setCursor(x, 150);
    tft.print(currentInput);

    // Blinking Cyber-cursor
    if ((millis() / 500) % 2 == 0) {
        tft.fillRect(x + w + 5, 125, 4, 35, COL_ACCENT);
    }

    drawCenteredText("Bam [#] de xac nhan", 210, 1, COL_TEXT_MUTED, false);

    drawBalance(balance);
}

void showLoading(const String& line1, const String& line2) {
    prepareCanvas(COL_BG);
    drawCard(25, 90, 190, 140, COL_WHITE, COL_PRIMARY);

    drawCenteredMultilineText(line1, 115, 2, COL_PRIMARY, 2, 170, 24);
    drawDivider(145);
    drawCenteredMultilineText(line2, 160, 1, COL_TEXT_MAIN, 3, 170, 18);

    drawLoadingDots(210, COL_PRIMARY);
}

void showPaymentQr(const String& orderId, const String& amountText, const String& qrPayload) {
    prepareCanvas(COL_BG);

    // Gradient Header
    drawGradientRect(0, 0, kScreenWidth, 52, resolveHeaderColorStart(), resolveHeaderColorEnd());
    drawCenteredText("THANH TOAN QR", 30, 1, COL_WHITE, true);
    drawCenteredText("Don hang #" + orderId, 48, 1, COL_PLATINUM, false);

    // QR Code
    drawQr(qrPayload);

    // Amount Area
    drawCard(10, 260, 220, 50, COL_WHITE, COL_ACCENT);
    drawCenteredMultilineText(amountText, 282, 1, COL_PRIMARY, 2, 200, 20);
    
    drawCenteredText("CHO THANH TOAN...", 242, 1, COL_TEXT_MUTED, true);
}

void showPaymentResult(const String& title, const String& detail, bool success);

void showCashPaymentProgress(const String& orderId, uint32_t total, uint32_t received) {
    prepareCanvas(COL_BG);

    drawCommonHeader();

    // Progress Card
    drawCard(20, 65, 200, 155, COL_WHITE, COL_LIGHTGREY);

    drawCenteredText("TONG THANH TOAN:", 85, 1, COL_TEXT_MUTED);
    drawCenteredText(String(total) + " VND", 108, 2, COL_TEXT_MAIN);

    drawDivider(135);

    drawCenteredText("DA NHAN:", 152, 1, COL_TEXT_MUTED);
    drawCenteredText(String(received) + " VND", 175, 3, COL_ACCENT);

    // Modern Progress Bar
    int16_t pbX = 40, pbY = 235, pbW = 160, pbH = 18;
    tft.drawRoundRect(pbX - 2, pbY - 2, pbW + 4, pbH + 4, 6, COL_DIVIDER);
    tft.fillRoundRect(pbX, pbY, pbW, pbH, 4, COL_PLATINUM);

    if (total > 0) {
        float pct = (float)received / (float)total;
        if (pct > 1.0) pct = 1.0;
        int16_t fillW = (int16_t)(pct * pbW);
        
        if (fillW >= pbW) {
            drawGradientRect(pbX, pbY, pbW, pbH, COL_SUCCESS, 0x67E0);
        } else if (fillW > 0) {
            tft.fillRoundRect(pbX, pbY, fillW, pbH, 4, COL_SUCCESS);
        }
        
        String pctStr = String((int)(pct * 100)) + "%";
        drawCenteredText(pctStr, 275, 1, COL_PRIMARY, true);
    }

    drawCenteredText("Vui long dua tien vao khe", 305, 1, COL_TEXT_MUTED, false);
}

void showPaymentResult(const String& title, const String& detail, bool success) {
    prepareCanvas(COL_BG);

    uint16_t cardColor = COL_WHITE;
    uint16_t accentColor = success ? COL_SUCCESS : COL_ERROR;
    
    drawCard(15, 60, 210, 200, cardColor, accentColor);

    drawCenteredText(success ? "THANH CONG" : "THAT BAI", 95, 1, accentColor, true);
    
    // Real Icons instead of 'V'/'X'
    if (success) {
        tft.fillCircle(120, 145, 25, COL_SUCCESS);
        drawCheckIcon(120, 142, COL_WHITE);
    } else {
        tft.fillCircle(120, 145, 25, COL_ERROR);
        drawCrossIcon(120, 145, COL_WHITE);
    }

    drawCenteredMultilineText(title, 200, 1, COL_TEXT_MAIN, 2, 190, 24);
    drawCenteredMultilineText(detail, 230, 1, COL_TEXT_MUTED, 3, 190, 18);
    
    drawCenteredText("Bam bat ky de tiep tuc", 300, 1, COL_LIGHTGREY, false);
}

void showError(const String& title, const String& detail) {
    prepareCanvas(COL_BG);
    drawCard(15, 65, 210, 195, COL_WHITE, COL_ERROR);

    // Alert Icon
    tft.fillTriangle(120, 95, 95, 140, 145, 140, COL_ERROR);
    drawCenteredText("!", 128, 1, COL_WHITE, true);

    drawCenteredMultilineText(title, 165, 1, COL_TEXT_MAIN, 2, 190, 24);
    drawCenteredMultilineText(detail, 205, 1, COL_TEXT_MUTED, 3, 190, 18);
    
    drawCenteredText("Bam [#] de quay lai", 290, 1, COL_LIGHTGREY, false);
}

void showMaintenance(const String& reason) {
    prepareCanvas(COL_BG);
    drawCard(15, 45, 210, 235, COL_WHITE, COL_PRIMARY);

    drawCenteredText("BAO TRI HE THONG", 75, 1, COL_PRIMARY, true);
    
    drawGearIcon(120, 120, COL_PRIMARY);

    drawCenteredMultilineText(reason, 175, 1, COL_TEXT_MAIN, 4, 190, 24);

    drawCenteredText("Vui long quay lai sau", 245, 1, COL_TEXT_MUTED, false);
    drawCenteredText("SERVICE MAINTENANCE", 310, 1, COL_LIGHTGREY, false);
}

}  // namespace displayui
