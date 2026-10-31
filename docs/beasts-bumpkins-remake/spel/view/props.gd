class_name Props
extends RefCounted
## Kaartobjecten als node. data/objecten.json `model`: "natuur:<glb>" laadt assets/<glb>.glb via Natuur (wind, LOD, seizoen),
## "koe" de koe (Koe), "placeholder:<naam>" de oude blokjes hieronder (terugval als een glb ontbreekt).

static var steen_mat: StandardMaterial3D


static func _mat(kleur: Color, ruw := 0.9, emissie := 0.0) -> StandardMaterial3D:
	var m := StandardMaterial3D.new()
	m.albedo_color = kleur
	m.roughness = ruw
	if emissie > 0.0:
		m.emission_enabled = true
		m.emission = kleur
		m.emission_energy_multiplier = emissie
	return m


static func _steen() -> StandardMaterial3D:
	if steen_mat == null:
		steen_mat = _mat(Color(0.44, 0.42, 0.39), 0.95)
	return steen_mat


static func _kegel(r: float, h: float, seg := 9) -> CylinderMesh:
	var c := CylinderMesh.new()
	c.top_radius = 0.0
	c.bottom_radius = r
	c.height = h
	c.radial_segments = seg
	c.rings = 1
	return c


static func _cyl(rt: float, rb: float, h: float, seg := 8) -> CylinderMesh:
	var c := CylinderMesh.new()
	c.top_radius = rt
	c.bottom_radius = rb
	c.height = h
	c.radial_segments = seg
	c.rings = 1
	return c


static func _bol(r: float, seg := 10) -> SphereMesh:
	var s := SphereMesh.new()
	s.radius = r
	s.height = r * 2.0
	s.radial_segments = seg
	s.rings = seg / 2
	return s


## Een los kaartobject. `ob` komt uit Wereld.objecten. Geeft null voor niets-tonen.
static func maak(ob: Dictionary) -> Node3D:
	var model: String = ob["model"]
	if model.begins_with("natuur:"):
		var glb := model.substr(7)
		var n := Natuur.instantie(glb)
		if n == null:
			return _placeholder(glb, ob)
		var def: Dictionary = Gegevens.lees(Gegevens.OBJECTEN)["objecten"][str(ob["cls"])]
		n.scale = Vector3.ONE * float(def.get("schaal", 1.0))
		if glb == "kampvuur":
			_kampvuur_effecten(n)
		return n
	if model == "koe":
		return Koe.maak(Koe.STANDAARD, float((ob["x"] * 31 + ob["y"] * 17) % 30) / 10.0)
	if model.begins_with("placeholder:"):
		return _placeholder(model.substr(12), ob)
	return null


static func _placeholder(naam: String, ob: Dictionary) -> Node3D:
	var n := Node3D.new()
	match naam:
		"paddenstoel": _paddenstoel(n, ob["state"])
		"vlag": _vlag(n)
		"kampvuur": _kampvuur(n)
		"bron": _bron(n)
		"beker", "zilveren_beker": _beker(n)
		"gouden_kelk": _beker(n, Color(0.95, 0.75, 0.25))
		"put": _put(n)
		"gilde": _gilde(n)
		"wolf": _wolf(n)
		"goud": _goud(n)
		"drankje": _drankje(n)
		_:
			return MissieProps.maak(naam)      # missie 4: sleutel, poort, muur, mijn, olie, vuur (null als onbekend)
	return n


## Wolf als kaartobject (zelden: kaartwolven worden een Wolf in de sim): het wolfmodel in rust, zonder hp-balkje.
static func _wolf(n: Node3D) -> void:
	var w := WolfModel.maak()
	(w.get_node("Hp") as Node3D).visible = false
	n.add_child(w)


## Goudbuidel (origineel `gold`): bruine zak met een paar munten.
static func _goud(n: Node3D) -> void:
	var zak := MeshInstance3D.new()
	zak.mesh = _bol(0.2, 10)
	zak.material_override = _mat(Color(0.5, 0.36, 0.2), 0.95)
	zak.scale = Vector3(1.0, 0.85, 1.0)
	zak.position.y = 0.17
	n.add_child(zak)
	var gm := _mat(Color(1.0, 0.8, 0.25), 0.3, 0.4)
	gm.metallic = 0.9
	for i in 3:
		var munt := MeshInstance3D.new()
		munt.mesh = _cyl(0.07, 0.07, 0.02, 10)
		munt.material_override = gm
		munt.position = Vector3(0.22 + i * 0.05, 0.01 + i * 0.02, 0.05 * i)
		n.add_child(munt)


## Drankje (origineel `potion`): flesje met een blauwe vloeistof en een kurk.
static func _drankje(n: Node3D) -> void:
	var fles := MeshInstance3D.new()
	fles.mesh = _bol(0.1, 10)
	fles.material_override = _mat(Color(0.3, 0.45, 0.95), 0.15, 0.6)
	fles.position.y = 0.1
	n.add_child(fles)
	var hals := MeshInstance3D.new()
	hals.mesh = _cyl(0.03, 0.03, 0.1)
	hals.material_override = _mat(Color(0.75, 0.85, 0.9), 0.1)
	hals.position.y = 0.23
	n.add_child(hals)
	var kurk := MeshInstance3D.new()
	kurk.mesh = _cyl(0.035, 0.035, 0.04)
	kurk.material_override = _mat(Color(0.6, 0.45, 0.3), 0.9)
	kurk.position.y = 0.3
	n.add_child(kurk)


## Kampvuur uit de glb: deeltjes voor vlammen en rook op `vuur_bron`, een OmniLight3D (flikkert in WereldView).
## De namen "Vlam" (de emissieve vlamkaart, schaalt mee met de flikker) en "Vuurlicht" blijven de koppelpunten.
static func _kampvuur_effecten(n: Node3D) -> void:
	var bron := n.find_child("vuur_bron", true, false) as Node3D
	var plek := bron.position if bron else Vector3(0, 0.22, 0)
	var vlam := n.find_child("kampvuur_vlam", true, false)
	if vlam:
		vlam.name = "Vlam"
	var licht := OmniLight3D.new()
	licht.name = "Vuurlicht"
	licht.position = Vector3(0, 0.7, 0)
	licht.light_color = Color(1.0, 0.62, 0.30)
	licht.omni_range = 9.0
	licht.omni_attenuation = 1.3
	licht.light_energy = 1.6
	licht.shadow_enabled = false
	n.add_child(licht)
	# zacht rond deeltjesplaatje, zonder bestand
	var gr := Gradient.new()
	gr.colors = PackedColorArray([Color(1, 1, 1, 1), Color(1, 1, 1, 0)])
	gr.offsets = PackedFloat32Array([0.0, 1.0])
	var tex := GradientTexture2D.new()
	tex.gradient = gr
	tex.fill = GradientTexture2D.FILL_RADIAL
	tex.fill_from = Vector2(0.5, 0.5)
	tex.fill_to = Vector2(1.0, 0.5)
	tex.width = 64
	tex.height = 64
	n.add_child(_deeltjes("Vlammen", tex, 24, 0.8, 0.5, 0.06, Vector3(0, 0.6, 0), 0.7, 0.35,
		[0.0, 0.12, 0.6, 1.0], [Color(1.0, 0.85, 0.4, 0.0), Color(1.0, 0.7, 0.2, 0.95), Color(1.0, 0.35, 0.05, 0.55), Color(0.6, 0.1, 0.0, 0.0)],
		true, plek))
	n.add_child(_deeltjes("Rook", tex, 14, 3.6, 0.7, 0.12, Vector3(0.25, 0.25, 0.1), 0.7, 2.4,
		[0.0, 0.2, 1.0], [Color(0.35, 0.33, 0.32, 0.0), Color(0.30, 0.29, 0.28, 0.20), Color(0.25, 0.25, 0.26, 0.0)],
		false, plek + Vector3(0, 0.6, 0)))


static func _deeltjes(naam: String, tex: Texture2D, aantal: int, leven: float, grootte: float, straal: float, zwaartekracht: Vector3,
		snelheid: float, schaal_eind: float, offsets: Array, kleuren: Array, optellend: bool, plek: Vector3) -> GPUParticles3D:
	var p := GPUParticles3D.new()
	p.name = naam
	p.amount = aantal
	p.lifetime = leven
	p.position = plek
	p.local_coords = false
	p.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	p.visibility_aabb = AABB(Vector3(-3, -1, -3), Vector3(6, 8, 6))
	var pm := ParticleProcessMaterial.new()
	pm.emission_shape = ParticleProcessMaterial.EMISSION_SHAPE_SPHERE
	pm.emission_sphere_radius = straal
	pm.direction = Vector3(0, 1, 0)
	pm.spread = 18.0
	pm.initial_velocity_min = snelheid * 0.6
	pm.initial_velocity_max = snelheid
	pm.gravity = zwaartekracht
	pm.scale_min = 0.7
	pm.scale_max = 1.0
	var sc := Curve.new()
	sc.add_point(Vector2(0, 0.6))
	sc.add_point(Vector2(1, schaal_eind))
	var sct := CurveTexture.new()
	sct.curve = sc
	pm.scale_curve = sct
	var g := Gradient.new()
	g.offsets = PackedFloat32Array(offsets)
	g.colors = PackedColorArray(kleuren)
	var gt := GradientTexture1D.new()
	gt.gradient = g
	pm.color_ramp = gt
	p.process_material = pm
	var q := QuadMesh.new()
	q.size = Vector2(grootte, grootte)
	var mat := StandardMaterial3D.new()
	mat.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
	mat.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
	mat.blend_mode = BaseMaterial3D.BLEND_MODE_ADD if optellend else BaseMaterial3D.BLEND_MODE_MIX
	mat.billboard_mode = BaseMaterial3D.BILLBOARD_PARTICLES
	mat.particles_anim_h_frames = 1
	mat.particles_anim_v_frames = 1
	mat.vertex_color_use_as_albedo = true
	mat.albedo_texture = tex
	mat.disable_receive_shadows = true
	q.material = mat
	p.draw_pass_1 = q
	return p


static func _paddenstoel(n: Node3D, soort: int) -> void:
	var kappen := [Color(0.80, 0.15, 0.12), Color(0.55, 0.36, 0.20), Color(0.92, 0.90, 0.80), Color(0.55, 0.30, 0.60),
		Color(0.85, 0.60, 0.15), Color(0.70, 0.35, 0.15), Color(0.80, 0.15, 0.12)]
	var stam := MeshInstance3D.new()
	stam.mesh = _cyl(0.07, 0.09, 0.3)
	stam.material_override = _mat(Color(0.88, 0.85, 0.75))
	stam.position.y = 0.15
	n.add_child(stam)
	var kap := MeshInstance3D.new()
	kap.mesh = _bol(0.2, 10)
	kap.material_override = _mat(kappen[clampi(soort, 0, kappen.size() - 1)], 0.6)
	kap.scale = Vector3(1, 0.55, 1)
	kap.position.y = 0.32
	n.add_child(kap)


static func _vlag(n: Node3D) -> void:
	var paal := MeshInstance3D.new()
	paal.mesh = _cyl(0.05, 0.07, 4.0)
	paal.material_override = _mat(Color(0.35, 0.24, 0.14))
	paal.position.y = 2.0
	n.add_child(paal)
	var doek := MeshInstance3D.new()
	var b := BoxMesh.new()
	b.size = Vector3(1.3, 0.8, 0.04)
	doek.mesh = b
	doek.material_override = _mat(Color(0.75, 0.12, 0.10), 0.8)
	doek.position = Vector3(0.7, 3.5, 0)
	doek.name = "Vlagdoek"
	n.add_child(doek)


static func _kampvuur(n: Node3D) -> void:
	var rots := _steen()
	for i in 8:
		var a := i * TAU / 8.0
		var s := MeshInstance3D.new()
		s.mesh = _bol(0.22, 8)
		s.material_override = rots
		s.scale = Vector3(1.2, 0.7, 1.0)
		s.position = Vector3(cos(a) * 0.62, 0.12, sin(a) * 0.62)
		s.rotation.y = a
		n.add_child(s)
	var hout := _mat(Color(0.25, 0.15, 0.08))
	for i in 4:
		var l := MeshInstance3D.new()
		l.mesh = _cyl(0.06, 0.07, 0.8)
		l.material_override = hout
		l.rotation = Vector3(0, i * PI / 4.0 + 0.2, PI / 2 - 0.35)
		l.position = Vector3(0, 0.15, 0)
		n.add_child(l)
	var vlam := Node3D.new()
	vlam.name = "Vlam"
	var kern := MeshInstance3D.new()
	kern.mesh = _kegel(0.36, 0.75, 8)
	kern.material_override = _mat(Color(1.0, 0.55, 0.12), 1.0, 3.0)
	kern.position.y = 0.6
	vlam.add_child(kern)
	var top := MeshInstance3D.new()
	top.mesh = _kegel(0.2, 0.6, 8)
	top.material_override = _mat(Color(1.0, 0.85, 0.35), 1.0, 4.0)
	top.position.y = 0.75
	vlam.add_child(top)
	n.add_child(vlam)
	var licht := OmniLight3D.new()
	licht.name = "Vuurlicht"
	licht.position.y = 0.9
	licht.light_color = Color(1.0, 0.62, 0.30)
	licht.omni_range = 9.0
	licht.omni_attenuation = 1.3
	licht.light_energy = 1.6
	licht.shadow_enabled = false
	n.add_child(licht)


static func _bron(n: Node3D) -> void:
	for i in 10:
		var a := i * TAU / 10.0
		var s := MeshInstance3D.new()
		s.mesh = _bol(0.22, 8)
		s.material_override = _steen()
		s.scale = Vector3(1.0, 0.7, 1.0)
		s.position = Vector3(cos(a) * 0.85, 0.15, sin(a) * 0.85)
		n.add_child(s)
	var w := MeshInstance3D.new()
	w.mesh = _cyl(0.8, 0.8, 0.05, 16)
	var m := _mat(Color(0.25, 0.55, 0.75), 0.05)
	m.metallic = 0.3
	w.material_override = m
	w.position.y = 0.12
	n.add_child(w)


## Missie 3, nog zonder glb: put = stenen ring met een dakje op twee palen.
static func _put(n: Node3D) -> void:
	var ring := MeshInstance3D.new()
	ring.mesh = _cyl(0.55, 0.6, 0.6, 12)
	ring.material_override = _steen()
	ring.position.y = 0.3
	n.add_child(ring)
	var hout := _mat(Color(0.42, 0.28, 0.16))
	for z in [-0.5, 0.5]:
		var paal := MeshInstance3D.new()
		paal.mesh = _cyl(0.05, 0.05, 1.4)
		paal.material_override = hout
		paal.position = Vector3(0, 0.7, z)
		n.add_child(paal)
	var dak := MeshInstance3D.new()
	var bm := BoxMesh.new()
	bm.size = Vector3(1.2, 0.08, 1.3)
	dak.mesh = bm
	dak.material_override = _mat(Color(0.5, 0.22, 0.14))
	dak.position.y = 1.45
	n.add_child(dak)


## Missie 3, nog zonder glb (Bouwmenu, voetafdruk 3x3 = 6 m): voetvolkgilde naar de sprite `fguild`: ronde grijze
## toren met paarse kantelen, een houten deur aan de voorkant (+Z, Plan.DEUREN) en rechts een bijgebouwtje met strodak.
## Blijft binnen 2,6 m van het midden, dus binnen de voetafdruk (niet over de vlag).
static func _gilde(n: Node3D) -> void:
	var toren := MeshInstance3D.new()
	toren.mesh = _cyl(1.75, 1.9, 4.2, 14)
	toren.material_override = _steen()
	toren.position = Vector3(-0.3, 2.1, -0.3)
	n.add_child(toren)
	var paars := _mat(Color(0.45, 0.12, 0.5))
	var rand := MeshInstance3D.new()
	rand.mesh = _cyl(1.95, 1.95, 0.35, 14)
	rand.material_override = paars
	rand.position = Vector3(-0.3, 4.35, -0.3)
	n.add_child(rand)
	for i in 8:
		var a := TAU * i / 8.0
		var kantel := MeshInstance3D.new()
		var km := BoxMesh.new()
		km.size = Vector3(0.5, 0.45, 0.35)
		kantel.mesh = km
		kantel.material_override = _steen()
		kantel.position = Vector3(-0.3 + cos(a) * 1.8, 4.75, -0.3 + sin(a) * 1.8)
		kantel.rotation.y = -a
		n.add_child(kantel)
	var deur := MeshInstance3D.new()
	var dm := BoxMesh.new()
	dm.size = Vector3(0.9, 1.6, 0.15)
	deur.mesh = dm
	deur.material_override = _mat(Color(0.45, 0.28, 0.15))
	deur.position = Vector3(-0.3, 0.8, 1.55)
	n.add_child(deur)
	var schuur := MeshInstance3D.new()
	var sm := BoxMesh.new()
	sm.size = Vector3(1.4, 1.3, 1.6)
	schuur.mesh = sm
	schuur.material_override = _mat(Color(0.55, 0.42, 0.28))
	schuur.position = Vector3(1.75, 0.65, 0.9)
	n.add_child(schuur)
	var stro := MeshInstance3D.new()
	stro.mesh = _kegel(1.2, 0.9, 6)
	stro.material_override = _mat(Color(0.85, 0.65, 0.3))
	stro.position = Vector3(1.75, 1.75, 0.9)
	n.add_child(stro)
	var schild := MeshInstance3D.new()
	schild.mesh = _cyl(0.35, 0.35, 0.06, 10)
	schild.material_override = _mat(Color(0.95, 0.95, 0.95), 0.6)
	schild.rotation.x = PI * 0.5
	schild.position = Vector3(-0.3, 2.6, 1.6)
	n.add_child(schild)


static func _beker(n: Node3D, kleur := Color(0.85, 0.87, 0.92)) -> void:
	var m := _mat(kleur, 0.25, 0.25)
	m.metallic = 0.9
	var voet := MeshInstance3D.new()
	voet.mesh = _cyl(0.12, 0.16, 0.05)
	voet.material_override = m
	voet.position.y = 0.025
	n.add_child(voet)
	var steel := MeshInstance3D.new()
	steel.mesh = _cyl(0.03, 0.04, 0.25)
	steel.material_override = m
	steel.position.y = 0.17
	n.add_child(steel)
	var kom := MeshInstance3D.new()
	kom.mesh = _cyl(0.2, 0.06, 0.25, 12)
	kom.material_override = m
	kom.position.y = 0.42
	n.add_child(kom)
