"""Zombie (missie 4, wezen-type 18), game-ready (Blender 5.2 headless -> glb voor Godot 4).

Draaien:
  blender -b -P zombie.py -- [res=2048] [snel] [vlak] [geen_export] [preview]
- `vlak`: geen bake (platte kleuren), snel kijken naar vorm en clips.
- `preview`: preview/zombie_aanzichten.png (voor, 3/4, zij, achter) en preview/zombie_clips.png (strip per clip).
Uitvoer: bumpkin_zombie.glb (+ zombie_anim.json); sync.ps1 kopieert hem als spel/assets/zombie.glb.

Doel: concept/img/zombie.jpg (goedgekeurd 2026-10-31: kale grijsgroene kop, een groen gloeiend oog, bruine lompen
met gaten en rafelranden, driekwartbroek, blote voeten) en de sprites zombie/zombatta/zombdead (lokaal/bb_original).
Zelfde straat als de bumpkins (bumpkin_basis/bumpkin_delen, skelet bumpkin_rig), dus dezelfde stijl en maat; alleen
de clips zijn eigen (zoals wolf_anim.json, die view/wolf_model.gd leest):
| clip   | lus | wat                                                                                   |
| idle   | ja  | gebogen, zwaait van voet op voet, kop knikt mee                                       |
| lopen  | ja  | schuifelen: armen naar voren, rechterbeen sleept                                      |
| rennen | ja  | sneller strompelen, voorover                                                         |
| bijten | nee | aanval zoals zombatta: armen vooruit en de kop vliegt naar het doel en terug (bot Head |
|        |     | krijgt locatiesleutels; inslag op 0,42 = Wolf.STRIKE_AT); de nek heeft een stomp       |
| dood   | nee | wankelt, knieen knikken, valt voorover (zombdead: hoopje op de grond)                  |
Extra's (niet geskind, aan een bot): `zombie_oog` (gloeibol, emissief groen, rechteroog) en `zombie_stomp` (nekstomp)."""
import json
import math
import os
import sys

import bpy
import numpy as np
from mathutils import Matrix, Vector

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import bumpkin_basis as BB  # noqa: E402
import bumpkin_delen as BD  # noqa: E402
import bumpkin_rig as R  # noqa: E402
from bumpkin_basis import Bouwer, gladstap, keten, keten_param, overgang, ring, srgb, vertex_regio  # noqa: E402

MAAT = {"hoogte": 1.42, "kop": 0.245, "schouder": 0.30, "been": 0.47}
DELEN = ["lijf", "hemd", "broek"]
SOORT = {"lijf": "lijf", "hemd": "kledij", "broek": "broek"}
TINTBAAR = {"lijf": "huid", "hemd": "hemd", "broek": "broek"}
VAST = {"lijf": (3,)}
TEXEL = {"lijf": 1.9, "hemd": 1.0, "broek": 1.0}
TEXEL_REGIO = {("lijf", 2): 1.3 / 1.9, ("lijf", 4): 1.3 / 1.9, ("lijf", 5): 0.8 / 1.9, ("lijf", 7): 0.9 / 1.9}

KLEUR = {
    "huid": srgb("#5c6455"), "hemd": srgb("#5e4a34"), "broek": srgb("#5a4430"), "snor": srgb("#3a3a30"),
    "gat": srgb("#2a2620"), "oog": srgb("#30ff10"),
}
OOG_GLOED = 4.0                      # emissiesterkte van het groene oog (glTF KHR_materials_emissive_strength)

# Kop: de oude man als basis (diepe oogkassen, holle wangen, ingevallen mond), nog magerder, neus weggerot,
# mond half open met een paar tanden. Geen haar (een paar plukjes in de textuur).
KOP = dict(
    schedel=(0.094, 0.112, 0.126, 0.118), kaak=(-0.02, 0.32, 0.22), ogen_ph=0.42, ogen_z=1.115, mond_z=1.03,
    neus=(0, -0.1, -0.034),
    neusprof=((0.03, 0.009, 0.008, 0.01), (0.012, 0.012, 0.012, 0.0), (-0.006, 0.017, 0.016, -0.004),
              (-0.02, 0.017, 0.014, -0.004), (-0.03, 0.012, 0.009, 0.0)),
    oog=(0.0124, 0.0030, 0.0068),
    haar_c=(0, 0.015, 1.15), haar_r=(0.11, 0.115, 0.12, 0.13, 0.12), klont=(0.0, 0.0),
    gezicht=dict(stoppels=False, mond="lach", lach=-0.004, mondbreed=0.026, spleet=0.004, open=0.006, onderlip=0.002,
                 bovenlip=0.0015, lip="#4a4a3c", iris="#b8bca8", wang=0.0, neusrood=0.0, rood="#5a6a4a", rimpel=1.6,
                 voorhoofd=(0.036, 0.048, 0.06), kraai=(-0.3, 0.1, 0.45), wal=2.4, wimperkleur="#2a2a22",
                 lidtint="#4a4a3a", lidkleur="#3a3a2c", lid=0.002, schijf_lid=0.0018, oog_open=(0.0118, 0.0068),
                 brauw=(0.021, 0.006, 0.0022), tand="#c8b88a", tris=1500,
                 vorm=dict(neus_h=0.016, neus_r=0.0085, neus_breed=0.010, neus_vleugel=0.007, neus_brug=0.002,
                           richel=0.0068, oogkas=0.0115, oog_diep=0.008, wal=0.0032, lidkap=0.0012,
                           wang_hol=0.0105, jukbeen=0.0085, slaap=0.0055, mond_in=0.0035, kin=0.007, kin_z=0.034,
                           nlf=(0.003, 0.0028), rimpels=0.0006, kaakhoek=0.006, asym=0.0018, mond_scheef=0.003,
                           brauw_binnen=(0.001, 0.0), seed=31)),
)

# Hemd tot op de dij, V-hals; mouwen worden na het bouwen afgescheurd boven de elleboog (rafelrand).
HEMD = [(0.985, 0.078, 0.07, 0.068, 0.024), (0.968, 0.1, 0.082, 0.078, 0.022), (0.948, 0.14, 0.098, 0.096, 0.016),
        (0.922, 0.168, 0.114, 0.11, 0.006), (0.88, 0.168, 0.12, 0.116, 0.0), (0.8, 0.164, 0.122, 0.118, 0.0),
        (0.72, 0.166, 0.124, 0.12, 0.0), (0.645, 0.178, 0.132, 0.13, 0.0), (0.57, 0.188, 0.138, 0.137, 0.0),
        (0.52, 0.194, 0.142, 0.141, 0.0)]


def rafel(phi, seed, n=9, diep=1.0):
    """0..1 per hoek: onregelmatige punten (lompen); gesloten om de cirkel."""
    rng = np.random.default_rng(seed)
    fa = rng.uniform(0, 2 * np.pi, 4)
    w = 0.0
    for i, (k, a) in enumerate(((n, 0.5), (n * 2 + 1, 0.3), (5, 0.25), (3, 0.2))):
        w = w + a * np.abs(np.sin(k * phi * 0.5 + fa[i]))
    w = (w - 0.2) / 1.0
    return np.clip(w, 0, 1) * diep


def verts_np(me):
    P = np.zeros(len(me.vertices) * 3)
    me.vertices.foreach_get("co", P)
    return P.reshape(-1, 3)


def zet_verts(me, P):
    me.vertices.foreach_set("co", P.ravel())
    me.update()


def scheur_hemd(o, sk):
    """Rafelzoom (z omhoog per hoek) en mouwen afgescheurd net boven de elleboog, met een gescheurde rand."""
    import bmesh
    me = o.data
    s = sk.s
    P = verts_np(me)
    zl, _ = sk.kledij_z["hemd"]
    phi = np.arctan2(P[:, 0], -P[:, 1])
    onder = gladstap(zl + 0.07 * s, zl, P[:, 2])
    P[:, 2] += onder * rafel(phi, 4, n=11) * 0.075 * s
    zet_verts(me, P)
    # mouwen: vlakken voorbij de knip weg (regio 1 en 4), knip per hoek rond de arm
    bm = bmesh.new()
    bm.from_mesh(me)
    lay = bm.faces.layers.int.get("regio")
    weg = []
    for k, sx in (("Left", 1), ("Right", -1)):
        pts = sk.mouwen["hemd"][k]
        L0 = np.linalg.norm(pts[1] - pts[0])
        e = L0 + np.linalg.norm(pts[2] - pts[1])
        for f in bm.faces:
            if f[lay] not in (1, 4):
                continue
            c = np.array(f.calc_center_median())
            if np.sign(c[0]) != sx:
                continue
            d, rv = keten_param(c[None], pts)
            a = math.atan2(rv[0, 1], rv[0, 2])
            knip = e - 0.075 * s - 0.05 * s * float(rafel(np.array([a]), 7 if sx > 0 else 9, n=5)[0])
            if d[0] > knip:
                weg.append(f)
    bmesh.ops.delete(bm, geom=list(set(weg)), context="FACES")
    bm.to_mesh(me)
    bm.free()
    me.update()


def bouw_broek_kort(sk, coll, naam="broek", dik=0.9):
    """Driekwartbroek: pijpen tot halverwege de kuit met een rafelrand, heupstuk als bouw_broek."""
    J = sk.J
    s = sk.s
    Z = sk.z
    B = Bouwer()
    for k, sx in (("Left", 1), ("Right", -1)):
        pts = [J[k + "UpLeg"], J[k + "Leg"], J[k + "Foot"]]
        L1 = np.linalg.norm(pts[1] - pts[0])
        L2 = np.linalg.norm(pts[2] - pts[1])
        q = s
        eind = L1 + L2 * 0.55
        prof = [(-0.03 * q, 0.078, 0.082), (0.0, 0.085, 0.09), (0.04 * q, 0.087, 0.093), (0.10 * q, 0.087, 0.091),
                (0.17 * q, 0.085, 0.088), (L1 - 0.05 * q, 0.082, 0.085), (L1 - 0.02 * q, 0.08, 0.083),
                (L1, 0.079, 0.084), (L1 + 0.035 * q, 0.079, 0.082), (L1 + 0.08 * q, 0.078, 0.08),
                (eind - 0.04 * q, 0.077, 0.079), (eind, 0.079, 0.081)]
        fr = keten(pts, [p[0] for p in prof], zacht=0.06)
        rings = []
        for i, ((pos, t, f, sd), (d, a, b)) in enumerate(zip(fr, prof)):
            inw = np.array([-sx * 0.014 * s * (1 - np.clip(d / L1, 0, 1)), 0, 0])
            r = ring(pos + inw, sd, f, a * s * dik, b * s * dik, 20, 2.2)
            if i == len(prof) - 1:                                  # rafelrand: punten omlaag
                th = 2 * np.pi * np.arange(20) / 20
                r = r - t[None] * (rafel(th, 11 if sx > 0 else 13, n=7) * 0.06 * s)[:, None]
            rings.append(r)
        B.grid(np.array(rings), True, regio=0)
    hp = [(0.545, 0.10, 0.08), (0.57, 0.13, 0.10), (0.60, 0.152, 0.12), (0.64, 0.161, 0.126),
          (0.68, 0.163, 0.127), (0.687, 0.156, 0.12), (0.672, 0.148, 0.113)]
    rings = [ring((0, 0.004 * s, Z(z)), (1, 0, 0), (0, -1, 0), a * s * dik, b * s * dik, 22, 2.3, fase=-np.pi / 2)
             for z, a, b in hp]
    b0, _ = B.grid(np.array(rings), True, regio=1)
    B.kap(b0, 22, (0, 0.004 * s, Z(0.53)), regio=1)
    return B.obj(naam, coll)


def onderarmen(B, sk):
    """Blote, magere onderarmen (regio 2, zoals de handen) van onder de mouw tot in de hand."""
    J = sk.J
    s = sk.s
    for k in ("Left", "Right"):
        pts = [J[k + "Arm"], J[k + "ForeArm"], J[k + "Hand"]]
        L0 = np.linalg.norm(pts[1] - pts[0])
        L1 = np.linalg.norm(pts[2] - pts[1])
        prof = [(L0 - 0.12 * s, 0.036), (L0 - 0.06 * s, 0.035), (L0 - 0.015 * s, 0.033), (L0 + 0.01 * s, 0.033),
                (L0 + 0.05 * s, 0.034), (L0 + 0.10 * s, 0.031), (L0 + L1 - 0.05 * s, 0.026),
                (L0 + L1 - 0.015 * s, 0.026), (L0 + L1 + 0.01 * s, 0.026)]
        fr = keten(pts, [p[0] for p in prof], zacht=0.04)
        rings = [ring(pos, sd, f, r * s, r * s * 0.88, 12, 2.0) for (pos, t, f, sd), (d, r) in zip(fr, prof)]
        B.grid(np.array(rings), True, regio=2)


def voeten(B, sk):
    """Magere kuiten en blote voeten (regio 7): kuit van onder de broek tot de enkel, voet als loft hiel -> tenen."""
    J = sk.J
    s = sk.s
    BD.bouw_kuiten(B, sk, van=0.40, tot=0.075, dik=0.78)
    for k, sx in (("Left", 1), ("Right", -1)):
        an = J[k + "Foot"]
        rot = math.radians(8) * sx
        fwd = np.array([math.sin(rot) * 1, -math.cos(rot), 0.0])
        fwd = np.array([sx * math.sin(math.radians(8)), -math.cos(math.radians(8)), 0.0])
        side = np.array([-fwd[1], fwd[0], 0.0])
        # (y vooruit vanaf de enkel, halve breedte, hoogte boven, hoogte onder) in m bij s = 1
        prof = [(0.06, 0.014, 0.03, 0.0), (0.052, 0.024, 0.055, 0.0), (0.036, 0.028, 0.075, 0.0),
                (0.012, 0.029, 0.082, 0.0), (-0.02, 0.03, 0.066, 0.0), (-0.055, 0.034, 0.046, 0.0),
                (-0.09, 0.038, 0.032, 0.0), (-0.12, 0.038, 0.025, 0.0), (-0.142, 0.033, 0.02, 0.0),
                (-0.155, 0.022, 0.015, 0.0)]
        rings = []
        for y, w, ht, _ in prof:
            c = np.array([an[0], an[1], 0.0]) + fwd * (-y) * s * 1.0 + np.array([0, 0, ht * 0.5 * s])
            rings.append(ring(c, side, (0, 0, 1), w * s, ht * 0.5 * s, 14, 2.6))
        b0, _ = B.grid(np.array(rings), True, regio=7)
        B.kap(b0, 14, np.array([an[0], an[1], 0.0]) + fwd * (-0.068) * s + np.array([0, 0, 0.018 * s]), regio=7)
        B.kap(b0 + 14 * (len(prof) - 1), 14, np.array([an[0], an[1], 0.0]) + fwd * 0.162 * s +
              np.array([0, 0, 0.008 * s]), regio=7)


def nek_borst(B, sk):
    """Nek plus magere borst onder de V-hals (regio 5), lager dan bouw_nek: de V gaat dieper."""
    s = sk.s
    Z = sk.z
    nk = [(0.80, 0.14, 0.098), (0.85, 0.138, 0.096), (0.905, 0.112, 0.082), (0.94, 0.098, 0.076), (0.975, 0.074, 0.066),
          (1.0, 0.06, 0.06), (1.03, 0.047, 0.048), (1.07, 0.045, 0.046)]
    rings = [ring((0, 0.006 * s, Z(z)), (1, 0, 0), (0, -1, 0), a * s, b * s, 16, 2.2, fase=-np.pi / 2) for z, a, b in nk]
    B.grid(np.array(rings), True, regio=5)


def extra_lijf(B, sk, kop):
    BD.bouw_oren(B, sk, kop, grootte=1.0, uitstaan=0.3, z0=1.10, ph=1.62)
    BD.bouw_tanden(B, sk, kop, [(-0.011, 0.0075, 0.009), (-0.0035, 0.007, 0.011), (0.004, 0.007, 0.008),
                                (0.0115, 0.007, 0.010)], dz=0.0015)
    onderarmen(B, sk)
    voeten(B, sk)


def bouw(sk, coll):
    sk.stof = {"hemd": dict(weef=0.006, vlek=0.32, kraag=0.8, vuil=1.0, vuil_hoogte=0.3), "broek": dict(vuil=1.6)}
    sk.vuil = 2.2
    sk.handmaat = 1.1
    d = {}
    d["hemd"] = BD.bouw_kledij(sk, coll, "hemd", HEMD, mouw_dik=0.92, mouw_wijd=1.12)
    scheur_hemd(d["hemd"], sk)
    d["broek"] = bouw_broek_kort(sk, coll, "broek", dik=0.88)
    d["lijf"] = BD.bouw_lijf(sk, coll, kopvorm=KOP, nek=nek_borst, extra=extra_lijf)
    return d


# --- gewichten: kop helemaal aan Head (hij vliegt los), onderarm met elleboog, voet aan Foot ------------
_gw_lijf = BB.GEWICHT["lijf"]


def gw_zombie_lijf(g):
    _gw_lijf(g)
    P, G, J, s, sk = g.P, g.G, g.J, g.s, g.sk
    reg = vertex_regio(g.me)
    N = len(P)
    nul = np.zeros(N)

    def zet(mask, bot, w):
        for b in G:
            G[b] = np.where(mask, 0.0, G[b])
        G[bot] = np.where(mask, w, G.get(bot, nul))

    kopm = np.isin(reg, (0, 1, 3, 6))
    G["Neck"] = G.get("Neck", nul) + np.where(kopm, 0.0, G.get("Head", nul))   # nek/borst nooit aan de kop
    for b in list(G):
        G[b] = np.where(kopm, 0.0, G[b])
    G["Head"] = np.where(kopm, 1.0, 0.0)
    for k, sx in (("Left", 1), ("Right", -1)):
        pts = [J[k + "Arm"], J[k + "ForeArm"], J[k + "Hand"], J[k + "HandEnd"]]
        L0 = np.linalg.norm(pts[1] - pts[0])
        L1 = np.linalg.norm(pts[2] - pts[1])
        d, _ = keten_param(P, pts)
        arm = (reg == 2) & (sx * P[:, 0] > 0) & (d < L0 + L1 - 0.035 * s)
        if arm.any():
            W = overgang(d, [L0, L0 + L1], [0.06 * s, 0.03 * s])
            for b in list(G):
                G[b] = np.where(arm, 0.0, G[b])
            for i, b in enumerate((k + "Arm", k + "ForeArm", k + "Hand")):
                G[b] = np.where(arm, W[:, i], G.get(b, nul))
        voet = (reg == 7) & (sx * P[:, 0] > 0)
        wf = gladstap(J[k + "Foot"][2] + 0.035 * s, J[k + "Foot"][2] - 0.01 * s, P[:, 2]) * voet
        for b in list(G):
            G[b] = G[b] * (1 - wf)
        G[k + "Foot"] = G.get(k + "Foot", nul) + wf
    del zet


BB.GEWICHT["lijf"] = gw_zombie_lijf


# --- textuur: gaten en rafels in de stof, ontbinding op de huid ----------------------------------------
def _gaten(cx, plekken, seed):
    """Masker 0..1 voor gaten (donker, met een lichtere rafelrand) op willekeurige plekken in de stof."""
    from bumpkin_basis import ruis
    P = cx.P
    gat = np.zeros(cx.n)
    rand = np.zeros(cx.n)
    rng = np.random.default_rng(seed)
    nz = ruis(P, 160, seed, 2)
    for c, r in plekken:
        c = np.array(c) + rng.uniform(-0.01, 0.01, 3)
        dd = np.linalg.norm((P - c) * np.array([1.0, 1.0, 0.8]), axis=1) / r + 0.35 * nz
        gat = np.maximum(gat, gladstap(1.0, 0.92, dd))
        rand = np.maximum(rand, gladstap(1.3, 1.0, dd) * (dd > 0.95))
    return gat, rand


GATEN = {
    "hemd": [((0.07, -0.13, 0.86), 0.022), ((-0.08, -0.14, 0.72), 0.03), ((0.10, -0.12, 0.62), 0.018),
             ((-0.04, 0.13, 0.80), 0.026), ((0.09, 0.12, 0.66), 0.02), ((-0.13, -0.02, 0.92), 0.02),
             ((0.16, -0.03, 0.77), 0.017), ((0.20, 0.0, 1.0), 0.016), ((-0.21, -0.02, 0.98), 0.014),
             ((-0.12, 0.12, 0.62), 0.022), ((0.13, 0.11, 0.90), 0.018), ((0.0, 0.14, 0.70), 0.016),
             ((-0.15, -0.10, 0.58), 0.02), ((0.04, -0.15, 0.95), 0.014)],
    "broek": [((0.10, -0.10, 0.42), 0.03), ((-0.09, -0.09, 0.30), 0.024), ((-0.11, 0.06, 0.48), 0.022),
              ((0.08, 0.07, 0.24), 0.02), ((0.12, -0.06, 0.20), 0.016), ((-0.12, -0.05, 0.56), 0.018),
              ((-0.07, -0.10, 0.40), 0.02), ((0.11, 0.05, 0.36), 0.018), ((-0.10, 0.07, 0.25), 0.016)],
}


def _wikkel(soort, nm_gaten):
    orig = BB.VERF[soort]

    def f(cx):
        orig(cx)
        if cx.naam not in GATEN:
            return
        m = cx.Dm
        h = cx.sk.s / 1.37
        plekken = [((c[0] * h, c[1] * h, c[2] * BB.C.MAAT["hoogte"] / 1.37), r * h * 1.5) for c, r in GATEN[cx.naam]]
        gat, rand = _gaten(cx, plekken, 50 + len(cx.naam))
        huid = srgb("#4a5242")
        from bumpkin_basis import ruis
        c = cx.kl.copy()
        # vergane stof: vlekken, verkleuring, donker in de plooien
        vl = 0.5 + 0.5 * ruis(cx.P, 11, 61 + len(cx.naam), 3)
        c = c * (1 - 0.45 * vl[:, None]) + srgb("#3a3024")[None] * 0.3 * vl[:, None]
        c = c * (1 + 0.5 * rand[:, None])                          # rafelrand: verschoten draden
        c = c * (1 - gat[:, None]) + (huid * 0.35)[None] * gat[:, None]
        cx.kl[m] = c[m]
        cx.H[m] = (cx.H - 0.002 * gat + 0.0004 * rand)[m]
    BB.VERF[soort] = f


_wikkel("kledij", "hemd")
_wikkel("broek", "broek")


def zombie_gezicht(cx, c, h, huid, reg_h):
    """Ontbinding: donkere oogkassen, groenige vlekken, aders, wat plukjes haar op de kale schedel."""
    from bumpkin_basis import gauss, ruis
    kop = cx.sk.kop
    kk = kop.k
    P = cx.P
    q = (P - kop.C) / kk
    vlek = 0.5 + 0.5 * ruis(P, 30, 701, 3)
    groen = srgb("#55604a")
    c[:] = c * (1 - 0.35 * vlek[:, None] * huid[:, None]) + groen[None] * 0.35 * vlek[:, None] * huid[:, None]
    for oog in kop.ogen:
        do = (P - oog) / kk
        kas = gauss(np.hypot(do[:, 0] / 1.25, (do[:, 2] + 0.002) / 0.95), 0.016) * huid
        c[:] = c * (1 - 0.3 * kas[:, None]) + srgb("#2a2a22")[None] * 0.15 * kas[:, None]
    # wangen en slapen ingevallen: donkerder
    for sx in (1, -1):
        wang = gauss(np.hypot(q[:, 0] - sx * 0.055, q[:, 2] + 0.035), 0.02) * (q[:, 1] < -0.04) * huid
        c[:] = c * (1 - 0.12 * wang[:, None])
    # aders op de schedel
    ader = gladstap(0.03, 0.0, np.abs(ruis(P, 55, 702, 2))) * gladstap(0.0, 0.05, q[:, 2]) * huid
    c[:] = c * (1 - 0.18 * ader[:, None]) + srgb("#4a4a5a")[None] * 0.1 * ader[:, None]
    # plukjes haar: donkere strepen boven de oren en achter
    plukken = (ruis(P * np.array([1, 1, 0.15]), 260, 703, 1) > 0.55) & (q[:, 2] > 0.02) & (np.abs(q[:, 0]) > 0.05) & huid
    c[plukken] = c[plukken] * 0.45 + srgb("#3a3428") * 0.3
    h[plukken] += 0.0003 * kk


KOP["gezicht"]["extra"] = zombie_gezicht

_vf_lijf = BB.VERF["lijf"]


def vf_zombie_lijf(cx):
    _vf_lijf(cx)
    from bumpkin_basis import ruis
    m = cx.Dm & np.isin(cx.reg, (2, 4, 7, 5))
    vlek = 0.5 + 0.5 * ruis(cx.P, 25, 711, 3)
    c = cx.kl.copy()
    c = c * (1 - 0.3 * vlek[:, None]) + srgb("#4a5440")[None] * 0.3 * vlek[:, None]
    voet = cx.P[:, 2] < 0.12 * cx.s
    c[voet] = c[voet] * 0.8 + srgb("#3a3024") * 0.2                   # vuile voeten
    cx.kl[m] = c[m]


BB.VERF["lijf"] = vf_zombie_lijf
_slijtage = BB.VERF["_slijtage"]


def slijtage_zombie(cx):
    """Na de gewone sleet: dode huid is dof (anders glimt de donkere huid in de zon grijswit), stof nog doffer."""
    _slijtage(cx)
    huid = cx.D["lijf"] & (cx.reg != 3)
    cx.ruw[huid] = np.clip(0.86 + 0.06 * cx.r_fijn[huid], 0.75, 0.95)
    for nm in ("hemd", "broek"):
        cx.ruw[cx.D[nm]] = 0.97


BB.VERF["_slijtage"] = slijtage_zombie


# --- extra's na de bake: rig-props weg, gloeioog, nekstomp ------------------------------------------
def emissie_mat(naam, kleur, sterkte):
    m = bpy.data.materials.new(naam)
    m.use_nodes = True
    bs = m.node_tree.nodes["Principled BSDF"]
    bs.inputs["Base Color"].default_value = (*kleur, 1)
    bs.inputs["Emission Color"].default_value = (*kleur, 1)
    bs.inputs["Emission Strength"].default_value = sterkte
    bs.inputs["Roughness"].default_value = 0.3
    return m


def aan_bot(o, rig, bot):
    o.parent = rig
    o.parent_type = "BONE"
    o.parent_bone = bot
    bpy.context.view_layer.update()
    o.matrix_world = Matrix.Identity(4)


def extras(sk, rig, delen):
    for o in list(bpy.data.objects):
        if o.name.startswith("prop_"):
            bpy.data.objects.remove(o)
    kop = sk.kop
    kk = kop.k
    v = kop.vorm_v
    coll = bpy.context.scene.collection
    # gloeioog: rechteroog (-X), zoals het concept (van voren links in beeld)
    for sx, e, gd, up, out in kop.oogframes:
        if sx > 0:
            continue
        c = kop.C + kk * (np.array(e) + (v["oog_voor"] + 0.0015) * np.array(gd))
        B = Bouwer()
        r = kop.oog[0] * kk * 1.25
        rings = []
        for i in range(1, 8):
            t = math.pi * i / 8
            rings.append(ring(c + np.array(gd) * r * math.cos(t) * 0.7, out, up, r * math.sin(t), r * math.sin(t), 12))
        b0, _ = B.grid(np.array(rings), True)
        B.kap(b0, 12, c + np.array(gd) * r * 0.7)
        B.kap(b0 + 12 * 6, 12, c - np.array(gd) * r * 0.7)
        o = B.obj("zombie_oog", coll)
        o.data.materials.append(emissie_mat("zombie_oog", KLEUR["oog"], OOG_GLOED))
        aan_bot(o, rig, "Head")
    # nekstomp: donkere schijf boven in de nek (zichtbaar als de kop wegvliegt)
    Z = sk.z
    B = Bouwer()
    z0 = sk.kz - 0.005 * sk.s
    rings = [ring((0, 0.006 * sk.s, z0 - 0.004 * sk.s * i), (1, 0, 0), (0, -1, 0), (0.047 - 0.008 * i) * sk.s,
                  (0.047 - 0.008 * i) * sk.s, 14) for i in range(3)]
    b0, _ = B.grid(np.array(rings), True)
    B.kap(b0 + 14 * 2, 14, (0, 0.006 * sk.s, z0 - 0.012 * sk.s))
    o = B.obj("zombie_stomp", coll)
    m = bpy.data.materials.new("zombie_stomp")
    m.use_nodes = True
    bs = m.node_tree.nodes["Principled BSDF"]
    bs.inputs["Base Color"].default_value = (*srgb("#3a1a14"), 1)
    bs.inputs["Roughness"].default_value = 0.5
    o.data.materials.append(m)
    aan_bot(o, rig, "Neck")
    del Z


# --- clips ---------------------------------------------------------------------------------------------
FPS = R.FPS
STRIKE_AT = 0.42                                     # sim/wolf.gd Wolf.STRIKE_AT


def arm(sx, u, f):
    """Richtingssleutel (LA/RA) voor zijde sx (+1 links): u = bovenarm, f = onderarm (armatuurruimte, -Y = voor)."""
    u = (sx * u[0], u[1], u[2])
    f = (sx * f[0], f[1], f[2])
    return R.RA(u, f)


def gebogen(extra=None):
    """Basishouding: rug krom, nek naar voren, kop omhoog gekanteld (kijkt vooruit) en scheef."""
    p = {"Hips": (6, 0, 0), "Spine": (6, 0, 0), "Spine1": (8, 0, 0), "Spine2": (8, 0, 2), "Neck": (14, 0, 0),
         "Head": (-24, 6, 10), "LeftShoulder": (6, 0, 0), "RightShoulder": (8, 0, 0),
         "LeftHandFist": (25, 0, 0), "RightHandFist": (30, 0, 0)}
    p.update(extra or {})
    return p


def clip_idle(M):
    N = 72
    sl = M.sl
    keys = {}
    for f, zij, kn in ((0, 1, 0.0), (18, 0, 1.0), (36, -1, 0.0), (54, 0, 1.0)):
        keys[f] = gebogen({
            "T": (0.018 * zij * sl, 0.0, (-0.03 - 0.008 * kn) * sl), "Hips": (6, 2 * zij, -3 * zij),
            "Spine1": (8, 0, 1.5 * zij), "Neck": (14 + 3 * kn, 0, 0), "Head": (-24 + 6 * kn, 6 - 4 * zij, 10 + 6 * zij),
            "LA": arm(1, (0.25, -0.35, -0.9), (0.05, -0.55, -0.83)),
            "RA": arm(-1, (0.2, -0.5 - 0.05 * zij, -0.84), (0.0, -0.8, -0.6)),
        })
    k = R.sleutels_naar_reeksen(keys, N, True, M)
    return N, True, k, {"snelheid_mps": 0.0}, None


def schuifel(M, N, S, A, lift_l, lift_r, lean, armhoog, zwaai, sway, roll, schok):
    """Gemeenschappelijke loop: voeten via voet_pad, armen vooruit (richting), romp krom; rechts sleept."""
    sl = M.sl
    A = B_ = A * sl
    v = (A + B_) * FPS / S
    keys = {}
    for f in range(0, N, N // 4):
        fase = f / N
        w = math.sin(2 * math.pi * fase)
        keys[f] = gebogen({
            "Spine": (6 + lean * 0.4, 3 * w, 0), "Spine1": (8 + lean * 0.4, 3 * w, -2 * w),
            "Spine2": (8, 2 * w, 2), "Neck": (12, -2 * w, 0), "Head": (-26 - lean * 0.6, -4 * w, 10 - 6 * w),
            "LA": arm(1, (0.22, -0.92 + 0.05 * w * zwaai, armhoog - 0.1 * w * zwaai), (0.08, -0.97, 0.05 + 0.1 * w)),
            "RA": arm(-1, (0.2, -0.9 - 0.05 * w * zwaai, armhoog - 0.15 + 0.1 * w * zwaai), (0.05, -0.95, -0.1 - 0.1 * w)),
        })
    base = R.sleutels_naar_reeksen(keys, N, True, M)
    hp = R.loop_hips(M, N, S, N // 2, sl, -0.06 - schok, -0.02, 1.5, sway, roll, 6.0, 0.0)
    base.update(hp)
    for f in range(N + 1):                                 # slepend rechterbeen: heup zakt in de rechterstand
        u = 2 * math.pi * (f - N // 2 - S / 2) / N
        base[("T", "z")][f] -= schok * sl * max(0.0, math.cos(u)) * 0.8
    base[("Hips", "x")] = [lean] * (N + 1)
    for nm, contact, xs, ys, lift, pp in (("LF", 0, M.hx + 0.03 * sl, 10.0, lift_l, R.pitch_lopen),
                                          ("RF", N // 2, -(M.hx + 0.035 * sl), -16.0, lift_r,
                                           lambda t, stand: 0.35 * R.pitch_lopen(t, stand) - (6 if not stand else 0))):
        pad = [R.voet_pad(M, f, contact, N, S, A, B_, lift * sl, 0.7, xs, ys, pp) for f in range(N + 1)]
        for i in range(5):
            base[(nm, i)] = [p[i] for p in pad]
    return base, v


def clip_lopen(M):
    N, S = 36, 22
    k, v = schuifel(M, N, S, 0.17, 0.11, 0.035, 12.0, 0.05, 1.0, 0.035, 6.0, 0.02)
    return N, True, k, {"snelheid_mps": v}, None


def clip_rennen(M):
    N, S = 24, 13
    k, v = schuifel(M, N, S, 0.28, 0.16, 0.06, 20.0, 0.18, 1.6, 0.045, 8.0, 0.03)
    return N, True, k, {"snelheid_mps": v}, None


KOP_VLUCHT = 1.15        # m: zo ver vliegt de kop naar voren (sim: bereik 0,9 tegel = tot 1,8 m)


def clip_bijten(M):
    """zombatta: reikt met beide armen, de kop schiet naar het doel (inslag op STRIKE_AT) en keert terug."""
    N = 29
    imp = round(STRIKE_AT * N)
    sl = M.sl
    vooruit = {"LA": arm(1, (0.18, -0.95, 0.12), (0.05, -0.99, 0.05)),
               "RA": arm(-1, (0.18, -0.95, 0.12), (0.05, -0.99, 0.05))}
    keys = {
        0: gebogen({"T": (0, 0, -0.03 * sl), "LA": arm(1, (0.25, -0.6, -0.75), (0.08, -0.85, -0.5)),
                    "RA": arm(-1, (0.22, -0.6, -0.75), (0.05, -0.85, -0.5))}),
        7: gebogen({"T": (0, 0.03 * sl, -0.035 * sl), "Spine": (0, 0, 0), "Spine1": (-2, 0, 0), "Spine2": (-4, 0, 0),
                    "Head": (-24, 0, 4), "LA": arm(1, (0.5, -0.45, 0.55), (-0.55, -0.35, 0.45)),
                    "RA": arm(-1, (0.5, -0.45, 0.55), (-0.55, -0.35, 0.45))}),
        imp: gebogen(dict(vooruit, T=(0, -0.07 * sl, -0.06 * sl), Spine=(12, 0, 0), Spine1=(12, 0, 0),
                          Spine2=(10, 0, 0), Neck=(18, 0, 0), Head=(-10, 0, 0))),
        imp + 5: gebogen(dict(vooruit, T=(0, -0.05 * sl, -0.05 * sl), Spine=(10, 0, 0), Spine1=(10, 0, 0))),
        22: gebogen({"T": (0, 0, -0.035 * sl), "LA": arm(1, (0.45, -0.55, 0.45), (-0.5, -0.4, 0.45)),
                     "RA": arm(-1, (0.45, -0.55, 0.45), (-0.5, -0.4, 0.45))}),
        N: gebogen({"T": (0, 0, -0.03 * sl), "LA": arm(1, (0.25, -0.6, -0.75), (0.08, -0.85, -0.5)),
                    "RA": arm(-1, (0.22, -0.6, -0.75), (0.05, -0.85, -0.5))}),
    }
    k = R.sleutels_naar_reeksen(keys, N, False, M)
    return N, False, k, {"snelheid_mps": 0.0}, {"impact_s": imp / FPS}


def kop_vlucht(rig, N):
    """Locatiesleutels op bot Head voor `bijten` (lokaal: +Y langs het bot = omhoog, +Z = voor)."""
    act = bpy.data.actions["bijten"]
    ad = rig.animation_data_create()
    ad.action = act
    if getattr(ad, "action_slot", None) is None and len(getattr(act, "slots", [])):
        ad.action_slot = act.slots[0]
    pb = rig.pose.bones["Head"]
    sc = bpy.context.scene
    imp = STRIKE_AT * N
    los, terug = imp - 3.0, 22.0
    for f in range(N + 1):
        if f <= los or f >= terug:
            u, boog = 0.0, 0.0
        elif f <= imp:
            t = (f - los) / (imp - los)
            u = 1 - (1 - t) ** 2                             # snel weg, remt bij de inslag
            boog = math.sin(math.pi * t) * 0.10
        else:
            t = (f - imp) / (terug - imp)
            u = 1 - t * t * (3 - 2 * t)
            boog = math.sin(math.pi * t) * 0.25                # hoger terug
        pb.location = (0, 0, 0)
        sc.frame_set(f)
        pb.location = (0, 0, 0)
        bpy.context.view_layer.update()
        M0 = pb.matrix.copy()                                  # armatuurruimte, met de pose van dit frame
        # doel in armatuurruimte: recht naar voren (-Y) op ongeveer dezelfde hoogte (kop van het slachtoffer)
        delta = Vector((0.0, -KOP_VLUCHT * u, -0.05 * u + boog))
        M = Matrix.Translation(delta) @ M0
        L = rig.convert_space(pose_bone=pb, matrix=M, from_space="POSE", to_space="LOCAL")
        pb.location = L.to_translation()
        pb.keyframe_insert("location", frame=f)
    ad.action = None


def clip_dood(M):
    """Wankelt achteruit, knieen knikken, valt voorover op de grond (zombdead)."""
    N = 24
    sl = M.sl
    hx = M.hx
    st_l = (hx + 0.02 * sl, 0.0, 0.0, 0.0, 10.0)
    st_r = (-(hx + 0.02 * sl), 0.0, 0.0, 0.0, -10.0)
    hang = {"LA": arm(1, (0.4, -0.3, -0.85), (0.3, -0.5, -0.8)), "RA": arm(-1, (0.4, -0.3, -0.85), (0.3, -0.5, -0.8))}
    keys = {
        0: gebogen(dict(hang, T=(0, 0, -0.03 * sl), LF=st_l, RF=st_r)),
        5: gebogen({"T": (0, 0.05 * sl, -0.03 * sl), "Spine": (-6, 0, 0), "Spine1": (-6, 0, 0), "Spine2": (-4, 0, 0),
                    "Head": (-30, 10, 14), "LF": st_l, "RF": st_r,
                    "LA": arm(1, (0.75, -0.2, 0.35), (0.6, -0.5, 0.5)), "RA": arm(-1, (0.75, 0.1, 0.3), (0.6, 0.2, 0.6))}),
        11: gebogen({"T": (0, -0.04 * sl, -0.30 * sl), "Hips": (30, 0, 6), "Spine": (14, 0, 0), "Spine1": (12, 0, 0),
                     "Head": (10, 20, 10), "LF": st_l, "RF": (st_r[0], 0.04 * sl, 0, 0, -10),
                     "LA": arm(1, (0.4, -0.6, -0.6), (0.3, -0.8, -0.4)), "RA": arm(-1, (0.5, -0.4, -0.7), (0.4, -0.6, -0.6))}),
        15: gebogen({"T": (0, -0.30 * sl, -0.47 * sl), "Hips": (62, 0, 8), "Spine": (14, 0, 0), "Spine1": (10, 0, 0),
                     "Head": (0, 40, 10), "LF": (st_l[0], 0.02 * sl, 0.02 * sl, -30, 10),
                     "RF": (st_r[0], 0.06 * sl, 0.02 * sl, -35, -10),
                     "LA": arm(1, (0.5, -0.8, -0.3), (0.4, -0.9, -0.1)), "RA": arm(-1, (0.6, -0.7, -0.3), (0.5, -0.8, -0.2))}),
        19: {"T": (0, -0.62 * sl, -0.58 * sl), "Hips": (88, 0, 6), "Spine": (4, 0, 0), "Spine1": (2, 0, 0),
             "Spine2": (0, 0, 0), "Neck": (-10, 0, 0), "Head": (-20, 70, 0),
             "LF": (st_l[0] + 0.03 * sl, 0.05 * sl, 0.05 * sl, -70, 14), "RF": (st_r[0] - 0.02 * sl, 0.08 * sl, 0.05 * sl, -75, -12),
             "LA": arm(1, (0.75, -0.6, 0.0), (0.3, -0.95, 0.0)), "RA": arm(-1, (0.85, -0.45, 0.0), (0.2, -0.95, 0.0)),
             "LeftHandFist": (40, 0, 0), "RightHandFist": (50, 0, 0)},
        N: {"T": (0, -0.63 * sl, -0.60 * sl), "Hips": (90, 0, 6), "Spine": (2, 0, 0), "Spine1": (0, 0, 0),
            "Spine2": (0, 0, 0), "Neck": (-12, 0, 0), "Head": (-22, 74, 0),
            "LF": (st_l[0] + 0.03 * sl, 0.05 * sl, 0.04 * sl, -72, 14), "RF": (st_r[0] - 0.02 * sl, 0.08 * sl, 0.04 * sl, -77, -12),
            "LA": arm(1, (0.75, -0.6, -0.02), (0.3, -0.95, -0.02)), "RA": arm(-1, (0.85, -0.45, -0.02), (0.2, -0.95, -0.02)),
            "LeftHandFist": (45, 0, 0), "RightHandFist": (55, 0, 0)},
    }
    k = R.sleutels_naar_reeksen(keys, N, False, M)
    return N, False, k, {"snelheid_mps": 0.0}, {"impact_s": 19 / FPS}


R.CLIPS = [("idle", clip_idle), ("lopen", clip_lopen), ("rennen", clip_rennen), ("bijten", clip_bijten),
           ("dood", clip_dood)]
_bouw_animaties = R.bouw_animaties


def bouw_animaties_zombie(rig, alleen=None):
    info = _bouw_animaties(rig, alleen)
    kop_vlucht(rig, round(info["bijten"]["duur_s"] * FPS))
    # de andere clips zetten de kop expliciet terug (Godot laat een spoor dat ontbreekt op de oude waarde staan)
    for naam, d in info.items():
        if naam == "bijten":
            continue
        ad = rig.animation_data_create()
        ad.action = bpy.data.actions[naam]
        if getattr(ad, "action_slot", None) is None and len(getattr(ad.action, "slots", [])):
            ad.action_slot = ad.action.slots[0]
        pb = rig.pose.bones["Head"]
        for f in (0, round(d["duur_s"] * FPS)):
            pb.location = (0, 0, 0)
            pb.keyframe_insert("location", frame=f)
        ad.action = None
    info["bijten"]["kop_vlucht_m"] = KOP_VLUCHT
    json.dump(info, open(os.path.join(HERE, "zombie_anim.json"), "w"), indent=2)
    BB.log("anim", json.dumps(info))
    return info


R.bouw_animaties = bouw_animaties_zombie


# --- previews ------------------------------------------------------------------------------------------
def preview(sc, rig):
    tmp = bpy.app.tempdir
    H = rig.get("hoogte", 1.42)

    def zet(act, f):
        ad = rig.animation_data_create()
        ad.action = bpy.data.actions[act] if act else None
        if act and getattr(ad, "action_slot", None) is None and len(getattr(ad.action, "slots", [])):
            ad.action_slot = ad.action.slots[0]
        sc.frame_set(f)

    panelen = []
    for yaw in (270, 300, 0, 90):
        zet("idle", 0)
        BB.studio(sc, 420, 1.0, 1.7, doel=(0, 0, 0.74 * H / 1.42), yaw=yaw, pitch=8)
        panelen.append(BB.bijsnijden(BB.render_np(sc, os.path.join(tmp, f"a{yaw}.png"))))
    BB.schrijf(BB.plak(panelen, bg=(0.82, 0.82, 0.8)), os.path.join(BB.PREV, "zombie_aanzichten.png"))
    rijen = []
    for act, frames, breed in (("idle", (0, 18, 36, 54), 1.2), ("lopen", (0, 9, 18, 27), 1.3),
                               ("rennen", (0, 6, 12, 18), 1.4), ("bijten", (0, 7, 10, 12, 17, 22), 2.6),
                               ("dood", (0, 5, 11, 15, 19, 24), 2.0)):
        pan = []
        for f in frames:
            zet(act, f)
            BB.studio(sc, 200, breed, 1.8, doel=(0, -0.35 if act in ("bijten", "dood") else 0, 0.75), yaw=300, pitch=12)
            pan.append(BB.bijsnijden(BB.render_np(sc, os.path.join(tmp, f"c_{act}_{f}.png"))))
        rijen.append(BB.plak(pan, bg=(0.82, 0.82, 0.8)))
    BB.schrijf(BB.onder(*rijen, bg=(0.82, 0.82, 0.8)), os.path.join(BB.PREV, "zombie_clips.png"))
    zet(None, 0)


ZOMBIE = BB.Personage(
    "zombie", MAAT, DELEN, SOORT, TINTBAAR, VAST, TEXEL, KLEUR, bouw, texel_regio=TEXEL_REGIO,
    bak_ext={"hemd": (0.006, 0.02), "broek": (0.005, 0.016), "lijf": (0.008, 0.025)},
    kleurbak=(), sprites=("zombie", "zombie"), props=extras,
    extra={"weefsel": ("hemd", "broek"),
           "vlak": {"hemd": ["hemd"] * 5, "broek": ["broek", "broek"], "lijf": ["huid"] * 8}},
)

if __name__ == "__main__":
    rig, sk, delen = BB.bouw_personage(ZOMBIE)
    if "preview" in BB.OPTS:
        preview(bpy.context.scene, rig)
