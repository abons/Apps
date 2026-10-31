extends SceneTree
## Gedachten (sim/gedachten.gd, besluit gebruiker 2026-10-31):
##   godot --headless --path . --script res://test/gedachten_test.gd
## Elke behoefte geeft de goede gedachte, in de volgorde geraakt > honger > dorst > ziek > wil_<waar> > boos > somber >
## verliefd > blij; wil_<waar> alleen als de winkel staat of bouwbaar is; slapend of binnen niets; zichtbaar boven het
## hoofd alles behalve tevreden; de uitleg zegt wat je eraan doet; alle ikonen (view/gedachte_ikonen.gd) renderen;
## na een minuut spelen in missie 1 (nog geen kippenhok) wil iemand een ei.

var fouten := 0


func _initialize() -> void:
	_test_volgorde()
	_test_winkel()
	_test_ikonen()
	_test_spel()
	print("gedachten_test: %s" % ("ALLES GOED" if fouten == 0 else "%d FOUT" % fouten))
	quit(1 if fouten > 0 else 0)


func _wereld() -> Wereld:
	var w := Wereld.new()
	_check(w.laad("", 1), "missie 1 laadt")
	w.tik(w.tik_dt)          # Leven._begin: gezondheid uit de data
	return w


## Een volwassene zonder behoeften: geen trek, geen dorst, vol hp, geluk midden, niet geraakt.
func _rustig(d: Dorpeling) -> void:
	for waar in Wereld.WAREN:
		d.trek[waar] = 0.0
	d.dorst = 0.0
	d.gezondheid = d.gezondheid_max
	d.geraakt_s = 99.0
	d.geluk = 0.6
	d.wieg = {}
	d.slaapt = false
	d.binnen = false


func _test_volgorde() -> void:
	var w := _wereld()
	var d: Dorpeling = w.dorpelingen[0]
	_rustig(d)
	_is(w, d, &"", "geluk midden, geen behoefte: niets")
	d.geluk = 0.8
	_is(w, d, &"blij", "geluk hoog: blij")
	_check(not Gedachten.zichtbaar(&"blij") and Gedachten.zichtbaar(&"wil_ei"), "blij alleen bij de gekozen, wil_ei altijd")
	d.geluk = 0.6
	d.wieg = {"hut": null}
	_is(w, d, &"verliefd", "sticht een gezin: verliefd")
	d.geluk = 0.4
	_is(w, d, &"somber", "geluk laag gaat voor verliefd: somber")
	d.geluk = 0.1
	_is(w, d, &"boos", "geluk heel laag: boos")
	d.trek["ei"] = 70.0
	_is(w, d, &"wil_ei", "trek in een ei (kippenhok bouwbaar) gaat voor boos")
	d.trek["ei"] = 40.0
	_is(w, d, &"boos", "trek onder wil_s (koopt nog zelf): geen wolkje")
	d.trek["ei"] = 70.0
	d.gezondheid = 0.2 * d.gezondheid_max
	_is(w, d, &"ziek", "weinig hp gaat voor trek: ziek")
	d.dorst = 90.0 * 1.5 + 1.0
	_check(Gedachten.water_mogelijk(w), "missie 1 heeft water (de bron)")
	_is(w, d, &"dorst", "dorst gaat voor ziek")
	for waar in Wereld.WAREN:
		d.trek[waar] = 400.0
	_check(Leven.hongerig(w, d), "trek overal boven leven.honger.na_s: hongerig")
	_is(w, d, &"honger", "honger gaat voor dorst")
	_check(Gedachten.dringend(&"honger") and not Gedachten.dringend(&"wil_ei"), "honger dringend, wil_ei niet")
	d.geraakt_s = 1.0
	_is(w, d, &"geraakt", "net geraakt gaat voor alles")
	d.slaapt = true
	_is(w, d, &"", "slapend: niets")
	d.slaapt = false
	d.binnen = true
	_is(w, d, &"", "binnen: niets")
	for g: StringName in Gedachten.INFO:
		_check(Gedachten.tekst(g) != "" and Gedachten.ikoon(g) in GedachteIkonen.IKOON, "%s heeft tekst en ikoon" % g)


func _test_winkel() -> void:
	var w := _wereld()
	var d: Dorpeling = w.dorpelingen[0]
	_rustig(d)
	d.trek["brood"] = 90.0
	_check(not w.ontgrendeld(&"molen"), "missie 1 begin: molen nog niet bouwbaar")
	_is(w, d, &"", "trek in brood zonder bouwbare molen: geen wolkje")
	d.trek["ei"] = 70.0
	_is(w, d, &"wil_ei", "wel een ei")
	_check(Gedachten.uitleg(w, d, &"wil_ei") == "Bouw een kippenhok", "uitleg: bouw een kippenhok (%s)" % Gedachten.uitleg(w, d, &"wil_ei"))
	w.alles_open = true
	_is(w, d, &"wil_brood", "molen bouwbaar: de grootste trek (brood 90 > ei 70) wint")
	d.trek["melk"] = 120.0
	_is(w, d, &"wil_melk", "melk 120 wint")
	_check(Gedachten.uitleg(w, d, &"boos").contains("prijzen"), "uitleg boos noemt de prijzen")


func _test_ikonen() -> void:
	for naam: String in GedachteIkonen.IKOON:
		var t := GedachteIkonen.textuur(naam, true, false, 1.0)
		_check(t != null and t.get_width() == GedachteIkonen.ZIJ, "ikoon %s rendert" % naam)
	var a := GedachteIkonen.textuur("brood", true, true, 2.0, true)
	_check(a != null and a.get_width() == 2 * GedachteIkonen.ZIJ, "dringend, 2x, mipmaps")


func _test_spel() -> void:
	var w := _wereld()
	for i in int(65.0 / w.tik_dt):
		w.tik(w.tik_dt)
	var eieren := 0
	for d in w.dorpelingen:
		if Gedachten.van(w, d) == &"wil_ei":
			eieren += 1
	_check(eieren > 0, "na 65 s zonder kippenhok wil iemand een ei (%d)" % eieren)


func _is(w: Wereld, d: Dorpeling, verwacht: StringName, wat: String) -> void:
	var g := Gedachten.van(w, d)
	_check(g == verwacht, "%s (kreeg '%s')" % [wat, g])


func _check(ok: bool, wat: String) -> void:
	if ok:
		print("  ok   ", wat)
	else:
		fouten += 1
		print("  FOUT ", wat)
