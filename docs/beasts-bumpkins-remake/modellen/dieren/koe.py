"""Koe (zwartbont), game-ready: mesh, skin, atlas, animaties -> koe.glb (Blender 5.2 headless -> Godot 4).

Draaien:
  blender -b -P koe.py -- [res=2048] [snel] [vergelijk] [poses] [lopen] [geen_export] [tag=_r1]
- `snel`: atlas 1024, weinig samples.
- `vergelijk`: preview/koe_vergelijk_1x.png (sprites naast de render op HD-pixelschaal, iso yaw 225,
  pitch 30) en preview/koe_vergelijk_close.png (concept naast close-ups). Bevatten de sprite: nooit
  committen.
- `poses`: preview/koe_poses.png (extreme standen uit alle clips, iso + van opzij).
- `lopen`: preview/koe_lopen_zij.png (8 frames van opzij op een vloer met streepjes: voetglijden).
Doel: concept/img/koe.jpg (zwartbont, Holstein-achtig; onderste rij = dorpskoe met leren halsband
en koperen bel).

Uitvoer koe.glb: armatuur `koe_rig` (koe_rig.py) met alle acties, losse delen op hetzelfde skelet,
een gedeelde atlas in textures_koe/ (koe_kleur.jpg, koe_normaal.png, koe_orm.png; R=AO G=ruw B=metaal).

DELEN (mesh-object = glTF-node, stabiele namen):
| deel     | inhoud                                          | materiaal        | tint (baseColorFactor)  |
| -------- | ----------------------------------------------- | ---------------- | ----------------------- |
| lijf     | romp, hals, kop, benen, hoeven, staart, oren    | mat_lijf         | #ffffff vacht (wit)     |
|          | de vlekken (eigen vlakken, langs de rand gesneden) | mat_vlek      | #262422 vlekken (zwart) |
|          | ogen (eigen vlakken: ook leesbaar in een zwarte kop) | mat_vast    | wit (echte kleur)       |
| uier     | uier met vier spenen                            | mat_uier         | #f0b9ae roze            |
| halsband | leren halsband, VERBORGEN (extras.verborgen)     | mat_halsband     | #6e4226 leer            |
| bel      | koperen bel + lus + klepel, kind van prop_bel, VERBORGEN | mat_vast | wit (echte kleur)    |
Tintbaar: de kleurtextuur is lichtgrijs (gemiddeld ~0,86) met het detail als luminantie (snuit roze,
hoeven en ogen donker, kwast crème, vuile onderbenen als relatieve tint); kleur = factor x textuur.
mat_lijf en mat_vlek delen dezelfde textuur: vachtvariant = twee factoren, bv. roodbont = vlek
#7a3b22, blaarkop = vlek zwart of rood met een witte kop (vereist een andere vlekkenkaart, niet nu).
halsband en bel staan in de glb maar met extras {"verborgen": true}: het spel zet ze bij het spawnen
onzichtbaar en toont ze als de koe van het dorp is.

Bouw: een signed distance field (numpy; afgeronde kegels en ellipsoïden langs de gewrichten van het
skelet, glad samengevoegd) -> surface nets (7 mm) = hoog-poly; gedecimeerd (symmetrisch) = laag-poly.
De vlekgrens is een 3D-veld; de laag-poly wordt langs de nullijn doorgesneden zodat elk vlak óf vacht
óf vlek is. Gewichten: bone heat (ARMATURE_AUTO), daarna oren/hoeven/kaak rechtgezet. Cycles bakt
normaal en AO van hoog naar laag; kleur en ruwheid komen er per texel bij uit een gebakken positiekaart.
"""
import math
import os
import sys
import time

import bmesh
import bpy
import numpy as np
from mathutils import Matrix, Vector
from mathutils.bvhtree import BVHTree

HERE = os.path.dirname(os.path.abspath(__file__))
MOD = os.path.dirname(HERE)
sys.path.insert(0, HERE)
import koe_rig as R  # noqa: E402
import dieren_basis as BM  # noqa: E402  (studio, ruis, pbr, plak ...: de helpers van de man, bevroren kopie)

argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
OPTS = {a.split("=")[0]: (a.split("=", 1)[1] if "=" in a else "1") for a in argv}
SNEL = "snel" in OPTS
RES = int(OPTS.get("res", 1024 if SNEL else 2048))
SPP = 0.25 if SNEL else 1.0
TEX = os.path.join(HERE, "textures_koe")
PREV = os.path.join(HERE, "preview")
GLB = os.path.join(HERE, "koe.glb")
SCRATCH = os.path.join(os.environ.get("TEMP", ""), "claude", "E--werk-androidApps-Apps",
                       "16e99493-ac86-47c7-921f-1d215c266f51", "scratchpad")
REF = OPTS.get("ref", SCRATCH)
T0 = time.time()
H_GRID = 0.007 if not SNEL else 0.010
DOEL_LIJF = 5300                    # driehoeken na decimeren (de vlekgrens snijdt er nog ~400 bij)
DELEN = ["lijf", "uier", "halsband", "bel"]
GRIJS = 0.86
TINT = {"lijf": "#ffffff", "vlek": "#262422", "uier": "#f0b9ae", "halsband": "#6e4226"}
srgb, naar_srgb, ruis, gladstap = BM.srgb, BM.naar_srgb, BM.ruis, BM.gladstap


def log(*a):
    print(f"[koe {time.time() - T0:6.1f}s]", *a, flush=True)


def nrm(v):
    v = np.asarray(v, float)
    return v / (np.linalg.norm(v) + 1e-12)


# --- SDF ------------------------------------------------------------------------------------------
def smin(a, b, k):
    h = np.maximum(k - np.abs(a - b), 0) / k
    return np.minimum(a, b) - h * h * k * 0.25


def smax(a, b, k):
    return -smin(-a, -b, k)


def sd_rondkegel(P, a, b, r1, r2):
    """Afgeronde kegel tussen a (straal r1) en b (straal r2), exact (Quilez)."""
    ba = b - a
    l2 = ba @ ba
    rr = r1 - r2
    a2 = l2 - rr * rr
    il2 = 1.0 / l2
    pa = P - a
    y = pa @ ba
    z = y - l2
    q = pa * l2 - y[:, None] * ba
    x2 = np.einsum("ij,ij->i", q, q)
    y2 = y * y * l2
    z2 = z * z * l2
    k = np.sign(rr) * rr * rr * x2
    d = (np.sqrt(np.maximum(x2 * a2 * il2, 0)) + y * rr) * il2 - r1
    d = np.where(np.sign(y) * a2 * y2 < k, np.sqrt(x2 + y2) * il2 - r1, d)
    d = np.where(np.sign(z) * a2 * z2 > k, np.sqrt(x2 + z2) * il2 - r2, d)
    return d


def sd_ellips(P, c, assen, r):
    L = (P - c) @ assen.T                     # lokale coördinaten
    k0 = np.linalg.norm(L / r, axis=1)
    k1 = np.linalg.norm(L / (r * r), axis=1)
    return k0 * (k0 - 1.0) / np.maximum(k1, 1e-9)


class SDF:
    """Lijst primitieven met een AABB elk; d(P) = gladde unie (of aftrek) in volgorde."""

    def __init__(self):
        self.prims = []

    def rc(self, a, b, r1, r2, k=0.03, m="+"):
        a, b = np.asarray(a, float), np.asarray(b, float)
        rm = max(r1, r2) + k
        self.prims.append(("rc", (a, b, r1, r2), np.minimum(a, b) - rm, np.maximum(a, b) + rm, k, m))

    def el(self, c, r, k=0.03, m="+", assen=None):
        c = np.asarray(c, float)
        r = np.asarray(r, float)
        A = np.eye(3) if assen is None else np.asarray(assen, float)
        rm = r.max() + k
        self.prims.append(("el", (c, A, r), c - rm, c + rm, k, m))

    def __call__(self, P, grond=True):
        P = np.asarray(P, float)
        d = np.full(len(P), 1.0)
        for soort, arg, lo, hi, k, m in self.prims:
            sel = np.all((P >= lo) & (P <= hi), axis=1)
            if not sel.any():
                continue
            Q = P[sel]
            v = sd_rondkegel(Q, *arg) if soort == "rc" else sd_ellips(Q, *arg)
            d[sel] = smin(d[sel], v, k) if m == "+" else smax(d[sel], -v, k)
        if grond:
            d = np.maximum(d, -P[:, 2])          # hoeven plat op z=0
        return d

    def grens(self):
        lo = np.min([p[2] for p in self.prims if p[5] == "+"], 0)
        hi = np.max([p[3] for p in self.prims if p[5] == "+"], 0)
        return lo, hi


def oppervlak(sdf, h, naam, coll, symm=True):
    """Surface nets op een rooster met stap h -> mesh-object (op het oppervlak geprojecteerd)."""
    lo, hi = sdf.grens()
    lo = lo - 2 * h
    hi = hi + 2 * h
    lo[2] = max(lo[2], -2.5 * h)                # z=0 niet op een roosterpunt (anders naalden)
    if symm:
        xm = max(-lo[0], hi[0])
        lo[0], hi[0] = -xm, xm
    n = np.ceil((hi - lo) / h).astype(int) + 1
    if symm and n[0] % 2 == 0:
        n[0] += 1
    xs = [lo[i] + h * np.arange(n[i]) for i in range(3)]
    if symm:
        xs[0] = h * (np.arange(n[0]) - (n[0] - 1) / 2)
    F = np.empty(n, np.float32)
    YZ = np.stack(np.meshgrid(xs[1], xs[2], indexing="ij"), -1).reshape(-1, 2)
    for i, x in enumerate(xs[0]):
        P = np.column_stack([np.full(len(YZ), x), YZ])
        F[i] = sdf(P).reshape(n[1], n[2])
    log(naam, "rooster", tuple(n), f"{F.size / 1e6:.1f}M")
    cel = np.full(tuple(n - 1), -1, np.int64)
    som = np.zeros(tuple(n - 1) + (3,))
    aantal = np.zeros(tuple(n - 1))
    binnen = F < 0
    kanten = []
    for ax in range(3):
        sl0 = [slice(None)] * 3
        sl1 = [slice(None)] * 3
        sl0[ax] = slice(0, -1)
        sl1[ax] = slice(1, None)
        f0, f1 = F[tuple(sl0)], F[tuple(sl1)]
        kr = binnen[tuple(sl0)] != binnen[tuple(sl1)]
        idx = np.argwhere(kr)
        t = f0[kr] / (f0[kr] - f1[kr])
        pt = idx.astype(float)
        pt[:, ax] += t
        kanten.append((ax, idx, binnen[tuple(sl0)][kr]))
        o1, o2 = [a for a in range(3) if a != ax]
        for d1 in (0, 1):
            for d2 in (0, 1):
                c = idx.copy()
                c[:, o1] -= d1
                c[:, o2] -= d2
                ok = (c[:, o1] >= 0) & (c[:, o2] >= 0) & (c[:, o1] < n[o1] - 1) & (c[:, o2] < n[o2] - 1) & \
                     (c[:, ax] < n[ax] - 1)
                np.add.at(som, (c[ok, 0], c[ok, 1], c[ok, 2]), pt[ok])
                np.add.at(aantal, (c[ok, 0], c[ok, 1], c[ok, 2]), 1)
    act = aantal > 0
    cel[act] = np.arange(act.sum())
    V = som[act] / aantal[act][:, None]
    V = np.column_stack([xs[0][0] + V[:, 0] * h, xs[1][0] + V[:, 1] * h, xs[2][0] + V[:, 2] * h])
    vlakken = []
    for ax, idx, inn in kanten:
        o1, o2 = [a for a in range(3) if a != ax]
        ok = (idx[:, o1] >= 1) & (idx[:, o2] >= 1) & (idx[:, o1] <= n[o1] - 2) & (idx[:, o2] <= n[o2] - 2)
        idx, inn = idx[ok], inn[ok]
        hoek = []
        for d1, d2 in ((1, 1), (0, 1), (0, 0), (1, 0)):
            c = idx.copy()
            c[:, o1] -= d1
            c[:, o2] -= d2
            hoek.append(cel[c[:, 0], c[:, 1], c[:, 2]])
        Q = np.stack(hoek, 1)
        Q[~inn] = Q[~inn][:, ::-1]
        vlakken.append(Q)
    Q = np.concatenate(vlakken)
    Q = Q[(Q >= 0).all(1)]
    # projecteren op het oppervlak (Newton langs de gradiënt)
    e = h * 0.3
    for _ in range(3):
        d = sdf(V)
        g = np.column_stack([(sdf(V + np.array(o)) - d) / e for o in ((e, 0, 0), (0, e, 0), (0, 0, e))])
        g /= np.maximum((g * g).sum(1, keepdims=True), 1e-9)
        V = V - np.clip(d, -h, h)[:, None] * g
    V[:, 2] = np.maximum(V[:, 2], 0.0)
    me = bpy.data.meshes.new(naam)
    me.from_pydata(V.tolist(), [], Q.tolist())
    me.update()
    o = bpy.data.objects.new(naam, me)
    coll.objects.link(o)
    bm = bmesh.new()
    bm.from_mesh(me)
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=h * 0.05)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bm.to_mesh(me)
    bm.free()
    me.shade_smooth()
    log(naam, "hoog", len(me.vertices), "vertices", len(me.polygons), "vlakken")
    return o


# --- Vorm: primitieven langs het skelet ---------------------------------------------------------------
class Skelet:
    def __init__(self, rig):
        bn = rig.data.bones
        self.J = {b.name: np.array(b.head_local) for b in bn}
        self.T = {b.name: np.array(b.tail_local) for b in bn}
        self.s = float(rig.get("schaal", 1.0))


def kop_assen(sk):
    """Kopframe: d = langs de kop (naar de snuit), u = buikzijde (naar achter-onder), x opzij."""
    d = nrm(sk.T["Head"] - sk.J["Head"])
    u = nrm(np.array([0.0, -d[2], d[1]]))
    if u[2] > 0:
        u = -u
    return d, u


def vorm_lijf(sk):
    s, J, T = sk.s, sk.J, sk.T
    V = lambda x, y, z: np.array((x, y, z)) * s
    S = SDF()
    # romp
    S.el(V(0, -0.36, 0.82), np.array((0.24, 0.22, 0.31)) * s, k=0.10 * s)
    S.el(V(0, -0.02, 0.81), np.array((0.29, 0.38, 0.31)) * s, k=0.12 * s)
    S.el(V(0, 0.30, 0.84), np.array((0.28, 0.26, 0.25)) * s, k=0.10 * s)
    S.el(V(0, 0.47, 0.91), np.array((0.22, 0.14, 0.17)) * s, k=0.08 * s)
    S.rc(V(0, -0.48, 1.03), V(0, 0.52, 1.02), 0.10 * s, 0.10 * s, k=0.12 * s)          # rugbalk (vlakke rug)
    S.el(V(0, -0.44, 1.04), np.array((0.10, 0.15, 0.06)) * s, k=0.08 * s)             # schoft
    for sg in (1, -1):
        S.el(V(sg * 0.18, 0.34, 1.02), np.array((0.065, 0.07, 0.055)) * s, k=0.07 * s)  # heupknobbel
        S.el(V(sg * 0.085, 0.585, 0.98), np.array((0.05, 0.05, 0.05)) * s, k=0.05 * s)  # zitbeenknobbel
    # staart (wortel glad aan de romp, de rest los)
    S.rc(V(0, 0.52, 1.03), J["Tail"], 0.07 * s, 0.05 * s, k=0.05 * s)
    S.rc(J["Tail"], J["Tail1"], 0.05 * s, 0.034 * s, k=0.03 * s)
    S.rc(J["Tail1"], J["Tail2"], 0.034 * s, 0.026 * s, k=0.008 * s)
    S.rc(J["Tail2"], J["Tail3"], 0.026 * s, 0.022 * s, k=0.008 * s)
    td = nrm(T["Tail3"] - J["Tail3"])
    ax = np.array([[1, 0, 0], nrm(np.cross(td, [1, 0, 0])), td])
    S.el(J["Tail3"] + td * 0.13 * s, np.array((0.05, 0.042, 0.15)) * s, k=0.02 * s, assen=ax)   # kwast
    # hals + kwab
    S.rc(V(0, -0.40, 0.88), V(0, -0.91, 1.12), 0.23 * s, 0.13 * s, k=0.10 * s)
    S.rc(V(0, -0.45, 1.04), V(0, -0.91, 1.19), 0.08 * s, 0.075 * s, k=0.08 * s)
    S.el(V(0, -0.63, 0.74), np.array((0.045, 0.15, 0.10)) * s, k=0.06 * s)
    # kop
    d, u = kop_assen(sk)
    H0, H1 = J["Head"], T["Head"]
    KA = np.array([[1, 0, 0], d, u])
    S.el(H0 + d * 0.07 * s, np.array((0.135, 0.115, 0.125)) * s, k=0.05 * s, assen=KA)     # schedel
    S.rc(H0 + d * 0.06 * s, H1 - d * 0.06 * s, 0.115 * s, 0.088 * s, k=0.04 * s)          # gezicht
    S.el(H1 - d * 0.035 * s + u * 0.005 * s, np.array((0.107, 0.072, 0.082)) * s, k=0.03 * s, assen=KA)  # snuit
    S.rc(J["Jaw"], T["Jaw"], 0.07 * s, 0.045 * s, k=0.04 * s)                              # onderkaak
    for sg in (1, -1):
        S.el(J["Jaw"] + V(sg * 0.055, 0.0, 0.01), np.array((0.05, 0.08, 0.08)) * s, k=0.04 * s)   # wang
        S.el(H0 + d * 0.13 * s + np.array((sg * 0.093 * s, 0, 0)) - u * 0.025 * s, np.array((0.026,) * 3) * s,
             k=0.010 * s)                                                                    # oog
        S.el(H0 + d * 0.118 * s + np.array((sg * 0.098 * s, 0, 0)) - u * 0.05 * s,
             np.array((0.026, 0.02, 0.012)) * s, k=0.012 * s, assen=KA)                     # wenkbrauwboog
        S.el(H1 + d * 0.025 * s - u * 0.03 * s + np.array((sg * 0.034 * s, 0, 0)),
             np.array((0.016,) * 3) * s, k=0.008 * s, m="-")                                # neusgat
        # oor: plat blad met een kom aan de voorkant, steel in de kop
        eb = ("Left" if sg > 0 else "Right") + "Ear"
        ea, ee = J[eb], T[eb]
        e = nrm(ee - ea)
        t = nrm(np.array([0, -1.0, 0]) - e * e[1] * -1)
        w = nrm(np.cross(e, t))
        t = np.cross(w, e)
        OA = np.array([e, w, t])
        mid = ea + (ee - ea) * 0.55
        S.rc(ea - e * 0.02 * s, mid, 0.035 * s, 0.028 * s, k=0.02 * s)
        S.el(mid, np.array((0.105, 0.068, 0.022)) * s, k=0.012 * s, assen=OA)
        S.el(mid + t * 0.016 * s + e * 0.01 * s, np.array((0.085, 0.05, 0.013)) * s, k=0.006 * s, m="-", assen=OA)
    S.el(H0 + np.array((0, 0, 0.10 * s)) + d * 0.02 * s, np.array((0.075, 0.05, 0.04)) * s, k=0.03 * s)  # kuif
    # voorbenen
    for z, sg in (("Left", 1), ("Right", -1)):
        b = lambda n: z + n
        sh, el_, kn, ko, te = J[b("UpperArm")], J[b("ForeArm")], J[b("FrontCannon")], J[b("FrontHoof")], T[b("FrontHoof")]
        S.el(sh + V(-sg * 0.02, 0.03, 0.06), np.array((0.10, 0.15, 0.19)) * s, k=0.08 * s)   # schouder
        S.rc(sh, el_, 0.12 * s, 0.09 * s, k=0.06 * s)
        S.el(el_ + V(0, 0.02, 0.0), np.array((0.055,) * 3) * s, k=0.04 * s)                  # elleboog
        S.rc(el_, kn, 0.09 * s, 0.056 * s, k=0.04 * s)
        S.el(kn, np.array((0.055, 0.052, 0.06)) * s, k=0.025 * s)                            # voorknie
        poot(S, kn, ko, te, s, V)
    # achterbenen
    for z, sg in (("Left", 1), ("Right", -1)):
        b = lambda n: z + n
        hp, kn, hak, ko, te = J[b("Thigh")], J[b("Shin")], J[b("HindCannon")], J[b("HindHoof")], T[b("HindHoof")]
        S.rc(hp + V(0, 0, 0.03), kn, 0.17 * s, 0.10 * s, k=0.08 * s)                         # dij
        S.el((hp + kn) / 2 + V(sg * 0.02, 0.03, 0), np.array((0.12, 0.17, 0.20)) * s, k=0.08 * s)
        S.rc(kn, hak, 0.11 * s, 0.056 * s, k=0.05 * s)                                       # scheen
        S.el(kn + (hak - kn) * 0.3 + V(0, 0.025, 0), np.array((0.075, 0.07, 0.10)) * s, k=0.06 * s)
        S.rc(hak, hak + V(0, 0.04, 0.03), 0.036 * s, 0.028 * s, k=0.02 * s)                   # hakknobbel
        S.el(hak, np.array((0.047, 0.05, 0.05)) * s, k=0.025 * s)
        poot(S, hak, ko, te, s, V)
    return S


def poot(S, boven, ko, te, s, V):
    """Pijp, kogel, koot en klauw (afgekapt op de grond)."""
    S.rc(boven, ko, 0.05 * s, 0.046 * s, k=0.018 * s)
    S.el(ko + V(0, 0.008, 0), np.array((0.05, 0.053, 0.05)) * s, k=0.018 * s)
    hm = ko + (te - ko) * 0.5
    g0 = np.array((te[0], te[1] + 0.05 * s, -0.01 * s))
    S.rc(ko, hm, 0.043 * s, 0.042 * s, k=0.015 * s)
    S.rc(hm, g0, 0.046 * s, 0.058 * s, k=0.012 * s)


def vorm_uier(sk):
    s = sk.s
    V = lambda x, y, z: np.array((x, y, z)) * s
    S = SDF()
    S.el(V(0, 0.29, 0.52), np.array((0.12, 0.15, 0.10)) * s, k=0.04 * s)
    S.el(V(0, 0.29, 0.60), np.array((0.10, 0.14, 0.07)) * s, k=0.05 * s)
    for x in (0.055, -0.055):
        for y in (0.22, 0.36):
            S.rc(V(x, y, 0.45), V(x * 1.1, y, 0.375), 0.017 * s, 0.013 * s, k=0.015 * s)
    return S


# --- Vlekken --------------------------------------------------------------------------------------
VLEKKEN = [  # (midden, stralen) in basismaat; vrij naar het concept (links en rechts verschillen)
    ((0.0, -0.60, 1.00), (0.42, 0.30, 0.28)),     # hals en schouders
    ((0.20, -0.44, 0.74), (0.13, 0.15, 0.22)),    # linkerschouder tot de elleboog
    ((-0.19, -0.46, 0.76), (0.12, 0.14, 0.20)),   # rechterschouder tot de elleboog
    ((0.22, 0.30, 0.93), (0.10, 0.11, 0.10)),     # heup/flank links, klein
    ((0.0, 0.53, 1.02), (0.14, 0.08, 0.06)),      # bovenop het kruis
    ((0.30, -0.02, 0.93), (0.22, 0.24, 0.20)),    # flank links
    ((-0.30, 0.10, 0.90), (0.22, 0.28, 0.21)),    # flank rechts
    ((0.08, 0.02, 1.09), (0.26, 0.19, 0.13)),     # zadel over de rug (loopt over de ruglijn)
    ((0.0, 0.40, 1.05), (0.28, 0.11, 0.10)),      # heup
    ((0.20, 0.52, 0.86), (0.10, 0.12, 0.17)),     # dij links achter
    ((-0.20, 0.50, 0.83), (0.11, 0.13, 0.19)),    # dij rechts achter
]


def vlekveld(P, sk):
    """> 0 = zwart. Ellipsoïdes + ruis; kop zwart met witte bles en witte snuit; benen, buik, staart wit."""
    s = sk.s
    Q = np.asarray(P, float) / s
    # domein-vervorming: rafelige randen zoals het concept (geen ronde vlekken)
    W = np.column_stack([ruis(Q, 2.5, 21 + i, 2) for i in range(3)]) * 0.10 +         np.column_stack([ruis(Q, 7.0, 31 + i) for i in range(3)]) * 0.035
    Qw = Q + W
    f = np.full(len(Q), -1.0)
    for c, r in VLEKKEN:
        f = np.maximum(f, 1 - np.linalg.norm((Qw - np.array(c)) / np.array(r), axis=1))
    # kop
    d, u = kop_assen(sk)
    H0, H1 = sk.J["Head"] / s, sk.T["Head"] / s
    t = np.clip((Q - H0) @ (H1 - H0) / np.sum((H1 - H0) ** 2), 0, 1)
    afst = np.linalg.norm(Q - (H0 + t[:, None] * (H1 - H0)), axis=1)
    kop = 1 - afst / 0.19
    for z in ("Left", "Right"):                         # oren zwart
        ea, ee = sk.J[z + "Ear"] / s, sk.T[z + "Ear"] / s
        te = np.clip((Q - ea) @ (ee - ea) / np.sum((ee - ea) ** 2), 0, 1)
        kop = np.maximum(kop, 1 - np.linalg.norm(Q - (ea + te[:, None] * (ee - ea)), axis=1) / 0.09)
    voorkant = -(Q - H0) @ u                            # > 0 aan de bles-kant
    bles = (np.abs(Q[:, 0]) < 0.034 + 0.022 * t + 0.006 * ruis(Q, 6, 5)) & (voorkant > 0.0)
    kop = np.where(bles, -1.0, kop)
    snuit = np.linalg.norm(Q - (H1 - d * 0.04 + u * 0.02), axis=1) < 0.11
    kop = np.where(snuit, -1.0, kop)
    f = np.maximum(f, kop * 2)
    f = f + 0.18 * ruis(Q, 3.0, 11) + 0.08 * ruis(Q, 7, 12) + 0.04 * ruis(Q, 16, 13)
    # wit: onderbenen, buik, staart, kwast
    romp = (Q[:, 1] > -0.75) & (Q[:, 1] < 0.66)
    f -= 3 * gladstap(0.60, 0.50, Q[:, 2]) * romp
    f -= 3 * (Q[:, 1] > 0.64) * (Q[:, 2] < 1.0)
    f -= 3 * gladstap(0.62, 0.52, Q[:, 2]) * (np.abs(Q[:, 0]) < 0.2)
    return f


def snij_langs(bm, P_fn, naam):
    """Snijdt bm langs veld = 0 (randen gesplitst, vlakken opgedeeld). Geeft de vertex-laag met het veld."""
    lay = bm.verts.layers.float.new(naam)
    P = np.array([v.co for v in bm.verts])
    f = P_fn(P)
    f[np.abs(f) < 1e-5] = 1e-5
    for v, fv in zip(bm.verts, f):
        v[lay] = fv
    nieuw = set()
    for e in list(bm.edges):
        a, b = e.verts
        fa, fb = a[lay], b[lay]
        if fa * fb < 0:
            t = fa / (fa - fb)
            co = a.co.lerp(b.co, t)
            ne, nv = bmesh.utils.edge_split(e, a, t)
            nv.co = co
            nv[lay] = 0.0
            nieuw.add(nv)
    for fc in list(bm.faces):
        vs = [v for v in fc.verts if v in nieuw]
        if len(vs) == 2 and not any(vs[1] in (l.link_loop_next.vert, l.link_loop_prev.vert)
                                    for l in vs[0].link_loops if l.face == fc):
            try:
                bmesh.utils.face_split(fc, vs[0], vs[1])
            except ValueError:
                pass
    bmesh.ops.triangulate(bm, faces=[f_ for f_ in bm.faces if len(f_.verts) > 3])
    bmesh.ops.dissolve_degenerate(bm, dist=1e-5, edges=bm.edges)
    bm.faces.ensure_lookup_table()
    bm.faces.index_update()
    return lay


def oogveld(P, sk):
    """> 0 binnen de ogen (eigen vlakken, mat_vast: echte oogkleur ook in een zwarte kop)."""
    s = sk.s
    d, u = kop_assen(sk)
    H0 = sk.J["Head"]
    f = np.full(len(P), -1.0)
    for sg in (1, -1):
        c = H0 + (d * 0.13 + np.array((sg * 0.093, 0, 0)) - u * 0.025) * s
        f = np.maximum(f, 0.024 * s - np.linalg.norm(P - c, axis=1))
    return f


def snij_vlekken(o, sk):
    """Snijdt de mesh langs vlekveld = 0 en de oogranden; material_index 0 vacht, 1 vlek, 2 oog (vast)."""
    bm = bmesh.new()
    bm.from_mesh(o.data)
    lay = snij_langs(bm, lambda P: vlekveld(P, sk), "vlek")
    for fc in bm.faces:
        m = np.mean([v[lay] for v in fc.verts])
        fc.material_index = 1 if m > 0 else 0
    # losse spikkels (eilanden van < 8 vlakken) omzetten: die flikkeren op afstand
    gezien = set()
    for fc in bm.faces:
        if fc.index in gezien:
            continue
        eiland, rand = [fc], [fc]
        gezien.add(fc.index)
        while rand:
            f_ = rand.pop()
            for e in f_.edges:
                for g in e.link_faces:
                    if g.index not in gezien and g.material_index == fc.material_index:
                        gezien.add(g.index)
                        eiland.append(g)
                        rand.append(g)
        if len(eiland) < 20:
            for f_ in eiland:
                f_.material_index = 1 - f_.material_index
    lay2 = snij_langs(bm, lambda P: oogveld(P, sk), "oog")
    for fc in bm.faces:
        if np.mean([v[lay2] for v in fc.verts]) > 0:
            fc.material_index = 2
    bm.to_mesh(o.data)
    bm.free()
    o.data.validate(verbose=False)


# --- Halsband en bel -----------------------------------------------------------------------------------
def maak_halsband(sk, sdf, rig):
    """Leren band om de hals vlak achter de kop, loodrecht op de hals; de straal rondom komt uit het SDF
    (van binnen naar buiten gezocht). Zet daarna het bot prop_bel onder op de band. Geeft het object."""
    s = sk.s
    nb, ne = sk.J["Neck1"], sk.T["Neck1"]
    a = nrm(ne - nb)
    m = nb + (ne - nb) * 0.2
    e1 = np.array([1.0, 0, 0])
    e2 = nrm(np.cross(a, e1))
    n = 20
    w, dik = 0.05 * s, 0.011 * s

    def straal(o_, r):
        lo, hi = 0.0, 0.5 * s
        for _ in range(30):
            mid = (lo + hi) / 2
            if sdf(np.array([o_ + r * mid]), grond=False)[0] < 0:
                lo = mid
            else:
                hi = mid
        return lo

    rich, rad = [], []
    for i in range(n):
        th = 2 * math.pi * i / n
        r = math.cos(th) * e1 + math.sin(th) * e2
        rich.append(r)
        rad.append(max(straal(m + a * off, r) for off in (-w / 2, 0, w / 2)) + 0.003 * s)
    rad = np.array(rad)
    rad = (np.roll(rad, 1) + 2 * rad + np.roll(rad, -1)) / 4
    B = BM.Bouwer()
    prof = [(-w / 2, 0.0), (w / 2, 0.0), (w / 2, dik), (-w / 2, dik), (-w / 2, 0.0)]
    rows = [[m + a * off + rich[i] * (rad[i] + uit) for i in range(n)] for off, uit in prof]
    B.grid(np.array(rows), True)
    o = B.obj("halsband", bpy.context.scene.collection)
    # bel-socket: onderste punt van de band, aan de buitenkant
    buiten = np.array([m + rich[i] * (rad[i] + dik) for i in range(n)])
    onder = buiten[np.argmin(buiten[:, 2])] + np.array([0, 0, -0.004 * s])
    BM.ontkies()
    bpy.context.view_layer.objects.active = rig
    rig.select_set(True)
    bpy.ops.object.mode_set(mode="EDIT")
    eb = rig.data.edit_bones["prop_bel"]
    eb.head = Vector(onder)
    eb.tail = Vector(onder - np.array([0, 0, 0.06 * s]))
    eb.align_roll(R.VOOR)
    bpy.ops.object.mode_set(mode="OBJECT")
    sk.J["prop_bel"] = onder
    return o


def maak_bel(sk, rig):
    """Koperen bel (draaiprofiel), lus en klepel; gebouwd in de botruimte van prop_bel (+Y = omlaag).
    Hoogte ~0,15 m zoals in het concept (zichtbaar op 22 px/m)."""
    s = sk.s * 1.35
    B = BM.Bouwer()
    prof = [(0.012, 0.000), (0.026, 0.006), (0.034, 0.025), (0.040, 0.055), (0.047, 0.085), (0.054, 0.100),
            (0.050, 0.104), (0.043, 0.092), (0.036, 0.060), (0.030, 0.030), (0.020, 0.012), (0.004, 0.010)]
    n = 14
    rows = []
    for r, y in prof:
        th = 2 * np.pi * np.arange(n) / n
        # lokaal: Y = omlaag (as van de bel), X/Z = rondom; bel iets afgeplat (Zwitserse bel)
        rows.append(np.column_stack([r * s * np.cos(th) * 1.0, np.full(n, (y + 0.018) * s), r * s * np.sin(th) * 0.78]))
    b0, _ = B.grid(np.array(rows), True, regio=0, buiten=None)
    B.kap(b0, n, (0, 0.016 * s, 0), regio=0)
    # lus bovenop: halve torus in het XY-vlak, boven de bel (-Y)
    R_, r_ = 0.016 * s, 0.0035 * s
    rows = [[(R_ * math.cos(t_) + r_ * math.cos(t_) * math.cos(ph), -(R_ * math.sin(t_) + r_ * math.sin(t_) * math.cos(ph)),
              r_ * math.sin(ph)) for ph in 2 * np.pi * np.arange(6) / 6] for t_ in np.linspace(0, math.pi, 8)]
    B.grid(np.array(rows), True, regio=1)
    # klepel
    k = [ring((0, (0.06 + 0.04 * i / 4) * s, 0), 0.006 * s * (1 + (i == 4)), 6) for i in range(5)]
    b1, _ = B.grid(np.array(k), True, regio=1)
    B.kap(b1 + 6 * 4, 6, (0, 0.11 * s, 0), regio=1)
    o = B.obj("bel", bpy.context.scene.collection)
    bm = bmesh.new()
    bm.from_mesh(o.data)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bm.to_mesh(o.data)
    bm.free()
    return o


def ring(c, r, n):
    th = 2 * np.pi * np.arange(n) / n
    return np.column_stack([c[0] + r * np.cos(th), np.full(n, c[1]), c[2] + r * np.sin(th)])


# --- Laag-poly ----------------------------------------------------------------------------------------
def decimeer(hoog, naam, doel, coll):
    o = hoog.copy()
    o.data = hoog.data.copy()
    o.name = o.data.name = naam
    coll.objects.link(o)
    o.data.calc_loop_triangles()
    n = len(o.data.loop_triangles)
    m = o.modifiers.new("dec", "DECIMATE")
    m.decimate_type = "COLLAPSE"
    m.ratio = doel / n
    m.use_symmetry = True
    m.symmetry_axis = "X"
    BM.ontkies()
    bpy.context.view_layer.objects.active = o
    o.select_set(True)
    bpy.ops.object.modifier_apply(modifier="dec")
    bm = bmesh.new()
    bm.from_mesh(o.data)
    bmesh.ops.triangulate(bm, faces=bm.faces)
    bmesh.ops.dissolve_degenerate(bm, dist=1e-5, edges=bm.edges)
    bm.to_mesh(o.data)
    bm.free()
    o.data.validate(verbose=False)
    return o


def driehoeken(objs):
    n = 0
    for o in objs:
        o.data.calc_loop_triangles()
        n += len(o.data.loop_triangles)
    return n


# --- UV en bakken ---------------------------------------------------------------------------------------
def uv_atlas(delen):
    BM.ontkies()
    for o in delen.values():
        me = o.data
        while me.uv_layers:
            me.uv_layers.remove(me.uv_layers[0])
        me.uv_layers.new(name="UVMap")
        o.select_set(True)
    bpy.context.view_layer.objects.active = delen["lijf"]
    bpy.ops.object.mode_set(mode="EDIT")
    bpy.ops.mesh.select_all(action="SELECT")
    bpy.ops.uv.smart_project(angle_limit=math.radians(58), island_margin=0.0, area_weight=0.0,
                             correct_aspect=True, scale_to_bounds=False)
    bpy.ops.uv.select_all(action="SELECT")
    bpy.ops.uv.average_islands_scale()
    bpy.ops.uv.pack_islands(rotate=True, margin=0.004, scale=True, shape_method="CONCAVE")
    bpy.ops.object.mode_set(mode="OBJECT")
    # meter per texel per deel
    mpp = {}
    for naam, o in delen.items():
        me = o.data
        me.calc_loop_triangles()
        uv = np.zeros(len(me.loops) * 2)
        me.uv_layers[0].data.foreach_get("uv", uv)
        uv = uv.reshape(-1, 2)
        a3 = a2 = 0.0
        for t in me.loop_triangles:
            p = [np.array(me.vertices[i].co) for i in t.vertices]
            q = [uv[l] for l in t.loops]
            a3 += 0.5 * np.linalg.norm(np.cross(p[1] - p[0], p[2] - p[0]))
            a2 += 0.5 * abs(np.cross(q[1] - q[0], q[2] - q[0]))
        mpp[naam] = math.sqrt(a3 / max(a2, 1e-12)) / RES
    return mpp


def bak_mat(naam, soort, deel_id=0):
    m = bpy.data.materials.new(naam)
    m.use_nodes = True
    nt = m.node_tree
    out = nt.nodes["Material Output"]
    if soort in ("pos", "id"):
        em = nt.nodes.new("ShaderNodeEmission")
        if soort == "pos":
            g = nt.nodes.new("ShaderNodeNewGeometry")
            nt.links.new(g.outputs["Position"], em.inputs["Color"])
        else:
            em.inputs["Color"].default_value = ((deel_id + 1) / 8.0, 1.0, 0.0, 1.0)
        nt.links.new(em.outputs[0], out.inputs["Surface"])
    tn = nt.nodes.new("ShaderNodeTexImage")
    nt.nodes.active = tn
    return m


def bak(doel, highs, soort, img, ext=0.01, ray=0.03, margin=4, clear=False):
    sc = bpy.context.scene
    for m in doel.data.materials:
        m.node_tree.nodes.active.image = img
    BM.ontkies()
    for h in highs:
        h.select_set(True)
    doel.select_set(True)
    bpy.context.view_layer.objects.active = doel
    kw = dict(use_clear=clear, margin=margin, margin_type="EXTEND", target="IMAGE_TEXTURES")
    if soort in ("pos", "id"):
        sc.cycles.samples = 1
        kw.update(type="EMIT", use_selected_to_active=False)
    else:
        kw.update(use_selected_to_active=bool(highs), cage_extrusion=ext, max_ray_distance=ray)
        if soort == "normaal":
            sc.cycles.samples = max(1, int(16 * SPP))
            kw.update(type="NORMAL", normal_space="TANGENT", normal_r="POS_X", normal_g="POS_Y", normal_b="POS_Z")
        else:
            sc.cycles.samples = max(4, int(128 * SPP))
            kw.update(type="AO")
    bpy.ops.object.bake(**kw)


def bak_alles(delen, highs, sk):
    sc = bpy.context.scene
    sc.render.engine = "CYCLES"
    log("cycles op", BM.gpu(sc))
    sc.world = sc.world or bpy.data.worlds.new("w")
    sc.world.light_settings.distance = 0.15 * sk.s
    beelden = {k: BM.beeld("_" + k, RES) for k in ("pos", "id", "normaal", "ao")}
    eerst = True
    for i, (naam, o) in enumerate(delen.items()):
        t1 = time.time()
        me = o.data
        oud = list(me.materials)
        oud_idx = np.zeros(len(me.polygons), np.int32)
        me.polygons.foreach_get("material_index", oud_idx)
        for o2 in delen.values():
            o2.hide_render = o2 is not o
        for soort in ("pos", "id"):
            me.materials.clear()
            me.materials.append(bak_mat("_" + soort, soort, i))
            me.polygons.foreach_set("material_index", np.zeros(len(me.polygons), np.int32))
            bak(o, [], soort, beelden[soort], margin=0, clear=eerst)
        me.materials.clear()
        me.materials.append(bak_mat("_doel", "pos"))
        hs = highs.get(naam, [])
        for h in hs:
            h.hide_render = False
        ext, ray = {"lijf": (0.012, 0.03), "uier": (0.006, 0.02)}.get(naam, (0.004, 0.01))
        if hs:
            bak(o, hs, "normaal", beelden["normaal"], ext, ray, clear=eerst)
        else:
            bak(o, [], "normaal", beelden["normaal"], clear=eerst)
        bak(o, hs, "ao", beelden["ao"], ext, ray, clear=eerst)
        for h in hs:
            h.hide_render = True
        me.materials.clear()
        for m in oud:
            me.materials.append(m)
        me.polygons.foreach_set("material_index", oud_idx)
        eerst = False
        log("  bak", naam, f"{time.time() - t1:.1f}s")
    for o2 in delen.values():
        o2.hide_render = False
    return {k: BM.pixels(v) for k, v in beelden.items()}


# --- Texturen ---------------------------------------------------------------------------------------
def componeer(B, mpp, sk):
    """Kleur (lineair, relatief t.o.v. GRIJS), hoogte (m), ruwheid, metaal per gedekte texel."""
    s = sk.s
    idm = B["id"]
    ys, xs = np.nonzero(idm[..., 1] > 0.5)
    deel = np.clip(np.round(idm[ys, xs, 0] * 8).astype(int) - 1, 0, len(DELEN) - 1)
    P = B["pos"][ys, xs, :3].astype(np.float64)
    Q = P / s
    n = len(P)
    kl = np.ones((n, 3)) * GRIJS
    H = np.zeros(n)
    ruw = np.full(n, 0.72)
    met = np.zeros(n)
    L = deel == 0
    # vacht: lage variatie + korte haren (gestrekt langs de romp, langs de benen omlaag)
    var = 1 + 0.05 * ruis(Q, 4, 1, 2) + 0.03 * ruis(Q, 25, 2)
    kl *= var[:, None]
    been = gladstap(0.55, 0.45, Q[:, 2])
    fh = np.where(been[:, None] > 0.5, np.array([90.0, 90.0, 18.0]), np.array([90.0, 18.0, 70.0]))
    H += 0.00035 * ruis(Q * fh / 40.0, 40.0, 3) * L
    # vuile onderbenen, iets bruin
    vuil = gladstap(0.30, 0.06, Q[:, 2]) * L
    kl *= (1 - vuil[:, None] * np.array([0.25, 0.32, 0.42]) * (0.7 + 0.3 * ruis(Q, 14, 4))[:, None])
    # hoeven: alles onder de kroonrand donker en glad
    kroon = 0.075 + 0.006 * ruis(Q, 30, 5)
    hoef = gladstap(kroon + 0.006, kroon - 0.006, Q[:, 2]) * L
    kl = kl * (1 - hoef[:, None]) + hoef[:, None] * np.array([0.050, 0.045, 0.042]) * (1 + 0.3 * ruis(Q, 60, 6))[:, None]
    ruw = ruw * (1 - hoef) + 0.45 * hoef
    H += hoef * 0.0003 * np.sin(Q[:, 2] * 900)          # groeiringen
    # klauwspleet: smalle donkere groef vooraan in de hoef
    for zijde in ("Left", "Right"):
        for b in ("FrontHoof", "HindHoof"):
            x0 = sk.T[zijde + b][0] / s
            gl = np.exp(-((Q[:, 0] - x0) / 0.004) ** 2) * hoef * (Q[:, 2] < 0.07)
            kl *= (1 - 0.8 * gl[:, None])
            H -= 0.002 * gl
    # kop: snuit roze en vochtig, neusgaten donker, ogen
    d, u = kop_assen(sk)
    H0, H1 = sk.J["Head"] / s, sk.T["Head"] / s
    sn = np.linalg.norm(Q - (H1 - d * 0.005), axis=1)
    snuit = gladstap(0.085, 0.065, sn) * L
    roze = np.array([1.0, 0.70, 0.66]) * (0.9 + 0.1 * ruis(Q, 50, 7))[:, None]
    kl = kl * (1 - snuit[:, None]) + snuit[:, None] * kl * roze
    ruw = ruw * (1 - snuit) + 0.38 * snuit
    H += snuit * 0.0005 * ruis(Q, 160, 8)
    for sg in (1, -1):
        ng = np.linalg.norm(Q - (H1 + d * 0.025 - u * 0.03 + np.array((sg * 0.034, 0, 0))), axis=1)
        gat = gladstap(0.024, 0.014, ng) * L
        kl *= (1 - 0.75 * gat[:, None])
        oog_c = H0 + d * 0.13 + np.array((sg * 0.093, 0, 0)) - u * 0.025
        og = np.linalg.norm(Q - oog_c, axis=1)
        oog = gladstap(0.032, 0.024, og) * L
        kl = kl * (1 - oog[:, None]) + oog[:, None] * np.array([0.03, 0.02, 0.014])
        lid = gladstap(0.036, 0.030, og) * (1 - oog) * L
        kl *= (1 - 0.6 * lid[:, None])
        ruw = ruw * (1 - oog) + 0.10 * oog
        # iris (bruin), pupil (liggend ovaal), oogwit in de voorste hoek, glanspuntje: op het oppervlak
        uit = nrm(np.array((sg * 1.0, -0.25, 0.1)))
        ic = oog_c + uit * 0.026
        di = np.linalg.norm(Q - ic, axis=1)
        iris = gladstap(0.0135, 0.0105, di) * oog
        kl = kl * (1 - iris[:, None]) + iris[:, None] * np.array([0.11, 0.055, 0.025])
        dp = np.sqrt(((Q - ic)[:, 1] / 1.6) ** 2 + ((Q - ic)[:, 2]) ** 2 + ((Q - ic)[:, 0] * 0.3) ** 2)
        pup = gladstap(0.0055, 0.004, dp) * oog
        kl = kl * (1 - pup[:, None]) + pup[:, None] * 0.008
        wit = gladstap(0.006, 0.003, np.linalg.norm(Q - (oog_c + nrm(np.array((sg * 0.75, -0.62, 0.0))) * 0.026), axis=1)) * oog
        kl = kl * (1 - wit[:, None]) + wit[:, None] * np.array([0.55, 0.5, 0.45])
        gl = np.linalg.norm(Q - (ic + np.array((0, -0.004, 0.005))), axis=1)
        kl += (gladstap(0.0035, 0.0018, gl) * oog * 0.9)[:, None]
    # binnenkant oren iets roze (zichtbaar bij witte oren)
    # kwast crème met haarlijnen
    kw = gladstap(0.50, 0.42, Q[:, 2]) * (Q[:, 1] > 0.62) * L
    kl = kl * (1 - kw[:, None]) + kw[:, None] * kl * np.array([1.0, 0.92, 0.78])
    H += kw * 0.0012 * ruis(Q * np.array([1, 1, 0.15]), 120, 9)
    # nekplooien (onder de hals)
    hals = gladstap(-0.56, -0.64, Q[:, 1]) * gladstap(-0.86, -0.78, Q[:, 1]) * gladstap(0.88, 0.76, Q[:, 2]) *         (np.abs(Q[:, 0]) < 0.06) * L
    H += hals * 0.0002 * np.sin(Q[:, 1] * 2 * np.pi / 0.03 + 2 * ruis(Q, 8, 10))
    # uier: roze huid, spenen iets donkerder, fijne aders
    U = deel == 1
    kl[U] = GRIJS * np.array([1.0, 0.96, 0.95])
    sp = gladstap(0.45, 0.43, Q[:, 2]) * U
    kl *= (1 - 0.18 * sp[:, None])
    ad = np.abs(ruis(Q, 18, 13)) < 0.04
    kl[U & ad] *= np.array([0.93, 0.9, 0.95])
    ruw[U] = 0.55
    H += U * 0.0004 * ruis(Q, 90, 14)
    # halsband: leer (neutraal, tint geeft de kleur), naad langs de randen, gaatjes
    HB = deel == 2
    kl[HB] = GRIJS * (0.95 + 0.06 * ruis(Q[HB], 80, 15))[:, None]
    ruw[HB] = 0.6
    H += HB * 0.0003 * ruis(Q, 200, 16)
    # bel: koper, metaal; lus en klepel donkerder
    BE = deel == 3
    kl[BE] = srgb("#b08a3a") * (0.9 + 0.15 * ruis(Q[BE], 60, 17))[:, None]
    ruw[BE] = 0.33 + 0.15 * np.abs(ruis(Q[BE], 40, 18))
    met[BE] = 1.0
    return ys, xs, kl, H, ruw, met, deel


def bewaar(arr, naam, data, jpg=False):
    os.makedirs(TEX, exist_ok=True)
    pad = os.path.join(TEX, naam + (".jpg" if jpg else ".png"))
    img = bpy.data.images.new(naam, arr.shape[1], arr.shape[0], alpha=False)
    if data:
        img.colorspace_settings.name = "Non-Color"
    a = np.concatenate([np.clip(arr, 0, 1), np.ones((*arr.shape[:2], 1))], 2).astype(np.float32)
    img.pixels.foreach_set(a.ravel())
    img.filepath_raw = pad
    img.file_format = "JPEG" if jpg else "PNG"
    if jpg:
        bpy.context.scene.render.image_settings.quality = 92
    img.save()
    bpy.data.images.remove(img)
    out = bpy.data.images.load(pad, check_existing=False)
    out.name = naam
    if data:
        out.colorspace_settings.name = "Non-Color"
    return out


def texturen(B, mpp, sk):
    t1 = time.time()
    ys, xs, kl, H, ruw, met, deel = componeer(B, mpp, sk)
    h, w = B["pos"].shape[:2]
    mask = np.zeros((h, w), bool)
    mask[ys, xs] = True
    ao = B["ao"][..., 0]
    aov = ao[ys, xs]
    kl = kl * (0.55 + 0.45 * aov)[:, None]
    K = np.zeros((h, w, 3), np.float32)
    K[ys, xs] = naar_srgb(kl)
    Hm = np.zeros((h, w), np.float32)
    Hm[ys, xs] = H
    mp = np.full((h, w), np.mean(list(mpp.values())), np.float32)
    for i, nm in enumerate(DELEN):
        sel = deel == i
        mp[ys[sel], xs[sel]] = mpp[nm]
    Hd = BM.dilateer(Hm[..., None].repeat(3, -1), mask, 3)[..., 0]
    nd = BM.reliëf_normaal(Hd, mp)
    nb = B["normaal"][..., :3] * 2 - 1
    n = np.stack([nb[..., 0] + nd[..., 0], nb[..., 1] + nd[..., 1], nb[..., 2] * nd[..., 2]], -1)
    n /= np.linalg.norm(n, axis=-1, keepdims=True) + 1e-9
    Nimg = n * 0.5 + 0.5
    Nimg[~mask] = (0.5, 0.5, 1.0)
    ORM = np.zeros((h, w, 3), np.float32)
    ORM[..., 0] = np.clip(ao * 0.85 + 0.15, 0, 1)
    ORM[ys, xs, 1] = ruw
    ORM[ys, xs, 2] = met
    K = BM.dilateer(K, mask, 10)
    Nimg = BM.dilateer(Nimg.astype(np.float32), mask, 10)
    ORM = BM.dilateer(ORM, mask, 10)
    kleur = bewaar(K, "koe_kleur", False, jpg=True)
    normaal = bewaar(Nimg, "koe_normaal", True)
    orm = bewaar(ORM[::2, ::2] if RES >= 2048 else ORM, "koe_orm", True)
    log("texturen", f"{time.time() - t1:.1f}s")
    return kleur, normaal, orm


def materialen(delen, kleur, normaal, orm):
    mats = {k: BM.pbr("mat_" + k, kleur, normaal, orm, tuple(srgb(v))) for k, v in TINT.items()}
    vast = BM.pbr("mat_vast", kleur, normaal, orm)
    for naam, o in delen.items():
        me = o.data
        idx = np.zeros(len(me.polygons), np.int32)
        me.polygons.foreach_get("material_index", idx)
        me.materials.clear()
        if naam == "lijf":
            me.materials.append(mats["lijf"])
            me.materials.append(mats["vlek"])
            me.materials.append(vast)
        elif naam == "bel":
            me.materials.append(vast)
            idx[:] = 0
        else:
            me.materials.append(mats[naam])
            idx[:] = 0
        me.polygons.foreach_set("material_index", idx)


def vlak_materialen(delen):
    """Zonder bake (silhouetrondes): platte kleuren."""
    kl = {"oog": "#140c08", "lijf": "#ece9e2", "vlek": "#1d1b1b", "uier": "#e7b3a8", "halsband": "#6e4226", "bel": "#b08a3a"}
    for naam, o in delen.items():
        me = o.data
        idx = np.zeros(len(me.polygons), np.int32)
        me.polygons.foreach_get("material_index", idx)
        me.materials.clear()
        for k in (["lijf", "vlek", "oog"] if naam == "lijf" else [naam]):
            me.materials.append(BM.vlak_mat("v_" + k, srgb(kl[k]), 0.35 if k == "bel" else 0.75))
        me.polygons.foreach_set("material_index", idx if naam == "lijf" else idx * 0)


# --- Gewichten ------------------------------------------------------------------------------------
def skin(o, rig, sk, naam):
    BM.ontkies()
    if naam in ("lijf", "uier"):
        o.select_set(True)
        rig.select_set(True)
        bpy.context.view_layer.objects.active = rig
        bpy.ops.object.parent_set(type="ARMATURE_AUTO")
    else:
        o.parent = rig
        m = o.modifiers.new("Armature", "ARMATURE")
        m.object = rig
    me = o.data
    P = np.array([v.co for v in me.vertices])
    vg = {g.name: g for g in o.vertex_groups}

    def zet(mask, bot):
        """Vertices in mask: 100 % op bot."""
        ids = np.nonzero(mask)[0].tolist()
        if not ids:
            return
        for g in o.vertex_groups:
            g.remove(ids)
        (vg.get(bot) or o.vertex_groups.new(name=bot)).add(ids, 1.0, "REPLACE")

    s = sk.s
    if naam == "lijf":
        for z in ("Left", "Right"):
            ea, ee = sk.J[z + "Ear"], sk.T[z + "Ear"]
            e = ee - ea
            t = np.clip((P - ea) @ e / (e @ e), -1, 2)
            dist = np.linalg.norm(P - (ea + t[:, None] * e), axis=1)
            zet((t > 0.12) & (dist < 0.07 * s) & (np.sign(P[:, 0]) == np.sign(ea[0])), z + "Ear")
            for b in ("FrontHoof", "HindHoof"):
                ko = sk.J[z + b]
                zet((P[:, 2] < ko[2] - 0.035 * s) & (np.linalg.norm(P[:, :2] - ko[:2], axis=1) < 0.12 * s), z + b)
        # kwast hangt aan Tail3
        zet((P[:, 2] < sk.J["Tail3"][2]) & (P[:, 1] > 0.62 * s), "Tail3")
    elif naam == "halsband":
        zet(np.ones(len(P), bool), "Neck1")
    elif naam == "uier":
        zet(np.ones(len(P), bool), "Hips")
    # max 4 invloeden, normaliseren
    bpy.context.view_layer.objects.active = o
    BM.ontkies()
    o.select_set(True)
    bpy.ops.object.vertex_group_limit_total(group_select_mode="ALL", limit=4)
    bpy.ops.object.vertex_group_clean(group_select_mode="ALL", limit=0.01)
    bpy.ops.object.vertex_group_normalize_all(lock_active=False)
    leeg = sum(1 for v in me.vertices if not v.groups)
    if leeg:
        log("  let op:", naam, leeg, "vertices zonder gewicht")


# --- Previews -------------------------------------------------------------------------------------------
def sprite(pad, frame=None, breed=None):
    a = BM.laad_np(pad)
    if frame is not None:
        a = a[:, frame * breed:(frame + 1) * breed]
    return BM.bijsnijden(a)


def toon_bel(sc, aan):
    for n in ("halsband", "bel"):
        o = sc.objects.get(n)
        if o:
            o.hide_render = not aan


def vergelijk(sc, rig, tag=""):
    os.makedirs(PREV, exist_ok=True)
    rig.animation_data_create().action = None
    for b in rig.pose.bones:
        b.rotation_quaternion = (1, 0, 0, 0)
        b.location = (0, 0, 0)
    bpy.context.view_layer.update()
    tmp = bpy.app.tempdir
    U = os.path.join(REF, "Unity_bumpkins", "Bumpkins", "Assets", "Resources", "Sprites-HD", "Units")
    SH = os.path.join(REF, "bb_original", "sheets")
    se = sprite(os.path.join(U, "cow_se.png"))                                   # HD, 43,8 px/m
    zij = BM.nn(sprite(os.path.join(SH, "cowwalk.png"), 7, 54), 2)                # 1x -> HD
    melk = sprite(os.path.join(U, "milking.png"))
    toon_bel(sc, True)
    BM.studio(sc, 43.8, 2.6, 2.0, doel=(0, -0.1, 0.65))
    r_se = BM.bijsnijden(BM.render_np(sc, os.path.join(tmp, "r_se.png")))
    BM.studio(sc, 43.8, 2.6, 2.0, doel=(0, -0.1, 0.65), yaw=0)
    r_zij = BM.bijsnijden(BM.render_np(sc, os.path.join(tmp, "r_zij.png")))
    toon_bel(sc, False)
    BM.studio(sc, 43.8, 2.6, 2.0, doel=(0, -0.1, 0.65))
    r_wild = BM.bijsnijden(BM.render_np(sc, os.path.join(tmp, "r_wild.png")))
    k = 4
    rij = BM.plak([BM.nn(se, k), BM.nn(r_se, k), BM.nn(r_wild, k), BM.nn(zij, k), BM.nn(r_zij, k), BM.nn(melk, k)])
    BM.schrijf(rij, os.path.join(PREV, f"koe_vergelijk_1x{tag}.png"))
    # close-ups naast het concept
    concept = BM.laad_np(os.path.join(REF, "concept", "img", "koe.jpg"))
    big = []
    toon_bel(sc, False)
    for yw, pt in ((180, 8), (270, 5), (225, 30), (90, 5)):
        BM.studio(sc, 260, 2.4, 1.6, doel=(0, -0.15, 0.70), yaw=yw, pitch=pt)
        big.append(BM.bijsnijden(BM.render_np(sc, os.path.join(tmp, f"c_{yw}.png"))))
    rij1 = BM.plak(big)
    toon_bel(sc, True)
    big = []
    for yw, pt in ((180, 8), (270, 5), (225, 30), (300, 12)):
        BM.studio(sc, 260, 2.4, 1.6, doel=(0, -0.15, 0.70), yaw=yw, pitch=pt)
        big.append(BM.bijsnijden(BM.render_np(sc, os.path.join(tmp, f"d_{yw}.png"))))
    rij2 = BM.plak(big)
    c = concept[..., :3]
    c = np.concatenate([c, np.ones((*c.shape[:2], 1), np.float32)], 2)
    out = BM.onder(BM.plak([c])[..., :3], rij1, rij2)
    BM.schrijf(out, os.path.join(PREV, f"koe_vergelijk_close{tag}.png"))
    # kop dichtbij
    toon_bel(sc, True)
    pan = []
    for yw, pt in ((250, 10), (200, 20), (270, 0)):
        BM.studio(sc, 900, 0.7, 0.7, doel=(0, -1.0 * rig["schaal"], 0.95 * rig["schaal"]), yaw=yw, pitch=pt)
        pan.append(BM.render_np(sc, os.path.join(tmp, f"k_{yw}.png")))
    BM.schrijf(BM.plak(pan), os.path.join(PREV, f"koe_kop{tag}.png"))


def poses(sc, rig, tag=""):
    keuzes = [("idle", 0), ("idle", 40), ("lopen", 3), ("lopen", 10), ("lopen", 17), ("grazen", 32),
              ("gemolken_worden", 50), ("sterven", 22), ("sterven", 60), ("geboorte", 40)]
    tmp = bpy.app.tempdir
    toon_bel(sc, True)
    rijen = []
    for yaw, pitch in ((225, 30), (180, 6)):
        panelen = []
        for act, f in keuzes:
            if act not in bpy.data.actions:
                continue
            R.zet_actie(rig, act)
            sc.frame_set(f)
            BM.studio(sc, 150, 2.6, 2.0, doel=(0, -0.2, 0.62), yaw=yaw, pitch=pitch)
            panelen.append(BM.bijsnijden(BM.render_np(sc, os.path.join(tmp, f"p_{act}_{f}.png"))))
        rijen.append(BM.plak(panelen))
    BM.schrijf(BM.onder(*rijen), os.path.join(PREV, f"koe_poses{tag}.png"))
    # vervorming dichtbij: benen in de stap, hals bij het grazen, ligpose
    pan = []
    for act, f, yw, pt, doel, br in (("lopen", 3, 180, 8, (0, 0.2, 0.45), 1.3), ("lopen", 10, 180, 8, (0, -0.3, 0.45), 1.3),
                                     ("grazen", 32, 210, 15, (0, -0.8, 0.55), 1.3),
                                     ("sterven", 60, 200, 20, (0, -0.2, 0.40), 2.4),
                                     ("geboorte", 40, 160, 10, (0, -0.2, 0.50), 2.4)):
        R.zet_actie(rig, act)
        sc.frame_set(f)
        BM.studio(sc, 330 * 1.3 / br, br, 1.1 * br / 1.3, doel=doel, yaw=yw, pitch=pt)
        pan.append(BM.render_np(sc, os.path.join(tmp, f"v_{act}_{f}.png")))
    BM.schrijf(BM.plak(pan), os.path.join(PREV, f"koe_vervorming{tag}.png"))
    rig.animation_data.action = None


def lopen_blad(sc, rig, tag=""):
    """8 frames van opzij; vloer met streepjes elke 0,1 m die meeschuift met de grondsnelheid."""
    act = R.zet_actie(rig, "lopen")
    v = act["snelheid_mps"]
    N = int(act.frame_end)
    mat = BM.vlak_mat("streep", (0.1, 0.1, 0.1))
    vl = BM.vlak_mat("vloer", (0.45, 0.5, 0.4))
    bpy.ops.mesh.primitive_plane_add(size=6, location=(0, 0, -0.003))
    vloer = bpy.context.object
    vloer.data.materials.append(vl)
    strepen = []
    for i in range(-30, 31):
        bpy.ops.mesh.primitive_cube_add(size=1, location=(0.6, i * 0.1, 0.0), scale=(0.25, 0.006, 0.002))
        bpy.context.object.data.materials.append(mat)
        strepen.append(bpy.context.object)
    tmp = bpy.app.tempdir
    pan = []
    for i in range(8):
        f = int(round(i * N / 8))
        sc.frame_set(f)
        for j, st in enumerate(strepen):
            st.location.y = ((j - 30) * 0.1 + v * f / FPS_) % 6.0 - 3.0
        BM.studio(sc, 140, 2.4, 1.5, doel=(0, -0.2, 0.62), yaw=180, pitch=8)
        pan.append(BM.bijsnijden(BM.render_np(sc, os.path.join(tmp, f"l_{f}.png"))))
    BM.schrijf(BM.plak(pan[:4]) if False else BM.onder(BM.plak(pan[:4]), BM.plak(pan[4:])),
               os.path.join(PREV, f"koe_lopen_zij{tag}.png"))
    for o in [vloer] + strepen:
        bpy.data.objects.remove(o)
    rig.animation_data.action = None


FPS_ = R.FPS


# --- Hoofdprogramma ---------------------------------------------------------------------------------
def main():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    sc = bpy.context.scene
    sc.render.fps = R.FPS
    sc.frame_start = 0
    coll = sc.collection
    rig = R.bouw_rig()
    sk = Skelet(rig)
    hoog_uier = oppervlak(vorm_uier(sk), H_GRID * 0.7, "uier_hoog", coll)
    vorm = vorm_lijf(sk)
    hoog_lijf = oppervlak(vorm, H_GRID, "lijf_hoog", coll)
    lijf = decimeer(hoog_lijf, "lijf", DOEL_LIJF, coll)
    snij_vlekken(lijf, sk)
    uier = decimeer(hoog_uier, "uier", 480, coll)
    halsband = maak_halsband(sk, vorm, rig)
    bel = maak_bel(sk, rig)
    bel.parent = rig
    bel.parent_type = "BONE"
    bel.parent_bone = "prop_bel"
    bel.matrix_parent_inverse = Matrix.Identity(4)
    bel.location = (0, -rig.data.bones["prop_bel"].length, 0)
    bpy.context.view_layer.update()
    # de bel bakt in rustpositie (wereld) maar blijft als kind van het bot staan
    delen = {"lijf": lijf, "uier": uier, "halsband": halsband, "bel": bel}
    for o in delen.values():
        o.data.shade_smooth()
    log("driehoeken", driehoeken(delen.values()), {k: driehoeken([o]) for k, o in delen.items()})
    if "vlak" in OPTS:
        vlak_materialen(delen)
        for h in (hoog_lijf, hoog_uier):
            bpy.data.objects.remove(h)
    else:
        mpp = uv_atlas(delen)
        log("m/texel (mm)", {k: round(v * 1000, 2) for k, v in mpp.items()})
        # bel staat als kind van een bot; voor het bakken telt alleen dat de wereldpositie klopt
        B = bak_alles(delen, {"lijf": [hoog_lijf], "uier": [hoog_uier]}, sk)
        for h in (hoog_lijf, hoog_uier):
            bpy.data.objects.remove(h)
        kleur, normaal, orm = texturen(B, mpp, sk)
        materialen(delen, kleur, normaal, orm)
    for naam, o in delen.items():
        if naam != "bel":
            skin(o, rig, sk, naam)
    for naam in ("halsband", "bel"):
        delen[naam]["verborgen"] = True                  # glTF extras: het spel verbergt ze bij het spawnen
    log("LOD0 driehoeken", driehoeken(delen.values()), {k: driehoeken([o]) for k, o in delen.items()})
    info = R.bouw_animaties(rig)
    import json
    json.dump(info, open(os.path.join(HERE, "koe_anim.json"), "w"), indent=2)
    log("animaties", list(info))
    log("glij", R.glijcontrole(rig))
    if "geen_export" not in OPTS:
        BM.ontkies()
        bpy.ops.export_scene.gltf(filepath=GLB, export_format="GLB", export_animations=True,
                                  export_animation_mode="ACTIONS", export_force_sampling=True, export_yup=True,
                                  export_skins=True, export_def_bones=False, export_extras=True, use_selection=False,
                                  export_tangents=True, export_image_format="AUTO", export_cameras=False,
                                  export_lights=False)
        log("export", GLB, f"{os.path.getsize(GLB) / 1e6:.1f} MB")
    tag = OPTS.get("tag", "")
    if "vergelijk" in OPTS:
        vergelijk(sc, rig, tag)
    if "poses" in OPTS:
        poses(sc, rig, tag)
    if "lopen" in OPTS:
        lopen_blad(sc, rig, tag)
    os.makedirs(PREV, exist_ok=True)
    bpy.ops.wm.save_as_mainfile(filepath=os.path.join(PREV, "koe.blend"))
    log("KLAAR")


if __name__ == "__main__":
    main()
