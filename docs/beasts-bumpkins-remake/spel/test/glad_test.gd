extends SceneTree
## Telt hoeveel punten een route heeft voor en na Router.glad (minder = minder bochten = minder gedraai).

func _initialize() -> void:
	var w := Wereld.new()
	w.laad()
	var paren := [[Vector2i(108, 47), Vector2i(118, 58)], [Vector2i(99, 64), Vector2i(111, 65)], [Vector2i(95, 46), Vector2i(100, 66)]]
	for p in paren:
		var r := Router.route(w.raster, p[0], p[1])
		var g := Router.glad(w.raster, Vector2(p[0]) + Vector2(0.5, 0.5), r)
		var bochten := 0
		var vorige := Vector2(p[0]) + Vector2(0.5, 0.5)
		var oud := Vector2.ZERO
		for q in r:
			var d := (Vector2(q) + Vector2(0.5, 0.5)) - vorige
			if oud != Vector2.ZERO and d.normalized().distance_to(oud.normalized()) > 0.01:
				bochten += 1
			oud = d
			vorige = Vector2(q) + Vector2(0.5, 0.5)
		print("%s -> %s: tegelroute %d stappen, %d richtingswissels; recht getrokken %d punten" % [p[0], p[1], r.size(), bochten, g.size()])
	quit()
