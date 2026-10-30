class_name BouwRij
extends RefCounted
## Een rij weg of hek uit een sleepbeweging (besluit gebruiker 2026-10-30): de route van de begintegel naar de
## eindtegel, recht naar de buren (4 richtingen: een hek met een schuine naad sluit geen weide, en een weg ziet er
## hoekig netter uit). A* met een strafje per bocht, zodat het op open grond een L wordt (een bocht) en om bomen,
## rotsen en gebouwen heen loopt; tegels die al weg (pad) of al hek zijn mogen erin en kosten niets.
## Lukt geen route (doel ingesloten of te ver om): de rechte L, eerst langs x, dan langs z; wat daarvan niet kan
## kleurt rood en wordt niet geplaatst.

const MARGE := 8            ## tegels buiten het rechthoekje begin-eind waarin de route mag omlopen
const BOCHT := 0.6          ## extra kosten per bocht (een stap is 1)
const DC := [1, 0, -1, 0]
const DR := [0, 1, 0, -1]

enum { KAN, BESTAAT, KAN_NIET, TE_DUUR }


## Tegels van `a` naar `b` (beide erin) voor een rij `soort` (&"weg" of &"hek").
static func route(w: Wereld, soort: StringName, a: Vector2i, b: Vector2i) -> Array[Vector2i]:
	if a == b:
		return [a]
	var x0 := mini(a.x, b.x) - MARGE
	var y0 := mini(a.y, b.y) - MARGE
	var br := absi(a.x - b.x) + 2 * MARGE + 1
	var hg := absi(a.y - b.y) + 2 * MARGE + 1
	var n := br * hg * 4
	var kost := PackedFloat32Array()
	kost.resize(n)
	kost.fill(INF)
	var vorige := PackedInt32Array()
	vorige.resize(n)
	vorige.fill(-1)
	var vrij := {}              # tegel -> bool, per aanroep onthouden (kan_bouwen loopt alle plannen langs)
	var hp := PackedFloat32Array()
	var hi := PackedInt32Array()
	for r in 4:
		var s := ((a.y - y0) * br + (a.x - x0)) * 4 + r
		kost[s] = 0.0
		_push(hp, hi, _h(a, b), s)
	var eind := -1
	while hi.size() > 0:
		var top := _pop(hp, hi)
		var cel := top / 4
		var r0 := top % 4
		var t := Vector2i(x0 + cel % br, y0 + cel / br)
		if t == b:
			eind = top
			break
		var k := kost[top]
		for r in 4:
			var nt := t + Vector2i(DC[r], DR[r])
			if nt.x < x0 or nt.y < y0 or nt.x >= x0 + br or nt.y >= y0 + hg:
				continue
			if not vrij.has(nt):
				vrij[nt] = status(w, soort, nt) != KAN_NIET
			if not vrij[nt]:
				continue
			var nk := k + 1.0 + (BOCHT if r != r0 else 0.0)
			var ni := ((nt.y - y0) * br + (nt.x - x0)) * 4 + r
			if nk < kost[ni]:
				kost[ni] = nk
				vorige[ni] = top
				_push(hp, hi, nk + _h(nt, b), ni)
	var uit: Array[Vector2i] = []
	if eind < 0:
		return l_route(a, b)
	var i := eind
	while i >= 0:
		var c := i / 4
		uit.push_front(Vector2i(x0 + c % br, y0 + c / br))
		i = vorige[i]
	return uit


## De rechte L: eerst langs x, dan langs z.
static func l_route(a: Vector2i, b: Vector2i) -> Array[Vector2i]:
	var uit: Array[Vector2i] = []
	var t := a
	uit.append(t)
	while t.x != b.x:
		t.x += signi(b.x - t.x)
		uit.append(t)
	while t.y != b.y:
		t.y += signi(b.y - t.y)
		uit.append(t)
	return uit


## Wat een tegel in de rij is: KAN (nieuw plan), BESTAAT (al weg / al hek of poort, wordt overgeslagen), KAN_NIET.
static func status(w: Wereld, soort: StringName, t: Vector2i) -> int:
	if not w.raster.in_kaart(t.x, t.y):
		return KAN_NIET
	if soort == &"weg":
		if w.raster.soort_naam(t.x, t.y) == "pad":
			return BESTAAT
		var q := w.plan_op(t)
		if q != null and q.soort == &"weg":
			return BESTAAT
	else:
		for q in w.plannen:
			if (q.soort == &"hek" or q.soort == &"poort") and q.tegel == t:
				return BESTAAT
	var p := w.maak_plan(soort, t, 0)
	return KAN if p != null else KAN_NIET


## Status per tegel van een rij, met de kas erbij: wat niet meer te betalen is wordt TE_DUUR.
static func statussen(w: Wereld, soort: StringName, tegels: Array[Vector2i]) -> Array[int]:
	var uit: Array[int] = []
	var kas := w.kas
	var prijs := w.prijs(soort)
	for t in tegels:
		var s := status(w, soort, t)
		if s == KAN:
			if kas < prijs:
				s = TE_DUUR
			else:
				kas -= prijs
		uit.append(s)
	return uit


## Zet de rij neer: een plan per tegel die kan (elk betaalt zijn eigen prijs). Geeft het aantal nieuwe plannen.
static func zet(w: Wereld, soort: StringName, tegels: Array[Vector2i]) -> int:
	var n := 0
	for t in tegels:
		if status(w, soort, t) != KAN:
			continue
		var p := w.maak_plan(soort, t, 0)
		if p != null and w.plan_zet(p):
			n += 1
	return n


static func _h(t: Vector2i, b: Vector2i) -> float:
	return float(absi(t.x - b.x) + absi(t.y - b.y))


static func _push(hp: PackedFloat32Array, hi: PackedInt32Array, prio: float, v: int) -> void:
	hp.append(prio)
	hi.append(v)
	var i := hp.size() - 1
	while i > 0:
		var o := (i - 1) / 2
		if hp[o] <= hp[i]:
			break
		var tp := hp[o]; hp[o] = hp[i]; hp[i] = tp
		var ti := hi[o]; hi[o] = hi[i]; hi[i] = ti
		i = o


static func _pop(hp: PackedFloat32Array, hi: PackedInt32Array) -> int:
	var top := hi[0]
	var last := hp.size() - 1
	hp[0] = hp[last]
	hi[0] = hi[last]
	hp.resize(last)
	hi.resize(last)
	var i := 0
	while true:
		var l := i * 2 + 1
		var r := l + 1
		var m := i
		if l < last and hp[l] < hp[m]:
			m = l
		if r < last and hp[r] < hp[m]:
			m = r
		if m == i:
			break
		var tp := hp[m]; hp[m] = hp[i]; hp[i] = tp
		var ti := hi[m]; hi[m] = hi[i]; hi[i] = ti
		i = m
	return top
