shader_type spatial;
// Terrein: vijf getegelde texturensets (gras, bosgrond, rots, zand, water_rand) als Texture2DArray, per hoekpunt gewogen
// uit de omliggende tegelsoorten. COLOR = gewicht (gras, bosgrond, rots, zand); de rest (1 - som) is water_rand.
// UV = (pad, aarde): bruine tint over zand/bosgrond. Overgangen worden met ruis scherper en grilliger gemaakt dan de
// lineaire hoekverloop. Boven op de lagen: seizoenstint (droog), sneeuw, nat.

uniform sampler2DArray kleur_tex : source_color, filter_linear_mipmap_anisotropic, repeat_enable;
uniform sampler2DArray normaal_tex : filter_linear_mipmap_anisotropic, repeat_enable;
uniform sampler2DArray ruw_tex : filter_linear_mipmap_anisotropic, repeat_enable;
uniform float herhaling_m = 2.8;     // meter per herhaling van een texture
uniform float droog = 0.0;           // 0 groen .. 1 dor/herfst
uniform float sneeuw = 0.0;          // 0 geen .. 1 sneeuwdek
uniform float nat = 0.0;             // regen: donkerder, glanzender
uniform vec3 gras_droog : source_color = vec3(0.95, 0.78, 0.36);   // vermenigvuldiger op gras/bosgrond bij droogte
uniform vec3 pad_kleur : source_color = vec3(0.50, 0.36, 0.22);
uniform vec3 aarde_kleur : source_color = vec3(0.75, 0.56, 0.40);
uniform vec3 zeebodem : source_color = vec3(0.20, 0.25, 0.22);   // gelijk aan het Zeebodem-vlak buiten het venster
uniform float normaal_sterkte = 0.8;
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
// Seizoensgras (2026-10-31, view/gras_seizoen.gd): hoeveel `droog` het gras zelf nog kleurt. 1 = als voorheen
// (varianten); de seizoenssets zetten 0, want hun gras_kleur is al de herfstkleur. Bosgrond droogt altijd mee.
uniform float gras_droog_mee = 1.0;

varying vec3 wp;
varying vec4 vc;
varying vec2 pa;
varying vec3 nw;
varying float lv;

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
	for (int k = 0; k < 4; k++) { s += a * ruis(p); p = rot * p * 2.03 + 3.1; a *= 0.5; }
	return s;
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
	nw = NORMAL;
	lv = UV2.x;
	// planaire afbeelding langs wereld-x (u) en wereld-z (v): raakvlak = +x, binormaal volgt de OpenGL-normaalmap (Y+ = omhoog)
	TANGENT = normalize(vec3(1.0, 0.0, 0.0) - NORMAL * NORMAL.x);
	BINORMAL = normalize(cross(NORMAL, TANGENT));
}

void fragment() {
	vec2 uv = wp.xz / herhaling_m;
	vec2 dx = dFdx(uv);
	vec2 dy = dFdy(uv);
	float som = vc.x + vc.y + vc.z + vc.w;
	// steile helling (klifwand, rotsrand): rots erbij en getriplanarde mapping, zodat de wand niet uitgerekt wordt
	float steil = smoothstep(0.5, 0.8, 1.0 - normalize(nw).y);
	float w[5] = float[5](vc.x * (1.0 - steil), vc.y * (1.0 - steil), max(vc.z, steil), vc.w * (1.0 - steil), max(0.0, 1.0 - som) * (1.0 - steil));
	vec3 an = abs(normalize(nw));
	vec3 tb = pow(an, vec3(4.0));
	tb /= tb.x + tb.y + tb.z;
	// overgangen: scherper dan het lineaire verloop, met ruis erdoorheen
	float b[5];
	float tot = 0.0;
	for (int i = 0; i < 5; i++) {
		float fi = float(i);
		float n = ruis(wp.xz * (1.15 + 0.31 * fi) + fi * 13.7);
		b[i] = clamp((w[i] - 0.5) * 1.9 + 0.5 + (n - 0.5) * 0.75, 0.0, 1.0);
		tot += b[i];
	}
	if (tot < 0.01) {
		for (int i = 0; i < 5; i++) { b[i] = w[i]; }
		tot = max(som + w[4], 0.01);
	}
	vec3 alb = vec3(0.0);
	vec3 nrm = vec3(0.0);
	float ruw = 0.0;
	float droogw = 0.0;
	for (int i = 0; i < 5; i++) {
		float wi = b[i] / tot;
		if (wi > 0.004) {
			vec3 a1 = textureGrad(kleur_tex, vec3(uv, float(i)), dx, dy).rgb;
			if (i == 2 && steil > 0.01) {
				vec2 ux = wp.zy / herhaling_m;
				vec2 uz = wp.xy / herhaling_m;
				vec3 ax = textureGrad(kleur_tex, vec3(ux, 2.0), dFdx(ux), dFdy(ux)).rgb;
				vec3 az = textureGrad(kleur_tex, vec3(uz, 2.0), dFdx(uz), dFdy(uz)).rgb;
				a1 = a1 * tb.y + ax * tb.x + az * tb.z;
			}
			vec3 a2 = textureGrad(kleur_tex, vec3(uv * 0.29 + vec2(0.37, 0.61), float(i)), dx * 0.29, dy * 0.29).rgb;
			vec3 a = mix(a1, a2, 0.38);
			if (i == 0) {
				vec3 gb = mix(gras_kleur, gras_licht, clamp(lv * gras_licht_sterkte, 0.0, 1.0));
				if (gras_macro > 0.0) {
					gb = mix(gb, gras_macro_kleur, gras_macro * smoothstep(0.32, 0.68, ruis(wp.xz * gras_macro_schaal) * 0.65 + ruis(wp.xz * gras_macro_schaal * 2.7 + 5.3) * 0.35));
				}
				vec3 gh = gb * clamp(dot(a, vec3(0.3, 0.59, 0.11)) / 0.105, 0.6, 1.3);
				a = mix(a, gh, gras_herkleur);
				a = mix(vec3(dot(a, vec3(0.2126, 0.7152, 0.0722))), a, gras_verzadiging) * gras_helderheid;
			}
			alb += a * wi;
			nrm += (textureGrad(normaal_tex, vec3(uv, float(i)), dx, dy).rgb * 2.0 - 1.0) * wi * (i == 2 ? 1.0 - steil : 1.0);
			ruw += textureGrad(ruw_tex, vec3(uv, float(i)), dx, dy).r * wi;
			if (i < 2) { droogw += wi * (i == 0 ? gras_droog_mee : 1.0); }
		}
	}
	float n = fbm(wp.xz * 0.18);
	float fijn = ruis(wp.xz * 9.0);
	alb *= (0.78 + 0.5 * n) * (0.94 + 0.12 * fijn);
	vec3 sk;
	float st = stipjes(wp.xz, sk) * smoothstep(0.5, 0.8, b[0] / tot) * stip_sterkte;
	alb = mix(alb, sk, st);
	alb = mix(alb, alb * gras_droog, clamp(droog * droogw * (0.75 + 0.5 * n), 0.0, 1.0));
	alb = mix(alb, alb * pad_kleur, clamp(pa.x, 0.0, 1.0));
	alb = mix(alb, alb * aarde_kleur, clamp(pa.y, 0.0, 1.0));
	// sneeuw (niet onder water, onregelmatige rand)
	float dek = clamp(sneeuw * 1.6 - 0.5 + (fbm(wp.xz * 0.35) - 0.5) * 0.9, 0.0, 1.0);
	dek *= smoothstep(-0.12, 0.06, wp.y) * (1.0 - 0.8 * steil);
	dek = smoothstep(0.1, 0.5, dek);
	alb = mix(alb, vec3(0.90, 0.93, 0.98) * (0.93 + 0.07 * fijn), dek);
	alb *= 1.0 - 0.28 * nat;
	float diep = smoothstep(-0.2, -1.7, wp.y);
	alb = mix(alb, zeebodem, diep);
	ALBEDO = alb;
	ROUGHNESS = mix(mix(clamp(ruw, 0.3, 1.0), 0.8, dek) * mix(1.0, 0.7, nat), 1.0, diep);
	SPECULAR = 0.15;
	NORMAL_MAP = normalize(vec3(nrm.xy, max(nrm.z, 0.2))) * 0.5 + 0.5;
	NORMAL_MAP_DEPTH = normaal_sterkte * (1.0 - 0.7 * dek) * (1.0 - diep);
}
