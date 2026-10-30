# Missie 1 van het origineel (Beasts & Bumpkins, 1996)

Gedecodeerd uit `MISSIONS.BOX` (`M1.MIS`) met een Python-port van `BBTools/BBData/MAPFile.cs`. Teksten uit `MISTEXT0.BOX`.
Alle bestanden lokaal in de scratchpad (`SC` = `C:/Users/Axel/AppData/Local/Temp/claude/E--werk-androidApps-Apps/16e99493-ac86-47c7-921f-1d215c266f51/scratchpad/`), niets in git.

## Missie

| punt | waarde |
| --- | --- |
| Naam in bestand | "Mission 1"; kaartnaam in minimap "Hoonton" (screenshots) |
| Verhaal | Lord Mildew is door koning Roland naar het eiland **Aorta** verbannen, met een paar boeren |
| Doel | **6 boeren** en **4 koeien** (herd) |
| Hint | begin met kippenhokken, de mensen hebben honger; meer huizen = meer voortplanting |
| Verliezen | "Mission Failure" staat in de screenshots (voorwaarde niet in de tekst; vermoedelijk alle boeren dood) |
| Startgeld | HUD toont `10000` in alle screenshots (waarschijnlijk cheat/testgeld, onzeker) |
| Tutorial-hints (`MIS1-n.TXT`) | 2 peasant hut, 3 Builders Guild (bouwer werkt 2x sneller, via mannelijke boer), 4 Bakery (tarwe), 5 tarwe planten in lente/oogsten in herfst, 6 Farm + omheinde wei (hek/poort), 7 zwervende koeien claimen (paarse halsband), 8 "Hmmm, valuable" = zilveren beker naar de vlag brengen, 9 huizen gespreid bouwen (levensduur), 10 prijzen via goudicoon, 11 koeien fokken in de lente (dicht bijeen houden), 12 eerst kippenhokken |
| Seizoenen | wisselen (sneeuw- en lente-screenshots); gras en akkers hebben seizoensvarianten |

## Kaart

| punt | waarde |
| --- | --- |
| Raster | **192 x 192** tegels, maar alleen een eiland van ca. 77 x 88 tegels (x 68..144, y 21..108) is echt; de rest is leeg/zwart (tegel 0-2, buiten beeld) |
| Binnenste eiland (begin) | x 82..128, y 38..93, ca. 47 x 56 tegels, **1714 tegels** |
| Zee-ring | 2384 tegels water rond het eiland; daarbuiten een tweede kustrand (rots/zand/gras) NO en ZO |
| Tegelgrootte origineel | isometrisch 78 x 40 px per ruit |
| Tegelgrootte voor ons | **2,0 m** voorstel (hut 3,4 m = ca. 1,7 tegel). Binnen-eiland dan ca. 94 x 112 m, met zee 154 x 176 m |
| Startpunt | rond (102,66): vlag (104,65), kampvuur (102,68), bron (101,70) |

Terrein binnenste eiland (1714 tegels, uit de tegelkleuren): gras 1044 (incl. donkere en lichte vlekken en bloemen), aarde/dirt 195, rots 172, rotsrand 157, overig 84 (akker/stenen-cirkels), "bosgrond" 51, zand 11. Zee-ring: water 2384. Rotsen vormen een boog langs N en W (hoogteverschil in screenshots), zand/bruine strand ZO en O.

Tegel-id naar frame in `maptile` (132 frames, contactsheet `SC/map1/maptile_sheet.png`): 0-5 gras (3-5 met bloemetjes), 6-7 water, 11-26 water/zand-overgangen, 48-93 gras/zand/aarde-overgangen en donker gras, 98-113 rotsrand (`rockrim`), 227-231 rots (`rock0n`), 225/226 `tester` = bruine bosgrond onder dennen (twee vlekken NO van de start en W), 234-250 = id minus 119, 200/201 bos. Wegen: apart veld, 4 tegels bij (101,65) = het pad naar de vlag. Spelerseigendom per tegel: alles 0.

## Geplaatste objecten (60)

Klasse-ids uit `objects_list.txt`/BBTools-README. Posities zijn tegel (x,y). Lijst: `SC/map1/map1.json`.

| id | wat | aantal | posities / opmerking |
| --- | --- | --- | --- |
| 0 | boom (onverwoestbaar, grote den) | 27 | N-kust (104..109, 39..41), O-rand (113..124, 47..63), W-rand (82..89, 60..74), zuid (107,79) |
| 6 | spar | 11 | bij de bomen: (82..86, 62..69), (108..123, 42..57), (108,79), (115,67) |
| 5 | boom | 4 | (97,56), (105,79), (118,68), (114,65) |
| 83 | paddenstoel | 7 | (101,59), (104,58), (93,70), (88,63), (110,83), (118,73), (117,64); eigenaar 4 (wild), `state` 0/3/4/5/6. **Maat** (`mission1.png`, 2026-10-30): 38x42 px tegen een man van 50 px in dezelfde opname = 0,84 man, dus ~1,1 m: het origineel overdrijft al; remake `schaal` 2,3 op de 0,49 m-glb. Een sprite-uiterlijk (bruine bolle hoed, oranje voet), geen variaties te zien, dus `state` niet in kleur/maat. **Gedrag**: niets in de bestanden. Geen hinttekst (MISTEXT0 noemt geen mushroom), geen conditie in M1-M3.MIS op klasse 83 of de slotindexen (4, 34, 142-146); M2 heeft er 10, M3 25. Eten/gif/oprapen is dus spel-code (exe ontbreekt): alleen in het origineel te toetsen. Tot dan decor. |
| 103 | **villager** | 6 | (104,67), (99,65), (99,67), (103,69), (99,64), (102,64); veld `sex` 14,13,1,2,2,1 (1=man, 2=vrouw, 13/14 = waarschijnlijk kind; niet geverifieerd) |
| 98 | vlag (flagpost) | 1 | (104,65), inlever-/spawnpunt |
| 143 | kampvuur | 1 | (102,68) |
| 144 | bron (spring) | 1 | (101,70) |
| 159 | zilveren beker | 1 | (110,53), tutorial: naar de vlag brengen = +5.000 kas, beker weg (M1.MIS, zie `missies.md`; remake `sim/voorwerpen.gd`) |
| 171 | generator (README: "cow") | 1 | (118,58), `gen`=1; niet duidelijk of dit de koeienspawner is. Screenshots tonen meerdere koeien |

Geen gebouwen, geen kippen, geen vijanden en geen triggers in het bestand. Er staat 22 kB ongeparste staart (`ptr_to_smth2_arr`) achter de objecten; mogelijk missiescript, niet gedecodeerd.

## Boeren aan het begin

6 villagers bij de vlag, rond (99..104, 64..69), alle eigenaar 0 (speler). Een loopt al naar (104,65) (de vlag). Zie tabel boven voor `sex`.

## Vijanden

Geen in missie 1 (het eiland is leeg). De zwervende koeien en de paddenstoelen (gif) zijn het enige "wild". Vijanden komen pas vanaf missie 2.

## Hoe dit in Godot 3D te bouwen

| onderdeel | aanpak |
| --- | --- |
| Terrein | Heightmap 192x192 uit `map1.json` (alleen eiland uitsnijden: x 66..146, y 20..110). Hoogte: zee 0, strand 0,3 m, gras 1 m, rots-boog tot 4-6 m (rotsrand = klif). Per tegel splat-map (gras/zand/aarde/rots/water) in een terrain-shader, geen losse tegels |
| Water | Vlak op hoogte 0,5 m, ring van 2384 tegels, eenvoudige water-shader |
| Bomen | MultiMesh-scatter per id: klasse 0/5/6 uit de lijst (42 stuks) plus extra dennen op de `tester`-bosgrond (51 tegels) met dichtheid ca. 1 per 2 tegels; kleine wille variatie |
| Rotsen | Rotsboog uit rots-tegels: een paar rots-meshes (6 vormen als in `rock01..06`) langs de klif plus kliffen in de heightmap |
| Paddenstoelen, beker, vlag, kampvuur, bron | kleine props, eenvoudig |
| Objecten | Alles in `map1.json` > `objects` (x,y,klasse) 1:1 naar scene-nodes; tegel (x,y) x 2 m = positie |
| Seizoen | Later: shader-parameter (gras groen/oker, sneeuw); eerst alleen zomer |
| Nodig naast wat we hebben (hut, man) | vrouw, kinderen, ouderen, builder, koe (+kalf), kip (+kuiken), kippenhok, boerderij (farm), bakkerij, builders guild, windmolen/akker, hek en poort, bron, vlag, kampvuur, zilveren beker, den/spar/boom (3 maten), rotsen, paddenstoel; wolf en zombie pas vanaf missie 2 |

## Open vragen

| vraag | opmerking |
| --- | --- |
| Verlies-voorwaarde | niet in tekst; alleen "Mission Failure" in screenshot |
| Startgeld/-voorraad | HUD `10000` in screenshots, mogelijk testbuild; echte startwaarde staat misschien in de 22 kB staart |
| Koeien | wat is object 171 (README "cow", lijst "generator") en waar staan de 4 doelkoeien; screenshots tonen er meerdere |
| `sex`-waarden 13/14 | kinderen? |
| Bosgrond (tex 225/226) | zijn de dennen in de screenshots tegel-gebonden (maskvelden `m1`/`m2` in de JSON) of objecten? Bomen in de lijst (42) zijn minder dan op de screenshots te zien is |
| Hoogte | origineel is plat isometrisch; de rotsboog is alleen kleur. Hoogtes voor 3D zijn onze keuze |
| Schaal | 2 m per tegel is een voorstel, te testen met hut en boer |

## Lokale bestanden (niet in git)

| pad | inhoud |
| --- | --- |
| `SC/bb_original/maps/M1.MIS`, `MISSIONS.BOX`, `MISTEXT0.BOX`, `box.py`, `mapread.py` | rauw bestand en Python-decoder |
| `SC/map1/map1.json` | terrein (`kinds`, `tex`, `road` per tegel `[y][x]`) en `objects` |
| `SC/map1/layout.png` | top-down laag-uitsnede van het eiland met objecten (T/F/t boom, m paddenstoel, V villager, P vlag, C vuur, K generator, G beker, S bron; roze = bosgrond) |
| `SC/map1/tiles.png`, `maptile_sheet.png` | volledige kaart en tegelcontactsheet |
| `SC/map1/mission1.png`, `1_*.png`, `map1_*.png` | originele screenshots (uit `\\axel-laptop\Users\axelb\beasts\Unity_bumpkins\screenshots\`) |
