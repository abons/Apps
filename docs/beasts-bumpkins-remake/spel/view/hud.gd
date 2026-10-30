class_name Hud
extends CanvasLayer
## Minimale HUD: linksboven de minikaart (view/minikaart.gd, zoals het origineel), daaronder tijd, seizoen, weer,
## selectie, tempo. Linksonder de besturing.

var w: Wereld
var bestuur: Bestuur
var label: Label
var minikaart: Minikaart
var hulp: Label
var kader: Control
var uitslag: Label
var hints: Hints                 ## sim/hints.gd; zet_hints()
var brief: Brief                 ## view/brief.gd: briefing en geopende hints
var rollen: VBoxContainer        ## ongelezen hints als rolletje rechts (origineel MAIL: opgerolde brief met zegel)
var _wachtrij: Array = []        ## brieven die nog open moeten: {kop, tekst, groot, pauze}
var _pauzeerde := false          ## de briefing zette de sim op pauze
var prijzen: Prijzenscherm       ## view/prijzen.gd: open met het goudstukken-icoon (munt_knop) of O
var munt_knop: Button


func bouw(wereld: Wereld, b: Bestuur) -> void:
	w = wereld
	bestuur = b
	minikaart = Minikaart.new()
	add_child(minikaart)
	minikaart.bouw(w, b.cam, b.view.terrein if b.view != null else null)
	var pc := PanelContainer.new()
	pc.position = Vector2(12, minikaart.position.y + minikaart.size.y + 8)
	pc.mouse_filter = Control.MOUSE_FILTER_IGNORE
	pc.add_theme_stylebox_override("panel", _stijl())
	label = Label.new()
	label.add_theme_font_size_override("font_size", 18)
	label.mouse_filter = Control.MOUSE_FILTER_IGNORE
	pc.add_child(label)
	add_child(pc)

	var pc2 := PanelContainer.new()
	pc2.mouse_filter = Control.MOUSE_FILTER_IGNORE
	pc2.add_theme_stylebox_override("panel", _stijl())
	pc2.set_anchors_preset(Control.PRESET_BOTTOM_LEFT)
	pc2.position = Vector2(12, -82)
	hulp = Label.new()
	hulp.add_theme_font_size_override("font_size", 13)
	hulp.mouse_filter = Control.MOUSE_FILTER_IGNORE
	hulp.text = "links: kader/klik = kiezen, klik grond = lopen, klik koe = claimen, klik loods = bouwer (30)   rechts klik = selectie weg   rechts slepen / Q E = draaien\nbouwen: knop rechtsboven, indrukken-slepen-loslaten = plaatsen (weg/hek: slepen = rij), blijft aan; Draai / wiel / R, Stop / rechts / Esc\nWASD/rand = pannen   wiel = zoom   Spatie pauze   O / munten = prijzen   1 2 4 tempo   K regen   N seizoen   Esc stop"
	pc2.add_child(hulp)
	add_child(pc2)

	uitslag = Label.new()
	uitslag.add_theme_font_size_override("font_size", 44)
	uitslag.add_theme_color_override("font_outline_color", Color.BLACK)
	uitslag.add_theme_constant_override("outline_size", 10)
	uitslag.set_anchors_preset(Control.PRESET_CENTER_TOP)
	uitslag.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	uitslag.grow_horizontal = Control.GROW_DIRECTION_BOTH
	uitslag.position.y = 90
	uitslag.mouse_filter = Control.MOUSE_FILTER_IGNORE
	uitslag.visible = false
	add_child(uitslag)
	w.missie_einde.connect(func(u: String) -> void:
		uitslag.text = "Missie geslaagd!" if u == "gewonnen" else "Missie mislukt"
		uitslag.add_theme_color_override("font_color", Color(1.0, 0.85, 0.3) if u == "gewonnen" else Color(1.0, 0.35, 0.3))
		uitslag.visible = true)

	kader = Control.new()
	kader.set_script(load("res://view/kader.gd"))
	add_child(kader)

	# goudstukken-icoon rechts naast de minikaart (origineel: eerste knop in de bovenbalk, hint 1-10) -> prijzenscherm
	munt_knop = MuntKnop.new()
	munt_knop.position = Vector2(minikaart.position.x + minikaart.size.x + 10, minikaart.position.y)
	munt_knop.tooltip_text = "prijzen (O)"
	add_child(munt_knop)
	prijzen = Prijzenscherm.new()
	add_child(prijzen)
	prijzen.bouw(w)
	munt_knop.pressed.connect(prijzen.wissel)


func _stijl() -> StyleBoxFlat:
	var sb := StyleBoxFlat.new()
	sb.bg_color = Color(0, 0, 0, 0.5)
	sb.set_content_margin_all(8)
	sb.set_corner_radius_all(4)
	return sb


func _process(_dt: float) -> void:
	var uur := w.uur()
	var h := int(uur)
	var m := int(fposmod(uur, 1.0) * 60.0)
	var tempo := "PAUZE" if w.gepauzeerd else "%dx" % int(w.tempo)
	var weer := "regen" if w.regent() else "droog"
	var doel: Dictionary = w.missie.get("doel", {})
	# achter het getal het missiedoel, alleen als de missie dat doel heeft (missie 1: dorpelingen en koeien, 2: kas)
	var kas := "%d" % w.kas + (" / >%d" % int(doel["kas_boven"]) if doel.has("kas_boven") else "")
	var dorp := "%d" % w.dorpelingen.size() + ("/%d" % int(doel["dorpelingen"]) if doel.has("dorpelingen") else "")
	var koe := "%d" % w.eigen_koeien() + ("/%d" % int(doel["koeien"]) if doel.has("koeien") else "")
	var geluk := "geluk: %d%%" % roundi(w.handel.dorp_geluk(w) * 100.0)   # sim/handel.gd, prijzen via het munt-icoon
	if w.handel.misdaad_aan(w):
		geluk += "   misdaden: %d" % w.handel.totaal_misdaden()
	label.text = "%02d:%02d%s  dag %d  %s  %s
kas: %s   dorpelingen: %s   koeien: %s   bedden: %d   brood: %d   melk: %d   eieren: %d
%s   geselecteerd: %d   tempo: %s" % [
		h, m, " (nacht)" if w.is_nacht() else "", w.dag_nr() + 1, w.seizoen_naam(), weer,
		kas, dorp, koe, w.bedden(), w.brood(), w.melk(), w.eieren(),
		geluk, bestuur.gekozen.size(), tempo]


# ---------------------------------------------------------------- briefing en hints (sim/hints.gd, data/hints.json)

## Koppelt de hints: de briefing gaat bij de start open (sim op pauze tot je hem wegklikt); een hint met `open` opent
## meteen als brief, een andere komt als rolletje rechts in beeld en opent bij een klik.
func zet_hints(h: Hints, met_briefing := true) -> void:
	hints = h
	rollen = VBoxContainer.new()
	rollen.set_anchors_preset(Control.PRESET_CENTER_RIGHT)
	rollen.grow_horizontal = Control.GROW_DIRECTION_BEGIN
	rollen.grow_vertical = Control.GROW_DIRECTION_BOTH
	rollen.offset_right = -14
	rollen.add_theme_constant_override("separation", 10)
	rollen.mouse_filter = Control.MOUSE_FILTER_IGNORE
	add_child(rollen)
	brief = Brief.new()
	add_child(brief)
	brief.gesloten.connect(_brief_dicht)
	h.hint_getoond.connect(_hint)
	if met_briefing and not h.briefing.is_empty():
		_wachtrij.append({"kop": h.briefing.get("titel", ""), "tekst": h.briefing.get("tekst", ""), "groot": true, "pauze": true})
		_volgende_brief()


func _hint(hint: Dictionary) -> void:
	if hint["open"]:
		_wachtrij.append({"kop": "", "tekst": hint["tekst"], "groot": false, "pauze": false})
		_volgende_brief()
		return
	var r := Rol.new()
	r.tooltip_text = "nieuwe hint"
	r.pressed.connect(func() -> void:
		r.queue_free()
		_wachtrij.append({"kop": "", "tekst": hint["tekst"], "groot": false, "pauze": false})
		_volgende_brief())
	rollen.add_child(r)


func _volgende_brief() -> void:
	if brief.visible or _wachtrij.is_empty():
		return
	var b: Dictionary = _wachtrij.pop_front()
	if b["pauze"] and not w.gepauzeerd:
		w.gepauzeerd = true
		_pauzeerde = true
	brief.toon(b["kop"], b["tekst"], b["groot"])


func _brief_dicht() -> void:
	if _pauzeerde:
		w.gepauzeerd = false
		_pauzeerde = false
	_volgende_brief()


func _unhandled_input(e: InputEvent) -> void:
	if e is InputEventKey and e.pressed and not e.echo and e.keycode == KEY_O and prijzen != null:
		prijzen.wissel()
		get_viewport().set_input_as_handled()


## Goudstukken-icoon (eigen tekening naar de knop in de bovenbalk van het origineel): steenknop met een stapel munten.
class MuntKnop extends Button:
	func _init() -> void:
		flat = true
		focus_mode = Control.FOCUS_NONE
		custom_minimum_size = Vector2(52, 52)
		size = custom_minimum_size
		mouse_default_cursor_shape = Control.CURSOR_POINTING_HAND

	func _draw() -> void:
		var r := Rect2(Vector2.ZERO, size)
		draw_rect(r, Color8(74, 80, 101))
		draw_rect(Rect2(0, 0, r.size.x, 3), Color8(128, 136, 160))
		draw_rect(Rect2(0, 0, 3, r.size.y), Color8(128, 136, 160))
		draw_rect(Rect2(0, r.size.y - 3, r.size.x, 3), Color8(36, 39, 52))
		draw_rect(Rect2(r.size.x - 3, 0, 3, r.size.y), Color8(36, 39, 52))
		if is_hovered():
			draw_rect(r.grow(-3), Color(1, 1, 1, 0.08))
		for m in [Vector2(17, 34), Vector2(27, 34), Vector2(37, 34), Vector2(22, 26), Vector2(32, 26), Vector2(27, 18)]:
			draw_circle(m + Vector2(0, 1.5), 7.0, Color8(150, 105, 25))
			draw_circle(m, 7.0, Color8(236, 190, 60))
			draw_circle(m, 3.2, Color8(250, 222, 120))


## Rolletje: opgerolde brief met rode zegel (naar MAIL uit het origineel), knippert zachtjes tot je erop klikt.
class Rol extends Button:
	func _init() -> void:
		flat = true
		focus_mode = Control.FOCUS_NONE
		custom_minimum_size = Vector2(64, 40)
		mouse_default_cursor_shape = Control.CURSOR_POINTING_HAND

	func _process(_dt: float) -> void:
		modulate.a = 0.75 + 0.25 * sin(Time.get_ticks_msec() * 0.006)

	func _draw() -> void:
		var r := Rect2(Vector2(8, 10), Vector2(48, 20))
		draw_rect(Rect2(r.position + Vector2(3, 4), r.size), Color(0, 0, 0, 0.4))
		draw_rect(r, Color8(214, 200, 160))
		draw_rect(Rect2(r.position, Vector2(r.size.x, 5)), Color8(240, 230, 200))
		draw_rect(Rect2(r.position + Vector2(0, r.size.y - 5), Vector2(r.size.x, 5)), Color8(150, 135, 100))
		for x in [r.position.x, r.end.x]:
			draw_circle(Vector2(x, r.get_center().y), r.size.y * 0.5, Color8(170, 150, 110))
			draw_circle(Vector2(x, r.get_center().y), r.size.y * 0.22, Color8(110, 90, 60))
		draw_circle(r.get_center(), 8.0, Color8(120, 10, 10))
		draw_circle(r.get_center(), 6.0, Color8(190, 30, 30))
