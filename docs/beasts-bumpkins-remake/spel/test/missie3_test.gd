extends SceneTree
## Headless simtest missie 3 (Gouden kelk van Barathkar): godot --headless --path . --script res://test/missie3_test.gd
## Kaart laadt, 6 dorpelingen (3 m, 2 v, krijger als man), startkas 7.000, doel kas > 24.999, verlies onder 2,
## voorgebouwde hut (put en voetvolkgilde als blok), gouden kelk als object, 7 wolven, 2 koe-generators, rand dicht.

var fouten := 0


func _initialize() -> void:
	var w := Wereld.new()
	_check(w.laad("", 3), "kaart van missie 3 laadt")
	if fouten > 0:
		quit(1)
		return
	_check(w.missie_nr == 3 and w.missie.get("naam", "") == "Gouden kelk van Barathkar", "missie 3 gekozen (%s)" % w.missie.get("naam", "?"))
	_check(w.dorpelingen.size() == 6, "6 dorpelingen (zijn %d)" % w.dorpelingen.size())
	var tel := {"man": 0, "vrouw": 0, "kind": 0}
	var krijger := 0
	for d in w.dorpelingen:
		var k: String = d.geslacht if d.volwassen() else "kind"
		tel[k] = int(tel.get(k, 0)) + 1
		if d.sex_ruw == 7:
			krijger += 1
	_check(tel["man"] == 4 and tel["vrouw"] == 2 and tel["kind"] == 0, "4 man (waarvan 1 krijger), 2 vrouw (%s)" % tel)
	_check(krijger == 1, "1 krijger (type 7) als volwassen man")
	_check(w.kampvuur == Vector2i(102, 82), "kampvuur op (102,82) (staat op %s)" % w.kampvuur)
	var vlag := Vector2i(-1, -1)
	for ob in w.objecten:
		if ob["naam"] == "vlag":
			vlag = Vector2i(ob["x"], ob["y"])
	_check(vlag == Vector2i(104, 79), "vlag op (104,79) (%s)" % vlag)
	var los := 0
	for d in w.dorpelingen:
		var t := d.tegel()
		if not w.raster.loopbaar_v(t) or w.bereik[w.raster.idx(t.x, t.y)] == 0:
			los += 1
	_check(los == 0, "alle dorpelingen op een loopbare, bereikbare tegel (%d niet)" % los)
	_check(w.kas == 7000, "startkas 7.000 (is %d)" % w.kas)
	_check(int(w.missie["doel"].get("kas_boven", 0)) == 24999, "missiedoel kas > 24.999 gelezen (zoals het bestand)")
	_check(int(w.missie["verlies"].get("dorpelingen_onder", 0)) == 2, "verlies onder 2 dorpelingen")
	_check(w.wolven.size() == 7, "7 wolven (zijn %d)" % w.wolven.size())
	_check(w._generatoren.size() == 2 and w.vee.size() == 2, "2 koe-generators met elk 1 wilde koe (%d, %d koeien)" % [w._generatoren.size(), w.vee.size()])
	var namen := {}
	for ob in w.objecten:
		namen[ob["naam"]] = int(namen.get(ob["naam"], 0)) + 1
	_check(namen.get("put", 0) == 1 and namen.get("voetvolkgilde", 0) == 1, "put en voetvolkgilde staan als object (placeholder)")
	_check(w.raster.blok[w.raster.idx(101, 80)] == 1, "put blokkeert zijn tegel")
	var kelk := Vector2i(-1, -1)
	for ob in w.objecten:
		if ob["naam"] == "gouden_kelk":
			kelk = Vector2i(ob["x"], ob["y"])
	_check(kelk == Vector2i(96, 18), "gouden kelk ligt als object op (96,18) (%s)" % kelk)
	var kt := w.dichtstbij_loopbaar(kelk)
	_check(kt.x >= 0 and Vector2(kt).distance_to(Vector2(kelk)) <= 1.5, "kelk is te bereiken (%s)" % kt)
	var aan_rand := 0
	for i in w.bereik.size():
		if w.bereik[i] == 1:
			var t := Vector2i(i % w.raster.kolommen, i / w.raster.kolommen)
			for k in 8:
				if w.raster.soort_naam(t.x + Raster.DC[k], t.y + Raster.DR[k]) == "leeg":
					aan_rand += 1
	_check(aan_rand == 0, "geen bereikbare tegel grenst aan het buitengebied (%d wel)" % aan_rand)
	_check(w.eiland.size.x > 40 and w.eiland.size.y > 60, "speelgebied is groot: %s" % w.eiland)

	_check(w.plaats_voorgebouwd() == 1, "voorgebouwde hut neergezet")
	var hut: Plan = null
	for p in w.plannen:
		if p.soort == &"hut":
			hut = p
	_check(hut != null and hut.klaar and hut.afdruk().has_point(Vector2i(98, 80)), "hut klaar op (98,80) (%s)" % (hut.afdruk() if hut else "geen"))
	_check(w.kas == 7000, "hut kost niets (kas %d)" % w.kas)

	# kas: precies 24.999 is niet genoeg (origineel `cash>`), daarboven gewonnen
	var k := Wereld.new()
	k.laad("", 3)
	k.kas = 24999
	k.tik(k.tik_dt)
	_check(k.uitslag == "", "kas 24.999: nog bezig")
	k.kas = 25000
	k.tik(k.tik_dt)
	_check(k.uitslag == "gewonnen", "kas 25.000: gewonnen (%s)" % k.uitslag)

	var v := Wereld.new()
	v.laad("", 3)
	v.dorpelingen.resize(1)
	v.tik(v.tik_dt)
	_check(v.uitslag == "verloren", "1 dorpeling: verloren")

	print("---- ", "ALLES OK" if fouten == 0 else "%d FOUT(EN)" % fouten)
	quit(0 if fouten == 0 else 1)


func _check(ok: bool, tekst: String) -> void:
	print(("ok    " if ok else "FOUT  "), tekst)
	if not ok:
		fouten += 1
