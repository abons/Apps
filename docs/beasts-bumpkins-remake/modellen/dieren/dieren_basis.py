"""Gedeelde hulpjes voor de dieren (koe, later wolf): een bevroren kopie van de stabiele helpers uit
bumpkin_man.py (commit c1ef0b6), zodat een verbouwing daar de dieren niet breekt.

Ruis, superellips-ringen en de Bouwer (vertices + vlakken + UV in metres), Cycles-GPU, beelden naar
numpy, dilateren, reliëf -> tangent-normaal, het PBR-materiaal met tint (glTF baseColorFactor) en de
iso-studio (ortho, yaw 225, pitch 30, zon + HDR) met plak/schrijf voor de contactbladen.
"""
import math
import os

import bpy
import numpy as np
from mathutils import Vector

MOD = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def log(*a):
    print("[dier]", *a, flush=True)


def srgb(h):
    h = h.lstrip("#")
    c = [int(h[i:i + 2], 16) / 255 for i in (0, 2, 4)]
    return np.array([x / 12.92 if x <= 0.04045 else ((x + 0.055) / 1.055) ** 2.4 for x in c])


def naar_srgb(c):
    c = np.clip(c, 0, 1)
    return np.where(c <= 0.0031308, c * 12.92, 1.055 * np.power(c, 1 / 2.4) - 0.055)


# Albedo per deel (lineair). Iets lichter dan de sprite-middentoon: die is al belicht.
KLEUR = {
    "haar": srgb("#a5522c"), "huid": srgb("#d8925e"), "paars": srgb("#7a3888"),
    "hemd": srgb("#8d977f"), "metaal": srgb("#a4a4a0"), "snor": srgb("#6e3a1e"),
    "riem": srgb("#5a3a1f"), "gesp": srgb("#efbf00"), "laars": srgb("#4e2c15"), "zool": srgb("#2a1a0e"),
}


def _hash(ix, iy, iz, seed):
    h = (ix * 374761393 + iy * 668265263 + iz * 1440662683 + seed * 974634421) & 0xFFFFFFFF
    h = ((h ^ (h >> 13)) * 1274126177) & 0xFFFFFFFF
    h = h ^ (h >> 16)
    return (h & 0xFFFF).astype(np.float32) / 32767.5 - 1.0


def ruis(P, f=1.0, seed=0, octaven=1):
    """Waarde-ruis in [-1, 1] op punten P (n, 3), frequentie f per meter (scalar of 3-vector)."""
    P = np.asarray(P, np.float64)
    tot = np.zeros(len(P), np.float32)
    amp, norm = 1.0, 0.0
    for o in range(octaven):
        Q = P * np.asarray(f) * (2 ** o) + 17.3 * o
        i = np.floor(Q).astype(np.int64)
        t = (Q - i).astype(np.float32)
        t = t * t * (3 - 2 * t)
        v = 0
        for dx in (0, 1):
            for dy in (0, 1):
                for dz in (0, 1):
                    w = (t[:, 0] if dx else 1 - t[:, 0]) * (t[:, 1] if dy else 1 - t[:, 1]) * \
                        (t[:, 2] if dz else 1 - t[:, 2])
                    v = v + w * _hash(i[:, 0] + dx, i[:, 1] + dy, i[:, 2] + dz, seed + o)
        tot += amp * v
        norm += amp
        amp *= 0.5
    return tot / norm


def gladstap(a, b, x):
    t = np.clip((x - a) / (b - a), 0, 1)
    return t * t * (3 - 2 * t)


def gauss(x, s):
    return np.exp(-(x / s) ** 2)


# --- Skelet ---------------------------------------------------------------------------------------


class Bouwer:
    """Verzamelt vertices, vlakken en per hoek een UV in metres (laag 'UVm')."""

    def __init__(self):
        self.V, self.F, self.UV, self.reg = [], [], [], []

    def verts(self, P):
        b = len(self.V)
        self.V.extend([tuple(p) for p in np.asarray(P, float).reshape(-1, 3)])
        return b

    def vlak(self, idx, uv, regio=0):
        self.F.append(tuple(idx))
        self.UV.append(tuple(map(tuple, uv)))
        self.reg.append(regio)

    def grid(self, P, gesloten, regio=0, uv0=(0.0, 0.0), buiten=None):
        """P: (rijen, kolommen, 3). Gesloten: kolom n-1 sluit op kolom 0 (naad met eigen UV)."""
        P = np.asarray(P, float)
        R_, C = P.shape[:2]
        b = self.verts(P)
        Pc = np.concatenate([P, P[:, :1]], 1) if gesloten else P
        du = np.linalg.norm(np.diff(Pc, axis=1), axis=2)
        U = np.concatenate([np.zeros((R_, 1)), np.cumsum(du, 1)], 1)
        U -= U.mean(1, keepdims=True)
        dv = np.linalg.norm(np.diff(Pc, axis=0), axis=2)
        Vv = np.concatenate([np.zeros((1, Pc.shape[1])), np.cumsum(dv, 0)], 0)
        U += uv0[0]
        Vv += uv0[1]
        # wikkeling: een vlak in het midden moet van de rij-as af wijzen (open lofts: geen recalc)
        rm, cm = (R_ - 1) // 2, (C - 1) // 2
        p0, p1, p3 = P[rm, cm], P[rm, (cm + 1) % C], P[rm + 1, cm]
        ref_ = np.asarray(buiten, float) if buiten is not None else p0 - P[rm].mean(0)
        omkeren = np.dot(np.cross(p1 - p0, p3 - p0), ref_) < 0
        for r in range(R_ - 1):
            for c in range(C if gesloten else C - 1):
                c1 = (c + 1) % C
                idx = [b + r * C + c, b + r * C + c1, b + (r + 1) * C + c1, b + (r + 1) * C + c]
                uv = [(U[r, c], Vv[r, c]), (U[r, c + 1], Vv[r, c + 1]), (U[r + 1, c + 1], Vv[r + 1, c + 1]),
                      (U[r + 1, c], Vv[r + 1, c])]
                if omkeren:
                    idx, uv = idx[::-1], uv[::-1]
                self.vlak(idx, uv, regio)
        return b, C

    def kap(self, ring_b, n, punt, regio=0, buiten=None):
        """Waaier van een gesloten ring (n vertices vanaf ring_b) naar een punt; eigen UV-eiland."""
        c = self.verts([punt])
        P = np.array([self.V[ring_b + i] for i in range(n)])
        m = np.array(punt, float)
        ax = P[0] - m
        ax /= np.linalg.norm(ax) + 1e-9
        nn_ = np.cross(P[1] - m, P[0] - m)
        nn_ /= np.linalg.norm(nn_) + 1e-9
        ay = np.cross(nn_, ax)
        uv = lambda p: (np.dot(p - m, ax), np.dot(p - m, ay))
        bu = np.asarray(buiten, float) if buiten is not None else m - P.mean(0)
        omkeren = np.dot(np.cross(P[1] - P[0], m - P[0]), bu) < 0
        for i in range(n):
            idx = [ring_b + i, ring_b + (i + 1) % n, c]
            u = [uv(P[i]), uv(P[(i + 1) % n]), uv(m)]
            if omkeren:
                idx, u = idx[::-1], u[::-1]
            self.vlak(idx, u, regio)

    def obj(self, naam, coll):
        me = bpy.data.meshes.new(naam)
        me.from_pydata(self.V, [], self.F)
        me.update()
        lay = me.uv_layers.new(name="UVm")
        uv = np.array([c for f in self.UV for c in f], np.float32)
        lay.data.foreach_set("uv", uv.ravel())
        me.attributes.new("regio", "INT", "FACE").data.foreach_set("value", np.array(self.reg, np.int32))
        me.shade_smooth()
        o = bpy.data.objects.new(naam, me)
        coll.objects.link(o)
        return o


def ring(c, s, f, a, b, n, p=2.0, fase=0.0):
    """Superellips: zij-as s (straal a), voor-as f (straal b). Hoek 0 = +s, 90 graden = +f."""
    th = fase + 2 * np.pi * np.arange(n) / n
    cx, cy = np.cos(th), np.sin(th)
    x = np.sign(cx) * np.abs(cx) ** (2 / p)
    y = np.sign(cy) * np.abs(cy) ** (2 / p)
    return np.asarray(c)[None] + x[:, None] * a * np.asarray(s)[None] + y[:, None] * b * np.asarray(f)[None]


def gpu(scene):
    p = bpy.context.preferences.addons["cycles"].preferences
    for t in ("CUDA", "OPTIX"):
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


def ontkies():
    for o in bpy.context.scene.objects:
        if o is not None:
            o.select_set(False)


def beeld(naam, w, data=True, flt=True):
    img = bpy.data.images.new(naam, w, w, alpha=True, float_buffer=flt)
    if data:
        img.colorspace_settings.name = "Non-Color"
    return img


def pixels(img):
    a = np.zeros(img.size[0] * img.size[1] * 4, np.float32)
    img.pixels.foreach_get(a)
    return a.reshape(img.size[1], img.size[0], 4)


def reliëf_normaal(Hm, mpp_map):
    """Tangent-normaal uit een hoogteveld (m) per texel; atlas-assen = UVm-assen (niet gedraaid)."""
    gy, gx = np.gradient(Hm)
    nx = -gx / mpp_map
    ny = -gy / mpp_map
    nz = np.ones_like(nx)
    L = np.sqrt(nx * nx + ny * ny + nz * nz)
    return np.stack([nx / L, ny / L, nz / L], -1)


def dilateer(rgb, mask, stappen=8):
    rgb = rgb.copy()
    mask = mask.copy()
    for _ in range(stappen):
        acc = np.zeros_like(rgb)
        cnt = np.zeros(mask.shape, np.float32)
        for dy, dx in ((-1, 0), (1, 0), (0, -1), (0, 1)):
            m2 = np.roll(np.roll(mask, dy, 0), dx, 1)
            acc += np.roll(np.roll(rgb, dy, 0), dx, 1) * m2[..., None]
            cnt += m2
        nieuw = (~mask) & (cnt > 0)
        rgb[nieuw] = acc[nieuw] / cnt[nieuw][:, None]
        mask = mask | nieuw
    return rgb


GLTF_GROEP = None


def gltf_groep():
    global GLTF_GROEP
    if GLTF_GROEP is None:
        GLTF_GROEP = bpy.data.node_groups.new("glTF Material Output", "ShaderNodeTree")
        GLTF_GROEP.interface.new_socket("Occlusion", in_out="INPUT", socket_type="NodeSocketFloat")
    return GLTF_GROEP


def pbr(naam, kleur, nrm, orm_img, tint=(1, 1, 1)):
    """Principled met de atlas; tint als Mix(Multiply) -> glTF baseColorFactor."""
    m = bpy.data.materials.new(naam)
    m.use_nodes = True
    nt = m.node_tree
    b = nt.nodes["Principled BSDF"]
    b.inputs["Specular IOR Level"].default_value = 0.35
    t = nt.nodes.new("ShaderNodeTexImage")
    t.image = kleur
    mix = nt.nodes.new("ShaderNodeMix")
    mix.data_type = "RGBA"
    mix.blend_type = "MULTIPLY"
    mix.inputs["Factor"].default_value = 1.0
    nt.links.new(t.outputs["Color"], mix.inputs[6])
    mix.inputs[7].default_value = (*tint, 1.0)
    nt.links.new(mix.outputs[2], b.inputs["Base Color"])
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
    m.use_backface_culling = True
    return m


def vlak_mat(naam, kleur, ruw=0.8):
    m = bpy.data.materials.new(naam)
    m.use_nodes = True
    bs = m.node_tree.nodes["Principled BSDF"]
    bs.inputs["Base Color"].default_value = (*kleur, 1)
    bs.inputs["Roughness"].default_value = ruw
    return m


def studio(sc, px_per_m, breed=1.0, hoog_=1.5, doel=(0, 0, 0.68), yaw=225, pitch=30):
    sc.render.engine = "BLENDER_EEVEE"
    sc.eevee.taa_render_samples = 32
    sc.render.film_transparent = True
    sc.view_settings.view_transform = "Standard"
    cam = sc.objects.get("cam")
    if cam is None:
        cd = bpy.data.cameras.new("cam")
        cd.type = "ORTHO"
        cam = bpy.data.objects.new("cam", cd)
        sc.collection.objects.link(cam)
        sc.camera = cam
        w = bpy.data.worlds.new("studio")
        w.use_nodes = True
        nt = w.node_tree
        env = nt.nodes.new("ShaderNodeTexEnvironment")
        env.image = bpy.data.images.load(os.path.join(MOD, "textures", "qwantani_late_afternoon_1k.hdr"))
        nt.links.new(env.outputs[0], nt.nodes["Background"].inputs[0])
        nt.nodes["Background"].inputs[1].default_value = 0.4
        sc.world = w
        ld = bpy.data.lights.new("zon", "SUN")
        ld.energy = 3.0
        ld.color = (1.0, 0.94, 0.84)
        ld.angle = math.radians(3)
        zo = bpy.data.objects.new("zon", ld)
        zo.rotation_euler = (math.radians(40), 0, math.radians(-45))     # van de camerakant, hoog
        sc.collection.objects.link(zo)
    cam.data.ortho_scale = max(breed, hoog_)
    sc.render.resolution_x = max(4, int(round(breed * px_per_m)))
    sc.render.resolution_y = max(4, int(round(hoog_ * px_per_m)))
    sc.render.resolution_percentage = 100
    y, p = math.radians(yaw), math.radians(pitch)
    d = Vector((math.cos(y) * math.cos(p), math.sin(y) * math.cos(p), math.sin(p)))
    cam.location = Vector(doel) + d * 20
    cam.rotation_euler = (Vector(doel) - cam.location).to_track_quat("-Z", "Y").to_euler()
    cam.data.clip_end = 100
    return cam


def laad_np(pad):
    img = bpy.data.images.load(pad, check_existing=False)
    a = np.array(img.pixels[:], np.float32).reshape(img.size[1], img.size[0], 4)[::-1]
    bpy.data.images.remove(img)
    return a


def render_np(sc, pad):
    sc.render.filepath = pad
    bpy.ops.render.render(write_still=True)
    return laad_np(pad)


def bijsnijden(a):
    m = a[..., 3] > 0.5
    ys, xs = np.where(m)
    return a[ys.min():ys.max() + 1, xs.min():xs.max() + 1]


def plak(panelen, bg=(0.58, 0.66, 0.53), gat=12):
    """Panelen (rij 0 boven, RGBA, sRGB-waarden) onderaan uitgelijnd naast elkaar."""
    h = max(p.shape[0] for p in panelen) + 2 * gat
    w = sum(p.shape[1] for p in panelen) + gat * (len(panelen) + 1)
    out = np.ones((h, w, 3), np.float32) * np.array(bg, np.float32)
    x = gat
    for p in panelen:
        y = h - gat - p.shape[0]
        al = p[..., 3:4]
        out[y:y + p.shape[0], x:x + p.shape[1]] = p[..., :3] * al + out[y:y + p.shape[0], x:x + p.shape[1]] * (1 - al)
        x += p.shape[1] + gat
    return out


def onder(*rijen, bg=(0.58, 0.66, 0.53)):
    w = max(r.shape[1] for r in rijen)
    return np.concatenate([np.concatenate([r, np.ones((r.shape[0], w - r.shape[1], 3), np.float32) * np.array(bg, np.float32)], 1)
                           for r in rijen], 0)


def schrijf(out, pad):
    img = bpy.data.images.new("uit", out.shape[1], out.shape[0])
    img.colorspace_settings.name = "Non-Color"
    a = np.concatenate([out[::-1], np.ones((*out.shape[:2], 1), np.float32)], 2)
    img.pixels.foreach_set(a.ravel())
    img.filepath_raw = pad
    img.file_format = "PNG"
    img.save()
    bpy.data.images.remove(img)
    log("->", pad)


def nn(a, k):
    return np.repeat(np.repeat(a, k, 0), k, 1)


