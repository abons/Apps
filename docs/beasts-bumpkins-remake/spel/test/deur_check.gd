extends SceneTree
# Zet elk gebouw met een deur in 4 draaiingen neer zoals Bouwmenu._plan_klaar en vergelijkt het glb-deuranker
# (deur_voor_drempel / deur_drempel) met Plan.deur_punt() en Plan.deur_tegel(). Draaien:
#   Godot --headless --path . --script res://test/deur_check.gd     (faalt als een anker > 0,1 m van deur_punt ligt)
const GLB := {&"hut": "peasant_hut_rt", &"molen": "molen_rt", &"melkerij": "melkerij_boerderij_rt",
	&"kippenhok": "kippenhok_rt", &"gereedschapsloods": "gereedschapsloods_rt"}
func _init():
	var fout := 0
	for soort in GLB:
		var ps: PackedScene = load("res://assets/%s.glb" % GLB[soort])
		var af: Vector2i = Wereld.BOUWSOORTEN[soort]
		for draai in 4:
			var p := Plan.new(soort, Vector2i(10, 10), draai, af.x, af.y)
			var hut: Node3D = ps.instantiate()
			var box := Bouwmenu._omhulsel(hut, Transform3D.IDENTITY)
			var schaal := 1.0
			var deur := hut.find_child("voordeur", true, false)
			if deur == null:
				deur = hut.find_child("deur", true, false)
			if deur != null:
				var dh := Bouwmenu._omhulsel_van(hut, deur).size.y
				if dh >= 1.0:
					schaal = Bouwmenu.DEUR_M / dh
			var r := p.afdruk()
			var rot := draai * PI * 0.5
			var m := Vector3((r.position.x + r.size.x * 0.5) * 2.0, 0, (r.position.y + r.size.y * 0.5) * 2.0)
			var midden := box.get_center() * schaal
			var pos := m - Vector3(midden.x, box.position.y * schaal, midden.z).rotated(Vector3.UP, rot)
			var dr := hut.find_child("deur_voor_drempel", true, false) as Node3D
			if dr == null:
				dr = hut.find_child("deur_drempel", true, false) as Node3D
			var wp := pos + (dr.position * schaal).rotated(Vector3.UP, rot)
			var at := Vector2i(int(floor(wp.x / 2.0)), int(floor(wp.z / 2.0)))
			var dt := p.deur_tegel()
			var dm := Vector2((dt.x + 0.5) * 2.0, (dt.y + 0.5) * 2.0)
			var dp := p.deur_punt(2.0).distance_to(Vector2(wp.x, wp.z))
			if dp > 0.1:
				fout += 1
			print("%s %s draai %d: anker %s, deur_punt %.2f m ernaast, deurtegel %s op %.2f m" % ["ok  " if dp <= 0.1 else "FOUT", soort, draai, Vector2(wp.x, wp.z), dp, dt, dm.distance_to(Vector2(wp.x, wp.z))])
			hut.free()
	print("---- ", "ALLES OK" if fout == 0 else "%d FOUT(EN)" % fout)
	quit(0 if fout == 0 else 1)
