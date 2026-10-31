class_name GedachtenView
extends Node3D
## Gedachtewolkjes boven de dorpelingen (besluit gebruiker 2026-10-31; sim/gedachten.gd zegt welke gedachte).
## Niet op iedereen altijd: alleen als een behoefte over de drempel is (Gedachten.zichtbaar) of bij de gekozen
## dorpelingen (dan ook "tevreden"). Zacht in en uit (FADE_S), rode rand = dringend (gezondheid op het spel).
## Een Sprite3D per dorpeling (billboard, onbelicht, vaste schermgrootte zodat het bij elke zoom leesbaar blijft),
## pas gemaakt als hij voor het eerst een wolkje krijgt; de gedachten worden elke HERZIEN_S opnieuw bepaald.
## Pc: bij de (eerste) gekozen dorpeling staat de korte tekst erboven ("Wil melk", "Heeft dorst"); touch alleen het ikoon
## (gebruiker: geen kleine teksten op de telefoon).

const HERZIEN_S := 0.3
const FADE_S := 0.35
const GROOTTE := 0.075        ## Sprite3D.pixel_size met fixed_size: deel van de schermhoogte per textuurpixel / 256
const HOOFD_Y := 1.75         ## m boven de voeten (volwassene); kind x KIND_Y
const KIND_Y := 0.72

var w: Wereld
var view: WereldView
var _t := 0.0
var _gedacht := {}            ## dorpeling-id -> StringName
var _wolk := {}               ## dorpeling-id -> {"sprite": Sprite3D, "a": float, "g": StringName}
var _tekst: Label3D           ## pc: korte tekst bij de gekozen dorpeling


func bouw(wereld: Wereld, v: WereldView) -> void:
	w = wereld
	view = v
	if not Bouwmenu.touch:
		_tekst = Label3D.new()
		_tekst.billboard = BaseMaterial3D.BILLBOARD_ENABLED
		_tekst.fixed_size = true
		_tekst.pixel_size = 0.0011
		_tekst.font_size = 22
		_tekst.outline_size = 9
		_tekst.modulate = Color(1, 1, 1)
		_tekst.outline_modulate = Color(0.05, 0.05, 0.08, 0.9)
		_tekst.no_depth_test = true
		_tekst.render_priority = 11
		_tekst.outline_render_priority = 10
		_tekst.offset = Vector2(26, 74)
		_tekst.visible = false
		add_child(_tekst)


## De gedachte van een dorpeling zoals de view hem nu toont (tests, portret).
func gedachte(id: int) -> StringName:
	return _gedacht.get(id, &"")


func _process(dt: float) -> void:
	if w == null:
		return
	_t += dt
	if _t >= HERZIEN_S or _gedacht.is_empty():
		_t = 0.0
		_gedacht.clear()
		for d in w.dorpelingen:
			_gedacht[d.id] = Gedachten.van(w, d)
	var levend := {}
	var eerste: int = view.gekozen[0] if not view.gekozen.is_empty() else -1
	var tekst_bij := -1
	for d in w.dorpelingen:
		levend[d.id] = true
		var g: StringName = _gedacht.get(d.id, &"")
		var u: Dictionary = view.units.get(d.id, {})
		var b: Node3D = u.get("bump")
		var wil := g != &"" and b != null and b.visible and (Gedachten.zichtbaar(g) or d.id in view.gekozen)
		var k: Dictionary = _wolk.get(d.id, {})
		if k.is_empty():
			if not wil:
				continue
			k = {"sprite": _maak_sprite(), "a": 0.0, "g": &""}
			_wolk[d.id] = k
		var s: Sprite3D = k["sprite"]
		if wil and g != k["g"]:
			k["g"] = g
			s.texture = GedachteIkonen.textuur(Gedachten.ikoon(g), true, Gedachten.dringend(g), 2.0, true)
		k["a"] = move_toward(k["a"], 1.0 if wil else 0.0, dt / FADE_S)
		s.visible = k["a"] > 0.01
		if not s.visible:
			continue
		s.modulate = Color(1, 1, 1, k["a"])
		var hoogte := HOOFD_Y * (KIND_Y if d.leeftijd == "kind" else 1.0) * b.scale.y
		s.global_position = b.global_position + Vector3(0, hoogte, 0)
		if d.id == eerste and wil:
			tekst_bij = d.id
	for id in _wolk.keys():          # dood of weg: wolkje weg
		if not levend.has(id):
			(_wolk[id]["sprite"] as Node).queue_free()
			_wolk.erase(id)
	if _tekst != null:
		_tekst.visible = tekst_bij >= 0
		if _tekst.visible:
			var k: Dictionary = _wolk[tekst_bij]
			_tekst.text = Gedachten.tekst(k["g"])
			_tekst.global_position = (k["sprite"] as Sprite3D).global_position
			_tekst.modulate.a = k["a"]
			_tekst.outline_modulate.a = 0.9 * k["a"]


func _maak_sprite() -> Sprite3D:
	var s := Sprite3D.new()
	s.billboard = BaseMaterial3D.BILLBOARD_ENABLED
	s.fixed_size = true
	s.pixel_size = GROOTTE / 256.0
	s.shaded = false
	s.double_sided = true
	s.no_depth_test = true           # boven bomen en daken uit, zoals het origineel
	s.render_priority = 10
	s.alpha_cut = SpriteBase3D.ALPHA_CUT_DISABLED
	s.texture_filter = BaseMaterial3D.TEXTURE_FILTER_LINEAR_WITH_MIPMAPS
	s.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	s.offset = Vector2(96, 104)     # rechtsboven het hoofd, het staartje wijst naar hem
	s.visible = false
	add_child(s)
	return s
