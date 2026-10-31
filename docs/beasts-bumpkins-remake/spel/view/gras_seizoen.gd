class_name GrasSeizoen
extends RefCounted
## Gras per seizoen (besluit gebruiker 2026-10-31, lokaal/concept/gras_vergelijk.html "Seizoenen"): de grasuniforms van
## shaders/terrein*.gdshader per seizoen, in het laatste deel van het seizoen zacht naar het volgende (zelfde smoothstep
## als Wereld._geblend), elk frame op de cpu gemengd: pc en telefoon dezelfde uniforms, geen extra textuur-lookups.
## Bronnen: lente = variant e (voorstel), zomer = variant c (olijf als het scherm van het origineel, ~74,85,23), herfst =
## de herfsttegel van het origineel (lokaal/map1/grass_spring_fall.png: lente 5,82,4 -> herfst 61,69,0, dus geler en
## minder groen) op de olijfbasis van c, winter = de sneeuwtegel (bb_original/winter.png 195,207,218): de sneeuw zelf
## komt uit Wereld.SNEEUW, het gras eronder (randen, dooi) is grijsgroen berijpt en zonder stipjes.
## `-- --gras=naam` of `--gras.<uniform>=x` (view/gras_varianten.gd) zet dit uit, voor vergelijkingsbeelden.

const LENTE := {
	"gras_kleur": Color(0.17, 0.25, 0.03),
	"gras_licht": Color(0.25, 0.31, 0.05),
	"gras_licht_sterkte": 1.0,
	"gras_verzadiging": 0.85,
	"gras_helderheid": 1.0,
	"gras_macro": 0.6,
	"gras_macro_kleur": Color(0.27, 0.28, 0.04),
	"stip_sterkte": 1.0,
	"gras_droog_mee": 0.0,
}
const ZOMER := {
	"gras_kleur": Color(0.24, 0.27, 0.02),
	"gras_licht": Color(0.34, 0.36, 0.05),
	"gras_licht_sterkte": 1.4,
	"gras_verzadiging": 1.0,
	"gras_helderheid": 1.0,
	"gras_macro": 0.0,
	"gras_macro_kleur": Color(0.27, 0.28, 0.04),
	"stip_sterkte": 1.0,
	"gras_droog_mee": 0.0,
}
const HERFST := {
	"gras_kleur": Color(0.27, 0.26, 0.015),
	"gras_licht": Color(0.37, 0.34, 0.04),
	"gras_licht_sterkte": 1.2,
	"gras_verzadiging": 0.9,
	"gras_helderheid": 1.0,
	"gras_macro": 0.45,
	"gras_macro_kleur": Color(0.33, 0.22, 0.04),   # bruine vlekken
	"stip_sterkte": 0.7,
	"gras_droog_mee": 0.0,
}
const WINTER := {
	"gras_kleur": Color(0.20, 0.23, 0.13),
	"gras_licht": Color(0.30, 0.33, 0.24),
	"gras_licht_sterkte": 1.0,
	"gras_verzadiging": 0.55,
	"gras_helderheid": 1.05,
	"gras_macro": 0.0,
	"gras_macro_kleur": Color(0.33, 0.22, 0.04),
	"stip_sterkte": 0.0,
	"gras_droog_mee": 0.0,
}
const SETS := [LENTE, ZOMER, HERFST, WINTER]


## Mengfactor naar het volgende seizoen bij voortgang f (0..1) in het seizoen: 0 tot 0,7, dan zacht naar 1.
static func meng(f: float) -> float:
	return smoothstep(0.7, 1.0, f)


## Uniformwaarden voor seizoen s (0 lente .. 3 winter) bij voortgang f in dat seizoen.
static func waarden(s: int, f: float) -> Dictionary:
	var a: Dictionary = SETS[posmod(s, 4)]
	var b: Dictionary = SETS[posmod(s + 1, 4)]
	var k := meng(f)
	var uit := {}
	for n in a:
		uit[n] = (a[n] as Color).lerp(b[n], k) if a[n] is Color else lerpf(a[n], b[n], k)
	return uit


static func pas_toe(mat: ShaderMaterial, s: int, f: float) -> void:
	var v := waarden(s, f)
	for n in v:
		mat.set_shader_parameter(n, v[n])
