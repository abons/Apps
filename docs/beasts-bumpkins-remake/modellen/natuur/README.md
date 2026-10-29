# Natuur en props, missie 1

Real-time modellen voor Godot 4 (pc eerst), gebouwd met Blender 5.2 headless naar de goedgekeurde
concepten van ronde 2. Meters, Z-op in Blender (Y-op na import), oorsprong midden onder. Elke glb heeft
zijn texturen ingebakken. LOD1 zit **in dezelfde glb** als node `<naam>_lod1`: zet in Godot een
`visibility_range` op beide nodes (bijv. LOD0 tot 18 m, LOD1 vanaf 16 m).

## Assets

Driehoeken: LOD0 / LOD1 (+ sneeuwlaag).

| asset | bestand | tris | bijzonder |
| --- | --- | --- | --- |
| grote den, 6,6 m | `den_groot.glb` | 4120 / 540 (+404) | wind, seizoenstint, `den_groot_sneeuw` |
| spar, 4,8 m | `spar.glb` | 4186 / 540 (+412) | idem, blauwgroen |
| jonge den, 1,9 m | `jonge_den.glb` | 950 / 244 (+76) | idem |
| stronk + 5 houtstukken | `stronk.glb` | 456 | jaarringen op het snijvlak |
| loofboom, 5,6 m | `loofboom.glb` | 1888 / 540 (+230) | wind, tint, sneeuw; eivormige kroon |
| jonge loofboom, 3,9 m | `loofboom_jong.glb` | 1180 / 380 (+104) | idem |
| bloeiende struik, 1,8 m breed | `struik_bloem.glb` | 900 / 280 | wind; bloemen eigen materiaal (geen tint) |
| kleine struik, 1,2 m | `struik_klein.glb` | 440 / 146 | wind, tint |
| rotstegel 1..6, 2 x 2 m | `rots_1.glb` .. `rots_6.glb` | ~2600 / ~650 | vormen van rock01..06, gebakken |
| klifrand recht / buitenhoek / binnenhoek | `klif_recht.glb`, `klif_hoek_buiten.glb`, `klif_hoek_binnen.glb` | ~3200 / ~800 | stap 2,0 m, hoge kant +y; lassen in elke draaiing |
| paddenstoel, 0,4 m | `paddenstoel.glb` | 864 | pickup, groter dan echt |
| zilveren beker, 0,55 m | `zilveren_beker.glb` | 2224 | metaal, emissieve smaragden |
| vlag, paal 2,4 m | `vlag.glb` | 1000 | doek fladdert (UV2), vertexgroep `doek` |
| kampvuur, 1,1 m | `kampvuur.glb` | 1452 | `kampvuur_gloed` + `kampvuur_vlam` emissief, Empty `vuur_bron` (0, 0, 0,22) |
| houtstapel, 2,2 m | `houtstapel.glb` | 700 | 3 + 2 stammen |
| steenhoop, ~2 m | `steenhoop.glb` | 1520 | gebakken |
| bron (put, well 47/118, pas in latere missies), 4,6 x 4,7 m | `bron.glb` | 9988 | `bron_water` en `bron_straal` (BLEND, straal heeft trilling in UV2) |
| bronplas (spring 144, missie 1), 2 m | `bronplas.glb` | 1464 | kring keien (gebakken, steen-shader) + `bronplas_water` (BLEND) |
| hekpaal | `hek_paal.glb` | 50 | |
| heksegment, 2 m (palen op x = +-1) | `hek_segment.glb` | 2676 | oranje touw om de kruisingen |
| poort, doorgang 2 m | `poort.glb` | 2224 | blauwe steen emissief, keien met mos |
| akker kaal, 2 x 2 m | `akker_kaal.glb` | 2822 | vier ruggen langs x |
| akker rijp, 2 x 2 m | `akker_rijp.glb` | 3830 | tarwe als gekruiste kaarten (`akker_rijp_gewas`, wind) |

## Wind (alle planten, tarwe, vlag, waterstraal)

In **UV2** (glTF `TEXCOORD_1`), niet in COLOR_0: glTF en Godot vermenigvuldigen COLOR_0 met de kleur.
`UV2.x` = zwaai van de hele plant (0 voet .. 1 top); `y = 1 - UV2.y` (glTF draait v om):
`fract(y)` = trilling van tak/blad/doek (0 aanhechting .. 1 punt), `floor(y) / 8` = fase per tak.
Shader: `natuur_wind.gdshader` (schors met `alpha_kaart = false`, `use_orm = true`; vlag met `vlag = 1`).

## Seizoenen

Het gebladerte is neutraal bleek geelgroen getextureerd; de kleur komt uit `baseColorFactor`
(of `tint` in de shader). Zomer = de waarde in de glb.

| materiaal | lente | zomer | herfst |
| --- | --- | --- | --- |
| `naald_den` | 0.21 0.37 0.18 | 0.16 0.30 0.15 | 0.17 0.28 0.15 |
| `naald_spar` | 0.23 0.40 0.42 | 0.19 0.35 0.39 | 0.19 0.33 0.35 |
| `blad_loof`, `blad_loof_jong` | 0.40 0.62 0.24 | 0.28 0.48 0.20 | 0.78 0.42 0.12 |
| `blad_struik` / `blad_struik_klein` | 0.30 0.52 0.22 | 0.19 0.36 0.15 / 0.40 0.60 0.24 | 0.60 0.36 0.14 |
| `tarwe` | 0.55 0.85 0.35 (groen) | 1 1 1 (rijp) | 1 1 1 |

Winter: zet de kindnode `<boom>_sneeuw` aan (materiaal `sneeuw`, eigen atlas); loofbomen eventueel op
de herfsttint of donker bruingrijs (0.30 0.27 0.22).

## Texturen

Gegenereerd in `textures/` (en ingebakken in de glb's):

- Kaartatlassen: `naald_atlas` (2048 x 1024: den, spar), `sneeuw_atlas` (1024 x 512), `blad_atlas`
  (2048: loof, fijn blad, struikblad, bloemen), `akker_atlas` (1024 x 1536: tarwe, blad); kleur PNG
  met alfa, normaal JPG.
- Gebakken per asset (1k, rotsen/klif/steenhoop/keien; paddenstoel 512): `_kleur`, `_normaal`, `_orm`.
- Eigen: `jaarringen_kleur`, `vlag_kleur`, `vlam_kleur`, `gloed_emissie`, `as_kleur`, `dakpan_paars_kleur`,
  `steen_licht_kleur`, `water_normaal`; ORM's van de Poly Haven-sets (`<naam>_orm.jpg`).
- **Terrein** (1024, 2 x 2 m per herhaling, naadloos): `terrein_{gras,bosgrond,rots,zand,water_rand}_{kleur,normaal,ruw}.jpg`.
  Normaal is OpenGL (Y+), zoals Godot wil.

Poly Haven-bronnen (CC0) staan in `../textures/BRON.md`.

## Bouwen

```
blender -b -P kaarten.py      # atlassen (eerst)
blender -b -P bomen.py
blender -b -P rotsen.py       # ~10 min (hoogteveld + bakken)
blender -b -P props.py
blender -b -P terrein.py
blender -b -P voorbeeld.py -- items=den_groot,den_groot:sneeuw,klif_rij@50
```

`voorbeeld.py` rendert op het iso-gezicht (ortho, yaw 225, pitch 30); `vergelijk_natuur.py` en
`terrein_vergelijk.py` zetten concept, origineel en render naast elkaar in `preview/*_vergelijk_r<n>.png`.

## Nog niet goed

- Rotsen: rots_4 en rots_6 blijven piramide-achtig; het concept heeft grotere, hoekiger platen.
  Elke tegel heeft een schort tot -0,35 m (verdwijnt onder het terrein).
- Klifranden: de lasranden kloppen (`klif_rij` in `preview/rotsen_vergelijk_r4.png`), maar het plateau
  (terrein op +2 m) moet uit de heightmap komen; de zijkant van een losse tegel is een vlakke wand.
- LOD1 van de bomen is iets lichter dan LOD0 (minder lagen).
- Bosgrond: te veel naalden; de bron heeft weinig detail op de muren en de deur valt weg.
- De glTF-import van Godot zet bij COLOR_0 de vertexkleur aan; die hebben deze glb's niet (wind zit in UV2).
