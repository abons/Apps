class_name GrasVarianten
extends RefCounted
## Grasvarianten om naast elkaar te bekijken (2026-10-31, lokaal/concept/gras_vergelijk.html): `-- --gras=naam` zet een
## set shader-uniforms op het terreinmateriaal (pc en mobiel dezelfde namen, zie shaders/terrein*.gdshader); losse
## uniforms erbovenop met `-- --gras.<uniform>=x` of `=r,g,b`. Zonder optie verandert er niets: de shader-standaarden
## zijn het beeld van 144ea40. Alleen weergave; de sim ziet hier niets van.

const SETS := {
	"a": {},   # huidig (144ea40): diep donkergroen
	"b": {     # iets minder verzadigd, grote vlekken geelgroen/olijf
		"gras_verzadiging": 0.75,
		"gras_macro": 0.8,
		"gras_macro_kleur": Color(0.26, 0.30, 0.05),
	},
	"c": {     # als het origineel (screenshot): olijfgroen, lichte vlekken sterker
		"gras_kleur": Color(0.24, 0.27, 0.02),
		"gras_licht": Color(0.34, 0.36, 0.05),
		"gras_licht_sterkte": 1.4,
	},
	"d": {     # oud licht gras van voor 144ea40: textuurkleur, geen stipjes
		"gras_herkleur": 0.0,
		"stip_sterkte": 0.0,
	},
	"e": {     # voorstel: donker als het origineel, iets grijzer, subtiele grote vlekken, stipjes blijven
		"gras_kleur": Color(0.17, 0.25, 0.03),
		"gras_licht": Color(0.25, 0.31, 0.05),
		"gras_verzadiging": 0.85,
		"gras_macro": 0.6,
		"gras_macro_kleur": Color(0.27, 0.28, 0.04),
	},
}


static func pas_toe(mat: ShaderMaterial) -> void:
	for a in OS.get_cmdline_user_args():
		if a.begins_with("--gras="):
			var naam := a.substr(7)
			if not SETS.has(naam):
				push_warning("[gras] onbekende variant %s (bekend: %s)" % [naam, ", ".join(SETS.keys())])
			for k in SETS.get(naam, {}):
				mat.set_shader_parameter(k, SETS[naam][k])
	for a in OS.get_cmdline_user_args():
		if a.begins_with("--gras.") and a.contains("="):
			var kv := a.substr(7).split("=", true, 1)
			var d := kv[1].split(",")
			mat.set_shader_parameter(kv[0], Color(float(d[0]), float(d[1]), float(d[2])) if d.size() == 3 else float(d[0]))
