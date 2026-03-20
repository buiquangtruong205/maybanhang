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
    // ALWAYS reset textSize first to prevent inheritance from previous calls
    tft.setTextSize(1);
    
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
    if (x < 0) x = 2;
    
    tft.setCursor(x, y);
    tft.setTextColor(color);
    tft.print(text);
    
    // Reset to default after printing to prevent state leaking
    tft.setFont(NULL);
    tft.setTextSize(1);
}

void drawLoadingDots(int16_t y, uint16_t activeColor, uint32_t intervalMs = 350) {
    constexpr int16_t kR = 5, kGap = 22;
    uint32_t t = millis() / intervalMs;
    for (int i = 0; i < 3; i++) {
        tft.fillCircle(109 - kGap + (i * kGap), y, kR, 
                       (t % 3 == i) ? activeColor : COL_LIGHTGREY);
    }
}

void drawWifiIcon(int16_t cx, int16_t cy, uint16_t color, uint16_t bgColor = COL_BG) {
    tft.fillCircle(cx, cy + 12, 3, color);
    tft.drawCircle(cx, cy + 12, 8, color);
    tft.drawCircle(cx, cy + 12, 9, color);
    tft.drawCircle(cx, cy + 12, 14, color);
    tft.drawCircle(cx, cy + 12, 15, color);
    // Mask bottom part to make it look like arcs (use bgColor, not hardcoded)
    tft.fillRect(cx - 20, cy + 13, 40, 20, bgColor); 
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
    // Use signed int to prevent unsigned underflow when colorEnd < colorStart
    int16_t r1 = (colorStart >> 11) & 0x1F, g1 = (colorStart >> 5) & 0x3F, b1 = colorStart & 0x1F;
    int16_t r2 = (colorEnd >> 11) & 0x1F, g2 = (colorEnd >> 5) & 0x3F, b2 = colorEnd & 0x1F;
    for (int16_t i = 0; i < h; i++) {
        float factor = (float)i / (float)h;
        uint16_t r = (uint16_t)(r1 + (int16_t)((r2 - r1) * factor));
        uint16_t g = (uint16_t)(g1 + (int16_t)((g2 - g1) * factor));
        uint16_t b = (uint16_t)(b1 + (int16_t)((b2 - b1) * factor));
        uint16_t color = (r << 11) | (g << 5) | b;
        tft.drawFastHLine(x, y + i, w, color);
    }
}

String fitTextToWidth(const String& text, uint8_t size, int16_t maxWidth) {
    String fitted = text;
    int16_t x1, y1;
    uint16_t width, height;
    // Always reset to default font before measuring to prevent wrong bounds
    tft.setFont(NULL);
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

/** Reusable footer hint text (DRY) */
void drawFooterHint(const char* text, int16_t y, uint16_t color = COL_TEXT_MUTED) {
    tft.setFont(NULL);
    tft.setTextSize(1);
    tft.setTextColor(color);
    int16_t x1, y1; uint16_t tw, th;
    tft.getTextBounds(text, 0, 0, &x1, &y1, &tw, &th);
    tft.setCursor((kScreenWidth - (int16_t)tw) / 2, y);
    tft.print(text);
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
    drawGradientRect(0, 0, kScreenWidth, 50, start, end);
    tft.drawFastHLine(0, 50, kScreenWidth, COL_DIVIDER);

    // Title with high contrast (Custom Font)
    drawCenteredText(config_manager::getUiTitle(), 32, 1, COL_WHITE, true);

    const String machineName = config_manager::getMachineName();
    const String deviceLabel = config_manager::getDeviceLabel();
    String subLine = machineName;
    if (subLine.length() == 0 && deviceLabel.length() > 0) {
        subLine = deviceLabel;
    } else if (subLine.length() > 0 && deviceLabel.length() > 0) {
        subLine += " | " + deviceLabel;
    }
    
    if (subLine.length() > 0) {
        tft.setFont(NULL);
        tft.setTextSize(1);
        int16_t x1, y1; uint16_t tw, th;
        tft.getTextBounds(subLine, 0, 0, &x1, &y1, &tw, &th);
        int16_t sx = (kScreenWidth - (int16_t)tw) / 2;
        if (sx < 2) sx = 2;
        tft.setCursor(sx, 42);
        tft.setTextColor(COL_PLATINUM);
        tft.print(subLine);
    }
}

// =============================================
// Balance Display
// =============================================

void drawBalance(uint32_t balance) {
    if (balance > 0) {
        // Compact balance badge at the bottom
        drawCard(20, 285, 200, 30, COL_WHITE, COL_ACCENT);
        String balStr = "SO DU: " + String(balance) + " VND";
        tft.setFont(NULL);
        tft.setTextSize(1);
        int16_t x1, y1; uint16_t tw, th;
        tft.getTextBounds(balStr, 0, 0, &x1, &y1, &tw, &th);
        int16_t sx = (kScreenWidth - (int16_t)tw) / 2;
        tft.setCursor(sx, 296);
        tft.setTextColor(COL_PRIMARY);
        tft.print(balStr);
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

    drawLoadingDots(220, COL_ACCENT);
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

    // Status badges below header (evenly spaced)
    drawStatusIcon(5, 54, wifiOk, "WIFI");
    drawStatusIcon(187, 54, true, "SRV"); 

    // Main Greeting
    drawCenteredText("XIN CHAO", 98, 2, COL_PRIMARY, true);

    // Instructions Card (consistent spacing: 8px gap between elements)
    drawCard(12, 122, 216, 90, COL_WHITE, COL_SECONDARY);
    drawCenteredText("MOI CHON MON", 142, 1, COL_TEXT_MUTED, true);
    drawCenteredMultilineText(config_manager::getUiHomeLine1(), 168, 1, COL_TEXT_MAIN, 2, 196, 18);
    drawCenteredMultilineText(config_manager::getUiHomeLine2(), 193, 1, COL_TEXT_MAIN, 1, 196, 18);

    // Footer instructions (consistent spacing)
    drawDivider(220);
    drawCenteredText("CHON MA: 01 - 99", 234, 1, COL_TEXT_MUTED, true);
    drawFooterHint("[#] XAC NHAN   [*] XOA", 256, COL_PRIMARY);

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
    drawCard(20, 85, 200, 155, COL_WHITE, COL_PRIMARY);

    drawCenteredText(line1, 115, 1, COL_PRIMARY, true);
    drawDivider(135);
    drawCenteredMultilineText(line2, 155, 1, COL_TEXT_MAIN, 3, 180, 18);

    drawLoadingDots(220, COL_PRIMARY);
}

void showPaymentQr(const String& orderId, const String& amountText, const String& qrPayload) {
    prepareCanvas(COL_BG);

    // Gradient Header
    drawGradientRect(0, 0, kScreenWidth, 52, resolveHeaderColorStart(), resolveHeaderColorEnd());
    drawCenteredText("THANH TOAN QR", 32, 1, COL_WHITE, true);

    tft.setFont(NULL); tft.setTextSize(1);
    String orderLabel = "Don hang #" + orderId;
    int16_t x1, y1; uint16_t tw, th;
    tft.getTextBounds(orderLabel, 0, 0, &x1, &y1, &tw, &th);
    tft.setCursor((kScreenWidth - (int16_t)tw) / 2, 42);
    tft.setTextColor(COL_PLATINUM);
    tft.print(orderLabel);

    // QR Code
    drawQr(qrPayload);

    // Amount + status area
    drawCenteredText("CHO THANH TOAN...", 240, 1, COL_TEXT_MUTED, true);
    drawCard(10, 260, 220, 50, COL_WHITE, COL_ACCENT);
    drawCenteredText(amountText, 290, 1, COL_PRIMARY, true);
}

void showPaymentResult(const String& title, const String& detail, bool success);

void showCashPaymentProgress(const String& orderId, uint32_t total, uint32_t received) {
    prepareCanvas(COL_BG);

    drawCommonHeader();

    // Progress Card
    drawCard(20, 65, 200, 155, COL_WHITE, COL_LIGHTGREY);

    drawCenteredText("TONG TIEN:", 85, 1, COL_TEXT_MUTED);
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
        if (pct > 1.0f) pct = 1.0f;
        int16_t fillW = (int16_t)(pct * pbW);
        
        if (fillW >= pbW) {
            drawGradientRect(pbX, pbY, pbW, pbH, COL_SUCCESS, 0x67E0);
        } else if (fillW > 0) {
            tft.fillRoundRect(pbX, pbY, fillW, pbH, 4, COL_SUCCESS);
        }
        
        String pctStr = String((int)(pct * 100)) + "%";
        drawCenteredText(pctStr, 275, 1, COL_PRIMARY, true);
    }

    drawFooterHint("Vui long dua tien vao khe", 305);
}

void showPaymentResult(const String& title, const String& detail, bool success) {
    prepareCanvas(COL_BG);

    uint16_t accentColor = success ? COL_SUCCESS : COL_ERROR;
    
    drawCard(15, 50, 210, 215, COL_WHITE, accentColor);

    drawCenteredText(success ? "THANH CONG" : "THAT BAI", 85, 2, accentColor, true);
    
    // Circle icon with checkmark or cross
    if (success) {
        tft.fillCircle(120, 135, 25, COL_SUCCESS);
        drawCheckIcon(120, 132, COL_WHITE);
    } else {
        tft.fillCircle(120, 135, 25, COL_ERROR);
        drawCrossIcon(120, 135, COL_WHITE);
    }

    drawDivider(172);
    drawCenteredMultilineText(title, 190, 1, COL_TEXT_MAIN, 2, 190, 20);
    drawCenteredMultilineText(detail, 220, 1, COL_TEXT_MUTED, 2, 190, 18);
    
    drawFooterHint("Bam phim bat ky de tiep tuc", 300, COL_LIGHTGREY);
}

void showError(const String& title, const String& detail) {
    prepareCanvas(COL_BG);
    drawCard(15, 60, 210, 200, COL_WHITE, COL_ERROR);

    // Alert Triangle Icon
    tft.fillTriangle(120, 85, 95, 135, 145, 135, COL_ERROR);
    tft.setFont(NULL); tft.setTextSize(3);
    tft.setTextColor(COL_WHITE);
    tft.setCursor(113, 100);
    tft.print("!");

    drawCenteredMultilineText(title, 160, 1, COL_TEXT_MAIN, 2, 190, 22);
    drawCenteredMultilineText(detail, 200, 1, COL_TEXT_MUTED, 3, 190, 18);
    
    drawFooterHint("Bam [#] de quay lai", 290, COL_LIGHTGREY);
}

void showMaintenance(const String& reason) {
    prepareCanvas(COL_BG);
    drawCard(15, 45, 210, 230, COL_WHITE, COL_PRIMARY);

    drawCenteredText("BAO TRI", 80, 2, COL_PRIMARY, true);
    
    drawGearIcon(120, 130, COL_PRIMARY);

    drawDivider(165);
    drawCenteredMultilineText(reason, 185, 1, COL_TEXT_MAIN, 4, 190, 20);

    drawFooterHint("Vui long quay lai sau", 290);
}

}  // namespace displayui
