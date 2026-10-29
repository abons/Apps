class_name WereldView
extends Node3D
## Spiegelt de sim (Wereld) in 3D: terrein, objecten, een Bumpkin per Dorpeling, selectiering, looppad, bevelmarkering,
## seizoenstint, vuurflikker. Leest de sim, schrijft er niets in.

var w: Wereld
var licht: Licht
var regen: Regen
var terrein: TerreinView
var units := {}            # id -> {"bump": Bumpkin, "ring": MeshInstance3D}
var koeien := {}           # koe-id -> Node3D
var kippen := {}           # kip-id -> Node3D
const DRAAG_KLEUR := {"graan": Color(0.72, 0.6, 0.38), "melk": Color(0.92, 0.92, 0.88), "ei": Color(0.72, 0.42, 0.26)}
var gekozen: Array = []    # id's, gezet door Bestuur
var _pad: MeshInstance3D
var _markeringen: Array = []   # [{node, t}]
var _ring_mesh: TorusMesh
var _ring_mat: StandardMaterial3D
var _t := 0.0
var _nat := 0.0
var _vuur: Node3D
var wegen: Wegen


func bouw(wereld: Wereld, l: Licht) -> void:
	w = wereld
	licht = l
	terrein = TerreinView.new()
	terrein.name = "Terrein_Wereld"
	add_child(terrein)
	terrein.bouw(w)
	_vuur = terrein.kampvuur_node
	wegen = Wegen.new()
	add_child(wegen)
	wegen.bouw(w, terrein)

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
		_maak_unit(d)
	w.dorpeling_erbij.connect(_maak_unit)
	w.rol_veranderd.connect(func(d: Dorpeling) -> void: _zet_rol(d))
	w.volwassen_geworden.connect(func(d: Dorpeling) -> void:   # jongen/meisje-glb wordt man/vrouw
		var oud: Bumpkin = units[d.id]["bump"]
		var yaw := oud.rotation.y
		oud.queue_free()
		_maak_unit(d)
		(units[d.id]["bump"] as Node3D).rotation.y = yaw)

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

	for k in w.vee:
		_maak_koe(k)
	w.koe_erbij.connect(_maak_koe)
	for k in w.kippen:
		_maak_kip(k)
	w.kip_erbij.connect(_maak_kip)
	w.koe_geclaimd.connect(func(k: Vee) -> void:
		if koeien.has(k.id):
			Koe.zet_eigen(koeien[k.id], k.eigenaar == 0))


func _maak_unit(d: Dorpeling) -> void:
	var b := Bumpkin.new()
	b.name = "Dorpeling_%d" % d.id
	var g := Bumpkin.glb_voor(d.geslacht, d.leeftijd)
	if g != "":
		b.glb = g
	elif d.leeftijd == "kind":
		b.scale = Vector3.ONE * 0.81         # terugval op de man; lijst.md: kind 0,81x
	add_child(b)
	var ring := MeshInstance3D.new()
	ring.name = "Selectiering"
	ring.mesh = _ring_mesh
	ring.material_override = _ring_mat
	ring.scale = Vector3(1, 0.25, 1)
	ring.position.y = 0.06
	ring.visible = false
	ring.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	b.add_child(ring)
	# de baby op de arm (beasts-src BABY_SHOW): een bundeltje voor de borst, alleen zolang d.baby > 0
	var bundel := MeshInstance3D.new()
	bundel.name = "Baby"
	var cm := CapsuleMesh.new()
	cm.radius = 0.09
	cm.height = 0.34
	bundel.mesh = cm
	var bm := StandardMaterial3D.new()
	bm.albedo_color = Color(0.93, 0.9, 0.82)
	bundel.material_override = bm
	bundel.rotation.z = PI * 0.5
	bundel.position = Vector3(0, 0.85, 0.2)
	bundel.visible = false
	b.add_child(bundel)
	var zak := MeshInstance3D.new()
	zak.name = "Graanzak"
	var zm := SphereMesh.new()
	zm.radius = 0.16
	zm.height = 0.36
	zak.mesh = zm
	var zmat := StandardMaterial3D.new()
	zmat.albedo_color = Color(0.72, 0.6, 0.38)
	zmat.roughness = 0.95
	zak.material_override = zmat
	zak.position = Vector3(0, 1.0, -0.2)      # op de rug (gezicht langs +Z)
	zak.visible = false
	b.add_child(zak)
	units[d.id] = {"bump": b, "ring": ring, "baby": bundel, "zak": zak}
	_zet_rol(d)
	b.volg(_wereld_pos(d, 0.0), 0.0)
	b.kijk_naar(Vector3(0, 0, 1), true)


## Bouwer: een gele helm op het Head-bot (concept bouwer, "helm v2"), tot er een eigen bouwer-glb is.
func _zet_rol(d: Dorpeling) -> void:
	var b: Bumpkin = units[d.id]["bump"]
	var oud := b.find_child("Bouwerhelm", true, false)
	if oud != null:
		oud.queue_free()
	if d.rol != "bouwer":
		return
	var sk := b.find_child("Skeleton3D", true, false) as Skeleton3D
	if sk == null or sk.find_bone("Head") < 0:
		return
	var ba := BoneAttachment3D.new()
	ba.name = "Bouwerhelm"
	ba.bone_name = "Head"
	sk.add_child(ba)
	var helm := MeshInstance3D.new()
	var sm := SphereMesh.new()
	sm.radius = 0.12
	sm.height = 0.24
	sm.is_hemisphere = true
	helm.mesh = sm
	var m := StandardMaterial3D.new()
	m.albedo_color = Color(0.86, 0.68, 0.18)
	m.metallic = 0.3
	m.roughness = 0.45
	helm.material_override = m
	helm.position = Vector3(0, 0.15, 0.01)
	ba.add_child(helm)
	var rand := MeshInstance3D.new()
	var cm := CylinderMesh.new()
	cm.top_radius = 0.15
	cm.bottom_radius = 0.15
	cm.height = 0.015
	rand.mesh = cm
	rand.material_override = m
	rand.position = Vector3(0, 0.15, 0.01)
	ba.add_child(rand)


func _maak_koe(k: Vee) -> void:
	var n := Koe.maak("grazen", float(k.id % 3))
	if n == null:
		return
	n.name = "Koe_%d" % k.id
	add_child(n)
	koeien[k.id] = n
	var p := k.pos * w.tegel_m
	n.position = Vector3(p.x, terrein.hoogte_op(p.x, p.y), p.y)
	n.rotation.y = float(k.id) * 2.4
	Koe.zet_eigen(n, k.eigenaar == 0)


func _maak_kip(k: Kip) -> void:
	var n := KipModel.maak(float(k.id % 4) * 0.4)
	n.name = "Kip_%d" % k.id
	add_child(n)
	kippen[k.id] = n
	var p := k.pos * w.tegel_m
	n.position = Vector3(p.x, terrein.hoogte_op(p.x, p.y), p.y)
	n.rotation.y = float(k.id) * 1.9


func _werk_kippen(a: float, dt: float) -> void:
	for k in w.kippen:
		if not kippen.has(k.id):
			continue
		var n: Node3D = kippen[k.id]
		var p := k.vorige.lerp(k.pos, a) * w.tegel_m
		var nieuw := Vector3(p.x, terrein.hoogte_op(p.x, p.y), p.y)
		var d := nieuw - n.position
		if Vector2(d.x, d.z).length() > 0.001:
			n.rotation.y = lerp_angle(n.rotation.y, atan2(d.x, d.z), minf(1.0, dt * 10.0))
		n.position = nieuw
		var t := 0.0 if w.gepauzeerd else w.tempo
		if k.ei:
			KipModel.speel(n, "zitten", t)
		elif k.snelheid_mps > 0.0:
			KipModel.speel(n, "lopen", t)
		elif k.pikt:
			KipModel.speel(n, "pikken", t)
		else:
			KipModel.speel(n, "idle", t)


## Wereldpositie van een koe (voor Bestuur: klikken op een koe).
func koe_pos(id: int) -> Vector3:
	return (koeien[id] as Node3D).global_position if koeien.has(id) else Vector3.INF


func _werk_koeien(a: float, dt: float) -> void:
	for k in w.vee:
		if not koeien.has(k.id):
			continue
		var n: Node3D = koeien[k.id]
		var p := k.vorige.lerp(k.pos, a) * w.tegel_m
		var nieuw := Vector3(p.x, terrein.hoogte_op(p.x, p.y), p.y)
		var d := nieuw - n.position
		if Vector2(d.x, d.z).length() > 0.002:
			n.rotation.y = lerp_angle(n.rotation.y, atan2(d.x, d.z), minf(1.0, dt * 6.0))   # gezicht langs +Z, als Bumpkin
		n.position = nieuw
		if w.gepauzeerd:
			Koe.speel(n, "idle", 0.0)
		elif k.gemolken:
			Koe.speel(n, "gemolken_worden", w.tempo)
		elif k.snelheid_mps > 0.0:
			Koe.speel(n, "lopen", w.tempo)
		else:
			Koe.speel(n, "grazen", w.tempo)


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
		b.werk(d.bouwt and not w.gepauzeerd)
		b.zet_nacht(donker)
		b.visible = not d.binnen
		(u["ring"] as MeshInstance3D).visible = d.id in gekozen
		(u["baby"] as MeshInstance3D).visible = d.baby > 0.0
		var zak: MeshInstance3D = u["zak"]
		zak.visible = d.draagt != ""
		if zak.visible:
			(zak.material_override as StandardMaterial3D).albedo_color = DRAAG_KLEUR.get(d.draagt, Color.WHITE)
			zak.scale = Vector3.ONE * (0.45 if d.draagt == "ei" else 1.0)
	_werk_koeien(a, dt)
	_werk_kippen(a, dt)
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
	wegen.werk_seizoen(sneeuw, nat)


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
