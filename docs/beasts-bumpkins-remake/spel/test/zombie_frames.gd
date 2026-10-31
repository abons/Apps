extends SceneTree
## Spelframes van de zombie (missie 4, assets/zombie.glb uit modellen/bumpkin/zombie.py). Met venster:
##   "$G" --path . -s test/zombie_frames.gd -- --missie=4 --scenario=zombieframes --seizoen=zomer --uur=12 --uit=out/zombie_frames
## Een zombie (niet de bewaker op 47,12) krijgt een man naast zich: de camera volgt hem van dichtbij terwijl hij jaagt en
## bijt (de kop vliegt), daarna valt hij om. De andere wezens staan stil. PNG per opname: <uit>/z_<nr>_<toestand>.png.

const AFSTAND := 4.0
const HELLING := 24.0


func _initialize() -> void:
	_draai.call_deferred()


func _draai() -> void:
	var uit := "out/zombie_frames"
	for a in OS.get_cmdline_user_args():
		if a.begins_with("--uit="):
			uit = a.substr(6)
	DirAccess.make_dir_recursive_absolute(ProjectSettings.globalize_path("res://" + uit))
	var main: Node = load("res://main.tscn").instantiate()
	root.add_child(main)
	for i in 20:
		await process_frame
	var w: Wereld = main.w
	var z: Wolf = null
	for wf in w.wolven:
		if wf.soort == &"zombie" and wf.kaart_tegel != Vector2i(47, 12) and z == null:
			z = wf
		else:
			wf.cfg(w)["passief"] = true            # de rest staat stil
	var man: Dorpeling = null
	for d in w.dorpelingen:
		if d.geslacht == "man" and d.volwassen():
			man = d
			break
	var zt := z.tegel()
	man.zet_tegel(zt + Vector2i(3, 1))
	man.route.clear()
	man.bevel = {}
	man.anker = man.tegel()
	man.wacht = 999.0
	man.pos = z.pos + Vector2(0.7, 0.0)              # binnen bereik (0,9 tegel): meteen aanvallen
	man.vorige = man.pos
	z.prooi = man
	z.toestand = Wolf.ATTACK
	z.slag = 0.0
	var cam: Camera3D = main.cam
	var nr := 0
	var yaw := 0.6
	for i in 420:
		var p: Vector3 = main.view.wolven.wolf_pos(z.id)
		if p.is_finite():
			cam.zet_direct(p + Vector3(0, 0.5, 0), yaw, deg_to_rad(HELLING), AFSTAND)
		if i == 360:
			z.raak(w, 100000)
		await process_frame
		if i % 20 == 0:
			print("[zf] ", i, " z=", z.pos, " man=", man.pos, " ", z.toestand, " slag=", snappedf(z.slag, 0.01), " pauze=", snappedf(z.pauze, 0.1), " t=", snappedf(w.tijd_s, 0.1))
		if (i < 40 or (i > 310 and i < 350)) and i % 2 == 0 or i % 8 == 0:
			var img := root.get_texture().get_image()
			var pad := "res://%s/z_%03d_%s.png" % [uit, nr, String(z.toestand)]
			img.save_png(pad)
			nr += 1
	print("[zombie_frames] ", nr, " frames in ", uit)
	quit()
