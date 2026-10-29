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

from bumpkin_basis import (GEWICHT, HOOG, LAAG, VERF, Bouwer, Kop, gauss, gladstap, keten, keten_param, overgang,  # noqa: F401
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


def bouw_tuinbroek(sk, coll, naam="tuinbroek", dik=1.0):
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
            dk = 1 + (dik - 1) * np.clip((d + 0.03) / 0.08, 0, 1)                # smaller vanaf het kruis
            rings.append(ring(pos + inw, sd, f, a * s * dk, b * s * dk, 16, 2.2))
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
    sk.riem_z = zb
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
    n = 16
    th = 2 * np.pi * np.arange(n) / n
    for k, sx in (("Left", 1), ("Right", -1)):
        an = v(k + "Foot")
        rot = math.radians(8) * sx
        cr, sr = math.cos(rot), math.sin(rot)
        cy, cx = np.sin(th), np.cos(th)
        pe = 2.6
        x = np.sign(cx) * np.abs(cx) ** (2 / pe)
        y = np.sign(cy) * np.abs(cy) ** (2 / pe)
        W = 0.052 * (0.92 + 0.16 * np.clip(y, 0, 1))
        fy = np.where(y > 0, 0.148, 0.07) * y                     # lokaal +y = vooruit
        voet = np.stack([x * W, fy], 1) * s
        cirkel = np.stack([cx * 0.056, cy * 0.057 - 0.004], 1) * s
        # slanke schacht, smalle omslag (geen uitwaaierende trechter)
        prof = [(0.0, 0.0, 1.0), (0.013, 0.0, 1.035), (0.024, 0.0, 0.99), (0.05, 0.12, 0.97), (0.078, 0.42, 0.98),
                (0.105, 0.8, 0.97), (0.135, 1.0, 0.98), (0.165, 1.0, 1.0), (0.198, 1.0, 1.02),
                (0.204, 1.0, 1.05), (0.211, 1.0, 1.09), (0.208, 1.0, 1.13), (0.196, 1.0, 1.14), (0.186, 1.0, 1.1),
                (0.18, 1.0, 1.02)]
        rings = []
        for z, bl, sc in prof:
            q = (voet * (1 - bl) + cirkel * bl) * sc
            gx, gy = q[:, 0] * cr + q[:, 1] * sr, q[:, 0] * sr - q[:, 1] * cr
            rings.append(np.stack([an[0] + gx, an[1] + gy, np.full(n, z * s)], 1))
        b0, _ = B.grid(np.array(rings[:10]), True, regio=0)
        B.grid(np.array(rings[9:]), True, regio=0)                 # omslag: eigen vel, buitenkant naar buiten
        B.kap(b0, n, (an[0] + sr * 0.049 * s, an[1] - cr * 0.049 * s, 0.0), regio=1, buiten=(0, 0, -1))
    return B.obj(naam, coll)


def draai(v, as_, hoek):
    """Rodrigues: v om eenheidsas as_ over hoek (rad)."""
    v, as_ = np.asarray(v, float), np.asarray(as_, float)
    c, s_ = math.cos(hoek), math.sin(hoek)
    return v * c + np.cross(as_, v) * s_ + as_ * np.dot(as_, v) * (1 - c)


def vinger_buis(B, pad, radii, n=6, regio=2, ref=(0, -1, 0)):
    """Buis langs de punten van pad met een straal per punt; de punt wordt een kapje."""
    pad = [np.asarray(p, float) for p in pad]
    afst = np.concatenate([[0], np.cumsum([np.linalg.norm(pad[i + 1] - pad[i]) for i in range(len(pad) - 1)])])
    fr = keten(pad, list(afst), ref=ref, zacht=0.004)
    rings = [ring(pos, sd, f, r, r * 0.92, n, 2.1) for (pos, t, f, sd), r in zip(fr, radii)]
    b0, _ = B.grid(np.array(rings), True, regio=regio)
    B.kap(b0 + n * (len(pad) - 1), n, fr[-1][0] + fr[-1][1] * radii[-1] * 0.85, regio=regio)
    return fr


# (b over de breedte, a-knokkel, lengtes kootjes, straal basis, spreiding graden) bij een volwassen hand
VINGERS = [(0.025, 0.067, (0.025, 0.016, 0.014), 0.0097, 8), (0.0085, 0.07, (0.028, 0.018, 0.015), 0.01, 2),
           (-0.0085, 0.068, (0.026, 0.017, 0.014), 0.0094, -4), (-0.0245, 0.062, (0.02, 0.013, 0.012), 0.0084, -11)]


def bouw_handen(B, sk):
    """Handen: handpalm, vier vingers en een duim (regio 2; duim regio 4), in een losse greep zodat een steel
    door de socket prop_R/prop_L (op de botas, midden van de hand) tussen palm en vingers loopt: de palm ligt
    daarvoor iets naar buiten van de botas. Alles volgt het bot Hand (HandFist zou de vingers in het vlak van
    de palm laten zwaaien). sk.handmaat schaalt (standaard 1), sk.kromming de greep (standaard 1)."""
    J = sk.J
    s = sk.s
    hs = s * getattr(sk, "handmaat", 1.2)
    kr = getattr(sk, "kromming", 1.35)
    sk.knokkels, sk.nagels = {}, {}
    for k, sx in (("Left", 1), ("Right", -1)):
        pts = [J[k + "ForeArm"], J[k + "Hand"], J[k + "HandEnd"]]
        L1 = np.linalg.norm(pts[1] - pts[0])
        pos0, t, f, sd = keten(pts, [L1])[0]
        bin_ = -np.sign(np.dot(sd, (sx, 0, 0)) + 1e-9) * sd       # palmkant (naar het lichaam)
        pols = pts[1]

        def H(a, b, c):
            return pols + t * a * hs + f * b * hs + bin_ * c * hs
        off = -0.010                                               # palm naar buiten: ruimte voor de steel
        prof = [(-0.03, 0.017, 0.025, 0.0), (-0.004, 0.0155, 0.024, 0.0), (0.012, 0.0145, 0.029, 0.55),
                (0.03, 0.0135, 0.033, 0.9), (0.05, 0.0125, 0.035, 1.0), (0.066, 0.0115, 0.035, 1.0),
                (0.074, 0.008, 0.03, 1.0)]
        rings = []
        for a, dc, bw, fo in prof:
            c0 = off * fo
            th_ = 2 * np.pi * np.arange(10) / 10
            cs, sn = np.cos(th_), np.sin(th_)
            ring_ = []
            for c_, s_ in zip(cs, sn):
                x = np.sign(c_) * abs(c_) ** (2 / 2.4)
                y = np.sign(s_) * abs(s_) ** (2 / 2.4)
                duimbal = 0.006 * max(0.0, y) * max(0.0, x) * (1 if 0.0 < a < 0.045 else 0)   # muis van de duim
                ring_.append(H(a, y * bw + duimbal * 0.5, c0 + x * dc + duimbal))
            rings.append(ring_)
        b0, _ = B.grid(np.array(rings), True, regio=2)
        B.kap(b0 + 10 * (len(prof) - 1), 10, H(0.077, 0.0, off * 0.9), regio=2)
        sk.knokkels[k], sk.nagels[k] = [], []
        for bpos, ak, lens, r0, spr in VINGERS:
            basis = H(ak - 0.012, bpos, off)
            d = draai(t, bin_, math.radians(spr) * (1 if np.dot(np.cross(bin_, t), f) > 0 else -1))
            buig_as = np.cross(d, bin_)
            buig_as /= np.linalg.norm(buig_as)
            pad, radii = [basis, basis + d * 0.012 * hs], [r0 * hs * 1.05, r0 * hs * 1.05]
            sk.knokkels[k].append(H(ak, bpos, off - 0.011))
            p_ = pad[-1]
            for i, (L, hoek) in enumerate(zip(lens, (26, 38, 24))):
                d = draai(d, buig_as, math.radians(hoek * kr))
                rt = r0 * (1 - 0.1 * (i + 1))
                if i == 0:
                    pad.append(p_ + d * L * hs * 0.5)
                    radii.append(rt * hs)
                p_ = p_ + d * L * hs
                pad.append(p_ - d * 0.003 * hs if i == 2 else p_)
                radii.append(rt * hs * (0.86 if i == 2 else 0.97))
            vinger_buis(B, pad, radii, 5, regio=2, ref=tuple(bin_))
            sk.nagels[k].append((p_, d, -np.cross(buig_as, d)))
        # duim: van de muis naar voren en de palmkant op, krult naar de wijsvinger
        basis = H(0.014, 0.022, off + 0.006)
        d = t * 0.45 + f * 0.62 + bin_ * 0.64
        d /= np.linalg.norm(d)
        pad, radii, p_ = [basis], [0.0125 * hs], basis
        for L, hoek, r in ((0.03, 0.0, 0.0115), (0.022, 22, 0.0095), (0.019, 28, 0.0082)):
            buig_as = np.cross(d, t)
            buig_as /= np.linalg.norm(buig_as) + 1e-9
            d = draai(d, buig_as, math.radians(hoek * kr))
            if L > 0.025:
                pad.append(p_ + d * L * hs * 0.5)
                radii.append(r * hs)
            p_ = p_ + d * L * hs
            pad.append(p_)
            radii.append(r * hs * 0.92)
        pad[-1] = pad[-1] - d * 0.003 * hs
        vinger_buis(B, pad, radii, 5, regio=4, ref=tuple(bin_))
        sk.nagels[k].append((p_, d, -bin_))


# --- Gezicht: gebeeldhouwde vorm op de schedel ----------------------------------------------------
# Alle maten in kopmaten (k = 1, metres bij de volwassen kop), positief = naar buiten. Per personage te
# overschrijven met gezicht['vorm']; een (links, rechts)-paar geeft asymmetrie (links = +X).
VORM = dict(
    richel=0.0045, brauw_z=0.016, brauw_binnen=0.0, brauw_buiten=0.0,          # wenkbrauwrichel
    oogkas=0.006, oog_diep=0.0065, oog_voor=-0.0016, lid_dik=0.0019, lidplooi=0.0011, lidkap=0.0,
    oog_kantel=0.0, oog_dz=0.0, lid_hang=0.0, wal=0.0009,                      # ogen en leden
    jukbeen=0.0045, wang_hol=0.0, wang_vol=0.0, kaakhoek=0.003, slaap=0.0015, voorhoofd=0.002,
    neus_h=0.022, neus_tip=-0.012, neus_r=0.0105, neus_brug=0.0035, neus_brug_b=0.0062, neus_bult=0.0,
    neus_breed=0.0135, neus_vleugel=0.0095, neus_x=0.0, neus_hang=0.0,          # neus
    lip_b=0.0032, lip_o=0.0038, spleet_d=0.0016, snuit=0.0042, mond_scheef=0.0, mond_in=0.0, mond_z=0.0,
    kin=0.0065, kin_z=0.036, kin_breed=0.017, nlf=0.0015, rimpels=0.0, asym=0.0007, seed=1,
    kaak_voor=0.011,                    # onderste gezichtshelft naar voren: mond en kin staan rechtop
    brauw_bult=0.0012,                  # wenkbrauwhaar als lichte bult op de richel
    lip_rand=0.0007,                    # scherpe lippenrand (vermiljoenrand)
)


def vorm_par(kop):
    v = dict(VORM)
    v.update(kop.gezicht.get("vorm", {}))
    return v


def zijwaarde(v, sleutel, sx):
    x = v[sleutel]
    return x[0 if sx > 0 else 1] if isinstance(x, (tuple, list)) else x


def oog_frames(kop):
    """Per oog (sx, midden e, voor-as gd, boven up, buiten out) in kopmaten t.o.v. kop.C."""
    uit = []
    for o in kop.ogen:
        e = (o - kop.C) / kop.k
        sx = 1.0 if e[0] > 0 else -1.0
        gd = e / np.linalg.norm(e) * 0.55 + np.array([0, -1.0, 0]) * 0.45
        gd /= np.linalg.norm(gd)
        up = np.array([0, 0, 1.0]) - gd[2] * gd
        up /= np.linalg.norm(up)
        out = np.cross(up, gd)
        if out[0] * sx < 0:
            out = -out
        uit.append((sx, e, gd, up, out))
    return uit


def oog_lijnen(kop, v, fr, Q):
    """Oogkaart: ex (naar buiten), ez (omhoog), nz (voor) t.o.v. het oogmidden, en de lidranden zu/zl."""
    sx, e, gd, up, out = fr
    rel = Q - e
    ex, ez, nz = rel @ out, rel @ up - zijwaarde(v, "oog_dz", sx), rel @ gd
    w, top, bot = kop.oog
    top = top - zijwaarde(v, "lid_hang", sx)
    u = ex / w
    env = np.clip(1 - u * u, 0, 1)
    kant = zijwaarde(v, "oog_kantel", sx) * ex
    zu = top * env ** 0.5 + kant - 0.0005 * (1 - env)
    zl = -bot * env ** 0.65 + kant * 0.6
    return ex, ez, nz, zu, zl, u


def gezicht_vorm(kop):
    """Gezichtsvorm als functie f(P) -> verschuiving (m). Wenkbrauwrichel, oogkassen met oogleden over een
    oogbol, jukbeenderen, wangen, neus met brug/punt/vleugels/neusgaten, lippen en mondspleet, kin, kaakhoek,
    neus-mondplooi, rimpels (hoog-poly) en wat lage ruis voor asymmetrie."""
    g = kop.gezicht
    v = vorm_par(kop)
    k = kop.k
    C = kop.C
    E = [(o - C) / k for o in kop.ogen]
    M = (kop.mond - C) / k
    Nc = (kop.neus - C) / k
    mb = g.get("mondbreed", 0.021)
    lach = g.get("lach", 0.006)
    op = g.get("open", 0.0)
    frames = oog_frames(kop)
    kop.oogframes = frames
    kop.vorm_v = v
    ez0 = E[0][2]
    Zt0 = Nc[2] + v["neus_tip"]
    hn, rn, nb = v["neus_h"], v["neus_r"], v["neus_breed"]

    def neusvorm(X, Z):
        Zb = ez0 + 0.006
        Zt = Zt0 - v["neus_hang"]
        t = np.clip((Zb - Z) / (Zb - Zt), 0, 1)
        brug = v["neus_brug"] + (hn * 0.72 - v["neus_brug"]) * t ** 1.6 + v["neus_bult"] * np.sin(np.pi * np.clip(t * 1.2, 0, 1))
        wb = v["neus_brug_b"] + 0.0055 * t
        brug = brug * np.exp(-(X / wb) ** 2) * gladstap(Zt - 0.006, Zt + 0.002, Z) * gladstap(Zb + 0.01, Zb - 0.002, Z)
        dzt = Z - Zt
        tip = hn * np.exp(-(X / (rn * 1.05)) ** 2 - (dzt / np.where(dzt > 0, rn * 1.3, rn * 0.62)) ** 2)
        n = np.maximum(brug, tip)
        cz = Zt - 0.0035
        for s_ in (1, -1):
            dz_ = Z - cz
            ala = v["neus_vleugel"] * np.exp(-((X - s_ * nb) / 0.0068) ** 2 - (dz_ / np.where(dz_ > 0, 0.0078, 0.0052)) ** 2)
            n = np.maximum(n, ala)
        return n, Zt

    def f(P):
        Q = (np.asarray(P, float) - C) / k
        X, Y, Z = Q[:, 0], Q[:, 1], Q[:, 2]
        fm = gladstap(-0.005, -0.05, Y)
        h = np.zeros(len(Q))
        hz = np.zeros(len(Q))                                                       # zijkant: niet maskeren
        # voorhoofd, slapen, wenkbrauwrichel
        h += v["voorhoofd"] * np.exp(-(X / 0.045) ** 2 - ((Z - ez0 - 0.055) / 0.03) ** 2)
        h += v["richel"] * 0.7 * np.exp(-(X / 0.009) ** 2 - ((Z - ez0 - 0.012) / 0.008) ** 2)
        for sx, e, gd, up, out in frames:
            zb = e[2] + v["brauw_z"]
            r_ = zijwaarde(v, "richel", sx)
            h += r_ * np.exp(-((X - (e[0] - sx * 0.006)) / 0.012) ** 2 - ((Z - zb - zijwaarde(v, "brauw_binnen", sx)) / 0.0065) ** 2)
            h += r_ * np.exp(-((X - (e[0] + sx * 0.013)) / 0.014) ** 2 - ((Z - zb - zijwaarde(v, "brauw_buiten", sx) + 0.001) / 0.0065) ** 2)
            tb_ = np.clip((X - e[0]) * sx / 0.022, -0.6, 1.2)                         # wenkbrauwhaar
            zbr = e[2] + kop.gezicht.get("brauw", (0.0205, 0.006, 0.0034))[0] + 0.003 * (1 - tb_) - \
                kop.gezicht.get("brauw", (0.0205, 0.006, 0.0034))[1] * tb_ * tb_
            h += zijwaarde(v, "brauw_bult", sx) * gauss(Z - zbr, 0.0028) * gladstap(-0.7, -0.5, tb_) * gladstap(1.25, 1.05, tb_)
            h -= v["slaap"] * np.exp(-((X - sx * 0.082) / 0.016) ** 2 - ((Z - ez0 - 0.028) / 0.02) ** 2)
            # jukbeen (naar het oor), holle of volle wang
            h += zijwaarde(v, "jukbeen", sx) * (np.exp(-((X - (e[0] + sx * 0.02)) / 0.018) ** 2 - ((Z - e[2] + 0.025) / 0.0095) ** 2) +
                                             0.8 * np.exp(-((X - (e[0] + sx * 0.042)) / 0.016) ** 2 - ((Z - e[2] + 0.019) / 0.01) ** 2))
            h -= zijwaarde(v, "wang_hol", sx) * np.exp(-((X - sx * 0.05) / 0.017) ** 2 - ((Z - M[2] - 0.014) / 0.017) ** 2)
            h += v["wang_vol"] * np.exp(-((X - sx * 0.042) / 0.02) ** 2 - ((Z - M[2] - 0.012) / 0.018) ** 2)
            # oogkas en wallen
            h -= v["oogkas"] * np.exp(-((X - e[0] - sx * 0.002) / 0.021) ** 2 - ((Z - e[2] + 0.002) / 0.016) ** 2)
            h += zijwaarde(v, "wal", sx) * np.exp(-((X - e[0] - sx * 0.002) / 0.011) ** 2 -
                                               ((Z - e[2] + kop.oog[2] + 0.0062) / 0.0034) ** 2)
            h -= zijwaarde(v, "wal", sx) * 0.7 * np.exp(-((X - e[0]) / 0.012) ** 2 - ((Z - e[2] + kop.oog[2] + 0.0115) / 0.0022) ** 2)
            # kaakhoek (3D, ook opzij)
            kh = np.array([sx * 0.074, 0.0, M[2] - 0.022])
            hz += zijwaarde(v, "kaakhoek", sx) * np.exp(-np.sum(((Q - kh) / np.array([0.018, 0.03, 0.02])) ** 2, 1))
        # neus
        Xn = X - v["neus_x"]
        n, Zt = neusvorm(Xn, Z)
        h += n
        cz = Zt - 0.0035
        for s_ in (1, -1):
            dd = np.hypot((Xn - s_ * nb) / 0.0068, (Z - cz) / 0.0078)
            h -= 0.0016 * gauss(dd - 1.12, 0.16) * (Z > cz - 0.004)                  # vleugelgroef
            h -= 0.0045 * np.exp(-((Xn - s_ * 0.0062) / 0.0032) ** 2 - ((Z - (Zt - 0.0105)) / 0.0024) ** 2)   # neusgat
        # mond
        Xm = X
        Zs = M[2] + v["mond_z"] + lach * (Xm / mb) ** 2 + v["mond_scheef"] * (Xm / mb)
        dz = Z - Zs
        env = np.clip(1 - (Xm / (mb * 1.05)) ** 2, 0, 1) ** 0.6
        envb = np.clip(1 - (Xm / (mb * 1.12)) ** 2, 0, 1) ** 0.5
        vorm_open = op * np.clip(1 - (Xm / mb) ** 2, 0, 1) ** 0.5
        h += v["snuit"] * np.exp(-(Xm / 0.03) ** 2 - ((Z - M[2] - 0.002) / 0.024) ** 2)
        h += v["kaak_voor"] * np.exp(-(Xm / 0.05) ** 2) * gladstap(ez0 - 0.02, M[2] + 0.01, Z) * \
            gladstap(M[2] - v["kin_z"] - 0.03, M[2] - v["kin_z"] + 0.004, Z)
        h -= v["mond_in"] * np.exp(-(Xm / 0.026) ** 2 - ((Z - M[2] + 0.002) / 0.016) ** 2)
        h += v["lip_b"] * gauss(dz - 0.0034, 0.0032) * env
        h += v["lip_rand"] * gauss(dz - 0.0068, 0.0009) * env                         # rand bovenlip
        h += v["lip_o"] * gauss(dz + vorm_open + 0.0042, 0.0038) * env
        h -= v["spleet_d"] * gauss(dz, 0.0011) * envb
        if op:
            holte = gladstap(0.0, 0.0008, -dz) * gladstap(0.0, 0.0008, dz + vorm_open) * gladstap(0.0, 0.2, vorm_open / op)
            h -= 0.009 * holte
        for s_ in (1, -1):
            zc = M[2] + v["mond_z"] + lach + v["mond_scheef"] * s_
            h -= 0.0008 * np.exp(-((Xm - s_ * mb * 1.04) / 0.003) ** 2 - ((Z - zc) / 0.0032) ** 2)
        Zn = Zt - 0.012                                                              # neusonderkant
        Zs0 = M[2] + v["mond_z"]
        gootje = gladstap(Zs0 + 0.004, Zs0 + 0.007, Z) * gladstap(Zn + 0.001, Zn - 0.002, Z)
        h += 0.0007 * gootje * (np.exp(-((Xm - 0.0045) / 0.0022) ** 2) + np.exp(-((Xm + 0.0045) / 0.0022) ** 2))
        h -= 0.0008 * gauss(dz + vorm_open + 0.0125, 0.0028) * env                 # groef boven de kin
        h += v["kin"] * np.exp(-(Xm / v["kin_breed"]) ** 2 - ((Z - (M[2] - v["kin_z"])) / 0.013) ** 2)
        # neus-mondplooi met wangrol
        for s_ in (1, -1):
            a_ = np.array([s_ * (nb + 0.005), Zt - 0.002])
            b_ = np.array([s_ * (mb + 0.011), M[2] - 0.011])
            ab = b_ - a_
            q = np.stack([Xm, Z], 1)
            t = np.clip((q - a_) @ ab / (ab @ ab), 0, 1)
            dd = np.linalg.norm(q - (a_ + t[:, None] * ab), axis=1)
            buiten_ = (q - a_) @ np.array([ab[1], -ab[0]]) * s_ * -1 > 0
            nl = zijwaarde(v, "nlf", s_)
            h -= nl * gauss(dd, 0.0022)
            h += nl * 0.8 * gauss(dd - 0.0055, 0.0035) * buiten_
        # rimpels (alleen zichtbaar in de hoog-poly/bake)
        rm = v["rimpels"]
        if rm:
            for zr in g.get("voorhoofd", (0.036, 0.046, 0.057)):
                h -= rm * gauss(Z - ez0 - zr - 0.0018 * np.sin(X * 70 + zr * 300), 0.0011) * gladstap(0.055, 0.035, np.abs(X))
            for sx, e, gd, up, out in frames:
                ex_ = (X - e[0]) * sx
                for hk in g.get("kraai", (-0.25, 0.1, 0.45)):
                    h -= rm * gauss(Z - e[2] - hk * (ex_ - 0.014), 0.0009) * gladstap(0.013, 0.017, ex_) * gladstap(0.034, 0.024, ex_)
                for o_ in (0.004, 0.0075):                                           # onder het oog
                    h -= rm * 0.7 * gauss(Z - e[2] + kop.oog[2] + o_ + 0.004 * ((X - e[0]) / 0.012) ** 2, 0.0008) * \
                        gladstap(0.016, 0.01, np.abs(X - e[0]))
            ml = gladstap(0.009, 0.004, np.abs(dz - 0.006)) * gladstap(mb * 1.1, mb * 0.6, np.abs(Xm))
            h -= rm * 0.6 * np.clip(np.sin(Xm / 0.0026 * np.pi + 2 * ruis(Q, 60, 9)), 0, 1) ** 4 * ml   # lipplooitjes
        h += v["asym"] * ruis(Q, 18, int(v["seed"]), 2)
        h = h * fm + hz
        # ogen: binnen de oogzone bepaalt de oogbol met leden de vorm
        for fr in frames:
            ex, ez, nz, zu, zl, u = oog_lijnen(kop, v, fr, Q)
            w = kop.oog[0]
            ax, az, D = 1.35 * w, 1.1 * w, v["oog_diep"]
            r2 = (ex / ax) ** 2 + (ez / az) ** 2
            hb = v["oog_voor"] - D * (1 - np.sqrt(np.clip(1 - r2, 0, 1)))
            din = np.minimum(np.minimum(zu - ez, ez - zl), w * 0.98 - np.abs(ex))
            o = gladstap(-0.0003, 0.0005, din)
            t = v["lid_dik"] * np.where(ez > 0, 1.0, 0.7)
            he = hb + t * (1 - o) - 0.0035 * o
            au = np.abs(u)
            he -= v["lidplooi"] * gauss(ez - zu - 0.0048, 0.0013) * gladstap(1.2, 0.8, au)
            he += zijwaarde(v, "lidkap", fr[0]) * gauss(ez - zu - 0.0072, 0.0032) * gladstap(1.3, 0.7, au)
            he -= 0.0006 * gauss(ez - zl + 0.0028, 0.001) * gladstap(1.1, 0.7, au)
            we = gladstap(1.12, 0.86, np.sqrt(r2)) * gladstap(-0.03, -0.012, nz)    # alleen aan de voorkant
            h = h * (1 - we) + (he - nz) * we
        return h * k

    def neus(P):
        Q = (np.asarray(P, float) - C) / k
        return neusvorm(Q[:, 0] - v["neus_x"], Q[:, 2])[0] * gladstap(-0.005, -0.05, Q[:, 1])

    f.neus = neus
    return f


def verdeel(a, b, n, dichtheid):
    """n waarden van a tot b, dichter waar dichtheid(x) groot is."""
    x = np.linspace(a, b, 2000)
    c = np.concatenate([[0], np.cumsum((dichtheid(x[1:]) + dichtheid(x[:-1])) / 2 * np.diff(x))])
    return np.interp(np.linspace(0, c[-1], n), c, x)


def decimeer(o, doel, behoud=None, factor=2.0):
    """Collapse-decimatie naar ~doel driehoeken; behoud (per vertex 0..1) houdt die plekken fijner."""
    o.data.calc_loop_triangles()
    nt = len(o.data.loop_triangles)
    if nt <= doel:
        return o
    if behoud is not None:
        vg = o.vertex_groups.new(name="behoud")
        for i, w in enumerate(behoud):
            vg.add([i], float(w), "REPLACE")
    m = o.modifiers.new("dec", "DECIMATE")
    m.decimate_type = "COLLAPSE"
    m.ratio = doel / nt
    if behoud is not None:
        m.vertex_group = "behoud"
        m.invert_vertex_group = True                              # gewicht 1 = sparen
        m.vertex_group_factor = factor
    for x in bpy.context.view_layer.objects:
        x.select_set(False)
    bpy.context.view_layer.objects.active = o
    o.select_set(True)
    bpy.ops.object.modifier_apply(modifier="dec")
    if behoud is not None:
        o.vertex_groups.remove(o.vertex_groups["behoud"])
    return o


def mesh_in_bouwer(B, o):
    """Voegt een mesh-object (met UVm en regio) toe aan een Bouwer."""
    me = o.data
    P = np.zeros(len(me.vertices) * 3)
    me.vertices.foreach_get("co", P)
    b = B.verts(P.reshape(-1, 3))
    uv = np.zeros(len(me.loops) * 2, np.float32)
    me.uv_layers["UVm"].data.foreach_get("uv", uv)
    uv = uv.reshape(-1, 2)
    reg = np.zeros(len(me.polygons), np.int32)
    me.attributes["regio"].data.foreach_get("value", reg)
    for p, r in zip(me.polygons, reg):
        ls = range(p.loop_start, p.loop_start + p.loop_total)
        B.vlak([b + me.loops[i].vertex_index for i in ls], [tuple(uv[i]) for i in ls], int(r))


def bouw_kop(B, sk, kop):
    """Hoofd: schedel + gezicht_vorm op hoge resolutie (bron voor het bakken, sk.hoog_extra['lijf']),
    gedecimeerd tot gezicht['tris'] driehoeken in B (fijner rond ogen, neus en mond); echte oogbollen."""
    import bumpkin_basis as BBm
    kk = kop.k
    kop.vormfn = gezicht_vorm(kop)
    v = kop.vorm_v
    snel = BBm.SNEL
    nth, nph = (100, 150) if snel else (150, 230)
    th = verdeel(0.035 * np.pi, 0.985 * np.pi, nth, lambda t: 1 + 2.4 * np.exp(-((t - 1.8) / 0.6) ** 2))
    ph = verdeel(-np.pi, np.pi, nph + 1, lambda p: 1 + 3.2 * np.exp(-(p / 0.95) ** 2))[:-1]
    TH, PH = np.meshgrid(th, ph, indexing="ij")
    P = kop.punten(TH, PH)
    HB = Bouwer()
    b0, _ = HB.grid(P, True, regio=0)
    HB.kap(b0, nph, kop.punt(0, 0), regio=0)
    HB.kap(b0 + nph * (nth - 1), nph, kop.punt(np.pi, 0), regio=0)
    # regio 1 = neus (voor de neuskleur), per vlak uit de neusvorm
    nv = kop.vormfn.neus(P.reshape(-1, 3)).reshape(nth, nph) / kk
    nf = (nv[:-1] + np.roll(nv[:-1], -1, 1) + nv[1:] + np.roll(nv[1:], -1, 1)) / 4
    for i, x in enumerate(nf.ravel()):
        if x > 0.0045:
            HB.reg[i] = 1
    coll = bpy.context.scene.collection
    hi = HB.obj("kop_hoog", coll)
    lo = hi.copy()
    lo.data = hi.data.copy()
    coll.objects.link(lo)
    # sparen rond ogen, neus, mond, oren-aanzet; de schedel onder het haar mag grof
    Q = (np.array(HB.V) - kop.C) / kk
    sp = np.zeros(len(Q))
    for sx, e, gd, up, out in kop.oogframes:
        sp = np.maximum(sp, np.exp(-np.sum(((Q - e) / np.array([0.022, 0.03, 0.017])) ** 2, 1)))
    M = (kop.mond - kop.C) / kk
    sp = np.maximum(sp, np.exp(-((Q[:, 0]) / 0.032) ** 2 - ((Q[:, 2] - M[2]) / 0.02) ** 2) * (Q[:, 1] < -0.03))
    sp = np.maximum(sp, np.clip(np.concatenate([nv.ravel(), [0, 0]]) / 0.006, 0, 1))
    sp = np.maximum(sp * 0.9, 0.35 * gladstap(-0.0, -0.06, Q[:, 1]))
    decimeer(lo, kop.gezicht.get("tris", 1500), sp, factor=kop.gezicht.get("tris_factor", 3.0))
    mesh_in_bouwer(B, lo)
    bpy.data.objects.remove(lo)
    coll.objects.unlink(hi)
    sk.hoog_extra = getattr(sk, "hoog_extra", {})
    sk.hoog_extra["lijf"] = (hi, (0, 1))
    # oogbollen (regio 3, vaste kleur): kap van een afgeplatte ellipsoide, de achterkant onder de leden
    w = kop.oog[0]
    ax, az, D = 1.35 * w, 1.1 * w, v["oog_diep"]
    nseg = 10
    a_ = 2 * np.pi * np.arange(nseg) / nseg
    for sx, e, gd, up, out in kop.oogframes:
        dz = zijwaarde(v, "oog_dz", sx)
        rows = []
        for r in (0.3, 0.6, 0.84, 0.96):
            ex, ez = r * ax * np.cos(a_), r * az * np.sin(a_) + dz
            hb = v["oog_voor"] - D * (1 - math.sqrt(max(0.0, 1 - r * r)))
            rows.append(kop.C + kk * (e + ex[:, None] * out + ez[:, None] * up + hb * gd))
        rows.append(rows[-1] - gd * 0.004 * kk)
        b1, _ = B.grid(np.array(rows), True, regio=3)
        B.kap(b1, nseg, kop.C + kk * (e + dz * up + v["oog_voor"] * gd), regio=3)


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


def bouw_haar(sk, coll, naam="haar", lang=False, extra=None):
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
    nphi = 40
    phs = 2 * np.pi * np.arange(nphi) / nphi
    nrow = 14
    rows = [[] for _ in range(nrow + 3)]
    for ph in phs:
        zb = kop.haargrens(ph) + (0.005 * math.sin(ph * 5 + 1.3) + 0.003 * math.sin(ph * 11 + 0.4)) * kk
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
    if extra:
        extra(B, sk, kop)
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
        W = overgang(d, [L1 - 0.012 * s], [0.03 * s])
        duim = (reg == 4).astype(float)
        voeg(k + "ForeArm", W[:, 0] * m * (1 - duim))
        voeg(k + "Hand", (W[:, 1] * (1 - duim) + duim) * m)


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
    """Het hoofd komt als eigen hoog-poly (bouw_kop, sk.hoog_extra); hier alleen handen, nek en benen:
    knokkels, pezen, nagelranden en huidruis."""
    P, Nn, reg, J, s, hgt = h.P, h.Nn, h.reg, h.J, h.s, h.hgt
    hand = np.isin(reg, (2, 4))
    hgt += 0.0005 * s * ruis(P, 150, 51) * hand
    for k in ("Left", "Right"):
        for kn in getattr(sk, "knokkels", {}).get(k, []):
            hgt += 0.0014 * s * gauss(np.linalg.norm(P - kn, axis=1), 0.0045 * s) * hand
    hgt += 0.0003 * s * ruis(P, 220, 52) * np.isin(reg, (5, 7))


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
        # naden: achternaad, zijnaad, neuskap en hielstuk met stiksel; kreukels over de wreef
        for k, sx in (("Left", 1), ("Right", -1)):
            an = J[k + "Foot"]
            zij = (sx * P[:, 0] > 0) & m
            dx, dy = P[:, 0] - an[0], P[:, 1] - an[1]
            ang = np.arctan2(dx * sx, -dy)                        # 0 = voor, pi = achter
            achter = gauss(np.abs(ang) - np.pi, 0.05) * gladstap(0.03 * s, 0.05 * s, z) * zij
            buiten = gauss(ang - 1.45, 0.04) * gladstap(0.04 * s, 0.07 * s, z) * zij
            r_ = np.hypot(dx * 1.6, dy + 0.1 * s)
            kap = gauss(r_ - 0.045 * s, 0.0012 * s) * (dy < -0.07 * s) * gladstap(0.012 * s, 0.025 * s, z) * zij
            hiel = gauss(np.hypot(dx * 1.2, (dy - 0.03 * s)) - 0.05 * s, 0.0012 * s) * (dy > 0.02 * s) * \
                (z < 0.075 * s) * zij
            for naad in (achter, buiten, kap, hiel):
                h -= 0.0006 * naad
                c *= (1 - 0.3 * naad)[:, None]
                st = naad * steek(z + P[:, 0] * 0.3 + P[:, 1] * 0.5, 0.005, 0.003)
                c = c * (1 - 0.25 * st[:, None]) + srgb("#a08060")[None] * 0.25 * st[:, None]
            wreef = gladstap(0.045 * s, 0.07 * s, z) * gladstap(0.12 * s, 0.09 * s, z) * (dy < -0.02 * s) * zij
            kr = np.abs(np.sin((z / (0.009 * s)) * np.pi + 3 * ruis(P, 30, 93))) ** 6 * wreef
            c *= (1 - 0.25 * kr)[:, None]
            ruwm = ruwm + 0.1 * kr
        zet(m, c)
        H[m] = h[m]
        ruw[m] = np.clip(ruwm + 0.12, 0.55, 0.95)[m]                    # mat, versleten leer
        ruw[m & zool] = 0.88


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
        por2 = ruis(P, 2600, 107)
        vlekig = ruis(P, 45, 108, 3)
        c = basis[None] * (1 + 0.06 * r_groot[:, None] + 0.04 * por[:, None] + 0.05 * vlekig[:, None])
        c = c * (1 - 0.12 * np.clip(vlekig, 0, 1)[:, None]) + srgb("#c06850")[None] * 0.12 * np.clip(vlekig, 0, 1)[:, None]
        h = 0.00022 * por + 0.0001 * por2
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
                # oogleden (de opening is geometrie): wimperlijn op de lidranden, lid iets rozer, traankarunkel
                fr = [f_ for f_ in kop.oogframes if f_[0] == sx][0]
                ex_, ez_, nz_, zu, zl, u_ = oog_lijnen(kop, kop.vorm_v, fr, (P - kop.C) / kk)
                bij = voor & (np.abs(u_) < 1.08) & (nz_ > -0.03)
                wd = g.get("wimper", 0.0011)
                wb_ = bij & (ez_ > zu - 0.0005) & (ez_ < zu + wd)
                c[wb_] = c[wb_] * 0.3 + srgb(g.get("wimperkleur", "#2a1810")) * 0.45
                wo = bij & (ez_ < zl + 0.0003) & (ez_ > zl - 0.0007) & (np.abs(u_) < 0.95)
                c[wo] = c[wo] * 0.65 + srgb("#5a3424") * 0.2
                lid = bij & (ez_ > zu + wd) & (ez_ < zu + 0.0065)
                c[lid] = c[lid] * 0.9 + srgb(g.get("lidtint", "#b06a5a")) * 0.1
                kar = voor & (np.abs(u_ + 1.0) < 0.12) & (ez_ < zu) & (ez_ > zl - 0.001)
                c[kar] = c[kar] * 0.5 + srgb("#c0706a") * 0.5
                # wenkbrauw: borstelig, buitenkant zakt (droevig-goedig)
                t = np.clip(ex / 0.022, -0.6, 1.2)
                bz, bd, bdik = g.get("brauw", (0.0205, 0.006, 0.0034))
                zb = bz + 0.003 * (1 - t) - bd * t * t
                br = voor & (np.abs(do[:, 2] - zb) < bdik * (1 - 0.3 * t)) & (ex > -0.012) & (ex < 0.026)
                streep = 0.5 + 0.5 * np.sin((do[:, 2] - 0.4 * ex) / 0.0012 + 3 * ruis(P, 400, 104))
                c[br] = KLEUR["snor"] * (0.75 + 0.5 * streep[br, None])
                h[br] += 0.0005 * kk * streep[br]
            dm = (P - kop.mond) / kk
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
                lid = sch & (do[:, 2] > g.get("schijf_lid", 1.0))          # oude schijfoogjes; leden zijn nu geometrie
                c[lid] = srgb(g.get("lidkleur", "#5a3024"))
                rand_ = sch & (np.hypot(do[:, 0] / 1.3, do[:, 2]) > 0.011)   # oogwit naar de hoeken iets donkerder
                c[rand_] *= 0.85
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
                if getattr(sk, "nagels", None):
                    break                                             # echte vingers: geen wantengroeven
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
            for k in ("Left", "Right"):
                for kn_ in getattr(sk, "knokkels", {}).get(k, []):
                    rk = gauss(np.linalg.norm(P - kn_, axis=1), 0.007 * s) * m
                    c = c * (1 - 0.3 * rk[:, None]) + srgb("#c05a48")[None] * 0.3 * rk[:, None]
                for tip, dv, rug in getattr(sk, "nagels", {}).get(k, []):
                    q = P - (tip - dv * 0.006 * s)
                    na = m & (np.abs(q @ dv) < 0.0055 * s) & (q @ rug > 0.002 * s) &                         (np.linalg.norm(q - np.outer(q @ dv, dv), axis=1) < 0.0085 * s)
                    c[na] = c[na] * 0.55 + srgb("#e0b0a0") * 0.45
                    ruw[na] = 0.35
            vuil_h = gladstap(0.3, 0.9, ruis(P, 90, 105, 2)) * m                    # werkhanden: vuil in de plooien
            c *= (1 - 0.18 * vuil_h)[:, None]
            ruw[m] = np.clip(0.62 + 0.1 * ruis(P, 60, 106), 0.45, 0.8)[m]
        zet(m, c)
        H[m] = h[m]


def verf_mond(cx, c, h, dm, huid, g):
    """Mond zonder snor: lippen, mondspleet, glimlach (mondhoeken omhoog), lachplooien."""
    kk = cx.sk.kop.k
    lach = g.get("lach", 0.006)                     # hoe ver de mondhoeken omhoog gaan
    bw = g.get("mondbreed", 0.021)
    x = dm[:, 0] / bw
    v_ = getattr(cx.sk.kop, "vorm_v", VORM)
    lijn = dm[:, 2] - v_["mond_z"] - lach * x * x - v_["mond_scheef"] * x     # z t.o.v. de mondspleet (als de vorm)
    binnen = huid & (np.abs(x) < 1) & (dm[:, 1] < 0.02)
    lipk = srgb(g.get("lip", "#b86058"))
    bov = binnen & (lijn > 0) & (lijn < g.get("bovenlip", 0.0032) * (1 - 0.6 * x * x))
    ond = binnen & (lijn < 0) & (lijn > -g.get("onderlip", 0.0045) * (1 - 0.6 * x * x))
    zacht = np.clip(1 - x * x, 0, 1) ** 0.5
    bov = binnen & (lijn > 0) & (lijn < 0.0068 * zacht)
    ond = binnen & (lijn < 0) & (lijn > -(g.get("open", 0.0) + 0.0085) * zacht)
    c[bov] = c[bov] * 0.45 + lipk * 0.55
    c[ond] = c[ond] * 0.35 + lipk * 1.05 * 0.65
    sp = huid & (np.abs(lijn) < 0.0009 * zacht) & (np.abs(x) < 1.0) & (dm[:, 1] < 0.02)
    c[sp] = c[sp] * 0.35 + srgb("#5a2420") * 0.35
    h[sp] -= 0.0006 * kk
    op = g.get("open", 0.0)                                        # open mond: donkere holte onder de spleet
    if op:
        mo = huid & (lijn < 0) & (lijn > -op * np.sqrt(np.clip(1 - x * x, 0, 1))) & (np.abs(x) < 0.92) & (dm[:, 1] < 0.02)
        c[mo] = srgb("#4a1c18") * (0.8 + 0.4 * np.clip(-lijn[mo] / op, 0, 1))[:, None]
        h[mo] -= 0.001 * kk
        ond2 = binnen & (lijn <= -op * (1 - 0.7 * x * x)) & (lijn > -(op + g.get("onderlip", 0.0045)) * (1 - 0.6 * x * x))
        c[ond2] = c[ond2] * 0.45 + lipk * 0.55
    # mondhoeken en lachplooien
    for sx in (1, -1):
        hoek = np.hypot(dm[:, 0] - sx * bw * 1.05, dm[:, 2] - lach) / 0.004
        c *= (1 - 0.12 * gauss(hoek, 1.0) * huid)[:, None]


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
    hh = getattr(sk, "haarhuid", 0.0)                         # dun haar: de hoofdhuid schemert door de schil
    if hh:
        sch = (reg == 0) & m
        f_ = hh * (0.6 + 0.4 * (0.5 + 0.5 * ruis(P, 40, 502)))
        c[sch] = c[sch] * (1 - f_[sch, None]) + KLEUR["huid"] * f_[sch, None]
    zet(m, c)
    ruw[m] = 0.82
    kaart_verf(cx)


def kaart_verf(cx):
    """Haarkaarten (regio KAART_REGIO): strengen als alpha, punten taps en ongelijk lang, wortel donker."""
    import bumpkin_basis as BBm
    m = cx.Dm & (cx.reg == BBm.KAART_REGIO)
    if not m.any():
        return
    a = np.clip(cx.U / KAART_B, -1, 1)
    t = np.clip(cx.V / KAART_L, 0, 1)
    fase = ruis(cx.P, 25, 501)
    x = (a * 0.5 + 0.5) * 4.5 + 0.45 * np.sin(t * 4 + fase * 3) + 0.25 * ruis(cx.P, 160, 503)
    idx = np.floor(x)
    frac = x - idx
    hsh = (np.sin(idx * 12.9898 + fase * 78.233) * 43758.5453) % 1.0
    lengte = 0.6 + 0.4 * hsh
    breedte = 0.44 * (1 - 0.6 * t / lengte) + 0.06 * ruis(cx.P, 400, 504)
    s = np.abs(frac - 0.5)
    alfa = (s < breedte) & (t < lengte) & (np.abs(a) < 0.97)
    alfa |= (t < 0.1) & (np.abs(a) < 0.92)
    cx.alfa[m] = alfa[m].astype(float)
    kl = cx.KLEUR[cx.tint][None] * (0.78 + 0.35 * t[:, None] ** 0.8) * (0.9 + 0.2 * hsh[:, None]) * \
        (1 - 0.15 * (s[:, None] / 0.5) ** 2)
    cx.zet(m, kl)
    cx.H[m] = (0.0005 * (0.36 - s))[m]
    cx.ruw[m] = 0.62


KAART_B, KAART_L = 0.01, 0.06          # UVm van een haarkaart: halve breedte en lengte (vast, voor de schilder)


def haarkaart(B, sk, pad, breed, nrm=None, regio=3, tip=0.5, kruis=False):
    """Haarkaart langs pad: een strook van `breed` (halve breedte) met vaste UVm (KAART_B x KAART_L), die de
    schilder als strengen met alpha invult. nrm = de vlakrichting (normaal van de kaart); kruis = een tweede
    strook haaks erop (pluk die uitsteekt)."""
    pad = np.asarray(pad, float)
    m = len(pad)
    tg = np.gradient(pad, axis=0)
    tg /= np.linalg.norm(tg, axis=1, keepdims=True) + 1e-12
    if nrm is None:
        nrm = np.array([straal(sk.kop, q) for q in pad])
    nrm = np.asarray(nrm, float)
    for k_ in ((0, 1) if kruis else (0,)):
        b0 = len(B.V)
        for i in range(m):
            u = i / (m - 1)
            n_ = nrm[i] - (nrm[i] @ tg[i]) * tg[i]
            n_ /= np.linalg.norm(n_) + 1e-12
            sd = np.cross(tg[i], n_)
            if k_:
                sd = n_
            w = breed * (1 - (1 - tip) * u)
            B.verts([pad[i] - sd * w, pad[i] + sd * w])
        for i in range(m - 1):
            v0, v1 = (i / (m - 1)) * KAART_L, ((i + 1) / (m - 1)) * KAART_L
            B.vlak([b0 + 2 * i, b0 + 2 * i + 1, b0 + 2 * i + 3, b0 + 2 * i + 2],
                   [(-KAART_B, v0), (KAART_B, v0), (KAART_B, v1), (-KAART_B, v1)], regio)



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
        kuit = gladstap(sk.zr(0.36), sk.zr(0.18), P[:, 2]) * getattr(sk, "rok_kuit", 0.4) * kant * lijf
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
    sk.riem_z = zb
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
    v_ = getattr(kop, "vorm_v", VORM)
    kaal = lambda t, p: kop.punt(t, p, vorm=False)
    for x, br, ho in tanden:
        ph = math.atan2(x, 0.09)
        top = kop.punt(kop.theta_bij_z(ph, kop.mond[2] + dz * kk, kaal), ph, v_["snuit"] * kk * 0.8 + v_["lip_b"] * kk * 0.3, vorm=False)
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
    nphi = 34
    phs = 2 * np.pi * np.arange(nphi) / nphi
    nrow = 12
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
               schulp=0.0, hoog_=0.012, n=None, bv=0.95, zacht=0.7):
    """Kraag om de hals: plooikraag (plooi > 0, zigzag op en neer) of platte schulpkraag (schulp > 0).
    Dubbel vel met een gesloten buitenrand (regio 0)."""
    s = sk.s
    zc = (sk.nz + 0.012 * s) if z0 is None else z0
    n = n or plooien * 4
    th = 2 * np.pi * np.arange(n) / n
    zz = np.sin(th * plooien) * plooi * s * zacht
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
def bouw_staf(sk, coll, naam="prop_staf", lengte=1.45, ranken=2, bladeren=14, krul=True, seed=3, dik=1.0,
              rank_dik=1.0, blad=1.0):
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
        n = 40
        tt = np.linspace(0.02, 0.95 - 0.25 * r_, n)
        rp = []
        for t_ in tt:
            i = min(int(t_ * (nprof - 1)), nprof - 2)
            pos, tg, ff, ss = fr[i]
            a_ = fase + t_ * wind * 2 * math.pi
            rad = prof[i][1] + 0.0035 * s * rank_dik
            rp.append(pos + (ff * math.cos(a_) + ss * math.sin(a_)) * rad)
        rprof = [(t, 0.0055 * s * rank_dik * (1 - 0.5 * t), 0.0055 * s * rank_dik * (1 - 0.5 * t)) for t in np.linspace(0, 1, n)]
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
            ln = rng.uniform(0.026, 0.04) * s * blad
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
    c[rank] = KLEUR["rank"] * (1.5 + 0.3 * cx.r_fijn[rank, None])
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



# ================================================================================================
# Haar: plukken (laag, het silhouet) en strengen/krullen (hoog, alleen voor de bake)
# ================================================================================================
# De laag-poly is een schil (bouw_haar / bouw_haar_glad) plus plukken: platte, taps toelopende lokken,
# kurkentrekkerkrullen of piekende plukken. Plukken en schil leggen strengen vast in sk.strengen; de
# hoog-poly (haar_hoog, via sk.hoog_makers) bouwt daaruit dunne buisjes en spiraalkrullen met een kleur per
# streng (wortel donker, punt licht), zodat normaal, AO en kleur de richting van het haar dragen in plaats
# van ruis. Regio's: 0 schil, 1 plukken, 2 knot/staartjes.

def schil_hoeken(kop, d):
    d = np.asarray(d, float)
    d = d / np.linalg.norm(d)
    return math.acos(np.clip(d[2], -1, 1)), math.atan2(d[0], -d[1])


def op_schil(kop, d, lift=0.0, klont=True):
    """Punt op de haarschil in richting d (vanuit kop.Ch) plus lift langs de straal."""
    th, ph = schil_hoeken(kop, d)
    return kop.haarpunt(th, ph, klont, lift)


def boog(a, b, n):
    """n richtingen langs de grote cirkel van a naar b."""
    a = np.asarray(a, float) / np.linalg.norm(a)
    b = np.asarray(b, float) / np.linalg.norm(b)
    om = math.acos(np.clip(a @ b, -1, 1))
    if om < 1e-6:
        return [a] * n
    return [(math.sin((1 - t) * om) * a + math.sin(t * om) * b) / math.sin(om) for t in np.linspace(0, 1, n)]


def kopmaat(sk):
    return sk.kop.k if hasattr(sk, "kop") else 1.0


def streng(sk, pad, dikte, licht=1.0):
    sk.strengen = getattr(sk, "strengen", [])
    sk.strengen.append(("streng", np.asarray(pad, float), dikte, licht))


def spiraal(sk, p0, as_, lengte, rc, rt, slagen, licht=1.0, fase=0.0):
    """Een hoog-poly-krul: spiraalbuisje om as_ vanaf p0."""
    sk.strengen = getattr(sk, "strengen", [])
    sk.strengen.append(("krul", np.asarray(p0, float), np.asarray(as_, float), lengte, rc, rt, slagen, licht, fase))


def pluk_buis(B, pad, nrm, breed, dik, n=4, regio=1, tip=0.2, sk=None, strengen=0, licht=1.0, rng=None,
              krul=0.0, dikte=(0.0011, 0.0018)):
    """Lok langs pad (m, 3) met per punt een boven-richting nrm (weg van de schedel): breed/dik zijn de
    halve maten aan de wortel, taps naar de punt. Legt strengen (hoog-poly) vast in sk.strengen."""
    pad = np.asarray(pad, float)
    nrm = np.asarray(nrm, float)
    m = len(pad)
    tg = np.gradient(pad, axis=0)
    tg /= np.linalg.norm(tg, axis=1, keepdims=True) + 1e-12
    rings, frames = [], []
    for i in range(m):
        u = i / (m - 1)
        t = tg[i]
        nn_ = nrm[i] - (nrm[i] @ t) * t
        nn_ /= np.linalg.norm(nn_) + 1e-12
        sd = np.cross(t, nn_)
        w = breed * (1 - (1 - tip) * u ** 1.5)
        d = dik * (1 - 0.6 * u)
        frames.append((pad[i], t, nn_, sd, w, d))
        if n == 4:
            pts = [pad[i] + sd * w, pad[i] + nn_ * d, pad[i] - sd * w, pad[i] - nn_ * d * 0.35]
        else:
            a_ = 2 * np.pi * np.arange(n) / n
            pts = [pad[i] + sd * w * math.cos(x) + nn_ * d * math.sin(x) * (1 if math.sin(x) > 0 else 0.45) for x in a_]
        rings.append(pts)
    b0, _ = B.grid(np.array(rings), True, regio=regio)
    B.kap(b0 + n * (m - 1), n, pad[-1] + tg[-1] * breed * tip * 1.2, regio=regio)
    if sk is not None and strengen:
        rng = rng or np.random.default_rng(len(getattr(sk, "strengen", [])))
        kk = kopmaat(sk)
        for _ in range(strengen):
            a_ = rng.uniform(0, 2 * np.pi)
            rr = math.sqrt(rng.uniform(0.2, 1.0)) * 0.95
            fase = rng.uniform(0, 2 * np.pi)
            lengte = rng.uniform(0.75, 1.02)
            pts = []
            for i, (p, t, nn_, sd, w, d) in enumerate(frames):
                if i / (m - 1) > lengte:
                    break
                kr = krul * math.sin(i / (m - 1) * 6 + fase)
                pts.append(p + sd * w * (rr * math.cos(a_) + kr) +
                           nn_ * d * rr * math.sin(a_) * (1 if math.sin(a_) > 0 else 0.4))
            if len(pts) >= 3:
                streng(sk, pts, rng.uniform(*dikte) * kk * getattr(sk, "streng_dik", 1.8), licht * rng.uniform(0.85, 1.12))
    return frames


def schil_strengen(sk, n, van, naar, lift=0.0016, seed=0, licht=(0.85, 1.15), dikte=(0.0011, 0.0018),
                   klont=True, stappen=14):
    """n strengen over de schil: elk van een richting van(rng) naar een richting naar(rng), langs de grote
    cirkel, op de schil."""
    kop = sk.kop
    kk = kop.k
    rng = np.random.default_rng(seed)
    for _ in range(n):
        a, b = van(rng), naar(rng)
        ds = boog(a, b, stappen)
        pts = [op_schil(kop, d, lift * kk, klont) for d in ds]
        streng(sk, pts, rng.uniform(*dikte) * kk * getattr(sk, "streng_dik", 1.8), rng.uniform(*licht))


def haar_hoog(sk, kleur, naam="haar_strengen", donker=0.62, punt=1.18, warm=0.08):
    """Registreert de hoog-poly uit sk.strengen (sk.hoog_makers['haar']): strengen = 3-zijdige buisjes,
    krullen = 4-zijdige spiraalbuisjes. Kleur per vertex: basis x licht, van donker (wortel) naar punt."""
    def maak(coll):
        V, F, Ck = [], [], []
        rng = np.random.default_rng(77)
        for item in getattr(sk, "strengen", []):
            if item[0] == "streng":
                _, pad, rt, licht = item
                m = len(pad)
                if m < 2:
                    continue
                u = np.linspace(0, 1, m)
                sides = 3
            else:
                _, p0, as_, L, rc, rt, sl, licht, fase = item
                as_ = as_ / np.linalg.norm(as_)
                e1 = np.cross(as_, (0.3, 0.2, 0.9))
                e1 /= np.linalg.norm(e1) + 1e-9
                e2 = np.cross(as_, e1)
                m = max(8, int(sl * 9))
                u = np.linspace(0, 1, m)
                ang = fase + 2 * np.pi * sl * u
                rcu = rc * (1 - 0.25 * u)
                pad = p0[None] + as_[None] * (u * L)[:, None] + \
                    (np.cos(ang)[:, None] * e1 + np.sin(ang)[:, None] * e2) * rcu[:, None]
                sides = 4
            w_ = rng.uniform(-1, 1) * warm
            kl = np.clip(kleur * licht * np.array([1 + 0.3 * w_, 1 + w_ * 0.1, 1 - w_]), 0, 1)
            tg = np.gradient(pad, axis=0)
            tg /= np.linalg.norm(tg, axis=1, keepdims=True) + 1e-12
            b0 = len(V)
            for i in range(m):
                t = tg[i]
                a_ = np.cross(t, (0.31, 0.13, 0.94))
                if np.linalg.norm(a_) < 1e-3:
                    a_ = np.cross(t, (1, 0, 0))
                a_ /= np.linalg.norm(a_)
                b_ = np.cross(t, a_)
                r = rt * (1 - 0.55 * u[i] ** 2)
                f_ = donker + (punt - donker) * u[i] ** 0.7
                for kx in range(sides):
                    an = 2 * np.pi * kx / sides
                    V.append(pad[i] + (math.cos(an) * a_ + math.sin(an) * b_) * r)
                    Ck.append(np.clip(kl * f_, 0, 1))
            for i in range(m - 1):
                for kx in range(sides):
                    k1 = (kx + 1) % sides
                    F.append((b0 + i * sides + kx, b0 + i * sides + k1, b0 + (i + 1) * sides + k1,
                              b0 + (i + 1) * sides + kx))
        me = bpy.data.meshes.new(naam)
        me.from_pydata([tuple(p) for p in V], [], F)
        me.update()
        at = me.attributes.new("kleur", "FLOAT_COLOR", "POINT")
        at.data.foreach_set("color", np.concatenate([np.array(Ck), np.ones((len(Ck), 1))], 1).ravel().astype(np.float32))
        me.shade_smooth()
        o = bpy.data.objects.new(naam, me)
        coll.objects.link(o)
        print("  haarstrengen", len(getattr(sk, "strengen", [])), "stuks,", len(F) * 2, "driehoeken", flush=True)
        return o
    sk.hoog_makers = getattr(sk, "hoog_makers", {})
    sk.hoog_makers.setdefault("haar", []).append(maak)


def krullen_op_schil(sk, n, seed=3, lengte=(0.016, 0.03), rc=(0.0055, 0.009), rt=(0.0022, 0.0032),
                     slagen=(1.4, 2.4), licht=(0.8, 1.2), zak=0.6, tmin=0.02, grens=None, groep=7, diep=0.006,
                     spreid=0.06):
    """Ringelkrullen over de krullenbol, in groepjes (zelfde richting en tint) die schuin naar buiten en
    omlaag wijzen, half in de schil: in de bake leesbare krullen in plaats van ruis."""
    kop = sk.kop
    kk = kop.k
    rng = np.random.default_rng(seed)
    hg = grens or kop.haargrens
    i = 0
    while i < n:
        ph = rng.uniform(-np.pi, np.pi)
        tb = kop.theta_bij_z(ph, hg(ph), lambda t, p: kop.haarpunt(t, p, False))
        th = math.acos(rng.uniform(math.cos(tb + 0.04), math.cos(tmin)))
        c0 = kop.haarpunt(th, ph)
        nrm = c0 - kop.Ch
        nrm /= np.linalg.norm(nrm)
        neer = np.array([0, 0, -1.0]) - nrm[2] * nrm
        neer = neer / (np.linalg.norm(neer) + 1e-9)
        as0 = nrm * 0.75 + neer * zak + rng.normal(size=3) * 0.2
        as0 /= np.linalg.norm(as0)
        lt = rng.uniform(*licht)
        for _ in range(int(rng.integers(max(2, groep - 3), groep + 3))):
            d = (c0 - kop.Ch) / np.linalg.norm(c0 - kop.Ch) + rng.normal(size=3) * spreid
            t2, p2 = schil_hoeken(kop, d)
            if t2 > tb + 0.05:
                continue
            p0 = kop.haarpunt(t2, p2) - nrm * diep * kk
            as_ = as0 + rng.normal(size=3) * 0.15
            spiraal(sk, p0, as_ / np.linalg.norm(as_), rng.uniform(*lengte) * kk, rng.uniform(*rc) * kk,
                    rng.uniform(*rt) * kk, rng.uniform(*slagen), lt * rng.uniform(0.92, 1.08), rng.uniform(0, 6.3))
            i += 1


def kurkentrekkers(B, sk, plekken, lengte=(0.12, 0.18), r=0.012, buis=0.0095, spoed=0.038, n=5, seed=4,
                   regio=1, hoog_krullen=9):
    """Hangende kurkentrekkerkrullen (vrouw): plekken = [(ph, z0)] aanzet op de schil; laag = spiraalbuis,
    hoog = spiraalstrengen eromheen."""
    kop = sk.kop
    kk = kop.k
    rng = np.random.default_rng(seed)
    for ph, z0 in plekken:
        th = kop.theta_bij_z(ph, kop.zz(z0), lambda t, p: kop.haarpunt(t, p, False))
        q = kop.haarpunt(th, ph, False)
        p0 = q - (q - kop.Ch) * 0.08
        uit = np.array([math.sin(ph), -math.cos(ph), 0.0])
        L = rng.uniform(*lengte) * kk
        as_ = np.array([0, 0, -1.0]) + uit * rng.uniform(0.15, 0.35)
        as_ /= np.linalg.norm(as_)
        e1 = uit - (uit @ as_) * as_
        e1 /= np.linalg.norm(e1)
        e2 = np.cross(as_, e1)
        sl = L / (spoed * kk)
        m = max(6, int(sl * 4.5) + 2)
        fase = rng.uniform(0, 6.3)
        u = np.linspace(0, 1, m)
        ang = fase + 2 * np.pi * sl * u
        rr = r * kk * (0.7 + 0.5 * u)
        rad = np.cos(ang)[:, None] * e1 + np.sin(ang)[:, None] * e2
        pad = p0[None] + as_[None] * (u * L)[:, None] + rad * rr[:, None]
        pluk_buis(B, pad, rad, buis * kk, buis * kk * 0.9, n=n, regio=regio, tip=0.45)
        for j in range(hoog_krullen):
            a_ = j / max(hoog_krullen, 1) * 2 * np.pi
            off = (np.cos(a_) * e1 + np.sin(a_) * e2) * buis * kk * 0.35
            spiraal(sk, p0 + off, as_, L * rng.uniform(0.85, 1.0), r * kk * (1.0 + 0.25 * math.cos(a_)),
                    0.0028 * kk, sl * rng.uniform(0.95, 1.05), rng.uniform(0.85, 1.15), fase + a_ * 0.05)


@hoog("haar")
def hg_haar_nieuw(h, sk):
    """Schil en plukken: geen ruis meer (die gaf schors); vorm komt van de plukken, detail van de strengen."""
    pass


GEWICHT["haar"] = GEWICHT["kop"]


# ================================================================================================
# Plooien: zak en kreukels bij ellebogen, polsen, knieen, enkels en taille (hemd, kledij, tuinbroek, broek)
# ================================================================================================
# Hetzelfde veld twee keer: grof op de laag-poly (LAAG-register in bumpkin_basis: het silhouet zakt een
# beetje bij elleboog en knie) en fijn in de hoog-poly (scherpe vouwen, ronde ruggen). plooi(x) heeft scherpe
# dalen en ronde ruggen, zoals stof.

def plooi(x):
    return np.abs(np.sin(np.pi * x)) - 0.5


def plooiveld(P, sk, naam, soort, reg, fijn=True, sterkte=1.0):
    s = sk.s
    J = sk.J
    h = np.zeros(len(P))
    r1 = ruis(P, 8, 301)
    r2 = ruis(P, 15, 302)
    if soort == "hemd":
        mouwen, mm = getattr(sk, "mouw", {}), reg == 1
    elif soort == "kledij":
        mouwen, mm = getattr(sk, "mouwen", {}).get(naam, {}), np.isin(reg, (1, 4))
    else:
        mouwen, mm = {}, np.zeros(len(P), bool)
    for k, pts in mouwen.items():
        sx = 1 if k == "Left" else -1
        zij = (np.sign(P[:, 0]) == sx) & mm
        if not zij.any():
            continue
        d, rv = keten_param(P, pts)
        L0 = np.linalg.norm(pts[1] - pts[0])
        e = L0 + np.linalg.norm(pts[2] - pts[1])
        w = e + np.linalg.norm(pts[3] - pts[2])
        rn = rv / (np.linalg.norm(rv, axis=1, keepdims=True) + 1e-9)
        voor = np.clip(-rn[:, 1], 0, 1)
        achter = np.clip(rn[:, 1], 0, 1)
        ang = np.arctan2(rn[:, 0] * sx, -rn[:, 1])
        if fijn:
            x = (d - e) / (0.019 * s) + 0.55 * ang + 1.5 * r1                      # elleboogholte: halve manen
            h += 0.0048 * s * plooi(x) * gauss(d - e, 0.045 * s) * (0.3 + 0.7 * voor)
            x = (d - (w - 0.055 * s)) / (0.016 * s) + 2.0 * r2 + 0.45 * ang          # pols: gestuwde ringen
            h += 0.0036 * s * plooi(x) * gauss(d - (w - 0.06 * s), 0.03 * s)
            x = ang * 2 / np.pi + d / (0.085 * s) + r1                              # gedraaide val langs de arm
            h += 0.0018 * s * plooi(x) * gladstap(L0, L0 + 0.06 * s, d)
            x = ang * 3.0 + 2 * r2                                                  # oksel
            h += 0.003 * s * plooi(x / np.pi) * gauss(d - L0 - 0.015 * s, 0.03 * s) * np.clip(-rn[:, 2], 0, 1)
        h += 0.004 * s * gauss(d - e, 0.05 * s) * achter * zij * (0.6 + 0.4 * r1)    # zak achter de elleboog
        h += 0.0025 * s * gauss(d - (w - 0.06 * s), 0.035 * s) * zij                 # opgestuwd bij de pols
        h *= np.where(zij | ~mm, 1.0, 1.0)
    benen = np.zeros(len(P), bool)
    if soort in ("tuinbroek", "broek"):
        benen = reg == 0
    for k, sx in (("Left", 1), ("Right", -1)):
        zij = (sx * P[:, 0] > 0) & benen
        if not zij.any():
            continue
        pts = [J[k + "UpLeg"], J[k + "Leg"], J[k + "Foot"]]
        d, rv = keten_param(P, pts)
        L1 = np.linalg.norm(pts[1] - pts[0])
        L2 = np.linalg.norm(pts[2] - pts[1])
        rn = rv / (np.linalg.norm(rv, axis=1, keepdims=True) + 1e-9)
        voor = np.clip(-rn[:, 1], 0, 1)
        achter = np.clip(rn[:, 1], 0, 1)
        binnen = np.clip(-rn[:, 0] * sx, 0, 1)
        ang = np.arctan2(rn[:, 0] * sx, -rn[:, 1])
        hb = np.zeros(len(P))
        if fijn:
            x = (d - L1) / (0.021 * s) + 0.5 * ang + 1.4 * r1                       # knieholte
            hb += 0.0046 * s * plooi(x) * gauss(d - L1, 0.05 * s) * (0.3 + 0.7 * achter)
            x = (d - (L1 + L2 - 0.16 * s)) / (0.02 * s) + 2.0 * r2 + 0.35 * ang      # gestuwd boven de laars
            hb += 0.0042 * s * plooi(x) * gauss(d - (L1 + L2 - 0.15 * s), 0.04 * s)
            x = ang * 1.4 + d / (0.05 * s) + r1                                    # kruisplooien
            hb += 0.0026 * s * plooi(x) * gauss(d - 0.07 * s, 0.05 * s) * binnen
        hb += 0.0035 * s * gauss(d - L1 + 0.01 * s, 0.05 * s) * voor * (0.6 + 0.4 * r1)   # knie uitgezakt
        hb += 0.003 * s * gauss(d - (L1 + L2 - 0.15 * s), 0.035 * s)               # stuwing boven de laars
        h += hb * zij
    # taille: stof stuwt boven en onder de riem
    zr = getattr(sk, "riem_z", None)
    if zr is not None and soort in ("hemd", "kledij", "tuinbroek", "broek"):
        romp = ~mm & ~benen
        phi = np.arctan2(P[:, 0], -P[:, 1])
        z = P[:, 2]
        if fijn:
            x = (z - zr) / (0.014 * s) + 2.0 * r1 + 0.4 * np.sin(phi * 3)
            h += 0.003 * s * plooi(x) * gauss(z - zr - 0.035 * s, 0.03 * s) * romp
            x = phi * 9 / np.pi + 2 * r2                                         # verticale val onder de riem
            h += 0.0022 * s * plooi(x) * gladstap(zr - 0.01 * s, zr - 0.05 * s, z) * gladstap(zr - 0.2 * s, zr - 0.12 * s, z) * romp
        h += 0.003 * s * gauss(z - zr - 0.03 * s, 0.025 * s) * romp * (0.5 + 0.5 * r1)   # bloes boven de riem
    return h * sterkte


def laag_plooi(o, sk, naam):
    import bumpkin_basis as BBm
    me = o.data
    P, Nn = BBm.vert_np(me)
    reg = vertex_regio(me)
    h = plooiveld(P, sk, naam, BBm.C.soort(naam), reg, fijn=False, sterkte=getattr(sk, "plooi_sterkte", 1.4))
    me.vertices.foreach_set("co", (P + Nn * h[:, None]).ravel())
    me.update()


def plooi_hoog(h_, sk, soort):
    h_.hgt += plooiveld(h_.P, sk, h_.naam, soort, h_.reg, fijn=True, sterkte=getattr(sk, "plooi_sterkte", 1.7))


for _s in ("hemd", "kledij", "tuinbroek", "broek"):
    LAAG[_s] = laag_plooi
    if _s == "broek":                                             # hg_broek roept de tuinbroek aan
        continue
    _fn, _n, _simpel = HOOG[_s]

    def _hoog(h_, sk, _fn=_fn, _s=_s):
        _fn(h_, sk)
        plooi_hoog(h_, sk, _s)
    HOOG[_s] = (_hoog, _n, _simpel)


# ================================================================================================
# Slijtage: vuil en sleet na de schilders (VERF['_slijtage'], vanuit componeer), voor alle personages
# ================================================================================================
# Stof: opspattend vuil tot de kuit, vuile knieen, sleet op ellebogen en zitvlak, groezelige manchetten en
# zomen, en ruwheid die meevarieert (vuil = doffer). Laarzen: stof op neus en zool, lichte schaafplekken,
# donkere kreukels. Huid: ruwheid per zone (neus/voorhoofd glanzender), rode oorranden en knokkels.
# sk.vuil (standaard 1) schaalt alles per personage.

def slijtage(cx):
    import bumpkin_basis as BBm
    C = BBm.C
    P, z, s, J, sk, reg = cx.P, cx.z, cx.s, cx.J, cx.sk, cx.reg
    kl, ruw = cx.kl, cx.ruw
    vf = getattr(sk, "vuil", 1.0)
    vuilk = srgb("#6a5a44")
    stofk = srgb("#8a7a62")
    blot = 0.5 + 0.5 * ruis(P, 9, 401, 3)
    fijn = 0.5 + 0.5 * ruis(P, 70, 402, 2)
    for nm in C.DELEN:
        m = cx.D[nm]
        if not m.any():
            continue
        soort = C.soort(nm)
        if soort in ("hemd", "kledij", "tuinbroek", "broek"):
            a = 0.32 * gladstap(0.3 * s, 0.04 * s, z) * (0.35 + 0.65 * fijn) * (0.6 + 0.4 * blot)
            if soort in ("tuinbroek", "broek"):
                for k in ("Left", "Right"):
                    kn = J[k + "Leg"] + np.array([0, -0.07 * s, 0.01 * s])
                    a += 0.42 * gauss(np.linalg.norm((P - kn) * np.array([1, 1, 0.75]), axis=1), 0.045 * s) * \
                        (0.4 + 0.6 * blot) * (P[:, 1] < kn[1] + 0.05 * s)
                zit = (P[:, 1] > 0.03 * s) & (np.abs(z - sk.z(0.6)) < 0.06 * s)
                a += 0.18 * zit * blot
            mw = {}
            if soort == "hemd":
                mw = getattr(sk, "mouw", {})
            elif soort == "kledij":
                mw = getattr(sk, "mouwen", {}).get(nm, {})
            for k, pts in mw.items():
                d, rv = keten_param(P, pts)
                L0 = np.linalg.norm(pts[1] - pts[0])
                e = L0 + np.linalg.norm(pts[2] - pts[1])
                w = e + np.linalg.norm(pts[3] - pts[2])
                zij = np.sign(P[:, 0]) == (1 if k == "Left" else -1)
                rn = rv / (np.linalg.norm(rv, axis=1, keepdims=True) + 1e-9)
                a += 0.22 * gauss(d - e, 0.035 * s) * np.clip(rn[:, 1], 0, 1) * zij * blot     # elleboog
                a += 0.25 * gladstap(w - 0.05 * s, w, d) * zij * (0.5 + 0.5 * fijn)          # manchet
            zl = getattr(sk, "kledij_z", {}).get(nm, (None, None))[0]
            if soort == "kledij" and zl is not None and zl > 0:
                a += 0.3 * gladstap(zl + 0.05 * s, zl, z) * (0.5 + 0.5 * fijn)             # zoom
            a = np.clip(a * vf * 0.7, 0, 0.5) * (0.55 + 0.45 * fijn)
            kl[m] = (kl * (1 - a[:, None]) + vuilk[None] * a[:, None] * (0.8 + 0.4 * blot[:, None]))[m]
            ruw[m] = np.clip(ruw + 0.06 * (fijn - 0.5) + 0.06 * a, 0.5, 1.0)[m]
        elif soort == "laarzen":
            a = 0.45 * gladstap(0.07 * s, 0.0, z) * (0.4 + 0.6 * fijn)
            for k, sx in (("Left", 1), ("Right", -1)):
                neus = J[k + "Foot"] + np.array([sx * 0.01 * s, -0.14 * s, 0.03 * s])
                a += 0.35 * gauss(np.linalg.norm(P - neus, axis=1), 0.04 * s) * blot
            a = np.clip(a * vf, 0, 0.7)
            kl[m] = (kl * (1 - a[:, None]) + stofk[None] * a[:, None])[m]
            ruw[m] = np.clip(ruw + 0.25 * a + 0.08 * (fijn - 0.5), 0.35, 0.95)[m]
        elif soort == "lijf" and hasattr(sk, "kop"):
            kop = sk.kop
            q = (P - kop.C) / kop.k
            hoofd = np.isin(reg, (0, 1, 6)) & m
            tz = np.exp(-(q[:, 0] / 0.02) ** 2 - ((q[:, 2] - 0.02) / 0.05) ** 2) * (q[:, 1] < -0.05)  # T-zone
            r_ = 0.62 - 0.12 * tz - 0.08 * (reg == 1) + 0.08 * (fijn - 0.5)
            ruw[hoofd] = np.clip(r_, 0.4, 0.8)[hoofd]
            oor = (reg == 6) & m
            if oor.any():
                rand = gladstap(0.3, 0.9, np.abs(q[:, 0]) / (np.abs(q[:, 0]).max() + 1e-9))
                kl[oor] = (kl * (1 - 0.25 * rand[:, None]) + srgb("#c0584a")[None] * 0.25 * rand[:, None])[oor]


VERF["_slijtage"] = slijtage


# --- kapsels uit plukken -------------------------------------------------------------------------
def straal(kop, p):
    d = np.asarray(p, float) - kop.Ch
    return d / (np.linalg.norm(d) + 1e-12)


def kaart_over(B, sk, frames, factor=1.4, verleng=0.25, lift=0.7):
    """Haarkaart over een pluk (frames van pluk_buis): iets breder en verder dan de pluk, zodat de rand rafelt."""
    pad = [p + nn_ * d * lift for p, t, nn_, sd, w, d in frames]
    p, t = pad[-1], frames[-1][1]
    L = sum(np.linalg.norm(pad[i + 1] - pad[i]) for i in range(len(pad) - 1))
    pad = pad + [p + t * L * verleng * 0.5, p + t * L * verleng]
    nrm = [f[2] for f in frames] + [frames[-1][2]] * 2
    haarkaart(B, sk, pad, frames[0][4] * factor, nrm=nrm, tip=0.55)


def lok_meridiaan(B, sk, ph, th0, val, breed, dik, n=7, strengen=7, licht=1.0, seed=0, buig=0.0, naar_voren=0.0,
                  kaart=1.4):
    """Lok van de kruin (th0) langs de meridiaan ph tot de haargrens en dan `val` (m) vrij naar beneden
    (pony over het voorhoofd, lokken over de oren). buig: de punt draait opzij (rad)."""
    kop = sk.kop
    kk = kop.k
    zb = kop.haargrens(ph)
    tb = kop.theta_bij_z(ph, zb, lambda t, p: kop.haarpunt(t, p, False))
    pad, nrm = [], []
    na = max(3, n - 2)
    for i in range(na):
        th = th0 + (tb - th0) * (i / (na - 1)) ** 0.9
        q = kop.haarpunt(th, ph, True, dik * 0.6)
        pad.append(q)
        nrm.append(straal(kop, q))
    rest = n - na
    p = pad[-1]
    uit = straal(kop, p)
    for j in range(1, rest + 1):
        u = j / rest
        d = np.array([0, 0, -1.0]) + uit * (0.35 - 0.3 * u + naar_voren)
        d = draai(d / np.linalg.norm(d), uit, buig * u)
        p = p + d * val * kk / rest
        pad.append(p)
        nrm.append(uit)
    fr = pluk_buis(B, np.array(pad), np.array(nrm), breed * kk, dik * kk, n=4, regio=1, tip=0.12, sk=sk,
                   strengen=strengen, licht=licht, rng=np.random.default_rng(seed))
    if kaart:
        kaart_over(B, sk, fr, kaart)
    return fr


def lok_tussen(B, sk, d_van, d_naar, breed, dik, n=8, strengen=7, licht=1.0, seed=0, regio=1, lift=0.6,
               tip=0.25, kaart=1.35, verleng=0.12):
    """Lok over de schil langs de grote cirkel tussen twee richtingen (scheiding -> zijkant, haargrens -> knot)."""
    kop = sk.kop
    kk = kop.k
    ds = boog(d_van, d_naar, n)
    pad = np.array([op_schil(kop, d, dik * kk * lift) for d in ds])
    nrm = np.array([straal(kop, q) for q in pad])
    fr = pluk_buis(B, pad, nrm, breed * kk, dik * kk, n=4, regio=regio, tip=tip, sk=sk, strengen=strengen,
                   licht=licht, rng=np.random.default_rng(seed))
    if kaart:
        kaart_over(B, sk, fr, kaart, verleng=verleng)
    return fr


def pluk_vrij(B, sk, pad, breed, dik, n=5, strengen=8, licht=1.0, seed=0, regio=1, tip=0.15, ref=None):
    """Vrij hangende of uitstekende pluk (staartje, piek): nrm = weg van de kop of ref."""
    kop = sk.kop
    pad = np.asarray(pad, float)
    nrm = np.array([straal(kop, q) if ref is None else ref for q in pad])
    return pluk_buis(B, pad, nrm, breed, dik, n=n, regio=regio, tip=tip, sk=sk, strengen=strengen, licht=licht,
                     rng=np.random.default_rng(seed))


def pieken(B, sk, n, seed=5, lengte=(0.03, 0.07), breed=(0.010, 0.016), zmin=1.08, boven=0.6, strengen=8,
           licht=(0.9, 1.1), gat=None, kaarten=False, voor=0.75):
    """Wilde plukken (oudere man): spitse plukken die schuin uit de zijkanten en de kruin steken."""
    kop = sk.kop
    kk = kop.k
    rng = np.random.default_rng(seed)
    gemaakt = 0
    while gemaakt < n:
        ph = rng.uniform(-np.pi, np.pi)
        if abs(ph) < voor:                                        # niet voor het gezicht
            continue
        th = rng.uniform(0.15, 1.9)
        q = kop.haarpunt(th, ph, False)
        if q[2] < kop.zz(zmin):
            continue
        if gat is not None and gat(th, ph):
            continue
        u = straal(kop, q)
        raak = np.cross(u, np.array([0, 0, 1.0]))
        raak = raak / (np.linalg.norm(raak) + 1e-9) * rng.choice((-1, 1))
        d = u * 0.8 + np.array([0, 0, boven]) * rng.uniform(0.2, 0.8) + raak * rng.uniform(0.2, 0.7) + \
            rng.normal(size=3) * 0.2
        d /= np.linalg.norm(d)
        L = rng.uniform(*lengte) * kk
        kr = (raak * 0.6 - u * 0.4 + np.array([0, 0, -0.5])) * rng.uniform(0.3, 0.7)
        pad = [q - u * 0.01 * kk] + [q + d * L * t + (kr * L * t * t) for t in np.linspace(0.2, 1.0, 4)]
        b_ = rng.uniform(*breed) * kk
        if kaarten:
            haarkaart(B, sk, pad, b_ * 1.3, nrm=[u] * len(pad), tip=0.35, kruis=True)
        else:
            pluk_vrij(B, sk, pad, b_, b_ * 0.45, n=5, strengen=strengen, licht=rng.uniform(*licht),
                      seed=int(rng.integers(1e6)), tip=0.22)
        gemaakt += 1


def knot_spiraal(B, sk, plek=(0, 0.118, 0.095), r=0.04, buis=0.017, slagen=1.7, n=6, strengen=14, licht=1.0):
    """Knot als opgerolde streng (oudere vrouw): spiraal naar binnen, as naar achteren (regio 2)."""
    kop = sk.kop
    kk = kop.k
    c = kop.C + np.array(plek) * kk
    as_ = np.array([0, 1.0, 0.25])
    as_ /= np.linalg.norm(as_)
    e1 = np.array([1.0, 0, 0])
    e2 = np.cross(as_, e1)
    m = int(slagen * 14)
    u = np.linspace(0, 1, m)
    ang = 2 * np.pi * slagen * u
    rr = r * kk * (1 - 0.65 * u)
    rad = np.cos(ang)[:, None] * e1 + np.sin(ang)[:, None] * e2
    pad = c[None] + rad * rr[:, None] + as_[None] * (0.012 * kk * u)[:, None]
    nrm = rad * 0.6 + as_ * 0.8
    pluk_buis(B, pad, nrm, buis * kk, buis * kk * 0.85, n=n, regio=2, tip=0.5, sk=sk, strengen=strengen,
              licht=licht, rng=np.random.default_rng(11))
    return c


def staart_plukken(B, sk, kop, lengte=1.0, plukken=3, strengen=10):
    """Staartjes (meisje) als drie losse plukken langs het pad van staartjes(), licht om elkaar gedraaid,
    met eigen strengen; zet sk.staart_aanzet voor de strikken."""
    kk = kop.k
    sk.staart_aanzet = {}
    rng = np.random.default_rng(21)
    for sx in (1, -1):
        p0 = kop.Ch + np.array([sx * 0.108, 0.02, 0.03]) * kk
        L = lengte
        pad = np.array([p0, p0 + np.array([sx * 0.035, 0.0, -0.008]) * kk, p0 + np.array([sx * 0.07, 0.01, -0.06 * L]) * kk,
                        p0 + np.array([sx * 0.08, 0.015, -0.13 * L]) * kk, p0 + np.array([sx * 0.062, 0.005, -0.2 * L]) * kk,
                        p0 + np.array([sx * 0.035, -0.01, -0.235 * L]) * kk])
        fr = keten(list(pad), list(np.linspace(0, sum(np.linalg.norm(np.diff(pad, axis=0), axis=1)), 9)), zacht=0.02)
        for j in range(plukken):
            a0 = 2 * np.pi * j / plukken + rng.uniform(-0.3, 0.3)
            pts, nrm = [], []
            for i, (pos, t, f, sd) in enumerate(fr):
                u = i / (len(fr) - 1)
                a_ = a0 + u * 2.2
                rr = (0.008 + 0.006 * math.sin(math.pi * min(1, u * 1.6))) * kk * (1 - 0.5 * u)
                off = (f * math.cos(a_) + sd * math.sin(a_)) * rr
                pts.append(pos + off)
                nrm.append(off / (np.linalg.norm(off) + 1e-9))
            fr_ = pluk_buis(B, np.array(pts), np.array(nrm), (0.03 - 0.004 * j) * kk, 0.02 * kk, n=6, regio=2, tip=0.15,
                            sk=sk, strengen=strengen, rng=np.random.default_rng(31 + j + (sx > 0) * 7))
            kaart_over(B, sk, fr_[2:], 1.25, verleng=0.3, lift=0.9)

        sk.staart_aanzet[sx] = (p0 + np.array([sx * 0.016, 0, -0.002]) * kk, pad[1] - p0)


def rond(richting, spreid=0.15):
    """Strengbegin/-eind: een richting met wat spreiding (voor schil_strengen)."""
    r0 = np.asarray(richting, float) / np.linalg.norm(richting)
    return lambda rng: r0 + rng.normal(size=3) * spreid


def naar_grens(kop, boven=0.0, phs=None):
    """Strengeinde op de haargrens (willekeurige hoek, of uit phs), `boven` (m) erboven."""
    def f(rng):
        ph = rng.uniform(-np.pi, np.pi) if phs is None else rng.uniform(*phs)
        tb = kop.theta_bij_z(ph, kop.haargrens(ph) + boven * kop.k, lambda t, p: kop.haarpunt(t, p, False))
        return straal(kop, kop.haarpunt(tb, ph, False))
    return f


def krul_kaarten(B, sk, n, seed=12, lengte=(0.022, 0.04), breed=(0.009, 0.014), tmin=0.15, zmin=None):
    """Korte gekruiste haarkaarten die schuin uit een krullenbol steken: het silhouet rafelt (geen kleibol)."""
    kop = sk.kop
    kk = kop.k
    rng = np.random.default_rng(seed)
    gemaakt = 0
    while gemaakt < n:
        ph = rng.uniform(-np.pi, np.pi)
        tb = kop.theta_bij_z(ph, kop.haargrens(ph), lambda t, p: kop.haarpunt(t, p, False))
        th = math.acos(rng.uniform(math.cos(tb), math.cos(tmin)))
        q = kop.haarpunt(th, ph, True)
        if zmin is not None and q[2] < kop.zz(zmin):
            continue
        u = straal(kop, q)
        neer = np.array([0, 0, -1.0]) - u[2] * u
        d = u * 0.7 + neer * 0.5 + rng.normal(size=3) * 0.25
        d /= np.linalg.norm(d)
        L = rng.uniform(*lengte) * kk
        kr = np.cross(u, d)
        kr /= np.linalg.norm(kr) + 1e-9
        pad = [q - u * 0.006 * kk + d * L * t + kr * 0.006 * kk * math.sin(t * 5.5) for t in np.linspace(0, 1, 4)]
        haarkaart(B, sk, pad, rng.uniform(*breed) * kk, nrm=[u] * 4, tip=0.5, kruis=True)
        gemaakt += 1
