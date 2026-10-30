class_name Leven
extends RefCounted
## Leven en dood van dorpelingen: gezondheid, schade, sterven, herstel, ouderdom (pensioen) en vluchten voor wolven.
## Geen Node, alleen statische functies op Wereld + Dorpeling (zoals Wolf en Voorwerpen). Getallen in spel.json `leven`.
##
## Interface voor andere systemen (wolf, later soldaten/zwaarden/pijlen):
##   d.raak(w, schade, oorzaak)   gezondheid omlaag (Dorpeling.gezondheid, hp); bij 0 -> sterf. Signaal dorpeling_geraakt.
##   d.sterf(w, oorzaak)          meteen dood: uit Wereld.dorpelingen en alles wat naar hem wijst. Signaal dorpeling_dood.
##   d.leeft()                    gezondheid > 0
## Oorzaken nu: "wolf", "ouderdom". De view (wereld_view.gd) laat een dode omvallen en na leven.lijk_s verdwijnen.
##
## Levensloop (gebruiker 2026-10-30: baby > kind > volwassene > oudere > dood). Baby en kind staan in Wereld._gezin.
## Volwassen: ouderdom_s loopt; vanaf oud_vanaf x levensduur_s gaat hij met pensioen (leeftijd "oud": werkt, vecht en
## sticht geen gezin meer, alleen kopen, slapen en zwerven; signaal met_pensioen, view wisselt naar het oudere-model);
## bij levensduur_s sterft hij van ouderdom. Origineel (onderzoek.md, medium): baby, kind, werkende volwassene,
## gepensioneerde (old man / old woman), dood; een volwassene leeft 4-5 spel-jaren, afhankelijk van eten en water.
## Geluk (Dorpeling.geluk, 0..1) is een haak: laag geluk laat de ouderdom sneller lopen (hint 2-3); de prijzen vullen het in.

const OORZAAK_WOLF := "wolf"
const OORZAAK_OUDERDOM := "ouderdom"


static func cfg(w: Wereld) -> Dictionary:
	return w.spel["leven"]


## Elke tik vanuit Wereld.tik.
static func tik_alle(w: Wereld, dt: float) -> void:
	var c := cfg(w)
	for d in w.dorpelingen.duplicate():
		if d.levensduur_s <= 0.0:
			_begin(w, d)
		d.geraakt_s += dt
		if d.geraakt_s >= float(c["herstel_na_s"]) and d.gezondheid < d.gezondheid_max:
			var f := float(c["herstel_slaap"]) if d.slaapt else 1.0
			d.gezondheid = minf(d.gezondheid_max, d.gezondheid + float(c["herstel_per_s"]) * f * dt)
		if d.leeftijd == "kind":
			continue
		d.ouderdom_s += dt * (1.0 + (1.0 - clampf(d.geluk, 0.0, 1.0)) * float(c["ongeluk_versnelt"]))
		if d.ouderdom_s >= d.levensduur_s:
			sterf(w, d, OORZAAK_OUDERDOM)
			continue
		if d.volwassen() and d.ouderdom_s >= float(c["oud_vanaf"]) * d.levensduur_s \
				and d.wieg.is_empty() and d.baby <= 0.0 and not d.binnen:
			_met_pensioen(w, d)
	_vlucht_t(w, dt)


## Eerste tik: gezondheid uit de data, levensduur per dorpeling (hash op id: zelfde spel, zelfde levens), en de
## startdorpelingen (volwassen of oud) een verdeelde beginleeftijd. Kinderen beginnen op 0 (ouderdom telt pas als
## volwassene).
static func _begin(w: Wereld, d: Dorpeling) -> void:
	var c := cfg(w)
	d.gezondheid_max = float(c["gezondheid"])
	d.gezondheid = d.gezondheid_max
	var duur: Array = c["levensduur_s"]
	d.levensduur_s = lerpf(float(duur[0]), float(duur[1]), w._hash2(d.id * 11 + 3, 57))
	if d.leeftijd == "kind":
		d.ouderdom_s = 0.0
		return
	var st: Array = c["start_ouderdom"]
	var f := lerpf(float(st[0]), float(st[1]), w._hash2(d.id * 7 + 5, 23))
	if d.leeftijd == "oud":
		f = maxf(f, float(c["oud_vanaf"]))
	d.ouderdom_s = f * d.levensduur_s


## Volwassene wordt oudere: geen bouwer of gildelid meer, laat zijn bouwklus en gevecht los.
static func _met_pensioen(w: Wereld, d: Dorpeling) -> void:
	d.leeftijd = "oud"
	d.rol = ""
	d.gilde = null
	d.lid = null
	d.doel_wolf = null
	d.worp_t = -1.0
	if d.werk_plan != null:
		d.werk_plan = null
		d.route.clear()
		d.bevel = {}
	if d.doel_koe != null:
		d.doel_koe.vast = false
		d.doel_koe = null
		d.route.clear()
		d.bevel = {}
	w.pensioenen += 1
	w.met_pensioen.emit(d)


static func raak(w: Wereld, d: Dorpeling, schade: float, oorzaak := "") -> void:
	if not d.leeft() or not d in w.dorpelingen:
		return
	d.gezondheid = maxf(0.0, d.gezondheid - schade)
	d.geraakt_s = 0.0
	if d.slaapt and not d.binnen:      # gebeten bij het kampvuur: wakker
		d.slaapt = false
		d.bij_vuur = false
	w.dorpeling_geraakt.emit(d, oorzaak)
	if d.gezondheid <= 0.0:
		sterf(w, d, oorzaak)


## Dood: uit Wereld.dorpelingen en uit alles wat naar hem wijst (wieg, akker, koe, kip, voorwerp). Wolven en
## voorwerpen zien het zelf (prooi/drager niet meer in de lijst); een gedragen voorwerp valt hier meteen.
static func sterf(w: Wereld, d: Dorpeling, oorzaak := "") -> void:
	if not d in w.dorpelingen:
		return
	d.gezondheid = 0.0
	if not d.wieg.is_empty():
		w.annuleer_wieg(d.wieg)
	if d.klus_tegel.x >= 0:
		w.laat_akker_los(d.klus_tegel)
	if d.melk_koe != null:
		d.melk_koe.vast = false
		d.melk_koe.gemolken = false
	if d.raap_kip != null:
		d.raap_kip.vast = false
	if d.doel_koe != null:
		d.doel_koe.vast = false
	d.melk_koe = null
	d.raap_kip = null
	d.doel_koe = null
	d.klus = null
	d.klus_tegel = Vector2i(-1, -1)
	d.werk_plan = null
	d.slaapplek = null
	d.gilde = null
	d.lid = null
	d.doel_wolf = null
	d.route.clear()
	d.bevel = {}
	d.binnen = false
	d.slaapt = false
	d.baby = 0.0
	w.dorpelingen.erase(d)
	for ob in Voorwerpen.alle(w):
		if int(ob["drager"]) == d.id:
			Voorwerpen.laat_vallen(w, ob)
	w.doden += 1
	w.dorpeling_dood.emit(d, oorzaak)


# ---------------------------------------------------------------- vluchten (beasts-src World.flee/scare)

static var _vlucht_klok := 0.0


static func _vlucht_t(w: Wereld, dt: float) -> void:
	_vlucht_klok += dt
	if _vlucht_klok < float(cfg(w)["vlucht_kijk_s"]):
		return
	_vlucht_klok = 0.0
	if w.wolven.is_empty():
		return
	for d in w.dorpelingen:
		if vlucht_soort(w, d):
			vlucht(w, d)


## Wie wegrent voor een wolf: kinderen (besluit gebruiker 2026-10-30), ouderen en de bouwer (vechten niet), en iedereen
## met weinig gezondheid over. Niet wie binnen is of al aan het vluchten is.
static func vlucht_soort(w: Wereld, d: Dorpeling) -> bool:
	if d.binnen or (d.bevel.get("soort", "") == "vlucht" and not d.route.is_empty()):
		return false
	if d.leeftijd == "kind" or d.leeftijd == "oud" or d.rol == "bouwer":
		return true
	return d.gezondheid < float(cfg(w)["vlucht_onder"]) * d.gezondheid_max


## De dichtste levende wolf binnen vlucht_straal, of null.
static func dreiging(w: Wereld, d: Dorpeling) -> Wolf:
	var beste: Wolf = null
	var bd := float(cfg(w)["vlucht_straal"])
	for wf in w.wolven:
		var af := wf.pos.distance_to(d.pos)
		if wf.leeft() and af < bd:
			bd = af
			beste = wf
	return beste


## Rent weg als er een wolf dichtbij is: naar een bereikbare tegel binnen vlucht_ruimte die vlucht_winst verder van de
## wolf ligt dan hij nu staat, en daarvan de tegel die het minst ver is plus het dichtst bij het kampvuur (naar huis).
## Geeft true als hij is gaan rennen.
static func vlucht(w: Wereld, d: Dorpeling) -> bool:
	var wf := dreiging(w, d)
	if wf == null:
		return false
	var c := cfg(w)
	var veilig := d.pos.distance_to(wf.pos) + float(c["vlucht_winst"])
	var ruimte := int(c["vlucht_ruimte"])
	var hier := d.tegel()
	var beste := Vector2i(-1, -1)
	var bs := INF
	for dy in range(-ruimte, ruimte + 1):
		for dx in range(-ruimte, ruimte + 1):
			var t := hier + Vector2i(dx, dy)
			if t == hier or not w.raster.in_kaart(t.x, t.y) or not w.raster.loopbaar_v(t) \
					or w.bereik[w.raster.idx(t.x, t.y)] == 0:
				continue
			var m := Vector2(t) + Vector2(0.5, 0.5)
			if m.distance_to(wf.pos) < veilig:
				continue
			var s := m.distance_to(d.pos) + 0.5 * m.distance_to(Vector2(w.kampvuur) + Vector2(0.5, 0.5))
			if s < bs:
				bs = s
				beste = t
	if beste.x < 0:
		return false
	return d.geef_bevel(w, "vlucht", beste)
