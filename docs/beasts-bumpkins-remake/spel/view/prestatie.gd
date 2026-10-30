class_name Prestatie
extends Node
## Alleen op mobiel (main.gd: `OS.has_feature("mobile")` of `--prestatie` op de pc): zet de mobiele beeldinstellingen en
## logt elke s fps, frametijd, gpu/cpu-rendertijd en draw calls (logcat-tag `godot`, regels `[prestatie]`).
## Instellingen: STANDAARD hieronder, per sleutel te overschrijven met `user://prestatie.cfg` (sectie [beeld]); dat bestand
## wordt elke 2 s opnieuw gelezen als het veranderd is, dus op de telefoon live te proberen:
##   adb shell run-as nl.abons.beasts_remake sh -c 'cat > files/prestatie.cfg' < prestatie.cfg
## De pc ziet hier niets van: zonder `mobile` en zonder `--prestatie` wordt de node niet gemaakt.

const STANDAARD := {
	"schaal": 1.0,          # Viewport.scaling_3d_scale
	"fsr": false,           # true = FSR1-opschaling in plaats van bilineair
	"msaa": -1,             # Viewport.MSAA_* (0 uit, 1 x2, 2 x4, 3 x8); -1 = projectinstelling laten (msaa_3d=2 = x4)
	"glow": true,
	"ssao": true,
	"fog": true,
	"schaduw": 2048,        # directional-atlas in px; 0 = zon- en maanschaduw uit
	"splits": 4,            # 1, 2 of 4
	"schaduw_afstand": 140.0,
	"zacht": 3,             # soft-shadow-kwaliteit 0..5
	"mist": true,           # mist van oorlog-quad (alleen meten: uit laat de kaart zien)
	"water": true,          # alleen meten
	"max_fps": 0,           # 0 = geen grens
	"vsync": true,
	"lucht": true,          # false: effen achtergrond + kleur-omgevingslicht (geen sky-radiance)
	"lucht_proces": -1,     # Sky.ProcessMode (0 auto, 1 kwaliteit, 2 incrementeel, 3 realtime); -1 = laten
	"radiance": -1,         # Sky.RadianceSize (0=32 .. 3=256 .. 6=2048); -1 = laten
	"terrein": true,        # alleen meten: terreinmesh verbergen
	"bomen": true,          # alleen meten
	"decoratie": true,      # alleen meten
	"lod_m": 0.0,           # >0: LOD0->LOD1-wissel van bomen/struiken op deze afstand (Natuur.LOD_M = 28)
	"log": true,
	"toon": true,           # fps-regel linksboven in beeld
	"afstand": 0.0,         # >0: camera op deze afstand zetten (meten ingezoomd/uitgezoomd)
}

static var start_log := OS.has_feature("mobile") or OS.get_cmdline_user_args().has("--prestatie")
## Goedkopere shaders/paden voor de telefoon-gpu; op de pc te bekijken met `-- --mobiel_beeld`.
static var mobiel_beeld := OS.has_feature("mobile") or OS.get_cmdline_user_args().has("--mobiel_beeld")

var main: Node
var instelling := {}
var _vp: Viewport
var _mtijd := 0
var _lees_t := 0.0
var _n := 0
var _som := 0.0
var _max := 0.0
var _trage := 0
var _gpu := 0.0
var _cpu := 0.0
var sim_us := 0             # main.gd telt hier de tijd van w.vooruit bij
var _script_us := 0         # alle _process samen: van _begin (prioriteit -1000) tot _eind (1000)
var _t0 := 0
var _eind: Node
var _label: Label
var _frame_nr := 0


class Eind extends Node:
	var p: Prestatie
	func _process(_dt: float) -> void:
		p._script_us += Time.get_ticks_usec() - p._t0


## Starttijd-merk naar de log: ms sinds de engine startte (Time.get_ticks_msec) en sinds het vorige merk.
static var _vorig := 0
static func merk(wat: String) -> void:
	if not start_log:
		return
	var t := Time.get_ticks_msec()
	print("[start] %6d ms  +%5d  %s" % [t, t - _vorig, wat])
	_vorig = t


func bouw(m: Node) -> void:
	main = m
	_vp = get_viewport()
	process_priority = -1000
	_eind = Eind.new()
	_eind.p = self
	_eind.process_priority = 1000
	add_child(_eind)
	var laag := CanvasLayer.new()
	laag.layer = 120
	add_child(laag)
	_label = Label.new()
	_label.position = Vector2(340, 4)   # naast de minikaart
	_label.add_theme_font_size_override("font_size", 20)
	_label.add_theme_color_override("font_color", Color(1, 1, 0.6))
	_label.add_theme_color_override("font_outline_color", Color.BLACK)
	_label.add_theme_constant_override("outline_size", 6)
	_label.mouse_filter = Control.MOUSE_FILTER_IGNORE
	laag.add_child(_label)
	RenderingServer.viewport_set_measure_render_time(_vp.get_viewport_rid(), true)
	_lees(true)


func _lees(eerst: bool) -> void:
	var pad := "user://prestatie.cfg"
	var mt := FileAccess.get_modified_time(pad) if FileAccess.file_exists(pad) else 0
	if not eerst and mt == _mtijd:
		return
	_mtijd = mt
	instelling = STANDAARD.duplicate()
	if mt != 0:
		var cf := ConfigFile.new()
		if cf.load(pad) == OK and cf.has_section("beeld"):
			for k in cf.get_section_keys("beeld"):
				instelling[k] = cf.get_value("beeld", k)
	_pas_toe()
	print("[prestatie] instellingen ", instelling)


func _pas_toe() -> void:
	var s: Dictionary = instelling
	_vp.scaling_3d_mode = Viewport.SCALING_3D_MODE_FSR if s["fsr"] else Viewport.SCALING_3D_MODE_BILINEAR
	_vp.scaling_3d_scale = float(s["schaal"])
	if int(s["msaa"]) >= 0:
		_vp.msaa_3d = int(s["msaa"]) as Viewport.MSAA
	var licht: Licht = main.licht
	licht.env.glow_enabled = s["glow"]
	licht.env.ssao_enabled = s["ssao"]
	licht.env.fog_enabled = s["fog"]
	var maat := int(s["schaduw"])
	licht.zon.shadow_enabled = maat > 0
	licht.maan.shadow_enabled = maat > 0
	if maat > 0:
		RenderingServer.directional_shadow_atlas_set_size(maat, true)
	var modus := {1: DirectionalLight3D.SHADOW_ORTHOGONAL, 2: DirectionalLight3D.SHADOW_PARALLEL_2_SPLITS}.get(int(s["splits"]), DirectionalLight3D.SHADOW_PARALLEL_4_SPLITS) as DirectionalLight3D.ShadowMode
	licht.zon.directional_shadow_mode = modus
	licht.maan.directional_shadow_mode = modus
	licht.zon.directional_shadow_max_distance = float(s["schaduw_afstand"])
	RenderingServer.directional_soft_shadow_filter_set_quality(int(s["zacht"]) as RenderingServer.ShadowQuality)
	RenderingServer.positional_soft_shadow_filter_set_quality(int(s["zacht"]) as RenderingServer.ShadowQuality)
	_label.visible = s["toon"]
	Engine.max_fps = int(s["max_fps"])
	DisplayServer.window_set_vsync_mode(DisplayServer.VSYNC_ENABLED if s["vsync"] else DisplayServer.VSYNC_DISABLED)
	if float(s["afstand"]) > 0.0:
		main.cam.set("doel_afstand", float(s["afstand"]))
	var env: Environment = licht.env
	if s["lucht"]:
		env.background_mode = Environment.BG_SKY
		env.ambient_light_source = Environment.AMBIENT_SOURCE_SKY
		env.reflected_light_source = Environment.REFLECTION_SOURCE_SKY
	else:
		env.background_mode = Environment.BG_COLOR
		env.background_color = Color(0.45, 0.6, 0.8)
		env.ambient_light_source = Environment.AMBIENT_SOURCE_COLOR
		env.reflected_light_source = Environment.REFLECTION_SOURCE_DISABLED
	if int(s["lucht_proces"]) >= 0:
		env.sky.process_mode = int(s["lucht_proces"]) as Sky.ProcessMode
	if int(s["radiance"]) >= 0:
		env.sky.radiance_size = int(s["radiance"]) as Sky.RadianceSize
	var tv: Node = main.view.terrein
	for naam in ["Terrein", "Bomen", "Decoratie"]:
		var n: Node3D = tv.get_node_or_null(naam)
		if n != null:
			n.visible = s[{"Terrein": "terrein", "Bomen": "bomen", "Decoratie": "decoratie"}[naam]]
	if float(s["lod_m"]) > 0.0:
		var lod := float(s["lod_m"])
		for naam in ["Bomen", "Decoratie"]:
			var n: Node = tv.get_node_or_null(naam)
			if n == null:
				continue
			for mi: MeshInstance3D in n.find_children("*", "MeshInstance3D", true, false):
				if (mi.name as String).ends_with("_lod1"):
					mi.visibility_range_begin = lod
				elif mi.visibility_range_end > 0.0:
					mi.visibility_range_end = lod
	var mist: Node3D = main.get_node_or_null("Mist")
	if mist != null:
		mist.visible = bool(s["mist"]) and main.w.mist.aan
	var wm: ShaderMaterial = main.view.terrein.water_mat
	for mi in main.view.terrein.find_children("*", "MeshInstance3D", true, false):
		if (mi as MeshInstance3D).material_override == wm:
			mi.visible = s["water"]


func _process(dt: float) -> void:
	_t0 = Time.get_ticks_usec()
	if _frame_nr < 6 or dt > 0.5:
		merk("frame %d (dt %.0f ms)" % [_frame_nr, dt * 1000.0])
	_frame_nr += 1
	_lees_t += dt
	if _lees_t >= 2.0:
		_lees_t = 0.0
		_lees(false)
	_n += 1
	_som += dt
	_max = maxf(_max, dt)
	if dt > 1.0 / 28.0:
		_trage += 1
	var rid := _vp.get_viewport_rid()
	_gpu += RenderingServer.viewport_get_measured_render_time_gpu(rid)
	_cpu += RenderingServer.viewport_get_measured_render_time_cpu(rid) + RenderingServer.get_frame_setup_time_cpu()
	if _som >= 1.0:
		var calls := RenderingServer.get_rendering_info(RenderingServer.RENDERING_INFO_TOTAL_DRAW_CALLS_IN_FRAME)
		_label.text = "fps %.0f · %.0f ms (max %.0f) · gpu %.0f ms · script %.1f ms · calls %d · %d%%" % [
			_n / _som, _som / _n * 1000.0, _max * 1000.0, _gpu / _n, _script_us / 1000.0 / _n, calls, roundi(float(instelling["schaal"]) * 100.0)]
		if instelling.get("log", true):
			var cam: Node = main.cam
			print("[prestatie] fps %.1f  frame %.1f ms (max %.0f, >36ms %d/%d)  gpu %.1f ms  rcpu %.1f ms  script %.1f ms (sim %.1f)  calls %d  obj %d  prims %dk  vram %d MB  afstand %.0f" % [
				_n / _som, _som / _n * 1000.0, _max * 1000.0, _trage, _n, _gpu / _n, _cpu / _n,
				_script_us / 1000.0 / _n, sim_us / 1000.0 / _n,
				calls,
				RenderingServer.get_rendering_info(RenderingServer.RENDERING_INFO_TOTAL_OBJECTS_IN_FRAME),
				RenderingServer.get_rendering_info(RenderingServer.RENDERING_INFO_TOTAL_PRIMITIVES_IN_FRAME) / 1000,
				RenderingServer.get_rendering_info(RenderingServer.RENDERING_INFO_VIDEO_MEM_USED) / 1048576,
				float(cam.get("afstand"))])
		_n = 0; _som = 0.0; _max = 0.0; _trage = 0; _gpu = 0.0; _cpu = 0.0; _script_us = 0; sim_us = 0
