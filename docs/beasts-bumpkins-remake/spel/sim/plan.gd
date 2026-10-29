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


func afdruk() -> Rect2i:
	return Rect2i(tegel, Vector2i(diep, breed) if draai % 2 == 1 else Vector2i(breed, diep))
