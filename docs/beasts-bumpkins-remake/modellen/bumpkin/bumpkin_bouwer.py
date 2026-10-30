"""Bouwer (gilde van de gereedschapsloods), game-ready (Blender 5.2 headless -> glb voor Godot 4).

Draaien:
  blender -b -P bumpkin_bouwer.py -- [res=2048] [snel] [vlak] [vergelijk] [poses] [geen_export] [tag=<x>]
Zelfde rig, maat, animaties en straat als de man (bumpkin_basis.py + bumpkin_delen.py); dit script is alleen
de configuratie plus de helm. Doel: concept/img/bouwer.jpg (helm v2, goedgekeurd): kaal, grote oren, brede
grijns met een gat tussen de tanden, gele leren helm uit panelen met een klep voor, blauwe tuniek met lange
mouwen en V-hals tot halverwege de dij, bruine riem met ijzeren gesp, paarse maillot, bruine laarzen.
In het spel krijgt een dorpeling met rol "bouwer" dit model (Bumpkin.glb_voor); hij hamert en zaagt.

DELEN (tint = baseColorFactor op een lichtgrijze textuur, zoals de man):
| deel    | inhoud                                            | materiaal       | tint    |
| ------- | ------------------------------------------------- | --------------- | ------- |
| lijf    | kaal hoofd, oren, hals, handen; oogjes/tand vast   | mat_lijf + vast | huid    |
| helm    | gele leren helm, 6 panelen, knoop, klep, rand      | mat_helm        | #d9a23a |
| tuniek  | blauwe tuniek, lange mouwen, ronde hals               | mat_tuniek      | #4a68a0 |
| broek   | paarse maillot                                    | mat_broek       | #6e2f78 |
| riem    | bruine riem + ijzeren gesp                        | mat_vast        | wit     |
| laarzen | omgeslagen leren laarzen                          | mat_laarzen     | bruin   |
Plus prop_hamer/zwaard/steen/zaag op prop_R.
"""
import math
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import bumpkin_basis as BB  # noqa: E402
import bumpkin_delen as BD  # noqa: E402
from bumpkin_basis import GEWICHT, Bouwer, gauss, gladstap, ruis, srgb  # noqa: E402

MAAT = {"schouder": 0.31, "kop": 0.25}             # als de man
DELEN = ["lijf", "helm", "tuniek", "broek", "riem", "laarzen"]
SOORT = {"lijf": "lijf", "helm": "helm", "tuniek": "kledij", "broek": "broek", "riem": "riem", "laarzen": "laarzen"}
TINTBAAR = {"lijf": "huid", "helm": "helm", "tuniek": "blauw", "broek": "paars", "laarzen": "laars"}
VAST = {"lijf": (3,), "riem": (0, 1)}
TEXEL = {"lijf": 1.9, "helm": 1.3, "tuniek": 1.0, "broek": 1.0, "riem": 1.0, "laarzen": 1.1}
TEXEL_REGIO = {("lijf", 2): 1.4 / 1.9, ("lijf", 4): 1.4 / 1.9, ("lijf", 5): 0.6 / 1.9, ("lijf", 6): 1.2 / 1.9}

KLEUR = {
    "huid": srgb("#dc9a78"), "helm": srgb("#d6a03a"), "blauw": srgb("#4a66a0"), "paars": srgb("#6c2e78"),
    "laars": srgb("#4e2f1c"), "zool": srgb("#2a1a0e"), "riem": srgb("#5a3d24"), "gesp": srgb("#9a9a94"),
    "snor": srgb("#6e4a32"), "haar": srgb("#6e4a32"), "metaal": srgb("#a4a4a0"),
}

# concept: kaal, rond gezicht met een brede grijns (twee tanden, gat ertussen), grote neus, rode wangen
KOP = dict(
    schedel=(0.1, 0.113, 0.13, 0.118), kaak=(0.02, 0.2, 0.1), ogen_ph=0.42, ogen_z=1.115, mond_z=1.035,
    neus=(0, -0.104, -0.032),
    neusprof=((0.03, 0.011, 0.01, 0.014), (0.012, 0.016, 0.017, 0.002), (-0.007, 0.024, 0.023, -0.004),
              (-0.022, 0.025, 0.021, -0.006), (-0.033, 0.017, 0.013, 0.002)),
    oog=(0.0124, 0.0028, 0.0064),
    haar_c=(0, 0.012, 1.15), haar_r=(0.112, 0.118, 0.124, 0.135, 0.128),
    haargrens=[(0.0, 1.3), (3.1416, 1.3)],
    klont=(0.0, 0.0),
    gezicht=dict(stoppels=False, mond="lach", lach=0.012, mondbreed=0.033, spleet=0.003, open=0.009, onderlip=0.0038,
                 bovenlip=0.002, lip="#b86a5e", iris="#5a6a7a", wang=0.6, neusrood=0.4, rimpel=0.5,
                 voorhoofd=(0.04, 0.05, 0.06), kraai=(-0.2, 0.1, 0.4), wal=0.8,
                 lid=0.004, schijf_lid=0.004, oog_open=(0.0118, 0.006), brauw=(0.022, 0.006, 0.005),
                 tand="#e0d4b0", tris=1300,
                 vorm=dict(neus_h=0.028, neus_r=0.0115, neus_hang=0.002, neus_breed=0.0142, neus_vleugel=0.011,
                           neus_bult=0.001, richel=0.004, oogkas=0.006, wal=0.0016, lidkap=0.0014,
                           jukbeen=0.004, wang_vol=0.004, kin=0.0075, kin_z=0.036, nlf=(0.0014, 0.001),
                           rimpels=0.0004, asym=0.001, mond_scheef=0.0015, seed=31)),
)

# tuniek tot halverwege de dij: (z0, a, voor, achter, halve opening); ronde hals
# (zonder opening: een open loft heeft over de hele voorkant omgeslagen randen, die bakten als zwarte strepen)
TUNIEK = [(0.985, 0.078, 0.072, 0.07, 0.0), (0.968, 0.1, 0.084, 0.08, 0.0), (0.948, 0.14, 0.1, 0.098, 0.0),
          (0.922, 0.168, 0.116, 0.112, 0.0), (0.88, 0.168, 0.124, 0.118, 0.0), (0.8, 0.164, 0.126, 0.12, 0.0),
          (0.72, 0.164, 0.128, 0.122, 0.0), (0.645, 0.176, 0.136, 0.132, 0.0), (0.57, 0.188, 0.144, 0.14, 0.0),
          (0.49, 0.198, 0.15, 0.146, 0.0), (0.43, 0.204, 0.154, 0.15, 0.0)]


def extra_lijf(B, sk, kop):
    BD.bouw_oren(B, sk, kop, grootte=1.15, uitstaan=0.3, z0=1.09, ph=1.6)
    BD.bouw_tanden(B, sk, kop, [(-0.0075, 0.0105, 0.012), (0.0075, 0.0105, 0.012)], dz=0.004)


# --- helm -----------------------------------------------------------------------------------------
HELM_RAND = [(0.0, 1.175), (0.6, 1.17), (1.2, 1.15), (1.6, 1.14), (2.2, 1.125), (3.1416, 1.115)]   # onderrand per hoek


def bouw_helm(sk, coll, naam="helm"):
    """Leren helm: koepel (regio 0) iets boven de schedel, omgerolde onderrand (regio 1), klep voor (regio 2)."""
    kop = sk.kop
    kk = kop.k
    B = Bouwer()
    nphi, nrow = 48, 12
    phs = 2 * np.pi * np.arange(nphi) / nphi - np.pi
    xs, ys = zip(*HELM_RAND)

    def rand_z(ph):
        return kop.zz(float(np.interp(abs(ph), xs, ys)))

    dik = 0.011 * kk
    rows = [[] for _ in range(nrow + 1)]
    onder, rand_uit, rand_in = [], [], []
    for ph in phs:
        tb = kop.theta_bij_z(ph, rand_z(ph), lambda t, p: kop.punt(t, p, 0.0, False))
        for i in range(nrow + 1):
            f = i / nrow
            tht = 0.04 + (tb - 0.04) * f
            bol = 0.006 * kk * math.sin(math.pi * min(1.0, f * 1.15))   # bolle koepel
            rows[i].append(kop.punt(tht, ph, dik + bol, False))
        d = kop.richting(tb, ph)
        p0 = rows[nrow][-1]
        rand_uit.append(p0 + d * 0.004 * kk - np.array([0, 0, 0.006 * kk]))
        rand_in.append(kop.punt(tb + 0.02, ph, 0.002 * kk, False) - np.array([0, 0, 0.008 * kk]))
    b0, _ = B.grid(np.array(rows), True, regio=0)
    B.kap(b0, nphi, kop.punt(0.0, 0.0, dik + 0.002 * kk, False), regio=0)
    B.grid(np.array([rows[nrow], rand_uit, rand_in]), True, regio=1)
    # klep: alleen voor (|ph| < 1.15), naar voren en iets omlaag, loopt naar de zijkanten weg
    kph = [p for p in np.linspace(-1.15, 1.15, 25)]
    boven, buiten, buiten_o, onder = [], [], [], []
    for ph in kph:
        tb = kop.theta_bij_z(ph, rand_z(ph), lambda t, p: kop.punt(t, p, 0.0, False))
        p0 = kop.punt(tb, ph, dik + 0.003 * kk, False) - np.array([0, 0, 0.004 * kk])
        hor = np.array([math.sin(ph), -math.cos(ph), 0.0])
        L = 0.075 * kk * math.cos(ph / 1.15 * math.pi / 2) ** 0.8
        p1 = p0 + hor * L - np.array([0, 0, 0.012 * kk]) * (L / (0.075 * kk))
        boven.append(p0)
        buiten.append(p1)
        buiten_o.append(p1 - np.array([0, 0, 0.004 * kk]))
        onder.append(p0 - np.array([0, 0, 0.005 * kk]))
    B.grid(np.array([boven, buiten, buiten_o, onder]), False, regio=2)
    sk.helm_c = kop.C.copy()
    return B.obj(naam, coll)


GEWICHT["helm"] = GEWICHT["kop"]


@BD.hoog("helm", 2, True)
def hg_helm(h, sk):
    P, hgt = h.P, h.hgt
    kk = sk.kop.k
    q = P - sk.helm_c
    ang = np.arctan2(q[:, 0], -q[:, 1])
    naad = gauss(np.abs(np.sin(ang * 3)) * np.hypot(q[:, 0], q[:, 1]), 0.0018 * kk)  # 6 panelen
    hgt += -0.0012 * kk * naad * (h.reg == 0) + 0.0004 * kk * ruis(P, 120, 71)


@BD.verf("helm")
def vf_helm(cx):
    """Geel leer: panelen met donkere naden en stiksels, knoop boven, versleten randen, vuil."""
    P, reg, sk = cx.P, cx.reg, cx.sk
    ruw, zet, H, KLEUR, m = cx.ruw, cx.zet, cx.H, cx.KLEUR, cx.Dm
    kk = sk.kop.k
    q = P - sk.helm_c
    ang = np.arctan2(q[:, 0], -q[:, 1])
    rxy = np.hypot(q[:, 0], q[:, 1])
    nerf = ruis(P, 420, 72, 2)
    vlek = ruis(P, 30, 73, 3)
    c = KLEUR[cx.tint][None] * (1 + 0.18 * vlek[:, None] + 0.07 * nerf[:, None] + 0.06 * cx.r_groot[:, None])
    naad = gauss(np.abs(np.sin(ang * 3)) * rxy, 0.0016 * kk) * (reg == 0)
    st = gauss(np.abs(np.sin(ang * 3)) * rxy - 0.004 * kk, 0.0008 * kk) * BB.steek(q[:, 2] + rxy, 0.006, 0.003) * (reg == 0)
    c *= (1 - 0.45 * naad - 0.25 * st)[:, None]
    knoop = gauss(rxy, 0.008 * kk) * (q[:, 2] > 0.09 * kk)
    c *= (1 - 0.2 * knoop)[:, None]
    sleet = gladstap(0.3, 0.8, vlek) * 0.25 + 0.25 * (reg == 1) + 0.15 * (reg == 2)
    c = c * (1 + 0.15 * sleet[:, None])
    vuil = gladstap(0.4, 0.9, ruis(P, 12, 74))
    c = c * (1 - 0.25 * vuil[:, None]) + srgb("#5a4228")[None] * 0.25 * vuil[:, None]
    zet(m, c)
    H[m] = (0.0002 * nerf - 0.0006 * naad)[m]
    ruw[m] = np.clip(0.55 + 0.15 * vlek, 0.4, 0.8)[m]


def bouw(sk, coll):
    sk.haarhuid = 0.0
    sk.stof = {"tuniek": dict(weef=0.004, vlek=0.18, kraag=0.85, vuil=0.0),
               "broek": dict(vuil=1.0)}
    d = {}
    d["tuniek"] = BD.bouw_kledij(sk, coll, "tuniek", TUNIEK, mouw_dik=1.0)
    d["broek"] = BD.bouw_broek(sk, coll, "broek", dik=0.84, heup=False)   # heupstuk onder de tuniek gaf zwarte AO-strepen
    d["riem"] = BD.bouw_riem_op(sk, coll, "riem", z0=0.69, a=0.174, b=0.14, gesp="vierkant", gesp_b=0.032,
                                gesp_h=0.026, breed=0.018)
    d["laarzen"] = BD.bouw_laarzen(sk, coll)
    d["lijf"] = BD.bouw_lijf(sk, coll, kopvorm=KOP, extra=extra_lijf)
    d["helm"] = bouw_helm(sk, coll)
    return d


BOUWER = BB.Personage(
    "bouwer", MAAT, DELEN, SOORT, TINTBAAR, VAST, TEXEL, KLEUR, bouw, texel_regio=TEXEL_REGIO,
    bak_ext={"helm": (0.006, 0.02), "laarzen": (0.005, 0.02), "tuniek": (0.006, 0.02), "broek": (0.004, 0.015),
             "riem": (0.004, 0.015), "lijf": (0.008, 0.025)},
    kleurbak=(), sprites=("hammer", "hammer"),
    extra={"weefsel": ("tuniek", "broek"), "haardelen": ()},
)

if __name__ == "__main__":
    BB.bouw_personage(BOUWER)
