"""Melkerij / boerderij (Dairy.png, 213x160) uit Beasts & Bumpkins nagebouwd in 3D.

Lang vakwerkhuis met een rond (boogvormig) rieten dak, voorgevel naar de camera-links (-X) met deur
en twee ramen met bloembakken, gevel (-Y) met zwartbonte koeienvlekken in het vakwerk, stenen
schoorsteen op de nok met een paarse rand, een dakkapel met paarse pannen op het achterdak en een
varkenshok met stenen muurtjes erachter. Goedgekeurd: de LINKER helft van
concept/img/melkerij_boerderij.jpg plus de originele sprite (de rechterhelft heeft fouten).

Maten teruggerekend uit de sprite op 21,9 px/m (1x), zoals de hut.

Draaien (headless):
  blender -b -P melkerij_boerderij.py -- [schaal=2] [samples=64] [uit=pad.png] [deur=graden] [rt] [rt_vergelijk]
Zonder rt: melkerij_boerderij.blend + render (standaard preview/melkerij_boerderij_render.png).
rt: bakt de .blend naar melkerij_boerderij_rt.glb + _rt_lod1.glb (rt_textures/); rt_vergelijk rendert de glb.
"""
import math
import os
import random
import sys

import bmesh
import bpy
from mathutils import Matrix, Vector

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import erf_lib as E  # noqa: E402

OPTS = E.opties()
NAAM = "melkerij_boerderij"
BLEND = os.path.join(E.HERE, NAAM + ".blend")

# --- Sprite en camera -------------------------------------------------------------
SPRITE = (213, 160)                    # 1x
REF_WERELD = (-1.85, -2.9, 0.0)        # voorhoek gevel, op de grond
REF_PX = (107.5, 158.8)                # waar die hoek in de sprite staat (1x)

# --- Maten (meters) ---------------------------------------------------------------
HW, HL = 1.85, 2.9                     # halve breedte (x) en lengte (y) van de muren, buitenkant
MUUR = 0.2                             # wanddikte
WAND_TOP = 2.45                        # langsmuren tot onder het riet (achter de dakrand)
BINT = 1.95                            # bovenregel (bint) van de gevel
REGEL = 0.95                           # middenregel in het vakwerk
DAK_X = 2.15                           # dakrand opzij (overstek 0,3)
DAK_Y0 = -3.2                          # dak voor (overstek gevel)
HEUP_Y, HEUP_K = 1.2, 0.93             # achter: afgewolfd vanaf y = HEUP_Y, ingedrukt met HEUP_K
DAK_RAND_Z = 2.05                      # dakrand (bovenkant riet) aan de langszijde
NOK_Z = 4.3                            # nok
BOOG = 64.0                            # graden: hoe rond het dakprofiel is (90 = halve ellips)
RIET_DIK = 0.28                        # dikte van de rietschil aan de nok, RIET_RAND aan de rand
RIET_RAND = 0.42
SCH = (0.0, 2.0)                       # schoorsteen op de nok (x, y)
SCH_Z0, SCH_Z1 = 2.2, 5.15             # schoorsteen: van zolder tot de paarse rand
SCH_W0, SCH_W1 = 0.86, 0.58            # halve breedte onder (op het dak) en boven
KAPEL = (0.45, 2.05, -2.55, -1.05)     # dakkapel x0, x1, y0, y1 (achterdak, bij de gevel)
KAPEL_NOK = 4.62
DEUR = (-0.27, 1.02, 1.88)             # deur: midden y, breedte, hoogte (voorgevel)
RAMEN = (1.87, -1.56)                  # raammiddens y in de voorgevel
RAAM = (0.72, 0.78, 1.42)              # breedte, onder, boven
STIJLEN_VOOR = (2.9, 0.78, 0.25, -0.79, -2.9)   # stijlen in de voorgevel (y)
HOK = (3.3, 4.7, -2.75, -1.4)          # varkenshok x0, x1, y0, y1
HOK_H = 0.5
DEUR_OPEN = 100.0                      # graden, naar buiten

SCHAAL = float(OPTS.get("schaal", 2))
SAMPLES = int(OPTS.get("samples", 64))
UIT = OPTS.get("uit", os.path.join(E.PREVIEW, NAAM + "_render.png"))

if "rt" in OPTS or "rt_vergelijk" in OPTS:
    if "rt" in OPTS:
        n = E.rt_bouw(NAAM, BLEND, res=int(OPTS.get("res", 2048)),
                      ratio_opaak={"steen": 0.09, "bloem": 0.25, "varken": 0.35}, lod1_doel=7600,
                      riet_ext=0.40, riet_ray=0.55, schil_bron=False)   # schil ligt op de halmen: alleen halmen als bron (2026-10-30)
        print("RT", n)
    for lod, suf in (("_rt", ""), ("_rt_lod1", "_lod1")):
        E.rt_vergelijk(NAAM, SPRITE, 4, REF_WERELD, REF_PX, os.path.join(E.PREVIEW, f"{NAAM}_rt{suf}.png"), lod)
    sys.exit(0)

random.seed(5)
scene = E.leeg()

# --- Materialen -------------------------------------------------------------------
M_HALM = E.mat_halm("halm", grijs=0.6)
M_HALM_ROL = E.mat_halm("halm_rol", [(0.0, (0.45, 0.24, 0.03)), (0.35, (0.85, 0.58, 0.14)), (0.7, (0.98, 0.80, 0.33)),
                                     (1.0, (1.0, 0.9, 0.55))])
M_RIET = E.mat_rietlaag("rietlaag")
M_PLEISTER = E.mat_pleister("pleister", (0.80, 0.76, 0.66), vuil=1.5)
M_KOE = E.mat_pleister("koeienvlekken", (0.84, 0.82, 0.76), vlekken=1.0, vlek_schaal=3.2, vlek_kleur=(0.015, 0.014, 0.013), vuil=1.5)
M_BALK = E.mat_hout("balk", "rough_wood", (0.06, 0.028, 0.012), (0.30, 0.15, 0.07), 0.9, rand=5.0, grijs=0.35, vuil=0.9)
M_DEUR = E.mat_hout("deurhout", "weathered_brown_planks", (0.06, 0.025, 0.01), (0.30, 0.15, 0.06), 0.6, 5.0,
                    stretch=(1, 1, 0.5), grijs=0.4, vuil=1.0)
M_BAK = E.mat_hout("bakhout", "weathered_brown_planks", (0.07, 0.03, 0.012), (0.32, 0.17, 0.07), 0.8, 3.0)
M_PLANK = E.mat_hout("plank", "weathered_brown_planks", (0.06, 0.03, 0.015), (0.30, 0.17, 0.08), 0.6, 4.0,
                     grijs=0.6, vuil=0.8)
M_STEEN = E.mat_steen("steen", lo=(0.06, 0.06, 0.055), hi=(0.62, 0.60, 0.53), moss=0.6, lichen=1.4)
M_HOKSTEEN = E.mat_steen("hoksteen", lo=(0.03, 0.03, 0.028), hi=(0.45, 0.44, 0.40), moss=0.9)
M_SPECIE = E.mat_specie("specie")
M_PAARS = E.mat_pannen("paarse_pannen", schaal=0.55)
M_PAARS_RAND = E.mat_steen("paarse_rand", lo=(0.06, 0.0, 0.08), hi=(0.42, 0.08, 0.5), moss=0.3, lichen=0.4)
M_DONKER = E.mat_flat("donker", (0.012, 0.01, 0.008), 0.95)
M_GLAS = E.mat_flat("glas", (0.02, 0.025, 0.03), 0.15)
M_IJZER = E.mat_ijzer("ijzer")
M_GRAS = E.mat_gras("gras")
M_GROND = E.mat_grond("hokgrond", "forest_ground_04", (0.7, 0.85, 0.5))
M_MODDER = E.mat_grond("modder", "farm_soil", (0.55, 0.45, 0.35))
M_VARKEN = E.mat_huid("varken")
M_BLAD = E.mat_flat("blad", (0.03, 0.18, 0.02), 0.6)
M_BLOEM = [E.mat_flat("bloem_rood", (0.6, 0.02, 0.02), 0.5), E.mat_flat("bloem_geel", (0.85, 0.6, 0.02), 0.5),
           E.mat_flat("bloem_wit", (0.8, 0.78, 0.7), 0.5)]

box, balk = E.box, E.balk


# --- Dakprofiel ---------------------------------------------------------------------
def dak_profiel(n=40):
    """(x, z) van rand tot rand over de nok: ellipsboog afgesneden op BOOG graden."""
    tm = math.radians(BOOG)
    A = DAK_X / math.sin(tm)
    B = (NOK_Z - DAK_RAND_Z) / (1 - math.cos(tm))
    zc = NOK_Z - B
    return [(A * math.sin(t), zc + B * math.cos(t)) for t in (-tm + 2 * tm * i / n for i in range(n + 1))]


PROF = dak_profiel()
DAK = E.Dakvlak(PROF, DAK_Y0, HEUP_Y + 0.35, as_x=True)    # overlap: geen naad bij de heup
HEUP = E.Heup(PROF, HEUP_Y, HEUP_K, vierkant=5.0)


def dak_onder(x, extra=0.0):
    """z van de onderkant van het riet boven x (benadering, voor de gevelboog)."""
    tm = math.radians(BOOG)
    A = DAK_X / math.sin(tm)
    B = (NOK_Z - DAK_RAND_Z) / (1 - math.cos(tm))
    t = math.asin(max(-1, min(1, x / A)))
    return NOK_Z - B + B * math.cos(t) - RIET_DIK - extra


# --- Muren --------------------------------------------------------------------------
def prisma(name, poly, y0, y1, mat):
    """Veelhoek in (x, z), uitgetrokken van y0 tot y1."""
    bm = bmesh.new()
    vs0 = [bm.verts.new((x, y0, z)) for x, z in poly]
    vs1 = [bm.verts.new((x, y1, z)) for x, z in poly]
    bm.faces.new(vs0)
    bm.faces.new(list(reversed(vs1)))
    n = len(poly)
    for i in range(n):
        j = (i + 1) % n
        bm.faces.new([vs0[i], vs1[i], vs1[j], vs0[j]])
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    o = bpy.data.objects.new(name, me)
    E.col().objects.link(o)
    return E.put(o, mat, smooth=False)


def wand_y(name, x_buiten, inw, y0, y1, z1, gaten, mat):
    """Wand langs y (buitenvlak op x_buiten, dikte naar binnen in richting inw), met rechthoekige gaten
    [(ya, yb, za, zb)]: verticale stroken tussen de gatranden."""
    br = sorted({y0, y1} | {g[0] for g in gaten} | {g[1] for g in gaten})
    xm = x_buiten + inw * MUUR / 2
    for a, b in zip(br, br[1:]):
        if b - a < 1e-4:
            continue
        m = (a + b) / 2
        dicht = sorted((g[2], g[3]) for g in gaten if g[0] <= m <= g[1])
        z = 0.0
        for za, zb in dicht + [(z1, z1)]:
            if za - z > 1e-4:
                box(name, (xm, m, (z + za) / 2), (MUUR, b - a, za - z), mat)
            z = zb


# voorgevel (-X): wit pleister met deur en twee ramen
gaten_v = [(DEUR[0] - DEUR[1] / 2, DEUR[0] + DEUR[1] / 2, 0.0, DEUR[2])]
gaten_v += [(r - RAAM[0] / 2, r + RAAM[0] / 2, RAAM[1], RAAM[2]) for r in RAMEN]
wand_y("pleister_voor", -HW + 0.03, 1, -HL, HL, WAND_TOP, gaten_v, M_PLEISTER)
# achtergevel (+X): koeienvlekken, raampje
wand_y("pleister_achter", HW - 0.03, -1, -HL, HL, WAND_TOP, [(0.6, 1.2, 0.9, 1.5)], M_KOE)


def gevel(name, y_buiten, inw, mat):
    poly = [(-HW, 0.0), (HW, 0.0)]
    for i in range(24, -1, -1):
        x = -HW + 2 * HW * i / 24
        poly.append((x, max(dak_onder(x, 0.02), 0.5)))
    y0, y1 = sorted((y_buiten + inw * 0.03, y_buiten + inw * (0.03 + MUUR)))
    return prisma(name, poly, y0, y1, mat)


gevel("gevel_voor", -HL, 1, M_KOE)
box("gevel_achter", (0, HL - 0.03 - MUUR / 2, WAND_TOP / 2), (2 * HW - 0.06, MUUR, WAND_TOP), M_PLEISTER)

# binnen: donker (door deur en ramen zie je geen lucht), vloer
box("binnen", (0, 0, 1.3), (2 * HW - 2 * MUUR - 0.06, 2 * HL - 2 * MUUR - 0.06, 2.6), M_DONKER)
for o in [bpy.data.objects["binnen"]]:
    for p in o.data.polygons:                          # normalen naar binnen
        p.flip()

# --- Vakwerk ------------------------------------------------------------------------
B = 0.22                                               # balkdikte
XV = -HW - 0.01                                        # balken staan iets voor het pleister
for y in STIJLEN_VOOR:
    yy = max(min(y, HL - B / 2), -HL + B / 2)
    balk("stijl", (XV + B / 2, yy, 0.0), (XV + B / 2, yy, WAND_TOP), B, M_BALK)
balk("plaat_voor", (XV + B / 2, -HL, WAND_TOP - 0.1), (XV + B / 2, HL, WAND_TOP - 0.1), (0.2, 0.18), M_BALK)
balk("drempel_voor", (XV + B / 2, -HL, 0.08), (XV + B / 2, HL, 0.08), (0.21, 0.16), M_BALK)
for r in RAMEN:                                         # raamregels
    for z in (RAAM[1] - 0.05, RAAM[2] + 0.05):
        balk("raamregel", (XV + 0.06, r - RAAM[0] / 2 - 0.06, z), (XV + 0.06, r + RAAM[0] / 2 + 0.06, z), (0.14, 0.11), M_BALK)
balk("latei", (XV + 0.07, DEUR[0] - DEUR[1] / 2 - 0.08, DEUR[2] + 0.06),
     (XV + 0.07, DEUR[0] + DEUR[1] / 2 + 0.08, DEUR[2] + 0.06), (0.16, 0.13), M_BALK)

# gevel (-Y): hoekstijlen, bint, middenregel, twee stijlen, gebogen korbelen
YV = -HL - 0.01
for x in (-HW + B / 2, HW - B / 2):
    balk("hoekstijl", (x, YV + B / 2, 0.0), (x, YV + B / 2, BINT + 0.1), B, M_BALK)
balk("bint", (-HW - 0.1, YV + B / 2, BINT), (HW + 0.1, YV + B / 2, BINT), (0.2, 0.2), M_BALK)
balk("onderregel", (-HW, YV + B / 2, 0.08), (HW, YV + B / 2, 0.08), (0.17, 0.17), M_BALK)
for x in (-0.55, 0.62):
    balk("gevelstijl", (x, YV + B / 2, 0.0), (x, YV + B / 2, BINT), (0.16, 0.18), M_BALK)
balk("middenregel", (-HW, YV + B / 2, REGEL), (-0.55, YV + B / 2, REGEL), (0.16, 0.15), M_BALK)
balk("middenregel", (0.62, YV + B / 2, REGEL - 0.15), (HW, YV + B / 2, REGEL - 0.15), (0.16, 0.15), M_BALK)
balk("schoor", (0.62, YV + B / 2, 0.15), (HW - 0.2, YV + B / 2, BINT - 0.15), (0.15, 0.15), M_BALK)


def korbeel(x0, z0, x1, z1, bocht, n=7):
    """Gebogen schoor van stukjes balk langs een boog."""
    pts = []
    for i in range(n + 1):
        t = i / n
        p = Vector((x0 + (x1 - x0) * t, z0 + (z1 - z0) * t))
        d = Vector((x1 - x0, z1 - z0)).normalized()
        nrm = Vector((-d.y, d.x))
        pts.append(p + nrm * bocht * math.sin(math.pi * t))
    for a, b in zip(pts, pts[1:]):
        balk("korbeel", (a.x, YV + B / 2, a.y), (b.x, YV + B / 2, b.y), (0.14, 0.14), M_BALK, bevel=0.01)


korbeel(-HW + 0.15, REGEL + 0.05, -0.62, 0.2, -0.22)
korbeel(-0.5, BINT - 0.05, -HW + 0.2, REGEL + 0.1, 0.15)
# windveer langs de boog (bruine rand onder het riet)
wv = [(x, dak_onder(x, 0.04)) for x in [-HW - 0.25 + (2 * HW + 0.5) * i / 20 for i in range(21)]]
for (x0, z0), (x1, z1) in zip(wv, wv[1:]):
    balk("windveer", (x0, YV - 0.02, z0), (x1, YV - 0.02, z1), (0.12, 0.16), M_BALK, bevel=0.008)

# achterkant (+X) en achtergevel: alleen hoekstijlen
for y in (-HL + B / 2, HL - B / 2):
    balk("stijl_achter", (HW + 0.01 - B / 2, y, 0.0), (HW + 0.01 - B / 2, y, WAND_TOP), B, M_BALK)
for y in (-1.0, 0.9):
    balk("stijl_achter", (HW + 0.01 - B / 2, y, 0.0), (HW + 0.01 - B / 2, y, WAND_TOP), B, M_BALK)

# --- Deur ---------------------------------------------------------------------------
dy0, dy1 = DEUR[0] - DEUR[1] / 2, DEUR[0] + DEUR[1] / 2
delen = []
n_pl = 5
pw = (DEUR[1] - 0.04) / n_pl
for i in range(n_pl):
    y = dy1 - 0.02 - pw * (i + 0.5)
    delen.append(box("deurplank", (-HW + 0.07 + random.uniform(-0.004, 0.004), y, (DEUR[2] - 0.02) / 2 + 0.01),
                     (0.045, pw - 0.01, DEUR[2] - 0.03 - random.uniform(0, 0.03)), M_DEUR, bevel=0.008))
for z in (0.35, DEUR[2] - 0.35):
    delen.append(box("klamp", (-HW + 0.035, DEUR[0], z), (0.03, DEUR[1] - 0.12, 0.11), M_DEUR, bevel=0.008))
d = Vector((0, -(DEUR[1] - 0.2), DEUR[2] - 0.9))
sch = box("schoorplank", (-HW + 0.035, DEUR[0], DEUR[2] / 2), (0.03, 0.1, d.length), M_DEUR, bevel=0.008)
sch.rotation_euler.x = math.atan2(-d.y, d.z)
delen.append(sch)
for z in (0.35, DEUR[2] - 0.35):                        # hengsels
    delen.append(box("hengsel", (-HW + 0.015, dy1 - 0.25, z), (0.012, 0.45, 0.045), M_IJZER))
bpy.ops.mesh.primitive_torus_add(major_radius=0.05, minor_radius=0.009, location=(-HW + 0.01, dy0 + 0.18, 1.0),
                                 rotation=(0, math.pi / 2, 0))
delen.append(E.put(bpy.context.object, M_IJZER))
# scharnier op de +Y-kant: lokaal x naar buiten (-X), y langs het blad (-Y), z omhoog
T = Matrix(((-1, 0, 0, -HW + 0.095), (0, -1, 0, dy1 - 0.01), (0, 0, 1, 0), (0, 0, 0, 1)))
DEUR_E = E.scharnier("deur", delen, T)
DEUR_E["open_graden"] = DEUR_OPEN
if "deur" in OPTS:
    E.zet_deur(DEUR_E, float(OPTS["deur"]))
# kozijn
for y in (dy0 - 0.05, dy1 + 0.05):
    balk("kozijn", (XV + 0.08, y, 0.0), (XV + 0.08, y, DEUR[2]), (0.16, 0.1), M_BALK)
box("stoep", (-HW - 0.25, DEUR[0], 0.03), (0.45, DEUR[1] + 0.3, 0.08), M_STEEN, bevel=0.02, jitter=0.01)

# --- Ramen ----------------------------------------------------------------------------
for r in RAMEN:
    w, z0, z1 = RAAM
    box("ruit", (-HW + 0.14, r, (z0 + z1) / 2), (0.02, w, z1 - z0), M_GLAS)
    for yy in (r - w / 2 + 0.03, r, r + w / 2 - 0.03):
        box("roede", (-HW + 0.1, yy, (z0 + z1) / 2), (0.05, 0.045, z1 - z0), M_BALK)
    for zz in (z0 + 0.03, (z0 + z1) / 2, z1 - 0.03):
        box("roede", (-HW + 0.1, r, zz), (0.05, w, 0.045), M_BALK)
    for yy in (r - w / 2, r + w / 2):
        box("dag", (-HW + 0.07, yy, (z0 + z1) / 2), (0.16, 0.03, z1 - z0), M_PLEISTER)
    # bloembak
    bz = z0 - 0.12
    box("bloembak", (-HW - 0.14, r, bz), (0.2, w + 0.12, 0.16), M_BAK, bevel=0.012, jitter=0.006)
    box("aarde", (-HW - 0.14, r, bz + 0.075), (0.16, w + 0.06, 0.02), M_MODDER)
    for k in range(int(w / 0.04)):
        y = r - w / 2 + 0.03 + random.random() * (w - 0.04)
        x = -HW - 0.14 + random.uniform(-0.06, 0.06)
        z = bz + 0.09 + random.uniform(0, 0.12)
        if random.random() < 0.55:
            E.bol("blad", (x, y, z), random.uniform(0.02, 0.035), M_BLAD, (1, 1, 0.6), sub=1)
        else:
            E.bol("bloem", (x, y, z + 0.03), random.uniform(0.018, 0.03), random.choice(M_BLOEM), sub=1)

# --- Schoorsteen ----------------------------------------------------------------------
stenen = E.Stenen(M_STEEN, n=10, seed=200)


def sch_w(z):
    f = (z - SCH_Z0) / (SCH_Z1 - SCH_Z0)
    return SCH_W0 + (SCH_W1 - SCH_W0) * f


kern = []
for k in range(8):                                      # kern (specie), taps
    za, zb = SCH_Z0 + (SCH_Z1 - SCH_Z0) * k / 8, SCH_Z0 + (SCH_Z1 - SCH_Z0) * (k + 1) / 8
    w = sch_w((za + zb) / 2) - 0.06
    kern.append(box("schoorsteenkern", (SCH[0], SCH[1], (za + zb) / 2), (2 * w, 2 * w, zb - za), M_SPECIE))
z = 3.0
rij = 0
while z < SCH_Z1 - 0.05:
    h = random.uniform(0.13, 0.2)
    w = sch_w(z + h / 2)
    for zijde in range(4):
        rz = zijde * math.pi / 2
        d = Vector((math.cos(rz), math.sin(rz), 0))     # buitennormaal
        t = Vector((-d.y, d.x, 0))
        s = -w + (0.12 if (rij + zijde) % 2 else 0.0)
        while s < w - 0.02:
            l = min(random.uniform(0.22, 0.42), w + 0.05 - s)
            m = s + l / 2
            pos = Vector((SCH[0], SCH[1], z + h / 2)) + d * (w - 0.08) + t * m
            stenen.zet(pos, (0.2, l * 1.06, h * 1.12), rz + random.uniform(-0.04, 0.04),
                       (random.uniform(-0.05, 0.05), random.uniform(-0.05, 0.05)))
            s += l
    z += h
    rij += 1
# paarse rand met mond
RZ = SCH_Z1
rw = SCH_W1 + 0.0
rand_st = E.Stenen(M_PAARS_RAND, n=5, seed=250, p=8.0, bumps=0.06, cuts=3)
for zijde in range(4):                                   # rand van geverfde platen, twee per zijde
    a = zijde * math.pi / 2
    d = Vector((math.cos(a), math.sin(a), 0))
    t = Vector((-d.y, d.x, 0))
    for m in (-rw / 2, rw / 2):
        pos = Vector((SCH[0], SCH[1], RZ + 0.07)) + d * (rw - 0.08) + t * m
        rand_st.zet(pos, (0.17, rw * 1.08, 0.14), a + random.uniform(-0.03, 0.03),
                    (random.uniform(-0.03, 0.03), random.uniform(-0.03, 0.03)))
box("schoorsteenmond", (SCH[0], SCH[1], RZ + 0.05), (2 * rw - 0.3, 2 * rw - 0.3, 0.1), M_DONKER)

# --- Dakkapel (achterdak, paarse pannen) ---------------------------------------------
kx0, kx1, ky0, ky1 = KAPEL
kap_stenen = E.Stenen(M_STEEN, n=6, seed=300)
kz0 = 2.8
kz1 = KAPEL_NOK - (ky1 - ky0) / 2 * math.tan(math.radians(32))
for y in (ky0, ky1):                                   # wangen van steen
    kap_stenen.muur((kx0, y), (kx1, y), kz0, kz1, 0.18, hs=(0.1, 0.16), ls=(0.18, 0.34))
box("kapelkern", ((kx0 + kx1) / 2, (ky0 + ky1) / 2, (kz0 + kz1) / 2), (kx1 - kx0 - 0.05, ky1 - ky0 - 0.1, kz1 - kz0), M_SPECIE)
box("kapelraam", (kx1 + 0.01, (ky0 + ky1) / 2, (kz0 + kz1) / 2 + 0.1), (0.04, 0.5, 0.45), M_GLAS)
for y in (ky0 + 0.12, ky1 - 0.12):
    box("kapelstijl", (kx1 + 0.02, y, (kz0 + kz1) / 2), (0.12, 0.12, kz1 - kz0), M_BALK)
# dakje: twee vlakken, pannen als UV-vlak in meters, licht doorgezakt
hoek = math.radians(32)
oversteek = 0.18
for sg in (-1, 1):
    yb = (ky0 + ky1) / 2
    ye = yb + sg * ((ky1 - ky0) / 2 + oversteek)
    vs, fs, uvs = [], [], []
    nx, ny = 6, 4
    for i in range(nx + 1):
        for j in range(ny + 1):
            x = kx0 - 0.1 + (kx1 - kx0 + 0.3) * i / nx
            y = yb + (ye - yb) * j / ny
            zz = KAPEL_NOK + 0.04 - abs(y - yb) * math.tan(hoek) - 0.03 * math.sin(math.pi * i / nx) * (j / ny)
            vs.append((x, y, zz))
            uvs.append((x, abs(y - yb) / math.cos(hoek)))
    for i in range(nx):
        for j in range(ny):
            a = i * (ny + 1) + j
            f = [a, a + ny + 1, a + ny + 2, a + 1]
            fs.append(f if sg > 0 else list(reversed(f)))
    o = E.mesh_obj("kapeldak", vs, fs, M_PAARS, smooth=True)
    sol = o.modifiers.new("dik", "SOLIDIFY")
    sol.thickness = 0.06
    uvl = o.data.uv_layers.new(name="UVMap")
    for poly in o.data.polygons:
        for li in poly.loop_indices:
            uvl.data[li].uv = uvs[o.data.loops[li].vertex_index]
box("kapelnok", ((kx0 + kx1) / 2 + 0.05, (ky0 + ky1) / 2, KAPEL_NOK + 0.08), (kx1 - kx0 + 0.3, 0.12, 0.08), M_PAARS_RAND, bevel=0.02)

# --- Rieten dak -----------------------------------------------------------------------
rnd = random.Random(11)


def geraakt(p):
    """Geen halmen waar de schoorsteen of de dakkapel door het dak steekt."""
    if abs(p.x - SCH[0]) < SCH_W0 + 0.02 and abs(p.y - SCH[1]) < SCH_W0 + 0.02:
        return True
    return kx0 + 0.05 < p.x < kx1 + 0.1 and ky0 + 0.05 < p.y < ky1 - 0.05


skip = lambda u, s: geraakt(DAK.P(u, s))
skip_h = lambda u, s: geraakt(HEUP.P(u, s))
schil = DAK.schil("rietschil", M_RIET, dik=RIET_DIK, du=0.12, ds=0.09, rand_dik=RIET_RAND)
schil_h = HEUP.schil("rietschil_heup", M_RIET, dik=RIET_DIK, du=0.12, ds=0.09, rand_dik=RIET_RAND)
RUIG = dict(per_bos=12, lengte=(0.6, 1.05), hang=0.26, bult=0.11, rommel=0.1)
riet = [DAK.halmen("dakhalmen", M_HALM, rnd, skip=skip, **RUIG),
        HEUP.halmen("heuphalmen", M_HALM, rnd, skip=skip_h, kant=(1,), **RUIG),
        DAK.nokrol("nokhalmen", M_HALM, rnd, skip=lambda u, s: skip(u, 0.3) or skip(u, -0.3)),
        DAK.gevelrol("gevelrol_voor", M_HALM, rnd, DAK_Y0 + 0.06, -1, r=0.16, per_m=380, uit=0.0)]

# --- Varkenshok -------------------------------------------------------------------------
hx0, hx1, hy0, hy1 = HOK
hok_stenen = E.Stenen(M_HOKSTEEN, n=8, seed=400)
hok_stenen.muur((hx0, hy0), (hx1, hy0), 0.0, HOK_H, 0.32)           # voorkant (-Y)
hok_stenen.muur((hx0, hy1), (hx1, hy1), 0.0, HOK_H, 0.32)           # achter
hok_stenen.muur((hx0, hy0 + 0.15), (hx0, hy1 - 0.15), 0.0, HOK_H, 0.32)
for (x, y) in ((hx0, hy0), (hx1, hy0), (hx0, hy1), (hx1, hy1)):
    balk("hokpaal", (x, y, 0.0), (x + random.uniform(-0.02, 0.02), y, HOK_H + 0.28), 0.12, M_PLANK)
for z in (0.18, 0.42):                                              # planken aan de +X-kant (hekje)
    balk("hokplank", (hx1, hy0, z), (hx1, hy1, z + random.uniform(-0.03, 0.03)), (0.05, 0.16), M_PLANK)
for k in range(5):
    x = hx0 + 0.25 + (hx1 - hx0 - 0.5) * k / 4
    balk("muurplank", (x - 0.12, hy0 - 0.13, 0.08 + 0.02 * k), (x + 0.12, hy0 - 0.13, 0.45), (0.04, 0.12), M_PLANK)
box("hokgrond", ((hx0 + hx1) / 2, (hy0 + hy1) / 2, 0.03), (hx1 - hx0 - 0.1, hy1 - hy0 - 0.1, 0.06), M_GROND)
box("hokmodder", ((hx0 + hx1) / 2 + 0.25, (hy0 + hy1) / 2 - 0.15, 0.055), (0.7, 0.5, 0.03), M_MODDER, jitter=0.03)
for k in range(10):
    E.grasbos("hokgras", random.uniform(hx0 + 0.2, hx1 - 0.2), random.uniform(hy0 + 0.2, hy1 - 0.2), M_GRAS,
              n=4, hgt=0.16, seed=50 + k)
box("trog", (hx0 + 0.35, hy1 - 0.3, 0.1), (0.5, 0.22, 0.16), M_PLANK, bevel=0.02)


def varken(x, y, rz):
    """Varken van bollen: lijf, kop, snuit, oren, poten, krulstaart."""
    R = Matrix.Rotation(rz, 3, "Z") @ Matrix.Scale(1.35, 3)      # flink varken, leesbaar op afstand
    o = Vector((x, y, 0))
    delen = []

    def p(v):
        return o + R @ Vector(v)
    delen.append(E.bol("varken", p((0, 0, 0.3)), 0.2, M_VARKEN, (1.75, 1.0, 0.95)))
    delen.append(E.bol("varken", p((0.34, 0, 0.33)), 0.13, M_VARKEN, (1.0, 1.0, 0.95)))
    delen.append(E.cyl("varken", p((0.46, 0, 0.31)), 0.06, 0.08, M_VARKEN, rot=(0, math.pi / 2, rz)))
    for sy in (-1, 1):
        e = E.bol("varken", p((0.38, sy * 0.08, 0.44)), 0.05, M_VARKEN, (0.6, 1.0, 1.3), sub=2)
        e.rotation_euler = (sy * 0.5, 0.4, rz)
        delen.append(e)
        for sx in (-0.2, 0.2):
            delen.append(E.cyl("varken", p((sx, sy * 0.1, 0.09)), 0.045, 0.18, M_VARKEN))
    pts = [tuple(p((-0.33 - 0.03 * t, 0.03 * math.sin(t * 9), 0.34 + 0.03 * math.cos(t * 9)))) for t in [i / 10 for i in range(11)]]
    delen.append(E.tube("varken", pts, 0.012, M_VARKEN, sides=5))
    return delen


varken((hx0 + hx1) / 2 - 0.1, (hy0 + hy1) / 2 + 0.1, math.radians(200))
for k, (x, y, sx, sy) in enumerate(((hx0 - 0.35, (hy0 + hy1) / 2, 0.5, 1.3), ((hx0 + hx1) / 2, hy0 - 0.4, 1.5, 0.5),
                                       (-HW - 0.6, DEUR[0], 0.7, 1.3))):
    m = box("modder", (x, y, 0.004), (sx, sy, 0.006), M_MODDER, jitter=0.04)
    m.modifiers.new("r", "SUBSURF").levels = 2           # zachte, ronde vlek
voetst = E.Stenen(M_HOKSTEEN, n=4, seed=430)
for k in range(9):
    x = hx0 + (hx1 - hx0) * k / 8
    voetst.zet((x, hy0 - 0.2, 0.03), (0.22, 0.14, 0.08), random.uniform(-0.3, 0.3))
r_h = random.Random(77)
hokstro = []
for _ in range(2500):                                   # strooisel in het hok
    x, y = r_h.uniform(hx0 + 0.15, hx1 - 0.1), r_h.uniform(hy0 + 0.15, hy1 - 0.15)
    a, L = r_h.uniform(0, 6.3), r_h.uniform(0.06, 0.18)
    d = Vector((math.cos(a), math.sin(a), r_h.uniform(-0.2, 0.3))) * L
    hokstro.append([tuple(Vector((x, y, 0.065)) + d * (k / 3 - 0.5) + Vector((0, 0, 0.005 * k))) for k in range(4)])
E.strands("hokstro", hokstro, E.mat_halm("hokstro_m", [(0.0, (0.3, 0.17, 0.04)), (0.6, (0.7, 0.5, 0.18)), (1.0, (0.9, 0.75, 0.4))]),
          [r_h.random() for _ in hokstro], lambda u: 0.003)
for k in range(8):                                     # pollen langs de voet van de muurtjes
    a = k / 8
    E.grasbos("voetgras", hx0 + (hx1 - hx0) * a + 0.1, hy0 - 0.2, M_GRAS, n=5, hgt=0.22, seed=90 + k)
    E.grasbos("voetgras", hx0 - 0.2, hy0 + (hy1 - hy0) * a, M_GRAS, n=4, hgt=0.18, seed=120 + k)
# graspollen zoals de sprite: links van het hok
E.grasbos("gras", hx0 - 0.25, hy1 + 0.15, M_GRAS, n=14, hgt=0.55, seed=1)
E.grasbos("gras", hx0 - 0.35, hy0 - 0.2, M_GRAS, n=14, hgt=0.5, seed=2)
E.grasbos("gras", -HW - 0.2, -HL + 0.4, M_GRAS, n=6, hgt=0.25, seed=3)

# --- Ankers ---------------------------------------------------------------------------
E.anker("deur_drempel", (-HW - 0.45, DEUR[0], 0.0))                 # looppunt voor de deur
E.anker("rook_bron", (SCH[0], SCH[1], RZ + 0.12))                   # schoorsteenmond
E.anker("melkplek", (-0.4, -HL - 1.6, 0.0))                         # dorpeling melkt hier een koe (koe op +x)
E.anker("varkenshok", ((hx0 + hx1) / 2, (hy0 + hy1) / 2, 0.06))     # midden van het hok
E.anker("varkenshok_voer", (hx0 - 0.3, hy1 - 0.3, 0.0))             # buiten bij de trog: voeren

# --- Licht, camera, render ------------------------------------------------------------
dak_objs = [schil, schil_h] + riet + [o for o in scene.objects if o.name.startswith(("kapeldak", "kapelnok"))]
vanger = E.licht(scene, dak=dak_objs)
cam = E.camera(scene, SPRITE, SCHAAL, REF_WERELD, REF_PX)
tri, halm = E.tel()
print("TRIS", tri, "HALMEN", halm, "STENEN", len(stenen.uit) + len(hok_stenen.uit) + len(kap_stenen.uit))
os.makedirs(E.PREVIEW, exist_ok=True)
bpy.ops.wm.save_as_mainfile(filepath=BLEND)
if "geen_render" not in OPTS:
    E.render(scene, UIT, SAMPLES)
