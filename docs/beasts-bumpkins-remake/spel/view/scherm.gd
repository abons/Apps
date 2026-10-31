class_name Scherm
extends RefCounted
## Schermindeling voor staand en liggend (2026-10-30): de telefoon draait mee (project.godot
## `display/window/handheld/orientation` = sensor), en de HUD, het bouwmenu, de brief en het prijzenscherm leggen zich
## opnieuw neer bij elke `size_changed` van de viewport. Liggend op de pc is alles zoals het was.
## `--venster=1080x2400` (na `--`): de pc doet alsof het scherm die maat heeft (viewport op die maat, het venster
## geschaald zodat het op de monitor past), om staand te proberen en frames te maken.
## `--proef=bouw|lade|prijzen` (na `--`): alleen voor frames: bouwmodus (hut) aan, de gebouwenlade open, of de prijzen open.


## Staand = hoger dan breed.
static func staand(vp: Vector2) -> bool:
	return vp.y > vp.x


## Hoeveel px een dp is op touch (afgeleid van de knophoogte, die >= 48 dp is); op de pc 1.
static func dp() -> float:
	return Bouwmenu.touch_knop_h() / 52.0 if Bouwmenu.touch else 1.0


## Waarde van `--naam=...` na `--`, of "".
static func optie(naam: String) -> String:
	for a in OS.get_cmdline_user_args():
		if a.begins_with("--" + naam + "="):
			return a.substr(naam.length() + 3)
	return ""


## `--venster=BxH`: de viewport krijgt die maat (stretch viewport), het venster past op de monitor.
static func zet_venster(root: Window) -> void:
	var v := optie("venster").split("x")
	if v.size() != 2 or int(v[0]) <= 0 or int(v[1]) <= 0:
		return
	var maat := Vector2i(int(v[0]), int(v[1]))
	root.content_scale_mode = Window.CONTENT_SCALE_MODE_VIEWPORT
	root.content_scale_aspect = Window.CONTENT_SCALE_ASPECT_KEEP
	root.content_scale_size = maat
	if DisplayServer.get_name() == "headless":
		root.size = maat
		return
	var scherm := Vector2(DisplayServer.screen_get_usable_rect(root.current_screen).size) * 0.9
	var f := minf(1.0, minf(scherm.x / maat.x, scherm.y / maat.y))
	root.size = Vector2i(Vector2(maat) * f)
	root.move_to_center()


## `--opname=pad.png` (na `--`, met `--opname_frame=N`, standaard 40): na N frames het beeld van de viewport op zijn
## eigen maat opslaan en stoppen. Voor frames op `--venster`-maat: --write-movie neemt het venster op, niet de viewport.
static var _opname_gezet := false     ## een keer per proces (startmenu en hud vragen het allebei, ook na een herlaad)


static func zet_opname(n: Node) -> void:
	var pad := optie("opname")
	if pad == "" or _opname_gezet:
		return
	_opname_gezet = true
	n = n.get_tree().root          # de wortel blijft bestaan als de hoofdscène opnieuw laadt
	var na := int(optie("opname_frame")) if optie("opname_frame") != "" else 40
	var tree := n.get_tree()
	var teller := [0]
	tree.process_frame.connect(func() -> void:
		teller[0] += 1
		if teller[0] == na:
			await RenderingServer.frame_post_draw
			var img := n.get_viewport().get_texture().get_image()
			DirAccess.make_dir_recursive_absolute(ProjectSettings.globalize_path(pad).get_base_dir())
			img.save_png(pad)
			print("[scherm] opname ", pad, " ", img.get_size())
			tree.quit())
