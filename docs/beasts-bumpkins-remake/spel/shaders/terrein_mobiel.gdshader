shader_type spatial;
// Terrein voor mobiel (view/terrein_view.gd kiest dit met OS.has_feature("mobile")): dezelfde lagen en uniforms als
// terrein.gdshader, maar goedkoop voor een telefoon-gpu: alleen de kleurtextuur (geen normaal/ruw, geen tweede
// macro-sample, geen triplanar), uitgerold zonder lussen of arrays, een ruis voor de overgangen in plaats van vijf en
// een in plaats van de fbm. De pc gebruikt terrein.gdshader en ziet hier niets van.

uniform sampler2DArray kleur_tex : source_color, filter_linear_mipmap, repeat_enable;
uniform float herhaling_m = 2.8;
uniform float droog = 0.0;
uniform float sneeuw = 0.0;
uniform float nat = 0.0;
uniform vec3 gras_droog : source_color = vec3(0.95, 0.78, 0.36);
uniform vec3 pad_kleur : source_color = vec3(0.50, 0.36, 0.22);
uniform vec3 aarde_kleur : source_color = vec3(0.75, 0.56, 0.40);
uniform vec3 zeebodem : source_color = vec3(0.20, 0.25, 0.22);
// Gras (2026-10-31, als het origineel: diep donkergroen 8,85,7 met rode en gele stipjes): de graslaag wordt
// herkleurd naar gras_kleur (alleen de helderheid van de textuur blijft, de witte/gele bloemetjes vallen weg), in de
// lichte vlekken uit de kaart (UV2.x, view/terrein_view.gd GRAS_LICHT) naar gras_licht; stipjes per cel van 0,5 m.
uniform vec3 gras_kleur : source_color = vec3(0.075, 0.25, 0.035);
uniform vec3 gras_licht : source_color = vec3(0.115, 0.34, 0.05);
uniform float stip_kans = 0.04;
// Grasvarianten (2026-10-31, view/gras_varianten.gd, -- --gras=naam): standaardwaarden = het beeld van 144ea40.
uniform float gras_herkleur = 1.0;       // 0 = oude textuurkleur (voor 144ea40), 1 = herkleurd naar gras_kleur
uniform float gras_licht_sterkte = 1.0;  // vermenigvuldiger op de lichte vlekken uit de kaart (UV2.x)
uniform float gras_verzadiging = 1.0;    // 1 = ongewijzigd, < 1 grijzer
uniform float gras_helderheid = 1.0;
uniform float gras_macro = 0.0;          // grote vlekken (ruis) naar gras_macro_kleur; 0 = uit, kost dan niets
uniform vec3 gras_macro_kleur : source_color = vec3(0.16, 0.20, 0.04);
uniform float gras_macro_schaal = 0.1;   // ruisfrequentie per meter (0,1 = vlekken van ~10 m)
uniform float stip_sterkte = 1.0;

varying vec3 wp;
varying vec4 vc;
varying vec2 pa;
varying float steil;
varying float lv;

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
// rode en gele stipjes: een op de 1/stip_kans cellen van 0,5 m, rondje van ~5 cm, ver weg uitgedoofd
float stipjes(vec2 xz, out vec3 kleur) {
	vec2 sc = xz * 2.0;
	vec2 ci = floor(sc);
	vec2 jp = vec2(hash(ci + 3.1), hash(ci + 7.7)) * 0.6 + 0.2;
	float s = step(1.0 - stip_kans, hash(ci + 17.0)) * (1.0 - smoothstep(0.06, 0.1, length(fract(sc) - jp)));
	s *= 1.0 - smoothstep(0.12, 0.3, length(fwidth(sc)));
	kleur = hash(ci + 29.0) < 0.55 ? vec3(0.45, 0.04, 0.02) : vec3(0.70, 0.58, 0.08);
	return s;
}

void vertex() {
	wp = (MODEL_MATRIX * vec4(VERTEX, 1.0)).xyz;
	vc = COLOR;
	pa = UV;
	steil = smoothstep(0.5, 0.8, 1.0 - normalize(NORMAL).y);
	lv = UV2.x;
}

void fragment() {
	vec2 uv = wp.xz / herhaling_m;
	float som = vc.x + vc.y + vc.z + vc.w;
	float ns = 1.0 - steil;
	vec4 w4 = vec4(vc.x * ns, vc.y * ns, max(vc.z, steil), vc.w * ns);
	float w5 = max(0.0, 1.0 - som) * ns;
	// overgangen scherper met een ruis, per laag verschoven
	float n = ruis(wp.xz * 1.3);
	vec4 nv = fract(vec4(n, n + 0.37, n + 0.61, n + 0.83)) - 0.5;
	vec4 b4 = clamp((w4 - 0.5) * 1.9 + 0.5 + nv * 0.75, 0.0, 1.0);
	float b5 = clamp((w5 - 0.5) * 1.9 + 0.5 + (fract(n + 0.19) - 0.5) * 0.75, 0.0, 1.0);
	float tot = b4.x + b4.y + b4.z + b4.w + b5;
	if (tot < 0.01) { b4 = w4; b5 = w5; tot = max(som + w5, 0.01); }
	b4 /= tot;
	b5 /= tot;
	vec3 gt = texture(kleur_tex, vec3(uv, 0.0)).rgb;
	vec3 gb = mix(gras_kleur, gras_licht, clamp(lv * gras_licht_sterkte, 0.0, 1.0));
	if (gras_macro > 0.0) {
		gb = mix(gb, gras_macro_kleur, gras_macro * smoothstep(0.3, 0.7, ruis(wp.xz * gras_macro_schaal)));
	}
	vec3 gh = gb * clamp(dot(gt, vec3(0.3, 0.59, 0.11)) / 0.105, 0.6, 1.3);
	gt = mix(gt, gh, gras_herkleur);
	gt = mix(vec3(dot(gt, vec3(0.2126, 0.7152, 0.0722))), gt, gras_verzadiging) * gras_helderheid;
	vec3 alb = gt * b4.x
		+ texture(kleur_tex, vec3(uv, 1.0)).rgb * b4.y
		+ texture(kleur_tex, vec3(uv, 2.0)).rgb * b4.z
		+ texture(kleur_tex, vec3(uv, 3.0)).rgb * b4.w
		+ texture(kleur_tex, vec3(uv, 4.0)).rgb * b5;
	float droogw = b4.x + b4.y;
	float g = ruis(wp.xz * 0.18);
	alb *= 0.78 + 0.5 * g;
	vec3 sk;
	alb = mix(alb, sk, stipjes(wp.xz, sk) * smoothstep(0.5, 0.8, b4.x) * stip_sterkte);
	alb = mix(alb, alb * gras_droog, clamp(droog * droogw * (0.75 + 0.5 * g), 0.0, 1.0));
	alb = mix(alb, alb * pad_kleur, clamp(pa.x, 0.0, 1.0));
	alb = mix(alb, alb * aarde_kleur, clamp(pa.y, 0.0, 1.0));
	float dek = clamp(sneeuw * 1.6 - 0.5 + (g - 0.5) * 0.9, 0.0, 1.0);
	dek *= smoothstep(-0.12, 0.06, wp.y) * (1.0 - 0.8 * steil);
	dek = smoothstep(0.1, 0.5, dek);
	alb = mix(alb, vec3(0.90, 0.93, 0.98), dek);
	alb *= 1.0 - 0.28 * nat;
	float diep = smoothstep(-0.2, -1.7, wp.y);
	alb = mix(alb, zeebodem, diep);
	ALBEDO = alb;
	ROUGHNESS = mix(mix(0.85, 0.8, dek) * mix(1.0, 0.7, nat), 1.0, diep);
	SPECULAR = 0.15;
}
