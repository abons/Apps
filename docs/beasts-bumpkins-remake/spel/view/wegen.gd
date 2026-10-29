class_name Wegen
extends Node3D
## De wegen als keienstrook (shaders/weg.gdshader) over het terrein: per padtegel een achthoekje op het tegelmidden en een
## strook naar elke padburen (recht altijd, schuin alleen als de twee rechte tussenburen er niet allebei liggen, anders
## ontstaat er een driehoek). Volgt de grondhoogte. Wordt opnieuw opgebouwd bij Wereld.wegen_veranderd.

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
	var tm := w.tegel_m
	var half := BREED * 0.5
	for y in w.raster.rijen:
		for x in w.raster.kolommen:
			if w.raster.soort[w.raster.idx(x, y)] != pad:
				continue
			var c := Vector2((x + 0.5) * tm, (y + 0.5) * tm)
			# achthoek op het midden
			for i in 8:
				var a0 := TAU * i / 8.0
				var a1 := TAU * (i + 1) / 8.0
				_tri(st, _p(c.x, c.y), 0.0, _p(c.x + cos(a0) * half, c.y + sin(a0) * half), 1.0,
					_p(c.x + cos(a1) * half, c.y + sin(a1) * half), 1.0)
			# stroken naar de buren met een grotere index (elke verbinding een keer)
			for d in [Vector2i(1, 0), Vector2i(0, 1), Vector2i(1, 1), Vector2i(-1, 1)]:
				var n: Vector2i = Vector2i(x, y) + d
				if not w.raster.in_kaart(n.x, n.y) or w.raster.soort[w.raster.idx(n.x, n.y)] != pad:
					continue
				if d.x != 0 and d.y != 0:
					var a := w.raster.soort[w.raster.idx(x + d.x, y)] == pad
					var b := w.raster.soort[w.raster.idx(x, y + d.y)] == pad
					if a or b:
						continue
				var e := Vector2((n.x + 0.5) * tm, (n.y + 0.5) * tm)
				_strook(st, c, e, half)
	st.generate_normals()
	_mi.mesh = st.commit()
	_mi.material_override = mat


func _strook(st: SurfaceTool, a: Vector2, b: Vector2, half: float) -> void:
	var dir := (b - a).normalized()
	var zij := Vector2(-dir.y, dir.x) * half
	for i in STUKKEN:
		var p0 := a.lerp(b, float(i) / STUKKEN)
		var p1 := a.lerp(b, float(i + 1) / STUKKEN)
		var l0 := _p(p0.x + zij.x, p0.y + zij.y)
		var m0 := _p(p0.x, p0.y)
		var r0 := _p(p0.x - zij.x, p0.y - zij.y)
		var l1 := _p(p1.x + zij.x, p1.y + zij.y)
		var m1 := _p(p1.x, p1.y)
		var r1 := _p(p1.x - zij.x, p1.y - zij.y)
		_tri(st, l0, 1.0, m0, 0.0, m1, 0.0)
		_tri(st, l0, 1.0, m1, 0.0, l1, 1.0)
		_tri(st, m0, 0.0, r0, 1.0, r1, 1.0)
		_tri(st, m0, 0.0, r1, 1.0, m1, 0.0)


func _tri(st: SurfaceTool, a: Vector3, ra: float, b: Vector3, rb: float, c: Vector3, rc: float) -> void:
	for v in [[a, ra], [b, rb], [c, rc]]:
		st.set_color(Color(v[1], 0, 0))
		st.add_vertex(v[0])


func werk_seizoen(sneeuw: float, nat: float) -> void:
	mat.set_shader_parameter("sneeuw", sneeuw)
	mat.set_shader_parameter("nat", nat)
