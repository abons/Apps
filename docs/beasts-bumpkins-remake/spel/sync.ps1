# Kopieert de kaartdata en de glb's het project in (assets/ en data/origineel/ staan in .gitignore).
# map1.json en map2.json komen uit de gedecodeerde originele spelbestanden (auteursrecht) en blijven dus lokaal.
# map2.json maken: python ..\lokaal\map2\maak_map.py 2
param([string]$Map = (Join-Path $PSScriptRoot '..\lokaal\map1\map1.json'),   # lokaal/ staat in .gitignore
      [string]$Map2 = (Join-Path $PSScriptRoot '..\lokaal\map2\map2.json'))

$ErrorActionPreference = 'Stop'
$orig = Join-Path $PSScriptRoot 'data\origineel'
New-Item -ItemType Directory -Force $orig | Out-Null
foreach ($k in @(@($Map, 'map1.json'), @($Map2, 'map2.json'))) {
    if (Test-Path $k[0]) {
        Copy-Item $k[0] (Join-Path $orig $k[1]) -Force
        Write-Host "gekopieerd: data/origineel/$($k[1])"
    } else { Write-Host "ONTBREEKT: $($k[0])" }
}

$assets = Join-Path $PSScriptRoot 'assets'
New-Item -ItemType Directory -Force $assets | Out-Null
$bron = @(
    '..\modellen\peasant_hut_rt.glb',
    '..\modellen\peasant_hut_rt_lod1.glb',
    '..\modellen\bumpkin\bumpkin_man.glb',
    '..\modellen\bumpkin\bumpkin_vrouw.glb',
    '..\modellen\bumpkin\bumpkin_jongen.glb',
    '..\modellen\bumpkin\bumpkin_meisje.glb',
    '..\modellen\bumpkin\bumpkin_oudere_man.glb',
    '..\modellen\bumpkin\bumpkin_oudere_vrouw.glb',
    '..\modellen\bumpkin\bumpkin_anim.json',
    '..\modellen\gebouwen\gereedschapsloods_rt.glb',
    '..\modellen\gebouwen\kippenhok_rt.glb',
    '..\modellen\gebouwen\molen_rt.glb',
    '..\modellen\gebouwen\melkerij_boerderij_rt.glb',
    '..\modellen\dieren\kip.glb',
    '..\modellen\dieren\kip_anim.json',
    '..\modellen\dieren\ei.glb')
foreach ($b in $bron) {
    $src = Join-Path $PSScriptRoot $b
    if (Test-Path $src) {
        Copy-Item $src (Join-Path $assets (Split-Path $src -Leaf)) -Force
        Write-Host "gekopieerd: assets/$(Split-Path $src -Leaf)"
    } else { Write-Host "ontbreekt (overgeslagen): $b" }
}
# natuur en props (glb's hebben hun texturen ingebakken), de koe, en de terreintexturen (5 sets x kleur/normaal/ruw)
$nat = Join-Path $PSScriptRoot '..\modellen\natuur'
foreach ($g in Get-ChildItem (Join-Path $nat '*.glb')) {
    Copy-Item $g.FullName (Join-Path $assets $g.Name) -Force
}
Write-Host "gekopieerd: natuur-glb's"
foreach ($t in Get-ChildItem (Join-Path $nat 'textures\terrein_*.jpg')) {
    Copy-Item $t.FullName (Join-Path $assets $t.Name) -Force
}
Write-Host "gekopieerd: terreintexturen"
# de wind-shader is bron in modellen/natuur; shaders/natuur_wind.gdshader is de gesynchroniseerde kopie
Copy-Item (Join-Path $nat 'natuur_wind.gdshader') (Join-Path $PSScriptRoot 'shaders\natuur_wind.gdshader') -Force
foreach ($b in @('..\modellen\dieren\koe.glb', '..\modellen\dieren\koe_anim.json')) {
    $src = Join-Path $PSScriptRoot $b
    if (Test-Path $src) { Copy-Item $src (Join-Path $assets (Split-Path $src -Leaf)) -Force; Write-Host "gekopieerd: assets/$(Split-Path $src -Leaf)" }
    else { Write-Host "ontbreekt (overgeslagen): $b" }
}
# stemmen en klanken uit beasts-src naar assets/audio/beasts/ (prive, niet in git; audio.md sectie 6)
& (Join-Path $PSScriptRoot 'audio\haal_beasts.ps1')
Write-Host "Daarna: Godot --headless --path . --import"
