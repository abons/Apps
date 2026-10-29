class_name Props
extends RefCounted
## Placeholder-meshes voor kaartobjecten. De naam in data/objecten.json ("placeholder:boom_den") kiest de fabriek;
## een echt model vervangt later alleen deze functie (of laadt een glb op dezelfde naam).

static var kroon_mat: StandardMaterial3D        # gedeeld, seizoenstint in WereldView.werk_seizoen()
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


static func _kroon() -> StandardMaterial3D:
	if kroon_mat == null:
		kroon_mat = _mat(Color(0.13, 0.30, 0.11), 0.85)
	return kroon_mat


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


## Boommesh met twee vlakken (stam, kroon), geschikt voor MultiMesh. Hoogte ~5-7 m.
static func boom_mesh(soort: String) -> ArrayMesh:
	var stam := SurfaceTool.new()
	var kroon := SurfaceTool.new()
	stam.begin(Mesh.PRIMITIVE_TRIANGLES)
	kroon.begin(Mesh.PRIMITIVE_TRIANGLES)
	match soort:
		"boom_den":    # grote den: dikke stam, 4 kegels
			stam.append_from(_cyl(0.18, 0.32, 2.4), 0, Transform3D(Basis(), Vector3(0, 1.2, 0)))
			for k in 4:
				kroon.append_from(_kegel(2.0 - k * 0.38, 2.4, 10), 0, Transform3D(Basis(), Vector3(0, 2.4 + k * 1.15, 0)))
		"boom_spar":   # spar: smal en hoog
			stam.append_from(_cyl(0.12, 0.22, 1.6), 0, Transform3D(Basis(), Vector3(0, 0.8, 0)))
			for k in 5:
				kroon.append_from(_kegel(1.35 - k * 0.2, 2.0, 8), 0, Transform3D(Basis(), Vector3(0, 1.8 + k * 1.0, 0)))
		_:             # boom_rond: loofboom
			stam.append_from(_cyl(0.2, 0.3, 2.6), 0, Transform3D(Basis(), Vector3(0, 1.3, 0)))
			kroon.append_from(_bol(1.7, 12), 0, Transform3D(Basis().scaled(Vector3(1, 0.85, 1)), Vector3(0, 3.7, 0)))
			kroon.append_from(_bol(1.1, 10), 0, Transform3D(Basis(), Vector3(0.9, 3.1, 0.3)))
	var m := ArrayMesh.new()
	stam.generate_normals()
	kroon.generate_normals()
	stam.commit(m)
	kroon.commit(m)
	m.surface_set_material(0, _mat(Color(0.30, 0.21, 0.13)))
	m.surface_set_material(1, _kroon() if soort != "boom_rond" else _kroon())
	return m


static func rots_mesh() -> Mesh:
	var s := _bol(1.0, 6)
	s.material = _steen()
	return s


## Een los kaartobject. `ob` komt uit Wereld.objecten. Geeft null voor niets-tonen (bv. de koe-generator).
static func maak(ob: Dictionary) -> Node3D:
	var model: String = ob["model"]
	if not model.begins_with("placeholder:"):
		return null
	var n := Node3D.new()
	match model.substr(12):
		"paddenstoel": _paddenstoel(n, ob["state"])
		"vlag": _vlag(n)
		"kampvuur": _kampvuur(n)
		"bron": _bron(n)
		"beker": _beker(n)
		_: return null
	return n


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


static func _beker(n: Node3D) -> void:
	var m := _mat(Color(0.85, 0.87, 0.92), 0.25, 0.25)
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
