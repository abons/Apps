class_name TerreinView
extends Node3D
## Bouwt het terrein: een mesh met hoogte en kleur per hoekpunt (uit tegelhoogte en tegelkleur), een waterlaag,
## bomen (MultiMesh), rotsblokken (MultiMesh) en de losse kaartobjecten (placeholders uit Props).
## Hoogte is alleen weergave; de sim is plat. `hoogte_op()` geeft de grondhoogte voor units.

const MARGE := 14           # tegels water/land rondom het eiland

var w: Wereld
var tegel_m := 2.0
var x0 := 0                 # linkerbovenhoek van het getoonde venster (tegels)
var y0 := 0
var br := 0
var ho := 0
var _hoek_h := PackedFloat32Array()   # (br+1) * (ho+1) hoekhoogtes
var terrein_mat: ShaderMaterial
var water_mat: ShaderMaterial
var kampvuur_node: Node3D
var vlag_doek: Node3D


func bouw(wereld: Wereld) -> void:
	w = wereld
	tegel_m = w.tegel_m
	var e := w.eiland.grow(MARGE)
	x0 = maxi(e.position.x, 0)
	y0 = maxi(e.position.y, 0)
	br = mini(e.end.x, w.raster.kolommen) - x0
	ho = mini(e.end.y, w.raster.rijen) - y0
	_bouw_terrein()
	_bouw_water()
	_bouw_objecten()
	_bouw_bomen_en_rotsen()


func tegel_midden(t: Vector2i) -> Vector3:
	var p := Vector3((t.x + 0.5) * tegel_m, 0, (t.y + 0.5) * tegel_m)
	p.y = hoogte_op(p.x, p.z)
	return p


func _tegel_h(c: int, r: int) -> float:
	if not w.raster.in_kaart(c, r):
		return w.raster.hoogte_soort[w.raster.namen.find("leeg")]
	return w.raster.hoogte_soort[w.raster.soort[w.raster.idx(c, r)]]


func _hoek(i: int, j: int) -> float:
	return _hoek_h[j * (br + 1) + i]


## Grondhoogte op wereldpositie (m), bilineair over de hoekhoogtes.
func hoogte_op(xm: float, zm: float) -> float:
	var tx := xm / tegel_m - x0
	var ty := zm / tegel_m - y0
	if tx < 0.0 or ty < 0.0 or tx >= br or ty >= ho:
		return -2.0
	var i := int(tx)
	var j := int(ty)
	var fx := tx - i
	var fy := ty - j
	var a := lerpf(_hoek(i, j), _hoek(i + 1, j), fx)
	var b := lerpf(_hoek(i, j + 1), _hoek(i + 1, j + 1), fx)
	return lerpf(a, b, fy)


func _bouw_terrein() -> void:
	_hoek_h.resize((br + 1) * (ho + 1))
	var kleur_lin: Array[Color] = []
	for k in w.raster.kleuren:
		kleur_lin.append(k.srgb_to_linear())
	var verts := PackedVector3Array()
	var normals := PackedVector3Array()
	var kleuren := PackedColorArray()
	var idx := PackedInt32Array()
	# hoekhoogtes: gemiddelde van de vier tegels rond de hoek
	for j in ho + 1:
		for i in br + 1:
			var som := 0.0
			for dj in 2:
				for di in 2:
					som += _tegel_h(x0 + i - 1 + di, y0 + j - 1 + dj)
			_hoek_h[j * (br + 1) + i] = som / 4.0
	for j in ho + 1:
		for i in br + 1:
			var hh := _hoek(i, j)
			verts.append(Vector3((x0 + i) * tegel_m, hh, (y0 + j) * tegel_m))
			var hl := _hoek(maxi(i - 1, 0), j)
			var hr := _hoek(mini(i + 1, br), j)
			var hu := _hoek(i, maxi(j - 1, 0))
			var hd := _hoek(i, mini(j + 1, ho))
			normals.append(Vector3(hl - hr, 2.0 * tegel_m, hu - hd).normalized())
			var c := Color(0, 0, 0, 0)
			for dj in 2:
				for di in 2:
					var tc := x0 + i - 1 + di
					var tr := y0 + j - 1 + dj
					var si := w.raster.soort[w.raster.idx(tc, tr)] if w.raster.in_kaart(tc, tr) else w.raster.namen.find("leeg")
					var k := kleur_lin[si]
					c += Color(k.r, k.g, k.b, w.raster.gras_soort[si])
			kleuren.append(c / 4.0)
	for j in ho:
		for i in br:
			var a := j * (br + 1) + i
			var b := a + 1
			var d := a + (br + 1)
			var c2 := d + 1
			idx.append_array([a, b, c2, a, c2, d])
	var arrays := []
	arrays.resize(Mesh.ARRAY_MAX)
	arrays[Mesh.ARRAY_VERTEX] = verts
	arrays[Mesh.ARRAY_NORMAL] = normals
	arrays[Mesh.ARRAY_COLOR] = kleuren
	arrays[Mesh.ARRAY_INDEX] = idx
	var m := ArrayMesh.new()
	m.add_surface_from_arrays(Mesh.PRIMITIVE_TRIANGLES, arrays)
	terrein_mat = ShaderMaterial.new()
	terrein_mat.shader = load("res://shaders/terrein.gdshader")
	m.surface_set_material(0, terrein_mat)
	var mi := MeshInstance3D.new()
	mi.name = "Terrein"
	mi.mesh = m
	add_child(mi)


func _bouw_water() -> void:
	water_mat = ShaderMaterial.new()
	water_mat.shader = load("res://shaders/water.gdshader")
	var pm := PlaneMesh.new()
	pm.size = Vector2(1800, 1800)
	pm.subdivide_width = 1
	pm.subdivide_depth = 1
	var bed := MeshInstance3D.new()           # zeebodem buiten het getoonde venster, zelfde diepte als de waterbodem
	bed.name = "Zeebodem"
	var bm := PlaneMesh.new()
	bm.size = Vector2(1800, 1800)
	var bmat := StandardMaterial3D.new()
	bmat.albedo_color = Color(0.20, 0.25, 0.22)
	bmat.roughness = 1.0
	bm.material = bmat
	bed.mesh = bm
	bed.position = Vector3((x0 + br * 0.5) * tegel_m, -2.02, (y0 + ho * 0.5) * tegel_m)
	add_child(bed)
	var mi := MeshInstance3D.new()
	mi.name = "Water"
	mi.mesh = pm
	mi.material_override = water_mat
	mi.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	mi.position = Vector3((x0 + br * 0.5) * tegel_m, 0.0, (y0 + ho * 0.5) * tegel_m)
	add_child(mi)


func _hash(x: int, y: int, s: int) -> float:
	var h: int = ((x * 73856093) ^ (y * 19349663) ^ (s * 83492791)) & 0x7fffffff
	h = ((h ^ (h >> 13)) * 1274126177) & 0x7fffffff
	h = h ^ (h >> 16)
	return float(h & 0xffff) / 65535.0


func _bouw_objecten() -> void:
	var tellers := {}
	for ob in w.objecten:
		var naam: String = ob["naam"]
		if naam.begins_with("boom_") or ob["spawn"]:
			continue
		var n := Props.maak(ob)
		if n == null:
			n = Node3D.new()      # gemarkeerd maar zonder model (koe_generator)
		tellers[naam] = int(tellers.get(naam, 0)) + 1
		n.name = naam if int(tellers[naam]) == 1 and naam != "paddenstoel" else "%s_%d_%d" % [naam, ob["x"], ob["y"]]
		n.position = tegel_midden(Vector2i(ob["x"], ob["y"]))
		n.rotation.y = _hash(ob["x"], ob["y"], 5) * TAU if naam == "paddenstoel" else 0.0
		add_child(n)
		if naam == "kampvuur":
			kampvuur_node = n
		elif naam == "vlag":
			vlag_doek = n.find_child("Vlagdoek", true, false)
		elif naam == "zilveren_beker":
			n.scale = Vector3.ONE * 1.8


func _bouw_bomen_en_rotsen() -> void:
	var per_soort := {}      # modelnaam -> Array[Transform3D]
	for ob in w.objecten:
		if not (ob["naam"] as String).begins_with("boom_"):
			continue
		var model: String = (ob["model"] as String).substr(12)
		var x: int = ob["x"]
		var y: int = ob["y"]
		var p := tegel_midden(Vector2i(x, y)) + Vector3((_hash(x, y, 1) - 0.5) * 0.9, 0, (_hash(x, y, 2) - 0.5) * 0.9)
		p.y = hoogte_op(p.x, p.z) - 0.05
		var s := 0.85 + _hash(x, y, 3) * 0.5
		var b := Basis(Vector3.UP, _hash(x, y, 4) * TAU).scaled(Vector3(s, s * (0.9 + _hash(x, y, 6) * 0.3), s))
		if not per_soort.has(model):
			per_soort[model] = []
		per_soort[model].append(Transform3D(b, p))
	for model in per_soort:
		var lijst: Array = per_soort[model]
		var mm := MultiMesh.new()
		mm.transform_format = MultiMesh.TRANSFORM_3D
		mm.mesh = Props.boom_mesh(model)
		mm.instance_count = lijst.size()
		for i in lijst.size():
			mm.set_instance_transform(i, lijst[i])
		var mmi := MultiMeshInstance3D.new()
		mmi.name = "Bomen_" + model
		mmi.multimesh = mm
		add_child(mmi)
	# rotsblokken op rots- en rotsrandtegels
	var rots: Array[Transform3D] = []
	for y in range(y0, y0 + ho):
		for x in range(x0, x0 + br):
			var sn := w.raster.soort_naam(x, y)
			if sn != "rots" and sn != "rotsrand":
				continue
			var aantal := 1 if sn == "rots" else (1 if _hash(x, y, 7) < 0.3 else 0)
			for k in aantal:
				var p := tegel_midden(Vector2i(x, y)) + Vector3((_hash(x, y, 8 + k) - 0.5) * 1.4, 0, (_hash(x, y, 9 + k) - 0.5) * 1.4)
				var sc := (0.95 if sn == "rots" else 0.6) * (0.6 + _hash(x, y, 10) * 0.9)
				p.y = hoogte_op(p.x, p.z) + 0.15 * sc
				var b := Basis(Vector3.UP, _hash(x, y, 11) * TAU).scaled(Vector3(sc * (0.8 + _hash(x, y, 12) * 0.7), sc * (0.55 + _hash(x, y, 13) * 0.5), sc * (0.8 + _hash(x, y, 14) * 0.6)))
				rots.append(Transform3D(b, p))
	var mm2 := MultiMesh.new()
	mm2.transform_format = MultiMesh.TRANSFORM_3D
	mm2.mesh = Props.rots_mesh()
	mm2.instance_count = rots.size()
	for i in rots.size():
		mm2.set_instance_transform(i, rots[i])
	var mmi2 := MultiMeshInstance3D.new()
	mmi2.name = "Rotsen"
	mmi2.multimesh = mm2
	add_child(mmi2)
