# Conceptart-inventaris Beasts & Bumpkins-remake

Doel: per model eerst Gemini-conceptart, door de gebruiker beoordeeld, pas daarna modelleren. Dit is alleen de lijst (geen beelden, alleen paden en tekst). Stand 2026-10-29.

Bronnen: `../onderzoek.md` (aantallen, gilden, 33 units uit BBTools-catalogi), de originele sprites (alleen persoonlijk gebruik, nooit in git) in `Unity_bumpkins/Bumpkins/Assets/Resources/Sprites/` en `Sprites-HD/` (exact 2x, zelfde tekening), en de C#-scripts van dat project.

## Wat de bronnen wel en niet hebben
- Elke PNG is **een frame in een richting** (geen sheets); spiegelen gaat in code (flipX). "1 r, N" = 1 richting, N poses/delen. Pad-afkortingen: U/ = `Units/`, B/ = `Buildings/`, A/ = `Animals/`, T/ = `Terrain/`.
- Het Unity-project is een kleine nabouw: **geen json-catalogi** (`state_catalog.json` e.d. staan alleen in BBTools), en geen koppeling unit-naam naar sprite buiten `BumpkinAnimator.cs`. Het heeft sprites voor ongeveer 10 mensen-/dierfiguren, 9 gebouwen en enkele props. **Alle gilde-eenheden en de meeste gebouwen (gilden, kerk, brouwerij, ...) hebben geen sprite**: die staan op de onderzoekslijst (33 units, 21 + ~10 gebouwen).
- **Avatarportret**: er is er maar een, `scratchpad/bumpkin/ref/avatar_man.png` (man: grote bruine krullenbol, snor, grashalm in de mond, grijs jasje, paarse bretels). `Sprites/UI/` bevat alleen `season.png`; geen script verwijst naar portretten. Een koppeling portret-unit is voor de rest niet te maken.

## Hergebruik
- Elk eenheidsconcept is een **keerplaat** (voor, zij, achter). Hergebruik van de man betekent: zijn plaat als stijlreferentie meegeven, niet de plaat overslaan; een keerplaat per gilde blijft nodig.
- Mens-eenheden delen basislichaam (man 1,37 m, kind 0,81x, oudere 0,96x) met eigen outfit en gereedschap.
- Samen op een plaat (telt als 1 beeld): kippen-sheet, dorpsprops, bomen, rots+heuvel, hek/muur/poort, wesp+bloedwesp, wolf+donkere wolf, bruidspaar, dwerg+struikman, missiegebouwen per drie, vallen, artefacten.

## Klaar (goedgekeurd) — 2 rijen

| Nr | Naam | Origineel | Sprites (rel. aan `Sprites/`) | Portret | Richt./staten | Prio | Batch | Opmerking |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| - | Boerenhut | House | `B/House.png`, `B/HouseDoor.png` | geen | 1 richting, 2 delen | klaar | - | Blender + realtime-glb klaar (`../modellen/peasant_hut*.glb`) |
| - | Volwassen man | m_still / m_walk | `U/m_still.png`, `U/m_walk.png`, `U/m_sack.png`, `U/mthrow.png`, `U/m_harvest.png`, `U/d_male.png` | `scratchpad/bumpkin/ref/avatar_man.png` | 1 richting, 6 poses | klaar | - | Rig + 6 animaties klaar (`../modellen/bumpkin/`) |

## 1. Bumpkins (dorpelingen) — 9 rijen

| Nr | Naam | Origineel | Sprites (rel. aan `Sprites/`) | Portret | Richt./staten | Prio | Batch | Opmerking |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | Vrouw | f_still / f_walk | `U/f_still.png`, `U/f_walk.png`, `U/f_sack.png`, `U/f_milk.png`, `U/fthrow.png`, `U/f_harvest.png`, `U/milking.png`, `U/d_fema.png` | geen | 1 r, 8 poses | 1 | 1 | Blond, grijsgroen jasje, paarse rok; melkt, oogst. Zelfde stijl als man (hergebruik) |
| 2 | Jongen | kidm | `U/kidm.png`, `U/d_kidm.png` | geen | 1 r, 2 | 1 | 1 | 0,81x man; paars hemd, bruin haar |
| 3 | Meisje | kidf | `U/kidf.png`, `U/d_kidf.png` | geen | 1 r, 2 | 1 | 1 | 0,81x man; blond, paarse jurk |
| 4 | Oudere man | elderm | `U/elderm.png` | geen | 1 r, 1 | 1 | 1 | Wit haar, wandelstok met ranken, licht gebogen (0,96x) |
| 5 | Oudere vrouw | elderf | `U/elderf.png` | geen | 1 r, 1 | 1 | 1 | Zelfde stok-silhouet als oudere man |
| 6 | Bouwer (bouwersgilde-eenheid) | reparman / rp_still / bushk_rp | `U/reparman.png`, `U/rp_still.png`, `U/bushk_rp.png`, `U/hammer.png`, `U/d_buil.png` | geen | 1 r, 5 | 1 | 1 | Blauwe tuniek, gele muts, hamer; bushk_rp lijkt rugaanzicht |
| 7 | Baby | baby | `U/baby.png` | geen | 1 r, 1 | 2 | 2 | Ligt in doek; kan op de kinderplaat |
| 8 | Bruid + bruidegom | bride, groom | geen | geen | geen sprite | 3 | 4 | Een plaat met beide; trouwstap in levenscyclus |
| 9 | Skelet (resten) | skeleton | `U/skeleton.png` | geen | 1 r, 1 | 3 | 5 | Rest na dood; prop |

## 2. Gilde- en overige eenheden (geen sprites in het project) — 15 rijen

| Nr | Naam | Origineel | Sprites (rel. aan `Sprites/`) | Portret | Richt./staten | Prio | Batch | Opmerking |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 10 | Voetsoldaat | footman | geen | geen | geen sprite | 1 | 2 | Eerste gilde; basislichaam man + wapenrok, zwaard, schild |
| 11 | Boogschutter | archer | geen | geen | geen sprite | 1 | 2 | Eerste gilde; boog, pijlkoker |
| 12 | Ridder | knight | geen | geen | geen sprite | 2 | 3 | Harnas; aanval 7 frames in origineel |
| 13 | Tovenaar | wizard | geen | geen | geen sprite | 2 | 3 | 7 spreuken; staf, mantel |
| 14 | Priester | priest | geen | geen | geen sprite | 2 | 3 | 7 spreuken, zegent, begraaft; kerk |
| 15 | Minstreel | minstrel | geen | geen | geen sprite | 2 | 3 | Luit; sfeer |
| 16 | Monnik | monk | geen | geen | geen sprite | 3 | 4 | Kap, bij kerk |
| 17 | Belastinginner | taxman | geen | geen | geen sprite | 3 | 4 | Geldzak, boek |
| 18 | Wachter (piekenier) | guard / pikeman | geen | geen | geen sprite | 3 | 4 | Lange piek |
| 19 | Vlagdrager | flagman | geen | geen | geen sprite | 3 | 4 | Vlag; variant van voetsoldaat |
| 20 | Cavalerist + paard | cavalier, horse | geen | geen | geen sprite | 3 | 4 | Te paard (stallen); twee modellen op een plaat |
| 21 | Kruisboogschutter | crossbow | geen | geen | geen sprite | 3 | 4 | Origineel 2 frames; variant van boogschutter |
| 22 | Bommenwerper | bombman | geen | geen | geen sprite | 3 | 4 | Bommen; gebruikt `Effects/shrapnel` |
| 23 | Trebuchet (geschut + bemanning) | trebuchet | geen | geen | geen sprite | 3 | 4 | Belegeringswapen; een plaat met het gebouw/object |
| 24 | Dwerg | dwarf-like | geen | geen | geen sprite | 3 | 4 | Alleen draw-code; onzeker |

## 3. Vijanden en wezens — 9 rijen

| Nr | Naam | Origineel | Sprites (rel. aan `Sprites/`) | Portret | Richt./staten | Prio | Batch | Opmerking |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 25 | Wolf (+ donkere wolf) | wolf, dark wolf | `A/wolf.png`, `A/wolfstil.png`, `A/wolfatta.png`, `A/wolfdead.png` | geen | 1 r, 4 | 1 | 1 | Eerste vijand; grijs, rode ogen, eet baby's; donkere wolf = recolor op dezelfde plaat |
| 26 | Zombie | zombie | `A/zombie.png`, `A/zombatta.png`, `A/zombdead.png` | geen | 1 r, 3 | 1 | 1 | Groen oog, bruine lompen; ook via tovenaarsspreuk |
| 27 | Wesp (+ bloedwesp) | wasp, blood wasp | `A/wasp.png`, `A/waspat.png`, `A/waspdead.png`, `A/bloodwsp.png`, `A/bloodead.png` | geen | 1 r, 5 | 2 | 3 | Vliegend, geel; bloedwesp rood; een plaat |
| 28 | Vleermuis | bat | `A/bat.png`, `A/batatta.png`, `A/deadbat.png` | geen | 1 r, 3 | 2 | 3 | Vliegend, zwart; grote spanwijdte |
| 29 | Reus | giant | `A/giant.png`, `A/gianstil.png`, `A/gianatt.png`, `A/giandead.png` | geen | 1 r, 4 | 2 | 4 | Bloot bovenlijf, maliënbroek, bijl; veel groter dan bumpkin |
| 30 | Ogre | ogre | `A/ogrestil.png`, `A/ogrewalk.png`, `A/ogreatta.png`, `A/ogredead.png` | geen | 1 r, 4 | 2 | 4 | Groen, schild, strijdhamer |
| 31 | Vampier | vampire | geen | geen | geen sprite | 3 | 4 | Undead |
| 32 | Demon (fiend) | demon | geen | geen | geen sprite | 3 | 4 | Eindbaas-sfeer, bij duister altaar |
| 33 | Struikman / etende struik | bush-man | geen | geen | geen sprite | 3 | 4 | Alleen draw-code; samen met dwerg een plaat |

## 4. Boerderijdieren — 3 rijen

| Nr | Naam | Origineel | Sprites (rel. aan `Sprites/`) | Portret | Richt./staten | Prio | Batch | Opmerking |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 34 | Koe | cow | `U/cow_se.png`, `U/milking.png` | geen | 1 r, 2 | 1 | 1 | Zwartbont; melken, slacht, kalven; 51x34 px |
| 35 | Kippen-sheet (kip, kuiken, ei) | Chicken, ChickenEgg | `U/Chicken.png`, `U/ChickenEgg.png` | geen | 1 r, 2 | 1 | 1 | Een plaat voor 3 onderwerpen; kuiken heeft geen sprite |
| 36 | Kalf + varken | calf, pig | geen | geen | geen sprite | 3 | 5 | Een plaat; varken alleen in boerderij-animatie |

## 5. Gebouwen — 26 rijen

| Nr | Naam | Origineel | Sprites (rel. aan `Sprites/`) | Portret | Richt./staten | Prio | Batch | Opmerking |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 37 | Gereedschapsloods | Toolshed | `B/Toolshed.png`, `B/ToolshedDoor.png` | geen | 1 r, 2 delen | 1 | 1 | 162x129; deur is apart animatiedeel |
| 38 | Melkerij / boerderij | Dairy | `B/Dairy.png`, `B/DairyDoor.png` | geen | 1 r, 2 delen | 1 | 1 | 213x160, grootste; research: farm met koestal |
| 39 | Molen | Mill | `B/Mill.png`, `B/MillDoor.png`, `B/MillSails.png` | geen | 1 r, 3 delen | 1 | 1 | Wieken zijn eigen draaideel |
| 40 | Kippenhok | ChickenCoop | `B/ChickenCoop.png` | geen | 1 r, 1 | 1 | 1 | 66x45, klein |
| 41 | Voetsoldatengilde | footmans guild | geen | geen | geen sprite | 1 | 2 | Eerste gilde |
| 42 | Boogschuttersgilde | archers guild | geen | geen | geen sprite | 1 | 2 | Eerste gilde |
| 43 | Bouwersgilde | builders guild | geen | geen | geen sprite | 1 | 2 | Onduidelijk of de loods dit is |
| 44 | Waterput | well | geen | geen | geen sprite | 1 | 2 | Water is een behoefte |
| 45 | Bakkerij | bakery | geen | geen | geen sprite | 1 | 2 | Tarwe naar brood |
| 46 | Akker (kaal + rijp) | WheatField | `B/WheatField.png`, `B/WheatField_grown.png` | geen | 1 r, 2 stadia | 1 | 2 | Seizoensplant; een plaat met beide stadia |
| 47 | Dorpsprops: kampvuur, houtstapel, steenhoop | Campfire, Logpile, Rockpile | `B/Campfire.png`, `B/Logpile.png`, `B/Rockpile.png` | geen | 1 r, 3 | 1 | 2 | Een plaat voor 3 grondstofprops; kampvuur ook missiegebouw |
| 48 | Stadhuis | town hall | geen | geen | geen sprite | 2 | 2 | Belasting; groot |
| 49 | Hek / muur / poort | fence, stone wall, gate | geen | geen | geen sprite | 2 | 2 | Een plaat; sneeuwhek in code aanwezig |
| 50 | Brouwerij | brewery | geen | geen | geen sprite | 2 | 3 | Appels naar cider |
| 51 | Kerk | church | geen | geen | geen sprite | 2 | 3 | Priester, begraafplaats |
| 52 | Ridderlijke gilde | knights guild | geen | geen | geen sprite | 2 | 3 |  |
| 53 | Tovenaarsgilde | wizards guild | geen | geen | geen sprite | 2 | 3 |  |
| 54 | Minstrelsgilde | minstrels guild | geen | geen | geen sprite | 2 | 3 |  |
| 55 | Stallen | stables | geen | geen | geen sprite | 2 | 3 | Cavaliers en paarden |
| 56 | Gevangenis | prison | geen | geen | geen sprite | 2 | 3 | Dorpelingen arresteren |
| 57 | Uitkijkpost | lookout post | geen | geen | geen sprite | 2 | 3 |  |
| 58 | Missiegebouwen A: kapel, barak, kasteel | chapel, barrack, castle | geen | geen | geen sprite | 3 | 5 | Een plaat voor 3; alleen missies |
| 59 | Missiegebouwen B: toren, hut (cabin), tent | tower, cabin, keep/tent | geen | geen | geen sprite | 3 | 5 | Een plaat voor 3 |
| 60 | Tempel + teleporttempel | temple, teleport temple | geen | geen | geen sprite | 3 | 5 | Twee naast elkaar op een plaat |
| 61 | Duister altaar | dark altar | geen | geen | geen sprite | 3 | 5 | Bij vampier/demon |
| 62 | Boutval (gebouw) | bolt trap | geen | geen | geen sprite | 3 | 5 | Zie ook vallen-sheet |

## 6. Props en effecten — 13 rijen

| Nr | Naam | Origineel | Sprites (rel. aan `Sprites/`) | Portret | Richt./staten | Prio | Batch | Opmerking |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 63 | Bomen-sheet (groot, middel, klein) | tree01/05, 02/04, 10/11 | `T/tree01.png`, `T/tree05.png`, `T/tree02.png`, `T/tree04.png`, `T/tree10.png`, `T/tree11.png` | geen | 1 r, 6 | 1 | 2 | Een plaat; seizoensvarianten in `SeasonalTreeTile.cs` |
| 64 | Rots + zandheuvel | rock01, sandhill | `T/rock01.png`, `T/sandhill.png` | geen | 1 r, 2 | 2 | 2 | Een plaat |
| 65 | Vallen-sheet (6) | spike, mine, flame, gas, bolt, oil | geen | geen | geen sprite | 3 | 5 | Een plaat |
| 66 | Artefacten-sheet 1 (bekers, zwaard, helm, ...) | artefacten | geen | geen | geen sprite | 3 | 5 | ~15 artefacten over 2 platen |
| 67 | Artefacten-sheet 2 (ring, schild, sleutel, ...) | artefacten | geen | geen | geen sprite | 3 | 5 |  |
| 68 | Graven / doodskist | grave, coffin | geen | geen | geen sprite | 3 | 5 | Priester begraaft |
| 69 | Bouwgereedschap (zaag, pikhouweel) | saw, pick | `B/saw.png`, `B/vsaw.png`, `B/pick.png`, `B/vpick.png` | geen | 1 r, 4 | 3 | 5 | Animatieprops bij bouwen; 'v' = variant (onduidelijk) |
| 70 | Winterbomen en sneeuw | GrassWinter | `T/GrassWinter.png` | geen | 1 r, 1 | 3 | 6 | Sneeuwvarianten van de bomen-sheet |
| 71 | Vuur, rook, explosie | Flames | `Effects/Flames.png` | geen | 1 r, 1 | 3 | 6 | Effect-sheet |
| 72 | Projectielen (pijl, bout, steen, bom) | shrapnel | `Effects/shrapnel.png` | geen | 1 r, 1 | 3 | 6 | Een plaat |
| 73 | Spreukeffecten (14) | 14 spells | geen | geen | geen sprite | 3 | 6 | 2 platen van 7 |
| 74 | Draagprops (zak, emmer, korf) | f_sack, f_milk | `U/m_sack.png`, `U/f_milk.png` | geen | 1 r, 2 | 3 | 6 | Bij werkanimaties |
| 75 | Regen- en onweerswolken | rain/thunder | geen | geen | geen sprite | 3 | 6 | Weereffect |

## Tellingen
- Rijen (onderwerpen): Bumpkins 9, Gilde- en overige eenheden 15, Vijanden en wezens 9, Boerderijdieren 3, Gebouwen 26, Props en effecten 13 = **75** rijen, plus 2 klaar. 29 daarvan hebben sprites in het project, 46 niet.

## Batches (ongeveer 14 beelden per dag, prio 1 eerst)

| Batch | Beelden | Inhoud |
| --- | --- | --- |
| 1 | 14 | Vrouw; Jongen; Meisje; Oudere man; Oudere vrouw; Bouwer; Wolf; Zombie; Koe; Kippen-sheet; Gereedschapsloods; Melkerij / boerderij; Molen; Kippenhok |
| 2 | 14 | Baby; Voetsoldaat; Boogschutter; Voetsoldatengilde; Boogschuttersgilde; Bouwersgilde; Waterput; Bakkerij; Akker; Dorpsprops: kampvuur, houtstapel, steenhoop; Stadhuis; Hek / muur / poort; Bomen-sheet; Rots + zandheuvel |
| 3 | 14 | Ridder; Tovenaar; Priester; Minstreel; Wesp; Vleermuis; Brouwerij; Kerk; Ridderlijke gilde; Tovenaarsgilde; Minstrelsgilde; Stallen; Gevangenis; Uitkijkpost |
| 4 | 14 | Bruid + bruidegom; Monnik; Belastinginner; Wachter; Vlagdrager; Cavalerist + paard; Kruisboogschutter; Bommenwerper; Trebuchet; Dwerg; Reus; Ogre; Vampier; Demon; Struikman / etende struik |
| 5 | 12 | Skelet; Kalf + varken; Missiegebouwen A: kapel, barak, kasteel; Missiegebouwen B: toren, hut; Tempel + teleporttempel; Duister altaar; Boutval; Vallen-sheet; Artefacten-sheet 1; Artefacten-sheet 2; Graven / doodskist; Bouwgereedschap |
| 6 | 7 | Winterbomen en sneeuw; Vuur, rook, explosie; Projectielen; Spreukeffecten; Draagprops; Regen- en onweerswolken |

Totaal **75 beelden in 6 batches**. Batch 1 is het speelbare dorp (vrouw, kinderen, ouderen, bouwer, koe, kippen, eerste vijanden, vier gebouwen), batch 2 de eerste gilden en basisgebouwen.

## Open vragen
1. **Portretten**: alleen `avatar_man.png` is bekend en zit niet in het Unity-project (eigen screenshot-crop). Portretten van vrouw, kinderen, bouwer en de gilden ontbreken; screenshots van het origineel nodig.
2. Gilde-eenheden, vampier, demon, struikman en dwerg hebben **geen sprite**; uiterlijk komt uit screenshots of eigen ontwerp.
3. Paladijn(sgilde)? Onderzoek: waarschijnlijk de cavalerist van de stallen.
4. Is de gereedschapsloods (`Toolshed`) het bouwersgilde-gebouw?
5. `Dairy` heet in de code melkerij; research noemt "farm" met koestal. Welke naam?
6. Wat zijn `vsaw`/`vpick` (variant of andere hand)?
7. Kuiken en kalf hebben geen sprite (ei wel).
8. `bushk_rp` lijkt het rugaanzicht van de bouwer; onzeker.
9. Schaal reus/ogre t.o.v. de 1,37 m man: sprites 34x41 en 37x47 px suggereren 1,5 tot 2x.
