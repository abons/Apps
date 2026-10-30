extends SceneTree
## Headless simtest mist van oorlog (sim/mist.gd): godot --headless --path . --script res://test/mist_test.gd
## Start verkend rond vlag en kampvuur, ver weg nog zwart; lopen verkent en verkend blijft verkend; `leeg` wordt nooit
## verkend, ook niet als alles om een dorpeling heen open gaat; uit = alles zichtbaar; missie 1-3 alle drie.

var fouten := 0


func _initialize() -> void:
	for nr in [1, 2, 3]:
		_test_start(nr)
	_test_lopen()
	_test_leeg()
	_test_uit()
	print("---- ", "ALLES OK" if fouten == 0 else "%d FOUT(EN)" % fouten)
	quit(0 if fouten == 0 else 1)


func _test_start(nr: int) -> void:
	var w := Wereld.new()
	_check(w.laad("", nr), "missie %d laadt" % nr)
	var m := w.mist
	_check(m.is_verkend(w.kampvuur), "M%d kampvuur verkend" % nr)
	var vlag := Mist.eigen_vlag(w)
	_check(vlag.x >= 0 and m.is_verkend(vlag), "M%d eigen vlag verkend (%s)" % [nr, vlag])
	for d in w.dorpelingen:
		_check(m.is_verkend(d.tegel()), "M%d dorpeling %d staat in verkend gebied" % [nr, d.id])
	var ver := w.kampvuur + Vector2i(int(m.start_straal) + int(m.zicht_dorpeling) + 12, 0)
	_check(not m.is_verkend(ver), "M%d %s ver van het dorp nog onverkend" % [nr, ver])
	var n := m.aantal()
	var tot := 0
	for i in w.bereik.size():
		tot += w.bereik[i]
	print("  M%d start verkend %d tegels, bereikbaar %d" % [nr, n, tot])
	_check(n > 150 and n < tot / 2, "M%d startgebied klein maar niet leeg (%d)" % [nr, n])


func _test_lopen() -> void:
	var w := Wereld.new()
	w.laad("", 1)
	var m := w.mist
	var d: Dorpeling = w.dorpelingen[0]
	var doel := w.dichtstbij_loopbaar(w.kampvuur + Vector2i(20, -4))
	_check(not m.is_verkend(doel), "loopdoel %s begint onverkend" % doel)
	var v0 := m.versie
	var voor := m.aantal()
	var start := d.tegel()
	_check(w.geef_bevel([d.id], "loop", doel) == 1, "loopbevel geaccepteerd")
	for i in 900:
		w.tik(w.tik_dt)
		if d.tegel().distance_to(doel) < 1.5:
			break
	_check(d.tegel().distance_to(doel) < 1.5, "dorpeling bij het doel (%s, doel %s)" % [d.tegel(), doel])
	_check(m.is_verkend(doel), "loopdoel nu verkend")
	_check(m.aantal() > voor and m.versie > v0, "meer verkend (%d > %d)" % [m.aantal(), voor])
	_check(m.is_verkend(start), "vertrekplek blijft verkend")
	# terug naar het dorp: het doel blijft verkend (geen grijze laag)
	w.geef_bevel([d.id], "loop", w.dichtstbij_loopbaar(w.kampvuur))
	for i in 900:
		w.tik(w.tik_dt)
	_check(m.is_verkend(doel), "doel blijft verkend als er niemand meer staat")


func _test_leeg() -> void:
	for nr in [1, 2]:
		var w := Wereld.new()
		w.laad("", nr)
		var r := w.raster
		var li := r.namen.find("leeg")
		# alles onthullen wat aan het bereik grenst, met een grote straal: leeg mag er niet bij zijn
		for y in range(0, r.rijen, 6):
			for x in range(0, r.kolommen, 6):
				w.mist.onthul(Vector2i(x, y), 9.0)
		var fout := 0
		var leeg := 0
		for i in r.soort.size():
			if r.soort[i] == li:
				leeg += 1
				if w.mist.verkend[i] != 0:
					fout += 1
		_check(leeg > 1000 and fout == 0, "M%d leeg nooit verkend (%d van %d)" % [nr, fout, leeg])
		_check(not w.mist.is_verkend(Vector2i(-1, -1)) and not w.mist.is_verkend(Vector2i(r.kolommen, 0)), "M%d buiten het raster onverkend" % nr)


func _test_uit() -> void:
	var w := Wereld.new()
	w.laad("", 2)
	var v := w.mist.versie
	w.mist.zet_aan(false)
	_check(w.mist.versie != v, "uitzetten telt als wijziging (view werkt bij)")
	_check(w.mist.is_verkend(Vector2i(0, 0)), "uit: alles zichtbaar")
	w.mist.zet_aan(true)
	_check(not w.mist.is_verkend(Vector2i(0, 0)), "weer aan: hoek (0,0) onverkend")


func _check(ok: bool, wat: String) -> void:
	print(("  ok   " if ok else "  FOUT ") + wat)
	if not ok:
		fouten += 1
