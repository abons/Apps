shader_type spatial;
// Rotsen, kliffen en steenhopen uit de natuur-glb's: gebakken kleur/normaal/ORM plus een sneeuwdek op alles wat omhoog wijst.

uniform sampler2D albedo_tex : source_color, filter_linear_mipmap_anisotropic, repeat_enable;
uniform sampler2D normal_tex : hint_normal, filter_linear_mipmap_anisotropic, repeat_enable;
uniform sampler2D orm_tex : hint_default_white, filter_linear_mipmap, repeat_enable;
uniform float sneeuw = 0.0;    // 0 .. 1
uniform float nat = 0.0;

varying vec3 wn;

void vertex() {
	wn = normalize((MODEL_MATRIX * vec4(NORMAL, 0.0)).xyz);
}

void fragment() {
	vec3 c = texture(albedo_tex, UV).rgb;
	vec3 orm = texture(orm_tex, UV).rgb;
	NORMAL_MAP = texture(normal_tex, UV).rgb;
	float lum = dot(c, vec3(0.33));
	float dek = clamp((wn.y - (1.05 - sneeuw * 0.85) + (lum - 0.3) * 0.25) * 5.0, 0.0, 1.0);
	c = mix(c, vec3(0.88, 0.91, 0.96), dek);
	c *= 1.0 - 0.25 * nat;
	ALBEDO = c;
	AO = orm.r;
	ROUGHNESS = mix(orm.g, 0.85, dek);
	METALLIC = orm.b * (1.0 - dek);
}
