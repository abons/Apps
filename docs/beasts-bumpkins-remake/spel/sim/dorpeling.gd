class_name Dorpeling
extends RefCounted
## Dorpeling in de sim: positie in tegels (continu; tegel (x,y) = [x,x+1)), route, bevel, zwerven.
## Kent geen Node: de view spiegelt hem (view/bumpkin.gd volgt `pos` en `snelheid_mps`).

var id := 0
var naam := ""
var sex_ruw := 0          ## zoals in map1.json: 1 man, 2 vrouw, 13/14 onbekend (vermoedelijk kind, niet geverifieerd)
var geslacht := "onbekend"
var leeftijd := "volwassen"   ## volwassen | kind | oud
var rol := ""                ## "" gewone dorpeling, "bouwer" (bouwersgilde: bouwt sneller, vecht niet), "voetsoldaat"
                             ## (voetvolkgilde, missie 3: zwaard, boert en bouwt niet, sticht geen gezin)
var gilde: Plan = null       ## gilde waar hij heen loopt om zich in te schrijven (bevel "gilde", Wereld.GILDEN)
var lid: Plan = null         ## gilde waar hij lid van is (telt voor gilde_max_leden); null bij een rol uit de kaart zonder gilde
var dorst := 0.0             ## s sinds hij water dronk (put, missie 3); Wereld._kies_klus stuurt hem boven economie.dorst_s
var pos := Vector2.ZERO
var vorige := Vector2.ZERO    ## positie bij de vorige tik, voor interpolatie in de view
var route: Array[Vector2] = []   ## te volgen punten (tegelmiddens, in tegelcoördinaten), recht getrokken door Router.glad
var bevel := {}               ## {} (geen) of {"soort": "loop"|"vecht"|"werk", "doel": Vector2i}
var anker := Vector2i.ZERO    ## zwerfmiddelpunt: het kampvuur, na een bevel de plek waar hij bleef staan
var wacht := 2.0
var werk_plan: Plan = null   ## bouwplek waar hij heen loopt en aan werkt
var werk_punt := Vector2(-1, -1)   ## zijn werkplek bij dat plan (tegels, continu; Wereld.werk_plekken), -1 = geen
var werk_soort := &""        ## wat hij daar doet: bouwen (hamer), zagen (bij de zaagbok), houweel (bij de steenhoop)
var werk_kijk := Vector2.INF  ## waar hij naar kijkt tijdens het werk (tegels), INF = geen
var doel_koe: Vee = null     ## koe die hij gaat claimen (bevel "claim")
var wieg: Dictionary = {}     ## gezin dat hij met een partner in een hut sticht (Wereld._gezin), {} = geen
var binnen := false          ## in de hut (onzichtbaar, staat stil op de deurtegel)
var slaapt := false          ## 's nachts in zijn bed (binnen in `slaapplek`)
var slaapplek: Plan = null   ## de hut waar hij vannacht slaapt (2 bedden per hut)
var bij_vuur := false        ## geen bed: 's nachts liggen bij het kampvuur (slaapt = ligt daar al)
var rust := 0.0              ## s tot hij weer aan een gezin begint (ouder of net volwassen)
var baby := 0.0              ## s dat de moeder de baby nog draagt; daarna staat het kind er
var groeit := 0.0            ## s tot het kind volwassen is
var trek := {}               ## waar -> s sinds hij die voor het laatst kocht (beasts-src need); kinderen kopen ook
var draagt := ""             ## "graan" naar de molen, "melk" naar de melkerij, "ei" naar het kippenhok, "" = lege handen
var koopt := ""              ## waar hij voor naar de winkel loopt
var melk_koe: Vee = null     ## koe die hij gaat melken
var raap_kip: Kip = null     ## kip waarvan hij het ei gaat rapen
var klus: Object = null      ## Plan (molen) of null; bij "oogst" de akker
var klus_tegel := Vector2i(-1, -1)   ## akkertegel bij "oogst"
var bezig := 0.0             ## s dat hij nog staat te oogsten of aan de toonbank staat
var bouwt := false           ## in deze tik aan het bouwen (view: hamerlus)
var snelheid_mps := 0.0       ## werkelijke loopsnelheid in deze tik, m/s incl. looptempo (0 = stil)
var doel_wolf: Wolf = null    ## wolf waar hij stenen naar gooit (vechtbevel of zelf verdedigen, sim/wolf.gd vecht_tik)
var worp_t := -1.0            ## s in de huidige worp, -1 = geen worp bezig
var vecht_kijk := 0.0         ## s tot hij zijn route naar de wolf weer bijwerkt
# ---- leven (sim/leven.gd): gezondheid, dood, ouderdom, vluchten. Getallen in spel.json `leven`.
var gezondheid := 24.0        ## hp; 0 = dood (Leven.sterf). Wordt bij het laden gezet op leven.gezondheid
var gezondheid_max := 24.0
var geraakt_s := 99.0         ## s sinds de laatste schade (herstel begint na leven.herstel_na_s; view: hp-balkje)
var ouderdom_s := 0.0         ## s als volwassene (of oudere); kinderen 0. Loopt sneller als `geluk` laag is
var levensduur_s := 0.0       ## sterft van ouderdom als ouderdom_s dit haalt; oud vanaf leven.oud_vanaf x dit
## Geluk 0..1 (haak voor de economie/prijzen, niet hier ingevuld): 1 = tevreden. Lager laat ouderdom_s sneller lopen
## (origineel hint 2-3: "hoge prijzen maken ontevreden, en ontevreden mensen leven korter"), zie leven.ongeluk_versnelt.
var geluk := 1.0
## Stilstaan (besluit gebruiker 2026-10-31, origineel: de hand-knop): blijft staan waar hij is, geen zelfstandige klussen,
## niet zwerven, niet slapen gaan, niet zelf vechten; alleen vluchten voor een wolf. Een nieuw bevel heft het op.
var stil := false


## Schade (wolfbeet, later zwaard of pijl): gezondheid omlaag; bij 0 sterft hij (Leven.sterf: uit alle lijsten,
## signaal Wereld.dorpeling_dood). `oorzaak` gaat mee in het signaal ("wolf", "ouderdom", ...).
func raak(w: Wereld, schade: float, oorzaak := "") -> void:
	Leven.raak(w, self, schade, oorzaak)


## Meteen dood (ouderdom, of een missie die iemand weghaalt). Zie Leven.sterf.
func sterf(w: Wereld, oorzaak := "") -> void:
	Leven.sterf(w, self, oorzaak)


func leeft() -> bool:
	return gezondheid > 0.0


func oud() -> bool:
	return leeftijd == "oud"


func volwassen() -> bool:
	return leeftijd == "volwassen"


## Lopen, slapen en vluchten kan iedereen; vechten, werken, koeien claimen en een gezin stichten ("huis") alleen volwassenen.
func kan_bevel(soort: String) -> bool:
	if soort == "werk" and not kan_bouwen():
		return false
	if soort == "vecht" and rol == "bouwer":
		return false
	if rol == "voetsoldaat" and soort in ["werk", "claim", "huis", "oogst", "melk", "raap", "lever"]:
		return false                 # origineel: soldaten boeren en bouwen niet (gameplay.md "Gilden en training")
	if soort == "koop":
		return true                  # kinderen kopen ook (origineel, gebruiker 2026-10-30); drinken bij de plas is gratis
	return soort == "loop" or soort == "slaap" or soort == "vuur" or soort == "vlucht" or volwassen()


## Bouwen: alleen volwassen mannen en bouwers (besluit gebruiker 2026-10-31, origineel hamerpunt 0x440b3c: man of
## bouwer; de vrouw heeft geen hamerknop). Voetsoldaten bouwen niet.
func kan_bouwen() -> bool:
	return volwassen() and rol != "voetsoldaat" and (geslacht == "man" or rol == "bouwer")


## Vrij voor een gezin: volwassen, uitgerust, zonder bevel, bouwklus, koe of wieg, en geen baby op de arm.
func vrij_voor_gezin() -> bool:
	return volwassen() and rust <= 0.0 and ledig() and draagt == "" and rol != "voetsoldaat"


## Niets omhanden: geen bevel, route, bouwklus, koe, wieg, klus of baby en niet binnen.
func ledig() -> bool:
	return not stil and bevel.is_empty() and route.is_empty() and werk_plan == null and doel_koe == null and wieg.is_empty() \
		and baby <= 0.0 and not binnen and bezig <= 0.0 and klus == null and klus_tegel.x < 0 and melk_koe == null and raap_kip == null and gilde == null and slaapplek == null and not slaapt and doel_wolf == null


func tegel() -> Vector2i:
	return Vector2i(int(floor(pos.x)), int(floor(pos.y)))


func zet_tegel(t: Vector2i) -> void:
	pos = Vector2(t) + Vector2(0.5, 0.5)
	vorige = pos


func geef_bevel(w: Wereld, soort: String, doel: Vector2i) -> bool:
	if not kan_bevel(soort):
		return false
	if soort != "vlucht":             # vluchten houdt stilstaan aan, elk ander bevel heft het op
		stil = false
	if soort != "gilde":
		gilde = null
	if soort != "slaap" and soort != "vuur":          # een bevel van de speler wekt hem
		slaapt = false
		slaapplek = null
		bij_vuur = false
	if soort != "huis" and not wieg.is_empty():   # een bevel van de speler breekt het gezin af
		w.annuleer_wieg(wieg)
	if not soort in ["lever", "koop", "oogst", "melk", "raap"]:
		if klus_tegel.x >= 0:
			w.laat_akker_los(klus_tegel)
		if melk_koe != null:
			melk_koe.vast = false
			melk_koe.gemolken = false
			melk_koe = null
		if raap_kip != null:
			raap_kip.vast = false
			raap_kip = null
		koopt = ""
		klus = null
		klus_tegel = Vector2i(-1, -1)
		bezig = 0.0
	binnen = false
	werk_plan = null
	werk_punt = Vector2(-1, -1)
	werk_soort = &""
	werk_kijk = Vector2.INF
	doel_wolf = null             # elk nieuw bevel stopt het gooien; Wereld.geef_bevel("vecht") zet hem daarna weer
	worp_t = -1.0
	if doel_koe != null:          # een nieuw bevel laat de koe die hij ging claimen weer vrij
		doel_koe.vast = false
		doel_koe = null
	var r := Router.route(w.raster, tegel(), doel)
	if r.is_empty() and tegel() != doel:
		return false
	route = Router.glad(w.raster, pos, r)
	bevel = {"soort": soort, "doel": doel}
	if r.is_empty():
		binnen = soort == "huis" or soort == "slaap"
		slaapt = soort == "slaap" or soort == "vuur"
		if soort == "gilde":
			w.gilde_aangekomen(self)
		if soort in ["lever", "koop", "oogst", "melk", "raap"]:
			w.klus_aangekomen(self, soort)
		_klaar()
	return true


## Bevel af. Alleen na een loop- of vechtbevel (of claimen, gilde) van de speler blijft hij in de buurt van waar hij stond; na een
## eigen klus (oogsten, melken, kopen, slapen, ...) zwerft hij terug naar zijn anker in het dorp (besluit gebruiker:
## zonder opdracht niet te ver van het dorp).
func _klaar() -> void:
	if bevel.get("soort", "") in ["loop", "vecht", "claim", "gilde"]:
		anker = tegel()
	bevel = {}
	wacht = 1.0


func tick(w: Wereld, dt: float) -> void:
	if not binnen and not w.raster.loopbaar_v(tegel()):   # vangnet: nooit vast in een muur of een dichte poort
		var t := w.dichtstbij_loopbaar(tegel())
		if t.x >= 0:
			zet_tegel(t)
			route.clear()
	vorige = pos
	snelheid_mps = 0.0
	bouwt = false
	if binnen:
		return
	if doel_wolf != null and Wolf.vecht_tik(w, self, dt):   # stenen gooien; false = erheen lopen (hieronder)
		return
	if bezig > 0.0:
		bezig = maxf(0.0, bezig - dt)
		bouwt = klus_tegel.x >= 0 or melk_koe != null or raap_kip != null   # oogsten, melken, rapen: de werkclip
		if bezig <= 0.0:
			w.klus_af(self)
		return
	if route.is_empty():
		if werk_plan != null and not werk_plan.klaar:
			bouwt = true
			var f: float = float(w.spel["bouwer"]["tempo"]) if rol == "bouwer" else 1.0
			werk_plan.voortgang = minf(1.0, werk_plan.voortgang + dt * f / werk_plan.bouwtijd_s)
			return
		if bevel.is_empty() and baby <= 0.0 and not slaapt and not stil:    # met de baby op de arm blijft ze staan; wie ligt, ligt
			_zwerf(w, dt)
		return
	var rest := dt
	var teller := 0
	while rest > 1e-6 and not route.is_empty() and teller < 8:
		teller += 1
		var t := tegel()
		var f := w.raster.factor(t.x, t.y)
		if f <= 0.0:
			f = 1.0
		var eff: float = w.loop_mps * w.looptempo * f   # m/s
		if bevel.get("soort", "") == "vlucht":          # wegrennen voor een wolf (Leven._vlucht): rennen
			eff *= float(w.spel["leven"]["vlucht_tempo"])
		var v := eff / w.tegel_m                     # tegels per seconde
		snelheid_mps = eff
		var doel := route[0]
		var d := doel - pos
		var afstand := d.length()
		var stap := v * rest
		if afstand <= stap:
			pos = doel
			route.pop_front()
			rest -= afstand / v
		else:
			pos += d / afstand * stap
			rest = 0.0
	if route.is_empty():
		if doel_koe != null:
			w.claim_aangekomen(self)
		if bevel.get("soort", "") == "huis":
			binnen = true
		elif bevel.get("soort", "") == "slaap":
			binnen = true
			slaapt = true
		elif bevel.get("soort", "") == "vuur":
			slaapt = true
		elif bevel.get("soort", "") == "gilde":
			w.gilde_aangekomen(self)
		elif bevel.get("soort", "") in ["lever", "koop", "oogst", "melk", "raap"]:
			w.klus_aangekomen(self, bevel["soort"])
		_klaar()


func _zwerf(w: Wereld, dt: float) -> void:
	wacht -= dt
	if wacht > 0.0:
		return
	var lo: float = w.spel["zwerf_wacht"][0]
	var hi: float = w.spel["zwerf_wacht"][1]
	wacht = w.rng.randf_range(lo, hi)
	var straal: int = int(w.spel["zwerf_straal"])
	for _i in 8:
		var t := anker + Vector2i(w.rng.randi_range(-straal, straal), w.rng.randi_range(-straal, straal))
		if t == tegel() or not w.raster.loopbaar_v(t) or w.bereik[w.raster.idx(t.x, t.y)] == 0:
			continue
		var r := Router.route(w.raster, tegel(), t)
		if not r.is_empty():
			route = Router.glad(w.raster, pos, r)
			return
