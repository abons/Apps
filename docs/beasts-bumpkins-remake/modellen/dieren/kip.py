"""Kip (roodbruine hen), game-ready: mesh, skin, atlas, animaties -> kip.glb, plus een los ei.glb
(Blender 5.2 headless -> Godot 4).

Draaien:
  blender -b -P kip.py -- [res=1024] [snel] [vergelijk] [poses] [geen_export] [tag=_r1]
  blender -b -P kip.py -- ei            -> alleen ei.glb
- `snel`: weinig samples (silhouetrondes).
- `vergelijk`: preview/kip_vergelijk.png (concept naast renders zij, 3/4, iso, voor + kop dichtbij).
- `poses`: preview/kip_poses.png (extreme standen uit alle clips, iso + van opzij).
Doel: lokaal/concept/img/kippen_sheet.jpg (links: roodbruine hen; rode kam en lellen, gele poten,
donkere staartveren). De sprite (bb_original/chicken.png) komt in geen enkele preview: die mag nooit
gecommit worden.

Uitvoer kip.glb: armatuur `kip_rig` (kip_rig.py) met de acties idle, lopen, pikken, zitten; twee
mesh-nodes op hetzelfde skelet met één materiaal `mat_kip` en een gedeelde atlas in textures_kip/
(kip_kleur.jpg, kip_normaal.png, kip_orm.png; R=AO G=ruw B=metaal):
| node  | inhoud                                                            |
| ----- | ----------------------------------------------------------------- |
| lijf  | romp, borst, vleugels, dijen, hals, kop, kam, lellen, snavel, staart; |
|       | oog, gezichtshuid en veren zitten in de textuur                    |
| poten | loopbenen en tenen (fijner rooster: de tenen zijn maar ~6 mm dik)  |

Bouw: zoals de koe (koe.py): een signed distance field (numpy; afgeronde kegels en ellipsoïden met een
label per primitief, glad samengevoegd) -> surface nets = hoog-poly; gedecimeerd (symmetrisch) =
laag-poly. Kleur per texel uit de gebakken positie: het label met de kleinste afstand (zacht gemengd)
kiest kleur en verenpatroon. Veren = een 3D-Voronoi van schubjes die met de veerrichting mee scheef
getrokken zijn (de stroomopwaartse veer ligt bovenop), met donkere of lichte zoom, schacht en een
hoogteveld voor de normaalkaart. Gewichten: per label een vaste set botten (afstand tot het bot),
gladgestreken; de poten star per bot. Cycles bakt normaal en AO van hoog naar laag.
"""
import json
import math
import os
import sys
import time

import bmesh
import bpy
import numpy as np
from mathutils import Vector

HERE = os.path.dirname(os.path.abspath(__file__))
MOD = os.path.dirname(HERE)
sys.path.insert(0, HERE)
import kip_rig as R  # noqa: E402
import dieren_basis as BM  # noqa: E402

argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
OPTS = {a.split("=")[0]: (a.split("=", 1)[1] if "=" in a else "1") for a in argv}
SNEL = "snel" in OPTS
RES = int(OPTS.get("res", 1024))
SPP = 0.25 if SNEL else 1.0
TEX = os.path.join(HERE, "textures_kip")
PREV = os.path.join(HERE, "preview")
GLB = os.path.join(HERE, "kip.glb")
CONCEPT = os.path.join(MOD, "..", "lokaal", "concept", "img", "kippen_sheet.jpg")
T0 = time.time()
H_LIJF, H_POOT = 0.0030, 0.0014
DOEL = {"lijf": 4300, "poten": 1100}
DELEN = ["lijf", "poten"]
srgb, naar_srgb, ruis, gladstap = BM.srgb, BM.naar_srgb, BM.ruis, BM.gladstap


def log(*a):
    print(f"[kip {time.time() - T0:6.1f}s]", *a, flush=True)


# --- SDF (zoals koe.py, met een label per primitief) -------------------------------------------------
def smin(a, b, k):
    h = np.maximum(k - np.abs(a - b), 0) / k
    return np.minimum(a, b) - h * h * k * 0.25


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
    L = (P - c) @ assen.T
    k0 = np.linalg.norm(L / r, axis=1)
    k1 = np.linalg.norm(L / (r * r), axis=1)
    return k0 * (k0 - 1.0) / np.maximum(k1, 1e-9)


def kantel(g):
    """Assen van een ellipsoïde gekanteld om X: + = achterkant (+y) omhoog."""
    a = math.radians(g)
    return np.array([[1, 0, 0], [0, math.cos(a), math.sin(a)], [0, -math.sin(a), math.cos(a)]])


class SDF:
    def __init__(self):
        self.prims = []

    def rc(self, a, b, r1, r2, k=0.01, lab="", m="+"):
        a, b = np.asarray(a, float), np.asarray(b, float)
        rm = max(r1, r2) + k
        self.prims.append(("rc", (a, b, r1, r2), np.minimum(a, b) - rm, np.maximum(a, b) + rm, k, m, lab))

    def el(self, c, r, k=0.01, lab="", assen=None, m="+"):
        c, r = np.asarray(c, float), np.asarray(r, float)
        A = np.eye(3) if assen is None else np.asarray(assen, float)
        rm = r.max() + k
        self.prims.append(("el", (c, A, r), c - rm, c + rm, k, m, lab))

    def _een(self, soort, arg, Q):
        return sd_rondkegel(Q, *arg) if soort == "rc" else sd_ellips(Q, *arg)

    def __call__(self, P, grond=True):
        P = np.asarray(P, float)
        d = np.full(len(P), 1.0)
        for soort, arg, lo, hi, k, m, _ in self.prims:
            sel = np.all((P >= lo) & (P <= hi), axis=1)
            if not sel.any():
                continue
            v = self._een(soort, arg, P[sel])
            d[sel] = smin(d[sel], v, k) if m == "+" else -smin(-d[sel], v, k)
        if grond:
            d = np.maximum(d, -P[:, 2])
        return d

    def labels(self, P):
        """{label: kleinste afstand van de primitieven met dat label} (exact, zonder AABB)."""
        P = np.asarray(P, float)
        uit = {}
        for soort, arg, lo, hi, k, m, lab in self.prims:
            if m != "+" or not lab:
                continue
            v = self._een(soort, arg, P)
            uit[lab] = np.minimum(uit[lab], v) if lab in uit else v
        return uit

    def grens(self):
        lo = np.min([p[2] for p in self.prims if p[5] == "+"], 0)
        hi = np.max([p[3] for p in self.prims if p[5] == "+"], 0)
        return lo, hi


def oppervlak(sdf, h, naam, coll):
    """Surface nets (symmetrisch in x) op een rooster met stap h -> mesh-object, geprojecteerd."""
    lo, hi = sdf.grens()
    lo, hi = lo - 2 * h, hi + 2 * h
    lo[2] = max(lo[2], -2.5 * h)
    xm = max(-lo[0], hi[0])
    n = np.ceil((hi - lo) / h).astype(int) + 1
    n[0] = int(np.ceil(2 * xm / h)) + 1
    if n[0] % 2 == 0:
        n[0] += 1
    xs = [lo[i] + h * np.arange(n[i]) for i in range(3)]
    xs[0] = h * (np.arange(n[0]) - (n[0] - 1) / 2)
    F = np.empty(n, np.float32)
    YZ = np.stack(np.meshgrid(xs[1], xs[2], indexing="ij"), -1).reshape(-1, 2)
    for i, x in enumerate(xs[0]):
        F[i] = sdf(np.column_stack([np.full(len(YZ), x), YZ])).reshape(n[1], n[2])
    log(naam, "rooster", tuple(n), f"{F.size / 1e6:.1f}M")
    cel = np.full(tuple(n - 1), -1, np.int64)
    som = np.zeros(tuple(n - 1) + (3,))
    aantal = np.zeros(tuple(n - 1))
    binnen = F < 0
    kanten = []
    for ax in range(3):
        sl0, sl1 = [slice(None)] * 3, [slice(None)] * 3
        sl0[ax], sl1[ax] = slice(0, -1), slice(1, None)
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
        Qd = np.stack(hoek, 1)
        Qd[~inn] = Qd[~inn][:, ::-1]
        vlakken.append(Qd)
    Qd = np.concatenate(vlakken)
    Qd = Qd[(Qd >= 0).all(1)]
    e = h * 0.3
    for _ in range(3):
        d = sdf(V)
        g = np.column_stack([(sdf(V + np.array(o)) - d) / e for o in ((e, 0, 0), (0, e, 0), (0, 0, e))])
        g /= np.maximum((g * g).sum(1, keepdims=True), 1e-9)
        V = V - np.clip(d, -h, h)[:, None] * g
    V[:, 2] = np.maximum(V[:, 2], 0.0)
    me = bpy.data.meshes.new(naam)
    me.from_pydata(V.tolist(), [], Qd.tolist())
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


# --- Vorm ---------------------------------------------------------------------------------------------
def V3(x, y, z):
    return np.array([x, y, z], float)


KAM = [(-0.149, 0.368), (-0.137, 0.379), (-0.125, 0.385), (-0.112, 0.383), (-0.100, 0.374)]
KOP_C = V3(0, -0.122, 0.334)


def vorm_lijf():
    s = SDF()
    s.el(V3(0, 0.035, 0.205), (0.080, 0.130, 0.090), 0.030, "romp", kantel(14))
    s.el(V3(0, -0.045, 0.190), (0.071, 0.070, 0.082), 0.040, "borst")
    s.el(V3(0, 0.070, 0.162), (0.068, 0.080, 0.064), 0.040, "buik")
    s.el(V3(0, 0.112, 0.246), (0.056, 0.068, 0.052), 0.035, "rug", kantel(25))
    s.rc(V3(0, -0.058, 0.232), V3(0, -0.106, 0.312), 0.048, 0.030, 0.035, "hals")
    s.el(KOP_C, (0.028, 0.040, 0.032), 0.016, "kop")
    s.rc(V3(0, -0.149, 0.333), V3(0, -0.183, 0.323), 0.0105, 0.0025, 0.005, "snavel")
    s.rc(V3(0, -0.147, 0.325), V3(0, -0.171, 0.319), 0.0080, 0.0020, 0.004, "snavel")
    s.el(V3(0, -0.124, 0.366), (0.0062, 0.030, 0.015), 0.006, "kam")
    for i, (y, z) in enumerate(KAM):
        s.el(V3(0, y, z), (0.0052, 0.0075, 0.0105), 0.004, "kam")
    for sg in (1, -1):
        s.el(V3(sg * 0.0065, -0.147, 0.303), (0.0062, 0.0095, 0.0145), 0.006, "lel")
    s.el(V3(0, 0.165, 0.296), (0.030, 0.034, 0.080), 0.030, "staart", kantel(-16))
    s.el(V3(0, 0.188, 0.322), (0.018, 0.028, 0.058), 0.018, "staart", kantel(-26))
    for x, y, z, g in ((0.0, 0.176, 0.352, -6), (0.014, 0.196, 0.338, -30), (-0.014, 0.196, 0.338, -30),
                       (0.020, 0.210, 0.318, -48), (-0.020, 0.210, 0.318, -48)):
        s.el(V3(x, y, z), (0.009, 0.013, 0.040), 0.010, "staart", kantel(g))      # losse pennen: rafelig silhouet
    for sg in (1, -1):
        s.el(V3(sg * 0.077, 0.044, 0.214), (0.024, 0.100, 0.055), 0.006, "vleugel", kantel(8))
        s.el(V3(sg * 0.043, 0.022, 0.122), (0.031, 0.042, 0.044), 0.030, "dij")
    return s


def poot_punten(sg):
    x = sg * R.J["bal"][0]
    bal = V3(*R.jp("bal", sg))
    tenen = [(V3(x, -0.050, 0.0034), 0.0060, 0.0032), (V3(x - sg * 0.024, -0.036, 0.0034), 0.0054, 0.0030),
             (V3(x + sg * 0.026, -0.033, 0.0034), 0.0054, 0.0030), (V3(x + sg * 0.004, 0.027, 0.0034), 0.0050, 0.0028)]
    return bal, tenen


def vorm_poten():
    s = SDF()
    for sg in (1, -1):
        hak = V3(*R.jp("hak", sg))
        bal, tenen = poot_punten(sg)
        s.rc(hak, bal, 0.0092, 0.0072, 0.004, "poot")
        s.rc(hak, V3(hak[0], 0.012, 0.103), 0.0092, 0.0105, 0.004, "poot")
        for eind, r1, r2 in tenen:
            s.rc(bal, eind, r1, r2, 0.003, "teen")
    return s


def oog_c(sdf, sg):
    """Oogmidden op het kopoppervlak (Newton langs de gradiënt vanuit een punt naast de kop)."""
    p = KOP_C + np.array([sg * 0.040, -0.016, 0.009])
    for _ in range(30):
        d = sdf(p[None])[0]
        g = np.array([(sdf((p + o)[None])[0] - d) / 1e-4 for o in np.eye(3) * 1e-4])
        p = p - d * g / (g @ g)
    return p


# --- Laag-poly ----------------------------------------------------------------------------------------
def decimeer(hoog, naam, doel, coll):
    o = hoog.copy()
    o.data = hoog.data.copy()
    o.name = o.data.name = naam
    coll.objects.link(o)
    o.data.calc_loop_triangles()
    m = o.modifiers.new("dec", "DECIMATE")
    m.decimate_type = "COLLAPSE"
    m.ratio = doel / len(o.data.loop_triangles)
    m.use_symmetry = True
    m.symmetry_axis = "X"
    BM.ontkies()
    bpy.context.view_layer.objects.active = o
    o.select_set(True)
    bpy.ops.object.modifier_apply(modifier="dec")
    bm = bmesh.new()
    bm.from_mesh(o.data)
    for v in bm.verts:
        v.co.z = max(v.co.z, 0.0)
    bmesh.ops.triangulate(bm, faces=bm.faces)
    bmesh.ops.dissolve_degenerate(bm, dist=1e-6, edges=bm.edges)
    bm.to_mesh(o.data)
    bm.free()
    o.data.validate(verbose=False)
    o.data.shade_smooth()
    return o


def driehoeken(objs):
    n = 0
    for o in objs:
        o.data.calc_loop_triangles()
        n += len(o.data.loop_triangles)
    return n


# --- UV en bakken -------------------------------------------------------------------------------------
def uv_atlas(delen):
    BM.ontkies()
    for o in delen.values():
        while o.data.uv_layers:
            o.data.uv_layers.remove(o.data.uv_layers[0])
        o.data.uv_layers.new(name="UVMap")
        o.select_set(True)
    bpy.context.view_layer.objects.active = delen["lijf"]
    bpy.ops.object.mode_set(mode="EDIT")
    bpy.ops.mesh.select_all(action="SELECT")
    bpy.ops.uv.smart_project(angle_limit=math.radians(58), island_margin=0.0, area_weight=0.0,
                             correct_aspect=True, scale_to_bounds=False)
    bpy.ops.uv.select_all(action="SELECT")
    bpy.ops.uv.average_islands_scale()
    bpy.ops.uv.pack_islands(rotate=True, margin=0.006, scale=True, shape_method="CONCAVE")
    bpy.ops.object.mode_set(mode="OBJECT")
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
        g = nt.nodes.new("ShaderNodeNewGeometry")
        if soort == "pos":
            nt.links.new(g.outputs["Position"], em.inputs["Color"])
        elif soort == "nrm":
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


def bak(doel, highs, soort, img, ext=0.004, ray=0.01, margin=4, clear=False):
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


def bak_alles(delen, highs):
    sc = bpy.context.scene
    sc.render.engine = "CYCLES"
    log("cycles op", BM.gpu(sc))
    sc.world = sc.world or bpy.data.worlds.new("w")
    sc.world.light_settings.distance = 0.05
    beelden = {k: BM.beeld("_" + k, RES) for k in ("pos", "id", "nrm", "normaal", "ao")}
    eerst = True
    for i, (naam, o) in enumerate(delen.items()):
        me = o.data
        for o2 in delen.values():
            o2.hide_render = o2 is not o
        for soort in ("pos", "id", "nrm"):
            me.materials.clear()
            me.materials.append(bak_mat("_" + soort, soort, i))
            bak(o, [], soort, beelden[soort], margin=0, clear=eerst)
        me.materials.clear()
        me.materials.append(bak_mat("_doel", "pos"))
        hs = highs[naam]
        for h in hs:
            h.hide_render = False
        ext, ray = {"lijf": (0.005, 0.012), "poten": (0.002, 0.005)}[naam]
        bak(o, hs, "normaal", beelden["normaal"], ext, ray, clear=eerst)
        for o2 in delen.values():               # AO: de poten en het lijf schaduwen elkaar
            o2.hide_render = False
        bak(o, hs, "ao", beelden["ao"], ext, ray, clear=eerst)
        for h in hs:
            h.hide_render = True
        me.materials.clear()
        eerst = False
        log("  bak", naam)
    for o2 in delen.values():
        o2.hide_render = False
    return {k: BM.pixels(v) for k, v in beelden.items()}


# --- Texturen ---------------------------------------------------------------------------------------
# per label: kleur (sRGB), veerafstand (m), anisotropie (lengte/breedte), stroomrichting, zoomfactor
STREEK = {
    "romp":    ("#9c4719", 0.016, 1.25, (0, 1, -0.35), 0.72),
    "rug":     ("#8a3a15", 0.016, 1.35, (0, 1, -0.45), 0.70),
    "borst":   ("#cc7631", 0.013, 1.00, (0, 0.35, -1), 1.22),
    "buik":    ("#dca064", 0.013, 1.00, (0, 0.60, -1), 1.12),
    "dij":     ("#c27a3e", 0.011, 1.00, (0, 0.20, -1), 1.15),
    "hals":    ("#83301a", 0.010, 1.80, (0, 0.40, -1), 1.30),
    "kop":     ("#8c3b1a", 0.007, 1.20, (0, 1, 0.25), 1.10),
    "vleugel": ("#933e18", 0.017, 1.40, (0, 1, -0.25), 0.66),
    "staart":  ("#2b1b13", 0.016, 3.00, (0, 0.55, 0.85), 2.10),
}
VAST = {"kam": "#c3231b", "lel": "#bd221b", "snavel": "#d9a646", "poot": "#dfae48", "teen": "#d9a848"}
PASSEN = sorted({v[1] for v in STREEK.values()})


def hash3(I, seed=0):
    h = (I[:, 0] * 73856093 ^ I[:, 1] * 19349663 ^ I[:, 2] * 83492791 ^ seed * 2654435761) & 0xFFFFFFFF
    h = ((h ^ (h >> 13)) * 1274126177) & 0xFFFFFFFF
    return ((h ^ (h >> 16)) & 0xFFFF).astype(np.float64) / 65535.0


def veren(P, F, s, A, beta=1.5):
    """Schubjes: jittered rooster met stap s; score = afstand (langs de veer / A) - beta * langs.
    De veer stroomopwaarts (kleinste score) ligt bovenop. -> t (positie in de veer, ~-1..1.5),
    rand (0 op de grens), dwars (afstand tot de schacht / s), rnd per veer."""
    G = np.floor(P / s).astype(np.int64)
    best = np.full((len(P), 2), np.inf)
    t_b = np.zeros(len(P))
    dw_b = np.zeros(len(P))
    rnd = np.zeros(len(P))
    for dx in (-1, 0, 1):
        for dy in (-1, 0, 1):
            for dz in (-1, 0, 1):
                I = G + np.array([dx, dy, dz])
                j = np.column_stack([hash3(I, k) for k in (1, 2, 3)])
                C = (I + 0.15 + 0.7 * j) * s
                D = P - C
                langs = np.einsum("ij,ij->i", D, F) / (A * s)
                dwars = np.linalg.norm(D - (langs * A * s)[:, None] * F, axis=1) / s
                e = langs ** 2 + dwars ** 2 - beta * langs
                nieuw = e < best[:, 0]
                tweede = ~nieuw & (e < best[:, 1])
                best[:, 1] = np.where(nieuw, best[:, 0], np.where(tweede, e, best[:, 1]))
                best[:, 0] = np.where(nieuw, e, best[:, 0])
                t_b = np.where(nieuw, langs, t_b)
                dw_b = np.where(nieuw, dwars, dw_b)
                rnd = np.where(nieuw, hash3(I, 9) * 2 - 1, rnd)
    return t_b, best[:, 1] - best[:, 0], dw_b, rnd


def componeer(B, sdf_l, sdf_p, ogen):
    idm = B["id"]
    ys, xs = np.nonzero(idm[..., 1] > 0.5)
    deel = np.clip(np.round(idm[ys, xs, 0] * 8).astype(int) - 1, 0, 1)
    P = B["pos"][ys, xs, :3].astype(np.float64)
    N = B["nrm"][ys, xs, :3].astype(np.float64) * 2 - 1
    N /= np.linalg.norm(N, axis=1, keepdims=True) + 1e-9
    n = len(P)
    kl = np.zeros((n, 3))
    H = np.zeros(n)
    ruw = np.full(n, 0.75)
    # labelgewichten (zacht), apart per deel
    labs = list(STREEK) + list(VAST)
    W = np.zeros((n, len(labs)))
    for di, sdf in ((0, sdf_l), (1, sdf_p)):
        sel = deel == di
        D = sdf.labels(P[sel])
        dm = np.min(np.stack(list(D.values())), 0)
        for lab, d in D.items():
            W[sel, labs.index(lab)] = np.exp(-(d - dm) / 0.004)
    W /= W.sum(1, keepdims=True)
    lw = {lab: W[:, i] for i, lab in enumerate(labs)}
    # vleugel: achteraan de slagpennen (langer, donkerder)
    slag = lw["vleugel"] * gladstap(0.055, 0.115, P[:, 1])
    # stroomrichting en patroonwaarden per label, gemengd
    F = np.zeros((n, 3))
    for lab, (_, sp, A, f, _) in STREEK.items():
        F += lw[lab][:, None] * np.asarray(f, float) / np.linalg.norm(f)
    F -= np.einsum("ij,ij->i", F, N)[:, None] * N
    F /= np.linalg.norm(F, axis=1, keepdims=True) + 1e-9
    A = sum(lw[lab] * STREEK[lab][2] for lab in STREEK) + slag * 1.6
    tt, rand, dw, rnd = (np.zeros(n) for _ in range(4))
    gewveer = np.zeros(n)
    for sp in PASSEN:
        w = sum(lw[lab] for lab in STREEK if STREEK[lab][1] == sp)
        sel = w > 0.02
        if not sel.any():
            continue
        t_, r_, d_, x_ = veren(P[sel], F[sel], sp, A[sel])
        for arr, v in ((tt, t_), (rand, r_), (dw, d_), (rnd, x_)):
            arr[sel] += w[sel] * v
        gewveer[sel] += w[sel]
    g = np.maximum(gewveer, 1e-6)
    tt, rand, dw, rnd = tt / g, rand / g, dw / g, rnd / g
    tip = gladstap(-0.7, 0.9, tt)
    zoom = (1 - gladstap(0.0, 0.30, rand)) * gladstap(0.15, 0.6, tt)
    schacht = np.exp(-(dw / 0.07) ** 2) * gladstap(-0.4, 0.5, tt) * (1 - zoom)
    laag = ruis(P, 28.0, seed=3, octaven=2)
    for lab, (hexk, sp, _, _, zm) in STREEK.items():
        basis = srgb(hexk)
        c = basis[None] * (0.72 + 0.34 * tip)[:, None] * (1 + 0.07 * rnd + 0.08 * laag)[:, None]
        c = c * (1 - 0.55 * zoom[:, None]) + np.clip(basis * zm, 0, 1)[None] * 0.55 * zoom[:, None]
        c = c + 0.10 * schacht[:, None] * basis[None]
        kl += lw[lab][:, None] * c
    # staart: de dekveren onderaan in rugkleur, de pennen erboven bijna zwart
    dekv = lw["staart"] * gladstap(0.315, 0.285, P[:, 2]) * gladstap(0.215, 0.17, P[:, 1])
    kl = kl * (1 - dekv)[:, None] + dekv[:, None] * srgb(STREEK["rug"][0])[None] * (0.72 + 0.34 * tip)[:, None]
    # vleugelrand: donkere lijn waar de vleugel op het lijf ligt
    rand_v = np.clip(4 * lw["vleugel"] * (1 - lw["vleugel"]), 0, 1) * (P[:, 2] < 0.235)
    kl = kl * (1 - 0.45 * rand_v)[:, None]
    H -= 0.0006 * rand_v
    # slagpennen donker, staartdekveren met bruine rand
    kl = kl * (1 - 0.45 * slag)[:, None] + slag[:, None] * srgb("#4a1d0c")[None] * 0.45 * (0.85 + 0.3 * tip)[:, None]
    H += gewveer * (0.00075 * tip - 0.00035 * zoom) * (A / 1.2) ** 0.3
    ruw = ruw - 0.15 * lw["staart"]
    # kam en lellen: rood, licht glanzend, fijn bobbelig
    rood = lw["kam"] + lw["lel"]
    bob = ruis(P, 900.0, seed=5)
    kc = srgb(VAST["kam"])[None] * (0.88 + 0.12 * bob)[:, None]
    kc = kc * (1 - 0.25 * gladstap(0.375, 0.355, P[:, 2]) * lw["kam"])[:, None]   # voet van de kam donkerder
    kl += rood[:, None] * kc
    H += rood * 0.00025 * bob
    ruw = ruw * (1 - rood) + rood * 0.45
    # snavel: hoornkleur, donkere rug, bek-naad
    sn = lw["snavel"]
    sc_ = srgb(VAST["snavel"])[None] * (1 - 0.30 * gladstap(0.334, 0.343, P[:, 2]))[:, None]
    naad = np.exp(-((P[:, 2] - (0.3265 + 0.22 * (P[:, 1] + 0.150))) / 0.0010) ** 2) * gladstap(0.002, 0.005, np.abs(P[:, 0]))
    sc_ = sc_ * (1 - 0.75 * naad)[:, None]
    kl += sn[:, None] * sc_
    ruw = ruw * (1 - sn) + sn * 0.40
    # poten: geschubd geel, nagels hoornkleurig
    pt = lw["poot"] + lw["teen"]
    pc = np.zeros((n, 3))
    nagel = np.zeros(n)
    for sg in (1, -1):
        zk = np.sign(P[:, 0]) == sg
        hak, bal = V3(*R.jp("hak", sg)), V3(*R.jp("bal", sg))
        ax = (bal - hak) / np.linalg.norm(bal - hak)
        u = (P - hak) @ ax
        ring_ = np.abs(((u / 0.0042) % 1.0) - 0.5) * 2
        rb = np.linalg.norm(P[:, :2] - bal[:2], axis=1)
        ring_t = np.abs(((rb / 0.0036) % 1.0) - 0.5) * 2
        r = np.where(lw["teen"] > lw["poot"], ring_t, ring_)
        sch = gladstap(0.75, 1.0, r)
        _, tenen = poot_punten(sg)
        for eind, _, _ in tenen:
            L_ = np.linalg.norm(eind[:2] - bal[:2])
            dt = np.linalg.norm(P[:, :2] - eind[:2], axis=1)
            nagel = np.where(zk, np.maximum(nagel, gladstap(0.009, 0.005, dt) * (rb > 0.5 * L_)), nagel)
        pc = np.where(zk[:, None], srgb(VAST["poot"])[None] * (1 - 0.28 * sch)[:, None], pc)
        H += np.where(zk, pt * 0.00018 * (1 - sch), 0)
    pc = pc * (1 - nagel[:, None]) + srgb("#b9965f")[None] * nagel[:, None]
    kl += pt[:, None] * pc
    ruw = ruw * (1 - pt) + pt * (0.55 - 0.2 * nagel)
    # gezicht: kale rode huid rond het oog en op de wang, oorlel; dan het oog zelf
    kop = lw["kop"] + lw["hals"] * gladstap(0.30, 0.32, P[:, 2])
    for sg, oc in ogen:
        zk = np.sign(P[:, 0]) == sg
        rel = (P - (oc + np.array([sg * -0.002, -0.004, -0.008]))) / np.array([0.024, 0.021, 0.019])
        gez = gladstap(1.0, 0.55, np.linalg.norm(rel, axis=1)) * zk * kop
        lob = gladstap(0.0095, 0.006, np.linalg.norm(P - (oc + np.array([0.0, 0.013, -0.015])), axis=1)) * zk
        huid = np.clip(gez + lob, 0, 1)
        kl = kl * (1 - huid[:, None]) + huid[:, None] * srgb("#c43a2a")[None] * (0.9 + 0.1 * bob)[:, None]
        H = H * (1 - huid)
        ruw = ruw * (1 - huid) + huid * 0.5
        r = np.linalg.norm(P - oc, axis=1)
        pupil = gladstap(0.0034, 0.0028, r) * zk
        iris = gladstap(0.0062, 0.0056, r) * zk
        lid = gladstap(0.0074, 0.0066, r) * zk
        kl = kl * (1 - lid[:, None]) + lid[:, None] * srgb("#3a120c")[None]
        kl = kl * (1 - iris[:, None]) + iris[:, None] * srgb("#c87a1c")[None] * (0.8 + 0.4 * gladstap(0.006, 0.002, r))[:, None]
        kl = kl * (1 - pupil[:, None]) + pupil[:, None] * srgb("#050302")[None]
        glim = gladstap(0.0013, 0.0007, np.linalg.norm(P - (oc + np.array([sg * 0.0006, -0.0012, 0.0016])), axis=1)) * zk
        kl = kl * (1 - glim[:, None]) + glim[:, None] * 0.85
        ruw = ruw * (1 - iris) + iris * 0.12
        H = H * (1 - lid)
    return ys, xs, np.clip(kl, 0, 1), H, np.clip(ruw, 0.05, 1), deel


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


def texturen(B, mpp, sdf_l, sdf_p, ogen):
    t1 = time.time()
    ys, xs, kl, H, ruw, deel = componeer(B, sdf_l, sdf_p, ogen)
    h, w = B["pos"].shape[:2]
    mask = np.zeros((h, w), bool)
    mask[ys, xs] = True
    ao = B["ao"][..., 0]
    kl = kl * (0.60 + 0.40 * ao[ys, xs])[:, None]
    K = np.zeros((h, w, 3), np.float32)
    K[ys, xs] = naar_srgb(kl)
    Hm = np.zeros((h, w), np.float32)
    Hm[ys, xs] = H
    mp = np.full((h, w), mpp["lijf"], np.float32)
    mp[ys[deel == 1], xs[deel == 1]] = mpp["poten"]
    Hd = BM.dilateer(Hm[..., None].repeat(3, -1), mask, 3)[..., 0]
    nd = BM.reliëf_normaal(Hd, mp)
    nb = B["normaal"][..., :3] * 2 - 1
    nn_ = np.stack([nb[..., 0] + nd[..., 0], nb[..., 1] + nd[..., 1], nb[..., 2] * nd[..., 2]], -1)
    nn_ /= np.linalg.norm(nn_, axis=-1, keepdims=True) + 1e-9
    Nimg = nn_ * 0.5 + 0.5
    Nimg[~mask] = (0.5, 0.5, 1.0)
    ORM = np.zeros((h, w, 3), np.float32)
    ORM[..., 0] = np.clip(ao * 0.85 + 0.15, 0, 1)
    ORM[ys, xs, 1] = ruw
    K = BM.dilateer(K, mask, 10)
    Nimg = BM.dilateer(Nimg.astype(np.float32), mask, 10)
    ORM = BM.dilateer(ORM, mask, 10)
    kleur = bewaar(K, "kip_kleur", False, jpg=True)
    normaal = bewaar(Nimg, "kip_normaal", True)
    orm = bewaar(ORM, "kip_orm", True)
    log("texturen", f"{time.time() - t1:.1f}s")
    return kleur, normaal, orm


# --- Gewichten ------------------------------------------------------------------------------------
def seg_afst(P, a, b):
    ab = b - a
    t = np.clip((P - a) @ ab / (ab @ ab), 0, 1)
    return np.linalg.norm(P - (a + t[:, None] * ab), axis=1)


BOTSET = {"romp": ["Hips", "Spine"], "rug": ["Hips"], "borst": ["Spine", "Hips"], "buik": ["Hips"],
          "hals": ["Spine", "Neck", "Neck1", "Head"], "kop": ["Head"], "snavel": ["Head"], "kam": ["Head"],
          "lel": ["Head"], "staart": ["Tail"], "vleugel": ["*Wing", "Spine"], "dij": ["*Shin", "*Thigh", "Hips"]}


def zet_gewichten(o, rig, Wb):
    """Wb {bot: gewichten per vertex} -> vertexgroepen (max 4, genormaliseerd) + armatuur-modifier."""
    namen = list(Wb)
    W = np.stack([Wb[b] for b in namen], 1)
    orde = np.argsort(-W, 1)
    W[np.arange(len(W))[:, None], orde[:, 4:]] = 0
    W[W < 0.01] = 0
    W /= np.maximum(W.sum(1, keepdims=True), 1e-9)
    for i, b in enumerate(namen):
        nz = np.nonzero(W[:, i])[0]
        if not len(nz):
            continue
        g = o.vertex_groups.new(name=b)
        for vi in nz:
            g.add([int(vi)], float(W[vi, i]), "REPLACE")
    o.parent = rig
    m = o.modifiers.new("Armature", "ARMATURE")
    m.object = rig


def glad_W(o, Wb, a=0.5, n=3):
    me = o.data
    E = np.zeros(len(me.edges) * 2, np.int64)
    me.edges.foreach_get("vertices", E)
    E = E.reshape(-1, 2)
    nv = len(me.vertices)
    deg = np.bincount(E.ravel(), minlength=nv).astype(float)
    for b in Wb:
        w = Wb[b]
        for _ in range(n):
            S = np.zeros(nv)
            np.add.at(S, E[:, 0], w[E[:, 1]])
            np.add.at(S, E[:, 1], w[E[:, 0]])
            w = (1 - a) * w + a * S / np.maximum(deg, 1)
        Wb[b] = w


def skin_lijf(o, rig, sdf):
    M = R.Maten(rig)
    P = np.array([v.co for v in o.data.vertices])
    D = sdf.labels(P)
    dm = np.min(np.stack(list(D.values())), 0)
    Wb = {b.name: np.zeros(len(P)) for b in rig.data.bones}
    links = P[:, 0] >= 0
    for lab, d in D.items():
        wl = np.exp(-(d - dm) / 0.006)
        bots = []
        for b in BOTSET[lab]:
            if b.startswith("*"):
                bots += [("Left" + b[1:], links), ("Right" + b[1:], ~links)]
            else:
                bots.append((b, np.ones(len(P), bool)))
        G = np.stack([np.where(m, 1.0 / (seg_afst(P, np.array(M.kop[b]), np.array(M.staart[b])) + 0.008) ** 4, 0)
                      for b, m in bots], 1)
        G /= G.sum(1, keepdims=True) + 1e-12
        for i, (b, _) in enumerate(bots):
            Wb[b] += wl * G[:, i]
    glad_W(o, Wb, 0.5, 3)
    zet_gewichten(o, rig, Wb)


def skin_poten(o, rig):
    P = np.array([v.co for v in o.data.vertices])
    Wb = {}
    for z, sg in R.ZIJDEN:
        zk = (np.sign(P[:, 0]) == sg).astype(float)
        hak = R.jp("hak", sg)
        shin = gladstap(hak.z - 0.004, hak.z + 0.010, P[:, 2])
        voet = gladstap(0.016, 0.008, P[:, 2])
        Wb[z + "Shin"] = zk * shin
        Wb[z + "Foot"] = zk * voet * (1 - shin)
        Wb[z + "Tarsus"] = zk * np.clip(1 - shin - voet, 0, 1)
    zet_gewichten(o, rig, Wb)


# --- Previews -------------------------------------------------------------------------------------------
def rust(rig):
    if rig.animation_data:
        rig.animation_data.action = None
    for b in rig.pose.bones:
        b.rotation_quaternion = (1, 0, 0, 0)
        b.location = (0, 0, 0)
    bpy.context.view_layer.update()


def vloer(sc):
    bpy.ops.mesh.primitive_plane_add(size=3, location=(0, 0, -0.0005))
    v = bpy.context.object
    v.name = "vloer"
    v.data.materials.append(BM.vlak_mat("vloer", srgb("#8f9f7f"), 0.9))
    v.is_shadow_catcher = True
    return v


def poses(sc, rig, tag=""):
    keuzes = [("idle", 0), ("idle", 50), ("lopen", 0), ("lopen", 3), ("lopen", 7), ("lopen", 10),
              ("pikken", 15), ("pikken", 19), ("zitten", 24)]
    tmp = bpy.app.tempdir
    rijen = []
    for yaw, pitch in ((225, 30), (180, 4)):
        pan = []
        for act, f in keuzes:
            R.zet_actie(rig, act)
            sc.frame_set(f)
            BM.studio(sc, 520, 0.62, 0.48, doel=(0, 0.0, 0.19), yaw=yaw, pitch=pitch)
            pan.append(BM.bijsnijden(BM.render_np(sc, os.path.join(tmp, f"p_{act}_{f}.png"))))
        rijen.append(BM.plak(pan))
    BM.schrijf(BM.onder(*rijen), os.path.join(PREV, f"kip_poses{tag}.png"))
    rust(rig)


def vergelijk(sc, rig, tag=""):
    rust(rig)
    tmp = bpy.app.tempdir
    concept = BM.laad_np(CONCEPT)
    c = concept[: concept.shape[0], : concept.shape[1] // 2 - 120, :3]       # alleen de hennen (links)
    c = np.concatenate([c, np.ones((*c.shape[:2], 1), np.float32)], 2)
    pan = []
    for yw, pt in ((180, 3), (200, 8), (225, 30), (270, 6)):
        BM.studio(sc, 1000, 0.62, 0.48, doel=(0, 0.0, 0.2), yaw=yw, pitch=pt)
        pan.append(BM.bijsnijden(BM.render_np(sc, os.path.join(tmp, f"c_{yw}.png"))))
    kop = []
    for yw, pt in ((180, 3), (215, 15)):
        BM.studio(sc, 3600, 0.15, 0.13, doel=(0, -0.135, 0.345), yaw=yw, pitch=pt)
        kop.append(BM.render_np(sc, os.path.join(tmp, f"k_{yw}.png")))
    out = BM.onder(BM.plak([c] + pan[:2]), BM.plak(pan[2:] + kop))
    BM.schrijf(out, os.path.join(PREV, f"kip_vergelijk{tag}.png"))


# --- Ei ----------------------------------------------------------------------------------------------
def maak_ei():
    """Bruin ei, ~6 cm hoog (staand, stompe kant onder), oorsprong onderaan op de grond."""
    bpy.ops.wm.read_factory_settings(use_empty=True)
    L, Rm = 0.060, 0.0225
    nr, ns = 14, 20
    V, F = [(0, 0, 0)], []
    for i in range(1, nr):
        t = i / nr
        th = math.pi * t
        z = L * (1 - math.cos(th)) / 2
        r = Rm * math.sin(th) * (1 + 0.11 * math.cos(th))        # breder onderaan (stompe kant)
        for j in range(ns):
            a = 2 * math.pi * j / ns
            V.append((r * math.cos(a), r * math.sin(a), z))
    V.append((0, 0, L))
    top = len(V) - 1
    for j in range(ns):
        F.append((0, 1 + (j + 1) % ns, 1 + j))
    for i in range(nr - 2):
        b0, b1 = 1 + i * ns, 1 + (i + 1) * ns
        for j in range(ns):
            j1 = (j + 1) % ns
            F.append((b0 + j, b0 + j1, b1 + j1, b1 + j))
    b0 = 1 + (nr - 2) * ns
    for j in range(ns):
        F.append((b0 + j, b0 + (j + 1) % ns, top))
    me = bpy.data.meshes.new("ei")
    me.from_pydata(V, [], F)
    me.update()
    bm = bmesh.new()
    bm.from_mesh(me)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bmesh.ops.triangulate(bm, faces=bm.faces)
    bm.to_mesh(me)
    bm.free()
    me.shade_smooth()
    o = bpy.data.objects.new("ei", me)
    bpy.context.scene.collection.objects.link(o)
    m = BM.vlak_mat("mat_ei", srgb("#b8693f"), 0.55)
    me.materials.append(m)
    me.calc_loop_triangles()
    pad = os.path.join(HERE, "ei.glb")
    bpy.ops.export_scene.gltf(filepath=pad, export_format="GLB", export_yup=True, use_selection=False,
                              export_cameras=False, export_lights=False, export_animations=False)
    log("ei", len(me.loop_triangles), "driehoeken ->", pad)
    if "poses" in OPTS or "vergelijk" in OPTS:
        sc = bpy.context.scene
        BM.studio(sc, 3000, 0.1, 0.08, doel=(0, 0, 0.03), yaw=225, pitch=15)
        BM.schrijf(BM.plak([BM.bijsnijden(BM.render_np(sc, os.path.join(bpy.app.tempdir, "ei.png")))]),
                   os.path.join(PREV, "ei.png"))


# --- Hoofdprogramma ---------------------------------------------------------------------------------
def main():
    if "ei" in OPTS:
        maak_ei()
        return
    bpy.ops.wm.read_factory_settings(use_empty=True)
    sc = bpy.context.scene
    sc.render.fps = R.FPS
    sc.frame_start = 0
    coll = sc.collection
    rig = R.bouw_rig()
    sdf_l, sdf_p = vorm_lijf(), vorm_poten()
    ogen = [(sg, oog_c(sdf_l, sg)) for sg in (1, -1)]
    log("oog", ogen[0][1].round(4))
    hoog_l = oppervlak(sdf_l, H_LIJF, "lijf_hoog", coll)
    hoog_p = oppervlak(sdf_p, H_POOT, "poten_hoog", coll)
    delen = {"lijf": decimeer(hoog_l, "lijf", DOEL["lijf"], coll),
             "poten": decimeer(hoog_p, "poten", DOEL["poten"], coll)}
    log("driehoeken", {k: driehoeken([o]) for k, o in delen.items()})
    mpp = uv_atlas(delen)
    log("mm/texel", {k: round(v * 1000, 2) for k, v in mpp.items()})
    B = bak_alles(delen, {"lijf": [hoog_l], "poten": [hoog_p]})
    for h in (hoog_l, hoog_p):
        bpy.data.objects.remove(h)
    kleur, normaal, orm = texturen(B, mpp, sdf_l, sdf_p, ogen)
    mat = BM.pbr("mat_kip", kleur, normaal, orm)
    for o in delen.values():
        o.data.materials.clear()
        o.data.materials.append(mat)
    skin_lijf(delen["lijf"], rig, sdf_l)
    skin_poten(delen["poten"], rig)
    info = R.bouw_animaties(rig)
    json.dump(info, open(os.path.join(HERE, "kip_anim.json"), "w"), indent=2)
    log("animaties", json.dumps(info))
    log("LOD0 driehoeken", driehoeken(delen.values()), {k: driehoeken([o]) for k, o in delen.items()})
    if "geen_export" not in OPTS:
        BM.ontkies()
        bpy.ops.export_scene.gltf(filepath=GLB, export_format="GLB", export_animations=True,
                                  export_animation_mode="ACTIONS", export_force_sampling=True, export_yup=True,
                                  export_skins=True, export_def_bones=False, export_extras=True, use_selection=False,
                                  export_tangents=True, export_image_format="AUTO", export_cameras=False,
                                  export_lights=False)
        log("export", GLB, f"{os.path.getsize(GLB) / 1e6:.2f} MB")
    os.makedirs(PREV, exist_ok=True)
    tag = OPTS.get("tag", "")
    if "poses" in OPTS or "vergelijk" in OPTS:
        v = vloer(sc)
        if "vergelijk" in OPTS:
            vergelijk(sc, rig, tag)
        if "poses" in OPTS:
            poses(sc, rig, tag)
        bpy.data.objects.remove(v)
    bpy.ops.wm.save_as_mainfile(filepath=os.path.join(PREV, "kip.blend"))
    log("KLAAR")


if __name__ == "__main__":
    main()
