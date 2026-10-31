# Mist van oorlog (fog of war)

2026-10-30. Code: `spel/sim/mist.gd`, `spel/view/mist_view.gd`, `spel/shaders/mist.gdshader`, test `spel/test/mist_test.gd`.
Minikaart: `spel/view/minikaart.gd`, `spel/shaders/minikaart.gdshader`, test `spel/test/minikaart_test.gd`.
Getallen: `spel/data/spel.json` `mist`. Achtergrond (void, `leeg`): `map2.md`.

## Wat het origineel deed

| punt | bevinding | bron |
| --- | --- | --- |
| Standen | **Twee**: onverkend = effen zwart, verkend = volle kleur. Geen grijze "niet meer in zicht"-laag: verkend blijft verkend. | Alle 9 opnamen van M1 (`mission1.png`, `1_*.png`): nergens gedimd terrein naast de mist. De donkere grasvlakken in `1_left`/`1_rightbottom` zijn grasvarianten (tex 3-5, eigen textuur en rasterrand), geen mist. |
| Eenheden in verkend gebied | Zichtbaar, ook zonder dorpeling ernaast. | `1_right.png`: koe en beker in beeld, geen levende dorpeling in de buurt. |
| Rand | Zwart in **bolle bogen** van ca. 1-2 tegels die het land in steken, met een **smalle gerasterde zoom** (enkele pixels, om-en-om). Geen brede verloop. | Uitsnede `mission1.png` rechtsboven (rotsen NO) en de bovenrand van `1.png`. Past bij tegelframes 37 (effen zwart) en 36 (gerasterd). |
| Start | Klein verkend gebied rond vlag en kampvuur, de rest zwart. Bovenrand in `1.png` ligt ca. 8 tegels van de vlag (gemeten: 231 px native recht omhoog = 5,8 diagonale stappen van 40 px). | `1.png`, minikaart: een klein ovaal rond "HOONTON". |
| Minikaart | Linksboven onder de kasteller, stenen kader ca. 158x101 px (native 640x480). Isometrisch, zwart buiten verkend, terreinkleuren, gebouwen als gele vlekken, plaatsnaam van de eigen vlag in het midden. **Venster op vaste schaal dat met de camera meeschuift** (camera in het midden), niet de hele kaart. Geen camerakader te zien. | `1_lefttop.png`, `1.png`, `11954560-…png` (M2). |
| Zichtstraal (2026-10-31) | **Dorpeling 7 tegels, gebouwen 12, toren 22**, euclidisch. Bij elke nieuwe tegel (`0x449c04`) roept het spel `0x447a80` aan met object `+0x12c`; binnen de straal (afstandstabel `0x5fb2f0` = sqrt(dx²+dy²) x 65536) gaat tegelbit `0x4000` (mist) eraf en `0x800` erop, de vier buren van elke onthulde tegel verliezen alleen `0x4000` (de gerasterde rand ligt dus **buiten** de cirkel). `+0x12c` = max(typetabel `+0xfe`, 7) (`0x43803b`, `0x435594`, `0x436900`): elke eenheid minstens 7; vijand (speler 4) +12. Gebouwen: waarde uit de .MIS, meest 12 (klasse `+0x12a` 10, plus 2 bij oude bestanden `0x416358`), toren (75) 22. Gebouwen met afdruk onthullen om elke afdrukcel. | `BEASTS.EXE`; .MIS-objecten M1-M30 (`lokaal/missies/mis.py`, byte `0x12c`). Klopt met de opnamen van de gebruiker (`lokaal/concept/img/r5/mist_origineel_lopen.png`: rand ca. 7,5 tegels van een lopende dorpeling). |
| Startgebied in de .MIS | M1: kern = straal 4 om elk van de zes startdorpelingen (typetabel `+0xfd` = object `+0x12a`), opgeslagen in de tegelvlaggen (`m2`). `0x4216e0` (zet alles op mist en onthult met `+0x12a`) hangt aan een toets (`0x4050b2`), niet aan de start. | M1.MIS `m2`, ASCII-uitsnede 2026-10-31. |
| beasts-src | Heeft geen mist (alleen `MARAUDER_SIGHT`, `HOARD_SIGHT`). | grep fog/reveal/sight op `beasts-src`. |

## Wat de remake doet

- **Sim** (`Mist`, in `Wereld.mist`): `verkend` per tegel (0/1) en `versie`. Start: cirkel `start_straal` 8 om eigen vlag
  en kampvuur, plus het zicht van de startdorpelingen. Elke tik: een dorpeling op een nieuwe tegel verkent binnen
  `dorpeling` 7; een afgebouwd gebouw eenmalig binnen `gebouw` 12 plus halve afdruk (origineel, zie boven; tot 2026-10-31 4 en 4). `leeg` nooit.
- **View**: één schermvullende quad na alles (render_priority 127) leest de dieptebuffer, rekent de wereldpositie uit en
  kijkt in het raster (R8-textuur, 1 texel per tegel). Onverkend = zwart over terrein, water, bomen en eenheden tegelijk;
  lucht en buiten het raster ook. Rand: smoothstep-interpolatie, drempel 0,27 plus ruis (golf 0,24), daarboven
  een zoom van 0,11 met om-en-om-pixels (frame 36); max 0,50, dus zwart en zoom liggen buiten de verkende tegels zoals
  in het origineel (tot 2026-10-31 0,62 / 0,5 / 0,10: at bijna een tegel van het zicht). Frame `--scenario=mist_zicht`. Wolven in onverkend gebied worden ook verborgen (schaduw, hp-balk).
- **Startgebied** (besluit gebruiker 2026-10-30): de cirkel `start_straal` ligt niet alleen om vlag en kampvuur maar om
  het hele gebouwde gebied: ook om elk voorgebouwd eigen gebouw (`Wereld.voorgebouwd`: M2 boerderij, M3 hut) en eigen
  objecten uit `mist.start_objecten` (M3 put en gilde). `Mist.startgebouwen()`.
- **Camera** (besluit gebruiker 2026-10-30): met mist aan mag het brandpunt over het hele 192x192-raster plus 12 m
  (`main.gd` `RAND_M`), zoals het origineel ver het zwart in liet scrollen; daar is alleen zwart (frame
  `--scenario=mist_rand`). Mist uit: de oude grens, eiland + 6 m.
- **Minikaart** (`Minikaart`, in de HUD linksboven; de HUD-tekst staat eronder): 300x186 px, 2,6 px per tegel langs
  x-y (2:1-ruit, tegel (0,0) boven), schuift met het camerabrandpunt mee zoals het origineel. Terrein (RGB8, 1 texel per
  tegel, `tegels.json` `kleur`) maal mist (R8) in de shader; terrein opnieuw alleen als `raster.soort` verandert
  (eens per seconde vergeleken), mist alleen bij een nieuwe `mist.versie`. Stippen elk frame: dorpelingen paars, eigen
  koeien wit, wilde beige, gebouwen geel (afdruk als ruit, in aanbouw donkerder), wolven rood en alleen op verkende
  tegels; wit kader = de schermhoeken op de grond. Klik/tik = brandpunt springt erheen (`rts_camera.spring_naar`),
  slepen = de camera schuift mee terwijl het venster stilstaat; touch via emulate_mouse_from_touch, als het bouwmenu.
  Frame `--scenario=minikaart` (klik na 8 s op de voorste dorpeling): `spel/screenshots/minikaart.jpg`.
- **Aan/uit**: standaard aan; met een `--scenario` standaard uit (oude frames blijven gelijk), behalve `mist_*`.
  `--mist=aan|uit` overschrijft. Frames: `--scenario=mist_start` en `mist_verkend` (`spel/screenshots/mist_*.jpg`).

## Eigen keuzes (niet vastgesteld)

| keuze | waarom |
| --- | --- |
| Startcirkel 8 om vlag, kampvuur en voorgebouwde gebouwen | Straal gemeten in `1.png`, één opname; de gebouwen erbij is een besluit van de gebruiker (2026-10-30). |
| Minikaart-schaal 2,6 px per tegel, venster 300x186 | Het origineel bij 900 px hoog: ovaal M1 ca. 32 px native breed voor een cirkel van 8, kader 158x101 x1,875. |
| Camerakader en stippen op de minikaart | Gevraagd door de gebruiker; in de drie opnamen van het origineel is geen kader te zien. |
| Minikaart draait niet mee met de camera | Het origineel had een vaste kijkrichting; hier draait het kader mee. |
| `leeg` blijft hoogte -2 (`tegels.json`) | Leeg is altijd zwart; alleen de halve tegel water/oever op de grens van verkend land en leeg (noordoever meer M2) kan nog wegzakken. Pas aanpakken als het opvalt (`map2.md` punt 1/5). |
| Plaatsnaam op de minikaart | Nog niet: waar de namen ("HOONTON", "GOATTON") vandaan komen is niet nagegaan. |
