# Gebouwen

Gebouwen uit Beasts & Bumpkins in 3D, in de huisstijl van `../peasant_hut.py` (hoge Cycles-versie op de
sprite, iso-camera yaw 225 / pitch 30, ortho 21,9 px/m op 1x) en `../peasant_hut_realtime.py` (gebakken
game-glb, LOD0 + LOD1, ankers als lege nodes). Blender 5.2 headless; CUDA (OptiX werkt hier niet).

## Melkerij / boerderij (`melkerij_boerderij.py`)

Gedeelde code: `erf_lib.py` (materialen, riet als hair curves, iso-camera, licht, bakken naar glb);
drieluik voor de iteratie: `vergelijk_erf.py` (origineel | render | concept).

- Bouwen + render: `blender -b -P melkerij_boerderij.py -- schaal=4 samples=128`
  (geeft `melkerij_boerderij.blend` en `preview/melkerij_boerderij_render.png`).
- Game-glb: `blender -b -P melkerij_boerderij.py -- rt` (eerst de stap hierboven) geeft
  `melkerij_boerderij_rt.glb`, `melkerij_boerderij_rt_lod1.glb` en `rt_textures/melkerij_boerderij_*`;
  `rt_vergelijk` rendert alleen de glb's opnieuw (`preview/melkerij_boerderij_rt*.png`).
- Maat: 3,7 x 5,8 m muren, nok 4,3 m, schoorsteen tot 5,3 m, varkenshok 1,4 x 1,35 m achter de
  achtergevel. Teruggerekend uit `Dairy.png` (213x160).
- Driehoeken: zie de tabel onderaan. Atlassen: `opaak` (2048), `riet` (2048).
- Ankers (Empties): `deur` (scharnier; open naar buiten = **positieve graden als `dicht - hoek` om
  lokaal Z** in Blender, om lokaal Y in Godot; max. **100°**, eigenschap `open_graden`), `deur_drempel`
  (looppunt voor de deur), `rook_bron` (schoorsteenmond), `melkplek` (voor de gevel, koe op +x),
  `varkenshok` (midden van het hok), `varkenshok_voer` (buiten bij de trog).
- Rondes (Sonnet-jury, realisme / gelijkenis): 1: 6/7, 2: 7/7, 3: 6/8, 4: 6/7. Gestopt na 4.
- Nog mis: het riet is nog te schoon en egaal geel, de jury wil donkerder, verweerd en mossig riet met
  ruigere randen. De koeienvlekken lezen nog als plakplaatjes. Schoorsteen en dakkapel zijn in
  ronde 4 vergroot en nu juist te groot (ronde 3 was beter). Het varkenshok staat volgens de sprite
  1,5 m achter de achtergevel; in het concept staat het tegen de gevel.

## Kippenhok (`kippenhok.py`)

- Bouwen + render: `blender -b -P kippenhok.py -- schaal=8 samples=96 [deur=graden]` (deur staat
  standaard 20° open).
- Game-glb: `blender -b -P kippenhok.py -- rt` geeft `kippenhok_rt.glb`, `kippenhok_rt_lod1.glb`.
  Atlassen: `opaak`, `riet` en `grond` (stromat met de strohalmen erop gebakken). De kippen zijn
  spelfiguren: alleen in de render (`rt = weg`).
- Maat: in de sprite is het huisje 0,55 m breed, een poppenhuis naast een dorpeling van 1,37 m. Het hok
  is daarom 0,8 x 0,8 m met de nok op 1,3 m, zoals het concept; de stromat houdt de sprite-maat
  (~2,3 m). Het canvas van de render is 15 px (1x) hoger dan de sprite, voor de nok.
- Ankers: `deur` (scharnier van het kippendeurtje, zelfde conventie als de melkerij, max. **110°**),
  `deur_drempel` (dorpeling naast de loopplank), `kip_uitgang` (voet van de loopplank), `leg_nest`
  (in het legnest aan de +Y-kant, met eieren), `voerplek` (voor de voerbak), `rook_bron` (geen
  schoorsteen; op de nok, alleen voor de vorm).
- Rondes (realisme / gelijkenis): 1: 7/6, 2: 7/6, 3: 7/6. Gestopt: geen verbetering meer.
- Nog mis: het riet is te bleek en gekamd, de wanden lezen donker, en de kippen zijn bolletjes. De
  sprite is vooral stro met een lage hut; het hok is bewust groter. De gele vlek vooraan in de sprite
  is hier een hoop vers stro.

## Driehoeken

| gebouw | LOD0 | LOD1 |
| --- | --- | --- |

## Gereedschapsloods en molen (`gereedschapsloods.py`, `molen.py`)

Gedeelde code: `loods_molen_lib.py` (materialen, losse stenen, deuren met scharnier, iso-camera, licht);
real-time bake voor beide: `loods_molen_rt.py`; drieluik: `vergelijk_loods_molen.py` (origineel | render |
concept). Nieuwe Poly Haven-texturen: `white_plaster_rough_01`, `rusty_metal_02` (zie `../textures/BRON.md`).
De vergelijkingen per ronde staan in `preview/<naam>_vergelijk_ronde<n>.png`, de glb's naast de
Cycles-beauty in `preview/<naam>_rt_vergelijk.png` (beauty | LOD0 | LOD1, EEVEE).

### Gereedschapsloods

- Bouwen + render: `blender -b -P gereedschapsloods.py -- [schaal=4] [snel] [deur=graden]`; game-glb:
  `blender -b -P loods_molen_rt.py -- naam=gereedschapsloods vergelijk` (eerst de stap ervoor).
- Maat: begane grond 2,3 x 1,9 m (stijlen), verdieping 3,65 x 2,47 m, muurplaat 3,45 m, nok 4,1 m;
  het aambeeld is 8,9 m lang (hoorn tot x = -3,6 m buiten de gevel, hiel 1,8 m uit de andere).
  Teruggerekend uit `toolshed.png` (162x129).
- Driehoeken: LOD0 ~79k, LOD1 ~0,4k. Atlassen per groep (steen, dak, hout 2048; ijzer, pleister,
  rest 1024).
- Ankers: `deur` (scharnier, open naar buiten met `rotation.z = dicht - hoek` om lokaal Z in Blender,
  lokaal Y in Godot; max. **100°**), `deur_drempel` (looppunt voor de deur), `werkplek` (onder de
  hoorn, hier hamert de bouwer). Geen schoorsteen, dus geen `rook_bron`.
- Rondes (Sonnet-jury, realisme / gelijkenis): 1: 6/6, 2: 6/6, 3: 6/6, 4: 6,5/6. Gestopt na 4.
- Nog mis: de pannen lezen nog te schoon en egaal; het aambeeld is glad (geen deuken of krassen in de
  vorm) en de hiel verdwijnt half onder het dak; de begane grond is donkerder breuksteen dan het
  concept. LOD1 is erg grof (proxies).

### Molen

- Bouwen + render: `blender -b -P molen.py -- [schaal=4] [snel] [deur=graden] [wieken=graden]`;
  game-glb: `blender -b -P loods_molen_rt.py -- naam=molen vergelijk`. De sprite voor de vergelijking is
  `mill.png` met `millsails.png` op (368, -8) erop gelegd (4x).
- Maat: huis 4,0 x 3,1 m met een vleugel van 1,7 x 4,4 m naar voren (samen 5,7 x 4,4 m), dakrand
  1,7 m, nok 3,4 m, stenen voet 2,7 m in het vierkant, kap tot 5,5 m, wiekpunten tot 7,9 m.
  Teruggerekend uit `mill.png` (202x180).
- Driehoeken: LOD0 ~75k, LOD1 ~0,5k (de exacte getallen print `loods_molen_rt.py`).
- Ankers: `wieken` (as = **lokale Z in Blender = lokale Y in Godot**; draai met
  `rotate_object_local(Vector3.UP, hoek)`, de wieken hangen er als eigen meshes onder), `deur` (de
  molendeur in de vleugel, zoals `MillDoor`; zelfde conventie als de loods, max. **100°**),
  `deur_drempel`, `deur_gevel` + `deur_gevel_drempel` (de rondboogdeur in de gevel, ook draaibaar),
  `rook_bron` (schoorsteenmond), `maalplek` (bij de meelzakken voor de vleugel).
- De as steekt 1,05 m uit de kap, zodat de draaiende wieken (3,0 m) vrij blijven van het riet.
- Rondes (realisme / gelijkenis): 1: 6/6, 2: 6/6, 3: 6/5, 4: 6/5. Gestopt na 4.
- Nog mis: de kap leest als een strakke houten ton, niet als het zware, scheve blok van sprite en
  concept; de stenen voet verdwijnt grotendeels in het riet en oogt rommelig; het riet heeft in het
  dal naast de toren een knik. In de glb mist het riet de rafelige zoom (geen alfakaarten zoals de hut).

| gebouw | LOD0 | LOD1 |
| --- | --- | --- |
| gereedschapsloods | ~79k | ~0,4k |
| molen | ~75k | ~0,5k |
