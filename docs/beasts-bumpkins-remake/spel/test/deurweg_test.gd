extends SceneTree
## Headless test van de deurweg (gebruiker 2026-10-31: bij het plaatsen zie je al de weg naar de deur):
## godot --headless --path . -s test/deurweg_test.gd
## De ghost toont Wereld.weg_route van de deurtegel naar het pad; plan_zet legt precies die tegels en rekent
## prijs + nieuwe padtegels x weg_per_tegel af; draaien geeft een andere route; de hint noemt "Hut 300 + pad n x 20";
## de weg-ghost is de keienweg (shaders/weg_ghost.gdshader) in de ghost-tint;
## geen route -> rood met "Geen pad naar je dorp" en geen voorbeeld; te duur met het pad -> rood "Te duur".

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
	var tekst := "Hut %d + pad %d x %d = %d" % [w.prijs(&"hut"), n, wpt, w.prijs(&"hut") + n * wpt]
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

	# geen route: de deurtegel ingesloten door water/rots -> rood, reden, geen voorbeeld
	var dicht := _ingesloten()
	if dicht != null:
		_check(not bm._toon_ghost(dicht) and Wereld.REDEN_GEEN_PAD in bm.hint.text, "geen route: rood, '%s'" % bm.hint.text)
		_check(bm.pad_route.is_empty() and not bm._pad_mi.visible, "geen route: geen voorbeeld")
		_check(not w.plan_zet(dicht), "geen route: niet gezet")
	else:
		_check(false, "geen ingesloten plek gevonden")
	_klaar()


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
