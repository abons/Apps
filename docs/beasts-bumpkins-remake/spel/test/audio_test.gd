extends SceneTree
## Headless: laden alle verwachte klanken (view/geluid.gd catalogus) en staan de bussen?
## audio/eigen/ moet compleet zijn (in git). assets/audio/beasts/ (uit beasts-src, sync.ps1) alleen als de map er is.
## Daarna de muziekspeler (view/muziek.gd) met twee gemaakte stille tracks: context menu -> briefing (overvloeien, oude
## stopt) -> missie (stil), zelfde context = doorspelen, einde, dempen (M/Shift+M), volume, bewaren en teruglezen.
##   "$G" --headless --path . --script res://test/audio_test.gd

const Geluid := preload("res://view/geluid.gd")
const CFG := "user://muziek_test.cfg"

var fout := 0


func _initialize() -> void:
	_klanken()
	process_frame.connect(_muziek, CONNECT_ONE_SHOT)


func _check(ok: bool, wat: String) -> void:
	if not ok:
		print("FOUT  ", wat)
		fout += 1


func _klanken() -> void:
	var ok := 0
	var beasts_er := DirAccess.dir_exists_absolute(Geluid.BEASTS)
	if not beasts_er:
		print("LET OP  assets/audio/beasts/ ontbreekt: draai sync.ps1 (stemmen, koe, hamer, munt blijven stil)")
	var cat: Dictionary = Geluid.catalogus()
	for groep in cat:
		for pad in cat[groep]:
			if pad.begins_with(Geluid.BEASTS) and not beasts_er:
				continue
			var s: AudioStream = Geluid.laad(pad)
			if s == null or s.get_length() <= 0.0:
				_check(false, "laadt niet: " + pad)
			else:
				ok += 1
	for lus in Geluid.LUSSEN:
		var s: AudioStream = Geluid.laad(Geluid.EIGEN + lus + ".wav")
		_check(s == null or s.get_length() >= 3.0, "lus te kort: " + lus)
	Geluid.zet_bussen()
	for bus in Geluid.BUSSEN:
		_check(AudioServer.get_bus_index(bus) >= 0, "bus ontbreekt: " + bus)
	print("audio: %d klanken geladen" % ok)


## Een stille wav van `s` seconden (de echte tracks staan niet in git).
func _stil(s: float) -> AudioStreamWAV:
	var w := AudioStreamWAV.new()
	w.format = AudioStreamWAV.FORMAT_16_BITS
	w.mix_rate = 22050
	var d := PackedByteArray()
	d.resize(int(s * 22050) * 2)
	w.data = d
	return w


func _wacht(s: float) -> void:
	await create_timer(s).timeout


func _muziek() -> void:
	DirAccess.remove_absolute(ProjectSettings.globalize_path(CFG))
	Muziek.cfg_pad = CFG
	var m := Muziek.van(self)
	_check(Muziek.van(self) == m, "Muziek.van geeft steeds dezelfde speler")
	await process_frame
	_check(m.is_inside_tree() and m.get_parent() == root, "muziekspeler onder de root (overleeft het herladen van de scène)")
	_check(AudioServer.get_bus_index(Muziek.BUS) >= 0, "bus Muziek bestaat")
	_check(not m.stil and is_equal_approx(m.volume, Muziek.VOLUME_STANDAARD), "zonder cfg: standaard volume, niet gedempt")
	var t2 := _stil(4.0)
	var t3 := _stil(4.0)
	m.streams = {2: t2, 3: t3}

	m.zet(&"menu")
	var p1 := m.speler()
	_check(p1.playing and p1.stream == t2, "menu: track 2 speelt")
	_check(t2.loop_mode == AudioStreamWAV.LOOP_FORWARD, "menu: track lust")
	m.zet(&"menu")
	_check(m.speler() == p1 and p1.playing, "zelfde context: doorspelen, niet opnieuw")
	await _wacht(Muziek.FADE + 0.3)
	_check(p1.volume_db > -1.0, "na het invloeien op vol volume (%.1f dB)" % p1.volume_db)

	m.zet(&"briefing")
	var p2 := m.speler()
	_check(p2 != p1 and p2.playing and p2.stream == t3, "briefing: track 3 op de andere speler")
	_check(p1.playing, "overvloeien: track 2 klinkt nog even")
	await _wacht(Muziek.FADE + 0.3)
	_check(not p1.playing, "na het overvloeien is track 2 gestopt")
	_check(p2.playing and p2.volume_db > -1.0, "track 3 op vol volume")

	m._bij_brief_dicht()
	_check(m.context == &"missie", "briefing dicht: context missie")
	await _wacht(Muziek.FADE + 0.3)
	_check(not p1.playing and not p2.playing, "missie: stil (zoals het origineel)")
	m._bij_einde("verloren")
	_check(m.context == &"verloren", "einde: context verloren")
	m.zet(&"bestaat_niet")
	_check(m.context == &"verloren", "onbekende context: genegeerd")

	# dempen en volume, bewaard in de cfg
	var bus := AudioServer.get_bus_index(Muziek.BUS)
	var gemeld := [0]
	m.gewijzigd.connect(func() -> void: gemeld[0] += 1)
	var k := InputEventKey.new()
	k.keycode = KEY_M
	k.pressed = true
	k.shift_pressed = true
	m._input(k)
	_check(m.stil and AudioServer.is_bus_mute(bus), "Shift+M: gedempt, bus Muziek stil")
	m.wissel_stil()
	_check(not m.stil and not AudioServer.is_bus_mute(bus), "nog eens: weer aan")
	m.zet_volume(0.3)
	_check(absf(AudioServer.get_bus_volume_db(bus) - linear_to_db(0.3)) < 0.01, "volume 0,3 op de bus")
	m.zet_stil(true)
	_check(gemeld[0] == 4, "gewijzigd bij elke verandering (%d)" % gemeld[0])
	var n := Muziek.new()          # teruglezen zoals bij een nieuwe start
	_check(n.stil and is_equal_approx(n.volume, 0.3), "bewaard en teruggelezen: gedempt, volume 0,3")
	n.free()
	m.zet_volume(5.0)
	_check(is_equal_approx(m.volume, 1.0), "volume begrensd op 1")
	var cf := ConfigFile.new()
	cf.set_value("muziek", "volume", "onzin")
	cf.set_value("muziek", "stil", 3)
	cf.save(CFG)
	var o := Muziek.new()
	_check(is_equal_approx(o.volume, Muziek.VOLUME_STANDAARD) and not o.stil, "onzin in de cfg: standaard")
	o.free()

	# een echte track van schijf (alleen als audio/haal_muziek.ps1 hem maakte)
	for t in [2, 3]:
		if FileAccess.file_exists(Muziek.pad(t)) or ResourceLoader.exists(Muziek.pad(t)):
			var s: AudioStream = Geluid.laad(Muziek.pad(t))
			_check(s != null and s.get_length() > 0.0, "laadt: " + Muziek.pad(t))
		else:
			print("LET OP  %s ontbreekt (eigen cd-rip, audio/haal_muziek.ps1): het spel blijft daar stil" % Muziek.pad(t))
	_check(m.stream_voor(0) == null, "track 0 = stilte")

	m.queue_free()
	DirAccess.remove_absolute(ProjectSettings.globalize_path(CFG))
	await process_frame
	print("%s  audio: %d fouten" % ["OK" if fout == 0 else "FOUT", fout])
	quit(1 if fout > 0 else 0)
