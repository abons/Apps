extends SceneTree
## Headless: laden alle verwachte klanken (view/geluid.gd catalogus) en staan de bussen?
## audio/eigen/ moet compleet zijn (in git). assets/audio/beasts/ (uit beasts-src, sync.ps1) alleen als de map er is.
##   "$G" --headless --path . --script res://test/audio_test.gd

const Geluid := preload("res://view/geluid.gd")


func _init() -> void:
	var fout := 0
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
				print("FOUT  laadt niet: ", pad)
				fout += 1
			else:
				ok += 1
	for lus in Geluid.LUSSEN:
		var s: AudioStream = Geluid.laad(Geluid.EIGEN + lus + ".wav")
		if s != null and s.get_length() < 3.0:
			print("FOUT  lus te kort: ", lus)
			fout += 1
	Geluid.zet_bussen()
	for bus in Geluid.BUSSEN:
		if AudioServer.get_bus_index(bus) < 0:
			print("FOUT  bus ontbreekt: ", bus)
			fout += 1
	print("%s  audio: %d klanken geladen, %d fouten" % ["OK" if fout == 0 else "FOUT", ok, fout])
	quit(1 if fout > 0 else 0)
