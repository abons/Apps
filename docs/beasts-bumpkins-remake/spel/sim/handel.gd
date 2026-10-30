class_name Handel
extends RefCounted
## Prijzen, geluk en misdaad (origineel: het economiescherm achter het goudstukken-icoon in de bovenbalk, hint 1-10).
## Getallen in spel.json `handel`. Origineel (STATS-scherm): een schuif per waar van weinig munten (links) naar een
## stapel goud (rechts): eieren, water, brood, melk, cider, kerk (tiende) en belasting; daaronder per misdaad (vloeken,
## diefstal, mishandeling, moord) de straf, van duim omhoog tot duim omlaag. De remake heeft alleen de waren uit
## Wereld.WAREN (brood, melk, ei); water, cider, tiende en belasting komen met put, brouwerij, kerk en belastinginner.
##
## - Prijs per waar (`prijs` [min, max], start economie.prijs_per_stuk): wat de kas krijgt per verkoop (Wereld.klus_af).
## - Geluk per dorpeling 0..1 (Dorpeling.geluk): loopt met `geluk_per_s` naar 1 - prijsdruk (gemiddelde over de waren
##   van (prijs - min) / (max - min), maal `druk_gewicht`). Hint 2-3: hoge prijzen maken ontevreden en ontevreden
##   mensen leven korter (dat laatste doet sim/leven.gd met leven.ongeluk_versnelt). Elke misdaad kost iedereen
##   `misdaad_ongeluk` (hint 13-4: misdaad maakt de dorpelingen ongelukkig tot je er iets aan doet).
## - Misdaad, alleen als de missie `misdaad.aan` heeft (origineel pas in missie 13, met gevangenis en pikenier): elke
##   seconde kans per volwassene onder `drempel` geluk, `kans_per_s` x ernst (ernst = (drempel - geluk) / drempel).
##   Hoe ongelukkiger, hoe zwaarder: moord, mishandeling (schade), diefstal (een waar uit een winkel) of vloeken.

signal misdaad(soort: String, dader: Dorpeling, slachtoffer: Dorpeling)

const SOORTEN := ["vloeken", "diefstal", "mishandeling", "moord"]

var prijzen := {}          ## waar -> goud per verkoop
var misdaden := {}         ## soort -> aantal (origineel statistiek Crimes)
var veroordelingen := 0    ## origineel Convictions; nog altijd 0 (geen gevangenis)
var inkomsten := 0         ## kas uit verkoop (origineel Trade/Income)
var _c: Dictionary = {}
var _t := 0.0
var _start := 3            ## startprijs: economie.prijs_per_stuk (beasts-src VISIT_PRICE)
var rng := RandomNumberGenerator.new()


func _init(w: Wereld) -> void:
	_c = w.spel.get("handel", {})
	rng.seed = 7
	_start = int(w.spel["economie"].get("prijs_per_stuk", 3))
	for waar in Wereld.WAREN:
		prijzen[waar] = _start
	for s in SOORTEN:
		misdaden[s] = 0


func prijs_min() -> int:
	return int(_c.get("prijs", [1, 9])[0])


func prijs_max() -> int:
	return int(_c.get("prijs", [1, 9])[1])


func prijs(waar: String) -> int:
	return int(prijzen.get(waar, _start))


## Zet de prijs (begrensd op [min, max]); geeft de nieuwe prijs.
func zet_prijs(waar: String, p: int) -> int:
	prijzen[waar] = clampi(p, prijs_min(), prijs_max())
	return prijzen[waar]


## Een verkoop: de prijs voor de kas.
func verkoop(waar: String) -> int:
	var p := prijs(waar)
	inkomsten += p
	return p


## 0 (alles op het minimum) .. 1 (alles op het maximum).
func prijsdruk() -> float:
	var span := float(maxi(1, prijs_max() - prijs_min()))
	var som := 0.0
	for waar in prijzen:
		som += float(prijzen[waar] - prijs_min()) / span
	return som / maxf(1.0, float(prijzen.size()))


func geluk_doel() -> float:
	return clampf(1.0 - prijsdruk() * float(_c.get("druk_gewicht", 1.0)), 0.0, 1.0)


## Gemiddeld geluk van het dorp (HUD), 0..1.
func dorp_geluk(w: Wereld) -> float:
	if w.dorpelingen.is_empty():
		return geluk_doel()
	var som := 0.0
	for d in w.dorpelingen:
		som += d.geluk
	return som / float(w.dorpelingen.size())


func misdaad_aan(w: Wereld) -> bool:
	return bool(w.missie.get("misdaad", {}).get("aan", false))


func totaal_misdaden() -> int:
	var n := 0
	for s in misdaden:
		n += int(misdaden[s])
	return n


## Startwaarde: iedereen begint op het doel van de startprijzen.
func start(w: Wereld) -> void:
	for d in w.dorpelingen:
		d.geluk = geluk_doel()


func tik(w: Wereld, dt: float) -> void:
	var doel := geluk_doel()
	var stap := float(_c.get("geluk_per_s", 0.01)) * dt
	for d in w.dorpelingen:
		d.geluk = move_toward(d.geluk, doel, stap)
	if not misdaad_aan(w):
		return
	_t += dt
	if _t < 1.0:
		return
	_t -= 1.0
	var m: Dictionary = _c.get("misdaad", {})
	var drempel := float(m.get("drempel", 0.5))
	for d: Dorpeling in w.dorpelingen.duplicate():
		if not d.volwassen() or d.slaapt or d.binnen or d.geluk >= drempel or not w.dorpelingen.has(d):
			continue
		var ernst: float = (drempel - d.geluk) / drempel
		if rng.randf() < float(m.get("kans_per_s", 0.01)) * ernst:
			pleeg(w, d, ernst)


## Een misdaad door `dader`; `ernst` 0..1 kiest hoe zwaar (moord alleen bij grote ernst). Zonder slachtoffer in de buurt
## wordt het vloeken, zonder winkelvoorraad ook. Geeft de soort.
func pleeg(w: Wereld, dader: Dorpeling, ernst: float) -> String:
	var m: Dictionary = _c.get("misdaad", {})
	var r := rng.randf()
	var soort := "vloeken"
	if r < ernst * float(m.get("moord_deel", 0.15)):
		soort = "moord"
	elif r < ernst * float(m.get("mishandeling_deel", 0.5)):
		soort = "mishandeling"
	elif r < float(m.get("diefstal_deel", 0.7)):
		soort = "diefstal"
	var slachtoffer: Dorpeling = null
	if soort == "moord" or soort == "mishandeling":
		slachtoffer = _slachtoffer(w, dader, float(m.get("straal", 6.0)))
		if slachtoffer == null:
			soort = "vloeken"
	if soort == "diefstal":
		var winkel: Plan = null
		for s in Wereld.WINKELS:
			for p in w.winkels(s):
				if p.voorraad > 0:
					winkel = p
					break
			if winkel != null:
				break
		if winkel == null:
			soort = "vloeken"
		else:
			winkel.voorraad -= 1
	misdaden[soort] = int(misdaden[soort]) + 1
	var ongeluk := float(_c.get("misdaad_ongeluk", 0.05))
	for d in w.dorpelingen:
		d.geluk = maxf(0.0, d.geluk - ongeluk)
	misdaad.emit(soort, dader, slachtoffer)
	if soort == "mishandeling":
		slachtoffer.raak(w, float(m.get("schade", 8.0)), "mishandeling")
	elif soort == "moord":
		slachtoffer.sterf(w, "moord")
	return soort


func _slachtoffer(w: Wereld, dader: Dorpeling, straal: float) -> Dorpeling:
	var beste: Dorpeling = null
	var bd := straal * straal
	for d in w.dorpelingen:
		if d == dader or d.binnen:
			continue
		var af := d.pos.distance_squared_to(dader.pos)
		if af <= bd:
			bd = af
			beste = d
	return beste
