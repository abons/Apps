// Deurweg-ghost bij het plaatsen (view/bouwmenu.gd _toon_pad): de keienweg van weg.gdshaderinc, doorzichtig en groen
// of rood getint zoals de gebouw-ghost. Stencil: elke pixel een keer, want achthoeken en stroken overlappen en zouden
// daar dubbel dekken (donkere vlekken op de knopen).
shader_type spatial;
render_mode cull_disabled, depth_draw_never, shadows_disabled;
stencil_mode read, write, compare_not_equal, 7;

#define GHOST
#include "res://shaders/weg.gdshaderinc"
