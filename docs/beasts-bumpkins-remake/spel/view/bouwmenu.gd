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
## Menu = variant A uit lokaal/concept/bouwmenu_schets.html (besluit gebruiker 2026-10-31): vier tabbladen (Wonen,
## Voedsel, Gilden, Wegen; CATEGORIE) met per gebouw een tegel: ikoon (ikonen/bouw/<soort>.png, gerenderd uit de eigen
## glb door tools/maak_ikonen.gd) en de prijs eronder. Op slot (Wereld.ONTGRENDEL / VANAF_MISSIE) = grijs met slotje en
## de reden ("na Loods", "missie 3"); te duur = prijs rood. Tikken op zo'n tegel geeft een melding (signaal `melding`,
## main.gd -> Hud.toon_melding) in plaats van de bouwmodus. Paneelmodus (touch, of staand op de pc): hamerknop
## rechtsonder (duimzone) opent het paneel onderin, 3 tegels breed staand, 4 liggend; een keuze sluit het, daarna de
## ghost en de balk Draai/Bouwen/Annuleer; weg/hek: Bouwen toont aantal x prijs. Telefoon: alleen ikonen en prijs, geen
## kleine tekst (de reden van het slot wel). Pc liggend: het paneel staat altijd open als een rij onderin het midden,
## met naam en lettertoets per tegel; hint, Draai en Stop erboven. `_indeling` loopt bij elke size_changed.

const GROND_Y := 0.25
const KLIK_DREMPEL := 6.0
## Per bouwsoort (voetafdruk in Wereld.BOUWSOORTEN): knoptekst, toets, glb, hoogte van de kist.
const GEBOUWEN := {
	&"hut": {"tekst": "Hut", "toets": KEY_B, "glb": "res://assets/peasant_hut_rt.glb", "hoogte": 2.4},
	&"gereedschapsloods": {"tekst": "Loods", "toets": KEY_L, "glb": "res://assets/gereedschapsloods_rt.glb", "hoogte": 2.4},
	&"kippenhok": {"tekst": "Kippenhok", "toets": KEY_H, "glb": "res://assets/kippenhok_rt.glb", "hoogte": 1.2},
	&"molen": {"tekst": "Molen", "toets": KEY_Z, "glb": "res://assets/molen_rt.glb", "hoogte": 3.0},
	&"melkerij": {"tekst": "Melkerij", "toets": KEY_J, "glb": "res://assets/melkerij_boerderij_rt.glb", "hoogte": 2.6},
	&"akker": {"tekst": "Akker", "toets": KEY_G, "glb": "", "hoogte": 0.3},   # geen glb: per tegel akker_kaal + akker_rijp
	&"weg": {"tekst": "Weg", "toets": KEY_T, "glb": "", "hoogte": 0.15},      # af = padtegel, view/wegen.gd (slepen = rij)
	&"hek": {"tekst": "Hek", "toets": KEY_F, "glb": "", "hoogte": 1.1},       # palen + segmenten naar de buren (slepen = rij)
	&"poort": {"tekst": "Poort", "toets": KEY_P, "glb": "", "hoogte": 1.3},   # hek_poort.glb, vleugel draait open (klik)
	# missie 3 (Wereld.VANAF_MISSIE): put = bron.glb (well, 4,9 x 4,9 m, deur en trap op +Z, tuit op +X); gilde = voetvolkgilde_rt.glb (zonder glb het
	# blok uit Props). De gildedeur zit in de glb op -X, Plan.DEUREN wil +Z: `draai` = extra hoek om Y bovenop
	# Plan.draai, alleen voor het beeld (afdruk en deur blijven die van de sim).
	&"put": {"tekst": "Put", "toets": KEY_U, "glb": "res://assets/bron.glb", "hoogte": 2.0},
	&"voetvolkgilde": {"tekst": "Gilde", "toets": KEY_V, "glb": "res://assets/voetvolkgilde_rt.glb", "hoogte": 3.0,
		"placeholder": "gilde", "draai": PI * 0.5},
}
const RIJ_SOORTEN := [&"weg", &"hek"]     ## slepen = een rij (BouwRij); draaien doet er niet toe
const KNOP_H := 44.0                      ## knophoogte in px: met een vinger te raken
## Tabbladen van het paneel (schets variant A): naam en het ikoon van het tabblad (touch: alleen het ikoon).
const CATEGORIEEN := [{"k": "wonen", "n": "Wonen", "ik": &"hut"}, {"k": "voedsel", "n": "Voedsel", "ik": &"molen"},
	{"k": "gilden", "n": "Gilden", "ik": &"gereedschapsloods"}, {"k": "wegen", "n": "Wegen", "ik": &"weg"}]
## Tabblad per soort, in de volgorde van de tegels (schets: wonen hut, put; voedsel kippenhok, akker, molen, melkerij;
## gilden loods, voetvolkgilde; wegen weg, hek, poort).
const CATEGORIE := {&"hut": "wonen", &"put": "wonen", &"kippenhok": "voedsel", &"akker": "voedsel", &"molen": "voedsel",
	&"melkerij": "voedsel", &"gereedschapsloods": "gilden", &"voetvolkgilde": "gilden", &"weg": "wegen", &"hek": "wegen",
	&"poort": "wegen"}
const IKONEN := "res://ikonen/bouw/"      ## <soort>.png, tools/maak_ikonen.gd
const PC_TEGEL := Vector2(112, 132)       ## pc: tegel bij 1080 px hoogte (schaalt mee)
const KLEUR_KAN := Color(0.3, 1.0, 0.3, 0.45)
const KLEUR_NIET := Color(1.0, 0.1, 0.1, 0.55)
const KLEUR_BESTAAT := Color(0.85, 0.85, 0.85, 0.25)
const POORT_OPEN_RAD := deg_to_rad(100.0)
const WIEKEN_RAD_S := 0.9      ## draaisnelheid van de molenwieken

const STAPELS := ["zaagbok", "steenhoop"]   ## bouwplaats (besluit gebruiker, origineel woodpile + rockpile); = Plan.STAPELS
const STAPEL_TERUG := {"zaagbok": "houtstapel"}   ## als de eerste ontbreekt
const STAPEL_RESTANT := 0.35   ## schaal van een stapel vlak voor klaar
const VOLWASSENE_M := 1.37     ## de man, langste volwassene (bumpkin_basis.py; vrouw en ouderen 1,31-1,33)
const DEUR_M := VOLWASSENE_M * 1.15   ## gewenste hoogte van de voordeur: iets groter dan een volwassene

var w: Wereld
var bestuur: Bestuur
var actief := false
var soort: StringName = &"hut"
var draai := 0
var knoppen := {}          ## soort -> Button
var ghost: MeshInstance3D  ## de kist: terugval zolang de glb laadt, en voor akker, weg, hek, poort
var _gmodel: Node3D         ## ghost van het gebouw zelf: een instantie van de af-glb (null = nog de kist)
var _gmodel_soort: StringName = &""
var _gmodel_sleutel := []   ## [tegel, draai] waarop _gmodel nu staat
var _gsurf: Array = []      ## [MeshInstance3D, surface, mat_kan, mat_niet] per oppervlak van _gmodel
var _gkan := -1             ## kleur van _gmodel nu: 1 kan, 0 niet, -1 nog niet gezet
var _pijl: MeshInstance3D   ## deurpijl op de grond: op de deurtegel (Plan.deur_tegel), wijst naar de deur
var _pad_mi: MeshInstance3D ## deurweg-ghost: de keienweg van de deur naar het pad (Wereld.weg_route), zie _toon_pad
var _pad_sleutel := []      ## [soort, tegel, draai, _pad_rev, kas]: alleen bij verandering opnieuw (BFS, reden)
var _pad_rev := 0           ## +1 bij wegen_veranderd, plan_gezet en plan_klaar: de route kan anders zijn
var pad_route: Array[Vector2i] = []   ## de getoonde deurweg (deurtegel eerst); leeg = geen (of geen deur)
var pad_nieuw := 0          ## nieuwe padtegels daarin: elk weg_per_tegel
var _pad_reden := ""        ## Wereld.bouw_reden van de ghost bij _pad_sleutel
var prijs_tekst := ""       ## "Hut 300 + pad 4 x 20 = 380" (of "Hut 300"), in de hint
var _pad_mat: Array[ShaderMaterial] = []   ## deurweg-ghost [niet, kan]: shaders/weg_ghost.gdshader
static var _gmat := {}      ## bronmateriaal -> [kan, niet]: doorzichtige getinte kopieen (texturen gedeeld)
var _proef_tegel := Vector2i(-1, -1)   ## alleen --proef=bouw op de pc: de ghost staat hier in plaats van onder de wijzer
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
var _hint_basis := ""        ## hinttekst van de modus; _toon_ghost zet er de reden achter als de ghost rood is
static var touch := OS.has_feature("mobile") or "--touch" in OS.get_cmdline_user_args()   ## touch-bouwen (zie boven)
var knop_h := KNOP_H        ## touch: >= 48 dp (bouw())
var kolom: VBoxContainer   ## hint (en op de pc Draai en Stop): pc liggend boven het paneel, anders onderin
var rij2: HBoxContainer    ## hint (en op de pc Draai en Stop)
var balk: HBoxContainer    ## touch: Draai, Bouwen, Annuleer
var paneel: PanelContainer ## tabbladen + tegels (pc liggend altijd open onderin, anders achter de hamerknop)
var tabs: HBoxContainer
var tab_knoppen := {}      ## categorie -> Button
var knop_dicht: Button     ## paneelmodus: x sluit het paneel
var rooster: GridContainer ## de tegels van het open tabblad
var tab := "wonen"
var knop_hamer: Button     ## paneelmodus: rechtsonder, opent het paneel
var paneel_open := false   ## paneelmodus: paneel open
var _staand := false
signal melding(tekst: String)   ## op slot of te duur gekozen: Hud.toon_melding (main.gd)
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
	_pijl = _maak_pijl()
	_pijl.visible = false
	parent3d.add_child(_pijl)
	_pad_mi = MeshInstance3D.new()
	_pad_mi.name = "DeurwegVoorbeeld"
	_pad_mi.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	_pad_mat = [_weg_ghost_mat(false), _weg_ghost_mat(true)]
	_pad_mi.material_override = _pad_mat[1]
	_pad_mi.visible = false
	parent3d.add_child(_pad_mi)
	var nieuw_pad := func(_a = null) -> void: _pad_rev += 1
	w.wegen_veranderd.connect(nieuw_pad)
	w.plan_gezet.connect(nieuw_pad)
	w.plan_klaar.connect(nieuw_pad)
	w.plan_gezet.connect(_toon_plan)
	w.plan_klaar.connect(_plan_klaar)
	_hekken = Node3D.new()
	_hekken.name = "Hekken"
	parent3d.add_child(_hekken)

	if touch:
		knop_h = touch_knop_h()
	var laag := CanvasLayer.new()
	add_child(laag)
	# hint, Draai en Stop: pc liggend boven het paneel, anders onderin boven de touchbalk (_indeling)
	kolom = VBoxContainer.new()
	kolom.add_theme_constant_override("separation", 8)
	kolom.mouse_filter = Control.MOUSE_FILTER_IGNORE
	laag.add_child(kolom)
	rij2 = HBoxContainer.new()
	rij2.add_theme_constant_override("separation", 8)
	rij2.alignment = BoxContainer.ALIGNMENT_CENTER
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
	_bouw_paneel(laag)
	knop_hamer = HamerKnop.new()
	knop_hamer.name = "Hamer"
	knop_hamer.tooltip_text = "bouwen"
	knop_hamer.pressed.connect(func() -> void: zet_paneel(not paneel_open))
	laag.add_child(knop_hamer)
	zet_actief(false)
	get_viewport().size_changed.connect(_indeling)
	_indeling()
	match Scherm.optie("proef"):     # alleen voor frames (view/scherm.gd)
		"bouw": _proef_bouw.call_deferred()
		"lade", "paneel": _proef_paneel.call_deferred()
		"rij": _proef_rij.call_deferred()


## Het paneel: tabbladen en een rooster met een tegel per soort (in CATEGORIE-volgorde; alleen die van het open tabblad
## zijn zichtbaar).
func _bouw_paneel(laag: CanvasLayer) -> void:
	paneel = PanelContainer.new()
	paneel.name = "Paneel"
	paneel.mouse_filter = Control.MOUSE_FILTER_STOP      # een klik op de achtergrond is geen loopbevel
	var sb := StyleBoxFlat.new()
	sb.bg_color = Color(0.094, 0.082, 0.067, 0.92)
	sb.set_corner_radius_all(10)
	sb.set_content_margin_all(8)
	sb.shadow_color = Color(0, 0, 0, 0.45)
	sb.shadow_size = 6
	paneel.add_theme_stylebox_override("panel", sb)
	laag.add_child(paneel)
	var vb := VBoxContainer.new()
	vb.add_theme_constant_override("separation", 8)
	vb.mouse_filter = Control.MOUSE_FILTER_IGNORE
	paneel.add_child(vb)
	tabs = HBoxContainer.new()
	tabs.add_theme_constant_override("separation", 6)
	tabs.mouse_filter = Control.MOUSE_FILTER_IGNORE
	vb.add_child(tabs)
	for c: Dictionary in CATEGORIEEN:
		var t := Button.new()
		t.toggle_mode = true
		t.focus_mode = Control.FOCUS_NONE
		t.size_flags_horizontal = Control.SIZE_EXPAND_FILL
		if touch:       # geen kleine tekst op de telefoon: alleen het ikoon
			t.icon = _ikoon_van(c["ik"])
			t.expand_icon = true
			t.icon_alignment = HORIZONTAL_ALIGNMENT_CENTER
		else:
			t.text = c["n"]
		t.tooltip_text = c["n"]
		_tab_stijl(t)
		t.pressed.connect(zet_tab.bind(String(c["k"])))
		tabs.add_child(t)
		tab_knoppen[c["k"]] = t
	knop_dicht = Button.new()
	knop_dicht.focus_mode = Control.FOCUS_NONE
	knop_dicht.icon = _ikoon(false)
	knop_dicht.icon_alignment = HORIZONTAL_ALIGNMENT_CENTER
	knop_dicht.tooltip_text = "dicht"
	_tab_stijl(knop_dicht)
	knop_dicht.pressed.connect(func() -> void: zet_paneel(false))
	tabs.add_child(knop_dicht)
	rooster = GridContainer.new()
	rooster.add_theme_constant_override("h_separation", 8)
	rooster.add_theme_constant_override("v_separation", 8)
	rooster.mouse_filter = Control.MOUSE_FILTER_IGNORE
	rooster.size_flags_horizontal = Control.SIZE_SHRINK_CENTER
	vb.add_child(rooster)
	for s: StringName in CATEGORIE:
		var g: Dictionary = GEBOUWEN[s]
		var tg := BouwTegel.new()
		tg.name = "Tegel_" + String(s)
		tg.soort = s
		tg.ikoon = _ikoon_van(s)
		tg.prijs = w.prijs(s)
		tg.naam = g["tekst"]
		tg.pc = not touch
		tg.toets = OS.get_keycode_string(g["toets"])
		tg.tooltip_text = "%s %d (%s)" % [g["tekst"], tg.prijs, tg.toets] if not touch else ""
		tg.pressed.connect(kies_tegel.bind(s))
		rooster.add_child(tg)
		knoppen[s] = tg
	_werk_tegels()


func _tab_stijl(t: Button) -> void:
	for st in ["normal", "hover", "pressed", "hover_pressed"]:
		var sb := StyleBoxFlat.new()
		var aan: bool = st.contains("pressed")
		sb.bg_color = Color(0.35, 0.29, 0.16) if aan else Color(1, 1, 1, 0.13 if st == "hover" else 0.07)
		if aan:
			sb.border_color = Color(0.95, 0.76, 0.31)
			sb.border_width_bottom = 3
		sb.set_corner_radius_all(6)
		sb.set_content_margin_all(4)
		sb.content_margin_left = 10
		sb.content_margin_right = 10
		t.add_theme_stylebox_override(st, sb)
	t.add_theme_font_size_override("font_size", 16)


## Bouwmenu-ikoon van een soort (ikonen/bouw/<soort>.png). Niet geimporteerd (headless zonder --import): de png
## rechtstreeks; ontbreekt hij: null (de tegel tekent dan een kist).
static var _ikonen := {}


static func _ikoon_van(s: StringName) -> Texture2D:
	if _ikonen.has(s):
		return _ikonen[s]
	var pad := IKONEN + String(s) + ".png"
	var t: Texture2D = null
	if ResourceLoader.exists(pad):
		t = load(pad) as Texture2D
	if t == null and FileAccess.file_exists(pad):
		var img := Image.load_from_file(ProjectSettings.globalize_path(pad))
		if img != null and not img.is_empty():
			t = ImageTexture.create_from_image(img)
	_ikonen[s] = t
	return t


## Paneelmodus: touch, of staand op de pc. Anders (pc liggend) staat het paneel altijd open als een rij onderin.
func paneel_modus() -> bool:
	return touch or _staand


## 48 dp met een marge; de Motorola (~400 dpi) geeft ~130 px.
static func touch_knop_h() -> float:
	return clampf(52.0 * DisplayServer.screen_get_dpi() / 160.0, 110.0, 180.0)


## Legt het menu neer voor de huidige viewport: pc liggend de rij onderin met hint/Draai/Stop erboven; in de
## paneelmodus de hamer rechtsonder, het paneel onderin (3 breed staand, 4 liggend) en de touchbalk onderin het midden.
func _indeling() -> void:
	var vp := get_viewport().get_visible_rect().size
	_staand = Scherm.staand(vp)
	var pm := paneel_modus()
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
	# tegelmaat
	var gap := 8.0
	var tb: Vector2
	var tab_h: float
	if pm:
		var kol := 3 if _staand else 4
		var b := floorf((vp.x - 24.0 - 16.0 - (kol - 1) * gap) / kol) if _staand else roundf(knop_h * 2.0)
		tb = Vector2(b, roundf(b * 1.12))
		tab_h = maxf(knop_h * 0.9, 44.0) if touch else maxf(44.0, b * 0.32)
	else:
		var k := clampf(vp.y / 1080.0, 0.8, 1.4)
		tb = (PC_TEGEL * k).round()
		tab_h = roundf(34.0 * k)
	for s in knoppen:
		(knoppen[s] as Control).custom_minimum_size = tb
	for t: Button in tab_knoppen.values() + [knop_dicht]:
		t.custom_minimum_size = Vector2(tab_h * (1.0 if t == knop_dicht else 1.6), tab_h)
		t.add_theme_font_size_override("font_size", int(tab_h * 0.45))
	knop_dicht.visible = pm
	# hamer: rechtsonder, duimzone
	var hk := roundf(maxf(knop_h * 1.4, vp.x * 0.16 if _staand else 0.0))
	knop_hamer.custom_minimum_size = Vector2(hk, hk)
	knop_hamer.size = knop_hamer.custom_minimum_size
	var hm := roundf(maxf(12.0, hk * 0.2))
	knop_hamer.position = vp - knop_hamer.size - Vector2(hm, hm)
	# hint/Draai/Stop
	if pm:
		kolom.set_anchors_preset(Control.PRESET_BOTTOM_WIDE)
		kolom.offset_left = 12
		kolom.offset_right = -12
		hint.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
		hint.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
		hint.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	else:
		kolom.set_anchors_preset(Control.PRESET_CENTER_BOTTOM)
		kolom.offset_left = 0
		kolom.offset_right = 0
		hint.autowrap_mode = TextServer.AUTOWRAP_OFF
		hint.horizontal_alignment = HORIZONTAL_ALIGNMENT_LEFT
		hint.size_flags_horizontal = Control.SIZE_FILL
	kolom.grow_horizontal = Control.GROW_DIRECTION_BOTH
	kolom.grow_vertical = Control.GROW_DIRECTION_BEGIN
	zet_tab(tab)
	if pm:
		kolom.offset_bottom = -onder
		kolom.offset_top = -onder
	else:
		var top := paneel.position.y - 8.0
		kolom.offset_bottom = top - vp.y
		kolom.offset_top = top - vp.y
	_zichtbaar()


## Paneelmodus: het paneel open of dicht (hamerknop, x; een keuze sluit het). Pc liggend is het altijd open.
func zet_paneel(open: bool) -> void:
	paneel_open = open
	if open:
		zet_tab(tab)
	_zichtbaar()


## Open tabblad `k`: alleen zijn tegels; pc liggend een rij, anders 3 (staand) of 4 breed. Het paneel krimpt mee en
## blijft onderin het midden.
func zet_tab(k: String) -> void:
	tab = k
	var n := 0
	for s in knoppen:
		var hier: bool = CATEGORIE[s] == k
		(knoppen[s] as Control).visible = hier
		n += int(hier)
	for c in tab_knoppen:
		(tab_knoppen[c] as Button).set_pressed_no_signal(c == k)
	var pm := paneel_modus()
	rooster.columns = maxi(1, (3 if _staand else 4) if pm else n)
	if not is_inside_tree():
		return
	var vp := get_viewport().get_visible_rect().size
	paneel.reset_size()
	var marge := 0 if pm and _staand else 12
	paneel.set_anchors_and_offsets_preset(Control.PRESET_CENTER_BOTTOM, Control.PRESET_MODE_MINSIZE, marge)
	paneel.grow_horizontal = Control.GROW_DIRECTION_BOTH
	paneel.grow_vertical = Control.GROW_DIRECTION_BEGIN
	if pm and _staand:      # staand: over de hele breedte
		paneel.set_anchors_and_offsets_preset(Control.PRESET_BOTTOM_WIDE, Control.PRESET_MODE_MINSIZE, 0)
		paneel.offset_left = 0
		paneel.offset_right = 0
	paneel.position.y = vp.y - paneel.get_combined_minimum_size().y - marge


func _zichtbaar() -> void:
	var pm := paneel_modus()
	paneel.visible = paneel_open if pm else true
	knop_hamer.visible = pm and not actief and not paneel_open
	knop_hamer.set_pressed_no_signal(paneel_open)


## Een tegel gekozen (klik, tik of lettertoets): op slot of te duur = een melding; anders de bouwmodus (een keer op
## de gekozen soort = uit).
func kies_tegel(s: StringName) -> void:
	if actief and soort == s:
		zet_actief(false)
		return
	var st := tegel_staat(s)
	var g: String = GEBOUWEN[s]["tekst"]
	if st[0] == BouwTegel.SLOT:
		var na: StringName = Wereld.ONTGRENDEL.get(s, &"")
		melding.emit(("%s: eerst een %s bouwen" % [g, GEBOUWEN[na]["tekst"]]) if na != &"" and not Wereld.VANAF_MISSIE.has(s) \
				else ("%s: pas vanaf missie %d" % [g, int(Wereld.VANAF_MISSIE.get(s, 0))]))
		return
	if st[0] == BouwTegel.DUUR:
		melding.emit("%s: te weinig goud, nog %d" % [g, w.prijs(s) - w.kas])
		return
	kies(s)


## [staat, reden] van een tegel: BouwTegel.SLOT met "na Loods" / "missie 3", DUUR (kas < prijs), of KAN.
func tegel_staat(s: StringName) -> Array:
	if not w.ontgrendeld(s):
		if Wereld.VANAF_MISSIE.has(s) and w.missie_nr < int(Wereld.VANAF_MISSIE[s]):
			return [BouwTegel.SLOT, "missie %d" % int(Wereld.VANAF_MISSIE[s])]
		var na: StringName = Wereld.ONTGRENDEL.get(s, &"")
		return [BouwTegel.SLOT, ("na " + String(GEBOUWEN[na]["tekst"])) if na != &"" else ""]
	if not w.kan_betalen(s):
		return [BouwTegel.DUUR, ""]
	return [BouwTegel.KAN, ""]


func _werk_tegels() -> void:
	for s in knoppen:
		var st := tegel_staat(s)
		(knoppen[s] as BouwTegel).zet(st[0], st[1], actief and soort == s)


## `--proef=rij` (frames): een weg slepen van een vrije tegel bij het kampvuur 7 tegels naar rechts en 3 omlaag (pc: de
## knop blijft ingedrukt met de wijzer op het eind; touch: begin en eind gezet, Bouwen toont aantal x prijs).
func _proef_rij() -> void:
	w.kas = maxi(w.kas, 100000)
	kies(&"weg")
	var a := w.kampvuur + Vector2i(-3, 4)
	var e := a + Vector2i(7, 3)
	if bestuur.cam != null and bestuur.cam.has_method("spring_naar"):
		bestuur.cam.spring_naar(_grond(a).lerp(_grond(e), 0.5))
	if touch:
		_t_tegel = a
		_t_eind = e
		return
	_drukt = true
	_sleep_start = a
	get_tree().process_frame.connect(func() -> void:
		if actief and _drukt and bestuur.cam != null:
			_wijzer = bestuur.cam.unproject_position(_grond(e)))


## `--proef=paneel` (frames): het paneel open; met `--proef_tab=` een ander tabblad, `--proef_kas=` een andere kas.
func _proef_paneel() -> void:
	if Scherm.optie("proef_kas") != "":
		w.kas = int(Scherm.optie("proef_kas"))
	if Scherm.optie("proef_tab") != "":
		tab = Scherm.optie("proef_tab")
	zet_paneel(true)
	zet_tab(tab)


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
	knop_bouw.clip_text = true          # "Bouwen 12 x 20" mag de balk niet breder maken
	knop_bouw.text_overrun_behavior = TextServer.OVERRUN_TRIM_ELLIPSIS
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
		_wis_gmodel()
	if aan and not soort in RIJ_SOORTEN:
		_scene(GEBOUWEN[soort]["glb"])     # de glb alvast in de achtergrond; tot hij er is de kist
	if aan and not paneel_modus() and CATEGORIE.get(soort, tab) != tab:
		zet_tab(CATEGORIE[soort])     # pc: de lettertoets van een ander tabblad opent dat tabblad
	if aan and paneel_open:
		paneel_open = false
	zet_actief(aan)
	if aan and touch:
		_touch_begin()


func zet_actief(aan: bool) -> void:
	actief = aan
	ghost.visible = aan
	if _gmodel != null:
		_gmodel.visible = false
	if _pijl != null:
		_pijl.visible = false
	if _pad_mi != null:
		_pad_mi.visible = false
	_pad_sleutel = []
	_drukt = false
	_sleep_start = Vector2i(-1, -1)
	_t_vinger = -1
	_t_tik.clear()
	_t_sleutel = []
	_t_getoond = []
	_toon_rij([], [])
	if paneel != null:
		_werk_tegels()
		_zichtbaar()
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
		_hint_basis = hint.text
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
	if paneel != null and paneel.visible:
		_werk_tegels()
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
		_pijl.visible = false
		_pad_mi.visible = false
		var eind := bestuur.tegel_onder(_wijzer)
		if eind.x < 0:
			return
		var sleutel := [_sleep_start, eind, w.plannen.size(), w.kas]
		if sleutel != _rij_sleutel:       # A* alleen als er iets veranderd is
			_rij_sleutel = sleutel
			_rij = BouwRij.route(w, soort, _sleep_start, eind)
			var st := BouwRij.statussen(w, soort, _rij)
			_toon_rij(_rij, st)
			var n := st.count(BouwRij.KAN)     # aantal x prijs (besluit gebruiker 2026-10-31)
			hint.text = "%s: %d x %d = %d   loslaten = plaatsen" % [GEBOUWEN[soort]["tekst"], n, w.prijs(soort), n * w.prijs(soort)]
		return
	_toon_ghost(_plan_op(_proef_tegel) if _proef_tegel.x >= 0 else _plan_onder(_wijzer))


## De ghost op plan `p` (groen = kan, rood = kan niet); geeft of het kan. Null = geen ghost.
## Gebouwen met een glb tonen het gebouw zelf, doorzichtig en groen of rood getint, precies zoals _plan_klaar het
## neerzet (_zet_op_plek, zelfde draai), plus een pijl op de deurtegel; zolang de glb laadt de kist.
func _toon_ghost(p: Plan) -> bool:
	var gm := _ghost_model()
	ghost.visible = p != null and gm == null
	if gm != null:
		gm.visible = p != null
	_pijl.visible = p != null and Plan.DEUREN.has(soort)
	if p == null:
		_pad_mi.visible = false
		return false
	ghost.position = _midden(p)
	if soort == &"weg":
		ghost.position.y = _grond(p.tegel).y + _hoogte(soort) * 0.5
	ghost.rotation.y = draai * PI * 0.5
	var sleutel := [soort, p.tegel, p.draai, _pad_rev, w.kas]
	var nieuw := sleutel != _pad_sleutel
	if nieuw:            # BFS en reden alleen als ghosttegel, draai, wegen, plannen of kas veranderen
		_pad_sleutel = sleutel
		_pad_reden = w.bouw_reden(p)     # te ver van het dorp, geen pad (besluit gebruiker 2026-10-31), of kan hier niet
		pad_route = w.weg_route(p.deur_tegel(), p) if Plan.DEUREN.has(soort) \
				and (_pad_reden == "" or _pad_reden == Wereld.REDEN_TE_VER) else ([] as Array[Vector2i])
		pad_nieuw = w.weg_nieuw(pad_route)
		var pp := w.prijs(soort)
		var wpt := int(w.spel.get("weg_per_tegel", 0))
		prijs_tekst = "%s %d" % [GEBOUWEN[soort]["tekst"], pp] if pad_nieuw == 0 \
				else "%s %d + pad %d x %d = %d" % [GEBOUWEN[soort]["tekst"], pp, pad_nieuw, wpt, pp + pad_nieuw * wpt]
	var reden := _pad_reden
	if reden == "" and w.kas < w.prijs(soort) + pad_nieuw * int(w.spel.get("weg_per_tegel", 0)):
		reden = "Te duur"
	var kan := reden == ""
	if soort in RIJ_SOORTEN:
		kan = BouwRij.statussen(w, soort, [p.tegel])[0] == BouwRij.KAN
		if kan:
			reden = ""
	if nieuw:
		_toon_pad(kan, p)
	elif _pad_mi.visible and _pad_mi.material_override != _pad_mat[int(kan)]:
		_pad_mi.material_override = _pad_mat[int(kan)]     # zelfde route, andere kleur (kas veranderd)
	if hint != null and _hint_basis != "":
		var t := _hint_basis
		if not soort in RIJ_SOORTEN:
			t += ("\n" if touch else "   ") + prijs_tekst
		hint.text = t if kan or reden == "" else "%s   (%s)" % [t, reden]
	(ghost.material_override as StandardMaterial3D).albedo_color = KLEUR_KAN if kan else KLEUR_NIET
	if gm != null:
		var sl := [p.tegel, p.draai]
		if sl != _gmodel_sleutel:
			_gmodel_sleutel = sl
			_zet_op_plek(gm, p)
		if _gkan != int(kan):
			_gkan = int(kan)
			for e: Array in _gsurf:
				(e[0] as MeshInstance3D).set_surface_override_material(e[1], e[2] if kan else e[3])
	if _pijl.visible:
		var dt := p.deur_tegel()
		var dr := -p.deur_richting()        # van de deurtegel naar de deur: hier gaan ze naar binnen
		_pijl.position = _grond(dt) + Vector3(0, 0.06, 0)
		_pijl.rotation.y = atan2(-float(dr.y), float(dr.x))
		(_pijl.material_override as StandardMaterial3D).albedo_color = PIJL_KAN if kan else PIJL_NIET
	return kan


const PAD_BOVEN := 0.05     ## m boven de grond: net boven de echte weg (Wegen.BOVEN), zodat de aansluiting erop ligt

## De deurweg-ghost (gebruiker 2026-10-31: in het origineel zie je bij het plaatsen al de weg naar de deur; "waarom niet
## als ghost road zoals het gebouw?"): de nieuwe tegels van pad_route als keienweg, met hetzelfde net als de echte weg
## (Wegen.net: achthoek per tegel, stroken naar de buren, schuin alleen zonder rechte tussenburen) alsof de route er al
## ligt, zodat hij aansluit op het bestaande pad zoals de weg straks; plus de stoep naar de deur (Wegen.stoep).
## Doorzichtig en getint als de gebouw-ghost (_weg_ghost_mat). Alleen bij een nieuwe sleutel, dus geen mesh per frame.
func _toon_pad(kan: bool, p: Plan) -> void:
	_pad_mi.visible = not pad_route.is_empty()
	if pad_route.is_empty():
		return
	var pad_i := w.raster.namen.find("pad")
	var route := {}
	var tegels: Array[Vector2i] = []
	for t in pad_route:
		route[t] = true
		if not Wegen._weg(w, t.x, t.y, pad_i):
			tegels.append(t)
	var is_weg := func(t: Vector2i) -> bool: return route.has(t) or Wegen._weg(w, t.x, t.y, pad_i)
	var nieuw := func(t: Vector2i) -> bool: return route.has(t) and not Wegen._weg(w, t.x, t.y, pad_i)
	var grond := func(x: float, z: float) -> Vector3:
		return Vector3(x, (terrein.hoogte_op(x, z) if terrein != null else GROND_Y) + PAD_BOVEN, z)
	var st := SurfaceTool.new()
	st.begin(Mesh.PRIMITIVE_TRIANGLES)
	Wegen.net(st, tegels, is_weg, nieuw, w.tegel_m, grond)
	Wegen.stoep(st, p, is_weg, w.tegel_m, grond)
	st.generate_normals()
	_pad_mi.mesh = st.commit()
	_pad_mi.material_override = _pad_mat[int(kan)]


## Het materiaal van de deurweg-ghost: de keienweg (shaders/weg.gdshaderinc) met de tint, alfa en het eigen licht van
## _ghost_mat, zodat weg en gebouw een ghost zijn.
static func _weg_ghost_mat(kan: bool) -> ShaderMaterial:
	var m := ShaderMaterial.new()
	m.shader = load("res://shaders/weg_ghost.gdshader")
	m.set_shader_parameter("ghost_tint", GHOST_TINT_KAN if kan else GHOST_TINT_NIET)
	m.set_shader_parameter("ghost_alfa", GHOST_ALFA)
	m.set_shader_parameter("ghost_licht", GHOST_LICHT_KAN if kan else GHOST_LICHT_NIET)
	return m


## De model-ghost van de huidige soort: een instantie van de af-glb met doorzichtige getinte materialen, zonder
## schaduw en zonder botsing. Een instantie tegelijk, opnieuw bij een andere soort; de PackedScene en de materialen
## komen uit de caches (_scenes, _gmat). Null zolang de glb nog laadt, of als de soort er geen heeft.
func _ghost_model() -> Node3D:
	if _gmodel != null and _gmodel_soort == soort:
		return _gmodel
	if soort in RIJ_SOORTEN:
		return null
	var ps := _scene(GEBOUWEN[soort]["glb"])
	if ps == null:
		return null
	_wis_gmodel()
	_info(soort, ps)
	var n: Node3D = ps.instantiate()
	_gmodel_soort = soort
	_gmodel = n
	_gkan = -1
	_gmodel_sleutel = []
	_ontbots(n)
	var lijst: Array = []
	Natuur._meshes(n, lijst)
	for mi: MeshInstance3D in lijst:
		mi.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
		if mi.mesh == null:
			continue
		for s in mi.mesh.get_surface_count():
			var bron := mi.get_active_material(s)
			if not _gmat.has(bron):
				_gmat[bron] = [_ghost_mat(bron, true), _ghost_mat(bron, false)]
			_gsurf.append([mi, s, _gmat[bron][0], _gmat[bron][1]])
	n.visible = false
	ghost.get_parent().add_child(n)
	return n


func _wis_gmodel() -> void:
	if _gmodel != null:
		_gmodel.queue_free()
	_gmodel = null
	_gmodel_soort = &""
	_gsurf.clear()


## Botsvormen en physics uit een ghost: hij mag niets tegenhouden en geen klik vangen.
static func _ontbots(n: Node) -> void:
	for c in n.get_children():
		if c is CollisionObject3D or c is CollisionShape3D:
			c.queue_free()
		else:
			_ontbots(c)


const GHOST_ALFA := 0.6
const GHOST_TINT_KAN := Color(0.55, 1.0, 0.5)
const GHOST_TINT_NIET := Color(1.0, 0.45, 0.4)
const GHOST_LICHT_KAN := Color(0.1, 0.45, 0.1)
const GHOST_LICHT_NIET := Color(0.5, 0.08, 0.06)
const PIJL_KAN := Color(0.45, 1.0, 0.4, 0.9)
const PIJL_NIET := Color(1.0, 0.3, 0.25, 0.9)

## Doorzichtige, getinte kopie van een gebouwmateriaal: de textuur blijft (zo blijft de deur te zien) en wordt met de
## tint vermenigvuldigd, plus wat eigen licht in de tint zodat hij ook 's nachts en in de schaduw opvalt. Depth
## prepass: alleen de voorste laag, geen rommel van achterwanden door de voorgevel heen.
static func _ghost_mat(bron: Material, kan: bool) -> Material:
	var m: BaseMaterial3D
	if bron is BaseMaterial3D:
		m = (bron as BaseMaterial3D).duplicate() as BaseMaterial3D
	else:
		m = StandardMaterial3D.new()
	var tint := GHOST_TINT_KAN if kan else GHOST_TINT_NIET
	var a := m.albedo_color
	m.albedo_color = Color(a.r * tint.r, a.g * tint.g, a.b * tint.b, GHOST_ALFA)
	m.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA_DEPTH_PRE_PASS
	m.cull_mode = BaseMaterial3D.CULL_BACK
	m.emission_enabled = true
	m.emission = GHOST_LICHT_KAN if kan else GHOST_LICHT_NIET
	m.emission_energy_multiplier = 1.0
	m.emission_texture = null
	m.disable_receive_shadows = true
	return m


## Platte pijl (langs +x, 1,5 m lang) die op de grond ligt en altijd boven het terrein tekent.
func _maak_pijl() -> MeshInstance3D:
	var st := SurfaceTool.new()
	st.begin(Mesh.PRIMITIVE_TRIANGLES)
	st.set_normal(Vector3.UP)
	var punten := [Vector2(-0.75, -0.18), Vector2(0.1, -0.18), Vector2(0.1, 0.18), Vector2(-0.75, 0.18),   # steel
		Vector2(0.1, -0.55), Vector2(0.75, 0.0), Vector2(0.1, 0.55)]                                        # punt
	for i in [0, 2, 1, 0, 3, 2, 4, 6, 5]:
		var v: Vector2 = punten[i]
		st.add_vertex(Vector3(v.x, 0.0, v.y))
	var mi := MeshInstance3D.new()
	mi.mesh = st.commit()
	var mat := StandardMaterial3D.new()
	mat.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
	mat.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
	mat.no_depth_test = true
	mat.render_priority = 1
	mat.cull_mode = BaseMaterial3D.CULL_DISABLED
	mat.albedo_color = PIJL_KAN
	mi.material_override = mat
	mi.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	return mi


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
	var plekken := p.stapels      # sim: Wereld.stapel_plekken (bij plan_zet), leeg voor akker, hek, poort, weg
	for i in plekken.size():
		var naam: String = STAPELS[i]
		if not Natuur.bestaat(naam) and STAPEL_TERUG.has(naam):
			naam = STAPEL_TERUG[naam]
		var n := Natuur.instantie(naam)
		if n == null:
			continue
		n.position = _grond(plekken[i])
		n.rotation.y = p.stapel_hoek(i)
		n.set_meta("stapel", STAPELS[i])
		ghost.get_parent().add_child(n)
		lijst.append(n)
	_stapels[p] = lijst


func _grond(t: Vector2i) -> Vector3:
	var v := Vector3((t.x + 0.5) * w.tegel_m, GROND_Y, (t.y + 0.5) * w.tegel_m)
	if terrein != null:
		v.y = terrein.hoogte_op(v.x, v.z)
	return v


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
	if p.soort == &"put":
		BronWater.zet(hut)          # rimpelend bassin en stromende straal (view/bron_water.gd)
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
	n.rotation.y = p.draai * PI * 0.5 + float(GEBOUWEN[p.soort].get("draai", 0.0))
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


## Een dorpeling die aan een plan werkt doet wat zijn werkplek zegt (sim: Wereld.werk_plekken, Dorpeling.werk_soort):
## zagen bij de zaagbok (origineel `saw`), hakken met de houweel bij de steenhoop (`pick`), anders hameren aan de
## gevel (`hammer`); hij kijkt naar `werk_kijk` (de stam, de keien, de gevel).
func _kijk_bouwers() -> void:
	if view == null:
		return
	for d in w.dorpelingen:
		var u: Dictionary = view.units.get(d.id, {})
		if u.is_empty():
			continue
		var b: Bumpkin = u["bump"]
		b.werk_voorkeur = &""
		if not d.bouwt or d.werk_plan == null or d.werk_plan.klaar or d.werk_soort == &"":
			continue
		b.werk_voorkeur = d.werk_soort
		if d.werk_kijk.is_finite():
			var k := Vector3(d.werk_kijk.x * w.tegel_m, 0.0, d.werk_kijk.y * w.tegel_m)
			b.kijk_naar(k - b.global_position)

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
				kies_tegel(s)
				get_viewport().set_input_as_handled()
				return
		if actief and e.keycode == KEY_R:
			draai_verder()
			get_viewport().set_input_as_handled()
		elif actief and e.keycode == KEY_ESCAPE:
			zet_actief(false)
			get_viewport().set_input_as_handled()
		elif paneel_open and e.keycode == KEY_ESCAPE:
			zet_paneel(false)
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
		hint.text = _hint_basis
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
	return p != null and w.bouw_reden(p) == "" and w.kan_betalen_plan(p)     # incl. de deurweg


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
		_pijl.visible = false
		_pad_mi.visible = false
		_touch_rij()
		if _t_sleutel != _t_getoond:
			_t_getoond = _t_sleutel
			_toon_rij(_t_rij, _t_st)
			var n := _t_st.count(BouwRij.KAN)
			knop_bouw.text = ("%d x %d" % [n, w.prijs(soort)]) if n > 0 else "Bouwen"   # aantal x prijs, met het vinkje: past ook staand
		knop_bouw.disabled = not BouwRij.KAN in _t_st
		return
	knop_bouw.text = "Bouwen"
	knop_bouw.disabled = not _toon_ghost(_plan_op(_t_tegel))


## `--proef=bouw` (alleen frames, view/scherm.gd): bouwmodus voor `--proef_soort=` (standaard hut), `--proef_draai=0..3`;
## de ghost groen op de vrije plek die het dichtst bij het midden van het beeld ligt, of met `--proef_rood` op het
## kampvuur (kan niet); `--proef_pad`: de dichtste plek met een deurweg van 3+ nieuwe tegels (met `--proef_duur` net
## te weinig kas voor het pad: rood "Te duur"). De camera springt erheen;
## kas en menu staan open, zodat alleen de plek de kleur bepaalt.
func _proef_bouw() -> void:
	w.alles_open = true
	w.kas = maxi(w.kas, 100000)
	var s := StringName(Scherm.optie("proef_soort"))
	if not GEBOUWEN.has(s):
		s = &"hut"
	kies(s)
	_scene(GEBOUWEN[s]["glb"], true)     # frames: wachten op de glb, anders hangt het van de laadtijd af of het de kist is
	draai = posmod(int(Scherm.optie("proef_draai")), 4)
	var t := w.kampvuur
	var pad_proef := "--proef_pad" in OS.get_cmdline_user_args()     # een plek met een deurweg van 3+ nieuwe tegels
	if not "--proef_rood" in OS.get_cmdline_user_args():
		var mid := bestuur.tegel_onder(get_viewport().get_visible_rect().size * 0.5)
		if mid.x < 0:
			mid = w.kampvuur
		var best := Vector2i(-1, -1)
		for r in range(0, 14):
			for dx in range(-r, r + 1):
				for dz in range(-r, r + 1):
					if best.x >= 0 or maxi(absi(dx), absi(dz)) != r:
						continue
					var p := _plan_op(mid + Vector2i(dx, dz))
					if p != null and w.kan_bouwen(p) and w.binnen_bouwafstand(p) and (not pad_proef \
							or (Plan.DEUREN.has(s) and w.weg_nieuw(w.weg_route(p.deur_tegel(), p)) >= 3)):
						best = mid + Vector2i(dx, dz)
		if best.x >= 0:
			t = best
	if pad_proef and "--proef_duur" in OS.get_cmdline_user_args():   # genoeg voor het gebouw, niet voor het pad: rood
		w.kas = w.prijs(s) + int(w.spel.get("weg_per_tegel", 0))
	if touch:
		_t_tegel = t
		_t_eind = t
	else:
		_proef_tegel = t
	if bestuur.cam != null and bestuur.cam.has_method("spring_naar"):
		bestuur.cam.spring_naar(_grond(t))


# ---------------------------------------------------------------- tegel en hamer (schets variant A)

## Een gebouw in het paneel: ikoon, prijs eronder (goud; rood als het te duur is), op slot grijs met een slotje en de
## reden. Pc: ook de naam en de lettertoets linksboven. Alles zelf getekend (geen kleine Labels).
class BouwTegel extends Button:
	const KAN := 0
	const DUUR := 1
	const SLOT := 2
	const GOUD := Color(0.95, 0.76, 0.31)
	const ROOD := Color(1.0, 0.42, 0.36)
	const GROEN := Color(0.37, 0.83, 0.35)
	var soort: StringName
	var ikoon: Texture2D
	var prijs := 0
	var naam := ""
	var toets := ""
	var pc := false
	var staat := KAN
	var reden := ""
	var aan := false

	func _init() -> void:
		focus_mode = Control.FOCUS_NONE
		flat = true
		mouse_default_cursor_shape = Control.CURSOR_POINTING_HAND
		mouse_entered.connect(queue_redraw)
		mouse_exited.connect(queue_redraw)

	func zet(st: int, r: String, a: bool) -> void:
		if st == staat and r == reden and a == aan:
			return
		staat = st
		reden = r
		aan = a
		queue_redraw()

	func _draw() -> void:
		var sb := StyleBoxFlat.new()
		sb.set_corner_radius_all(int(size.x * 0.08))
		sb.bg_color = Color(GROEN, 0.18) if aan else Color(1, 1, 1, 0.13 if is_hovered() else 0.07)
		if aan:
			sb.border_color = GROEN
			sb.set_border_width_all(2)
		draw_style_box(sb, Rect2(Vector2.ZERO, size))
		var f := get_theme_default_font()
		var fs := clampi(int(size.x * (0.14 if pc else 0.13)), 12, 48)
		var pad := size.x * 0.06
		var y_prijs := size.y - pad - fs * 0.2
		var vaal := 0.5 if staat == SLOT else 1.0
		_tekst(f, str(prijs), y_prijs, fs, Color(ROOD if staat == DUUR else GOUD, vaal))
		var onder := y_prijs - fs * 1.05
		if pc:
			_tekst(f, naam, onder, int(fs * 0.95), Color(1, 1, 1, vaal))
			onder -= fs * 1.1
		var zijde := minf(size.x - 2.0 * pad, onder - pad)
		var ik := Rect2(Vector2((size.x - zijde) * 0.5, pad), Vector2(zijde, zijde))
		var mod := Color(0.4, 0.4, 0.4) if staat == SLOT else (Color(0.75, 0.68, 0.68) if staat == DUUR else Color.WHITE)
		if ikoon != null:
			draw_texture_rect(ikoon, ik, false, mod)
		else:
			draw_rect(ik.grow(-zijde * 0.2), Color(0.55, 0.4, 0.25) * mod)
		if staat == SLOT:
			var m := ik.get_center() - Vector2(0, zijde * 0.1)
			var r := zijde * 0.2
			draw_circle(m, r, Color(0, 0, 0, 0.8))
			var sl := Color(1.0, 0.82, 0.48)
			draw_arc(m + Vector2(0, -r * 0.12), r * 0.32, PI, TAU, 16, sl, r * 0.13)
			draw_rect(Rect2(m + Vector2(-r * 0.45, -r * 0.12), Vector2(r * 0.9, r * 0.65)), sl)
			draw_circle(m + Vector2(0, r * 0.18), r * 0.1, Color.BLACK)
			if reden != "":
				_tekst(f, reden, m.y + r + fs * 1.0, fs, sl, true)
		if pc and toets != "":
			var tf := int(fs * 0.8)
			var tw := f.get_string_size(toets, HORIZONTAL_ALIGNMENT_LEFT, -1, tf)
			var tr := Rect2(Vector2(4, 4), tw + Vector2(8, 2))
			var tsb := StyleBoxFlat.new()
			tsb.bg_color = Color(0, 0, 0, 0.65)
			tsb.border_color = Color(1, 1, 1, 0.33)
			tsb.set_border_width_all(1)
			tsb.set_corner_radius_all(3)
			draw_style_box(tsb, tr)
			draw_string(f, Vector2(tr.position.x + 4, tr.position.y + tf * 0.95), toets, HORIZONTAL_ALIGNMENT_LEFT, -1, tf, Color.WHITE)

	## Gecentreerde regel met de basislijn op `y`; `rand` = zwarte omlijning (over het ikoon).
	func _tekst(f: Font, t: String, y: float, fs: int, kleur: Color, rand := false) -> void:
		var b := f.get_string_size(t, HORIZONTAL_ALIGNMENT_LEFT, -1, fs).x
		var p := Vector2((size.x - b) * 0.5, y)
		if rand:
			draw_string_outline(f, p, t, HORIZONTAL_ALIGNMENT_LEFT, -1, fs, maxi(2, fs / 6), Color(0, 0, 0, 0.9))
		draw_string(f, p, t, HORIZONTAL_ALIGNMENT_LEFT, -1, fs, kleur)


## Ronde hamerknop (paneelmodus, rechtsonder): donker met een gouden rand, hamer zelf getekend (schets variant A).
class HamerKnop extends Button:
	func _init() -> void:
		focus_mode = Control.FOCUS_NONE
		flat = true
		toggle_mode = true

	func _draw() -> void:
		var m := size * 0.5
		var r := minf(size.x, size.y) * 0.5
		draw_circle(m, r - 1.0, Color(0.12, 0.1, 0.08, 0.88))
		draw_arc(m, r - maxf(2.0, r * 0.04), 0.0, TAU, 48, Color(0.95, 0.76, 0.31), maxf(2.0, r * 0.07), true)
		# hamer op een 24-raster (schets: SVG.hamer), 0,62 van de knop
		var k := r * 1.24 / 24.0
		var o := m - Vector2(12, 12) * k
		var steel := PackedVector2Array([Vector2(13.5, 9.5), Vector2(4, 19), Vector2(6.2, 21.2), Vector2(15.7, 11.7)])
		var kop := PackedVector2Array([Vector2(11, 4.5), Vector2(15.5, 2), Vector2(21.5, 8), Vector2(19, 12.5),
			Vector2(17, 10.5), Vector2(14, 13.5), Vector2(10, 9.5), Vector2(13, 6.5)])
		for poly: Array in [[steel, Color(0.69, 0.48, 0.27), Color(0.23, 0.14, 0.07)], [kop, Color(0.79, 0.81, 0.82), Color(0.2, 0.22, 0.24)]]:
			var pts := PackedVector2Array()
			for p: Vector2 in poly[0]:
				pts.append(o + p * k)
			draw_colored_polygon(pts, poly[1])
			pts.append(pts[0])
			draw_polyline(pts, poly[2], maxf(1.0, k), true)
