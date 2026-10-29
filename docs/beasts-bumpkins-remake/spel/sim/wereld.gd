class_name Wereld
extends RefCounted
## Wereldstaat van de sim: raster, objecten, dorpelingen, klok, seizoen, weer. Geen Node, geen render.
## `vooruit(dt)` verzamelt tijd en tikt op vaste `sim_hz`; de view interpoleert met `alpha()`.

const SEIZOENEN := ["lente", "zomer", "herfst", "winter"]
## Visuele waarden per seizoen (lente, zomer, herfst, winter); worden tegen het einde zacht naar het volgende geblend.
const SNEEUW := [0.0, 0.0, 0.0, 1.0]
const DROOG := [0.0, 0.1, 0.8, 0.55]
const KOU := [0.25, 0.0, 0.5, 1.0]        # stuurt zonnestand/daglengte
const REGENKANS := [0.35, 0.10, 0.40, 0.0]

signal bevel_gegeven(ids: Array, soort: String, doel: Vector2i)

var spel: Dictionary
var raster := Raster.new()
var objecten: Array[Dictionary] = []     # {cls, naam, model, x, y, blokkeert, state, sex}
var dorpelingen: Array[Dorpeling] = []
var kampvuur := Vector2i.ZERO
var bereik := PackedByteArray()          # tegels bereikbaar vanaf het kampvuur
var eiland := Rect2i()                   # omhullende van `bereik`
var rng := RandomNumberGenerator.new()
var tegel_m := 2.0
var loop_mps := 0.849                    # uit bumpkin_anim.json (lopen)
var looptempo := 2.0                     # globale vermenigvuldiger op het loopen (spel.json); 1 = animatiesnelheid
var tik_dt := 0.1

var tijd_s := 0.0                        # sim-tijd; dag 0 begint op 0
var tik_nr := 0
var tempo := 1.0                         # 1, 2, 4
var gepauzeerd := false
var regen_handmatig := -1                # -1 automatisch, 0 uit, 1 aan
var _acc := 0.0
var _obj_def: Dictionary


## Laadt de data en de kaart. Geeft false als iets ontbreekt (dan staat er een fout in de log).
func laad(kaart_pad := "") -> bool:
	spel = Gegevens.lees(Gegevens.SPEL)
	var tegels = Gegevens.lees(Gegevens.TEGELS)
	_obj_def = Gegevens.lees(Gegevens.OBJECTEN)
	if spel == null or tegels == null or _obj_def == null:
		return false
	tegel_m = float(spel["tegel_m"])
	tik_dt = 1.0 / float(spel["sim_hz"])
	loop_mps = Gegevens.loop_mps(spel)
	looptempo = float(spel.get("looptempo", 1.0))
	rng.seed = 1
	raster.laad_tegels(tegels)
	var pad: String = kaart_pad if kaart_pad != "" else spel["kaart"]
	var kaart = Gegevens.lees(pad)
	if kaart == null:
		push_error("wereld: kaart ontbreekt, draai sync.ps1 (" + pad + ")")
		return false
	_vul_raster(kaart, tegels)
	_plaats_objecten(kaart)
	if kampvuur == Vector2i.ZERO:
		push_error("wereld: geen kampvuur in de kaart")
		return false
	bereik = Router.bereikbaar(raster, _vrij_naast(kampvuur))
	_bepaal_eiland()
	_maak_dorpelingen()
	tijd_s = float(spel["start_seizoen"]) * float(spel["seizoen_s"]) + float(spel["start_klok_s"])
	return true


func _vul_raster(kaart: Dictionary, tegels: Dictionary) -> void:
	var k: int = kaart["size"][0]
	var r: int = kaart["size"][1]
	raster.maak(k, r)
	var map_kind: Dictionary = tegels["kind_naar_tegel"]
	var wegen: Dictionary = tegels["weg_naar_tegel"]
	for y in r:
		var rij_kind: Array = kaart["kinds"][y]
		var rij_weg: Array = kaart["road"][y]
		for x in k:
			var naam: String = map_kind.get(rij_kind[x], "leeg")
			var i := raster.idx(x, y)
			raster.soort[i] = raster.namen.find(naam)
			var weg := str(int(rij_weg[x]))
			if wegen.has(weg) and naam != "water" and naam != "leeg":
				raster.soort[i] = raster.namen.find(wegen[weg])


func _plaats_objecten(kaart: Dictionary) -> void:
	var defs: Dictionary = _obj_def["objecten"]
	for o in kaart["objects"]:
		var cls := str(int(o["cls"]))
		if not defs.has(cls):
			push_warning("wereld: onbekend object %s (%s)" % [cls, o.get("name", "?")])
			continue
		var d: Dictionary = defs[cls]
		var ob := {"cls": int(o["cls"]), "naam": d["naam"], "model": d["model"], "x": int(o["x"]), "y": int(o["y"]),
			"blokkeert": d["blokkeert"], "voetafdruk": d["voetafdruk"], "state": int(o["state"]), "sex": int(o["sex"]),
			"spawn": d.get("spawn", false)}
		objecten.append(ob)
		if int(o["cls"]) == int(spel["kampvuur_id"]):
			kampvuur = Vector2i(ob["x"], ob["y"])
	# Gegenereerde bomen op bosgrond (kaart heeft maar 42 bomen; de originele dennen zijn onbekend, zie map1.md).
	var dichtheid: float = spel["bos_dichtheid"]
	for y in raster.rijen:
		for x in raster.kolommen:
			if raster.soort_naam(x, y) != "bosgrond":
				continue
			if _hash2(x, y) < dichtheid:
				objecten.append({"cls": 1000, "naam": "boom_bos", "model": defs["1000"]["model"], "x": x, "y": y,
					"blokkeert": true, "voetafdruk": [1, 1], "state": 0, "sex": 0, "spawn": false})
	for ob in objecten:
		if ob["blokkeert"]:
			var vw: int = ob["voetafdruk"][0]
			var vd: int = ob["voetafdruk"][1]
			for dy in vd:
				for dx in vw:
					if raster.in_kaart(ob["x"] + dx, ob["y"] + dy):
						raster.blok[raster.idx(ob["x"] + dx, ob["y"] + dy)] = 1


func _maak_dorpelingen() -> void:
	var sexmap: Dictionary = _obj_def["sex"]
	var n := 0
	for ob in objecten:
		if not ob["spawn"]:
			continue
		n += 1
		var d := Dorpeling.new()
		d.id = n
		d.naam = "dorpeling%d" % n
		d.sex_ruw = ob["sex"]
		var s: Dictionary = sexmap.get(str(ob["sex"]), {"geslacht": "onbekend", "leeftijd": "volwassen"})
		d.geslacht = s["geslacht"]
		d.leeftijd = s["leeftijd"]
		d.zet_tegel(Vector2i(ob["x"], ob["y"]))
		d.anker = kampvuur
		d.wacht = rng.randf_range(1.0, 6.0)
		dorpelingen.append(d)


## Een begaanbare tegel bij een (geblokkeerde) tegel, voor de bereikbaarheidsveeg vanaf het kampvuur.
func _vrij_naast(t: Vector2i) -> Vector2i:
	for r in range(1, 5):
		for dy in range(-r, r + 1):
			for dx in range(-r, r + 1):
				var c := t + Vector2i(dx, dy)
				if raster.loopbaar_v(c):
					return c
	return t


func _bepaal_eiland() -> void:
	var x0 := 9999
	var y0 := 9999
	var x1 := -1
	var y1 := -1
	for y in raster.rijen:
		for x in raster.kolommen:
			if bereik[raster.idx(x, y)] == 1:
				x0 = mini(x0, x)
				y0 = mini(y0, y)
				x1 = maxi(x1, x)
				y1 = maxi(y1, y)
	eiland = Rect2i(x0, y0, x1 - x0 + 1, y1 - y0 + 1)


func _hash2(x: int, y: int) -> float:
	var h: int = ((x * 73856093) ^ (y * 19349663)) & 0x7fffffff
	h = ((h ^ (h >> 13)) * 1274126177) & 0x7fffffff
	h = h ^ (h >> 16)
	return float(h & 0xffff) / 65535.0


# ---------------------------------------------------------------- tijd

func vooruit(dt: float) -> void:
	if gepauzeerd:
		return
	_acc += dt * tempo
	var n := 0
	while _acc >= tik_dt - 1e-9 and n < 200:
		_acc -= tik_dt
		n += 1
		tik(tik_dt)
	if n >= 200:
		_acc = 0.0  # na een lange hapering niet frames lang blijven inhalen


func tik(dt: float) -> void:
	tijd_s += dt
	tik_nr += 1
	for d in dorpelingen:
		d.tick(self, dt)


## 0..1 tussen de vorige en de volgende tik, voor interpolatie in de view.
func alpha() -> float:
	return clampf(maxf(_acc, 0.0) / tik_dt, 0.0, 1.0)


# ---------------------------------------------------------------- klok, seizoen, weer

func seizoen_duur() -> float:
	return float(spel["seizoen_s"])


func dag_nr() -> int:
	return int(tijd_s / seizoen_duur())    # een seizoen = een dag-nacht (beasts-src)


func dag_t() -> float:
	return fmod(tijd_s, seizoen_duur())


func is_nacht() -> bool:
	return dag_t() >= float(spel["dag_s"])


## Spel-uur voor licht en HUD: dag = 05:00 tot 21:00, nacht = 21:00 tot 05:00.
func uur() -> float:
	return fposmod(5.0 + 24.0 * dag_t() / seizoen_duur(), 24.0)


func seizoen() -> int:
	return dag_nr() % 4


func seizoen_naam() -> String:
	return SEIZOENEN[seizoen()]


## Waarde uit een seizoenstabel, in het laatste kwart zacht naar het volgende seizoen.
func _geblend(tabel: Array) -> float:
	var s := seizoen()
	var f := dag_t() / seizoen_duur()
	return lerpf(tabel[s], tabel[(s + 1) % 4], smoothstep(0.7, 1.0, f))


func sneeuw() -> float:
	return _geblend(SNEEUW)


func droog() -> float:
	return _geblend(DROOG)


func kou() -> float:
	return _geblend(KOU)


## Weerhaak: de view zet er regendeeltjes mee aan of uit. -1 automatisch (deterministisch per dag), 0 uit, 1 aan.
func regent() -> bool:
	if regen_handmatig >= 0:
		return regen_handmatig == 1
	var dag := dag_nr()
	if _hash2(dag, 7) >= REGENKANS[seizoen()]:
		return false
	var start := 0.1 + 0.55 * _hash2(dag, 99)
	var f := dag_t() / seizoen_duur()
	return f >= start and f < start + 0.2


# ---------------------------------------------------------------- bevelen

func dorpeling(id: int) -> Dorpeling:
	for d in dorpelingen:
		if d.id == id:
			return d
	return null


## Dichtstbijzijnde begaanbare tegel (op het eiland) bij `t`; (-1,-1) als er geen is binnen 6 tegels.
func dichtstbij_loopbaar(t: Vector2i) -> Vector2i:
	var beste := Vector2i(-1, -1)
	var bd := 1e9
	for dy in range(-6, 7):
		for dx in range(-6, 7):
			var c := t + Vector2i(dx, dy)
			if raster.in_kaart(c.x, c.y) and raster.loopbaar_v(c) and bereik[raster.idx(c.x, c.y)] == 1:
				var d := float(dx * dx + dy * dy)
				if d < bd:
					bd = d
					beste = c
	return beste


## Tegels rondom `doel`, in ringen van dichtbij naar ver (BFS), voor het uitwaaieren van een groep.
func spreid(doel: Vector2i, n: int) -> Array[Vector2i]:
	var uit: Array[Vector2i] = []
	if not raster.loopbaar_v(doel):
		return uit
	var gezien := {doel: true}
	var rij: Array[Vector2i] = [doel]
	var i := 0
	while i < rij.size() and uit.size() < n:
		var t := rij[i]
		i += 1
		uit.append(t)
		for d in 8:
			var nt := t + Vector2i(Raster.DC[d], Raster.DR[d])
			if gezien.has(nt) or not raster.kan_stap(t.x, t.y, nt.x, nt.y):
				continue
			gezien[nt] = true
			rij.append(nt)
	return uit


## Geef een bevel aan de dorpelingen in `ids`. Lopen kan iedereen; "vecht" en "werk" alleen volwassenen.
## Meerdere uitvoerders waaieren uit over tegels rond het doel. Geeft het aantal dat het bevel kreeg.
## ("vecht" en "werk" lopen voorlopig alleen naar het doel; het gedrag volgt met de economie.)
func geef_bevel(ids: Array, soort: String, doel: Vector2i) -> int:
	var uitvoerders: Array[Dorpeling] = []
	for id in ids:
		var d := dorpeling(id)
		if d != null and d.kan_bevel(soort):
			uitvoerders.append(d)
	if uitvoerders.is_empty():
		return 0
	var t := dichtstbij_loopbaar(doel)
	if t.x < 0:
		return 0
	var plekken := spreid(t, uitvoerders.size())
	var over: Array[Dorpeling] = uitvoerders.duplicate()
	var gelukt := 0
	for plek in plekken:
		if over.is_empty():
			break
		var beste: Dorpeling = over[0]
		for d in over:
			if d.pos.distance_squared_to(Vector2(plek)) < beste.pos.distance_squared_to(Vector2(plek)):
				beste = d
		over.erase(beste)
		if beste.geef_bevel(self, soort, plek):
			gelukt += 1
	bevel_gegeven.emit(ids, soort, t)
	return gelukt
