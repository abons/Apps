extends Node
## Scenario `missie4` (main.gd --missie=4 --scenario=missie4 --stap=overzicht|poort|beker|wezens|muur), frames voor
## ../map4.md (out/missie4/):
##   overzicht  de hele kaart van schuin boven (zonder mist): dorp, bossen, het meer, poort, ommuurde plek.
##   poort      een man met de sleutel loopt naar de magische poort; de deur zakt weg.
##   beker      poort open; een man raapt de tinnen beker op: vuur op de olie, de mijnen eromheen gaan af.
##   wezens     de zombies (passief: den met ogen) bij de beker kijken naar een man die langsloopt.
##   muur       de zombie bij de ommuurde plek valt om, de oostmuur verdwijnt, een man loopt naar de gouden kelk.
## Frames: --write-movie out/missie4/<stap>/f.png --fixed-fps 10 --quit-after 120.

var m: Node            ## main.gd
var w: Wereld
var stap := "overzicht"
var t := 0.0
var man: Dorpeling
var fase := 0


func start(main: Node) -> Node:
	m = main
	w = m.w
	for a in OS.get_cmdline_user_args():
		if a.begins_with("--stap="):
			stap = a.get_slice("=", 1)
	for d in w.dorpelingen:
		if d.geslacht == "man" and d.volwassen():
			man = d
			break
	var tm := func(t2: Vector2i) -> Vector3: return m.view.terrein.tegel_midden(t2)
	match stap:
		"overzicht":
			m.cam.zet_direct(tm.call(Vector2i(92, 68)), 0.0, deg_to_rad(62), 260.0)
		"poort":
			var sleutel := _ob("magische_sleutel")
			_zet(man, Vector2i(72, 69))
			sleutel["drager"] = man.id
			w.opgeraapt[198] = true
			w.geef_bevel([man.id], "loop", Vector2i(72, 73))
			m.cam.zet_direct(tm.call(Vector2i(72, 73)), 0.5, deg_to_rad(30), 14.0)
		"beker":
			Regels._doe(w, {"type": "open", "object": "magische_poort"})
			_zet(man, Vector2i(68, 80))
			w.geef_bevel([man.id], "loop", Vector2i(68, 85))
			m.cam.zet_direct(tm.call(Vector2i(68, 84)), 0.4, deg_to_rad(36), 18.0)
		"wezens":
			Regels._doe(w, {"type": "open", "object": "magische_poort"})
			_zet(man, Vector2i(72, 77))
			w.geef_bevel([man.id], "loop", Vector2i(77, 83))
			m.cam.zet_direct(tm.call(Vector2i(75, 81)), 2.6, deg_to_rad(26), 12.0)
		"muur":
			Regels.maak(w, 172, Vector2i(40, 10))
			_zet(man, Vector2i(48, 10))
			m.cam.zet_direct(tm.call(Vector2i(43, 11)), 0.3, deg_to_rad(40), 20.0)
	return self


func _zet(d: Dorpeling, tg: Vector2i) -> void:
	d.zet_tegel(tg)
	d.route.clear()
	d.bevel = {}
	d.anker = tg
	d.wacht = 999.0


func _ob(naam: String) -> Dictionary:
	for ob in w.objecten:
		if ob["naam"] == naam:
			return ob
	return {}


func _process(dt: float) -> void:
	t += dt
	if stap == "muur":
		if fase == 0 and t > 1.0:
			fase = 1
			for wf in w.wolven:
				if wf.kaart_tegel == Vector2i(47, 12):
					wf.raak(w, 10000)
				elif wf.kaart_tegel == Vector2i(45, 14):
					wf.zet_tegel(Vector2i(52, 20))      # de wolf ernaast even uit beeld
					wf.anker = wf.tegel()
		if fase == 1 and w.regels_af.has("muur_open") and t > 4.0:
			fase = 2
			w.geef_bevel([man.id], "loop", Vector2i(41, 11))
		if w.uitslag != "" and fase == 2:
			fase = 3
			print("[missie4] uitslag ", w.uitslag, " op %.1f s" % t)
