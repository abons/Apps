class_name Bouwmenu
extends Node
## Bouwmenu (stap 5, gameplay.md §7): een knop per gebouw in GEBOUWEN (of zijn toets), ghost volgt de muis over de tegels (groen = kan, rood = kan niet),
## R draait, linkerklik plaatst een Plan in Wereld, rechterklik of Esc stopt. Shift bij het plaatsen houdt de modus aan.
## Een Plan is een kist die in Plan.STANDEN groeit, met een houtstapel en steenhoop ernaast die slinken met de voortgang
## (alleen weergave; kas en aanvoer staan nog niet in de sim). Klaar: de kist wordt de glb van het gebouw. De glb's
## zijn op ware grootte (dorpeling 1,37 m); een mensendeur ("voordeur", anders "deur", >= 1 m) schaalt ze op DEUR_M,
## iets groter dan een volwassene. Ontbreekt de glb: een bruine kist.
## Moet NA Bestuur in de boom staan: dan krijgt het de invoer eerst en neemt het de linkerklik van het kiezen over.

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
}
const WIEKEN_RAD_S := 0.9      ## draaisnelheid van de molenwieken

const STAPELS := ["houtstapel", "steenhoop"]
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
var _kisten := {}          ## Plan -> kist
var _stapels := {}         ## Plan -> [Node3D]
var terrein: TerreinView   ## optioneel: grondhoogte voor stapels en hut (anders GROND_Y)
var _scenes := {}          ## soort -> PackedScene
var _wieken: Array[Node3D] = []
var _gewas := {}           ## akkertegel -> Node3D (akker_rijp, groeit mee met Wereld.akkers)


func bouw(wereld: Wereld, b: Bestuur, parent3d: Node3D) -> void:
	w = wereld
	bestuur = b
	ghost = _kist(soort, Color(0.3, 1.0, 0.3, 0.45))
	ghost.visible = false
	parent3d.add_child(ghost)
	w.plan_gezet.connect(_toon_plan)
	w.plan_klaar.connect(_plan_klaar)

	var laag := CanvasLayer.new()
	add_child(laag)
	var rij := HBoxContainer.new()
	rij.add_theme_constant_override("separation", 8)
	rij.set_anchors_preset(Control.PRESET_BOTTOM_WIDE)
	rij.alignment = BoxContainer.ALIGNMENT_END      # rechtsonder: links staat de hulptekst
	rij.offset_top = -56
	rij.offset_bottom = -16
	rij.offset_right = -16
	laag.add_child(rij)
	for s: StringName in GEBOUWEN:
		var g: Dictionary = GEBOUWEN[s]
		var k := Button.new()
		k.text = "%s %d (%s)" % [g["tekst"], w.prijs(s), OS.get_keycode_string(g["toets"])]
		k.toggle_mode = true
		k.add_theme_font_size_override("font_size", 18)
		k.focus_mode = Control.FOCUS_NONE
		k.toggled.connect(func(aan: bool) -> void: kies(s, aan))
		rij.add_child(k)
		knoppen[s] = k


## Zet de bouwmodus aan voor `s`, of uit.
func kies(s: StringName, aan := true) -> void:
	if aan and s != soort:
		soort = s
		var oud := ghost
		ghost = _kist(soort, Color(0.3, 1.0, 0.3, 0.45))
		oud.get_parent().add_child(ghost)
		oud.queue_free()
	zet_actief(aan)


func zet_actief(aan: bool) -> void:
	actief = aan
	ghost.visible = aan
	for s in knoppen:
		var k: Button = knoppen[s]
		var moet: bool = aan and s == soort
		if k.button_pressed != moet:
			k.set_pressed_no_signal(moet)
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
	var t := bestuur.tegel_onder(pos)
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
		var k: MeshInstance3D = _kisten[p]
		if p.klaar:
			continue
		var f: float = float(p.stand()) / Plan.STANDEN
		k.scale.y = f
		k.position.y = GROND_Y + _hoogte(p.soort) * 0.5 * k.scale.y
		(k.material_override as StandardMaterial3D).albedo_color = Color(0.9, 0.8, 0.4, 0.5).lerp(Color(0.55, 0.4, 0.25, 1.0), f)
	if not actief:
		return
	var p := _plan_onder(get_viewport().get_mouse_position())
	ghost.visible = p != null
	if p == null:
		return
	ghost.position = _midden(p)
	ghost.rotation.y = draai * PI * 0.5
	var kan := w.kan_bouwen(p) and w.kan_betalen(p.soort)
	(ghost.material_override as StandardMaterial3D).albedo_color = Color(0.3, 1.0, 0.3, 0.45) if kan else Color(1.0, 0.25, 0.2, 0.45)


func _toon_plan(p: Plan) -> void:
	var mi := _kist(p.soort, Color(0.9, 0.8, 0.4, 0.5))
	mi.position = _midden(p)
	mi.rotation.y = p.draai * PI * 0.5
	_kisten[p] = mi
	ghost.get_parent().add_child(mi)
	var lijst: Array[Node3D] = []
	var plekken := _stapelplekken(p, STAPELS.size() if p.soort != &"akker" else 0)
	for i in plekken.size():
		var n := Natuur.instantie(STAPELS[i])
		if n == null:
			continue
		n.position = _grond(plekken[i])
		n.rotation.y = p.draai * PI * 0.5 + i * 0.7
		ghost.get_parent().add_child(n)
		lijst.append(n)
	_stapels[p] = lijst


func _grond(t: Vector2i) -> Vector3:
	var v := Vector3((t.x + 0.5) * w.tegel_m, GROND_Y, (t.y + 0.5) * w.tegel_m)
	if terrein != null:
		v.y = terrein.hoogte_op(v.x, v.z)
	return v


## Loopbare tegels die aan de voetafdruk grenzen (niet op de hoeken), te beginnen aan de voorkant (+z na draaien).
func _stapelplekken(p: Plan, n: int) -> Array[Vector2i]:
	var r := p.afdruk()
	var rand: Array[Vector2i] = []
	for c in range(r.position.x, r.end.x):
		rand.append(Vector2i(c, r.end.y))
	for rij in range(r.position.y, r.end.y):
		rand.append(Vector2i(r.end.x, rij))
	for c in range(r.position.x, r.end.x):
		rand.append(Vector2i(c, r.position.y - 1))
	for rij in range(r.position.y, r.end.y):
		rand.append(Vector2i(r.position.x - 1, rij))
	var uit: Array[Vector2i] = []
	for t in rand:
		if uit.size() < n and w.raster.loopbaar_v(t) and w.plan_op(t) == null:
			uit.append(t)
	return uit


## Plan af: stapels weg, de kist wordt het gebouw (glb op ware grootte, of op de mensendeur geschaald).
func _plan_klaar(p: Plan) -> void:
	for s: Node3D in _stapels.get(p, []):
		s.queue_free()
	_stapels.erase(p)
	var k: MeshInstance3D = _kisten.get(p)
	if k == null:
		return
	if p.soort == &"akker":
		_maak_akker(p)
		k.queue_free()
		_kisten.erase(p)
		return
	var glb: String = GEBOUWEN[p.soort]["glb"]
	if not _scenes.has(p.soort) and ResourceLoader.exists(glb):
		_scenes[p.soort] = load(glb)
	if not _scenes.has(p.soort):
		k.scale.y = 1.0
		k.position.y = GROND_Y + _hoogte(p.soort) * 0.5
		(k.material_override as StandardMaterial3D).albedo_color = Color(0.55, 0.4, 0.25, 1.0)
		return
	var hut: Node3D = (_scenes[p.soort] as PackedScene).instantiate()
	var box := _omhulsel(hut, Transform3D.IDENTITY)
	var r := p.afdruk()
	# Ware grootte, tenzij er een mensendeur is: dan op DEUR_M (het kippendeurtje van 0,4 m telt niet).
	var schaal := 1.0
	var deur := hut.find_child("voordeur", true, false)
	if deur == null:
		deur = hut.find_child("deur", true, false)
	if deur != null:
		var dh := _omhulsel_van(hut, deur).size.y
		if dh >= 1.0:
			schaal = DEUR_M / dh
	hut.scale = Vector3.ONE * schaal
	hut.rotation.y = p.draai * PI * 0.5
	var m := Vector3((r.position.x + r.size.x * 0.5) * w.tegel_m, GROND_Y, (r.position.y + r.size.y * 0.5) * w.tegel_m)
	if terrein != null:
		m.y = terrein.hoogte_op(m.x, m.z)
	var midden := box.get_center() * schaal
	hut.position = m - Vector3(midden.x, box.position.y * schaal, midden.z).rotated(Vector3.UP, hut.rotation.y)
	ghost.get_parent().add_child(hut)
	var wk := hut.find_child("wieken", true, false) as Node3D
	if wk != null:
		_wieken.append(wk)
	k.queue_free()
	_kisten.erase(p)


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


func _unhandled_input(e: InputEvent) -> void:
	if e is InputEventKey and e.pressed and not e.echo:
		for s: StringName in GEBOUWEN:
			if e.keycode == GEBOUWEN[s]["toets"]:
				kies(s, not (actief and soort == s))
				get_viewport().set_input_as_handled()
				return
		if actief and e.keycode == KEY_R:
			draai = (draai + 1) % 4
			get_viewport().set_input_as_handled()
		elif actief and e.keycode == KEY_ESCAPE:
			zet_actief(false)
			get_viewport().set_input_as_handled()
	elif actief and e is InputEventMouseButton:
		if e.button_index == MOUSE_BUTTON_LEFT and e.pressed:
			var p := _plan_onder(e.position)
			if p != null and w.plan_zet(p) and not Input.is_key_pressed(KEY_SHIFT):
				zet_actief(false)
			get_viewport().set_input_as_handled()
		elif e.button_index == MOUSE_BUTTON_RIGHT:
			if e.pressed:
				_rechts = true
				_rechts_start = e.position
			elif _rechts:
				_rechts = false
				if e.position.distance_to(_rechts_start) < KLIK_DREMPEL:
					zet_actief(false)
