# Conceptart-inventaris Beasts & Bumpkins-remake

Doel: per model eerst Gemini-conceptart, door de gebruiker beoordeeld, pas daarna modelleren. Dit is alleen de lijst (geen beelden, alleen paden en tekst). Stand 2026-10-29.

Bronnen: `../onderzoek.md` (aantallen, gilden, 33 units uit BBTools-catalogi), de **originele game-uitpak** (`bb_original/`, 625 PNG's uit de MFB-bestanden) en het Unity-project (`Unity_bumpkins/Bumpkins/Assets/Resources/Sprites/` en `Sprites-HD/`, exact 2x).

⚠️ **`bb_original/<naam>.png` is een lokale map (scratchpad), niet in git**: persoonlijk gebruik, nooit committen. Per sprite staat ook een sheet met alle frames in `bb_original/sheets/<naam>.png` (zie hieronder); de MFB's en `mfb.py` staan in `bb_original/mfb/`.

## Wat de bronnen wel en niet hebben
- **De 625 uitgepakte PNG's zijn alleen het eerste frame** van elke MFB (`mfb.py` bewaart `entries[0]`). Alle frames zijn wel te exporteren: `bb_original/mfb/sheets.py` zet ze in een horizontale sheet per sprite (`bb_original/sheets/`, 603 stuks, `_info.txt` = frames en afmeting). Lopen/aanval is **8 richtingen x 6 frames** (48 totaal), een gewone plaat is 1 richting; spiegelen gaat in code.
- Het origineel heeft **sprites voor vrijwel alles**: alle gilde-eenheden, vampier, demon, struikman, reus, ogre, bijna alle gebouwen, vallen, artefacten en spreukpictogrammen. Het Unity-project had maar ~10 figuren en 9 gebouwen. Pad-afkortingen: U/ = `Units/`, B/ = `Buildings/`, A/ = `Animals/`, T/ = `Terrain/` (Unity), `bb_original/` = origineel.
- Naamregels: `d_*` = doodsprite, `mn_*` = minikaart-pictogram, `ni_*` = nacht-overlay (verlichte ramen), `*over`/`*door` = dak- of deur-overlay, `l_*` = licht-overlay, `m_*`/`f_*` = man/vrouw-acties, `v*` = variant met een dorpeling.
- **Portretten bestaan wel**: `statbust` bevat 18 portretten van 102x102 (uitgesneden naar `bb_original/portret/bustNN.png`). Toewijzing is op het oog; zie open vragen.

## Hergebruik
- Elk eenheidsconcept is een **keerplaat** (voor, zij, achter). Hergebruik van de man betekent: zijn plaat als stijlreferentie meegeven, niet de plaat overslaan; een keerplaat per gilde blijft nodig.
- Mens-eenheden delen basislichaam (man 26 px hoog in het origineel = 1,37 m, kind 0,81x, oudere 0,96x) met eigen outfit en gereedschap.
- Samen op een plaat (telt als 1 beeld): kippen-sheet, dorpsprops, bomen, rots+heuvel, hek/muur/poort, wesp+bloedwesp, wolf+donkere wolf, bruidspaar, missiegebouwen per drie, vallen, artefacten.

## Klaar (goedgekeurd) — 2 rijen

| Nr | Naam | Origineel | Sprites (U/ B/ A/ T/ = Unity-project, `bb_original/` = lokale uitpak) | Portret | Richt./staten | Prio | Batch | Opmerking |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| - | Boerenhut | House | `B/House.png`, `B/HouseDoor.png` | geen | 1 richting, 2 delen | klaar | - | Blender + realtime-glb klaar (`../modellen/peasant_hut*.glb`) |
| - | Volwassen man | m_still / m_walk | `U/m_still.png`, `U/m_walk.png`, `U/m_sack.png`, `U/mthrow.png`, `U/m_harvest.png`, `U/d_male.png` | `scratchpad/bumpkin/ref/avatar_man.png` | 1 richting, 6 poses | klaar | - | Rig + 6 animaties klaar (`../modellen/bumpkin/`) |

## 1. Bumpkins (dorpelingen) — 10 rijen

| Nr | Naam | Origineel | Sprites (U/ B/ A/ T/ = Unity-project, `bb_original/` = lokale uitpak) | Portret | Richt./staten | Prio | Batch | Opmerking |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | Vrouw | f_still / f_walk | `U/f_still.png`, `U/f_walk.png`, `U/f_sack.png`, `U/f_milk.png`, `U/fthrow.png`, `U/f_harvest.png`, `U/milking.png`, `U/d_fema.png` | geen | 1 r, 8 poses | 1 | 1 | Blond, grijsgroen jasje, paarse rok; melkt, oogst. Zelfde stijl als man (hergebruik) |
| 2 | Jongen | kidm | `U/kidm.png`, `U/d_kidm.png` | geen | 1 r, 2 | 1 | 1 | 0,81x man; paars hemd, bruin haar |
| 3 | Meisje | kidf | `U/kidf.png`, `U/d_kidf.png` | geen | 1 r, 2 | 1 | 1 | 0,81x man; blond, paarse jurk |
| 4 | Oudere man | elderm | `U/elderm.png` | geen | 1 r, 1 | 1 | 1 | Wit haar, wandelstok met ranken, licht gebogen (0,96x) |
| 5 | Oudere vrouw | elderf | `U/elderf.png` | geen | 1 r, 1 | 1 | 1 | Zelfde stok-silhouet als oudere man |
| 6 | Bouwer (bouwersgilde-eenheid) | reparman / rp_still / bushk_rp | `U/reparman.png`, `U/rp_still.png`, `U/bushk_rp.png`, `U/hammer.png`, `U/d_buil.png` | geen | 1 r, 5 | 1 | 1 | Blauwe tuniek, gele muts, hamer; bushk_rp lijkt rugaanzicht |
| 7 | Baby | baby | `U/baby.png`, `bb_original/baby.png` | geen | 1 r, 4 frames | 2 | 2 | Ligt in doek; kan op de kinderplaat |
| 8 | Bruid + bruidegom | bride, groom | `bb_original/d_bride.png`, `bb_original/d_groom.png`, `bb_original/f_weddin.png`, `bb_original/m_weddin.png` | geen | 8 r x 6 lopen, 5 dood | 3 | 4 | Een plaat met beide; bruid in lichtgrijze jurk, bruidegom met hoge hoed; trouwlopen en dood |
| 9 | Skelet (resten) | skeleton | `U/skeleton.png`, `bb_original/skeleton.png`, `bb_original/mineskul.png` | geen | 1 r, 1 | 3 | 5 | Rest na dood; prop; mineskul = botten bij de mijn |
| 10 | Beul + hakblok | executioner, execblok | `bb_original/execstil.png`, `bb_original/m_exec.png`, `bb_original/execblok.png` | geen | 1 r, 13 frames + blok | 3 | 5 | Zwarte kap, bijl; werkt aan de hakblok (gevangenis/straf). Nieuw uit origineel |

## 2. Gilde- en overige eenheden — 15 rijen

| Nr | Naam | Origineel | Sprites (U/ B/ A/ T/ = Unity-project, `bb_original/` = lokale uitpak) | Portret | Richt./staten | Prio | Batch | Opmerking |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 11 | Voetsoldaat | footman | `bb_original/ft_still.png`, `bb_original/footwalk.png`, `bb_original/footatta.png`, `bb_original/footdie.png`, `bb_original/d_foot.png` | `bb_original/portret/bust04.png` | 8 r x 6 lopen, 8 x 6 slaan, 1 dood | 1 | 2 | Eerste gilde; paars-wit schild, zwaard, helm; portret = gok |
| 12 | Boogschutter | archer | `bb_original/arc_stil.png`, `bb_original/archer.png`, `bb_original/archshoo.png`, `bb_original/d_arch.png` | `bb_original/portret/bust10.png` | 8 r x 6 lopen, 32 schieten | 1 | 2 | Eerste gilde; boog, pijlkoker, paarse kap/veer |
| 13 | Ridder | knight | `bb_original/kn_still.png`, `bb_original/knigwalk.png`, `bb_original/knigatta.png`, `bb_original/knigdie.png`, `bb_original/d_knig.png` | `bb_original/portret/bust09.png` | 8 r x 6 lopen, 56 slaan, 7 dood | 2 | 3 | Plaatharnas, groot zwaard, wit-paars schild; aanval 107x64 px (grote uithaal) |
| 14 | Tovenaar | wizard | `bb_original/wz_still.png`, `bb_original/wizwalk.png`, `bb_original/wizcast.png`, `bb_original/wizaim.png`, `bb_original/wizadie.png`, `bb_original/d_wiza.png` | `bb_original/portret/bust11.png` | 8 r x 6 lopen, 8 cast, 8 richten | 2 | 3 | Paarse puntmuts en mantel, baard, staf met gouden kop |
| 15 | Priester | priest | `bb_original/pr_still.png`, `bb_original/priest.png`, `bb_original/pri_heal.png`, `bb_original/d_prie.png` | `bb_original/portret/bust15.png` | 8 r x 6 lopen, 11 genezen | 2 | 3 | Zwart habijt, paarse accenten, priesterkraag; zegent, begraaft; kerk |
| 16 | Minstreel | minstrel | `bb_original/minstrel.png`, `bb_original/minlyre.png`, `bb_original/minbow.png` | `bb_original/portret/bust01.png` | 8 r x 6 lopen, 5 luit, 5 boog | 2 | 3 | Paars kostuum, luit; sfeer; heeft ook een boog-animatie |
| 17 | Monnik | monk | `bb_original/mk_stil.png`, `bb_original/monkwalk.png` | geen | 8 r x 6 lopen, 4 still | 3 | 4 | Bruine pij; mk_stil draagt een net/zak; bij kerk |
| 18 | Belastinginner | taxman | `bb_original/tx_still.png`, `bb_original/taxman.png`, `bb_original/d_taxm.png` | `bb_original/portret/bust16.png` | 8 r x 6 lopen, 5 dood | 3 | 4 | Hoge zwarte hoed, geldzak; portret met gouden muntjes |
| 19 | Wachter (piekenier) | guard / pikeman | `bb_original/pk_still.png`, `bb_original/pikewalk.png`, `bb_original/pikeatta.png`, `bb_original/pikedie.png`, `bb_original/d_pike.png` | `bb_original/portret/bust14.png` | 8 r x 6 lopen, 24 steken | 3 | 4 | Bruin leer, lange piek met bijl-kop; portret met bijl |
| 20 | Vlagdrager | flagman | `bb_original/fg_still.png`, `bb_original/flagwalk.png`, `bb_original/flagdie.png`, `bb_original/flag.png` | `bb_original/portret/bust05.png` | 8 r x 6 lopen, 10 vlag | 3 | 4 | Paars-wit maliënkap met paarse vlag; variant van voetsoldaat |
| 21 | Cavalerist + paard | cavalier, horse | `bb_original/cavalier.png`, `bb_original/cavatta.png`, `bb_original/d_cava.png` | `bb_original/portret/bust06.png` | 8 r x 4 lopen, 40 aanval, 5 dood | 3 | 4 | Een model: ruiter met lans op paars-wit paard (55x48 px); geen los paard; portret = gok |
| 22 | Kruisboog (wielgeschut) | crossbow | `bb_original/crossbow.png`, `bb_original/cbolt.png` | geen | 8 r x 4, bout 8 | 3 | 4 | Geen schutter maar een kruisboog op wielen (belegering), net als de trebuchet |
| 23 | Bommenwerper | bombman | `bb_original/bombman.png`, `bb_original/bombfroz.png` | geen | 8 r x 6, 1 bevroren | 3 | 4 | Klein zwart figuur met bom; gebruikt `Effects/shrapnel`; bombfroz = blauw bevroren |
| 24 | Trebuchet (geschut + bemanning) | catapult | `bb_original/catapult.png`, `bb_original/catfire.png`, `bb_original/ctnomove.png`, `bb_original/ctnofire.png` | geen | 8 r x 4, schieten | 3 | 4 | Houten katapult op stenen wielen, paarse beladen arm (69x49); ct* = richtingvarianten lopen/vuren |
| 25 | Nar / jongleur | juggler, jester | `bb_original/juggler.png`, `bb_original/minjuggl.png`, `bb_original/d_jest.png` | `bb_original/portret/bust08.png` | 1 r x 5 frames | 3 | 4 | Paars narrenkostuum, balletjes; variant van de minstreel. Nieuw uit origineel |

## 3. Vijanden en wezens — 9 rijen

| Nr | Naam | Origineel | Sprites (U/ B/ A/ T/ = Unity-project, `bb_original/` = lokale uitpak) | Portret | Richt./staten | Prio | Batch | Opmerking |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 26 | Wolf (+ donkere wolf) | wolf, dark wolf | `A/wolf.png`, `A/wolfstil.png`, `A/wolfatta.png`, `A/wolfdead.png` | geen | 1 r, 4 | 1 | 1 | Eerste vijand; grijs, rode ogen, eet baby's; donkere wolf = recolor op dezelfde plaat |
| 27 | Zombie | zombie | `A/zombie.png`, `A/zombatta.png`, `A/zombdead.png` | geen | 1 r, 3 | 1 | 1 | Groen oog, bruine lompen; ook via tovenaarsspreuk |
| 28 | Wesp (+ bloedwesp) | wasp, blood wasp | `A/wasp.png`, `A/waspat.png`, `A/waspdead.png`, `A/bloodwsp.png`, `A/bloodead.png`, `bb_original/wasp.png`, `bb_original/waspat.png`, `bb_original/bloodwsp.png`, `bb_original/hive.png` | geen | 8 r x 6, 5 dood | 2 | 3 | Vliegend, geel; bloedwesp rood; een plaat; hive = bijenkorf (64x63) erbij |
| 29 | Vleermuis | bat | `A/bat.png`, `A/batatta.png`, `A/deadbat.png`, `bb_original/bat.png`, `bb_original/batatta.png`, `bb_original/deadbat.png`, `bb_original/vampbat.png` | geen | 8 r x 6, 8 aanval | 2 | 3 | Vliegend, zwart; grote spanwijdte; vampbat = vampier in vleermuisvorm |
| 30 | Reus | giant | `A/giant.png`, `A/gianstil.png`, `A/gianatt.png`, `A/giandead.png`, `bb_original/gianstil.png`, `bb_original/giant.png`, `bb_original/gianatt.png`, `bb_original/giandead.png` | geen | 8 r x 6, 32 aanval, dood | 2 | 4 | Bloot bovenlijf, maliënbroek, bijl; ~1,35x de man (36 px tegen 26) |
| 31 | Ogre | ogre | `A/ogrestil.png`, `A/ogrewalk.png`, `A/ogreatta.png`, `A/ogredead.png`, `bb_original/ogrestil.png`, `bb_original/ogrewalk.png`, `bb_original/ogreatta.png`, `bb_original/ogredead.png`, `bb_original/ogrefire.png` | geen | 8 r x 6, 56 aanval, dood | 2 | 4 | Groen, rond houten schild, hoge staf met bol; ~1,8x de man incl. staf (47 px); ogrefire = magische vonk |
| 32 | Vampier | vampire | `bb_original/vampstil.png`, `bb_original/vampbat.png`, `bb_original/vampdead.png` | geen | 6 still, 7 vleermuis, 11 dood | 3 | 4 | Zwarte mantel met hoge kraag, rode kam; 1,2x de man; wisselt in vleermuis |
| 33 | Demon (fiend) | demon / fiend | `bb_original/fiend.png`, `bb_original/darkdead.png` | geen | 8 r x 8 (64 frames) | 3 | 4 | Gevleugelde duivel, rood-grijs, 88x71 px (groter dan de reus); eindbaas-sfeer, bij duister altaar |
| 34 | Struikman / etende struik | bush-man | `bb_original/bushman.png` | geen | 6 frames | 3 | 4 | Een dennenboom met ogen (29x48 px); geen dwerg erbij: `dw_*` blijkt een zwarte wolf |

## 4. Boerderijdieren — 3 rijen

| Nr | Naam | Origineel | Sprites (U/ B/ A/ T/ = Unity-project, `bb_original/` = lokale uitpak) | Portret | Richt./staten | Prio | Batch | Opmerking |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 35 | Koe | cow | `U/cow_se.png`, `U/milking.png` | geen | 1 r, 2 | 1 | 1 | Zwartbont; melken, slacht, kalven; 51x34 px |
| 36 | Kippen-sheet (kip, kuiken, ei) | Chicken, ChickenEgg | `U/Chicken.png`, `U/ChickenEgg.png` | geen | 1 r, 2 | 1 | 1 | Een plaat voor 3 onderwerpen; kuiken heeft geen sprite |
| 37 | Kalf + varken | calf, pig | `bb_original/cowborn.png`, `bb_original/pigsy.png` | geen | 2 + 1 frame | 3 | 5 | Een plaat; kalf ligt wit-zwart (34x21), varken staat in een kleine pen-tegel (26x20); beide klein |

## 5. Gebouwen — 31 rijen

| Nr | Naam | Origineel | Sprites (U/ B/ A/ T/ = Unity-project, `bb_original/` = lokale uitpak) | Portret | Richt./staten | Prio | Batch | Opmerking |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 38 | Gereedschapsloods | Toolshed | `B/Toolshed.png`, `B/ToolshedDoor.png` | geen | 1 r, 2 delen | 1 | 1 | 162x129; deur is apart animatiedeel |
| 39 | Melkerij / boerderij | Dairy | `B/Dairy.png`, `B/DairyDoor.png` | geen | 1 r, 2 delen | 1 | 1 | 213x160, grootste; research: farm met koestal |
| 40 | Molen | Mill | `B/Mill.png`, `B/MillDoor.png`, `B/MillSails.png` | geen | 1 r, 3 delen | 1 | 1 | Wieken zijn eigen draaideel |
| 41 | Kippenhok | ChickenCoop | `B/ChickenCoop.png` | geen | 1 r, 1 | 1 | 1 | 66x45, klein |
| 42 | Voetsoldatengilde | footmans guild | `bb_original/fguild.png`, `bb_original/footdoor.png`, `bb_original/mn_foot.png` | geen | 2 frames + deur | 1 | 2 | Eerste gilde; ronde stenen toren met paarse rand en strodak-bijgebouw (118x129) |
| 43 | Boogschuttersgilde | archers guild | `bb_original/fletcher.png`, `bb_original/archdoor.png`, `bb_original/mn_arch.png` | geen | 2 frames + deur | 1 | 2 | Eerste gilde; strodak met schietschijf en pijl (132x139) |
| 44 | Bouwersgilde | builders guild | `bb_original/workover.png`, `bb_original/l_work01.png`, `bb_original/mn_work.png` | geen | alleen deur/overlay | 1 | 2 | Gebouw zelf niet gevonden (alleen deur `workover` en pictogram); mogelijk de gereedschapsloods |
| 45 | Waterput | well | `bb_original/well.png`, `bb_original/wellover.png`, `bb_original/wellwate.png` | geen | 2 frames + overlay + water | 1 | 2 | Water is een behoefte; stenen huisje met paars dak en blauwe vijver (133x110) |
| 46 | Bakkerij | bakery | `bb_original/bakery.png`, `bb_original/bakeover.png`, `bb_original/bakeanim.png` | geen | 2 frames + deur + anim | 1 | 2 | Tarwe naar brood; strodak met tonschoorsteen (202x180); bakeanim = windmolen met wieken |
| 47 | Akker (kaal + rijp) | WheatField | `B/WheatField.png`, `B/WheatField_grown.png`, `bb_original/wheat.png`, `bb_original/wheatovr.png`, `bb_original/crops.png`, `bb_original/f_scythe.png` | geen | 1 r, 2 stadia | 1 | 2 | Seizoensplant; een plaat met beide stadia; f_scythe = maaien |
| 48 | Dorpsprops: kampvuur, houtstapel, steenhoop | Campfire, Logpile, Rockpile | `B/Campfire.png`, `B/Logpile.png`, `B/Rockpile.png`, `bb_original/campfire.png`, `bb_original/logs.png`, `bb_original/pile01.png` | geen | 1 r, 3 | 1 | 2 | Een plaat voor 3 grondstofprops; kampvuur ook missiegebouw |
| 49 | Stadhuis | town hall | `bb_original/th_nodo.png`, `bb_original/th_over.png`, `bb_original/ni_townh.png` | geen | 2 frames + overlay | 2 | 2 | Belasting; groot; onzeker welk gebouw het stadhuis is: `th_nodo` (strodak met klok) of een ander; `th_over` = steen met bruin dak |
| 50 | Hek / muur / poort | fence, stone wall, gate | `bb_original/fence.png`, `bb_original/gfence.png`, `bb_original/wall.png`, `bb_original/gate.png`, `bb_original/mgate.png`, `bb_original/bridge.png` | geen | 16 stukken per hek/muur | 2 | 2 | Een plaat; houten hek, graf-hek, stenen muur, houten poort, stenen poort, brug; sneeuwhek (`snwfence`) ook |
| 51 | Brouwerij | brewery | `bb_original/brewery.png`, `bb_original/brewover.png`, `bb_original/brewbig.png`, `bb_original/beer.png` | geen | 2 frames + deur | 2 | 3 | Appels naar cider; strodak met ton en pijp (179x153); beer = bierton |
| 52 | Kerk | church | `bb_original/church.png`, `bb_original/churover.png`, `bb_original/crucifix.png` | geen | 2 frames | 2 | 3 | Priester, begraafplaats; stenen toren met paars dak + kerkschip (220x220); ni_cathd = nachtversie (kathedraal) |
| 53 | Ridderlijke gilde | knights guild | `bb_original/barrack.png`, `bb_original/mn_keep.png` | geen | onzeker | 2 | 3 | Eigen sprite niet gevonden; kandidaat `barrack` (222x143, tonvormige daken) of `keep` |
| 54 | Tovenaarsgilde | wizards guild | `bb_original/treehous.png`, `bb_original/mn_wiz.png` | geen | 1 frame | 2 | 3 | Waarschijnlijk de boomhut `treehous` (118x157, ladder, strodak): pictogram mn_wiz is bruin met boom |
| 55 | Minstrelsgilde | minstrels guild | `bb_original/pub.png`, `bb_original/mn_pub.png` | geen | onzeker | 2 | 3 | Eigen sprite niet gevonden; kandidaat de taverne `pub` (zie Herberg) |
| 56 | Stallen | stables | `bb_original/stables.png`, `bb_original/stabdoor.png`, `bb_original/mn_stabl.png` | geen | 2 frames + deur | 2 | 3 | Cavaliers en paarden; rond strodak met hoefijzer (137x141) |
| 57 | Gevangenis | prison | `bb_original/jail.png`, `bb_original/jaildoor.png`, `bb_original/mn_jail.png` | geen | 2 frames + deur | 2 | 3 | Dorpelingen arresteren; stenen cel met zwarte kogel en ketting (140x124) |
| 58 | Uitkijkpost | lookout post | `bb_original/lookout.png`, `bb_original/look_ov.png`, `bb_original/mn_look.png` | geen | 1 frame + overlay | 2 | 3 | Houten wachttoren met strodak (189x159) |
| 59 | Herberg (pub) | pub | `bb_original/pub.png`, `bb_original/pubover.png`, `bb_original/ni_pub.png` | geen | 3 frames + nacht | 2 | 3 | Brede taverne met bruin dak (260x131); drinkende dorpelingen (f_drink/m_drink). Nieuw uit origineel |
| 60 | Graanschuur (granary) | granary | `bb_original/granover.png`, `bb_original/mn_gran.png`, `bb_original/ni_gran.png` | geen | alleen overlay | 3 | 6 | Gevonden zijn alleen dakoverlay (97x77) en pictogram; stenen muur, bruin dak. Nieuw uit origineel |
| 61 | Appelboom + appelpluk | apple tree | `bb_original/appltree.png`, `bb_original/apples.png`, `bb_original/appsprig.png`, `bb_original/f_shaker.png` | geen | 2 frames + schudden 21 | 3 | 6 | Appels voor de brouwerij; f_shaker/m_shaker = dorpeling die schudt. Nieuw uit origineel |
| 62 | Missiegebouwen A: kapel, barak, kasteel | chapel, barrack, castle | `bb_original/chapel.png`, `bb_original/barrack.png`, `bb_original/castle.png` | geen | 1 + 1 + 3 frames | 3 | 5 | Een plaat voor 3; alleen missies; kapel (221x221) lijkt op de kerk, kasteel 210x181 |
| 63 | Missiegebouwen B: toren, hut (cabin), tent | tower, cabin, keep/tent | `bb_original/towin.png`, `bb_original/towreal.png`, `bb_original/cabin.png`, `bb_original/hut.png`, `bb_original/tent.png`, `bb_original/keep.png` | geen | diverse | 3 | 5 | Een plaat voor 3 (toren, houten hut `cabin`/`hut`, gestreepte tent); `keep` (287x211) is een paarse burcht |
| 64 | Tempel + teleporttempel | temple, teleport temple | `bb_original/pagnbulk.png`, `bb_original/paganrok.png` | geen | 1 + 1 | 3 | 5 | Twee naast elkaar op een plaat; heidense stenen cirkel met pentagram (115x94) en losse boog |
| 65 | Duister altaar | dark altar | `bb_original/altar.png`, `bb_original/summon.png`, `bb_original/landmark.png` | geen | 2 frames | 3 | 5 | Bij vampier/demon; rood pentagram met kaarsen (57x38); summon = stronk met schedel |
| 66 | Boutval (gebouw) | bolt trap | `bb_original/bolt.png`, `bb_original/cbolt.png` | geen | 4 + 8 | 3 | 5 | Zie ook vallen-sheet; bolt = pijl-projectiel |
| 67 | Zombiegraf (zombie tomb) | zombie tomb | `bb_original/zombtomb.png`, `bb_original/spkzomb.png`, `bb_original/zombglow.png` | geen | 1 + 2 | 3 | 5 | Stenen kist met kruis, begroeid (86x97); zombie kruipt eruit. Nieuw uit origineel |
| 68 | Spookboom + wortelaltaar | weird tree | `bb_original/spooky.png`, `bb_original/landmark.png`, `bb_original/stump.png` | geen | 4 frames | 3 | 5 | Dode boom met kale takken (41x46), boomwortel met schedels. Nieuw uit origineel |

## 6. Props en effecten — 15 rijen

| Nr | Naam | Origineel | Sprites (U/ B/ A/ T/ = Unity-project, `bb_original/` = lokale uitpak) | Portret | Richt./staten | Prio | Batch | Opmerking |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 69 | Bomen-sheet (groot, middel, klein) | tree01/05, 02/04, 10/11 | `T/tree01.png`, `T/tree05.png`, `T/tree02.png`, `T/tree04.png`, `T/tree10.png`, `T/tree11.png` | geen | 1 r, 6 | 1 | 2 | Een plaat; seizoensvarianten in `SeasonalTreeTile.cs` |
| 70 | Rots + zandheuvel | rock01, sandhill | `T/rock01.png`, `T/sandhill.png` | geen | 1 r, 2 | 2 | 2 | Een plaat |
| 71 | Vallen-sheet (6) | spike, mine, flame, gas, bolt, oil | `bb_original/spike.png`, `bb_original/d_spike.png`, `bb_original/mineskul.png`, `bb_original/flamepit.png`, `bb_original/gas.png`, `bb_original/bolt.png`, `bb_original/oilslick.png` | geen | 1 r, 6 vallen | 3 | 5 | Een plaat; pennen, mijn (schedel), vlampit, gaswolk, bout, olievlek |
| 72 | Artefacten-sheet 1 (bekers, zwaard, helm, ...) | artefacten | `bb_original/gob_gold.png`, `bb_original/gob_silv.png`, `bb_original/sword.png`, `bb_original/mace.png`, `bb_original/helmet.png`, `bb_original/holyswrd.png`, `bb_original/goldcoin.png` | geen | 1 r, ~7 | 3 | 5 | ~15 artefacten over 2 platen |
| 73 | Artefacten-sheet 2 (ring, schild, sleutel, ...) | artefacten | `bb_original/magring.png`, `bb_original/mainring.png`, `bb_original/shield.png`, `bb_original/mkey.png`, `bb_original/cloak.png`, `bb_original/crucifix.png`, `bb_original/pot_red.png`, `bb_original/pot_blue.png`, `bb_original/pot_gren.png`, `bb_original/shovel.png` | geen | 1 r, ~10 | 3 | 5 |  |
| 74 | Graven / doodskist | grave, coffin | `bb_original/grave.png`, `bb_original/grave01.png`, `bb_original/body.png` | geen | 2 + 1 | 3 | 5 | Priester begraaft; grafkelder (66x49) en kruis; `body` is een rood-geruite zak/stof, geen lijkkist |
| 75 | Bouwgereedschap (zaag, pikhouweel) | saw, pick | `B/saw.png`, `B/vsaw.png`, `B/pick.png`, `B/vpick.png` | geen | 1 r, 4 | 3 | 5 | Animatieprops bij bouwen; `v` = dezelfde animatie met een dorpeling (bruin haar) in plaats van de bouwer (blauw, gele muts) |
| 76 | Winterbomen en sneeuw | GrassWinter | `T/GrassWinter.png` | geen | 1 r, 1 | 3 | 6 | Sneeuwvarianten van de bomen-sheet |
| 77 | Vuur, rook, explosie | Flames | `Effects/Flames.png`, `bb_original/flames.png`, `bb_original/burn.png`, `bb_original/smolder.png`, `bb_original/explode.png`, `bb_original/fired.png` | geen | 1 r, 5 | 3 | 6 | Effect-sheet |
| 78 | Projectielen (pijl, bout, steen, bom) | shrapnel | `Effects/shrapnel.png` | geen | 1 r, 1 | 3 | 6 | Een plaat |
| 79 | Spreukeffecten (9 + extra) | s_* spells | `bb_original/s_cure.png`, `bb_original/s_fear.png`, `bb_original/s_ffood.png`, `bb_original/s_fireb.png`, `bb_original/s_flash.png`, `bb_original/s_heal.png`, `bb_original/s_see.png`, `bb_original/s_summon.png`, `bb_original/s_tport.png`, `bb_original/lgtning.png`, `bb_original/equake.png`, `bb_original/acidbolt.png` | geen | 9 s_* + 3 | 3 | 6 | Slechts 9 s_*-sprites (genezen, angst, voedsel, vuurbal, flits, heal, oog, oproepen, teleport) + bliksem, aardbeving, zuur; rest zelf ontwerpen |
| 80 | Draagprops (zak, emmer, korf) | f_sack, f_milk | `U/m_sack.png`, `U/f_milk.png` | geen | 1 r, 2 | 3 | 6 | Bij werkanimaties |
| 81 | Regen- en onweerswolken | rain/thunder | `bb_original/rain.png`, `bb_original/cloud.png`, `bb_original/blkcloud.png`, `bb_original/lgtning.png` | geen | 1 r, 4 | 3 | 6 | Weereffect |
| 82 | Straatlamp en toorts | street lamp | `bb_original/lamp.png`, `bb_original/lantern.png`, `bb_original/torch.png` | geen | 9 + 2 + 6 | 3 | 6 | Straatlamp (49x40), lantaarn, brandende toorts. Nieuw uit origineel |
| 83 | Meubilair: bank, stoel, kist, drinkbak | bench, logchair, crate, trough | `bb_original/bench.png`, `bb_original/logchair.png`, `bb_original/crate.png`, `bb_original/trough.png`, `bb_original/sign.png`, `bb_original/salepost.png` | geen | 1 r, 6 | 3 | 6 | Kleine props rond huizen; bord/verkoopbord. Nieuw uit origineel |

## Tellingen
- Rijen (onderwerpen): Bumpkins 10, Gilde- en overige eenheden 15, Vijanden en wezens 9, Boerderijdieren 3, Gebouwen 31, Props en effecten 15 = **83** rijen, plus 2 klaar. Alle 83 hebben nu minstens een sprite; 63 hebben een sprite uit het origineel (`bb_original/`), de rest alleen uit het Unity-project (batch 1 is bewust ongewijzigd gelaten).

- Nieuw ten opzichte van de vorige stand: Beul + hakblok, Nar / jongleur, Herberg (pub), Graanschuur, Appelboom + appelpluk, Zombiegraf, Spookboom + wortelaltaar, Straatlamp en toorts, Meubilair. Vervallen: Dwerg (`dw_*` is een zwarte wolf). Kruisboogschutter is nu Kruisboog (wielgeschut); Struikman staat apart (geen dwerg erbij).

## Batches (ongeveer 14 beelden per dag, prio 1 eerst)

| Batch | Beelden | Inhoud |
| --- | --- | --- |
| 1 | 14 | Vrouw; Jongen; Meisje; Oudere man; Oudere vrouw; Bouwer; Wolf; Zombie; Koe; Kippen-sheet; Gereedschapsloods; Melkerij / boerderij; Molen; Kippenhok |
| 2 | 14 | Baby; Voetsoldaat; Boogschutter; Voetsoldatengilde; Boogschuttersgilde; Bouwersgilde; Waterput; Bakkerij; Akker; Dorpsprops: kampvuur, houtstapel, steenhoop; Stadhuis; Hek / muur / poort; Bomen-sheet; Rots + zandheuvel |
| 3 | 15 | Ridder; Tovenaar; Priester; Minstreel; Wesp; Vleermuis; Brouwerij; Kerk; Ridderlijke gilde; Tovenaarsgilde; Minstrelsgilde; Stallen; Gevangenis; Uitkijkpost; Herberg |
| 4 | 15 | Bruid + bruidegom; Monnik; Belastinginner; Wachter; Vlagdrager; Cavalerist + paard; Kruisboog; Bommenwerper; Trebuchet; Nar / jongleur; Reus; Ogre; Vampier; Demon; Struikman / etende struik |
| 5 | 15 | Skelet; Beul + hakblok; Kalf + varken; Missiegebouwen A: kapel, barak, kasteel; Missiegebouwen B: toren, hut; Tempel + teleporttempel; Duister altaar; Boutval; Zombiegraf; Spookboom + wortelaltaar; Vallen-sheet; Artefacten-sheet 1; Artefacten-sheet 2; Graven / doodskist; Bouwgereedschap |
| 6 | 11 | Graanschuur; Appelboom + appelpluk; Winterbomen en sneeuw; Vuur, rook, explosie; Projectielen; Spreukeffecten; Draagprops; Regen- en onweerswolken; Straatlamp en toorts; Meubilair: bank, stoel, kist, drinkbak |

Totaal **84 beelden in 6 batches**. Batch 1 is het speelbare dorp (vrouw, kinderen, ouderen, bouwer, koe, kippen, eerste vijanden, vier gebouwen) en is ongewijzigd; batch 2 de eerste gilden en basisgebouwen.

## Beantwoord uit de sprites
- **Paladijn**: bestaat niet. Geen sprite, niet in `objects_list.txt`; de zwaarst bepantserde eenheid is de ridder (`kn_*`) en te paard de cavalerist (`cavalier`, ruiter en paard in een model).
- **`vsaw` / `vpick`**: dezelfde animatie als `saw` / `pick`, maar met een dorpeling (bruin haar, grijs hemd, paarse broek) in plaats van de bouwer (blauw, gele muts). `v` = villager. Het laatste frame van `saw`/`pick` is de afgewerkte tegel.
- **Reus**: 36 px hoog tegen 26 px voor de man, dus ~1,35x (ca. 1,9 m). Niet 1,5 tot 2x.
- **Ogre**: 47 px incl. hoge staf met bol (~1,8x); zonder staf ~35 px, ca. 1,35x. Dik en breed (37 px), groen, met rond houtschild.
- **Dwerg**: bestaat niet; `dw_still`/`dw_walk`/`dw_attak` zijn een **zwarte wolf** (35x30). Dat is de "donkere wolf" van de wolf-plaat. **Struikman** (`bushman`) is een dennenboom met ogen.
- **Kruisboogschutter**: `crossbow` is een kruisboog op wielen (belegeringswapen), geen schutter; `catapult` is de trebuchet. Bommenwerper (`bombman`) is een klein zwart figuur.
- **Wachter/piekenier**: wel, `pk_still`/`pikewalk`/`pikeatta`; vlagdrager (`flagwalk`, `fg_still`) ook.
- **Demon**: `fiend` is een gevleugelde duivel van 88x71 px, 64 frames; **vampier** heeft stil, vleermuisvorm en doodsprite.
- **Bruid en bruidegom**: `d_bride`, `d_groom`, `f_weddin`, `m_weddin`: bestaan wel.
- **Portretten**: er zijn er 18 in `statbust`. Gok-toewijzing: 1 minstreel, 2 jongen (rood haar), 3 bouwer (kaal, blauw), 4 voetsoldaat, 5 vlagdrager, 6 cavalerist (knots), 7 meisje, 8 nar, 9 ridder, 10 boogschutter, 11 tovenaar, 12 man (avatar), 13 vrouw, 14 wachter (bijl), 15 priester, 16 belastinginner, 0 en 17 oudere vrouwen. Voor batch 1 (vrouw, jongen, meisje, bouwer) zijn er dus portretten.

## Open vragen
1. **Gildegebouwen**: voetsoldaten (`fguild`) en boogschutters (`fletcher`) zijn zeker (deur-sprites `footdoor`, `archdoor`). Tovenaars waarschijnlijk `treehous`. Ridders (`barrack` of `keep`), minstrels (`pub`?) en bouwers (alleen deur `workover`) onzeker; `uguild` is een menu-pictogram. Controle in een screenshot van het origineel.
2. **Stadhuis**: welke sprite? `th_nodo` (strodak met klok) of `th_over` (steen met bruin dak, lijkt op `granover`). `mn_tax` (belastingkantoor) is geel strodak.
3. Is de gereedschapsloods (`Toolshed`, nachtversie `ni_tools`) het bouwersgilde-gebouw, of is dat `mn_work`?
4. `Dairy` heet in de code melkerij; research noemt "farm" met koestal; origineel `farm`. Welke naam?
5. Kuiken heeft geen sprite (ei `chickegg` wel); `bushk_fl/ml/pr/rp` zijn vier kleine figuurtjes (vrouw, man, priester, bouwer; 4 frames) van onbekend gebruik, waarschijnlijk liggend/schuilend; `soldier` is een paarse gebogen figuur (48 frames) van onbekend gebruik.
6. Portret-toewijzing (hierboven) klopt op het oog; controleren in het spel (`mn_*`/portretvenster).
7. Spreukeffecten: slechts 9 `s_*`-sprites tegen 14 spreuken (7 + 7); de rest is zelf te ontwerpen.
