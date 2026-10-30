"""Wolf en donkere wolf, game-ready: mesh, skin, atlas, animaties -> wolf.glb + donkere_wolf.glb
(Blender 5.2 headless -> Godot 4).

Draaien:
  blender -b -P wolf.py -- [res=1024] [snel] [vergelijk] [poses] [geen_export] [tag=_r1]
- `snel`: weinig samples, grover rooster (silhouetrondes).
- `vergelijk`: preview/wolf_vergelijk_1x.png (sprites naast de render op 1x-pixelschaal, iso yaw 225) en
  preview/wolf_vergelijk_close.png (concept naast close-ups). Bevatten sprite/concept: NOOIT committen.
- `poses`: preview/wolf_poses.png (standen uit alle clips, iso + van opzij, grijs en donker): mag in git.
Doel: lokaal/concept/img/wolf.jpg (grijze wolf, ruige vacht, lichte keel/snuit/buik, zwarte neus, rode
ogen); de donkere wolf (sprites dw_*) is dezelfde wolf in zwart met een witte borst.

Uitvoer: armatuur `wolf_rig` (wolf_rig.py) met idle, lopen, rennen, bijten, dood; nodes
| node | inhoud                                                   | materiaal            |
| ---- | -------------------------------------------------------- | -------------------- |
| lijf | romp, nek, kop, oren, poten, staart (vacht in de textuur) | mat_lijf (atlas)     |
| ogen | twee oogbollen, star aan Head                            | mat_oog (rood, gloei)|
Atlas ingebakken in de glb (textures_wolf/: wolf_kleur.jpg, donkere_wolf_kleur.jpg, wolf_normaal.png,
wolf_orm.png). Beide glb's delen mesh, skin, normaal en ORM; alleen de kleur verschilt.

Bouw zoals de koe (koe.py; de SDF, surface nets, decimeren, UV, bakken en gewichtshulpjes komen daar
vandaan): primitieven langs het skelet, met een ruisrand (plukken) op nek, rug en staart; vacht = strengen
als hoogte langs een 3D-richting per streek. Kleur per texel: agouti-grijs met donker zadel en lichte
onderkant (wolf) of zwart met witte borst (donkere wolf).
"""
import json
import math
import os
import sys
import time

import bmesh
import bpy
import numpy as np
from mathutils import Matrix, Vector

HERE = os.path.dirname(os.path.abspath(__file__))
MOD = os.path.dirname(HERE)
sys.path.insert(0, HERE)
import wolf_rig as R  # noqa: E402
import dieren_basis as BM  # noqa: E402
import koe as KO  # noqa: E402  (SDF, oppervlak, decimeer, uv_atlas, bak_alles, bewaar, gewichten)

argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
OPTS = {a.split("=")[0]: (a.split("=", 1)[1] if "=" in a else "1") for a in argv}
SNEL = "snel" in OPTS
RES = int(OPTS.get("res", 1024))
TEX = os.path.join(HERE, "textures_wolf")
PREV = os.path.join(HERE, "preview")
GLB = {"wolf": os.path.join(HERE, "wolf.glb"), "donker": os.path.join(HERE, "donkere_wolf.glb")}
SCRATCH = KO.SCRATCH
H_GRID = 0.007 if SNEL else 0.0045
DOEL_LIJF = 6500
T0 = time.time()
srgb, naar_srgb, ruis, gladstap = BM.srgb, BM.naar_srgb, BM.ruis, BM.gladstap
nrm = KO.nrm
# koe.py-helpers lezen hun eigen globals: naar de wolf zetten
KO.RES, KO.TEX, KO.SPP = RES, TEX, (0.25 if SNEL else 1.0)
KO.DELEN = ["lijf"]


def log(*a):
    print(f"[wolf {time.time() - T0:6.1f}s]", *a, flush=True)


KO.log = log

# vachtkleuren (sRGB), per soort: licht (keel, buik, snuit), midden (flank), donker (zadel, staartpunt, oorrug)
VACHT = {
    "wolf": {"licht": "#dcd8d0", "midden": "#7f7c77", "donker": "#353331", "punt": "#efede8", "neus": "#151414"},
    "donker": {"licht": "#c9c6c0", "midden": "#2c2b2a", "donker": "#141313", "punt": "#5a5856", "neus": "#0c0c0c"},
}
OOG_KLEUR = "#ff1a0d"


# --- Vorm -----------------------------------------------------------------------------------------------
class Ruig:
    """SDF met een ruisrand: d - amp * ruis, alleen waar `gewicht` (plukken in de vacht)."""

    def __init__(self, S, sk):
        self.S, self.sk = S, sk

    def grens(self):
        lo, hi = self.S.grens()
        return lo - 0.02, hi + 0.02

    def __call__(self, P, grond=True):
        d = self.S(P, grond)
        sel = d < 0.03
        if sel.any():
            Q = P[sel]
            w = vacht_gewicht(Q, self.sk)
            # plukken: langgerekt langs de haarrichting (grofweg naar achteren-onder)
            Qa = Q * np.array([38.0, 14.0, 22.0])
            r = ruis(Qa, 1.0, 5, 2)
            d[sel] -= w * (0.008 + 0.010 * r)
        return d


def vacht_gewicht(Q, sk):
    """0..1: hoe ruig de vacht hier is (nek/manen en staart ruig, snuit en onderpoten glad)."""
    s = sk.s
    z, y = Q[:, 2], Q[:, 1]
    w = 0.45 * gladstap(0.45, 0.62, z)                                     # romp
    manen = gladstap(0.20, 0.08, np.linalg.norm((Q - np.array([0, -0.46, 0.76]) * s) / np.array([1.3, 1.0, 1.0]), axis=1))
    w = np.maximum(w, manen)
    st = gladstap(0.50, 0.58, y) * gladstap(0.20, 0.30, z)
    w = np.maximum(w, st)
    kop = gladstap(-0.60 * s, -0.66 * s, y)                                # voor de oren: kort haar
    return np.clip(w * (1 - kop), 0, 1)


def vorm_lijf(sk):
    s, J, T = sk.s, sk.J, sk.T
    V = lambda x, y, z: np.array((x, y, z)) * s
    S = KO.SDF()
    # romp: diepe smalle borst, ingetrokken buik, gespierde achterhand
    S.el(V(0, -0.27, 0.60), np.array((0.14, 0.19, 0.20)) * s, k=0.08 * s)       # borstkas
    S.el(V(0, -0.40, 0.56), np.array((0.10, 0.10, 0.15)) * s, k=0.07 * s)        # voorborst
    S.el(V(0, 0.02, 0.65), np.array((0.12, 0.22, 0.125)) * s, k=0.08 * s)         # buik (tuck-up)
    S.el(V(0, 0.30, 0.64), np.array((0.13, 0.15, 0.145)) * s, k=0.08 * s)        # achterhand
    S.rc(V(0, -0.36, 0.75), V(0, 0.44, 0.71), 0.065 * s, 0.06 * s, k=0.08 * s)    # ruglijn
    S.el(V(0, -0.34, 0.78), np.array((0.08, 0.10, 0.05)) * s, k=0.06 * s)        # schoft
    # nek met manen
    S.rc(V(0, -0.34, 0.66), V(0, -0.60, 0.84), 0.17 * s, 0.125 * s, k=0.08 * s)
    S.el(V(0, -0.49, 0.72), np.array((0.17, 0.13, 0.19)) * s, k=0.08 * s)        # manen / kraag
    S.el(V(0, -0.55, 0.65), np.array((0.09, 0.08, 0.09)) * s, k=0.06 * s)        # keel
    # kop
    d, u = KO.kop_assen(sk)
    H0, H1 = J["Head"], T["Head"]
    KA = np.array([[1, 0, 0], d, u])
    S.el(H0 + d * 0.055 * s, np.array((0.100, 0.090, 0.088)) * s, k=0.03 * s, assen=KA)            # schedel
    S.el(H0 + d * 0.065 * s + u * 0.055 * s, np.array((0.120, 0.08, 0.075)) * s, k=0.04 * s, assen=KA)  # wangkraag
    S.rc(H0 + d * 0.11 * s + u * 0.005 * s, H1 - d * 0.022 * s + u * 0.010 * s, 0.052 * s, 0.029 * s,
         k=0.03 * s)                                                                                # snuit
    S.el(H1 - d * 0.018 * s + u * 0.002 * s, np.array((0.026, 0.022, 0.022)) * s, k=0.01 * s, assen=KA)  # neus
    S.rc(J["Jaw"], T["Jaw"] - d * 0.01 * s, 0.036 * s, 0.021 * s, k=0.02 * s)                        # onderkaak
    S.el(H0 + d * 0.09 * s - u * 0.05 * s, np.array((0.05, 0.03, 0.02)) * s, k=0.02 * s, assen=KA)    # voorhoofd/stop
    for sg in (1, -1):
        oc = oog_c(sk, sg)
        S.el(oc, np.array((0.020, 0.022, 0.014)) * s, k=0.008 * s, m="-", assen=KA)                 # oogkas
        # oor: driehoekig, rechtop, kom naar voren
        eb = ("Left" if sg > 0 else "Right") + "Ear"
        ea, ee = J[eb], T[eb]
        e = nrm(ee - ea)
        t = nrm(np.array([0, -1.0, 0]) - e * e[1])          # naar voren, loodrecht op het oor
        w = nrm(np.cross(e, t))
        t = np.cross(w, e)
        OA = np.array([e, w, t])
        S.el(ea + e * 0.025 * s, np.array((0.042, 0.048, 0.028)) * s, k=0.015 * s, assen=OA)
        S.el(ea + e * 0.060 * s, np.array((0.038, 0.028, 0.018)) * s, k=0.010 * s, assen=OA)
        S.el(ea + e * 0.042 * s - t * 0.013 * s, np.array((0.040, 0.028, 0.010)) * s, k=0.006 * s, m="-", assen=OA)
    # voorbenen
    for z in ("Left", "Right"):
        b = lambda n: z + n
        sg = 1 if z == "Left" else -1
        sh, el_, kn, ko, te = J[b("UpperArm")], J[b("ForeArm")], J[b("FrontCannon")], J[b("FrontHoof")], T[b("FrontHoof")]
        S.el(sh + V(-sg * 0.015, 0.03, 0.03), np.array((0.06, 0.09, 0.12)) * s, k=0.06 * s)      # schouder
        S.rc(sh, el_, 0.058 * s, 0.042 * s, k=0.05 * s)
        S.rc(el_, kn, 0.041 * s, 0.025 * s, k=0.025 * s)
        S.el(kn, np.array((0.024, 0.026, 0.028)) * s, k=0.012 * s)                                  # pols
        poot(S, kn, ko, te, s)
    # achterbenen
    for z in ("Left", "Right"):
        b = lambda n: z + n
        sg = 1 if z == "Left" else -1
        hp, kn, hak, ko, te = J[b("Thigh")], J[b("Shin")], J[b("HindCannon")], J[b("HindHoof")], T[b("HindHoof")]
        S.rc(hp + V(0, -0.02, 0.02), kn, 0.10 * s, 0.055 * s, k=0.06 * s)                            # dij
        S.el((hp + kn) / 2 + V(sg * 0.01, 0.03, 0), np.array((0.075, 0.11, 0.13)) * s, k=0.06 * s)
        S.rc(kn, hak, 0.05 * s, 0.024 * s, k=0.03 * s)                                              # scheen
        S.el(kn + (hak - kn) * 0.3 + V(0, 0.02, 0), np.array((0.045, 0.05, 0.07)) * s, k=0.04 * s)  # kuit
        S.el(hak + V(0, 0.012, 0.005), np.array((0.022, 0.03, 0.03)) * s, k=0.012 * s)              # hak
        poot(S, hak, ko, te, s)
    # staart: pluim, hangt
    st = [J["Tail"], J["Tail1"], J["Tail2"], J["Tail3"], T["Tail3"]]
    S.rc(V(0, 0.42, 0.72), st[0], 0.05 * s, 0.045 * s, k=0.04 * s)
    rs = [0.045, 0.062, 0.070, 0.060, 0.028]
    for i in range(4):
        S.rc(st[i], st[i + 1], rs[i] * s, rs[i + 1] * s, k=0.03 * s)
    return Ruig(S, sk)


def poot(S, boven, ko, te, s):
    """Middenvoet, bal en voet (teen naar voren, plat op de grond)."""
    S.rc(boven, ko, 0.022 * s, 0.024 * s, k=0.012 * s)
    c = np.array(((ko[0] + te[0]) / 2, (ko[1] + te[1]) / 2 - 0.005 * s, 0.022 * s))
    S.el(c, np.array((0.032, 0.048, 0.026)) * s, k=0.014 * s)


OOG = (0.105, 0.050, 0.036, 0.013)     # langs de kop, opzij, omhoog (-u), straal


def oog_c(sk, sg):
    d, u = KO.kop_assen(sk)
    return sk.J["Head"] + (d * OOG[0] + np.array((sg * OOG[1], 0, 0)) - u * OOG[2]) * sk.s


def maak_ogen(sk):
    """Twee oogbollen (iets afgeplat, schuin naar voren), voor de rode gloed een eigen materiaal."""
    B = BM.Bouwer()
    d, u = KO.kop_assen(sk)
    for sg in (1, -1):
        c = oog_c(sk, sg)
        r = OOG[3] * sk.s
        uit = nrm(np.array((sg * 0.75, 0, 0)) + 0.6 * d - 0.1 * u)
        a1 = nrm(np.cross(uit, -u))
        a2 = np.cross(uit, a1)
        n, m = 10, 6
        rows = []
        for i in range(1, m):
            th = math.pi * i / m
            ring = [c + uit * r * 0.7 * math.cos(th) + (a1 * math.cos(p) * 1.25 + a2 * math.sin(p)) * r * math.sin(th)
                    for p in 2 * np.pi * np.arange(n) / n]
            rows.append(ring)
        b0, _ = B.grid(np.array(rows), True)
        B.kap(b0, n, c + uit * r * 0.7)
        B.kap(b0 + n * (m - 2), n, c - uit * r * 0.7)
    o = B.obj("ogen", bpy.context.scene.collection)
    bm = bmesh.new()
    bm.from_mesh(o.data)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bm.to_mesh(o.data)
    bm.free()
    return o


# --- Texturen --------------------------------------------------------------------------------------------
def velden(B, sk):
    """Per gedekte texel: positie, normaal en de maskers die beide soorten delen."""
    s = sk.s
    idm = B["id"]
    ys, xs = np.nonzero(idm[..., 1] > 0.5)
    P = B["pos"][ys, xs, :3].astype(np.float64)
    Q = P / s
    N = B["nrm"][ys, xs, :3].astype(np.float64) * 2 - 1
    N /= np.linalg.norm(N, axis=1, keepdims=True) + 1e-9
    n = len(P)
    d, u = KO.kop_assen(sk)
    H0, H1 = sk.J["Head"] / s, sk.T["Head"] / s
    tk = np.clip((Q - H0) @ (H1 - H0) / np.sum((H1 - H0) ** 2), -0.6, 1.5)
    kopafst = np.linalg.norm(Q - (H0 + np.clip(tk, 0, 1)[:, None] * (H1 - H0)), axis=1)
    w_kop = gladstap(0.15, 0.10, kopafst) * (tk > -0.15)
    w_staart = gladstap(0.44, 0.50, Q[:, 1]) * gladstap(0.74, 0.70, Q[:, 2])
    w_been = gladstap(0.42, 0.30, Q[:, 2]) * (1 - w_staart)
    w_romp = np.clip(1 - w_kop - w_been - w_staart, 0, 1)
    streken = [  # (gewicht, richting, fijn dwars/langs, pluk dwars/langs, hoogte fijn/pluk)
        (w_romp, (0, 0.6, -1.0), (260, 14), (55, 4), (0.0010, 0.0024)),
        (w_been, (0, 0.10, -1.0), (300, 22), (90, 8), (0.0005, 0.0008)),
        (w_kop, tuple(d), (320, 26), (110, 10), (0.0004, 0.0007)),
        (w_staart, (0, 0.25, -1.0), (240, 5), (60, 2), (0.0012, 0.0030)),
    ]

    def streng(t, fd, fl, seed, octv=2):
        t = nrm(t)
        Qa = Q * fd + np.outer(Q @ t, t) * (fl - fd)
        return ruis(Qa, 1.0, seed, octv)

    haar = np.zeros(n)
    H = np.zeros(n)
    for i, (w, t, fijn, pluk, amp) in enumerate(streken):
        hf = streng(t, *fijn, 50 + i)
        hp = streng(t, *pluk, 60 + i)
        haar += w * (0.5 * hf + 0.5 * hp)
        H += w * (amp[0] * hf + amp[1] * hp)
    # --- maskers
    # onderkant licht: buik, keel, borst, binnenkant poten, onderkaak, wangen
    onder = gladstap(-0.05, -0.55, N[:, 2]) * (1 - w_staart)
    keel = gladstap(0.15, 0.05, np.linalg.norm((Q - np.array([0, -0.55, 0.64])) / np.array([0.8, 1.0, 1.3]), axis=1))
    borst = gladstap(0.13, 0.04, np.linalg.norm((Q - np.array([0, -0.43, 0.52])) / np.array([0.7, 1.0, 1.4]), axis=1))
    binnen = gladstap(0.07, 0.03, np.abs(Q[:, 0])) * gladstap(0.6, 0.45, Q[:, 2])
    kin = gladstap(0.035, 0.06, (Q - H0) @ u) * w_kop                 # onderkant kop
    snuit_z = gladstap(0.45, 0.6, tk) * gladstap(0.0, 0.03, (Q - H0) @ u) * w_kop
    wang = 0.0 * Q[:, 0]
    for sg in (1, -1):
        wc = H0 + d * 0.12 + np.array((sg * 0.06, 0, 0)) + u * 0.035
        wang = np.maximum(wang, gladstap(0.05, 0.02, np.linalg.norm(Q - wc, axis=1)))
    licht = np.clip(np.maximum.reduce([onder * 0.9, keel, borst, binnen * 0.8, kin, snuit_z * 0.7, wang * 0.9]), 0, 1)
    licht = np.clip(licht + 0.25 * haar * licht * (1 - licht) * 4, 0, 1)
    # zadel donker: rug en bovenkant nek, staart boven en punt, oorrug
    rug = gladstap(0.25, 0.75, N[:, 2]) * gladstap(0.64, 0.74, Q[:, 2]) * (1 - w_kop)
    zadel = rug * gladstap(-0.50, -0.30, Q[:, 1]) * gladstap(0.55, 0.40, Q[:, 1])
    zadel = np.maximum(zadel, 0.6 * gladstap(0.70, 0.80, Q[:, 2]) * gladstap(-0.62, -0.45, Q[:, 1]) * (1 - w_kop))
    st_boven = w_staart * gladstap(-0.1, 0.5, N @ nrm(np.array([0, 1.0, 1.0])))
    punt = gladstap(0.34, 0.30, Q[:, 2]) * w_staart
    oorrug = 0.0 * Q[:, 0]
    for z in ("Left", "Right"):
        ea, ee = sk.J[z + "Ear"] / s, sk.T[z + "Ear"] / s
        te = (Q - ea) @ (ee - ea) / np.sum((ee - ea) ** 2)
        dist = np.linalg.norm(Q - (ea + np.clip(te, 0, 1)[:, None] * (ee - ea)), axis=1)
        oor = gladstap(0.05, 0.03, dist) * gladstap(-0.1, 0.15, te)
        voor = gladstap(0.0, 0.6, -N[:, 1])
        oorrug = np.maximum(oorrug, oor * (1 - 0.7 * voor) * (0.6 + 0.4 * gladstap(0.5, 1.0, te)))
    donker = np.clip(np.maximum.reduce([zadel, st_boven * 0.7, oorrug]) * (1 - licht), 0, 1)
    donker = np.clip(donker + 0.25 * gladstap(0.2, 0.8, ruis(Q, 9, 3, 2)) * rug, 0, 1)
    # neus en lippen, klauwen
    neus = gladstap(0.024, 0.016, np.linalg.norm(Q - (H1 - d * 0.018), axis=1))
    kaak = sk.J["Jaw"] / s
    kint = sk.T["Jaw"] / s
    lip = np.exp(-(seg_d(Q, kaak + d * 0.01 - u * 0.012, kint - u * 0.012) / 0.006) ** 2) * w_kop
    klauw = gladstap(0.012, 0.004, Q[:, 2]) * w_been
    return dict(ys=ys, xs=xs, Q=Q, N=N, haar=haar, H=H, licht=licht, borst=np.maximum(keel, borst), kin=kin, donker=donker, punt=punt, neus=neus,
                lip=lip, klauw=klauw, w_kop=w_kop)


def seg_d(P, a, b):
    ab = b - a
    t = np.clip((P - a) @ ab / (ab @ ab), 0, 1)
    return np.linalg.norm(P - (a + t[:, None] * ab), axis=1)


def kleur_voor(F, soort):
    """Lineaire kleur per texel voor soort 'wolf' of 'donker'."""
    v = VACHT[soort]
    Q, haar = F["Q"], F["haar"]
    lic, don = F["licht"], F["donker"]
    if soort == "donker":                       # alleen keel en borst wit, de rest zwart
        lic = np.clip(np.maximum(F["borst"], 0.6 * F["kin"]) * (0.85 + 0.3 * haar), 0, 1)
    mid = srgb(v["midden"]) * (1 + 0.20 * ruis(Q, 4, 11, 2))[:, None]
    # agouti: haarpunten licht, wortels donker, per pluk afwisselend
    band = np.clip(haar * 1.6, -1, 1)
    mid = mid * (1 + 0.75 * band)[:, None]
    mid *= (1 + 0.15 * gladstap(0.3, 0.9, ruis(Q * np.array([1, 0.4, 1]), 30, 12)))[:, None]
    kl = mid
    dk = srgb(v["donker"]) * (1 + 0.45 * band)[:, None]
    kl = kl * (1 - don[:, None]) + dk * don[:, None]
    lt = srgb(v["licht"]) * (1 + 0.12 * band)[:, None] * (1 + 0.05 * ruis(Q, 12, 13))[:, None]
    kl = kl * (1 - lic[:, None]) + lt * lic[:, None]
    pk = srgb(v["donker"]) * 0.8
    kl = kl * (1 - F["punt"][:, None]) + pk * F["punt"][:, None]
    nz = srgb(v["neus"])
    kl = kl * (1 - F["neus"][:, None]) + nz * F["neus"][:, None]
    kl = kl * (1 - 0.85 * F["lip"][:, None]) + 0.85 * F["lip"][:, None] * nz
    kl = kl * (1 - F["klauw"][:, None]) + F["klauw"][:, None] * srgb("#1e1c1a")
    return kl


def texturen(B, mpp, sk):
    t1 = time.time()
    F = velden(B, sk)
    ys, xs = F["ys"], F["xs"]
    h, w = B["pos"].shape[:2]
    mask = np.zeros((h, w), bool)
    mask[ys, xs] = True
    ao = B["ao"][..., 0]
    aov = ao[ys, xs]
    kleuren = {}
    for soort in VACHT:
        kl = kleur_voor(F, soort) * (0.55 + 0.45 * aov)[:, None]
        K = np.zeros((h, w, 3), np.float32)
        K[ys, xs] = naar_srgb(kl)
        K = BM.dilateer(K, mask, 10)
        naam = "wolf_kleur" if soort == "wolf" else "donkere_wolf_kleur"
        kleuren[soort] = KO.bewaar(K, naam, False, jpg=True)
    Hm = np.zeros((h, w), np.float32)
    Hm[ys, xs] = F["H"] * (1 - F["neus"])
    mp = np.full((h, w), mpp["lijf"], np.float32)
    Hd = BM.dilateer(Hm[..., None].repeat(3, -1), mask, 3)[..., 0]
    nd = BM.reliëf_normaal(Hd, mp)
    nb = B["normaal"][..., :3] * 2 - 1
    n = np.stack([nb[..., 0] + nd[..., 0], nb[..., 1] + nd[..., 1], nb[..., 2] * nd[..., 2]], -1)
    n /= np.linalg.norm(n, axis=-1, keepdims=True) + 1e-9
    Nimg = n * 0.5 + 0.5
    Nimg[~mask] = (0.5, 0.5, 1.0)
    ORM = np.zeros((h, w, 3), np.float32)
    ORM[..., 0] = np.clip(ao * 0.85 + 0.15, 0, 1)
    ORM[ys, xs, 1] = np.clip(0.86 - 0.06 * F["haar"] - 0.5 * F["neus"], 0, 1)
    Nimg = BM.dilateer(Nimg.astype(np.float32), mask, 10)
    ORM = BM.dilateer(ORM, mask, 10)
    normaal = KO.bewaar(Nimg, "wolf_normaal", True)
    orm = KO.bewaar(ORM, "wolf_orm", True)
    log("texturen", f"{time.time() - t1:.1f}s")
    return kleuren, normaal, orm


def oog_mat():
    m = bpy.data.materials.new("mat_oog")
    m.use_nodes = True
    b = m.node_tree.nodes["Principled BSDF"]
    c = (*srgb(OOG_KLEUR), 1)
    b.inputs["Base Color"].default_value = c
    b.inputs["Roughness"].default_value = 0.15
    b.inputs["Emission Color"].default_value = c
    b.inputs["Emission Strength"].default_value = 2.5
    return m


# --- Gewichten -------------------------------------------------------------------------------------------
def skin(o, rig, sk):
    BM.ontkies()
    o.select_set(True)
    rig.select_set(True)
    bpy.context.view_layer.objects.active = rig
    bpy.ops.object.parent_set(type="ARMATURE_AUTO")
    me = o.data
    P = np.array([v.co for v in me.vertices])
    vg = {g.name: g for g in o.vertex_groups}

    def zet(mask, bot):
        ids = np.nonzero(mask)[0].tolist()
        if not ids:
            return
        for g in o.vertex_groups:
            g.remove(ids)
        (vg.get(bot) or o.vertex_groups.new(name=bot)).add(ids, 1.0, "REPLACE")

    s = sk.s
    KO.glad_gewichten(o, 0.5, 3)
    for z in ("Left", "Right"):
        ea, ee = sk.J[z + "Ear"], sk.T[z + "Ear"]
        e = ee - ea
        t = np.clip((P - ea) @ e / (e @ e), -1, 2)
        dist = np.linalg.norm(P - (ea + t[:, None] * e), axis=1)
        zet((t > 0.15) & (dist < 0.05 * s) & (np.sign(P[:, 0]) == np.sign(ea[0])), z + "Ear")
    # kop voor de oren star aan Head (snuit, neus), onderkaak aan Jaw
    d, u = KO.kop_assen(sk)
    H0 = sk.J["Head"]
    tk = (P - H0) @ d
    kaak = (seg_d(P, sk.J["Jaw"], sk.T["Jaw"]) < 0.03 * s) & (((P - H0) @ u) > 0.045 * s) & (tk > 0.12 * s)
    zet((tk > 0.10 * s) & ~kaak & (P[:, 2] > 0.70 * s), "Head")
    zet(kaak, "Jaw")
    KO.onderbenen(o, sk)
    bpy.context.view_layer.objects.active = o
    BM.ontkies()
    o.select_set(True)
    bpy.ops.object.vertex_group_limit_total(group_select_mode="ALL", limit=4)
    bpy.ops.object.vertex_group_clean(group_select_mode="ALL", limit=0.01)
    bpy.ops.object.vertex_group_normalize_all(lock_active=False)
    leeg = sum(1 for v in me.vertices if not v.groups)
    if leeg:
        log("  let op:", leeg, "vertices zonder gewicht")


def skin_ogen(o, rig):
    o.parent = rig
    m = o.modifiers.new("Armature", "ARMATURE")
    m.object = rig
    g = o.vertex_groups.new(name="Head")
    g.add(list(range(len(o.data.vertices))), 1.0, "REPLACE")


# --- Previews --------------------------------------------------------------------------------------------
def zet_kleur(mat, img):
    for nd in mat.node_tree.nodes:
        if nd.type == "TEX_IMAGE" and nd.image is not None and nd.image.name.endswith("_kleur"):
            nd.image = img


def rust(rig):
    rig.animation_data_create().action = None
    for b in rig.pose.bones:
        b.rotation_quaternion = (1, 0, 0, 0)
        b.location = (0, 0, 0)
    bpy.context.view_layer.update()


def poses(sc, rig, mat, kleuren, tag=""):
    keuzes = [("idle", 0), ("idle", 60), ("lopen", 4), ("lopen", 17), ("rennen", 2), ("rennen", 7),
              ("bijten", 5), ("bijten", 9), ("dood", 14), ("dood", 24)]
    tmp = bpy.app.tempdir
    rijen = []
    for soort, yaw, pitch in (("wolf", 225, 30), ("wolf", 180, 6), ("donker", 225, 30)):
        if mat is not None:
            zet_kleur(mat, kleuren[soort])
        panelen = []
        for act, f in keuzes:
            R.K.zet_actie(rig, act)
            sc.frame_set(f)
            BM.studio(sc, 150, 2.4, 1.6, doel=(0, -0.2, 0.5), yaw=yaw, pitch=pitch)
            panelen.append(BM.bijsnijden(BM.render_np(sc, os.path.join(tmp, f"p_{act}_{f}.png"))))
        rijen.append(BM.plak(panelen))
    if mat is not None:
        zet_kleur(mat, kleuren["wolf"])
    BM.schrijf(BM.onder(*rijen), os.path.join(PREV, f"wolf_poses{tag}.png"))
    rust(rig)


def vergelijk(sc, rig, mat, kleuren, tag=""):
    """Lokaal: concept en sprites naast de renders (NIET committen)."""
    rust(rig)
    tmp = bpy.app.tempdir
    big = []
    for yw, pt in ((180, 5), (270, 5), (240, 12), (90, 5)):
        BM.studio(sc, 330, 1.9, 1.3, doel=(0, -0.25, 0.55), yaw=yw, pitch=pt)
        big.append(BM.bijsnijden(BM.render_np(sc, os.path.join(tmp, f"c_{yw}.png"))))
    pad = os.path.join(MOD, "..", "lokaal", "concept", "img", "wolf.jpg")
    rij = BM.plak(big)
    if os.path.exists(pad):
        c = BM.laad_np(pad)[..., :3]
        c = np.concatenate([c, np.ones((*c.shape[:2], 1), np.float32)], 2)
        k = max(1, int(round(c.shape[1] / rij.shape[1]))) if c.shape[1] > rij.shape[1] else 1
        c = c[::k, ::k]
        rij = BM.onder(BM.plak([c]), rij)
    BM.schrijf(rij, os.path.join(PREV, f"wolf_vergelijk_close{tag}.png"))
    # 1x: sprites (grijs, donker) naast de render op 21,9 px/m, iso yaw 225 pitch 30
    so = os.path.join(SCRATCH, "bb_original")
    pan = []
    for soort, spr in (("wolf", "wolfstil.png"), ("donker", "dw_still.png")):
        p = os.path.join(so, spr)
        if os.path.exists(p):
            pan.append(BM.bijsnijden(BM.laad_np(p)))
        if mat is not None:
            zet_kleur(mat, kleuren[soort])
        BM.studio(sc, 21.9, 2.4, 1.6, doel=(0, -0.2, 0.5), yaw=225, pitch=30)
        pan.append(BM.bijsnijden(BM.render_np(sc, os.path.join(tmp, f"r1_{soort}.png"))))
    if mat is not None:
        zet_kleur(mat, kleuren["wolf"])
    BM.schrijf(BM.plak([BM.nn(p, 6) for p in pan]), os.path.join(PREV, f"wolf_vergelijk_1x{tag}.png"))


# --- Hoofdprogramma --------------------------------------------------------------------------------------
def exporteer(pad):
    BM.ontkies()
    bpy.ops.export_scene.gltf(filepath=pad, export_format="GLB", export_animations=True,
                              export_animation_mode="ACTIONS", export_force_sampling=True, export_yup=True,
                              export_skins=True, export_def_bones=False, export_extras=True, use_selection=False,
                              export_tangents=True, export_image_format="AUTO", export_cameras=False,
                              export_lights=False)
    log("export", pad, f"{os.path.getsize(pad) / 1e6:.1f} MB")


def main():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    sc = bpy.context.scene
    sc.render.fps = R.FPS
    sc.frame_start = 0
    coll = sc.collection
    rig = R.bouw_rig()
    sk = KO.Skelet(rig)
    vorm = vorm_lijf(sk)
    hoog = KO.oppervlak(vorm, H_GRID, "lijf_hoog", coll)
    lijf = KO.decimeer(hoog, "lijf", DOEL_LIJF, coll)
    lijf.data.shade_smooth()
    ogen = maak_ogen(sk)
    log("driehoeken", KO.driehoeken([lijf, ogen]))
    mat, kleuren = None, {}
    if "vlak" in OPTS:
        lijf.data.materials.append(BM.vlak_mat("v_lijf", srgb("#8d8a84")))
        bpy.data.objects.remove(hoog)
    else:
        mpp = KO.uv_atlas({"lijf": lijf})
        log("m/texel (mm)", round(mpp["lijf"] * 1000, 2))
        B = KO.bak_alles({"lijf": lijf}, {"lijf": [hoog]}, sk)
        bpy.data.objects.remove(hoog)
        kleuren, normaal, orm = texturen(B, mpp, sk)
        mat = BM.pbr("mat_lijf", kleuren["wolf"], normaal, orm)
        lijf.data.materials.clear()
        lijf.data.materials.append(mat)
    ogen.data.materials.append(oog_mat())
    skin(lijf, rig, sk)
    skin_ogen(ogen, rig)
    info = R.bouw_animaties(rig)
    json.dump(info, open(os.path.join(HERE, "wolf_anim.json"), "w"), indent=2)
    log("animaties", list(info))
    if "geen_export" not in OPTS and mat is not None:
        exporteer(GLB["wolf"])
        zet_kleur(mat, kleuren["donker"])
        exporteer(GLB["donker"])
        zet_kleur(mat, kleuren["wolf"])
    tag = OPTS.get("tag", "")
    os.makedirs(PREV, exist_ok=True)
    if "vergelijk" in OPTS:
        vergelijk(sc, rig, mat, kleuren, tag)
    if "poses" in OPTS:
        poses(sc, rig, mat, kleuren, tag)
    bpy.ops.wm.save_as_mainfile(filepath=os.path.join(PREV, "wolf.blend"))
    log("KLAAR")


if __name__ == "__main__":
    main()
