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
| beasts-src | Heeft geen mist (alleen `MARAUDER_SIGHT`, `HOARD_SIGHT`). | grep fog/reveal/sight op `beasts-src`. |

## Wat de remake doet

- **Sim** (`Mist`, in `Wereld.mist`): `verkend` per tegel (0/1) en `versie`. Start: cirkel `start_straal` 8 om eigen vlag
  en kampvuur, plus het zicht van de startdorpelingen. Elke tik: een dorpeling op een nieuwe tegel verkent binnen
  `dorpeling` 4; een afgebouwd gebouw eenmalig binnen `gebouw` 4 plus halve afdruk. `leeg` nooit.
- **View**: één schermvullende quad na alles (render_priority 127) leest de dieptebuffer, rekent de wereldpositie uit en
  kijkt in het raster (R8-textuur, 1 texel per tegel). Onverkend = zwart over terrein, water, bomen en eenheden tegelijk;
  lucht en buiten het raster ook. Rand: smoothstep-interpolatie, drempel 0,62 plus ruis (bolle zwarte bogen), daaronder
  een zoom van 0,10 met om-en-om-pixels (frame 36). Wolven in onverkend gebied worden ook verborgen (schaduw, hp-balk).
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
| Zicht dorpeling 4, gebouw 4 tegels | Niet te meten zonder het origineel te draaien: in `1.png` ligt de mist ca. 3 tegels boven de bovenste dorpeling, dus het startgebied is niet de som van dorpelingzicht. |
| Startcirkel 8 om vlag, kampvuur en voorgebouwde gebouwen | Straal gemeten in `1.png`, één opname; de gebouwen erbij is een besluit van de gebruiker (2026-10-30). |
| Minikaart-schaal 2,6 px per tegel, venster 300x186 | Het origineel bij 900 px hoog: ovaal M1 ca. 32 px native breed voor een cirkel van 8, kader 158x101 x1,875. |
| Camerakader en stippen op de minikaart | Gevraagd door de gebruiker; in de drie opnamen van het origineel is geen kader te zien. |
| Minikaart draait niet mee met de camera | Het origineel had een vaste kijkrichting; hier draait het kader mee. |
| `leeg` blijft hoogte -2 (`tegels.json`) | Leeg is altijd zwart; alleen de halve tegel water/oever op de grens van verkend land en leeg (noordoever meer M2) kan nog wegzakken. Pas aanpakken als het opvalt (`map2.md` punt 1/5). |
| Plaatsnaam op de minikaart | Nog niet: waar de namen ("HOONTON", "GOATTON") vandaan komen is niet nagegaan. |
