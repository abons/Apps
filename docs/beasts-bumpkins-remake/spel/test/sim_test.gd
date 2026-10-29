extends SceneTree
## Headless simtest: godot --headless --path . --script res://test/sim_test.gd
## Laadt kaart 1, geeft een loopbevel, tikt, controleert aankomst, spreiding, leeftijdscheck, pad rond rots, seizoen.

var fouten := 0


func _initialize() -> void:
	var w := Wereld.new()
	_check(w.laad(), "kaart laadt")
	if fouten > 0:
		quit(1)
		return
	_check(w.dorpelingen.size() == 6, "6 dorpelingen (zijn %d)" % w.dorpelingen.size())
	_check(w.kampvuur == Vector2i(102, 68), "kampvuur op (102,68)")
	var kinderen := 0
	for d in w.dorpelingen:
		if d.leeftijd == "kind":
			kinderen += 1
	_check(kinderen == 2, "2 kinderen (sex 13/14)")
	_check(w.raster.factor(102, 65) > w.raster.factor(100, 65), "pad is sneller dan gras")
	_check(not w.raster.loopbaar(102, 68), "kampvuur blokkeert zijn tegel")
	_check(not w.raster.loopbaar(100, 20), "buiten het eiland is niet loopbaar")

	# 1. loopbevel aan een volwassene
	var d := w.dorpeling(3)            # sex 1 = man
	_check(d.volwassen(), "dorpeling 3 is volwassen")
	var doel := Vector2i(d.tegel().x + 8, d.tegel().y - 5)
	_check(w.raster.loopbaar_v(doel), "doeltegel loopbaar")
	var n := w.geef_bevel([d.id], "loop", doel)
	_check(n == 1, "bevel geaccepteerd")
	var tikken := 0
	while not d.route.is_empty() and tikken < 5000:
		w.tik(w.tik_dt)
		tikken += 1
	_check(d.route.is_empty() and d.tegel() == doel, "aangekomen op %s (staat op %s, %d tikken = %.1f s)" % [doel, d.tegel(), tikken, tikken * w.tik_dt])
	var min_s: float = float(w.tegel_m) * Vector2(doel - Vector2i(d.tegel().x - 8, d.tegel().y + 5)).length() / (w.loop_mps * w.looptempo * 1.15)
	_check(tikken * w.tik_dt > min_s * 0.9 and tikken * w.tik_dt < min_s * 2.0, "loopt op looptempo: %.1f s (minimaal %.1f s)" % [tikken * w.tik_dt, min_s])

	# 2. snelheid: pad is sneller dan gras
	var a := Wereld.new()
	a.laad()
	var b := a.dorpeling(1)
	b.zet_tegel(Vector2i(101, 65))     # pad
	var c := a.dorpeling(2)
	c.zet_tegel(Vector2i(99, 62))      # gras
	var t0 := b.pos
	var t1 := c.pos
	b.route = [Vector2(102.5, 65.5), Vector2(103.5, 65.5)]
	b.bevel = {"soort": "loop"}
	c.route = [Vector2(100.5, 62.5), Vector2(101.5, 62.5)]
	c.bevel = {"soort": "loop"}
	for i in 10:
		a.tik(a.tik_dt)
	_check((b.pos - t0).length() > (c.pos - t1).length() * 1.05, "pad-loper is verder na 1 s dan gras-loper")

	# 3. uitwaaieren
	var ids := []
	for x in w.dorpelingen:
		ids.append(x.id)
	var ziel := Vector2i(106, 72)
	var gel := w.geef_bevel(ids, "loop", ziel)
	_check(gel == 6, "6 dorpelingen kregen loopbevel (%d)" % gel)
	var doelen := {}
	for x in w.dorpelingen:
		doelen[x.bevel.get("doel", Vector2i.ZERO)] = true
	_check(doelen.size() == 6, "6 verschillende doeltegels (%d)" % doelen.size())
	tikken = 0
	var stand := {}
	while tikken < 6000 and stand.size() < 6:
		w.tik(w.tik_dt)
		tikken += 1
		for x in w.dorpelingen:
			if x.bevel.is_empty() and not stand.has(x.id):
				stand[x.id] = x.tegel()
	var allemaal := stand.size() == 6
	for id in stand:
		if Vector2(stand[id]).distance_to(Vector2(ziel)) > 3.0:
			allemaal = false
	_check(allemaal, "groep staat rond het doel na %d tikken" % tikken)

	# 4. leeftijdscheck
	var kind: Dorpeling = null
	for x in w.dorpelingen:
		if x.leeftijd == "kind":
			kind = x
	_check(w.geef_bevel([kind.id], "vecht", ziel) == 0, "kind krijgt geen vechtbevel")
	_check(w.geef_bevel([kind.id], "werk", ziel) == 0, "kind krijgt geen werkbevel")
	_check(w.geef_bevel([kind.id], "loop", ziel) == 1, "kind mag wel lopen")
	_check(w.geef_bevel([d.id], "vecht", ziel) == 1, "volwassene mag wel vechten")

	# 5. pad rond rots: een paar tegels waarvan de rechte lijn door rots/water/boom gaat maar een route bestaat
	var gevonden := false
	var naar := Vector2i(100, 66)
	_check(w.raster.loopbaar_v(naar) and w.bereik[w.raster.idx(naar.x, naar.y)] == 1, "routedoel %s is loopbaar en bereikbaar" % naar)
	for y in range(40, 60):
		for x in range(82, 96):
			var van := Vector2i(x, y)
			if not w.raster.loopbaar_v(van) or w.bereik[w.raster.idx(x, y)] == 0:
				continue
			if Vector2(van).distance_to(Vector2(naar)) < 12:
				continue
			var geraakt := false
			for s in 41:
				var p := Vector2(van).lerp(Vector2(naar), s / 40.0)
				if not w.raster.loopbaar(int(p.x), int(p.y)):
					geraakt = true
			if geraakt:
				var r := Router.route(w.raster, van, naar)
				if not r.is_empty():
					var ok := r[-1] == naar
					for t in r:
						if not w.raster.loopbaar_v(t):
							ok = false
					_check(ok, "route %s -> %s om obstakels heen: %d stappen, alle loopbaar" % [van, naar, r.size()])
					gevonden = true
					break
		if gevonden:
			break
	_check(gevonden, "een obstakel-omweg gevonden")

	# 6. onbereikbaar
	_check(Router.route(w.raster, Vector2i(102, 66), Vector2i(135, 60)).is_empty(), "buitenring is onbereikbaar (leeg)")

	# 7. seizoenen en klok
	var s := Wereld.new()
	s.laad()
	var gezien := {}
	for i in int(4 * s.seizoen_duur() / s.tik_dt):
		s.tik(s.tik_dt)
		gezien[s.seizoen_naam()] = true
	_check(gezien.size() == 4, "alle 4 seizoenen doorlopen: %s" % [gezien.keys()])
	s.tijd_s = 3.5 * s.seizoen_duur()
	_check(s.sneeuw() > 0.9, "midden in de winter is er sneeuw")

	# 8. vooruit(): vaste tik, pauze
	var v := Wereld.new()
	v.laad()
	v.vooruit(1.0)
	_check(v.tik_nr == 10, "1 s = 10 tikken (%d)" % v.tik_nr)
	v.gepauzeerd = true
	v.vooruit(1.0)
	_check(v.tik_nr == 10, "pauze houdt de sim stil")
	v.gepauzeerd = false
	v.tempo = 4.0
	v.vooruit(1.0)
	_check(v.tik_nr == 50, "4x = 40 tikken erbij (%d)" % v.tik_nr)

	# bouwplan: hut op gras naast het kampvuur kan, op het kampvuur of dubbel niet
	var vrij := Vector2i(-1, -1)          # eerste plek bij het kampvuur waar een hut kan (niet op het pad)
	for r in 8:
		for dy in range(-r, r + 1):
			for dx in range(-r, r + 1):
				if vrij.x < 0 and w.kan_bouwen(Plan.new(&"hut", Vector2i(98 + dx, 62 + dy), 0, 4, 4)):
					vrij = Vector2i(98 + dx, 62 + dy)
	_check(vrij.x >= 0, "testplek %s is vrij" % vrij)
	var bp := w.maak_plan(&"hut", vrij, 0)
	_check(bp != null and w.plan_zet(bp), "hut kan op een vrije plek")
	_check(w.maak_plan(&"hut", vrij + Vector2i(1, 1), 0) == null, "tweede hut er half overheen kan niet")
	_check(w.maak_plan(&"hut", w.kampvuur, 0) == null, "hut op het kampvuur kan niet")
	var padtegel := Vector2i(-1, -1)
	for y in range(50, 80):
		for x in range(90, 115):
			if padtegel.x < 0 and w.raster.soort_naam(x, y) == "pad":
				padtegel = Vector2i(x, y)
	_check(padtegel.x >= 0 and w.maak_plan(&"kippenhok", padtegel, 0) == null, "niet op een pad bouwen (%s)" % padtegel)
	_check(w.maak_plan(&"kerk", vrij + Vector2i(5, 0), 0) == null, "onbekende soort geeft null")
	var lm: Vector2i = Wereld.BOUWSOORTEN[&"gereedschapsloods"]
	_check(Plan.new(&"gereedschapsloods", Vector2i.ZERO, 1, lm.x, lm.y).afdruk().size == Vector2i(2, 5), "loods kwartslag gedraaid is 2x5")

	# bouwen: een volwassene loopt naar het plan, werkt tot het klaar is, de plek wordt blokkerend
	var bouwer: Dorpeling = null
	var jong: Dorpeling = null
	for dl in w.dorpelingen:
		if dl.volwassen():
			bouwer = dl
		else:
			jong = dl
	_check(bouwer != null and w.geef_bouwbevel([bouwer.id], bp) == 1, "volwassene krijgt bouwbevel")
	_check(jong != null and w.geef_bouwbevel([jong.id], bp) == 0, "kind kan niet bouwen")
	var bouwtikken := 0
	while not bp.klaar and bouwtikken < 1500:
		w.tik(w.tik_dt)
		bouwtikken += 1
	_check(bp.klaar, "hut klaar na %d bouwtikken (%.0f s)" % [bouwtikken, bouwtikken * w.tik_dt])
	_check(not w.raster.loopbaar(vrij.x, vrij.y), "afgebouwde hut blokkeert zijn tegels")
	_check(bouwer.werk_plan == null and not bouwer.bouwt, "bouwer is vrij na afloop")
	var in_hut := 0
	for dl in w.dorpelingen:
		if bp.afdruk().has_point(dl.tegel()):
			in_hut += 1
	_check(in_hut == 0, "niemand staat in de afgebouwde hut (%d)" % in_hut)

	# kas: de hut is betaald; te duur kan niet
	var wegtegels := int(w.spel["start_kas"]) - w.prijs(&"hut") - w.kas
	_check(wegtegels >= 0 and wegtegels % int(w.spel["weg_per_tegel"]) == 0, "hut kostte %d, plus %d voor de weg naar de deur (kas %d)" % [w.prijs(&"hut"), wegtegels, w.kas])
	var dt2 := bp.deur_tegel()
	_check(w.raster.soort_naam(dt2.x, dt2.y) == "pad" or not w.raster.loopbaar(dt2.x, dt2.y), "voor de hutdeur ligt pad")
	var arm := Wereld.new()
	arm.laad()
	arm.kas = 10
	var ap := arm.maak_plan(&"hut", vrij, 0)
	_check(ap != null and not arm.plan_zet(ap) and arm.kas == 10, "plan te duur: niet gezet, kas blijft 10")

	# koeien: generator, claimen, loslaten, missie 1 winnen
	var k := Wereld.new()
	k.laad()
	_check(k.vee.size() == 1 and k.vee[0].eigenaar == -1, "generator begint met 1 wilde koe")
	for i in int(200.0 / k.tik_dt):
		k.tik(k.tik_dt)
	_check(k.vee.size() == 3, "na 200 s 3 wilde koeien, het maximum (%d)" % k.vee.size())
	var boer: Dorpeling = null
	var kleuter: Dorpeling = null
	for dl in k.dorpelingen:
		if dl.volwassen():
			boer = dl
		else:
			kleuter = dl
	var koe1: Vee = k.vee[0]
	_check(k.geef_claimbevel([kleuter.id], koe1.id) == 0, "kind claimt geen koe")
	_check(k.geef_claimbevel([boer.id], koe1.id) == 1 and koe1.vast, "volwassene loopt naar de koe, die blijft staan")
	var claimtikken := 0
	while koe1.eigenaar != 0 and claimtikken < 3000:
		k.tik(k.tik_dt)
		claimtikken += 1
	_check(koe1.eigenaar == 0 and not koe1.vast and koe1.anker == k.kampvuur, "koe geclaimd na %.0f s, zwerft naar het kampvuur" % (claimtikken * k.tik_dt))
	_check(k.eigen_koeien() == 1 and k.uitslag == "", "1 eigen koe, missie nog bezig")
	k.geef_claimbevel([boer.id], koe1.id)
	for i in 3000:
		if koe1.eigenaar != 0:
			break
		k.tik(k.tik_dt)
	_check(koe1.eigenaar == -1, "nog eens claimen laat haar los")
	for kk in k.vee:
		kk.eigenaar = 0
	while k.vee.size() < 4:
		k.tik(k.tik_dt)
	k.vee[3].eigenaar = 0
	k.tik(k.tik_dt)
	_check(k.uitslag == "gewonnen", "6 dorpelingen en 4 eigen koeien: gewonnen (%s)" % k.uitslag)
	var v2 := Wereld.new()
	v2.laad()
	v2.dorpelingen.resize(1)
	v2.tik(v2.tik_dt)
	_check(v2.uitslag == "verloren", "1 dorpeling: verloren")

	# gezin: alleen met een vrij bed; stel naar de hut, 12 s binnen, baby 5 s op de arm, kind 150 s
	var gz := Wereld.new()
	gz.laad()
	var hutten := 0
	for y in range(40, 92, 5):
		for x in range(84, 126, 5):
			if hutten >= 3:
				break
			var hp := gz.maak_plan(&"hut", Vector2i(x, y), 0)
			if hp != null and gz.bereik[gz.raster.idx(hp.deur_tegel().x, hp.deur_tegel().y)] == 1 and gz.plan_zet(hp):
				gz._rond_af(hp)
				hutten += 1
	_check(hutten == 3 and gz.bedden() == 6, "3 hutten = 6 bedden (%d)" % gz.bedden())
	for i in 50:
		gz.tik(gz.tik_dt)
	_check(gz.wiegen.is_empty(), "6 mensen in 6 bedden: geen gezin")
	var vierde: Plan = null
	for y in range(40, 92, 5):
		for x in range(84, 126, 5):
			if vierde == null:
				var hp := gz.maak_plan(&"hut", Vector2i(x, y), 1)
				if hp != null and gz.bereik[gz.raster.idx(hp.deur_tegel().x, hp.deur_tegel().y)] == 1 and gz.plan_zet(hp):
					gz._rond_af(hp)
					vierde = hp
	var wtikken := 0
	while gz.wiegen.is_empty() and wtikken < 600:
		gz.tik(gz.tik_dt)
		wtikken += 1
	_check(gz.wiegen.size() == 1 and gz.ruimte() == 1, "vierde hut: een stel gaat na %.1f s naar binnen, het tweede wacht (ruimte %d)" % [wtikken * gz.tik_dt, gz.ruimte()])
	var gtikken := 0
	while gz.dorpelingen.size() == 6 and gtikken < 6000:
		gz.tik(gz.tik_dt)
		gtikken += 1
	_check(gz.dorpelingen.size() == 7, "kind geboren na %.0f s" % (gtikken * gz.tik_dt))
	var nieuw: Dorpeling = gz.dorpelingen[6]
	_check(nieuw.leeftijd == "kind" and gz.raster.loopbaar_v(nieuw.tegel()), "nieuwe dorpeling is een kind op een loopbare tegel")
	_check(gz.ruimte() + gz.wiegen.size() == 1, "na de geboorte: 1 bed over of al door het tweede stel genomen")
	for i in int(151.0 / gz.tik_dt):
		gz.tik(gz.tik_dt)
	_check(nieuw.leeftijd == "volwassen", "kind is na 150 s volwassen")
	var ouders := 0
	for dl in gz.dorpelingen:
		if dl.rust > 0.0 or not dl.wieg.is_empty():
			ouders += 1
	_check(ouders >= 1, "ouders en nieuwe volwassene rusten of zitten in een nieuw gezin (%d)" % ouders)
	# een bevel van de speler breekt een gezin af (eerst een vijfde hut, anders is er geen bed meer)
	for y in range(40, 92, 5):
		for x in range(84, 126, 5):
			var hp := gz.maak_plan(&"hut", Vector2i(x, y), 2)
			if hp != null and gz.bereik[gz.raster.idx(hp.deur_tegel().x, hp.deur_tegel().y)] == 1 and gz.plan_zet(hp):
				gz._rond_af(hp)
				break
		if gz.ruimte() > 0:
			break
	var lopend: Dictionary = {}
	for i in 3000:
		if not gz.wiegen.is_empty():
			lopend = gz.wiegen[0]
			break
		gz.tik(gz.tik_dt)
	if not lopend.is_empty():
		var vd: Dorpeling = lopend["vader"]
		gz.geef_bevel([vd.id], "loop", gz.kampvuur + Vector2i(2, 2))
		_check(gz.wiegen.is_empty() and vd.wieg.is_empty() and not vd.binnen, "loopbevel breekt het gezin af")
	else:
		_check(false, "tweede gezin gevonden om af te breken")

	# graan en brood: molen (start 8 brood), akker rijpt in 60 s, oogsten -> naar de molen, trek -> kopen = kas +3
	var ec := Wereld.new()
	ec.laad()
	ec.alles_open = true
	var molen: Plan = null
	var akker: Plan = null
	for y in range(44, 90, 3):
		for x in range(86, 124, 3):
			if molen == null:
				var mp := ec.maak_plan(&"molen", Vector2i(x, y), 0)
				if mp != null and ec.bereik[ec.raster.idx(mp.deur_tegel().x, mp.deur_tegel().y)] == 1 and ec.plan_zet(mp):
					ec._rond_af(mp)
					molen = mp
			elif akker == null:
				var ap2 := ec.maak_plan(&"akker", Vector2i(x, y), 0)
				if ap2 != null and ec.bereik[ec.raster.idx(x, y)] == 1 and ec.plan_zet(ap2):
					ec._rond_af(ap2)
					akker = ap2
	_check(molen != null and molen.voorraad == 8, "molen staat met 8 brood")
	_check(akker != null and ec.akkers.size() == 4 and ec.raster.loopbaar(akker.tegel.x, akker.tegel.y), "akker: 4 tegels, loopbaar")
	var md := molen.deur_tegel()
	_check(not molen.afdruk().has_point(md) and molen.afdruk().grow(1).has_point(md), "molendeur (%s) grenst aan de voetafdruk" % md)
	var kas0 := ec.kas
	for i in int(70.0 / ec.tik_dt):
		ec.tik(ec.tik_dt)
	_check(ec.kas > kas0, "na 70 s is er brood gekocht: kas %d -> %d" % [kas0, ec.kas])
	var geleverd := false
	var vr := molen.voorraad
	for i in int(120.0 / ec.tik_dt):
		ec.tik(ec.tik_dt)
		if molen.voorraad > vr:
			geleverd = true
		vr = molen.voorraad
	_check(geleverd, "graan geoogst en naar de molen gebracht")
	_check(ec.akkers.size() == 4, "akker blijft 4 tegels na het oogsten")

	# melk: melkerij, de (wilde) koe dicht bij het dorp wordt gemolken, de melk gaat naar de melkerij, 90 s leeg
	var mw := Wereld.new()
	mw.laad()
	mw.alles_open = true
	var mkr: Plan = null
	for y in range(44, 90, 3):
		for x in range(86, 124, 3):
			if mkr == null:
				var mp := mw.maak_plan(&"melkerij", Vector2i(x, y), 0)
				if mp != null and mw.bereik[mw.raster.idx(mp.deur_tegel().x, mp.deur_tegel().y)] == 1 and mw.plan_zet(mp):
					mw._rond_af(mp)
					mkr = mp
	_check(mkr != null and mkr.voorraad == 8, "melkerij staat met 8 melk")
	var mkoe: Vee = mw.vee[0]
	_check(not mw.melkbaar(mkoe), "koe bij de generator (ver van het dorp) wordt niet gemolken")
	mkoe.zet_tegel(mw.dichtstbij_loopbaar(mw.kampvuur + Vector2i(4, -4)))
	mkoe.anker = mkoe.tegel()
	_check(mw.melkbaar(mkoe), "koe bij het dorp is melkbaar")
	var mv := mkr.voorraad
	var gemolken := false
	var gebracht := false
	for i in int(60.0 / mw.tik_dt):
		mw.tik(mw.tik_dt)
		if mkoe.leeg > 0.0:
			gemolken = true
		if mkr.voorraad > mv:
			gebracht = true
		mv = mkr.voorraad
	_check(gemolken and mkoe.leeg > 0.0, "koe gemolken, nog %.0f s leeg" % mkoe.leeg)
	_check(gebracht, "melk naar de melkerij gebracht")

	# eieren: kippenhok krijgt 3 kippen, een kip legt en blijft zitten, een volwassene raapt, het ei gaat het hok in
	var kw := Wereld.new()
	kw.laad()
	var hok: Plan = null
	for y in range(44, 90, 3):
		for x in range(86, 124, 3):
			if hok == null:
				var hp := kw.maak_plan(&"kippenhok", Vector2i(x, y), 0)
				if hp != null and kw.bereik[kw.raster.idx(hp.deur_tegel().x, hp.deur_tegel().y)] == 1 and kw.plan_zet(hp):
					kw._rond_af(hp)
					hok = hp
	_check(hok != null and kw.kippen.size() == 3 and hok.voorraad == 8, "kippenhok: 3 kippen, 8 eieren")
	var ev := hok.voorraad
	var gelegd := false
	var geraapt := false
	for i in int(120.0 / kw.tik_dt):
		kw.tik(kw.tik_dt)
		for kp in kw.kippen:
			if kp.ei:
				gelegd = true
		if hok.voorraad > ev:
			geraapt = true
		ev = hok.voorraad
	_check(gelegd, "een kip heeft een ei gelegd")
	_check(geraapt, "ei geraapt en naar het kippenhok gebracht")
	var ver := 0
	for kp in kw.kippen:
		ver = maxi(ver, int(Vector2(kp.tegel()).distance_to(Vector2(kp.anker))))
	_check(ver <= Kip.ZWERF_STRAAL + 1, "kippen blijven bij het hok (max %d tegels)" % ver)

	# bouwersgilde: een man wordt bij de loods bouwer (kost 30), bouwt 2x zo snel en vecht niet
	var bw := Wereld.new()
	bw.laad()
	var ld: Plan = null
	for y in range(44, 90, 3):
		for x in range(86, 124, 3):
			if ld == null:
				var lp2 := bw.maak_plan(&"gereedschapsloods", Vector2i(x, y), 0)
				if lp2 != null and bw.bereik[bw.raster.idx(lp2.deur_tegel().x, lp2.deur_tegel().y)] == 1 and bw.plan_zet(lp2):
					bw._rond_af(lp2)
					ld = lp2
	var man: Dorpeling = null
	var vrouw: Dorpeling = null
	for dl in bw.dorpelingen:
		if dl.volwassen() and dl.geslacht == "man" and man == null:
			man = dl
		elif dl.volwassen() and dl.geslacht == "vrouw" and vrouw == null:
			vrouw = dl
	_check(bw.geef_gildebevel([vrouw.id], ld) == 0, "een vrouw wordt geen bouwer")
	var bkas := bw.kas
	_check(bw.geef_gildebevel([man.id], ld) == 1, "man loopt naar de loods")
	for i in 3000:
		if man.rol == "bouwer":
			break
		bw.tik(bw.tik_dt)
	_check(man.rol == "bouwer" and bw.kas == bkas - 30, "man is bouwer, kas -30 (%d)" % (bkas - bw.kas))
	_check(not man.kan_bevel("vecht") and man.kan_bevel("werk"), "bouwer vecht niet, werkt wel")
	var bh: Plan = null
	for y in range(44, 90, 3):
		for x in range(86, 124, 3):
			if bh == null:
				var hp2 := bw.maak_plan(&"hut", Vector2i(x, y), 0)
				if hp2 != null and bw.plan_zet(hp2):
					bh = hp2
	man.zet_tegel(bh.deur_tegel())
	man.route.clear()
	man.bevel = {}
	man.werk_plan = bh
	for i in int(10.0 / bw.tik_dt):
		bw.tik(bw.tik_dt)
	_check(absf(bh.voortgang - 20.0 / 60.0) < 0.02, "bouwer: 10 s werk = 20 werker-seconden (%.2f)" % (bh.voortgang * 60.0))

	# bouwmenu-volgorde: hut/kippenhok/loods -> (loods) molen + akker -> (molen) melkerij + hek + poort
	var om := Wereld.new()
	om.laad()
	_check(om.ontgrendeld(&"hut") and om.ontgrendeld(&"kippenhok") and om.ontgrendeld(&"gereedschapsloods"), "start: hut, kippenhok, loods")
	_check(not om.ontgrendeld(&"molen") and not om.ontgrendeld(&"akker") and not om.ontgrendeld(&"melkerij"), "start: geen molen, akker, melkerij")
	var _plek := func(soort: StringName) -> Plan:
		for y in range(44, 90, 2):
			for x in range(86, 124, 2):
				var q := om.maak_plan(soort, Vector2i(x, y), 0)
				if q != null and om.plan_zet(q):
					return q
		return null
	_check(_plek.call(&"molen") == null, "molen plaatsen kan nog niet")
	var lo: Plan = _plek.call(&"gereedschapsloods")
	_check(not om.ontgrendeld(&"molen"), "loods als plan opent nog niets")
	om._rond_af(lo)
	_check(om.ontgrendeld(&"molen") and om.ontgrendeld(&"akker") and not om.ontgrendeld(&"melkerij"), "loods af: molen en akker erbij")
	var mo: Plan = _plek.call(&"molen")
	om._rond_af(mo)
	_check(om.ontgrendeld(&"melkerij") and om.ontgrendeld(&"hek") and om.ontgrendeld(&"poort"), "molen af: melkerij, hek, poort erbij")
	# poort: dicht blokkeert, klik = open = loopbaar
	var pt: Plan = _plek.call(&"poort")
	om._rond_af(pt)
	_check(om.poort_dicht(pt.tegel) and om.raster.loopbaar(pt.tegel.x, pt.tegel.y), "poort dicht: dicht voor koeien, dorpelingen lopen erdoor")
	om.wissel_poort(pt)
	_check(pt.open and not om.poort_dicht(pt.tegel), "poort open")
	om.wissel_poort(pt)
	_check(not pt.open and om.poort_dicht(pt.tegel), "poort weer dicht")
	var hk: Plan = _plek.call(&"hek")
	_check(hk != null and hk.bouwtijd_s == 3.0 and om.prijs(&"hek") == 2, "hek: 2 kas, 3 s werk")

	# regressie 2026-10-29: na een afgebouwd kippenhok bleven de bouwers in de muren staan (doorbouwen naar het tweede
	# plan sloeg het eruit zetten over); nu staan ze buiten en wordt het tweede hok ook gebouwd
	var vw := Wereld.new()
	vw.laad()
	var hokken: Array[Plan] = []
	for r in 10:
		for dy in range(-r, r + 1):
			for dx in range(-r, r + 1):
				if hokken.size() < 2:
					var q := vw.maak_plan(&"kippenhok", Vector2i(104 + dx, 64 + dy), 0)
					if q != null and vw.plan_zet(q):
						hokken.append(q)
	var vids := []
	for dl in vw.dorpelingen:
		if dl.volwassen():
			vids.append(dl.id)
	vw.geef_bouwbevel(vids, hokken[0])
	for i in int(120.0 / vw.tik_dt):
		vw.tik(vw.tik_dt)
	var in_muur := 0
	for dl in vw.dorpelingen:
		if not dl.binnen and not vw.raster.loopbaar_v(dl.tegel()):
			in_muur += 1
	_check(in_muur == 0, "na het kippenhok staat niemand in een muur (%d)" % in_muur)
	_check(hokken[0].klaar and hokken[1].klaar, "bouwers lopen door naar het tweede kippenhok")

	# zelfstandig: een geplaatst plan wordt zonder bevel gebouwd; 's nachts 2 in de hut en de rest bij het kampvuur,
	# 's ochtends weer op; zonder opdracht blijft iedereen bij het dorp
	var zw := Wereld.new()
	zw.laad()
	var zh: Plan = null
	for r in 10:
		for dy in range(-r, r + 1):
			for dx in range(-r, r + 1):
				if zh == null:
					var q := zw.maak_plan(&"hut", Vector2i(98 + dx, 60 + dy), 0)
					if q != null and zw.plan_zet(q):
						zh = q
	var zmax := 0.0
	var in_bed := 0
	var bij_vuur := 0
	for i in int(540.0 / zw.tik_dt):
		zw.tik(zw.tik_dt)

		if i % 50 == 0 and zw.is_nacht():
			var b1 := 0
			var v1 := 0
			for dl in zw.dorpelingen:
				if dl.slaapt and dl.binnen:
					b1 += 1
				if dl.slaapt and dl.bij_vuur:
					v1 += 1
			in_bed = maxi(in_bed, b1)
			bij_vuur = maxi(bij_vuur, v1)
	_check(zh != null and zh.klaar, "hut zonder bouwbevel gebouwd")
	_check(in_bed == 2 and bij_vuur == 4, "nacht: %d in het bed van de hut, %d bij het kampvuur" % [in_bed, bij_vuur])
	var op := 0
	for dl in zw.dorpelingen:
		if not dl.slaapt and not dl.binnen:
			op += 1
	_check(not zw.is_nacht() and op == 6, "ochtend: iedereen weer op (%d)" % op)
	for i in int(60.0 / zw.tik_dt):      # een minuut zonder klussen: terug naar het dorp
		zw.tik(zw.tik_dt)
	for dl in zw.dorpelingen:
		zmax = maxf(zmax, Vector2(dl.tegel()).distance_to(Vector2(zw.kampvuur)))
	_check(zmax <= 7.0, "zonder opdracht blijft iedereen bij het dorp: max %.1f tegels van het kampvuur" % zmax)

	# weide: hek rondom met een poort; een eigen koe komt er alleen in als de poort open is, en blijft erin als hij dicht is
	var ww := Wereld.new()
	ww.laad()
	ww.alles_open = true
	var wo := Vector2i(-1, -1)
	for y in range(50, 80):
		for x in range(100, 118):
			if wo.x >= 0:
				continue
			var vrij2 := true
			for dx in range(6):
				for dy in range(5):
					var t := Vector2i(x + dx, y + dy)
					if not ww.raster.loopbaar_v(t) or ww.raster.soort_naam(t.x, t.y) == "pad" or ww.bereik[ww.raster.idx(t.x, t.y)] == 0:
						vrij2 = false
			if vrij2:
				wo = Vector2i(x, y)
	var wpoort: Plan = null
	for dx in range(6):
		for dy in range(5):
			if dx != 0 and dx != 5 and dy != 0 and dy != 4:
				continue
			var srt := &"poort" if (dx == 2 and dy == 4) else &"hek"
			var hp := Plan.new(srt, wo + Vector2i(dx, dy), 0, 1, 1)
			if ww.plan_zet(hp):
				ww._rond_af(hp)
				if srt == &"poort":
					wpoort = hp
	_check(wo.x >= 0 and ww.weides.size() == 1 and ww.weides[0].size() == 12, "weide van 4x3 binnen het hek gevonden (%d)" % (ww.weides[0].size() if not ww.weides.is_empty() else -1))
	var wkoe: Vee = ww.vee[0]
	wkoe.zet_tegel(ww.dichtstbij_loopbaar(wo + Vector2i(2, 7)))
	wkoe.eigenaar = 0
	ww._wijs_weides_toe()
	_check(not wkoe.weide.is_empty(), "eigen koe hoort in de weide")
	for i in int(40.0 / ww.tik_dt):
		ww.tik(ww.tik_dt)
	_check(not wkoe.weide.has(wkoe.tegel()), "poort dicht: koe komt er niet in")
	ww.wissel_poort(wpoort)
	var erin := false
	for i in int(120.0 / ww.tik_dt):
		ww.tik(ww.tik_dt)
		if wkoe.weide.has(wkoe.tegel()):
			erin = true
			break
	_check(erin, "poort open: koe loopt de weide in")
	ww.wissel_poort(wpoort)
	var bleef := true
	for i in int(120.0 / ww.tik_dt):
		ww.tik(ww.tik_dt)
		if not wkoe.weide.has(wkoe.tegel()) and wkoe.tegel() != wpoort.tegel:
			bleef = false
	_check(bleef, "poort dicht: koe blijft in de weide")

	print("---- ", "ALLES OK" if fouten == 0 else "%d FOUT(EN)" % fouten)
	quit(0 if fouten == 0 else 1)


func _check(ok: bool, tekst: String) -> void:
	print(("ok    " if ok else "FOUT  "), tekst)
	if not ok:
		fouten += 1
