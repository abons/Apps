class_name Kip
extends RefCounted
## Een kip in de sim: hoort bij een kippenhok, scharrelt rond de deur, legt na `kip_leeg_s` een ei en blijft daarop
## zitten tot een volwassene het raapt (beasts-src Herd: kip `again` 55 s, `work` 1,6 s). Kent geen Node: de view
## spiegelt haar (view/kip_model.gd, clips idle/lopen/pikken/zitten).

const LOOP_MPS := 0.35        ## kip_anim.json "lopen"
const ZWERF_STRAAL := 3

var id := 0
var hok: Plan
var pos := Vector2.ZERO
var vorige := Vector2.ZERO
var route: Array[Vector2] = []
var anker := Vector2i.ZERO
var wacht := 2.0
var leeg := 0.0               ## s tot het volgende ei
var ei := false               ## zit op een ei
var vast := false             ## iemand komt het ei rapen
var pikt := false             ## staat te pikken (alleen weergave)
var snelheid_mps := 0.0


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
	if not ei:
		leeg = maxf(0.0, leeg - dt)
		if leeg <= 0.0 and route.is_empty():
			ei = true
	if ei or vast:
		route.clear()
		pikt = false
		return
	if route.is_empty():
		_scharrel(w, dt)
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


func _scharrel(w: Wereld, dt: float) -> void:
	wacht -= dt
	if wacht > 0.0:
		return
	wacht = w.rng.randf_range(2.0, 7.0)
	pikt = w.rng.randf() < 0.6        # de helft van het stilstaan is pikken
	for _i in 8:
		var t := anker + Vector2i(w.rng.randi_range(-ZWERF_STRAAL, ZWERF_STRAAL), w.rng.randi_range(-ZWERF_STRAAL, ZWERF_STRAAL))
		if t == tegel() or not w.raster.loopbaar_v(t) or w.bereik[w.raster.idx(t.x, t.y)] == 0:
			continue
		var r := Router.route(w.raster, tegel(), t)
		if not r.is_empty():
			route = Router.glad(w.raster, pos, r)
			pikt = false
			return
