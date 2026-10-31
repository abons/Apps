extends SceneTree
## Test start- en pauzemenu (view/startmenu.gd, view/pauzemenu.gd, main.gd), headless:
## godot --headless --path . --script res://test/menu_test.gd
## Met een venster en `-- --frames` (zonder --headless) ook frames naar out/menu/:
## godot --path . --script res://test/menu_test.gd -- --frames
## Loopt de echte hoofdscène door: startmenu (1-3 speelbaar, 4-30 vaal) -> missie 2 -> menuknop (klik) = pauze, sim stil
## -> Esc = hervat -> Esc = pauze -> Missie opnieuw (nieuwe Wereld, de oude is weg, evenveel nodes) -> gewonnen ->
## Volgende missie (3) -> Andere missie -> startmenu met Doorgaan en "gewonnen" bij 2 -> missie 1. Indeling op 1600x900,
## 2400x1080 en 1080x2400, pc en touch: start- en pauzemenu in beeld, knoppen op touch >= 48 dp, tekst >= 16 dp.

var fouten := 0
var frames := false
const PAD := "user://menu_test_voortgang.cfg"
const MATEN := [Vector2i(1600, 900), Vector2i(2400, 1080), Vector2i(1080, 2400)]


func _initialize() -> void:
	frames = OS.get_cmdline_user_args().has("--frames")
	process_frame.connect(_start, CONNECT_ONE_SHOT)


func _start() -> void:
	Hud.cfg_pad = ""
	DirAccess.remove_absolute(ProjectSettings.globalize_path(PAD))
	Startmenu.voortgang_pad = PAD
	if frames:
		DirAccess.make_dir_recursive_absolute(ProjectSettings.globalize_path("res://out/menu"))
	_maat(Vector2i(1600, 900))
	Bouwmenu.touch = false
	change_scene_to_file("res://main.tscn")
	await _frames(3)
	var sm := _startmenu()
	_check(sm != null and (current_scene as Node).get("w") == null, "zonder --missie: startmenu, geen wereld")
	if sm == null:
		return _klaar()
	for nr in [1, 2, 3]:
		_check(sm.rijen.has(nr) and not (sm.rijen[nr] as Button).disabled, "missie %d speelbaar" % nr)
	var vaal := range(4, 31).filter(func(n: int) -> bool: return sm.rijen.has(n) and (sm.rijen[n] as Button).disabled)
	_check(vaal.size() == 27, "missie 4-30 vaal (%d)" % vaal.size())
	_check(not sm.knop_door.visible, "nog geen Doorgaan zonder voortgang")
	_check(Startmenu.titel(2) == "Terug op het vasteland" and Startmenu.titel(7) == "Oorlogskas", "titels: briefing of campagne.json")
	await _indeling_start(sm, "pc", "start")

	# missie 2 kiezen: de scène laadt opnieuw met de briefing als laadscherm
	(sm.rijen[2] as Button).pressed.emit()
	var m := await _wacht_missie(2)
	if m == null:
		return _klaar()
	var hud: Hud = m.hud
	_check(hud.brief.visible and m.w.gepauzeerd, "missie 2: briefing open, sim op pauze")
	if frames:
		await _opname("missie2_briefing_pc_1600x900")
	hud.brief.sluit()
	await _frames(2)
	_check(not m.w.gepauzeerd, "briefing dicht: sim loopt")
	_check(Startmenu.laatste_missie() == 2, "laatst gespeeld = 2 bewaard")
	if frames:
		await _opname("hud_menuknop_pc_1600x900")

	# menuknop met een echte klik
	var pm: Pauzemenu = m.pauzemenu
	_klik(_midden(hud.menu_knop))
	await _frames(2)
	_check(pm.open_nu and pm.visible and m.w.gepauzeerd and not m.cam.invoer_aan, "menuknop: pauzemenu open, sim stil, camera uit")
	_check(pm.knoppen.has("hervat") and pm.knoppen.has("opnieuw") and pm.knoppen.has("andere") and pm.knoppen.has("afsluiten"), "pauze: Hervatten, Missie opnieuw, Andere missie, Afsluiten")
	var tik: int = m.w.tik_nr
	await _frames(10)
	_check(m.w.tik_nr == tik, "pauze: de sim tikt niet")
	_toets(KEY_SPACE)
	await _frames(1)
	_check(m.w.gepauzeerd and pm.open_nu, "Spatie doet niets onder het menu")
	await _indeling_pauze(pm, "pc", "pauze")
	_toets(KEY_ESCAPE)
	await _frames(2)
	_check(not pm.open_nu and not pm.visible and not m.w.gepauzeerd and m.cam.invoer_aan, "Esc: hervat, sim en camera weer aan")
	m.bouwmenu.kies(&"hut")
	await _frames(1)
	_toets(KEY_ESCAPE)
	await _frames(1)
	_check(not m.bouwmenu.actief and not pm.open_nu, "Esc in de bouwmodus: alleen de bouwmodus uit")
	_toets(KEY_ESCAPE)
	await _frames(2)
	_check(pm.open_nu, "Esc: pauzemenu open")

	# Missie opnieuw: alles nieuw (een nieuwe Wereld, de oude vrijgegeven), evenveel nodes
	m.w.kas += 1234
	var oud: WeakRef = weakref(m.w)
	var nodes := Performance.get_monitor(Performance.OBJECT_NODE_COUNT)
	pm.knoppen["opnieuw"].pressed.emit()
	m = await _wacht_missie(2)
	if m == null:
		return _klaar()
	await _frames(5)
	_check(oud.get_ref() == null, "opnieuw: de oude Wereld is vrijgegeven")
	_check(m.w.kas == int(m.w.missie.get("start_kas", -1)), "opnieuw: kas terug op de start (%d)" % m.w.kas)
	var nodes2 := Performance.get_monitor(Performance.OBJECT_NODE_COUNT)
	_check(absf(nodes2 - nodes) <= 20.0, "opnieuw: evenveel nodes (%d -> %d)" % [nodes, nodes2])
	m.hud.brief.sluit()

	# gewonnen: einde-menu met Volgende missie
	m._missie_einde("gewonnen")
	await create_timer(2.3).timeout
	pm = m.pauzemenu
	_check(pm.open_nu and pm.knoppen.has("volgende") and m.w.gepauzeerd, "gewonnen: einde-menu met Volgende missie, sim stil")
	_check(Startmenu.gewonnen(2), "gewonnen bewaard")
	if frames:
		await _opname("einde_gewonnen_pc_1600x900")
	await _indeling_pauze(pm, "pc", "einde")
	pm.knoppen["volgende"].pressed.emit()
	m = await _wacht_missie(3)
	if m == null:
		return _klaar()
	m.hud.brief.sluit()
	m.pauzemenu.open_einde("gewonnen")
	_check(not m.pauzemenu.knoppen.has("volgende") and m.pauzemenu.sub.text.contains("nog niet gebouwd"), "missie 3 gewonnen: geen volgende (4 is er nog niet)")
	m.pauzemenu.open_einde("verloren")
	_check(m.pauzemenu.knoppen.has("opnieuw") and m.pauzemenu.knoppen.size() == 3, "verloren: Opnieuw, Andere missie, Bekijken")

	# Andere missie: terug naar het startmenu, met Doorgaan (3) en "gewonnen" bij 2
	m.pauzemenu.knoppen["andere"].pressed.emit()
	await _frames(4)
	sm = _startmenu()
	_check(sm != null and (current_scene as Node).get("w") == null, "Andere missie: startmenu, geen wereld")
	if sm == null:
		return _klaar()
	_check(sm.knop_door.visible and sm.knop_door.text.contains("3"), "Doorgaan: missie 3 (%s)" % sm.knop_door.text)
	_check(_tekst(sm.rijen[2]).contains("gewonnen") and not _tekst(sm.rijen[1]).contains("gewonnen"), "gewonnen bij missie 2, niet bij 1")
	if frames:
		await _opname("startmenu_doorgaan_pc_1600x900")
	(sm.rijen[1] as Button).pressed.emit()
	m = await _wacht_missie(1)
	if m == null:
		return _klaar()

	# touch: startmenu en pauzemenu op alle maten
	Bouwmenu.touch = true
	m.hud.brief.sluit()
	m.pauzemenu.open()
	m.pauzemenu.kies("andere")
	await _frames(4)
	sm = _startmenu()
	if sm == null:
		return _klaar()
	await _indeling_start(sm, "touch", "start")
	(sm.rijen[1] as Button).pressed.emit()
	m = await _wacht_missie(1)
	if m == null:
		return _klaar()
	m.hud.brief.sluit()
	await _frames(2)
	_check(m.hud.menu_knop.size.y >= Bouwmenu.touch_knop_h() - 0.5, "touch: menuknop >= 48 dp (%d px)" % m.hud.menu_knop.size.y)
	m.pauzemenu.open()
	await _indeling_pauze(m.pauzemenu, "touch", "pauze")
	m.pauzemenu.kies("hervat")
	if frames:
		_maat(Vector2i(1080, 2400))
		await _frames(4)
		await _opname("hud_menuknop_touch_1080x2400")
	_klaar()


func _klaar() -> void:
	DirAccess.remove_absolute(ProjectSettings.globalize_path(PAD))
	print("---- ", "ALLES OK" if fouten == 0 else "%d FOUTEN" % fouten)
	quit(1 if fouten > 0 else 0)


## Wacht tot main.gd missie `nr` helemaal heeft opgebouwd (laadscherm weg, _process aan).
func _wacht_missie(nr: int) -> Node:
	for i in 4000:
		await process_frame
		var m := current_scene
		if m != null and m.get("pauzemenu") != null and m.get("w") != null and m.is_processing():
			_check(m.w.missie_nr == nr, "missie %d geladen" % nr)
			await _frames(2)
			return m
	_check(false, "missie %d laadt niet" % nr)
	return null


func _startmenu() -> Startmenu:
	var m := current_scene
	return m.get("startmenu") if m != null else null


func _indeling_start(sm: Startmenu, naam: String, wat: String) -> void:
	for maat in MATEN:
		_maat(maat)
		await _frames(3)
		var tag := "%s %s %dx%d" % [naam, wat, maat.x, maat.y]
		_binnen(sm.paneel, tag + ": perkament")
		for c: Control in [sm.knop_door, sm.knop_uit, sm.scroll]:
			if c.is_visible_in_tree():
				_binnen(c, tag + ": " + (c.name if c != sm.scroll else "lijst"))
		var r: Button = sm.rijen[1]
		_binnen(r, tag + ": eerste regel")
		if Bouwmenu.touch:
			var dp := Scherm.dp()
			_check(_rect(r).size.y >= 48.0 * dp - 0.5, "%s: regel >= 48 dp (%.0f px, dp %.2f)" % [tag, _rect(r).size.y, dp])
			_check(_kleinste_tekst(sm.paneel) >= 16.0 * dp - 0.5, "%s: tekst >= 16 dp" % tag)
		if frames:
			await _opname("startmenu_%s_%dx%d" % [naam, maat.x, maat.y])
	_maat(Vector2i(1600, 900))
	await _frames(2)


func _indeling_pauze(pm: Pauzemenu, naam: String, wat: String) -> void:
	for maat in MATEN:
		_maat(maat)
		await _frames(3)
		var tag := "%s %s %dx%d" % [naam, wat, maat.x, maat.y]
		_binnen(pm.paneel, tag + ": perkament")
		for a in pm.knoppen:
			_binnen(pm.knoppen[a], "%s: knop %s" % [tag, a])
			if Bouwmenu.touch:
				_check(_rect(pm.knoppen[a]).size.y >= 48.0 * Scherm.dp() - 0.5, "%s: knop %s >= 48 dp (%.0f px, paneel %s)" % [tag, a, _rect(pm.knoppen[a]).size.y, _rect(pm.paneel)])
		if Bouwmenu.touch:
			_check(_kleinste_tekst(pm.paneel) >= 16.0 * Scherm.dp() - 0.5, "%s: tekst >= 16 dp" % tag)
		if frames:
			await _opname("%s_%s_%dx%d" % [wat, naam, maat.x, maat.y])
	_maat(Vector2i(1600, 900))
	await _frames(2)


## Kleinste lettergrootte op het scherm (px x schaal) van de labels en knoppen in `c`.
func _kleinste_tekst(c: Control) -> float:
	var k := 1e9
	for n in _alle(c):
		if (n is Label or n is Button) and (n as Control).is_visible_in_tree() and (n as Control).get("text") != "":
			k = minf(k, (n as Control).get_theme_font_size("font_size") * (n as Control).get_global_transform_with_canvas().get_scale().y)
	return k


func _alle(n: Node) -> Array:
	var uit: Array = []
	for k in n.get_children():
		uit.append(k)
		uit.append_array(_alle(k))
	return uit


func _tekst(b: Button) -> String:
	var t := ""
	for n in _alle(b):
		if n is Label:
			t += (n as Label).text + " "
	return t


## Viewport op maat (zoals Scherm.zet_venster: stretch viewport, met venster geschaald op de monitor).
func _maat(maat: Vector2i) -> void:
	root.content_scale_mode = Window.CONTENT_SCALE_MODE_VIEWPORT
	root.content_scale_aspect = Window.CONTENT_SCALE_ASPECT_KEEP
	root.content_scale_size = maat
	if DisplayServer.get_name() == "headless":
		root.size = maat
	else:
		var scherm := Vector2(DisplayServer.screen_get_usable_rect().size) * 0.9
		var f := minf(1.0, minf(scherm.x / maat.x, scherm.y / maat.y))
		root.size = Vector2i(Vector2(maat) * f)


func _opname(naam: String) -> void:
	await _frames(2)
	await RenderingServer.frame_post_draw
	var img := root.get_texture().get_image()
	var pad := "res://out/menu/%s.png" % naam
	img.save_png(ProjectSettings.globalize_path(pad))
	print("  frame ", pad, " ", img.get_size())


func _toets(k: Key) -> void:
	for p in [true, false]:
		var e := InputEventKey.new()
		e.keycode = k
		e.physical_keycode = k
		e.pressed = p
		Input.parse_input_event(e)


func _klik(pos: Vector2) -> void:
	for p in [true, false]:
		var e := InputEventMouseButton.new()
		e.button_index = MOUSE_BUTTON_LEFT
		e.pressed = p
		e.position = pos
		e.global_position = pos
		root.push_input(e)


func _midden(c: Control) -> Vector2:
	return _rect(c).get_center()


func _frames(n: int) -> void:
	for i in n:
		await process_frame


func _rect(c: Control) -> Rect2:
	var t := c.get_global_transform_with_canvas()
	return Rect2(t.origin, c.size * t.get_scale())


func _binnen(c: Control, wat: String) -> void:
	var vp := Rect2(Vector2.ZERO, root.get_visible_rect().size).grow(1.0)
	_check(vp.encloses(_rect(c)), "%s binnen beeld (%s)" % [wat, _rect(c)])


func _check(ok: bool, wat: String) -> void:
	if ok:
		print("  ok   ", wat)
	else:
		fouten += 1
		print("  FOUT ", wat)
