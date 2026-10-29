class_name Router
extends RefCounted
## A* over het raster, acht richtingen, met de prijs van de grond erin (pad is goedkoper dan gras).
## Port van beasts-src Router.kt (route, reachable, octile-heuristiek tegen de goedkoopste grond).

const RECHT := 100
const SCHUIN := 141


## Route van `van` tot en met `naar`, zonder `van` zelf. Leeg als er geen route is of begin == eind.
static func route(r: Raster, van: Vector2i, naar: Vector2i) -> Array[Vector2i]:
	var uit: Array[Vector2i] = []
	if van == naar or not r.loopbaar_v(naar) or not r.loopbaar_v(van):
		return uit
	var n := r.kolommen * r.rijen
	var kost := PackedInt32Array()
	kost.resize(n)
	kost.fill(0x7fffffff)
	var vorige := PackedInt32Array()
	vorige.resize(n)
	vorige.fill(-1)
	var klaar := PackedByteArray()
	klaar.resize(n)
	var hp := PackedInt32Array()   # heap: prioriteit
	var hi := PackedInt32Array()   # heap: tegelindex
	var min_prijs := r.goedkoopste_prijs()
	var start := r.idx(van.x, van.y)
	var doel := r.idx(naar.x, naar.y)
	kost[start] = 0
	_push(hp, hi, _h(van.x, van.y, naar, min_prijs), start)
	while not hp.is_empty():
		var huidig := _pop(hp, hi)
		if huidig == doel:
			return _terug(r, vorige, doel)
		if klaar[huidig] == 1:
			continue
		klaar[huidig] = 1
		var c := huidig % r.kolommen
		var rij := huidig / r.kolommen
		for d in 8:
			var nc: int = c + Raster.DC[d]
			var nr: int = rij + Raster.DR[d]
			if not r.kan_stap(c, rij, nc, nr):
				continue
			var nxt := nr * r.kolommen + nc
			if klaar[nxt] == 1:
				continue
			var stap := r.prijs(nc, nr) * (SCHUIN if d >= 4 else RECHT)
			var kandidaat := kost[huidig] + stap
			if kandidaat < kost[nxt]:
				kost[nxt] = kandidaat
				vorige[nxt] = huidig
				_push(hp, hi, kandidaat + _h(nc, nr, naar, min_prijs), nxt)
	return uit


## Trekt een tegelroute recht: loopt vanaf `van` (tegelcoördinaten) steeds naar het verste routepunt dat in een rechte
## lijn vrij ligt (0,3 tegel ruimte aan weerszijden), zodat dorpelingen geen trap-zigzag lopen en niet op elke
## tegelhoek draaien. Geeft de te volgen punten (tegelmiddens).
static func glad(r: Raster, van: Vector2, route: Array[Vector2i]) -> Array[Vector2]:
	var pts: Array[Vector2] = []
	for t in route:
		pts.append(Vector2(t) + Vector2(0.5, 0.5))
	var uit: Array[Vector2] = []
	var huidig := van
	var i := 0
	while i < pts.size():
		var j := pts.size() - 1
		while j > i and not _vrij(r, huidig, pts[j]):
			j -= 1
		uit.append(pts[j])
		huidig = pts[j]
		i = j + 1
	return uit


static func _vrij(r: Raster, a: Vector2, b: Vector2) -> bool:
	var d := b - a
	var len := d.length()
	if len < 0.001:
		return true
	var loodrecht := Vector2(-d.y, d.x) / len * 0.3
	var stappen := int(ceil(len / 0.2))
	for s in range(1, stappen + 1):
		var p := a + d * (float(s) / stappen)
		for off in [Vector2.ZERO, loodrecht, -loodrecht]:
			var q: Vector2 = p + off
			if not r.loopbaar(int(floor(q.x)), int(floor(q.y))):
				return false
	return true


## Alle tegels waar je vanaf `van` kunt komen (stapregel zonder prijzen): vlag per tegel.
static func bereikbaar(r: Raster, van: Vector2i) -> PackedByteArray:
	var gezien := PackedByteArray()
	gezien.resize(r.kolommen * r.rijen)
	if not r.loopbaar_v(van):
		return gezien
	var stapel: Array[int] = [r.idx(van.x, van.y)]
	gezien[stapel[0]] = 1
	while not stapel.is_empty():
		var huidig: int = stapel.pop_back()
		var c := huidig % r.kolommen
		var rij := huidig / r.kolommen
		for d in 8:
			var nc: int = c + Raster.DC[d]
			var nr: int = rij + Raster.DR[d]
			if not r.kan_stap(c, rij, nc, nr):
				continue
			var nxt := nr * r.kolommen + nc
			if gezien[nxt] == 1:
				continue
			gezien[nxt] = 1
			stapel.append(nxt)
	return gezien


static func _h(c: int, rij: int, naar: Vector2i, min_prijs: int) -> int:
	var dc := absi(c - naar.x)
	var dr := absi(rij - naar.y)
	return min_prijs * (RECHT * (maxi(dc, dr) - mini(dc, dr)) + SCHUIN * mini(dc, dr))


static func _terug(r: Raster, vorige: PackedInt32Array, doel: int) -> Array[Vector2i]:
	var uit: Array[Vector2i] = []
	var at := doel
	while at != -1:
		uit.append(Vector2i(at % r.kolommen, at / r.kolommen))
		at = vorige[at]
	uit.remove_at(uit.size() - 1)   # het beginvak hoort er niet bij
	uit.reverse()
	return uit


static func _push(hp: PackedInt32Array, hi: PackedInt32Array, p: int, i: int) -> void:
	hp.append(p)
	hi.append(i)
	var k := hp.size() - 1
	while k > 0:
		var ouder := (k - 1) >> 1
		if hp[ouder] <= hp[k]:
			break
		var tp := hp[ouder]; hp[ouder] = hp[k]; hp[k] = tp
		var ti := hi[ouder]; hi[ouder] = hi[k]; hi[k] = ti
		k = ouder


static func _pop(hp: PackedInt32Array, hi: PackedInt32Array) -> int:
	var top := hi[0]
	var laatste := hp.size() - 1
	hp[0] = hp[laatste]
	hi[0] = hi[laatste]
	hp.resize(laatste)
	hi.resize(laatste)
	var k := 0
	var n := laatste
	while true:
		var l := 2 * k + 1
		var rr := l + 1
		var m := k
		if l < n and hp[l] < hp[m]:
			m = l
		if rr < n and hp[rr] < hp[m]:
			m = rr
		if m == k:
			break
		var tp := hp[m]; hp[m] = hp[k]; hp[k] = tp
		var ti := hi[m]; hi[m] = hi[k]; hi[k] = ti
		k = m
	return top
