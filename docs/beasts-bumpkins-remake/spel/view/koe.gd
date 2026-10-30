class_name Koe
extends RefCounted
## De koe: assets/koe.glb + koe_anim.json (uit modellen/dieren/, een andere sessie verbetert hem nog). Alleen hier staat wat
## van de glb afhangt: het pad, de verborgen onderdelen (extras.verborgen) en de animatienamen. Nieuwe versie = sync.ps1 + --import.

const GLB := "res://assets/koe.glb"
## spel.json `koe_model` "tripo": de procedurele koe vervormd naar de Tripo-referentie met geprojecteerde textuur
## (modellen/dieren/koe_tripo.py, lokaal: textuur uit de Tripo-render). Zelfde skelet, clips en assen.
const GLB_TRIPO := "res://assets/koe_tripo.glb"
const ANIM := "res://assets/koe_anim.json"
const STANDAARD := "grazen"        # idle, lopen, grazen, gemolken_worden, sterven, geboorte


static func bestaat() -> bool:
	return ResourceLoader.exists(glb_pad())


## Glb-pad: spel.json `koe_model` ("tripo" | "procedureel"; voor vergelijkingsframes overschrijft `-- --koe_model=...`
## dat), terugval op de procedurele glb.
static func glb_pad() -> String:
	var d = Gegevens.lees(Gegevens.SPEL)
	var keuze := String(d.get("koe_model", "procedureel")) if d is Dictionary else "procedureel"
	for a in OS.get_cmdline_user_args():
		if a.begins_with("--koe_model="):
			keuze = a.get_slice("=", 1)
	if keuze == "tripo" and ResourceLoader.exists(GLB_TRIPO):
		return GLB_TRIPO
	return GLB


## Een koe met verborgen onderdelen weg en de gewenste animatie aan. Null zonder glb.
static func maak(anim := STANDAARD, start := 0.0) -> Node3D:
	if not bestaat():
		return null
	var n: Node3D = (load(glb_pad()) as PackedScene).instantiate()
	n.name = "koe"
	_verberg(n)
	var ap := _speler(n)
	if ap:
		var naam := StringName(anim)
		if not ap.has_animation(naam):
			naam = &"idle" if ap.has_animation(&"idle") else StringName()
		if naam != StringName():
			if _lus(String(naam)):
				ap.get_animation(naam).loop_mode = Animation.LOOP_LINEAR
			ap.play(naam)
			ap.seek(start, true)
	return n


## Eigen koe: halsband (paars, zoals de "purple collars" van het origineel) en bel zichtbaar; wild: beide weg.
static func zet_eigen(n: Node3D, eigen: bool) -> void:
	var hb := n.find_child("halsband", true, false) as MeshInstance3D
	var bel := n.find_child("bel", true, false) as Node3D
	if hb:
		hb.visible = eigen
		if eigen and hb.material_override == null:
			var m := StandardMaterial3D.new()
			m.albedo_color = Color(0.42, 0.12, 0.55)
			m.roughness = 0.6
			hb.material_override = m
	if bel:
		bel.visible = eigen


## Kalf (sim/vee.gd `kalf`): de koe verkleind, van KALF_SCHAAL bij de geboorte naar 1 als ze volwassen is (`groei` 0..1).
## Origineel `cowborn`: een klein wit-zwart kalf, ~0,6 van de koe (34x21 tegen 51x34 px).
const KALF_SCHAAL := 0.55


static func zet_kalf(n: Node3D, groei: float) -> void:
	n.scale = Vector3.ONE * lerpf(KALF_SCHAAL, 1.0, clampf(groei, 0.0, 1.0))


## Speel `anim` (lus volgens koe_anim.json) als hij nog niet speelt; `tempo` schaalt het afspelen.
static func speel(n: Node3D, anim: String, tempo := 1.0) -> void:
	var ap := _speler(n)
	if ap == null or not ap.has_animation(StringName(anim)):
		return
	if ap.current_animation != anim:
		if _lus(anim):
			ap.get_animation(StringName(anim)).loop_mode = Animation.LOOP_LINEAR
		ap.play(StringName(anim), 0.3)
	ap.speed_scale = tempo


static func _lus(naam: String) -> bool:
	var d = Gegevens.lees(ANIM)
	return d is Dictionary and d.has(naam) and d[naam].get("loop", false)


static func _verberg(n: Node) -> void:
	if n is Node3D and n.has_meta("extras"):
		var ex = n.get_meta("extras")
		if ex is Dictionary and ex.get("verborgen", false):
			(n as Node3D).visible = false
	for c in n.get_children():
		_verberg(c)


static func _speler(n: Node) -> AnimationPlayer:
	if n is AnimationPlayer:
		return n
	for c in n.get_children():
		var r := _speler(c)
		if r:
			return r
	return null
