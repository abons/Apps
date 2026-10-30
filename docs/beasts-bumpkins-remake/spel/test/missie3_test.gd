extends SceneTree
## Headless simtest missie 3 (Gouden kelk van Barathkar): godot --headless --path . --script res://test/missie3_test.gd
## Kaart laadt, 6 dorpelingen (3 m, 2 v, krijger als man), startkas 7.000, doel kas > 24.999, verlies onder 2,
## voorgebouwde hut, put en voetvolkgilde (Plan, 3x3), gouden kelk als object, 7 wolven, 2 koe-generators, rand dicht.
## Gameplay: krijger = voetsoldaat, man wordt voetsoldaat in het gilde (kosten, max 6, geen vrouw), soldaat boert niet en
## doodt een wolf met het zwaard, put: dorstige dorpeling haalt water; put en gilde bouwbaar vanaf M3.

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
	var donker := w.wolven.filter(func(wf: Wolf) -> bool: return wf.soort == &"donkere_wolf").size()
	_check(donker == 2, "2 donkere wolven (sex 29, hover_names dark wolf; zijn %d)" % donker)
	_check(w._generatoren.size() == 2 and w.vee.size() == 2, "2 koe-generators met elk 1 wilde koe (%d, %d koeien)" % [w._generatoren.size(), w.vee.size()])
	var namen := {}
	for ob in w.objecten:
		namen[ob["naam"]] = int(namen.get(ob["naam"], 0)) + 1
	_check(namen.get("put", 0) == 0 and namen.get("voetvolkgilde", 0) == 0 and w.voorgebouwd.size() == 3, "put en voetvolkgilde zijn voorgebouwd, geen object meer")
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

	_check(w.plaats_voorgebouwd() == 3, "voorgebouwde hut, put en gilde neergezet")
	var hut: Plan = null
	var put: Plan = null
	var gilde: Plan = null
	for p in w.plannen:
		match p.soort:
			&"hut": hut = p
			&"put": put = p
			&"voetvolkgilde": gilde = p
	_check(hut != null and hut.klaar and hut.afdruk().has_point(Vector2i(98, 80)), "hut klaar op (98,80) (%s)" % (hut.afdruk() if hut else "geen"))
	_check(put != null and put.klaar and put.afdruk().has_point(Vector2i(101, 80)), "put klaar op (101,80) (%s)" % (put.afdruk() if put else "geen"))
	_check(gilde != null and gilde.klaar and gilde.afdruk().has_point(Vector2i(103, 77)), "gilde klaar op (103,77) (%s)" % (gilde.afdruk() if gilde else "geen"))
	_check(gilde != null and not gilde.afdruk().has_point(vlag) and not gilde.afdruk().has_point(w.kampvuur), "gilde staat niet op vlag of kampvuur")
	_check(w.raster.blok[w.raster.idx(101, 80)] == 1, "put blokkeert zijn tegel")
	_check(w.kas == 7000, "voorgebouwd kost niets (kas %d)" % w.kas)
	_check(w.ontgrendeld(&"put") and w.ontgrendeld(&"voetvolkgilde"), "put en gilde in het bouwmenu van M3")
	w.missie_nr = 1
	_check(not w.ontgrendeld(&"put") and not w.ontgrendeld(&"voetvolkgilde"), "niet in het bouwmenu van M1")
	w.missie_nr = 3

	# krijger type 7 = voetsoldaat, lid van het voorgebouwde gilde
	var pigsy: Dorpeling = null
	for d in w.dorpelingen:
		if d.sex_ruw == 7:
			pigsy = d
	_check(pigsy != null and pigsy.rol == "voetsoldaat" and pigsy.lid == gilde, "krijger is voetsoldaat en lid van het gilde")
	_check(pigsy != null and not pigsy.kan_bevel("werk") and not pigsy.kan_bevel("claim") and pigsy.kan_bevel("vecht"), "voetsoldaat bouwt en claimt niet, vecht wel")
	_check(gilde != null and w.gilde_plaats(gilde) == 5, "gilde: nog 5 plaatsen (%d)" % (w.gilde_plaats(gilde) if gilde else -1))

	# een man wordt voetsoldaat: lopen naar de deur, betalen, rol
	var man: Dorpeling = null
	var vrouw: Dorpeling = null
	for d in w.dorpelingen:
		if d.rol == "" and d.geslacht == "man" and man == null:
			man = d
		if d.geslacht == "vrouw" and vrouw == null:
			vrouw = d
	_check(w.geef_gildebevel([vrouw.id], gilde) == 0, "een vrouw wordt geen voetsoldaat")
	var prijs := int(w.spel["voetsoldaat"]["prijs"])
	var kas0 := w.kas
	var rollen := []
	w.rol_veranderd.connect(func(d: Dorpeling) -> void: rollen.append(d.id))
	_check(w.geef_gildebevel([man.id], gilde) == 1, "man loopt naar het gilde")
	for i in 600:
		if man.rol != "":
			break
		w.tik(w.tik_dt)
	_check(man.rol == "voetsoldaat" and man.lid == gilde and man.id in rollen, "man is voetsoldaat geworden (%s)" % man.rol)
	_check(kas0 - w.kas >= prijs and kas0 - w.kas < prijs + 40, "kost %d uit de kas (%d -> %d)" % [prijs, kas0, w.kas])
	_check(w.geef_gildebevel([man.id], gilde) == 0, "al voetsoldaat: niet nog eens")

	# limiet 6: vul het gilde aan tot 6 leden, dan past er niemand meer bij
	while w.gilde_plaats(gilde) > 0:
		var x := Dorpeling.new()
		x.id = 100 + w.dorpelingen.size()
		x.geslacht = "man"
		x.rol = "voetsoldaat"
		x.lid = gilde
		x.zet_tegel(w.kampvuur + Vector2i(0, 2))
		w.dorpelingen.append(x)
	var nog: Dorpeling = null
	for d in w.dorpelingen:
		if d.rol == "" and d.geslacht == "man" and d.volwassen():
			nog = d
	_check(nog != null and w.geef_gildebevel([nog.id], gilde) == 0, "gilde vol (6): de zevende man kan er niet bij")
	_check(int(w.spel.get("gilde_max_leden", 0)) == 6, "gilde_max_leden 6 (hint 3-5)")
	for i in range(w.dorpelingen.size() - 1, -1, -1):
		if w.dorpelingen[i].id >= 100:
			w.dorpelingen.remove_at(i)
	var arm := Wereld.new()
	arm.laad("", 3)
	arm.plaats_voorgebouwd()
	arm.kas = prijs - 1
	var ag: Plan = null
	for p in arm.plannen:
		if p.soort == &"voetvolkgilde":
			ag = p
	var am: Dorpeling = null
	for d in arm.dorpelingen:
		if d.rol == "" and d.geslacht == "man":
			am = d
	_check(arm.geef_gildebevel([am.id], ag) == 0, "te weinig kas: geen voetsoldaat")

	# voetsoldaat doodt een wolf met het zwaard (bevel), zonder stenen
	var wf: Wolf = w.wolven[0]
	wf.zet_tegel(w.dichtstbij_loopbaar(man.tegel() + Vector2i(3, 0)))
	wf.anker = wf.tegel()
	var slagen := [0]
	var stenen := [0]
	w.zwaard_slag.connect(func(d: Dorpeling, _wf: Wolf) -> void: if d == man: slagen[0] += 1)
	w.steen_gegooid.connect(func(d: Dorpeling, _wf: Wolf) -> void: if d == man: stenen[0] += 1)
	_check(w.geef_vechtbevel([man.id], wf.id) == 1, "vechtbevel voor de voetsoldaat")
	for i in 300:
		if not wf.leeft():
			break
		w.tik(w.tik_dt)
	_check(not wf.leeft(), "wolf is dood door het zwaard (hp %d, %d slagen)" % [wf.hp, slagen[0]])
	_check(slagen[0] >= 1 and slagen[0] <= 3 and stenen[0] == 0, "zwaardslagen %d (schade 6, wolf 8 hp), geen stenen (%d)" % [slagen[0], stenen[0]])

	# zelf verdedigen: een ledige voetsoldaat valt een rondzwervende wolf binnen verweer_straal aan
	var wf2: Wolf = w.wolven[1]
	for i in 100:
		w.tik(w.tik_dt)
	man.bevel = {}
	man.route.clear()
	wf2.zet_tegel(w.dichtstbij_loopbaar(man.tegel() + Vector2i(4, 1)))
	wf2.anker = wf2.tegel()
	wf2.toestand = Wolf.ROAM
	for i in 20:
		w.tik(w.tik_dt)
		if man.doel_wolf == wf2:
			break
	_check(man.doel_wolf == wf2, "ledige voetsoldaat valt een zwervende wolf aan")

	# put: wie dorst heeft haalt water bij de put, gratis
	var dorstig: Dorpeling = vrouw
	var drank := []
	w.gedronken.connect(func(d: Dorpeling, p: Plan) -> void: drank.append([d.id, p]))
	dorstig.bevel = {}
	dorstig.route.clear()
	dorstig.dorst = float(w.spel["economie"]["dorst_s"]) + 1.0
	for k in dorstig.trek:
		dorstig.trek[k] = 0.0
	var kas_d := w.kas
	for i in 600:
		if not drank.is_empty():
			break
		w.tik(w.tik_dt)
	_check(not drank.is_empty() and drank[0][0] == dorstig.id and drank[0][1] == put, "dorstige dorpeling dronk bij de put")
	_check(dorstig.dorst < 1.0, "dorst weer 0 (%.1f)" % dorstig.dorst)
	_check(w.kas >= kas_d, "water kost niets")
	var hdef: Dictionary = Gegevens.lees("res://data/hints.json")
	var wacht := 0
	for h in hdef["missies"]["3"]["hints"]:
		if h["id"] in ["3-4", "3-5"] and h.has("wacht_op"):
			wacht += 1
	_check(wacht == 0, "hints 3-4 en 3-5 wachten nergens meer op")

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
