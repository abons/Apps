class_name Prijzenscherm
extends Control
## Prijzenscherm (sim/handel.gd): open met het goudstukken-icoon naast de minikaart of met O, naar het economiescherm
## van het origineel (STATS: grijsblauw steenpaneel, per waar een schuif van een paar munten links naar een stapel goud
## rechts). Eigen tekening, geen originele sprites. Per waar - / + of klik/sleep op de balk (muis en vinger:
## emulate_mouse_from_touch). Eronder het geluk van het dorp en, als de missie misdaad heeft, de misdaden.
## Open = de sim staat op pauze (zoals de briefing); dicht met Sluiten, O, Esc of nog eens het icoon.

signal gesloten

const STEEN := Color8(74, 80, 101)
const STEEN_LICHT := Color8(128, 136, 160)
const STEEN_DONKER := Color8(36, 39, 52)
const GOUD := Color8(236, 190, 60)
const GOUD_DONKER := Color8(150, 105, 25)
const NAMEN := {"brood": "Brood", "melk": "Melk", "ei": "Eieren"}
const B := 500.0             ## breedte van het paneel

var w: Wereld
var balken := {}             ## waar -> Balk
var waarden := {}            ## waar -> Label
var geluk_balk: Balk
var geluk_label: Label
var misdaad_label: Label
var doel_label: Label        ## waar het geluk naartoe loopt bij de prijzen van nu (Handel.geluk_doel)
var _paneel: Control
var _pauzeerde := false


func bouw(wereld: Wereld) -> void:
	w = wereld
	mouse_filter = Control.MOUSE_FILTER_STOP     # klikken gaan niet door naar de wereld (Bestuur: _unhandled_input)
	visible = false
	_paneel = Control.new()
	_paneel.mouse_filter = Control.MOUSE_FILTER_PASS
	_paneel.draw.connect(_teken_paneel)
	add_child(_paneel)
	var kolom := VBoxContainer.new()
	kolom.position = Vector2(24, 18)
	kolom.custom_minimum_size = Vector2(B - 48, 0)
	kolom.add_theme_constant_override("separation", 10)
	_paneel.add_child(kolom)
	var kop := _label("Prijzen", 26)
	kop.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	kolom.add_child(kop)
	var uitleg := _label("hoge prijs = meer goud per verkoop, maar een ontevreden dorp", 14)
	uitleg.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	uitleg.modulate.a = 0.8
	kolom.add_child(uitleg)
	# munten-legenda boven de balken: weinig links, een stapel rechts (origineel)
	var legenda := Munten.new()
	legenda.custom_minimum_size = Vector2(B - 48, 26)
	kolom.add_child(legenda)
	for waar in Wereld.WAREN:
		var rij := HBoxContainer.new()
		rij.add_theme_constant_override("separation", 8)
		var naam := _label(NAMEN.get(waar, waar), 19)
		naam.custom_minimum_size = Vector2(84, 0)
		rij.add_child(naam)
		var min_k := _knop("-")
		min_k.pressed.connect(func() -> void: zet(waar, w.handel.prijs(waar) - 1))
		rij.add_child(min_k)
		var b := Balk.new()
		b.custom_minimum_size = Vector2(190, 40)
		b.size_flags_horizontal = Control.SIZE_EXPAND_FILL
		b.gekozen.connect(func(f: float) -> void:
			zet(waar, w.handel.prijs_min() + roundi(f * float(w.handel.prijs_max() - w.handel.prijs_min()))))
		rij.add_child(b)
		balken[waar] = b
		var plus_k := _knop("+")
		plus_k.pressed.connect(func() -> void: zet(waar, w.handel.prijs(waar) + 1))
		rij.add_child(plus_k)
		var v := _label("", 19)
		v.custom_minimum_size = Vector2(70, 0)
		v.horizontal_alignment = HORIZONTAL_ALIGNMENT_RIGHT
		rij.add_child(v)
		waarden[waar] = v
		kolom.add_child(rij)
	var rij_g := HBoxContainer.new()
	rij_g.add_theme_constant_override("separation", 8)
	var gk := _label("Geluk", 19)
	gk.custom_minimum_size = Vector2(84, 0)
	rij_g.add_child(gk)
	geluk_balk = Balk.new()
	geluk_balk.alleen_tonen = true
	geluk_balk.kleur = Color8(90, 200, 90)
	geluk_balk.custom_minimum_size = Vector2(190, 26)
	geluk_balk.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	rij_g.add_child(geluk_balk)
	geluk_label = _label("", 19)
	geluk_label.custom_minimum_size = Vector2(70, 0)
	geluk_label.horizontal_alignment = HORIZONTAL_ALIGNMENT_RIGHT
	rij_g.add_child(geluk_label)
	kolom.add_child(rij_g)
	doel_label = _label("", 14)
	doel_label.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	doel_label.modulate.a = 0.8
	kolom.add_child(doel_label)
	misdaad_label = _label("", 15)
	kolom.add_child(misdaad_label)
	var sluit_k := _knop("Sluiten (O / Esc)")
	sluit_k.pressed.connect(sluit)
	kolom.add_child(sluit_k)
	_paneel.size = Vector2(B, kolom.get_combined_minimum_size().y + 36.0)


func _label(t: String, px: int) -> Label:
	var l := Label.new()
	l.text = t
	l.add_theme_font_size_override("font_size", px)
	l.add_theme_color_override("font_color", Color8(240, 236, 224))
	l.add_theme_color_override("font_outline_color", STEEN_DONKER)
	l.add_theme_constant_override("outline_size", 4)
	l.vertical_alignment = VERTICAL_ALIGNMENT_CENTER
	l.mouse_filter = Control.MOUSE_FILTER_IGNORE
	return l


func _knop(t: String) -> Button:
	var k := Button.new()
	k.text = t
	k.custom_minimum_size = Vector2(44, 40)       # met een vinger te raken (bouwmenu KNOP_H)
	k.add_theme_font_size_override("font_size", 20)
	k.focus_mode = Control.FOCUS_NONE
	return k


func zet(waar: String, p: int) -> void:
	w.handel.zet_prijs(waar, p)
	_ververs()


func open() -> void:
	if visible:
		return
	if not w.gepauzeerd:
		w.gepauzeerd = true
		_pauzeerde = true
	var vp := get_viewport().get_visible_rect().size if is_inside_tree() else Vector2(1600, 900)
	position = Vector2.ZERO
	size = vp                                     # het hele scherm: dimt en vangt klikken
	_paneel.position = ((vp - _paneel.size) * 0.5).floor()
	visible = true
	_ververs()


func sluit() -> void:
	if not visible:
		return
	visible = false
	if _pauzeerde:
		w.gepauzeerd = false
		_pauzeerde = false
	gesloten.emit()


func wissel() -> void:
	if visible:
		sluit()
	else:
		open()


func _ververs() -> void:
	var span := float(maxi(1, w.handel.prijs_max() - w.handel.prijs_min()))
	for waar in balken:
		var p := w.handel.prijs(waar)
		(balken[waar] as Balk).zet(float(p - w.handel.prijs_min()) / span)
		(waarden[waar] as Label).text = "%d goud" % p
	var g := w.handel.dorp_geluk(w)
	geluk_balk.zet(g)
	geluk_label.text = "%d%%" % roundi(g * 100.0)
	var doel := w.handel.geluk_doel()
	var gaat := "blijft" if absf(doel - g) < 0.005 else ("stijgt" if doel > g else "daalt")
	doel_label.text = "bij deze prijzen %s het geluk langzaam naar %d%%" % [gaat, roundi(doel * 100.0)]
	if gaat == "blijft":
		doel_label.text = "bij deze prijzen blijft het geluk op %d%%" % roundi(doel * 100.0)
	misdaad_label.visible = w.handel.misdaad_aan(w)
	var m: Dictionary = w.handel.misdaden
	misdaad_label.text = "misdaden: %d  (vloeken %d, diefstal %d, mishandeling %d, moord %d)" % [
		w.handel.totaal_misdaden(), m["vloeken"], m["diefstal"], m["mishandeling"], m["moord"]]


func _process(_dt: float) -> void:
	if visible:
		_ververs()


## Toetsen terwijl het scherm open is: O en Esc sluiten, de rest gaat niet door (geen bouwtoetsen, geen Esc = stoppen).
func _input(e: InputEvent) -> void:
	if not visible or not e is InputEventKey or not e.pressed:
		return
	if e.keycode == KEY_O or e.keycode == KEY_ESCAPE:
		sluit()
	get_viewport().set_input_as_handled()


func _gui_input(e: InputEvent) -> void:
	# een klik naast het paneel sluit het (zoals de brief)
	if e is InputEventMouseButton and e.pressed and e.button_index == MOUSE_BUTTON_LEFT:
		if not Rect2(_paneel.position, _paneel.size).has_point(e.position):
			sluit()
		accept_event()


func _draw() -> void:
	draw_rect(Rect2(Vector2.ZERO, size), Color(0, 0, 0, 0.45))


func _teken_paneel() -> void:
	var r := Rect2(Vector2.ZERO, _paneel.size)
	_paneel.draw_rect(Rect2(r.position + Vector2(6, 8), r.size), Color(0, 0, 0, 0.45))
	_paneel.draw_rect(r, STEEN)
	# vlekken: grof marmer (deterministisch)
	for i in 140:
		var h := sin(float(i) * 12.9898) * 43758.5453
		var x := fposmod(h, 1.0) * r.size.x
		var y := fposmod(h * 1.7, 1.0) * r.size.y
		var c := STEEN_LICHT if i % 3 == 0 else STEEN_DONKER
		c.a = 0.18
		_paneel.draw_circle(Vector2(x, y), 4.0 + fposmod(h * 3.1, 1.0) * 14.0, c)
	# afgeschuinde rand: licht boven/links, donker onder/rechts
	_paneel.draw_rect(Rect2(0, 0, r.size.x, 4), STEEN_LICHT)
	_paneel.draw_rect(Rect2(0, 0, 4, r.size.y), STEEN_LICHT)
	_paneel.draw_rect(Rect2(0, r.size.y - 4, r.size.x, 4), STEEN_DONKER)
	_paneel.draw_rect(Rect2(r.size.x - 4, 0, 4, r.size.y), STEEN_DONKER)
	_paneel.draw_rect(r.grow(-8), STEEN_DONKER, false, 2.0)


## Schuif als ingelegde goot met een gouden vulling (0..1); klik of sleep zet de waarde, ook met een vinger.
class Balk extends Control:
	signal gekozen(f: float)
	var waarde := 0.0
	var alleen_tonen := false
	var kleur := GOUD
	var _vast := false

	func _init() -> void:
		mouse_filter = Control.MOUSE_FILTER_STOP
		mouse_default_cursor_shape = Control.CURSOR_POINTING_HAND

	func zet(f: float) -> void:
		if not is_equal_approx(f, waarde):
			waarde = clampf(f, 0.0, 1.0)
			queue_redraw()

	func _gui_input(e: InputEvent) -> void:
		if alleen_tonen:
			return
		if e is InputEventMouseButton and e.button_index == MOUSE_BUTTON_LEFT:
			_vast = e.pressed
			if e.pressed:
				gekozen.emit(_f(e.position.x))
			accept_event()
		elif e is InputEventMouseMotion and _vast:
			gekozen.emit(_f(e.position.x))
			accept_event()

	func _f(x: float) -> float:
		return clampf((x - 4.0) / maxf(1.0, size.x - 8.0), 0.0, 1.0)

	func _draw() -> void:
		var r := Rect2(Vector2.ZERO, size)
		draw_rect(r, STEEN_DONKER)
		draw_rect(Rect2(0, r.size.y - 2, r.size.x, 2), STEEN_LICHT)
		var vul := Rect2(4, 4, (r.size.x - 8) * waarde, r.size.y - 8)
		if vul.size.x > 0.5:
			draw_rect(vul, kleur.darkened(0.35))
			draw_rect(Rect2(vul.position, Vector2(vul.size.x, vul.size.y * 0.45)), kleur)
		if not alleen_tonen:
			var x := 4.0 + (r.size.x - 8) * waarde
			draw_rect(Rect2(x - 3, 1, 6, r.size.y - 2), Color8(240, 236, 224))


## Legenda boven de schuiven: links een paar munten, rechts een stapel (eigen tekening).
class Munten extends Control:
	func _init() -> void:
		mouse_filter = Control.MOUSE_FILTER_IGNORE

	func _draw() -> void:
		_munt(Vector2(150, 16), 6.0)
		_munt(Vector2(160, 12), 6.0)
		var x := size.x - 172.0          # rechts boven het eind van de balken
		for i in 4:
			_munt(Vector2(x + i * 9.0, 20), 7.0)
		for i in 3:
			_munt(Vector2(x + 4.5 + i * 9.0, 13), 7.0)
		_munt(Vector2(x + 13.5, 6), 7.0)

	func _munt(p: Vector2, r: float) -> void:
		draw_circle(p + Vector2(0, 1.5), r, GOUD_DONKER)
		draw_circle(p, r, GOUD)
		draw_circle(p, r * 0.5, GOUD.lightened(0.3))
