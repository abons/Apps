# Gameplay Beasts & Bumpkins-remake (3D, Godot 4.7)

Stand 2026-10-29. Werkcontext, geen leesstof. Bronnen: `beasts-src` (Kotlin, Android; **niet gewijzigd**), `onderzoek.md`, `concept/lijst.md`, `bb_original/objects_list.txt` (scratchpad, lokaal), BBTools-share (alleen `README.md` + `additions/*.cpp` bekeken).

Markering: **[V]** = in de code van beasts-src nagelopen (`bestand:regel`, alle in `E:/werk/androidApps/beasts-src/app/src/main/java/com/hrbons/beasts/`, hieronder afgekort tot `World.kt:123`). **[O]** = alleen uit `onderzoek.md` (niet geverifieerd, zoekmachine-extracten). **[?]** = onbekend, niet te vinden.

⚠️ **Wat dit document eerlijk zegt over de bronnen:** `onderzoek.md` is bijna alleen toolchain en assets; de spelregels van het origineel zijn er maar op ~10 regels in beschreven, **zonder getallen** behalve objectgezondheid. De share (`BBTools/additions/Objects__Handler.cpp`) is animatiecode: ik vond er **geen** schade-, honger- of snelheidsconstanten in (grep op food/hunger/damage/morale leverde alleen animatieframes). Alle speelgetallen in §3 komen dus uit beasts-src, en die zijn daar **eerste gokken van de AI-sessies, geen origineel** (zo staat het ook in de kdoc: "een gok van mij").

⚠️ **beasts-src is geen kopie van het origineel maar een eigen spel "in de geest van"**: winkel-economie (bewoners kopen, kas groeit), geen honger/ouderdom/gilden/spreuken/belasting. Poorten we alleen beasts-src, dan bouwen we dát spel in 3D.

---

## 1. Kernlus (beasts-src, geverifieerd)

1. Start: 2–8 volwassenen, 1–2 hutten, kas 70–200 munten, kaart 32–56 vakken breed (`Level.kt:228`).
2. Speler **bestelt** (hut, winkel, akker, weide, weg) uit de kas; een bouwplaats ontstaat, tot 4 dorpelingen bouwen hem in 4 standen (`Plan.kt`, `Site.WORKERS`, `Building.STAGES`).
3. Dorpelingen kiezen **zelf** klussen (prioriteitslijst `chooses`, `World.kt:4428`): verdedigen, schat graven, bouwen, paren, kopen, oogsten/melken/scheren/eieren rapen, vee halen, hout/steen halen. De speler kiest één man en geeft hem bevelen (tik).
4. Winkel krijgt voorraad (graan, melk, wol, eieren) → bewoner heeft een behoefte (30 s per soort) → loopt naar de toonbank → **3 munten** in de kas (`visit`, `World.kt:2224`). Kas betaalt nieuwe panden.
5. Een stel in een hut met vrije bedden krijgt na 12 s een baby; kind groeit 150 s tot volwassene (`family`, `World.kt:3658`). Meer huizen = meer bedden = meer volk.
6. Buiten komen beesten (rat, kraai, wolf, zwijn, lynx, beer) van de rand of uit holen; ze stelen voorraad/gewas, bijten mensen en slopen gebouwen. Dorpelingen vechten blootshands (4 schade per 0,8 s) of met speer (6, na wapenhut).
7. **Winnen** (`World.progress`, `World.kt:1050`): inwoners ≥ N · kas ≥ N munten · schat opgegraven · N beesten verslagen · alle holen gesloopt · tegenstanderdorp leeg. **Verliezen**: 0 eigen inwoners (`World.lost`, `World.kt:1081`). Dag/nacht (270 s) en seizoen elke dag-nacht; groei stopt in herfst, rijpe akkers sterven in winter.

---

## 2. Systemen

| Systeem | Origineel (onderzoek) | beasts-src (met `bestand:regel` en getallen) | Gaten / verschillen | 3D-opmerking |
| --- | --- | --- | --- | --- |
| **Behoeften** (eten, slaap, geluk) | Honger, water, geluk, fitheid + slaap 's nachts; denkwolk toont staat; priester "bless" herstelt alles; slachten geeft eten/water/geluk [O] | **Alleen "behoefte om te kopen"**: `Villager.need[goods]` (`World.kt:151`) loopt per soort op met `dt`, toe bij `NEED_EVERY`=30 s (`:6140`, `crave :4496`); kopen zet hem terug. Geen honger, water of geluk; niemand sterft door gebrek. Slaap: alleen volwassenen 's nachts in een hut, `sleep :4025`, `wake :4065`; geen bed = blijft staan | Origineel heeft 4 behoeften met gevolgen; hier 1 die geld oplevert. Geen denkwolk-UI | Logica 1:1 portabel. Denkwolk/icoon boven het hoofd is billboard-sprite: goedkoop, leest vanaf elke camerahoek |
| **Veroudering, geboorte, huwelijk, dood** | Baby → kind → volwassene → oud → dood; volwassene leeft ~4–5 spel-jaar afhankelijk van eten/water; man+vrouw in hut → baby; bruid/bruidegom en "attend wedding" bestaan; plaag onder ouderen [O] | **Geboorte + opgroeien, geen ouderdom.** `goPair :3847`: willige man+vrouw (`rest`=0), plek vrij (`roomToGrowOf :3650` = bedden − inwoners − wiegen − baby's), samen naar dichtste hut → `Cradle` (`:585`), na `WOMB`=12 s komt zij naar buiten met baby (`birth :3777`, `BABY_SHOW`=5 s), kind `GROW_UP`=150 s (`age :3693`), daarna `PARENT_REST`=75 s geen nieuw kind. Man/vrouw 50/50 via hash (`born :3798`). Dood alleen door gevecht (`fell :3056`) | **Geen ouderen, geen huwelijk, geen plaag, geen natuurlijke dood.** Onze assets hebben wel oudere man/vrouw (concept 4,5) en bruid/bruidegom (8) | Bumpkin-rig voor kind (0,81x) en oudere (0,96x, stok) bestaat als schaal/variant [lijst.md]. Ouder worden = nieuwe tijdsteller + status; ruim 1:1 |
| **Banen en jobkiezer** | 33 unit-types, 11 dorpelingsrollen; vrouwen werken op de boerderij (melken, tarwe, appels), mannen bouwen/repareren en zijn enige gildeleden; automatische jobkiezer doet tarwe/appels/melken (`action_catalog.json`, **niet lokaal**) [O] | **Geen vaste rollen; iedereen volwassene kan alles** (geen man/vrouw-verschil in `chooses`). `chooses :4428`: kind → spelen/kopen/slenteren; volwassene → `goGuard :3458` > `goDig :3544` > `goBuild :5053` > `goPair :3847` > `goShopping :5285` > `goProduce :4663` > `goFetch :4842` > `wander`. Elke tak bouwt een lijst `Try(afstand, doel){…}` en `attempt :4633` probeert de dichtstbijzijnde die lukt (A\*-bereikbaarheid vooraf gezeefd). `goProduce` kiest wat het **naast** is over akker/koe/schaap/kip/hout/steen. Wachttijd tussen klussen `ERRAND_WAIT`=4 s (`:6124`). Bevel (`bidden`) heeft voorrang | Rolverdeling (man bouwt, vrouw melkt) en bouwersrol ontbreken; appels/cider/brood ontbreken (alleen "gewas"). Beslissing nodig: zie Open vragen 3 | **Engine-onafhankelijk, 1:1 porten** (bijna regel voor regel). Enige 3D-wijziging: afstanden in meters i.p.v. vakken |
| **Grondstoffen en productieketens** | Tarwe → bakkerij → brood; appels → brouwerij → cider; melk; kip → eieren; hout/steen (rockpile/woodpile objecten); goud/belasting door belastinginner, tiende door priester [O] | `Goods` = CROP, MILK, WOOL, EGGS, WOOD, STONE (`Grid.kt:293`). Ketens zijn **één schakel**: produceren (akker `Grid.RIPEN` 60 s, koe/schaap/kip `Herd.again`) → dragen (`carrying`, `deliver :5245`) → winkelvoorraad `Building.stock` (start leeg, `restock :2246`) → `visit` = 3 munten. Hout/steen: rotsvak `Grid.GATHER` 60 s (`gather :4529`), geleverd aan wapenhut (cap 20/20). Winkels: SHOP→CROP, DAIRY→MILK, CLOTHIER→WOOL, HENHOUSE→EGGS (`Grid.kt:356`) | Geen bewerking (graan → brood), geen appel/cider, geen belasting, geen wol → kleding ("geen bewerking, laat staan", design 2026-09-01). `⚠️` Voorraad op 0 bij opening is een bewuste regel (`ProduceTest.noBuildingPaysForItselfOnItsOpeningStock`): 8×3 < 40 | Onze molen = SHOP(CROP) (graan→brood als puur visuele/naam-laag of echte stap, vraag 1), melkerij = DAIRY, kippenhok = HENHOUSE, gereedschapsloods = WAPENHUT-achtig/bouwersopslag. Dragen: Bumpkin heeft `m_sack`-pose in 2D-assets maar **geen** draaganimatie in de 3D-set (6 animaties: idle, lopen, rennen, bouwen, zwaard, steen) |
| **Bouwen en repareren** | 21 speler-gebouwen, elk eigen bouwplaats-klasse; ontgrendelingsvolgorde (boerderij vereist bakkerij) [O]; mannen bouwen/repareren; bouwersgilde bestaat | Bestellen via `Proposal` (anker+cursor, `Plan.Shape` SPOT/RECT/LINE) → `commit :2133` rekent prijs af → `raise :2142` zet `Building(stage=0)` + eventueel weg-`Job`s; `Site` met `Job` per vak; `Job.work` loopt op per werker; `Site.WORKERS`=4 (`Plan.kt`); 4 zichtbare standen; werk/vak = 60 s per gebouw, 3–4 s per grondvak. Prijs wordt bij bestellen betaald. Regels: gebouw ≥ `Grid.SPACING`=4 vakken van een ander, deur naar de camera (`Iso.FACING_CAMERA`), weg naar de deur wordt mee-bestelde `Job`s (`World.aim :1894`). **Geen reparatie**: gebouw heeft `Building.HP`=40 en valt om (`wreck :3028`) | Reparatie ontbreekt; ontgrendeling ontbreekt (alles direct in menu); geen upgrade (origineel ook niet [O]) | Plaatsing met raycast op grondvlak; 4 deurrichtingen i.p.v. alleen camera-gericht (vrije camera). Bouwstanden: 4 stappen = scaffold/ruwbouw-reveal in shader of 4 meshes (open voor asset) |
| **Gilden en training** | 5 gilden (voetsoldaat, boogschutter, ridder, tovenaar, minstreel) + bouwers; kost goud per leerling; ~6 voetsoldaten per gilde; alleen mannen [O]; paladijn bestaat **niet** (lijst.md) | **Eén "gilde": wapenhut** (`Plan.WAPENHUT` 50 munten). `enlist :2265`: gekozen dorpeling → speer-eenheid voor `SPEAR_PRICE`=30 munten + 10 hout + 10 steen uit de hut; blijvend (`spearman`). Schade 6, bereik 2,1 | Geen boogschutters/ridders/tovenaars/minstrels/priesters ("Later", `docs/open/later.md`); geen limiet per gilde | Gilde-eenheden hebben concept art nodig (lijst.md rij 11–25), modellen ontbreken; de speer vraagt een eigen wapen-prop op de gedeelde rig |
| **Gevecht** | Licht, kleine schermutselingen; peasants **gooien stenen** (`mthrow`/`m_throw` sprites, 5 frames); eenheden vluchten (flee-sprites) [O]; voetvolk, boogschutters, ridders, cavalerie, belegering [O] | Melee only. `fight :3087`: dorpeling loopt naar `quarry`, slaat elke `HIT_CYCLE`=0,8 s voor `HIT_DAMAGE`=4 (speer 6) binnen `HIT_REACH`=1,6 (speer 2,1); `VILLAGER_HP`=24. Achtervolging herberekent route elke `CHASE_WAIT`=0,35 s. Stilgezette man slaat toe bij vijand binnen `TRAP_RANGE`=3 (laat los >4,5). **Kinderen vluchten** (`flee :3952`, schrikken binnen 6, 4 verder rennen). Volwassenen vluchten niet; geen moreel; geen afstandswapen | Steengooi, boogschutters, vluchten van volwassenen, moreel, vallen/artefacten ontbreken. `⚠️` Verhouding is de keuze: 1 dorpeling wint van rat; verliest van beer (22 hp, 12 per 1,3 s); beer vergt 2 man | **Steengooi bestaat al in 3D** (`gooi_steen`, signal `impact('steen')`). Dus melee én ranged zijn visueel klaar. Raakschade in 3D: afstand in meters + impacttijd uit `bumpkin_anim.json` (zwaard 0,4167 s van 1,0 s; steen 0,5 s van 1,1 s) |
| **Vijanden en spawnen** | 10 wezens: zombie, wolf, donkere wolf, wesp, bloedwesp, vleermuis, vampier, demon, reus, ogre (+struikman); zombietomb en ei als spawner; wolf eet baby's; mission-scripts bepalen golven [O] | 11 `Beast.Kind` (`Beast.kt:289`), geen zombie/baby-eter: rat→voorraad, kraai/zwijn→gewas, beer→gebouw, wolf→**koe**, wesp/vleermuis/spin/adder/tijger/lynx→dorpeling. Toestandsmachine ROAM→HUNT→ATTACK→DYING→DEAD (`Beast.advance`). Spawn: `Level.menace` NONE/LIGHT(45 s, max 3: rat+kraai)/HEAVY(28 s, max 5: +wolf/zwijn/lynx/beer) vanaf een willekeurige randvak (`raid :2573`, `edge :2648`); **hol** (`Den` 400 hp, elke 22 s, eerste 8 s, max 2 extra) en **vijandig kamp** `Camp` (140 hp, elke 90 s, 2 `Marauder`s, max 4) (`World.kt:6436`, `:6462`) | Geen zombies, geen wolf-eet-baby. Wesp, vleermuis, spin, adder en tijger bestaan als `Kind` maar staan in **geen** `Menace`-lijst (alleen in de wegwerp-`DRILL`, `Level.kt:67–110`), dus geen level gebruikt ze. Geen scriptmotor | Eenvoudig: wolf/zombie = `Beast.Kind`-rijen in `beasts.json`; zombie heeft concept (27) maar **nog geen rig**. Wolf (26) idem. Vliegende types vragen hoogte (3D: Y gratis) |
| **Dieren** (koe, kip, eigendom) | Koeien in omheinde velden gelokt om te melken, kalven, slachten; kippen leggen eieren → kuikens; slachten; varken alleen in boerderij-anim [O] | `Animal` (`World.kt:453`) in `Herd` CATTLE/SHEEP/HENS (`Grid.kt:45`). Start: 2 kuddes van 3/4/5 dieren los op gras. **"Eigendom" = hek**: dier geeft alleen melk/wol/eieren in zijn eigen hek (`Pen`) óf binnen `STORE_RANGE`=20 vakken van een verkopend gebouw (`tendable :4975`, 2026-09-28). Brengen: dorpeling leidt dier (`lead :4544`, `LEAD_GAP` 0,9, `LEAD_PACE` 1,5) naar vrij hek, loslaten `loose :1750`. Los dier loopt zelf (`stir`: koe 11 s, schaap 8 s, kip 3,5 s; `ROAM_PACE`=0,4, `GRAZE_RANGE`=2). Gewonnen: leeg `again` 90/75/55 s, klus `work` 2,2/2,6/1,6 s. Dorpeling gaat uit zichzelf een dier halen binnen `HOMELY`=9 van zijn dorp | **Geen belletje, geen eigendomsstatus, geen kalf/kuiken/slacht/varken.** `Animal.led`/`settle` is het dichtstbijzijnde. Wolf pakt koe: `bite :2998` verwijdert het dier | Koebel = visuele marker voor "in het dorp opgenomen". Voorstel: `Animal.eigen` (bool) gezet bij `loose` in eigen hek of binnen `STORE_RANGE` van DAIRY; bel = prop op de nek. Zie vraag 5. Koe/kip-rigs bestaan niet (quadruped); concept wel |
| **Seizoenen en weer** | 4 seizoenen; tarwe lente → herfst; winter: sneeuw, oogst sterft; sneeuwhek-sprite; regen- en onweerswolk-sprites [O] | `Season` SPRING→SUMMER→AUTUMN→WINTER, **een seizoen = één volledige dag-nacht** (270 s), `World.tick :2331`. Groei alleen lente+zomer (`Grid.ripen`, `:2343`), op winter-start sterft rijp gewas (`Grid.wither`, `:886`). Visuele tint (`GameView.seasonTint`). **Geen weer.** Seizoen staat in `snapshot` | Geen regen/onweer/bliksem; geen sneeuwe obstakels | Demo heeft al zomer/winter-schakelaar (F): korte dag, lage zon, dor gras, altijd rook (`godot3d/README.md`). Koppelen aan `Sim.season` is triviaal. Regen = deeltjes + natte shader |
| **Dag/nacht** | Cyclus aanwezig; slaap wordt "gewist bij einde nacht" [O] | `clock` loopt van 0 tot `DAY_LEN`+`NIGHT_LEN` = 180+90 s (`World.kt:6096`); `isNight` = `clock ≥ DAY_LEN` (`:1115`). Slapen in hut (max `beds`=2), `wake()` stuurt ze naar buiten. Deurgloed/licht vloeien bij (`GLOW_SPEED`=2, `DOOR_SPEED`=3,5) | Dag-lengte per seizoen is constant (demo-winter is korter) | Demo heeft `DAG_SECONDEN`=60 voor 24 u (`main.gd:10,710`). **Koppel via mapping** sim-klok → uur (bv. 6–18 u over 180 s, 18–6 u over 90 s). Kaars/rook/raam-gloed al klaar op hut |
| **Spreuken en priesters** | Tovenaar 7 spreuken (vuurbal, bliksem, zien, teleport, zombie oproepen, angst, vallen detecteren); priester 7 (massa-genezen, doof vuur, bescherm, snel eten, plaag, genees plaag, zegen); spreuken via scrolls; priester begraaft, collecteert tiende [O] | **Niet aanwezig** (grep priest/spell/plague: geen). Alleen een zombie-opmerking in kdoc | Volledig gat. Slechts 9 `s_*` spreuksprites tegen 14 spreuken (lijst.md) | Spreukeffecten zijn vrijwel allemaal deeltjes+licht in 3D: goed realiseerbaar; pas ná slice |
| **Missies en doelen** | 30 missies met scripts; doelen: item halen (Graal met sleutel, boobytrap), vijand/dorp doden, goud verdienen, overleven; sommige missies starten met dorp en golven; BBTools heeft graaf-editor [O]. Verhaal: Lord Mildew vs Dark Lord Sabellian [O] | `Quest` (`Level.kt:20`): PEOPLE, COINS, TREASURE, BEASTS, DENS, RIVAL. 22 levels (`Level.ALL :228`), per level: seed, kaartmaat 32–56, kas, aantal man, quest+target, `Land` (rijkdom: `OPEN/RICH/PLAIN/LEAN/BARE`), `Menace`, `camps`, `starterRoad`. Schat (`Treasure`): 120 munten, `DIG_WORK` 16 s, zichtbaar binnen `HOARD_SIGHT`=2,5 vakken (`:1295`, `:6506`). Level 22: `Rival` = bot op dezelfde API (`Rival.kt`, verlies bij 0 man). Verhaalbord per level (`strings.xml story_N`) | Geen scriptmotor/triggers, geen items/sleutel, geen "overleef tijd", geen Lord Mildew-verhaal (beasts-src heeft eigen verhaal). Geen `Quest.SURVIVE` | Missiedata → `levels.json`; quest-types 1:1. Voor het origineel-scripting: eigen kleine trigger-DSL later |
| **UI en besturing** | 640×480 (patch: 1280×720); portretten (18 `statbust`), bouw-/spreukpictogrammen, 8 commando-cursors, denkwolken [O] [lijst.md] | Eén vinger: tik man = selecteren + camera volgt (`GameView.tap :786`); tik op grond = lopen; op rijp vak = oogsten; op dier = melken of leiden; op vijand = aanvallen; op bouwplaats = helpen; op wapenhut = enlist (`:859–971`). Slepen = camera, knijpen = zoom (0,23–2×). Menu: bouw/grond-rij (`MenuArt`), stilzet-knop (stil = valt aan binnen 3 vakken), deselecteer, bouw-ghost met greep MOVE/SIZE. Tekstbord: kas, bevolking X/N, doel, tijd. Icoon boven het bevel (`Sign`). Stemfragmenten (`Voice`, 56 bestanden: man/vrouw/jongen/meisje) | Geen groepsselectie (1 man tegelijk), geen pauze/snelheid **[?]** niet nagelopen. Touch-only | PC-eerst: klik-selecteer, rechtsklik-bevel, drag-box voor groepen, WASD/rand-pannen (`rts_camera.gd` al klaar). Selecteren via raycast op capsule; `PICK_RANGE`=0,9 vak. Bevel-icoon boven doel als billboard |

---

## 3. Data en getallen

⚠️ Eenheid is **vakken** (1 vak = 1 gridcel, 96×48 px in beasts-src, zie vraag 7 voor meters) en **seconden spel-tijd**, tenzij anders gezegd. Bron per rij; alles **[V]** tenzij gemarkeerd. Alle zijn "eerste gok", behalve de ⚠️ verhoudingen.

### 3a. Tijd, beweging, kaart

| Getal | Waarde | Bron |
| --- | --- | --- |
| Simulatietik | 1/60 s | `World.TICK`, `World.kt:6086` |
| Looptempo gras | 2,2 vak/s; weg `cost` 6, gras 10, zand 16, akker 22, furrow 18, weide 12, kippenren 14 (tempo = SPEED·10/cost) | `World.SPEED :6080`, `speedOn :5540`, `Grid.kt:141–230` |
| Looptempo per man (Look.pace) | ≈1 gemiddeld, varieert per look | `Villager.pace`, `Look` (`Bumpkin.kt:100`) |
| Looppas (cyclus) | 1,35 vak per 2 stappen | `World.CYCLE :6083` |
| Pathfinding | A\*, 8 richtingen, diagonaal ×1,41, rand-regel `canStep` (hek), `Router.reachable` | `Router.kt:18–90` |
| Kaartmaten | 32–56 vakken, vierkant; basis 48 | `Level.kt:228–` |
| Dag / nacht | 180 s / 90 s; seizoen elke dag-nacht (270 s, jaar 18 min) | `World.kt:6096` |
| Deur opent binnen | 1,6 vak; poort 1,4 → 0,35; deurtempo 3,5/s, gloed 2/s | `:6100–6113` |
| Level-duur (bot) | tientallen min: level 11 100 munten in **2556 s (43 min)**, levelmarge één derde onder `PlayTest.minutes` | `Level.kt:345` (kdoc) |

### 3b. Economie en bouwen

| Getal | Waarde | Bron |
| --- | --- | --- |
| Beginkas | 120 (level 1), 50–200 per level | `World.PURSE :6617`, `Level.ALL` |
| Prijs / werk per vak | Hut 40/60 s · Groenteboer(SHOP) 40/60 · Melkerij 45/60 · Kledingmaker 45/60 · Kippenhok 40/60 · Wapenhut 50/60 · Akker 4/4 s · Weide 5/4 · Schapenweide 5/4 · Kippenren 4/3 · Weg 2/3 | `Plan.kt` (enum-rijen) |
| Werkers per bouwplaats | 4 (werk loopt ×4 sneller) | `Site.WORKERS` |
| Bouwstanden / gebouw-hp | 4 stappen / 40 hp | `Grid.kt:550,557` |
| Bezoekprijs / winkelvoorraad | 3 munten per bezoek · 8 per gebouw (start 0, na `finish`) | `World.VISIT_PRICE :6618`, `Kind.stock` |
| Behoefte | 30 s per goederensoort | `World.NEED_EVERY :6140` |
| Toonbankwacht / oogstklus / hakklus | 1,2 s / 1,2 s / 1,2 s | `COUNTER_WAIT`, `REAP_WAIT`, `GATHER_WAIT` |
| Akker herstel / rots herstel | 60 s / 60 s | `Grid.RIPEN :1198`, `Grid.GATHER :1207` |
| Bedden | Hut 2, rest 0 | `Building.Kind.HUT` (`Grid.kt:366`) |
| Wapenhut | hout/steen-cap 20/20; speer = 30 munten + 10 hout + 10 steen | `Grid.kt:409`, `World.kt:6627` |
| Schat | 120 munten, graafwerk 16 s door één man | `TREASURE_PRIZE`, `DIG_WORK :6506` |
| Generator | 7 hutten max, 7 vijvers, 10 rotsen, 6 akkers (2–4), 3 weiden (3–5), 2 schapenwei, 2 kippenren, `SPACING` 4 | `Grid.kt:1120–1187` |

### 3c. Bevolking en vee

| Getal | Waarde | Bron |
| --- | --- | --- |
| Baby-wachttijd / toont / volwassen / ouderrust | 12 s / 5 s / 150 s / 75 s | `WOMB`, `BABY_SHOW`, `GROW_UP`, `PARENT_REST` (`World.kt:6532–6547`) |
| Kind: speelafstand, kijktijd, vlucht | 7 vak, 2,5 s; schrikt <6, ≥6 ruimte, wint ≥4 | `PLAY_RANGE`, `PLAY_WAIT`, `FLEE_FEAR`, `FLEE_ROOM`, `FLEE_GAIN` |
| Thuis-afstand | 9 vak (uit zichzelf dier halen, kind blijft binnen) | `HOMELY :6254` |
| Winkelbereik los dier | 20 vak | `STORE_RANGE :6198` |

| Vee (`Herd`, `Grid.kt:45`) | Koe | Schaap | Kip |
| --- | ---: | ---: | ---: |
| leeg na leveren (`again`) | 90 s | 75 s | 55 s |
| klus (`work`) | 2,2 s | 2,6 s | 1,6 s |
| kudden × grootte | 2×3 | 2×4 | 2×5 |
| kans per vak in hek (‰) | 430 | 520 | 340 |
| neemt 2 vakken (`wide`) | ja | ja | nee |
| eigen stap (`stir`) / cyclus | 11 s / 0,9 | 8 s / 0,72 | 3,5 s / 0,45 |

Leiden: `LEAD_GAP`=0,9, `LEAD_PACE`=1,5×, `LEAD_REACH`=1,4; melkreik `TEND_REACH`=1,4; `ROAM_PACE`=0,4×; `GRAZE_RANGE`=2 (`World.kt:6177–6244`).

### 3d. Gevecht

| Getal | Waarde | Bron |
| --- | --- | --- |
| Dorpeling hp / schade / cyclus / bereik | 24 / 4 / 0,8 s (=5 per s) / 1,6 (ondergrens 1,5811 berekend) | `World.kt:6295–6298` |
| Speer | schade 6, bereik 2,1 | `SPEAR_*` |
| Val (stilgezet) | binnen 3, laat los 4,5, kijkt elke 0,5 s | `TRAP_*` |
| Marauder (vijandige dorpeling) | hp 20, schade 4 per 0,9 s, bereik 1,2, zicht 7, tempo 1 | `MARAUDER_*`, `:6407–6412` |
| Hol | 400 hp, elke 22 s (eerste 8 s), max 2 extra tegelijk; kandidaat 9‰, ≥15 van dorp | `DEN_*`, `:6436–6490` |
| Kamp | 140 hp, elke 90 s (eerste 60 s), groepje 2, max 4; ≥22 van dorp | `CAMP_*`, `:6462–6469` |
| Schat zoeken | zicht 2,5, ≥14 van dorp, 12‰ | `HOARD_*` |

| Beest (`Beast.kt:289–299`) | pace | zicht | bereik | hp | schade | slag (s) | doelwit |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| Wolf | 1,6 | 7 | 0,9 | 8 | 5 | 0,9 | koe |
| Wesp (vliegt) | 1,5 | 2,5 | 0,5 | 2 | 2 | 0,6 | dorpeling |
| Vleermuis (vliegt) | 1,8 | 5 | 0,6 | 3 | 2 | 0,5 | dorpeling |
| Rat | 1,2 | 6 | 1,1 | 2 | 1 | 0,7 | winkelvoorraad |
| Spin | 0,9 | 2 | 0,6 | 5 | 4 | 0,8 | dorpeling |
| Zwijn | 1,4 | 4 | 1,0 | 12 | 7 | 1,1 | gewas |
| Beer | 0,75 | 5 | 1,1 | 22 | 12 | 1,3 | gebouw |
| Adder | 0,5 | 1,5 | 0,8 | 4 | 6 | 0,7 | dorpeling |
| Kraai (vliegt) | 1,7 | 4 | 0,5 | 3 | 1 | 0,6 | gewas |
| Tijger | 1,5 | 8 | 1,1 | 16 | 9 | 1,0 | dorpeling |
| Lynx | 1,65 | 6 | 1,0 | 11 | 7 | 0,85 | dorpeling |

Slaan landt op `STRIKE_AT`=0,42 van de slagcyclus; verliest spoor op zicht×1,4 (`Beast.kt` companion). `Menace`: LIGHT 45 s/max 3 (rat, kraai); HEAVY 28 s/max 5 (+wolf, zwijn, lynx, beer) (`Level.kt:67`).

### 3e. Levelladder (eerste 12 van 22, `Level.kt:228–577`)

| # | kaart | kas | man | doel | `Menace` |
| --- | ---: | ---: | ---: | --- | --- |
| 1 | 48 | 120 | 4 | 8 inwoners (2 hutten, open dorp) | geen |
| 2 | 48 | 120 | 4 | 200 munten | geen |
| 3 | 40 | 200 | 4 | 14 inwoners | geen |
| 4 | 48 | 100 | 4 | schat | geen |
| 5 | 40 | 90 | 3 | 120 munten | geen |
| 6 | 40 | 120 | 4 | 3 beesten | LIGHT |
| 7 | 40 | 80 | 3 | 20 inwoners | LIGHT |
| 8 | 48 | 80 | 3 | schat | LIGHT |
| 9 | 40 | 100 | 4 | 8 beesten | HEAVY |
| 10 | 40 | 90 | 3 | 1 hol | HEAVY |
| 11 | 36 | 70 | 2 | 100 munten | LIGHT |
| 12 | 44 | 100 | 5 | 2 holen | HEAVY |

13–22 zelfde vormen (schat, 8–24 inwoners, 12 beesten, 3 holen); 20 = lege kaart met 5 vak startweg; 21 = 56 vak, kas 180, 8 man, 230 munten + 1 kamp; 22 = tegenstanderdorp (`Quest.RIVAL`, kas 180, 6 man).

### 3f. Origineel (uit `objects_list.txt` en onderzoek, **geen balans**)

| Gegeven | Waarde | Bron |
| --- | --- | --- |
| Gezondheid objecten | kerk 1200 · stadhuis 800 · bakkerij 800 · brouwerij 700 · boerderij 600 · gilden 800 · gevangenis 800 · kampvuur 800 · put 500 · hut 400 · stal 400 · tempel 400 · wachttoren 400 · uitkijkpost 400 · hek/stenen muur/poort 200 · koe 80 · kip 30 · dorpeling 200 · boom 110–130 · tarwe 30 · appelboom 120/30 · val 400 | `bb_original/objects_list.txt` (schaal onbekend; vermoedelijk andere basis dan beasts-src: hut 400 vs 40) |
| Lengte man / kind / oudere | 26 px = ~1,37 m / 0,81× / 0,96× | `lijst.md` |
| Reus / ogre | ~1,35× / ~1,8× (met staf) | `lijst.md` |
| Tegel | 78×40 px diamant (MAPViewer) | `onderzoek.md` [O] |
| Richtingen/frames | 8 richtingen; loop 6 frames, aanval 4–7; frame schakelt elke 4e tik (`(frame+1) % (4·n)`, indruk uit `Objects__Handler.cpp`, niet beproefd) | `onderzoek.md`, share |
| Aantallen | 33 unit-types, 21 speler-gebouwen + 8–10 missie-gebouwen, 14 spreuken, 30 missies, 15 artefacten, 6 vallen | `onderzoek.md` [O] |
| Levensduur / gildecap | ~4–5 spel-jaar; ~6 voetsoldaten per gilde | `onderzoek.md` [O, medium] |
| Cavalerist | paard en ruiter zijn één model | `lijst.md` |

Onbekend **[?]**: looptempo, schade, honger-/slaapsnelheid, kosten van gilden, kas van het origineel, spreukkosten.

---

## 4. Architectuur-advies voor Godot

### 4a. Wat 1:1 porteerbaar is (zuiver data + logica, geen engine in de Kotlin)

Laagindeling van beasts-src (`CLAUDE.md`): `Iso.kt` kent alleen de schermtransform (89 r, **niet** porteren), `Grid`/`Router`/`World` kennen tegels en geen schermpixels, `GameView` kent de camera en rekent geen regels. De drie middelste zijn dus de portbare kern:

| beasts-src | Doel in GDScript | Opmerking |
| --- | --- | --- |
| `World.kt` tick, `chooses`/`attempt`, `errands`, `labour`, `family`, `age`, `fight`, `raid`/`prowl`, `crave`, `visit`/`restock`, `sleep`/`wake`, `commit`/`raise`/`finish`, `Quest`/`progress`/`lost` | `sim/sim.gd` (+ opsplitsen: `sim/jobs.gd`, `sim/family.gd`, `sim/combat.gd`) | 6674 regels, waarvan ~1000 kdoc; kern ~3000 regels logica. Gebruik de `.claude-index` + bereiken, geen volledige leesbeurt |
| `Grid.kt` (grond, `canStep`-randregel, gewasrijpheid, `Herd`, `Goods`, `Building.Kind`) | `sim/grid.gd` + `data/*.json` | Randregel voor hekken blijft; in 3D wordt dit een logisch rooster onder de wereld |
| `Router.kt` (A\* 8-richtings, cost, `reachable`) | `sim/router.gd` of Godot `AStarGrid2D` | AStarGrid2D heeft diagonaal-modi en gewichten; randregel (hekken) eist eigen blokkering. **Reachability-zeef voor `attempt` blijft nodig** |
| `Level.kt` (`Quest`, `Menace`, `Land`, `Level.ALL`) | `data/levels.json` + `sim/level.gd` | Rijen zijn data; `Land.village()` en `starterRoad` moeten in `sim/gen.gd` |
| `Beast.kt` toestandsmachine | `sim/beast.gd` | Puur getallen; vliegende types met `airborne` |
| `Props.hash` (vakhash voor spawns, deterministisch) | `sim/hash.gd` | Zonder `Random`; behoud voor testbaarheid en savegames |
| `Save.kt`/`World.snapshot :5630` | `sim/save.gd` (Dictionary → JSON) | Tekstformaat, `restore :5811` |
| `PlayTest.Bot` + `Rival.kt` (headless speler op publieke API) | `test/bot.gd` + GUT | **Hoogste waarde voor balans**: laat levels uitspelen op `--fixed-fps` zonder render. In beasts-src kostte dit 2m28 (ladder) / 13 min (volledig) |

### 4b. Wat opnieuw moet

| Onderdeel | Waarom | Aanpak |
| --- | --- | --- |
| Alle `*Art.kt`, `GameView` render, `HudArt` | Canvas-tekening; wij hebben echte modellen | Vervangen door `view/*.gd` die sim-entiteiten spiegelen |
| Invoer (`GameView.tap`, pinch, hold) | Aanraak, vaste isometrie | `ui/controller.gd`: raycast naar grondvlak, `rts_camera.gd` is er al; vertaal klik → dezelfde sim-API-aanroepen (`select`, `walk`, `harvest`, `tend`, `attack`, `help`, `enlist`) |
| Pathfinding in 3D | Geen vaste diamanten; hoogte/obstakels | **Houd een logisch rooster** (vak = cel van N m) voor sim + bouwregels; Navigation mesh alleen als hoogteverschil of vrije bouw komt. Rooster + A\* + lokale uitwijking is genoeg voor slice |
| Camera/zoom | `Iso.FACING_CAMERA` (deuren altijd naar camera) | Deur-richting vrij (4–8); sorteerprobleem bestaat niet meer (diepte via GPU) |
| Geluid | `Voice.kt` SoundPool | `AudioStreamPlayer3D`; 56 stemfragmenten uit beasts-src zijn ElevenLabs en **commercieel check nodig voor reuse** [?] |

### 4c. Voorgestelde mappen en bestanden (minimaal)

```
godot_game/
  data/units.json  buildings.json  goods.json  herds.json  beasts.json  levels.json  balance.json
  sim/   sim.gd  grid.gd  router.gd  jobs.gd  family.gd  combat.gd  beast.gd  hash.gd  save.gd
  view/  world_view.gd  villager_view.gd(Bumpkin)  building_view.gd(hut, deur/kaars/rook)  animal_view.gd  fx.gd
  ui/    controller.gd  hud.gd  build_menu.gd  rts_camera.gd(bestaand)
  test/  bot.gd  test_*.gd (GUT)
```

**Sim los van render:** `Sim` is een `RefCounted`/autoload zonder `Node3D`; `_physics_process` roept `tick(dt)` met vaste 1/20 s en `view` interpoleert (beasts-src 60 Hz is "ruim, RTS heeft er minder nodig", `World.kt:6085`). Alleen `sim/` mag `data/*.json` lezen; `view/` krijgt events (`gebouwd`, `geboren`, `geraakt`, `gestorven`, `verkocht`) via signalen. Headless (`--headless`) draait `sim/` + bot zonder GPU.

**Entiteiten en data** (voorbeeld `units.json`, velden = beasts-src + `lijst.md`):

```json
{ "man":   {"rig":"bumpkin_man","orig":"m_still/m_walk","lijst":"-","schaal":1.0,"hp":24,"hit":4,"cyclus":0.8,"bereik":1.6,"pace":1.0},
  "vrouw": {"rig":"bumpkin_man","orig":"f_still/f_walk","lijst":1,"schaal":0.95,"hp":24},
  "jongen":{"rig":"bumpkin_man","orig":"kidm","lijst":2,"schaal":0.81,"groeit":150},
  "oudere_man":{"orig":"elderm","lijst":4,"schaal":0.96},
  "bouwer":{"orig":"reparman/rp_still","lijst":6,"werk":"bouwen"},
  "wolf": {"orig":"wolf/wolfstil/wolfatta","lijst":26,"pace":1.6,"notice":7,"reach":0.9,"hp":8,"dmg":5,"strike":0.9,"prey":"cow"},
  "zombie":{"orig":"zombie/zombatta","lijst":27} }
```
`buildings.json`: `{id, orig:"House", lijst, prijs, werk_per_vak, bedden, goederen, hp, deur:["front","left"], voorraad}`; `herds.json` = tabel 3c; `levels.json` = tabel 3e; `balance.json` = alle constanten van 3a–3d zodat de bot ze kan overschrijven. Voor de **sprite-namen uit `lijst.md`** volstaat een `orig` + `lijst`-veld: de remake gebruikt ze alleen als herkomst/QA, niet als asset.

### 4d. Hoe de gebouwde Godot-stukken aansluiten

**`modellen/godot3d/bumpkin.gd` (`class_name Bumpkin`, 435 r):**

| Wat | Koppeling |
| --- | --- |
| `loop_naar(doel, rennen)` + signal `aangekomen` | **Aanbevolen niet de sim eraan te hangen.** Bumpkin beweegt zelf (`_beweeg`, `ACCEL` 6, `DRAAI` 10); als de sim de bron van positie is moet het model volgen. Voeg een dunne `volg(pos, snelheid_mps)`-modus toe (zet positie, kijk, schaal `tempo` zodat voeten niet glijden: loopsnelheid = `snelheid_mps` × `tempo`). Zo blijft de sim headless en deterministisch |
| `werk(aan)` | Sim-toestand "bouwen/oogsten/melken" → `werk(true)`. Nu is er **alleen één hamerlus** (`bouwen`, 1,25 s per lus, impact 0,4583 s in `bumpkin_anim.json`); maaien/melken/hakken/dragen moeten nog als clips |
| `val_aan()` | Sim `fight`: start slag → `val_aan()`; schade pas op `impact_s` van de clip (0,4167 s van 1,0 s). **Data-gedreven:** laat sim `HIT_CYCLE` en treffermoment uit `bumpkin_anim.json` lezen; dan is geen signal-terugkoppeling nodig |
| `gooi_steen(doel)` + `impact('steen')` | Nieuw 3D-geschenk: **de afstandsaanval bestaat al**. Voorstel `balance.json`: `steen_schade`, `steen_bereik` (nu in `beasts-src` ontbrekend). Signal `impact('steen')` kan het raakmoment voor het geluid zijn; schade blijft in sim op timing |
| `zet_nacht(f)` | Aanroepen vanuit `world_view` per man (rimlicht en meelopend licht) op `Sim.isNight`/overgang |
| `tempo` | Looptempo per man (`Look.pace`) → `tempo` |
| Signals `aangekomen`, `impact(welke)` | Alleen voor geluid en visuele FX, niet voor spelregels |

`bumpkin.gd` kent **6 animaties** (idle, lopen, rennen, bouwen, zwaard, steen); `bumpkin_anim.json` zegt lopen = **0,849 m/s**, rennen = **2,40 m/s**. Zie vraag 7: de sim loopt op 2,2 vak/s.

**Hut (`main.gd`, `peasant_hut_rt.glb`, LOD1 vanaf 28 m):**

| Ankerknoop | Sim-koppeling |
| --- | --- |
| `deur_voor` (−90° open) | `doorWanted :5492` / `gateOpenness :5513`: deur open als iemand binnen `DOOR_RANGE` is. In 3D: schakel de rotatie met `DOOR_SPEED` |
| `deur_voor_drempel` | `Building.doorstep`: looproute, ook `Villager.entering`/`inside` |
| `kaars` | Aan als `isNight` **en** iemand `inside` (sim.sleep). Demo doet dit al (`main.gd:710`) |
| `rook_bron` | Aan bij nacht of winter of bewoond |
| `ruit*` | Gloeimateriaal als kaars brandt |

Een tweede gebouw (molen, melkerij, kippenhok, gereedschapsloods) krijgt dezelfde ankernamen (`deur_*`, `kaars`, `rook_bron`, `ruit*`) zodat `building_view.gd` generiek blijft; elk gebouw moet een `doorstep` en footprint in `buildings.json` hebben.

---

## 5. Eerste speelbare slice

**Doel van de missie ("Het eerste dorp"):** op een kaart van 40 vakken beginnen met 2 man + 1 vrouw (+ 2 hutten, 1 weide met 3 koeien, 1 kippenren, 1 akker), kas 120; groei tot **12 inwoners** (kinderen tellen mee) en **verdedig** tegen wolven (dag) en zombies (nacht). Verlies bij 0 inwoners. Quest = `PEOPLE` 12 (`World.progress`), maar zonder `RIVAL`/`DENS`. Verhaalbord: één alinea.

Gebouw-mapping naar beschikbare assets:

| Asset | Spelrol (beasts-src) |
| --- | --- |
| Hut | `HUT` (2 bedden, deur, kaars) |
| Molen | `SHOP` (CROP: graan), brood is alleen naam |
| Melkerij | `DAIRY` (MILK) |
| Kippenhok | `HENHOUSE` (EGGS) |
| Gereedschapsloods | bouwersopslag / `WAPENHUT`-rol (hout, steen, speer) |
| Bouwer | man met rol "bouwt sneller" (vraag 3) of cosmetisch |
| Man / vrouw / jongen / meisje / oudere | volwassen / kind (`GROW_UP`) / "oud" (zie vraag 2) |
| Koe, kippen | `Herd.CATTLE`, `Herd.HENS` |
| Wolf, zombie | `Beast.Kind.WOLF`, nieuw `ZOMBIE` (nacht) |

**Bouwvolgorde (geschat 12 stappen, elk testbaar):**

1. **Skelet**: Godot-project met `data/*.json` en `Sim` (autoload, headless), vaste tik, `Hash`. Poort `Grid`/`Ground`/`Router` en een mini-kaart 40×40. Test: A\* levert een route en de randregel blokkeert een hek.
2. **Kaart + wereldview**: gras-vlak (bestaand `gras.gdshader`), vakken zichtbaar in debug, tikken op de grond geeft een vak (raycast). `rts_camera.gd` hergebruiken.
3. **Eerste man**: `Villager` in sim + `villager_view.gd` met `Bumpkin` (volg-modus, §4d). Klik = `walk`; selecteer via raycast; `PICK_RANGE`.
4. **Hut + dag/nacht**: `building_view.gd` met ankers; poort `clock`, `isNight`, `sleep`/`wake`, `beds`; deur opent, kaars aan. Kaart-klok → uur-mapping.
5. **Bestellen en bouwen**: bouwmenu (alleen hut), ghost met raycast, `Plan`/`Site`/`Job`, `commit`; `werk(true)` hamerlus; 4 bouwstanden (scaffold of scherm-schaal). Prijs van kas.
6. **Kas en HUD**: `purses`, tekstbalk (kas, inwoners X/12, seizoen/tijd, doel); verhaalbord.
7. **Winkels en behoeften**: molen + melkerij + kippenhok (placeholder-modellen mogen), `Goods`, `stock`, `visit`, `crave`/`need`, `goShopping`. Test via bot: kas stijgt.
8. **Gewas en jobkiezer**: akker + `ripen`, `goProduce`/`goHarvest`/`deliver`, `chooses` volledig geport met `attempt`; claim-/dubbele-doelregels (`it.spot`, `crew`). Dit is de port-kern: bot moet 10 min zonder vastlopen halen.
9. **Vee**: `Animal`/`Herd`, roam, `lead`/`loose`, `tend`, `STORE_RANGE`; eerst capsules, dan koe-/kip-rig; **koebel** zodra `eigen` gezet. Melkklus (vrouw: melk-clip nieuw).
10. **Gezin**: `Cradle`, `birth`, baby (prop), kind (schaal 0,81), `GROW_UP`, `PARENT_REST`, oudere (statusmodel).
11. **Vijanden**: `Beast` (wolf) + `fight`, `goGuard`, steen gooien, kind-vlucht; zombie bij nacht vanaf rand. Sim-schade op `impact_s` uit `bumpkin_anim.json`. Ontbreekt: wolf- en zombie-rig (concept 26, 27).
12. **Missie en einde**: `progress`/`done`/`lost`, win-/verliesscherm, level uit `levels.json`.
13. **Bot en balans**: port `PlayTest.Bot` (kleine versie: bouwt hut + winkel, oogst, vecht), draai headless op `--fixed-fps` + `--time-scale`, controleer dat de missie in redelijke tijd (<~15 min) te winnen is en te verliezen valt; stel `balance.json` bij.
14. **Opslaan/laden** (optioneel): `snapshot`/`restore`, deterministische seed.

Kosten: stap 1–6 zijn het eigenlijke "spel"; 7–8 geven het dorp; 9–11 geven drama. Assets die we straks hebben (hut, man) volstaan voor 1–6; voor 7+ zijn placeholders (capsule + kleur) genoeg tot er rigs zijn.

---

## 6. Open vragen voor de gebruiker

1. **Welke economie?** beasts-src: bewoners kopen waar → kas groeit; geen honger/water/geluk/belasting. Origineel: eten/water/geluk/fitheid, belastinginner, tiende. Voorstel: beasts-src-lus voor de slice, daarna behoeften toevoegen (eerst eten/geluk). Wil je **graan → brood** (molen + bakkerij) als echte productiestap of blijft het één schakel?
2. **Ouderen en dood door ouderdom?** Origineel: baby → kind → volwassene → oud → dood (~4–5 jaar). beasts-src stopt bij volwassen. Onze oudere man/vrouw assets bestaan; moeten ze **spelers** zijn (werken minder, overlijden) of alleen sfeer?
3. **Wie bouwt?** beasts-src: elke volwassene (max 4 per bouwplaats). Origineel: mannen bouwen; bouwersgilde bestaat. Is "Bouwer" een **eigen rol** (sneller, alleen via gereedschapsloods) of een uiterlijk van een man met hamer? En gereedschapsloods = wapenhut-achtige opslag of puur bouwersgilde?
4. **Wat eet de wolf?** beasts-src: koeien. Origineel: baby's (die tegenstelling raakt gezin én vee). Welke, en is er **een nachtvijand** (zombie vanuit tombe/ei, origineel `Egg (zombie spawner)`) of blijft het rand-spawnen?
5. **Eigendom en koebel.** Voorstel: dier is "eigen" zodra het in een eigen hek staat of door een dorpeling is geleid en binnen `STORE_RANGE`=20 van een melkerij komt; belletje als visueel teken; eigen dieren geven melk, wolven jagen op alle. Kan een eigen koe weglopen/verloren raken? Moet de speler dieren **kopen** (kas) of alleen lokken?
6. **Afstandswapen.** Steengooi (3D-clip aanwezig) is origineel (mthrow). Moet elke volwassene stenen kunnen gooien (bereik? schade? munitie?), of alleen een gildeklasse? En vluchten volwassenen/moraal (origineel heeft flee-sprites)?
7. **Maat en tempo.** Man loopt 0,85 m/s (lopen) of 2,4 m/s (rennen); beasts-src 2,2 vak/s. Hoe groot is één logische cel in meters, en is **loopt** of **rent** de standaard? Alle afstanden (`HOMELY`=9, `STORE_RANGE`=20, `HIT_REACH`=1,6) schalen hiermee. Zonder keus bestaat een hutgrootte-in-vakken niet; hutmaat nog niet gemeten uit `peasant_hut_rt.glb` **[?]**.
8. **Besturing.** beasts-src: één gekozen man krijgt bevelen, de rest werkt automatisch; touch. PC: wil je **groepsselectie** (sleep-box), rechtsklik-bevel, formaties? Pauze en snelheid?
9. **Hoe ver bouwen?** Vrije plaatsing in 3D (rotatie, ook schuin) of rooster met 4 deurrichtingen? `Grid.SPACING`=4 en de "weg naar de deur"-regel (`World.aim`) zijn dan opnieuw te bepalen.
10. **Missies.** Poorten we de ladder van beasts-src (22 levels, 6 questtypes) als campagne-skelet, of schrijven we nieuwe missies (Lord Mildew-verhaal uit het origineel [O]) en dan welke doelen (overleven, item halen met sleutel)? Het origineel heeft 30 missies met scripts die we niet hebben.
11. **Veertig rigs?** Concept noemt ~40 rigs (onderzoek). Welke eenheden moeten de slice halen, en wil je **quadruped-rig** (koe/wolf) via Tripo (onderzoek, 25 credits) of handwerk in Blender? Belangrijk voor stap 9 en 11.
12. **Seizoen en weer.** beasts-src: seizoen per dag-nacht (270 s); jaar = 18 min, winter doodt gewas. Houden we dat (kort) of rekken we naar langere seizoenen? Weer (regen/onweer) in de slice of later?
13. **Geluid.** De 56 stemfragmenten van beasts-src zijn gegenereerd (ElevenLabs, 4 stemmen). Herbruikbaar in de remake (licentie van het plan ten tijde van maken) of opnieuw?

## 7. Besluiten van de gebruiker (2026-10-29)

Vervangt de voorstellen in sectie 6 waar ze botsen.

| Onderwerp | Besluit |
| --- | --- |
| Economie | beasts-src-lus (kopen vult de kas) eerst, daarna eten en geluk |
| Celmaat en tempo | 2 m per tegel. **Geen rennen in missie 1** (origineel heeft het niet; later leuk). Lopen over een **pad is iets sneller** dan over gras, zoals in het origineel |
| Koe en eigendom | Eigen koe krijgt een bel. **Ook wilde koeien geven melk**; dorpelingen gaan alleen melken als de koe **dicht bij het dorp** staat |
| Werk naar leeftijd | **Alleen volwassenen werken.** Kinderen en ouderen werken niet, maar **kopen wel** |
| Wie bouwt | Elke volwassen man bouwt, de bouwer bouwt sneller |
| Bouwen in de remake (2026-10-29, gebruiker) | **Geen limiet van 4 werkers** (werkers tellen op); **de hut gaat in stappen** (4 bouwstanden, zichtbaar per stand; modern). **Nostalgie:** de bouwer zaagt of hamert bij een **houtstapel (woodpile)** of **steenstapel (stonepile)** bij de bouwplaats, zoals in het origineel. Werk 60 s per hut (origineel); prijs 40 uit de kas volgt met de economie |
| Besturing (PC) | Selecteren met **selectiekader of klik op een unit**. **Linkerklik = bevel**, **rechterklik = selectie weg**. Lopen kan iedereen; **vechten en werken alleen volwassenen** |
| Plaatsen | Rooster, 4 deurrichtingen (R draait) |
| Steen gooien | **Munitie is oneindig** en komt nergens vandaan, zoals in het origineel. Per worp **hurken en een steen van de grond rapen**, dan opstaan en gooien: de bestaande `aanval_steen` (rapen op `pak_s`, loslaten op `release_s`) volgt dat al |
| Wolf | Eet koeien; baby's als moeilijkheid later |
| Seizoenen en weer | **Ook in missie 1** |
| Missieladder | Origineel volgen, beginnend bij Aorta |
| Rigs voor dieren | Zelf in Blender, Tripo alleen als dat vastloopt |
| Stemmen | beasts-src-fragmenten hergebruiken waar ze passen |
