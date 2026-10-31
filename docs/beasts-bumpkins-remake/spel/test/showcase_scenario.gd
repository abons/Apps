extends Node
## Scenario `showcase` (main.gd --scenario=showcase --stap=dorp|dieren|put), voorbeeldbeelden van de voortgang
## (lokaal/showcase/, met --geen_hud en de --cam*-opties van main.gd):
##   dorp    missie 1 als een druk dorp: twee hutten, molen met rijpe akkers, melkerij, kippenhok, eigen koeien; 2x.
##   put     missie 3: de dorpelingen lopen om de beurt de trap van de put op en drinken binnen.
##   dieren  kippenhok met scharrelende en leggende kippen, drie eigen koeien ervoor, een melkerij ernaast.

var m: Node            ## main.gd
var w: Wereld
var stap := "dorp"


func start(main: Node) -> Node:
	m = main
	w = m.w
	for a in OS.get_cmdline_user_args():
		if a.begins_with("--stap="):
			stap = a.get_slice("=", 1)
	w.alles_open = true
	var v := w.kampvuur
	match stap:
		"dorp":
			for sd in [[&"hut", v + Vector2i(-7, -6), 0], [&"hut", v + Vector2i(-8, 2), 0], [&"molen", v + Vector2i(5, -8), 0],
					[&"melkerij", v + Vector2i(7, 1), 0], [&"kippenhok", v + Vector2i(0, -7), 0]]:
				_af(sd[0], sd[1], sd[2])
			for bij in [v + Vector2i(11, -8), v + Vector2i(13, -8), v + Vector2i(11, -6), v + Vector2i(13, -6)]:
				_af(&"akker", bij, 0)
			for t in w.akkers:
				w.akkers[t] = 55.0
			_koeien(v + Vector2i(4, 6), 2)
			w.tempo = 2.0
			m.cam.zet_direct(m.view.terrein.tegel_midden(v + Vector2i(0, -2)), 0.6, deg_to_rad(36), 30.0)
		"dieren":
			var kh := _af(&"kippenhok", v + Vector2i(9, 1), 0)
			_af(&"melkerij", v + Vector2i(9, -6), 0)
			for k in w.kippen:
				k.leeg = 2.0
			var deur: Vector2i = kh.deur_tegel() if kh != null else v
			_koeien(deur + Vector2i(4, 2), 3)
			for k in w.vee:
				k.anker = deur + Vector2i(4, 2)
				k.wacht = 99.0          # blijven staan: in beeld naast het hok
			var hok: Vector3 = m.view.terrein.tegel_midden(deur)
			var kudde: Vector3 = m.view.terrein.tegel_midden(deur + Vector2i(4, 2))
			m.cam.zet_direct((hok + kudde) * 0.5 + Vector3(0, 0.4, 0), 0.6, deg_to_rad(28), 8.0)
		"put":
			# missie 3: de dorpelingen staan bij de put en krijgen om de 2 s dorst: ze lopen een voor een de trap op
			var put := w.dichtste_gebouw(&"put", w.kampvuur)
			var dt := put.deur_tegel()
			var drempel := float(w.spel["economie"].get("dorst_s", 90.0))
			var i := 0
			for d in w.dorpelingen:
				d.zet_tegel(w.dichtstbij_loopbaar(dt + Vector2i(-3 + (i % 3) * 3, 3 + i / 3 * 2)))
				d.route.clear()
				d.bevel = {}
				d.anker = d.tegel()
				d.dorst = drempel - 0.5 - i * 2.0
				i += 1
			m.cam.zet_direct(m.view.terrein.tegel_midden(dt), 0.2, deg_to_rad(28), 8.0)
	return self


func _af(soort: StringName, bij: Vector2i, draai: int) -> Plan:
	var p: Plan = m._vrij_plan(soort, bij, draai)
	if p != null and w.plan_zet(p):
		w._rond_af(p)
		return p
	return null


## `n` eigen koeien rond `bij`.
func _koeien(bij: Vector2i, n: int) -> void:
	while w.vee.size() < n:
		w._spawn_koe()
	for i in n:
		var k: Vee = w.vee[i]
		k.eigenaar = 0
		k.van_generator = false
		k.anker = bij
		k.zet_tegel(w.dichtstbij_loopbaar(bij + Vector2i(i * 3 - 3, (i % 2) * 2)))
		w.koe_geclaimd.emit(k)
