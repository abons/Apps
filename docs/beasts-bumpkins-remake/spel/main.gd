extends Node3D
## Beasts & Bumpkins remake, missie 1 (Aorta): zet sim (Wereld), view, licht, camera, besturing en HUD in elkaar.
## Opties na `--`:  --seizoen=lente|zomer|herfst|winter  --uur=12  --tempo=1|2|4  --regen  --scenario=overzicht|dorp|selectie|pad|vlag|bos|rots|bouw|claim|gezin|molen|melk|kippen|bouwer|hek|nacht
## Een scenario scriptt camera en invoer (voor frames met --write-movie); zonder scenario speel je zelf.

var w: Wereld
var licht: Licht
var view: WereldView
var cam: Camera3D
var bestuur: Bestuur
var hud: Hud
var bouwmenu: Bouwmenu
var scenario := ""
var szt := 0.0
var _stap := 0


func _ready() -> void:
	var opt := _opties()
	w = Wereld.new()
	if not w.laad():
		push_error("main: wereld laden mislukt (draai sync.ps1 en --import)")
		get_tree().quit(1)
		return
	if opt.has("seizoen"):
		var i: int = Wereld.SEIZOENEN.find(opt["seizoen"])
		if i >= 0:
			w.tijd_s = i * w.seizoen_duur() + w.dag_t()
	if opt.has("uur"):
		var u := float(opt["uur"])
		w.tijd_s = w.dag_nr() * w.seizoen_duur() + fposmod(u - 5.0, 24.0) / 24.0 * w.seizoen_duur()
	if opt.has("tempo"):
		w.tempo = float(opt["tempo"])
	if opt.has("regen"):
		w.regen_handmatig = 1
	scenario = opt.get("scenario", "")
	_fps_aan = opt.has("fps")
	_trace = opt.has("trace")
	if opt.has("gang"):
		Bumpkin.gang = int(opt["gang"])

	licht = Licht.new()
	licht.name = "Licht"
	add_child(licht)
	view = WereldView.new()
	view.name = "WereldView"
	add_child(view)
	view.bouw(w, licht)

	cam = Camera3D.new()
	cam.set_script(load("res://rts_camera.gd"))
	cam.name = "Camera"
	add_child(cam)
	var e := w.eiland
	var m := w.tegel_m
	cam.grens = Rect2(e.position.x * m - 6.0, e.position.y * m - 6.0, e.size.x * m + 12.0, e.size.y * m + 12.0)
	var vuur := view.terrein.tegel_midden(w.kampvuur)
	cam.zet_direct(vuur, 0.6, deg_to_rad(38), 24.0)
	cam.make_current()

	bestuur = Bestuur.new()
	bestuur.name = "Bestuur"
	add_child(bestuur)
	hud = Hud.new()
	hud.name = "Hud"
	add_child(hud)
	bestuur.w = w
	bestuur.view = view
	bestuur.cam = cam
	hud.bouw(w, bestuur)
	bestuur.kader = hud.kader
	bouwmenu = Bouwmenu.new()
	bouwmenu.name = "Bouwmenu"
	bouwmenu.terrein = view.terrein
	add_child(bouwmenu)
	bouwmenu.bouw(w, bestuur, self)
	if scenario != "":
		cam.invoer_aan = false
		_start_scenario()
	print("[spel] eiland ", w.eiland, " dorpelingen ", w.dorpelingen.size(), " objecten ", w.objecten.size(), " seizoen ", w.seizoen_naam())


func _opties() -> Dictionary:
	var uit := {}
	for a in OS.get_cmdline_user_args():
		if a.begins_with("--"):
			var kv := a.substr(2).split("=", true, 1)
			uit[kv[0]] = kv[1] if kv.size() > 1 else "1"
	return uit


var _trace := false
var _fps_aan := false
var _fps_n := 0
var _fps_som := 0.0
var _fps_max := 0.0
var _fps_trage := 0


func _process(dt: float) -> void:
	if _fps_aan:
		_fps_n += 1
		_fps_som += dt
		_fps_max = maxf(_fps_max, dt)
		if dt > 0.025:
			_fps_trage += 1
		if _fps_som >= 3.0:
			print("[fps] gem %.1f  langste frame %.1f ms  frames >25 ms: %d van %d" % [_fps_n / _fps_som, _fps_max * 1000.0, _fps_trage, _fps_n])
			_fps_n = 0; _fps_som = 0.0; _fps_max = 0.0; _fps_trage = 0
	w.vooruit(dt)
	if _trace:
		var u: Bumpkin = view.units[3]["bump"]
		print("[trace] t=%.3f tik=%d alpha=%.2f pos=(%.3f, %.3f) yaw=%.3f" % [szt, w.tik_nr, w.alpha(), u.global_position.x, u.global_position.z, u.rotation.y])
	view.regen.volg(cam.focus)
	if scenario != "":
		szt += dt
		_scenario_stap()


func _unhandled_input(e: InputEvent) -> void:
	if e is InputEventKey and e.pressed and not e.echo:
		match e.keycode:
			KEY_SPACE: w.gepauzeerd = not w.gepauzeerd
			KEY_1: w.tempo = 1.0
			KEY_2: w.tempo = 2.0
			KEY_4: w.tempo = 4.0
			KEY_K: w.regen_handmatig = {-1: 1, 1: 0, 0: -1}[w.regen_handmatig]
			KEY_N: w.tijd_s = (w.dag_nr() + 1) * w.seizoen_duur() + 60.0
			KEY_ESCAPE: get_tree().quit()


# ---------------------------------------------------------------- scenario's (frames voor verificatie)

func _start_scenario() -> void:
	var vuur := view.terrein.tegel_midden(w.kampvuur)
	var eiland_m := Vector3((w.eiland.position.x + w.eiland.size.x * 0.5) * w.tegel_m, 0, (w.eiland.position.y + w.eiland.size.y * 0.5) * w.tegel_m)
	match scenario:
		"overzicht":
			cam.zet_direct(eiland_m, 0.5, deg_to_rad(52), 125.0)
		"dorp":
			cam.zet_direct(vuur + Vector3(0, 0, 0), 0.5, deg_to_rad(26), 9.0)
		"selectie":
			cam.zet_direct(vuur + Vector3(2, 0, -2), 0.5, deg_to_rad(52), 26.0)
		"loop":
			cam.zet_direct(vuur + Vector3(4, 0, -2), 1.0, deg_to_rad(22), 8.0)
		"vlag":
			cam.zet_direct(view.terrein.tegel_midden(Vector2i(104, 65)) + Vector3(0, 1.6, 0), 0.9, deg_to_rad(12), 7.0)
		"bos":
			cam.zet_direct(view.terrein.tegel_midden(Vector2i(114, 50)), 0.8, deg_to_rad(24), 16.0)
		"koe":
			cam.zet_direct(view.terrein.tegel_midden(Vector2i(118, 58)) + Vector3(0, 0.6, 0), -2.2, deg_to_rad(28), 7.0)
		"gezin":
			# vier hutten staan al (8 bedden voor 6 mensen): het eerste stel gaat naar binnen, de baby komt eruit, 4x
			var eerste: Plan = null
			for i in 4:
				var p := _vrij_plan(&"hut", Vector2i(96 + (i % 2) * 6, 58 + (i / 2) * 14))
				if p != null and w.plan_zet(p):
					w._rond_af(p)
					if eerste == null:
						eerste = p
			w.tempo = 4.0
			var mid := view.terrein.tegel_midden(eerste.deur_tegel() if eerste != null else Vector2i(99, 65))
			cam.zet_direct(mid + Vector3(0, 0.6, 0), 0.6, deg_to_rad(32), 13.0)
		"molen":
			# molen + twee akkers bij het dorp; de akkers staan al bijna rijp, de dorpelingen oogsten, brengen en kopen, 4x
			w.alles_open = true
			var m := _vrij_plan(&"molen", Vector2i(96, 60))
			if m != null and w.plan_zet(m):
				w._rond_af(m)
			for bij in [Vector2i(104, 60), Vector2i(107, 60)]:
				var a := _vrij_plan(&"akker", bij)
				if a != null and w.plan_zet(a):
					w._rond_af(a)
			for t in w.akkers:
				w.akkers[t] = 50.0
			w.tempo = 4.0
			cam.zet_direct(view.terrein.tegel_midden(Vector2i(102, 62)) + Vector3(0, 0.6, 0), 0.6, deg_to_rad(36), 24.0)
		"melk":
			# melkerij bij het kampvuur, de wilde koe bij het dorp gezet: een volwassene melkt haar en brengt de melk weg, 4x
			w.alles_open = true
			var mk := _vrij_plan(&"melkerij", Vector2i(95, 62))
			if mk != null and w.plan_zet(mk):
				w._rond_af(mk)
			w.vee[0].zet_tegel(w.dichtstbij_loopbaar(w.kampvuur + Vector2i(4, -4)))
			w.vee[0].anker = w.vee[0].tegel()
			w.tempo = 4.0
			cam.zet_direct(view.terrein.tegel_midden(Vector2i(100, 63)) + Vector3(0, 0.6, 0), 0.6, deg_to_rad(36), 20.0)
		"kippen":
			# kippenhok bij het dorp; de eerste kip legt meteen, een volwassene raapt het ei en brengt het het hok in, 2x
			var kh := _vrij_plan(&"kippenhok", Vector2i(99, 62))
			if kh != null and w.plan_zet(kh):
				w._rond_af(kh)
			if not w.kippen.is_empty():
				w.kippen[0].leeg = 3.0
			w.tempo = 2.0
			cam.zet_direct(view.terrein.tegel_midden(kh.deur_tegel() if kh != null else Vector2i(99, 62)) + Vector3(0, 0.3, 0), 0.6, deg_to_rad(30), 9.0)
		"bouwer":
			# loods staat; een man laat zich bouwer maken en bouwt daarna een hut, naast een gewone man op een tweede hut, 4x
			var ld := _vrij_plan(&"gereedschapsloods", Vector2i(99, 61))
			if ld != null and w.plan_zet(ld):
				w._rond_af(ld)
			var mannen := []
			for d in w.dorpelingen:
				if d.volwassen() and d.geslacht == "man":
					mannen.append(d.id)
			if ld != null and mannen.size() >= 1:
				w.dorpeling(mannen[0]).zet_tegel(w.dichtstbij_loopbaar(ld.deur_tegel() + Vector2i(0, 2)))
				w.geef_gildebevel([mannen[0]], ld)
			w.tempo = 2.0
			var dt_ := ld.deur_tegel() if ld != null else Vector2i(101, 63)
			cam.zet_direct(view.terrein.tegel_midden(dt_ + Vector2i(0, 1)) + Vector3(0, 0.8, 0), 0.6, deg_to_rad(22), 6.0)
		"hek":
			# een weide van 6x5 tegels met een poort in de onderkant, meteen af; de poort gaat na 2 s open (via _scenario_stap)
			# en na 12 s weer dicht
			w.alles_open = true
			var o := Vector2i(106, 62)
			for x in range(6):
				for y in range(5):
					if x != 0 and x != 5 and y != 0 and y != 4:
						continue
					var srt := &"poort" if (x == 2 and y == 4) else &"hek"
					var hp := Plan.new(srt, o + Vector2i(x, y), 0, 1, 1)
					if w.plan_zet(hp):
						w._rond_af(hp)
			# een eigen koe buiten de poort: zodra die opengaat loopt ze de weide in (4x)
			var hk := w.vee[0]
			hk.zet_tegel(w.dichtstbij_loopbaar(o + Vector2i(2, 6)))
			hk.eigenaar = 0
			w._wijs_weides_toe()
			hk.wacht = 0.5
			w.tempo = 4.0
			cam.zet_direct(view.terrein.tegel_midden(o + Vector2i(3, 3)) + Vector3(0, 0.4, 0), 0.5, deg_to_rad(38), 13.0)
		"nacht":
			# een hut staat; bij het invallen van de nacht gaan er twee naar binnen en gaan de anderen bij het vuur liggen
			var nh := _vrij_plan(&"hut", Vector2i(98, 60))
			if nh != null and w.plan_zet(nh):
				w._rond_af(nh)
			w.tempo = 2.0
			cam.zet_direct(view.terrein.tegel_midden(w.kampvuur) + Vector3(0, 0.4, 0), 0.6, deg_to_rad(36), 14.0)
		"claim":
			# een volwassene loopt naar de wilde koe bij de generator en claimt haar (halsband + bel), 4x
			for d in w.dorpelingen:
				if d.volwassen():
					d.zet_tegel(w.vee[0].tegel() + Vector2i(-3, 1))
					w.geef_claimbevel([d.id], w.vee[0].id)
					break
			w.tempo = 2.0
			cam.zet_direct(view.terrein.tegel_midden(w.vee[0].tegel()) + Vector3(0, 0.6, 0), -2.2, deg_to_rad(24), 6.0)
		"rots":
			cam.zet_direct(view.terrein.tegel_midden(Vector2i(108, 44)), 0.4, deg_to_rad(30), 20.0)
		"klif":
			w.dorpeling(3).zet_tegel(Vector2i(108, 47))
			w.dorpeling(3).anker = Vector2i(108, 47)
			cam.zet_direct(view.terrein.tegel_midden(Vector2i(109, 49)) + Vector3(0, 1.0, 0), -1.1, deg_to_rad(22), 11.0)
		"bouw":
			# hut naast het kampvuur, alle volwassenen bouwen; tempo 4x zodat de vier standen in een korte opname passen
			# plus een loods en een kippenhok verderop, elk door een eigen volwassene
			var ids := []
			for d in w.dorpelingen:
				if d.volwassen():
					ids.append(d.id)
			var p := _vrij_plan(&"hut", Vector2i(99, 62))
			if p != null and w.plan_zet(p):
				w.geef_bouwbevel(ids.slice(0, 2), p)
			var l := _vrij_plan(&"gereedschapsloods", Vector2i(106, 60))
			if l != null and w.plan_zet(l):
				w.geef_bouwbevel(ids.slice(2, 3), l)
			var h := _vrij_plan(&"kippenhok", Vector2i(105, 66))
			if h != null and w.plan_zet(h):
				w.geef_bouwbevel(ids.slice(3, 4), h)
			w.tempo = 4.0
			cam.zet_direct(view.terrein.tegel_midden(Vector2i(105, 64)) + Vector3(0, 0.8, 0), 0.7, deg_to_rad(32), 21.0)
		"pad":
			# unit 3 in de noordoostelijke rotsboog zetten; het directe pad naar (118,58) loopt door rots
			w.dorpeling(3).zet_tegel(Vector2i(108, 47))
			w.dorpeling(3).anker = Vector2i(108, 47)
			cam.zet_direct(view.terrein.tegel_midden(Vector2i(113, 52)), 0.3, deg_to_rad(60), 34.0)


## Eerste plan van `soort` dat kan, in ringen rond `bij` (voor scenario's).
func _vrij_plan(soort: StringName, bij: Vector2i) -> Plan:
	for r in 8:
		for dy in range(-r, r + 1):
			for dx in range(-r, r + 1):
				if maxi(absi(dx), absi(dy)) == r:
					var p := w.maak_plan(soort, bij + Vector2i(dx, dy), 0)
					if p != null:
						return p
	return null


func _scenario_stap() -> void:
	match scenario:
		"hek":
			if _stap == 0 and szt >= 2.0:
				for p in w.plannen:
					if p.soort == &"poort":
						w.wissel_poort(p)
				_stap = 1
			elif _stap == 1 and szt >= 12.0:
				for p in w.plannen:
					if p.soort == &"poort":
						w.wissel_poort(p)
				_stap = 2
		"selectie":
			_selectie_stap()
		"pad":
			_pad_stap()
		"klif":
			_klif_stap()
		"loop":
			if _stap == 0 and szt >= 0.3:
				bestuur.gekozen = [1, 2, 3, 4, 5, 6]
				view.gekozen = bestuur.gekozen
				bestuur.geef_loopbevel(Vector2i(w.kampvuur.x + 12, w.kampvuur.y + 2))
				_stap = 1
			elif _stap == 1:
				cam.doel_focus = cam.doel_focus.lerp(view.unit_pos(3) + Vector3(0, 0, 0), 0.04)


func _selectie_stap() -> void:
	var alle := Rect2(Vector2.INF, Vector2.ZERO)
	var min_p := Vector2(1e9, 1e9)
	var max_p := Vector2(-1e9, -1e9)
	for d in w.dorpelingen:
		var s := cam.unproject_position(view.unit_pos(d.id) + Vector3(0, 0.9, 0))
		min_p = min_p.min(s)
		max_p = max_p.max(s)
	var doel := Rect2(min_p - Vector2(50, 60), (max_p - min_p) + Vector2(100, 110))
	if szt < 1.0:
		return
	if _stap == 0:
		# kader groeit vanuit de hoek
		var f := clampf((szt - 1.0) / 1.0, 0.0, 1.0)
		hud.kader.zet(Rect2(doel.position, doel.size * f), true)
		if f >= 1.0:
			_stap = 1
	elif _stap == 1 and szt >= 2.4:
		hud.kader.zet(Rect2(), false)
		bestuur.kies_in_rechthoek(doel)
		print("[scenario] gekozen: ", bestuur.gekozen.size())
		_stap = 2
	elif _stap == 2 and szt >= 3.4:
		var t := Vector2i(w.kampvuur.x + 9, w.kampvuur.y - 3)
		var n := bestuur.geef_loopbevel(t)
		print("[scenario] bevel naar ", t, " accepteerden ", n)
		w.tempo = 2.0
		_stap = 3


func _pad_stap() -> void:
	if _stap == 0 and szt >= 1.0:
		bestuur.gekozen = [3]
		view.gekozen = bestuur.gekozen
		_stap = 1
	elif _stap == 1 and szt >= 2.0:
		var n := bestuur.geef_loopbevel(Vector2i(118, 58))
		print("[scenario] pad-bevel accepteerden ", n, " route ", w.dorpeling(3).route.size(), " stappen")
		w.tempo = 2.0
		_stap = 2
	elif _stap == 2:
		pass


func _klif_stap() -> void:
	if _stap == 0 and szt >= 0.5:
		bestuur.gekozen = [3]
		view.gekozen = bestuur.gekozen
		bestuur.geef_loopbevel(Vector2i(111, 55))
		w.tempo = 1.0
		_stap = 1
	elif _stap == 1:
		cam.doel_focus = cam.doel_focus.lerp(view.unit_pos(3) + Vector3(1.5, 1.0, 0), 0.08)
