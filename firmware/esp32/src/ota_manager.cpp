#include "ota_manager.h"
#include <HTTPUpdate.h>
#include <Update.h>
#include <WiFi.h>
#include "api_client.h"

namespace ota_manager {

namespace {
bool updating = false;
int currentUpdateId = 0;
int lastProgress = -1;

void update_progress(int cur, int total) {
    int percentage = (cur * 100) / total;
    if (percentage != lastProgress && percentage % 5 == 0) {
        lastProgress = percentage;
        Serial.printf("[OTA] Progress: %d%%\n", percentage);
        api_client::reportOTAProgress(currentUpdateId, percentage, "downloading");
    }
}

void update_error(int err) {
    Serial.printf("[OTA] Error Code: %d\n", err);
    api_client::reportLog("error", "OTA update failed with error code: " + String(err));
    api_client::reportOTAProgress(currentUpdateId, lastProgress, "failed");
    updating = false;
}

void update_finished() {
    Serial.println("[OTA] Update finished successfully!");
    api_client::reportOTAProgress(currentUpdateId, 100, "completed");
    updating = false;
}
}

void init() {
    // Optional ESP32 httpUpdate callbacks
    Update.onProgress(update_progress);
}

void startUpdate(int updateId, const String& url, const String& checksum) {
    if (updating) {
        Serial.println("[OTA] Update already in progress");
        return;
    }

    updating = true;
    currentUpdateId = updateId;
    lastProgress = -1;

    Serial.printf("[OTA] Starting update from %s\n", url.c_str());
    api_client::reportLog("info", "Starting OTA update ID: " + String(updateId));
    api_client::reportOTAProgress(updateId, 0, "installing");

    if (checksum.length() > 0) {
        Serial.printf("[OTA] Expected checksum: %s\n", checksum.c_str());
    }

    WiFiClient client;

    // Standard ESP32 httpUpdate for .bin files
    // Note: This is a blocking call on ESP32 by default.
    t_httpUpdate_return ret = httpUpdate.update(client, url);

    switch (ret) {
        case HTTP_UPDATE_FAILED:
            update_error(httpUpdate.getLastError());
            break;

        case HTTP_UPDATE_NO_UPDATES:
            Serial.println("[OTA] No updates available");
            updating = false;
            break;

        case HTTP_UPDATE_OK:
            update_finished();
            // The ESP32 will usually restart automatically here
            break;
    }
}

bool isUpdating() {
    return updating;
}

} // namespace ota_manager
