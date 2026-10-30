extends Node
## Scenario `deur` (main.gd --scenario=deur): een gebouw met een deur staat bij het dorp (--gebouw=hut|kippenhok|molen|
## melkerij|gereedschapsloods, --draai=0..3, camera --pitch=30 --afstand=9); een volwassene loopt vanaf 4 tegels voor de deur naar binnen ("huis"), blijft
## 3 s binnen en loopt daarna weer weg. Frames: --write-movie out/deur/f.png --fixed-fps 10 --quit-after 120.

var m: Node            ## main.gd
var t := 0.0
var stap := 0
var p: Plan
var d: Dorpeling
var weg := Vector2i.ZERO


func start(main: Node) -> Node:
	m = main
	var w: Wereld = m.w
	var opt := {}
	for a in OS.get_cmdline_user_args():
		if a.begins_with("--") and "=" in a:
			opt[a.substr(2).get_slice("=", 0)] = a.get_slice("=", 1)
	var soort := StringName(opt.get("gebouw", "hut"))
	var draai := int(opt.get("draai", "0"))
	w.alles_open = true
	for r in 10:
		for dy in range(-r, r + 1):
			for dx in range(-r, r + 1):
				if p == null and maxi(absi(dx), absi(dy)) == r:
					p = w.maak_plan(soort, Vector2i(98, 60) + Vector2i(dx, dy), draai)
	if p == null or not w.plan_zet(p):
		push_error("deur: geen plek voor %s" % soort)
		return self
	w._rond_af(p)
	for x in w.dorpelingen:
		if x.volwassen():
			d = x
			break
	var dt := p.deur_tegel()
	weg = w.dichtstbij_loopbaar(dt + p.deur_richting() * 4)
	d.zet_tegel(weg)
	d.anker = weg
	w.tempo = 1.0
	var mid: Vector2 = p.deur_punt(w.tegel_m)
	var r2 := Vector2(p.deur_richting())
	var yaw := atan2(r2.x, r2.y) + 0.7
	m.cam.zet_direct(Vector3(mid.x, m.view.terrein.hoogte_op(mid.x, mid.y), mid.y) + Vector3(r2.x, 0, r2.y) * 1.5, yaw, deg_to_rad(float(opt.get("pitch", "30"))), float(opt.get("afstand", "9")))
	print("[deur] %s draai %d: deurtegel %s, deur_punt %s, richting %s" % [soort, draai, dt, mid, p.deur_richting()])
	return self


func _process(dt: float) -> void:
	if d == null:
		return
	t += dt
	var w: Wereld = m.w
	if stap == 0 and t >= 0.5:
		d.geef_bevel(w, "huis", w.dichtstbij_loopbaar(p.deur_tegel()))
		stap = 1
	elif stap == 1 and d.binnen:
		print("[deur] binnen op t=%.1f, sim-plek %s" % [t, d.pos])
		stap = 2
		t = 0.0
	elif stap == 2 and t >= 5.0:
		d.geef_bevel(w, "loop", weg)
		print("[deur] naar buiten op t=%.1f" % t)
		stap = 3
