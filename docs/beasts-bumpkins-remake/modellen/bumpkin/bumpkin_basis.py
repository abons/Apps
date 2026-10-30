"""Gedeelde bouwstraat voor alle bumpkins (Blender 5.2 headless -> glb voor Godot 4).

Gebruikt door bumpkin_man.py, bumpkin_vrouw.py, bumpkin_jongen.py, bumpkin_meisje.py,
bumpkin_oudere_man.py en bumpkin_oudere_vrouw.py. Elk personage-script maakt een `Personage`
(naam, MAAT, DELEN, SOORT, TINTBAAR, VAST, TEXEL, KLEUR, bouw-functie) en roept `bouw_personage(p)`.

Opbouw:
  bumpkin_basis.py  hulpjes (ruis, Skelet, Bouwer, Kop), gewichten/hoog-poly/texturen als raamwerk,
                    bakken, atlas, materialen, studio/vergelijk/poses, export. Dispatch per SOORT van een
                    deel via de registers GEWICHT, HOOG en VERF.
  bumpkin_delen.py  de bibliotheek van delen: per soort een bouwer (geometrie), een gewichtregel, een
                    plooi/reliëfregel (hoog-poly) en een schilder (textuur). De man-delen staan er
                    ongewijzigd in; de andere personages voegen soorten toe (tuniek, jurk, broek, ...).
Opties (na `--`): res=2048 snel vlak vergelijk poses geen_export tag=<x> ref=<map>.
"""
import math
import os
import sys
import time

import bmesh
import bpy
import numpy as np
from mathutils import Euler, Matrix, Quaternion, Vector

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import bumpkin_rig as R  # noqa: E402


argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
OPTS = {a.split("=")[0]: (a.split("=", 1)[1] if "=" in a else "1") for a in argv}
SNEL = "snel" in OPTS
VLAK = "vlak" in OPTS
RES = int(OPTS.get("res", 512 if SNEL else 2048))
SPP = 0.25 if SNEL else 1.0


MOD = os.path.dirname(HERE)
PREV = os.path.join(HERE, "preview")
SCRATCH = os.path.join(os.environ.get("TEMP", ""), "claude", "E--werk-androidApps-Apps",
                       "16e99493-ac86-47c7-921f-1d215c266f51", "scratchpad")
REF = OPTS.get("ref", os.path.join(SCRATCH, "bumpkin", "ref"))
T0 = time.time()
GRIJS = 0.86                       # gemiddelde luminantie van een tintbare textuur; tint = kleur / GRIJS
KAART_REGIO, KAART_TEXEL = 3, 2.4  # haarkaarten (alpha): regio in een haar-deel, eigen texeldichtheid
GEWICHT, HOOG, VERF = {}, {}, {}   # registers per soort (gevuld door bumpkin_delen)
LAAG = {}                          # soort -> fn(o, sk, naam): vervorming van de laag-poly (plooien)
C = None                           # het actieve Personage


class Personage:
    """Alles wat een personage anders maakt. bouw(sk, coll) -> {deel: object} (volgorde = bakvolgorde)."""

    def __init__(self, naam, maat, delen, soort, tintbaar, vast, texel, kleur, bouw, texel_regio=None,
                 bak_ext=None, kleurbak=("haar",), krullen=None, sprites=("m_still", "m_walk"), props=None,
                 na_animatie=None, extra=None):
        self.naam, self.MAAT, self.DELEN, self.SOORT = naam, maat, delen, soort
        self.TINTBAAR, self.VAST, self.TEXEL, self.KLEUR = tintbaar, vast, texel, kleur
        self.TEXEL_REGIO = texel_regio or {}
        self.bouw = bouw
        self.BAK_EXT = bak_ext or {}
        self.KLEURBAK = kleurbak            # delen waarvan de kleur uit de hoog-poly gebakken wordt
        self.KRULLEN = krullen              # fn(sk, coll) -> {deel: [extra hoog-poly objecten]}
        self.SPRITES = sprites
        self.PROPS = props                  # fn(sk, rig, delen): extra props (strootje, staf)
        self.NA_ANIMATIE = na_animatie      # fn(rig): b.v. de ouderdomshouding op de clips
        self.extra = extra or {}
        self.TEX = os.path.join(HERE, "textures_" + naam)
        self.GLB = os.path.join(HERE, "bumpkin_" + naam + ".glb")

    def soort(self, deel):
        return self.SOORT.get(deel, deel)


def log(*a):
    print(f"[{C.naam if C else 'basis'} {time.time() - T0:6.1f}s]", *a, flush=True)



def srgb(h):
    h = h.lstrip("#")
    c = [int(h[i:i + 2], 16) / 255 for i in (0, 2, 4)]
    return np.array([x / 12.92 if x <= 0.04045 else ((x + 0.055) / 1.055) ** 2.4 for x in c])


def hexkleur(lin):
    return "#" + "".join("%02x" % round(255 * c) for c in naar_srgb(np.asarray(lin)))


def naar_srgb(c):
    c = np.clip(c, 0, 1)
    return np.where(c <= 0.0031308, c * 12.92, 1.055 * np.power(c, 1 / 2.4) - 0.055)


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

    def zr(self, z0):
        """Als z(), maar onder de heup naar de beenlengte (rok, tuniek en broek van kind en vrouw)."""
        if z0 >= 0.644:
            return self.z(z0)
        return z0 * self.hz / 0.644

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
    """Schedel op ware grootte (gezicht volgens het portret), het volume komt van de krullenbol.

    Alle maten zijn bij de volwassen kop (k = 1) en schalen met k; de standaardwaarden zijn de man.
    schedel=(a, b, top, bot), kaak=(breed, smal, plat): wangen/kaak, ogen_ph/ogen_z: oogposities,
    mond_z, neus (offset t.o.v. C), neusprof (ringen z, a, b, dy), oog (half-breedte, boven, onder),
    haar_c/haar_r: ellipsoide van het haar, haargrens: [(hoek vanaf voor, z0)], klont: amplitude.
    """

    def __init__(self, sk, schedel=(0.098, 0.113, 0.128, 0.122), kaak=(0.06, 0.22, 0.15), ogen_ph=0.42,
                 ogen_z=1.118, mond_z=1.038, neus=(0, -0.102, -0.036), neusprof=None, oog=(0.0128, 0.0012, 0.0068),
                 haar_c=(0, 0.012, 1.175), haar_r=(0.156, 0.13, 0.148, 0.145, 0.165), haargrens=None,
                 klont=(0.13, 0.05), gezicht=None):
        self.k = k = sk.kh
        self.kz = sk.kz
        self.kaak = kaak
        self.vormfn = None
        self.C = np.array([0, -0.004 * k, self.zz(1.118)])
        self.a, self.b, self.top, self.bot = [x * k for x in schedel]
        self.ogen = [self.punt(self.theta_bij_z(ph, self.zz(ogen_z)), ph, 0.0) for ph in (ogen_ph, -ogen_ph)]
        self.mond = self.punt(self.theta_bij_z(0.0, self.zz(mond_z)), 0.0, 0.0)
        self.neus = self.C + np.array(neus) * k
        self.neusprof = neusprof or ((0.03, 0.011, 0.01, 0.014), (0.012, 0.016, 0.018, 0.0),
                                     (-0.006, 0.026, 0.026, -0.008), (-0.02, 0.027, 0.026, -0.01),
                                     (-0.032, 0.019, 0.016, 0.0))
        self.oog = oog
        self.gezicht = dict(gezicht or {})
        # krullenbol: ellipsoide boven/achter de schedel, klonten op een vaste set richtingen
        self.Ch = np.array([0, haar_c[1] * k, self.zz(haar_c[2])])
        self.hr = dict(zip(("x", "yv", "ya", "zt", "zo"), [r * k for r in haar_r]))
        self.grens = haargrens or [(0.0, 1.16), (0.55, 1.156), (0.95, 1.136), (1.3, 1.11), (1.6, 1.1), (2.2, 1.08),
                                   (np.pi, 1.07)]
        self.klont_amp = klont
        rng = np.random.default_rng(5)
        d = rng.normal(size=(260, 3))
        self.klontdir = d / np.linalg.norm(d, axis=1, keepdims=True)
        self.klontw = rng.uniform(0.55, 1.0, 260)
        # gezichtsvorm (bumpkin_delen.gezicht_vorm): f(P (n, 3)) -> verschuiving (m) langs de straal.
        # Pas gezet als ogen/mond/neus op de kale schedel liggen; daarna volgt punt() het gezicht.
        self.vormfn = None

    def punten(self, TH, PH, vorm=True):
        """punt() over arrays (zelfde vorm als TH/PH, plus een as van 3)."""
        TH, PH = np.broadcast_arrays(np.asarray(TH, float), np.asarray(PH, float))
        d = np.stack([np.sin(TH) * np.sin(PH), -np.sin(TH) * np.cos(PH), np.cos(TH)], -1)
        cz = np.where(d[..., 2] > 0, self.top, self.bot)
        r = 1 / np.sqrt((d[..., 0] / self.a) ** 2 + (d[..., 1] / self.b) ** 2 + (d[..., 2] / cz) ** 2)
        p = d * r[..., None]
        q = np.where(p[..., 2] < 0, (-p[..., 2] / self.bot) ** 2, 0.0)
        p[..., 0] *= 1 + self.kaak[0] * q - self.kaak[1] * q * q
        p[..., 1] = p[..., 1] * (1 - self.kaak[2] * q) - 0.01 * self.k * q
        voor = p[..., 1] < 0
        p[..., 1] = np.where(voor, p[..., 1] * (0.9 + 0.1 * np.minimum(1, np.abs(p[..., 0]) / (0.08 * self.k)) ** 2),
                             p[..., 1])
        P = self.C + p
        if vorm and self.vormfn is not None:
            sh = P.shape
            Pf = P.reshape(-1, 3)
            Pf = Pf + self.vormrichting(d.reshape(-1, 3)) * self.vormfn(Pf)[:, None]
            P = Pf.reshape(sh)
        return P

    @staticmethod
    def vormrichting(d):
        """Richting van de gezichtsvorm: de straal, maar platter in z (een neus steekt naar voren uit)."""
        d = np.asarray(d, float) * np.array([1.0, 1.0, 0.35])
        return d / (np.linalg.norm(d, axis=-1, keepdims=True) + 1e-9)

    def zz(self, z0):
        return self.kz + (z0 - 1.0) * self.k

    @staticmethod
    def richting(tht, ph):
        return np.array([math.sin(tht) * math.sin(ph), -math.sin(tht) * math.cos(ph), math.cos(tht)])

    def punt(self, tht, ph, extra=0.0, vorm=True):
        """Punt op de schedel: polair tht vanaf de kruin, ph om z (0 = voor, -Y; +ph = naar +X).
        Met vorm (en een gezet vormfn) ligt het punt op het gebeeldhouwde gezicht."""
        d = self.richting(tht, ph)
        cz = self.top if d[2] > 0 else self.bot
        r = 1 / math.sqrt((d[0] / self.a) ** 2 + (d[1] / self.b) ** 2 + (d[2] / cz) ** 2)
        p = d * r
        if p[2] < 0:                                              # zware wangen, brede kaak
            q = (-p[2] / self.bot) ** 2
            p[0] *= 1 + self.kaak[0] * q - self.kaak[1] * q * q
            p[1] = p[1] * (1 - self.kaak[2] * q) - 0.01 * self.k * q
        if p[1] < 0:                                              # gezicht platter
            p[1] *= 0.9 + 0.1 * min(1, (abs(p[0]) / (0.08 * self.k))) ** 2
        if vorm and self.vormfn is not None:
            p = p + self.vormrichting(d[None])[0] * float(self.vormfn((self.C + p)[None])[0])
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
            r *= 1 + self.klont_amp[0] * self.klont(d) - self.klont_amp[1]
        return self.Ch + d * (r + extra)

    def haargrens(self, ph):
        """Onderrand van de bol per hoek: haarlijn voor, oren bedekt, nek achter."""
        a = abs((ph + np.pi) % (2 * np.pi) - np.pi)
        xs, ys = zip(*self.grens)
        return self.zz(float(np.interp(a, xs, ys)))




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

    g = type("G", (), {})()
    g.P, g.N, g.J, g.G, g.s, g.sk, g.me, g.naam = P, N, J, G, s, sk, me, naam
    g.voeg, g.romp_gewicht, g.romp = voeg, romp_gewicht, romp
    GEWICHT[C.soort(naam)](g)
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
    fn, niveau, simpel = HOOG.get(C.soort(naam), (None, 2, False))
    m.levels = m.render_levels = niveau
    m.uv_smooth = "PRESERVE_BOUNDARIES"
    if simpel:
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
    if fn:
        h_ = type("H", (), {})()
        h_.P, h_.Nn, h_.reg, h_.J, h_.s, h_.hgt, h_.naam = P, Nn, reg, J, s, hgt, naam
        fn(h_, sk)
    P = P + Nn * hgt[:, None]
    me.vertices.foreach_set("co", P.ravel())
    me.update()
    vervang = getattr(sk, "hoog_extra", {}).get(naam)
    if vervang:                                                   # b.v. het hoofd: echte hoog-poly-bron
        bron, regios = vervang
        bm = bmesh.new()
        bm.from_mesh(me)
        lay = bm.faces.layers.int.get("regio")
        weg = [f for f in bm.faces if f[lay] in regios]
        bmesh.ops.delete(bm, geom=weg, context="FACES")
        bm.to_mesh(me)
        bm.free()
        k = bron.copy()
        k.data = bron.data.copy()
        coll.objects.link(k)
        ontkies()
        h.select_set(True)
        k.select_set(True)
        bpy.context.view_layer.objects.active = h
        bpy.ops.object.join()
    return h


def krullen(sk, coll, n=2600, kleur=None, seed=9, lengte=(0.016, 0.03), rc=(0.0045, 0.0075),
            rt=(0.0016, 0.0024), draai=(1.6, 2.8), licht=(0.9, 1.6), warm=(-0.1, 0.16), naam="haar_krullen",
            haarpunt=None, grens=None, tmin=0.02):
    """Krullen als kleine spiraalbuisjes, half in het oppervlak van de bol: normaal- en kleurdetail."""
    kop = sk.kop
    kk = kop.k
    rng = np.random.default_rng(seed)
    hp = haarpunt or kop.haarpunt
    hg = grens or kop.haargrens
    basis_kl = C.KLEUR["haar"] if kleur is None else kleur
    V, F, Ck = [], [], []
    sides, seg = 4, 18
    tb_cache = {}
    for _ in range(n):
        ph = rng.uniform(0, 2 * np.pi)
        key = round(ph, 2)
        if key not in tb_cache:
            tb_cache[key] = kop.theta_bij_z(ph, hg(ph), lambda t, p: hp(t, p, False))
        tb = tb_cache[key]
        tht = math.acos(rng.uniform(math.cos(tb), math.cos(tmin)))       # gelijk over het oppervlak
        p0 = hp(tht, ph)
        e = 0.01
        dt = hp(tht + e, ph) - hp(tht - e, ph)
        dp = hp(tht, ph + e) - hp(tht, ph - e)
        nrm = np.cross(dt, dp)
        nrm /= np.linalg.norm(nrm) + 1e-9
        if np.dot(nrm, p0 - kop.Ch) < 0:
            nrm = -nrm
        a = rng.normal(size=3)
        a -= np.dot(a, nrm) * nrm
        a /= np.linalg.norm(a)
        e2 = np.cross(a, nrm)
        L = rng.uniform(*lengte) * kk
        rc_ = rng.uniform(*rc) * kk
        rt_ = rng.uniform(*rt) * kk
        tw = rng.uniform(*draai)
        fase = rng.uniform(0, 2 * np.pi)
        u = np.linspace(0, 1, seg)
        ang = fase + 2 * np.pi * tw * u
        pad = p0 + nrm * rc_ * 0.35 + a * (u - 0.5)[:, None] * L + \
            (np.cos(ang)[:, None] * nrm + np.sin(ang)[:, None] * e2) * rc_
        licht_ = rng.uniform(*licht)
        warm_ = rng.uniform(*warm)
        kl = np.clip(basis_kl * licht_ * np.array([1 + warm_ * 0.3, 1 + warm_, 1 - warm_ * 0.6]), 0, 1)
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
                V.append(pad[i] + (np.cos(an) * sd + np.sin(an) * up) * rt_)
                Ck.append(kl)
        for i in range(seg - 1):
            for k in range(sides):
                k1 = (k + 1) % sides
                F.append((b0 + i * sides + k, b0 + i * sides + k1, b0 + (i + 1) * sides + k1, b0 + (i + 1) * sides + k))
    me = bpy.data.meshes.new("krullen")
    me.from_pydata([tuple(p) for p in V], [], F)
    me.update()
    at = me.attributes.new("kleur", "FLOAT_COLOR", "POINT")
    Cc = np.concatenate([np.array(Ck), np.ones((len(Ck), 1))], 1)
    at.data.foreach_set("color", Cc.ravel().astype(np.float32))
    me.shade_smooth()
    o = bpy.data.objects.new(naam, me)
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
        fac = np.array([C.TEXEL_REGIO.get((naam, int(r)), KAART_TEXEL / C.TEXEL[naam]
                                          if (C.soort(naam) == "haar" and int(r) == KAART_REGIO) else 1.0)
                        for r in reg]) * C.TEXEL[naam]
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
        zet_kleur_attr(h, C.KLEUR[C.TINTBAAR[naam]] * 0.85 if naam in C.KLEURBAK
                       else C.KLEUR.get("hemd", np.array([0.3, 0.3, 0.3])))
        highs[naam] = [h]
    if C.KRULLEN:
        for nm, objs in C.KRULLEN(sk, coll).items():
            highs[nm] += objs
    for nm, makers in getattr(sk, "hoog_makers", {}).items():     # b.v. haarstrengen (bumpkin_delen)
        for mk in makers:
            highs[nm].append(mk(coll))
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
        at.data.foreach_set("value", ((C.DELEN.index(naam) * 8 + reg + 1) / 128.0).astype(np.float32))
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
        ext, ray = C.BAK_EXT.get(naam, (0.01, 0.03))
        bak(o, hs, "normaal", beelden["normaal"], ext, ray, clear=(i == 0))
        bak(o, hs, "ao", beelden["ao"], ext, ray, clear=(i == 0))
        if naam in C.KLEURBAK or i == 0:
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
    alfa = np.ones(n)
    D = {k: deel == C.DELEN.index(k) for k in C.DELEN}
    z = P[:, 2]

    def zet(m, c):
        kl[m] = c[m] if np.ndim(c) == 2 else c

    wf = float(np.clip((0.005 / np.mean([mpp[k] for k in C.extra.get("weefsel", ("hemd", "tuinbroek"))]) - 2.5) / 2, 0, 1))
    # stof: algemene grove ruis
    r_groot = ruis(P, 7, 1, 3)
    r_fijn = ruis(P, 60, 2, 2)

    cx = type("CX", (), {})()
    cx.P, cx.U, cx.V, cx.z, cx.reg, cx.n, cx.s, cx.J, cx.sk = P, U, V, z, reg, n, s, J, sk
    cx.kl, cx.H, cx.ruw, cx.met, cx.zet, cx.D, cx.alfa = kl, H, ruw, met, zet, D, alfa
    cx.r_groot, cx.r_fijn, cx.wf, cx.B, cx.ys, cx.xs, cx.KLEUR = r_groot, r_fijn, wf, B, ys, xs, C.KLEUR
    for nm in C.DELEN:
        f = VERF.get(C.soort(nm))
        if f is None or not D[nm].any():
            continue
        cx.Dm, cx.naam, cx.tint = D[nm], nm, C.TINTBAAR.get(nm)
        f(cx)
    if "_slijtage" in VERF:                                       # vuil en sleet over alle delen
        VERF["_slijtage"](cx)
    # tintbare delen naar lichtgrijs: textuur = kleur / tint (tint = basiskleur / GRIJS); vaste regio's echt
    vast = np.zeros(n, bool)
    for nm, regs in C.VAST.items():
        vast |= D[nm] & np.isin(reg, regs)
    for nm, sleutel in C.TINTBAAR.items():
        mm = D[nm] & ~vast
        kl[mm] = kl[mm] / (C.KLEUR[sleutel] / GRIJS)[None]
    C.ALFA = alfa
    C.KAARTMASK = np.isin(deel, [C.DELEN.index(k) for k in C.DELEN if C.soort(k) == "haar"]) & (reg == KAART_REGIO)
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
    os.makedirs(C.TEX, exist_ok=True)
    pad = os.path.join(C.TEX, naam + (".jpg" if jpg else ".png"))
    img = bpy.data.images.new(naam, arr.shape[1], arr.shape[0], alpha=arr.shape[2] == 4)
    tweeling = os.path.join(C.TEX, naam + (".png" if jpg else ".jpg"))
    if os.path.exists(tweeling) and not naam.endswith(("_normaal", "_orm")):
        os.remove(tweeling)                                       # geen verouderde kleurkaart naast de nieuwe
    if data:
        img.colorspace_settings.name = "Non-Color"
    a = np.clip(arr, 0, 1) if arr.shape[2] == 4 else np.concatenate([np.clip(arr, 0, 1), np.ones((*arr.shape[:2], 1))], 2)
    a = a.astype(np.float32)
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
    oogje = vast & (deel == C.DELEN.index("lijf"))
    aov = np.where(oogje, 0.9, ao[ys, xs])
    ao[ys[oogje], xs[oogje]] = 0.9
    hr_ = np.isin(deel, [C.DELEN.index(k) for k in C.extra.get("haardelen", C.KLEURBAK)])
    huid_ = (deel == C.DELEN.index("lijf")) if "lijf" in C.DELEN else np.zeros(len(deel), bool)
    kl = kl * np.where(hr_, 0.8 + 0.2 * aov, np.where(huid_, 0.78 + 0.22 * aov, 0.45 + 0.55 * aov))[:, None]  # holtes in de kleur
    K = np.zeros((h, w, 3), np.float32)
    K[ys, xs] = naar_srgb(kl)
    # normaal: gebakken (vorm, plooien, lokken) + reliëf uit numpy (weefsel, naden, steken)
    Hm = np.zeros((h, w), np.float32)
    Hm[ys, xs] = H
    mp = np.full((h, w), np.mean(list(mpp.values())), np.float32)
    for i, nm in enumerate(C.DELEN):
        sel = deel == i
        mp[ys[sel], xs[sel]] = mpp[nm]
    Hd = dilateer(Hm[..., None].repeat(3, -1), mask, 3)[..., 0]
    nd = reliëf_normaal(Hd, mp)
    nb = B["normaal"][..., :3] * 2 - 1
    # haar: krullen iets verzachten (anders spikkels op afstand)
    hm = np.zeros((h, w), bool)
    hm[ys[hr_], xs[hr_]] = True
    zacht = (nb + np.roll(nb, 1, 0) + np.roll(nb, -1, 0) + np.roll(nb, 1, 1) + np.roll(nb, -1, 1)) / 5
    zacht = zacht * 0.85 + np.array([0, 0, 1.0]) * 0.15
    nb[hm] = zacht[hm]
    hn = C.extra.get("haar_normaal")                          # < 1: lokken nog vlakker (pluishaar, geen folie)
    if hn is not None:
        v = nb[hm] * hn + np.array([0, 0, 1.0]) * (1 - hn)
        nb[hm] = v / (np.linalg.norm(v, axis=-1, keepdims=True) + 1e-9)
    nb[ys[oogje], xs[oogje]] = (0, 0, 1)
    kaart = C.ALFA < 0.999 if np.ndim(C.ALFA) else np.zeros(len(ys), bool)
    kaart |= np.isin(deel, [C.DELEN.index(k) for k in C.DELEN if C.soort(k) == "haar"]) & \
        (getattr(C, "KAARTMASK", np.zeros(len(ys), bool)))
    nb[ys[kaart], xs[kaart]] = (0, 0, 1)                          # haarkaarten: plat, reliëf uit de schilder
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
    A = np.ones((h, w), np.float32)
    A[ys, xs] = C.ALFA
    C.HEEFT_ALFA = bool((A < 0.999).any())
    if C.HEEFT_ALFA:
        K = np.concatenate([K, A[..., None]], 2)
    Nimg = dilateer(Nimg.astype(np.float32), mask, 10)
    ORM = dilateer(ORM, mask, 10)
    kleur = bewaar(K, C.naam + "_kleur", False, jpg=K.shape[2] == 3)
    normaal = bewaar(Nimg, C.naam + "_normaal", True)
    orm = bewaar(ORM[::2, ::2] if RES >= 2048 else ORM, C.naam + "_orm", True)
    log("texturen", f"{time.time() - t1:.1f}s")
    return kleur, normaal, orm


GLTF_GROEP = None




def gltf_groep():
    global GLTF_GROEP
    if GLTF_GROEP is None:
        GLTF_GROEP = bpy.data.node_groups.new("glTF Material Output", "ShaderNodeTree")
        GLTF_GROEP.interface.new_socket("Occlusion", in_out="INPUT", socket_type="NodeSocketFloat")
    return GLTF_GROEP


def pbr(naam, kleur, nrm, orm_img, tint=(1, 1, 1), alfa=False):
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
    m.use_backface_culling = not alfa
    if alfa:                                                      # glTF alphaMode MASK (afronden = knip op 0,5)
        rd = nt.nodes.new("ShaderNodeMath")
        rd.operation = "ROUND"
        nt.links.new(t.outputs["Alpha"], rd.inputs[0])
        nt.links.new(rd.outputs[0], b.inputs["Alpha"])
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
        if naam in C.TINTBAAR:
            sl = C.TINTBAAR[naam]
            mn = C.extra.get("mat", {}).get(naam, "mat_" + naam)
            if mn not in cache:
                cache[mn] = pbr(mn, kleur, normaal, orm, tuple(np.clip(C.KLEUR[sl] / GRIJS, 0, 1)),
                                alfa=(C.soort(naam) == "haar" and getattr(C, "HEEFT_ALFA", False) and
                                      bool(np.isin(reg, (KAART_REGIO,)).any())))
            me.materials.append(cache[mn])
            me.materials.append(vast)
            idx = np.isin(reg, C.VAST.get(naam, ())).astype(np.int32)
        else:
            me.materials.append(vast)
            idx = np.zeros(len(reg), np.int32)
        me.polygons.foreach_set("material_index", idx)
        if naam in C.TINTBAAR:
            log("  tint", naam, hexkleur(np.clip(C.KLEUR[C.TINTBAAR[naam]] / GRIJS, 0, 1)))


# --- Platte materialen (silhouetrondes) ---------------------------------------------------------
def vlak_mat(naam, kleur, ruw=0.8):
    m = bpy.data.materials.new(naam)
    m.use_nodes = True
    bs = m.node_tree.nodes["Principled BSDF"]
    bs.inputs["Base Color"].default_value = (*kleur, 1)
    bs.inputs["Roughness"].default_value = ruw
    m.use_backface_culling = True
    return m


def vlakke_kleuren(delen):
    tabel = C.extra.get("vlak", {})
    for naam, o in delen.items():
        o.data.materials.clear()
        for k in tabel.get(naam, [C.TINTBAAR.get(naam, "huid")]):
            o.data.materials.append(vlak_mat(naam + "_" + k, C.KLEUR[k], 0.35 if k == "gesp" else 0.8))
        reg = np.zeros(len(o.data.polygons), np.int32)
        o.data.attributes["regio"].data.foreach_get("value", reg)
        idx = np.minimum(reg, len(o.data.materials) - 1)
        if naam == "lijf":                                        # oogbollen/tanden wit
            o.data.materials.append(vlak_mat("lijf_oog", srgb("#e8e0d4"), 0.2))
            idx = np.where(reg == 3, len(o.data.materials) - 1, idx)
        o.data.polygons.foreach_set("material_index", idx)


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


UNITS = os.path.join(SCRATCH, "Unity_bumpkins", "Bumpkins", "Assets", "Resources", "Sprites-HD", "Units")
CONCEPT = os.path.join(SCRATCH, "concept")
PORTRET = os.path.join(SCRATCH, "bb_original", "portret")


def sprite_hd(naam):
    """HD-sprite (43,8 px/m) uit Unity; de man gebruikt zijn eigen frames/<naam>_hd_x2 (2x HD)."""
    pad = os.path.join(REF, "frames", naam + "_hd_x2.png")
    if os.path.exists(pad):
        return bijsnijden(laad_np(pad))[::2, ::2]
    return bijsnijden(laad_np(os.path.join(UNITS, naam + ".png")))


def schaal(a, h):
    """Herschaal (bilineair genoeg: box via index) naar hoogte h."""
    f = h / a.shape[0]
    w = max(1, int(round(a.shape[1] * f)))
    yi = np.clip((np.arange(h) / f).astype(int), 0, a.shape[0] - 1)
    xi = np.clip((np.arange(w) / f).astype(int), 0, a.shape[1] - 1)
    out = a[yi][:, xi]
    if out.shape[2] == 3:
        out = np.concatenate([out, np.ones((*out.shape[:2], 1), np.float32)], 2)
    return out


def verberg_props(sc, behalve=()):
    for o in sc.objects:
        if o.name.startswith("prop_") and o.name not in behalve:
            o.hide_render = True


def vergelijk(sc, rig, tag="", sk=None):
    """Sprite naast de render in een rustige stand (armen langs het lijf, zoals m_still); plus concept,
    portret en gezicht dichtbij. Bevat originele sprites/portretten: *_vergelijk*.png, nooit committen."""
    os.makedirs(PREV, exist_ok=True)
    if rig:
        rig.animation_data_create().action = None
        pose(rig, STAND)
        va = C.extra.get("vergelijk_actie")
        if va:                                                    # ouderen: idle met de staf in de hand
            ad = rig.animation_data
            ad.action = bpy.data.actions[va[0]]
            if getattr(ad, "action_slot", None) is None and len(getattr(ad.action, "slots", [])):
                ad.action_slot = ad.action.slots[0]
            sc.frame_set(va[1])
    verberg_props(sc, C.extra.get("zichtbare_props", ("prop_strootje",)))
    tmp = bpy.app.tempdir
    H = rig.get("hoogte", 1.37) if rig else 1.37
    zc = 0.72 * H / 1.37
    spr = sprite_hd(C.SPRITES[0])
    walk = sprite_hd(C.SPRITES[1])
    studio(sc, 43.8, 1.0, 1.6, doel=(0, 0, zc))
    r_se = bijsnijden(render_np(sc, os.path.join(tmp, "r_se.png")))
    studio(sc, 43.8, 1.0, 1.6, doel=(0, 0, zc), yaw=315)
    r_sw = bijsnijden(render_np(sc, os.path.join(tmp, "r_sw.png")))
    k = 6
    rij = plak([nn(spr, k), nn(r_se, k), nn(r_sw, k), nn(walk, k)])
    schrijf(rij, os.path.join(PREV, f"{C.naam}_vergelijk_1x{tag}.png"))
    studio(sc, 420, 0.8, 1.55, doel=(0, 0, zc))
    big = [bijsnijden(render_np(sc, os.path.join(tmp, "c_se.png")))]
    for yw in (270, 0, 45):
        studio(sc, 300, 0.8, 1.55, doel=(0, 0, zc), yaw=yw, pitch=15)
        big.append(bijsnijden(render_np(sc, os.path.join(tmp, f"c_{yw}.png"))))
    panelen = [nn(spr, 5)] + big
    cpad = os.path.join(CONCEPT, "img", C.naam + ".jpg")
    if os.path.exists(cpad):
        panelen.append(schaal(laad_np(cpad), big[0].shape[0]))
    schrijf(plak(panelen), os.path.join(PREV, f"{C.naam}_vergelijk_close{tag}.png"))
    # gezicht dichtbij naast het portret (origineel en concept)
    kz = sk.kop.C[2] if sk is not None else 1.17
    kh = sk.kop.k if sk is not None else 1.0
    w = 0.45 * kh
    studio(sc, 1600 / kh, w, w, doel=(0, -0.05, kz + 0.01), yaw=250, pitch=12)
    kop = render_np(sc, os.path.join(tmp, "kop.png"))
    studio(sc, 1600 / kh, w, w, doel=(0, -0.05, kz + 0.01), yaw=270, pitch=5)
    kop2 = render_np(sc, os.path.join(tmp, "kop2.png"))
    kp = [kop2, kop]
    bust = C.extra.get("bust")
    if bust:
        kp.append(schaal(laad_np(os.path.join(PORTRET, bust + ".png")), kop.shape[0]))
    ppad = os.path.join(CONCEPT, "portret", C.naam + ".png")
    if os.path.exists(ppad):
        kp.append(schaal(laad_np(ppad), kop.shape[0]))
    if C.naam != "man":
        schrijf(plak(kp), os.path.join(PREV, f"{C.naam}_vergelijk_kop{tag}.png"))
    if C.naam == "man":
        studio(sc, 1600, 0.45, 0.45, doel=(0, -0.05, 1.17), yaw=250, pitch=12)
        kop = render_np(sc, os.path.join(tmp, "kop.png"))
        studio(sc, 1600, 0.45, 0.45, doel=(-0.18, 0, 0.55), yaw=225, pitch=25)
        hand = render_np(sc, os.path.join(tmp, "hand.png"))
        studio(sc, 1600, 0.45, 0.45, doel=(-0.09, -0.05, 0.1), yaw=235, pitch=25)
        voet = render_np(sc, os.path.join(tmp, "voet.png"))
        schrijf(plak([kop, hand, voet]), os.path.join(PREV, f"man_detail{tag}.png"))
    # eigen render (zonder origineel) voor de commit: 3/4 iso op spelschaal x6 en dichtbij
    schrijf(plak([nn(r_se, k), nn(r_sw, k)] + big), os.path.join(PREV, f"{C.naam}_render{tag}.png"))


def poses(sc, rig, tag=""):
    """Extreme standen uit de animaties, iso en van voren-opzij."""
    keuzes = [("idle", 0), ("lopen", 3), ("lopen", 15), ("bouwen", 0), ("bouwen", 11),
              ("aanval_zwaard", 6), ("aanval_zwaard", 10), ("aanval_steen", 8), ("aanval_steen", 16),
              ("zagen", 0), ("zagen", 10), ("dragen", 0)]
    props = [o for o in sc.objects if o.name.startswith("prop_") and o.name != "prop_strootje"
             and o.name not in C.extra.get("zichtbare_props", ())]
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
                                     (act == "aanval_steen" and "steen" in p.name) or
                                     (act == "zagen" and "zaag" in p.name))
            sc.frame_set(f)
            studio(sc, 260, 1.5, 1.9, doel=(0, -0.1, 0.8 * rig.get("hoogte", 1.37) / 1.37), yaw=yaw, pitch=pitch)
            panelen.append(bijsnijden(render_np(sc, os.path.join(tmp, f"p_{act}_{f}.png"))))
        rijen.append(plak(panelen))
    schrijf(onder(*rijen), os.path.join(PREV, f"{C.naam}_poses{tag}.png"))
    rig.animation_data.action = None




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


def bouw_personage(p):
    """De hele straat voor een personage: rig, delen, bake, texturen, materialen, gewichten, props,
    animaties, export, previews."""
    global C
    C = p
    bpy.ops.wm.read_factory_settings(use_empty=True)
    sc = bpy.context.scene
    sc.render.fps = R.FPS
    sc.frame_start = 0
    coll = sc.collection
    maat = dict(p.MAAT)
    maat.update({k: float(v) for k, v in OPTS.items() if k in ("hoogte", "kop", "schouder", "been")})
    rig = R.bouw_rig(maat)
    sk = Skelet(rig)
    delen = p.bouw(sk, coll)
    for naam, o in delen.items():
        if p.soort(naam) in LAAG:
            LAAG[p.soort(naam)](o, sk, naam)
    log("driehoeken", driehoeken(delen.values()), {k: driehoeken([o]) for k, o in delen.items()})
    if VLAK:
        vlakke_kleuren(delen)
    else:
        B, mpp = bak_alles(delen, sk, coll)
        kleur, normaal, orm = texturen(B, mpp, sk)
        materialen(delen, kleur, normaal, orm)
    prop_delen = p.extra.get("prop_delen", {})            # deel -> bot: star aan een socket, niet geskind
    for naam, o in delen.items():
        if naam not in prop_delen:
            gewichten(o, sk, naam)
        me = o.data
        me.uv_layers.active = me.uv_layers.get("UVMap") or me.uv_layers[0]
        if "UVm" in me.uv_layers and "UVMap" in me.uv_layers:
            me.uv_layers.remove(me.uv_layers["UVm"])
        for a in ("regio", "deel"):
            if a in me.attributes:
                me.attributes.remove(me.attributes[a])
    objs = [o for n_, o in delen.items() if n_ not in prop_delen]
    for o in objs:
        o.parent = rig
        m = o.modifiers.new("Armature", "ARMATURE")
        m.object = rig
    for naam, bot in prop_delen.items():
        o = delen[naam]
        o.parent = rig
        o.parent_type = "BONE"
        o.parent_bone = bot
        bpy.context.view_layer.update()
        o.matrix_world = Matrix.Identity(4)
    log("LOD0 driehoeken", driehoeken(delen.values()), {o.name: driehoeken([o]) for o in delen.values()})
    # props van de rig op prop_R, zoals bumpkin_test.glb
    for pn, fn in (("prop_hamer", R.maak_hamer), ("prop_zwaard", R.maak_zwaard), ("prop_steen", R.maak_steen),
                   ("prop_zaag", R.maak_zaag)):
        ob = fn(pn)
        ob.parent = rig
        ob.parent_type = "BONE"
        ob.parent_bone = "prop_R"
        ob.location = (0, -rig.data.bones["prop_R"].length, 0)
    if p.PROPS:
        p.PROPS(sk, rig, delen)
    info = R.bouw_animaties(rig)
    if p.NA_ANIMATIE:
        p.NA_ANIMATIE(rig)
    log("animaties", list(info))
    if "geen_export" not in OPTS:
        ontkies()
        bpy.ops.export_scene.gltf(filepath=p.GLB, export_format="GLB", export_animations=True,
                                  export_animation_mode="ACTIONS", export_force_sampling=True, export_yup=True,
                                  export_skins=True, export_def_bones=False, export_extras=True, use_selection=False,
                                  export_tangents=True, export_image_format="AUTO", export_cameras=False,
                                  export_lights=False)
        log("export", p.GLB, f"{os.path.getsize(p.GLB) / 1e6:.1f} MB")
    tag = OPTS.get("tag", "")
    if "vergelijk" in OPTS:
        vergelijk(sc, rig, tag, sk)
    if "poses" in OPTS:
        poses(sc, rig, tag)
    bpy.ops.wm.save_as_mainfile(filepath=os.path.join(HERE, "preview", f"bumpkin_{p.naam}.blend"))
    log("KLAAR")
    return rig, sk, delen


# --- Houding als additief op de clips (ouderen) -------------------------------------------------
def fcurves(act):
    """Alle F-curves van een actie (Blender 5: gelaagde acties met channelbags)."""
    try:
        return list(act.fcurves)
    except AttributeError:
        pass
    out = []
    for lay in act.layers:
        for st in lay.strips:
            for cb in st.channelbags:
                out += list(cb.fcurves)
    return out


def houding_additief(rig, extra, acties=None):
    """Draait per bot een vaste lokale rotatie (graden, XYZ-euler) achter elke sleutel van elke actie:
    q_nieuw = q_clip @ q_extra. Zelfde zes clips, zelfde timing; alleen de houding verschuift."""
    add = {b: Euler([math.radians(x) for x in e], "XYZ").to_quaternion() for b, e in extra.items()}
    for act in bpy.data.actions:
        if acties and act.name not in acties:
            continue
        per = {}
        for fc in fcurves(act):
            for b in add:
                if fc.data_path == f'pose.bones["{b}"].rotation_quaternion':
                    per.setdefault(b, {})[fc.array_index] = fc
        for b, fcs in per.items():
            if len(fcs) < 4:
                continue
            n = len(fcs[0].keyframe_points)
            for i in range(n):
                q = Quaternion([fcs[j].keyframe_points[i].co[1] for j in range(4)])
                q2 = q @ add[b]
                for j in range(4):
                    kp = fcs[j].keyframe_points[i]
                    d = q2[j] - kp.co[1]
                    kp.co[1] = q2[j]
                    kp.handle_left[1] += d
                    kp.handle_right[1] += d
            for fc in fcs.values():
                fc.update()
        act["houding"] = (act.get("houding", "") + " " + str(extra)).strip()
    log("houding additief", extra)
