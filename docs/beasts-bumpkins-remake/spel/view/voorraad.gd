class_name Voorraad
extends Node3D
## De winkelvoorraad op het scherm: een kraam bij de deur van elke molen, melkerij en kippenhok met zoveel broden,
## melkkannen of eieren als er op het schap liggen, een gouden "+3" die bij elke verkoop omhoog drijft, een korte
## "+1" met een opspringend stuk waar bij elke levering, en een rood "!" boven een lege kraam.
##
## Uit beasts-src overgenomen:
## - de voorraad als `kind.stock` (8) vakjes in vier kolommen, gevuld tot `stock` met het waar-icoon, en het lege
##   vakje is wat "hier zit niets" zegt (`HudArt.stock`, HudArt.kt:551). Hier: twee rijen van vier op de kraam,
##   daarboven een getal.
## - "de winkel mag er anders uitzien als hij vol staat dan als hij leeg is" (beasts-src
##   docs/besluiten/wat-de-winkel-is-in-het-spel.md) en de klant koopt aan de toonbank, bij de drempel.
## - het bedrag boven de toonbank (`GameView.buying`/`drawSales`, GameView.kt:1133 en :1710): het goud van de munt
##   (`HudArt.C_COIN` 0xE0B84A), donkere rand onder gouden vulling, de hele reis `SALE_RISE` in `SALE_S` (1,6 s) en
##   geen snelheid, vervagen alleen op het laatste stuk (`SALE_FADE_S` 0,5 s), twee bedragen op een pand stapelen
##   (`SALE_STACK`) en worden niet samengevoegd, hoogstens `SALE_MAX` (6) tegelijk, hangt aan de plek en niet aan het
##   gebouw.
## - een pulsje met precies een lezer (`Building.sold`, Grid.kt:504): de sim meldt met `Wereld.verkocht`/`geleverd`
##   (in `klus_af`) en dit is de enige luisteraar; de waarheid blijft `Plan.voorraad` en `Wereld.kas`.
## Leest de sim, schrijft er niets in.

const ZICHTBAAR := 8                 # beasts-src Kind.stock: zoveel vakjes, daarboven een getal
const KOLOMMEN := 4                  # beasts-src STOCK_COLS
const KRAAM_B := 1.6                 # breedte van de toonbank (m)
const KRAAM_D := 0.7
const KRAAM_H := 0.72
const OPZIJ := 1.4                   # zo ver naast de deur, zodat de deur en de weg vrij blijven
const VOOR := 0.9                    # zo ver voor de gevel (vanaf het deuranker)
const SALE_S := 1.6                  # beasts-src GameView.SALE_S
const SALE_FADE_S := 0.5             # beasts-src SALE_FADE_S
const SALE_RISE := 1.6               # m, de hele reis (beasts-src 86 px)
const SALE_STACK := 0.5              # m, wat een tweede bedrag op dezelfde kraam erbovenop krijgt
const STACK_MAX := 1.5               # m, hoger stapelt het niet (op 4x tempo rekent een heel dorp tegelijk af)
const SALE_MAX := 6
const LEVER_S := 1.0
const LEVER_RISE := 0.8
const POP_S := 0.35
const C_MUNT := Color8(0xE0, 0xB8, 0x4A)    # beasts-src HudArt.C_COIN
const C_RAND := Color(0.14, 0.09, 0.05)
const C_LEEG := Color(0.95, 0.22, 0.16)
const LUIFEL := {"molen": Color(0.85, 0.62, 0.2), "melkerij": Color(0.3, 0.5, 0.8), "kippenhok": Color(0.75, 0.3, 0.22)}
const WAAR_KLEUR := {"brood": Color(0.78, 0.5, 0.22), "melk": Color(0.95, 0.95, 0.92), "ei": Color(0.93, 0.84, 0.68),
	"graan": Color(0.85, 0.72, 0.4)}

var w: Wereld
var terrein: TerreinView
var _kramen := {}          # Plan -> {"node", "waren": Array, "getal": Label3D, "leeg": Label3D, "top": Vector3, "pop": float}
var _meldingen: Array = [] # [{"node": Label3D, "kraam": Plan, "t": float, "duur", "rise", "basis", "munt"}]
var _waar_mesh := {}
var _waar_mat := {}
var _hout: StandardMaterial3D
var _hout_donker: StandardMaterial3D
var _munt_mesh: CylinderMesh
var _munt_mat: StandardMaterial3D
var _klok := 0.0


func bouw(wereld: Wereld, t: TerreinView) -> void:
	w = wereld
	terrein = t
	name = "Voorraad"
	_maak_materialen()
	for p in w.plannen:
		_plan_klaar(p)
	w.plan_klaar.connect(_plan_klaar)
	w.verkocht.connect(_verkocht)
	w.geleverd.connect(_geleverd)


func _maak_materialen() -> void:
	_hout = StandardMaterial3D.new()
	_hout.albedo_color = Color(0.6, 0.43, 0.26)
	_hout.roughness = 0.9
	_hout_donker = StandardMaterial3D.new()
	_hout_donker.albedo_color = Color(0.36, 0.24, 0.14)
	_hout_donker.roughness = 0.95
	var brood := SphereMesh.new()       # een brood: afgeplatte, langgerekte bol
	brood.radius = 0.17
	brood.height = 0.22
	brood.radial_segments = 12
	brood.rings = 6
	_waar_mesh["brood"] = brood
	var kan := CylinderMesh.new()       # een melkkan: smaller aan de hals
	kan.top_radius = 0.09
	kan.bottom_radius = 0.13
	kan.height = 0.38
	kan.radial_segments = 10
	_waar_mesh["melk"] = kan
	var ei := SphereMesh.new()
	ei.radius = 0.1
	ei.height = 0.26
	ei.radial_segments = 10
	ei.rings = 6
	_waar_mesh["ei"] = ei
	for waar in ["brood", "melk", "ei"]:
		var m := StandardMaterial3D.new()
		m.albedo_color = WAAR_KLEUR[waar]
		m.roughness = 0.6 if waar == "melk" else 0.85
		_waar_mat[waar] = m
	_munt_mesh = CylinderMesh.new()
	_munt_mesh.top_radius = 0.16
	_munt_mesh.bottom_radius = 0.16
	_munt_mesh.height = 0.04
	_munt_mesh.radial_segments = 16
	_munt_mat = StandardMaterial3D.new()
	_munt_mat.albedo_color = C_MUNT
	_munt_mat.metallic = 0.8
	_munt_mat.roughness = 0.3
	_munt_mat.emission_enabled = true
	_munt_mat.emission = C_MUNT * 0.35


# ---------------------------------------------------------------- de kraam

func _plan_klaar(p: Plan) -> void:
	if not p.klaar or not Wereld.WINKELS.has(p.soort) or _kramen.has(p):
		return
	var waar: String = Wereld.WINKELS[p.soort]["waar"]
	var r := Vector2(p.deur_richting())
	var opzij := Vector2(-r.y, r.x)
	# welke kant van de deur: eerst de kant naar +x/+z (de startcamera kijkt van daar; de melkerij verstopte de kraam
	# eerst achter zich), maar niet op de weg en niet op een geblokkeerde tegel
	var pad := w.raster.namen.find("pad")
	var kanten := [opzij, -opzij] if opzij.x + opzij.y >= 0 else [-opzij, opzij]
	var plek: Vector2 = p.deur_punt(w.tegel_m) + r * VOOR + kanten[0] * OPZIJ
	for k: Vector2 in kanten:
		# tegen de gevel, naast de deur: vanaf het deuranker een stap naar buiten en opzij (de klant staat op de deurtegel)
		var kp: Vector2 = p.deur_punt(w.tegel_m) + r * VOOR + k * OPZIJ
		var t := Vector2i(int(floor(kp.x / w.tegel_m)), int(floor(kp.y / w.tegel_m)))
		if w.raster.loopbaar_v(t) and w.raster.soort[w.raster.idx(t.x, t.y)] != pad:
			plek = kp
			break
	var kraam := Node3D.new()
	kraam.name = "Kraam_%s" % p.soort
	kraam.position = Vector3(plek.x, terrein.hoogte_op(plek.x, plek.y), plek.y)
	kraam.rotation.y = atan2(r.x, r.y)       # lokaal +z = de deurrichting: de voorkant kijkt naar buiten
	add_child(kraam)
	_maak_tafel(kraam, p.soort)
	var waren: Array = []
	for i in ZICHTBAAR:
		var mi := MeshInstance3D.new()
		mi.mesh = _waar_mesh[waar]
		mi.material_override = _waar_mat[waar]
		var kol := i % KOLOMMEN
		var rij := i / KOLOMMEN                  # rij 0 vooraan, bij de klant
		var x := (kol - (KOLOMMEN - 1) * 0.5) * (KRAAM_B - 0.2) / KOLOMMEN
		var z := 0.17 - rij * 0.34
		var y := KRAAM_H + 0.03
		match waar:
			"brood":
				mi.scale = Vector3(1.0, 1.0, 1.4)
				mi.rotation.y = 0.25 * ((i * 7) % 3 - 1)
				y += 0.09
			"melk": y += 0.19
			"ei":
				y += 0.12 + rij * 0.0
				mi.rotation.z = 0.35 * ((i * 5) % 3 - 1)
		mi.position = Vector3(x, y, z)
		kraam.add_child(mi)
		waren.append(mi)
	var getal := _label(52, Color(1, 1, 1), 0.012)
	getal.position = Vector3(0, KRAAM_H + 0.75, 0)
	kraam.add_child(getal)
	var leeg := _label(110, C_LEEG, 0.012)
	leeg.text = "!"
	leeg.position = Vector3(0, KRAAM_H + 1.3, 0)
	kraam.add_child(leeg)
	_kramen[p] = {"node": kraam, "waren": waren, "getal": getal, "leeg": leeg, "toon": -1, "pop": 0.0,
		"top": kraam.position + Vector3(0, 2.0, 0)}


## Toonbank op vier poten, met een luifel in de kleur van de winkel aan twee palen erachter.
func _maak_tafel(kraam: Node3D, soort: StringName) -> void:
	var blad := MeshInstance3D.new()
	var bm := BoxMesh.new()
	bm.size = Vector3(KRAAM_B, 0.06, KRAAM_D)
	blad.mesh = bm
	blad.material_override = _hout
	blad.position.y = KRAAM_H
	kraam.add_child(blad)
	var front := MeshInstance3D.new()        # voorplank: zo leest het als toonbank en niet als tafel
	var fm := BoxMesh.new()
	fm.size = Vector3(KRAAM_B, KRAAM_H - 0.1, 0.04)
	front.mesh = fm
	front.material_override = _hout_donker
	front.position = Vector3(0, (KRAAM_H - 0.1) * 0.5 + 0.05, KRAAM_D * 0.5 - 0.03)
	kraam.add_child(front)
	var poot_m := BoxMesh.new()
	poot_m.size = Vector3(0.07, KRAAM_H, 0.07)
	for sx in [-1, 1]:
		for sz in [-1, 1]:
			var poot := MeshInstance3D.new()
			poot.mesh = poot_m
			poot.material_override = _hout_donker
			poot.position = Vector3(sx * (KRAAM_B * 0.5 - 0.05), KRAAM_H * 0.5, sz * (KRAAM_D * 0.5 - 0.05))
			kraam.add_child(poot)
	var paal_m := BoxMesh.new()
	paal_m.size = Vector3(0.07, 1.75, 0.07)
	for sx in [-1, 1]:
		var paal := MeshInstance3D.new()
		paal.mesh = paal_m
		paal.material_override = _hout_donker
		paal.position = Vector3(sx * (KRAAM_B * 0.5 - 0.05), 0.875, -KRAAM_D * 0.5 + 0.04)
		kraam.add_child(paal)
	var luifel := MeshInstance3D.new()
	var lm := BoxMesh.new()
	lm.size = Vector3(KRAAM_B + 0.2, 0.04, KRAAM_D + 0.35)
	luifel.mesh = lm
	var doek := StandardMaterial3D.new()
	doek.albedo_color = LUIFEL.get(String(soort), Color(0.7, 0.7, 0.6))
	doek.roughness = 1.0
	luifel.material_override = doek
	luifel.position = Vector3(0, 1.62, 0.1)
	luifel.rotation.x = 0.32                 # schuin naar voren omlaag
	kraam.add_child(luifel)


func _label(grootte: int, kleur: Color, px: float) -> Label3D:
	var l := Label3D.new()
	l.billboard = BaseMaterial3D.BILLBOARD_ENABLED
	l.font_size = grootte
	l.outline_size = int(grootte * 0.22)
	l.modulate = kleur
	l.outline_modulate = C_RAND
	l.pixel_size = px
	l.no_depth_test = true                   # boven het dak en de luifel altijd te lezen
	l.render_priority = 2
	l.outline_render_priority = 1
	l.visible = false
	return l


# ---------------------------------------------------------------- meldingen (beasts-src buying/drawSales)

func _verkocht(p: Plan, _waar: String, prijs: int) -> void:
	if not _kramen.has(p):
		return
	_melding(p, "+%d" % prijs, C_MUNT, 72, SALE_S, SALE_RISE, true)


func _geleverd(p: Plan, brengt: String) -> void:
	if not _kramen.has(p):
		return
	_kramen[p]["pop"] = POP_S
	_melding(p, "+1", WAAR_KLEUR.get(brengt, Color.WHITE), 50, LEVER_S, LEVER_RISE, false)


## Een getal dat boven de kraam omhoog drijft. Twee op dezelfde kraam stapelen (beasts-src SALE_STACK): het nieuwe
## begint boven waar het vorige nu staat, zodat een "+3" die je aan het lezen bent geen "+6" wordt.
func _melding(p: Plan, tekst: String, kleur: Color, grootte: int, duur: float, rise: float, munt: bool) -> void:
	var basis := 0.0
	for m in _meldingen:
		if m["kraam"] != p:
			continue
		var op: float = m["rise"] * (1.0 - m["t"] / m["duur"]) + m["basis"]
		basis = maxf(basis, op + SALE_STACK)
	basis = minf(basis, STACK_MAX)
	if munt:
		var tel := 0
		for m in _meldingen:
			if m["munt"] != null:
				tel += 1
		if tel >= SALE_MAX:                  # meer dan zes is geen melding meer; de kas blijft de waarheid
			for i in _meldingen.size():
				if _meldingen[i]["munt"] != null:
					_weg(_meldingen[i])
					_meldingen.remove_at(i)
					break
	var l := _label(grootte, kleur, 0.012)
	l.text = tekst
	l.visible = true
	add_child(l)
	var mn: MeshInstance3D = null
	if munt:
		mn = MeshInstance3D.new()
		mn.mesh = _munt_mesh
		mn.material_override = _munt_mat
		mn.rotation.x = PI * 0.5
		mn.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
		add_child(mn)
	_meldingen.append({"node": l, "kraam": p, "t": duur, "duur": duur, "rise": rise, "basis": basis, "munt": mn,
		"bij": (_kramen[p]["top"] as Vector3) - Vector3(0, 0.0 if munt else 0.4, 0)})


func _weg(m: Dictionary) -> void:
	(m["node"] as Node).queue_free()
	if m["munt"] != null:
		(m["munt"] as Node).queue_free()


func _process(dt: float) -> void:
	_klok += dt
	for p: Plan in _kramen.keys():
		var k: Dictionary = _kramen[p]
		if not is_instance_valid(k["node"]):
			continue
		var n := p.voorraad
		var zien := mini(n, ZICHTBAAR)
		if zien != k["toon"]:
			var waren: Array = k["waren"]
			for i in waren.size():
				(waren[i] as Node3D).visible = i < zien
			k["toon"] = zien
		var getal: Label3D = k["getal"]
		getal.visible = n > ZICHTBAAR
		if getal.visible:
			getal.text = "%d" % n
		var leeg: Label3D = k["leeg"]
		leeg.visible = n <= 0
		if leeg.visible:     # zacht deinen en kloppen: leeg moet opvallen, aanvoer nodig
			leeg.position.y = KRAAM_H + 1.3 + 0.12 * sin(_klok * 3.0)
			leeg.modulate.a = 0.75 + 0.25 * sin(_klok * 6.0)
		if k["pop"] > 0.0:   # het stuk dat er net bij kwam springt even op
			k["pop"] = maxf(0.0, k["pop"] - dt)
			if zien > 0:
				var f: float = k["pop"] / POP_S
				var stuk: Node3D = k["waren"][zien - 1]
				stuk.scale = _basis_schaal(p) * (1.0 + 0.7 * f)
				if k["pop"] <= 0.0:
					stuk.scale = _basis_schaal(p)
	var i := 0
	while i < _meldingen.size():
		var m: Dictionary = _meldingen[i]
		m["t"] = m["t"] - dt
		if m["t"] <= 0.0:
			_weg(m)
			_meldingen.remove_at(i)
			continue
		var weg := 1.0 - clampf(m["t"] / m["duur"], 0.0, 1.0)
		var pos: Vector3 = m["bij"] + Vector3(0, m["basis"] + m["rise"] * weg, 0)
		var l: Label3D = m["node"]
		var a := minf(1.0, m["t"] / SALE_FADE_S)
		l.position = pos
		l.modulate.a = a
		l.outline_modulate.a = a
		if m["munt"] != null:
			var mn: MeshInstance3D = m["munt"]
			mn.position = pos + Vector3(0, -0.45, 0)
			mn.rotation = Vector3(PI * 0.5, 0, 0)
			mn.rotate_y(_klok * 7.0)
			mn.transparency = 1.0 - a
		i += 1


func _basis_schaal(p: Plan) -> Vector3:
	return Vector3(1.0, 1.0, 1.4) if p.soort == &"molen" else Vector3.ONE
