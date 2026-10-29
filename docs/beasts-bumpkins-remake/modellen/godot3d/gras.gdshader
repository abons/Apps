shader_type spatial;
// Procedureel gras: wereldpositie-ruis, droge plekken, een kale erfplek rond de hut.

uniform vec3 kleur_a : source_color = vec3(0.20, 0.33, 0.10);
uniform vec3 kleur_b : source_color = vec3(0.34, 0.44, 0.15);
uniform vec3 kleur_droog : source_color = vec3(0.47, 0.43, 0.24);
uniform vec3 kleur_aarde : source_color = vec3(0.33, 0.26, 0.17);
uniform vec2 erf_midden = vec2(0.65, 0.05);
uniform float erf_straal = 4.0;
uniform float winter = 0.0;

varying vec3 wp;

float hash(vec2 p) {  // zonder sin: stabiel op de GPU, ook bij grote coördinaten
	vec3 p3 = fract(vec3(p.xyx) * 0.1031);
	p3 += dot(p3, p3.yzx + 33.33);
	return fract((p3.x + p3.y) * p3.z);
}
float ruis(vec2 p) {
	vec2 i = floor(p);
	vec2 f = fract(p);
	f = f * f * f * (f * (f * 6.0 - 15.0) + 10.0);
	return mix(mix(hash(i), hash(i + vec2(1, 0)), f.x), mix(hash(i + vec2(0, 1)), hash(i + vec2(1, 1)), f.x), f.y);
}
float fbm(vec2 p) {
	float s = 0.0, a = 0.5;
	mat2 rot = mat2(vec2(0.8, 0.6), vec2(-0.6, 0.8));  // gedraaide octaven: geen blokpatroon
	for (int k = 0; k < 5; k++) { s += a * ruis(p); p = rot * p * 2.03 + 3.1; a *= 0.5; }
	return s;
}

void vertex() { wp = (MODEL_MATRIX * vec4(VERTEX, 1.0)).xyz; }

void fragment() {
	float n = fbm(wp.xz * 0.18);
	float fijn = ruis(wp.xz * 9.0) * 0.5 + ruis(wp.xz * 23.0) * 0.5;
	vec3 c = mix(kleur_a, kleur_b, n);
	c = mix(c, kleur_droog, smoothstep(0.45, 0.85, fbm(wp.xz * 0.05 + 7.0)) * 0.5);
	c *= 0.8 + 0.4 * fijn;
	vec3 w = mix(c, vec3(0.40, 0.38, 0.29), 0.6);
	c = mix(c, w, winter);
	float d = length(wp.xz - erf_midden) + (fbm(wp.xz * 0.9) - 0.5) * 1.6;
	float aarde = 1.0 - smoothstep(erf_straal * 0.6, erf_straal, d);
	c = mix(c, kleur_aarde * (0.8 + 0.4 * fijn), aarde * 0.85);
	ALBEDO = c;
	ROUGHNESS = 0.95;
	SPECULAR = 0.15;
}
