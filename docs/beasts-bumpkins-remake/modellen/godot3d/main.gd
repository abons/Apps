extends Node3D
## Hut 3D demo: grond, hut (glTF), dag/nacht, kaars, rook, deur, dorpeling.
## Alles wordt in code opgebouwd; de hut-knopen worden op naam gezocht met vaste terugvalposities.
## Start met `-- --demo` voor de autopiloot (camera + tijd vast gescript, voor Movie Maker).

const HUT_RES := "res://hut/peasant_hut_rt.glb"
const HUT_LOD1 := "res://hut/peasant_hut_rt_lod1.glb"
const LOD_WISSEL := 28.0  # m: verder weg toont LOD1 (6k driehoeken) in plaats van LOD0 (112k)
const HUT_BRON := "../peasant_hut_rt.glb"  # relatief aan de projectmap, runtime-terugval
const DAG_SECONDEN := 60.0
const DEUR_OPEN_HOEK := deg_to_rad(-90.0)  # deur_voor draait naar buiten: negatief om lokale Y
const LOOPSNELHEID := 1.3

# Terugval (Godot-coördinaten): Blender (x,y,z) -> (x, z, -y).
const HUT_MIDDEN := Vector3(0.65, 0.0, 0.05)
const TV_ROOK := Vector3(1.02, 3.95, 1.59)
const TV_KAARS := Vector3(1.16, 1.07, 1.62)

var uur := 11.0
var winter := false
var demo := false
var demo_t := 0.0
var _keys: Array = []

var cam: Camera3D
var env: Environment
var sky_mat: ProceduralSkyMaterial
var zon: DirectionalLight3D
var maan: DirectionalLight3D
var gras_mat: ShaderMaterial
var kaars: OmniLight3D
var deurgloed: OmniLight3D
var gloedvlak: MeshInstance3D
var gloed_mat: StandardMaterial3D
var ruit_mat: StandardMaterial3D
var rook: GPUParticles3D
var rook_mat: StandardMaterial3D
var label: Label
var hut: Node3D

var deur: Node3D            # scharnierknoop voordeur (of null)
var deur_basis := Basis()
var deur_open := 0.0        # 0..1
var deur_doel := 0.0
var drempel := Vector3.ZERO
var naar_buiten := Vector3.LEFT
var kaars_pos := TV_KAARS
var rook_pos := TV_ROOK
var kaars_niveau := 0.0
var gevonden := {}          # voor het rapport in de log

# Dorpeling
var dorp: Node3D
var d_staat := "erf"
var d_wacht := 2.0
var d_doel := Vector3.ZERO
var binnen_tijd := 8.0
var p_erf := Vector3.ZERO
var p_buiten := Vector3.ZERO
var p_binnen := Vector3.ZERO
var _flikker := 0.0


func _ready() -> void:
	demo = "--demo" in OS.get_cmdline_user_args() or "--demo" in OS.get_cmdline_args()
	_bouw_omgeving()
	_bouw_grond()
	_laad_hut()
	_zoek_hut_knopen()
	_bouw_kaars_en_rook()
	_bouw_dorpeling()
	_bouw_camera()
	_bouw_hud()
	if demo:
		_maak_demo()
	print("[hut3d] gevonden: ", gevonden)


# ---------------------------------------------------------------- omgeving

func _bouw_omgeving() -> void:
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
	env.ssao_radius = 0.8
	env.ssao_intensity = 2.0
	env.glow_enabled = true
	env.glow_intensity = 0.6
	env.glow_bloom = 0.05
	env.glow_hdr_threshold = 1.0
	env.fog_enabled = true
	env.fog_density = 0.0025
	env.fog_sky_affect = 0.0
	var we := WorldEnvironment.new()
	we.environment = env
	add_child(we)

	zon = DirectionalLight3D.new()
	zon.name = "Zon"
	zon.shadow_enabled = true
	zon.directional_shadow_mode = DirectionalLight3D.SHADOW_PARALLEL_4_SPLITS
	zon.directional_shadow_max_distance = 70.0
	zon.light_angular_distance = 0.8   # zachte (PCSS) schaduwranden
	zon.shadow_blur = 1.0
	zon.shadow_bias = 0.03
	zon.shadow_normal_bias = 1.2
	add_child(zon)

	maan = DirectionalLight3D.new()
	maan.name = "Maan"
	maan.shadow_enabled = true
	maan.directional_shadow_mode = DirectionalLight3D.SHADOW_PARALLEL_4_SPLITS
	maan.directional_shadow_max_distance = 50.0
	maan.light_angular_distance = 1.5
	maan.light_color = Color(0.55, 0.66, 1.0)
	maan.sky_mode = DirectionalLight3D.SKY_MODE_LIGHT_ONLY
	add_child(maan)


func _bouw_grond() -> void:
	gras_mat = ShaderMaterial.new()
	gras_mat.shader = load("res://gras.gdshader")
	gras_mat.set_shader_parameter("erf_midden", Vector2(HUT_MIDDEN.x, HUT_MIDDEN.z))
	var pm := PlaneMesh.new()
	pm.size = Vector2(400, 400)
	pm.subdivide_width = 8
	pm.subdivide_depth = 8
	var g := MeshInstance3D.new()
	g.name = "Grond"
	g.mesh = pm
	g.material_override = gras_mat
	g.position.y = -0.01
	add_child(g)

	# Plaatsvervangende bomen en stenen.
	var rng := RandomNumberGenerator.new()
	rng.seed = 7
	var stam_m := StandardMaterial3D.new()
	stam_m.albedo_color = Color(0.30, 0.21, 0.13)
	stam_m.roughness = 0.9
	var blad_m := StandardMaterial3D.new()
	blad_m.albedo_color = Color(0.13, 0.27, 0.10)
	blad_m.roughness = 0.85
	var steen_m := StandardMaterial3D.new()
	steen_m.albedo_color = Color(0.45, 0.44, 0.41)
	steen_m.roughness = 0.9
	for i in 40:
		var pos := _ring_punt(rng, 10.0, 70.0)
		var boom := Node3D.new()
		boom.position = pos
		var s := rng.randf_range(0.8, 1.5)
		boom.scale = Vector3.ONE * s
		boom.rotation.y = rng.randf() * TAU
		var stam := MeshInstance3D.new()
		var cm := CylinderMesh.new()
		cm.top_radius = 0.12; cm.bottom_radius = 0.2; cm.height = 2.0
		stam.mesh = cm; stam.material_override = stam_m; stam.position.y = 1.0
		boom.add_child(stam)
		var lagen := 3
		for k in lagen:
			var kegel := MeshInstance3D.new()
			var km := CylinderMesh.new()
			km.top_radius = 0.0
			km.bottom_radius = 1.6 - k * 0.4
			km.height = 2.0
			km.radial_segments = 10
			kegel.mesh = km; kegel.material_override = blad_m
			kegel.position.y = 2.0 + k * 1.0
			boom.add_child(kegel)
		add_child(boom)
	for i in 25:
		var r := MeshInstance3D.new()
		var sm := SphereMesh.new()
		sm.radius = 0.5; sm.height = 1.0; sm.radial_segments = 8; sm.rings = 5
		r.mesh = sm; r.material_override = steen_m
		r.position = _ring_punt(rng, 6.0, 50.0)
		var s := rng.randf_range(0.3, 1.1)
		r.scale = Vector3(s * rng.randf_range(0.9, 1.6), s * 0.55, s)
		r.rotation.y = rng.randf() * TAU
		add_child(r)


func _ring_punt(rng: RandomNumberGenerator, rmin: float, rmax: float) -> Vector3:
	var a := rng.randf() * TAU
	var r := sqrt(rng.randf_range(rmin * rmin, rmax * rmax))
	return HUT_MIDDEN + Vector3(cos(a) * r, 0, sin(a) * r)


# ---------------------------------------------------------------- hut

func _laad_hut() -> void:
	if ResourceLoader.exists(HUT_RES):
		var ps: PackedScene = load(HUT_RES)
		hut = ps.instantiate()
		gevonden["bron"] = HUT_RES
	else:
		var pad := ProjectSettings.globalize_path("res://").path_join(HUT_BRON)
		var doc := GLTFDocument.new()
		var st := GLTFState.new()
		if doc.append_from_file(pad, st) == OK:
			hut = doc.generate_scene(st)
			gevonden["bron"] = pad
		else:
			push_warning("hut niet gevonden: " + HUT_RES + " of " + pad)
			hut = Node3D.new()
			gevonden["bron"] = "geen"
	hut.name = "Hut"
	add_child(hut)
	# LOD1 als broer, niet als kind: de ankers en de deur komen alleen uit LOD0.
	if ResourceLoader.exists(HUT_LOD1):
		var ver: Node3D = (load(HUT_LOD1) as PackedScene).instantiate()
		ver.name = "HutLOD1"
		add_child(ver)
		_zet_bereik(hut, 0.0, LOD_WISSEL)
		_zet_bereik(ver, LOD_WISSEL, 0.0)
		gevonden["lod1"] = true


func _zet_bereik(n: Node, van: float, tot: float) -> void:
	if n is GeometryInstance3D:
		n.visibility_range_begin = van
		n.visibility_range_end = tot
	for c in n.get_children():
		_zet_bereik(c, van, tot)


func _alle(n: Node, diepte: int, uit: Array) -> void:
	for c in n.get_children():
		uit.append([c, diepte])
		_alle(c, diepte + 1, uit)


func _zoek(pred: Callable) -> Node3D:
	var lijst: Array = []
	_alle(hut, 0, lijst)
	var beste: Node3D = null
	var beste_d := 1 << 30
	for e in lijst:
		var n: Node = e[0]
		if n is Node3D and pred.call(String(n.name).to_lower()) and e[1] < beste_d:
			beste = n
			beste_d = e[1]
	return beste


func _zoek_hut_knopen() -> void:
	var rb := _zoek(func(s): return s.begins_with("rook_bron"))
	rook_pos = rb.global_position if rb else TV_ROOK
	gevonden["rook_bron"] = rb != null
	var ka := _zoek(func(s): return s == "kaars" or s.begins_with("kaars_") or s.begins_with("kaars."))
	kaars_pos = ka.global_position if ka else TV_KAARS
	gevonden["kaars"] = ka != null
	var dr := _zoek(func(s): return s.begins_with("deur_voor_drempel"))
	if dr:
		drempel = dr.global_position
	else:
		var a := deg_to_rad(172.0)
		drempel = HUT_MIDDEN + Vector3(cos(a) * 1.7, 0, -sin(a) * 1.7)
	gevonden["deur_voor_drempel"] = dr != null
	drempel.y = 0.0
	naar_buiten = (drempel - HUT_MIDDEN) * Vector3(1, 0, 1)
	naar_buiten = naar_buiten.normalized()
	var niet := func(s): return not s.contains("drempel") and not s.contains("kozijn")
	deur = _zoek(func(s): return (s.contains("voordeur") or s.contains("deur_voor")) and niet.call(s))
	if deur:
		deur_basis = deur.transform.basis
	gevonden["voordeur"] = String(deur.name) if deur else ""
	var ad := _zoek(func(s): return s.contains("deur") and not s.contains("voordeur") \
		and not s.contains("drempel") and not s.contains("kozijn"))
	gevonden["aanbouwdeur"] = String(ad.name) if ad else ""

	# Ruiten gaan gloeien als de kaars brandt.
	ruit_mat = StandardMaterial3D.new()
	ruit_mat.albedo_color = Color(0.10, 0.11, 0.12)
	ruit_mat.roughness = 0.2
	ruit_mat.emission_enabled = true
	ruit_mat.emission = Color(1.0, 0.62, 0.28)
	ruit_mat.emission_energy_multiplier = 0.0
	var lijst: Array = []
	_alle(hut, 0, lijst)
	var ruiten := 0
	for e in lijst:
		var n: Node = e[0]
		if n is MeshInstance3D and String(n.name).to_lower().begins_with("ruit"):
			n.material_override = ruit_mat
			ruiten += 1
	gevonden["ruiten"] = ruiten


# ---------------------------------------------------------------- kaars, gloed, rook

func _bouw_kaars_en_rook() -> void:
	kaars = OmniLight3D.new()
	kaars.name = "Kaars"
	kaars.position = kaars_pos
	kaars.light_color = Color(1.0, 0.62, 0.30)
	kaars.omni_range = 5.0
	kaars.omni_attenuation = 1.2
	kaars.shadow_enabled = true
	kaars.light_size = 0.05
	kaars.light_energy = 0.0
	add_child(kaars)

	# Licht dat 's avonds uit de deuropening valt.
	deurgloed = OmniLight3D.new()
	deurgloed.name = "Deurgloed"
	deurgloed.position = drempel - naar_buiten * 1.0 + Vector3(0, 1.1, 0)
	deurgloed.light_color = Color(1.0, 0.55, 0.25)
	deurgloed.omni_range = 4.5
	deurgloed.shadow_enabled = true
	deurgloed.light_energy = 0.0
	add_child(deurgloed)

	gloed_mat = StandardMaterial3D.new()
	gloed_mat.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
	gloed_mat.albedo_color = Color(1.0, 0.55, 0.22)
	gloed_mat.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
	gloed_mat.albedo_color.a = 0.0
	gloed_mat.cull_mode = BaseMaterial3D.CULL_DISABLED
	var qm := QuadMesh.new()
	qm.size = Vector2(1.0, 1.9)
	gloedvlak = MeshInstance3D.new()
	gloedvlak.name = "Gloedvlak"
	gloedvlak.mesh = qm
	gloedvlak.material_override = gloed_mat
	gloedvlak.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	add_child(gloedvlak)
	gloedvlak.global_position = drempel - naar_buiten * 0.8 + Vector3(0, 0.95, 0)
	gloedvlak.look_at(gloedvlak.global_position + naar_buiten, Vector3.UP)

	rook = GPUParticles3D.new()
	rook.name = "Rook"
	rook.position = rook_pos
	rook.amount = 48
	rook.lifetime = 6.0
	rook.preprocess = 6.0
	rook.visibility_aabb = AABB(Vector3(-6, -1, -6), Vector3(12, 14, 12))
	var pm := ParticleProcessMaterial.new()
	pm.direction = Vector3(0, 1, 0)
	pm.spread = 12.0
	pm.initial_velocity_min = 0.5
	pm.initial_velocity_max = 0.8
	pm.gravity = Vector3(0.35, 0.12, 0.1)
	pm.damping_min = 0.05
	pm.damping_max = 0.1
	pm.emission_shape = ParticleProcessMaterial.EMISSION_SHAPE_SPHERE
	pm.emission_sphere_radius = 0.1
	pm.angle_min = 0.0
	pm.angle_max = 360.0
	pm.angular_velocity_min = -20.0
	pm.angular_velocity_max = 20.0
	pm.scale_min = 0.5
	pm.scale_max = 0.8
	var sc := Curve.new()
	sc.add_point(Vector2(0, 0.35))
	sc.add_point(Vector2(1, 2.6))
	var sct := CurveTexture.new()
	sct.curve = sc
	pm.scale_curve = sct
	var gr := Gradient.new()
	gr.set_color(0, Color(0.9, 0.9, 0.9, 0.0))
	gr.set_color(1, Color(1, 1, 1, 0.0))
	gr.add_point(0.12, Color(0.85, 0.85, 0.85, 0.6))
	gr.add_point(0.6, Color(0.95, 0.95, 0.95, 0.3))
	var grt := GradientTexture1D.new()
	grt.gradient = gr
	pm.color_ramp = grt
	rook.process_material = pm
	var vm := StandardMaterial3D.new()
	rook_mat = vm
	vm.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
	vm.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
	vm.billboard_mode = BaseMaterial3D.BILLBOARD_PARTICLES
	vm.vertex_color_use_as_albedo = true
	vm.cull_mode = BaseMaterial3D.CULL_DISABLED
	vm.roughness = 1.0
	vm.shadow_to_opacity = false
	var tex := GradientTexture2D.new()
	tex.fill = GradientTexture2D.FILL_RADIAL
	tex.fill_from = Vector2(0.5, 0.5)
	tex.fill_to = Vector2(1.0, 0.5)
	var rg := Gradient.new()
	rg.set_color(0, Color(1, 1, 1, 1))
	rg.set_color(1, Color(1, 1, 1, 0))
	tex.gradient = rg
	vm.albedo_texture = tex
	var q := QuadMesh.new()
	q.size = Vector2(0.7, 0.7)
	q.material = vm
	rook.draw_pass_1 = q
	rook.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	add_child(rook)


# ---------------------------------------------------------------- dorpeling

func _bouw_dorpeling() -> void:
	var zij := naar_buiten.cross(Vector3.UP)
	# Wachtplek buiten, een stap opzij van het scharnier zodat de naar buiten draaiende deur vrij is.
	var weg := zij
	if deur:
		var s_vec := (drempel - deur.global_position) * Vector3(1, 0, 1)
		s_vec -= naar_buiten * s_vec.dot(naar_buiten)
		if s_vec.length() > 0.01: weg = s_vec.normalized()
	p_buiten = drempel + naar_buiten * 1.15 + weg * 0.35
	p_binnen = drempel - naar_buiten * 0.9
	p_erf = drempel + naar_buiten * 4.5 + zij * 2.0
	dorp = Node3D.new()
	dorp.name = "Dorpeling"
	var lijf := MeshInstance3D.new()
	var cap := CapsuleMesh.new()
	cap.radius = 0.22
	cap.height = 1.55
	lijf.mesh = cap
	lijf.position.y = 0.775
	var m := StandardMaterial3D.new()
	m.albedo_color = Color(0.55, 0.32, 0.18)
	m.roughness = 0.8
	lijf.material_override = m
	dorp.add_child(lijf)
	var neus := MeshInstance3D.new()
	var bm := BoxMesh.new()
	bm.size = Vector3(0.1, 0.08, 0.14)
	neus.mesh = bm
	neus.position = Vector3(0, 1.38, -0.24)
	var nm := StandardMaterial3D.new()
	nm.albedo_color = Color(0.85, 0.65, 0.5)
	neus.material_override = nm
	dorp.add_child(neus)
	add_child(dorp)
	dorp.global_position = p_erf
	d_staat = "erf"
	d_wacht = 2.0


func dorp_herstart(binnen: float) -> void:
	binnen_tijd = binnen
	dorp.global_position = p_erf
	dorp.visible = true
	d_staat = "erf"
	d_wacht = 0.0


func _loop_naar(doel: Vector3, dt: float) -> bool:
	var p := dorp.global_position
	var v := doel - p
	v.y = 0
	var stap := LOOPSNELHEID * dt
	if v.length() <= stap:
		dorp.global_position = doel
		return true
	var r := v.normalized()
	dorp.global_position = p + r * stap
	dorp.look_at(dorp.global_position + r, Vector3.UP)
	return false


func _dorp_stap(dt: float) -> void:
	match d_staat:
		"erf":
			d_wacht -= dt
			if d_wacht <= 0: d_staat = "naar_deur"
		"naar_deur":
			if _loop_naar(p_buiten, dt):
				deur_doel = 1.0; d_staat = "wacht_open_in"
		"wacht_open_in":
			if deur_open > 0.95: d_staat = "naar_binnen"
		"naar_binnen":
			var klaar := _loop_naar(p_binnen, dt)
			if (dorp.global_position - drempel).dot(naar_buiten) < -0.35:
				dorp.visible = false
			if klaar:
				deur_doel = 0.0; d_staat = "binnen"; d_wacht = binnen_tijd
		"binnen":
			d_wacht -= dt
			if d_wacht <= 0:
				deur_doel = 1.0; d_staat = "wacht_open_uit"
		"wacht_open_uit":
			if deur_open > 0.95:
				dorp.look_at(dorp.global_position + naar_buiten, Vector3.UP)
				d_staat = "naar_buiten"
		"naar_buiten":
			var klaar := _loop_naar(p_buiten, dt)
			if (dorp.global_position - drempel).dot(naar_buiten) > -0.35:
				dorp.visible = true
			if klaar:
				deur_doel = 0.0; d_staat = "naar_erf"
		"naar_erf":
			if _loop_naar(p_erf, dt):
				d_staat = "erf"; d_wacht = 5.0


func dorp_binnen() -> bool:
	return d_staat in ["binnen", "wacht_open_uit"] or (d_staat == "naar_binnen" and not dorp.visible) \
		or (d_staat == "naar_buiten" and deur_open > 0.3)


# ---------------------------------------------------------------- camera, hud

func _bouw_camera() -> void:
	cam = Camera3D.new()
	cam.set_script(load("res://rts_camera.gd"))
	cam.name = "Camera"
	add_child(cam)
	cam.zet_direct(HUT_MIDDEN, _deur_yaw() + 0.8, deg_to_rad(40), 18.0)
	cam.make_current()
	if demo:
		cam.invoer_aan = false


func _deur_yaw() -> float:
	return atan2(naar_buiten.x, naar_buiten.z)


func _bouw_hud() -> void:
	var cl := CanvasLayer.new()
	add_child(cl)
	var pc := PanelContainer.new()
	pc.position = Vector2(12, 12)
	var sb := StyleBoxFlat.new()
	sb.bg_color = Color(0, 0, 0, 0.45)
	sb.set_content_margin_all(8)
	sb.set_corner_radius_all(4)
	pc.add_theme_stylebox_override("panel", sb)
	label = Label.new()
	label.add_theme_font_size_override("font_size", 16)
	pc.add_child(label)
	cl.add_child(pc)


func _unhandled_input(e: InputEvent) -> void:
	if e is InputEventKey and e.pressed and not e.echo:
		match e.keycode:
			KEY_T: uur = fmod(uur + 3.0, 24.0)
			KEY_F: winter = not winter
			KEY_ESCAPE: get_tree().quit()


# ---------------------------------------------------------------- tijd en licht

func _zon_hoeken(h: float) -> Vector2:
	## (azimut vanaf noord met de klok mee, elevatie) in graden.
	var opkomst := 8.5 if winter else 5.0
	var onder := 16.5 if winter else 21.5
	var max_el := 24.0 if winter else 58.0
	var az_op := 125.0 if winter else 50.0
	var az_onder := 235.0 if winter else 310.0
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
	# noord = -Z, oost = +X
	return Vector3(sin(a) * cos(e), sin(e), -cos(a) * cos(e))


func _kleur_bij(el: float, punten: Array) -> Color:
	# punten: [[el, Color], ...] oplopend
	if el <= punten[0][0]: return punten[0][1]
	for i in range(1, punten.size()):
		if el <= punten[i][0]:
			var f := inverse_lerp(punten[i - 1][0], punten[i][0], el)
			return (punten[i - 1][1] as Color).lerp(punten[i][1], smoothstep(0.0, 1.0, f))
	return punten[-1][1]


func _werk_licht() -> void:
	var zh := _zon_hoeken(uur)
	var el := zh.y
	var d := _richting(zh.x, maxf(el, -1.0))
	zon.look_at_from_position(Vector3.ZERO, -d, Vector3.UP if absf(d.y) < 0.99 else Vector3.FORWARD)
	var dag := smoothstep(-1.0, 6.0, el)
	zon.light_energy = dag * lerpf(1.3, 1.9, smoothstep(2.0, 30.0, el))
	zon.light_color = _kleur_bij(el, [
		[0.0, Color(1.0, 0.42, 0.18)], [6.0, Color(1.0, 0.62, 0.35)],
		[18.0, Color(1.0, 0.86, 0.70)], [35.0, Color(1.0, 0.96, 0.90)]])
	zon.visible = dag > 0.001

	var nacht := 1.0 - smoothstep(-8.0, 0.0, el)
	var md := _richting(fposmod(zh.x + 180.0, 360.0), 38.0)
	maan.look_at_from_position(Vector3.ZERO, -md, Vector3.UP)
	maan.light_energy = nacht * 0.22
	maan.visible = nacht > 0.001

	sky_mat.sky_top_color = _kleur_bij(el, [
		[-14.0, Color(0.008, 0.012, 0.035)], [-5.0, Color(0.05, 0.07, 0.18)],
		[2.0, Color(0.18, 0.28, 0.55)], [20.0, Color(0.20, 0.40, 0.78)]])
	sky_mat.sky_horizon_color = _kleur_bij(el, [
		[-14.0, Color(0.02, 0.03, 0.07)], [-5.0, Color(0.30, 0.20, 0.25)],
		[1.0, Color(0.95, 0.52, 0.30)], [8.0, Color(0.90, 0.72, 0.55)],
		[20.0, Color(0.68, 0.79, 0.90)]])
	sky_mat.ground_horizon_color = sky_mat.sky_horizon_color
	sky_mat.ground_bottom_color = sky_mat.sky_top_color.darkened(0.5)
	sky_mat.sky_energy_multiplier = lerpf(0.35, 1.0, smoothstep(-12.0, 4.0, el))

	env.ambient_light_energy = lerpf(0.12, 0.55, smoothstep(-10.0, 15.0, el))
	env.ambient_light_sky_contribution = lerpf(0.4, 1.0, dag)
	env.ambient_light_color = Color(0.10, 0.13, 0.26)
	env.fog_light_color = sky_mat.sky_horizon_color.darkened(0.1)
	env.tonemap_exposure = lerpf(1.6, 0.85, dag)
	rook_mat.albedo_color = _kleur_bij(el, [[-10.0, Color(0.16, 0.18, 0.24)], [0.0, Color(0.45, 0.40, 0.40)], [12.0, Color(0.80, 0.80, 0.80)]])

	gras_mat.set_shader_parameter("winter", 1.0 if winter else 0.0)
	_werk_kaars(el)
	rook.emitting = winter or el < 2.0


func _werk_kaars(el: float) -> void:
	var donker := 1.0 - smoothstep(2.0, 10.0, el)
	var doel := donker if dorp_binnen() else 0.0
	var dt := get_process_delta_time()
	kaars_niveau = move_toward(kaars_niveau, doel, dt * 0.8)
	_flikker += dt
	var fl := 0.85 + 0.1 * sin(_flikker * 13.0) + 0.06 * sin(_flikker * 31.7 + 1.3) + 0.05 * sin(_flikker * 7.3)
	kaars.light_energy = kaars_niveau * 2.2 * fl
	kaars.visible = kaars_niveau > 0.002
	var open := smoothstep(0.0, 1.0, deur_open)
	deurgloed.light_energy = kaars_niveau * 1.6 * fl * (0.25 + 0.75 * open)
	deurgloed.visible = deurgloed.light_energy > 0.002
	gloed_mat.albedo_color.a = kaars_niveau * 0.85 * open
	gloedvlak.visible = gloed_mat.albedo_color.a > 0.01
	ruit_mat.emission_energy_multiplier = kaars_niveau * 2.5 * fl


# ---------------------------------------------------------------- lus

func _process(dt: float) -> void:
	if demo:
		_demo_stap(dt)
	else:
		uur = fmod(uur + dt * 24.0 / DAG_SECONDEN, 24.0)
	_dorp_stap(dt)
	deur_open = move_toward(deur_open, deur_doel, dt * 1.1)
	if deur:
		var a := smoothstep(0.0, 1.0, deur_open) * DEUR_OPEN_HOEK
		deur.transform.basis = deur_basis * Basis(Vector3.UP, a)
	_werk_licht()
	var h := int(fposmod(uur, 24.0))
	var mi := int(fposmod(uur, 1.0) * 60.0)
	label.text = "%02d:%02d  ·  %s  ·  %s\n[T] +3 uur   [F] seizoen   wiel: zoom   rechts/midden slepen: draaien\nlinks slepen / WASD / rand: pannen   Q/E draaien   PgUp/PgDn kantelen" % [
		h, mi, "winter" if winter else "zomer", d_staat]


# ---------------------------------------------------------------- autopiloot

func _maak_demo() -> void:
	var yd := _deur_yaw()
	var raam := kaars_pos - HUT_MIDDEN
	var yr := atan2(raam.x, raam.z)
	var c := HUT_MIDDEN
	var dfocus := drempel + naar_buiten * 0.6
	# [t, uur, focus, yaw, pitch°, afstand]
	_keys = [
		[0.0, 11.0, c, yd + 0.9, 48.0, 34.0],
		[8.0, 13.0, c, yd + 0.5, 44.0, 28.0],
		[9.0, 20.6, c, yd + 0.5, 40.0, 24.0],
		[14.0, 21.2, dfocus, yd + 0.55, 12.0, 4.2],
		[20.0, 21.7, dfocus, yd + 0.35, 10.0, 3.6],
		[24.0, 23.3, c + Vector3(0, 2.2, 0), yr + 0.2, 16.0, 15.0],
		[30.0, 24.3, c + Vector3(0, 2.2, 0), yr + 0.5, 14.0, 13.0],
		[32.0, 24.8, dfocus, yd + 0.45, 14.0, 4.8],
		[38.0, 26.3, dfocus, yd + 0.3, 16.0, 5.5],
		[40.0, 28.6, c, yd + 1.2, 30.0, 16.0],
		[46.0, 30.2, c, yd + 1.5, 28.0, 18.0],
	]
	dorp.global_position = p_erf
	d_staat = "erf"
	d_wacht = 1e9
	_zet_demo(0.0)


func _demo_stap(dt: float) -> void:
	var vorige := demo_t
	demo_t += dt
	if vorige < 8.0 and demo_t >= 8.0:
		dorp_herstart(17.0)
	_zet_demo(demo_t)


func _zet_demo(t: float) -> void:
	var i := 0
	while i < _keys.size() - 2 and t > _keys[i + 1][0]:
		i += 1
	var a: Array = _keys[i]
	var b: Array = _keys[i + 1]
	var f := smoothstep(0.0, 1.0, clampf(inverse_lerp(a[0], b[0], t), 0.0, 1.0))
	uur = lerpf(a[1], b[1], clampf(inverse_lerp(a[0], b[0], t), 0.0, 1.0))
	cam.zet_direct((a[2] as Vector3).lerp(b[2], f), lerpf(a[3], b[3], f),
		deg_to_rad(lerpf(a[4], b[4], f)), exp(lerpf(log(a[5]), log(b[5]), f)))
