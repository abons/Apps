class_name Licht
extends Node
## Zon, maan, lucht, mist en omgevingslicht uit uur, kou (seizoen) en regen. Overgenomen uit modellen/godot3d/main.gd:
## de zonnestand en kleurtabellen zijn dezelfde, `winter` is hier een vloeiende `kou` 0..1.

var env: Environment
var sky_mat: ProceduralSkyMaterial
var zon: DirectionalLight3D
var maan: DirectionalLight3D
var donker := 0.0           # 0 dag .. 1 nacht, voor vuurlicht en dorpelingen


func _ready() -> void:
	sky_mat = ProceduralSkyMaterial.new()
	sky_mat.sun_angle_max = 20.0
	sky_mat.sun_curve = 0.12
	var sky := Sky.new()
	sky.sky_material = sky_mat
	env = Environment.new()
	env.background_mode = Environment.BG_SKY
	env.sky = sky
	env.ambient_light_source = Environment.AMBIENT_SOURCE_SKY
	env.reflected_light_source = Environment.REFLECTION_SOURCE_SKY
	env.tonemap_mode = Environment.TONE_MAPPER_ACES
	env.tonemap_white = 6.0
	env.ssao_enabled = true
	env.ssao_radius = 1.0
	env.ssao_intensity = 1.6
	env.glow_enabled = true
	env.glow_intensity = 0.6
	env.glow_bloom = 0.05
	env.glow_hdr_threshold = 1.0
	env.fog_enabled = true
	env.fog_density = 0.0016
	env.fog_sky_affect = 0.0
	var we := WorldEnvironment.new()
	we.environment = env
	add_child(we)

	zon = DirectionalLight3D.new()
	zon.name = "Zon"
	zon.shadow_enabled = true
	zon.directional_shadow_mode = DirectionalLight3D.SHADOW_PARALLEL_4_SPLITS
	zon.directional_shadow_max_distance = 140.0
	zon.light_angular_distance = 0.8
	zon.shadow_blur = 1.0
	zon.shadow_bias = 0.04
	zon.shadow_normal_bias = 1.2
	add_child(zon)

	maan = DirectionalLight3D.new()
	maan.name = "Maan"
	maan.shadow_enabled = true
	maan.directional_shadow_mode = DirectionalLight3D.SHADOW_PARALLEL_4_SPLITS
	maan.directional_shadow_max_distance = 90.0
	maan.light_angular_distance = 1.5
	maan.light_color = Color(0.55, 0.66, 1.0)
	maan.sky_mode = DirectionalLight3D.SKY_MODE_LIGHT_ONLY
	add_child(maan)


func _zon_hoeken(h: float, kou: float) -> Vector2:
	## (azimut vanaf noord met de klok mee, elevatie) in graden. kou 0 = zomer, 1 = winter.
	var opkomst := lerpf(5.0, 8.5, kou)
	var onder := lerpf(21.5, 16.5, kou)
	var max_el := lerpf(58.0, 24.0, kou)
	var az_op := lerpf(50.0, 125.0, kou)
	var az_onder := lerpf(310.0, 235.0, kou)
	h = fposmod(h, 24.0)
	if h >= opkomst and h <= onder:
		var f := (h - opkomst) / (onder - opkomst)
		return Vector2(lerpf(az_op, az_onder, f), sin(f * PI) * max_el)
	var nacht := 24.0 - (onder - opkomst)
	var nf := fposmod(h - onder, 24.0) / nacht
	return Vector2(lerpf(az_onder, az_op + 360.0, nf), -sin(nf * PI) * 35.0)


func _richting(az: float, el: float) -> Vector3:
	var a := deg_to_rad(az)
	var e := deg_to_rad(el)
	return Vector3(sin(a) * cos(e), sin(e), -cos(a) * cos(e))   # noord = -Z, oost = +X


func _kleur_bij(el: float, punten: Array) -> Color:
	if el <= punten[0][0]:
		return punten[0][1]
	for i in range(1, punten.size()):
		if el <= punten[i][0]:
			var f := inverse_lerp(punten[i - 1][0], punten[i][0], el)
			return (punten[i - 1][1] as Color).lerp(punten[i][1], smoothstep(0.0, 1.0, f))
	return punten[-1][1]


func werk(uur: float, kou: float, regen: float) -> void:
	var zh := _zon_hoeken(uur, kou)
	var el := zh.y
	var d := _richting(zh.x, maxf(el, -1.0))
	zon.look_at_from_position(Vector3.ZERO, -d, Vector3.UP if absf(d.y) < 0.99 else Vector3.FORWARD)
	var dag := smoothstep(-1.0, 6.0, el)
	var bewolkt := 1.0 - 0.55 * regen
	zon.light_energy = dag * lerpf(1.3, 1.9, smoothstep(2.0, 30.0, el)) * bewolkt
	zon.light_color = _kleur_bij(el, [
		[0.0, Color(1.0, 0.42, 0.18)], [6.0, Color(1.0, 0.62, 0.35)],
		[18.0, Color(1.0, 0.86, 0.70)], [35.0, Color(1.0, 0.96, 0.90)]])
	zon.visible = dag > 0.001

	var nacht := 1.0 - smoothstep(-8.0, 0.0, el)
	donker = 1.0 - smoothstep(2.0, 10.0, el)
	var md := _richting(fposmod(zh.x + 180.0, 360.0), 38.0)
	maan.look_at_from_position(Vector3.ZERO, -md, Vector3.UP)
	maan.light_energy = nacht * 0.22
	maan.visible = nacht > 0.001

	var grijs := Color(0.50, 0.53, 0.58)
	sky_mat.sky_top_color = _kleur_bij(el, [
		[-14.0, Color(0.008, 0.012, 0.035)], [-5.0, Color(0.05, 0.07, 0.18)],
		[2.0, Color(0.18, 0.28, 0.55)], [20.0, Color(0.20, 0.40, 0.78)]]).lerp(grijs * dag, regen * 0.7)
	sky_mat.sky_horizon_color = _kleur_bij(el, [
		[-14.0, Color(0.02, 0.03, 0.07)], [-5.0, Color(0.30, 0.20, 0.25)],
		[1.0, Color(0.95, 0.52, 0.30)], [8.0, Color(0.90, 0.72, 0.55)],
		[20.0, Color(0.68, 0.79, 0.90)]]).lerp(grijs * (0.3 + 0.7 * dag), regen * 0.7)
	sky_mat.ground_horizon_color = sky_mat.sky_horizon_color
	sky_mat.ground_bottom_color = sky_mat.sky_top_color.darkened(0.5)
	sky_mat.sky_energy_multiplier = lerpf(0.35, 1.0, smoothstep(-12.0, 4.0, el))

	env.ambient_light_energy = lerpf(0.12, 0.55, smoothstep(-10.0, 15.0, el))
	env.ambient_light_sky_contribution = lerpf(0.4, 1.0, dag)
	env.ambient_light_color = Color(0.10, 0.13, 0.26)
	env.fog_light_color = sky_mat.sky_horizon_color.darkened(0.1)
	env.fog_density = lerpf(0.0016, 0.006, regen)
	env.tonemap_exposure = lerpf(1.6, 0.85, dag)
