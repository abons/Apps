"""Volwassen mannelijke bumpkin, game-ready (Blender 5.2 headless -> glb voor Godot 4).

Draaien:
  blender -b -P bumpkin_man.py -- [res=2048] [snel] [vergelijk] [poses] [geen_export] [ref=<map>]
- `snel`: bake op 512 met weinig samples.
- `vergelijk`: preview/man_vergelijk_1x.png (sprite naast render op HD-pixelschaal),
  preview/man_vergelijk_close.png en preview/man_detail.png. Bevatten de sprite: nooit committen.
- `poses`: preview/man_poses.png, extreme standen uit de rig-animaties (vervorming).
Doel: ref/gemini_man_v4.jpg (grijsgroen hemd, paarse tuinbroek, korte rode krullenbol, hangsnor).

Uitvoer bumpkin_man.glb: armatuur `bumpkin_rig` met alle acties, losse delen op hetzelfde skelet,
een gedeelde atlas in textures_man/ (man_kleur.jpg, man_normaal.png, man_orm.png; R=AO G=ruw B=metaal).

DELEN (mesh-object = glTF-node, stabiele namen; elk deel los te vervangen door een outfit/kapsel):
| deel          | inhoud                                        | materiaal       | tint (baseColorFactor) |
| ------------- | --------------------------------------------- | --------------- | ---------------------- |
| lijf          | hoofd, nek, handen (huid); oogjes = vast       | mat_lijf + vast | #e79c65 huid           |
| haar          | krullenbol                                    | mat_haar        | #b15830 roodbruin      |
| snor          | hangsnor (zelfde materiaal als haar)          | mat_haar        | #b15830                |
| hemd          | grijsgroen werkhemd, lange mouwen, open kraag | mat_hemd        | #97a288 grijsgroen     |
| tuinbroek     | pijpen, heupstuk, slab, rugpand, bretels      | mat_tuinbroek   | #833d92 paars          |
|               | bretelgespen = vast                           | + mat_vast      |                        |
| riem          | riem en gele gesp                             | mat_vast        | wit (echte kleur)      |
| laarzen       | omgeslagen leren laarzen                      | mat_laarzen     | #543017 bruin          |
| prop_strootje | strohalm, kind van bot Head                   | strootje        | vast #d4ad55           |
Tintbare delen: de kleurtextuur is lichtgrijs (gemiddeld ~0,86) met alle detail als luminantie
(plus een beetje relatieve tint, bv. rode wangen, vuil); kleur = baseColorFactor x textuur. In Godot
per eenheid albedo_color (of een instance-parameter) zetten; geen nieuwe texturen nodig.
mat_vast heeft factor wit en draagt echte kleuren (gesp geel, metaal, oogwit/iris).
Plus de props van de rig (prop_hamer/zwaard/steen) op prop_R, zodat bumpkin.gd ze vindt.

Gedeelde code: bumpkin_basis.py (straat) en bumpkin_delen.py (delen per soort); dit script is alleen
de configuratie van de man plus zijn strootje.

Bouw: elk deel is een loft van ringen langs de gewrichten van het skelet uit bumpkin_rig.py (rust =
A-pose), dus de mesh volgt de rustpose en de `maat` van de rig (kind en oudere later via MAAT_MAN).
Gewichten zijn analytisch: per deel een keten van botten met lineaire overgangen rond elk gewricht.
Hoog-poly = de lage mesh gesubdivideerd met plooien/kreukels (numpy) plus krulspiralen; daarvan bakt
Cycles normaal, AO en krulkleur. Weefsel, naden, steken, zakken, leer en gezicht komen er in numpy bij,
per texel uit een gebakken positie- en UV(m)-kaart."""
import math
import os
import sys

import bpy
import numpy as np
from mathutils import Matrix

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import bumpkin_basis as BB  # noqa: E402
import bumpkin_delen as BD  # noqa: E402
from bumpkin_basis import Bouwer, keten, ring, srgb  # noqa: E402

# Maat voor de rig: smallere schouders dan de rig-standaard (0,40 tussen de gewrichten maakt de jas
# 0,52 breed; de sprite is ~0,40 over de jas).
MAAT_MAN = {"schouder": 0.31}
DELEN = ["lijf", "haar", "snor", "hemd", "tuinbroek", "riem", "laarzen"]
TINTBAAR = {"lijf": "huid", "haar": "haar", "snor": "haar", "hemd": "hemd", "tuinbroek": "paars", "laarzen": "laars"}
VAST = {"lijf": (3,), "tuinbroek": (6,), "riem": (0, 1)}     # regio's met echte kleur (mat_vast)
TEXEL = {"lijf": 1.9, "haar": 1.2, "snor": 1.9, "hemd": 1.0, "tuinbroek": 1.0, "riem": 1.0, "laarzen": 1.1}
TEXEL_REGIO = {("lijf", 2): 1.4 / 1.9, ("lijf", 4): 1.4 / 1.9, ("lijf", 5): 0.6 / 1.9}

# Albedo per deel (lineair). Iets lichter dan de sprite-middentoon: die is al belicht.
KLEUR = {
    "haar": srgb("#a5522c"), "huid": srgb("#d8925e"), "paars": srgb("#7a3888"),
    "hemd": srgb("#8d977f"), "metaal": srgb("#a4a4a0"), "snor": srgb("#6e3a1e"),
    "riem": srgb("#5a3a1f"), "gesp": srgb("#efbf00"), "laars": srgb("#4e2c15"), "zool": srgb("#2a1a0e"),
}


def bouw(sk, coll):
    d = {}
    d["hemd"] = BD.bouw_hemd(sk, coll)
    d["tuinbroek"] = BD.bouw_tuinbroek(sk, coll)
    d["riem"] = BD.bouw_riem(sk, coll)
    d["laarzen"] = BD.bouw_laarzen(sk, coll)
    d["lijf"] = BD.bouw_lijf(sk, coll)
    d["snor"] = BD.bouw_snor(sk, coll)
    d["haar"] = BD.bouw_haar(sk, coll)
    return d


def maak_strootje(sk, rig):
    """Strohalm in de linker mondhoek, met een aartje; los te schakelen (prop_strootje, kind van Head)."""
    kop = sk.kop
    kk = kop.k
    start = kop.mond + np.array([0.034, -0.004, -0.006]) * kk
    d = np.array([0.72, -0.5, 0.2])
    d /= np.linalg.norm(d)
    B = Bouwer()
    n = 14
    pts = [start + d * 0.13 * kk * i / (n - 1) + np.array([0, 0, -0.012 * kk]) * (i / (n - 1)) ** 2 for i in range(n)]
    fr = keten(pts, list(np.linspace(-0.004, 0.13 * kk, n)), ref=(0, 0, 1))
    rings = []
    for i, (pos, t, f, sd) in enumerate(fr):
        r = 0.0024 * kk
        if i > n - 5:                                             # aartje
            u = (i - (n - 5)) / 4
            r = (0.0024 + 0.006 * math.sin(math.pi * min(u * 1.2, 1))) * kk
        rings.append(ring(pos, sd, f, r, r * 0.8, 6))
    b0, _ = B.grid(np.array(rings), True)
    B.kap(b0 + 6 * (n - 1), 6, fr[-1][0] + fr[-1][1] * 0.008 * kk)
    o = B.obj("prop_strootje", bpy.context.scene.collection)
    m = bpy.data.materials.new("strootje")
    m.use_nodes = True
    bs = m.node_tree.nodes["Principled BSDF"]
    bs.inputs["Base Color"].default_value = (*srgb("#d4ad55"), 1)
    bs.inputs["Roughness"].default_value = 0.55
    o.data.materials.append(m)
    o.data.uv_layers.active.name = "UVMap"
    o.parent = rig
    o.parent_type = "BONE"
    o.parent_bone = "Head"
    bpy.context.view_layer.update()
    o.matrix_world = Matrix.Identity(4)
    return o


MAN = BB.Personage(
    "man", MAAT_MAN, DELEN, {"haar": "haar", "snor": "snor"}, TINTBAAR, VAST, TEXEL, KLEUR, bouw,
    texel_regio=TEXEL_REGIO,
    bak_ext={"haar": (0.024, 0.05), "laarzen": (0.005, 0.02), "hemd": (0.005, 0.018), "riem": (0.004, 0.015),
             "tuinbroek": (0.004, 0.015), "lijf": (0.008, 0.025), "snor": (0.006, 0.02)},
    kleurbak=("haar",),
    krullen=lambda sk, coll: {"haar": [BB.krullen(sk, coll, 1500 if BB.SNEL else 4200)]},
    sprites=("m_still", "m_walk"),
    props=lambda sk, rig, delen: maak_strootje(sk, rig),
    extra={"mat": {"snor": "mat_haar"},
           "vlak": {"hemd": ["hemd", "hemd"], "tuinbroek": ["paars"] * 6 + ["metaal"], "riem": ["riem", "gesp"],
                    "laarzen": ["laars", "zool"], "lijf": ["huid"] * 6, "snor": ["snor"], "haar": ["haar"]}},
)

if __name__ == "__main__":
    BB.bouw_personage(MAN)
