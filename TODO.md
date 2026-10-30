# TODO (op je pc)

Wat hier nog niet automatisch kon. Het meeste gaat over echte gameplay-video's van de Android-games,
want die kunnen alleen op een telefoon of emulator opgenomen worden.

## Hier begint de volgende sessie

Beasts & Bumpkins-remake (`docs/beasts-bumpkins-remake/`, stand in de README daar; originele data lokaal in `lokaal/`, niet in git):

0. ⚠️ **Onafgemaakt werk in de werkmap (2026-10-30, 5 agents gestopt op budget, niets gecommit, niet getest):** M2-gameplay (dorpelingen gezondheid/dood, wolven bijten/doden, kinderen vluchten, wolf-respawn, levensloop baby>kind>volwassene>oudere>dood, kas-beloningen uit de MIS; was bij wolf_test), M3-gameplay (voetvolkgilde: soldaat worden, max 6, zwaardvechten, put, tweede kelkregel +6.000; was bij frames), prijzen/geluk/misdaad (prijzenscherm per waar, menu pauzeert, misdaad per missie aan/uit; was bij hint_test en missies.md), assets (wolf + donkere wolf, voetvolkgilde v3, voetsoldaat; typfout in `koepel`), APK (export templates staan, Android-preset, touch-camera, Mobile-renderer; emulator gaf geen beeld met SwiftShader, volgende poging `-gpu host`). Alle wijzigingen staan door elkaar in `spel/` (`git status`): eerst alle tests draaien, fouten herstellen, dan per onderwerp committen. Open vragen gebruiker: minikaartkader beoordelen tijdens spelen.

1. **Spellogica missie 1** (`spel/sim/`): staat sinds 2026-10-29: bouwen (hut/loods/kippenhok, stapels, hut-glb), kas + prijzen, koe-generator + koeien claimen, gezin (2 bedden per hut, `--scenario=gezin`), winst (6 dorpelingen + 4 eigen koeien) en verlies (<2), HUD-telling en uitslag (`--scenario=claim`). Graan en brood staan (molen + akker, `--scenario=molen`). Melk staat ook (melkerij, `--scenario=melk`; het rieten dak is nog de oude bake). Zelfstandig: bouwen aan open plannen, oogsten, melken, rapen; nacht = hut (2 bedden) of slaapzak bij het kampvuur; zonder opdracht bij het dorp. Bouwmenu groeit (hut/kippenhok/loods -> molen/akker -> melkerij/hek/poort), hek (slepen = rij, bouwers lopen door naar het volgende stuk) en poort (klik = open/dicht) staan; eigen koeien gaan de weide in (poort open) en blijven erin (poort dicht). Wegen ook (kaartpad als keienstrook, weg van elke deur naar het pad, 2 kas per tegel, direct; in beasts-src zijn het bouwklussen van 3 s per vak). Bouwersgilde ook (man + klik op loods = bouwer, 30 kas, 2x bouwen, vecht niet; gele helm als placeholder, eigen bouwer-glb uit concept `bouwer.jpg` open). Eieren ook (kippenhok + 3 kippen, `modellen/dieren/kip.py`, ~6/10 na 3 rondes, `--scenario=kippen`; `ei.glb` nog niet in beeld). Nog open: **zaagclip** naast de hamerclip. Gezin: de deurtegel ligt ~3,5 m van de echte voordeur (voetafdruk 4x4 blokkeert, en het hek van de hut-glb staat ervoor), dus ze verdwijnen een stukje voor de deur; een opening in het hek of een looppad naar binnen is open. ⚠️ Startvolk is al 6, dus de winst hangt nu alleen aan de koeien; of het origineel kinderen meetelt is niet nagekeken. Niet door mij gespeeld, alleen headless/frames.
2. **Modellen in het spel**: de zes personages staan erin (2026-10-29, `Bumpkin.glb_voor`; sex 13 = jongen, 14 = meisje aangenomen). Loods en kippenhok staan in het bouwmenu (2026-10-29). Nog: molen, melkerij (`modellen/gebouwen/`), koe met `koe_vacht.gdshader`. Eerst het rieten dak van melkerij en kippenhok opnieuw bakken (dakschil niet als bakbron; nu bruin met strepen).
3. **Conceptronde 3 is af** (2026-10-30, alles goedgekeurd: voetsoldatengilde v3 met wenteltrap, boogschuttersgilde, stadhuis, brouwerij (straal pas als animatie beoordelen, anders gesloten tank), slaapzak; log `lokaal/concept/ronde3_log.md`). Draagprops pas na de rigs. Volle maat van voetsoldatengilde v3 nog ophalen (nu 941x1024). Lijst op de telefoon: `http://axel-pc:8098/lijst.html`. Volgende conceptronde: 4 (gebouwen: kerk, gilden, stallen, gevangenis, uitkijkpost, herberg); de **hut in 4 bouwstanden** heeft nog geen concept.

## 1. Gameplay-video's van de Android-games

Deze kaartjes tonen nu een slideshow van screenshots uit de repo's. Een korte video maakt ze levendiger.

- [ ] **Beasts**: dorp bouwen, oogst naar de winkel, beesten die rondlopen
- [ ] **Kwelder**: eiland verkennen in de mist, een stad veroveren, een kwelder inpolderen
- [ ] **DnDAI**: een beurt aan tafel: verhaal, suggestie tikken, dobbelsteen rollen
- [ ] **Fast Lane**: een week in de stad: lopen, werken, de weekafrekening

Opnemen (telefoon via USB, met USB-debugging aan):

```sh
adb shell screenrecord --time-limit 20 --size 720x1600 /sdcard/demo.mp4
adb pull /sdcard/demo.mp4
```

Of met [scrcpy](https://github.com/Genymobile/scrcpy): `scrcpy --record demo.mp4 --no-audio`.

Daarna klein maken en in de juiste map zetten (voorbeeld voor Beasts):

```sh
ffmpeg -i demo.mp4 -t 20 -vf scale=390:-2 -an -c:v libx264 -crf 26 -movflags +faststart media/beasts/demo.mp4
ffmpeg -i media/beasts/demo.mp4 -c:v libvpx-vp9 -b:v 0 -crf 38 -an media/beasts/demo.webm
ffmpeg -i media/beasts/demo.mp4 -frames:v 1 -q:v 3 media/beasts/poster.jpg
```

En in `apps.js` bij die app toevoegen:

```js
video: ["media/beasts/demo.mp4", "media/beasts/demo.webm"],
poster: "media/beasts/poster.jpg",
```

## 2. Web-demo's eventueel opnieuw opnemen

De video's van Word Guesser, Woord Swiper, Woord Puzzel, Kinderwoordjes en e-charge zijn automatisch
opgenomen in een headless browser. Ze werken, maar:

- [ ] **Kinderwoordjes**: in de opname wordt niets voorgelezen (de testbrowser heeft geen stem). Een
      opname op de telefoon, met geluid, laat beter zien hoe een peuter de app gebruikt.
- [ ] **e-charge**: de video (`demo.mp4`/`demo.webm`) toont nog "geen prijzen", omdat de stroomprijs-API toen
      niet bereikbaar was. De drie screenshots (`planner`, `laden`, `uitleg`, 2026-10-06) hebben wél echte
      prijzen; neem de video opnieuw op, dan staan de kosten er ook in.
      Opnieuw proberen in de lokale sessie met emulator (2026-10-08): de cloudsessie kon dit niet, want haar
      netwerkregels blokkeren `public.api.energyzero.nl` (403 op CONNECT). Stappen:
      1. `git clone https://github.com/abons/e-charge`, `npm ci`, `npm run build`, serveer `build/` lokaal
         (of `npm run serve`).
      2. Controleer eerst dat de prijzen binnenkomen: kies een auto (de Leaf, anders geeft de app geen
         kosten), vul huidig en doel in en kijk of de kostenregel een bedrag toont, niet "geen prijzen".
         Lukt dat niet: stop, neem niets op.
      3. Neem 15-20 s op op 390x844 (Playwright `recordVideo`, of de emulator): planner met prijzen, een
         laadbeurt starten en laten lopen, kosten zichtbaar, daarna uitleg. Volg de flow van de
         screenshots.
      4. Maak klein met de ffmpeg-commando's uit sectie 1 (naar `media/e-charge/demo.mp4`, `demo.webm`,
         `poster.jpg`), elk onder een paar MB. Kijk een paar frames na op bedragen.
      5. Haal dit punt weg en pas `apps.js` alleen aan als paden of velden wijzigen.
- [ ] **Alle andere kaartjes zijn verouderd**: de screenshots en video's van Word Guesser, Woord Swiper,
      Woord Puzzel, Fast Lane, Kwelder, Beasts, DnDAI, Kinderwoordjes en Volleybal dateren van 2026-09-30
      tot 2026-10-05 en komen niet meer overeen met de huidige apps. Alleen e-charge is op 2026-10-06
      ververst. Maak ze opnieuw, per app, van de huidige versie.
- [ ] Optioneel: opnemen op je eigen telefoon (schermopname van Android/iOS) voor een scherper beeld.

- [ ] **Volleybal**: het kaartje toont screenshots; een korte opname van de app op je telefoon (team kiezen,
      aanwezigheid doorgeven) maakt het levendiger.

- [ ] **DnDAI**: de screenshots op het kaartje (`media/dndai/`) zijn dezelfde als in de publieke repo en
      inmiddels verouderd. Vervang ze door nieuwe van de huidige versie van de app.

## 3. Welke apps horen erbij?

- [ ] **Vocal**: het kaartje staat er, zonder GitHub-link omdat de repo privé is. Maak de repo publiek en
      voeg de link toe, of laat het zo.
- [ ] Niet opgenomen: `timecalc` (werktool), `Unity_bumpkins` en `godot_bumpkins` (voorlopers van Beasts),
      en oudere repo's. Toevoegen als je dat wilt.
- [ ] Zodra de Android-games op Google Play staan: Play-links toevoegen bij `links` en de `status` aanpassen.

## 4. Onderzoek afmaken (gemerged 2026-10-23, beide onvolledig)

- [ ] **Monetisatie-onderzoek herstarten**: `onderzoek/2026-10-monetisatie/workflow.js` lokaal opnieuw
      draaien (pad `R` bovenin aanpassen, Sonnet-agents, netwerk vrij zodat Play Store en App Store
      bereikbaar zijn). De cijfers in de README daar zijn ongecontroleerd en 13 onderwerpen uit
      "Niet gedekt" ontbreken nog.
- [ ] **Remake-rapporten factchecken**: `docs/beasts-bumpkins-remake/onderzoek.md` nalopen op prijzen,
      licenties en versies voordat er iets gekocht of geïnstalleerd wordt. De factcheck-agents vielen
      uit door de sessielimiet.
- [ ] **Woordspellen-vergelijking uitvoeren**: het cloudrapport staat er (`onderzoek/verbeteringen-woordspellen.md`);
      de verbeteringen zelf zijn nog niet gebouwd. Materiaal: `media/ai-sessie/` (README, per app
      `NOTES.md` + screenshots + filmstrips; lees nooit de mp4). Open waarnemingen: wordpuzzle-bord verschuift ~20 px bij wisselende
      aanwijsbalk; wordpuzzle-invoer weg na force-stop (normaal sluiten niet getest); wordguesser
      toont Engelse dialoogtekst in NL; shake-animatie bij afgewezen woord nooit gefilmd; dialoog-,
      swipe- en shuffle-filmstrips zijn op timing benoemd, niet visueel gecontroleerd.

## 5. Ideeën voor nieuwe apps

Uit een vergelijking met negen open-source Android-spellen zonder reclame (2026-09-30); het hele
onderzoek staat in [Klein, snel, reclamevrij](https://claude.ai/artifact/RRZoGKhAdJLwQGLt44Z5yQ) (privé,
alleen voor mij te openen). Ze staan op
volgorde van hoeveel ze hergebruiken van wat er al is. Alle vijf volgen de regels van de rest: klein,
offline, geen reclame, geen runtime-dependencies. ⚠️ Idee overnemen mag, code niet: zeven van de negen
vergeleken projecten zijn GPLv3.

- [ ] **Woordraster**: letters in een raster van 4×4 tot 6×6, zo veel mogelijk woorden vinden binnen de
      tijd. Draait op de 17 woordlijsten, de dagpuzzel en het scorebord van de woordspellen.
- [ ] **Kruiswoordhulp**: bekende letters invullen en passende woorden zien, plus anagrammen, met de
      Nederlandse definities die al offline op het toestel staan. Kan als web-app, zoals Kinderwoordjes.
- [ ] **Stroomplanner**: wanneer draai je de was, de vaatwasser of de droger? Dezelfde kwartierprijzen
      als e-charge, één scherm, geen login.
- [ ] **Dagelijkse logicapuzzel**: een nonogram of ander rasterspel met een puzzel per dag. Er is geen
      woordlijst nodig, dus hij werkt in elke taal.
- [ ] **Kindertellen**: een tweede peuter-app naast Kinderwoordjes, met grote plaatjes om te tellen en
      voorlezen. Dezelfde bediening, geen build-stap.

De verbeterpunten voor de bestaande apps (deelknop, snelkoppeling naar de dagpuzzel, uitdaging per
bordcode, toegankelijkheid) staan in de todo van elke app zelf.
