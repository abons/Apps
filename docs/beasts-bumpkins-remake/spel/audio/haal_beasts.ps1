# Kopieert de stemfragmenten en klanken uit beasts-src (prive repo) naar assets/audio/beasts/ (staat in .gitignore).
# Waarom niet in git: dit repo (Apps) is publiek, beasts-src niet; de licentie van de ElevenLabs-mp3 is open
# (audio.md sectie 2). Prive gebruik mag (besluit gebruiker). Aangeroepen vanuit sync.ps1; los draaien kan ook.
# Geen ffmpeg op dit systeem (2026-10-30), dus mp3 blijft mp3: Godot importeert mp3 zelf.
param([string]$Bron = (Join-Path $PSScriptRoot '..\..\..\..\..\beasts-src\app\src\main\res\raw'))

$ErrorActionPreference = 'Stop'
$doel = Join-Path $PSScriptRoot '..\assets\audio\beasts'
if (-not (Test-Path $Bron)) { Write-Host "beasts-src niet gevonden (overgeslagen, het spel is dan stiller): $Bron"; return }
New-Item -ItemType Directory -Force $doel | Out-Null
$n = 0
foreach ($f in Get-ChildItem $Bron -File | Where-Object { $_.Extension -in '.mp3', '.wav' }) {
    $uit = Join-Path $doel $f.Name
    if (-not (Test-Path $uit) -or (Get-Item $uit).Length -ne $f.Length) { Copy-Item $f.FullName $uit -Force; $n++ }
}
Write-Host "audio uit beasts-src: $n nieuw/bijgewerkt in assets/audio/beasts/"
