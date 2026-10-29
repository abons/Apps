"""Molen uit Beasts & Bumpkins nagebouwd in 3D.

Lang laag huisje met een bol goudgeel rieten dak, een gekalkte gevel met rondboogdeur en
klimplanten, een planken zijwand met kleine ramen, een vleugel naar voren met de molendeur en een
ronde stenen schoorsteen. Uit het dak rijst een vierkante stenen voet met een grote achtkantige
houten kap; vier paars-wit gestreepte wieken op het rechtsvoorvlak (-Y) van de kap. De wieken hangen
onder het lege object `wieken`: hun as is de lokale Z van dat object (Godot: lokale Y).
Maten teruggerekend uit mill.png + millsails.png (87,5 px per meter op 4x), uitwerking naar de
goedgekeurde concepten (molen.jpg; de gevel van molen_v3.jpg).

Draaien (headless):
  blender -b -P molen.py -- [schaal=4] [snel] [geen_glb] [geen_render] [deur=graden] [wieken=graden]
Schrijft molen.blend en molen.glb naast dit script en preview/molen_render.png.
"""
import math
import os
import random
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from loods_molen_lib import *  # noqa: E402,F401,F403
from mathutils import Matrix, Vector  # noqa: E402

NAAM = "molen"
SPRITE = SC + "gb/mill_sprite.png"     # mill.png met millsails.png erop, 820 x 740 (4x)
W_PX, H_PX = 820, 740
REF_PX = (300, 735)                    # voet van de hoek gevel/zijwand in de sprite

# --- Maten (meters; lokaal: hoek gevel/zijwand op de oorsprong, gevel op x = 0 kijkt naar -X,
# zijwand op y = 0 kijkt naar -Y) ----------------------------------------------------------------
HX1, HY1 = 4.0, 3.1                    # hoofdhuis x 0..4, y 0..3,1
VX0, VX1, VY0 = 4.0, 5.7, -1.3         # vleugel naar voren: x 4..5,7, y -1,3..3,1
WAND_H = 1.82                          # tot de dakvoet
DAK_Z0, DAK_H, DAK_D = 1.72, 1.7, 1.95 # dakrand, opbolling, afstand rand -> vlak bovenop
DAK_DIK = 0.34
RAND_X0, RAND_X1 = -0.38, 6.05         # dak over de gevels heen
RAND_YB = HY1 + 0.42                   # achterrand
RAND_YV, RAND_YW = -0.42, VY0 - 0.42   # voorrand hoofdhuis, vleugel
OVERGANG = (3.25, 4.0)                 # voorrand loopt hier rond naar de vleugel
TOREN = (4.55, 1.15)                   # midden van de stenen voet en de kap
VOET_ZIJ, VOET_Z0, VOET_Z1 = 2.7, 2.4, 4.1
KAP_R0, KAP_R1, KAP_Z1 = 1.6, 1.78, 5.5       # omgeschreven straal onder, boven: wijkt uit naar boven
KAP_HELLING = math.radians(7)          # kapdak loopt af naar achter (+Y)
HUB_X, HUB_Z = 4.45, 4.85              # as van de wieken op het -Y-vlak
WIEK_L, WIEK_B, WIEK_R0 = 3.0, 0.62, 0.5
AS_UIT = 1.05                          # as steekt ver uit: de draaiende wieken blijven vrij van het riet
SCHOORSTEEN = (1.3, 1.45)
GEVEL_DEUR = (1.86, 0.86, 1.78)        # y, breedte, hoogte (rondboog)
MOLENDEUR = (4.55, 0.82, 1.72)         # x, breedte, hoogte (recht, op de vleugel)
RAMEN = (0.72, 1.78, 2.95)             # x van de drie raampjes in de zijwand
OX, OY = 2.85, 0.9                     # verschuiving naar het midden (spel-oorsprong)

# --- Materialen --------------------------------------------------------------------------------
M_STEEN = mat_steen("steen", lo=(0.05, 0.05, 0.045), hi=(0.55, 0.53, 0.46), moss=0.6, lichen=0.9)
M_SCHOOR = mat_steen("schoorsteensteen", lo=(0.04, 0.04, 0.035), hi=(0.5, 0.49, 0.42), moss=0.5)
M_STOEP = mat_steen("stoep", lo=(0.12, 0.12, 0.10), hi=(0.55, 0.54, 0.47), moss=0.4)
M_SPECIE = mat_specie("specie", (0.06, 0.05, 0.04), (0.18, 0.16, 0.12))
M_BALK = mat_hout("balk", "rough_wood", (0.08, 0.045, 0.02), (0.36, 0.23, 0.12), rand=5.0, grijs=0.4)
M_PLANK = mat_hout("plank", "weathered_brown_planks", (0.10, 0.06, 0.03), (0.42, 0.28, 0.15), 0.5, 5.0, grijs=0.5)
M_PLANK_V = mat_hout("plank_v", "weathered_brown_planks", (0.07, 0.035, 0.015), (0.32, 0.18, 0.08), 0.5, 5.0,
                     rot=math.pi / 2)
M_KAP = mat_hout("kaphout", "weathered_brown_planks", (0.13, 0.06, 0.02), (0.55, 0.30, 0.12), 0.45, 7.0,
                 rot=math.pi / 2, grijs=0.25)
M_KAPDAK = mat_hout("kapdak", "weathered_brown_planks", (0.13, 0.07, 0.03), (0.52, 0.32, 0.15), 0.45, 7.0,
                    grijs=0.4)
M_PLEISTER = mat_pleister("pleister", wit=(0.8, 0.79, 0.74), vuil=(0.3, 0.26, 0.19), afbladder=0.58)
M_IJZER = mat_flat("beslag", (0.02, 0.02, 0.02), 0.45, "ijzer")
M_NAAF = mat_ijzer("naaf")
M_RUIT = mat_ruit("ruit")
M_DOEK = mat_doek("doek")
M_HALM = mat_halm("halm", [(0.0, (0.28, 0.1, 0.01)), (0.3, (0.66, 0.34, 0.04)), (0.55, (0.9, 0.56, 0.1)),
                            (0.8, (0.98, 0.7, 0.22)), (1.0, (1.0, 0.84, 0.42))], verweerd=0.45)
M_RIET = mat_rietlaag("riet")
M_GRAS = mat_gras("gras")
M_BLAD = mat_blad("blad", (0.03, 0.10, 0.02), (0.16, 0.32, 0.05))
M_RANK = mat_hout("rank", "rough_wood", (0.05, 0.03, 0.015), (0.2, 0.12, 0.06), 2.0)
M_DONKER = mat_flat("donker", (0.01, 0.008, 0.006), 0.95)
M_JUTE = mat_hout("jute", "rough_wood", (0.10, 0.07, 0.04), (0.30, 0.22, 0.12), 3.0, 2.0)
stenen_maken(M_STEEN, p=7.0, bumps=0.1)


# --- Dakvorm: een bolle rieten deken over de L-vormige plattegrond -----------------------------
def smooth(a, b, x):
    t = min(max((x - a) / (b - a), 0.0), 1.0)
    return t * t * (3 - 2 * t)


def voorrand(x):
    return RAND_YV + (RAND_YW - RAND_YV) * smooth(*OVERGANG, x)


def vorm(s):
    """Doorsnede: 0 aan de rand, 1 bovenop; steil midden, zacht naar de rand en de top."""
    s = min(max(s, 0.0), 1.0)
    return 0.9 * s + 1.2 * s * s - 1.1 * s ** 3


def dak_punt(x, t):
    """(x, t) -> punt op het dak; t = 0 voorrand, 1 achterrand."""
    yf = voorrand(x)
    y = yf + (RAND_YB - yf) * t
    d = min(y - yf, RAND_YB - y)
    return Vector((x, y, DAK_Z0 + DAK_H * vorm(d / DAK_D)))


def dak_z(x, y):
    yf = voorrand(x)
    d = min(y - yf, RAND_YB - y)
    return DAK_Z0 + DAK_H * vorm(d / DAK_D)


def dak_normaal(x, t):
    e = 0.01
    p = dak_punt(x, t)
    a = dak_punt(x + e, t) - p
    b = dak_punt(x, t + e) - p
    n = a.cross(b).normalized()
    return n if n.z > 0 else -n


NX, NT = 72, 56
vs, fs = [], []
for i in range(NX + 1):
    x = RAND_X0 + (RAND_X1 - RAND_X0) * i / NX
    for j in range(NT + 1):
        vs.append(tuple(dak_punt(x, j / NT)))
for i in range(NX):
    for j in range(NT):
        k = i * (NT + 1) + j
        fs.append([k, k + NT + 1, k + NT + 2, k + 1])
dak = mesh_obj("dak", vs, fs, M_RIET)
s_ = dak.modifiers.new("dik", "SOLIDIFY")
s_.thickness = DAK_DIK
s_.offset = -1.0
bv_ = dak.modifiers.new("rond", "BEVEL")
bv_.width, bv_.segments = 0.13, 4

# --- Halmen: lagen evenwijdig aan de rand, halmen de helling af (hair curves) --------------------
rnd = random.Random(11)
halm_c, halm_b = [], []
BOS_DX = 0.068 if not SNEL else 0.14
PER_BOS = 14 if not SNEL else 6


def halm(x, d_top, L, kant, hang, lift, lean):
    """Een halm van afstand-tot-de-rand d_top omlaag over L (meter, langs de helling)."""
    pts = []
    yf = voorrand(x)
    breed = RAND_YB - yf
    for k in range(8):
        u = k / 7
        d = max(d_top - L * u, 0.0)
        t = d / breed if kant < 0 else 1 - d / breed
        p = dak_punt(x + lean * u, t)
        n = dak_normaal(x + lean * u, t)
        off = -0.02 + lift + 0.07 * u ** 0.9
        pts.append(p + n * off)
    if hang:
        d7 = (pts[-1] - pts[-2]).normalized()
        for f in (0.5, 1.0):
            pts.append(pts[-1] + d7 * hang * 0.5 + Vector((0, 0, -0.35 * hang * f)))
    else:
        pts += [pts[-1] + (pts[-1] - pts[-2]) * 0.01, pts[-1] + (pts[-1] - pts[-2]) * 0.02]
    return [tuple(p) for p in pts]


x = RAND_X0 + 0.02
while x < RAND_X1 - 0.02:
    yf = voorrand(x)
    breed = RAND_YB - yf
    for kant in (-1, 1):
        dmax = breed / 2 if kant < 0 else breed / 2
        dtop = dmax + 0.1
        while dtop > 0.15:
            L = rnd.uniform(0.75, 0.95)
            bos = rnd.random()
            bol = rnd.uniform(0.0, 0.02)              # bos ligt wat hoger of lager: rul, geen kam
            schuin = rnd.gauss(0, 0.05)               # hele bos iets scheef gelegd
            for _ in range(PER_BOS):
                xi = x + rnd.gauss(0, 0.024)
                di = dtop + rnd.uniform(-0.04, 0.04)
                Lb = L * rnd.uniform(0.9, 1.05)
                hang = 0.0
                if di - Lb < 0.0:
                    hang = rnd.uniform(0.0, 0.12) * rnd.random() ** 0.5
                halm_c.append(halm(xi, di, min(Lb, di), kant, hang, bol + rnd.uniform(0, 0.025), schuin + rnd.gauss(0, 0.04)))
                halm_b.append(bos)
            dtop -= rnd.uniform(0.26, 0.34)
    x += BOS_DX * rnd.uniform(0.85, 1.15)
# gevelrand (x = RAND_X0): halmen dwars over de rand gekamd en omlaag, zodat de doorsnede dicht is
for x_rand, sgn in ((RAND_X0, -1), (RAND_X1, 1)):
    t = 0.0
    while t < 1.0:
        bos = rnd.random()
        for _ in range(9 if not SNEL else 4):
            ti = t + rnd.gauss(0, 0.006)
            hang = rnd.uniform(0.04, 0.16)
            pts = []
            for k in range(10):
                u = k / 9
                xx = x_rand - sgn * rnd.uniform(0.3, 0.42) * (1 - min(u / 0.7, 1.0))
                p = dak_punt(min(max(xx, RAND_X0), RAND_X1), ti) + Vector((0, 0, 0.03 + 0.02 * u))
                if u > 0.6:
                    p += Vector((sgn * 0.04 * (u - 0.6) / 0.4, 0, -(u - 0.6) / 0.4 * (DAK_DIK * 0.7 + hang)))
                pts.append(tuple(p))
            halm_c.append(pts)
            halm_b.append(bos)
        t += 0.012
riet = strands("dakhalmen", halm_c, M_HALM, halm_b, lambda u: 0.0062 - 0.0018 * u)

# --- Gevel (x = 0): gekalkt pleister met rondboogdeur, hoekstijlen, klimplanten -----------------
def gevel_top(y):
    return dak_z(0.0, y) - DAK_DIK - 0.02


gy, gb, gh = GEVEL_DEUR
gzc = gh - gb / 2
strips = 48
vs, fs = [], []
for i in range(strips + 1):
    y = 0.05 + (HY1 - 0.1) * i / strips
    top = gevel_top(y)
    dy = abs(y - gy)
    if dy < gb / 2 + 0.04:
        bot = gzc + math.sqrt(max((gb / 2 + 0.04) ** 2 - dy * dy, 0.0))
    else:
        bot = 0.0
    vs += [(0.0, y, bot), (0.0, y, (bot + top) / 2), (0.0, y, top)]
for i in range(strips):
    a = 3 * i
    fs += [[a, a + 3, a + 4, a + 1], [a + 1, a + 4, a + 5, a + 2]]
gevel = mesh_obj("gevel", vs, fs, M_PLEISTER, smooth=False)
s_ = gevel.modifiers.new("dik", "SOLIDIFY")
s_.thickness = 0.2
s_.offset = 1.0                                   # naar binnen (+X): de ranken liggen ervoor
# deurposten van de opening (de strips laten een spleet onder de boog): kant van de opening dicht
box("negge", (0.12, gy - gb / 2 - 0.05, gzc / 2), (0.2, 0.04, gzc), M_PLEISTER)
box("negge", (0.12, gy + gb / 2 + 0.05, gzc / 2), (0.2, 0.04, gzc), M_PLEISTER)
box("gevelgat", (0.25, gy, gh / 2), (0.05, gb + 0.1, gh + 0.05), M_DONKER)
# houten boogkozijn om de deur
n = 14
for k in range(n):
    a0, a1 = math.pi * k / n, math.pi * (k + 1) / n
    r = gb / 2 + 0.07
    p0 = (-0.03, gy + r * math.cos(a0), gzc + r * math.sin(a0))
    p1 = (-0.03, gy + r * math.cos(a1), gzc + r * math.sin(a1))
    balk("boogkozijn", p0, p1, 0.12, 0.1, M_BALK, bevel=0.01)
for s in (-1, 1):
    balk("deurstijl", (-0.03, gy + s * (gb / 2 + 0.07), 0.0), (-0.03, gy + s * (gb / 2 + 0.07), gzc), 0.12, 0.12, M_BALK,
         ruw=0.008)
delen = plank_door("gevelplank", -0.0, gy, 0.05, gb, gh - 0.05, math.pi, M_PLANK_V, M_IJZER, n=5)
scharnier("deur_gevel", delen, 0.0, gy, gb, math.pi)
stone((-0.4, gy, 0.0), (0.5, 1.0, 0.12), 0.04, M_STOEP)
# hoekstijlen en de gebogen windveer langs de dakrand
for y in (0.0, HY1):
    balk("hoekstijl", (-0.02, y, 0.0), (-0.02, y, gevel_top(y) + 0.05), 0.2, 0.2, M_BALK, ruw=0.012)
prev = None
for i in range(25):
    y = 0.0 + HY1 * i / 24
    p = Vector((-0.06, y, gevel_top(y) + 0.06))
    if prev is not None:
        balk("windveer", prev, p, 0.07, 0.16, M_BALK, bevel=0.01, ruw=0.004)
    prev = p
box("voetlijst", (-0.02, HY1 / 2, 0.1), (0.1, HY1, 0.2), M_STEEN)

# klimplant: ranken die van de grond omhoog kronkelen langs de deur en over de gevel
rr = random.Random(5)


def rank(y0, z1, seed):
    r = random.Random(seed)
    pts = [Vector((-0.03, y0, 0.0))]
    y, z = y0, 0.0
    while z < z1:
        z += r.uniform(0.08, 0.14)
        y += r.uniform(-0.07, 0.07)
        y = min(max(y, 0.1), HY1 - 0.1)
        if abs(y - gy) < gb / 2 + 0.12 and z < gzc + gb / 2 + 0.15:
            y = gy + math.copysign(gb / 2 + 0.14, y - gy)
        pts.append(Vector((-0.03 - r.uniform(0, 0.02), y, z)))
    for a, b in zip(pts, pts[1:]):
        balk("rank", a, b, 0.03, 0.028, M_RANK, bevel=0.0)
        if r.random() < 0.8:                          # zijtakje met blaadjes
            for _ in range(r.randint(3, 6)):
                bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=1, radius=r.uniform(0.06, 0.09),
                                                      location=(b.x - 0.025, b.y + r.uniform(-0.12, 0.12),
                                                                b.z + r.uniform(-0.08, 0.08)))
                o = bpy.context.object
                o.name = "blad"
                o.scale = (0.25, 1.0, 0.75)
                o.rotation_euler = (r.uniform(-0.8, 0.8), 0, r.uniform(-0.3, 0.3))
                put(o, M_BLAD, smooth=False)
    return pts


for k, (y0, z1) in enumerate(((gy - gb / 2 - 0.2, 2.2), (gy + gb / 2 + 0.2, 2.3), (0.35, 1.3), (2.85, 1.5),
                              (gy - gb / 2 - 0.35, 1.0), (gy + gb / 2 + 0.4, 1.6), (1.2, 2.4), (2.3, 2.1))):
    rank(y0, z1, 40 + k)

# --- Zijwand (y = 0) en vleugel: planken onder, pleister met raampjes onder de dakvoet --------------
def planken_wand(p0, p1, z0, z1, mat=M_PLANK, gaten=()):
    """Liggende overnaadse planken van p0 naar p1 (x, y); gaten = (t0, t1) waar geen plank komt."""
    d = Vector((p1[0] - p0[0], p1[1] - p0[1], 0))
    L = d.length
    d.normalize()
    nrm = Vector((d.y, -d.x, 0))
    ang = math.atan2(d.y, d.x)
    z = z0
    while z < z1 - 0.02:
        h = random.uniform(0.17, 0.23)
        t = 0.0
        while t < L - 0.01:
            seg = min(random.uniform(1.2, 2.6), L - t)
            vrij = [(a, b) for (a, b) in [(t, t + seg)]]
            for g0, g1, gz0, gz1 in gaten:
                if z < gz1 and z + h > gz0:
                    nv = []
                    for a, b in vrij:
                        if b <= g0 or a >= g1:
                            nv.append((a, b))
                        else:
                            if a < g0:
                                nv.append((a, g0))
                            if b > g1:
                                nv.append((g1, b))
                    vrij = nv
            for a, b in vrij:
                if b - a < 0.05:
                    continue
                tm = (a + b) / 2
                o = random.uniform(0.0, 0.012)
                pc = Vector((p0[0], p0[1], 0)) + d * tm + nrm * (0.02 + o)
                pl = box("plank", (pc.x, pc.y, z + h / 2), (b - a - 0.006, 0.03, h + 0.03), mat, bevel=0.006)
                pl.rotation_euler = (0, 0, ang)
                pl.rotation_euler.rotate_axis("X", -0.06 + random.uniform(-0.015, 0.015))   # overnaads
                pl.data.transform(Matrix.Identity(4))
            t += seg
        z += h


VOET = 0.2
ZB = 1.12                                       # bovenkant planken, daarboven pleister en raampjes
# stenen voet onder de zijwand en de vleugel
flat_wall((0.1, -0.02), (HX1, -0.02), 0.0, VOET, [], depth=0.2, hs=(0.08, 0.12), ls=(0.2, 0.36))
flat_wall((VX0 - 0.02, -0.05), (VX0 - 0.02, VY0 + 0.1), 0.0, VOET, [], depth=0.2, hs=(0.08, 0.12), ls=(0.2, 0.36))
planken_wand((0.08, 0.0), (HX1, 0.0), VOET, ZB)
planken_wand((VX0, 0.0), (VX0, VY0), VOET, ZB + 0.4)
box("kern", (HX1 / 2 + 0.1, HY1 / 2, WAND_H / 2), (HX1 - 0.1, HY1 - 0.1, WAND_H), M_SPECIE)
box("kern", ((VX0 + VX1) / 2, (VY0 + HY1) / 2, WAND_H / 2), (VX1 - VX0 - 0.06, HY1 - VY0 - 0.06, WAND_H), M_SPECIE)
# pleisterband met raampjes, stijlen ertussen
yv = 0.06
for x in [0.08] + [r for r in RAMEN] + [HX1 - 0.05]:
    pass
ram_b, ram_z0, ram_z1 = 0.62, ZB + 0.12, WAND_H - 0.12
xs = [0.1]
for xr in RAMEN:
    xs += [xr - ram_b / 2, xr + ram_b / 2]
xs.append(HX1 - 0.05)
for a, b in zip(xs[0::2], xs[1::2]):
    box("pleister", ((a + b) / 2, yv, (ZB + WAND_H) / 2), (b - a, 0.1, WAND_H - ZB), M_PLEISTER)
for xr in RAMEN:
    box("pleister", (xr, yv, (ZB + ram_z0) / 2), (ram_b, 0.1, ram_z0 - ZB), M_PLEISTER)
    box("pleister", (xr, yv, (ram_z1 + WAND_H) / 2), (ram_b, 0.1, WAND_H - ram_z1), M_PLEISTER)
    box("ruit", (xr, yv + 0.03, (ram_z0 + ram_z1) / 2), (ram_b, 0.02, ram_z1 - ram_z0), M_RUIT)
    for xx in (xr - ram_b / 2, xr, xr + ram_b / 2):
        balk("kozijn", (xx, -0.01, ram_z0), (xx, -0.01, ram_z1), 0.06 if xx == xr else 0.09, 0.08, M_BALK)
    for zz in (ram_z0, (ram_z0 + ram_z1) / 2, ram_z1):
        balk("kozijn", (xr - ram_b / 2, -0.01, zz), (xr + ram_b / 2, -0.01, zz), 0.06 if 0 < zz - ram_z0 < 0.3 else 0.09,
             0.08, M_BALK)
for x in (0.12, (RAMEN[0] + RAMEN[1]) / 2, (RAMEN[1] + RAMEN[2]) / 2, HX1 - 0.12):
    balk("stijl", (x, -0.03, ZB - 0.02), (x, -0.03, WAND_H), 0.14, 0.12, M_BALK, ruw=0.008)
balk("regel", (0.0, -0.04, ZB), (HX1, -0.04, ZB), 0.12, 0.1, M_BALK, ruw=0.008)
balk("muurplaat", (0.0, -0.04, WAND_H - 0.04), (HX1, -0.04, WAND_H - 0.04), 0.16, 0.12, M_BALK, ruw=0.008)
# -X-wand van de vleugel (x = 4): pleister boven de planken
box("pleister", (VX0 - 0.05, VY0 / 2, (ZB + 0.4 + WAND_H) / 2), (0.1, -VY0, WAND_H - ZB - 0.4), M_PLEISTER)
for y in (VY0, -0.05):
    balk("hoekstijl", (VX0 - 0.03, y, 0.0), (VX0 - 0.03, y, WAND_H + 0.05), 0.2, 0.2, M_BALK, ruw=0.012)
# voorkant van de vleugel (y = -1,3): molendeur, planken
mx, mb, mh = MOLENDEUR
t0 = mx - mb / 2 - 0.06 - VX0
planken_wand((VX0, VY0), (VX1, VY0), VOET, WAND_H, mat=M_PLANK, gaten=[(t0, t0 + mb + 0.12, 0.0, mh + 0.08)])
flat_wall((VX0 + 0.1, VY0 - 0.02), (VX1, VY0 - 0.02), 0.0, VOET, [(t0, t0 + mb + 0.12, -1, 1)], depth=0.2,
          hs=(0.08, 0.12), ls=(0.2, 0.36))
box("deurgat", (mx, VY0 + 0.12, mh / 2), (mb + 0.1, 0.05, mh), M_DONKER)
for s in (-1, 1):
    balk("deurstijl", (mx + s * (mb / 2 + 0.06), VY0 - 0.03, 0.0), (mx + s * (mb / 2 + 0.06), VY0 - 0.03, mh + 0.1), 0.12,
         0.12, M_BALK, ruw=0.008)
balk("latei", (mx - mb / 2 - 0.15, VY0 - 0.03, mh + 0.08), (mx + mb / 2 + 0.15, VY0 - 0.03, mh + 0.08), 0.14, 0.14,
     M_BALK, ruw=0.008)
delen = plank_door("deurplank", mx, VY0 + 0.0, 0.08, mb, mh - 0.06, -math.pi / 2, M_PLANK_V, M_IJZER, n=5, boog=False)
scharnier("deur", delen, mx, VY0 + 0.0, mb, -math.pi / 2)
stone((mx, VY0 - 0.38, 0.0), (1.0, 0.55, 0.13), 0.04, M_STOEP)
stone((mx + 0.15, VY0 - 0.8, -0.01), (0.7, 0.4, 0.1), -0.1, M_STOEP)
for x in (VX1 - 0.03,):
    balk("hoekstijl", (x, VY0 - 0.03, 0.0), (x, VY0 - 0.03, WAND_H + 0.05), 0.2, 0.2, M_BALK, ruw=0.012)
balk("muurplaat", (VX0, VY0 - 0.04, WAND_H - 0.04), (VX1, VY0 - 0.04, WAND_H - 0.04), 0.16, 0.12, M_BALK, ruw=0.008)
# zakken meel tegen de vleugel (molen): twee jute zakken
for k, (zx, zy) in enumerate(((5.25, VY0 - 0.35), (5.5, VY0 - 0.3))):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=16, ring_count=10, radius=0.2, location=(zx, zy, 0.24))
    o = bpy.context.object
    o.name = "zak"
    o.scale = (1.0, 0.8, 1.25)
    for v in o.data.vertices:                     # zak zakt uit: onder breder, boven dichtgebonden
        v.co.x *= 1 + 0.25 * max(0.0, -v.co.z) / 0.2
        v.co.y *= 1 + 0.25 * max(0.0, -v.co.z) / 0.2
    put(o, M_JUTE)

# --- Stenen voet en achtkantige kap -----------------------------------------------------------------------
tx, ty = TOREN
hz = VOET_ZIJ / 2
box("voetkern", (tx, ty, (VOET_Z0 + VOET_Z1) / 2), (VOET_ZIJ - 0.2, VOET_ZIJ - 0.2, VOET_Z1 - VOET_Z0), M_SPECIE)
flat_wall((tx - hz + 0.1, ty - hz + 0.08), (tx + hz, ty - hz + 0.08), VOET_Z0, VOET_Z1, [], depth=0.2, hs=(0.12, 0.18),
          ls=(0.25, 0.45), uit=0.004)
flat_wall((tx - hz + 0.08, ty + hz), (tx - hz + 0.08, ty - hz + 0.1), VOET_Z0, VOET_Z1, [], depth=0.2, hs=(0.12, 0.18),
          ls=(0.25, 0.45), uit=0.004)
for (p, q) in (((tx + hz - 0.08, ty - hz), (tx + hz - 0.08, ty + hz)), ((tx + hz, ty + hz - 0.08), (tx - hz, ty + hz - 0.08))):
    flat_wall(p, q, VOET_Z0, VOET_Z1, [], depth=0.2, hs=(0.14, 0.22), ls=(0.3, 0.5))


def kap_r(z):
    return KAP_R0 + (KAP_R1 - KAP_R0) * (z - VOET_Z1) / (KAP_Z1 - VOET_Z1)


# ligger (vloer van de kap) en planken per vlak; vlaknormalen op k * 45 graden, -Y is k = 6
bpy.ops.mesh.primitive_cylinder_add(vertices=8, radius=KAP_R0 - 0.05, depth=0.12, location=(tx, ty, VOET_Z1 + 0.06),
                                    rotation=(0, 0, math.pi / 8))
put(bpy.context.object, M_BALK, smooth=False).name = "kapvloer"
PLANKEN = 4
for k in range(8):
    an = math.radians(45 * k)
    nrm = Vector((math.cos(an), math.sin(an), 0))
    raak = Vector((-math.sin(an), math.cos(an), 0))
    for i in range(PLANKEN):
        u = (i + 0.5) / PLANKEN - 0.5
        z0, z1 = VOET_Z1 - random.uniform(0.0, 0.06), KAP_Z1 - 0.05 + random.uniform(-0.02, 0.03)
        uitp = random.uniform(0.0, 0.03)                     # ongelijke planken
        pts = []
        for z in (z0, z1):
            R = kap_r(z)
            ap = R * math.cos(math.pi / 8)
            hw = R * math.sin(math.pi / 8)
            pts.append(Vector((tx, ty, z)) + nrm * (ap + uitp) + raak * (u * 2 * hw))
        w = 2 * kap_r((z0 + z1) / 2) * math.sin(math.pi / 8) / PLANKEN - 0.01
        o = balk("kapplank", pts[0], pts[1], w, 0.04, M_KAP, bevel=0.006, rol=0.0)
        # balk() legt de breedte langs y van zijn eigen as; draai om de lengteas naar het vlak
        q = (pts[1] - pts[0]).normalized()
        M = Matrix((q, raak, q.cross(raak))).transposed()
        if M.col[2].dot(nrm) < 0:
            M = Matrix((q, -raak, q.cross(-raak))).transposed()
        o.rotation_quaternion = (M.to_4x4() @ Matrix.Rotation(random.uniform(-0.06, 0.06), 4, "X")).to_quaternion()
    # lijst onderaan en bovenaan het vlak
    for z, hh, uit in ((VOET_Z1 + 0.08, 0.14, 0.03), (KAP_Z1 + 0.01, 0.16, 0.05)):
        R = kap_r(z) + uit
        ap, hw = R * math.cos(math.pi / 8), R * math.sin(math.pi / 8)
        c = Vector((tx, ty, z)) + nrm * ap
        balk("kaplijst", c - raak * hw, c + raak * hw, 0.06, hh, M_BALK, bevel=0.008)
# kapdak: brede planken in de x-richting, licht aflopend naar achter, boeiplanken eromheen
A = KAP_R1 * math.cos(math.pi / 8) + 0.1
y = -A
while y < A:
    bw_ = random.uniform(0.26, 0.34)
    yc = y + bw_ / 2
    xm = min(A, A * math.sqrt(2) - abs(yc)) - 0.04
    if xm > 0.1:
        zc = KAP_Z1 + 0.04 - math.tan(KAP_HELLING) * yc + random.uniform(-0.008, 0.008)
        box("kapdakplank", (tx, ty + yc, zc), (2 * xm, bw_ - 0.015, 0.05), M_KAPDAK,
            rot=(-KAP_HELLING + random.uniform(-0.015, 0.015), random.uniform(-0.012, 0.012), 0), bevel=0.008)
    y += bw_
for k in range(8):                                  # boeiplank langs de dakrand
    an = math.radians(45 * k)
    nrm = Vector((math.cos(an), math.sin(an), 0))
    raak = Vector((-math.sin(an), math.cos(an), 0))
    ap, hw = (KAP_R1 + 0.08) * math.cos(math.pi / 8), (KAP_R1 + 0.08) * math.sin(math.pi / 8)
    c = Vector((tx, ty, 0)) + nrm * ap
    z0 = KAP_Z1 + 0.02 - math.tan(KAP_HELLING) * (c.y - ty)
    p, q = c - raak * hw, c + raak * hw
    p.z = KAP_Z1 + 0.02 - math.tan(KAP_HELLING) * (p.y - ty)
    q.z = KAP_Z1 + 0.02 - math.tan(KAP_HELLING) * (q.y - ty)
    balk("boeiplank", p, q, 0.05, 0.16, M_KAPDAK, bevel=0.008, ruw=0.004)
# kapring: zware balk rond de voet van de kap, sluit de spleet naar de stenen voet
bpy.ops.mesh.primitive_cylinder_add(vertices=8, radius=KAP_R0 + 0.06, depth=0.2, location=(tx, ty, VOET_Z1 + 0.02),
                                    rotation=(0, 0, math.pi / 8))
put(bpy.context.object, M_BALK, smooth=False).name = "kapring"
# asgat en as op het -Y-vlak
fy = ty - kap_r(HUB_Z) * math.cos(math.pi / 8)
cyl("asgat", (HUB_X, fy - 0.01, HUB_Z), 0.2, 0.05, M_DONKER, rot=(math.pi / 2, 0, 0), verts=20)
cyl("as", (HUB_X, fy - AS_UIT / 2, HUB_Z), 0.14, AS_UIT + 0.1, M_BALK, rot=(math.pi / 2, 0, 0), verts=16)

# --- Wieken onder het lege object `wieken` (as = lokale Z, naar -Y) --------------------------------
naaf_pos = Vector((HUB_X, fy - AS_UIT - 0.05, HUB_Z))
wk = bpy.data.objects.new("wieken", None)
wk.empty_display_type = "SINGLE_ARROW"
col.objects.link(wk)
wk.matrix_world = Matrix.Translation(naaf_pos) @ Matrix.Rotation(math.pi / 2, 4, "X")   # lokale Z -> wereld -Y
WK = wk.matrix_world.copy()
wiek_delen = []


def wl(p):
    """Lokaal punt van de wieken -> wereld."""
    return WK @ Vector(p)


def onder_wieken(o):
    o.parent = wk
    o.matrix_parent_inverse = WK.inverted()
    wiek_delen.append(o)
    return o


bpy.ops.mesh.primitive_uv_sphere_add(segments=16, ring_count=8, radius=0.32, location=naaf_pos)
naaf = bpy.context.object
naaf.name = "naaf"
naaf.scale = (1, 0.7, 1)
put(naaf, M_NAAF)
onder_wieken(naaf)
for k in range(4):
    a = math.pi / 2 * k
    rd = Vector((math.cos(a), math.sin(a), 0))
    rz = Vector((-math.sin(a), math.cos(a), 0))
    onder_wieken(balk("roede", wl(rd * 0.1), wl(rd * (WIEK_L + 0.1)), 0.16, 0.13, M_BALK, bevel=0.01, ruw=0.004))
    # tralie: twee lange latten, dwarslatten, en het doek ertussen (aan de achterkant van de roede)
    for side in (0.0, WIEK_B):
        off = rz * (side + 0.07)
        onder_wieken(balk("lat", wl(rd * WIEK_R0 + off + Vector((0, 0, -0.04))),
                          wl(rd * WIEK_L + off + Vector((0, 0, -0.04))), 0.06, 0.05, M_BALK, bevel=0.006))
    r = WIEK_R0
    while r <= WIEK_L + 0.01:
        onder_wieken(balk("dwarslat", wl(rd * r + rz * 0.05 + Vector((0, 0, -0.05))),
                          wl(rd * r + rz * (WIEK_B + 0.09) + Vector((0, 0, -0.05))), 0.045, 0.04, M_BALK))
        r += (WIEK_L - WIEK_R0) / 8
    c = rd * (WIEK_R0 + WIEK_L) / 2 + rz * (WIEK_B / 2 + 0.07) + Vector((0, 0, -0.06))
    doek = box("doek", (0, 0, 0), (WIEK_L - WIEK_R0, WIEK_B, 0.008), M_DOEK)
    doek.matrix_world = WK @ Matrix.Translation(c) @ Matrix.Rotation(a, 4, "Z")
    s_ = doek.modifiers.new("bol", "SIMPLE_DEFORM")
    s_.deform_method = "BEND"
    s_.deform_axis = "X"
    s_.angle = math.radians(4)
    onder_wieken(doek)

# --- Schoorsteen: rond, stenen in ringen, iets taps ------------------------------------------------------
sx, sy = SCHOORSTEEN
sz0, sz1 = dak_z(sx, sy) - 0.35, dak_z(sx, sy) + 0.42
z = sz0
while z < sz1:
    h = random.uniform(0.1, 0.15)
    R = 0.5 - 0.16 * ((z - sz0) / (sz1 - sz0)) ** 1.5      # bol, naar boven ingesnoerd
    a = random.uniform(0, 0.4)
    while a < 2 * math.pi:
        L = random.uniform(0.18, 0.3)
        da = L / R
        am = a + da / 2
        stone((sx + R * math.cos(am), sy + R * math.sin(am), z + h / 2), (L * 0.95, 0.16, h * 0.92), am + math.pi / 2,
              M_SCHOOR, tilt=(random.uniform(-0.08, 0.08), random.uniform(-0.08, 0.08)))
        a += da + 0.01
    z += h + 0.006
cyl("rookgat", (sx, sy, sz1 - 0.08), 0.3, 0.12, M_DONKER, verts=20)
cyl("schoorsteenkern", (sx, sy, (sz0 + sz1) / 2 - 0.05), 0.36, sz1 - sz0 - 0.1, M_SPECIE, verts=20)

# --- Gras en varens --------------------------------------------------------------------------------------
for k, (gx_, gy_) in enumerate(((-0.25, 0.35), (-0.2, 2.6), (0.6, -0.25), (3.6, -0.3), (4.3, VY0 - 0.25),
                                (-0.3, 1.2), (5.8, VY0 - 0.1), (2.4, -0.22))):
    gras_pol((gx_, gy_, 0.0), M_GRAS, n=60, h=0.28, r=0.18, seed=k)

# --- LOD1-proxies ------------------------------------------------------------------------------------------
vs, fs = [], []
nx1, nt1 = 14, 10
for i in range(nx1 + 1):
    x = RAND_X0 + (RAND_X1 - RAND_X0) * i / nx1
    for j in range(nt1 + 1):
        vs.append(tuple(dak_punt(x, j / nt1) + Vector((0, 0, 0.05))))
for i in range(nx1):
    for j in range(nt1):
        k = i * (nt1 + 1) + j
        fs.append([k, k + nt1 + 1, k + nt1 + 2, k + 1])
l1dak = lod1(mesh_obj("l1_dak", vs, fs, M_RIET))
lod1(box("l1_huis", (HX1 / 2, HY1 / 2, WAND_H / 2), (HX1, HY1, WAND_H), M_PLANK))
lod1(box("l1_vleugel", ((VX0 + VX1) / 2, (VY0 + HY1) / 2, WAND_H / 2), (VX1 - VX0, HY1 - VY0, WAND_H), M_PLANK))
vs = [(0.0, 0.0, 0.0)] + [(0.0, HY1 * i / 10, gevel_top(HY1 * i / 10)) for i in range(11)] + [(0.0, HY1, 0.0)]
lod1(mesh_obj("l1_gevel", [(-0.02, v[1], v[2]) for v in vs], [list(range(len(vs)))], M_PLEISTER, smooth=False))     # normaal naar -X
lod1(box("l1_voet", (tx, ty, (VOET_Z0 + VOET_Z1) / 2), (VOET_ZIJ, VOET_ZIJ, VOET_Z1 - VOET_Z0), M_STEEN))
bpy.ops.mesh.primitive_cone_add(vertices=8, radius1=KAP_R0 + 0.02, radius2=KAP_R1 + 0.02, depth=KAP_Z1 - VOET_Z1 + 0.06,
                                    location=(tx, ty, (VOET_Z1 + KAP_Z1) / 2 + 0.02), rotation=(0, 0, math.pi / 8))
lod1(put(bpy.context.object, M_KAP, smooth=False)).name = "l1_kap"
cyl("l1_schoorsteen", (sx, sy, (sz0 + sz1) / 2), 0.46, sz1 - sz0, M_SCHOOR, verts=8)
lod1(bpy.context.object)
for k in range(4):                                  # wieken als platte balken, onder `wieken`
    a = math.pi / 2 * k
    rd = Vector((math.cos(a), math.sin(a), 0))
    rz = Vector((-math.sin(a), math.cos(a), 0))
    c = rd * (0.1 + WIEK_L) / 2 + rz * (WIEK_B / 2 + 0.03)
    o = box("l1_wiek", (0, 0, 0), (WIEK_L, WIEK_B + 0.14, 0.06), M_DOEK)
    o.matrix_world = WK @ Matrix.Translation(c + Vector((0, 0, -0.04))) @ Matrix.Rotation(a, 4, "Z")
    o.parent = wk
    o.matrix_parent_inverse = WK.inverted()
    lod1(o)

# --- Ankers --------------------------------------------------------------------------------------------------
anker("rook_bron", (sx, sy, sz1 + 0.02))
anker("deur_drempel", (mx, VY0 - 0.6, 0.0))                 # molendeur op de vleugel (MillDoor)
anker("deur_gevel_drempel", (-0.65, gy, 0.0))
anker("maalplek", (5.0, VY0 - 0.9, 0.0))                     # bij de zakken voor de vleugel

# --- Alles naar het midden schuiven (spel-oorsprong) ---------------------------------------------------------
for o in list(scene.objects):
    if o.parent is None:
        o.location.x -= OX
        o.location.y -= OY
if "deur" in OPTS:
    zet_deur("deur", float(OPTS["deur"]))
if "wieken" in OPTS:
    wk.rotation_euler.rotate_axis("Z", math.radians(float(OPTS["wieken"])))
print("HALMEN", len(halm_c))
afronden(NAAM, (-OX, -OY, 0.0), REF_PX, W_PX, H_PX)
