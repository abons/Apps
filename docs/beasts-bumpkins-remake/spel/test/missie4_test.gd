extends SceneTree
## Headless simtest missie 4 (Beker van Vervulling): godot --headless --path . --script res://test/missie4_test.gd
## Kaart laadt, 4 dorpelingen (2 m, 2 v), kas 8.000, voorgebouwde hut en bouwersgilde, 4 zombies + 3 wolven, rand dicht.
## Puzzel (M4.MIS, ../map4.md): sleutel naar de poort -> poort open + gouden kelk in de ommuurde plek; zilveren beker
## oprapen = hint 4-9 + vuur (olie zet de mijnen af); mijn gaat af onder een dorpeling; zombie (47,12) dood -> oostmuur
## weg; dorpeling op de triggerplek (41,11) = gewonnen; onder 2 dorpelingen = verloren.

var fouten := 0


func _initialize() -> void:
	var w := Wereld.new()
	_check(w.laad("", 4), "kaart van missie 4 laadt")
	if fouten > 0:
		quit(1)
		return
	_check(w.missie.get("naam", "") == "Beker van Vervulling" and w.missie.get("dorp", "") == "Parpton", "missie 4, dorp Parpton")
	var tel := {"man": 0, "vrouw": 0, "kind": 0}
	for d in w.dorpelingen:
		var k: String = d.geslacht if d.volwassen() else "kind"
		tel[k] = int(tel.get(k, 0)) + 1
	_check(w.dorpelingen.size() == 4 and tel["man"] == 2 and tel["vrouw"] == 2, "2 mannen en 2 vrouwen (%s)" % tel)
	_check(w.kas == 8000, "startkas 8.000 (is %d)" % w.kas)
	_check(w.kampvuur == Vector2i(115, 103), "kampvuur op (115,103) (%s)" % w.kampvuur)
	_check(_obj(w, "vlag") == Vector2i(117, 100), "vlag op (117,100)")
	_check(w.plaats_voorgebouwd() == 2, "voorgebouwde hut en bouwersgilde neergezet")
	var soorten := []
	for p in w.plannen:
		soorten.append(String(p.soort))
	_check("hut" in soorten and "gereedschapsloods" in soorten, "hut en gereedschapsloods (bouwersgilde) staan er (%s)" % [soorten])
	_check(w.ontgrendeld(&"molen") and w.ontgrendeld(&"put") and w.ontgrendeld(&"voetvolkgilde"), "bouwmenu: molen (na de loods), put en gilde (vanaf M3)")
	var los := 0
	for d in w.dorpelingen:
		var t := d.tegel()
		if not w.raster.loopbaar_v(t) or w.bereik[w.raster.idx(t.x, t.y)] == 0:
			los += 1
	_check(los == 0, "alle dorpelingen bereikbaar (%d niet)" % los)

	# kaartobjecten
	var sleutel := _obj(w, "magische_sleutel")
	var poort := _obj(w, "magische_poort")
	var beker := _obj(w, "zilveren_beker")
	_check(sleutel == Vector2i(54, 26), "sleutel op (54,26) (%s)" % sleutel)
	_check(poort == Vector2i(72, 74) and w.raster.blok[w.raster.idx(72, 74)] == 1, "poort op (72,74) blokkeert")
	_check(beker == Vector2i(68, 85), "zilveren beker op (68,85)")
	_check(_obj(w, "triggerplek") == Vector2i(41, 11), "triggerplek op (41,11)")
	_check(_tel(w, "mijn") == 11 and _tel(w, "olie") == 1 and _tel(w, "stenen_muur") == 27, "11 mijnen, olie, 27 muurstukken (%d, %d, %d)" % [_tel(w, "mijn"), _tel(w, "olie"), _tel(w, "stenen_muur")])
	_check(_bereik(w, sleutel), "sleutel is bereikbaar")
	_check(not _bereik(w, beker) and not _bereik(w, Vector2i(41, 11)), "beker (achter de poort) en triggerplek (ommuurd) niet bereikbaar")
	var aan_rand := 0
	for i in w.bereik.size():
		if w.bereik[i] == 1:
			var t := Vector2i(i % w.raster.kolommen, i / w.raster.kolommen)
			for k in 8:
				if w.raster.soort_naam(t.x + Raster.DC[k], t.y + Raster.DR[k]) == "leeg":
					aan_rand += 1
	_check(aan_rand == 0, "geen bereikbare tegel grenst aan het buitengebied (%d wel)" % aan_rand)

	# wezens: 4 zombies (type 18) en 3 wolven
	var zombies := w.wolven.filter(func(wf: Wolf) -> bool: return wf.soort == &"zombie")
	_check(w.wolven.size() == 7 and zombies.size() == 4, "7 wezens, waarvan 4 zombies (%d, %d)" % [w.wolven.size(), zombies.size()])
	_check(zombies.all(func(z: Wolf) -> bool: return z.hp == 240), "zombie hp 240 (BEASTS.EXE)")
	var bewaker: Wolf = null
	for z in zombies:
		if z.kaart_tegel == Vector2i(47, 12):
			bewaker = z
	_check(bewaker != null, "zombie bij de ommuurde plek (47,12)")
	_check(not w.doel_gehaald() and w.uitslag == "", "nog niet gewonnen")

	var hints := Hints.new().bouw(w)
	var getoond := []
	hints.hint_getoond.connect(func(h: Dictionary) -> void: getoond.append(h["id"]))
	var man: Dorpeling = w.dorpelingen[0]
	var man2: Dorpeling = w.dorpelingen[1]
	for d in w.dorpelingen:
		d.wacht = 999.0

	# 4-1: bij de poort zonder sleutel
	_zet(man, Vector2i(72, 73))
	_tik(w, hints, 2)
	_check("4-1" in getoond, "hint 4-1 bij de poort zonder sleutel")

	# sleutel oprapen -> 4-2, naar de poort -> open + gouden kelk
	_zet(man, sleutel)
	_tik(w, hints, 2)
	_check(not Voorwerpen.van(w, man).is_empty() and "4-2" in getoond, "sleutel opgeraapt, hint 4-2")
	_zet(man, Vector2i(72, 72))
	w.geef_bevel([man.id], "loop", Vector2i(72, 73))
	for i in 100:
		_tik(w, hints, 1)
		if w.regels_af.has("poort_open"):
			break
	_check(w.regels_af.has("poort_open") and _obj(w, "magische_sleutel") == Vector2i(-1, -1), "sleutel bij de poort: regel poort_open, sleutel weg")
	_check(w.raster.blok[w.raster.idx(72, 74)] == 0 and _bereik(w, beker), "poort open: de beker is nu bereikbaar")
	_check(_obj(w, "gouden_kelk") == Vector2i(40, 10), "gouden kelk verschenen op (40,10) (%s)" % _obj(w, "gouden_kelk"))
	_check(w.kas == 8000, "sleutel levert geen kas op")

	# mijn: wie erop stapt is meteen dood (besluit gebruiker 2026-10-31: "unit was gelijk dood")
	var geraakt := []
	w.dorpeling_geraakt.connect(func(d: Dorpeling, o: String) -> void: geraakt.append([d.id, o]))
	var doden := []
	w.dorpeling_dood.connect(func(d: Dorpeling, o: String) -> void: doden.append([d.id, o]))
	var knal := []
	w.ontploffing.connect(func(t: Vector2i) -> void: knal.append(t))
	_zet(man2, Vector2i(67, 82))
	_tik(w, hints, 1)
	_check(knal.has(Vector2i(67, 82)) and _tel(w, "mijn") == 10, "mijn op (67,82) gaat af onder de dorpeling")
	_check(not man2 in w.dorpelingen and [man2.id, "mijn"] in doden, "mijn: meteen dood (%s)" % [doden])

	# valbeker: oprapen = 4-9 + vuur op de beker; direct contact met de vlam = dood; met olie gaan de mijnen eromheen af
	_zet(man, beker)
	_tik(w, hints, 1)
	_check("4-9" in getoond and w.regels_af.has("valbeker"), "beker opgeraapt: hint 4-9, regel valbeker")
	_check(_tel(w, "vuur") == 1 and _obj(w, "vuur") == beker, "vuur op de beker (68,85)")
	_tik(w, hints, 1)
	_check(not man in w.dorpelingen and [man.id, "vuur"] in doden, "direct contact met het vuur: meteen dood (%s)" % [doden])
	_tik(w, hints, int(2.5 / w.tik_dt))
	_check(_tel(w, "mijn") < 10, "olie onder het vuur: mijnen eromheen gingen af (nog %d)" % _tel(w, "mijn"))
	# de rand van het vuur (buiten de kern, binnen straal): schade per s, overleefbaar
	var rand: Dorpeling = w.dorpelingen[0]
	var vc: Dictionary = w.spel["vallen"]["vuur"]
	var vt0 := _obj(w, "vuur")
	rand.gezondheid = rand.gezondheid_max
	rand.zet_tegel(vt0)
	rand.pos = Vector2(vt0) + Vector2(0.5, 0.5) + Vector2((float(vc["kern"]) + float(vc["straal"])) * 0.5, 0.0)
	rand.route.clear()
	rand.bevel = {}
	rand.stil = true
	var hpr := rand.gezondheid
	_tik(w, hints, int(1.5 / w.tik_dt))
	_check(rand in w.dorpelingen and rand.gezondheid < hpr, "rand van het vuur: schade, niet dood (%.0f -> %.0f)" % [hpr, rand.gezondheid])
	rand.stil = false
	_zet(rand, w.kampvuur + Vector2i(0, 2))
	_tik(w, hints, int(30.0 / w.tik_dt))
	_check(_tel(w, "vuur") == 0, "vuur is uitgebrand")
	# de tinnen beker (gevallen bij de dode) is niets waard bij de vlag; geen nieuw vuur
	var drager: Dorpeling = w.dorpelingen[1]
	drager.gezondheid = drager.gezondheid_max
	_zet(drager, _obj(w, "zilveren_beker"))
	_tik(w, hints, 2)
	_check(not Voorwerpen.van(w, drager).is_empty() and _tel(w, "vuur") == 0, "beker weer opgeraapt, geen tweede vuur")
	var kas_b := w.kas
	_zet(drager, _obj(w, "vlag") + Vector2i(1, 1))
	_tik(w, hints, 2)
	_check(Voorwerpen.van(w, drager).is_empty() and w.kas == kas_b, "tinnen beker bij de vlag: weg, geen kas")
	# een bouwer dooft vuur (hij raakt het voor hij in de kern komt)
	var vt := w.dichtstbij_loopbaar(Vector2i(110, 108))
	var v2 := Regels.maak(w, 7, vt)
	var b: Dorpeling = w.dorpelingen[0]
	b.rol = "bouwer"
	_zet(b, vt + Vector2i(0, 1) if w.raster.loopbaar_v(vt + Vector2i(0, 1)) else vt)
	_tik(w, hints, 1)
	_check(not v2 in w.objecten and b in w.dorpelingen, "een bouwer dooft het vuur (origineel 0x448f78)")
	b.rol = ""
	# spies (klasse 36, vanaf M6): schade, overleefbaar
	var st := w.dichtstbij_loopbaar(w.kampvuur + Vector2i(3, 3))
	var sp := Regels.maak(w, 36, st)
	_check(not sp.is_empty() and sp["naam"] == "spies", "spies te maken (klasse 36)")
	b.gezondheid = b.gezondheid_max
	var hps := b.gezondheid
	_zet(b, st)
	_tik(w, hints, 1)
	_check(b in w.dorpelingen and b.gezondheid < hps and [b.id, "spies"] in geraakt, "spies: schade (%.0f -> %.0f), overleefd" % [hps, b.gezondheid])
	_zet(b, w.kampvuur + Vector2i(0, 2))
	_check(w.uitslag == "", "nog 2 dorpelingen: niet verloren (%d)" % w.dorpelingen.size())

	# zombie (type 18): standaard actief (gebruiker: de zombie valt aan); passief = staat stil, kijkt, bijt niet
	var z: Wolf = zombies[1] if zombies[0] == bewaker else zombies[0]
	_check(not z.passief(w), "zombie valt standaard aan (spel.json wezens.zombie.passief false)")
	z._c["passief"] = true
	for wf in w.wolven:         # de andere wezens jagen nu ook: even stil zetten, anders vlucht het slachtoffer
		if wf != z:
			wf.cfg(w)["passief"] = true
			wf.prooi = null
			wf.toestand = Wolf.ROAM if wf.leeft() else wf.toestand
	z.zet_tegel(w.dichtstbij_loopbaar(Vector2i(100, 90)))
	z.anker = z.tegel()
	z.toestand = Wolf.ROAM
	z.prooi = null
	z.route.clear()
	z.rust = 0.0                # kan eerder al gejaagd hebben: nu actief vanaf de start
	z.pauze = 0.0
	z.kijk = 0.0
	for d in w.dorpelingen:
		_zet(d, w.kampvuur + Vector2i(0, 2))
		d.doel_wolf = null       # wie eerder door een (nu actieve) zombie is aangevallen, vecht anders nog terug
	var slachtoffer: Dorpeling = w.dorpelingen[0]
	slachtoffer.gezondheid = slachtoffer.gezondheid_max
	_zet(slachtoffer, w.dichtstbij_loopbaar(z.tegel() + Vector2i(2, 0)))
	var zp := z.pos
	geraakt.clear()
	for i in 100:
		slachtoffer.route.clear()
		slachtoffer.bevel = {}
		w.tik(w.tik_dt)
	_check(geraakt.is_empty() and z.pos == zp, "passieve zombie loopt niet en bijt niet")
	_check(z.kijkt_naar == slachtoffer, "passieve zombie kijkt naar de dorpeling naast hem")
	_check(Leven.dreiging(w, slachtoffer) == null, "geen reden om voor een passieve zombie te vluchten")
	# actief (de standaard): jaagt niet op koeien, wel op dorpelingen, bijt 22
	z._c["passief"] = false
	z.kijk = 0.0
	if not w.vee.is_empty():
		w.vee[0].zet_tegel(w.dichtstbij_loopbaar(z.tegel() + Vector2i(0, 2)))
		_zet(slachtoffer, w.kampvuur + Vector2i(0, 2))
		_check(z._zoek_prooi(w) == null, "actieve zombie ziet een koe niet als prooi")
		_zet(slachtoffer, w.dichtstbij_loopbaar(z.tegel() + Vector2i(2, 0)))
	var t0 := w.tijd_s
	for i in 200:
		slachtoffer.route.clear()
		slachtoffer.bevel = {}
		w.tik(w.tik_dt)
		if not geraakt.is_empty():
			break
	_check(not geraakt.is_empty() and geraakt[0][1] == "zombie", "actieve zombie bijt een dorpeling (%s na %.1f s)" % [geraakt, w.tijd_s - t0])
	_check(float(z.cfg(w)["snelheid_mps"]) < float(w.spel["wolf"]["snelheid_mps"]), "zombie is trager dan een wolf")
	for wf in w.wolven:
		wf.cfg(w)["passief"] = w.spel["wezens"].get(String(wf.soort), {}).get("passief", false)

	# zombie (47,12) dood -> oostmuur weg -> triggerplek bereikbaar -> gewonnen
	bewaker.raak(w, 1000)
	_check(not bewaker.leeft(), "bewakende zombie verslagen")
	_tik(w, hints, 1)
	_check(w.regels_af.has("muur_open") and _tel(w, "stenen_muur") == 24, "regel muur_open: 3 muurstukken weg (%d over)" % _tel(w, "stenen_muur"))
	_check(w.raster.blok[w.raster.idx(44, 10)] == 0 and _bereik(w, Vector2i(41, 11)), "ommuurde plek nu bereikbaar")
	var winnaar: Dorpeling = w.dorpelingen[0]
	winnaar.gezondheid = winnaar.gezondheid_max
	_zet(winnaar, Vector2i(46, 10))
	w.geef_bevel([winnaar.id], "loop", Vector2i(41, 11))
	for i in 300:
		w.tik(w.tik_dt)
		if w.uitslag != "":
			break
	_check(w.uitslag == "gewonnen", "dorpeling op de triggerplek: gewonnen (%s)" % w.uitslag)

	# zonder sleutel of muur: de triggerplek alleen telt (zoals M4.MIS)
	var v := Wereld.new()
	v.laad("", 4)
	v.dorpelingen.resize(1)
	v.tik(v.tik_dt)
	_check(v.uitslag == "verloren", "1 dorpeling: verloren")

	print("---- ", "ALLES OK" if fouten == 0 else "%d FOUT(EN)" % fouten)
	quit(0 if fouten == 0 else 1)


func _zet(d: Dorpeling, t: Vector2i) -> void:
	d.zet_tegel(t)
	d.route.clear()
	d.bevel = {}
	d.anker = t


func _tik(w: Wereld, h: Hints, n: int) -> void:
	for i in n:
		w.tik(w.tik_dt)
		h.controleer()


func _obj(w: Wereld, naam: String) -> Vector2i:
	for ob in w.objecten:
		if ob["naam"] == naam:
			return Vector2i(ob["x"], ob["y"])
	return Vector2i(-1, -1)


func _tel(w: Wereld, naam: String) -> int:
	return w.objecten.filter(func(o: Dictionary) -> bool: return o["naam"] == naam).size()


## Een loopbare tegel naast `t` (of `t` zelf) ligt in Wereld.bereik.
func _bereik(w: Wereld, t: Vector2i) -> bool:
	for dy in range(-1, 2):
		for dx in range(-1, 2):
			var n := t + Vector2i(dx, dy)
			if w.raster.in_kaart(n.x, n.y) and w.raster.loopbaar_v(n) and w.bereik[w.raster.idx(n.x, n.y)] == 1:
				return true
	return false


func _check(ok: bool, tekst: String) -> void:
	print(("ok    " if ok else "FOUT  "), tekst)
	if not ok:
		fouten += 1
