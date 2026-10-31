# Missie 3: Gouden kelk van Barathkar (kaart)

2026-10-30. `data/origineel/map3.json` uit `M3.MIS` met `lokaal/map2/maak_map.py 3 <pad>` (lokaal, nooit in git).
Laden: `--missie=3`; test `test/missie3_test.gd`.

| punt | waarde |
| --- | --- |
| Raster | 192 x 192; niet-void x 46..153, y 0..125 = **108 x 126**; raakt de bovenrand (y 0) |
| Tegels | gras 2.954, rots 2.236 + rotsrand 1.818, water 814, aarde 206, bosgrond 147, overig 144, zand 22 |
| Rand | 382 randtegels: rots 84 %, water 14 %, bos 3 % (map2.md tabel 3). Buiten = zwart (mist), geen zee |
| Bereikbaar | omhullende vanaf het kampvuur (59,10)..(137,112); geen bereikbare tegel raakt leeg (`RAND_DICHT`, test) |
| Dorp | kampvuur (102,82), vlag (104,79), bron (101,84); hut (98,80), put (101,80), voetvolkgilde (103,77) |
| Dorpelingen | 3 m, 2 v, 1 krijger type 7 (Pigsy) = voetsoldaat, lid van het voorgebouwde gilde |
| Wezens | 7, eigenaar 4: 4x sex 23 (wolf), 2x 29 (donkere wolf), 1x 24 (wesp, (127,78)); `hover_names.json` (BBTools) |
| Generators | 2 (83,32) en (105,109), spawnen koeien; `koe_generator` geldt per generator |
| Voorwerpen | gouden kelk (96,18), naast twee wolven (97,17/18); 6 goud, 1 drankje |
| Missie | kas 7.000; winst kas > 24.999 (`cash>`) of kelk naar de vlag (conditie 12); verlies < 2 |

## Placeholder / nog niet

- **Gouden kelk**: op te rapen, naar de vlag = +7.000 (`sim/voorwerpen.gd`); de tweede regel (+6.000) vuurt niet
  (eigen keuze, `spel.json` `_doel_kelk`).
- **Put** (2026-10-30): voorgebouwd Plan 3x3 (`bron.glb`) en bouwbaar vanaf M3 (40 kas); dorst > 90 s = gratis water
  halen (2 s). Effect op de levensduur nog niet.
- **Voetvolkgilde**: voorgebouwd 3x3, niet over vlag of kampvuur, bouwbaar vanaf M3 (50); man + klik op het gilde =
  voetsoldaat (30 kas, max 6 per gilde, hint 3-5), zwaard (`prop_zwaard`, schade 6, slag 0,8 s, bereik 1,5), boert
  niet, valt wolven binnen 8 tegels zelf aan. Gebouw = `voetvolkgilde_rt.glb` + standen (2026-10-31, `modellen/gebouwen/README.md`); zonder glb het blok uit `view/props.gd`.
- **Donkere wolf** (sex 29): `Wolf.soort = &"donkere_wolf"` (eigen glb), zelfde gedrag. **Wesp** (24): nog een gewone wolf.
- Hut: voorgebouwd als afgebouwd Plan, draai vrij gekozen (deur bij het pad).
