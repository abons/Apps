class_name Paddenstoelen
extends RefCounted
## Paddenstoelen eten (kaartklasse 83). Statisch op Wereld + Dorpeling, zoals Voorwerpen en Leven.
## Origineel: de kaart-`state` (0-6) kiest het frame van poison.mfb (rood met stippen, blauw met stippen, drie bruine,
## grijsgroen, wit; frame 7 = afgegeten stompje). Het exe laadt ook ueat.mfb (een dorpeling die eet). Wat elke soort
## doet staat niet in de bestanden: volgens de gebruiker (2026-10-31) geneest rood, is bruin voeding, geeft blauw de
## tovenaar mana en is wit dodelijk. Tabel en getallen: data/objecten.json klasse 83 `eten`.
## Wie eet: een dorpeling die de speler erheen stuurde (loopbevel naar de paddenstoeltegel, of na dat bevel met zijn
## anker daar) en binnen `raak` tegels komt. Wie toevallig langsloopt (werk, zwerven) laat hem staan, zodat de
## witte niet zomaar iemand doodt. Opgegeten = uit Wereld.objecten, signaal Wereld.paddenstoel_gegeten (view haalt de node weg).

const KLASSE := 83


static func cfg() -> Dictionary:
	return Gegevens.lees(Gegevens.OBJECTEN)["objecten"][str(KLASSE)].get("eten", {})


## Het effect van een paddenstoel: "heel", "voeding", "mana", "dood" of "" (onbekend).
static func effect(ob: Dictionary) -> String:
	return str(cfg().get("soorten", {}).get(str(int(ob.get("state", 0))), ""))


static func midden(ob: Dictionary) -> Vector2:
	return Vector2(ob["x"], ob["y"]) + Vector2(0.5, 0.5)


static func tik_alle(w: Wereld, _dt: float) -> void:
	var c := cfg()
	var raak := float(c.get("raak", 0.75))
	for ob in w.objecten.duplicate():
		if int(ob["cls"]) != KLASSE:
			continue
		var t := Vector2i(ob["x"], ob["y"])
		for d in w.dorpelingen:
			if d.binnen or not d.leeft() or d.pos.distance_to(midden(ob)) > raak or not _gestuurd(d, t):
				continue
			eet(w, d, ob)
			break


## Door de speler naar tegel t gestuurd: loopbevel met doel t, of net aangekomen (bevel af, anker op t). Precies de
## tegel: wie naast de paddenstoel gezet wordt (een groep krijgt plekken rondom, Wereld.spreid) eet niet.
static func _gestuurd(d: Dorpeling, t: Vector2i) -> bool:
	if d.bevel.get("soort", "") == "loop":
		return d.bevel["doel"] == t
	return d.bevel.is_empty() and d.anker == t


## `d` eet paddenstoel `ob` op: het effect, en de paddenstoel is weg.
static func eet(w: Wereld, d: Dorpeling, ob: Dictionary) -> void:
	var c := cfg()
	var e := effect(ob)
	w.objecten.erase(ob)
	match e:
		"heel":
			d.gezondheid = minf(d.gezondheid_max, d.gezondheid + float(c.get("heel_deel", 1.0)) * d.gezondheid_max)
		"voeding":
			for waar in Wereld.WAREN:
				d.trek[waar] = 0.0
			d.geluk = minf(1.0, d.geluk + float(c.get("voeding_geluk", 0.1)))
		"mana":
			if "mana" in d:      # nog geen tovenaar in de remake: dan alleen opgegeten
				d.set("mana", float(d.get("mana")) + float(c.get("mana", 20)))
	w.paddenstoel_gegeten.emit(ob, d, e)
	if e == "dood":
		d.sterf(w, "paddenstoel")
