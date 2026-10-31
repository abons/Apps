class_name Hints
extends RefCounted
## Briefing en hints per missie uit data/hints.json (origineel: MISTEXT0.BOX + conditie-records in Mn.MIS, zie
## ../missies.md "Hints"). Geen Node: `controleer()` na elke sim-stap (main.gd, tests). Elke hint vuurt een keer;
## wat tegelijk waar wordt, komt in volgorde van het bestand.

const PAD := "res://data/hints.json"

signal hint_getoond(hint: Dictionary)      ## {id, tekst, open, bron}

var w: Wereld
var briefing: Dictionary = {}              ## {titel, tekst, bron}; leeg als de missie er geen heeft
var hints: Array = []                      ## alle hints van de missie, ook die met wacht_op of type geen
var getoond: Array[String] = []            ## ids in de volgorde waarin ze vuurden
var _start_s := 0.0
var _tik_s := 0.09375                      ## s per originele tik: seizoen_s / seizoen_tikken
var _opgeraapt := {}                       ## klasse -> true zodra een voorwerp van die klasse is opgeraapt


func bouw(wereld: Wereld) -> Hints:
	w = wereld
	_start_s = w.tijd_s
	var d = Gegevens.lees(PAD)
	if d is Dictionary:
		var m: Dictionary = d.get("missies", {}).get(str(w.missie_nr), {})
		briefing = m.get("briefing", {})
		hints = m.get("hints", [])
		_tik_s = float(w.spel["seizoen_s"]) / float(d.get("seizoen_tikken", 2880))
	# een methode, geen lambda: een lambda houdt deze Hints vast en Hints de Wereld, zodat de Wereld na het herladen van
	# de scène (startmenu, pauzemenu) nooit vrijkwam
	w.voorwerp_opgeraapt.connect(_bij_opgeraapt)
	return self


func _bij_opgeraapt(ob: Dictionary, _d: Dorpeling) -> void:
	_opgeraapt[int(ob["cls"])] = true


## Vuurt elke hint waarvan de trigger nu waar is (en waarvan de `na`-hint al getoond is). Geeft de gevuurde ids.
func controleer() -> Array[String]:
	var nieuw: Array[String] = []
	for h in hints:
		var id: String = h["id"]
		if id in getoond or h.has("wacht_op"):
			continue
		if h.has("na") and not String(h["na"]) in getoond:
			continue
		if not _waar(h.get("trigger", {})):
			continue
		getoond.append(id)
		nieuw.append(id)
		hint_getoond.emit({"id": id, "tekst": h["tekst"], "open": bool(h.get("open", false)), "bron": h.get("bron", "")})
	return nieuw


func sinds_start_s() -> float:
	return w.tijd_s - _start_s


func _waar(t: Dictionary) -> bool:
	match String(t.get("type", "geen")):
		"start":
			return true
		"timer":
			return sinds_start_s() >= float(t["tikken"]) * _tik_s
		"aantal":
			return aantal(String(t["wat"])) > int(t.get("meer_dan", 0))
		"kas_boven":
			return w.kas > int(t["bedrag"])
		"voorwerp":
			return _opgeraapt.has(int(t["klasse"]))
		"aanraken":       # missie 4 (hint 4-1): een dorpeling staat bij het object, en (tenzij_voorwerp) de sleutel is nog niet gevonden
			if t.has("tenzij_voorwerp") and w.opgeraapt.has(int(t["tenzij_voorwerp"])):
				return false
			return _bij_object(String(t["object"]), float(t.get("straal", 1.6)))
	return false


func _bij_object(naam: String, straal: float) -> bool:
	for ob in w.objecten:
		if ob["naam"] != naam:
			continue
		var m := Vector2(ob["x"], ob["y"]) + Vector2(0.5, 0.5)
		for d in w.dorpelingen:
			if not d.binnen and d.pos.distance_to(m) <= straal:
				return true
	return false


## kippen, koeien (eigen), dorpelingen, of een gebouwsoort (afgebouwde plannen).
func aantal(wat: String) -> int:
	match wat:
		"kippen":
			return w.kippen.size()
		"koeien":
			return w.eigen_koeien()
		"dorpelingen":
			return w.dorpelingen.size()
	var n := 0
	for p in w.plannen:
		if p.klaar and String(p.soort) == wat:
			n += 1
	return n
