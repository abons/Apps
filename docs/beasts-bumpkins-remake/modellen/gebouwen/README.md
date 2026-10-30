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
- Driehoeken: LOD0 50.650, LOD1 7.597. Atlassen: `opaak`, `riet`.
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

Glb's: atlassen 1024 (`rt res=1024`, budget 2026-10-29); `res=2048` voor de volle maat.
Vergelijkingen per ronde: `preview/<naam>_vergelijk_ronde<n>.png`; glb's: `preview/<naam>_rt_vergelijk.png`
(beauty | LOD0 | LOD1, Cycles).

- ⚠️ Gebakken riet (melkerij en kippenhok) mist de halmen grotendeels: veel stralen raken de onderlaag
  (die ook bron is) i.p.v. de halmen, het dak wordt bruin-egaal met gele vlekken. Te doen: de rietschil
  als bron weglaten of de cage groter, opnieuw bakken. De bronnen worden voor het bakken samengevoegd
  (selected-to-active met honderden objecten liep uren op de CPU), dus de tint per steen gaat verloren.
- `pack_islands` hangt in Blender 5.2 op duizenden eilandjes; `uv_atlas` gebruikt alleen smart project.

| gebouw | LOD0 | LOD1 |
| --- | --- | --- |
| melkerij_boerderij | 50.650 | 7.597 |
| kippenhok | 15.746 | 6.998 |

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

## Bouwstanden (`standen.py`, `standen_lib.py`, hut: `../peasant_hut_standen.py`)

Standen 1-3 worden UIT de af-glb gesneden (besluit 2026-10-30): de gebakken eilanden van `<naam>_rt.blend` met
hun eigen UV's, dus muren, ramen en deuren lopen in elke stand gelijk door en de atlassen zijn die van de af-glb.
Stand 4 = `<naam>_rt.glb`. Oorsprong, schaal, assen en alle ankers (lege nodes, zelfde namen en plek) zijn gelijk:
in Godot op exact dezelfde transform omwisselen. Geen LOD1. Deurbladen en wieken (meshes onder een scharnier)
zitten in geen stand; de lege `deur`/`wieken`-nodes wel.

- Gedeelde code: `standen_lib.py` (eilanden, kopie, snij, sluit, hol, gaten, balk-sjabloon, touw, aarde,
  export, previewplaat). De hut gebruikt hem met zijn eigen indeling en komt er byte-gelijk uit (md5 van
  stand 1-3 voor en na gelijk, 2026-10-30).
- Gebouwen: `blender -b -P standen.py -- naam=<gebouw> [standen=1,2,3] [preview] [procent=100]` (eerst de
  rt-stap). Geeft `<naam>_stand1..3.glb` en `../render/<naam>_standen.png` (1 | 2 | 3 | af, EEVEE, camera en
  licht van `<naam>.blend`). Hut: `blender -b -P peasant_hut_standen.py -- [preview]`, plaat `../render/hut_standen.png`.
- Hoe: elk eiland krijgt de naam van het bronobject in `<naam>.blend` waarvan de bbox het best past. `CFG` in
  `standen.py` zegt per naam wat stand 2 en 3 doen: `weg`, `heel`, `auto` (kleine eilanden heel/weg op hun
  midden, zodat de muurkop rafelig blijft; grote doorgesneden op de muurhoogte en dichtgemaakt in de kleur van
  hun zijkant), `hol` (dichte kern wordt muurschil met binnenkant, muurkop en deuropeningen), `steen@z`/`snij@z`
  (eigen hoogte). Deuropeningen = bbox van het deurblad, dwars verlengd. Stand 1 = aarde (farm_soil) op de
  veelhoek `voet` met paaltjes (sjabloon: een paal uit de af-glb) en touw. Dakgeraamte in stand 3: doorsnedes
  van de dakmesh, de balken volgen de onderkant van het dak (`spanten`: as, posities, bereik).
- Muurhoogte stand 2: 0,7 m; stand 3: volle muren.

| gebouw | stand 1 | 2 | 3 | af | glb 1 / 2 / 3 / af (MB) |
| --- | --- | --- | --- | --- | --- |
| hut | 5,9k | 29k | 87k | 112k | 6,4 / 10,1 / 12,7 / 25,1 |
| gereedschapsloods | 1,7k | 2,5k | 11,7k | 79k | 13,6 / 18,1 / 21,0 / 30,3 |
| molen | 4,9k | 6,1k | 43k | 75k | 10,9 / 16,4 / 19,0 / 31,7 |
| melkerij_boerderij | 7,1k | 11,3k | 41k | 51k | 4,9 / 2,8 / 3,9 / 6,3 |
| kippenhok | 1,4k | 6,6k | 14,5k | 15,7k | 4,9 / 3,7 / 4,1 / 6,5 |

- ⚠️ De atlassen zitten in elke glb opnieuw (glb sluit alles in): per stand alleen de materialen die erin zitten,
  maar loods en molen dragen 2048-atlassen, dus 11-21 MB per stand. Delen kan alleen met `.gltf` + losse
  beelden (zelfde bestanden als de af-glb) of door in Godot de materialen van de af-glb op naam te hergebruiken.
- Per gebouw:
  - Gereedschapsloods: 2 = stenen voet tot 0,7 m met stijlen, holle kern met deuropening; 3 = begane grond,
    verdieping (vakwerk, pleister, raam), gevelpunten, windveren, spanten + gordingen; geen pannen/beschot/nok,
    geen aambeeld (hoorn, lijf, hiel) en geen bloembak.
  - Molen: 2 = L-vormige muren 0,7 m (planken, stenen, holle kernen) met beide deuropeningen; 3 = volle muren,
    gevel tot 3,06 m, schoorsteen, stenen voet (kern omlaag gerekt tot de muurkop, in de af-molen staat hij op
    het riet), kap zonder dakplanken, de as; geen riet, wieken, klimop, zakken. Spanten volgen het L-dak.
  - Melkerij: 2 = muren 0,7 m (pleister, stijlen), holle binnenkern met vloer en deuropening, varkenshok heel
    (laag); 3 = volle muren, voorgevel, ramen, ronde spanten + gordingen, halve schoorsteen (3,5 m); geen riet,
    dakkapel, bloembakken, varken. Binnenkern dicht (plafond op 2,6 m).
  - Kippenhok: drie standen, ze zijn te onderscheiden: 1 = aarde met paaltjes (28 cm), 2 = stromat, stenen voet,
    hoekstijlen, regels, kozijn en dakgeraamte (geen planken), 3 = planken, gevels, loopplank, legnest, trog,
    hek en spanten; geen riet, eieren, korrels.
- Nog mis: muurkoppen en binnenkant van holle kernen zijn egaal (kleur van de zijkant, leest als beton bij
  molen en loods); binnenmuren van de melkerij zijn donker (gebakken AO); losse stenen/planken rond de bouw
  ontbreken (de hut heeft ze); de schoorsteenstomp van de melkerij staat op het plafond; stand 1-aarde is
  egaal roodbruin; alleen de hut heeft binnenstenen. De hut houdt een oude rijfout in `aarde` (`rij_vast=False`)
  zodat hij byte-gelijk blijft.
