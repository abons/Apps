extends SceneTree
## Headless test hints (sim/hints.gd, data/hints.json): godot --headless --path . --script res://test/hint_test.gd
## Missie 1: keten 1-12 (start) -> 1-2 (timer 108 tikken) -> 1-3 (hut af) -> 1-4 (loods af) -> 1-5 (molen af) ->
## 1-6 (timer 288, na 1-5) -> 1-7 (poort af), 1-11 en 1-10 op 360 tikken, 1-8 bij het oprapen van de beker; hints met
## wacht_op vuren niet. Missie 2 en 3: briefing en de hints die de remake kan tonen.

var fouten := 0


func _initialize() -> void:
	var w := Wereld.new()
	_check(w.laad(), "missie 1 laadt")
	var h := Hints.new().bouw(w)
	var gevuurd: Array = []
	h.hint_getoond.connect(func(x: Dictionary) -> void: gevuurd.append(x["id"]))
	_check(h.briefing.get("titel", "") != "" and h.briefing.get("tekst", "") != "", "briefing missie 1")
	_check(h.hints.size() == 11, "11 hints in missie 1 (%d)" % h.hints.size())

	h.controleer()
	_check(gevuurd == ["1-12"], "bij de start alleen 1-12 (%s)" % [gevuurd])
	var tik_s := float(w.spel["seizoen_s"]) / 2880.0
	_loop(w, h, 100 * tik_s)
	_check(gevuurd == ["1-12"], "op 100 tikken nog niets (%s)" % [gevuurd])
	# een hut voor 1-2 af: 1-3 wacht op 1-2
	_bouw(w, &"hut")
	h.controleer()
	_check(not "1-3" in gevuurd, "hut af voor 1-2: 1-3 wacht (keten)")
	_loop(w, h, 10 * tik_s)
	_check(gevuurd.slice(0, 3) == ["1-12", "1-2", "1-3"], "1-2 op 108 tikken, dan meteen 1-3 (%s)" % [gevuurd])
	_check(not "1-4" in gevuurd, "1-4 nog niet zonder loods")
	_bouw(w, &"gereedschapsloods")
	h.controleer()
	_check(gevuurd.back() == "1-4", "loods af -> 1-4 (%s)" % [gevuurd])
	_loop(w, h, 200 * tik_s)       # voorbij 288 tikken: 1-6 wacht op 1-5 (molen)
	_check(not "1-6" in gevuurd, "1-6 wacht op de molen")
	_bouw(w, &"molen")
	h.controleer()
	_check(gevuurd.slice(gevuurd.find("1-4") + 1, gevuurd.find("1-4") + 3) == ["1-5", "1-6"], "molen af -> 1-5, dan 1-6 (%s)" % [gevuurd])
	_check(not "1-7" in gevuurd, "1-7 nog niet zonder poort")
	_bouw(w, &"poort")
	h.controleer()
	_check(gevuurd.back() == "1-7", "poort af -> 1-7 (%s)" % [gevuurd])
	_loop(w, h, 80 * tik_s)
	_check("1-11" in gevuurd, "1-11 op 360 tikken")
	_check("1-10" in gevuurd, "1-10 (prijzen) op 360 tikken")
	_check(not "1-9" in gevuurd, "1-9 (wacht_op) vuurt niet")
	_check(not "1-8" in gevuurd, "1-8 nog niet")
	var b: Dictionary = Voorwerpen.alle(w)[0]
	var man: Dorpeling = null
	for d in w.dorpelingen:
		if d.volwassen() and d.geslacht == "man":
			man = d
			break
	Voorwerpen.geef_pakbevel(w, [man.id], b)
	var n := 0
	while int(b["drager"]) < 0 and n < 4000:
		w.tik(w.tik_dt)
		n += 1
	h.controleer()
	_check(gevuurd.back() == "1-8", "beker opgeraapt -> 1-8 (%s)" % [gevuurd])
	var dubbel := gevuurd.duplicate()
	_loop(w, h, 30.0)
	_check(gevuurd == dubbel, "geen hint twee keer")
	_check(gevuurd == ["1-12", "1-2", "1-3", "1-4", "1-5", "1-6", "1-7", "1-11", "1-10", "1-8"], "volgorde %s" % [gevuurd])

	for nr in [2, 3]:
		var w2 := Wereld.new()
		_check(w2.laad("", nr), "missie %d laadt" % nr)
		var h2 := Hints.new().bouw(w2)
		_check(h2.briefing.get("tekst", "") != "", "briefing missie %d" % nr)
		var g2: Array = []
		h2.hint_getoond.connect(func(x: Dictionary) -> void: g2.append(x["id"]))
		_loop(w2, h2, 5.0 * float(w2.spel["seizoen_s"]))
		var verwacht: Array = ["2-1", "2-3"] if nr == 2 else []
		_check(g2 == verwacht, "missie %d na 5 seizoenen: %s (verwacht %s)" % [nr, g2, verwacht])
		if nr == 3:      # kelk aanraken (dorpeling erop gezet) -> 3-1
			var k: Dictionary = Voorwerpen.alle(w2)[0]
			var d3: Dorpeling = w2.dorpelingen[0]
			d3.zet_tegel(Vector2i(k["x"], k["y"]))
			d3.route.clear()
			var m := 0
			while int(k["drager"]) < 0 and m < 50:
				w2.tik(w2.tik_dt)
				m += 1
			h2.controleer()
			_check(g2 == ["3-1"], "kelk opgeraapt -> 3-1 (%s)" % [g2])

	print("ALLES OK" if fouten == 0 else "%d FOUT(EN)" % fouten)
	quit(0 if fouten == 0 else 1)


func _loop(w: Wereld, h: Hints, s: float) -> void:
	var n := int(ceil(s / w.tik_dt))
	for i in n:
		w.tik(w.tik_dt)
		h.controleer()


## Zet een plan van `soort` bij het kampvuur en rondt het in een tik af (zoals --scenario=hints).
func _bouw(w: Wereld, soort: StringName) -> void:
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
					return
	_check(false, "geen plek voor %s" % soort)


func _check(ok: bool, wat: String) -> void:
	if ok:
		print("  ok   ", wat)
	else:
		print("  FOUT ", wat)
		fouten += 1
