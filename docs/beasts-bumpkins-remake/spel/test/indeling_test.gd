extends SceneTree
## Headless test schermindeling (view/scherm.gd, hud.gd, bouwmenu.gd, brief.gd, prijzen.gd):
## godot --headless --path . --script res://test/indeling_test.gd
## Pc en touch, elk op 2400x1080 (liggend) en 1080x2400 (staand), gewisseld tijdens het spel (size_changed): geen
## zichtbare Control buiten beeld, en de vaste delen (minikaart, munt-icoon, stand/tellers, bouwknoppen, lade-knop,
## hint, touchbalk) overlappen elkaar niet; ook met de bouwmodus aan en (staand) de lade open. Brief en prijzenscherm
## passen in beeld. Touch: de tellers zijn >= 16 dp (Scherm.dp), de stand-tekstregels zijn weg.
## Pc (2026-10-31): ook op 1600x900; standaard alleen de tellerrij en de knop "? Toetsen", en met de details (Tab) en de
## sneltoetsuitleg (F1) uitgeklapt, apart en samen, weer niets buiten beeld of over elkaar. De menuknop (2026-10-31) telt
## mee als vast deel. Start- en pauzemenu: test/menu_test.gd.
## Portret (2026-10-31, view/portret.gd): met een gekozen dorpeling rechtsonder in beeld, zonder overlap; in de
## paneelmodus weg in de bouwmodus en met het paneel open.
## Bouwmenu variant A (2026-10-31): pc liggend de rij onderin (paneel altijd open, geen hamer); touch en staand de
## hamerknop rechtsonder die het paneel opent, een keuze sluit het. Paneel, hamer en hint/Draai/Stop tellen mee.

var fouten := 0
var cam: Camera3D


func _initialize() -> void:
	process_frame.connect(_start, CONNECT_ONE_SHOT)


func _start() -> void:
	Hud.cfg_pad = ""      # niet de bewaarde stand van deze pc lezen of overschrijven
	for touch in [false, true]:
		await _ronde(touch)
	print("---- ", "ALLES OK" if fouten == 0 else "%d FOUTEN" % fouten)
	quit(1 if fouten > 0 else 0)


func _ronde(touch: bool) -> void:
	Bouwmenu.touch = touch
	root.size = Vector2i(2400, 1080)
	var w := Wereld.new()
	_check(w.laad("", 1), "missie 1 laadt")
	w.alles_open = true
	w.kas = 100000
	var bak := Node.new()
	root.add_child(bak)
	var wereld3d := Node3D.new()
	bak.add_child(wereld3d)
	cam = Camera3D.new()
	cam.set_script(load("res://rts_camera.gd"))
	wereld3d.add_child(cam)
	cam.make_current()
	var m := w.tegel_m
	cam.zet_direct(Vector3((w.kampvuur.x + 0.5) * m, 0, (w.kampvuur.y + 0.5) * m), 0.6, deg_to_rad(40), 24.0)
	var b := Bestuur.new()
	b.w = w
	b.cam = cam
	bak.add_child(b)
	var hud := Hud.new()
	bak.add_child(hud)
	hud.bouw(w, b)
	b.kader = hud.kader
	var bm := Bouwmenu.new()
	bak.add_child(bm)
	bm.bouw(w, b, wereld3d)
	cam.pan_blokkade = func() -> bool: return bm.actief and not Bouwmenu.touch
	var h := Hints.new().bouw(w)
	hud.zet_hints(h)
	b.gekozen.append(w.dorpelingen[0].id)      # portret rechtsonder
	bm.zet_tab("voedsel")         # het breedste tabblad (4 tegels)

	var naam := "touch" if touch else "pc"
	if touch:
		_check(not hud.stand.visible and hud.tellers != null and hud.tellers.visible, "%s: tekstregels weg, tellers aan" % naam)
		_check(hud.tellers.kas.get_theme_font_size("font_size") >= roundi(16.0 * Scherm.dp()), "%s: tellers >= 16 dp" % naam)
	else:
		_check(not hud.stand.visible and hud.kop.visible and hud.tellers.is_visible_in_tree(), "%s: standaard tellerrij, tekstregels dicht" % naam)
		_check(not hud.hulp.is_visible_in_tree() and hud.knop_hulp.visible, "%s: standaard sneltoetsuitleg dicht, knop zichtbaar" % naam)
		_check(hud.tellers.tempo_ik != null and not hud.tellers.tempo_ik.visible, "%s: geen pauze-icoon bij 1x" % naam)
		_toets(hud, KEY_TAB)
		_check(hud.details_open and hud.stand.visible and hud.label.text.contains("geluk"), "%s: Tab klapt de details uit" % naam)
		_toets(hud, KEY_I)
		_check(not hud.details_open and not hud.stand.visible, "%s: I klapt ze weer in" % naam)
		hud.knop_details.pressed.emit()
		_check(hud.details_open, "%s: het pijltje klapt uit" % naam)
		hud.knop_details.pressed.emit()
		_toets(hud, KEY_F1)
		_check(hud.hulp_open and hud.hulp.is_visible_in_tree(), "%s: F1 opent de sneltoetsuitleg" % naam)
		hud.knop_hulp.pressed.emit()
		_check(not hud.hulp_open and not hud.hulp.is_visible_in_tree(), "%s: de knop sluit hem" % naam)
		w.gepauzeerd = true
		await _frames(1)
		_check(hud.tellers.tempo_ik.visible and not hud.tellers.tempo.visible, "%s: pauze-icoon bij pauze" % naam)
		w.gepauzeerd = false
		w.tempo = 4.0
		await _frames(1)
		_check(not hud.tellers.tempo_ik.visible and hud.tellers.tempo.visible and hud.tellers.tempo.text == "4x", "%s: 4x bij tempo 4" % naam)
		w.tempo = 1.0
	var maten := [Vector2i(2400, 1080), Vector2i(1080, 2400), Vector2i(2400, 1080), Vector2i(1080, 2400)]
	if not touch:
		maten = [Vector2i(1600, 900)] + maten
	for maat in maten:
		root.size = maat
		if b.gekozen.is_empty():      # de bouwmodus wist de selectie
			b.gekozen.append(w.dorpelingen[0].id)
		await _frames(3)
		var tag := "%s %dx%d" % [naam, maat.x, maat.y]
		_check(hud.brief.visible, "%s: briefing open" % tag)
		_binnen(hud.brief, "%s briefing" % tag)
		_check(cam.keep_aspect == (Camera3D.KEEP_WIDTH if maat.y > maat.x else Camera3D.KEEP_HEIGHT), "%s: camera houdt de %s vast" % [tag, "breedte" if maat.y > maat.x else "hoogte"])
		hud.brief.sluit()
		await _frames(2)
		_check(hud.portret.visible, "%s: portret van de gekozen dorpeling" % tag)
		# gewoon, bouwmodus, (staand) lade open; op de pc ingeklapt en uitgeklapt
		_indeling(hud, bm, "%s rust" % tag)
		if not touch:
			await _inklap_standen(hud, bm, "%s rust" % tag)
		bm.kies(&"hut")
		await _frames(2)
		_check(bm.actief, "%s: bouwmodus aan" % tag)
		_indeling(hud, bm, "%s bouwmodus" % tag)
		if not touch:
			await _inklap_standen(hud, bm, "%s bouwmodus" % tag)
		if touch or maat.y > maat.x:
			_check(not bm.knop_hamer.visible and not bm.paneel.visible, "%s: in de bouwmodus geen hamer en geen paneel" % tag)
			bm.zet_actief(false)
			await _frames(2)
			_check(bm.knop_hamer.visible and not bm.paneel.visible, "%s: paneel dicht, hamerknop" % tag)
			if b.gekozen.is_empty():
				b.gekozen.append(w.dorpelingen[0].id)
			await _frames(2)
			_indeling(hud, bm, "%s rust met hamer" % tag)
			bm.knop_hamer.pressed.emit()
			bm.zet_tab("voedsel")
			await _frames(2)
			_check(bm.paneel.visible and bm.paneel_open, "%s: hamer opent het paneel" % tag)
			_indeling(hud, bm, "%s paneel open" % tag)
			_check(not hud.portret.visible, "%s: portret weg bij het open paneel" % tag)
			(bm.knoppen[&"kippenhok"] as Button).pressed.emit()
			await _frames(2)
			_check(bm.soort == &"kippenhok" and bm.actief and not bm.paneel.visible, "%s: keuze in het paneel sluit het" % tag)
		else:
			_check(not bm.knop_hamer.visible and bm.paneel.visible, "%s: rij onderin, geen hamer" % tag)
			_check(bm.kolom.get_global_rect().end.y <= bm.paneel.position.y, "%s: hint/Draai/Stop boven de rij" % tag)
		bm.zet_actief(false)
		hud.prijzen.open()
		await _frames(2)
		_binnen(hud.prijzen._paneel, "%s prijzen" % tag)
		hud.prijzen.sluit()
		# een hint (klein) en de briefing weer open voor de volgende maat
		hud.brief.toon("", "Begin met twee kippenhokken. Kies het kippenhok in het bouwmenu en zet het op vrije grond.")
		await _frames(1)
		_binnen(hud.brief, "%s hint" % tag)
		hud.brief.toon(h.briefing.get("titel", ""), h.briefing.get("tekst", ""), true)
	bak.queue_free()
	await _frames(2)


## Pc: details, sneltoetsuitleg en beide uitgeklapt, telkens de indeling; daarna weer alles dicht.
func _inklap_standen(hud: Hud, bm: Bouwmenu, wat: String) -> void:
	for stand in [[true, false], [false, true], [true, true]]:
		if hud.details_open != stand[0]:
			hud.wissel_details()
		if hud.hulp_open != stand[1]:
			hud.wissel_hulp()
		await _frames(2)
		_indeling(hud, bm, "%s %s" % [wat, "details+uitleg" if stand[0] and stand[1] else ("details" if stand[0] else "uitleg")])
	hud.wissel_details()
	hud.wissel_hulp()
	await _frames(2)


func _toets(hud: Hud, k: Key) -> void:
	var e := InputEventKey.new()
	e.keycode = k
	e.pressed = true
	hud._unhandled_input(e)


func _frames(n: int) -> void:
	for i in n:
		await process_frame


## Rechthoek van een Control op het scherm, met schaal.
func _rect(c: Control) -> Rect2:
	var t := c.get_global_transform_with_canvas()
	return Rect2(t.origin, c.size * t.get_scale())


func _binnen(c: Control, wat: String) -> void:
	var vp := Rect2(Vector2.ZERO, root.get_visible_rect().size).grow(1.0)
	var r := _rect(c)
	_check(vp.encloses(r), "%s binnen beeld (%s)" % [wat, r])


## Alle zichtbare Controls van Hud en Bouwmenu in beeld; de vaste delen zonder overlap.
func _indeling(hud: Hud, bm: Bouwmenu, wat: String) -> void:
	var vp := Rect2(Vector2.ZERO, root.get_visible_rect().size).grow(1.0)
	var buiten: Array = []
	for wortel: Node in [hud, bm]:
		for c in _controls(wortel):
			if c.size.x < 1.0 or c.size.y < 1.0:
				continue
			if not vp.encloses(_rect(c)):
				buiten.append("%s %s" % [c.get_class() if c.name.begins_with("@") else String(c.name), _rect(c)])
	_check(buiten.is_empty(), "%s: alles in beeld %s" % [wat, buiten])
	var delen := {"minikaart": hud.minikaart, "munt": hud.munt_knop, "menu": hud.menu_knop, "stand": hud.kop if hud.kop != null else hud.tellers,
		"details": hud.stand, "toetsen-knop": hud.knop_hulp, "hulpregels": hud.hulp.get_parent(),
		"hamer": bm.knop_hamer, "portret": hud.portret, "paneel": bm.paneel, "hint/draai/stop": bm.rij2, "touchbalk": bm.balk}
	var namen := delen.keys().filter(func(k: String) -> bool:
		var c: Control = delen[k]
		return c != null and c.is_visible_in_tree() and c.size.x >= 1.0 and c.size.y >= 1.0 and _heeft_inhoud(c))
	for i in namen.size():
		for j in range(i + 1, namen.size()):
			var a := _rect(delen[namen[i]])
			var c := _rect(delen[namen[j]])
			_check(not a.intersects(c), "%s: %s en %s overlappen niet (%s, %s)" % [wat, namen[i], namen[j], a, c])


## Een container zonder zichtbare kinderen telt niet mee (rij2 zonder hint en knoppen).
func _heeft_inhoud(c: Control) -> bool:
	if not c is Container:
		return true
	for k in c.get_children():
		if k is Control and (k as Control).visible:
			return true
	return false


func _controls(n: Node) -> Array:
	var uit: Array = []
	for k in n.get_children():
		if k is CanvasItem and not (k as CanvasItem).visible:
			continue
		if k is Control and k.get_script() != load("res://view/kader.gd") and not k is Prijzenscherm and not k is Brief:
			uit.append(k)
		if not k is Prijzenscherm and not k is Brief:
			uit.append_array(_controls(k))
	return uit


func _check(ok: bool, wat: String) -> void:
	if ok:
		print("  ok   ", wat)
	else:
		fouten += 1
		print("  FOUT ", wat)
