class_name Bouwmenu
extends Node
## Bouwmenu (stap 5, gameplay.md §7): knop "Hut" of B, ghost volgt de muis over de tegels (groen = kan, rood = kan niet),
## R draait, linkerklik plaatst een Plan in Wereld, rechterklik of Esc stopt. Shift bij het plaatsen houdt de modus aan.
## Een Plan is nog een doorzichtige kist: bouwplaats, werkers en kas (prijs) staan nog niet in de sim.
## Moet NA Bestuur in de boom staan: dan krijgt het de invoer eerst en neemt het de linkerklik van het kiezen over.

const GROND_Y := 0.25
const KLIK_DREMPEL := 6.0
const HOOGTE := 2.4

var w: Wereld
var bestuur: Bestuur
var actief := false
var soort: StringName = &"hut"
var draai := 0
var knop: Button
var ghost: MeshInstance3D
var _rechts_start := Vector2.ZERO
var _rechts := false
var _kisten := {}          ## Plan -> kist


func bouw(wereld: Wereld, b: Bestuur, parent3d: Node3D) -> void:
	w = wereld
	bestuur = b
	ghost = _kist(Color(0.3, 1.0, 0.3, 0.45))
	ghost.visible = false
	parent3d.add_child(ghost)
	w.plan_gezet.connect(_toon_plan)

	var laag := CanvasLayer.new()
	add_child(laag)
	knop = Button.new()
	knop.text = "Hut (B)"
	knop.toggle_mode = true
	knop.add_theme_font_size_override("font_size", 18)
	knop.set_anchors_preset(Control.PRESET_CENTER_BOTTOM)
	knop.position = Vector2(-50, -56)
	knop.focus_mode = Control.FOCUS_NONE
	knop.toggled.connect(func(aan: bool) -> void: zet_actief(aan))
	laag.add_child(knop)


func zet_actief(aan: bool) -> void:
	actief = aan
	ghost.visible = aan
	if knop.button_pressed != aan:
		knop.set_pressed_no_signal(aan)
	if aan:
		bestuur.wis_selectie()


func _kist(kleur: Color) -> MeshInstance3D:
	var m := BoxMesh.new()
	var af: Vector2i = Wereld.BOUWSOORTEN[soort]
	m.size = Vector3(af.x * w.tegel_m, HOOGTE, af.y * w.tegel_m)
	var mat := StandardMaterial3D.new()
	mat.albedo_color = kleur
	mat.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
	mat.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
	var mi := MeshInstance3D.new()
	mi.mesh = m
	mi.material_override = mat
	return mi


func _midden(p: Plan) -> Vector3:
	var r := p.afdruk()
	return Vector3((r.position.x + r.size.x * 0.5) * w.tegel_m, GROND_Y + HOOGTE * 0.5, (r.position.y + r.size.y * 0.5) * w.tegel_m)


func _plan_onder(pos: Vector2) -> Plan:
	var t := bestuur.tegel_onder(pos)
	if t.x < 0:
		return null
	var af: Vector2i = Wereld.BOUWSOORTEN[soort]
	var links := t - Vector2i(af.x / 2, af.y / 2)
	return Plan.new(soort, links, draai, af.x, af.y)


func _process(_dt: float) -> void:
	for p in _kisten:
		var k: MeshInstance3D = _kisten[p]
		var f: float = float(p.stand()) / Plan.STANDEN
		k.scale.y = f
		k.position.y = GROND_Y + HOOGTE * 0.5 * k.scale.y
		(k.material_override as StandardMaterial3D).albedo_color = Color(0.9, 0.8, 0.4, 0.5).lerp(Color(0.55, 0.4, 0.25, 1.0), f)
	if not actief:
		return
	var p := _plan_onder(get_viewport().get_mouse_position())
	ghost.visible = p != null
	if p == null:
		return
	ghost.position = _midden(p)
	ghost.rotation.y = draai * PI * 0.5
	var kan := w.kan_bouwen(p)
	(ghost.material_override as StandardMaterial3D).albedo_color = Color(0.3, 1.0, 0.3, 0.45) if kan else Color(1.0, 0.25, 0.2, 0.45)


func _toon_plan(p: Plan) -> void:
	var mi := _kist(Color(0.9, 0.8, 0.4, 0.5))
	mi.position = _midden(p)
	mi.rotation.y = p.draai * PI * 0.5
	_kisten[p] = mi
	ghost.get_parent().add_child(mi)


func _unhandled_input(e: InputEvent) -> void:
	if e is InputEventKey and e.pressed and not e.echo:
		if e.keycode == KEY_B:
			zet_actief(not actief)
			get_viewport().set_input_as_handled()
		elif actief and e.keycode == KEY_R:
			draai = (draai + 1) % 4
			get_viewport().set_input_as_handled()
		elif actief and e.keycode == KEY_ESCAPE:
			zet_actief(false)
			get_viewport().set_input_as_handled()
	elif actief and e is InputEventMouseButton:
		if e.button_index == MOUSE_BUTTON_LEFT and e.pressed:
			var p := _plan_onder(e.position)
			if p != null and w.plan_zet(p) and not Input.is_key_pressed(KEY_SHIFT):
				zet_actief(false)
			get_viewport().set_input_as_handled()
		elif e.button_index == MOUSE_BUTTON_RIGHT:
			if e.pressed:
				_rechts = true
				_rechts_start = e.position
			elif _rechts:
				_rechts = false
				if e.position.distance_to(_rechts_start) < KLIK_DREMPEL:
					zet_actief(false)
