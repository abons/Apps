extends SceneTree
## Headless test voorwerpen (sim/voorwerpen.gd): godot --headless --path . --script res://test/voorwerp_test.gd
## Missie 1: zilveren beker oprapen (pakbevel), dragen, aan de vlag afleveren (+5.000, weg); kind raapt ook;
## drager weg = beker valt. Missie 3: gouden kelk naar de vlag (+7.000).

var fouten := 0
var opgeraapt := 0
var afgeleverd := 0
var gevallen := 0


func _initialize() -> void:
	var w := Wereld.new()
	_check(w.laad(), "missie 1 laadt")
	w.voorwerp_opgeraapt.connect(func(_o: Dictionary, _d: Dorpeling) -> void: opgeraapt += 1)
	w.voorwerp_afgeleverd.connect(func(_o: Dictionary, _d: Dorpeling, _k: int) -> void: afgeleverd += 1)
	w.voorwerp_gevallen.connect(func(_o: Dictionary) -> void: gevallen += 1)
	var bekers := Voorwerpen.alle(w)
	_check(bekers.size() == 1, "een voorwerp op kaart 1 (%d)" % bekers.size())
	if bekers.is_empty():
		quit(1)
		return
	var b: Dictionary = bekers[0]
	_check(b["naam"] == "zilveren_beker" and Vector2i(b["x"], b["y"]) == Vector2i(110, 53), "zilveren beker op (110,53)")
	_check(int(b["drager"]) == -1, "ligt op de grond")
	_check(w.bereik[w.raster.idx(110, 53)] == 1, "beker is bereikbaar vanaf het kampvuur")

	# 1. pakbevel aan een man, hij loopt erheen en raapt op
	var man: Dorpeling = null
	for d in w.dorpelingen:
		if d.volwassen() and d.geslacht == "man":
			man = d
			break
	_check(Voorwerpen.geef_pakbevel(w, [man.id], b) == 1, "pakbevel geaccepteerd")
	var tikken := 0
	while int(b["drager"]) < 0 and tikken < 3000:
		w.tik(w.tik_dt)
		tikken += 1
	_check(int(b["drager"]) == man.id, "man draagt de beker na %.1f s" % (tikken * w.tik_dt))
	_check(opgeraapt == 1, "signaal opgeraapt")
	_check(Voorwerpen.van(w, man) == b, "Voorwerpen.van(man) is de beker")
	_check(Voorwerpen.geef_pakbevel(w, [man.id], b) == 0, "gedragen beker is niet nog eens te pakken")

	# 2. naar de vlag: kas +5000, beker weg
	var kas0 := w.kas
	var vlag := Vector2i(104, 65)
	w.geef_bevel([man.id], "loop", w.dichtstbij_loopbaar(vlag))
	tikken = 0
	var loopt_mee := true
	while afgeleverd == 0 and tikken < 3000:
		w.tik(w.tik_dt)
		tikken += 1
		if afgeleverd == 0 and Vector2i(b["x"], b["y"]) != man.tegel():
			loopt_mee = false
	_check(loopt_mee, "beker volgt de drager")
	_check(afgeleverd == 1, "afgeleverd aan de vlag na %.1f s" % (tikken * w.tik_dt))
	_check(w.kas - kas0 >= 5000 and w.kas - kas0 < 5100, "kas +5000 (%d)" % (w.kas - kas0))
	_check(Voorwerpen.alle(w).is_empty() and not b in w.objecten, "beker is weg")

	# 3. een kind raakt de beker: raapt hem ook op; drager weg = beker valt op zijn tegel
	var w2 := Wereld.new()
	w2.laad()
	w2.voorwerp_gevallen.connect(func(_o: Dictionary) -> void: gevallen += 1)
	var b2: Dictionary = Voorwerpen.alle(w2)[0]
	var kind: Dorpeling = null
	for d in w2.dorpelingen:
		if d.leeftijd == "kind":
			kind = d
	kind.zet_tegel(Vector2i(108, 53))
	kind.route.clear()
	kind.bevel = {}
	_check(Voorwerpen.geef_pakbevel(w2, [kind.id], b2) == 1, "kind krijgt een pakbevel")
	for i in 200:
		w2.tik(w2.tik_dt)
		if int(b2["drager"]) >= 0:
			break
	_check(int(b2["drager"]) == kind.id, "kind draagt de beker")
	kind.zet_tegel(Vector2i(106, 58))
	kind.route.clear()
	kind.bevel = {}
	w2.tik(w2.tik_dt)                    # de beker volgt hem naar zijn nieuwe tegel
	w2.dorpelingen.erase(kind)          # zoals bij een dood (nog niet in de sim)
	w2.tik(w2.tik_dt)
	_check(int(b2["drager"]) == -1 and gevallen == 1, "beker valt als de drager weg is")
	_check(Vector2i(b2["x"], b2["y"]) == Vector2i(106, 58), "op de laatste tegel van de drager (%d,%d)" % [b2["x"], b2["y"]])

	# 4. missie 3: gouden kelk naar de vlag = +7000
	var w3 := Wereld.new()
	_check(w3.laad("", 3), "missie 3 laadt")
	var kelken := Voorwerpen.alle(w3)
	_check(kelken.size() == 1 and kelken[0]["naam"] == "gouden_kelk", "gouden kelk is een voorwerp")
	if kelken.size() == 1:
		var k: Dictionary = kelken[0]
		var m := w3.dorpelingen[0]
		m.zet_tegel(w3.dichtstbij_loopbaar(Vector2i(k["x"], k["y"])))
		m.route.clear()
		m.bevel = {}
		w3.tik(w3.tik_dt)
		_check(int(k["drager"]) == m.id, "kelk opgeraapt door aanraken")
		var vt := Vector2i(-1, -1)
		for o in w3.objecten:
			if o["naam"] == "vlag" and int(o["owner"]) == 0:
				vt = Vector2i(o["x"], o["y"])
		var k0 := w3.kas
		m.zet_tegel(w3.dichtstbij_loopbaar(vt))
		m.route.clear()
		w3.tik(w3.tik_dt)
		_check(w3.kas - k0 >= 7000 and w3.kas - k0 < 7100 and not k in w3.objecten, "kelk aan de vlag: +7000 (%d)" % (w3.kas - k0))

	print("ALLES OK" if fouten == 0 else "%d FOUT(EN)" % fouten)
	quit(0 if fouten == 0 else 1)


func _check(ok: bool, wat: String) -> void:
	if ok:
		print("  ok   ", wat)
	else:
		fouten += 1
		print("  FOUT ", wat)
