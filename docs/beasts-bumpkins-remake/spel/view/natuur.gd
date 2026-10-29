class_name Natuur
extends RefCounted
## Laadt de natuur- en prop-glb's (assets/, gesynct uit modellen/natuur/), zet er de wind-shader en de steen-shader op
## en past de seizoenstint toe. Een glb: root `<naam>2` -> LOD0 `<naam>` (met kind `<naam>_sneeuw`) + LOD1 `<naam>_lod1`.
## Materialen worden een keer per glb vervangen (de meshes zijn gedeeld tussen instanties), dus een seizoenswissel is
## een handvol set_shader_parameter-aanroepen, niet een per boom.

const LOD_M := 28.0                    # LOD0 tot hier, LOD1 vanaf hier (visibility_range)

## Gebladerte: materiaalnaam -> tint per seizoen [lente, zomer, herfst, winter] in LINEAIRE waarden (README modellen/natuur).
const TINT := {
	"naald_den": [[0.21, 0.37, 0.18], [0.16, 0.30, 0.15], [0.17, 0.28, 0.15], [0.14, 0.24, 0.13]],
	"naald_spar": [[0.23, 0.40, 0.42], [0.19, 0.35, 0.39], [0.19, 0.33, 0.35], [0.16, 0.28, 0.30]],
	"blad_loof": [[0.40, 0.62, 0.24], [0.28, 0.48, 0.20], [0.78, 0.42, 0.12], [0.30, 0.27, 0.22]],
	"blad_loof_jong": [[0.40, 0.62, 0.24], [0.28, 0.48, 0.20], [0.78, 0.42, 0.12], [0.30, 0.27, 0.22]],
	"blad_struik": [[0.30, 0.52, 0.22], [0.19, 0.36, 0.15], [0.60, 0.36, 0.14], [0.30, 0.27, 0.22]],
	"blad_struik_klein": [[0.50, 0.72, 0.30], [0.40, 0.60, 0.24], [0.70, 0.45, 0.20], [0.34, 0.31, 0.26]],
	"tarwe": [[0.55, 0.85, 0.35], [1, 1, 1], [1, 1, 1], [1, 1, 1]],
}
## Materialen die wel de wind-shader krijgen maar geen tint (hout, bloemen, sneeuw, vlagdoek)
const WIND_ZONDER_TINT := ["bast_den", "bast_loof", "bloemen", "sneeuw", "vlag_doek", "akker_blad"]
const SCHORS := ["bast_den", "bast_loof"]

static var _wind_shader: Shader
static var _steen_shader: Shader
static var _bewerkt := {}              # glb-naam -> true
static var _tint_mats: Array = []      # {mat: ShaderMaterial, naam: String, lod1: bool}
static var _steen_mats: Array = []     # ShaderMaterial


static func _pad(naam: String) -> String:
	return "res://assets/%s.glb" % naam


static func bestaat(naam: String) -> bool:
	return ResourceLoader.exists(_pad(naam))


## Een nieuwe instantie van assets/<naam>.glb met shaders en LOD-bereiken. Null als het bestand ontbreekt.
static func instantie(naam: String) -> Node3D:
	if not bestaat(naam):
		push_warning("natuur: %s ontbreekt (sync.ps1 + --import)" % naam)
		return null
	var n: Node3D = (load(_pad(naam)) as PackedScene).instantiate()
	if not _bewerkt.has(naam):
		_bewerkt[naam] = true
		_vervang_materialen(n)
	_zet_lod(n)
	n.name = naam
	return n


static func _meshes(n: Node, uit: Array) -> void:
	if n is MeshInstance3D:
		uit.append(n)
	for c in n.get_children():
		_meshes(c, uit)


static func _vervang_materialen(root: Node) -> void:
	if _wind_shader == null:
		_wind_shader = load("res://shaders/natuur_wind.gdshader")
		_steen_shader = load("res://shaders/natuur_steen.gdshader")
	var lijst: Array = []
	_meshes(root, lijst)
	for mi: MeshInstance3D in lijst:
		var lod1 := (mi.name as String).ends_with("_lod1")
		for s in mi.mesh.get_surface_count():
			var m := mi.mesh.surface_get_material(s) as StandardMaterial3D
			if m == null:
				continue
			var nm := m.resource_name
			if TINT.has(nm) or WIND_ZONDER_TINT.has(nm):
				var sm := _wind_materiaal(m, nm)
				mi.mesh.surface_set_material(s, sm)
				if TINT.has(nm):
					_tint_mats.append({"mat": sm, "naam": nm, "lod1": lod1})
			elif nm.begins_with("rots_") or nm.begins_with("klif_") or nm == "steenhoop":
				var st := ShaderMaterial.new()
				st.shader = _steen_shader
				st.set_shader_parameter("albedo_tex", m.albedo_texture)
				st.set_shader_parameter("normal_tex", m.normal_texture)
				if m.roughness_texture:
					st.set_shader_parameter("orm_tex", m.roughness_texture)
				mi.mesh.surface_set_material(s, st)
				_steen_mats.append(st)


static func _wind_materiaal(m: StandardMaterial3D, nm: String) -> ShaderMaterial:
	var sm := ShaderMaterial.new()
	sm.shader = _wind_shader
	sm.set_shader_parameter("albedo_tex", m.albedo_texture)
	if m.normal_texture:
		sm.set_shader_parameter("normal_tex", m.normal_texture)
	if m.roughness_texture:
		sm.set_shader_parameter("orm_tex", m.roughness_texture)
		sm.set_shader_parameter("use_orm", true)
	var schors := SCHORS.has(nm)
	sm.set_shader_parameter("alpha_kaart", not schors)
	sm.set_shader_parameter("alpha_cut", m.alpha_scissor_threshold if m.transparency == BaseMaterial3D.TRANSPARENCY_ALPHA_SCISSOR else 0.5)
	if nm == "vlag_doek":
		sm.set_shader_parameter("vlag", 1.0)
		sm.set_shader_parameter("vlag_m", 0.16)
		sm.set_shader_parameter("wind_kracht", 1.3)
	if schors:
		sm.set_shader_parameter("doorschijn", 0.0)
	if TINT.has(nm):
		sm.set_shader_parameter("tint", m.albedo_color)
	return sm


## LOD0 tot LOD_M, LOD1 (`_lod1`) vanaf LOD_M; het sneeuwkind van LOD0 volgt LOD0.
static func _zet_lod(root: Node) -> void:
	var lijst: Array = []
	_meshes(root, lijst)
	var heeft_lod1 := false
	for mi: MeshInstance3D in lijst:
		if (mi.name as String).ends_with("_lod1"):
			heeft_lod1 = true
	if not heeft_lod1:
		return
	for mi: MeshInstance3D in lijst:
		if (mi.name as String).ends_with("_lod1"):
			mi.visibility_range_begin = LOD_M
		else:
			mi.visibility_range_end = LOD_M


## Sneeuwkinderen aan of uit (winter) voor een boom-instantie.
static func zet_sneeuwlaag(root: Node, aan: bool) -> void:
	var lijst: Array = []
	_meshes(root, lijst)
	for mi: MeshInstance3D in lijst:
		if (mi.name as String).ends_with("_sneeuw"):
			mi.visible = aan


static func _tint(nm: String, s: int, f: float) -> Color:
	var t: Array = TINT[nm]
	var a: Array = t[s]
	var b: Array = t[(s + 1) % 4]
	var k := smoothstep(0.7, 1.0, f)      # zelfde zachte overgang als Wereld._geblend()
	return Color(lerpf(a[0], b[0], k), lerpf(a[1], b[1], k), lerpf(a[2], b[2], k))


## Seizoen: s = index (lente..winter), f = voortgang in het seizoen 0..1, sneeuw 0..1, nat 0..1.
static func werk_seizoen(s: int, f: float, sneeuw: float, nat: float) -> void:
	for e in _tint_mats:
		var lin := _tint(e["naam"], s, f)
		if e["lod1"]:
			lin = lin.lerp(Color(0.8, 0.85, 0.9), clampf(sneeuw * 1.4 - 0.2, 0.0, 1.0) * 0.55)  # LOD1 heeft geen sneeuwlaag
		(e["mat"] as ShaderMaterial).set_shader_parameter("tint", lin.linear_to_srgb())
	for m: ShaderMaterial in _steen_mats:
		m.set_shader_parameter("sneeuw", sneeuw)
		m.set_shader_parameter("nat", nat)
