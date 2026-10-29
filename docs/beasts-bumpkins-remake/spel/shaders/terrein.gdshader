shader_type spatial;
// Terrein: vertexkleur = tegelkleur (rgb) en grasgewicht (a), wereldruis erbovenop, seizoenstint.

uniform float droog = 0.0;    // 0 groen .. 1 dor/herfst
uniform float sneeuw = 0.0;   // 0 geen .. 1 sneeuwdek
uniform float nat = 0.0;      // regen: donkerder, glanzender
uniform vec3 gras_bloei : source_color = vec3(0.30, 0.55, 0.12);
uniform vec3 gras_droog : source_color = vec3(0.56, 0.46, 0.20);

varying vec3 wp;
varying vec4 vc;

float hash(vec2 p) {
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
	mat2 rot = mat2(vec2(0.8, 0.6), vec2(-0.6, 0.8));
	for (int k = 0; k < 5; k++) { s += a * ruis(p); p = rot * p * 2.03 + 3.1; a *= 0.5; }
	return s;
}

void vertex() {
	wp = (MODEL_MATRIX * vec4(VERTEX, 1.0)).xyz;
	vc = COLOR;
}

void fragment() {
	float n = fbm(wp.xz * 0.18);
	float fijn = ruis(wp.xz * 9.0) * 0.5 + ruis(wp.xz * 23.0) * 0.5;
	vec3 c = vc.rgb * (0.80 + 0.40 * fijn);
	float g = vc.a;
	// gras: kleurvlekken + seizoen
	vec3 gras = mix(vc.rgb * 0.8, gras_bloei * 0.9, 0.35) * (0.65 + 0.75 * n);
	vec3 dor = gras_droog * (0.75 + 0.5 * n) * (0.85 + 0.3 * fijn);
	gras = mix(gras, dor, clamp(droog * (0.7 + 0.5 * n), 0.0, 1.0));
	c = mix(c, gras, g);
	// sneeuw (niet op de waterrand, onregelmatige rand)
	float dek = clamp(sneeuw * 1.6 - 0.5 + (fbm(wp.xz * 0.35) - 0.5) * 0.9, 0.0, 1.0);
	dek *= smoothstep(-0.12, 0.06, wp.y);
	c = mix(c, vec3(0.90, 0.93, 0.98) * (0.93 + 0.07 * fijn), smoothstep(0.1, 0.5, dek));
	c *= 1.0 - 0.28 * nat;
	ALBEDO = c;
	ROUGHNESS = mix(0.95, 0.62, nat);
	SPECULAR = 0.12;
}
