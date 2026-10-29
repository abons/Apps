class_name Bestuur
extends Node
## Muisbesturing (besluit gebruiker 2026-10-29): selecteren met een kader of een klik op een unit,
## linkerklik op de grond = loopbevel, rechterklik = selectie weg. Rechts slepen draait de camera (rts_camera.gd).
## Fight- en werkbevelen bestaan in Wereld.geef_bevel (alleen volwassenen); er is nog geen invoer voor.

const KLIK_DREMPEL := 6.0       # px: minder slepen telt als klik
const PICK_PX := 30.0           # px rond een unit waarbinnen een klik hem kiest
const GROND_Y := 0.25           # vlak waar de muisstraal de grond raakt

var w: Wereld
var view: WereldView
var cam: Camera3D
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
		if _voor_camera(d.id) and r.has_point(_scherm(d.id)) and not d.id in gekozen:
			gekozen.append(d.id)
	view.gekozen = gekozen


## Klik: op een unit = die kiezen; op de grond met een selectie = loopbevel.
func klik(pos: Vector2, toevoegen := false) -> void:
	var beste := -1
	var bd := PICK_PX
	for d in w.dorpelingen:
		if not _voor_camera(d.id):
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
	if gekozen.is_empty():
		return
	var t := tegel_onder(pos)
	if t.x >= 0:
		var p := w.plan_op(t)
		if p != null and w.geef_bouwbevel(gekozen, p) > 0:
			view.markeer(p.tegel)
			return
		geef_loopbevel(t)


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
