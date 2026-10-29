# Kopieer de laatste realtime-export van de hut (LOD0 + LOD1) het project in. Draai na elke re-export.
$dir = Join-Path $PSScriptRoot 'hut'
New-Item -ItemType Directory -Force $dir | Out-Null
Get-ChildItem $dir -Filter 'peasant_hut.*' -ErrorAction SilentlyContinue | Remove-Item -Force
Get-ChildItem $dir -Filter 'peasant_hut_*_1k.*' -ErrorAction SilentlyContinue | Remove-Item -Force
foreach ($f in 'peasant_hut_rt.glb', 'peasant_hut_rt_lod1.glb') {
    $src = Join-Path $PSScriptRoot "..\$f"
    $dst = Join-Path $dir $f
    Copy-Item $src $dst -Force
    Write-Host "gekopieerd: $f ($((Get-Item $dst).Length) bytes)"
}
