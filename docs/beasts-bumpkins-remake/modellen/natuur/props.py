"""Props voor missie 1: paddenstoel, zilveren_beker, vlag, kampvuur, houtstapel, steenhoop, bron (put, latere
missies), bronplas (de spring van missie 1: kring keien om een plasje),
hek_segment, hek_paal, poort, akker_kaal, akker_rijp.

Hout en steen: tegelbare Poly Haven-sets met UV in meters; losse keien (steenhoop, kampvuur) en de
paddenstoel worden van een hoge versie gebakken (kleur/normaal/ORM). Wind/fladderen zoals de bomen
(TEXCOORD_1, zie natuur_lib). Kampvuur: emissieve gloed + Empty `vuur_bron` (deeltjes).

  blender -b -P props.py -- [alleen=bron,vlag,...]
"""
import math
import os
import random
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bmesh
import bpy
import numpy as np
from mathutils import Matrix, Vector, noise

import natuur_lib as L
from atlas import CEL

ALLE = ["paddenstoel", "zilveren_beker", "vlag", "kampvuur", "houtstapel", "steenhoop", "bron", "bronplas", "hek_segment",
        "hek_paal", "poort", "akker_kaal", "akker_rijp"]
ALLEEN = [n for n in L.OPTS.get("alleen", ",".join(ALLE)).split(",") if n]


# --- Hulpjes ------------------------------------------------------------------------------------
def draai(b, prof, seg, uvr=(0, 0, 1, 1), mat=0, punt=None, col=(0, 0, 0, 1), u_rep=1.0):
    """Omwentelingsvlak uit (r, z); uv: u rond (u_rep keer), v langs het profiel, in vak uvr."""
    u0, v0, u1, v1 = uvr
    lens = [0.0]
    for i in range(1, len(prof)):
        lens.append(lens[-1] + math.hypot(prof[i][0] - prof[i - 1][0], prof[i][1] - prof[i - 1][1]))
    tot = lens[-1] or 1
    ringen = []
    for j, (r, z) in enumerate(prof):
        ring = []
        for i in range(seg + 1):
            a = 2 * math.pi * i / seg
            p = punt(a, r, z) if punt else (r * math.cos(a), r * math.sin(a), z)
            ring.append((b.v(p, col), (u0 + (u1 - u0) * (i / seg) * u_rep, v0 + (v1 - v0) * lens[j] / tot)))
        ringen.append(ring)
    for j in range(len(prof) - 1):
        for i in range(seg):
            a, c, d, e = ringen[j][i], ringen[j][i + 1], ringen[j + 1][i + 1], ringen[j + 1][i]
            b.f([a[0], c[0], d[0], e[0]], [a[1], c[1], d[1], e[1]], mat)
    return ringen


def schijf_uv(b, ring, midden, mat, uvc=(0.5, 0.5), r_uv=0.48, omgekeerd=False, col=(0, 0, 0, 1)):
    """Dop op een ring (lijst (vi, uv)): waaiervlak met radiale UV."""
    c = b.v(midden, col)
    n = len(ring) - 1
    for k in range(n):
        va, vb = ring[k][0], ring[k + 1][0]
        a0, a1 = 2 * math.pi * k / n, 2 * math.pi * (k + 1) / n
        ua = (uvc[0] + r_uv * math.cos(a0), uvc[1] + r_uv * math.sin(a0))
        ub = (uvc[0] + r_uv * math.cos(a1), uvc[1] + r_uv * math.sin(a1))
        if omgekeerd:
            b.f([vb, va, c], [ub, ua, uvc], mat)
        else:
            b.f([va, vb, c], [ua, ub, uvc], mat)


def stam_stuk(b, p0, p1, r, mat_bast, mat_kop, zijden=10, ruw=0.0, rnd=None, kop_uv=1.0):
    """Liggend rondhout met schors en twee kopse kanten (jaarringen)."""
    P = [p0.lerp(p1, t) for t in np.linspace(0, 1, 5)]
    R = [r * (1 + (rnd.uniform(-ruw, ruw) if rnd else 0)) for _ in P]
    rr = L.buis(b, P, R, zijden=zijden, uvschaal=1 / 0.9, mat=mat_bast, u_rep=2 * math.pi * r * 1.2)
    schijf_uv(b, rr[0], P[0], mat_kop, omgekeerd=True)
    schijf_uv(b, rr[-1], P[-1], mat_kop)
    return rr


def kei_functie(seed, vlakken=10, ruis=0.16):
    rnd = random.Random(seed)
    N = [Vector((rnd.uniform(-1, 1), rnd.uniform(-1, 1), rnd.uniform(-0.6, 1))).normalized() for _ in range(vlakken)]
    D = [rnd.uniform(0.62, 0.86) for _ in N]
    off = Vector((rnd.random() * 40, rnd.random() * 40, rnd.random() * 40))

    def f(p):
        p = p.normalized()
        r = 1 + ruis * noise.noise(p * 1.4 + off) + 0.05 * noise.noise(p * 4.0 + off)
        for n, d in zip(N, D):
            dot = p.dot(n)
            if dot > 0 and r * dot > d:
                r = d / dot
        return r
    return f


def kei(naam_bm, fn, maat, plek, rot, sub):
    bm = bmesh.new()
    bmesh.ops.create_icosphere(bm, subdivisions=sub, radius=1.0)
    for v in bm.verts:
        v.co = v.co.normalized() * fn(v.co)
    M = Matrix.Translation(plek) @ Matrix.Rotation(rot, 4, "Z") @ Matrix.Diagonal((*maat, 1))
    for v in bm.verts:
        v.co = M @ v.co
        if v.co.z < plek.z - maat[2] * 0.55:
            v.co.z = plek.z - maat[2] * 0.55 + (v.co.z - (plek.z - maat[2] * 0.55)) * 0.15
    return bm


def keien_obj(naam, keien, sub, mat=None):
    """keien: [(fn, maat, plek, rot)] -> een object."""
    alles = bmesh.new()
    for fn, maat, plek, rot in keien:
        bm = kei(naam, fn, maat, plek, rot, sub)
        me = bpy.data.meshes.new("_k")
        bm.to_mesh(me)
        bm.free()
        alles.from_mesh(me)
        bpy.data.meshes.remove(me)
    me = bpy.data.meshes.new(naam)
    alles.to_mesh(me)
    alles.free()
    me.shade_smooth()
    o = L.obj(naam, me)
    if mat:
        me.materials.append(mat)
    return o


def gebakken_keien(naam, keien, res=1024, mos=0.35):
    import rotsen
    hoog = keien_obj(naam + "_hoog", keien, 5, rotsen.rotsmateriaal(naam + "_hm", mos=mos))
    laag = keien_obj(naam, keien, 2)
    laag.data.set_sharp_from_angle(angle=math.radians(80))
    L.uv_slim(laag, hoek=66, marge=0.008)
    mat = L.bak_set(naam, laag, [hoog], res=res, ext=0.04, ray=0.1, ao_min=0.3)
    laag.data.materials.append(mat)
    bpy.data.objects.remove(hoog)
    return laag


def eigen_textuur(naam, maak, data=False, jpg=True):
    pad = os.path.join(L.NTEX, naam + (".jpg" if jpg else ".png"))
    if not os.path.exists(pad):
        arr = maak()
        h, w = arr.shape[:2]
        if arr.shape[2] == 3:
            arr = np.concatenate([arr, np.ones((h, w, 1))], 2)
        img = bpy.data.images.new(naam, w, h, alpha=not jpg)
        if data:
            img.colorspace_settings.name = "Non-Color"
        img.pixels.foreach_set(np.clip(arr, 0, 1).astype(np.float32).ravel())
        img.filepath_raw = pad
        img.file_format = "JPEG" if jpg else "PNG"
        img.save()
        bpy.data.images.remove(img)
    return L.laad(pad, data=data)


def ruisveld(N, schaal, seed, oct=4):
    """Tegelbare ruis via sommen van sinussen met gehele frequenties."""
    rng = np.random.default_rng(seed)
    y, x = np.mgrid[0:N, 0:N] / N * 2 * np.pi
    out = np.zeros((N, N))
    amp = 1.0
    for o in range(oct):
        for _ in range(6):
            fx, fy = rng.integers(-schaal * 2 ** o, schaal * 2 ** o + 1, 2)
            out += amp * np.sin(fx * x + fy * y + rng.uniform(0, 6.28))
        amp *= 0.5
    return (out - out.min()) / (np.ptp(out) + 1e-9)


def normaal_uit_hoogte(h, kracht):
    gy, gx = np.gradient(h)
    n = np.stack([-gx * kracht, -gy * kracht, np.ones_like(h)], 2)
    n /= np.linalg.norm(n, axis=2, keepdims=True)
    return n * 0.5 + 0.5


def ringen_kop():
    import bomen
    return bomen.ringen_textuur()


MAT = {}


def m(naam):
    if naam in MAT:
        return MAT[naam]
    if naam == "hout":
        MAT[naam] = L.ph("rough_wood", "hout", factor=(1.0, 0.78, 0.56))
    elif naam == "planken":
        MAT[naam] = L.ph("weathered_brown_planks", "planken", factor=(1.0, 0.82, 0.62))
    elif naam == "schors":
        MAT[naam] = L.ph("pine_bark", "schors")
    elif naam == "kopshout":
        MAT[naam] = L.pbr("kopshout", ringen_kop(), ruw=0.8)
    elif naam == "steen":
        MAT[naam] = L.ph("rock_surface", "steen", factor=(1.0, 0.97, 0.9))
    elif naam == "ijzer":
        MAT[naam] = L.pbr("ijzer", (0.09, 0.085, 0.08), ruw=0.55, metaal=0.85)
    elif naam == "touw":
        MAT[naam] = L.pbr("touw", (0.78, 0.33, 0.08), ruw=0.9)
    return MAT[naam]


# --- Paddenstoel -----------------------------------------------------------------------------
def paddenstoel():
    """Eekhoorntjesbrood-achtig: bruine hoed met putjes, oranje voet; 0,36 m hoog (kaartpickup)."""
    rnd = random.Random(3)
    putjes = [Vector((rnd.uniform(-1, 1), rnd.uniform(-1, 1), rnd.uniform(0.15, 1))).normalized() for _ in range(55)]
    putr = [rnd.uniform(0.016, 0.034) for _ in putjes]

    def hoed_prof(n):
        out = []
        for i in range(n + 1):
            t = i / n                          # 0 = top, 1 = rand
            a = t * math.pi * 0.56
            out.append((0.24 * math.sin(a) * 1.05, 0.28 + 0.12 * math.cos(a)))
        out.append((0.235, 0.275))             # omkrulde rand
        out.append((0.2, 0.27))
        return out

    def hoed_punt(a, r, z):
        p = Vector((r * math.cos(a), r * math.sin(a), z))
        q = (p - Vector((0, 0, 0.26))).normalized()
        d = 0.0
        for pv, pr in zip(putjes, putr):
            ang = q.angle(pv)
            d += 0.0 * math.exp(-(ang * 0.25 / pr) ** 2)          # putjes zitten in het materiaal
        d += 0.004 * noise.noise(p * 40)
        return tuple(p - q * d)

    def voet_punt(a, r, z):
        k = 1 + 0.04 * noise.noise(Vector((math.cos(a) * 3, math.sin(a) * 3, z * 20)))
        return (r * k * math.cos(a), r * k * math.sin(a), z)
    voet = [(0.0, 0.0), (0.065, 0.0), (0.09, 0.02), (0.095, 0.07), (0.087, 0.14), (0.075, 0.21), (0.066, 0.28)]
    plaat = [(0.2, 0.27), (0.14, 0.265), (0.07, 0.275)]

    def bouw_deel(fijn):
        b = L.Bouwer()
        s = 3 if fijn else 1
        draai(b, hoed_prof(10 * s), 24 * s, uvr=(0, 0.5, 1, 1), mat=0, punt=hoed_punt)
        draai(b, voet, 16 * s, uvr=(0, 0, 0.6, 0.5), mat=1, punt=voet_punt)
        draai(b, plaat, 24 * s, uvr=(0.6, 0, 1, 0.5), mat=2)
        return b
    # hoog: procedurele materialen
    hm = L.smat("hoed_h", lambda nt: _putjes(nt, _ruiskleur(nt, (0.20, 0.075, 0.025), (0.33, 0.14, 0.05), 18)), ruw=0.55,
                normaal=lambda nt: _putjes_bump(nt))
    vm = L.smat("voet_h", lambda nt: _ruiskleur(nt, (0.48, 0.14, 0.035), (0.66, 0.27, 0.08), 60, streep=True), ruw=0.7,
                normaal=lambda nt: _bump(nt, 120, 0.4))
    pm = L.smat("plaat_h", (0.42, 0.26, 0.12), ruw=0.8, normaal=lambda nt: _bump(nt, 300, 0.6))
    for mm in (hm, vm, pm):
        STUDIO_LIT(mm)
    hoog = L.obj("_hoog", bouw_deel(True).mesh("_hoog", [hm, vm, pm]))
    laag = L.obj("paddenstoel", bouw_deel(False).mesh("paddenstoel"))
    mat = L.bak_set("paddenstoel", laag, [hoog], res=512, ext=0.01, ray=0.03, ao_min=0.35)
    laag.data.materials.append(mat)
    bpy.data.objects.remove(hoog)
    return [laag]


def STUDIO_LIT(mm):
    """Studio-materialen staan standaard op hun BSDF (modus lit) - koppel de uitgang."""
    s = L.STUDIO_MATS[mm.name]
    s["m"].node_tree.links.new(s["bsdf"].outputs[0], s["out"].inputs["Surface"])


def _ruiskleur(nt, a, b, schaal, streep=False):
    tc = nt.nodes.new("ShaderNodeTexCoord")
    n = nt.nodes.new("ShaderNodeTexNoise")
    n.inputs["Scale"].default_value = schaal
    n.inputs["Detail"].default_value = 6
    if streep:
        mp = nt.nodes.new("ShaderNodeMapping")
        mp.inputs["Scale"].default_value = (1, 1, 0.12)
        nt.links.new(tc.outputs["Object"], mp.inputs["Vector"])
        nt.links.new(mp.outputs[0], n.inputs["Vector"])
    else:
        nt.links.new(tc.outputs["Object"], n.inputs["Vector"])
    mx = nt.nodes.new("ShaderNodeMix")
    mx.data_type = "RGBA"
    nt.links.new(n.outputs["Fac"], mx.inputs["Factor"])
    mx.inputs[6].default_value = (*a, 1)
    mx.inputs[7].default_value = (*b, 1)
    # holtes donkerder
    g = nt.nodes.new("ShaderNodeNewGeometry")
    pr = nt.nodes.new("ShaderNodeMapRange")
    nt.links.new(g.outputs["Pointiness"], pr.inputs["Value"])
    pr.inputs["From Min"].default_value = 0.45
    pr.inputs["From Max"].default_value = 0.52
    pr.inputs["To Min"].default_value = 0.45
    mm = nt.nodes.new("ShaderNodeMix")
    mm.data_type = "RGBA"
    mm.blend_type = "MULTIPLY"
    mm.inputs["Factor"].default_value = 1
    nt.links.new(mx.outputs[2], mm.inputs[6])
    nt.links.new(pr.outputs[0], mm.inputs[7])
    return mm.outputs[2]


def _putjes_voronoi(nt):
    tc = nt.nodes.new("ShaderNodeTexCoord")
    vo = nt.nodes.new("ShaderNodeTexVoronoi")
    vo.inputs["Scale"].default_value = 34.0
    vo.inputs["Randomness"].default_value = 1.0
    nt.links.new(tc.outputs["Object"], vo.inputs["Vector"])
    # gat waar F1 klein is; cel-kleur bepaalt of de cel een putje heeft (ca. 40 %)
    mr = nt.nodes.new("ShaderNodeMapRange")
    nt.links.new(vo.outputs["Distance"], mr.inputs["Value"])
    mr.inputs["From Min"].default_value = 0.16
    mr.inputs["From Max"].default_value = 0.26
    sep = nt.nodes.new("ShaderNodeSeparateColor")
    nt.links.new(vo.outputs["Color"], sep.inputs["Color"])
    gt = nt.nodes.new("ShaderNodeMath")
    gt.operation = "GREATER_THAN"
    nt.links.new(sep.outputs["Red"], gt.inputs[0])
    gt.inputs[1].default_value = 0.45
    inv = nt.nodes.new("ShaderNodeMath")
    inv.operation = "SUBTRACT"
    inv.inputs[0].default_value = 1.0
    nt.links.new(mr.outputs[0], inv.inputs[1])
    mul = nt.nodes.new("ShaderNodeMath")
    mul.operation = "MULTIPLY"
    nt.links.new(inv.outputs[0], mul.inputs[0])
    nt.links.new(gt.outputs[0], mul.inputs[1])
    return mul.outputs[0]          # 1 = in een putje


def _putjes(nt, kleur):
    p = _putjes_voronoi(nt)
    mx = nt.nodes.new("ShaderNodeMix")
    mx.data_type = "RGBA"
    nt.links.new(p, mx.inputs["Factor"])
    nt.links.new(kleur, mx.inputs[6])
    mx.inputs[7].default_value = (0.05, 0.018, 0.006, 1)
    return mx.outputs[2]


def _putjes_bump(nt):
    p = _putjes_voronoi(nt)
    bp = nt.nodes.new("ShaderNodeBump")
    bp.inputs["Strength"].default_value = 0.9
    bp.inputs["Distance"].default_value = 0.01
    bp.invert = True
    nt.links.new(p, bp.inputs["Height"])
    return bp.outputs["Normal"]


def _bump(nt, schaal, kracht):
    n = nt.nodes.new("ShaderNodeTexNoise")
    n.inputs["Scale"].default_value = schaal
    bp = nt.nodes.new("ShaderNodeBump")
    bp.inputs["Strength"].default_value = kracht
    nt.links.new(n.outputs["Fac"], bp.inputs["Height"])
    return bp.outputs["Normal"]


# --- Zilveren beker --------------------------------------------------------------------------
def zilveren_beker():
    """Kelk met knoop en zes groene stenen; 0,55 m (pickup, groter dan echt voor leesbaarheid)."""
    b = L.Bouwer()   # 0 zilver, 1 steen, 2 zilver-mat (knoop)
    s = 0.55 / 0.62
    prof = [(0.0, 0.0), (0.16, 0.0), (0.17, 0.012), (0.165, 0.025), (0.13, 0.04), (0.07, 0.06), (0.045, 0.1),
            (0.035, 0.16), (0.032, 0.22), (0.05, 0.24), (0.052, 0.255)]
    prof = [(r * s, z * s) for r, z in prof]
    knoop = [(0.052 * s, 0.255 * s), (0.068 * s, 0.27 * s), (0.07 * s, 0.29 * s), (0.068 * s, 0.31 * s), (0.05 * s, 0.325 * s)]
    kelk = [(0.04 * s, 0.33 * s), (0.034 * s, 0.36 * s), (0.06 * s, 0.38 * s), (0.11 * s, 0.4 * s), (0.15 * s, 0.44 * s),
            (0.17 * s, 0.5 * s), (0.18 * s, 0.56 * s), (0.185 * s, 0.61 * s), (0.19 * s, 0.62 * s),
            (0.178 * s, 0.62 * s), (0.17 * s, 0.57 * s), (0.155 * s, 0.5 * s), (0.12 * s, 0.45 * s), (0.0, 0.43 * s)]
    draai(b, prof, 32, mat=0)
    draai(b, knoop, 32, mat=2)
    draai(b, kelk, 40, mat=0)
    # stenen met kasjes
    for k in range(6):
        a = 2 * math.pi * k / 6
        z = 0.52 * s
        r = 0.172 * s
        c = Vector((r * math.cos(a), r * math.sin(a), z))
        n = Vector((math.cos(a), math.sin(a), -0.12)).normalized()
        x, y = L.frame(n)
        # kasje: ring
        rr = 0.042 * s
        P = [c - n * 0.004, c + n * 0.01]
        ring = L.buis(b, P, [rr, rr * 0.92], zijden=12, mat=0)
        # steen: facet-koepel
        top = c + n * 0.02
        rij = []
        for i in range(9):
            t = 2 * math.pi * i / 8
            q = c + n * 0.009 + (x * math.cos(t) + y * math.sin(t)) * rr * 0.82
            rij.append(b.v(q))
        mid = []
        for i in range(9):
            t = 2 * math.pi * (i + 0.5) / 8
            q = c + n * 0.016 + (x * math.cos(t) + y * math.sin(t)) * rr * 0.5
            mid.append(b.v(q))
        tv = b.v(top)
        for i in range(8):
            b.f([rij[i], rij[i + 1], mid[i]], [(0, 0), (1, 0), (0.5, 0.5)], 1)
            b.f([mid[i], rij[i + 1], mid[(i + 1) % 8]], [(0, 0), (1, 0), (0.5, 0.5)], 1)
            b.f([mid[i], mid[(i + 1) % 8], tv], [(0, 0), (1, 0), (0.5, 1)], 1)
    zilver = L.pbr("zilver", (0.80, 0.80, 0.82), ruw=0.26, metaal=1.0)
    knoopm = L.pbr("zilver_mat", (0.70, 0.70, 0.72), ruw=0.5, metaal=1.0)
    steen = L.pbr("smaragd", (0.01, 0.32, 0.05), ruw=0.05, emissie=(0.01, 0.30, 0.04), emissie_kracht=0.8)
    me = b.mesh("zilveren_beker", [zilver, steen, knoopm])
    o = L.obj("zilveren_beker", me)
    me.set_sharp_from_angle(angle=math.radians(60))
    return [o]


# --- Vlag -----------------------------------------------------------------------------------
def vlag_textuur():
    def maak():
        N = 512
        rng = np.random.default_rng(9)
        import terrein
        h = terrein.fbm(N, 4, 1, 5)
        h = (h - h.min()) / np.ptp(h)
        h2 = terrein.fbm(N, 24, 2, 3)
        # effen paars doek, licht gesleten: zachte variatie (+-5 %) en iets verschoten naar de vrije rand
        basis = np.array([0.50, 0.14, 0.58])
        licht = np.array([0.62, 0.30, 0.68])
        y0, x0 = np.mgrid[0:N, 0:N]
        slijt = np.clip(0.5 * h2 + 0.5 * h, 0, 1) * np.clip((x0 / N - 0.35) * 1.4, 0, 1)
        c = basis * (0.95 + 0.10 * h2[..., None])
        c = c + (licht - c) * (0.45 * slijt)[..., None]
        # weefsel
        y, x = np.mgrid[0:N, 0:N]
        c *= (0.93 + 0.07 * np.sin(x * 1.6) * np.sin(y * 1.6))[..., None]
        # rafelige vrije rand (rechts) en onderrand
        a = np.ones((N, N))
        u = x / N
        v = y / N
        rafel = 0.80 + 0.14 * terrein.fbm(N, 8, 5, 4)[:, :1].repeat(N, 1)
        tand = (np.sin(v * 90) * 0.5 + 0.5) * 0.06 * terrein.fbm(N, 30, 6, 2)
        a[u > rafel - tand] = 0
        onder = 0.03 + 0.04 * ruisveld(N, 8, 7, oct=2)[:1, :].repeat(N, 0)
        a[v < onder * (u + 0.2)] = 0
        # gaatjes
        gat = ruisveld(N, 12, 11, oct=2)
        a[(gat > 0.93) & (u > 0.5)] = 0
        return np.concatenate([c, a[..., None]], 2)
    return eigen_textuur("vlag_kleur", maak, jpg=False)


def vlag():
    b = L.Bouwer()           # 0 paal, 1 doek, 2 touw
    paal_h = 2.4
    P = [Vector((0, 0, -0.1)), Vector((0.005, 0, 1.2)), Vector((0, 0.004, paal_h))]
    L.buis(b, P, [0.055, 0.05, 0.042], zijden=8, uvschaal=1 / 0.6, mat=0, dop=True)
    # doek: 18 x 12, vast aan de paal, statische golf; fladdergewicht = afstand tot de paal
    W, H, nu, nv = 1.35, 0.95, 18, 12
    z0 = paal_h - 0.05 - H
    idx = {}
    for j in range(nv + 1):
        for i in range(nu + 1):
            u, v = i / nu, j / nv
            x = 0.035 + u * W
            golf = 0.13 * u * math.sin(u * 6.0 + v * 1.5) + 0.04 * u * math.sin(v * 8 + u * 3)
            z = z0 + v * H - 0.08 * u * u
            idx[i, j] = b.v((x, golf, z), (0.0, min(0.999, u), 0.0, 1))
    for j in range(nv):
        for i in range(nu):
            b.f([idx[i, j], idx[i + 1, j], idx[i + 1, j + 1], idx[i, j + 1]],
                [(i / nu, j / nv), ((i + 1) / nu, j / nv), ((i + 1) / nu, (j + 1) / nv), (i / nu, (j + 1) / nv)], 1)
    # touwtjes
    for z in (z0 + 0.06, z0 + H - 0.04):
        for k in range(3):
            P = [Vector((0.045 * math.cos(a), 0.045 * math.sin(a), z + k * 0.012 + a * 0.002)) for a in np.linspace(0, 6.6, 12)]
            L.buis(b, P, [0.007] * 12, zijden=4, mat=2)
    doek = L.pbr("vlag_doek", vlag_textuur(), alpha=True, tweezijdig=True, ruw=0.85)
    touw = L.pbr("touw_licht", (0.62, 0.50, 0.32), ruw=0.9)
    o = L.obj("vlag", b.mesh("vlag", [m("hout"), doek, touw]))
    # vertexgroep `doek` (zelfde gewicht) voor wie liever een bot of cloth-sim gebruikt
    vg = o.vertex_groups.new(name="doek")
    for vi, c in enumerate(b.C):
        if c[1] > 0:
            vg.add([vi], c[1], "REPLACE")
    return [o]


# --- Kampvuur -----------------------------------------------------------------------------
def gloed_textuur():
    def maak():
        N = 256
        h = ruisveld(N, 4, 21)
        h2 = ruisveld(N, 14, 22, oct=2)
        y, x = np.mgrid[0:N, 0:N] / N * 2 - 1
        r = np.sqrt(x * x + y * y)
        heet = np.clip((1 - r) * 1.4, 0, 1) * (0.4 + 0.6 * h) * (0.6 + 0.4 * h2)
        heet = np.clip(heet * 1.3 - 0.15, 0, 1)
        c = np.stack([np.clip(heet * 2.0, 0, 1), np.clip(heet * 1.1 - 0.25, 0, 1) * 0.75, np.clip(heet - 0.7, 0, 1) * 0.5], 2)
        return c
    return eigen_textuur("gloed_emissie", maak)


def as_textuur():
    def maak():
        N = 256
        h = ruisveld(N, 5, 31)
        h2 = ruisveld(N, 16, 32, oct=2)
        y, x = np.mgrid[0:N, 0:N] / N * 2 - 1
        r = np.sqrt(x * x + y * y)
        c = np.array([0.08, 0.07, 0.065]) * (0.6 + 0.8 * h2[..., None])
        grijs = np.clip((r - 0.55) * 3, 0, 1)[..., None] * (0.5 + 0.5 * h[..., None])
        c = c * (1 - grijs) + np.array([0.32, 0.30, 0.28]) * grijs
        gloed = np.clip((1 - r) * 1.4, 0, 1) * (0.4 + 0.6 * h) * (0.6 + 0.4 * h2)
        c = c + np.array([0.5, 0.12, 0.02]) * np.clip(gloed * 1.3 - 0.4, 0, 1)[..., None]
        return c
    return eigen_textuur("as_kleur", maak)


def kampvuur():
    rnd = random.Random(17)
    uit = []
    # stenen ring
    keien = []
    for k in range(10):
        a = 2 * math.pi * k / 10 + rnd.uniform(-0.12, 0.12)
        r = 0.52 + rnd.uniform(-0.03, 0.03)
        sz = rnd.uniform(0.1, 0.14)
        keien.append((L_kei(rnd), (sz * 1.2, sz, sz * 0.75), Vector((r * math.cos(a), r * math.sin(a), sz * 0.45)),
                      a + rnd.uniform(-0.3, 0.3)))
    stenen = gebakken_keien("kampvuur_stenen", keien, res=512, mos=0.0)
    uit.append(stenen)
    # hout: tipi van vijf stukken + twee liggende
    b = L.Bouwer()
    houts = []
    for k in range(5):
        a = 2 * math.pi * k / 5 + rnd.uniform(-0.2, 0.2)
        voet = Vector((0.32 * math.cos(a), 0.32 * math.sin(a), 0.04))
        top = Vector((0.03 * math.cos(a + 2), 0.03 * math.sin(a + 2), 0.48 + rnd.uniform(-0.05, 0.05)))
        stam_stuk(b, voet, top, rnd.uniform(0.035, 0.05), 0, 1, zijden=8, rnd=rnd, ruw=0.1)
    for a in (0.5, 2.6):
        d = Vector((math.cos(a), math.sin(a), 0))
        stam_stuk(b, -d * 0.36 + Vector((0, 0, 0.05)), d * 0.36 + Vector((0, 0, 0.06)), 0.05, 0, 1, zijden=8)
    # houtskool: schors donkerder via een eigen materiaal (factor)
    verkoold = L.ph("pine_bark", "schors_verkoold", factor=(0.35, 0.3, 0.28))
    hout = L.obj("kampvuur_hout", b.mesh("kampvuur_hout", [verkoold, m("kopshout")]))
    uit.append(hout)
    # asbed met gloed (emissief)
    g = L.Bouwer()
    ring = []
    n = 24
    for i in range(n + 1):
        a = 2 * math.pi * i / n
        rr = 0.34 * (1 + 0.06 * math.sin(a * 5))
        ring.append((g.v((rr * math.cos(a), rr * math.sin(a), 0.012)), (0.5 + 0.5 * math.cos(a), 0.5 + 0.5 * math.sin(a))))
    c = g.v((0, 0, 0.04))
    for i in range(n):
        g.f([ring[i][0], ring[i + 1][0], c], [ring[i][1], ring[i + 1][1], (0.5, 0.5)], 0)
    # gloeiende kooltjes
    for k in range(14):
        a, r = rnd.uniform(0, 6.28), rnd.uniform(0.02, 0.22)
        p = Vector((r * math.cos(a), r * math.sin(a), 0.04))
        s = rnd.uniform(0.02, 0.035)
        v = [g.v(p + Vector((dx * s, dy * s, dz * s))) for dx, dy, dz in
             ((1, 0, 0), (0, 1, 0), (-1, 0, 0), (0, -1, 0), (0, 0, 0.8))]
        for i in range(4):
            g.f([v[i], v[(i + 1) % 4], v[4]], [(0.5, 0.5), (0.55, 0.5), (0.5, 0.55)], 0)
    gloed = L.pbr("gloed", as_textuur(), ruw=0.95, emissie=gloed_textuur(), emissie_kracht=3.0)
    asbed = L.obj("kampvuur_gloed", g.mesh("kampvuur_gloed", [gloed]))
    uit.append(asbed)
    # vlammen: drie gekruiste emissieve kaarten (vervangbaar door deeltjes op vuur_bron)
    v = L.Bouwer()
    for k in range(3):
        a = k * math.pi / 3
        w = Vector((math.cos(a), math.sin(a), 0))
        L.kaart(v, Vector((0, 0, 0.03)), Vector((0, 0, 1)), w, 0.75, 0.5, (0, 0, 1, 1), (0, 0, 0, 1), (0, 1, 0.3 * k, 1),
                seg=2, mat=0)
    vt = vlam_textuur()
    vm = L.pbr("vlam", vt, alpha=True, tweezijdig=True, ruw=1.0, emissie=vt, emissie_kracht=6.0)
    vo = L.obj("kampvuur_vlam", v.mesh("kampvuur_vlam", [vm]))
    uit.append(vo)
    e = bpy.data.objects.new("vuur_bron", None)
    e.empty_display_type = "SPHERE"
    e.empty_display_size = 0.15
    e.location = (0, 0, 0.22)
    bpy.context.scene.collection.objects.link(e)
    wortel = bpy.data.objects.new("kampvuur", None)
    bpy.context.scene.collection.objects.link(wortel)
    for o in uit + [e]:
        o.parent = wortel
    return [wortel]


def vlam_textuur():
    def maak():
        import terrein
        N = 256
        y, x = np.mgrid[0:N, 0:N] / N
        r = terrein.fbm(N, 6, 51, 4)
        u = (x - 0.5) * 2
        breed = 0.75 * (1 - y) ** 0.7 * (0.6 + 0.4 * np.sin(y * 3.1))
        vorm = 1 - np.abs(u + 0.25 * (r - 0.5) * y * 2) / np.maximum(breed, 1e-3)
        a = np.clip(vorm * 3 + (r - 0.5) * 1.5, 0, 1) * (y < 0.97) * (1 - np.clip((y - 0.6) * 2.5 * (1.2 - r), 0, 1))
        heet = np.clip(vorm * 1.6, 0, 1) * (1 - y * 0.6)
        c = np.stack([np.ones_like(heet) * 0.95, 0.25 + 0.6 * heet, 0.02 + 0.35 * heet ** 3], 2)
        return np.concatenate([c, (a > 0.45)[..., None].astype(float)], 2)
    return eigen_textuur("vlam_kleur", maak, jpg=False)


def L_kei(rnd):
    return kei_functie(rnd.randrange(10000))


# --- Houtstapel, steenhoop ----------------------------------------------------------------------
def houtstapel():
    rnd = random.Random(5)
    b = L.Bouwer()
    r = 0.17
    lengte = 2.2
    pos = [(-2 * r, r), (0, r), (2 * r, r), (-r, r + 1.73 * r), (r, r + 1.73 * r)]
    for (y, z) in pos:
        dx = rnd.uniform(-0.08, 0.08)
        rr = r * rnd.uniform(0.93, 1.03)
        p0 = Vector((-lengte / 2 + dx, y * 1.02, z))
        p1 = Vector((lengte / 2 + dx + rnd.uniform(-0.05, 0.05), y * 1.02 + rnd.uniform(-0.02, 0.02), z))
        stam_stuk(b, p0, p1, rr, 0, 1, zijden=14, rnd=rnd, ruw=0.03)
    o = L.obj("houtstapel", b.mesh("houtstapel", [m("schors"), m("kopshout")]))
    o.data.set_sharp_from_angle(angle=math.radians(50))
    return [o]


def steenhoop():
    rnd = random.Random(23)
    keien = []
    for k in range(16):
        a = rnd.uniform(0, 6.28)
        r = rnd.uniform(0.35, 0.8) if k > 3 else rnd.uniform(0, 0.3)
        sz = rnd.uniform(0.22, 0.34) if k > 3 else rnd.uniform(0.36, 0.46)
        z = sz * 0.45 + (0.25 if k < 4 else 0.0)
        keien.append((L_kei(rnd), (sz * rnd.uniform(1.0, 1.3), sz, sz * rnd.uniform(0.75, 0.95)),
                      Vector((r * math.cos(a), r * math.sin(a), z)), rnd.uniform(0, 6.28)))
    for k in range(3):   # bovenop
        a = rnd.uniform(0, 6.28)
        sz = rnd.uniform(0.3, 0.38)
        keien.append((L_kei(rnd), (sz * 1.2, sz, sz * 0.85), Vector((0.2 * math.cos(a), 0.2 * math.sin(a), 0.75)),
                      rnd.uniform(0, 6.28)))
    o = gebakken_keien("steenhoop", keien, res=1024, mos=0.1)
    return [o]


# --- Bron ---------------------------------------------------------------------------------
def dakpan_textuur():
    def maak():
        src = L.laad(os.path.join(L.TEX, "clay_roof_tiles_diff_1k.jpg"))
        p = L.pixels(src)[..., :3]
        lum = (p * np.array([0.3, 0.55, 0.15])).sum(2, keepdims=True)
        paars = np.array([0.46, 0.08, 0.62])
        return np.clip(lum * paars * 4.0, 0, 1)
    return eigen_textuur("dakpan_paars_kleur", maak)


def water_normaal():
    def maak():
        N = 512
        h = ruisveld(N, 3, 41) + 0.5 * ruisveld(N, 9, 42, oct=2)
        return normaal_uit_hoogte(h, 6.0)
    return eigen_textuur("water_normaal", maak, data=True)


def steen_licht():
    def maak():
        src = L.laad(os.path.join(L.TEX, "rock_surface_diff_1k.jpg"))
        p = L.pixels(src)[..., :3]
        lum = (p * np.array([0.3, 0.59, 0.11])).sum(2, keepdims=True)
        grijs = lum * np.array([1.0, 0.98, 0.93])
        return np.clip((0.35 * p + 0.65 * grijs) * 1.55, 0, 1)
    return eigen_textuur("steen_licht_kleur", maak)


def steen_licht_mat(naam):
    return L.pbr(naam, steen_licht(), L.laad(os.path.join(L.TEX, "rock_surface_nor_gl_1k.jpg"), data=True),
                 L.orm_van("rock_surface"))


def blok_rij(b, rnd, p0, p1, z, h, diep, mat, lengte=0.42, uvs=1 / 1.2, buiten=None):
    """Rij afgekante blokken van p0 naar p1 op hoogte z (onderkant), hoogte h, diepte diep."""
    d = p1 - p0
    L_ = d.length
    if L_ < 1e-4:
        return
    dn = d.normalized()
    n = max(1, round(L_ / lengte))
    hoek = math.atan2(dn.y, dn.x)
    stuk = L_ / n
    for k in range(n):
        c = p0 + dn * (stuk * (k + 0.5))
        l = stuk - 0.012
        bm = L.blok((l * rnd.uniform(0.97, 1.0), diep * rnd.uniform(0.95, 1.02), h * rnd.uniform(0.93, 1.0)),
                    afkant=min(0.025, h * 0.15), seg=1)
        M = Matrix.Translation(Vector((c.x, c.y, z + h / 2))) @ Matrix.Rotation(hoek + rnd.uniform(-0.02, 0.02), 4, "Z")
        L.bm_naar_bouwer(bm, b, mat=mat, uvschaal=uvs, M=M @ Matrix.Translation(Vector((rnd.uniform(-2, 2), rnd.uniform(-2, 2), 0)) * 0) )
        bm.free()


def ring_blokken(b, rnd, punten, z, h, diep, mat, lengte=0.42, verspring=0.0):
    for i in range(len(punten)):
        p0, p1 = punten[i], punten[(i + 1) % len(punten)]
        d = (p1 - p0).normalized()
        blok_rij(b, rnd, p0 + d * verspring, p1 + d * verspring, z, h, diep, mat, lengte)


def bron():
    """Bronhuisje met paars pannendak op een getrapte sokkel, in een veelhoekig bassin; ca. 5 x 4,6 m."""
    rnd = random.Random(31)
    b = L.Bouwer()       # 0 steen, 1 dak, 2 planken, 3 ijzer, 4 wit, 5 rand-steen
    # bassin (concept: veelhoek met een inham linksvoor)
    poly = [(2.3, 1.2), (1.2, 2.3), (-1.0, 2.3), (-2.3, 1.0), (-2.3, -0.4), (-1.5, -0.4), (-1.5, -1.6), (-0.6, -2.4),
            (1.2, -2.4), (2.3, -1.3)]
    poly = [Vector((x, y, 0)) for x, y in poly]
    for laag in range(2):
        ring_blokken(b, rnd, poly, -0.05 + laag * 0.24, 0.24, 0.3, 0, lengte=0.45, verspring=0.12 * laag)
    # bodem en water
    w = L.Bouwer()
    c = w.v((0, 0, 0.3))
    n = len(poly)
    ring = [w.v((p.x * 0.97, p.y * 0.97, 0.3)) for p in poly]
    for i in range(n):
        p, q = poly[i], poly[(i + 1) % n]
        w.f([ring[i], ring[(i + 1) % n], c], [(p.x / 2, p.y / 2), (q.x / 2, q.y / 2), (0, 0)], 0)
    # sokkel: drie treden (vierkant om het huisje)
    hx, hy = 0.35, 0.35
    for t, (half, z0) in enumerate(((1.35, 0.0), (1.1, 0.25), (0.88, 0.5))):
        pts = [Vector((hx + sx * half, hy + sy * half, 0)) for sx, sy in ((1, 1), (-1, 1), (-1, -1), (1, -1))]
        ring_blokken(b, rnd, pts, z0, 0.25, 0.5, 0, lengte=0.5, verspring=0.15 * t)
        # bovenvlak van de trede
        doos = L.blok((half * 2 - 0.3, half * 2 - 0.3, 0.05), afkant=0)
        L.bm_naar_bouwer(doos, b, mat=0, uvschaal=1 / 1.2, M=Matrix.Translation(Vector((hx, hy, z0 + 0.22))))
        doos.free()
    # huisje: wanden 1,4 x 1,4, 1,55 hoog, van blokken in lagen; openingen voor deur (-x) en tuit (-y)
    half, z0, zh = 0.7, 0.75, 1.55
    laagh = 0.22
    lagen = int(zh / laagh)
    hoeken = [Vector((hx + sx * half, hy + sy * half, 0)) for sx, sy in ((1, 1), (-1, 1), (-1, -1), (1, -1))]
    for k in range(lagen):
        z = z0 + k * laagh
        for i in range(4):
            p0, p1 = hoeken[i], hoeken[(i + 1) % 4]
            d = (p1 - p0).normalized()
            off = 0.13 if k % 2 else 0.0
            open_ = None
            if i == 1 and z < z0 + 1.15:         # -x-wand: deur
                open_ = 0.38
            if i == 2 and z < z0 + 1.15 and z >= z0 + 0.0:   # -y-wand: witte nis
                open_ = 0.34
            if open_:
                m_ = (p0 + p1) / 2
                blok_rij(b, rnd, p0 + d * off * 0, m_ - d * open_, z, laagh, 0.3, 0, lengte=0.36)
                blok_rij(b, rnd, m_ + d * open_, p1, z, laagh, 0.3, 0, lengte=0.36)
            else:
                blok_rij(b, rnd, p0 + d * off, p1 + d * off * 0, z, laagh, 0.3, 0, lengte=0.42)
    # bogen boven deur en nis (voegstenen in een halve cirkel)
    for i, br in ((1, 0.38), (2, 0.34)):
        p0, p1 = hoeken[i], hoeken[(i + 1) % 4]
        d = (p1 - p0).normalized()
        nrm = Vector((d.y, -d.x, 0))
        m_ = (p0 + p1) / 2
        zc = z0 + 1.1
        for k in range(7):
            a0 = math.pi * k / 7
            a1 = math.pi * (k + 1) / 7
            am = (a0 + a1) / 2
            c = m_ + d * (math.cos(am) * (br + 0.08)) + Vector((0, 0, zc + math.sin(am) * (br + 0.08)))
            bm = L.blok((0.18, 0.34, 0.15), afkant=0.02)
            M = Matrix.Translation(c) @ Matrix.Rotation(math.atan2(d.y, d.x), 4, "Z") @ Matrix.Rotation(-(am - math.pi / 2), 4, "Y")
            L.bm_naar_bouwer(bm, b, mat=5, uvschaal=1 / 1.2, M=M)
            bm.free()
    # deur (-x-wand)
    p0, p1 = hoeken[1], hoeken[2]
    d = (p1 - p0).normalized()
    m_ = (p0 + p1) / 2
    for k in range(4):
        x = -0.36 + 0.18 * k + 0.09
        bm = L.blok((0.17, 0.05, 1.3), afkant=0.01)
        c = m_ + d * x + Vector((0.05, 0, z0 + 0.65))
        L.bm_naar_bouwer(bm, b, mat=2, uvschaal=1 / 1.0, M=Matrix.Translation(c) @ Matrix.Rotation(math.atan2(d.y, d.x), 4, "Z"))
        bm.free()
    # deur: bovenkant rond (halve schijf van planken)
    for k in range(6):
        a0, a1 = math.pi * k / 6, math.pi * (k + 1) / 6
        q = [m_ + Vector((0.025, 0, 0)) + d * (math.cos(a) * 0.36) + Vector((0, 0, z0 + 1.3 + math.sin(a) * 0.3)) for a in (a0, a1)]
        cc = m_ + Vector((0.025, 0, z0 + 1.3))
        vi = [b.v(q[0]), b.v(q[1]), b.v(cc)]
        b.f([vi[1], vi[0], vi[2]], [(q[1].y, q[1].z), (q[0].y, q[0].z), (cc.y, cc.z)], 2)
    for z in (z0 + 0.3, z0 + 1.0):            # hengsels
        bm = L.blok((0.5, 0.015, 0.06), afkant=0.003)
        c = m_ + d * 0.1 + Vector((0.08, 0, z))
        L.bm_naar_bouwer(bm, b, mat=3, M=Matrix.Translation(c) @ Matrix.Rotation(math.atan2(d.y, d.x), 4, "Z"))
        bm.free()
    bm = L.blok((0.03, 0.06, 0.12), afkant=0.005)  # slot
    L.bm_naar_bouwer(bm, b, mat=3, M=Matrix.Translation(m_ + d * -0.22 + Vector((0.08, 0, z0 + 0.7))))
    bm.free()
    # witte nis met tuit (-y-wand)
    p0, p1 = hoeken[2], hoeken[3]
    d = (p1 - p0).normalized()
    m_ = (p0 + p1) / 2
    nis = L.blok((0.66, 0.08, 1.12), afkant=0.02)
    L.bm_naar_bouwer(nis, b, mat=4, uvschaal=1.0, M=Matrix.Translation(m_ + Vector((0, 0.06, z0 + 0.56))))
    nis.free()
    for k in range(8):
        a0, a1 = math.pi * k / 8, math.pi * (k + 1) / 8
        q = [m_ + Vector((0, 0.02, 0)) + d * (math.cos(a) * 0.34) + Vector((0, 0, z0 + 1.1 + math.sin(a) * 0.3)) for a in (a0, a1)]
        cc = m_ + Vector((0, 0.02, z0 + 1.1))
        vi = [b.v(q[0]), b.v(q[1]), b.v(cc)]
        b.f([vi[0], vi[1], vi[2]], [(q[0].x, q[0].z), (q[1].x, q[1].z), (cc.x, cc.z)], 4)
    tuit_z = z0 + 0.45
    P = [m_ + Vector((0, 0.05, tuit_z)), m_ + Vector((0, -0.25, tuit_z - 0.02))]
    rr = L.buis(b, P, [0.12, 0.11], zijden=14, mat=4)
    # dakrand (steen) en schilddak met paarse pannen
    zr = z0 + lagen * laagh
    rand = L.blok((half * 2 + 0.36, half * 2 + 0.36, 0.14), afkant=0.03)
    L.bm_naar_bouwer(rand, b, mat=5, uvschaal=1 / 1.2, M=Matrix.Translation(Vector((hx, hy, zr + 0.07))))
    rand.free()
    dh, ov = 0.95, 0.32
    top = b.v((hx, hy, zr + 0.14 + dh))
    hk = [Vector((hx + sx * (half + ov), hy + sy * (half + ov), zr + 0.16)) for sx, sy in ((1, 1), (-1, 1), (-1, -1), (1, -1))]
    hv = [b.v(p) for p in hk]
    for i in range(4):
        p, q = hk[i], hk[(i + 1) % 4]
        lang = (q - p).length
        hoogte = math.hypot(dh, half + ov)
        b.f([hv[i], hv[(i + 1) % 4], top], [(0, 0), (lang / 1.0, 0), (lang / 2.0, hoogte / 1.0)], 1)
    # nokken (stenen ribbels langs de graten)
    for i in range(4):
        p = hk[i]
        q = Vector((hx, hy, zr + 0.14 + dh))
        Q = [p.lerp(q, t) + Vector((0, 0, 0.03)) for t in np.linspace(0, 1, 6)]
        L.buis(b, Q, [0.045] * 6, zijden=6, mat=1)
    # waterstraal (doorzichtig, met fladder-uv voor een golvende shader)
    s = L.Bouwer()
    start = m_ + Vector((0, -0.3, tuit_z))
    for j in range(10):
        t0, t1 = j / 10, (j + 1) / 10
        def pt(t, k):
            y = -0.3 - t * 0.55
            z = tuit_z - 0.02 - (t ** 2) * (tuit_z - 0.3) - t * 0.05
            return Vector((m_.x + k * (0.11 + t * 0.05), m_.y + y, z))
        a, bb, c2, d2 = pt(t0, -1), pt(t0, 1), pt(t1, 1), pt(t1, -1)
        vi = [s.v(a, (0, t0, 0, 1)), s.v(bb, (0, t0, 0, 1)), s.v(c2, (0, t1, 0, 1)), s.v(d2, (0, t1, 0, 1))]
        s.f(vi, [(0, t0 * 2), (1, t0 * 2), (1, t1 * 2), (0, t1 * 2)], 0)
    # materialen
    steen = steen_licht_mat("bronsteen")
    dak = L.pbr("dakpan_paars", dakpan_textuur(), L.laad(os.path.join(L.TEX, "clay_roof_tiles_nor_gl_1k.jpg"), data=True),
                L.orm_van("clay_roof_tiles", ruw_plus=-0.2), ruw=0.5)
    wit = L.pbr("wit_pleister", (0.86, 0.85, 0.82), ruw=0.8)
    huis = L.obj("bron", b.mesh("bron", [steen, dak, m("planken"), m("ijzer"), wit, steen]))
    huis.data.set_sharp_from_angle(angle=math.radians(45))
    wn = water_normaal()
    water = L.pbr("water", (0.02, 0.05, 0.12), nrm=wn, ruw=0.06, alfa_waarde=0.82, blend=True)
    wo = L.obj("bron_water", w.mesh("bron_water", [water]))
    straal_m = L.pbr("waterstraal", (0.72, 0.80, 0.86), nrm=wn, ruw=0.05, alfa_waarde=0.8, blend=True, tweezijdig=True)
    so = L.obj("bron_straal", s.mesh("bron_straal", [straal_m]))
    for o in (wo, so):
        o.parent = huis
    return [huis]


def bronplas():
    """De spring (klasse 144) van missie 1: een kring van ~14 keien om een ondiep plasje, buiten ~2 m
    (een tegel). Geen gebouw: het bronhuisje (`bron`) is de put (well, klasse 47/118) van latere missies."""
    rnd = random.Random(144)
    keien = []
    n = 14
    for k in range(n):
        a = 2 * math.pi * k / n + rnd.uniform(-0.08, 0.08)
        r = 0.78 + rnd.uniform(-0.05, 0.05)
        sz = rnd.uniform(0.16, 0.23)
        keien.append((L_kei(rnd), (sz * rnd.uniform(1.1, 1.4), sz, sz * rnd.uniform(0.6, 0.8)),
                      Vector((r * math.cos(a), r * math.sin(a), sz * 0.3)), a + rnd.uniform(-0.3, 0.3)))
    for k in range(4):   # een paar kleine erbij, ongelijk
        a = rnd.uniform(0, 2 * math.pi)
        sz = rnd.uniform(0.09, 0.13)
        keien.append((L_kei(rnd), (sz * 1.2, sz, sz * 0.7), Vector((0.98 * math.cos(a), 0.98 * math.sin(a), sz * 0.25)),
                      rnd.uniform(0, 6.28)))
    o = gebakken_keien("bronplas", keien, res=512, mos=0.15)
    w = L.Bouwer()
    c = w.v((0, 0, 0.07))
    seg = 24
    ring = [w.v((0.74 * math.cos(2 * math.pi * i / seg), 0.74 * math.sin(2 * math.pi * i / seg), 0.07)) for i in range(seg)]
    for i in range(seg):
        a0, a1 = 2 * math.pi * i / seg, 2 * math.pi * (i + 1) / seg
        w.f([ring[i], ring[(i + 1) % seg], c], [(0.5 + 0.5 * math.cos(a0), 0.5 + 0.5 * math.sin(a0)),
                                                (0.5 + 0.5 * math.cos(a1), 0.5 + 0.5 * math.sin(a1)), (0.5, 0.5)], 0)
    water = L.pbr("water", (0.03, 0.08, 0.14), nrm=water_normaal(), ruw=0.06, alfa_waarde=0.85, blend=True)
    wo = L.obj("bronplas_water", w.mesh("bronplas_water", [water]))
    wo.parent = o
    return [o]


# --- Hek en poort ------------------------------------------------------------------------------
def paal(b, rnd, p, h, r=0.09):
    P = [p, p + Vector((rnd.uniform(-0.01, 0.01), rnd.uniform(-0.01, 0.01), h))]
    rr = L.buis(b, [P[0], P[0].lerp(P[1], 0.5), P[1]], [r, r * 0.98, r * 0.95], zijden=10, uvschaal=1 / 0.8, mat=0,
                u_rep=2 * math.pi * r * 1.2)
    schijf_uv(b, rr[-1], P[1] + Vector((0, 0, 0.015)), 1)


def touwrol(b, c, as_, r, breed, winden=5):
    x, y = L.frame(as_)
    P = []
    for i in range(winden * 10 + 1):
        a = 2 * math.pi * i / 10
        t = i / (winden * 10)
        P.append(c + as_ * (breed * (t - 0.5)) + (x * math.cos(a) + y * math.sin(a)) * r)
    L.buis(b, P, [0.024] * len(P), zijden=5, mat=2)
    # kruiswikkeling
    for s in (-1, 1):
        Q = [c + as_ * (breed * 0.5 * s * (1 - 2 * t)) + (x * math.cos(t * 3) + y * math.sin(t * 3)) * (r + 0.012) for t in np.linspace(0, 1, 12)]
        L.buis(b, Q, [0.02] * 12, zijden=5, mat=2)


def hek_segment():
    """2 m tussen de palen (tegelmaat), twee regels, oranje touw om de kruisingen; palen op x = 0 en 2."""
    rnd = random.Random(2)
    b = L.Bouwer()
    for x in (-1.0, 1.0):
        paal(b, rnd, Vector((x, 0, -0.05)), 1.1, r=0.13)
    for z in (0.45, 0.85):
        p0, p1 = Vector((-1.12, 0.1, z)), Vector((1.12, 0.1, z + rnd.uniform(-0.03, 0.03)))
        rr = L.buis(b, [p0, p0.lerp(p1, 0.5) + Vector((0, 0, -0.015)), p1], [0.085, 0.082, 0.085], zijden=8,
                    uvschaal=1 / 0.8, mat=0, u_rep=0.45)
        schijf_uv(b, rr[0], p0, 1, omgekeerd=True)
        schijf_uv(b, rr[-1], p1, 1)
        for x in (-1.0, 1.0):
            touwrol(b, Vector((x, 0.05, z)), Vector((0, 0, 1)), 0.15, 0.2, winden=4)
    o = L.obj("hek_segment", b.mesh("hek_segment", [m("hout"), m("kopshout"), m("touw")]))
    o.data.set_sharp_from_angle(angle=math.radians(50))
    return [o]


def hek_paal():
    rnd = random.Random(4)
    b = L.Bouwer()
    paal(b, rnd, Vector((0, 0, -0.05)), 1.05, r=0.14)
    o = L.obj("hek_paal", b.mesh("hek_paal", [m("hout"), m("kopshout")]))
    o.data.set_sharp_from_angle(angle=math.radians(50))
    return [o]


def poort():
    """Stenen pijlers met een houten deur en blauwe steen; doorgang 2 m (tegelmaat), langs x."""
    rnd = random.Random(8)
    b = L.Bouwer()          # 0 steen, 1 planken, 2 ijzer, 3 blauwe steen
    for x in (-1.25, 1.25):
        # taps toelopende pijler uit blokken
        for k in range(6):
            z = k * 0.3
            w = 0.62 - k * 0.04
            bm = L.blok((w, w, 0.3), afkant=0.03)
            L.bm_naar_bouwer(bm, b, mat=0, uvschaal=1 / 1.2,
                             M=Matrix.Translation(Vector((x + rnd.uniform(-0.01, 0.01), rnd.uniform(-0.01, 0.01), z + 0.15)))
                             @ Matrix.Rotation(rnd.uniform(-0.03, 0.03), 4, "Z"))
            bm.free()
        kap = L.blok((0.58, 0.58, 0.2), afkant=0.05, seg=2)
        L.bm_naar_bouwer(kap, b, mat=0, uvschaal=1 / 1.2, M=Matrix.Translation(Vector((x, 0, 1.9))))
        kap.free()
    # deur: verticale planken met ijzeren banden, een eigen object `poort_deur` met het scharnier op x = -0.95
    # (lokale oorsprong), zodat het spel hem open kan draaien (om lokaal Z in Blender = lokaal Y in Godot)
    d = L.Bouwer()          # 0 planken, 1 ijzer, 2 blauwe steen
    H = 0.95
    for k in range(10):
        x = -0.95 + 0.19 * k + 0.095
        h = 1.45 + 0.08 * math.sin(k * 0.9)
        bm = L.blok((0.185, 0.07, h), afkant=0.01)
        L.bm_naar_bouwer(bm, d, mat=0, uvschaal=1.0, M=Matrix.Translation(Vector((x + H, 0, 0.12 + h / 2))))
        bm.free()
    for z in (0.35, 1.2):
        bm = L.blok((1.9, 0.02, 0.08), afkant=0.005)
        L.bm_naar_bouwer(bm, d, mat=1, M=Matrix.Translation(Vector((H, -0.045, z))))
        bm.free()
    # beslag met blauwe steen in het midden (beide kanten)
    for kant in (-1, 1):
        P = [Vector((H, kant * 0.04, 0.8)), Vector((H, kant * 0.07, 0.8))]
        rr = L.buis(d, P, [0.16, 0.13], zijden=4, mat=1)
        schijf_uv(d, rr[-1], P[-1], 1, omgekeerd=kant < 0)
        bm = bmesh.new()
        bmesh.ops.create_uvsphere(bm, u_segments=16, v_segments=8, radius=0.075)
        L.bm_naar_bouwer(bm, d, mat=2, M=Matrix.Translation(Vector((H, kant * 0.085, 0.8))) @ Matrix.Diagonal((1, 0.6, 1, 1)))
        bm.free()
    blauw = L.pbr("blauwe_steen", (0.05, 0.18, 0.75), ruw=0.08, emissie=(0.02, 0.08, 0.4), emissie_kracht=0.8)
    o = L.obj("poort", b.mesh("poort", [steen_licht_mat("poortsteen"), m("planken"), m("ijzer"), blauw]))
    o.data.set_sharp_from_angle(angle=math.radians(40))
    do = L.obj("poort_deur", d.mesh("poort_deur", [m("planken"), m("ijzer"), blauw]))
    do.data.set_sharp_from_angle(angle=math.radians(40))
    do.parent = o
    do.location = (-H, 0, 0)
    # een paar keien met mos aan de voet van de pijlers (gebakken)
    keien = []
    for x in (-1.25, 1.25):
        for k in range(3):
            sz = rnd.uniform(0.2, 0.32)
            a = rnd.uniform(0, 6.28)
            keien.append((L_kei(rnd), (sz * 1.2, sz, sz * 0.8),
                          Vector((x + 0.42 * math.cos(a), 0.42 * math.sin(a), sz * 0.35)), rnd.uniform(0, 6)))
    ko = gebakken_keien("poort_keien", keien, res=512, mos=0.6)
    ko.parent = o
    return [o]


# --- Akker --------------------------------------------------------------------------------------
def akker_grond(naam, n=56):
    """2 x 2 m, vier ruggen langs x; rand 6 cm boven het terrein met een schuine kant."""
    b = L.Bouwer()
    off = Vector((3.1, 1.7, 0))
    idx = {}
    for j in range(n + 1):
        for i in range(n + 1):
            x = -1 + 2 * i / n
            y = -1 + 2 * j / n
            rug = 0.5 + 0.5 * math.cos((y + 1) / 2 * 4 * 2 * math.pi + math.pi)
            z = 0.05 + 0.15 * rug ** 0.8 + 0.02 * noise.noise(Vector((x * 5, y * 5, 0)) + off)                 + 0.008 * noise.noise(Vector((x * 18, y * 18, 0)) + off)
            rand = max(abs(x), abs(y))
            if rand > 0.94:
                z *= max(0.0, (1 - rand) / 0.06)
            idx[i, j] = b.v((x, y, z))
    for j in range(n):
        for i in range(n):
            q = [idx[i, j], idx[i + 1, j], idx[i + 1, j + 1], idx[i, j + 1]]
            b.f(q, [(b.V[k][0] / 1.0, b.V[k][1] / 1.0) for k in q], 0)
    grond = L.ph("farm_soil", "akkergrond", factor=(0.8, 0.72, 0.66))
    o = L.obj(naam, b.mesh(naam, [grond]))
    L.decimeer(o, 0.45)
    return o


def akker_kaal():
    return [akker_grond("akker_kaal")]


def akker_rijp():
    rnd = random.Random(12)
    g = akker_grond("akker_rijp")
    b = L.Bouwer()      # 0 tarwe, 1 blad
    tw = CEL["tarwe"][1]
    bl = CEL["akker_blad"][1]
    for rij in range(4):
        y = -1 + (rij + 0.5) * 0.5
        for k in range(18):
            x = -0.92 + 1.84 * (k + rnd.uniform(0.1, 0.9)) / 18
            p = Vector((x, y + rnd.uniform(-0.08, 0.08), 0.1))
            h = rnd.uniform(0.85, 1.05)
            a0 = rnd.uniform(0, math.pi)
            fase = rnd.random()
            for q in range(3):     # drie gekruiste kaarten
                a = a0 + q * math.pi / 3
                w = Vector((math.cos(a), math.sin(a), 0))
                d = Vector((rnd.uniform(-0.08, 0.08), rnd.uniform(-0.08, 0.08), 1)).normalized()
                L.kaart(b, p - Vector((0, 0, 0.03)), d, w, h, h * 0.75, tw, (0, 0.0, fase, 1), (0, 1.0, fase, 1),
                        buig=0.04, seg=2, mat=0)
            if k % 2 == 0:
                for q in range(2):
                    a = a0 + 0.8 + q * math.pi / 2
                    w = Vector((math.cos(a), math.sin(a), 0))
                    L.kaart(b, p - Vector((0, 0, 0.04)), Vector((0, 0, 1)), w, 0.4, 0.75, bl, (0, 0.0, fase, 1),
                            (0, 0.6, fase, 1), seg=1, mat=1)
    ak = L.laad(os.path.join(L.NTEX, "akker_atlas_kleur.png"))
    an = L.laad(os.path.join(L.NTEX, "akker_atlas_normaal.jpg"), data=True)
    tarwe = L.pbr("tarwe", ak, an, alpha=True, tweezijdig=True, ruw=0.7, factor=(1, 1, 1))
    blad = L.pbr("akker_blad", ak, an, alpha=True, tweezijdig=True, ruw=0.6, factor=(1, 1, 1))
    o = L.obj("akker_rijp_gewas", b.mesh("akker_rijp_gewas", [tarwe, blad]))
    o.parent = g
    return [g]


def bouw(naam):
    L.leeg()
    MAT.clear()
    objs = globals()[naam]()
    alle = objs + [c for o in objs for c in o.children_recursive]
    L.exporteer(os.path.join(L.HERE, naam + ".glb"), objs)
    return {naam: L.tris([o for o in alle if o.type == "MESH"])}


if __name__ == "__main__":
    import json
    stat = {}
    for n in ALLEEN:
        stat.update(bouw(n))
        L.log(n, stat[n])
    p = os.path.join(L.HERE, "_tris.json")
    oud = json.load(open(p)) if os.path.exists(p) else {}
    oud.update(stat)
    json.dump(oud, open(p, "w"), indent=1, sort_keys=True)
    L.log("KLAAR", stat)
