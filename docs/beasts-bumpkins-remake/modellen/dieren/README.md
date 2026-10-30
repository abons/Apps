# Dieren: AI-route (TRELLIS)

Proef 2026-10-30: de wolf uit TRELLIS (beeld -> 3D) op het bestaande wolfskelet, naast de procedurele
`wolf.py`. Schakelaar: `spel/data/spel.json` `wolf_model` = `"trellis"` | `"procedureel"` (voor frames:
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

## Voor koe, personages, gebouwen

- **Dieren**: goed bruikbaar als het skelet al bestaat (`*_rig.py`): alleen `MAAT_T` aflezen + gewichten.
  Een uur werk per dier in plaats van een dag. Invoerbeeld in de rustpose van het rig (kop recht vooruit).
- **Personages**: lastiger; handen/vingers en gezicht zijn bij ~6k driehoeken klonterig, kleding en lijf
  vergroeid. Alleen voor verre figuren; de Bumpkin-rig (`modellen/bumpkin/`) vraagt T/A-pose als invoer.
- **Gebouwen**: kansrijk (statisch, geen rig), maar rechte lijnen/dakpannen worden zacht en de textuur heeft
  ingebakken schaduw. Proberen met een orthografisch 3/4-beeld op wit.
