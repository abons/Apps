"""Voetsoldaat (voetvolkgilde), game-ready (Blender 5.2 headless -> glb voor Godot 4).

Draaien:
  blender -b -P bumpkin_voetsoldaat.py -- [res=2048] [snel] [vlak] [vergelijk] [poses] [geen_export] [tag=<x>]
  (of: bash alles.sh voetsoldaat)
Zelfde rig, maat, animaties en straat als de man (bumpkin_basis.py + bumpkin_delen.py); dit script is de
configuratie plus helm, schild en knots. Doel: concept/img/voetsoldaat.jpg (ronde 3, goedgekeurd) en sprite
ft_still: stalen puntige helm met gouden band, lang bruin golvend haar, hangsnor, paarse col, paars hemd met
lange mouwen, bruin leren vest met drie riemen en gouden gespen, paarse maillot, bruine laarzen, paars-wit
gevierendeeld puntschild links, stekelknots rechts.

KNOTS: het concept en de sprite hebben een stekelknots; die heet in de glb `prop_zwaard` (op prop_R), zodat
clip aanval_zwaard en bumpkin.gd hem schakelen zoals het zwaard. Bij de voetsoldaat houdt het spel hem
altijd zichtbaar (Bumpkin: glb eindigt op bumpkin_voetsoldaat.glb).
SCHILD: `prop_schild` is een star kind van bot prop_L (zoals de staf van de ouderen); plaats_schild zet hem
zo dat hij in idle frame 0 rechtop naast het been hangt, voorkant naar buiten en iets naar voren.

DELEN (tint = baseColorFactor op een lichtgrijze textuur, zoals de man):
| deel        | inhoud                                          | materiaal       | tint    |
| ----------- | ----------------------------------------------- | --------------- | ------- |
| lijf        | hoofd, oren, hals, handen; oogjes = vast         | mat_lijf + vast | huid    |
| haar        | lang bruin haar tot op de schouders              | mat_haar        | #6a4426 |
| snor        | hangsnor                                         | mat_haar        | #6a4426 |
| helm        | stalen punthelm, gouden band en spangen          | mat_vast        | echt    |
| hemd        | paars hemd, lange mouwen                         | mat_hemd        | #7a3c94 |
| col         | paarse col om de hals                            | mat_col         | #7a3c94 |
| vest        | bruin leren vest, kruisriemen geschilderd        | mat_vast        | echt    |
| broek       | paarse maillot                                   | mat_broek       | #6e3486 |
| riem, riem2, riem3 | leren riemen met gouden gesp              | mat_vast        | echt    |
| laarzen     | omgeslagen leren laarzen                         | mat_laarzen     | bruin   |
| prop_schild | gevierendeeld puntschild, ijzeren rand (prop_L)  | mat_vast        | echt    |
Plus prop_hamer/steen/zaag van de rig en de knots als prop_zwaard op prop_R.
"""
import math
import os
import sys

import bmesh
import bpy
import numpy as np
from mathutils import Matrix, Vector

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import bumpkin_basis as BB  # noqa: E402
import bumpkin_delen as BD  # noqa: E402
import bumpkin_rig as R  # noqa: E402
from bumpkin_basis import GEWICHT, HOOG, Bouwer, gauss, gladstap, ruis, srgb  # noqa: E402

MAAT = {"schouder": 0.32, "kop": 0.25}             # als de man, iets bredere schouders
DELEN = ["lijf", "haar", "snor", "helm", "hemd", "col", "vest", "broek", "riem2", "riem3", "riem", "laarzen",
         "prop_schild"]
SOORT = {"lijf": "lijf", "haar": "haar", "snor": "snor", "helm": "helm", "hemd": "kledij", "col": "kraag",
         "vest": "vest", "broek": "broek", "riem": "riem", "riem2": "riem", "riem3": "riem", "laarzen": "laarzen",
         "prop_schild": "schild"}
TINTBAAR = {"lijf": "huid", "haar": "haar", "snor": "haar", "hemd": "paars", "col": "paars", "broek": "maillot",
            "laarzen": "laars"}
VAST = {"lijf": (3,), "riem": (0, 1), "riem2": (0, 1), "riem3": (0, 1), "helm": (0, 1, 2),
        "vest": (0, 1, 2, 3, 4), "prop_schild": (0, 1, 2)}
TEXEL = {"lijf": 1.9, "haar": 1.2, "snor": 1.9, "helm": 1.3, "hemd": 1.0, "col": 1.0, "vest": 1.0, "broek": 1.0,
         "riem": 1.0, "riem2": 1.0, "riem3": 1.0, "laarzen": 1.1, "prop_schild": 0.9}
TEXEL_REGIO = {("lijf", 2): 1.4 / 1.9, ("lijf", 4): 1.4 / 1.9, ("lijf", 5): 0.6 / 1.9, ("lijf", 6): 1.2 / 1.9}

KLEUR = {
    "huid": srgb("#d9967a"), "haar": srgb("#6a4426"), "snor": srgb("#5a3820"), "paars": srgb("#7a3c94"),
    "maillot": srgb("#6e3486"), "laars": srgb("#4e2f1c"), "zool": srgb("#2a1a0e"), "riem": srgb("#4a2e1a"),
    "gesp": srgb("#c89a30"), "metaal": srgb("#a4a4a0"), "staal": srgb("#9a9ca2"), "goud": srgb("#c8962c"),
    "leer": srgb("#6a4024"), "wit": srgb("#dcdcd6"), "schildpaars": srgb("#7a2e96"), "ijzer": srgb("#5c5e62"),
    "hout": srgb("#4a3424"),
}

# concept: lang gezicht, rechte neus, hangsnor, ernstig; ogen onder de helmrand
KOP = dict(
    oog=(0.0126, 0.0026, 0.0064),
    haar_c=(0, 0.02, 1.15), haar_r=(0.142, 0.118, 0.15, 0.122, 0.3),
    haargrens=[(0.0, 1.2), (0.45, 1.19), (0.8, 1.15), (1.05, 1.06), (1.3, 0.97), (1.8, 0.9), (np.pi, 0.89)],
    klont=(0.08, 0.03),
    gezicht=dict(mond="snor", lach=-0.002, mondbreed=0.022, tris=1500, iris="#5a6a5a", wang=0.4, neusrood=0.3,
                 vorm=dict(neus_h=0.032, neus_r=0.0122, neus_breed=0.0152, neus_vleugel=0.012, neus_bult=0.002,
                           neus_hang=0.002, richel=0.0055, brauw_binnen=(0.002, 0.0015), lidkap=0.002, wal=0.0016,
                           wang_hol=(0.005, 0.004), jukbeen=0.005, kin=0.009, kin_z=0.042, nlf=(0.0022, 0.0018),
                           kaakhoek=0.004, asym=0.001, rimpels=0.0003, seed=41)),
)

# hemd tot op de heup (onder het vest), ronde hals, lange mouwen
HEMD = [(0.985, 0.076, 0.07, 0.068, 0.0), (0.968, 0.098, 0.082, 0.078, 0.0), (0.948, 0.138, 0.098, 0.096, 0.0),
        (0.922, 0.166, 0.114, 0.11, 0.0), (0.88, 0.166, 0.122, 0.116, 0.0), (0.8, 0.162, 0.124, 0.118, 0.0),
        (0.72, 0.162, 0.124, 0.12, 0.0), (0.645, 0.172, 0.132, 0.13, 0.0), (0.6, 0.178, 0.136, 0.134, 0.0)]
# mouwloos leren vest over het hemd, tot over de heup
VEST = [(0.958, 0.13, 0.096, 0.094, 0.0), (0.935, 0.178, 0.12, 0.116, 0.0), (0.9, 0.184, 0.136, 0.13, 0.0),
        (0.86, 0.178, 0.14, 0.134, 0.0), (0.8, 0.174, 0.14, 0.133, 0.0), (0.72, 0.176, 0.14, 0.134, 0.0),
        (0.645, 0.186, 0.146, 0.144, 0.0), (0.57, 0.196, 0.152, 0.15, 0.0), (0.53, 0.2, 0.155, 0.153, 0.0)]


def extra_lijf(B, sk, kop):
    BD.bouw_oren(B, sk, kop, grootte=1.0, uitstaan=0.25, z0=1.09, ph=1.6)


# --- helm -----------------------------------------------------------------------------------------
HELM_RAND = [(0.0, 1.178), (0.6, 1.172), (1.2, 1.155), (1.6, 1.145), (2.2, 1.13), (3.1416, 1.12)]
HELM_PUNT = 0.06          # hoe ver de punt boven de bol uitsteekt (x kop)


def bouw_helm(sk, coll, naam="helm"):
    """Stalen punthelm op de haarschil: koepel (regio 0) die naar een punt loopt, gouden band (regio 1),
    onderrand naar binnen (regio 2). De spangen (gouden stroken) zijn geschilderd."""
    kop = sk.kop
    kk = kop.k
    B = Bouwer()
    nphi, nrow = 48, 14
    phs = 2 * np.pi * np.arange(nphi) / nphi - np.pi
    xs, ys = zip(*HELM_RAND)
    hp = lambda t, p: kop.haarpunt(t, p, False)

    def rand_z(ph):
        return kop.zz(float(np.interp(abs(ph), xs, ys)))

    dik = 0.008 * kk
    rows = [[] for _ in range(nrow + 1)]
    band_o, band_b, band_bo, band_in = [], [], [], []
    for ph in phs:
        tb = kop.theta_bij_z(ph, rand_z(ph), hp)
        for i in range(nrow + 1):
            f = i / nrow
            tht = 0.02 + (tb - 0.02) * f
            p = hp(tht, ph)
            d = (p - kop.C) / np.linalg.norm(p - kop.C)
            punt = HELM_PUNT * kk * (1 - f) ** 2.2
            rows[i].append(p + d * dik + np.array([0, 0, punt]))
        p0 = rows[nrow][-1]
        d = kop.richting(tb, ph)
        dh = np.array([d[0], d[1], 0.0]) / (np.hypot(d[0], d[1]) + 1e-9)
        band_o.append(p0 + dh * 0.005 * kk + np.array([0, 0, 0.004 * kk]))
        band_b.append(p0 + dh * 0.006 * kk - np.array([0, 0, 0.026 * kk]))
        band_bo.append(p0 + dh * 0.002 * kk - np.array([0, 0, 0.03 * kk]))
        band_in.append(p0 - dh * 0.006 * kk - np.array([0, 0, 0.028 * kk]))
    rows_np = np.array(rows)
    b0, _ = B.grid(rows_np[: nrow - 1], True, regio=0)
    top = rows_np[0].mean(0) + np.array([0, 0, 0.004 * kk])
    B.kap(b0, nphi, top, regio=0)
    B.grid(rows_np[nrow - 2:], True, regio=0)
    B.grid(np.array([rows_np[nrow], band_o, band_b]), True, regio=1)
    B.grid(np.array([band_b, band_bo, band_in]), True, regio=2)
    sk.helm_c = kop.C.copy()
    sk.helm_rand = rand_z
    return B.obj(naam, coll)


GEWICHT["helm"] = GEWICHT["kop"]


@BD.hoog("helm", 2, True)
def hg_helm(h, sk):
    P, hgt = h.P, h.hgt
    kk = sk.kop.k
    hgt += 0.0002 * kk * ruis(P, 200, 81) - 0.0005 * kk * gladstap(0.5, 0.9, ruis(P, 25, 82)) * (h.reg == 0)


@BD.verf("helm")
def vf_helm(cx):
    """Geslepen staal met krassen en roestvlekjes; gouden band met gedreven rankwerk; vier gouden spangen."""
    P, reg, sk = cx.P, cx.reg, cx.sk
    ruw, zet, H, KLEUR, m, met = cx.ruw, cx.zet, cx.H, cx.KLEUR, cx.Dm, cx.met
    kk = sk.kop.k
    q = P - sk.helm_c
    ang = np.arctan2(q[:, 0], -q[:, 1])
    rxy = np.hypot(q[:, 0], q[:, 1])
    kras = ruis(np.stack([P[:, 0] * 900, P[:, 1] * 900, P[:, 2] * 40], 1), 1, 83)
    vlek = ruis(P, 30, 84, 3)
    c = KLEUR["staal"][None] * (1 + 0.12 * vlek[:, None] + 0.08 * kras[:, None])
    span = gauss(np.abs(np.sin(ang * 2)) * rxy, 0.006 * kk) * (reg == 0) * (q[:, 2] > -0.02 * kk)
    goud = KLEUR["goud"][None] * (1 + 0.15 * vlek[:, None])
    c = c * (1 - span[:, None]) + goud * span[:, None]
    band = reg == 1
    rank = 0.5 + 0.5 * np.sin(ang * 40) * np.sin((P[:, 2] - sk.helm_rand(0.0)) / (0.003 * kk))
    c[band] = goud[band] * (0.75 + 0.35 * rank[band, None])
    c[reg == 2] = KLEUR["ijzer"] * 0.7
    roest = gladstap(0.55, 0.9, ruis(P, 18, 85)) * (reg == 0) * (1 - span)
    c = c * (1 - 0.3 * roest[:, None]) + srgb("#6a4a30")[None] * 0.3 * roest[:, None]
    zet(m, c)
    H[m] = (0.0003 * rank * band - 0.0004 * gauss(np.abs(np.sin(ang * 2)) * rxy - 0.006 * kk, 0.0012 * kk))[m]
    ruw[m] = np.clip(np.where(band | (span > 0.5), 0.35, 0.38 + 0.15 * vlek + 0.25 * roest), 0.25, 0.8)[m]
    met[m] = np.clip(0.85 - 0.6 * roest, 0, 1)[m]


# --- vest ------------------------------------------------------------------------------------------
GEWICHT["vest"] = GEWICHT["kledij"]
HOOG["vest"] = HOOG["kledij"]


@BD.verf("vest")
def vf_vest(cx):
    """Bruin leer met nerf, sleet en stiksel; twee schouderriemen die voor kruisen, gouden gespjes."""
    P, U, V, z, reg, n, s, sk = cx.P, cx.U, cx.V, cx.z, cx.reg, cx.n, cx.s, cx.sk
    ruw, zet, H, KLEUR, m = cx.ruw, cx.zet, cx.H, cx.KLEUR, cx.Dm
    nerf = ruis(P, 380, 91, 2)
    vlek = ruis(P, 22, 92, 3)
    c = KLEUR["leer"][None] * (1 + 0.22 * vlek[:, None] + 0.08 * nerf[:, None])
    h = 0.0002 * nerf
    voor = P[:, 1] < 0
    # schouderriemen: van de schouder schuin naar het midden, voor (kruis) en achter
    zs = sk.zr(0.93)
    zm = sk.zr(0.72)
    for kant in (-1, 1):
        x_lijn = kant * (0.09 * s - (zs - z) / (zs - zm) * 0.085 * s)
        d = np.abs(P[:, 0] - x_lijn)
        strap = (d < 0.012 * s) & (z < zs + 0.01 * s) & (z > zm) & voor
        rand = (np.abs(d - 0.012 * s) < 0.0012 * s) & (z < zs + 0.01 * s) & (z > zm) & voor
        c[strap] = KLEUR["riem"] * (1 + 0.15 * vlek[strap, None])
        c[rand] *= 0.6
        h += 0.0012 * strap
    # gespjes op de kruisriemen en midden voor
    gesp_m = np.zeros(n, bool)
    for gz in (0.86, 0.8):
        g = (np.abs(z - sk.zr(gz)) < 0.011 * s) & (np.abs(P[:, 0]) < 0.016 * s) & voor
        ring_ = g & ((np.abs(np.abs(z - sk.zr(gz)) - 0.009 * s) < 0.0025 * s) |
                     (np.abs(np.abs(P[:, 0]) - 0.013 * s) < 0.0025 * s))
        gesp_m |= ring_
        h += 0.0015 * ring_
    # voorsluiting: naad met stiksel
    naad = gauss(P[:, 0], 0.0015 * s) * voor
    c *= (1 - 0.35 * naad)[:, None]
    zl, _ = getattr(sk, "kledij_z", {}).get(cx.naam, (0.0, 0.0))
    rand_o = z < zl + 0.015 * s
    c[rand_o] *= 0.8
    st = (np.abs(z - (zl + 0.012 * s)) < 0.0012 * s) & (BB.steek(U, 0.006, 0.0035) > 0)
    c[st] *= 0.65
    sleet = gladstap(0.3, 0.8, vlek) * 0.2
    c = c * (1 + sleet[:, None])
    c[gesp_m] = KLEUR["gesp"]
    c[reg == 3] *= 0.8
    zet(m, c)
    H[m] = h[m]
    ruw[m] = np.clip(0.55 + 0.15 * vlek, 0.4, 0.8)[m]
    cx.met[m] = (0.9 * gesp_m)[m]


# --- schild ----------------------------------------------------------------------------------------
SCHILD_C = np.array([0.75, 0.0, 0.55])   # bouwplek (buiten het lijf, voor de bake), voorkant naar +X
SCHILD_B, SCHILD_BOVEN, SCHILD_ONDER = 0.215, 0.27, 0.34   # halve breedte, boven en onder het midden (m x s)


def schild_omtrek(s, n=56):
    """Omtrek van een puntschild in (y, z) t.o.v. het midden: rechte bovenkant, zijden die naar de punt buigen."""
    b, bo, on = SCHILD_B * s, SCHILD_BOVEN * s, SCHILD_ONDER * s
    pts = []
    for t in np.linspace(0, 1, n, endpoint=False):
        a = t * 2 * np.pi
        if t < 0.25:                                  # bovenkant van rechts naar links (y: +b -> -b)
            u = t / 0.25
            pts.append((b * (1 - 2 * u), bo + 0.012 * s * math.sin(u * math.pi)))
        elif t < 0.625:                               # linkerzijde: recht omlaag, dan in een boog naar de punt
            u = (t - 0.25) / 0.375
            ang = u * math.pi / 2
            pts.append((-b * math.cos(ang) ** 0.75, bo - (bo + on) * math.sin(ang) ** 1.4))
        else:                                         # rechterzijde: van de punt terug omhoog
            u = (t - 0.625) / 0.375
            ang = (1 - u) * math.pi / 2
            pts.append((b * math.cos(ang) ** 0.75, bo - (bo + on) * math.sin(ang) ** 1.4))
        del a
    return np.array(pts)


def bouw_schild(sk, coll, naam="prop_schild"):
    """Gebold puntschild, voorkant naar +X op SCHILD_C: voorvlak (regio 0), ijzeren rand (1), houten achterkant (2)."""
    s = sk.s
    O = schild_omtrek(s)
    n = len(O)
    C0 = SCHILD_C * np.array([s, s, s])
    bol, dik = 0.035 * s, 0.018 * s
    rmax = np.max(np.hypot(O[:, 0], O[:, 1]))

    def voor(f):
        y, z = O[:, 0] * f, O[:, 1] * f
        r2 = (y ** 2 + (z * 0.8) ** 2) / rmax ** 2
        return np.stack([C0[0] + bol * (1 - r2) - 0.0 * y, C0[1] + y, C0[2] + z], 1)

    B = Bouwer()
    fs = [0.12, 0.3, 0.5, 0.7, 0.86, 0.93]
    rows = np.array([voor(f) for f in fs])
    b0, _ = B.grid(rows, True, regio=0, buiten=(1, 0, 0))
    B.kap(b0, n, voor(0.0)[0], regio=0, buiten=(1, 0, 0))
    rand = voor(1.0)
    uit = np.concatenate([np.zeros((n, 1)), O / (np.linalg.norm(O, axis=1, keepdims=True) + 1e-9)], 1)
    r1 = rand + uit * 0.004 * s + np.array([0.003 * s, 0, 0])
    r2 = rand + uit * 0.006 * s - np.array([dik * 0.5, 0, 0])
    r3 = rand - np.array([dik, 0, 0])
    B.grid(np.array([rows[-1], rand, r1, r2, r3]), True, regio=1)
    achter = lambda f: voor(f) - np.array([dik, 0, 0]) - np.array([bol * 0.3, 0, 0]) * (1 - f)
    rows_a = np.array([achter(f) for f in (1.0, 0.7, 0.4, 0.15)])
    rows_a[0] = r3
    ba, _ = B.grid(rows_a, True, regio=2, buiten=(-1, 0, 0))
    B.kap(ba + 3 * n, n, achter(0.0)[0], regio=2, buiten=(-1, 0, 0))
    # handgreep achter (regio 2): een leren lus
    g0 = C0 + np.array([-dik - 0.012 * s, 0, 0.0])
    gp = [g0 + np.array([-0.025 * s * math.sin(a), 0, 0.07 * s * math.cos(a)]) for a in np.linspace(0, math.pi, 9)]
    fr = BB.keten(gp, list(np.linspace(0, 0.2 * s, 9)), ref=(0, 1, 0))
    rings = [BB.ring(pos, sd, f, 0.012 * s, 0.004 * s, 6) for pos, t, f, sd in fr]
    B.grid(np.array(rings), True, regio=2)
    sk.schild = dict(C=C0, O=O, rmax=rmax)
    return B.obj(naam, coll)


@BD.hoog("schild", 1, True)
def hg_schild(h, sk):
    P, reg, s, hgt = h.P, h.reg, h.s, h.hgt
    hgt += 0.0006 * s * ruis(P, 60, 93) * (reg == 0) + 0.0008 * s * ruis(P * np.array([0.2, 1, 6]), 40, 94) * (reg == 2)


@BD.verf("schild")
def vf_schild(cx):
    """Gevierendeeld paars/wit (links boven wit van voren gezien), verweerd, met krassen; ijzeren rand met
    klinknagels; houten achterkant met planken."""
    P, reg, s, sk, n = cx.P, cx.reg, cx.s, cx.sk, cx.n
    ruw, zet, H, KLEUR, m, met = cx.ruw, cx.zet, cx.H, cx.KLEUR, cx.Dm, cx.met
    sc = getattr(sk, "schild", None)
    C0 = sc["C"] if sc else SCHILD_C * s
    y = P[:, 1] - C0[1]
    zq = P[:, 2] - (C0[2] + 0.02 * s)
    # van voren (vanaf +X kijkend) is links = +Y
    wit = (np.sign(y) * np.sign(zq)) > 0
    vlek = ruis(P, 25, 95, 3)
    kras = ruis(np.stack([P[:, 0] * 50, P[:, 1] * 600 + P[:, 2] * 300, P[:, 2] * 80], 1), 1, 96)
    c = np.where(wit[:, None], KLEUR["wit"][None], KLEUR["schildpaars"][None])
    c = c * (1 + 0.12 * vlek[:, None] + 0.06 * kras[:, None])
    grens = gauss(np.minimum(np.abs(y), np.abs(zq)), 0.0015 * s)
    c *= (1 - 0.15 * grens)[:, None]
    afgebladderd = 0.7 * gladstap(0.72, 0.9, ruis(P, 70, 97)) * (reg == 0)
    c = c * (1 - afgebladderd[:, None]) + srgb("#7a6048")[None] * afgebladderd[:, None]
    vuil = gladstap(0.0, -0.3 * s, zq) * 0.3
    c = c * (1 - vuil[:, None]) + srgb("#5a4a36")[None] * vuil[:, None]
    h = -0.0004 * afgebladderd + 0.0001 * kras
    r = reg == 1
    O = sc["O"] if sc else None
    nagel = np.zeros(n)
    if O is not None:
        kp = O[::4] * 0.965
        dmin = np.min(np.hypot(y[:, None] - kp[None, :, 0], (P[:, 2] - C0[2])[:, None] - kp[None, :, 1]), 1)
        nagel = gauss(dmin, 0.0045 * s) * ((reg == 1) | (reg == 0))
    c[r] = KLEUR["ijzer"] * (1 + 0.2 * vlek[r, None])
    c = c * (1 - nagel[:, None]) + KLEUR["metaal"][None] * 1.1 * nagel[:, None]
    h += 0.0012 * nagel
    a = reg == 2
    plank = 0.5 + 0.5 * np.sin(P[a, 1] / (0.045 * s) * math.pi)
    c[a] = KLEUR["hout"] * (0.8 + 0.4 * ruis(P[a] * np.array([0.3, 1, 8]), 30, 98)[:, None]) * \
        (1 - 0.25 * gauss(plank - 1, 0.05))[:, None]
    zet(m, c)
    H[m] = h[m]
    ruw[m] = np.where(r | (nagel > 0.5), 0.45, np.where(a, 0.85, 0.6 + 0.2 * afgebladderd))[m]
    met[m] = np.where(r | (nagel > 0.5), 0.8, 0.0)[m]


def plaats_schild(rig, obj, actie="idle", frame=0):
    """Zet het (op SCHILD_C gebouwde) schild star in de linkerhand: in idle frame 0 rechtop naast het been,
    voorkant naar buiten (+X) en 55 graden naar voren gedraaid, de greep in de vuist."""
    act = bpy.data.actions[actie]
    ad = rig.animation_data_create()
    ad.action = act
    if getattr(ad, "action_slot", None) is None and len(getattr(act, "slots", [])):
        ad.action_slot = act.slots[0]
    bpy.context.scene.frame_set(frame)
    bpy.context.view_layer.update()
    Mp = rig.pose.bones["prop_L"].matrix.copy()
    Mr = rig.data.bones["prop_L"].matrix_local.copy()
    s = rig["hoogte"] / 1.37
    rot = Matrix.Rotation(math.radians(-55), 4, "Z")
    n = rot @ Vector((1, 0, 0, 0))
    palm = Mp.translation
    doel_pos = Vector((palm.x, palm.y, palm.z)) + Vector((n.x, n.y, n.z)) * 0.045 * s + Vector((0, 0, 0.03 * s))
    greep = Vector((SCHILD_C[0] * s - 0.03 * s, SCHILD_C[1] * s, SCHILD_C[2] * s))
    T = Mr @ Mp.inverted() @ Matrix.Translation(doel_pos) @ rot @ Matrix.Translation(-greep)
    me = obj.data
    for v in me.vertices:
        v.co = T @ v.co
    me.update()
    ad.action = None
    for b in rig.pose.bones:
        b.rotation_quaternion = (1, 0, 0, 0)
        b.location = (0, 0, 0)
    bpy.context.scene.frame_set(0)
    bpy.context.view_layer.update()


# --- knots (als prop_zwaard) -----------------------------------------------------------------------
def maak_knots(naam="prop_zwaard"):
    """Stekelknots langs +Y (greep-as van prop_R, zoals het zwaard): houten steel met leren wikkel, ijzeren
    kraag, stalen bol met 14 stekels. Twee materialen (hout, staal)."""
    mb = R.MeshBouwer()
    mb.kapsel((0, -0.09, 0), (0, 0.36, 0), 0.0135, 0.0155, "hout")
    for y in np.linspace(-0.06, 0.07, 6):                         # leren wikkel
        mb.kapsel((0, y, 0), (0, y + 0.018, 0), 0.0165, 0.0165, "leer")
    mb.bol((0, -0.1, 0), 0.02, "staal", 10)                       # knop
    mb.kapsel((0, 0.34, 0), (0, 0.39, 0), 0.02, 0.024, "staal")   # kraag
    hc = (0, 0.44, 0)
    mb.bol(hc, 0.052, "staal", 14)
    bm = mb.bm
    gr = (1 + 5 ** 0.5) / 2
    k = 14
    for i in range(k):                                            # fibonacci-bol: stekels gelijk verdeeld
        zz = 1 - 2 * (i + 0.5) / k
        r = math.sqrt(1 - zz * zz)
        a = 2 * math.pi * i / gr
        d = Vector((r * math.cos(a), zz, r * math.sin(a)))
        if d.y < -0.75:
            continue                                              # niet in de steel
        p0 = Vector(hc) + d * 0.045
        L = 0.04
        q = d.to_track_quat("Z", "Y")
        M = Matrix.Translation(p0 + d * L / 2) @ q.to_matrix().to_4x4()
        res = bmesh.ops.create_cone(bm, cap_ends=True, cap_tris=False, segments=6, radius1=0.011, radius2=0.0008,
                                    depth=L, matrix=M)
        mb._reg("staal", res)
    ob = mb.naar_object(naam, R.materiaal("knots_hout", (0.25, 0.15, 0.08)))
    me = ob.data
    staal = R.materiaal("knots_staal", (0.55, 0.56, 0.6))
    staal.node_tree.nodes["Principled BSDF"].inputs["Metallic"].default_value = 0.9
    staal.node_tree.nodes["Principled BSDF"].inputs["Roughness"].default_value = 0.35
    leer = R.materiaal("knots_leer", (0.2, 0.12, 0.06))
    me.materials.append(staal)
    me.materials.append(leer)
    groep = {}
    for vg_naam, idx in (("staal", 1), ("leer", 2)):
        vg = ob.vertex_groups.get(vg_naam)
        if vg is None:
            continue
        for v in me.vertices:
            for g in v.groups:
                if g.group == vg.index:
                    groep[v.index] = idx
    for p in me.polygons:
        ids = [groep.get(v, 0) for v in p.vertices]
        p.material_index = max(set(ids), key=ids.count)
    for v in list(ob.vertex_groups):
        ob.vertex_groups.remove(v)
    R.bmesh_fix(ob)
    return ob


def props(sk, rig, delen):
    oud = bpy.data.objects.get("prop_zwaard")
    if oud is not None:
        bpy.data.objects.remove(oud, do_unlink=True)
    ob = maak_knots("prop_zwaard")
    ob.parent = rig
    ob.parent_type = "BONE"
    ob.parent_bone = "prop_R"
    ob.location = (0, -rig.data.bones["prop_R"].length, 0)


def na_animatie(rig):
    plaats_schild(rig, bpy.data.objects["prop_schild"])


def bouw(sk, coll):
    sk.haarlicht = (0.7, 1.2)
    sk.stof = {"hemd": dict(weef=0.004, vlek=0.15, kraag=0.85, vuil=0.0),
               "broek": dict(vuil=1.0)}
    d = {}
    d["hemd"] = BD.bouw_kledij(sk, coll, "hemd", HEMD, mouw_dik=1.0)
    d["vest"] = BD.bouw_kledij(sk, coll, "vest", VEST, mouwen=False, zoom=0.008)
    d["col"] = BD.bouw_kraag(sk, coll, "col", r_in=0.06, r_uit=0.11, zak=0.035, plooien=7, plooi=0.006,
                             hoog_=0.03, bv=0.92, zacht=0.8)
    d["broek"] = BD.bouw_broek(sk, coll, "broek", dik=0.84, heup=False)
    d["riem3"] = BD.bouw_riem_op(sk, coll, "riem3", z0=0.86, a=0.188, b=0.146, gesp="vierkant", gesp_b=0.02,
                                 gesp_h=0.016, breed=0.01)
    d["riem2"] = BD.bouw_riem_op(sk, coll, "riem2", z0=0.79, a=0.182, b=0.146, gesp="vierkant", gesp_b=0.02,
                                 gesp_h=0.016, breed=0.01)
    d["riem"] = BD.bouw_riem_op(sk, coll, "riem", z0=0.66, a=0.194, b=0.154, gesp="vierkant", gesp_b=0.03,
                                gesp_h=0.024, breed=0.017)
    d["laarzen"] = BD.bouw_laarzen(sk, coll)
    d["lijf"] = BD.bouw_lijf(sk, coll, kopvorm=KOP, extra=extra_lijf)
    d["snor"] = BD.bouw_snor(sk, coll)
    d["haar"] = BD.bouw_haar(sk, coll, lang=True)   # geen krulkaarten: die staken door de helm
    BD.schil_strengen(sk, 160 if BB.SNEL else 420, BD.rond((0, 0.1, 1), 0.3), BD.naar_grens(sk.kop, 0.003), seed=11,
                      dikte=(0.0011, 0.0017), licht=(0.8, 1.15))
    BD.haar_hoog(sk, KLEUR["haar"], donker=0.7, punt=1.15, warm=0.05)
    d["helm"] = bouw_helm(sk, coll)
    d["prop_schild"] = bouw_schild(sk, coll)
    # volgorde = DELEN (bakvolgorde)
    return {k: d[k] for k in DELEN}


VOETSOLDAAT = BB.Personage(
    "voetsoldaat", MAAT, DELEN, SOORT, TINTBAAR, VAST, TEXEL, KLEUR, bouw, texel_regio=TEXEL_REGIO,
    bak_ext={"haar": (0.03, 0.06), "snor": (0.006, 0.02), "helm": (0.006, 0.02), "laarzen": (0.005, 0.02),
             "hemd": (0.006, 0.02), "vest": (0.006, 0.02), "col": (0.006, 0.02), "broek": (0.004, 0.015),
             "riem": (0.004, 0.015), "riem2": (0.004, 0.015), "riem3": (0.004, 0.015), "lijf": (0.008, 0.025),
             "prop_schild": (0.006, 0.02)},
    kleurbak=("haar",), sprites=("m_still", "m_walk"),
    props=props, na_animatie=na_animatie,
    extra={"mat": {"snor": "mat_haar"}, "weefsel": ("hemd", "broek"),
           "prop_delen": {"prop_schild": "prop_L"}, "zichtbare_props": ("prop_schild", "prop_zwaard"),
           "vergelijk_actie": ("idle", 0)},
)

if __name__ == "__main__":
    BB.bouw_personage(VOETSOLDAAT)
