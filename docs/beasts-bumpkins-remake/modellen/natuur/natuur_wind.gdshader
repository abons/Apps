// Wind en seizoen voor de natuur-glb's (Godot 4). Eén shader voor schors, gebladerte, tarwe en de vlag.
// Wind zit in UV2 (glTF TEXCOORD_1), gezet door natuur_lib.Bouwer:
//   UV2.x            = zwaai van de hele plant (0 aan de voet .. 1 in de top)
//   y = 1.0 - UV2.y  (glTF draait v om)
//   fract(y)         = trilling van tak/blad/doek (0 aan de aanhechting .. ~1 aan de punt)
//   floor(y) / 8     = fase per tak (0..1), zodat takken niet in de maat bewegen
// Seizoen: zet `tint` op de baseColorFactor uit de README (gebladerte), schors/tarwe/bloemen op wit.
shader_type spatial;
render_mode cull_disabled, depth_draw_opaque;

uniform sampler2D albedo_tex : source_color, filter_linear_mipmap_anisotropic, repeat_enable;
uniform sampler2D normal_tex : hint_normal, filter_linear_mipmap_anisotropic, repeat_enable;
uniform sampler2D orm_tex : hint_default_white, filter_linear_mipmap, repeat_enable;
uniform bool use_orm = false;
uniform vec4 tint : source_color = vec4(1.0);
uniform bool alpha_kaart = true;
uniform float alpha_cut : hint_range(0.0, 1.0) = 0.5;
uniform float roughness_waarde : hint_range(0.0, 1.0) = 0.75;
uniform float doorschijn : hint_range(0.0, 1.0) = 0.25;   // licht door bladeren (achterlicht)

uniform vec2 wind_richting = vec2(1.0, 0.35);
uniform float wind_kracht = 1.0;
uniform float zwaai_m = 0.10;      // uitslag van de top (m) bij kracht 1
uniform float tril_m = 0.035;      // uitslag van een tak-/bladpunt (m)
uniform float vlag = 0.0;          // 1 = doek: lopende golf in plaats van trillen
uniform float vlag_m = 0.10;

void vertex() {
	float zwaai = UV2.x;
	float y = 1.0 - UV2.y;
	float tril = fract(y);
	float fase = floor(y + 0.0001) / 8.0 * 6.2831;
	vec3 plek = (MODEL_MATRIX * vec4(0.0, 0.0, 0.0, 1.0)).xyz;
	float t = TIME + dot(plek.xz, vec2(0.13, 0.17));
	vec2 d = normalize(wind_richting);
	vec3 d_obj = (inverse(MODEL_MATRIX) * vec4(d.x, 0.0, d.y, 0.0)).xyz;
	float vlaag = sin(t * 1.1) * 0.65 + sin(t * 2.7 + 1.3) * 0.25 + 0.35;
	VERTEX += d_obj * vlaag * zwaai * zwaai * zwaai_m * wind_kracht;
	if (vlag > 0.5) {
		float g = sin(TIME * 6.0 - tril * 9.0 + fase) * 0.7 + sin(TIME * 9.0 - tril * 15.0) * 0.3;
		VERTEX += NORMAL * g * tril * vlag_m * wind_kracht;
	} else {
		float f = sin(TIME * 3.7 + fase + VERTEX.y * 1.7) * 0.6 + sin(TIME * 7.1 + fase * 2.0) * 0.4;
		VERTEX += (NORMAL * 0.6 + d_obj * 0.4) * f * tril * tril_m * wind_kracht;
	}
}

void fragment() {
	vec4 c = texture(albedo_tex, UV);
	ALBEDO = c.rgb * tint.rgb;
	if (alpha_kaart) {
		ALPHA = c.a;
		ALPHA_SCISSOR_THRESHOLD = alpha_cut;
	}
	NORMAL_MAP = texture(normal_tex, UV).rgb;
	if (use_orm) {
		vec3 orm = texture(orm_tex, UV).rgb;
		AO = orm.r;
		ROUGHNESS = orm.g;
		METALLIC = orm.b;
	} else {
		ROUGHNESS = roughness_waarde;
	}
	BACKLIGHT = ALBEDO * doorschijn * (alpha_kaart ? 1.0 : 0.0);
}
