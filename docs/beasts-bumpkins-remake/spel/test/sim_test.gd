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
	var wegtegels := int(w.missie["start_kas"]) - w.prijs(&"hut") - w.kas
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
	k.spel = k.spel.duplicate(true)           # zonder kalveren: deze test telt koeien uit de generator
	k.spel["economie"]["kalf_kans"] = 0.0
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
	var groei := float(gz.spel["gezin"]["opgroeien_s"])
	for i in int((groei + 1.0) / gz.tik_dt):
		gz.tik(gz.tik_dt)
	_check(nieuw.leeftijd == "volwassen", "kind is na %.0f s volwassen (gezin.opgroeien_s)" % groei)
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
	var bprijs := int(bw.spel["bouwer"]["prijs"])
	_check(man.rol == "bouwer" and bw.kas == bkas - bprijs, "man is bouwer, kas -%d (%d)" % [bprijs, bkas - bw.kas])
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
	_check(hk != null and hk.bouwtijd_s == 3.0 and om.prijs(&"hek") == 80, "hek: 80 kas (origineel), 3 s werk")

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

	_test_wegen()
	_test_kalveren()
	_test_stapels()
	_test_bron()

	print("---- ", "ALLES OK" if fouten == 0 else "%d FOUT(EN)" % fouten)
	quit(0 if fouten == 0 else 1)


## Weg als bouwsoort (bouwmenu 2026-10-30): slepen = rij (BouwRij, hoekig, om gebouwen heen), 2 kas en 3 s per tegel,
## dorpelingen bouwen hem zelf en bouwen door, af = padtegel en het plan verdwijnt; niet op een gebouw, geen plan erop.
func _test_wegen() -> void:
	var wg := Wereld.new()
	wg.laad()
	_check(wg.ontgrendeld(&"weg"), "weg: vanaf de start in het bouwmenu")
	var veranderd := [0]
	wg.wegen_veranderd.connect(func() -> void: veranderd[0] += 1)
	# een vrij stuk van 12x9 tegels dicht bij het kampvuur, bereikbaar
	var o := Vector2i(-1, -1)
	for r in range(2, 20):
		for dy in range(-r, r + 1):
			for dx in range(-r, r + 1):
				if o.x >= 0 or maxi(absi(dx), absi(dy)) != r:
					continue
				var c := wg.kampvuur + Vector2i(dx, dy)
				var vrij := true
				for x in 12:
					for y in 9:
						var t := c + Vector2i(x, y)
						if BouwRij.status(wg, &"weg", t) != BouwRij.KAN or wg.bereik[wg.raster.idx(t.x, t.y)] == 0:
							vrij = false
				if vrij:
					o = c
	_check(o.x >= 0, "weg: vrij stuk van 12x9 gevonden (%s)" % o)
	if o.x < 0:
		return
	var hut := wg.maak_plan(&"hut", o + Vector2i(4, 2), 0)
	_check(hut != null and wg.plan_zet(hut), "weg: hut als obstakel geplaatst")
	_check(BouwRij.status(wg, &"weg", o + Vector2i(5, 3)) == BouwRij.KAN_NIET and wg.maak_plan(&"weg", o + Vector2i(5, 3), 0) == null,
		"weg: niet onder een gebouw")
	var om := BouwRij.route(wg, &"weg", o + Vector2i(0, 4), o + Vector2i(11, 4))
	var langs := om.size() > 0 and om[0] == o + Vector2i(0, 4) and om[-1] == o + Vector2i(11, 4)
	for i in om.size():
		if hut.afdruk().has_point(om[i]) or (i > 0 and absi(om[i].x - om[i - 1].x) + absi(om[i].y - om[i - 1].y) != 1):
			langs = false
	_check(langs, "weg: rij loopt recht-aansluitend om de hut heen (%d tegels)" % om.size())
	var a := o
	var b := o + Vector2i(3, 7)
	var rij := BouwRij.route(wg, &"weg", a, b)
	var bochten := 0
	for i in range(2, rij.size()):
		if (rij[i] - rij[i - 1]) != (rij[i - 1] - rij[i - 2]):
			bochten += 1
	_check(rij.size() == 11 and bochten == 1, "weg: op open grond een L met een bocht (%d tegels, %d bochten)" % [rij.size(), bochten])
	var kas0 := wg.kas
	var n := BouwRij.zet(wg, &"weg", rij)
	_check(n == 11 and wg.kas == kas0 - 11 * wg.prijs(&"weg"), "weg: 11 plannen voor %d kas per tegel (kas %d -> %d)" % [wg.prijs(&"weg"), kas0, wg.kas])
	var wp := wg.plan_op(a)
	_check(wp != null and wp.soort == &"weg" and wp.bouwtijd_s == 3.0 and wg.raster.soort_naam(a.x, a.y) != "pad",
		"weg: plan van 3 s, nog geen pad")
	_check(wg.maak_plan(&"kippenhok", b - Vector2i(1, 1), 0) == null, "weg: geen plan op een geplande weg")
	_check(BouwRij.status(wg, &"weg", b) == BouwRij.BESTAAT and BouwRij.zet(wg, &"weg", [b]) == 0, "weg: een geplande tegel nog eens = overgeslagen")
	var open := 11
	for i in int(240.0 / wg.tik_dt):
		wg.tik(wg.tik_dt)
		open = 0
		for q in wg.plannen:
			if q.soort == &"weg":
				open += 1
		if open == 0:
			break
	var alles_pad := true
	for t in rij:
		if wg.raster.soort_naam(t.x, t.y) != "pad":
			alles_pad = false
	_check(open == 0 and alles_pad, "weg: dorpelingen bouwen de hele rij zelf, alle tegels pad (%d open)" % open)
	_check(veranderd[0] >= 11, "weg: wegen_veranderd per afgebouwde tegel (%d)" % veranderd[0])
	_check(wg.maak_plan(&"kippenhok", a, 0) == null and BouwRij.status(wg, &"weg", a) == BouwRij.BESTAAT, "weg: niet bouwen op de nieuwe weg")


func _check(ok: bool, tekst: String) -> void:
	print(("ok    " if ok else "FOUT  "), tekst)
	if not ok:
		fouten += 1

## Kalven (hint 1-11, origineel klasse 96 `baby cow`): twee eigen koeien bij elkaar krijgen in de lente elk een kalf
## (kans 1 in de test), een keer per lente; een kalf telt niet mee als koe, wordt niet gemolken en is na kalf_groei_s een
## koe die wel meetelt. Een koe alleen of in de zomer kalft niet.
func _test_kalveren() -> void:
	var w := Wereld.new()
	w.laad()
	w.spel["economie"]["kalf_kans"] = 1.0
	w.tijd_s = 10.0
	var koeien: Array[Vee] = []
	for i in 3:
		var k := w._spawn_koe()
		k.van_generator = false
		koeien.append(k)
	for i in 2:
		koeien[i].eigenaar = 0
		koeien[i].anker = w.kampvuur
		koeien[i].zet_tegel(w.dichtstbij_loopbaar(w.kampvuur + Vector2i(2 + i, 2)))
	koeien[2].eigenaar = 0                       # derde eigen koe ver weg, alleen
	koeien[2].vast = true
	koeien[2].zet_tegel(w.dichtstbij_loopbaar(w.kampvuur + Vector2i(14, 0)))
	koeien[0].vast = true
	koeien[1].vast = true
	_check(w.seizoen() == 0 and w.eigen_koeien() == 3 and w.kalveren() == 0, "lente, 3 eigen koeien, geen kalf")
	for i in int(30.0 / w.tik_dt):
		w.tik(w.tik_dt)
	_check(w.kalveren() == 2, "twee koeien bij elkaar: twee kalveren (%d)" % w.kalveren())
	_check(w.eigen_koeien() == 3, "kalf telt niet mee als koe (%d)" % w.eigen_koeien())
	var kalf: Vee = w.vee[w.vee.size() - 1]
	_check(kalf.is_kalf() and kalf.eigenaar == 0 and kalf.moeder != null and kalf.moeder != koeien[2], "kalf is eigen en hoort bij een moeder")
	kalf.leeg = 0.0
	_check(not w.melkbaar(kalf), "kalf wordt niet gemolken")
	for i in int(60.0 / w.tik_dt):
		w.tik(w.tik_dt)
	_check(w.kalveren() == 2, "een kalf per koe per lente")
	_check(kalf.moeder == null or Vector2(kalf.tegel()).distance_to(Vector2(kalf.moeder.tegel())) <= 3.0, "kalf blijft bij de moeder")
	for i in int(240.0 / w.tik_dt):
		w.tik(w.tik_dt)
	var eigen_kalf := 0                         # wilde koeien kalven ook; tel alleen de eigen kalveren
	for kk in w.vee:
		if kk.is_kalf() and kk.eigenaar == 0:
			eigen_kalf += 1
	_check(eigen_kalf == 0 and w.eigen_koeien() == 5, "na kalf_groei_s zijn de kalveren koeien (%d koeien, %d kalveren, %d vee, t=%.0f)" % [w.eigen_koeien(), w.kalveren(), w.vee.size(), w.tijd_s])
	var z := Wereld.new()
	z.laad()
	z.spel["economie"]["kalf_kans"] = 1.0
	z.tijd_s = z.seizoen_duur() + 10.0
	for i in 2:
		var k := z._spawn_koe()
		k.eigenaar = 0
		k.vast = true
		k.zet_tegel(z.dichtstbij_loopbaar(z.kampvuur + Vector2i(2 + i, 2)))
	for i in int(40.0 / z.tik_dt):
		z.tik(z.tik_dt)
	_check(z.kalveren() == 0, "in de zomer geen kalveren")

## Bouwplaatsstapels (view/bouwmenu.gd _stapelplekken): voor elk gebouw in elke draaiing twee tegels buiten de
## voetafdruk, aan de deurkant (langs de gevel of een rij verder), niet op de deurtegel of het pad ervoor.

	# wilde koeien kalven ook, ongeacht eigenaar (gebruiker 2026-10-30)
	var v := Wereld.new()
	v.laad()
	v.spel["economie"]["kalf_kans"] = 1.0
	v.tijd_s = 10.0
	var wild: Array[Vee] = []
	for i in 2:
		var k := v._spawn_koe()
		k.van_generator = false
		k.vast = true
		k.zet_tegel(v.dichtstbij_loopbaar(v.kampvuur + Vector2i(8 + i, 6)))
		wild.append(k)
	for i in int(30.0 / v.tik_dt):
		v.tik(v.tik_dt)
	var wilde_kalveren := 0
	for k in v.vee:
		if k.is_kalf() and k.eigenaar != 0:
			wilde_kalveren += 1
	_check(wilde_kalveren >= 1, "twee wilde koeien bij elkaar in de lente: wild kalf (%d)" % wilde_kalveren)
	# ouderdom: een koe die haar levensduur haalt sterft, haar kalf blijft
	var oud := wild[0]
	oud.leeftijd_s = oud.levensduur_s - 0.05
	var n_voor := v.vee.size()
	v.tik(v.tik_dt)
	v.tik(v.tik_dt)
	_check(not oud in v.vee and v.vee.size() == n_voor - 1, "koe sterft van ouderdom (%d -> %d)" % [n_voor, v.vee.size()])
	var levens := []
	for k in v.vee:
		levens.append(k.levensduur_s)
	_check(levens.min() >= 4320.0 and levens.max() <= 6480.0, "levensduur 4-6 jaar")
	# kudde-maximum los van de generator
	v.spel["economie"]["vee_max"] = v.vee.size()
	v.tijd_s = 4.0 * v.seizoen_duur() + 10.0    # volgende lente
	var n_max := v.vee.size()
	for i in int(30.0 / v.tik_dt):
		v.tik(v.tik_dt)
	_check(v.vee.size() <= n_max + 1, "boven vee_max geen kalveren meer (%d, max %d; generator mag er 1 bij zetten)" % [v.vee.size(), n_max])
	v.spel["economie"]["vee_max"] = 24
## Missie 1 heeft geen put: wie dorst heeft drinkt bij de bron (de plas bij het dorp), gratis.
func _test_bron() -> void:
	var w := Wereld.new()
	w.laad()
	var drank := []
	w.gedronken.connect(func(d: Dorpeling, p: Plan) -> void: drank.append([d.id, p]))
	var d: Dorpeling = null
	for x in w.dorpelingen:
		if x.volwassen() and d == null:
			d = x
	d.bevel = {}
	d.route.clear()
	d.dorst = float(w.spel["economie"]["dorst_s"]) + 1.0
	for k in d.trek:
		d.trek[k] = 0.0
	var kas := w.kas
	for i in 900:
		if not drank.is_empty():
			break
		w.tik(w.tik_dt)
	_check(not drank.is_empty() and drank[0][1] == null, "missie 1: dorstige dorpeling drinkt bij de bron (%s)" % str(drank))
	_check(d.dorst < 1.0 and w.kas >= kas, "dorst weer 0, water kost niets")
	var kind: Dorpeling = null
	for x in w.dorpelingen:
		if not x.volwassen() and kind == null:
			kind = x
	if kind != null:
		drank.clear()
		kind.bevel = {}
		kind.route.clear()
		kind.dorst = float(w.spel["economie"]["dorst_s"]) + 1.0
		for k in kind.trek:
			kind.trek[k] = 0.0
		for i in 900:
			if not drank.is_empty():
				break
			w.tik(w.tik_dt)
		_check(not drank.is_empty() and drank[0][0] == kind.id, "een kind drinkt ook bij de bron")


func _test_stapels() -> void:
	var w := Wereld.new()
	w.laad()
	var bm := Bouwmenu.new()
	bm.w = w
	var goed := 0
	var fout := []
	for soort in [&"hut", &"melkerij", &"kippenhok", &"gereedschapsloods", &"molen"]:
		for dr_ in 4:
			var p: Plan = null
			for r in 10:
				for dy in range(-r, r + 1):
					for dx in range(-r, r + 1):
						if p == null and maxi(absi(dx), absi(dy)) == r:
							p = w.maak_plan(soort, w.kampvuur + Vector2i(4 + dx, 4 + dy), dr_)
			if p == null:
				fout.append("%s/%d geen plek" % [soort, dr_])
				continue
			var pl: Array[Vector2i] = bm._stapelplekken(p, 2)
			var deur := p.deur_tegel()
			var dr := p.deur_richting()
			var ok := pl.size() == 2
			for t in pl:
				var v := Vector2(t - deur).dot(Vector2(dr))
				if p.afdruk().has_point(t) or t == deur or t == deur + dr or v < 0.0 or v > 1.0:
					ok = false
			if ok:
				goed += 1
			else:
				fout.append("%s/%d %s deur %s" % [soort, dr_, pl, deur])
	bm.free()
	_check(fout.is_empty(), "stapels aan de deurkant, vrij van voetafdruk en pad: %d/20 %s" % [goed, fout])
