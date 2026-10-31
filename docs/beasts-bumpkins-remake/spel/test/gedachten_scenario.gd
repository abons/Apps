extends Node
## Scenario `gedachten` (main.gd --scenario=gedachten), frames voor de gedachtewolkjes en het portret (sim/gedachten.gd,
## view/gedachten_view.gd, view/portret.gd): zes dorpelingen rond het kampvuur, elk met een andere behoefte (wil melk,
## honger, dorst, wil een ei, boos, tevreden), sim op pauze; de eerste (wil melk) is gekozen. --stap=verliefd kiest de
## vrouw die een gezin sticht. --stap=man|vrouw|bouwer|voetsoldaat kiest zo een (bouwer en voetsoldaat: een volwassen man
## krijgt die rol), voor de frames van het portret (test/portret_frames.sh).

var m: Node            ## main.gd
var w: Wereld
var stap := ""
var _rollen := []      ## [Dorpeling, rol]


func start(main: Node) -> Node:
	m = main
	w = m.w
	for a in OS.get_cmdline_user_args():
		if a.begins_with("--stap="):
			stap = a.get_slice("=", 1)
	w.alles_open = true
	var v := w.kampvuur
	var plekken := [Vector2i(-2, 2), Vector2i(1, 3), Vector2i(3, 0), Vector2i(-3, -1), Vector2i(0, -3), Vector2i(3, -3)]
	var rollen := ["melk", "honger", "dorst", "ei", "boos", "blij"]
	if stap == "verliefd":
		rollen = ["verliefd", "honger", "dorst", "ei", "boos", "blij"]
	for i in mini(w.dorpelingen.size(), plekken.size()):
		var d: Dorpeling = w.dorpelingen[i]
		d.zet_tegel(w.dichtstbij_loopbaar(v + plekken[i]))
		d.route.clear()
		_rollen.append([d, rollen[i]])
	_zet()
	w.gepauzeerd = true
	var eerste: Dorpeling = _rollen[0][0]
	if stap == "verliefd":
		for r in _rollen:
			if (r[0] as Dorpeling).geslacht == "vrouw" and (r[0] as Dorpeling).volwassen():
				eerste = r[0]
				r[1] = "verliefd"
				_rollen[0][1] = "melk" if _rollen[0][0] != eerste else "verliefd"
				break
		_zet()
	if stap in ["man", "vrouw", "bouwer", "voetsoldaat"]:
		for r in _rollen:
			var d: Dorpeling = r[0]
			if d.volwassen() and d.leeftijd == "volwassen" and d.geslacht == ("vrouw" if stap == "vrouw" else "man"):
				eerste = d
				if stap in ["bouwer", "voetsoldaat"]:
					d.rol = stap
					w.rol_veranderd.emit(d)
				break
	m.bestuur.gekozen.clear()
	m.bestuur.gekozen.append(eerste.id)
	m.view.gekozen = m.bestuur.gekozen
	return self


func _process(_dt: float) -> void:
	_zet()


func _zet() -> void:
	for r in _rollen:
		var d: Dorpeling = r[0]
		for waar in Wereld.WAREN:
			d.trek[waar] = 0.0
		d.dorst = 0.0
		d.geluk = 0.6
		d.geraakt_s = 99.0
		d.wieg = {}
		match r[1]:
			"melk": d.trek["melk"] = 80.0
			"honger":
				for waar in Wereld.WAREN:
					d.trek[waar] = 400.0
			"dorst": d.dorst = 200.0
			"ei": d.trek["ei"] = 80.0
			"boos": d.geluk = 0.1
			"blij": d.geluk = 0.9
			"verliefd": d.wieg = {"scenario": true}
