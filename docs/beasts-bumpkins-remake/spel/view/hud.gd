class_name Hud
extends CanvasLayer
## Minimale HUD: linksboven de minikaart (view/minikaart.gd, zoals het origineel), daaronder tijd, seizoen, weer,
## selectie, tempo. Linksonder de besturing.
## Touch (2026-10-30, gebruiker: de tekstregels zijn op de telefoon te klein om te lezen): geen tekstregels en geen
## sneltoetsuitleg, alleen een rij icoon + getal (kas, dorpelingen en koeien met het missiedoel) op >= 16 dp; minikaart,
## munt-icoon en rolletjes groter. Staand (view/scherm.gd) op de pc: de stand in korte regels. Brief en prijzenscherm
## leggen zich opnieuw neer bij size_changed (`_indeling`).
## Pc (2026-10-31, gebruiker: te veel tekst): dezelfde rij icoon + getal, met pauze-icoon / 2x / 4x erachter; de tekstregels
## klappen uit met het pijltje of Tab / I, de sneltoetsuitleg met "? Toetsen" of F1. Beide standaard dicht, per speler
## bewaard in user://hud.cfg.
## Stilstaan (besluit gebruiker 2026-10-31, "alleen stilstaan knop", origineel de hand): naast de menuknop een hand-knop,
## alleen zichtbaar met een selectie, of X: de gekozen dorpelingen blijven staan zonder eigen klussen (Wereld.geef_stilstaan).
## Melding (midden boven, 2,5 s): een geweigerd bevel (Wereld.bevel_geweigerd, bv. een vrouw laten bouwen).

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
var menu_knop: Button            ## naast het munt-icoon: pauzemenu (view/pauzemenu.gd, main.gd); touch >= 48 dp
signal menu_gevraagd
var stil_knop: Button            ## hand: stilstaan voor de selectie (X); touch >= 48 dp, alleen met een selectie
var melding: Label               ## geweigerd bevel, verdwijnt na MELDING_S
var _melding_t := 0.0
const MELDING_S := 2.5
var kas_toon := -1               ## getoonde kas: loopt in stappen naar w.kas (kas_stap, spel.json kas_teller)
var _kas_t := 0.0
var stand: PanelContainer        ## de tekstregels (pc)
var tellers: Tellers             ## touch: icoon + getal
var schaal := 1.0                ## touch: minikaart, munt-icoon en rolletjes (1 op de pc)
var kop: HBoxContainer           ## pc: tellers + pijltje naar de details
var knop_details: Button         ## pc: pijltje (Tab / I) klapt de tekstregels (stand) uit en in
var knop_hulp: Button            ## pc: "? Toetsen (F1)" klapt de sneltoetsuitleg uit en in
var details_open := false        ## pc: tekstregels zichtbaar (standaard ingeklapt, gebruiker 2026-10-31)
var hulp_open := false           ## pc: sneltoetsuitleg zichtbaar
## Ingeklapt/uitgeklapt per speler; "" = niet lezen of schrijven (tests). Scenario's lezen en schrijven niet (frames
## blijven gelijk), `--hud=details|hulp|beide` klapt voor frames uit.
static var cfg_pad := "" if Scherm.optie("scenario") != "" else "user://hud.cfg"
var _was_staand := false


func bouw(wereld: Wereld, b: Bestuur) -> void:
	w = wereld
	bestuur = b
	if is_inside_tree():
		Scherm.zet_venster(get_tree().root)
		Scherm.zet_opname(self)
	if Bouwmenu.touch:
		schaal = clampf(Scherm.dp() * 0.6, 1.0, 1.6)
	minikaart = Minikaart.new()
	add_child(minikaart)
	minikaart.bouw(w, b.cam, b.view.terrein if b.view != null else null)
	minikaart.scale = Vector2(schaal, schaal)
	var pc := PanelContainer.new()
	stand = pc
	pc.position = Vector2(12, minikaart.position.y + minikaart.size.y * schaal + 8)
	pc.mouse_filter = Control.MOUSE_FILTER_IGNORE
	pc.add_theme_stylebox_override("panel", _stijl())
	label = Label.new()
	label.add_theme_font_size_override("font_size", 18)
	label.mouse_filter = Control.MOUSE_FILTER_IGNORE
	pc.add_child(label)
	add_child(pc)
	tellers = Tellers.new()
	tellers.bouw(w, Scherm.dp(), not Bouwmenu.touch)
	if Bouwmenu.touch:
		pc.visible = false
		tellers.position = pc.position
		add_child(tellers)
	else:
		# pc (2026-10-31, gebruiker: te veel tekst): dezelfde rij als touch, met pijltje (Tab / I) naar de details
		kop = HBoxContainer.new()
		kop.position = pc.position
		kop.mouse_filter = Control.MOUSE_FILTER_IGNORE
		kop.add_theme_constant_override("separation", 6)
		kop.add_child(tellers)
		knop_details = Pijl.new()
		knop_details.tooltip_text = "details (Tab)"
		knop_details.pressed.connect(wissel_details)
		kop.add_child(knop_details)
		add_child(kop)

	var pc2 := PanelContainer.new()
	pc2.mouse_filter = Control.MOUSE_FILTER_IGNORE
	pc2.add_theme_stylebox_override("panel", _stijl())
	hulp = Label.new()
	hulp.add_theme_font_size_override("font_size", 13)
	hulp.mouse_filter = Control.MOUSE_FILTER_IGNORE
	hulp.text = "links: kader/klik = kiezen, klik grond = lopen, klik koe = claimen, klik loods = bouwer (75)   rechts klik = selectie weg   rechts slepen / Q E = draaien\nbouwen: knop rechtsboven, indrukken-slepen-loslaten = plaatsen (weg/hek: slepen = rij), blijft aan; Draai / wiel / R, Stop / rechts / Esc\nWASD/rand = pannen   wiel = zoom   Spatie pauze   O / munten = prijzen   1 2 4 tempo   K regen   N seizoen   Esc menu\nX / hand = stilstaan (selectie)   M = muziek aan/uit   Tab / I = details   F1 = deze uitleg"
	pc2.add_child(hulp)
	add_child(pc2)
	knop_hulp = Button.new()
	knop_hulp.text = "? Toetsen (F1)"
	knop_hulp.focus_mode = Control.FOCUS_NONE
	knop_hulp.add_theme_font_size_override("font_size", 13)
	for st in ["normal", "hover", "pressed"]:
		var sb := _stijl()
		sb.set_content_margin_all(5)
		sb.content_margin_left = 8
		sb.content_margin_right = 8
		if st != "normal":
			sb.bg_color = Color(0.15, 0.15, 0.15, 0.7)
		knop_hulp.add_theme_stylebox_override(st, sb)
	knop_hulp.mouse_default_cursor_shape = Control.CURSOR_POINTING_HAND
	knop_hulp.pressed.connect(wissel_hulp)
	add_child(knop_hulp)
	if Bouwmenu.touch:      # sneltoetsen en muisknoppen: zonder toetsenbord zinloos
		pc2.visible = false
		knop_hulp.visible = false
	else:
		_lees_cfg()
		match Scherm.optie("hud"):      # alleen voor frames: --hud=details|hulp|beide
			"details": details_open = true
			"hulp": hulp_open = true
			"beide":
				details_open = true
				hulp_open = true
		_pas_inklap_toe()

	uitslag = Label.new()
	uitslag.add_theme_font_size_override("font_size", int(44 * maxf(1.0, Scherm.dp() * 0.8)))
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
	munt_knop.position = Vector2(minikaart.position.x + minikaart.size.x * schaal + 10, minikaart.position.y)
	munt_knop.scale = Vector2(schaal, schaal)
	munt_knop.tooltip_text = "prijzen (O)"
	add_child(munt_knop)
	prijzen = Prijzenscherm.new()
	add_child(prijzen)
	prijzen.bouw(w)
	munt_knop.pressed.connect(prijzen.wissel)
	# menuknop (2026-10-31): pauzemenu met opnieuw / andere missie; op touch een volle knophoogte (>= 48 dp)
	menu_knop = MenuKnop.new()
	var mk := Bouwmenu.touch_knop_h() if Bouwmenu.touch else 52.0
	menu_knop.custom_minimum_size = Vector2(mk, mk)
	menu_knop.size = menu_knop.custom_minimum_size
	menu_knop.position = Vector2(munt_knop.position.x + munt_knop.size.x * schaal + 10, minikaart.position.y)
	menu_knop.tooltip_text = "menu (Esc)"
	menu_knop.pressed.connect(func() -> void: menu_gevraagd.emit())
	add_child(menu_knop)
	stil_knop = StilKnop.new()
	stil_knop.custom_minimum_size = Vector2(mk, mk)
	stil_knop.size = stil_knop.custom_minimum_size
	stil_knop.position = Vector2(menu_knop.position.x + mk + 10, minikaart.position.y)
	stil_knop.tooltip_text = "stilstaan (X)"
	stil_knop.visible = false
	stil_knop.pressed.connect(stilstaan)
	add_child(stil_knop)
	melding = Label.new()
	melding.add_theme_font_size_override("font_size", int(22 * maxf(1.0, Scherm.dp() * 0.6)))
	melding.add_theme_color_override("font_outline_color", Color.BLACK)
	melding.add_theme_constant_override("outline_size", 6)
	melding.set_anchors_preset(Control.PRESET_CENTER_TOP)
	melding.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	melding.grow_horizontal = Control.GROW_DIRECTION_BOTH
	melding.position.y = 150
	melding.mouse_filter = Control.MOUSE_FILTER_IGNORE
	melding.visible = false
	add_child(melding)
	w.bevel_geweigerd.connect(_geweigerd)
	if is_inside_tree():
		get_viewport().size_changed.connect(_indeling)
	if Scherm.optie("proef") == "prijzen":     # alleen voor frames (view/scherm.gd)
		prijzen.open.call_deferred()


## Na een draai van het scherm (size_changed): open brief en prijzenscherm opnieuw neerleggen (de rest hangt aan
## ankers of staat linksboven; de korte regels kiest _process).
func _indeling() -> void:
	if brief != null and brief.visible:
		brief.herschik()
	if prijzen.visible:
		prijzen.leg_neer()


func _stijl() -> StyleBoxFlat:
	var sb := StyleBoxFlat.new()
	sb.bg_color = Color(0, 0, 0, 0.5)
	sb.set_content_margin_all(8)
	sb.set_corner_radius_all(4)
	return sb


## Een stap van de getoonde kas naar de echte (BEASTS.EXE 0x40cea2): de grootste stap uit `stappen`
## ([[drempel, stap], ...], aflopend) waarvoor het verschil groter is dan de drempel; nooit voorbij het doel.
static func kas_stap(toon: int, kas: int, stappen: Array) -> int:
	var v := absi(kas - toon)
	if v == 0:
		return toon
	for st in stappen:
		if v > int(st[0]):
			return toon + signi(kas - toon) * mini(int(st[1]), v)
	return kas


func _kas_teller(dt: float) -> void:
	var c: Dictionary = w.spel.get("kas_teller", {})
	if kas_toon < 0 or c.is_empty():
		kas_toon = w.kas
		return
	_kas_t += dt
	var tik := 1.0 / maxf(1.0, float(c.get("hz", 25)))
	while _kas_t >= tik and kas_toon != w.kas:
		_kas_t -= tik
		kas_toon = kas_stap(kas_toon, w.kas, c["stappen"])
	if kas_toon == w.kas:
		_kas_t = 0.0


func _process(dt: float) -> void:
	_kas_teller(dt)
	if stil_knop != null and bestuur != null:
		stil_knop.visible = not bestuur.gekozen.is_empty()
	if _melding_t > 0.0:
		_melding_t -= dt
		if _melding_t <= 0.0:
			melding.visible = false
	var uur := w.uur()
	var h := int(uur)
	var m := int(fposmod(uur, 1.0) * 60.0)
	var tempo := "PAUZE" if w.gepauzeerd else "%dx" % int(w.tempo)
	var weer := "regen" if w.regent() else "droog"
	var doel: Dictionary = w.missie.get("doel", {})
	# achter het getal het missiedoel, alleen als de missie dat doel heeft (missie 1: dorpelingen en koeien, 2: kas)
	var kas := "%d" % kas_toon + (" / >%d" % int(doel["kas_boven"]) if doel.has("kas_boven") else "")
	var dorp := "%d" % w.dorpelingen.size() + ("/%d" % int(doel["dorpelingen"]) if doel.has("dorpelingen") else "")
	var koe := "%d" % w.eigen_koeien() + ("/%d" % int(doel["koeien"]) if doel.has("koeien") else "")
	var geluk := "geluk: %d%%" % roundi(w.handel.dorp_geluk(w) * 100.0)   # sim/handel.gd, prijzen via het munt-icoon
	if w.handel.misdaad_aan(w):
		geluk += "   misdaden: %d" % w.handel.totaal_misdaden()
	tellers.zet(kas_toon)
	if Bouwmenu.touch:
		return
	tellers.zet_tempo(w.gepauzeerd, int(w.tempo))
	var staand: bool = is_inside_tree() and Scherm.staand(get_viewport().get_visible_rect().size)
	if details_open:
		var regels := ["%02d:%02d%s  dag %d  %s  %s" % [h, m, " (nacht)" if w.is_nacht() else "", w.dag_nr() + 1, w.seizoen_naam(), weer],
			"kas: %s   dorpelingen: %s   koeien: %s" % [kas, dorp, koe],
			"bedden: %d   brood: %d   melk: %d   eieren: %d" % [w.bedden(), w.brood(), w.melk(), w.eieren()],
			geluk, "geselecteerd: %d   tempo: %s" % [bestuur.gekozen.size(), tempo]]
		if staand:      # smal: korte regels
			label.text = "\n".join(regels)
		else:
			label.text = "%s\n%s   %s\n%s   %s" % regels
	if staand != _was_staand:      # van lange naar korte regels of terug: het paneel krimpt mee
		_was_staand = staand
		stand.reset_size()
	_leg_links_neer(staand)


## Pc: de rij (kop) onder de minikaart, de details eronder; de sneltoetsknop linksonder met de uitleg erboven, of
## staand (onderin zit het bouwmenu) onder de details.
func _leg_links_neer(staand: bool) -> void:
	stand.position = Vector2(12, kop.position.y + kop.size.y + 6)
	var pc2 := hulp.get_parent() as Control
	var vp := get_viewport().get_visible_rect().size if is_inside_tree() else Vector2(1600, 900)
	if staand:
		var y := (stand.position.y + stand.size.y if stand.visible else kop.position.y + kop.size.y) + 8
		knop_hulp.position = Vector2(12, y)
		pc2.position = Vector2(12, y + knop_hulp.size.y + 6)
	else:
		knop_hulp.position = Vector2(12, vp.y - knop_hulp.size.y - 12)
		pc2.position = Vector2(12, knop_hulp.position.y - pc2.size.y - 6)


## Pc: details (Tab / I, of het pijltje) uit- of inklappen.
func wissel_details() -> void:
	details_open = not details_open
	_pas_inklap_toe()
	_bewaar_cfg()


## Pc: sneltoetsuitleg (F1, of de knop) uit- of inklappen.
func wissel_hulp() -> void:
	hulp_open = not hulp_open
	_pas_inklap_toe()
	_bewaar_cfg()


func _pas_inklap_toe() -> void:
	if Bouwmenu.touch:
		return
	stand.visible = details_open
	(knop_details as Pijl).open = details_open
	knop_details.queue_redraw()
	knop_details.tooltip_text = ("details dicht" if details_open else "details") + " (Tab)"
	(hulp.get_parent() as Control).visible = hulp_open
	knop_hulp.text = ("x Toetsen (F1)" if hulp_open else "? Toetsen (F1)")
	knop_hulp.reset_size()
	stand.reset_size()
	if details_open:      # tekst meteen, niet pas na het volgende frame (anders een frame een leeg paneel)
		_process(0.0)


func _lees_cfg() -> void:
	if cfg_pad == "":
		return
	var cf := ConfigFile.new()
	if cf.load(cfg_pad) != OK:      # nog niet bewaard of onleesbaar: standaard (ingeklapt)
		return
	var d: Variant = cf.get_value("hud", "details", false)
	var u: Variant = cf.get_value("hud", "hulp", false)
	details_open = d if d is bool else false
	hulp_open = u if u is bool else false


func _bewaar_cfg() -> void:
	if cfg_pad == "":
		return
	var cf := ConfigFile.new()
	cf.set_value("hud", "details", details_open)
	cf.set_value("hud", "hulp", hulp_open)
	var fout := cf.save(cfg_pad)
	if fout != OK:
		push_warning("hud: %s niet bewaard (%s)" % [cfg_pad, error_string(fout)])


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
	r.k = schaal
	r.custom_minimum_size *= schaal
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


## Stilstaan voor de selectie (hand-knop of X).
func stilstaan() -> int:
	if bestuur == null or bestuur.gekozen.is_empty():
		return 0
	return w.geef_stilstaan(bestuur.gekozen)


func _geweigerd(_ids: Array, reden: String) -> void:
	toon_melding(reden)


func toon_melding(tekst: String) -> void:
	melding.text = tekst
	melding.visible = true
	_melding_t = MELDING_S


func _brief_dicht() -> void:
	if _pauzeerde:
		w.gepauzeerd = false
		_pauzeerde = false
	_volgende_brief()


func _unhandled_input(e: InputEvent) -> void:
	if not (e is InputEventKey and e.pressed and not e.echo):
		return
	var k := (e as InputEventKey).keycode
	if k == KEY_O and prijzen != null:
		prijzen.wissel()
		get_viewport().set_input_as_handled()
	elif (k == KEY_TAB or k == KEY_I) and kop != null:
		wissel_details()
		get_viewport().set_input_as_handled()
	elif k == KEY_X and bestuur != null and not bestuur.gekozen.is_empty():
		stilstaan()
		get_viewport().set_input_as_handled()
	elif k == KEY_F1 and kop != null:
		wissel_hulp()
		get_viewport().set_input_as_handled()


## Pc: pijltje naast de tellers; omlaag = details uitklappen, omhoog = inklappen.
class Pijl extends Button:
	var open := false

	func _init() -> void:
		flat = true
		focus_mode = Control.FOCUS_NONE
		custom_minimum_size = Vector2(32, 32)
		size_flags_vertical = Control.SIZE_SHRINK_CENTER
		mouse_default_cursor_shape = Control.CURSOR_POINTING_HAND

	func _draw() -> void:
		var r := Rect2(Vector2.ZERO, size)
		var sb := StyleBoxFlat.new()
		sb.bg_color = Color(0, 0, 0, 0.65 if is_hovered() else 0.5)
		sb.set_corner_radius_all(4)
		draw_style_box(sb, r)
		var c := r.get_center()
		var s := minf(size.x, size.y) * 0.22
		var d := -1.0 if open else 1.0
		var punten := PackedVector2Array([c + Vector2(-s * 1.3, -s * 0.55 * d), c + Vector2(0, s * 0.65 * d), c + Vector2(s * 1.3, -s * 0.55 * d)])
		draw_polyline(punten, Color(0, 0, 0, 0.8), 5.0, true)
		draw_polyline(punten, Color.WHITE, 2.5, true)


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


## Menuknop: dezelfde steenknop als het munt-icoon, met drie perkamentkleurige strepen.
class MenuKnop extends Button:
	func _init() -> void:
		flat = true
		focus_mode = Control.FOCUS_NONE
		mouse_default_cursor_shape = Control.CURSOR_POINTING_HAND

	func _draw() -> void:
		var r := Rect2(Vector2.ZERO, size)
		var k := size.y / 52.0
		draw_rect(r, Color8(74, 80, 101))
		draw_rect(Rect2(0, 0, r.size.x, 3 * k), Color8(128, 136, 160))
		draw_rect(Rect2(0, 0, 3 * k, r.size.y), Color8(128, 136, 160))
		draw_rect(Rect2(0, r.size.y - 3 * k, r.size.x, 3 * k), Color8(36, 39, 52))
		draw_rect(Rect2(r.size.x - 3 * k, 0, 3 * k, r.size.y), Color8(36, 39, 52))
		if is_hovered():
			draw_rect(r.grow(-3 * k), Color(1, 1, 1, 0.08))
		for i in 3:
			var y := (16.0 + i * 10.0) * k
			draw_rect(Rect2(Vector2(13 * k, y + 1.5 * k), Vector2(26, 5) * k), Color(0, 0, 0, 0.5))
			draw_rect(Rect2(Vector2(13 * k, y), Vector2(26, 5) * k), Brief.INKT)


## Hand (stilstaan, naar de hand-knop van het origineel): steenknop met een open hand.
class StilKnop extends Button:
	func _init() -> void:
		flat = true
		focus_mode = Control.FOCUS_NONE
		mouse_default_cursor_shape = Control.CURSOR_POINTING_HAND

	func _draw() -> void:
		var r := Rect2(Vector2.ZERO, size)
		var k := size.y / 52.0
		draw_rect(r, Color8(74, 80, 101))
		draw_rect(Rect2(0, 0, r.size.x, 3 * k), Color8(128, 136, 160))
		draw_rect(Rect2(0, 0, 3 * k, r.size.y), Color8(128, 136, 160))
		draw_rect(Rect2(0, r.size.y - 3 * k, r.size.x, 3 * k), Color8(36, 39, 52))
		draw_rect(Rect2(r.size.x - 3 * k, 0, 3 * k, r.size.y), Color8(36, 39, 52))
		if is_hovered():
			draw_rect(r.grow(-3 * k), Color(1, 1, 1, 0.08))
		var huid := Color8(236, 200, 160)
		var rand := Color(0, 0, 0, 0.55)
		var delen := [Rect2(17, 24, 19, 16), Rect2(17, 12, 4, 14), Rect2(22, 9, 4, 16), Rect2(27, 10, 4, 15),
			Rect2(32, 13, 4, 13)]
		var duim := PackedVector2Array([Vector2(36, 30) * k, Vector2(42, 22) * k, Vector2(44, 25) * k, Vector2(37, 37) * k])
		for d: Rect2 in delen:
			draw_rect(Rect2(d.position * k, d.size * k).grow(1.5 * k), rand)
		draw_colored_polygon(duim, rand)
		for d: Rect2 in delen:
			draw_rect(Rect2(d.position * k, d.size * k), huid)
		draw_colored_polygon(PackedVector2Array([Vector2(36, 31) * k, Vector2(42, 23.5) * k, Vector2(43, 25) * k,
			Vector2(36.5, 35) * k]), huid)


## Rolletje: opgerolde brief met rode zegel (naar MAIL uit het origineel), knippert zachtjes tot je erop klikt.
class Rol extends Button:
	var k := 1.0                 ## touch: groter (Hud.schaal)

	func _init() -> void:
		flat = true
		focus_mode = Control.FOCUS_NONE
		custom_minimum_size = Vector2(64, 40)
		mouse_default_cursor_shape = Control.CURSOR_POINTING_HAND

	func _process(_dt: float) -> void:
		modulate.a = 0.75 + 0.25 * sin(Time.get_ticks_msec() * 0.006)

	func _draw() -> void:
		draw_set_transform(Vector2.ZERO, 0.0, Vector2(k, k))
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


## Touch: icoon + getal op >= 16 dp, zonder woorden: kas (munten), dorpelingen en eigen koeien, met het missiedoel
## erachter als de missie dat doel heeft (missie 1: 6 dorpelingen en 4 koeien, missie 2: kas > 10.000).
class Tellers extends PanelContainer:
	var w: Wereld
	var kas: Label
	var dorp: Label
	var koe: Label
	var tempo_ik: Ikoon          ## pc: pauze-icoon als de sim stilstaat
	var tempo: Label             ## pc: 2x / 4x

	func bouw(wereld: Wereld, dp: float, met_tempo := false) -> void:
		w = wereld
		mouse_filter = Control.MOUSE_FILTER_IGNORE
		var sb := StyleBoxFlat.new()
		sb.bg_color = Color(0, 0, 0, 0.5)
		sb.set_content_margin_all(roundf(6 * dp))
		sb.set_corner_radius_all(roundi(4 * dp))
		add_theme_stylebox_override("panel", sb)
		var rij := HBoxContainer.new()
		rij.add_theme_constant_override("separation", roundi(6 * dp))
		rij.mouse_filter = Control.MOUSE_FILTER_IGNORE
		add_child(rij)
		var px := roundi(18.0 * dp)
		kas = _teller(rij, "munt", px, false)
		dorp = _teller(rij, "dorpeling", px, false)
		koe = _teller(rij, "koe", px, true)
		if met_tempo:      # pc: pauze en tempo blijven zichtbaar als de details dicht zijn
			tempo_ik = Ikoon.new()
			tempo_ik.soort = "pauze"
			tempo_ik.custom_minimum_size = Vector2(px, px) * 1.15
			tempo_ik.mouse_filter = Control.MOUSE_FILTER_IGNORE
			tempo_ik.visible = false
			rij.add_child(tempo_ik)
			tempo = Label.new()
			tempo.add_theme_font_size_override("font_size", px)
			tempo.add_theme_color_override("font_color", Color(1.0, 0.85, 0.3))
			tempo.add_theme_color_override("font_outline_color", Color.BLACK)
			tempo.add_theme_constant_override("outline_size", maxi(4, px / 6))
			tempo.mouse_filter = Control.MOUSE_FILTER_IGNORE
			tempo.visible = false
			rij.add_child(tempo)

	func _teller(rij: HBoxContainer, soort: String, px: int, laatste: bool) -> Label:
		var ik := Ikoon.new()
		ik.soort = soort
		ik.custom_minimum_size = Vector2(px, px) * 1.15
		ik.mouse_filter = Control.MOUSE_FILTER_IGNORE
		rij.add_child(ik)
		var l := Label.new()
		l.add_theme_font_size_override("font_size", px)
		l.add_theme_color_override("font_outline_color", Color.BLACK)
		l.add_theme_constant_override("outline_size", maxi(4, px / 6))
		l.mouse_filter = Control.MOUSE_FILTER_IGNORE
		rij.add_child(l)
		if not laatste:
			var tussen := Control.new()
			tussen.custom_minimum_size.x = px * 0.6
			tussen.mouse_filter = Control.MOUSE_FILTER_IGNORE
			rij.add_child(tussen)
		return l

	func zet(kas_toon: int) -> void:
		var doel: Dictionary = w.missie.get("doel", {})
		var t := ["%d" % kas_toon + ("/%d" % int(doel["kas_boven"]) if doel.has("kas_boven") else ""),
			"%d" % w.dorpelingen.size() + ("/%d" % int(doel["dorpelingen"]) if doel.has("dorpelingen") else ""),
			"%d" % w.eigen_koeien() + ("/%d" % int(doel["koeien"]) if doel.has("koeien") else "")]
		if t[0] != kas.text or t[1] != dorp.text or t[2] != koe.text:
			kas.text = t[0]
			dorp.text = t[1]
			koe.text = t[2]
			reset_size()

	## Pc: pauze-icoon als de sim stilstaat, anders "2x"/"4x" als het tempo niet 1 is; bij 1x niets.
	func zet_tempo(pauze: bool, x: int) -> void:
		var t := "" if pauze or x == 1 else "%dx" % x
		if pauze != tempo_ik.visible or t != tempo.text:
			tempo_ik.visible = pauze
			tempo.text = t
			tempo.visible = t != ""
			reset_size()
			if get_parent() is Container:
				(get_parent() as Control).reset_size()


## Zelf getekend icoon (geen lettertekens: het standaardlettertype heeft misschien geen emoji).
class Ikoon extends Control:
	var soort := "munt"

	func _draw() -> void:
		var s := size.y
		var c := size * 0.5
		match soort:
			"pauze":
				for x in [-0.22, 0.08]:
					draw_rect(Rect2(c + Vector2(x, -0.3) * s + Vector2(1, 1), Vector2(0.14, 0.6) * s), Color(0, 0, 0, 0.8))
					draw_rect(Rect2(c + Vector2(x, -0.3) * s, Vector2(0.14, 0.6) * s), Color(1.0, 0.85, 0.3))
			"munt":
				for m in [Vector2(-0.2, 0.18), Vector2(0.2, 0.18), Vector2(0.0, -0.16)]:
					var p: Vector2 = c + m * s
					draw_circle(p + Vector2(0, s * 0.04), s * 0.24, Color8(150, 105, 25))
					draw_circle(p, s * 0.24, Color8(236, 190, 60))
					draw_circle(p, s * 0.11, Color8(250, 222, 120))
			"dorpeling":
				var paars := Color8(214, 70, 214)
				draw_rect(Rect2(c + Vector2(-0.24, -0.04) * s, Vector2(0.48, 0.48) * s), paars)
				draw_circle(c + Vector2(0, -0.04) * s, s * 0.24, paars)
				draw_circle(c + Vector2(0, -0.28) * s, s * 0.17, Color8(240, 200, 160))
			"koe":
				var wit := Color8(245, 245, 240)
				draw_rect(Rect2(c + Vector2(-0.4, -0.14) * s, Vector2(0.62, 0.32) * s), wit)
				for x in [-0.36, -0.2, 0.0, 0.14]:
					draw_rect(Rect2(c + Vector2(x, 0.16) * s, Vector2(0.07, 0.24) * s), wit)
				draw_rect(Rect2(c + Vector2(0.18, -0.32) * s, Vector2(0.24, 0.24) * s), wit)
				draw_circle(c + Vector2(-0.2, 0.0) * s, s * 0.08, Color8(40, 36, 32))
				draw_circle(c + Vector2(0.02, 0.08) * s, s * 0.06, Color8(40, 36, 32))
				draw_rect(Rect2(c + Vector2(0.3, -0.14) * s, Vector2(0.14, 0.08) * s), Color8(230, 160, 160))
