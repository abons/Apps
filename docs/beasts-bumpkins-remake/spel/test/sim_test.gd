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
	var vrij := Vector2i(100, 64)
	_check(w.raster.loopbaar(100, 64) and w.raster.loopbaar(101, 65), "testplek (100,64) is vrij")
	var bp := w.maak_plan(&"hut", vrij, 0)
	_check(bp != null and w.plan_zet(bp), "hut kan op een vrije plek")
	_check(w.maak_plan(&"hut", vrij + Vector2i(1, 1), 0) == null, "tweede hut er half overheen kan niet")
	_check(w.maak_plan(&"hut", w.kampvuur, 0) == null, "hut op het kampvuur kan niet")
	_check(w.maak_plan(&"molen", vrij + Vector2i(5, 0), 0) == null, "onbekende soort geeft null")

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
	_check(not w.raster.loopbaar(100, 64), "afgebouwde hut blokkeert zijn tegels")
	_check(bouwer.werk_plan == null and not bouwer.bouwt, "bouwer is vrij na afloop")
	var in_hut := 0
	for dl in w.dorpelingen:
		if bp.afdruk().has_point(dl.tegel()):
			in_hut += 1
	_check(in_hut == 0, "niemand staat in de afgebouwde hut (%d)" % in_hut)

	print("---- ", "ALLES OK" if fouten == 0 else "%d FOUT(EN)" % fouten)
	quit(0 if fouten == 0 else 1)


func _check(ok: bool, tekst: String) -> void:
	print(("ok    " if ok else "FOUT  "), tekst)
	if not ok:
		fouten += 1
