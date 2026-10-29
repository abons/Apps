class_name Dorpeling
extends RefCounted
## Dorpeling in de sim: positie in tegels (continu; tegel (x,y) = [x,x+1)), route, bevel, zwerven.
## Kent geen Node: de view spiegelt hem (view/bumpkin.gd volgt `pos` en `snelheid_mps`).

var id := 0
var naam := ""
var sex_ruw := 0          ## zoals in map1.json: 1 man, 2 vrouw, 13/14 onbekend (vermoedelijk kind, niet geverifieerd)
var geslacht := "onbekend"
var leeftijd := "volwassen"   ## volwassen | kind | oud
var rol := ""                ## "" gewone dorpeling, "bouwer" (bouwersgilde: bouwt sneller, vecht niet)
var gilde: Plan = null       ## gereedschapsloods waar hij zich laat inschrijven (bevel "gilde")
var pos := Vector2.ZERO
var vorige := Vector2.ZERO    ## positie bij de vorige tik, voor interpolatie in de view
var route: Array[Vector2] = []   ## te volgen punten (tegelmiddens, in tegelcoördinaten), recht getrokken door Router.glad
var bevel := {}               ## {} (geen) of {"soort": "loop"|"vecht"|"werk", "doel": Vector2i}
var anker := Vector2i.ZERO    ## zwerfmiddelpunt: het kampvuur, na een bevel de plek waar hij bleef staan
var wacht := 2.0
var werk_plan: Plan = null   ## bouwplek waar hij heen loopt en aan werkt
var doel_koe: Vee = null     ## koe die hij gaat claimen (bevel "claim")
var wieg: Dictionary = {}     ## gezin dat hij met een partner in een hut sticht (Wereld._gezin), {} = geen
var binnen := false          ## in de hut (onzichtbaar, staat stil op de deurtegel)
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


func volwassen() -> bool:
	return leeftijd == "volwassen"


## Lopen kan iedereen; vechten, werken, koeien claimen en een gezin stichten ("huis") alleen volwassenen.
func kan_bevel(soort: String) -> bool:
	if soort == "vecht" and rol == "bouwer":
		return false
	return soort == "loop" or volwassen()


## Vrij voor een gezin: volwassen, uitgerust, zonder bevel, bouwklus, koe of wieg, en geen baby op de arm.
func vrij_voor_gezin() -> bool:
	return volwassen() and rust <= 0.0 and ledig() and draagt == ""


## Niets omhanden: geen bevel, route, bouwklus, koe, wieg, klus of baby en niet binnen.
func ledig() -> bool:
	return bevel.is_empty() and route.is_empty() and werk_plan == null and doel_koe == null and wieg.is_empty() \
		and baby <= 0.0 and not binnen and bezig <= 0.0 and klus == null and klus_tegel.x < 0 and melk_koe == null and raap_kip == null and gilde == null


func tegel() -> Vector2i:
	return Vector2i(int(floor(pos.x)), int(floor(pos.y)))


func zet_tegel(t: Vector2i) -> void:
	pos = Vector2(t) + Vector2(0.5, 0.5)
	vorige = pos


func geef_bevel(w: Wereld, soort: String, doel: Vector2i) -> bool:
	if not kan_bevel(soort):
		return false
	if soort != "gilde":
		gilde = null
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
	if doel_koe != null:          # een nieuw bevel laat de koe die hij ging claimen weer vrij
		doel_koe.vast = false
		doel_koe = null
	var r := Router.route(w.raster, tegel(), doel)
	if r.is_empty() and tegel() != doel:
		return false
	route = Router.glad(w.raster, pos, r)
	bevel = {"soort": soort, "doel": doel}
	if r.is_empty():
		binnen = soort == "huis"
		if soort == "gilde":
			w.gilde_aangekomen(self)
		if soort in ["lever", "koop", "oogst", "melk", "raap"]:
			w.klus_aangekomen(self, soort)
		_klaar()
	return true


func _klaar() -> void:
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
		if bevel.is_empty() and baby <= 0.0:    # met de baby op de arm blijft ze staan
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
