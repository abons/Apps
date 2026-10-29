class_name Vee
extends RefCounted
## Een koe in de sim: positie in tegels (continu, zoals Dorpeling), zwerft rond haar anker. Wild (eigenaar -1) graast bij
## de koe-generator; geclaimd (eigenaar 0, de speler) zwerft ze rond het kampvuur. Kent geen Node: view/wereld_view.gd
## spiegelt haar met view/koe.gd (halsband en bel zichtbaar bij een eigen koe).

const LOOP_MPS := 0.7097      ## koe_anim.json "lopen"; rustig, zonder looptempo
const ZWERF_STRAAL := 5

var id := 0
var pos := Vector2.ZERO
var vorige := Vector2.ZERO
var route: Array[Vector2] = []
var anker := Vector2i.ZERO
var wacht := 2.0
var eigenaar := -1            ## -1 wild, 0 speler
var van_generator := false    ## telt mee voor het maximum van de generator zolang ze wild is
var vast := false             ## er loopt iemand naartoe om haar te claimen: blijft staan
var snelheid_mps := 0.0
var leeg := 0.0               ## s tot ze weer melk geeft (beasts-src Herd.again: koe 90 s)
var gemolken := false         ## er zit iemand naast te melken (view: gemolken_worden)


func tegel() -> Vector2i:
	return Vector2i(int(floor(pos.x)), int(floor(pos.y)))


func zet_tegel(t: Vector2i) -> void:
	pos = Vector2(t) + Vector2(0.5, 0.5)
	vorige = pos


func tick(w: Wereld, dt: float) -> void:
	if not w.raster.loopbaar_v(tegel()):   # vangnet: nooit vast in een nieuw gebouw, hek of dichte poort
		var t := w.dichtstbij_loopbaar(tegel())
		if t.x >= 0:
			zet_tegel(t)
			route.clear()
	vorige = pos
	snelheid_mps = 0.0
	if vast:
		route.clear()
		return
	if route.is_empty():
		_zwerf(w, dt)
		return
	var v := LOOP_MPS / w.tegel_m
	var rest := dt
	while rest > 1e-6 and not route.is_empty():
		var d := route[0] - pos
		var afstand := d.length()
		var stap := v * rest
		snelheid_mps = LOOP_MPS
		if afstand <= stap:
			pos = route[0]
			route.pop_front()
			rest -= afstand / v
		else:
			pos += d / afstand * stap
			rest = 0.0


func _zwerf(w: Wereld, dt: float) -> void:
	wacht -= dt
	if wacht > 0.0:
		return
	wacht = w.rng.randf_range(5.0, 14.0)    # grazen duurt langer dan een dorpeling stilstaat
	for _i in 8:
		var t := anker + Vector2i(w.rng.randi_range(-ZWERF_STRAAL, ZWERF_STRAAL), w.rng.randi_range(-ZWERF_STRAAL, ZWERF_STRAAL))
		if t == tegel() or not w.raster.loopbaar_v(t) or w.bereik[w.raster.idx(t.x, t.y)] == 0:
			continue
		var r := Router.route(w.raster, tegel(), t)
		if not r.is_empty():
			route = Router.glad(w.raster, pos, r)
			return
