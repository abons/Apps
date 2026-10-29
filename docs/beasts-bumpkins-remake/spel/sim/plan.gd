class_name Plan
extends RefCounted
## Een bestelde bouw: nog geen bouwplaats. Stap 5 van de bouwvolgorde (gameplay.md §7):
## Plan -> Site (dorpeling loopt erheen) -> Job (hamerlus) -> commit; prijs van de kas. Nog niet gebouwd.

var soort: StringName       ## "hut"
var tegel: Vector2i         ## linksboven van de voetafdruk
var draai: int              ## kwartslagen, 0..3
var breed: int
var diep: int


func _init(s: StringName, t: Vector2i, d: int, b: int, di: int) -> void:
	soort = s
	tegel = t
	draai = d
	breed = b
	diep = di


## Voetafdruk in tegels, na draaien (oneven kwartslag wisselt breed en diep).
func afdruk() -> Rect2i:
	return Rect2i(tegel, Vector2i(diep, breed) if draai % 2 == 1 else Vector2i(breed, diep))
