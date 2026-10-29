"""Volwassen mannelijke bumpkin, game-ready (Blender 5.2 headless -> glb voor Godot 4).

Draaien:
  blender -b -P bumpkin_man.py -- [res=2048] [snel] [vergelijk] [poses] [geen_export] [ref=<map>]
- `snel`: bake op 512 met weinig samples.
- `vergelijk`: preview/man_vergelijk_1x.png (sprite naast render op HD-pixelschaal),
  preview/man_vergelijk_close.png en preview/man_detail.png. Bevatten de sprite: nooit committen.
- `poses`: preview/man_poses.png, extreme standen uit de rig-animaties (vervorming).
Doel: ref/gemini_man_v4.jpg (grijsgroen hemd, paarse tuinbroek, korte rode krullenbol, hangsnor).

Uitvoer bumpkin_man.glb: armatuur `bumpkin_rig` met alle acties, losse delen op hetzelfde skelet,
een gedeelde atlas in textures_man/ (man_kleur.jpg, man_normaal.png, man_orm.png; R=AO G=ruw B=metaal).

DELEN (mesh-object = glTF-node, stabiele namen; elk deel los te vervangen door een outfit/kapsel):
| deel          | inhoud                                        | materiaal       | tint (baseColorFactor) |
| ------------- | --------------------------------------------- | --------------- | ---------------------- |
| lijf          | hoofd, nek, handen (huid); oogjes = vast       | mat_lijf + vast | #e79c65 huid           |
| haar          | krullenbol                                    | mat_haar        | #b15830 roodbruin      |
| snor          | hangsnor (zelfde materiaal als haar)          | mat_haar        | #b15830                |
| hemd          | grijsgroen werkhemd, lange mouwen, open kraag | mat_hemd        | #97a288 grijsgroen     |
| tuinbroek     | pijpen, heupstuk, slab, rugpand, bretels      | mat_tuinbroek   | #833d92 paars          |
|               | bretelgespen = vast                           | + mat_vast      |                        |
| riem          | riem en gele gesp                             | mat_vast        | wit (echte kleur)      |
| laarzen       | omgeslagen leren laarzen                      | mat_laarzen     | #543017 bruin          |
| prop_strootje | strohalm, kind van bot Head                   | strootje        | vast #d4ad55           |
Tintbare delen: de kleurtextuur is lichtgrijs (gemiddeld ~0,86) met alle detail als luminantie
(plus een beetje relatieve tint, bv. rode wangen, vuil); kleur = baseColorFactor x textuur. In Godot
per eenheid albedo_color (of een instance-parameter) zetten; geen nieuwe texturen nodig.
mat_vast heeft factor wit en draagt echte kleuren (gesp geel, metaal, oogwit/iris).
Plus de props van de rig (prop_hamer/zwaard/steen) op prop_R, zodat bumpkin.gd ze vindt.

Bouw: elk deel is een loft van ringen langs de gewrichten van het skelet uit bumpkin_rig.py (rust =
A-pose), dus de mesh volgt de rustpose en de `maat` van de rig (kind en oudere later via MAAT_MAN).
Gewichten zijn analytisch: per deel een keten van botten met lineaire overgangen rond elk gewricht.
Hoog-poly = de lage mesh gesubdivideerd met plooien/kreukels (numpy) plus krulspiralen; daarvan bakt
Cycles normaal, AO en krulkleur. Weefsel, naden, steken, zakken, leer en gezicht komen er in numpy bij,
per texel uit een gebakken positie- en UV(m)-kaart.
"""
import math
import os
import sys
import time

import bmesh
import bpy
import numpy as np
from mathutils import Euler, Vector

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import bumpkin_rig as R  # noqa: E402

argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
OPTS = {a.split("=")[0]: (a.split("=", 1)[1] if "=" in a else "1") for a in argv}
SNEL = "snel" in OPTS
VLAK = "vlak" in OPTS
RES = int(OPTS.get("res", 512 if SNEL else 2048))
SPP = 0.25 if SNEL else 1.0
TEX = os.path.join(HERE, "textures_man")
PREV = os.path.join(HERE, "preview")
GLB = os.path.join(HERE, "bumpkin_man.glb")
MOD = os.path.dirname(HERE)
REF = OPTS.get("ref", os.path.join(os.environ.get("TEMP", ""), "claude", "E--werk-androidApps-Apps",
                                   "16e99493-ac86-47c7-921f-1d215c266f51", "scratchpad", "bumpkin", "ref"))
T0 = time.time()

# Maat voor de rig: smallere schouders dan de rig-standaard (0,40 tussen de gewrichten maakt de jas
# 0,52 breed; de sprite is ~0,40 over de jas).
MAAT_MAN = {"schouder": 0.31}
MAAT_MAN.update({k: float(v) for k, v in OPTS.items() if k in ("hoogte", "kop", "schouder", "been")})
DELEN = ["lijf", "haar", "snor", "hemd", "tuinbroek", "riem", "laarzen"]
TINTBAAR = {"lijf": "huid", "haar": "haar", "snor": "haar", "hemd": "hemd", "tuinbroek": "paars", "laarzen": "laars"}
GRIJS = 0.86                       # gemiddelde luminantie van een tintbare textuur; tint = kleur / GRIJS
VAST = {"lijf": (3,), "tuinbroek": (6,), "riem": (0, 1)}     # regio's met echte kleur (mat_vast)
TEXEL = {"lijf": 1.9, "haar": 1.2, "snor": 1.9, "hemd": 1.0, "tuinbroek": 1.0, "riem": 1.0, "laarzen": 1.1}
TEXEL_REGIO = {("lijf", 2): 1.4 / 1.9, ("lijf", 4): 1.4 / 1.9, ("lijf", 5): 0.6 / 1.9}


def log(*a):
    print(f"[man {time.time() - T0:6.1f}s]", *a, flush=True)


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


# --- Ruis (numpy, 3D waarde-ruis) -------------------------------------------------------------
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
class Skelet:
    """Gewrichtsposities (rust, armatuurruimte) uit de rig, plus de afgeleide maten van de mesh."""

    def __init__(self, rig):
        bn = rig.data.bones
        self.J = {b.name: np.array(b.head_local) for b in bn}
        self.T = {b.name: np.array(b.tail_local) for b in bn}
        for k in ("Left", "Right"):
            self.J[k + "HandEnd"] = np.array(bn[k + "HandFist"].tail_local)
        self.H = float(rig.get("hoogte", 1.37))
        self.s = self.H / 1.37
        self.hz = self.J["LeftUpLeg"][2]                      # heupgewricht
        self.nz = self.J["Neck"][2]                           # nekbasis
        self.kz = self.J["Head"][2]                           # kopbasis
        self.kh = (self.H - self.kz) / 0.37                   # kopschaal t.o.v. de volwassen 0,37 m

    def z(self, z0):
        """Romphoogte uit de volwassen referentie (heup 0,644, nek 0,965) naar deze rig."""
        if z0 >= 0.965:
            return self.nz + (z0 - 0.965) * self.kh
        return self.hz + (z0 - 0.644) * (self.nz - self.hz) / (0.965 - 0.644)


# --- Mesh-bouwer ---------------------------------------------------------------------------------
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


def keten(punten, afstanden, ref=(0, -1, 0), zacht=0.05):
    """Posities en frames langs een polylijn op afstanden (m) vanaf punt 0 (negatief = ervoor)."""
    P = [np.array(p, float) for p in punten]
    seg = [P[i + 1] - P[i] for i in range(len(P) - 1)]
    L = [np.linalg.norm(s) for s in seg]
    D = [s / l for s, l in zip(seg, L)]
    cum = np.concatenate([[0], np.cumsum(L)])
    uit = []
    for d in afstanden:
        i = int(np.clip(np.searchsorted(cum, d, side="right") - 1, 0, len(seg) - 1))
        pos = P[i] + D[i] * (d - cum[i])
        t = D[i].copy()
        for j in range(1, len(P) - 1):                      # ring op de bissectrice rond gewrichten
            w = 1 - min(1, abs(d - cum[j]) / zacht)
            if w > 0:
                t = t * (1 - w) + (D[j - 1] + D[j]) * 0.5 * w
        t /= np.linalg.norm(t)
        r = np.array(ref, float)
        f = r - np.dot(r, t) * t
        f /= np.linalg.norm(f)
        s = np.cross(t, f)
        uit.append((pos, t, f, s))
    return uit


def keten_param(P, punten):
    """Per punt: afstand langs de polylijn (dichtstbijzijnde segment) en de radiale vector."""
    P = np.asarray(P, float)
    best = np.full(len(P), 1e9)
    d_uit = np.zeros(len(P))
    r_uit = np.zeros_like(P)
    cum = 0.0
    for a, b in zip(punten[:-1], punten[1:]):
        a, b = np.asarray(a, float), np.asarray(b, float)
        ab = b - a
        L = np.linalg.norm(ab)
        t = np.clip((P - a) @ ab / L ** 2, 0, 1)
        q = a + t[:, None] * ab
        r = P - q
        dd = np.linalg.norm(r, axis=1)
        m = dd < best
        best[m] = dd[m]
        d_uit[m] = cum + t[m] * L
        r_uit[m] = r[m]
        cum += L
    return d_uit, r_uit


# --- Kop ----------------------------------------------------------------------------------------
class Kop:
    """Schedel op ware grootte (gezicht volgens het portret), het volume komt van de krullenbol."""

    def __init__(self, sk):
        self.k = k = sk.kh
        self.kz = sk.kz
        self.C = np.array([0, -0.004 * k, self.zz(1.118)])
        self.a, self.b, self.top, self.bot = 0.098 * k, 0.113 * k, 0.128 * k, 0.122 * k
        self.ogen = [self.punt(self.theta_bij_z(ph, self.zz(1.118)), ph, 0.0) for ph in (0.42, -0.42)]
        self.mond = self.punt(self.theta_bij_z(0.0, self.zz(1.038)), 0.0, 0.0)
        self.neus = self.C + np.array([0, -0.102, -0.036]) * k
        # krullenbol: ellipsoide boven/achter de schedel, klonten op een vaste set richtingen
        self.Ch = np.array([0, 0.012 * k, self.zz(1.175)])
        self.hr = dict(x=0.156 * k, yv=0.13 * k, ya=0.148 * k, zt=0.145 * k, zo=0.165 * k)
        rng = np.random.default_rng(5)
        d = rng.normal(size=(260, 3))
        self.klontdir = d / np.linalg.norm(d, axis=1, keepdims=True)
        self.klontw = rng.uniform(0.55, 1.0, 260)

    def zz(self, z0):
        return self.kz + (z0 - 1.0) * self.k

    @staticmethod
    def richting(tht, ph):
        return np.array([math.sin(tht) * math.sin(ph), -math.sin(tht) * math.cos(ph), math.cos(tht)])

    def punt(self, tht, ph, extra=0.0):
        """Punt op de schedel: polair tht vanaf de kruin, ph om z (0 = voor, -Y; +ph = naar +X)."""
        d = self.richting(tht, ph)
        cz = self.top if d[2] > 0 else self.bot
        r = 1 / math.sqrt((d[0] / self.a) ** 2 + (d[1] / self.b) ** 2 + (d[2] / cz) ** 2)
        p = d * r
        if p[2] < 0:                                              # zware wangen, brede kaak
            q = (-p[2] / self.bot) ** 2
            p[0] *= 1 + 0.06 * q - 0.22 * q * q
            p[1] = p[1] * (1 - 0.15 * q) - 0.01 * self.k * q
        if p[1] < 0:                                              # gezicht platter
            p[1] *= 0.9 + 0.1 * min(1, (abs(p[0]) / (0.08 * self.k))) ** 2
        if extra:
            p = p + d * extra
        return self.C + p

    def theta_bij_z(self, ph, z, f=None):
        f = f or self.punt
        lo, hi = 0.0, np.pi
        for _ in range(40):
            m = (lo + hi) / 2
            if f(m, ph)[2] > z:
                lo = m
            else:
                hi = m
        return (lo + hi) / 2

    def klont(self, d):
        """0..1: hoeveel krulklont er in richting d zit (bloemkoolsilhouet)."""
        c = self.klontdir @ d
        return float(np.clip(np.max(self.klontw * np.exp(-(1 - c) / 0.016)), 0, 1))

    def haarpunt(self, tht, ph, klont=True, extra=0.0):
        d = self.richting(tht, ph)
        h = self.hr
        ry = h["ya"] if d[1] > 0 else h["yv"]
        rz = h["zt"] if d[2] > 0 else h["zo"]
        r = 1 / math.sqrt((d[0] / h["x"]) ** 2 + (d[1] / ry) ** 2 + (d[2] / rz) ** 2)
        if klont:
            r *= 1 + 0.13 * self.klont(d) - 0.05
        return self.Ch + d * (r + extra)

    def haargrens(self, ph):
        """Onderrand van de bol per hoek: haarlijn voor, oren bedekt, nek achter."""
        a = abs((ph + np.pi) % (2 * np.pi) - np.pi)
        pts = [(0.0, 1.16), (0.55, 1.156), (0.95, 1.136), (1.3, 1.11), (1.6, 1.1), (2.2, 1.08),
               (np.pi, 1.07)]
        xs, ys = zip(*pts)
        return self.zz(float(np.interp(a, xs, ys)))


# --- Delen ---------------------------------------------------------------------------------------
def bouw_delen(sk, coll):
    delen = {}
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
    delen["hemd"] = B.obj("hemd", coll)

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
    delen["tuinbroek"] = B.obj("tuinbroek", coll)

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
    delen["riem"] = B.obj("riem", coll)

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
    delen["laarzen"] = B.obj("laarzen", coll)

    # handen: wanten met duim, langs onderarm-pols-vingertop
    B = Bouwer()
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

    # hoofd: schedel op ware maat, knolneus, hangsnor (regio 2)
    kop = Kop(sk)
    kk = kop.k
    nphi, nth = 24, 14
    rows = [[kop.punt(np.pi * (0.05 + 0.9 * i / nth), ph) for ph in 2 * np.pi * np.arange(nphi) / nphi]
            for i in range(nth + 1)]
    b0, _ = B.grid(np.array(rows), True, regio=0)
    B.kap(b0, nphi, kop.punt(0, 0), regio=0)
    B.kap(b0 + nphi * nth, nphi, kop.punt(np.pi, 0), regio=0)
    nc = kop.neus
    nr = [ring(nc + np.array([0, dy, z]) * kk, (1, 0, 0), (0, -1, 0), a * kk, b * kk, 10)
          for z, a, b, dy in ((0.03, 0.011, 0.01, 0.014), (0.012, 0.016, 0.018, 0.0), (-0.006, 0.026, 0.026, -0.008),
                              (-0.02, 0.027, 0.026, -0.01), (-0.032, 0.019, 0.016, 0.0))]
    b0, _ = B.grid(np.array(nr), True, regio=1)
    B.kap(b0 + 40, 10, nc + np.array([0, 0.006, -0.036]) * kk, regio=1)
    # oogjes: amandelvormige schijfjes net voor de huid (vaste kleur: oogwit en iris niet tinten)
    for oog in kop.ogen:
        nrm = (oog - kop.C) / np.linalg.norm(oog - kop.C)
        sd = np.cross((0, 0, 1.0), nrm)
        sd /= np.linalg.norm(sd)
        up = np.cross(nrm, sd)
        rand_ = []
        for tt in np.linspace(0, 2 * np.pi, 13)[:-1]:
            x = 0.0128 * kk * math.cos(tt)
            zz = (0.0012 if math.sin(tt) > 0 else 0.0068) * kk * math.sin(tt) - 0.0005 * kk
            q = oog + sd * x + up * zz
            dq = (q - kop.C) / np.linalg.norm(q - kop.C)
            ph = math.atan2(dq[0], -dq[1])
            th = math.acos(np.clip(dq[2], -1, 1))
            rand_.append(kop.punt(th, ph, 0.0007 * kk))
        b0 = B.verts(rand_)
        mid = np.mean(rand_, 0) + nrm * 0.0004 * kk
        B.kap(b0, 12, mid, regio=3, buiten=nrm)
    # nek en bovenborst onder het hemd (huid in de V)
    nk = [(0.905, 0.108, 0.08), (0.94, 0.1, 0.076), (0.975, 0.078, 0.07), (1.0, 0.068, 0.066),
          (1.03, 0.052, 0.052), (1.07, 0.049, 0.049)]
    rings = [ring((0, 0.006 * s, Z(z)), (1, 0, 0), (0, -1, 0), a * s, b * s, 14, 2.2, fase=-np.pi / 2) for z, a, b in nk]
    B.grid(np.array(rings), True, regio=5)
    delen["lijf"] = B.obj("lijf", coll)

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
    delen["snor"] = B.obj("snor", coll)

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
            if w > 0:
                d = (q - kop.C) / np.linalg.norm(q - kop.C)
                sch = kop.punt(math.acos(np.clip(d[2], -1, 1)), math.atan2(d[0], -d[1]), 0.016 * kk)
                q = q * (1 - w) + sch * w
            rows[i].append(q)
        rand = rows[nrow][-1]
        hl = kop.punt(kop.theta_bij_z(ph, zb + 0.004 * kk), ph, 0.004 * kk)
        rows[nrow + 1].append(rand * 0.45 + hl * 0.55 + np.array([0, 0, 0.012 * kk]))
        rows[nrow + 2].append(hl)
    b0, _ = B.grid(np.array(rows), True, regio=0)
    B.kap(b0, nphi, kop.haarpunt(0, 0), regio=0)
    delen["haar"] = B.obj("haar", coll)

    sk.kop = kop
    return delen


# --- Gewichten (analytisch) ----------------------------------------------------------------------
def overgang(x, grenzen, breedtes):
    """Gewichten (n, k+1) voor k grenzen langs x: lineaire overgang van breedte b rond elke grens."""
    n = len(grenzen) + 1
    W = np.zeros((len(x), n))
    vorig = np.ones(len(x))
    for i, (g, b) in enumerate(zip(grenzen, breedtes)):
        t = np.clip((x - (g - b / 2)) / b, 0, 1)
        W[:, i] = vorig * (1 - t) if i == 0 else W[:, i] * 0 + (vorig - 0) * (1 - t)
        vorig = t
        if i == 0:
            W[:, 0] = 1 - t
        else:
            W[:, i] = prev_t - 0 if False else W[:, i]
    # eenvoudiger: berekenen als verschillen van opgaande trappen
    T = [np.clip((x - (g - b / 2)) / b, 0, 1) for g, b in zip(grenzen, breedtes)]
    W[:, 0] = 1 - T[0]
    for i in range(1, n - 1):
        W[:, i] = T[i - 1] - T[i]
    W[:, n - 1] = T[-1]
    return np.clip(W, 0, 1)


def gewichten(o, sk, naam):
    """Zet vertexgroepen op o (rust) volgens de regels per deel. Geeft {bot: gewichten}."""
    me = o.data
    P = np.zeros(len(me.vertices) * 3)
    me.vertices.foreach_get("co", P)
    P = P.reshape(-1, 3)
    N = len(P)
    J = sk.J
    G = {}

    def voeg(bot, w):
        G[bot] = G.get(bot, np.zeros(N)) + w

    zj = [J[b][2] for b in ("Hips", "Spine", "Spine1", "Spine2", "Neck", "Head")]
    romp = ["Hips", "Spine", "Spine1", "Spine2", "Neck", "Head"]
    s = sk.s

    def romp_gewicht(mask, x=P[:, 2]):
        W = overgang(x, zj[1:], [0.05 * s, 0.06 * s, 0.06 * s, 0.04 * s, 0.03 * s])
        for i, b in enumerate(romp):
            voeg(b, W[:, i] * mask)

    if naam in ("haar", "snor"):
        voeg("Head", np.ones(N))
    elif naam == "riem":
        romp_gewicht(np.ones(N))
    elif naam == "tuinbroek":
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
    elif naam == "hemd":
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
    elif naam == "laarzen":
        for k, sx in (("Left", 1), ("Right", -1)):
            m = (sx * P[:, 0] > 0).astype(float)
            teen = gladstap(J[k + "ToeBase"][1] + 0.025 * s, J[k + "ToeBase"][1] - 0.015 * s, P[:, 1]) * \
                gladstap(0.09 * s, 0.05 * s, P[:, 2])
            schacht = gladstap(0.09 * s, 0.2 * s, P[:, 2]) * 0.85
            voeg(k + "Leg", schacht * m)
            voeg(k + "ToeBase", (1 - schacht) * teen * m)
            voeg(k + "Foot", (1 - schacht) * (1 - teen) * m)
    elif naam == "lijf":
        reg = vertex_regio(me)
        kopm = np.isin(reg, (0, 1, 3)).astype(float)
        t = gladstap(sk.kz - 0.01 * s, sk.kz + 0.035 * s, P[:, 2])
        voeg("Head", t * kopm)
        voeg("Neck", (1 - t) * kopm)
        romp_gewicht((reg == 5).astype(float))
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
    # normaliseren, max 4 invloeden, kleine weg
    botten = list(G)
    W = np.stack([G[b] for b in botten], 1)
    W[W < 0.01] = 0
    if W.shape[1] > 4:
        orde = np.argsort(-W, 1)
        W2 = np.zeros_like(W)
        rows = np.arange(N)[:, None]
        W2[rows, orde[:, :4]] = W[rows, orde[:, :4]]
        W = W2
    som = W.sum(1, keepdims=True)
    leeg = som[:, 0] < 1e-6
    if leeg.any():
        log("  let op:", naam, int(leeg.sum()), "vertices zonder gewicht")
    W = W / np.maximum(som, 1e-6)
    for i, b in enumerate(botten):
        vg = o.vertex_groups.get(b) or o.vertex_groups.new(name=b)
        for vi in np.nonzero(W[:, i] > 0)[0]:
            vg.add([int(vi)], float(W[vi, i]), "REPLACE")


def vertex_regio(me):
    reg = np.zeros(len(me.polygons), np.int32)
    me.attributes["regio"].data.foreach_get("value", reg)
    vr = np.zeros(len(me.vertices), np.int32)
    for p, r in zip(me.polygons, reg):
        for vi in p.vertices:
            vr[vi] = max(vr[vi], r)
    return vr


# --- Hoog-poly: subdivisie + plooien, haarlokken -----------------------------------------------
def vert_np(me):
    P = np.zeros(len(me.vertices) * 3)
    me.vertices.foreach_get("co", P)
    Nn = np.zeros(len(me.vertices) * 3)
    me.vertex_normals.foreach_get("vector", Nn)
    return P.reshape(-1, 3), Nn.reshape(-1, 3)


def hoog(o, sk, coll):
    naam = o.name
    h = o.copy()
    h.data = o.data.copy()
    h.name = naam + "_hoog"
    coll.objects.link(h)
    for vg in list(h.vertex_groups):
        h.vertex_groups.remove(vg)
    m = h.modifiers.new("sub", "SUBSURF")
    m.levels = m.render_levels = 3 if naam in ("lijf", "snor") else 2
    m.uv_smooth = "PRESERVE_BOUNDARIES"
    if naam in ("hemd", "tuinbroek", "laarzen", "riem"):
        m.subdivision_type = "SIMPLE"                             # dunne randen en omslagen niet laten inzakken
    ontkies()
    bpy.context.view_layer.objects.active = h
    h.select_set(True)
    bpy.ops.object.modifier_apply(modifier="sub")
    me = h.data
    P, Nn = vert_np(me)
    reg = vertex_regio(me)
    J = sk.J
    s = sk.s
    hgt = np.zeros(len(P))
    if naam == "hemd":
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
    elif naam == "tuinbroek":
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
    elif naam == "laarzen":
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
    elif naam == "snor":
        kk = sk.kop.k
        hgt += 0.0011 * kk * np.sin(2 * np.pi * (P[:, 2] + 0.55 * np.abs(P[:, 0])) / (0.0032 * kk)
                                    + 2 * ruis(P, 150, 42)) + 0.0015 * kk * ruis(P, 60, 43)
    elif naam == "lijf":
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
    elif naam == "haar":
        hgt += 0.006 * s * (0.5 - np.abs(ruis(P, 32, 61, 2))) + 0.002 * s * ruis(P, 90, 62)
    P = P + Nn * hgt[:, None]
    me.vertices.foreach_set("co", P.ravel())
    me.update()
    return h


def krullen(sk, coll, n=2600):
    """Krullen als kleine spiraalbuisjes, half in het oppervlak van de bol: normaal- en kleurdetail."""
    kop = sk.kop
    kk = kop.k
    rng = np.random.default_rng(9)
    V, F, C = [], [], []
    sides, seg = 4, 18
    tb_cache = {}
    for _ in range(n):
        ph = rng.uniform(0, 2 * np.pi)
        key = round(ph, 2)
        if key not in tb_cache:
            tb_cache[key] = kop.theta_bij_z(ph, kop.haargrens(ph), lambda t, p: kop.haarpunt(t, p, False))
        tb = tb_cache[key]
        tht = math.acos(rng.uniform(math.cos(tb), math.cos(0.02)))       # gelijk over het oppervlak
        p0 = kop.haarpunt(tht, ph)
        e = 0.01
        dt = kop.haarpunt(tht + e, ph) - kop.haarpunt(tht - e, ph)
        dp = kop.haarpunt(tht, ph + e) - kop.haarpunt(tht, ph - e)
        nrm = np.cross(dt, dp)
        nrm /= np.linalg.norm(nrm) + 1e-9
        if np.dot(nrm, p0 - kop.Ch) < 0:
            nrm = -nrm
        a = rng.normal(size=3)
        a -= np.dot(a, nrm) * nrm
        a /= np.linalg.norm(a)
        e2 = np.cross(a, nrm)
        L = rng.uniform(0.016, 0.03) * kk
        rc = rng.uniform(0.0045, 0.0075) * kk
        rt = rng.uniform(0.0016, 0.0024) * kk
        tw = rng.uniform(1.6, 2.8)
        fase = rng.uniform(0, 2 * np.pi)
        u = np.linspace(0, 1, seg)
        ang = fase + 2 * np.pi * tw * u
        pad = p0 + nrm * rc * 0.35 + a * (u - 0.5)[:, None] * L + \
            (np.cos(ang)[:, None] * nrm + np.sin(ang)[:, None] * e2) * rc
        licht = rng.uniform(0.9, 1.6)
        warm = rng.uniform(-0.1, 0.16)
        kl = np.clip(KLEUR["haar"] * licht * np.array([1 + warm * 0.3, 1 + warm, 1 - warm * 0.6]), 0, 1)
        b0 = len(V)
        for i in range(seg):
            t = pad[min(i + 1, seg - 1)] - pad[max(i - 1, 0)]
            t /= np.linalg.norm(t) + 1e-9
            up = np.cross(t, a)
            if np.linalg.norm(up) < 1e-4:
                up = nrm
            up /= np.linalg.norm(up)
            sd = np.cross(t, up)
            for k in range(sides):
                an = 2 * np.pi * k / sides
                V.append(pad[i] + (np.cos(an) * sd + np.sin(an) * up) * rt)
                C.append(kl)
        for i in range(seg - 1):
            for k in range(sides):
                k1 = (k + 1) % sides
                F.append((b0 + i * sides + k, b0 + i * sides + k1, b0 + (i + 1) * sides + k1, b0 + (i + 1) * sides + k))
    me = bpy.data.meshes.new("krullen")
    me.from_pydata([tuple(p) for p in V], [], F)
    me.update()
    at = me.attributes.new("kleur", "FLOAT_COLOR", "POINT")
    Cc = np.concatenate([np.array(C), np.ones((len(C), 1))], 1)
    at.data.foreach_set("color", Cc.ravel().astype(np.float32))
    me.shade_smooth()
    o = bpy.data.objects.new("haar_krullen", me)
    coll.objects.link(o)
    log("  krullen", n, "spiralen,", len(F) * 2, "driehoeken")
    return o


def zet_kleur_attr(o, kleur):
    me = o.data
    a = me.attributes.get("kleur") or me.attributes.new("kleur", "FLOAT_COLOR", "POINT")
    a.data.foreach_set("color", np.tile(np.array([*kleur, 1.0], np.float32), len(me.vertices)))


# --- Bakken ----------------------------------------------------------------------------------------
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
    for o in bpy.context.view_layer.objects:
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


def bak_mat(naam, soort):
    """Materiaal voor de bake: 'kleur' (hoog: Base Color = attribuut kleur), 'pos'/'uvm' (laag: emissie)."""
    m = bpy.data.materials.new(naam)
    m.use_nodes = True
    nt = m.node_tree
    bs = nt.nodes["Principled BSDF"]
    out = nt.nodes["Material Output"]
    if soort == "kleur":
        at = nt.nodes.new("ShaderNodeAttribute")
        at.attribute_name = "kleur"
        nt.links.new(at.outputs["Color"], bs.inputs["Base Color"])
        bs.inputs["Roughness"].default_value = 0.8
    else:
        em = nt.nodes.new("ShaderNodeEmission")
        if soort == "pos":
            g = nt.nodes.new("ShaderNodeNewGeometry")
            nt.links.new(g.outputs["Position"], em.inputs["Color"])
        else:
            uv = nt.nodes.new("ShaderNodeUVMap")
            uv.uv_map = "UVm"
            sep = nt.nodes.new("ShaderNodeSeparateXYZ")
            nt.links.new(uv.outputs["UV"], sep.inputs[0])
            at = nt.nodes.new("ShaderNodeAttribute")
            at.attribute_name = "deel"
            cb = nt.nodes.new("ShaderNodeCombineXYZ")
            nt.links.new(sep.outputs[0], cb.inputs[0])
            nt.links.new(sep.outputs[1], cb.inputs[1])
            nt.links.new(at.outputs["Fac"], cb.inputs[2])
            nt.links.new(cb.outputs[0], em.inputs["Color"])
        nt.links.new(em.outputs[0], out.inputs["Surface"])
    tn = nt.nodes.new("ShaderNodeTexImage")
    nt.nodes.active = tn
    return m


def bak(doel, highs, soort, img, ext=0.012, ray=0.03, margin=4, clear=False):
    sc = bpy.context.scene
    m = doel.data.materials[0]
    tn = m.node_tree.nodes.active
    tn.image = img
    ontkies()
    for h in highs:
        h.select_set(True)
    doel.select_set(True)
    bpy.context.view_layer.objects.active = doel
    kw = dict(use_clear=clear, margin=margin, margin_type="EXTEND", target="IMAGE_TEXTURES")
    if soort in ("pos", "uvm"):
        sc.cycles.samples = 1
        kw.update(type="EMIT", use_selected_to_active=False)
    else:
        kw.update(use_selected_to_active=True, cage_extrusion=ext, max_ray_distance=ray)
        if soort == "normaal":
            sc.cycles.samples = max(1, int(16 * SPP))
            kw.update(type="NORMAL", normal_space="TANGENT", normal_r="POS_X", normal_g="POS_Y", normal_b="POS_Z")
        elif soort == "ao":
            sc.cycles.samples = max(4, int(128 * SPP))
            kw.update(type="AO")
        elif soort == "kleur":
            sc.cycles.samples = max(1, int(16 * SPP))
            kw.update(type="DIFFUSE", pass_filter={"COLOR"})
    bpy.ops.object.bake(**kw)


def atlas(delen):
    """UVMap = UVm x texeldichtheid per deel, samen gepakt (zonder draaien: weefsel blijft recht)."""
    ontkies()
    for naam, o in delen.items():
        me = o.data
        uvm = np.zeros(len(me.loops) * 2, np.float32)
        me.uv_layers["UVm"].data.foreach_get("uv", uvm)
        lay = me.uv_layers.get("UVMap") or me.uv_layers.new(name="UVMap")
        reg = np.zeros(len(me.polygons), np.int32)
        me.attributes["regio"].data.foreach_get("value", reg)
        fac = np.array([TEXEL_REGIO.get((naam, int(r)), 1.0) for r in reg]) * TEXEL[naam]
        tot = np.zeros(len(me.polygons), np.int32)
        me.polygons.foreach_get("loop_total", tot)
        lay.data.foreach_set("uv", (uvm.reshape(-1, 2) * np.repeat(fac, tot)[:, None]).astype(np.float32).ravel())
        me.uv_layers.active = lay
        lay.active_render = True
        o.select_set(True)
    bpy.context.view_layer.objects.active = delen["lijf"]
    bpy.ops.object.mode_set(mode="EDIT")
    bpy.ops.mesh.select_all(action="SELECT")
    bpy.ops.uv.select_all(action="SELECT")
    bpy.ops.uv.pack_islands(rotate=False, margin=0.006, scale=True, shape_method="CONCAVE")
    bpy.ops.object.mode_set(mode="OBJECT")
    # meter per texel per deel (voor het reliëf): wortel van de oppervlakteverhouding UVm / UVMap
    def opp(lay, me):
        a_ = np.zeros(len(me.loops) * 2, np.float32)
        me.uv_layers[lay].data.foreach_get("uv", a_)
        a_ = a_.reshape(-1, 2).astype(np.float64)
        tot = 0.0
        for p in me.polygons:
            q = a_[p.loop_start:p.loop_start + p.loop_total]
            tot += 0.5 * abs(np.dot(q[:, 0], np.roll(q[:, 1], -1)) - np.dot(q[:, 1], np.roll(q[:, 0], -1)))
        return tot
    mpp = {}
    for naam, o in delen.items():
        mpp[naam] = math.sqrt(opp("UVm", o.data) / max(opp("UVMap", o.data), 1e-12)) / RES
    return mpp


def bak_alles(delen, sk, coll):
    sc = bpy.context.scene
    sc.render.engine = "CYCLES"
    log("cycles op", gpu(sc))
    sc.render.bake.use_selected_to_active = True
    sc.world = sc.world or bpy.data.worlds.new("w")
    sc.world.light_settings.distance = 0.12 * sk.s
    mpp = atlas(delen)
    log("atlas, m/texel", {k: round(v * 1000, 2) for k, v in mpp.items()})
    # hoog-poly
    highs = {}
    for naam, o in delen.items():
        h = hoog(o, sk, coll)
        zet_kleur_attr(h, KLEUR["haar"] * 0.85 if naam == "haar" else KLEUR["hemd"])
        highs[naam] = [h]
    highs["haar"].append(krullen(sk, coll, 1500 if SNEL else 4200))
    km = bak_mat("_bak_kleur", "kleur")
    for hs in highs.values():
        for h in hs:
            h.data.materials.clear()
            h.data.materials.append(km)
    beelden = {k: beeld("_" + k, RES) for k in ("pos", "uvm", "normaal", "ao", "kleur")}
    for i, (naam, o) in enumerate(delen.items()):
        t1 = time.time()
        me = o.data
        at = me.attributes.get("deel") or me.attributes.new("deel", "FLOAT", "FACE")
        reg = np.zeros(len(me.polygons), np.int32)
        me.attributes["regio"].data.foreach_get("value", reg)
        at.data.foreach_set("value", ((DELEN.index(naam) * 8 + reg + 1) / 128.0).astype(np.float32))
        oud = list(me.materials)
        for o2 in delen.values():
            o2.hide_render = o2 is not o
        o.visible_diffuse = o.visible_glossy = o.visible_shadow = o.visible_transmission = False
        for soort in ("pos", "uvm"):
            me.materials.clear()
            me.materials.append(bak_mat("_" + soort, soort))
            bak(o, [], soort, beelden[soort], margin=0, clear=(i == 0))
        me.materials.clear()
        me.materials.append(bak_mat("_doel", "uvm"))
        hs = highs[naam]
        ext, ray = {"haar": (0.024, 0.05), "laarzen": (0.005, 0.02), "hemd": (0.005, 0.018), "riem": (0.004, 0.015),
                    "tuinbroek": (0.004, 0.015), "lijf": (0.008, 0.025), "snor": (0.006, 0.02)}.get(naam, (0.01, 0.03))
        bak(o, hs, "normaal", beelden["normaal"], ext, ray, clear=(i == 0))
        bak(o, hs, "ao", beelden["ao"], ext, ray, clear=(i == 0))
        if naam == "haar" or i == 0:
            bak(o, hs, "kleur", beelden["kleur"], ext, ray, clear=(i == 0))
        me.materials.clear()
        for m in oud:
            me.materials.append(m)
        log("  bak", naam, f"{time.time() - t1:.1f}s")
    for o2 in delen.values():
        o2.hide_render = False
        o2.visible_diffuse = o2.visible_glossy = o2.visible_shadow = o2.visible_transmission = True
    for hs in highs.values():
        for h in hs:
            bpy.data.objects.remove(h)
    return {k: pixels(v) for k, v in beelden.items()}, mpp


# --- Texturen in numpy ---------------------------------------------------------------------------
def steek(x, periode, lengte):
    """1 op een steek, 0 in het gat: gestippelde lijn langs x."""
    return (np.mod(x, periode) < lengte).astype(np.float32)


def componeer(B, mpp, sk):
    """Kleur (lineair), hoogte (m), ruwheid, metaal per texel uit de gebakken kaarten."""
    pos, uvm = B["pos"], B["uvm"]
    idf = np.round(uvm[..., 2] * 128 - 1).astype(np.int32)
    dekking = idf >= 0
    ys, xs = np.nonzero(dekking)
    P = pos[ys, xs, :3].astype(np.float64)
    U = uvm[ys, xs, 0].astype(np.float64)
    V = uvm[ys, xs, 1].astype(np.float64)
    ids = idf[ys, xs]
    deel = ids // 8
    reg = ids % 8
    n = len(P)
    s = sk.s
    J = sk.J
    kl = np.zeros((n, 3))
    H = np.zeros(n)
    ruw = np.full(n, 0.85)
    met = np.zeros(n)
    D = {k: deel == DELEN.index(k) for k in DELEN}
    z = P[:, 2]

    def zet(m, c):
        kl[m] = c[m] if np.ndim(c) == 2 else c

    wf = float(np.clip((0.005 / np.mean([mpp["hemd"], mpp["tuinbroek"]]) - 2.5) / 2, 0, 1))
    # stof: algemene grove ruis
    r_groot = ruis(P, 7, 1, 3)
    r_fijn = ruis(P, 60, 2, 2)

    # --- hemd: linnen/wol, effen binding, slubs, naden, open kraag, manchetten
    m = D["hemd"]
    if m.any():
        lam = 0.0045
        wv = np.sin(2 * np.pi * U / lam) * np.sin(2 * np.pi * V / lam) * wf
        slub = ruis(np.stack([U * 25, V * 500, np.zeros(n)], 1), 1, 3)
        c = KLEUR["hemd"][None] * (1 + 0.12 * r_groot[:, None] + 0.05 * r_fijn[:, None] + 0.06 * slub[:, None])
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
            c[kn] = c[kn] * 0.5 + KLEUR["hemd"] * 0.7 * (0.8 + 0.2 * (dk[kn] / (0.005 * s)))[:, None]
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
    # --- tuinbroek: paarse keper, slab met borstzak, bretels met gespen, gulp, vuil onderaan
    m = D["tuinbroek"] & ((reg <= 3) | (reg == 6))
    if m.any():
        lam = 0.005
        wv = np.sin(2 * np.pi * (U + V) / lam) * wf
        c = KLEUR["paars"][None] * (1 + 0.13 * r_groot[:, None] + 0.06 * r_fijn[:, None] + 0.05 * wv[:, None])
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
        gesp = D["tuinbroek"] & (reg == 6)
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
            kn = D["tuinbroek"] & (dk < 0.007 * s) & (reg != 6)
            kl[kn] = KLEUR["metaal"] * 0.7
            met[kn] = 0.9
    # riem en gesp
    m = D["riem"] & (reg == 0)
    c = KLEUR["riem"][None] * (1 + 0.25 * ruis(P, 300, 81)[:, None] + 0.15 * r_groot[:, None])
    zet(m, c)
    H[m] = 0.0003 * ruis(P, 400, 82)[m]
    ruw[m] = 0.55
    m = D["riem"] & (reg == 1)
    c = KLEUR["gesp"][None] * (0.85 + 0.15 * r_fijn[:, None])
    zet(m, c)
    ruw[m] = 0.35
    met[m] = 0.85
    # --- laarzen: leer, nerf, slijtplekken, welnaad, zool, modder
    m = D["laarzen"]
    if m.any():
        nerf = ruis(P, 500, 91, 2)
        vlek = ruis(P, 25, 92, 3)
        c = KLEUR["laars"][None] * (1 + 0.2 * vlek[:, None] + 0.08 * nerf[:, None])
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
    # --- huid: hoofd en handen
    for nm in ("hoofd", "handen"):
        m = D["lijf"] & (np.isin(reg, (0, 1, 3, 5)) if nm == "hoofd" else np.isin(reg, (2, 4)))
        if not m.any():
            continue
        basis = KLEUR["huid"] * (np.array([1.03, 0.95, 0.9]) if nm == "handen" else 1)
        por = ruis(P, 900, 101)
        c = basis[None] * (1 + 0.06 * r_groot[:, None] + 0.03 * por[:, None])
        h = 0.00006 * por
        if nm == "hoofd":
            kop = sk.kop
            kk = kop.k
            rood = srgb("#c4583e")
            vlek = 0.5 + 0.5 * ruis(P, 120, 103, 2)
            for oog in kop.ogen:
                sx = np.sign(oog[0])
                wang = oog + np.array([sx * 0.026, -0.012, -0.04]) * kk
                f = 0.62 * gauss(np.linalg.norm(P - wang, axis=1) / kk, 0.03) * (0.7 + 0.3 * vlek)
                c = c * (1 - f[:, None]) + rood[None] * f[:, None]
            reg_h = np.where(D["lijf"], reg, -1)
            neus = reg_h == 1
            fn = 0.38 * (0.6 + 0.4 * vlek)
            c[neus] = c[neus] * (1 - fn[neus, None]) + rood * fn[neus, None]
            ruw[m] = 0.6
            ruw[m & neus] = 0.58
            huid = reg_h == 0
            # voorhoofdrimpels
            vz = (z - kop.ogen[0][2]) / kk
            for zr in (0.036, 0.046, 0.057):
                lijn = gauss(vz - zr - 0.002 * np.sin(P[:, 0] / kk * 60), 0.0012) * (np.abs(P[:, 0]) < 0.05 * kk) * \
                    (P[:, 1] < kop.C[1] - 0.05 * kk) * huid
                h -= 0.00045 * kk * lijn
                c *= (1 - 0.18 * lijn)[:, None]
            for oog in kop.ogen:
                sx = np.sign(oog[0])
                do = (P - oog) / kk
                ex = do[:, 0] * sx                                  # naar buiten positief
                voor = (do[:, 1] < 0.012) & huid & (np.sign(P[:, 0]) == sx)
                # kraaienpootjes
                for hk in (-0.25, 0.1, 0.45):
                    kr = gauss((do[:, 2] - hk * (ex - 0.014)), 0.0009) * gladstap(0.013, 0.016, ex) * \
                        gladstap(0.03, 0.024, ex) * voor
                    h -= 0.0004 * kk * kr
                    c *= (1 - 0.15 * kr)[:, None]
                # wallen: iets donkerder, paarsig
                wal = gauss(np.hypot(do[:, 0] / 1.3, (do[:, 2] + 0.011) / 0.6), 0.008) * voor
                c = c * (1 - 0.18 * wal[:, None]) + srgb("#8a5a5a")[None] * 0.12 * wal[:, None]
                # slaperig oog: opening is een smalle ellips, het lid hangt tot over de helft van de iris
                ox, oz = do[:, 0] / 0.0118, (do[:, 2] + 0.0012) / 0.0058
                open_ = voor & (ox * ox + oz * oz < 1) & (do[:, 2] < 0.0012)
                ir = np.hypot(do[:, 0], do[:, 2] + 0.0008)
                c[open_] = srgb("#e2d6c6")
                iris = open_ & (ir < 0.0063)
                c[iris] = srgb("#4a3020") * (0.8 + 0.4 * (ir[iris] / 0.0063))[:, None]
                pup = open_ & (ir < 0.0029)
                c[pup] = srgb("#0e0806")
                gl = open_ & (np.hypot(do[:, 0] + 0.002 * sx, do[:, 2] - 0.0002) < 0.0012)
                c[gl] = srgb("#f2ece4")
                ruw[m & open_] = 0.12
                lidrand = voor & (np.abs(do[:, 2] - 0.0012) < 0.0011) & (np.abs(do[:, 0]) < 0.0125)
                c[lidrand] = c[lidrand] * 0.35 + srgb("#3a1e14") * 0.3
                lid = voor & (do[:, 2] > 0.0012) & (do[:, 2] < 0.009) & (np.abs(do[:, 0]) < 0.014) & ~open_
                c[lid] = c[lid] * 0.85 + srgb("#b86a58") * 0.15
                onder = voor & (np.abs(oz + 1.0) < 0.15) & (np.abs(ox) < 0.9)
                c[onder] *= 0.85
                # wenkbrauw: borstelig, buitenkant zakt (droevig-goedig)
                t = np.clip(ex / 0.022, -0.6, 1.2)
                zb = 0.0205 + 0.003 * (1 - t) - 0.006 * t * t
                br = voor & (np.abs(do[:, 2] - zb) < 0.0034 * (1 - 0.3 * t)) & (ex > -0.012) & (ex < 0.026)
                streep = 0.5 + 0.5 * np.sin((do[:, 2] - 0.4 * ex) / 0.0012 + 3 * ruis(P, 400, 104))
                c[br] = KLEUR["snor"] * (0.75 + 0.5 * streep[br, None])
                h[br] += 0.0005 * kk * streep[br]
            dm = (P - kop.mond) / kk
            # hangende onderlip onder de snor, half open mond
            lipz = dm[:, 2] + 0.012 + 0.006 * (dm[:, 0] / 0.02) ** 2
            onderlip = huid & (np.abs(lipz) < 0.0042) & (np.abs(dm[:, 0]) < 0.021) & (dm[:, 1] < 0.02)
            c[onderlip] = c[onderlip] * 0.4 + srgb("#b05848") * 0.6
            spleet = huid & (np.abs(lipz - 0.0048) < 0.0012) & (np.abs(dm[:, 0]) < 0.018) & (dm[:, 1] < 0.02)
            c[spleet] = srgb("#3a1a14")
            # stoppels op kaak en kin
            kaak = gladstap(kop.zz(1.075), kop.zz(1.03), z) * (P[:, 1] < kop.C[1]) * huid
            c *= (1 - 0.14 * kaak * (0.4 + 0.6 * (ruis(P, 2200, 102) > 0.2)))[:, None]
            # nek iets roder (zon), oogjes op de schijfjes (vaste kleur)
            nek = reg_h == 5
            c[nek] = c[nek] * 0.9 + rood * 0.1
            for oog in kop.ogen:
                sx = np.sign(oog[0])
                do = (P - oog) / kk
                sch = D["lijf"] & (reg == 3) & (np.sign(P[:, 0]) == sx)
                c[sch] = srgb("#ddd2c2")
                ir = np.hypot(do[:, 0], do[:, 2] + 0.0012)
                iris = sch & (ir < 0.0064)
                c[iris] = srgb("#4a3020") * (0.75 + 0.45 * (ir[iris] / 0.0064))[:, None]
                pup = sch & (ir < 0.0029)
                c[pup] = srgb("#0e0806")
                gl = sch & (np.hypot(do[:, 0] + 0.002 * sx, do[:, 2] - 0.0) < 0.0011)
                c[gl] = srgb("#f2ece4")
                lid = sch & (do[:, 2] > -0.0006)
                c[lid] = srgb("#5a3024")
                hoek = sch & (np.abs(do[:, 0]) > 0.0105)
                c[hoek] = c[hoek] * 0.6 + srgb("#b0706a") * 0.4
                ruw[sch] = 0.12
        else:
            # wanten-vingers: drie groeven over het vingerdeel, knokkels
            for k, sx in (("Left", 1), ("Right", -1)):
                pts = [J[k + "Hand"], J[k + "HandEnd"]]
                d, rv = keten_param(P, pts)
                t = (pts[1] - pts[0]) / np.linalg.norm(pts[1] - pts[0])
                f = np.array([0, -1, 0]) - np.dot([0, -1, 0], t) * t
                f /= np.linalg.norm(f)
                w = rv @ f
                zij = (sx * P[:, 0] > 0) & (reg == 2) & D["lijf"]
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
    # --- snor: donkerbruin met haarstrepen, puntjes lichter
    m = D["snor"]
    if m.any():
        kk = sk.kop.k
        strp = 0.5 + 0.5 * np.sin(2 * np.pi * (z + 0.55 * np.abs(P[:, 0])) / (0.0032 * kk) + 2 * ruis(P, 150, 42))
        pt = gladstap(0.02 * kk, 0.05 * kk, np.abs(P[:, 0]))
        cs = KLEUR["snor"][None] * (0.7 + 0.55 * strp[:, None]) * (1 + 0.35 * pt[:, None])
        zet(m, cs)
        ruw[m] = 0.72
    # --- haar: lokkleur uit de bake
    m = D["haar"]
    kb = B["kleur"][ys, xs, :3]
    c = kb * (1 + 0.1 * r_fijn[:, None])
    zet(m, c)
    ruw[m] = 0.82
    # tintbare delen naar lichtgrijs: textuur = kleur / tint (tint = basiskleur / GRIJS); vaste regio's echt
    vast = np.zeros(n, bool)
    for nm, regs in VAST.items():
        vast |= D[nm] & np.isin(reg, regs)
    for nm, sleutel in TINTBAAR.items():
        mm = D[nm] & ~vast
        kl[mm] = kl[mm] / (KLEUR[sleutel] / GRIJS)[None]
    return ys, xs, kl, H, ruw, met, deel, vast


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


def bewaar(arr, naam, data, jpg=False):
    """arr (h, w, 3) waarden 0..1 (al sRGB of data); rij 0 = onderkant (Blender-volgorde)."""
    os.makedirs(TEX, exist_ok=True)
    pad = os.path.join(TEX, naam + (".jpg" if jpg else ".png"))
    img = bpy.data.images.new(naam, arr.shape[1], arr.shape[0], alpha=False)
    if data:
        img.colorspace_settings.name = "Non-Color"
    a = np.concatenate([np.clip(arr, 0, 1), np.ones((*arr.shape[:2], 1))], 2).astype(np.float32)
    img.pixels.foreach_set(a.ravel())
    img.filepath_raw = pad
    img.file_format = "JPEG" if jpg else "PNG"
    if jpg:
        bpy.context.scene.render.image_settings.quality = 92
    img.save()
    bpy.data.images.remove(img)
    out = bpy.data.images.load(pad, check_existing=False)
    out.name = naam
    if data:
        out.colorspace_settings.name = "Non-Color"
    return out


def texturen(B, mpp, sk):
    t1 = time.time()
    ys, xs, kl, H, ruw, met, deel, vast = componeer(B, mpp, sk)
    h, w = B["pos"].shape[:2]
    mask = np.zeros((h, w), bool)
    mask[ys, xs] = True
    # AO
    ao = B["ao"][..., 0]
    oogje = vast & (deel == DELEN.index("lijf"))
    aov = np.where(oogje, 0.9, ao[ys, xs])
    ao[ys[oogje], xs[oogje]] = 0.9
    hr_ = deel == DELEN.index("haar")
    kl = kl * np.where(hr_, 0.8 + 0.2 * aov, 0.45 + 0.55 * aov)[:, None]                      # holtes ook in de kleur (leesbaar op 20 m)
    K = np.zeros((h, w, 3), np.float32)
    K[ys, xs] = naar_srgb(kl)
    # normaal: gebakken (vorm, plooien, lokken) + reliëf uit numpy (weefsel, naden, steken)
    Hm = np.zeros((h, w), np.float32)
    Hm[ys, xs] = H
    mp = np.full((h, w), np.mean(list(mpp.values())), np.float32)
    for i, nm in enumerate(DELEN):
        sel = deel == i
        mp[ys[sel], xs[sel]] = mpp[nm]
    Hd = dilateer(Hm[..., None].repeat(3, -1), mask, 3)[..., 0]
    nd = reliëf_normaal(Hd, mp)
    nb = B["normaal"][..., :3] * 2 - 1
    # haar: krullen iets verzachten (anders spikkels op afstand)
    hm = np.zeros((h, w), bool)
    hm[ys[hr_], xs[hr_]] = True
    zacht = (nb + np.roll(nb, 1, 0) + np.roll(nb, -1, 0) + np.roll(nb, 1, 1) + np.roll(nb, -1, 1)) / 5
    zacht = zacht * 0.65 + np.array([0, 0, 1.0]) * 0.35
    nb[hm] = zacht[hm]
    nb[ys[oogje], xs[oogje]] = (0, 0, 1)
    # whiteout-menging
    n = np.stack([nb[..., 0] + nd[..., 0], nb[..., 1] + nd[..., 1], nb[..., 2] * nd[..., 2]], -1)
    n /= np.linalg.norm(n, axis=-1, keepdims=True) + 1e-9
    Nimg = n * 0.5 + 0.5
    Nimg[~mask] = (0.5, 0.5, 1.0)
    ORM = np.zeros((h, w, 3), np.float32)
    ORM[..., 0] = np.clip(ao * 0.85 + 0.15, 0, 1)
    ORM[ys, xs, 1] = ruw
    ORM[ys, xs, 2] = met
    K = dilateer(K, mask, 10)
    Nimg = dilateer(Nimg.astype(np.float32), mask, 10)
    ORM = dilateer(ORM, mask, 10)
    kleur = bewaar(K, "man_kleur", False, jpg=True)
    normaal = bewaar(Nimg, "man_normaal", True)
    orm = bewaar(ORM[::2, ::2] if RES >= 2048 else ORM, "man_orm", True)
    log("texturen", f"{time.time() - t1:.1f}s")
    return kleur, normaal, orm


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


def materialen(delen, kleur, normaal, orm):
    """Een materiaal per tintbaar deel (zelfde atlas, eigen factor) plus mat_vast voor vaste kleuren."""
    vast = pbr("mat_vast", kleur, normaal, orm)
    cache = {}
    for naam, o in delen.items():
        me = o.data
        reg = np.zeros(len(me.polygons), np.int32)
        me.attributes["regio"].data.foreach_get("value", reg)
        me.materials.clear()
        if naam in TINTBAAR:
            sl = TINTBAAR[naam]
            mn = "mat_haar" if naam == "snor" else "mat_" + naam
            if mn not in cache:
                cache[mn] = pbr(mn, kleur, normaal, orm, tuple(np.clip(KLEUR[sl] / GRIJS, 0, 1)))
            me.materials.append(cache[mn])
            me.materials.append(vast)
            idx = np.isin(reg, VAST.get(naam, ())).astype(np.int32)
        else:
            me.materials.append(vast)
            idx = np.zeros(len(reg), np.int32)
        me.polygons.foreach_set("material_index", idx)
        if naam in TINTBAAR:
            log("  tint", naam, "#" + "".join("%02x" % round(255 * c) for c in naar_srgb(np.clip(KLEUR[TINTBAAR[naam]] / GRIJS, 0, 1))))


# --- Platte materialen (silhouetrondes) ---------------------------------------------------------
def vlak_mat(naam, kleur, ruw=0.8):
    m = bpy.data.materials.new(naam)
    m.use_nodes = True
    bs = m.node_tree.nodes["Principled BSDF"]
    bs.inputs["Base Color"].default_value = (*kleur, 1)
    bs.inputs["Roughness"].default_value = ruw
    return m


def vlakke_kleuren(delen):
    tabel = {"hemd": ["hemd", "hemd"], "tuinbroek": ["paars"] * 6 + ["metaal"], "riem": ["riem", "gesp"],
             "laarzen": ["laars", "zool"], "lijf": ["huid"] * 6, "snor": ["snor"], "haar": ["haar"]}
    for naam, o in delen.items():
        o.data.materials.clear()
        for k in tabel[naam]:
            o.data.materials.append(vlak_mat(naam + "_" + k, KLEUR[k], 0.35 if k == "gesp" else 0.8))
        reg = np.zeros(len(o.data.polygons), np.int32)
        o.data.attributes["regio"].data.foreach_get("value", reg)
        o.data.polygons.foreach_set("material_index", np.minimum(reg, len(tabel[naam]) - 1))


# --- Studio: camera en licht zoals de hut (2:1-iso, yaw 225, pitch 30, ortho) ------------------
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


def pose(rig, standen):
    for b in rig.pose.bones:
        b.rotation_mode = "QUATERNION"
        b.rotation_quaternion = (1, 0, 0, 0)
        b.location = (0, 0, 0)
    for naam, e in standen.items():
        rig.pose.bones[naam].rotation_quaternion = Euler([math.radians(x) for x in e], "XYZ").to_quaternion()
    bpy.context.view_layer.update()


STAND = {"LeftArm": (0, 0, -31), "RightArm": (0, 0, 31), "LeftForeArm": (8, 0, 0), "RightForeArm": (8, 0, 0),
         "LeftHandFist": (15, 0, 0), "RightHandFist": (15, 0, 0)}


def vergelijk(sc, rig, tag=""):
    """Sprite naast de render in een rustige stand (armen langs het lijf, zoals m_still)."""
    os.makedirs(PREV, exist_ok=True)
    if rig:
        rig.animation_data_create().action = None
        pose(rig, STAND)
    for o in sc.objects:
        if o.name.startswith("prop_") and o.name != "prop_strootje":
            o.hide_render = True
    tmp = bpy.app.tempdir
    spr = bijsnijden(laad_np(os.path.join(REF, "frames", "m_still_hd_x2.png")))     # 87,6 px/m
    walk = bijsnijden(laad_np(os.path.join(REF, "frames", "m_walk_hd_x2.png")))
    studio(sc, 43.8, 1.0, 1.6, doel=(0, 0, 0.72))
    r_se = bijsnijden(render_np(sc, os.path.join(tmp, "r_se.png")))
    studio(sc, 43.8, 1.0, 1.6, doel=(0, 0, 0.72), yaw=315)
    r_sw = bijsnijden(render_np(sc, os.path.join(tmp, "r_sw.png")))
    k = 6
    rij = plak([nn(spr[::2, ::2], k), nn(r_se, k), nn(r_sw, k), nn(walk[::2, ::2], k)])
    schrijf(rij, os.path.join(PREV, f"man_vergelijk_1x{tag}.png"))
    studio(sc, 420, 0.8, 1.55, doel=(0, 0, 0.72))
    big = [bijsnijden(render_np(sc, os.path.join(tmp, "c_se.png")))]
    for yw in (270, 0, 45):
        studio(sc, 300, 0.8, 1.55, doel=(0, 0, 0.72), yaw=yw, pitch=15)
        big.append(bijsnijden(render_np(sc, os.path.join(tmp, f"c_{yw}.png"))))
    schrijf(plak([nn(spr, 5)] + big), os.path.join(PREV, f"man_vergelijk_close{tag}.png"))
    # gezicht en handen echt dichtbij
    studio(sc, 1600, 0.45, 0.45, doel=(0, -0.05, 1.17), yaw=250, pitch=12)
    kop = render_np(sc, os.path.join(tmp, "kop.png"))
    studio(sc, 1600, 0.45, 0.45, doel=(-0.18, 0, 0.55), yaw=225, pitch=25)
    hand = render_np(sc, os.path.join(tmp, "hand.png"))
    studio(sc, 1600, 0.45, 0.45, doel=(-0.09, -0.05, 0.1), yaw=235, pitch=25)
    voet = render_np(sc, os.path.join(tmp, "voet.png"))
    schrijf(plak([kop, hand, voet]), os.path.join(PREV, f"man_detail{tag}.png"))


def poses(sc, rig, tag=""):
    """Extreme standen uit de animaties, iso en van voren-opzij."""
    keuzes = [("idle", 0), ("lopen", 3), ("lopen", 15), ("bouwen", 0), ("bouwen", 11),
              ("aanval_zwaard", 6), ("aanval_zwaard", 10), ("aanval_steen", 8), ("aanval_steen", 16)]
    props = [o for o in sc.objects if o.name.startswith("prop_") and o.name != "prop_strootje"]
    tmp = bpy.app.tempdir
    rijen = []
    for yaw, pitch in ((225, 30), (300, 10)):
        panelen = []
        for act, f in keuzes:
            a = bpy.data.actions.get(act)
            if a is None:
                continue
            ad = rig.animation_data_create()
            ad.action = a
            if getattr(ad, "action_slot", None) is None and len(getattr(a, "slots", [])):
                ad.action_slot = a.slots[0]
            for p in props:
                p.hide_render = not ((act == "bouwen" and "hamer" in p.name) or
                                     (act == "aanval_zwaard" and "zwaard" in p.name) or
                                     (act == "aanval_steen" and "steen" in p.name))
            sc.frame_set(f)
            studio(sc, 260, 1.5, 1.9, doel=(0, -0.1, 0.8), yaw=yaw, pitch=pitch)
            panelen.append(bijsnijden(render_np(sc, os.path.join(tmp, f"p_{act}_{f}.png"))))
        rijen.append(plak(panelen))
    schrijf(onder(*rijen), os.path.join(PREV, f"man_poses{tag}.png"))
    rig.animation_data.action = None


# --- Hoofdprogramma ------------------------------------------------------------------------------
def maak_strootje(sk, rig):
    """Strohalm in de linker mondhoek, met een aartje; los te schakelen (prop_strootje, kind van Head)."""
    kop = sk.kop
    kk = kop.k
    start = kop.mond + np.array([0.034, -0.004, -0.006]) * kk
    d = np.array([0.72, -0.5, 0.2])
    d /= np.linalg.norm(d)
    B = Bouwer()
    n = 14
    pts = [start + d * 0.13 * kk * i / (n - 1) + np.array([0, 0, -0.012 * kk]) * (i / (n - 1)) ** 2 for i in range(n)]
    fr = keten(pts, list(np.linspace(-0.004, 0.13 * kk, n)), ref=(0, 0, 1))
    rings = []
    for i, (pos, t, f, sd) in enumerate(fr):
        r = 0.0024 * kk
        if i > n - 5:                                             # aartje
            u = (i - (n - 5)) / 4
            r = (0.0024 + 0.006 * math.sin(math.pi * min(u * 1.2, 1))) * kk
        rings.append(ring(pos, sd, f, r, r * 0.8, 6))
    b0, _ = B.grid(np.array(rings), True)
    B.kap(b0 + 6 * (n - 1), 6, fr[-1][0] + fr[-1][1] * 0.008 * kk)
    o = B.obj("prop_strootje", bpy.context.scene.collection)
    m = bpy.data.materials.new("strootje")
    m.use_nodes = True
    bs = m.node_tree.nodes["Principled BSDF"]
    bs.inputs["Base Color"].default_value = (*srgb("#d4ad55"), 1)
    bs.inputs["Roughness"].default_value = 0.55
    o.data.materials.append(m)
    o.data.uv_layers.active.name = "UVMap"
    o.parent = rig
    o.parent_type = "BONE"
    o.parent_bone = "Head"
    bpy.context.view_layer.update()
    from mathutils import Matrix
    o.matrix_world = Matrix.Identity(4)
    return o


def driehoeken(objs):
    n = 0
    for o in objs:
        o.data.calc_loop_triangles()
        n += len(o.data.loop_triangles)
    return n


def samenvoegen(objs, naam):
    ontkies()
    for o in objs:
        o.select_set(True)
    bpy.context.view_layer.objects.active = objs[0]
    bpy.ops.object.join()
    o = bpy.context.view_layer.objects.active
    o.name = naam
    o.data.name = naam
    return o


def main():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    sc = bpy.context.scene
    sc.render.fps = R.FPS
    sc.frame_start = 0
    coll = sc.collection
    rig = R.bouw_rig(MAAT_MAN)
    sk = Skelet(rig)
    delen = bouw_delen(sk, coll)
    log("driehoeken", driehoeken(delen.values()), {k: driehoeken([o]) for k, o in delen.items()})
    if VLAK:
        vlakke_kleuren(delen)
    else:
        B, mpp = bak_alles(delen, sk, coll)
        kleur, normaal, orm = texturen(B, mpp, sk)
        materialen(delen, kleur, normaal, orm)
    for naam, o in delen.items():
        gewichten(o, sk, naam)
        me = o.data
        me.uv_layers.active = me.uv_layers.get("UVMap") or me.uv_layers[0]
        if "UVm" in me.uv_layers and "UVMap" in me.uv_layers:
            me.uv_layers.remove(me.uv_layers["UVm"])
        for a in ("regio", "deel"):
            if a in me.attributes:
                me.attributes.remove(me.attributes[a])
    objs = list(delen.values())
    for o in objs:
        o.parent = rig
        m = o.modifiers.new("Armature", "ARMATURE")
        m.object = rig
    log("LOD0 driehoeken", driehoeken(objs), {o.name: driehoeken([o]) for o in objs})
    # props van de rig op prop_R, zoals bumpkin_test.glb
    for pn, fn in (("prop_hamer", R.maak_hamer), ("prop_zwaard", R.maak_zwaard), ("prop_steen", R.maak_steen)):
        ob = fn(pn)
        ob.parent = rig
        ob.parent_type = "BONE"
        ob.parent_bone = "prop_R"
        ob.location = (0, -rig.data.bones["prop_R"].length, 0)
    maak_strootje(sk, rig)
    info = R.bouw_animaties(rig)
    log("animaties", list(info))
    if "geen_export" not in OPTS:
        ontkies()
        bpy.ops.export_scene.gltf(filepath=GLB, export_format="GLB", export_animations=True,
                                  export_animation_mode="ACTIONS", export_force_sampling=True, export_yup=True,
                                  export_skins=True, export_def_bones=False, export_extras=True, use_selection=False,
                                  export_tangents=True, export_image_format="AUTO", export_cameras=False,
                                  export_lights=False)
        log("export", GLB, f"{os.path.getsize(GLB) / 1e6:.1f} MB")
    tag = OPTS.get("tag", "")
    if "vergelijk" in OPTS:
        vergelijk(sc, rig, tag)
    if "poses" in OPTS:
        poses(sc, rig, tag)
    bpy.ops.wm.save_as_mainfile(filepath=os.path.join(HERE, "preview", "bumpkin_man.blend"))
    log("KLAAR")


if __name__ == "__main__":
    main()
