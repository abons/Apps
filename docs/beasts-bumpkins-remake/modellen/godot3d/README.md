# Hut 3D demo (Godot 4)

Echte 3D-scène voor de Beasts & Bumpkins-remake: één hut (glTF) op een grasvlak, dag/nacht in 60 s,
RTS-camera, een geanimeerde dorpeling (`Bumpkin`) die door de voordeur in en uit loopt, bouwt, zwaait en stenen gooit. Godot 4.7, Forward+, alles in GDScript.

## Draaien

```
G=$LOCALAPPDATA/Microsoft/WinGet/Packages/GodotEngine.GodotEngine_Microsoft.Winget.Source_8wekyb3d8bbwe/Godot_v4.7.2-stable_win64_console.exe
"$G" --headless --path . --import          # eerste keer en na elke glb-sync
"$G" --path .                               # vrij spelen
"$G" --path . -- --demo                     # autopiloot, ~60 s
"$G" --path . -- --toon [--uur=12 --yaw=3.14]  # camera volgt de dorpeling, korte animatieshow
"$G" --path . --write-movie out/frame.png --fixed-fps 10 --quit-after 620 -- --demo   # frames opnemen
```

Eerst `powershell -File sync_glb.ps1` (hut- en bumpkin-glb, zie onder). Autopiloot: middag-overzicht → schemer, inzoomen op de deur, dorpeling gaat naar binnen →
nacht met kaars in het raam en rook → dorpeling komt naar buiten (deurgloed) → dageraad → hij loopt naar het hek, bouwt (hamer), één zwaardzwaai, één steenworp.

## Besturing

| invoer | doet |
| --- | --- |
| wiel | zoom, 2 m (deurhoogte) tot 40 m |
| rechts/midden slepen, Q/E | draaien |
| PgUp/PgDn | kantelen |
| links slepen, WASD/pijlen, muis aan de rand | pannen |
| R | rennen aan/uit (voor volgende loopopdrachten) |
| B | bouwen aan/uit (hamer; start zodra hij stilstaat) |
| V | zwaardzwaai (bovenlichaam, over idle/lopen) |
| G | steen gooien naar het punt onder de muis |
| T | +3 uur |
| F | zomer/winter (winter: korte dag, lage zon, dor gras, altijd rook) |
| Esc | stoppen |

## glb syncen

Naast de hut kopieert het script `../bumpkin/bumpkin_test.glb`, `bumpkin_man.glb` en `bumpkin_anim.json` naar `bumpkin/` (genegeerd door git; ontbrekende worden overgeslagen).
`powershell -File sync_glb.ps1` kopieert `../peasant_hut_rt.glb` en `../peasant_hut_rt_lod1.glb` naar `hut/` (genegeerd
door git); daarna opnieuw `--import`. Ontbreekt de kopie, dan laadt `main.gd` `../peasant_hut_rt.glb`
runtime via `GLTFDocument`. LOD1 neemt het over vanaf 28 m (`LOD_WISSEL` in `main.gd`).

## Bumpkin (`bumpkin.gd`, `class_name Bumpkin`)

Herbruikbare `Node3D`: laadt `BUMPKIN_GLB` (nu `bumpkin_test.glb`, later `bumpkin_man.glb`, zelfde skelet) en
`bumpkin_anim.json` (`{naam: {loop, duur_s, snelheid_mps, impact_s}}`), bouwt een AnimationTree:
BlendSpace1D idle/lopen/rennen op snelheid → TimeScale → Transition (loco | bouwen) → OneShot (zwaard | steen,
gefilterd op bovenlichaam). Zonder glb: capsule-terugval met dezelfde API.

| API | doet |
| --- | --- |
| `loop_naar(doel, rennen := false)` | loopt/rent naar doel (draait eerst bij, versnelt/remt zacht); signal `aangekomen` |
| `werk(aan)` | hamerlus (hamer zichtbaar); start pas bij stilstand, `loop_naar` stopt hem |
| `val_aan()` | zwaardzwaai (zwaard zichtbaar), stopt werken |
| `gooi_steen(doel)` | draait naar doel, `aanval_steen`, bij `impact_s` (release) vliegt een steen in een boog; werkt ook zonder clip |
| `kijk_naar(richting, direct)`, `zet_nacht(f)`, `tempo` | richting, randlicht + meelopend licht 's nachts, tempofactor (anim schaalt mee) |
| signal `impact(welke)` | `bouwen` (elke lus), `aanval_zwaard` (op `impact_s`), `steen` (bij inslag) |

Voeten glijden niet: loopsnelheid = `snelheid_mps` × `tempo`, afspeeltempo = `tempo`. Het model kijkt in Blender
naar −Y; na glTF-import wijst dat langs lokale **+Z** (de importer draait niet), dus yaw = `atan2(dx, dz)`
(`MODEL_YAW_OFFSET` in `bumpkin.gd`). De hut-scène voegt `Hek` toe (autopiloot-werkplek).

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

`main.gd` scène, licht, deur, autopiloot, toonbank · `bumpkin.gd` dorpeling · `rts_camera.gd` camera · `gras.gdshader` grond ·
`sync_glb.ps1` · `screenshots/` frames uit de autopiloot.
