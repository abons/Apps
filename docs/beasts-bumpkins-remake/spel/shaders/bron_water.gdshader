shader_type spatial;
render_mode blend_mix, depth_draw_opaque, cull_back;
// Put (bron.glb, mesh `bron_water`): het bassin rimpelt. Drie lopende sinusgolven plus kringen waar de straal
// neerkomt, alleen in de normaal (en wat schuim bij de inslag). Geen textuur en geen depth-texture: ook goedkoop
// genoeg voor de telefoon (view/bron_water.gd zet hem, op pc en mobiel dezelfde).

uniform vec3 kleur : source_color = vec3(0.03, 0.09, 0.18);
uniform vec2 inslag = vec2(1.81, -0.2);   // lokaal (x, z) waar de straal het water raakt (props.py bron())
uniform float kantel = 0.11;              // hoe sterk de golfjes de normaal kantelen

varying vec2 lp;

void vertex() {
	lp = VERTEX.xz;
}

// Helling (d/dx, d/dz) van sin(k . p + w t) * a = k * a * cos(...).
vec2 golf(vec2 k, float w, float a, float t) {
	return k * (a * cos(dot(lp, k) + w * t));
}

void fragment() {
	float t = TIME;
	vec2 g = golf(vec2(5.0, 2.0), 1.7, 0.10, t) + golf(vec2(-3.0, 6.0), 2.3, 0.08, t) + golf(vec2(7.0, -8.0), -2.9, 0.04, t);
	vec2 dv = lp - inslag;
	float r = length(dv) + 1e-4;
	float kring = cos(r * 14.0 - t * 6.0) * exp(-r * 1.8);
	g += dv / r * (kring * 0.9);
	vec3 n = normalize(vec3(-g.x * kantel, 1.0, -g.y * kantel));
	NORMAL = normalize((VIEW_MATRIX * (MODEL_MATRIX * vec4(n, 0.0))).xyz);
	float schuim = smoothstep(0.55, 0.0, r) * (0.55 + 0.45 * kring);
	ALBEDO = mix(kleur, vec3(0.85, 0.90, 0.95), schuim * 0.7);
	ALPHA = mix(0.93, 0.97, schuim);
	ROUGHNESS = 0.12;
	SPECULAR = 0.8;
}
