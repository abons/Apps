"""Kaartatlassen voor het gebladerte: naalden, blad, tarwe (Cycles-studio, bovenaanzicht).

Elke cel wordt als echte geometrie gebouwd (twijgen, naalden, blaadjes, aren) en van boven
gerenderd in drie modi (kleur x AO, normaal, ruwheid); daarna in een atlas gezet en de lege
pixels gedilateerd (anders donkere randen in de mips).

Kleur is bewust NEUTRAAL (bleek geelgroen): de tint komt uit baseColorFactor, zodat seizoenen
alleen de factor wisselen. Bloemen en tarwe zijn wel op kleur (hun materiaal heeft factor wit).

  blender -b -P kaarten.py -- [res=1024] [alleen=naald,blad,akker]
Schrijft textures/{naald,blad,akker}_atlas_{kleur,normaal}.png.
"""
import math
import os
import random
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bpy
import numpy as np
from mathutils import Matrix, Vector, noise

import natuur_lib as L
from atlas import ATLAS, CEL

RES = int(L.OPTS.get("res", 1024))
ALLEEN = set(L.OPTS.get("alleen", "naald,blad,akker").split(","))


# --- Geometrie ---------------------------------------------------------------------------
def naald(b, p, d, lengte, breedte, var, mat=0):
    """Platte naald (twee driehoeken, punt), d = richting."""
    d = Vector(d).normalized()
    x, y = L.frame(d)
    w = x * breedte * 0.5
    q = p + d * lengte
    c = (var, 0, 0, 1)
    a, bb, m, t = b.v(p - w, c), b.v(p + w, c), b.v(p + d * lengte * 0.5 + w * 0.8, c), b.v(q, c)
    m2 = b.v(p + d * lengte * 0.5 - w * 0.8, c)
    b.f([a, bb, m, t, m2], [(0, 0), (1, 0), (1, 0.5), (0.5, 1), (0, 0.5)], mat)


def twijg_pad(p0, d, lengte, n, kromming=0.0, zak=0.0, seed=0):
    rnd = random.Random(seed)
    P = []
    d = Vector(d).normalized()
    zij = Vector((-d.y, d.x, 0))
    for i in range(n + 1):
        t = i / n
        p = p0 + d * lengte * t + zij * kromming * lengte * t * t + Vector((0, 0, -zak * t * t))
        p += Vector((rnd.uniform(-1, 1), rnd.uniform(-1, 1), 0)) * 0.003
        P.append(p)
    return P


def naaldtak(b, rnd, naaldlen, dichtheid, hoofdlen=0.92, zijmax=0.30, zijstap=0.065, sneeuw=None,
             spar=False):
    """Dennen-/sparrentak: hoofdtwijg langs +y, zijtwijgen om en om, naalden rondom.
    sneeuw: Bouwer voor sneeuwklontjes op de bovenkant (of None)."""
    hout = []
    hoofd = twijg_pad(Vector((0, 0.0, 0)), (0, 1, 0), hoofdlen, 14, kromming=rnd.uniform(-0.05, 0.05), seed=rnd.random())
    hout.append((hoofd, 0.009, 0.003))
    zijden = []
    y, kant = 0.07, 1
    while y < hoofdlen - 0.04:
        t = y / hoofdlen
        lengte = zijmax * (math.sin(math.pi * min(1, t * 1.05)) ** 0.7) * rnd.uniform(0.75, 1.1) + 0.03
        hoek = math.radians(rnd.uniform(38, 58))
        i = min(len(hoofd) - 1, int(t * 14))
        p0 = hoofd[i].lerp(hoofd[min(i + 1, 14)], (t * 14) % 1)
        d = Vector((kant * math.sin(hoek), math.cos(hoek), 0))
        pad = twijg_pad(p0, d, lengte, 6, kromming=-kant * 0.15, zak=0.0, seed=rnd.random())
        hout.append((pad, 0.004, 0.0015))
        zijden.append(pad)
        # soms een tweede orde twijgje
        if lengte > 0.18 and not spar:
            for s in (0.4, 0.7):
                q0 = pad[int(s * 6)]
                dd = (d + Vector((0, 0.9, 0)) * rnd.uniform(0.3, 0.8)).normalized()
                pp = twijg_pad(q0, dd, lengte * 0.35, 4, seed=rnd.random())
                hout.append((pp, 0.0025, 0.0012))
                zijden.append(pp)
        y += zijstap * rnd.uniform(0.8, 1.2)
        kant = -kant
    # hout
    for pad, r0, r1 in hout:
        R = [r0 + (r1 - r0) * i / (len(pad) - 1) for i in range(len(pad))]
        L.buis(b, pad, R, zijden=5, mat=1, col=lambda i, s: (0.5, 0, 0, 1))
    # naalden
    for pad, r0, _ in hout:
        lengte = sum((pad[i + 1] - pad[i]).length for i in range(len(pad) - 1))
        n = int(lengte * dichtheid)
        for k in range(n):
            t = rnd.random()
            f = t * (len(pad) - 1)
            i = min(int(f), len(pad) - 2)
            p = pad[i].lerp(pad[i + 1], f - i)
            ax = (pad[i + 1] - pad[i]).normalized()
            x, yv = L.frame(ax)
            a = rnd.uniform(0, 2 * math.pi)
            uit = x * math.cos(a) + yv * math.sin(a)
            uit.z = abs(uit.z) * 0.6 + 0.15 if not spar else uit.z * 0.8 + 0.1     # meer naar boven
            voor = rnd.uniform(0.45, 0.85) if not spar else rnd.uniform(0.25, 0.6)
            d = (uit.normalized() + ax * voor).normalized()
            ll = naaldlen * rnd.uniform(0.7, 1.15) * (0.75 + 0.25 * (1 - t) if t > 0.85 else 1)
            var = rnd.random()
            if t > 0.88 and rnd.random() < 0.5:
                var = 1.3                       # jonge, lichte punt
            naald(b, p, d, ll, 0.0028 if not spar else 0.0022, var)
    if sneeuw is not None:
        for pad, r0, _ in hout:
            if r0 < 0.003:
                continue
            for i in range(1, len(pad) - 1):
                if rnd.random() < 0.85:
                    c = pad[i] + Vector((rnd.uniform(-0.01, 0.01), rnd.uniform(-0.01, 0.01), naaldlen * 0.35))
                    s = 0.034 * rnd.uniform(0.6, 1.2) * (1.4 if r0 > 0.005 else 0.9)
                    klont(sneeuw, c, (s * 1.25, s, s * 0.45), rnd)


def klont(b, c, maat, rnd):
    import bmesh
    bm = bmesh.new()
    bmesh.ops.create_icosphere(bm, subdivisions=2, radius=1.0)
    for v in bm.verts:
        n = noise.noise(v.co * 2.3 + Vector((rnd.random() * 50, 0, 0)))
        v.co *= 1 + 0.25 * n
    rot = Matrix.Rotation(rnd.uniform(0, math.pi), 4, "Z")
    M = Matrix.Translation(c) @ rot @ Matrix.Diagonal((*maat, 1))
    L.bm_naar_bouwer(bm, b, M=M)
    bm.free()


def blad(b, p, d, lengte, breedte, var, rnd, kop=0.0, mat=0, vorm="ovaal"):
    """Blaadje met nerf-vouw: 2 x 6 driehoeken. d = richting van steel naar punt (3D)."""
    d = Vector(d).normalized()
    up = Vector((0, 0, 1))
    x = d.cross(up)
    if x.length < 1e-4:
        x = Vector((1, 0, 0))
    x.normalize()
    n = x.cross(d).normalized()
    if n.z < 0:
        n = -n
    c = (var, rnd.random(), 0, 1)
    prof = {"ovaal": [0, 0.55, 0.85, 1.0, 0.85, 0.5, 0],
            "lang": [0, 0.45, 0.7, 0.8, 0.7, 0.45, 0],
            "breed": [0, 0.75, 1.0, 1.0, 0.9, 0.6, 0],
            "kartel": [0, 0.7, 0.55, 0.95, 0.6, 0.75, 0]}[vorm]
    m = len(prof)
    mid, L_, R_ = [], [], []
    for i in range(m):
        t = i / (m - 1)
        buig = -0.18 * lengte * t * t + kop * t
        pm = p + d * lengte * t + n * buig
        w = breedte * 0.5 * prof[i]
        mid.append(b.v(pm, c))
        L_.append(b.v(pm - x * w + n * w * 0.25, c))
        R_.append(b.v(pm + x * w + n * w * 0.25, c))
    for i in range(m - 1):
        t0, t1 = i / (m - 1), (i + 1) / (m - 1)
        b.f([mid[i], mid[i + 1], L_[i + 1], L_[i]], [(0.5, t0), (0.5, t1), (0, t1), (0, t0)], mat)
        b.f([mid[i], R_[i], R_[i + 1], mid[i + 1]], [(0.5, t0), (1, t0), (1, t1), (0.5, t1)], mat)


def bladtros(b, rnd, n_blad, bladlen, straal=0.42, vorm="ovaal", twijg_r=0.006, top=0.92):
    """Twijg vanaf de voet (0, 0) met zijtwijgjes; blaadjes vullen een ronde vorm."""
    hoofd = twijg_pad(Vector((0, 0, 0)), (0, 1, 0), top * 0.8, 10, kromming=rnd.uniform(-0.1, 0.1), seed=rnd.random())
    paden = [hoofd]
    for k in range(7):
        t = 0.25 + 0.1 * k
        p0 = hoofd[int(t * 10)]
        kant = 1 if k % 2 else -1
        d = Vector((kant * rnd.uniform(0.6, 1.0), rnd.uniform(0.5, 1.0), 0))
        paden.append(twijg_pad(p0, d, straal * rnd.uniform(0.6, 0.9), 6, seed=rnd.random()))
    for pad in paden:
        R = [twijg_r * (1 - 0.7 * i / (len(pad) - 1)) for i in range(len(pad))]
        L.buis(b, pad, R, zijden=5, mat=1)
    cy = top * 0.55
    for k in range(n_blad):
        # punt in de ronde vorm, iets dichter naar de rand
        while True:
            q = Vector((rnd.uniform(-1, 1), rnd.uniform(-1, 1), 0))
            if q.length <= 1:
                break
        q = q * straal
        q.y = q.y * 1.05 + cy
        # aanhechting: dichtstbijzijnde twijgpunt
        best = min((pp for pad in paden for pp in pad), key=lambda pp: (pp - q).length)
        d = q - best
        if d.length < 0.02:
            d = Vector((rnd.uniform(-1, 1), rnd.uniform(0, 1), 0))
        d.z = rnd.uniform(-0.2, 0.5) * d.length
        ll = bladlen * rnd.uniform(0.75, 1.2)
        basis = q - d.normalized() * ll * 0.6
        basis.z = rnd.uniform(0.0, 0.04) + (1 - (q - Vector((0, cy, 0))).length / straal) * 0.05
        blad(b, basis, d, ll, ll * rnd.uniform(0.5, 0.62), rnd.uniform(0, 1), rnd, kop=rnd.uniform(-0.01, 0.02),
             vorm=vorm)


def aar(b, rnd, voet, richting, lengte, mat_halm=0, mat_korrel=1, mat_kafnaald=2):
    """Tarwehalm met aar: halm (buis), korrels (platte ellipsjes) en kafnaalden."""
    d = Vector(richting).normalized()
    zij = Vector((-d.y, d.x, 0))
    kr = rnd.uniform(-1, 1)
    P = [voet + d * lengte * t + zij * 0.04 * t * t * kr for t in np.linspace(0, 1, 8)]
    L.buis(b, P, [0.0035] * 8, zijden=4, mat=mat_halm)
    top = P[-1]
    ad = (P[-1] - P[-2]).normalized()
    alen = rnd.uniform(0.13, 0.17)
    kz = Vector((-ad.y, ad.x, 0))
    for i in range(12):
        t = i / 11
        c = top + ad * alen * t
        for s in (-1, 1):
            w = 0.010 * (1 - 0.35 * abs(t - 0.4))
            q = c + kz * s * w
            korrel_d = (ad + kz * s * 0.7).normalized()
            blad(b, q - korrel_d * 0.006, korrel_d, 0.022, 0.013, rnd.random(), rnd, mat=mat_korrel)
            if rnd.random() < 0.75:
                kd = (ad * 1.0 + kz * s * rnd.uniform(0.15, 0.45)).normalized()
                naald(b, q + korrel_d * 0.006, kd, rnd.uniform(0.05, 0.09), 0.0018, rnd.random(), mat=mat_kafnaald)


# --- Materialen ---------------------------------------------------------------------------
def attr_mix(base, licht, punt=None):
    """Kleur = mix(base, licht) op attribuut R; R > 1 = jonge punt."""
    def f(nt):
        at = nt.nodes.new("ShaderNodeAttribute")
        at.attribute_name = "wind"
        sp = nt.nodes.new("ShaderNodeSeparateColor")
        nt.links.new(at.outputs["Color"], sp.inputs["Color"])
        mx = nt.nodes.new("ShaderNodeMix")
        mx.data_type = "RGBA"
        mx.clamp_factor = False
        nt.links.new(sp.outputs["Red"], mx.inputs["Factor"])
        mx.inputs[6].default_value = (*base, 1)
        mx.inputs[7].default_value = (*licht, 1)
        return mx.outputs[2]
    return f


def bump_ruis(schaal, kracht=0.3):
    def f(nt):
        tn = nt.nodes.new("ShaderNodeTexNoise")
        tn.inputs["Scale"].default_value = schaal
        bp = nt.nodes.new("ShaderNodeBump")
        bp.inputs["Strength"].default_value = kracht
        nt.links.new(tn.outputs["Fac"], bp.inputs["Height"])
        return bp.outputs["Normal"]
    return f


# --- Cellen -------------------------------------------------------------------------------
def cel(naam, bouw, groot=(1.0, 1.0), midden=(0.0, 0.5), res=None, ao=0.03):
    sc = L.leeg()
    res = res or (RES, RES)
    bouw(sc)
    L.studio_camera(sc, midden[0], midden[1], groot[0], groot[1], res[0], res[1])
    return L.studio_render(sc, os.path.join(L.STUDIO, naam))


def cel_naald(naam, spar=False, sneeuw=False):
    def bouw(sc):
        rnd = random.Random(11 if not spar else 23)
        b = L.Bouwer()
        s = L.Bouwer() if sneeuw else None
        if spar:
            naaldtak(b, rnd, 0.03, 1300, zijmax=0.30, zijstap=0.045, hoofdlen=0.9, sneeuw=s, spar=True)
        else:
            naaldtak(b, rnd, 0.055, 820, zijmax=0.36, zijstap=0.05, hoofdlen=0.9, sneeuw=s)
        m_naald = L.smat(naam + "_naald", attr_mix((0.50, 0.56, 0.40), (0.72, 0.76, 0.56)), ruw=0.55, ao=0.04)
        m_hout = L.smat(naam + "_hout", (0.36, 0.27, 0.19), ruw=0.8, ao=0.03)
        o = L.obj(naam, b.mesh(naam, [m_naald, m_hout]))
        if sneeuw:
            o.hide_render = True
            m_s = L.smat(naam + "_sneeuw", (0.92, 0.94, 0.98), ruw=0.45, normaal=bump_ruis(60, 0.4), ao=0.02)
            L.obj(naam + "_s", s.mesh(naam + "_s", [m_s]))
    return cel(naam, bouw)


def cel_blad(naam, n_blad, bladlen, vorm, straal=0.42, base=(0.56, 0.60, 0.42), licht=(0.74, 0.76, 0.52)):
    def bouw(sc):
        rnd = random.Random(hash(naam) & 0xffff)
        b = L.Bouwer()
        bladtros(b, rnd, n_blad, bladlen, straal=straal, vorm=vorm)
        mb = L.smat(naam + "_blad", attr_mix(base, licht), ruw=0.5, normaal=bump_ruis(140, 0.15), ao=0.05)
        mh = L.smat(naam + "_hout", (0.40, 0.33, 0.25), ruw=0.8, ao=0.03)
        L.obj(naam, b.mesh(naam, [mb, mh]))
    return cel(naam, bouw)


def cel_bloemen(naam):
    """Vier bloemclusters (rood, paars, geel, wit) in de vier kwadranten, met een paar blaadjes."""
    def bouw(sc):
        rnd = random.Random(5)
        b = L.Bouwer()
        kleuren = [(0.75, 0.06, 0.08), (0.45, 0.12, 0.62), (0.95, 0.75, 0.10), (0.92, 0.90, 0.85)]
        for q, (cx, cy) in enumerate(((-0.25, 0.25), (0.25, 0.25), (-0.25, 0.75), (0.25, 0.75))):
            for k in range(5):
                c = Vector((cx + rnd.uniform(-0.12, 0.12), cy + rnd.uniform(-0.12, 0.12), rnd.uniform(0.0, 0.05)))
                n_bl = 5 if q != 1 else 6
                r = rnd.uniform(0.028, 0.04)
                for i in range(n_bl):
                    a = 2 * math.pi * i / n_bl + rnd.uniform(-0.2, 0.2)
                    d = Vector((math.cos(a), math.sin(a), 0.35))
                    blad(b, c, d, r, r * 0.9, q / 3.0, rnd, mat=0, vorm="breed")
                klont(b, c + Vector((0, 0, 0.008)), (0.008, 0.008, 0.005), rnd)
            for k in range(6):
                p = Vector((cx + rnd.uniform(-0.15, 0.15), cy + rnd.uniform(-0.15, 0.15), -0.02))
                a = rnd.uniform(0, 2 * math.pi)
                blad(b, p, Vector((math.cos(a), math.sin(a), 0.1)), 0.06, 0.03, 0.0, rnd, mat=1, vorm="lang")

        def bloemkleur(nt):
            at = nt.nodes.new("ShaderNodeAttribute")
            at.attribute_name = "wind"
            sp = nt.nodes.new("ShaderNodeSeparateColor")
            nt.links.new(at.outputs["Color"], sp.inputs["Color"])
            rp = nt.nodes.new("ShaderNodeValToRGB")
            rp.color_ramp.interpolation = "CONSTANT"
            e = rp.color_ramp.elements
            e[0].position, e[0].color = 0.0, (*kleuren[0], 1)
            e[1].position, e[1].color = 0.3, (*kleuren[1], 1)
            e.new(0.6).color = (*kleuren[2], 1)
            e.new(0.95).color = (*kleuren[3], 1)
            nt.links.new(sp.outputs["Red"], rp.inputs["Fac"])
            return rp.outputs["Color"]
        mb = L.smat(naam + "_bl", bloemkleur, ruw=0.5, ao=0.02, sss=0.1)
        mg = L.smat(naam + "_gr", (0.18, 0.36, 0.10), ruw=0.5, ao=0.02)
        L.obj(naam, b.mesh(naam, [mb, mg]))
    return cel(naam, bouw)


def cel_tarwe(naam):
    """Bundel van 7 halmen met aren, platgelegd (zijaanzicht): voet onderaan midden."""
    def bouw(sc):
        rnd = random.Random(3)
        b = L.Bouwer()
        for k in range(11):
            a = math.radians(rnd.uniform(-20, 20))
            d = Vector((math.sin(a), math.cos(a), 0))
            aar(b, rnd, Vector((rnd.uniform(-0.05, 0.05), 0, rnd.uniform(-0.03, 0.03))), d, rnd.uniform(0.62, 0.78))
        # een paar bladen langs de halm
        for k in range(5):
            p = Vector((rnd.uniform(-0.03, 0.03), rnd.uniform(0.15, 0.45), 0.01))
            s = rnd.choice((-1, 1))
            blad(b, p, Vector((s * 0.6, 0.8, 0)), rnd.uniform(0.18, 0.25), 0.014, 0.0, rnd, mat=3, vorm="lang")
        m_halm = L.smat(naam + "_halm", (0.62, 0.33, 0.08), ruw=0.5, ao=0.02)
        m_korrel = L.smat(naam + "_korrel", attr_mix((0.66, 0.26, 0.04), (0.85, 0.45, 0.10)), ruw=0.45, ao=0.03)
        m_kaf = L.smat(naam + "_kaf", (0.80, 0.48, 0.15), ruw=0.5)
        m_blad = L.smat(naam + "_blad", (0.40, 0.28, 0.06), ruw=0.5)
        L.obj(naam, b.mesh(naam, [m_halm, m_korrel, m_kaf, m_blad]))
    return cel(naam, bouw, groot=(1.0, 1.0), midden=(0, 0.5))


def cel_grasblad(naam):
    """Groene bladpol (zijaanzicht): lange bladen die uitwaaieren en overhangen."""
    def bouw(sc):
        rnd = random.Random(8)
        b = L.Bouwer()
        for k in range(26):
            a = math.radians(rnd.uniform(-55, 55))
            d = Vector((math.sin(a), math.cos(a), rnd.uniform(-0.1, 0.1)))
            ll = rnd.uniform(0.25, 0.42)
            blad(b, Vector((rnd.uniform(-0.05, 0.05), 0, 0)), d, ll, rnd.uniform(0.025, 0.04), rnd.random(), rnd,
                 vorm="lang", kop=-0.06)
        mb = L.smat(naam + "_blad", attr_mix((0.18, 0.36, 0.10), (0.30, 0.50, 0.14)), ruw=0.5, ao=0.03)
        L.obj(naam, b.mesh(naam, [mb]))
    return cel(naam, bouw, groot=(1.0, 0.5), midden=(0, 0.25), res=(RES, RES // 2))


# --- Atlas samenstellen ----------------------------------------------------------------------
def lees(p, lineair=False):
    img = bpy.data.images.load(p, check_existing=False)
    if lineair:
        img.colorspace_settings.name = "Non-Color"
    a = L.pixels(img).copy()
    bpy.data.images.remove(img)
    return a


def dilateer(p, vul, stappen=24):
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


def stel_samen(atlas, cellen):
    W, H = ATLAS[atlas]
    K = np.zeros((H, W, 4), np.float32)
    N = np.zeros((H, W, 4), np.float32)
    N[..., :3] = (0.5, 0.5, 1.0)
    N[..., 3] = 1
    for naam, paden in cellen.items():
        u0, v0, u1, v1 = CEL[naam][1]
        x0, y0 = int(round(u0 * W)), int(round(v0 * H))
        x1, y1 = int(round(u1 * W)), int(round(v1 * H))
        k = lees(paden["kleur"])
        n = lees(paden["normaal"], lineair=True)
        # cel kan groter gerenderd zijn: schaal met nearest naar het vak
        def pas(a):
            h, w = a.shape[:2]
            yy = (np.arange(y1 - y0) * h / (y1 - y0)).astype(int)
            xx = (np.arange(x1 - x0) * w / (x1 - x0)).astype(int)
            return a[yy][:, xx]
        k, n = pas(k), pas(n)
        kd = dilateer(k, k[..., :3][k[..., 3] > 0.5].mean(0) if (k[..., 3] > 0.5).any() else (0.5, 0.5, 0.4))
        n2 = n.copy()
        n2[..., 3] = k[..., 3]
        nd = dilateer(n2, (0.5, 0.5, 1.0))
        K[y0:y1, x0:x1] = kd
        N[y0:y1, x0:x1, :3] = nd[..., :3]
    for arr, naam, data in ((K, "kleur", False), (N, "normaal", True)):
        img = bpy.data.images.new(f"{atlas}_{naam}", W, H, alpha=not data)
        if data:
            img.colorspace_settings.name = "Non-Color"
        img.pixels.foreach_set(arr.ravel())
        img.filepath_raw = os.path.join(L.NTEX, f"{atlas}_atlas_{naam}." + ("jpg" if data else "png"))
        img.file_format = "JPEG" if data else "PNG"
        bpy.context.scene.render.image_settings.quality = 92
        img.save()
        L.log("atlas", img.filepath_raw)


def PADEN(ns):
    return {n: {m: os.path.join(L.STUDIO, f"{n}_{m}.png") for m in ("kleur", "normaal")} for n in ns}


if __name__ == "__main__":
    if "naald" in ALLEEN:
        if "samen" not in L.OPTS:
            cel_naald("den_tak")
            cel_naald("den_sneeuw", sneeuw=True)
            cel_naald("spar_tak", spar=True)
            cel_naald("spar_sneeuw", spar=True, sneeuw=True)
        stel_samen("naald", PADEN(("den_tak", "spar_tak")))
        stel_samen("sneeuw", PADEN(("den_sneeuw", "spar_sneeuw")))
    if "blad" in ALLEEN:
        if "samen" not in L.OPTS:
            cel_blad("blad_tros", 200, 0.085, "ovaal", base=(0.46, 0.52, 0.34), licht=(0.80, 0.80, 0.56))
            cel_blad("blad_fijn", 420, 0.05, "ovaal", straal=0.40, base=(0.46, 0.52, 0.34), licht=(0.80, 0.80, 0.56))
            cel_blad("struik_blad", 75, 0.15, "breed", straal=0.40, base=(0.40, 0.46, 0.30), licht=(0.58, 0.62, 0.42))
            cel_bloemen("bloemen")
        stel_samen("blad", {n: {m: os.path.join(L.STUDIO, f"{n}_{m}.png") for m in ("kleur", "normaal")}
                            for n in ("blad_tros", "blad_fijn", "struik_blad", "bloemen")})
    if "akker" in ALLEEN:
        if "samen" not in L.OPTS:
            cel_tarwe("tarwe")
            cel_grasblad("akker_blad")
        stel_samen("akker", {n: {m: os.path.join(L.STUDIO, f"{n}_{m}.png") for m in ("kleur", "normaal")}
                             for n in ("tarwe", "akker_blad")})
    L.log("KLAAR")
