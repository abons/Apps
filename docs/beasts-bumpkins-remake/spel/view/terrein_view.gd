class_name TerreinView
extends Node3D
## Bouwt het terrein: een mesh met hoogte en texturengewichten per hoekpunt (uit tegelhoogte en tegelsoort, shader
## terrein.gdshader), een waterlaag, bomen en losse kaartobjecten (glb's via Props/Natuur) en de decoratie (rotsen, struiken,
## stronken; alleen weergave, uit data/objecten.json "decoratie"). Bomen zijn gewone instanties: visibility_range werkt per
## instantie, niet per MultiMesh-instantie, en een LOD-wissel bij 28 m is meer waard dan het bespaarde draw-call.
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
var _sneeuwlaag_bomen: Array[Node3D] = []   # instanties met `_sneeuw`-kinderen
var _sneeuwlaag_aan := false
var aantallen := {}                          # voor het log: soort -> aantal


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
	_bouw_bomen()
	_bouw_decoratie()
	zet_sneeuwlaag(false, true)
	print("[terrein] ", aantallen)


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
	var verts := PackedVector3Array()
	var normals := PackedVector3Array()
	var kleuren := PackedColorArray()
	var uvs := PackedVector2Array()
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
			var u := Vector2.ZERO
			for dj in 2:
				for di in 2:
					var sw := _splat(w.raster.soort_naam(x0 + i - 1 + di, y0 + j - 1 + dj))
					c += Color(sw[0], sw[1], sw[2], sw[3])
					u += Vector2(sw[4], sw[5])
			kleuren.append(c / 4.0)
			uvs.append(u / 4.0)
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
	arrays[Mesh.ARRAY_TEX_UV] = uvs
	arrays[Mesh.ARRAY_INDEX] = idx
	var m := ArrayMesh.new()
	m.add_surface_from_arrays(Mesh.PRIMITIVE_TRIANGLES, arrays)
	terrein_mat = ShaderMaterial.new()
	terrein_mat.shader = load("res://shaders/terrein.gdshader")
	for soort in ["kleur", "normaal", "ruw"]:
		terrein_mat.set_shader_parameter(soort + "_tex", _texturenset(soort))
	m.surface_set_material(0, terrein_mat)
	var mi := MeshInstance3D.new()
	mi.name = "Terrein"
	mi.mesh = m
	add_child(mi)


## Gewichten per tegelsoort: [gras, bosgrond, rots, zand, pad-tint, aarde-tint]; water/leeg = alles 0 (= water_rand).
func _splat(soort: String) -> Array:
	match soort:
		"gras": return [1.0, 0.0, 0.0, 0.0, 0.0, 0.0]
		"bosgrond": return [0.0, 1.0, 0.0, 0.0, 0.0, 0.0]
		"rots", "rotsrand": return [0.0, 0.0, 1.0, 0.0, 0.0, 0.0]
		"zand": return [0.0, 0.0, 0.0, 1.0, 0.0, 0.0]
		"pad": return [0.0, 0.0, 0.0, 1.0, 1.0, 0.0]
		"aarde": return [0.0, 0.65, 0.0, 0.35, 0.0, 1.0]
		"overig": return [0.0, 0.5, 0.5, 0.0, 0.0, 0.5]
	return [0.0, 0.0, 0.0, 0.0, 0.0, 0.0]


## Texture2DArray met de vijf terreinsets (volgorde = lagen in de shader): kleur, normaal of ruw.
func _texturenset(soort: String) -> Texture2DArray:
	var imgs: Array[Image] = []
	for naam in ["gras", "bosgrond", "rots", "zand", "water_rand"]:
		var tx := load("res://assets/terrein_%s_%s.jpg" % [naam, soort]) as Texture2D
		if tx == null:
			push_error("terrein: texture ontbreekt: " + naam + "_" + soort)
			return null
		var img := tx.get_image()
		if img.is_compressed():
			img.decompress()
		img.convert(Image.FORMAT_RGB8)
		img.generate_mipmaps(soort == "normaal")
		imgs.append(img)
	var t := Texture2DArray.new()
	t.create_from_images(imgs)
	return t


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
			n = Node3D.new()      # gemarkeerd maar zonder model
		tellers[naam] = int(tellers.get(naam, 0)) + 1
		n.name = naam if int(tellers[naam]) == 1 and naam != "paddenstoel" else "%s_%d_%d" % [naam, ob["x"], ob["y"]]
		n.position = tegel_midden(Vector2i(ob["x"], ob["y"]))
		if naam == "paddenstoel" or naam == "koe_generator":
			n.rotation.y = _hash(ob["x"], ob["y"], 5) * TAU
		elif naam == "vlag":
			n.rotation.y = deg_to_rad(-90)     # het doek wappert naar het oosten
		add_child(n)
		aantallen[naam] = int(aantallen.get(naam, 0)) + 1
		if naam == "kampvuur":
			kampvuur_node = n
		elif naam == "vlag":
			vlag_doek = n


## Kiest uit [[naam, gewicht], ...] met een vaste (gehashte) waarde 0..1.
func _kies(lijst: Array, r: float) -> String:
	var som := 0.0
	for e in lijst:
		som += float(e[1])
	var t := r * som
	for e in lijst:
		t -= float(e[1])
		if t <= 0.0:
			return e[0]
	return lijst[-1][0]


func _bouw_bomen() -> void:
	var defs: Dictionary = Gegevens.lees(Gegevens.OBJECTEN)["objecten"]
	var bos := Node3D.new()
	bos.name = "Bomen"
	add_child(bos)
	for ob in w.objecten:
		if not (ob["naam"] as String).begins_with("boom_"):
			continue
		var def: Dictionary = defs[str(ob["cls"])]
		var x: int = ob["x"]
		var y: int = ob["y"]
		var glb := _kies(def.get("varianten", [[(def["model"] as String).substr(7), 1.0]]), _hash(x, y, 20))
		var n := Natuur.instantie(glb)
		if n == null:
			continue
		var p := tegel_midden(Vector2i(x, y)) + Vector3((_hash(x, y, 1) - 0.5) * 0.9, 0, (_hash(x, y, 2) - 0.5) * 0.9)
		p.y = hoogte_op(p.x, p.z) - 0.05
		var s := 0.85 + _hash(x, y, 3) * 0.5
		n.transform = Transform3D(Basis(Vector3.UP, _hash(x, y, 4) * TAU).scaled(Vector3(s, s * (0.92 + _hash(x, y, 6) * 0.2), s)), p)
		bos.add_child(n)
		_sneeuwlaag_bomen.append(n)
		aantallen[glb] = int(aantallen.get(glb, 0)) + 1


## Winter: de `_sneeuw`-kinderen van de bomen aan (alleen bij verandering).
func zet_sneeuwlaag(aan: bool, geforceerd := false) -> void:
	if aan == _sneeuwlaag_aan and not geforceerd:
		return
	_sneeuwlaag_aan = aan
	for n in _sneeuwlaag_bomen:
		Natuur.zet_sneeuwlaag(n, aan)


## Decoratie uit data/objecten.json "decoratie": alleen weergave, geen sim.
func _bouw_decoratie() -> void:
	var dec: Dictionary = Gegevens.lees(Gegevens.OBJECTEN)["decoratie"]
	var deco := Node3D.new()
	deco.name = "Decoratie"
	add_child(deco)
	# afstand tot kaartobjecten (alles behalve dorpelingen)
	var bezet := {}
	for ob in w.objecten:
		if not ob["spawn"]:
			bezet[Vector2i(ob["x"], ob["y"])] = true
	for soort in ["rotsen", "struiken", "stronken"]:
		var d: Dictionary = dec[soort]
		var op: Dictionary = d["op"]
		var afstand: int = int(d.get("afstand", 0))
		var dorp_vrij: int = int(d.get("dorp_vrij", 0))
		var sc: Array = d.get("schaal", [1.0, 1.0])
		var sd: int = 40 + soort.length()
		for y in range(y0, y0 + ho):
			for x in range(x0, x0 + br):
				var sn := w.raster.soort_naam(x, y)
				if not op.has(sn) or _hash(x, y, sd) >= float(op[sn]):
					continue
				if afstand > 0:
					if w.raster.blok[w.raster.idx(x, y)] == 1 or _dichtbij(bezet, x, y, afstand):
						continue
				if dorp_vrij > 0 and maxi(absi(x - w.kampvuur.x), absi(y - w.kampvuur.y)) <= dorp_vrij:
					continue
				var lijst: Array = d["modellen"]
				var naam: String = lijst[int(_hash(x, y, sd + 1) * lijst.size()) % lijst.size()] if lijst[0] is String else _kies(lijst, _hash(x, y, sd + 1))
				var n := Natuur.instantie(naam)
				if n == null:
					continue
				var s := lerpf(sc[0], sc[1], _hash(x, y, sd + 2))
				var p := tegel_midden(Vector2i(x, y))
				var yaw := _hash(x, y, sd + 3) * TAU
				if soort == "rotsen":
					yaw = floorf(_hash(x, y, sd + 3) * 4.0) * PI * 0.5    # 2x2-tegels sluiten alleen in kwartslagen aan
				else:
					p += Vector3((_hash(x, y, sd + 4) - 0.5) * 1.2, 0, (_hash(x, y, sd + 5) - 0.5) * 1.2)
					p.y = hoogte_op(p.x, p.z)
				n.transform = Transform3D(Basis(Vector3.UP, yaw).scaled(Vector3(s, s * float(d.get("schaal_y", 1.0)), s)), p)
				deco.add_child(n)
				aantallen[naam] = int(aantallen.get(naam, 0)) + 1


func _dichtbij(bezet: Dictionary, x: int, y: int, r: int) -> bool:
	for dy in range(-r, r + 1):
		for dx in range(-r, r + 1):
			if bezet.has(Vector2i(x + dx, y + dy)):
				return true
	return false
