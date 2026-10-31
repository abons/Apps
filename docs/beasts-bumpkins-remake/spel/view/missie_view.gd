extends Node3D
## Spiegelt de objecten die tijdens het spel veranderen (objecten.json "dynamisch", missie 4): magische poort (gaat open:
## de deur `poort_deur` zakt weg en verdwijnt, zoals de deur in het origineel oplost), stenen muren (weg na de regel),
## mijnen (weg als ze afgaan, met een knal), olie en vuur (vlammen flakkeren). Nieuwe objecten uit een regel
## (Wereld.object_erbij) komen erbij; voorwerpen (gouden kelk) tekent view/voorwerpen_view.gd. Leest de sim alleen.
## Aanhaken in main.gd na WereldView.bouw: `var mv = preload("res://view/missie_view.gd").new(); add_child(mv); mv.bouw(w, view)`.

const KNAL_S := 0.7

var w: Wereld
var view: WereldView
var nodes: Array[Dictionary] = []        ## {"ob": objectdict (zelfde referentie als in de sim), "node", "open": 0..1}
var knallen: Array[Dictionary] = []      ## {"node", "t"}
var _t := 0.0


func bouw(wereld: Wereld, wereld_view: WereldView) -> void:
	w = wereld
	view = wereld_view
	name = "MissieObjecten"
	for ob in w.objecten:
		if ob.get("dynamisch", false):
			_maak(ob)
	w.object_erbij.connect(_erbij)
	w.object_weg.connect(_weg)
	w.object_veranderd.connect(_veranderd)
	w.ontploffing.connect(_knal)


func _erbij(ob: Dictionary) -> void:
	if ob.get("dynamisch", false) and not ob.get("voorwerp", false):
		_maak(ob)


func _maak(ob: Dictionary) -> void:
	var n := Props.maak(ob)
	if n == null:
		n = Node3D.new()
	n.name = "%s_%d_%d" % [ob["naam"], ob["x"], ob["y"]]
	add_child(n)
	n.position = view.terrein.tegel_midden(Vector2i(ob["x"], ob["y"]))
	nodes.append({"ob": ob, "node": n, "open": 1.0 if ob.get("open", false) else 0.0})
	if ob.get("open", false):
		_zet_open(nodes[-1], 1.0)


func _van(ob: Dictionary) -> Dictionary:
	for e in nodes:
		if is_same(e["ob"], ob):
			return e
	return {}


func _weg(ob: Dictionary) -> void:
	var e := _van(ob)
	if e.is_empty():
		return
	if ob["naam"] == "stenen_muur":
		_stof(e["node"].position)
	(e["node"] as Node3D).queue_free()
	nodes.erase(e)


func _veranderd(ob: Dictionary) -> void:
	var e := _van(ob)
	if not e.is_empty() and ob.get("open", false):
		e["opent"] = true          # _process laat de deur wegzakken


## Deur van de poort: `poort_deur` (glb en placeholder) zakt en krimpt; bij 1 onzichtbaar.
func _zet_open(e: Dictionary, u: float) -> void:
	e["open"] = u
	var deur := _zoek(e["node"], "poort_deur")
	if deur == null:
		return
	if not e.has("deur_y"):
		e["deur_y"] = deur.position.y
	deur.position.y = float(e["deur_y"]) - 2.0 * u
	deur.scale = Vector3.ONE * maxf(0.01, 1.0 - 0.6 * u)
	deur.visible = u < 1.0


func _zoek(n: Node, naam: String) -> Node3D:
	if n.name == naam and n is Node3D:
		return n
	for c in n.get_children():
		var r := _zoek(c, naam)
		if r != null:
			return r
	return null


## Een mijn gaat af: oranje flits, een bol die uitzet en vervaagt, licht.
func _knal(t: Vector2i) -> void:
	var n := Node3D.new()
	n.name = "Knal"
	add_child(n)
	n.position = view.terrein.tegel_midden(t)
	var bol := MeshInstance3D.new()
	var s := SphereMesh.new()
	s.radius = 1.0
	s.height = 2.0
	bol.mesh = s
	var m := StandardMaterial3D.new()
	m.albedo_color = Color(1.0, 0.55, 0.15, 0.85)
	m.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
	m.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
	bol.material_override = m
	bol.name = "Bol"
	n.add_child(bol)
	var l := OmniLight3D.new()
	l.light_color = Color(1.0, 0.6, 0.2)
	l.light_energy = 6.0
	l.omni_range = 9.0
	l.position.y = 1.0
	n.add_child(l)
	knallen.append({"node": n, "t": 0.0})


func _stof(p: Vector3) -> void:
	var n := Node3D.new()
	add_child(n)
	n.position = p
	var bol := MeshInstance3D.new()
	var s := SphereMesh.new()
	s.radius = 1.0
	s.height = 2.0
	bol.mesh = s
	var m := StandardMaterial3D.new()
	m.albedo_color = Color(0.6, 0.57, 0.52, 0.6)
	m.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
	m.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
	bol.material_override = m
	bol.name = "Bol"
	n.add_child(bol)
	knallen.append({"node": n, "t": 0.0})


func _process(dt: float) -> void:
	_t += dt
	var tempo := 0.0 if w.gepauzeerd else w.tempo
	for e in nodes:
		if e.get("opent", false) and float(e["open"]) < 1.0:
			_zet_open(e, minf(1.0, float(e["open"]) + dt * tempo / 1.5))
		var ob: Dictionary = e["ob"]
		if ob["naam"] == "vuur":
			var n: Node3D = e["node"]
			for i in 5:
				var v := n.get_node_or_null("Vlam%d" % i) as Node3D
				if v != null:
					v.scale = Vector3.ONE * (0.8 + 0.3 * sin(_t * 9.0 + i * 1.7))
			var l := n.get_node_or_null("Licht") as OmniLight3D
			if l != null:
				l.light_energy = 2.0 + 0.8 * sin(_t * 13.0)
	for k in knallen.duplicate():
		k["t"] = float(k["t"]) + dt
		var u := float(k["t"]) / KNAL_S
		var n: Node3D = k["node"]
		if u >= 1.0:
			n.queue_free()
			knallen.erase(k)
			continue
		var bol := n.get_node("Bol") as MeshInstance3D
		bol.scale = Vector3.ONE * (0.3 + 1.7 * u)
		var m := bol.material_override as StandardMaterial3D
		m.albedo_color.a = 0.85 * (1.0 - u)
