$workspaceRoot = "E:\IoT\Du_An\Vending_Machine"
$shortRoot = Join-Path $workspaceRoot "f3"
$projectTarget = "E:\IoT\Du_An\Vending_Machine\Vesion_3\firmware\esp32"
$sharedTarget = "E:\IoT\Du_An\Vending_Machine\Vesion_3\firmware\shared"
$coreTarget = "E:\IoT\Du_An\Vending_Machine\Vesion_3\firmware\.platformio-local"

if (-not (Test-Path $shortRoot)) {
    New-Item -ItemType Directory -Path $shortRoot | Out-Null
}
if (-not (Test-Path (Join-Path $shortRoot "esp32"))) {
    New-Item -ItemType Junction -Path (Join-Path $shortRoot "esp32") -Target $projectTarget | Out-Null
}
if (-not (Test-Path (Join-Path $shortRoot "shared"))) {
    New-Item -ItemType Junction -Path (Join-Path $shortRoot "shared") -Target $sharedTarget | Out-Null
}
if (-not (Test-Path (Join-Path $shortRoot ".platformio-local"))) {
    New-Item -ItemType Junction -Path (Join-Path $shortRoot ".platformio-local") -Target $coreTarget | Out-Null
}

$env:PLATFORMIO_CORE_DIR = Join-Path $shortRoot ".platformio-local"
Push-Location (Join-Path $shortRoot "esp32")
try {
    pio run -j 1
} finally {
    Pop-Location
}
