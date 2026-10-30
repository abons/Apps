extends SceneTree
## Headless simtest missie 2 (Terug op het vasteland): godot --headless --path . --script res://test/missie2_test.gd
## Kaart laadt, 10 dorpelingen (4 m, 4 v, 2 jongens), kampvuur, eigen koeien, 3 wolven (Wolf), voorgebouwde
## boerderij (melkerij), routes over het vasteland, missiedoel kas > 10.000 en verlies onder 2.

var fouten := 0


func _initialize() -> void:
	var w := Wereld.new()
	_check(w.laad("", 2), "kaart van missie 2 laadt")
	if fouten > 0:
		quit(1)
		return
	_check(w.missie_nr == 2 and w.missie.get("naam", "") == "Terug op het vasteland", "missie 2 gekozen (%s)" % w.missie.get("naam", "?"))
	_check(w.dorpelingen.size() == 10, "10 dorpelingen (zijn %d)" % w.dorpelingen.size())
	var tel := {"man": 0, "vrouw": 0, "jongen": 0, "meisje": 0}
	for d in w.dorpelingen:
		var k: String = d.geslacht if d.volwassen() else ("jongen" if d.geslacht == "man" else "meisje")
		tel[k] = int(tel.get(k, 0)) + 1
	_check(tel["man"] == 4 and tel["vrouw"] == 4 and tel["jongen"] == 2 and tel["meisje"] == 0, "4 man, 4 vrouw, 2 jongens (%s)" % tel)
	_check(w.kampvuur == Vector2i(90, 76), "kampvuur op (90,76) (staat op %s)" % w.kampvuur)
	var vlag := Vector2i(-1, -1)
	var wolven := 0
	for ob in w.objecten:
		if ob["naam"] == "vlag":
			vlag = Vector2i(ob["x"], ob["y"])
	_check(vlag == Vector2i(92, 73), "vlag op (92,73)")
	wolven = w.wolven.size()
	_check(wolven == 3, "3 wolven (sim/wolf.gd, zijn %d)" % wolven)
	var als_object := 0
	for ob in w.objecten:
		if ob["naam"] == "wolf":
			als_object += 1
	_check(als_object == 0, "wolven staan niet meer als statisch object (%d)" % als_object)
	var los := 0
	for d in w.dorpelingen:
		var t := d.tegel()
		if not w.raster.loopbaar_v(t) or w.bereik[w.raster.idx(t.x, t.y)] == 0:
			los += 1
	_check(los == 0, "alle dorpelingen op een loopbare, bereikbare tegel (%d niet)" % los)
	_check(w.kas == 6999, "startkas 6.999 (is %d)" % w.kas)
	_check(int(w.missie["doel"].get("kas_boven", 0)) == 10000, "missiedoel kas > 10.000 gelezen")
	_check(w.eigen_koeien() == 4, "4 eigen koeien uit de kaart (zijn %d)" % w.eigen_koeien())
	_check(w.vee.size() == 5, "plus 1 wilde koe van de generator (%d koeien)" % w.vee.size())
	_check(w.eiland.size.x > 50 and w.eiland.size.y > 50, "vasteland is groot: %s" % w.eiland)
	var aan_rand := 0             # het buitengebied is onbereikbaar: dicht bos, water of rots ertussen (zoals het origineel)
	for i in w.bereik.size():
		if w.bereik[i] == 1:
			var t := Vector2i(i % w.raster.kolommen, i / w.raster.kolommen)
			for k in 8:
				if w.raster.soort_naam(t.x + Raster.DC[k], t.y + Raster.DR[k]) == "leeg":
					aan_rand += 1
	_check(aan_rand == 0, "geen bereikbare tegel grenst aan het buitengebied (%d wel)" % aan_rand)
	_check(w.raster.factor(89, 72) > w.raster.factor(88, 72), "kaartpad bij het dorp is sneller dan gras")

	# voorgebouwde boerderij = melkerij, afgebouwd, kost niets
	_check(w.plaats_voorgebouwd() == 1, "voorgebouwde boerderij neergezet")
	var mk: Plan = null
	for p in w.plannen:
		if p.soort == &"melkerij":
			mk = p
	_check(mk != null and mk.klaar and mk.afdruk().has_point(Vector2i(90, 68)), "melkerij klaar op (90,68) (%s)" % (mk.afdruk() if mk else "geen"))
	_check(w.kas == 6999, "boerderij en haar weg kosten niets (kas %d)" % w.kas)

	# routes: een volwassene loopt het bos in het oosten in, een ander naar de rotsen in het zuiden
	var d1 := w.dorpelingen[0]
	var doelen := [w.dichtstbij_loopbaar(Vector2i(115, 70)), w.dichtstbij_loopbaar(Vector2i(100, 100))]
	for i in doelen.size():
		var d := w.dorpelingen[i]
		var doel: Vector2i = doelen[i]
		_check(doel.x >= 0 and w.geef_bevel([d.id], "loop", doel) == 1, "bevel naar %s geaccepteerd" % doel)
		var tikken := 0
		# tot hij er is: in dezelfde tik kan hij al een eigen klus kiezen (kopen), dan is de route meteen weer gevuld
		while d.tegel() != doel and d.bevel.get("soort", "") == "loop" and tikken < 8000:
			w.tik(w.tik_dt)
			tikken += 1
		_check(d.tegel() == doel, "aangekomen op %s (staat op %s, %.0f s)" % [doel, d.tegel(), tikken * w.tik_dt])
	_check(d1.volwassen(), "eerste dorpeling is volwassen")

	# missiedoel: kas precies 10.000 is niet genoeg (origineel `cash>`), daarboven gewonnen
	w.kas = 10000
	w.tik(w.tik_dt)
	_check(w.uitslag == "", "kas 10.000: nog bezig")
	w.kas = 10001
	w.tik(w.tik_dt)
	_check(w.uitslag == "gewonnen", "kas 10.001: gewonnen (%s)" % w.uitslag)

	var v := Wereld.new()
	v.laad("", 2)
	v.dorpelingen.resize(1)
	v.tik(v.tik_dt)
	_check(v.uitslag == "verloren", "1 dorpeling: verloren")

	print("---- ", "ALLES OK" if fouten == 0 else "%d FOUT(EN)" % fouten)
	quit(0 if fouten == 0 else 1)


func _check(ok: bool, tekst: String) -> void:
	print(("ok    " if ok else "FOUT  "), tekst)
	if not ok:
		fouten += 1
