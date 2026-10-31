extends SceneTree
## Headless test paddenstoelen (sim/paddenstoelen.gd): godot --headless --path . --script res://test/paddenstoel_test.gd
## Missie 1: een man erheen sturen = opeten. Rood geneest, bruin is voeding (trek 0, geluk omhoog), blauw mana (nog geen
## tovenaar: alleen weg), wit dodelijk. Wie niet gestuurd is eet niet; 120 s zonder bevelen eet niemand er een.
## Maat: kniehoogte (objecten.json schaal x 0,49 m-glb).

var fouten := 0
var gegeten: Array = []    # [ob, d, effect]


func _initialize() -> void:
	var objn: Dictionary = Gegevens.lees(Gegevens.OBJECTEN)["objecten"]["83"]
	var maat := float(objn["schaal"]) * 0.49
	_check(maat >= 0.35 and maat <= 0.6, "paddenstoel op kniehoogte (%.2f m)" % maat)

	# 1. zonder bevelen eet niemand (werk en zwerven lopen er langs), en geen paddenstoel naast een kampvuur (anker)
	for m in [1, 2, 3, 4]:
		var w0 := Wereld.new()
		w0.laad("", m)
		for ob in w0.objecten:
			if int(ob["cls"]) == 83:
				var t := Vector2i(ob["x"], ob["y"])
				_check(maxi(absi(t.x - w0.kampvuur.x), absi(t.y - w0.kampvuur.y)) > 1, "M%d paddenstoel %s niet naast het kampvuur" % [m, t])
	var wv := Wereld.new()
	wv.laad()
	var n0 := _aantal(wv)
	for i in int(120.0 / wv.tik_dt):
		wv.tik(wv.tik_dt)
	_check(_aantal(wv) == n0, "120 s zonder bevelen: alle %d paddenstoelen staan er nog (%d)" % [n0, _aantal(wv)])

	# 2. per kleur een man erheen sturen
	_check(_proef("heel", 0), "rood geneest")
	_check(_proef("voeding", 2), "bruin voedt")
	_check(_proef("mana", 1), "blauw: mana of niets")
	_check(_proef("dood", 6), "wit doodt")

	# 3. voeding direct: geluk + voeding_geluk
	var w := Wereld.new()
	w.laad()
	var d: Dorpeling = w.dorpelingen[0]
	d.geluk = 0.3
	var ob := _paddenstoel(w, 3)
	Paddenstoelen.eet(w, d, ob)
	_check(is_equal_approx(d.geluk, 0.4), "voeding: geluk 0,3 -> 0,4 (%.2f)" % d.geluk)
	_check(not ob in w.objecten, "opgegeten = weg")

	# 4. niet gestuurd: een man met een loopbevel ver weg, naast een paddenstoel gezet, eet niet
	w = Wereld.new()
	w.laad()
	ob = _paddenstoel(w, 6)
	var man := _man(w)
	w.geef_bevel([man.id], "loop", w.dichtstbij_loopbaar(w.kampvuur))
	man.pos = Paddenstoelen.midden(ob)
	w.tik(w.tik_dt)
	_check(ob in w.objecten and man.leeft(), "langslopen (bevel elders): niet gegeten")

	print("paddenstoel_test: %s (%d fouten)" % ["OK" if fouten == 0 else "FOUT", fouten])
	quit(1 if fouten > 0 else 0)


func _proef(effect: String, state: int) -> bool:
	var w := Wereld.new()
	w.laad()
	gegeten.clear()
	w.paddenstoel_gegeten.connect(func(o: Dictionary, dd: Dorpeling, e: String) -> void: gegeten.append([o, dd, e]))
	var doden: Array = []
	w.dorpeling_dood.connect(func(dd: Dorpeling, oorzaak: String) -> void: doden.append([dd, oorzaak]))
	var ob := _paddenstoel(w, state)
	var man := _man(w)
	w.tik(w.tik_dt)                 # eerste tik zet de gezondheid per rol (sim/leven.gd)
	var hp_max := man.gezondheid_max
	man.gezondheid = 5.0
	for waar in Wereld.WAREN:
		man.trek[waar] = 100.0
	var n := w.geef_bevel([man.id], "loop", Vector2i(ob["x"], ob["y"]))
	_check(n == 1, "%s: loopbevel naar de paddenstoel" % effect)
	var tikken := 0
	while gegeten.is_empty() and tikken < 4000:
		w.tik(w.tik_dt)
		tikken += 1
	if gegeten.is_empty():
		print("  %s: niet gegeten na %.0f s" % [effect, tikken * w.tik_dt])
		return false
	var g: Array = gegeten[0]
	var ok: bool = g[0] == ob and g[1] == man and g[2] == effect and not ob in w.objecten
	match effect:
		"heel":
			ok = ok and is_equal_approx(man.gezondheid, hp_max) and man.leeft()
			print("  heel: gezondheid 5 -> %.0f (max %.0f)" % [man.gezondheid, hp_max])
		"voeding":
			for waar in Wereld.WAREN:
				ok = ok and float(man.trek.get(waar, 99.0)) < 1.0
			ok = ok and man.leeft()
		"mana":
			ok = ok and man.leeft() and man.gezondheid < hp_max * 0.5     # niet geheeld (wel wat herstel onderweg)
		"dood":
			ok = ok and not man.leeft() and not man in w.dorpelingen and doden.size() == 1 and doden[0][1] == "paddenstoel"
	print("  %s: gegeten na %.1f s, %s" % [effect, tikken * w.tik_dt, "goed" if ok else "FOUT"])
	return ok


## De paddenstoel van missie 1 op (101,59), met kaart-state `state` (kleur).
func _paddenstoel(w: Wereld, state: int) -> Dictionary:
	for ob in w.objecten:
		if int(ob["cls"]) == 83 and Vector2i(ob["x"], ob["y"]) == Vector2i(101, 59):
			ob["state"] = state
			return ob
	_check(false, "paddenstoel op (101,59)")
	return {}


func _man(w: Wereld) -> Dorpeling:
	for d in w.dorpelingen:
		if d.volwassen() and d.geslacht == "man":
			return d
	return w.dorpelingen[0]


func _aantal(w: Wereld) -> int:
	var n := 0
	for ob in w.objecten:
		if int(ob["cls"]) == 83:
			n += 1
	return n


func _check(ok: bool, wat: String) -> void:
	if not ok:
		fouten += 1
		print("FOUT: " + wat)
	else:
		print("ok   " + wat)
