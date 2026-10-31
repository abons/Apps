class_name Raster
extends RefCounted
## Tegelrooster van de kaart: tegelsoort per vakje, snelheidsfactor, blokkades door objecten.
## Gedeeld door sim, router en view. Kaartcoordinaten: kolom x, rij y (zoals map1.json).

const DC := [0, 1, 0, -1, 1, 1, -1, -1]   # recht eerst, dan schuin (zoals Tile.DC in beasts-src)
const DR := [-1, 0, 1, 0, -1, 1, 1, -1]

var kolommen := 0
var rijen := 0
var namen: Array[String] = []       # tegelsoort-index -> naam
var kleuren: Array[Color] = []
var loopbaar_soort := PackedByteArray()
var factor_soort := PackedFloat32Array()
var hoogte_soort := PackedFloat32Array()
var gras_soort := PackedFloat32Array()
var soort := PackedByteArray()      # per tegel: index in namen
var blok := PackedByteArray()       # per tegel: 1 = object blokkeert
var tex := PackedByteArray()        # per tegel: tegelframe uit de kaart (alleen weergave: lichte grasvlekken)
var max_factor := 1.0


func laad_tegels(def: Dictionary) -> void:
	for naam in def["tegels"]:
		var t: Dictionary = def["tegels"][naam]
		namen.append(naam)
		kleuren.append(Color.html(t["kleur"]))
		loopbaar_soort.append(1 if t["loopbaar"] else 0)
		factor_soort.append(float(t["factor"]))
		hoogte_soort.append(float(t["hoogte"]))
		gras_soort.append(float(t["gras"]))
		max_factor = maxf(max_factor, float(t["factor"]))


func maak(k: int, r: int) -> void:
	kolommen = k
	rijen = r
	soort.resize(k * r)
	soort.fill(namen.find("leeg"))
	blok.resize(k * r)
	blok.fill(0)
	tex.resize(k * r)
	tex.fill(0)


func idx(c: int, r: int) -> int:
	return r * kolommen + c


func in_kaart(c: int, r: int) -> bool:
	return c >= 0 and r >= 0 and c < kolommen and r < rijen


func soort_naam(c: int, r: int) -> String:
	return namen[soort[idx(c, r)]] if in_kaart(c, r) else "leeg"


func loopbaar(c: int, r: int) -> bool:
	if not in_kaart(c, r):
		return false
	var i := idx(c, r)
	return loopbaar_soort[soort[i]] == 1 and blok[i] == 0


func loopbaar_v(t: Vector2i) -> bool:
	return loopbaar(t.x, t.y)


func factor(c: int, r: int) -> float:
	return factor_soort[soort[idx(c, r)]] if in_kaart(c, r) else 0.0


## Prijs van het betreden van een tegel (duizendsten): gras 1000, pad ~870.
func prijs(c: int, r: int) -> int:
	return int(round(1000.0 / factor_soort[soort[idx(c, r)]]))


func goedkoopste_prijs() -> int:
	return int(round(1000.0 / max_factor))


## Mag een stap van (c,r) naar (nc,nr)? Schuin alleen als beide rechte buren open zijn
## (anders glipt een route door de punt tussen twee obstakels): Grid.canStep in beasts-src.
func kan_stap(c: int, r: int, nc: int, nr: int) -> bool:
	if not loopbaar(nc, nr):
		return false
	if c != nc and r != nr:
		return loopbaar(nc, r) and loopbaar(c, nr)
	return true
