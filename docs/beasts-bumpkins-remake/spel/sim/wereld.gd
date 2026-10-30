class_name Wereld
extends RefCounted
## Wereldstaat van de sim: raster, objecten, dorpelingen, klok, seizoen, weer. Geen Node, geen render.
## `vooruit(dt)` verzamelt tijd en tikt op vaste `sim_hz`; de view interpoleert met `alpha()`.

const SEIZOENEN := ["lente", "zomer", "herfst", "winter"]
## Visuele waarden per seizoen (lente, zomer, herfst, winter); worden tegen het einde zacht naar het volgende geblend.
const SNEEUW := [0.0, 0.0, 0.0, 1.0]
const DROOG := [0.0, 0.1, 0.8, 0.55]
const KOU := [0.25, 0.0, 0.5, 1.0]        # stuurt zonnestand/daglengte
const REGENKANS := [0.35, 0.10, 0.40, 0.0]

signal bevel_gegeven(ids: Array, soort: String, doel: Vector2i)
signal plan_gezet(plan: Plan)
signal plan_klaar(plan: Plan)
signal koe_erbij(koe: Vee)
signal koe_geclaimd(koe: Vee)
signal missie_einde(uitslag: String)      ## "gewonnen" of "verloren", een keer
signal dorpeling_erbij(d: Dorpeling)      ## een kind is geboren
signal kip_erbij(k: Kip)
signal rol_veranderd(d: Dorpeling)
signal wegen_veranderd
signal poort_gewisseld(p: Plan)
signal volwassen_geworden(d: Dorpeling)
## Melding voor de view (beasts-src `Building.sold`, een pulsje): een klant rekende af aan de toonbank van `winkel`.
## De kas en `Plan.voorraad` blijven de waarheid; dit verandert niets aan de sim.
signal verkocht(winkel: Plan, waar: String, prijs: int)
## Melding voor de view (beasts-src `World.restock`): er kwam een stuk graan/melk/ei op het schap van `winkel`.
signal geleverd(winkel: Plan, brengt: String)
## Wolven (sim/wolf.gd): een koe is opgegeten (uit `vee`), een dorpeling begint een worp, een steen raakt, een wolf valt
## om, een dode wolf is vergaan (uit `wolven`).
signal koe_weg(koe: Vee)
signal steen_gegooid(d: Dorpeling, wolf: Wolf)
signal wolf_geraakt(wolf: Wolf)
signal wolf_dood(wolf: Wolf)
signal wolf_weg(wolf: Wolf)
signal wolf_erbij(wolf: Wolf)              ## uit een wolf-generator (sim/wolf.gd spawn)
signal zwaard_slag(d: Dorpeling, wolf: Wolf)   ## voetsoldaat begint een zwaardslag (view: clip aanval_zwaard)
signal gedronken(d: Dorpeling, put: Plan)      ## water gehaald bij de put (missie 3), dorst weer 0
signal voorwerp_opgeraapt(ob: Dictionary, d: Dorpeling)   ## sim/voorwerpen.gd: beker of kelk aangeraakt
signal voorwerp_afgeleverd(ob: Dictionary, d: Dorpeling, kas: int)   ## bij het doel (vlag): kas erbij, object weg
signal voorwerp_gevallen(ob: Dictionary)   ## drager weg: ligt weer op de grond
## Leven (sim/leven.gd): schade, dood (oorzaak "wolf", "ouderdom", ...; al uit `dorpelingen`), met pensioen (oud).
signal dorpeling_geraakt(d: Dorpeling, oorzaak: String)
signal dorpeling_dood(d: Dorpeling, oorzaak: String)
signal met_pensioen(d: Dorpeling)
signal kas_beloning(id: String, kas: int)   ## sim/beloningen.gd: een kas-actie uit het missiebestand (0x16)

## Bouwbare soorten: voetafdruk in tegels (2 m per tegel). Prijs en bouwtijd volgen met de economie.
## Voetafdruk in tegels (2 m), breed (x) x diep (z) bij draai 0, uit de glb op ware grootte (Bouwmenu.GEBOUWEN):
## hut 7,6 x 7,1 m incl. hek (deur 1,58 m, zie Bouwmenu.DEUR_M), gereedschapsloods 8,9 x 3,6 m incl. het ijzer aan de
## zijkant, kippenhok 2,4 x 2,4 m (stromat).
## Molen (= bakkerij, beasts-src SHOP) 8,2 x 5,8 m incl. wieken; akker 2x2 tegels, elk een akker-glb van 2 x 2 m;
## melkerij 7,7 x 6,6 m incl. varkenshok, op deurmaat (deur 1,84 m -> 0,86x) 6,6 x 5,6 m.
const BOUWSOORTEN := {&"hut": Vector2i(4, 4), &"gereedschapsloods": Vector2i(5, 2), &"kippenhok": Vector2i(2, 2),
	&"molen": Vector2i(4, 3), &"akker": Vector2i(2, 2), &"melkerij": Vector2i(4, 4), &"hek": Vector2i(1, 1),
	&"poort": Vector2i(1, 1), &"weg": Vector2i(1, 1), &"put": Vector2i(3, 3), &"voetvolkgilde": Vector2i(3, 3)}
## Missie 3 (2026-10-30): put en voetvolkgilde 3x3. De put is `bron.glb` (4,9 x 5,0 m); het gilde heeft nog geen glb.
## Maat naar de sprites ten opzichte van de hut (4x4): `well` 133 px breed = hut 134 px, `fguild` 118 px = 0,88 x hut.
## Vanaf welke missie een soort in het bouwmenu staat (los van de keten in ONTGRENDEL): het origineel heeft een eigen
## voortgangstabel die niet gevonden is; hint 3-4 ("putten plaatsen") en 3-5 ("bouw nog een gilde") zeggen M3.
const VANAF_MISSIE := {&"put": 3, &"voetvolkgilde": 3}
## Gilden: afgebouwd gebouw -> rol die een man er krijgt (prijs en de rest in spel.json onder de rol). Origineel: alleen
## mannen, hoogstens `gilde_max_leden` (6, hint 3-5) per gilde; daarboven een tweede gilde bouwen.
const GILDEN := {&"gereedschapsloods": "bouwer", &"voetvolkgilde": "voetsoldaat"}
## Bouwmenu-volgorde (besluit gebruiker 2026-10-29): eerst hut, kippenhok en loods; een afgebouwde loods opent molen
## en akker; een afgebouwde molen opent melkerij, hek en poort. Weg (1 tegel, slepen = rij, sim/bouwrij.gd) kan vanaf
## de start (2026-10-30); af wordt de tegel pad en verdwijnt het plan (_weg_af).
const START_SOORTEN := [&"hut", &"kippenhok", &"gereedschapsloods", &"weg"]
var alles_open := false                  ## tests en scenario's: het hele bouwmenu meteen
const ONTGRENDEL := {&"molen": &"gereedschapsloods", &"akker": &"gereedschapsloods", &"melkerij": &"molen",
	&"hek": &"molen", &"poort": &"molen"}
const NIET_BLOKKEREND := [&"akker"]       ## loopbaar na de bouw (beasts-src Ground.FIELD is begaanbaar)
var plannen: Array[Plan] = []

var spel: Dictionary
var missie_nr := 1
## De missie uit spel.json `missies.<nr>`: kaart, start_kas, doel, verlies, koe_generator (zie laad()).
var missie: Dictionary = {}
var voorgebouwd: Array[Dictionary] = []  # {soort, tegel}: gebouwen die de kaart al heeft (plaats_voorgebouwd)
var _kaart_vee: Array[Dictionary] = []   # {tegel, eigen}: koeien die de kaart al heeft (klasse met "vee")
var _ontbreekt_gemeld := {}              # klasse-id's die al een waarschuwing gaven
var raster := Raster.new()
var mist := Mist.new()                   # sim/mist.gd: verkend gebied (fog of war)
var objecten: Array[Dictionary] = []     # {cls, naam, model, x, y, blokkeert, state, sex}
var dorpelingen: Array[Dorpeling] = []
var vee: Array[Vee] = []
var kippen: Array[Kip] = []
var wolven: Array[Wolf] = []             # missie 2: klasse 104 (objecten.json "beest": "wolf"), sim/wolf.gd
var _kaart_wolven: Array = []            # wolven uit de kaart: {tegel, soort} (objecten.json 104 "soorten")
var kas := 0
var handel: Handel                        ## sim/handel.gd: prijzen per waar, geluk, misdaad (spel.json handel)
var doden := 0                            # dorpelingen gestorven (sim/leven.gd), origineel statistiek Deaths
var pensioenen := 0                       # met pensioen gegaan, origineel Retirements
var beloningen := {}                      # sim/beloningen.gd: id -> tijd_s waarop de kas-actie vuurde
var beloning_start_s := -1.0
var wolf_gen_t: Array[float] = []         # sim/wolf.gd: s per wolf-generator (missie.wolf_generator)
var wolven_gemaakt := 0                   # hoogste wolf-id tot nu toe (id's worden niet hergebruikt)
var uitslag := ""                         # "" bezig, "gewonnen", "verloren"
var _generatoren: Array[Vector2i] = []    # tegels van de koe-generators (klasse 171); missie 3 heeft er twee
var _generator_t: Array[float] = []
var _volgende_koe_id := 1
var wiegen: Array[Dictionary] = []        # {moeder, vader, hut: Plan, wacht}
var akkers := {}                          # tegel -> s groei (>= economie.rijp_s = rijp)
var _geoogst := {}                        # tegel -> id van de dorpeling die erheen loopt
var _klus_t := 0.0
var _was_nacht := false
var kampvuur := Vector2i.ZERO
var bereik := PackedByteArray()          # tegels bereikbaar vanaf het kampvuur
var _onbekend_gemeld := {}               # tegelnamen die al een waarschuwing gaven
var eiland := Rect2i()                   # omhullende van `bereik`
var rng := RandomNumberGenerator.new()
var tegel_m := 2.0
var loop_mps := 0.849                    # uit bumpkin_anim.json (lopen)
var looptempo := 2.0                     # globale vermenigvuldiger op het loopen (spel.json); 1 = animatiesnelheid
var tik_dt := 0.1

var tijd_s := 0.0                        # sim-tijd; dag 0 begint op 0
var tik_nr := 0
var tempo := 1.0                         # 1, 2, 4
var gepauzeerd := false
var regen_handmatig := -1                # -1 automatisch, 0 uit, 1 aan
var _acc := 0.0
var _obj_def: Dictionary


## Laadt de data en de kaart van missie `nr` (spel.json `missies`). Geeft false als iets ontbreekt (dan staat er een
## fout in de log). `kaart_pad` overschrijft de kaart van de missie.
func laad(kaart_pad := "", nr := 1) -> bool:
	spel = Gegevens.lees(Gegevens.SPEL)
	var tegels = Gegevens.lees(Gegevens.TEGELS)
	_obj_def = Gegevens.lees(Gegevens.OBJECTEN)
	if spel == null or tegels == null or _obj_def == null:
		return false
	var missies: Dictionary = spel.get("missies", {})
	if not missies.has(str(nr)):
		push_error("wereld: missie %d staat niet in spel.json (missies)" % nr)
		return false
	missie_nr = nr
	missie = missies[str(nr)]
	tegel_m = float(spel["tegel_m"])
	tik_dt = 1.0 / float(spel["sim_hz"])
	loop_mps = Gegevens.loop_mps(spel)
	looptempo = float(spel.get("looptempo", 1.0))
	rng.seed = 1
	raster.laad_tegels(tegels)
	var pad: String = kaart_pad if kaart_pad != "" else missie["kaart"]
	var kaart = Gegevens.lees(pad)
	if kaart == null:
		push_error("wereld: kaart ontbreekt, draai sync.ps1 (" + pad + ")")
		return false
	_vul_raster(kaart, tegels)
	_plaats_objecten(kaart)
	if kampvuur == Vector2i.ZERO:
		push_error("wereld: geen kampvuur in de kaart")
		return false
	bereik = Router.bereikbaar(raster, _vrij_naast(kampvuur))
	_bepaal_eiland()
	_maak_dorpelingen()
	kas = int(missie.get("start_kas", 0))
	_maak_kaart_vee()
	wolven = Wolf.uit_kaart(self, _kaart_wolven)
	_start_generator()
	mist.start(self)
	handel = Handel.new(self)
	handel.start(self)
	tijd_s = float(spel["start_seizoen"]) * float(spel["seizoen_s"]) + float(spel["start_klok_s"])
	return true


func _vul_raster(kaart: Dictionary, tegels: Dictionary) -> void:
	var k: int = kaart["size"][0]
	var r: int = kaart["size"][1]
	raster.maak(k, r)
	var map_kind: Dictionary = tegels["kind_naar_tegel"]
	var wegen: Dictionary = tegels["weg_naar_tegel"]
	for y in r:
		var rij_kind: Array = kaart["kinds"][y]
		var rij_weg: Array = kaart["road"][y]
		for x in k:
			var naam: String = map_kind.get(rij_kind[x], "leeg")
			var i := raster.idx(x, y)
			raster.soort[i] = _soort_index(naam)
			var weg := str(int(rij_weg[x]))
			if wegen.has(weg) and naam != "water" and naam != "leeg":
				raster.soort[i] = _soort_index(wegen[weg])


## Index van een tegelnaam; een onbekende naam wordt "leeg" (anders 255 in de bytes en later een index buiten bereik).
func _soort_index(naam: String) -> int:
	var i := raster.namen.find(naam)
	if i < 0:
		if not _onbekend_gemeld.has(naam):
			_onbekend_gemeld[naam] = true
			push_warning("wereld: onbekende tegelsoort '%s', wordt leeg" % naam)
		i = raster.namen.find("leeg")
	return i


func _plaats_objecten(kaart: Dictionary) -> void:
	var defs: Dictionary = _obj_def["objecten"]
	for o in kaart["objects"]:
		var cls := str(int(o["cls"]))
		if not defs.has(cls):
			push_warning("wereld: onbekend object %s (%s)" % [cls, o.get("name", "?")])
			continue
		var d: Dictionary = defs[cls]
		if d.has("ontbreekt") and not _ontbreekt_gemeld.has(cls):
			_ontbreekt_gemeld[cls] = true
			push_warning("wereld: klasse %s (%s) nog zonder eigen model of gedrag: %s" % [cls, d["naam"], d["ontbreekt"]])
		if d.has("gebouw"):          # voorgebouwd (eigenaar 0): wordt een afgebouwd Plan, zie plaats_voorgebouwd()
			if int(o.get("owner", 0)) == 0:
				voorgebouwd.append({"soort": StringName(d["gebouw"]), "tegel": Vector2i(int(o["x"]), int(o["y"])),
					"draai": int(d.get("draai", -1))})
			continue
		if d.get("vee", false):      # koe uit de kaart: wordt een Vee, zie _maak_kaart_vee()
			_kaart_vee.append({"tegel": Vector2i(int(o["x"]), int(o["y"])), "eigen": int(o.get("owner", 4)) == 0})
			continue
		if d.get("beest", "") == "wolf":   # wolf uit de kaart: wordt een Wolf, geen object
			_kaart_wolven.append({"tegel": Vector2i(int(o["x"]), int(o["y"])),
				"soort": StringName(d.get("soorten", {}).get(str(int(o.get("sex", 23))), "wolf"))})
			continue
		var ob := {"cls": int(o["cls"]), "naam": d["naam"], "model": d["model"], "x": int(o["x"]), "y": int(o["y"]),
			"blokkeert": d["blokkeert"], "voetafdruk": d["voetafdruk"], "state": int(o["state"]), "sex": int(o["sex"]),
			"spawn": d.get("spawn", false), "owner": int(o.get("owner", 0))}
		if d.get("voorwerp", false):  # op te rapen (sim/voorwerpen.gd)
			ob["voorwerp"] = true
			ob["drager"] = -1
		objecten.append(ob)
		if int(o["cls"]) == int(spel["kampvuur_id"]):
			kampvuur = Vector2i(ob["x"], ob["y"])
		elif int(o["cls"]) == int(spel.get("koe_generator_id", -1)):
			_generatoren.append(Vector2i(ob["x"], ob["y"]))
			_generator_t.append(0.0)
	# Gegenereerde bomen op bosgrond (kaart heeft maar 42 bomen; de originele dennen zijn onbekend, zie map1.md).
	var dichtheid: float = float(missie.get("bos_dichtheid", spel["bos_dichtheid"]))   # per missie te overschrijven
	var rand := _afstand_tot_leeg(RAND_DICHT)
	for y in raster.rijen:
		for x in raster.kolommen:
			if raster.soort_naam(x, y) != "bosgrond":
				continue
			if _hash2(x, y) < dichtheid or rand[raster.idx(x, y)] <= RAND_DICHT:
				objecten.append({"cls": 1000, "naam": "boom_bos", "model": defs["1000"]["model"], "x": x, "y": y,
					"blokkeert": true, "voetafdruk": [1, 1], "state": 0, "sex": 0, "spawn": false})
	for ob in objecten:
		if ob["blokkeert"]:
			var vw: int = ob["voetafdruk"][0]
			var vd: int = ob["voetafdruk"][1]
			for dy in vd:
				for dx in vw:
					if raster.in_kaart(ob["x"] + dx, ob["y"] + dy):
						raster.blok[raster.idx(ob["x"] + dx, ob["y"] + dy)] = 1
	for i in rand.size():          # oever of open land direct aan het buitengebied: ook dicht
		if rand[i] == 1:
			raster.blok[i] = 1


## Het buitengebied (leeg) is in het origineel onbereikbaar: dicht bos, water of rots ertussen. Bosgrond binnen
## `RAND_DICHT` tegels van leeg krijgt altijd een boom, en elke andere tegel direct ernaast wordt geblokkeerd.
const RAND_DICHT := 3


## Per tegel de afstand (8-buren, in tegels) tot de dichtste leeg-tegel, tot `max_d`; verder weg = max_d + 1.
func _afstand_tot_leeg(max_d: int) -> PackedByteArray:
	var af := PackedByteArray()
	af.resize(raster.kolommen * raster.rijen)
	af.fill(max_d + 1)
	var leeg := raster.namen.find("leeg")
	var rij: Array[Vector2i] = []
	for y in raster.rijen:
		for x in raster.kolommen:
			if raster.soort[raster.idx(x, y)] == leeg:
				af[raster.idx(x, y)] = 0
				rij.append(Vector2i(x, y))
	var j := 0
	while j < rij.size():
		var t := rij[j]
		j += 1
		var d: int = af[raster.idx(t.x, t.y)]
		if d >= max_d:
			continue
		for k in 8:
			var n := t + Vector2i(Raster.DC[k], Raster.DR[k])
			if raster.in_kaart(n.x, n.y) and af[raster.idx(n.x, n.y)] > d + 1:
				af[raster.idx(n.x, n.y)] = d + 1
				rij.append(n)
	return af


func _maak_dorpelingen() -> void:
	var sexmap: Dictionary = _obj_def["sex"]
	var n := 0
	for ob in objecten:
		if not ob["spawn"]:
			continue
		n += 1
		var d := Dorpeling.new()
		d.id = n
		d.naam = "dorpeling%d" % n
		d.sex_ruw = ob["sex"]
		var s: Dictionary = sexmap.get(str(ob["sex"]), {"geslacht": "onbekend", "leeftijd": "volwassen"})
		d.geslacht = s["geslacht"]
		d.leeftijd = s["leeftijd"]
		d.rol = s.get("rol", "")          # objecten.json sex 7: krijger = voetsoldaat (missie 3, Pigsy)
		var t := Vector2i(ob["x"], ob["y"])
		if not raster.loopbaar_v(t):      # missie 2: een dorpeling staat op de bron; naar de dichtste vrije tegel
			var v := dichtstbij_loopbaar(t)
			if v.x >= 0:
				t = v
		d.zet_tegel(t)
		d.anker = kampvuur
		d.wacht = rng.randf_range(1.0, 6.0)
		dorpelingen.append(d)


## Een begaanbare tegel bij een (geblokkeerde) tegel, voor de bereikbaarheidsveeg vanaf het kampvuur.
func _vrij_naast(t: Vector2i) -> Vector2i:
	for r in range(1, 5):
		for dy in range(-r, r + 1):
			for dx in range(-r, r + 1):
				var c := t + Vector2i(dx, dy)
				if raster.loopbaar_v(c):
					return c
	return t


func _bepaal_eiland() -> void:
	var x0 := 9999
	var y0 := 9999
	var x1 := -1
	var y1 := -1
	for y in raster.rijen:
		for x in raster.kolommen:
			if bereik[raster.idx(x, y)] == 1:
				x0 = mini(x0, x)
				y0 = mini(y0, y)
				x1 = maxi(x1, x)
				y1 = maxi(y1, y)
	eiland = Rect2i(x0, y0, x1 - x0 + 1, y1 - y0 + 1)


func _hash2(x: int, y: int) -> float:
	var h: int = ((x * 73856093) ^ (y * 19349663)) & 0x7fffffff
	h = ((h ^ (h >> 13)) * 1274126177) & 0x7fffffff
	h = h ^ (h >> 16)
	return float(h & 0xffff) / 65535.0


# ---------------------------------------------------------------- tijd

func vooruit(dt: float) -> void:
	if gepauzeerd:
		return
	_acc += dt * tempo
	var n := 0
	while _acc >= tik_dt - 1e-9 and n < 200:
		_acc -= tik_dt
		n += 1
		tik(tik_dt)
	if n >= 200:
		_acc = 0.0  # na een lange hapering niet frames lang blijven inhalen


func tik(dt: float) -> void:
	tijd_s += dt
	tik_nr += 1
	for d in dorpelingen:
		d.tick(self, dt)
	for k in vee:
		k.tick(self, dt)
	for k in kippen:
		k.tick(self, dt)
	for p in plannen.duplicate():       # kopie: een afgebouwde weg haalt zijn plan uit de lijst
		if not p.klaar and p.voortgang >= 1.0:
			_rond_af(p)
	Wolf.tik_alle(self, dt)
	Leven.tik_alle(self, dt)
	Beloningen.tik(self)
	Voorwerpen.tik_alle(self, dt)
	mist.tik(self)
	_werk_generator(dt)
	_gezin(dt)
	_economie(dt)
	handel.tik(self, dt)
	_check_missie()


# ---------------------------------------------------------------- winkels: graan -> molen -> brood, melk -> melkerij (beasts-src-lus)

## Winkel per waar: wat erheen gedragen wordt en wat er gekocht wordt (beasts-src Kind.SHOP = CROP, DAIRY = MILK).
const WINKELS := {&"molen": {"brengt": "graan", "waar": "brood"}, &"melkerij": {"brengt": "melk", "waar": "melk"},
	&"kippenhok": {"brengt": "ei", "waar": "ei"}}
const WAREN := ["brood", "melk", "ei"]

## Akkers groeien in lente en zomer; bij het begin van de winter sterft wat rijp staat (gameplay.md 3, Grid.wither).
## Koeien geven na het melken pas na `koe_leeg_s` weer melk. Elke halve seconde kiest wie niets omhanden heeft een klus:
## wegbrengen wat hij draagt, kopen waar hij trek in heeft, of (volwassen) oogsten of melken.
func _economie(dt: float) -> void:
	var e: Dictionary = spel["economie"]
	var rijp := float(e["rijp_s"])
	var s := seizoen()
	if s <= 1:
		for t in akkers:
			akkers[t] = minf(rijp, akkers[t] + dt)
	elif s == 3 and int((tijd_s - dt) / seizoen_duur()) != int(tijd_s / seizoen_duur()):
		for t in akkers:
			if akkers[t] >= rijp:
				akkers[t] = 0.0
	for k in vee:
		k.leeg = maxf(0.0, k.leeg - dt)
	_kalveren(dt)
	for d in dorpelingen:
		if not d.slaapt:          # wie slaapt krijgt geen trek
			for waar in WAREN:
				d.trek[waar] = float(d.trek.get(waar, 0.0)) + dt
			d.dorst += dt
	if not is_nacht() and _was_nacht:
		_wek()
	_was_nacht = is_nacht()
	_klus_t += dt
	if _klus_t < 0.5:
		return
	_klus_t = 0.0
	for d in dorpelingen:
		if d.ledig():
			_kies_klus(d)


func winkels(soort: StringName) -> Array[Plan]:
	var uit: Array[Plan] = []
	for p in plannen:
		if p.klaar and p.soort == soort:
			uit.append(p)
	return uit


func molens() -> Array[Plan]:
	return winkels(&"molen")


func voorraad(soort: StringName) -> int:
	var n := 0
	for m in winkels(soort):
		n += m.voorraad
	return n


func brood() -> int:
	return voorraad(&"molen")


func melk() -> int:
	return voorraad(&"melkerij")


func eieren() -> int:
	return voorraad(&"kippenhok")


## Een nieuw kippenhok krijgt zijn kippen bij de deur; elk legt pas na een eigen, verspreide eerste wachttijd.
func _maak_kippen(hok: Plan) -> void:
	var e: Dictionary = spel["economie"]
	var deur := dichtstbij_loopbaar(hok.deur_tegel())
	var plekken := spreid(deur, int(e["kippen_per_hok"]))
	for i in plekken.size():
		var k := Kip.new()
		k.id = kippen.size() + 1
		k.hok = hok
		k.zet_tegel(plekken[i])
		k.anker = deur
		k.leeg = float(e["kip_leeg_s"]) * (0.5 + 0.25 * i)
		k.wacht = rng.randf_range(0.5, 3.0)
		kippen.append(k)
		kip_erbij.emit(k)


func rijp(t: Vector2i) -> bool:
	return akkers.has(t) and akkers[t] >= float(spel["economie"]["rijp_s"])


func _winkel_voor(waar: String, brengt: bool) -> StringName:
	for s in WINKELS:
		if WINKELS[s]["brengt" if brengt else "waar"] == waar:
			return s
	return &""


func _dichtste_winkel(d: Dorpeling, soort: StringName, met_voorraad: bool) -> Plan:
	var beste: Plan = null
	var bd := INF
	for m in winkels(soort):
		if met_voorraad and m.voorraad <= 0:
			continue
		var af := d.pos.distance_squared_to(Vector2(m.deur_tegel()))
		if af < bd:
			bd = af
			beste = m
	return beste


## Melkbaar: niet leeg, niet al vast (claim of melker onderweg) en binnen `melk_straal` tegels van het kampvuur
## (besluit gebruiker: ook wilde koeien geven melk, maar alleen als ze dicht bij het dorp staan).
func melkbaar(k: Vee) -> bool:
	return k.leeg <= 0.0 and not k.vast and not k.is_kalf() and Vector2(k.tegel()).distance_to(Vector2(kampvuur)) <= float(spel["economie"]["melk_straal"])


## Zelfstandig werk, in deze volgorde: wat hij draagt wegbrengen; 's nachts naar bed (een hut met een vrij bed);
## kopen waar hij trek in heeft; (volwassen) bouwen aan een open plan (bouwers altijd, anderen met hoogstens
## `zelf_bouwen_per_plan` tegelijk), oogsten, melken, eieren rapen. Een bevel van de speler gaat altijd voor.
func _kies_klus(d: Dorpeling) -> void:
	var e: Dictionary = spel["economie"]
	if d.draagt != "":
		var m := _dichtste_winkel(d, _winkel_voor(d.draagt, true), false)
		if m != null and d.geef_bevel(self, "lever", dichtstbij_loopbaar(m.deur_tegel())):
			d.klus = m
		return
	if is_nacht():
		# geen klus maar de nacht: een bed in een hut, en anders liggen bij het kampvuur
		var hut := _vrij_bed(d)
		if hut != null and d.geef_bevel(self, "slaap", dichtstbij_loopbaar(hut.deur_tegel())):
			d.slaapplek = hut
		elif hut == null and not d.slaapt:
			var plek := _plek_bij_vuur(d)
			if plek.x >= 0 and d.geef_bevel(self, "vuur", plek):
				d.bij_vuur = true
		return
	for waar in WAREN:
		if float(d.trek.get(waar, 0.0)) < float(e["trek_s"]):
			continue
		var m := _dichtste_winkel(d, _winkel_voor(waar, false), true)
		if m != null and d.geef_bevel(self, "koop", dichtstbij_loopbaar(m.deur_tegel())):
			d.klus = m
			d.koopt = waar
			return
	if d.dorst >= float(e.get("dorst_s", 90.0)):     # water halen, gratis: bij de put (missie 3) of de bron/plas (origineel)
		var put := dichtste_gebouw(&"put", d.tegel())
		var bron := _dichtste_bron(d.tegel())
		var naar_put := put != null and (bron.x < 0 or Vector2(d.tegel()).distance_to(Vector2(put.deur_tegel())) <= Vector2(d.tegel()).distance_to(Vector2(bron)))
		if naar_put and d.geef_bevel(self, "koop", dichtstbij_loopbaar(put.deur_tegel())):
			d.klus = put
			d.koopt = "water"
			return
		if not naar_put and bron.x >= 0 and d.geef_bevel(self, "koop", dichtstbij_loopbaar(bron)):
			d.klus = null
			d.koopt = "water"
			return
	if not d.volwassen() or d.rol == "voetsoldaat":    # soldaten boeren niet (origineel)
		return
	var plan := _open_plan(d)
	if plan != null and geef_bouwbevel([d.id], plan) > 0:
		return
	if not molens().is_empty():
		var beste := Vector2i(-1, -1)
		var bd := INF
		for t in akkers:
			if rijp(t) and not _geoogst.has(t):
				var af := d.pos.distance_squared_to(Vector2(t))
				if af < bd:
					bd = af
					beste = t
		if beste.x >= 0 and d.geef_bevel(self, "oogst", beste):
			d.klus_tegel = beste
			_geoogst[beste] = d.id
			return
	if not winkels(&"melkerij").is_empty():
		var koe_best: Vee = null
		var kd := INF
		for k in vee:
			if melkbaar(k):
				var af := d.pos.distance_squared_to(k.pos)
				if af < kd:
					kd = af
					koe_best = k
		if koe_best != null and d.geef_bevel(self, "melk", _naast(koe_best.tegel(), d.tegel())):
			d.melk_koe = koe_best
			koe_best.vast = true
			return
	var kip_best: Kip = null
	var kpd := INF
	for k in kippen:
		if k.ei and not k.vast:
			var af := d.pos.distance_squared_to(k.pos)
			if af < kpd:
				kpd = af
				kip_best = k
	if kip_best != null and d.geef_bevel(self, "raap", _naast(kip_best.tegel(), d.tegel())):
		d.raap_kip = kip_best
		kip_best.vast = true


## Dichtste afgebouwde hut met een bed over (bedden_per_hut min wie er vannacht al slaapt), of null.
func _vrij_bed(d: Dorpeling) -> Plan:
	var per_hut := int(spel["gezin"]["bedden_per_hut"])
	var beste: Plan = null
	var bd := INF
	for p in plannen:
		if not p.klaar or p.soort != &"hut":
			continue
		var bezet := 0
		for x in dorpelingen:
			if x.slaapplek == p:
				bezet += 1
		if bezet >= per_hut:
			continue
		var af := d.pos.distance_squared_to(Vector2(p.deur_tegel()))
		if af < bd:
			bd = af
			beste = p
	return beste


## Een vrije tegel in de kring rond het kampvuur (1 tot 2,3 tegels), een per slaper.
func _plek_bij_vuur(d: Dorpeling) -> Vector2i:
	var bezet := {}
	for x in dorpelingen:
		if x != d and x.bij_vuur and not x.bevel.is_empty():
			bezet[x.bevel["doel"]] = true
		elif x != d and x.bij_vuur:
			bezet[x.tegel()] = true
	for t in spreid(dichtstbij_loopbaar(kampvuur), 40):
		var af := Vector2(t).distance_to(Vector2(kampvuur))
		if af >= 1.0 and af <= 2.3 and not bezet.has(t) and bereik[raster.idx(t.x, t.y)] == 1:
			return t
	return Vector2i(-1, -1)


## 's Ochtends iedereen het bed uit, naast de deur van zijn hut, en wie bij het vuur lag staat op.
func _wek() -> void:
	for d in dorpelingen:
		if d.bij_vuur:
			d.bij_vuur = false
			d.slaapt = false
			if d.bevel.get("soort", "") == "vuur":
				d.route.clear()
				d.bevel = {}
			d.anker = kampvuur
			d.wacht = rng.randf_range(0.5, 4.0)
		if d.slaapplek == null:
			continue
		var hut := d.slaapplek
		d.slaapplek = null
		if d.slaapt:
			d.slaapt = false
			d.binnen = false
			var plekken := spreid(dichtstbij_loopbaar(hut.deur_tegel()), 4)
			d.zet_tegel(plekken[d.id % plekken.size()] if not plekken.is_empty() else hut.deur_tegel())
			d.anker = kampvuur        # het dorp
			d.wacht = rng.randf_range(0.5, 4.0)
		elif d.bevel.get("soort", "") == "slaap":    # nog onderweg naar bed: laat maar
			d.route.clear()
			d.bevel = {}


## Dichtste open plan voor deze volwassene: een bouwer neemt elk plan, een ander alleen een plan waar nog minder dan
## `zelf_bouwen_per_plan` aan werken (zodat er ook geoogst en gemolken wordt). Null als er niets is.
func _open_plan(d: Dorpeling) -> Plan:
	var max_n := int(spel.get("zelf_bouwen_per_plan", 2))
	var beste: Plan = null
	var bd := INF
	for p in plannen:
		if p.klaar:
			continue
		if d.rol != "bouwer":
			var n := 0
			for x in dorpelingen:
				if x.werk_plan == p:
					n += 1
			if n >= max_n:
				continue
		var af := d.pos.distance_squared_to(Vector2(p.tegel))
		if af < bd:
			bd = af
			beste = p
	return beste


func laat_akker_los(t: Vector2i) -> void:
	_geoogst.erase(t)


## Aangekomen voor een klus: even staan (oogsten, melken of aan de toonbank), daarna `klus_af`.
func klus_aangekomen(d: Dorpeling, soort: String) -> void:
	var e: Dictionary = spel["economie"]
	match soort:
		"oogst": d.bezig = float(e["oogst_s"])
		"melk":
			d.bezig = float(e["melk_s"])
			if d.melk_koe != null:
				d.melk_koe.gemolken = true
		"koop":
			if d.koopt == "water":
				d.bezig = float(e.get("drink_s", 2.0))
			else:
				d.bezig = float(e["toonbank_s"]) + 2.0 * deur_loop_s(d)
		"raap": d.bezig = float(e["raap_s"])
		_: d.bezig = 0.3 + 2.0 * deur_loop_s(d)


## Leveren of kopen in een gebouw met een deur: de tijd voor het stukje door de deur (heen = terug); de view laat hem
## dat lopen (view/deur_loop.gd). 0 zonder deur.
func deur_loop_s(d: Dorpeling) -> float:
	if not (d.klus is Plan) or not Plan.DEUREN.has((d.klus as Plan).soort) or (d.klus as Plan).soort == &"put":
		return 0.0                 # bij de put drinken ze buiten
	return (d.klus as Plan).deur_loop_m(tegel_m) / (loop_mps * looptempo)


## Dichtste bron (klasse 144 `spring`, de plas bij het dorp) die bereikbaar is, of (-1, -1). Dorpelingen drinken er ook
## uit (gebruiker 2026-10-30: "in het origineel drinken ze ook uit de pond").
func _dichtste_bron(van: Vector2i) -> Vector2i:
	var beste := Vector2i(-1, -1)
	var bd := INF
	for ob in objecten:
		if ob["naam"] != "bron":
			continue
		var t := Vector2i(ob["x"], ob["y"])
		var af := Vector2(van).distance_squared_to(Vector2(t))
		if af < bd and dichtstbij_loopbaar(t).x >= 0:
			bd = af
			beste = t
	return beste


func klus_af(d: Dorpeling) -> void:
	var e: Dictionary = spel["economie"]
	if d.klus_tegel.x >= 0:
		var t := d.klus_tegel
		_geoogst.erase(t)
		if rijp(t):
			akkers[t] = 0.0
			d.draagt = "graan"
	elif d.melk_koe != null:
		var k := d.melk_koe
		k.vast = false
		k.gemolken = false
		if k.leeg <= 0.0:
			k.leeg = float(e["koe_leeg_s"])
			d.draagt = "melk"
		d.melk_koe = null
	elif d.raap_kip != null:
		var k := d.raap_kip
		k.vast = false
		if k.ei:
			k.ei = false
			k.leeg = float(e["kip_leeg_s"])
			d.draagt = "ei"
		d.raap_kip = null
	elif d.koopt == "water":
		d.dorst = 0.0
		gedronken.emit(d, d.klus as Plan)          # null = gedronken bij de bron/plas
		d.koopt = ""
	elif d.klus is Plan:
		var m: Plan = d.klus
		if d.draagt != "":
			m.voorraad += 1         # beasts-src restock
			geleverd.emit(m, d.draagt)
			d.draagt = ""
		elif m.voorraad > 0:
			m.voorraad -= 1         # beasts-src visit: de kas krijgt de prijs
			var p := handel.verkoop(d.koopt)   # prijs per waar uit het prijzenscherm (sim/handel.gd)
			kas += p
			verkocht.emit(m, d.koopt, p)
			d.trek[d.koopt] = 0.0
		d.koopt = ""
	d.klus = null
	d.klus_tegel = Vector2i(-1, -1)


# ---------------------------------------------------------------- gezin (port van beasts-src World.family)

## Bedden van afgebouwde hutten.
func bedden() -> int:
	var n := 0
	for p in plannen:
		if p.klaar and p.soort == &"hut":
			n += int(spel["gezin"]["bedden_per_hut"])
	return n


## Plek voor nog een kind: bedden min iedereen, min de wiegen en de baby's die er al aan komen (beasts-src
## roomToGrowOf; zonder de wiegen kiezen twee paren in dezelfde tik hetzelfde laatste bed).
func ruimte() -> int:
	var n := bedden() - dorpelingen.size() - wiegen.size()
	for d in dorpelingen:
		if d.baby > 0.0:
			n -= 1
	return n


func _gezin(dt: float) -> void:
	var g: Dictionary = spel["gezin"]
	for i in dorpelingen.size():          # op index: een geboorte voegt er een toe
		var d := dorpelingen[i]
		d.rust = maxf(0.0, d.rust - dt)
		if d.groeit > 0.0:
			d.groeit = maxf(0.0, d.groeit - dt)
			if d.groeit <= 0.0:
				d.leeftijd = "volwassen"
				Leven.pas_gezondheid_aan(self, d)
				d.rust = float(g["ouder_rust_s"])   # net volwassen en meteen een gezin is een sneeuwbal
				volwassen_geworden.emit(d)
		if d.baby > 0.0:
			d.baby = maxf(0.0, d.baby - dt)
			if d.baby <= 0.0:
				_geboren(d)
	for wg in wiegen.duplicate():
		var m: Dorpeling = wg["moeder"]
		var v: Dorpeling = wg["vader"]
		if not (m.binnen and v.binnen):
			continue
		wg["wacht"] -= dt
		if wg["wacht"] <= 0.0:
			_baring(wg)
	_zoek_paar()


## Een vrije man en vrouw en een vrije hut: samen naar binnen.
func _zoek_paar() -> void:
	if ruimte() <= 0:
		return
	var man: Dorpeling = null
	var vrouw: Dorpeling = null
	for d in dorpelingen:
		if not d.vrij_voor_gezin():
			continue
		if d.geslacht == "man" and man == null:
			man = d
		elif d.geslacht == "vrouw" and vrouw == null:
			vrouw = d
	if man == null or vrouw == null:
		return
	var hut: Plan = null
	var beste := INF
	for p in plannen:
		if not p.klaar or p.soort != &"hut" or _hut_bezet(p):
			continue
		var af := vrouw.pos.distance_squared_to(Vector2(p.deur_tegel()))
		if af < beste:
			beste = af
			hut = p
	if hut == null:
		return
	var deur := dichtstbij_loopbaar(hut.deur_tegel())
	var wg := {"moeder": vrouw, "vader": man, "hut": hut, "wacht": float(spel["gezin"]["wieg_s"]), "deur": deur}
	vrouw.wieg = wg
	man.wieg = wg
	if not (vrouw.geef_bevel(self, "huis", deur) and man.geef_bevel(self, "huis", deur)):
		annuleer_wieg(wg)
		return
	wiegen.append(wg)


func _hut_bezet(p: Plan) -> bool:
	for wg in wiegen:
		if wg["hut"] == p:
			return true
	return false


## Het gezin gaat niet door (bevel van de speler): wie binnen zit komt naar buiten.
func annuleer_wieg(wg: Dictionary) -> void:
	wiegen.erase(wg)
	for k in ["moeder", "vader"]:
		var d: Dorpeling = wg[k]
		d.wieg = {}
		if d.binnen:
			d.binnen = false
		elif d.bevel.get("soort", "") == "huis":
			d.route.clear()
			d.bevel = {}


## Zij komt met de baby op de arm naar buiten, hij een tegel verder (beasts-src birth: niet op elkaar).
func _baring(wg: Dictionary) -> void:
	wiegen.erase(wg)
	var g: Dictionary = spel["gezin"]
	var m: Dorpeling = wg["moeder"]
	var v: Dorpeling = wg["vader"]
	var plekken := spreid(wg["deur"], 2)
	for d in [m, v]:
		d.wieg = {}
		d.binnen = false
		d.rust = float(g["ouder_rust_s"])
		d.anker = kampvuur
	m.zet_tegel(plekken[0] if plekken.size() > 0 else wg["deur"])
	v.zet_tegel(plekken[1] if plekken.size() > 1 else wg["deur"])
	m.baby = float(g["baby_s"])


## De baby is een kind: jongen of meisje uit een hash van tegel en aantal (geen rng: hetzelfde spel, hetzelfde kind).
func _geboren(moeder: Dorpeling) -> void:
	var g: Dictionary = spel["gezin"]
	var d := Dorpeling.new()
	var hoogste := 0
	for x in dorpelingen:
		hoogste = maxi(hoogste, x.id)
	d.id = hoogste + 1
	d.naam = "dorpeling%d" % d.id
	var t := moeder.tegel()
	var meisje := _hash2(t.x * 7 + dorpelingen.size(), t.y * 13 + 3) < 0.5
	d.geslacht = "vrouw" if meisje else "man"
	d.leeftijd = "kind"
	d.sex_ruw = 14 if meisje else 13
	d.groeit = float(g["opgroeien_s"])
	var plek := spreid(t, 2)
	d.zet_tegel(plek[1] if plek.size() > 1 else t)
	d.anker = kampvuur
	d.wacht = 2.0
	dorpelingen.append(d)
	dorpeling_erbij.emit(d)


# ---------------------------------------------------------------- koeien en missie

## Koe-generator (missie 1, klasse 171: spawnt cls 110 = koe). `start` koeien meteen; daarna elke `interval_s` een
## nieuwe zolang er minder dan `max` wilde van de generator rondlopen. Een geclaimde koe telt niet meer mee.
## Meerdere generators (missie 3): `start` en `max` gelden per generator.
func _start_generator() -> void:
	var g: Dictionary = missie.get("koe_generator", {})
	for gi in _generatoren.size():
		for _i in int(g.get("start", 1)):
			_spawn_koe(gi)


func _wild_van(gi: int) -> int:
	var wild := 0
	for k in vee:
		if k.van_generator and k.generator == gi and k.eigenaar < 0:
			wild += 1
	return wild


func _werk_generator(dt: float) -> void:
	var g: Dictionary = missie.get("koe_generator", {})
	for gi in _generatoren.size():
		var wild := _wild_van(gi)
		if wild >= int(g.get("max", 3)):
			_generator_t[gi] = 0.0
			continue
		_generator_t[gi] += dt
		if _generator_t[gi] >= float(g.get("interval_s", 45.0)):
			_generator_t[gi] = 0.0
			_spawn_koe(gi)


## Koeien die al op de kaart staan (missie 2: 4 eigen koeien bij het dorp). Eigen: zwerft rond het kampvuur.
func _maak_kaart_vee() -> void:
	for kv in _kaart_vee:
		var t := dichtstbij_loopbaar(kv["tegel"])
		if t.x < 0:
			continue
		var k := Vee.new()
		k.id = _volgende_koe_id
		_volgende_koe_id += 1
		k.zet_tegel(t)
		k.eigenaar = 0 if kv["eigen"] else -1
		k.anker = kampvuur if kv["eigen"] else t
		k.wacht = rng.randf_range(0.5, 4.0)
		vee.append(k)


## Zet de voorgebouwde gebouwen van de kaart (missie 2: de boerderij = melkerij) als afgebouwd Plan neer, gratis
## (ook de weg naar de deur). Na de view aanroepen: Bouwmenu en Wegen tekenen ze via plan_gezet/plan_klaar.
## De tegel uit de kaart ligt in de voetafdruk; draai en plek kiezen we zo dat de deur het dichtst bij een pad uitkomt.
var voorgebouwd_draai := -1       ## >= 0: alleen deze draai proberen (frames: --voordraai=)


func plaats_voorgebouwd() -> int:
	var n := 0
	_kies_volgorde()
	for vg in voorgebouwd:
		var soort: StringName = vg["soort"]
		var t: Vector2i = vg["tegel"]
		var beste := _voorgebouwd_plan(vg)
		if beste == null:
			push_warning("wereld: voorgebouwd %s op %s past niet" % [soort, t])
			continue
		var was := kas
		plannen.append(beste)
		plan_gezet.emit(beste)
		_rond_af(beste)
		kas = was
		n += 1
	voorgebouwd.clear()
	# een rol uit de kaart (krijger type 7 = voetsoldaat) is lid van het dichtste gilde van zijn soort, als dat er staat
	for d in dorpelingen:
		if d.rol != "" and d.lid == null:
			for gs in GILDEN:
				if GILDEN[gs] == d.rol:
					d.lid = dichtste_gebouw(gs, d.tegel())
	return n


## Het plan voor voorgebouwd `vg`, of null als het niet past. Draai zoals in het origineel (gebruiker 2026-10-30: de
## melkerij stond gedraaid): objecten.json "draai"; zonder die waarde de eerste draai die past, met de deur het dichtst
## bij een pad; --voordraai= overschrijft.
func _voorgebouwd_plan(vg: Dictionary) -> Plan:
	var pad := raster.namen.find("pad")
	var soort: StringName = vg["soort"]
	var t: Vector2i = vg["tegel"]
	var m: Vector2i = BOUWSOORTEN[soort]
	var beste: Plan = null
	var bd := INF
	for dr in 4:
		if beste != null:
			break
		var wil: int = voorgebouwd_draai if voorgebouwd_draai >= 0 else int(vg.get("draai", -1))
		if wil >= 0 and dr != wil:
			continue
		var b := m.y if dr % 2 == 1 else m.x
		var di := m.x if dr % 2 == 1 else m.y
		for oy in di:
			for ox in b:
				var p := maak_plan(soort, t - Vector2i(ox, oy), dr)
				if p == null or _raakt_ander_anker(p, vg):
					continue
				var af := _afstand_tot_soort(p.deur_tegel(), pad)
				if af < bd:
					bd = af
					beste = p
	return beste


## Missie 3 heeft drie gebouwen dicht op elkaar (hut, put, gilde) en de remake-hut is groter dan in het origineel: in
## kaartvolgorde past de put niet meer. Probeer de volgordes (hoogstens 4 gebouwen, anders kaartvolgorde) en neem de
## eerste waarin alles past; proefplannen staan alleen even in `plannen` (geen raster, geen signalen).
func _kies_volgorde() -> void:
	if voorgebouwd.size() < 2 or voorgebouwd.size() > 4:
		return
	for perm in _permutaties(voorgebouwd.size()):
		var proef: Array[Plan] = []
		var volgorde: Array[Dictionary] = []
		for i in perm:
			volgorde.append(voorgebouwd[i])
		var oud := voorgebouwd
		voorgebouwd = volgorde
		for vg in volgorde:
			var p := _voorgebouwd_plan(vg)
			if p == null:
				break
			proef.append(p)
			plannen.append(p)
		for p in proef:
			plannen.erase(p)
		voorgebouwd = oud
		if proef.size() == volgorde.size():
			voorgebouwd = volgorde
			return


static func _permutaties(n: int) -> Array:
	if n <= 1:
		return [[0]] if n == 1 else [[]]
	var uit: Array = []
	for rest in _permutaties(n - 1):
		for pos in range(n - 1, -1, -1):     # de kaartvolgorde eerst
			var p: Array = rest.duplicate()
			p.insert(pos, n - 1)
			uit.append(p)
	return uit


## Voorgebouwd plan `p` mag de kaarttegel van een ander voorgebouwd gebouw niet afdekken, en zijn deur ook niet: anders
## pakt de (te grote) hut de plek van de put die drie tegels verder staat (missie 3).
func _raakt_ander_anker(p: Plan, eigen: Dictionary) -> bool:
	var r := p.afdruk()
	for vg in voorgebouwd:
		if vg == eigen:
			continue
		var t: Vector2i = vg["tegel"]
		if r.has_point(t) or (Plan.DEUREN.has(p.soort) and p.deur_tegel() == t):
			return true
	return false


## Afstand (tegels, recht) van `t` tot de dichtste tegel van soort-index `s` (binnen 12), anders 99.
func _afstand_tot_soort(t: Vector2i, s: int) -> float:
	var beste := 99.0
	for dy in range(-12, 13):
		for dx in range(-12, 13):
			var c := t + Vector2i(dx, dy)
			if raster.in_kaart(c.x, c.y) and raster.soort[raster.idx(c.x, c.y)] == s:
				beste = minf(beste, Vector2(dx, dy).length())
	return beste


func _spawn_koe(gi := 0) -> Vee:
	if gi >= _generatoren.size():
		return null
	var t := dichtstbij_loopbaar(_generatoren[gi])
	if t.x < 0:
		return null
	var k := Vee.new()
	k.id = _volgende_koe_id
	_volgende_koe_id += 1
	k.zet_tegel(t)
	k.anker = t
	k.van_generator = true
	k.generator = gi
	k.wacht = rng.randf_range(0.5, 4.0)
	vee.append(k)
	koe_erbij.emit(k)
	return k


func koe(id: int) -> Vee:
	for k in vee:
		if k.id == id:
			return k
	return null


## Volwassen eigen koeien: het doel van missie 1 telt klasse 110 (cow > 3, M1.MIS), een kalf is klasse 96 en telt
## pas mee als het een koe is.
func eigen_koeien() -> int:
	var n := 0
	for k in vee:
		if k.eigenaar == 0 and not k.is_kalf():
			n += 1
	return n


## 0 = net geboren kalf .. 1 = koe (view/koe.gd zet_kalf).
func kalf_groei(k: Vee) -> float:
	if not k.is_kalf():
		return 1.0
	return 1.0 - k.kalf / float(spel["economie"].get("kalf_groei_s", 270.0))


func kalveren() -> int:
	var n := 0
	for k in vee:
		if k.is_kalf():
			n += 1
	return n


## Ouderdom: elke koe sterft na `koe_levensduur_s` (per koe tussen min en max; startkoeien beginnen op 0-50 %), net als
## door een wolf, dus de kudde groeit en krimpt (gebruiker 2026-10-30). Kalven stopt bij `vee_max` koeien in totaal.
## Kalven (hint 1-11: "koeien kalven in de lente, houd ze bij elkaar"; origineel klasse 96 `baby cow`, sprite cowborn).
## Een volwassen koe (eigen of wild) die deze lente `kalf_samen_s` binnen `kalf_straal` tegels van een andere volwassen
## koe stond (ongeacht eigenaar, besluit gebruiker 2026-10-30), krijgt met kans `kalf_kans` (hash, geen rng: zelfde spel, zelfde kalveren) een kalf naast zich; een keer per
## lente. Een kalf is na `kalf_groei_s` een koe. Getallen zijn eigen keuze (niet in de data gevonden).
func _kalveren(dt: float) -> void:
	var e: Dictionary = spel["economie"]
	var groei := float(e.get("kalf_groei_s", 270.0))
	var vee_max := int(missie.get("vee_max", e.get("vee_max", 24)))
	var duur: Array = e.get("koe_levensduur_s", [4320.0, 6480.0])
	var oud: Array[Vee] = []
	for k in vee:
		if k.leeftijd_s < 0.0:                # eerste tik: levensduur per koe, startkoeien al een stuk oud
			var h := _hash2(k.id * 3 + 1, 77)
			k.levensduur_s = lerpf(float(duur[0]), float(duur[1]), h)
			k.leeftijd_s = 0.0 if k.is_kalf() else _hash2(k.id * 5 + 2, 91) * 0.5 * k.levensduur_s
		k.leeftijd_s += dt
		if k.leeftijd_s >= k.levensduur_s:
			oud.append(k)
	for k in oud:
		for c in vee:
			if c.moeder == k:
				c.moeder = null
		verwijder_koe(k)                         # dood van ouderdom
	for k in vee:
		if k.is_kalf():
			k.kalf = maxf(0.0, k.kalf - dt)
			if not k.is_kalf():
				k.moeder = null
				k.anker = kampvuur if k.eigenaar == 0 else k.tegel()
	if seizoen() != 0:
		for k in vee:
			k.samen_s = 0.0
		return
	var jaar := int(tijd_s / (4.0 * seizoen_duur()))
	var straal := float(e.get("kalf_straal", 4.0))
	var nieuw: Array[Vee] = []
	for k in vee:
		if k.is_kalf() or k.kalf_jaar == jaar:        # elke koe, eigen of wild (gebruiker 2026-10-30)
			continue
		if vee.size() + nieuw.size() >= vee_max:
			break                                      # de kudde groeit niet onbeperkt (sterven houdt haar in evenwicht)
		for o in vee:
			if o != k and not o.is_kalf() and k.pos.distance_to(o.pos) <= straal:    # ongeacht eigenaar
				k.samen_s += dt
				break
		if k.samen_s < float(e.get("kalf_samen_s", 20.0)):
			continue
		k.kalf_jaar = jaar
		if _hash2(k.id, jaar + 11) < float(e.get("kalf_kans", 0.5)):
			nieuw.append(k)
	for m in nieuw:
		var t := dichtstbij_loopbaar(m.tegel() + Vector2i(1, 0))
		if t.x < 0:
			continue
		var c := Vee.new()
		c.id = _volgende_koe_id
		_volgende_koe_id += 1
		c.zet_tegel(t)
		c.anker = m.tegel()
		c.eigenaar = m.eigenaar
		c.weide = m.weide
		c.kalf = groei
		c.moeder = m
		c.wacht = 2.0
		vee.append(c)
		koe_erbij.emit(c)


## Stuur de eerste volwassene uit `ids` naar koe `koe_id`; aangekomen claimt hij haar, of laat haar los als ze al van
## de speler is (origineel: "click on it again ... a moo will confirm"). De koe blijft staan tot hij er is.
func geef_claimbevel(ids: Array, koe_id: int) -> int:
	var k := koe(koe_id)
	if k == null:
		return 0
	for id in ids:
		var d := dorpeling(id)
		if d != null and d.kan_bevel("werk") and d.geef_bevel(self, "claim", _naast(k.tegel(), d.tegel())):
			d.doel_koe = k
			k.vast = true
			if d.route.is_empty():
				claim_aangekomen(d)
			return 1
	return 0


## Loopbare buurtegel van `t` die het dichtst bij `van` ligt (hij gaat naast de koe staan, niet erin); anders `t`.
func _naast(t: Vector2i, van: Vector2i) -> Vector2i:
	var beste := t
	var bd := INF
	for i in 8:
		var n := t + Vector2i(Raster.DC[i], Raster.DR[i])
		if raster.kan_stap(t.x, t.y, n.x, n.y) and Vector2(n).distance_squared_to(Vector2(van)) < bd:
			bd = Vector2(n).distance_squared_to(Vector2(van))
			beste = n
	return beste


## Dorpeling is bij zijn koe: claimen of loslaten. Een eigen koe zwerft voortaan rond het kampvuur.
func claim_aangekomen(d: Dorpeling) -> void:
	var k := d.doel_koe
	d.doel_koe = null
	if k == null:
		return
	k.vast = false
	if k.eigenaar == 0:
		k.eigenaar = -1
		k.anker = k.tegel()
	else:
		k.eigenaar = 0
		k.anker = kampvuur
	for c in vee:
		if c.moeder == k:
			c.eigenaar = k.eigenaar      # haar kalf gaat mee
	_wijs_weides_toe()       # een eigen koe hoort in een weide als die er is
	k.wacht = 1.0
	koe_geclaimd.emit(k)


## Missie uit spel.json: verloren bij minder dan `verlies.dorpelingen_onder` dorpelingen; gewonnen als elk doel
## gehaald is: `doel.dorpelingen` (>=), `doel.koeien` eigen koeien (>=), `doel.kas_boven` (kas >, origineel `cash>`).
func _check_missie() -> void:
	if uitslag != "":
		return
	var doel: Dictionary = missie.get("doel", {})
	var verlies: Dictionary = missie.get("verlies", {})
	if doel.is_empty() and verlies.is_empty():
		return
	if verlies.has("dorpelingen_onder") and dorpelingen.size() < int(verlies["dorpelingen_onder"]):
		uitslag = "verloren"
	elif not doel.is_empty() and doel_gehaald():
		uitslag = "gewonnen"
	if uitslag != "":
		missie_einde.emit(uitslag)


func doel_gehaald() -> bool:
	var doel: Dictionary = missie.get("doel", {})
	if doel.has("dorpelingen") and dorpelingen.size() < int(doel["dorpelingen"]):
		return false
	if doel.has("koeien") and eigen_koeien() < int(doel["koeien"]):
		return false
	if doel.has("kas_boven") and kas <= int(doel["kas_boven"]):
		return false
	return true


func prijs(soort: StringName) -> int:
	return int(spel.get("prijzen", {}).get(String(soort), 0))


func kan_betalen(soort: StringName) -> bool:
	return kas >= prijs(soort)


## 0..1 tussen de vorige en de volgende tik, voor interpolatie in de view.
func alpha() -> float:
	return clampf(maxf(_acc, 0.0) / tik_dt, 0.0, 1.0)


# ---------------------------------------------------------------- klok, seizoen, weer

func seizoen_duur() -> float:
	return float(spel["seizoen_s"])


func dag_nr() -> int:
	return int(tijd_s / seizoen_duur())    # een seizoen = een dag-nacht (beasts-src)


func dag_t() -> float:
	return fmod(tijd_s, seizoen_duur())


func is_nacht() -> bool:
	return dag_t() >= float(spel["dag_s"])


## Spel-uur voor licht en HUD: dag = 05:00 tot 21:00, nacht = 21:00 tot 05:00.
func uur() -> float:
	return fposmod(5.0 + 24.0 * dag_t() / seizoen_duur(), 24.0)


func seizoen() -> int:
	return dag_nr() % 4


func seizoen_naam() -> String:
	return SEIZOENEN[seizoen()]


## Waarde uit een seizoenstabel, in het laatste kwart zacht naar het volgende seizoen.
func _geblend(tabel: Array) -> float:
	var s := seizoen()
	var f := dag_t() / seizoen_duur()
	return lerpf(tabel[s], tabel[(s + 1) % 4], smoothstep(0.7, 1.0, f))


func sneeuw() -> float:
	return _geblend(SNEEUW)


func droog() -> float:
	return _geblend(DROOG)


func kou() -> float:
	return _geblend(KOU)


## Weerhaak: de view zet er regendeeltjes mee aan of uit. -1 automatisch (deterministisch per dag), 0 uit, 1 aan.
func regent() -> bool:
	if regen_handmatig >= 0:
		return regen_handmatig == 1
	var dag := dag_nr()
	if _hash2(dag, 7) >= REGENKANS[seizoen()]:
		return false
	var start := 0.1 + 0.55 * _hash2(dag, 99)
	var f := dag_t() / seizoen_duur()
	return f >= start and f < start + 0.2


# ---------------------------------------------------------------- bevelen

func dorpeling(id: int) -> Dorpeling:
	for d in dorpelingen:
		if d.id == id:
			return d
	return null


## Dichtstbijzijnde begaanbare tegel (op het eiland) bij `t`; (-1,-1) als er geen is binnen 6 tegels.
func dichtstbij_loopbaar(t: Vector2i) -> Vector2i:
	var beste := Vector2i(-1, -1)
	var bd := 1e9
	for dy in range(-6, 7):
		for dx in range(-6, 7):
			var c := t + Vector2i(dx, dy)
			if raster.in_kaart(c.x, c.y) and raster.loopbaar_v(c) and bereik[raster.idx(c.x, c.y)] == 1:
				var d := float(dx * dx + dy * dy)
				if d < bd:
					bd = d
					beste = c
	return beste


## Tegels rondom `doel`, in ringen van dichtbij naar ver (BFS), voor het uitwaaieren van een groep.
func spreid(doel: Vector2i, n: int) -> Array[Vector2i]:
	var uit: Array[Vector2i] = []
	if not raster.loopbaar_v(doel):
		return uit
	var gezien := {doel: true}
	var rij: Array[Vector2i] = [doel]
	var i := 0
	while i < rij.size() and uit.size() < n:
		var t := rij[i]
		i += 1
		uit.append(t)
		for d in 8:
			var nt := t + Vector2i(Raster.DC[d], Raster.DR[d])
			if gezien.has(nt) or not raster.kan_stap(t.x, t.y, nt.x, nt.y):
				continue
			gezien[nt] = true
			rij.append(nt)
	return uit


## Geef een bevel aan de dorpelingen in `ids`. Lopen kan iedereen; "vecht" en "werk" alleen volwassenen.
## Meerdere uitvoerders waaieren uit over tegels rond het doel. Geeft het aantal dat het bevel kreeg.
## ("vecht" bij een wolf: stenen gooien, zie onder; anders, net als "werk", alleen naar het doel lopen.)
func geef_bevel(ids: Array, soort: String, doel: Vector2i) -> int:
	var uitvoerders: Array[Dorpeling] = []
	for id in ids:
		var d := dorpeling(id)
		if d != null and d.kan_bevel(soort):
			uitvoerders.append(d)
	if uitvoerders.is_empty():
		return 0
	var t := dichtstbij_loopbaar(doel)
	if t.x < 0:
		return 0
	var plekken := spreid(t, uitvoerders.size())
	var over: Array[Dorpeling] = uitvoerders.duplicate()
	var gelukt := 0
	if plekken.is_empty():
		return 0
	# Meer uitvoerders dan vrije plekken (smalle doorgang): de rest deelt de plekken, rond en rond.
	var k := 0
	while not over.is_empty():
		var plek := plekken[k % plekken.size()]
		k += 1
		var beste: Dorpeling = over[0]
		for d in over:
			if d.pos.distance_squared_to(Vector2(plek)) < beste.pos.distance_squared_to(Vector2(plek)):
				beste = d
		over.erase(beste)
		if beste.geef_bevel(self, soort, plek):
			gelukt += 1
	if soort == "vecht":            # een levende wolf bij het doel: stenen gooien (sim/wolf.gd vecht_tik)
		var wf := wolf_bij(doel, 2.5)
		if wf != null:
			for d in uitvoerders:
				if d.bevel.get("soort", "") == "vecht" or d.route.is_empty():
					d.doel_wolf = wf
					d.vecht_kijk = 0.0
	bevel_gegeven.emit(ids, soort, t)
	return gelukt


## Vechtbevel op wolf `wolf_id` (Bestuur: klik op een wolf met een selectie). Alleen volwassenen, niet de bouwer.
func geef_vechtbevel(ids: Array, wolf_id: int) -> int:
	for wf in wolven:
		if wf.id == wolf_id and wf.leeft():
			return geef_bevel(ids, "vecht", wf.tegel())
	return 0


## Levende wolf binnen `straal` tegels van tegel `t` (de dichtste), of null.
func wolf_bij(t: Vector2i, straal: float) -> Wolf:
	var beste: Wolf = null
	var bd := straal
	for wf in wolven:
		var af := wf.pos.distance_to(Vector2(t) + Vector2(0.5, 0.5))
		if wf.leeft() and af <= bd:
			bd = af
			beste = wf
	return beste


## Een koe gaat van de kaart (de wolf heeft haar): wie haar ging melken of claimen stopt, de weides worden herverdeeld.
func verwijder_koe(k: Vee) -> void:
	if not k in vee:
		return
	vee.erase(k)
	for d in dorpelingen:
		if d.melk_koe == k or d.doel_koe == k:
			d.melk_koe = null
			d.doel_koe = null
			d.bezig = 0.0
			d.bevel = {}
			d.route.clear()
	_wijs_weides_toe()
	koe_weg.emit(k)


## Maak een Plan van `soort` op `tegel` (linksboven), `draai` kwartslagen; null als de plek niet kan.
## Staat `soort` al in het bouwmenu: een startsoort, of het gebouw dat hem opent is ergens afgebouwd.
func ontgrendeld(soort: StringName) -> bool:
	if alles_open or soort in START_SOORTEN:
		return true
	if VANAF_MISSIE.has(soort):
		return missie_nr >= int(VANAF_MISSIE[soort])
	if not ONTGRENDEL.has(soort):
		return false
	for p in plannen:
		if p.klaar and p.soort == ONTGRENDEL[soort]:
			return true
	return false


## Poort open of dicht (origineel: "click on the gate to open and shut it"). Dicht blokkeert hij de tegel.
func wissel_poort(p: Plan) -> void:
	if p == null or not p.klaar or p.soort != &"poort":
		return
	p.open = not p.open
	poort_gewisseld.emit(p)


## Dicht poort op tegel `t`: houdt koeien tegen (Vee), dorpelingen lopen er wel door (zij doen hem open en dicht).
func poort_dicht(t: Vector2i) -> bool:
	for p in plannen:
		if p.klaar and p.soort == &"poort" and not p.open and p.tegel == t:
			return true
	return false


## Weides: ingesloten stukken grond achter een poort. Vanaf elke loopbare buurtegel van een poort vullen over loopbare
## tegels zonder door een poort te gaan; blijft dat binnen `WEIDE_MAX` tegels en zit het kampvuur er niet in, dan is het
## een weide. Bij elk afgebouwd hek of poort opnieuw; eigen koeien krijgen de weide met de meeste ruimte per koe.
const WEIDE_MAX := 150
var weides: Array[Dictionary] = []


func _bepaal_weides() -> void:
	weides.clear()
	var gezien := {}
	for p in plannen:
		if not p.klaar or p.soort != &"poort":
			continue
		for i in 8:
			var s := p.tegel + Vector2i(Raster.DC[i], Raster.DR[i])
			if gezien.has(s) or not raster.loopbaar_v(s) or _is_poort(s):
				continue
			var vak := {s: true}
			var rij: Array[Vector2i] = [s]
			var j := 0
			var open := false
			while j < rij.size():
				var t := rij[j]
				j += 1
				if vak.size() > WEIDE_MAX or t == kampvuur:
					open = true
					break
				for k in 4:          # recht: een hek met een schuine naad laat niets door
					var n: Vector2i = t + [Vector2i(1, 0), Vector2i(-1, 0), Vector2i(0, 1), Vector2i(0, -1)][k]
					if vak.has(n) or not raster.loopbaar_v(n) or _is_poort(n):
						continue
					vak[n] = true
					rij.append(n)
			for t in vak:
				gezien[t] = true
			if not open and vak.size() >= 4:
				weides.append(vak)
	_wijs_weides_toe()


func _is_poort(t: Vector2i) -> bool:
	for p in plannen:
		if p.klaar and p.soort == &"poort" and p.tegel == t:
			return true
	return false


func _wijs_weides_toe() -> void:
	for k in vee:
		k.weide = {}
	if weides.is_empty():
		return
	var aantal: Array[int] = []
	for wd in weides:
		aantal.append(0)
	for k in vee:
		if k.eigenaar != 0:
			continue
		var beste := 0
		for i in weides.size():
			if float(weides[i].size()) / (aantal[i] + 1) > float(weides[beste].size()) / (aantal[beste] + 1):
				beste = i
		aantal[beste] += 1
		k.weide = weides[beste]
		k.wacht = minf(k.wacht, 1.0)


func maak_plan(soort: StringName, tegel: Vector2i, draai: int) -> Plan:
	if not BOUWSOORTEN.has(soort):
		return null
	var m: Vector2i = BOUWSOORTEN[soort]
	var p := Plan.new(soort, tegel, posmod(draai, 4), m.x, m.y)
	p.bouwtijd_s = float(spel.get("bouwtijd_s", {}).get(String(soort), 60.0))
	return p if kan_bouwen(p) else null


## Alle tegels van de voetafdruk loopbaar (objecten staan al in het raster), geen pad, vrij van andere plannen en hun
## deuren, en de eigen deurtegel loopbaar en bereikbaar.
func kan_bouwen(p: Plan) -> bool:
	var r := p.afdruk()
	for c in range(r.position.x, r.end.x):
		for rij in range(r.position.y, r.end.y):
			if not raster.loopbaar(c, rij):
				return false
			if raster.soort_naam(c, rij) == "pad" and p.soort != &"poort":   # origineel: niet op een weg bouwen
				return false
	for q in plannen:
		if q.afdruk().intersects(r):
			return false
		if Plan.DEUREN.has(q.soort) and r.has_point(q.deur_tegel()) and p.soort != &"weg":    # niet voor andermans deur (een weg wel)
			return false
	if Plan.DEUREN.has(p.soort):        # de eigen deur moet bereikbaar zijn: daar begint de weg en daar gaan ze naar binnen
		var dt := p.deur_tegel()
		if not raster.loopbaar_v(dt) or bereik[raster.idx(dt.x, dt.y)] == 0:
			return false
		for q in plannen:
			if q.afdruk().has_point(dt) and q.soort != &"weg":     # een geplande weg voor de deur mag
				return false
	return true


## Zet het plan neer en betaal de prijs uit de kas (origineel: bij het bestellen). False als het niet kan of te duur is.
func plan_zet(p: Plan) -> bool:
	if not ontgrendeld(p.soort) or not kan_bouwen(p) or not kan_betalen(p.soort):
		return false
	p.bouwtijd_s = float(spel.get("bouwtijd_s", {}).get(String(p.soort), p.bouwtijd_s))
	kas -= prijs(p.soort)
	plannen.append(p)
	plan_gezet.emit(p)
	return true


## Weg van `van` (de deurtegel) naar het dichtste stuk pad, zoals beasts-src de weg naar de deur meebestelt
## (World.aim). Kortste route over loopbare tegels (BFS, 8 richtingen via kan_stap); elke nieuwe padtegel kost
## `weg_per_tegel` uit de kas. Water en rots worden nooit pad (niet loopbaar); bestaat er geen pad, dan naar het
## kampvuur. Geeft het aantal nieuwe padtegels.
func leg_weg(van: Vector2i) -> int:
	var pad := raster.namen.find("pad")
	var start := dichtstbij_loopbaar(van)
	if start.x < 0 or pad < 0:
		return 0
	var vorige := {start: start}
	var rij: Array[Vector2i] = [start]
	var doel := Vector2i(-1, -1)
	var i := 0
	while i < rij.size():
		var t := rij[i]
		i += 1
		if raster.soort[raster.idx(t.x, t.y)] == pad or (t - kampvuur).length_squared() <= 2:
			doel = t
			break
		for d in 8:
			var n := t + Vector2i(Raster.DC[d], Raster.DR[d])
			if vorige.has(n) or not raster.kan_stap(t.x, t.y, n.x, n.y):
				continue
			vorige[n] = t
			rij.append(n)
	if doel.x < 0:
		return 0
	var nieuw := 0
	var t := doel
	while true:
		var ix := raster.idx(t.x, t.y)
		if raster.soort[ix] != pad:
			raster.soort[ix] = pad
			nieuw += 1
		if t == start:
			break
		t = vorige[t]
	kas = maxi(0, kas - nieuw * int(spel.get("weg_per_tegel", 0)))
	wegen_veranderd.emit()      # ook zonder nieuwe tegels: de stoep naar de deur (view/wegen.gd)
	return nieuw


## Afgebouwd gebouw waarvan de voetafdruk `t` bevat, of null.
func gebouw_op(t: Vector2i) -> Plan:
	for p in plannen:
		if p.klaar and p.afdruk().has_point(t):
			return p
	return null


## Gilde (GILDEN): volwassen mannen uit `ids` zonder rol lopen naar de deur van het afgebouwde gilde en krijgen daar
## tegen `<rol>.prijs` de rol. Bouwersgilde (missie 1, origineel "bouwer 2x sneller"): bouwt `bouwer.tempo` keer zo
## snel en vecht niet. Voetvolkgilde (missie 3): voetsoldaat, vecht met het zwaard (sim/wolf.gd) en boert niet meer.
## Hoogstens `gilde_max_leden` per gilde, wie onderweg is telt mee; zoveel als er plaats en kas is. Geeft het aantal.
func geef_gildebevel(ids: Array, gilde: Plan) -> int:
	if gilde == null or not gilde.klaar or not GILDEN.has(gilde.soort):
		return 0
	var rol: String = GILDEN[gilde.soort]
	var prijs_rol := int(spel[rol]["prijs"])
	var plaats := gilde_plaats(gilde)
	var n := 0
	for id in ids:
		if plaats <= 0 or kas < prijs_rol * (n + 1):
			break
		var d := dorpeling(id)
		if d != null and d.volwassen() and d.geslacht == "man" and d.rol == "" \
				and d.geef_bevel(self, "gilde", dichtstbij_loopbaar(gilde.deur_tegel())):
			d.gilde = gilde
			n += 1
			plaats -= 1
			if d.route.is_empty() and d.gilde != null:
				gilde_aangekomen(d)
	return n


## Nog vrije plaatsen in `gilde`: `gilde_max_leden` min de leden (Dorpeling.lid) en wie erheen loopt.
func gilde_plaats(gilde: Plan) -> int:
	var n := 0
	for d in dorpelingen:
		if d.lid == gilde or d.gilde == gilde:
			n += 1
	return int(spel.get("gilde_max_leden", 6)) - n


func kan_bouwer_worden() -> bool:
	return kas >= int(spel["bouwer"]["prijs"])


func gilde_aangekomen(d: Dorpeling) -> void:
	if d.gilde == null:
		return
	var g := d.gilde
	d.gilde = null
	var rol: String = GILDEN.get(g.soort, "")
	if rol == "" or d.rol != "" or kas < int(spel[rol]["prijs"]) or gilde_plaats(g) <= 0:
		return
	kas -= int(spel[rol]["prijs"])
	d.rol = rol
	d.lid = g
	Leven.pas_gezondheid_aan(self, d)
	rol_veranderd.emit(d)


## Het dichtste afgebouwde gebouw van `soort` bij tegel `t`, of null.
func dichtste_gebouw(soort: StringName, t: Vector2i) -> Plan:
	var beste: Plan = null
	var bd := INF
	for p in plannen:
		if p.klaar and p.soort == soort:
			var af := Vector2(p.deur_tegel()).distance_squared_to(Vector2(t))
			if af < bd:
				bd = af
				beste = p
	return beste


func plan_op(t: Vector2i) -> Plan:
	for p in plannen:
		if not p.klaar and p.afdruk().has_point(t):
			return p
	return null


## Stuur volwassenen in `ids` naar het plan om te bouwen (elk naar een eigen tegel van de voetafdruk). Geeft het aantal.
func geef_bouwbevel(ids: Array, p: Plan) -> int:
	var r := p.afdruk()
	var tegels: Array[Vector2i] = []
	for c in range(r.position.x, r.end.x):
		for rij in range(r.position.y, r.end.y):
			tegels.append(Vector2i(c, rij))
	var n := 0
	for id in ids:
		var d := dorpeling(id)
		if d != null and d.geef_bevel(self, "werk", tegels[n % tegels.size()]):
			d.werk_plan = p
			n += 1
	return n


## Het dichtste onafgebouwde plan van dezelfde soort binnen 8 tegels (een rij hek bouwt zo door), of null.
func _volgend_plan(p: Plan) -> Plan:
	var beste: Plan = null
	var bd := 64.0
	for q in plannen:
		if q == p or q.klaar or q.soort != p.soort:
			continue
		var af := Vector2(q.tegel).distance_squared_to(Vector2(p.tegel))
		if af <= bd:
			bd = af
			beste = q
	return beste


## Weg af: de tegel wordt pad (view/wegen.gd tekent hem bij wegen_veranderd), het plan gaat uit de lijst (een weg
## is grond, geen gebouw) en de werkers bouwen door aan het volgende stuk weg, zoals bij hek.
func _weg_af(p: Plan) -> void:
	var pad := raster.namen.find("pad")
	if pad >= 0:
		raster.soort[raster.idx(p.tegel.x, p.tegel.y)] = pad
	plannen.erase(p)
	var volgende := _volgend_plan(p)
	for d in dorpelingen:
		if d.werk_plan == p:
			d.werk_plan = null
			d.bouwt = false
			if volgende != null:
				geef_bouwbevel([d.id], volgende)
	wegen_veranderd.emit()
	plan_klaar.emit(p)


## Plan af: de voetafdruk wordt blokkerend en de werkers lopen weg van de nieuwe muren.
func _rond_af(p: Plan) -> void:
	p.klaar = true
	if p.soort == &"weg":
		_weg_af(p)
		return
	var r := p.afdruk()
	if WINKELS.has(p.soort):
		p.voorraad = int(spel["economie"]["winkel_start"])
	if p.soort in NIET_BLOKKEREND:
		for c in range(r.position.x, r.end.x):
			for rij in range(r.position.y, r.end.y):
				akkers[Vector2i(c, rij)] = 0.0
		for d in dorpelingen:
			if d.werk_plan == p:
				d.werk_plan = null
				d.bouwt = false
		plan_klaar.emit(p)
		return
	for c in range(r.position.x, r.end.x):
		for rij in range(r.position.y, r.end.y):
			raster.blok[raster.idx(c, rij)] = 1
	var volgende := _volgend_plan(p)
	for d in dorpelingen:
		var bouwde := d.werk_plan == p
		if bouwde:
			d.werk_plan = null
			d.bouwt = false
		# eerst de nieuwe muren uit (ook zwervers op de voetafdruk): vanaf een geblokkeerde tegel vindt Router niets,
		# en wie daar bleef staan kreeg nooit meer een route (2026-10-29: bouwers vast in het kippenhok)
		if r.has_point(d.tegel()):
			var t := dichtstbij_loopbaar(d.tegel())
			if t.x >= 0:
				d.zet_tegel(t)
				d.route.clear()
				d.bevel = {}
		if bouwde and volgende != null:
			geef_bouwbevel([d.id], volgende)
	bereik = Router.bereikbaar(raster, _vrij_naast(kampvuur))   # nieuwe muren kunnen een doorgang afsluiten
	if Plan.DEUREN.has(p.soort):
		leg_weg(p.deur_tegel())
	if p.soort == &"kippenhok":
		_maak_kippen(p)
	if p.soort == &"poort":
		raster.blok[raster.idx(p.tegel.x, p.tegel.y)] = 0     # dorpelingen lopen erdoor; koeien kijken naar poort_dicht
		bereik = Router.bereikbaar(raster, _vrij_naast(kampvuur))
	if p.soort == &"poort" or p.soort == &"hek":
		_bepaal_weides()
	plan_klaar.emit(p)
