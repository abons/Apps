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


## Richting waarin de deur kijkt, in tegels: de hut-glb heeft zijn voordeur aan -x, en draaien gaat zoals
## Bouwmenu (rotation.y = draai * 90 graden): 0 -> (-1,0), 1 -> (0,1), 2 -> (1,0), 3 -> (0,-1).
func deur_richting() -> Vector2i:
	return [Vector2i(-1, 0), Vector2i(0, 1), Vector2i(1, 0), Vector2i(0, -1)][draai]


## De tegel voor de deur, net buiten de voetafdruk, midden op die zijde.
func deur_tegel() -> Vector2i:
	var r := afdruk()
	var m := r.position + r.size / 2
	match draai:
		0: return Vector2i(r.position.x - 1, m.y)
		1: return Vector2i(m.x, r.end.y)
		2: return Vector2i(r.end.x, m.y)
		_: return Vector2i(m.x, r.position.y - 1)


func afdruk() -> Rect2i:
	return Rect2i(tegel, Vector2i(diep, breed) if draai % 2 == 1 else Vector2i(breed, diep))
