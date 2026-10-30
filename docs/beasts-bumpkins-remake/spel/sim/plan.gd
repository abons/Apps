class_name Plan
extends RefCounted
## Een bestelde bouw: nog geen bouwplaats. Stap 5 van de bouwvolgorde (gameplay.md §7):
## Plan -> Site (dorpeling loopt erheen) -> Job (hamerlus) -> commit; prijs van de kas. Nog niet gebouwd.

var soort: StringName       ## "hut"
var tegel: Vector2i         ## linksboven van de voetafdruk
var draai: int              ## kwartslagen, 0..3
var breed: int
var diep: int
const STANDEN := 4
var bouwtijd_s := 60.0     ## werker-seconden tot klaar (origineel: hut 60 s); werkers tellen op, geen limiet
var voortgang := 0.0       ## 0..1
var klaar := false
var voorraad := 0          ## molen: brood op het schap (beasts-src Building.stock)
var open := false          ## poort: open = loopbaar

## Voordeur per soort bij draai 0, in meters vanaf het midden van de voetafdruk (x, z), uit de glb-ankers
## (`deur_voor_drempel`, `deur_drempel`) min het midden van het omhulsel; de deur kijkt langs `richting`.
const DEUREN := {
	&"hut": {"plek": Vector2(-1.53, 0.07), "richting": Vector2i(-1, 0)},
	&"molen": {"plek": Vector2(1.05, 2.38), "richting": Vector2i(0, 1)},
	&"melkerij": {"plek": Vector2(-2.9, 0.16), "richting": Vector2i(-1, 0)},
	&"kippenhok": {"plek": Vector2(-0.45, -0.7), "richting": Vector2i(0, -1)},
	&"gereedschapsloods": {"plek": Vector2(0.6, 1.44), "richting": Vector2i(0, 1)},
	# Missie 3, eigen keuze (geen ankers: het gilde heeft nog geen glb, bron.glb geen deur): midden van de voorkant.
	# Put: de plek waar ze water halen (geen binnenloop, Wereld.deur_loop_s); gilde: de deur (sprite `footdoor`).
	&"put": {"plek": Vector2(0.0, 2.5), "richting": Vector2i(0, 1)},
	&"voetvolkgilde": {"plek": Vector2(0.0, 2.3), "richting": Vector2i(0, 1)},
}


func _init(s: StringName, t: Vector2i, d: int, b: int, di: int) -> void:
	soort = s
	tegel = t
	draai = d
	breed = b
	diep = di


## Voetafdruk in tegels, na draaien (oneven kwartslag wisselt breed en diep).
## Zichtbare bouwstand 1..STANDEN (STANDEN = klaar); begint bij 1 zodra het plan er staat.
func stand() -> int:
	return STANDEN if klaar else clampi(1 + int(voortgang * (STANDEN - 1)), 1, STANDEN - 1)


## Richting waarin de deur kijkt, in tegels, na draaien zoals Bouwmenu (rotation.y = draai * 90 graden).
func deur_richting() -> Vector2i:
	var r: Vector2i = DEUREN.get(soort, DEUREN[&"hut"])["richting"]
	return Vector2i(Vector2(r).rotated(-draai * PI * 0.5).round())


## Het deuranker in wereldmeters (x, z): waar de weg vanaf de deurtegel naartoe loopt (view/wegen.gd), want de
## voetafdruk is groter dan het gebouw en de deur ligt er dus binnen.
func deur_punt(tegel_m: float) -> Vector2:
	var r := afdruk()
	var d: Dictionary = DEUREN.get(soort, DEUREN[&"hut"])
	var m := (Vector2(r.position) + Vector2(r.size) * 0.5) * tegel_m
	return m + (d["plek"] as Vector2).rotated(-draai * PI * 0.5)


## De tegel voor de deur: het deuranker naar tegels, dan langs de deurrichting tot net buiten de voetafdruk.
func deur_tegel() -> Vector2i:
	var r := afdruk()
	var d: Dictionary = DEUREN.get(soort, DEUREN[&"hut"])
	var plek: Vector2 = (d["plek"] as Vector2).rotated(-draai * PI * 0.5) / 2.0   # tegels (2 m)
	var m := Vector2(r.position) + Vector2(r.size) * 0.5 + plek
	var t := Vector2i(int(floor(m.x)), int(floor(m.y)))
	t.x = clampi(t.x, r.position.x, r.end.x - 1)
	t.y = clampi(t.y, r.position.y, r.end.y - 1)
	var stap := deur_richting()
	while r.has_point(t):
		t += stap
	return t


## Het laatste stukje naar binnen, in meters: van het midden van de deurtegel naar het deuranker en BINNEN_M erachter.
## De sim staat dan stil op de deurtegel; de view loopt het (view/deur_loop.gd).
const BINNEN_M := 0.6
func deur_loop_m(tegel_m: float) -> float:
	return (Vector2(deur_tegel()) + Vector2(0.5, 0.5)).distance_to(deur_punt(tegel_m) / tegel_m) * tegel_m + BINNEN_M


func afdruk() -> Rect2i:
	return Rect2i(tegel, Vector2i(diep, breed) if draai % 2 == 1 else Vector2i(breed, diep))
