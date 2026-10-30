class_name Bouwmenu
extends Node
## Bouwmenu (stap 5, gameplay.md §7): een knop per gebouw in GEBOUWEN (of zijn toets), alleen voor wat Wereld.ontgrendeld
## al toelaat (hut/kippenhok/loods/weg; loods -> molen, akker; molen -> melkerij, hek, poort).
## Alles kan met een wijzer alleen (besluit gebruiker 2026-10-30, ook voor touch later): indrukken toont de ghost, slepen
## schuift hem (groen = kan, rood = kan niet), loslaten plaatst een Plan. Weg en hek: slepen legt een rij (BouwRij: hoekige
## route om obstakels, een ghost per tegel). De modus blijft aan na het plaatsen; stoppen met de Stop-knop, nog eens op
## de bouwknop, rechterklik of Esc. Draaien met de Draai-knop, het wiel (dan zoomt het wiel niet) of R.
## Een Plan toont de bouwstand (Plan.stand() 1..3 = `<glb>_stand1..3.glb`, uit de af-glb gesneden: zelfde oorsprong en
## ankers), op exact de transform van de af-glb, met een zaagbok en steenhoop ernaast die slinken met de voortgang
## (alleen weergave; kas en aanvoer staan nog niet in de sim). Klaar: de af-glb. De glb's zijn op ware grootte
## (dorpeling 1,37 m); een mensendeur ("voordeur", anders "deur", >= 1 m) schaalt ze op DEUR_M, iets groter dan een
## volwassene. Ontbreekt een stand-glb: een kist die meegroeit; ontbreekt de af-glb: een bruine kist.
## Glb's laden een keer, in de achtergrond (load_threaded_request) zodra een plan er staat; tot de stand er is staat
## de kist er. De materialen van een stand worden op naam die van de af-glb (dus ook dezelfde atlassen), en de
## bouwgrond van stand 1 is een gedeeld materiaal: de eigen atlassen van de stand-glb's vallen daarna vrij.
## Moet NA Bestuur in de boom staan: dan krijgt het de invoer eerst en neemt het de linkerklik van het kiezen over.
## Touch (`touch`: telefoon, of `-- --touch` op de pc; besluit gebruiker 2026-10-30 na de Motorola-proef): niets wordt
## geplaatst voor Bouwen. Bouwknop = ghost op de tegel midden in beeld; een vinger op de ghost sleept hem, slepen ernaast
## pant de camera, een tik ernaast zet de ghost daar. Weg/hek: tik = begin, sleep vanaf begin of eind = dat einde
## verschuift (de rij volgt), Bouwen legt de rij en het eind wordt het nieuwe begin. Knoppen onderin: Draai, Bouwen
## (alleen als het kan), Annuleer; >= 48 dp. De muis-/toetsenbordbesturing hierboven is op de pc ongewijzigd.
## Staand (view/scherm.gd, 2026-10-30): de bouwknoppen zitten in een lade onderin die de knop Gebouwen (rechtsboven)
## opent en een keuze weer sluit; hint, Draai/Stop en de touchbalk staan onderin, de balk past in de breedte. Liggend
## is de indeling zoals ze was. `_indeling` loopt bij elke size_changed.

const GROND_Y := 0.25
const KLIK_DREMPEL := 6.0
## Per bouwsoort (voetafdruk in Wereld.BOUWSOORTEN): knoptekst, toets, glb, hoogte van de kist.
const GEBOUWEN := {
	&"hut": {"tekst": "Hut", "toets": KEY_B, "glb": "res://assets/peasant_hut_rt.glb", "hoogte": 2.4},
	&"gereedschapsloods": {"tekst": "Loods", "toets": KEY_L, "glb": "res://assets/gereedschapsloods_rt.glb", "hoogte": 2.4},
	&"kippenhok": {"tekst": "Kippenhok", "toets": KEY_H, "glb": "res://assets/kippenhok_rt.glb", "hoogte": 1.2},
	&"molen": {"tekst": "Molen", "toets": KEY_M, "glb": "res://assets/molen_rt.glb", "hoogte": 3.0},
	&"melkerij": {"tekst": "Melkerij", "toets": KEY_J, "glb": "res://assets/melkerij_boerderij_rt.glb", "hoogte": 2.6},
	&"akker": {"tekst": "Akker", "toets": KEY_G, "glb": "", "hoogte": 0.3},   # geen glb: per tegel akker_kaal + akker_rijp
	&"weg": {"tekst": "Weg", "toets": KEY_T, "glb": "", "hoogte": 0.15},      # af = padtegel, view/wegen.gd (slepen = rij)
	&"hek": {"tekst": "Hek", "toets": KEY_F, "glb": "", "hoogte": 1.1},       # palen + segmenten naar de buren (slepen = rij)
	&"poort": {"tekst": "Poort", "toets": KEY_P, "glb": "", "hoogte": 1.3},   # hek_poort.glb, vleugel draait open (klik)
	# missie 3 (Wereld.VANAF_MISSIE): put = bron.glb (well, 4,9 x 5,0 m); gilde nog zonder glb: het blok uit Props
	&"put": {"tekst": "Put", "toets": KEY_U, "glb": "res://assets/bron.glb", "hoogte": 2.0},
	&"voetvolkgilde": {"tekst": "Gilde", "toets": KEY_V, "glb": "", "hoogte": 3.0, "placeholder": "gilde"},
}
const RIJ_SOORTEN := [&"weg", &"hek"]     ## slepen = een rij (BouwRij); draaien doet er niet toe
const KNOP_H := 44.0                      ## knophoogte in px: met een vinger te raken
const MENU_LINKS := 760.0                 ## px: het menu begint rechts van de stand linksboven (Hud)
const KLEUR_KAN := Color(0.3, 1.0, 0.3, 0.45)
const KLEUR_NIET := Color(1.0, 0.1, 0.1, 0.55)
const KLEUR_BESTAAT := Color(0.85, 0.85, 0.85, 0.25)
const POORT_OPEN_RAD := deg_to_rad(100.0)
const WIEKEN_RAD_S := 0.9      ## draaisnelheid van de molenwieken

const STAPELS := ["zaagbok", "steenhoop"]   ## bouwplaats (besluit gebruiker, origineel woodpile + rockpile)
const STAPEL_TERUG := {"zaagbok": "houtstapel"}   ## als de eerste ontbreekt
const KIJK_M := 2.6           ## een bouwer binnen deze afstand van de zaagbok of steenhoop kijkt ernaartoe
const STAPEL_RESTANT := 0.35   ## schaal van een stapel vlak voor klaar
const VOLWASSENE_M := 1.37     ## de man, langste volwassene (bumpkin_basis.py; vrouw en ouderen 1,31-1,33)
const DEUR_M := VOLWASSENE_M * 1.15   ## gewenste hoogte van de voordeur: iets groter dan een volwassene

var w: Wereld
var bestuur: Bestuur
var actief := false
var soort: StringName = &"hut"
var draai := 0
var knoppen := {}          ## soort -> Button
var ghost: MeshInstance3D
var _rechts_start := Vector2.ZERO
var _rechts := false
var _kisten := {}          ## Plan -> wat er op de bouwplaats staat: de kist of een stand-instantie
var _getoond := {}         ## Plan -> getoonde stand (0 = de kist)
var view: WereldView       ## optioneel: bouwers laten kijken naar zaagbok of steenhoop
var _stapels := {}         ## Plan -> [Node3D]
var terrein: TerreinView   ## optioneel: grondhoogte voor stapels en hut (anders GROND_Y)
static var _scenes := {}   ## glb-pad -> PackedScene (een keer geladen; null = ontbreekt of mislukt)
static var _laden := {}    ## glb-pad -> true: load_threaded_request loopt
static var _af_info := {}  ## soort -> {schaal, midden}: de transform van de af-glb, ook voor de standen
static var _af_mats := {}  ## soort -> {materiaalnaam: Material} uit de af-glb
static var _los_mats := {} ## materiaalnaam -> Material dat niet in een af-glb zit (bouwgrond), gedeeld over gebouwen
static var _gedeeld := {}  ## stand-pad -> true: materialen al omgezet
var _wieken: Array[Node3D] = []
var _gewas := {}           ## akkertegel -> Node3D (akker_rijp, groeit mee met Wereld.akkers)
var _hekken: Node3D        ## alle hekpalen en -segmenten, opnieuw opgebouwd bij elk afgebouwd hek of poort
var _poorten := {}         ## Plan -> Node3D (poort_deur)
var _sleep_start := Vector2i(-1, -1)   ## weg/hek: tegel waar het slepen begon
var _drukt := false        ## linkerknop (of vinger) ingedrukt in de bouwmodus: loslaten plaatst
var _wijzer := Vector2(-1, -1)          ## laatste wijzerpositie uit de invoer (muis of geemuleerde touch)
var _rij: Array[Vector2i] = []          ## weg/hek: de route van het slepen
var _rij_sleutel := []                  ## wanneer de route opnieuw moet (begin, eind, plannen, kas)
var _rij_ghosts: Array[MeshInstance3D] = []
var knop_draai: Button
var knop_stop: Button
var knop_bouw: Button       ## alleen touch: Bouwen (bevestigen)
var hint: Label
static var touch := OS.has_feature("mobile") or "--touch" in OS.get_cmdline_user_args()   ## touch-bouwen (zie boven)
var knop_h := KNOP_H        ## touch: >= 48 dp (bouw())
var kolom: VBoxContainer   ## liggend rechtsboven (knoppen, hint, Draai, Stop); staand onderin (lade, hint, Draai, Stop)
var rij: HFlowContainer    ## de bouwknoppen
var rij2: HBoxContainer    ## hint (en op de pc Draai en Stop)
var balk: HBoxContainer    ## touch: Draai, Bouwen, Annuleer
var knop_lade: Button      ## staand: Gebouwen (lade open/dicht)
var lade_open := false
var _staand := false
var _t_tegel := Vector2i(-1, -1)   ## touch: gebouw = tegel zoals _plan_onder hem geeft; weg/hek = begintegel
var _t_eind := Vector2i(-1, -1)    ## touch, weg/hek: eindtegel
var _t_vinger := -1                ## touch: vinger die de ghost (of een rij-einde) vasthoudt
var _t_greep := Vector2i.ZERO      ## touch, gebouw: tegel onder de vinger min _t_tegel bij het vastpakken
var _t_einde := 1                  ## touch, weg/hek: 0 = begin vast, 1 = eind vast
var _t_tik := {}                   ## touch: vinger naast de ghost -> startpositie (tik = ghost daarheen)
var _t_rij: Array[Vector2i] = []   ## touch, weg/hek: route _t_tegel -> _t_eind
var _t_st: Array[int] = []         ## en de BouwRij-status per tegel
var _t_sleutel := []
var _t_getoond := []               ## de _t_sleutel waarvan de rij-ghosts nu staan


func bouw(wereld: Wereld, b: Bestuur, parent3d: Node3D) -> void:
	w = wereld
	bestuur = b
	ghost = _kist(soort, Color(0.3, 1.0, 0.3, 0.45))
	ghost.visible = false
	parent3d.add_child(ghost)
	w.plan_gezet.connect(_toon_plan)
	w.plan_klaar.connect(_plan_klaar)
	_hekken = Node3D.new()
	_hekken.name = "Hekken"
	parent3d.add_child(_hekken)

	if touch:
		knop_h = touch_knop_h()
	var laag := CanvasLayer.new()
	add_child(laag)
	# rechtsboven, rechts van de stand (linksboven): de knoppen lopen door op een tweede regel als het niet past,
	# daaronder hint, Draai en Stop. Onder staat de hulptekst.
	kolom = VBoxContainer.new()
	kolom.set_anchors_preset(Control.PRESET_TOP_WIDE)
	kolom.offset_left = MENU_LINKS
	kolom.offset_top = 12
	kolom.offset_right = -16
	kolom.add_theme_constant_override("separation", 8)
	kolom.mouse_filter = Control.MOUSE_FILTER_IGNORE
	laag.add_child(kolom)
	rij = HFlowContainer.new()
	rij.add_theme_constant_override("h_separation", 8)
	rij.add_theme_constant_override("v_separation", 8)
	rij.alignment = FlowContainer.ALIGNMENT_END
	rij.mouse_filter = Control.MOUSE_FILTER_IGNORE
	kolom.add_child(rij)
	for s: StringName in GEBOUWEN:
		var g: Dictionary = GEBOUWEN[s]
		var k := _knop(("%s %d" % [g["tekst"], w.prijs(s)]) if touch \
				else ("%s %d (%s)" % [g["tekst"], w.prijs(s), OS.get_keycode_string(g["toets"])]))
		k.toggle_mode = true
		k.toggled.connect(func(aan: bool) -> void: kies(s, aan))
		rij.add_child(k)
		knoppen[s] = k
		k.visible = w.ontgrendeld(s)
	w.plan_klaar.connect(func(_p: Plan) -> void:       # nieuwe knoppen na een loods of molen
		for s2 in knoppen:
			(knoppen[s2] as Button).visible = w.ontgrendeld(s2))
	# draaien en stoppen ook zonder toets, wiel of rechterknop (touch): twee knoppen onder het menu, alleen in de modus
	rij2 = HBoxContainer.new()
	rij2.add_theme_constant_override("separation", 8)
	rij2.alignment = BoxContainer.ALIGNMENT_END
	rij2.mouse_filter = Control.MOUSE_FILTER_IGNORE
	kolom.add_child(rij2)
	hint = Label.new()
	hint.add_theme_font_size_override("font_size", int(knop_h * 0.3) if touch else 15)
	hint.add_theme_color_override("font_outline_color", Color.BLACK)
	hint.add_theme_constant_override("outline_size", 5)
	hint.mouse_filter = Control.MOUSE_FILTER_IGNORE
	hint.vertical_alignment = VERTICAL_ALIGNMENT_CENTER
	rij2.add_child(hint)
	if touch:
		_bouw_touch_balk(laag)
	else:
		knop_draai = _knop("Draai (R / wiel)")
		knop_draai.custom_minimum_size.x = 150
		knop_draai.pressed.connect(draai_verder)
		rij2.add_child(knop_draai)
		knop_stop = _knop("X  Stop (Esc)")
		knop_stop.custom_minimum_size.x = 130
		knop_stop.pressed.connect(func() -> void: zet_actief(false))
		rij2.add_child(knop_stop)
	knop_lade = _knop("Gebouwen")
	knop_lade.toggle_mode = true
	knop_lade.visible = false
	knop_lade.toggled.connect(zet_lade)
	laag.add_child(knop_lade)
	kolom.draw.connect(_teken_lade)
	zet_actief(false)
	get_viewport().size_changed.connect(_indeling)
	_indeling()
	match Scherm.optie("proef"):     # alleen voor frames (view/scherm.gd)
		"bouw": kies.call_deferred(&"hut")
		"lade": zet_lade.call_deferred(true)


## 48 dp met een marge; de Motorola (~400 dpi) geeft ~130 px.
static func touch_knop_h() -> float:
	return clampf(52.0 * DisplayServer.screen_get_dpi() / 160.0, 110.0, 180.0)


## Legt het menu neer voor de huidige viewport: liggend zoals altijd (rechtsboven), staand de lade onderin.
func _indeling() -> void:
	var vp := get_viewport().get_visible_rect().size
	_staand = Scherm.staand(vp)
	var onder := 12.0
	if balk != null:
		var sep := int(knop_h * 0.3)
		var per := knop_h * 2.4
		if _staand:
			per = minf(per, floorf((vp.x - 24.0 - 2.0 * sep) / 3.0))
		for k: Button in [knop_draai, knop_bouw, knop_stop]:
			k.custom_minimum_size.x = per
		balk.set_anchors_and_offsets_preset(Control.PRESET_CENTER_BOTTOM, Control.PRESET_MODE_MINSIZE, int(knop_h * 0.25))
		balk.grow_horizontal = Control.GROW_DIRECTION_BOTH
		balk.grow_vertical = Control.GROW_DIRECTION_BEGIN
		onder = knop_h * 1.25 + 12.0
	if _staand:
		kolom.set_anchors_preset(Control.PRESET_BOTTOM_WIDE)
		kolom.grow_vertical = Control.GROW_DIRECTION_BEGIN
		kolom.offset_left = 12
		kolom.offset_right = -12
		kolom.offset_bottom = -onder
		kolom.offset_top = -onder
		rij.alignment = FlowContainer.ALIGNMENT_CENTER
		rij2.alignment = BoxContainer.ALIGNMENT_CENTER
		hint.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
		hint.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
		hint.size_flags_horizontal = Control.SIZE_EXPAND_FILL
		knop_lade.visible = true
		knop_lade.set_anchors_and_offsets_preset(Control.PRESET_TOP_RIGHT, Control.PRESET_MODE_MINSIZE, 12)
		knop_lade.grow_horizontal = Control.GROW_DIRECTION_BEGIN
	else:
		kolom.set_anchors_preset(Control.PRESET_TOP_WIDE)
		kolom.grow_vertical = Control.GROW_DIRECTION_END
		kolom.offset_left = MENU_LINKS
		kolom.offset_top = 12
		kolom.offset_right = -16
		kolom.offset_bottom = 12
		rij.alignment = FlowContainer.ALIGNMENT_END
		rij2.alignment = BoxContainer.ALIGNMENT_END
		hint.autowrap_mode = TextServer.AUTOWRAP_OFF
		hint.horizontal_alignment = HORIZONTAL_ALIGNMENT_LEFT
		hint.size_flags_horizontal = Control.SIZE_FILL
		knop_lade.visible = false
	rij.visible = lade_open or not _staand
	kolom.queue_redraw()


## Staand: de lade met bouwknoppen open of dicht (knop Gebouwen; een keuze sluit hem).
func zet_lade(open: bool) -> void:
	lade_open = open
	if knop_lade.button_pressed != open:
		knop_lade.set_pressed_no_signal(open)
	rij.visible = open or not _staand
	kolom.queue_redraw()


## Donkere achtergrond achter de open lade (staand); liggend tekent dit niets.
func _teken_lade() -> void:
	if _staand and rij.visible:
		var sb := StyleBoxFlat.new()
		sb.bg_color = Color(0, 0, 0, 0.55)
		sb.set_corner_radius_all(8)
		kolom.draw_style_box(sb, Rect2(rij.position, rij.size).grow(8))


## Touch: Draai, Bouwen en Annuleer onderin het midden, groot genoeg voor een duim.
func _bouw_touch_balk(laag: CanvasLayer) -> void:
	balk = HBoxContainer.new()
	balk.add_theme_constant_override("separation", int(knop_h * 0.3))
	laag.add_child(balk)
	knop_draai = _knop("Draai")
	knop_draai.pressed.connect(draai_verder)
	knop_bouw = _knop("Bouwen")
	knop_bouw.icon = _ikoon(true)
	knop_bouw.add_theme_color_override("font_color", Color(0.75, 1.0, 0.7))
	knop_bouw.pressed.connect(bevestig)
	knop_stop = _knop("Annuleer")
	knop_stop.icon = _ikoon(false)
	knop_stop.add_theme_color_override("font_color", Color(1.0, 0.75, 0.7))
	knop_stop.pressed.connect(func() -> void: zet_actief(false))
	for k: Button in [knop_draai, knop_bouw, knop_stop]:
		k.custom_minimum_size.x = knop_h * 2.4
		k.expand_icon = false
		balk.add_child(k)


## Vinkje (true) of kruis als knopicoon, zelf getekend: het standaardlettertype heeft misschien geen ✓ en ✗.
func _ikoon(vink: bool) -> ImageTexture:
	var n := int(knop_h * 0.45)
	var img := Image.create(n, n, false, Image.FORMAT_RGBA8)
	var kleur := Color(0.45, 1.0, 0.4) if vink else Color(1.0, 0.4, 0.35)
	var lijnen: Array = [[Vector2(0.12, 0.55), Vector2(0.4, 0.82)], [Vector2(0.4, 0.82), Vector2(0.9, 0.2)]] if vink \
			else [[Vector2(0.18, 0.18), Vector2(0.82, 0.82)], [Vector2(0.82, 0.18), Vector2(0.18, 0.82)]]
	var dik := 0.075 * n
	for y in n:
		for x in n:
			var p := Vector2(x + 0.5, y + 0.5)
			var d := INF
			for l in lijnen:
				var a: Vector2 = l[0] * n
				var b: Vector2 = l[1] * n
				d = minf(d, p.distance_to(Geometry2D.get_closest_point_to_segment(p, a, b)))
			var al := clampf(dik + 0.5 - d, 0.0, 1.0)
			if al > 0.0:
				img.set_pixel(x, y, Color(kleur, al))
	return ImageTexture.create_from_image(img)


func _knop(tekst: String) -> Button:
	var k := Button.new()
	k.text = tekst
	k.custom_minimum_size = Vector2(0, knop_h)
	k.add_theme_font_size_override("font_size", int(knop_h * 0.33) if touch else 18)
	k.focus_mode = Control.FOCUS_NONE
	return k


## Een kwartslag verder (Draai-knop, wiel omlaag, R); -1 = terug (wiel omhoog). Niet voor weg en hek.
func draai_verder(stap := 1) -> void:
	if actief and not soort in RIJ_SOORTEN:
		draai = posmod(draai + stap, 4)


## Zet de bouwmodus aan voor `s`, of uit.
func kies(s: StringName, aan := true) -> void:
	if aan and not w.ontgrendeld(s):
		return
	if aan and s != soort:
		soort = s
		var oud := ghost
		ghost = _kist(soort, Color(0.3, 1.0, 0.3, 0.45))
		oud.get_parent().add_child(ghost)
		oud.queue_free()
	zet_actief(aan)
	if aan and _staand and lade_open:
		zet_lade(false)
	if aan and touch:
		_touch_begin()


func zet_actief(aan: bool) -> void:
	actief = aan
	ghost.visible = aan
	_drukt = false
	_sleep_start = Vector2i(-1, -1)
	_t_vinger = -1
	_t_tik.clear()
	_t_sleutel = []
	_t_getoond = []
	_toon_rij([], [])
	for s in knoppen:
		var k: Button = knoppen[s]
		var moet: bool = aan and s == soort
		if k.button_pressed != moet:
			k.set_pressed_no_signal(moet)
	if knop_stop != null:
		knop_stop.visible = aan
		knop_draai.visible = aan
		knop_draai.disabled = soort in RIJ_SOORTEN
		hint.visible = aan
		var g: String = GEBOUWEN[soort]["tekst"]
		if touch:
			knop_bouw.visible = aan
			hint.text = ("%s: tik = begin, sleep het eind, dan Bouwen" % g) if soort in RIJ_SOORTEN \
					else ("%s: sleep de ghost, dan Bouwen" % g)
		else:
			hint.text = ("%s: slepen = rij, loslaten = plaatsen" % g) if soort in RIJ_SOORTEN \
					else ("%s: loslaten = plaatsen" % g)
			hint.text += "   rechts = stop"
	if aan:
		bestuur.wis_selectie()


func _hoogte(s: StringName) -> float:
	return GEBOUWEN[s]["hoogte"]


func _kist(s: StringName, kleur: Color) -> MeshInstance3D:
	var m := BoxMesh.new()
	var af: Vector2i = Wereld.BOUWSOORTEN[s]
	m.size = Vector3(af.x * w.tegel_m, _hoogte(s), af.y * w.tegel_m)
	var mat := StandardMaterial3D.new()
	mat.albedo_color = kleur
	mat.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
	mat.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
	var mi := MeshInstance3D.new()
	mi.mesh = m
	mi.material_override = mat
	return mi


func _midden(p: Plan) -> Vector3:
	var r := p.afdruk()
	return Vector3((r.position.x + r.size.x * 0.5) * w.tegel_m, GROND_Y + _hoogte(p.soort) * 0.5, (r.position.y + r.size.y * 0.5) * w.tegel_m)


func _plan_onder(pos: Vector2) -> Plan:
	return _plan_op(bestuur.tegel_onder(pos))


## Het plan van de huidige soort en draai met tegel `t` als middentegel (zoals onder de wijzer), null buiten de grond.
func _plan_op(t: Vector2i) -> Plan:
	if t.x < 0:
		return null
	var af: Vector2i = Wereld.BOUWSOORTEN[soort]
	var links := t - Vector2i(af.x / 2, af.y / 2)
	return Plan.new(soort, links, draai, af.x, af.y)


func _process(_dt: float) -> void:
	if not w.gepauzeerd:
		for wk in _wieken:
			wk.rotate_object_local(Vector3.UP, WIEKEN_RAD_S * _dt * w.tempo)   # as = lokale Y (README gebouwen)
	var rijp := float(w.spel["economie"]["rijp_s"])
	for t in _gewas:
		var g: Node3D = _gewas[t]
		var f: float = w.akkers.get(t, 0.0) / rijp
		g.visible = f > 0.05
		g.scale = Vector3(1.0, maxf(0.05, f), 1.0)
	for p in _stapels:
		for s: Node3D in _stapels[p]:
			s.scale = Vector3.ONE * lerpf(1.0, STAPEL_RESTANT, p.voortgang)
	for p in _kisten:
		if p.klaar:
			continue
		if _werk_stand(p):
			continue
		var k := _kisten[p] as MeshInstance3D
		if k == null:
			continue
		var f: float = float(p.stand()) / Plan.STANDEN
		if p.soort != &"weg":      # een weg is plat: alleen de kleur loopt mee
			k.scale.y = f
			k.position.y = GROND_Y + _hoogte(p.soort) * 0.5 * k.scale.y
		(k.material_override as StandardMaterial3D).albedo_color = Color(0.9, 0.8, 0.4, 0.5).lerp(Color(0.55, 0.4, 0.25, 1.0), f)
	_kijk_bouwers()
	for pt in _poorten:
		var dr: Node3D = _poorten[pt]
		dr.rotation.y = lerp_angle(dr.rotation.y, POORT_OPEN_RAD if pt.open else 0.0, minf(1.0, _dt * 5.0))
	if not actief:
		return
	if touch:
		_toon_touch()
		return
	if soort in RIJ_SOORTEN and _drukt and _sleep_start.x >= 0:
		ghost.visible = false
		var eind := bestuur.tegel_onder(_wijzer)
		if eind.x < 0:
			return
		var sleutel := [_sleep_start, eind, w.plannen.size(), w.kas]
		if sleutel != _rij_sleutel:       # A* alleen als er iets veranderd is
			_rij_sleutel = sleutel
			_rij = BouwRij.route(w, soort, _sleep_start, eind)
			_toon_rij(_rij, BouwRij.statussen(w, soort, _rij))
		return
	_toon_ghost(_plan_onder(_wijzer))


## De ghost op plan `p` (groen = kan, rood = kan niet); geeft of het kan. Null = geen ghost.
func _toon_ghost(p: Plan) -> bool:
	ghost.visible = p != null
	if p == null:
		return false
	ghost.position = _midden(p)
	if soort == &"weg":
		ghost.position.y = _grond(p.tegel).y + _hoogte(soort) * 0.5
	ghost.rotation.y = draai * PI * 0.5
	var kan := w.kan_bouwen(p) and w.kan_betalen(p.soort)
	if soort in RIJ_SOORTEN:
		kan = BouwRij.statussen(w, soort, [p.tegel])[0] == BouwRij.KAN
	(ghost.material_override as StandardMaterial3D).albedo_color = KLEUR_KAN if kan else KLEUR_NIET
	return kan


## Een ghost-tegel per tegel van de rij, gekleurd naar BouwRij-status (groen kan, rood kan niet of te duur, grijs al
## weg of al hek). Lege lijst = alles weg.
func _toon_rij(tegels: Array[Vector2i], st: Array[int]) -> void:
	if ghost == null:
		return
	while _rij_ghosts.size() < tegels.size():
		var m := BoxMesh.new()
		m.size = Vector3(w.tegel_m * 0.9, 1.0, w.tegel_m * 0.9)
		var mat := StandardMaterial3D.new()
		mat.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
		mat.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
		var mi := MeshInstance3D.new()
		mi.mesh = m
		mi.material_override = mat
		mi.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
		ghost.get_parent().add_child(mi)
		_rij_ghosts.append(mi)
	var h := _hoogte(soort)
	for i in _rij_ghosts.size():
		var mi := _rij_ghosts[i]
		mi.visible = i < tegels.size()
		if not mi.visible:
			continue
		var s: int = st[i]
		var hh := h if s != BouwRij.BESTAAT else 0.05
		mi.scale = Vector3(1.0, hh, 1.0)
		mi.position = _grond(tegels[i]) + Vector3(0, hh * 0.5, 0)
		(mi.material_override as StandardMaterial3D).albedo_color = KLEUR_KAN if s == BouwRij.KAN \
				else (KLEUR_BESTAAT if s == BouwRij.BESTAAT else KLEUR_NIET)


func _toon_plan(p: Plan) -> void:
	var mi := _kist(p.soort, Color(0.9, 0.8, 0.4, 0.5))
	mi.position = _midden(p)
	mi.rotation.y = p.draai * PI * 0.5
	_kisten[p] = mi
	_getoond[p] = 0
	ghost.get_parent().add_child(mi)
	var lijst: Array[Node3D] = []
	var plekken := _stapelplekken(p, STAPELS.size() if not p.soort in [&"akker", &"hek", &"poort", &"weg"] else 0)
	for i in plekken.size():
		var naam: String = STAPELS[i]
		if not Natuur.bestaat(naam) and STAPEL_TERUG.has(naam):
			naam = STAPEL_TERUG[naam]
		var n := Natuur.instantie(naam)
		if n == null:
			continue
		n.position = _grond(plekken[i])
		n.rotation.y = p.draai * PI * 0.5 + i * 0.7
		n.set_meta("stapel", STAPELS[i])
		ghost.get_parent().add_child(n)
		lijst.append(n)
	_stapels[p] = lijst


func _grond(t: Vector2i) -> Vector3:
	var v := Vector3((t.x + 0.5) * w.tegel_m, GROND_Y, (t.y + 0.5) * w.tegel_m)
	if terrein != null:
		v.y = terrein.hoogte_op(v.x, v.z)
	return v


## Stapelplekken: tegels net buiten de voetafdruk aan de deurkant (sim/plan.gd deur_richting, ook na draaien), naast de
## deurtegel en niet op het pad ervoor of op een weg, dichtstbij de deur eerst; pas als die kant vol is de andere
## kanten. Zo staan zaagbok en steenhoop voor het gebouw bij de deur, nooit erachter of erin (2026-10-30).
func _stapelplekken(p: Plan, n: int) -> Array[Vector2i]:
	var uit: Array[Vector2i] = []
	if n <= 0:
		return uit
	var r := p.afdruk()
	var deur := p.deur_tegel()
	var dr := p.deur_richting()
	var pad_i := w.raster.namen.find("pad")
	var vrij := func(t: Vector2i) -> bool:
		if r.has_point(t) or t == deur or t == deur + dr or not w.raster.loopbaar_v(t) or w.plan_op(t) != null:
			return false
		return pad_i < 0 or w.raster.soort[w.raster.idx(t.x, t.y)] != pad_i
	var zij := Vector2i(-dr.y, dr.x)       # langs de gevel
	var kand: Array[Vector2i] = []
	for k in range(1, maxi(r.size.x, r.size.y) + 2):   # deurkant: om en om naast de deur, eerst dichtbij
		kand.append(deur + zij * k)
		kand.append(deur - zij * k)
	for k in range(1, 4):                  # een rij verder van de gevel
		kand.append(deur + dr + zij * k)
		kand.append(deur + dr - zij * k)
	for c in range(r.position.x - 1, r.end.x + 1):     # noodgeval: de rest van de rand
		kand.append(Vector2i(c, r.end.y))
		kand.append(Vector2i(c, r.position.y - 1))
	for rij in range(r.position.y, r.end.y):
		kand.append(Vector2i(r.end.x, rij))
		kand.append(Vector2i(r.position.x - 1, rij))
	for t in kand:
		if uit.size() < n and not t in uit and vrij.call(t):
			uit.append(t)
	return uit


## Plan af: stapels weg, de kist wordt het gebouw (glb op ware grootte, of op de mensendeur geschaald).
func _plan_klaar(p: Plan) -> void:
	for s: Node3D in _stapels.get(p, []):
		s.queue_free()
	_stapels.erase(p)
	var k: Node3D = _kisten.get(p)
	if k == null:
		return
	_getoond.erase(p)
	if p.soort == &"akker":
		_maak_akker(p)
		k.queue_free()
		_kisten.erase(p)
		return
	if p.soort == &"weg":       # de padtegel tekent view/wegen.gd (Wereld.wegen_veranderd)
		k.queue_free()
		_kisten.erase(p)
		return
	if p.soort == &"hek" or p.soort == &"poort":
		k.queue_free()
		_kisten.erase(p)
		_bouw_hekken()
		return
	var ps := _scene(GEBOUWEN[p.soort]["glb"], true)
	if ps == null and GEBOUWEN[p.soort].has("placeholder"):     # nog geen glb (voetvolkgilde): het blok uit Props
		var ph := Props.maak({"model": "placeholder:" + String(GEBOUWEN[p.soort]["placeholder"]), "cls": 0,
			"x": p.tegel.x, "y": p.tegel.y, "state": 0})
		if ph != null:
			var r := p.afdruk()
			var m := Vector3((r.position.x + r.size.x * 0.5) * w.tegel_m, GROND_Y, (r.position.y + r.size.y * 0.5) * w.tegel_m)
			if terrein != null:
				m.y = _laagste_grond(r)
			ph.position = m
			ph.rotation.y = p.draai * PI * 0.5
			ghost.get_parent().add_child(ph)
			k.queue_free()
			_kisten.erase(p)
			return
	if ps == null:
		if not k is MeshInstance3D:      # kan niet: een stand staat er alleen als de af-glb er is
			return
		k.scale.y = 1.0
		k.position.y = GROND_Y + _hoogte(p.soort) * 0.5
		(k.material_override as StandardMaterial3D).albedo_color = Color(0.55, 0.4, 0.25, 1.0)
		return
	var hut: Node3D = ps.instantiate()
	_zet_op_plek(hut, p)
	ghost.get_parent().add_child(hut)
	var wk := hut.find_child("wieken", true, false) as Node3D
	if wk != null:
		_wieken.append(wk)
	k.queue_free()
	_kisten.erase(p)


## Glb-pad van bouwstand `n` (1..3) van `soort`, "" als de soort geen standen heeft (akker, weg, hek, poort).
static func stand_pad(soort: StringName, n: int) -> String:
	var glb: String = GEBOUWEN[soort]["glb"]
	if not glb.ends_with("_rt.glb"):
		return ""
	return glb.trim_suffix("_rt.glb") + "_stand%d.glb" % n


## De PackedScene van `pad` uit de cache. Niet geladen: start het laden in de achtergrond en geeft null (wacht = true:
## blokkeert tot hij er is). Null blijft null als het bestand ontbreekt of het laden mislukte.
static func _scene(pad: String, wacht := false) -> PackedScene:
	if _scenes.has(pad):
		return _scenes[pad]
	if pad == "" or not ResourceLoader.exists(pad):
		_scenes[pad] = null
		return null
	if not _laden.has(pad):
		if wacht:
			_scenes[pad] = load(pad) as PackedScene
			return _scenes[pad]
		ResourceLoader.load_threaded_request(pad, "PackedScene", true)
		_laden[pad] = true
		return null
	var st := ResourceLoader.load_threaded_get_status(pad)
	if st == ResourceLoader.THREAD_LOAD_LOADED or (wacht and st == ResourceLoader.THREAD_LOAD_IN_PROGRESS):
		_scenes[pad] = ResourceLoader.load_threaded_get(pad) as PackedScene
		_laden.erase(pad)
		return _scenes[pad]
	if st == ResourceLoader.THREAD_LOAD_IN_PROGRESS:
		return null
	_scenes[pad] = null      # mislukt
	_laden.erase(pad)
	return null


## Schaal (op de mensendeur) en midden van het omhulsel van de af-glb van `soort`, een keer gemeten; de standen
## krijgen dezelfde, want hun omhulsel is kleiner en hun deurblad ontbreekt. Bewaart ook de materialen van de af-glb.
static func _info(soort: StringName, ps: PackedScene) -> Dictionary:
	if _af_info.has(soort):
		return _af_info[soort]
	var hut: Node3D = ps.instantiate()
	var box := _omhulsel(hut, Transform3D.IDENTITY)
	# Ware grootte, tenzij er een mensendeur is: dan op DEUR_M (het kippendeurtje van 0,4 m telt niet).
	var schaal := 1.0
	var deur := hut.find_child("voordeur", true, false)
	if deur == null:
		deur = hut.find_child("deur", true, false)
	if deur != null:
		var dh := _omhulsel_van(hut, deur).size.y
		if dh >= 1.0:
			schaal = DEUR_M / dh
	var mats := {}
	_verzamel_mats(hut, mats)
	_af_mats[soort] = mats
	hut.free()
	_af_info[soort] = {"schaal": schaal, "midden": box.get_center() * schaal}
	return _af_info[soort]


static func _verzamel_mats(n: Node, uit: Dictionary) -> void:
	if n is MeshInstance3D and (n as MeshInstance3D).mesh != null:
		var mesh := (n as MeshInstance3D).mesh
		for s in mesh.get_surface_count():
			var m := mesh.surface_get_material(s)
			if m != null and m.resource_name != "" and not uit.has(m.resource_name):
				uit[m.resource_name] = m
	for c in n.get_children():
		_verzamel_mats(c, uit)


## Zet de materialen van een stand-glb een keer om naar die van de af-glb (zelfde naam = zelfde atlas en UV's); wat
## daar niet in zit (bouwgrond) wordt een materiaal dat alle gebouwen delen. De meshes zijn gedeeld tussen instanties,
## dus dit geldt voor elke volgende instantie, en de eigen materialen en texturen van de stand vallen vrij.
static func _deel_materialen(pad: String, soort: StringName, ps: PackedScene) -> void:
	if _gedeeld.has(pad):
		return
	_gedeeld[pad] = true
	var af: Dictionary = _af_mats.get(soort, {})
	var n := ps.instantiate()
	var lijst: Array = []
	Natuur._meshes(n, lijst)
	for mi: MeshInstance3D in lijst:
		if mi.mesh == null:
			continue
		for s in mi.mesh.get_surface_count():
			var m := mi.mesh.surface_get_material(s)
			if m == null or m.resource_name == "":
				continue
			var nm := m.resource_name
			if af.has(nm):
				mi.mesh.surface_set_material(s, af[nm])
			elif _los_mats.has(nm):
				mi.mesh.surface_set_material(s, _los_mats[nm])
			else:
				_los_mats[nm] = m
	n.free()


## Zet een gebouw-instantie (af of stand) op de transform van de af-glb voor plan `p`.
func _zet_op_plek(n: Node3D, p: Plan) -> void:
	var info := _info(p.soort, _scene(GEBOUWEN[p.soort]["glb"], true))
	var schaal: float = info["schaal"]
	var r := p.afdruk()
	n.scale = Vector3.ONE * schaal
	n.rotation.y = p.draai * PI * 0.5
	var m := Vector3((r.position.x + r.size.x * 0.5) * w.tegel_m, GROND_Y, (r.position.y + r.size.y * 0.5) * w.tegel_m)
	if terrein != null:
		m.y = _laagste_grond(r)
	var midden: Vector3 = info["midden"]
	# y = 0 in de glb is de grond (stenen en keien steken er met opzet onder); vroeger zette dit de onderkant van het
	# omhulsel op de grond, en dan zweefde de hut 16 cm (de funderingsstenen gaan tot -0,16 m)
	n.position = m - Vector3(midden.x, 0.0, midden.z).rotated(Vector3.UP, n.rotation.y)


## Bouwstand bijwerken voor een plan dat nog niet klaar is. False = deze soort of stand heeft geen glb (dan groeit de
## kist zoals vroeger); true = de stand staat er, of hij wordt nog geladen (dan blijft staan wat er stond).
func _werk_stand(p: Plan) -> bool:
	var wil := p.stand()
	var pad := stand_pad(p.soort, wil)
	if pad == "":
		return false
	var nu: int = _getoond.get(p, 0)
	if nu == wil:
		return true
	var af_pad: String = GEBOUWEN[p.soort]["glb"]
	var af := _scene(af_pad)
	var ps := _scene(pad)
	if wil < Plan.STANDEN - 1:
		_scene(stand_pad(p.soort, wil + 1))     # de volgende alvast in de achtergrond
	if (ps == null and _scenes.has(pad)) or (af == null and _scenes.has(af_pad)):
		return nu > 0              # ontbreekt: de vorige stand blijft staan, of de kist groeit verder
	if ps == null or af == null:
		return true                # wordt nog geladen: de kist (of de vorige stand) blijft
	_info(p.soort, af)
	_deel_materialen(pad, p.soort, ps)
	var n: Node3D = ps.instantiate()
	_zet_op_plek(n, p)
	ghost.get_parent().add_child(n)
	(_kisten[p] as Node3D).queue_free()
	_kisten[p] = n
	_getoond[p] = wil
	return true


## Een bouwer die aan een plan werkt en binnen KIJK_M van de zaagbok of steenhoop staat, kijkt ernaartoe en pakt
## het gereedschap van het origineel: bij de zaagbok de zaag (`saw`), bij de steenhoop de houweel (`pick`).
const STAPEL_WERK := {"zaagbok": &"zagen", "steenhoop": &"houweel"}

func _kijk_bouwers() -> void:
	if view == null:
		return
	for d in w.dorpelingen:
		var u: Dictionary = view.units.get(d.id, {})
		if u.is_empty():
			continue
		var b: Bumpkin = u["bump"]
		b.werk_voorkeur = &""
		if not d.bouwt or d.werk_plan == null or d.werk_plan.klaar or not _stapels.has(d.werk_plan):
			continue
		var best: Node3D = null
		var best_d := KIJK_M
		for s: Node3D in _stapels[d.werk_plan]:
			var a := Vector2(s.global_position.x - b.global_position.x, s.global_position.z - b.global_position.z).length()
			if a < best_d:
				best_d = a
				best = s
		if best != null:
			b.kijk_naar(best.global_position - b.global_position)
			b.werk_voorkeur = STAPEL_WERK.get(best.get_meta("stapel", ""), &"")

## Hekken opnieuw: een paal op elk hektegelmidden, een segment (2 m, palen op x = +-1) naar elk hek- of poortbuur
## (recht; schuin alleen zonder rechte tussenburen, dan 1,41x lang). Een poort draait zijn doorgang langs de hekken.
func _bouw_hekken() -> void:
	for c in _hekken.get_children():
		c.queue_free()
	_poorten.clear()
	var hek := {}
	var poort := {}
	for p in w.plannen:
		if p.klaar and p.soort == &"hek":
			hek[p.tegel] = p
		elif p.klaar and p.soort == &"poort":
			poort[p.tegel] = p
	var tm := w.tegel_m
	for t: Vector2i in hek:
		var paal := Natuur.instantie("hek_paal")
		if paal:
			paal.position = _grond(t)
			_hekken.add_child(paal)
		for d in [Vector2i(1, 0), Vector2i(0, 1), Vector2i(1, 1), Vector2i(-1, 1), Vector2i(-1, 0), Vector2i(0, -1)]:
			var n: Vector2i = t + d
			var naar_hek := hek.has(n)
			if not naar_hek and not poort.has(n):
				continue
			if naar_hek and (d.x < 0 or d.y < 0):
				continue        # hek-hek een keer (alleen naar + richtingen); naar een poort altijd vanaf het hek
			if d.x != 0 and d.y != 0 and (hek.has(t + Vector2i(d.x, 0)) or hek.has(t + Vector2i(0, d.y))):
				continue
			var seg := Natuur.instantie("hek_segment")
			if seg == null:
				continue
			var a := _grond(t)
			var b := _grond(n)
			if poort.has(n):    # tot aan de poortpaal op de tegelrand
				b = a.lerp(b, 0.5)
			seg.position = (a + b) * 0.5
			seg.rotation.y = atan2(-(b.z - a.z), b.x - a.x)
			seg.scale.x = Vector2(b.x - a.x, b.z - a.z).length() / tm
			_hekken.add_child(seg)
	for t: Vector2i in poort:
		var p: Plan = poort[t]
		var n := Natuur.instantie("hek_poort")       # houten hekpoort (origineel `gate`); `poort` is de stenen sleutelpoort
		if n == null:
			continue
		n.position = _grond(t)
		# doorgang langs x; staan de hekken boven en onder (z), dan een kwartslag
		var langs_z := hek.has(t + Vector2i(0, 1)) or hek.has(t + Vector2i(0, -1))
		var langs_x := hek.has(t + Vector2i(1, 0)) or hek.has(t + Vector2i(-1, 0))
		var rot := (p.draai % 2) * PI * 0.5        # zonder hekken ernaast: zoals de speler hem draaide
		if langs_z and not langs_x:
			rot = PI * 0.5
		elif langs_x:
			rot = 0.0
		n.rotation.y = rot
		_hekken.add_child(n)
		var deur := n.find_child("poort_deur", true, false) as Node3D
		if deur:
			_poorten[p] = deur


## Laagste grond onder de voetafdruk (hoeken en midden): op een helling zakt het gebouw liever iets in dan dat het zweeft.
func _laagste_grond(r: Rect2i) -> float:
	var tm := w.tegel_m
	var x0 := r.position.x * tm + 0.3
	var x1 := r.end.x * tm - 0.3
	var z0 := r.position.y * tm + 0.3
	var z1 := r.end.y * tm - 0.3
	var h := terrein.hoogte_op((x0 + x1) * 0.5, (z0 + z1) * 0.5)
	for p in [Vector2(x0, z0), Vector2(x1, z0), Vector2(x0, z1), Vector2(x1, z1)]:
		h = minf(h, terrein.hoogte_op(p.x, p.y))
	return h


## Akker af: per tegel de kale grond en het gewas erop, dat in _process meegroeit met Wereld.akkers.
func _maak_akker(p: Plan) -> void:
	var r := p.afdruk()
	for c in range(r.position.x, r.end.x):
		for rij in range(r.position.y, r.end.y):
			var t := Vector2i(c, rij)
			var kaal := Natuur.instantie("akker_kaal")
			if kaal != null:
				kaal.position = _grond(t)
				kaal.rotation.y = p.draai * PI * 0.5
				ghost.get_parent().add_child(kaal)
			var rijp := Natuur.instantie("akker_rijp")
			if rijp != null:
				rijp.position = _grond(t)
				rijp.rotation.y = p.draai * PI * 0.5
				rijp.visible = false
				ghost.get_parent().add_child(rijp)
				_gewas[t] = rijp


## Omhulsel van `doel` in het assenstelsel van `wortel`.
static func _omhulsel_van(wortel: Node3D, doel: Node) -> AABB:
	var t := Transform3D.IDENTITY
	var n := doel.get_parent()
	while n != null and n != wortel:
		if n is Node3D:
			t = (n as Node3D).transform * t
		n = n.get_parent()
	return _omhulsel(doel, t)


static func _omhulsel(n: Node, t: Transform3D) -> AABB:
	var uit := AABB()
	var eerste := true
	var tt := t * (n as Node3D).transform if n is Node3D else t
	if n is MeshInstance3D and (n as MeshInstance3D).mesh != null:
		uit = tt * (n as MeshInstance3D).get_aabb()
		eerste = false
	for c in n.get_children():
		var b := _omhulsel(c, tt)
		if b.size == Vector3.ZERO:
			continue
		uit = b if eerste else uit.merge(b)
		eerste = false
	return uit




## Wijzerpositie bijhouden (ook boven knoppen en met touch-emulatie, waar viewport.get_mouse_position de echte muis geeft).
func _input(e: InputEvent) -> void:
	if e is InputEventMouse:
		_wijzer = (e as InputEventMouse).position


## Neemt in de bouwmodus de linkerknop over (indrukken = ghost, slepen = schuiven of een rij, loslaten = plaatsen),
## het wiel bij een draaibare soort (draaien in plaats van zoomen) en een rechterklik (stoppen; rechts slepen blijft
## de camera draaien). Werkt ook met een vinger (emulate_mouse_from_touch, standaard aan).
func _unhandled_input(e: InputEvent) -> void:
	if e is InputEventKey and e.pressed and not e.echo:
		for s: StringName in GEBOUWEN:
			if e.keycode == GEBOUWEN[s]["toets"]:
				kies(s, not (actief and soort == s))
				get_viewport().set_input_as_handled()
				return
		if actief and e.keycode == KEY_R:
			draai_verder()
			get_viewport().set_input_as_handled()
		elif actief and e.keycode == KEY_ESCAPE:
			zet_actief(false)
			get_viewport().set_input_as_handled()
		return
	if touch and actief:
		if e is InputEventScreenTouch or e is InputEventScreenDrag:
			_touch(e)
			return
		if e is InputEventMouseButton and (e as InputEventMouseButton).button_index == MOUSE_BUTTON_LEFT:
			get_viewport().set_input_as_handled()   # de geemuleerde muisklik van de vinger: Bestuur kiest of loopt niet
			return
	if not actief or not e is InputEventMouseButton:
		return
	var mb := e as InputEventMouseButton
	_wijzer = mb.position
	match mb.button_index:
		MOUSE_BUTTON_WHEEL_UP, MOUSE_BUTTON_WHEEL_DOWN:
			if soort in RIJ_SOORTEN:
				return                  # niets te draaien: het wiel blijft zoomen
			if mb.pressed:
				draai_verder(1 if mb.button_index == MOUSE_BUTTON_WHEEL_DOWN else -1)
			get_viewport().set_input_as_handled()
		MOUSE_BUTTON_LEFT:
			if mb.pressed:
				_drukt = true
				_sleep_start = bestuur.tegel_onder(mb.position)
				_rij_sleutel = []
			elif _drukt:
				_plaats(mb.position)
			get_viewport().set_input_as_handled()
		MOUSE_BUTTON_RIGHT:
			if mb.pressed:
				_rechts = true
				_rechts_start = mb.position
			elif _rechts:
				_rechts = false
				if mb.position.distance_to(_rechts_start) < KLIK_DREMPEL:
					zet_actief(false)


## Loslaten: de rij (weg/hek) of het ene plan onder de wijzer neerzetten. De modus blijft aan.
func _plaats(pos: Vector2) -> void:
	_drukt = false
	if soort in RIJ_SOORTEN:
		var eind := bestuur.tegel_onder(pos)
		if _sleep_start.x >= 0 and eind.x >= 0:
			BouwRij.zet(w, soort, BouwRij.route(w, soort, _sleep_start, eind))
		_sleep_start = Vector2i(-1, -1)
		_toon_rij([], [])
		return
	var p := _plan_onder(pos)
	if p != null:
		w.plan_zet(p)


# ---------------------------------------------------------------- touch (zie de kop)

## Bouwknop getikt: de ghost (of het begin van de rij) op de tegel midden in beeld.
func _touch_begin() -> void:
	var r := get_viewport().get_visible_rect().size if is_inside_tree() else Vector2.ZERO
	var t := bestuur.tegel_onder(r * 0.5)
	if t.x < 0 and bestuur.cam != null:
		var f: Vector3 = bestuur.cam.global_position
		if bestuur.cam.get("focus") is Vector3:
			f = bestuur.cam.get("focus")
		t = Vector2i(int(floor(f.x / w.tegel_m)), int(floor(f.z / w.tegel_m)))
	_t_tegel = t
	_t_eind = t
	_t_vinger = -1
	_t_sleutel = []


func _touch(e: InputEvent) -> void:
	var idx: int = e.index
	var pos: Vector2 = e.position
	if e is InputEventScreenTouch:
		if e.pressed:
			if _t_vinger < 0 and _t_tik.is_empty() and _pak(pos):
				_t_vinger = idx
				get_viewport().set_input_as_handled()     # de camera ziet deze vinger niet: geen pannen
			else:
				_t_tik[idx] = pos
		elif idx == _t_vinger:
			_t_vinger = -1
			get_viewport().set_input_as_handled()
		elif _t_tik.has(idx):
			var start: Vector2 = _t_tik[idx]
			_t_tik.erase(idx)
			# een tik (niet gesleept, geen tweede vinger: de camera zette dan touch_pant) zet de ghost of het begin daar
			if _t_tik.is_empty() and pos.distance_to(start) <= knop_h * 0.15 and bestuur.cam.get("touch_pant") != true:
				var t := bestuur.tegel_onder(pos)
				if t.x >= 0:
					_t_tegel = t
					_t_eind = t
		return
	if idx == _t_vinger:
		var t := bestuur.tegel_onder(pos)
		if t.x >= 0:
			if not soort in RIJ_SOORTEN:
				_t_tegel = t - _t_greep
			elif _t_einde == 1:
				_t_eind = t
			else:
				_t_tegel = t
		get_viewport().set_input_as_handled()


## Raakt de vinger op `pos` de ghost (gebouw: de voetafdruk plus een tegel rand, of binnen een knophoogte van het midden)
## of een einde van de rij? Dan houdt hij die vast (_t_greep, _t_einde).
func _pak(pos: Vector2) -> bool:
	var t := bestuur.tegel_onder(pos)
	if soort in RIJ_SOORTEN:
		for einde in [1, 0]:          # het eind eerst: bij een rij van een tegel trekt slepen hem uit
			var et: Vector2i = _t_eind if einde == 1 else _t_tegel
			if et.x < 0:
				continue
			var bij := t.x >= 0 and maxi(absi(t.x - et.x), absi(t.y - et.y)) <= 1
			if bij or _scherm_af(_grond(et), pos) < knop_h * 0.6:
				_t_einde = einde
				return true
		return false
	var p := _plan_op(_t_tegel)
	if p == null:
		return false
	if (t.x >= 0 and p.afdruk().grow(1).has_point(t)) or _scherm_af(_midden(p), pos) < knop_h * 0.6:
		_t_greep = t - _t_tegel if t.x >= 0 else Vector2i.ZERO
		return true
	return false


func _scherm_af(p: Vector3, pos: Vector2) -> float:
	var cam := bestuur.cam
	if cam == null or cam.is_position_behind(p):
		return INF
	return cam.unproject_position(p).distance_to(pos)


## Touch: de route van begin naar eind (opnieuw als er iets veranderd is) met de status per tegel.
func _touch_rij() -> void:
	var sleutel := [soort, _t_tegel, _t_eind, w.plannen.size(), w.kas]
	if sleutel == _t_sleutel:
		return
	_t_sleutel = sleutel
	_t_rij = BouwRij.route(w, soort, _t_tegel, _t_eind) if _t_tegel.x >= 0 and _t_eind.x >= 0 else ([] as Array[Vector2i])
	_t_st = BouwRij.statussen(w, soort, _t_rij)


## Kan Bouwen nu iets neerzetten?
func kan_bevestigen() -> bool:
	if not actief:
		return false
	if soort in RIJ_SOORTEN:
		_touch_rij()
		return BouwRij.KAN in _t_st
	var p := _plan_op(_t_tegel)
	return p != null and w.kan_bouwen(p) and w.kan_betalen(p.soort)


## Bouwen (touch): het plan of de rij neerzetten. De modus blijft aan; bij een rij wordt het eind het nieuwe begin.
func bevestig() -> void:
	if not kan_bevestigen():
		return
	if soort in RIJ_SOORTEN:
		BouwRij.zet(w, soort, _t_rij)
		_t_tegel = _t_eind
		_t_sleutel = []
	else:
		w.plan_zet(_plan_op(_t_tegel))


func _toon_touch() -> void:
	if soort in RIJ_SOORTEN:
		ghost.visible = false
		_touch_rij()
		if _t_sleutel != _t_getoond:
			_t_getoond = _t_sleutel
			_toon_rij(_t_rij, _t_st)
		knop_bouw.disabled = not BouwRij.KAN in _t_st
		return
	knop_bouw.disabled = not _toon_ghost(_plan_op(_t_tegel))
