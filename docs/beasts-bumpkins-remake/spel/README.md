# Beasts & Bumpkins remake: fundament (missie 1, Aorta)

Godot 4.7.2 (Forward+, GDScript, pc eerst). Het eiland Aorta uit de originele kaartdata, zes dorpelingen onder
spelersbesturing, dag/nacht, seizoenen en weer. Nog geen economie, gebouwen, dieren of vijanden.

## Draaien

```
G=$LOCALAPPDATA/Microsoft/WinGet/Packages/GodotEngine.GodotEngine_Microsoft.Winget.Source_8wekyb3d8bbwe/Godot_v4.7.2-stable_win64_console.exe
powershell -File sync.ps1                       # kaart (data/origineel/) en glb's (assets/) kopieren
"$G" --headless --path . --import               # eerste keer en na elke sync
"$G" --path .                                   # spelen
"$G" --headless --path . --script res://test/sim_test.gd    # simtest (zonder GPU)
"$G" --path . --write-movie out/x/f.png --fixed-fps 10 --quit-after 60 -- --scenario=selectie   # frames (map out/x moet bestaan)
```

Opties na `--`: `--seizoen=lente|zomer|herfst|winter`, `--uur=12`, `--tempo=2`, `--regen`, `--fps` (frametijden loggen),
`--gang=0|1|2` (loopanimatie, zie onder), `--scenario=overzicht|dorp|selectie|pad|loop` (gescripte camera/invoer voor frames).

`data/origineel/map1.json` komt uit de gedecodeerde originele spelbestanden (auteursrecht): staat in `.gitignore`, net als `assets/`.

## Besturing

| invoer | doet |
| --- | --- |
| links slepen | selectiekader (Shift = toevoegen) |
| links klikken op unit | die unit kiezen |
| links klikken op grond | loopbevel voor de selectie; meerdere units waaieren uit rond de tegel |
| rechts klikken | selectie weg |
| rechts slepen, Q/E | camera draaien (PgUp/PgDn kantelen) |
| WASD/pijlen, schermrand | pannen (begrensd tot het eiland) |
| wiel | zoomen (2 m tot eilandoverzicht) |
| Spatie, 1 / 2 / 4 | pauze, tempo 1x/2x/4x |
| K, N | regen automatisch/aan/uit, volgend seizoen (debug) |

Lopen kan iedereen; vechten en werken alleen volwassenen (`Wereld.geef_bevel`, nog zonder invoer en zonder gedrag).

## Structuur

- `data/` `spel.json` (tegelmaat 2 m, 10 Hz, looptempo, klok), `tegels.json` (kleur, loopbaar, snelheidsfactor: pad 1,15, gras 1, zand 0,9; water en rots niet loopbaar), `objecten.json` (klasse-id naar naam, model, voetafdruk, blokkeert).
- `sim/` zonder Node, dus headless te testen: `Wereld` (staat, vaste tik, klok, seizoen, weer, bevelen), `Raster`, `Router` (A* met grondprijs, port van beasts-src `Router.kt`, plus `glad` voor rechte routes), `Dorpeling`, `Gegevens`.
- `view/` `WereldView` spiegelt de sim, `TerreinView` (een mesh met vertexkleur en hoogte, water, MultiMesh-bomen en -rotsen), `Props` (placeholders), `Bumpkin` (geanimeerde man, `volg()`-modus voor de sim), `Licht`, `Regen`, `Bestuur`, `Hud`.
- `shaders/` terrein (seizoenstint, sneeuw, nat) en water (diepte, schuim).
- `main.gd` zet alles in elkaar en bevat de scenario's. `test/` simtest, routetijd en glad_test. `screenshots/` verificatieframes.

De sim tikt op 10 Hz los van het renderen; de view interpoleert tussen twee tikken. Looptempo = 0,849 m/s (animatie-sidecar) x `looptempo` 2,0 (spel.json) x tegelfactor. Routes worden recht getrokken (`Router.glad`). De loopanimatie volgt de grondsnelheid via `Bumpkin.gang`: 0 clip exact op tempo (cadans 2x, druk), 1 `SCHREDE` 1,4 (standaard: rustiger, lichte voetglijding), 2 blend naar de rennen-clip (ziet eruit als joggen).
Tijd: een dag-nacht is 270 s (180 dag, 90 nacht), een seizoen is een dag-nacht. Begint in de lente.

## Placeholder

Alle modellen behalve de dorpeling: bomen (den, spar, rond; ook gegenereerd op bosgrond), rotsblokken, paddenstoelen, vlag, kampvuur, bron, beker.
Namen in de scene (`Bomen_boom_den`, `kampvuur`, `vlag`, ...) zijn de koppelpunten voor echte modellen. De koe-generator (klasse 171) is alleen een lege marker.
Kinderen (`sex` 13/14, niet geverifieerd) zijn de mangeometrie op schaal 0,81. De hut-glb wordt gesynct maar nog niet gebruikt.
Hoogte (rotsboog, strand) is alleen weergave; de sim is plat.
