class_name Portret
extends PanelContainer
## Portret van de gekozen dorpeling rechtsonder (besluit gebruiker 2026-10-31; origineel: statbust rechtsonder met zijn
## gedachtewolkje). Kop = het Gemini-portret van zijn soort of rol (spel.json `portret`, bestand_voor; besluit gebruiker
## 2026-10-31), bijgesneden (`uitsnede`) en op maat geschaald met ronde hoeken in een rand. Die png's zijn afgeleid van
## het originele statbust en staan niet in git (sync.ps1 kopieert ze naar assets/portret/). Ontbreekt de png: terugval
## op een render uit het eigen bumpkin-model (Bumpkin.glb_voor) in een eigen SubViewport, een paar frames na elke wissel
## en daarna niet meer (goedkoop op mobiel).
## Pc: kop, naam, gezondheidsbalk en de gedachte met zijn betekenis en wat je eraan doet (sim/gedachten.gd uitleg);
## inklapbaar met het streepje (alleen nog naam, balk en ikoon), bewaard in user://hud.cfg (view/hud.gd).
## Touch: compact, kop + balk + ikoon, geen tekst (gebruiker: geen kleine teksten op de telefoon).

signal ingeklapt_gewisseld

const RENDER_FRAMES := 6          ## zoveel frames rendert de SubViewport na een wissel (animatieboom staat dan stil)
const KOP_PC := 110.0             ## px: kop op de pc
const KOP_TOUCH := 80.0           ## dp: kop op touch (compact)
const HOEK := 10.0                ## hoekstraal van kop en rand (x k)

var w: Wereld
var touch := false
var k := 1.0                      ## schaal (touch: dp)
var ingeklapt := false
var dorpeling: Dorpeling = null

var _sv: SubViewport
var _cam: Camera3D
var _model: Bumpkin
var _model_glb := "?"
var png := ""                     ## het getoonde portretbestand; "" = de 3D-terugval
static var _png_cache := {}       ## "pad|px" -> ImageTexture (bijgesneden, geschaald, ronde hoeken)
var _render_n := 0
var _kop: TextureRect
var _naam: Label
var _balk: Balk
var _ikoon: TextureRect
var _tekst: Label
var _uitleg: Label
var _knop: Button
var _info: VBoxContainer
var _g: StringName = &"-"


func bouw(wereld: Wereld, is_touch: bool, schaal: float) -> void:
	w = wereld
	touch = is_touch
	k = schaal
	name = "Portret"
	mouse_filter = Control.MOUSE_FILTER_STOP
	var sb := StyleBoxFlat.new()
	sb.bg_color = Color(0.08, 0.07, 0.06, 0.78)
	sb.border_color = Color(0.55, 0.45, 0.3, 0.9)
	sb.set_border_width_all(2)
	sb.set_corner_radius_all(int(8 * k))
	sb.set_content_margin_all(8 * k)
	add_theme_stylebox_override("panel", sb)
	_sv = SubViewport.new()
	_sv.size = Vector2i(roundi(160 * k), roundi(160 * k))
	_sv.own_world_3d = true
	_sv.transparent_bg = true
	_sv.msaa_3d = Viewport.MSAA_4X
	_sv.render_target_update_mode = SubViewport.UPDATE_DISABLED
	add_child(_sv)
	var omg := WorldEnvironment.new()
	var env := Environment.new()
	env.background_mode = Environment.BG_CLEAR_COLOR
	env.ambient_light_source = Environment.AMBIENT_SOURCE_COLOR
	env.ambient_light_color = Color(0.75, 0.72, 0.68)
	env.ambient_light_energy = 0.7
	omg.environment = env
	_sv.add_child(omg)
	var zon := DirectionalLight3D.new()
	zon.light_energy = 1.3
	zon.rotation = Vector3(deg_to_rad(-35), deg_to_rad(30), 0)
	_sv.add_child(zon)
	_cam = Camera3D.new()
	_cam.fov = 30
	_sv.add_child(_cam)

	var rij := HBoxContainer.new()
	rij.add_theme_constant_override("separation", int(8 * k))
	rij.mouse_filter = Control.MOUSE_FILTER_IGNORE
	add_child(rij)
	_kop = TextureRect.new()
	_kop.name = "Kop"
	_kop.texture = _sv.get_texture()
	_kop.custom_minimum_size = Vector2(KOP_PC, KOP_PC) * k if not touch else Vector2(KOP_TOUCH, KOP_TOUCH) * k
	_kop.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
	_kop.stretch_mode = TextureRect.STRETCH_KEEP_ASPECT_CENTERED
	_kop.mouse_filter = Control.MOUSE_FILTER_IGNORE
	rij.add_child(_kop)
	var rand := Rand.new()
	rand.straal = int(HOEK * k)
	rand.set_anchors_preset(Control.PRESET_FULL_RECT)
	_kop.add_child(rand)
	_info = VBoxContainer.new()
	_info.add_theme_constant_override("separation", int(4 * k))
	_info.mouse_filter = Control.MOUSE_FILTER_IGNORE
	_info.alignment = BoxContainer.ALIGNMENT_CENTER
	rij.add_child(_info)
	var kop_rij := HBoxContainer.new()
	kop_rij.mouse_filter = Control.MOUSE_FILTER_IGNORE
	_info.add_child(kop_rij)
	_naam = Label.new()
	_naam.add_theme_font_size_override("font_size", 18)
	_naam.add_theme_color_override("font_color", Color(1.0, 0.92, 0.75))
	_naam.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	_naam.mouse_filter = Control.MOUSE_FILTER_IGNORE
	_naam.visible = not touch
	kop_rij.add_child(_naam)
	_knop = Button.new()
	_knop.focus_mode = Control.FOCUS_NONE
	_knop.flat = true
	_knop.add_theme_font_size_override("font_size", 16)
	_knop.custom_minimum_size = Vector2(26, 22)
	_knop.mouse_default_cursor_shape = Control.CURSOR_POINTING_HAND
	_knop.pressed.connect(func() -> void:
		zet_ingeklapt(not ingeklapt)
		ingeklapt_gewisseld.emit())
	_knop.visible = not touch
	kop_rij.add_child(_knop)
	_balk = Balk.new()
	_balk.custom_minimum_size = Vector2(150, 10) * k if not touch else Vector2(80, 12) * k
	_info.add_child(_balk)
	var g_rij := HBoxContainer.new()
	g_rij.add_theme_constant_override("separation", int(6 * k))
	g_rij.mouse_filter = Control.MOUSE_FILTER_IGNORE
	_info.add_child(g_rij)
	_ikoon = TextureRect.new()
	_ikoon.custom_minimum_size = Vector2(48, 48) * k
	_ikoon.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
	_ikoon.stretch_mode = TextureRect.STRETCH_KEEP_ASPECT_CENTERED
	_ikoon.mouse_filter = Control.MOUSE_FILTER_IGNORE
	g_rij.add_child(_ikoon)
	var tv := VBoxContainer.new()
	tv.add_theme_constant_override("separation", 0)
	tv.alignment = BoxContainer.ALIGNMENT_CENTER
	tv.mouse_filter = Control.MOUSE_FILTER_IGNORE
	tv.visible = not touch
	g_rij.add_child(tv)
	_tekst = Label.new()
	_tekst.add_theme_font_size_override("font_size", 17)
	_tekst.mouse_filter = Control.MOUSE_FILTER_IGNORE
	tv.add_child(_tekst)
	_uitleg = Label.new()
	_uitleg.add_theme_font_size_override("font_size", 13)
	_uitleg.add_theme_color_override("font_color", Color(0.8, 0.8, 0.78))
	_uitleg.mouse_filter = Control.MOUSE_FILTER_IGNORE
	tv.add_child(_uitleg)
	zet_ingeklapt(ingeklapt)
	visible = false


func zet_ingeklapt(aan: bool) -> void:
	ingeklapt = aan
	_kop.visible = not aan
	if _uitleg != null:
		_uitleg.visible = not aan
	_knop.text = "+" if aan else "–"
	_knop.tooltip_text = "portret uitklappen" if aan else "portret inklappen"
	reset_size()


## Elke frame vanuit de HUD: d = de (eerste) gekozen dorpeling of null.
func zet(d: Dorpeling) -> void:
	if d != null and not d.leeft():
		d = null
	visible = d != null
	if d == null:
		dorpeling = null
		_sv.render_target_update_mode = SubViewport.UPDATE_DISABLED
		return
	var nieuw := d != dorpeling
	dorpeling = d
	var p := bestand_voor(w.spel, d.geslacht, d.leeftijd, d.rol)
	if p != png:
		png = p
		_kop.texture = png_textuur(png, roundi(_kop.custom_minimum_size.x), float(w.spel.get("portret", {}).get("uitsnede", 0.0)), HOEK * k) 				if png != "" else _sv.get_texture()
		_render_n = RENDER_FRAMES if png == "" else 0
	if png == "":
		var glb := Bumpkin.glb_voor(d.geslacht, d.leeftijd, d.rol)
		if glb != _model_glb:
			_wissel_model(glb, d.leeftijd == "kind")
	if nieuw:
		_naam.text = d.naam if d.naam != "" else "dorpeling %d" % d.id
		_render_n = RENDER_FRAMES if png == "" else 0
	_balk.deel = d.gezondheid / maxf(1.0, d.gezondheid_max)
	_balk.queue_redraw()
	var g := Gedachten.van(w, d)
	if g != _g or nieuw:
		_g = g
		var ik := Gedachten.ikoon(g)
		_ikoon.texture = GedachteIkonen.textuur(ik, true, Gedachten.dringend(g), 1.0) if ik != "" else null
		_ikoon.visible = ik != ""
		_tekst.text = Gedachten.tekst(g) if g != &"" else "Niets bijzonders"
		_tekst.add_theme_color_override("font_color", Color(1.0, 0.55, 0.45) if Gedachten.dringend(g) else Color(1, 1, 1))
	_uitleg.text = Gedachten.uitleg(w, d, g)
	if _render_n > 0:
		_render_n -= 1
		_sv.render_target_update_mode = SubViewport.UPDATE_ALWAYS
		_richt()
	else:
		_sv.render_target_update_mode = SubViewport.UPDATE_DISABLED


## Sleutel in spel.json `portret.soort`, zoals Bumpkin.glb_voor: kind = jongen/meisje, oud = oude_man/oude_vrouw.
static func soort_sleutel(geslacht: String, leeftijd: String) -> String:
	var v := geslacht == "vrouw"
	if leeftijd == "kind":
		return "meisje" if v else "jongen"
	if leeftijd == "oud":
		return "oude_vrouw" if v else "oude_man"
	return "vrouw" if v else "man"


## Het portretbestand voor deze dorpeling (rol gaat voor soort), "" als het niet in de data staat of ontbreekt (dan
## de 3D-terugval). Een rol met een eigen bestand dat ontbreekt valt ook terug op 3D (het rolmodel), niet op de soort.
static func bestand_voor(spel: Dictionary, geslacht: String, leeftijd: String, rol := "") -> String:
	var c: Dictionary = spel.get("portret", {})
	var b := ""
	if rol != "" and (c.get("rol", {}) as Dictionary).has(rol):
		b = c["rol"][rol]
	else:
		b = (c.get("soort", {}) as Dictionary).get(soort_sleutel(geslacht, leeftijd), "")
	if b == "":
		return ""
	var p := String(c.get("map", "res://assets/portret/")) + b
	return p if ResourceLoader.exists(p) else ""


## Het portret als vierkante textuur van `px`: `uitsnede` van elke kant eraf (de grijze rand), Lanczos naar px
## (scherp zonder mipmaps, ook als de bron op Android VRAM-gecomprimeerd is) en ronde hoeken met straal `hoek`.
static func png_textuur(pad: String, px: int, uitsnede: float, hoek: float) -> Texture2D:
	var sl := "%s|%d|%.3f|%d" % [pad, px, uitsnede, roundi(hoek)]
	if _png_cache.has(sl):
		return _png_cache[sl]
	var tex := load(pad) as Texture2D
	if tex == null:
		return null
	var img := tex.get_image()
	if img == null:
		return tex
	if img.is_compressed():
		img.decompress()
	img.convert(Image.FORMAT_RGBA8)
	var z := mini(img.get_width(), img.get_height())
	var rand := roundi(z * clampf(uitsnede, 0.0, 0.4))
	var maat := z - 2 * rand
	img = img.get_region(Rect2i((img.get_width() - z) / 2 + rand, (img.get_height() - z) / 2 + rand, maat, maat))
	img.resize(px, px, Image.INTERPOLATE_LANCZOS)
	var r := maxf(hoek, 0.0)
	if r > 0.5:
		for y in px:
			for x in px:
				var cx := clampf(x + 0.5, r, px - r)
				var cy := clampf(y + 0.5, r, px - r)
				var af := Vector2(x + 0.5 - cx, y + 0.5 - cy).length()
				if af > r - 1.0:
					var c := img.get_pixel(x, y)
					c.a *= clampf(r - af, 0.0, 1.0)
					img.set_pixel(x, y, c)
	var uit := ImageTexture.create_from_image(img)
	_png_cache[sl] = uit
	return uit


func _wissel_model(glb: String, kind: bool) -> void:
	_model_glb = glb
	if _model != null:
		_model.queue_free()
	_model = Bumpkin.new()
	if glb != "":
		_model.glb = glb
	elif kind:
		_model.scale = Vector3.ONE * 0.81
	_model.rotation.y = deg_to_rad(20)      # iets gedraaid, zoals een borstbeeld
	_sv.add_child(_model)
	_render_n = RENDER_FRAMES


## Camera op het borstbeeld: het Head-bot als het er is, anders een vaste hoogte.
func _richt() -> void:
	if _model == null:
		return
	var hoofd := _model.global_position + Vector3(0, 1.6 * _model.scale.y, 0)
	var sk := _model.find_child("Skeleton3D", true, false) as Skeleton3D
	if sk != null:
		var i := sk.find_bone("Head")
		if i >= 0:
			hoofd = sk.global_transform * sk.get_bone_global_pose(i).origin
	var schaal := hoofd.y / 1.6       # kinderen kleiner: dichterbij
	var doel := hoofd + Vector3(0, 0.1, 0) * schaal      # het bot zit onder in het hoofd; midden = kin tot kruin
	_cam.position = doel + Vector3(0, 0.06, 1.45) * schaal
	_cam.look_at(doel)


## Rand om de kop: ronde hoeken in de kleur van het paneel (de png heeft dezelfde hoeken).
class Rand extends Control:
	var straal := 10

	func _ready() -> void:
		mouse_filter = Control.MOUSE_FILTER_IGNORE

	func _draw() -> void:
		var sb := StyleBoxFlat.new()
		sb.draw_center = false
		sb.border_color = Color(0.72, 0.58, 0.36, 0.95)
		sb.set_border_width_all(2)
		sb.set_corner_radius_all(straal)
		sb.anti_aliasing = true
		draw_style_box(sb, Rect2(Vector2.ZERO, size))


## Gezondheidsbalk: groen > geel > rood.
class Balk extends Control:
	var deel := 1.0

	func _ready() -> void:
		mouse_filter = Control.MOUSE_FILTER_IGNORE

	func _draw() -> void:
		var r := Rect2(Vector2.ZERO, size)
		draw_rect(r, Color(0.1, 0.05, 0.04, 0.9))
		var f := clampf(deel, 0.0, 1.0)
		var kleur := Color(0.85, 0.2, 0.15).lerp(Color(0.95, 0.8, 0.2), clampf(f * 2.0, 0.0, 1.0))
		if f > 0.5:
			kleur = Color(0.95, 0.8, 0.2).lerp(Color(0.35, 0.8, 0.3), (f - 0.5) * 2.0)
		draw_rect(Rect2(r.position + Vector2(1, 1), Vector2((r.size.x - 2) * f, r.size.y - 2)), kleur)
		draw_rect(r, Color(0, 0, 0, 0.8), false, 1.0)
