# Kopieert de stemfragmenten en klanken uit beasts-src (prive repo) naar assets/audio/beasts/ (staat in .gitignore).
# Waarom niet in git: dit repo (Apps) is publiek, beasts-src niet; de licentie van de ElevenLabs-mp3 is open
# (audio.md sectie 2). Prive gebruik mag (besluit gebruiker). Aangeroepen vanuit sync.ps1; los draaien kan ook.
# Met ffmpeg (sinds 2026-10-30, winget Gyan.FFmpeg) wordt elke mp3 ook een .ogg: mono 44,1 kHz, stemmen
# genormaliseerd op -16 LUFS (piek -1 dBTP, audio.md 4e). geluid.gd neemt de .ogg als die er is. Zonder ffmpeg blijft het mp3.
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

$ff = Get-Command ffmpeg -ErrorAction SilentlyContinue
if (-not $ff) { Write-Host "geen ffmpeg: mp3 blijft mp3"; return }
$m = 0
foreach ($f in Get-ChildItem $doel -File -Filter *.mp3) {
    $ogg = [IO.Path]::ChangeExtension($f.FullName, '.ogg')
    if ((Test-Path $ogg) -and (Get-Item $ogg).LastWriteTime -ge $f.LastWriteTime) { continue }
    & $ff.Source -hide_banner -loglevel error -y -i $f.FullName -af 'loudnorm=I=-16:TP=-1:LRA=11' -ac 1 -ar 44100 -c:a libvorbis -q:a 4 $ogg
    if ($LASTEXITCODE -eq 0) { $m++ } else { Write-Host "ffmpeg faalde op $($f.Name)" }
}
Write-Host "ogg gemaakt: $m"
