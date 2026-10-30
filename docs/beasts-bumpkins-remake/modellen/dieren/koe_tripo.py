"""Koe naar de Tripo-referentie: de procedurele koe (koe.py, preview/koe.blend) vervormd tot het silhouet van een
zijaanzicht-render en die beelden erop geprojecteerd, met hetzelfde skelet (botten door dezelfde afbeelding) en
de clips van koe_rig.py -> spel/assets/koe_tripo.glb (spel.json koe_model "tripo"), koe_tripo_anim.json.

Draaien (eerst koe.py, die schrijft preview/koe.blend):
  blender -b -P koe_tripo.py -- [zij] [poses] [ankers] [geen_export]
- `zij`: lokaal/tripo/koe/koe_tripo_zij.png (links en rechts naast de referentie, zelfde maat).
- `poses`: lokaal/tripo/koe/koe_tripo_poses.png (standen uit alle clips).
- `ankers`: lokaal/tripo/koe/koe_tripo_ankers.png (beide contouren met de ankerparen).
⚠️ Alles met de geprojecteerde textuur blijft lokaal (glb in spel/assets/, previews in lokaal/): de kleuren komen
uit de Tripo-render. Alleen dit script gaat in git.

Invoer (lokaal, gitignored): lokaal/tripo/koe/koe_{links,rechts,voor,boven}.png (Tripo-koe, studio-achtergrond).

Stappen:
1. koe.blend laden: lijf, uier, halsband, bel, koe_rig (gewichten, UV-atlas, normaal/ORM blijven).
2. Silhouet van opzij (lijf zonder hangende staart, 300 px/m) en van koe_links.png (staart weggesneden, slagschaduw
   weg) als contour; ANKERS + tussenpunten = thin-plate spline (y, z) -> referentiepixel; lineair terug naar m
   (schofthoogte als de procedurele koe, voeten op 0). x: wortel van de oppervlaktefactor rond lijf- of pootmidden.
   Staart (Tail1-3) rigide mee met zijn wortel, hangt dus nog vrij achter de billen.
3. Rustbotten door dezelfde afbeelding, clips opnieuw (koe_rig.bouw_animaties).
4. Kleur (atlas 2048, alleen de mat_lijf-texels): linkerkant uit koe_links, rechterkant uit koe_rechts (gespiegeld,
   tweede TPS links-px -> rechts-px: de vlekken verschillen per kant), naar boven gerichte texels uit koe_boven,
   kop-voorkant uit koe_voor. Scherende normalen iets naar binnen bemonsterd. ORM: ruwheid uit de helderheid.
"""
import json
import math
import os
import sys
import time

argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
OPTS = {a.split("=")[0]: (a.split("=", 1)[1] if "=" in a else "1") for a in argv}

import bpy  # noqa: E402
import numpy as np  # noqa: E402
from mathutils import Vector  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import koe_rig as R  # noqa: E402
import dieren_basis as BM  # noqa: E402
import projectie as PJ  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(HERE))
BLEND = os.path.join(HERE, "preview", "koe.blend")
REFD = os.path.join(ROOT, "lokaal", "tripo", "koe")
UIT = REFD
ASSETS = os.path.join(ROOT, "spel", "assets")
GLB = os.path.join(ASSETS, "koe_tripo.glb")
ANIM = os.path.join(HERE, "koe_tripo_anim.json")
PPM = 300.0
LAM = 0.5
KX = float(OPTS.get("kx", 0.93))         # extra breedte bovenop de oppervlaktefactor (koe_voor: romp smaller)
KOP = float(OPTS.get("kop", 0.70))        # x van kop en kaak (koe_voor: smalle kop)
OOR = float(OPTS.get("oor", 1.35))        # oren groter (koe_voor: grote, horizontale oren)
OUD = {}                                  # rustbotten van de procedurele koe (kop, staart), voor de oren
T0 = time.time()
gladstap = BM.gladstap


def log(*a):
    print(f"[koe_tripo {time.time() - T0:6.1f}s]", *a, flush=True)


# (y, z) op de procedurele koe (m, -y = voor) -> (kolom, rij) in koe_links.png, op_contour. Met de klok mee vanaf de
# kruin: rug, billen, achterbeen (achterkant van het NABIJE been: binnenin het silhouet, dus losse punten), hoef,
# voorkant achterbeen, buik, voorbeen (idem), borst, keel, kin, snuit, voorhoofd.
ANKERS = [
    ((-0.759, 1.219), (127, 62), True),     # kruin
    ((-0.709, 1.189), (145, 70), True),
    ((-0.596, 1.149), (178, 84), True),     # nek
    ((-0.347, 1.106), (234, 76), True),     # schoft
    ((-0.030, 1.066), (304, 84), True),
    ((0.360, 1.062), (379, 76), True),      # heupknobbel
    ((0.534, 1.009), (431, 97), True),
    ((0.571, 0.891), (427, 107), True),     # zitbeen / staartwortel
    ((0.477, 0.695), (430, 186), True),     # billen
    ((0.375, 0.537), (419, 251), True),
    ((0.393, 0.448), (419, 292), False),    # achterkant nabije achterpoot
    ((0.451, 0.382), (418, 312), False),    # hak
    ((0.422, 0.294), (411, 330), False),
    ((0.405, 0.201), (408, 345), False),
    ((0.401, 0.111), (405, 358), False),
    ((0.377, 0.030), (397, 369), False),    # hiel
    ((0.349, 0.002), (372, 380), True),     # zool
    ((0.281, 0.067), (367, 371), True),     # teen
    ((0.325, 0.183), (385, 339), True),
    ((0.322, 0.362), (382, 283), True),
    ((0.217, 0.430), (374, 266), True),     # knie / flank
    ((-0.018, 0.436), (317, 260), True),    # buik
    ((-0.207, 0.462), (259, 256), True),
    ((-0.260, 0.447), (246, 264), True),    # elleboog
    ((-0.292, 0.361), (234, 276), False),   # achterkant nabije voorpoot
    ((-0.317, 0.271), (226, 295), False),
    ((-0.332, 0.177), (221, 318), False),
    ((-0.330, 0.087), (217, 343), False),
    ((-0.355, 0.038), (212, 359), False),   # hiel
    ((-0.434, 0.002), (187, 372), True),    # zool
    ((-0.447, 0.011), (183, 367), False),   # teen
    ((-0.418, 0.130), (201, 325), True),
    ((-0.412, 0.319), (198, 287), True),
    ((-0.392, 0.444), (198, 267), True),
    ((-0.389, 0.509), (190, 251), True),    # borstpunt
    ((-0.470, 0.607), (170, 219), True),
    ((-0.555, 0.705), (159, 185), True),    # keel
    ((-0.699, 0.832), (128, 162), True),
    ((-0.807, 0.867), (109, 160), True),    # kaak
    ((-0.907, 0.786), (85, 157), True),     # kin
    ((-0.990, 0.857), (73, 147), True),
    ((-1.009, 0.916), (71, 138), True),     # neuspunt
    ((-0.942, 1.022), (92, 111), True),     # voorhoofd
    ((-0.886, 1.132), (102, 85), True),
    ((-0.815, 1.192), (111, 73), True),
]
# koe_links-pixel -> koe_rechts-pixel (horizontaal gespiegeld, kop links): dezelfde plekken op het silhouet
RECHTS = [
    ((129, 61), (139, 62)), ((145, 70), (157, 67)), ((178, 84), (189, 84)), ((234, 76), (244, 76)),
    ((304, 84), (314, 84)), ((379, 76), (389, 76)), ((431, 97), (437, 101)), ((428, 147), (437, 157)),
    ((430, 206), (438, 215)), ((419, 261), (430, 262)), ((419, 318), (426, 326)), ((405, 368), (410, 372)),
    ((372, 380), (376, 383)), ((367, 371), (367, 376)), ((385, 339), (379, 361)), ((382, 283), (389, 306)),
    ((374, 266), (376, 271)), ((317, 260), (323, 260)), ((259, 256), (270, 256)), ((246, 264), (258, 265)),
    ((233, 315), (248, 299)), ((221, 363), (245, 352)), ((187, 372), (199, 372)), ((191, 360), (196, 361)),
    ((201, 325), (209, 327)), ((198, 267), (206, 270)), ((190, 251), (202, 251)), ((164, 201), (178, 203)),
    ((128, 162), (143, 161)), ((90, 159), (105, 158)), ((75, 133), (93, 131)), ((96, 103), (112, 100)),
    ((111, 73), (125, 74)), ((300, 170), (310, 170)), ((380, 180), (390, 182)), ((200, 160), (212, 160)),
]
# staart in koe_links: binnenrand per rij (alles rechts ervan is staart, geen lijf)
STAART_RAND = ([105, 150, 200, 225, 250, 290, 300], [427, 429, 431, 428, 420, 420, 424])


# --- Referenties ----------------------------------------------------------------------------------------
def _box(x, k=2):
    c = np.cumsum(np.cumsum(np.pad(x, k + 1, mode="edge"), 0), 1)
    n = 2 * k + 1
    return (c[n:, n:] - c[:-n, n:] - c[n:, :-n] + c[:-n, :-n])[:x.shape[0], :x.shape[1]] / n / n


def segmenteer(a):
    """projectie.segmenteer plus: vlakke grijze slagschaduw op de vloer (lage verzadiging en ruis) is geen koe."""
    m = PJ.segmenteer(a)
    a = a * 255.0
    lum = a.mean(-1)
    sat = a.max(-1) - a.min(-1)
    sd = np.sqrt(np.maximum(_box(lum * lum) - _box(lum) ** 2, 0))
    m &= ~((sat < 7) & (lum > 60) & (lum < 100) & (sd < 2.0))
    m = PJ.grootste(m)
    return ~PJ.grootste(~m, rand=True)


def referentie(naam, spiegel=False):
    a = BM.laad_np(os.path.join(REFD, naam + ".png"))[..., :3]
    if spiegel:
        a = a[:, ::-1].copy()
    m = segmenteer(a)
    a = ontlicht(a, m)
    ext, _ = PJ.uitbreiden(a, m, 60)
    log("referentie", naam, a.shape, int(m.sum()), "px")
    return a, m, ext


WIT = float(OPTS.get("wit", 0.84))       # sRGB-waarde van de witte vacht na ontlichten (procedureel GRIJS 0,86)
ONTLICHT = 0.8                            # 1 = de studioschaduw helemaal weg, 0 = zoals gerenderd


def ontlicht(a, m):
    """Ingebakken studiolicht eruit: de helderheid van de witte vacht, breed uitgesmeerd, is het licht; daardoor
    delen (deels) en op WIT zetten. Zwart schaalt mee, zodat de vlekken hun eigen glans houden."""
    lum = a @ np.array([0.2126, 0.7152, 0.0722], np.float32)
    w = (m & (lum > 0.42)).astype(np.float32)
    def blur(x):
        for _ in range(2):
            x = _box(x, 14)
        return x
    S = blur(lum * w) / np.maximum(blur(w), 1e-4)
    S = np.where(blur(w) > 0.02, S, float(np.median(lum[w > 0])))
    k = (WIT / np.clip(S, 0.25, 1.0)) ** ONTLICHT
    return np.clip(a * k[..., None], 0, 1)


# --- Vervorming -----------------------------------------------------------------------------------------
def staartgewichten(o):
    gi = {g.index: g.name for g in o.vertex_groups}
    w = np.zeros((len(o.data.vertices), 3))
    for v in o.data.vertices:
        for ge in v.groups:
            if gi[ge.group] in ("Tail1", "Tail2", "Tail3"):
                w[v.index, ("Tail1", "Tail2", "Tail3").index(gi[ge.group])] += ge.weight
    return w


def staartgewicht(o):
    return np.clip(staartgewichten(o).sum(1), 0, 1)


def driehoeken(o):
    o.data.calc_loop_triangles()
    return np.array([t.vertices[:] for t in o.data.loop_triangles])


class Afbeelding:
    """Procedureel (y, z) in m -> koe_links-pixel (TPS) -> nieuwe (y, z) in m (lineair)."""

    def __init__(self, P, T, mref):
        self.u0, self.v1 = float(P[:, 1].min()), float(P[:, 2].max())
        P2 = self.px(P[:, 1], P[:, 2])
        H = int((self.v1 - P[:, 2].min()) * PPM) + 9
        W = int((P[:, 1].max() - self.u0) * PPM) + 9
        mm = PJ.raster_masker(P2, T, H, W)
        mm = ~PJ.grootste(~PJ.grootste(mm), rand=True)
        self.cs = PJ.herbemonster(PJ.contour(mm), 2.0)
        self.cd = PJ.herbemonster(PJ.contour(mref), 2.0)
        S, D = self.paren()
        self.S, self.D = S, D
        self.t = PJ.tps_fit(S, D, LAM)
        det = PJ.tps_jac(self.t, P2)
        log("TPS", len(S), "paren; det min", round(float(det.min()), 3), "p50", round(float(np.median(det)), 3),
            "gevouwen", int((det <= 0).sum()))
        # lineair ref-px -> m: schofthoogte als de procedurele koe, voeten op 0, midden tussen de voeten y = 0
        band = (P[:, 1] > -0.42) & (P[:, 1] < -0.28)
        schoft_m = float(P[band, 2].max())
        rr = np.nonzero(mref.any(1))[0]
        grond = float(rr.max()) + 0.5
        cols = np.nonzero(mref[:, 225:245].any(0))[0]
        top = min(float(np.nonzero(mref[:, 225 + c])[0].min()) for c in cols)
        self.s = schoft_m / (grond - top)
        self.z0r = grond
        self.yc = 0.5 * (187 + 372)                       # voorzool en achterzool (ANKERS)
        log("schoft", round(schoft_m, 3), "m =", grond - top, "px ->", round(self.s * 1000, 3), "mm/px")

    def paren(self):
        cs, cd = self.cs, self.cd
        ank = [(PJ.dichtst(cs, self.px(*a)[0]), np.array(b, float), PJ.dichtst(cd, b) if c else None) for a, b, c in ANKERS]
        ns, nd = len(cs), len(cd)
        S, D = [], []

        def ip(c, i):
            i0 = int(np.floor(i)) % len(c)
            f = i - np.floor(i)
            return c[i0] * (1 - f) + c[(i0 + 1) % len(c)] * f
        self.ank = ank
        for k in range(len(ank)):
            a0, p0, b0 = ank[k]
            a1, p1, b1 = ank[(k + 1) % len(ank)]
            la = (a1 - a0) % ns
            if b0 is not None and b1 is not None:
                lb = (b1 - b0) % nd
                m = max(2, int(max(la, lb) / 3))
                for j in range(m):
                    S.append(ip(cs, a0 + j / m * la))
                    D.append(ip(cd, b0 + j / m * lb))
            else:
                q0 = cd[b0] if b0 is not None else p0
                q1 = cd[b1] if b1 is not None else p1
                m = max(2, int(max(la, np.linalg.norm(q1 - q0)) / 3))
                for j in range(m):
                    S.append(ip(cs, a0 + j / m * la))
                    D.append(q0 + (q1 - q0) * j / m)
        return np.array(S), np.array(D)

    def px(self, y, z):
        return np.stack([(np.asarray(y) - self.u0) * PPM + 4, (self.v1 - np.asarray(z)) * PPM + 4], -1).reshape(-1, 2)

    def naar_ref(self, y, z):
        return PJ.tps_pas(self.t, self.px(y, z))

    def ref_naar_m(self, q):
        q = np.asarray(q, float).reshape(-1, 2)
        return (q[:, 0] - self.yc) * self.s, (self.z0r - q[:, 1]) * self.s

    def m_naar_ref(self, y, z):
        return np.stack([np.asarray(y) / self.s + self.yc, self.z0r - np.asarray(z) / self.s], -1)

    def yz(self, y, z):
        return self.ref_naar_m(self.naar_ref(y, z))

    def factor(self, y, z):
        return np.sqrt(np.clip(PJ.tps_jac(self.t, self.px(y, z)), 0.05, None)) * self.s * PPM * KX


def poot_midden(P):
    """x-midden per vertex: lijf 0, onder de buik het midden van de poot (zelfde kant, hoogte, y)."""
    x, y, z = P[:, 0], P[:, 1], P[:, 2]
    cx = np.zeros(len(P))
    for i in np.nonzero(z < 0.50)[0]:
        m = (np.sign(x) == np.sign(x[i])) & (np.abs(y - y[i]) < 0.06) & (np.abs(z - z[i]) < 0.03)
        cx[i] = x[m].mean()
    return cx * gladstap(0.50, 0.36, z)


# hangend deel van de staart in koe_links (middenlijn, px): tegen de billen aan zoals de referentie
STAART_LIJN = [(437, 150), (438, 200), (437, 250), (433, 290)]
STAARTBOTTEN = ("Tail1", "Tail2", "Tail3")


class Staart:
    """Staart: nieuwe rustbotten langs STAART_LIJN; de staart-vertices gaan als lineaire skinning mee
    (oude rustmatrix -> nieuwe, met lengteschaal), gemengd met de TPS naar hun staartgewicht."""

    def __init__(self, A, rig):
        bn = rig.data.bones
        self.oud = {n: (np.array(bn[n].matrix_local), bn[n].length) for n in STAARTBOTTEN}
        L = np.array([bn[n].length for n in STAARTBOTTEN])
        f = np.r_[0, np.cumsum(L)] / L.sum()
        q = np.array(STAART_LIJN, float)
        d = np.r_[0, np.cumsum(np.linalg.norm(np.diff(q, axis=0), axis=1))]
        d /= d[-1]
        pts = np.stack([np.interp(f, d, q[:, 0]), np.interp(f, d, q[:, 1])], 1)
        y, z = A.ref_naar_m(pts)
        self.punten = np.stack([np.zeros(len(y)), y, z], 1)          # Tail1-kop .. Tail3-staart
        self.nieuw = {}

    def kop_staart(self, naam):
        i = STAARTBOTTEN.index(naam)
        return self.punten[i], self.punten[i + 1]

    def zet_nieuw(self, rig):
        bn = rig.data.bones
        self.nieuw = {n: (np.array(bn[n].matrix_local), bn[n].length) for n in STAARTBOTTEN}

    def lbs(self, P, W):
        """P (n, 3), W (n, 3) gewichten van Tail1-3 -> getransformeerde punten (genormaliseerd)."""
        P = np.c_[np.asarray(P, float), np.ones(len(P))]
        uit = np.zeros((len(P), 3))
        ws = np.maximum(W.sum(1, keepdims=True), 1e-9)
        for i, n in enumerate(STAARTBOTTEN):
            Mo, Lo = self.oud[n]
            Mn, Ln = self.nieuw[n]
            S = np.diag([1.0, Ln / Lo, 1.0, 1.0])
            M = Mn @ S @ np.linalg.inv(Mo)
            uit += (P @ M.T)[:, :3] * (W[:, i:i + 1] / ws)
        return uit


def vervorm_punten(A, P, cx=None, st=None, wst=None):
    P = np.asarray(P, float).reshape(-1, 3)
    x, y, z = P[:, 0], P[:, 1], P[:, 2]
    k = np.clip(A.factor(y, z), 0.6, 1.6)
    if cx is None:
        cx = np.zeros(len(P))
    yn, zn = A.yz(y, z)
    Q = np.stack([cx + (x - cx) * k, yn, zn], 1)
    if st is not None:
        w = np.clip(wst.sum(1), 0, 1)[:, None]
        Q = Q * (1 - w) + st.lbs(P, wst) * w
    return Q, k


def gewicht(o, namen):
    gi = {g.index: g.name for g in o.vertex_groups}
    w = np.zeros(len(o.data.vertices))
    for v in o.data.vertices:
        for ge in v.groups:
            if gi[ge.group] in namen:
                w[v.index] += ge.weight
    return np.clip(w, 0, 1)


NIEUW = {}


def vervorm(o, A, st, tail=False):
    me = o.data
    P = np.array([v.co for v in me.vertices], float)
    cx = poot_midden(P) if o.name == "lijf" else np.zeros(len(P))
    Q, k = vervorm_punten(A, P, cx, st if tail else None, staartgewichten(o) if tail else None)
    if o.name == "lijf":
        wh = gewicht(o, ("Head", "Jaw"))
        Q[:, 0] *= 1 - (1 - KOP) * wh
        for zijde in ("Left", "Right"):
            we = gewicht(o, (zijde + "Ear",))
            sel = we > 0.5
            h0, _ = OUD[zijde + "Ear"]
            h1 = NIEUW[zijde + "Ear"][0]
            Q[sel, 0] = h1[0] + (P[sel, 0] - h0[0]) * OOR
            Q[sel, 1:] = h1[1:] + (Q[sel, 1:] - vervorm_punten(A, h0[None])[0][0, 1:]) * OOR
    me.vertices.foreach_set("co", Q.astype(np.float32).ravel())
    me.update()
    log("vervormd", o.name, "x-factor p5/p50/p95", np.round(np.percentile(k, [5, 50, 95]), 2).tolist(),
        "maat", np.round(np.ptp(Q, 0), 3).tolist())


def botten(rig, A, st):
    """Rustbotten door de afbeelding; staartbotten rigide; poten: x blijft (pootmidden)."""
    bpy.context.view_layer.objects.active = rig
    bpy.ops.object.mode_set(mode="EDIT")
    eb = rig.data.edit_bones
    rol = {}
    for b in eb:
        n = b.name
        rol[n] = R.ACHTER if n.startswith("Tail") else R.BOVEN if n.endswith("Ear") else \
            R.ONDER if n in ("Hips", "Spine", "Spine1", "Spine2", "Neck", "Neck1", "Head", "Jaw") else R.VOOR
    pos = {}
    for b in eb:
        OUD[b.name] = (np.array(b.head, float), np.array(b.tail, float))
    for b in eb:
        for kant in ("head", "tail"):
            p = np.array(getattr(b, kant), float)
            if b.name in STAARTBOTTEN:
                q = st.kop_staart(b.name)[0 if kant == "head" else 1]
            elif b.name == "Tail" and kant == "tail":
                q = st.punten[0]
            else:
                cx = p[0] * gladstap(0.50, 0.36, p[2])
                q, _ = vervorm_punten(A, p[None], np.array([cx]))
                q = q[0]
            pos[(b.name, kant)] = q
    for zijde in ("Left", "Right"):
        n = zijde + "Ear"
        h0, t0 = OUD[n]
        h1 = pos[(n, "head")].copy()
        h1[0] *= KOP
        t1 = h1 + (pos[(n, "tail")] - pos[(n, "head")]) * OOR
        t1[0] = h1[0] + (t0[0] - h0[0]) * OOR
        pos[(n, "head")], pos[(n, "tail")] = h1, t1
    for b in eb:
        NIEUW[b.name] = (pos[(b.name, "head")], pos[(b.name, "tail")])
    for b in eb:
        b.head = Vector(pos[(b.name, "head")])
        b.tail = Vector(pos[(b.name, "tail")])
        b.align_roll(rol[b.name])
    bpy.ops.object.mode_set(mode="OBJECT")
    st.zet_nieuw(rig)
    rig["schofthoogte"] = float(pos[("Spine2", "tail")][2])
    log("botten: Head", np.round(pos[("Head", "head")], 3).tolist(), "->", np.round(pos[("Head", "tail")], 3).tolist(),
        "schoft", round(rig["schofthoogte"], 3))


# --- Textuur --------------------------------------------------------------------------------------------
def texels(o, w, h, mat=0):
    """Per texel 3D-positie en normaal (rustpose) van de vlakken met material_index `mat`."""
    pos = np.zeros((h, w, 3), np.float32)
    nrm = np.zeros((h, w, 3), np.float32)
    gezet = np.zeros((h, w), bool)
    me = o.data
    uv = me.uv_layers.active.data
    V = np.array([v.co for v in me.vertices], np.float32)
    N = np.array([v.normal for v in me.vertices], np.float32)
    for p in me.polygons:
        if p.material_index != mat:
            continue
        li = list(p.loop_indices)
        for k in range(1, len(li) - 1):
            tri = [li[0], li[k], li[k + 1]]
            U = np.array([uv[i].uv for i in tri], np.float32) * [w, h]
            vi = [me.loops[i].vertex_index for i in tri]
            x0, y0 = np.floor(U.min(0)).astype(int)
            x1, y1 = np.ceil(U.max(0)).astype(int)
            x0, y0 = max(x0 - 1, 0), max(y0 - 1, 0)
            x1, y1 = min(x1 + 1, w - 1), min(y1 + 1, h - 1)
            xs, ys = np.meshgrid(np.arange(x0, x1 + 1) + 0.5, np.arange(y0, y1 + 1) + 0.5)
            d = (U[1, 1] - U[2, 1]) * (U[0, 0] - U[2, 0]) + (U[2, 0] - U[1, 0]) * (U[0, 1] - U[2, 1])
            if abs(d) < 1e-9:
                continue
            a = ((U[1, 1] - U[2, 1]) * (xs - U[2, 0]) + (U[2, 0] - U[1, 0]) * (ys - U[2, 1])) / d
            b = ((U[2, 1] - U[0, 1]) * (xs - U[2, 0]) + (U[0, 0] - U[2, 0]) * (ys - U[2, 1])) / d
            c = 1 - a - b
            m = (a > -0.02) & (b > -0.02) & (c > -0.02)
            if not m.any():
                continue
            iy, ix = (ys[m] - 0.5).astype(int), (xs[m] - 0.5).astype(int)
            bc = np.stack([a[m], b[m], c[m]], 1)
            pos[iy, ix] = bc @ V[vi]
            nrm[iy, ix] = bc @ N[vi]
            gezet[iy, ix] = True
    n = np.linalg.norm(nrm, axis=-1, keepdims=True)
    nrm = nrm / np.maximum(n, 1e-6)
    return pos, nrm, gezet


def zijkleur(A, tr, links, rechts, pos, nrm, staart):
    """Kleur uit de twee zijaanzichten; per texel de kant van zijn x (midden overvloeien)."""
    y, z, x = pos[:, 1], pos[:, 2], pos[:, 0]
    nx = np.abs(nrm[:, 0])
    q = A.m_naar_ref(y, z)
    bn = np.stack([nrm[:, 1], -nrm[:, 2]], 1)
    bn /= np.linalg.norm(bn, axis=1, keepdims=True) + 1e-6
    q = q - bn * (5.0 * (1 - nx) ** 2)[:, None]
    # billen niet uit de staart (die ligt in de referentie ertegenaan): kolom voor de staartrand houden
    r0, r1 = STAART_RAND[0][0], STAART_RAND[0][-1]
    rij = (q[:, 1] >= r0) & (q[:, 1] <= r1) & ~staart
    q[rij, 0] = np.minimum(q[rij, 0], np.interp(q[rij, 1], *STAART_RAND) - 4)
    cl = PJ.bilineair(links, q[:, 0], q[:, 1])
    qr = PJ.tps_pas(tr, q)
    cr = PJ.bilineair(rechts, qr[:, 0], qr[:, 1])
    wl = gladstap(-0.025, 0.025, x)[:, None]
    return cl * wl + cr * (1 - wl)


def zbuffer(V, T, px, diepte, H, W):
    """Kleinste diepte per pixel (orthografisch; px: (n, 2) pixelcoordinaten per vertex)."""
    zb = np.full((H, W), np.inf)
    for a, b, c in T:
        xs = px[[a, b, c], 0]
        ys = px[[a, b, c], 1]
        x0, x1 = max(int(np.floor(xs.min())), 0), min(int(np.ceil(xs.max())), W - 1)
        y0, y1 = max(int(np.floor(ys.min())), 0), min(int(np.ceil(ys.max())), H - 1)
        if x1 < x0 or y1 < y0:
            continue
        gx, gy = np.meshgrid(np.arange(x0, x1 + 1) + 0.5, np.arange(y0, y1 + 1) + 0.5)
        d = (ys[1] - ys[2]) * (xs[0] - xs[2]) + (xs[2] - xs[1]) * (ys[0] - ys[2])
        if abs(d) < 1e-12:
            continue
        l0 = ((ys[1] - ys[2]) * (gx - xs[2]) + (xs[2] - xs[1]) * (gy - ys[2])) / d
        l1 = ((ys[2] - ys[0]) * (gx - xs[2]) + (xs[0] - xs[2]) * (gy - ys[2])) / d
        l2 = 1 - l0 - l1
        k = (l0 >= -1e-3) & (l1 >= -1e-3) & (l2 >= -1e-3)
        dz = l0 * diepte[a] + l1 * diepte[b] + l2 * diepte[c]
        iy, ix = (gy[k] - 0.5).astype(int), (gx[k] - 0.5).astype(int)
        np.minimum.at(zb, (iy, ix), dz[k])
    return zb


def voorkleur(lijf, voor, P, N, rgb):
    """Naar voren gerichte texels (kop, borst) uit koe_voor: orthografisch op de hoogte van het silhouet
    geschaald, alleen waar de texel vooraan zichtbaar is (z-buffer van het eigen lijf)."""
    img, m, ext = voor
    rr = np.nonzero(m.any(1))[0]
    cc = np.nonzero(m[int(0.75 * rr.max() + 0.25 * rr.min()):].any(0))[0]       # poten: midden
    V = np.array([v.co for v in lijf.data.vertices], float)
    hoog = V[:, 2].max()
    ppm = (rr.max() - rr.min()) / hoog
    cx, grond = 0.5 * (cc.min() + cc.max()), rr.max() + 0.5

    def px(Q):
        return np.stack([cx - Q[:, 0] * ppm, grond - Q[:, 2] * ppm], 1)     # van voren: +x (links) staat rechts
    H, W = m.shape
    zb = zbuffer(V, driehoeken(lijf), px(V), V[:, 1], H, W)
    q = px(P)
    ix = np.clip(q[:, 0].astype(int), 0, W - 1)
    iy = np.clip(q[:, 1].astype(int), 0, H - 1)
    zicht = P[:, 1] <= zb[iy, ix] + 0.025
    oor = np.zeros(len(P), bool)                      # oren: zwart uit de zijaanzichten (van voren zie je de binnenkant)
    for zijde in ("Left", "Right"):
        h, t = NIEUW[zijde + "Ear"]
        ab = t - h
        u = np.clip((P - h) @ ab / (ab @ ab), 0, 1)
        oor |= (np.linalg.norm(P - (h + u[:, None] * ab), axis=1) < 0.05) & (u > 0.15)
    w = np.clip((-N[:, 1] - 0.55) / 0.3, 0, 1) * zicht * ~oor
    cv = PJ.bilineair(ext, q[:, 0], q[:, 1])
    log("voor-texels", int((w > 0.5).sum()))
    return rgb * (1 - w[:, None]) + cv * w[:, None]


STAART_KOLOM = 437        # koe_links: lichtste baan van de staart (de binnenrand is een donkere naad)


def textuur(lijf, A, refs, st):
    kl = bpy.data.images["koe_kleur"]
    w, h = kl.size
    basis = np.array(kl.pixels[:], np.float32).reshape(h, w, 4)
    pos, nrm, gezet = texels(lijf, w, h, 0)
    P, N = pos[gezet].astype(float), nrm[gezet].astype(float)
    # staart: per hoogte de kleur uit de staartbaan van de referentie (de vertices hangen er niet precies voor)
    L = st.punten
    d = np.full(len(P), 9.0)
    for i in range(len(L) - 1):
        ab = L[i + 1] - L[i]
        t = np.clip((P - L[i]) @ ab / (ab @ ab), 0, 1)
        d = np.minimum(d, np.linalg.norm(P - (L[i] + t[:, None] * ab), axis=1))
    staart = (d < 0.07) & (P[:, 2] < L[0][2] + 0.02)
    P[staart, 1] = (STAART_KOLOM - A.yc) * A.s
    P[staart, 0] = np.abs(P[staart, 0]) + 0.03          # beide kanten uit koe_links (rechts valt de staart buiten beeld)
    N[staart] = np.array([1.0, 0, 0])
    log("staart-texels", int(staart.sum()))
    rgb = zijkleur(A, refs["tr"], refs["links"][2], refs["rechts"][2], P, N, staart)
    rgb = voorkleur(lijf, refs["voor"], P, N, rgb)
    # wit: de staart (de baan in de referentie is half beschaduwd) en de achterkant rond de staart (koe_achter:
    # wit tussen de zwarte bilvlekken; de zijaanzichten zien daar alleen de vlek op de bil)
    a, m, _ = refs["links"]
    la = a @ np.array([0.2126, 0.7152, 0.0722], np.float32)
    wit = np.median(a[m & (la > 0.6)], axis=0)
    w_ach = np.clip((N[:, 1] - 0.35) / 0.3, 0, 1) * gladstap(0.13, 0.06, np.abs(pos[gezet][:, 0])) *         gladstap(0.35, 0.50, P[:, 2]) * gladstap(0.20, 0.35, P[:, 1])
    w_wit = np.maximum(w_ach, staart.astype(float))
    rgb = rgb * (1 - w_wit[:, None]) + wit[None] * w_wit[:, None]
    log("wit", np.round(wit, 3).tolist(), "achter-texels", int((w_ach > 0.5).sum()))
    # fijne ruis tegen strepen waar de projectie scheert
    fijn = BM.ruis(P, f=(140, 70, 140), seed=5)
    rgb = rgb * (1 + (0.03 + 0.06 * (1 - np.abs(N[:, 0]))) * fijn)[:, None]
    # buik en binnenkant: de referentie is daar beschaduwd, het spel schaduwt zelf al
    onder = np.clip(-N[:, 2], 0, 1) * gladstap(0.75, 0.35, P[:, 2])
    rgb = np.clip(rgb * GAIN * (1 + 0.30 * onder)[:, None], 0, 1)
    uit = basis[..., :3].copy()
    uit[gezet] = rgb
    m = gezet.copy()
    # naden: kleur over de UV-rand, maar niet over andere delen heen
    pos_all, _, gez_all = texels_alle(lijf, w, h)
    ext, _ = PJ.uitbreiden(np.where(m[..., None], uit, 0), m, 4)
    rand = (~m) & (ext.sum(-1) > 0) & (~gez_all)
    uit[rand] = ext[rand]
    img = bpy.data.images.new("koe_tripo_kleur", w, h)
    img.pixels.foreach_set(np.concatenate([uit, np.ones((h, w, 1), np.float32)], 2).ravel())
    img.pack()
    lum = rgb @ np.array([0.2126, 0.7152, 0.0722], np.float32)
    log("textuur", w, "x", h, "gezet", int(gezet.sum()), "lum p5/p50/p95", np.round(np.percentile(lum, [5, 50, 95]), 3).tolist())
    return img, gezet, lum


_ALLE = {}


def texels_alle(lijf, w, h):
    """Alle texels die een ander deel (uier, halsband, bel, ogen) gebruikt: daar niet overheen uitsmeren."""
    if "r" not in _ALLE:
        g = np.zeros((h, w), bool)
        for o in bpy.data.objects:
            if o.type != "MESH" or not o.data.uv_layers:
                continue
            for mi in range(len(o.data.materials)):
                if o == lijf and mi == 0:
                    continue
                g |= texels(o, w, h, mi)[2]
        _ALLE["r"] = (None, None, g)
    return _ALLE["r"]


GAIN = float(OPTS.get("gain", 1.0))


def orm(gezet, lum):
    """Ruwheid (G) van de lijf-texels uit de helderheid: zwart iets glanziger."""
    om = bpy.data.images["koe_orm"]
    w, h = om.size
    A = np.array(om.pixels[:], np.float32).reshape(h, w, 4)
    H, W = gezet.shape
    L = np.zeros((H, W), np.float32)
    L[gezet] = lum
    f = H // h
    g = gezet.reshape(h, f, w, f).mean((1, 3))
    l = L.reshape(h, f, w, f).sum((1, 3)) / np.maximum(g * f * f, 1)
    sel = g > 0.5
    A[sel, 1] = 0.62 + 0.22 * np.clip(l[sel] / 0.75, 0, 1)
    img = bpy.data.images.new("koe_tripo_orm", w, h)
    img.colorspace_settings.name = "Non-Color"
    img.pixels.foreach_set(A.ravel())
    img.pack()
    return img


def wissel_beelden(kleur, ormb):
    for m in bpy.data.materials:
        if not m.node_tree:
            continue
        for n in m.node_tree.nodes:
            if n.type == "TEX_IMAGE" and n.image is not None:
                if n.image.name == "koe_kleur":
                    n.image = kleur
                elif n.image.name == "koe_orm":
                    n.image = ormb
    ml = bpy.data.materials["mat_lijf"]
    for k in ("tint_vacht", "tint_vlek", "vlek_standaard", "vlek_masker"):
        if k in ml.keys():
            del ml[k]


# --- Controle en previews -------------------------------------------------------------------------------
CLIPS = ("idle", "lopen", "grazen", "gemolken_worden", "sterven", "geboorte")


def rust(rig):
    rig.animation_data_create().action = None
    for b in rig.pose.bones:
        b.rotation_quaternion = (1, 0, 0, 0)
        b.location = (0, 0, 0)
    bpy.context.view_layer.update()


def rek(o, rig, sc):
    E = np.zeros(len(o.data.edges) * 2, np.int64)
    o.data.edges.foreach_get("vertices", E)
    E = E.reshape(-1, 2)
    P0 = np.array([v.co for v in o.data.vertices])
    L0 = np.linalg.norm(P0[E[:, 0]] - P0[E[:, 1]], axis=1) + 1e-6
    uit = {}
    dg = bpy.context.evaluated_depsgraph_get()
    for act in CLIPS:
        R.zet_actie(rig, act)
        a = bpy.data.actions[act]
        slechtst = 0.0
        for f in range(int(a.frame_range[0]), int(a.frame_range[1]) + 1, 3):
            sc.frame_set(f)
            ev = o.evaluated_get(dg)
            m = ev.to_mesh()
            P = np.array([v.co for v in m.vertices])
            ev.to_mesh_clear()
            r = np.linalg.norm(P[E[:, 0]] - P[E[:, 1]], axis=1) / L0
            slechtst = max(slechtst, float(np.percentile(r, 99.9)))
        uit[act] = round(slechtst, 2)
    rust(rig)
    return uit


def toon(naam, aan):
    o = bpy.data.objects.get(naam)
    if o:
        o.hide_render = not aan


def zij_vergelijk(sc, rig, refs, A):
    rust(rig)
    toon("halsband", False)
    toon("bel", False)
    ppm = 1.0 / A.s
    rijen = []
    for naam, yaw in (("links", 0), ("rechts", 180)):
        ref = refs[naam][0]
        H, W = ref.shape[:2]
        yc, zc = A.ref_naar_m(np.array([[W / 2, H / 2]]))
        BM.studio(sc, ppm, W / ppm, H / ppm, doel=(0, float(yc[0]) * (1 if yaw == 0 else 1), float(zc[0])), yaw=yaw, pitch=0)
        sc.objects["cam"].data.ortho_scale = W / ppm
        a = BM.render_np(sc, os.path.join(bpy.app.tempdir, f"zij_{naam}.png"))
        if yaw == 180:
            a = a[:, ::-1]
        al = a[..., 3:]
        ons = a[..., :3] * al + 0.3 * (1 - al)
        rijen.append(np.concatenate([ref if yaw == 0 else ref[:, ::-1], ons if yaw == 0 else ons[:, ::-1]], 1))
    # voor- en achteraanzicht naast koe_voor / koe_achter, op de hoogte van het referentiesilhouet geschaald
    paneel = []
    for naam, yaw in (("koe_voor", 270), ("koe_achter", 90)):
        ref = BM.laad_np(os.path.join(REFD, naam + ".png"))[..., :3]
        m = segmenteer(ref)
        rr = np.nonzero(m.any(1))[0]
        H, W = ref.shape[:2]
        hoog = float(max(v.co.z for v in bpy.data.objects["lijf"].data.vertices))
        ppm = (rr.max() - rr.min()) / hoog
        BM.studio(sc, ppm, W / ppm, H / ppm, doel=(0, 0, hoog * 0.5 + (H / 2 - 0.5 * (rr.max() + rr.min())) / ppm),
                  yaw=yaw, pitch=0)
        sc.objects["cam"].data.ortho_scale = W / ppm
        a = BM.render_np(sc, os.path.join(bpy.app.tempdir, f"vo_{naam}.png"))
        al = a[..., 3:]
        paneel += [ref, a[..., :3] * al + 0.3 * (1 - al)]
    hh = max(p.shape[0] for p in paneel)
    paneel = [np.concatenate([p, np.full((hh - p.shape[0], p.shape[1], 3), 0.3, np.float32)], 0) for p in paneel]
    rijen.append(np.concatenate(paneel, 1))
    BM.schrijf(BM.onder(*rijen), os.path.join(UIT, "koe_tripo_zij.png"))


def poses(sc, rig):
    keuzes = [("idle", 0), ("lopen", 6), ("lopen", 18), ("grazen", 30), ("gemolken_worden", 20),
              ("sterven", 40), ("geboorte", 10)]
    rijen = []
    for yaw, pitch, bel in ((225, 30, True), (180, 6, False), (45, 30, False), (315, 60, False)):
        toon("halsband", bel)
        toon("bel", bel)
        panelen = []
        for act, f in keuzes:
            R.zet_actie(rig, act)
            sc.frame_set(f)
            BM.studio(sc, 140, 2.6, 1.9, doel=(0, -0.1, 0.6), yaw=yaw, pitch=pitch)
            panelen.append(BM.bijsnijden(BM.render_np(sc, os.path.join(bpy.app.tempdir, f"p_{act}_{f}.png"))))
        rijen.append(BM.plak(panelen))
    BM.schrijf(BM.onder(*rijen), os.path.join(UIT, "koe_tripo_poses.png"))
    rust(rig)


def ankers_beeld(A, ref):
    H = max(ref.shape[0], int(A.cs[:, 1].max()) + 5)
    links = np.ones((H, int(A.cs[:, 0].max()) + 5, 3), np.float32) * 0.85
    rechts = np.ones((H, ref.shape[1], 3), np.float32)
    rechts[:ref.shape[0]] = ref
    for c, img in ((A.cs, links), (A.cd, rechts)):
        for x, y in c.astype(int):
            img[np.clip(y, 0, H - 1), np.clip(x, 0, img.shape[1] - 1)] = (1, 0, 0)
    rng = np.random.default_rng(1)
    for i, p, j in A.ank:
        k = rng.random(3)
        q = A.cd[j] if j is not None else p
        for (x, y), img in ((A.cs[i], links), (q, rechts)):
            x, y = int(x), int(y)
            img[max(y - 3, 0):y + 4, max(x - 3, 0):x + 4] = k
    BM.schrijf(np.concatenate([links, rechts], 1), os.path.join(UIT, "koe_tripo_ankers.png"))


# --- Hoofdlijn ------------------------------------------------------------------------------------------
def main():
    bpy.ops.wm.open_mainfile(filepath=BLEND)
    sc = bpy.context.scene
    sc.render.fps = R.FPS
    sc.frame_start = 0
    rig = bpy.data.objects["koe_rig"]
    rust(rig)
    lijf, uier = bpy.data.objects["lijf"], bpy.data.objects["uier"]
    refs = {"links": referentie("koe_links"), "rechts": referentie("koe_rechts", spiegel=True),
            "voor": referentie("koe_voor")}
    mcut = refs["links"][1].copy()
    yy, xx = np.mgrid[0:mcut.shape[0], 0:mcut.shape[1]]
    rand = np.interp(yy, *STAART_RAND)
    mcut &= ~((yy >= STAART_RAND[0][0]) & (yy <= STAART_RAND[0][-1]) & (xx >= rand))
    mcut = ~PJ.grootste(~PJ.grootste(mcut), rand=True)
    P = np.array([v.co for v in lijf.data.vertices], float)
    T = driehoeken(lijf)
    T = T[staartgewicht(lijf)[T].max(1) < 0.3]
    A = Afbeelding(P, T, mcut)
    refs["tr"] = PJ.tps_fit(np.array([a for a, b in RECHTS], float), np.array([b for a, b in RECHTS], float), 2.0)
    if "ankers" in OPTS:
        ankers_beeld(A, refs["links"][0])
    st = Staart(A, rig)
    botten(rig, A, st)
    vervorm(lijf, A, st, tail=True)
    for n in ("uier", "halsband"):
        vervorm(bpy.data.objects[n], A, None)
    for a in list(bpy.data.actions):
        bpy.data.actions.remove(a)
    info = R.bouw_animaties(rig)
    json.dump(info, open(ANIM, "w"), indent=2)
    log("animaties", {k: v["snelheid_mps"] for k, v in info.items()})
    kleur, gezet, lum = textuur(lijf, A, refs, st)
    wissel_beelden(kleur, orm(gezet, lum))
    log("rek p99.9", rek(lijf, rig, sc))
    if "geen_export" not in OPTS:
        os.makedirs(ASSETS, exist_ok=True)
        BM.ontkies()
        for n in ("cam", "zon"):
            if n in bpy.data.objects:
                bpy.data.objects.remove(bpy.data.objects[n])
        for o in list(bpy.data.objects):
            if o.type == "MESH" and o.name not in ("lijf", "uier", "halsband", "bel"):
                bpy.data.objects.remove(o)
        bpy.ops.export_scene.gltf(filepath=GLB, export_format="GLB", export_animations=True,
                                  export_animation_mode="ACTIONS", export_force_sampling=True, export_yup=True,
                                  export_skins=True, export_def_bones=False, export_extras=True, use_selection=False,
                                  export_tangents=True, export_image_format="AUTO", export_cameras=False,
                                  export_lights=False)
        log("export", GLB, f"{os.path.getsize(GLB) / 1e6:.1f} MB")
    os.makedirs(UIT, exist_ok=True)
    if "zij" in OPTS:
        zij_vergelijk(sc, rig, refs, A)
    if "poses" in OPTS:
        poses(sc, rig)
    if "blend" in OPTS:
        bpy.ops.wm.save_as_mainfile(filepath=os.path.join(UIT, "koe_tripo.blend"))
    log("KLAAR")


if __name__ == "__main__":
    main()
