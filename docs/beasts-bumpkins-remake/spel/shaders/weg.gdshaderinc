// Keienweg, gedeeld door weg.gdshader (de wegen, view/wegen.gd) en weg_ghost.gdshader (de deurweg bij het plaatsen,
// view/bouwmenu.gd): grijze kinderkopjes in voeg, procedureel (voronoi in wereld-xz), geen textuur nodig.
// COLOR.r = afstand tot de as van de weg (0 midden, 1 rand); de rand rafelt met ruis (alpha scissor via discard).
// Seizoen: `sneeuw` legt er wit over, `nat` maakt de stenen donker en glanzend (zoals terrein.gdshader).
// GHOST: doorzichtig en getint zoals de gebouw-ghost (ALPHA staat alleen daar: een shader die ALPHA schrijft is
// helemaal doorzichtig, dus de echte weg blijft ondoorzichtig).

uniform float steen_m = 0.32;          // gemiddelde keimaat
uniform vec3 steen_kleur : source_color = vec3(0.56, 0.55, 0.52);
uniform vec3 steen_kleur2 : source_color = vec3(0.47, 0.45, 0.42);
uniform vec3 voeg_kleur : source_color = vec3(0.24, 0.21, 0.17);
uniform float rand_rafel = 0.22;
uniform float sneeuw : hint_range(0.0, 1.0) = 0.0;
uniform float nat : hint_range(0.0, 1.0) = 0.0;
#ifdef GHOST
uniform vec3 ghost_tint : source_color = vec3(0.55, 1.0, 0.5);     // Bouwmenu._ghost_mat: tint, alfa en eigen licht
uniform float ghost_alfa = 0.6;
uniform vec3 ghost_licht : source_color = vec3(0.1, 0.45, 0.1);
#endif

varying vec3 wpos;
varying float rand_af;

vec2 hash2(vec2 p) {
	p = vec2(dot(p, vec2(127.1, 311.7)), dot(p, vec2(269.5, 183.3)));
	return fract(sin(p) * 43758.5453);
}

float hash1(vec2 p) {
	return fract(sin(dot(p, vec2(12.9898, 78.233))) * 43758.5453);
}

float ruis(vec2 p) {
	vec2 i = floor(p);
	vec2 f = fract(p);
	f = f * f * (3.0 - 2.0 * f);
	return mix(mix(hash1(i), hash1(i + vec2(1, 0)), f.x), mix(hash1(i + vec2(0, 1)), hash1(i + vec2(1, 1)), f.x), f.y);
}

// voronoi: x = afstand tot de rand van de cel (F2 - F1), y = celhash
vec2 voronoi(vec2 p) {
	vec2 i = floor(p);
	vec2 f = fract(p);
	float d1 = 8.0;
	float d2 = 8.0;
	vec2 id = vec2(0.0);
	for (int y = -1; y <= 1; y++) {
		for (int x = -1; x <= 1; x++) {
			vec2 g = vec2(float(x), float(y));
			vec2 o = 0.15 + 0.7 * hash2(i + g);
			float d = length(g + o - f);
			if (d < d1) {
				d2 = d1;
				d1 = d;
				id = i + g;
			} else if (d < d2) {
				d2 = d;
			}
		}
	}
	return vec2(d2 - d1, hash1(id));
}

void vertex() {
	wpos = (MODEL_MATRIX * vec4(VERTEX, 1.0)).xyz;
	rand_af = COLOR.r;
}

void fragment() {
	float r = rand_af + (ruis(wpos.xz * 3.1) - 0.5) * rand_rafel * 2.0;
	if (r > 0.92) {
		discard;
	}
	vec2 v = voronoi(wpos.xz / steen_m);
	float voeg = 1.0 - smoothstep(0.06, 0.2, v.x);
	vec3 steen = mix(steen_kleur, steen_kleur2, v.y) * (0.85 + 0.3 * ruis(wpos.xz * 9.0));
	vec3 kleur = mix(steen, voeg_kleur, voeg);
	// aan de rand zakken de stenen weg in de aarde
	kleur = mix(kleur, voeg_kleur * 1.3, smoothstep(0.6, 0.92, r) * 0.6);
	kleur = mix(kleur, kleur * 0.55, nat);
	kleur = mix(kleur, vec3(0.92, 0.94, 0.97), sneeuw * (1.0 - voeg * 0.5));
	ALBEDO = kleur;
	ROUGHNESS = mix(mix(0.82, 0.95, voeg), 0.25, nat * (1.0 - voeg));
	// bolle keien: normaal uit de afstand tot de voeg
	float hd = smoothstep(0.0, 0.35, v.x);
	vec2 e = vec2(0.03, 0.0);
	float hx = smoothstep(0.0, 0.35, voronoi((wpos.xz + e.xy) / steen_m).x) - hd;
	float hz = smoothstep(0.0, 0.35, voronoi((wpos.xz + e.yx) / steen_m).x) - hd;
	vec3 n_wereld = normalize(vec3(-hx * 1.2, 1.0, -hz * 1.2));
	NORMAL = normalize((VIEW_MATRIX * vec4(n_wereld, 0.0)).xyz);
#ifdef GHOST
	ALBEDO *= ghost_tint;
	ALPHA = ghost_alfa;
	EMISSION = ghost_licht;
#endif
}
