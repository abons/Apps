# Audioplan Beasts & Bumpkins-remake (Godot 4.7.2)

Stand 2026-10-29: analyse en inventaris (sectie 1 tot 5). **2026-10-30: missie 1 heeft geluid, zie sectie 6.** **Niets beluisterd**: alles over de originele klanken is afgeleid uit bestandsnamen, groottes, kanalen en een eenvoudige signaalmeting (duur, RMS, nuldoorgangen). Zo gemerkt met **[?]**. Het originele audiomateriaal is auteursrechtelijk beschermd, alleen voor eigen gebruik en **gaat nooit in git**; dit bestand bevat alleen tekst.

Lokale kopie (niet in git): `SC/audio_origineel/{BBRBANK,BBSPRAUT,BBSUMMER,BBWINTER,SPEECH0}/` met `SC` = `C:/Users/Axel/AppData/Local/Temp/claude/E--werk-androidApps-Apps/16e99493-ac86-47c7-921f-1d215c266f51/scratchpad/` (416 wav, ca. 9,5 MB). Bron: `\\axel-laptop\Users\axelb\beasts\beastnbump\extracted_audio\`.

## 1. Origineel (1996)

### 1a. Wat de extractiescripts dekken

| bestand | wat het doet | dekking |
| --- | --- | --- |
| `extract_audio.ps1` | `.FAT` (magic `0.30`, 8 byte kop, 16 byte per entry: offset, size, kanalen, vlag) naar WAV, **16-bit PCM, 22050 Hz aangenomen** (parameter) | `BBRBANK`, `BBSPRAUT`, `BBSUMMER`, `BBWINTER` |
| `extract_speech.ps1` | `.BOX`: zoekt het pad `c:\windows\desktop\b&bwork\compressenglish\<naam>.M10`, dan `PT`-kop (8 byte), **8-bit unsigned, 11025 Hz aangenomen** | alle `*.BOX`, maar alleen `SPEECH0` heeft M10-audio |

| bevinding | detail |
| --- | --- |
| `SPEECH0..4.BOX` zijn **byte-identiek** | alle vijf 2.408.044 byte, zelfde md5. De padnaam zegt `compressenglish`; talen zijn dus niet verspreid over de vijf. Eén set telt, 267 fragmenten |
| `MISC.BOX`, `MISSIONS.BOX`, `VIDEO.BOX`, `MISTEXT*.BOX` | **geen audio**: lettertypen/strings (`.FDF`, `.TXT`, `.SYN`), 60 missies (`.MIS`), 1248 sprites (`.MFB`) |
| `BBRBANK.FAT` | 88 entries, **79 geëxtraheerd**. De 9 ontbrekende (2, 20, 40, 44, 55, 82, 85, 86, 87; allemaal mono, samen ca. 223 KB, ca. 5 s) zijn geldig en passen in het bestand: de map is onvolledig, **opnieuw extraheren** |
| Overige FAT | `BBSPRAUT` 24/24, `BBSUMMER` 30/30, `BBWINTER` 16/16 compleet |
| Vlagwoord per FAT-entry | `0x01010001` bij 86 van 88; entries 36 en 75 hebben `0x02010001` **[?]** (loop-vlag of formaat). Geen samplefrequentie in de kop: 22050 Hz is een aanname, de signaalmeting (piek 0,9 genormaliseerd, geen ruisbeeld) klopt ermee |
| Muziek | **cd-audio, zie sectie 7** (2026-10-31). Geen in de geëxtraheerde bestanden. Alle FAT-klanken duren 0,04 tot 6,3 s. `QMIXER95.DLL` (Q-Sound-mixer), `MIX.DAT`, `REFLECT.DAT` zijn geen muziek. Muziek zit waarschijnlijk op de cd of in `BEASTS.EXE` **[?]**; `INTRO/OUTRO/CREDITS/EALOGO.VID` zijn 0 byte (weggelaten). Niet onderzocht: `M*.VID`/`MAP*.VID` (1 tot 3 MB, waarschijnlijk kaart-/missiebeelden, geen audio) |

### 1b. Effecten: de vier banken (149 wav)

Alles is een **one-shot**; er zit geen lus of omgevingsklank van betekenis in. Seizoensbanken delen onderling klanken (`BBWINTER_006..012` is gelijk aan `BBSPRAUT_000..003/007..009`; `BBSUMMER_008/009` is gelijk aan `BBSPRAUT_018/019`): spel laadt vermoedelijk **`BBRBANK` + één seizoensbank**.

| bank | entries (stereo / mono) | bestandspatroon | duur | MB | vermoeden (afgeleid) |
| --- | --- | --- | --- | --- | --- |
| `BBRBANK` | 88 (16 / 72), 79 geëxtraheerd | `BBRBANK_nnn_{mono,stereo}.wav` | 0,04 tot 3,0 s | 3,2 | basisbank: acties en voorwerpen. 000/001 (2,4 s, 99 Hz, luid) = **donder** **[?]**; 003 tot 005 (1,2 tot 1,6 s, zacht, ruisig) = regen/wind **[?]**; 006 tot 016 stereo 0,2 tot 1,2 s = spreuk/explosie/vuur; mono 018 tot 063 korte tikken en plofjes (0,04 tot 0,7 s) = klik/munt/slag/bouw; mono 064 tot 081 (0,4 tot 3,0 s) = langere dier-, mens- of poortgeluiden |
| `BBSUMMER` | 30 (6 / 24) | `BBSUMMER_nnn_*.wav` | 0,1 tot 3,4 s | 2,0 | 000 tot 002 stereo 0,7 tot 0,9 s met zeer hoge toonhoogte (ca. 8,5 kHz) = **krekel/insect/vogel** **[?]**; 020 tot 025 mono 1,2 tot 2,2 s, laag = dierstemmen (koe?) **[?]**; 026 tot 029 stil, 1,4 tot 3,4 s = omgeving |
| `BBSPRAUT` | 24 (15 / 9) | `BBSPRAUT_nnn_*.wav` | 0,5 tot 2,0 s | 2,0 | lente/herfst: 000 tot 003 en 007 tot 009 stereo laag = wind/blad **[?]**; 010 tot 013 hoger = vogel/regen **[?]** |
| `BBWINTER` | 16 (11 / 5) | `BBWINTER_nnn_*.wav` | 0,3 tot 6,3 s | 2,1 | 000 tot 003 en 005 (6,3 s mono, 480 Hz) = **wind** **[?]**; 004 = windvlaag **[?]** |

**Wat dit betekent:** het origineel kent seizoensgebonden omgevingsklank, maar als **korte stukjes die willekeurig worden afgespeeld**, geen doorlopende lus. Voor ons: eigen lussen en one-shots met een scheduler, de stukken uit de originele banken zijn hooguit referentie.

### 1c. Spraak: `SPEECH0` (267 fragmenten, 11025 Hz, 8-bit, mono)

Patroon: `SPEECH0_nnn_<NAAM>.M10.wav`, 0,04 tot 6,5 s (gemiddeld 0,2 tot 2,0 s, mediaan ca. 0,7 s), 2,2 MB. De volgorde in het archief is per naam gemengd, niet gegroepeerd. **Aanname: PF/PM lijnen = selectie, bevel, werk, klacht** (zie 1d, niet gecontroleerd). Voorvoegsels (de lettercodes zijn de eenheden uit `concept/lijst.md`):

| voorvoegsel | n | gemiddeld | vermoedelijk |
| --- | --- | --- | --- |
| `PM` 1 tot 42 | 42 | 0,6 s | **man (peasant male)**: selectie, bevel, werk |
| `PF` 1 tot 46 | 46 | 0,7 s | **vrouw (peasant female)** |
| `YPB`, `YPG` | 2 + 2 | 0,7 / 0,9 s | **jongen, meisje** (young peasant boy/girl) |
| `OPM`, `OPF` | 2 + 2 | 0,9 / 0,5 s | **oudere man, oudere vrouw** |
| `BAB`, `Pop2baby`, `Popbaby2`, `popp` | 3 + 3 | 0,1 tot 0,8 s | baby: gehuil en geboorte-"plop" |
| `MONKP`, `MONKF` | 4 + 7 | 0,7 tot 0,9 s | monnik |
| `PRE` 1 tot 13 | 13 | 0,8 s | priester |
| `PIK` 1 tot 11, `FOOT` 1 tot 4, `CAV`, `KN`, `ARC`, `FLAG`, `FB` | 11, 4, 4, 4, 4, 5, 3 | 0,2 tot 0,9 s | piekenier, voetsoldaat, cavalerist, ridder, boogschutter, vlagdrager, ?, **[?]** |
| `WIZ` 1 tot 12, `MAG` 1 tot 6 | 12, 6 | 0,5 / 1,0 s | tovenaar, spreukklanken |
| `JES`, `TG`, `TAX`, `TOW`, `BUL` | 5, 5, 5, 5, 4 | 0,4 tot 0,8 s | nar, ?, belastinginner, ?, (beul?) **[?]** |
| `GHOS`, `ZOM`, `VAM`, `DEM`, `DVOX`, `EX` | 4, 1, 5, 7, 7, 6 | 0,9 tot 1,5 s | spook, zombie, vampier, demon, duivelsstem, ? |
| `crow` 1 tot 13 | 13 | 2,0 s | **menigte/volkslawaai** (applaus, gemurmel) |
| `munch3`, `chickdie`, `pig3`, `wbark2`, `wolfbite`, `wolfgrwl`, `Fart2/4/5/6`, `Beertent` | 1,1,1,1,1,1,4,1 | 0,1 tot 0,8 s | **kauwen, kippendood, varken, wolf blaffen/bijten/grommen**, scheten, bierfeest |
| `MISC1..6`, `FON1..3`, `DS1` | 6, 3, 1 | 0,8 / 1,7 / 6,5 s | losse stingers en een lang fragment (verhaal/intro) |

### 1d. Wat het origineel doet

| gedrag | bron | zekerheid |
| --- | --- | --- |
| Dorpelingen hebben **eigen stemsets per geslacht en leeftijd** (man 42, vrouw 46, jongen/meisje 2, oud 2) | bestandsnamen | goed |
| Selectie- en bevelgeluid per eenheid; spraakbellen/denkwolken in beeld (`concept/lijst.md` noemt denkwolken, `gameplay.md` sectie 2) | namen + gameplay.md | geluid bij tekst **[?]** |
| Eigen klanken voor wolf, kip, varken, kauwen, baby: dieren en geboorte zijn hoorbaar | namen | goed |
| Seizoensbank bepaalt omgevingsklank; weer (donder, regen) in de basisbank | bankindeling | **[?]** |
| Eenheden buiten missie 1 (vampier, demon, spook, zombie) hebben eigen stemmen: pas bij missie 2+ nodig | namen | goed |

**Luisterlijst voor Axel (15 minuten):** speel `PM1,PM2,PM10,PM30,PF1,PF20,YPB1,YPG1,OPM1,OPF1,crow1,wolfgrwl`, `BBRBANK_000/003/017/064`, `BBSUMMER_000/020/026`, `BBWINTER_005`, `BBSPRAUT_000/010`. Dan staat vast of de aannames hierboven kloppen, en of 22050/11025 Hz de juiste snelheid is.

## 2. Eigen Android-versie (`beasts-src`)

`app/src/main/res/raw/`, 2,4 MB, **69 bestanden**: 62 mp3 (ElevenLabs) en 7 wav (eigen synthese). Code: `Voice.kt` (`SoundPool`, 4 stromen, eigen draad omdat `SoundPool.play` op het toestel 31 tot 127 ms blokkeert), aangeroepen vanuit `GameView.kt`. Bestanden worden op **naam** gezocht (`getIdentifier`); `Voice.Line.fallback` valt terug op het gewone bevelfragment. Besluiten: `design.md` > *Stemfragmenten bij een tik* en *Een verkoop is te zien en te horen*.

| groep | bestanden | n | inhoud | trigger (`GameView.kt`) |
| --- | --- | --- | --- | --- |
| Selectie `voice_select_{m,f,b,g}_0..3` | mp3, ca. 1,6 tot 1,8 s | 16 | tussenwerpsels zonder woorden: m "Hm? Mm? Hnh? Oi?", f "Hm? Mm-hm? Ah? Oh?", b/g "Hm? Mm? Huh? Oh?" | `tap` bij `world.select(man)` (`:794`) |
| Bevel `voice_order_{m,f,b,g}_0..3` | mp3, ca. 1,6 tot 1,8 s | 16 | "Hup! Aye. Mm. Hop!", f "Hup! Mm. Ha! Oh!", b/g "Hup! Ha! Hop! Oh!" | `tap`: lopen, aanvallen, enlist, bouwhulp (`:861 tot :972`) |
| Lokroep `voice_{cattle,sheep,hens}_{m,f,b,g}_0..1` | mp3, ca. 2 s | 24 | "Hoi! Hoi!" (koe), "Tsk, tsk!" (schaap), "Tuk, tuk, tuk!" (kip) | bij aankomst bij het dier en bij de poort (`herding`, `:1108`, `:1112`) |
| Dier `voice_{moo,baa,cluck}_0..1` | mp3, 3 tot 4,5 s | 6 | ElevenLabs **Sound Effects**, echte boerderijgeluiden | bij tik op dier (`:826`, `:880`) en bij de poort (`:1113`) |
| Eigen synthese `voice_{build_0,build_1,coin_0,crop_0,milk_0,wool_0,eggs_0}.wav` | wav | 7 | hamer (2x), munt, oogst, melk, wol, eieren; **plaatshouders**, op toestel goedgekeurd (`todo.md` van beasts-src) | `Sound.COIN` (`:1149`), `Sound.taking(goods)` (`:1177`), `Sound.BUILD` (`:1210`) |

Stemmen (alle vier **taalneutraal**, dus ook bruikbaar in elke taalversie): Jerry B. (m, "Warm, Friendly Storyteller"), Louise (f, "Warm and Friendly"), Dibsy (b, "Sweet and Childish"), Emmaline (g, "young British girl"). Spreiding en volume gaan via `Voice.Spot` (pan en volume uit schermpositie), **geen** afstandsdemping zoals 3D; `KNOCK_GAP = 0,30 s` knijpt bellers af.

**Herbruik in Godot:**

| wat | oordeel |
| --- | --- |
| 32 selectie/bevel (man, vrouw, jongen, meisje) | **ja, direct**: past op de besluiten (sectie 7 gameplay.md: "beasts-src-fragmenten hergebruiken waar ze passen"). Convert naar `.ogg` |
| 24 lokroepen + 6 dierklanken | **ja**: koe moo en lokroep passen bij missie 1; schaap/kip pas later |
| 7 eigen wav | ja, eigen werk, rechtenvrij; kwaliteit laag, vervangen zodra er een betere is (hamer, melken, oogst) |
| Ouderen | **ontbreken**: oudere man/vrouw krijgen m/f met lagere toonhoogte (pitch 0,88 tot 0,92) of nieuwe stemmen |
| **Licentie (open, uit gameplay.md vraag 13)** | De 62 mp3 zijn gegenereerd met ElevenLabs op het toenmalige plan (2026-09-03, via de browser, gebruiker ingelogd). Welk plan het was staat nergens vastgelegd. Voorwaarde van ElevenLabs (te verifiëren, niet in het repo): commercieel gebruik alleen met een **betaald** abonnement op het moment van genereren; gratis plan = niet-commercieel met bronvermelding. Voor **privé/niet-gepubliceerd** gebruik (beasts is niet gepubliceerd) is het geen probleem; voor publicatie moet het plan vaststaan of moeten we opnieuw genereren |

## 3. Geluidslijst missie 1 en eerste speelbare slice

Missie 1 (Aorta): 6 dorpelingen (man, vrouw, kinderen), vlag, kampvuur, bron, koeien, bomen (den en spar), rotsboog, zee-ring, paddenstoelen, zilveren beker; geen vijanden (zie `map1.md`). Seizoen en weer ook in missie 1 (besluit). Prioriteit: **P1** = slice kan niet zonder, **P2** = missie 1 af, **P3** = later.

Bron: **B** = hergebruik beasts-src, **C** = CC0-bibliotheek, **G** = genereren (ElevenLabs SFX/voice), **R** = zelf opnemen.

### 3a. Stemmen en acties

| geluid | prio | n | bron | opmerking |
| --- | --- | --- | --- | --- |
| Selectie man / vrouw / jongen / meisje | P1 | 4 x 4 | B | direct uit de 16 `select` |
| Bevel man / vrouw / jongen / meisje | P1 | 4 x 4 | B | 16 `order` |
| Selectie en bevel **oudere man / vrouw** | P2 | 2 x 4 + 2 x 4 | G | lage, dunne stem; of B met pitch 0,9 als noodoplossing |
| Groepsselectie | P1 | 0 | n.v.t. | alleen de **leider** spreekt (zie 4) |
| Bouwen: hamer, zaag | P2 | 4 + 3 | B (hamer 2), C | Freesound CC0 `hammer wood nail`, `handsaw` |
| Oogsten, maaien | P2 | 3 | B (`crop`), C | Freesound `scythe grass swipe` |
| Steen rapen, gooien, inslag | P2 | 2 + 3 + 3 | C | `pebble pickup`, `whoosh short`, `stone impact dirt`; moment: `pak_s`, `release_s`, `impact('steen')` |
| Melken | P2 | 3 | B (`milk`), C | later opnieuw: `milk squirt bucket` |
| Eten (bij nood), eieren/wol | P3 | 3 | B | `eggs`, `wool` |
| Geboorte (baby "plop" en gehuil) | P3 | 2 | G | origineel heeft `Pop2baby`; wij: eigen baby-SFX |

### 3b. Voetstappen per ondergrond

| ondergrond | prio | n | bron | opmerking |
| --- | --- | --- | --- | --- |
| Gras | P1 | 6 varianten | C | Freesound `footsteps grass`; Sonniss GDC *Footstep* packs; Kenney heeft geen gras. Zacht, dof |
| Pad / aarde | P1 | 6 | C | `footsteps dirt gravel`; sneller tempo, +10 % pitch in lijn met besluit "pad is iets sneller" |
| Zand | P2 | 6 | C | `footsteps sand beach` (zandstrand zuid/oost) |
| Sneeuw | P2 | 6 | C | `footsteps snow crunch`, wintertegels |
| Rots / steen | P3 | 4 | C | rotsboog; alleen als er lopen mogelijk is |
| Water (door ondiep) | P3 | 4 | C | `splash shallow` |

Aanpak: voetstap via animatie-event (`footstep_l/r`) op de loopklip, ondergrond per tegel (splat-map) opvragen; zacht voor een groep (alleen de dichtstbijzijnde 3 klinken).

### 3c. Omgeving en seizoenen

| geluid | prio | n | bron | opmerking |
| --- | --- | --- | --- | --- |
| **Kampvuur** (lus, 3D bij het vuur, 2 tot 12 m) | P1 | 1 lus + 3 knallen | C | Freesound `campfire loop crackle` |
| **Wind** laag, boven open land (lus) | P1 | 1 | C | `wind ambience grass`; speelt altijd |
| **Wind door dennen** (lus, zweeft in bomen) | P2 | 1 | C | `wind pine trees` |
| **Water en kust** (golven op strand, lus, 3D langs de ring) | P1 | 1 + 3 | C | `ocean waves beach loop`; plaats langs kusttegels, niet 1x globaal |
| **Bron/waterput** (kabbelend, 3D) | P2 | 1 + 2 | C | `water well bucket`, `spring trickle` |
| **Regen** (lus, licht en zwaar) + dakklank op gebouwen | P2 | 2 + 1 | C | `rain loop light/heavy`; donder: origineel `BBRBANK_000/001` is **vermoedelijk** donder (alleen persoonlijk) of C `thunder distant` |
| **Vogels dag** (lente/zomer, one-shots plus lus) | P1 | 1 lus + 8 | C | `birds morning forest`, Sonniss; per seizoen minder |
| **Krekels nacht** (zomer/herfst) | P2 | 1 lus | C | `crickets night loop` |
| **Uil** (nacht, one-shot, ver) | P2 | 3 | C | `owl hoot distant` |
| **Winter**: stille wind, krakende sneeuw, geen insecten | P2 | 1 lus | C | `wind winter cold howl` |
| Gras bladeren fladderen / boomkruin | P3 | 1 | C | `leaves rustle` |

**Muziek**: het origineel had 7 cd-audiotracks; gebouwd in sectie 7.

### 3d. Koe, dier en overig

| geluid | prio | n | bron | opmerking |
| --- | --- | --- | --- | --- |
| **Koe loeien** | P1 | 2 + 4 | B (`moo`) + C | `cow moo` ca. 4 s; zware en lichte variant |
| **Koebel** (eigen koe, met stap) | P1 | 4 | C of G | `cow bell` (bel zonder dier), ritme op loopfase |
| **Kauwen / grazen** | P2 | 3 | C (origineel `munch3` alleen eigen) | `cow chewing grass` |
| **Melken** | P2 | 3 | B + C | zie 3a |
| Lokroep naar koe | P1 | 8 | B | `voice_cattle_*` |
| Schaap, kip | P3 | 6 + 6 | B | later |
| Wolf: grom, blaf, hap | P3 | 3 + 2 + 2 | C of G | vanaf missie 2 |
| Zombie, vampier, spook, demon | P3 | n.v.t. | G | vanaf missie 2+ |

### 3e. Interface

| geluid | prio | n | bron | opmerking |
| --- | --- | --- | --- | --- |
| Klik/hover, bouwmenu, plaatsen en draaien (R) | P1 | 4 | C | Kenney *UI Audio*, *Interface Sounds* (CC0) |
| Bouwen geslaagd / niet mogelijk | P1 | 2 | C | |
| Munt, kas (verkoop) | P2 | 2 | B (`coin`) | |
| Missie klaar, verloren (stinger) | P2 | 2 | G of C | korte fanfare, cartoonachtig hoornsignaal |
| Zilveren beker oppakken, vlag | P2 | 2 | C | `item pickup chime` |
| Seizoenswissel, dag-nacht (zacht) | P3 | 2 | C | |

Totaal ruwweg **P1: 9 klanken + 32 stemmen, P2: ca. 20, P3: de rest** (geen exacte telling zolang de bibliotheek niet is doorzocht). Libraries (kandidaten, **bestandsnamen niet gecontroleerd, zoek op de term**):

| bron | licentie | gebruik |
| --- | --- | --- |
| Freesound, filter **CC0** | CC0, geen bronvermelding (let op de filter: alleen CC0, niet CC-BY) | voetstappen, wind, kampvuur, golven, dieren |
| **Sonniss GDC Game Audio Bundle** (jaarlijks) | royalty-free, commercieel toegestaan, geen bronvermelding, **geen CC0** (voorwaarden bewaren) | omgeving en foley |
| **Kenney** (UI Audio, Impact Sounds, RPG Audio) | CC0 | UI en slagen |
| OpenGameArt, filter CC0 | CC0 per bestand | aanvulling |
| ElevenLabs Sound Effects / Voice | afhankelijk van plan, zie 2 | ontbrekende stemmen en een paar SFX |
| Zelf opnemen (telefoon) | eigen | koebel, hek/poort, hamer op hout |

## 4. Godot-implementatie

### 4a. Bussen en AudioManager

`AudioManager` als autoload (`audio_manager.gd`), de enige plek die `AudioStreamPlayer*` aanmaakt.

| bus | voor | effecten |
| --- | --- | --- |
| Master | alles, vloer van de eindvolume | limiter, ca. -1 dB plafond |
| SFX | acties, voetstappen, vuur, dieren | licht hoogdoorlaat 60 Hz |
| Stem | stemmen van eenheden (bij `Master`, geen eigen kind van SFX) | compressor met **sidechain** naar Stem op bus Ambient (ducken 3 tot 4 dB) |
| Ambient | wind, water, vogels, regen | lichte reverb, laag volume |
| Muziek | thema's | gedempt wanneer Stem klinkt |

Volumeschuiven per bus in opties (dB, niet lineair; 0 tot -40 dB, daaronder uit). Instellingen opslaan in `user://`.

### 4b. 3D-geluid voor een RTS-camera (2 tot 40 m)

| keuze | waarde |
| --- | --- |
| Luisteraar | **`AudioListener3D` op het camerabrandpunt** (de grond onder het scherm midden, 1 tot 2 m omhoog), **niet** op de `Camera3D`: dan bepaalt de zoom niet hoe hard een koe klinkt |
| `unit_size` | stem 8 (hoorbaar in beeld), voetstap 4, kampvuur 6, golven 12 |
| `max_distance` | stem 45 m, voetstap 25 m, kampvuur 30 m, golven 60 m, wind 0 (geen 3D, gewone `AudioStreamPlayer`) |
| `attenuation_model` | `ATTENUATION_INVERSE_DISTANCE` voor eenheden (zachter dan het standaard kwadraat), `ATTENUATION_LOGARITHMIC` voor omgeving |
| `panning_strength` | 0,6 (de camera kijkt schuin van boven; volle panning klinkt vreemd) |
| Hoogdoorlaat bij afstand | `attenuation_filter_cutoff_hz` 5000 voor eenheden, de standaard laten werken |
| Doppler | uit |
| Zoom | `AudioManager` zet SFX-volume af naar het uitzoomniveau: -3 dB per 10 m camerahoogte boven 20 m |
| Mono | voor 3D-bronnen altijd **mono**; stereo alleen voor `Ambient`-lussen zonder 3D |

### 4c. Stemmen: prioriteit, cooldown, selectie

| regel | waarde |
| --- | --- |
| Per eenheid | minimaal 3 s tussen twee stemlijnen; nooit dezelfde variant twee keer achter elkaar (shuffle-bag) |
| Globaal | maximaal 2 gelijktijdige Stem-lijnen; een nieuwe krijgt voorrang als prioriteit hoger of de vorige > 40 % klaar |
| Prioriteit | 3 meldingen (aanval, vlucht, missie) > 2 bevel > 1 selectie > 0 klaagzang/sfeer |
| Groep | bij groepsselectie spreekt **alleen de dichtstbijzijnde eenheid**; bij een bevel aan een groep ook één |
| Dubbelklik | een bevel binnen 0,3 s na de vorige (beasts-src `KNOCK_GAP`) speelt niets |
| Verwerking | stemklikken meteen spelen op `play()` (Godot blokkeert niet, in tegenstelling tot Android `SoundPool`) |
| Oude eenheden | pitch 0,9; baby/kind: pitch 1,08 en geluid van jongen/meisje |
| Koe | `moo` bij tik op dier (zoals beasts-src), lokroep pas wanneer de dorpeling bij het dier staat |

### 4d. Omgeving: dag/nacht en seizoen

Sim-signalen (geen spelregels in audio): `dagdeel_veranderd(naam)`, `seizoen_veranderd(naam)`, `weer_veranderd(soort)`. `AmbienceLayers` houdt één `AudioStreamPlayer` per **laag** (wind, wind-dennen, vogels, krekels, winterwind, regen_licht, regen_zwaar, golven) en tweent `volume_db` met `create_tween()` over **3 tot 6 s** (lineair in dB, daarna `stop()` bij -60 dB zodat er geen stille streams meedraaien).

| laag | dag | nacht | lente | zomer | herfst | winter | regen |
| --- | --- | --- | --- | --- | --- | --- | --- |
| wind laag | aan | aan | aan | aan | harder | harder | harder |
| vogels | aan | uit | aan | aan | weinig | uit | uit |
| krekels | uit | aan | uit | aan | zacht | uit | uit |
| uil (one-shot, 20 tot 60 s random) | uit | aan | uit | aan | aan | aan | uit |
| winterwind | uit | uit | uit | uit | uit | aan | uit |
| regenlus | uit | uit | - | - | - | - | aan (licht/zwaar) |

Eenmalige klanken (uil, vogelroep, donder) via een **scheduler** (random interval, random positie in de buurt van de camera, 3D op 15 tot 35 m), niet als eindeloze lus. Dag/nacht-overgang: crossfade 6 s rond zonsopgang/zonsondergang.

### 4e. Importinstellingen

| type | formaat | instellingen |
| --- | --- | --- |
| Korte SFX en stemmen (< 3 s) | `.ogg` Vorbis q4 (ca. 128 kbps), mono 44,1 kHz; of `.wav` 16-bit mono met `compress/mode=ADPCM` | `loop=false` |
| Lussen (wind, vuur, golven, regen) | `.ogg` stereo/mono, q5, 30 tot 60 s | `loop=true`, `loop_offset=0`, geluid **zelf naadloos** maken (crossfade binnen het bestand) |
| Muziek | `.ogg` stereo q5 | `loop=true`, via `Muziek` |
| Variaties | `AudioStreamRandomizer` met 3 tot 6 klanken, `random_pitch=1,05`, `random_volume_offset_db=1,5` | gebruik die voor voetstappen, hamer, loeien |
| Mp3 uit beasts-src | omzetten naar `.ogg` (mp3-import werkt, maar ogg is de standaard voor lussen en is kleiner) | ffmpeg |
| Normaliseren | -16 LUFS voor stemmen, -23 LUFS voor omgeving, piek -1 dBTP | achteraf in Godot met bus-volume bijstellen |

### 4f. Polyphony en pool

| onderdeel | advies |
| --- | --- |
| `max_polyphony` per `AudioStreamPlayer3D` | 1 voor een eenheid (nieuwe stem snijdt de oude af), 4 voor voetstappen in een groep, 2 voor kampvuur-knallen |
| Pool | `AudioManager` houdt een pool van ca. **24** `AudioStreamPlayer3D` en één van **8** `AudioStreamPlayer` (UI); herbruik het oudste vrije exemplaar, geen `queue_free()` per klank |
| Globale limiet | 32 gelijktijdige 3D-stemmen; een nieuwe verdringt de **zachtste of verste** van dezelfde bus |
| Afstandsafkap | buiten `max_distance` niet eens starten (scheelt CPU) |
| Streaming | alle lussen en muziek gestreamd; korte klanken in geheugen, ca. 3 MB totaal voor P1 |
| `AudioStreamPolyphonic` | voor UI-geluiden, niet voor 3D |

## 5. Open vragen voor Axel

| # | vraag | invloed |
| --- | --- | --- |
| 1 | **Originele stemmen en klanken lokaal gebruiken voor privé-spel**, naast nieuwe gegenereerde? Of volledig nieuw/eigen (aanbevolen als de remake ooit gepubliceerd wordt)? Origineel gaat nooit in git en nooit in een build voor anderen | bepaalt of 1c als bron dient of alleen als referentie |
| 2 | Welk **ElevenLabs-plan** was actief op 2026-09-03 (gratis of betaald)? Zonder dat is de licentie van de 62 mp3 onbekend. Voor privégebruik geen probleem; bij publicatie opnieuw genereren of plan vaststellen | herbruik 62 mp3 |
| 3 | Wil je een **luistersessie** (de lijst in 1d) zodat ik de 22050/11025 Hz-aanname, de classificatie van de banken en de PM/PF-lijnen kan vastleggen? | 1b en 1c |
| 4 | **Ouderen**: nieuwe stemmen (ElevenLabs, ca. 16 fragmenten) of m/f met lagere pitch als noodoplossing? | P2 |
| 5 | **Muziek**: ja/nee, en zo ja welke bron (CC0, genereren, eigen)? Het origineel heeft hier geen bestand voor, de cd-audio is niet gevonden | muziekbus |
| 6 | **Bibliotheek**: mag ik CC0 downloaden (Freesound-inlog nodig) of lever jij een map? Sonniss GDC-bundels zijn groot (meer dan 30 GB) | sectie 3 |
| 7 | De 9 ontbrekende `BBRBANK`-entries: opnieuw laten extraheren (alleen nodig als origineel een bron blijft) | 1a |
| 8 | **Taal**: lijnen zijn nu taalneutraal (geen woorden). Houden we dat, of echte Nederlandse/Engelse zinnen (bijv. "Yes?", "Ja baas?")? Dat kost per taal een set | stemmenset |

## Besluiten van de gebruiker (2026-10-29)

| Vraag | Besluit |
| --- | --- |
| Originele stemmen lokaal | **Ja**, voor eigen gebruik (nooit in git) |
| Muziek | Origineel had muziek, vooral in het menu; **volgende fase** |
| Woorden | Originele stemmen hebben herkenbare Engelse woorden; beasts-src heeft woordloze gegenereerde klanken |
| Bron per geluid | **Schakelbaar tussen origineel en gegenereerd** (instelling), zodat het origineel later volledig uit te sluiten is. AudioManager kiest per geluids-id uit `origineel/` of `eigen/`; ontbreekt een eigen variant, dan valt hij terug op het origineel (alleen in de lokale build) |

## 6. Wat er nu in zit (2026-10-30, missie 1)

`spel/view/geluid.gd`: een Node, in `main.gd` aangehaakt; leest sim en view, wijzigt niets. Geen autoload (de plan-`AudioManager` uit 4a is dit bestand). Bussen worden in code gemaakt (`Geluid.BUSSEN`: Master 0, Effecten -2, Stemmen 0, Omgeving -6 dB; limiter -1 dB op Master). Pool 24 x `AudioStreamPlayer3D` + 8 x 2D, oudste wordt verdrongen; buiten `max_distance` start niets. `AudioListener3D` op het camerabrandpunt + 1,5 m. Werk op Effecten -3 dB per 10 m camera-afstand boven 20 m. Pauze zet Effecten en Stemmen stil (`stream_paused`); dierengeluid volgt `tempo`. Met `--write-movie` stil (lek bij afsluiten). `--geluid-log` print elke klank.

| geluid | trigger | bron |
| --- | --- | --- |
| Selectie m/f/b/g (4 elk) | nieuwe id in `Bestuur.gekozen`, alleen de leider (dichtst bij brandpunt) | B `voice_select_*` |
| Bevel m/f/b/g (4 elk) | nieuw `bevel` (`loop/werk/claim/gilde/vecht`) bij een gekozen dorpeling binnen 0,35 s na linkerklik | B `voice_order_*` |
| Ouderen | m/f met pitch 0,9 (noodoplossing 4c) | B |
| Lokroep koe | `koe_geclaimd` (eigen), dichtste volwassene | B `voice_cattle_*` |
| Hamer / zaag (20 %, hout) / houweel (akker) | `Bumpkin.impact(&"bouwen")` | B `voice_build_0/1`; G zaag_0/1, houweel_0..2 |
| Sikkel, oogst | `bezig` start met `klus_tegel`; `draagt` wordt graan | G sikkel_0..2; B `voice_crop_0` |
| Melken, eieren rapen | `bezig` start met `melk_koe` / `raap_kip` | B `voice_milk_0`, `voice_eggs_0` (+ G tok) |
| Munt | `verkocht` (3D bij de deur) | B `voice_coin_0` |
| Levering | `geleverd`, zacht | G plaats |
| Plan geplaatst / gebouw klaar | `plan_gezet` (2D) / `plan_klaar` (2D klokje, hek en weg alleen een tik) | G plaats, klaar |
| Poort open/dicht | `poort_gewisseld` (3D) | G poort_open/dicht |
| Missie geslaagd/verloren | `missie_einde` | G missie_geslaagd/verloren |
| UI-klik | `pressed` van elke `BaseButton` (via `node_added`, geen wijziging in bouwmenu/hud) | G klik |
| Koe loeit (3D) | per koe elke 35 tot 90 s sim-tijd | B `voice_moo_0/1` |
| Kip tokt (3D) | per kip elke 10 tot 30 s; 12 % de lange mp3 | G tok_0..3; B `voice_cluck_0/1` |
| Kampvuur (3D-lus, 4/30 m) | altijd | G vuur |
| Golven (3D-lus) | 5 spelers op de dichtste kustpunten (zee-tegel met landbuur, 1 per 6x6), elke 0,5 s; zachter bij ijs | G golven |
| Wind (2D-lus) | altijd; harder in herfst/winter, bij regen en uitgezoomd; winter pitch 1,12 | G wind |
| Regen (2D-lus) | `regent()` | G regen |
| Krekels (2D-lus) | nacht, niet bij regen; lente 0,35 zomer 1 herfst 0,6 winter 0 | G krekels |
| Vogels (3D one-shot, 10 tot 25 m) | dag, niet bij regen; dichtheid 1 / 0,8 / 0,35 / 0 | G vogel_0..5 |
| Uil (3D, 20 tot 35 m) | nacht, niet bij regen, elke 20 tot 60 s | G uil_0/1 |
| Wolf gromt (3D) | per wolf elke 9 tot 22 s sim-tijd, en bij `wolf_erbij` | G wolf_grom_0/1 |
| Wolf jankt | `wolf_geraakt` (pitch 1,2), `wolf_dood` (0,85) | G wolf_jank |
| Wolf hapt | `koe_weg` (+ angstige loei, pitch 1,25), `dorpeling_geraakt` met oorzaak wolf | G wolf_hap_0/1 |
| Steen worp / inslag | `steen_gegooid` / `Bumpkin.impact(&"steen")` bij de dichtste wolf | G worp_0/1, steen_0..2 |
| Zwaard | `zwaard_slag` (zoef) / `impact(&"aanval_zwaard")` (klank) | G worp, zwaard_0/1 |
| Geraakt, dood | `dorpeling_geraakt` (hoogstens 1 per 0,6 s: vuur raakt elke tik) / `dorpeling_dood` (lage klok) | G raak_0/1, dood |
| Geboorte | `dorpeling_erbij` | G plop |
| Drinken | `gedronken` (put, missie 3) | G water_0/1 |
| Munten tellen | `voorwerp_afgeleverd` (5 munten, 0,09 s uit elkaar), `kas_beloning` (4, 2D) | B `voice_coin_0` |
| Ontploffing | `ontploffing` (missie 4, alleen als het signaal bestaat) | G boem |

Bron **B** = beasts-src `app/src/main/res/raw/` (privé repo; ElevenLabs-mp3, licentie open, zie 2; de 7 wav eigen werk). Gekopieerd door `spel/audio/haal_beasts.ps1` (vanuit `sync.ps1`) naar `spel/assets/audio/beasts/`, **niet in git** omdat het Apps-repo publiek is. **ffmpeg sinds 2026-10-30** (winget `Gyan.FFmpeg`): `haal_beasts.ps1` maakt van elke mp3 een `.ogg` (mono 44,1 kHz, Vorbis q4, -16 LUFS, piek -1 dBTP; 62 stuks, 2,1 MB mp3 wordt 0,9 MB ogg); `geluid.gd` neemt de ogg als die er is, anders de mp3. Bron **G** = eigen synthese, `spel/audio/maak_geluid.py` (numpy, `py -3.10`; Python 3.12 heeft geen numpy), 32 wav, 22050 Hz mono, 3,1 MB, deterministisch, lussen naadloos (circulair gefilterd), in git in `spel/audio/eigen/` (51 wav sinds 2026-10-31, de nieuwe achteraan in `__main__` zodat de oude byte voor byte gelijk blijven). Rechtenvrij, eigen werk. **Niets uit het origineel** (niet beluisterd, niet gekopieerd). Fallback: een niet-geïmporteerd bestand laadt via `load_from_file`; een ontbrekend bestand blijft stil met één melding. Test: `test/audio_test.gd` (101 klanken met beasts-src, plus de muziekspeler).

**Nog niet:** voetstappen (3b), koebel, kauwen, donder, wind door dennen, bronklank (kabbelen), schaap, baby-gehuil, eigen oudere stemmen, stem bij geraakt/dood (origineel heeft die), volume per bus behalve muziek, schakelaar origineel/eigen uit de besluiten, sidechain-ducking, mislukte plaatsing, kasteller-tik bij elke verkoop. Synthese is plaatshouder-kwaliteit; vervangen door CC0 zodra downloaden mag (5, vraag 6).

## 7. Muziek (2026-10-31)

### 7a. Wat het origineel deed

Bron: openbumpkins (decompilatie van `BEASTS.EXE`, GPLv3; `src/bridge/session_controls.c`, `cd_control.c`, `statistics.c`, `startup.c`, `world.c`, `native/cd.c`), RaZLeN-patch README, `onderzoek.md`. **Niets beluisterd; de cd zelf is hier niet** (laptop-share offline, geen image op deze pc).

| wat | detail | zekerheid |
| --- | --- | --- |
| Formaat | **7 cd-audiotracks** (2 tot 8; track 1 = data), 44,1 kHz stereo, James Hannigan. Geen muziek in de spelbestanden | goed |
| Afspelen | MCI: `open cdaudio`, `set time format tmsf`, `play cdaudio from N` (zonder `to`), `close` | goed |
| Hoofdmenu | **track 2**, gestart bij het binnenkomen van het menu; ook de outro (campagne uit) | goed |
| Briefing | **track 3** zolang het briefingvenster open is (`bb_mission_popup_visibility_entry`); dicht = stop | goed |
| In de missie | **geen muziek**: alleen effecten, stemmen, omgeving | goed (geen andere aanroep gevonden) |
| Gewonnen/verloren | geen muziek: een van drie stemfragmenten (`bb_faction_end_state_entry`) | goed |
| Tracks 4 tot 8 | door de exe **niet** aangeroepen; vermoedelijk alleen voor een cd-speler of de FMV | **[?]** |
| Lus | **nee**: een vaste duur per track in de exe (2: 67 s, 3: 109 s, 4..8: 100, 285, 71, 76, 59 s), daarna `stop`. Het menu viel na 67 s stil | goed |
| Demoversie | speelt altijd track 2 | goed |
| Volume/opties | geen muziekoptie in het spelmenu gevonden; volume via de Windows-mixer. De RaZLeN-patch heeft een "muziek uit" in zijn launcher | redelijk |

### 7b. Wat er nu in zit

`spel/view/muziek.gd` (`class_name Muziek`): een Node onder de **root** (niet in `main.tscn`), zodat hij het herladen van de scène door start- en pauzemenu overleeft. Twee `AudioStreamPlayer`'s op bus `Muziek` (onder Master, zelf aangemaakt), overvloeien 1,5 s. `main.gd` zet de context op drie plekken: startmenu `menu`, missie laden `briefing` (ook als laadscherm), na de HUD `volg(hud, w)`: briefing dicht = `missie`, `missie_einde` = `gewonnen`/`verloren`. Scenario's en `--write-movie`: geen muziek.

| context | track | lus | origineel |
| --- | --- | --- | --- |
| menu | 2 | ja | 2, een keer (67 s) |
| briefing | 3 | ja | 3, tot de briefing dicht is |
| missie | afspeellijst 4..8, elk een keer, dan 30 s stilte, 0,45 x volume (besluit gebruiker 2026-10-31) | nee | stil |
| gewonnen, verloren | stil | - | stil |

Dempen: **M** overal, met of zonder Shift (besluit gebruiker 2026-10-31; de molen kreeg **Z**), en een getekende noot-knop rechtsboven in het pauzemenu. Volumeschuif onderaan in het pauzemenu, **alleen pc** (op touch maakte de extra rij het paneel te hoog voor de 48 dp-knoppen op 1600x900; daar het toestelvolume). Volume en dempen in `user://muziek.cfg` (onleesbaar = standaard 0,7, niet gedempt).

Bestanden: `spel/assets/audio/muziek/track02.ogg .. track08.ogg`, **niet in git** (`assets/` staat in `.gitignore`). `spel/audio/haal_muziek.ps1` (vanuit `sync.ps1`) zoekt de eigen cd-rip in `lokaal/muziek/` of op de laptop-share, als `TrackNN.*` (RaZLeN-naam) of `beastsNN.wav` (bchunk/openbumpkins), en maakt stereo 44,1 kHz Vorbis q5, loudnorm -18 LUFS, piek -1 dBTP. Ontbreekt een track, dan blijft die context stil met een melding. Test: `test/audio_test.gd` (stille testtracks: wissel, overvloeien, doorspelen, dempen, volume, bewaren).

### 7c. Open vragen

| # | vraag |
| --- | --- |
| 1 | **De cd-tracks**: heb je een rip (of de cd)? Zet `Track02..Track08` in `lokaal/muziek/` en draai `sync.ps1`. Niet van internet gehaald |
| 2 | ✅ 2026-10-31: menu en briefing blijven lussen |
| 3 | ✅ 2026-10-31: tracks 4 tot 8 zacht in de missie (afspeellijst met pauzes), afwijking van het origineel |
| 4 | ✅ 2026-10-31: M = muziek overal, molen op Z |
| 5 | Voor publicatie mag het origineel er niet in: eigen of gegenereerde muziek (zie `onderzoek.md`: Stable Audio 3 lokaal of Eleven Music) |
