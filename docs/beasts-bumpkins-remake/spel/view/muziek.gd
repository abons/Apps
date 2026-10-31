class_name Muziek
extends Node
## Muziek (2026-10-31, audio.md sectie 7): een eigen Node onder de root, niet in de hoofdscène, zodat hij het herladen van
## main.tscn (start- en pauzemenu laden de scène opnieuw) overleeft en tussen menu en missie kan overvloeien.
## Aanhaken: `Muziek.van(get_tree()).zet(&"menu")`; in een missie `Muziek.van(get_tree()).volg(hud, w)`.
##
## Origineel (openbumpkins-decompilatie, audio.md 7): zeven cd-audiotracks (2 tot 8, James Hannigan) via MCI `cdaudio`.
## De exe speelt er maar twee: **track 2** in het hoofdmenu (en de outro), **track 3** zolang de missiebriefing open
## staat. In de missie zelf **geen muziek**, bij winst of verlies een stemfragment en geen muziek. Elke track speelde
## een keer (de exe stopte hem na een vaste duur, 67 en 109 s) en lus niet; er was geen volume-instelling in het spel.
## Wij: menu en briefing lussen (je blijft er langer dan 67 s), met overvloeien, een volume en dempen (M overal, sinds
## 2026-10-31; de molen kreeg Z; knop in het pauzemenu), bewaard in user://. Afwijking van het origineel (besluit
## gebruiker 2026-10-31): in de missie een zachte afspeellijst van tracks 4..8, na elke track een pauze (LIJST_PAUZE_S),
## op MISSIE_GAIN van het volume.
##
## Bestanden: assets/audio/muziek/track02.ogg .. track08.ogg (niet in git: `assets/` staat in .gitignore), gemaakt door
## audio/haal_muziek.ps1 uit je eigen cd-rip. Ontbreekt een track, dan blijft die context stil (een melding).

signal gewijzigd                     ## volume of dempen veranderd (pauzemenu werkt zijn knop bij)

const MAP := "res://assets/audio/muziek/"
const BUS := "Muziek"
const FADE := 1.5                    ## s overvloeien
const STIL_DB := -60.0
const VOLUME_STANDAARD := 0.7
const LIJST_PAUZE_S := 30.0          ## s stilte tussen twee tracks van een afspeellijst (missie)
const MISSIE_GAIN := 0.45            ## missiemuziek zachter dan het menu (lineair, bovenop het volume)
## Per context: cd-track (0 = stilte) en of hij lust, of een afspeellijst `tracks` (elk een keer, dan pauze, dan de
## volgende, rond en rond) met `gain` (lineair, 1 = vol). Menu en briefing zoals het origineel; zie de kop.
const CONTEXTEN := {
	&"menu": {"track": 2, "lus": true},
	&"briefing": {"track": 3, "lus": true},
	&"missie": {"tracks": [4, 5, 6, 7, 8], "lus": false, "gain": MISSIE_GAIN},
	&"gewonnen": {"track": 0, "lus": false},
	&"verloren": {"track": 0, "lus": false},
	&"stil": {"track": 0, "lus": false},
}

## Instellingen (volume, dempen); "" = niet lezen of schrijven (tests en scenario's).
static var cfg_pad := "" if Scherm.optie("scenario") != "" else "user://muziek.cfg"
static var _ik: Muziek

var context: StringName = &""
var volume := VOLUME_STANDAARD       ## 0..1, lineair; de bus krijgt linear_to_db
var stil := false
var streams := {}                    ## track -> AudioStream; tests vullen dit, anders van schijf (cache)
var _gemist := {}                    ## track -> true: al gemeld dat het bestand ontbreekt
var _spelers: Array[AudioStreamPlayer] = []
var _actief := 0
var _tweens := {}                    ## speler -> Tween van zijn lopende fade
var _uit := false                    ## --write-movie: stil (zie geluid.gd, lek bij afsluiten)
var lijst_pauze_s := LIJST_PAUZE_S   ## tests zetten hem korter
var _lijst_i := 0                    ## volgende track uit de afspeellijst (blijft over missies heen, de node blijft bestaan)
var _wacht_s := -1.0                 ## >= 0: pauze tot de volgende track van de afspeellijst


## De ene muziekspeler: bestaat hij nog niet, dan komt hij onder de root (uitgesteld: de root kan bezig zijn).
static func van(tree: SceneTree) -> Muziek:
	if is_instance_valid(_ik) and not _ik.is_queued_for_deletion():
		return _ik
	_ik = Muziek.new()
	_ik.name = "Muziek"
	tree.root.add_child.call_deferred(_ik)
	return _ik


static func pad(track: int) -> String:
	return MAP + "track%02d.ogg" % track


func _init() -> void:
	process_mode = Node.PROCESS_MODE_ALWAYS
	_uit = Engine.get_write_movie_path() != ""
	for i in 2:
		var p := AudioStreamPlayer.new()
		p.bus = BUS
		p.volume_db = STIL_DB
		add_child(p)
		p.finished.connect(_track_af.bind(p))
		_spelers.append(p)
	lees()


func _ready() -> void:
	zorg_bus()
	_pas_bus()
	if context != &"":
		_speel()


func _exit_tree() -> void:
	for p in _spelers:
		p.stop()
		p.stream = null
	if _ik == self:
		_ik = null


## Bus Muziek onder Master (geluid.gd maakt de andere; het startmenu bouwt geen Geluid, dus hier zelf).
static func zorg_bus() -> int:
	var i := AudioServer.get_bus_index(BUS)
	if i < 0:
		AudioServer.add_bus()
		i = AudioServer.bus_count - 1
		AudioServer.set_bus_name(i, BUS)
		AudioServer.set_bus_send(i, "Master")
	return i


func _pas_bus() -> void:
	var i := zorg_bus()
	AudioServer.set_bus_volume_db(i, linear_to_db(maxf(volume, 0.0001)))
	AudioServer.set_bus_mute(i, stil or volume <= 0.001)


# ---------------------------------------------------------------- context

## Wisselt naar `ctx` (zie CONTEXTEN). Zelfde track = doorspelen, anders overvloeien in FADE s.
func zet(ctx: StringName) -> void:
	if not CONTEXTEN.has(ctx):
		push_warning("muziek: onbekende context %s" % ctx)
		return
	if ctx == context:
		return
	context = ctx
	if is_inside_tree():
		_speel()


## In een missie: de briefing-track zolang de briefing open is, daarna de missie; bij het einde gewonnen/verloren.
## Verbindt met methoden, niet met lambda's die `w` vangen (zie Hints: dat lekte de Wereld).
func volg(hud: Hud, w: Wereld) -> void:
	if hud != null and hud.brief != null and hud.brief.visible:
		zet(&"briefing")
		hud.brief.gesloten.connect(_bij_brief_dicht, CONNECT_ONE_SHOT)
	else:
		zet(&"missie")
	if w != null and not w.missie_einde.is_connected(_bij_einde):
		w.missie_einde.connect(_bij_einde)


func _bij_brief_dicht() -> void:
	if context == &"briefing":
		zet(&"missie")


func _bij_einde(uitslag: String) -> void:
	zet(&"gewonnen" if uitslag == "gewonnen" else &"verloren")


## De speler die nu klinkt (of het laatst klonk).
func speler() -> AudioStreamPlayer:
	return _spelers[_actief]


func _speel() -> void:
	if _uit:
		return
	var c: Dictionary = CONTEXTEN[context]
	_wacht_s = -1.0
	var s := stream_voor(_kies_track(c))
	var nu := _spelers[_actief]
	if s != null and nu.stream == s and nu.playing:
		zet_lus(s, bool(c["lus"]))
		return                                   # zelfde track: doorspelen
	if nu.playing:
		_fade(nu, 0.0, true)
	if s == null:
		return
	zet_lus(s, bool(c["lus"]))
	_actief = 1 - _actief
	var p := _spelers[_actief]
	_stop_tween(p)
	p.stop()
	p.stream = s
	p.volume_db = STIL_DB
	p.play()
	_fade(p, float(c.get("gain", 1.0)), false)


## De track voor context `c`: `track`, of de volgende uit de afspeellijst `tracks` die er is (0 = geen).
func _kies_track(c: Dictionary) -> int:
	if not c.has("tracks"):
		return int(c.get("track", 0))
	var lijst: Array = c["tracks"]
	for i in lijst.size():
		var n := int(lijst[(_lijst_i + i) % lijst.size()])
		if stream_voor(n) != null:
			_lijst_i = (_lijst_i + i + 1) % lijst.size()
			return n
	return 0


## Een track is uit (alleen zonder lus): in een afspeellijst begint de pauze naar de volgende.
func _track_af(p: AudioStreamPlayer) -> void:
	if p == speler() and CONTEXTEN.get(context, {}).has("tracks"):
		_wacht_s = lijst_pauze_s


func _process(dt: float) -> void:
	if _wacht_s < 0.0:
		return
	_wacht_s -= dt
	if _wacht_s < 0.0 and CONTEXTEN.get(context, {}).has("tracks"):
		_speel()


func _fade(p: AudioStreamPlayer, doel: float, stop_na: bool) -> void:
	_stop_tween(p)
	var t := create_tween()
	t.tween_method(func(g: float) -> void: p.volume_db = linear_to_db(maxf(g, 0.001)),
			db_to_linear(p.volume_db), doel, FADE)
	if stop_na:
		t.tween_callback(p.stop)
	_tweens[p] = t


func _stop_tween(p: AudioStreamPlayer) -> void:
	var oud: Tween = _tweens.get(p)
	if oud != null and oud.is_valid():
		oud.kill()


## Track `n` (2..8) of null: uit `streams` (tests, cache), anders van schijf via Geluid.laad.
func stream_voor(n: int) -> AudioStream:
	if n <= 0:
		return null
	if streams.has(n):
		return streams[n]
	var s: AudioStream = preload("res://view/geluid.gd").laad(pad(n))
	if s == null:
		if not _gemist.has(n):
			_gemist[n] = true
			print("[muziek] %s ontbreekt (eigen cd-rip: audio/haal_muziek.ps1), stil" % pad(n))
		return null
	streams[n] = s
	return s


static func zet_lus(s: AudioStream, aan: bool) -> void:
	if s is AudioStreamOggVorbis:
		(s as AudioStreamOggVorbis).loop = aan
	elif s is AudioStreamMP3:
		(s as AudioStreamMP3).loop = aan
	elif s is AudioStreamWAV:
		var wav := s as AudioStreamWAV
		wav.loop_mode = AudioStreamWAV.LOOP_FORWARD if aan else AudioStreamWAV.LOOP_DISABLED
		wav.loop_begin = 0
		wav.loop_end = int(round(wav.get_length() * wav.mix_rate)) if aan else 0


# ---------------------------------------------------------------- volume, dempen, bewaren

func zet_volume(v: float) -> void:
	v = clampf(v, 0.0, 1.0)
	if is_equal_approx(v, volume):
		return
	volume = v
	_pas_bus()
	bewaar()
	gewijzigd.emit()


func zet_stil(s: bool) -> void:
	if s == stil:
		return
	stil = s
	_pas_bus()
	bewaar()
	gewijzigd.emit()


func wissel_stil() -> void:
	zet_stil(not stil)


## Leest volume en dempen; ontbreekt het bestand of is een waarde onzin, dan de standaard.
func lees() -> void:
	if cfg_pad == "":
		return
	var cf := ConfigFile.new()
	if cf.load(cfg_pad) != OK:
		return
	var v: Variant = cf.get_value("muziek", "volume", VOLUME_STANDAARD)
	var s: Variant = cf.get_value("muziek", "stil", false)
	volume = clampf(float(v), 0.0, 1.0) if (v is float or v is int) else VOLUME_STANDAARD
	stil = s if s is bool else false


func bewaar() -> void:
	if cfg_pad == "":
		return
	var cf := ConfigFile.new()
	cf.set_value("muziek", "volume", volume)
	cf.set_value("muziek", "stil", stil)
	var fout := cf.save(cfg_pad)
	if fout != OK:
		push_warning("muziek: %s niet bewaard (%s)" % [cfg_pad, error_string(fout)])


# ---------------------------------------------------------------- toetsen

## M dempt overal, met of zonder Shift (besluit gebruiker 2026-10-31; de molen kreeg Z in Bouwmenu.GEBOUWEN).
func _input(e: InputEvent) -> void:
	if e is InputEventKey and e.pressed and not e.echo and (e as InputEventKey).keycode == KEY_M:
		wissel_stil()
		get_viewport().set_input_as_handled()
