"""Meisje (kind, vrouw), game-ready (Blender 5.2 headless -> glb voor Godot 4).

Draaien:
  blender -b -P bumpkin_meisje.py -- [res=2048] [snel] [vlak] [vergelijk] [poses] [geen_export] [tag=<x>]
Zelfde rig, animaties en straat als de man (bumpkin_basis.py + bumpkin_delen.py); dit script is alleen
de configuratie. Doel: portret bust07 en concept/img/meisje.jpg (blond met pony en middenscheiding, twee
staartjes met paarse strikken, witgrijze plooikraag, paarse jurk-tuniek tot halverwege de dij met lange
mouwen, paarse maillot, omgeslagen laarzen); sprite kidf. Lengte 0,81 x de man (spec.md).

Uitvoer bumpkin_meisje.glb: armatuur `bumpkin_rig` (zelfde botten, MAAT_MEISJE: 1,11 m, kop 0,33) met
alle zes acties, props op prop_R, atlas textures_meisje/. Previews: preview/meisje_render.png,
meisje_poses.png; meisje_vergelijk_*.png nooit committen.

DELEN (tint = baseColorFactor op een lichtgrijze textuur, zoals de man):
| deel     | inhoud                                        | materiaal        | tint     |
| -------- | --------------------------------------------- | ---------------- | -------- |
| lijf     | hoofd, hals, handen; oogjes = vast            | mat_lijf + vast  | #eba17a  |
| haar     | blond glad kapsel met pony + twee staartjes   | mat_haar         | #f2ba4e  |
| strikken | twee paarse satijnen strikken                 | mat_strikken     | #ab45b4  |
| kraag    | witgrijze plooikraag                          | mat_kraag        | #a7a7a9  |
| jurk     | paarse jurk-tuniek, lange mouwen              | mat_jurk         | #853893  |
| maillot  | paarse gebreide maillot                       | mat_maillot      | #81528b  |
| laarzen  | omgeslagen leren laarzen                      | mat_laarzen      | #54311e  |
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import bumpkin_basis as BB  # noqa: E402
import bumpkin_delen as BD  # noqa: E402
from bumpkin_basis import srgb  # noqa: E402

MAAT_MEISJE = {"hoogte": 1.11, "kop": 0.33, "schouder": 0.25, "been": 0.47}
DELEN = ["lijf", "haar", "strikken", "kraag", "jurk", "maillot", "laarzen"]
SOORT = {"lijf": "lijf", "haar": "haar", "strikken": "strik", "kraag": "kraag", "jurk": "kledij",
         "maillot": "broek", "laarzen": "laarzen"}
TINTBAAR = {"lijf": "huid", "haar": "haar", "strikken": "strik", "kraag": "kraag", "jurk": "paars",
            "maillot": "maillot", "laarzen": "laars"}
VAST = {"lijf": (3,)}
TEXEL = {"lijf": 1.9, "haar": 1.2, "strikken": 1.2, "kraag": 1.2, "jurk": 1.0, "maillot": 1.0, "laarzen": 1.1}
TEXEL_REGIO = {("lijf", 2): 1.4 / 1.9, ("lijf", 4): 1.4 / 1.9, ("lijf", 5): 0.6 / 1.9}

KLEUR = {
    "haar": srgb("#e2ae48"), "huid": srgb("#dc9672"), "strik": srgb("#a040a8"), "kraag": srgb("#9c9c9e"),
    "paars": srgb("#7c3489"), "maillot": srgb("#784c82"), "laars": srgb("#4e2d1b"), "zool": srgb("#2a1a0e"),
    "snor": srgb("#b0782a"),
}

KOP = dict(
    schedel=(0.097, 0.11, 0.132, 0.118), kaak=(0.0, 0.34, 0.1), ogen_ph=0.41, ogen_z=1.115, mond_z=1.04,
    neus=(0, -0.104, -0.026),
    neusprof=((0.026, 0.008, 0.008, 0.012), (0.01, 0.01, 0.011, 0.006), (-0.006, 0.015, 0.014, 0.002),
              (-0.015, 0.016, 0.013, 0.0), (-0.021, 0.011, 0.008, 0.005)),
    oog=(0.0126, 0.0048, 0.0062),
    haar_c=(0, 0.014, 1.175), haar_r=(0.113, 0.121, 0.13, 0.136, 0.14),
    haargrens=[(0.0, 1.168), (0.45, 1.165), (0.85, 1.14), (1.2, 1.09), (1.6, 1.06), (2.3, 1.05), (3.1416, 1.04)],
    klont=(0.0, 0.0),
    gezicht=dict(stoppels=False, mond="lach", lach=0.008, mondbreed=0.022, onderlip=0.0042, bovenlip=0.0026,
                 lip="#c86a6a", iris="#5868a8", wang=0.42, neusrood=0.12, rimpel=0.0, kraai=(), wal=0.25,
                 lid=0.006, schijf_lid=0.006, oog_open=(0.0124, 0.0072), brauw=(0.0255, 0.003, 0.0022),
                 wimper=0.0016, lidkleur="#7a4a3a", open=0.0018, tris=1300,
                 # bust07: lang smal gezicht, lange rechte neus, spitse kin, glimlach met tanden, grote ogen
                 vorm=dict(neus_h=0.017, neus_r=0.0078, neus_breed=0.0098, neus_vleugel=0.0068, neus_brug=0.0024,
                           neus_brug_b=0.0055, richel=0.0012, jukbeen=0.004, wang_hol=0.0, wang_vol=0.0038,
                           kin=0.0075, kin_z=0.04, kin_breed=0.013, nlf=0.0004, lip_b=0.0026, lip_o=0.0034,
                           snuit=0.003, wal=0.0003, kaakhoek=0.0012, lidplooi=0.0007, oogkas=0.0045, slaap=0.0006,
                           mond_scheef=-0.0012, asym=0.0006, seed=7)),
)

JURK = [(0.992, 0.072, 0.068, 0.066, 0.0), (0.975, 0.086, 0.075, 0.073, 0.0), (0.952, 0.135, 0.095, 0.094, 0.0),
        (0.925, 0.163, 0.112, 0.11, 0.0), (0.88, 0.163, 0.118, 0.115, 0.0), (0.8, 0.16, 0.12, 0.117, 0.0),
        (0.72, 0.162, 0.124, 0.121, 0.0), (0.645, 0.172, 0.131, 0.13, 0.0), (0.57, 0.182, 0.138, 0.137, 0.0),
        (0.5, 0.192, 0.145, 0.144, 0.0)]


def extra_haar(B, sk, kop):
    """Middenscheiding: lokken van de scheiding naar de staartjes, staartjes als drie plukken."""
    import numpy as np
    BD.staart_plukken(B, sk, kop, lengte=1.0)
    i = 0
    for sx in (1, -1):
        aan = sk.staart_aanzet[sx][0] - kop.Ch
        for y in np.linspace(-0.55, 0.75, 7):
            van = np.array([sx * 0.04, y, 1.0])
            naar = aan + np.array([0, y * 0.03, 0.02]) * kop.k
            BD.lok_tussen(B, sk, van, naar, 0.024, 0.0062, n=8, licht=0.92 + 0.16 * ((i * 7) % 5) / 4, seed=i)
            i += 1



def bouw(sk, coll):
    sk.stof = {"jurk": dict(weef=0.004, vlek=0.1, kraag=0.9), "maillot": dict(brei=True, vuil=0.6, knie=0.08)}
    sk.haarstijl = {"kruin": (0, 0.06, 0.12), "strengen": 60, "scheiding": True, "warm": (0.06, 0.02, -0.08)}
    d = {}
    d["jurk"] = BD.bouw_kledij(sk, coll, "jurk", JURK, mouw_dik=0.95, kraag=(0.014,))
    d["maillot"] = BD.bouw_broek(sk, coll, "maillot", dik=0.72)
    d["laarzen"] = BD.bouw_laarzen(sk, coll)
    d["lijf"] = BD.bouw_lijf(sk, coll, kopvorm=KOP)
    d["haar"] = BD.bouw_haar_glad(sk, coll, extra=extra_haar)
    import numpy as np
    BD.schil_strengen(sk, 200 if BB.SNEL else 480,
                      lambda rng: np.array([rng.choice((-1, 1)) * 0.03, rng.uniform(-0.6, 0.8), 1.0]),
                      BD.naar_grens(sk.kop, 0.004), seed=6, dikte=(0.0012, 0.0018))
    BD.haar_hoog(sk, KLEUR["haar"], donker=0.72, punt=1.25)
    d["strikken"] = BD.bouw_strikken(sk, coll, maat=1.6)
    d["kraag"] = BD.bouw_kraag(sk, coll, "kraag", z0=sk.z(1.0), r_in=0.07, r_uit=0.118, zak=0.028,
                               plooien=20, plooi=0.009, hoog_=0.01, n=64)
    return d


MEISJE = BB.Personage(
    "meisje", MAAT_MEISJE, DELEN, SOORT, TINTBAAR, VAST, TEXEL, KLEUR, bouw, texel_regio=TEXEL_REGIO,
    bak_ext={"haar": (0.01, 0.03), "laarzen": (0.005, 0.02), "jurk": (0.006, 0.02), "maillot": (0.004, 0.015),
             "lijf": (0.008, 0.025), "kraag": (0.004, 0.012), "strikken": (0.0015, 0.005)},
    kleurbak=("haar",), sprites=("kidf", "kidf"),
    extra={"bust": "bust07", "weefsel": ("jurk", "maillot"), "haardelen": ("haar",)},
)

if __name__ == "__main__":
    BB.bouw_personage(MEISJE)
