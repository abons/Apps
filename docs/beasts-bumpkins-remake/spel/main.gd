extends Node3D
## Beasts & Bumpkins remake: zet sim (Wereld), view, licht, camera, besturing en HUD in elkaar.
## Opties na `--`:  --missie=1|2|3 (standaard 1, spel.json `missies`)  --seizoen=lente|zomer|herfst|winter  --uur=12  --tempo=1|2|4  --regen  --scenario=overzicht|kaart|dorp|selectie|pad|vlag|wolf|bos|rots|bouw|claim|gezin|molen|melk|kalf|kippen|ei|bouwer|zagen|houweel|stapels|daken|hek|sleep|nacht|beker|deur|paddenstoel|mist_start|mist_verkend|mist_rand|minikaart|prijzen
## --mist=aan|uit: mist van oorlog (sim/mist.gd). Standaard aan in gewoon spel en in de mist_*- en minikaart-scenario's, uit in de
## andere scenario's (zodat hun frames gelijk blijven).
## Een scenario scriptt camera en invoer (voor frames met --write-movie); zonder scenario speel je zelf.
## Zonder --missie en --scenario begint het spel met het startmenu (view/startmenu.gd); een keuze daar, of in het
## pauzemenu (view/pauzemenu.gd, menuknop of Esc), laadt deze scène opnieuw met `Startmenu.volgende`.

var w: Wereld
var licht: Licht
var view: WereldView
var cam: Camera3D
var bestuur: Bestuur
var hud: Hud
var bouwmenu: Bouwmenu
var scenario := ""
var voorwerpen: Node3D            # view/voorwerpen_view.gd
var hints: Hints                  # sim/hints.gd, alleen in gewoon spel en --scenario=hints
var szt := 0.0
const RAND_M := 12.0              ## m marge buiten het 192x192-raster voor de camera (alleen met mist)
var _stap := 0
var startmenu: Startmenu           # alleen als er (nog) geen missie gekozen is
var pauzemenu: Pauzemenu          # view/pauzemenu.gd: menuknop of Esc, en na de missie


func _ready() -> void:
	Prestatie.merk("main _ready")
	var opt := _opties()
	var uit_menu := Startmenu.volgende > 0
	if Startmenu.naar_menu or (not uit_menu and not opt.has("missie") and not opt.has("scenario")):
		Startmenu.naar_menu = false
		set_process(false)
		startmenu = Startmenu.new()
		startmenu.name = "Startmenu"
		add_child(startmenu)
		return
	var nr := int(opt.get("missie", "1"))
	if uit_menu:                       # gekozen in het start- of pauzemenu: geen scenario, de opdrachtregel-missie telt niet
		nr = Startmenu.volgende
		Startmenu.volgende = 0
		opt.erase("scenario")
	w = Wereld.new()
	if not w.laad("", nr):
		push_error("main: wereld laden mislukt (draai sync.ps1 en --import)")
		get_tree().quit(1)
		return
	Prestatie.merk("wereld geladen (sim)")
	Voorladen.start(w.missie_nr)       # alleen mobiel: glb's parallel lezen (view/voorladen.gd)
	var laadscherm: CanvasLayer = null
	if Voorladen.aan or uit_menu:      # mobiel, of na een keuze in het menu: briefing als laadscherm, eerst een frame tekenen, dan opbouwen
		set_process(false)
		laadscherm = Voorladen.scherm(self, w)
		await get_tree().process_frame
		await get_tree().process_frame
		Prestatie.merk("laadscherm getekend")
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
	var mist_aan := scenario == "" or scenario.begins_with("mist") or scenario == "minikaart"
	if opt.has("mist"):
		mist_aan = opt["mist"] != "uit"
	w.mist.zet_aan(mist_aan)
	if opt.has("voordraai"):
		w.voorgebouwd_draai = int(opt["voordraai"])
	if opt.has("camyaw"):      # alleen voor frames: --camyaw=<graden> overschrijft na het scenario de camerahoek
		call_deferred("_camyaw", deg_to_rad(float(opt["camyaw"])))
	if opt.has("camwolf"):     # alleen voor frames: --camwolf=<afstand> volgt de eerste wolf van dichtbij (wolfmodel vergelijken)
		_camwolf = float(opt["camwolf"])
	_fps_aan = opt.has("fps")
	_trace = opt.has("trace")
	if opt.has("gang"):
		Bumpkin.gang = int(opt["gang"])

	licht = Licht.new()
	licht.name = "Licht"
	add_child(licht)
	Prestatie.merk("licht")
	view = WereldView.new()
	view.name = "WereldView"
	add_child(view)
	view.bouw(w, licht)
	Prestatie.merk("wereldview gebouwd")
	voorwerpen = preload("res://view/voorwerpen_view.gd").new()   # beker, kelk: op de grond en in de hand
	add_child(voorwerpen)
	voorwerpen.bouw(w, view)
	var mist_view := MistView.new()   # zwart over alles wat op onverkende tegels staat (shaders/mist.gdshader)
	add_child(mist_view)
	mist_view.bouw(w)

	Prestatie.merk("voorwerpen + mist")
	cam = Camera3D.new()
	cam.set_script(load("res://rts_camera.gd"))
	cam.name = "Camera"
	add_child(cam)
	var e := w.eiland
	var m := w.tegel_m
	cam.grens = Rect2(e.position.x * m - 6.0, e.position.y * m - 6.0, e.size.x * m + 12.0, e.size.y * m + 12.0)
	if w.mist.aan:   # het origineel liet je ver het zwart in scrollen: het hele raster plus marge (mist maakt alles zwart)
		cam.grens = Rect2(-RAND_M, -RAND_M, w.raster.kolommen * m + 2.0 * RAND_M, w.raster.rijen * m + 2.0 * RAND_M)
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
	bestuur.voorwerpen = voorwerpen
	hud.bouw(w, bestuur)
	bestuur.kader = hud.kader
	if scenario == "" or scenario == "hints":   # briefing en hints (sim/hints.gd); andere scenario's houden hun frames
		hints = Hints.new().bouw(w)
		hud.zet_hints(hints)
	Prestatie.merk("camera, bestuur, hud, hints")
	bouwmenu = Bouwmenu.new()
	bouwmenu.name = "Bouwmenu"
	bouwmenu.terrein = view.terrein
	bouwmenu.view = view            # bouwers kijken naar zaagbok of steenhoop
	add_child(bouwmenu)
	bouwmenu.bouw(w, bestuur, self)
	# een vinger slepen in de bouwmodus schuift de ghost (muisstijl) en pant niet; met touch-bouwen sleept alleen een
	# vinger op de ghost hem (Bouwmenu vangt die af), de rest pant
	cam.pan_blokkade = func() -> bool: return bouwmenu.actief and not Bouwmenu.touch
	Prestatie.merk("bouwmenu")
	var geluid: Node3D = preload("res://view/geluid.gd").new()   # stemmen, werk, dieren, omgeving (view/geluid.gd)
	add_child(geluid)
	geluid.bouw(w, view, cam, bestuur)
	Prestatie.merk("geluid")
	w.plaats_voorgebouwd()          # na view en bouwmenu: die tekenen het via plan_gezet/plan_klaar
	Prestatie.merk("voorgebouwd")
	pauzemenu = Pauzemenu.new()
	pauzemenu.name = "Pauzemenu"
	add_child(pauzemenu)
	pauzemenu.bouw(w, cam, bouwmenu)
	hud.menu_gevraagd.connect(pauzemenu.wissel)
	if scenario == "":
		Startmenu.bewaar_laatste(w.missie_nr)
		w.missie_einde.connect(_missie_einde)
	if scenario != "":
		cam.invoer_aan = false
		_start_scenario()
	if OS.has_feature("mobile") or opt.has("prestatie"):   # mobiele beeldinstellingen + fps-log (view/prestatie.gd)
		_prestatie = Prestatie.new()
		_prestatie.name = "Prestatie"
		add_child(_prestatie)
		_prestatie.bouw(self)
	Prestatie.merk("main _ready klaar")
	if laadscherm != null:
		laadscherm.queue_free()
		set_process(true)
	print("[spel] missie ", w.missie_nr, " (", w.missie.get("naam", "?"), ") eiland ", w.eiland, " dorpelingen ", w.dorpelingen.size(), " objecten ", w.objecten.size(), " seizoen ", w.seizoen_naam())


## Na de missie: gewonnen onthouden; na 2 s (de uitslag staat dan even in beeld) het einde-menu.
func _missie_einde(u: String) -> void:
	if u == "gewonnen":
		Startmenu.bewaar_gewonnen(w.missie_nr)
	get_tree().create_timer(2.0).timeout.connect(_open_einde.bind(u))


func _open_einde(u: String) -> void:
	if is_instance_valid(pauzemenu):
		pauzemenu.open_einde(u)


func _opties() -> Dictionary:
	var uit := {}
	for a in OS.get_cmdline_user_args():
		if a.begins_with("--"):
			var kv := a.substr(2).split("=", true, 1)
			uit[kv[0]] = kv[1] if kv.size() > 1 else "1"
	return uit


var _trace := false
var _camwolf := 0.0
var _fps_aan := false
var _prestatie: Prestatie
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
	if _prestatie != null:
		var t0 := Time.get_ticks_usec()
		w.vooruit(dt)
		_prestatie.sim_us += Time.get_ticks_usec() - t0
	else:
		w.vooruit(dt)
	if hints != null and not w.gepauzeerd:   # niet tijdens de briefing: 1-12 komt pas daarna
		hints.controleer()
	if _trace:
		var u: Bumpkin = view.units[3]["bump"]
		print("[trace] t=%.3f tik=%d alpha=%.2f pos=(%.3f, %.3f) yaw=%.3f" % [szt, w.tik_nr, w.alpha(), u.global_position.x, u.global_position.z, u.rotation.y])
	view.regen.volg(cam.focus)
	if scenario != "":
		szt += dt
		_scenario_stap()


func _unhandled_input(e: InputEvent) -> void:
	if w == null:
		return
	if e is InputEventKey and e.pressed and not e.echo:
		match e.keycode:
			KEY_SPACE: w.gepauzeerd = not w.gepauzeerd
			KEY_1: w.tempo = 1.0
			KEY_2: w.tempo = 2.0
			KEY_4: w.tempo = 4.0
			KEY_K: w.regen_handmatig = {-1: 1, 1: 0, 0: -1}[w.regen_handmatig]
			KEY_N: w.tijd_s = (w.dag_nr() + 1) * w.seizoen_duur() + 60.0
			KEY_ESCAPE: pauzemenu.open()      # bouwmodus vangt Esc eerst af (Bouwmenu), het open menu ook (Pauzemenu)


# ---------------------------------------------------------------- scenario's (frames voor verificatie)

func _start_scenario() -> void:
	var vuur := view.terrein.tegel_midden(w.kampvuur)
	var eiland_m := Vector3((w.eiland.position.x + w.eiland.size.x * 0.5) * w.tegel_m, 0, (w.eiland.position.y + w.eiland.size.y * 0.5) * w.tegel_m)
	match scenario:
		"mist_start":
			# de startview met mist, iets hoger dan het gewone begin zodat de rand rondom te zien is
			cam.zet_direct(vuur, 0.6, deg_to_rad(44), 46.0)
		"mist_verkend":
			# alle dorpelingen lopen 22 tegels naar het oosten en verkennen onderweg (4x); daarna van boven
			bestuur.gekozen = w.dorpelingen.map(func(d: Dorpeling) -> int: return d.id)
			bestuur.geef_loopbevel(w.dichtstbij_loopbaar(w.kampvuur + Vector2i(22, -4)))
			w.tempo = 4.0
			cam.zet_direct(vuur + Vector3(16, 0, -4), 0.6, deg_to_rad(52), 62.0)
		"minikaart":
			# gewone startcamera; alle dorpelingen lopen 22 tegels naar het oosten (4x); na 8 s een klik op de minikaart
			# op de voorste dorpeling: de camera springt erheen (view/minikaart.gd)
			bestuur.gekozen = w.dorpelingen.map(func(d: Dorpeling) -> int: return d.id)
			bestuur.geef_loopbevel(w.dichtstbij_loopbaar(w.kampvuur + Vector2i(22, -4)))
			w.tempo = 4.0
			cam.zet_direct(vuur, 0.6, deg_to_rad(40), 26.0)
		"prijzen":
			# het prijzenscherm (view/prijzen.gd) open boven het dorp: brood duurder, eieren goedkoper (sim op pauze)
			cam.zet_direct(vuur, 0.6, deg_to_rad(40), 26.0)
			w.handel.zet_prijs("brood", 7)
			w.handel.zet_prijs("ei", 2)
			hud.prijzen.open()
		"mist_rand":
			# de camera in de hoek van het raster (grens met mist: raster + RAND_M), van ver: alleen zwart
			cam.zet_direct(Vector3(-RAND_M, 0, -RAND_M), 0.6, deg_to_rad(30), 125.0)
		"overzicht":
			cam.zet_direct(eiland_m, 0.5, deg_to_rad(52), 125.0)
		"kaart":
			# bijna recht van boven, noord (kleine y) boven: naast lokaal/missies/m<nn>_layout.png te leggen
			cam.zet_direct(eiland_m, 0.0, deg_to_rad(82), 1.25 * maxf(w.eiland.size.x, w.eiland.size.y) * w.tegel_m)
		"dorp":
			cam.zet_direct(vuur + Vector3(0, 0, 0), 0.5, deg_to_rad(26), 9.0)
		"selectie":
			cam.zet_direct(vuur + Vector3(2, 0, -2), 0.5, deg_to_rad(52), 26.0)
		"loop":
			cam.zet_direct(vuur + Vector3(4, 0, -2), 1.0, deg_to_rad(22), 8.0)
		"vlag":
			cam.zet_direct(view.terrein.tegel_midden(_object_tegel("vlag", Vector2i(104, 65))) + Vector3(0, 1.6, 0), 0.9, deg_to_rad(12), 7.0)
		"hints":
			# --scenario=hints, missie 1: briefing (na 1,5 s weggeklikt), rolletje 1-12, op 4x tempo brief 1-2; na het wegklikken staat er
			# meteen een afgebouwde hut en opent brief 1-3 (frame screenshots/missie1_hint.jpg)
			w.tempo = 4.0
			cam.zet_direct(vuur, 0.6, deg_to_rad(40), 26.0)
		"beker":
			# missie 1: een man staat bij de zilveren beker, raapt hem op (pakbevel) en loopt ermee naar de vlag
			_beker_scenario()
		"wolf":
			# missie 2: de eerste wolf besluipt een wilde koe, een man krijgt na 1 s een vechtbevel en gooit stenen
			_wolf_scenario()
		"bos":
			cam.zet_direct(view.terrein.tegel_midden(Vector2i(114, 50)), 0.8, deg_to_rad(24), 16.0)
		"koe":
			cam.zet_direct(view.terrein.tegel_midden(Vector2i(118, 58)) + Vector3(0, 0.6, 0), -2.2, deg_to_rad(28), 7.0)
		"paddenstoel":
			# missie 1: de paddenstoel op (101,59) met een man ernaast voor de maat
			var pt := _object_tegel("paddenstoel", Vector2i(101, 59))
			for d in w.dorpelingen:
				if d.volwassen() and d.geslacht == "man":
					d.zet_tegel(w.dichtstbij_loopbaar(pt + Vector2i(1, 0)))
					d.route.clear()
					d.bevel = {}
					d.anker = d.tegel()
					break
			cam.zet_direct(view.terrein.tegel_midden(pt) + Vector3(0.8, 0.5, 0), 0.5, deg_to_rad(30), 7.0)
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
		"kalf":
			# lente: drie eigen koeien bij elkaar bij het kampvuur; na 2 s samen kalven ze (kans 1), het kalf loopt bij de moeder
			w.spel["economie"]["kalf_kans"] = 1.0
			w.spel["economie"]["kalf_samen_s"] = 2.0
			while w.vee.size() < 3:
				w._spawn_koe()
			for i in w.vee.size():
				var k: Vee = w.vee[i]
				k.eigenaar = 0
				k.van_generator = false
				k.anker = w.kampvuur + Vector2i(4, -4)
				k.zet_tegel(w.dichtstbij_loopbaar(k.anker + Vector2i(i * 2 - 2, i % 2)))
				w.koe_geclaimd.emit(k)
			cam.zet_direct(view.terrein.tegel_midden(w.kampvuur + Vector2i(4, -4)) + Vector3(0, 0.4, 0), 0.6, deg_to_rad(34), 9.0)
		"kippen":
			# kippenhok bij het dorp; de eerste kip legt meteen, een volwassene raapt het ei en brengt het het hok in, 2x
			var kh := _vrij_plan(&"kippenhok", Vector2i(99, 62))
			if kh != null and w.plan_zet(kh):
				w._rond_af(kh)
			if not w.kippen.is_empty():
				w.kippen[0].leeg = 3.0
			w.tempo = 2.0
			cam.zet_direct(view.terrein.tegel_midden(kh.deur_tegel() if kh != null else Vector2i(99, 62)) + Vector3(0, 0.3, 0), 0.6, deg_to_rad(30), 9.0)
		"ei":
			# kippenhok bij het dorp; alle kippen leggen meteen en blijven 6 s ongestoord op hun ei (vast), daarna raapt een
			# volwassene ze en brengt ze het hok in (view/kip_model.gd zet_ei)
			var kh := _vrij_plan(&"kippenhok", Vector2i(99, 62))
			if kh != null and w.plan_zet(kh):
				w._rond_af(kh)
			for k in w.kippen:
				k.leeg = 0.5
				k.vast = true
			var kt: Vector2i = w.kippen[0].tegel() if not w.kippen.is_empty() else Vector2i(99, 62)
			cam.zet_direct(view.terrein.tegel_midden(kt), 0.6, deg_to_rad(42), 7.0)
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
		"zagen", "houweel":
			# houweel: hetzelfde, maar de bouwer begint met de houweel (werk_zaad 2 in _scenario_stap, Bumpkin.WERK_REEKS).
			# een hut naast het kampvuur, twee mannen bouwen; de eerste is meteen bouwer (eigen model), dichtbij, de camera van voren.
			# Bouwers wisselen hamer, zaag en houweel af (Bumpkin.WERK_WISSEL, per id een ander begin); bij de zaagbok de zaag,
			# bij de steenhoop de houweel (Bouwmenu.STAPEL_WERK)
			var ids := []
			for d in w.dorpelingen:
				if d.volwassen() and d.geslacht == "man":
					ids.append(d.id)
			var p := _vrij_plan(&"hut", Vector2i(99, 62))
			if p != null and w.plan_zet(p) and not ids.is_empty():
				_wolf_man = w.dorpeling(ids[0])           # de camera volgt hem (_scenario_stap)
				_wolf_man.rol = "bouwer"
				w.rol_veranderd.emit(_wolf_man)
				w.geef_bouwbevel(ids.slice(0, 2), p)
			var pt: Vector2i = p.deur_tegel() if p != null else Vector2i(99, 62)
			cam.zet_direct(view.terrein.tegel_midden(pt) + Vector3(0, 0.6, 0), 3.7, deg_to_rad(26), 5.0)
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
		"daken":
			# hut, melkerij en kippenhok af naast elkaar: het riet van de drie vergelijken (gebakken halmen, 2026-10-30)
			w.alles_open = true
			for sd in [[&"hut", Vector2i(98, 60)], [&"melkerij", Vector2i(103, 59)], [&"kippenhok", Vector2i(108, 61)]]:
				var dp := _vrij_plan(sd[0], sd[1])
				if dp != null and w.plan_zet(dp):
					w._rond_af(dp)
			cam.zet_direct(view.terrein.tegel_midden(Vector2i(104, 61)) + Vector3(0, 1.0, 0), 0.7, deg_to_rad(36), 17.0)
		"stapels":
			# vijf bouwplaatsen in alle vier draaiingen: zaagbok en steenhoop staan aan de deurkant, naast de deur
			w.alles_open = true
			for sd in [[&"hut", Vector2i(97, 60), 0], [&"melkerij", Vector2i(104, 58), 1], [&"kippenhok", Vector2i(110, 62), 2],
					[&"gereedschapsloods", Vector2i(97, 68), 3], [&"molen", Vector2i(105, 68), 0]]:
				var sp := _vrij_plan(sd[0], sd[1], sd[2])
				if sp != null and w.plan_zet(sp):
					sp.voortgang = 0.7      # stand 3: het gebouw is te zien, de stapels nog groot genoeg
			cam.zet_direct(view.terrein.tegel_midden(Vector2i(104, 63)), 0.7, deg_to_rad(52), 22.0)
		"bouw2":
			# molen en melkerij naast het kampvuur, elk door de helft van de volwassenen, 4x: alle vier de bouwstanden
			w.alles_open = true
			var ids2 := []
			for d in w.dorpelingen:
				if d.volwassen():
					ids2.append(d.id)
			var ml := _vrij_plan(&"molen", Vector2i(98, 60))
			if ml != null and w.plan_zet(ml):
				w.geef_bouwbevel(ids2.slice(0, 2), ml)
			var mk2 := _vrij_plan(&"melkerij", Vector2i(105, 61))
			if mk2 != null and w.plan_zet(mk2):
				w.geef_bouwbevel(ids2.slice(2, 4), mk2)
			w.tempo = 4.0
			cam.zet_direct(view.terrein.tegel_midden(Vector2i(103, 62)) + Vector3(0, 0.8, 0), 0.7, deg_to_rad(32), 21.0)
		"missie3":
			# missie 3: dorp, voetsoldaat worden + wolf, put (test/missie3_scenario.gd, --stap=dorp|soldaat|put)
			add_child(load("res://test/missie3_scenario.gd").new().start(self))
		"deur":
			# een dorpeling loopt door de voordeur naar binnen en weer naar buiten (test/deur_scenario.gd, --gebouw= --draai=)
			add_child(load("res://test/deur_scenario.gd").new().start(self))
		"sleep":
			# een weg en een hek slepen door het bouwmenu, met echte muisinvoer (test/sleep_scenario.gd)
			add_child(load("res://test/sleep_scenario.gd").new().start(self))
		"pad":
			# unit 3 in de noordoostelijke rotsboog zetten; het directe pad naar (118,58) loopt door rots
			w.dorpeling(3).zet_tegel(Vector2i(108, 47))
			w.dorpeling(3).anker = Vector2i(108, 47)
			cam.zet_direct(view.terrein.tegel_midden(Vector2i(113, 52)), 0.3, deg_to_rad(60), 34.0)


var _wolf_man: Dorpeling = null


func _beker_scenario() -> void:
	var bekers := Voorwerpen.alle(w)
	if bekers.is_empty():
		return
	var b: Dictionary = bekers[0]
	for d in w.dorpelingen:
		if d.volwassen() and d.geslacht == "man":
			_wolf_man = d
			break
	_wolf_man.zet_tegel(w.dichtstbij_loopbaar(Vector2i(b["x"] - 3, b["y"] + 2)))
	_wolf_man.route.clear()
	_wolf_man.bevel = {}
	_wolf_man.anker = _wolf_man.tegel()
	cam.zet_direct(view.terrein.tegel_midden(Vector2i(b["x"] - 1, b["y"] + 1)), 0.5, deg_to_rad(34), 9.0)


## Scenario wolf: op open grasland (12x8 vrij) staat de eerste wolf aan de oostkant, een wilde koe 5 tegels west en een
## man nog 4 tegels verder; de koe houdt het langer vol (koe_beten 20) zodat de stenen vliegen terwijl de wolf bijt.
func _wolf_scenario() -> void:
	if w.wolven.is_empty():
		return
	var wf: Wolf = w.wolven[0]
	w.spel["wolf"]["koe_beten"] = 20
	var o := Vector2i(-1, -1)
	for r in range(6, 30):
		for dy in range(-r, r + 1):
			for dx in range(-r, r + 1):
				if o.x >= 0 or maxi(absi(dx), absi(dy)) != r:
					continue
				var c := w.kampvuur + Vector2i(dx, dy)
				var vrij := true
				for ey in range(-2, 10):
					for ex in range(-2, 14):
						var t := c + Vector2i(ex, ey)
						if not w.raster.loopbaar_v(t) or w.bereik[w.raster.idx(t.x, t.y)] == 0:
							vrij = false
				if vrij:
					o = c
	if o.x < 0:
		o = wf.tegel() + Vector2i(-11, -3)
	wf.zet_tegel(o + Vector2i(11, 3))
	wf.anker = wf.tegel()
	var kt := o + Vector2i(6, 4)
	# niet op een kaartobject: in M2 lag hier een paddenstoel (klasse 83, schaal 2,3), die stak als bruine koepel
	# door de koe heen (screenshots/wolf_model.jpg)
	for _i in 8:
		var bezet := false
		for ob in w.objecten:
			if Vector2i(ob["x"], ob["y"]) == kt:
				bezet = true
		if not bezet:
			break
		kt.y += 1
	var k := Vee.new()
	k.id = w._volgende_koe_id
	w._volgende_koe_id += 1
	k.zet_tegel(kt)
	k.anker = kt
	k.wacht = 99.0
	w.vee.append(k)
	w.koe_erbij.emit(k)
	for d in w.dorpelingen:
		if d.volwassen() and d.geslacht == "man":
			_wolf_man = d
			break
	_wolf_man.zet_tegel(o + Vector2i(1, 5))
	_wolf_man.route.clear()
	_wolf_man.bevel = {}
	_wolf_man.anker = _wolf_man.tegel()
	cam.zet_direct(view.terrein.tegel_midden(kt) + Vector3(-3.0, 0.4, 0), 0.25, deg_to_rad(50), 11.0)


## Tegel van het eerste kaartobject met `naam` (voor scenario's op elke kaart), anders `anders`.
func _object_tegel(naam: String, anders: Vector2i) -> Vector2i:
	for ob in w.objecten:
		if ob["naam"] == naam:
			return Vector2i(ob["x"], ob["y"])
	return anders


## Eerste plan van `soort` dat kan, in ringen rond `bij` (voor scenario's).
func _vrij_plan(soort: StringName, bij: Vector2i, draai := 0) -> Plan:
	for r in 8:
		for dy in range(-r, r + 1):
			for dx in range(-r, r + 1):
				if maxi(absi(dx), absi(dy)) == r:
					var p := w.maak_plan(soort, bij + Vector2i(dx, dy), draai)
					if p != null:
						return p
	return null


func _hints_stap() -> void:
	if _stap == 0 and szt >= 1.5:
		hud.brief.sluit()
		_stap = 1
	elif _stap == 1 and "1-2" in hints.getoond and szt >= 5.0:
		print("[scenario] 1-2 op %.1f s sim" % hints.sinds_start_s())
		hud.brief.sluit()
		var p := _vrij_plan(&"hut", w.kampvuur + Vector2i(5, 3))
		if p != null and w.plan_zet(p):
			p.voortgang = 1.0
		_stap = 2
	elif _stap == 2 and "1-3" in hints.getoond:
		print("[scenario] getoond: ", hints.getoond)
		_stap = 3


func _camyaw(y: float) -> void:
	cam.zet_direct(cam.focus, y, cam.pitch, cam.afstand)


func _scenario_stap() -> void:
	if _camwolf > 0.0 and not w.wolven.is_empty():
		var wp: Vector3 = view.wolven.wolf_pos(w.wolven[0].id)
		if wp.is_finite():
			cam.zet_direct(wp + Vector3(0, 0.4, 0), cam.yaw, deg_to_rad(28), _camwolf)
	match scenario:
		"hints":
			_hints_stap()
		"zagen", "houweel":
			if _wolf_man != null:
				cam.doel_focus = cam.doel_focus.lerp(view.unit_pos(_wolf_man.id) + Vector3(0, 0.6, 0), 0.05)
				if scenario == "houweel" and view.units.has(_wolf_man.id):
					(view.units[_wolf_man.id]["bump"] as Bumpkin).werk_zaad = 2   # leest hij bij de eerste werkstart
		"ei":
			if _stap == 0 and szt >= 6.0:
				_stap = 1
				for k in w.kippen:
					k.vast = false
		"minikaart":
			if _stap == 0 and szt >= 8.0:
				_stap = 1
				var mk := hud.minikaart
				var voor: Dorpeling = w.dorpelingen[0]
				for d in w.dorpelingen:
					if d.pos.x > voor.pos.x:
						voor = d
				var p := mk.global_position + Vector2(Minikaart.RAND, Minikaart.RAND) + mk.naar_venster(voor.pos)
				for druk in [true, false]:
					var e := InputEventMouseButton.new()
					e.button_index = MOUSE_BUTTON_LEFT
					e.pressed = druk
					e.position = p
					e.global_position = p
					Input.parse_input_event(e)
				print("[scenario] klik minikaart op ", voor.tegel(), " (", p, ")")
			elif _stap == 1 and szt >= 8.5:
				_stap = 2
				print("[scenario] camerabrandpunt nu tegel ", Vector2(cam.focus.x, cam.focus.z) / w.tegel_m)
		"beker":
			if _wolf_man == null or Voorwerpen.alle(w).is_empty():
				return
			var b: Dictionary = Voorwerpen.alle(w)[0]
			if _stap == 0 and szt >= 0.5:
				bestuur.gekozen = [_wolf_man.id]
				view.gekozen = bestuur.gekozen
				print("[scenario] pakbevel ", Voorwerpen.geef_pakbevel(w, bestuur.gekozen, b))
				_stap = 1
			elif _stap == 1 and int(b["drager"]) == _wolf_man.id:
				print("[scenario] beker opgeraapt op ", szt, " s")
				bestuur.geef_loopbevel(w.dichtstbij_loopbaar(_object_tegel("vlag", Vector2i(104, 65))))
				_stap = 2
			if _stap >= 1:
				cam.doel_focus = cam.doel_focus.lerp(view.unit_pos(_wolf_man.id), 0.05)
		"wolf":
			if _stap == 0 and szt >= 1.0 and _wolf_man != null and not w.wolven.is_empty():
				bestuur.gekozen = [_wolf_man.id]
				view.gekozen = bestuur.gekozen
				w.geef_vechtbevel(bestuur.gekozen, w.wolven[0].id)
				_stap = 1
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
