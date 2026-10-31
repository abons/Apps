class_name Perkament
extends PanelContainer
## Perkamentpaneel voor het startmenu en het pauzemenu (view/startmenu.gd, view/pauzemenu.gd): dezelfde kleuren, gerafelde
## rand en lakzegel als de brief (view/brief.gd, naar LETSCR uit het origineel). Groeit met zijn inhoud mee
## (PanelContainer); `knop()` geeft een knop in dezelfde stijl.
## Maat: alles is in basis-px neergezet en het paneel krijgt `scale` = `Perkament.schaal()` (pc 1, touch zo dat de tekst
## >= 16 dp is en een knop >= 48 dp, zoals de brief).

const KNOP_H_PC := 44.0
const KNOP_H_TOUCH := 58.0          ## x schaal() (0,85 dp) = 49 dp
var zegel := true
var _rand: PackedVector2Array


func _init() -> void:
	mouse_filter = Control.MOUSE_FILTER_STOP
	var sb := StyleBoxEmpty.new()
	sb.content_margin_left = 44
	sb.content_margin_right = 44
	sb.content_margin_top = 30
	sb.content_margin_bottom = 68          # ruimte voor de lakzegel rechtsonder
	add_theme_stylebox_override("panel", sb)
	resized.connect(func() -> void:
		_rand = Brief.rand_punten(size)
		queue_redraw())


## Schaal van de basis-px: pc 1, touch 0,85 dp (tekst van 19 px wordt 16 dp), zoals Brief.toon.
static func schaal() -> float:
	return maxf(1.0, Scherm.dp() * 0.85)


static func knop_h() -> float:
	return KNOP_H_TOUCH if Bouwmenu.touch else KNOP_H_PC


## Label in inkt op perkament.
static func label(tekst: String, px: int, kleur := Brief.INKT) -> Label:
	var l := Label.new()
	l.text = tekst
	l.add_theme_font_size_override("font_size", px)
	l.add_theme_color_override("font_color", kleur)
	l.add_theme_color_override("font_outline_color", Color(0.18, 0.09, 0.03))
	l.add_theme_constant_override("outline_size", 4)
	l.mouse_filter = Control.MOUSE_FILTER_IGNORE
	return l


## Knop in de stijl van het perkament: donkerder bruin, rand in de randkleur, inkt; uitgeschakeld vaal.
static func knop(tekst: String, px := 20) -> Button:
	var b := Button.new()
	b.text = tekst
	b.focus_mode = Control.FOCUS_NONE
	b.custom_minimum_size = Vector2(0, knop_h())
	b.mouse_default_cursor_shape = Control.CURSOR_POINTING_HAND
	stijl(b, px)
	return b


static func stijl(b: Button, px := 20) -> void:
	b.add_theme_font_size_override("font_size", px)
	for st in ["normal", "hover", "pressed", "disabled", "focus"]:
		var sb := StyleBoxFlat.new()
		sb.bg_color = {"normal": Color8(92, 54, 28), "hover": Color8(128, 80, 44), "pressed": Color8(66, 37, 18),
			"disabled": Color8(96, 64, 42, 140), "focus": Color(0, 0, 0, 0)}[st]
		sb.border_color = Brief.RAND if st != "hover" else Color8(196, 150, 90)
		sb.set_border_width_all(2 if st != "focus" else 0)
		sb.set_corner_radius_all(5)
		sb.content_margin_left = 16
		sb.content_margin_right = 16
		sb.content_margin_top = 6
		sb.content_margin_bottom = 6
		b.add_theme_stylebox_override(st, sb)
	for c in ["font_color", "font_hover_color", "font_pressed_color", "font_focus_color"]:
		b.add_theme_color_override(c, Brief.INKT)
	b.add_theme_color_override("font_disabled_color", Color(Brief.INKT, 0.45))
	b.add_theme_color_override("font_outline_color", Color(0.18, 0.09, 0.03))
	b.add_theme_constant_override("outline_size", 4)


## Legt het paneel midden in een vlak van `vp` neer op schaal `s`; past het niet, dan kleiner (nooit buiten beeld).
func leg_midden(vp: Vector2, s: float) -> void:
	reset_size()
	var f := minf(s, minf((vp.x - 24.0) / maxf(1.0, size.x), (vp.y - 24.0) / maxf(1.0, size.y)))
	scale = Vector2(f, f)
	position = ((vp - size * f) * 0.5).floor()


func _draw() -> void:
	Brief.teken_perkament(self, _rand, zegel)
