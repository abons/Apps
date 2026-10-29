class_name Koe
extends RefCounted
## De koe: assets/koe.glb + koe_anim.json (uit modellen/dieren/, een andere sessie verbetert hem nog). Alleen hier staat wat
## van de glb afhangt: het pad, de verborgen onderdelen (extras.verborgen) en de animatienamen. Nieuwe versie = sync.ps1 + --import.

const GLB := "res://assets/koe.glb"
const ANIM := "res://assets/koe_anim.json"
const STANDAARD := "grazen"        # idle, lopen, grazen, gemolken_worden, sterven, geboorte


static func bestaat() -> bool:
	return ResourceLoader.exists(GLB)


## Een koe met verborgen onderdelen weg en de gewenste animatie aan. Null zonder glb.
static func maak(anim := STANDAARD, start := 0.0) -> Node3D:
	if not bestaat():
		return null
	var n: Node3D = (load(GLB) as PackedScene).instantiate()
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
