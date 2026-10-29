class_name Bumpkin
extends Node3D
## Herbruikbare dorpeling: laadt een geriggde glb (Mixamo-botnamen) en stuurt hem met een AnimationTree.
## Wissel het uiterlijk (leeftijd/sekse) door BUMPKIN_GLB te wijzigen; skelet en animatienamen blijven gelijk.
##
## Animaties (in de glb): idle, lopen, rennen, bouwen, aanval_zwaard, aanval_steen (optioneel: zonder clip gooit hij toch).
## Sidecar `bumpkin_anim.json`: {naam: {loop, duur_s, snelheid_mps, impact_s}}.
## Boom: BlendSpace1D(idle, lopen, rennen op snelheid) -> TimeScale -> Transition(loco | werk=bouwen)
##       -> OneShot(Transition zwaard | steen, alleen bovenlichaam, dus loopbenen blijven doorlopen).
## Model kijkt in Blender naar -Y; glTF (+Y op) zet dat om naar +Z in Godot en de importer draait niet mee:
## het gezicht wijst langs lokale +Z. Daarom yaw = atan2(dx, dz) (+ MODEL_YAW_OFFSET).

signal aangekomen          ## loop_naar() is bij het doel
signal impact(welke: StringName)  ## bouwen (elke lus) en aanval_zwaard op impact_s; steen bij inslag; voor geluid/treffers

const BUMPKIN_GLB := "res://bumpkin/bumpkin_man.glb"   # bumpkin_test.glb is het placeholder-lijf, zelfde skelet
const BUMPKIN_ANIM := "res://bumpkin/bumpkin_anim.json"
const MODEL_YAW_OFFSET := 0.0
const ACCEL := 6.0          # m/s^2
const DRAAI := 10.0         # draaisnelheid (1/s, exponentieel)
const CROSSFADE := 0.25
const BOVENLICHAAM := ["Spine", "Spine1", "Spine2", "Neck", "Head", "LeftShoulder", "RightShoulder",
	"LeftArm", "RightArm", "LeftForeArm", "RightForeArm", "LeftHand", "RightHand", "prop_L", "prop_R"]

var tempo := 1.0            ## 1 = de loopsnelheid uit de sidecar; <1 langzamer (afspeeltempo schaalt mee)
var heeft_model := false

var _model: Node3D
var _speler: AnimationPlayer
var _boom: AnimationTree
var _meta := {
	"idle": {"loop": true, "duur_s": 3.0, "snelheid_mps": 0.0, "impact_s": 0.0},
	"lopen": {"loop": true, "duur_s": 1.0, "snelheid_mps": 1.4, "impact_s": 0.0},
	"rennen": {"loop": true, "duur_s": 0.6, "snelheid_mps": 3.8, "impact_s": 0.0},
	"bouwen": {"loop": true, "duur_s": 1.6, "snelheid_mps": 0.0, "impact_s": 0.4},
	"aanval_zwaard": {"loop": false, "duur_s": 1.0, "snelheid_mps": 0.0, "impact_s": 0.45},
	"aanval_steen": {"loop": false, "duur_s": 1.1, "snelheid_mps": 0.0, "impact_s": 0.5},  # impact_s = release
}
var _hamer: Node3D
var _zwaard: Node3D
var _steen_prop: Node3D
var _hand_r: Node3D
var _worpen: Array = []   # [{mi, van, naar, t, duur, hoogte}]
var _gooi_doel := Vector3.ZERO
var _gooi_wacht := -1.0   # >=0: draait nog naar het doel
var _aanval_soort := &"zwaard"
var _nachtlicht: OmniLight3D
var _rim_mats: Array[StandardMaterial3D] = []

var _doel := Vector3.ZERO
var _onderweg := false
var _rennen := false
var _snelheid := 0.0
var _yaw_doel := 0.0
var _werk_gewenst := false
var _werkt := false
var _werk_t := 0.0
var _werk_impact_gedaan := false
var _aanval_t := -1.0       # <0: geen aanval bezig
var _aanval_impact_gedaan := false


func _ready() -> void:
	_lees_meta()
	_bouw_model()
	_yaw_doel = rotation.y


# ---------------------------------------------------------------- api

func loop_naar(doel: Vector3, rennen := false) -> void:
	_doel = doel
	_rennen = rennen
	_onderweg = true
	werk(false)


func werk(aan: bool) -> void:
	## Hamerlus; start pas als hij stilstaat, loop_naar() stopt hem.
	_werk_gewenst = aan
	if not aan:
		_stop_werk()


func val_aan() -> void:
	## Eenmalige zwaardzwaai over idle of lopen; stopt werken.
	if _aanval_t >= 0.0:
		return
	_start_aanval(&"zwaard")


func gooi_steen(doel: Vector3) -> void:
	## Draait naar het doel, gooit, de steen vliegt in een boog en geeft impact(&"steen") bij inslag.
	if _aanval_t >= 0.0 or _gooi_wacht >= 0.0:
		return
	_onderweg = false
	_stop_werk()
	_werk_gewenst = false
	_gooi_doel = doel
	_gooi_wacht = 0.0
	kijk_naar(doel - global_position)


func kijk_naar(richting: Vector3, direct := false) -> void:
	richting.y = 0.0
	if richting.length() < 0.001:
		return
	_yaw_doel = atan2(richting.x, richting.z) + MODEL_YAW_OFFSET
	if direct:
		rotation.y = _yaw_doel


func _start_aanval(soort: StringName) -> void:
	_stop_werk()
	_werk_gewenst = false
	_aanval_soort = soort
	_aanval_t = 0.0
	_aanval_impact_gedaan = false
	var clip := &"aanval_zwaard" if soort == &"zwaard" else &"aanval_steen"
	if _boom and _speler.has_animation(clip):
		_boom.set("parameters/keuze/transition_request", "zwaard" if soort == &"zwaard" else "steen")
		_boom.set("parameters/aanval/request", AnimationNodeOneShot.ONE_SHOT_REQUEST_FIRE)
	if soort == &"zwaard" and _zwaard:
		_zwaard.visible = true
	if soort == &"steen" and not _heeft_clip(clip):
		_steen_prop = null   # zonder clip geen prop in de hand; de worp zelf blijft


func _heeft_clip(n: String) -> bool:
	return _speler != null and _speler.has_animation(n)


func onderweg() -> bool: return _onderweg
func werkt() -> bool: return _werkt
func aanvallend() -> bool: return _aanval_t >= 0.0
func gooit() -> bool: return _gooi_wacht >= 0.0 or not _worpen.is_empty()
func snelheid() -> float: return _snelheid


func zet_nacht(f: float) -> void:
	## f 0..1: randlicht op de materialen en een zacht meelopend licht, zodat hij 's nachts geen silhouet is.
	for m in _rim_mats:
		m.rim = 0.55 * f
	if _nachtlicht:
		_nachtlicht.light_energy = 0.6 * f
		_nachtlicht.visible = f > 0.01


# ---------------------------------------------------------------- opbouw

func _lees_meta() -> void:
	if not FileAccess.file_exists(BUMPKIN_ANIM):
		return
	var d = JSON.parse_string(FileAccess.get_file_as_string(BUMPKIN_ANIM))
	if d is Dictionary:
		for k in d:
			if _meta.has(k) and d[k] is Dictionary:
				for f in d[k]:
					if d[k][f] != null:      # null (impact_s van loops) laat de standaardwaarde staan
						_meta[k][f] = d[k][f]


func _bouw_model() -> void:
	if ResourceLoader.exists(BUMPKIN_GLB):
		_model = (load(BUMPKIN_GLB) as PackedScene).instantiate()
		add_child(_model)
		_speler = _model.find_child("AnimationPlayer", true, false) as AnimationPlayer
	if _model == null or _speler == null:
		push_warning("bumpkin: glb of AnimationPlayer ontbreekt, capsule als terugval")
		_bouw_capsule()
		return
	heeft_model = true
	_hamer = _model.find_child("prop_hamer", true, false) as Node3D
	_zwaard = _model.find_child("prop_zwaard", true, false) as Node3D
	_steen_prop = _model.find_child("prop_steen", true, false) as Node3D
	_hand_r = _model.find_child("prop_R", true, false) as Node3D
	if _hamer: _hamer.visible = false
	if _zwaard: _zwaard.visible = false
	if _steen_prop: _steen_prop.visible = false
	for n in _meta:
		if _speler.has_animation(n):
			_speler.get_animation(n).loop_mode = Animation.LOOP_LINEAR if _meta[n]["loop"] else Animation.LOOP_NONE
	_bouw_boom()
	_bouw_nacht()


func _bouw_capsule() -> void:
	var lijf := MeshInstance3D.new()
	var cap := CapsuleMesh.new()
	cap.radius = 0.22
	cap.height = 1.55
	lijf.mesh = cap
	lijf.position.y = 0.775
	var m := StandardMaterial3D.new()
	m.albedo_color = Color(0.55, 0.32, 0.18)
	lijf.material_override = m
	add_child(lijf)
	var neus := MeshInstance3D.new()
	var bm := BoxMesh.new()
	bm.size = Vector3(0.1, 0.08, 0.14)
	neus.mesh = bm
	neus.position = Vector3(0, 1.38, 0.24)
	add_child(neus)


func _anim_knoop(naam: StringName) -> AnimationNodeAnimation:
	var a := AnimationNodeAnimation.new()
	a.animation = naam if _speler.has_animation(naam) else &"idle"
	return a


func _bouw_boom() -> void:
	var v_lopen: float = _meta["lopen"]["snelheid_mps"]
	var v_ren: float = _meta["rennen"]["snelheid_mps"]
	var bs := AnimationNodeBlendSpace1D.new()
	bs.min_space = 0.0
	bs.max_space = v_ren * 1.2
	bs.sync = true
	bs.add_blend_point(_anim_knoop(&"idle"), 0.0, -1, &"idle")
	bs.add_blend_point(_anim_knoop(&"lopen"), v_lopen, -1, &"lopen")
	bs.add_blend_point(_anim_knoop(&"rennen"), v_ren, -1, &"rennen")

	var tr := AnimationNodeTransition.new()
	tr.input_count = 2
	tr.set_input_name(0, "loco")
	tr.set_input_name(1, "werk")
	tr.xfade_time = CROSSFADE

	var os := AnimationNodeOneShot.new()
	os.fadein_time = 0.12
	os.fadeout_time = 0.2
	os.filter_enabled = true
	for clip in ["aanval_zwaard", "aanval_steen"]:
		if not _speler.has_animation(clip):
			continue
		var ref := _speler.get_animation(clip)
		for i in ref.get_track_count():
			var p := String(ref.track_get_path(i))
			var bot := p.get_slice(":", 1) if p.contains(":") else ""
			if bot in BOVENLICHAAM:
				os.set_filter_path(ref.track_get_path(i), true)

	var kz := AnimationNodeTransition.new()
	kz.input_count = 2
	kz.set_input_name(0, "zwaard")
	kz.set_input_name(1, "steen")
	kz.xfade_time = 0.0

	var bt := AnimationNodeBlendTree.new()
	bt.add_node("loco", bs, Vector2(0, 0))
	bt.add_node("tempo", AnimationNodeTimeScale.new(), Vector2(200, 0))
	bt.add_node("werkanim", _anim_knoop(&"bouwen"), Vector2(0, 150))
	bt.add_node("basis", tr, Vector2(400, 0))
	bt.add_node("zwaardanim", _anim_knoop(&"aanval_zwaard"), Vector2(400, 150))
	bt.add_node("steenanim", _anim_knoop(&"aanval_steen"), Vector2(400, 300))
	bt.add_node("keuze", kz, Vector2(500, 150))
	bt.add_node("aanval", os, Vector2(600, 0))
	bt.connect_node("tempo", 0, "loco")
	bt.connect_node("basis", 0, "tempo")
	bt.connect_node("basis", 1, "werkanim")
	bt.connect_node("aanval", 0, "basis")
	bt.connect_node("keuze", 0, "zwaardanim")
	bt.connect_node("keuze", 1, "steenanim")
	bt.connect_node("aanval", 1, "keuze")
	bt.connect_node("output", 0, "aanval")

	_boom = AnimationTree.new()
	_boom.name = "AnimationTree"
	_boom.tree_root = bt
	_model.add_child(_boom)                     # root_node ".." = de glb-wortel, net als de speler
	_boom.anim_player = _boom.get_path_to(_speler)
	_boom.active = true
	_boom.set("parameters/basis/transition_request", "loco")


func _bouw_nacht() -> void:
	var lijst: Array[Node] = []
	_verzamel(_model, lijst)
	for n in lijst:
		var mi := n as MeshInstance3D
		if mi == null or mi.mesh == null or mi.name.begins_with("prop_"):
			continue
		for s in mi.mesh.get_surface_count():
			var bron := mi.get_active_material(s) as StandardMaterial3D
			if bron == null:
				continue
			var m := bron.duplicate() as StandardMaterial3D
			m.rim_enabled = true
			m.rim = 0.0
			m.rim_tint = 0.4
			mi.set_surface_override_material(s, m)
			_rim_mats.append(m)
	_nachtlicht = OmniLight3D.new()
	_nachtlicht.name = "Nachtlicht"
	_nachtlicht.position = Vector3(0, 1.9, 0.9)
	_nachtlicht.light_color = Color(1.0, 0.78, 0.55)
	_nachtlicht.omni_range = 3.2
	_nachtlicht.omni_attenuation = 1.0
	_nachtlicht.light_energy = 0.0
	_nachtlicht.visible = false
	_nachtlicht.shadow_enabled = false
	add_child(_nachtlicht)


func _verzamel(n: Node, uit: Array[Node]) -> void:
	uit.append(n)
	for c in n.get_children():
		_verzamel(c, uit)


# ---------------------------------------------------------------- lus

func _stop_werk() -> void:
	_werkt = false
	if _boom:
		_boom.set("parameters/basis/transition_request", "loco")
	if _hamer:
		_hamer.visible = false


func _process(dt: float) -> void:
	_beweeg(dt)
	rotation.y = lerp_angle(rotation.y, _yaw_doel, 1.0 - exp(-DRAAI * dt))
	_werk_stap(dt)
	_aanval_stap(dt)
	if _boom:
		_boom.set("parameters/loco/blend_position", _snelheid / maxf(tempo, 0.1))
		_boom.set("parameters/tempo/scale", tempo)


func _beweeg(dt: float) -> void:
	if not _onderweg:
		_snelheid = move_toward(_snelheid, 0.0, ACCEL * 1.5 * dt)
		return
	var d := _doel - global_position
	d.y = 0.0
	var afstand := d.length()
	var vmax: float = _meta["rennen" if _rennen else "lopen"]["snelheid_mps"] * tempo
	var wil := maxf(minf(vmax, sqrt(2.0 * ACCEL * afstand)), 0.25)
	if afstand > 0.05:
		_yaw_doel = atan2(d.x, d.z) + MODEL_YAW_OFFSET
		# eerst ruim genoeg naar het doel gedraaid, dan pas lopen
		var fout := absf(angle_difference(rotation.y, _yaw_doel))
		wil *= clampf(1.0 - (fout - 0.3) / 0.9, 0.0, 1.0)
	_snelheid = move_toward(_snelheid, wil, ACCEL * dt)
	var stap := _snelheid * dt
	if afstand <= maxf(stap, 0.02):
		global_position = Vector3(_doel.x, global_position.y, _doel.z)
		_onderweg = false
		aangekomen.emit()
	else:
		global_position += d / afstand * stap


func _werk_stap(dt: float) -> void:
	if _werk_gewenst and not _werkt and not _onderweg and _snelheid < 0.05 and _aanval_t < 0.0:
		_werkt = true
		_werk_t = -CROSSFADE   # impact_s telt vanaf het begin van de bouwen-clip
		_werk_impact_gedaan = false
		if _boom:
			_boom.set("parameters/basis/transition_request", "werk")
		if _hamer:
			_hamer.visible = true
	if not _werkt:
		return
	_werk_t += dt
	var duur: float = _meta["bouwen"]["duur_s"]
	var imp: float = _meta["bouwen"]["impact_s"]
	if _werk_t >= duur:
		_werk_t -= duur
		_werk_impact_gedaan = false
	if not _werk_impact_gedaan and _werk_t >= imp:
		_werk_impact_gedaan = true
		impact.emit(&"bouwen")


func _aanval_stap(dt: float) -> void:
	if _gooi_wacht >= 0.0:
		_gooi_wacht += dt
		var fout := absf(angle_difference(rotation.y, _yaw_doel))
		if fout < 0.15 or _gooi_wacht > 0.8:
			_gooi_wacht = -1.0
			_start_aanval(&"steen")
	_werp_stap(dt)
	if _aanval_t < 0.0:
		return
	_aanval_t += dt
	var clip := "aanval_zwaard" if _aanval_soort == &"zwaard" else "aanval_steen"
	var imp: float = _meta[clip]["impact_s"]
	if not _aanval_impact_gedaan and _aanval_t >= imp:
		_aanval_impact_gedaan = true
		if _aanval_soort == &"zwaard":
			impact.emit(&"aanval_zwaard")
		else:
			_laat_los()
	if _aanval_soort == &"steen" and _steen_prop and _heeft_clip(clip) and not _aanval_impact_gedaan:
		_steen_prop.visible = _aanval_t >= float(_meta[clip].get("pak_s", 0.0))   # pak_s: steen gepakt
	if _aanval_t >= float(_meta[clip]["duur_s"]) + 0.1:
		_aanval_t = -1.0
		if _zwaard: _zwaard.visible = false
		if _steen_prop: _steen_prop.visible = false


func _laat_los() -> void:
	if _steen_prop: _steen_prop.visible = false
	var van := global_position + Vector3(0, 1.3, 0) + Vector3(sin(rotation.y), 0, cos(rotation.y)) * 0.3
	if _hand_r and heeft_model and _speler.has_animation("aanval_steen"):
		van = _hand_r.global_position
	var mi := MeshInstance3D.new()
	var sm := SphereMesh.new()
	sm.radius = 0.06; sm.height = 0.12; sm.radial_segments = 8; sm.rings = 4
	mi.mesh = sm
	var m := StandardMaterial3D.new()
	m.albedo_color = Color(0.45, 0.44, 0.41)
	m.roughness = 0.9
	mi.material_override = m
	mi.top_level = true
	add_child(mi)
	mi.global_position = van
	var dist := van.distance_to(_gooi_doel)
	_worpen.append({"mi": mi, "van": van, "naar": _gooi_doel, "t": 0.0,
		"duur": maxf(0.35, dist / 9.0), "hoogte": 0.5 + 0.12 * dist})


func _werp_stap(dt: float) -> void:
	for w in _worpen.duplicate():
		w["t"] += dt
		var f := clampf(w["t"] / w["duur"], 0.0, 1.0)
		var p: Vector3 = (w["van"] as Vector3).lerp(w["naar"], f)
		p.y += 4.0 * w["hoogte"] * f * (1.0 - f)
		(w["mi"] as Node3D).global_position = p
		if f >= 1.0:
			(w["mi"] as Node3D).queue_free()
			_worpen.erase(w)
			impact.emit(&"steen")
