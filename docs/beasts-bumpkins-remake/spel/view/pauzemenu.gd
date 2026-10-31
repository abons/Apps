class_name Pauzemenu
extends CanvasLayer
## Pauzemenu en missie-einde (2026-10-31): een perkament (view/perkament.gd) midden in beeld boven een donker waas.
## Open met de menuknop in de HUD (Hud.menu_knop, naast het munt-icoon) of Esc op de pc. Zolang het open is staat de sim
## stil (het origineel pauzeerde in menu's), pant en draait de camera niet en is de bouwmodus uit; dicht zet de pauze
## terug zoals hij was (een open briefing houdt de sim dus op pauze).
## Knoppen: Hervatten, Missie opnieuw, Andere missie (terug naar het startmenu, view/startmenu.gd), Afsluiten (pc).
## Na de missie (`open_einde`): gewonnen = Volgende missie (als die speelbaar is), Verder spelen, Andere missie;
## verloren = Opnieuw, Andere missie, Bekijken. Opnieuw en een andere missie laden de hoofdscène opnieuw.

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
	titel = Perkament.label("", 28)
	titel.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	kolom.add_child(titel)
	sub = Perkament.label("", 19)
	sub.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	sub.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	sub.custom_minimum_size.x = 340          # anders meet de autowrap op breedte 0: een woord per regel, veel te hoog
	kolom.add_child(sub)
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
