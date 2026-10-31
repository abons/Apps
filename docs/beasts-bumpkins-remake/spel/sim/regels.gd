class_name Regels
extends RefCounted
## Missieregels naar het origineel (Mn.MIS: conditie-records met acties, ../missies.md "Bestandsformaat", ../map4.md).
## Per missie in spel.json `missies.<nr>.regels` = [{id, als: {...}, doe: [{...}, ...]}]; elke regel vuurt een keer.
##   als.type  afgeleverd {klasse}   een voorwerp van die klasse kwam bij zijn doel (sim/voorwerpen.gd, origineel type 10)
##             opgeraapt {klasse}    een dorpeling raakte/pakte een voorwerp van die klasse (type 12)
##             wezen_dood {tegel}    het wezen dat op die kaarttegel begon leeft niet meer (type 6, object vernietigd)
##             aanraken {tegel}      een dorpeling staat op die tegel (type 12 op een triggerplek, klasse 87)
##   doe.type  maak {klasse, tegel}  nieuw object uit objecten.json (actie 0x04: klasse, x, y)
##             open {object}         object met die naam blokkeert niet meer (0x13; de magische poort)
##             weg {klasse, tegels}  objecten van die klasse op die tegels van de kaart (0x17)
## Vallen (spel.json `vallen`): een mijn (klasse 37) gaat af als een dorpeling erop stapt; vuur (klasse 7) brandt een
## tijd, doet schade in de buurt, een bouwer dooft het, en met olie (61) eronder zet het de mijnen eromheen af.
## Besluit gebruiker 2026-10-31: een mijn is meteen dodelijk (vallen.mijn.dodelijk), direct contact met het vuur (binnen
## vallen.vuur.kern) ook; de rand van het vuur doet schade per s; een spies (klasse 36, vanaf M6) doet schade, overleefbaar.
## Geen signalen naar de Wereld toe (die zouden de Wereld vasthouden): alles wordt per tik afgelezen.

const RAAK := 0.75


static func tik(w: Wereld, dt: float) -> void:
	var regels: Array = w.missie.get("regels", [])
	for r in regels:
		var id := String(r.get("id", ""))
		if w.regels_af.has(id) or not _waar(w, r.get("als", {})):
			continue
		w.regels_af[id] = w.tijd_s
		for a in r.get("doe", []):
			_doe(w, a)
		w.regel_gevuurd.emit(id)
	_mijnen(w)
	_vuren(w, dt)
	_spiezen(w, dt)


static func _waar(w: Wereld, als: Dictionary) -> bool:
	match String(als.get("type", "")):
		"afgeleverd":
			return w.afgeleverd.has(int(als["klasse"]))
		"opgeraapt":
			return w.opgeraapt.has(int(als["klasse"]))
		"wezen_dood":
			var t := Vector2i(int(als["tegel"][0]), int(als["tegel"][1]))
			for wf in w.wolven:
				if wf.kaart_tegel == t and wf.leeft():
					return false
			return true
		"aanraken":
			return aangeraakt(w, Vector2i(int(als["tegel"][0]), int(als["tegel"][1])))
	return false


## Staat er een dorpeling (buiten) binnen RAAK tegels van het midden van tegel `t`.
static func aangeraakt(w: Wereld, t: Vector2i) -> bool:
	var m := Vector2(t) + Vector2(0.5, 0.5)
	for d in w.dorpelingen:
		if not d.binnen and d.pos.distance_to(m) <= RAAK:
			return true
	return false


static func _doe(w: Wereld, a: Dictionary) -> void:
	match String(a.get("type", "")):
		"maak":
			maak(w, int(a["klasse"]), Vector2i(int(a["tegel"][0]), int(a["tegel"][1])))
		"open":
			for ob in w.objecten:
				if ob["naam"] == String(a["object"]) and not ob.get("open", false):
					ob["open"] = true
					ob["blokkeert"] = false
					_herbereken_blok(w, Vector2i(ob["x"], ob["y"]))
					w.object_veranderd.emit(ob)
			_herbereken_bereik(w)
		"weg":
			var tegels := {}
			for t in a.get("tegels", []):
				tegels[Vector2i(int(t[0]), int(t[1]))] = true
			for ob in w.objecten.duplicate():
				if int(ob["cls"]) == int(a["klasse"]) and tegels.has(Vector2i(ob["x"], ob["y"])):
					verwijder(w, ob)
			_herbereken_bereik(w)


## Nieuw object van klasse `cls` op tegel `t` (zelfde vorm als Wereld._plaats_objecten). Geeft het object.
static func maak(w: Wereld, cls: int, t: Vector2i) -> Dictionary:
	var d: Dictionary = w._obj_def["objecten"].get(str(cls), {})
	if d.is_empty():
		push_warning("regels: klasse %d staat niet in objecten.json" % cls)
		return {}
	var ob := {"cls": cls, "naam": d["naam"], "model": d["model"], "x": t.x, "y": t.y, "blokkeert": d["blokkeert"],
		"voetafdruk": d["voetafdruk"], "state": 0, "sex": 0, "spawn": false, "owner": 0, "dynamisch": d.get("dynamisch", false)}
	if d.get("voorwerp", false):
		ob["voorwerp"] = true
		ob["drager"] = -1
	if ob["naam"] == "vuur":
		ob["brand_s"] = float(_vallen(w, "vuur").get("duur_s", 20.0))
		ob["puls"] = 0.0
		ob["ontstoken"] = false
	w.objecten.append(ob)
	if ob["blokkeert"]:
		w.raster.blok[w.raster.idx(t.x, t.y)] = 1
	w.object_erbij.emit(ob)
	return ob


static func verwijder(w: Wereld, ob: Dictionary) -> void:
	w.objecten.erase(ob)
	if ob.get("blokkeert", false):
		_herbereken_blok(w, Vector2i(ob["x"], ob["y"]))
	w.object_weg.emit(ob)


## Blokkade van tegel `t` opnieuw uit de objecten die er (nog) staan; een gebouw of plan blijft blokkeren.
static func _herbereken_blok(w: Wereld, t: Vector2i) -> void:
	var dicht := false
	for ob in w.objecten:
		if ob.get("blokkeert", false) and ob["x"] == t.x and ob["y"] == t.y:
			dicht = true
	if w.plan_op(t) != null or w.gebouw_op(t) != null:
		dicht = true
	w.raster.blok[w.raster.idx(t.x, t.y)] = 1 if dicht else 0


static func _herbereken_bereik(w: Wereld) -> void:
	w.bereik = Router.bereikbaar(w.raster, w._vrij_naast(w.kampvuur))


static func _vallen(w: Wereld, soort: String) -> Dictionary:
	return w.spel.get("vallen", {}).get(soort, {})


# ---------------------------------------------------------------- vallen: mijnen en vuur

static func _mijnen(w: Wereld) -> void:
	var c := _vallen(w, "mijn")
	var raak := float(c.get("raak", 0.6))
	for ob in w.objecten.duplicate():
		if ob["naam"] != "mijn":
			continue
		var m := Vector2(ob["x"], ob["y"]) + Vector2(0.5, 0.5)
		for d in w.dorpelingen:
			if not d.binnen and d.pos.distance_to(m) <= raak:
				ontplof(w, ob)
				break


## Een mijn gaat af: schade aan elke dorpeling binnen `straal`, mijn weg.
static func ontplof(w: Wereld, ob: Dictionary) -> void:
	if not ob in w.objecten:
		return
	var c := _vallen(w, "mijn")
	var t := Vector2i(ob["x"], ob["y"])
	var m := Vector2(t) + Vector2(0.5, 0.5)
	verwijder(w, ob)
	w.ontploffing.emit(t)
	for d in w.dorpelingen.duplicate():
		if not d.binnen and d.pos.distance_to(m) <= float(c.get("straal", 1.5)):
			d.raak(w, d.gezondheid if bool(c.get("dodelijk", false)) else float(c.get("schade", 60)), "mijn")


static func _vuren(w: Wereld, dt: float) -> void:
	var c := _vallen(w, "vuur")
	for ob in w.objecten.duplicate():
		if ob["naam"] != "vuur":
			continue
		var m := Vector2(ob["x"], ob["y"]) + Vector2(0.5, 0.5)
		ob["brand_s"] = float(ob["brand_s"]) - dt
		for d in w.dorpelingen:     # origineel 0x448f78: een bouwer die het vuur raakt, dooft het
			if d.rol == "bouwer" and not d.binnen and d.pos.distance_to(m) <= RAAK + 0.5:
				ob["brand_s"] = 0.0
		if float(ob["brand_s"]) <= 0.0:
			verwijder(w, ob)
			continue
		var kern := float(c.get("kern", 0.0))
		for d in w.dorpelingen.duplicate():     # direct contact met de vlam: meteen dood (een bouwer dooft hem hierboven al)
			if not d.binnen and d.pos.distance_to(m) <= kern:
				d.raak(w, d.gezondheid, "vuur")
		var oud := float(ob["puls"])
		ob["puls"] = oud + dt
		if floor(oud) != floor(float(ob["puls"])):      # elke seconde schade
			for d in w.dorpelingen.duplicate():
				if not d.binnen and d.pos.distance_to(m) <= float(c.get("straal", 1.2)):
					d.raak(w, float(c.get("schade_per_s", 10)), "vuur")
		if not ob["ontstoken"] and float(ob["puls"]) >= float(c.get("ontsteek_s", 2.0)) and _olie_op(w, Vector2i(ob["x"], ob["y"])):
			ob["ontstoken"] = true
			for mo in w.objecten.duplicate():
				if mo["naam"] == "mijn" and (Vector2(mo["x"], mo["y"]) + Vector2(0.5, 0.5)).distance_to(m) <= float(c.get("mijn_straal", 2.5)):
					ontplof(w, mo)


static func _olie_op(w: Wereld, t: Vector2i) -> bool:
	for ob in w.objecten:
		if ob["naam"] == "olie" and ob["x"] == t.x and ob["y"] == t.y:
			return true
	return false


## Spies (spike trap, klasse 36; objecten.json naam "spies"): een dorpeling die binnen `raak` komt krijgt `schade`
## (overleefbaar, besluit gebruiker 2026-10-31); daarna doet de val `herlaad_s` niets.
static func _spiezen(w: Wereld, dt: float) -> void:
	var c := _vallen(w, "spies")
	if c.is_empty():
		return
	for ob in w.objecten:
		if ob["naam"] != "spies":
			continue
		if float(ob.get("herlaad", 0.0)) > 0.0:
			ob["herlaad"] = float(ob["herlaad"]) - dt
			continue
		var m := Vector2(ob["x"], ob["y"]) + Vector2(0.5, 0.5)
		for d in w.dorpelingen.duplicate():
			if not d.binnen and d.pos.distance_to(m) <= float(c.get("raak", 0.6)):
				d.raak(w, float(c.get("schade", 40)), "spies")
				ob["herlaad"] = float(c.get("herlaad_s", 5.0))
				break
