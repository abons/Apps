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
- [ ] **e-charge**: in de opname staat "geen prijzen", omdat de stroomprijs-API niet bereikbaar was.
      Een opname met echte prijzen toont ook de kosten.
- [ ] Optioneel: opnemen op je eigen telefoon (schermopname van Android/iOS) voor een scherper beeld.

## 3. Welke apps horen erbij?

- [ ] **Vocal** is een privé-repo zonder publieke pagina, daar kon ik niets over vinden. Hoort die op de
      pagina? Voeg dan een kaartje toe in `apps.js`.
- [ ] Niet opgenomen: `timecalc` (werktool), `Unity_bumpkins` en `godot_bumpkins` (voorlopers van Beasts),
      en oudere repo's. Toevoegen als je dat wilt.
- [ ] Zodra de Android-games op Google Play staan: Play-links toevoegen bij `links` en de `status` aanpassen.

## 4. Online zetten

- [ ] Het werk samenvoegen in `main`.
- [ ] GitHub Pages aanzetten: Settings → Pages → Source "Deploy from a branch" → `main`, map `/ (root)`.
      De pagina staat dan op <https://abons.github.io/Apps/>.

## 5. Ideeën voor nieuwe apps

Uit een vergelijking met negen open-source Android-spellen zonder reclame (2026-09-30). Ze staan op
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
