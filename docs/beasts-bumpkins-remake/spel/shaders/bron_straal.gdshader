shader_type spatial;
render_mode blend_mix, depth_draw_opaque, cull_disabled;
// Put (bron.glb, mesh `bron_straal`): de waterstraal stroomt. UV.x = dwars (0..1), en props.py bron() zet v = 2 t
// langs de straal (t = 0 bij de tuit); glTF draait v om, dus hier UV.y = 1 - 2 t: een fase UV.y * k + TIME * w
// schuift met de tijd naar grotere t, de straal af. Alleen sinussen, geen textuur (view/bron_water.gd).

uniform vec3 kleur : source_color = vec3(0.62, 0.74, 0.84);
uniform float snelheid = 1.0;

void fragment() {
	float t = TIME * snelheid;
	float u = UV.x;
	float v = UV.y;
	float s1 = sin(v * 9.0 + t * 7.0 + sin(u * 11.0) * 0.9);
	float s2 = sin(v * 19.0 + t * 11.0 + u * 23.0);
	float streep = 0.5 + 0.3 * s1 + 0.2 * s2;
	float rand = smoothstep(0.0, 0.3, u) * smoothstep(1.0, 0.7, u);
	ALBEDO = mix(kleur * 0.75, vec3(0.96, 0.98, 1.0), smoothstep(0.55, 0.95, streep));
	ALPHA = (0.40 + 0.45 * streep) * mix(0.45, 1.0, rand);
	ROUGHNESS = 0.1;
	SPECULAR = 0.7;
}
