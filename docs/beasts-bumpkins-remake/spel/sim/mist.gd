class_name Mist
extends RefCounted
## Mist van oorlog (fog of war), zoals het origineel (../mist.md): twee standen per tegel, onverkend (zwart) of
## verkend. Wat eenmaal verkend is blijft zichtbaar, ook als er niemand meer staat (het origineel kent geen grijze
## "niet meer in zicht"-laag). Start: verkend rond de eigen vlag en het kampvuur (`mist.start_straal`), plus het zicht
## van de startdorpelingen. Daarna verkent elke dorpeling binnen `mist.dorpeling` tegels en elk afgebouwd gebouw
## binnen `mist.gebouw`. Tegel `leeg` (het buitengebied) wordt nooit verkend. Leest de wereld, schrijft er niets in;
## de view (view/mist_view.gd) leest `verkend` en `versie`.

var aan := true
var verkend := PackedByteArray()   ## per tegel (Raster.idx): 1 = verkend
var versie := 0                    ## telt op bij elke wijziging (view: textuur bijwerken)
var start_straal := 8.0
var zicht_dorpeling := 4.0
var zicht_gebouw := 4.0
var _laatst := {}                  ## dorpeling-id -> tegel waarop hij het laatst verkende
var _gebouwd := {}                 ## Plan -> true: al verkend
var _leeg := -1
var _r: Raster


func start(w: Wereld) -> void:
	_r = w.raster
	_leeg = _r.namen.find("leeg")
	var def: Dictionary = w.spel.get("mist", {})
	start_straal = float(def.get("start_straal", start_straal))
	zicht_dorpeling = float(def.get("dorpeling", zicht_dorpeling))
	zicht_gebouw = float(def.get("gebouw", zicht_gebouw))
	verkend.resize(_r.kolommen * _r.rijen)
	verkend.fill(0)
	_laatst.clear()
	_gebouwd.clear()
	onthul(w.kampvuur, start_straal)
	var vlag := eigen_vlag(w)
	if vlag.x >= 0:
		onthul(vlag, start_straal)
	tik(w)


## Tegel van de eigen vlag (object "vlag", eigenaar 0) die het dichtst bij het kampvuur staat, (-1,-1) als er geen is.
static func eigen_vlag(w: Wereld) -> Vector2i:
	var best := Vector2i(-1, -1)
	var bd := INF
	for ob in w.objecten:
		if ob.get("naam", "") == "vlag" and int(ob.get("owner", 0)) == 0:
			var t := Vector2i(int(ob["x"]), int(ob["y"]))
			var d := Vector2(t - w.kampvuur).length()
			if d < bd:
				bd = d
				best = t
	return best


## Zet aan/uit. Uit = alles zichtbaar (frame-scenario's, --mist=uit); de sim verkent gewoon door.
func zet_aan(a: bool) -> void:
	aan = a
	versie += 1


func tik(w: Wereld) -> void:
	for d in w.dorpelingen:
		var t := d.tegel()
		if _laatst.get(d.id, Vector2i(-9999, -9999)) != t:
			_laatst[d.id] = t
			onthul(t, zicht_dorpeling)
	for p in w.plannen:
		if p.klaar and not _gebouwd.has(p):
			_gebouwd[p] = true
			var a := p.afdruk()
			onthul(a.position + a.size / 2, zicht_gebouw + maxf(a.size.x, a.size.y) * 0.5)


## Verkent alle tegels binnen `straal` (tegels, cirkel om het tegelmidden) behalve `leeg`.
func onthul(t: Vector2i, straal: float) -> void:
	var s := int(ceil(straal))
	var s2 := straal * straal + 0.25
	var nieuw := false
	for dy in range(-s, s + 1):
		var y := t.y + dy
		if y < 0 or y >= _r.rijen:
			continue
		for dx in range(-s, s + 1):
			var x := t.x + dx
			if x < 0 or x >= _r.kolommen or dx * dx + dy * dy > s2:
				continue
			var i := y * _r.kolommen + x
			if verkend[i] == 0 and _r.soort[i] != _leeg:
				verkend[i] = 1
				nieuw = true
	if nieuw:
		versie += 1


func is_verkend(t: Vector2i) -> bool:
	if not aan:
		return true
	return _r.in_kaart(t.x, t.y) and verkend[_r.idx(t.x, t.y)] == 1


func aantal() -> int:
	var n := 0
	for v in verkend:
		n += v
	return n
