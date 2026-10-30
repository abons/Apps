extends Camera3D
## RTS-camera: draaien om een brandpunt, pannen, zoomen van deurhoogte (~2 m) tot eilandoverzicht (~130 m), begrensd
## tot `grens` (main.gd: met mist het hele raster plus marge, zoals het origineel ver het zwart in liet scrollen).
## Alle invoer zet doelwaarden; _process loopt er zacht naartoe.
## Touch (alleen InputEventScreenTouch/Drag, op pc dus niets): een vinger slepen = pannen (niet als `pan_blokkade`
## true geeft: bouwmenu actief), twee vingers: midden slepen = pannen, knijpen = zoom, draaien = yaw. Een tik blijft
## via emulate_mouse_from_touch een linkerklik (Bestuur, bouwmenu, minikaart). Randpannen staat op mobiel uit.

const AFSTAND_MIN := 2.0
const AFSTAND_MAX := 130.0
const PITCH_MIN := deg_to_rad(4.0)
const PITCH_MAX := deg_to_rad(82.0)
const RAND := 12  # px voor rand-pannen

var doel_focus := Vector3(0.65, 0.0, 0.05)
var doel_yaw := 0.6
var doel_pitch := deg_to_rad(40.0)
var doel_afstand := 18.0

var focus := doel_focus
var yaw := doel_yaw
var pitch := doel_pitch
var afstand := doel_afstand

var grens := Rect2(-1e6, -1e6, 2e6, 2e6)   # m (x,z): waar het brandpunt mag komen, door main.gd gezet
var invoer_aan := true
var rand_pannen := true
var _draaien := false
var pan_blokkade := Callable()   # main.gd: true = een vinger slepen pant niet (bouwmenu actief)
const TOUCH_DREMPEL := 12.0      # px: minder slepen telt als tik
var _vingers := {}               # index -> positie, alleen aanrakingen die hier (buiten de GUI) begonnen
var _touch_start := Vector2.ZERO
var touch_pant := false          # vinger voorbij de drempel of twee vingers: Bestuur maakt er geen klik van


func _ready() -> void:
	fov = 50.0
	near = 0.05
	far = 1500.0
	_plaats()


func zet_direct(f: Vector3, y: float, p: float, a: float) -> void:
	doel_focus = f; doel_yaw = y; doel_pitch = p; doel_afstand = a
	focus = f; yaw = y; pitch = p; afstand = a
	_plaats()


## Brandpunt direct naar `f` (minikaart: klik = springen), binnen `grens`; hoek en zoom blijven.
func spring_naar(f: Vector3) -> void:
	f.x = clampf(f.x, grens.position.x, grens.end.x)
	f.z = clampf(f.z, grens.position.y, grens.end.y)
	doel_focus = f
	focus = f
	if is_inside_tree():
		_plaats()


func _unhandled_input(e: InputEvent) -> void:
	if not invoer_aan:
		return
	if e is InputEventScreenTouch or e is InputEventScreenDrag:
		_touch(e)
		return
	if e is InputEventMouseButton:
		match e.button_index:
			MOUSE_BUTTON_WHEEL_UP:
				if e.pressed: doel_afstand = clampf(doel_afstand / 1.15, AFSTAND_MIN, AFSTAND_MAX)
			MOUSE_BUTTON_WHEEL_DOWN:
				if e.pressed: doel_afstand = clampf(doel_afstand * 1.15, AFSTAND_MIN, AFSTAND_MAX)
			MOUSE_BUTTON_RIGHT, MOUSE_BUTTON_MIDDLE:
				_draaien = e.pressed
			# Links is voor selectie en bevelen (Bestuur); pannen kan met WASD/pijlen of de schermrand.
	elif e is InputEventMouseMotion:
		if _draaien:
			doel_yaw -= e.relative.x * 0.006
			doel_pitch = clampf(doel_pitch + e.relative.y * 0.005, PITCH_MIN, PITCH_MAX)


func _touch(e: InputEvent) -> void:
	var idx: int = e.index
	var pos: Vector2 = e.position
	if e is InputEventScreenTouch:
		if e.pressed:
			_vingers[idx] = pos
			if _vingers.size() == 1:
				_touch_start = pos
				touch_pant = false
			else:
				touch_pant = true           # twee vingers: nooit een tik of kader
		else:
			_vingers.erase(idx)      # touch_pant blijft staan tot de volgende eerste vinger (Bestuur leest het bij loslaten)
		return
	if not _vingers.has(idx):
		return
	var oud: Vector2 = _vingers[idx]
	if _vingers.size() == 1:
		if not touch_pant and pos.distance_to(_touch_start) > TOUCH_DREMPEL:
			if pan_blokkade.is_valid() and pan_blokkade.call():
				_vingers[idx] = pos
				return
			touch_pant = true
		if touch_pant:
			_pan_scherm(pos - oud)
	else:
		var ander: int = idx
		for i in _vingers:
			if i != idx:
				ander = i
				break
		var p2: Vector2 = _vingers[ander]
		var d_oud := oud.distance_to(p2)
		var d_nieuw := pos.distance_to(p2)
		if d_oud > 1.0 and d_nieuw > 1.0:
			doel_afstand = clampf(doel_afstand * d_oud / d_nieuw, AFSTAND_MIN, AFSTAND_MAX)
			doel_yaw -= wrapf((pos - p2).angle() - (oud - p2).angle(), -PI, PI)
		_pan_scherm((pos - oud) * 0.5)
	_vingers[idx] = pos


## Schuift het brandpunt zo dat de grond ongeveer met de vinger meegaat (`d` = schermverschuiving in px).
func _pan_scherm(d: Vector2) -> void:
	var h := get_viewport().get_visible_rect().size.y
	var m_per_px := 2.0 * doel_afstand * tan(deg_to_rad(fov) * 0.5) / maxf(h, 1.0)
	doel_focus += (-_rechts() * d.x + _vooruit() * d.y / maxf(sin(pitch), 0.35)) * m_per_px


func _rechts() -> Vector3:
	return Vector3(cos(yaw), 0, -sin(yaw))


func _vooruit() -> Vector3:
	return Vector3(-sin(yaw), 0, -cos(yaw))


func _process(dt: float) -> void:
	if invoer_aan:
		var v := Vector2.ZERO
		if Input.is_key_pressed(KEY_W) or Input.is_key_pressed(KEY_UP): v.y += 1
		if Input.is_key_pressed(KEY_S) or Input.is_key_pressed(KEY_DOWN): v.y -= 1
		if Input.is_key_pressed(KEY_D) or Input.is_key_pressed(KEY_RIGHT): v.x += 1
		if Input.is_key_pressed(KEY_A) or Input.is_key_pressed(KEY_LEFT): v.x -= 1
		if rand_pannen and not OS.has_feature("mobile") and DisplayServer.window_is_focused() and not _draaien:
			var m := get_viewport().get_mouse_position()
			var r := get_viewport().get_visible_rect().size
			if m.x >= 0 and m.y >= 0 and m.x <= r.x and m.y <= r.y:
				if m.x < RAND: v.x -= 1
				elif m.x > r.x - RAND: v.x += 1
				if m.y < RAND: v.y += 1
				elif m.y > r.y - RAND: v.y -= 1
		if v != Vector2.ZERO:
			var snel := (4.0 + doel_afstand * 0.9) * dt
			doel_focus += (_rechts() * v.x + _vooruit() * v.y).normalized() * snel
		if Input.is_key_pressed(KEY_Q): doel_yaw += 1.6 * dt
		if Input.is_key_pressed(KEY_E): doel_yaw -= 1.6 * dt
		if Input.is_key_pressed(KEY_PAGEUP): doel_pitch = clampf(doel_pitch + 1.0 * dt, PITCH_MIN, PITCH_MAX)
		if Input.is_key_pressed(KEY_PAGEDOWN): doel_pitch = clampf(doel_pitch - 1.0 * dt, PITCH_MIN, PITCH_MAX)
	doel_focus.x = clampf(doel_focus.x, grens.position.x, grens.end.x)
	doel_focus.z = clampf(doel_focus.z, grens.position.y, grens.end.y)
	var k := 1.0 - exp(-8.0 * dt)
	focus = focus.lerp(doel_focus, k)
	yaw = lerpf(yaw, doel_yaw, k)
	pitch = lerpf(pitch, doel_pitch, k)
	afstand = exp(lerpf(log(afstand), log(doel_afstand), k))
	_plaats()


func _plaats() -> void:
	# Dichtbij kijkt de camera op deurhoogte, ver weg naar de grond.
	var t := clampf((afstand - AFSTAND_MIN) / 10.0, 0.0, 1.0)
	var doel := focus + Vector3(0, lerpf(1.1, 0.0, t), 0)
	var p := pitch
	var off := Vector3(sin(yaw) * cos(p), sin(p), cos(yaw) * cos(p)) * afstand
	var pos := doel + off
	pos.y = maxf(pos.y, 0.3)
	global_position = pos
	look_at(doel, Vector3.UP)
