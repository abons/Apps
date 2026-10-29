# Kopieert de kaartdata en de glb's het project in (assets/ en data/origineel/ staan in .gitignore).
# map1.json komt uit de gedecodeerde originele spelbestanden (auteursrecht) en blijft dus lokaal.
param([string]$Map = 'C:\Users\Axel\AppData\Local\Temp\claude\E--werk-androidApps-Apps\16e99493-ac86-47c7-921f-1d215c266f51\scratchpad\map1\map1.json')

$ErrorActionPreference = 'Stop'
$orig = Join-Path $PSScriptRoot 'data\origineel'
New-Item -ItemType Directory -Force $orig | Out-Null
if (Test-Path $Map) {
    Copy-Item $Map (Join-Path $orig 'map1.json') -Force
    Write-Host "gekopieerd: data/origineel/map1.json"
} else { Write-Host "ONTBREEKT: $Map (geef -Map <pad>)" }

$assets = Join-Path $PSScriptRoot 'assets'
New-Item -ItemType Directory -Force $assets | Out-Null
$bron = @(
    '..\modellen\peasant_hut_rt.glb',
    '..\modellen\peasant_hut_rt_lod1.glb',
    '..\modellen\bumpkin\bumpkin_man.glb',
    '..\modellen\bumpkin\bumpkin_anim.json')
foreach ($b in $bron) {
    $src = Join-Path $PSScriptRoot $b
    if (Test-Path $src) {
        Copy-Item $src (Join-Path $assets (Split-Path $src -Leaf)) -Force
        Write-Host "gekopieerd: assets/$(Split-Path $src -Leaf)"
    } else { Write-Host "ontbreekt (overgeslagen): $b" }
}
Write-Host "Daarna: Godot --headless --path . --import"
