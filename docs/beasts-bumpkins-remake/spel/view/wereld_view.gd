class_name WereldView
extends Node3D
## Spiegelt de sim (Wereld) in 3D: terrein, objecten, een Bumpkin per Dorpeling, selectiering, looppad, bevelmarkering,
## seizoenstint, vuurflikker. Leest de sim, schrijft er niets in.

var w: Wereld
var licht: Licht
var regen: Regen
var terrein: TerreinView
var units := {}            # id -> {"bump": Bumpkin, "ring": MeshInstance3D}
var gekozen: Array = []    # id's, gezet door Bestuur
var _pad: MeshInstance3D
var _markeringen: Array = []   # [{node, t}]
var _ring_mesh: TorusMesh
var _ring_mat: StandardMaterial3D
var _t := 0.0
var _nat := 0.0
var _vuur: Node3D


func bouw(wereld: Wereld, l: Licht) -> void:
	w = wereld
	licht = l
	terrein = TerreinView.new()
	terrein.name = "Terrein_Wereld"
	add_child(terrein)
	terrein.bouw(w)
	_vuur = terrein.kampvuur_node

	_ring_mesh = TorusMesh.new()
	_ring_mesh.inner_radius = 0.50
	_ring_mesh.outer_radius = 0.64
	_ring_mesh.rings = 20
	_ring_mesh.ring_segments = 6
	_ring_mat = StandardMaterial3D.new()
	_ring_mat.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
	_ring_mat.albedo_color = Color(0.55, 1.0, 0.35)
	_ring_mat.no_depth_test = false

	for d in w.dorpelingen:
		var b := Bumpkin.new()
		b.name = "Dorpeling_%d" % d.id
		add_child(b)
		if d.leeftijd == "kind":
			b.scale = Vector3.ONE * 0.81         # lijst.md: kind 0,81x
		var ring := MeshInstance3D.new()
		ring.name = "Selectiering"
		ring.mesh = _ring_mesh
		ring.material_override = _ring_mat
		ring.scale = Vector3(1, 0.25, 1)
		ring.position.y = 0.06
		ring.visible = false
		ring.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
		b.add_child(ring)
		units[d.id] = {"bump": b, "ring": ring}
		b.volg(_wereld_pos(d, 0.0), 0.0)
		b.kijk_naar(Vector3(0, 0, 1), true)

	_pad = MeshInstance3D.new()
	_pad.name = "Looppad"
	_pad.mesh = ImmediateMesh.new()
	var pm := StandardMaterial3D.new()
	pm.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
	pm.albedo_color = Color(1.0, 0.9, 0.3)
	_pad.material_override = pm
	_pad.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	add_child(_pad)

	regen = Regen.new()
	add_child(regen)


func _wereld_pos(d: Dorpeling, alpha: float) -> Vector3:
	var p := d.vorige.lerp(d.pos, alpha) * w.tegel_m
	return Vector3(p.x, terrein.hoogte_op(p.x, p.y), p.y)


## Wereldpositie van een dorpeling (voor Bestuur: schermprojectie).
func unit_pos(id: int) -> Vector3:
	return (units[id]["bump"] as Node3D).global_position


func _process(dt: float) -> void:
	_t += dt
	var a := w.alpha()
	var donker := licht.donker
	for d in w.dorpelingen:
		var u: Dictionary = units[d.id]
		var b: Bumpkin = u["bump"]
		var v := 0.0 if w.gepauzeerd else d.snelheid_mps * w.tempo
		b.volg(_wereld_pos(d, a), v)
		b.werk(d.bouwt)
		b.zet_nacht(donker)
		(u["ring"] as MeshInstance3D).visible = d.id in gekozen
	_werk_pad()
	_werk_markeringen(dt)
	werk_seizoen()
	_werk_vuur(donker)


func werk_seizoen() -> void:
	var sneeuw := w.sneeuw()
	var droog := w.droog()
	_nat = lerpf(_nat, 1.0 if w.regent() else 0.0, 0.03)   # zacht aan- en uitgaan
	var nat := _nat
	terrein.terrein_mat.set_shader_parameter("sneeuw", sneeuw)
	terrein.terrein_mat.set_shader_parameter("droog", droog)
	terrein.terrein_mat.set_shader_parameter("nat", nat)
	terrein.water_mat.set_shader_parameter("ijs", sneeuw)
	licht.werk(w.uur(), w.kou(), nat)
	regen.aan(w.regent())
	# gebladerte (tint per seizoen), rotsen (sneeuwdek) en de sneeuwlaag op de bomen
	Natuur.werk_seizoen(w.seizoen(), w.dag_t() / w.seizoen_duur(), sneeuw, nat)
	terrein.zet_sneeuwlaag(sneeuw > 0.3)


func _werk_vuur(donker: float) -> void:
	if _vuur == null:
		return
	var fl := 0.85 + 0.1 * sin(_t * 13.0) + 0.06 * sin(_t * 31.7 + 1.3) + 0.05 * sin(_t * 7.3)
	var l: OmniLight3D = _vuur.find_child("Vuurlicht", true, false)
	l.light_energy = lerpf(0.5, 3.2, donker) * fl
	var vlam := _vuur.find_child("Vlam", true, false) as Node3D
	if vlam:
		vlam.scale = Vector3(1.0 + 0.1 * sin(_t * 9.0), fl * 1.1, 1.0 + 0.1 * cos(_t * 11.0))


func _werk_pad() -> void:
	var im := _pad.mesh as ImmediateMesh
	im.clear_surfaces()
	for id in gekozen:
		var d := w.dorpeling(id)
		if d == null or d.route.is_empty():
			continue
		im.surface_begin(Mesh.PRIMITIVE_LINE_STRIP)
		var p := unit_pos(id)
		im.surface_add_vertex(p + Vector3(0, 0.25, 0))
		for t in d.route:
			var px := t.x * w.tegel_m
			var pz := t.y * w.tegel_m
			im.surface_add_vertex(Vector3(px, terrein.hoogte_op(px, pz) + 0.25, pz))
		im.surface_end()


## Markering op de grond waar een bevel naartoe gaat (ring die uitdooft).
func markeer(t: Vector2i) -> void:
	var n := MeshInstance3D.new()
	n.mesh = _ring_mesh
	var m := StandardMaterial3D.new()
	m.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
	m.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
	m.albedo_color = Color(1.0, 0.95, 0.4, 0.9)
	n.material_override = m
	n.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	n.position = terrein.tegel_midden(t) + Vector3(0, 0.08, 0)
	add_child(n)
	_markeringen.append({"node": n, "t": 0.0, "mat": m})


func _werk_markeringen(dt: float) -> void:
	for mk in _markeringen.duplicate():
		mk["t"] += dt
		var f: float = mk["t"] / 1.2
		var n: MeshInstance3D = mk["node"]
		n.scale = Vector3.ONE * lerpf(1.6, 0.8, f) * Vector3(1, 0.2, 1)
		(mk["mat"] as StandardMaterial3D).albedo_color.a = 0.9 * (1.0 - f)
		if f >= 1.0:
			n.queue_free()
			_markeringen.erase(mk)
