shader_type canvas_item;
// Minikaart (view/minikaart.gd): de terreinkleuren (TEXTURE, 1 texel per tegel) maal het verkend-raster van de mist
// (R8, 0/1 per tegel). Onverkend = zwart, zoals het origineel (1_lefttop.png). aan = 0: mist uit, alles zichtbaar.

uniform sampler2D verkend : filter_nearest;
uniform float aan = 1.0;

void fragment() {
	vec4 c = texture(TEXTURE, UV);
	float v = max(step(0.5, texture(verkend, UV).r * 255.0), 1.0 - aan);
	COLOR = vec4(c.rgb * v, 1.0);
}
