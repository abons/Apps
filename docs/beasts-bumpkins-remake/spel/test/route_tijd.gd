extends SceneTree
## Meet hoe lang een route kost: godot --headless --path . --script res://test/route_tijd.gd

func _initialize() -> void:
	var w := Wereld.new()
	w.laad()
	var t0 := Time.get_ticks_usec()
	var n := 0
	for i in 20:
		var van := Vector2i(95 + (i % 5), 50 + i)
		var naar := Vector2i(112, 78 - i)
		if w.raster.loopbaar_v(van) and w.raster.loopbaar_v(naar):
			Router.route(w.raster, van, naar)
			n += 1
	print("route: ", float(Time.get_ticks_usec() - t0) / 1000.0 / maxf(n, 1), " ms per route (", n, ")")
	var t1 := Time.get_ticks_usec()
	for i in 600:
		w.tik(w.tik_dt)
	print("tik: ", float(Time.get_ticks_usec() - t1) / 1000.0 / 600.0, " ms per tik (6 zwervers)")
	quit()
