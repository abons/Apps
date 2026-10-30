class_name Minikaart
extends Control
## Minikaart linksboven, zoals het origineel (1_lefttop.png, 1.png): isometrisch (de tegelruit staat op zijn punt,
## tegel (0,0) boven), zwart buiten het verkende gebied (sim/mist.gd), terreinkleuren uit data/tegels.json `kleur`.
## Net als in het origineel een venster op vaste schaal dat met de camera meeschuift (het camerabrandpunt in het
## midden), niet de hele 192x192-kaart. Stippen: eigen dorpelingen, koeien, gebouwen, en wolven alleen op verkende
## tegels. Wit kader = wat de camera ziet (de hoeken van het beeld op de grond).
## Klik of tik = camera springt erheen; slepen = de camera schuift mee (de kaart staat stil zolang je drukt). Touch via
## emulate_mouse_from_touch (standaard aan), net als view/bouwmenu.gd.
## Tekenen: terrein- en mist-textuur alleen bijwerken als `mist.versie` of `raster.soort` verandert; de shader
## (shaders/minikaart.gdshader) vermenigvuldigt ze. Stippen en kader tekent `_laag` elk frame opnieuw.

const MAAT := Vector2(300, 186)        ## binnenmaat (px): het origineel 158x101 bij 640x480, x1,875 voor 900 hoog
const RAND := 7.0                      ## stenen rand rondom
const SCHAAL := 2.6                    ## px per tegel langs (x - y); verticaal de helft (2:1-isometrie)
const KLEUR_DORPELING := Color8(214, 70, 214)   ## paars, de spelerskleur (vlag en kleding in het origineel)
const KLEUR_KOE := Color8(245, 245, 240)
const KLEUR_KOE_WILD := Color8(190, 170, 140)
const KLEUR_GEBOUW := Color8(232, 196, 92)
const KLEUR_WOLF := Color8(230, 40, 30)
const GEEN_GEBOUW := [&"weg", &"hek"]

var w: Wereld
var cam: Camera3D                       ## rts_camera.gd
var terrein: TerreinView                ## hoogte voor het brandpunt; null mag (dan y = 0)
var midden := Vector2.ZERO              ## tegel (float) in het midden van het venster
var _vast := false                      ## knop ingedrukt: midden staat stil, de camera volgt de wijzer
var _binnen: Control                    ## knipt af op MAAT
var _kaart: Control                     ## tekent de terreintextuur met de shader
var _laag: Control                      ## stippen en kader
var _mat: ShaderMaterial
var _terrein_img: Image
var _terrein_tex: ImageTexture
var _mist_img: Image
var _mist_tex: ImageTexture
var _versie := -1
var _soort := PackedByteArray()
var _mist_aan := true
var _sinds_soort := 0.0


func bouw(wereld: Wereld, camera: Camera3D, tv: TerreinView = null) -> Minikaart:
	w = wereld
	cam = camera
	terrein = tv
	name = "Minikaart"
	position = Vector2(12, 12)
	size = MAAT + Vector2(RAND, RAND) * 2.0
	mouse_filter = Control.MOUSE_FILTER_STOP
	_binnen = Control.new()
	_binnen.position = Vector2(RAND, RAND)
	_binnen.size = MAAT
	_binnen.clip_contents = true
	_binnen.mouse_filter = Control.MOUSE_FILTER_IGNORE
	add_child(_binnen)
	_kaart = Control.new()
	_kaart.mouse_filter = Control.MOUSE_FILTER_IGNORE
	_kaart.texture_filter = CanvasItem.TEXTURE_FILTER_NEAREST
	_kaart.size = MAAT
	_mat = ShaderMaterial.new()
	_mat.shader = load("res://shaders/minikaart.gdshader")
	_kaart.material = _mat
	_kaart.draw.connect(_teken_kaart)
	_binnen.add_child(_kaart)
	_laag = Control.new()
	_laag.mouse_filter = Control.MOUSE_FILTER_IGNORE
	_laag.size = MAAT
	_laag.draw.connect(_teken_laag)
	_binnen.add_child(_laag)
	var r := w.raster
	_terrein_img = Image.create(r.kolommen, r.rijen, false, Image.FORMAT_RGB8)
	_terrein_tex = ImageTexture.create_from_image(_terrein_img)
	_mist_img = Image.create(r.kolommen, r.rijen, false, Image.FORMAT_R8)
	_mist_tex = ImageTexture.create_from_image(_mist_img)
	_mat.set_shader_parameter("verkend", _mist_tex)
	_werk_terrein_bij()
	_werk_mist_bij()
	midden = _cam_tegel()
	return self


# ---------------------------------------------------------------- omrekenen (ook voor test/minikaart_test.gd)

## Tegel (float, x/y in tegels) -> punt in het venster (px, linksboven van MAAT = 0,0).
func naar_venster(t: Vector2) -> Vector2:
	var d := t - midden
	return MAAT * 0.5 + Vector2(d.x - d.y, (d.x + d.y) * 0.5) * SCHAAL


## Punt in het venster -> tegel (float).
func naar_tegel(p: Vector2) -> Vector2:
	var q := (p - MAAT * 0.5) / SCHAAL     # q.x = dx - dy, q.y = (dx + dy) / 2
	return midden + Vector2(q.y + q.x * 0.5, q.y - q.x * 0.5)


func _cam_tegel() -> Vector2:
	if cam == null:
		return Vector2(w.kampvuur)
	var f: Vector3 = cam.get("doel_focus")
	return Vector2(f.x, f.z) / w.tegel_m


# ---------------------------------------------------------------- invoer

func _gui_input(e: InputEvent) -> void:
	if e is InputEventMouseButton and e.button_index == MOUSE_BUTTON_LEFT:
		_vast = e.pressed
		if e.pressed:
			spring(e.position - _binnen.position)
		accept_event()
	elif e is InputEventMouseMotion and _vast:
		if e.button_mask & MOUSE_BUTTON_MASK_LEFT:
			spring(e.position - _binnen.position)
		else:
			_vast = false
		accept_event()


## Zet het camerabrandpunt (direct, zonder naglijden) op de tegel onder vensterpunt `p` (px binnen MAAT).
func spring(p: Vector2) -> void:
	var t := naar_tegel(p)
	var xm := t.x * w.tegel_m
	var zm := t.y * w.tegel_m
	var y := terrein.hoogte_op(xm, zm) if terrein != null else 0.0
	if cam != null and cam.has_method("spring_naar"):
		cam.spring_naar(Vector3(xm, y, zm))


# ---------------------------------------------------------------- bijwerken en tekenen

func _process(dt: float) -> void:
	if w.mist.versie != _versie or w.mist.aan != _mist_aan:
		_werk_mist_bij()
	_sinds_soort += dt
	if _sinds_soort > 1.0:                 # wegen maken pad: eens per seconde vergelijken (native, 37k bytes)
		_sinds_soort = 0.0
		if w.raster.soort != _soort:
			_werk_terrein_bij()
	if not _vast:
		var doel := _cam_tegel()
		midden = doel if midden.distance_to(doel) > 40.0 else midden.lerp(doel, 1.0 - exp(-10.0 * dt))
	_kaart.queue_redraw()
	_laag.queue_redraw()


func _werk_terrein_bij() -> void:
	var r := w.raster
	_soort = r.soort.duplicate()
	var kl := PackedByteArray()
	kl.resize(r.namen.size() * 3)
	for i in r.namen.size():
		var c: Color = r.kleuren[i]
		kl[i * 3] = c.r8
		kl[i * 3 + 1] = c.g8
		kl[i * 3 + 2] = c.b8
	var px := PackedByteArray()
	px.resize(_soort.size() * 3)
	for i in _soort.size():
		var s := _soort[i] * 3
		px[i * 3] = kl[s]
		px[i * 3 + 1] = kl[s + 1]
		px[i * 3 + 2] = kl[s + 2]
	_terrein_img.set_data(r.kolommen, r.rijen, false, Image.FORMAT_RGB8, px)
	_terrein_tex.update(_terrein_img)


func _werk_mist_bij() -> void:
	_versie = w.mist.versie
	_mist_aan = w.mist.aan
	_mat.set_shader_parameter("aan", 1.0 if _mist_aan else 0.0)
	_mist_img.set_data(w.raster.kolommen, w.raster.rijen, false, Image.FORMAT_R8, w.mist.verkend)
	_mist_tex.update(_mist_img)


## Transform tegelruimte -> venster: x-as (S, S/2), y-as (-S, S/2), oorsprong zo dat `midden` in het midden staat.
func _xf() -> Transform2D:
	return Transform2D(Vector2(SCHAAL, SCHAAL * 0.5), Vector2(-SCHAAL, SCHAAL * 0.5), naar_venster(Vector2.ZERO))


func _teken_kaart() -> void:
	_kaart.draw_set_transform_matrix(_xf())
	_kaart.draw_texture_rect(_terrein_tex, Rect2(Vector2.ZERO, Vector2(w.raster.kolommen, w.raster.rijen)), false)
	_kaart.draw_set_transform_matrix(Transform2D.IDENTITY)


func _draw() -> void:
	# stenen rand zoals het origineel: grijs met donkere omtrek, binnen een verzonken zwarte kaart
	var sb := StyleBoxFlat.new()
	sb.bg_color = Color8(122, 126, 134)
	sb.set_corner_radius_all(9)
	sb.border_color = Color8(70, 72, 80)
	sb.set_border_width_all(2)
	sb.shadow_color = Color(0, 0, 0, 0.45)
	sb.shadow_size = 4
	draw_style_box(sb, Rect2(Vector2.ZERO, size))
	var binnen := Rect2(Vector2(RAND, RAND), MAAT)
	draw_rect(binnen.grow(2), Color8(52, 54, 60))
	var licht := Color8(176, 180, 188)
	draw_line(Vector2(binnen.position.x - 2, binnen.end.y + 2), binnen.end + Vector2(2, 2), licht, 2.0)
	draw_line(Vector2(binnen.end.x + 2, binnen.position.y - 2), binnen.end + Vector2(2, 2), licht, 2.0)
	draw_rect(binnen, Color.BLACK)


func _teken_laag() -> void:
	for p in w.plannen:
		if p.soort in GEEN_GEBOUW or not w.mist.is_verkend(p.tegel):
			continue
		var a := p.afdruk()
		var pts := PackedVector2Array([naar_venster(Vector2(a.position)),
			naar_venster(Vector2(a.end.x, a.position.y)), naar_venster(Vector2(a.end)),
			naar_venster(Vector2(a.position.x, a.end.y))])
		_laag.draw_colored_polygon(pts, KLEUR_GEBOUW if p.klaar else KLEUR_GEBOUW.darkened(0.4))
	for k in w.vee:
		if w.mist.is_verkend(k.tegel()):
			_stip(k.pos, KLEUR_KOE if k.eigenaar == 0 else KLEUR_KOE_WILD)
	for wf in w.wolven:
		if wf.leeft() and w.mist.is_verkend(wf.tegel()):
			_stip(wf.pos, KLEUR_WOLF)
	for d in w.dorpelingen:
		_stip(d.pos, KLEUR_DORPELING)
	var kader := _camera_kader()
	if kader.size() == 4:
		kader.append(kader[0])
		_laag.draw_polyline(kader, Color(1, 1, 1, 0.9), 1.0)


## Stip van 3x3 px met een donkere rand, zodat hij ook op zand en gras leesbaar is.
func _stip(pos: Vector2, kleur: Color) -> void:
	var p := naar_venster(pos).floor()
	_laag.draw_rect(Rect2(p - Vector2(2, 2), Vector2(5, 5)), Color(0, 0, 0, 0.7))
	_laag.draw_rect(Rect2(p - Vector2(1, 1), Vector2(3, 3)), kleur)


## De vier schermhoeken op de grond (y = 0), als vensterpunten. Een straal boven de horizon telt tot 300 m ver.
func _camera_kader() -> PackedVector2Array:
	var uit := PackedVector2Array()
	if cam == null or not cam.is_inside_tree():
		return uit
	var vp := cam.get_viewport().get_visible_rect().size
	for s in [Vector2(0, 0), Vector2(vp.x, 0), vp, Vector2(0, vp.y)]:
		var o := cam.project_ray_origin(s)
		var n := cam.project_ray_normal(s)
		var p: Vector3
		if n.y < -0.02:
			p = o + n * minf(-o.y / n.y, 300.0)
		else:
			p = o + Vector3(n.x, 0, n.z).normalized() * 300.0
		uit.append(naar_venster(Vector2(p.x, p.z) / w.tegel_m))
	return uit
