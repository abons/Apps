class_name Gedachten
extends RefCounted
## Gedachten van een dorpeling (besluit gebruiker 2026-10-31: wolkjes boven het hoofd en bij het portret, zoals het
## origineel, maar duidelijker). Leest alleen bestaande toestand (trek, dorst, geluk, gezondheid, geraakt_s, wieg) en
## verandert niets: de regels zelf zitten in sim/wereld.gd, sim/leven.gd en sim/handel.gd.
## Origineel (thoughts-sprite, strings0 194-197): brood, ei, melk, appel, cider, water, blij, somber, liefde, boos en de
## meldingen "No water/bread/milk/cider". Daar was onduidelijk wat een wolkje betekende; hier heeft elke gedachte een
## korte tekst (pc) en een uitleg met wat de speler eraan kan doen (portret, pc). Dringend = er staat gezondheid op het
## spel (rode rand om het wolkje).
## Volgorde (de eerste die geldt wint):
##   geraakt (net schade) > honger (Leven.hongerig) > dorst > ziek (weinig hp) > wil_<waar> (de grootste trek) >
##   boos (geluk heel laag) > somber (geluk laag) > verliefd (sticht een gezin) > blij (geluk hoog) > "" (niets).
## Wil_<waar> en dorst tellen pas als de behoefte onvervuld blijft: hij koopt al bij economie.trek_s en drinkt bij
## economie.dorst_s, dus het wolkje komt bij wil_s / dorst_factor x dorst_s, en alleen als er in deze missie iets aan te
## doen is (de winkel staat of is bouwbaar; water: een bron op de kaart of de put is bouwbaar). Getallen in spel.json
## `gedachten` (eigen keuze), met dezelfde standaardwaarden hieronder.

const STANDAARD := {"geraakt_s": 8.0, "wil_s": 60.0, "dorst_factor": 1.5, "ziek_onder": 0.35, "boos_onder": 0.25,
	"somber_onder": 0.45, "blij_vanaf": 0.7}

## Gedachte -> ikoon (view/gedachte_ikonen.gd), korte tekst, dringend.
const INFO := {
	&"geraakt": {"ikoon": "boos", "tekst": "Aangevallen!", "dringend": true},
	&"honger": {"ikoon": "brood", "tekst": "Heeft honger", "dringend": true},
	&"dorst": {"ikoon": "water", "tekst": "Heeft dorst", "dringend": false},
	&"ziek": {"ikoon": "somber", "tekst": "Voelt zich ziek", "dringend": true},
	&"wil_brood": {"ikoon": "brood", "tekst": "Wil brood", "dringend": false},
	&"wil_melk": {"ikoon": "melk", "tekst": "Wil melk", "dringend": false},
	&"wil_ei": {"ikoon": "ei", "tekst": "Wil een ei", "dringend": false},
	&"wil_appel": {"ikoon": "appel", "tekst": "Wil een appel", "dringend": false},
	&"wil_cider": {"ikoon": "cider", "tekst": "Wil cider", "dringend": false},
	&"boos": {"ikoon": "boos", "tekst": "Is boos", "dringend": false},
	&"somber": {"ikoon": "somber", "tekst": "Is somber", "dringend": false},
	&"verliefd": {"ikoon": "liefde", "tekst": "Verliefd", "dringend": false},
	&"blij": {"ikoon": "blij", "tekst": "Tevreden", "dringend": false},
}

## Waar -> winkel (zoals Wereld.WINKELS, plus de waren die de remake nog niet heeft) en de naam voor de uitleg.
const WINKEL := {"brood": &"molen", "melk": &"melkerij", "ei": &"kippenhok", "appel": &"", "cider": &""}
const WINKEL_NAAM := {&"molen": "molen", &"melkerij": "melkerij", &"kippenhok": "kippenhok"}


static func cfg(w: Wereld, sleutel: String) -> float:
	return float(w.spel.get("gedachten", {}).get(sleutel, STANDAARD[sleutel]))


## De gedachte die nu het zwaarst weegt, of &"" (niets aan de hand, of slaapt / binnen).
static func van(w: Wereld, d: Dorpeling) -> StringName:
	if not d.leeft() or d.slaapt or d.binnen:
		return &""
	var hp := d.gezondheid / maxf(1.0, d.gezondheid_max)
	if d.geraakt_s < cfg(w, "geraakt_s"):
		return &"geraakt"
	if Leven.hongerig(w, d):
		return &"honger"
	var e: Dictionary = w.spel.get("economie", {})
	if d.dorst >= float(e.get("dorst_s", 90.0)) * cfg(w, "dorst_factor") and water_mogelijk(w):
		return &"dorst"
	if hp < cfg(w, "ziek_onder"):
		return &"ziek"
	var waar := grootste_trek(w, d)
	if waar != "":
		return StringName("wil_" + waar)
	if d.geluk < cfg(w, "boos_onder"):
		return &"boos"
	if d.geluk < cfg(w, "somber_onder"):
		return &"somber"
	if not d.wieg.is_empty():
		return &"verliefd"
	if d.geluk >= cfg(w, "blij_vanaf"):
		return &"blij"
	return &""


## De waar met de grootste onvervulde trek (>= wil_s) waar in deze missie iets aan te doen is, of "".
static func grootste_trek(w: Wereld, d: Dorpeling) -> String:
	var beste := ""
	var bt := cfg(w, "wil_s")
	for waar: String in d.trek:
		var t := float(d.trek[waar])
		if t >= bt and INFO.has(StringName("wil_" + waar)) and winkel_mogelijk(w, waar):
			bt = t
			beste = waar
	return beste


## De winkel voor die waar staat of is bouwbaar.
static func winkel_mogelijk(w: Wereld, waar: String) -> bool:
	var s: StringName = WINKEL.get(waar, &"")
	return s != &"" and (not w.winkels(s).is_empty() or w.ontgrendeld(s))


## Er is water te halen of te maken: een bron op de kaart, of de put staat of is bouwbaar.
static func water_mogelijk(w: Wereld) -> bool:
	return _bron(w) or w.dichtste_gebouw(&"put", w.kampvuur) != null or w.ontgrendeld(&"put")


## Wolkje boven het hoofd ook als hij niet gekozen is: alles behalve tevreden (dat alleen bij de gekozen).
static func zichtbaar(g: StringName) -> bool:
	return g != &"" and g != &"blij"


static func ikoon(g: StringName) -> String:
	return INFO[g]["ikoon"] if INFO.has(g) else ""


static func tekst(g: StringName) -> String:
	return INFO[g]["tekst"] if INFO.has(g) else ""


static func dringend(g: StringName) -> bool:
	return INFO.has(g) and bool(INFO[g]["dringend"])


## Wat de speler eraan kan doen (portret op de pc): de uitleg die het origineel niet gaf.
static func uitleg(w: Wereld, d: Dorpeling, g: StringName) -> String:
	match g:
		&"geraakt":
			return "Breng hem in veiligheid"
		&"honger":
			return "Te lang niets gegeten: verliest gezondheid"
		&"dorst":
			return "Geen water bereikbaar" if w.dichtste_gebouw(&"put", d.tegel()) == null and not _bron(w) else "Kan niet bij het water"
		&"ziek":
			return "Laat hem rusten of slapen"
		&"boos":
			return "Ontevreden: verlaag de prijzen"
		&"somber":
			return "Niet blij: prijzen of honger"
		&"verliefd":
			return "Sticht een gezin in een hut"
		&"blij":
			return "Alles in orde"
	var s := String(g)
	if s.begins_with("wil_"):
		var waar := s.substr(4)
		var winkel: StringName = WINKEL.get(waar, &"")
		var naam: String = WINKEL_NAAM.get(winkel, String(winkel))
		if w.winkels(winkel).is_empty():
			return "Bouw een %s" % naam
		if w.voorraad(winkel) <= 0:
			return "De %s is leeg" % naam
		return "Kan er niet bij"
	return ""


static func _bron(w: Wereld) -> bool:
	for ob in w.objecten:
		if ob["naam"] == "bron":
			return true
	return false
