extends Node
## Scenario `missie3` (main.gd --missie=3 --scenario=missie3 --stap=dorp|soldaat|put), frames voor ../map3.md:
##   dorp     het voorgebouwde dorp: hut, put (bron.glb), voetvolkgilde (blok) en vlag, van schuin boven.
##   soldaat  een man loopt naar het gilde en wordt voetsoldaat (zwaard); daarna komt een wolf naast hem en hij valt aan.
##   put      iedereen heeft dorst en haalt water bij de put.
## Frames: --write-movie out/m3/f.png --fixed-fps 10 --quit-after 200.

var m: Node            ## main.gd
var w: Wereld
var stap := "dorp"
var t := 0.0
var man: Dorpeling
var wf: Wolf
var fase := 0


func start(main: Node) -> Node:
	m = main
	w = m.w
	for a in OS.get_cmdline_user_args():
		if a.begins_with("--stap="):
			stap = a.get_slice("=", 1)
	var gilde := w.dichtste_gebouw(&"voetvolkgilde", w.kampvuur)
	var put := w.dichtste_gebouw(&"put", w.kampvuur)
	match stap:
		"dorp":
			m.cam.zet_direct(m.view.terrein.tegel_midden(Vector2i(100, 79)), 0.6, deg_to_rad(38), 22.0)
		"soldaat":
			for d in w.dorpelingen:
				if d.rol == "" and d.geslacht == "man" and d.volwassen():
					man = d
					break
			print("[missie3] gildebevel ", w.geef_gildebevel([man.id], gilde), " kas ", w.kas)
			m.cam.zet_direct(m.view.terrein.tegel_midden(gilde.deur_tegel()), 0.6, deg_to_rad(34), 13.0)
		"put":
			for d in w.dorpelingen:
				d.dorst = 999.0
			m.cam.zet_direct(m.view.terrein.tegel_midden(put.deur_tegel()), 0.3, deg_to_rad(34), 12.0)
	return self


func _process(dt: float) -> void:
	t += dt
	if stap != "soldaat" or man == null:
		return
	if fase == 0 and man.rol == "voetsoldaat":
		fase = 1
		print("[missie3] voetsoldaat op %.1f s, kas %d" % [t, w.kas])
		wf = w.wolven[0]
		wf.zet_tegel(w.dichtstbij_loopbaar(man.tegel() + Vector2i(4, 2)))
		wf.anker = wf.tegel()
		w.geef_vechtbevel([man.id], wf.id)
	if fase >= 1 and wf != null:
		var mid: Vector2 = (man.pos + wf.pos) * 0.5 * w.tegel_m
		m.cam.zet_direct(Vector3(mid.x, m.view.terrein.hoogte_op(mid.x, mid.y), mid.y), 0.6, deg_to_rad(30), 9.0)
		if fase == 1 and not wf.leeft():
			fase = 2
			print("[missie3] wolf dood op %.1f s" % t)
