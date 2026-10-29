"""Real-time bake van gereedschapsloods.blend en molen.blend voor Godot 4 (zoals
../peasant_hut_realtime.py, maar algemeen voor beide gebouwen).

Bouwt op <naam>.blend (eerst `blender -b -P <naam>.py`). De procedurele Cycles-materialen gaan niet
mee naar glTF en de halmen (hair curves) ook niet, dus:
- de objecten worden per bakgroep (materiaal["groep"]: steen, hout, pleister, ijzer, dak, doek,
  rest) samengevoegd en per object gedecimeerd tot het hele gebouw onder LOD0_MAX driehoeken zit;
- elke groep krijgt een UV-atlas, in Cycles gebakken van de echte objecten (selected-to-active):
  kleur, ORM (R = AO, G = ruwheid, B = metaal) en een tangent-normal map; de halmen worden als
  buisjes op de rieten schil gebakken;
- wat onder een scharnier hangt (`deur`, `deur_gevel`, `wieken`) blijft een eigen object onder dat
  lege object, zodat het in Godot kan draaien;
- LOD1 is een losse glb van de proxies uit het bouwscript (`lod1`), op een eigen atlas.

Draaien (headless):
  blender -b -P loods_molen_rt.py -- naam=molen [res=2048] [snel] [vergelijk] [alleen_vergelijk]
Schrijft <naam>_rt.glb, <naam>_rt_lod1.glb en rt_textures/<naam>_*; `vergelijk` rendert de glb's in
EEVEE naast de Cycles-beauty: preview/<naam>_rt_vergelijk.png.
"""
import math
import os
import random
import sys
import time
from collections import defaultdict

import bmesh
import bpy
import numpy as np
from mathutils import Vector

HERE = os.path.dirname(os.path.abspath(__file__))
argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
OPTS = {a.split("=")[0]: (a.split("=", 1)[1] if "=" in a else "1") for a in argv}
NAAM = OPTS.get("naam", "molen")
BLEND = os.path.join(HERE, f"{NAAM}.blend")
TEXDIR = os.path.join(HERE, "rt_textures")
GLB0 = os.path.join(HERE, f"{NAAM}_rt.glb")
GLB1 = os.path.join(HERE, f"{NAAM}_rt_lod1.glb")
SNEL = "snel" in OPTS
RES = int(OPTS.get("res", 512 if SNEL else 2048))
ORM_RES = RES // 2
LOD1_RES = RES // 2
SPP = 0.25 if SNEL else 1.0
LOD0_MAX = 76000                       # budget ~80k
KLEIN = 28                             # objecten tot zoveel driehoeken (een doos) blijven heel
SCHARNIEREN = ("deur", "deur_gevel", "wieken")
# gewicht per groep bij het decimeren: dak blijft heel (silhouet), losse stenen mogen het meest kwijt
WEEG = {"dak": None, "steen": 0.55}
# kooi (extrusie) en straal per groep: hoe ver de hoge bron van de lage kan liggen
KOOI = {"dak": (0.16, 0.3), "steen": (0.04, 0.1)}
KOOI_STD = (0.025, 0.08)
T0 = time.time()


def log(*a):
    print(f"[rt {time.time() - T0:6.1f}s]", *a, flush=True)


# --- Hulpjes (uit peasant_hut_realtime.py) -----------------------------------------------
def gpu(scene):
    p = bpy.context.preferences.addons["cycles"].preferences
    try:
        p.compute_device_type = "CUDA"               # OptiX faalt op deze driver
    except TypeError:
        return "CPU"
    p.get_devices()
    for d in p.devices:
        d.use = d.type == "CUDA"
    scene.cycles.device = "GPU"
    return "CUDA"


def mat0(o):
    return o.material_slots[0].material if o.material_slots and o.material_slots[0].material else None


def groep_van(o):
    m = mat0(o)
    return m.get("groep", "rest") if m else "rest"


def ontkies():
    bpy.context.view_layer.update()
    for o in bpy.context.view_layer.objects:
        if o is not None:
            o.select_set(False)


def mesh_np(name, V, F, smooth=True):
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


def eval_mesh(ob, name=None):
    dg = bpy.context.evaluated_depsgraph_get()
    me = bpy.data.meshes.new_from_object(ob.evaluated_get(dg), preserve_all_data_layers=False, depsgraph=dg)
    me.transform(ob.matrix_world)
    me.name = name or ob.name + "_rt"
    return me


def obj(name, me, coll):
    o = bpy.data.objects.new(name, me)
    coll.objects.link(o)
    return o


def ntris(me):
    me.calc_loop_triangles()
    return len(me.loop_triangles)


def decimeer_me(me, ratio, coll):
    o = obj("_dec", me, coll)
    m = o.modifiers.new("d", "DECIMATE")
    m.ratio = ratio
    m.use_collapse_triangulate = True
    dg = bpy.context.evaluated_depsgraph_get()
    out = bpy.data.meshes.new_from_object(o.evaluated_get(dg), depsgraph=dg)
    bpy.data.objects.remove(o)
    out.set_sharp_from_angle(angle=math.radians(50))
    return out


def samen_bm(name, meshes, mats=()):
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
    ontkies()
    for o in objs:
        o.select_set(True)
    bpy.context.view_layer.objects.active = objs[0]
    bpy.ops.object.join()
    o = bpy.context.view_layer.objects.active
    o.name = name
    o.data.name = name
    return o


def box_mesh(name, lo, hi):
    (x0, y0, z0), (x1, y1, z1) = lo, hi
    vs = [(x, y, z) for z in (z0, z1) for y in (y0, y1) for x in (x0, x1)]
    fs = [[0, 2, 3, 1], [4, 5, 7, 6], [0, 1, 5, 4], [2, 6, 7, 3], [0, 4, 6, 2], [1, 3, 7, 5]]
    me = bpy.data.meshes.new(name)
    me.from_pydata(vs, [], fs)
    me.update()
    return me


def buizen(name, krommen, stralen, per_kromme, sides=4):
    """Hair curves -> buisjes met 'hint' (0..1 langs de halm) en per-kromme attributen."""
    groep = defaultdict(list)
    for i, c in enumerate(krommen):
        groep[len(c)].append(i)
    th = np.linspace(0, 2 * np.pi, sides, endpoint=False)
    cs, sn = np.cos(th), np.sin(th)
    V, F, HI = [], [], []
    PF = {k: [] for k in per_kromme}
    off = 0
    for n, idx in groep.items():
        P = np.array([krommen[i] for i in idx], np.float64)
        R = np.array([stralen[i] for i in idx], np.float64)
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
    return [pos[offs[i]:offs[i + 1]] for i in range(nc)], [rad[offs[i]:offs[i + 1]] for i in range(nc)], bos


def mat_attr(src):
    """Halmmateriaal voor buisjes: Hair Info (Random, Intercept) -> attributen hrand, hint."""
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
    """Kopie waarin Object/Generated-coordinaten en Object Info > Random uit attributen komen."""
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
    for n in list(nt.nodes):
        if n.type.startswith("TEX_") and n.type not in ("TEX_COORD", "TEX_IMAGE", "TEX_ENVIRONMENT"):
            v = n.inputs.get("Vector")
            if v is not None and not v.is_linked:
                nt.links.new(a("o_gen").outputs["Vector"], v)
    cache[src.name] = m
    return m


_ZCACHE = {}


def zelfstandig(naam, objs, coll):
    """Bronobjecten samengevoegd tot een mesh met de per-object invoer als attributen."""
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
    for me, idx in delen:
        me.materials.clear()
        for m in mats:
            me.materials.append(m)
        me.polygons.foreach_set("material_index", idx)
    delen = [d for d, _ in delen]
    me = samen_bm(naam, delen, mats)
    for d in delen:
        bpy.data.meshes.remove(d)
    log("  bron", naam, len(objs), "objecten", len(me.polygons), "vlakken")
    return obj(naam, me, coll)


def uv_atlas(objs, marge=0.003):
    for o in objs:
        while o.data.uv_layers:
            o.data.uv_layers.remove(o.data.uv_layers[0])
        o.data.uv_layers.new(name="UVMap")
    ontkies()
    for o in objs:
        o.select_set(True)
    bpy.context.view_layer.objects.active = objs[0]
    bpy.context.scene.tool_settings.use_uv_select_sync = True
    bpy.ops.object.mode_set(mode="EDIT")
    bpy.ops.mesh.select_all(action="SELECT")
    bpy.ops.uv.smart_project(angle_limit=math.radians(50), island_margin=0.0, area_weight=0.0,
                             correct_aspect=True, scale_to_bounds=False)
    bpy.ops.uv.average_islands_scale()
    bpy.ops.uv.pack_islands(rotate=True, margin=marge, shape_method="CONCAVE")
    bpy.ops.object.mode_set(mode="OBJECT")


def beeld(naam, w, data=False):
    img = bpy.data.images.new(naam, w, w)
    if data:
        img.colorspace_settings.name = "Non-Color"
    return img


BAKSOORT = {"kleur": ("DIFFUSE", {"COLOR"}, 16), "ruwheid": ("ROUGHNESS", set(), 4),
            "normaal": ("NORMAL", set(), 16), "ao": ("AO", set(), 96)}


def bak(lows, highs, beelden, ext, ray, coll, margin=6):
    """Bak highs -> een tijdelijke samengevoegde kopie van lows (zelfde UV)."""
    sc = bpy.context.scene
    kop = []
    for o in lows:
        k = o.copy()
        k.data = o.data.copy()
        k.parent = None
        k.matrix_world = o.matrix_world
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
    for v in ("visible_diffuse", "visible_glossy", "visible_shadow", "visible_transmission", "visible_volume_scatter"):
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
        log("  bak", img.name, f"{time.time() - t1:.1f}s")
    for o in verborgen:
        o.hide_render = False
    bpy.data.objects.remove(doel)
    bpy.data.materials.remove(m)


def pixels(img):
    a = np.zeros(img.size[0] * img.size[1] * 4, np.float32)
    img.pixels.foreach_get(a)
    return a.reshape(img.size[1], img.size[0], 4)


def bewaar(img, naam, jpg=False):
    pad = os.path.join(TEXDIR, naam + (".jpg" if jpg else ".png"))
    img.filepath_raw = pad
    img.file_format = "JPEG" if jpg else "PNG"
    if jpg:
        bpy.context.scene.render.image_settings.quality = 92
    img.save(filepath=pad, quality=92) if jpg else img.save(filepath=pad)
    data = img.colorspace_settings.name == "Non-Color"
    bpy.data.images.remove(img)
    out = bpy.data.images.load(pad, check_existing=False)
    out.name = naam
    if data:
        out.colorspace_settings.name = "Non-Color"
    return out


def orm(ao, ruw, naam, metaal=0.0):
    a, r = pixels(ao), pixels(ruw)
    out = beeld(naam, ao.size[0], data=True)
    p = np.ones_like(a)
    p[..., 0] = a[..., 0]
    p[..., 1] = r[..., 0]
    p[..., 2] = metaal
    out.pixels.foreach_set(p.ravel())
    return out


GLTF_GROEP = None


def gltf_groep():
    global GLTF_GROEP
    if GLTF_GROEP is None:
        GLTF_GROEP = bpy.data.node_groups.new("glTF Material Output", "ShaderNodeTree")
        GLTF_GROEP.interface.new_socket("Occlusion", in_out="INPUT", socket_type="NodeSocketFloat")
    return GLTF_GROEP


def pbr(naam, kleur, nrm, orm_img, tweezijdig=False):
    m = bpy.data.materials.new(naam)
    m.use_nodes = True
    nt = m.node_tree
    b = nt.nodes["Principled BSDF"]
    b.inputs["Specular IOR Level"].default_value = 0.3
    t = nt.nodes.new("ShaderNodeTexImage")
    t.image = kleur
    nt.links.new(t.outputs["Color"], b.inputs["Base Color"])
    tn = nt.nodes.new("ShaderNodeTexImage")
    tn.image = nrm
    nm = nt.nodes.new("ShaderNodeNormalMap")
    nt.links.new(tn.outputs["Color"], nm.inputs["Color"])
    nt.links.new(nm.outputs["Normal"], b.inputs["Normal"])
    to = nt.nodes.new("ShaderNodeTexImage")
    to.image = orm_img
    sp = nt.nodes.new("ShaderNodeSeparateColor")
    nt.links.new(to.outputs["Color"], sp.inputs["Color"])
    nt.links.new(sp.outputs["Green"], b.inputs["Roughness"])
    nt.links.new(sp.outputs["Blue"], b.inputs["Metallic"])
    g = nt.nodes.new("ShaderNodeGroup")
    g.node_tree = gltf_groep()
    nt.links.new(sp.outputs["Red"], g.inputs["Occlusion"])
    m.use_backface_culling = not tweezijdig
    return m


def zet_mat(o, m):
    o.data.materials.clear()
    o.data.materials.append(m)


def tris(objs):
    return sum(ntris(o.data) for o in objs)


def exporteer(pad, objs):
    ontkies()
    for o in objs:
        o.select_set(True)
    bpy.ops.export_scene.gltf(filepath=pad, export_format="GLB", use_selection=True, export_apply=True,
                              export_tangents=True, export_image_format="AUTO", export_cameras=False,
                              export_lights=False, export_extras=False, export_animations=False)
    log("export", os.path.basename(pad), f"{os.path.getsize(pad) / 1e6:.1f} MB")


def scharnier_van(o):
    p = o.parent
    while p is not None:
        if p.type == "EMPTY" and p.name in SCHARNIEREN:
            return p
        p = p.parent
    return None


# --- Bouwen --------------------------------------------------------------------------------------
def bouw():
    bpy.ops.wm.open_mainfile(filepath=BLEND)
    sc = bpy.context.scene
    log("blend geopend; GPU:", gpu(sc))
    sc.render.engine = "CYCLES"
    sc.cycles.use_denoising = False
    sc.world.light_settings.distance = 0.35
    os.makedirs(TEXDIR, exist_ok=True)
    RT = bpy.data.collections.new("RT")
    sc.collection.children.link(RT)
    ORIG = [o for o in sc.objects if o.type == "MESH" and not o.get("lod1") and o.name != "vanger"]
    PROXY = [o for o in sc.objects if o.type == "MESH" and o.get("lod1")]
    HAAR = [o for o in sc.objects if o.type == "CURVES"]

    # halmen -> buisjes (hoge bron voor de dakgroep)
    BUIS = []
    for ob in HAAR:
        kr, st, bos = halmen_van(ob)
        rnd = np.random.default_rng(len(kr))
        me = buizen(ob.name + "_buis", kr, st, {"bos": bos, "hrand": rnd.random(len(kr))})
        me.materials.append(mat_attr(ob.data.materials[0]))
        BUIS.append(obj(ob.name + "_buis", me, sc.collection))
        ob.hide_render = True
        log("halmen", ob.name, len(kr), "->", len(me.polygons), "quads")

    # ---------------------------------------------------------------- LOD0: decimeren per object
    per = defaultdict(list)                           # (groep, scharnier) -> objecten
    for o in ORIG:
        piv = scharnier_van(o)
        per[(groep_van(o), piv.name if piv else "")].append(o)
    bron_tris = {}
    for o in ORIG:
        key = o.data.name if not o.modifiers else o.name
        if key not in bron_tris:
            me = eval_mesh(o, "_t")
            bron_tris[key] = ntris(me)
            bpy.data.meshes.remove(me)
    tel = lambda o: bron_tris[o.data.name if not o.modifiers else o.name]

    def doel(n, k, g="rest"):
        w = WEEG.get(g, 1.0)
        if w is None or n <= KLEIN:
            return n
        return KLEIN + (n - KLEIN) * min(1.0, k * w)
    lo_k, hi_k = 0.0, 1.0
    if sum(tel(o) for o in ORIG) > LOD0_MAX:
        for _ in range(30):
            k = (lo_k + hi_k) / 2
            if sum(doel(tel(o), k, groep_van(o)) for o in ORIG) > LOD0_MAX:
                hi_k = k
            else:
                lo_k = k
    K = lo_k
    log("bron", len(ORIG), "objecten,", sum(tel(o) for o in ORIG), "driehoeken; k =", round(K, 4))
    dec_cache = {}
    LOW = {}
    for (g, piv), objs in per.items():
        delen = []
        for o in objs:
            n = tel(o)
            ratio = doel(n, K, g) / n
            if ratio >= 0.999:
                delen.append(eval_mesh(o))
                continue
            key = (o.data.name, round(ratio, 4)) if not o.modifiers else None
            if key and key in dec_cache:
                me = dec_cache[key].copy()
                me.transform(o.matrix_world)
            else:
                lok = eval_mesh(o)
                lok.transform(o.matrix_world.inverted())
                me0 = decimeer_me(lok, ratio, RT)
                bpy.data.meshes.remove(lok)
                if key:
                    dec_cache[key] = me0
                me = me0.copy()
                me.transform(o.matrix_world)
            delen.append(me)
        naam = f"{g}_{piv}" if piv else g
        me = samen_bm(naam, delen)
        for d in delen:
            bpy.data.meshes.remove(d)
        me.materials.clear()
        LOW[(g, piv)] = obj(naam + "_rt", me, RT)
        log("laag", naam, len(objs), "objecten ->", tris([LOW[(g, piv)]]), "driehoeken")
    log("LOD0 totaal", tris(list(LOW.values())))

    # ---------------------------------------------------------------- LOD1: proxies
    L1 = {}
    per1 = defaultdict(list)
    for o in PROXY:
        piv = scharnier_van(o)
        per1[piv.name if piv else ""].append(o)
    for pivn in SCHARNIEREN:                           # scharnier zonder proxy: doos om de delen
        e = sc.objects.get(pivn)
        if e and pivn not in per1 and pivn != "wieken":
            M = e.matrix_world.copy()
            Mi = M.inverted()
            kids = [k for k in ORIG if scharnier_van(k) is e]
            pts = [Mi @ (k.matrix_world @ Vector(c)) for k in kids for c in k.bound_box]
            lo = Vector([min(p[i] for p in pts) for i in range(3)])
            hi = Vector([max(p[i] for p in pts) for i in range(3)])
            me = box_mesh(pivn + "_l1", lo, hi)
            me.transform(M)
            L1[pivn] = obj(pivn + "_lod1", me, RT)
    for pivn, objs in per1.items():
        me = samen_bm("l1", [eval_mesh(o) for o in objs])
        me.materials.clear()
        L1[pivn] = obj((pivn or NAAM) + "_lod1", me, RT)
    log("LOD1 totaal", tris(list(L1.values())))

    # ---------------------------------------------------------------- bronnen en bakken
    Z = {}
    for g in sorted({g for g, _ in per}):
        Z[g] = zelfstandig("_z_" + g, [o for (gg, _), objs in per.items() if gg == g for o in objs], RT)
    for o in ORIG + PROXY:
        o.hide_render = True
    for o in Z.values():
        o.hide_render = True
    for o in BUIS:
        o.hide_render = True
    alle_z = list(Z.values())
    MAT = {}
    groepen = [(g, [LOW[k] for k in LOW if k[0] == g]) for g in Z] + [("lod1", list(L1.values()))]
    for g, lows in groepen:
        t1 = time.time()
        highs = (alle_z + BUIS) if g == "lod1" else ([Z[g]] + (BUIS if g == "dak" else []))
        ext, ray = (0.14, 0.4) if g == "lod1" else KOOI.get(g, KOOI_STD)
        uv_atlas(lows)
        res, ores = (LOD1_RES, LOD1_RES // 2) if g == "lod1" else (RES, ORM_RES)
        if g not in ("lod1", "dak", "steen", "hout"):          # kleine groepen: kleinere atlas
            res, ores = res // 2, ores // 2
        kl, nr = beeld(f"{NAAM}_{g}_kleur", res), beeld(f"{NAAM}_{g}_normaal", res, data=True)
        ao, ru = beeld(f"{NAAM}_{g}_ao", ores, data=True), beeld(f"{NAAM}_{g}_ruw", ores, data=True)
        for o in alle_z + BUIS:                        # AO ziet het hele gebouw
            o.hide_render = False
        # metaal: de diffuse kleur van metaal is zwart; even zonder metaal bakken
        metaal = {}
        for o in highs:
            for ms in o.data.materials:
                if ms and ms.node_tree and "Principled BSDF" in ms.node_tree.nodes:
                    inp = ms.node_tree.nodes["Principled BSDF"].inputs["Metallic"]
                    if not inp.is_linked and inp.default_value > 0:
                        metaal[ms.name] = inp.default_value
                        inp.default_value = 0.0
        bak(lows, highs, [("kleur", kl), ("normaal", nr)], ext, ray, RT)
        for naam, v in metaal.items():
            bpy.data.materials[naam].node_tree.nodes["Principled BSDF"].inputs["Metallic"].default_value = v
        bak(lows, highs, [("ao", ao), ("ruwheid", ru)], ext, ray, RT, margin=3)
        for o in alle_z + BUIS:
            o.hide_render = True
        mv = 0.9 if g == "ijzer" else 0.0
        o_img = bewaar(orm(ao, ru, f"{NAAM}_{g}_orm", mv), f"{NAAM}_{g}_orm")
        bpy.data.images.remove(ao)
        bpy.data.images.remove(ru)
        MAT[g] = pbr(f"{NAAM}_{g}", bewaar(kl, f"{NAAM}_{g}_kleur", jpg=True), bewaar(nr, f"{NAAM}_{g}_normaal"),
                     o_img, tweezijdig=g in ("doek", "rest", "dak"))
        for o in lows:
            zet_mat(o, MAT[g])
        log("groep", g, f"{time.time() - t1:.0f}s")

    # ---------------------------------------------------------------- opruimen, ophangen, export
    for o in [o for o in sc.objects if o.type in ("MESH", "CURVES", "LIGHT", "CAMERA") and o.users_collection[0] is not RT]:
        bpy.data.objects.remove(o)
    for o in Z.values():
        if o.name in bpy.data.objects:
            bpy.data.objects.remove(o)
    bpy.data.orphans_purge(do_recursive=True)
    for (g, piv), o in LOW.items():
        o.name = o.data.name = (f"{g}_{piv}" if piv else g)
        if piv:
            e = sc.objects[piv]
            o.parent = e
            o.matrix_parent_inverse = e.matrix_world.inverted()
    for pivn, o in L1.items():
        if pivn:
            e = sc.objects[pivn]
            o.parent = e
            o.matrix_parent_inverse = e.matrix_world.inverted()
    ANKERS = [o for o in sc.objects if o.type == "EMPTY"]
    lod0, lod1 = list(LOW.values()), list(L1.values())
    log("LOD0 tris", tris(lod0), "LOD1 tris", tris(lod1))
    for o in lod0 + lod1:
        log("   ", o.name, tris([o]))
    exporteer(GLB0, lod0 + ANKERS)
    exporteer(GLB1, lod1 + ANKERS)
    bpy.ops.wm.save_as_mainfile(filepath=os.path.join(HERE, f"{NAAM}_rt.blend"), compress=True)


# --- Vergelijk: de glb's in EEVEE met de camera en het licht van de beauty -------------------------
def vergelijk():
    bpy.ops.wm.open_mainfile(filepath=BLEND)
    sc = bpy.context.scene
    for o in [o for o in sc.objects if o.type in ("MESH", "CURVES") and o.name != "vanger"]:
        bpy.data.objects.remove(o)
    sc.objects["vanger"].hide_render = True
    sc.render.engine = "BLENDER_EEVEE"
    sc.eevee.taa_render_samples = 64
    try:
        sc.eevee.use_raytracing = True
    except AttributeError:
        pass
    sc.render.film_transparent = True
    panelen = []
    for pad, naam in ((GLB0, "lod0"), (GLB1, "lod1")):
        before = set(sc.objects)
        bpy.ops.import_scene.gltf(filepath=pad)
        nieuw = [o for o in sc.objects if o not in before]
        sc.render.filepath = os.path.join(bpy.app.tempdir, f"_eevee_{NAAM}_{naam}.png")
        bpy.ops.render.render(write_still=True)
        panelen.append(sc.render.filepath)
        for o in nieuw:
            bpy.data.objects.remove(o)
    rijen = []
    for p in [os.path.join(HERE, "preview", f"{NAAM}_render.png")] + panelen:
        img = bpy.data.images.load(p, check_existing=False)
        a = pixels(img)
        bpy.data.images.remove(img)
        bg = np.array([0.32, 0.36, 0.30])
        rijen.append(a[..., :3] * a[..., 3:4] + bg * (1 - a[..., 3:4]))
    h = min(r.shape[0] for r in rijen)
    out = np.concatenate([r[:h] for r in rijen], axis=1)
    img = bpy.data.images.new("vergelijk", out.shape[1], out.shape[0])
    img.pixels.foreach_set(np.concatenate([out, np.ones((*out.shape[:2], 1))], 2).astype(np.float32).ravel())
    img.filepath_raw = os.path.join(HERE, "preview", f"{NAAM}_rt_vergelijk.png")
    img.file_format = "PNG"
    img.save()
    log("vergelijk ->", img.filepath_raw)


if __name__ == "__main__":
    if "alleen_vergelijk" not in OPTS:
        bouw()
    if "vergelijk" in OPTS or "alleen_vergelijk" in OPTS:
        vergelijk()
    log("KLAAR")
