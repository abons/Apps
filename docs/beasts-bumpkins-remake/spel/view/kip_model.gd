class_name KipModel
extends RefCounted
## De kip: assets/kip.glb + kip_anim.json (uit modellen/dieren/kip.py). Alleen hier staat wat van de glb afhangt: het
## pad en de clipnamen (idle, lopen, pikken, zitten). Zonder glb een eenvoudig placeholder-kipje (geen animatie).

const GLB := "res://assets/kip.glb"
const ANIM := "res://assets/kip_anim.json"


static func maak(start := 0.0) -> Node3D:
	if not ResourceLoader.exists(GLB):
		return _placeholder()
	var n: Node3D = (load(GLB) as PackedScene).instantiate()
	n.name = "kip"
	speel(n, "idle")
	var ap := _speler(n)
	if ap:
		ap.seek(start, true)
	return n


## Speel `anim` (lus volgens kip_anim.json) als hij nog niet speelt; `tempo` schaalt het afspelen.
static func speel(n: Node3D, anim: String, tempo := 1.0) -> void:
	var ap := _speler(n)
	if ap == null or not ap.has_animation(StringName(anim)):
		return
	if ap.current_animation != anim:
		var d = Gegevens.lees(ANIM)
		if d is Dictionary and d.has(anim) and d[anim].get("loop", false):
			ap.get_animation(StringName(anim)).loop_mode = Animation.LOOP_LINEAR
		ap.play(StringName(anim), 0.2)
	ap.speed_scale = tempo


## Het ei bij een zittende kip (sim/kip.gd `ei`): assets/ei.glb achter de staart, weg zodra het geraapt is. Het
## origineel (`chickegg`) toont een los bruin ei naast de kip; 6 cm is vanaf de RTS-camera onzichtbaar, dus x2.
const EI_GLB := "res://assets/ei.glb"
const EI_PLEK := Vector3(0.1, 0.0, -0.24)   # lokaal: kip kijkt langs +Z
const EI_SCHAAL := 2.0


static func zet_ei(n: Node3D, aan: bool) -> void:
	var e := n.get_node_or_null("ei") as Node3D
	if e == null:
		if not aan:
			return
		if ResourceLoader.exists(EI_GLB):
			e = (load(EI_GLB) as PackedScene).instantiate()
		else:
			var mi := MeshInstance3D.new()
			var sm := SphereMesh.new()
			sm.radius = 0.025
			sm.height = 0.06
			mi.mesh = sm
			mi.position.y = 0.03
			e = Node3D.new()
			e.add_child(mi)
		e.name = "ei"
		e.position = EI_PLEK
		e.scale = Vector3.ONE * EI_SCHAAL
		n.add_child(e)
	e.visible = aan


static func _speler(n: Node) -> AnimationPlayer:
	if n is AnimationPlayer:
		return n
	for c in n.get_children():
		var r := _speler(c)
		if r:
			return r
	return null


static func _placeholder() -> Node3D:
	var n := Node3D.new()
	n.name = "kip"
	var lijf := MeshInstance3D.new()
	var sm := SphereMesh.new()
	sm.radius = 0.14
	sm.height = 0.24
	lijf.mesh = sm
	var m := StandardMaterial3D.new()
	m.albedo_color = Color(0.62, 0.27, 0.12)
	lijf.material_override = m
	lijf.position = Vector3(0, 0.2, 0)
	n.add_child(lijf)
	var kop := MeshInstance3D.new()
	var km := SphereMesh.new()
	km.radius = 0.06
	km.height = 0.12
	kop.mesh = km
	kop.material_override = m
	kop.position = Vector3(0, 0.34, 0.12)
	n.add_child(kop)
	var kam := MeshInstance3D.new()
	var bm := BoxMesh.new()
	bm.size = Vector3(0.02, 0.04, 0.06)
	kam.mesh = bm
	var rm := StandardMaterial3D.new()
	rm.albedo_color = Color(0.85, 0.08, 0.08)
	kam.material_override = rm
	kam.position = Vector3(0, 0.41, 0.12)
	n.add_child(kam)
	return n
