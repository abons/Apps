"""Tegelbare terreintexturen (1024 px, 2 x 2 m per herhaling) voor de Godot-terreinshader.

gras en bosgrond: Cycles-studio van boven (Poly Haven-grond + echte grassprieten, bloemetjes,
naalden, takjes, steentjes), met geometrie die over de randen heen herhaald wordt, dus naadloos.
rots, zand en water_rand: periodieke ruis/voronoi in numpy (hoogte -> normaal).

Per set: textures/terrein_<naam>_kleur.jpg (sRGB), _normaal.jpg (OpenGL, Y+), _ruw.jpg (ruwheid).
  blender -b -P terrein.py -- [alleen=gras,bosgrond,rots,zand,water_rand] [res=1024]
"""
import math
import os
import random
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bpy
import numpy as np
from mathutils import Vector

import natuur_lib as L

RES = int(L.OPTS.get("res", 1024))
ALLEEN = L.OPTS.get("alleen", "gras,bosgrond,rots,zand,water_rand").split(",")
T = 2.0                      # tegel in meters


# --- Numpy: periodieke ruis -----------------------------------------------------------------
def waarde_ruis(N, g, seed):
    rng = np.random.default_rng(seed)
    r = rng.random((g, g))
    x = np.arange(N) / N * g
    i0 = np.floor(x).astype(int)
    f = x - i0
    f = f * f * (3 - 2 * f)
    i1 = (i0 + 1) % g
    i0 %= g
    a = r[i0][:, i0] * (1 - f)[None, :] + r[i0][:, i1] * f[None, :]
    b = r[i1][:, i0] * (1 - f)[None, :] + r[i1][:, i1] * f[None, :]
    return a * (1 - f)[:, None] + b * f[:, None]


def fbm(N, g, seed, oct=5, pers=0.5):
    out, amp, tot = np.zeros((N, N)), 1.0, 0.0
    for o in range(oct):
        out += amp * waarde_ruis(N, g * 2 ** o, seed + o)
        tot += amp
        amp *= pers
    return out / tot


def voronoi(N, n, seed, warp=None):
    """F1 en F2 (periodiek) voor n zaden; warp = (dx, dy) in tegelfracties."""
    rng = np.random.default_rng(seed)
    S = rng.random((n, 2))
    y, x = np.mgrid[0:N, 0:N] / N
    if warp is not None:
        x = (x + warp[0]) % 1
        y = (y + warp[1]) % 1
    f1 = np.full((N, N), 9.0)
    f2 = np.full((N, N), 9.0)
    cel = np.zeros((N, N), int)
    for k, (sx, sy) in enumerate(S):
        dx = np.abs(x - sx)
        dx = np.minimum(dx, 1 - dx)
        dy = np.abs(y - sy)
        dy = np.minimum(dy, 1 - dy)
        d = np.sqrt(dx * dx + dy * dy)
        f2 = np.where(d < f1, f1, np.minimum(f2, d))
        cel = np.where(d < f1, k, cel)
        f1 = np.minimum(f1, d)
    voronoi.cel = cel
    return f1, f2


def normaal(h, kracht):
    gx = (np.roll(h, -1, 1) - np.roll(h, 1, 1)) * 0.5
    gy = (np.roll(h, -1, 0) - np.roll(h, 1, 0)) * 0.5
    n = np.stack([-gx * kracht, -gy * kracht, np.ones_like(h)], 2)
    n /= np.linalg.norm(n, axis=2, keepdims=True)
    return n * 0.5 + 0.5


def schrijf(naam, kleur, nrm, ruw):
    """kleur als sRGB-waarden (8-bit beeld), nrm/ruw als data. Rij 0 = onder (bpy)."""
    N = kleur.shape[0]
    for soort, arr, data in (("kleur", kleur, False), ("normaal", nrm, True), ("ruw", ruw, True)):
        if arr.ndim == 2:
            arr = np.repeat(arr[..., None], 3, 2)
        rgba = np.concatenate([np.clip(arr, 0, 1), np.ones((N, N, 1))], 2).astype(np.float32)
        img = bpy.data.images.new(f"t_{naam}_{soort}", N, N)
        if data:
            img.colorspace_settings.name = "Non-Color"
        img.pixels.foreach_set(rgba.ravel())
        img.filepath_raw = os.path.join(L.NTEX, f"terrein_{naam}_{soort}.jpg")
        img.file_format = "JPEG"
        bpy.context.scene.render.image_settings.quality = 92
        img.save()
        bpy.data.images.remove(img)
        L.log("terrein", naam, soort)


def lin(c):
    """bpy.pixels van een 8-bit sRGB-beeld zijn al sRGB-waarden: niets omrekenen."""
    return np.asarray(c, float)


# --- Rots, zand, water ---------------------------------------------------------------------
def rots():
    N = RES
    w = (fbm(N, 3, 5, 3) - 0.5) * 0.16, (fbm(N, 3, 6, 3) - 0.5) * 0.16
    f1, f2 = voronoi(N, 9, 11, warp=w)
    rand = f2 - f1
    celtint = np.random.default_rng(16).uniform(0.82, 1.12, 9)[voronoi.cel]
    breedte = 0.006 + 0.014 * fbm(N, 4, 17, 3)
    barst = np.clip(1 - rand / breedte, 0, 1) ** 1.5
    g1, g2 = voronoi(N, 26, 12, warp=w)
    fijn = np.clip(1 - (g2 - g1) / 0.005, 0, 1) * 0.35
    plaat = fbm(N, 4, 13, 5)
    h = 0.6 * plaat + 0.4 * np.clip(rand * 12, 0, 1) - 0.9 * barst - 0.25 * fijn
    det = fbm(N, 32, 14, 3)
    h += 0.08 * det
    basis = lin([0.50, 0.53, 0.56])
    korrel = fbm(N, 64, 18, 2)
    kl = basis[None, None, :] * celtint[..., None] * (0.9 + 0.2 * plaat[..., None]) * (0.88 + 0.24 * korrel[..., None])
    kl = kl * (1 - 0.75 * barst[..., None]) * (1 - 0.3 * fijn[..., None])
    # lichte afgesleten randen langs de barsten
    kl = kl * (1 + 0.18 * np.clip(1 - rand / (breedte * 2.5), 0, 1) * (1 - barst))[..., None]
    ruw = 0.62 + 0.25 * (1 - plaat) + 0.1 * barst
    schrijf("rots", kl, normaal(h, 9.0), ruw)


def zand():
    N = RES
    y, x = np.mgrid[0:N, 0:N] / N
    warp = fbm(N, 3, 21, 4)
    rib = np.sin(2 * np.pi * (y * 9 + x * 2 + warp * 2.2)) * 0.75 + 0.25 * np.sin(2 * np.pi * (y * 5 - x * 4 + warp * 1.5))
    rib = (rib + 1) / 2
    rib = rib ** 1.6                      # scherpe kam, flauwe trog
    korrel = fbm(N, 128, 22, 2)
    h = 0.7 * rib + 0.3 * fbm(N, 8, 23, 4) + 0.06 * korrel
    basis = lin([0.93, 0.87, 0.75])
    kl = basis[None, None, :] * (0.9 + 0.12 * rib[..., None] + 0.08 * (korrel[..., None] - 0.5))
    rng = np.random.default_rng(24)
    spik = rng.random((N, N)) > 0.9975
    kl[spik] *= np.array([0.45, 0.42, 0.40])
    ruw = 0.85 + 0.1 * korrel
    schrijf("zand", kl, normaal(h, 5.0), ruw)


def water_rand():
    """Ondiep water over zand: lichtturquoise met kaustieklijnen (het is de bodem die je ziet)."""
    N = RES
    w = (fbm(N, 3, 31, 3) - 0.5) * 0.22, (fbm(N, 3, 32, 3) - 0.5) * 0.22
    f1, f2 = voronoi(N, 40, 37, warp=w)
    lijn = np.clip(1 - (f2 - f1) / 0.03, 0, 1) ** 1.6
    g1, g2 = voronoi(N, 90, 38, warp=w)
    lijn2 = np.clip(1 - (g2 - g1) / 0.012, 0, 1) ** 2
    caust = np.clip(0.75 * lijn + 0.45 * lijn2, 0, 1)
    diep = fbm(N, 2, 35, 3)
    bodem = lin([0.62, 0.80, 0.82])
    kl = bodem[None, None, :] * (0.85 + 0.25 * diep[..., None])
    kl = kl * 0.9 + (np.array([1.0, 1.0, 0.96]) - kl * 0.9) * caust[..., None] * 0.9
    golf = fbm(N, 6, 36, 4)
    schrijf("water_rand", kl, normaal(golf, 14.0), 0.06 + 0.04 * golf)


# --- Studio: gras en bosgrond ------------------------------------------------------------------
def grond_mat(naam, ph, tint=None, licht=1.0):
    """Studio-materiaal met een Poly Haven-grond, 1 herhaling per meter."""
    def kleur(nt):
        tc = nt.nodes.new("ShaderNodeTexCoord")
        mp = nt.nodes.new("ShaderNodeMapping")
        nt.links.new(tc.outputs["UV"], mp.inputs["Vector"])
        mp.inputs["Scale"].default_value = (T, T, 1)
        t = nt.nodes.new("ShaderNodeTexImage")
        t.image = L.laad(os.path.join(L.TEX, f"{ph}_diff_1k.jpg"))
        nt.links.new(mp.outputs[0], t.inputs["Vector"])
        if not tint:
            return t.outputs["Color"]
        mx = nt.nodes.new("ShaderNodeMix")
        mx.data_type = "RGBA"
        mx.blend_type = "MULTIPLY"
        mx.inputs["Factor"].default_value = 1
        nt.links.new(t.outputs["Color"], mx.inputs[6])
        mx.inputs[7].default_value = (*tint, 1)
        return mx.outputs[2]

    def nrm(nt):
        tc = nt.nodes.new("ShaderNodeTexCoord")
        mp = nt.nodes.new("ShaderNodeMapping")
        nt.links.new(tc.outputs["UV"], mp.inputs["Vector"])
        mp.inputs["Scale"].default_value = (T, T, 1)
        t = nt.nodes.new("ShaderNodeTexImage")
        t.image = L.laad(os.path.join(L.TEX, f"{ph}_nor_gl_1k.jpg"), data=True)
        nt.links.new(mp.outputs[0], t.inputs["Vector"])
        nm = nt.nodes.new("ShaderNodeNormalMap")
        nt.links.new(t.outputs["Color"], nm.inputs["Color"])
        return nm.outputs["Normal"]
    return L.smat(naam, kleur, ruw=0.9, normaal=nrm, ao=0.04)


def grondvlak(mat):
    b = L.Bouwer()
    vs = [b.v((x, y, 0)) for x, y in ((-T / 2, -T / 2), (T / 2, -T / 2), (T / 2, T / 2), (-T / 2, T / 2))]
    b.f(vs, [(0, 0), (1, 0), (1, 1), (0, 1)])
    return L.obj("grond", b.mesh("grond", [mat]))


def herhaal(plaats, marge):
    """Kopieen over de tegelrand: geeft de offsets voor een punt (x, y) nabij een rand."""
    x, y = plaats
    offs = [(0, 0)]
    for dx in (-T, 0, T):
        for dy in (-T, 0, T):
            if (dx, dy) == (0, 0):
                continue
            if -T / 2 - marge < x + dx < T / 2 + marge and -T / 2 - marge < y + dy < T / 2 + marge:
                offs.append((dx, dy))
    return offs


def spriet(b, rnd, p, lengte, breed, mat, var):
    a = rnd.uniform(0, 2 * math.pi)
    tilt = rnd.uniform(0.2, 1.1)
    d = Vector((math.cos(a) * math.sin(tilt), math.sin(a) * math.sin(tilt), math.cos(tilt)))
    w = Vector((-math.sin(a), math.cos(a), 0))
    c = (var, 0, 0, 1)
    pts = []
    for j in range(4):
        t = j / 3
        q = p + d * lengte * t + Vector((math.cos(a), math.sin(a), 0)) * 0.25 * lengte * t * t
        q.z -= 0.15 * lengte * t * t
        ww = breed * (1 - t) * 0.5
        pts.append((b.v(q - w * ww, c), b.v(q + w * ww, c)))
    for j in range(3):
        b.f([pts[j][0], pts[j][1], pts[j + 1][1], pts[j + 1][0]], [(0, 0), (1, 0), (1, 1), (0, 1)], mat)


def gras():
    sc = L.leeg()
    rnd = random.Random(1)
    gm = grond_mat("ondergrond", "forest_ground_04", tint=(0.55, 0.6, 0.35))
    grondvlak(gm)
    b = L.Bouwer()

    def sprietkleur(nt):
        at = nt.nodes.new("ShaderNodeAttribute")
        at.attribute_name = "wind"
        sp = nt.nodes.new("ShaderNodeSeparateColor")
        nt.links.new(at.outputs["Color"], sp.inputs["Color"])
        rp = nt.nodes.new("ShaderNodeValToRGB")
        e = rp.color_ramp.elements
        e[0].position, e[0].color = 0.0, (0.035, 0.11, 0.015, 1)
        e[1].position, e[1].color = 0.55, (0.08, 0.24, 0.03, 1)
        e.new(0.85).color = (0.16, 0.34, 0.05, 1)
        e.new(1.0).color = (0.26, 0.38, 0.08, 1)
        nt.links.new(sp.outputs["Red"], rp.inputs["Fac"])
        return rp.outputs["Color"]
    ms = L.smat("spriet", sprietkleur, ruw=0.55, ao=0.05)
    n = int(9000 * T * T)
    for k in range(n):
        p = (rnd.uniform(-T / 2, T / 2), rnd.uniform(-T / 2, T / 2))
        lengte = rnd.uniform(0.05, 0.13)
        var = rnd.random()
        s = rnd.random()
        for dx, dy in herhaal(p, 0.15):
            r2 = random.Random(k)
            spriet(b, r2, Vector((p[0] + dx, p[1] + dy, 0)), lengte, rnd.uniform(0.006, 0.01) if dx == dy == 0 else 0.008, 0, var)
    # bloemetjes: geel en wit, in groepjes (zoals het concept)
    bl = L.Bouwer()
    for g in range(7):
        cx, cy = rnd.uniform(-T / 2, T / 2), rnd.uniform(-T / 2, T / 2)
        geel = g % 2 == 0
        for k in range(rnd.randint(8, 14)):
            p = (cx + rnd.gauss(0, 0.06), cy + rnd.gauss(0, 0.06))
            r = rnd.uniform(0.01, 0.014) if geel else rnd.uniform(0.008, 0.011)
            for dx, dy in herhaal(p, 0.05):
                c = Vector((p[0] + dx, p[1] + dy, rnd.uniform(0.07, 0.12)))
                kleur = 1.0 if geel else 0.0
                for i in range(6 if geel else 8):
                    a = 2 * math.pi * i / (6 if geel else 8)
                    q = [c, c + Vector((math.cos(a - 0.3), math.sin(a - 0.3), 0)) * r,
                         c + Vector((math.cos(a), math.sin(a), 0.1)) * r * 1.3, c + Vector((math.cos(a + 0.3), math.sin(a + 0.3), 0)) * r]
                    vi = [bl.v(v, (kleur, 0, 0, 1)) for v in q]
                    bl.f(vi, [(0, 0), (1, 0), (1, 1), (0, 1)], 0)
                hart = [bl.v(c + Vector((math.cos(a), math.sin(a), 0.2)) * r * 0.3, (0.5, 0, 0, 1)) for a in np.linspace(0, 6.28, 6, endpoint=False)]
                bl.f(hart, [(0, 0)] * 6, 1)

    def bloemkleur(nt):
        at = nt.nodes.new("ShaderNodeAttribute")
        at.attribute_name = "wind"
        sp = nt.nodes.new("ShaderNodeSeparateColor")
        nt.links.new(at.outputs["Color"], sp.inputs["Color"])
        mx = nt.nodes.new("ShaderNodeMix")
        mx.data_type = "RGBA"
        nt.links.new(sp.outputs["Red"], mx.inputs["Factor"])
        mx.inputs[6].default_value = (0.85, 0.85, 0.8, 1)
        mx.inputs[7].default_value = (0.9, 0.62, 0.02, 1)
        return mx.outputs[2]
    mb = L.smat("bloem", bloemkleur, ruw=0.5, ao=0.02)
    mh = L.smat("hart", (0.8, 0.45, 0.02), ruw=0.5)
    L.obj("sprieten", b.mesh("sprieten", [ms]))
    L.obj("bloemen", bl.mesh("bloemen", [mb, mh]))
    L.log("gras", b.ntris(), "tris")
    return studio("gras")


def bosgrond():
    sc = L.leeg()
    rnd = random.Random(2)
    gm = grond_mat("bodem", "forest_ground_04", tint=(0.36, 0.26, 0.19))
    grondvlak(gm)
    b = L.Bouwer()      # 0 naald, 1 takje, 2 steentje
    for k in range(int(700 * T * T)):
        p = (rnd.uniform(-T / 2, T / 2), rnd.uniform(-T / 2, T / 2))
        a = rnd.uniform(0, 2 * math.pi)
        lengte = rnd.uniform(0.04, 0.08)
        var = rnd.random()
        for dx, dy in herhaal(p, 0.09):
            q = Vector((p[0] + dx, p[1] + dy, rnd.uniform(0.001, 0.008)))
            d = Vector((math.cos(a), math.sin(a), 0))
            w = Vector((-d.y, d.x, 0)) * 0.002
            vi = [b.v(q - w, (var, 0, 0, 1)), b.v(q + w, (var, 0, 0, 1)), b.v(q + d * lengte + w, (var, 0, 0, 1)),
                  b.v(q + d * lengte - w, (var, 0, 0, 1))]
            b.f(vi, [(0, 0), (1, 0), (1, 1), (0, 1)], 0)
    for k in range(int(5 * T * T)):
        p = (rnd.uniform(-T / 2, T / 2), rnd.uniform(-T / 2, T / 2))
        a = rnd.uniform(0, 2 * math.pi)
        lengte = rnd.uniform(0.2, 0.42)
        for dx, dy in herhaal(p, 0.45):
            q0 = Vector((p[0] + dx, p[1] + dy, 0.008))
            d = Vector((math.cos(a), math.sin(a), 0))
            P = [q0 + d * lengte * t + Vector((-d.y, d.x, 0)) * 0.02 * math.sin(t * 5) for t in np.linspace(0, 1, 6)]
            L.buis(b, P, [0.012 * (1 - 0.5 * t) for t in np.linspace(0, 1, 6)], zijden=6, mat=1)
            # zijtakje
            q1 = P[3]
            d2 = (d + Vector((-d.y, d.x, 0)) * 0.8).normalized()
            L.buis(b, [q1, q1 + d2 * lengte * 0.35], [0.005, 0.003], zijden=5, mat=1)
    import bmesh
    for k in range(int(10 * T * T)):
        p = (rnd.uniform(-T / 2, T / 2), rnd.uniform(-T / 2, T / 2))
        s = rnd.uniform(0.012, 0.03)
        for dx, dy in herhaal(p, 0.05):
            bm = bmesh.new()
            bmesh.ops.create_icosphere(bm, subdivisions=2, radius=1)
            M = L.Matrix.Translation(Vector((p[0] + dx, p[1] + dy, s * 0.2))) @ L.Matrix.Diagonal((s * 1.2, s, s * 0.6, 1))
            L.bm_naar_bouwer(bm, b, mat=2, M=M)
            bm.free()

    def naaldkleur(nt):
        at = nt.nodes.new("ShaderNodeAttribute")
        at.attribute_name = "wind"
        sp = nt.nodes.new("ShaderNodeSeparateColor")
        nt.links.new(at.outputs["Color"], sp.inputs["Color"])
        mx = nt.nodes.new("ShaderNodeMix")
        mx.data_type = "RGBA"
        nt.links.new(sp.outputs["Red"], mx.inputs["Factor"])
        mx.inputs[6].default_value = (0.10, 0.04, 0.015, 1)
        mx.inputs[7].default_value = (0.30, 0.12, 0.04, 1)
        return mx.outputs[2]
    mn = L.smat("naald", naaldkleur, ruw=0.6, ao=0.02)
    mt = L.smat("takje", (0.10, 0.075, 0.055), ruw=0.8, ao=0.02, normaal=lambda nt: _bump(nt))
    mst = L.smat("steentje", (0.15, 0.12, 0.09), ruw=0.55, ao=0.03, normaal=lambda nt: _bump(nt))
    L.obj("strooisel", b.mesh("strooisel", [mn, mt, mst]))
    L.log("bosgrond", b.ntris(), "tris")
    return studio("bosgrond")


def _bump(nt):
    n = nt.nodes.new("ShaderNodeTexNoise")
    n.inputs["Scale"].default_value = 200
    bp = nt.nodes.new("ShaderNodeBump")
    bp.inputs["Strength"].default_value = 0.5
    nt.links.new(n.outputs["Fac"], bp.inputs["Height"])
    return bp.outputs["Normal"]


def studio(naam):
    sc = bpy.context.scene
    L.studio_camera(sc, 0, 0, T, T, RES, RES)
    paden = L.studio_render(sc, os.path.join(L.STUDIO, "terrein_" + naam), spp=48, transparant=False)
    imgs = {}
    for m_, p in paden.items():
        img = bpy.data.images.load(p, check_existing=False)
        if m_ != "kleur":
            img.colorspace_settings.name = "Non-Color"
        imgs[m_] = L.pixels(img)[..., :3].copy()
        bpy.data.images.remove(img)
    # kleur is als sRGB gelezen -> lineair; schrijf() zet weer naar sRGB
    N = imgs["kleur"].shape[0]
    var = 0.85 + 0.3 * fbm(N, 2, 61 + len(naam), 3)
    kl = imgs["kleur"] * var[..., None]
    nr = imgs["normaal"]
    if naam == "gras":
        nr = nr * 0.55 + np.array([0.5, 0.5, 1.0]) * 0.45       # minder korrelig
    schrijf(naam, kl, nr, imgs["ruw"][..., 0])


if __name__ == "__main__":
    for n in ALLEEN:
        globals()[n]()
    L.log("KLAAR")
