class_name Regen
extends GPUParticles3D
## Regendeeltjes boven de camera-focus. `aan(bool)` is de weerhaak: Wereld.regent() stuurt hem.


func _ready() -> void:
	name = "Regen"
	amount = 7000
	lifetime = 0.6
	preprocess = 1.0
	emitting = false
	local_coords = false
	visibility_aabb = AABB(Vector3(-40, -20, -40), Vector3(80, 40, 80))
	cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	var pm := ParticleProcessMaterial.new()
	pm.emission_shape = ParticleProcessMaterial.EMISSION_SHAPE_BOX
	pm.emission_box_extents = Vector3(34, 0.5, 34)
	pm.direction = Vector3(0.12, -1, 0.05)
	pm.spread = 2.0
	pm.initial_velocity_min = 22.0
	pm.initial_velocity_max = 28.0
	pm.gravity = Vector3.ZERO
	process_material = pm
	var q := QuadMesh.new()
	q.size = Vector2(0.012, 0.45)
	var m := StandardMaterial3D.new()
	m.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
	m.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
	m.albedo_color = Color(0.75, 0.82, 0.9, 0.22)
	m.billboard_mode = BaseMaterial3D.BILLBOARD_FIXED_Y
	m.cull_mode = BaseMaterial3D.CULL_DISABLED
	q.material = m
	draw_pass_1 = q


func aan(b: bool) -> void:
	if emitting != b:
		emitting = b


func volg(focus: Vector3) -> void:
	global_position = Vector3(focus.x, 16.0, focus.z)
