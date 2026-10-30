class_name Beloningen
extends RefCounted
## Kas-acties uit het missiebestand (origineel actie 0x16 "kas erbij", ../missies.md "Hints en briefing"). Per missie in
## spel.json `missies.<nr>.beloningen`: [{id, trigger, na, kas}], dezelfde triggervorm als data/hints.json:
##   start                  meteen bij de eerste tik
##   timer {tikken}         originele tikken (2880 = 1 seizoen, omgerekend met seizoen_s) vanaf de start, of, met `na`,
##                          vanaf het moment dat die regel vuurde
##   kas_boven {bedrag}     kas groter dan bedrag
## Elke regel vuurt een keer: kas erbij en signaal Wereld.kas_beloning. Tijden in Wereld.beloningen (id -> tijd_s).
## M2: vier regels timer 6480 -> +1000. Of die tegelijk of na elkaar vuren zegt de data niet; spel.json zet ze na elkaar.

const SEIZOEN_TIKKEN := 2880.0


static func tik(w: Wereld) -> void:
	var regels: Array = w.missie.get("beloningen", [])
	if regels.is_empty():
		return
	if w.beloning_start_s < 0.0:
		w.beloning_start_s = w.tijd_s
	var tik_s := float(w.spel["seizoen_s"]) / SEIZOEN_TIKKEN
	for r in regels:
		var id := String(r["id"])
		if w.beloningen.has(id):
			continue
		var vanaf := w.beloning_start_s
		if r.has("na"):
			if not w.beloningen.has(String(r["na"])):
				continue
			vanaf = float(w.beloningen[String(r["na"])])
		if not _waar(w, r.get("trigger", {}), vanaf, tik_s):
			continue
		w.beloningen[id] = w.tijd_s
		var kas := int(r.get("kas", 0))
		w.kas += kas
		w.kas_beloning.emit(id, kas)


static func _waar(w: Wereld, t: Dictionary, vanaf: float, tik_s: float) -> bool:
	match String(t.get("type", "")):
		"start":
			return true
		"timer":
			return w.tijd_s - vanaf >= float(t["tikken"]) * tik_s - 1e-6
		"kas_boven":
			return w.kas > int(t["bedrag"])
	return false
