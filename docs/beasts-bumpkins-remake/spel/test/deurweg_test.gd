extends SceneTree
## Headless test van de deurweg (gebruiker 2026-10-31: bij het plaatsen zie je al de weg naar de deur):
## godot --headless --path . -s test/deurweg_test.gd
## De ghost toont Wereld.weg_route van de deurtegel naar het pad; plan_zet legt precies die tegels en rekent
## prijs + nieuwe padtegels x weg_per_tegel af; draaien geeft een andere route; de hint noemt "Hut 300 + pad n x 20";
## de weg-ghost is de keienweg (shaders/weg_ghost.gdshader) in de ghost-tint;
## geen route -> rood met "Geen pad naar je dorp" en geen voorbeeld; te duur met het pad -> rood "Te duur".
## Annuleren (besluit gebruiker 2026-10-31, Wereld.annuleer_plan): kas terug zoals voor het plaatsen, de nieuwe
## padtegels weer de oude grond; een tegel die een ander plan of een eigen weg gebruikt blijft (en komt niet terug);
## begonnen = toch alles terug (gebruiker 2026-10-31).

var fouten := 0
var w: Wereld
var bm: Bouwmenu


func _initialize() -> void:
	process_frame.connect(_start, CONNECT_ONE_SHOT)


func _start() -> void:
	root.size = Vector2i(1600, 900)
	Bouwmenu.touch = false
	w = Wereld.new()
	_check(w.laad("", 1), "missie 1 laadt")
	w.kas = 100000
	var wereld3d := Node3D.new()
	root.add_child(wereld3d)
	var cam := Camera3D.new()
	cam.set_script(load("res://rts_camera.gd"))
	wereld3d.add_child(cam)
	cam.make_current()
	var b := Bestuur.new()
	b.w = w
	b.cam = cam
	root.add_child(b)
	bm = Bouwmenu.new()
	root.add_child(bm)
	bm.bouw(w, b, wereld3d)
	bm.kies(&"hut")
	var wpt := int(w.spel["weg_per_tegel"])

	# een plek met een deurweg van minstens 2 nieuwe tegels, die in een andere draai een andere route heeft
	var plek := Vector2i(-1, -1)
	var d0 := 0
	var d1 := 0
	for r in range(2, 12):
		for dx in range(-r, r + 1):
			for dz in range(-r, r + 1):
				if plek.x >= 0 or maxi(absi(dx), absi(dz)) != r:
					continue
				var t := w.kampvuur + Vector2i(dx, dz)
				var routes: Array[Array] = []
				for d in 4:
					bm.draai = d
					var p := bm._plan_op(t)
					routes.append(w.weg_route(p.deur_tegel(), p) if w.bouw_reden(p) == "" else ([] as Array[Vector2i]))
				for d in 4:
					if plek.x < 0 and w.weg_nieuw(routes[d] as Array[Vector2i]) >= 2:
						for e in 4:
							if plek.x < 0 and e != d and not routes[e].is_empty() and routes[e] != routes[d]:
								plek = t
								d0 = d
								d1 = e
	_check(plek.x >= 0, "plek met een deurweg gevonden (%s, draai %d en %d)" % [plek, d0, d1])
	if plek.x < 0:
		_klaar()
		return

	# ghost: voorbeeld = weg_route, zichtbaar, prijs in de hint
	bm.draai = d0
	var p0 := bm._plan_op(plek)
	_check(bm._toon_ghost(p0), "ghost groen")
	var verwacht := w.weg_route(p0.deur_tegel(), p0)
	_check(bm.pad_route == verwacht and not verwacht.is_empty(), "voorbeeld = weg_route (%d tegels)" % verwacht.size())
	_check(bm.pad_route[0] == p0.deur_tegel(), "voorbeeld begint op de deurtegel")
	_check(bm._pad_mi.visible and bm._pad_mi.mesh != null, "voorbeeld zichtbaar")
	var gm := bm._pad_mi.material_override as ShaderMaterial
	_check(gm != null and gm.shader.resource_path == "res://shaders/weg_ghost.gdshader" 			and gm.get_shader_parameter("ghost_tint") == Bouwmenu.GHOST_TINT_KAN 			and is_equal_approx(float(gm.get_shader_parameter("ghost_alfa")), Bouwmenu.GHOST_ALFA), "voorbeeld = keienweg-ghost, groen")
	var n := bm.pad_nieuw
	var tekst := ("Hut %d + pad %d x %d = %d" % [w.prijs(&"hut"), n, wpt, w.prijs(&"hut") + n * wpt]) if wpt > 0 else "Hut %d" % w.prijs(&"hut")
	_check(tekst in bm.hint.text, "hint: '%s'" % bm.hint.text)
	# goedkoop: zelfde sleutel = geen nieuwe BFS (de mesh blijft dezelfde)
	var mesh := bm._pad_mi.mesh
	bm._toon_ghost(bm._plan_op(plek))
	_check(bm._pad_mi.mesh == mesh, "zelfde tegel en draai: niet opnieuw gerekend")

	# draaien: andere deur, andere route
	bm.draai = d1
	var p1 := bm._plan_op(plek)
	bm._toon_ghost(p1)
	_check(bm.pad_route == w.weg_route(p1.deur_tegel(), p1) and bm.pad_route != verwacht, "draaien: nieuwe route (%d tegels)" % bm.pad_route.size())
	_check(bm._pad_mi.mesh != mesh, "draaien: voorbeeld opnieuw getekend")

	# te duur met het pad, wel genoeg voor het gebouw alleen
	bm.draai = d0
	w.kas = w.prijs(&"hut") + n * wpt - 1
	_check(not bm._toon_ghost(bm._plan_op(plek)) and "Te duur" in bm.hint.text, "prijs + pad te duur: rood (%s)" % bm.hint.text)
	var rm := bm._pad_mi.material_override as ShaderMaterial
	_check(bm._pad_mi.visible and rm.get_shader_parameter("ghost_tint") == Bouwmenu.GHOST_TINT_NIET, "prijs + pad te duur: weg-ghost rood")
	_check(not w.plan_zet(bm._plan_op(plek)), "prijs + pad te duur: niet gezet")

	# plaatsen: precies de getoonde tegels worden pad, kas = prijs + pad
	w.kas = 100000
	bm._toon_ghost(bm._plan_op(plek))
	var getoond := bm.pad_route.duplicate()
	var nieuw := bm.pad_nieuw
	var kas0 := w.kas
	var pz := bm._plan_op(plek)
	_check(w.plan_zet(pz), "plan gezet")
	var alles_pad := true
	for t: Vector2i in getoond:
		if w.raster.soort_naam(t.x, t.y) != "pad":
			alles_pad = false
	_check(alles_pad, "alle getoonde tegels zijn pad na plan_zet")
	_check(kas0 - w.kas == w.prijs(&"hut") + nieuw * wpt, "kas: %d eraf = %d + %d x %d" % [kas0 - w.kas, w.prijs(&"hut"), nieuw, wpt])
	var st_vrij := true
	for s in pz.stapels:
		if s in getoond:
			st_vrij = false
	_check(st_vrij, "stapels niet op de deurweg")
	# afbouwen kost niets meer: de deurweg ligt er al
	var kas1 := w.kas
	_check(w.leg_weg(pz.deur_tegel(), pz) == 0 and w.kas == kas1, "deurweg opnieuw leggen: 0 nieuw, gratis")

	_annuleren(pz, plek, kas0, wpt)

	# geen route: de deurtegel ingesloten door water/rots -> rood, reden, geen voorbeeld
	var dicht := _ingesloten()
	if dicht != null:
		_check(not bm._toon_ghost(dicht) and Wereld.REDEN_GEEN_PAD in bm.hint.text, "geen route: rood, '%s'" % bm.hint.text)
		_check(bm.pad_route.is_empty() and not bm._pad_mi.visible, "geen route: geen voorbeeld")
		_check(not w.plan_zet(dicht), "geen route: niet gezet")
	else:
		_check(false, "geen ingesloten plek gevonden")
	_klaar()


func _annuleren(pz: Plan, plek: Vector2i, kas0: int, wpt: int) -> void:
	# 1. plaatsen -> annuleren: alles terug, de nieuwe tegels weg, de bouwplaats weg (ook in de view)
	var oud := pz.pad_oud.duplicate()
	_check(not oud.is_empty(), "plan legde %d nieuwe padtegels" % oud.size())
	var bouwer: Dorpeling = null
	for d in w.dorpelingen:
		if d.kan_bouwen():
			bouwer = d
			break
	if bouwer != null:
		bouwer.werk_plan = pz
	_check(w.annuleer_opbrengst(pz) == w.prijs(&"hut") + oud.size() * wpt, "opbrengst vooraf = prijs + pad (%d)" % w.annuleer_opbrengst(pz))
	var terug := w.annuleer_plan(pz)
	_check(w.kas == kas0, "annuleren: kas terug op %d (nu %d, +%d)" % [kas0, w.kas, terug])
	var weg := true
	for t: Vector2i in oud:
		if w.raster.soort[w.raster.idx(t.x, t.y)] != int(oud[t]):
			weg = false
	_check(weg, "annuleren: de nieuwe padtegels zijn weer de oude grond")
	_check(not pz in w.plannen and w.plan_op(plek) == null, "annuleren: plan weg")
	_check(not bm._kisten.has(pz) and not bm._stapels.has(pz), "annuleren: bouwplaats en stapels weg uit de view")
	_check(bouwer == null or bouwer.werk_plan == null, "annuleren: de bouwer is vrij")
	_check(w.annuleer_plan(pz) == -1, "nog eens annuleren: kan niet")

	# 2. gedeeld: een tweede plan waarvan de route op een nieuwe tegel van A uitkomt; A annuleren laat die staan
	bm.draai = 0
	var a := bm._plan_op(plek)
	for d in 4:
		bm.draai = d
		a = bm._plan_op(plek)
		if w.bouw_reden(a) == "" and w.weg_nieuw(w.weg_route(a.deur_tegel(), a)) >= 3:
			break
	var kas_a := w.kas
	_check(w.plan_zet(a), "gedeeld: plan A gezet (%d nieuwe tegels)" % a.pad_oud.size())
	var b := _plan_over(a)
	if b == null:
		_check(false, "gedeeld: geen tweede plan gevonden dat over de deurweg van A loopt")
	else:
		var b_route := w.weg_route(b.deur_tegel(), b)
		var gedeeld: Vector2i = b_route[b_route.size() - 1]
		var k := a.deurweg.find(gedeeld)
		var kas_b := w.kas
		_check(w.plan_zet(b), "gedeeld: plan B komt uit op tegel %d van A's deurweg" % k)
		var b_kosten := kas_b - w.kas
		var verwacht := w.prijs(&"hut") + k * wpt      # tegels 0..k-1 van A gaan weg, k en verder blijven
		_check(w.annuleer_opbrengst(a) == verwacht, "gedeeld: opbrengst %d = prijs + %d x %d" % [w.annuleer_opbrengst(a), k, wpt])
		var blijft: Array[Vector2i] = []
		for i in range(k, a.deurweg.size()):
			blijft.append(a.deurweg[i])
		var weg_a: Array[Vector2i] = []
		for i in k:
			weg_a.append(a.deurweg[i])
		w.annuleer_plan(a)
		_check(w.kas == kas_a - b_kosten - (a.pad_oud.size() - k) * wpt, "gedeeld: kas terug op alles behalve de gedeelde tegels")
		var ok_blijft := true
		for t in blijft:
			if w.raster.soort_naam(t.x, t.y) != "pad":
				ok_blijft = false
		_check(ok_blijft, "gedeeld: de %d gedeelde tegels blijven pad" % blijft.size())
		var ok_weg := true
		for t in weg_a:
			if w.raster.soort_naam(t.x, t.y) == "pad":
				ok_weg = false
		_check(ok_weg, "gedeeld: de %d eigen tegels zijn weg" % weg_a.size())
		var b_pad := true
		for t in b.deurweg:
			if w.raster.soort_naam(t.x, t.y) != "pad":
				b_pad = false
		_check(b_pad, "gedeeld: de deurweg van B is heel")
		w.annuleer_plan(b)

	# 3. eigen weg: een padtegel naast de deurweg (een zelf gelegde weg) houdt die tegel en wat erachter ligt
	var c := _vrij_hutplan(plek)
	if c == null:
		_check(false, "eigen weg: geen plek")
	else:
		var kas_c := w.kas
		w.plan_zet(c)
		var naast := _vrije_buur(c, c.deurweg[c.pad_oud.size() - 1])
		var k := 0         # de eerste deurwegtegel naast de nieuwe weg: daar stopt het weghalen
		while k < c.deurweg.size() and maxi(absi(c.deurweg[k].x - naast.x), absi(c.deurweg[k].y - naast.y)) > 1:
			k += 1
		if naast.x < 0:
			_check(false, "eigen weg: geen vrije buurtegel")
		else:
			var naast_oud := w.raster.soort[w.raster.idx(naast.x, naast.y)]
			w.raster.soort[w.raster.idx(naast.x, naast.y)] = w.raster.namen.find("pad")    # zoals Wereld._weg_af
			var verwacht := w.prijs(&"hut") + k * wpt
			_check(w.annuleer_plan(c) == verwacht, "eigen weg: alleen %d tegel(s) voor de aansluiting terug" % k)
			_check(w.raster.soort_naam(c.deurweg[k].x, c.deurweg[k].y) == "pad", "eigen weg: de aansluiting blijft pad")
			_check(w.kas == kas_c - (c.pad_oud.size() - k) * wpt, "eigen weg: kas klopt")
			w.raster.soort[w.raster.idx(naast.x, naast.y)] = naast_oud

	# 4. begonnen: toch alles terug, gebouwprijs en deurweg (gebruiker 2026-10-31)
	var e := _vrij_hutplan(plek)
	_check(e != null, "begonnen: plek gevonden")
	if e != null:
		var kas_e := w.kas
		w.plan_zet(e)
		e.voortgang = 0.3
		var n_e := e.pad_oud.size()
		_check(w.annuleer_plan(e) == w.prijs(&"hut") + n_e * wpt and w.kas == kas_e, "begonnen: alles terug (%d + %d x %d)" % [w.prijs(&"hut"), n_e, wpt])


## Een hutplan op dezelfde plek als eerder, in de eerste draai die kan en 2+ nieuwe padtegels heeft.
func _vrij_hutplan(plek: Vector2i) -> Plan:
	for d in 4:
		bm.draai = d
		var p := bm._plan_op(plek)
		if w.bouw_reden(p) == "" and w.kan_betalen_plan(p) and w.weg_nieuw(w.weg_route(p.deur_tegel(), p)) >= 2:
			return p
	return null


## Een buurtegel van `t` die geen pad is, niet op de deurweg en niet in de voetafdruk ligt, en loopbaar is.
func _vrije_buur(p: Plan, t: Vector2i) -> Vector2i:
	for d in 8:
		var n := t + Vector2i(Raster.DC[d], Raster.DR[d])
		if not n in p.deurweg and not p.afdruk().has_point(n) and w.raster.loopbaar_v(n) 				and w.raster.soort_naam(n.x, n.y) != "pad" and not p.pad_buren.has(n):
			return n
	return Vector2i(-1, -1)


## Een hutplan (andere plek) waarvan de deurweg uitkomt op een tegel die `a` nieuw legde, niet de deurtegel van a.
func _plan_over(a: Plan) -> Plan:
	for r in range(3, 14):
		for dx in range(-r, r + 1):
			for dz in range(-r, r + 1):
				if maxi(absi(dx), absi(dz)) != r:
					continue
				for d in 4:
					bm.draai = d
					var q := bm._plan_op(a.tegel + Vector2i(dx, dz))
					if q == null or w.bouw_reden(q) != "" or not w.kan_betalen_plan(q):
						continue
					var route := w.weg_route(q.deur_tegel(), q)
					if route.is_empty() or w.weg_nieuw(route) < 1:
						continue
					var eind: Vector2i = route[route.size() - 1]
					var k := a.deurweg.find(eind)
					if k >= 1 and a.pad_oud.has(eind):
						return q
	return null


## Een hutplan waarvan de deurweg niet kan: de deurtegel ligt in een stuk dat niet aan het dorp vastzit. We sluiten de
## plek zelf in met een ring geblokkeerde tegels om de voetafdruk en de deurtegel heen (raster.blok), dan bereik opnieuw.
func _ingesloten() -> Plan:
	bm.draai = 0
	for r in range(14, 40):
		var t := w.kampvuur + Vector2i(r, r)
		var p := bm._plan_op(t)
		if p == null or not w.kan_bouwen(p):
			continue
		var omvat := p.afdruk().merge(Rect2i(p.deur_tegel(), Vector2i.ONE)).grow(1)
		for c in range(omvat.position.x, omvat.end.x):
			for rij in range(omvat.position.y, omvat.end.y):
				if c == omvat.position.x or rij == omvat.position.y or c == omvat.end.x - 1 or rij == omvat.end.y - 1:
					w.raster.blok[w.raster.idx(c, rij)] = 1
		w.bereik = Router.bereikbaar(w.raster, w._vrij_naast(w.kampvuur))
		w.overal_bouwen = true      # alleen de deurweg mag de reden zijn
		return p
	return null


func _klaar() -> void:
	print("deurweg_test: %s" % ("OK" if fouten == 0 else "%d FOUT(EN)" % fouten))
	quit(1 if fouten > 0 else 0)


func _check(ok: bool, wat: String) -> void:
	if not ok:
		fouten += 1
	print(("  ok   " if ok else "  FOUT ") + wat)
