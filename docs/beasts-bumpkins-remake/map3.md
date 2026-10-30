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
| Dorpelingen | 3 m, 2 v, 1 krijger type 7 (Pigsy): krijger = gewone volwassen man (`sex` 7) |
| Wezens | 7, eigenaar 4: 4x 13/23 (wolf), 2x 13/29 en 1x 14/24: alle zeven als `Wolf` |
| Generators | 2 (83,32) en (105,109), spawnen koeien; `koe_generator` geldt per generator |
| Voorwerpen | gouden kelk (96,18), naast twee wolven (97,17/18); 6 goud, 1 drankje |
| Missie | kas 7.000; winst kas > 24.999 (`cash>`) of kelk naar de vlag (conditie 12); verlies < 2 |

## Placeholder / nog niet

- **Gouden kelk**: staat als object (gouden blokbeker), nog niet op te rapen. Doel is nu alleen de kas; de kelk-route
  sluit aan op het algemene "voorwerp naar de vlag" (`spel.json` `_doel_kelk`).
- **Put** en **voetvolkgilde**: blok-placeholders (`view/props.gd`), blokkeren hun tegel(s), geen gedrag, niet
  bouwbaar. Gildelimiet 6 en gildeleden ontbreken.
- **Wolfsoorten** 13/29 en 14/24: wat ze in het origineel zijn is niet nagekeken; nu dezelfde wolf.
- Hut: voorgebouwd als afgebouwd Plan, draai vrij gekozen (deur bij het pad).
