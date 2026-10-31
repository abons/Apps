extends Node
## Scenario `sleep` (main.gd --scenario=sleep): sleept met echte muisinvoer (Input.parse_input_event, zoals een vinger
## met emulate_mouse_from_touch) een weg en daarna een hek door het bouwmenu, laat los en laat de dorpelingen bouwen.
## Frames: zie README (Draaien). Tegels naast het kampvuur van missie 1.

var m: Node            ## main.gd
var t := 0.0
var stap := 0
const WEG := [Vector2i(104, 67), Vector2i(112, 72)]
const HEK := [Vector2i(105, 74), Vector2i(114, 69)]


func start(main: Node) -> Node:
	m = main
	m.w.alles_open = true
	m.w.tempo = 2.0
	m.cam.zet_direct(m.view.terrein.tegel_midden(Vector2i(109, 70)) + Vector3(0, 0.4, 0), 0.35, deg_to_rad(42), 24.0)
	return self


func _scherm(tg: Vector2i) -> Vector2:
	return m.cam.unproject_position(m.view.terrein.tegel_midden(tg))


func _knop(pos: Vector2, aan: bool) -> void:
	var e := InputEventMouseButton.new()
	e.button_index = MOUSE_BUTTON_LEFT
	e.pressed = aan
	e.position = pos
	e.global_position = pos
	Input.parse_input_event(e)


func _beweeg(pos: Vector2) -> void:
	var e := InputEventMouseMotion.new()
	e.position = pos
	e.global_position = pos
	e.button_mask = MOUSE_BUTTON_MASK_LEFT
	Input.parse_input_event(e)


## Slepen van rij[0] naar rij[1] tussen t0 en t1 (s), loslaten op t1 + 0,5.
func _sleep(rij: Array, t0: float, t1: float, s0: int) -> void:
	if stap == s0 and t >= t0:
		m.bouwmenu.kies(&"weg" if rij == WEG else &"hek")
		_knop(_scherm(rij[0]), true)
		stap += 1
	elif stap == s0 + 1:
		var f := clampf((t - t0) / (t1 - t0), 0.0, 1.0)
		_beweeg(_scherm(rij[0]).lerp(_scherm(rij[1]), f))
		if t >= t1 + 0.5:
			_knop(_scherm(rij[1]), false)
			print("[scenario] %s gesleept: %d plannen, kas %d" % ["weg" if rij == WEG else "hek", m.w.plannen.size(), m.w.kas])
			stap += 1


func _process(dt: float) -> void:
	t += dt
	_sleep(WEG, 0.5, 2.5, 0)
	_sleep(HEK, 3.5, 5.5, 2)
	if stap == 4 and t >= 6.5:
		m.bouwmenu.zet_actief(false)
		m.w.tempo = 4.0
		stap = 5
