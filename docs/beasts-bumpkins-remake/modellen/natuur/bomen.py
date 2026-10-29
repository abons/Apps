"""Bomen en struiken voor missie 1: den_groot, spar, jonge_den, stronk, loofboom, loofboom_jong,
struik_bloem, struik_klein. Stam en takken zijn buizen met tegelbare schors (Poly Haven), het
gebladerte zijn alfakaarten uit textures/{naald,blad}_atlas (eerst kaarten.py draaien).

Per boom: <naam>.glb (LOD0, met kind-node <naam>_sneeuw) en <naam>_lod1.glb (minder, grotere kaarten,
zelfde materialen, dus de seizoenstint werkt ook op afstand).
Wind: kleurattribuut COLOR_0 (zie natuur_lib en README). Seizoen: baseColorFactor van het blad.

  blender -b -P bomen.py -- [alleen=den_groot,spar,...] [vergelijk]
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
from atlas import CEL, sub

ALLE = ["den_groot", "spar", "jonge_den", "stronk", "loofboom", "loofboom_jong", "struik_bloem", "struik_klein"]
ALLEEN = [n for n in L.OPTS.get("alleen", ",".join(ALLE)).split(",") if n]

# zomertint (baseColorFactor) per bladmateriaal; textuur is neutraal bleek geelgroen
TINT = {"den": (0.16, 0.30, 0.15), "spar": (0.19, 0.35, 0.39), "loof": (0.28, 0.48, 0.20),
        "loof_jong": (0.27, 0.46, 0.20), "struik": (0.19, 0.36, 0.15), "struik_klein": (0.40, 0.60, 0.24)}

MATS = {}


def mats():
    if MATS:
        return MATS
    nk = L.laad(os.path.join(L.NTEX, "naald_atlas_kleur.png"))
    nn = L.laad(os.path.join(L.NTEX, "naald_atlas_normaal.jpg"), data=True)
    sk = L.laad(os.path.join(L.NTEX, "sneeuw_atlas_kleur.png"))
    sn = L.laad(os.path.join(L.NTEX, "sneeuw_atlas_normaal.jpg"), data=True)
    bk = L.laad(os.path.join(L.NTEX, "blad_atlas_kleur.png"))
    bn = L.laad(os.path.join(L.NTEX, "blad_atlas_normaal.jpg"), data=True)
    MATS["bast_den"] = L.ph("pine_bark", "bast_den")
    MATS["bast_loof"] = L.ph("bark_brown_02", "bast_loof")
    for k in ("den", "spar"):
        MATS["naald_" + k] = L.pbr("naald_" + k, nk, nn, alpha=True, tweezijdig=True, ruw=0.75, factor=TINT[k])
    for k in ("loof", "loof_jong", "struik", "struik_klein"):
        MATS["blad_" + k] = L.pbr("blad_" + k, bk, bn, alpha=True, tweezijdig=True, ruw=0.7, factor=TINT[k])
    MATS["bloemen"] = L.pbr("bloemen", bk, bn, alpha=True, tweezijdig=True, ruw=0.6, factor=(1, 1, 1))
    MATS["sneeuw"] = L.pbr("sneeuw", sk, sn, alpha=True, tweezijdig=True, ruw=0.5, factor=(1, 1, 1))
    return MATS


def wcol(z, H, g=0.0, fase=0.0):
    return (min(1.0, max(0.0, z / H)) ** 1.5, min(1.0, g), fase, 1.0)


# --- Stam ------------------------------------------------------------------------------------
def stam(b, rnd, H, r0, r1, wortels=5, flare=0.9, zijden=10, krom=0.08, mat=0, top=None):
    """Stam met wortelvoeten. Geeft het pad terug (voor takposities)."""
    zs = [0, 0.05, 0.12, 0.22, 0.35, 0.55] + list(np.linspace(0.8, top or H, 9))
    zs = [z for z in zs if z <= (top or H)]
    ox, oy = rnd.uniform(0, 9), rnd.uniform(0, 9)
    P = [Vector((krom * noise.noise(Vector((ox, z * 0.4, 0))), krom * noise.noise(Vector((oy, z * 0.4, 0))), z)) for z in zs]
    R = [r0 + (r1 - r0) * (z / H) ** 0.8 for z in zs]
    a0 = rnd.uniform(0, 6.28)

    def fn(i, a):
        z = zs[i]
        w = max(0.0, math.cos(wortels * (a - a0) * 0.5) ** 2) ** 2 if wortels else 0
        return 1 + flare * math.exp(-z / 0.22) * (0.25 + w) + 0.04 * noise.noise(Vector((a * 2, z * 3, 1)))
    L.buis(b, P, R, zijden=zijden, col=lambda i, s: wcol(zs[i], H), uvschaal=1 / 0.9, straal_fn=fn, mat=mat,
           u_rep=2 * math.pi * r0 * 1.3)
    # wortels die in de grond lopen
    for k in range(wortels):
        a = a0 + 2 * math.pi * k / wortels + rnd.uniform(-0.2, 0.2)
        d = Vector((math.cos(a), math.sin(a), 0))
        lengte = r0 * rnd.uniform(1.6, 2.4)
        Q = [d * (r0 * 0.6) + Vector((0, 0, r0 * 0.9)), d * (r0 * 0.6 + lengte * 0.45) + Vector((0, 0, r0 * 0.3)),
             d * (r0 * 0.6 + lengte) + Vector((0, 0, -0.06))]
        L.buis(b, Q, [r0 * 0.42, r0 * 0.25, r0 * 0.08], zijden=6, col=lambda i, s: wcol(0, H), uvschaal=1 / 0.9, mat=mat)
    return P, R


def pad_op(P, z):
    for i in range(len(P) - 1):
        if P[i].z <= z <= P[i + 1].z:
            t = (z - P[i].z) / max(1e-6, P[i + 1].z - P[i].z)
            return P[i].lerp(P[i + 1], t)
    return P[-1]


# --- Conifeer ------------------------------------------------------------------------------
def conifeer(naam, H, r0, kroon0, Rmax, stap, per_krans, cel, tint_mat, seed, lod=0, zak=0.25,
             vorm_exp=0.95, kaart_w=0.75, zijkaarten=2, takdikte=0.035, opwaarts=0.12):
    rnd = random.Random(seed)
    b = L.Bouwer()          # mat 0 = bast, 1 = naald
    s = L.Bouwer()          # sneeuw
    P, R = stam(b, rnd, H - 0.3, r0, r0 * 0.08, zijden=10 if lod == 0 else 6, wortels=5 if lod == 0 else 0,
                flare=0.9 if lod == 0 else 0.4)
    uv = CEL[cel][1]
    uvs = CEL[cel.replace("_tak", "_sneeuw")][1]
    z = kroon0
    kransen = []
    while z < H - 0.25:
        kransen.append(z)
        z += stap * rnd.uniform(0.85, 1.15) * (1 if z < H * 0.7 else 0.8)
    if lod:
        kransen = kransen[::2]
        stap = stap * 2
    gouden = rnd.uniform(0, 6.28)
    for ki, zk in enumerate(kransen):
        f = (H - zk) / (H - kroon0)
        Lb = Rmax * f ** vorm_exp * rnd.uniform(0.85, 1.1) + 0.18
        n = max(3, int(per_krans * (0.6 + 0.4 * f)) - (1 if lod else 0))
        c = pad_op(P, zk)
        for j in range(n):
            a = gouden + 2 * math.pi * j / n + rnd.uniform(-0.3, 0.3)
            gouden += 0.9
            d = Vector((math.cos(a), math.sin(a), opwaarts + rnd.uniform(-0.08, 0.08)))
            d.normalize()
            fase = rnd.random()
            lb = Lb * rnd.uniform(0.8, 1.1)
            zk2 = zk + rnd.uniform(-0.06, 0.06)
            p0 = Vector((c.x, c.y, zk2))
            # tak: buis met doorzakkende punt
            Q = [p0 + d * lb * t + Vector((0, 0, -zak * lb * t * t)) for t in (0, 0.35, 0.7, 1.0)]
            if lod == 0:
                L.buis(b, Q, [takdikte * lb + 0.01, takdikte * lb * 0.6, takdikte * lb * 0.3, 0.004], zijden=4,
                       col=lambda i, s_, q=Q: wcol(q[i].z, H, i / 3 * 0.6, fase), uvschaal=1 / 0.9, mat=0)
            hor = Vector((-d.y, d.x, 0)).normalized()
            # hoofdkaart over de hele tak, plat met wat rol
            schaal = 1.5 if lod else 1.0
            for k in range(1 + (zijkaarten if lod == 0 else 1)):
                if k == 0:
                    rol, off, lk = rnd.uniform(-0.25, 0.25), 0.0, lb * 1.1 * schaal
                else:
                    rol, off, lk = (0.6 if k == 1 else -0.6) + rnd.uniform(-0.2, 0.2), rnd.uniform(0.15, 0.4), lb * 0.75
                w = Matrix.Rotation(rol, 3, d) @ hor
                start = p0.lerp(Q[-1], off) - d * 0.05
                # kaartnormaal: omhoog + radiaal naar buiten
                def nrm(p, cz=c):
                    rad = Vector((p.x - cz.x, p.y - cz.y, 0))
                    rad = rad.normalized() if rad.length > 1e-4 else Vector((0, 0, 1))
                    return (Vector((0, 0, 1)) * 0.7 + rad * 0.6).normalized()
                L.kaart(b, start, d, w, lk, lk * kaart_w, uv, wcol(start.z, H, 0.15, fase),
                        wcol(start.z, H, 1.0, fase), buig=zak * lk * 0.8, seg=2, nrm=nrm, mat=1)
                if k == 0 and lod == 0:
                    L.kaart(s, start + Vector((0, 0, 0.035)), d, w, lk, lk * kaart_w, uvs,
                            wcol(start.z, H, 0.15, fase), wcol(start.z, H, 1.0, fase), buig=zak * lk * 0.8, seg=2,
                            nrm=lambda p: Vector((0, 0, 1)), mat=0)
        # binnenvulling: korte schuine kaarten tegen de stam
        if lod == 0 and Lb > 0.5:
            for j in range(3):
                a = rnd.uniform(0, 6.28)
                d = Vector((math.cos(a), math.sin(a), 0.6)).normalized()
                hor = Vector((-d.y, d.x, 0)).normalized()
                L.kaart(b, Vector((c.x, c.y, zk)), d, hor, Lb * 0.6, Lb * 0.45, uv, wcol(zk, H, 0.1, 0),
                        wcol(zk, H, 0.5, 0), buig=0.05, seg=1, mat=1)
    # top: drie rechtopstaande kaarten
    top = pad_op(P, H - 0.45)
    for j in range(3 if lod == 0 else 2):
        a = j * math.pi / (3 if lod == 0 else 2)
        w = Vector((math.cos(a), math.sin(a), 0))
        L.kaart(b, top - Vector((0, 0, 0.1)), Vector((0, 0, 1)), w, 0.9, 0.6, uv, wcol(H - 0.5, H, 0.2, 0.5), wcol(H, H, 0.8, 0.5),
                seg=1, mat=1)
    M = mats()
    o = L.obj(naam if lod == 0 else naam + "_lod1", b.mesh(naam, [M["bast_den"], M[tint_mat]]))
    uit = [o]
    if lod == 0:
        so = L.obj(naam + "_sneeuw", s.mesh(naam + "_sneeuw", [M["sneeuw"]]))
        so.parent = o
    return o


# --- Loofboom --------------------------------------------------------------------------------
def loofboom(naam, H, r0, kroon_z, kroon_r, kroon_h, n_kaart, kaart_l, cel, tint_mat, seed, lod=0,
             n_tak=5, bast="bast_loof", vul=0.55):
    rnd = random.Random(seed)
    b = L.Bouwer()
    s = L.Bouwer()
    stamtop = kroon_z + kroon_h * 0.55
    P, R = stam(b, rnd, H, r0, r0 * 0.35, zijden=9 if lod == 0 else 6, wortels=4 if lod == 0 else 0, flare=0.6,
                krom=0.12, top=stamtop)
    midden = Vector((P[-1].x, P[-1].y, kroon_z + kroon_h * 0.5))
    uv = CEL[cel][1]
    uvs = CEL["den_sneeuw"][1]
    takken = []
    for j in range(n_tak if lod == 0 else 3):
        a = 2 * math.pi * j / n_tak + rnd.uniform(-0.3, 0.3)
        z0 = kroon_z + rnd.uniform(-0.1, 0.4) + j * 0.12
        p0 = pad_op(P, min(z0, stamtop - 0.1))
        d = Vector((math.cos(a), math.sin(a), rnd.uniform(0.9, 1.6))).normalized()
        lt = kroon_r * rnd.uniform(0.9, 1.15)
        Q = [p0 + d * lt * t + Vector((0, 0, -0.15 * lt * t * t)) for t in (0, 0.33, 0.66, 1.0)]
        fase = rnd.random()
        L.buis(b, Q, [r0 * 0.45, r0 * 0.3, r0 * 0.18, r0 * 0.06], zijden=6 if lod == 0 else 4,
               col=lambda i, s_, q=Q, f=fase: wcol(q[i].z, H, i / 3 * 0.4, f), uvschaal=1 / 0.9, mat=0)
        takken.append((Q, fase))
        if lod == 0:
            for t in (0.45, 0.75):
                q0 = Q[int(t * 3)]
                a2 = a + rnd.choice((-1, 1)) * rnd.uniform(0.6, 1.2)
                d2 = Vector((math.cos(a2), math.sin(a2), rnd.uniform(0.3, 1.0))).normalized()
                l2 = lt * 0.5
                Q2 = [q0 + d2 * l2 * u for u in (0, 0.5, 1)]
                L.buis(b, Q2, [r0 * 0.15, r0 * 0.08, r0 * 0.03], zijden=4,
                       col=lambda i, s_, q=Q2, f=fase: wcol(q[i].z, H, 0.4 + i * 0.2, f), uvschaal=1 / 0.9, mat=0)
                takken.append((Q2, fase))
    eind = [(q, f) for Q, f in takken for q in Q[1:]]
    n = n_kaart if lod == 0 else n_kaart // 4
    kl = kaart_l * (1.0 if lod == 0 else 1.7)
    for k in range(n):
        # punt in de ellipsoide, schil-gewogen
        while True:
            q = Vector((rnd.uniform(-1, 1), rnd.uniform(-1, 1), rnd.uniform(-1, 1)))
            if q.length <= 1:
                break
        q = q.normalized() * (q.length ** (1 - vul) if rnd.random() < 0.8 else q.length)
        ei = 1 - 0.32 * max(0.0, q.z) ** 1.3                  # eivorm: smaller naar de top
        p = midden + Vector((q.x * kroon_r * ei, q.y * kroon_r * ei, q.z * kroon_h * 0.5))
        # vorm: onderkant iets platter, top iets spitser
        if q.z < -0.6:
            p.z = midden.z - kroon_h * 0.5 * (0.6 + (abs(q.z) - 0.6) * 0.5)
        rad = (p - midden)
        radn = Vector((rad.x / kroon_r, rad.y / kroon_r, rad.z / (kroon_h * 0.5))).normalized()
        anker, fase = min(eind, key=lambda e: (e[0] - p).length)
        uit = (radn + Vector((rnd.uniform(-0.4, 0.4), rnd.uniform(-0.4, 0.4), rnd.uniform(-0.2, 0.5)))).normalized()
        hor = uit.cross(Vector((0, 0, 1)))
        if hor.length < 0.1:
            hor = Vector((1, 0, 0))
        hor = Matrix.Rotation(rnd.uniform(-0.7, 0.7), 3, uit) @ hor.normalized()
        ll = kl * rnd.uniform(0.8, 1.2)
        start = p - uit * ll * 0.45

        def nrm(pp, m=midden):
            r = pp - m
            return Vector((r.x / kroon_r, r.y / kroon_r, r.z / (kroon_h * 0.5) + 0.35)).normalized()
        L.kaart(b, start, uit, hor, ll, ll * 0.95, uv, wcol(start.z, H, 0.35, fase), wcol(start.z, H, 1.0, fase),
                buig=0.06 * ll, seg=1, nrm=nrm, mat=1)
        if lod == 0 and radn.z > 0.35 and rnd.random() < 0.55:
            w2 = Vector((1, 0, 0)) if abs(uit.x) < 0.9 else Vector((0, 1, 0))
            L.kaart(s, p + Vector((0, 0, 0.05)), Vector((-w2.y, w2.x, 0)), w2, ll * 0.5, ll * 0.5, uvs,
                    wcol(p.z, H, 0.5, fase), wcol(p.z, H, 1.0, fase), seg=1, nrm=lambda pp: Vector((0, 0, 1)))
    M = mats()
    o = L.obj(naam if lod == 0 else naam + "_lod1", b.mesh(naam, [M[bast], M[tint_mat]]))
    if lod == 0:
        so = L.obj(naam + "_sneeuw", s.mesh(naam + "_sneeuw", [M["sneeuw"]]))
        so.parent = o
    return o


# --- Struik ----------------------------------------------------------------------------------
def struik(naam, lobben, n_kaart, kaart_l, cel, tint_mat, seed, bloemen=0, lod=0):
    """lobben: [(x, y, r, h)] halve ellipsoiden op de grond."""
    rnd = random.Random(seed)
    b = L.Bouwer()           # mat 0 = blad, 1 = bloemen
    uv = CEL[cel][1]
    bl = CEL["bloemen"][1]
    totaal = sum(l[2] ** 2 for l in lobben)
    Hs = max(l[3] for l in lobben)
    n = n_kaart if lod == 0 else n_kaart // 3
    for k in range(n):
        x, y, r, h = rnd.choices(lobben, weights=[l[2] ** 2 for l in lobben])[0]
        while True:
            q = Vector((rnd.uniform(-1, 1), rnd.uniform(-1, 1), rnd.uniform(0, 1)))
            if q.length <= 1:
                break
        q = q.normalized() * (q.length ** 0.4)
        p = Vector((x + q.x * r, y + q.y * r, q.z * h))
        radn = Vector((q.x, q.y, q.z + 0.3)).normalized()
        uit = (radn + Vector((rnd.uniform(-0.5, 0.5), rnd.uniform(-0.5, 0.5), rnd.uniform(0, 0.6)))).normalized()
        hor = uit.cross(Vector((0, 0, 1)))
        hor = hor.normalized() if hor.length > 0.1 else Vector((1, 0, 0))
        hor = Matrix.Rotation(rnd.uniform(-0.8, 0.8), 3, uit) @ hor
        ll = kaart_l * rnd.uniform(0.8, 1.2) * (1.6 if lod else 1.0)
        start = p - uit * ll * 0.4
        start.z = max(start.z, 0.0)
        fase = rnd.random()
        c = Vector((x, y, 0))
        L.kaart(b, start, uit, hor, ll, ll, uv, (0, 0.2, fase, 1), (0, 1.0, fase, 1), buig=0.05 * ll, seg=1,
                nrm=lambda pp, c=c, r=r, h=h: Vector(((pp.x - c.x) / r, (pp.y - c.y) / r, pp.z / h + 0.4)).normalized(),
                mat=0)
    for k in range(bloemen if lod == 0 else bloemen // 5):
        x, y, r, h = rnd.choice(lobben)
        if rnd.random() < 0.3:
            # losse bloempjes op de grond ernaast
            a = rnd.uniform(0, 6.28)
            p = Vector((x + math.cos(a) * r * 1.25, y + math.sin(a) * r * 1.25, 0.12))
        else:
            while True:
                q = Vector((rnd.uniform(-1, 1), rnd.uniform(-1, 1), rnd.uniform(0.2, 1)))
                if 0.7 < q.length <= 1:
                    break
            q.normalize()
            p = Vector((x + q.x * r * 1.02, y + q.y * r * 1.02, q.z * h * 1.02))
        kw = rnd.randrange(4)
        a, bb = (kw % 2) * 0.5, (kw // 2) * 0.5
        uvq = (bl[0] + (bl[2] - bl[0]) * a, bl[1] + (bl[3] - bl[1]) * bb,
               bl[0] + (bl[2] - bl[0]) * (a + 0.5), bl[1] + (bl[3] - bl[1]) * (bb + 0.5))
        sz = rnd.uniform(0.5, 0.7)
        hor = Vector((1, 0, 0))
        # bloemkaart: liggend, naar de camera gekanteld
        d = Vector((0.55, 0.55, 0.6)).normalized()
        w = Vector((0.707, -0.707, 0))
        L.kaart(b, p - d * sz * 0.5, d, w, sz, sz, uvq, (0, 0.5, 0, 1), (0, 1, 0, 1), seg=1,
                nrm=lambda pp: Vector((0, 0, 1)), mat=1)
    M = mats()
    o = L.obj(naam if lod == 0 else naam + "_lod1", b.mesh(naam, [M[tint_mat], M["bloemen"]]))
    return o


# --- Stronk ---------------------------------------------------------------------------------
def ringen_textuur():
    pad = os.path.join(L.NTEX, "jaarringen_kleur.jpg")
    if os.path.exists(pad):
        return L.laad(pad)
    N = 512
    y, x = np.mgrid[0:N, 0:N] / N * 2 - 1
    r = np.sqrt(x ** 2 + y ** 2)
    a = np.arctan2(y, x)
    wob = 0.03 * np.sin(a * 3 + 1) + 0.02 * np.sin(a * 7)
    ring = 0.5 + 0.5 * np.sin((r + wob) * 70)
    ring = ring ** 3
    rng = np.random.default_rng(3)
    ruis = rng.normal(0, 1, (N, N)).astype(np.float32)
    for _ in range(3):
        ruis = (ruis + np.roll(ruis, 1, 0) + np.roll(ruis, 1, 1) + np.roll(ruis, -1, 0) + np.roll(ruis, -1, 1)) / 5
    licht = np.array([0.70, 0.52, 0.34])
    donker = np.array([0.45, 0.28, 0.15])
    kern = np.clip(1 - r / 0.08, 0, 1)
    c = licht * (1 - ring[..., None] * 0.8) + donker * ring[..., None] * 0.8
    c = c * (0.92 + 0.15 * ruis[..., None])
    c = c * (1 - 0.25 * np.clip((r - 0.82) / 0.1, 0, 1))[..., None]           # donkere rand (spint)
    # barstjes vanuit het hart
    for k in range(6):
        ak = rng.uniform(-np.pi, np.pi)
        m = (np.abs(np.angle(np.exp(1j * (a - ak)))) < 0.012 * (1.2 - r)) & (r < rng.uniform(0.3, 0.7))
        c[m] *= 0.5
    c = c * (1 - 0.3 * kern[..., None])
    img = bpy.data.images.new("jaarringen", N, N)
    rgba = np.concatenate([np.clip(c, 0, 1), np.ones((N, N, 1))], 2).astype(np.float32)
    img.pixels.foreach_set(rgba.ravel())
    img.filepath_raw = pad
    img.file_format = "JPEG"
    img.save()
    bpy.data.images.remove(img)
    return L.laad(pad)


def stronk(naam):
    rnd = random.Random(41)
    b = L.Bouwer()            # 0 bast, 1 snijvlak
    H, r0 = 0.55, 0.36
    zs = [0, 0.05, 0.12, 0.22, 0.34, H]
    a0 = 0.4

    def fn(i, a):
        z = zs[i]
        w = max(0.0, math.cos(5 * (a - a0) * 0.5) ** 2) ** 2
        return 1 + 0.9 * math.exp(-z / 0.12) * (0.2 + w) + 0.03 * noise.noise(Vector((a * 3, z * 4, 2)))
    P = [Vector((0, 0, z)) for z in zs]
    ring = L.buis(b, P, [r0] * len(zs), zijden=16, straal_fn=fn, uvschaal=1 / 0.9, mat=0, u_rep=2.2)
    top = ring[-1]
    # snijvlak: schuin, iets gebroken
    c = b.v((0, 0, H + 0.02))
    for k in range(16):
        va, vb = top[k][0], top[k + 1][0]
        pa, pb = Vector(b.V[va]), Vector(b.V[vb])
        def uv(p):
            return (0.5 + p.x / (2 * r0 * 1.15), 0.5 + p.y / (2 * r0 * 1.15))
        b.f([va, vb, c], [uv(pa), uv(pb), (0.5, 0.5)], 1)
    for k in range(5):
        a = a0 + 2 * math.pi * k / 5 + rnd.uniform(-0.15, 0.15)
        d = Vector((math.cos(a), math.sin(a), 0))
        Q = [d * 0.22 + Vector((0, 0, 0.2)), d * 0.45 + Vector((0, 0, 0.06)), d * 0.7 + Vector((0, 0, -0.04))]
        L.buis(b, Q, [0.11, 0.07, 0.025], zijden=6, uvschaal=1 / 0.9, mat=0)
    # losse stukken hout eromheen
    stukken = [((0.95, 0.4), 0.4, 0.1, 0.42), ((-0.6, 0.85), 2.1, 0.08, 0.36), ((-0.95, -0.4), 3.6, 0.09, 0.45),
               ((0.5, -0.95), 5.0, 0.06, 0.3), ((1.05, -0.35), 1.0, 0.04, 0.3)]
    for (x, y), a, r, l in stukken:
        d = Vector((math.cos(a), math.sin(a), 0))
        p = Vector((x, y, r))
        Q = [p - d * l / 2, p + d * l / 2]
        rr = L.buis(b, Q, [r, r * 0.95], zijden=8, uvschaal=1 / 0.9, mat=0, u_rep=0.4)
        for kant, ri in ((0, rr[0]), (1, rr[-1])):
            cc = b.v(Q[kant])
            for k in range(8):
                va, vb = ri[k][0], ri[k + 1][0]
                ang0, ang1 = 2 * math.pi * k / 8, 2 * math.pi * (k + 1) / 8
                f = [va, vb, cc] if kant else [vb, va, cc]
                uvs = [(0.5 + 0.45 * math.cos(ang0), 0.5 + 0.45 * math.sin(ang0)),
                       (0.5 + 0.45 * math.cos(ang1), 0.5 + 0.45 * math.sin(ang1)), (0.5, 0.5)]
                b.f(f, uvs if kant else [uvs[1], uvs[0], uvs[2]], 1)
    M = mats()
    top_m = L.pbr("snijvlak", ringen_textuur(), ruw=0.75)
    me = b.mesh(naam, [M["bast_den"], top_m])
    o = L.obj(naam, me)
    o.data.set_sharp_from_angle(angle=math.radians(50))
    return o


# --- Bouw ------------------------------------------------------------------------------------
def bouw(naam):
    L.leeg()
    MATS.clear()
    lod0 = lod1 = None
    if naam == "den_groot":
        mk = lambda lod: conifeer(naam, 6.6, 0.27, 1.75, 1.3, 0.30, 8, "den_tak", "naald_den", 7, lod=lod, kaart_w=0.95, zak=0.3)
    elif naam == "spar":
        mk = lambda lod: conifeer(naam, 4.8, 0.14, 1.0, 1.0, 0.22, 8, "spar_tak", "naald_spar", 13, lod=lod,
                                  zak=0.35, vorm_exp=1.0, kaart_w=0.85, takdikte=0.03, opwaarts=0.0)
    elif naam == "jonge_den":
        mk = lambda lod: conifeer(naam, 1.9, 0.035, 0.65, 0.42, 0.2, 4, "den_tak", "naald_den", 19, lod=lod,
                                  zijkaarten=0, takdikte=0.03, kaart_w=0.8, zak=0.35)
    elif naam == "loofboom":
        mk = lambda lod: loofboom(naam, 5.6, 0.22, 1.25, 1.6, 4.3, 600, 1.0, "blad_tros", "blad_loof", 29, lod=lod)
    elif naam == "loofboom_jong":
        mk = lambda lod: loofboom(naam, 3.9, 0.09, 1.15, 0.8, 2.6, 280, 0.62, "blad_fijn", "blad_loof_jong", 31,
                                  lod=lod, n_tak=4, vul=0.6)
    elif naam == "struik_bloem":
        mk = lambda lod: struik(naam, [(-0.35, 0.2, 0.85, 1.3), (0.6, -0.25, 0.72, 1.05), (0.1, -0.6, 0.5, 0.6)],
                                380, 0.55, "struik_blad", "blad_struik", 37, bloemen=70, lod=lod)
    elif naam == "struik_klein":
        mk = lambda lod: struik(naam, [(0, 0, 0.75, 1.15), (0.25, 0.3, 0.5, 0.85)], 220, 0.45, "blad_fijn",
                                "blad_struik_klein", 43, lod=lod)
    elif naam == "stronk":
        lod0 = stronk(naam)
        L.exporteer(os.path.join(L.HERE, naam + ".glb"), [lod0])
        return {naam: L.tris([lod0])}
    lod0 = mk(0)
    t0 = L.tris([lod0])
    ts = L.tris(list(lod0.children))
    lod1 = mk(1)
    t1 = L.tris([lod1])
    L.exporteer(os.path.join(L.HERE, naam + ".glb"), [lod0, lod1])      # LOD0 + LOD1 in een glb
    L.log(naam, "LOD0", t0, "sneeuw", ts, "LOD1", t1)
    return {naam: t0, naam + "_sneeuw": ts, naam + "_lod1": t1}


def ontkies_alles():
    L.ontkies()


if __name__ == "__main__":
    import json
    stat = {}
    for n in ALLEEN:
        stat.update(bouw(n))
    p = os.path.join(L.HERE, "_tris.json")
    oud = json.load(open(p)) if os.path.exists(p) else {}
    oud.update(stat)
    json.dump(oud, open(p, "w"), indent=1, sort_keys=True)
    L.log("KLAAR", stat)
