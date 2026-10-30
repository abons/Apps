extends SceneTree
## Headless simtest wolven (missie 2, sim/wolf.gd): godot --headless --path . --script res://test/wolf_test.gd
## Wolf zwerft; jaagt op een wilde koe en eet haar op; een koe in een weide achter een dichte poort haalt hij niet (open:
## wel); een volwassene met een vechtbevel gooit hem met stenen dood; kind en bouwer krijgen geen vechtbevel; wie niets
## omhanden heeft verdedigt zelf. Dorpelingen (gebruiker 2026-10-30): de wolf kiest een kind eerder dan een volwassene,
## bijt met tussenpozen, een beet doet schade en kan doden (uit alle lijsten, voorwerp valt, wieg weg, missie verloren);
## een kind rent weg; wolven komen terug uit een wolf-generator (missie.wolf_generator).

var fouten := 0


func _initialize() -> void:
	_test_zwerven()
	_test_jagen()
	_test_weide()
	_test_vechten()
	_test_wie_vecht()
	_test_verweer()
	_test_prooi_keuze()
	_test_beet()
	_test_dood()
	_test_kind_vlucht()
	_test_generator()
	_test_model()
	var w1 := Wereld.new()
	w1.laad()
	_check(w1.wolven.is_empty(), "missie 1 heeft geen wolven")
	print("---- ", "ALLES OK" if fouten == 0 else "%d FOUT(EN)" % fouten)
	quit(0 if fouten == 0 else 1)


## Missie 2 zonder koeien en zonder zelfverdediging: alleen de wolven en het dorp.
func _wereld() -> Wereld:
	var w := Wereld.new()
	w.laad("", 2)
	w.vee.clear()
	w.spel["wolf"]["verweer_straal"] = 0.0
	return w


func _koe(w: Wereld, t: Vector2i, eigen := false) -> Vee:
	var k := Vee.new()
	k.id = 900 + w.vee.size()
	k.zet_tegel(t)
	k.anker = t
	k.eigenaar = 0 if eigen else -1
	k.wacht = 99.0                # staat stil, dan meet de test alleen de wolf
	w.vee.append(k)
	return k


## Een loopbare, bereikbare tegel op afstand `af` van `van` (eerste die past, rondom).
func _tegel_op(w: Wereld, van: Vector2i, af: int) -> Vector2i:
	for dy in range(-af, af + 1):
		for dx in range(-af, af + 1):
			if maxi(absi(dx), absi(dy)) != af:
				continue
			var t := van + Vector2i(dx, dy)
			if w.raster.loopbaar_v(t) and w.bereik[w.raster.idx(t.x, t.y)] == 1:
				return t
	return Vector2i(-1, -1)


func _test_zwerven() -> void:
	var w := _wereld()
	_check(w.wolven.size() == 3, "3 wolven in missie 2 (zijn %d)" % w.wolven.size())
	var wf: Wolf = w.wolven[0]
	_check(wf.hp == int(w.spel["wolf"]["hp"]) and wf.toestand == Wolf.ROAM, "wolf begint zwervend met %d hp" % wf.hp)
	var start := wf.pos
	var verst := 0.0
	var bewogen := false
	for i in int(60.0 / w.tik_dt):
		w.tik(w.tik_dt)
		verst = maxf(verst, wf.pos.distance_to(Vector2(wf.anker) + Vector2(0.5, 0.5)))
		if wf.pos.distance_to(start) > 0.5:
			bewogen = true
	_check(bewogen, "wolf zwerft (beweegt in 60 s)")
	var straal := float(w.spel["wolf"]["zwerf_straal"])
	_check(verst <= straal * 1.5 + 0.5, "blijft rond zijn startplek (verst %.1f tegels, straal %d)" % [verst, int(straal)])
	_check(wf.toestand == Wolf.ROAM, "zonder koeien blijft hij zwerven")


func _test_jagen() -> void:
	var w := _wereld()
	var wf: Wolf = w.wolven[0]
	var t := _tegel_op(w, wf.tegel(), 5)
	_check(t.x >= 0, "wilde koe 5 tegels van de wolf (%s)" % t)
	var k := _koe(w, t)
	var weg := [false]
	w.koe_weg.connect(func(kw: Vee) -> void:
		if kw == k:
			weg[0] = true)
	var jaagde := false
	var viel_aan := false
	var tikken := 0
	while k in w.vee and tikken < int(40.0 / w.tik_dt):
		w.tik(w.tik_dt)
		tikken += 1
		jaagde = jaagde or wf.toestand == Wolf.HUNT
		viel_aan = viel_aan or wf.toestand == Wolf.ATTACK
	_check(jaagde, "wolf ziet de koe en jaagt")
	_check(viel_aan, "wolf valt de koe aan")
	_check(not k in w.vee and weg[0], "koe is opgegeten (na %.1f s, signaal koe_weg)" % (tikken * w.tik_dt))
	_check(wf.toestand == Wolf.ROAM and wf.prooi == null and wf.rust > 0.0, "daarna zwerft hij verder, verzadigd")


## Vrij stuk grond van 6x5 binnen een paar tegels van `bij` (geen pad, loopbaar, bereikbaar), voor een hek rondom.
func _vrij_vak(w: Wereld, bij: Vector2i) -> Vector2i:
	for r in range(2, 12):
		for dy in range(-r, r + 1):
			for dx in range(-r, r + 1):
				if maxi(absi(dx), absi(dy)) != r:
					continue
				var o := bij + Vector2i(dx, dy)
				var vrij := true
				for ex in range(-1, 7):
					for ey in range(-1, 6):
						var t := o + Vector2i(ex, ey)
						if not w.raster.loopbaar_v(t) or w.raster.soort_naam(t.x, t.y) == "pad" or w.bereik[w.raster.idx(t.x, t.y)] == 0:
							vrij = false
				if vrij:
					return o
	return Vector2i(-1, -1)


func _test_weide() -> void:
	var w := _wereld()
	w.alles_open = true
	var wf: Wolf = w.wolven[0]
	var o := _vrij_vak(w, wf.tegel())
	_check(o.x >= 0, "vrij vak voor een weide bij de wolf (%s)" % o)
	if o.x < 0:
		return
	var poort: Plan = null
	for dx in range(6):
		for dy in range(5):
			if dx != 0 and dx != 5 and dy != 0 and dy != 4:
				continue
			var srt := &"poort" if (dx == 2 and dy == 4) else &"hek"
			var p := Plan.new(srt, o + Vector2i(dx, dy), 0, 1, 1)
			if w.plan_zet(p):
				w._rond_af(p)
				if srt == &"poort":
					poort = p
	_check(poort != null and w.weides.size() == 1 and w.poort_dicht(poort.tegel), "weide met dichte poort gebouwd")
	var k := _koe(w, o + Vector2i(2, 2), true)
	w._wijs_weides_toe()
	k.wacht = 99.0
	# de wolf zet vlak naast het hek: de koe is binnen zicht
	var buiten := o + Vector2i(2, 6)
	wf.zet_tegel(buiten)
	wf.anker = buiten
	_check(wf.pos.distance_to(k.pos) <= float(w.spel["wolf"]["zicht"]), "koe binnen het zicht van de wolf (%.1f)" % wf.pos.distance_to(k.pos))
	var ooit_aanval := false
	var ooit_erin := false
	for i in int(40.0 / w.tik_dt):
		w.tik(w.tik_dt)
		ooit_aanval = ooit_aanval or wf.toestand == Wolf.ATTACK
		ooit_erin = ooit_erin or w.weides[0].has(wf.tegel())
	_check(k in w.vee and not ooit_aanval and not ooit_erin, "poort dicht: wolf komt de weide niet in en pakt de koe niet")
	w.wissel_poort(poort)
	var tikken := 0
	while k in w.vee and tikken < int(60.0 / w.tik_dt):
		w.tik(w.tik_dt)
		tikken += 1
	_check(not k in w.vee, "poort open: wolf loopt erin en pakt de koe (%.1f s)" % (tikken * w.tik_dt))


func _volwassen_man(w: Wereld) -> Dorpeling:
	for d in w.dorpelingen:
		if d.volwassen() and d.geslacht == "man":
			return d
	return null


func _test_vechten() -> void:
	var w := _wereld()
	var wf: Wolf = w.wolven[0]
	var d := _volwassen_man(w)
	var t := _tegel_op(w, wf.tegel(), 9)
	d.zet_tegel(t)
	var worpen := [0]
	var dood := [false]
	var vergaan := [false]
	w.steen_gegooid.connect(func(dd: Dorpeling, ww: Wolf) -> void:
		if dd == d and ww == wf:
			worpen[0] += 1)
	w.wolf_dood.connect(func(ww: Wolf) -> void: dood[0] = dood[0] or ww == wf)
	w.wolf_weg.connect(func(ww: Wolf) -> void: vergaan[0] = vergaan[0] or ww == wf)
	_check(w.geef_vechtbevel([d.id], wf.id) == 1 and d.doel_wolf == wf, "volwassene krijgt een vechtbevel op de wolf")
	var tikken := 0
	var gooide_binnen := true
	while wf.leeft() and tikken < int(90.0 / w.tik_dt):
		w.tik(w.tik_dt)
		tikken += 1
		if d.worp_t == 0.0 and d.pos.distance_to(wf.pos) > float(w.spel["wolf"]["steen_bereik"]) + 0.01:
			gooide_binnen = false
	var c: Dictionary = w.spel["wolf"]
	var nodig := int(ceil(float(c["hp"]) / float(c["steen_schade"])))
	_check(not wf.leeft() and dood[0], "wolf is dood na %.1f s" % (tikken * w.tik_dt))
	_check(worpen[0] >= nodig, "met stenen: %d worpen (minstens %d nodig)" % [worpen[0], nodig])
	_check(gooide_binnen, "hij gooit alleen binnen het steenbereik (%.1f tegels)" % float(c["steen_bereik"]))
	_check(wf.hp == 0 and wf.toestand == Wolf.DYING, "hp 0, wolf valt om (DYING)")
	for i in int((float(c["sterf_s"]) + 0.5) / w.tik_dt):
		w.tik(w.tik_dt)
	_check(wf.toestand == Wolf.DEAD, "daarna DEAD")
	_check(d.doel_wolf == null and d.bevel.is_empty(), "dorpeling stopt met gooien")
	for i in int((float(c["rot_s"]) + 1.0) / w.tik_dt):
		w.tik(w.tik_dt)
	_check(vergaan[0] and not wf in w.wolven and w.wolven.size() == 2, "dode wolf vergaat (2 over)")
	_check(w.geef_vechtbevel([d.id], wf.id) == 0, "geen vechtbevel op een dode wolf")


func _test_wie_vecht() -> void:
	var w := _wereld()
	var wf: Wolf = w.wolven[0]
	var kind: Dorpeling = null
	for d in w.dorpelingen:
		if not d.volwassen():
			kind = d
	_check(kind != null and w.geef_vechtbevel([kind.id], wf.id) == 0 and kind.doel_wolf == null, "kind krijgt geen vechtbevel")
	var man := _volwassen_man(w)
	man.rol = "bouwer"
	_check(w.geef_vechtbevel([man.id], wf.id) == 0 and man.doel_wolf == null, "bouwer krijgt geen vechtbevel")
	man.rol = ""
	_check(w.geef_vechtbevel([kind.id, man.id], wf.id) == 1 and man.doel_wolf == wf and kind.doel_wolf == null, "gemengde selectie: alleen de volwassene vecht")
	_check(w.geef_bevel([man.id], "loop", man.tegel()) >= 0 and man.doel_wolf == null, "een nieuw bevel stopt het vechten")


func _test_verweer() -> void:
	var w := _wereld()
	w.spel["wolf"]["verweer_straal"] = 6.0
	var wf: Wolf = w.wolven[0]
	var k := _koe(w, _tegel_op(w, wf.tegel(), 4))
	var d := _volwassen_man(w)
	d.zet_tegel(_tegel_op(w, wf.tegel(), 3))
	d.anker = d.tegel()
	d.route.clear()
	d.bevel = {}
	var zelf := false
	for i in int(20.0 / w.tik_dt):
		w.tik(w.tik_dt)
		if d.doel_wolf == wf:
			zelf = true
			break
	_check(k != null and zelf, "volwassene zonder klus gooit zelf naar een wolf die vlakbij op een koe jaagt")


## Alle dorpelingen ver weg (binnen, bij het kampvuur) behalve die in `houd`: de wolf ziet alleen wie de test neerzet.
func _alleen(w: Wereld, houd: Array) -> void:
	for d in w.dorpelingen:
		if not d in houd:
			d.binnen = true
			d.zet_tegel(w.dichtstbij_loopbaar(w.kampvuur))


func _kind(w: Wereld) -> Dorpeling:
	for d in w.dorpelingen:
		if d.leeftijd == "kind":
			return d
	return null


func _test_prooi_keuze() -> void:
	var w := _wereld()
	var wf: Wolf = w.wolven[0]
	var kind := _kind(w)
	var man := _volwassen_man(w)
	_alleen(w, [kind, man])
	w.spel["leven"]["vlucht_straal"] = 0.0          # niemand rent weg: alleen de keuze telt
	var a := _tegel_op(w, wf.tegel(), 4)
	var b := wf.tegel() + (wf.tegel() - a)
	if not w.raster.loopbaar_v(b) or w.bereik[w.raster.idx(b.x, b.y)] == 0:
		b = a + Vector2i(1, 0) if w.raster.loopbaar_v(a + Vector2i(1, 0)) else a
	kind.zet_tegel(b)
	man.zet_tegel(a)
	for d in [kind, man]:
		d.wacht = 99.0
		d.anker = d.tegel()
	wf.kijk = 0.0
	var gekozen = null
	for i in int(3.0 / w.tik_dt):
		w.tik(w.tik_dt)
		if wf.prooi != null:
			gekozen = wf.prooi
			break
	_check(gekozen == kind, "wolf kiest het kind boven de volwassene op (bijna) gelijke afstand (prooi_voorkeur)")


func _test_beet() -> void:
	var w := _wereld()
	var wf: Wolf = w.wolven[0]
	var d := _volwassen_man(w)
	_alleen(w, [d])
	w.spel["leven"]["vlucht_onder"] = 0.0            # de volwassene blijft staan
	d.zet_tegel(_tegel_op(w, wf.tegel(), 3))
	d.anker = d.tegel()
	d.wacht = 99.0
	var beten: Array[float] = []
	w.dorpeling_geraakt.connect(func(dd: Dorpeling, oorzaak: String) -> void:
		if dd == d and oorzaak == "wolf":
			beten.append(w.tijd_s))
	var c: Dictionary = w.spel["wolf"]
	w.tik(w.tik_dt)
	var voor := d.gezondheid
	for i in int(30.0 / w.tik_dt):
		w.tik(w.tik_dt)
		if beten.size() >= 3:
			break
	_check(beten.size() >= 3, "wolf bijt de dorpeling (%d beten in 30 s)" % beten.size())
	_check(is_equal_approx(d.gezondheid, voor - float(beten.size()) * float(c["beet_schade"])),
		"elke beet %d schade (%.0f -> %.0f hp)" % [int(c["beet_schade"]), voor, d.gezondheid])
	var min_tussen := INF
	for i in range(1, beten.size()):
		min_tussen = minf(min_tussen, beten[i] - beten[i - 1])
	_check(min_tussen >= float(c["beet_pauze_s"]) - 0.01, "met tussenpozen: minstens %.1f s tussen beten (%.1f)" % [float(c["beet_pauze_s"]), min_tussen])
	_check(d in w.dorpelingen and d.leeft(), "na 3 beten leeft hij nog (%.0f/%.0f hp)" % [d.gezondheid, d.gezondheid_max])
	# herstel: geen wolf meer, na herstel_na_s komt de gezondheid terug
	w.wolven.clear()
	var na := d.gezondheid
	var l: Dictionary = w.spel["leven"]
	for i in int((float(l["herstel_na_s"]) + 20.0) / w.tik_dt):
		w.tik(w.tik_dt)
	_check(d.gezondheid > na, "herstel na %.0f s zonder schade (%.1f -> %.1f hp)" % [float(l["herstel_na_s"]), na, d.gezondheid])


func _test_dood() -> void:
	var w := _wereld()
	var wf: Wolf = w.wolven[0]
	var kind := _kind(w)
	var vader := _volwassen_man(w)
	_alleen(w, [kind])
	w.spel["leven"]["vlucht_straal"] = 0.0          # dit kind rent niet weg
	kind.zet_tegel(_tegel_op(w, wf.tegel(), 3))
	kind.anker = kind.tegel()
	kind.wacht = 99.0
	w.tik(w.tik_dt)                                   # leven begint (gezondheid uit de data)
	kind.gezondheid = 4.0
	# het kind draagt een voorwerp en staat (kunstmatig) in een wieg: beide moeten na de dood weg zijn
	var ob := {"cls": 159, "naam": "zilveren_beker", "model": "geen", "x": kind.tegel().x, "y": kind.tegel().y,
		"blokkeert": false, "voetafdruk": [1, 1], "state": 0, "sex": 0, "spawn": false, "owner": 0, "voorwerp": true,
		"drager": kind.id}
	w.objecten.append(ob)
	var wg := {"moeder": kind, "vader": vader, "hut": null, "wacht": 99.0, "deur": vader.tegel()}
	kind.wieg = wg
	vader.wieg = wg
	w.wiegen.append(wg)
	var dood := [""]
	w.dorpeling_dood.connect(func(dd: Dorpeling, oorzaak: String) -> void:
		if dd == kind:
			dood[0] = oorzaak)
	var n := w.dorpelingen.size()
	for i in int(20.0 / w.tik_dt):
		w.tik(w.tik_dt)
		if dood[0] != "":
			break
	_check(dood[0] == "wolf", "de wolf bijt het kind dood (signaal dorpeling_dood, oorzaak '%s')" % dood[0])
	_check(not kind in w.dorpelingen and w.dorpelingen.size() == n - 1 and w.doden == 1,
		"kind is uit de dorpelingen (%d over, doden %d)" % [w.dorpelingen.size(), w.doden])
	_check(int(ob["drager"]) == -1, "het gedragen voorwerp valt op de grond")
	_check(w.wiegen.is_empty() and vader.wieg.is_empty(), "de wieg is weg, de partner is vrij")
	_check(wf.prooi == null and wf.toestand == Wolf.ROAM and wf.rust > 0.0, "de wolf laat los en zwerft verzadigd verder")
	# verlies werkt echt: wie overblijft sterft tot er 1 is
	for d in w.dorpelingen.duplicate():
		if w.dorpelingen.size() > 1:
			d.sterf(w, "test")
	w.tik(w.tik_dt)
	_check(w.uitslag == "verloren", "1 dorpeling over na sterven: missie verloren")


func _test_kind_vlucht() -> void:
	var w := _wereld()
	var wf: Wolf = w.wolven[0]
	var kind := _kind(w)
	_alleen(w, [kind])
	wf.rust = 999.0                                   # de wolf jaagt niet: het kind schrikt van hem alleen
	var t := _tegel_op(w, wf.tegel(), 4)
	kind.zet_tegel(t)
	kind.anker = kind.tegel()
	kind.wacht = 99.0
	var af0 := kind.pos.distance_to(wf.pos)
	var vlucht := false
	var v_max := 0.0
	for i in int(3.0 / w.tik_dt):
		w.tik(w.tik_dt)
		vlucht = vlucht or kind.bevel.get("soort", "") == "vlucht"
		v_max = maxf(v_max, kind.snelheid_mps)
	_check(vlucht, "kind ziet een wolf binnen %.0f tegels en rent weg (bevel vlucht)" % float(w.spel["leven"]["vlucht_straal"]))
	_check(kind.pos.distance_to(wf.pos) > af0 + 1.0, "verder van de wolf (%.1f -> %.1f tegels)" % [af0, kind.pos.distance_to(wf.pos)])
	_check(v_max > w.loop_mps * w.looptempo * 1.2, "rent sneller dan lopen (%.2f m/s)" % v_max)
	var man := _volwassen_man(w)
	man.binnen = false
	man.zet_tegel(t)
	man.bevel = {}
	man.route.clear()
	_check(not Leven.vlucht_soort(w, man), "een gezonde volwassene vlucht niet (hij vecht)")
	man.gezondheid = 2.0
	_check(Leven.vlucht_soort(w, man), "een zwaargewonde volwassene vlucht wel")
	man.gezondheid = man.gezondheid_max
	man.rol = "bouwer"
	_check(Leven.vlucht_soort(w, man), "de bouwer vecht niet en vlucht")


func _test_generator() -> void:
	var w := _wereld()
	var t := w.wolven[0].anker
	w.missie["wolf_generator"] = [{"tegel": [t.x, t.y], "start": 1, "max": 2, "interval_s": 10.0}]
	var erbij := [0]
	w.wolf_erbij.connect(func(_wf: Wolf) -> void: erbij[0] += 1)
	w.tik(w.tik_dt)
	_check(w.wolven.size() == 4 and erbij[0] == 1, "generator zet 1 wolf bij de start (%d wolven)" % w.wolven.size())
	for i in int(10.5 / w.tik_dt):
		w.tik(w.tik_dt)
	_check(w.wolven.size() == 5, "na interval_s een tweede (%d)" % w.wolven.size())
	for i in int(25.0 / w.tik_dt):
		w.tik(w.tik_dt)
	_check(w.wolven.size() == 5, "niet boven max 2 (%d)" % w.wolven.size())
	var ids := {}
	for wf in w.wolven:
		ids[wf.id] = true
	_check(ids.size() == 5, "elke wolf een eigen id")
	var g: Wolf = null
	for wf in w.wolven:
		if wf.generator == 0:
			g = wf
	g.raak(w, 999)
	for i in int(10.5 / w.tik_dt):
		w.tik(w.tik_dt)
	var levend := 0
	for wf in w.wolven:
		if wf.generator == 0 and wf.leeft():
			levend += 1
	_check(levend == 2 and erbij[0] == 3, "een gedode wolf komt terug na interval_s (%d levend, %d gemaakt)" % [levend, erbij[0]])
	var w2 := _wereld()
	for i in int(5.0 / w2.tik_dt):
		w2.tik(w2.tik_dt)
	_check(w2.wolven.size() == 3, "missie 2 zelf heeft geen wolf-generator (origineel M2.MIS): blijft 3")


## Model (view/wolf_model.gd): spel.json wolf_model kiest de glb, met terugval; elke glb heeft de vijf clips.
func _test_model() -> void:
	var d = Gegevens.lees(Gegevens.SPEL)
	var keuze := String(d.get("wolf_model", ""))
	_check(keuze in ["trellis", "procedureel"], "spel.json wolf_model is trellis of procedureel (%s)" % keuze)
	for soort in [&"wolf", &"donkere_wolf"]:
		var pad := WolfModel.glb_pad(soort)
		if keuze == "trellis" and ResourceLoader.exists(WolfModel.GLB_TRELLIS[soort]):
			_check(pad == WolfModel.GLB_TRELLIS[soort], "%s: trellis-glb gekozen" % soort)
		else:
			_check(pad == WolfModel.GLB[soort], "%s: procedurele glb (terugval)" % soort)
		if not ResourceLoader.exists(pad):
			continue                    # assets/ staat niet in git: placeholder
		var n := WolfModel.maak(soort)
		var ap := WolfModel._speler(n)
		var clips := ap.get_animation_list() if ap else PackedStringArray()
		var alle := true
		for c in ["idle", "lopen", "rennen", "bijten", "dood"]:
			alle = alle and c in clips
		_check(alle, "%s: %s heeft idle, lopen, rennen, bijten, dood" % [soort, pad.get_file()])
		n.free()


func _check(ok: bool, tekst: String) -> void:
	print(("ok    " if ok else "FOUT  "), tekst)
	if not ok:
		fouten += 1
