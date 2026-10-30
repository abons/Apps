class_name Voorwerpen
extends RefCounted
## Voorwerpen oprapen en wegbrengen (missie 1 zilveren beker, missie 3 gouden kelk). Een voorwerp is een kaartobject
## met "voorwerp": true in data/objecten.json; het blijft in `Wereld.objecten` (dict) met twee extra sleutels:
## `drager` (dorpeling-id, -1 = ligt op de grond op x,y) en `voorwerp` = true.
## Origineel (M1.MIS, conditie type 12 "object raakt object"): een dorpeling (klasse 103, elk type) die de beker raakt
## heeft hem; raakt de beker (159) de vlag (object 1), dan volgen twee acties: +5.000 kas (actie 0x16) en het object
## verdwijnt (actie 0x17). M3: kelk (172) raakt vlag -> +7.000 en weg. Wat waar heen moet en wat het oplevert staat
## per missie in spel.json `missies.<nr>.voorwerpen`: {"<klasse>": {"naar": "<objectnaam>", "kas": n}}.
## Oprapen = aanraken: wie binnen `RAAK` tegels komt en nog niets draagt, pakt het op (het pakbevel is een loopbevel
## erheen). Afleveren = de drager komt binnen `LEVER` tegels van het doel (eigen object, eigenaar 0).
## Valt de drager weg (geen dorpeling meer met dat id), dan valt het voorwerp op zijn laatste tegel.

const RAAK := 0.75
const LEVER := 1.6


static func alle(w: Wereld) -> Array:
	var uit := []
	for ob in w.objecten:
		if ob.get("voorwerp", false):
			uit.append(ob)
	return uit


## Wat dorpeling `d` draagt, of {}.
static func van(w: Wereld, d: Dorpeling) -> Dictionary:
	for ob in w.objecten:
		if ob.get("voorwerp", false) and int(ob["drager"]) == d.id:
			return ob
	return {}


static func midden(ob: Dictionary) -> Vector2:
	return Vector2(ob["x"], ob["y"]) + Vector2(0.5, 0.5)


## Pakbevel (Bestuur: klik op een voorwerp met een selectie): de dichtste uit `ids` die nog niets draagt loopt erheen.
static func geef_pakbevel(w: Wereld, ids: Array, ob: Dictionary) -> int:
	if not ob.get("voorwerp", false) or int(ob["drager"]) >= 0:
		return 0
	var beste: Dorpeling = null
	for id in ids:
		var d := w.dorpeling(id)
		if d == null or not d.kan_bevel("loop") or not van(w, d).is_empty():
			continue
		if beste == null or d.pos.distance_squared_to(midden(ob)) < beste.pos.distance_squared_to(midden(ob)):
			beste = d
	if beste == null:
		return 0
	return w.geef_bevel([beste.id], "loop", Vector2i(ob["x"], ob["y"]))


static func tik_alle(w: Wereld, _dt: float) -> void:
	var regels: Dictionary = w.missie.get("voorwerpen", {})
	for ob in alle(w):
		var id := int(ob["drager"])
		if id >= 0:
			var d := w.dorpeling(id)
			if d == null:
				laat_vallen(w, ob)
				continue
			var t := d.tegel()
			ob["x"] = t.x
			ob["y"] = t.y
			var regel: Dictionary = regels.get(str(ob["cls"]), {})
			if not regel.is_empty() and _bij_doel(w, d, str(regel["naar"])):
				_lever(w, ob, d, int(regel.get("kas", 0)))
			continue
		for d in w.dorpelingen:
			if not d.binnen and d.pos.distance_to(midden(ob)) <= RAAK and van(w, d).is_empty():
				ob["drager"] = d.id
				w.voorwerp_opgeraapt.emit(ob, d)
				break


static func _bij_doel(w: Wereld, d: Dorpeling, naar: String) -> bool:
	for o in w.objecten:
		if o["naam"] == naar and int(o.get("owner", 0)) == 0 and d.pos.distance_to(midden(o)) <= LEVER:
			return true
	return false


static func _lever(w: Wereld, ob: Dictionary, d: Dorpeling, kas: int) -> void:
	w.kas += kas
	w.objecten.erase(ob)
	w.voorwerp_afgeleverd.emit(ob, d, kas)


## Het voorwerp valt op de tegel van de drager (of de dichtste loopbare ernaast) en ligt weer op de grond.
static func laat_vallen(w: Wereld, ob: Dictionary) -> void:
	var t := Vector2i(ob["x"], ob["y"])
	if not w.raster.loopbaar_v(t):
		var n := w.dichtstbij_loopbaar(t)
		if n.x >= 0:
			t = n
	ob["x"] = t.x
	ob["y"] = t.y
	ob["drager"] = -1
	w.voorwerp_gevallen.emit(ob)
