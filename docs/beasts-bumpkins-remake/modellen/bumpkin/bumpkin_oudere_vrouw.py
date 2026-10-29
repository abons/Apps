"""Oudere vrouw, game-ready (Blender 5.2 headless -> glb voor Godot 4).

Draaien:
  blender -b -P bumpkin_oudere_vrouw.py -- [res=2048] [snel] [vlak] [vergelijk] [poses] [geen_export] [tag=<x>]
Zelfde rig, animaties en straat als de man (bumpkin_basis.py + bumpkin_delen.py); dit script is alleen
de configuratie. Doel: concept/img/oudere_vrouw.jpg (grijs haar strak naar achteren in een knot, gele
schulpkraag, grijsgroen open jasje met grijze omgeslagen manchetten, leren riem met gesp, lange paarse jurk
tot de enkels, laarzen, wandelstok met klimop, hand bovenop) en portret bust17 (lange neus, puntkin,
rimpels, gele kraag); sprite elderf. 0,96 x de man.

HOUDING: rustpose = de gewone A-pose. De gebogen houding is een **additief dat in de clips is gebakken**
(BB.houding_additief): HOUDING op alle zes clips (Spine +6, Spine1 +6, Spine2 +5, Neck -6, Head -9 rx);
STAFARM alleen op idle, lopen, rennen (LeftArm (16, 0, 10), LeftForeArm 22 rx: hand op de stok); bouwen
en de aanvallen houden hun eigen linkerarm. Zelfde clipnamen, lengtes en snelheden; extra `houding` per actie.

STAF: `prop_staf` (wandelstok met klimop) is een star kind van bot `prop_L`; BD.plaats_staf zet hem zo dat
hij in idle frame 0 verticaal onder de hand op de grond staat.

Uitvoer bumpkin_oudere_vrouw.glb (armatuur `bumpkin_rig`, alle zes acties, prop_hamer/zwaard/steen op
prop_R, prop_staf op prop_L), atlas textures_oudere_vrouw/. Previews: preview/oudere_vrouw_render.png,
oudere_vrouw_poses.png; oudere_vrouw_vergelijk_*.png nooit committen.

DELEN (tint = baseColorFactor op een lichtgrijze textuur, zoals de man):
| deel      | inhoud                                                 | materiaal        | tint     |
| --------- | ------------------------------------------------------ | ---------------- | -------- |
| lijf      | hoofd, oren, hals, handen; oogjes + tanden = vast      | mat_lijf + vast  | #e8a383  |
| haar      | grijs haar strak naar achteren + knot                  | mat_haar         | #bcbac3  |
| kraag     | gele schulpkraag                                       | mat_kraag        | #da9a21  |
| jasje     | grijsgroen open jasje; manchetten grijs = vast         | mat_jasje + vast | #83916a  |
| jurk      | lange paarse jurk                                      | mat_jurk         | #83379f  |
| riem      | leren riem + gesp                                      | mat_vast         | wit      |
| laarzen   | omgeslagen leren laarzen                               | mat_laarzen      | #54311e  |
| prop_staf | wandelstok met klimop (op prop_L)                      | mat_vast         | wit      |
"""
import os
import sys

import bpy

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import bumpkin_basis as BB  # noqa: E402
import bumpkin_delen as BD  # noqa: E402
from bumpkin_basis import srgb  # noqa: E402

MAAT_OUD = {"hoogte": 1.31, "kop": 0.27, "schouder": 0.28, "been": 0.47}
HOUDING = {"Spine": (6, 0, 0), "Spine1": (6, 0, 0), "Spine2": (5, 0, 0), "Neck": (-6, 0, 0), "Head": (-9, 0, 0)}
STAFARM = {"LeftArm": (16, 0, 10), "LeftForeArm": (22, 0, 0)}


def na_animatie(rig):
    BB.houding_additief(rig, HOUDING)
    BB.houding_additief(rig, STAFARM, acties=("idle", "lopen", "rennen"))
    BD.plaats_staf(rig, bpy.data.objects["prop_staf"], binnen=0.0)


DELEN = ["lijf", "haar", "kraag", "jasje", "jurk", "riem", "laarzen", "prop_staf"]
SOORT = {"lijf": "lijf", "haar": "haar", "kraag": "kraag", "jasje": "kledij", "jurk": "kledij", "riem": "riem",
         "laarzen": "laarzen", "prop_staf": "staf"}
TINTBAAR = {"lijf": "huid", "haar": "haar", "kraag": "kraag", "jasje": "groen", "jurk": "paars", "laarzen": "laars"}
VAST = {"lijf": (3,), "jasje": (4,), "riem": (0, 1), "prop_staf": (0, 1, 2)}
TEXEL = {"lijf": 1.9, "haar": 1.2, "kraag": 1.2, "jasje": 1.0, "jurk": 1.0, "riem": 1.0, "laarzen": 1.1,
         "prop_staf": 0.9}
TEXEL_REGIO = {("lijf", 2): 1.4 / 1.9, ("lijf", 4): 1.4 / 1.9, ("lijf", 5): 0.6 / 1.9, ("lijf", 6): 1.2 / 1.9}

KLEUR = {
    "haar": srgb("#b0aeb6"), "huid": srgb("#d9987a"), "kraag": srgb("#cc901e"), "groen": srgb("#7a8763"),
    "paars": srgb("#7a3394"), "laars": srgb("#4e2d1b"), "zool": srgb("#2a1a0e"), "riem": srgb("#4a3020"),
    "gesp": srgb("#8a8a86"), "snor": srgb("#a8a6b0"), "manchet": srgb("#8a8a84"),
    "hout": srgb("#5a4430"), "rank": srgb("#3e4420"), "blad": srgb("#4e7a2c"),
}

KOP = dict(
    schedel=(0.092, 0.11, 0.124, 0.122), kaak=(-0.02, 0.4, 0.2), ogen_ph=0.42, ogen_z=1.12, mond_z=1.03,
    neus=(0, -0.106, -0.03),
    neusprof=((0.034, 0.009, 0.009, 0.014), (0.014, 0.013, 0.016, -0.004), (-0.006, 0.018, 0.022, -0.014),
              (-0.022, 0.019, 0.02, -0.02), (-0.034, 0.013, 0.012, -0.012)),
    oog=(0.0122, 0.0034, 0.0062),
    haar_c=(0, 0.012, 1.168), haar_r=(0.106, 0.118, 0.124, 0.142, 0.13),
    haargrens=[(0.0, 1.205), (0.5, 1.195), (0.9, 1.165), (1.25, 1.14), (1.6, 1.13), (2.3, 1.07), (3.1416, 1.05)],
    klont=(0.0, 0.0),
    gezicht=dict(stoppels=False, mond="lach", lach=0.01, mondbreed=0.024, spleet=0.003, open=0.006, onderlip=0.0032,
                 bovenlip=0.0018, lip="#a86060", iris="#5a6a8a", wang=0.4, neusrood=0.3, rimpel=2.0,
                 voorhoofd=(0.034, 0.043, 0.052, 0.061), kraai=(-0.4, -0.15, 0.1, 0.35, 0.6), wal=1.4,
                 lid=0.003, schijf_lid=0.0028, oog_open=(0.0112, 0.0056), brauw=(0.0215, 0.006, 0.0032),
                 tand="#ddd0b0", wimper=0.0013, tris=1300,
                 # bust17/concept: lange haakneus, holle wangen, ingevallen mond, puntige kin, veel rimpels
                 vorm=dict(neus_h=0.028, neus_r=0.0092, neus_bult=0.0042, neus_hang=0.005, neus_breed=0.0112,
                           neus_vleugel=0.0085, neus_brug=0.0038, richel=0.0042, oogkas=0.0075, wal=0.002,
                           lidkap=0.0018, wang_hol=0.007, jukbeen=0.0062, mond_in=0.0038, kin=0.0082, kin_z=0.034,
                           kin_breed=0.013, nlf=(0.0034, 0.003), rimpels=0.0008, slaap=0.004, asym=0.0011,
                           mond_scheef=-0.0018, seed=17)),
)

# jasje: open voor (halve opening 0,045-0,06), tot op de heup; jurk: hoge ronde hals, tot de enkels
JASJE = [(0.975, 0.09, 0.08, 0.078, 0.05), (0.955, 0.14, 0.1, 0.098, 0.05), (0.925, 0.172, 0.12, 0.114, 0.052),
         (0.88, 0.174, 0.13, 0.12, 0.055), (0.8, 0.168, 0.132, 0.122, 0.058), (0.72, 0.17, 0.134, 0.126, 0.062),
         (0.645, 0.182, 0.14, 0.134, 0.068), (0.57, 0.192, 0.146, 0.14, 0.075)]
JURK = [(0.962, 0.1, 0.082, 0.08, 0.0), (0.925, 0.16, 0.112, 0.106, 0.0),
        (0.88, 0.162, 0.122, 0.112, 0.0), (0.8, 0.156, 0.124, 0.114, 0.0), (0.72, 0.158, 0.126, 0.118, 0.0),
        (0.645, 0.17, 0.132, 0.128, 0.0), (0.55, 0.182, 0.14, 0.136, 0.0), (0.42, 0.19, 0.146, 0.142, 0.0),
        (0.3, 0.202, 0.155, 0.152, 0.0), (0.2, 0.212, 0.163, 0.16, 0.0), (0.135, 0.218, 0.168, 0.165, 0.0)]


def rimpels_wang(cx, c, h, huid, reg_h):
    """Neus-mondplooien, wangrimpels en levervlekjes."""
    import numpy as np
    kop = cx.sk.kop
    kk = kop.k
    P = cx.P
    # de plooien zelf zitten nu in de gezichtsvorm (vorm: nlf, rimpels); hier alleen levervlekjes
    vl = (BD.ruis(P, 70, 132) > 0.58) & huid
    c[vl] = c[vl] * 0.88 + srgb("#8a5a3a") * 0.12


KOP["gezicht"]["extra"] = rimpels_wang


def extra_lijf(B, sk, kop):
    BD.bouw_oren(B, sk, kop, grootte=1.1, uitstaan=0.25, z0=1.09, ph=1.6)
    BD.bouw_tanden(B, sk, kop, [(-0.009, 0.008, 0.008), (0.008, 0.008, 0.009)], dz=0.003)


def extra_haar(B, sk, kop):
    """Naar achteren gekamd in een opgerolde knot."""
    import numpy as np
    c = BD.knot_spiraal(B, sk, plek=(0, 0.1, 0.125), r=0.05, buis=0.021, slagen=1.8)
    doel = c - kop.Ch
    for i, ph in enumerate(np.linspace(-2.6, 2.6, 13)):
        tb = kop.theta_bij_z(ph, kop.haargrens(ph) + 0.004 * kop.k, lambda t, p: kop.haarpunt(t, p, False))
        van = kop.haarpunt(tb, ph, False) - kop.Ch
        BD.lok_tussen(B, sk, van, doel + np.array([0.02 * np.sin(ph), -0.01, 0]) * kop.k, 0.028, 0.0045, n=8,
                      licht=0.92 + 0.16 * ((i * 3) % 5) / 4, seed=i, tip=0.6, kaart=1.25, verleng=0.0)
    # losse pluisjes bij de slapen en in de nek
    rng = np.random.default_rng(3)
    for ph in (0.95, -0.95, 1.25, -1.25, 2.9, -2.9, 3.14):
        tb = kop.theta_bij_z(ph, kop.haargrens(ph) + 0.01 * kop.k, lambda t, p: kop.haarpunt(t, p, False))
        q = kop.haarpunt(tb, ph, False, 0.002 * kop.k)
        u = BD.straal(kop, q)
        d = np.array([0, 0, -1.0]) + u * 0.5 + rng.normal(size=3) * 0.2
        pad = [q + d * 0.03 * kop.k * t + u * 0.004 * kop.k * t for t in np.linspace(0, 1, 4)]
        BD.haarkaart(B, sk, pad, 0.008 * kop.k, nrm=[u] * 4, tip=0.3)


def bouw(sk, coll):
    sk.stof = {"jasje": dict(weef=0.0045, vlek=0.16, kraag=0.88, manchet="manchet"),
               "jurk": dict(weef=0.004, vlek=0.14, vuil=0.55, vuil_hoogte=0.2)}
    sk.rok_kuit = 0.68                                  # lange rok volgt het scheenbeen: laars blijft eronder
    d = {}
    d["jasje"] = BD.bouw_kledij(sk, coll, "jasje", JASJE, mouw_dik=1.02, mouw_wijd=1.12, manchet=6)
    d["jurk"] = BD.bouw_kledij(sk, coll, "jurk", JURK, mouwen=False, kraag=(0.012,))
    d["riem"] = BD.bouw_riem_op(sk, coll, "riem", z0=0.7, a=0.178, b=0.14, gesp="vierkant", gesp_b=0.03,
                                gesp_h=0.024, breed=0.017)
    d["laarzen"] = BD.bouw_laarzen(sk, coll)
    d["lijf"] = BD.bouw_lijf(sk, coll, kopvorm=KOP, extra=extra_lijf)
    d["haar"] = BD.bouw_haar_glad(sk, coll, extra=extra_haar)
    import numpy as np
    knot = sk.kop.C + np.array([0, 0.1, 0.125]) * sk.kop.k - sk.kop.Ch
    BD.schil_strengen(sk, 200 if BB.SNEL else 460, BD.naar_grens(sk.kop, 0.002), BD.rond(knot, 0.08), seed=4,
                      dikte=(0.0011, 0.0016))
    BD.haar_hoog(sk, KLEUR["haar"], donker=0.75, punt=1.12, warm=0.03)
    d["kraag"] = BD.bouw_kraag(sk, coll, "kraag", z0=sk.z(0.992), r_in=0.064, r_uit=0.13, zak=0.045, plooien=14,
                               plooi=0.0, schulp=0.018, hoog_=0.008)
    d["prop_staf"] = BD.bouw_staf(sk, coll, lengte=0.66, ranken=1, bladeren=16, krul=False, seed=7, dik=1.05)
    return d


OUDERE_VROUW = BB.Personage(
    "oudere_vrouw", MAAT_OUD, DELEN, SOORT, TINTBAAR, VAST, TEXEL, KLEUR, bouw, texel_regio=TEXEL_REGIO,
    bak_ext={"haar": (0.01, 0.03), "laarzen": (0.005, 0.02), "jasje": (0.006, 0.02), "jurk": (0.006, 0.02),
             "riem": (0.004, 0.015), "lijf": (0.008, 0.025), "kraag": (0.004, 0.012), "prop_staf": (0.004, 0.012)},
    kleurbak=("haar",), sprites=("elderf", "elderf"),
    na_animatie=na_animatie,
    extra={"bust": "bust17", "weefsel": ("jasje", "jurk"), "haardelen": ("haar",),
           "prop_delen": {"prop_staf": "prop_L"}, "zichtbare_props": ("prop_staf",),
           "vergelijk_actie": ("idle", 0)},
)

if __name__ == "__main__":
    BB.bouw_personage(OUDERE_VROUW)
