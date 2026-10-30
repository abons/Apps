extends SceneTree
## Headless test minikaart (view/minikaart.gd): godot --headless --path . --script res://test/minikaart_test.gd
## Omrekenen tegel <-> venster heen en terug; klik = camerabrandpunt op de tegel onder de klik; slepen = camera schuift
## mee terwijl de kaart stilstaat; klik buiten het raster blijft binnen de cameragrens; mist-textuur volgt `versie`.

var fouten := 0


func _initialize() -> void:
	var w := Wereld.new()
	_check(w.laad("", 1), "missie 1 laadt")
	var cam := Camera3D.new()
	cam.set_script(load("res://rts_camera.gd"))
	root.add_child(cam)
	var m := w.tegel_m
	cam.grens = Rect2(-12, -12, w.raster.kolommen * m + 24, w.raster.rijen * m + 24)
	cam.doel_focus = Vector3((w.kampvuur.x + 0.5) * m, 0, (w.kampvuur.y + 0.5) * m)   # zet_direct wil een boom (look_at)
	cam.focus = cam.doel_focus
	var mk := Minikaart.new()
	root.add_child(mk)
	mk.bouw(w, cam, null)
	_check(mk.midden.distance_to(Vector2(w.kampvuur) + Vector2(0.5, 0.5)) < 0.01, "midden = camerabrandpunt (%s)" % mk.midden)
	_check(mk.naar_venster(mk.midden).distance_to(Minikaart.MAAT * 0.5) < 0.01, "brandpunt in het midden van het venster")
	# isometrisch: x op = rechtsonder, y op = linksonder
	var o := mk.naar_venster(mk.midden)
	var px := mk.naar_venster(mk.midden + Vector2(1, 0)) - o
	var py := mk.naar_venster(mk.midden + Vector2(0, 1)) - o
	_check(px.x > 0 and px.y > 0 and py.x < 0 and py.y > 0 and is_equal_approx(px.x, 2.0 * px.y), "ruit 2:1 (x %s, y %s)" % [px, py])
	for t in [Vector2(3.5, -7.25), Vector2(-20, 11), Vector2(0, 0)]:
		var tt: Vector2 = mk.midden + t
		_check(mk.naar_tegel(mk.naar_venster(tt)).distance_to(tt) < 1e-3, "heen en terug %s" % tt)

	# klik op een tegel 10 naar rechts, 5 omlaag: de camera springt erheen (direct, geen naglijden)
	var doel := Vector2(w.kampvuur) + Vector2(10.5, 5.5)
	var plek := mk.naar_venster(doel) + Vector2(Minikaart.RAND, Minikaart.RAND)
	mk._gui_input(_knop(plek, true))
	var f := Vector2(cam.focus.x, cam.focus.z) / m
	_check(f.distance_to(doel) < 0.01, "klik: brandpunt op tegel %s (is %s)" % [doel, f])
	_check(Vector2(cam.doel_focus.x, cam.doel_focus.z).distance_to(Vector2(cam.focus.x, cam.focus.z)) < 1e-4, "klik: doel = brandpunt (springen)")
	var midden_vast := mk.midden
	# slepen met de knop ingedrukt: camera volgt, het venster staat stil
	var doel2 := doel + Vector2(-6, 3)
	var sleep := InputEventMouseMotion.new()
	sleep.position = mk.naar_venster(doel2) + Vector2(Minikaart.RAND, Minikaart.RAND)
	sleep.button_mask = MOUSE_BUTTON_MASK_LEFT
	mk._gui_input(sleep)
	f = Vector2(cam.focus.x, cam.focus.z) / m
	_check(f.distance_to(doel2) < 0.01, "slepen: brandpunt volgt naar %s (is %s)" % [doel2, f])
	mk._process(0.1)
	_check(mk.midden == midden_vast, "slepen: venster staat stil zolang de knop is ingedrukt")
	mk._gui_input(_knop(sleep.position, false))
	for i in 30:
		mk._process(0.1)
	_check(mk.midden.distance_to(doel2) < 0.05, "losgelaten: venster schuift naar het brandpunt (%s)" % mk.midden)
	# zonder knop: bewegen doet niets
	var los := InputEventMouseMotion.new()
	los.position = Vector2(5, 5)
	mk._gui_input(los)
	f = Vector2(cam.focus.x, cam.focus.z) / m
	_check(f.distance_to(doel2) < 0.01, "bewegen zonder knop verplaatst de camera niet")

	# ver buiten het raster klikken: binnen de grens
	mk.midden = Vector2(-60, -60)
	mk._gui_input(_knop(Vector2(Minikaart.RAND, Minikaart.RAND), true))
	mk._gui_input(_knop(Vector2(Minikaart.RAND, Minikaart.RAND), false))
	_check(cam.focus.x >= cam.grens.position.x - 1e-3 and cam.focus.z >= cam.grens.position.y - 1e-3, "klik buiten het raster: brandpunt binnen de grens (%s)" % cam.focus)

	# mist: nieuw verkend gebied = textuur bijwerken
	var v := w.mist.versie
	w.mist.onthul(w.kampvuur + Vector2i(20, -4), 3.0)
	_check(w.mist.versie != v, "onthullen verhoogt de versie")
	mk._process(0.016)
	_check(mk._versie == w.mist.versie, "minikaart heeft de nieuwe mistversie")
	_check(mk._mist_img.get_pixel(w.kampvuur.x + 20, w.kampvuur.y - 4).r > 0.0, "verkende tegel staat in de misttextuur")
	_check(mk._mist_img.get_pixel(0, 0).r == 0.0, "hoek (0,0) zwart in de misttextuur")
	print("---- ", "ALLES OK" if fouten == 0 else "%d FOUT(EN)" % fouten)
	quit(0 if fouten == 0 else 1)


func _knop(p: Vector2, druk: bool) -> InputEventMouseButton:
	var e := InputEventMouseButton.new()
	e.button_index = MOUSE_BUTTON_LEFT
	e.pressed = druk
	e.position = p
	return e


func _check(ok: bool, wat: String) -> void:
	print(("  ok   " if ok else "  FOUT ") + wat)
	if not ok:
		fouten += 1
