extends SceneTree
## Besluiten van de gebruiker van 2026-10-31 (spel.json, sim/):
##   godot --headless --path . --script res://test/besluiten_test.gd
## 1. alleen mannen en bouwers bouwen (speler en zelfstandig); M1 met 2 mannen bouwt hut, kippenhok en loods af
## 2. maximale bouwafstand tot het dorp (bouw_afstand), reden "te ver"; weg mag overal
## 3. M1: drinken bij de bron duurt even (drink_s)
## 4. honger: te lang geen eten = langzaam hp eraf en minder geluk; een bruine paddenstoel heft het op
## 6. stilstaan: geen zelfstandige klussen, niet zwerven, tot een nieuw bevel

var fouten := 0


func _initialize() -> void:
	_test_bouwers()
	_test_afstand()
	_test_bron()
	_test_honger()
	_test_stilstaan()
	_test_m1_economie()
	print("besluiten_test: %s" % ("ALLES GOED" if fouten == 0 else "%d FOUT" % fouten))
	quit(1 if fouten > 0 else 0)


func _eerste(w: Wereld, geslacht: String) -> Dorpeling:
	for d in w.dorpelingen:
		if d.volwassen() and d.geslacht == geslacht:
			return d
	return null


func _plek(w: Wereld, soort: StringName, van := 3) -> Plan:
	for r in range(van, 20):
		for dy in range(-r, r + 1):
			for dx in range(-r, r + 1):
				if maxi(absi(dx), absi(dy)) != r:
					continue
				var p := w.maak_plan(soort, w.kampvuur + Vector2i(dx, dy), 0)
				if p != null:
					return p
	return null


func _test_bouwers() -> void:
	var w := Wereld.new()
	w.laad()
	var man := _eerste(w, "man")
	var vrouw := _eerste(w, "vrouw")
	_check(man.kan_bouwen() and man.kan_bevel("werk"), "een man bouwt")
	_check(not vrouw.kan_bouwen() and not vrouw.kan_bevel("werk"), "een vrouw bouwt niet (origineel: geen hamerknop)")
	var p := _plek(w, &"hut")
	_check(p != null and w.plan_zet(p), "hut gezet")
	var geweigerd := []
	w.bevel_geweigerd.connect(func(ids: Array, reden: String) -> void: geweigerd.append(reden))
	_check(w.geef_bouwbevel([vrouw.id], p) == 0 and vrouw.werk_plan == null, "bouwbevel aan een vrouw: geweigerd")
	_check(geweigerd.size() == 1, "melding bij weigeren (%s)" % [geweigerd])
	_check(w.geef_bouwbevel([vrouw.id, man.id], p) == 1 and man.werk_plan == p, "gemengde selectie: alleen de man bouwt")
	# zelfstandig: vrouwen en kinderen nemen geen open plan
	for i in int(20.0 / w.tik_dt):
		w.tik(w.tik_dt)
	for d in w.dorpelingen:
		if d.werk_plan != null:
			_check(d.geslacht == "man" and d.volwassen(), "alleen mannen aan het plan (%s, %s)" % [d.geslacht, d.leeftijd])


func _test_afstand() -> void:
	var w := Wereld.new()
	w.laad()
	w.kas = 99999
	var max_t := int(w.spel["bouw_afstand"]["max_tegels"])
	var dichtbij := _plek(w, &"kippenhok")
	_check(dichtbij != null and w.bouw_reden(dichtbij) == "", "kippenhok bij het kampvuur kan")
	var ver: Plan = null
	for r in range(max_t + 4, 60):
		for dx in [-r, r]:
			for dy in range(-r, r + 1, 3):
				if ver == null:
					var q := Plan.new(&"kippenhok", w.kampvuur + Vector2i(dx, dy), 0, 2, 2)
					if w.kan_bouwen(q) and w.bouw_reden(q) != "":
						ver = q
	_check(ver != null and w.bouw_reden(ver) == Wereld.REDEN_TE_VER, "ver weg: te ver van je gebouwen")
	_check(ver != null and not w.plan_zet(ver), "te ver: niet gezet")
	_check(w.maak_plan(&"kippenhok", ver.tegel, 0) == null if ver != null else false, "maak_plan geeft null als het te ver is")
	_check(w.afstand_tot_dorp(dichtbij) <= max_t, "afstand_tot_dorp dichtbij (%d)" % w.afstand_tot_dorp(dichtbij))
	var weg := Plan.new(&"weg", ver.tegel if ver != null else w.kampvuur, 0, 1, 1)
	_check(w.binnen_bouwafstand(weg), "een weg mag overal (bouw_afstand.uitgezonderd)")


func _test_bron() -> void:
	var w := Wereld.new()
	w.laad()
	var d := _eerste(w, "vrouw")
	d.bevel = {}
	d.route.clear()
	d.dorst = float(w.spel["economie"]["dorst_s"]) + 1.0
	for k in d.trek:
		d.trek[k] = 0.0
	var max_bezig := 0.0
	for i in 900:
		if d.koopt == "water":
			max_bezig = maxf(max_bezig, d.bezig)
		if d.dorst < 1.0:
			break
		w.tik(w.tik_dt)
	_check(d.dorst < 1.0, "missie 1: dorst gelest bij de bron")
	_check(max_bezig >= 1.0, "drinken bij de bron duurt even (%.1f s)" % max_bezig)


func _test_honger() -> void:
	var w := Wereld.new()
	w.laad()
	var c: Dictionary = w.spel["leven"]["honger"]
	var d := _eerste(w, "man")
	w.tik(w.tik_dt)                     # Leven._begin: gezondheid gezet
	d.gezondheid = d.gezondheid_max
	for waar in Wereld.WAREN:
		d.trek[waar] = 0.0
	_check(not Leven.hongerig(w, d), "net gegeten: geen honger")
	for waar in Wereld.WAREN:
		d.trek[waar] = float(c["na_s"]) + 1.0
	_check(Leven.hongerig(w, d), "na honger.na_s zonder eten: honger")
	var hp0 := d.gezondheid
	var geluk0 := d.geluk
	for i in int(30.0 / w.tik_dt):
		for waar in Wereld.WAREN:       # geen winkel in de buurt: blijft hongerig
			d.trek[waar] = float(c["na_s"]) + 1.0
		w.tik(w.tik_dt)
	var verlies := hp0 - d.gezondheid
	var verwacht := float(c["verlies_deel_per_s"]) * d.gezondheid_max * 30.0
	_check(absf(verlies - verwacht) < 0.5, "langzaam hp eraf (%.2f, verwacht %.2f)" % [verlies, verwacht])
	_check(d in w.dorpelingen, "na 30 s honger leeft hij nog")
	_check(d.geluk < geluk0, "honger maakt minder gelukkig (%.3f -> %.3f)" % [geluk0, d.geluk])
	# bruine paddenstoel = voeding: honger weg
	var ob := {"cls": Paddenstoelen.KLASSE, "naam": "paddenstoel", "x": 0, "y": 0, "state": _bruin()}
	w.objecten.append(ob)
	Paddenstoelen.eet(w, d, ob)
	_check(not Leven.hongerig(w, d), "bruine paddenstoel heft de honger op")
	# uiteindelijk dood van de honger
	var doden := []
	w.dorpeling_dood.connect(func(x: Dorpeling, o: String) -> void: doden.append(o))
	d.gezondheid = 1.0
	for i in int(20.0 / w.tik_dt):
		for waar in Wereld.WAREN:
			d.trek[waar] = float(c["na_s"]) + 1.0
		w.tik(w.tik_dt)
		if not d in w.dorpelingen:
			break
	_check(not d in w.dorpelingen and "honger" in doden, "zonder eten sterft hij uiteindelijk (%s)" % [doden])


func _bruin() -> int:
	var soorten: Dictionary = Paddenstoelen.cfg().get("soorten", {})
	for k in soorten:
		if soorten[k] == "voeding":
			return int(k)
	return 2


func _test_stilstaan() -> void:
	var w := Wereld.new()
	w.laad()
	var man := _eerste(w, "man")
	w.kas = 99999
	var p := _plek(w, &"hut")
	w.plan_zet(p)
	_check(w.geef_stilstaan([man.id]) == 1 and man.stil, "stilstaan-bevel")
	var t0 := man.tegel()
	for i in int(30.0 / w.tik_dt):
		w.tik(w.tik_dt)
	_check(man.werk_plan == null and man.tegel() == t0, "staat stil: bouwt niet zelf aan het open plan, zwerft niet (%s -> %s)" % [t0, man.tegel()])
	_check(not man.ledig(), "stilstaand telt niet als ledig (geen klus)")
	w.geef_bevel([man.id], "loop", t0 + Vector2i(1, 0))
	_check(not man.stil, "een nieuw bevel heft stilstaan op")


## M1 met alleen de 2 mannen als bouwers: hut, kippenhok en loods gaan zelfstandig af, en na 20 min is niemand
## van honger dood (het kippenhok verkoopt eieren).
func _test_m1_economie() -> void:
	var w := Wereld.new()
	w.laad()
	var plannen: Array[Plan] = []
	for s in [&"kippenhok", &"hut", &"gereedschapsloods"]:
		var p := _plek(w, s)
		if p != null and w.plan_zet(p):
			plannen.append(p)
	_check(plannen.size() == 3, "drie plannen gezet (%d)" % plannen.size())
	var n0 := w.dorpelingen.size()
	var doden := []
	w.dorpeling_dood.connect(func(x: Dorpeling, o: String) -> void: doden.append(o))
	for i in int(1200.0 / w.tik_dt):
		w.tik(w.tik_dt)
	var af := plannen.filter(func(p: Plan) -> bool: return p.klaar).size()
	_check(af == 3, "2 mannen bouwen zelf alles af (%d van 3)" % af)
	_check(not "honger" in doden, "niemand van honger dood in 20 min (%s)" % [doden])
	print("  m1: %d -> %d dorpelingen, doden %s, kas %d" % [n0, w.dorpelingen.size(), doden, w.kas])


func _check(ok: bool, wat: String) -> void:
	if not ok:
		fouten += 1
		print("FOUT: " + wat)
	else:
		print("ok    " + wat)
