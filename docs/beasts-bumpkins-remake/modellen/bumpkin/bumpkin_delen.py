"""Bibliotheek van bumpkin-delen: geometrie, gewichten, plooien (hoog-poly) en textuur per soort.

Elke soort heeft (waar nodig) een bouwer `bouw_<soort>(sk, coll, ...)` die een mesh-object met UV-laag
`UVm` (metres) en face-attribuut `regio` teruggeeft, een gewichtregel (@gewicht), een plooiregel voor de
hoog-poly (@hoog) en een schilder (@verf). De soorten van de man (hemd, tuinbroek, riem, laarzen, lijf,
kop = haar/snor, haar, snor) staan hier ongewijzigd uit bumpkin_man.py; de andere personages voegen
soorten toe onderaan (tuniek, jurk, rok, broek, kraag, staartjes, strikken, knot, staf, ...).
De rig levert de gewrichten (Skelet), dus alles schaalt mee met `maat`.
"""
import math

import bpy  # noqa: F401
import numpy as np

from bumpkin_basis import (GEWICHT, HOOG, VERF, Bouwer, Kop, gauss, gladstap, keten, keten_param, overgang,  # noqa: F401
                           ring, ruis, srgb, steek, vertex_regio)


def gewicht(soort):
    def f(fn):
        GEWICHT[soort] = fn
        return fn
    return f


def hoog(soort, niveau=2, simpel=False):
    def f(fn):
        HOOG[soort] = (fn, niveau, simpel)
        return fn
    return f


def verf(soort):
    def f(fn):
        VERF[soort] = fn
        return fn
    return f


# ================================================================================================
# Man-delen (ongewijzigd uit bumpkin_man.py)
# ================================================================================================


def bouw_hemd(sk, coll, naam="hemd"):
    J = sk.J
    s = sk.s
    v = lambda k: J[k]
    Z = sk.z
    # hemd: los grijsgroen werkhemd met lange mouwen (regio 0 romp, 1 mouwen); hals = huid
    B = Bouwer()
    n = 22
    prof = [(0.57, 0.138, 0.108), (0.62, 0.146, 0.113), (0.68, 0.152, 0.117), (0.74, 0.155, 0.12),
            (0.80, 0.155, 0.12), (0.86, 0.158, 0.12), (0.90, 0.165, 0.116), (0.93, 0.163, 0.108),
            (0.955, 0.13, 0.092), (0.978, 0.088, 0.074), (0.998, 0.064, 0.063)]
    # (z, a, b, halve opening): dicht tot de V, dan open hals en een omgeslagen kraagje
    rijen = [(0.6, 0.128, 0.098, 0.0), (0.635, 0.14, 0.108, 0.0)] + [(z, a, b, 0.0) for z, a, b in prof[2:8]] + \
        [(0.952, 0.134, 0.094, 0.007), (0.975, 0.094, 0.077, 0.015), (0.992, 0.07, 0.067, 0.021),
         (1.006, 0.067, 0.065, 0.024), (1.017, 0.071, 0.069, 0.026), (1.003, 0.085, 0.079, 0.031),
         (0.988, 0.095, 0.087, 0.037)]
    t = 0.008 * s
    K = 30
    P = []
    for zr, a, b, g in rijen:
        a, b, g = a * s, b * s, g * s
        f0 = math.asin(min(0.95, g / a))
        kol = [(f0 + 0.25, t), (f0, t)] + [(f0 + (2 * np.pi - 2 * f0) * k / (K - 1), 0.0) for k in range(K)] + \
              [(2 * np.pi - f0, t), (2 * np.pi - f0 - 0.25, t)]
        P.append([(math.sin(ph) * (a - i2), 0.004 * s - math.cos(ph) * (b - i2), Z(zr)) for ph, i2 in kol])
    B.grid(np.array(P[:-2]), False, regio=0, buiten=(0, 1, 0))
    B.grid(np.array(P[-3:]), False, regio=0)                      # omgeslagen kraag: eigen vel
    gz = np.array([Z(r[0]) for r in rijen[7:11]])
    gg = np.array([r[3] * s for r in rijen[7:11]])  # noqa
    sk.hemd_v = lambda z: np.interp(z, gz, gg)
    rz_ = np.array([Z(z) for z, _, _ in prof])
    ra_ = np.array([a * s for _, a, _ in prof])
    rb_ = np.array([b * s for _, _, b in prof])
    sk.romp_ab = lambda z: (float(np.interp(z, rz_, ra_)), float(np.interp(z, rz_, rb_)))
    sk.mouw = {}
    for k, sx in (("Left", 1), ("Right", -1)):
        sch = v(k + "Arm")
        wortel = sch * np.array([0.42, 1, 1]) + np.array([0, 0, 0.018 * s])
        pts = [wortel, sch, v(k + "ForeArm"), v(k + "Hand")]
        sk.mouw[k] = pts
        L0 = np.linalg.norm(pts[1] - pts[0])
        L1 = np.linalg.norm(pts[2] - pts[1])
        L2 = np.linalg.norm(pts[3] - pts[2])
        e, w = L0 + L1, L0 + L1 + L2
        mp = [(0.0, 0.045, 0.05), (L0 * 0.5, 0.058, 0.065), (L0, 0.061, 0.066), (L0 + 0.05, 0.058, 0.061),
              (L0 + 0.11, 0.055, 0.057), (e - 0.03, 0.053, 0.055), (e, 0.053, 0.055), (e + 0.03, 0.052, 0.054),
              (e + 0.09, 0.051, 0.052), (w - 0.04, 0.05, 0.051), (w - 0.03, 0.043, 0.044), (w + 0.004, 0.045, 0.046),
              (w + 0.006, 0.036, 0.037), (w - 0.015, 0.034, 0.035)]
        fr = keten(pts, [q[0] for q in mp], zacht=0.05)
        rings = [ring(pos, sd, f, a * s, b * s, 16, 2.1) for (pos, tt, f, sd), (_, a, b) in zip(fr, mp)]
        B.grid(np.array(rings), True, regio=1)
    return B.obj(naam, coll)


def bouw_tuinbroek(sk, coll, naam="tuinbroek"):
    J = sk.J
    s = sk.s
    v = lambda k: J[k]
    Z = sk.z
    # tuinbroek: pijpen (0), heupstuk (1), slab en rugpand (2), bretels (3), riem (4), gesp (5)
    B = Bouwer()
    for k, sx in (("Left", 1), ("Right", -1)):
        pts = [v(k + "UpLeg"), v(k + "Leg"), v(k + "Foot")]
        L1 = np.linalg.norm(pts[1] - pts[0])
        L2 = np.linalg.norm(pts[2] - pts[1])
        prof = [(-0.03, 0.078, 0.082), (0.0, 0.085, 0.09), (0.04, 0.087, 0.093), (0.10, 0.087, 0.091),
                (0.17, 0.085, 0.088), (0.23, 0.082, 0.085), (L1 - 0.035, 0.08, 0.083), (L1, 0.079, 0.084),
                (L1 + 0.035, 0.079, 0.082), (L1 + 0.08, 0.077, 0.079), (L1 + L2 - 0.18, 0.068, 0.069),
                (L1 + L2 - 0.14, 0.06, 0.06), (L1 + L2 - 0.09, 0.054, 0.054), (L1 + L2 - 0.03, 0.05, 0.05),
                (L1 + L2 + 0.0, 0.048, 0.048)]
        fr = keten(pts, [q[0] for q in prof], zacht=0.06)
        rings = []
        for (pos, t, f, sd), (d, a, b) in zip(fr, prof):
            inw = np.array([-sx * 0.014 * s * (1 - np.clip(d / L1, 0, 1)), 0, 0])
            rings.append(ring(pos + inw, sd, f, a * s, b * s, 16, 2.2))
        B.grid(np.array(rings), True, regio=0)
    hp = [(0.545, 0.10, 0.08), (0.57, 0.13, 0.10), (0.60, 0.152, 0.12), (0.64, 0.161, 0.126), (0.68, 0.163, 0.127),
          (0.687, 0.156, 0.12), (0.672, 0.148, 0.113)]
    rings = [ring((0, 0.004 * s, Z(z)), (1, 0, 0), (0, -1, 0), a * s, b * s, 22, 2.3, fase=-np.pi / 2) for z, a, b in hp]
    b0, _ = B.grid(np.array(rings), True, regio=1)
    B.kap(b0, 22, (0, 0.004 * s, Z(0.53)), regio=1)

    def op_romp(x, z, kant, off):
        a, b = sk.romp_ab(z)
        y = kant * b * math.sqrt(max(0.03, 1 - (x / a) ** 2))
        return np.array([x, 0.004 * s + y + kant * off, z])

    def plaat(zlo, zhi, hb, kant, off=0.007 * s, K=9, R_=7):
        """Paneel op de romp (slab/rugpand) met omgeslagen boven- en zijranden."""
        rows = []
        zs = [zlo + (zhi - zlo) * i / (R_ - 1) for i in range(R_)] + [zhi - 0.005 * s]
        for i, z in enumerate(zs):
            w = hb(z)
            o_ = off if i < R_ else 0.0015 * s
            row = [op_romp(-w + 0.004 * s, z, kant, 0.0015 * s)]
            row += [op_romp(-w + 2 * w * j / (K - 1), z, kant, o_) for j in range(K)]
            row += [op_romp(w - 0.004 * s, z, kant, 0.0015 * s)]
            rows.append(row)
        B.grid(np.array(rows), False, regio=2, buiten=(0, kant, 0))
    sk.slab = (Z(0.66), Z(0.885), lambda z: (0.088 - 0.01 * (z - Z(0.66)) / (Z(0.885) - Z(0.66))) * s)
    sk.rug = (Z(0.66), Z(0.80), lambda z: (0.13 - 0.07 * (z - Z(0.66)) / (Z(0.80) - Z(0.66))) * s)
    plaat(*sk.slab, -1)
    plaat(*sk.rug, 1)
    # bretels: van de slabhoek over de schouder, kruisen op de rug naar de andere kant van het rugpand
    sk.bretel = {}
    for k, sx in (("Left", 1), ("Right", -1)):
        pad, nrm = [], []
        x0 = sx * 0.066 * s
        for z in (Z(0.872), Z(0.9), Z(0.925)):
            pad.append(op_romp(x0 + sx * 0.012 * s * (z - Z(0.872)) / 0.05, z, -1, 0.009 * s))
            nrm.append(np.array([0, -1.0, 0.2]))
        xs_ = sx * 0.085 * s
        c = np.array([xs_, 0.004 * s, Z(0.9)])
        for psi in np.linspace(0.75, np.pi - 0.75, 6):
            d = np.array([0, -math.cos(psi), math.sin(psi)])
            t = 0.0
            while True:
                q = c + d * t
                a, b = sk.romp_ab(q[2])
                if (q[0] / a) ** 2 + ((q[1] - 0.004 * s) / b) ** 2 > 1 or t > 0.3:
                    break
                t += 0.001
            pad.append(c + d * (t + 0.008 * s))
            nrm.append(d)
        extra = 0.003 * s if sx > 0 else 0.0
        for i, z in enumerate(np.linspace(Z(0.915), Z(0.795), 6)):
            f = i / 5
            x = sx * (0.08 - 0.12 * f) * s
            pad.append(op_romp(x, z, 1, 0.009 * s + extra))
            nrm.append(np.array([0, 1.0, 0.1]))
        pad = np.array(pad)
        tg = np.gradient(pad, axis=0)
        rings = []
        for p_, t_, n_ in zip(pad, tg, nrm):
            t_ = t_ / np.linalg.norm(t_)
            n_ = n_ - np.dot(n_, t_) * t_
            n_ /= np.linalg.norm(n_)
            sd = np.cross(n_, t_)
            hw, th = 0.015 * s, 0.0022 * s
            rings.append([p_ - sd * hw + n_ * th, p_ + sd * hw + n_ * th, p_ + sd * hw - n_ * th, p_ - sd * hw - n_ * th])
        B.grid(np.array(rings[:2]), True, regio=6)                # metalen gesp, vaste kleur
        B.grid(np.array(rings[1:]), True, regio=3)
        sk.bretel[k] = pad
    return B.obj(naam, coll)


def bouw_riem(sk, coll, naam="riem"):
    J = sk.J
    s = sk.s
    v = lambda k: J[k]
    Z = sk.z
    # riem met gele gesp (vaste kleuren)
    B = Bouwer()
    zb = Z(0.645)
    rr = [ring((0, 0.004 * s, z), (1, 0, 0), (0, -1, 0), (0.161 + d) * s, (0.126 + d) * s, 24, 2.3, fase=-np.pi / 2)
          for z, d in ((zb - 0.016 * s, 0.0), (zb - 0.014 * s, 0.006), (zb + 0.013 * s, 0.006), (zb + 0.015 * s, 0.0))]
    B.grid(np.array(rr), True, regio=0)
    gy = (-0.126 - 0.01) * s
    gp = []
    for dy, sc in ((0.004, 1.0), (-0.004, 1.0), (-0.008, 0.8)):
        gp.append([(x * 0.031 * sc * s, gy + dy * s, zb + z * 0.025 * sc * s) for x, z in ((-1, -1), (1, -1), (1, 1), (-1, 1))])
    bg, _ = B.grid(np.array(gp), True, regio=1)
    B.kap(bg + 8, 4, (0, gy - 0.009 * s, zb), regio=1)
    return B.obj(naam, coll)


def bouw_laarzen(sk, coll, naam="laarzen"):
    J = sk.J
    s = sk.s
    v = lambda k: J[k]
    Z = sk.z
    # laarzen: zoolvorm onder, ronde schacht boven; neus iets naar buiten
    B = Bouwer()
    n = 20
    th = 2 * np.pi * np.arange(n) / n
    for k, sx in (("Left", 1), ("Right", -1)):
        an = v(k + "Foot")
        rot = math.radians(8) * sx
        cr, sr = math.cos(rot), math.sin(rot)
        cy, cx = np.sin(th), np.cos(th)
        pe = 2.6
        x = np.sign(cx) * np.abs(cx) ** (2 / pe)
        y = np.sign(cy) * np.abs(cy) ** (2 / pe)
        W = 0.058 * (0.92 + 0.16 * np.clip(y, 0, 1))
        fy = np.where(y > 0, 0.148, 0.07) * y                     # lokaal +y = vooruit
        voet = np.stack([x * W, fy], 1) * s
        cirkel = np.stack([cx * 0.064, cy * 0.064 - 0.004], 1) * s
        prof = [(0.0, 0.0, 1.0), (0.013, 0.0, 1.035), (0.024, 0.0, 0.99), (0.05, 0.12, 0.97), (0.078, 0.42, 1.0),
                (0.105, 0.8, 1.0), (0.135, 1.0, 1.0), (0.165, 1.0, 1.03), (0.198, 1.0, 1.05),
                (0.212, 1.0, 1.1), (0.207, 1.0, 1.17), (0.172, 1.0, 1.19), (0.165, 1.0, 1.08)]
        rings = []
        for z, bl, sc in prof:
            q = (voet * (1 - bl) + cirkel * bl) * sc
            gx, gy = q[:, 0] * cr + q[:, 1] * sr, q[:, 0] * sr - q[:, 1] * cr
            rings.append(np.stack([an[0] + gx, an[1] + gy, np.full(n, z * s)], 1))
        b0, _ = B.grid(np.array(rings[:10]), True, regio=0)
        B.grid(np.array(rings[9:]), True, regio=0)                 # omslag: eigen vel, buitenkant naar buiten
        B.kap(b0, n, (an[0] + sr * 0.049 * s, an[1] - cr * 0.049 * s, 0.0), regio=1, buiten=(0, 0, -1))
    return B.obj(naam, coll)


def bouw_handen(B, sk):
    J = sk.J
    s = sk.s
    v = lambda k: J[k]
    Z = sk.z
    # handen: wanten met duim, langs onderarm-pols-vingertop
    for k, sx in (("Left", 1), ("Right", -1)):
        pts = [v(k + "ForeArm"), v(k + "Hand"), v(k + "HandEnd")]
        L1 = np.linalg.norm(pts[1] - pts[0])
        hs = 1.2 * s
        prof = [(L1 - 0.03 * s, 0.027 * s, 0.029 * s), (L1 - 0.005 * s, 0.026 * s, 0.032 * s)] + \
               [(L1 + d * hs, a * hs, b * hs) for d, a, b in
                ((0.02, 0.025, 0.04), (0.045, 0.026, 0.045), (0.068, 0.025, 0.045), (0.085, 0.022, 0.04),
                 (0.099, 0.017, 0.031), (0.108, 0.009, 0.018))]
        fr = keten(pts, [p[0] for p in prof], zacht=0.03)
        rings = [ring(pos, sd, f, a, b, 12, 2.3) for (pos, t, f, sd), (_, a, b) in zip(fr, prof)]
        b0, _ = B.grid(np.array(rings), True, regio=2)
        pos, t, f, sd = fr[-1]
        B.kap(b0 + 12 * (len(prof) - 1), 12, pos + t * 0.007 * s, regio=2)
        pos, t, f, sd = keten(pts, [L1 + 0.03 * s])[0]           # duim
        bin_ = -np.sign(np.dot(sd, (sx, 0, 0)) + 1e-9) * sd       # naar het lichaam toe
        d = t * 0.55 + f * 0.75 + bin_ * 0.2
        d /= np.linalg.norm(d)
        basis = pos + f * 0.036 * s + bin_ * 0.006 * s
        tp = [basis, basis + d * 0.06 * s]
        tprof = [(-0.005, 0.019, 0.02), (0.022, 0.019, 0.019), (0.043, 0.016, 0.016), (0.058, 0.008, 0.008)]
        tfr = keten(tp, [p[0] * s for p in tprof], ref=tuple(bin_))
        rings = [ring(pp, ss, ff, a * s, b * s, 8) for (pp, tt, ff, ss), (_, a, b) in zip(tfr, tprof)]
        b0, _ = B.grid(np.array(rings), True, regio=4)
        B.kap(b0 + 8 * 3, 8, tfr[-1][0] + tfr[-1][1] * 0.006 * s, regio=4)



def bouw_kop(B, sk, kop):
    J = sk.J
    s = sk.s
    v = lambda k: J[k]
    Z = sk.z
    # hoofd: schedel op ware maat, knolneus, hangsnor (regio 2)
    kk = kop.k
    nphi, nth = 24, 14
    rows = [[kop.punt(np.pi * (0.05 + 0.9 * i / nth), ph) for ph in 2 * np.pi * np.arange(nphi) / nphi]
            for i in range(nth + 1)]
    b0, _ = B.grid(np.array(rows), True, regio=0)
    B.kap(b0, nphi, kop.punt(0, 0), regio=0)
    B.kap(b0 + nphi * nth, nphi, kop.punt(np.pi, 0), regio=0)
    nc = kop.neus
    nr = [ring(nc + np.array([0, dy, z]) * kk, (1, 0, 0), (0, -1, 0), a * kk, b * kk, 10)
          for z, a, b, dy in kop.neusprof]
    b0, _ = B.grid(np.array(nr), True, regio=1)
    B.kap(b0 + 10 * (len(nr) - 1), 10, nc + np.array([0, 0.006, kop.neusprof[-1][0] - 0.004]) * kk, regio=1)
    # oogjes: amandelvormige schijfjes net voor de huid (vaste kleur: oogwit en iris niet tinten)
    for oog in kop.ogen:
        nrm = (oog - kop.C) / np.linalg.norm(oog - kop.C)
        sd = np.cross((0, 0, 1.0), nrm)
        sd /= np.linalg.norm(sd)
        up = np.cross(nrm, sd)
        rand_ = []
        for tt in np.linspace(0, 2 * np.pi, 13)[:-1]:
            x = kop.oog[0] * kk * math.cos(tt)
            zz = (kop.oog[1] if math.sin(tt) > 0 else kop.oog[2]) * kk * math.sin(tt) - 0.0005 * kk
            q = oog + sd * x + up * zz
            dq = (q - kop.C) / np.linalg.norm(q - kop.C)
            ph = math.atan2(dq[0], -dq[1])
            th = math.acos(np.clip(dq[2], -1, 1))
            rand_.append(kop.punt(th, ph, 0.0007 * kk))
        b0 = B.verts(rand_)
        mid = np.mean(rand_, 0) + nrm * 0.0004 * kk
        B.kap(b0, 12, mid, regio=3, buiten=nrm)


def bouw_nek(B, sk):
    J = sk.J
    s = sk.s
    v = lambda k: J[k]
    Z = sk.z
    # nek en bovenborst onder het hemd (huid in de V)
    nk = [(0.905, 0.108, 0.08), (0.94, 0.1, 0.076), (0.975, 0.078, 0.07), (1.0, 0.068, 0.066),
          (1.03, 0.052, 0.052), (1.07, 0.049, 0.049)]
    rings = [ring((0, 0.006 * s, Z(z)), (1, 0, 0), (0, -1, 0), a * s, b * s, 14, 2.2, fase=-np.pi / 2) for z, a, b in nk]
    B.grid(np.array(rings), True, regio=5)


def bouw_lijf(sk, coll, naam="lijf", kopvorm=None, nek=bouw_nek, extra=None):
    """Huid: handen, hoofd (Kop met kopvorm), nek; extra(B, sk, kop) voegt oren/tanden/benen toe."""
    B = Bouwer()
    bouw_handen(B, sk)
    kop = Kop(sk, **(kopvorm or {}))
    sk.kop = kop
    bouw_kop(B, sk, kop)
    if nek:
        nek(B, sk)
    if extra:
        extra(B, sk, kop)
    return B.obj(naam, coll)


def bouw_snor(sk, coll, naam="snor"):
    J = sk.J
    s = sk.s
    v = lambda k: J[k]
    Z = sk.z
    kop = sk.kop
    kk = kop.k
    # snor: dikke hangsnor onder de neus, punten zakken tot onder de mondhoeken
    B = Bouwer()
    xs = np.linspace(-1, 1, 15)
    zm = kop.mond[2]
    posl = []
    for x in xs:
        ax = abs(x)
        px = x * 0.078 * kk
        pz = zm + (0.024 - 0.066 * ax ** 1.8) * kk
        ph = math.atan2(px, 0.09 * kk)
        opp = kop.punt(kop.theta_bij_z(ph, pz), ph)
        posl.append(opp + (opp - kop.C) / np.linalg.norm(opp - kop.C) * (0.011 - 0.004 * ax) * kk)
    posl = np.array(posl)
    tng = np.gradient(posl, axis=0)
    rings = []
    for x, pos, t in zip(xs, posl, tng):
        ax = abs(x)
        t = t / np.linalg.norm(t)
        fw = np.array([0, -1.0, 0]) - np.dot([0, -1.0, 0], t) * t
        fw /= np.linalg.norm(fw)
        up = np.cross(fw, t)
        up *= 1 if up[2] > 0 else -1
        hoog_ = (0.03 * (1 - 0.55 * ax) + 0.007) * kk
        dik = (0.016 * (1 - 0.45 * ax) + 0.005) * kk
        rings.append(ring(pos, up, fw, hoog_ / 2, dik / 2, 8))
    b0, _ = B.grid(np.array(rings), True, regio=0)
    B.kap(b0, 8, rings[0].mean(0) + np.array([-0.004, 0, -0.004]) * kk, regio=0)
    B.kap(b0 + 8 * 14, 8, rings[-1].mean(0) + np.array([0.004, 0, -0.004]) * kk, regio=0)
    return B.obj(naam, coll)


def bouw_haar(sk, coll, naam="haar", lang=False):
    """Krullenbol (man). lang=True (vrouw): de onderrand hangt los (geen trek naar de schedel) en rolt maar
    een vingerdikte naar binnen, zodat de lokken tot op de schouders vallen."""
    J = sk.J
    s = sk.s
    v = lambda k: J[k]
    Z = sk.z
    kop = sk.kop
    kk = kop.k
    # haar: grote krullenbol (klonten in het silhouet), onderrand rolt naar binnen naar de haarlijn
    B = Bouwer()
    nphi = 48
    phs = 2 * np.pi * np.arange(nphi) / nphi
    nrow = 16
    rows = [[] for _ in range(nrow + 3)]
    for ph in phs:
        zb = kop.haargrens(ph) + (0.008 * math.sin(ph * 7 + 1.3) + 0.006 * math.sin(ph * 13 + 0.4)) * kk
        tb = kop.theta_bij_z(ph, zb, lambda t, p: kop.haarpunt(t, p, False))
        for i in range(nrow + 1):
            f = i / nrow
            tht = 0.05 + (tb - 0.05) * (1 - (1 - f) ** 1.3)
            q = kop.haarpunt(tht, ph)
            w = 0.6 * gladstap(0.55, 1.0, f) ** 1.3
            if lang:
                w *= 0.25
            if w > 0:
                d = (q - kop.C) / np.linalg.norm(q - kop.C)
                sch = kop.punt(math.acos(np.clip(d[2], -1, 1)), math.atan2(d[0], -d[1]), 0.016 * kk)
                q = q * (1 - w) + sch * w
            rows[i].append(q)
        rand = rows[nrow][-1]
        hl = kop.punt(kop.theta_bij_z(ph, zb + 0.004 * kk), ph, 0.004 * kk)
        if lang and zb < kop.zz(1.1):
            ax = np.array([kop.C[0], kop.C[1], rand[2]])
            rows[nrow + 1].append(rand + (ax - rand) * 0.05 + np.array([0, 0, 0.006 * kk]))
            rows[nrow + 2].append(rand + (ax - rand) * 0.09 + np.array([0, 0, 0.03 * kk]))
        else:
            rows[nrow + 1].append(rand * 0.45 + hl * 0.55 + np.array([0, 0, 0.012 * kk]))
            rows[nrow + 2].append(hl)
    b0, _ = B.grid(np.array(rows), True, regio=0)
    B.kap(b0, nphi, kop.haarpunt(0, 0), regio=0)
    return B.obj(naam, coll)


# --- Gewichten ---------------------------------------------------------------------------------
@gewicht("kop")
def gw_kop(g):
    P, N, J, G, s, sk, me = g.P, g.N, g.J, g.G, g.s, g.sk, g.me
    voeg, romp_gewicht, romp = g.voeg, g.romp_gewicht, g.romp
    voeg("Head", np.ones(N))


@gewicht("riem")
def gw_riem(g):
    P, N, J, G, s, sk, me = g.P, g.N, g.J, g.G, g.s, g.sk, g.me
    voeg, romp_gewicht, romp = g.voeg, g.romp_gewicht, g.romp
    romp_gewicht(np.ones(N))


@gewicht("tuinbroek")
def gw_tuinbroek(g):
    P, N, J, G, s, sk, me = g.P, g.N, g.J, g.G, g.s, g.sk, g.me
    voeg, romp_gewicht, romp = g.voeg, g.romp_gewicht, g.romp
    reg = vertex_regio(me)
    for r_ in (1, 2, 3, 6):
        romp_gewicht((reg == r_).astype(float))
    for k, sx in (("Left", 1), ("Right", -1)):
        m = (sx * P[:, 0] > 0).astype(float)
        # pijpen
        pts = [J[k + "UpLeg"], J[k + "Leg"], J[k + "Foot"]]
        d, _ = keten_param(P, pts)
        d = np.where(P[:, 2] > J[k + "UpLeg"][2], -(P[:, 2] - J[k + "UpLeg"][2]), d)
        L1 = np.linalg.norm(pts[1] - pts[0])
        L2 = np.linalg.norm(pts[2] - pts[1])
        W = overgang(d, [-0.005 * s, L1, L1 + L2 - 0.01 * s], [0.07 * s, 0.08 * s, 0.03 * s])
        pijp = (reg == 0) * m
        for i, b in enumerate(["Hips", k + "UpLeg", k + "Leg", k + "Foot"]):
            voeg(b, W[:, i] * pijp)
        # zitvlak en kruis van het heupstuk volgen de dij deels
        f = gladstap(sk.z(0.63), sk.z(0.565), P[:, 2]) * 0.55 * gladstap(0.0, 0.07 * s, sx * P[:, 0]) * (reg == 1)
        for b in romp:
            if b in G:
                G[b] *= 1 - f
        voeg(k + "UpLeg", f)
        # bretel over de schouder deels mee met de schouder
        f = gladstap(sk.z(0.92), sk.z(0.96), P[:, 2]) * 0.4 * np.isin(reg, (3, 6)) * m
        for b in romp:
            if b in G:
                G[b] *= 1 - f
        voeg(k + "Shoulder", f)


@gewicht("hemd")
def gw_hemd(g):
    P, N, J, G, s, sk, me = g.P, g.N, g.J, g.G, g.s, g.sk, g.me
    voeg, romp_gewicht, romp = g.voeg, g.romp_gewicht, g.romp
    reg = vertex_regio(me)
    mouw = (reg == 1).astype(float)
    lijf = 1 - mouw
    romp_gewicht(lijf, np.minimum(P[:, 2], J["Neck"][2] + 0.01 * s))
    for k, sx in (("Left", 1), ("Right", -1)):
        m = (sx * P[:, 0] > 0).astype(float)
        pts = sk.mouw[k]
        d, _ = keten_param(P, pts)
        L0 = np.linalg.norm(pts[1] - pts[0])
        L1 = np.linalg.norm(pts[2] - pts[1])
        L2 = np.linalg.norm(pts[3] - pts[2])
        W = overgang(d, [0.025 * s, L0 - 0.005 * s, L0 + L1, L0 + L1 + L2 + 0.012 * s],
                     [0.04 * s, 0.07 * s, 0.08 * s, 0.03 * s])
        for i, b in enumerate(["Spine2", k + "Shoulder", k + "Arm", k + "ForeArm", k + "Hand"]):
            voeg(b, W[:, i] * m * mouw)
        ax = sx * P[:, 0]
        sch = gladstap(0.085 * s, 0.15 * s, ax) * gladstap(sk.z(0.84), sk.z(0.91), P[:, 2]) * lijf * m
        for b in romp:
            if b in G:
                G[b] = G[b] * (1 - sch * 0.55)
        voeg(k + "Shoulder", sch * 0.3)
        voeg(k + "Arm", sch * 0.25)
        f = gladstap(sk.z(0.63), sk.z(0.565), P[:, 2]) * 0.55 * gladstap(0.0, 0.07 * s, ax) * lijf * m
        for b in romp:
            if b in G:
                G[b] *= 1 - f
        voeg(k + "UpLeg", f)


@gewicht("laarzen")
def gw_laarzen(g):
    P, N, J, G, s, sk, me = g.P, g.N, g.J, g.G, g.s, g.sk, g.me
    voeg, romp_gewicht, romp = g.voeg, g.romp_gewicht, g.romp
    for k, sx in (("Left", 1), ("Right", -1)):
        m = (sx * P[:, 0] > 0).astype(float)
        teen = gladstap(J[k + "ToeBase"][1] + 0.025 * s, J[k + "ToeBase"][1] - 0.015 * s, P[:, 1]) * \
            gladstap(0.09 * s, 0.05 * s, P[:, 2])
        schacht = gladstap(0.09 * s, 0.2 * s, P[:, 2]) * 0.85
        voeg(k + "Leg", schacht * m)
        voeg(k + "ToeBase", (1 - schacht) * teen * m)
        voeg(k + "Foot", (1 - schacht) * (1 - teen) * m)


@gewicht("lijf")
def gw_lijf(g):
    P, N, J, G, s, sk, me = g.P, g.N, g.J, g.G, g.s, g.sk, g.me
    voeg, romp_gewicht, romp = g.voeg, g.romp_gewicht, g.romp
    reg = vertex_regio(me)
    kopm = np.isin(reg, (0, 1, 3, 6)).astype(float)                # 6 = oren (niet bij de man)
    t = gladstap(sk.kz - 0.01 * s, sk.kz + 0.035 * s, P[:, 2])
    voeg("Head", t * kopm)
    voeg("Neck", (1 - t) * kopm)
    romp_gewicht((reg == 5).astype(float))
    if getattr(sk, "decollete", False):                            # blote schouders volgen de arm deels
        for k, sx in (("Left", 1), ("Right", -1)):
            ax = sx * P[:, 0]
            sch = gladstap(0.07 * s, 0.14 * s, ax) * (reg == 5)
            for b_ in romp:
                if b_ in G:
                    G[b_] = G[b_] * (1 - sch * 0.6)
            voeg(k + "Shoulder", sch * 0.35)
            voeg(k + "Arm", sch * 0.25)
    benen = (reg == 7).astype(float)                               # 7 = blote kuiten (vrouw)
    if benen.any():
        for k, sx in (("Left", 1), ("Right", -1)):
            m = (sx * P[:, 0] > 0).astype(float) * benen
            pts = [J[k + "UpLeg"], J[k + "Leg"], J[k + "Foot"]]
            d, _ = keten_param(P, pts)
            L1 = np.linalg.norm(pts[1] - pts[0])
            L2 = np.linalg.norm(pts[2] - pts[1])
            W = overgang(d, [L1, L1 + L2 - 0.01 * s], [0.08 * s, 0.03 * s])
            for i, b_ in enumerate([k + "UpLeg", k + "Leg", k + "Foot"]):
                voeg(b_, W[:, i] * m)
    hand = np.isin(reg, (2, 4)).astype(float)
    for k, sx in (("Left", 1), ("Right", -1)):
        m = (sx * P[:, 0] > 0).astype(float) * hand
        pts = [J[k + "ForeArm"], J[k + "Hand"], J[k + "HandEnd"]]
        d, _ = keten_param(P, pts)
        L1 = np.linalg.norm(pts[1] - pts[0])
        vf = np.linalg.norm(J[k + "HandFist"] - J[k + "Hand"])
        W = overgang(d, [L1 - 0.012 * s, L1 + vf + 0.012 * s], [0.03 * s, 0.035 * s])
        duim = (reg == 4).astype(float)
        voeg(k + "ForeArm", W[:, 0] * m * (1 - duim))
        voeg(k + "Hand", (W[:, 1] * (1 - duim) + duim) * m)
        voeg(k + "HandFist", W[:, 2] * m * (1 - duim))


@hoog("hemd", 2, True)
def hg_hemd(h, sk):
    P, Nn, reg, J, s, hgt = h.P, h.Nn, h.reg, h.J, h.s, h.hgt
    mouw = reg == 1
    phi = np.arctan2(P[:, 0], -P[:, 1])
    r1 = ruis(P, 9, 11)
    drape = 0.003 * s * np.sin(phi * 7 + 2.6 * r1) * gladstap(sk.z(0.92), sk.z(0.75), P[:, 2])
    bloes = 0.0035 * s * np.sin(P[:, 2] / (0.02 * s) * 2 * np.pi + 3 * r1) * gauss(P[:, 2] - sk.z(0.70), 0.03 * s)
    hgt += np.where(mouw, 0, drape + bloes)
    for k in ("Left", "Right"):
        pts = sk.mouw[k]
        d, _ = keten_param(P, pts)
        L0 = np.linalg.norm(pts[1] - pts[0])
        e = L0 + np.linalg.norm(pts[2] - pts[1])
        w = e + np.linalg.norm(pts[3] - pts[2])
        band = gauss(d - e, 0.05 * s) + 0.8 * gauss(d - (w - 0.05 * s), 0.045 * s) + \
            0.5 * gauss(d - L0, 0.04 * s)
        zij = (np.sign(P[:, 0]) == (1 if k == "Left" else -1))
        hgt += np.where(mouw & zij, 0.0032 * s * np.sin(d / (0.027 * s) * 2 * np.pi + 2.2 * r1) * band, 0)
    hgt += 0.0016 * s * ruis(P, 30, 12, 2)


@hoog("tuinbroek", 2, True)
def hg_tuinbroek(h, sk):
    P, Nn, reg, J, s, hgt = h.P, h.Nn, h.reg, h.J, h.s, h.hgt
    for k, sx in (("Left", 1), ("Right", -1)):
        pts = [J[k + "UpLeg"], J[k + "Leg"], J[k + "Foot"]]
        d, rv = keten_param(P, pts)
        L1 = np.linalg.norm(pts[1] - pts[0])
        L2 = np.linalg.norm(pts[2] - pts[1])
        r1 = ruis(P, 10, 21 + sx)
        band = 1.1 * gauss(d - (L1 + L2 - 0.2 * s), 0.05 * s) + 0.6 * gauss(d - L1, 0.05 * s)
        ring_ = 0.003 * s * np.sin(d / (0.03 * s) * 2 * np.pi + 2.5 * r1) * band
        ang = np.arctan2(rv[:, 1], rv[:, 0] * sx)
        lang = 0.0018 * s * np.sin(ang * 5 + 2 * r1)
        zij = (sx * P[:, 0] > 0) & (reg == 0)
        hgt += np.where(zij, (ring_ + lang) * (0.5 + 0.5 * ruis(P, 6, 23 + sx)), 0)
    hgt += 0.0015 * s * ruis(P, 25, 22, 2)


@hoog("laarzen", 2, True)
def hg_laarzen(h, sk):
    P, Nn, reg, J, s, hgt = h.P, h.Nn, h.reg, h.J, h.s, h.hgt
    for k, sx in (("Left", 1), ("Right", -1)):
        an = J[k + "Foot"]
        zij = sx * P[:, 0] > 0
        voor = gladstap(an[1] + 0.01 * s, an[1] - 0.05 * s, P[:, 1])
        kreuk = 0.0016 * s * np.sin(P[:, 2] / (0.011 * s) * 2 * np.pi + 3 * ruis(P, 25, 31)) * \
            gladstap(0.045 * s, 0.065 * s, P[:, 2]) * gladstap(0.13 * s, 0.10 * s, P[:, 2]) * voor
        schacht = 0.0012 * s * np.sin(np.arctan2(P[:, 1] - an[1], P[:, 0] - an[0]) * 9 + 2 * ruis(P, 18, 33)) * \
            gladstap(0.11 * s, 0.15 * s, P[:, 2])
        hgt += np.where(zij, kreuk + schacht, 0)
    hgt += 0.0009 * s * ruis(P, 45, 32, 2)


@hoog("snor", 3)
def hg_snor(h, sk):
    P, Nn, reg, J, s, hgt = h.P, h.Nn, h.reg, h.J, h.s, h.hgt
    kk = sk.kop.k
    hgt += 0.0011 * kk * np.sin(2 * np.pi * (P[:, 2] + 0.55 * np.abs(P[:, 0])) / (0.0032 * kk)
                                + 2 * ruis(P, 150, 42)) + 0.0015 * kk * ruis(P, 60, 43)


@hoog("lijf", 3)
def hg_lijf(h, sk):
    P, Nn, reg, J, s, hgt = h.P, h.Nn, h.reg, h.J, h.s, h.hgt
    kop = sk.kop
    kk = kop.k

    def bult(c, r, amp, schaal=(1, 1, 1)):
        return amp * kk * gauss(np.linalg.norm((P - c) * np.array(schaal) / kk, axis=1), r)

    def groef(a_, b_, r, amp):
        ab = b_ - a_
        t = np.clip((P - a_) @ ab / (ab @ ab), 0, 1)
        d = np.linalg.norm(P - (a_ + t[:, None] * ab), axis=1) / kk
        return -amp * kk * gauss(d, r)

    huid = reg == 0
    for oog in kop.ogen:
        sx = np.sign(oog[0])
        hgt += bult(oog, 0.012, -0.003)                                             # oogkas
        hgt += bult(oog + np.array([0, -0.004, 0.0065]) * kk, 0.011, 0.0035, (0.8, 1, 1.9))  # zware oogleden
        hgt += bult(oog + np.array([0, -0.002, -0.012]) * kk, 0.01, 0.0022, (0.8, 1, 2.0))   # wallen
        hgt += bult(oog + np.array([sx * 0.004, 0, 0.022]) * kk, 0.016, 0.0028, (0.6, 1, 1.8))  # wenkbrauwboog
        hgt += bult(oog + np.array([sx * 0.026, -0.004, -0.042]) * kk, 0.028, 0.005)  # hangwangen
        hgt += groef(kop.neus + np.array([sx * 0.026, 0.006, -0.012]) * kk,
                     kop.mond + np.array([sx * 0.04, 0.004, -0.016]) * kk, 0.004, 0.0022)   # neus-mondplooi
    hgt += bult(kop.mond + np.array([0, -0.004, -0.013]) * kk, 0.012, 0.0032, (0.6, 1, 1.8))  # hangende onderlip
    hgt += bult(kop.mond + np.array([0, -0.002, -0.042]) * kk, 0.02, 0.003)                  # kin
    hgt *= huid
    nb = kop.neus + np.array([0, 0.0, -0.03]) * kk                                         # neusgaten
    for sxn in (1, -1):
        hgt += bult(nb + np.array([sxn * 0.011, -0.004, 0.0]) * kk, 0.006, -0.004) * (reg == 1)
    hgt += 0.0005 * kk * ruis(P, 260, 41) * (reg == 1)                                     # pukkelige neus
    hgt += 0.00035 * kk * ruis(P, 300, 44) * huid
    hgt += 0.0007 * s * ruis(P, 150, 51) * np.isin(reg, (2, 4))


@hoog("riem", 2, True)
def hg_riem(h, sk):
    pass


@hoog("haar")
def hg_haar(h, sk):
    P, Nn, reg, J, s, hgt = h.P, h.Nn, h.reg, h.J, h.s, h.hgt
    hgt += 0.006 * s * (0.5 - np.abs(ruis(P, 32, 61, 2))) + 0.002 * s * ruis(P, 90, 62)


# --- Verf -----------------------------------------------------------------------------------------
@verf("hemd")
def vf_hemd(cx):
    P, U, V, z, reg, n, s, J, sk = cx.P, cx.U, cx.V, cx.z, cx.reg, cx.n, cx.s, cx.J, cx.sk
    kl, H, ruw, met, zet = cx.kl, cx.H, cx.ruw, cx.met, cx.zet
    r_groot, r_fijn, wf, B, ys, xs = cx.r_groot, cx.r_fijn, cx.wf, cx.B, cx.ys, cx.xs
    KLEUR, Dm = cx.KLEUR, cx.Dm
    # --- hemd: linnen/wol, effen binding, slubs, naden, open kraag, manchetten
    m = Dm
    if m.any():
        lam = 0.0045
        wv = np.sin(2 * np.pi * U / lam) * np.sin(2 * np.pi * V / lam) * wf
        slub = ruis(np.stack([U * 25, V * 500, np.zeros(n)], 1), 1, 3)
        c = KLEUR[cx.tint][None] * (1 + 0.12 * r_groot[:, None] + 0.05 * r_fijn[:, None] + 0.06 * slub[:, None])
        c *= (1 + 0.05 * wv)[:, None]
        h = 0.0002 * wv + 0.00015 * slub
        mouw = reg == 1
        romp_ = ~mouw
        phi = np.arctan2(P[:, 0], -P[:, 1])
        for fn in (np.pi / 2, -np.pi / 2):
            dphi = np.abs((phi - fn + np.pi) % (2 * np.pi) - np.pi) * 0.15
            naad = gauss(dphi, 0.0015) * romp_ * (z < sk.z(0.93))
            h -= 0.0007 * naad
            c *= (1 - 0.25 * naad)[:, None]
        # kraag en V-randen (de opening is echte geometrie), knoopsluiting onder de V
        voor = P[:, 1] < 0
        ax = np.abs(P[:, 0])
        zv = sk.z(0.93)
        kraag = romp_ & (z > sk.z(0.995))
        c[kraag] *= 0.94
        vg = sk.hemd_v(z)
        vr = romp_ & voor & (z > zv) & (np.abs(ax - vg) < 0.004 * s)
        c[vr] *= 0.78
        h[vr] += 0.0004
        st = romp_ & voor & (z > zv) & (np.abs(ax - vg - 0.007 * s) < 0.001 * s) & (steek(z, 0.006, 0.0037) > 0)
        c[st] *= 0.7
        pl = romp_ & voor & (z < zv + 0.004 * s) & (np.abs(ax - 0.011 * s) < 0.0012 * s)
        c[pl] *= 0.8
        h[pl] -= 0.0004
        for zk in (zv - 0.012 * s, zv - 0.05 * s):
            dk = np.hypot(P[:, 0], z - zk)
            kn = romp_ & voor & (dk < 0.005 * s)
            c[kn] = c[kn] * 0.5 + KLEUR[cx.tint] * 0.7 * (0.8 + 0.2 * (dk[kn] / (0.005 * s)))[:, None]
            h += 0.0009 * romp_ * voor * gladstap(0.005 * s, 0.0035 * s, dk)
        # mouwen: schoudernaad, ellebogen verschoten, manchet met stiksel
        for k in ("Left", "Right"):
            pts = sk.mouw[k]
            zij = (np.sign(P[:, 0]) == (1 if k == "Left" else -1)) & mouw
            d, rv = keten_param(P, pts)
            L0 = np.linalg.norm(pts[1] - pts[0])
            e = L0 + np.linalg.norm(pts[2] - pts[1])
            w = e + np.linalg.norm(pts[3] - pts[2])
            sn = gauss(d - (L0 * 0.75), 0.0015 * s) * zij
            c *= (1 - 0.3 * sn)[:, None]
            h -= 0.0007 * sn
            rn = rv / (np.linalg.norm(rv, axis=1, keepdims=True) + 1e-9)
            el = gauss(d - e, 0.04 * s) * np.clip(rn[:, 1], 0, 1) * zij
            c *= (1 + 0.15 * el)[:, None]
            man = (d > w - 0.03 * s) & zij
            c[man] *= 0.94
            ms = gauss(d - (w - 0.025 * s), 0.0011 * s) * steek(U, 0.006, 0.0038) * zij
            c *= (1 - 0.35 * ms)[:, None]
            h -= 0.0005 * gauss(d - (w - 0.03 * s), 0.0018 * s) * zij
        zet(m, c)
        H[m] = h[m]
        ruw[m] = 0.92


@verf("tuinbroek")
def vf_tuinbroek(cx):
    P, U, V, z, reg, n, s, J, sk = cx.P, cx.U, cx.V, cx.z, cx.reg, cx.n, cx.s, cx.J, cx.sk
    kl, H, ruw, met, zet = cx.kl, cx.H, cx.ruw, cx.met, cx.zet
    r_groot, r_fijn, wf, B, ys, xs = cx.r_groot, cx.r_fijn, cx.wf, cx.B, cx.ys, cx.xs
    KLEUR, Dm = cx.KLEUR, cx.Dm
    # --- tuinbroek: paarse keper, slab met borstzak, bretels met gespen, gulp, vuil onderaan
    m = Dm & ((reg <= 3) | (reg == 6))
    if m.any():
        lam = 0.005
        wv = np.sin(2 * np.pi * (U + V) / lam) * wf
        c = KLEUR[cx.tint][None] * (1 + 0.13 * r_groot[:, None] + 0.06 * r_fijn[:, None] + 0.05 * wv[:, None])
        h = 0.0002 * wv
        voor = P[:, 1] < 0
        pijp = reg == 0
        vuil = gladstap(0.32 * s, 0.17 * s, z) * pijp
        c = c * (1 - 0.4 * vuil[:, None] * (0.6 + 0.4 * r_fijn[:, None])) + \
            srgb("#4a3424")[None] * 0.3 * vuil[:, None] * (0.5 + 0.5 * r_groot[:, None])
        for k, sx in (("Left", 1), ("Right", -1)):
            kn = J[k + "Leg"] + np.array([0, -0.08 * s, 0])
            dk = np.linalg.norm((P - kn) * [1, 1, 0.8], axis=1)
            c *= (1 + 0.16 * gauss(dk, 0.06 * s) * pijp)[:, None]
            pts = [J[k + "UpLeg"], J[k + "Leg"], J[k + "Foot"]]
            d, rv = keten_param(P, pts)
            rn = rv / (np.linalg.norm(rv, axis=1, keepdims=True) + 1e-9)
            naad = gauss(rn[:, 0] * sx - 1, 0.004) * (sx * P[:, 0] > 0) * pijp
            h -= 0.0006 * naad
            c *= (1 - 0.3 * naad)[:, None]
        # gulp
        heup = reg == 1
        gulp = heup & voor & (np.abs(P[:, 0] - 0.022 * s) < 0.0012 * s) & (z > sk.z(0.585)) & (z < sk.z(0.665))
        c[gulp] *= 0.7
        h[gulp] -= 0.0005
        # achterzakken
        for sxk in (1, -1):
            zx, zz = sxk * 0.065 * s, sk.z(0.6)
            zak = heup & ~voor & (np.abs(P[:, 0] - zx) < 0.035 * s) & (np.abs(z - zz) < 0.03 * s)
            zr = zak & ((np.abs(np.abs(P[:, 0] - zx) - 0.035 * s) < 0.0025 * s) | (np.abs(z - zz - 0.03 * s) < 0.0025 * s) |
                        (np.abs(z - zz + 0.03 * s) < 0.0025 * s))
            h[zak] += 0.0005
            c[zr] *= 0.72
        # slab en rugpand: stiksel langs de randen, borstzak op de slab
        pan = reg == 2
        for (zlo, zhi, hb), kant in ((sk.slab, -1), (sk.rug, 1)):
            mk = pan & ((P[:, 1] < 0) if kant < 0 else (P[:, 1] > 0))
            wz = np.array([hb(zz) for zz in np.clip(z, zlo, zhi)])
            rd = np.minimum(wz - np.abs(P[:, 0]), zhi - z)
            st = mk & (np.abs(rd - 0.008 * s) < 0.0011 * s) & (steek(z + P[:, 0], 0.0065, 0.004) > 0)
            c[st] = srgb("#c7a6cf")
            rr_ = mk & (rd < 0.004 * s)
            c[rr_] *= 0.82
        zak = pan & voor & (np.abs(P[:, 0]) < 0.042 * s) & (z > sk.z(0.765)) & (z < sk.z(0.845))
        zr = zak & ((np.abs(np.abs(P[:, 0]) - 0.042 * s) < 0.0025 * s) | (np.abs(z - sk.z(0.765)) < 0.0025 * s) |
                    (np.abs(z - sk.z(0.845)) < 0.0035 * s))
        h[zak] += 0.0009
        c[zr] *= 0.72
        zs_ = zak & (np.abs(np.minimum(0.042 * s - np.abs(P[:, 0]), z - sk.z(0.765)) - 0.005 * s) < 0.001 * s)
        c[zs_] = srgb("#c7a6cf")
        # bretels: iets donkerder, metalen gesp aan de voorkant (eigen regio, vaste kleur)
        br = reg == 3
        c[br] *= 0.9
        gesp = Dm & (reg == 6)
        c[gesp] = KLEUR["metaal"] * (0.85 + 0.15 * r_fijn[gesp, None])
        met[gesp] = 0.9
        ruw[gesp] = 0.38
        h[gesp] += 0.001
        zet(m, c)
        H[m] = h[m]
        ruw[m & ~gesp] = 0.9
        # knoopjes waar de bretels op de slab vastzitten
        for k in ("Left", "Right"):
            kp = sk.bretel[k][0]
            dk = np.linalg.norm(P - kp, axis=1)
            kn = Dm & (dk < 0.007 * s) & (reg != 6)
            kl[kn] = KLEUR["metaal"] * 0.7
            met[kn] = 0.9


@verf("riem")
def vf_riem(cx):
    P, U, V, z, reg, n, s, J, sk = cx.P, cx.U, cx.V, cx.z, cx.reg, cx.n, cx.s, cx.J, cx.sk
    kl, H, ruw, met, zet = cx.kl, cx.H, cx.ruw, cx.met, cx.zet
    r_groot, r_fijn, wf, B, ys, xs = cx.r_groot, cx.r_fijn, cx.wf, cx.B, cx.ys, cx.xs
    KLEUR, Dm = cx.KLEUR, cx.Dm
    # riem en gesp
    m = Dm & (reg == 0)
    c = KLEUR["riem"][None] * (1 + 0.25 * ruis(P, 300, 81)[:, None] + 0.15 * r_groot[:, None])
    zet(m, c)
    H[m] = 0.0003 * ruis(P, 400, 82)[m]
    ruw[m] = 0.55
    m = Dm & (reg == 1)
    c = KLEUR["gesp"][None] * (0.85 + 0.15 * r_fijn[:, None])
    zet(m, c)
    ruw[m] = 0.35
    met[m] = 0.85


@verf("laarzen")
def vf_laarzen(cx):
    P, U, V, z, reg, n, s, J, sk = cx.P, cx.U, cx.V, cx.z, cx.reg, cx.n, cx.s, cx.J, cx.sk
    kl, H, ruw, met, zet = cx.kl, cx.H, cx.ruw, cx.met, cx.zet
    r_groot, r_fijn, wf, B, ys, xs = cx.r_groot, cx.r_fijn, cx.wf, cx.B, cx.ys, cx.xs
    KLEUR, Dm = cx.KLEUR, cx.Dm
    # --- laarzen: leer, nerf, slijtplekken, welnaad, zool, modder
    m = Dm
    if m.any():
        nerf = ruis(P, 500, 91, 2)
        vlek = ruis(P, 25, 92, 3)
        c = KLEUR[cx.tint][None] * (1 + 0.2 * vlek[:, None] + 0.08 * nerf[:, None])
        h = 0.00025 * nerf
        ruwm = 0.55 + 0.15 * vlek
        for k, sx in (("Left", 1), ("Right", -1)):
            an = J[k + "Foot"]
            neus = np.linalg.norm((P - (an + np.array([sx * 0.02, -0.15 * s, 0.035 * s]))) * [1, 1, 1.5], axis=1)
            hiel = np.linalg.norm((P - (an + np.array([0, 0.06 * s, 0.03 * s]))) * [1, 1, 1.5], axis=1)
            sl = (gauss(neus, 0.045 * s) + 0.7 * gauss(hiel, 0.035 * s)) * (sx * P[:, 0] > 0)
            c *= (1 + 0.45 * sl * (0.6 + 0.4 * r_fijn))[:, None]
            ruwm += 0.2 * sl
        modder = gladstap(0.05 * s, 0.015 * s, z)
        c = c * (1 - 0.35 * modder[:, None]) + srgb("#5a4a36")[None] * 0.35 * modder[:, None] * (0.6 + 0.4 * r_groot[:, None])
        zool = (reg == 1) | (z < 0.012 * s)
        c[zool] = KLEUR["zool"] * (1 + 0.2 * r_fijn[zool, None])
        welnaad = gauss(z - 0.02 * s, 0.0012 * s) * steek(U, 0.006, 0.0035)
        c *= (1 - 0.4 * welnaad)[:, None]
        h -= 0.0005 * gauss(z - 0.02 * s, 0.002 * s)
        top = gladstap(0.16 * s, 0.17 * s, z)
        c *= (1 + 0.25 * top)[:, None]
        zet(m, c)
        H[m] = h[m]
        ruw[m] = np.clip(ruwm, 0.4, 0.95)[m]
        ruw[m & zool] = 0.85


@verf("lijf")
def vf_lijf(cx):
    P, U, V, z, reg, n, s, J, sk = cx.P, cx.U, cx.V, cx.z, cx.reg, cx.n, cx.s, cx.J, cx.sk
    kl, H, ruw, met, zet = cx.kl, cx.H, cx.ruw, cx.met, cx.zet
    r_groot, r_fijn, wf, B, ys, xs = cx.r_groot, cx.r_fijn, cx.wf, cx.B, cx.ys, cx.xs
    KLEUR, Dm = cx.KLEUR, cx.Dm
    # --- huid: hoofd en handen
    for nm in ("hoofd", "handen"):
        m = Dm & (np.isin(reg, (0, 1, 3, 5, 6)) if nm == "hoofd" else np.isin(reg, (2, 4, 7)))
        if not m.any():
            continue
        basis = KLEUR[cx.tint] * (np.array([1.03, 0.95, 0.9]) if nm == "handen" else 1)
        por = ruis(P, 900, 101)
        c = basis[None] * (1 + 0.06 * r_groot[:, None] + 0.03 * por[:, None])
        h = 0.00006 * por
        if nm == "hoofd":
            kop = sk.kop
            kk = kop.k
            g = kop.gezicht                                   # leeg = de man
            rood = srgb(g.get("rood", "#c4583e"))
            vlek = 0.5 + 0.5 * ruis(P, 120, 103, 2)
            for oog in kop.ogen:
                sx = np.sign(oog[0])
                wang = oog + np.array([sx * 0.026, -0.012, -0.04]) * kk
                f = g.get("wang", 0.62) * gauss(np.linalg.norm(P - wang, axis=1) / kk, 0.03) * (0.7 + 0.3 * vlek)
                c = c * (1 - f[:, None]) + rood[None] * f[:, None]
            reg_h = np.where(Dm, reg, -1)
            neus = reg_h == 1
            fn = g.get("neusrood", 0.38) * (0.6 + 0.4 * vlek)
            c[neus] = c[neus] * (1 - fn[neus, None]) + rood * fn[neus, None]
            ruw[m] = 0.6
            ruw[m & neus] = 0.58
            huid = reg_h == 0
            # voorhoofdrimpels
            vz = (z - kop.ogen[0][2]) / kk
            rf = g.get("rimpel", 1.0)
            for zr in g.get("voorhoofd", (0.036, 0.046, 0.057)):
                lijn = gauss(vz - zr - 0.002 * np.sin(P[:, 0] / kk * 60), 0.0012) * (np.abs(P[:, 0]) < 0.05 * kk) * \
                    (P[:, 1] < kop.C[1] - 0.05 * kk) * huid
                h -= 0.00045 * kk * lijn * rf
                c *= (1 - 0.18 * rf * lijn)[:, None]
            for oog in kop.ogen:
                sx = np.sign(oog[0])
                do = (P - oog) / kk
                ex = do[:, 0] * sx                                  # naar buiten positief
                voor = (do[:, 1] < 0.012) & huid & (np.sign(P[:, 0]) == sx)
                # kraaienpootjes
                for hk in g.get("kraai", (-0.25, 0.1, 0.45)):
                    kr = gauss((do[:, 2] - hk * (ex - 0.014)), 0.0009) * gladstap(0.013, 0.016, ex) * \
                        gladstap(0.03, 0.024, ex) * voor
                    h -= 0.0004 * kk * kr * rf
                    c *= (1 - 0.15 * rf * kr)[:, None]
                # wallen: iets donkerder, paarsig
                wal = gauss(np.hypot(do[:, 0] / 1.3, (do[:, 2] + 0.011) / 0.6), 0.008) * voor
                wf_ = g.get("wal", 1.0)
                c = c * (1 - 0.18 * wf_ * wal[:, None]) + srgb("#8a5a5a")[None] * 0.12 * wf_ * wal[:, None]
                # slaperig oog: opening is een smalle ellips, het lid hangt tot over de helft van de iris
                ow, oh = g.get("oog_open", (0.0118, 0.0058))
                lz = g.get("lid", 0.0012)
                ox, oz = do[:, 0] / ow, (do[:, 2] + 0.0012) / oh
                open_ = voor & (ox * ox + oz * oz < 1) & (do[:, 2] < lz)
                ir = np.hypot(do[:, 0], do[:, 2] + 0.0008)
                c[open_] = srgb("#e2d6c6")
                iris = open_ & (ir < 0.0063)
                c[iris] = srgb(g.get("iris", "#4a3020")) * (0.8 + 0.4 * (ir[iris] / 0.0063))[:, None]
                pup = open_ & (ir < 0.0029)
                c[pup] = srgb("#0e0806")
                gl = open_ & (np.hypot(do[:, 0] + 0.002 * sx, do[:, 2] - 0.0002) < 0.0012)
                c[gl] = srgb("#f2ece4")
                ruw[m & open_] = 0.12
                lidrand = voor & (np.abs(do[:, 2] - lz) < g.get("wimper", 0.0011)) & (np.abs(do[:, 0]) < 0.0125)
                c[lidrand] = c[lidrand] * 0.35 + srgb("#3a1e14") * 0.3
                lid = voor & (do[:, 2] > lz) & (do[:, 2] < lz + 0.0078) & (np.abs(do[:, 0]) < 0.014) & ~open_
                c[lid] = c[lid] * 0.85 + srgb("#b86a58") * 0.15
                onder = voor & (np.abs(oz + 1.0) < 0.15) & (np.abs(ox) < 0.9)
                c[onder] *= 0.85
                # wenkbrauw: borstelig, buitenkant zakt (droevig-goedig)
                t = np.clip(ex / 0.022, -0.6, 1.2)
                bz, bd, bdik = g.get("brauw", (0.0205, 0.006, 0.0034))
                zb = bz + 0.003 * (1 - t) - bd * t * t
                br = voor & (np.abs(do[:, 2] - zb) < bdik * (1 - 0.3 * t)) & (ex > -0.012) & (ex < 0.026)
                streep = 0.5 + 0.5 * np.sin((do[:, 2] - 0.4 * ex) / 0.0012 + 3 * ruis(P, 400, 104))
                c[br] = KLEUR["snor"] * (0.75 + 0.5 * streep[br, None])
                h[br] += 0.0005 * kk * streep[br]
            dm = (P - kop.mond) / kk
            if g.get("mond", "snor") == "snor":
                # hangende onderlip onder de snor, half open mond
                lipz = dm[:, 2] + 0.012 + 0.006 * (dm[:, 0] / 0.02) ** 2
                onderlip = huid & (np.abs(lipz) < 0.0042) & (np.abs(dm[:, 0]) < 0.021) & (dm[:, 1] < 0.02)
                c[onderlip] = c[onderlip] * 0.4 + srgb("#b05848") * 0.6
                spleet = huid & (np.abs(lipz - 0.0048) < 0.0012) & (np.abs(dm[:, 0]) < 0.018) & (dm[:, 1] < 0.02)
                c[spleet] = srgb("#3a1a14")
            else:
                verf_mond(cx, c, h, dm, huid, g)
            if g.get("stoppels", True):
                # stoppels op kaak en kin
                kaak = gladstap(kop.zz(1.075), kop.zz(1.03), z) * (P[:, 1] < kop.C[1]) * huid
                c *= (1 - 0.14 * kaak * (0.4 + 0.6 * (ruis(P, 2200, 102) > 0.2)))[:, None]
            if g.get("extra"):
                g["extra"](cx, c, h, huid, reg_h)
            # nek iets roder (zon), oogjes op de schijfjes (vaste kleur)
            nek = reg_h == 5
            c[nek] = c[nek] * 0.9 + rood * 0.1
            for oog in kop.ogen:
                sx = np.sign(oog[0])
                do = (P - oog) / kk
                sch = Dm & (reg == 3) & (np.sign(P[:, 0]) == sx) & (np.linalg.norm(do, axis=1) < 0.025)
                c[sch] = srgb("#ddd2c2")
                ir = np.hypot(do[:, 0], do[:, 2] + 0.0012)
                iris = sch & (ir < 0.0064)
                c[iris] = srgb(g.get("iris", "#4a3020")) * (0.75 + 0.45 * (ir[iris] / 0.0064))[:, None]
                pup = sch & (ir < 0.0029)
                c[pup] = srgb("#0e0806")
                gl = sch & (np.hypot(do[:, 0] + 0.002 * sx, do[:, 2] - 0.0) < 0.0011)
                c[gl] = srgb("#f2ece4")
                lid = sch & (do[:, 2] > g.get("schijf_lid", -0.0006))
                c[lid] = srgb(g.get("lidkleur", "#5a3024"))
                hoek = sch & (np.abs(do[:, 0]) > 0.0105)
                c[hoek] = c[hoek] * 0.6 + srgb("#b0706a") * 0.4
                ruw[sch] = 0.12
            # tanden: regio 3 ver van de ogen (vaste kleur)
            ver = np.ones(n, bool)
            for oog in kop.ogen:
                ver &= np.linalg.norm((P - oog) / kk, axis=1) >= 0.025
            tand = Dm & (reg == 3) & ver
            c[tand] = srgb(g.get("tand", "#e6dcc4")) * (0.9 + 0.1 * r_fijn[tand, None])
            ruw[tand] = 0.3
        else:
            # wanten-vingers: drie groeven over het vingerdeel, knokkels
            for k, sx in (("Left", 1), ("Right", -1)):
                pts = [J[k + "Hand"], J[k + "HandEnd"]]
                d, rv = keten_param(P, pts)
                t = (pts[1] - pts[0]) / np.linalg.norm(pts[1] - pts[0])
                f = np.array([0, -1, 0]) - np.dot([0, -1, 0], t) * t
                f /= np.linalg.norm(f)
                w = rv @ f
                zij = (sx * P[:, 0] > 0) & (reg == 2) & Dm
                vinger = gladstap(0.05 * s, 0.065 * s, d) * zij
                g = sum(gauss(w - o_, 0.0022 * s) for o_ in (-0.024 * s, 0.0, 0.024 * s))
                g = g * vinger * (np.abs(w) < 0.045 * s)
                h -= 0.0012 * g
                c *= (1 - 0.25 * g)[:, None]
                kn = gauss(d - 0.055 * s, 0.004 * s) * zij
                c *= (1 - 0.15 * kn)[:, None]
                h -= 0.0005 * kn
            ruw[m] = 0.6
        zet(m, c)
        H[m] = h[m]


def verf_mond(cx, c, h, dm, huid, g):
    """Mond zonder snor: lippen, mondspleet, glimlach (mondhoeken omhoog), lachplooien."""
    kk = cx.sk.kop.k
    lach = g.get("lach", 0.006)                     # hoe ver de mondhoeken omhoog gaan
    bw = g.get("mondbreed", 0.021)
    x = dm[:, 0] / bw
    lijn = dm[:, 2] - lach * x * x                 # z t.o.v. de mondlijn
    binnen = huid & (np.abs(x) < 1) & (dm[:, 1] < 0.02)
    lipk = srgb(g.get("lip", "#b86058"))
    bov = binnen & (lijn > 0) & (lijn < g.get("bovenlip", 0.0032) * (1 - 0.6 * x * x))
    ond = binnen & (lijn < 0) & (lijn > -g.get("onderlip", 0.0045) * (1 - 0.6 * x * x))
    c[bov] = c[bov] * 0.55 + lipk * 0.45
    c[ond] = c[ond] * 0.45 + lipk * 0.55
    sp = huid & (np.abs(lijn) < g.get("spleet", 0.0011) * (1 - 0.5 * x * x)) & (np.abs(x) < 1.02) & (dm[:, 1] < 0.02)
    c[sp] = srgb("#3a1a14")
    h[sp] -= 0.0006 * kk
    op = g.get("open", 0.0)                                        # open mond: donkere holte onder de spleet
    if op:
        mo = huid & (lijn < 0) & (lijn > -op * (1 - 0.7 * x * x)) & (np.abs(x) < 0.95) & (dm[:, 1] < 0.02)
        c[mo] = srgb("#4a1c18") * (0.8 + 0.4 * np.clip(-lijn[mo] / op, 0, 1))[:, None]
        h[mo] -= 0.001 * kk
        ond2 = binnen & (lijn <= -op * (1 - 0.7 * x * x)) & (lijn > -(op + g.get("onderlip", 0.0045)) * (1 - 0.6 * x * x))
        c[ond2] = c[ond2] * 0.45 + lipk * 0.55
    # mondhoeken en lachplooien
    for sx in (1, -1):
        hoek = np.hypot(dm[:, 0] - sx * bw * 1.05, dm[:, 2] - lach) / 0.004
        c *= (1 - 0.25 * gauss(hoek, 1.0) * huid)[:, None]


@verf("snor")
def vf_snor(cx):
    P, U, V, z, reg, n, s, J, sk = cx.P, cx.U, cx.V, cx.z, cx.reg, cx.n, cx.s, cx.J, cx.sk
    kl, H, ruw, met, zet = cx.kl, cx.H, cx.ruw, cx.met, cx.zet
    r_groot, r_fijn, wf, B, ys, xs = cx.r_groot, cx.r_fijn, cx.wf, cx.B, cx.ys, cx.xs
    KLEUR, Dm = cx.KLEUR, cx.Dm
    # --- snor: donkerbruin met haarstrepen, puntjes lichter
    m = Dm
    if m.any():
        kk = sk.kop.k
        strp = 0.5 + 0.5 * np.sin(2 * np.pi * (z + 0.55 * np.abs(P[:, 0])) / (0.0032 * kk) + 2 * ruis(P, 150, 42))
        pt = gladstap(0.02 * kk, 0.05 * kk, np.abs(P[:, 0]))
        cs = KLEUR["snor"][None] * (0.7 + 0.55 * strp[:, None]) * (1 + 0.35 * pt[:, None])
        zet(m, cs)
        ruw[m] = 0.72


@verf("haar")
def vf_haar(cx):
    P, U, V, z, reg, n, s, J, sk = cx.P, cx.U, cx.V, cx.z, cx.reg, cx.n, cx.s, cx.J, cx.sk
    kl, H, ruw, met, zet = cx.kl, cx.H, cx.ruw, cx.met, cx.zet
    r_groot, r_fijn, wf, B, ys, xs = cx.r_groot, cx.r_fijn, cx.wf, cx.B, cx.ys, cx.xs
    KLEUR, Dm = cx.KLEUR, cx.Dm
    # --- haar: lokkleur uit de bake
    m = Dm
    kb = B["kleur"][ys, xs, :3]
    c = kb * (1 + 0.1 * r_fijn[:, None])
    hl = getattr(sk, "haarlicht", None)                       # (meng, versterking): lichter blond (vrouw)
    if hl:
        c = (c * (1 - hl[0]) + KLEUR[cx.tint][None] * hl[0]) * hl[1]
    zet(m, c)
    ruw[m] = 0.82



GEWICHT["haar"] = GEWICHT["snor"] = GEWICHT["kop"]          # alles op Head


# ================================================================================================
# Nieuwe soorten (vrouw, kinderen, ouderen)
# ================================================================================================
def mouw_punten(sk, k):
    """Zelfde mouwas als het hemd van de man: wortel in de romp, schouder, elleboog, pols."""
    J = sk.J
    s = sk.s
    sch = J[k + "Arm"]
    wortel = sch * np.array([0.42, 1, 1]) + np.array([0, 0, 0.018 * s])
    return [wortel, sch, J[k + "ForeArm"], J[k + "Hand"]]


def mouw_profiel(L0, e, w, dik=1.0, wijd=1.0):
    """Mouwprofiel (d, a, b) als bij het hemd; wijd > 1 maakt de mouw naar de pols wijder (jurk, jasje).
    De laatste vijf ringen zijn de manchet/omslag (regio 4)."""
    mp = [(0.0, 0.045, 0.05), (L0 * 0.5, 0.058, 0.065), (L0, 0.061, 0.066), (L0 + 0.05, 0.058, 0.061),
          (L0 + 0.11, 0.055, 0.057), (e - 0.03, 0.053, 0.055), (e, 0.053, 0.055), (e + 0.03, 0.052, 0.054),
          (e + 0.09, 0.051, 0.052), (w - 0.04, 0.05, 0.051), (w - 0.03, 0.043, 0.044), (w + 0.004, 0.045, 0.046),
          (w + 0.006, 0.036, 0.037), (w - 0.015, 0.034, 0.035)]
    uit = []
    for d, a, b in mp:
        f = np.clip((d - L0) / max(w - L0, 1e-6), 0, 1)
        g = 1 + (wijd - 1) * f
        uit.append((d, a * dik * g, b * dik * g))
    return uit


def bouw_kledij(sk, coll, naam, rijen, hals="rond", mouwen=True, mouw_dik=1.0, mouw_wijd=1.0,
                dikte=0.008, K=34, kraag=None, zoom=0.014, p=2.2, manchet=4, golf=0.0):
    """Generiek kledingstuk: romp-loft van rijen (z0, a, bv, ba, halve opening voor) van hals naar zoom,
    plus mouwen. z0 via Skelet.zr (onder de heup naar de beenlengte). Regio's: 0 lijf, 1 mouw, 2 zoom
    (omslag), 3 kraag/halsrand, 4 manchet. Zonder opening is de loft gesloten (naad achter); met een
    opening (V-hals of open jasje) open aan de voorkant met omgeslagen randen. kraag=(hoogte,): staande
    kraag; golf: de bovenrand loopt aan de zijkanten zoveel (z0) hoger (off-shoulder over de bovenarmen)."""
    s = sk.s
    Z = sk.zr
    B = Bouwer()
    t = dikte * s
    open_ = any(r[4] > 0 for r in rijen)
    P = []
    for i_r, (z0, a, bv, ba, g) in enumerate(rijen):
        a, bv, ba, g = a * s, bv * s, ba * s, g * s
        if open_:
            f0 = math.asin(min(0.95, g / a)) if g > 0 else 0.0
            kol = [(f0 + 0.25, t), (f0, t)] + [(f0 + (2 * np.pi - 2 * f0) * k / (K - 1), 0.0) for k in range(K)] +                   [(2 * np.pi - f0, t), (2 * np.pi - f0 - 0.25, t)]
        else:
            kol = [(np.pi + 2 * np.pi * k / K, 0.0) for k in range(K)]
        gw = golf * max(0.0, 1 - i_r / 2.0)
        rij = []
        for ph, i2 in kol:
            cp, sp = math.cos(ph), math.sin(ph)
            xs = np.sign(sp) * abs(sp) ** (2 / p)
            yc = np.sign(cp) * abs(cp) ** (2 / p)
            b = bv if cp > 0 else ba
            rij.append((xs * (a - i2), 0.004 * s - yc * (b - i2), Z(z0 + gw * sp * sp)))
        P.append(rij)
    P = np.array(P)
    sl = not open_
    # zoom: omslag naar binnen
    onder = P[-1]
    c = np.array([0, 0.004 * s, onder[0, 2]])
    binnen = c + (onder - c) * np.array([0.93, 0.93, 1.0]) + np.array([0, 0, zoom * s])
    B.grid(P, sl, regio=0, buiten=None if sl else (0, 1, 0))
    B.grid(np.array([P[-1], binnen]), sl, regio=2, buiten=None if sl else (0, 1, 0))
    # bovenrand: staande kraag of omgerolde rand naar binnen
    top = P[0]
    c = np.array([0, 0.004 * s, 0.0])
    if kraag:
        hk = kraag[0] * s
        r1 = c + (top - c) * np.array([0.96, 0.96, 1]) + np.array([0, 0, hk])
        r2 = c + (top - c) * np.array([0.9, 0.9, 1]) + np.array([0, 0, hk])
        r3 = c + (top - c) * np.array([0.86, 0.86, 1]) + np.array([0, 0, -0.01 * s])
        rand = [r3, r2, r1, top]
    else:
        r1 = c + (top - c) * np.array([1.015, 1.015, 1]) + np.array([0, 0, 0.004 * s])
        r2 = c + (top - c) * np.array([0.95, 0.95, 1]) + np.array([0, 0, 0.006 * s])
        r3 = c + (top - c) * np.array([0.9, 0.9, 1]) + np.array([0, 0, -0.012 * s])
        rand = [r3, r2, r1, top]
    B.grid(np.array(rand), sl, regio=3, buiten=None if sl else (0, 1, 0))
    rz_ = np.array([Z(r[0]) for r in rijen])[::-1]
    ra_ = np.array([r[1] * s for r in rijen])[::-1]
    rb_ = np.array([max(r[2], r[3]) * s for r in rijen])[::-1]
    sk.kledij_ab = getattr(sk, "kledij_ab", {})
    sk.kledij_ab[naam] = lambda z: (float(np.interp(z, rz_, ra_)), float(np.interp(z, rz_, rb_)))
    sk.kledij_z = getattr(sk, "kledij_z", {})
    sk.kledij_z[naam] = (Z(rijen[-1][0]), Z(rijen[0][0]))
    sk.mouwen = getattr(sk, "mouwen", {})
    if mouwen:
        sk.mouwen[naam] = {}
        for k in ("Left", "Right"):
            pts = mouw_punten(sk, k)
            sk.mouwen[naam][k] = pts
            L0 = np.linalg.norm(pts[1] - pts[0])
            L1 = np.linalg.norm(pts[2] - pts[1])
            L2 = np.linalg.norm(pts[3] - pts[2])
            e, w = L0 + L1, L0 + L1 + L2
            mp = mouw_profiel(L0, e, w, mouw_dik, mouw_wijd)
            fr = keten(pts, [q[0] for q in mp], zacht=0.05)
            rings = [ring(pos, sd, f, a * s, b * s, 16, 2.1) for (pos, tt, f, sd), (_, a, b) in zip(fr, mp)]
            B.grid(np.array(rings[:-manchet + 1]), True, regio=1)
            B.grid(np.array(rings[-manchet:]), True, regio=4)
    return B.obj(naam, coll)


def zijde(P, s):
    """0..1: hoeveel een punt bij de linkerkant hoort (zacht over het midden)."""
    return gladstap(-0.035 * s, 0.035 * s, P[:, 0])


@gewicht("kledij")
def gw_kledij(g):
    P, N, J, G, s, sk, me = g.P, g.N, g.J, g.G, g.s, g.sk, g.me
    voeg, romp_gewicht, romp = g.voeg, g.romp_gewicht, g.romp
    reg = vertex_regio(me)
    mouw = np.isin(reg, (1, 4)).astype(float)
    lijf = 1 - mouw
    romp_gewicht(lijf, np.minimum(P[:, 2], J["Neck"][2] + 0.01 * s))
    links = zijde(P, s)
    for k, sx in (("Left", 1), ("Right", -1)):
        m = (sx * P[:, 0] > 0).astype(float)
        ax = sx * P[:, 0]
        if g.naam in getattr(sk, "mouwen", {}):
            pts = sk.mouwen[g.naam][k]
            d, _ = keten_param(P, pts)
            L0 = np.linalg.norm(pts[1] - pts[0])
            L1 = np.linalg.norm(pts[2] - pts[1])
            L2 = np.linalg.norm(pts[3] - pts[2])
            W = overgang(d, [0.025 * s, L0 - 0.005 * s, L0 + L1, L0 + L1 + L2 + 0.012 * s],
                         [0.04 * s, 0.07 * s, 0.08 * s, 0.03 * s])
            for i, b in enumerate(["Spine2", k + "Shoulder", k + "Arm", k + "ForeArm", k + "Hand"]):
                voeg(b, W[:, i] * m * mouw)
        # schouderpartij van het lijf mee met de schouder (als het hemd)
        sch = gladstap(0.085 * s, 0.15 * s, ax) * gladstap(sk.z(0.84), sk.z(0.91), P[:, 2]) * lijf * m
        for b in romp:
            if b in G:
                G[b] = G[b] * (1 - sch * 0.55)
        voeg(k + "Shoulder", sch * 0.3)
        voeg(k + "Arm", sch * 0.25)
        # rok/pand onder de heup: steeds meer met het bovenbeen mee, links/rechts zacht over het midden
        kant = links if sx > 0 else 1 - links
        diep = gladstap(sk.zr(0.64), sk.zr(0.52), P[:, 2])
        f = diep * (0.65 + 0.27 * gladstap(sk.zr(0.52), sk.zr(0.35), P[:, 2])) * kant * lijf
        for b in romp:
            if b in G:
                G[b] *= 1 - f
        # lange rok: onder de knie deels met het scheenbeen mee (anders steekt de laars er achter uit)
        kuit = gladstap(sk.zr(0.36), sk.zr(0.18), P[:, 2]) * 0.4 * kant * lijf
        voeg(k + "UpLeg", f * (1 - kuit))
        voeg(k + "Leg", f * kuit)


@hoog("kledij", 2, True)
def hg_kledij(h, sk):
    P, Nn, reg, J, s, hgt = h.P, h.Nn, h.reg, h.J, h.s, h.hgt
    mouw = np.isin(reg, (1, 4))
    phi = np.arctan2(P[:, 0], -P[:, 1])
    r1 = ruis(P, 9, 11)
    z = P[:, 2]
    drape = 0.003 * s * np.sin(phi * 7 + 2.6 * r1) * gladstap(sk.z(0.92), sk.z(0.75), z)
    rok = gladstap(sk.zr(0.62), sk.zr(0.3), z)                   # rok: vallende plooien, dieper naar de zoom
    plooi = 0.006 * s * np.sin(phi * 9 + 3.0 * r1) * rok
    hgt += np.where(mouw, 0, drape + plooi)
    for k in ("Left", "Right"):
        pts = getattr(sk, "mouwen", {}).get(h.naam, {}).get(k)
        if pts is None:
            continue
        d, _ = keten_param(P, pts)
        L0 = np.linalg.norm(pts[1] - pts[0])
        e = L0 + np.linalg.norm(pts[2] - pts[1])
        w = e + np.linalg.norm(pts[3] - pts[2])
        band = gauss(d - e, 0.05 * s) + 0.8 * gauss(d - (w - 0.05 * s), 0.045 * s) + 0.5 * gauss(d - L0, 0.04 * s)
        zij = (np.sign(P[:, 0]) == (1 if k == "Left" else -1))
        hgt += np.where(mouw & zij, 0.0032 * s * np.sin(d / (0.027 * s) * 2 * np.pi + 2.2 * r1) * band, 0)
    hgt += 0.0016 * s * ruis(P, 30, 12, 2)


@verf("kledij")
def vf_kledij(cx):
    """Wol/linnen: binding, slubs, zijnaden, zoom met stiksel, halsrand, vuil onderaan, manchet.
    Per deel instelbaar via sk.stof[naam] = dict(weef, keper, vlek, vuil, vuil_hoogte, kraag, manchet)."""
    P, U, V, z, reg, n, s, sk = cx.P, cx.U, cx.V, cx.z, cx.reg, cx.n, cx.s, cx.sk
    ruw, zet, H = cx.ruw, cx.zet, cx.H
    r_groot, r_fijn, wf = cx.r_groot, cx.r_fijn, cx.wf
    KLEUR, m = cx.KLEUR, cx.Dm
    st = getattr(sk, "stof", {}).get(cx.naam, {})
    lam = st.get("weef", 0.0045)
    if st.get("keper"):
        wv = np.sin(2 * np.pi * (U + V) / lam) * wf
    else:
        wv = np.sin(2 * np.pi * U / lam) * np.sin(2 * np.pi * V / lam) * wf
    slub = ruis(np.stack([U * 25, V * 500, np.zeros(n)], 1), 1, 3)
    vl = 0.5 + 0.5 * ruis(P, 14, 7, 2)
    c = KLEUR[cx.tint][None] * (1 + st.get("vlek", 0.12) * r_groot[:, None] + 0.05 * r_fijn[:, None] +
                                0.06 * slub[:, None])
    c *= (1 + 0.05 * wv)[:, None]
    h = 0.0002 * wv + 0.00015 * slub
    mouw = np.isin(reg, (1, 4))
    romp_ = ~mouw
    phi = np.arctan2(P[:, 0], -P[:, 1])
    for fn in (np.pi / 2, -np.pi / 2):                            # zijnaden
        dphi = np.abs((phi - fn + np.pi) % (2 * np.pi) - np.pi) * 0.15
        naad = gauss(dphi, 0.0015) * romp_
        h -= 0.0007 * naad
        c *= (1 - 0.25 * naad)[:, None]
    zl, zh = getattr(sk, "kledij_z", {}).get(cx.naam, (0.0, 0.0))
    zoom = romp_ & (z < zl + 0.022 * s)                           # zoom: rand donkerder, stiksel erboven
    c[zoom] *= 0.88
    zs = romp_ & (np.abs(z - (zl + 0.02 * s)) < 0.0012 * s) & (steek(U, 0.006, 0.0037) > 0)
    c[zs] *= 0.72
    h -= 0.0005 * gauss(z - (zl + 0.022 * s), 0.0018 * s) * romp_
    c[reg == 2] *= 0.8
    c[reg == 3] *= st.get("kraag", 0.92)
    vu = st.get("vuil", 0.0)
    if vu:                                                        # vuil en verkleuring onderaan
        vz = gladstap(zl + st.get("vuil_hoogte", 0.2) * s, zl, z) * romp_
        c = c * (1 - vu * vz[:, None] * (0.6 + 0.4 * vl[:, None])) + \
            srgb("#5a4a36")[None] * vu * 0.5 * vz[:, None] * vl[:, None]
    for k in ("Left", "Right"):                                   # schoudernaad, ellebogen verschoten
        pts = getattr(sk, "mouwen", {}).get(cx.naam, {}).get(k)
        if pts is None:
            continue
        zij = (np.sign(P[:, 0]) == (1 if k == "Left" else -1)) & mouw
        d, rv = keten_param(P, pts)
        L0 = np.linalg.norm(pts[1] - pts[0])
        e = L0 + np.linalg.norm(pts[2] - pts[1])
        sn = gauss(d - (L0 * 0.75), 0.0015 * s) * zij
        c *= (1 - 0.3 * sn)[:, None]
        h -= 0.0007 * sn
        rn = rv / (np.linalg.norm(rv, axis=1, keepdims=True) + 1e-9)
        el = gauss(d - e, 0.04 * s) * np.clip(rn[:, 1], 0, 1) * zij
        c *= (1 + 0.15 * el)[:, None]
    man = reg == 4
    if st.get("manchet"):
        c[man] = KLEUR[st["manchet"]] * (1 + 0.1 * r_groot[man, None] + 0.05 * slub[man, None])
    else:
        c[man] *= 0.9
    zet(m, c)
    H[m] = h[m]
    ruw[m] = 0.92


def bouw_broek(sk, coll, naam="broek", dik=1.0, heup=True, wijd_onder=1.0):
    """Broek of maillot: pijpen en heupstuk van de tuinbroek (regio 0 pijpen, 1 heupstuk), zonder slab.
    Gewicht en plooien als de tuinbroek, eigen schilder 'broek'."""
    J = sk.J
    s = sk.s
    Z = sk.z
    B = Bouwer()
    for k, sx in (("Left", 1), ("Right", -1)):
        pts = [J[k + "UpLeg"], J[k + "Leg"], J[k + "Foot"]]
        L1 = np.linalg.norm(pts[1] - pts[0])
        L2 = np.linalg.norm(pts[2] - pts[1])
        q = s
        prof = [(-0.03 * q, 0.078, 0.082), (0.0, 0.085, 0.09), (0.04 * q, 0.087, 0.093), (0.10 * q, 0.087, 0.091),
                (0.17 * q, 0.085, 0.088), (L1 - 0.05 * q, 0.082, 0.085), (L1 - 0.02 * q, 0.08, 0.083),
                (L1, 0.079, 0.084), (L1 + 0.035 * q, 0.079, 0.082), (L1 + 0.08 * q, 0.077, 0.079),
                (L1 + L2 - 0.18 * q, 0.068, 0.069), (L1 + L2 - 0.14 * q, 0.06, 0.06), (L1 + L2 - 0.09 * q, 0.054, 0.054),
                (L1 + L2 - 0.03 * q, 0.05, 0.05), (L1 + L2 + 0.0, 0.048, 0.048)]
        fr = keten(pts, [q[0] for q in prof], zacht=0.06)
        rings = []
        for (pos, t, f, sd), (d, a, b) in zip(fr, prof):
            fd = np.clip(d / (L1 + L2), 0, 1)
            dk = dik * (1 + (wijd_onder - 1) * fd)
            inw = np.array([-sx * 0.014 * s * (1 - np.clip(d / L1, 0, 1)), 0, 0])
            rings.append(ring(pos + inw, sd, f, a * s * dk, b * s * dk, 16, 2.2))
        B.grid(np.array(rings), True, regio=0)
    if heup:
        hp = [(0.545, 0.10, 0.08), (0.57, 0.13, 0.10), (0.60, 0.152, 0.12), (0.64, 0.161, 0.126),
              (0.68, 0.163, 0.127), (0.687, 0.156, 0.12), (0.672, 0.148, 0.113)]
        rings = [ring((0, 0.004 * s, Z(z)), (1, 0, 0), (0, -1, 0), a * s * dik, b * s * dik, 22, 2.3, fase=-np.pi / 2)
                 for z, a, b in hp]
        b0, _ = B.grid(np.array(rings), True, regio=1)
        B.kap(b0, 22, (0, 0.004 * s, Z(0.53)), regio=1)
    return B.obj(naam, coll)


@verf("broek")
def vf_broek(cx):
    """Wollen broek of gebreide maillot (sk.stof[naam]['brei']): binding, kniestukken, naden, vuil."""
    P, U, V, z, reg, n, s, J, sk = cx.P, cx.U, cx.V, cx.z, cx.reg, cx.n, cx.s, cx.J, cx.sk
    ruw, zet, H = cx.ruw, cx.zet, cx.H
    r_groot, r_fijn, wf = cx.r_groot, cx.r_fijn, cx.wf
    KLEUR, m = cx.KLEUR, cx.Dm
    st = getattr(sk, "stof", {}).get(cx.naam, {})
    if st.get("brei"):
        lam = 0.0035
        wv = (np.abs(np.sin(np.pi * U / lam + 0.5 * np.sin(2 * np.pi * V / (lam * 1.4)))) * 2 - 1) * wf
    else:
        wv = np.sin(2 * np.pi * (U + V) / 0.005) * wf
    c = KLEUR[cx.tint][None] * (1 + 0.12 * r_groot[:, None] + 0.06 * r_fijn[:, None] + 0.06 * wv[:, None])
    h = 0.00025 * wv
    pijp = reg == 0
    vuil = gladstap(0.3 * s, 0.16 * s, z) * pijp * st.get("vuil", 1.0)
    c = c * (1 - 0.35 * vuil[:, None] * (0.6 + 0.4 * r_fijn[:, None])) + \
        srgb("#4a3424")[None] * 0.25 * vuil[:, None] * (0.5 + 0.5 * r_groot[:, None])
    for k, sx in (("Left", 1), ("Right", -1)):
        kn = J[k + "Leg"] + np.array([0, -0.06 * s, 0])
        dk = np.linalg.norm((P - kn) * [1, 1, 0.8], axis=1)
        c *= (1 + st.get("knie", 0.16) * gauss(dk, 0.05 * s) * pijp)[:, None]
        pts = [J[k + "UpLeg"], J[k + "Leg"], J[k + "Foot"]]
        d, rv = keten_param(P, pts)
        rn = rv / (np.linalg.norm(rv, axis=1, keepdims=True) + 1e-9)
        for nx in (1, -1):
            naad = gauss(rn[:, 0] * sx * nx - 1, 0.004) * (sx * P[:, 0] > 0) * pijp
            h -= 0.0006 * naad
            c *= (1 - 0.25 * naad)[:, None]
    zet(m, c)
    H[m] = h[m]
    ruw[m] = 0.9


@hoog("broek", 2, True)
def hg_broek(h, sk):
    HOOG["tuinbroek"][0](h, sk)


GEWICHT["broek"] = GEWICHT["tuinbroek"]


def bouw_riem_op(sk, coll, naam="riem", z0=0.645, a=0.161, b=0.126, gesp="vierkant", gesp_b=0.031, gesp_h=0.025,
                 breed=0.015):
    """Riem op een willekeurige hoogte/omtrek (a, b bij de man-maat, z0 via zr); gesp vierkant of rond (regio 1).
    Zelfde soort als de riem van de man (gewicht, hoog, verf)."""
    s = sk.s
    zb = sk.zr(z0)
    B = Bouwer()
    rr = [ring((0, 0.004 * s, z), (1, 0, 0), (0, -1, 0), (a + d) * s, (b + d) * s, 28, 2.3, fase=-np.pi / 2)
          for z, d in ((zb - (breed + 0.001) * s, 0.0), (zb - breed * s, 0.006), (zb + breed * s, 0.006),
                       (zb + (breed + 0.001) * s, 0.0))]
    B.grid(np.array(rr), True, regio=0)
    gy = (-b - 0.01) * s
    if gesp == "rond":
        n = 14
        th = 2 * np.pi * np.arange(n) / n
        gp = []
        for dy, sc in ((0.004, 1.0), (-0.003, 1.0), (-0.007, 0.78)):
            gp.append([(math.cos(t_) * gesp_b * sc * s, gy + dy * s, zb + math.sin(t_) * gesp_h * sc * s) for t_ in th])
        bg, _ = B.grid(np.array(gp), True, regio=1)
        B.kap(bg + 2 * n, n, (0, gy - 0.0085 * s, zb), regio=1)
    else:
        gp = []
        for dy, sc in ((0.004, 1.0), (-0.004, 1.0), (-0.008, 0.8)):
            gp.append([(x * gesp_b * sc * s, gy + dy * s, zb + zz * gesp_h * sc * s)
                       for x, zz in ((-1, -1), (1, -1), (1, 1), (-1, 1))])
        bg, _ = B.grid(np.array(gp), True, regio=1)
        B.kap(bg + 8, 4, (0, gy - 0.009 * s, zb), regio=1)
    return B.obj(naam, coll)


# --- lijf-extra's: oren, tanden, blote kuiten, decollete --------------------------------------------
def bouw_oren(B, sk, kop, grootte=1.0, uitstaan=0.35, z0=1.10, ph=1.62):
    """Twee oren (regio 6): afgeplatte schelp op de zijkant van de schedel, staan `uitstaan` rad naar voren uit."""
    kk = kop.k * grootte
    for sx in (1, -1):
        p = kop.punt(kop.theta_bij_z(sx * ph, kop.zz(z0)), sx * ph, -0.004 * kop.k)
        uit = np.array([sx, 0.0, 0.0])
        voor = np.array([0, -1.0, 0])
        n_ = uit * math.cos(uitstaan) + voor * math.sin(uitstaan)
        n_ = n_ / np.linalg.norm(n_)
        up = np.array([0, 0.25, 1.0])
        up = up - np.dot(up, n_) * n_
        up /= np.linalg.norm(up)
        sd = np.cross(up, n_)
        rows = []
        prof = [(-1.0, 0.25), (-0.8, 0.62), (-0.45, 0.88), (0.0, 1.0), (0.45, 0.95), (0.8, 0.7), (1.0, 0.3)]
        for v_, w_ in prof:
            row = []
            for j in range(10):
                a_ = 2 * np.pi * j / 10
                x = math.cos(a_) * 0.022 * kk * w_
                y = math.sin(a_) * 0.007 * kk * (0.5 + 0.5 * w_)
                schelp = -0.005 * kk * (1 - math.cos(a_) ** 2) * w_ * (math.sin(a_) > 0)   # holte voor
                q = p + up * (v_ * 0.034 * kk + 0.004 * kk) + sd * x + n_ * (y + 0.012 * kk + schelp)
                row.append(q)
            rows.append(row)
        b0, _ = B.grid(np.array(rows), True, regio=6)
        B.kap(b0, 10, np.mean(rows[0], 0) - up * 0.004 * kk, regio=6)
        B.kap(b0 + 10 * (len(prof) - 1), 10, np.mean(rows[-1], 0) + up * 0.004 * kk, regio=6)


def bouw_tanden(B, sk, kop, tanden, dz=0.002):
    """Tanden (regio 3, vaste kleur) net onder de mondlijn: [(x, breedte, hoogte)] in kopmaten (k)."""
    kk = kop.k
    for x, br, ho in tanden:
        ph = math.atan2(x, 0.09)
        top = kop.punt(kop.theta_bij_z(ph, kop.mond[2] + dz * kk), ph, 0.0)
        nrm = (top - kop.C) / np.linalg.norm(top - kop.C)
        nrm = np.array([nrm[0] * 0.5, nrm[1], 0.0])
        nrm /= np.linalg.norm(nrm)
        sd = np.cross((0, 0, 1.0), nrm)
        sd /= np.linalg.norm(sd)
        pts = []
        for off in (0.003, -0.003):
            for zz in (0.0, -ho):
                for xx in (-br / 2, br / 2):
                    rond = 0.5 if zz < 0 else 1.0
                    pts.append(top + sd * xx * kk * rond ** 0.3 + np.array([0, 0, zz * kk]) + nrm * off * kk)
        b0 = B.verts(pts)
        for f in ((0, 1, 3, 2), (4, 6, 7, 5), (0, 4, 5, 1), (2, 3, 7, 6), (0, 2, 6, 4), (1, 5, 7, 3)):
            B.vlak([b0 + i for i in f], [(0, 0), (br * kk, 0), (br * kk, ho * kk), (0, ho * kk)], regio=3)


def bouw_kuiten(B, sk, van=0.30, tot=0.17, dik=1.0):
    """Blote kuiten (regio 7) tussen rokzoom en laars, langs Leg -> Foot (hoogtes in m bij s = 1)."""
    J = sk.J
    s = sk.s
    for k, sx in (("Left", 1), ("Right", -1)):
        pts = [J[k + "UpLeg"], J[k + "Leg"], J[k + "Foot"]]
        L1 = np.linalg.norm(pts[1] - pts[0])
        L2 = np.linalg.norm(pts[2] - pts[1])
        zk, ze = pts[1][2], pts[2][2]
        dv = L1 + (zk - van * s) / max(zk - ze, 1e-6) * L2
        dt = L1 + (zk - tot * s) / max(zk - ze, 1e-6) * L2
        fr = keten(pts, list(np.linspace(dv, dt, 7)), zacht=0.05)
        rings = []
        for i, (pos, t, f, sd) in enumerate(fr):
            u = i / 6
            r = (0.046 + 0.012 * math.sin(math.pi * min(1, 0.4 + u * 1.2)) - 0.014 * u) * s * dik
            rings.append(ring(pos - f * 0.004 * s, sd, f, r, r * 1.08, 14, 2.0))
        B.grid(np.array(rings), True, regio=7)


def bouw_decollete(B, sk, rijen=None):
    """Nek, blote schouders en bovenborst (regio 5) onder een off-shoulder halslijn (vrouw)."""
    s = sk.s
    Z = sk.z
    rijen = rijen or [(0.845, 0.135, 0.105, 0.115), (0.875, 0.15, 0.108, 0.112), (0.905, 0.165, 0.098, 0.1),
                      (0.93, 0.158, 0.085, 0.09), (0.952, 0.125, 0.075, 0.08), (0.975, 0.082, 0.066, 0.07),
                      (1.0, 0.064, 0.062, 0.062), (1.03, 0.05, 0.05, 0.05), (1.07, 0.048, 0.048, 0.048)]
    rings = []
    th = 2 * np.pi * np.arange(18) / 18
    for z0, a, bv, bb in rijen:
        x = np.sin(th)
        y = -np.cos(th)
        b = np.where(y < 0, bv, bb)
        xs = np.sign(x) * np.abs(x) ** (2 / 2.4)
        rings.append(np.stack([xs * a * s, 0.004 * s + y * b * s, np.full(18, Z(z0))], 1))
    B.grid(np.array(rings), True, regio=5)
    sk.decollete = True


# --- haar: glad (strengen), staartjes, knot, strikken ------------------------------------------------
@hoog("glad", 2)
def hg_glad(h, sk):
    """Strengen: groeven die van de kruin uitwaaieren; staartjes/knot (regio >= 1) groeven in de lengte."""
    P, Nn, reg, J, s, hgt = h.P, h.Nn, h.reg, h.J, h.s, h.hgt
    kop = sk.kop
    kk = kop.k
    st = getattr(sk, "haarstijl", {})
    q = P - (kop.Ch + np.array(st.get("kruin", (0, 0.02, 0.14))) * kk)
    ang = np.arctan2(q[:, 0], -q[:, 1])
    fase = 3.0 * ruis(P, 25, 63)
    gr = 0.5 - np.abs(np.sin(ang * st.get("strengen", 46) / 2 + fase))
    hgt += (0.0022 * kk * gr + 0.0012 * kk * ruis(P, 120, 64)) * (reg == 0)
    hgt += 0.0022 * kk * (0.5 - np.abs(ruis(P, 140, 65))) * (reg >= 1)


@verf("glad")
def vf_glad(cx):
    """Glad haar: streng-strepen met lichte en donkere lokken, scheiding (sk.haarstijl['scheiding'])."""
    P, U, V, z, reg, n, s, sk = cx.P, cx.U, cx.V, cx.z, cx.reg, cx.n, cx.s, cx.sk
    ruw, zet, H = cx.ruw, cx.zet, cx.H
    KLEUR, m = cx.KLEUR, cx.Dm
    kop = sk.kop
    kk = kop.k
    st = getattr(sk, "haarstijl", {})
    q = P - (kop.Ch + np.array(st.get("kruin", (0, 0.02, 0.14))) * kk)
    ang = np.arctan2(q[:, 0], -q[:, 1])
    fase = 3.0 * ruis(P, 25, 63)
    f1 = np.sin(ang * st.get("strengen", 46) + fase)
    f2 = np.sin(ang * 131 + 5 * ruis(P, 60, 66))
    lang = reg >= 1
    f1 = np.where(lang, np.sin(U / (0.004 * kk) + 4 * ruis(P, 40, 67)), f1)
    f2 = np.where(lang, np.sin(U / (0.0013 * kk) + 6 * ruis(P, 90, 68)), f2)
    c = KLEUR[cx.tint][None] * (1 + 0.16 * f1[:, None] + 0.09 * f2[:, None] + 0.08 * cx.r_groot[:, None])
    c *= (1 + np.array(st.get("warm", (0.04, 0.0, -0.06)))[None] * f1[:, None])
    h = 0.0003 * kk * f2
    if st.get("scheiding"):
        sch = (np.abs(P[:, 0]) < 0.0035 * kk) & (P[:, 2] > kop.zz(1.2)) & (reg == 0) & (P[:, 1] > kop.C[1] - 0.08 * kk)
        c[sch] = c[sch] * 0.55 + KLEUR["huid"] * 0.3
        h[sch] -= 0.0008 * kk
    c *= (0.86 + 0.22 * gladstap(kop.zz(1.1), kop.zz(1.3), z))[:, None]    # kruin lichter (zon)
    zet(m, c)
    H[m] = h[m]
    ruw[m] = 0.7


def staart_buis(B, pad, prof, n=12, regio=1, ref=(0, -1, 0), kappen=True):
    """Buis langs een pad (punten) met profiel [(t 0..1, a, b)]; uiteinden dicht."""
    pad = [np.asarray(p, float) for p in pad]
    L = sum(np.linalg.norm(pad[i + 1] - pad[i]) for i in range(len(pad) - 1))
    fr = keten(pad, [t * L for t, _, _ in prof], ref=ref, zacht=0.01)
    rings = [ring(pos, sd, f, a, b, n, 2.0) for (pos, t, f, sd), (_, a, b) in zip(fr, prof)]
    b0, _ = B.grid(np.array(rings), True, regio=regio)
    if kappen:
        B.kap(b0 + n * (len(prof) - 1), n, fr[-1][0] + fr[-1][1] * prof[-1][1] * 0.6, regio=regio)
        B.kap(b0, n, fr[0][0] - fr[0][1] * prof[0][1] * 0.5, regio=regio)
    return fr


def bouw_haar_glad(sk, coll, naam="haar", extra=None, rand=0.004):
    """Glad kapsel: de schil van bouw_haar (klont uit via de kopvorm) + extra(B, sk, kop) (staartjes, knot)."""
    kop = sk.kop
    kk = kop.k
    B = Bouwer()
    nphi = 40
    phs = 2 * np.pi * np.arange(nphi) / nphi
    nrow = 14
    rows = [[] for _ in range(nrow + 3)]
    for ph in phs:
        zb = kop.haargrens(ph) + rand * math.sin(ph * 9 + 1.3) * kk
        tb = kop.theta_bij_z(ph, zb, lambda t, p: kop.haarpunt(t, p, False))
        for i in range(nrow + 1):
            f = i / nrow
            tht = 0.05 + (tb - 0.05) * (1 - (1 - f) ** 1.3)
            rows[i].append(kop.haarpunt(tht, ph))
        rnd = rows[nrow][-1]
        hl = kop.punt(kop.theta_bij_z(ph, zb + 0.006 * kk), ph, 0.002 * kk)
        rows[nrow + 1].append(rnd * 0.5 + hl * 0.5 + np.array([0, 0, 0.004 * kk]))
        rows[nrow + 2].append(hl)
    b0, _ = B.grid(np.array(rows), True, regio=0)
    B.kap(b0, nphi, kop.haarpunt(0, 0), regio=0)
    if extra:
        extra(B, sk, kop)
    return B.obj(naam, coll)


def staartjes(B, sk, kop, lengte=1.0):
    """Twee staartjes aan de zijkant (meisje): naar buiten en omlaag, punten krullen iets naar binnen."""
    kk = kop.k
    sk.staart_aanzet = {}
    for sx in (1, -1):
        p0 = kop.Ch + np.array([sx * 0.108, 0.02, 0.03]) * kk
        L = lengte
        pad = [p0, p0 + np.array([sx * 0.035, 0.0, -0.008]) * kk, p0 + np.array([sx * 0.07, 0.01, -0.06 * L]) * kk,
               p0 + np.array([sx * 0.08, 0.015, -0.13 * L]) * kk, p0 + np.array([sx * 0.062, 0.005, -0.2 * L]) * kk,
               p0 + np.array([sx * 0.035, -0.01, -0.235 * L]) * kk]
        prof = [(0.0, 0.016 * kk, 0.016 * kk), (0.05, 0.02 * kk, 0.02 * kk), (0.2, 0.034 * kk, 0.03 * kk),
                (0.45, 0.04 * kk, 0.033 * kk), (0.7, 0.032 * kk, 0.027 * kk), (0.88, 0.018 * kk, 0.016 * kk),
                (1.0, 0.005 * kk, 0.005 * kk)]
        staart_buis(B, pad, prof, n=12, regio=1)
        sk.staart_aanzet[sx] = (p0 + np.array([sx * 0.016, 0, -0.002]) * kk, pad[1] - p0)


def bouw_strikken(sk, coll, naam="strikken", maat=1.0):
    """Twee strikken op de aanzet van de staartjes: knoop, twee lussen, twee linten (regio 0)."""
    kk = sk.kop.k * maat
    B = Bouwer()
    for sx in (1, -1):
        c, d = sk.staart_aanzet[sx]
        d = d / np.linalg.norm(d)
        up = np.array([0, 0.0, 1.0])
        voor = np.cross(d, up)
        voor /= np.linalg.norm(voor)
        knoop = c + d * 0.004 * kk
        staart_buis(B, [knoop - voor * 0.012 * kk, knoop + voor * 0.012 * kk],
                    [(0, 0.011 * kk, 0.009 * kk), (0.5, 0.014 * kk, 0.012 * kk), (1, 0.011 * kk, 0.009 * kk)],
                    n=10, regio=0, ref=tuple(d))
        for kant in (1, -1):                                       # lussen: platte buis langs een boog
            pad = []
            for t_ in np.linspace(0, 1, 9):
                a_ = math.pi * t_
                pad.append(knoop + voor * kant * (0.008 + 0.042 * math.sin(a_ * 0.5 + 0.2)) * kk * (0.4 + 0.6 * math.sin(a_))
                           + up * (0.03 * math.sin(a_) - 0.004) * kk + d * 0.004 * kk * math.sin(a_))
            staart_buis(B, pad, [(t, 0.006 * kk, 0.013 * kk * (0.6 + 0.6 * math.sin(math.pi * t)))
                                 for t in np.linspace(0, 1, 9)], n=8, regio=0, ref=tuple(d))
            pad = [knoop, knoop + voor * kant * 0.012 * kk - up * 0.022 * kk,
                   knoop + voor * kant * 0.02 * kk - up * 0.048 * kk]
            staart_buis(B, pad, [(0, 0.004 * kk, 0.009 * kk), (0.5, 0.003 * kk, 0.01 * kk), (1, 0.002 * kk, 0.012 * kk)],
                        n=6, regio=0, ref=tuple(d))
    return B.obj(naam, coll)


@verf("strik")
def vf_strik(cx):
    """Satijnen lint: glansbanen langs het lint."""
    ruw, zet, H, KLEUR, m = cx.ruw, cx.zet, cx.H, cx.KLEUR, cx.Dm
    c = KLEUR[cx.tint][None] * (1 + 0.1 * cx.r_groot[:, None] + 0.12 * np.sin(cx.V / 0.004)[:, None])
    zet(m, c)
    H[m] = (0.0002 * np.sin(cx.V / 0.002))[m]
    ruw[m] = 0.4


GEWICHT["strik"] = GEWICHT["kop"]
GEWICHT["glad"] = GEWICHT["kop"]


def knot(B, sk, kop, plek=(0, 0.115, 0.095), r=(0.052, 0.045, 0.05)):
    """Knot achter op het hoofd (oudere vrouw): afgeplatte bol (regio 2), as naar achteren."""
    kk = kop.k
    c = kop.C + np.array(plek) * kk
    nth, nph = 10, 18
    rows = []
    for i in range(1, nth):
        th = math.pi * i / nth
        row = []
        for j in range(nph):
            ph = 2 * math.pi * j / nph
            d = np.array([math.sin(th) * math.cos(ph), math.sin(th) * math.sin(ph), math.cos(th)])
            row.append(c + np.array([d[0] * r[0], d[2] * r[1], d[1] * r[2]]) * kk)
        rows.append(row)
    b0, _ = B.grid(np.array(rows), True, regio=2)
    B.kap(b0, nph, c + np.array([0, r[1], 0]) * kk, regio=2)
    B.kap(b0 + nph * (nth - 2), nph, c - np.array([0, r[1], 0]) * kk, regio=2)


# --- kragen ----------------------------------------------------------------------------------------
def bouw_kraag(sk, coll, naam="kraag", z0=None, r_in=0.062, r_uit=0.105, zak=0.03, plooien=22, plooi=0.012,
               schulp=0.0, hoog_=0.012, n=None, bv=0.95):
    """Kraag om de hals: plooikraag (plooi > 0, zigzag op en neer) of platte schulpkraag (schulp > 0).
    Dubbel vel met een gesloten buitenrand (regio 0)."""
    s = sk.s
    zc = (sk.nz + 0.012 * s) if z0 is None else z0
    n = n or plooien * 4
    th = 2 * np.pi * np.arange(n) / n
    zz = np.sin(th * plooien) * plooi * s
    ro = (r_uit - schulp * np.abs(np.cos(th * plooien / 2)) ** 3) * s
    ri = r_in * s
    sk.kraag_plooien = plooien

    def rij(r, dz, f=1.0):
        return np.stack([np.sin(th) * r, 0.004 * s - np.cos(th) * r * bv, zc + dz + zz * f], 1)
    rows = [rij(ri, hoog_ * s, 0.3), rij(ri + (ro - ri) * 0.5, (hoog_ * 0.4 - zak * 0.4) * s, 0.8),
            rij(ro, -zak * s, 1.0), rij(ro - 0.003 * s, -zak * s - 0.005 * s, 1.0),
            rij(ri + (ro - ri) * 0.5, (hoog_ * 0.4 - zak * 0.4 - 0.006) * s, 0.8), rij(ri - 0.002 * s, 0.0, 0.3)]
    B = Bouwer()
    B.grid(np.array(rows), True, regio=0)
    return B.obj(naam, coll)


@verf("kraag")
def vf_kraag(cx):
    P, n, sk = cx.P, cx.n, cx.sk
    ruw, zet, H, KLEUR, m = cx.ruw, cx.zet, cx.H, cx.KLEUR, cx.Dm
    phi = np.arctan2(P[:, 0], -P[:, 1])
    pl = getattr(sk, "kraag_plooien", 22)
    c = KLEUR[cx.tint][None] * (1 + 0.06 * cx.r_groot[:, None] + 0.1 * np.cos(phi * pl)[:, None])
    zet(m, c)
    H[m] = (0.0002 * np.sin(cx.U / 0.002))[m]
    ruw[m] = 0.85


@gewicht("kraag")
def gw_kraag(g):
    P, J, s = g.P, g.J, g.s
    t = gladstap(J["Neck"][2] - 0.01 * s, J["Neck"][2] + 0.03 * s, P[:, 2])
    g.voeg("Spine2", 1 - t)
    g.voeg("Neck", t)


@hoog("kraag", 2, True)
def hg_kraag(h, sk):
    pass


# --- staf (oudere man en vrouw) -----------------------------------------------------------------
def bouw_staf(sk, coll, naam="prop_staf", lengte=1.45, ranken=2, bladeren=14, krul=True, seed=3, dik=1.0):
    """Knoestige houten staf met ranken en blaadjes (regio 0 hout, 1 rank, 2 blad), gebouwd rechtop met de
    onderkant op z = 0. Na de animaties zet plaats_staf hem star in de linkerhand (kind van bot prop_L, geen
    skin, zie Personage.extra['prop_delen']): verticaal en op de grond in idle frame 0."""
    s = sk.s
    rng = np.random.default_rng(seed)
    # vaste stand: verticaal, onderkant op z = 0 (plaats_staf zet hem later in de hand)
    u = np.array([0, 0, -1.0])
    f = np.array([0, -1.0, 0])
    binnen = np.array([1.0, 0, 0])
    onder = 0.55 * s
    boven = lengte * s - onder
    c = np.array([0, 0, onder])
    N = 24
    pad = []
    for d in np.linspace(-boven, onder, N):
        kr = 0.008 * s * math.sin(d / (0.21 * s) * 2 * math.pi + 1.0) + 0.004 * s * math.sin(d / (0.09 * s) + 2)
        pad.append(c + u * d + f * kr + binnen * 0.006 * s * math.sin(d / (0.33 * s) * 2 * math.pi))
    if krul:                                                       # gekrulde kop
        top = pad[0]
        for j in range(1, 6):
            a_ = j / 5 * 2.4
            pad.insert(0, top - u * 0.035 * s * math.sin(a_) + f * 0.04 * s * (1 - math.cos(a_)))
    pad = np.array(pad)
    B = Bouwer()
    L = np.sum(np.linalg.norm(np.diff(pad, axis=0), axis=1))
    nprof = len(pad)
    prof = []
    for i in range(nprof):
        t = i / (nprof - 1)
        r = (0.016 - 0.003 * t) * s * dik * (1 + 0.16 * math.sin(t * 37) * math.sin(t * 13))
        if t < 0.15:
            r *= 0.7 + 0.3 * t / 0.15
        prof.append((t, r, r * 0.92))
    fr = keten(list(pad), [t * L for t, _, _ in prof], ref=tuple(f), zacht=0.02)
    rings = [ring(pos, s_, f_, a, b, 10, 2.0) for (pos, t_, f_, s_), (_, a, b) in zip(fr, prof)]
    b0, _ = B.grid(np.array(rings), True, regio=0)
    B.kap(b0, 10, fr[0][0] - fr[0][1] * 0.01 * s, regio=0)
    B.kap(b0 + 10 * (nprof - 1), 10, fr[-1][0] + fr[-1][1] * 0.006 * s, regio=0)
    sk.staf_as = (c, u, f, binnen, boven, onder)
    for r_ in range(ranken):                                       # ranken: spiralen om de staf
        fase = r_ * math.pi + 0.4
        wind = 5.5 + r_ * 1.3
        n = 64
        tt = np.linspace(0.02, 0.95 - 0.25 * r_, n)
        rp = []
        for t_ in tt:
            i = min(int(t_ * (nprof - 1)), nprof - 2)
            pos, tg, ff, ss = fr[i]
            a_ = fase + t_ * wind * 2 * math.pi
            rad = prof[i][1] + 0.0035 * s
            rp.append(pos + (ff * math.cos(a_) + ss * math.sin(a_)) * rad)
        rprof = [(t, 0.0055 * s * (1 - 0.5 * t), 0.0055 * s * (1 - 0.5 * t)) for t in np.linspace(0, 1, n)]
        staart_buis(B, rp, rprof, n=5, regio=1, ref=tuple(u))
        for _ in range(bladeren // ranken):                        # blaadjes langs de rank
            j = int(rng.uniform(3, n - 3))
            p = rp[j]
            tg = rp[j + 1] - rp[j - 1]
            tg /= np.linalg.norm(tg)
            uit = p - fr[min(int(tt[j] * (nprof - 1)), nprof - 1)][0]
            uit /= np.linalg.norm(uit) + 1e-9
            dirb = uit * 0.8 + tg * 0.4 + rng.normal(size=3) * 0.2
            dirb /= np.linalg.norm(dirb)
            vl = np.cross(dirb, tg)
            vl /= np.linalg.norm(vl) + 1e-9
            ln = rng.uniform(0.026, 0.04) * s
            bw = ln * 0.4
            nv = np.cross(dirb, vl)
            pts = [p, p + dirb * ln * 0.35 + vl * bw, p + dirb * ln, p + dirb * ln * 0.35 - vl * bw,
                   p + dirb * ln * 0.45 + nv * 0.003 * s]
            b1 = B.verts(pts)
            for a_, b_ in ((0, 1), (1, 2), (2, 3), (3, 0)):
                B.vlak([b1 + a_, b1 + b_, b1 + 4], [(0, 0), (bw, ln * 0.35), (0, ln * 0.45)], regio=2)
                B.vlak([b1 + b_, b1 + a_, b1 + 4], [(0, 0), (bw, ln * 0.35), (0, ln * 0.45)], regio=2)
    return B.obj(naam, coll)


@verf("staf")
def vf_staf(cx):
    """Hout met nerf en knoesten (0), donkere rank (1), groene blaadjes met nerf (2). Vaste kleuren."""
    P, U, V, reg, n = cx.P, cx.U, cx.V, cx.reg, cx.n
    ruw, zet, H, KLEUR, m = cx.ruw, cx.zet, cx.H, cx.KLEUR, cx.Dm
    nerf = ruis(np.stack([U * 40, V * 3, np.zeros(n)], 1), 1, 71, 3)
    kn = ruis(P, 22, 72)
    c = KLEUR["hout"][None] * (1 + 0.35 * nerf[:, None] + 0.25 * np.clip(kn, 0, 1)[:, None] - 0.1 * cx.r_fijn[:, None])
    h = 0.0006 * nerf - 0.0008 * np.clip(kn - 0.4, 0, 1)
    rank = reg == 1
    c[rank] = KLEUR["rank"] * (1 + 0.2 * cx.r_fijn[rank, None])
    blad = reg == 2
    c[blad] = KLEUR["blad"] * (1 + 0.25 * cx.r_groot[blad, None] + 0.15 * np.sin(U[blad] / 0.002)[:, None])
    zet(m, c)
    H[m] = h[m]
    ruw[m] = np.where(reg == 0, 0.8, np.where(blad, 0.55, 0.7))[m]


@hoog("staf", 1, True)
def hg_staf(h, sk):
    P, reg, s, hgt = h.P, h.reg, h.s, h.hgt
    hgt += 0.0012 * s * ruis(P * np.array([1, 1, 0.2]), 90, 73) * (reg == 0)


def bouw_mouwen(sk, coll, naam="mouwen", dik=1.0, wijd=1.0, start=0.0, pof=0.0, manchet=4):
    """Alleen mouwen (soort 'kledij', regio 1 + manchet 4): blouse-mouwen onder een off-shoulder jurk.
    start: mouw begint pas op deze afstand langs de as (0 = in de romp; L0 = bij het schoudergewricht);
    pof: extra wijdte vlak na de start (pofmouw)."""
    s = sk.s
    B = Bouwer()
    sk.mouwen = getattr(sk, "mouwen", {})
    sk.mouwen[naam] = {}
    for k in ("Left", "Right"):
        pts = mouw_punten(sk, k)
        sk.mouwen[naam][k] = pts
        L0 = np.linalg.norm(pts[1] - pts[0])
        L1 = np.linalg.norm(pts[2] - pts[1])
        L2 = np.linalg.norm(pts[3] - pts[2])
        e, w = L0 + L1, L0 + L1 + L2
        mp = [q for q in mouw_profiel(L0, e, w, dik, wijd) if q[0] >= start * L0 - 1e-9]
        if pof:
            mp = [(d, a * (1 + pof * gauss((d - start * L0 - 0.05) / 0.05, 1.0)),
                   b * (1 + pof * gauss((d - start * L0 - 0.05) / 0.05, 1.0))) for d, a, b in mp]
        fr = keten(pts, [q[0] for q in mp], zacht=0.05)
        rings = [ring(pos, sd, f, a * s, b * s, 16, 2.1) for (pos, tt, f, sd), (_, a, b) in zip(fr, mp)]
        B.grid(np.array(rings[:-manchet + 1]), True, regio=1)
        B.grid(np.array(rings[-manchet:]), True, regio=4)
    sk.kledij_z = getattr(sk, "kledij_z", {})
    sk.kledij_z[naam] = (-1.0, -1.0)
    return B.obj(naam, coll)


def plaats_staf(rig, obj, actie="idle", frame=0, binnen=0.012, voor=0.0):
    """Verplaatst de (rechtop gebouwde) staf star zodat hij in `actie`/`frame` verticaal door de linkerhand
    staat met de onderkant op de grond, en zet de vertices terug in de rustruimte van bot prop_L.
    Een starre verplaatsing: UV en textuur blijven gelijk."""
    import bpy
    from mathutils import Matrix, Vector
    act = bpy.data.actions[actie]
    ad = rig.animation_data_create()
    ad.action = act
    if getattr(ad, "action_slot", None) is None and len(getattr(act, "slots", [])):
        ad.action_slot = act.slots[0]
    bpy.context.scene.frame_set(frame)
    bpy.context.view_layer.update()
    Mp = rig.pose.bones["prop_L"].matrix.copy()
    Mr = rig.data.bones["prop_L"].matrix_local.copy()
    palm = Mp.translation
    s = rig["hoogte"] / 1.37
    doel = Matrix.Translation(Vector((palm.x - binnen * s, palm.y - voor * s, 0.0)))
    T = Mr @ Mp.inverted() @ doel
    me = obj.data
    for v in me.vertices:
        v.co = T @ v.co
    me.update()
    ad.action = None
    for b in rig.pose.bones:
        b.rotation_quaternion = (1, 0, 0, 0)
        b.location = (0, 0, 0)
    bpy.context.scene.frame_set(0)
    bpy.context.view_layer.update()
