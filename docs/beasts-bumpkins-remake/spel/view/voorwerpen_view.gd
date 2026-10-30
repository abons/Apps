extends Node3D
## Spiegelt de voorwerpen van de sim (sim/voorwerpen.gd): op de grond het kaartmodel (Props.maak), gedragen voor de
## borst van de Bumpkin (kleiner, in beide handen), weg bij afleveren. Leest de sim, schrijft er niets in.
## TerreinView slaat objecten met "voorwerp" over; deze view tekent ze. Aanhaken in main.gd na WereldView.bouw.

const HAND := Vector3(0.0, 0.8, 0.34)    ## in Bumpkin-ruimte (gezicht langs +Z)
const HAND_SCHAAL := 0.5                 ## t.o.v. de grondschaal

var w: Wereld
var view: WereldView
var nodes: Array[Dictionary] = []        ## {"ob": objectdict (zelfde referentie als in de sim), "node", "schaal"}


func bouw(wereld: Wereld, wereld_view: WereldView) -> void:
	w = wereld
	view = wereld_view
	name = "Voorwerpen"
	for ob in Voorwerpen.alle(w):
		var n := Props.maak(ob)
		if n == null:
			n = Node3D.new()
		n.name = "%s_%d_%d" % [ob["naam"], ob["x"], ob["y"]]
		add_child(n)
		nodes.append({"ob": ob, "node": n, "schaal": n.scale})
		_op_grond(ob)
	w.voorwerp_afgeleverd.connect(func(ob: Dictionary, _d: Dorpeling, _k: int) -> void:
		var e := _van(ob)
		if not e.is_empty():
			(e["node"] as Node3D).queue_free()
			nodes.erase(e))
	w.voorwerp_gevallen.connect(_op_grond)


## Een dict is als sleutel niet bruikbaar (hash op inhoud, en x/y/drager veranderen): zoeken op referentie.
func _van(ob: Dictionary) -> Dictionary:
	for e in nodes:
		if is_same(e["ob"], ob):
			return e
	return {}


func _op_grond(ob: Dictionary) -> void:
	var e := _van(ob)
	if e.is_empty():
		return
	var n: Node3D = e["node"]
	n.scale = e["schaal"]
	n.rotation = Vector3.ZERO
	n.position = view.terrein.tegel_midden(Vector2i(ob["x"], ob["y"]))
	n.visible = true


## Wereldpositie van een voorwerp-node (Bestuur: klikken), Vector3.INF als het niet op de grond ligt.
func grond_pos(ob: Dictionary) -> Vector3:
	var e := _van(ob)
	if e.is_empty() or int(ob["drager"]) >= 0:
		return Vector3.INF
	return (e["node"] as Node3D).position


func _process(_dt: float) -> void:
	for e in nodes:
		var ob: Dictionary = e["ob"]
		var id := int(ob["drager"])
		if id < 0:
			continue
		var n: Node3D = e["node"]
		var u: Dictionary = view.units.get(id, {})
		if u.is_empty():
			n.visible = false
			continue
		var b: Node3D = u["bump"]
		n.visible = b.is_visible_in_tree()
		n.global_transform = Transform3D(b.global_transform.basis.orthonormalized(), b.global_transform * HAND)
		n.scale = e["schaal"] * HAND_SCHAAL
