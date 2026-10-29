"""Volwassen vrouwelijke bumpkin, game-ready (Blender 5.2 headless -> glb voor Godot 4).

Draaien:
  blender -b -P bumpkin_vrouw.py -- [res=2048] [snel] [vlak] [vergelijk] [poses] [geen_export] [tag=<x>]
Zelfde rig, animaties en straat als de man (bumpkin_basis.py + bumpkin_delen.py); dit script is alleen
de configuratie. Doel: portret bust13 (blonde krullen, paarse off-shoulder jurk, blote schouders) en
concept/img/vrouw.jpg (krullen tot de schouders, grijsgroene mouwen, paarse rok tot net onder de knie,
blote kuiten, omgeslagen laarzen); sprite f_still/f_walk (grijsgroen boven, paars onder).
Keuze: de jurk is paars en off-shoulder (bust13), de lange mouwen zijn een los grijsgroen deel `mouwen`
(de blouse eronder, zoals concept en sprite); los te tinten of te vervangen.

Uitvoer bumpkin_vrouw.glb: armatuur `bumpkin_rig` (zelfde botten, MAAT_VROUW) met alle zes acties,
props prop_hamer/zwaard/steen op prop_R, atlas textures_vrouw/ (vrouw_kleur.jpg, vrouw_normaal.png,
vrouw_orm.png; R=AO G=ruw B=metaal). Previews: preview/vrouw_render.png, vrouw_poses.png (eigen werk) en
vrouw_vergelijk_*.png (met sprite/portret: nooit committen).

DELEN (mesh = glTF-node; tint = baseColorFactor op een lichtgrijze textuur, zoals de man):
| deel    | inhoud                                                   | materiaal          | tint     |
| ------- | -------------------------------------------------------- | ------------------ | -------- |
| lijf    | hoofd, hals, blote schouders/decollete, handen, kuiten   | mat_lijf + vast    | #eba178  |
|         | oogjes = vast (mat_vast)                                 |                    |          |
| haar    | blonde krullenbol tot op de schouders                    | mat_haar           | #fabc30  |
| jurk    | paarse off-shoulder jurk, lijfje + rok tot onder de knie | mat_jurk           | #833893  |
| mouwen  | grijsgroene blouse-mouwen (lang, manchet)                | mat_mouwen         | #98a689  |
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
    oog=(0.0128, 0.0042, 0.0066),
    # krullenbol: groter, lager middelpunt, valt aan de zijkant en achter tot op de schouders
    haar_c=(0, 0.024, 1.165), haar_r=(0.168, 0.118, 0.165, 0.132, 0.34),
    haargrens=[(0.0, 1.19), (0.45, 1.18), (0.8, 1.14), (1.05, 1.06), (1.3, 0.95), (1.8, 0.89), (np.pi, 0.88)],
    klont=(0.15, 0.06),
    gezicht=dict(stoppels=False, mond="lach", lach=0.007, lip="#b84a52", iris="#4a6a9e", wang=0.38,
                 neusrood=0.12, rimpel=0.45, kraai=(-0.2, 0.2), wal=0.5, lid=0.0042, schijf_lid=0.0035,
                 oog_open=(0.0118, 0.0064), brauw=(0.0225, 0.004, 0.0026), wimper=0.0018,
                 lidkleur="#6a3a2a"),
)

# jurk: (z0, a, voor, achter, halve opening); z0 als bij de man (heup 0,644, nek 0,965), onder de heup
# naar de beenlengte
JURK = [(0.9, 0.2, 0.112, 0.108, 0.0), (0.885, 0.172, 0.12, 0.104, 0.0), (0.855, 0.158, 0.128, 0.104, 0.0),
        (0.815, 0.146, 0.116, 0.1, 0.0), (0.775, 0.136, 0.102, 0.098, 0.0), (0.735, 0.136, 0.099, 0.101, 0.0),
        (0.69, 0.149, 0.106, 0.113, 0.0), (0.645, 0.163, 0.116, 0.126, 0.0), (0.6, 0.172, 0.123, 0.132, 0.0),
        (0.52, 0.182, 0.131, 0.139, 0.0), (0.43, 0.19, 0.139, 0.146, 0.0), (0.34, 0.197, 0.146, 0.152, 0.0)]


def extra_lijf(B, sk, kop):
    BD.bouw_decollete(B, sk)
    BD.bouw_kuiten(B, sk, van=0.36, tot=0.17)


def bouw(sk, coll):
    sk.haarlicht = (0.35, 1.25)
    sk.stof = {"jurk": dict(weef=0.004, vlek=0.14, kraag=0.85, vuil=0.25, vuil_hoogte=0.12),
               "mouwen": dict(weef=0.0045)}
    d = {}
    d["jurk"] = BD.bouw_kledij(sk, coll, "jurk", JURK, hals="schouder", mouwen=False, golf=0.025, zoom=0.007)
    d["mouwen"] = BD.bouw_mouwen(sk, coll, "mouwen", dik=0.95, wijd=1.08, start=1.0, pof=0.08)
    d["laarzen"] = BD.bouw_laarzen(sk, coll)
    d["lijf"] = BD.bouw_lijf(sk, coll, kopvorm=KOP, nek=None, extra=extra_lijf)
    d["haar"] = BD.bouw_haar(sk, coll, lang=True)
    return d


VROUW = BB.Personage(
    "vrouw", MAAT_VROUW, DELEN, SOORT, TINTBAAR, VAST, TEXEL, KLEUR, bouw, texel_regio=TEXEL_REGIO,
    bak_ext={"haar": (0.03, 0.06), "laarzen": (0.005, 0.02), "jurk": (0.006, 0.02), "mouwen": (0.005, 0.018),
             "lijf": (0.008, 0.025)},
    kleurbak=("haar",),
    krullen=lambda sk, coll: {"haar": [BB.krullen(sk, coll, 1800 if BB.SNEL else 6000, lengte=(0.02, 0.036),
                                                  rc=(0.005, 0.0085), licht=(1.0, 1.6), warm=(-0.02, 0.14))]},
    sprites=("f_still", "f_walk"),
    extra={"bust": "bust13", "weefsel": ("jurk", "mouwen")},
)

if __name__ == "__main__":
    BB.bouw_personage(VROUW)
