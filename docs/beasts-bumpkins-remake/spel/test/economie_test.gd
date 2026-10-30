extends SceneTree
## Headless test prijzen, geluk en misdaad (sim/handel.gd, view/prijzen.gd):
## godot --headless --path . --script res://test/economie_test.gd
## Prijs omhoog = meer kas per verkoop en lager geluk; misdaad alleen als de missie het aan heeft; het prijzenscherm
## pauzeert de sim en zet hem bij het sluiten weer aan (maar niet als hij al op pauze stond).

var fouten := 0


func _initialize() -> void:
	var w := Wereld.new()
	_check(w.laad(), "missie 1 laadt")
	var start := w.handel.basis("brood")
	_check(start == 50 and w.handel.prijs("brood") == start, "startprijs brood = basis uit het origineel (%d)" % start)
	_check(w.handel.prijs("ei") == 80 and w.handel.prijs("melk") == 100, "startprijs ei 80, melk 100 (origineel)")
	_check(w.handel.prijs_min("ei") == 0 and w.handel.prijs_max("ei") == 160, "schuif ei 0..2 x basis (%d..%d)" % [w.handel.prijs_min("ei"), w.handel.prijs_max("ei")])
	_check(absf(w.handel.deel("ei") - 0.5) < 0.001, "startprijs = midden van de schuif")
	_check(absf(w.handel.prijsdruk()) < 0.001, "alles op de basis -> prijsdruk 0")
	var molen := _bouw(w, &"molen")
	# verkoop tegen de startprijs en tegen een hogere
	var d: Dorpeling = w.dorpelingen[0]
	var bij_start := _verkoop(w, d, molen)
	_check(bij_start == start, "verkoop brengt de prijs op (%d)" % bij_start)
	w.handel.zet_prijs("brood", start + 4)
	var bij_hoog := _verkoop(w, d, molen)
	_check(bij_hoog == start + 4 and bij_hoog > bij_start, "prijs omhoog -> meer kas per verkoop (%d > %d)" % [bij_hoog, bij_start])
	_check(w.handel.zet_prijs("brood", 999) == w.handel.prijs_max("brood"), "prijs begrensd op het maximum")
	_check(w.handel.zet_prijs("brood", -5) == w.handel.prijs_min("brood"), "prijs begrensd op het minimum")
	_check(w.handel.zet_deel("melk", 1.0) == 200, "schuif helemaal rechts -> melk 2 x basis")

	# geluk: twee dorpen, een met alles goedkoop en een met alles duur, 200 s
	var goedkoop := _dorp(0.0)
	var duur := _dorp(1.0)
	var g0 := goedkoop.handel.dorp_geluk(goedkoop)
	var g1 := duur.handel.dorp_geluk(duur)
	_check(g1 < g0 - 0.5, "hoge prijzen -> lager geluk (%.2f < %.2f)" % [g1, g0])
	_check(g0 > 0.95, "lage prijzen -> tevreden (%.2f)" % g0)

	# misdaad: missie 1 heeft het niet, dus ook bij geluk 0 niets
	_check(not duur.handel.misdaad_aan(duur), "missie 1: misdaad uit")
	_loop(duur, 300.0)
	_check(duur.handel.totaal_misdaden() == 0, "misdaad uit: geen misdaden bij laag geluk (%d)" % duur.handel.totaal_misdaden())
	# aan (zoals missie 13 in het origineel): dan wel
	duur.missie["misdaad"] = {"aan": true}
	var soorten: Array = []
	duur.handel.misdaad.connect(func(s: String, _a: Dorpeling, _b: Dorpeling) -> void: soorten.append(s))
	_loop(duur, 600.0)
	_check(duur.handel.totaal_misdaden() > 0, "misdaad aan: misdaden bij laag geluk (%d: %s)" % [duur.handel.totaal_misdaden(), duur.handel.misdaden])
	_check(soorten.size() == duur.handel.totaal_misdaden(), "signaal per misdaad")
	duur.missie.erase("misdaad")   # spel.json kan gedeeld zijn tussen werelden (Gegevens)
	# geen misdaad bij tevreden mensen, ook als het aan staat
	goedkoop.missie = goedkoop.missie.duplicate()
	goedkoop.missie["misdaad"] = {"aan": true}
	_loop(goedkoop, 300.0)
	_check(goedkoop.handel.totaal_misdaden() == 0, "misdaad aan maar tevreden dorp: geen misdaden")
	# mishandeling raakt het slachtoffer, misdaad maakt iedereen ongelukkiger
	var w3 := _dorp(1.0)
	var dader: Dorpeling = null
	var slachtoffer: Dorpeling = null
	for x in w3.dorpelingen:
		if x.volwassen():
			if dader == null:
				dader = x
			elif slachtoffer == null:
				slachtoffer = x
	slachtoffer.zet_tegel(dader.tegel())
	for x in w3.dorpelingen:
		x.geluk = 0.5
	var hp: float = slachtoffer.gezondheid
	var soort := ""
	var n := 0
	while soort != "mishandeling" and n < 200:
		for x in w3.dorpelingen:
			x.geluk = 0.5
		soort = w3.handel.pleeg(w3, dader, 0.9)
		n += 1
	_check(soort == "mishandeling", "mishandeling komt voor bij grote ernst")
	_check(slachtoffer.gezondheid < hp, "mishandeling kost het slachtoffer gezondheid (%.1f < %.1f)" % [slachtoffer.gezondheid, hp])
	_check(dader.geluk < 0.5, "misdaad maakt het dorp ongelukkiger (%.2f)" % dader.geluk)

	# het prijzenscherm pauzeert de sim
	var scherm := Prijzenscherm.new()
	root.add_child(scherm)
	scherm.bouw(w)
	w.gepauzeerd = false
	scherm.open()
	_check(w.gepauzeerd and scherm.visible, "scherm open -> sim op pauze")
	var t := w.tijd_s
	w.vooruit(1.0)
	_check(w.tijd_s == t, "op pauze loopt de tijd niet")
	var melk := w.handel.zet_prijs("melk", w.handel.basis("melk"))
	scherm.zet("melk", melk + w.handel.stap("melk"))
	_check(w.handel.prijs("melk") == melk + 10, "+ in het scherm zet de prijs (stap 0,1 x basis = %d)" % w.handel.stap("melk"))
	scherm.sluit()
	_check(not w.gepauzeerd and not scherm.visible, "scherm dicht -> sim loopt weer")
	w.gepauzeerd = true
	scherm.open()
	scherm.sluit()
	_check(w.gepauzeerd, "stond hij al op pauze, dan blijft dat zo")
	scherm.free()

	print("ALLES OK" if fouten == 0 else "%d FOUT(EN)" % fouten)
	quit(0 if fouten == 0 else 1)


## Missie 1 met alle schuiven op deel `f` (0 = min, 1 = max), 200 s gedraaid.
func _dorp(f: float) -> Wereld:
	var w := Wereld.new()
	w.laad()
	for waar in Wereld.WAREN:
		w.handel.zet_deel(waar, f)
	_loop(w, 200.0)
	return w


## Laat `d` een brood kopen in `molen` (voorraad aangevuld); geeft wat de kas erbij kreeg.
func _verkoop(w: Wereld, d: Dorpeling, molen: Plan) -> int:
	molen.voorraad = maxi(molen.voorraad, 1)
	d.draagt = ""
	d.klus = molen
	d.koopt = "brood"
	var kas := w.kas
	w.klus_af(d)
	return w.kas - kas


func _loop(w: Wereld, s: float) -> void:
	for i in int(ceil(s / w.tik_dt)):
		w.tik(w.tik_dt)


## Zet een plan van `soort` bij het kampvuur en rondt het in een tik af (zoals test/hint_test.gd).
func _bouw(w: Wereld, soort: StringName) -> Plan:
	w.alles_open = true
	w.kas = maxi(w.kas, 5000)
	for r in range(3, 20):
		for dy in range(-r, r + 1):
			for dx in range(-r, r + 1):
				if maxi(absi(dx), absi(dy)) != r:
					continue
				var p := w.maak_plan(soort, w.kampvuur + Vector2i(dx, dy), 0)
				if p != null and w.plan_zet(p):
					p.voortgang = 1.0
					w.tik(w.tik_dt)
					_check(p.klaar, "%s afgebouwd" % soort)
					return p
	_check(false, "geen plek voor %s" % soort)
	return null


func _check(ok: bool, wat: String) -> void:
	if ok:
		print("  ok   ", wat)
	else:
		print("  FOUT ", wat)
		fouten += 1
