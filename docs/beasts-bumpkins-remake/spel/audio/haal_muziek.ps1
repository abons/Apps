# Zet de originele muziek (7 cd-audiotracks, James Hannigan; eigen cd-rip, prive) om naar assets/audio/muziek/trackNN.ogg.
# NOOIT in git: assets/ staat in .gitignore, en lokaal/ ook. Zie audio.md sectie 7 en view/muziek.gd.
# Bron: een map met de tracks 2..8 van de cd, als TrackNN.* (de naam uit de RaZLeN-patch, Music\Track02.ogg) of
# beastsNN.wav (bchunk -w, de naam uit openbumpkins); ogg, wav, mp3 of flac. Track 1 is de datatrack.
# Standaard: lokaal/muziek/, dan de laptop-share. Ontbreekt alles, dan niets (het spel blijft dan stil zonder muziek).
# ffmpeg (winget Gyan.FFmpeg): stereo 44,1 kHz, Vorbis q5, loudnorm -18 LUFS, piek -1 dBTP (audio.md 4e: muziek q5 stereo).
param([string[]]$Bron = @((Join-Path $PSScriptRoot '..\..\lokaal\muziek'),
                          '\\axel-laptop\Users\axelb\beasts\beastnbump\Music',
                          '\\axel-laptop\Users\axelb\beasts\Music'))

$ErrorActionPreference = 'Stop'
$map = $null
foreach ($b in $Bron) { if (Test-Path $b) { $map = $b; break } }
if (-not $map) { Write-Host "muziek: geen bron gevonden (eigen cd-rip in lokaal/muziek/ als Track02..Track08), overgeslagen"; return }
$ff = Get-Command ffmpeg -ErrorAction SilentlyContinue
if (-not $ff) {   # een shell van voor de installatie kent het PATH nog niet: de winget-map zelf
    $exe = Get-ChildItem "$env:LOCALAPPDATA\Microsoft\WinGet\Packages\Gyan.FFmpeg*\*\bin\ffmpeg.exe" -ErrorAction SilentlyContinue | Select-Object -First 1
    if ($exe) { $ff = Get-Command $exe.FullName }
}
if (-not $ff) { Write-Host "muziek: geen ffmpeg, overgeslagen"; return }
$doel = Join-Path $PSScriptRoot '..\assets\audio\muziek'
New-Item -ItemType Directory -Force $doel | Out-Null
$n = 0
foreach ($t in 2..8) {
    $nn = '{0:D2}' -f $t
    $src = Get-ChildItem $map -File | Where-Object {
        $_.BaseName -match "^(track|beasts)[ _-]?0?$t$" -and $_.Extension -in '.ogg', '.wav', '.mp3', '.flac'
    } | Select-Object -First 1
    if (-not $src) { Write-Host "muziek: track $nn ontbreekt in $map"; continue }
    $uit = Join-Path $doel "track$nn.ogg"
    if ((Test-Path $uit) -and (Get-Item $uit).LastWriteTime -ge $src.LastWriteTime) { continue }
    & $ff.Source -hide_banner -loglevel error -y -i $src.FullName -af 'loudnorm=I=-18:TP=-1:LRA=11' -ac 2 -ar 44100 -c:a libvorbis -q:a 5 $uit
    if ($LASTEXITCODE -eq 0) { $n++ } else { Write-Host "ffmpeg faalde op $($src.Name)" }
}
Write-Host "muziek: $n tracks omgezet naar assets/audio/muziek/ (uit $map)"
