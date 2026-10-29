"""Jongen (kind, man), game-ready (Blender 5.2 headless -> glb voor Godot 4).

Draaien:
  blender -b -P bumpkin_jongen.py -- [res=2048] [snel] [vlak] [vergelijk] [poses] [geen_export] [tag=<x>]
Zelfde rig, animaties en straat als de man (bumpkin_basis.py + bumpkin_delen.py); dit script is alleen
de configuratie. Doel: portret bust02 en concept/img/jongen.jpg (paarse tuniek tot halverwege de dij met
staande kraag en V-spleet, grijze riem met grote ronde gele gesp, bruine broek, omgeslagen laarzen,
roodbruin bloempotkapsel, flaporen, twee konijnentanden); sprite kidm. Lengte 0,81 x de man (spec.md).

Uitvoer bumpkin_jongen.glb: armatuur `bumpkin_rig` (zelfde botten, MAAT_JONGEN: 1,11 m, kop 0,33) met
alle zes acties, props op prop_R, atlas textures_jongen/ (jongen_kleur.jpg, _normaal.png, _orm.png).
Previews: preview/jongen_render.png, jongen_poses.png; jongen_vergelijk_*.png nooit committen.

DELEN (tint = baseColorFactor op een lichtgrijze textuur, zoals de man):
| deel    | inhoud                                           | materiaal        | tint     |
| ------- | ------------------------------------------------ | ---------------- | -------- |
| lijf    | hoofd, flaporen, hals, handen; oogjes + tanden    | mat_lijf + vast  | #e89a78  |
|         | = vast (mat_vast)                                 |                  |          |
| haar    | roodbruin bloempotkapsel met pony                 | mat_haar         | #782c1d  |
| tuniek  | paarse tuniek, lange mouwen, staande kraag        | mat_tuniek       | #943087  |
| broek   | bruine wollen broek                               | mat_broek        | #654630  |
| riem    | grijze riem + ronde gele gesp                     | mat_vast         | wit      |
| laarzen | omgeslagen leren laarzen                          | mat_laarzen      | #54311e  |
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import bumpkin_basis as BB  # noqa: E402
import bumpkin_delen as BD  # noqa: E402
from bumpkin_basis import srgb  # noqa: E402

MAAT_JONGEN = {"hoogte": 1.11, "kop": 0.33, "schouder": 0.25, "been": 0.47}
DELEN = ["lijf", "haar", "tuniek", "broek", "riem", "laarzen"]
SOORT = {"lijf": "lijf", "haar": "glad", "tuniek": "kledij", "broek": "broek", "riem": "riem", "laarzen": "laarzen"}
TINTBAAR = {"lijf": "huid", "haar": "haar", "tuniek": "paars", "broek": "broek", "laarzen": "laars"}
VAST = {"lijf": (3,), "riem": (0, 1)}
TEXEL = {"lijf": 1.9, "haar": 1.2, "tuniek": 1.0, "broek": 1.0, "riem": 1.0, "laarzen": 1.1}
TEXEL_REGIO = {("lijf", 2): 1.4 / 1.9, ("lijf", 4): 1.4 / 1.9, ("lijf", 5): 0.6 / 1.9}

KLEUR = {
    "haar": srgb("#70281a"), "huid": srgb("#d99070"), "paars": srgb("#8a2c7e"), "broek": srgb("#5e412c"),
    "laars": srgb("#4e2d1b"), "zool": srgb("#2a1a0e"), "riem": srgb("#77705c"), "gesp": srgb("#e8bf10"),
    "snor": srgb("#5a2618"),
}

KOP = dict(
    schedel=(0.1, 0.11, 0.132, 0.112), kaak=(0.02, 0.3, 0.1), ogen_ph=0.42, ogen_z=1.115, mond_z=1.04,
    neus=(0, -0.104, -0.026),
    neusprof=((0.026, 0.009, 0.009, 0.012), (0.01, 0.012, 0.012, 0.006), (-0.006, 0.018, 0.016, 0.0),
              (-0.016, 0.019, 0.015, -0.002), (-0.023, 0.013, 0.01, 0.004)),
    oog=(0.0152, 0.007, 0.008),
    haar_c=(0, 0.012, 1.18), haar_r=(0.118, 0.124, 0.132, 0.15, 0.13),
    haargrens=[(0.0, 1.172), (0.5, 1.168), (0.9, 1.15), (1.25, 1.14), (1.6, 1.12), (2.3, 1.06), (3.1416, 1.03)],
    klont=(0.05, 0.015),
    gezicht=dict(stoppels=False, mond="lach", lach=0.012, mondbreed=0.036, onderlip=0.004, bovenlip=0.0022,
                 spleet=0.003, open=0.008, lip="#c06a62", iris="#5a3a22", wang=0.5, neusrood=0.2, rimpel=0.0, kraai=(),
                 wal=0.3, lid=0.007, schijf_lid=0.007, oog_open=(0.0142, 0.0082), brauw=(0.0255, 0.004, 0.0036),
                 tand="#ece4cc"),
)

# tuniek: (z0, a, voor, achter, halve opening); staande kraag met een korte V-spleet
TUNIEK = [(0.992, 0.074, 0.07, 0.068, 0.008), (0.975, 0.088, 0.076, 0.074, 0.007), (0.952, 0.135, 0.095, 0.094, 0.004),
          (0.925, 0.165, 0.113, 0.11, 0.0), (0.88, 0.165, 0.12, 0.116, 0.0), (0.8, 0.16, 0.122, 0.118, 0.0),
          (0.72, 0.158, 0.124, 0.12, 0.0), (0.645, 0.168, 0.13, 0.13, 0.0), (0.57, 0.178, 0.136, 0.136, 0.0),
          (0.5, 0.185, 0.14, 0.14, 0.0)]


def extra_lijf(B, sk, kop):
    BD.bouw_oren(B, sk, kop, grootte=1.42, uitstaan=0.62, z0=1.095, ph=1.58)
    BD.bouw_tanden(B, sk, kop, [(-0.0068, 0.0125, 0.014), (0.0068, 0.0125, 0.014)], dz=0.0045)


def bouw(sk, coll):
    sk.stof = {"tuniek": dict(weef=0.004, vlek=0.1, kraag=0.9), "broek": dict(vuil=1.0)}
    sk.haarstijl = {"kruin": (0, 0.03, 0.15), "strengen": 52, "warm": (0.05, 0.0, -0.05)}
    d = {}
    d["tuniek"] = BD.bouw_kledij(sk, coll, "tuniek", TUNIEK, mouw_dik=0.96, kraag=(0.016,))
    d["broek"] = BD.bouw_broek(sk, coll, "broek", dik=0.86)
    d["riem"] = BD.bouw_riem_op(sk, coll, "riem", z0=0.69, a=0.166, b=0.132, gesp="rond", gesp_b=0.04,
                                gesp_h=0.034, breed=0.018)
    d["laarzen"] = BD.bouw_laarzen(sk, coll)
    d["lijf"] = BD.bouw_lijf(sk, coll, kopvorm=KOP, extra=extra_lijf)
    d["haar"] = BD.bouw_haar_glad(sk, coll)
    return d


JONGEN = BB.Personage(
    "jongen", MAAT_JONGEN, DELEN, SOORT, TINTBAAR, VAST, TEXEL, KLEUR, bouw, texel_regio=TEXEL_REGIO,
    bak_ext={"haar": (0.01, 0.03), "laarzen": (0.005, 0.02), "tuniek": (0.006, 0.02), "broek": (0.004, 0.015),
             "riem": (0.004, 0.015), "lijf": (0.008, 0.025)},
    kleurbak=(), sprites=("kidm", "kidm"),
    extra={"bust": "bust02", "weefsel": ("tuniek", "broek"), "haardelen": ("haar",)},
)

if __name__ == "__main__":
    BB.bouw_personage(JONGEN)
