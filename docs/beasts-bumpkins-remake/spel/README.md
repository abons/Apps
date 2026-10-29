# Beasts & Bumpkins remake: fundament (missie 1, Aorta)

Godot 4.7.2 (Forward+, GDScript, pc eerst). Het eiland Aorta uit de originele kaartdata, zes dorpelingen onder
spelersbesturing, dag/nacht, seizoenen en weer, bouwen (hut, loods, kippenhok; prijs uit de kas), koeien claimen en het
missiedoel (6 dorpelingen + 4 eigen koeien, verlies onder 2), gezinnen (stel in een hut met een vrij bed krijgt een kind).
Nog geen winkels/inkomsten of vijanden.

## Draaien

Snelst: rechtermuisknop op `speel.ps1` > **Run with PowerShell** (sync, import en spelen in een keer;
`speel.ps1 -Seizoen winter -Uur 22` voor een ander begin).

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
| links klikken op een koe | de eerste volwassene uit de selectie claimt haar (paarse halsband + bel); nog eens = loslaten |
| rechts klikken | selectie weg |
| rechts slepen, Q/E | camera draaien (PgUp/PgDn kantelen) |
| WASD/pijlen, schermrand | pannen (begrensd tot het eiland) |
| wiel | zoomen (2 m tot eilandoverzicht) |
| Spatie, 1 / 2 / 4 | pauze, tempo 1x/2x/4x |
| B / L / H, R, Esc | bouwen: hut / loods / kippenhok, draaien, stoppen |
| K, N | regen automatisch/aan/uit, volgend seizoen (debug) |

Lopen kan iedereen; vechten en werken alleen volwassenen (`Wereld.geef_bevel`, nog zonder invoer en zonder gedrag).

## Structuur

- `data/` `spel.json` (tegelmaat 2 m, 10 Hz, looptempo, klok), `tegels.json` (kleur, loopbaar, snelheidsfactor: pad 1,15, gras 1, zand 0,9; water en rots niet loopbaar), `objecten.json` (klasse-id naar naam, model, voetafdruk, blokkeert).
- `sim/` zonder Node, dus headless te testen: `Wereld` (staat, vaste tik, klok, seizoen, weer, bevelen), `Raster`, `Router` (A* met grondprijs, port van beasts-src `Router.kt`, plus `glad` voor rechte routes), `Dorpeling`, `Vee` (koe: zwerft rond generator of, eigen, rond het kampvuur), `Plan`, `Gegevens`.
  Missie 1 in `Wereld`: kas (`spel.json` `start_kas`, `prijzen`, betaald bij `plan_zet`), koe-generator (klasse 171, `koe_generator`: start 1, max 3 wilde, elke 45 s; uit `m01.json` p5=1/p6=3, betekenis aangenomen), `geef_claimbevel`, `uitslag` + signaal `missie_einde`.
  Gezin (`Wereld._gezin`, port van beasts-src `family`, waarden in `spel.json` `gezin`): bedden = 2 per afgebouwde hut; `ruimte()` = bedden - iedereen - wiegen - baby's. Een vrije man + vrouw lopen naar de deurtegel (`Plan.deur_tegel`, voordeur aan -x bij draai 0) en verdwijnen naar binnen; 12 s later komt zij met de baby op de arm (5 s), dan staat er een jongen of meisje (hash, geen rng), 150 s later volwassen (glb wisselt). Ouders rusten 75 s. Een bevel van de speler breekt het af. ⚠️ Met 6 startbewoners zijn er 4 hutten nodig voor het eerste kind.
- `view/` `WereldView` spiegelt de sim, `TerreinView` (een mesh met vertexkleur en hoogte, water, MultiMesh-bomen en -rotsen), `Props` (placeholders), `Bumpkin` (geanimeerde man, `volg()`-modus voor de sim), `Licht`, `Regen`, `Bestuur`, `Hud`.
- `shaders/` terrein (vijf texturensets, seizoenstint, sneeuw, nat), natuur_wind (gesynct uit modellen/natuur), natuur_steen (rotsen met sneeuw) en water (diepte, schuim).
- `main.gd` zet alles in elkaar en bevat de scenario's. `test/` simtest, routetijd en glad_test. `screenshots/` verificatieframes.

De sim tikt op 10 Hz los van het renderen; de view interpoleert tussen twee tikken. Looptempo = 0,849 m/s (animatie-sidecar) x `looptempo` 2,0 (spel.json) x tegelfactor. Routes worden recht getrokken (`Router.glad`). De loopanimatie volgt de grondsnelheid via `Bumpkin.gang`: 0 clip exact op tempo (cadans 2x, druk), 1 `SCHREDE` 1,4 (standaard: rustiger, lichte voetglijding), 2 blend naar de rennen-clip (ziet eruit als joggen).
Tijd: een dag-nacht is 270 s (180 dag, 90 nacht), een seizoen is een dag-nacht. Begint in de lente.

## Modellen en natuur

Kaartobjecten gebruiken de glb's uit `modellen/natuur/` (sync.ps1 kopieert ze, de terreintexturen, `natuur_wind.gdshader` en de koe):
`data/objecten.json` kiest per klasse-id `natuur:<glb>` (+ `varianten` met gewichten, `schaal`); `view/natuur.gd` laadt ze, zet de
wind- en steen-shader op de materialen, LOD (`visibility_range`, 28 m) en de seizoenstint; `view/props.gd` maakt de losse objecten en het
kampvuur-effect (GPUParticles3D vlammen en rook op `vuur_bron`, OmniLight3D flikkert in `WereldView`). Bomen zijn gewone instanties
(geen MultiMesh: `visibility_range` werkt niet per MultiMesh-instantie). `decoratie` in objecten.json (rotstegels op rots/rotsrand, struiken,
stronken) is ALLEEN weergave: de sim leest het niet en geen tegel wordt erdoor geblokkeerd. Terrein: `shaders/terrein.gdshader` mengt vijf
texturensets (Texture2DArray, 2,8 m per herhaling) uit de hoekgewichten van `TerreinView._splat()`. De koe (klasse 171) komt uit `view/koe.gd`
(pad, verborgen onderdelen en animatienaam staan alleen daar; nieuwe glb = sync + import). Seizoen: `Natuur.werk_seizoen()` (tint, rotssneeuw) en
`TerreinView.zet_sneeuwlaag()` (winter), aangeroepen vanuit `WereldView.werk_seizoen()`.
Scenario's voor frames: overzicht, dorp, selectie, pad, loop, vlag, bos, rots, koe, bouw (hut, loods en kippenhok naast het kampvuur, 4x), claim, gezin (4 hutten, het eerste stel). De oude blokjes-placeholders in `props.gd` zijn alleen nog terugval als een glb ontbreekt.
Uiterlijk per dorpeling: `Bumpkin.glb_voor(geslacht, leeftijd)` kiest een van de zes glb's (man, vrouw, jongen, meisje, oudere man/vrouw; kinderen zijn al 1,11 m in de glb). `sex` 13 = jongen, 14 = meisje is een aanname (niet geverifieerd). Ontbreekt een glb: de man (kind op 0,81x).
Bouwplaats: houtstapel en steenhoop naast het plan slinken tot 35 % met de voortgang; bouwmenu: hut (B), gereedschapsloods (L, 5x2) en kippenhok (H, 2x2), `Bouwmenu.GEBOUWEN` + `Wereld.BOUWSOORTEN`; glb's op ware grootte, een mensendeur schaalt. Hut klaar = `peasant_hut_rt.glb`, geschaald op de voordeur: 1,15x de langste volwassene (1,37 m) = 1,58 m, dat is de glb op ware grootte; voetafdruk dus 4x4 tegels (7,6 x 7,1 m incl. hek). Die glb (25 MB) staat niet in git: `blender -b -P ../modellen/peasant_hut_realtime.py`, anders blijft het een bruine kist.
Hoogte (rotsboog, strand) is alleen weergave; de sim is plat.
