extends SceneTree
## Headless test van de bouw-ghost (view/bouwmenu.gd): godot --headless --path . --script res://test/ghost_test.gd
## Per gebouw met een glb (hut, loods, kippenhok, molen, melkerij) en per draai: eerst de kist, na het laden het gebouw
## zelf (kist weg), doorzichtig, zonder schaduw; groen op een vrije plek, rood op het kampvuur; de deurpijl op
## Plan.deur_tegel en wijzend naar de deur; en het gebouw dat er na plan_zet + klaar staat heeft exact de transform
## van de ghost. Zonder glb (assets/ ontbreekt) slaat het die soort over.

var fouten := 0
var w: Wereld
var bm: Bouwmenu
var wereld3d: Node3D
var _taak: Array = []     ## [soort, draai] nog te doen
var _wacht := 0


func _initialize() -> void:
	process_frame.connect(_start, CONNECT_ONE_SHOT)


func _start() -> void:
	root.size = Vector2i(1600, 900)
	Bouwmenu.touch = false
	w = Wereld.new()
	_check(w.laad("", 1), "missie 1 laadt")
	w.alles_open = true
	w.kas = 1000000
	wereld3d = Node3D.new()
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
	for s in [&"hut", &"gereedschapsloods", &"kippenhok", &"molen", &"melkerij"]:
		if not ResourceLoader.exists(Bouwmenu.GEBOUWEN[s]["glb"]):
			print("  overgeslagen (geen glb): ", s)
			continue
		for d in 4:
			_taak.append([s, d])
	# de kist zolang de glb laadt (eerste keer, nog niet in de cache)
	bm.kies(&"hut")
	var p := bm._plan_op(_vrije_tegel())
	bm._toon_ghost(p)
	if not Bouwmenu._scenes.has(Bouwmenu.GEBOUWEN[&"hut"]["glb"]):
		_check(bm.ghost.visible and bm._gmodel == null, "kist zolang de glb laadt")
	process_frame.connect(_stap)


func _stap() -> void:
	if _taak.is_empty():
		print("ghost_test: %s" % ("OK" if fouten == 0 else "%d FOUT(EN)" % fouten))
		quit(1 if fouten > 0 else 0)
		return
	var s: StringName = _taak[0][0]
	var d: int = _taak[0][1]
	if bm.soort != s or not bm.actief:
		bm.kies(s)
	bm.draai = d
	var t := _vrije_tegel()
	var p := bm._plan_op(t)
	var kan := bm._toon_ghost(p)
	if bm._gmodel == null:
		_wacht += 1
		if _wacht > 3000:
			_check(false, "%s: glb laadt niet" % s)
			_taak.pop_front()
		return
	_wacht = 0
	_taak.pop_front()
	var tag := "%s draai %d" % [s, d]
	_check(kan, tag + ": groen op vrije tegel %s" % t)
	_check(bm._gmodel.visible and not bm.ghost.visible, tag + ": gebouw zichtbaar, kist weg")
	var mats_ok := bm._gsurf.size() > 0
	for e: Array in bm._gsurf:
		var mi: MeshInstance3D = e[0]
		var m := mi.get_surface_override_material(e[1]) as BaseMaterial3D
		if m == null or m.transparency == BaseMaterial3D.TRANSPARENCY_DISABLED or m != e[2] \
				or mi.cast_shadow != GeometryInstance3D.SHADOW_CASTING_SETTING_OFF:
			mats_ok = false
	_check(mats_ok, tag + ": alle oppervlakken doorzichtig groen, geen schaduw (%d)" % bm._gsurf.size())
	# deurpijl
	var dt := p.deur_tegel()
	var pp := bm._pijl.position
	_check(bm._pijl.visible and Vector2i(int(floor(pp.x / w.tegel_m)), int(floor(pp.z / w.tegel_m))) == dt,
			tag + ": pijl op de deurtegel %s" % dt)
	var punt := p.deur_punt(w.tegel_m)
	var naar := (punt - Vector2(pp.x, pp.z)).normalized()
	var pijl_x := bm._pijl.global_transform.basis.x
	_check(Vector2(pijl_x.x, pijl_x.z).normalized().dot(naar) > 0.7, tag + ": pijl wijst naar de deur")
	# rood op het kampvuur
	var rood := bm._toon_ghost(bm._plan_op(w.kampvuur))
	var m0 := (bm._gsurf[0][0] as MeshInstance3D).get_surface_override_material(bm._gsurf[0][1])
	_check(not rood and m0 == bm._gsurf[0][3], tag + ": rood op het kampvuur")
	# bouwen en vergelijken: het afgebouwde gebouw staat precies waar de ghost stond
	bm._toon_ghost(p)
	var g_tf := bm._gmodel.global_transform
	var voor := wereld3d.get_child_count()
	_check(w.plan_zet(p), tag + ": plan gezet")
	p.voortgang = 1.0
	p.klaar = true
	bm._plan_klaar(p)
	var gebouw: Node3D = wereld3d.get_child(wereld3d.get_child_count() - 1)
	_check(wereld3d.get_child_count() >= voor and gebouw != bm._gmodel, tag + ": gebouw neergezet")
	_check(gebouw.global_transform.is_equal_approx(g_tf), tag + ": gebouw = ghost (%s vs %s)" % [gebouw.global_transform.origin, g_tf.origin])
	w.plannen.erase(p)        # plek weer vrij voor de volgende
	gebouw.visible = false   # niet vrijgeven: de molenwieken staan in Bouwmenu._wieken


## Eerste vrije tegel in een spiraal rond het kampvuur (een paar tegels ervandaan) waar de huidige soort past.
func _vrije_tegel() -> Vector2i:
	var mid := w.kampvuur + Vector2i(0, 8)
	for r in range(0, 30):
		for dx in range(-r, r + 1):
			for dz in range(-r, r + 1):
				if maxi(absi(dx), absi(dz)) != r:
					continue
				var p := bm._plan_op(mid + Vector2i(dx, dz))
				if p != null and w.kan_bouwen(p):
					return mid + Vector2i(dx, dz)
	return w.kampvuur


func _check(ok: bool, wat: String) -> void:
	if not ok:
		fouten += 1
	print(("  ok   " if ok else "  FOUT ") + wat)
