class_name Wegen
extends Node3D
## De wegen als keienstrook (shaders/weg.gdshader) over het terrein: per padtegel een achthoekje op het tegelmidden en een
## strook naar elke padburen (recht altijd, schuin alleen als de twee rechte tussenburen er niet allebei liggen, anders
## ontstaat er een driehoek), plus per gebouw een stoep van de deurtegel tot het deuranker. Volgt de grondhoogte. Wordt opnieuw opgebouwd bij Wereld.wegen_veranderd.

const BREED := 1.3          ## m, de keienstrook (origineel: ongeveer een halve tegel)
const BOVEN := 0.035        ## m boven de grond
const STUKKEN := 4          ## onderverdeling per strook, voor de hoogte

var w: Wereld
var terrein: TerreinView
var mat: ShaderMaterial
var _mi: MeshInstance3D


func bouw(wereld: Wereld, t: TerreinView) -> void:
	w = wereld
	terrein = t
	mat = ShaderMaterial.new()
	mat.shader = load("res://shaders/weg.gdshader")
	_mi = MeshInstance3D.new()
	_mi.name = "Wegen"
	_mi.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	add_child(_mi)
	herbouw()
	w.wegen_veranderd.connect(herbouw)


func _p(x: float, z: float) -> Vector3:
	return Vector3(x, terrein.hoogte_op(x, z) + BOVEN, z)


func herbouw() -> void:
	var st := SurfaceTool.new()
	st.begin(Mesh.PRIMITIVE_TRIANGLES)
	var pad := w.raster.namen.find("pad")
	var tegels: Array[Vector2i] = []
	for y in w.raster.rijen:
		for x in w.raster.kolommen:
			if _weg(w, x, y, pad):
				tegels.append(Vector2i(x, y))
	var is_weg := func(t: Vector2i) -> bool: return _weg(w, t.x, t.y, pad)
	net(st, tegels, is_weg, func(_t: Vector2i) -> bool: return true, w.tegel_m, _p)
	# de stoep: van het midden van de deurtegel naar het deuranker, binnen de voetafdruk
	for p in w.plannen:
		if p.klaar and Plan.DEUREN.has(p.soort):
			stoep(st, p, is_weg, w.tegel_m, _p)
	st.generate_normals()
	_mi.mesh = st.commit()
	_mi.material_override = mat


## Het keiennet in `st`: een achthoekje op elke tegel van `tegels` en een strook naar elke weg-buur (recht altijd, schuin
## alleen als de twee rechte tussenburen er niet allebei liggen, anders ontstaat er een driehoek). `is_weg(t)`: ligt er
## (straks) weg; `nieuw(t)`: hoort bij `tegels`, dan tekent de tegel met de grotere index de strook (elke verbinding een
## keer); een buur die niet nieuw is krijgt de strook altijd (de deurweg-ghost sluit zo aan op het bestaande pad).
## `p(x, z)`: punt op de grond. Ook voor de ghost (view/bouwmenu.gd _toon_pad), dus dezelfde vorm als straks de weg.
static func net(st: SurfaceTool, tegels: Array[Vector2i], is_weg: Callable, nieuw: Callable, tm: float, p: Callable) -> void:
	var half := BREED * 0.5
	for t in tegels:
		var c := (Vector2(t) + Vector2(0.5, 0.5)) * tm
		var m: Vector3 = p.call(c.x, c.y)
		for i in 8:
			var a0 := TAU * i / 8.0
			var a1 := TAU * (i + 1) / 8.0
			_tri(st, m, 0.0, p.call(c.x + cos(a0) * half, c.y + sin(a0) * half), 1.0,
				p.call(c.x + cos(a1) * half, c.y + sin(a1) * half), 1.0)
		for d: Vector2i in [Vector2i(1, 0), Vector2i(0, 1), Vector2i(1, 1), Vector2i(-1, 1),
				Vector2i(-1, 0), Vector2i(0, -1), Vector2i(-1, -1), Vector2i(1, -1)]:
			var n: Vector2i = t + d
			if not is_weg.call(n):
				continue
			var achter: bool = d.y < 0 or (d.y == 0 and d.x < 0)     # de andere kant van de vier hierboven
			if achter and nieuw.call(n):
				continue
			if d.x != 0 and d.y != 0 and (is_weg.call(Vector2i(t.x + d.x, t.y)) or is_weg.call(Vector2i(t.x, t.y + d.y))):
				continue
			strook(st, c, (Vector2(n) + Vector2(0.5, 0.5)) * tm, half, p)


## De stoep van plan `pl`: van het midden van de deurtegel naar het deuranker, binnen de voetafdruk (als daar weg ligt).
static func stoep(st: SurfaceTool, pl: Plan, is_weg: Callable, tm: float, p: Callable) -> void:
	var dt := pl.deur_tegel()
	if is_weg.call(dt):
		strook(st, (Vector2(dt) + Vector2(0.5, 0.5)) * tm, pl.deur_punt(tm), BREED * 0.5 * 0.85, p)


## Pad waar een weg te zien is: niet onder een blokkerend object (de vlag staat op het kaartpad; de weg gaat eromheen).
static func _weg(wereld: Wereld, x: int, y: int, pad: int) -> bool:
	var r := wereld.raster
	return r.in_kaart(x, y) and r.soort[r.idx(x, y)] == pad and r.blok[r.idx(x, y)] == 0


static func strook(st: SurfaceTool, a: Vector2, b: Vector2, half: float, p: Callable) -> void:
	var dir := (b - a).normalized()
	var zij := Vector2(-dir.y, dir.x) * half
	for i in STUKKEN:
		var p0 := a.lerp(b, float(i) / STUKKEN)
		var p1 := a.lerp(b, float(i + 1) / STUKKEN)
		var l0: Vector3 = p.call(p0.x + zij.x, p0.y + zij.y)
		var m0: Vector3 = p.call(p0.x, p0.y)
		var r0: Vector3 = p.call(p0.x - zij.x, p0.y - zij.y)
		var l1: Vector3 = p.call(p1.x + zij.x, p1.y + zij.y)
		var m1: Vector3 = p.call(p1.x, p1.y)
		var r1: Vector3 = p.call(p1.x - zij.x, p1.y - zij.y)
		_tri(st, l0, 1.0, m0, 0.0, m1, 0.0)
		_tri(st, l0, 1.0, m1, 0.0, l1, 1.0)
		_tri(st, m0, 0.0, r0, 1.0, r1, 1.0)
		_tri(st, m0, 0.0, r1, 1.0, m1, 0.0)


static func _tri(st: SurfaceTool, a: Vector3, ra: float, b: Vector3, rb: float, c: Vector3, rc: float) -> void:
	for v in [[a, ra], [b, rb], [c, rc]]:
		st.set_color(Color(v[1], 0, 0))
		st.add_vertex(v[0])


func werk_seizoen(sneeuw: float, nat: float) -> void:
	mat.set_shader_parameter("sneeuw", sneeuw)
	mat.set_shader_parameter("nat", nat)
