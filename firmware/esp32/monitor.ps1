$workspaceRoot = "E:\IoT\Du_An\Vending_Machine"
$shortRoot = Join-Path $workspaceRoot "f3"
$coreTarget = "E:\IoT\Du_An\Vending_Machine\Vesion_3\firmware\.platformio-local"

if (-not (Test-Path $shortRoot)) {
    New-Item -ItemType Directory -Path $shortRoot | Out-Null
}
if (-not (Test-Path (Join-Path $shortRoot ".platformio-local"))) {
    New-Item -ItemType Junction -Path (Join-Path $shortRoot ".platformio-local") -Target $coreTarget | Out-Null
}

$env:PLATFORMIO_CORE_DIR = Join-Path $shortRoot ".platformio-local"
pio device monitor -b 115200
