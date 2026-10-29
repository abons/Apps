extends Camera3D
## RTS-camera: draaien om een brandpunt, pannen, zoomen van deurhoogte (~2 m) tot eilandoverzicht (~130 m), begrensd tot het eiland.
## Alle invoer zet doelwaarden; _process loopt er zacht naartoe.

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

var grens := Rect2(-1e6, -1e6, 2e6, 2e6)   # m (x,z): waar het brandpunt mag komen, door main.gd op het eiland gezet
var invoer_aan := true
var rand_pannen := true
var _draaien := false


func _ready() -> void:
	fov = 50.0
	near = 0.05
	far = 1500.0
	_plaats()


func zet_direct(f: Vector3, y: float, p: float, a: float) -> void:
	doel_focus = f; doel_yaw = y; doel_pitch = p; doel_afstand = a
	focus = f; yaw = y; pitch = p; afstand = a
	_plaats()


func _unhandled_input(e: InputEvent) -> void:
	if not invoer_aan:
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
		if rand_pannen and DisplayServer.window_is_focused() and not _draaien:
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
