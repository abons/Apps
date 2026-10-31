class_name GedachteIkonen
extends RefCounted
## Eigen ikonen voor de gedachten (sim/gedachten.gd): brood, ei, melk(kan), appel, cider, water(druppel), hart, blij,
## somber en boos gezicht. Getekend als SVG in deze file (geen originele sprites, geen importstap: Image.load_svg_from_string),
## in een wolkje zoals het origineel (thoughts-sprite), met een rode rand als de gedachte dringend is.

const ZIJ := 128                      ## SVG-maat; gerenderd op `schaal` x
const _WOLK_RAND := "#3a3550"
const _WOLK_DRINGEND := "#d0302a"
const _WOLK_VUL := "#f1eefa"
const _WOLK_VUL_DRINGEND := "#ffe1dc"

## Ikoon-inhoud, getekend in een vak van 128 met het midden rond (64, 56) (het wolkje heeft onderaan zijn staartjes).
const IKOON := {
	"brood": """<g stroke="#5a3210" stroke-width="3" stroke-linejoin="round">
<path d="M30 70 Q28 44 52 40 Q64 34 76 40 Q100 44 98 70 Q98 76 92 76 L36 76 Q30 76 30 70 Z" fill="#d89a4c"/>
<path d="M44 52 L52 62 M58 48 L66 60 M72 48 L80 60" fill="none" stroke="#f3d39a" stroke-width="4" stroke-linecap="round"/></g>""",
	"ei": """<ellipse cx="64" cy="58" rx="19" ry="25" fill="#fbf3e2" stroke="#7a5a3a" stroke-width="3"/>
<ellipse cx="57" cy="49" rx="5" ry="8" fill="#ffffff"/>""",
	"melk": """<g stroke="#2e3b55" stroke-width="3" stroke-linejoin="round">
<path d="M76 46 Q92 46 90 60 Q88 72 74 72" fill="none" stroke-width="5"/>
<path d="M46 32 L74 32 L72 40 L78 50 L78 80 Q78 84 74 84 L46 84 Q42 84 42 80 L42 50 L48 40 Z" fill="#ffffff"/>
<path d="M42 58 L78 58 L78 66 L42 66 Z" fill="#4f86c6"/></g>""",
	"appel": """<path d="M64 44 Q50 34 40 46 Q30 60 42 76 Q52 88 64 82 Q76 88 86 76 Q98 60 88 46 Q78 34 64 44 Z" fill="#d42a2a" stroke="#6a1010" stroke-width="3"/>
<path d="M64 44 Q64 34 68 28" fill="none" stroke="#5a3210" stroke-width="4" stroke-linecap="round"/>
<path d="M68 34 Q80 24 88 32 Q78 40 68 34 Z" fill="#3c9a3c" stroke="#1d5a1d" stroke-width="2"/>
<ellipse cx="50" cy="56" rx="4" ry="7" fill="#ff9a8a"/>""",
	"cider": """<g stroke="#3a2410" stroke-width="3" stroke-linejoin="round">
<path d="M78 46 Q94 46 92 60 Q90 72 78 72" fill="none" stroke-width="6"/>
<path d="M40 38 L80 38 L78 82 Q78 86 74 86 L46 86 Q42 86 42 82 Z" fill="#8a5a2c"/>
<path d="M44 48 L76 48 L75 80 L45 80 Z" fill="#e0a23a" stroke="none"/>
<path d="M38 40 Q44 30 52 36 Q58 28 66 34 Q74 28 82 38 Q80 44 72 42 L48 42 Q40 46 38 40 Z" fill="#fff6dc"/></g>""",
	"water": """<path d="M64 26 Q86 56 86 68 Q86 86 64 86 Q42 86 42 68 Q42 56 64 26 Z" fill="#4aa0e6" stroke="#1d4f86" stroke-width="3" stroke-linejoin="round"/>
<path d="M54 62 Q52 72 58 78" fill="none" stroke="#d8f0ff" stroke-width="5" stroke-linecap="round"/>""",
	"liefde": """<path d="M64 84 L38 58 Q28 46 38 36 Q50 26 64 42 Q78 26 90 36 Q100 46 90 58 Z" fill="#e0263a" stroke="#6a0a16" stroke-width="3" stroke-linejoin="round"/>
<ellipse cx="46" cy="44" rx="5" ry="7" fill="#ff9aa6"/>""",
	"blij": """<circle cx="64" cy="58" r="26" fill="#ffd23a" stroke="#8a5a00" stroke-width="3"/>
<circle cx="55" cy="51" r="3.5" fill="#3a2400"/><circle cx="73" cy="51" r="3.5" fill="#3a2400"/>
<path d="M50 62 Q64 76 78 62" fill="none" stroke="#3a2400" stroke-width="4" stroke-linecap="round"/>""",
	"somber": """<circle cx="64" cy="58" r="26" fill="#9aaac4" stroke="#2e3b55" stroke-width="3"/>
<circle cx="55" cy="52" r="3.5" fill="#1d2433"/><circle cx="73" cy="52" r="3.5" fill="#1d2433"/>
<path d="M51 72 Q64 62 77 72" fill="none" stroke="#1d2433" stroke-width="4" stroke-linecap="round"/>
<path d="M76 58 Q72 66 76 68 Q80 66 76 58 Z" fill="#4aa0e6"/>""",
	"boos": """<circle cx="64" cy="58" r="26" fill="#e8553a" stroke="#6a1a0a" stroke-width="3"/>
<path d="M48 44 L60 50 M80 44 L68 50" stroke="#2a0a00" stroke-width="4" stroke-linecap="round"/>
<circle cx="56" cy="54" r="3.5" fill="#2a0a00"/><circle cx="72" cy="54" r="3.5" fill="#2a0a00"/>
<path d="M52 72 Q64 64 76 72" fill="none" stroke="#2a0a00" stroke-width="4" stroke-linecap="round"/>""",
}

static var _cache := {}


## Wolkje van cirkels: eerst alle cirkels met een dikke rand, dan dezelfde cirkels gevuld eroverheen (één omtrek).
static func _wolk(rand: String, vul: String) -> String:
	var c := [[64, 58, 36], [36, 56, 22], [92, 56, 22], [48, 32, 20], [80, 32, 20], [46, 80, 18], [82, 80, 18], [64, 86, 16]]
	var s := ""
	for k in c:
		s += '<circle cx="%d" cy="%d" r="%d" fill="%s" stroke="%s" stroke-width="%d"/>' % [k[0], k[1], k[2], rand, rand, 10 if rand == _WOLK_DRINGEND else 7]
	s += '<circle cx="22" cy="108" r="8" fill="%s" stroke="%s" stroke-width="4"/>' % [vul, rand]
	s += '<circle cx="10" cy="122" r="5" fill="%s" stroke="%s" stroke-width="3"/>' % [vul, rand]
	for k in c:
		s += '<circle cx="%d" cy="%d" r="%d" fill="%s"/>' % [k[0], k[1], k[2], vul]
	return s


static func svg(naam: String, wolk := true, dringend := false) -> String:
	var s := '<svg xmlns="http://www.w3.org/2000/svg" width="%d" height="%d" viewBox="0 0 128 128">' % [ZIJ, ZIJ]
	if wolk:
		s += _wolk(_WOLK_DRINGEND, _WOLK_VUL_DRINGEND) if dringend else _wolk(_WOLK_RAND, _WOLK_VUL)
	s += IKOON.get(naam, "")
	return s + "</svg>"


## Textuur (gecachet). `wolk` = in het wolkje; `mipmaps` voor gebruik in 3D (Sprite3D boven het hoofd).
static func textuur(naam: String, wolk := true, dringend := false, schaal := 2.0, mipmaps := false) -> Texture2D:
	var sleutel := "%s|%s|%s|%s|%s" % [naam, wolk, dringend, schaal, mipmaps]
	if _cache.has(sleutel):
		return _cache[sleutel]
	var img := Image.new()
	if img.load_svg_from_string(svg(naam, wolk, dringend), schaal) != OK:
		return null
	if mipmaps:
		img.generate_mipmaps()
	var t := ImageTexture.create_from_image(img)
	_cache[sleutel] = t
	return t
