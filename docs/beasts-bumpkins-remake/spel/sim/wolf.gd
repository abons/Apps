class_name Wolf
extends RefCounted
## Een wolf in de sim (missie 2, klasse 104): positie in tegels (continu, zoals Dorpeling en Vee), hp en een toestand.
## Port van beasts-src `Beast` (Kind.WOLF): ROAM -> HUNT -> ATTACK -> DYING -> DEAD.
##   ROAM   zwerft rond zijn startplek en kijkt elke `kijk_s` of er een prooi binnen `zicht` is die hij kan bereiken:
##          een koe of een dorpeling die buiten staat (_zoek_prooi: afstand x prooi_voorkeur x zwakte).
##   HUNT   rent naar de prooi (route elke `kijk_s` opnieuw); verliest haar boven zicht x `verlies` (beasts-src LOSE 1,4).
##   ATTACK binnen `bereik`: elke `slag_s` een beet op STRIKE_AT van de slag. Koe: na `koe_beten` beten weg (uit `vee`).
##          Dorpeling: `beet_schade` (Dorpeling.raak, sim/leven.gd), daarna `beet_pauze_s` niet bijten (tussenpozen).
##   DYING  hp 0 (stenen of zwaarden van dorpelingen): valt om in `sterf_s`; DEAD ligt er `rot_s`, dan van de kaart.
## Een dichte poort laat hij niet door (zoals een koe): een koe in een gesloten weide is onbereikbaar ("omheining helpt").
## Gebruiker 2026-10-30: wolven pakken geen kinderen weg, maar bijten dorpelingen en kunnen ze doden, ook kinderen;
## kinderen rennen weg (sim/leven.gd vlucht). Wolf-generator: missies.<nr>.wolf_generator (tik_alle, _generatoren).
## Alle getallen in spel.json `wolf`. Vechten (stenen gooien) staat hier ook: `vecht_tik` voor de dorpeling.

const ROAM := &"zwerft"
const HUNT := &"jaagt"
const ATTACK := &"valt_aan"
const DYING := &"sterft"
const DEAD := &"dood"
const STRIKE_AT := 0.42         ## beasts-src Beast.STRIKE_AT: waar in de slag de beet valt

var id := 0
var soort := &"wolf"            ## &"wolf" | &"donkere_wolf" (objecten.json 104 "soorten", sex 29); zelfde gedrag, eigen glb
var pos := Vector2.ZERO
var vorige := Vector2.ZERO
var route: Array[Vector2] = []
var anker := Vector2i.ZERO
var toestand := ROAM
var hp := 8
var hp_max := 8
var prooi = null                ## Vee of Dorpeling
var beten := 0                  ## beten op de huidige prooi
var pauze := 0.0                ## s tot hij weer bijt na een beet op een dorpeling (beet_pauze_s)
var generator := -1             ## index in missie.wolf_generator, -1 = uit de kaart
var slag := 0.0                 ## 0..1 in de aanval; in DYING/DEAD de voortgang van omvallen/vergaan
var wacht := 2.0
var kijk := 0.0                 ## s tot hij weer om zich heen kijkt (prooi zoeken, route bijwerken)
var rust := 0.0                 ## s verzadigd na een koe: zwerft alleen
var geraakt := 0.0              ## s sinds de laatste steen (view: hp-balkje), groot = lang geleden
var snelheid_mps := 0.0
var richting := Vector2(0, 1)   ## laatste looprichting (view: kop naar voren)


func leeft() -> bool:
	return toestand != DYING and toestand != DEAD


func tegel() -> Vector2i:
	return Vector2i(int(floor(pos.x)), int(floor(pos.y)))


func zet_tegel(t: Vector2i) -> void:
	pos = Vector2(t) + Vector2(0.5, 0.5)
	vorige = pos


static func _cfg(w: Wereld) -> Dictionary:
	return w.spel["wolf"]


## Wolven uit de kaart (Wereld._kaart_wolven: {tegel, soort} van klasse 104; een kale Vector2i = gewone wolf).
static func uit_kaart(w: Wereld, tegels: Array) -> Array[Wolf]:
	var uit: Array[Wolf] = []
	var c := _cfg(w)
	for kw in tegels:
		var t: Vector2i = kw["tegel"] if kw is Dictionary else kw
		var v := w.dichtstbij_loopbaar(t)
		if v.x < 0:
			continue
		var wf := Wolf.new()
		wf.id = uit.size() + 1
		if kw is Dictionary:
			wf.soort = kw.get("soort", &"wolf")
		wf.zet_tegel(v)
		wf.anker = v
		wf.hp = int(c["hp"])
		wf.hp_max = wf.hp
		wf.geraakt = 99.0
		wf.wacht = w.rng.randf_range(0.5, 3.0)
		wf.kijk = w.rng.randf_range(0.0, float(c["kijk_s"]))
		uit.append(wf)
	return uit


## Elke tik vanuit Wereld.tik: alle wolven, dode opruimen, en wie niets omhanden heeft verdedigt het vee.
static func tik_alle(w: Wereld, dt: float) -> void:
	_generatoren(w, dt)
	for wf in w.wolven.duplicate():
		wf.tick(w, dt)
		if wf.toestand == DEAD and wf.slag >= 1.0:
			w.wolven.erase(wf)
			w.wolf_weg.emit(wf)
	_verweer(w, dt)


func tick(w: Wereld, dt: float) -> void:
	var c := _cfg(w)
	vorige = pos
	snelheid_mps = 0.0
	geraakt += dt
	if toestand == DYING:
		slag += dt / float(c["sterf_s"])
		if slag >= 1.0:
			toestand = DEAD
			slag = 0.0
		return
	if toestand == DEAD:
		slag = minf(1.0, slag + dt / float(c["rot_s"]))
		return
	if not w.raster.loopbaar_v(tegel()):     # vangnet: nooit vast in een nieuw gebouw, hek of dichte poort
		var t := w.dichtstbij_loopbaar(tegel())
		if t.x >= 0:
			zet_tegel(t)
			route.clear()
	rust = maxf(0.0, rust - dt)
	pauze = maxf(0.0, pauze - dt)
	if prooi != null and _prooi_weg(w):
		_laat_los()
	kijk -= dt
	match toestand:
		ROAM:
			if kijk <= 0.0:
				kijk = float(c["kijk_s"])
				if rust <= 0.0:
					var k := _zoek_prooi(w)
					if k != null:
						prooi = k
						beten = 0
						toestand = HUNT
						kijk = 0.0
			if toestand == ROAM:
				if route.is_empty():
					_zwerf(w, dt)
				else:
					_loop(w, dt, float(c["zwerf_mps"]))
				return
		ATTACK:
			if _afstand() > float(c["bereik"]):
				toestand = HUNT
				kijk = 0.0
			else:
				route.clear()
				_kijk_naar(prooi.pos)
				if pauze > 0.0:              # net gebeten: even niet (bijten met tussenpozen)
					slag = 0.0
					return
				var voor := slag
				slag += dt / float(c["slag_s"])
				if voor < STRIKE_AT and slag >= STRIKE_AT:
					beten += 1
					if prooi is Dorpeling:
						var d: Dorpeling = prooi
						d.raak(w, float(c["beet_schade"]), Leven.OORZAAK_WOLF)
						if not d.leeft():
							_laat_los()
							rust = float(c["rust_s"])
							return
						pauze = float(c["beet_pauze_s"])
						slag = 0.0
						return
					if beten >= int(c["koe_beten"]):
						w.verwijder_koe(prooi)
						_laat_los()
						rust = float(c["rust_s"])
						return
				if slag >= 1.0:
					slag = 0.0
				return
	if toestand == HUNT:
		var af := _afstand()
		if af <= float(c["bereik"]):
			toestand = ATTACK
			slag = 0.0
			route.clear()
			return
		if kijk <= 0.0:
			kijk = float(c["kijk_s"])
			if af > float(c["zicht"]) * float(c["verlies"]):
				_laat_los()
				return
			var r := pad(w, tegel(), prooi.tegel(), int(ceil(float(c["zicht"]) * float(c["verlies"]))) + 2)
			if r.is_empty() and tegel() != prooi.tegel():
				_laat_los()         # onbereikbaar geworden (poort ging dicht)
				return
			route.clear()
			for rt in r:
				route.append(Vector2(rt) + Vector2(0.5, 0.5))
			if not route.is_empty():
				route[route.size() - 1] = prooi.pos   # het laatste stuk recht op de koe af
		_loop(w, dt, float(c["snelheid_mps"]))


func _afstand() -> float:
	return pos.distance_to(prooi.pos) if prooi != null else INF


## De prooi is er niet meer: koe opgegeten of dood, dorpeling dood of binnen (onzichtbaar is onaanraakbaar).
func _prooi_weg(w: Wereld) -> bool:
	if prooi is Vee:
		return not prooi in w.vee
	if prooi is Dorpeling:
		return not prooi in w.dorpelingen or prooi.binnen
	return true


func _laat_los() -> void:
	prooi = null
	beten = 0
	slag = 0.0
	toestand = ROAM
	route.clear()
	wacht = 1.0


func _kijk_naar(p: Vector2) -> void:
	var d := p - pos
	if d.length() > 0.01:
		richting = d.normalized()


## Prooi binnen `zicht` die hij kan bereiken, met de laagste score = afstand x prooi_voorkeur[koe|kind|oud|volwassen]
## x lerp(zwak_voorkeur, 1, gezondheid/max): vooral kinderen en vee (hint 2-1), een gewonde eerder. Elke koe telt (wild
## of eigen), maar een koe in een weide achter een dichte poort haalt hij niet: daar is geen pad heen. Een dorpeling in
## een hut ook niet.
func _zoek_prooi(w: Wereld) -> Object:
	var c := _cfg(w)
	var zicht := float(c["zicht"])
	var vk: Dictionary = c.get("prooi_voorkeur", {})
	var kandidaten: Array = []
	for k in w.vee:
		var af := pos.distance_to(k.pos)
		if af <= zicht:
			kandidaten.append([af * float(vk.get("koe", 1.0)), k])
	for d in w.dorpelingen:
		if d.binnen:
			continue
		var af := pos.distance_to(d.pos)
		if af <= zicht:
			var zwak := lerpf(float(c.get("zwak_voorkeur", 1.0)), 1.0, d.gezondheid / maxf(1.0, d.gezondheid_max))
			kandidaten.append([af * float(vk.get(d.leeftijd, 1.0)) * zwak, d])
	kandidaten.sort_custom(func(a, b): return a[0] < b[0])
	for kd in kandidaten:
		var k = kd[1]
		if k.tegel() == tegel() or not pad(w, tegel(), k.tegel(), int(ceil(zicht * float(c["verlies"]))) + 2).is_empty():
			return k
	return null


func _zwerf(w: Wereld, dt: float) -> void:
	wacht -= dt
	if wacht > 0.0:
		return
	var c := _cfg(w)
	wacht = w.rng.randf_range(float(c["zwerf_wacht"][0]), float(c["zwerf_wacht"][1]))
	var straal := int(c["zwerf_straal"])
	for _i in 8:
		var t := anker + Vector2i(w.rng.randi_range(-straal, straal), w.rng.randi_range(-straal, straal))
		if t == tegel() or not w.raster.loopbaar_v(t):
			continue
		var r := pad(w, tegel(), t, straal * 2 + 2)
		if r.is_empty():
			continue
		route.clear()
		for rt in r:
			route.append(Vector2(rt) + Vector2(0.5, 0.5))
		return


func _loop(w: Wereld, dt: float, mps: float) -> void:
	var v := mps / w.tegel_m
	var rest := dt
	while rest > 1e-6 and not route.is_empty():
		var d := route[0] - pos
		var afstand := d.length()
		var stap := v * rest
		snelheid_mps = mps
		if afstand > 0.001:
			richting = d / afstand
		if afstand <= stap:
			pos = route[0]
			route.pop_front()
			rest -= afstand / v
		else:
			pos += d / afstand * stap
			rest = 0.0


## Tegelroute van `van` naar `naar` (zonder `van`), BFS over acht richtingen binnen `straal` tegels rond `van`, niet door
## een dichte poort (die houdt wolven tegen zoals koeien). Leeg als er geen is. Begrensd, dus goedkoop: een koe achter
## een dichte poort kost een volle zoektocht van hoogstens (2 straal + 1)^2 tegels.
static func pad(w: Wereld, van: Vector2i, naar: Vector2i, straal: int) -> Array[Vector2i]:
	var uit: Array[Vector2i] = []
	if van == naar or not w.raster.loopbaar_v(naar):
		return uit
	var dicht := {}
	for p in w.plannen:
		if p.klaar and p.soort == &"poort" and not p.open:
			dicht[p.tegel] = true
	if dicht.has(naar):
		return uit
	var vorige := {van: van}
	var rij: Array[Vector2i] = [van]
	var i := 0
	while i < rij.size():
		var t := rij[i]
		i += 1
		if t == naar:
			var stap := naar
			while stap != van:
				uit.push_front(stap)
				stap = vorige[stap]
			return uit
		for k in 8:
			var n := t + Vector2i(Raster.DC[k], Raster.DR[k])
			if vorige.has(n) or absi(n.x - van.x) > straal or absi(n.y - van.y) > straal:
				continue
			if dicht.has(n) or not w.raster.kan_stap(t.x, t.y, n.x, n.y):
				continue
			if n.x != t.x and n.y != t.y and (dicht.has(Vector2i(n.x, t.y)) or dicht.has(Vector2i(t.x, n.y))):
				continue        # niet schuin langs een dichte poort glippen
			vorige[n] = t
			rij.append(n)
	return uit


# ---------------------------------------------------------------- wolven komen terug: generators

## Origineel: wezens komen uit een generator (klasse 171 met 0xE7 = 104, subtype 23 = wolf; ../missies.md "Antwoorden").
## Per missie in spel.json `missies.<nr>.wolf_generator` = [{tegel: [x, y], start, max, interval_s}]: `start` wolven bij
## de eerste tik, daarna elke `interval_s` een nieuwe zolang er minder dan `max` levende van die generator zijn.
## M2.MIS heeft geen wolf-generator (alleen de koe-generator), dus daar komen ze niet terug.
static func _generatoren(w: Wereld, dt: float) -> void:
	var gens: Array = w.missie.get("wolf_generator", [])
	if gens.is_empty():
		return
	var eerste := w.wolf_gen_t.size() < gens.size()
	while w.wolf_gen_t.size() < gens.size():
		w.wolf_gen_t.append(0.0)
	for gi in gens.size():
		var g: Dictionary = gens[gi]
		var t := Vector2i(int(g["tegel"][0]), int(g["tegel"][1]))
		if eerste:
			for _i in int(g.get("start", 0)):
				spawn(w, t, gi)
		var levend := 0
		for wf in w.wolven:
			if wf.generator == gi and wf.leeft():
				levend += 1
		if levend >= int(g.get("max", 1)):
			w.wolf_gen_t[gi] = 0.0
			continue
		w.wolf_gen_t[gi] += dt
		if w.wolf_gen_t[gi] >= float(g.get("interval_s", 120.0)):
			w.wolf_gen_t[gi] = 0.0
			spawn(w, t, gi)


## Nieuwe wolf op (de dichtste loopbare tegel bij) `t`, zwerft daar rond. Null als er geen plek is.
static func spawn(w: Wereld, t: Vector2i, gi := -1) -> Wolf:
	var v := w.dichtstbij_loopbaar(t)
	if v.x < 0:
		return null
	var c := _cfg(w)
	var wf := Wolf.new()
	for o in w.wolven:
		w.wolven_gemaakt = maxi(w.wolven_gemaakt, o.id)
	w.wolven_gemaakt += 1
	wf.id = w.wolven_gemaakt
	wf.zet_tegel(v)
	wf.anker = v
	wf.hp = int(c["hp"])
	wf.hp_max = wf.hp
	wf.geraakt = 99.0
	wf.generator = gi
	wf.wacht = w.rng.randf_range(0.5, 3.0)
	w.wolven.append(wf)
	w.wolf_erbij.emit(wf)
	return wf


# ---------------------------------------------------------------- gevecht: dorpelingen gooien stenen

## Een steen raakt: schade, en bij 0 hp valt hij om (beasts-src Beast.hurt/kill).
func raak(w: Wereld, schade: int) -> void:
	if not leeft():
		return
	hp = maxi(0, hp - schade)
	geraakt = 0.0
	w.wolf_geraakt.emit(self)
	if hp <= 0:
		toestand = DYING
		slag = 0.0
		route.clear()
		prooi = null
		w.wolf_dood.emit(self)


## Vechtende dorpeling (Dorpeling.doel_wolf): buiten `steen_bereik` loopt hij erheen (route elke `kijk_s` opnieuw, de wolf
## beweegt); binnen bereik blijft hij staan en gooit elke `worp_s` een steen (munitie oneindig: hurken, rapen, gooien met
## de clip aanval_steen). De worp begint op worp_t 0 (signaal `steen_gegooid`, de view start de clip) en raakt op
## `raak_s` (loslaten op release_s plus de vlucht) als de wolf dan nog binnen bereik x 1,5 is.
## Geeft true als hij deze tik stond te gooien (Dorpeling.tick doet dan niets meer), false als hij moet lopen.
static func vecht_tik(w: Wereld, d: Dorpeling, dt: float) -> bool:
	var wf := d.doel_wolf
	var c := _cfg(w)
	if wf == null or not wf.leeft() or not wf in w.wolven:
		d.doel_wolf = null
		d.worp_t = -1.0
		d.route.clear()
		d.anker = d.tegel()        # blijft in de buurt, zoals na een vechtbevel
		d.bevel = {}
		d.wacht = 1.0
		return true
	# voetsoldaat (missie 3): zwaard van dichtbij, spel.json `voetsoldaat` (beasts-src spearman: schade 6, slag 0,8 s);
	# zelfde lus als de steen, alleen bereik, ritme, schade en het signaal verschillen
	var zwaard := d.rol == "voetsoldaat"
	var z: Dictionary = w.spel.get("voetsoldaat", {}) if zwaard else {}
	var bereik := float(z["bereik"]) if zwaard else float(c["steen_bereik"])
	var af := d.pos.distance_to(wf.pos)
	if d.worp_t >= 0.0:            # midden in een worp of slag: afmaken
		var voor := d.worp_t
		d.worp_t += dt
		var raak_s := float(z["raak_s"]) if zwaard else float(c["raak_s"])
		if voor < raak_s and d.worp_t >= raak_s and af <= bereik * 1.5:
			wf.raak(w, int(z["schade"]) if zwaard else int(c["steen_schade"]))
		if d.worp_t >= (float(z["slag_s"]) if zwaard else float(c["worp_s"])):
			d.worp_t = -1.0
		return true
	if af <= bereik:
		d.route.clear()
		d.worp_t = 0.0
		if zwaard:
			w.zwaard_slag.emit(d, wf)
		else:
			w.steen_gegooid.emit(d, wf)
		return true
	d.vecht_kijk -= dt
	if d.route.is_empty() or d.vecht_kijk <= 0.0:
		d.vecht_kijk = float(c["kijk_s"])
		var r := Router.route(w.raster, d.tegel(), _naast_wolf(w, wf, d))
		d.route.clear()
		if not r.is_empty():
			d.route = Router.glad(w.raster, d.pos, r)
		if d.route.is_empty():
			d.route.append(wf.pos)       # zelfde tegel: recht erheen
	return false


static func _naast_wolf(w: Wereld, wf: Wolf, d: Dorpeling) -> Vector2i:
	var t := wf.tegel()
	if w.raster.loopbaar_v(t):
		return t
	var v := w.dichtstbij_loopbaar(t)
	return v if v.x >= 0 else d.tegel()


## Zelf verdedigen (optioneel, eenvoudig): een volwassene zonder iets omhanden (geen bouwer, geen kind) die een levende wolf
## binnen `verweer_straal` tegels ziet die op een koe jaagt of haar aanvalt, gaat zelf stenen gooien. Elke `kijk_s`.
static var _verweer_t := 0.0


static func _verweer(w: Wereld, dt: float) -> void:
	_verweer_t += dt
	var c := _cfg(w)
	if _verweer_t < float(c["kijk_s"]):
		return
	_verweer_t = 0.0
	var straal := float(c["verweer_straal"])
	for wf in w.wolven:
		if not wf.leeft() or (wf.toestand != HUNT and wf.toestand != ATTACK):
			continue
		for d in w.dorpelingen:
			if d.ledig() and d.kan_bevel("vecht") and not d.slaapt and d.pos.distance_to(wf.pos) <= straal:
				d.doel_wolf = wf
				d.worp_t = -1.0
				d.vecht_kijk = 0.0
	_verweer_soldaten(w)


## Voetsoldaten (missie 3) zonder iets omhanden vallen elke levende wolf binnen `voetsoldaat.verweer_straal` aan, ook een
## die alleen rondzwerft: daar zijn ze voor (eigen keuze; het origineel is niet nagekeken).
static func _verweer_soldaten(w: Wereld) -> void:
	var straal := float(w.spel.get("voetsoldaat", {}).get("verweer_straal", 0.0))
	for d in w.dorpelingen:
		if d.rol != "voetsoldaat" or not d.ledig() or d.slaapt:
			continue
		var beste: Wolf = null
		var bd := straal
		for wf in w.wolven:
			var af := d.pos.distance_to(wf.pos)
			if wf.leeft() and af <= bd:
				bd = af
				beste = wf
		if beste != null:
			d.doel_wolf = beste
			d.worp_t = -1.0
			d.vecht_kijk = 0.0
