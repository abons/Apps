extends SceneTree
## Headless test van het portret (besluit gebruiker 2026-10-31: de Gemini-portretten in plaats van de 3D-kop):
## godot --headless --path . -s test/portret_test.gd
## Mapping per soort en rol uit spel.json `portret` (oude man 00, oude vrouw 17, man 12, vrouw 13, jongen 02,
## meisje 07, bouwer 03, voetsoldaat 04), het paneel toont de png bijgesneden met ronde hoeken, en zonder png
## (schone checkout, of een map die niet bestaat) de 3D-render uit het model.
## De png's staan niet in git (sync.ps1 -> assets/portret/); ontbreken ze, dan slaat de test de png-checks over.

var fouten := 0


func _initialize() -> void:
	process_frame.connect(_start, CONNECT_ONE_SHOT)


func _start() -> void:
	root.size = Vector2i(1600, 900)
	var w := Wereld.new()
	_check(w.laad("", 1), "missie 1 laadt")
	var c: Dictionary = w.spel.get("portret", {})
	_check(not c.is_empty(), "spel.json heeft portret")
	var verwacht := [["man", "volwassen", "", "bust12.png"], ["vrouw", "volwassen", "", "bust13.png"],
		["man", "kind", "", "bust02.png"], ["vrouw", "kind", "", "bust07.png"],
		["man", "oud", "", "bust00.png"], ["vrouw", "oud", "", "bust17.png"],
		["man", "volwassen", "bouwer", "bust03.png"], ["man", "volwassen", "voetsoldaat", "bust04.png"]]
	# de data zelf (los van of de png er is)
	for v in verwacht:
		var sl := Portret.soort_sleutel(v[0], v[1])
		var b: String = c["rol"][v[2]] if v[2] != "" else c["soort"][sl]
		_check(b == v[3], "data: %s %s %s -> %s (%s)" % [v[0], v[1], v[2], b, v[3]])
	_check((c["rol"] as Dictionary).size() >= 12, "data: ook de rollen zonder eenheid (%d)" % (c["rol"] as Dictionary).size())
	var heeft_png := ResourceLoader.exists("res://assets/portret/bust12.png")
	if heeft_png:
		for v in verwacht:
			var p := Portret.bestand_voor(w.spel, v[0], v[1], v[2])
			_check(p == "res://assets/portret/" + v[3], "bestand: %s %s %s -> %s" % [v[0], v[1], v[2], p])
	else:
		print("  --   assets/portret/ ontbreekt (sync.ps1): png-checks overgeslagen")

	# terugval: een map zonder png's, en een rol met een ontbrekend bestand
	var leeg := w.spel.duplicate(true)
	leeg["portret"]["map"] = "res://assets/bestaat_niet/"
	_check(Portret.bestand_voor(leeg, "man", "volwassen") == "", "terugval: map zonder png -> ''")
	var rol_mist := w.spel.duplicate(true)
	rol_mist["portret"]["rol"]["bouwer"] = "bestaat_niet.png"
	_check(Portret.bestand_voor(rol_mist, "man", "volwassen", "bouwer") == "", "terugval: rol zonder png -> 3D (niet de soort)")
	_check(Portret.bestand_voor({}, "man", "volwassen") == "", "terugval: geen portret in de data")

	# het paneel
	var hud := CanvasLayer.new()
	root.add_child(hud)
	var pt := Portret.new()
	pt.bouw(w, false, 1.0)
	hud.add_child(pt)
	var d: Dorpeling = null
	for x in w.dorpelingen:
		if x.leeftijd == "volwassen" and x.rol == "":
			d = x
			break
	_check(d != null, "een volwassen dorpeling")
	if d != null:
		pt.zet(d)
		var kop := pt.find_child("Kop", true, false) as TextureRect
		if heeft_png:
			_check(pt.png == Portret.bestand_voor(w.spel, d.geslacht, d.leeftijd, d.rol), "paneel: png %s" % pt.png)
			var t := kop.texture
			_check(t is ImageTexture and t.get_width() == roundi(Portret.KOP_PC), "paneel: kop is de png op %d px" % roundi(Portret.KOP_PC))
			var img := t.get_image()
			_check(img.get_pixel(0, 0).a < 0.05 and img.get_pixel(55, 55).a > 0.99, "paneel: ronde hoek doorzichtig, midden dicht")
			# rol wisselt het portret
			d.rol = "bouwer"
			pt.zet(d)
			_check(pt.png.ends_with("bust03.png"), "paneel: bouwer -> bust03 (%s)" % pt.png)
			d.rol = ""
		# zonder png: de 3D-render
		pt.w = Wereld.new()
		pt.w.spel = leeg
		pt.zet(d)
		_check(pt.png == "" and kop.texture is ViewportTexture, "terugval: paneel toont de 3D-render")
		_check(pt._model != null, "terugval: model geladen")
	_klaar()


func _klaar() -> void:
	print("portret_test: %s" % ("OK" if fouten == 0 else "%d FOUT(EN)" % fouten))
	quit(1 if fouten > 0 else 0)


func _check(ok: bool, wat: String) -> void:
	if not ok:
		fouten += 1
	print(("  ok   " if ok else "  FOUT ") + wat)
