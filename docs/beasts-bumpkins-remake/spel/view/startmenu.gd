class_name Startmenu
extends CanvasLayer
## Startmenu (2026-10-31, gebruiker: "ik wil in het spel een missie kunnen kiezen"): bij het opstarten zonder `--missie` of
## `--scenario` toont main.gd dit in plaats van een wereld. Een perkament (view/perkament.gd) met alle 30 missies van de
## campagne (data/campagne.json): nummer, titel (de briefingtitel uit hints.json als de missie er een heeft), dorp en doel.
## Speelbaar = staat in spel.json `missies` en de kaart is er; de rest staat vaal onder "Nog niet gebouwd".
## Bovenaan **Doorgaan** (de laatst gestarte missie) en op de pc **Afsluiten**.
## Kiezen = `Startmenu.volgende` zetten en de hoofdscène opnieuw laden: main.gd begint dan met die missie, zodat er van
## de vorige wereld niets overblijft (zie ook view/pauzemenu.gd: opnieuw, andere missie, volgende missie).
## Origineel: een lineaire campagne (na een gewonnen missie de briefing van de volgende), zonder vrije keuze; wij laten elke
## speelbare missie kiezen en onthouden de voortgang (gewonnen, laatst gespeeld) in user://voortgang.cfg.

signal gekozen(nr: int)

## Na het herladen van de hoofdscène: met deze missie beginnen (0 = niet gekozen). main.gd leest en wist het.
static var volgende := 0
## Na het herladen: het startmenu tonen, ook als de opdrachtregel een missie noemt.
static var naar_menu := false
## Voortgang (gewonnen missies, laatst gestarte); "" = niet lezen of schrijven (tests en scenario's).
static var voortgang_pad := "" if Scherm.optie("scenario") != "" else "user://voortgang.cfg"
const CAMPAGNE := "res://data/campagne.json"

var paneel: Perkament
var lijst: VBoxContainer
var scroll: ScrollContainer
var knop_door: Button
var knop_uit: Button
var rijen := {}                 ## nr -> Button
var _achter: Control


func _ready() -> void:
	layer = 90
	Scherm.zet_venster(get_tree().root)
	Scherm.zet_opname(self)
	_achter = Achtergrond.new()
	_achter.set_anchors_preset(Control.PRESET_FULL_RECT)
	add_child(_achter)
	paneel = Perkament.new()
	add_child(paneel)
	var kolom := VBoxContainer.new()
	kolom.add_theme_constant_override("separation", 10)
	paneel.add_child(kolom)
	var kop := Perkament.label("Beasts & Bumpkins", 34, Color8(255, 214, 102))
	kop.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	kolom.add_child(kop)
	var sub := Perkament.label("Kies een missie", 22)
	sub.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	kolom.add_child(sub)
	var laatste := laatste_missie()
	knop_door = Perkament.knop("", 20)
	knop_door.visible = laatste > 0 and speelbaar(laatste)
	if knop_door.visible:
		knop_door.text = "Doorgaan: %d  %s" % [laatste, titel(laatste)]
		knop_door.text_overrun_behavior = TextServer.OVERRUN_TRIM_ELLIPSIS
		knop_door.pressed.connect(kies.bind(laatste))
	kolom.add_child(knop_door)
	scroll = ScrollContainer.new()
	scroll.horizontal_scroll_mode = ScrollContainer.SCROLL_MODE_DISABLED
	scroll.size_flags_vertical = Control.SIZE_EXPAND_FILL
	kolom.add_child(scroll)
	lijst = VBoxContainer.new()
	lijst.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	lijst.add_theme_constant_override("separation", 6)
	scroll.add_child(lijst)
	var kopje_gezet := false
	for m: Dictionary in campagne():
		var nr := int(m["nr"])
		if not speelbaar(nr) and not kopje_gezet:
			kopje_gezet = true
			var k := Perkament.label("Nog niet gebouwd", 19, Color(Brief.INKT, 0.7))
			k.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
			lijst.add_child(k)
		var r := _rij(nr, m)
		rijen[nr] = r
		lijst.add_child(r)
	knop_uit = Perkament.knop("Afsluiten", 20)
	knop_uit.visible = not OS.has_feature("mobile")       # Android: de terugknop of het overzicht sluit de app
	knop_uit.pressed.connect(func() -> void: get_tree().quit())
	kolom.add_child(knop_uit)
	get_viewport().size_changed.connect(leg_neer)
	leg_neer()


## Een regel: "3  De gouden kelk van Barathkar" en daaronder dorp, doel en "gewonnen"; vaal en uit als niet speelbaar.
func _rij(nr: int, m: Dictionary) -> Button:
	var b := Button.new()
	b.focus_mode = Control.FOCUS_NONE
	Perkament.stijl(b)
	b.mouse_default_cursor_shape = Control.CURSOR_POINTING_HAND
	var ok := speelbaar(nr)
	b.disabled = not ok
	var marge := MarginContainer.new()
	marge.set_anchors_preset(Control.PRESET_FULL_RECT)
	marge.mouse_filter = Control.MOUSE_FILTER_IGNORE
	for z in ["left", "right"]:
		marge.add_theme_constant_override("margin_" + z, 14)
	for z in ["top", "bottom"]:
		marge.add_theme_constant_override("margin_" + z, 5)
	b.add_child(marge)
	var regels := VBoxContainer.new()
	regels.mouse_filter = Control.MOUSE_FILTER_IGNORE
	regels.add_theme_constant_override("separation", 0)
	regels.alignment = BoxContainer.ALIGNMENT_CENTER
	marge.add_child(regels)
	var groot := 20
	var klein := 19 if Bouwmenu.touch else 16
	var t := Perkament.label("%d   %s" % [nr, titel(nr)], groot)
	t.text_overrun_behavior = TextServer.OVERRUN_TRIM_ELLIPSIS
	t.clip_text = true
	regels.add_child(t)
	var delen: Array[String] = []
	var dorp := String(m.get("dorp", ""))
	delen.append(dorp if dorp != "" else "geen eigen dorp")
	if ok:
		var d := doel_tekst(nr)
		if d != "":
			delen.append(d)
		if gewonnen(nr):
			delen.append("gewonnen")
	else:
		delen.append("nog niet speelbaar")
	var s := Perkament.label("      " + "  ·  ".join(delen), klein, Color(1.0, 0.85, 0.4) if ok and gewonnen(nr) else Color(Brief.INKT, 0.8))
	s.text_overrun_behavior = TextServer.OVERRUN_TRIM_ELLIPSIS
	s.clip_text = true
	regels.add_child(s)
	var h := maxf(Perkament.knop_h(), groot * 1.45 + klein * 1.45 + 12.0)
	b.custom_minimum_size = Vector2(0, h)
	if not ok:
		b.modulate.a = 0.55
		b.mouse_default_cursor_shape = Control.CURSOR_ARROW
	else:
		b.pressed.connect(kies.bind(nr))
	return b


## Legt het perkament neer: zo breed als past (hoogstens 720 basis-px), zo hoog als het scherm; de lijst scrollt.
func leg_neer() -> void:
	var vp := get_viewport().get_visible_rect().size
	var s := Perkament.schaal()
	var b := minf(720.0, (vp.x - 24.0) / s)
	var h := (vp.y - 24.0) / s
	paneel.custom_minimum_size = Vector2(b, h)
	paneel.size = Vector2(b, h)
	paneel.scale = Vector2(s, s)
	paneel.position = ((vp - paneel.size * s) * 0.5).floor()


func kies(nr: int) -> void:
	if not speelbaar(nr):
		return
	gekozen.emit(nr)
	start(nr, get_tree())


## Begint missie `nr` door de hoofdscène opnieuw te laden (main.gd leest `volgende`).
static func start(nr: int, tree: SceneTree) -> void:
	volgende = nr
	naar_menu = false
	tree.reload_current_scene()


## Terug naar het startmenu (pauzemenu "Andere missie").
static func terug_naar_menu(tree: SceneTree) -> void:
	volgende = 0
	naar_menu = true
	tree.reload_current_scene()


func _unhandled_input(e: InputEvent) -> void:
	if not (e is InputEventKey and e.pressed and not e.echo):
		return
	var k := (e as InputEventKey).keycode
	if k in [KEY_ENTER, KEY_KP_ENTER] and knop_door.visible:
		get_viewport().set_input_as_handled()
		knop_door.pressed.emit()
	elif k == KEY_ESCAPE and knop_uit.visible:
		get_viewport().set_input_as_handled()
		get_tree().quit()


# ---------------------------------------------------------------- campagne en voortgang (statisch, ook voor main.gd)

static var _campagne: Array = []


static func campagne() -> Array:
	if _campagne.is_empty():
		var d: Variant = Gegevens.lees(CAMPAGNE)
		if d is Dictionary and (d as Dictionary).get("missies") is Array:
			_campagne = d["missies"]
		else:
			for i in 30:
				_campagne.append({"nr": i + 1, "titel": "Missie %d" % (i + 1), "dorp": ""})
	return _campagne


static func _missies() -> Dictionary:
	var spel: Variant = Gegevens.lees(Gegevens.SPEL)
	return spel.get("missies", {}) if spel is Dictionary else {}


## Speelbaar: staat in spel.json `missies` en de kaart is er (data/origineel/ komt van sync.ps1).
static func speelbaar(nr: int) -> bool:
	var m: Variant = _missies().get(str(nr))
	if not m is Dictionary:
		return false
	var kaart := String((m as Dictionary).get("kaart", ""))
	return kaart == "" or FileAccess.file_exists(kaart)


## Titel: de briefingtitel (hints.json) als die er is, anders het label uit campagne.json.
static func titel(nr: int) -> String:
	var h: Variant = Gegevens.lees("res://data/hints.json")
	if h is Dictionary:
		var b: Variant = (h as Dictionary).get("missies", {}).get(str(nr), {}).get("briefing", {})
		if b is Dictionary and String((b as Dictionary).get("titel", "")) != "":
			return String(b["titel"])
	for m: Dictionary in campagne():
		if int(m["nr"]) == nr:
			return String(m.get("titel", ""))
	return "Missie %d" % nr


## Het missiedoel in een paar woorden, uit spel.json `doel`.
static func doel_tekst(nr: int) -> String:
	var m: Variant = _missies().get(str(nr))
	if not m is Dictionary:
		return ""
	var d: Dictionary = (m as Dictionary).get("doel", {})
	var uit: Array[String] = []
	if d.has("dorpelingen"):
		uit.append("%d dorpelingen" % int(d["dorpelingen"]))
	if d.has("koeien"):
		uit.append("%d koeien" % int(d["koeien"]))
	if d.has("kas_boven"):
		uit.append("kas boven %s" % _duizend(int(d["kas_boven"]) + (1 if int(d["kas_boven"]) % 1000 == 999 else 0)))
	return ", ".join(uit)


static func _duizend(n: int) -> String:
	var s := str(n)
	var uit := ""
	while s.length() > 3:
		uit = "." + s.substr(s.length() - 3) + uit
		s = s.substr(0, s.length() - 3)
	return s + uit


static func _lees() -> ConfigFile:
	var cf := ConfigFile.new()
	if voortgang_pad != "":
		cf.load(voortgang_pad)          # ontbreekt of onleesbaar: leeg
	return cf


static func _bewaar(cf: ConfigFile) -> void:
	if voortgang_pad == "":
		return
	var fout := cf.save(voortgang_pad)
	if fout != OK:
		push_warning("startmenu: %s niet bewaard (%s)" % [voortgang_pad, error_string(fout)])


static func laatste_missie() -> int:
	var v: Variant = _lees().get_value("voortgang", "laatste", 0)
	return int(v) if (v is int or v is float) else 0


static func gewonnen(nr: int) -> bool:
	var v: Variant = _lees().get_value("voortgang", "gewonnen", [])
	return v is Array and (v as Array).has(nr)


static func bewaar_laatste(nr: int) -> void:
	var cf := _lees()
	cf.set_value("voortgang", "laatste", nr)
	_bewaar(cf)


static func bewaar_gewonnen(nr: int) -> void:
	var cf := _lees()
	var v: Variant = cf.get_value("voortgang", "gewonnen", [])
	var lijst: Array = v if v is Array else []
	if not lijst.has(nr):
		lijst.append(nr)
		lijst.sort()
	cf.set_value("voortgang", "gewonnen", lijst)
	_bewaar(cf)


## Donkere achtergrond achter het perkament: van boven naar onder iets lichter, met een vignet.
class Achtergrond extends Control:
	func _init() -> void:
		mouse_filter = Control.MOUSE_FILTER_STOP

	func _draw() -> void:
		var n := 24
		for i in n:
			var f := float(i) / (n - 1)
			draw_rect(Rect2(0, size.y * i / n, size.x, size.y / n + 1.0), Color(0.06, 0.045, 0.03).lerp(Color(0.16, 0.10, 0.05), f))
		var c := size * 0.5
		var r := size.length() * 0.5
		for i in 6:
			draw_arc(c, r - i * r * 0.04, 0.0, TAU, 64, Color(0, 0, 0, 0.12), r * 0.05)

	func _notification(what: int) -> void:
		if what == NOTIFICATION_RESIZED:
			queue_redraw()
