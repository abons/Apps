# Dieren: AI-route (TRELLIS)

Proef 2026-10-30: de wolf uit TRELLIS (beeld -> 3D) op het bestaande wolfskelet, naast de procedurele
`wolf.py`. Schakelaar: `spel/data/spel.json` `wolf_model` = `"tripo"` (standaard sinds 2026-10-30) | `"trellis"` | `"procedureel"` (voor frames:
`-- --wolf_model=procedureel`); zonder trellis-glb valt `WolfModel.maak` terug op de procedurele.

## Werkwijze (herhaalbaar)

1. **Invoerbeeld** (Gemini, uit het goedgekeurde concept): hele figuur, 3/4 van voren, witte achtergrond,
   niets afgesneden, staande rustpose. -> `lokaal/concept/img/<dier>_3d_invoer.png`.
2. **TRELLIS-Space** `https://trellis-community-trellis.hf.space`: geen login, gratis. Beeld uploaden,
   Generate, Extract GLB (standaardinstellingen) -> `lokaal/trellis/<dier>_trellis.glb` (gitignored).
   ⚠️ Chrome-besturing kan alleen de hoofdsessie, niet een subagent.
3. **Script** `blender -b -P wolf_trellis.py -- [zij] [poses] [detail]`: samenvoegen op afstand, losse
   eilandjes weg, schalen op de schofthoogte, centreren, skelet (`MAAT_T`) op de vorm, gewichten, clips van
   `wolf_rig.py`, export naar `spel/assets/wolf_trellis.glb` + `donkere_wolf_trellis.glb`.
   - `zij` -> `preview/wolf_trellis_zij.png`: zij/boven met raster per 10 cm en de botten erover. Daarop
     `MAAT_T` afgelezen (`y = -0,05 - (kolom-360)/400`, `z = 0,55 - (rij-240)/400`).
   - `poses` -> `preview/wolf_trellis_poses.png`; `detail` -> grote standen (lokaal).
   - Het log meldt per clip de ergste randrek en waar (bot, frame, positie).

## Wat TRELLIS levert, en de beperkingen

- 6.440 driehoeken, één mesh, één 1024-kleurtextuur. Gesplitst op UV-naden: na samenvoegen één eiland.
  Assen kloppen al (kijkt naar Blender -Y = Godot +Z, grond onder), maat in eigen eenheden: schalen.
- **Alleen kleur**, met ingebakken licht, en licht/vlak: in het spel bijna wit. `toon()` maakt hem donkerder
  en contrastrijker. Geen normal/ORM-map; de vacht is geschilderd, geen reliëf.
- **Pose = invoerbeeld**: kop hoog en ver naar voren, staart kort. Dus het skelet op de vorm zetten, niet
  andersom; de clips (absolute IK-doelen) geven dan "onbereikbare beendoelen" (lopen 26, rennen 11, dood 34
  van alle frames x poten) en de standen worden iets anders dan bij de procedurele wolf.
- Poten zijn dikke klompjes rond het balgewricht: half middenvoet/half zool scheurt bij de galop. Daarom de
  hele poot aan de middenvoet (max. 30 % zool) en pols/hak over 14 cm overvloeien (`poten()`); nog een
  klein knikje bij de opgetilde voorpoot in `rennen`.
- Ogen staan in de textuur (geen gloei-bol zoals bij `wolf.py`): rode ogen zijn op spelafstand weg.
- Donkere variant = kleurbewerking op de textuur met een borst/keelmasker uit de mesh (per texel de
  3D-positie via de UV's).
- Uitkomst: anatomisch schoner en "echter" dan procedureel, maar leest als vos/husky (slank, kop hoog),
  minder als de ruige B&B-wolf. Zie `spel/screenshots/wolf_vergelijk.jpg` (links procedureel, rechts trellis).

## Tripo-route: TRELLIS-mesh naar een referentie-render (2026-10-30, `wolf_tripo.py`)

Tripo (gratis plan) mag niet exporteren; alleen schermafbeeldingen als referentie (`lokaal/tripo/*.png`, nooit in git).
`blender -b -P wolf_tripo.py -- [zij] [poses] [ankers]`, ~30 s -> `spel/assets/wolf_tripo.glb` + `donkere_wolf_tripo.glb`.
- Silhouet van de ruwe TRELLIS-mesh en van `wolf_links.png` (achtergrond weg: `projectie.segmenteer`) als contour;
  41 `ANKERS` (m op TRELLIS -> pixel) + tussenpunten = thin-plate spline (y, z). Elke vertex en `MAAT_T` gaan erdoor:
  kop laag, lange dunne poten, hangende pluimstaart. x: wortel van de oppervlaktefactor rond lijf- of pootmidden,
  staart x 1,6. Geen vouwen (det min 0,26).
- Textuur 2048: per texel de referentiepixel (beide kanten gespiegeld, scherend iets naar binnen, fijne ruis).
  Ogen = rode texels -> gloeibollen (`extras(haar=0)`). Donker: zwart, keel/borst licht via een gebied in referentiepixels.
- ⚠️ Textuur komt uit de Tripo-render: glb's, previews en spelframes blijven lokaal (`lokaal/tripo/`).
  Voor een publieke release eerst een eigen geschilderde textuur.
- Rek (p99.9): lopen 3,7, rennen 3,1, bijten 3,4, dood 3,2 (tussen de dijen). Oordeel: 7,5 tegen 6,5 (trellis).
- Hunyuan3D-2.1 (vorm, `lokaal/hunyuan/`) zou als basis nog beter passen, maar de licentie sluit de EU uit
  (zie `../../README.md`): niet gebruikt.

## Koe naar de Tripo-referentie (2026-10-30, `koe_tripo.py`)

Geen TRELLIS-koe (quotum op): basis is de procedurele koe zelf. Eerst `koe.py` (schrijft `preview/koe.blend`), dan
`blender -b -P koe_tripo.py -- [zij] [poses] [ankers] [kx=] [kop=] [oor=]`, ~35 s -> `spel/assets/koe_tripo.glb` (+ `koe_tripo_anim.json`).
Schakelaar `spel.json` `koe_model` = `"tripo"` (standaard sinds 2026-10-30) | `"procedureel"`, frames `-- --koe_model=procedureel`.
- Referenties `lokaal/tripo/koe/` (nooit in git). Silhouet: `segmenteer` + vlakke grijze vloerschaduw weg; staart uit
  `koe_links` gesneden (`STAART_RAND`: ligt tegen de billen). 45 `ANKERS`; poten naar het NABIJE been (achterrand binnen
  het silhouet = losse punten). TPS (y, z), schoft als procedureel (1,11 m): koe wordt korter (1,36 m) en ronder.
- x: oppervlaktefactor x `KX` 0,93, kop/kaak x `KOP` 0,70, oren x `OOR` 1,35 (naar `koe_voor`).
- Staart: nieuwe rustbotten langs `STAART_LIJN` (tegen de billen), vertices via lineaire skinning oud -> nieuw.
- Kleur (zelfde UV-atlas, alleen mat_lijf; normaal-map blijft, ORM-ruwheid uit de helderheid): links uit `koe_links`,
  rechts uit `koe_rechts` (gespiegeld, eigen TPS: andere vlekken), voorkant (kop, borst) uit `koe_voor` met z-buffer,
  oren zwart. Studiolicht eruit (`ontlicht`, wit 0,84), buik +30 %, staart en achterkant rond de staart wit.
  `koe_boven` niet gebruikt: de rug uit beide zijkanten klopte al met het bovenaanzicht.
- Rek (p99.9) als procedureel: lopen 3,8 (3,7), sterven 7,3 (6,5), geboorte 5,4 (4,5). Lopen 0,71 m/s ongewijzigd.
- Oordeel: 7 tegen 6,5 (procedureel): natuurlijker vorm en vlekken, echte kop; zwakker: dunne onderbenen, achteraanzicht
  wat vlak, vlekranden zachter. Kalveren (schaal 0,55) en wilde koeien gebruiken dezelfde glb.
  Vergelijking: `lokaal/tripo/koe/koe_tripo_zij.png`, `koe_tripo_poses.png`, `koe_spel_vergelijk.png` (links procedureel).

## Voor koe, personages, gebouwen

- **Dieren**: goed bruikbaar als het skelet al bestaat (`*_rig.py`): alleen `MAAT_T` aflezen + gewichten.
  Een uur werk per dier in plaats van een dag. Invoerbeeld in de rustpose van het rig (kop recht vooruit).
- **Personages**: lastiger; handen/vingers en gezicht zijn bij ~6k driehoeken klonterig, kleding en lijf
  vergroeid. Alleen voor verre figuren; de Bumpkin-rig (`modellen/bumpkin/`) vraagt T/A-pose als invoer.
- **Gebouwen**: kansrijk (statisch, geen rig), maar rechte lijnen/dakpannen worden zacht en de textuur heeft
  ingebakken schaduw. Proberen met een orthografisch 3/4-beeld op wit.
