# TODO (op je pc)

Wat hier nog niet automatisch kon. Het meeste gaat over echte gameplay-video's van de Android-games,
want die kunnen alleen op een telefoon of emulator opgenomen worden.

## Hier begint de volgende sessie

- [ ] **Gebruiker zoekt uit (B&B):** gaf de kelk in missie 3 alleen +7.000, of ook de tweede regel +6.000 (M3.MIS heeft er twee; nu alleen +7.000)?

Beasts & Bumpkins-remake (`docs/beasts-bumpkins-remake/`, stand in `spel/README.md` en `mobiel.md`; originele data lokaal in `lokaal/`, niet in git; open vragen voor de gebruiker op `lokaal/concept/vragen.html` = http://axel-pc:8098/vragen.html):

- **Compatibility-renderer als mobiele standaard** (besluit nog niet genomen, wel aangevinkt 2026-11-01): gemeten M1 Edge 30 Neo Vulkan 20,8 / Compatibility 23,2 fps, Moto G9 Play 12,7 / 14,8 (compat-apk van 2026-10-31 23:10, tekent de hele kaart omdat de mist er niet werkt). Nodig: mist-diepte omrekenen (`d*2-1`, zie `mobiel.md` Web), kleuren gelijk aan pc (compat-gras veel feller), stencil van `shaders/weg_ghost.gdshader` vervangen. Daarna opnieuw meten op beide telefoons.
- **Niet op een telefoon gezien** (2026-11-01): build vanaf `2d9c44a` (mist vroeg stoppen) en `30a7ecb` (egaliseren), emmer `6f6f60b`, sikkel/rapen `6093d7e`; touch: bouwplaats aantikken + "Annuleer", hand-knop Stilstaan tegen de bovenste rij, portretpaneel. Op de Moto G9 Play (`ZY32825QBS`, niet in de familietabel) staat nu de compat-apk, op de Edge 30 Neo de Vulkan-build van 09:02.
- **Wesp en wespennest, ronde 1** (2026-11-02): ronde 2 pas na deze week (gebruiker: "niet deze week, focus op speelbaar geheel"). Stand: `modellen/dieren/wesp.py`, preview `modellen/dieren/preview/wesp*.png`.
- **Ronde 6, modelronde 1 gedaan** (2026-11-02; gebruiker: "1 iteratie per model is prima voor nu"): `modellen/natuur/kerkhof.py` -> heilig_zwaard, zombiegraf, kerkhofhek, graf, grafsteen, vreemde_boom (glb's, previews `modellen/natuur/preview/m5_*.png`), in het spel gekoppeld (`objecten.json`, `MissieProps.effecten`/`_kerkhofmuur`, `spel.json wezen_model.zombiegraf` glb + licht), beeld `spel/screenshots/missie5.jpg`. Procedureel ~5-6/10. Voor een volgende ronde: vreemde boom te recht en het gezicht klein/ondiep (concept: gedraaide stam met een lus); graf-gloed is een vlak groen paneel en de mist valt weinig op; vlechtwerk op de kruisen is een herhaald patroon, geen echt knoopwerk; zombiegraf-dak glad (concept: platen met scheuren), deur te donker; zwaard leest op afstand als een streepje (schaal 1,4), geen aura zoals het concept; kerkhofhek zonder hoekpaal-sierkrullen zoals de sprite; kerkhofpoort (klasse 220) heeft nog geen model.
- **Missie 5 speelbaar** (2026-11-02, `map5.md`): nog niet door de gebruiker gespeeld. Zwaarddrager hakt het graf kapot (gebruiker 2026-11-02). Eigen keuzes ter controle: graf zet zombies uit (max 2, 120 s), doel 10 mensen (bestand > 10). Modellen sinds ronde 6 (zie boven).
- **Missie 6 speelbaar** (2026-11-02, `map6.md`): nog niet gespeeld. Eigen keuzes ter controle: Parpton = 5 vechtende wezens zonder economie (geen AI-dorp, toren schiet niet); vlammenval direct dood; alle 26 vallen verborgen, ook de mijnen (vallen zien toont ze 20 s); goudregels (klasse 203 + koe) niet nagebouwd; Murray (eigenaar 96) en wezen type 30 (nu wolf) onbekend.
- **Missie 7 speelbaar** (2026-11-02, `map7.md`): nog niet gespeeld. Eigen keuzes ter controle: kampvuur (86,124) erbij (kaart heeft er geen); put en hutten over de wegen van Pantston; boom (104,110) weg (anders noorden onbereikbaar: alleen schuin tussen bomen door); kerk zonder huwelijken (MIS7-3); bekerpuzzel: neergezette beker blijft staan, prijs 5 goud, klasse 203/204 niet nagebouwd; goud in het oliebed = 7 vuren. Vraag: wat deed het huwelijk in de kerk, en konden dorpelingen schuin tussen bomen door?
- **Missie 8 speelbaar** (2026-11-02, `map8.md`): nog niet gespeeld. Eigen keuzes ter controle: winst = kas >= 14.000 (bestand > 13.999 en > 14.000) en Wormton uitgeroeid; Wormton = 4 vechtende wezens zoals Parpton (geen AI-dorp); hek van Wormton houten placeholder, poort open, hun 3 koeien wild; type 3 = priester (gebruiker 2026-11-03); tweede vlag "Goatton" op Gruffton onbekend; goudregel (koe + klasse 203) niet nagebouwd. Vraag: viel Wormton in het origineel ons dorp aan?
- **Missie 9 speelbaar** (2026-11-02, `map9.md`): nog niet gespeeld. Eigen keuzes ter controle: leerling = tovenaar met één spreuk (zoals M6); winst binnen 1 tegel van de tempel (blok 2x2, placeholder); Wormton = 6 vechtende wezens (geen AI-dorp), bakkerij (53) en tarwe (78) weggelaten; type 3 = priester (gebruiker 2026-11-03); geen hints (geen MIS9-*.TXT), dus niets vertelt dat de krijger de muur om de sleutel opent. Vraag: had M9 een tekst over sleutel of muur, en kon de leerling zelf vechten?
- **Missie 10 speelbaar** (2026-11-03, `map10.md`): nog niet gespeeld. Eigen keuzes ter controle: klasse 90 voor de ingang van het westen = puinhoop (plus tegel (80,79) dicht); alle drie de hendels openen de magische poort; de twee tempels teleporteren naar elkaar (de zaal met de mantel heeft geen ingang); de mantel maakt de drager onzichtbaar voor elk wezen; de toren is met stenen kapot te gooien (400 hp); bos helemaal dicht; altaar = twee knallen; vleermuis/bloedwesp als wespen, type 0 weggelaten. Antwoord gebruiker 2026-11-03: toren slopen met de mantel onder de neus van de reuzen, of ze lang genoeg weglokken (kan nu al). Hendels openen de magische poort, de mantel ligt bij het donkere altaar: bevestigd.
- **Missie 11 speelbaar** (2026-11-03, `map11.md`): nog niet gespeeld. Eigen keuzes ter controle: Bearton = 4 vechtende wezens (ook de 2 kinderen, zwak, gooien stenen); Fontein der Jeugd = volle gezondheid, ook een oudje weer jong volwassen (gebruiker 2026-11-03, gebouwd); rotsrand (64,9) begaanbaar zodat de sleutel te halen is; de demon (type 26, eigenaar 1) op de oever (98,88) is onbereikbaar en weggelaten; boogschutters, ridders, uitkijkpost en stadhuis (hints 11-3..11-6) bestaan nog niet. **Open: Bearton was in het origineel een computergestuurd vijandig dorp met dezelfde units en gebouwen als het eigen dorp, andere kleur (gebruiker 2026-11-03); de remake heeft nog geen AI-dorp dat bouwt, boert en aanvalt.** Beeld al gedaan: vijandige dorpelingen = Bumpkin, gebouwen en vlag = eigen glb, in de dorpskleur per eigenaar (1 oranje Bearton, 2 groen Parpton; eigenaar 3 onbekend). Na een nieuwe glb: `tools/maak_dorpkleur.gd` + `--import`.
- **Missie 12 speelbaar** (2026-11-03, `map12.md`): nog niet gespeeld. Eigen keuzes ter controle: torens alleen door een BomberMan te slopen (onkwetsbare wezens); de tempels teleporteren naar het eiland (zoals M10); de vijandelijke bommenwerper komt elke dag (180 s), loopt recht naar de eigen toren en is met 1 klap dood (gebruiker 2026-11-03); ridders (max 2 per 180 s), ogre (max 1) en wolven als generators (p5/p6 onduidelijk); eigen type 8 = voetsoldaat; vijandelijke boogschutters gooien stenen. Eiland via de teleportcirkel: bevestigd.
- **Missie 13 speelbaar** (2026-11-03, `map13.md`): nog niet gespeeld. Klooster over land door het rotsdoolhof en over het ijs (gebruiker); vijf schuine doorgangen in de rots zijn gras (`missies.13.begaanbaar`). Eigen keuzes ter controle: Ringworm vreedzaam (verdrag), pest pas op het wiel na het kopen van de rol (10.000), Ringworm < 2 = gewonnen. Ringworms dorp is te voet onbereikbaar, zoals het origineel: pest werpen over de berg vanaf (65,27) (gebruiker 2026-11-03). Ijs (tex 64-70) is begaanbaar maar ziet eruit als zand. Nog nodig: gevangenis (154), brouwerij (54), appelbomen (94), klasse 123, misdaad (hint 13-4).
- **Priester en spreukenwiel gebouwd** (2026-11-02, `spel/sim/priester.gd`, `spel/view/spreukwiel.gd`, beeld `spel/screenshots/priester.jpg`): nog niet gespeeld. Eigen keuzes ter controle: alleen mannen, 6 per kerk, rol 200, kerk 2.000 / 180 s / 2x2, mana 100 (start 50, +0,5/s); genezen 30 mana straal 3 = naar max hp, regen 40 straal 4, groei 25 straal 3 (koe alleen eigen); de dichtste priester met mana gaat; begraven vanzelf binnen 24 tegels, 4 s, grafsteen (57); onbegraven lijk weg na 40 s (geen ziekte); priester vlucht zoals de bouwer; mijter-placeholder, geen eigen model. Niet gebouwd: tiende, huwelijk; de tovenaar heeft alleen bliksem op het wiel. Vraag: betaalde een priester mana of scrolls?
- **Tovenaarsspreuken** (2026-11-03, lijst gebruiker, `spel/sim/vuurbal.gd`, `spel/test/tovenaar_test.gd`, beeld `spel/screenshots/tovenaar.jpg`): nog niet gespeeld. Eigen keuzes ter controle: vuurbal 25 mana, 50 schade, 12 tegels/s, 10 tegels ver; vallen zien 20 mana straal 10, 20 s zichtbaar; zien 15 mana straal 8, blijft verkend (origineel tijdelijk); zombie 50 mana, 60 s, eerst wezens dan dorpelingen; angst 30 mana straal 4, 8 s; vakken 0-4; magische rol geeft de spreuk in plaats van +50 mana. Geen eigen geluid voor vuurbal (067 ogre-staf?). Open: `indeling_test` faalt (F1-uitleg 1127 px breed op 1080x2400), niet door deze wijziging.
- **Zeven priesterspreuken compleet** (2026-11-03, `spel/sim/pest.gd`, koppeling in `gameplay.md` sectie 7): nog niet gespeeld. Eigen keuzes ter controle: zegen 40 mana, 30 s, schade x1,5, ontvangen x0,75, +10 % hp; bescherm (Special) 30 mana, 30 s, ontvangen x0,5 (stapelt met zegen); pest 50 mana, besmet het dichtste doel binnen 1 tegel, -3 hp per 2 s zonder herstel, 15 % kans per 2 s om iemand binnen 1,5 tegel te besmetten (dorpelingen en vijand_*-wezens, geen wolven), gaat niet vanzelf over; pest genezen 35 mana straal 3; pest-vakje linksonder (M13); geldig doel: genezen/zegen/bescherm alleen op een dorpeling (eerder ook de grond), pest op dorpeling of vijand, regen/groei/pest genezen op elke tegel; ongeldige klik = melding, spreuk blijft gekozen. Open: wiel M26-M29 wacht op die missies; priester heeft nog geen eigen model.
- **Schade en brand aan gebouwen gebouwd** (2026-11-03, `spel/sim/gebouw_schade.gd`, beeld `spel/screenshots/gebouw_brand.jpg`): nog niet gespeeld. Eigen keuzes ter controle (`spel.json gebouw_schade`): hp hut 300, kippenhok 150, loods 300, molen/melkerij/gilde 400, put 250, kerk 500; klap 20 per 2 s (+ slagduur), brand na 3 klappen, -1,5 hp/s; aanvallers zombie en `vijand_*` (wolven en wespen niet), alleen als er geen dorpeling in zicht is; bouwer repareert 3 hp/s x tempo 2, vanzelf onder 80 % hp, max 2 per gebouw, blust niet (in M1-M6 zonder kerk brandt een gebouw dus door tot het instort, tenzij een bouwer het bijhoudt: zo laten?); instorten = puinhoop 10 s en weg, hut weg = bewoners dakloos, gilde weg = leden houden hun rol, kippen blijven rondlopen.
- **audio_test faalt** (2026-11-02, ook zonder de M5-wijzigingen): "na track 4 een pauze, dan track 5"; eerder een flake, nu elke run.
- **Open vraag gebruiker** (vragen.html): graanmodel lager, tot het middel zoals het origineel? (nu bijna hoofdhoogte; tijdens maaien zakt de oogsttegel tot 30 %, `view/bouwmenu.gd`).

## Openstaand B&B (stand 2026-10-30, deels achterhaald door 2026-10-31/11-01 — eerst nakijken voor je er iets mee doet)

0. ⚠️ **Onafgemaakt werk in de werkmap (2026-10-30, 5 agents gestopt op budget, niets gecommit, niet getest):** M2- en M3-gameplay is gecommit (`35b8b3d`: leven/dood, wolven bijten, vluchten, levensloop, kas-beloningen, voetvolkgilde max 6, zwaard, put + dorst, donkere wolf = sex 29; sex 24 is een wesp, nog als wolf; tweede kelkregel +6.000 vuurt bewust niet; dorst verlengt het leven nog niet; frames `missie2_wolf.jpg`, `missie3_soldaat.jpg`, `missie3_put.jpg`), assets (wolf + donkere wolf, voetvolkgilde v3, voetsoldaat; typfout in `koepel`), APK (gecommit; Mobile/Vulkan op de emulator zwart na 3 pogingen, Compatibility-rooktest met `--mist=uit` speelt wel; nu de Motorola: zie `mobiel.md` "Stand APK"). Alle wijzigingen staan door elkaar in `spel/` (`git status`): eerst alle tests draaien, fouten herstellen, dan per onderwerp committen. Klaar gekomen na het stoppen: voetsoldaat-model (`15e8329`) en wolf + donkere wolf (`cc44598`; doodpose matig; de bruine koepel was een paddenstoel (klasse 83, schaal 2,3, bijna mensgroot) onder de scenario-koe). Prijzen/geluk/misdaad is gecommit (prijzenscherm, `--scenario=prijzen`, `test/economie_test.gd`). Nog geen missie met `misdaad.aan` (origineel M13), geen straf-schuiven per misdaad. Open vragen gebruiker: minikaartkader beoordelen tijdens spelen.

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
