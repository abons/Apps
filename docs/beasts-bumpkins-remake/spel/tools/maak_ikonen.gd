extends SceneTree
## Bouwmenu-ikonen (besluit gebruiker 2026-10-31, bouwmenu variant A): per bouwsoort een klein plaatje gerenderd uit de
## eigen spel-glb (Bouwmenu.GEBOUWEN), geen originele sprites. Akker = akker_rijp, hek = palen met segmenten, poort =
## hek_poort, weg = een stukje keienweg (shaders/weg.gdshader) op gras. Schuin van voren (3/4), doorzichtige achtergrond.
## Met GPU (niet headless):
##   "$G" --path . -s tools/maak_ikonen.gd            -> ikonen/bouw/<soort>.png (256 x 256)
## Daarna `"$G" --headless --path . --import`. De png's staan in git (afgeleid van eigen modellen).

const MAAT := 256
const UIT := "res://ikonen/bouw/"

var _sv: SubViewport
var _cam: Camera3D
var _wortel: Node3D
var _lijst: Array = []


func _initialize() -> void:
	process_frame.connect(_start, CONNECT_ONE_SHOT)


func _start() -> void:
	DirAccess.make_dir_recursive_absolute(ProjectSettings.globalize_path(UIT))
	_sv = SubViewport.new()
	_sv.size = Vector2i(MAAT, MAAT)
	_sv.transparent_bg = true
	_sv.own_world_3d = true
	_sv.msaa_3d = Viewport.MSAA_8X
	_sv.render_target_update_mode = SubViewport.UPDATE_ALWAYS
	root.add_child(_sv)
	var omg := WorldEnvironment.new()
	var env := Environment.new()
	env.background_mode = Environment.BG_CLEAR_COLOR
	env.background_color = Color(0, 0, 0, 0)
	env.ambient_light_source = Environment.AMBIENT_SOURCE_COLOR
	env.ambient_light_color = Color(0.78, 0.76, 0.72)
	env.ambient_light_energy = 0.55
	env.tonemap_mode = Environment.TONE_MAPPER_FILMIC
	omg.environment = env
	_sv.add_child(omg)
	var zon := DirectionalLight3D.new()
	zon.rotation_degrees = Vector3(-50, 30, 0)
	zon.light_energy = 1.25
	zon.shadow_enabled = true
	_sv.add_child(zon)
	_cam = Camera3D.new()
	_cam.fov = 30.0
	_sv.add_child(_cam)
	_cam.make_current()
	for s: StringName in Bouwmenu.GEBOUWEN:
		await _render(s)
	print("[ikonen] klaar: ", _lijst)
	quit()


func _render(s: StringName) -> void:
	if _wortel != null:
		_wortel.free()
	_wortel = Node3D.new()
	_sv.add_child(_wortel)
	var g: Dictionary = Bouwmenu.GEBOUWEN[s]
	match s:
		&"akker":
			for t in [Vector3(-1, 0, -1), Vector3(1, 0, -1), Vector3(-1, 0, 1), Vector3(1, 0, 1)]:
				for naam in ["akker_kaal", "akker_rijp"]:
					var n := Natuur.instantie(naam)
					if n != null:
						n.position = t
						_wortel.add_child(n)
		&"hek":
			for i in 3:
				var p := Natuur.instantie("hek_paal")
				if p != null:
					p.position = Vector3(i * 2.0 - 2.0, 0, 0)
					_wortel.add_child(p)
				if i < 2:
					var sg := Natuur.instantie("hek_segment")
					if sg != null:
						sg.position = Vector3(i * 2.0 - 1.0, 0, 0)
						_wortel.add_child(sg)
		&"poort":
			var n := Natuur.instantie("hek_poort")
			if n != null:
				_wortel.add_child(n)
		&"weg":
			_wortel.add_child(_weg())
		_:
			var ps := load(String(g["glb"])) as PackedScene
			if ps == null:
				push_warning("ikonen: %s ontbreekt" % g["glb"])
				return
			var n: Node3D = ps.instantiate()
			n.rotation.y = float(g.get("draai", 0.0))
			_wortel.add_child(n)
	await process_frame
	var box := _omhulsel(_wortel, Transform3D.IDENTITY)
	if box.size == Vector3.ZERO:
		return
	# schuin van voren rechts (deur op +Z), helling ~30 graden zoals de spelcamera; afstand zodat het omhulsel past
	var dir := Vector3(0.55, 0.62, 1.0).normalized()
	var r := box.size.length() * 0.5
	var af := r / sin(deg_to_rad(_cam.fov * 0.5)) * 0.92
	var mid := box.get_center()
	_cam.global_position = mid + dir * af
	_cam.look_at(mid, Vector3.UP)
	for i in 8:
		await process_frame
	await RenderingServer.frame_post_draw
	var img := _sv.get_texture().get_image()
	img.convert(Image.FORMAT_RGBA8)
	# bijsnijden tot wat er staat en weer vullen tot MAAT met een kleine rand: elk ikoon even groot in zijn vakje
	var used := img.get_used_rect()
	if used.size.x > 0 and used.size.y > 0:
		var stuk := img.get_region(used)
		var f := float(MAAT - 12) / maxf(used.size.x, used.size.y)
		stuk.resize(maxi(1, roundi(used.size.x * f)), maxi(1, roundi(used.size.y * f)), Image.INTERPOLATE_LANCZOS)
		img = Image.create(MAAT, MAAT, false, Image.FORMAT_RGBA8)
		img.blit_rect(stuk, Rect2i(Vector2i.ZERO, stuk.get_size()), (Vector2i(MAAT, MAAT) - stuk.get_size()) / 2)
	var pad := UIT + String(s) + ".png"
	img.save_png(ProjectSettings.globalize_path(pad))
	_lijst.append(String(s))


## Een gebogen stuk keienweg op een grasvlak (COLOR.r = afstand tot de as, zoals view/wegen.gd).
func _weg() -> Node3D:
	var n := Node3D.new()
	var gras := MeshInstance3D.new()
	var pm := PlaneMesh.new()
	pm.size = Vector2(5.0, 5.0)
	gras.mesh = pm
	var gm := StandardMaterial3D.new()
	gm.albedo_color = Color(0.23, 0.36, 0.14)
	gras.material_override = gm
	n.add_child(gras)
	var st := SurfaceTool.new()
	st.begin(Mesh.PRIMITIVE_TRIANGLES)
	var punten: Array[Vector3] = []
	for i in 13:
		var t := i / 12.0
		punten.append(Vector3(lerpf(-2.4, 2.4, t), 0.03, sin(t * PI * 1.2 - 0.6) * 0.9))
	var breed := 0.65
	for i in punten.size() - 1:
		var a := punten[i]
		var b := punten[i + 1]
		var d := (b - a).normalized()
		var nrm := Vector3(-d.z, 0, d.x) * breed
		var quad := [[a - nrm, 1.0], [a, 0.0], [b - nrm, 1.0], [b, 0.0], [a + nrm, 1.0], [b + nrm, 1.0]]
		for tri in [[0, 1, 2], [1, 3, 2], [1, 4, 3], [4, 5, 3]]:
			for k in tri:
				st.set_color(Color(quad[k][1], 0, 0))
				st.set_normal(Vector3.UP)
				st.add_vertex(quad[k][0])
	var weg := MeshInstance3D.new()
	weg.mesh = st.commit()
	var mat := ShaderMaterial.new()
	mat.shader = load("res://shaders/weg.gdshader")
	weg.material_override = mat
	n.add_child(weg)
	return n


static func _omhulsel(n: Node, t: Transform3D) -> AABB:
	var uit := AABB()
	var eerste := true
	var tt := t * (n as Node3D).transform if n is Node3D else t
	if n is MeshInstance3D and (n as MeshInstance3D).mesh != null:
		uit = tt * (n as MeshInstance3D).get_aabb()
		eerste = false
	for c in n.get_children():
		var b := _omhulsel(c, tt)
		if b.size == Vector3.ZERO:
			continue
		uit = b if eerste else uit.merge(b)
		eerste = false
	return uit
