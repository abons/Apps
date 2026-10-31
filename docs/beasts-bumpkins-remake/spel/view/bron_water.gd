class_name BronWater
extends RefCounted
## Bewegend water op de put (bron.glb): het bassin (`bron_water`) rimpelt en de straal (`bron_straal`) stroomt, met
## twee kleine shaders (shaders/bron_water.gdshader, shaders/bron_straal.gdshader) in plaats van de stilstaande
## glb-materialen. Eén gedeeld materiaal per soort voor alle putten; Bouwmenu._plan_klaar roept `zet` aan.

static var _water: ShaderMaterial
static var _straal: ShaderMaterial


static func zet(n: Node3D) -> void:
	if _water == null:
		_water = ShaderMaterial.new()
		_water.shader = load("res://shaders/bron_water.gdshader")
		_straal = ShaderMaterial.new()
		_straal.shader = load("res://shaders/bron_straal.gdshader")
	var w := n.find_child("bron_water", true, false) as MeshInstance3D
	if w != null:
		w.material_override = _water
	var s := n.find_child("bron_straal", true, false) as MeshInstance3D
	if s != null:
		s.material_override = _straal
