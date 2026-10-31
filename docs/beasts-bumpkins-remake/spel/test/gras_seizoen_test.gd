extends SceneTree
## Seizoensgras (view/gras_seizoen.gd, besluit gebruiker 2026-10-31):
##   godot --headless --path . -s test/gras_seizoen_test.gd
## Elk seizoen geeft tot 70 % zijn eigen set (lente = e, zomer = c), aan het eind exact die van het volgende (winter ->
## lente rond), de overgang is continu (geen sprong tussen opeenvolgende stappen, ook niet over de seizoensgrens), elke
## set heeft alle uniforms en die bestaan in beide terreinshaders; stipjes 's winters uit; met de wereldklok volgt het
## dezelfde mengfactor als Wereld.sneeuw()/droog().

var fouten := 0


func _initialize() -> void:
	_test_sets()
	_test_overgang()
	_test_shaders()
	_test_klok()
	print("gras_seizoen_test: %s" % ("ALLES GOED" if fouten == 0 else "%d FOUT" % fouten))
	quit(1 if fouten > 0 else 0)


func _gelijk(a: Dictionary, b: Dictionary, tol := 1e-5) -> bool:
	for n in a:
		if _afstand(a[n], b[n]) > tol:
			return false
	return a.size() == b.size()


func _afstand(x, y) -> float:
	if x is Color:
		return maxf(maxf(absf(x.r - y.r), absf(x.g - y.g)), absf(x.b - y.b))
	return absf(float(x) - float(y))


func _test_sets() -> void:
	for s in 4:
		for f in [0.0, 0.3, 0.69]:
			_check(_gelijk(GrasSeizoen.waarden(s, f), GrasSeizoen.SETS[s]), "%s bij f=%.2f is zijn eigen set" % [Wereld.SEIZOENEN[s], f])
		_check(_gelijk(GrasSeizoen.waarden(s, 1.0), GrasSeizoen.SETS[(s + 1) % 4]), "%s eindigt op %s" % [Wereld.SEIZOENEN[s], Wereld.SEIZOENEN[(s + 1) % 4]])
		_check(GrasSeizoen.SETS[s].keys() == GrasSeizoen.LENTE.keys(), "%s heeft dezelfde uniforms als lente" % Wereld.SEIZOENEN[s])
	_check(_gelijk(GrasSeizoen.LENTE, _variant("e", GrasSeizoen.LENTE)), "lente = variant e")
	_check(_gelijk(GrasSeizoen.ZOMER, _variant("c", GrasSeizoen.ZOMER)), "zomer = variant c")
	_check(GrasSeizoen.WINTER["stip_sterkte"] == 0.0, "winter: geen stipjes")
	var h: Color = GrasSeizoen.HERFST["gras_kleur"]
	var z: Color = GrasSeizoen.ZOMER["gras_kleur"]
	_check(h.r > z.r and h.g <= z.g, "herfst geler/bruiner dan zomer (als grass_spring_fall.png)")
	var wk: Color = GrasSeizoen.WINTER["gras_kleur"]
	_check(wk.s < z.s and wk.s < h.s, "winter grijzer dan zomer en herfst")


## De set van variant `naam` aangevuld met de shader-standaarden voor wat de variant niet zet (alleen de sleutels van ref).
func _variant(naam: String, ref: Dictionary) -> Dictionary:
	var std := {"gras_licht_sterkte": 1.0, "gras_verzadiging": 1.0, "gras_helderheid": 1.0, "gras_macro": 0.0,
		"stip_sterkte": 1.0, "gras_droog_mee": 0.0, "gras_macro_kleur": ref["gras_macro_kleur"]}
	var uit := {}
	for n in ref:
		uit[n] = GrasVarianten.SETS[naam].get(n, std.get(n, ref[n]))
	return uit


func _test_overgang() -> void:
	var stap := 0.001
	var max_sprong := 0.0
	var vorige := GrasSeizoen.waarden(0, 0.0)
	for i in range(1, int(4.0 / stap) + 1):
		var t := i * stap
		var s := int(t) if t < 4.0 else 4
		var v := GrasSeizoen.waarden(s, t - s)
		for n in v:
			max_sprong = maxf(max_sprong, _afstand(v[n], vorige[n]))
		vorige = v
	# grootste verschil tussen sets is ~0,6 (gras_macro, verzadiging), smoothstep piekt op 1,5x / 0,3 per seizoen
	_check(max_sprong < 0.006, "continu over een heel jaar, grootste stap %.4f bij stap %.3f" % [max_sprong, stap])
	_check(_gelijk(vorige, GrasSeizoen.LENTE), "na vier seizoenen weer lente")
	var mid := GrasSeizoen.waarden(1, 0.85)
	_check(_afstand(mid["gras_kleur"], GrasSeizoen.ZOMER["gras_kleur"]) > 0.01 and _afstand(mid["gras_kleur"], GrasSeizoen.HERFST["gras_kleur"]) > 0.01, "midden in de overgang zomer->herfst tussen beide")


func _test_shaders() -> void:
	for pad in ["res://shaders/terrein.gdshader", "res://shaders/terrein_mobiel.gdshader"]:
		var sh: Shader = load(pad)
		var namen := {}
		for u in sh.get_shader_uniform_list():
			namen[u["name"]] = true
		for n in GrasSeizoen.LENTE:
			_check(namen.has(n), "%s heeft uniform %s" % [pad.get_file(), n])


func _test_klok() -> void:
	var w := Wereld.new()
	_check(w.laad("", 1), "missie 1 laadt")
	for t in [0.2, 0.75, 0.9, 1.0 - 1e-4]:
		w.tijd_s = (2.0 + t) * w.seizoen_duur()          # herfst
		var k := GrasSeizoen.meng(w.dag_t() / w.seizoen_duur())
		var verwacht := lerpf(Wereld.SNEEUW[2], Wereld.SNEEUW[3], k)
		_check(absf(w.sneeuw() - verwacht) < 1e-4, "herfst t=%.2f: zelfde mengfactor als Wereld.sneeuw() (%.3f)" % [t, k])


func _check(ok: bool, wat: String) -> void:
	if ok:
		print("  ok   ", wat)
	else:
		fouten += 1
		print("  FOUT ", wat)
