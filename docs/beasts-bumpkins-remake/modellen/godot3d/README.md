# Hut 3D demo (Godot 4)

Echte 3D-scène voor de Beasts & Bumpkins-remake: één hut (glTF) op een grasvlak, dag/nacht in 60 s,
RTS-camera, dorpeling die door de voordeur in en uit loopt. Godot 4.7, Forward+, alles in GDScript.

## Draaien

```
G=$LOCALAPPDATA/Microsoft/WinGet/Packages/GodotEngine.GodotEngine_Microsoft.Winget.Source_8wekyb3d8bbwe/Godot_v4.7.2-stable_win64_console.exe
"$G" --headless --path . --import          # eerste keer en na elke glb-sync
"$G" --path .                               # vrij spelen
"$G" --path . -- --demo                     # autopiloot, 46 s
"$G" --path . --write-movie out/frame.png --fixed-fps 10 --quit-after 462 -- --demo   # frames opnemen
```

Autopiloot: middag-overzicht → schemer, inzoomen op de deur, dorpeling gaat naar binnen →
nacht met kaars in het raam en rook → dorpeling komt naar buiten (deurgloed) → dageraad.

## Besturing

| invoer | doet |
| --- | --- |
| wiel | zoom, 2 m (deurhoogte) tot 40 m |
| rechts/midden slepen, Q/E | draaien |
| PgUp/PgDn | kantelen |
| links slepen, WASD/pijlen, muis aan de rand | pannen |
| T | +3 uur |
| F | zomer/winter (winter: korte dag, lage zon, dor gras, altijd rook) |
| Esc | stoppen |

## glb syncen

`powershell -File sync_glb.ps1` kopieert `../peasant_hut_rt.glb` en `../peasant_hut_rt_lod1.glb` naar `hut/` (genegeerd
door git); daarna opnieuw `--import`. Ontbreekt de kopie, dan laadt `main.gd` `../peasant_hut_rt.glb`
runtime via `GLTFDocument`. LOD1 neemt het over vanaf 28 m (`LOD_WISSEL` in `main.gd`).

## Knopen die de scène zoekt (op naam, ondiepste treffer)

| knoop | gebruik | terugval |
| --- | --- | --- |
| `deur_voor` (of `voordeur*`) | scharnier-Empty, draait om lokale Y, open = **−90°** (naar buiten) | geen deuranimatie |
| `deur_aanbouw` | alleen gevonden/gelogd, niet geanimeerd | — |
| `deur_voor_drempel` | looproute dorpeling, deurgloed | 172° op r=1,7 rond (0.65, 0.05) |
| `kaars` | OmniLight met flikkering, aan als de dorpeling binnen is en het donker is | (1.16, 1.07, 1.62) |
| `rook_bron` | GPUParticles3D, aan bij nacht of winter | (1.02, 3.95, 1.59) |
| `ruit*` (mesh) | krijgt een gloeiend materiaal als de kaars brandt | — |

Coördinaten in Godot (Y-op); Blender (x,y,z) → Godot (x, z, −y). De log print bij start wat gevonden is.

## Bestanden

`main.gd` scène, licht, dorpeling, autopiloot · `rts_camera.gd` camera · `gras.gdshader` grond ·
`sync_glb.ps1` · `screenshots/` frames uit de autopiloot.
