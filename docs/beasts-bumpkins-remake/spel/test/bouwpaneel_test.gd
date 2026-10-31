extends SceneTree
## Headless test bouwpaneel variant A (view/bouwmenu.gd, besluit gebruiker 2026-10-31):
## godot --headless --path . --script res://test/bouwpaneel_test.gd
## Pc (liggend: rij onderin, lettertoetsen) en touch (staand en liggend: hamerknop, paneel): vier tabbladen met de goede
## tegels, ikonen geladen, op slot (reden "na Loods" / "missie 3") en te duur, met melding in plaats van bouwmodus;
## kiezen sluit het paneel en zet de ghost; weg op touch: Bouwen toont aantal x prijs; tegels >= 48 dp, staand 3 breed.

var fouten := 0


func _initialize() -> void:
	process_frame.connect(_start, CONNECT_ONE_SHOT)


func _start() -> void:
	Hud.cfg_pad = ""
	await _ronde(false, Vector2i(1920, 1080))
	await _ronde(true, Vector2i(1080, 2400))
	await _ronde(true, Vector2i(2400, 1080))
	print("---- ", "ALLES OK" if fouten == 0 else "%d FOUTEN" % fouten)
	quit(1 if fouten > 0 else 0)


func _ronde(touch: bool, maat: Vector2i) -> void:
	Bouwmenu.touch = touch
	root.size = maat
	var tag := "%s %dx%d" % ["touch" if touch else "pc", maat.x, maat.y]
	var w := Wereld.new()
	w.laad("", 1)
	w.kas = 1000
	var bak := Node.new()
	root.add_child(bak)
	var wereld3d := Node3D.new()
	bak.add_child(wereld3d)
	var cam := Camera3D.new()
	cam.set_script(load("res://rts_camera.gd"))
	wereld3d.add_child(cam)
	cam.make_current()
	var m := w.tegel_m
	cam.zet_direct(Vector3((w.kampvuur.x + 0.5) * m, 0, (w.kampvuur.y + 0.5) * m), 0.6, deg_to_rad(40), 24.0)
	var b := Bestuur.new()
	b.w = w
	b.cam = cam
	bak.add_child(b)
	var bm := Bouwmenu.new()
	bak.add_child(bm)
	bm.bouw(w, b, wereld3d)
	var meldingen: Array[String] = []
	bm.melding.connect(func(t: String) -> void: meldingen.append(t))
	await _frames(2)

	# tabbladen en tegels
	_check(bm.tab_knoppen.size() == 4, "%s: vier tabbladen" % tag)
	var verwacht := {"wonen": [&"hut", &"put"], "voedsel": [&"kippenhok", &"akker", &"molen", &"melkerij"],
		"gilden": [&"gereedschapsloods", &"voetvolkgilde"], "wegen": [&"weg", &"hek", &"poort"]}
	for k: String in verwacht:
		bm.zet_tab(k)
		var zicht: Array = []
		for s in bm.knoppen:
			if (bm.knoppen[s] as Control).visible:
				zicht.append(s)
		_check(zicht == verwacht[k], "%s: tabblad %s = %s (%s)" % [tag, k, verwacht[k], zicht])
		_check((bm.tab_knoppen[k] as Button).button_pressed, "%s: tabblad %s ingedrukt" % [tag, k])
	var ikonen := 0
	for s in bm.knoppen:
		ikonen += int((bm.knoppen[s] as Bouwmenu.BouwTegel).ikoon != null)
	_check(ikonen == bm.knoppen.size(), "%s: alle ikonen geladen (%d/%d)" % [tag, ikonen, bm.knoppen.size()])

	# staten: missie 1 zonder loods
	await _frames(1)
	bm._werk_tegels()
	var st: Callable = func(s: StringName) -> Bouwmenu.BouwTegel: return bm.knoppen[s]
	_check(st.call(&"molen").staat == Bouwmenu.BouwTegel.SLOT and st.call(&"molen").reden == "na Loods", "%s: molen op slot, na Loods" % tag)
	_check(st.call(&"melkerij").reden == "na Molen", "%s: melkerij na Molen" % tag)
	_check(st.call(&"put").staat == Bouwmenu.BouwTegel.SLOT and st.call(&"put").reden == "missie 3", "%s: put op slot, missie 3" % tag)
	_check(st.call(&"hut").staat == Bouwmenu.BouwTegel.KAN, "%s: hut kan (kas 1000)" % tag)
	w.kas = 250
	bm._werk_tegels()
	_check(st.call(&"hut").staat == Bouwmenu.BouwTegel.DUUR and st.call(&"kippenhok").staat == Bouwmenu.BouwTegel.KAN,
		"%s: kas 250: hut te duur, kippenhok kan" % tag)
	bm.kies_tegel(&"hut")
	_check(not bm.actief and meldingen.size() == 1 and meldingen[-1] == "Hut: te weinig goud, nog 50", "%s: te duur = melding %s" % [tag, meldingen])
	bm.kies_tegel(&"molen")
	_check(not bm.actief and meldingen[-1] == "Molen: eerst een Loods bouwen", "%s: op slot = melding (%s)" % [tag, meldingen[-1]])
	bm.kies_tegel(&"put")
	_check(not bm.actief and meldingen[-1] == "Put: pas vanaf missie 3", "%s: missie 3 = melding (%s)" % [tag, meldingen[-1]])
	w.kas = 1000

	if touch:
		var dp := Scherm.dp()
		_check((bm.knoppen[&"hut"] as Control).size.x >= 48.0 * dp, "%s: tegel >= 48 dp (%d px, dp %.2f)" % [tag, (bm.knoppen[&"hut"] as Control).size.x, dp])
		_check(bm.knop_hamer.visible and not bm.paneel.visible, "%s: hamer zichtbaar, paneel dicht" % tag)
		bm.knop_hamer.pressed.emit()
		await _frames(2)
		_check(bm.paneel.visible and not bm.knop_hamer.visible, "%s: hamer opent het paneel" % tag)
		if maat.y > maat.x:
			_check(bm.rooster.columns == 3, "%s: staand 3 tegels breed" % tag)
		var vp := Rect2(Vector2.ZERO, Vector2(maat)).grow(1.0)
		_check(vp.encloses(bm.paneel.get_global_rect()), "%s: paneel in beeld %s" % [tag, bm.paneel.get_global_rect()])
		bm.zet_tab("wonen")
		(bm.knoppen[&"hut"] as Button).pressed.emit()
		await _frames(3)
		_check(bm.actief and bm.soort == &"hut" and not bm.paneel.visible and bm.knop_bouw.visible, "%s: hut gekozen: paneel dicht, Bouwen-balk" % tag)
		_check(bm.ghost.visible or (bm._gmodel != null and bm._gmodel.visible), "%s: ghost staat" % tag)
		bm.knop_stop.pressed.emit()
		await _frames(1)
		_check(not bm.actief and bm.knop_hamer.visible, "%s: Annuleer, hamer terug" % tag)
		# weg: Bouwen toont aantal x prijs
		bm.kies_tegel(&"weg")
		var t0 := w.kampvuur + Vector2i(3, 3)
		bm._t_tegel = t0
		bm._t_eind = t0 + Vector2i(4, 0)
		await _frames(2)
		var n := bm._t_st.count(BouwRij.KAN)
		_check(n > 0 and bm.knop_bouw.text == "%d x %d" % [n, w.prijs(&"weg")], "%s: weg: '%s' (%d tegels)" % [tag, bm.knop_bouw.text, n])
		bm.zet_actief(false)
	else:
		_check(bm.paneel.visible and not bm.knop_hamer.visible, "%s: rij onderin altijd open, geen hamer" % tag)
		_check(st.call(&"hut").pc and st.call(&"hut").toets == "B" and st.call(&"molen").toets == "Z", "%s: lettertoetsen B en Z (molen)" % tag)
		var r := bm.paneel.get_global_rect()
		_check(r.end.y <= maat.y and r.position.y > maat.y * 0.6 and absf(r.get_center().x - maat.x * 0.5) < 2.0, "%s: rij onderin het midden %s" % [tag, r])
		bm.zet_tab("wonen")
		_toets(bm, KEY_G)        # akker, op slot
		_check(not bm.actief and meldingen[-1] == "Akker: eerst een Loods bouwen", "%s: G = akker op slot" % tag)
		w.alles_open = true
		_toets(bm, KEY_G)
		await _frames(2)
		_check(bm.actief and bm.soort == &"akker" and bm.tab == "voedsel", "%s: G kiest akker en opent Voedsel" % tag)
		_check(st.call(&"akker").aan, "%s: tegel akker gemarkeerd" % tag)
		_toets(bm, KEY_G)
		_check(not bm.actief, "%s: nog eens G = uit" % tag)
		(bm.knoppen[&"kippenhok"] as Button).pressed.emit()
		await _frames(3)
		_check(bm.actief and bm.soort == &"kippenhok" and bm.paneel.visible, "%s: klik kippenhok: bouwmodus, rij blijft" % tag)
		_check(bm.ghost.visible or (bm._gmodel != null and bm._gmodel.visible) or bm._wijzer.x < 0, "%s: ghost (of nog geen wijzer)" % tag)
		bm.zet_actief(false)
	bak.queue_free()
	await _frames(2)


func _toets(bm: Bouwmenu, k: Key) -> void:
	var e := InputEventKey.new()
	e.keycode = k
	e.pressed = true
	bm._unhandled_input(e)


func _frames(n: int) -> void:
	for i in n:
		await process_frame


func _check(ok: bool, wat: String) -> void:
	if ok:
		print("  ok   ", wat)
	else:
		fouten += 1
		print("  FOUT ", wat)
