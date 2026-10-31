class_name MissieProps
extends RefCounted
## Placeholders voor de objecten van missie 4 (terugval van Props._placeholder als er geen glb is) en de den met ogen
## (terugval voor het wezen zombie, spel.json wezen_model). Alles uit meshes, geen texturen.
## magische_sleutel, magische_poort (kind `poort_deur` gaat weg als hij open is, zoals de glb), stenen_muur, mijn,
## olie, vuur (vlammen + licht), boom_ogen (den met twee ogen: `Ogen` schaalt open als er iemand in de buurt is).

static func _mat(kleur: Color, ruw := 0.9, emissie := 0.0) -> StandardMaterial3D:
	var m := StandardMaterial3D.new()
	m.albedo_color = kleur
	m.roughness = ruw
	if emissie > 0.0:
		m.emission_enabled = true
		m.emission = kleur
		m.emission_energy_multiplier = emissie
	return m


static func _mi(ouder: Node3D, mesh: Mesh, mat: Material, pos: Vector3, schaal := Vector3.ONE) -> MeshInstance3D:
	var mi := MeshInstance3D.new()
	mi.mesh = mesh
	mi.material_override = mat
	mi.position = pos
	mi.scale = schaal
	ouder.add_child(mi)
	return mi


static func _doos(x: float, y: float, z: float) -> BoxMesh:
	var b := BoxMesh.new()
	b.size = Vector3(x, y, z)
	return b


static func _cyl(rt: float, rb: float, h: float, seg := 10) -> CylinderMesh:
	var c := CylinderMesh.new()
	c.top_radius = rt
	c.bottom_radius = rb
	c.height = h
	c.radial_segments = seg
	c.rings = 1
	return c


static func _bol(r: float) -> SphereMesh:
	var s := SphereMesh.new()
	s.radius = r
	s.height = r * 2.0
	s.radial_segments = 12
	s.rings = 6
	return s


static func maak(naam: String) -> Node3D:
	var n := Node3D.new()
	match naam:
		"magische_sleutel": _sleutel(n)
		"magische_poort": _poort(n)
		"stenen_muur": _muur(n)
		"mijn": _mijn(n)
		"olie": _olie(n)
		"vuur": _vuur(n)
		"boom_ogen": _boom_ogen(n)
		_: return null
	return n


static func _sleutel(n: Node3D) -> void:
	var m := _mat(Color(0.95, 0.78, 0.3), 0.3, 0.5)
	m.metallic = 0.9
	var s := Node3D.new()
	s.name = "Sleutel"
	s.position.y = 0.35
	s.rotation.z = PI * 0.5
	n.add_child(s)
	_mi(s, _cyl(0.025, 0.025, 0.4), m, Vector3.ZERO)
	var oog := _mi(s, TorusMesh.new(), m, Vector3(0, 0.26, 0), Vector3.ONE * 0.12)
	oog.rotation.x = PI * 0.5
	_mi(s, _doos(0.1, 0.03, 0.03), m, Vector3(0.05, -0.15, 0))
	_mi(s, _doos(0.07, 0.03, 0.03), m, Vector3(0.035, -0.09, 0))


static func _poort(n: Node3D) -> void:
	var steen := _mat(Color(0.5, 0.5, 0.52), 0.95)
	_mi(n, _doos(1.0, 2.6, 1.2), steen, Vector3(-1.6, 1.3, 0))
	_mi(n, _doos(1.0, 2.6, 1.2), steen, Vector3(1.6, 1.3, 0))
	_mi(n, _doos(4.2, 0.5, 1.2), steen, Vector3(0, 2.45, 0))
	_mi(n, _bol(0.18), _mat(Color(0.3, 0.55, 1.0), 0.2, 2.0), Vector3(0, 2.5, 0.62))
	var deur := Node3D.new()
	deur.name = "poort_deur"
	n.add_child(deur)
	_mi(deur, _doos(2.2, 2.2, 0.15), _mat(Color(0.42, 0.28, 0.16), 0.9), Vector3(0, 1.1, 0))


static func _muur(n: Node3D) -> void:
	_mi(n, _doos(1.95, 1.4, 1.95), _mat(Color(0.55, 0.53, 0.5), 0.95), Vector3(0, 0.7, 0))
	_mi(n, _doos(2.0, 0.15, 2.0), _mat(Color(0.45, 0.44, 0.42), 0.95), Vector3(0, 1.45, 0))


static func _mijn(n: Node3D) -> void:
	# half ingegraven: een donkere bult met een slagpin (in het origineel nauwelijks te zien)
	_mi(n, _cyl(0.18, 0.28, 0.12), _mat(Color(0.25, 0.22, 0.18), 0.9), Vector3(0, 0.03, 0))
	_mi(n, _cyl(0.025, 0.025, 0.12), _mat(Color(0.5, 0.5, 0.5), 0.4), Vector3(0, 0.14, 0))


static func _olie(n: Node3D) -> void:
	var plas := _mi(n, _cyl(0.55, 0.55, 0.01, 16), _mat(Color(0.05, 0.05, 0.06), 0.1), Vector3(0, 0.02, 0), Vector3(1.0, 1.0, 0.7))
	plas.name = "Plas"


static func _vuur(n: Node3D) -> void:
	for i in 5:
		var a := float(i) / 5.0 * TAU
		var v := _mi(n, _cyl(0.0, 0.22, 0.9, 6), _mat(Color(1.0, 0.45 + 0.1 * (i % 2), 0.1), 0.5, 3.0),
			Vector3(cos(a) * 0.35, 0.45, sin(a) * 0.35))
		v.name = "Vlam%d" % i
	var l := OmniLight3D.new()
	l.name = "Licht"
	l.light_color = Color(1.0, 0.6, 0.25)
	l.light_energy = 2.5
	l.omni_range = 6.0
	l.position.y = 1.0
	n.add_child(l)


## Den met ogen: wat de gebruiker zich van het wezen herinnert (een boom met ogen die verder niets doet). De kroon is
## de natuur-den als die er is, anders kegels; `Ogen` (twee witte bollen met pupil) draait naar wie in de buurt is.
static func _boom_ogen(n: Node3D) -> void:
	var den := Natuur.instantie("jonge_den") if Natuur.bestaat("jonge_den") else null
	var hoogte := 3.2
	var straal := 1.0
	if den != null:
		n.add_child(den)
		var box := _aabb(den, Transform3D.IDENTITY)
		if box.size.y > 0.1:          # schalen naar een kleine den (het sprite-wezen is een boompje van mensenhoogte x 2)
			var s := 3.2 / box.size.y
			den.scale = Vector3.ONE * s
			straal = maxf(box.size.x, box.size.z) * 0.5 * s
	else:
		var groen := _mat(Color(0.16, 0.36, 0.18), 0.95)
		_mi(n, _cyl(0.12, 0.16, 1.2), _mat(Color(0.35, 0.24, 0.15)), Vector3(0, 0.6, 0))
		for i in 3:
			_mi(n, _cyl(0.0, 1.1 - i * 0.25, 1.4, 9), groen, Vector3(0, 1.5 + i * 0.8, 0))
	var ogen := Node3D.new()
	ogen.name = "Ogen"
	ogen.position = Vector3(0, hoogte * 0.45, 0)
	n.add_child(ogen)
	var wit := _mat(Color(1.0, 0.97, 0.75), 0.4, 1.2)
	var zwart := _mat(Color(0.05, 0.05, 0.05), 0.3)
	for kant in [-1.0, 1.0]:
		var oog := Node3D.new()
		oog.name = "Oog"
		oog.position = Vector3(0.22 * kant, 0, straal * 0.55 + 0.1)
		ogen.add_child(oog)
		_mi(oog, _bol(0.17), wit, Vector3.ZERO)
		_mi(oog, _bol(0.08), zwart, Vector3(0, 0, 0.13))
	ogen.scale = Vector3(1.0, 0.1, 1.0)     # dicht; WolfModel.werk opent ze


static func _aabb(n: Node, xf: Transform3D) -> AABB:
	var t := xf * ((n as Node3D).transform if n is Node3D else Transform3D.IDENTITY)
	var box := AABB()
	var eerste := true
	if n is MeshInstance3D and (n as MeshInstance3D).mesh != null:
		box = t * (n as MeshInstance3D).mesh.get_aabb()
		eerste = false
	for c in n.get_children():
		var b := _aabb(c, t)
		if b.size == Vector3.ZERO:
			continue
		box = b if eerste else box.merge(b)
		eerste = false
	return box
