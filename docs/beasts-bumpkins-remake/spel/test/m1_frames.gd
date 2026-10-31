extends SceneTree
## Vergelijkingsframes missie 1 (remake naast de originele screenshots, lokaal/concept/m1_kaart.html).
## Met venster (niet headless):
##   "$G" --path . -s test/m1_frames.gd -- --missie=1 --scenario=m1frames --seizoen=zomer --uur=12 --uit=out/m1
## Scenario-naam onbekend = startcamera, geen mist, geen briefing. Per opname: camera zetten, 12 frames wachten, PNG.
## iso = de kijkrichting van het origineel: noordwest (tegel 0,0) boven, yaw 45 graden, helling 31 graden
## (ruit 78 x 40 px: sin = 40/78), afstand 16 m (ca. 26 m beeldbreedte, het origineel toont ~23 m op 640 px).

const ISO_YAW := PI / 4.0
const ISO_PITCH := 31.0
const OPNAMES := [
	# naam, tegel, yaw, helling (graden), afstand (m), hud
	["start_remake", Vector2i(-1, -1), PI / 4.0, 32.0, 18.0, true],   # main.gd START_*
	["start_iso", Vector2i(103, 67), ISO_YAW, ISO_PITCH, 16.0, false],
	["bos_no_iso", Vector2i(107, 51), ISO_YAW, ISO_PITCH, 16.0, false],
	["oost_iso", Vector2i(112, 58), ISO_YAW, ISO_PITCH, 16.0, false],
	["west_iso", Vector2i(88, 60), ISO_YAW, ISO_PITCH, 22.0, false],
	["zuidkust_iso", Vector2i(116, 88), ISO_YAW, ISO_PITCH, 22.0, false],
	["vlag_dicht", Vector2i(104, 65), ISO_YAW, ISO_PITCH, 8.0, false],
	["beker_dicht", Vector2i(110, 53), ISO_YAW, ISO_PITCH, 8.0, false],
]


func _initialize() -> void:
	_draai.call_deferred()


func _draai() -> void:
	var uit := "out/m1"
	for a in OS.get_cmdline_user_args():
		if a.begins_with("--uit="):
			uit = a.substr(6)
	DirAccess.make_dir_recursive_absolute(ProjectSettings.globalize_path("res://" + uit) if not uit.is_absolute_path() else uit)
	var main: Node = load("res://main.tscn").instantiate()
	root.add_child(main)
	for i in 30:
		await process_frame
	var cam: Camera3D = main.cam
	for o in OPNAMES:
		var t: Vector2i = o[1]
		if t.x < 0:
			t = main.w.kampvuur
		cam.zet_direct(main.view.terrein.tegel_midden(t), o[2], deg_to_rad(o[3]), o[4])
		_zet_hud(main, o[5])
		for i in 12:
			await process_frame
		var img := root.get_texture().get_image()
		var pad: String = uit.path_join(o[0] + ".png")
		img.save_png(pad if pad.is_absolute_path() else "res://" + pad)
		print("[m1_frames] ", pad, " ", img.get_size())
	quit()


var _was := {}   ## node -> zichtbaar bij de start (het pauzemenu is een verborgen Control: niet aanzetten)


func _zet_hud(n: Node, aan: bool) -> void:
	for c in n.get_children() + n.get_children().reduce(func(a, k): return a + k.get_children(), []):
		if c is CanvasLayer or c is Control:
			if not _was.has(c):
				_was[c] = c.visible
			c.visible = _was[c] and aan
