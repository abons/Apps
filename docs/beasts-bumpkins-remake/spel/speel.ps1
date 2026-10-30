# Start het spel: kaart en modellen syncen, importeren, spelen.
# Rechtermuisknop > Run with PowerShell. Extra opties mogen erachter, bv. -Seizoen winter -Uur 22 -Missie 2.
param([string]$Seizoen = "", [int]$Uur = -1, [int]$Missie = 1)

$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot

$G = Join-Path $env:LOCALAPPDATA "Microsoft\WinGet\Packages\GodotEngine.GodotEngine_Microsoft.Winget.Source_8wekyb3d8bbwe\Godot_v4.7.2-stable_win64_console.exe"
if (-not (Test-Path $G)) {
    $cmd = Get-Command godot -ErrorAction SilentlyContinue
    if ($cmd) { $G = $cmd.Source } else { Write-Host "Godot 4.7.2 niet gevonden: $G"; Read-Host "Enter om te sluiten"; exit 1 }
}

try {
    Write-Host "== sync" -ForegroundColor Cyan
    & powershell -NoProfile -ExecutionPolicy Bypass -File (Join-Path $PSScriptRoot "sync.ps1")

    if (-not (Test-Path (Join-Path $PSScriptRoot "data\origineel\map1.json"))) {
        throw "data/origineel/map1.json ontbreekt; maak hem met tools/origineel/ (bron: docs/beasts-bumpkins-remake/lokaal/)"
    }

    Write-Host "== import" -ForegroundColor Cyan
    & $G --headless --path . --import | Out-Null

    $extra = @()
    if ($Seizoen) { $extra += "--seizoen=$Seizoen" }
    if ($Uur -ge 0) { $extra += "--uur=$Uur" }
    if ($Missie -ne 1) { $extra += "--missie=$Missie" }

    Write-Host "== spelen" -ForegroundColor Cyan
    if ($extra.Count -gt 0) { & $G --path . -- @extra } else { & $G --path . }
}
catch {
    Write-Host "Fout: $_" -ForegroundColor Red
    Read-Host "Enter om te sluiten"
    exit 1
}
