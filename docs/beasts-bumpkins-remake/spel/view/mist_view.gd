class_name MistView
extends MeshInstance3D
## Tekent de mist van oorlog (sim/mist.gd) als schermvullende quad met shaders/mist.gdshader: die leest de diepte en
## maakt alles zwart wat op een onverkende tegel staat, terrein, water en objecten in een keer. Het verkend-raster gaat
## als R8-textuur mee (1 texel per tegel) en wordt alleen bijgewerkt als `Mist.versie` verandert.
## Aanhaken (main.gd): `var mv := MistView.new(); add_child(mv); mv.bouw(w)`.

var w: Wereld
var _mat: ShaderMaterial
var _img: Image
var _tex: ImageTexture
var _versie := -1


func bouw(wereld: Wereld) -> void:
	w = wereld
	name = "Mist"
	var q := QuadMesh.new()
	q.size = Vector2(2, 2)
	mesh = q
	_mat = ShaderMaterial.new()
	_mat.shader = load("res://shaders/mist.gdshader")
	_mat.render_priority = 127        # als laatste, ook na het (transparante) water
	material_override = _mat
	cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	extra_cull_margin = 16384.0       # nooit wegknippen: de quad staat in schermruimte
	custom_aabb = AABB(Vector3(-1e5, -1e5, -1e5), Vector3(2e5, 2e5, 2e5))
	var r := w.raster
	_img = Image.create(r.kolommen, r.rijen, false, Image.FORMAT_R8)
	_tex = ImageTexture.create_from_image(_img)
	_mat.set_shader_parameter("verkend", _tex)
	_mat.set_shader_parameter("maat", Vector2(r.kolommen, r.rijen))
	_mat.set_shader_parameter("tegel_m", w.tegel_m)
	_werk_bij()


func _process(_dt: float) -> void:
	if w.mist.versie != _versie:
		_werk_bij()


func _werk_bij() -> void:
	_versie = w.mist.versie
	visible = w.mist.aan
	_mat.set_shader_parameter("aan", 1.0 if w.mist.aan else 0.0)
	var r := w.raster
	_img.set_data(r.kolommen, r.rijen, false, Image.FORMAT_R8, w.mist.verkend)   # 0/1; de shader schaalt x255
	_tex.update(_img)
