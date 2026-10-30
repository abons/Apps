class_name Voorladen
extends RefCounted
## Alleen op mobiel (of `-- --voorladen` op de pc): vraagt bij de start alle glb's die de eerste opbouw nodig heeft
## tegelijk aan bij ResourceLoader.load_threaded_request. De worker-threads lezen ze parallel; de gewone `load()` in
## Natuur/Bumpkin/Koe wacht dan alleen nog op dat ene bestand, of vindt het al in de cache. Volgorde = volgorde van gebruik
## (kaartobjecten, bomen, kliffen, decoratie, dorpelingen, koeien). Niets aan het beeld verandert, alleen wanneer er
## gelezen wordt. Op de pc staat het uit, zodat de laadvolgorde daar blijft zoals hij was.

static var aan := OS.has_feature("mobile") or OS.get_cmdline_user_args().has("--voorladen")


static func start(missie: int) -> void:
	if not aan:
		return
	var namen: Array[String] = []
	var tekst := FileAccess.get_file_as_string(Gegevens.OBJECTEN) if FileAccess.file_exists(Gegevens.OBJECTEN) else ""
	var re := RegEx.create_from_string("\"(?:natuur:)?([a-z0-9_]+)\"")
	for m in re.search_all(tekst):
		var n := m.get_string(1)
		if missie < 2 and n.contains("wolf"):
			continue
		if not namen.has(n):
			namen.append(n)
	for n in ["klif_recht", "klif_hoek_buiten", "klif_hoek_binnen", "bumpkin_man", "bumpkin_vrouw"]:
		if not namen.has(n):
			namen.append(n)
	var paden: Array[String] = []
	for n in namen:
		var p := "res://assets/%s.glb" % n
		if ResourceLoader.exists(p):
			paden.append(p)
	paden.append(Koe.glb_pad())
	var k := 0
	for p in paden:
		if ResourceLoader.exists(p) and ResourceLoader.load_threaded_request(p, "", false) == OK:
			k += 1
	Prestatie.merk("voorladen: %d glb's aangevraagd" % k)
