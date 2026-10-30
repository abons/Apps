# Mist van oorlog (fog of war)

2026-10-30. Code: `spel/sim/mist.gd`, `spel/view/mist_view.gd`, `spel/shaders/mist.gdshader`, test `spel/test/mist_test.gd`.
Getallen: `spel/data/spel.json` `mist`. Achtergrond (void, `leeg`): `map2.md`.

## Wat het origineel deed

| punt | bevinding | bron |
| --- | --- | --- |
| Standen | **Twee**: onverkend = effen zwart, verkend = volle kleur. Geen grijze "niet meer in zicht"-laag: verkend blijft verkend. | Alle 9 opnamen van M1 (`mission1.png`, `1_*.png`): nergens gedimd terrein naast de mist. De donkere grasvlakken in `1_left`/`1_rightbottom` zijn grasvarianten (tex 3-5, eigen textuur en rasterrand), geen mist. |
| Eenheden in verkend gebied | Zichtbaar, ook zonder dorpeling ernaast. | `1_right.png`: koe en beker in beeld, geen levende dorpeling in de buurt. |
| Rand | Zwart in **bolle bogen** van ca. 1-2 tegels die het land in steken, met een **smalle gerasterde zoom** (enkele pixels, om-en-om). Geen brede verloop. | Uitsnede `mission1.png` rechtsboven (rotsen NO) en de bovenrand van `1.png`. Past bij tegelframes 37 (effen zwart) en 36 (gerasterd). |
| Start | Klein verkend gebied rond vlag en kampvuur, de rest zwart. Bovenrand in `1.png` ligt ca. 8 tegels van de vlag (gemeten: 231 px native recht omhoog = 5,8 diagonale stappen van 40 px). | `1.png`, minikaart: een klein ovaal rond "HOONTON". |
| Minikaart | Zwart buiten verkend. | `1_lefttop.png`. De remake heeft nog geen minikaart. |
| beasts-src | Heeft geen mist (alleen `MARAUDER_SIGHT`, `HOARD_SIGHT`). | grep fog/reveal/sight op `beasts-src`. |

## Wat de remake doet

- **Sim** (`Mist`, in `Wereld.mist`): `verkend` per tegel (0/1) en `versie`. Start: cirkel `start_straal` 8 om eigen vlag
  en kampvuur, plus het zicht van de startdorpelingen. Elke tik: een dorpeling op een nieuwe tegel verkent binnen
  `dorpeling` 4; een afgebouwd gebouw eenmalig binnen `gebouw` 4 plus halve afdruk. `leeg` nooit.
- **View**: één schermvullende quad na alles (render_priority 127) leest de dieptebuffer, rekent de wereldpositie uit en
  kijkt in het raster (R8-textuur, 1 texel per tegel). Onverkend = zwart over terrein, water, bomen en eenheden tegelijk;
  lucht en buiten het raster ook. Rand: smoothstep-interpolatie, drempel 0,62 plus ruis (bolle zwarte bogen), daaronder
  een zoom van 0,10 met om-en-om-pixels (frame 36). Wolven in onverkend gebied worden ook verborgen (schaduw, hp-balk).
- **Aan/uit**: standaard aan; met een `--scenario` standaard uit (oude frames blijven gelijk), behalve `mist_*`.
  `--mist=aan|uit` overschrijft. Frames: `--scenario=mist_start` en `mist_verkend` (`spel/screenshots/mist_*.jpg`).

## Eigen keuzes (niet vastgesteld)

| keuze | waarom |
| --- | --- |
| Zicht dorpeling 4, gebouw 4 tegels | Niet te meten zonder het origineel te draaien: in `1.png` ligt de mist ca. 3 tegels boven de bovenste dorpeling, dus het startgebied is niet de som van dorpelingzicht. |
| Startcirkel 8 om vlag en kampvuur | Gemeten in `1.png`, één opname. |
| `leeg` blijft hoogte -2 (`tegels.json`) | Leeg is altijd zwart; alleen de halve tegel water/oever op de grens van verkend land en leeg (noordoever meer M2) kan nog wegzakken. Pas aanpakken als het opvalt (`map2.md` punt 1/5). |
| Camera niet extra begrensd | Grens blijft eiland + 6 m (`main.gd`). Of het origineel scrollen in het zwart toeliet, is niet te zien. |
