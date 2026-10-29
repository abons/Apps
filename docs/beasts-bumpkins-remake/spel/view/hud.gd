class_name Hud
extends CanvasLayer
## Minimale HUD: tijd, seizoen, weer, selectie, tempo. Rechtsonder de besturing.

var w: Wereld
var bestuur: Bestuur
var label: Label
var hulp: Label
var kader: Control
var uitslag: Label


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
	hulp.text = "links: kader/klik = kiezen, klik grond = lopen, klik koe = claimen   rechts klik = selectie weg   rechts slepen / Q E = draaien\nWASD/rand = pannen   wiel = zoom   Spatie pauze   1 2 4 tempo   K regen   N seizoen   Esc stop"
	pc2.add_child(hulp)
	add_child(pc2)

	uitslag = Label.new()
	uitslag.add_theme_font_size_override("font_size", 44)
	uitslag.add_theme_color_override("font_outline_color", Color.BLACK)
	uitslag.add_theme_constant_override("outline_size", 10)
	uitslag.set_anchors_preset(Control.PRESET_CENTER_TOP)
	uitslag.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	uitslag.grow_horizontal = Control.GROW_DIRECTION_BOTH
	uitslag.position.y = 90
	uitslag.mouse_filter = Control.MOUSE_FILTER_IGNORE
	uitslag.visible = false
	add_child(uitslag)
	w.missie_einde.connect(func(u: String) -> void:
		uitslag.text = "Missie geslaagd!" if u == "gewonnen" else "Missie mislukt"
		uitslag.add_theme_color_override("font_color", Color(1.0, 0.85, 0.3) if u == "gewonnen" else Color(1.0, 0.35, 0.3))
		uitslag.visible = true)

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
	var doel: Dictionary = w.spel.get("missie", {})
	label.text = "%02d:%02d%s  dag %d  %s  %s
kas: %d   dorpelingen: %d/%d   koeien: %d/%d   bedden: %d
geselecteerd: %d   tempo: %s" % [
		h, m, " (nacht)" if w.is_nacht() else "", w.dag_nr() + 1, w.seizoen_naam(), weer,
		w.kas, w.dorpelingen.size(), int(doel.get("dorpelingen", 0)), w.eigen_koeien(), int(doel.get("koeien", 0)), w.bedden(),
		bestuur.gekozen.size(), tempo]
