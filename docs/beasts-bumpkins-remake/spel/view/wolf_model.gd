class_name WolfModel
extends RefCounted
## De wolf (missie 2 en 3): assets/wolf[_trellis].glb of assets/donkere_wolf[_trellis].glb + wolf_anim.json (uit modellen/dieren/wolf.py;
## clips idle, lopen, rennen, bijten, dood). Kijkt langs +Z, zoals Bumpkin. `werk()` kiest de clip uit de sim-toestand
## (sim/wolf.gd): lopen/rennen op de loopsnelheid, bijten en dood op `slag` (deterministisch, zoals de sim), en het karkas
## zakt weg als het vergaat. Zonder glb (assets/ staat niet in git) de oude placeholder uit meshes.
## Soorten: &"wolf" (grijs) en &"donkere_wolf" (zwart met witte borst, sprites dw_*; iets groter).

const GLB := {&"wolf": "res://assets/wolf.glb", &"donkere_wolf": "res://assets/donkere_wolf.glb"}
## AI-model (TRELLIS, modellen/dieren/wolf_trellis.py): zelfde skelet, clips en assen; spel.json wolf_model.
const GLB_TRELLIS := {&"wolf": "res://assets/wolf_trellis.glb", &"donkere_wolf": "res://assets/donkere_wolf_trellis.glb"}
## TRELLIS-mesh vervormd naar de Tripo-referentie, met geprojecteerde textuur (modellen/dieren/wolf_tripo.py).
const GLB_TRIPO := {&"wolf": "res://assets/wolf_tripo.glb", &"donkere_wolf": "res://assets/donkere_wolf_tripo.glb"}
const ANIM := "res://assets/wolf_anim.json"
const SCHAAL := {&"wolf": 1.0, &"donkere_wolf": 1.08}
const REN_MPS := 1.5            ## boven deze sim-snelheid de galop

const GRIJS := Color(0.47, 0.47, 0.46)
const DONKER := Color(0.33, 0.33, 0.33)
const LICHT := Color(0.74, 0.73, 0.71)
const HEUP_Y := 0.52
const BEEN := 0.46


static func _mat(kleur: Color, ruw := 0.95, emissie := 0.0) -> StandardMaterial3D:
	var m := StandardMaterial3D.new()
	m.albedo_color = kleur
	m.roughness = ruw
	if emissie > 0.0:
		m.emission_enabled = true
		m.emission = kleur
		m.emission_energy_multiplier = emissie
	return m


static func _mesh(ouder: Node3D, mesh: Mesh, mat: Material, pos: Vector3, rot := Vector3.ZERO, schaal := Vector3.ONE) -> MeshInstance3D:
	var mi := MeshInstance3D.new()
	mi.mesh = mesh
	mi.material_override = mat
	mi.position = pos
	mi.rotation = rot
	mi.scale = schaal
	ouder.add_child(mi)
	return mi


static func _capsule(r: float, h: float) -> CapsuleMesh:
	var c := CapsuleMesh.new()
	c.radius = r
	c.height = h
	c.radial_segments = 12
	c.rings = 4
	return c


static func _bol(r: float) -> SphereMesh:
	var s := SphereMesh.new()
	s.radius = r
	s.height = r * 2.0
	s.radial_segments = 12
	s.rings = 6
	return s


static func _kegel(r: float, h: float) -> CylinderMesh:
	var c := CylinderMesh.new()
	c.top_radius = 0.0
	c.bottom_radius = r
	c.height = h
	c.radial_segments = 6
	c.rings = 1
	return c


## Glb-pad per soort: spel.json `wolf_model` ("tripo" | "trellis" | "procedureel"; voor vergelijkingsframes overschrijft
## `-- --wolf_model=procedureel` dat), terugval op de procedurele glb.
static func glb_pad(soort: StringName) -> String:
	var d = Gegevens.lees(Gegevens.SPEL)
	var keuze := String(d.get("wolf_model", "procedureel")) if d is Dictionary else "procedureel"
	for a in OS.get_cmdline_user_args():
		if a.begins_with("--wolf_model="):
			keuze = a.get_slice("=", 1)
	var ai := {"trellis": GLB_TRELLIS, "tripo": GLB_TRIPO}
	if ai.has(keuze):
		var t: String = ai[keuze].get(soort, ai[keuze][&"wolf"])
		if ResourceLoader.exists(t):
			return t
	return GLB.get(soort, GLB[&"wolf"])


## Wezen zonder eigen wolf-glb (missie 4: zombie): spel.json `wezen_model.<soort>` = {glb, terugval, tint, schaal}.
## Keuze: `-- --<soort>_model=glb|boom|wolf`, anders glb als die er is, anders de terugval. Geeft {} voor een wolf.
static func wezen_cfg(soort: StringName) -> Dictionary:
	if GLB.has(soort):
		return {}
	var d = Gegevens.lees(Gegevens.SPEL)
	var c: Dictionary = d.get("wezen_model", {}).get(String(soort), {}) if d is Dictionary else {}
	if c.is_empty():
		return {}
	c = c.duplicate()
	var keuze := ""
	for a in OS.get_cmdline_user_args():
		if a.begins_with("--%s_model=" % soort):
			keuze = a.get_slice("=", 1)
	if keuze == "":
		keuze = "glb" if ResourceLoader.exists(String(c.get("glb", ""))) else String(c.get("terugval", "wolf"))
	if keuze == "glb" and not ResourceLoader.exists(String(c.get("glb", ""))):
		keuze = String(c.get("terugval", "wolf"))
	c["keuze"] = keuze
	return c


static func maak(soort: StringName = &"wolf") -> Node3D:
	var wc := wezen_cfg(soort)
	if not wc.is_empty():
		return _maak_wezen(soort, wc)
	var pad := glb_pad(soort)
	if not ResourceLoader.exists(pad):
		return _placeholder()
	var n := Node3D.new()
	n.name = "Wolf"
	var lijf: Node3D = (load(pad) as PackedScene).instantiate()
	lijf.name = "Lijf"
	lijf.scale = Vector3.ONE * float(SCHAAL.get(soort, 1.0))
	n.add_child(lijf)
	var ap := _speler(lijf)
	if ap:
		var d = Gegevens.lees(ANIM)
		for naam in ap.get_animation_list():
			if d is Dictionary and d.has(naam) and d[naam].get("loop", false):
				ap.get_animation(naam).loop_mode = Animation.LOOP_LINEAR
		ap.play(&"idle")
	_hp(n)
	return n


static func _speler(n: Node) -> AnimationPlayer:
	if n is AnimationPlayer:
		return n
	for c in n.get_children():
		var r := _speler(c)
		if r:
			return r
	return null


## Blokken-wolf zonder glb (poten aan scharnieren, zie werk_placeholder).
static func _placeholder() -> Node3D:
	var n := Node3D.new()
	n.name = "Wolf"
	var lijf := Node3D.new()          # alles behalve het hp-balkje: kantelt bij het omvallen
	lijf.name = "Lijf"
	n.add_child(lijf)
	var grijs := _mat(GRIJS)
	var donker := _mat(DONKER)
	var licht := _mat(LICHT)
	# romp langs Z, rug donkerder
	_mesh(lijf, _capsule(0.19, 0.95), grijs, Vector3(0, 0.60, 0), Vector3(PI * 0.5, 0, 0), Vector3(1.0, 1.0, 1.05))
	_mesh(lijf, _capsule(0.12, 0.7), donker, Vector3(0, 0.73, -0.02), Vector3(PI * 0.5, 0, 0), Vector3(1.1, 1.0, 0.6))
	# borst en keel (licht), nek
	_mesh(lijf, _bol(0.21), licht, Vector3(0, 0.62, 0.33), Vector3.ZERO, Vector3(1.0, 1.1, 0.9))
	_mesh(lijf, _capsule(0.13, 0.38), grijs, Vector3(0, 0.74, 0.42), Vector3(-0.9, 0, 0))
	# kop: schedel, snuit, neus, oren, ogen
	var kop := Node3D.new()
	kop.name = "Kop"
	kop.position = Vector3(0, 0.86, 0.52)
	lijf.add_child(kop)
	_mesh(kop, _bol(0.13), grijs, Vector3.ZERO, Vector3.ZERO, Vector3(1.0, 0.9, 1.05))
	_mesh(kop, _capsule(0.065, 0.26), licht, Vector3(0, -0.035, 0.14), Vector3(PI * 0.5, 0, 0), Vector3(1.0, 1.0, 0.85))
	_mesh(kop, _bol(0.032), _mat(Color(0.05, 0.05, 0.05), 0.4), Vector3(0, -0.02, 0.27))
	_mesh(kop, _kegel(0.055, 0.14), donker, Vector3(-0.07, 0.13, -0.02), Vector3(0, 0, 0.2))
	_mesh(kop, _kegel(0.055, 0.14), donker, Vector3(0.07, 0.13, -0.02), Vector3(0, 0, -0.2))
	var oog := _mat(Color(1.0, 0.12, 0.08), 0.3, 2.5)
	_mesh(kop, _bol(0.018), oog, Vector3(-0.055, 0.035, 0.1))
	_mesh(kop, _bol(0.018), oog, Vector3(0.055, 0.035, 0.1))
	# vier poten aan een heup/schouder-scharnier (draait om X)
	var i := 0
	for p in [Vector3(-0.1, HEUP_Y, 0.3), Vector3(0.1, HEUP_Y, 0.3), Vector3(-0.1, HEUP_Y, -0.32), Vector3(0.1, HEUP_Y, -0.32)]:
		var sch := Node3D.new()
		sch.name = "Poot%d" % i
		sch.position = p
		lijf.add_child(sch)
		var bm := CylinderMesh.new()
		bm.top_radius = 0.055
		bm.bottom_radius = 0.035
		bm.height = BEEN
		bm.radial_segments = 6
		bm.rings = 1
		_mesh(sch, bm, grijs if i < 2 else donker, Vector3(0, -BEEN * 0.5, 0))
		_mesh(sch, _bol(0.045), licht, Vector3(0, -BEEN + 0.01, 0.03), Vector3.ZERO, Vector3(1.0, 0.6, 1.4))
		i += 1
	# staart: hangt naar achteren en omlaag, bossig
	var st := Node3D.new()
	st.name = "Staart"
	st.position = Vector3(0, 0.68, -0.5)
	lijf.add_child(st)
	_mesh(st, _capsule(0.075, 0.5), donker, Vector3(0, -0.12, -0.18), Vector3(-2.4, 0, 0))
	_hp(n)
	return n


static func _maak_wezen(soort: StringName, wc: Dictionary) -> Node3D:
	match String(wc["keuze"]):
		"glb":      # eigen glb met dezelfde clips als de wolf (idle, lopen, rennen, bijten, dood)
			var n := Node3D.new()
			n.name = String(soort).capitalize()
			var lijf: Node3D = (load(String(wc["glb"])) as PackedScene).instantiate()
			lijf.name = "Lijf"
			n.add_child(lijf)
			var ap := _speler(lijf)
			if ap:
				for naam in ap.get_animation_list():
					if naam in [&"idle", &"lopen", &"rennen"]:
						ap.get_animation(naam).loop_mode = Animation.LOOP_LINEAR
				if ap.has_animation(&"idle"):
					ap.play(&"idle")
			_hp(n)
			return n
		"boom":     # den met ogen (view/missie_props.gd)
			var n := Node3D.new()
			n.name = String(soort).capitalize()
			var lijf: Node3D = MissieProps.maak("boom_ogen")
			lijf.name = "Lijf"
			n.add_child(lijf)
			_hp(n)
			(n.get_node("Hp") as Node3D).position.y = 3.6
			return n
	# wolf met tint en schaal: van een gewone wolf te onderscheiden
	var w := maak(&"wolf")
	var lijf2 := w.get_node("Lijf") as Node3D
	lijf2.scale *= float(wc.get("schaal", 1.0))
	var t: Array = wc.get("tint", [0.5, 0.65, 0.4])
	var over := StandardMaterial3D.new()
	over.albedo_color = Color(float(t[0]), float(t[1]), float(t[2]), 0.45)
	over.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
	over.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
	_tint(lijf2, over)
	return w


static func _tint(n: Node, m: Material) -> void:
	if n is GeometryInstance3D:
		(n as GeometryInstance3D).material_overlay = m
	for c in n.get_children():
		_tint(c, m)


## Hp-balkje (WolvenView draait het naar de camera).
static func _hp(n: Node3D) -> void:
	var hp := Node3D.new()
	hp.name = "Hp"
	hp.position = Vector3(0, 1.25, 0)
	hp.visible = false
	n.add_child(hp)
	var q := QuadMesh.new()
	q.size = Vector2(0.62, 0.09)
	var bg := StandardMaterial3D.new()
	bg.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
	bg.albedo_color = Color(0.12, 0.05, 0.04)
	bg.no_depth_test = true
	bg.render_priority = 1
	var achter := _mesh(hp, q, bg, Vector3.ZERO)
	achter.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	var q2 := QuadMesh.new()
	q2.size = Vector2(0.58, 0.06)
	q2.center_offset = Vector3(0.29, 0, 0)     # schaalt vanaf links
	var vg := StandardMaterial3D.new()
	vg.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
	vg.albedo_color = Color(0.85, 0.2, 0.12)
	vg.no_depth_test = true
	vg.render_priority = 2
	var vul := _mesh(hp, q2, vg, Vector3(-0.29, 0, 0.001))
	vul.name = "Vul"
	vul.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF


## Eén frame. `tempo` = speltempo (0 bij pauze); `fase`/`t`/`dt` alleen voor de placeholder.
static func werk(n: Node3D, wf: Wolf, fase: float, t: float, dt: float, tempo := 1.0) -> void:
	var lijf := n.get_node("Lijf") as Node3D
	var ap := _speler(lijf)
	if lijf.has_node("Ogen"):
		_werk_boom(lijf, wf, dt)
	elif ap == null:
		_werk_placeholder(n, wf, fase, t, dt)
	else:
		_werk_glb(ap, lijf, wf, tempo)
	var hp := n.get_node("Hp") as Node3D
	hp.visible = wf.leeft() and (wf.hp < wf.hp_max or wf.geraakt < 3.0)
	if hp.visible:
		(hp.get_node("Vul") as Node3D).scale.x = maxf(0.001, float(wf.hp) / float(wf.hp_max))


## Den met ogen: ogen gaan open als er een dorpeling in de buurt is (Wolf.kijkt_naar) en volgen hem; dood = omvallen.
static func _werk_boom(lijf: Node3D, wf: Wolf, dt: float) -> void:
	var ogen := lijf.get_node("Ogen") as Node3D
	var open := 1.0 if wf.leeft() and (wf.kijkt_naar != null or wf.toestand != Wolf.ROAM) else 0.1
	ogen.scale.y = move_toward(ogen.scale.y, open, dt * 4.0)
	if wf.toestand == Wolf.DYING or wf.toestand == Wolf.DEAD:
		var u := 1.0 if wf.toestand == Wolf.DEAD else wf.slag
		lijf.rotation.x = -PI * 0.5 * u
		if wf.toestand == Wolf.DEAD:
			lijf.position.y = -0.6 * clampf((wf.slag - 0.7) / 0.3, 0.0, 1.0)
	else:
		lijf.rotation.x = 0.0


static func _clip_v(naam: String) -> float:
	var d = Gegevens.lees(ANIM)
	return float(d[naam]["snelheid_mps"]) if d is Dictionary and d.has(naam) else 1.0


## Clip op een vaste plek (bijten/dood volgen `slag` van de sim, dus geen eigen klok).
static func _zet(ap: AnimationPlayer, naam: StringName, u: float) -> void:
	if ap.current_animation != naam:
		ap.play(naam, 0.12)
	ap.speed_scale = 0.0
	ap.seek(clampf(u, 0.0, 1.0) * ap.get_animation(naam).length, true)


static func _speel(ap: AnimationPlayer, naam: StringName, snelheid: float) -> void:
	if ap.current_animation != naam:
		ap.play(naam, 0.25)
	ap.speed_scale = snelheid


static func _werk_glb(ap: AnimationPlayer, lijf: Node3D, wf: Wolf, tempo: float) -> void:
	lijf.position.y = 0.0
	match wf.toestand:
		Wolf.DYING:
			_zet(ap, &"dood", wf.slag)
		Wolf.DEAD:
			_zet(ap, &"dood", 1.0)
			lijf.position.y = -0.5 * clampf((wf.slag - 0.7) / 0.3, 0.0, 1.0)   # laatste 30 %: zakt weg
		Wolf.ATTACK:
			_zet(ap, &"bijten", wf.slag)
		_:
			if wf.snelheid_mps > 0.05:
				var clip := &"rennen" if wf.snelheid_mps > REN_MPS else &"lopen"
				_speel(ap, clip, wf.snelheid_mps * tempo / _clip_v(String(clip)))
			else:
				_speel(ap, &"idle", tempo)


static func _werk_placeholder(n: Node3D, wf: Wolf, fase: float, t: float, dt: float) -> void:
	var lijf := n.get_node("Lijf") as Node3D
	var kop := lijf.get_node("Kop") as Node3D
	var st := lijf.get_node("Staart") as Node3D
	var loopt := wf.snelheid_mps > 0.05 and wf.leeft()
	var zwaai := 0.0
	if loopt:
		zwaai = (0.75 if wf.snelheid_mps > 1.5 else 0.45)
	for i in 4:
		var p := lijf.get_node("Poot%d" % i) as Node3D
		# diagonale paren (draf): links-voor met rechts-achter
		var tegen := 1.0 if (i == 0 or i == 3) else -1.0
		p.rotation.x = lerp_angle(p.rotation.x, sin(fase) * zwaai * tegen, minf(1.0, dt * 14.0))
	var kop_x := 0.0
	var kop_z := 0.52
	if wf.toestand == Wolf.ATTACK:
		# uithaal: naar voren en omlaag rond STRIKE_AT, daarna terug
		var u := clampf(1.0 - absf(wf.slag - Wolf.STRIKE_AT) / 0.3, 0.0, 1.0)
		kop_x = 0.55 * u
		kop_z = 0.52 + 0.14 * u
	elif wf.toestand == Wolf.HUNT:
		kop_x = 0.25            # kop laag, op de prooi gericht
	elif not loopt:
		kop_x = 0.05 * sin(t * 1.3)
	kop.rotation.x = lerpf(kop.rotation.x, kop_x, minf(1.0, dt * 12.0))
	kop.position.z = lerpf(kop.position.z, kop_z, minf(1.0, dt * 12.0))
	st.rotation.y = sin(t * (6.0 if loopt else 1.5)) * (0.12 if loopt else 0.25)
	st.rotation.x = 0.35 if wf.toestand == Wolf.HUNT or wf.toestand == Wolf.ATTACK else 0.0
	lijf.position.y = absf(sin(fase)) * 0.03 if loopt else 0.0
	match wf.toestand:
		Wolf.DYING:
			lijf.rotation.z = lerpf(0.0, PI * 0.5, ease(wf.slag, 0.5))
			lijf.position.y = 0.19 * wf.slag
		Wolf.DEAD:
			lijf.rotation.z = PI * 0.5
			lijf.position.y = 0.19 - 0.5 * clampf((wf.slag - 0.7) / 0.3, 0.0, 1.0)   # laatste 30 %: zakt weg
		_:
			lijf.rotation.z = 0.0
