class_name Gegevens
extends RefCounted
## Laadt de json-bestanden. Geen engine-knopen: werkt ook in een headless test.

const SPEL := "res://data/spel.json"
const TEGELS := "res://data/tegels.json"
const OBJECTEN := "res://data/objecten.json"
const ANIM := "res://assets/bumpkin_anim.json"


static func lees(pad: String) -> Variant:
	if not FileAccess.file_exists(pad):
		push_error("gegevens: ontbreekt: " + pad)
		return null
	return JSON.parse_string(FileAccess.get_file_as_string(pad))


## Looptempo uit de animatie-sidecar (assets/), met de waarde uit spel.json als terugval.
static func loop_mps(spel: Dictionary) -> float:
	var a = lees(ANIM) if FileAccess.file_exists(ANIM) else null
	if a is Dictionary and a.has("lopen") and a["lopen"].has("snelheid_mps"):
		return float(a["lopen"]["snelheid_mps"])
	return float(spel.get("loop_mps", 0.849))
