$ErrorActionPreference = "Stop"

$projectDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$firmwareRoot = Split-Path -Parent $projectDir
$workspaceRoot = Split-Path -Parent $firmwareRoot
$shortRoot = Join-Path $workspaceRoot "f3"
$shortProject = Join-Path $shortRoot "esp32"
$shortShared = Join-Path $shortRoot "shared"
$coreDir = Join-Path $shortRoot ".platformio-local"

New-Item -ItemType Directory -Force -Path $shortRoot | Out-Null

if (-not (Test-Path $shortProject)) {
    New-Item -ItemType Junction -Path $shortProject -Target $projectDir | Out-Null
}

if (-not (Test-Path $shortShared)) {
    New-Item -ItemType Junction -Path $shortShared -Target (Join-Path $firmwareRoot "shared") | Out-Null
}

$env:PLATFORMIO_CORE_DIR = $coreDir
Set-Location $shortProject

Write-Host "[build] Project path: $projectDir"
Write-Host "[build] Short path:   $shortProject"
Write-Host "[build] Shared path:  $shortShared"
Write-Host "[build] Core dir:     $coreDir"

pio run -e esp32dev @args
