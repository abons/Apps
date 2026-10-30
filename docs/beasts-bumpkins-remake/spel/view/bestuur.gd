class_name Bestuur
extends Node
## Muisbesturing (besluit gebruiker 2026-10-29): selecteren met een kader of een klik op een unit,
## linkerklik op de grond = loopbevel, rechterklik = selectie weg. Rechts slepen draait de camera (rts_camera.gd).
## Klik op een poort (met of zonder selectie): open of dicht.
## Klik op een afgebouwd gilde met een selectie (Wereld.GILDEN): loods = bouwer, voetvolkgilde = voetsoldaat (mannen, kas, max 6).
## Klik op een koe met een selectie: de eerste volwassene loopt erheen en claimt haar (nog eens = loslaten).
## Klik op een levende wolf met een selectie: vechtbevel (Wereld.geef_vechtbevel; alleen volwassenen, niet de bouwer),
## ze lopen erheen en gooien stenen (sim/wolf.gd). Werkbevelen hebben nog geen eigen invoer.
## Klik op een voorwerp op de grond (beker, kelk) met een selectie: de dichtste loopt erheen en raapt het op
## (sim/voorwerpen.gd); naar de vlag brengen is daarna een gewoon loopbevel.

const KLIK_DREMPEL := 6.0       # px: minder slepen telt als klik
const PICK_PX := 30.0           # px rond een unit waarbinnen een klik hem kiest
const GROND_Y := 0.25           # vlak waar de muisstraal de grond raakt

var w: Wereld
var view: WereldView
var cam: Camera3D
var voorwerpen: Node3D          # view/voorwerpen_view.gd (grond_pos)
var kader: Control
var gekozen: Array = []
var _links := false
var _start := Vector2.ZERO
var _sleept := false
var _rechts := false
var _rechts_beweging := 0.0


func _unhandled_input(e: InputEvent) -> void:
	if e is InputEventMouseButton:
		if e.button_index == MOUSE_BUTTON_LEFT:
			if e.pressed:
				_links = true
				_start = e.position
				_sleept = false
			elif _links:
				_links = false
				if _sleept:
					kader.zet(Rect2(), false)
					kies_in_rechthoek(Rect2(_start, e.position - _start).abs(), Input.is_key_pressed(KEY_SHIFT))
				else:
					klik(e.position, Input.is_key_pressed(KEY_SHIFT))
				_sleept = false
				cam.rand_pannen = true
		elif e.button_index == MOUSE_BUTTON_RIGHT:
			if e.pressed:
				_rechts = true
				_rechts_beweging = 0.0
			elif _rechts:
				_rechts = false
				if _rechts_beweging < KLIK_DREMPEL:
					wis_selectie()
	elif e is InputEventMouseMotion:
		if _links:
			if not _sleept and e.position.distance_to(_start) > KLIK_DREMPEL:
				_sleept = true
				cam.rand_pannen = false      # geen randpannen midden in een kader
			if _sleept:
				kader.zet(Rect2(_start, e.position - _start).abs(), true)
		if _rechts:
			_rechts_beweging += e.relative.length()


func wis_selectie() -> void:
	gekozen.clear()
	view.gekozen = gekozen


func _scherm(id: int) -> Vector2:
	return cam.unproject_position(view.unit_pos(id) + Vector3(0, 0.9, 0))


func _voor_camera(id: int) -> bool:
	return not cam.is_position_behind(view.unit_pos(id))


func kies_in_rechthoek(r: Rect2, toevoegen := false) -> void:
	if not toevoegen:
		gekozen.clear()
	for d in w.dorpelingen:
		if not d.binnen and _voor_camera(d.id) and r.has_point(_scherm(d.id)) and not d.id in gekozen:
			gekozen.append(d.id)
	view.gekozen = gekozen


## Klik: op een unit = die kiezen; op de grond met een selectie = loopbevel.
func klik(pos: Vector2, toevoegen := false) -> void:
	var beste := -1
	var bd := PICK_PX
	for d in w.dorpelingen:
		if d.binnen or not _voor_camera(d.id):
			continue
		var af := _scherm(d.id).distance_to(pos)
		if af < bd:
			bd = af
			beste = d.id
	if beste >= 0:
		if not toevoegen:
			gekozen.clear()
		if not beste in gekozen:
			gekozen.append(beste)
		view.gekozen = gekozen
		return
	var tp := tegel_onder(pos)
	if tp.x >= 0:
		var poort := w.gebouw_op(tp)
		if poort != null and poort.soort == &"poort":
			w.wissel_poort(poort)
			return
	if gekozen.is_empty():
		return
	var wid := _wolf_onder(pos)          # vechtbevel: de volwassenen (niet de bouwer) gooien stenen
	if wid >= 0 and w.geef_vechtbevel(gekozen, wid) > 0:
		for wf in w.wolven:
			if wf.id == wid:
				view.markeer(wf.tegel())
		return
	var vw := _voorwerp_onder(pos)
	if not vw.is_empty() and Voorwerpen.geef_pakbevel(w, gekozen, vw) > 0:
		view.markeer(Vector2i(vw["x"], vw["y"]))
		return
	var kid := _koe_onder(pos)
	if kid >= 0 and w.geef_claimbevel(gekozen, kid) > 0:
		view.markeer(w.koe(kid).tegel())
		return
	var t := tegel_onder(pos)
	if t.x >= 0:
		var p := w.plan_op(t)
		if p != null and w.geef_bouwbevel(gekozen, p) > 0:
			view.markeer(p.tegel)
			return
		var g := w.gebouw_op(t)
		if g != null and Wereld.GILDEN.has(g.soort) and w.geef_gildebevel(gekozen, g) > 0:
			view.markeer(g.deur_tegel())
			return
		geef_loopbevel(t)


## Levende wolf onder een schermpunt (binnen PICK_PX rond zijn rug), -1 als er geen is.
func _wolf_onder(pos: Vector2) -> int:
	if view.wolven == null:
		return -1
	var beste := -1
	var bd := PICK_PX * 1.4
	for wf in w.wolven:
		var p: Vector3 = view.wolven.wolf_pos(wf.id)
		if not wf.leeft() or p == Vector3.INF or cam.is_position_behind(p):
			continue
		var af := cam.unproject_position(p + Vector3(0, 0.6, 0)).distance_to(pos)
		if af < bd:
			bd = af
			beste = wf.id
	return beste


## Voorwerp op de grond onder een schermpunt (binnen PICK_PX), {} als er geen is.
func _voorwerp_onder(pos: Vector2) -> Dictionary:
	if voorwerpen == null:
		return {}
	var beste := {}
	var bd := PICK_PX
	for ob in Voorwerpen.alle(w):
		var p: Vector3 = voorwerpen.grond_pos(ob)
		if p == Vector3.INF or cam.is_position_behind(p):
			continue
		var af := cam.unproject_position(p + Vector3(0, 0.4, 0)).distance_to(pos)
		if af < bd:
			bd = af
			beste = ob
	return beste


## Koe onder een schermpunt (binnen PICK_PX rond haar rug), -1 als er geen is.
func _koe_onder(pos: Vector2) -> int:
	var beste := -1
	var bd := PICK_PX * 1.4
	for k in w.vee:
		var p := view.koe_pos(k.id)
		if p == Vector3.INF or cam.is_position_behind(p):
			continue
		var af := cam.unproject_position(p + Vector3(0, 0.8, 0)).distance_to(pos)
		if af < bd:
			bd = af
			beste = k.id
	return beste


func geef_loopbevel(t: Vector2i) -> int:
	var n := w.geef_bevel(gekozen, "loop", t)
	if n > 0:
		for id in gekozen:
			var d := w.dorpeling(id)
			if d != null and not d.bevel.is_empty():
				view.markeer(d.bevel["doel"])
	return n


## Tegel onder een schermpunt (muisstraal tegen het grondvlak), (-1,-1) als de straal de grond mist.
func tegel_onder(pos: Vector2) -> Vector2i:
	var o := cam.project_ray_origin(pos)
	var r := cam.project_ray_normal(pos)
	if r.y > -0.001:
		return Vector2i(-1, -1)
	var t := (GROND_Y - o.y) / r.y
	var p := o + r * t
	return Vector2i(int(floor(p.x / w.tegel_m)), int(floor(p.z / w.tegel_m)))
