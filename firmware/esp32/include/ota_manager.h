#pragma once

#include <Arduino.h>

namespace ota_manager {

void init();
void startUpdate(int updateId, const String& url, const String& checksum);
bool isUpdating();

} // namespace ota_manager
