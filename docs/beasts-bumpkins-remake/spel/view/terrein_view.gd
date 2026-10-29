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
const SUB := 2              # mesh-cellen per tegel (per as)
const GRAS_RUIS := 0.05     # m, hoogteruis op gras en zand
var _sw := 0                # (br*SUB+1) x (ho*SUB+1) hoogtes van het mesh
var _sh := 0
var _sub_h := PackedFloat32Array()
var _hoek_t := PackedFloat32Array()   # (br+1) * (ho+1): 1 = rotsplateau-hoek, 0 = grondhoek (raakt een tegel buiten de rotsmassa)
var _hoek_g := PackedFloat32Array()   # grondhoogte
var _hoek_p := PackedFloat32Array()   # plateauhoogte (op grondhoeken: wat het plateau er zou hebben)
var _hoek_dw := PackedFloat32Array()  # gewicht van het fijne reliefdetail (0 aan de klifrand)
var _ruis := FastNoiseLite.new()
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


func _is_m(c: int, r: int) -> bool:
	var n := w.raster.soort_naam(c, r)
	return n == "rots" or n == "rotsrand"


func _tegel_h(c: int, r: int) -> float:
	if not w.raster.in_kaart(c, r):
		return w.raster.hoogte_soort[w.raster.namen.find("leeg")]
	return w.raster.hoogte_soort[w.raster.soort[w.raster.idx(c, r)]]


func _ci(i: int, j: int) -> int:
	return j * (br + 1) + i


## Hoogte op hoekcoordinaat (u, v) in tegels (float, relatief aan het venster): grond en plateau gemengd met een
## steile S-curve op de plateau-gewichten, plus fijn rotsreliëf op het plateau.
func _hoogte_hoek(u: float, v: float) -> float:
	var i := clampi(int(u), 0, br - 1)
	var j := clampi(int(v), 0, ho - 1)
	var fx := u - i
	var fy := v - j
	var a := _ci(i, j)
	var b := a + 1
	var c := a + (br + 1)
	var d := c + 1
	var w00 := (1.0 - fx) * (1.0 - fy)
	var w10 := fx * (1.0 - fy)
	var w01 := (1.0 - fx) * fy
	var w11 := fx * fy
	var t := _hoek_t[a] * w00 + _hoek_t[b] * w10 + _hoek_t[c] * w01 + _hoek_t[d] * w11
	var g := _hoek_g[a] * w00 + _hoek_g[b] * w10 + _hoek_g[c] * w01 + _hoek_g[d] * w11
	if t <= 0.0:
		return g
	var p := _hoek_p[a] * w00 + _hoek_p[b] * w10 + _hoek_p[c] * w01 + _hoek_p[d] * w11
	var dw := _hoek_dw[a] * w00 + _hoek_dw[b] * w10 + _hoek_dw[c] * w01 + _hoek_dw[d] * w11
	var f := smoothstep(0.2, 0.75, t)
	var xm := (x0 + u) * tegel_m
	var zm := (y0 + v) * tegel_m
	var detail := dw * f * (0.7 * _ruis.get_noise_2d(xm * 35.0, zm * 35.0) + 0.3 * _ruis.get_noise_2d(xm * 100.0 + 40.0, zm * 100.0))
	return lerpf(g, p, f) + detail


## Grondhoogte op wereldpositie (m), bilineair over het mesh.
func hoogte_op(xm: float, zm: float) -> float:
	var tx := (xm / tegel_m - x0) * SUB
	var ty := (zm / tegel_m - y0) * SUB
	if tx < 0.0 or ty < 0.0 or tx >= br * SUB or ty >= ho * SUB:
		return -2.0
	var i := int(tx)
	var j := int(ty)
	var fx := tx - i
	var fy := ty - j
	var k := j * _sw + i
	var a := lerpf(_sub_h[k], _sub_h[k + 1], fx)
	var b := lerpf(_sub_h[k + _sw], _sub_h[k + _sw + 1], fx)
	return lerpf(a, b, fy)


## Hoekdata: grond/plateau, afstand tot de rand van de rotsmassa, plateauhoogte met lage-frequentieruis.
func _bereken_hoeken() -> void:
	var n := (br + 1) * (ho + 1)
	_hoek_t.resize(n)
	_hoek_g.resize(n)
	_hoek_p.resize(n)
	_hoek_dw.resize(n)
	var dc := PackedFloat32Array()
	dc.resize(n)
	_ruis.noise_type = FastNoiseLite.TYPE_SIMPLEX_SMOOTH
	_ruis.seed = 7
	_ruis.frequency = 0.01
	for j in ho + 1:
		for i in br + 1:
			var som := 0.0
			var gr_n := 0
			var ruw := true
			for dj in 2:
				for di in 2:
					var c := x0 + i - 1 + di
					var r := y0 + j - 1 + dj
					if not _is_m(c, r):
						som += _tegel_h(c, r)
						gr_n += 1
						if _tegel_h(c, r) < 0.1:
							ruw = false
			var k := _ci(i, j)
			var g := 0.25
			if gr_n > 0:
				g = som / gr_n
				if ruw:
					g += GRAS_RUIS * _ruis.get_noise_2d((x0 + i) * tegel_m * 25.0, (y0 + j) * tegel_m * 25.0)
			_hoek_g[k] = g
			_hoek_t[k] = 1.0 if gr_n == 0 else 0.0
			dc[k] = 1000.0 if gr_n == 0 else 0.0
	# afstand (in tegels) tot de dichtstbijzijnde grondhoek: tweepasses-chamfer
	for pas in 2:
		var st := 1 if pas == 0 else -1
		var nabij := [[-st, 0, 1.0], [0, -st, 1.0], [-st, -st, 1.414], [st, -st, 1.414]]
		for jj in ho + 1:
			var j := jj if pas == 0 else ho - jj
			for ii in br + 1:
				var i := ii if pas == 0 else br - ii
				var k := _ci(i, j)
				for o in nabij:
					var ni: int = i + o[0]
					var nj: int = j + o[1]
					if ni < 0 or nj < 0 or ni > br or nj > ho:
						continue
					dc[k] = minf(dc[k], dc[_ci(ni, nj)] + o[2])
	for j in ho + 1:
		for i in br + 1:
			var k := _ci(i, j)
			var xm := (x0 + i) * tegel_m
			var zm := (y0 + j) * tegel_m
			var d := minf(dc[k], 6.0)
			var p := 2.7 + 0.5 * clampf(d - 1.0, 0.0, 3.0) + 0.45 * _ruis.get_noise_2d(xm * 3.0, zm * 3.0)
			p += 0.4 * clampf(d - 1.0, 0.0, 2.0) * _ruis.get_noise_2d(xm * 8.0 + 90.0, zm * 8.0)
			_hoek_p[k] = clampf(p, 2.3, 4.3)
			_hoek_dw[k] = clampf(0.4 + (d - 1.0) / 1.5, 0.0, 1.0)


func _bouw_terrein() -> void:
	_bereken_hoeken()
	_sw = br * SUB + 1
	_sh = ho * SUB + 1
	_sub_h.resize(_sw * _sh)
	var verts := PackedVector3Array()
	var normals := PackedVector3Array()
	var kleuren := PackedColorArray()
	var uvs := PackedVector2Array()
	var idx := PackedInt32Array()
	# splat per hoek (gemiddelde van de vier tegels), daarna bilineair naar de mesh-hoekpunten
	var hoek_c := PackedColorArray()
	var hoek_u := PackedVector2Array()
	hoek_c.resize((br + 1) * (ho + 1))
	hoek_u.resize((br + 1) * (ho + 1))
	for j in ho + 1:
		for i in br + 1:
			var c := Color(0, 0, 0, 0)
			var u := Vector2.ZERO
			for dj in 2:
				for di in 2:
					var sw := _splat(w.raster.soort_naam(x0 + i - 1 + di, y0 + j - 1 + dj))
					c += Color(sw[0], sw[1], sw[2], sw[3])
					u += Vector2(sw[4], sw[5])
			hoek_c[_ci(i, j)] = c / 4.0
			hoek_u[_ci(i, j)] = u / 4.0
	for j in _sh:
		for i in _sw:
			_sub_h[j * _sw + i] = _hoogte_hoek(float(i) / SUB, float(j) / SUB)
	var stap := tegel_m / SUB
	for j in _sh:
		for i in _sw:
			var hh := _sub_h[j * _sw + i]
			verts.append(Vector3((x0 + float(i) / SUB) * tegel_m, hh, (y0 + float(j) / SUB) * tegel_m))
			var hl := _sub_h[j * _sw + maxi(i - 1, 0)]
			var hr := _sub_h[j * _sw + mini(i + 1, _sw - 1)]
			var hu := _sub_h[maxi(j - 1, 0) * _sw + i]
			var hd := _sub_h[mini(j + 1, _sh - 1) * _sw + i]
			normals.append(Vector3(hl - hr, 2.0 * stap, hu - hd).normalized())
			var ci := mini(i / SUB, br - 1)
			var cj := mini(j / SUB, ho - 1)
			var fx := float(i - ci * SUB) / SUB
			var fy := float(j - cj * SUB) / SUB
			var a := _ci(ci, cj)
			var wa := (1.0 - fx) * (1.0 - fy)
			var wb := fx * (1.0 - fy)
			var wc := (1.0 - fx) * fy
			var wd := fx * fy
			kleuren.append(hoek_c[a] * wa + hoek_c[a + 1] * wb + hoek_c[a + br + 1] * wc + hoek_c[a + br + 2] * wd)
			uvs.append(hoek_u[a] * wa + hoek_u[a + 1] * wb + hoek_u[a + br + 1] * wc + hoek_u[a + br + 2] * wd)
	for j in _sh - 1:
		for i in _sw - 1:
			var a := j * _sw + i
			var b := a + 1
			var d := a + _sw
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
		"pad": return [0.55, 0.0, 0.0, 0.45, 0.0, 0.6]    # vertrapte grond; de keien zelf komen van view/wegen.gd
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
		var vw: int = ob["voetafdruk"][0]
		var vd: int = ob["voetafdruk"][1]
		if vw > 1 or vd > 1:       # model in het midden van de voetafdruk (tegels vanaf x,y)
			n.position += Vector3((vw - 1) * 0.5 * tegel_m, 0, (vd - 1) * 0.5 * tegel_m)
			n.position.y = hoogte_op(n.position.x, n.position.z)
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
	_bouw_kliffen(deco)
	_bouw_rotsen(deco, dec["rotsen"])
	for soort in ["struiken", "stronken"]:
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


## Per rotstegel: welke hoeken zijn grond (raken een tegel buiten de massa)? Bitmasker NW=1, NE=2, SE=4, SW=8.
func _grondhoeken(c: int, r: int) -> int:
	var i := c - x0
	var j := r - y0
	var m := 0
	if _hoek_t[_ci(i, j)] == 0.0: m |= 1
	if _hoek_t[_ci(i + 1, j)] == 0.0: m |= 2
	if _hoek_t[_ci(i + 1, j + 1)] == 0.0: m |= 4
	if _hoek_t[_ci(i, j + 1)] == 0.0: m |= 8
	return m


## Kliffen: een klif_*-stuk op elke rotstegel met grond- en plateauhoeken, gekozen op het patroon van de grondhoeken
## (2 naburige = recht, 3 = buitenhoek, 1 = binnenhoek), y-geschaald van de grondhoogte naar het plateau (stuk = 2,0 m stap).
func _bouw_kliffen(deco: Node3D) -> void:
	var kl := Node3D.new()
	kl.name = "Kliffen"
	deco.add_child(kl)
	# patroon -> [model, draaiing (graden)]; yaw 0 = open naar zuid (+z), model heeft zijn hoge kant op -z
	var tabel := {
		12: ["klif_recht", 0], 6: ["klif_recht", 90], 3: ["klif_recht", 180], 9: ["klif_recht", 270],
		14: ["klif_hoek_buiten", 0], 7: ["klif_hoek_buiten", 90], 11: ["klif_hoek_buiten", 180], 13: ["klif_hoek_buiten", 270],
		4: ["klif_hoek_binnen", 0], 2: ["klif_hoek_binnen", 90], 1: ["klif_hoek_binnen", 180], 8: ["klif_hoek_binnen", 270]}
	for r in range(y0, y0 + ho):
		for c in range(x0, x0 + br):
			if not _is_m(c, r):
				continue
			var m := _grondhoeken(c, r)
			if not tabel.has(m):
				continue
			var i := c - x0
			var j := r - y0
			var lage := 0.0
			var n_lage := 0
			var hoge := 0.0
			var n_hoge := 0
			for k in 4:
				var hi := i + (1 if k == 1 or k == 2 else 0)
				var hj := j + (1 if k >= 2 else 0)
				if (m >> k) & 1:
					lage += _hoek_g[_ci(hi, hj)]
					n_lage += 1
				else:
					hoge += _hoogte_hoek(hi, hj)
					n_hoge += 1
			var laag := maxf(lage / n_lage, -0.45)
			var top := hoge / n_hoge
			var sy := clampf((top - laag + 0.05) / 2.0, 0.7, 1.7)
			var inst := Natuur.instantie(tabel[m][0])
			if inst == null:
				continue
			var p := Vector3((c + 0.5) * tegel_m, laag - 0.03, (r + 0.5) * tegel_m)
			inst.transform = Transform3D(Basis(Vector3.UP, deg_to_rad(float(tabel[m][1]))).scaled(Vector3(1, sy, 1)), p)
			kl.add_child(inst)
			aantallen[tabel[m][0]] = int(aantallen.get(tabel[m][0], 0)) + 1


## Rotsen op het plateau: weinig en groot, gedraaid en deels in de grond. Zuilen (rotstegel zonder plateauhoek, bv. een
## rots in het water) krijgen er een uit de grond.
func _bouw_rotsen(deco: Node3D, d: Dictionary) -> void:
	var lijst: Array = d["modellen"]
	var kans: float = float(d.get("kans", 0.2))
	var sc: Array = d.get("schaal", [0.9, 1.6])
	var sink: float = float(d.get("zak", 0.3))
	for r in range(y0, y0 + ho):
		for c in range(x0, x0 + br):
			if not _is_m(c, r):
				continue
			var m := _grondhoeken(c, r)
			var zuil := m == 15 or m == 5 or m == 10
			if m != 0 and not zuil:
				continue
			if zuil:
				if _hash(c, r, 61) > 0.7:
					continue
			elif _hash(c, r, 60) >= kans:
				continue
			var naam: String = lijst[int(_hash(c, r, 62) * lijst.size()) % lijst.size()]
			var n := Natuur.instantie(naam)
			if n == null:
				continue
			var s := lerpf(sc[0], sc[1], _hash(c, r, 63))
			if zuil:
				s = lerpf(0.9, 1.3, _hash(c, r, 63))
			var p := Vector3((c + 0.5 + (_hash(c, r, 64) - 0.5) * 0.8) * tegel_m, 0, (r + 0.5 + (_hash(c, r, 65) - 0.5) * 0.8) * tegel_m)
			p.y = (hoogte_op(p.x, p.z) - sink * s) if not zuil else -0.7
			var yaw := _hash(c, r, 66) * TAU
			n.transform = Transform3D(Basis(Vector3.UP, yaw).scaled(Vector3(s, s * lerpf(0.9, 1.15, _hash(c, r, 67)), s)), p)
			deco.add_child(n)
			aantallen[naam] = int(aantallen.get(naam, 0)) + 1
