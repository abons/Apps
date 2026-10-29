shader_type spatial;
render_mode cull_back, depth_draw_always;
// Water: diepte uit de depth-texture (ondiep = doorzichtig, schuim aan de kant), rimpels uit ruis.

uniform sampler2D depth_tex : hint_depth_texture, repeat_disable, filter_nearest;
uniform vec3 diep : source_color = vec3(0.05, 0.20, 0.28);
uniform vec3 ondiep : source_color = vec3(0.20, 0.50, 0.52);
uniform float ijs = 0.0;   // 0..1: winter, water wordt grijzer/lichter

varying vec3 wp;

float hash(vec2 p) {
	vec3 p3 = fract(vec3(p.xyx) * 0.1031);
	p3 += dot(p3, p3.yzx + 33.33);
	return fract((p3.x + p3.y) * p3.z);
}
float ruis(vec2 p) {
	vec2 i = floor(p);
	vec2 f = fract(p);
	f = f * f * (3.0 - 2.0 * f);
	return mix(mix(hash(i), hash(i + vec2(1, 0)), f.x), mix(hash(i + vec2(0, 1)), hash(i + vec2(1, 1)), f.x), f.y);
}
float golf(vec2 p, float t) {
	return ruis(p * 0.9 + vec2(t * 0.35, t * 0.2)) * 0.6 + ruis(p * 2.3 - vec2(t * 0.5, -t * 0.3)) * 0.4;
}

void vertex() { wp = (MODEL_MATRIX * vec4(VERTEX, 1.0)).xyz; }

void fragment() {
	float d = textureLod(depth_tex, SCREEN_UV, 0.0).r;
	vec3 ndc = vec3(SCREEN_UV * 2.0 - 1.0, d);
	vec4 v = INV_PROJECTION_MATRIX * vec4(ndc, 1.0);
	v.xyz /= v.w;
	float verschil = max(-v.z + VERTEX.z, 0.0);
	float t = TIME;
	float e = 0.15;
	float h0 = golf(wp.xz, t);
	float hx = golf(wp.xz + vec2(e, 0), t);
	float hz = golf(wp.xz + vec2(0, e), t);
	NORMAL = normalize(NORMAL + vec3((h0 - hx), (h0 - hz), 0.0) * 1.6);
	vec3 kleur = mix(ondiep, diep, smoothstep(0.1, 2.5, verschil));
	kleur = mix(kleur, vec3(0.30, 0.42, 0.50), ijs * 0.55);
	float schuim = smoothstep(0.35, 0.0, verschil + (h0 - 0.5) * 0.25) * 0.8;
	ALBEDO = mix(kleur, vec3(0.9, 0.95, 0.95), schuim);
	ALPHA = clamp(0.35 + smoothstep(0.0, 1.2, verschil) * 0.6 + schuim * 0.4, 0.0, 0.95);
	ROUGHNESS = 0.08;
	SPECULAR = 0.7;
	METALLIC = 0.0;
}
