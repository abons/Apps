# Missie 2: wat ligt buiten de kaart (void)

Onderzoek 2026-10-30. Alleen tekst en getallen; beelden en afgeleide data staan lokaal (`lokaal/`, nooit in git).
Bronnen: `lokaal/missies/mis/M*.MIS` (via `lokaal/map2/maak_map.py`), `lokaal/map2/map2.json`, `lokaal/map1/`
(screenshots, `maptile_sheet.png`). Het netwerkpad `\\axel-laptop\Users\axelb\beasts` was niet bereikbaar (laptop
offline); alles hieronder komt uit wat lokaal staat.

## 1. Wat toont het origineel buiten de kaart

**Zwart, en geen zee.** In de data is "void" geen aparte tegel maar het standaardgras van de editor.

| bewijs | wat het zegt |
| --- | --- |
| Tegeldata | Void-tegels hebben tex 0-5 (gewoon gras): over alle 30 missies 0/1/2 elk ca. 230.000 keer, 3/4/5 elk ca. 26.000 keer. Dat is de willekeurige grasvulling van de editor. In de 12 bytes per tegel zit **geen vlag** die void van binnengras onderscheidt (bytes 1-11 zijn in void overal 0, op byte 9 = 64 na, en dat staat ook op 86 % van het binnenland). |
| Tegelsheet | Frames 36 (zwart gerasterd) en 37 (effen zwart) zijn de enige zwarte tegels. Ze komen in **geen enkele** kaart voor, dus het spel tekent ze tijdens het spelen: vermoedelijk de mist (onverkend gebied) en de gerasterde overgang daarvan. |
| Screenshots missie 1 (`mission1.png`, `1_*.png`) | De startview is grotendeels zwart met golvende, ronde randen rond het verkende stuk. Hetzelfde zwart met dezelfde randen ligt later achter de zee en achter de rotsen NO. Het is dus de **mist** (onverkend = zwart), geen getekende zee. De zee ligt alleen waar de kaart watertegels heeft. |
| Minikaart | Zwart buiten het verkende gebied, ook als het eiland helemaal verkend is (`1_lefttop.png`). De minikaart is isometrisch (ruitvormig). |
| Webscreenshot missie 2 (`11954560-…png`, minikaart "GOATTON" = de eigen vlag van M2) | Het meer ligt bovenaan, daarboven alleen zwart. Grijze rots links en onder, gras en bos naar rechts, en er is nergens zee. |

Conclusie: buiten het ontworpen gebied ligt in de data "meer land" (gras) dat de speler nooit ziet, omdat het
onverkend blijft. In het origineel is het daar zwart. De rand van het ontworpen gebied is bijna overal een muur van
rots, bos of water (zie 2 en 3), zodat niemand er komt. Of een eenheid echt over de rand kan lopen (bijv. bij de
noordoever van het meer) is niet te zien zonder het origineel te draaien: zie open vragen.

## 2. Missie 2: grootte en rand

| punt | waarde |
| --- | --- |
| Raster | 192 x 192; niet-void x 65..147, y 35..119 = **83 x 85** tegels |
| Niet-void | **4.668** tegels: land 4.014 en water 654 (14 %) |
| Bereikbaar vanaf de vlag (92,73) | 3.056 tegels over gras, aarde, zand, overig en bosgrond (zonder bosgrond 1.917) |
| Rand (niet-void naast void, 4-buren) | 245 tegels. Kijkend 2 tegels naar binnen: water 22 % (het meer), rots 34 %, bos 44 %, open 0 % |
| Per kant | N: rots en rotsrand. NO, O en ZO: een brede dennenbosband (bosgrond, 1.090 tegels). Z en ZW: een rotsmassa. W en NW: het meer |
| Kaartrand van 192 | wordt nergens geraakt; void ligt rondom |
| Loopbaar land direct naast void | 126 tegels: de buitenrand van de bosband (O) en een smalle oeverstrook aan de noordkant van het meer (x 75..85, y 38..48) |

**Het meer** (654 tegels, x 66..99, y 41..79) is een echt meer, maar het ligt **aan de rand van het ontworpen
gebied**. Aan de oost- en zuidkant ligt het startland, aan de N-, W- en NW-kant meestal maar **1 tegel** oever
(zand/gras-overgang, tex 63-75 en water/zand 11-22) en daarachter direct void. Op een paar plekken grenst water
of oevergras zonder strand aan void. In het origineel is die buitenoever een dunne strook strand met daarachter
zwart. Het is dus geen open water dat in een zee overgaat.

Overzichtsplaat (lokaal, auteursrechtelijk afgeleid, niet committen): `lokaal/map2/map2_overzicht.png`. Daarop:
void paars-zwart, water blauw, gras, aarde, zand, overgang, bosgrond, rots en rotsrand elk een eigen kleur, oranje
omlijnd = loopbaar naast void, geel = vlag. Scripts ernaast: `lokaal/map2/plaat.py` (plaat), `rand.py` en `rand2.py 2` (randtabel hieronder).

## 3. De rand van alle 30 missies

Methode: void = gras (tex 0-5) dat vanaf de rasterrand aaneengesloten is (zoals `maak_map.py` en `export.py`).
Rand = niet-void tegels naast void of op de rasterrand. Per randtegel kijk ik 2 tegels om me heen: is er water,
dan telt hij als water; anders rots (rots/rotsrand); anders bos (bosgrond); anders open. "Kaartrand" telt de
niet-void tegels op rij of kolom 0/191: daar loopt het land tot het einde van het raster. Labels: **zee rondom** bij
60 % water of meer, **deels zee** bij 40-60 %, anders **land aan void** met de soort muur die het meest voorkomt.

| nr | rand | water % | rots % | bos % | open % | kaartrand | label |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | 245 | 75 | 23 | 0 | 2 | - | zee rondom |
| 2 | 245 | 22 | 34 | 44 | 0 | - | land aan void (bos) |
| 3 | 382 | 14 | 84 | 3 | 0 | 7 | land aan void (rots) |
| 4 | 611 | 6 | 35 | 59 | 0 | - | land aan void (bos) |
| 5 | 298 | 0 | 100 | 0 | 0 | - | land aan void (rots) |
| 6 | 471 | 30 | 70 | 0 | 0 | - | land aan void (rots) |
| 7 | 553 | 23 | 27 | 45 | 5 | - | land aan void (bos) |
| 8 | 483 | 52 | 31 | 14 | 2 | - | deels zee |
| 9 | 542 | 41 | 17 | 41 | 1 | 91 | deels zee |
| 10 | 397 | 0 | 0 | 100 | 0 | - | land aan void (bos) |
| 11 | 403 | 66 | 34 | 0 | 0 | 5 | zee rondom |
| 12 | 483 | 5 | 7 | 87 | 0 | - | land aan void (bos) |
| 13 | 519 | 71 | 13 | 16 | 0 | 30 | zee rondom |
| 14 | 845 | 67 | 28 | 2 | 2 | 21 | zee rondom |
| 15 | 581 | 19 | 81 | 0 | 0 | 89 | land aan void (rots) |
| 16 | 556 | 61 | 31 | 5 | 3 | 10 | zee rondom |
| 17 | 325 | 0 | 100 | 0 | 0 | 9 | land aan void (rots) |
| 18 | 409 | 0 | 0 | 100 | 0 | - | land aan void (bos) |
| 19 | 488 | 2 | 61 | 34 | 4 | - | land aan void (rots) |
| 20 | 594 | 23 | 14 | 45 | 18 | 3 | land aan void (bos) |
| 21 | 546 | 46 | 26 | 23 | 5 | 5 | deels zee |
| 22 | 540 | 21 | 76 | 3 | 0 | - | land aan void (rots) |
| 23 | 793 | 53 | 35 | 9 | 3 | 11 | deels zee |
| 24 | 413 | 19 | 14 | 66 | 1 | - | land aan void (bos) |
| 25 | 280 | 22 | 0 | 78 | 0 | - | land aan void (bos) |
| 26 | 598 | 4 | 94 | 2 | 0 | 23 | land aan void (rots) |
| 27 | 591 | 43 | 49 | 7 | 0 | - | deels zee |
| 28 | 280 | 22 | 0 | 78 | 0 | - | land aan void (bos) |
| 29 | 545 | 0 | 56 | 44 | 0 | - | land aan void (rots) |
| 30 | 716 | 16 | 83 | 0 | 2 | 52 | land aan void (rots) |

Totaal: **5 zee rondom** (1, 11, 13, 14, 16), **5 deels zee** (8, 9, 21, 23, 27), **20 land aan void** (10 rots, 10
bos). Het land loopt tot de rasterrand in 13 missies, maar alleen in 9, 15 en 30 over een flink stuk (50-90
tegels). Open rand (gras dat zonder muur aan void grenst) komt bijna niet voor: 0-5 %, met als uitschieter 18 %
in missie 20. De ontwerpers hebben dus bijna altijd een muur van rots, bos of water op de rand gezet. Zelfs bij
"zee rondom" is de zee een ring van watertegels: missie 1 heeft buiten de zee-ring nog een tweede kustrand (NO en
ZO, de 25 % rots), en daarachter is void. **Void is in geen enkele missie zee.**

Kanttekening bij de methode: als het speelbare gras van een missie aan de rasterrand raakt, eet de vulling dat gras
mee op als void. Bij de 13 missies met "kaartrand" is het speelbare gebied daar dus misschien iets groter dan
`kinds` zegt.

## Waarom de remake het verkeerd toont

| plek | wat er gebeurt |
| --- | --- |
| `spel/data/tegels.json` | `void` wordt `leeg`, met `hoogte` -2,0: precies zo diep als `water`. |
| `terrein_view.gd` `_splat` | `leeg` krijgt alle gewichten 0. Dat geeft de laag `water_rand`, dezelfde oevertextuur als water. |
| `terrein_view.gd` `_bouw_water` | Een waterplaat van 1.800 x 1.800 m op hoogte 0 over alles, met een "Zeebodem" op -2,02. Alles onder 0 wordt dus water, void ook, en ook alles buiten het getoonde venster (`eiland.grow(MARGE)`, `MARGE` 14 met als commentaar "tegels water/land rondom het eiland"). |
| `_tegel_h` / `hoogte_op` | Buiten het raster geldt de hoogte van `leeg`, en buiten het venster -2: weer water. |

Bij missie 1 valt dat weg, omdat daar echt water rond het eiland ligt. Bij missie 2 zakt de buitenoever van het meer
(1 tegel breed) door de hoekgemiddelde hoogte en splat weg naar -2. Het meer loopt dan over in een "zee" die er in
het origineel niet is. Hetzelfde gebeurt bij elke missie waar land of water direct aan void grenst.

## 4. Voorstel (plan, geen code)

**Besluit 2026-10-30 (gebruiker):** niet apart bouwen. Met mist van oorlog (fog of war) zie je het zwarte gebied niet meer, dus void wordt "nooit verkend" in de mist-laag (punt 7). Wel blijft: void niet als zee tekenen. Onderstaande stappen dienen als naslag voor die mist-laag.

Uitgangspunt: **void is land dat je niet ziet**, zoals in het origineel. Water komt alleen van watertegels. Daarmee
klopt missie 1 nog steeds (de zee-ring zijn echte watertegels) en wordt het meer van missie 2 weer een meer.

1. **`tegels.json`, `leeg`:** `hoogte` van -2,0 naar grondniveau (ca. 0,2, net onder gras 0,25 en boven het water
   op 0). Houd `loopbaar: false` en `gras: 0`, en maak de `kleur` bijna zwart (bijv. `#0c0f0a`). Optioneel een veld
   als `"zicht": "donker"`, zodat de view het herkent zonder op de naam te testen.
2. **`terrein_view.gd` `_splat`:** geef `leeg` niet langer "alles 0" (= water_rand). Geef het gras- of
   aarde-gewicht plus een **eigen void-gewicht**. Dat gewicht moet in een vrij kanaal (de 6 bestaande zitten in
   COLOR en UV; bijv. `UV2.x` of `CUSTOM0`).
3. **`terrein.gdshader`:** meng het albedo met dat void-gewicht naar zwart. Omdat het gewicht per hoek wordt
   gemiddeld en dan bilineair verloopt, ontstaat vanzelf een zachte afloop over 1-2 tegels. Wil je dat breder
   (2-4 tegels, zoals de golvende mistrand van het origineel), reken dan per hoek de afstand tot de dichtstbijzijnde
   niet-void tegel uit (een BFS in `_bereken_hoeken`) en gebruik `smoothstep` op die afstand, met wat ruis voor de
   golvende rand. Het resultaat: **zwart onder een mistrand**, geen rotsen en geen zee.
4. **`_bouw_water`:** laat de waterplaat staan (die is nodig voor meren en zee-ringen). Vervang de "Zeebodem"
   (-2,02) door een **zwart grondvlak op ca. +0,15**, zodat er buiten het venster ook geen water meer te zien is.
   Pas `hoogte_op` buiten het venster en `_tegel_h` buiten het raster aan, zodat ze de nieuwe `leeg`-hoogte geven
   in plaats van -2.
5. **Oevers langs void:** waar water direct aan void grenst (een paar plekken bij het meer van M2), loopt de
   hoogte van -2 naar +0,2 over een halve tegel. Dat geeft een steile, donkere wand die in de mist verdwijnt. Dat is
   prima; er hoeft geen extra strand te komen.
6. **Camera (los, optioneel):** begrens `rts_camera.gd` op `eiland` plus een paar tegels, zodat de speler niet ver
   het zwart in kan scrollen. In het origineel bepaalde de mist hetzelfde.
7. **Later, met mist van oorlog:** void is dan gewoon "nooit verkend". Dezelfde zwarte laag kan de mist worden.
8. **Variant (alleen als de gebruiker het wil):** een vlag per missie in `spel.json`, bijv. `"buiten": "zee"`, die
   void in water verandert. Zinnig hooguit voor de 5 "zee rondom"-missies (1, 11, 13, 14, 16), omdat de zee daar
   anders als een smalle ring tegen zwart staat. Dat is mooier, maar het origineel toont het niet zo.

Wat ik **niet** zou doen: een kunstmatige rand van rotsen of bos rond void leggen. De kaarten hebben die muur al
in 78 % van de gevallen (rots + bos + water op de rand, zie tabel 3), en een extra rand zou de maat van de kaart
veranderen.

Te raken bestanden: `spel/data/tegels.json` (`leeg`), `spel/view/terrein_view.gd` (`_splat`, `_bouw_terrein`
voor het extra kanaal, `_bereken_hoeken` voor de afstand, `_bouw_water`, `_tegel_h`, `hoogte_op`),
`spel/shaders/terrein.gdshader` (void naar zwart), en optioneel `spel/rts_camera.gd`. De sim (`raster.gd`) blijft
gelijk: `leeg` is al niet loopbaar.

## Open vragen

| vraag | hoe te beantwoorden |
| --- | --- |
| ~~Kan een eenheid in het origineel over de rand lopen?~~ | **Nee** (gebruiker, 2026-10-30): het buitengebied is onbereikbaar door dicht bos, water of bergen. Remake: `wereld.gd` `RAND_DICHT` = 3, bosgrond binnen 3 tegels van leeg krijgt altijd een boom en open land direct aan leeg wordt geblokkeerd; `missie2_test` controleert dat geen bereikbare tegel aan leeg grenst. |
| Zijn frames 36/37 echt de mist? | Een savegame van het origineel bekijken of de renderer lezen; nu afgeleid uit de screenshots. |
| Ligt er ergens in de missiestaart een kaartgrens? | Niet gevonden in kop (74 bytes) of tegelvelden; de staart is niet helemaal gedecodeerd. |
