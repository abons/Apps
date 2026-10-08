# TODO (op je pc)

Wat hier nog niet automatisch kon. Het meeste gaat over echte gameplay-video's van de Android-games,
want die kunnen alleen op een telefoon of emulator opgenomen worden.

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

## 4. Online zetten

- [ ] Het werk samenvoegen in `main`.
- [ ] GitHub Pages aanzetten: Settings → Pages → Source "Deploy from a branch" → `main`, map `/ (root)`.
      De pagina staat dan op <https://abons.github.io/Apps/>.

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
