extends SceneTree
## Werkplekken op de bouwplaats (Wereld.werk_plekken, gebruiker 2026-10-31: "units mogen niet op dezelfde plek bouwen
## en moeten bij de log zagen en bij de stenen hakken"). Draaien:
##   godot --headless --path . --script res://test/bouw_plek_test.gd
## Zes bouwers op een hut: elk een eigen plek, een zaagt bij de zaagbok, een hakt bij de steenhoop, de rest hamert aan
## de gevel; een voor een toegewezen (zoals _kies_klus) ook verschillend; hek: twee man niet op dezelfde tegel;
## twee werelden geven dezelfde indeling (geen rng).

var fouten := 0


func _initialize() -> void:
	var a := _hut_met_bouwers(true)
	var b := _hut_met_bouwers(false)
	_check(a == b, "dezelfde indeling, of ze nu samen of een voor een komen: %s" % [a])
	_test_hek()
	print("bouw_plek_test: %s" % ("ALLES GOED" if fouten == 0 else "%d FOUT" % fouten))
	quit(1 if fouten > 0 else 0)


## Zet een hut naast het kampvuur, maakt iedereen volwassen en stuurt ze erheen (samen of een voor een); controleert
## plekken, soorten en aankomst. Geeft [soort, punt] per id voor de vergelijking.
func _hut_met_bouwers(samen: bool) -> Array:
	var w := Wereld.new()
	w.laad()
	for d in w.dorpelingen:
		d.leeftijd = "volwassen"
	var p: Plan = null
	for r in 10:
		for dy in range(-r, r + 1):
			for dx in range(-r, r + 1):
				if p == null and maxi(absi(dx), absi(dy)) == r:
					p = w.maak_plan(&"hut", w.kampvuur + Vector2i(4 + dx, 4 + dy), 0)
	w.kas = 99999
	_check(p != null and w.plan_zet(p), "hut gezet")
	p.bouwtijd_s = 9999.0          # niet af terwijl ze er nog heen lopen
	_check(p.stapels.size() == 2, "zaagbok en steenhoop liggen (%s)" % [p.stapels])
	var ids := []
	for d in w.dorpelingen:
		ids.append(d.id)
	var n := 0
	if samen:
		n = w.geef_bouwbevel(ids, p)
	else:
		for id in ids:
			n += w.geef_bouwbevel([id], p)
	_check(n == ids.size(), "%d van %d aan het werk (%s)" % [n, ids.size(), "samen" if samen else "een voor een"])
	var soorten := {}
	for d in w.dorpelingen:
		soorten[d.werk_soort] = soorten.get(d.werk_soort, 0) + 1
	_check(soorten.get(&"zagen", 0) == 1 and soorten.get(&"houweel", 0) == 1 and soorten.get(&"bouwen", 0) == ids.size() - 2,
			"een zaagt, een hakt, de rest hamert: %s" % [soorten])
	var ds := w.dorpelingen
	var dubbel := 0
	for i in ds.size():
		for j in range(i + 1, ds.size()):
			if ds[i].werk_punt.distance_to(ds[j].werk_punt) < Wereld.WERKPLEK_BEZET:
				dubbel += 1
	_check(dubbel == 0, "niemand deelt een werkplek")
	# de zager staat bij de zaagbok, de hakker bij de steenhoop (binnen 0,6 tegel = 1,2 m van het midden), hamerplekken
	# buiten de voetafdruk naast de gevel
	var r := p.afdruk()
	for d in ds:
		var t := Vector2i(int(floor(d.werk_punt.x)), int(floor(d.werk_punt.y)))
		match d.werk_soort:
			&"zagen":
				_check(d.werk_punt.distance_to(Vector2(p.stapels[0]) + Vector2(0.5, 0.5)) < 0.6, "zager bij de zaagbok")
			&"houweel":
				_check(d.werk_punt.distance_to(Vector2(p.stapels[1]) + Vector2(0.5, 0.5)) < 0.6, "hakker bij de steenhoop")
			_:
				_check(not r.has_point(t) and not t in p.stapels and t != p.deur_tegel(), "hamerplek %s buiten de voetafdruk, niet op stapel of deur" % [t])
				_check(d.werk_kijk.is_finite() and d.werk_kijk.distance_to(d.werk_punt) < 1.0, "hamert naar de gevel")
	# lopen tot iedereen er is
	for i in int(40.0 / w.tik_dt):
		w.tik(w.tik_dt)
	var aan := 0
	for d in ds:
		if d.bouwt and d.pos.distance_to(d.werk_punt) < 0.02:
			aan += 1
	_check(aan == ds.size(), "iedereen staat op zijn plek en werkt (%d/%d)" % [aan, ds.size()])
	var uit := []
	for d in ds:
		uit.append([d.id, d.werk_soort, d.werk_punt.snapped(Vector2(0.01, 0.01))])
	return uit


## Hek (1x1, geen stapels): twee man op een plan, een voor een toegewezen, staan niet op dezelfde tegel.
func _test_hek() -> void:
	var w := Wereld.new()
	w.laad()
	w.kas = 99999
	w.alles_open = true
	var p: Plan = null
	for r in 10:
		for dy in range(-r, r + 1):
			for dx in range(-r, r + 1):
				if p == null and maxi(absi(dx), absi(dy)) == r:
					p = w.maak_plan(&"hek", w.kampvuur + Vector2i(3 + dx, -3 + dy), 0)
	_check(p != null and w.plan_zet(p), "hek gezet")
	_check(p.stapels.is_empty(), "hek: geen stapels")
	var vol: Array[Dorpeling] = []
	for d in w.dorpelingen:
		if d.volwassen():
			vol.append(d)
	w.geef_bouwbevel([vol[0].id], p)
	w.geef_bouwbevel([vol[1].id], p)
	_check(vol[0].werk_punt == Vector2(p.tegel) + Vector2(0.5, 0.5), "de eerste bouwt op de hektegel")
	_check(Vector2i(vol[1].werk_punt.floor()) != p.tegel and vol[0].werk_punt.distance_to(vol[1].werk_punt) >= 0.5,
			"de tweede op de tegel ernaast (%s, %s)" % [vol[0].werk_punt, vol[1].werk_punt])
	_check(vol[1].werk_soort == &"bouwen", "hek: hameren")


func _check(ok: bool, wat: String) -> void:
	print(("ok   " if ok else "FOUT ") + wat)
	if not ok:
		fouten += 1
