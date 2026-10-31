class_name Pauzemenu
extends CanvasLayer
## Pauzemenu en missie-einde (2026-10-31): een perkament (view/perkament.gd) midden in beeld boven een donker waas.
## Open met de menuknop in de HUD (Hud.menu_knop, naast het munt-icoon) of Esc op de pc. Zolang het open is staat de sim
## stil (het origineel pauzeerde in menu's), pant en draait de camera niet en is de bouwmodus uit; dicht zet de pauze
## terug zoals hij was (een open briefing houdt de sim dus op pauze).
## Knoppen: Hervatten, Missie opnieuw, Andere missie (terug naar het startmenu, view/startmenu.gd), Afsluiten (pc).
## Na de missie (`open_einde`): gewonnen = Volgende missie (als die speelbaar is), Verder spelen, Andere missie;
## verloren = Opnieuw, Andere missie, Bekijken. Opnieuw en een andere missie laden de hoofdscène opnieuw.
## Rechtsboven een noot-knop: muziek aan/uit; op de pc onderaan ook een volumeschuif (view/muziek.gd, user://muziek.cfg).

signal gekozen(actie: String)      ## "hervat", "opnieuw", "andere", "volgende", "afsluiten" (voor tests)

var w: Wereld
var cam: Node                      ## rts_camera.gd: invoer_aan uit zolang het menu open is
var bouwmenu: Bouwmenu
var waas: ColorRect
var paneel: Perkament
var kolom: VBoxContainer
var titel: Label
var sub: Label
var knoppen := {}                  ## actie -> Button
var muziek_rij: HBoxContainer      ## "Muziek" + volumeschuif (view/muziek.gd), alleen pc; niet in `knoppen`
var muziek_knop: Button            ## noot-knop rechts in de kopregel: muziek aan/uit (ook Shift+M)
var _kop_links: Control
var muziek_schuif: HSlider
var _was_gepauzeerd := false
var _cam_invoer := true
var open_nu := false


func _init() -> void:
	layer = 100
	waas = ColorRect.new()
	waas.color = Color(0, 0, 0, 0.5)
	waas.set_anchors_preset(Control.PRESET_FULL_RECT)
	waas.mouse_filter = Control.MOUSE_FILTER_STOP
	add_child(waas)
	paneel = Perkament.new()
	add_child(paneel)
	kolom = VBoxContainer.new()
	kolom.add_theme_constant_override("separation", 10)
	kolom.custom_minimum_size.x = 340
	paneel.add_child(kolom)
	# kopregel: titel in het midden, rechts de muziekknop (view/muziek.gd), links een even brede leegte
	var kop := HBoxContainer.new()
	kolom.add_child(kop)
	var links := Control.new()
	links.mouse_filter = Control.MOUSE_FILTER_IGNORE
	kop.add_child(links)
	titel = Perkament.label("", 28)
	titel.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	titel.vertical_alignment = VERTICAL_ALIGNMENT_CENTER
	titel.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	titel.size_flags_vertical = Control.SIZE_FILL
	kop.add_child(titel)
	muziek_knop = MuziekKnop.new()
	muziek_knop.pressed.connect(func() -> void: Muziek.van(get_tree()).wissel_stil())
	kop.add_child(muziek_knop)
	_kop_links = links
	sub = Perkament.label("", 19)
	sub.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	sub.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	sub.custom_minimum_size.x = 340          # anders meet de autowrap op breedte 0: een woord per regel, veel te hoog
	kolom.add_child(sub)
	# muziekvolume (alleen pc: op touch is de schuif te klein en het paneel te hoog; daar het toestelvolume), onderaan
	muziek_rij = HBoxContainer.new()
	muziek_rij.add_theme_constant_override("separation", 10)
	var mlabel := Perkament.label("Muziek", 19)
	muziek_rij.add_child(mlabel)
	muziek_schuif = HSlider.new()
	muziek_schuif.min_value = 0.0
	muziek_schuif.max_value = 1.0
	muziek_schuif.step = 0.05
	muziek_schuif.focus_mode = Control.FOCUS_NONE
	muziek_schuif.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	muziek_schuif.size_flags_vertical = Control.SIZE_SHRINK_CENTER
	muziek_schuif.tooltip_text = "muziekvolume"
	muziek_schuif.value_changed.connect(func(v: float) -> void: Muziek.van(get_tree()).zet_volume(v))
	muziek_rij.add_child(muziek_schuif)
	kolom.add_child(muziek_rij)
	visible = false


func bouw(wereld: Wereld, camera: Node, bm: Bouwmenu) -> void:
	w = wereld
	cam = camera
	bouwmenu = bm
	if is_inside_tree():
		get_viewport().size_changed.connect(leg_neer)


## Het pauzemenu.
func open() -> void:
	var acties := [["hervat", "Hervatten"], ["opnieuw", "Missie opnieuw"], ["andere", "Andere missie"]]
	if not OS.has_feature("mobile"):
		acties.append(["afsluiten", "Afsluiten"])
	_toon("Pauze", "Missie %d: %s" % [w.missie_nr, Startmenu.titel(w.missie_nr)], acties, Color8(255, 214, 102))


## Na de missie: gewonnen of verloren.
func open_einde(uitslag: String) -> void:
	var nr := w.missie_nr
	if uitslag == "gewonnen":
		var acties := []
		var tekst := "Missie %d: %s" % [nr, Startmenu.titel(nr)]
		if Startmenu.speelbaar(nr + 1):
			acties.append(["volgende", "Volgende missie: %d" % (nr + 1)])
		else:
			tekst += "\nDe volgende missie is nog niet gebouwd."
		acties.append_array([["hervat", "Verder spelen"], ["andere", "Andere missie"]])
		_toon("Missie geslaagd!", tekst, acties, Color(1.0, 0.85, 0.3))
	else:
		_toon("Missie mislukt", "Missie %d: %s" % [nr, Startmenu.titel(nr)],
			[["opnieuw", "Opnieuw"], ["andere", "Andere missie"], ["hervat", "Bekijken"]], Color(1.0, 0.45, 0.35))


func _toon(kop: String, tekst: String, acties: Array, kleur: Color) -> void:
	for b: Button in knoppen.values():
		b.queue_free()
	knoppen.clear()
	titel.text = kop
	titel.add_theme_color_override("font_color", kleur)
	sub.text = tekst
	for a in acties:
		var b := Perkament.knop(a[1], 21)
		b.pressed.connect(kies.bind(a[0]))
		kolom.add_child(b)
		knoppen[a[0]] = b
	kolom.move_child(muziek_rij, -1)
	muziek_rij.visible = not Bouwmenu.touch
	var h := Perkament.knop_h()
	muziek_knop.custom_minimum_size = Vector2(h, h)
	_kop_links.custom_minimum_size = Vector2(h, h)
	werk_muziek_bij()
	if not open_nu:
		open_nu = true
		_was_gepauzeerd = w.gepauzeerd
		if cam != null:
			_cam_invoer = cam.invoer_aan
			cam.invoer_aan = false
	w.gepauzeerd = true
	if bouwmenu != null and bouwmenu.actief:
		bouwmenu.zet_actief(false)
	visible = true
	leg_neer()


## Knoptekst en schuif volgen de muziekspeler (ook als Shift+M hem omzet terwijl het menu open is).
func werk_muziek_bij() -> void:
	if not is_inside_tree():
		return
	var m := Muziek.van(get_tree())
	if not m.gewijzigd.is_connected(werk_muziek_bij):
		m.gewijzigd.connect(werk_muziek_bij)
	muziek_knop.set("uit", m.stil)
	muziek_knop.tooltip_text = "Muziek aan (Shift+M)" if m.stil else "Muziek uit (Shift+M)"
	muziek_knop.queue_redraw()
	muziek_schuif.set_value_no_signal(m.volume)


func sluit() -> void:
	if not open_nu:
		return
	open_nu = false
	visible = false
	w.gepauzeerd = _was_gepauzeerd
	if cam != null:
		cam.invoer_aan = _cam_invoer


func wissel() -> void:
	if open_nu:
		sluit()
	else:
		open()


func kies(actie: String) -> void:
	gekozen.emit(actie)
	match actie:
		"hervat":
			sluit()
		"opnieuw":
			Startmenu.start(w.missie_nr, get_tree())
		"volgende":
			Startmenu.start(w.missie_nr + 1, get_tree())
		"andere":
			Startmenu.terug_naar_menu(get_tree())
		"afsluiten":
			get_tree().quit()


func leg_neer() -> void:
	if not visible:
		return
	var vp := get_viewport().get_visible_rect().size
	paneel.leg_midden(vp, Perkament.schaal())


## Zolang het open is gaan alle toetsen hierheen (geen pauze, tempo, bouwen of prijzen eronder); Esc = hervatten.
func _unhandled_input(e: InputEvent) -> void:
	if not open_nu:
		return
	if e is InputEventKey and e.pressed and not e.echo and (e as InputEventKey).keycode == KEY_ESCAPE:
		kies("hervat")
	if e is InputEventKey or e is InputEventScreenTouch or e is InputEventScreenDrag:
		get_viewport().set_input_as_handled()


## Muziek aan/uit: een getekende dubbele noot in inkt, met een rode streep als de muziek uit staat.
class MuziekKnop extends Button:
	var uit := false

	func _init() -> void:
		focus_mode = Control.FOCUS_NONE
		mouse_default_cursor_shape = Control.CURSOR_POINTING_HAND
		Perkament.stijl(self)

	func _draw() -> void:
		var s := minf(size.x, size.y)
		var o := (size - Vector2(s, s)) * 0.5
		var c := Brief.INKT if not uit else Color(Brief.INKT, 0.55)
		var r := s * 0.11
		var k1 := o + Vector2(s * 0.34, s * 0.7)
		var k2 := o + Vector2(s * 0.66, s * 0.62)
		for k in [k1, k2]:
			draw_set_transform(k, -0.35, Vector2(1.25, 0.9))
			draw_circle(Vector2.ZERO, r, c)
		draw_set_transform(Vector2.ZERO)
		var st := maxf(2.0, s * 0.05)
		var t1 := k1 + Vector2(r * 1.05, -s * 0.42)
		var t2 := k2 + Vector2(r * 1.05, -s * 0.42)
		draw_line(k1 + Vector2(r * 1.05, 0), t1, c, st)
		draw_line(k2 + Vector2(r * 1.05, 0), t2, c, st)
		draw_line(t1, t2, c, st * 2.0)
		if uit:
			draw_line(o + Vector2(s * 0.2, s * 0.2), o + Vector2(s * 0.8, s * 0.8), Color(0.85, 0.2, 0.15), st * 1.4)
