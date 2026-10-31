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
Extra's (niet geskind, aan een bot): `zombie_oog` (gloeibol, emissief groen, rechteroog) en `zombie_stomp` (nekstomp).

v2 (2026-10-31, gebruiker: "meer gedetailleerd zoals in Gemini"): schedelgezicht (schedel_extra bovenop
BD.gezicht_vorm: oogkassen, jukbeen, holle wangen, neusgat, tandenrij; verf in zombie_gezicht), deel `pluk` (dunne
haarslierten, star aan Head), lijf met romp en dijen onder de kleren, kuiten en tenen. Hemd en broek knippen hun gaten
en repen uit met alfa (franje: repen langs de open randen; mat_hemd/mat_broek alphaMode MASK, dubbelzijdig).
`preview uit=<map>`: losse panelen (aanzicht_<yaw>, kop_voor, kop_34, voeten, dood_zij) voor de vergelijking.
In het spel dempt spel.json wezen_model.zombie.albedo de kleuren (de middagzon maakt ze anders bijna wit)."""
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
from bumpkin_basis import Bouwer, gauss, gladstap, keten, keten_param, overgang, ring, srgb, vertex_regio  # noqa: E402

MAAT = {"hoogte": 1.42, "kop": 0.218, "schouder": 0.30, "been": 0.47}
DELEN = ["lijf", "hemd", "broek", "pluk"]
SOORT = {"lijf": "lijf", "hemd": "kledij", "broek": "broek", "pluk": "pluk"}
TINTBAAR = {"lijf": "huid", "hemd": "hemd", "broek": "broek"}
VAST = {"lijf": (3,)}
TEXEL = {"lijf": 1.9, "hemd": 1.0, "broek": 1.0, "pluk": 1.0}
TEXEL_REGIO = {("lijf", 2): 1.3 / 1.9, ("lijf", 4): 1.3 / 1.9, ("lijf", 5): 0.8 / 1.9, ("lijf", 7): 0.9 / 1.9}

# v2 (2026-10-31, "meer gedetailleerd zoals in Gemini"): kleuren gemeten op concept/img/zombie.jpg (huid olijfgrijs,
# hemd koel donkerbruin, broek warmer roodbruin), gaten echt (alfa-knip), plukjes haar, schedelgezicht.
KLEUR = {
    "huid": srgb("#62655b"), "hemd": srgb("#4a3c2c"), "broek": srgb("#553f2c"), "snor": srgb("#3a3a30"),
    "gat": srgb("#2a2620"), "oog": srgb("#3cff1e"), "haar": srgb("#a29e90"),
}
OOG_GLOED = 8.0                      # emissiesterkte van het groene oog (glTF KHR_materials_emissive_strength)
OOGKAS = 0.0105                      # extra diepte van de oogkassen (kopmaten); oogbol en leden schuiven even ver mee

# Kop: schedelgezicht. Smalle schedel, diepe oogkassen (oogbol ver naar achter), harde jukbeenderen met holle
# wangen eronder, slapen ingevallen, neus weggerot tot een neusgat, lippen weg: twee rijen tanden (vorm + verf).
KOP = dict(
    schedel=(0.084, 0.108, 0.114, 0.112), kaak=(-0.12, 0.42, 0.24), ogen_ph=0.40, ogen_z=1.115, mond_z=1.036,
    neus=(0, -0.1, -0.034),
    neusprof=((0.03, 0.007, 0.006, 0.006), (0.012, 0.008, 0.008, 0.0), (-0.006, 0.01, 0.01, -0.002),
              (-0.02, 0.01, 0.009, -0.002), (-0.03, 0.008, 0.006, 0.0)),
    oog=(0.0118, 0.0006, 0.0052),
    haar_c=(0, 0.015, 1.15), haar_r=(0.11, 0.115, 0.12, 0.13, 0.12), klont=(0.0, 0.0),
    gezicht=dict(stoppels=False, mond="lach", lach=-0.002, mondbreed=0.027, spleet=0.002, open=0.0, onderlip=0.0,
                 bovenlip=0.0, lip="#3a3a30", iris="#c8ccb4", wang=0.0, neusrood=0.0, rood="#5a6a4a", rimpel=1.2,
                 voorhoofd=(0.036, 0.048, 0.06), kraai=(-0.3, 0.1, 0.45), wal=0.0, wimperkleur="#1e1e18",
                 lidtint="#2e2e26", lidkleur="#3a3b32", lid=0.002, schijf_lid=-0.001, oog_open=(0.0112, 0.0062),
                 brauw=(0.021, 0.006, 0.0), tand="#c8b88a", tris=2200,
                 vorm=dict(neus_h=0.004, neus_r=0.006, neus_breed=0.006, neus_vleugel=0.0015, neus_brug=0.0015,
                           richel=0.0085, oogkas=0.008, oog_diep=0.007, oog_voor=-0.0016 - OOGKAS, wal=0.0,
                           lidkap=0.0, lid_dik=0.0012, lidplooi=0.0, brauw_bult=0.0,
                           wang_hol=0.0, jukbeen=0.0, slaap=0.009, mond_in=0.0, kin=0.008, kin_z=0.036,
                           kin_breed=0.014, lip_b=0.0, lip_o=0.0, lip_rand=0.0, spleet_d=0.0, snuit=0.0055,
                           kaak_voor=0.006, nlf=(0.0, 0.0), rimpels=0.0005, kaakhoek=0.007, asym=0.0016,
                           mond_scheef=0.0015, brauw_binnen=(0.001, 0.0), seed=31)),
)

# tanden (kopmaten t.o.v. de mond): x-midden, halve breedte, lengte; boven en onder dezelfde rij
TANDEN = [(-0.0225, 0.0027, 0.0075), (-0.0172, 0.0027, 0.0090), (-0.0117, 0.0028, 0.0104), (-0.0059, 0.0029, 0.0116),
          (0.0, 0.0029, 0.0120), (0.0059, 0.0029, 0.0114), (0.0117, 0.0028, 0.0106), (0.0172, 0.0027, 0.0088),
          (0.0225, 0.0027, 0.0074)]


def schedel_extra(kop, Q):
    """Schedelgezicht bovenop BD.gezicht_vorm (kopmaten): oogkassen, jukbeen, holle wangen, neusgat, tanden.
    Geeft (verschuiving, tandmasker, tandvoeg) per punt."""
    X, Z = Q[:, 0], Q[:, 2]
    E = [(o - kop.C) / kop.k for o in kop.ogen]
    M = (kop.mond - kop.C) / kop.k
    Nc = (kop.neus - kop.C) / kop.k
    h = np.zeros(len(Q))
    for fr in kop.oogframes:
        e = fr[1]
        sx = fr[0]
        # brede, diepe oogkas; binnen de ooggleuf doet gezicht_vorm het al (oog_voor is OOGKAS dieper, de oogbol ook)
        ex, ez, nz, zu, zl, u = BD.oog_lijnen(kop, kop.vorm_v, fr, Q)
        w = kop.oog[0]
        we = gladstap(1.12, 0.86, np.sqrt((ex / (1.35 * w)) ** 2 + (ez / (1.1 * w)) ** 2)) * gladstap(-0.03, -0.012, nz)
        h -= OOGKAS * np.exp(-((X - e[0] - sx * 0.002) / 0.025) ** 2 - ((Z - e[2] + 0.002) / 0.021) ** 2) * (1 - we)
        # harde rand van de oogkas boven (wenkbrauwboog) en opzij
        h += 0.004 * np.exp(-((X - e[0]) / 0.02) ** 2 - ((Z - e[2] - 0.023) / 0.006) ** 2)
        h += 0.0035 * np.exp(-((X - e[0] - sx * 0.027) / 0.006) ** 2 - ((Z - e[2] + 0.002) / 0.014) ** 2)
        # jukbeen: scherpe richel onder het oog naar het oor
        h += 0.0075 * np.exp(-((X - e[0] - sx * 0.018) / 0.021) ** 2 - ((Z - e[2] + 0.029) / 0.0065) ** 2)
        # holle wang eronder en ingevallen tussen kaak en jukbeen
        h -= 0.0135 * np.exp(-((X - sx * 0.047) / 0.017) ** 2 - ((Z - M[2] - 0.010) / 0.017) ** 2)
    # neusgat: omgekeerd hartje, diep
    zn = Nc[2] - 0.006
    h -= 0.0085 * np.exp(-(X / (0.0075 + 0.004 * np.clip((zn - Z) / 0.02, 0, 1))) ** 2 - ((Z - zn) / 0.011) ** 2)
    # tandenrij: tanden bol, voegen en de spleet ertussen diep; tandvlees eromheen ingezakt
    dz = Z - M[2]
    tand = np.zeros(len(Q))
    voeg = np.zeros(len(Q))
    for x0, hb, L in TANDEN:
        for rij in (1, -1):
            lz = (dz * rij - 0.0008) / L                               # 0 aan de spleet, 1 aan de punt (wortel)
            bx = (X - x0) / hb
            m = np.clip(1 - bx * bx, 0, 1) ** 0.6 * gladstap(-0.05, 0.08, lz) * gladstap(1.08, 0.86, lz)
            tand = np.maximum(tand, m)
    voeg = gladstap(0.02, 0.0, tand) * gladstap(0.0275, 0.0215, np.abs(X)) * gladstap(0.0135, 0.011, np.abs(dz))
    rijen = gladstap(0.028, 0.0235, np.abs(X)) * gladstap(0.0145, 0.011, np.abs(dz))
    h += 0.0016 * tand - 0.0022 * voeg - 0.002 * gauss(dz, 0.0009) * rijen
    h -= 0.003 * np.exp(-(X / 0.03) ** 2 - (dz / 0.02) ** 2) * (1 - rijen)          # tandvlees/lippen ingevallen
    return h, tand * rijen, voeg


_gv = BD.gezicht_vorm


def gezicht_vorm_zombie(kop):
    f = _gv(kop)
    k = kop.k
    C = kop.C

    def g(P):
        P = np.asarray(P, float)
        Q = (P - C) / k
        fm = gladstap(-0.0, -0.045, Q[:, 1])
        return f(P) + schedel_extra(kop, Q)[0] * k * fm

    g.neus = f.neus
    return g


BD.gezicht_vorm = gezicht_vorm_zombie

# Hemd tot op de dij, V-hals; mouwen worden na het bouwen afgescheurd boven de elleboog (rafelrand).
HEMD = [(0.985, 0.076, 0.068, 0.066, 0.022), (0.968, 0.098, 0.08, 0.076, 0.02), (0.948, 0.138, 0.096, 0.094, 0.014),
        (0.922, 0.164, 0.11, 0.106, 0.005), (0.88, 0.163, 0.114, 0.11, 0.0), (0.8, 0.157, 0.112, 0.108, 0.0),
        (0.72, 0.153, 0.11, 0.106, 0.0), (0.645, 0.158, 0.114, 0.11, 0.0), (0.57, 0.164, 0.119, 0.116, 0.0),
        (0.52, 0.168, 0.122, 0.12, 0.0)]


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
    """Magere kuiten en lange, benige blote voeten (regio 7): voet als loft hiel -> tenen, tenen als stompjes."""
    J = sk.J
    s = sk.s
    for k in ("Left", "Right"):                              # kuit: knie benig, kuitspier achter, smalle enkel
        pts = [J[k + "UpLeg"], J[k + "Leg"], J[k + "Foot"]]
        L1 = np.linalg.norm(pts[1] - pts[0])
        L2 = np.linalg.norm(pts[2] - pts[1])
        # (d langs Leg vanaf de knie in L2, straal zij, straal voor-achter, verschuiving naar achter)
        prof = [(0.08, 0.040, 0.042, 0.0), (0.2, 0.041, 0.046, 0.006), (0.34, 0.040, 0.047, 0.009),
                (0.5, 0.035, 0.041, 0.007), (0.66, 0.029, 0.033, 0.004), (0.8, 0.025, 0.027, 0.002),
                (0.92, 0.024, 0.026, 0.0), (1.0, 0.025, 0.028, 0.0), (1.12, 0.022, 0.024, -0.004)]
        fr = keten(pts, [L1 + L2 * p[0] for p in prof], zacht=0.04)
        rings = [ring(pos - f * o * s, sd, f, a * s, b * s, 12, 2.0) for (pos, t, f, sd), (_, a, b, o) in zip(fr, prof)]
        B.grid(np.array(rings), True, regio=7)
    for k, sx in (("Left", 1), ("Right", -1)):
        an = J[k + "Foot"]
        fwd = np.array([sx * math.sin(math.radians(8)), -math.cos(math.radians(8)), 0.0])
        side = np.array([-fwd[1], fwd[0], 0.0])
        # (y vooruit vanaf de enkel, halve breedte, hoogte) in m bij s = 1; de bal eindigt op -0.125, dan tenen
        prof = [(0.058, 0.013, 0.03), (0.05, 0.022, 0.056), (0.034, 0.026, 0.074), (0.012, 0.027, 0.078),
                (-0.02, 0.028, 0.06), (-0.055, 0.031, 0.04), (-0.09, 0.035, 0.028), (-0.115, 0.036, 0.022),
                (-0.128, 0.034, 0.018)]
        rings = []
        for y, w, ht in prof:
            c = np.array([an[0], an[1], 0.0]) + fwd * (-y) * s + np.array([0, 0, ht * 0.5 * s])
            rings.append(ring(c, side, (0, 0, 1), w * s, ht * 0.5 * s, 12, 2.6))
        b0, _ = B.grid(np.array(rings), True, regio=7)
        B.kap(b0, 12, np.array([an[0], an[1], 0.0]) + fwd * (-0.066) * s + np.array([0, 0, 0.016 * s]), regio=7)
        B.kap(b0 + 12 * (len(prof) - 1), 12, np.array([an[0], an[1], 0.0]) + fwd * 0.13 * s +
              np.array([0, 0, 0.009 * s]), regio=7)
        # vijf tenen: grote teen dik, de rest kleiner en korter, iets gekromd naar de grond
        for i, (o, L, r) in enumerate(((-0.022, 0.034, 0.0085), (-0.008, 0.03, 0.0062), (0.004, 0.027, 0.0057),
                                       (0.015, 0.023, 0.0052), (0.025, 0.019, 0.0048))):
            p0 = np.array([an[0], an[1], 0.0]) + fwd * 0.112 * s + side * (o * s * -sx) + np.array([0, 0, 0.011 * s])
            pad = [p0, p0 + fwd * L * 0.55 * s + np.array([0, 0, 0.002 * s]), p0 + fwd * L * s - np.array([0, 0, 0.004 * s])]
            BD.staart_buis(B, pad, [(0.0, r * s, r * s * 0.8), (0.55, r * 0.95 * s, r * 0.75 * s),
                                    (1.0, r * 0.8 * s, r * 0.6 * s)], n=6, regio=7, ref=(0, 0, 1))


def dijen(B, sk):
    """Magere dijen tot onder de knie (regio 7) onder de broek: door de gaten zie je huid, geen leegte."""
    J = sk.J
    s = sk.s
    for k in ("Left", "Right"):
        pts = [J[k + "UpLeg"], J[k + "Leg"], J[k + "Foot"]]
        L1 = np.linalg.norm(pts[1] - pts[0])
        prof = [(0.0, 0.062), (0.08 * s, 0.062), (0.2 * s, 0.056), (L1 - 0.05 * s, 0.047), (L1, 0.044),
                (L1 + 0.04 * s, 0.04)]
        fr = keten(pts, [p[0] for p in prof], zacht=0.05)
        rings = [ring(pos, sd, f, r * s, r * s * 1.05, 10, 2.0) for (pos, t, f, sd), (d, r) in zip(fr, prof)]
        B.grid(np.array(rings), True, regio=7)


def nek_borst(B, sk):
    """Nek plus mager bovenlijf (regio 5) tot in de broek: zichtbaar in de V-hals en door de gaten van het hemd."""
    s = sk.s
    Z = sk.z
    nk = [(0.56, 0.118, 0.084), (0.62, 0.124, 0.087), (0.70, 0.133, 0.09), (0.76, 0.14, 0.093),
          (0.80, 0.143, 0.095), (0.85, 0.14, 0.094), (0.905, 0.112, 0.082), (0.94, 0.098, 0.076),
          (0.975, 0.062, 0.056), (1.0, 0.042, 0.042), (1.03, 0.033, 0.035), (1.07, 0.032, 0.034)]
    rings = [ring((0, 0.006 * s, Z(z)), (1, 0, 0), (0, -1, 0), a * s, b * s, 16, 2.2, fase=-np.pi / 2) for z, a, b in nk]
    B.grid(np.array(rings), True, regio=5)


def extra_lijf(B, sk, kop):
    BD.bouw_oren(B, sk, kop, grootte=0.62, uitstaan=0.0, z0=1.10, ph=1.62)
    onderarmen(B, sk)
    voeten(B, sk)
    dijen(B, sk)


def bouw_plukken(sk, coll, naam="pluk", n=150):
    """Dunne, slierterige plukjes haar (eigen deel, star aan de kop): kruin, achterhoofd en boven de oren;
    het voorhoofd blijft kaal. Elk plukje een dun driehoekig buisje dat uitwaaiert en dan hangt."""
    kop = sk.kop
    kk = kop.k
    rng = np.random.default_rng(41)
    B = Bouwer()

    def boven_schedel(p, marge):
        d = p - kop.C
        r = np.linalg.norm(d)
        d = d / r
        th = math.acos(np.clip(d[2], -1, 1))
        ph = math.atan2(d[0], -d[1])
        q = kop.punt(th, ph)
        rq = np.linalg.norm(q - kop.C) + marge
        return kop.C + d * max(r, rq)

    gemaakt = 0
    while gemaakt < n:
        th = rng.uniform(0.05, 1.45)
        ph = rng.uniform(-np.pi, np.pi)
        if abs(ph) < 1.0 and th > 0.55 or abs(ph) < 0.6 and th > 0.35:
            continue                                                   # voorhoofd en slapen kaal
        if rng.random() < 0.35 and th < 0.5:
            continue                                                   # kruin dunner
        d = kop.richting(th, ph)
        root = kop.punt(th, ph) - d * 0.001 * kk
        L = rng.uniform(0.032, 0.07) * kk * (1.2 if abs(ph) > 2.0 else 1.0)

        def achter(d_):
            t_ = np.array([0, 1.0, -0.7]) - np.dot([0, 1.0, -0.7], d_) * d_     # naar achter/omlaag over de schedel
            return t_ / (np.linalg.norm(t_) + 1e-9)
        v = achter(d) + d * 0.55 + rng.normal(0, 0.3, 3)
        v /= np.linalg.norm(v)
        pts = [root]
        for j in range(4):
            dj = (pts[-1] - kop.C) / np.linalg.norm(pts[-1] - kop.C)
            v = v + (achter(dj) * 0.45 + np.array([0, 0, -0.3]) + rng.normal(0, 0.35, 3)) * 0.55
            v /= np.linalg.norm(v)
            p = boven_schedel(pts[-1] + v * L / 4, 0.0012 * kk * (1 + j * 0.8))
            pts.append(p)
        r0 = rng.uniform(0.0005, 0.0009) * kk
        prof = [(t, r0 * (1 - 0.7 * t), r0 * 0.7 * (1 - 0.7 * t)) for t in np.linspace(0, 1, 5)]
        ref = np.cross(pts[-1] - pts[0], d)
        if np.linalg.norm(ref) < 1e-6:
            ref = np.array([1.0, 0, 0])
        BD.staart_buis(B, pts, prof, n=3, regio=0, ref=tuple(ref / np.linalg.norm(ref)), kappen=False)
        gemaakt += 1
    return B.obj(naam, coll)


def bouw(sk, coll):
    sk.stof = {"hemd": dict(weef=0.0055, vlek=0.4, kraag=0.8, vuil=1.0, vuil_hoogte=0.3), "broek": dict(weef=0.0055, vlek=0.35, vuil=1.6)}
    sk.vuil = 2.2
    sk.handmaat = 1.22                                       # lange, benige handen, vingers half open
    sk.kromming = 0.85
    d = {}
    d["hemd"] = BD.bouw_kledij(sk, coll, "hemd", HEMD, mouw_dik=0.86, mouw_wijd=1.0)
    scheur_hemd(d["hemd"], sk)
    d["broek"] = bouw_broek_kort(sk, coll, "broek", dik=0.8)
    d["lijf"] = BD.bouw_lijf(sk, coll, kopvorm=KOP, nek=nek_borst, extra=extra_lijf)
    d["pluk"] = bouw_plukken(sk, coll)
    sk.zombie_delen = d
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


KLEINE_GATEN = {"hemd": 30, "broek": 18}
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


def randen(o, s, z_max=None, stap=0.0015, voornaad=None):
    """Open randen van een kledingstuk (zoom, mouw, pijp) als punten om de stap, met per punt de booglengte
    langs zijn lus en het lusnummer. z_max: lussen die hoger liggen (halsrand) tellen niet."""
    import bmesh
    bm = bmesh.new()
    bm.from_mesh(o.data)
    rand = [e for e in bm.edges if e.is_boundary]
    buren = {}
    for e in rand:
        for v in e.verts:
            buren.setdefault(v.index, []).append(e)
    gezien = set()
    pts, booglen, lus = [], [], []
    nl = 0
    for e0 in rand:
        if e0.index in gezien:
            continue
        keten_ = [e0.verts[0].co.copy()]
        v = e0.verts[1]
        gezien.add(e0.index)
        while True:
            keten_.append(v.co.copy())
            vol = [x for x in buren.get(v.index, []) if x.index not in gezien]
            if not vol:
                break
            e = vol[0]
            gezien.add(e.index)
            v = e.other_vert(v)
        K = np.array([tuple(c) for c in keten_])
        if z_max is not None and K[:, 2].mean() > z_max:
            continue
        L = np.concatenate([[0], np.cumsum(np.linalg.norm(np.diff(K, axis=0), axis=1))])
        t = np.arange(0, L[-1], stap)
        Pk = np.stack([np.interp(t, L, K[:, i]) for i in range(3)], 1)
        hou = np.ones(len(t), bool)
        if voornaad is not None:                                      # open hemd: de naad voor is geen zoom
            hou = ~((np.abs(Pk[:, 0]) < 0.065 * s) & (Pk[:, 1] < 0) & (Pk[:, 2] > voornaad))
        pts.append(Pk[hou])
        booglen.append(t[hou])
        lus.append(np.full(int(hou.sum()), nl))
        nl += 1
    bm.free()
    if not booglen:
        return np.zeros((0, 3)), np.zeros(0), np.zeros(0, int)
    return np.concatenate(pts), np.concatenate(booglen), np.concatenate(lus)


def _hash01(a, b, seed):
    x = (np.asarray(a, np.int64) * 73856093) ^ (np.asarray(b, np.int64) * 19349663) ^ (seed * 83492791)
    x = (x ^ (x >> 13)) * 1274126177
    return ((x ^ (x >> 16)) & 0xFFFF) / 65535.0


def franje(cx, o, z_max, seed, band=0.06, breed=0.012, voornaad=None):
    """Alfa 0/1 en een rafelmasker langs de open randen: repen van ongelijke lengte met scheuren ertussen
    en puntige, uitgerafelde uiteinden (concept: zoom, mouwen en pijpen hangen in slierten)."""
    from mathutils import kdtree
    from bumpkin_basis import ruis
    s = cx.s
    R, U, Lp = randen(o, s, z_max, voornaad=voornaad)
    m = cx.Dm
    alfa = np.ones(cx.n)
    if len(R) == 0:
        return alfa, np.zeros(cx.n)
    kd = kdtree.KDTree(len(R))
    for i, p in enumerate(R):
        kd.insert(p, i)
    kd.balance()
    idx = np.nonzero(m)[0]
    dist = np.full(cx.n, 9.0)
    near = np.zeros(cx.n, int)
    Pm = cx.P
    for i in idx:
        co, j, d = kd.find(Pm[i])
        dist[i] = d
        near[i] = j
    u = U[near] / (breed * s) + 0.35 * ruis(cx.P, 40, seed, 1)
    rep = np.floor(u).astype(np.int64)
    fr = u - rep
    lus = Lp[near]
    B = band * s
    r1 = _hash01(rep, lus, seed)
    r2 = _hash01(rep, lus, seed + 1)
    r3 = _hash01(rep, lus, seed + 2)
    eind = np.where(r1 < 0.55, r2 * 0.75 * B, 0.0)                  # deze reep is korter afgescheurd
    eind += 0.016 * s * np.abs(2 * fr - 1) ** 1.6                    # puntig uiteinde
    eind += 0.004 * s * ruis(cx.P, 300, seed + 3, 1)                  # rafelig
    spleet = (np.abs(fr - 0.5) > 0.5 - (0.06 + 0.08 * r3)) & (dist < B * (0.35 + 0.65 * r3))
    knip = m & (dist < B) & ((dist < eind) | spleet)
    alfa[knip] = 0.0
    return alfa, m * gladstap(B, 0.0, dist)


def _gatafstand(cx, plekken, seed):
    """Genormeerde afstand tot het dichtste gat (1 = op de rand); zelfde ruis en plekken als _gaten."""
    from bumpkin_basis import ruis
    P = cx.P
    dd_min = np.full(cx.n, 9.0)
    rng = np.random.default_rng(seed)
    nz = ruis(P, 160, seed, 2)
    for c, r in plekken:
        c = np.array(c) + rng.uniform(-0.01, 0.01, 3)
        dd = np.linalg.norm((P - c) * np.array([1.0, 1.0, 0.8]), axis=1) / r + 0.35 * nz
        dd_min = np.minimum(dd_min, dd)
    return dd_min


def _wikkel(soort, nm_gaten):
    orig = BB.VERF[soort]

    def f(cx):
        orig(cx)
        if cx.naam not in GATEN:
            return
        from bumpkin_basis import ruis
        m = cx.Dm
        s = cx.s
        h = s / 1.37 * 1.036
        plekken = [((c[0] * h, c[1] * h, c[2] * BB.C.MAAT["hoogte"] / 1.37), r * h * 1.15) for c, r in GATEN[cx.naam]]
        # plus kleine gaatjes verspreid over de stof (concept: tientallen, 1-3 cm, donker)
        rng = np.random.default_rng(70 + len(cx.naam))
        zl, zh = cx.sk.kledij_z.get(cx.naam, (0.0, 9.0)) if cx.naam == "hemd" else (0.12 * s, 0.6 * s)
        kand = np.nonzero(m & (cx.P[:, 2] > zl + 0.05 * s) & (cx.P[:, 2] < zh - 0.06 * s))[0]
        for i in rng.choice(kand, KLEINE_GATEN[cx.naam], replace=False):
            plekken.append((tuple(cx.P[i]), rng.uniform(0.007, 0.016) * s))
        gat, rand = _gaten(cx, plekken, 50 + len(cx.naam))
        o = cx.sk.zombie_delen[cx.naam]
        hemd = cx.naam == "hemd"
        alfa, raf = franje(cx, o, cx.sk.z(0.9) if hemd else None, 90 + len(cx.naam),
                           band=0.075 if not hemd else 0.06,
                           voornaad=cx.sk.kledij_z["hemd"][0] + 0.09 * s if hemd else None)
        c = cx.kl.copy()
        P = cx.P
        # vergane stof: grote vlekken, verkleuring (concept: gevlekt, lichter versleten, donker vuil in de plooien)
        vl = 0.5 + 0.5 * ruis(P, 9, 61 + len(cx.naam), 3)
        vf = 0.5 + 0.5 * ruis(P, 38, 63 + len(cx.naam), 2)
        c = c * (1 - 0.4 * vl[:, None]) + srgb("#3a3024")[None] * 0.28 * vl[:, None]
        c = c * (1 + 0.22 * (vf[:, None] - 0.5))
        vlekken = gladstap(0.5, 0.78, 0.5 + 0.5 * ruis(P, 6, 65 + len(cx.naam), 2))     # grote donkere vuilplekken
        c = c * (1 - 0.32 * vlekken)[:, None]
        streep = gladstap(0.6, 0.9, 0.5 + 0.5 * ruis(P * np.array([4.0, 4.0, 0.25]), 30, 66 + len(cx.naam), 1))
        c = c * (1 - 0.18 * streep)[:, None]                                            # verticale vuilstrepen
        sleet = gladstap(0.55, 0.85, 0.5 + 0.5 * ruis(P, 16, 64 + len(cx.naam), 2))
        c = c * (1 - 0.25 * sleet[:, None]) + srgb("#8a7558")[None] * 0.25 * sleet[:, None]
        # randen van de repen: verschoten draden, iets lichter, met donkere vuilrand erboven
        draad = 0.5 + 0.5 * np.sin(cx.U / 0.0016 * np.pi * 2) * np.sin(cx.V / 0.0019 * np.pi * 2)
        c = c * (1 + (0.28 * raf * draad - 0.18 * raf * (1 - raf)))[:, None]
        # gaten: echt open (alfa), rand gerafeld: lichte draden, daarbuiten verschroeid/vuil
        alfa = np.where(gat > 0.5, 0.0, alfa)
        rd = rand * (gat <= 0.5)
        c = c * (1 + 0.55 * rd * draad)[:, None]
        donker = gladstap(1.9, 1.0, _gatafstand(cx, plekken, 50 + len(cx.naam))) * (gat <= 0.5) * (1 - rd)
        c = c * (1 - 0.35 * donker)[:, None]
        cx.kl[m] = c[m]
        cx.H[m] = (cx.H + 0.0005 * rd * draad - 0.0004 * raf)[m]
        cx.alfa[m] = alfa[m]
    BB.VERF[soort] = f


_wikkel("kledij", "hemd")
_wikkel("broek", "broek")


def zombie_gezicht(cx, c, h, huid, reg_h):
    """Schedelgezicht in verf: zwarte oogkassen, neusgat, ontblote tanden met tandvlees, ingevallen wangen
    (donker) onder lichte jukbeenderen, aders en vlekken op de kale schedel."""
    from bumpkin_basis import gauss, ruis
    kop = cx.sk.kop
    kk = kop.k
    P = cx.P
    q = (P - kop.C) / kk
    X, Z = q[:, 0], q[:, 2]
    voor = q[:, 1] < -0.02
    hu = huid[:, None]
    vlek = 0.5 + 0.5 * ruis(P, 30, 701, 3)
    c[:] = c * (1 - 0.4 * vlek[:, None] * hu) + srgb("#3e4238")[None] * 0.4 * vlek[:, None] * hu
    groot = gladstap(0.45, 0.8, 0.5 + 0.5 * ruis(P, 14, 704, 2)) * huid
    c[:] = c * (1 - 0.22 * groot)[:, None]
    sch, tandm, voeg = schedel_extra(kop, q)
    # holtes donker, bulten licht (uit de schedelvorm zelf)
    diep = np.clip(-sch / 0.009, 0, 1) * voor * gladstap(-0.03, -0.06, q[:, 1]) * 0.7
    bol = np.clip(sch / 0.006, 0, 1) * voor
    c[:] = c * (1 - 0.55 * diep[:, None] * hu) + srgb("#22231c")[None] * 0.25 * diep[:, None] * hu
    c[:] = c * (1 + 0.22 * bol[:, None] * hu)
    for fr in kop.oogframes:
        e = fr[1]
        kas = np.exp(-((X - e[0]) / 0.022) ** 2 - ((Z - e[2] + 0.002) / 0.018) ** 2) * voor
        kas = np.clip(kas * 1.4, 0, 1)
        c[:] = c * (1 - 0.85 * kas[:, None] * hu) + srgb("#0c0c0a")[None] * 0.6 * kas[:, None] * hu
    # neusgat zwart
    Nc = (kop.neus - kop.C) / kk
    zn = Nc[2] - 0.006
    ng = np.exp(-(X / (0.006 + 0.0035 * np.clip((zn - Z) / 0.02, 0, 1))) ** 2 - ((Z - zn) / 0.0085) ** 2) * voor
    ng = gladstap(0.25, 0.6, ng)
    c[:] = c * (1 - 0.85 * ng[:, None] * hu) + srgb("#0e0c0a")[None] * 0.8 * ng[:, None] * hu
    # tanden: geelbruin, glazuur iets lichter aan de snijrand, voegen en de spleet zwart, tandvlees eromheen
    M = (kop.mond - kop.C) / kk
    dz = Z - M[2]
    rij = gladstap(0.028, 0.0235, np.abs(X)) * gladstap(0.0145, 0.011, np.abs(dz)) * voor
    tv = rij * (1 - tandm) * gladstap(0.0, 0.006, np.abs(dz))
    c[:] = c * (1 - tv[:, None] * hu) + srgb("#3a2a20")[None] * tv[:, None] * hu
    tk = srgb("#d2c49a")[None] * (0.85 + 0.25 * gladstap(0.008, 0.001, np.abs(dz)))[:, None]
    vl_t = 0.5 + 0.5 * ruis(P, 400, 705, 2)
    tk = tk * (0.82 + 0.25 * vl_t[:, None]) * np.array([1.0, 0.97, 0.88])
    t_ = (tandm * voor)[:, None] * hu
    c[:] = c * (1 - t_) + tk * t_
    zw = np.maximum(voeg * voor, gauss(dz, 0.0008) * rij)
    c[:] = c * (1 - 0.9 * zw[:, None] * hu)
    h += (0.0004 * tandm - 0.0005 * zw) * kk * huid
    cx.ruw[huid & (tandm > 0.5)] = 0.45
    # aders op de schedel en de slapen
    ader = gladstap(0.03, 0.0, np.abs(ruis(P, 55, 702, 2))) * gladstap(-0.01, 0.04, Z) * huid
    c[:] = c * (1 - 0.2 * ader[:, None]) + srgb("#45475a")[None] * 0.12 * ader[:, None]
    h -= 0.0002 * kk * ader
    # rimpelige, gebarsten huid: fijne donkere scheurtjes
    sc = gladstap(0.018, 0.0, np.abs(ruis(P, 140, 706, 2))) * huid
    c[:] = c * (1 - 0.18 * sc[:, None])
    h -= 0.00025 * kk * sc
    # rimpels over het hele hoofd: fijn net van groeven, horizontaal gerekt op voorhoofd en wangen
    rw = gladstap(0.06, 0.0, np.abs(ruis(P * np.array([1.0, 1.0, 2.6]), 260, 708, 2))) * huid
    rw2 = gladstap(0.05, 0.0, np.abs(ruis(P, 520, 709, 1))) * huid
    c[:] = c * (1 - (0.2 * rw + 0.1 * rw2)[:, None])
    h -= (0.0005 * rw + 0.00025 * rw2) * kk
    # haarwortels op het achterhoofd
    wortel = (ruis(P, 900, 707, 1) > 0.45) & (Z > 0.0) & huid & ~voor
    c[wortel] *= 0.75


KOP["gezicht"]["extra"] = zombie_gezicht

_vf_lijf = BB.VERF["lijf"]


def vf_zombie_lijf(cx):
    _vf_lijf(cx)
    from bumpkin_basis import gauss, ruis
    P, s, sk = cx.P, cx.s, cx.sk
    m = cx.Dm & np.isin(cx.reg, (2, 4, 7, 5))
    vlek = 0.5 + 0.5 * ruis(P, 25, 711, 3)
    c = cx.kl.copy()
    c = c * (1 - 0.4 * vlek[:, None]) + srgb("#3e4238")[None] * 0.4 * vlek[:, None]
    groot = gladstap(0.45, 0.8, 0.5 + 0.5 * ruis(P, 8, 714, 2))                     # grote donkere ontbindingsvlekken
    c = c * (1 - 0.25 * groot)[:, None]
    voet = P[:, 2] < 0.12 * s
    c[voet] = c[voet] * 0.78 + srgb("#3a3024") * 0.2                   # vuile voeten
    # ribben, sleutelbeenderen en borstbeen op de romp (V-hals en gaten)
    romp = cx.Dm & (cx.reg == 5)
    Z = sk.z
    rel = np.zeros(cx.n)
    ax = np.abs(P[:, 0])
    for i in range(7):
        zr = Z(0.885 - 0.045 * i)
        boog = zr - 0.03 * s * (ax / (0.14 * s)) ** 2 + 0.01 * s
        rel += gauss(P[:, 2] - boog, 0.0065 * s) * gladstap(0.012 * s, 0.03 * s, ax)
    rel += 1.2 * gauss(P[:, 2] - (Z(0.935) + 0.012 * s * (ax / (0.1 * s))), 0.005 * s) * \
        gladstap(0.012 * s, 0.025 * s, ax) * gladstap(0.13 * s, 0.1 * s, ax)          # sleutelbeenderen
    rel += 0.7 * gauss(P[:, 0], 0.008 * s) * gladstap(Z(0.94), Z(0.92), P[:, 2]) * gladstap(Z(0.72), Z(0.76), P[:, 2])
    rel *= romp
    tussen = np.clip(0.6 - rel, 0, 0.6) * (rel > 0.02)
    c = c * (1 + 0.25 * rel)[:, None] * (1 - 0.4 * tussen)[:, None]
    cx.H[romp] = (cx.H + 0.0014 * rel)[romp]
    # onder de kleren is het donker (de bake ziet het lijf zonder kleren): gaten lezen als schaduw met wat huid,
    # behalve in de V-hals; dijen idem boven de broekzoom
    vhals = gladstap(0.06 * s, 0.035 * s, np.abs(P[:, 0])) * gladstap(Z(0.80), Z(0.86), P[:, 2]) * (P[:, 1] < 0)
    onder = romp * gladstap(Z(0.93), Z(0.88), P[:, 2]) * (1 - vhals)
    dij = cx.Dm & (cx.reg == 7) & (P[:, 2] > 0.30 * s)
    c = c * (1 - 0.5 * np.maximum(onder, dij * gladstap(0.30 * s, 0.36 * s, P[:, 2])))[:, None]
    # pezen op handen en voeten: donkere groeven; ledematen niet warmer dan het hoofd (vf_lijf maakt handen warm)
    ld = cx.Dm & np.isin(cx.reg, (2, 4, 7))
    c[ld] = c[ld] * np.array([0.97, 1.04, 1.1])
    rw = gladstap(0.06, 0.0, np.abs(ruis(P * np.array([1.0, 1.0, 2.2]), 220, 713, 2))) * m
    c = c * (1 - 0.18 * rw)[:, None]
    cx.H[m] = (cx.H - 0.0004 * rw)[m]
    pees = gladstap(0.02, 0.0, np.abs(ruis(P * np.array([1, 1, 0.2]), 160, 712, 1))) * ld
    c = c * (1 - 0.15 * pees)[:, None]
    cx.H[ld] = (cx.H - 0.0003 * pees)[ld]
    cx.kl[m] = c[m]
    # het dode oog (links; rechts zit de gloeibol ervoor): troebel grijsgeel, geen glans, donkere rand
    kop = sk.kop
    for oog in kop.ogen:
        do = (P - oog) / kop.k
        sch = cx.Dm & (cx.reg == 3) & (np.linalg.norm(do, axis=1) < 0.025)
        ir = np.hypot(do[:, 0], do[:, 2] + 0.0012)
        cx.kl[sch] = srgb("#7e7c68") * (0.8 + 0.25 * gladstap(0.012, 0.0, ir[sch]))[:, None]
        cx.kl[sch & (ir < 0.006)] = srgb("#a8ab96")
        cx.kl[sch & (ir < 0.0022)] = srgb("#5a5c4c")
        cx.ruw[sch] = 0.55


BB.VERF["lijf"] = vf_zombie_lijf
_slijtage = BB.VERF["_slijtage"]


def slijtage_zombie(cx):
    """Na de gewone sleet: dode huid is dof (anders glimt de donkere huid in de zon grijswit), stof nog doffer;
    de tanden (ruwheid < 0,5 uit zombie_gezicht) houden hun glans."""
    _slijtage(cx)
    huid = cx.D["lijf"] & (cx.reg != 3)
    tand = huid & (cx.ruw < 0.5)
    r = np.clip(0.88 + 0.06 * cx.r_fijn, 0.8, 0.96)
    cx.ruw[huid & ~tand] = r[huid & ~tand]
    for nm in ("hemd", "broek"):
        cx.ruw[cx.D[nm]] = 0.97


BB.VERF["_slijtage"] = slijtage_zombie


# --- plukjes haar: eigen deel (soort pluk), star aan de kop -----------------------------------------
def gw_pluk(g):
    g.voeg("Head", np.ones(g.N))


def vf_pluk(cx):
    from bumpkin_basis import ruis
    m = cx.Dm
    v = 0.5 + 0.5 * ruis(cx.P, 300, 721, 2)
    c = KLEUR["haar"][None] * (0.6 + 0.6 * v[:, None])
    c = c * (0.85 + 0.15 * np.sin(cx.U / 0.0007))[:, None]
    cx.zet(m, c)
    cx.ruw[m] = 0.7
    cx.H[m] = 0.0


BB.GEWICHT["pluk"] = gw_pluk
BB.HOOG["pluk"] = (None, 1, True)
BB.VERF["pluk"] = vf_pluk


# --- alfa: hemd en broek knippen hun gaten en repen uit (glTF alphaMode MASK), dubbelzijdig ------------
_materialen = BB.materialen


def materialen_zombie(delen, kleur, normaal, orm):
    _materialen(delen, kleur, normaal, orm)
    if not getattr(BB.C, "HEEFT_ALFA", False):
        return
    for mn in ("mat_hemd", "mat_broek"):
        m = bpy.data.materials.get(mn)
        if m is None:
            continue
        nt = m.node_tree
        b = nt.nodes["Principled BSDF"]
        t = [n for n in nt.nodes if n.type == "TEX_IMAGE" and n.image == kleur][0]
        rd = nt.nodes.new("ShaderNodeMath")
        rd.operation = "ROUND"
        nt.links.new(t.outputs["Alpha"], rd.inputs[0])
        nt.links.new(rd.outputs[0], b.inputs["Alpha"])
        m.use_backface_culling = False


BB.materialen = materialen_zombie


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
        c = kop.C + kk * (np.array(e) + (v["oog_voor"] + 0.002) * np.array(gd))
        B = Bouwer()
        r = kop.oog[0] * kk * 1.3
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
    rings = [ring((0, 0.006 * sk.s, z0 - 0.004 * sk.s * i), (1, 0, 0), (0, -1, 0), (0.031 - 0.006 * i) * sk.s,
                  (0.032 - 0.006 * i) * sk.s, 14) for i in range(3)]
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
    """Basishouding: rug licht krom, nek naar voren, kop omhoog gekanteld (kijkt vooruit) en scheef.
    v2: minder krom (concept staat bijna rechtop, alleen kop en schouders naar voren)."""
    p = {"Hips": (4, 0, 0), "Spine": (3, 0, 0), "Spine1": (5, 0, 0), "Spine2": (5, 0, 2), "Neck": (12, 0, 0),
         "Head": (-22, 6, 10), "LeftShoulder": (6, 0, 0), "RightShoulder": (8, 0, 0),
         "LeftHandFist": (25, 0, 0), "RightHandFist": (30, 0, 0)}
    p.update(extra or {})
    return p


def clip_idle(M):
    N = 72
    sl = M.sl
    keys = {}
    for f, zij, kn in ((0, 1, 0.0), (18, 0, 1.0), (36, -1, 0.0), (54, 0, 1.0)):
        keys[f] = gebogen({
            "T": (0.018 * zij * sl, 0.0, (-0.016 - 0.008 * kn) * sl), "Hips": (3, 2 * zij, -3 * zij),
            "Spine1": (5, 0, 1.5 * zij), "Neck": (11 + 3 * kn, 0, 0), "Head": (-24 + 5 * kn, 6 - 4 * zij, 8 + 5 * zij),
            "LA": arm(1, (0.28, -0.25, -0.93), (0.1, -0.45, -0.89)),
            "RA": arm(-1, (0.24, -0.35 - 0.05 * zij, -0.9), (0.06, -0.6, -0.8)),
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


def lig(M, pitch, enkel):
    """Lift zodat de enkel op `enkel` m (x sl) ligt bij een voet die gestrekt achter het liggende lijf ligt
    (pitch < -90: wreef op de grond, zool omhoog); M.grond_z rekent alleen met zoolpunten."""
    return enkel * M.sl - M.grond_z(pitch)


_been_ik = R.been_ik


def been_ik_zombie(M, zijde, T, Dh, enkel, pitch, yaw, tenen):
    """Gestrekte voet (pitch < -90, dood) zonder tenen die 150 graden omkrullen (tenen = -pitch in de rig)."""
    return _been_ik(M, zijde, T, Dh, enkel, pitch, yaw, 0.0 if tenen > 90 else tenen)


R.been_ik = been_ik_zombie


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
             "LF": (st_l[0] + 0.03 * sl, 0.10 * sl, lig(M, -150, 0.07), -150, 14),
             "RF": (st_r[0] - 0.02 * sl, 0.12 * sl, lig(M, -155, 0.07), -155, -12),
             "LA": arm(1, (0.75, -0.6, 0.0), (0.3, -0.95, 0.0)), "RA": arm(-1, (0.85, -0.45, 0.0), (0.2, -0.95, 0.0)),
             "LeftHandFist": (40, 0, 0), "RightHandFist": (50, 0, 0)},
        N: {"T": (0, -0.63 * sl, -0.60 * sl), "Hips": (90, 0, 6), "Spine": (2, 0, 0), "Spine1": (0, 0, 0),
            "Spine2": (0, 0, 0), "Neck": (-12, 0, 0), "Head": (-22, 74, 0),
            "LF": (st_l[0] + 0.03 * sl, 0.10 * sl, lig(M, -160, 0.06), -160, 14),
            "RF": (st_r[0] - 0.02 * sl, 0.12 * sl, lig(M, -165, 0.06), -165, -12),
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
    """Aanzichten zoals het concept (voor, 3/4 naar rechts, zij, achter), kopjes van dichtbij, clipstrook.
    Met uit=<map> ook elk paneel los (voor de vergelijking met concept/img/zombie.jpg)."""
    tmp = bpy.app.tempdir
    H = rig.get("hoogte", 1.42)
    uit = BB.OPTS.get("uit")
    if uit:
        os.makedirs(uit, exist_ok=True)
    BG = (0.835, 0.835, 0.835)

    def zet(act, f):
        ad = rig.animation_data_create()
        ad.action = bpy.data.actions[act] if act else None
        if act and getattr(ad, "action_slot", None) is None and len(getattr(ad.action, "slots", [])):
            ad.action_slot = ad.action.slots[0]
        if not act:
            for pb in rig.pose.bones:
                pb.rotation_quaternion = (1, 0, 0, 0)
                pb.rotation_euler = (0, 0, 0)
                pb.location = (0, 0, 0)
        sc.frame_set(f)

    def los(a, naam):
        if uit:
            BB.schrijf(BB.plak([a], bg=BG, gat=0), os.path.join(uit, naam + ".png"))

    panelen = []
    for yaw in (270, 240, 0, 90):                     # het model draait, de camera en de zon staan vast (voor)
        zet("idle", 0)
        rig.rotation_euler = (0, 0, math.radians(270 - yaw))
        BB.studio(sc, 420, 1.0, 1.7, doel=(0, 0, 0.74 * H / 1.42), yaw=270, pitch=8)
        a = BB.bijsnijden(BB.render_np(sc, os.path.join(tmp, f"a{yaw}.png")))
        panelen.append(a)
        los(a, f"aanzicht_{yaw}")
    rig.rotation_euler = (0, 0, 0)
    BB.schrijf(BB.plak(panelen, bg=(0.82, 0.82, 0.8)), os.path.join(BB.PREV, "zombie_aanzichten.png"))
    zet(None, 0)
    bpy.context.view_layer.update()
    kop = rig.matrix_world @ rig.pose.bones["Head"].matrix @ Vector((0, 0.07, 0))
    for yaw, nm in ((270, "kop_voor"), (240, "kop_34")):
        BB.studio(sc, 2400, 0.3, 0.3, doel=tuple(kop), yaw=yaw, pitch=4)
        los(BB.render_np(sc, os.path.join(tmp, nm + ".png")), nm)
    BB.studio(sc, 1600, 0.5, 0.3, doel=(0, -0.03, 0.1), yaw=240, pitch=14)
    los(BB.render_np(sc, os.path.join(tmp, "voeten.png")), "voeten")
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
    zet("dood", 24)
    BB.studio(sc, 400, 1.8, 0.6, doel=(0, -0.4, 0.15), yaw=0, pitch=2)
    los(BB.bijsnijden(BB.render_np(sc, os.path.join(tmp, "dood_zij.png"))), "dood_zij")
    zet(None, 0)


ZOMBIE = BB.Personage(
    "zombie", MAAT, DELEN, SOORT, TINTBAAR, VAST, TEXEL, KLEUR, bouw, texel_regio=TEXEL_REGIO,
    bak_ext={"hemd": (0.006, 0.02), "broek": (0.005, 0.016), "lijf": (0.008, 0.025), "pluk": (0.0015, 0.004)},
    kleurbak=(), sprites=("zombie", "zombie"), props=extras,
    extra={"weefsel": ("hemd", "broek"),
           "vlak": {"hemd": ["hemd"] * 5, "broek": ["broek", "broek"], "lijf": ["huid"] * 8, "pluk": ["haar"]}},
)

if __name__ == "__main__":
    rig, sk, delen = BB.bouw_personage(ZOMBIE)
    if "preview" in BB.OPTS:
        preview(bpy.context.scene, rig)
