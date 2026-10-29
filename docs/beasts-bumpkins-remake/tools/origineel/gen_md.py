import json,collections
TY={1:'m',2:'v',3:'oude man?',5:'belastinginner',7:'t7',8:'t8',9:'tovenaar',10:'t10',13:'jongen',14:'meisje',16:'t16',17:'bommenwerper',19:'t19',21:'monnik',32:'prins',33:'prinses'}
NAME={
1:'Aorta (verbannen)',2:'Terug op het vasteland',3:'Gouden kelk van Barathkar',4:'Beker van Vervulling',5:'Zombiedorp en heilig zwaard',
6:'Parpton',7:'Oorlogskas',8:'Wormton en kas',9:'Tovenaarsleerling',10:'Toren der Kennis',11:'Vijandelijke enclave (Bearton)',12:'Grens: BomberMan',
13:'Ringworm en de pest',14:'Vloek van de zombies',15:'Blagton en de toverrollen',16:'Big Pockets Barry',17:'Schatkaart (40.000)',18:'Koe naar de heler',
19:'Biggunton en Sykeston',20:'Fast Fingers Freddy',21:'Goluckyton',22:'Graaf Drapoga',23:'Goud en vee',24:'Bruiloft van Lurkio',25:'Drie gebouwen (tijdslimiet)',
26:'Reus Deavo',27:'Lord Randybar (Grymton)',28:'Verdediging tegen de Dark Lord',29:'Heilige Kelk en Fontein',30:'Slotgevecht (demonen, Parpton)'}
DOEL={
1:'W: 6 dorpelingen (telling >5) en 4 koeien (>3). V: minder dan 2 dorpelingen.',
2:'W: kas >10.000. V: <2 dorpelingen. Wolven lopen los.',
3:'W: kas >25.000 (telling >24.999); de bewaakte gouden kelk naar de vlag is de snelle route. V: <2.',
4:'W: Beker van Vervulling vinden; sleutel opent poort, de zilveren beker is een val (tin), echte doel = triggerplek (41,11). V: <2.',
5:'W: heilig zwaard (52,98) halen, zombiegraf (74,37) slopen, dorp >10 mensen. V: <2.',
6:'W: Parpton (eigenaar 2, vlag 132,66) uitroeien. V: alle eigen mensen dood. Vallen.',
7:'W: kas >26.000 (meldingen bij 15k en 24k). V: alle mensen dood. Kelkenpuzzel met 2 gouden + 1 zilveren kelk.',
8:'W: kas >14.000 en Wormton (eigenaar 1) uitroeien. V: <2.',
9:'W: leerling (villager 201, 169,161) levend naar tempel (82,96); sleutel (119,159) opent poort (98,102). V: leerling sterft.',
10:'W: toren (162,131) slopen; 6 reuzen bewaken hem; monnikenwinkel verkoopt voor 10.000 (o.a. onzichtbaarheid). V: <2.',
11:'W: vijandelijk dorp (eigenaar 1) uitroeien; sleutel (58,9) opent poort naar Fontein der Jeugd (50,22). V: alle eigen mensen dood.',
12:'W: vijandelijke uitkijktoren (55,128) slopen met eigen BomberMan (villager 730, type 17), die op een eiland vastzit tot een trigger hem bevrijdt. V: eigen toren (56,41) of BomberMan weg, of <2 mensen.',
13:'W: Ringworm (eigenaar 2) uitroeien via de pest: spreukrol bij monnik voor 10.000 kopen; geen oorlog. V: alle eigen mensen dood. Timer 25.200.',
14:'W: 18.000 ticks overleven (zombiegolven, timer 32.400 voor de vloek). V: <3 dorpelingen of kerk (112,67) valt.',
15:'W: Blagton (eigenaar 3) uitroeien; hendels openen de toverkluis met spreuken. V: alle eigen mensen dood.',
16:'W: Barry (villager 13, 19,31) via 2 sleutel-poortparen naar het stadhuis (91,117) brengen. V: Barry dood of timer 36.000 (waarschuwing bij 34.200).',
17:'W: kas >40.000; schat via 7 graafplekken (schop) en dode reus. V: <2.',
18:'W: een koe naar de heler (villager 46, 152,115) brengen; alle koeien zijn dood (explosiekoeien). V: alle mensen dood.',
19:'W: Biggunton (eigenaar 1) en Sykeston (eigenaar 2) uitroeien. V: alle eigen mensen dood.',
20:'W: Freddy (villager 13 owner 3, 57,113) doden, sleutel (49,51) naar poort (24,131), goud (23,127). V: alle mensen dood.',
21:'W: Goluckyton (eigenaar 3) uitroeien; tovenaarsgilde van Chubbston slopen levert sleutel op; hendel en poort in de stad. V: alle mensen dood.',
22:'W: crucifix (56,103) via kelk bij de monniken halen en vampier (creature 3, 148,124) doden. V: alle mensen dood.',
23:'W: kas >40.000 en >15 koeien. V: alle mensen dood.',
24:'W: prins (698) en prinses (694) naar kerk (112,101) brengen; wizard Wilberforce bij rots (162,113). V: een van beiden dood. Startkas 0.',
25:'W: 3 vijandelijke gebouwen (voetvolk-, boogschutters-, ridders-gilde) veroveren. V: timer 4.320 of alle mensen dood.',
26:'W: reus Deavo (creature 95, 66,14) doden met bevrijde ridder Thrice (villager 97, naar kraal 79,26); spreuk kost 20.000. V: Thrice dood of <2.',
27:'W: Grymton (eigenaar 2) uitroeien; Gruffton (eigenaar 1) is de tweede stad en meldt het als het valt. V: alle mensen dood.',
28:'W: alle aanvallers (eigenaar 4) verslaan; 1 seizoen (2.880 ticks) voorbereiding. V: een van 6 gilde-/kerkgebouwen valt of alle mensen dood.',
29:'W: zilveren beker (159) naar Heilige Fontein (19,51); doolhof, meisje meebrengen voor het huwelijk. V: alle mensen dood.',
30:'W: Parpton (eigenaar 2) slopen; demonen via donker altaar (164,59) vraagt een offer van een eigen dorpeling; 4 vlammen-timers van 36. V: alle mensen dood.'}
NIEUW={
1:'Boerenhut, bouwersgilde (bouwer 2x sneller), bakkerij, boerderij, kippenhok, koeien claimen, hek en poort, zilveren beker. Seizoenen.',
2:'Wolven (13,23) die kinderen en vee pakken; omheining helpt; prijzen/geluk; pensioen; items zoeken (goud, drankjes).',
3:'Gildelimiet 6 leden; putten; voetvolkgilde al aanwezig; bewaakte gouden kelk; twee wolf-soorten (13,29),(14,24).',
4:'Magische sleutel en poort; valstrik-beker; eerste (21,18)-wezens (vermoedelijk apen).',
5:'Zombies (eigenaar 4, type 7), graven en zombiegraf, heilig zwaard; eerste wegversperring met voetvolkgilde.',
6:'Eerste vijandig dorp (Parpton); spijkervallen en mijnen; tovenaar met spreuken; bouwbalk scrollen; toren.',
7:'Kerk (priesters, genezing, huwelijken); kelkenpuzzel; beloningsberichten bij 15k/24k/26k.',
8:'Wormton (eerste echte rivaal naast Parpton); geldplicht plus aanval.',
9:'Tovenaarsleerling (type 9), tempel, sleutel/poort, vijandelijk dorp Wormton.',
10:'Monnikenwinkel (verkoopt 3 items), reuzen (16,27)/(22,25), donker altaar, onzichtbaarheidsmantel, bos zonder water, hendels.',
11:'Boogschuttersgilde, uitkijkpost, ridderlijk gilde, stadhuis/belastinginner, Fontein der Jeugd, tovenaar Wilberforce.',
12:'BomberMan (type 17), trigger-vlakken (klasse 87), 5 spawners (vijandelijke soldaten komen na).',
13:'Gevangenis (pikenier), misdaad, pest-spreuk, kloosters met monniken (type 21), rivaal-lord.',
14:'Zombievloek, zieken verzorgen, kerk beschermen; doodskisten, graven, zombiegraf.',
15:'Toverrollen en spreuken, tovenaarsgilde voor de speler, hendels; zeer groot vijanddorp (17 vijandelijke mensen, 36 vallen).',
16:'Belastinginner Barry, stadhuis, sleutel/poort-ketens, tijdslimiet 36.000.',
17:'Schatkaart met 7 graafplekken en schop, dode reus; slechts 5.000 startkas.',
18:'Explosiekoeien (alle koeien dood), heler (monnik), vee zoeken; 3 wezen-spawners.',
19:'Twee vijandelijke dorpen tegelijk; geen extra items.',
20:'Dief Freddy, stadhuis voor de speler, bandietenschuilplaats met sleutel.',
21:'Brouwerij (cider), appelbomen, stallen (cavaliers) en minstreelsgilde; stad Goluckyton met poort en hendel; 19 vijandelijke gebouwen.',
22:'Vampier (18,31), crucifix, monniken, kelk-aflevering; 5 spawners; 71 muren.',
23:'Rijke kaart: 17 goudbuidels, 11 koeien, vijand Wigginston (eigenaar 1) met 6 mensen.',
24:'Prins en prinses (types 32/33), Wilberforce, 8 eigen krijgers (type 8) en 0 gouden startkas; geen dorp.',
25:'Alleen krijgers (14 stuks): voetvolk 8, ridders 19, boogschutters 16, type 7 en 10; kasteelkaart zonder eigen dorp (zelfde kaart als M28).',
26:'Reus Deavo, bevrijde ridder Thrice, spreuk Teleportatie, monnik in kraal; hoogste startkas (15.000).',
27:'Twee rivalen (Gruffton owner 1, Grymton owner 2); 25 kippen; geen items.',
28:'Alleen 12 mannen en 6 gebouwen; 8 spawners met types 16,8,7,19 (de gastheer van de Dark Lord); kaart = M25.',
29:'Doolhof, vuurvaste ring, doel (target), monniken, put van de Heilige Fontein; reus met kelk.',
30:'Laatste kaart: 28.390 landtegels (rots 70 %), vijanddorp Parpton (eigenaar 2) en 2 tempels; doolhof.'}
ZWAAR={
1:'Laag. Geen vijanden.',2:'Laag. 3 wolven.',3:'Middel. 7 wolven; groot rotsgebied.',4:'Middel. 4+3 wezens; grote bossen.',5:'Middel. 6 zombies, 30 muren.',
6:'Middel-hoog. 5 vijandelijke dorpelingen, 26 vallen.',7:'Middel. Geen vijandelijk dorp; 6 wezens, 14 vallen.',8:'Middel. 4 vijandelijke dorpelingen, kas 6.000.',9:'Hoog. 6 vijanden, 14 vallen, 60 muren.',
10:'Hoog. 281 muren, 11 wezens (6 reuzen) en geen water.',11:'Middel. 4 vijandelijke dorpelingen.',12:'Hoog. 16 vijandelijke soldaten + 5 spawners.',
13:'Middel. Dorp met 6 vijandelijke bewoners, veel water (42 %).',14:'Middel. Tijdgebonden (18.000 ticks).',15:'Hoog. 17 vijandelijke mensen, 36 vallen.',
16:'Hoog. Tijdlimiet; 7 vijanden + 3 spawners.',17:'Middel. Armoede (5.000) en een grote reus.',18:'Middel. Geen vee; 13 vijandelijke mensen; 3 spawners.',
19:'Hoog. Twee dorpen (10 vijandelijke mensen).',20:'Hoog. 14 vijandelijke mensen; rovers.',21:'Hoog. 19 vijandelijke gebouwen, 59 muren, 5 vijandelijke mensen.',
22:'Middel-hoog. 5 spawners, vampier, 71 muren.',23:'Middel. 6 vijandelijke mensen, grote kaart.',24:'Hoog. Startkas 0; 8 vijandelijke krijgers en 29 vallen.',
25:'Hoog. Tijdlimiet 4.320 ticks (1,5 seizoen), 19 verdedigers (eigenaar 4).',26:'Hoog. Reus Deavo, 168 muren.',27:'Hoog. Twee dorpen (18 vijandelijke mensen).',
28:'Zeer hoog. 8 spawners; je mag niets verliezen.',29:'Hoog. 48 vallen, reuzen.',30:'Zeer hoog. 33 vijandelijke mensen, 23 vijandelijke gebouwen, 209 muren, 25 vallen.'}
rows=[]
for k in range(1,31):
    r=json.load(open('m%02d.json'%k))
    kc=r['kind_counts'];land=r['land_total'];nv=sum(v for a,v in kc.items() if a!='void')
    pc=lambda *a: round(100*sum(kc.get(x,0) for x in a)/land)
    x0,y0,x1,y1=r['bbox_nonvoid']
    v0=collections.Counter(v['type'] for v in r['villagers'] if v['owner']==0)
    vs=', '.join('%d %s'%(n,TY.get(t,'t%d'%t)) for t,n in sorted(v0.items()))
    ho=r['home_island']['tiles']
    rows.append('| %d | %s | %dx%d | %s%s | gras %d, bos %d, rots %d, rest %d; water %d %% | %s; kas %s | %s | %s | %s |'%(
        k,NAME[k],x1-x0+1,y1-y0+1,format(land,',').replace(',','.'),(' (thuiseiland %s)'%format(ho,',').replace(',','.')) if ho and ho!=land else '',
        pc('grass'),pc('forest'),pc('rock','rockrim'),pc('dirt','sand','other'),round(100*kc.get('water',0)/nv),
        vs,format(r['players'][0]['cash'],',').replace(',','.'),DOEL[k],NIEUW[k],ZWAAR[k]))
open('tabel.md','w',encoding='utf-8').write('\n'.join(rows))
print(len('\n'.join(rows)))
