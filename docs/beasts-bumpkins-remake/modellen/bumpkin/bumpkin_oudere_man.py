"""Oudere man, game-ready (Blender 5.2 headless -> glb voor Godot 4).

Draaien:
  blender -b -P bumpkin_oudere_man.py -- [res=2048] [snel] [vlak] [vergelijk] [poses] [geen_export] [tag=<x>]
Zelfde rig, animaties en straat als de man (bumpkin_basis.py + bumpkin_delen.py); dit script is alleen
de configuratie. Doel: concept/img/oudere_man.jpg (wilde witte haren, borstelige witte wenkbrauwen,
grote neus, bijna tandeloze grijns, grijs hemd met lange mouwen, mouwloze paarse tuniek met V-hals tot
halverwege de dij, donkere riem met koperen gesp, donkergrijze broek, laarzen, knoestige staf met ranken)
en portret bust00 (rimpels, grote neus); sprite elderm (staf links, iets gebogen). 0,96 x de man.

HOUDING: de rustpose blijft de gewone A-pose (zelfde skelet, mesh recht gebouwd). De gebogen houding is een
**additief dat in de clips is gebakken** (BB.houding_additief, na bouw_animaties): per sleutel
q = q_clip @ q_extra. HOUDING (alle zes clips): Spine +6, Spine1 +8, Spine2 +6, Neck -7, Head -10 graden rx
(voorover, kop weer omhoog). STAFARM (alleen idle, lopen, rennen): LeftArm (14, 0, 8), LeftForeArm 62 rx,
zodat de vuist voor het lijf de staf vasthoudt; bouwen en de aanvallen houden hun eigen linkerarm (het spel
verbergt de staf daar). Zelfde clipnamen, lengtes en snelheden; de waarden staan als extra `houding` op
elke actie.

STAF: `prop_staf` is een star kind van bot `prop_L` (linkerhand), 1,45 m x s; BD.plaats_staf zet hem zo dat
hij in idle frame 0 verticaal door de vuist op de grond staat. Het spel schakelt hem zoals de andere props.

Uitvoer bumpkin_oudere_man.glb (armatuur `bumpkin_rig`, alle zes acties, prop_hamer/zwaard/steen op prop_R,
prop_staf op prop_L), atlas textures_oudere_man/. Previews: preview/oudere_man_render.png,
oudere_man_poses.png; oudere_man_vergelijk_*.png nooit committen.

DELEN (tint = baseColorFactor op een lichtgrijze textuur, zoals de man):
| deel      | inhoud                                               | materiaal        | tint     |
| --------- | ---------------------------------------------------- | ---------------- | -------- |
| lijf      | hoofd, oren, hals, handen; oogjes + tand = vast      | mat_lijf + vast  | #e8a383  |
| haar      | wilde witte haardos                                  | mat_haar         | #edebf4  |
| hemd      | grijs hemd, lange mouwen (het hemd van de man)       | mat_hemd         | #858983  |
| tuniek    | mouwloze paarse tuniek, V-hals                       | mat_tuniek       | #674577  |
| broek     | donkergrijze broek                                   | mat_broek        | #55514b  |
| riem      | donkerbruine riem + koperen gesp                     | mat_vast         | wit      |
| laarzen   | omgeslagen leren laarzen                             | mat_laarzen      | #54311e  |
| prop_staf | knoestige staf, ranken, blaadjes (op prop_L)         | mat_vast         | wit      |
"""
import os
import sys

import bpy

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import bumpkin_basis as BB  # noqa: E402
import bumpkin_delen as BD  # noqa: E402
from bumpkin_basis import srgb  # noqa: E402

MAAT_OUD = {"hoogte": 1.33, "kop": 0.27, "schouder": 0.30, "been": 0.47}
HOUDING = {"Spine": (6, 0, 0), "Spine1": (8, 0, 0), "Spine2": (6, 0, 0), "Neck": (-7, 0, 0), "Head": (-10, 0, 0)}
# linkerarm met de staf (alleen idle, lopen, rennen; bouwen en aanvallen houden hun eigen linkerarm)
STAFARM = {"LeftArm": (14, 0, 8), "LeftForeArm": (62, 0, 0), "LeftHand": (0, 0, 0)}


def na_animatie(rig):
    BB.houding_additief(rig, HOUDING)
    BB.houding_additief(rig, STAFARM, acties=("idle", "lopen", "rennen"))
    BD.plaats_staf(rig, bpy.data.objects["prop_staf"])


DELEN = ["lijf", "haar", "hemd", "tuniek", "broek", "riem", "laarzen", "prop_staf"]
SOORT = {"lijf": "lijf", "haar": "haar", "hemd": "hemd", "tuniek": "kledij", "broek": "broek", "riem": "riem",
         "laarzen": "laarzen", "prop_staf": "staf"}
TINTBAAR = {"lijf": "huid", "haar": "haar", "hemd": "hemd", "tuniek": "paars", "broek": "broek", "laarzen": "laars"}
VAST = {"lijf": (3,), "riem": (0, 1), "prop_staf": (0, 1, 2)}
TEXEL = {"lijf": 1.9, "haar": 1.2, "hemd": 1.0, "tuniek": 1.0, "broek": 1.0, "riem": 1.0, "laarzen": 1.1,
         "prop_staf": 0.9}
TEXEL_REGIO = {("lijf", 2): 1.4 / 1.9, ("lijf", 4): 1.4 / 1.9, ("lijf", 5): 0.6 / 1.9, ("lijf", 6): 1.2 / 1.9}

KLEUR = {
    "haar": srgb("#dedce4"), "huid": srgb("#d9987a"), "hemd": srgb("#7c807a"), "paars": srgb("#60406f"),
    "broek": srgb("#4f4b46"), "laars": srgb("#4e2d1b"), "zool": srgb("#2a1a0e"), "riem": srgb("#3e2a1c"),
    "gesp": srgb("#a8823a"), "snor": srgb("#f0eef4"), "metaal": srgb("#a4a4a0"),
    "hout": srgb("#4a3424"), "rank": srgb("#3a3a1c"), "blad": srgb("#5a7a32"),
}

KOP = dict(
    schedel=(0.096, 0.112, 0.124, 0.12), kaak=(0.0, 0.3, 0.2), ogen_ph=0.42, ogen_z=1.115, mond_z=1.03,
    neus=(0, -0.104, -0.034),
    neusprof=((0.032, 0.011, 0.01, 0.014), (0.012, 0.016, 0.017, 0.002), (-0.008, 0.025, 0.024, -0.004),
              (-0.024, 0.026, 0.022, -0.006), (-0.036, 0.018, 0.013, 0.002)),
    oog=(0.0122, 0.0024, 0.0062),
    haar_c=(0, 0.02, 1.17), haar_r=(0.17, 0.13, 0.155, 0.165, 0.15),
    haargrens=[(0.0, 1.22), (0.5, 1.21), (0.9, 1.17), (1.25, 1.13), (1.6, 1.12), (2.3, 1.08), (3.1416, 1.06)],
    klont=(0.16, 0.05),
    gezicht=dict(stoppels=False, mond="lach", lach=0.009, mondbreed=0.025, spleet=0.003, open=0.007, onderlip=0.0035,
                 bovenlip=0.002, lip="#a86058", iris="#6a7080", wang=0.35, neusrood=0.45, rimpel=2.2,
                 voorhoofd=(0.034, 0.043, 0.052, 0.061, 0.07), kraai=(-0.4, -0.15, 0.1, 0.35, 0.6), wal=1.6,
                 lid=0.002, schijf_lid=0.0018, oog_open=(0.0112, 0.0052), brauw=(0.021, 0.007, 0.0062),
                 tand="#d8c8a0", extra=None),
)

TUNIEK0 = [(0.958, 0.122, 0.09, 0.088, 0.05), (0.935, 0.17, 0.112, 0.108, 0.045), (0.9, 0.178, 0.13, 0.124, 0.03),
          (0.86, 0.172, 0.135, 0.128, 0.012), (0.8, 0.168, 0.134, 0.127, 0.0), (0.72, 0.17, 0.136, 0.13, 0.0),
          (0.645, 0.18, 0.142, 0.14, 0.0), (0.57, 0.19, 0.148, 0.146, 0.0), (0.49, 0.198, 0.152, 0.15, 0.0),
          (0.42, 0.204, 0.156, 0.154, 0.0)]
TUNIEK = TUNIEK0


def rimpels_wang(cx, c, h, huid, reg_h):
    """Extra ouderdom: neus-mondplooien en wangrimpels, levervlekjes."""
    import numpy as np
    kop = cx.sk.kop
    kk = kop.k
    P = cx.P
    for sx in (1, -1):
        for off in (0.0, 0.008, 0.016):
            a = kop.neus + np.array([sx * (0.028 + off), 0.004, -0.008 - off]) * kk
            b = kop.mond + np.array([sx * (0.042 + off * 1.4), 0.006, -0.02 - off]) * kk
            ab = b - a
            t = np.clip((P - a) @ ab / (ab @ ab), 0, 1)
            d = np.linalg.norm(P - (a + t[:, None] * ab), axis=1) / kk
            g = BD.gauss(d, 0.0016) * huid * (1.0 if off == 0 else 0.6)
            h -= 0.0008 * kk * g
            c *= (1 - 0.22 * g)[:, None]
    vl = (BD.ruis(P, 70, 131) > 0.55) & huid
    c[vl] = c[vl] * 0.85 + srgb("#8a5a3a") * 0.15


KOP["gezicht"]["extra"] = rimpels_wang


def extra_lijf(B, sk, kop):
    BD.bouw_oren(B, sk, kop, grootte=1.15, uitstaan=0.3, z0=1.085, ph=1.6)
    BD.bouw_tanden(B, sk, kop, [(0.011, 0.009, 0.008)], dz=0.003)


def bouw(sk, coll):
    sk.haarlicht = (0.75, 1.2)
    sk.stof = {"tuniek": dict(weef=0.004, vlek=0.2, kraag=0.85, vuil=0.35, vuil_hoogte=0.14),
               "broek": dict(vuil=1.2)}
    d = {}
    d["hemd"] = BD.bouw_hemd(sk, coll)
    d["tuniek"] = BD.bouw_kledij(sk, coll, "tuniek", TUNIEK, mouwen=False)
    d["broek"] = BD.bouw_broek(sk, coll, "broek", dik=0.9)
    d["riem"] = BD.bouw_riem_op(sk, coll, "riem", z0=0.69, a=0.175, b=0.142, gesp="vierkant", gesp_b=0.03,
                                gesp_h=0.024, breed=0.016)
    d["laarzen"] = BD.bouw_laarzen(sk, coll)
    d["lijf"] = BD.bouw_lijf(sk, coll, kopvorm=KOP, extra=extra_lijf)
    d["haar"] = BD.bouw_haar(sk, coll)
    d["prop_staf"] = BD.bouw_staf(sk, coll, lengte=1.45, ranken=2, bladeren=20)
    return d


OUDERE_MAN = BB.Personage(
    "oudere_man", MAAT_OUD, DELEN, SOORT, TINTBAAR, VAST, TEXEL, KLEUR, bouw, texel_regio=TEXEL_REGIO,
    bak_ext={"haar": (0.03, 0.06), "laarzen": (0.005, 0.02), "hemd": (0.005, 0.018), "tuniek": (0.006, 0.02),
             "broek": (0.004, 0.015), "riem": (0.004, 0.015), "lijf": (0.008, 0.025), "prop_staf": (0.004, 0.012)},
    kleurbak=("haar",),
    krullen=lambda sk, coll: {"haar": [BB.krullen(sk, coll, 1500 if BB.SNEL else 7000, lengte=(0.025, 0.05),
                                                  rc=(0.003, 0.006), rt=(0.0016, 0.0024), draai=(0.4, 1.0),
                                                  licht=(0.95, 1.12), warm=(-0.04, 0.03), seed=21)]},
    sprites=("elderm", "elderm"),
    na_animatie=na_animatie,
    extra={"bust": "bust00", "weefsel": ("hemd", "tuniek"), "prop_delen": {"prop_staf": "prop_L"},
           "zichtbare_props": ("prop_staf",),
           "vergelijk_actie": ("idle", 0), "haar_normaal": 0.35},
)

if __name__ == "__main__":
    BB.bouw_personage(OUDERE_MAN)
