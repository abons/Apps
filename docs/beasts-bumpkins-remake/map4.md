# Missie 4: Beker van Vervulling (kaart)

2026-10-31. `data/origineel/map4.json` uit `M4.MIS` met `python lokaal/map2/maak_map.py 4 spel/data/origineel/map4.json`
(lokaal, nooit in git). Laden: `--missie=4`; test `test/missie4_test.gd`; frames `--scenario=missie4 --stap=...`.

| punt | waarde |
| --- | --- |
| Raster | 192 x 192; niet-void x 15..178, y 1..138 = **164 x 138** |
| Tegels | gras 3.926, bos 2.950 (200-217 gemengd 2.685, dennen 225/226 265), water 1.497, rotsrand 868, rots 829, aarde 623, overig 488, zand 39 |
| Rand | 611 randtegels: bos 59 %, rots 35 %, water 6 % (map2.md tabel 3); geen bereikbare tegel raakt leeg (test) |
| Dorp | vlag (117,100) **Parpton**, kampvuur (115,103), bron (114,105); hut (115,98), bouwersgilde (112,102, op het eind van het pad: deur op die padtegel) |
| Dorpelingen | 2 m (Edward, Perky), 2 v (Mary, Victoria); kas 8.000 |
| Koeien | 1 wilde koe (109,79), generator (107,77) p5=5 p6=4 |
| Wezens | 7, eigenaar 4: 3 wolven (79,39), (45,14), (45,51); 4 **zombies** (type 18): (47,12) bij de ommuurde plek, (75,82), (74,81), (71,89) bij de valbeker |
| Puzzel | sleutel (54,26), magische poort (72,74), zilveren beker (68,85) op olie tussen 11 mijnen, ommuurde plek x 38..44, y 7..14 (27 muurstukken) met triggerplek (41,11) |
| Overig | 144 bomen, 23 paddenstoelen |

## Regels uit M4.MIS (scriptgebied, ontcijferd 2026-10-31)

Acties staan na de condities als `<ptr> <ptr> 0a 00 <type> 00 0a 00 00 <arg>`. Nieuw ontcijferd: **actie 0x04 = maak object**
(arg = klasse, x, y; over alle missies 91 keer, bv. M7 `07 7d 46` = vuur op (125,70)), **0x13 = object activeren/openen**
(arg = slotindex; poort), **0x18 = conditie-id als voldaan zetten** (arg = id). 0x17 object weg, 0x16 kas, 0x14 1/2 winst/verlies
waren al bekend.

| regel | conditie | acties | remake (`spel.json` missies.4) |
| --- | --- | --- | --- |
| sleutel nodig | dorpeling raakt poort 9 en conditie 5 (sleutel geraakt) nog niet | tekst mis4-1 | hint 4-1 `aanraken` + `tenzij_voorwerp` |
| sleutel | dorpeling raakt sleutel 451 | 0x18 5, tekst mis4-2 | hint 4-2 |
| poort | sleutel 451 bij poort 9 (type 10) | 0x17 sleutel weg, **0x04 maak gouden kelk (172) op (40,10)**, 0x13 poort 9 | `voorwerpen.198` naar de poort, regel `poort_open` |
| valbeker | dorpeling raakt zilveren beker 48 | tekst mis4-9, **0x04 maak vuur (7) op (68,85)** | regel `valbeker`, hint 4-9 |
| muur | object 179 (zombie op 47,12) vernietigd | 0x17 muren 79, 95, 74 = (44,10), (44,11), (44,9) | regel `muur_open` |
| winst | dorpeling raakt object 21 (klasse 87 op 41,11) | 0x14 1 | `doel.aanraken` |
| verlies | eigen dorpelingen < 2 | 0x14 2 | `verlies.dorpelingen_onder` |

Achter de poort ligt een gesloten kom (160 tegels) met de valbeker, de mijnen en drie zombies: de sleutel opent dus
de val. De echte beker verschijnt pas als de poort opengaat, in de ommuurde plek die alleen opengaat als de zombie
ernaast dood is. **De winst vraagt alleen de triggerplek**: wie de zombie op (47,12) doodt zonder de poort te openen,
wint ook (de gouden kelk ligt er dan niet). Zo staat het in het bestand; de remake doet hetzelfde.

## Het wezen (groep 21, type 18)

**Zombie, bewezen in BEASTS.EXE**: klasse 104 kiest in toestand 0 per type een sprite (`0x43c23d`, tabel `0x43edcc`);
type 18 springt naar `0x43c29f` en laadt `zombie.mfb` (`[0x5f6f30]`, geladen op `0x4090ec`). hover_names.json (BBTools)
zegt ook 18 = zombie. De "groep" (0xF3) is het wapen uit de typetabel (+0xfc, gezet op `0x43801d`), geen soort: 21 bij
de zombie, 13 bij wolven. De **boom met ogen** (`bushman.mfb`, `busheyes.mfb`, `bushk_*.mfb`) is een aparte objectklasse
92 (teken-case `0x43e8d4`) en staat in **geen enkele** van de 30 .MIS-bestanden.
Typetabel (`0x5e5e00 + 292 x 18`): hp 240, wapen 21 = 15 + 0..14 schade elke 80 tikken (7,5 s), +0x100 = 60 (wolf 200,
man 128; betekenis onbekend). Of hij in M4 loopt of aanvalt is niet uit de code gehaald.
**Besluit gebruiker 2026-10-31:** hij herinnert zich een boom met ogen die verder niets deed. Remake: `wezens.zombie.passief`
= true: staat stil, kijkt naar de dichtste dorpeling binnen 6 tegels, valt niet aan, geen vluchtreden, wel te doden met
stenen (nodig voor `muur_open`). Model: `wezen_model.zombie` (`assets/zombie.glb` als die er is, anders een den met ogen,
`view/missie_props.gd`; `-- --zombie_model=boom|wolf|glb`). Met passief false het actieve gedrag (eigen keuze, getest).

## Vallen (eigen keuze waar niet gevonden)

- **Mijn** (37): aanraken = klank + toestand 24 (ontploffen), `0x448ff6`. Schade 60 binnen 1,5 tegel, alleen dorpelingen.
- **Vuur** (7): een bouwer die het raakt dooft het (`0x448f78`). Brandt 25 s, 10 schade/s binnen 1,2 tegel; met olie (61)
  eronder gaan na 2 s de mijnen binnen 2,5 tegel af. Waarden in `spel.json` `vallen`.
- **Tinnen beker**: geen regel naar de vlag in M4.MIS; remake: naar de vlag = weg zonder kas (anders kan de drager nooit
  meer iets oprapen). Model `natuur:tinnen_beker` via `missies.4.modellen`.

## Remake

`sim/regels.gd` (regels per missie uit `spel.json`, mijnen, vuur), `view/missie_view.gd` (poort met wegzakkende
`poort_deur`, muren, mijnen, olie, vuur, knal), `view/missie_props.gd` (placeholders), `view/wolf_model.gd` (wezen-model),
`data/objecten.json` (69, 198, 199, 87, 29, 37, 61, 7; 104 soort 18 = zombie). Bouwmenu: niets nieuws in M4 (geen hint
noemt een gebouw); put en voetvolkgilde vanaf M3, molen en akker meteen (voorgebouwde loods).
Frames: `spel/screenshots/missie4_{overzicht,poort,beker,wezens,muur}.jpg`, ruw in `spel/out/missie4/` (niet in git).

## Open vragen

| vraag | stand |
| --- | --- |
| Loopt en vecht de zombie in het origineel? | Sprite, hp en wapen zeggen zombie; de gebruiker herinnert zich een stilstaande boom met ogen. Remake passief; omzetten = `passief: false`. |
| Schade van mijn en vuur, duur van het vuur | niet gevonden; eigen keuze |
| Wat doet de tinnen beker bij de vlag? | geen regel; eigen keuze: weg, geen kas |
| Generator p5=5, p6=4 | betekenis onzeker; remake start 1, max 4 |
| Snelheid zombie (+0x100 = 60?) | niet bewezen; alleen relevant als hij actief wordt |
