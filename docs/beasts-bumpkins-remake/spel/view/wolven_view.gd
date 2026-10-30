extends Node3D
## Spiegelt de wolven van de sim (Wereld.wolven, sim/wolf.gd) met WolfModel, en het gevecht: bij `steen_gegooid` gooit de
## Bumpkin van die dorpeling (clip aanval_steen: hurken, steen rapen, gooien; de steen vliegt als projectiel, zie
## Bumpkin.gooi_steen). Een opgegeten koe (`koe_weg`) gaat uit WereldView.koeien. Leest de sim, schrijft er niets in.
## Aanhaken (WereldView.bouw): `var wv = preload("res://view/wolven_view.gd").new(); add_child(wv); wv.bouw(w, self)`.

var w: Wereld
var view: Node3D                 # WereldView (units, koeien, terrein)
var wolven := {}                 # wolf-id -> {"node": Node3D, "fase": float}
var _t := 0.0


func bouw(wereld: Wereld, wereld_view: Node3D) -> void:
	w = wereld
	view = wereld_view
	name = "Wolven"
	for wf in w.wolven:
		_maak(wf)
	w.wolf_weg.connect(func(wf: Wolf) -> void:
		if wolven.has(wf.id):
			(wolven[wf.id]["node"] as Node3D).queue_free()
			wolven.erase(wf.id))
	w.koe_weg.connect(func(k: Vee) -> void:
		var koeien: Dictionary = view.koeien
		if koeien.has(k.id):
			(koeien[k.id] as Node3D).queue_free()
			koeien.erase(k.id))
	w.steen_gegooid.connect(_gooi)


func _maak(wf: Wolf) -> void:
	var n := WolfModel.maak()
	n.name = "Wolf_%d" % wf.id
	add_child(n)
	n.position = _wereld_pos(wf, 1.0)
	n.rotation.y = atan2(wf.richting.x, wf.richting.y)
	wolven[wf.id] = {"node": n, "fase": float(wf.id) * 1.7}


func _wereld_pos(wf: Wolf, a: float) -> Vector3:
	var p := wf.vorige.lerp(wf.pos, a) * w.tegel_m
	return Vector3(p.x, view.terrein.hoogte_op(p.x, p.y), p.y)


## Wereldpositie van wolf `id` (Bestuur: klikken op een wolf), Vector3.INF als hij er niet (meer) is.
func wolf_pos(id: int) -> Vector3:
	return (wolven[id]["node"] as Node3D).global_position if wolven.has(id) else Vector3.INF


func _gooi(d: Dorpeling, wf: Wolf) -> void:
	if not view.units.has(d.id):
		return
	var b: Bumpkin = view.units[d.id]["bump"]
	var doel := _wereld_pos(wf, 1.0) + Vector3(0, 0.45, 0)
	if wf.snelheid_mps > 0.0:      # een beetje voorhouden: de steen is ~1 s onderweg
		doel += Vector3(wf.richting.x, 0, wf.richting.y) * wf.snelheid_mps * 0.6
	b.gooi_steen(doel)


func _process(dt: float) -> void:
	_t += dt
	var a := w.alpha()
	var cam := get_viewport().get_camera_3d()
	var tempo := 0.0 if w.gepauzeerd else w.tempo
	for wf in w.wolven:
		if not wolven.has(wf.id):
			_maak(wf)
		var u: Dictionary = wolven[wf.id]
		var n: Node3D = u["node"]
		n.visible = w.mist.is_verkend(wf.tegel())   # sim/mist.gd: in onverkend gebied niet tonen
		var nieuw := _wereld_pos(wf, a)
		var stap := Vector2(nieuw.x - n.position.x, nieuw.z - n.position.z).length()
		n.position = nieuw
		var yaw := atan2(wf.richting.x, wf.richting.y)
		n.rotation.y = lerp_angle(n.rotation.y, yaw, minf(1.0, dt * 8.0))
		# poten: een volle pas (2 PI) per ~0,9 m afgelegde grond
		u["fase"] = float(u["fase"]) + stap / 0.9 * TAU
		WolfModel.werk(n, wf, u["fase"], _t, dt * maxf(tempo, 0.01))
		var hp := n.get_node("Hp") as Node3D
		if hp.visible and cam != null:
			hp.look_at(cam.global_position, Vector3.UP, true)    # quad met de voorkant (+Z) naar de camera
