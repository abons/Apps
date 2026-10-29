"""Volwassen vrouwelijke bumpkin, game-ready (Blender 5.2 headless -> glb voor Godot 4).

Draaien:
  blender -b -P bumpkin_vrouw.py -- [res=2048] [snel] [vlak] [vergelijk] [poses] [geen_export] [tag=<x>]
Zelfde rig, animaties en straat als de man (bumpkin_basis.py + bumpkin_delen.py); dit script is alleen
de configuratie. Doel: portret bust13 (blonde krullen, paarse off-shoulder jurk, blote schouders) en
concept/img/vrouw.jpg (krullen tot de schouders, grijsgroene mouwen, paarse rok tot net onder de knie,
blote kuiten, omgeslagen laarzen); sprite f_still/f_walk (grijsgroen boven, paars onder).
Keuze (realisme-ronde 2026-10-29): kleding naar het concept: `mouwen` is nu de hele grijsgroene blouse
(V-hals, lange mouwen, los over de rok tot op de heup), `jurk` de paarse rok tot net boven de knie; de
deelnamen en tinten zijn gebleven. Het gezicht volgt bust13.

Uitvoer bumpkin_vrouw.glb: armatuur `bumpkin_rig` (zelfde botten, MAAT_VROUW) met alle zes acties,
props prop_hamer/zwaard/steen op prop_R, atlas textures_vrouw/ (vrouw_kleur.jpg, vrouw_normaal.png,
vrouw_orm.png; R=AO G=ruw B=metaal). Previews: preview/vrouw_render.png, vrouw_poses.png (eigen werk) en
vrouw_vergelijk_*.png (met sprite/portret: nooit committen).

DELEN (mesh = glTF-node; tint = baseColorFactor op een lichtgrijze textuur, zoals de man):
| deel    | inhoud                                                   | materiaal          | tint     |
| ------- | -------------------------------------------------------- | ------------------ | -------- |
| lijf    | hoofd, hals, handen, knieen en kuiten                    | mat_lijf + vast    | #eba178  |
|         | oogjes = vast (mat_vast)                                 |                    |          |
| haar    | blonde krullenbol tot op de schouders                    | mat_haar           | #fabc30  |
| jurk    | paarse rok tot net boven de knie                         | mat_jurk           | #833893  |
| mouwen  | grijsgroene blouse: V-hals, lange mouwen, tot de heup    | mat_mouwen         | #98a689  |
| laarzen | omgeslagen leren laarzen (die van de man)                | mat_laarzen        | #654428  |
"""
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import bumpkin_basis as BB  # noqa: E402
import bumpkin_delen as BD  # noqa: E402
from bumpkin_basis import srgb  # noqa: E402

MAAT_VROUW = {"hoogte": 1.34, "kop": 0.27, "schouder": 0.29, "been": 0.47}
DELEN = ["lijf", "haar", "jurk", "mouwen", "laarzen"]
SOORT = {"lijf": "lijf", "haar": "haar", "jurk": "kledij", "mouwen": "kledij", "laarzen": "laarzen"}
TINTBAAR = {"lijf": "huid", "haar": "haar", "jurk": "paars", "mouwen": "groen", "laarzen": "laars"}
VAST = {"lijf": (3,)}
TEXEL = {"lijf": 1.9, "haar": 1.2, "jurk": 1.0, "mouwen": 1.0, "laarzen": 1.1}
TEXEL_REGIO = {("lijf", 2): 1.4 / 1.9, ("lijf", 4): 1.4 / 1.9, ("lijf", 5): 1.0 / 1.9, ("lijf", 7): 0.8 / 1.9}

KLEUR = {
    "haar": srgb("#eab02c"), "huid": srgb("#dc9670"), "paars": srgb("#7a3489"), "groen": srgb("#8e9b80"),
    "laars": srgb("#5e3f25"), "zool": srgb("#2a1a0e"), "snor": srgb("#a0681c"),   # snor = wenkbrauwen
}

KOP = dict(
    schedel=(0.094, 0.109, 0.126, 0.118), kaak=(0.02, 0.32, 0.12), ogen_ph=0.40, ogen_z=1.12, mond_z=1.04,
    neus=(0, -0.099, -0.03),
    neusprof=((0.03, 0.008, 0.008, 0.014), (0.012, 0.01, 0.011, 0.006), (-0.006, 0.015, 0.015, 0.002),
              (-0.017, 0.016, 0.014, 0.0), (-0.025, 0.011, 0.009, 0.006)),
    oog=(0.0124, 0.0026, 0.0056),                 # zware leden (bust13)
    # krullenbol: groter, lager middelpunt, valt aan de zijkant en achter tot op de schouders
    haar_c=(0, 0.026, 1.16), haar_r=(0.176, 0.12, 0.17, 0.122, 0.33),          # geen hoge koepel
    haargrens=[(0.0, 1.19), (0.45, 1.18), (0.8, 1.14), (1.05, 1.06), (1.3, 0.95), (1.8, 0.89), (np.pi, 0.88)],
    klont=(0.15, 0.06),
    gezicht=dict(stoppels=False, mond="lach", lach=0.007, lip="#b84a52", iris="#4a6a9e", wang=0.38,
                 neusrood=0.12, rimpel=0.6, kraai=(-0.2, 0.2), wal=0.5, lid=0.0042, schijf_lid=0.0035,
                 oog_open=(0.0118, 0.0064), brauw=(0.0225, 0.004, 0.0026), wimper=0.0018,
                 lidkleur="#6a3a2a", open=0.0, tris=1500, mondbreed=0.022,
                 # bust13: hoge jukbeenderen, rechte middelgrote neus, volle lippen, open lach, zware leden
                 vorm=dict(neus_h=0.021, neus_r=0.0092, neus_breed=0.0118, neus_vleugel=0.0085, neus_brug=0.003,
                           richel=0.0028, jukbeen=0.0066, wang_hol=0.0018, wang_vol=0.0012, kin=0.0072, kin_breed=0.016,
                           wal=0.0013, lidplooi=0.0011, rimpels=0.00035, kaak_voor=0.013,
                           lip_b=0.0032, lip_o=0.004, snuit=0.0038, lid_hang=(0.0012, 0.0006), lidkap=0.0009,
                           mond_scheef=0.0018, brauw_buiten=(0.0012, -0.0004), nlf=0.0019, asym=0.0009, seed=13)),
)

# jurk: (z0, a, voor, achter, halve opening); z0 als bij de man (heup 0,644, nek 0,965), onder de heup
# naar de beenlengte
# rok (deel 'jurk'): taille tot net boven de knie
JURK = [(0.705, 0.148, 0.108, 0.112, 0.0), (0.645, 0.166, 0.12, 0.13, 0.0), (0.6, 0.175, 0.127, 0.136, 0.0),
        (0.52, 0.181, 0.132, 0.14, 0.0), (0.44, 0.186, 0.136, 0.144, 0.0), (0.405, 0.188, 0.137, 0.145, 0.0)]
# blouse (deel 'mouwen'): V-hals, buste, los tot op de heup
BLOUSE = [(0.992, 0.07, 0.066, 0.064, 0.018), (0.975, 0.09, 0.077, 0.074, 0.018), (0.952, 0.137, 0.098, 0.095, 0.012),
          (0.925, 0.166, 0.12, 0.111, 0.005), (0.875, 0.164, 0.132, 0.115, 0.0), (0.815, 0.154, 0.128, 0.112, 0.0),
          (0.75, 0.152, 0.116, 0.112, 0.0), (0.69, 0.162, 0.12, 0.124, 0.0), (0.63, 0.178, 0.131, 0.139, 0.0),
          (0.585, 0.186, 0.137, 0.145, 0.0)]


def extra_lijf(B, sk, kop):
    BD.bouw_tanden(B, sk, kop, [(x, 0.0068, 0.0058) for x in (-0.0105, -0.0036, 0.0036, 0.0105)], dz=0.0012)
    BD.bouw_kuiten(B, sk, van=0.43, tot=0.17)


def bouw(sk, coll):
    sk.haarlicht = (0.35, 1.25)
    sk.stof = {"jurk": dict(weef=0.004, vlek=0.14, kraag=0.85, vuil=0.25, vuil_hoogte=0.12),
               "mouwen": dict(weef=0.0045, vlek=0.12, kraag=0.9)}
    d = {}
    d["jurk"] = BD.bouw_kledij(sk, coll, "jurk", JURK, mouwen=False, zoom=0.01, K=30)
    d["mouwen"] = BD.bouw_kledij(sk, coll, "mouwen", BLOUSE, mouw_dik=0.95, mouw_wijd=1.04, K=30)
    d["laarzen"] = BD.bouw_laarzen(sk, coll)
    d["lijf"] = BD.bouw_lijf(sk, coll, kopvorm=KOP, extra=extra_lijf)
    d["haar"] = BD.bouw_haar(sk, coll, lang=True, extra=krullen_laag)
    BD.krullen_op_schil(sk, 380 if BB.SNEL else 950, seed=7, lengte=(0.02, 0.04), rc=(0.0075, 0.0125),
                        rt=(0.0028, 0.0038), slagen=(1.6, 2.6), licht=(0.95, 1.3), zak=1.0, groep=5, spreid=0.12,
                        diep=0.004)
    BD.haar_hoog(sk, KLEUR["haar"], donker=0.7, punt=1.25)
    return d


def krullen_laag(B, sk, kop):
    """Grote blonde kurkentrekkers rond het gezicht, opzij en achter tot op de schouders."""
    plekken = [(s * ph, z) for s in (1, -1) for ph, z in ((0.8, 1.11), (1.2, 1.07), (1.75, 1.03), (2.35, 1.0))] + \
        [(3.14, 0.99), (2.85, 1.0), (-2.85, 1.0)]
    BD.kurkentrekkers(B, sk, plekken, lengte=(0.09, 0.15), r=0.014, buis=0.0145, spoed=0.042, n=5, seed=4)
    BD.krul_kaarten(B, sk, 56, seed=13, lengte=(0.028, 0.05), breed=(0.011, 0.016))


VROUW = BB.Personage(
    "vrouw", MAAT_VROUW, DELEN, SOORT, TINTBAAR, VAST, TEXEL, KLEUR, bouw, texel_regio=TEXEL_REGIO,
    bak_ext={"haar": (0.03, 0.06), "laarzen": (0.005, 0.02), "jurk": (0.006, 0.02), "mouwen": (0.005, 0.018),
             "lijf": (0.008, 0.025)},
    kleurbak=("haar",),
    sprites=("f_still", "f_walk"),
    extra={"bust": "bust13", "weefsel": ("jurk", "mouwen")},
)

if __name__ == "__main__":
    BB.bouw_personage(VROUW)
