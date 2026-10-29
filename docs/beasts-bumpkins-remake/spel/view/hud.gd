class_name Hud
extends CanvasLayer
## Minimale HUD: tijd, seizoen, weer, selectie, tempo. Rechtsonder de besturing.

var w: Wereld
var bestuur: Bestuur
var label: Label
var hulp: Label
var kader: Control


func bouw(wereld: Wereld, b: Bestuur) -> void:
	w = wereld
	bestuur = b
	var pc := PanelContainer.new()
	pc.position = Vector2(12, 12)
	pc.mouse_filter = Control.MOUSE_FILTER_IGNORE
	pc.add_theme_stylebox_override("panel", _stijl())
	label = Label.new()
	label.add_theme_font_size_override("font_size", 18)
	label.mouse_filter = Control.MOUSE_FILTER_IGNORE
	pc.add_child(label)
	add_child(pc)

	var pc2 := PanelContainer.new()
	pc2.mouse_filter = Control.MOUSE_FILTER_IGNORE
	pc2.add_theme_stylebox_override("panel", _stijl())
	pc2.set_anchors_preset(Control.PRESET_BOTTOM_LEFT)
	pc2.position = Vector2(12, -64)
	hulp = Label.new()
	hulp.add_theme_font_size_override("font_size", 13)
	hulp.mouse_filter = Control.MOUSE_FILTER_IGNORE
	hulp.text = "links: kader/klik = kiezen, klik grond = lopen   rechts klik = selectie weg   rechts slepen / Q E = draaien\nWASD/rand = pannen   wiel = zoom   Spatie pauze   1 2 4 tempo   K regen   N seizoen   Esc stop"
	pc2.add_child(hulp)
	add_child(pc2)

	kader = Control.new()
	kader.set_script(load("res://view/kader.gd"))
	add_child(kader)


func _stijl() -> StyleBoxFlat:
	var sb := StyleBoxFlat.new()
	sb.bg_color = Color(0, 0, 0, 0.5)
	sb.set_content_margin_all(8)
	sb.set_corner_radius_all(4)
	return sb


func _process(_dt: float) -> void:
	var uur := w.uur()
	var h := int(uur)
	var m := int(fposmod(uur, 1.0) * 60.0)
	var tempo := "PAUZE" if w.gepauzeerd else "%dx" % int(w.tempo)
	var weer := "regen" if w.regent() else "droog"
	label.text = "%02d:%02d%s  dag %d  %s  %s
geselecteerd: %d   tempo: %s" % [
		h, m, " (nacht)" if w.is_nacht() else "", w.dag_nr() + 1, w.seizoen_naam(), weer, bestuur.gekozen.size(), tempo]
