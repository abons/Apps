"""Real-time peasant hut voor Godot 4 (pc eerst; Android later via LOD1).

Bouwt op peasant_hut.blend (eerst `blender -b -P peasant_hut.py -- 4`). De procedurele Cycles-
materialen gaan niet mee naar glTF en de ~43k halmen (hair curves) ook niet, dus:
- elke materiaalgroep krijgt een eigen UV-atlas, in Cycles gebakken van de echte objecten
  (selected-to-active): kleur, ORM (R = AO, G = ruwheid, B = metaal 0) en een tangent-normal map;
- de muurstenen blijven echte stenen, gedecimeerd, met de verborgen kanten weggesneden;
- het riet: de koepel en het aanbouwdak dragen de gebakken halmen, daarop kaarten met alfa (MASK)
  in de lagen van de halmen (zelfde rnd-volgorde als peasant_hut.py), rafelige zoom, kuifschoven;
- LOD1 is een losse glb: wand als cilinder, koepel als schil, alles op een eigen 1k-atlas.

Draaien (headless):
  blender -b -P peasant_hut_realtime.py -- [res=2048] [snel] [vergelijk] [alleen_vergelijk]
Schrijft peasant_hut_rt.glb, peasant_hut_rt_lod1.glb en rt_textures/ naast dit script;
`vergelijk` rendert daarna de glb in EEVEE met de camera van de beauty: peasant_hut_rt_vergelijk.png.
"""
import ast
import math
import os
import random
import sys
import time
from collections import defaultdict

import bmesh
import bpy
import numpy as np
from mathutils import Matrix, Vector
from mathutils.bvhtree import BVHTree

HERE = os.path.dirname(os.path.abspath(__file__))
BLEND = os.path.join(HERE, "peasant_hut.blend")
TEXDIR = os.path.join(HERE, "rt_textures")
GLB0 = os.path.join(HERE, "peasant_hut_rt.glb")
GLB1 = os.path.join(HERE, "peasant_hut_rt_lod1.glb")
argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
OPTS = {a.split("=")[0]: (a.split("=", 1)[1] if "=" in a else "1") for a in argv}
SNEL = "snel" in OPTS
RES = int(OPTS.get("res", 512 if SNEL else 2048))       # kleur en normaal per atlas
ORM_RES = RES // 2                                       # AO en ruwheid zijn laagfrequent
LOD1_RES = RES // 2
KAART_RES = RES                                          # kaartatlas: 2 x 2 m, ~1 mm per pixel
SPP = 0.25 if SNEL else 1.0                              # schaal op de bake-samples
T0 = time.time()


def log(*a):
    print(f"[rt {time.time() - T0:6.1f}s]", *a, flush=True)


# --- Maten en halmlagen uit peasant_hut.py (via ast, zonder het te draaien) ---------
class LogRandom(random.Random):
    """Zelfde reeks als random.Random; onthoudt elke uniform(a, b) voor de lagen van de halmen."""
    LOG = []

    def uniform(self, a, b):
        v = super().uniform(a, b)
        LogRandom.LOG.append((a, b, v))
        return v


def lees_bron():
    tree = ast.parse(open(os.path.join(HERE, "peasant_hut.py"), encoding="utf-8").read())
    fun = {"dome_profile", "brow", "resample", "at", "lid_z", "lid_top", "ch_r", "on_wall"}
    var = {"HX", "HY", "HUT_R", "WALL_H", "DOME_R", "DOME_Z0", "DOME_TOP", "DOME_P", "DOOR_DEG", "BROW_W",
           "BROW_UP", "BROW_IN", "CH", "CH_PROF", "AX0", "AX1", "AY0", "AY1", "LX0", "LX1", "LY0", "LY1"}
    ns = {"math": math, "Vector": Vector, "random": random}
    run = lambda nodes, g: exec(compile(ast.Module(body=nodes, type_ignores=[]), "peasant_hut.py", "exec"), g)
    namen = lambda n: {x.id for t in n.targets for x in ast.walk(t) if isinstance(x, ast.Name)}
    start = end = None
    for i, n in enumerate(tree.body):
        if isinstance(n, ast.FunctionDef) and n.name in fun:
            run([n], ns)
        elif isinstance(n, ast.Assign) and namen(n) <= var:
            run([n], ns)
        if isinstance(n, ast.Assign) and "rnd" in namen(n):
            start = i
        if start is not None and end is None and isinstance(n, ast.AugAssign) and getattr(n.target, "id", "") == "nok":
            end = i
    # het halmblok opnieuw, met een loggende rnd: zo liggen de kaarten op de lagen van de halmen
    g = dict(ns, random=type("R", (), {"Random": LogRandom}), strands=lambda *a, **k: None, M_HALM=None,
             M_KUIF=None)
    run(tree.body[start:end], g)
    dak, lid = [], []
    s0, y0, fase = 0.0, g["LY0"], "dak"
    for a, b, v in LogRandom.LOG:
        if (a, b) == (0.75, 0.95):
            dak.append((s0, v))
        elif (a, b) == (0.7, 0.9):
            fase = "lid"
            lid.append((y0, v))
        elif (a, b) == (0.26, 0.34):
            if fase == "dak":
                s0 += v
            else:
                y0 += v
    ns.update(PROF=g["PROF"], S_END=g["S_END"], KUIF_C=g["kuif_c"], KUIF_B=g["kuif_b"], KOERS_DAK=dak, KOERS_LID=lid)
    return ns


B = lees_bron()
HX, HY, HUT_R, WALL_H = B["HX"], B["HY"], B["HUT_R"], B["WALL_H"]
AX0, AX1, AY0, AY1 = B["AX0"], B["AX1"], B["AY0"], B["AY1"]
LX0, LX1, LY0, LY1 = B["LX0"], B["LX1"], B["LY0"], B["LY1"]
CH, PROF, S_END = B["CH"], B["PROF"], B["S_END"]
at, brow, lid_top, ch_r, dome_profile = B["at"], B["brow"], B["lid_top"], B["ch_r"], B["dome_profile"]
log("lagen dak", len(B["KOERS_DAK"]), "aanbouw", len(B["KOERS_LID"]), "S_END", round(S_END, 3))


# --- Scene, GPU ------------------------------------------------------------------------
def gpu(scene):
    p = bpy.context.preferences.addons["cycles"].preferences
    for t in ("CUDA", "OPTIX"):              # OptiX-kernel faalt op deze driver (2026-10-29)
        try:
            p.compute_device_type = t
        except TypeError:
            continue
        p.get_devices()
        if any(d.type == t for d in p.devices):
            for d in p.devices:
                d.use = d.type == t
            scene.cycles.device = "GPU"
            return t
    return "CPU"


def mat0(o):
    return o.material_slots[0].material.name if o.material_slots and o.material_slots[0].material else ""


def ontkies():
    bpy.context.view_layer.update()                   # na objects.remove staat er anders None in
    for o in bpy.context.view_layer.objects:
        if o is not None:
            o.select_set(False)


# --- Mesh-hulpjes ----------------------------------------------------------------------
def mesh_np(name, V, F, smooth=True):
    """Mesh uit numpy: V (n, 3), F (m, 4) quads of (m, 3) driehoeken."""
    V = np.asarray(V, np.float32).reshape(-1, 3)
    F = np.asarray(F, np.int32)
    k = F.shape[1]
    me = bpy.data.meshes.new(name)
    me.vertices.add(len(V))
    me.vertices.foreach_set("co", V.ravel())
    me.loops.add(F.size)
    me.loops.foreach_set("vertex_index", F.ravel())
    me.polygons.add(len(F))
    me.polygons.foreach_set("loop_start", np.arange(len(F), dtype=np.int32) * k)
    me.update(calc_edges=True)
    if smooth:
        me.shade_smooth()
    return me


def mesh_py(name, verts, faces, smooth=True):
    me = bpy.data.meshes.new(name)
    me.from_pydata([tuple(v) for v in verts], [], faces)
    me.update()
    if smooth:
        me.shade_smooth()
    return me


def eval_mesh(ob, name=None):
    """Mesh met modifiers, in wereldcoordinaten."""
    dg = bpy.context.evaluated_depsgraph_get()
    me = bpy.data.meshes.new_from_object(ob.evaluated_get(dg), preserve_all_data_layers=False, depsgraph=dg)
    me.transform(ob.matrix_world)
    me.name = name or ob.name + "_rt"
    return me


def obj(name, me, coll):
    o = bpy.data.objects.new(name, me)
    coll.objects.link(o)
    return o


_DEC = {}


def decimeer(me, ratio, coll, sharp=None):
    """Collapse-decimatie via een tijdelijk object; sharp = hoek (graden) voor scherpe randen."""
    key = (me.name, ratio)
    if key in _DEC:
        return _DEC[key]
    o = obj("_dec", me, coll)
    m = o.modifiers.new("d", "DECIMATE")
    m.ratio = ratio
    m.use_collapse_triangulate = True
    dg = bpy.context.evaluated_depsgraph_get()
    out = bpy.data.meshes.new_from_object(o.evaluated_get(dg), depsgraph=dg)
    bpy.data.objects.remove(o)
    out.shade_smooth()
    if sharp:
        out.set_sharp_from_angle(angle=math.radians(sharp))
    _DEC[key] = out
    return out


def samen_bm(name, meshes, mats=()):
    """Meshes samenvoegen (bmesh voegt toe). mats: slots van het resultaat; zonder slots klemt
    to_mesh elke materiaalindex naar 0."""
    bm = bmesh.new()
    for me in meshes:
        bm.from_mesh(me)
    out = bpy.data.meshes.new(name)
    for m in mats:
        out.materials.append(m)
    bm.to_mesh(out)
    bm.free()
    return out


def join(name, objs, coll):
    """Objecten samenvoegen tot een (materiaalslots blijven)."""
    ontkies()
    for o in objs:
        o.select_set(True)
    bpy.context.view_layer.objects.active = objs[0]
    bpy.ops.object.join()
    o = bpy.context.view_layer.objects.active
    o.name = name
    o.data.name = name
    return o


def lathe_np(name, prof, seg, cap_top=False, punt=None):
    """Omwentelingsmesh rond de z-as uit (r, z); punt(a, r, z) -> (x, y, z) mag vervormen."""
    vs, fs = [], []
    for j, (r, z) in enumerate(prof):
        for i in range(seg):
            a = 2 * math.pi * i / seg
            vs.append(punt(a, r, z) if punt else (r * math.cos(a), r * math.sin(a), z))
    for j in range(len(prof) - 1):
        for i in range(seg):
            a, b = j * seg + i, j * seg + (i + 1) % seg
            fs.append([a, b, b + seg, a + seg])          # buitenkant naar buiten bij stijgende z
    if cap_top:
        c = len(vs)
        r, z = prof[-1]
        vs.append(punt(0, 0, z) if punt else (0, 0, z))
        last = (len(prof) - 1) * seg
        fs += [[last + i, last + (i + 1) % seg, c] for i in range(seg)]
    return mesh_py(name, vs, fs)


def torus_mesh(name, R, r, nu=32, nv=6):
    vs, fs = [], []
    for i in range(nu):
        a = 2 * math.pi * i / nu
        for j in range(nv):
            b = 2 * math.pi * j / nv
            rr = R + r * math.cos(b)
            vs.append((rr * math.cos(a), rr * math.sin(a), r * math.sin(b)))
    for i in range(nu):
        for j in range(nv):
            a, b = i * nv + j, i * nv + (j + 1) % nv
            c, d = ((i + 1) % nu) * nv + (j + 1) % nv, ((i + 1) % nu) * nv + j
            fs.append([a, d, c, b])
    return mesh_py(name, vs, fs)


def box_mesh(name, lo, hi):
    (x0, y0, z0), (x1, y1, z1) = lo, hi
    vs = [(x, y, z) for z in (z0, z1) for y in (y0, y1) for x in (x0, x1)]
    fs = [[0, 2, 3, 1], [4, 5, 7, 6], [0, 1, 5, 4], [2, 6, 7, 3], [0, 4, 6, 2], [1, 3, 7, 5]]
    return mesh_py(name, vs, fs, smooth=False)


# --- Halmen (hair curves) als buizen: bron voor het bakken -----------------------------
def buizen(name, krommen, stralen, per_kromme, sides=4):
    """krommen: lijst (n, 3); stralen: lijst (n,); per_kromme: {attr: waarde per kromme}.
    Mesh met 'hint' (POINT, 0..1 langs de halm) en per-kromme attributen op FACE."""
    groep = defaultdict(list)
    for i, c in enumerate(krommen):
        groep[len(c)].append(i)
    th = np.linspace(0, 2 * np.pi, sides, endpoint=False)
    cs, sn = np.cos(th), np.sin(th)
    V, F, HI = [], [], []
    PF = {k: [] for k in per_kromme}
    off = 0
    for n, idx in groep.items():
        P = np.array([krommen[i] for i in idx], np.float64)            # (m, n, 3)
        R = np.array([stralen[i] for i in idx], np.float64)            # (m, n)
        T = np.gradient(P, axis=1)
        T /= np.linalg.norm(T, axis=2, keepdims=True) + 1e-12
        ref = np.where(np.abs(T[..., 2:3]) > 0.9, np.array([1.0, 0, 0]), np.array([0, 0, 1.0]))
        U = np.cross(T, ref)
        U /= np.linalg.norm(U, axis=2, keepdims=True) + 1e-12
        W = np.cross(T, U)
        ring = P[:, :, None, :] + R[:, :, None, None] * (U[:, :, None, :] * cs[None, None, :, None]
                                                          + W[:, :, None, :] * sn[None, None, :, None])
        m = len(idx)
        base = off + (np.arange(m)[:, None, None] * n * sides + np.arange(n - 1)[None, :, None] * sides)
        k = np.arange(sides)
        k2 = (k + 1) % sides
        q = np.stack([base + k, base + k2, base + sides + k2, base + sides + k], axis=-1)
        V.append(ring.reshape(-1, 3))
        F.append(q.reshape(-1, 4))
        HI.append(np.repeat(np.tile(np.linspace(0, 1, n), m), sides))
        for key, vals in per_kromme.items():
            PF[key].append(np.repeat(np.asarray(vals, np.float32)[idx], (n - 1) * sides))
        off += m * n * sides
    me = mesh_np(name, np.concatenate(V), np.concatenate(F))
    a = me.attributes.new("hint", "FLOAT", "POINT")
    a.data.foreach_set("value", np.concatenate(HI).astype(np.float32))
    for key, arr in PF.items():
        a = me.attributes.new(key, "FLOAT", "FACE")
        a.data.foreach_set("value", np.concatenate(arr))
    return me


def halmen_van(ob):
    """Hair curves -> (krommen, stralen, bos) in wereldcoordinaten."""
    cv = ob.data
    n, nc = len(cv.points), len(cv.curves)
    pos = np.zeros(n * 3, np.float32)
    cv.attributes["position"].data.foreach_get("vector", pos)
    pos = pos.reshape(-1, 3) @ np.array(ob.matrix_world.to_3x3()).T + np.array(ob.matrix_world.translation)
    offs = np.zeros(nc + 1, np.int32)
    cv.curve_offset_data.foreach_get("value", offs)
    rad = np.zeros(n, np.float32)
    cv.attributes["radius"].data.foreach_get("value", rad)
    bos = np.zeros(nc, np.float32)
    cv.attributes["bos"].data.foreach_get("value", bos)
    kr = [pos[offs[i]:offs[i + 1]] for i in range(nc)]
    st = [rad[offs[i]:offs[i + 1]] for i in range(nc)]
    return kr, st, bos


def mat_attr(src):
    """Halmmateriaal voor een mesh: Hair Info (Random, Intercept) -> attributen hrand, hint."""
    m = src.copy()
    m.name = src.name + "_buis"
    nt = m.node_tree
    for hi in [n for n in nt.nodes if n.type == "HAIR_INFO"]:
        for out, naam in (("Random", "hrand"), ("Intercept", "hint")):
            a = nt.nodes.new("ShaderNodeAttribute")
            a.attribute_name = naam
            for l in list(hi.outputs[out].links):
                nt.links.new(a.outputs["Fac"], l.to_socket)
        nt.nodes.remove(hi)
    return m


def mat_zelf(src, cache):
    """Kopie die niet meer van het object afhangt: Object- en Generated-coordinaten en Object Info >
    Random komen uit attributen (o_obj, o_gen, o_rand) van de samengevoegde bron."""
    if src.name in cache:
        return cache[src.name]
    m = src.copy()
    m.name = src.name + "_z"
    nt = m.node_tree
    attr = {}

    def a(naam):
        if naam not in attr:
            attr[naam] = nt.nodes.new("ShaderNodeAttribute")
            attr[naam].attribute_name = naam
        return attr[naam]
    for n in list(nt.nodes):
        if n.type == "TEX_COORD":
            for out, naam in (("Object", "o_obj"), ("Generated", "o_gen")):
                for l in list(n.outputs[out].links):
                    nt.links.new(a(naam).outputs["Vector"], l.to_socket)
        elif n.type == "OBJECT_INFO":
            for l in list(n.outputs["Random"].links):
                nt.links.new(a("o_rand").outputs["Fac"], l.to_socket)
    for n in list(nt.nodes):                           # procedurele textuur zonder vector: Generated
        if n.type.startswith("TEX_") and n.type not in ("TEX_COORD", "TEX_IMAGE", "TEX_ENVIRONMENT"):
            v = n.inputs.get("Vector")
            if v is not None and not v.is_linked:
                nt.links.new(a("o_gen").outputs["Vector"], v)
    cache[src.name] = m
    return m


_ZCACHE = {}


def zelfstandig(naam, objs, coll):
    """Bronobjecten samengevoegd tot een mesh (selected-to-active cast per pixel naar elk bronobject
    apart: 460 stenen = 13 min per 512-bake, een mesh = seconden). Per-object invoer als attributen."""
    rng = random.Random(len(objs))
    mats, delen = [], []
    for o in objs:
        me = eval_mesh(o, "_z")
        n = len(me.vertices)
        co = np.zeros(n * 3, np.float32)
        me.vertices.foreach_get("co", co)
        Mi = np.array(o.matrix_world.inverted())
        loc = co.reshape(-1, 3) @ Mi[:3, :3].T + Mi[:3, 3]
        lo, hi = loc.min(0), loc.max(0)
        gen = (loc - lo) / np.maximum(hi - lo, 1e-6)
        for key, arr in (("o_obj", loc), ("o_gen", gen)):
            at_ = me.attributes.new(key, "FLOAT_VECTOR", "POINT")
            at_.data.foreach_set("vector", arr.astype(np.float32).ravel())
        at_ = me.attributes.new("o_rand", "FLOAT", "FACE")
        at_.data.foreach_set("value", np.full(len(me.polygons), rng.random(), np.float32))
        idx = np.zeros(len(me.polygons), np.int32)
        me.polygons.foreach_get("material_index", idx)
        slots = [s.material for s in o.material_slots] or [None]
        remap = []
        for s in slots:
            mz = mat_zelf(s, _ZCACHE) if s else None
            if mz not in mats:
                mats.append(mz)
            remap.append(mats.index(mz))
        delen.append((me, np.array(remap, np.int32)[np.minimum(idx, len(remap) - 1)]))
    for me, idx in delen:                              # alle slots per deel, anders klemt bmesh de index
        me.materials.clear()
        for m in mats:
            me.materials.append(m)
        me.polygons.foreach_set("material_index", idx)
    delen = [d for d, _ in delen]
    me = samen_bm(naam, delen, mats)
    for d in delen:
        bpy.data.meshes.remove(d)
    log("  bron", naam, len(objs), "objecten", len(me.polygons), "vlakken", sorted(me.attributes.keys())[:8])
    return obj(naam, me, bpy.context.scene.collection)


def uv_eenheid(me, coll, hoek=66):
    """Eigen UV van een losse mesh in [0, 1]^2 (smart project + pakken)."""
    while me.uv_layers:
        me.uv_layers.remove(me.uv_layers[0])
    me.uv_layers.new(name="UVMap")
    o = obj("_uv", me, coll)
    ontkies()
    o.select_set(True)
    bpy.context.view_layer.objects.active = o
    bpy.context.scene.tool_settings.use_uv_select_sync = True
    bpy.ops.object.mode_set(mode="EDIT")
    bpy.ops.mesh.select_all(action="SELECT")
    bpy.ops.uv.smart_project(angle_limit=math.radians(hoek), island_margin=0.02, area_weight=0.0,
                             correct_aspect=True, scale_to_bounds=False)
    bpy.ops.uv.pack_islands(rotate=True, margin=0.015, shape_method="CONCAVE")
    bpy.ops.object.mode_set(mode="OBJECT")
    bpy.data.objects.remove(o)


def schap(maten, marge):
    """Vierkante cellen met relatieve zijde `maten` op planken in [0, 1]^2, zo groot mogelijk.
    -> lijst (x, y, zijde). Smart project over 455 gefacetteerde stenen gaf duizenden eilandjes
    en 2 % dekking; een cel per steen haalt ~60 %."""
    volg = sorted(range(len(maten)), key=lambda i: -maten[i])

    def probeer(k):
        x = y = rij = 0.0
        pos = [None] * len(maten)
        for i in volg:
            z = maten[i] * k
            if x + z + marge > 1.0:
                x, y, rij = 0.0, y + rij + marge, 0.0
            if y + z + marge > 1.0:
                return None
            pos[i] = (x + marge, y + marge, z)
            x += z + marge
            rij = max(rij, z)
        return pos
    lo, hi, best = 0.0, 1.0 / max(maten), None
    for _ in range(40):
        k = (lo + hi) / 2
        p = probeer(k)
        if p:
            lo, best = k, p
        else:
            hi = k
    return best


def uv_plaats(me, cel):
    x, y, z = cel
    uv = np.zeros(len(me.loops) * 2, np.float32)
    me.uv_layers[0].data.foreach_get("uv", uv)
    uv = uv.reshape(-1, 2) * z + (x, y)
    me.uv_layers[0].data.foreach_set("uv", uv.ravel())


def dekking(objs):
    """Deel van [0, 1]^2 dat door UV-eilanden bedekt wordt."""
    a = 0.0
    for o in objs:
        me = o.data
        me.calc_loop_triangles()
        t = np.zeros(len(me.loop_triangles) * 3, np.int32)
        me.loop_triangles.foreach_get("loops", t)
        uv = np.zeros(len(me.loops) * 2, np.float32)
        me.uv_layers[0].data.foreach_get("uv", uv)
        q = uv.reshape(-1, 2)[t.reshape(-1, 3)]
        d1, d2 = q[:, 1] - q[:, 0], q[:, 2] - q[:, 0]
        a += float(np.abs(d1[:, 0] * d2[:, 1] - d1[:, 1] * d2[:, 0]).sum() / 2)
    return a


def opp(me):
    a = np.zeros(len(me.polygons), np.float32)
    me.polygons.foreach_get("area", a)
    return float(a.sum())


# --- UV-atlas en bakken -----------------------------------------------------------------
def uv_atlas(objs, gewicht=None, marge=0.003):
    """Een gedeelde UV-ruimte over objs (multi-edit): smart project, gelijke texeldichtheid,
    dan per object geschaald met gewicht[naam] en samen gepakt."""
    gewicht = gewicht or {}
    for o in objs:
        while o.data.uv_layers:
            o.data.uv_layers.remove(o.data.uv_layers[0])
        o.data.uv_layers.new(name="UVMap")
    ontkies()
    for o in objs:
        o.select_set(True)
    bpy.context.view_layer.objects.active = objs[0]
    ts = bpy.context.scene.tool_settings
    ts.use_uv_select_sync = True
    bpy.ops.object.mode_set(mode="EDIT")
    bpy.ops.mesh.select_all(action="SELECT")
    bpy.ops.uv.smart_project(angle_limit=math.radians(50), island_margin=0.0, area_weight=0.0,
                             correct_aspect=True, scale_to_bounds=False)
    bpy.ops.uv.average_islands_scale()
    bpy.ops.object.mode_set(mode="OBJECT")
    for o in objs:
        w = gewicht.get(o.name, 1.0)
        if w != 1.0:
            uv = np.zeros(len(o.data.loops) * 2, np.float32)
            o.data.uv_layers[0].data.foreach_get("uv", uv)
            o.data.uv_layers[0].data.foreach_set("uv", uv * math.sqrt(w))
    bpy.ops.object.mode_set(mode="EDIT")
    bpy.ops.mesh.select_all(action="SELECT")
    bpy.ops.uv.pack_islands(rotate=True, margin=marge, shape_method="CONCAVE")
    bpy.ops.object.mode_set(mode="OBJECT")


def beeld(naam, w, h=None, data=False, alpha=False):
    img = bpy.data.images.new(naam, w, h or w, alpha=alpha)
    if data:
        img.colorspace_settings.name = "Non-Color"
    return img


BAKSOORT = {"kleur": ("DIFFUSE", {"COLOR"}, 16), "ruwheid": ("ROUGHNESS", set(), 4),
            "normaal": ("NORMAL", set(), 16), "ao": ("AO", set(), 96), "emissie": ("EMIT", set(), 4)}


def bak(lows, highs, beelden, ext, ray, coll, margin=6):
    """Bak highs -> een tijdelijke samengevoegde kopie van lows (zelfde UV). beelden: [(soort, img)]."""
    sc = bpy.context.scene
    kop = []
    for o in lows:
        k = o.copy()
        k.data = o.data.copy()
        coll.objects.link(k)
        kop.append(k)
    doel = join("_bakdoel", kop, coll) if len(kop) > 1 else kop[0]
    m = bpy.data.materials.new("_bak")
    m.use_nodes = True
    tn = m.node_tree.nodes.new("ShaderNodeTexImage")
    m.node_tree.nodes.active = tn
    doel.data.materials.clear()
    doel.data.materials.append(m)
    doel.data.polygons.foreach_set("material_index", np.zeros(len(doel.data.polygons), np.int32))
    for v in ("visible_diffuse", "visible_glossy", "visible_shadow", "visible_transmission",
              "visible_volume_scatter"):
        setattr(doel, v, False)
    verborgen = [o for o in coll.objects if o is not doel and not o.hide_render]
    for o in verborgen:
        o.hide_render = True
    ontkies()
    for h in highs:
        h.select_set(True)
    doel.select_set(True)
    bpy.context.view_layer.objects.active = doel
    for soort, img in beelden:
        t, pf, spp = BAKSOORT[soort]
        sc.cycles.samples = max(1, int(spp * SPP))
        tn.image = img
        t1 = time.time()
        kw = dict(type=t, use_selected_to_active=True, cage_extrusion=ext, max_ray_distance=ray, margin=margin,
                  margin_type="EXTEND", use_clear=True, target="IMAGE_TEXTURES")
        if pf:
            kw["pass_filter"] = pf
        if t == "NORMAL":
            kw.update(normal_space="TANGENT", normal_r="POS_X", normal_g="POS_Y", normal_b="POS_Z")
        bpy.ops.object.bake(**kw)
        log("  bak", img.name, soort, f"{time.time() - t1:.1f}s")
    for o in verborgen:
        o.hide_render = False
    bpy.data.objects.remove(doel)
    bpy.data.materials.remove(m)


def pixels(img):
    a = np.zeros(img.size[0] * img.size[1] * 4, np.float32)
    img.pixels.foreach_get(a)
    return a.reshape(img.size[1], img.size[0], 4)


def bewaar(img, naam, jpg=False):
    """Schrijf naar rt_textures/ en laad terug van schijf (de exporter neemt dan het bestand)."""
    pad = os.path.join(TEXDIR, naam + (".jpg" if jpg else ".png"))
    img.filepath_raw = pad
    img.file_format = "JPEG" if jpg else "PNG"
    img.save(filepath=pad, quality=jpg if jpg is not True else 92) if jpg else img.save(filepath=pad)
    data = img.colorspace_settings.name == "Non-Color"
    bpy.data.images.remove(img)
    out = bpy.data.images.load(pad, check_existing=False)
    out.name = naam
    if data:
        out.colorspace_settings.name = "Non-Color"
    return out


def orm(ao, ruw, naam, ao_min=0.0):
    """R = AO, G = ruwheid, B = metaal 0, in een beeld (glTF occlusion + metallicRoughness)."""
    a, r = pixels(ao), pixels(ruw)
    out = beeld(naam, ao.size[0], data=True)
    p = np.ones_like(a)
    p[..., 0] = np.maximum(a[..., 0], ao_min)
    p[..., 1] = r[..., 0]
    p[..., 2] = 0.0
    out.pixels.foreach_set(p.ravel())
    return out


GLTF_GROEP = None


def gltf_groep():
    global GLTF_GROEP
    if GLTF_GROEP is None:
        GLTF_GROEP = bpy.data.node_groups.new("glTF Material Output", "ShaderNodeTree")
        GLTF_GROEP.interface.new_socket("Occlusion", in_out="INPUT", socket_type="NodeSocketFloat")
    return GLTF_GROEP


def pbr(naam, kleur, nrm=None, orm_img=None, alpha=False, tweezijdig=False, ruw=0.8, uv="UVMap"):
    """Principled met beeldtexturen zoals de glTF-exporter ze herkent."""
    m = bpy.data.materials.new(naam)
    m.use_nodes = True
    nt = m.node_tree
    b = nt.nodes["Principled BSDF"]
    b.inputs["Specular IOR Level"].default_value = 0.3
    t = nt.nodes.new("ShaderNodeTexImage")
    t.image = kleur
    nt.links.new(t.outputs["Color"], b.inputs["Base Color"])
    if alpha:
        rnd = nt.nodes.new("ShaderNodeMath")
        rnd.operation = "ROUND"                           # glTF MASK, afkap 0,5
        nt.links.new(t.outputs["Alpha"], rnd.inputs[0])
        nt.links.new(rnd.outputs[0], b.inputs["Alpha"])
    if nrm:
        tn = nt.nodes.new("ShaderNodeTexImage")
        tn.image = nrm
        nm = nt.nodes.new("ShaderNodeNormalMap")
        nt.links.new(tn.outputs["Color"], nm.inputs["Color"])
        nt.links.new(nm.outputs["Normal"], b.inputs["Normal"])
    if orm_img:
        to = nt.nodes.new("ShaderNodeTexImage")
        to.image = orm_img
        sp = nt.nodes.new("ShaderNodeSeparateColor")
        nt.links.new(to.outputs["Color"], sp.inputs["Color"])
        nt.links.new(sp.outputs["Green"], b.inputs["Roughness"])
        nt.links.new(sp.outputs["Blue"], b.inputs["Metallic"])
        g = nt.nodes.new("ShaderNodeGroup")
        g.node_tree = gltf_groep()
        nt.links.new(sp.outputs["Red"], g.inputs["Occlusion"])
    else:
        b.inputs["Roughness"].default_value = ruw
    m.use_backface_culling = not tweezijdig
    return m


def vlak_mat(src, naam, emissie=None):
    """Vlakke kleur (geen textuur nodig): base, ruwheid en emissie uit het bronmateriaal."""
    sb = src.node_tree.nodes["Principled BSDF"]
    m = bpy.data.materials.new(naam)
    m.use_nodes = True
    b = m.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = sb.inputs["Base Color"].default_value
    b.inputs["Roughness"].default_value = sb.inputs["Roughness"].default_value
    b.inputs["Specular IOR Level"].default_value = 0.3
    if emissie:
        b.inputs["Emission Color"].default_value = sb.inputs["Emission Color"].default_value
        b.inputs["Emission Strength"].default_value = emissie
    m.use_backface_culling = True
    return m


def zet_mat(o, mats):
    """Slots vervangen; materials.clear() zet elke vlakindex op 0, dus indices bewaren."""
    idx = np.zeros(len(o.data.polygons), np.int32)
    o.data.polygons.foreach_get("material_index", idx)
    o.data.materials.clear()
    for m in mats:
        o.data.materials.append(m)
    o.data.polygons.foreach_set("material_index", np.minimum(idx, len(mats) - 1))


def tris(objs):
    n = 0
    for o in objs:
        o.data.calc_loop_triangles()
        n += len(o.data.loop_triangles)
    return n


# --- Dilatie voor alfakaarten: kleur in de lege pixels, anders donkere randen in de mips ---
def dilateer(p, vul, stappen=24):
    """p (h, w, 4) met alfa; vul = rgb voor wat na de stappen nog leeg is."""
    rgb, a = p[..., :3].copy(), p[..., 3]
    mask = a > 0.3
    rgb[~mask] = 0
    for _ in range(stappen):
        acc = np.zeros_like(rgb)
        cnt = np.zeros(mask.shape, np.float32)
        for dy, dx in ((-1, 0), (1, 0), (0, -1), (0, 1), (-1, -1), (1, 1), (-1, 1), (1, -1)):
            m2 = np.roll(np.roll(mask, dy, 0), dx, 1)
            acc += np.roll(np.roll(rgb, dy, 0), dx, 1) * m2[..., None]
            cnt += m2
        nieuw = (~mask) & (cnt > 0)
        rgb[nieuw] = acc[nieuw] / cnt[nieuw][:, None]
        mask = mask | nieuw
    rgb[~mask] = vul
    return np.concatenate([rgb, a[..., None]], axis=2)


# =========================================================================================
def bouw():
    bpy.ops.wm.open_mainfile(filepath=BLEND)
    sc = bpy.context.scene
    log("blend geopend; GPU:", gpu(sc))
    sc.render.engine = "CYCLES"
    sc.cycles.use_denoising = False
    sc.render.bake.use_selected_to_active = True
    sc.world.light_settings.distance = 0.35            # AO-afstand voor de bake
    os.makedirs(TEXDIR, exist_ok=True)
    RT = bpy.data.collections.new("RT")
    sc.collection.children.link(RT)
    ORIG = [o for o in sc.objects if o.type == "MESH" and o.name != "Plane"]
    per_mat = defaultdict(list)
    for o in ORIG:
        per_mat[mat0(o)].append(o)

    # halmen -> buizen (hoog), de hair curves zelf uit de render
    HALM = {}
    for naam in ("dakhalmen", "aanbouwhalmen", "kuifhalmen"):
        ob = sc.objects[naam]
        kr, st, bos = halmen_van(ob)
        rnd = np.random.default_rng(len(kr))
        me = buizen(naam + "_buis", kr, st, {"bos": bos, "hrand": rnd.random(len(kr))})
        me.materials.append(mat_attr(ob.data.materials[0]))
        HALM[naam] = obj(naam + "_buis", me, sc.collection)
        ob.hide_render = True
        log("halmen", naam, len(kr), "->", len(me.polygons), "quads")

    # ---------------------------------------------------------------- LOD0: stenen
    STEEN_M = ("steen", "schoorsteensteen", "rots", "stoep")
    stenen = [o for m in STEEN_M for o in per_mat[m]]
    kozijnen = per_mat["kozijn"]
    kern_r = lambda z: HUT_R - 0.04 - 0.02 * min(max(z / (WALL_H + 0.2), 0), 1)
    dprof = [(r, z) for r, z in dome_profile()[3:]]       # bovenkant koepel, r dalend met z

    def onder_dak(r, z):
        for (r0, z0), (r1, z1) in zip(dprof, dprof[1:]):
            if r1 <= r <= r0:
                return z < z0 + (z1 - z0) * (r0 - r) / (r0 - r1) - 0.03
        return False

    def verborgen(c):
        """Vlakmidden dat nooit te zien is: in de grond, in de muurkern, in de schoorsteen, onder het dak."""
        x, y, z = c
        if z < -0.004:
            return True
        rh = math.hypot(x - HX, y - HY)
        if z < WALL_H + 0.15 and HUT_R - 0.22 < rh < kern_r(z) - 0.008:
            return True
        rc = math.hypot(x - CH[0], y - CH[1])
        if 2.6 < z < 3.95 and rc < ch_r(z) - 0.068:
            return True
        if z > 2.3 and rc < 0.7 and onder_dak(rh, z):
            return True
        if z < 2.0 and AX0 + 0.068 < x < AX0 + 0.3 and AY0 < y < AY1:      # aanbouw, -X-muur
            return True
        if z < 2.0 and AY0 + 0.068 < y < AY0 + 0.3 and AX0 < x < 0.35:      # aanbouw, voorkant
            return True
        return False

    def snij(me):
        bm = bmesh.new()
        bm.from_mesh(me)
        weg = [f for f in bm.faces if all(verborgen(v.co) for v in f.verts)]   # zijvlakken steken half uit
        bmesh.ops.delete(bm, geom=weg, context="FACES")
        bm.to_mesh(me)
        bm.free()
        return len(weg)

    delen, weg, maten = [], 0, []
    met_uv = set()
    for o in stenen:
        kei = o.data.name.startswith("kei")
        base = decimeer(o.data, 0.04 if kei else 0.18, RT, sharp=60)
        if base.name not in met_uv:
            uv_eenheid(base, RT)
            met_uv.add(base.name)
        me = base.copy()
        me.transform(o.matrix_world)
        maten.append(math.sqrt(opp(me)))
        weg += snij(me)
        delen.append(me)
    for o in kozijnen:                                 # bron heeft wisselende windingen; Cycles is tweezijdig
        me = eval_mesh(o)
        bm = bmesh.new()
        bm.from_mesh(me)
        bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
        bm.to_mesh(me)
        bm.free()
        uv_eenheid(me, RT)
        maten.append(math.sqrt(opp(me)) * 0.8)
        delen.append(me)
    for me, cel in zip(delen, schap(maten, 3.0 / RES)):
        uv_plaats(me, cel)
    me = samen_bm("stenen", delen)
    for d in delen:
        bpy.data.meshes.remove(d)
    me.materials.clear()
    o_stenen = obj("stenen_rt", me, RT)
    log("stenen", len(stenen), "+ kozijnen", len(kozijnen), "tris", tris([o_stenen]), "weggesneden vlakken", weg)

    # ---------------------------------------------------------------- LOD0: riet (koepel, deksel, band)
    bandtouw = [o for o in per_mat["band"] if o.name.startswith("touw")]
    band = [o for o in per_mat["band"] if o.name.startswith("band")]
    dak, adak = sc.objects["dak"], sc.objects["aanbouwdak"]
    m_dak = eval_mesh(dak)
    m_adak = eval_mesh(adak)
    m_band = lathe_np("band_rt", [(0.66, 3.80), (0.66, 3.95), (0.66, 4.10), (0.66, 4.25), (0.66, 4.43)], 40,
                      cap_top=True)
    m_band.transform(Matrix.Translation((HX, HY, 0)))
    o_riet = obj("riet_rt", samen_bm("riet", [m_dak, m_adak, m_band]), RT)
    log("riet tris", tris([o_riet]))

    # ---------------------------------------------------------------- LOD0: hout, specie, gras, deuren
    HOUT = ("stijl", "kopshout")
    hout_bron = [o for m in HOUT for o in per_mat[m]]
    delen = []
    for o in hout_bron:
        me = eval_mesh(o)
        if o.name.startswith("regel") and len(me.polygons) > 1000:
            o2 = obj("_r", me, RT)
            me = decimeer(me, 0.45, RT)
            bpy.data.objects.remove(o2)
        delen.append(me)
    # sjorringen: per ring drie strengen -> een torus om ze heen
    ringen = defaultdict(list)
    for o in per_mat["touw"]:
        key = tuple(round(v, 3) for v in (*o.location, *o.rotation_euler))
        ringen[key].append(o)
    for key, plies in ringen.items():
        me = torus_mesh("sjor", 0.16, 0.032, 32, 6)
        me.transform(plies[0].matrix_world)
        delen.append(me)
    o_hout = obj("hout_rt", samen_bm("hout", delen), RT)
    o_specie = obj("specie_rt", samen_bm("specie", [eval_mesh(o) for o in per_mat["specie"]]), RT)
    o_gras = obj("gras_rt", samen_bm("gras", [eval_mesh(o) for o in per_mat["gras"]]), RT)
    log("sjorringen", len(ringen), "hout tris", tris([o_hout]), "specie", tris([o_specie]), "gras", tris([o_gras]))

    ijzer = per_mat["ijzer"]
    M_IJZER = vlak_mat(ijzer[0].material_slots[0].material, "ijzer_rt")

    def deurmesh(naam, planken, ring):
        me_p = samen_bm(naam + "_p", [eval_mesh(p) for p in planken])
        rm = eval_mesh(ring)
        rob = obj("_ring", rm, RT)
        rm2 = decimeer(rm, 0.12, RT)
        bpy.data.objects.remove(rob)
        po, ro = obj(naam, me_p, RT), obj("_ring", rm2.copy(), RT)
        zet_mat(po, [bpy.data.materials.new("_a")])        # zet_mat wist eerst de bronslots
        zet_mat(ro, [M_IJZER])
        return join(naam, [po, ro], RT)

    DEUR = {}
    for piv, naam in (("deur_voor", "voordeur"), ("deur_aanbouw", "aanbouwdeur")):
        e = sc.objects[piv]
        kids = list(e.children)
        ring = [k for k in kids if mat0(k) == "ijzer"][0]
        DEUR[piv] = deurmesh(naam + "_rt", [k for k in kids if mat0(k) == "deur"], ring)
    luik_p = [o for o in per_mat["deur"] if o.name.startswith("luik")]
    lc = sum((p.matrix_world.translation for p in luik_p), Vector()) / len(luik_p)
    luik_r = min([o for o in ijzer if o.parent is None], key=lambda o: (o.matrix_world.translation - lc).length)
    o_luik = deurmesh("luik_rt", luik_p, luik_r)
    deuren_bron = [k for piv in DEUR for k in sc.objects[piv].children] + luik_p + [luik_r]

    # ---------------------------------------------------------------- LOD0: vlakke materialen
    def vlak(naam, bronnen, emissie=None, dec=None):
        delen = []
        for o in bronnen:
            me = eval_mesh(o)
            if dec:
                t = obj("_v", me, RT)
                me = decimeer(me, dec, RT, sharp=40).copy()
                bpy.data.objects.remove(t)
            delen.append(me)
        o = obj(naam, samen_bm(naam, delen), RT)
        o.data.materials.clear()
        o.data.materials.append(vlak_mat(bronnen[0].material_slots[0].material, naam, emissie))
        return o

    VLAK = [vlak("ruit_rt", per_mat["ruit"], 0.0),                    # overdag uit, zoals Cycles; nacht: game
             vlak("tafelkaars_rt", per_mat["was"]),
            vlak("kaarsvlam_rt", per_mat["vlam"], 4.0), vlak("haardvuur_rt", per_mat["vuur"], 0.6, dec=0.1),
            vlak("rookgat_rt", per_mat["donker"]), vlak("dakonder_rt", per_mat["onderkant"])]

    # ---------------------------------------------------------------- riet: kaarten
    kaarten, kuif_kaarten = kaarten_bouwen(sc, RT, dak)
    log("kaarten tris", tris([kaarten]), "kuif", tris([kuif_kaarten]))

    # ---------------------------------------------------------------- LOD1
    lod1 = lod1_bouwen(sc, RT, per_mat, stenen, kozijnen, hout_bron, adak)
    l1_deur = {}
    for piv in DEUR:
        e = sc.objects[piv]
        kids = [k for k in e.children if mat0(k) == "deur"]
        l1_deur[piv] = obj(piv + "_l1", deur_doos(kids, e), RT)
    luik_l1 = obj("luik_l1", deur_doos(luik_p, None), RT)
    l1_alles = [lod1, luik_l1] + list(l1_deur.values())

    # ---------------------------------------------------------------- bakken
    halm = list(HALM.values())
    hout_alle = hout_bron + per_mat["touw"] + per_mat["specie"] + per_mat["gras"] + deuren_bron
    riet_alle = [dak, adak] + band + bandtouw
    l1_bron = (stenen + kozijnen + hout_alle + riet_alle + per_mat["onderkant"] + per_mat["donker"])
    l1_bron = [o for o in l1_bron if not o.name.startswith(("vloer", "tafel", "kist", "ton", "gras"))]
    Z = {k: zelfstandig("_z_" + k, v, RT) for k, v in
         (("steen", stenen + kozijnen), ("riet", riet_alle), ("hout", hout_alle), ("lod1", l1_bron))}
    for o in ORIG:
        o.hide_render = True                              # alleen de samengevoegde bronnen in Cycles
    for o in Z.values():
        o.hide_render = True
    gm = bpy.data.materials["gras_z"].node_tree           # gras: translucent telt niet als diffuus
    [n for n in gm.nodes if n.type == "MIX_SHADER"][0].inputs["Fac"].default_value = 0.0
    G = [("steen", [o_stenen], [Z["steen"]], 0.025, 0.08, {}),
         ("riet", [o_riet], halm + [Z["riet"]], 0.16, 0.26, {}),
         ("hout", [o_hout, o_specie, o_gras, DEUR["deur_voor"], DEUR["deur_aanbouw"], o_luik], [Z["hout"]],
          0.035, 0.1, {"specie_rt": 0.2, "voordeur_rt": 1.6, "aanbouwdeur_rt": 1.6, "luik_rt": 1.6, "gras_rt": 1.5}),
         ("lod1", l1_alles, halm + [Z["lod1"]], 0.12, 0.3, {})]
    ZGROEP = {k: ["steen", "riet", "hout"] for k in ("steen", "riet", "hout")} | {"lod1": ["lod1"]}  # AO ziet de rest
    MAT = {}
    for naam, lows, highs, ext, ray, w in G:
        t1 = time.time()
        if naam != "steen":                               # stenen: al een cel per steen
            uv_atlas(lows, w)
        log("groep", naam, "UV-dekking", round(dekking(lows), 2))
        res, ores = (LOD1_RES, LOD1_RES // 2) if naam == "lod1" else (RES, ORM_RES)
        kl, nr = beeld(naam + "_kleur", res), beeld(naam + "_normaal", res, data=True)
        ao, ru = beeld(naam + "_ao", ores, data=True), beeld(naam + "_ruw", ores, data=True)
        for k in ZGROEP[naam]:                             # alleen deze bron doet mee in Cycles
            Z[k].hide_render = False
        bak(lows, highs, [("kleur", kl), ("normaal", nr)], ext, ray, RT)
        bak(lows, highs, [("ao", ao), ("ruwheid", ru)], ext, ray, RT, margin=3)
        for k in ZGROEP[naam]:
            Z[k].hide_render = True
        o_img = bewaar(orm(ao, ru, naam + "_orm"), naam + "_orm")
        bpy.data.images.remove(ao)
        bpy.data.images.remove(ru)
        MAT[naam] = (bewaar(kl, naam + "_kleur", jpg=True), bewaar(nr, naam + "_normaal", jpg=95), o_img)  # png: 22 MB
        log("groep", naam, f"{time.time() - t1:.0f}s")
    k, n, o_ = MAT["steen"]
    zet_mat(o_stenen, [pbr("steen_rt", k, n, o_)])
    k, n, o_ = MAT["riet"]
    zet_mat(o_riet, [pbr("riet_rt", k, n, o_)])
    k, n, o_ = MAT["hout"]
    m_hout, m_2z = pbr("hout_rt", k, n, o_), pbr("hout_2z_rt", k, n, o_, tweezijdig=True)
    for o in (o_hout, ):
        zet_mat(o, [m_hout])
    for o in (o_specie, o_gras):
        zet_mat(o, [m_2z])
    for o in (DEUR["deur_voor"], DEUR["deur_aanbouw"], o_luik):
        zet_mat(o, [m_hout, M_IJZER])
    k, n, o_ = MAT["lod1"]
    m_l1 = pbr("lod1_rt", k, n, o_)
    for o in l1_alles:
        zet_mat(o, [m_l1])

    # ---------------------------------------------------------------- opruimen en hernoemen
    for o in [o for o in sc.objects if o.type in ("MESH", "CURVES", "LIGHT", "CAMERA") and o.users_collection[0] is not RT]:
        bpy.data.objects.remove(o)
    bpy.data.orphans_purge(do_recursive=True)
    for m in bpy.data.materials:
        if m.name.endswith("_rt"):
            m.name = m.name[:-3]
    for o in list(RT.objects):
        if o.name.endswith("_rt"):
            o.name = o.name[:-3]
            o.data.name = o.name
    for piv, o in list(DEUR.items()) + list(l1_deur.items()):
        e = sc.objects[piv]
        o.parent = e
        o.matrix_parent_inverse = e.matrix_world.inverted()
    l1_deur["deur_voor"].name = "voordeur_lod1"
    l1_deur["deur_aanbouw"].name = "aanbouwdeur_lod1"
    lod1.name = "hut_lod1"
    luik_l1.name = "luik_lod1"
    ANKERS = [o for o in sc.objects if o.type == "EMPTY"]

    lod0 = [o for o in RT.objects if o not in l1_alles]
    log("LOD0 tris", tris(lod0), "LOD1 tris", tris(l1_alles))
    for o in lod0:
        log("   ", o.name, tris([o]), [m.name for m in o.data.materials])
    exporteer(GLB0, lod0 + ANKERS)
    exporteer(GLB1, l1_alles + ANKERS)
    bpy.ops.wm.save_as_mainfile(filepath=os.path.join(HERE, "peasant_hut_rt.blend"), compress=True)


def exporteer(pad, objs):
    ontkies()
    for o in objs:
        o.select_set(True)
    bpy.ops.export_scene.gltf(filepath=pad, export_format="GLB", use_selection=True, export_apply=True,
                              export_tangents=True, export_image_format="AUTO", export_cameras=False,
                              export_lights=False, export_extras=False, export_animations=False)
    log("export", os.path.basename(pad), f"{os.path.getsize(pad) / 1e6:.1f} MB")


def deur_doos(planken, piv):
    """LOD1-deur: een doos om de planken, in het assenstelsel van de scharnier (of van de eerste plank)."""
    M = (piv.matrix_world if piv else planken[0].matrix_world).copy()
    Mi = M.inverted()
    pts = [Mi @ (p.matrix_world @ Vector(c)) for p in planken for c in p.bound_box]
    lo = Vector([min(p[i] for p in pts) for i in range(3)])
    hi = Vector([max(p[i] for p in pts) for i in range(3)])
    me = box_mesh("deur_l1", lo, hi)
    me.transform(M)
    return me


# --- Kaarten ------------------------------------------------------------------------------
# Kaartatlas: 2 x 2 m wereld op [0, 1]^2. Boven: vijf stroken van 0,4 x 1,0 m (3 koepel, zoom, deksel);
# onder: kuifschoof van opzij (1,0 x 0,6 m) en van boven (0,8 x 0,8 m).
STROOK = [((0.4 * k, 1.0), (0.4 * k + 0.4, 2.0)) for k in range(5)]   # 0-2 koepel, 3 zoom, 4 aanbouwdak
KUIF_ZIJ = ((0.0, 0.4), (1.0, 1.0))
KUIF_TOP = ((1.0, 0.2), (1.8, 1.0))
KUIF_VOET = 0.43                                      # voet van de schoof in KUIF_ZIJ (y, m)
LREF = 0.82                                           # laaglengte waarop een strook getekend is
CONTRAST = 1.4                                        # op de kaartkleur, rond het gemiddelde
VERZADIG = 1.25                                       # gemeten tegen de Cycles-beauty (HSV-s 0,68)


def uv_van(p):
    return (p[0] / 2.0, p[1] / 2.0)


def grid(naam, P, nu, nv, regio, n_uit, flip_ok=True):
    """Kaart als raster; P(t, w) -> punt, t dwars 0..1, w van wortel (0) naar punt (1).
    regio = ((x0, y0), (x1, y1)) in de kaartatlas; wortel boven. n_uit: buitennormaal (Vector).
    Spiegelt t als de UV anders gespiegeld zou liggen t.o.v. de buitenkant."""
    (x0, y0), (x1, y1) = regio
    c, d = P(0.5, 0.5), 0.02
    et = P(0.5 + d, 0.5) - P(0.5 - d, 0.5)
    eb = P(0.5, 0.5 - d) - P(0.5, 0.5 + d)                # naar de wortel = tekstuur omhoog
    if et.cross(eb).dot(n_uit) < 0:
        P0 = P
        P = lambda t, w: P0(1 - t, w)
    vs, uvs, fs = [], [], []
    for j in range(nv):
        for i in range(nu):
            t, w = i / (nu - 1), j / (nv - 1)
            vs.append(P(t, w))
            uvs.append(uv_van((x0 + (x1 - x0) * t, y1 - (y1 - y0) * w)))
    for j in range(nv - 1):
        for i in range(nu - 1):
            a = j * nu + i
            fs.append([a, a + nu, a + nu + 1, a + 1])
    return vs, uvs, fs


class Kaartset:
    def __init__(self):
        self.vs, self.uvs, self.fs, self.nrm = [], [], [], []

    def voeg(self, vs, uvs, fs, nrm=None):
        k = len(self.vs)
        self.vs += vs
        self.uvs += uvs
        self.fs += [[k + i for i in f] for f in fs]
        self.nrm += nrm or [None] * len(vs)

    def mesh(self, naam):
        me = mesh_py(naam, self.vs, self.fs)
        uv = me.uv_layers.new(name="UVMap")
        for poly in me.polygons:
            for li in poly.loop_indices:
                uv.data[li].uv = self.uvs[me.loops[li].vertex_index]
        if any(n is not None for n in self.nrm):
            me.normals_split_custom_set_from_vertices([tuple(n) if n is not None else tuple(me.vertices[i].normal)
                                                       for i, n in enumerate(self.nrm)])
        return me


def dak_punt(a, s, off):
    """Punt op de koepel zoals de halmen: profiel op booglengte s (voorbij S_END: hangend),
    `off` langs de normaal, dan de schulp en de wenkbrauw."""
    if s <= S_END:
        _, rr, zz, nr, nz = at(PROF, max(s, 0.0))
        rr, zz = rr + nr * off, zz + nz * off
    else:
        _, r1, z1, nr, nz = at(PROF, S_END)
        _, r0, z0, _, _ = at(PROF, S_END - 0.06)
        L = math.hypot(r1 - r0, z1 - z0)
        h = s - S_END
        rr = r1 + nr * off + (r1 - r0) / L * h
        zz = z1 + nz * off + (z1 - z0) / L * h - 0.3 * h * h / 0.11
    if zz < 2.06:
        rr *= 1 + 0.03 * math.cos(9 * a) * min(1.0, (2.06 - zz) / 0.1)
    rr, zz = brow(a, rr, zz)
    return Vector((HX + rr * math.cos(a), HY + rr * math.sin(a), zz))


def kaarten_bouwen(sc, RT, dak):
    rnd = random.Random(5)
    K = Kaartset()
    BREED = 0.40
    dg = bpy.context.evaluated_depsgraph_get()
    dak_bvh = BVHTree.FromObject(dak, dg)
    dak_inv = dak.matrix_world.inverted()

    def in_dak(p):
        q = dak_inv @ p
        hit = dak_bvh.ray_cast(q, Vector((0, 0, 1)), 5.0)
        return hit[0] is not None and hit[1].z > 0

    # koepel: per laag een ring kaarten, wortel op s0, lengte 1,22 L (zoals de strook)
    for s0, L in B["KOERS_DAK"]:
        zoom = s0 + L > S_END - 0.05
        s_a = s0 - 0.05
        s_b = S_END + 0.12 if zoom else s_a + L / LREF
        rmid = at(PROF, min(s0 + 0.7 * L, S_END))[1]
        n = max(8, math.ceil(2 * math.pi * rmid / 0.26))
        fase = rnd.random()
        for j in range(n):
            ac = 2 * math.pi * (j + fase + rnd.uniform(-0.15, 0.15)) / n
            reg = STROOK[3] if zoom else STROOK[rnd.randrange(3)]

            def P(t, w, ac=ac, s0=s0, L=L, s_a=s_a, s_b=s_b):
                s = s_a + (s_b - s_a) * w
                u = min(max((s - s0) / L, 0.0), 1.0)
                off = -0.025 + 0.0075 + 0.075 * u ** 0.9 + 0.005
                r = max(at(PROF, min(s, S_END))[1], 0.55)
                a = ac + (t - 0.5) * BREED / r
                return dak_punt(a, s, off)
            c = P(0.5, 0.3)
            nuit = (c - Vector((HX, HY, 1.2))).normalized()
            K.voeg(*grid("k", P, 3, 9, reg, nuit))
    nd = len(K.fs)
    # aanbouwdak: lagen langs +Y, kaarten dwars (x), zoom over de achterrand
    for y0, L in B["KOERS_LID"]:
        zoom = y0 + L > LY1 - 0.05
        y_a = y0 - 0.05
        y_b = LY1 + 0.12 if zoom else y_a + L / LREF
        n = math.ceil((LX1 - LX0) / 0.26)
        for j in range(n):
            xc = LX0 + 0.22 + (LX1 - LX0 - 0.44) * (j + rnd.uniform(-0.2, 0.2)) / max(n - 1, 1)
            reg = STROOK[3] if zoom else STROOK[4]

            def P(t, w, xc=xc, y0=y0, L=L, y_a=y_a, y_b=y_b):
                x = xc + (t - 0.5) * BREED
                x = min(max(x, LX0 + 0.02), LX1 - 0.01)
                y = y_a + (y_b - y_a) * w
                u = min(max((y - y0) / L, 0.0), 1.0)
                if y <= LY1:
                    z = lid_top(x, y) - 0.02 + 0.0075 + 0.06 * u ** 0.9 + 0.005
                else:
                    h = y - LY1
                    z = lid_top(x, LY1) - 0.02 + 0.0675 + 0.005 - 2.0 * h
                    y = LY1 + 0.5 * h
                return Vector((x, y, z))
            pts = [P(t, w) for t in (0, 1) for w in (0, 0.5, 1)]
            if all(in_dak(p) for p in pts):
                continue
            K.voeg(*grid("k", P, 3, 7, reg, Vector((0, 0, 1))))
    # linkerrand van het aanbouwdak: dwars over de rand gekamd en naar beneden (onderste 60 % van de zoom)
    (zx0, zy0), (zx1, zy1) = STROOK[3]
    zreg = ((zx0, zy0), (zx1, zy0 + 0.6))
    y = LY0 + 0.1
    while y < LY1 + 0.05:
        yc = y + rnd.uniform(-0.04, 0.04)
        x0 = LX0 + 0.36

        def P(t, w, yc=yc, x0=x0):
            yy = yc + (t - 0.5) * BREED
            yy = min(max(yy, LY0), LY1 + 0.04)
            x = x0 + (LX0 - 0.05 - x0) * min(w / 0.75, 1.0)
            z = lid_top(max(x, LX0), min(yy, LY1)) + 0.03 + 0.03 * w
            if w > 0.6:
                z -= (w - 0.6) / 0.4 * 0.19
                x -= (w - 0.6) / 0.4 * 0.03
            return Vector((x, yy, z))
        pts = [P(t, w) for t in (0, 1) for w in (0, 1)]
        if not all(in_dak(p) for p in pts):
            K.voeg(*grid("k", P, 3, 7, zreg, Vector((-0.6, 0, 0.8)).normalized()))
        y += 0.3
    log("kaarten: koepel", nd // 16, "aanbouw", (len(K.fs) - nd) // 12)
    me = K.mesh("riet_kaarten")
    o_k = obj("riet_kaarten_rt", me, RT)

    # kuif: per schoof drie gekruiste kaarten om de as en een liggende bovenop
    KU = Kaartset()
    for k in range(7):
        if k < 6:
            a = 2 * math.pi * k / 6 + 0.3
            cx, cy, tilt = 0.40 * math.cos(a), 0.40 * math.sin(a), 0.25
        else:
            a, cx, cy, tilt = 0.0, 0.0, 0.0, 0.0
        out = Vector((math.cos(a), math.sin(a), 0))
        voet = Vector((HX + cx, HY + cy, 4.28))
        as_ = (Vector((0, 0, 1)) + out * tilt).normalized()
        zij = out.cross(Vector((0, 0, 1)))
        if zij.length < 1e-6:
            zij = Vector((0, 1, 0))
        zij.normalize()
        voor = as_.cross(zij).normalized()
        midden = voet + as_ * 0.22
        (rx0, ry0), (rx1, ry1) = KUIF_ZIJ
        for fi in range(3):
            phi = math.pi * fi / 3 + 0.4 * k
            e_t = zij * math.cos(phi) + voor * math.sin(phi)

            def P(t, w, e_t=e_t):
                return voet + e_t * ((rx0 + (rx1 - rx0) * t) - 0.5) + as_ * (ry1 - KUIF_VOET - (ry1 - ry0) * w)
            vs, uvs, fs = grid("ku", P, 3, 4, KUIF_ZIJ, e_t.cross(as_), flip_ok=False)
            nr_ = [((v - midden).normalized() + as_ * 0.5).normalized() for v in vs]
            KU.voeg(vs, uvs, fs, nr_)
            KU.voeg(vs, uvs, [f[::-1] for f in fs], nr_)     # achterkant apart: tweezijdig zou de normaal omdraaien
        (tx0, ty0), (tx1, ty1) = KUIF_TOP
        top = voet + as_ * 0.36

        def P(t, w):
            return top + zij * ((tx1 - tx0) * (t - 0.5)) + voor * ((ty1 - ty0) * (0.5 - w))
        vs, uvs, fs = grid("kt", P, 3, 3, KUIF_TOP, as_)
        nr_ = [((v - (voet + as_ * 0.1)).normalized() * 0.5 + as_).normalized() for v in vs]
        KU.voeg(vs, uvs, fs, nr_)
        KU.voeg(vs, uvs, [f[::-1] for f in fs], nr_)
    o_ku = obj("kuif_rt", KU.mesh("kuif"), RT)

    # textuur: de echte halmen in een studio, recht van boven, ortho
    kl, nr = kaart_studio(sc)
    m = pbr("riet_kaart_rt", kl, nr, None, alpha=True, tweezijdig=True, ruw=0.75)
    zet_mat(o_k, [m])
    zet_mat(o_ku, [pbr("kuif_rt", kl, nr, None, alpha=True, tweezijdig=False, ruw=0.75)])
    return o_k, o_ku


def strook_halmen(rnd, regio, zoom, bereik=(0.0, 1.0)):
    """Halmen van een laag, plat op z = 0, wortel boven (+y), zoals het halmblok in peasant_hut.py."""
    (x0, y0), (x1, y1) = regio
    kr, st, bos = [], [], []
    nb = int((x1 - x0) / 0.065) + 1
    for b in range(nb):
        xb = x0 + 0.02 + (x1 - x0 - 0.04) * (b + rnd.uniform(-0.3, 0.3)) / (nb - 1)
        bv = rnd.uniform(*bereik)
        Lb = LREF * rnd.uniform(0.85, 1.1)
        lean = rnd.gauss(0, 0.012)
        for _ in range(18):
            xi = xb + rnd.gauss(0, 0.024)
            if not x0 + 0.012 < xi < x1 - 0.012:
                continue
            yi = y1 - 0.05 + rnd.uniform(-0.04, 0.04)
            if zoom:
                ye = y0 + 0.12 - rnd.uniform(0.0, 0.11) * rnd.random() ** 0.5
            else:
                ye = max(yi - Lb * rnd.uniform(0.9, 1.05), y0 + 0.01)
            lift = rnd.uniform(0.0, 0.015)
            pts = []
            for k in range(8):
                u = k / 7
                x = xi + lean * u * (yi - ye) + (xi - xb) * (-0.15 * u)
                x = min(max(x, x0 + 0.008), x1 - 0.008)
                pts.append((x, yi + (ye - yi) * u, lift + 0.075 * u ** 0.9))
            kr.append(np.array(pts))
            st.append(np.array([0.0062 - 0.0018 * k / 7 for k in range(8)]))
            bos.append(bv)
    return kr, st, bos


def kaart_studio(sc0):
    """Rendert de kaartatlas: kleur (emissie, met wat AO) en normaal (Raw), alfa uit de film."""
    rnd = random.Random(23)
    kr, st, bos = [], [], []
    for k, reg in enumerate(STROOK):
        a, b, c = strook_halmen(rnd, reg, zoom=(k == 3), bereik=(0.35, 0.7) if k == 4 else (0.0, 1.0))  # deksel: als de bron
        kr += a
        st += b
        bos += c
    kk, ks, kb = [], [], []
    alle = B["KUIF_C"]
    sch = [np.array(alle[i]) for i in range(6 * 340, 7 * 340)]  # middelste schoof: rechtop
    voet = np.array([HX, HY, 4.28])
    rot = np.array([[1, 0, 0], [0, 0, 1], [0, -1, 0]], float)   # zijaanzicht: z -> +y, y -> -z
    zx = (KUIF_ZIJ[0][0] + KUIF_ZIJ[1][0]) / 2
    tx, ty = (KUIF_TOP[0][0] + KUIF_TOP[1][0]) / 2, (KUIF_TOP[0][1] + KUIF_TOP[1][1]) / 2
    for c in sch:
        q = c - voet
        kk.append(q @ rot.T + np.array([zx, KUIF_VOET, 0.5]))
        kk.append(q + np.array([tx, ty, 0.0]))
        rad = np.array([0.006 + 0.008 * (j / 6) ** 3 for j in range(len(c))])
        ks += [rad, rad]
        kb += [0.3 * random.Random(len(kb)).random()] * 2   # laag: de kuifhelling loopt naar bleek geel

    s = bpy.data.scenes.new("kaartstudio")
    s.render.engine = "CYCLES"
    gpu(s)
    s.cycles.samples = 48 if not SNEL else 12
    s.cycles.use_denoising = False
    s.render.film_transparent = True
    s.render.resolution_x = s.render.resolution_y = KAART_RES
    s.render.filter_size = 0.9
    s.render.image_settings.color_mode = "RGBA"
    s.render.image_settings.file_format = "PNG"
    s.render.image_settings.color_depth = "8"
    s.world = bpy.data.worlds.new("zwart")
    cd = bpy.data.cameras.new("kaartcam")
    cd.type = "ORTHO"
    cd.ortho_scale = 2.0
    cam = bpy.data.objects.new("kaartcam", cd)
    s.collection.objects.link(cam)
    cam.location = (1.0, 1.0, 5.0)
    s.camera = cam
    halm_m = bpy.data.materials["halm_buis"]
    kuif_m = bpy.data.materials["kuifhalm_buis"]

    def emis(src, naam, ao_d=0.04, ao_f=0.6):
        m = src.copy()
        m.name = naam
        nt = m.node_tree
        bs = nt.nodes["Principled BSDF"]
        kleur = bs.inputs["Base Color"].links[0].from_socket
        ao = nt.nodes.new("ShaderNodeAmbientOcclusion")
        ao.inputs["Distance"].default_value = ao_d
        ao.samples = 16
        mul = nt.nodes.new("ShaderNodeMix")
        mul.data_type = "RGBA"
        mul.blend_type = "MULTIPLY"
        mul.inputs["Factor"].default_value = ao_f
        nt.links.new(kleur, [i for i in mul.inputs if i.name == "A" and i.type == "RGBA"][0])
        nt.links.new(ao.outputs["AO"], [i for i in mul.inputs if i.name == "B" and i.type == "RGBA"][0])
        em = nt.nodes.new("ShaderNodeEmission")
        nt.links.new([o for o in mul.outputs if o.type == "RGBA"][0], em.inputs["Color"])
        nt.links.new(em.outputs[0], nt.nodes["Material Output"].inputs["Surface"])
        return m

    nm = bpy.data.materials.new("normaal_emis")
    nm.use_nodes = True
    nt = nm.node_tree
    geo = nt.nodes.new("ShaderNodeNewGeometry")
    vm = nt.nodes.new("ShaderNodeVectorMath")
    vm.operation = "MULTIPLY_ADD"
    vm.inputs[1].default_value = (0.5, 0.5, 0.5)
    vm.inputs[2].default_value = (0.5, 0.5, 0.5)
    nt.links.new(geo.outputs["Normal"], vm.inputs[0])
    em = nt.nodes.new("ShaderNodeEmission")
    nt.links.new(vm.outputs[0], em.inputs["Color"])
    nt.links.new(em.outputs[0], nt.nodes["Material Output"].inputs["Surface"])

    r2 = np.random.default_rng(3)
    o1 = obj("strook", buizen("strook", kr, st, {"bos": bos, "hrand": r2.random(len(kr))}, sides=6), s.collection)
    o2 = obj("schoof", buizen("schoof", kk, ks, {"bos": kb, "hrand": r2.random(len(kk))}, sides=6), s.collection)
    uit = {}
    for soort, mats, vt in (("kleur", (emis(halm_m, "halm_emis"), emis(kuif_m, "kuif_emis", 0.08, 0.7)), "Standard"),
                            ("normaal", (nm, nm), "Raw")):
        zet_mat(o1, [mats[0]])
        zet_mat(o2, [mats[1]])
        s.view_settings.view_transform = vt
        s.view_settings.look = "None"
        s.render.filepath = os.path.join(TEXDIR, f"_studio_{soort}.png")
        bpy.ops.render.render(write_still=True, scene=s.name)
        img = bpy.data.images.load(s.render.filepath, check_existing=False)
        if soort == "normaal":
            img.colorspace_settings.name = "Non-Color"
        p = pixels(img)
        bpy.data.images.remove(img)
        os.remove(s.render.filepath)
        if soort == "kleur":                           # Cycles-halmen hebben meer contrast (std 0,15 tegen 0,09)
            lum = p[..., :3] @ np.array([0.2126, 0.7152, 0.0722])   # alleen helderheid: tint blijft
            gem = lum[p[..., 3] > 0.5].mean()
            f = (gem + (lum - gem) * CONTRAST) / np.maximum(lum, 1e-4)
            p[..., :3] = p[..., :3] * f[..., None]
            lum = (gem + (lum - gem) * CONTRAST)[..., None]
            p[..., :3] = np.clip(lum + (p[..., :3] - lum) * VERZADIG, 0, 1)
        p = dilateer(p, (0.5, 0.5, 1.0) if soort == "normaal" else p[..., :3][p[..., 3] > 0.5].mean(0))
        out = beeld("riet_kaart_" + soort, KAART_RES, data=(soort == "normaal"), alpha=(soort == "kleur"))
        if soort == "normaal":
            p[..., 3] = 1.0
        out.pixels.foreach_set(p.ravel())
        uit[soort] = bewaar(out, "riet_kaart_" + soort)
        log("studio", soort)
    bpy.data.scenes.remove(s)
    return uit["kleur"], uit["normaal"]


# --- LOD1 ---------------------------------------------------------------------------------
def lod1_bouwen(sc, RT, per_mat, stenen, kozijnen, hout_bron, adak):
    delen = []
    seg = 40
    # wand: cilinder net buiten de stenen
    R = HUT_R + 0.03
    me = lathe_np("muur", [(R, z) for z in (0.0, 0.5, 1.0, 1.5, 2.0)], seg)
    me.transform(Matrix.Translation((HX, HY, 0)))
    delen.append(me)
    # aanbouw: vier wanden
    x0, x1, y0, y1 = AX0 - 0.03, AX1 + 0.01, AY0 - 0.03, AY1 - 0.01
    vs = [(x, y, z) for z in (0.0, 1.95) for (x, y) in ((x0, y0), (x1, y0), (x1, y1), (x0, y1))]
    fs = [[0, 1, 5, 4], [1, 2, 6, 5], [2, 3, 7, 6], [3, 0, 4, 7]]
    delen.append(mesh_py("aanbouw", vs, fs, smooth=False))
    # schoorsteen
    prof = [(ch_r(z) + 0.03, z) for z in (2.6, 2.9, 3.2, 3.5, 3.8)] + [(0.47, 3.95), (0.30, 3.97), (0.27, 3.66)]
    me = lathe_np("schoorsteen", prof, 16, cap_top=True)
    me.transform(Matrix.Translation((CH[0], CH[1], 0)))
    delen.append(me)
    # koepel: schil op het halmoppervlak, zoom, terug onder de rand naar binnen
    ss = [S_END * (k / 18) ** 0.9 for k in range(19)] + [S_END + 0.05, S_END + 0.1]
    prof = [(s, 0.05) for s in ss] + [(S_END + 0.1, -0.03)]
    rings = []
    for s, off in prof:
        rings.append([dak_punt(2 * math.pi * i / 48, s, off) for i in range(48)])
    binnen = [brow(2 * math.pi * i / 48, 1.6, 2.02) for i in range(48)]
    rings.append([Vector((HX + r * math.cos(2 * math.pi * i / 48), HY + r * math.sin(2 * math.pi * i / 48), z))
                  for i, (r, z) in enumerate(binnen)])
    vs = [v for r in rings for v in r] + [Vector((HX, HY, at(PROF, 0)[2] + 0.05))]
    fs = []
    for j in range(len(rings) - 1):
        for i in range(48):
            a, b = j * 48 + i, j * 48 + (i + 1) % 48
            fs.append([a, a + 48, b + 48, b])
    top = len(vs) - 1
    fs += [[i, (i + 1) % 48, top] for i in range(48)]
    delen.append(mesh_py("koepel", vs, fs))
    # band en kuif
    me = lathe_np("band", [(0.66, 3.80), (0.66, 4.43)], 16, cap_top=True)
    me.transform(Matrix.Translation((HX, HY, 0)))
    delen.append(me)
    for k in range(7):
        if k < 6:
            a = 2 * math.pi * k / 6 + 0.3
            cx, cy, tilt = 0.40 * math.cos(a), 0.40 * math.sin(a), 0.25
        else:
            a, cx, cy, tilt = 0.0, 0.0, 0.0, 0.0
        me = lathe_np("kuif", [(0.12, 0.0), (0.26, 0.25), (0.36, 0.42)], 8, cap_top=True)
        sh = Matrix.Identity(4)
        sh[0][2], sh[1][2] = math.cos(a) * tilt, math.sin(a) * tilt
        me.transform(Matrix.Translation((HX + cx, HY + cy, 4.28)) @ sh)
        delen.append(me)
    # aanbouwdak, stijlen, hek, keien, stoepen, kozijnen: gedecimeerde kopieen
    for o, r in ([(adak, 0.3)] + [(o, 1.0) for o in hout_bron if o.name.startswith("stijl")]
                 + [(o, 0.1) for o in hout_bron if o.name.startswith("paal") and not o.name.startswith("paalkop")]
                 + [(o, 0.05) for o in hout_bron if o.name.startswith("regel") and not o.name.startswith("regelkop")]
                 + [(o, 0.35) for o in kozijnen] + [(o, 1.0) for o in per_mat["onderkant"]]):
        me = eval_mesh(o)
        if r < 1.0:
            t = obj("_l", me, RT)
            me = decimeer(me, r, RT).copy()
            bpy.data.objects.remove(t)
        delen.append(me)
    for o in stenen:
        if mat0(o) in ("rots", "stoep") and math.hypot(o.location.x - HX, o.location.y - HY) > HUT_R:
            me = decimeer(o.data, 0.012 if o.data.name.startswith("kei") else 0.04, RT, sharp=40).copy()
            me.transform(o.matrix_world)
            delen.append(me)
    o = obj("hut_lod1", samen_bm("hut_lod1", delen), RT)
    o.data.materials.clear()
    log("LOD1 hut tris", tris([o]))
    return o


# --- Vergelijk: de glb in EEVEE met de camera en het licht van de beauty -------------------
def vergelijk():
    bpy.ops.wm.open_mainfile(filepath=BLEND)
    sc = bpy.context.scene
    for o in [o for o in sc.objects if o.type in ("MESH", "CURVES")]:
        bpy.data.objects.remove(o)
    for n in ("zon_grond", "vul_grond"):
        bpy.data.objects.remove(sc.objects[n])
    for n in ("zon", "vul"):
        sc.objects[n].light_linking.receiver_collection = None
        sc.objects[n].light_linking.blocker_collection = None
    sc.render.engine = "BLENDER_EEVEE"
    sc.eevee.taa_render_samples = 64
    try:
        sc.eevee.use_raytracing = True
        sc.eevee.use_shadows = True
    except AttributeError:
        pass
    sc.render.film_transparent = True
    panelen = []
    for pad, naam in ((GLB0, "lod0"), (GLB1, "lod1")):
        before = set(sc.objects)
        bpy.ops.import_scene.gltf(filepath=pad)
        nieuw = [o for o in sc.objects if o not in before]
        sc.render.filepath = os.path.join(bpy.app.tempdir, f"_eevee_{naam}.png")
        bpy.ops.render.render(write_still=True)
        panelen.append(sc.render.filepath)
        for o in nieuw:
            bpy.data.objects.remove(o)
    beauty = os.path.join(HERE, "peasant_hut_render.png")
    rijen = []
    for p in [beauty] + panelen:
        img = bpy.data.images.load(p, check_existing=False)
        a = pixels(img)
        bpy.data.images.remove(img)
        bg = np.array([0.32, 0.36, 0.30])                # grasgroen-grijs, zoals een speelveld
        rijen.append(a[..., :3] * a[..., 3:4] + bg * (1 - a[..., 3:4]))
    h = min(r.shape[0] for r in rijen)
    out = np.concatenate([r[:h] for r in rijen], axis=1)
    img = bpy.data.images.new("vergelijk", out.shape[1], out.shape[0])
    img.pixels.foreach_set(np.concatenate([out, np.ones((*out.shape[:2], 1))], 2).astype(np.float32).ravel())
    img.filepath_raw = os.path.join(HERE, "peasant_hut_rt_vergelijk.png")
    img.file_format = "PNG"
    img.save()
    log("vergelijk ->", img.filepath_raw)


if __name__ == "__main__":
    if "alleen_vergelijk" not in OPTS:
        bouw()
    if "vergelijk" in OPTS or "alleen_vergelijk" in OPTS:
        vergelijk()
    log("KLAAR")
