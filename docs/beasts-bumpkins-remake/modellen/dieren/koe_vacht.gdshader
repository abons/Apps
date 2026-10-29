// Hertint-shader voor mat_lijf van koe.glb (zie DELEN/HERTINTEN in koe.py).
// albedo = kleur * mix(tint_vacht, tint_vlek / vlek_standaard, masker); standaardwaarden = geen verschil.
// Gebruik: ShaderMaterial op surface 0 van "lijf", textures uit textures_koe/ (kleur, normaal, orm, vlek).
shader_type spatial;

uniform sampler2D kleur : source_color, filter_linear_mipmap, repeat_disable;
uniform sampler2D normaal : hint_normal, filter_linear_mipmap, repeat_disable;
uniform sampler2D orm : hint_default_white, filter_linear_mipmap, repeat_disable;   // R=AO G=ruw B=metaal
uniform sampler2D vlek_masker : hint_default_black, filter_linear_mipmap, repeat_disable;
uniform vec4 tint_vacht : source_color = vec4(1.0);
uniform vec4 tint_vlek : source_color = vec4(0.149, 0.141, 0.133, 1.0);       // #262422
uniform vec4 vlek_standaard : source_color = vec4(0.149, 0.141, 0.133, 1.0);  // waar de textuur op gemaakt is

void fragment() {
	vec3 c = texture(kleur, UV).rgb;
	float m = texture(vlek_masker, UV).r;
	vec3 factor = mix(tint_vacht.rgb, tint_vlek.rgb / max(vlek_standaard.rgb, vec3(1e-3)), m);
	ALBEDO = c * factor;
	vec3 o = texture(orm, UV).rgb;
	AO = o.r;
	ROUGHNESS = o.g;
	METALLIC = o.b;
	NORMAL_MAP = texture(normaal, UV).rgb;
	SPECULAR = 0.35;
}
