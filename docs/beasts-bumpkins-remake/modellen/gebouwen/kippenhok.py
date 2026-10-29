"""Kippenhok (ChickenCoop.png, 66x45) uit Beasts & Bumpkins nagebouwd in 3D.

Klein houten hok op een stenen voet met een rieten zadeldak, op een grote mat van los stro (de
sprite is vooral stro). Voorkant (-X, camera-links) met een klein deurtje en een kippenloopplank,
legnesten aan de achterkant (+Y), voerbak op het stro aan de -Y-kant, een hoop vers stro vooraan.
Goedgekeurd concept: concept/img/kippenhok.jpg (riet, planken, stenen voet, loopplank, nesten, trog).

Maat: de sprite tekent het huisje 0,55 m breed (op 21,9 px/m) -- een poppenhuis naast een dorpeling
van 1,37 m. Het hok is daarom 0,9 x 0,9 m met de nok op ~1,5 m, zoals het concept; de stromat
(2,2 m) houdt de sprite-maat.

Draaien (headless):
  blender -b -P kippenhok.py -- [schaal=8] [samples=64] [uit=pad.png] [deur=graden] [rt] [rt_vergelijk]
"""
import math
import os
import random
import sys

import bpy
from mathutils import Matrix, Vector

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import erf_lib as E  # noqa: E402

OPTS = E.opties()
NAAM = "kippenhok"
BLEND = os.path.join(E.HERE, NAAM + ".blend")

# --- Sprite en camera -------------------------------------------------------------
SPRITE = (66, 60)                       # 1x: HD-sprite 132x90 op 2x, boven 15 px bijgezet (PAD) voor de nok
PAD = 15
REF_WERELD = (0.0, 0.0, 0.0)            # midden van de stromat
REF_PX = (33.0, 26.5 + PAD)

# --- Maten (meters) ---------------------------------------------------------------
X0, X1, Y0, Y1 = -0.06, 0.74, -0.04, 0.76  # buitenkant wanden
VOET_H = 0.22                           # stenen voet
WAND_H = 0.68                           # tot de dakvoet
NOK_Z = 1.3
DAK_UIT = 0.2                           # overstek opzij (y) en voor/achter (x)
RIET_DIK = 0.2
MAT = 1.2                               # halve maat van de stromat
DEUR = (0.36, 0.3, 0.4, VOET_H + 0.03)   # midden y, breedte, hoogte, onderkant (voorkant -X)
LOOP = 0.62                             # lengte loopplank
NEST_Y = (Y1, Y1 + 0.32)                # legnesten aan de achterkant
TROG = (0.25, -0.62)                    # voerbak (x, y)
DEUR_OPEN = 110.0                       # graden, naar buiten

SCHAAL = float(OPTS.get("schaal", 8))
SAMPLES = int(OPTS.get("samples", 64))
UIT = OPTS.get("uit", os.path.join(E.PREVIEW, NAAM + "_render.png"))

if "rt" in OPTS or "rt_vergelijk" in OPTS:
    if "rt" in OPTS:
        n = E.rt_bouw(NAAM, BLEND, res=int(OPTS.get("res", 2048)),
                      ratio_opaak={"steen": 0.12, "korrel": 0.3, "ei": 0.4}, lod1_doel=7000,
                      riet_ext=0.08, riet_ray=0.16)
        print("RT", n)
    for lod, suf in (("_rt", ""), ("_rt_lod1", "_lod1")):
        E.rt_vergelijk(NAAM, SPRITE, 8, REF_WERELD, REF_PX, os.path.join(E.PREVIEW, f"{NAAM}_rt{suf}.png"), lod)
    sys.exit(0)

random.seed(9)
scene = E.leeg()
box, balk = E.box, E.balk

# --- Materialen -------------------------------------------------------------------
M_HALM = E.mat_halm("halm", grijs=0.85)
M_STRO = E.mat_halm("stro", [(0.0, (0.12, 0.07, 0.03)), (0.35, (0.36, 0.24, 0.10)), (0.7, (0.62, 0.46, 0.22)),
                             (1.0, (0.85, 0.70, 0.42))], grijs=0.5)
M_VERS = E.mat_halm("vers_stro", [(0.0, (0.55, 0.36, 0.06)), (0.4, (0.92, 0.70, 0.2)), (1.0, (1.0, 0.9, 0.5))])
M_RIET = E.mat_rietlaag("rietlaag")
M_PLANK = E.mat_hout("plank", "weathered_brown_planks", (0.08, 0.065, 0.05), (0.44, 0.37, 0.29), 0.9, 6.0,
                     stretch=(1, 1, 0.45), grijs=1.2, vuil=0.8, vuil_h=0.15)
M_BALK = E.mat_hout("balk", "rough_wood", (0.06, 0.035, 0.02), (0.30, 0.20, 0.12), 0.8, 5.0, grijs=0.6, vuil=0.5, vuil_h=0.12)
M_DEUR = E.mat_hout("deurhout", "weathered_brown_planks", (0.05, 0.035, 0.025), (0.30, 0.22, 0.15), 0.9, 4.0,
                    stretch=(1, 1, 0.5), grijs=0.7)
M_STEEN = E.mat_steen("steen", lo=(0.04, 0.045, 0.04), hi=(0.48, 0.50, 0.46), moss=1.0)
M_SPECIE = E.mat_specie("specie")
M_DONKER = E.mat_flat("donker", (0.012, 0.01, 0.008), 0.95)
M_IJZER = E.mat_ijzer("ijzer")
M_GROND = E.mat_grond("grond", "farm_soil", (0.42, 0.34, 0.25), 1.2)
M_KORREL = E.mat_flat("korrel", (0.55, 0.38, 0.12), 0.7)
M_EI = E.mat_flat("ei", (0.78, 0.62, 0.45), 0.4)
M_KEI = E.mat_steen("kei", lo=(0.05, 0.05, 0.05), hi=(0.5, 0.52, 0.5), moss=0.3)

# --- Stenen voet ----------------------------------------------------------------------
stenen = E.Stenen(M_STEEN, n=8, seed=500)
for p0, p1 in (((X0, Y0), (X1, Y0)), ((X0, Y1), (X1, Y1)), ((X0, Y0 + 0.06), (X0, Y1 - 0.06)),
               ((X1, Y0 + 0.06), (X1, Y1 - 0.06))):
    stenen.muur(p0, p1, 0.0, VOET_H, 0.12, hs=(0.06, 0.09), ls=(0.1, 0.2))
box("voetkern", ((X0 + X1) / 2, (Y0 + Y1) / 2, VOET_H / 2), (X1 - X0 - 0.1, Y1 - Y0 - 0.1, VOET_H), M_SPECIE)

# --- Wanden: liggende planken op stijlen, gevels met staande planken --------------------
P = 0.12                                                # plankbreedte (hoogte bij liggend)
for (x, y) in ((X0, Y0), (X1, Y0), (X0, Y1), (X1, Y1)):
    balk("hoekstijl", (x, y, VOET_H - 0.02), (x + random.uniform(-0.01, 0.01), y, WAND_H + 0.04), 0.075, M_BALK)


def liggend(p0, p1, z0, z1, gat=None):
    """Liggende planken van p0 naar p1 (buitenvlak), gat = (a, b, za, zb) langs de wand."""
    p0, p1 = Vector(p0), Vector(p1)
    d = (p1 - p0)
    L = d.length
    d.normalize()
    rz = math.atan2(d.y, d.x)
    z = z0
    while z < z1 - 0.01:
        h = min(P, z1 - z)
        stukken = [(0.0, L)]
        if gat and gat[2] < z + h / 2 < gat[3]:
            stukken = [(0.0, gat[0]), (gat[1], L)]
        for a, b in stukken:
            if b - a < 0.02:
                continue
            m = p0 + d * ((a + b) / 2)
            o = box("plank", (m.x, m.y, z + h / 2), (b - a, 0.022, h - random.uniform(0.008, 0.02)), M_PLANK, bevel=0.004, jitter=0.004)
            o.rotation_euler = (random.uniform(-0.02, 0.02), 0, rz + random.uniform(-0.01, 0.01))
        z += h


gat_v = (DEUR[0] - DEUR[1] / 2 - Y0, DEUR[0] + DEUR[1] / 2 - Y0, DEUR[3], DEUR[3] + DEUR[2])
liggend((X0, Y0), (X0, Y1), VOET_H, WAND_H, gat_v)          # voorkant (-X), met deurgat
liggend((X0, Y0), (X1, Y0), VOET_H, WAND_H)                 # -Y
liggend((X0, Y1), (X1, Y1), VOET_H, WAND_H)                 # +Y
liggend((X1, Y0), (X1, Y1), VOET_H, WAND_H)                 # achter (+X)
box("binnen", ((X0 + X1) / 2, (Y0 + Y1) / 2, (VOET_H + WAND_H + 0.2) / 2), (X1 - X0 - 0.05, Y1 - Y0 - 0.05, WAND_H + 0.2 - VOET_H), M_DONKER)
for p in bpy.data.objects["binnen"].data.polygons:
    p.flip()
for y in (Y0, Y1):
    balk("dakregel", (X0 - 0.06, y, WAND_H), (X1 + 0.06, y, WAND_H), (0.07, 0.06), M_BALK)

# gevels (x = X0 en X1): staande planken tot onder het dak, schoor in de voorgevel
YM = (Y0 + Y1) / 2
HELL = (NOK_Z - 0.12 - WAND_H) / ((Y1 - Y0) / 2 + DAK_UIT)


def gevel_z(y):
    return WAND_H + (NOK_Z - 0.16 - WAND_H) * (1 - abs(y - YM) / ((Y1 - Y0) / 2 + 0.02))


for x in (X0, X1):
    n = int((Y1 - Y0) / 0.1)
    for k in range(n):
        y = Y0 + (k + 0.5) * (Y1 - Y0) / n
        top = gevel_z(y) - 0.02
        box("gevelplank", (x - 0.005 * (1 if x < 0.3 else -1), y, (WAND_H + top) / 2 - 0.01),
            (0.022, (Y1 - Y0) / n - 0.008, top - WAND_H + 0.02), M_PLANK, bevel=0.004, jitter=0.003)
balk("gevelschoor", (X0 - 0.03, Y0 + 0.08, WAND_H + 0.02), (X0 - 0.03, YM - 0.03, NOK_Z - 0.22), (0.05, 0.06), M_BALK)
balk("gevelstijl", (X0 - 0.03, YM, WAND_H), (X0 - 0.03, YM, NOK_Z - 0.15), (0.05, 0.06), M_BALK)
for sg in (-1, 1):                                       # windveren
    balk("windveer", (X0 - 0.06, YM + sg * ((Y1 - Y0) / 2 + 0.12), WAND_H - 0.06), (X0 - 0.06, YM, NOK_Z - 0.06),
         (0.04, 0.07), M_BALK)

# --- Deurtje ------------------------------------------------------------------------------
dy0, dy1 = DEUR[0] - DEUR[1] / 2, DEUR[0] + DEUR[1] / 2
delen = []
for k in range(3):
    pw = DEUR[1] / 3
    y = dy1 - pw * (k + 0.5)
    delen.append(box("deurplank", (X0 - 0.03, y, DEUR[3] + DEUR[2] / 2), (0.025, pw - 0.006, DEUR[2] - random.uniform(0, 0.02)),
                     M_DEUR, bevel=0.004))
for z in (0.1, DEUR[2] - 0.1):
    delen.append(box("klamp", (X0 - 0.05, DEUR[0], DEUR[3] + z), (0.02, DEUR[1] - 0.04, 0.05), M_DEUR, bevel=0.004))
    delen.append(box("hengsel", (X0 - 0.062, dy1 - 0.1, DEUR[3] + z), (0.006, 0.18, 0.025), M_IJZER))
delen.append(box("grendel", (X0 - 0.065, dy0 + 0.05, DEUR[3] + DEUR[2] / 2), (0.01, 0.1, 0.022), M_IJZER))
# scharnier aan de +Y-kant; open naar buiten (-X) -- zoals de melkerij
T = Matrix(((-1, 0, 0, X0 - 0.015), (0, -1, 0, dy1), (0, 0, 1, 0), (0, 0, 0, 1)))
DEUR_E = E.scharnier("deur", delen, T)
DEUR_E["open_graden"] = DEUR_OPEN
E.zet_deur(DEUR_E, float(OPTS.get("deur", 20)))          # standaard op een kier: de kippen moeten erdoor
for y in (dy0 - 0.03, dy1 + 0.03):
    balk("kozijn", (X0 - 0.02, y, DEUR[3]), (X0 - 0.02, y, DEUR[3] + DEUR[2] + 0.04), (0.04, 0.045), M_BALK)
balk("latei", (X0 - 0.02, dy0 - 0.06, DEUR[3] + DEUR[2] + 0.03), (X0 - 0.02, dy1 + 0.06, DEUR[3] + DEUR[2] + 0.03),
     (0.045, 0.05), M_BALK)

# loopplank met latjes
lp0 = Vector((X0 - 0.03, DEUR[0], DEUR[3]))
lp1 = Vector((X0 - 0.03 - LOOP, DEUR[0], 0.02))
d = lp1 - lp0
for k in range(3):
    y = DEUR[0] + (k - 1) * 0.085
    o = box("loopplank", ((lp0.x + lp1.x) / 2, y, (lp0.z + lp1.z) / 2 + 0.01), (d.length, 0.08, 0.022), M_PLANK, bevel=0.004)
    o.rotation_euler.y = math.atan2(-d.z, -d.x) * -1
for k in range(5):
    t = (k + 0.6) / 5.5
    p = lp0 + d * t
    o = box("latje", (p.x, p.y, p.z + 0.035), (0.025, 0.26, 0.018), M_BALK, bevel=0.003)
    o.rotation_euler.y = math.atan2(-d.z, -d.x) * -1

# --- Legnesten (+Y): kist met schuin deksel, stro en eieren --------------------------------
nx0, nx1 = X0 + 0.08, X1 - 0.08
ny0, ny1 = NEST_Y
box("nestbodem", ((nx0 + nx1) / 2, (ny0 + ny1) / 2, 0.32), (nx1 - nx0, ny1 - ny0, 0.03), M_PLANK)
box("nestvoor", ((nx0 + nx1) / 2, ny1, 0.42), (nx1 - nx0, 0.025, 0.2), M_PLANK, bevel=0.004)
for x in (nx0, (nx0 + nx1) / 2, nx1):
    box("nestschot", (x, (ny0 + ny1) / 2, 0.47), (0.025, ny1 - ny0, 0.3), M_PLANK, bevel=0.004)
dek = box("nestdeksel", ((nx0 + nx1) / 2, (ny0 + ny1) / 2 + 0.02, 0.66), (nx1 - nx0 + 0.06, ny1 - ny0 + 0.12, 0.025), M_PLANK, bevel=0.004)
dek.rotation_euler.x = -0.35
for x in (nx0 - 0.02, nx1 + 0.02):
    balk("nestpoot", (x, ny1, 0.0), (x, ny1, 0.33), 0.045, M_BALK)
for k in range(2):
    xm = nx0 + (nx1 - nx0) * (k + 0.5) / 2
    for j in range(k + 1):
        E.bol("ei", (xm + 0.04 * j, (ny0 + ny1) / 2 + 0.02, 0.37), 0.028, M_EI, (1, 1, 1.25), sub=2)

# --- Dak (riet, nok langs X) ---------------------------------------------------------------
hb = (Y1 - Y0) / 2 + DAK_UIT
prof = []
for i in range(17):                                     # licht hol naar de rand (holle kromme)
    t = -1 + 2 * i / 16
    y = hb * t
    z = NOK_Z - (NOK_Z - (WAND_H - 0.04)) * (abs(t) ** 1.15)
    prof.append((y, z))
DAK = E.Dakvlak(prof, X0 - DAK_UIT, X1 + DAK_UIT * 0.8, as_x=False, oorsprong=(0.0, YM))
rnd = random.Random(21)
schil = DAK.schil("rietschil", M_RIET, dik=RIET_DIK, du=0.06, ds=0.05, rand_dik=0.2, rafel=0.05)
DUN = lambda u: 0.0036 - 0.001 * u                     # kleiner dak: dunnere halmen
riet = [DAK.halmen("dakhalmen", M_HALM, rnd, bos_d=0.04, per_bos=14, laag=(0.12, 0.17), lengte=(0.36, 0.56),
                   hang=0.28, dik=0.08, bult=0.06, rommel=0.22, rad=DUN),
        DAK.nokrol("nokhalmen", M_HALM, rnd, breed=0.22, per_m=1800, hoog=0.05, rad=DUN),
        DAK.gevelrol("gevelrol_voor", M_HALM, rnd, X0 - DAK_UIT + 0.04, -1, r=0.1, per_m=1600, uit=0.0, rad=DUN),
        DAK.gevelrol("gevelrol_achter", M_HALM, rnd, X1 + DAK_UIT * 0.8, 1, r=0.05, per_m=600, uit=0.015, rad=DUN)]

# --- Stromat, verse hoop, trog, keien --------------------------------------------------------
def mat_rand(a):
    """Rafelige rand van de stromat (straal per hoek): vierkant-achtig zoals de sprite."""
    c, s = abs(math.cos(a)), abs(math.sin(a))
    r = MAT / max(c, s) ** 0.75 / 1.12
    return r * (1 + 0.12 * math.sin(5 * a + 1.3) + 0.07 * math.sin(11 * a))


vs, fs = [(0, 0, 0.004)], []
n = 72
for i in range(n):
    a = 2 * math.pi * i / n
    vs.append((mat_rand(a) * math.cos(a), mat_rand(a) * math.sin(a), 0.004))
    fs.append([0, i + 1, (i + 1) % n + 1])
grond = E.mesh_obj("strogrond", vs, fs, M_GROND, smooth=False)
grond["rt"] = "grond"
uvl = grond.data.uv_layers.new(name="UVMap")


def strohalmen(name, mat, n, plek, lengte=(0.08, 0.22), hoog=0.0, seed=1):
    r = random.Random(seed)
    curves, bos = [], []
    for _ in range(n):
        x, y, z = plek(r)
        if x is None:
            continue
        a = r.uniform(0, 2 * math.pi)
        L = r.uniform(*lengte)
        d = Vector((math.cos(a), math.sin(a), r.uniform(-0.25, 0.35)))
        b = Vector((-d.y, d.x, 0)) * r.uniform(-0.15, 0.15)
        pts = []
        for k in range(5):
            f = k / 4
            p = Vector((x, y, z)) + d * (L * (f - 0.5)) + b * (L * (f - 0.5) ** 2 * 2)
            p.z = max(p.z, 0.006 + 0.004 * r.random()) + hoog
            pts.append(tuple(p))
        curves.append(pts)
        bos.append(r.random())
    return E.strands(name, curves, mat, bos, lambda u: 0.0035 - 0.001 * u)


def op_mat(r):
    a = r.uniform(0, 2 * math.pi)
    rr = mat_rand(a) * math.sqrt(r.random()) * 1.02
    x, y = rr * math.cos(a), rr * math.sin(a)
    if X0 + 0.02 < x < X1 - 0.02 and Y0 + 0.02 < y < Y1 - 0.02:
        return None, None, None
    z = 0.006 + 0.03 * r.random() ** 3 * max(0.0, 1 - rr / MAT)
    return x, y, z


def hoop(cx, cy, R, H):
    def f(r):
        a, rr = r.uniform(0, 2 * math.pi), R * math.sqrt(r.random())
        return cx + rr * math.cos(a), cy + rr * math.sin(a) * 0.8, H * (1 - (rr / R) ** 2) * r.uniform(0.6, 1.0)
    return f


stro = [strohalmen("strohalmen", M_STRO, 42000, op_mat, seed=3),
        strohalmen("verse_hoop", M_VERS, 6000, hoop(-0.72, -0.72, 0.42, 0.06), lengte=(0.12, 0.3), seed=4)]
for o in stro:
    o["rt"] = "halm_grond"
# voerbak met graan
tx, ty = TROG
for sx, sy, sz, px, py, pz in ((0.62, 0.025, 0.12, 0, -0.1, 0.07), (0.62, 0.025, 0.12, 0, 0.1, 0.07),
                               (0.025, 0.22, 0.12, -0.3, 0, 0.07), (0.025, 0.22, 0.12, 0.3, 0, 0.07),
                               (0.62, 0.22, 0.02, 0, 0, 0.02)):
    box("trog", (tx + px, ty + py, pz), (sx, sy, sz), M_PLANK, bevel=0.004, jitter=0.004)
box("korrel", (tx, ty, 0.06), (0.5, 0.15, 0.02), M_KORREL, jitter=0.02)
for k in range(30):
    E.bol("korrel", (tx + random.uniform(-0.45, 0.45), ty + random.uniform(-0.25, 0.25), 0.008), 0.008, M_KORREL, sub=1)
keien = E.Stenen(M_KEI, n=4, seed=600, p=2.4, bumps=0.25, cuts=3)
for (x, y, s) in ((-0.95, 0.2, 0.09), (-0.8, 0.75, 0.06), (0.95, -0.4, 0.07), (0.45, -1.0, 0.05), (-0.3, -0.95, 0.06),
                  (-1.0, -0.3, 0.04), (-0.7, -1.0, 0.05), (0.9, 0.3, 0.05), (-0.15, -1.1, 0.035), (-1.05, 0.55, 0.04)):
    keien.zet((x, y, s * 0.3), (s * 2.2, s * 1.7, s * 1.0), random.uniform(0, 6.3))

# rommel: takjes, plankstukjes, veertjes
for k in range(14):
    a, rr = random.uniform(0, 6.3), random.uniform(0.5, 1.1)
    x, y = rr * math.cos(a), rr * math.sin(a)
    if X0 - 0.1 < x < X1 + 0.1 and Y0 - 0.1 < y < NEST_Y[1] + 0.1:
        continue
    o = box("takje", (x, y, 0.012), (random.uniform(0.08, 0.22), random.uniform(0.012, 0.03), 0.012),
            random.choice((M_BALK, M_PLANK)), jitter=0.003)
    o.rotation_euler.z = random.uniform(0, 3.14)
# hekje links en achter (concept): palen met twee regels, scheef en verweerd
for p0, p1 in (((-1.0, -0.15), (-1.0, 1.0)), ((-1.0, 1.0), (0.2, 1.05))):
    p0, p1 = Vector((*p0, 0)), Vector((*p1, 0))
    n_p = max(2, int((p1 - p0).length / 0.55) + 1)
    pal = [p0.lerp(p1, k / (n_p - 1)) for k in range(n_p)]
    for q in pal:
        balk("hekpaal", (q.x, q.y, 0.0), (q.x + random.uniform(-0.02, 0.02), q.y + random.uniform(-0.02, 0.02), 0.5), 0.055, M_BALK)
    for z in (0.22, 0.42):
        for a, b in zip(pal, pal[1:]):
            balk("hekregel", (a.x, a.y, z + random.uniform(-0.02, 0.02)), (b.x, b.y, z + random.uniform(-0.02, 0.02)), (0.03, 0.06), M_PLANK)


M_VEER = [E.mat_halm("veer_bruin", [(0.0, (0.25, 0.08, 0.02)), (0.5, (0.55, 0.22, 0.06)), (1.0, (0.75, 0.42, 0.15))]),
          E.mat_halm("veer_wit", [(0.0, (0.55, 0.52, 0.48)), (0.5, (0.82, 0.8, 0.75)), (1.0, (0.92, 0.9, 0.86))])]
M_KAM = E.mat_flat("kam", (0.55, 0.03, 0.02), 0.5)
M_POOT = E.mat_flat("poot", (0.65, 0.45, 0.1), 0.6)


def kip(x, y, rz, mat, pik=False):
    """Kip: lijf en kop als bol, veertjes als korte halmen, kam, snavel, pootjes."""
    R = Matrix.Rotation(rz, 3, "Z")
    o = Vector((x, y, 0))
    p = lambda v: o + R @ Vector(v)
    kz = 0.09 if pik else 0.25
    lijf = E.bol("kip", p((0, 0, 0.17)), 0.1, M_KORREL, (1.3, 0.9, 0.95))
    kop = E.bol("kip", p((0.13, 0, kz)), 0.045, M_KORREL)
    rr = random.Random(int(x * 1000 + y * 77))
    veren = []
    for _ in range(1400):                                 # veertjes op lijf en kop, naar achteren gestreken
        kopje = rr.random() < 0.15
        c, rad = (p((0.13, 0, kz)), 0.047) if kopje else (p((0, 0, 0.17)), 0.1)
        d = Vector((rr.gauss(0, 1), rr.gauss(0, 1), rr.gauss(0, 1))).normalized()
        q = c + Vector((d.x * rad * (1.3 if not kopje else 1), d.y * rad * 0.9, d.z * rad * 0.95))
        t = (q - c).normalized().lerp(R @ Vector((-1, 0, -0.2)), 0.6).normalized()
        veren.append([tuple(q), tuple(q + t * 0.012), tuple(q + t * 0.024)])
    staart = [[tuple(p((-0.12, rr.uniform(-0.03, 0.03), 0.2))), tuple(p((-0.17, rr.uniform(-0.03, 0.03), 0.27))),
               tuple(p((-0.19 + rr.uniform(-0.02, 0.02), rr.uniform(-0.03, 0.03), 0.31)))] for _ in range(60)]
    E.strands("kipveren", veren + staart, mat, [rr.random() for _ in veren + staart], lambda u: 0.0035 - 0.0025 * u)
    E.bol("kam", p((0.14, 0, kz + 0.045)), 0.02, M_KAM, (1.2, 0.4, 0.8), sub=2)
    E.bol("kam", p((0.17, 0, kz - 0.035)), 0.012, M_KAM, (0.6, 0.5, 1.2), sub=1)
    E.cyl("snavel", p((0.18, 0, kz - 0.005)), 0.01, 0.035, M_POOT, rot=(0, math.pi / 2, rz), verts=6)
    for sy in (-0.035, 0.035):
        E.cyl("poot", p((0.0, sy, 0.04)), 0.007, 0.08, M_POOT, verts=6)


voor = set(bpy.data.objects)
kip(-0.75, -0.25, math.radians(30), M_VEER[0], pik=True)
kip(-0.25, -0.95, math.radians(120), M_VEER[1])
kip(-0.85, 0.55, math.radians(-40), M_VEER[0])
kip(0.75, -0.95, math.radians(200), M_VEER[0], pik=True)
kip(-0.45, -0.3, math.radians(-100), M_VEER[1], pik=True)
for o in set(bpy.data.objects) - voor:                  # kippen zijn spelfiguren: alleen in de render
    o["rt"] = "weg"

# --- Ankers -----------------------------------------------------------------------------------
E.anker("deur_drempel", (X0 - 0.35, DEUR[0] + 0.38, 0.0))      # naast de loopplank: dorpeling bij de deur
E.anker("kip_uitgang", (X0 - 0.03 - LOOP - 0.08, DEUR[0], 0.0))  # voet van de loopplank: kippen in/uit
E.anker("leg_nest", ((nx0 + nx1) / 2, (ny0 + ny1) / 2, 0.36))  # in het legnest: eieren rapen
E.anker("voerplek", (tx, ty - 0.3, 0.0))                       # voor de voerbak (dorpeling strooit hier)
E.anker("rook_bron", ((X0 + X1) / 2, YM, NOK_Z + 0.05))        # geen schoorsteen: nok (stof/damp), voor de vorm

# --- Licht, camera, render ------------------------------------------------------------------
vanger = E.licht(scene, dak=[schil] + riet + stro)
E.camera(scene, SPRITE, SCHAAL, REF_WERELD, REF_PX)
tri, halm = E.tel()
print("TRIS", tri, "HALMEN", halm)
os.makedirs(E.PREVIEW, exist_ok=True)
bpy.ops.wm.save_as_mainfile(filepath=BLEND)
if "geen_render" not in OPTS:
    E.render(scene, UIT, SAMPLES)
