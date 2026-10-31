# Beasts & Bumpkins remake: fundament (missie 1 Aorta, missie 2 Terug op het vasteland)

Godot 4.7.2 (Forward+, GDScript, pc eerst). Het eiland Aorta uit de originele kaartdata, zes dorpelingen onder
spelersbesturing, dag/nacht, seizoenen en weer, bouwen (hut, loods, kippenhok; prijs uit de kas), koeien claimen en het
missiedoel (6 dorpelingen + 4 eigen koeien, verlies onder 2), gezinnen (stel in een hut met een vrij bed krijgt een kind).
graan en brood (akker rijpt, oogsten naar de molen, bewoners kopen brood = kas), melk (koe bij het dorp melken, naar de
melkerij, bewoners kopen melk), eieren (kippenhok met 3 kippen, die leggen en op het ei blijven zitten tot het geraapt
wordt). Vijanden: de wolven van missie 2 (zie Missies).

## Draaien

Snelst: rechtermuisknop op `speel.ps1` > **Run with PowerShell** (sync, import en spelen in een keer;
`speel.ps1 -Seizoen winter -Uur 22` voor een ander begin, `speel.ps1 -Missie 2` voor missie 2).

```
G=$LOCALAPPDATA/Microsoft/WinGet/Packages/GodotEngine.GodotEngine_Microsoft.Winget.Source_8wekyb3d8bbwe/Godot_v4.7.2-stable_win64_console.exe
powershell -File sync.ps1                       # kaart (data/origineel/) en glb's (assets/) kopieren
"$G" --headless --path . --import               # eerste keer en na elke sync
"$G" --path .                                   # spelen
"$G" --headless --path . --script res://test/sim_test.gd    # simtest (zonder GPU)
"$G" --headless --path . --script res://test/missie2_test.gd # simtest missie 2 (ook missie3_test, missie4_test)
"$G" --headless --path . --script res://test/wolf_test.gd    # wolven: zwerven, jagen, weide, stenen gooien
"$G" --headless --path . --script res://test/audio_test.gd   # laden alle klanken, muziekspeler
"$G" --headless --path . --script res://test/touch_bouw_test.gd  # touch: bouwen met Bouwen-knop, twee-vingerdraai
"$G" --headless --path . --script res://test/indeling_test.gd    # staand/liggend, pc/touch: niets buiten beeld of over elkaar
"$G" --headless --path . --script res://test/menu_test.gd        # startmenu, pauzemenu, opnieuw, andere/volgende missie
"$G" --headless --path . --script res://test/ghost_test.gd       # bouw-ghost: gebouw-glb, groen/rood, deurpijl, = gebouwd
"$G" --headless --path . --script res://test/bouw_plek_test.gd   # bouwers: elk een eigen plek, zagen bij de zaagbok, hakken bij de steenhoop
"$G" --path . --write-movie out/x/f.png --fixed-fps 10 --quit-after 60 -- --scenario=selectie   # frames (map out/x moet bestaan)
```

Opties na `--`: `--missie=1|2|3` (zonder: startmenu), `--seizoen=lente|zomer|herfst|winter`, `--uur=12`, `--tempo=2`, `--regen`, `--fps` (frametijden loggen),
`--gang=0|1|2` (loopanimatie, zie onder), `--scenario=overzicht|kaart|dorp|selectie|pad|loop` (gescripte camera/invoer voor frames),
`--geluid-log` (elke klank die start in de uitvoer), `--wolf_model=tripo|trellis|procedureel`, `--koe_model=tripo|procedureel` (spel.json `koe_model`, view/koe.gd), `--camwolf=4.5` (camera volgt de eerste wolf, met `--missie=2 --scenario=wolf`).

## Startmenu en pauzemenu

Zonder `--missie`/`--scenario` (telefoon, `speel.ps1` zonder `-Missie`) begint het spel met het **startmenu**
(`view/startmenu.gd`): perkament met alle 30 missies (`data/campagne.json`: ons label, dorp van de eigen vlag; een speelbare
missie toont de briefingtitel en het doel). Speelbaar = in `spel.json` `missies` en de kaart is er (nu 1-3); de rest staat vaal
onder "Nog niet gebouwd". **Doorgaan** = laatst gestarte missie; gewonnen missies krijgen "gewonnen" (`user://voortgang.cfg`,
scenario's en tests schrijven niet). In het spel: **menuknop** naast het munt-icoon (touch >= 48 dp) of **Esc** (in de bouwmodus
eerst bouwmodus uit) = pauzemenu (`view/pauzemenu.gd`): Hervatten, Missie opnieuw, Andere missie, Afsluiten (pc); sim, camera
en bouwmodus staan stil zolang het open is. Na de missie (2 s na de uitslag): gewonnen = Volgende missie / Verder spelen /
Andere missie, verloren = Opnieuw / Andere missie / Bekijken. Elke keuze laadt `main.tscn` opnieuw met `Startmenu.volgende`
(niets blijft over; de briefing is het laadscherm). Origineel: lineaire campagne zonder vrije keuze (alleen de dev-opdracht
`loadmission`), menu's pauzeerden; vrije keuze tussen de speelbare missies is eigen keuze. Test `test/menu_test.gd`
(`-- --frames` met venster: frames in `out/menu/`).

## Geluid

`view/geluid.gd` (een Node, in `main.gd` aangehaakt) leest sim en view en speelt: stem bij selectie en bevel (alleen de
leider; man/vrouw/jongen/meisje, ouderen pitch 0,9), hamer/zaag/houweel op `Bumpkin.impact`, sikkel en oogst, melken,
eieren, munt bij `verkocht`, klokje bij `plan_klaar`, poort, missie-stinger, UI-klik op elke knop; 3D: kampvuur, golven langs
de kust (5 lussen naar de dichtste kustpunten), koeien loeien, kippen tokken; 2D-lagen: wind (seizoen, regen, zoom), regen,
krekels 's nachts, vogels overdag, uil; missie 2 en 3: wolf gromt/hapt/jankt, steen (worp en inslag), zwaard, klap bij
geraakt, klok bij een dode, plop bij een geboorte, water bij de put, munten die tellen (beker, kasbeloning). Bussen
Master/Effecten/Stemmen/Omgeving, volumes in `Geluid.BUSSEN`. Pauze zet
werkgeluid stil; met `--write-movie` is alles stil. Bronnen: `audio/eigen/` (eigen synthese, `py -3.10 audio/maak_geluid.py`,
in git) en `assets/audio/beasts/` (beasts-src, via `audio/haal_beasts.ps1` uit sync.ps1, niet in git). Details: `../audio.md` sectie 6.

**Muziek** (`view/muziek.gd`, onder de root zodat hij het herladen van de scène overleeft): zoals het origineel cd-track 2
in het startmenu, track 3 zolang de briefing open is, in de missie en bij het einde stil; lussen en 1,5 s overvloeien.
Dempen met **Shift+M** (gewone M in het startmenu; in een missie is M de molen) of de noot-knop rechtsboven in het
pauzemenu, volumeschuif in het pauzemenu (pc); bewaard in `user://muziek.cfg`. De tracks zijn je eigen cd-rip:
`audio/haal_muziek.ps1` (uit sync.ps1) zet `lokaal/muziek/Track02..08` om naar `assets/audio/muziek/trackNN.ogg`, niet in
git. Zonder die bestanden blijft het stil. Details: `../audio.md` sectie 7.

`data/origineel/map1.json` en `map2.json` komen uit de gedecodeerde originele spelbestanden (auteursrecht): staan in `.gitignore`, net als `assets/`.

## Missies

`data/spel.json` `missies.<nr>`: kaart, `start_kas`, `doel` (alles moet: `dorpelingen` >=, `koeien` eigen >=, `kas_boven` = kas >,
origineel `cash>`), `verlies` (`dorpelingen_onder`), `koe_generator` (klasse 171) en optioneel `bos_dichtheid`. `Wereld.laad("", nr)`,
`main.gd --missie=nr`. Missie 1 (Aorta) ongewijzigd. **Missie 2** (Terug op het vasteland, `--missie=2`): kaart
`lokaal/map2/map2.json` (`python lokaal/map2/maak_map.py 2`, zelfde decoder als kaart 1; die geeft op kaart 1 dezelfde tex, wegen en
objecten), 10 dorpelingen (4 m, 4 v, 2 jongens), kas 6.999, doel kas > 10.000, verlies onder 2; kampvuur (90,76), vlag (92,73),
4 eigen koeien (klasse 110), voorgebouwde boerderij (klasse 51) als afgebouwde melkerij (`Wereld.plaats_voorgebouwd`, gratis, na de view),
bos 0,6. Scenario's `kaart` (van boven, noord boven, naast `lokaal/missies/m02_layout.png`) en `wolf`; frames `screenshots/missie2_*.jpg`.
**Wolven** (klasse 104, 3x, `sim/wolf.gd`, port van beasts-src `Beast` Kind.WOLF, waarden in `spel.json` `wolf`): zwerven rond hun
startplek, jagen op de dichtste koe binnen 7 tegels (wild of eigen) en eten haar na 2 beten op (`Wereld.verwijder_koe`, signaal
`koe_weg`); een dichte poort houdt ze tegen, dus een koe in een gesloten weide is veilig. Daarna 25 s verzadigd. Dorpelingen doen ze
niets. Vechten: met een selectie op een wolf klikken (`Wereld.geef_vechtbevel`, alleen volwassenen, niet de bouwer): hij loopt tot 4
tegels en gooit elke 1,8 s een steen (2 schade, hp 8; munitie oneindig, clip `aanval_steen`); wie niets omhanden heeft gooit zelf naar
een jagende wolf binnen 6 tegels. Hp 0: valt om, ligt 30 s. View: `view/wolf_model.gd` (placeholder uit meshes in de kleuren van
`lokaal/concept/img/wolf.jpg`, poten, kop, hp-balkje als hij geraakt is) en `view/wolven_view.gd`. Test `test/wolf_test.gd`; scenario
`wolf` (wolf bijt een koe, een man gooit), frame `screenshots/missie2_wolf_steen.jpg`.
Nog niet: wolf-glb, kinderen/baby's pakken, vluchten; goud (161) en drankjes (160) zijn placeholders, niet
op te rapen; klasse 226 (betekenis onbekend) is `geen`; prijzen/geluk, pensioen en de hints van missie 2 ontbreken; het leeg buiten de
kaart (zwart in het origineel) wordt water, zodat het meer in het NW in de zee overloopt. `ontbreekt` in objecten.json geeft per klasse
een waarschuwing in de log.

**Missie 4** (Beker van Vervulling, `--missie=4`, `../map4.md`): kaart `python ../lokaal/map2/maak_map.py 4 data/origineel/map4.json`, 4 dorpelingen, kas 8.000, voorgebouwde hut en bouwersgilde. Puzzel uit M4.MIS als data: `missies.4.voorwerpen` (sleutel naar de poort, tinnen beker naar de vlag = 0), `missies.4.regels` (`sim/regels.gd`: afgeleverd/opgeraapt/wezen_dood/aanraken -> maak/open/weg), `doel.aanraken` (triggerplek 41,11), mijnen en vuur in `spel.json` `vallen`. Wezens type 18 = zombie (`wezens.zombie`, standaard passief: den met ogen, `wezen_model`). Dynamische objecten (poort, muur, mijn, olie, vuur) tekent `view/missie_view.gd`. Test `test/missie4_test.gd`, frames `--scenario=missie4 --stap=overzicht|poort|beker|wezens|muur`, `screenshots/missie4_*.jpg`.

## Zelfstandig werk en de nacht

Wie niets omhanden heeft kiest elke 0,5 s zelf (`Wereld._kies_klus`): wat hij draagt wegbrengen, kopen waar hij trek in
heeft, en als volwassene bouwen aan een open plan (een bouwer altijd, anderen met hoogstens `zelf_bouwen_per_plan` (2)
tegelijk; een plan hoeft dus niet meer aangeklikt te worden), oogsten, melken, eieren rapen. 's Nachts is er geen klus:
wie een bed heeft (2 per hut) gaat de hut in, de rest gaat in een slaapzak (origineel `sleepers`) bij het kampvuur liggen;
's ochtends staat iedereen op. Zonder opdracht zwerft iedereen rond het kampvuur (anker); alleen na een loop-, vecht-,
claim- of gildebevel van de speler blijft hij in de buurt van waar hij stond. Een bevel van de speler gaat altijd voor.

## Weide

Een stuk grond dat hek en poort helemaal omsluiten (rechte buren, hoogstens 150 tegels, niet het kampvuur) is een weide
(`Wereld.weides`, opnieuw na elk afgebouwd hek of poort). Eigen koeien krijgen de weide met de meeste ruimte per koe
en zwerven alleen nog daarin; een dichte poort laat ze er niet in en niet uit (`poort_dicht`; koeien volgen tegelmiddens,
zodat ze niet langs de poort snijden). Origineel: "Don't forget a fenced-in enclosure in which to keep your cattle".

## Wegen

Padtegels (uit de kaart: `road` 1/2/6, plus wat er later bijkomt) worden een keienstrook van 1,3 m (`view/wegen.gd`,
`shaders/weg.gdshader`: procedurele kinderkopjes, rafelrand, sneeuw en nat), van tegelmidden naar tegelmidden; het terrein
eronder is alleen wat vertrapte grond. Onder een blokkerend object (de vlag staat op het kaartpad en blokkeert nu)
komt geen weg; de stroken lopen eromheen, en nieuwe wegen zoeken er een omweg langs. Elk afgebouwd gebouw met een deur (`Plan.DEUREN`: hut, molen, melkerij, kippenhok,
loods) krijgt meteen een weg van zijn deur naar het dichtste pad of het kampvuur (`Wereld.leg_weg`, BFS; beasts-src
`World.aim` bestelt die weg mee), `weg_per_tegel` (2) kas per nieuwe tegel, zonder bouwtijd. De laatste meters, van de
deurtegel tot de echte deur binnen de voetafdruk, tekent `Wegen` als stoep naar `Plan.deur_punt`.
Zelf wegen leggen (2026-10-30): bouwsoort **weg** (vanaf de start, `prijzen.weg` 2 kas en `bouwtijd_s.weg` 3 s per tegel,
beasts-src). Slepen legt een rij (`sim/bouwrij.gd`, ook voor hek): A* over 4 richtingen met een strafje per bocht, dus op
open grond een L met een bocht en anders om gebouwen, bomen en water heen; tegels die al pad (of al hek) zijn tellen mee en
kosten niets; lukt geen route dan de rechte L (eerst x, dan z) en wat daarvan niet kan wordt rood en niet geplaatst.
Dorpelingen bouwen een weg-plan zelf (`_open_plan`) en bouwen door naar het volgende stuk (`_volgend_plan`, zoals hek);
af wordt de tegel pad, gaat het plan uit de lijst (`Wereld._weg_af`) en tekent `Wegen` hem (`wegen_veranderd`). Een weg
mag niet onder een gebouw of plan, en op een (geplande) weg komt geen plan; voor een deur mag een weg wel.
Bouwen kan niet op pad (zoals het origineel), niet op andermans deurtegel, en alleen als de eigen deurtegel loopbaar en
bereikbaar is (een boompje voor de deur liet de weg eerst ernaast uitkomen). `test/deur_check.gd` legt `Plan.DEUREN` naast
de glb-ankers in alle vier de draaiingen (faalt boven 0,1 m): na een nieuwe gebouw-glb opnieuw draaien.

## Besturing

| invoer | doet |
| --- | --- |
| links slepen | selectiekader (Shift = toevoegen) |
| links klikken op unit | die unit kiezen |
| links klikken op grond | loopbevel voor de selectie; meerdere units waaieren uit rond de tegel |
| links klikken op een afgebouwde gereedschapsloods | de eerste volwassen man uit de selectie loopt erheen en wordt bouwer (30 kas): bouwt 2x zo snel, vecht niet, gele helm |
| links klikken op een koe | de eerste volwassene uit de selectie claimt haar (paarse halsband + bel); nog eens = loslaten |
| links klikken op een wolf | vechtbevel: de volwassenen uit de selectie (niet de bouwer) lopen erheen en gooien stenen |
| rechts klikken | selectie weg |
| rechts slepen, Q/E | camera draaien (PgUp/PgDn kantelen) |
| WASD/pijlen, schermrand | pannen (begrensd tot het eiland) |
| wiel | zoomen (2 m tot eilandoverzicht) |
| Spatie, 1 / 2 / 4 | pauze, tempo 1x/2x/4x |
| Esc, of de menuknop naast het munt-icoon | pauzemenu (opnieuw, andere missie, afsluiten) |
| knop rechtsboven (of B / L / H / M / J / G / T / F / P) | bouwmodus: hut / loods / kippenhok / molen / melkerij / akker / weg / hek / poort. Het menu groeit: eerst hut, kippenhok, loods, weg; na een loods molen en akker; na een molen melkerij, hek en poort |
| in de bouwmodus: links indrukken, slepen, loslaten | indrukken toont de ghost onder de wijzer, slepen schuift hem, loslaten plaatst (groen = kan, rood = kan niet of te duur). De ghost is het gebouw zelf (af-glb, doorzichtig getint, zelfde transform als na het bouwen; de kist alleen zolang de glb laadt) met een pijl op de deurtegel naar de deur, ook op touch; test `test/ghost_test.gd`. Weg en hek: slepen legt een rij met een ghost per tegel (grijs = is er al). De modus **blijft aan** na het plaatsen |
| in de bouwmodus: knop Draai, wiel, R | een kwartslag draaien (wiel: omlaag verder, omhoog terug; het wiel zoomt dan niet). Weg en hek draaien niet, daar blijft het wiel zoomen |
| in de bouwmodus: knop Stop, nog eens op de bouwknop, rechts klikken, Esc | bouwmodus uit (rechts slepen draait gewoon de camera) |
| links klikken op een poort | open of dicht: dicht houdt koeien tegen, dorpelingen lopen er altijd door |
| K, N | regen automatisch/aan/uit, volgend seizoen (debug) |
| Tab / I, of het pijltje naast de tellers | details uit/in: tijd, dag, seizoen, weer, voorraden, geluk, selectie, tempo |
| F1, of de knop **? Toetsen** linksonder | sneltoetsuitleg uit/in |

**HUD op de pc** (gebruiker 2026-10-31, te veel tekst): standaard alleen de rij icoon + getal (kas, dorpelingen x/doel,
koeien x/doel, zoals touch) met een pauze-icoon of 2x/4x erachter; details en sneltoetsuitleg staan dicht en klappen uit
met Tab/I en F1. De stand wordt per speler bewaard in `user://hud.cfg` (scenario's niet; `-- --hud=details|hulp|beide` voor frames).

Alles van het bouwen kan met alleen een linkerknop of een vinger (besluit gebruiker 2026-10-30): kiezen, Draai en Stop
zijn knoppen (44 px hoog), plaatsen is indrukken-slepen-loslaten, en de ghost volgt de laatste wijzerpositie uit de invoer
(`Bouwmenu._input`), dus zonder hover. Wiel, rechterklik en toetsen zijn alleen sneltoetsen.

**Touch** (telefoon, of `-- --touch` op de pc; `Bouwmenu.touch`, 2026-10-30 na de Motorola-proef; de pc-besturing hierboven
blijft gelijk): een vinger pant, twee vingers pannen/knijpen/draaien (de kaart draait met de vingers mee). Bouwen: knop =
ghost op de tegel midden in beeld; vinger op de ghost = schuiven (geen pannen), slepen ernaast = pannen, tik ernaast = ghost
daarheen; weg/hek: tik = begin, sleep vanaf begin of eind = dat einde verschuift. Niets staat er voor **Bouwen** (onderin,
naast Draai en Annuleer, >= 110 px / 48 dp, alleen aan als het kan); daarna blijft de modus aan (rij: eind = nieuw begin).
De sneltoetsuitleg onderin is weg. Test `test/touch_bouw_test.gd`. Nog niet: selectie wissen zonder rechterklik, kader.
Touch-HUD (gebruiker 2026-10-30, tekst te klein op de telefoon): geen tekstregels, alleen icoon + getal (kas, dorpelingen
x/doel, koeien x/doel) op >= 16 dp; minikaart, munt-icoon en rolletjes x1,3-1,6; brief en prijzenscherm geschaald tot
>= 16 dp en nooit groter dan het scherm (`Scherm.dp()` = touchknophoogte / 52).

**Staand en liggend** (2026-10-30, `view/scherm.gd`): de telefoon draait mee (`display/window/handheld/orientation=6`,
sensor) en alles legt zich opnieuw neer bij `size_changed`. Staand: bouwknoppen in een lade onderin (knop **Gebouwen**
rechtsboven, een keuze sluit hem), hint en Draai/Bouwen/Annuleer onderin op schermbreedte, camera houdt de breedte vast
(38 graden horizontaal) en staat 1,3x verder en 12 graden steiler. Liggend (en de pc op 1600x900) zoals het was.
Op de pc proberen: `-- --venster=1080x2400` (viewport op die maat, venster geschaald); frames op die maat:
`-- --venster=1080x2400 --opname=out/x.png --opname_frame=30` (`--write-movie` neemt het venster op, niet de viewport),
met `--proef=bouw|lade|prijzen` voor de bouwmodus, de open lade of de prijzen (bouw: `--proef_soort=molen`, `--proef_draai=0..3`, `--proef_rood` = op het kampvuur; frames in `out/ghost/`). `bash test/portret_frames.sh` maakt de set in `out/portret/`.

Lopen kan iedereen; vechten en werken alleen volwassenen (`Wereld.geef_bevel`; vechten = stenen gooien naar een wolf, werken heeft nog geen eigen invoer).

## Structuur

- `data/` `spel.json` (tegelmaat 2 m, 10 Hz, looptempo, klok), `tegels.json` (kleur, loopbaar, snelheidsfactor: pad 1,15, gras 1, zand 0,9; water en rots niet loopbaar), `objecten.json` (klasse-id naar naam, model, voetafdruk, blokkeert).
- `sim/` zonder Node, dus headless te testen: `Wereld` (staat, vaste tik, klok, seizoen, weer, bevelen), `Raster`, `Router` (A* met grondprijs, port van beasts-src `Router.kt`, plus `glad` voor rechte routes), `Dorpeling`, `Vee` (koe: zwerft rond generator of, eigen, rond het kampvuur), `Wolf` (missie 2: zwerven, jagen, koe opeten, stenen gooien), `Plan`, `BouwRij` (rij weg of hek uit een sleepbeweging), `Gegevens`.
  Missie 1 in `Wereld`: kas (`spel.json` `missies.1.start_kas`, `prijzen`, betaald bij `plan_zet`), koe-generator (klasse 171, `missies.1.koe_generator`: start 1, max 3 wilde, elke 45 s; uit `m01.json` p5=1/p6=3, betekenis aangenomen), `geef_claimbevel`, `uitslag` + signaal `missie_einde`.
  Gezin (`Wereld._gezin`, port van beasts-src `family`, waarden in `spel.json` `gezin`): bedden = 2 per afgebouwde hut; `ruimte()` = bedden - iedereen - wiegen - baby's. Een vrije man + vrouw lopen naar de deurtegel (`Plan.deur_tegel`, voordeur aan -x bij draai 0) en verdwijnen naar binnen; 12 s later komt zij met de baby op de arm (5 s), dan staat er een jongen of meisje (hash, geen rng), 150 s later volwassen (glb wisselt). Ouders rusten 75 s. Een bevel van de speler breekt het af. ⚠️ Met 6 startbewoners zijn er 4 hutten nodig voor het eerste kind.
  Graan en brood (`Wereld._economie`, beasts-src-lus, `spel.json` `economie`): molen (= bakkerij, 4x3, deur aan +z, wieken draaien) begint met 8 brood; akker (2x2, 16 kas, 16 s werk, loopbaar) rijpt in 60 s in lente en zomer, rijp sterft bij het begin van de winter. Wie niets omhanden heeft kiest elke 0,5 s een klus: graan naar de dichtste molen, brood kopen na 30 s trek (ook kinderen; 3 kas per brood, 1,2 s aan de toonbank), of (volwassen) een rijpe akkertegel oogsten (2 s, zak op de rug). Een bevel van de speler gaat voor.
  Melk (zelfde lus, `Wereld.WINKELS`): melkerij (4x4, 45 kas, deur aan -x, begint met 8 melk); een volwassene melkt een koe die niet leeg is en binnen `melk_straal` (14) tegels van het kampvuur staat, wild of eigen (besluit gebruiker), 2,2 s, daarna is ze 90 s leeg (beasts-src Herd.again). Trek houdt per waar bij (brood, melk, ei), elk na 30 s.
  Eieren: een afgebouwd kippenhok (`Kip` in `sim/kip.gd`) krijgt `kippen_per_hok` (3) kippen die binnen 3 tegels van de deur scharrelen en pikken; na `kip_leeg_s` (55, beasts-src) legt een kip en blijft zitten; een volwassene raapt (1,6 s) en brengt het ei naar het hok (start 8), bewoners kopen het voor 3. Model: `view/kip_model.gd` (assets/kip.glb, clips idle/lopen/pikken/zitten; zonder glb een placeholder). Het ei ligt achter de zittende kip (`KipModel.zet_ei`, assets/ei.glb x2, origineel `chickegg`), weg na rapen; scenario `ei`.
  Kalveren (`Wereld._kalveren`, hint 1-11, origineel klasse 96 `baby cow`): een eigen koe die in de lente `kalf_samen_s` (20 s) binnen `kalf_straal` (4) tegels van een andere eigen koe staat, kalft met `kalf_kans` (0,5, hash) een keer per lente; het kalf (`Vee.kalf`, verkleinde koe `Koe.zet_kalf` 0,55 -> 1) loopt bij de moeder, wordt niet gemolken en telt pas na `kalf_groei_s` (270) als koe voor het doel (M1.MIS telt klasse 110, cow). Getallen eigen keuze; scenario `kalf`.
  Voorraad op het scherm (`view/voorraad.gd`, beasts-src `HudArt.stock` + `GameView.buying`/`drawSales`): elke winkel krijgt een kraam naast de deur (luifel geel/blauw/rood voor molen/melkerij/kippenhok) met zoveel broden, melkkannen of eieren als `Plan.voorraad`, tot 8 (2 rijen van 4), daarboven een getal. Leeg = lege toonbank met een deinend rood `!`. Een verkoop laat een gouden `+3` met munt 1,6 s boven de kraam opdrijven (vervaagt de laatste 0,5 s, twee stapelen, hoogstens 6), een levering een korte `+1` in de kleur van de waar en het nieuwe stuk springt op. De sim meldt dat met de signalen `Wereld.verkocht`/`geleverd` (in `klus_af`, geen gedragsverandering).
- `view/` `WereldView` spiegelt de sim, `TerreinView` (een mesh met vertexkleur en hoogte, water, MultiMesh-bomen en -rotsen), `Props` (placeholders), `Bumpkin` (geanimeerde man, `volg()`-modus voor de sim), `Licht`, `Regen`, `Bestuur`, `Hud`.
- `shaders/` terrein (vijf texturensets, seizoenstint, sneeuw, nat), natuur_wind (gesynct uit modellen/natuur), natuur_steen (rotsen met sneeuw) en water (diepte, schuim).
- `main.gd` zet alles in elkaar en bevat de scenario's. `test/` simtest, routetijd en glad_test. `screenshots/` verificatieframes.

De sim tikt op 10 Hz los van het renderen; de view interpoleert tussen twee tikken. Looptempo = 0,849 m/s (animatie-sidecar) x `looptempo` 2,0 (spel.json) x tegelfactor. Routes worden recht getrokken (`Router.glad`). De loopanimatie volgt de grondsnelheid via `Bumpkin.gang`: 0 clip exact op tempo (cadans 2x, druk), 1 `SCHREDE` 1,4 (standaard: rustiger, lichte voetglijding), 2 blend naar de rennen-clip (ziet eruit als joggen).
Tijd: een dag-nacht is 270 s (180 dag, 90 nacht), een seizoen is een dag-nacht. Begint in de lente.

## Modellen en natuur

Kaartobjecten gebruiken de glb's uit `modellen/natuur/` (sync.ps1 kopieert ze, de terreintexturen, `natuur_wind.gdshader` en de koe):
`data/objecten.json` kiest per klasse-id `natuur:<glb>` (+ `varianten` met gewichten, `schaal`); `view/natuur.gd` laadt ze, zet de
wind- en steen-shader op de materialen, LOD (`visibility_range`, 28 m) en de seizoenstint; `view/props.gd` maakt de losse objecten en het
kampvuur-effect (GPUParticles3D vlammen en rook op `vuur_bron`, OmniLight3D flikkert in `WereldView`). Bomen zijn gewone instanties
(geen MultiMesh: `visibility_range` werkt niet per MultiMesh-instantie). `decoratie` in objecten.json (rotstegels op rots/rotsrand, struiken,
stronken) is ALLEEN weergave: de sim leest het niet en geen tegel wordt erdoor geblokkeerd. Terrein: `shaders/terrein.gdshader` mengt vijf
texturensets (Texture2DArray, 2,8 m per herhaling) uit de hoekgewichten van `TerreinView._splat()`. De koe (klasse 171) komt uit `view/koe.gd`
(pad, verborgen onderdelen en animatienaam staan alleen daar; nieuwe glb = sync + import). Seizoen: `Natuur.werk_seizoen()` (tint, rotssneeuw) en
`TerreinView.zet_sneeuwlaag()` (winter), aangeroepen vanuit `WereldView.werk_seizoen()`.
Scenario's voor frames: overzicht, kaart, dorp, selectie, pad, loop, vlag, wolf (missie 2: wolf bijt een koe, een man gooit stenen tot hij omvalt), bos, rots, koe, bouw (hut, loods en kippenhok naast het kampvuur, 4x), bouw2 (molen en melkerij, 4x; samen met bouw alle vier de standen, `screenshots/bouwstanden_bouwplaats.jpg`), claim, gezin (4 hutten, het eerste stel), molen (molen + 2 akkers, bijna rijp), melk (melkerij + koe bij het dorp), kippen (kippenhok, eerste ei na 3 s), bouwer (man wordt bouwer bij de loods), hek (weide met poort die opengaat), sleep (een weg en een hek door het bouwmenu gesleept met echte muisinvoer, `test/sleep_scenario.gd`; frame in `screenshots/bouwmenu_sleep_weg_hek.jpg`), nacht (hut + slaapzakken bij het vuur, --uur=20.6), ei (kippen leggen meteen, na 6 s geraapt, `screenshots/ei.jpg`), kalf (drie eigen koeien in de lente, `screenshots/kalf.jpg`), stapels (vijf bouwplaatsen in vier draaiingen, zaagbok en steenhoop aan de deurkant, `screenshots/stapels.jpg`), zagen en houweel (hut, de volwassenen bouwen, de camera volgt wie zaagt of hakt, `screenshots/zagen.jpg`, `screenshots/houweel.jpg`), bouwploeg (hut, zes bouwers op eigen plekken). De oude blokjes-placeholders in `props.gd` zijn alleen nog terugval als een glb ontbreekt.
Uiterlijk per dorpeling: `Bumpkin.glb_voor(geslacht, leeftijd)` kiest een van de zes glb's (man, vrouw, jongen, meisje, oudere man/vrouw; kinderen zijn al 1,11 m in de glb). `sex` 13 = jongen, 14 = meisje is een aanname (niet geverifieerd). Ontbreekt een glb: de man (kind op 0,81x).
Bouwplaats: hut, loods, kippenhok, molen en melkerij tonen `<glb>_stand1..3.glb` (`Plan.stand()`, op exact de transform van de af-glb; ontbreekt er een, dan de kist), zaagbok en steenhoop ernaast (tegels uit de sim: `Wereld.stapel_plekken` bij `plan_zet`, `Plan.stapels`) slinken tot 35 % met de voortgang (zonder zaagbok de houtstapel). **Werkplekken** (2026-10-31, gebruiker: niet op dezelfde plek, zagen bij de stam, hakken bij de stenen): `Wereld.werk_plekken` geeft elke bouwer een eigen plek (`Dorpeling.werk_punt/werk_soort/werk_kijk`, geen rng): eerst een hamerplek aan de gevel, dan zagen aan de stam op de zaagbok, dan hakken met de houweel in de steenhoop, dan de overige hamerplekken op de rand rond de voetafdruk (telkens de verste van wat al gekozen is); de view speelt die clip en kijkt naar `werk_kijk`, zonder wissel. Origineel: sprites `saw` (zaagbok met zager), `pick` (steenhoop met hakker) en `hammer` (8 richtingen), klassen 114-116 rockpile/woodpile/hammer point. Akker, hek, poort, weg: de tegels van de voetafdruk, dan de rand. Test `test/bouw_plek_test.gd`, scenario `bouwploeg` (`--stap=0..2`: overzicht, zaagbok, steenhoop); akker, weg, hek en poort: kist zonder stapels. De glb's laden een keer in de achtergrond zodra er een plan staat; de stand-materialen worden op naam die van de af-glb (texturen van alle 5 x 4 glb's 1594 -> 624 MB, gemeten 2026-10-30); bouwmenu: hut (B), gereedschapsloods (L, 5x2), kippenhok (H, 2x2), weg (T, 1x1) en de rest (zie Besturing), `Bouwmenu.GEBOUWEN` + `Wereld.BOUWSOORTEN`; glb's op ware grootte, een mensendeur schaalt. Hut klaar = `peasant_hut_rt.glb`, geschaald op de voordeur: 1,15x de langste volwassene (1,37 m) = 1,58 m, dat is de glb op ware grootte; voetafdruk dus 4x4 tegels (7,6 x 7,1 m incl. hek). Die glb (25 MB) staat niet in git: `blender -b -P ../modellen/peasant_hut_realtime.py`, anders blijft het een bruine kist.
Hoogte (rotsboog, strand) is alleen weergave; de sim is plat.
