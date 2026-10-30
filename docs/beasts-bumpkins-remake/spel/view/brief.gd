class_name Brief
extends Control
## Een brief op perkament (briefing en hints), naar het briefscherm van het origineel (LETSCR: bruin perkament met
## gerafelde rand en een paarse lakzegel rechtsonder, kleuren daaruit gemeten). Klik, Enter of Spatie = weg.

signal gesloten

const PERKAMENT := Color8(115, 71, 39)
const RAND := Color8(78, 44, 20)
const ZEGEL := Color8(147, 0, 147)
const ZEGEL_DONKER := Color8(67, 7, 67)
const INKT := Color8(244, 228, 190)

var titel: Label
var tekst: Label
var voet: Label
var _rand: PackedVector2Array


func _init() -> void:
	mouse_filter = Control.MOUSE_FILTER_STOP
	titel = _label(26)
	tekst = _label(19)
	tekst.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	voet = _label(14)
	voet.modulate.a = 0.75
	voet.text = "klik om verder te spelen"
	visible = false


func _label(px: int) -> Label:
	var l := Label.new()
	l.add_theme_font_size_override("font_size", px)
	l.add_theme_color_override("font_color", INKT)
	l.add_theme_color_override("font_outline_color", Color(0.18, 0.09, 0.03))
	l.add_theme_constant_override("outline_size", 4)
	l.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	l.mouse_filter = Control.MOUSE_FILTER_IGNORE
	add_child(l)
	return l


## Toont de brief midden in beeld; `groot` = briefing (breder, met titel).
func toon(kop: String, inhoud: String, groot := false) -> void:
	var vp := get_viewport_rect().size if is_inside_tree() else Vector2(1600, 900)
	var b := 640.0 if groot else 520.0
	titel.text = kop
	titel.visible = kop != ""
	tekst.text = inhoud
	tekst.horizontal_alignment = HORIZONTAL_ALIGNMENT_LEFT if groot else HORIZONTAL_ALIGNMENT_CENTER
	var y := 34.0
	if titel.visible:
		titel.position = Vector2(40, y)
		titel.size = Vector2(b - 80, 34)
		y += 50.0
	tekst.position = Vector2(48, y)
	tekst.size = Vector2(b - 96, 0)
	tekst.custom_minimum_size = Vector2(b - 96, 0)
	var th := get_theme_default_font().get_multiline_string_size(inhoud, HORIZONTAL_ALIGNMENT_LEFT, b - 96, 19).y + 8.0
	y += th + 26.0
	voet.position = Vector2(40, y)
	voet.size = Vector2(b - 80, 20)
	size = Vector2(b, y + 56.0)
	position = Vector2((vp.x - size.x) * 0.5, maxf(40.0, (vp.y - size.y) * 0.42))
	_maak_rand()
	visible = true
	queue_redraw()


func sluit() -> void:
	if visible:
		visible = false
		gesloten.emit()


func _gui_input(e: InputEvent) -> void:
	if e is InputEventMouseButton and e.pressed:
		accept_event()
		sluit()


func _unhandled_key_input(e: InputEvent) -> void:
	if visible and e is InputEventKey and e.pressed and e.keycode in [KEY_ENTER, KEY_KP_ENTER, KEY_SPACE]:
		get_viewport().set_input_as_handled()
		sluit()


## Gerafelde rand: punten rondom met een vaste ruis (geen rng-toestand, zelfde brief = zelfde rand).
func _maak_rand() -> void:
	_rand = PackedVector2Array()
	var s := size
	var stap := 18.0
	var n := 0
	var zij := [[Vector2(0, 0), Vector2(s.x, 0), Vector2(0, -1)], [Vector2(s.x, 0), Vector2(s.x, s.y), Vector2(1, 0)],
		[Vector2(s.x, s.y), Vector2(0, s.y), Vector2(0, 1)], [Vector2(0, s.y), Vector2(0, 0), Vector2(-1, 0)]]
	for z in zij:
		var a: Vector2 = z[0]
		var e: Vector2 = z[1]
		var stappen := maxi(2, int(a.distance_to(e) / stap))
		for i in stappen:
			n += 1
			var f := float(i) / stappen
			var ruis := sin(n * 12.9898) * 43758.5453
			ruis = (ruis - floorf(ruis)) * 7.0
			_rand.append(a.lerp(e, f) - (z[2] as Vector2) * ruis)


func _draw() -> void:
	if _rand.size() < 3:
		return
	var schaduw := PackedVector2Array()
	for p in _rand:
		schaduw.append(p + Vector2(6, 8))
	draw_colored_polygon(schaduw, Color(0, 0, 0, 0.45))
	draw_colored_polygon(_rand, PERKAMENT)
	var lus := _rand.duplicate()
	lus.append(_rand[0])
	draw_polyline(lus, RAND, 3.0, true)
	# vlekken in het perkament
	for i in 9:
		var h := Vector2(fposmod(sin(i * 3.7) * 977.0, 1.0), fposmod(sin(i * 5.3) * 613.0, 1.0))
		draw_circle(Vector2(30, 30) + h * (size - Vector2(60, 60)), 18.0 + i * 3.0, Color(0, 0, 0, 0.05))
	# lakzegel met lint rechtsonder
	var c := Vector2(size.x - 52, size.y - 34)
	draw_colored_polygon(PackedVector2Array([c + Vector2(-12, 8), c + Vector2(-2, 8), c + Vector2(-10, 36), c + Vector2(-20, 30)]), ZEGEL_DONKER)
	draw_colored_polygon(PackedVector2Array([c + Vector2(2, 8), c + Vector2(12, 8), c + Vector2(20, 30), c + Vector2(10, 36)]), ZEGEL_DONKER)
	draw_circle(c, 24.0, ZEGEL_DONKER)
	draw_circle(c, 20.0, ZEGEL)
	draw_arc(c, 12.0, 0.0, TAU, 24, ZEGEL_DONKER, 2.5, true)
	draw_string(get_theme_default_font(), c + Vector2(-6, 7), "M", HORIZONTAL_ALIGNMENT_LEFT, -1, 18, ZEGEL_DONKER)
