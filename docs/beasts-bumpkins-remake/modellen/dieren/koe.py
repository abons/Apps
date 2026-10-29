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
| deel     | inhoud                                          | materiaal        | tint                    |
| -------- | ----------------------------------------------- | ---------------- | ----------------------- |
| lijf     | romp, hals, kop, benen, hoeven, staart, oren,   | mat_lijf         | factor #ffffff; vlekken |
|          | vlekken (in de textuur, masker apart)           |                  | zie HERTINTEN           |
|          | ogen (eigen vlakken: ook leesbaar in een zwarte kop) | mat_vast    | wit (echte kleur)       |
| uier     | uier met vier spenen                            | mat_uier         | #f0b9ae roze            |
| halsband | leren halsband, VERBORGEN (extras.verborgen)     | mat_halsband     | #6e4226 leer            |
| bel      | koperen bel + lus + klepel, kind van prop_bel, VERBORGEN | mat_vast | wit (echte kleur)    |
HERTINTEN (r7, vervangt mat_vlek met gesneden vlakken): de vlekken zitten op textuurresolutie in
koe_kleur.jpg, dus de glb toont zonder meer een zwartbonte koe (factor wit). Het masker staat los in
textures_koe/koe_vlek.png (R = 1 in de vlek, zachte haarrand). mat_lijf draagt glTF-extras (in Godot
meta op het materiaal): tint_vacht "#ffffff", tint_vlek "#262422", vlek_standaard "#262422",
vlek_masker "textures_koe/koe_vlek.png". Hertinten = één parameter per deel, in een shader:
  albedo = tex.rgb * mix(tint_vacht, tint_vlek / vlek_standaard, masker)      (lineaire kleuren)
koe_vacht.gdshader doet precies dat (uniforms tint_vacht, tint_vlek; standaard = geen verschil).
Voorbeeld roodbont: tint_vlek #7a3b22. De textuur is in het wit lichtgrijs (~0,86) met crème en vuil
als relatieve tint, in de vlek vlek_standaard x detail (bruinzwarte glans, haarplukken).
halsband en bel staan in de glb maar met extras {"verborgen": true}: het spel zet ze bij het spawnen
onzichtbaar en toont ze als de koe van het dorp is.

Bouw: een signed distance field (numpy; afgeronde kegels en ellipsoïden langs de gewrichten van het
skelet, glad samengevoegd) -> surface nets (7 mm) = hoog-poly; gedecimeerd (symmetrisch) = laag-poly.
De vlekgrens is een 3D-veld, per texel geëvalueerd (positie- en normaalkaart gebakken); vacht = haar-
strengen en plukken als hoogte langs een vaste 3D-richting per streek (romp, buik, been, kop, staart),
krullen op de kuif, lange haren in kwast en oor. Gewichten: bone heat (ARMATURE_AUTO), gladgestreken,
romp los van de bovenbenen (romp_los), onderbenen star (onderbenen), oren/hoeven/kwast vast. Romp korter
via koe_rig.ROMP; bas() rekent de velden terug naar de basismaat. Cycles bakt normaal en AO van hoog naar
laag; kleur, ruwheid en het vlekkenmasker komen er per texel bij.
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
DOEL_LIJF = 5500                    # driehoeken na decimeren (de oogranden snijden er nog ~40 bij)
DELEN = ["lijf", "uier", "halsband", "bel"]
GRIJS = 0.86
TINT = {"lijf": "#ffffff", "vlek": "#262422", "uier": "#f0b9ae", "halsband": "#6e4226"}
srgb, naar_srgb, ruis, gladstap = BM.srgb, BM.naar_srgb, BM.ruis, BM.gladstap


def log(*a):
    print(f"[koe {time.time() - T0:6.1f}s]", *a, flush=True)


def bas(A):
    """Wereld/schaal -> basismaat: maakt de romp-inkorting (koe_rig.ROMP) ongedaan, zodat de vlakken- en
    kleurvelden in de oude basismaat blijven rekenen."""
    A = np.array(A, float)
    A[..., 1] = R.romp_y_inv(A[..., 1])
    return A


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
    V = lambda x, y, z: np.array((x, float(R.romp_y(y)), z)) * s
    S = SDF()
    # romp
    S.el(V(0, -0.36, 0.83), np.array((0.25, 0.22, 0.31)) * s, k=0.10 * s)
    S.el(V(0, -0.02, 0.80), np.array((0.30, 0.38, 0.33)) * s, k=0.12 * s)
    S.el(V(0, 0.30, 0.84), np.array((0.28, 0.26, 0.25)) * s, k=0.10 * s)
    S.el(V(0, 0.48, 0.94), np.array((0.23, 0.15, 0.19)) * s, k=0.08 * s)                 # kruis (vlakke ruglijn)
    S.rc(V(0, -0.48, 1.03), V(0, 0.52, 1.02), 0.10 * s, 0.10 * s, k=0.12 * s)          # rugbalk (vlakke rug)
    S.el(V(0, -0.44, 1.04), np.array((0.10, 0.15, 0.06)) * s, k=0.08 * s)             # schoft
    for sg in (1, -1):
        S.el(V(sg * 0.18, 0.34, 1.02), np.array((0.065, 0.07, 0.055)) * s, k=0.07 * s)  # heupknobbel
        S.el(V(sg * 0.085, 0.59, 1.00), np.array((0.05, 0.05, 0.05)) * s, k=0.05 * s)  # zitbeenknobbel
    # staart (wortel glad aan de romp, de rest los)
    S.rc(V(0, 0.52, 1.03), J["Tail"], 0.07 * s, 0.05 * s, k=0.05 * s)
    S.rc(J["Tail"], J["Tail1"], 0.05 * s, 0.034 * s, k=0.03 * s)
    S.rc(J["Tail1"], J["Tail2"], 0.034 * s, 0.026 * s, k=0.008 * s)
    S.rc(J["Tail2"], J["Tail3"], 0.026 * s, 0.022 * s, k=0.008 * s)
    td = nrm(T["Tail3"] - J["Tail3"])
    ax = np.array([[1, 0, 0], nrm(np.cross(td, [1, 0, 0])), td])
    S.el(J["Tail3"] + td * 0.07 * s, np.array((0.055, 0.046, 0.10)) * s, k=0.025 * s, assen=ax)  # kwast
    S.rc(J["Tail3"] + td * 0.08 * s, J["Tail3"] + td * 0.30 * s, 0.045 * s, 0.012 * s, k=0.03 * s)        # punt
    # hals + kwab
    S.rc(V(0, -0.36, 0.90), V(0, -0.80, 1.09), 0.26 * s, 0.16 * s, k=0.10 * s)
    S.rc(V(0, -0.45, 1.06), V(0, -0.80, 1.15), 0.10 * s, 0.09 * s, k=0.08 * s)             # halskam
    S.rc(V(0, -0.50, 0.73), V(0, -0.72, 0.86), 0.05 * s, 0.03 * s, k=0.05 * s)         # kwab langs de keel
    # kop
    d, u = kop_assen(sk)
    H0, H1 = J["Head"], T["Head"]
    KA = np.array([[1, 0, 0], d, u])
    S.el(H0 + d * 0.07 * s, np.array((0.143, 0.12, 0.13)) * s, k=0.05 * s, assen=KA)       # schedel
    S.rc(H0 + d * 0.06 * s, H1 - d * 0.06 * s, 0.12 * s, 0.094 * s, k=0.04 * s)           # gezicht
    S.el(H1 - d * 0.035 * s + u * 0.008 * s, np.array((0.126, 0.06, 0.09)) * s, k=0.03 * s, assen=KA)   # snuit: breed, plat
    S.el(H0 - u * 0.09 * s + d * 0.03 * s, np.array((0.07, 0.06, 0.035)) * s, k=0.04 * s, assen=KA)      # kuif (krullenkam)
    S.rc(J["Jaw"], T["Jaw"], 0.07 * s, 0.045 * s, k=0.04 * s)                              # onderkaak
    for sg in (1, -1):
        S.el(J["Jaw"] + V(sg * 0.055, 0.0, 0.01), np.array((0.05, 0.08, 0.08)) * s, k=0.04 * s)   # wang
        # oog: ondiepe kas, oogbol, boven- en onderlid, wenkbrauwboog erboven
        oc = oog_c(sk, sg)
        X = np.array((sg * 1.0, 0, 0))
        uit = nrm(X + 0.2 * d - 0.15 * u)
        S.el(oc + uit * 0.022 * s - u * 0.004 * s, np.array((0.034, 0.045, 0.038)) * s, k=0.014 * s, m="-",
             assen=KA)                                                                       # oogkas
        S.el(oc, np.array((OOG[3],) * 3) * s, k=0.004 * s)                                  # oogbol
        S.el(oc - u * 0.017 * s + X * 0.001 * s, np.array((0.0275, 0.0325, 0.0105)) * s, k=0.004 * s,
             assen=KA)                                                                       # bovenlid
        S.el(oc + u * 0.019 * s - X * 0.001 * s, np.array((0.025, 0.029, 0.0085)) * s, k=0.004 * s,
             assen=KA)                                                                       # onderlid
        S.el(H0 + d * 0.118 * s + np.array((sg * 0.100 * s, 0, 0)) - u * 0.056 * s,
             np.array((0.026, 0.024, 0.012)) * s, k=0.012 * s, assen=KA)                    # wenkbrauwboog
        # neusgat: komma (diep ovaal + kleine staart naar binnen-onder), met een opstaande vleugel
        nc = H1 + d * 0.028 * s - u * 0.024 * s + X * 0.034 * s
        S.el(nc + X * 0.012 * s - d * 0.006 * s, np.array((0.009, 0.012, 0.022)) * s, k=0.006 * s,
             assen=KA)                                                                       # neusvleugel
        S.el(nc, np.array((0.010, 0.020, 0.017)) * s, k=0.006 * s, m="-", assen=KA)
        S.el(nc + u * 0.014 * s - X * 0.009 * s, np.array((0.007, 0.014, 0.008)) * s, k=0.005 * s, m="-",
             assen=KA)
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
        S.el(mid, np.array((0.10, 0.054, 0.025)) * s, k=0.012 * s, assen=OA)
        S.el(mid + t * 0.019 * s + e * 0.012 * s, np.array((0.084, 0.040, 0.016)) * s, k=0.006 * s, m="-", assen=OA)
    S.el(H0 + np.array((0, 0, 0.10 * s)) + d * 0.02 * s, np.array((0.075, 0.05, 0.04)) * s, k=0.03 * s)  # kuif
    # voorbenen
    for z, sg in (("Left", 1), ("Right", -1)):
        b = lambda n: z + n
        sh, el_, kn, ko, te = J[b("UpperArm")], J[b("ForeArm")], J[b("FrontCannon")], J[b("FrontHoof")], T[b("FrontHoof")]
        S.el(sh + V(-sg * 0.03, 0.10, 0.08), np.array((0.08, 0.12, 0.17)) * s, k=0.08 * s)   # schouder
        S.rc(sh + V(-sg * 0.01, 0.04, 0.0), el_, 0.075 * s, 0.068 * s, k=0.06 * s)
        S.el(el_ + V(0, 0.02, 0.01), np.array((0.045,) * 3) * s, k=0.04 * s)                 # elleboog
        S.rc(el_, kn, 0.08 * s, 0.05 * s, k=0.04 * s)
        S.el(kn, np.array((0.055, 0.052, 0.06)) * s, k=0.025 * s)                            # voorknie
        poot(S, kn, ko, te, s, V)
    # achterbenen
    for z, sg in (("Left", 1), ("Right", -1)):
        b = lambda n: z + n
        hp, kn, hak, ko, te = J[b("Thigh")], J[b("Shin")], J[b("HindCannon")], J[b("HindHoof")], T[b("HindHoof")]
        S.rc(hp + V(0, 0, 0.03), kn, 0.17 * s, 0.10 * s, k=0.08 * s)                         # dij
        S.el((hp + kn) / 2 + V(sg * 0.02, 0.03, 0), np.array((0.12, 0.17, 0.20)) * s, k=0.08 * s)
        S.rc(kn, hak, 0.10 * s, 0.05 * s, k=0.05 * s)                                       # scheen
        S.el(kn + (hak - kn) * 0.3 + V(0, 0.025, 0), np.array((0.075, 0.07, 0.10)) * s, k=0.06 * s)
        S.rc(hak, hak + V(0, 0.04, 0.03), 0.036 * s, 0.028 * s, k=0.02 * s)                   # hakknobbel
        S.el(hak, np.array((0.047, 0.05, 0.05)) * s, k=0.025 * s)
        poot(S, hak, ko, te, s, V)
    return S


def poot(S, boven, ko, te, s, V):
    """Pijp, kogel, koot en klauw (afgekapt op de grond)."""
    S.rc(boven, ko, 0.045 * s, 0.042 * s, k=0.018 * s)
    S.el(ko + V(0, 0.008, 0), np.array((0.05, 0.053, 0.05)) * s, k=0.018 * s)
    hm = ko + (te - ko) * 0.5
    g0 = np.array((te[0], te[1] + 0.05 * s, -0.01 * s))
    S.rc(ko, hm, 0.043 * s, 0.042 * s, k=0.015 * s)
    S.rc(hm, g0, 0.046 * s, 0.058 * s, k=0.012 * s)


def vorm_uier(sk):
    s = sk.s
    V = lambda x, y, z: np.array((x, float(R.romp_y(y)), z)) * s
    S = SDF()
    S.el(V(0, 0.30, 0.53), np.array((0.10, 0.145, 0.095)) * s, k=0.04 * s)
    S.el(V(0, 0.30, 0.61), np.array((0.09, 0.14, 0.07)) * s, k=0.05 * s)
    for x in (0.055, -0.055):
        for y in (0.22, 0.36):
            S.rc(V(x, y, 0.45), V(x * 1.1, y, 0.38), 0.017 * s, 0.013 * s, k=0.015 * s)
    return S


# --- Vlekken --------------------------------------------------------------------------------------
VLEKKEN = [  # (midden, stralen) in basismaat; naar het concept: weinig grote, rafelige vlekken (links != rechts)
    ((0.0, -0.62, 0.98), (0.40, 0.30, 0.30)),     # hals, borst en schouders (rondom)
    ((0.0, -0.80, 1.10), (0.32, 0.24, 0.27)),     # bovenhals tot achter de kop
    ((0.20, -0.46, 0.72), (0.12, 0.13, 0.21)),    # linkerschouder tot de elleboog
    ((-0.20, -0.44, 0.75), (0.12, 0.15, 0.22)),   # rechterschouder tot de elleboog
    ((0.25, -0.03, 0.94), (0.21, 0.26, 0.21)),    # grote middenvlek links (raakt de ruglijn)
    ((0.10, 0.06, 1.08), (0.19, 0.17, 0.09)),     # ... en zijn lob over de rug
    ((0.21, 0.34, 1.01), (0.08, 0.07, 0.07)),     # klein, links bij de heup
    ((0.15, 0.60, 0.82), (0.11, 0.10, 0.25)),     # links achter op de dij (ook van achteren)
    ((-0.27, 0.07, 0.92), (0.21, 0.30, 0.22)),    # grote flankvlek rechts
    ((-0.16, 0.56, 0.86), (0.13, 0.13, 0.24)),    # dij en kruis rechts (ook van achteren)
    ((0.0, 0.56, 1.02), (0.11, 0.06, 0.05)),      # band over de zitbeenderen
]


WIT_IN = [  # witte inhammen (r9) gaven ronde gaten; alleen een baai onder in de grote linkervlek
    ((0.31, 0.07, 0.76), (0.09, 0.12, 0.10)),
]


def vlekveld(P, sk, fijn=True):
    """> 0 = zwart (basismaat-eenheden: ~5 per meter rond een vlekrand). Ellipsoïdes met domeinvervorming
    op drie schalen (rafelige, gekartelde randen), losse eilandjes langs de randen; kop zwart met witte
    bles, snuit en kuif; benen, buik en staart wit. Wordt per texel geëvalueerd (masker), niet gesneden."""
    s = sk.s
    Q = bas(np.asarray(P, float) / s)
    W = np.column_stack([ruis(Q, 2.0, 21 + i, 2) for i in range(3)]) * 0.16 + \
        np.column_stack([ruis(Q, 4.5, 26 + i) for i in range(3)]) * 0.07 + \
        np.column_stack([ruis(Q, 9.0, 31 + i) for i in range(3)]) * 0.03
    if fijn:
        W += np.column_stack([ruis(Q, 15.0, 41 + i) for i in range(3)]) * 0.018
    Qw = Q + W
    f = np.full(len(Q), -1.0)
    for c, r in VLEKKEN:
        f = np.maximum(f, 1 - np.linalg.norm((Qw - np.array(c)) / np.array(r), axis=1))
    for c, r in WIT_IN:
        f = np.minimum(f, -0.7 * (1 - np.linalg.norm((Qw - np.array(c)) / np.array(r), axis=1)))
    f = f + 0.16 * ruis(Q, 3.0, 11) + 0.09 * ruis(Q, 8, 12) + 0.20 * ruis(Q, 5.5, 18, 2)
    if fijn:
        f += 0.15 * ruis(Q, 11, 17) + 0.07 * ruis(Q, 24, 13) + 0.01 * ruis(Q, 50, 14)   # gekartelde rand
        # eilandjes: kleine zwarte spikkels in het wit vlak bij een vlek (en witte in het zwart)
        sp = ruis(Q, 9.0, 15)
        dicht = gladstap(-0.22, -0.04, f) * gladstap(0.05, -0.02, f)
        f = np.maximum(f, (sp - 0.86) * 1.5 * dicht - 0.02 * (1 - dicht))
        gat = ruis(Q, 11.0, 16)
        f = np.where((f > 0) & (f < 0.12) & (gat > 0.97), f - (gat - 0.80) * 1.2, f)
    # kop
    d, u = kop_assen(sk)
    H0, H1 = bas(sk.J["Head"] / s), bas(sk.T["Head"] / s)
    t = np.clip((Q - H0) @ (H1 - H0) / np.sum((H1 - H0) ** 2), 0, 1)
    afst = np.linalg.norm(Q - (H0 + t[:, None] * (H1 - H0)), axis=1)
    kop = 1 - afst / 0.19
    for z in ("Left", "Right"):                         # oren zwart
        ea, ee = bas(sk.J[z + "Ear"] / s), bas(sk.T[z + "Ear"] / s)
        te = np.clip((Q - ea) @ (ee - ea) / np.sum((ee - ea) ** 2), 0, 1)
        kop = np.maximum(kop, 1 - np.linalg.norm(Q - (ea + te[:, None] * (ee - ea)), axis=1) / 0.09)
    voorkant = -(Q - H0) @ u                            # > 0 aan de bles-kant
    rb = 0.006 * ruis(Q, 6, 5) + (0.004 * ruis(Q, 30, 6) if fijn else 0)
    bles = (np.abs(Q[:, 0]) < 0.026 + 0.010 * t + 0.032 * gladstap(0.40, 0.05, t) + 2.5 * rb) & (voorkant > -0.02)
    snuit = np.linalg.norm(Q - (H1 - d * 0.04 + u * 0.02), axis=1) < 0.11 + 0.006 * ruis(Q, 6, 5)
    kuif = kuifveld(Q, sk) + 3 * rb > 0.5
    f = np.maximum(f, kop * 2)
    # witte aftekening van de kop wint van alles (geen rompvlekken of eilandjes in bles, snuit, kuif)
    inkop = (afst < 0.26) & (Q[:, 1] < H0[1] + 0.10)
    f = np.where(inkop & (bles | snuit | kuif), np.minimum(f, -0.5), f)
    # wit: onderbenen, buik, staart, kwast
    romp = (Q[:, 1] > -0.75) & (Q[:, 1] < 0.66)
    f -= 3 * gladstap(0.60, 0.50, Q[:, 2]) * romp
    f -= 3 * (Q[:, 1] > 0.64) * gladstap(1.0, 0.93, Q[:, 2]) * gladstap(0.10, 0.06, np.abs(Q[:, 0]))   # staart wit
    f -= 3 * gladstap(0.62, 0.52, Q[:, 2]) * (np.abs(Q[:, 0]) < 0.2)
    return f


def kuifveld(Q, sk):
    """0..1: de lichte krullenkuif boven op de kop tussen de oren (Q in basismaat)."""
    s = sk.s
    d, u = kop_assen(sk)
    H0, H1 = bas(sk.J["Head"] / s), bas(sk.T["Head"] / s)
    t = (Q - H0) @ (H1 - H0) / np.sum((H1 - H0) ** 2)
    hoog = -(Q - H0) @ u
    return gladstap(-0.12, 0.0, t) * gladstap(0.32, 0.18, t) * gladstap(0.05, 0.085, hoog) *         gladstap(0.075, 0.045, np.abs(Q[:, 0]))


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


def oog_c(sk, sg):
    d, u = kop_assen(sk)
    return sk.J["Head"] + (d * OOG[0] + np.array((sg * OOG[1], 0, 0)) - u * OOG[2]) * sk.s


OOG = (0.13, 0.096, 0.030, 0.027)       # langs de kop, opzij, omhoog (-u), straal: basismaat


def oog_uit(sk, sg):
    """Kijkrichting van het oog: opzij, iets naar voren en omhoog."""
    d, u = kop_assen(sk)
    return nrm(np.array((sg * 1.0, 0, 0)) + 0.2 * d - 0.15 * u)


def oogveld(P, sk):
    """> 0 binnen de ogen (eigen vlakken, mat_vast: echte oogkleur ook in een zwarte kop)."""
    f = np.full(len(P), -1.0)
    for sg in (1, -1):
        kap = oog_c(sk, sg) + oog_uit(sk, sg) * OOG[3] * 0.6 * sk.s
        f = np.maximum(f, OOG[3] * 0.76 * sk.s - np.linalg.norm(P - kap, axis=1))
    return f


def snij_ogen(o, sk):
    """Snijdt de mesh langs de oogranden: material_index 0 vacht (vlekken zitten in het masker), 1 oog (vast)."""
    bm = bmesh.new()
    bm.from_mesh(o.data)
    lay2 = snij_langs(bm, lambda P: oogveld(P, sk), "oog")
    for fc in bm.faces:
        fc.material_index = 1 if np.mean([v[lay2] for v in fc.verts]) > 0 else 0
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
    for v in bm.verts:                            # decimeren mag niet onder de grond prikken (klauwpunten)
        if v.co.z < 0:
            v.co.z = 0.0
    bmesh.ops.triangulate(bm, faces=bm.faces)
    bmesh.ops.dissolve_degenerate(bm, dist=1e-5, edges=bm.edges)
    # lange splinters (decimeren verbindt soms de zool met de knie): opdelen, zodat elk stuk zijn eigen
    # gewicht krijgt en niet als naald meedraait met de klauw
    def splinter(e):
        L_ = e.calc_length()
        return L_ > 0.08 and any(2 * f.calc_area() / L_ < 0.12 * L_ for f in e.link_faces)
    lang = [e for e in bm.edges if splinter(e)]
    if lang:
        bmesh.ops.subdivide_edges(bm, edges=lang, cuts=2, use_grid_fill=False)
        bmesh.ops.triangulate(bm, faces=[f for f in bm.faces if len(f.verts) > 3])
        log(naam, len(lang), "lange randen opgedeeld")
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
    if soort in ("pos", "id", "nrm"):
        em = nt.nodes.new("ShaderNodeEmission")
        if soort == "pos":
            g = nt.nodes.new("ShaderNodeNewGeometry")
            nt.links.new(g.outputs["Position"], em.inputs["Color"])
        elif soort == "nrm":                      # wereldnormaal (glad), als n*0,5+0,5
            g = nt.nodes.new("ShaderNodeNewGeometry")
            vm = nt.nodes.new("ShaderNodeVectorMath")
            vm.operation = "MULTIPLY_ADD"
            vm.inputs[1].default_value = (0.5, 0.5, 0.5)
            vm.inputs[2].default_value = (0.5, 0.5, 0.5)
            nt.links.new(g.outputs["Normal"], vm.inputs[0])
            nt.links.new(vm.outputs[0], em.inputs["Color"])
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
    if soort in ("pos", "id", "nrm"):
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
    beelden = {k: BM.beeld("_" + k, RES) for k in ("pos", "id", "nrm", "normaal", "ao")}
    eerst = True
    for i, (naam, o) in enumerate(delen.items()):
        t1 = time.time()
        me = o.data
        oud = list(me.materials)
        oud_idx = np.zeros(len(me.polygons), np.int32)
        me.polygons.foreach_get("material_index", oud_idx)
        for o2 in delen.values():
            o2.hide_render = o2 is not o
        for soort in ("pos", "id", "nrm"):
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
    Q = bas(P / s)
    n = len(P)
    kl = np.ones((n, 3)) * GRIJS
    H = np.zeros(n)
    ruw = np.full(n, 0.72)
    met = np.zeros(n)
    L = deel == 0
    N = B["nrm"][ys, xs, :3].astype(np.float64) * 2 - 1
    N /= np.linalg.norm(N, axis=1, keepdims=True) + 1e-9
    d, u = kop_assen(sk)
    H0, H1 = bas(sk.J["Head"] / s), bas(sk.T["Head"] / s)
    tk = np.clip((Q - H0) @ (H1 - H0) / np.sum((H1 - H0) ** 2), -0.5, 1.5)
    kopafst = np.linalg.norm(Q - (H0 + np.clip(tk, 0, 1)[:, None] * (H1 - H0)), axis=1)
    # --- haarrichting: gewichten per streek (romp, buik, been, kop, staart), elk een vaste 3D-richting
    w_kop = gladstap(0.24, 0.17, kopafst) * (tk > -0.3)
    w_staart = ((Q[:, 1] > 0.62) & (Q[:, 2] < 1.0)).astype(float)
    w_been = gladstap(0.50, 0.40, Q[:, 2]) * (1 - w_staart)
    w_buik = gladstap(-0.35, -0.70, N[:, 2]) * (1 - w_been) * (1 - w_kop) * (1 - w_staart)
    w_romp = np.clip(1 - w_kop - w_been - w_buik - w_staart, 0, 1)
    streken = [  # (gewicht, richting, fijn dwars/langs, pluk dwars/langs, hoogte fijn/pluk m)
        (w_romp, (0, 0.55, -1.0), (190, 16), (45, 4), (0.00075, 0.00160)),
        (w_buik, (0, 1.0, -0.15), (170, 9), (60, 4), (0.00090, 0.00160)),     # buiklijn: langer haar
        (w_been, (0, 0.12, -1.0), (230, 22), (80, 9), (0.00050, 0.00070)),
        (w_kop, tuple(d), (230, 22), (90, 9), (0.00050, 0.00070)),
        (w_staart, (0, 0.05, -1.0), (200, 4), (70, 2), (0.00090, 0.00200)),
    ]

    def streng(t, fd, fl, seed, octv=2, Qp=None):
        Qp = Q if Qp is None else Qp
        t = nrm(t)
        Qa = Qp * fd + np.outer(Qp @ t, t) * (fl - fd)
        return ruis(Qa, 1.0, seed, octv)

    haar = np.zeros(n)          # -1..1, fijne strengen + plukken (voor kleur, ruwheid, randen)
    H_haar = np.zeros(n)
    rand_streep = np.zeros(n)
    for i, (w, t, fijn, pluk, amp) in enumerate(streken):
        sel = w > 1e-3
        if not sel.any():
            continue
        Qs = Q[sel]
        hf = streng(t, *fijn, 50 + i, Qp=Qs)
        hp = streng(t, *pluk, 60 + i, Qp=Qs)
        rs = streng(t, 55, 5, 70 + i, 1, Qp=Qs)
        haar[sel] += w[sel] * (0.55 * hf + 0.45 * hp)
        H_haar[sel] += w[sel] * (amp[0] * hf + amp[1] * hp)
        rand_streep[sel] += w[sel] * rs
    # kuif: krullen, langer haar; kwast: lange strengen (zit al in w_staart, extra hoogte)
    kuif = kuifveld(Q, sk) * L
    krul = ruis(Q, 120, 80, 2)
    haar = haar * (1 - kuif) + kuif * krul
    H_haar = H_haar * (1 - kuif) + kuif * 0.0026 * krul
    kw = gladstap(0.52, 0.40, Q[:, 2]) * (Q[:, 1] > 0.62) * L
    H_haar += kw * 0.0008 * streng((0, 0.05, -1), 260, 3, 81)
    H += H_haar * L
    # --- vlekkenmasker (per texel): rand breekt langs de haarrichting
    fv = vlekveld(P, sk) + 0.01 * rand_streep + 0.035 * haar
    M = gladstap(-0.016, 0.016, fv) * L
    bruinrand = gladstap(0.0, 0.03, fv) * gladstap(0.09, 0.03, fv)      # bruine waas net binnen de rand
    # --- kleur wit: crème-zweem, vuil aan buik en benen, haarlicht
    lage = ruis(Q, 3.0, 1, 2)
    wit = np.ones((n, 3)) * GRIJS * np.array([1.0, 0.975, 0.935])
    creme = np.clip(0.5 + 0.8 * lage, 0, 1)
    wit *= (1 - 0.14 * creme[:, None] * np.array([0.0, 0.25, 0.75]))
    warm = gladstap(0.75, 0.35, Q[:, 2])                      # buik en benen warm gebroken wit
    wit *= (1 - 0.10 * warm[:, None] * np.array([0.1, 0.4, 0.9]))
    wit *= (1 + 0.035 * ruis(Q, 9, 2))[:, None]
    buikvuil = gladstap(0.70, 0.52, Q[:, 2]) * gladstap(-0.2, -0.6, N[:, 2]) * (1 - w_been)
    wit *= (1 - ((0.10 + 0.08 * ruis(Q, 7, 3)) * buikvuil)[:, None] * np.array([0.6, 0.85, 1.2]))
    vuil = gladstap(0.42, 0.05, Q[:, 2]) * (0.7 + 0.3 * ruis(Q * np.array([1, 1, 0.3]), 18, 4)) + \
        0.25 * gladstap(0.55, 0.40, Q[:, 2]) * (1 - w_staart)
    knie = np.zeros(n)
    for z in ("Left", "Right"):
        for b in ("FrontCannon", "HindCannon"):
            knie = np.maximum(knie, gladstap(0.07, 0.02, np.linalg.norm(Q - bas(sk.J[z + b] / s), axis=1)))
    vuil = np.clip(vuil + 0.5 * knie, 0, 1)
    wit *= (1 - vuil[:, None] * np.array([0.30, 0.38, 0.50]))
    wit *= (1 + 0.16 * haar)[:, None]                   # haarpunten licht, wortels in de schaduw
    # --- kleur zwart: bruinzwarte glans, verbleekt op rug en lichtzijde, haarstructuur sterker
    v0 = srgb(TINT["vlek"])
    bleek = np.clip(ruis(Q, 2.4, 7, 2) * 1.8 - 0.1, 0, 1) * (0.5 + 0.5 * gladstap(0.75, 1.05, Q[:, 2]))
    zwart = np.ones((n, 3)) * (1 + 0.18 * ruis(Q, 5, 8))[:, None]
    zwart *= 1 + bleek[:, None] * np.array([1.4, 0.95, 0.55])
    zwart *= 1 + (bruinrand * (0.6 + 0.4 * haar))[:, None] * np.array([1.6, 1.0, 0.5])
    zwart *= (1 + 0.45 * haar + 0.15 * rand_streep)[:, None]
    zwart *= 1 + (0.45 * np.clip(ruis(Q, 6.5, 24, 2) * 1.6 - 0.3, 0, 1))[:, None] * np.array([0.95, 0.95, 1.0])
    kam = np.clip(haar * 1.8 - 0.35, 0, 1)
    zwart *= 1 + kam[:, None] * np.array([1.1, 0.85, 0.6])                    # bruingrijze glans op de plukken
    zwart *= (1 + 0.25 * ruis(Q * np.array([1, 1, 0.5]), 18, 9))[:, None]    # lokken: tweede toon
    zwart *= v0                                          # textuur = vlek-standaard x detail (zie DELEN)
    kl = wit * (1 - M[:, None]) + zwart * M[:, None]
    ruw = 0.80 - 0.06 * haar - M * (0.16 + 0.05 * haar)
    # hoeven: alles onder de kroonrand donker en glad
    kroon = 0.075 + 0.006 * ruis(Q, 30, 5)
    hoef = gladstap(kroon + 0.006, kroon - 0.006, Q[:, 2]) * L
    kl = kl * (1 - hoef[:, None]) + hoef[:, None] * np.array([0.050, 0.045, 0.042]) * (1 + 0.3 * ruis(Q, 60, 6))[:, None]
    ruw = ruw * (1 - hoef) + 0.45 * hoef
    H = H * (1 - hoef) + hoef * 0.00012 * np.sin(Q[:, 2] * 700 + 3 * ruis(Q, 40, 23))   # groeiringen (geen haar)
    M = M * (1 - hoef)
    for zijde in ("Left", "Right"):
        for b in ("FrontHoof", "HindHoof"):
            ko = bas(sk.J[zijde + b] / s)
            x0 = sk.T[zijde + b][0] / s
            gl = np.exp(-((Q[:, 0] - x0) / 0.004) ** 2) * hoef * (Q[:, 2] < 0.07)
            kl *= (1 - 0.8 * gl[:, None])
            H -= 0.002 * gl
    # --- snuit: roze, vochtig, grijze spikkels, filtrum, neusgaten diep donker, mondlijn
    sn = np.linalg.norm(Q - (H1 - d * 0.005), axis=1)
    snuit = gladstap(0.088, 0.066, sn + 0.004 * ruis(Q, 40, 7)) * L
    roze = np.array([1.0, 0.66, 0.62]) * (0.9 + 0.1 * ruis(Q, 50, 7))[:, None]
    spik = gladstap(0.45, 0.75, ruis(Q, 45, 17, 2))
    roze = roze * (1 - 0.45 * spik[:, None] * np.array([0.7, 0.85, 0.8]))
    kl = kl * (1 - snuit[:, None]) + snuit[:, None] * GRIJS * roze
    M = M * (1 - snuit)
    ruw = ruw * (1 - snuit) + (0.30 + 0.1 * spik) * snuit
    H = H * (1 - snuit) + snuit * 0.0006 * np.abs(ruis(Q, 140, 8))       # poriën
    fil = np.exp(-(Q[:, 0] / 0.0035) ** 2) * gladstap(0.0, 0.04, (Q - H1) @ u + 0.03) * snuit
    kl *= (1 - 0.35 * fil[:, None])
    H -= 0.0012 * fil
    for sg in (1, -1):
        nc = H1 + d * 0.028 - u * 0.024 + np.array((sg * 0.034, 0, 0))
        ng = np.linalg.norm((Q - nc) / np.array((1.2, 1.0, 0.8)), axis=1)
        gat = gladstap(0.026, 0.012, ng) * L
        kl *= (1 - 0.85 * gat[:, None])
        ruw = ruw * (1 - gat) + 0.25 * gat
    # mondlijn: donkere naad tussen boven- en onderkaak
    kin = bas(sk.T["Jaw"] / s)
    mond = np.exp(-(((Q - kin) @ u + 0.035) / 0.006) ** 2) * gladstap(0.10, 0.06, np.linalg.norm(Q - kin, axis=1)) * L
    kl *= (1 - 0.7 * mond[:, None])
    # --- ogen: donkerbruine bol met iris, pupil, glans; leden met donkere rand en wimpers
    for sg in (1, -1):
        oc = bas(oog_c(sk, sg) / s)
        uit = oog_uit(sk, sg)
        kap = oc + uit * OOG[3] * 0.6                # bol gezien door de oogspleet: kap rond de as
        og = np.linalg.norm(Q - kap, axis=1)
        oog = gladstap(OOG[3] * 0.80, OOG[3] * 0.72, og) * (deel == 0)
        ic = oc + uit * OOG[3]
        di = np.linalg.norm(Q - ic, axis=1)
        bol = np.array([0.020, 0.011, 0.007]) * (1 + 0.15 * ruis(Q, 300, 19))[:, None]
        iris = gladstap(0.016, 0.012, di)
        bol = bol * (1 - iris[:, None]) + iris[:, None] * np.array([0.075, 0.035, 0.014]) * (0.8 + 0.4 * ruis(Q, 500, 20))[:, None]
        dp = np.sqrt(((Q - ic) @ d / 1.7) ** 2 + ((Q - ic) @ u) ** 2 + ((Q - ic)[:, 0] * 0.2) ** 2)
        pup = gladstap(0.0065, 0.005, dp)
        bol = bol * (1 - pup[:, None]) + pup[:, None] * 0.006
        glans = gladstap(0.0042, 0.0022, np.linalg.norm(Q - (ic - u * 0.007 + d * 0.004), axis=1))
        bol = bol + glans[:, None] * 0.55                                   # natte glans (vangt licht)
        hoek = gladstap(0.007, 0.003, np.linalg.norm(Q - (oc + nrm(uit + 0.9 * d) * OOG[3]), axis=1))
        bol = bol * (1 - hoek[:, None]) + hoek[:, None] * np.array([0.35, 0.22, 0.18])   # roze ooghoek
        kl = kl * (1 - oog[:, None]) + oog[:, None] * bol
        M = M * (1 - oog)
        ruw = ruw * (1 - oog) + 0.06 * oog
        H = H * (1 - oog)
        # lidrand: smalle kale rand rond het oog, wimpers aan het bovenlid (strepen naar buiten-boven)
        rand = gladstap(OOG[3] * 0.98, OOG[3] * 0.78, og) * (1 - oog) * L
        kl = kl * (1 - 0.7 * rand[:, None]) + 0.7 * rand[:, None] * np.array([0.028, 0.020, 0.018])
        M = M * (1 - rand)
        ruw = ruw * (1 - rand) + 0.35 * rand
        boven = np.clip(-((Q - oc) @ u) / OOG[3], 0, 1)
        ang = np.arctan2((Q - oc) @ d, -((Q - oc) @ u))
        wimp = gladstap(OOG[3] * 1.35, OOG[3] * 0.85, og) * gladstap(0.3, 0.7, boven) * L * (1 - oog)
        lijn = np.clip(np.sin(ang * 60 + 3 * ruis(Q, 60, 21)) * 2 - 0.6, 0, 1)
        kl *= (1 - 0.8 * (wimp * lijn)[:, None])
        H += wimp * lijn * 0.0006
    # --- oren: binnenkant licht grijsroze met lange witte haren langs de rand
    for z in ("Left", "Right"):
        ea, ee = bas(sk.J[z + "Ear"] / s), bas(sk.T[z + "Ear"] / s)
        e = nrm(ee - ea)
        te = np.clip((Q - ea) @ e / np.linalg.norm(ee - ea), -1, 2)
        dist = np.linalg.norm(Q - (ea + np.clip(te, 0, 1)[:, None] * (ee - ea)), axis=1)
        tt = nrm(np.array([0, -1.0, 0]) - e * e[1] * -1)
        w_ = nrm(np.cross(e, tt))
        tt = np.cross(w_, e)
        binnen = (te > 0.2) * gladstap(0.075, 0.045, dist) * gladstap(0.2, 0.6, N @ tt) * L
        hr = streng(e, 160, 8, 90)
        haren = np.clip(hr * 1.5 - 0.3, 0, 1) * gladstap(0.03, 0.065, dist)        # lange haren aan de binnenrand
        bk = np.array([0.085, 0.058, 0.052]) * (1 - haren[:, None]) + haren[:, None] * np.array([0.42, 0.38, 0.34])
        kl = kl * (1 - binnen[:, None]) + binnen[:, None] * bk
        M = M * (1 - binnen)
        H += binnen * 0.0010 * hr
    # kuif en kwast: crème
    km = (kuif * (1 - M) * 0.85)[:, None]
    kl = kl * (1 - km) + km * GRIJS * np.array([0.86, 0.79, 0.68]) * (0.62 + 0.5 * np.clip(krul + 0.3, 0, 1.2))[:, None]
    kws = streng((0, 0.05, -1), 220, 3, 82)
    kl = kl * (1 - kw[:, None]) + kw[:, None] * kl * np.array([0.98, 0.86, 0.64]) * (1 + 0.25 * kws)[:, None]
    # nekplooien (onder de hals)
    hals = gladstap(-0.56, -0.64, Q[:, 1]) * gladstap(-0.86, -0.78, Q[:, 1]) * gladstap(0.88, 0.76, Q[:, 2]) * \
        (np.abs(Q[:, 0]) < 0.06) * L
    H += hals * 0.0003 * np.sin(Q[:, 1] * 2 * np.pi / 0.03 + 2 * ruis(Q, 8, 10))
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
    return ys, xs, kl, H, ruw, met, deel, M


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
    ys, xs, kl, H, ruw, met, deel, M = componeer(B, mpp, sk)
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
    VM = np.zeros((h, w, 3), np.float32)
    VM[ys, xs] = M[:, None]
    VM = BM.dilateer(VM, mask, 10)
    bewaar(VM, "koe_vlek", True)                     # vlekkenmasker (los bestand, voor de hertint-shader)
    kleur = bewaar(K, "koe_kleur", False, jpg=True)
    normaal = bewaar(Nimg, "koe_normaal", True)
    orm = bewaar(ORM[::2, ::2] if RES >= 2048 else ORM, "koe_orm", True)
    log("texturen", f"{time.time() - t1:.1f}s")
    return kleur, normaal, orm


def materialen(delen, kleur, normaal, orm):
    mats = {k: BM.pbr("mat_" + k, kleur, normaal, orm) if k == "lijf" else
            BM.pbr("mat_" + k, kleur, normaal, orm, tuple(srgb(v))) for k, v in TINT.items() if k != "vlek"}
    # hertint-schema (glTF extras -> Godot meta): zie DELEN in de docstring en koe_vacht.gdshader
    mats["lijf"]["tint_vacht"] = TINT["lijf"]
    mats["lijf"]["tint_vlek"] = TINT["vlek"]
    mats["lijf"]["vlek_standaard"] = TINT["vlek"]
    mats["lijf"]["vlek_masker"] = "textures_koe/koe_vlek.png"
    vast = BM.pbr("mat_vast", kleur, normaal, orm)
    for naam, o in delen.items():
        me = o.data
        idx = np.zeros(len(me.polygons), np.int32)
        me.polygons.foreach_get("material_index", idx)
        me.materials.clear()
        if naam == "lijf":
            me.materials.append(mats["lijf"])
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
    kl = {"oog": "#140c08", "lijf": "#ece9e2", "uier": "#e7b3a8", "halsband": "#6e4226", "bel": "#b08a3a"}
    for naam, o in delen.items():
        me = o.data
        idx = np.zeros(len(me.polygons), np.int32)
        me.polygons.foreach_get("material_index", idx)
        me.materials.clear()
        for k in (["lijf", "oog"] if naam == "lijf" else [naam]):
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
        # eerst gladstrijken (bone heat geeft harde naden), daarna de vaste toewijzingen
        glad_gewichten(o, 0.5, 3)
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
        zet((P[:, 2] < sk.J["Tail3"][2]) & (P[:, 1] > float(R.romp_y(0.62)) * s), "Tail3")
        # tegen het knijpen in de flank en achter de elleboog: de romp laat de bovenbenen los
        romp_los(o, sk)
        onderbenen(o, sk)
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


def glad_gewichten(o, a=0.5, n=3):
    """Laplace-gladstrijken van alle vertexgroepen (numpy, buren via de randen)."""
    me = o.data
    nv, ng = len(me.vertices), len(o.vertex_groups)
    W = np.zeros((nv, ng))
    for v in me.vertices:
        for ge in v.groups:
            W[v.index, ge.group] = ge.weight
    E = np.zeros(len(me.edges) * 2, np.int64)
    me.edges.foreach_get("vertices", E)
    E = E.reshape(-1, 2)
    P = np.array([v.co for v in me.vertices])
    E = E[np.linalg.norm(P[E[:, 0]] - P[E[:, 1]], axis=1) < 0.05]       # niet langs splinters smeren
    deg = np.bincount(E.ravel(), minlength=nv).astype(float)[:, None]
    for _ in range(n):
        S = np.zeros_like(W)
        np.add.at(S, E[:, 0], W[E[:, 1]])
        np.add.at(S, E[:, 1], W[E[:, 0]])
        W = (1 - a) * W + a * S / np.maximum(deg, 1)
    for gi, g in enumerate(o.vertex_groups):
        nz = np.nonzero(W[:, gi] > 1e-4)[0]
        g.remove(list(range(nv)))
        for vi in nz:
            g.add([int(vi)], float(W[vi, gi]), "REPLACE")


def onderbenen(o, sk):
    """Onderbeen (onder voorknie/hak) star per bot: pijp en klauw, met korte overgangen bij het gewricht.
    Bone heat + gladstrijken laten daar anders losse vertices aan verre botten hangen (naalden)."""
    s = sk.s
    me = o.data
    P = np.array([v.co for v in me.vertices])
    gi = {g.name: g for g in o.vertex_groups}
    for z in ("Left", "Right"):
        for boven, pijp, klauw in (("ForeArm", "FrontCannon", "FrontHoof"), ("Shin", "HindCannon", "HindHoof")):
            kn, ko = sk.J[z + pijp], sk.J[z + klauw]
            zijde = np.sign(kn[0])
            sel = (P[:, 2] < kn[2] + 0.03 * s) & (np.sign(P[:, 0]) == zijde) &                 (seg_afst(P, kn, sk.T[z + klauw]) < 0.10 * s)
            ids = np.nonzero(sel)[0]
            if not len(ids):
                continue
            zp = P[ids, 2]
            w_k = gladstap(ko[2] + 0.015 * s, ko[2] - 0.025 * s, zp)          # klauw
            w_b = gladstap(kn[2] - 0.03 * s, kn[2] + 0.03 * s, zp) * (1 - w_k)  # boven het gewricht
            w_p = 1 - w_k - w_b
            for g in o.vertex_groups:
                g.remove(ids.tolist())
            for nm, w in ((z + klauw, w_k), (z + pijp, w_p), (z + boven, w_b)):
                g = gi.get(nm) or o.vertex_groups.new(name=nm)
                gi[nm] = g
                for vi, wv in zip(ids, w):
                    if wv > 1e-3:
                        g.add([int(vi)], float(wv), "REPLACE")


def seg_afst(P, a, b):
    ab = b - a
    t = np.clip((P - a) @ ab / (ab @ ab), 0, 1)
    return np.linalg.norm(P - (a + t[:, None] * ab), axis=1)


def romp_los(o, sk):
    """Haalt gewicht van Thigh/UpperArm/ForeArm weg op de romp (voor de dij, achter de elleboog, boven
    de elleboog aan de binnenkant) en geeft het aan Hips resp. Spine2. Zachte overgang over ~10 cm."""
    s = sk.s
    me = o.data
    P = np.array([v.co for v in me.vertices])
    naam = {g.index: g.name for g in o.vertex_groups}
    gi = {g.name: g for g in o.vertex_groups}
    regels = []
    for z in ("Left", "Right"):
        hp, kn = sk.J[z + "Thigh"], sk.J[z + "Shin"]
        # voor de dij (flank, buik): y kleiner dan de heupkop - 0,08, boven de knie
        f = gladstap(0.0, 0.12 * s, (hp[1] - 0.06 * s) - P[:, 1]) * gladstap(kn[2] - 0.06 * s, kn[2] + 0.04 * s, P[:, 2])
        # binnenkant (buik/uier-zijde)
        f = np.maximum(f, gladstap(0.0, 0.08 * s, (np.abs(hp[0]) - 0.07 * s) - np.abs(P[:, 0])) *
                       gladstap(kn[2] - 0.04 * s, kn[2] + 0.06 * s, P[:, 2]))
        f = f * gladstap(0.10 * s, 0.17 * s, seg_afst(P, hp, kn))          # het been zelf blijft
        regels.append((z + "Thigh", "Hips", f))
        regels.append((z + "Shin", "Hips", f * gladstap(kn[2], kn[2] + 0.06 * s, P[:, 2])))
        el = sk.J[z + "ForeArm"]
        sh = sk.J[z + "UpperArm"]
        # achter de elleboog (singel) en eronder naar de borst
        f = gladstap(0.0, 0.10 * s, P[:, 1] - (el[1] + 0.04 * s)) * gladstap(el[2] - 0.08 * s, el[2] + 0.02 * s, P[:, 2])
        f = np.maximum(f, gladstap(0.0, 0.07 * s, (np.abs(sh[0]) - 0.06 * s) - np.abs(P[:, 0])) *
                       gladstap(el[2] - 0.06 * s, el[2] + 0.04 * s, P[:, 2]))
        f = f * gladstap(0.08 * s, 0.14 * s, seg_afst(P, sh, el))
        regels.append((z + "UpperArm", "Spine2", f))
        regels.append((z + "ForeArm", "Spine2", f))
    # algemeen: wat ver van de eigen beenketen ligt (buik, flank, borst) hoort niet bij dat been
    for z in ("Left", "Right"):
        for keten, doel in ((["UpperArm", "ForeArm", "FrontCannon"], "Spine2"), (["Thigh", "Shin", "HindCannon"], "Hips")):
            a = [sk.J[z + k] for k in keten] + [sk.T[z + keten[-1]]]
            dist = np.min([seg_afst(P, a[i], a[i + 1]) for i in range(len(a) - 1)], axis=0)
            f = gladstap(0.11 * s, 0.17 * s, dist)
            for k in keten[:2]:
                regels.append((z + k, doel, f))
    for bot, doel, f in regels:
        if bot not in gi:
            continue
        g = gi[bot]
        dg = gi.get(doel) or o.vertex_groups.new(name=doel)
        gi[doel] = dg
        for vi in np.nonzero(f > 1e-3)[0]:
            v = me.vertices[int(vi)]
            for ge in v.groups:
                if ge.group == g.index:
                    weg = ge.weight * float(f[vi])
                    ge.weight -= weg
                    dg.add([int(vi)], weg, "ADD")
                    break


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
        BM.studio(sc, 900, 0.7, 0.7, doel=(0, -0.97 * rig["schaal"], 0.90 * rig["schaal"]), yaw=yw, pitch=pt)
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


def lig_blad(sc, rig, tag=""):
    """Ligpose (sterven eind, geboorte begin, knielen) van opzij, voor, schuin en van boven."""
    tmp = bpy.app.tempdir
    toon_bel(sc, False)
    pan = []
    for act, f in (("sterven", 60), ("geboorte", 0), ("sterven", 26)):
        R.zet_actie(rig, act)
        sc.frame_set(f)
        for yw, pt in ((180, 4), (0, 4), (225, 30), (270, 10)):
            BM.studio(sc, 180, 2.4, 1.2, doel=(0, -0.2, 0.40), yaw=yw, pitch=pt)
            pan.append(BM.bijsnijden(BM.render_np(sc, os.path.join(tmp, f"g_{act}_{f}_{yw}.png"))))
    BM.schrijf(BM.onder(BM.plak(pan[:4]), BM.plak(pan[4:8]), BM.plak(pan[8:])), os.path.join(PREV, f"koe_lig{tag}.png"))
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
    snij_ogen(lijf, sk)
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
    if "lig" in OPTS:
        lig_blad(sc, rig, tag)
    os.makedirs(PREV, exist_ok=True)
    bpy.ops.wm.save_as_mainfile(filepath=os.path.join(PREV, "koe.blend"))
    log("KLAAR")


if __name__ == "__main__":
    main()
