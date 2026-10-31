class_name DeurLoop
extends RefCounted
## Het laatste stukje naar binnen en weer naar buiten (alleen beeld; de sim blijft op tegels): de sim zet `binnen` op de
## deurtegel, de view loopt hem van daar over de stoep naar het deuranker (Plan.deur_punt) en BINNEN_M erachter, en
## verbergt hem pas daar. Naar buiten andersom, van binnen door de deur naar waar de sim hem neerzette.
## `f` 0 = op de simplek, 1 = binnen (onzichtbaar).

const BINNEN_M := Plan.BINNEN_M   ## voorbij de drempel tot hij verdwijnt (muur en deur dekken hem dan af)
const UIT_MAX_S := 2.5      ## naar buiten hooguit zo lang: de sim kan hem al verder hebben laten lopen
const ZOEK_TEGELS := 5.0    ## deur zoeken als de view niet weet welk gebouw (bijv. bij de start al binnen)
## Put (bron.glb): de trap over het water naar de deur, als (meters vóór deur_punt, hoogte boven de grond), van ver
## naar dichtbij, ertussen lineair; treden uit modellen/natuur/props.py bron() (voorkanten 1,7 / 1,35 / 0,95 / 0,5 m
## voor het anker, bovenkanten 0,19 / 0,375 / 0,56 / 0,75 m).
const PUT_TRAP := [Vector2(1.75, 0.0), Vector2(1.65, 0.19), Vector2(1.40, 0.19), Vector2(1.30, 0.375),
	Vector2(1.00, 0.375), Vector2(0.90, 0.56), Vector2(0.55, 0.56), Vector2(0.45, 0.75)]


## Gebouw waar hij in gaat of uit komt: slaapplek, gezinshut, anders de dichtste afgebouwde deur binnen ZOEK_TEGELS.
static func gebouw(w: Wereld, d: Dorpeling) -> Plan:
	if d.slaapplek != null:
		return d.slaapplek
	if d.klus is Plan and Plan.DEUREN.has((d.klus as Plan).soort):
		return d.klus
	if not d.wieg.is_empty() and d.wieg.get("hut") is Plan:
		return d.wieg["hut"]
	var beste: Plan = null
	var af := ZOEK_TEGELS * ZOEK_TEGELS
	for p in w.plannen:
		if not p.klaar or not Plan.DEUREN.has(p.soort):
			continue
		var a := d.pos.distance_squared_to(Vector2(p.deur_tegel()) + Vector2(0.5, 0.5))
		if a < af:
			af = a
			beste = p
	return beste


## Is hij voor het beeld binnen: in de hut, of aan het leveren/kopen en nog niet aan het naar buiten lopen.
static func binnen(w: Wereld, d: Dorpeling) -> bool:
	return d.binnen or (d.bezig > 0.0 and d.route.is_empty() and d.bezig > w.deur_loop_s(d) + 0.05 and w.deur_loop_s(d) > 0.0)


## Punt (meters x, z) op het pad buiten -> deuranker -> binnen, bij fractie f.
static func punt(buiten: Vector2, p: Plan, tm: float, f: float) -> Vector2:
	var b := p.deur_punt(tm)
	var c := b - Vector2(p.deur_richting()) * BINNEN_M
	var l1 := buiten.distance_to(b)
	var s := clampf(f, 0.0, 1.0) * (l1 + BINNEN_M)
	if s <= l1:
		return buiten.lerp(b, s / l1) if l1 > 1e-4 else b
	return b.lerp(c, (s - l1) / BINNEN_M)


## Hoogte boven de grond op punt `q` (meters x, z) van het pad naar de deur: de trap van de put, anders 0.
static func hoogte(p: Plan, q: Vector2, tm: float) -> float:
	if p.soort != &"put":
		return 0.0
	var s := (q - p.deur_punt(tm)).dot(Vector2(p.deur_richting()))
	if s >= PUT_TRAP[0].x:
		return 0.0
	for i in range(1, PUT_TRAP.size()):
		var b: Vector2 = PUT_TRAP[i]
		if s >= b.x:
			var a: Vector2 = PUT_TRAP[i - 1]
			return lerpf(b.y, a.y, (s - b.x) / (a.x - b.x))
	return PUT_TRAP[-1].y


## Nieuwe f na dt (spelseconden): naar 1 als hij binnen is, naar 0 als niet; v_mps is de loopsnelheid in de sim.
static func stap(f: float, binnen: bool, buiten: Vector2, p: Plan, tm: float, v_mps: float, dt: float) -> float:
	var l := buiten.distance_to(p.deur_punt(tm)) + BINNEN_M
	var r := v_mps / maxf(l, 0.1)
	if not binnen:
		r = maxf(r, 1.0 / UIT_MAX_S)
	return move_toward(f, 1.0 if binnen else 0.0, r * dt)
