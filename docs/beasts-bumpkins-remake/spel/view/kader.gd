extends Control
## Tekent het selectiekader (slepen met links). Raakt de muis niet aan.

var rect := Rect2()
var zichtbaar := false


func _ready() -> void:
	mouse_filter = Control.MOUSE_FILTER_IGNORE
	set_anchors_preset(Control.PRESET_FULL_RECT)


func zet(r: Rect2, aan: bool) -> void:
	rect = r
	zichtbaar = aan
	queue_redraw()


func _draw() -> void:
	if zichtbaar:
		draw_rect(rect, Color(0.5, 1.0, 0.4, 0.15), true)
		draw_rect(rect, Color(0.6, 1.0, 0.45, 0.95), false, 2.0)
