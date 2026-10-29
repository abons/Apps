"""Gedeelde hulpjes voor de natuur- en propsmodellen (Blender 5.2, headless).

- Bouwer: geometrie in Python-lijsten (per hoek UV, per hoekpunt kleur en normaal) -> bpy-mesh.
- Wind als tweede UV-laag `wind` (glTF TEXCOORD_1, Godot UV2): u = zwaai van de stam (0 voet .. 1 top),
  v = trilling (0 aanhechting .. 0,999 punt) + floor(fase * 8), fase per tak. Niet als COLOR_0: glTF
  (en Godot) vermenigvuldigt COLOR_0 met de basiskleur. Intern blijft het kleurattribuut `wind`
  (R zwaai, G trilling, B fase) voor de studio; dat wordt niet geexporteerd.
- Materialen: tegelbare Poly Haven-sets (UV in meters), kaartmaterialen (atlas, MASK),
  vlakke kleuren; ORM wordt hier gemaakt (R = 1, G = ruwheid, B = metaal).
- Studio: bovenaanzicht-renders in modi (kleur, normaal, ruw) voor kaarten en terrein.
- Bakken (selected-to-active) zoals in peasant_hut_realtime.py.
- Export naar glb (wind als TEXCOORD_1) en een iso-voorvertoning (yaw 225, pitch 30, ortho).
"""
import math
import os
import random
import sys
import time

import bmesh
import bpy
import numpy as np
from mathutils import Matrix, Vector

HERE = os.path.dirname(os.path.abspath(__file__))
TEX = os.path.join(os.path.dirname(HERE), "textures")          # Poly Haven-bronnen
NTEX = os.path.join(HERE, "textures")                           # gegenereerd (atlas, terrein, orm)
PREV = os.path.join(HERE, "preview")
STUDIO = os.environ.get("NATUUR_TMP") or os.path.join(HERE, "_studio")   # tussenbeelden
for d in (NTEX, PREV, STUDIO):
    os.makedirs(d, exist_ok=True)
argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
OPTS = {a.split("=")[0]: (a.split("=", 1)[1] if "=" in a else "1") for a in argv}
T0 = time.time()


def log(*a):
    print(f"[natuur {time.time() - T0:6.1f}s]", *a, flush=True)


# --- Scene -----------------------------------------------------------------------------
def leeg():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    global GLTF_GROEP
    STUDIO_MATS.clear()
    GLTF_GROEP = None
    sc = bpy.context.scene
    sc.unit_settings.system = "METRIC"
    return sc


def gpu(sc):
    p = bpy.context.preferences.addons["cycles"].preferences
    for t in ("CUDA",):                        # OptiX faalt op deze driver
        try:
            p.compute_device_type = t
        except TypeError:
            continue
        p.get_devices()
        if any(d.type == t for d in p.devices):
            for d in p.devices:
                d.use = d.type == t
            sc.cycles.device = "GPU"
            return t
    return "CPU"


def coll(naam):
    c = bpy.data.collections.new(naam)
    bpy.context.scene.collection.children.link(c)
    return c


def ontkies():
    bpy.context.view_layer.update()
    for o in bpy.context.view_layer.objects:
        if o is not None:
            o.select_set(False)


# --- Bouwer ----------------------------------------------------------------------------
class Bouwer:
    """Vlakken met per-hoek UV; hoekpunten met wind-kleur en optionele eigen normaal."""

    def __init__(self):
        self.V, self.C, self.N = [], [], []
        self.F, self.UV, self.M = [], [], []

    def v(self, co, col=(0, 0, 0, 1), n=None):
        self.V.append(tuple(co))
        self.C.append(tuple(col) if len(col) == 4 else (*col, 1.0))
        self.N.append(None if n is None else tuple(n))
        return len(self.V) - 1

    def f(self, idx, uv, mat=0):
        self.F.append(list(idx))
        self.UV.append([tuple(u) for u in uv])
        self.M.append(mat)

    def voeg(self, b):
        o = len(self.V)
        self.V += b.V
        self.C += b.C
        self.N += b.N
        self.F += [[i + o for i in f] for f in b.F]
        self.UV += b.UV
        self.M += b.M

    def ntris(self):
        return sum(len(f) - 2 for f in self.F)

    def mesh(self, naam, mats=(), smooth=True):
        me = bpy.data.meshes.new(naam)
        me.from_pydata(self.V, [], self.F)
        me.update()
        for m in mats:
            me.materials.append(m)
        if self.F:
            me.polygons.foreach_set("material_index", np.array(self.M, np.int32))
            uvl = me.uv_layers.new(name="UVMap")
            uvs = np.array([u for f in self.UV for u in f], np.float32)
            uvl.data.foreach_set("uv", uvs.ravel())
            # wind als tweede UV (TEXCOORD_1): u = zwaai, v = trilling (0..0,999) + floor(fase * 8)
            C = np.array(self.C, np.float32)
            lp = np.array([i for f in self.F for i in f], np.int64)
            w = np.stack([C[lp, 0], np.minimum(C[lp, 1], 0.999) + np.floor(np.minimum(C[lp, 2], 0.999) * 8)], 1)
            uv2 = me.uv_layers.new(name="wind")
            uv2.data.foreach_set("uv", w.astype(np.float32).ravel())
            me.uv_layers.active = uvl
            uvl.active_render = True
        ca = me.color_attributes.new("wind", "FLOAT_COLOR", "POINT")
        ca.data.foreach_set("color", np.array(self.C, np.float32).ravel())
        me.color_attributes.active_color_name = "wind"
        if smooth:
            me.shade_smooth()
        if any(n is not None for n in self.N):
            vn = [Vector(n).normalized() if n is not None else None for n in self.N]
            me.update()
            eig = [tuple(vn[i]) if vn[i] is not None else tuple(me.vertices[i].normal) for i in range(len(vn))]
            me.normals_split_custom_set_from_vertices(eig)
        me.update()
        return me


def obj(naam, me, c=None):
    o = bpy.data.objects.new(naam, me)
    (c or bpy.context.scene.collection).objects.link(o)
    return o


def frame(d):
    """Twee loodrechte assen bij richting d."""
    d = Vector(d).normalized()
    a = Vector((0, 0, 1)) if abs(d.z) < 0.95 else Vector((1, 0, 0))
    x = d.cross(a).normalized()
    y = d.cross(x).normalized()
    return x, y


def buis(b, P, R, zijden=6, col=None, uvschaal=1.0, dop=False, straal_fn=None, mat=0, u_rep=None):
    """Buis langs P (lijst Vector) met stralen R. col(i, t) -> wind-kleur; straal_fn(i, hoek) -> factor.
    UV: u = omtrek (m) * uvschaal, v = booglengte (m) * uvschaal; naad gedupliceerd."""
    n = len(P)
    T = []
    for i in range(n):
        if i == 0:
            t = P[1] - P[0]
        elif i == n - 1:
            t = P[-1] - P[-2]
        else:
            t = P[i + 1] - P[i - 1]
        T.append(t.normalized())
    x, y = frame(T[0])
    ringen, s = [], 0.0
    for i in range(n):
        if i > 0:
            s += (P[i] - P[i - 1]).length
            # parallel transport
            ax = T[i - 1].cross(T[i])
            if ax.length > 1e-6:
                ang = T[i - 1].angle(T[i])
                rot = Matrix.Rotation(ang, 3, ax.normalized())
                x, y = rot @ x, rot @ y
        omtrek = 2 * math.pi * R[i] if u_rep is None else u_rep
        ring = []
        for k in range(zijden + 1):
            a = 2 * math.pi * k / zijden
            f = straal_fn(i, a) if straal_fn else 1.0
            nrm = x * math.cos(a) + y * math.sin(a)
            p = P[i] + nrm * R[i] * f
            c = col(i, s) if col else (0, 0, 0, 1)
            ring.append((b.v(p, c), k / zijden * omtrek * uvschaal, s * uvschaal))
        ringen.append(ring)
    for i in range(n - 1):
        r0, r1 = ringen[i], ringen[i + 1]
        for k in range(zijden):
            a, bb, c, d = r0[k], r0[k + 1], r1[k + 1], r1[k]
            b.f([a[0], bb[0], c[0], d[0]], [(a[1], a[2]), (bb[1], bb[2]), (c[1], c[2]), (d[1], d[2])], mat)
    if dop:
        r = ringen[-1]
        c = col(n - 1, s) if col else (0, 0, 0, 1)
        m = b.v(P[-1] + T[-1] * R[-1] * 0.3, c)
        for k in range(zijden):
            b.f([r[k][0], r[k + 1][0], m], [(0, 0), (0.1, 0), (0.05, 0.1)], mat)
    return ringen


def kaart(b, p0, d, w, L, W, uv, col0, col1, buig=0.0, seg=2, nrm=None, mat=0, smal_tip=1.0):
    """Alfakaart vanaf aanhechting p0 langs d (lengte L), breedte W langs w; uv = (u0, v0, u1, v1)
    met v0 bij de aanhechting. buig: doorzakking van de punt (m, langs -z). col0/col1: wind aan
    voet/punt. nrm: eigen normaal (functie van positie) of None."""
    d, w = Vector(d).normalized(), Vector(w).normalized()
    if nrm is not None and w.cross(d).dot(nrm(p0)) < 0:
        w = -w                                  # vlak (en raaklijnruimte) aan de kant van de eigen normaal
    u0, v0, u1, v1 = uv
    rij = []
    for j in range(seg + 1):
        t = j / seg
        c = p0 + d * (L * t) + Vector((0, 0, -buig * t * t))
        ww = W * (1 - (1 - smal_tip) * t)
        cc = tuple(col0[i] + (col1[i] - col0[i]) * t for i in range(4))
        vv = v0 + (v1 - v0) * t
        pa, pb = c - w * ww / 2, c + w * ww / 2
        du = (u1 - u0) * (1 - (1 - smal_tip) * t) / 2
        um = (u0 + u1) / 2
        rij.append((b.v(pa, cc, nrm(pa) if nrm else None), b.v(pb, cc, nrm(pb) if nrm else None),
                    (um - du, vv), (um + du, vv)))
    for j in range(seg):
        a, c = rij[j], rij[j + 1]
        b.f([a[0], a[1], c[1], c[0]], [a[2], a[3], c[3], c[2]], mat)


def doos(b, lo, hi, mat=0, col=(0, 0, 0, 1), uvschaal=1.0):
    """As-uitgelijnde doos met UV per vlak in meters."""
    x0, y0, z0 = lo
    x1, y1, z1 = hi
    P = [(x0, y0, z0), (x1, y0, z0), (x1, y1, z0), (x0, y1, z0), (x0, y0, z1), (x1, y0, z1), (x1, y1, z1), (x0, y1, z1)]
    F = [(0, 3, 2, 1), (4, 5, 6, 7), (0, 1, 5, 4), (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7)]
    for f in F:
        q = [Vector(P[i]) for i in f]
        n = (q[1] - q[0]).cross(q[2] - q[0]).normalized()
        ax = max(range(3), key=lambda k: abs(n[k]))
        uu, vv = [(1, 2), (0, 2), (0, 1)][ax]
        idx = [b.v(P[i], col) for i in f]
        b.f(idx, [(P[i][uu] * uvschaal, P[i][vv] * uvschaal) for i in f], mat)


# --- bmesh-vormen --------------------------------------------------------------------------
def bm_naar_bouwer(bm, b, mat=0, col=(0, 0, 0, 1), uvschaal=1.0, M=None):
    """bmesh -> Bouwer, met box-UV in meters (per vlak de dominante as)."""
    base = len(b.V)
    M = M or Matrix()
    co = [M @ v.co for v in bm.verts]
    for p in co:
        b.v(p, col)
    for f in bm.faces:
        n = (M.to_3x3() @ f.normal)
        ax = max(range(3), key=lambda k: abs(n[k]))
        uu, vv = [(1, 2), (0, 2), (0, 1)][ax]
        idx = [v.index for v in f.verts]
        b.f([base + i for i in idx], [(co[i][uu] * uvschaal, co[i][vv] * uvschaal) for i in idx], mat)


def blok(maat, afkant=0.02, seg=1):
    """Afgekante doos (bmesh), middelpunt in de oorsprong."""
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0)
    bmesh.ops.scale(bm, vec=Vector(maat), verts=bm.verts)
    if afkant > 0:
        bmesh.ops.bevel(bm, geom=list(bm.edges), offset=afkant, segments=seg, affect="EDGES", profile=0.6)
    bm.verts.index_update()
    bm.faces.index_update()
    return bm


# --- Materialen ------------------------------------------------------------------------
GLTF_GROEP = None


def gltf_groep():
    global GLTF_GROEP
    if GLTF_GROEP is None:
        GLTF_GROEP = bpy.data.node_groups.new("glTF Material Output", "ShaderNodeTree")
        GLTF_GROEP.interface.new_socket("Occlusion", in_out="INPUT", socket_type="NodeSocketFloat")
    return GLTF_GROEP


def laad(pad, data=False):
    img = bpy.data.images.load(pad, check_existing=True)
    if data:
        img.colorspace_settings.name = "Non-Color"
    return img


def orm_van(naam, metaal=0.0, ao=None, ruw_schaal=1.0, ruw_plus=0.0):
    """ORM-jpg uit een Poly Haven-ruwheidsmap (R = AO of 1, G = ruwheid, B = metaal)."""
    uit = os.path.join(NTEX, f"{naam}_orm.jpg")
    if not os.path.exists(uit):
        r = laad(os.path.join(TEX, f"{naam}_rough_1k.jpg"), data=True)
        w, h = r.size
        a = np.zeros(w * h * 4, np.float32)
        r.pixels.foreach_get(a)
        a = a.reshape(h, w, 4)
        o = np.ones_like(a)
        o[..., 1] = np.clip(a[..., 0] * ruw_schaal + ruw_plus, 0, 1)
        o[..., 2] = metaal
        img = bpy.data.images.new(naam + "_orm", w, h)
        img.colorspace_settings.name = "Non-Color"
        img.pixels.foreach_set(o.ravel())
        img.filepath_raw = uit
        img.file_format = "JPEG"
        bpy.context.scene.render.image_settings.quality = 90
        img.save()
        bpy.data.images.remove(img)
    return laad(uit, data=True)


def pbr(naam, kleur, nrm=None, orm=None, alpha=False, tweezijdig=False, ruw=0.8, factor=None,
        metaal=0.0, emissie=None, emissie_kracht=0.0, blend=False, alfa_waarde=None):
    """Principled met beeldtexturen zoals de glTF-exporter ze herkent. kleur = image of rgb-tuple."""
    m = bpy.data.materials.new(naam)
    m.use_nodes = True
    nt = m.node_tree
    b = nt.nodes["Principled BSDF"]
    b.inputs["Specular IOR Level"].default_value = 0.3
    if isinstance(kleur, tuple):
        b.inputs["Base Color"].default_value = (*kleur[:3], 1)
    else:
        t = nt.nodes.new("ShaderNodeTexImage")
        t.image = kleur
        if factor:
            mx = nt.nodes.new("ShaderNodeMix")
            mx.data_type = "RGBA"
            mx.blend_type = "MULTIPLY"
            mx.inputs["Factor"].default_value = 1.0
            nt.links.new(t.outputs["Color"], mx.inputs[6])
            mx.inputs[7].default_value = (*factor, 1)
            nt.links.new(mx.outputs[2], b.inputs["Base Color"])
        else:
            nt.links.new(t.outputs["Color"], b.inputs["Base Color"])
        if alpha:
            rnd = nt.nodes.new("ShaderNodeMath")
            rnd.operation = "ROUND"                  # glTF MASK, afkap 0,5
            nt.links.new(t.outputs["Alpha"], rnd.inputs[0])
            nt.links.new(rnd.outputs[0], b.inputs["Alpha"])
    if alfa_waarde is not None:
        b.inputs["Alpha"].default_value = alfa_waarde
    if nrm:
        tn = nt.nodes.new("ShaderNodeTexImage")
        tn.image = nrm
        nm = nt.nodes.new("ShaderNodeNormalMap")
        nt.links.new(tn.outputs["Color"], nm.inputs["Color"])
        nt.links.new(nm.outputs["Normal"], b.inputs["Normal"])
    if orm:
        to = nt.nodes.new("ShaderNodeTexImage")
        to.image = orm
        sp = nt.nodes.new("ShaderNodeSeparateColor")
        nt.links.new(to.outputs["Color"], sp.inputs["Color"])
        nt.links.new(sp.outputs["Green"], b.inputs["Roughness"])
        nt.links.new(sp.outputs["Blue"], b.inputs["Metallic"])
        g = nt.nodes.new("ShaderNodeGroup")
        g.node_tree = gltf_groep()
        nt.links.new(sp.outputs["Red"], g.inputs["Occlusion"])
    else:
        b.inputs["Roughness"].default_value = ruw
        b.inputs["Metallic"].default_value = metaal
    if emissie is not None:
        if isinstance(emissie, tuple):
            b.inputs["Emission Color"].default_value = (*emissie[:3], 1)
        else:
            te = nt.nodes.new("ShaderNodeTexImage")
            te.image = emissie
            nt.links.new(te.outputs["Color"], b.inputs["Emission Color"])
        b.inputs["Emission Strength"].default_value = emissie_kracht
    m.use_backface_culling = not tweezijdig
    if blend:
        m.surface_render_method = "BLENDED"
    return m


def ph(naam, prefix=None, factor=None, metaal=0.0, ruw_plus=0.0, tweezijdig=False):
    """Tegelbare Poly Haven-set als glTF-materiaal (UV in meters op de mesh)."""
    d = laad(os.path.join(TEX, f"{naam}_diff_1k.jpg"))
    n = laad(os.path.join(TEX, f"{naam}_nor_gl_1k.jpg"), data=True)
    o = orm_van(naam, metaal=metaal, ruw_plus=ruw_plus)
    return pbr(prefix or naam, d, n, o, factor=factor, tweezijdig=tweezijdig)


def zet_factor(m, factor):
    """baseColorFactor via een Multiply-mix (de exporter leest die als factor)."""
    for n in m.node_tree.nodes:
        if n.type == "MIX" and n.blend_type == "MULTIPLY":
            n.inputs[7].default_value = (*factor, 1)


# --- Studio: bovenaanzicht in modi --------------------------------------------------------
STUDIO_MATS = {}


def smat(naam, kleur, ruw=0.6, normaal=None, ao=0.0, sss=0.0, alfa=None, emissie=None, metaal=0.0):
    """Studiomateriaal. kleur/ruw: waarde of (nt -> socket). normaal: nt -> vector-socket (bump).
    ao: afstand voor AO in de kleurmodus (0 = uit). alfa: nt -> float-socket."""
    m = bpy.data.materials.new(naam)
    m.use_nodes = True
    nt = m.node_tree
    b = nt.nodes["Principled BSDF"]
    out = nt.nodes["Material Output"]

    def sock(v, kind):
        if callable(v):
            return v(nt)
        n = nt.nodes.new("ShaderNodeRGB" if kind == "c" else "ShaderNodeValue")
        if kind == "c":
            n.outputs[0].default_value = (*v[:3], 1)
        else:
            n.outputs[0].default_value = v
        return n.outputs[0]
    c = sock(kleur, "c")
    r = sock(ruw, "v")
    nt.links.new(c, b.inputs["Base Color"])
    nt.links.new(r, b.inputs["Roughness"])
    b.inputs["Metallic"].default_value = metaal
    b.inputs["Specular IOR Level"].default_value = 0.35
    if sss:
        b.inputs["Subsurface Weight"].default_value = sss
    nrm = None
    if normaal:
        nrm = normaal(nt)
        nt.links.new(nrm, b.inputs["Normal"])
    a = alfa(nt) if alfa else None
    if a is not None:
        nt.links.new(a, b.inputs["Alpha"])
    if emissie:
        nt.links.new(sock(emissie[0], "c"), b.inputs["Emission Color"])
        b.inputs["Emission Strength"].default_value = emissie[1]
    STUDIO_MATS[naam] = dict(m=m, c=c, r=r, n=nrm, a=a, bsdf=b, out=out, ao=ao)
    return m


def modus(mode):
    """'lit' = gewone shading; 'kleur' (x AO), 'normaal' (wereld, 0..1), 'ruw' als emissie."""
    for naam, s in STUDIO_MATS.items():
        nt = s["m"].node_tree
        out = s["out"]
        for l in list(out.inputs["Surface"].links):
            nt.links.remove(l)
        for n in [n for n in nt.nodes if n.get("_modus")]:
            nt.nodes.remove(n)
        if mode == "lit":
            nt.links.new(s["bsdf"].outputs[0], out.inputs["Surface"])
            continue

        def nieuw(t):
            n = nt.nodes.new(t)
            n["_modus"] = 1
            return n
        em = nieuw("ShaderNodeEmission")
        if mode == "kleur":
            if s["ao"]:
                ao = nieuw("ShaderNodeAmbientOcclusion")
                ao.inputs["Distance"].default_value = s["ao"]
                ao.samples = 8
                mx = nieuw("ShaderNodeMix")
                mx.data_type = "RGBA"
                mx.blend_type = "MULTIPLY"
                mx.inputs["Factor"].default_value = 1.0
                nt.links.new(s["c"], mx.inputs[6])
                # AO zachter: 0.35 + 0.65 * ao
                mr = nieuw("ShaderNodeMapRange")
                nt.links.new(ao.outputs["AO"], mr.inputs["Value"])
                mr.inputs["To Min"].default_value = 0.35
                nt.links.new(mr.outputs[0], mx.inputs[7])
                nt.links.new(mx.outputs[2], em.inputs["Color"])
            else:
                nt.links.new(s["c"], em.inputs["Color"])
        elif mode == "normaal":
            if s["n"] is not None:
                src = s["n"]
            else:
                g = nieuw("ShaderNodeNewGeometry")
                src = g.outputs["Normal"]
            vm = nieuw("ShaderNodeVectorMath")
            vm.operation = "MULTIPLY_ADD"
            nt.links.new(src, vm.inputs[0])
            vm.inputs[1].default_value = (0.5, 0.5, 0.5)
            vm.inputs[2].default_value = (0.5, 0.5, 0.5)
            nt.links.new(vm.outputs[0], em.inputs["Color"])
        elif mode == "ruw":
            nt.links.new(s["r"], em.inputs["Color"])
        if s["a"] is not None:
            tr = nieuw("ShaderNodeBsdfTransparent")
            ms = nieuw("ShaderNodeMixShader")
            nt.links.new(s["a"], ms.inputs[0])
            nt.links.new(tr.outputs[0], ms.inputs[1])
            nt.links.new(em.outputs[0], ms.inputs[2])
            nt.links.new(ms.outputs[0], out.inputs["Surface"])
        else:
            nt.links.new(em.outputs[0], out.inputs["Surface"])


def studio_camera(sc, cx, cy, bw, bh, resx, resy, z=20.0):
    cd = bpy.data.cameras.new("studio_cam")
    cd.type = "ORTHO"
    cd.ortho_scale = max(bw, bh)
    cd.clip_end = 100
    cam = bpy.data.objects.new("studio_cam", cd)
    sc.collection.objects.link(cam)
    cam.location = (cx, cy, z)
    cam.rotation_euler = (0, 0, 0)
    sc.camera = cam
    sc.render.resolution_x, sc.render.resolution_y = resx, resy
    return cam


def studio_render(sc, pad_basis, modi=("kleur", "normaal", "ruw"), spp=32, transparant=True):
    """Render de studio in elke modus naar <pad_basis>_<modus>.png. Kleur in sRGB, data lineair."""
    sc.render.engine = "CYCLES"
    gpu(sc)
    sc.cycles.use_denoising = False
    sc.cycles.max_bounces = 2
    sc.cycles.transparent_max_bounces = 64
    sc.render.film_transparent = transparant
    sc.render.filter_size = 1.0
    sc.render.image_settings.file_format = "PNG"
    sc.render.image_settings.color_mode = "RGBA"
    sc.render.image_settings.color_depth = "8"
    uit = {}
    for mo in modi:
        modus(mo)
        sc.cycles.samples = spp * (2 if mo == "kleur" else 1)
        vt = "Standard"
        sc.view_settings.view_transform = "Standard"
        if mo != "kleur":
            try:
                sc.view_settings.view_transform = "Raw"
                vt = "Raw"
            except TypeError:
                raise RuntimeError("geen Raw view transform: data-passes zouden sRGB worden")
        sc.view_settings.look = "None"
        p = f"{pad_basis}_{mo}.png"
        sc.render.filepath = p
        bpy.ops.render.render(write_still=True)
        uit[mo] = p
        log("studio", os.path.basename(p), vt)
    modus("lit")
    return uit


# --- Bakken ---------------------------------------------------------------------------
BAKSOORT = {"kleur": ("DIFFUSE", {"COLOR"}, 16), "ruwheid": ("ROUGHNESS", set(), 4),
            "normaal": ("NORMAL", set(), 16), "ao": ("AO", set(), 128), "emissie": ("EMIT", set(), 4)}


def beeld(naam, w, h=None, data=False, alpha=False):
    img = bpy.data.images.new(naam, w, h or w, alpha=alpha)
    if data:
        img.colorspace_settings.name = "Non-Color"
    return img


def bak(laag, hoog, beelden, ext=0.05, ray=0.2, margin=8):
    """Bak hoog (lijst objecten) -> laag (een object met UVMap). beelden: [(soort, img)]."""
    sc = bpy.context.scene
    sc.render.engine = "CYCLES"
    gpu(sc)
    oude = list(laag.data.materials)
    idx = np.zeros(len(laag.data.polygons), np.int32)
    laag.data.polygons.foreach_get("material_index", idx)
    m = bpy.data.materials.new("_bak")
    m.use_nodes = True
    tn = m.node_tree.nodes.new("ShaderNodeTexImage")
    m.node_tree.nodes.active = tn
    laag.data.materials.clear()
    laag.data.materials.append(m)
    for v in ("visible_diffuse", "visible_glossy", "visible_shadow", "visible_transmission"):
        setattr(laag, v, False)
    ontkies()
    for h in hoog:
        h.select_set(True)
    laag.select_set(True)
    bpy.context.view_layer.objects.active = laag
    for soort, img in beelden:
        t, pf, spp = BAKSOORT[soort]
        sc.cycles.samples = spp
        tn.image = img
        kw = dict(type=t, use_selected_to_active=True, cage_extrusion=ext, max_ray_distance=ray, margin=margin,
                  margin_type="EXTEND", use_clear=True, target="IMAGE_TEXTURES")
        if pf:
            kw["pass_filter"] = pf
        if t == "NORMAL":
            kw.update(normal_space="TANGENT", normal_r="POS_X", normal_g="POS_Y", normal_b="POS_Z")
        t1 = time.time()
        bpy.ops.object.bake(**kw)
        log("  bak", img.name, soort, f"{time.time() - t1:.1f}s")
    for v in ("visible_diffuse", "visible_glossy", "visible_shadow", "visible_transmission"):
        setattr(laag, v, True)
    laag.data.materials.clear()
    for mm in oude:
        laag.data.materials.append(mm)
    laag.data.polygons.foreach_set("material_index", idx)
    bpy.data.materials.remove(m)


def pixels(img):
    a = np.zeros(img.size[0] * img.size[1] * 4, np.float32)
    img.pixels.foreach_get(a)
    return a.reshape(img.size[1], img.size[0], 4)


def bewaar(img, naam, jpg=False):
    """Schrijf naar natuur/textures/ en laad terug (de exporter neemt dan het bestand)."""
    pad = os.path.join(NTEX, naam + (".jpg" if jpg else ".png"))
    img.filepath_raw = pad
    img.file_format = "JPEG" if jpg else "PNG"
    if jpg:
        bpy.context.scene.render.image_settings.quality = 90
    img.save()
    data = img.colorspace_settings.name == "Non-Color"
    bpy.data.images.remove(img)
    out = bpy.data.images.load(pad, check_existing=False)
    out.name = naam
    if data:
        out.colorspace_settings.name = "Non-Color"
    return out


def orm_beeld(ao, ruw, naam, ao_min=0.0, metaal=0.0):
    a, r = pixels(ao), pixels(ruw)
    out = beeld(naam, ao.size[0], ao.size[1], data=True)
    p = np.ones_like(a)
    p[..., 0] = np.maximum(a[..., 0], ao_min)
    p[..., 1] = r[..., 0]
    p[..., 2] = metaal
    out.pixels.foreach_set(p.ravel())
    return out


def bak_set(naam, laag, hoog, res=1024, ext=0.05, ray=0.2, ao_min=0.25, jpg=True):
    """Kleur + normaal + ORM voor een laag object; geeft het glTF-materiaal terug."""
    k = beeld(naam + "_k", res)
    n = beeld(naam + "_n", res, data=True)
    r = beeld(naam + "_r", res, data=True)
    a = beeld(naam + "_ao", res, data=True)
    bak(laag, hoog, [("kleur", k), ("normaal", n), ("ruwheid", r), ("ao", a)], ext=ext, ray=ray)
    o = orm_beeld(a, r, naam + "_orm", ao_min=ao_min)
    # AO ook licht in de kleur, anders vlak bij Godot zonder SSAO
    kp, ap = pixels(k), pixels(a)
    kp[..., :3] *= (0.55 + 0.45 * np.maximum(ap[..., :1], ao_min))
    k.pixels.foreach_set(kp.ravel())
    bpy.data.images.remove(r)
    bpy.data.images.remove(a)
    K = bewaar(k, naam + "_kleur", jpg=jpg)
    N = bewaar(n, naam + "_normaal", jpg=jpg)
    O = bewaar(o, naam + "_orm", jpg=jpg)
    return pbr(naam, K, N, O)


def uv_slim(o, hoek=66, marge=0.004):
    ontkies()
    bpy.context.view_layer.objects.active = o
    o.select_set(True)
    bpy.ops.object.mode_set(mode="EDIT")
    bpy.ops.mesh.select_all(action="SELECT")
    bpy.ops.uv.smart_project(angle_limit=math.radians(hoek), island_margin=marge, area_weight=0.0,
                             correct_aspect=True, scale_to_bounds=False)
    bpy.ops.uv.pack_islands(margin=marge, rotate=True)
    bpy.ops.object.mode_set(mode="OBJECT")


def decimeer(o, ratio):
    m = o.modifiers.new("d", "DECIMATE")
    m.ratio = ratio
    m.use_collapse_triangulate = True
    ontkies()
    bpy.context.view_layer.objects.active = o
    bpy.ops.object.modifier_apply(modifier="d")


def pas_toe(o):
    ontkies()
    bpy.context.view_layer.objects.active = o
    o.select_set(True)
    for m in list(o.modifiers):
        bpy.ops.object.modifier_apply(modifier=m.name)


def tris(objs):
    n = 0
    for o in objs:
        if o.type == "MESH":
            o.data.calc_loop_triangles()
            n += len(o.data.loop_triangles)
    return n


# --- Export --------------------------------------------------------------------------
def exporteer(pad, objs):
    ontkies()
    for o in objs:
        o.select_set(True)
        for c in o.children_recursive:
            c.select_set(True)
    bpy.ops.export_scene.gltf(filepath=pad, export_format="GLB", use_selection=True, export_apply=True,
                              export_tangents=True, export_image_format="AUTO", export_cameras=False,
                              export_lights=False, export_extras=True, export_animations=False,
                              export_vertex_color="NONE", export_all_vertex_colors=False)
    log("export", os.path.basename(pad), f"{os.path.getsize(pad) / 1e6:.2f} MB",
        tris([o for o in objs] + [c for o in objs for c in o.children_recursive]), "tris")


# --- Voorvertoning ----------------------------------------------------------------------
def iso_scene(sc, sneeuw=False):
    """HDRI + zon zoals de hut, schaduwvanger; geeft de zon terug."""
    sc.render.engine = "CYCLES"
    gpu(sc)
    sc.cycles.samples = 96
    sc.cycles.use_denoising = True
    sc.cycles.max_bounces = 6
    sc.cycles.transparent_max_bounces = 64          # veel alfakaarten achter elkaar: anders zwart
    sc.render.film_transparent = True
    sc.view_settings.view_transform = "Standard"
    sc.render.image_settings.file_format = "PNG"
    sc.render.image_settings.color_mode = "RGBA"
    w = bpy.data.worlds.new("w")
    w.use_nodes = True
    wn = w.node_tree
    bg = wn.nodes["Background"]
    env = wn.nodes.new("ShaderNodeTexEnvironment")
    env.image = bpy.data.images.load(os.path.join(TEX, "qwantani_late_afternoon_1k.hdr"))
    mx = wn.nodes.new("ShaderNodeMix")
    mx.data_type = "RGBA"
    mx.blend_type = "DARKEN"
    mx.inputs["Factor"].default_value = 1.0
    wn.links.new(env.outputs["Color"], mx.inputs[6])
    mx.inputs[7].default_value = (1.2, 1.2, 1.2, 1)
    wn.links.new(mx.outputs[2], bg.inputs["Color"])
    bg.inputs["Strength"].default_value = 0.5
    sc.world = w
    d = bpy.data.lights.new("zon", "SUN")
    d.energy = 3.2
    d.color = (1.0, 0.92, 0.8)
    d.angle = math.radians(2.5)
    z = bpy.data.objects.new("zon", d)
    sc.collection.objects.link(z)
    z.rotation_euler = (math.radians(36), 0, math.radians(61))
    dv = bpy.data.lights.new("vul", "SUN")              # linksvoor, zacht (zoals de hut)
    dv.energy = 1.6
    dv.color = (0.95, 0.95, 1.0)
    dv.angle = math.radians(25)
    v2 = bpy.data.objects.new("vul", dv)
    sc.collection.objects.link(v2)
    v2.rotation_euler = (math.radians(55), 0, math.radians(-115))
    bpy.ops.mesh.primitive_plane_add(size=200, location=(0, 0, -0.09))   # net onder de voeten (die steken 8 cm in de grond)
    v = bpy.context.object
    v.name = "_vanger"
    v.is_shadow_catcher = True
    return z


def iso_camera(sc, objs, yaw=225.0, pitch=30.0, marge=1.08, res=700):
    """Ortho-camera op het iso-gezicht, passend om de bounding boxes van objs."""
    pts = []
    for o in objs:
        if o.type == "MESH":
            pts += [o.matrix_world @ Vector(c) for c in o.bound_box]
    yw, pt = math.radians(yaw), math.radians(pitch)
    dirv = Vector((math.cos(yw) * math.cos(pt), math.sin(yw) * math.cos(pt), math.sin(pt)))
    cd = bpy.data.cameras.new("iso")
    cd.type = "ORTHO"
    cam = bpy.data.objects.new("iso", cd)
    sc.collection.objects.link(cam)
    mid = sum(pts, Vector()) / len(pts)
    cam.location = mid + dirv * 60
    cam.rotation_euler = (mid - cam.location).to_track_quat("-Z", "Y").to_euler()
    bpy.context.view_layer.update()
    Mi = cam.matrix_world.inverted()
    q = [Mi @ p for p in pts]
    xs, ys = [p.x for p in q], [p.y for p in q]
    w, h = max(xs) - min(xs), max(ys) - min(ys)
    cx, cy = (max(xs) + min(xs)) / 2, (max(ys) + min(ys)) / 2
    cam.location = cam.matrix_world @ Vector((cx, cy, 0))
    cd.ortho_scale = max(w, h) * marge
    cd.clip_end = 200
    if w >= h:
        sc.render.resolution_x, sc.render.resolution_y = res, max(16, int(res * h / w))
    else:
        sc.render.resolution_x, sc.render.resolution_y = max(16, int(res * w / h)), res
    sc.camera = cam
    return cam, cd.ortho_scale


def importeer(pad):
    voor = set(bpy.context.scene.objects)
    bpy.ops.import_scene.gltf(filepath=pad)
    return [o for o in bpy.context.scene.objects if o not in voor]


def render_naar(sc, pad):
    sc.render.filepath = pad
    bpy.ops.render.render(write_still=True)
    log("render", os.path.basename(pad))
