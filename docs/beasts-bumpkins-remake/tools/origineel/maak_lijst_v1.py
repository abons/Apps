import os, base64, html, io
SC = "C:/Users/Axel/AppData/Local/Temp/claude/E--werk-androidApps-Apps/16e99493-ac86-47c7-921f-1d215c266f51/scratchpad/"
R = SC + "Unity_bumpkins/Bumpkins/Assets/Resources/"
MD = "E:/werk/androidApps/Apps/docs/beasts-bumpkins-remake/concept/lijst.md"
HTML = SC + "concept/lijst.html"
AV = "bumpkin/ref/avatar_man.png"
N = "geen"

# (naam, origineel, sprites[], portret, richt/staten, prio, batch, samen_met_vorige(0/1), beelden, opmerking)
def r(naam, orig, spr, port, rs, prio, batch, opm, samen=0, beelden=1):
    return dict(naam=naam, orig=orig, spr=spr, port=port, rs=rs, prio=prio, batch=batch, opm=opm, samen=samen, beelden=beelden)

U = lambda *n: ["Units/%s.png" % x for x in n]
A = lambda *n: ["Animals/%s.png" % x for x in n]
B = lambda *n: ["Buildings/%s.png" % x for x in n]
T = lambda *n: ["Terrain/%s.png" % x for x in n]

G = []
O = lambda *n: ["bb_original/%s.png" % x for x in n]  # lokale uitpak van het origineel (niet in git); sheets/ heeft alle frames
BU = lambda n: "bb_original/portret/bust%02d.png" % n  # 18 portretten uit statbust (102x102)
G.append(("Klaar (goedgekeurd)", [
    r("Boerenhut", "House", B("House", "HouseDoor"), N, "1 richting, 2 delen", "klaar", "-", "Blender + realtime-glb klaar (`../modellen/peasant_hut*.glb`)"),
    r("Volwassen man", "m_still / m_walk", U("m_still", "m_walk", "m_sack", "mthrow", "m_harvest", "d_male"), AV, "1 richting, 6 poses", "klaar", "-", "Rig + 6 animaties klaar (`../modellen/bumpkin/`)"),
]))
G.append(("1. Bumpkins (dorpelingen)", [
    r("Vrouw", "f_still / f_walk", U("f_still", "f_walk", "f_sack", "f_milk", "fthrow", "f_harvest", "milking", "d_fema"), N, "1 r, 8 poses", 1, 1, "Blond, grijsgroen jasje, paarse rok; melkt, oogst. Zelfde stijl als man (hergebruik)"),
    r("Jongen", "kidm", U("kidm", "d_kidm"), N, "1 r, 2", 1, 1, "0,81x man; paars hemd, bruin haar"),
    r("Meisje", "kidf", U("kidf", "d_kidf"), N, "1 r, 2", 1, 1, "0,81x man; blond, paarse jurk"),
    r("Oudere man", "elderm", U("elderm"), N, "1 r, 1", 1, 1, "Wit haar, wandelstok met ranken, licht gebogen (0,96x)"),
    r("Oudere vrouw", "elderf", U("elderf"), N, "1 r, 1", 1, 1, "Zelfde stok-silhouet als oudere man"),
    r("Bouwer (bouwersgilde-eenheid)", "reparman / rp_still / bushk_rp", U("reparman", "rp_still", "bushk_rp", "hammer", "d_buil"), N, "1 r, 5", 1, 1, "Blauwe tuniek, gele muts, hamer; bushk_rp lijkt rugaanzicht"),
    r("Baby", "baby", U("baby") + O("baby"), N, "1 r, 4 frames", 2, 2, "Ligt in doek; kan op de kinderplaat"),
    r("Bruid + bruidegom", "bride, groom", O("d_bride", "d_groom", "f_weddin", "m_weddin"), N, "8 r x 6 lopen, 5 dood", 3, 5, "Een plaat met beide; bruid in lichtgrijze jurk, bruidegom met hoge hoed; trouwlopen en dood"),
    r("Skelet (resten)", "skeleton", U("skeleton") + O("skeleton", "mineskul"), N, "1 r, 1", 3, 6, "Rest na dood; prop; mineskul = botten bij de mijn"),
    r("Beul + hakblok", "executioner, execblok", O("execstil", "m_exec", "execblok"), N, "1 r, 13 frames + blok", 3, 6, "Zwarte kap, bijl; werkt aan de hakblok (gevangenis/straf). Nieuw uit origineel"),
]))
G.append(("2. Gilde- en overige eenheden", [
    r("Voetsoldaat", "footman", O("ft_still", "footwalk", "footatta", "footdie", "d_foot"), BU(4), "8 r x 6 lopen, 8 x 6 slaan, 1 dood", 1, 3, "Eerste gilde; paars-wit schild, zwaard, helm; portret = gok"),
    r("Boogschutter", "archer", O("arc_stil", "archer", "archshoo", "d_arch"), BU(10), "8 r x 6 lopen, 32 schieten", 1, 3, "Eerste gilde; boog, pijlkoker, paarse kap/veer"),
    r("Ridder", "knight", O("kn_still", "knigwalk", "knigatta", "knigdie", "d_knig"), BU(9), "8 r x 6 lopen, 56 slaan, 7 dood", 2, 3, "Plaatharnas, groot zwaard, wit-paars schild; aanval 107x64 px (grote uithaal)"),
    r("Tovenaar", "wizard", O("wz_still", "wizwalk", "wizcast", "wizaim", "wizadie", "d_wiza"), BU(11), "8 r x 6 lopen, 8 cast, 8 richten", 2, 3, "Paarse puntmuts en mantel, baard, staf met gouden kop"),
    r("Priester", "priest", O("pr_still", "priest", "pri_heal", "d_prie"), BU(15), "8 r x 6 lopen, 11 genezen", 2, 3, "Zwart habijt, paarse accenten, priesterkraag; zegent, begraaft; kerk"),
    r("Minstreel", "minstrel", O("minstrel", "minlyre", "minbow"), BU(1), "8 r x 6 lopen, 5 luit, 5 boog", 2, 3, "Paars kostuum, luit; sfeer; heeft ook een boog-animatie"),
    r("Monnik", "monk", O("mk_stil", "monkwalk"), N, "8 r x 6 lopen, 4 still", 3, 5, "Bruine pij; mk_stil draagt een net/zak; bij kerk"),
    r("Belastinginner", "taxman", O("tx_still", "taxman", "d_taxm"), BU(16), "8 r x 6 lopen, 5 dood", 3, 5, "Hoge zwarte hoed, geldzak; portret met gouden muntjes"),
    r("Wachter (piekenier)", "guard / pikeman", O("pk_still", "pikewalk", "pikeatta", "pikedie", "d_pike"), BU(14), "8 r x 6 lopen, 24 steken", 3, 5, "Bruin leer, lange piek met bijl-kop; portret met bijl"),
    r("Vlagdrager", "flagman", O("fg_still", "flagwalk", "flagdie", "flag"), BU(5), "8 r x 6 lopen, 10 vlag", 3, 5, "Paars-wit maliënkap met paarse vlag; variant van voetsoldaat"),
    r("Cavalerist + paard", "cavalier, horse", O("cavalier", "cavatta", "d_cava"), BU(6), "8 r x 4 lopen, 40 aanval, 5 dood", 3, 5, "Een model: ruiter met lans op paars-wit paard (55x48 px); geen los paard; portret = gok"),
    r("Kruisboog (wielgeschut)", "crossbow", O("crossbow", "cbolt"), N, "8 r x 4, bout 8", 3, 5, "Geen schutter maar een kruisboog op wielen (belegering), net als de trebuchet"),
    r("Bommenwerper", "bombman", O("bombman", "bombfroz"), N, "8 r x 6, 1 bevroren", 3, 5, "Klein zwart figuur met bom; gebruikt `Effects/shrapnel`; bombfroz = blauw bevroren"),
    r("Trebuchet (geschut + bemanning)", "catapult", O("catapult", "catfire", "ctnomove", "ctnofire"), N, "8 r x 4, schieten", 3, 5, "Houten katapult op stenen wielen, paarse beladen arm (69x49); ct* = richtingvarianten lopen/vuren"),
    r("Nar / jongleur", "juggler, jester", O("juggler", "minjuggl", "d_jest"), BU(8), "1 r x 5 frames", 3, 5, "Paars narrenkostuum, balletjes; variant van de minstreel. Nieuw uit origineel"),
]))
G.append(("3. Vijanden en wezens", [
    r("Wolf (+ donkere wolf)", "wolf, dark wolf", A("wolf", "wolfstil", "wolfatta", "wolfdead"), N, "1 r, 4", 1, 1, "Eerste vijand; grijs, rode ogen, eet baby's; donkere wolf = recolor op dezelfde plaat"),
    r("Zombie", "zombie", A("zombie", "zombatta", "zombdead"), N, "1 r, 3", 1, 1, "Groen oog, bruine lompen; ook via tovenaarsspreuk"),
    r("Wesp (+ bloedwesp)", "wasp, blood wasp", A("wasp", "waspat", "waspdead", "bloodwsp", "bloodead") + O("wasp", "waspat", "bloodwsp", "hive"), N, "8 r x 6, 5 dood", 2, 3, "Vliegend, geel; bloedwesp rood; een plaat; hive = bijenkorf (64x63) erbij"),
    r("Vleermuis", "bat", A("bat", "batatta", "deadbat") + O("bat", "batatta", "deadbat", "vampbat"), N, "8 r x 6, 8 aanval", 2, 3, "Vliegend, zwart; grote spanwijdte; vampbat = vampier in vleermuisvorm"),
    r("Reus", "giant", A("giant", "gianstil", "gianatt", "giandead") + O("gianstil", "giant", "gianatt", "giandead"), N, "8 r x 6, 32 aanval, dood", 2, 5, "Bloot bovenlijf, maliënbroek, bijl; ~1,35x de man (36 px tegen 26)"),
    r("Ogre", "ogre", A("ogrestil", "ogrewalk", "ogreatta", "ogredead") + O("ogrestil", "ogrewalk", "ogreatta", "ogredead", "ogrefire"), N, "8 r x 6, 56 aanval, dood", 2, 5, "Groen, rond houten schild, hoge staf met bol; ~1,8x de man incl. staf (47 px); ogrefire = magische vonk"),
    r("Vampier", "vampire", O("vampstil", "vampbat", "vampdead"), N, "6 still, 7 vleermuis, 11 dood", 3, 5, "Zwarte mantel met hoge kraag, rode kam; 1,2x de man; wisselt in vleermuis"),
    r("Demon (fiend)", "demon / fiend", O("fiend", "darkdead"), N, "8 r x 8 (64 frames)", 3, 5, "Gevleugelde duivel, rood-grijs, 88x71 px (groter dan de reus); eindbaas-sfeer, bij duister altaar"),
    r("Struikman / etende struik", "bush-man", O("bushman"), N, "6 frames", 3, 5, "Een dennenboom met ogen (29x48 px); geen dwerg erbij: `dw_*` blijkt een zwarte wolf"),
]))
G.append(("4. Boerderijdieren", [
    r("Koe", "cow", U("cow_se", "milking"), N, "1 r, 2", 1, 1, "Zwartbont; melken, slacht, kalven; 51x34 px"),
    r("Kippen-sheet (kip, kuiken, ei)", "Chicken, ChickenEgg", U("Chicken", "ChickenEgg"), N, "1 r, 2", 1, 1, "Een plaat voor 3 onderwerpen; kuiken heeft geen sprite"),
    r("Kalf + varken", "calf, pig", O("cowborn", "pigsy"), N, "2 + 1 frame", 3, 6, "Een plaat; kalf ligt wit-zwart (34x21), varken staat in een kleine pen-tegel (26x20); beide klein"),
]))
G.append(("5. Gebouwen", [
    r("Gereedschapsloods", "Toolshed", B("Toolshed", "ToolshedDoor"), N, "1 r, 2 delen", 1, 1, "162x129; deur is apart animatiedeel"),
    r("Melkerij / boerderij", "Dairy", B("Dairy", "DairyDoor"), N, "1 r, 2 delen", 1, 1, "213x160, grootste; research: farm met koestal"),
    r("Molen", "Mill", B("Mill", "MillDoor", "MillSails"), N, "1 r, 3 delen", 1, 1, "Wieken zijn eigen draaideel"),
    r("Kippenhok", "ChickenCoop", B("ChickenCoop"), N, "1 r, 1", 1, 1, "66x45, klein"),
    r("Voetsoldatengilde", "footmans guild", O("fguild", "footdoor", "mn_foot"), N, "2 frames + deur", 1, 3, "Eerste gilde; ronde stenen toren met paarse rand en strodak-bijgebouw (118x129)"),
    r("Boogschuttersgilde", "archers guild", O("fletcher", "archdoor", "mn_arch"), N, "2 frames + deur", 1, 3, "Eerste gilde; strodak met schietschijf en pijl (132x139)"),
    r("Bouwersgilde", "builders guild", O("workover", "l_work01", "mn_work"), N, "alleen deur/overlay", 1, 3, "Gebouw zelf niet gevonden (alleen deur `workover` en pictogram); mogelijk de gereedschapsloods"),
    r("Waterput", "well", O("well", "wellover", "wellwate"), N, "2 frames + overlay + water", 1, 2, "Water is een behoefte; stenen huisje met paars dak en blauwe vijver (133x110)"),
    r("Bakkerij", "bakery", O("bakery", "bakeover", "bakeanim"), N, "2 frames + deur + anim", 1, 3, "Tarwe naar brood; strodak met tonschoorsteen (202x180); bakeanim = windmolen met wieken"),
    r("Akker (kaal + rijp)", "WheatField", B("WheatField", "WheatField_grown") + O("wheat", "wheatovr", "crops", "f_scythe"), N, "1 r, 2 stadia", 1, 2, "Seizoensplant; een plaat met beide stadia; f_scythe = maaien"),
    r("Dorpsprops (kampvuur, houtstapel, steenhoop)", "Campfire, Logpile, Rockpile", B("Campfire", "Logpile", "Rockpile") + O("campfire", "logs", "pile01"), N, "1 r, 3", 1, 2, "Een plaat voor 3 grondstofprops; kampvuur ook missiegebouw"),
    r("Stadhuis", "town hall", O("th_nodo", "th_over", "ni_townh"), N, "2 frames + overlay", 2, 3, "Belasting; groot; onzeker welk gebouw het stadhuis is: `th_nodo` (strodak met klok) of een ander; `th_over` = steen met bruin dak"),
    r("Hek / muur / poort", "fence, stone wall, gate", O("fence", "gfence", "wall", "gate", "mgate", "bridge"), N, "16 stukken per hek/muur", 2, 2, "Een plaat; houten hek, graf-hek, stenen muur, houten poort, stenen poort, brug; sneeuwhek (`snwfence`) ook"),
    r("Brouwerij", "brewery", O("brewery", "brewover", "brewbig", "beer"), N, "2 frames + deur", 2, 3, "Appels naar cider; strodak met ton en pijp (179x153); beer = bierton"),
    r("Kerk", "church", O("church", "churover", "crucifix"), N, "2 frames", 2, 4, "Priester, begraafplaats; stenen toren met paars dak + kerkschip (220x220); ni_cathd = nachtversie (kathedraal)"),
    r("Ridderlijke gilde", "knights guild", O("barrack", "mn_keep"), N, "onzeker", 2, 4, "Eigen sprite niet gevonden; kandidaat `barrack` (222x143, tonvormige daken) of `keep`"),
    r("Tovenaarsgilde", "wizards guild", O("treehous", "mn_wiz"), N, "1 frame", 2, 4, "Waarschijnlijk de boomhut `treehous` (118x157, ladder, strodak): pictogram mn_wiz is bruin met boom"),
    r("Minstrelsgilde", "minstrels guild", O("pub", "mn_pub"), N, "onzeker", 2, 4, "Eigen sprite niet gevonden; kandidaat de taverne `pub` (zie Herberg)"),
    r("Stallen", "stables", O("stables", "stabdoor", "mn_stabl"), N, "2 frames + deur", 2, 4, "Cavaliers en paarden; rond strodak met hoefijzer (137x141)"),
    r("Gevangenis", "prison", O("jail", "jaildoor", "mn_jail"), N, "2 frames + deur", 2, 4, "Dorpelingen arresteren; stenen cel met zwarte kogel en ketting (140x124)"),
    r("Uitkijkpost", "lookout post", O("lookout", "look_ov", "mn_look"), N, "1 frame + overlay", 2, 4, "Houten wachttoren met strodak (189x159)"),
    r("Herberg (pub)", "pub", O("pub", "pubover", "ni_pub"), N, "3 frames + nacht", 2, 4, "Brede taverne met bruin dak (260x131); drinkende dorpelingen (f_drink/m_drink). Nieuw uit origineel"),
    r("Graanschuur (granary)", "granary", O("granover", "mn_gran", "ni_gran"), N, "alleen overlay", 3, 7, "Gevonden zijn alleen dakoverlay (97x77) en pictogram; stenen muur, bruin dak. Nieuw uit origineel"),
    r("Appelboom + appelpluk", "apple tree", O("appltree", "apples", "appsprig", "f_shaker"), N, "2 frames + schudden 21", 3, 7, "Appels voor de brouwerij; f_shaker/m_shaker = dorpeling die schudt. Nieuw uit origineel"),
    r("Missiegebouwen A: kapel, barak, kasteel", "chapel, barrack, castle", O("chapel", "barrack", "castle"), N, "1 + 1 + 3 frames", 3, 6, "Een plaat voor 3; alleen missies; kapel (221x221) lijkt op de kerk, kasteel 210x181"),
    r("Missiegebouwen B: toren, hut (cabin), tent", "tower, cabin, keep/tent", O("towin", "towreal", "cabin", "hut", "tent", "keep"), N, "diverse", 3, 6, "Een plaat voor 3 (toren, houten hut `cabin`/`hut`, gestreepte tent); `keep` (287x211) is een paarse burcht"),
    r("Tempel + teleporttempel", "temple, teleport temple", O("pagnbulk", "paganrok"), N, "1 + 1", 3, 6, "Twee naast elkaar op een plaat; heidense stenen cirkel met pentagram (115x94) en losse boog"),
    r("Duister altaar", "dark altar", O("altar", "summon", "landmark"), N, "2 frames", 3, 6, "Bij vampier/demon; rood pentagram met kaarsen (57x38); summon = stronk met schedel"),
    r("Boutval (gebouw)", "bolt trap", O("bolt", "cbolt"), N, "4 + 8", 3, 6, "Zie ook vallen-sheet; bolt = pijl-projectiel"),
    r("Zombiegraf (zombie tomb)", "zombie tomb", O("zombtomb", "spkzomb", "zombglow"), N, "1 + 2", 3, 6, "Stenen kist met kruis, begroeid (86x97); zombie kruipt eruit. Nieuw uit origineel"),
    r("Spookboom + wortelaltaar", "weird tree", O("spooky", "landmark", "stump"), N, "4 frames", 3, 6, "Dode boom met kale takken (41x46), boomwortel met schedels. Nieuw uit origineel"),
]))
G.append(("6. Props en effecten", [
    r("Dennen-sheet (grote den, spar, jonge den, stronk)", "bigfir, tree10, sap_fir, stump", O("bigfir", "tree10", "sap_fir", "stump"), N, "1 r, 4", 1, 2, "Map 1: 38 van 42 bomen zijn id 0/6 (grote den, spar); jonge den en stronk voor kappen/herplanten; extra dennen op bosgrond"),
    r("Loofbomen + struiken", "tree01-03, shrub", O("tree01", "tree02", "tree03", "shrub", "shrub_b"), N, "1 r, 5", 2, 2, "Map 1: id 5 (4 stuks) is onbekend welke loofboom; struiken (`shrub`) als gras-vulling. Winterbomen bewust niet"),
    r("Rotsen-sheet (6 vormen)", "rock01-06, rocks", O("rock01", "rock02", "rock03", "rock04", "rock05", "rock06", "rocks"), N, "1 r, 6 + steentje", 1, 2, "Map 1: 172 rotstegels + 157 rotsrand-tegels vormen de boog langs N en W; losse rotsen als scatter"),
    r("Rotsrand / klif", "rockrim", O("rockrim"), N, "1 r, 1", 1, 2, "Randstuk van de rotsboog (157 tegels op map 1); modulair stuk waar de rots in het gras overgaat"),
    r("Kaartprops (paddenstoel, zilveren beker, vlag)", "_mushroom (83), silver goblet, flag", O("gob_silv", "flag"), N, "1 r, 3", 1, 2, "Map 1: 7 paddenstoelen (geen eigen sprite gevonden; bruine hoed uit screenshot `mission1.png`), beker (tutorial: naar de vlag), vlag = startpunt"),
    r("Terreintexturen (gras, bosgrond, rots, zand, ondiep water)", "maptile", O("maptile"), N, "5 vierkante swatches", 1, 2, "Map 1: gras 1044, bosgrond 51 (bruin onder dennen), rots 172, zand/strand, water 2384 tegels; seamless top-down, geen object"),
    r("Vallen-sheet (6)", "spike, mine, flame, gas, bolt, oil", O("spike", "d_spike", "mineskul", "flamepit", "gas", "bolt", "oilslick"), N, "1 r, 6 vallen", 3, 6, "Een plaat; pennen, mijn (schedel), vlampit, gaswolk, bout, olievlek"),
    r("Artefacten-sheet 1 (bekers, zwaard, helm, ...)", "artefacten", O("gob_gold", "gob_silv", "sword", "mace", "helmet", "holyswrd", "goldcoin"), N, "1 r, ~7", 3, 6, "~15 artefacten over 2 platen"),
    r("Artefacten-sheet 2 (ring, schild, sleutel, ...)", "artefacten", O("magring", "mainring", "shield", "mkey", "cloak", "crucifix", "pot_red", "pot_blue", "pot_gren", "shovel"), N, "1 r, ~10", 3, 6, ""),
    r("Graven / doodskist", "grave, coffin", O("grave", "grave01", "body"), N, "2 + 1", 3, 6, "Priester begraaft; grafkelder (66x49) en kruis; `body` is een rood-geruite zak/stof, geen lijkkist"),
    r("Bouwgereedschap (zaag, pikhouweel)", "saw, pick", B("saw", "vsaw", "pick", "vpick"), N, "1 r, 4", 3, 2, "Animatieprops bij bouwen; `v` = dezelfde animatie met een dorpeling (bruin haar) in plaats van de bouwer (blauw, gele muts)"),
    r("Winterbomen en sneeuw", "GrassWinter", T("GrassWinter"), N, "1 r, 1", 3, 7, "Sneeuwvarianten van de bomen-sheet"),
    r("Vuur, rook, explosie", "Flames", ["Effects/Flames.png"] + O("flames", "burn", "smolder", "explode", "fired"), N, "1 r, 5", 3, 7, "Effect-sheet"),
    r("Projectielen (pijl, bout, steen, bom)", "shrapnel", ["Effects/shrapnel.png"], N, "1 r, 1", 3, 7, "Een plaat"),
    r("Spreukeffecten (9 + extra)", "s_* spells", O("s_cure", "s_fear", "s_ffood", "s_fireb", "s_flash", "s_heal", "s_see", "s_summon", "s_tport", "lgtning", "equake", "acidbolt"), N, "9 s_* + 3", 3, 7, "Slechts 9 s_*-sprites (genezen, angst, voedsel, vuurbal, flits, heal, oog, oproepen, teleport) + bliksem, aardbeving, zuur; rest zelf ontwerpen", beelden=2),
    r("Draagprops (zak, emmer, korf)", "f_sack, f_milk", U("m_sack", "f_milk"), N, "1 r, 2", 3, 3, "Bij werkanimaties; de sprites zijn mensen die dragen, geen losse props: pas na de rigs"),
    r("Regen- en onweerswolken", "rain/thunder", O("rain", "cloud", "blkcloud", "lgtning"), N, "1 r, 4", 3, 7, "Weereffect"),
    r("Straatlamp en toorts", "street lamp", O("lamp", "lantern", "torch"), N, "9 + 2 + 6", 3, 7, "Straatlamp (49x40), lantaarn, brandende toorts. Nieuw uit origineel"),
    r("Meubilair: bank, stoel, kist, drinkbak", "bench, logchair, crate, trough", O("bench", "logchair", "crate", "trough", "sign", "salepost"), N, "1 r, 6", 3, 7, "Kleine props rond huizen; bord/verkoopbord. Nieuw uit origineel"),
]))

def hd(p):
    if p.startswith("bb_original/"):
        s = SC + "bb_original/sheets/" + os.path.basename(p)  # alle frames in een sheet
        return (s, True) if os.path.exists(s) else (SC + p, True)
    h = R + "Sprites-HD/" + p
    return (h, True) if os.path.exists(h) else (R + "Sprites/" + p, False)

def b64(path):
    return "data:image/png;base64," + base64.b64encode(open(path, "rb").read()).decode()

# batch tellen
tel = {}
for _, rows in G:
    for x in rows:
        if isinstance(x["batch"], int) and not x["samen"]:
            tel[x["batch"]] = tel.get(x["batch"], 0) + x["beelden"]
print(tel, sum(tel.values()))
nrows = sum(len(rows) for g, rows in G if not g.startswith("Klaar"))
gespr = sum(1 for g, rows in G if not g.startswith("Klaar") for x in rows if x["spr"])
gcount = [(g, len(rows)) for g, rows in G]
print(nrows, gespr, gcount)
