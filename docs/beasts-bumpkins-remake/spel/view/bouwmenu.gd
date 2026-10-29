class_name Bouwmenu
extends Node
## Bouwmenu (stap 5, gameplay.md §7): knop "Hut" of B, ghost volgt de muis over de tegels (groen = kan, rood = kan niet),
## R draait, linkerklik plaatst een Plan in Wereld, rechterklik of Esc stopt. Shift bij het plaatsen houdt de modus aan.
## Een Plan is een kist die in Plan.STANDEN groeit, met een houtstapel en steenhoop ernaast die slinken met de voortgang
## (alleen weergave; kas en aanvoer staan nog niet in de sim). Klaar: de kist wordt de hut-glb (terugval: bruine kist).
## Moet NA Bestuur in de boom staan: dan krijgt het de invoer eerst en neemt het de linkerklik van het kiezen over.

const GROND_Y := 0.25
const KLIK_DREMPEL := 6.0
const HOOGTE := 2.4
const HUT_GLB := "res://assets/peasant_hut_rt.glb"
const STAPELS := ["houtstapel", "steenhoop"]
const STAPEL_RESTANT := 0.35   ## schaal van een stapel vlak voor klaar

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
var _stapels := {}         ## Plan -> [Node3D]
var terrein: TerreinView   ## optioneel: grondhoogte voor stapels en hut (anders GROND_Y)
var _hut_scene: PackedScene


func bouw(wereld: Wereld, b: Bestuur, parent3d: Node3D) -> void:
	w = wereld
	bestuur = b
	ghost = _kist(Color(0.3, 1.0, 0.3, 0.45))
	ghost.visible = false
	parent3d.add_child(ghost)
	w.plan_gezet.connect(_toon_plan)
	w.plan_klaar.connect(_plan_klaar)

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
	for p in _stapels:
		for s: Node3D in _stapels[p]:
			s.scale = Vector3.ONE * lerpf(1.0, STAPEL_RESTANT, p.voortgang)
	for p in _kisten:
		var k: MeshInstance3D = _kisten[p]
		if p.klaar:
			continue
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
	var lijst: Array[Node3D] = []
	var plekken := _stapelplekken(p, STAPELS.size())
	for i in plekken.size():
		var n := Natuur.instantie(STAPELS[i])
		if n == null:
			continue
		n.position = _grond(plekken[i])
		n.rotation.y = p.draai * PI * 0.5 + i * 0.7
		ghost.get_parent().add_child(n)
		lijst.append(n)
	_stapels[p] = lijst


func _grond(t: Vector2i) -> Vector3:
	var v := Vector3((t.x + 0.5) * w.tegel_m, GROND_Y, (t.y + 0.5) * w.tegel_m)
	if terrein != null:
		v.y = terrein.hoogte_op(v.x, v.z)
	return v


## Loopbare tegels die aan de voetafdruk grenzen (niet op de hoeken), te beginnen aan de voorkant (+z na draaien).
func _stapelplekken(p: Plan, n: int) -> Array[Vector2i]:
	var r := p.afdruk()
	var rand: Array[Vector2i] = []
	for c in range(r.position.x, r.end.x):
		rand.append(Vector2i(c, r.end.y))
	for rij in range(r.position.y, r.end.y):
		rand.append(Vector2i(r.end.x, rij))
	for c in range(r.position.x, r.end.x):
		rand.append(Vector2i(c, r.position.y - 1))
	for rij in range(r.position.y, r.end.y):
		rand.append(Vector2i(r.position.x - 1, rij))
	var uit: Array[Vector2i] = []
	for t in rand:
		if uit.size() < n and w.raster.loopbaar_v(t) and w.plan_op(t) == null:
			uit.append(t)
	return uit


## Plan af: stapels weg, de kist wordt de hut, geschaald naar de voetafdruk (de glb heeft zijn eigen maat).
func _plan_klaar(p: Plan) -> void:
	for s: Node3D in _stapels.get(p, []):
		s.queue_free()
	_stapels.erase(p)
	var k: MeshInstance3D = _kisten.get(p)
	if k == null:
		return
	if _hut_scene == null and ResourceLoader.exists(HUT_GLB):
		_hut_scene = load(HUT_GLB)
	if _hut_scene == null:
		k.scale.y = 1.0
		k.position.y = GROND_Y + HOOGTE * 0.5
		(k.material_override as StandardMaterial3D).albedo_color = Color(0.55, 0.4, 0.25, 1.0)
		return
	var hut: Node3D = _hut_scene.instantiate()
	var box := _omhulsel(hut, Transform3D.IDENTITY)
	var r := p.afdruk()
	var schaal := minf(r.size.x, r.size.y) * w.tegel_m * 0.95 / maxf(box.size.x, box.size.z)
	hut.scale = Vector3.ONE * schaal
	hut.rotation.y = p.draai * PI * 0.5
	var m := Vector3((r.position.x + r.size.x * 0.5) * w.tegel_m, GROND_Y, (r.position.y + r.size.y * 0.5) * w.tegel_m)
	if terrein != null:
		m.y = terrein.hoogte_op(m.x, m.z)
	var midden := box.get_center() * schaal
	hut.position = m - Vector3(midden.x, box.position.y * schaal, midden.z).rotated(Vector3.UP, hut.rotation.y)
	ghost.get_parent().add_child(hut)
	k.queue_free()
	_kisten.erase(p)


static func _omhulsel(n: Node, t: Transform3D) -> AABB:
	var uit := AABB()
	var eerste := true
	var tt := t * (n as Node3D).transform if n is Node3D else t
	if n is MeshInstance3D and (n as MeshInstance3D).mesh != null:
		uit = tt * (n as MeshInstance3D).get_aabb()
		eerste = false
	for c in n.get_children():
		var b := _omhulsel(c, tt)
		if b.size == Vector3.ZERO:
			continue
		uit = b if eerste else uit.merge(b)
		eerste = false
	return uit


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
