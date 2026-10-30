extends SceneTree
## Headless test touch-bouwen (view/bouwmenu.gd met Bouwmenu.touch) en de twee-vingerdraai (rts_camera.gd):
## godot --headless --path . --script res://test/touch_bouw_test.gd
## Touch-events gaan via root.push_input door de echte invoerketen (Bouwmenu voor de camera). Bouwknop = ghost midden in
## beeld; tik ernaast = ghost daarheen; slepen op de ghost schuift hem zonder pannen; slepen ernaast pant; de geemuleerde
## muisklik plaatst niets; Draai draait; Bouwen alleen als het kan; weg: tik begin, sleep het eind, Bouwen legt de rij;
## Annuleer stopt. Twee vingers met de klok mee: de kaart draait met de klok mee.

var fouten := 0
var w: Wereld
var cam: Camera3D
var bm: Bouwmenu


func _initialize() -> void:
	process_frame.connect(_start, CONNECT_ONE_SHOT)   # root.push_input en de camera willen een boom die draait


func _start() -> void:
	root.size = Vector2i(2400, 1080)      # headless is 64x64; de Motorola liggend
	Bouwmenu.touch = true
	w = Wereld.new()
	_check(w.laad("", 1), "missie 1 laadt")
	w.alles_open = true
	w.kas = 100000
	var wereld3d := Node3D.new()
	root.add_child(wereld3d)
	cam = Camera3D.new()
	cam.set_script(load("res://rts_camera.gd"))
	wereld3d.add_child(cam)
	cam.make_current()
	var m := w.tegel_m
	var vuur := Vector3((w.kampvuur.x + 0.5) * m, 0, (w.kampvuur.y + 0.5) * m)
	cam.zet_direct(vuur, 0.6, deg_to_rad(50), 30.0)
	var b := Bestuur.new()
	b.w = w
	b.cam = cam
	root.add_child(b)
	bm = Bouwmenu.new()
	root.add_child(bm)            # na camera en Bestuur: krijgt de invoer eerst, zoals in main.gd
	bm.bouw(w, b, wereld3d)
	cam.pan_blokkade = func() -> bool: return bm.actief and not Bouwmenu.touch
	var maat := root.get_visible_rect().size
	print("  venster ", maat, "  knophoogte ", bm.knop_h)
	_check(bm.knop_h >= 110.0, "touchknoppen >= 110 px (%d)" % bm.knop_h)
	_check(bm.knop_bouw != null and bm.knop_bouw.custom_minimum_size.y >= 110.0, "Bouwen-knop bestaat en is groot")

	# --- gebouw (hut)
	bm.kies(&"hut")
	_check(bm.actief, "bouwknop: modus aan")
	_check(bm._t_tegel == b.tegel_onder(maat * 0.5), "ghost op de tegel midden in beeld (%s)" % bm._t_tegel)
	var vrij := _vrije_tegel(w.kampvuur + Vector2i(5, 3))
	_check(vrij.x >= 0, "vrije plek voor een hut gevonden (%s)" % vrij)
	var n0 := w.plannen.size()
	_tik(_scherm(vrij), 0)
	_check(bm._t_tegel == vrij, "tik naast de ghost: ghost daarheen (%s, wil %s)" % [bm._t_tegel, vrij])
	_check(w.plannen.size() == n0, "tik plaatst niets")
	# slepen op de ghost: schuift hem, de camera pant niet
	var f0: Vector3 = cam.doel_focus
	var doel := vrij + Vector2i(2, 1)
	_sleep(_scherm(vrij), _scherm(doel), 0)
	_check(bm._t_tegel == doel, "slepen op de ghost schuift hem (%s, wil %s)" % [bm._t_tegel, doel])
	_check(cam.doel_focus.is_equal_approx(f0), "slepen op de ghost pant niet")
	_check(w.plannen.size() == n0, "slepen plaatst niets")
	# slepen ver van de ghost: pant, ghost blijft
	var ver := Vector2(maat.x * 0.15, maat.y * 0.3)
	_check(_scherm_tegel_af(doel, ver) > 4, "sleeppunt ver van de ghost")
	_sleep(ver, ver + Vector2(200, 120), 0)
	_check(not cam.doel_focus.is_equal_approx(f0), "slepen naast de ghost pant de camera")
	_check(bm._t_tegel == doel, "ghost blijft staan bij pannen")
	cam.zet_direct(cam.doel_focus, cam.doel_yaw, cam.doel_pitch, cam.doel_afstand)
	# de geemuleerde muisklik van een vinger plaatst niets en geeft geen loopbevel
	_muis(_scherm(doel), true)
	_muis(_scherm(doel), false)
	_check(w.plannen.size() == n0, "geemuleerde muisklik plaatst niets")
	# draaien
	var d0 := bm.draai
	bm.knop_draai.pressed.emit()
	_check(bm.draai == (d0 + 1) % 4, "Draai: kwartslag")
	# Bouwen op een vrije plek
	var plek := _vrije_tegel(doel + Vector2i(-7, 2))   # ver genoeg van de ghost: een tik, geen vastpakken
	_tik(_scherm(plek), 0)
	_check(bm._t_tegel == plek, "ghost naar vrije plek %s" % plek)
	bm._process(0.016)
	_check(not bm.knop_bouw.disabled, "Bouwen aan op een vrije plek")
	bm.knop_bouw.pressed.emit()
	_check(w.plannen.size() == n0 + 1, "Bouwen zet een plan")
	var p: Plan = w.plannen[-1]
	_check(p.soort == &"hut" and p.draai == bm.draai, "plan is een hut in de gekozen draai (%s, %d)" % [p.soort, p.draai])
	bm._process(0.016)
	_check(bm.knop_bouw.disabled, "Bouwen uit op een bezette plek")
	bm.knop_bouw.pressed.emit()
	_check(w.plannen.size() == n0 + 1, "Bouwen op een bezette plek doet niets")
	_check(bm.actief, "modus blijft aan na Bouwen")

	# --- weg: tik begin, sleep het eind, Bouwen
	bm.kies(&"weg")
	var a := _vrije_weg(w.kampvuur + Vector2i(-6, 5))
	_tik(_scherm(a), 1)
	_check(bm._t_tegel == a and bm._t_eind == a, "weg: tik = begin %s" % a)
	var e := a + Vector2i(4, 0)
	f0 = cam.doel_focus
	_sleep(_scherm(a), _scherm(e), 1)
	_check(bm._t_eind == e and bm._t_tegel == a, "weg: slepen vanaf het begin trekt het eind (%s)" % bm._t_eind)
	_check(cam.doel_focus.is_equal_approx(f0), "weg: slepen van het eind pant niet")
	var n1 := w.plannen.size()
	_check(n1 == n0 + 1, "weg: nog niets geplaatst voor Bouwen")
	bm._process(0.016)
	var kan := 0
	for s in bm._t_st:
		if s == BouwRij.KAN:
			kan += 1
	_check(kan > 0 and not bm.knop_bouw.disabled, "weg: %d tegels kunnen, Bouwen aan" % kan)
	bm.knop_bouw.pressed.emit()
	_check(w.plannen.size() == n1 + kan, "weg: Bouwen legt de rij (%d plannen)" % (w.plannen.size() - n1))
	_check(bm._t_tegel == e, "weg: het eind is het nieuwe begin")
	bm.knop_stop.pressed.emit()
	_check(not bm.actief, "Annuleer: modus uit")

	# --- twee vingers met de klok mee (schermhoek op, y omlaag): de kaart draait met de klok mee
	var c := maat * 0.5
	var p_wereld: Vector3 = Vector3(cam.focus.x + 6.0, 0.0, cam.focus.z)
	var hoek0: float = (cam.unproject_position(p_wereld) - cam.unproject_position(cam.focus)).angle()
	var yaw0: float = cam.doel_yaw
	var r := 200.0
	var stappen := 10
	var draai_tot := 0.4
	_druk(c + Vector2(-r, 0), 0, true)
	_druk(c + Vector2(r, 0), 1, true)
	for i in range(1, stappen + 1):
		var h := draai_tot * i / stappen
		_drag(c + Vector2(-r, 0).rotated(h), 0)
		_drag(c + Vector2(r, 0).rotated(h), 1)
	_druk(c + Vector2(-r, 0).rotated(draai_tot), 0, false)
	_druk(c + Vector2(r, 0).rotated(draai_tot), 1, false)
	_check(cam.doel_yaw > yaw0 + 0.3, "twee vingers met de klok mee: yaw op (%.2f -> %.2f)" % [yaw0, cam.doel_yaw])
	cam.zet_direct(cam.doel_focus, cam.doel_yaw, cam.doel_pitch, cam.doel_afstand)
	var hoek1: float = (cam.unproject_position(p_wereld) - cam.unproject_position(cam.focus)).angle()
	_check(wrapf(hoek1 - hoek0, -PI, PI) > 0.2, "de kaart draait met de vingers mee (%.2f rad)" % wrapf(hoek1 - hoek0, -PI, PI))
	# knijpen: vingers uit elkaar = inzoomen
	var af0: float = cam.doel_afstand
	_druk(c + Vector2(-100, 0), 0, true)
	_druk(c + Vector2(100, 0), 1, true)
	_drag(c + Vector2(-200, 0), 0)
	_drag(c + Vector2(200, 0), 1)
	_druk(c + Vector2(-200, 0), 0, false)
	_druk(c + Vector2(200, 0), 1, false)
	_check(cam.doel_afstand < af0 * 0.6, "vingers uit elkaar: inzoomen (%.1f -> %.1f)" % [af0, cam.doel_afstand])

	print("---- ", "ALLES OK" if fouten == 0 else "%d FOUT(EN)" % fouten)
	quit(0 if fouten == 0 else 1)


## Eerste middentegel rond `bij` (spiraal) waar een hut in de huidige draai kan, en die midden in beeld ligt.
func _vrije_tegel(bij: Vector2i) -> Vector2i:
	var maat := root.get_visible_rect().size
	for r in 12:
		for dy in range(-r, r + 1):
			for dx in range(-r, r + 1):
				if maxi(absi(dx), absi(dy)) != r:
					continue
				var t := bij + Vector2i(dx, dy)
				var p := bm._plan_op(t)
				var s := _scherm(t)
				if p != null and w.kan_bouwen(p) and Rect2(maat * 0.2, maat * 0.6).has_point(s):
					return t
	return Vector2i(-1, -1)


func _vrije_weg(bij: Vector2i) -> Vector2i:
	for r in 12:
		for dy in range(-r, r + 1):
			for dx in range(-r, r + 1):
				var t := bij + Vector2i(dx, dy)
				var ok := true
				for k in 5:
					if BouwRij.status(w, &"weg", t + Vector2i(k, 0)) != BouwRij.KAN:
						ok = false
				if ok:
					return t
	return bij


func _scherm(t: Vector2i) -> Vector2:
	return cam.unproject_position(Vector3((t.x + 0.5) * w.tegel_m, Bouwmenu.GROND_Y, (t.y + 0.5) * w.tegel_m))


func _scherm_tegel_af(t: Vector2i, pos: Vector2) -> int:
	var u := bm.bestuur.tegel_onder(pos)
	return maxi(absi(u.x - t.x), absi(u.y - t.y))


func _druk(pos: Vector2, idx: int, aan: bool) -> void:
	var e := InputEventScreenTouch.new()
	e.index = idx
	e.position = pos
	e.pressed = aan
	root.push_input(e)


func _drag(pos: Vector2, idx: int) -> void:
	var e := InputEventScreenDrag.new()
	e.index = idx
	e.position = pos
	root.push_input(e)


func _tik(pos: Vector2, idx: int) -> void:
	_druk(pos, idx, true)
	_druk(pos, idx, false)


func _sleep(van: Vector2, naar: Vector2, idx: int) -> void:
	_druk(van, idx, true)
	for i in range(1, 9):
		_drag(van.lerp(naar, i / 8.0), idx)
	_druk(naar, idx, false)


func _muis(pos: Vector2, aan: bool) -> void:
	var e := InputEventMouseButton.new()
	e.button_index = MOUSE_BUTTON_LEFT
	e.pressed = aan
	e.position = pos
	e.device = InputEvent.DEVICE_ID_EMULATION
	root.push_input(e)


func _check(ok: bool, wat: String) -> void:
	print(("  ok   " if ok else "  FOUT ") + wat)
	if not ok:
		fouten += 1
