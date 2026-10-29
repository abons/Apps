class_name Dorpeling
extends RefCounted
## Dorpeling in de sim: positie in tegels (continu; tegel (x,y) = [x,x+1)), route, bevel, zwerven.
## Kent geen Node: de view spiegelt hem (view/bumpkin.gd volgt `pos` en `snelheid_mps`).

var id := 0
var naam := ""
var sex_ruw := 0          ## zoals in map1.json: 1 man, 2 vrouw, 13/14 onbekend (vermoedelijk kind, niet geverifieerd)
var geslacht := "onbekend"
var leeftijd := "volwassen"   ## volwassen | kind | oud
var pos := Vector2.ZERO
var vorige := Vector2.ZERO    ## positie bij de vorige tik, voor interpolatie in de view
var route: Array[Vector2] = []   ## te volgen punten (tegelmiddens, in tegelcoördinaten), recht getrokken door Router.glad
var bevel := {}               ## {} (geen) of {"soort": "loop"|"vecht"|"werk", "doel": Vector2i}
var anker := Vector2i.ZERO    ## zwerfmiddelpunt: het kampvuur, na een bevel de plek waar hij bleef staan
var wacht := 2.0
var werk_plan: Plan = null   ## bouwplek waar hij heen loopt en aan werkt
var bouwt := false           ## in deze tik aan het bouwen (view: hamerlus)
var snelheid_mps := 0.0       ## werkelijke loopsnelheid in deze tik, m/s incl. looptempo (0 = stil)


func volwassen() -> bool:
	return leeftijd == "volwassen"


## Lopen kan iedereen; vechten en werken alleen volwassenen.
func kan_bevel(soort: String) -> bool:
	return soort == "loop" or volwassen()


func tegel() -> Vector2i:
	return Vector2i(int(floor(pos.x)), int(floor(pos.y)))


func zet_tegel(t: Vector2i) -> void:
	pos = Vector2(t) + Vector2(0.5, 0.5)
	vorige = pos


func geef_bevel(w: Wereld, soort: String, doel: Vector2i) -> bool:
	if not kan_bevel(soort):
		return false
	werk_plan = null
	var r := Router.route(w.raster, tegel(), doel)
	if r.is_empty() and tegel() != doel:
		return false
	route = Router.glad(w.raster, pos, r)
	bevel = {"soort": soort, "doel": doel}
	if r.is_empty():
		_klaar()
	return true


func _klaar() -> void:
	anker = tegel()
	bevel = {}
	wacht = 1.0


func tick(w: Wereld, dt: float) -> void:
	vorige = pos
	snelheid_mps = 0.0
	bouwt = false
	if route.is_empty():
		if werk_plan != null and not werk_plan.klaar:
			bouwt = true
			werk_plan.voortgang = minf(1.0, werk_plan.voortgang + dt / werk_plan.bouwtijd_s)
			return
		if bevel.is_empty():
			_zwerf(w, dt)
		return
	var rest := dt
	var teller := 0
	while rest > 1e-6 and not route.is_empty() and teller < 8:
		teller += 1
		var t := tegel()
		var f := w.raster.factor(t.x, t.y)
		if f <= 0.0:
			f = 1.0
		var eff: float = w.loop_mps * w.looptempo * f   # m/s
		var v := eff / w.tegel_m                     # tegels per seconde
		snelheid_mps = eff
		var doel := route[0]
		var d := doel - pos
		var afstand := d.length()
		var stap := v * rest
		if afstand <= stap:
			pos = doel
			route.pop_front()
			rest -= afstand / v
		else:
			pos += d / afstand * stap
			rest = 0.0
	if route.is_empty():
		_klaar()


func _zwerf(w: Wereld, dt: float) -> void:
	wacht -= dt
	if wacht > 0.0:
		return
	var lo: float = w.spel["zwerf_wacht"][0]
	var hi: float = w.spel["zwerf_wacht"][1]
	wacht = w.rng.randf_range(lo, hi)
	var straal: int = int(w.spel["zwerf_straal"])
	for _i in 8:
		var t := anker + Vector2i(w.rng.randi_range(-straal, straal), w.rng.randi_range(-straal, straal))
		if t == tegel() or not w.raster.loopbaar_v(t) or w.bereik[w.raster.idx(t.x, t.y)] == 0:
			continue
		var r := Router.route(w.raster, tegel(), t)
		if not r.is_empty():
			route = Router.glad(w.raster, pos, r)
			return
