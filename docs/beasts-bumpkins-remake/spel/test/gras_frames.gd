extends SceneTree
## Grasvarianten naast elkaar (lokaal/concept/gras_vergelijk.html): dezelfde M1-startbeelden per variant
## (view/gras_varianten.gd). Met venster (niet headless), per variant een run:
##   "$G" --path . -s test/gras_frames.gd -- --missie=1 --scenario=m1frames --seizoen=zomer --uur=12 --gras=b --uit=out/gras
## Schrijft <uit>/<variant>_start.png (main.gd START_*, met hud) en <variant>_dicht.png (kampvuur met dorpelingen).
## Seizoensgras (view/gras_seizoen.gd, standaard zonder --gras): `--naam=seizoen_lente` voor de bestandsnaam en eventueel
## `--seizoen_vast=2.85` (seizoen + voortgang, hier herfst op 85 % = midden in de overgang naar winter; licht volgt --uur):
##   "$G" --path . -s test/gras_frames.gd -- --missie=1 --scenario=m1frames --seizoen=herfst --uur=12 --seizoen_vast=2.85 --naam=seizoen_overgang --uit=out/gras

const OPNAMES := [
	# naam, yaw, helling (graden), afstand (m), hud
	["start", PI / 4.0, 32.0, 18.0, true],
	["dicht", PI / 4.0, 36.0, 9.0, false],
]


func _initialize() -> void:
	_draai.call_deferred()


func _draai() -> void:
	var uit := "out/gras"
	var variant := "a"
	var naam := ""
	var vast := -1.0
	for a in OS.get_cmdline_user_args():
		if a.begins_with("--uit="):
			uit = a.substr(6)
		elif a.begins_with("--gras="):
			variant = a.substr(7)
		elif a.begins_with("--naam="):
			naam = a.substr(7)
		elif a.begins_with("--seizoen_vast="):
			vast = float(a.substr(15))
	DirAccess.make_dir_recursive_absolute(ProjectSettings.globalize_path("res://" + uit) if not uit.is_absolute_path() else uit)
	var main: Node = load("res://main.tscn").instantiate()
	root.add_child(main)
	var droog := not OS.get_cmdline_user_args().has("--regen")   # droog beeld: de herfstdag van missie 1 regent om 12 uur
	for i in 30:
		if droog and main.w != null:
			main.w.regen_handmatig = 0
		await process_frame
	for i in 60 if droog else 0:   # resterende regendruppels laten vallen
		await process_frame
	if naam == "":
		naam = variant
	main.view.seizoen_vast = vast
	var cam: Camera3D = main.cam
	for o in OPNAMES:
		cam.zet_direct(main.view.terrein.tegel_midden(main.w.kampvuur), o[1], deg_to_rad(o[2]), o[3])
		_zet_hud(main, o[4])
		for i in 12:
			await process_frame
		var img := root.get_texture().get_image()
		var pad: String = uit.path_join(naam + "_" + o[0] + ".png")
		img.save_png(pad if pad.is_absolute_path() else "res://" + pad)
		print("[gras_frames] ", pad, " ", img.get_size())
	quit()


var _was := {}


func _zet_hud(n: Node, aan: bool) -> void:
	for c in n.get_children() + n.get_children().reduce(func(a, k): return a + k.get_children(), []):
		if c is CanvasLayer or c is Control:
			if not _was.has(c):
				_was[c] = c.visible
			c.visible = _was[c] and aan
