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

# Dorpeling: glb + animatie-sidecar van de bumpkin-asset (../bumpkin/). Bestandsnaam: zie BUMPKIN_GLB in bumpkin.gd
# (bumpkin_test.glb nu, later bumpkin_man.glb met hetzelfde skelet).
$bdir = Join-Path $PSScriptRoot 'bumpkin'
New-Item -ItemType Directory -Force $bdir | Out-Null
foreach ($f in 'bumpkin_test.glb', 'bumpkin_man.glb', 'bumpkin_anim.json') {
    $src = Join-Path $PSScriptRoot "..\bumpkin\$f"
    if (Test-Path $src) {
        Copy-Item $src (Join-Path $bdir $f) -Force
        Write-Host "gekopieerd: bumpkin/$f"
    } else { Write-Host "ontbreekt (overgeslagen): ..\bumpkin\$f" }
}
