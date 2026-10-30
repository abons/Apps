shader_type spatial;
// Mist van oorlog als schermvullende nabewerking (view/mist_view.gd): per pixel de wereldpositie uit de dieptebuffer,
// dan het verkend-raster (1 texel per tegel) op die x/z. Onverkend = zwart, over terrein, water, objecten en eenheden
// tegelijk. Rand zoals het origineel (mission1.png): ronde, golvende bogen van ongeveer een tegel, met een smalle
// gerasterde (dither) zoom op de grens. Lucht en alles buiten het raster tellen als onverkend.
render_mode unshaded, depth_draw_never, depth_test_disabled, cull_disabled, blend_mix, fog_disabled, shadows_disabled;

uniform sampler2D diepte : hint_depth_texture, filter_nearest;
uniform sampler2D verkend : filter_nearest;    // R8, kolommen x rijen
uniform vec2 maat = vec2(192.0, 192.0);
uniform float tegel_m = 2.0;
uniform float aan = 1.0;
uniform float drempel = 0.62;  // > 0,5: bolle zwarte bogen
uniform float golf = 0.5;      // ruis op de drempel: hoe grillig de rand
uniform float zoom = 0.10;      // breedte van de gerasterde zoom (in drempeleenheden)

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
float vk(ivec2 t) {
	if (t.x < 0 || t.y < 0 || t.x >= int(maat.x) || t.y >= int(maat.y)) { return 0.0; }
	return min(texelFetch(verkend, t, 0).r * 255.0, 1.0);   // sim schrijft 0/1
}

void vertex() {
	POSITION = vec4(VERTEX.xy, 1.0, 1.0);
}

void fragment() {
	if (aan < 0.5) { discard; }
	float d = texture(diepte, SCREEN_UV).x;
	float zwart;
	if (d <= 0.0) {
		zwart = 1.0;     // lucht (omgekeerde z: 0 = ver weg)
	} else {
		vec4 v = INV_PROJECTION_MATRIX * vec4(SCREEN_UV * 2.0 - 1.0, d, 1.0);
		v.xyz /= v.w;
		vec3 wp = (INV_VIEW_MATRIX * vec4(v.xyz, 1.0)).xyz;
		vec2 p = wp.xz / tegel_m - 0.5;      // in tegels, 0 = midden van tegel 0
		ivec2 i = ivec2(floor(p));
		vec2 f = fract(p);
		f = f * f * (3.0 - 2.0 * f);          // ronder dan bilineair
		float a = mix(mix(vk(i), vk(i + ivec2(1, 0)), f.x), mix(vk(i + ivec2(0, 1)), vk(i + ivec2(1, 1)), f.x), f.y);
		float n = ruis(wp.xz / tegel_m * 0.8) * 0.7 + ruis(wp.xz / tegel_m * 2.1 + 7.3) * 0.3;
		// drempel boven 0,5: het zwart steekt in bolle bogen het verkende land in, zoals in het origineel
		float dr = drempel + (n - 0.5) * golf;
		if (a >= dr + zoom) {
			discard;
		}
		if (a > dr) {
			// gerasterde zoom: om en om een pixel zwart, zoals tegelframe 36 van het origineel
			ivec2 px = ivec2(FRAGCOORD.xy);
			zwart = ((px.x + px.y) % 2 == 0) ? 1.0 : 0.0;
		} else {
			zwart = 1.0;
		}
	}
	if (zwart < 0.5) { discard; }
	ALBEDO = vec3(0.0);
	ALPHA = 1.0;
}
