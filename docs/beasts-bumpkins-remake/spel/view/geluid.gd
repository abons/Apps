extends Node3D
## Geluid voor missie 1 (audio.md sectie 3 en 4): stemmen, werk, dieren, omgeving, interface.
## Leest de sim (Wereld) en de view, schrijft er niets in. De enige plek die AudioStreamPlayer's maakt.
## Aanhaken: `var g := preload("res://view/geluid.gd").new(); add_child(g); g.bouw(w, view, cam, bestuur)`.
##
## Bronnen (audio.md, "Wat er nu in zit"): stemmen, koe, kip-mp3 en de 7 eigen wav uit beasts-src
## (assets/audio/beasts/, door audio/haal_beasts.ps1, niet in git); de rest eigen synthese uit
## audio/maak_geluid.py (audio/eigen/, wel in git). Ontbreekt een bestand, dan blijft dat geluid stil.

## Busvolumes in dB, de enige plek. Master krijgt een limiter.
const BUSSEN := {"Master": 0.0, "Effecten": -2.0, "Stemmen": 0.0, "Omgeving": -6.0}
const EIGEN := "res://audio/eigen/"
const BEASTS := "res://assets/audio/beasts/"
const LUSSEN := ["wind", "golven", "vuur", "regen", "krekels"]
const POOL_3D := 24             ## gelijktijdige 3D-klanken; een nieuwe verdringt de oudste
const POOL_2D := 8
const MAX_STEMMEN := 2          ## gelijktijdige stemlijnen (audio.md 4c)
const STEM_GAT := 0.3           ## s: een nieuwe lijn van dezelfde unit binnen deze tijd speelt niet (beasts-src KNOCK_GAP)
const BEVEL_NA_KLIK := 0.35     ## s: een nieuw bevel telt als bevel van de speler zo kort na een linkerklik
const GOLF_SPELERS := 5         ## golflussen, steeds verplaatst naar de dichtste kustpunten
const VOGELS_PER_SEIZOEN := [1.0, 0.8, 0.35, 0.0]
const KREKELS_PER_SEIZOEN := [0.35, 1.0, 0.6, 0.0]
const ZAAG_SOORTEN := [&"hut", &"gereedschapsloods", &"kippenhok", &"molen", &"melkerij", &"hek", &"poort"]
const GEEN_KLAAR := [&"hek", &"weg"]   ## geen klokje bij elk afgebouwd hek of stuk weg

var w: Wereld
var view: WereldView
var cam: Camera3D
var bestuur: Bestuur

var _streams := {}          # groep -> Array[AudioStream]
var _laatste := {}          # groep -> index van de vorige keuze (niet twee keer dezelfde)
var _pool3d: Array[AudioStreamPlayer3D] = []
var _pool2d: Array[AudioStreamPlayer] = []
var _stemmen: Array[AudioStreamPlayer3D] = []
var _stem_t := {}           # dorpeling-id -> tijd van de vorige lijn
var _luisteraar: AudioListener3D
var _lagen := {}            # laag -> {"speler": AudioStreamPlayer, "gain": float}
var _vuur: AudioStreamPlayer3D
var _golven: Array[AudioStreamPlayer3D] = []
var _kust: PackedVector3Array = []
var _golf_t := 0.0
var _tijd := 0.0
var _klik_t := -10.0
var _vorige_keus: Array = []
var _bevel_ref := {}        # dorpeling-id -> het bevel-Dictionary van de vorige frame (is_same)
var _bezig_vorig := {}      # dorpeling-id -> bezig > 0 in de vorige frame
var _draagt_vorig := {}
var _koe_t := {}            # koe-id -> s tot ze weer loeit
var _kip_t := {}
var _vogel_t := 3.0
var _uil_t := 20.0
var _klaar_t := -10.0
var _was_pauze := false
var _rng := RandomNumberGenerator.new()
var _log := false           ## --geluid-log: elke klank die start naar de uitvoer (controle zonder luidsprekers)


## Alle verwachte bestanden per groep (ook voor test/audio_test.gd).
static func catalogus() -> Dictionary:
	var c := {}
	for x in ["m", "f", "b", "g"]:
		c["select_" + x] = _reeks(BEASTS + "voice_select_%s_%%d.mp3" % x, 4)
		c["order_" + x] = _reeks(BEASTS + "voice_order_%s_%%d.mp3" % x, 4)
		c["lok_koe_" + x] = _reeks(BEASTS + "voice_cattle_%s_%%d.mp3" % x, 2)
	c["loei"] = _reeks(BEASTS + "voice_moo_%d.mp3", 2)
	c["kakel"] = _reeks(BEASTS + "voice_cluck_%d.mp3", 2)
	c["hamer"] = _reeks(BEASTS + "voice_build_%d.wav", 2)
	c["munt"] = [BEASTS + "voice_coin_0.wav"]
	c["oogst"] = [BEASTS + "voice_crop_0.wav"]
	c["melk"] = [BEASTS + "voice_milk_0.wav"]
	c["eieren"] = [BEASTS + "voice_eggs_0.wav"]
	for n in LUSSEN + ["klik", "plaats", "klaar", "poort_open", "poort_dicht", "missie_geslaagd", "missie_verloren"]:
		c[n] = [EIGEN + n + ".wav"]
	for g in [["vogel", 6], ["uil", 2], ["tok", 4], ["zaag", 2], ["houweel", 3], ["sikkel", 3]]:
		c[g[0]] = _reeks(EIGEN + g[0] + "_%d.wav", g[1])
	return c


static func _reeks(patroon: String, n: int) -> Array:
	var uit := []
	for i in n:
		uit.append(patroon % i)
	return uit


## Laadt een klank: geimporteerd via de ResourceLoader, anders rechtstreeks van schijf (nog niet geimporteerd).
## Een .ogg naast een .mp3 gaat voor (haal_beasts.ps1 maakt die met ffmpeg, genormaliseerd).
static func laad(pad: String) -> AudioStream:
	if pad.ends_with(".mp3"):
		var ogg := pad.get_basename() + ".ogg"
		if ResourceLoader.exists(ogg) or FileAccess.file_exists(ogg):
			pad = ogg
	if ResourceLoader.exists(pad):
		return load(pad) as AudioStream
	if not FileAccess.file_exists(pad):
		return null
	var echt := ProjectSettings.globalize_path(pad)
	if pad.ends_with(".wav"):
		return AudioStreamWAV.load_from_file(echt)
	if pad.ends_with(".mp3"):
		return AudioStreamMP3.load_from_file(echt)
	if pad.ends_with(".ogg"):
		return AudioStreamOggVorbis.load_from_file(echt)
	return null


## Bussen Effecten, Stemmen en Omgeving onder Master, volumes uit BUSSEN, limiter op Master.
static func zet_bussen() -> void:
	for naam in BUSSEN:
		var i := AudioServer.get_bus_index(naam)
		if i < 0:
			AudioServer.add_bus()
			i = AudioServer.bus_count - 1
			AudioServer.set_bus_name(i, naam)
			AudioServer.set_bus_send(i, "Master")
		AudioServer.set_bus_volume_db(i, BUSSEN[naam])
	if AudioServer.get_bus_effect_count(0) == 0:
		var lim := AudioEffectHardLimiter.new()
		lim.ceiling_db = -1.0
		AudioServer.add_bus_effect(0, lim)


func bouw(wereld: Wereld, v: WereldView, camera: Camera3D, b: Bestuur) -> void:
	name = "Geluid"
	if Engine.get_write_movie_path() != "":
		# frames voor verificatie: stil. De movie writer mixt na de laatste frame niet meer, dus spelende streams
		# lieten hun playback liggen (lek-melding bij afsluiten). Headless draait het geluid wel (dummy-driver).
		return
	w = wereld
	view = v
	cam = camera
	bestuur = b
	_rng.seed = 1996
	_log = "--geluid-log" in OS.get_cmdline_user_args()
	zet_bussen()
	var cat := catalogus()
	var mist := 0
	for groep in cat:
		var lijst: Array[AudioStream] = []
		for pad in cat[groep]:
			var s := laad(pad)
			if s != null:
				lijst.append(s)
			else:
				mist += 1
		_streams[groep] = lijst
	if mist > 0:
		print("[geluid] ", mist, " klanken ontbreken (draai sync.ps1 voor assets/audio/beasts, audio/maak_geluid.py voor audio/eigen)")
	for groep in LUSSEN:
		for s in _streams[groep]:
			_maak_lus(s)

	_luisteraar = AudioListener3D.new()
	add_child(_luisteraar)
	_luisteraar.make_current()
	for i in POOL_3D:
		var p := AudioStreamPlayer3D.new()
		p.attenuation_model = AudioStreamPlayer3D.ATTENUATION_INVERSE_DISTANCE
		p.panning_strength = 0.6
		p.attenuation_filter_cutoff_hz = 5000.0
		p.set_meta("t", -1.0)
		add_child(p)
		_pool3d.append(p)
	for i in POOL_2D:
		var p := AudioStreamPlayer.new()
		p.set_meta("t", -1.0)
		add_child(p)
		_pool2d.append(p)

	for laag in ["wind", "regen", "krekels"]:
		var sp := AudioStreamPlayer.new()
		sp.bus = "Omgeving"
		sp.stream = _eerste(laag)
		add_child(sp)
		_lagen[laag] = {"speler": sp, "gain": 0.0}
	_maak_vuur()
	_maak_kust()

	w.plan_gezet.connect(_bij_plan_gezet)
	w.plan_klaar.connect(_bij_plan_klaar)
	w.koe_geclaimd.connect(_bij_koe_geclaimd)
	w.missie_einde.connect(_bij_missie_einde)
	w.poort_gewisseld.connect(_bij_poort)
	w.verkocht.connect(func(m: Plan, _waar: String, _prijs: int) -> void: speel3d("munt", _deur(m), -3.0, 6.0, 45.0, 0.04))
	w.geleverd.connect(func(m: Plan, _brengt: String) -> void: speel3d("plaats", _deur(m), -12.0, 4.0, 30.0))
	w.voorwerp_opgeraapt.connect(func(ob: Dictionary, _d: Dorpeling) -> void: speel3d("plaats", _tegel3d(ob), -8.0, 4.0, 30.0))
	w.voorwerp_afgeleverd.connect(func(ob: Dictionary, _d: Dorpeling, _k: int) -> void:
		for i in 3:          # beker aan de vlag: een handvol munten
			speel3d("munt", _tegel3d(ob), -1.0, 6.0, 60.0, 0.06))
	get_tree().node_added.connect(_bij_node)
	_zoek_knoppen(get_tree().root)
	_klaar_t = 1.0            # wat plaats_voorgebouwd bij de start zet, klinkt niet


## Bij afsluiten alles stoppen: een spelende stream hield anders zijn playback vast (lek bij --write-movie).
func _exit_tree() -> void:
	for c in get_children():
		if c is AudioStreamPlayer or c is AudioStreamPlayer3D:
			c.stop()
			c.stream = null
	_streams.clear()


func _eerste(groep: String) -> AudioStream:
	var l: Array = _streams.get(groep, [])
	return l[0] if not l.is_empty() else null


func _maak_lus(s: AudioStream) -> void:
	if s is AudioStreamWAV:
		var wav := s as AudioStreamWAV
		wav.loop_mode = AudioStreamWAV.LOOP_FORWARD
		wav.loop_begin = 0
		wav.loop_end = int(round(wav.get_length() * wav.mix_rate))
	elif s is AudioStreamMP3:
		(s as AudioStreamMP3).loop = true
	elif s is AudioStreamOggVorbis:
		(s as AudioStreamOggVorbis).loop = true


func _kies(groep: String) -> AudioStream:
	var l: Array = _streams.get(groep, [])
	if l.is_empty():
		return null
	var i := _rng.randi() % l.size()
	if l.size() > 1 and i == _laatste.get(groep, -1):
		i = (i + 1 + _rng.randi() % (l.size() - 1)) % l.size()
	_laatste[groep] = i
	return l[i]


## 3D-klank op `pos`. Buiten `maxd` van de luisteraar start hij niet eens. `toon` = willekeur in toonhoogte.
func speel3d(groep: String, pos: Vector3, db := 0.0, unit := 5.0, maxd := 35.0, toon := 0.08,
		bus := "Effecten", pitch := 1.0) -> AudioStreamPlayer3D:
	if _luisteraar == null or _luisteraar.global_position.distance_to(pos) > maxd:
		return null
	var s := _kies(groep)
	if s == null:
		return null
	var p: AudioStreamPlayer3D = null
	for q in _pool3d:
		if not q.playing and not q.stream_paused:
			p = q
			break
		if p == null or float(q.get_meta("t")) < float(p.get_meta("t")):
			p = q
	p.stop()
	p.stream_paused = false
	p.stream = s
	p.bus = bus
	p.volume_db = db + (_zoom_db() if bus == "Effecten" else 0.0)
	p.unit_size = unit
	p.max_distance = maxd
	p.pitch_scale = pitch * _rng.randf_range(1.0 - toon, 1.0 + toon)
	p.global_position = pos
	p.set_meta("t", _tijd)
	p.play()
	if _log:
		print("[geluid] %.1f %s (%s, %.0f m)" % [_tijd, groep, bus, _luisteraar.global_position.distance_to(pos)])
	return p


## 2D-klank (interface en meldingen), bus Effecten.
func speel2d(groep: String, db := 0.0, toon := 0.0) -> void:
	var s := _kies(groep)
	if s == null:
		return
	var p: AudioStreamPlayer = _pool2d[0]
	for q in _pool2d:
		if not q.playing:
			p = q
			break
		if float(q.get_meta("t")) < float(p.get_meta("t")):
			p = q
	p.stop()
	p.stream = s
	p.bus = "Effecten"
	p.volume_db = db
	p.pitch_scale = _rng.randf_range(1.0 - toon, 1.0 + toon)
	p.set_meta("t", _tijd)
	p.play()
	if _log:
		print("[geluid] %.1f %s (2d)" % [_tijd, groep])


## Uitgezoomd klinkt werk zachter: -3 dB per 10 m camera-afstand boven 20 m (audio.md 4b), hoogstens -15.
func _zoom_db() -> float:
	var a := float(cam.get("afstand")) if cam != null else 20.0
	return clampf(-0.3 * (a - 20.0), -15.0, 0.0)


# ---------------------------------------------------------------- stemmen

func _stem_letter(d: Dorpeling) -> String:
	if d.leeftijd == "kind":
		return "g" if d.geslacht == "vrouw" else "b"
	return "f" if d.geslacht == "vrouw" else "m"


## Een stemlijn van dorpeling `d`: groep "select", "order" of "lok_koe". Hoogstens MAX_STEMMEN tegelijk.
func spreek(d: Dorpeling, soort: String) -> void:
	if d == null or not view.units.has(d.id):
		return
	if _tijd - float(_stem_t.get(d.id, -10.0)) < STEM_GAT:
		return
	_stem_t[d.id] = _tijd
	var levend: Array[AudioStreamPlayer3D] = []
	for p in _stemmen:
		if p.playing and p.bus == "Stemmen":
			levend.append(p)
	_stemmen = levend
	while _stemmen.size() >= MAX_STEMMEN:
		_stemmen.pop_front().stop()
	var pitch := 0.9 if d.leeftijd == "oud" else 1.0     # ouderen: m/f iets lager (audio.md 4c, noodoplossing)
	var p := speel3d(soort + "_" + _stem_letter(d), view.unit_pos(d.id) + Vector3(0, 1.4, 0), 0.0, 12.0, 120.0, 0.03,
			"Stemmen", pitch)
	if p != null:
		_stemmen.append(p)


func _werk_selectie() -> void:
	var keus: Array = bestuur.gekozen if bestuur != null else view.gekozen
	if keus == _vorige_keus:
		return
	var nieuw: Array = []
	for id in keus:
		if not id in _vorige_keus:
			nieuw.append(id)
	_vorige_keus = keus.duplicate()
	if nieuw.is_empty():
		return
	spreek(_leider(nieuw), "select")     # groep: alleen de leider spreekt (audio.md 4c)


## De dorpeling uit `ids` die het dichtst bij het camerabrandpunt staat.
func _leider(ids: Array) -> Dorpeling:
	var beste: Dorpeling = null
	var bd := INF
	for id in ids:
		var d := w.dorpeling(id)
		if d == null or not view.units.has(id):
			continue
		var af := view.unit_pos(id).distance_squared_to(_luisteraar.global_position)
		if af < bd:
			bd = af
			beste = d
	return beste


func _input(e: InputEvent) -> void:
	if e is InputEventMouseButton and e.button_index == MOUSE_BUTTON_LEFT and not e.pressed:
		_klik_t = _tijd


# ---------------------------------------------------------------- per frame

func _process(dt: float) -> void:
	if w == null:
		return
	_tijd += dt
	if cam != null:
		var f: Vector3 = cam.get("focus")
		_luisteraar.global_position = f + Vector3(0, 1.5, 0)
		_luisteraar.global_rotation = Vector3(0, cam.global_rotation.y, 0)
	_werk_pauze()
	_werk_selectie()
	_werk_dorpelingen()
	_werk_dieren(dt)
	_werk_lagen(dt)
	_werk_eenmalig(dt)
	_golf_t -= dt
	if _golf_t <= 0.0:
		_golf_t = 0.5
		_werk_golven()


## Pauze: geen werkgeluid. Alles op de bus Effecten (en stemmen) staat stil tot het spel weer loopt.
func _werk_pauze() -> void:
	if w.gepauzeerd == _was_pauze:
		return
	_was_pauze = w.gepauzeerd
	for p in _pool3d:
		if p.bus != "Omgeving" and (p.playing or p.stream_paused):
			p.stream_paused = _was_pauze


func _werk_dorpelingen() -> void:
	var na_klik := _tijd - _klik_t < BEVEL_NA_KLIK
	var bevel_van: Array = []
	for d in w.dorpelingen:
		var id := d.id
		if not view.units.has(id):
			continue
		var b: Bumpkin = view.units[id]["bump"]
		if not b.has_meta("geluid"):        # ook na volwassen_geworden (nieuwe Bumpkin)
			b.set_meta("geluid", true)
			b.impact.connect(_bij_impact.bind(id))
		# bevel van de speler: nieuw bevel bij een gekozen dorpeling, vlak na een linkerklik
		var ref = _bevel_ref.get(id)
		if not is_same(ref, d.bevel):
			_bevel_ref[id] = d.bevel
			if na_klik and not d.bevel.is_empty() and id in _vorige_keus \
					and d.bevel.get("soort", "") in ["loop", "werk", "claim", "gilde", "vecht"]:
				bevel_van.append(id)
		if w.gepauzeerd:
			continue
		var bezig := d.bezig > 0.0
		if bezig and not _bezig_vorig.get(id, false):
			var pos := view.unit_pos(id) + Vector3(0, 0.6, 0)
			if d.melk_koe != null:
				speel3d("melk", pos, -2.0, 5.0, 35.0)
			elif d.raap_kip != null:
				speel3d("eieren", pos, -2.0, 5.0, 35.0)
				speel3d("tok", pos, -6.0, 3.0, 25.0, 0.1)
			elif d.klus_tegel.x >= 0:
				speel3d("sikkel", pos, -3.0, 5.0, 35.0)
		_bezig_vorig[id] = bezig
		if d.draagt != _draagt_vorig.get(id, ""):
			if d.draagt == "graan":
				speel3d("oogst", view.unit_pos(id) + Vector3(0, 0.6, 0), -2.0, 5.0, 35.0)
			_draagt_vorig[id] = d.draagt
	if not bevel_van.is_empty():
		spreek(_leider(bevel_van), "order")


## Hamerklap op de bouwimpact (Bumpkin.impact); soms een zaag (hout), een houweel bij de akker.
## Zagen (de zaagclip van de bouwer, impact = einde van de duwslag) geeft altijd de zaag.
func _bij_impact(welke: StringName, id: int) -> void:
	if (welke != &"bouwen" and welke != &"zagen") or w.gepauzeerd:
		return
	var d := w.dorpeling(id)
	if d == null or not view.units.has(id):
		return
	var pos := view.unit_pos(id) + Vector3(0, 0.8, 0)
	var soort: StringName = d.werk_plan.soort if d.werk_plan != null else &""
	if welke == &"zagen":
		speel3d("zaag", pos, -4.0, 5.0, 35.0, 0.05)
	elif soort == &"akker":
		speel3d("houweel", pos, -2.0, 5.0, 35.0)
	elif soort in ZAAG_SOORTEN and _rng.randf() < 0.2:
		speel3d("zaag", pos, -4.0, 5.0, 35.0, 0.05)
	else:
		speel3d("hamer", pos, -2.0, 5.0, 35.0, 0.1)


func _werk_dieren(dt: float) -> void:
	if w.gepauzeerd:
		return
	var stap := dt * w.tempo
	for k in w.vee:
		var t: float = _koe_t.get(k.id, _rng.randf_range(8.0, 40.0)) - stap
		if t <= 0.0:
			t = _rng.randf_range(35.0, 90.0)
			var p := view.koe_pos(k.id)
			if p != Vector3.INF:
				speel3d("loei", p + Vector3(0, 1.2, 0), -5.0, 6.0, 45.0, 0.12)
		_koe_t[k.id] = t
	for k in w.kippen:
		var t: float = _kip_t.get(k.id, _rng.randf_range(2.0, 12.0)) - stap
		if t <= 0.0:
			t = _rng.randf_range(10.0, 30.0)
			if view.kippen.has(k.id):
				var p: Vector3 = (view.kippen[k.id] as Node3D).global_position + Vector3(0, 0.3, 0)
				if _rng.randf() < 0.12:
					speel3d("kakel", p, -9.0, 3.0, 25.0, 0.08)
				else:
					speel3d("tok", p, -6.0, 3.0, 25.0, 0.12)
		_kip_t[k.id] = t


# ---------------------------------------------------------------- omgeving

## Wind altijd (harder in herfst/winter, bij regen en uitgezoomd), regen als het regent, krekels 's nachts.
## Fades lineair in versterking, ongeveer 4 s (audio.md 4d).
func _werk_lagen(dt: float) -> void:
	var sz := w.seizoen()
	var regen := w.regent()
	var nacht := w.is_nacht()
	var a := float(cam.get("afstand")) if cam != null else 20.0
	var wind := 0.35 + (0.25 if sz >= 2 else 0.0) + (0.2 if regen else 0.0) + clampf((a - 20.0) / 150.0, 0.0, 0.4)
	var doel := {"wind": wind, "regen": 0.8 if regen else 0.0,
			"krekels": KREKELS_PER_SEIZOEN[sz] * 0.7 if nacht and not regen else 0.0}
	for laag in _lagen:
		var l: Dictionary = _lagen[laag]
		var sp: AudioStreamPlayer = l["speler"]
		if sp.stream == null:
			continue
		l["gain"] = move_toward(l["gain"], doel[laag], dt * 0.25)
		if l["gain"] <= 0.001:
			if sp.playing:
				sp.stop()
			continue
		sp.volume_db = linear_to_db(l["gain"])
		if laag == "wind":
			sp.pitch_scale = 1.12 if sz == 3 else 1.0       # winter: kouder, hoger
		if not sp.playing:
			sp.play(_rng.randf_range(0.0, sp.stream.get_length()))
			if _log:
				print("[geluid] %.1f laag %s aan" % [_tijd, laag])


## Vogels overdag (per seizoen minder, 's winters geen), een uil 's nachts; niet als het regent.
func _werk_eenmalig(dt: float) -> void:
	var regen := w.regent()
	var dicht: float = VOGELS_PER_SEIZOEN[w.seizoen()]
	_vogel_t -= dt
	if _vogel_t <= 0.0:
		_vogel_t = _rng.randf_range(1.5, 6.0) / maxf(dicht, 0.2)
		if not w.is_nacht() and not regen and dicht > 0.0:
			speel3d("vogel", _rond_luisteraar(10.0, 25.0, 5.0), -8.0, 8.0, 60.0, 0.12, "Omgeving")
	_uil_t -= dt
	if _uil_t <= 0.0:
		_uil_t = _rng.randf_range(20.0, 60.0)
		if w.is_nacht() and not regen:
			speel3d("uil", _rond_luisteraar(20.0, 35.0, 6.0), -6.0, 10.0, 80.0, 0.04, "Omgeving")


func _rond_luisteraar(van: float, tot: float, hoogte: float) -> Vector3:
	var hoek := _rng.randf() * TAU
	var r := _rng.randf_range(van, tot)
	return _luisteraar.global_position + Vector3(cos(hoek) * r, hoogte, sin(hoek) * r)


func _maak_vuur() -> void:
	var n: Node3D = view.terrein.kampvuur_node if view.terrein != null else null
	var s := _eerste("vuur")
	if n == null or s == null:
		return
	_vuur = AudioStreamPlayer3D.new()
	_vuur.name = "Kampvuur"
	_vuur.stream = s
	_vuur.bus = "Omgeving"
	_vuur.unit_size = 4.0
	_vuur.max_distance = 30.0
	_vuur.attenuation_model = AudioStreamPlayer3D.ATTENUATION_LOGARITHMIC
	_vuur.panning_strength = 0.6
	_vuur.volume_db = 2.0
	add_child(_vuur)          # eigen kind, niet onder het kampvuur: dat lekte bij het afsluiten
	_vuur.global_position = n.global_position + Vector3(0, 0.4, 0)
	_vuur.play()


## Kustpunten: zee-tegels met een landbuur, uitgedund tot een per 6x6 tegels.
func _maak_kust() -> void:
	var s := _eerste("golven")
	if s == null:
		return
	var r := w.raster
	var gezien := {}
	for y in r.rijen:
		for x in r.kolommen:
			if not _zee(r.soort_naam(x, y)):
				continue
			var land := false
			for k in 4:
				var n := r.soort_naam(x + Raster.DC[k], y + Raster.DR[k])
				if not _zee(n):
					land = true
			var vak := Vector2i(x / 6, y / 6)
			if land and not gezien.has(vak):
				gezien[vak] = true
				_kust.append(Vector3((x + 0.5) * w.tegel_m, 0.3, (y + 0.5) * w.tegel_m))
	for i in mini(GOLF_SPELERS, _kust.size()):
		var p := AudioStreamPlayer3D.new()
		p.name = "Golven_%d" % i
		p.stream = s
		p.bus = "Omgeving"
		p.unit_size = 10.0
		p.max_distance = 60.0
		p.attenuation_model = AudioStreamPlayer3D.ATTENUATION_LOGARITHMIC
		p.panning_strength = 0.6
		p.volume_db = -3.0
		p.pitch_scale = 0.9 + 0.05 * i
		add_child(p)
		_golven.append(p)


static func _zee(naam: String) -> bool:
	return naam == "water" or naam == "leeg"


func _werk_golven() -> void:
	if _golven.is_empty():
		return
	var l := _luisteraar.global_position
	var dichtst: Array = []
	for k in _kust:
		dichtst.append([Vector2(k.x - l.x, k.z - l.z).length_squared(), k])
	dichtst.sort_custom(func(a, b) -> bool: return a[0] < b[0])
	var ijs := w.sneeuw() > 0.5        # bevroren zee in de winter: stiller
	for i in _golven.size():
		var p := _golven[i]
		if i >= dichtst.size():
			break
		p.global_position = dichtst[i][1]
		p.volume_db = -12.0 if ijs else -3.0
		if not p.playing:
			p.play(_rng.randf_range(0.0, p.stream.get_length()))


# ---------------------------------------------------------------- sim-signalen en interface

func _tegel3d(ob: Dictionary) -> Vector3:
	return view.terrein.tegel_midden(Vector2i(ob["x"], ob["y"]))


func _midden(p: Plan) -> Vector3:
	var r := p.afdruk()
	var x := (r.position.x + r.size.x * 0.5) * w.tegel_m
	var z := (r.position.y + r.size.y * 0.5) * w.tegel_m
	return Vector3(x, view.terrein.hoogte_op(x, z) + 1.0, z)


func _deur(p: Plan) -> Vector3:
	var d := p.deur_punt(w.tegel_m)
	return Vector3(d.x, view.terrein.hoogte_op(d.x, d.y) + 1.0, d.y)


func _bij_plan_gezet(_p: Plan) -> void:
	if _tijd >= _klaar_t:
		speel2d("plaats", -6.0, 0.05)


func _bij_plan_klaar(p: Plan) -> void:
	if _tijd < _klaar_t:
		return
	if p.soort in GEEN_KLAAR:
		speel3d("plaats", _midden(p), -6.0, 5.0, 40.0, 0.1)
		return
	speel2d("klaar", -4.0)
	_klaar_t = _tijd + 1.5


func _bij_koe_geclaimd(k: Vee) -> void:
	var p := view.koe_pos(k.id)
	if p == Vector3.INF:
		return
	speel3d("loei", p + Vector3(0, 1.2, 0), -3.0, 6.0, 45.0, 0.1)
	if k.eigenaar != 0:
		return
	var beste: Dorpeling = null              # lokroep van wie het dichtst bij de koe staat
	var bd := INF
	for d in w.dorpelingen:
		if d.volwassen() and not d.binnen:
			var af := d.pos.distance_squared_to(k.pos)
			if af < bd:
				bd = af
				beste = d
	if beste != null:
		_stem_t.erase(beste.id)
		spreek(beste, "lok_koe")


func _bij_poort(p: Plan) -> void:
	speel3d("poort_open" if p.open else "poort_dicht", _midden(p), -2.0, 5.0, 40.0, 0.06)


func _bij_missie_einde(uitslag: String) -> void:
	speel2d("missie_geslaagd" if uitslag == "gewonnen" else "missie_verloren", 0.0)


func _bij_node(n: Node) -> void:
	if n is BaseButton:
		_koppel_knop(n)


func _zoek_knoppen(n: Node) -> void:
	if n is BaseButton:
		_koppel_knop(n)
	for c in n.get_children():
		_zoek_knoppen(c)


func _koppel_knop(k: BaseButton) -> void:
	if not k.pressed.is_connected(_bij_knop):
		k.pressed.connect(_bij_knop)


func _bij_knop() -> void:
	speel2d("klik", -4.0, 0.04)
