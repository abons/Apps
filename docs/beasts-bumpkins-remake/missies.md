# Alle 30 missies van het origineel (Beasts & Bumpkins, 1996)

Gedecodeerd uit `MISSIONS.BOX` (`M1.MIS` .. `M30.MIS`, 30 stuks) en `MISTEXT0.BOX` (briefings en hints) met de Python-port van `MAPFile.cs`, uitgebreid met een decoder voor de staart (zie "Bestandsformaat"). Missie 1 staat apart in `map1.md`.
Alleen tekst: de afgeleide gegevens (`SC/missies/m<nn>.json`, `m<nn>_layout.png`) staan lokaal in de scratchpad (`SC` = `C:/Users/Axel/AppData/Local/Temp/claude/E--werk-androidApps-Apps/16e99493-ac86-47c7-921f-1d215c266f51/scratchpad/`) en gaan nooit in git (auteursrecht). Briefings zijn hier met eigen woorden samengevat.

## Verhaal in het kort

Lord Mildew is door de oude koning Roland naar het eiland **Aorta** verbannen (M1), keert terug op het vasteland van **Lokyadore** (M2-M3), Roland sterft (M4) en de **Dark Lord** vult het machtsvacuüm met zombies (M5 en verder). Daarna volgen rivaliserende heren en dorpen, een reeks tovenaars-, sleutel- en schatpuzzels, een bruiloft (M24) en twee verdedigings- en slotmissies tegen de Dark Lord (M28-M30). Twee eindteksten: `m31` (de Dark Lord leeft nog, de vloot is gezonken, alleen het vlaggenschip rest: verlies-/vervolgscène) en `boutro` (overwinning: Lokyadore bevrijd, nieuwe landen over zee). Missies hebben in het bestand geen eigen naam ("Mission 1", "10", "Mission 12", wisselend): de namen in de tabel zijn onze korte labels. Bruikbare eigennamen zitten in de dorpsvlaggen (zie "Antwoorden").

## Tabel

Kolommen: nr, label, grootte van het bruikbare gebied in tegels (alle kaarten zijn 192 x 192, de rest is leeg), landtegels (zonder water; thuiseiland = aaneengesloten land rond de eigen vlag), terrein in % van het land (rots = rots + rotsrand, rest = aarde/zand/overig; water in % van het niet-lege gebied; bos = tegel-gebonden dennen, zie "Antwoorden"), startdorpelingen en -kas, doel (W win, V verlies; "telling >5" betekent dat het bestand `> 5` vergelijkt), nieuw, zwaarte. "Eigenaar 1-3" zijn AI-dorpen, "eigenaar 4" wilde/neutrale objecten en soldaten.
Typen dorpeling: m = man (1), v = vrouw (2), jongen (13), meisje (14), `t7`/`t8`/`t16`/`t19`/`t10` = krijgers (zie "Antwoorden"), tovenaar (9), belastinginner (5), bommenwerper (17), prins/prinses (32/33), monnik (21), oude man? (3).

| nr | label | gebied | land (tegels) | terrein | start | doel | nieuw | zwaarte |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | Aorta (verbannen) | 76x87 | 2.238 (thuiseiland 1.714) | gras 50, bos 2, rots 27, rest 21; water 52 % | 2 m, 2 v, 1 jongen, 1 meisje; kas 10.000 | W: 6 dorpelingen (telling >5) en 4 koeien (>3). V: minder dan 2 dorpelingen. | Boerenhut, bouwersgilde (bouwer 2x sneller), bakkerij, boerderij, kippenhok, koeien claimen, hek en poort, zilveren beker. Seizoenen. | Laag. Geen vijanden. |
| 2 | Terug op het vasteland | 83x85 | 4.014 (thuiseiland 3.986) | gras 36, bos 27, rots 23, rest 14; water 14 % | 4 m, 4 v, 2 jongen; kas 6.999 | W: kas >10.000. V: <2 dorpelingen. Wolven lopen los. | Wolven (13,23) die kinderen en vee pakken; omheining helpt; prijzen/geluk; pensioen; items zoeken (goud, drankjes). | Laag. 3 wolven. |
| 3 | Gouden kelk van Barathkar | 108x126 | 7.527 (thuiseiland 7.520) | gras 39, bos 2, rots 54, rest 5; water 10 % | 3 m, 2 v, 1 t7; kas 7.000 | W: kas >25.000 (telling >24.999); de bewaakte gouden kelk naar de vlag is de snelle route. V: <2. | Gildelimiet 6 leden; putten; voetvolkgilde al aanwezig; bewaakte gouden kelk; twee wolf-soorten (13,29),(14,24). | Middel. 7 wolven; groot rotsgebied. |
| 4 | Beker van Vervulling | 164x138 | 9.723 | gras 40, bos 30, rots 17, rest 12; water 13 % | 2 m, 2 v; kas 8.000 | W: Beker van Vervulling vinden; sleutel opent poort, de zilveren beker is een val (tin), echte doel = triggerplek (41,11). V: <2. | Magische sleutel en poort; valstrik-beker; eerste (21,18)-wezens (vermoedelijk apen). | Middel. 4+3 wezens; grote bossen. |
| 5 | Zombiedorp en heilig zwaard | 85x110 | 5.936 | gras 40, bos 2, rots 56, rest 2; water 0 % | 4 m, 2 v; kas 8.000 | W: heilig zwaard (52,98) halen, zombiegraf (74,37) slopen, dorp >10 mensen. V: <2. | Zombies (eigenaar 4, type 7), graven en zombiegraf, heilig zwaard; eerste wegversperring met voetvolkgilde. | Middel. 6 zombies, 30 muren. |
| 6 | Parpton | 149x164 | 12.174 (thuiseiland 11.776) | gras 42, bos 13, rots 35, rest 10; water 10 % | 2 m, 2 v, 1 tovenaar; kas 6.500 | W: Parpton (eigenaar 2, vlag 132,66) uitroeien. V: alle eigen mensen dood. Vallen. | Eerste vijandig dorp (Parpton); spijkervallen en mijnen; tovenaar met spreuken; bouwbalk scrollen; toren. | Middel-hoog. 5 vijandelijke dorpelingen, 26 vallen. |
| 7 | Oorlogskas | 137x113 | 7.953 (thuiseiland 3.233) | gras 55, bos 8, rots 14, rest 23; water 16 % | 1 m, 1 v, 1 jongen, 1 meisje; kas 8.200 | W: kas >26.000 (meldingen bij 15k en 24k). V: alle mensen dood. Kelkenpuzzel met 2 gouden + 1 zilveren kelk. | Kerk (priesters, genezing, huwelijken); kelkenpuzzel; beloningsberichten bij 15k/24k/26k. | Middel. Geen vijandelijk dorp; 6 wezens, 14 vallen. |
| 8 | Wormton en kas | 88x145 | 8.168 | gras 58, bos 11, rots 17, rest 14; water 10 % | 2 m, 2 v, 1 oude man?; kas 6.000 | W: kas >14.000 en Wormton (eigenaar 1) uitroeien. V: <2. | Wormton (eerste echte rivaal naast Parpton); geldplicht plus aanval. | Middel. 4 vijandelijke dorpelingen, kas 6.000. |
| 9 | Tovenaarsleerling | 131x147 | 10.342 (thuiseiland 10.220) | gras 44, bos 14, rots 23, rest 19; water 24 % | 2 m, 2 v, 1 oude man?, 1 tovenaar; kas 8.000 | W: leerling (villager 201, 169,161) levend naar tempel (82,96); sleutel (119,159) opent poort (98,102). V: leerling sterft. | Tovenaarsleerling (type 9), tempel, sleutel/poort, vijandelijk dorp Wormton. | Hoog. 6 vijanden, 14 vallen, 60 muren. |
| 10 | Toren der Kennis | 132x107 | 6.969 | gras 31, bos 65, rots 0, rest 4; water 0 % | 2 m, 2 v; kas 9.000 | W: toren (162,131) slopen; 6 reuzen bewaken hem; monnikenwinkel verkoopt voor 10.000 (o.a. onzichtbaarheid). V: <2. | Monnikenwinkel (verkoopt 3 items), reuzen (16,27)/(22,25), donker altaar, onzichtbaarheidsmantel, bos zonder water, hendels. | Hoog. 281 muren, 11 wezens (6 reuzen) en geen water. |
| 11 | Vijandelijke enclave (Bearton) | 121x101 | 7.125 | gras 62, bos 6, rots 19, rest 13; water 25 % | 2 m, 2 v; kas 10.000 | W: vijandelijk dorp (eigenaar 1) uitroeien; sleutel (58,9) opent poort naar Fontein der Jeugd (50,22). V: alle eigen mensen dood. | Boogschuttersgilde, uitkijkpost, ridderlijk gilde, stadhuis/belastinginner, Fontein der Jeugd, tovenaar Wilberforce. | Middel. 4 vijandelijke dorpelingen. |
| 12 | Grens: BomberMan | 131x142 | 12.835 (thuiseiland 12.556) | gras 48, bos 37, rots 8, rest 7; water 7 % | 2 m, 2 v, 6 t8, 1 bommenwerper; kas 10.000 | W: vijandelijke uitkijktoren (55,128) slopen met eigen BomberMan (villager 730, type 17), die op een eiland vastzit tot een trigger hem bevrijdt. V: eigen toren (56,41) of BomberMan weg, of <2 mensen. | BomberMan (type 17), trigger-vlakken (klasse 87), 5 spawners (vijandelijke soldaten komen na). | Hoog. 16 vijandelijke soldaten + 5 spawners. |
| 13 | Ringworm en de pest | 115x182 | 9.081 (thuiseiland 8.919) | gras 37, bos 11, rots 39, rest 13; water 42 % | 2 m, 2 v; kas 10.000 | W: Ringworm (eigenaar 2) uitroeien via de pest: spreukrol bij monnik voor 10.000 kopen; geen oorlog. V: alle eigen mensen dood. Timer 25.200. | Gevangenis (pikenier), misdaad, pest-spreuk, kloosters met monniken (type 21), rivaal-lord. | Middel. Dorp met 6 vijandelijke bewoners, veel water (42 %). |
| 14 | Vloek van de zombies | 171x162 | 11.483 (thuiseiland 9.300) | gras 52, bos 6, rots 21, rest 20; water 29 % | 2 m, 2 v, 2 t7; kas 8.000 | W: 18.000 ticks overleven (zombiegolven, timer 32.400 voor de vloek). V: <3 dorpelingen of kerk (112,67) valt. | Zombievloek, zieken verzorgen, kerk beschermen; doodskisten, graven, zombiegraf. | Middel. Tijdgebonden (18.000 ticks). |
| 15 | Blagton en de toverrollen | 118x164 | 11.776 (thuiseiland 11.743) | gras 41, bos 4, rots 50, rest 5; water 11 % | 2 m, 2 v; kas 6.000 | W: Blagton (eigenaar 3) uitroeien; hendels openen de toverkluis met spreuken. V: alle eigen mensen dood. | Toverrollen en spreuken, tovenaarsgilde voor de speler, hendels; zeer groot vijanddorp (17 vijandelijke mensen, 36 vallen). | Hoog. 17 vijandelijke mensen, 36 vallen. |
| 16 | Big Pockets Barry | 137x143 | 7.777 | gras 28, bos 20, rots 38, rest 14; water 16 % | 3 m, 3 v; kas 8.000 | W: Barry (villager 13, 19,31) via 2 sleutel-poortparen naar het stadhuis (91,117) brengen. V: Barry dood of timer 36.000 (waarschuwing bij 34.200). | Belastinginner Barry, stadhuis, sleutel/poort-ketens, tijdslimiet 36.000. | Hoog. Tijdlimiet; 7 vijanden + 3 spawners. |
| 17 | Schatkaart (40.000) | 97x109 | 7.429 | gras 44, bos 19, rots 26, rest 11; water 0 % | 2 m, 2 v; kas 5.000 | W: kas >40.000; schat via 7 graafplekken (schop) en dode reus. V: <2. | Schatkaart met 7 graafplekken en schop, dode reus; slechts 5.000 startkas. | Middel. Armoede (5.000) en een grote reus. |
| 18 | Koe naar de heler | 92x121 | 6.746 | gras 47, bos 31, rots 0, rest 22; water 0 % | 2 m, 2 v; kas 10.000 | W: een koe naar de heler (villager 46, 152,115) brengen; alle koeien zijn dood (explosiekoeien). V: alle mensen dood. | Explosiekoeien (alle koeien dood), heler (monnik), vee zoeken; 3 wezen-spawners. | Middel. Geen vee; 13 vijandelijke mensen; 3 spawners. |
| 19 | Biggunton en Sykeston | 136x165 | 11.459 (thuiseiland 11.271) | gras 50, bos 20, rots 19, rest 11; water 17 % | 2 m, 2 v; kas 8.000 | W: Biggunton (eigenaar 1) en Sykeston (eigenaar 2) uitroeien. V: alle eigen mensen dood. | Twee vijandelijke dorpen tegelijk; geen extra items. | Hoog. Twee dorpen (10 vijandelijke mensen). |
| 20 | Fast Fingers Freddy | 134x166 | 12.483 (thuiseiland 7.054) | gras 34, bos 36, rots 11, rest 20; water 18 % | 2 m, 2 v, 1 belastinginner; kas 8.000 | W: Freddy (villager 13 owner 3, 57,113) doden, sleutel (49,51) naar poort (24,131), goud (23,127). V: alle mensen dood. | Dief Freddy, stadhuis voor de speler, bandietenschuilplaats met sleutel. | Hoog. 14 vijandelijke mensen; rovers. |
| 21 | Goluckyton | 141x139 | 9.511 (thuiseiland 9.274) | gras 44, bos 18, rots 30, rest 8; water 9 % | 1 t0, 1 m, 2 v, 1 t64; kas 7.000 | W: Goluckyton (eigenaar 3) uitroeien; tovenaarsgilde van Chubbston slopen levert sleutel op; hendel en poort in de stad. V: alle mensen dood. | Brouwerij (cider), appelbomen, stallen (cavaliers) en minstreelsgilde; stad Goluckyton met poort en hendel; 19 vijandelijke gebouwen. | Hoog. 19 vijandelijke gebouwen, 59 muren, 5 vijandelijke mensen. |
| 22 | Graaf Drapoga | 149x129 | 9.138 (thuiseiland 7.500) | gras 45, bos 2, rots 47, rest 7; water 10 % | 3 m, 2 v, 1 t19; kas 7.000 | W: crucifix (56,103) via kelk bij de monniken halen en vampier (creature 3, 148,124) doden. V: alle mensen dood. | Vampier (18,31), crucifix, monniken, kelk-aflevering; 5 spawners; 71 muren. | Middel-hoog. 5 spawners, vampier, 71 muren. |
| 23 | Goud en vee | 190x153 | 14.783 (thuiseiland 13.909) | gras 56, bos 9, rots 18, rest 17; water 17 % | 2 m, 2 v, 1 jongen, 1 t96; kas 8.000 | W: kas >40.000 en >15 koeien. V: alle mensen dood. | Rijke kaart: 17 goudbuidels, 11 koeien, vijand Wigginston (eigenaar 1) met 6 mensen. | Middel. 6 vijandelijke mensen, grote kaart. |
| 24 | Bruiloft van Lurkio | 121x94 | 6.789 | gras 45, bos 31, rots 5, rest 19; water 7 % | 8 t8, 1 prins, 1 prinses; kas 0 | W: prins (698) en prinses (694) naar kerk (112,101) brengen; wizard Wilberforce bij rots (162,113). V: een van beiden dood. Startkas 0. | Prins en prinses (types 32/33), Wilberforce, 8 eigen krijgers (type 8) en 0 gouden startkas; geen dorp. | Hoog. Startkas 0; 8 vijandelijke krijgers en 29 vallen. |
| 25 | Drie gebouwen (tijdslimiet) | 84x93 | 3.982 | gras 10, bos 42, rots 1, rest 48; water 8 % | 2 t7, 4 t8, 1 t10, 2 t16, 5 t19; kas 8.000 | W: 3 vijandelijke gebouwen (voetvolk-, boogschutters-, ridders-gilde) veroveren. V: timer 4.320 of alle mensen dood. | Alleen krijgers (14 stuks): voetvolk 8, ridders 19, boogschutters 16, type 7 en 10; kasteelkaart zonder eigen dorp (zelfde kaart als M28). | Hoog. Tijdlimiet 4.320 ticks (1,5 seizoen), 19 verdedigers (eigenaar 4). |
| 26 | Reus Deavo | 169x171 | 16.701 (thuiseiland 16.148) | gras 41, bos 10, rots 41, rest 7; water 11 % | 2 m, 2 v, 1 t8; kas 15.000 | W: reus Deavo (creature 95, 66,14) doden met bevrijde ridder Thrice (villager 97, naar kraal 79,26); spreuk kost 20.000. V: Thrice dood of <2. | Reus Deavo, bevrijde ridder Thrice, spreuk Teleportatie, monnik in kraal; hoogste startkas (15.000). | Hoog. Reus Deavo, 168 muren. |
| 27 | Lord Randybar (Grymton) | 158x175 | 9.557 | gras 45, bos 10, rots 37, rest 8; water 15 % | 3 m, 2 v; kas 8.000 | W: Grymton (eigenaar 2) uitroeien; Gruffton (eigenaar 1) is de tweede stad en meldt het als het valt. V: alle mensen dood. | Twee rivalen (Gruffton owner 1, Grymton owner 2); 25 kippen; geen items. | Hoog. Twee dorpen (18 vijandelijke mensen). |
| 28 | Verdediging tegen de Dark Lord | 84x93 | 3.982 | gras 22, bos 42, rots 1, rest 35; water 8 % | 12 m; kas 8.000 | W: alle aanvallers (eigenaar 4) verslaan; 1 seizoen (2.880 ticks) voorbereiding. V: een van 6 gilde-/kerkgebouwen valt of alle mensen dood. | Alleen 12 mannen en 6 gebouwen; 8 spawners met types 16,8,7,19 (de gastheer van de Dark Lord); kaart = M25. | Zeer hoog. 8 spawners; je mag niets verliezen. |
| 29 | Heilige Kelk en Fontein | 166x119 | 11.902 | gras 38, bos 30, rots 29, rest 3; water 1 % | 2 m, 2 v; kas 8.000 | W: zilveren beker (159) naar Heilige Fontein (19,51); doolhof, meisje meebrengen voor het huwelijk. V: alle mensen dood. | Doolhof, vuurvaste ring, doel (target), monniken, put van de Heilige Fontein; reus met kelk. | Hoog. 48 vallen, reuzen. |
| 30 | Slotgevecht (demonen, Parpton) | 192x192 | 28.390 | gras 25, bos 2, rots 70, rest 4; water 5 % | 1 v, 3 t8, 2 tovenaar; kas 8.000 | W: Parpton (eigenaar 2) slopen; demonen via donker altaar (164,59) vraagt een offer van een eigen dorpeling; 4 vlammen-timers van 36. V: alle mensen dood. | Laatste kaart: 28.390 landtegels (rots 70 %), vijanddorp Parpton (eigenaar 2) en 2 tempels; doolhof. | Zeer hoog. 33 vijandelijke mensen, 23 vijandelijke gebouwen, 209 muren, 25 vallen. |


Alle missies beginnen met 4 tot 14 eigen mensen en (op M24, M25, M28 en M30 na) een eigen vlag, kampvuur en bron. M1 begint zonder gebouw; vanaf M2 staan er 1-2 voorgebouwde hutten en soms een boerderij, put of gilde. M24, M25 en M28 hebben geen dorp: alleen krijgers (M24 en M25) of 12 mannen met 6 vaste gebouwen (M28); M30 heeft eigen gebouwen maar geen eigen vlag. M25 en M28 gebruiken dezelfde kaart (zelfde 3.982 landtegels, eigenaarverdeling anders).

## Campagne-opbouw (wat komt wanneer)

| fase | missies | wat er bij komt |
| --- | --- | --- |
| 1. Basis | 1-3 | M1: hut, bouwersgilde, bakkerij, boerderij, kippenhok, koeien, hek en poort, seizoenen. M2: wolven (komen op kinderen en vee af), geld als doel, pensioen, prijzen en geluk. M3: gildelimiet 6, putten, bewaakte gouden kelk, geldmissie 25.000. |
| 2. Eerste vijand | 4-8 | M4: magische sleutel en poort, trapbeker. M5: zombies, zombiegraf, heilig zwaard. M6: eerste vijandig dorp (Parpton), vallen en mijnen, tovenaar en spreuken. M7: kerk (priesters, huwelijk), goud-doel met meldingen. M8: rivaal Wormton plus geldeis. |
| 3. Puzzels en nieuwe gilden | 9-17 | M9 leerling-tovenaar naar tempel. M10 monnikenwinkel (items voor 10.000), reuzen, onzichtbaarheid. M11 boogschutters- en ridderlijk gilde, uitkijkpost, stadhuis (belastinginner), Fontein der Jeugd. M12 BomberMan. M13 gevangenis (pikenier, misdaad) en pestspreuk. M14 zombievloek (overleven). M15 toverrollen en tovenaarsgilde. M16 gegijzelde belastinginner met tijdslimiet. M17 schatkaart met 7 graafplekken. |
| 4. Variatie | 18-23 | M18 explosiekoeien en heler. M19 twee dorpen tegelijk. M20 dief Freddy. M21 brouwerij (cider), stallen (cavaliers, alleen ridders), minstreelsgilde en een ommuurde stad. M22 vampier en crucifix. M23 goud en vee (40.000 en 15 koeien). |
| 5. Eindspel | 24-30 | M24 prins en prinses naar de kerk. M25 drie gebouwen veroveren met tijdslimiet. M26 reus Deavo. M27 twee rivalen. M28 een seizoen om je te verdedigen tegen de gastheer van de Dark Lord (8 spawners). M29 doolhof, Heilige Kelk en Fontein. M30 demonen oproepen en Parpton slopen. |

Gebouwen die de speler zelf al op de kaart krijgt (eigenaar 0, eerste missie): boerderij M2; hut, put, voetvolkgilde M3; bouwersgilde M4; kerk M7; bakkerij en toren M12; gevangenis M13; tovenaarsgilde M15; stadhuis M16; boogschuttersgilde M23; ridderlijk gilde M28 (alleen bij vijanden: brouwerij M13, tempel M9, ridderlijk gilde M21, uitkijkpost en stallen M30). Wat de speler zelf mag bouwen staat niet in de kaart, maar in een aparte voortgangstabel van het spel (niet gevonden); de hints (`MISn-k.TXT`) zijn daarom de bruikbaarste bron: M1 hut, bouwersgilde, bakkerij, boerderij; M3 put; M7 kerk; M11 boogschutters, uitkijkpost, ridders, stadhuis; M13 gevangenis; M21 brouwerij, stallen, minstreel.

Timing: ticks. M28 geeft "een seizoen" als 2.880 ticks, dus een jaar is ongeveer 11.520 ticks en de hints van 360 ticks komen een achtste seizoen na de start. Tijdsloten: M16 36.000 (waarschuwing bij 34.200), M25 4.320, M14 18.000 (overleven) en 32.400 (vloek), M13 25.200.

## Bestandsformaat (`*.MIS`)

Alles little endian. Alle 30 kaarten zijn 192 x 192.

| offset | inhoud |
| --- | --- |
| 0 | `"MAP"`, 5 bytes versie, 64 bytes naam (bv. "Mission 1", "10"), `u8 size_x`, `u8 size_y` |
| 74 | per rij: `i32 n` plus RLE-blok (byte 0 = N nullen volgen, anders letterlijk) dat ontrafelt tot `size_x x 12` bytes. Tegel van 12 bytes: `u8 tex`, `u8 road`, `u8 owner` (grondgebied; 0 = speler/niets, in M6 2 voor het vijanddorp), `i32 m1` (0x01000000 = bezet door object), `u8 u1`, `i32 m2` (0x4000 = standaard, 0x400000 e.a. = overige vlaggen) |
| daarna | `i32 ptr_objects`, `i32 ptr_smth2` (heap-adressen, betekenisloos), `i32 count` (altijd 5000 slots) |
| per slot | `u8 flag` (0 = leeg), `i32 n`, RLE-blok van 0x13A bytes. Extra payload erachter: pad-buffer (lengte in byte 0xF0) als `i32@236 != 0`, 32-byte naam bij klasse 98 (vlag), 2 bytes als `i32@56 != 0` |
| staart | 18-22 kB, zie hieronder |

Object (`0x13A` bytes): `0xD4` klasse-id (zie `objects_list.txt`), `0xD8/0xD9` x en y (tegel), `0xF7` eigenaar (0 speler, 1-3 AI-spelers, 4 neutraal/wild), `0xF4` subtype (bij klasse 103 het mensensoort, zie "Antwoorden"), `0xF3` groep (bij 104 het wezensdeel van het paar), `0xEA` toestand, `0x6E` gezondheid (u16), `0x3C` naam (bij vlag: dorpsnaam; bij dorpeling begint voornaam op `0x40` en achternaam op `0x4C`), generator (klasse 171): `0xE7` klasse die hij uitzet, `0xE5/0xE6` getallen (waarschijnlijk begin-/maximumaantal; onzeker), `0xF4` subtype van wat hij uitzet. De slotindex `i` van het object is zijn identiteit voor het script.

Staart, gedecodeerd:
1. **5 spelerrecords van 3328 bytes** (offset 0, 3328, ...). Record 0 is de speler (naam "Enemy" is een sjabloon), 1-3 AI-spelers ("Computer"), 4 is een restrecord. Gevonden: `i16 @ +78` = **startkas** (M1 10.000 .. M26 15.000, M24 0, M17 5.000), `i16 @ +336` = startbevolking (klopt voor alle missies met het aantal eigen dorpelingen), AI-spelers 8.000. De rest (statistiektellers, prijzentabellen, heap-vulling `0xCD`) is runtime-toestand zonder missie-ontwerp.
2. **Scriptgebied** vanaf offset 16.640 (heap-dump van C++-objecten met `0xCD`-vulling). Vervat zijn: conditie-records (hieronder), tekst-acties (`open[mis1-3.txt]` of `[mis1-3.txt]` in records van ca. 298 bytes; de conditie die ze start staat meestal 49 bytes ervoor), en leegte.
3. **Statistiekreeksen**: laatste ca. 300 bytes, 24 labels (Women, Children, Retired, Guildmen, Population, Births, Deaths, Marriages, Retirements, Cash, Income, Outgoings, Tax, Trade, Happiness, Health, Age, Crimes, Convictions, Eggs, Water, Bread, Milk, Cider), in elke missie gelijk.

Conditie-record (gevonden met regex `type 0xCD a b c id 0xCD 01 00 00 00`, `type 205` (16 stuks) zijn lege slots):

| type | betekenis (afgeleid, per voorbeeld getoetst) | velden |
| --- | --- | --- |
| 1 | timer | `a` = ticks |
| 2 en 3 | kas groter dan `b` (2) en een variant (3); doelen staan als N-1: 24.999 = 25.000 | `b` = bedrag |
| 4 | aantal van klasse `b` van eigenaar `a` groter dan `c` (M1: koeien >3, dorpelingen >5; hints: hut, gilde) | `a` eigenaar, `b` klasse, `c` aantal |
| 5 | aantal van klasse `b` van eigenaar `a` kleiner dan `c` (verlies: eigen dorpelingen <2, of een vijandig dorp uitgeroeid: eigenaar 1-3 dorpelingen <1; M25: eigenaar 4 gebouwen <1 = veroverd) | idem |
| 6 | object `a` (slotindex) vernietigd (M28: 6 gilde-/kerkgebouwen; M12 torens) | `a` |
| 7 | object `a` staat op plek (`b`,`c`) | |
| 9 | onbekend | |
| 10 | object `a` komt bij object `b` (sleutel naar poort, prinses naar kerk, leerling naar tempel) | |
| 11 | koop van item (M10 monnikenwinkel) | `a`, `b` |
| 12 | eenheid/voorwerp van klasse `a` raakt object `b` (dorpeling pakt sleutel/goud op, kelk naar vlag, schop bij graafplek) | |
| 13 | eenheid van type `a` bij object `b` (M12 BomberMan bij toren; M25 type 10 bij gebouw) | |
| 14 | object `a` gebruikt (M30 donker altaar) | |

`id` (0-30) is het regelnummer van de regel waartoe de conditie hoort; de uitkomst (win of verlies) van een regel is niet in een herkenbaar veld gevonden. Win en verlies zijn afgeleid uit briefing plus conditie (bv. `<2` eigen dorpelingen in bijna elke missie = verlies). Tekst-acties en `type 4`/`2` zitten niet altijd aan elkaar: de eerste hints (M1: tekst 1-2 .. 1-12) volgen een keten (hut -> bouwersgilde -> bakkerij -> boerderij -> hek en poort -> kippen) plus timers.

## Hints en briefing (M1-M3, 2026-10-30)

**Bron.** Briefing = `Mn.TXT`, hints = `MISn-k.TXT` (MISTEXT0.BOX). Een hint is een regel in het scriptgebied van `Mn.MIS`: conditie-record, dan `01 00 00 00 00 00 00 00 01 00 00 00 01 cd`, een pointer, en de actie `f6 00 06 00 f6 00 00` + `open[misN-k.txt]` of `[misN-k.txt]`. Andere acties in dezelfde vorm: `0x16` kas erbij (M2: 4x timer 6480 -> +1.000), `0x17` object weg, `0x14` met 1 of 2 (vermoedelijk missie gewonnen/verloren: staat bij de win- en verliesregels). Een regel zonder conditie (alleen nullen) vuurt bij de start (M1 `1-12`, M2 `2-1`).
**Keten.** In de data is geen koppeling tussen regels gevonden: elke hint vuurt een keer zodra zijn conditie waar is, timers tellen vanaf de start (aanname). De keten ontstaat doordat elke hint wacht op het gebouw waar de vorige om vroeg. De remake legt hem vast met `na` (melkerij en poort gaan pas open na de molen, dus de 288-tikken-timer van 1-6 mag niet eerder komen dan 1-5).
**Vorm.** Geen screenshot van een hint gevonden; de exe ontbreekt (share axel-laptop niet bereikbaar). Wel in de UI-sprites: `LETSCR` (briefscherm 640x480: bruin perkament, gerafelde rand, paarse lakzegel, links een paal met vastgeprikte brieven) en `MAIL` (opgerold briefje met rood zegel). Remake: briefing en `open`-hints als perkamentbrief midden in beeld (kleuren uit LETSCR), hints zonder `open` als rolletje rechts dat bij een klik opent. Briefing pauzeert de sim, hints niet (eigen keuze). Een `*` voor veel teksten (betekenis onbekend, niet gekoppeld aan `open`).
**Besluiten gebruiker 2026-10-30:** de gebruiker herinnert zich geen hints uit het origineel (de teksten staan wel in MISTEXT0); menu en briefing pauzeerden, de briefing stond op een soort perkamentrol (later eventueel een eigen ontwerp van de gebruiker); hints die wachten op een ontbrekend onderdeel blijven wachten (die onderdelen komen); geen extra triggers voor hints zonder regel (2-2, 2-6): "al spelend leer je"; een gebouw telt pas als het af is.
**Tikken.** 2.880 tikken = 1 seizoen (M28), in de remake omgerekend met `seizoen_s` (270 s): 108 tikken = 10 s.

| hint | trigger (M.MIS) | open | remake | inhoud (eigen woorden) |
| --- | --- | --- | --- | --- |
| M1 briefing | start | | brief, pauze | verbannen naar Aorta; 6 dorpelingen en 4 koeien; eerst kippenhokken, meer hutten = meer kinderen |
| 1-12 | geen conditie (start) | nee | start | twee kippenhokken bouwen |
| 1-2 | timer 108 | ja | timer | boerenhut bouwen |
| 1-3 | aantal hut (2) > 0 | ja | na 1-2 | bouwersgilde; man erheen = bouwer 2x sneller |
| 1-4 | aantal bouwersgilde (69) > 0 | ja | `gereedschapsloods`, na 1-3 | bakkerij voor brood |
| 1-5 | aantal bakkerij (53) > 0 | ja | `molen`, na 1-4 | tarwe zaaien in de lente, oogsten in de herfst; activiteit zelf kiezen |
| 1-6 | timer 288 | ja | na 1-5 | boerderij (melk) plus wei met hek en poort, poort klikken = open/dicht |
| 1-7 | aantal poort (169) > 0 | ja | na 1-6 | wilde koeien claimen, paarse halsband |
| 1-11 | timer 360 | nee | timer | koeien kalven in de lente, houd ze bij elkaar |
| 1-10 | timer 360 | nee | timer (view/prijzen.gd) | prijzen via het goudicoon |
| 1-9 | aantal kip (111) > 1 | nee | `wacht_op` ouderdom | hutten gespreid bouwen voor de levensduur |
| 1-8 | type 12: dorpeling raakt beker (object 6) | ja | `voorwerp` 159 | dat lijkt kostbaar, naar de vlag |
| M2 briefing | start | | brief, pauze | terug op het vasteland; kas boven 10.000; gevaarlijke beesten |
| 2-1 | geen conditie (start) | nee | start | wolven jagen op kinderen en koeien |
| 2-4 | timer 360 | nee | `wacht_op` stilstaan-knop | doet iemand niets: stilstaan-knop |
| 2-3 | timer 720 | nee | timer (sim/handel.gd) | hoge prijzen = ontevreden = korter leven |
| 2-5 | timer 4.320 | nee | `wacht_op` pensioen | ouderen kunnen met pensioen |
| 2-2, 2-6 | geen regel in M2.MIS | | `geen` | hek tegen wolven; verkennen loont |
| M3 briefing | start | | brief, pauze | 25.000 nodig; zoek de bewaakte gouden kelk |
| 3-4 | timer 180 | nee | `wacht_op` put | putten tegen dorst |
| 3-5 | timer 1.080 | nee | `wacht_op` gildelimiet | gilde max 6 leden |
| 3-1 | geen regel in M3.MIS | | `voorwerp` 172 (eigen keuze, patroon 1-8) | dat is de kelk, naar de vlag |
| 3-2 | geen regel | | weggelaten | dubbel van 3-5 |

**Remake:** `spel/data/hints.json` (trigger, `na`, `open`, `wacht_op`, eigen tekst), `spel/sim/hints.gd` (`Hints`, signaal `hint_getoond`, `controleer()` per frame in `main.gd`, niet tijdens pauze), `spel/view/brief.gd` + `view/hud.gd` `zet_hints`. Alleen in gewoon spel en `--scenario=hints`. Test `test/hint_test.gd`, frame `spel/screenshots/missie1_hint.jpg`.

## Antwoorden op de open vragen

| vraag | antwoord |
| --- | --- |
| Object 171 (koe of generator?) | **Generator (spawner).** Het is een onzichtbaar object dat iets uitzet: byte `0xE7` = klasse van het uitgezette, **110 (koe) bij 26 van de 54 generators, 104 (wezen) bij 15, 103 (dorpeling) bij 12**, eenmaal 26. In M1 is het koeien-generator `(118,58)`: er staat nergens een koe-object in het bestand maar de doelstelling is 4 koeien, dus de koeien komen uit deze generator. Overal waar een kaart wolven, ridders of golven vijanden brengt zit een generator (M12 5 stuks, M22 5, M28 8 stuks die vier soorten krijgers voortbrengen). De README "171 = Cow" klopt daarmee half: het is de koeienbron. |
| Dorpeling `sex` 13 en 14 | **Kinderen: 13 = jongen, 14 = meisje.** Bewijs: M1 start met precies 2 mannen, 2 vrouwen, een 13 en een 14 (een volledig gezin); 13 draagt mannelijke namen (Quentin, Harry, Wesley), 14 vrouwelijke (Morticia, Victoria, Rose); vijandige gezinnen (M11, M18, M23) bestaan uit 1, 2, 13, 14 (+2). Sprites `kidm`/`kidf`, `d_kidm`/`d_kidf`. Er is geen apart leeftijdsveld voor kinderen: kind of volwassen zit in het type (0x8C = 5 bij kinderen, 3 bij volwassenen; 0xCE = 11 tegen 12). Overige typen: 1 man, 2 vrouw, 3 vermoedelijk oude man (1 per dorp, mannelijke namen), 5 belastinginner (M16 Barry), 9 tovenaar/leerling (M6, M9), 17 BomberMan (M12), 21 monnik (M10, M13, M18, M22, M26, M29: altijd neutraal of heler), 32 prins, 33 prinses (M24). De krijgers 7, 8, 10, 16, 19 hebben allemaal vlag `0xFC = 22`: wie voetvolk, boogschutter, ridder of zombie is blijft onbepaald (7 is in M5 het type van de zombies, 8 is Thrice in M26, 19 is bandiet Freddy in M20). |
| Magenta onbekend tegeltype | **Dennenbos.** Tegel 225 en 226 zijn de sheets `tester` en `tester2` (82x100 en 80x66 px): een grote en een kleine den op een bruine tegel, naast `forest1`/`forest2` (zelfde dennen op groene tegel). Daarmee is "bosgrond" uit `map1.md` eigenlijk **een boom per tegel**: 51 dennen op M1, tot 1.090 in M2. Nog eens 18 bos-tegel-ids (200-217) bestaan in 22 missies (tot 4.500 tegels in M10); de lijst-objecten (klasse 0, 5, 6) zijn extra bomen. Voor 3D: een den per 225/226-tegel (dichtheid 1,0), de 200-217-reeks vermoedelijk gemengd loofbos. |
| Staart na de objecten (22 kB) | **Opgelost voor het ontwerp, niet volledig.** Het is geen apart script maar een heap-dump van het spelerrecord (5 x 3328 bytes), een scriptgebied met condities (timer, kas, tellingen, "object bij object", objecten vernietigd) en tekst-acties, en 24 statistiek-labels. Startkas, startbevolking, doelen, verlies, timers, hint-ketens en eenvoudige puzzels (sleutel, poort, kelk, schop) zijn eruit te halen. Niet gedecodeerd: de uitkomst per regel (win of verlies), de details van `type 9`, en welke tekst bij M3 "1" en "2" hoort (hardcode op de kelk). |
| Startgeld M1 | **10.000 is echt** (spelerrecord, niet cheat). Eerdere veronderstelling in `map1.md` klopt dus niet. Andere missies: M2 6.999, M3 7.000, M7 8.200, de rest (M4, M5, M9, M14, M16, M19, M20, M23, M25, M27-M30) 8.000, M6 6.500, M8 6.000, M10 9.000, M11/M12/M13/M18 10.000, M15 6.000, M17 5.000, M21/M22 7.000, M24 0, M26 15.000. |
| Verlies | Bijna overal "eigen dorpelingen <2" (of <1 op sommige missies): in M1 `<2`. Aanvullend: M12 eigen toren of BomberMan weg, M14 kerk gevallen of <3 mensen, M16 timer of Barry dood, M24 prins of prinses dood, M25 timer, M26 Thrice dood, M28 een van zes gebouwen weg. |

## Correcties op map1.md

- De dorpsnaam op de vlag van M1 is **`Moonton`** (in het bestand), niet "Hoonton" (waarschijnlijk een leesfout van de minimap).
- Startkas **10.000 is echt**; "HUD-testgeld" kan weg.
- Verlies in M1: eigen dorpelingen **<2** (bestand: `count < 2`); winst: dorpelingen **>5** en koeien **>3**, dus 6 en 4.
- Object 171 `(118,58)` is een **koeien-generator**; de 4 doelkoeien komen daaruit.
- `sex` 13 en 14 zijn **jongen en meisje**: het begingezin is 2 mannen, 2 vrouwen, jongen en meisje (de eerste twee dorpelingen, op (104,67) en (99,65)).
- Het magenta/`special`-type (tegel 225/226) is **dennenbos, een boom per tegel**: de 51 tegels in M1 zijn dennen en geen "bosgrond".
- De 22 kB staart is geen opgeblazen script: het is het spelerrecord (kas) plus een condities- en hintgebied; hints in M1 zijn een keten (hut -> bouwersgilde -> bakkerij -> boerderij -> poort -> koeien) plus timers van 108-360 ticks, en de keuze "begin met kippenhokken" (tekst 1-12) komt zonder conditie bij de start.
- M1 heeft geen eigen gebouwen bij de start (net als de bevinding "geen gebouwen" in `map1.md`), wel een zilveren beker (index 6, (110,53)) die via conditie `type 12` naar de vlag (index 1) moet.
- **Beker naar de vlag (M1.MIS, 2026-10-30).** Twee regels `type 12` ("object raakt object"): dorpeling (klasse 103, elk type, dus ook kinderen) raakt de beker (object 6) -> hint 8 ("dat ziet er waardevol uit, breng het naar je vlag"); beker (159) raakt de vlag (object 1) -> acties `0x17` object 6 weg en `0x16` **+5.000** kas (`88 13` = 5000). M3 zelfde patroon: kelk (172) raakt vlag (1578) -> **+7.000** en kelk 2483 weg; een tweede regel met dezelfde conditie geeft 6.000 (betekenis onbekend). Niet in de data: of de beker in de hand te zien is, wat er bij de dood van de drager gebeurt.
- **Remake:** `sim/voorwerpen.gd`. Oprapen = aanraken (binnen 0,75 tegel, wie nog niets draagt); pakbevel = klik op het voorwerp met een selectie (loopbevel erheen); afleveren = drager binnen 1,6 tegel van de eigen vlag. Regels per missie in `spel.json` `missies.<nr>.voorwerpen` (`{"159": {"naar": "vlag", "kas": 5000}}`). Drager weg = voorwerp valt op zijn laatste tegel (eigen keuze; dorpelingen sterven nog niet). In de hand: `view/voorwerpen_view.gd`, geen draagclip. Test `test/voorwerp_test.gd`, frame `spel/screenshots/missie1_beker.jpg`.

## M2 in de remake

Speelbaar met `--missie=2` (zie `spel/README.md`, "Missies"). Kaart: `lokaal/map2/map2.json` uit `lokaal/map2/maak_map.py`. Uit het
bestand: dorp **Goatton**, vlag (92,73), kampvuur (90,76), bron (89,78; een dorpeling staat erop en schuift een tegel op), 10
dorpelingen (4 x type 1, 4 x type 2, 2 x type 13: geen meisje), **4 eigen koeien** (klasse 110, eigenaar 0, (83..88, 77..82)), een
**boerderij** (klasse 51, (90,68), eigenaar 0: in de remake een afgebouwde melkerij), koe-generator (111,101) met p5=1/p6=2 (start 1, max 2),
3 wolven (klasse 104, groep 13, type 23) op (111,55), (125,88), (116,100), 3 goudbuidels (161), 3 drankjes (160), 10 paddenstoelen,
52 bomen, klasse 226 (123,69) onbekend. Wegtypes 1-5 (14 tegels, van de boerderij langs de vlag naar de bron). Bos: 1.090 tegels 225/226;
de kleine "vlekken" in het gras zijn bosjes met overgangsranden (tex 115-130).
Wolven (2026-10-30, `spel/sim/wolf.gd`): zwerven rond hun startplek, jagen op koeien (wild of eigen) en eten ze op; een koe in een weide
achter een dichte poort halen ze niet ("omheining helpt"). Volwassenen (niet de bouwer) gooien stenen op bevel (klik op de wolf) of zelf
als een wolf vlakbij jaagt. Kinderen en baby's pakken (origineel) komt later (gameplay.md 7: "baby's als moeilijkheid later").

**Prijzen, geluk en misdaad (2026-10-30).** **Besluit gebruiker:** misdaad en de straf-schuiven per misdaad pas vanaf M13 (met de gevangenis), zoals het origineel. Origineel: goudicoon in de bovenbalk (MIS1-10) opent `STATS.MFB` (`lokaal/bb_original/stats.png`):
een schuif per waar (eieren, water, brood, melk, cider, kerk, belasting) van weinig munten naar een stapel goud, daaronder per misdaad
(vloeken, diefstal, mishandeling, moord) de straf van duim omhoog tot duim omlaag. MIS2-3: hoge prijzen = ontevreden = korter leven.
Statistiekreeksen in elke .MIS: Happiness, Crimes, Convictions, Trade, Tax. Misdaad en gevangenis (pikenier) pas in M13.
**Prijzen uit `BEASTS.EXE` (2026-10-30).** Warentabel (init `0x414537`-`0x414803`, 36 bytes: naam + `i16` basis): **water 50, ei 80,
brood 50, melk 100, cider 100, kerk/tiende 20, belasting 150** (plus vier onbekende: 2000, 320, 500, 60). Schuif (teken `0x42cad0`,
klik `0x42d0ca`, zet `0x42d780`): 82 px, x = 47 + 82 x prijs / (2 x basis), klik zet prijs = basis x (x - 47) / 41 begrensd op 0..2,
dus **bereik 0..2 x basis, per pixel, start = basis (midden)**; getal naast de schuif = de prijs. Straf per misdaad: (x - 47) / 27 begrensd
op 0..3, byte, dus **4 standen** (duim omhoog 0 .. duim omlaag 3), start 0 in alle .MIS. Misdaadnamen in de EXE: Nowt, Swearing, Arson,
Murder, Assault, Stealing. In het .MIS-spelerrecord staan de prijzen als `i16` vanaf `+84` (index x 2; water `+84`, ei `+92`, brood `+96`,
cider `+100`, belasting `+104`, kerk `+106`, melk `+118`), gelijk aan de basis in alle M1..M30 en alle 5 records, behalve kerk 200 in
M1-4/14/18/25 en belasting 0 in M2/M18. Wat de prijs in de sim doet (per verkoop, per seizoen) is niet uitgezocht.
**Remake** (`spel/sim/handel.gd`, `spel/view/prijzen.gd`, spel.json `handel`): alleen brood/melk/ei, basis en bereik zoals het origineel,
prijs per verkoop naar de kas, - / + = 0,1 x basis (eigen keuze); geluk loopt naar 0,75 - 0,75 x prijsdruk (prijs / basis - 1, gemiddeld),
dus 0,75 op de basis zoals voorheen, 0 als alles op max (eigen keuze), laag geluk versnelt
de ouderdom (`sim/leven.gd`); misdaad alleen met `missies.N.misdaad.aan` (nu geen missie), kans en zwaarte (vloeken > diefstal >
mishandeling > moord) groeien met het ongeluk. Scherm pauzeert de sim, +/- en klikken/slepen op de balk (muis en touch), toets O.
Eigen keuze: overige getallen, geen straf-schuiven, geen water/cider/kerk/belasting (komen met put, brouwerij, kerk, belastinginner).
Test `spel/test/economie_test.gd`, frame `spel/screenshots/prijzen.jpg` (`--scenario=prijzen`).

## Lokale bestanden (niet in git)

| pad | inhoud |
| --- | --- |
| `SC/missies/m<nn>.json` (30) | per missie: terrein-tegels samengevat (`kind_counts`, `home_island`, `bbox_nonvoid`), alle objecten (id, klasse, naam, tegel, eigenaar), `villagers` (type, voornaam), `generators`, `creatures`, `buildings`, `villages` (vlaggen met naam), `conditions`, `hint_texts`, `players` (startkas), `briefing` |
| `SC/missies/m<nn>_layout.png` (30) | bovenaanzicht, 4 px per tegel, per eigenaar gekleurd (geel = speler, rood/oranje/magenta = AI 1-3, wit = neutraal), cyaan = vlag |
| `SC/missies/mis/M<n>.MIS`, `txt/` | uitgepakte kaarten en teksten uit de `.BOX`-bestanden |
| `SC/missies/mis.py`, `export.py`, `gen_md.py` | decoder, exporter en tabelgenerator |
