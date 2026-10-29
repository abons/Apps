"""Gereedschapsloods (toolshed, gilde van de bouwers) uit Beasts & Bumpkins nagebouwd in 3D.

Smalle begane grond van ruwe steen met een rondboogdeur, daarop een bredere vakwerkverdieping op
houten stijlen, een bloembak, een uitstekende balk en een lang paars pannendak. Een reusachtig
ijzeren aambeeld steekt in de lengte door de verdieping: de hoorn uit de linkergevel (-X), de hiel
uit de rechter (+X). Maten teruggerekend uit toolshed.png (87,5 px per meter op 4x) en het
goedgekeurde concept (gereedschapsloods.jpg).

Draaien (headless):
  blender -b -P gereedschapsloods.py -- [schaal=4] [snel] [geen_glb] [geen_render] [deur=graden]
Schrijft gereedschapsloods.blend en .glb naast dit script en preview/gereedschapsloods_render.png.
"""
import math
import os
import random
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from loods_molen_lib import *  # noqa: E402,F401,F403
from mathutils import Matrix, Vector  # noqa: E402

NAAM = "gereedschapsloods"
SPRITE = SC + "concept/upload/toolshed.png"
W_PX, H_PX = 648, 516                  # 4x-sprite
REF_PX = (305, 512)                    # voet van de stijl linksvoor in de sprite

# --- Maten (meters; lokaal: stijl linksvoor op de oorsprong, voorgevel op y = 0, -Y naar voren) --
GX0, GX1, GY0, GY1 = 0.0, 2.3, 0.0, 1.9        # stijlen van de begane grond
G_H = 2.0                                       # begane grond tot onderkant verdieping
UX0, UX1, UY0, UY1 = -0.15, 3.5, -0.12, 2.35    # verdieping (overstek naar rechts en achter)
U_Z1 = 3.45                                     # bovenkant muurplaat
YC = (UY0 + UY1) / 2                            # nok
DAK_HOEK = math.radians(28)
OVERSTEK, VERGE_L, VERGE_R = 0.25, 0.55, 0.25
NOK_Z = U_Z1 + (YC - UY0) * math.tan(DAK_HOEK)
DEUR_X, DEUR_B, DEUR_H = 1.42, 0.80, 1.62       # rondboogdeur in de voorgevel
AAMBEELD_Z1 = 3.58                              # werkvlak (bovenkant)
AAMBEELD_Z0 = 2.12                              # onderkant van de hoorn bij de gevel
AY0, AY1 = YC - 0.68, YC + 0.68                 # breedte van het aambeeld
HOORN_TIP = -3.6
HIEL_X1, HIEL_Z0 = 5.3, 2.12
BALK_Y = -1.0                                   # uitstekende balk rechtsvoor, tot hier naar voren
OX, OY = 1.6, 1.1                               # verschuiving naar het midden (spel-oorsprong)

# --- Materialen --------------------------------------------------------------------------------
M_STEEN = mat_steen("steen", lo=(0.16, 0.15, 0.12), hi=(0.74, 0.68, 0.55), moss=0.35, lichen=0.6)
M_KWARTIER = mat_steen("hoeksteen", lo=(0.2, 0.19, 0.16), hi=(0.75, 0.7, 0.6), moss=0.2, lichen=0.5)
M_STOEP = mat_steen("stoep", lo=(0.12, 0.12, 0.10), hi=(0.55, 0.54, 0.47), moss=0.4)
M_SPECIE = mat_specie("specie", (0.16, 0.14, 0.11), (0.34, 0.30, 0.24))
M_BALK = mat_hout("balk", "rough_wood", (0.10, 0.06, 0.03), (0.42, 0.29, 0.17), rand=5.0, grijs=0.5)
M_PLANK = mat_hout("plank", "weathered_brown_planks", (0.14, 0.08, 0.04), (0.50, 0.33, 0.17), 0.5, 5.0,
                   rot=math.pi / 2)
M_DAKBORD = mat_hout("dakbord", "weathered_brown_planks", (0.03, 0.016, 0.008), (0.14, 0.08, 0.04), 0.6, 3.0)
M_PLEISTER = mat_pleister("pleister", wit=(0.82, 0.79, 0.70), vuil=(0.5, 0.45, 0.36), afbladder=0.74)
M_IJZER = mat_ijzer("ijzer")
M_BESLAG = mat_flat("beslag", (0.02, 0.02, 0.02), 0.45, "ijzer")
M_PAN = mat_dakpan("dakpan", lo=(0.14, 0.04, 0.2), hi=(0.5, 0.22, 0.6))
M_RUIT = mat_ruit("ruit")
M_GRAS = mat_gras("gras")
M_BLAD = mat_blad("blad")
M_AARDE = mat_flat("aarde", (0.05, 0.03, 0.015), 1.0)
BLOEM = [mat_flat("bloem_rood", (0.6, 0.02, 0.01), 0.6), mat_flat("bloem_geel", (0.8, 0.5, 0.02), 0.6),
         mat_flat("bloem_wit", (0.75, 0.72, 0.65), 0.6), mat_flat("bloem_paars", (0.3, 0.05, 0.5), 0.6),
         mat_flat("bloem_oranje", (0.85, 0.22, 0.02), 0.6)]
stenen_maken(M_STEEN, p=11.0, bumps=0.05)                 # hoekiger dan de hut: gekapte breuksteen

# --- Begane grond: stijlen, stenen muren, deur ---------------------------------------------------
for (px, py) in ((GX0, GY0), (GX1, GY0), (GX0, GY1), (GX1, GY1)):
    balk("stijl", (px, py, 0.0), (px, py, G_H + 0.02), 0.22, 0.22, M_BALK, bevel=0.03, rol=random.uniform(-0.05, 0.05),
         ruw=0.012)
# kern achter de stenen (donkere leem), zodat er nergens een gat is
box("kern", ((GX0 + GX1) / 2, (GY0 + GY1) / 2, G_H / 2), (GX1 - GX0 - 0.25, GY1 - GY0 - 0.25, G_H), M_SPECIE)
T0 = GX0 + 0.13                                  # t langs de voormuur = x - T0
ZC = DEUR_H + 0.08 - (DEUR_B + 0.08) / 2          # middelpunt van de boog
gaten_voor = [(DEUR_X - DEUR_B / 2 - 0.05 - T0, DEUR_X + DEUR_B / 2 + 0.05 - T0, -1, DEUR_H + 0.3),
              (DEUR_X - DEUR_B / 2 - 0.36 - T0, DEUR_X + DEUR_B / 2 + 0.36 - T0, -1, ZC + 0.05)]
LAGEN = dict(depth=0.16, uit=0.003, hs=(0.085, 0.12), ls=(0.17, 0.32))     # gelaagd breuksteen, platte stenen
flat_wall((GX0 + 0.13, GY0 + 0.03), (GX1 - 0.13, GY0 + 0.03), 0.0, G_H, gaten_voor, **LAGEN)
flat_wall((GX0 + 0.03, GY1 - 0.13), (GX0 + 0.03, GY0 + 0.13), 0.0, G_H, [], **LAGEN)
# rondboog van wiggen en negge-stenen om de deur, deuropening donker
boog_stenen(DEUR_X, GY0 + 0.03, -math.pi / 2, 0.0, DEUR_B + 0.08, DEUR_H + 0.08, dikte=0.2, diep=0.26, mat=M_KWARTIER)
box("deurgat", (DEUR_X, GY0 + 0.15, DEUR_H / 2), (DEUR_B + 0.06, 0.05, DEUR_H), M_SPECIE)
dx = DEUR_X
# deur draait naar buiten (scharnier links); de onderkant ligt op 0,1 m, boven de stoep
delen = plank_door("deurplank", dx, GY0 + 0.07, 0.1, DEUR_B, DEUR_H - 0.1, -math.pi / 2, M_PLANK, M_BESLAG, n=5)
scharnier("deur", delen, dx, GY0 + 0.07, DEUR_B, -math.pi / 2)
stone((DEUR_X, GY0 - 0.3, 0.0), (1.0, 0.5, 0.14), 0.03, M_STOEP)
stone((DEUR_X + 0.1, GY0 - 0.7, -0.01), (0.8, 0.36, 0.1), -0.08, M_STOEP)

# --- Verdieping: balklaag, vakwerk, pleister --------------------------------------------------------
Z0 = G_H
# zware dorpelbalken rondom en kinderbinten die voor uitsteken
for (p, q) in (((UX0, UY0, Z0 + 0.1), (UX1, UY0, Z0 + 0.1)), ((UX0, UY0, Z0 + 0.1), (UX0, UY1, Z0 + 0.1)),
               ((UX1, UY0, Z0 + 0.1), (UX1, UY1, Z0 + 0.1)), ((UX0, UY1, Z0 + 0.1), (UX1, UY1, Z0 + 0.1))):
    balk("dorpel", p, q, 0.24, 0.2, M_BALK, bevel=0.02, ruw=0.01)
balk("dwarsbalk", (GX1, GY0, Z0 - 0.08), (GX1, GY1, Z0 - 0.08), 0.22, 0.18, M_BALK, ruw=0.01)
balk("uitstekende_balk", (3.3, UY1 - 0.3, Z0 - 0.04), (3.3, BALK_Y, Z0 - 0.04), 0.21, 0.21, M_BALK, bevel=0.02,
     ruw=0.012)
# korbelen: schoren van de stijlen naar de dorpel (rechts dragen ze de overstek)
for (px, py, dxx, dyy) in ((GX1, GY0, 0.6, 0.0), (GX1, GY0, -0.45, 0.0), (GX0, GY1, 0.0, 0.42), (GX1, GY1, 0.6, 0.0)):
    balk("korbeel", (px, py, Z0 - 0.66), (px + dxx, py + dyy, Z0 - 0.02), 0.13, 0.15, M_BALK, ruw=0.008)

WZ0, WZ1 = Z0 + 0.2, U_Z1 - 0.1                  # vakwerk tussen dorpel en muurplaat
VENSTER = (0.92, 2.14, 2.62, 3.28)               # x0, x1, z0, z1 in de voorgevel
STIJLEN_V = [UX0 + 0.12, 0.86, 2.2, UX1 - 0.12]
REGEL_Z = 2.6


def pleister_vak(x0, x1, z0, z1, y, dik=0.12):
    if x1 - x0 > 0.02 and z1 - z0 > 0.02:
        box("pleister", ((x0 + x1) / 2, y, (z0 + z1) / 2), (x1 - x0, dik, z1 - z0), M_PLEISTER)


def pleister_vak_x(y0, y1, z0, z1, x, dik=0.12):
    if y1 - y0 > 0.02 and z1 - z0 > 0.02:
        box("pleister", (x, (y0 + y1) / 2, (z0 + z1) / 2), (dik, y1 - y0, z1 - z0), M_PLEISTER)


# voorgevel (y = UY0): pleister achter het hout, raamgat vrij
yv = UY0 + 0.05
pleister_vak(UX0 + 0.05, VENSTER[0], WZ0, WZ1, yv)
pleister_vak(VENSTER[1], UX1 - 0.05, WZ0, WZ1, yv)
pleister_vak(VENSTER[0], VENSTER[1], WZ0, VENSTER[2], yv)
pleister_vak(VENSTER[0], VENSTER[1], VENSTER[3], WZ1, yv)
yh = UY0 - 0.01                                  # hout steekt 4 cm voor het pleister uit
for x in STIJLEN_V:
    balk("stijl_v", (x, yh, WZ0 - 0.02), (x, yh, WZ1 + 0.02), 0.17, 0.12, M_BALK, ruw=0.008, rol=random.uniform(-0.02, 0.02))
balk("muurplaat", (UX0 - 0.05, yh, U_Z1 - 0.06), (UX1 + 0.05, yh, U_Z1 - 0.06), 0.14, 0.18, M_BALK, ruw=0.01)
balk("regel", (STIJLEN_V[0], yh, REGEL_Z), (STIJLEN_V[1], yh, REGEL_Z), 0.11, 0.12, M_BALK, ruw=0.008)
balk("regel", (STIJLEN_V[2], yh, REGEL_Z), (STIJLEN_V[3], yh, REGEL_Z), 0.11, 0.12, M_BALK, ruw=0.008)
balk("schoor", (STIJLEN_V[0] + 0.05, yh, WZ1 - 0.05), (STIJLEN_V[1] - 0.05, yh, REGEL_Z + 0.05), 0.16, 0.11, M_BALK,
     ruw=0.008)
balk("schoor", (STIJLEN_V[2] + 0.05, yh, REGEL_Z + 0.05), (STIJLEN_V[3] - 0.05, yh, WZ1 - 0.05), 0.16, 0.11, M_BALK,
     ruw=0.008)
# venster: kozijn, roeden, ruiten, bank
x0, x1, z0, z1 = VENSTER
box("ruit", ((x0 + x1) / 2, yv + 0.02, (z0 + z1) / 2), (x1 - x0, 0.02, z1 - z0), M_RUIT)
for x in (x0, (x0 + x1) / 2, x1):
    balk("kozijn", (x, yh, z0), (x, yh, z1), 0.08 if x not in (x0, x1) else 0.11, 0.1, M_BALK, ruw=0.004)
for z in (z0, (z0 + z1) / 2, z1):
    balk("kozijn", (x0, yh, z), (x1, yh, z), 0.07 if z not in (z0, z1) else 0.11, 0.1, M_BALK, ruw=0.004)
for xs in ((3 * x0 + x1) / 4, (x0 + 3 * x1) / 4):     # dunne roeden: 2 x 2 ruitjes per vak
    balk("roede", (xs, yh + 0.01, z0), (xs, yh + 0.01, z1), 0.025, 0.04, M_BALK, bevel=0.004)
# bloembak onder het venster met bloemen
bb_z = z0 - 0.22
box("bloembak", ((x0 + x1) / 2, UY0 - 0.2, bb_z), (x1 - x0 + 0.1, 0.26, 0.22), M_PLANK, bevel=0.01)
for s in (-1, 1):
    balk("bakdrager", ((x0 + x1) / 2 + s * 0.4, UY0 - 0.02, bb_z - 0.35), ((x0 + x1) / 2 + s * 0.4, UY0 - 0.3, bb_z - 0.1),
         0.06, 0.06, M_BALK)
box("bakaarde", ((x0 + x1) / 2, UY0 - 0.2, bb_z + 0.1), (x1 - x0, 0.2, 0.03), M_AARDE)
rb = random.Random(3)
for i in range(46):
    bx = x0 + 0.06 + (x1 - x0 - 0.12) * rb.random()
    by = UY0 - 0.2 + rb.uniform(-0.08, 0.08)
    hh = rb.uniform(0.08, 0.2)
    top = (bx + rb.uniform(-0.04, 0.04), by + rb.uniform(-0.06, 0.02), bb_z + 0.1 + hh)
    balk("steel", (bx, by, bb_z + 0.1), top, 0.008, 0.008, M_BLAD, bevel=0.0)
    if i % 3 == 0:
        bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=1, radius=0.035, location=(bx, by - 0.02, bb_z + 0.1 + hh * 0.5))
        o = bpy.context.object
        o.scale = (1.4, 0.6, 0.35)
        o.rotation_euler = (rb.uniform(-0.5, 0.5), 0, rb.uniform(0, 3))
        put(o, M_BLAD)
    bpy.ops.mesh.primitive_uv_sphere_add(segments=8, ring_count=4, radius=rb.uniform(0.028, 0.045), location=top)
    o = bpy.context.object
    o.scale = (1, 1, 0.45)
    put(o, BLOEM[i % len(BLOEM)])

# linkergevel (x = UX0): pleister met het gat voor de hoorn, stijlen, de gevelpunt eronder dak
xg = UX0 + 0.05
xh = UX0 - 0.01


def gevel_hoogte(y):
    return U_Z1 + (min(y - UY0, UY1 - y)) * math.tan(DAK_HOEK)


GAT = (AY0 + 0.03, AY1 - 0.03, AAMBEELD_Z0 + 0.03, AAMBEELD_Z1 - 0.03)      # y0, y1, z0, z1
for (x_, xh_) in ((xg, xh), (UX1 - 0.05, UX1 + 0.01)):
    pleister_vak_x(UY0 + 0.05, GAT[0], WZ0, WZ1, x_)
    pleister_vak_x(GAT[1], UY1 - 0.05, WZ0, WZ1, x_)
    pleister_vak_x(GAT[0], GAT[1], WZ0, GAT[2], x_)
    # gevelpunt: driehoek boven de muurplaat, ook boven het aambeeld
    vs, fs = [], []
    n = 12
    for i in range(n + 1):
        y = UY0 + (UY1 - UY0) * i / n
        vs += [(x_ - 0.06, y, WZ1 if not (GAT[0] < y < GAT[1]) else GAT[3]), (x_ - 0.06, y, gevel_hoogte(y) - 0.03)]
    for i in range(n):
        fs.append([2 * i, 2 * i + 2, 2 * i + 3, 2 * i + 1])
    g = mesh_obj("gevelpunt", vs, fs, M_PLEISTER, smooth=False)
    s = g.modifiers.new("dik", "SOLIDIFY")
    s.thickness = 0.12
    for y in (UY0 + 0.08, UY1 - 0.08):
        balk("hoekstijl", (xh_, y, WZ0 - 0.02), (xh_, y, WZ1 + 0.02), 0.12, 0.17, M_BALK, ruw=0.008)
    balk("gevelstijl", (xh_, YC, GAT[3] + 0.02), (xh_, YC, NOK_Z - 0.1), 0.12, 0.15, M_BALK, ruw=0.008)
    balk("gevelregel", (xh_, UY0 + 0.1, U_Z1 - 0.06), (xh_, GAT[0], U_Z1 - 0.06), 0.12, 0.14, M_BALK, ruw=0.008)
    balk("gevelregel", (xh_, GAT[1], U_Z1 - 0.06), (xh_, UY1 - 0.1, U_Z1 - 0.06), 0.12, 0.14, M_BALK, ruw=0.008)
    balk("gevelschoor", (xh_, UY0 + 0.12, U_Z1 - 0.02), (xh_, YC - 0.1, NOK_Z - 0.35), 0.11, 0.12, M_BALK, ruw=0.008)
    balk("gevelschoor", (xh_, UY1 - 0.12, U_Z1 - 0.02), (xh_, YC + 0.1, NOK_Z - 0.35), 0.11, 0.12, M_BALK, ruw=0.008)
# achtergevel: alleen pleister (niet te zien vanuit de camera, wel in het spel bij draaien)
pleister_vak(UX0 + 0.05, UX1 - 0.05, WZ0, WZ1, UY1 - 0.05)

# hoekstenen (kwartierstenen) op de twee voorhoeken van de verdieping
for (cx, sx) in ((UX0, 1), (UX1, -1)):
    z = WZ0
    k = 0
    while z < U_Z1 - 0.12:
        h = random.uniform(0.17, 0.22)
        lang = 0.42 if k % 2 == 0 else 0.26
        # langs de voorgevel en om de hoek langs de zijgevel, om en om lang en kort
        stone((cx + sx * lang / 2 - sx * 0.06, UY0 - 0.02, z + h / 2), (lang, 0.2, h * 0.94), 0.0, M_KWARTIER,
              tilt=(random.uniform(-0.03, 0.03), random.uniform(-0.03, 0.03)))
        stone((cx - sx * 0.03, UY0 + (0.26 if k % 2 else 0.42) / 2 - 0.06, z + h / 2),
              ((0.26 if k % 2 else 0.42), 0.24, h * 0.94), math.pi / 2, M_KWARTIER)
        z += h + 0.012
        k += 1

# --- Aambeeld: hoorn uit de linkergevel, lijf binnen, hiel uit de rechter -------------------------


def hoorn_mesh(n_u=28, n_v=32):
    """Hoorn als verlopende doorsnede: platte bovenkant op het werkvlak die licht zakt naar de punt,
    de onderkant die in een boog naar de punt oploopt. u = 0 bij de gevel, 1 in de punt."""
    vs, fs = [], []
    x_a = UX0 + 0.25                                   # begint in de muur
    for j in range(n_u + 1):
        u = j / n_u
        x = x_a + (HOORN_TIP - x_a) * u
        top = AAMBEELD_Z1 - 0.18 * u ** 1.5
        bot = AAMBEELD_Z0 + (AAMBEELD_Z1 - 0.4 - AAMBEELD_Z0) * (1 - (1 - u) ** 1.35)
        hw = (AY1 - AY0) / 2 * (1 - u ** 3.0) ** 0.42          # dik tot ver naar voren, ronde punt
        hh = max((top - bot) / 2, 0.0)
        zc = (top + bot) / 2
        if j == n_u:
            hw = hh = 0.0
        for i in range(n_v):
            a = 2 * math.pi * i / n_v
            c, s = math.cos(a), math.sin(a)
            p = 4.0 if s > 0 else 2.2                       # boven vlakker (werkvlak), onder rond
            ry = hw * math.copysign(abs(c) ** (2 / p), c)
            rz = hh * math.copysign(abs(s) ** (2 / p), s)
            vs.append((x, YC + ry, zc + rz))
    for j in range(n_u):
        for i in range(n_v):
            a, b = j * n_v + i, j * n_v + (i + 1) % n_v
            fs.append([a, a + n_v, b + n_v, b])
    return mesh_obj("hoorn", vs, fs, M_IJZER)


hoorn = hoorn_mesh()
sub = hoorn.modifiers.new("glad", "SUBSURF")
sub.levels = 1
sub.render_levels = 2
# lijf (binnen, verborgen) en hiel: afgeronde blokken
box("lijf", ((UX0 + UX1) / 2, YC, (AAMBEELD_Z0 + AAMBEELD_Z1) / 2 - 0.05),
    (UX1 - UX0 - 0.1, AY1 - AY0 - 0.05, AAMBEELD_Z1 - AAMBEELD_Z0 - 0.1), M_IJZER)
def hiel_mesh(name, sub=5, p=8.0):
    """Hiel als afgerond blok (superellips), boven vlak, de zijden licht bol, onder iets taps en
    wat gehamerde oneffenheid."""
    hx, hy, hz = (HIEL_X1 - UX1 + 0.3) / 2, (AY1 - AY0 + 0.36) / 2, (AAMBEELD_Z1 - HIEL_Z0) / 2
    bm = bmesh.new()
    bmesh.ops.create_icosphere(bm, subdivisions=sub, radius=1.0)
    for v in bm.verts:
        d = v.co.normalized()
        pz = 9.0 if d.z > 0 else p                       # bovenkant bijna vlak (werkvlak)
        k = (abs(d.x) ** p + abs(d.y) ** p + abs(d.z) ** pz) ** (1 / p)
        c = d / k
        t = (c.x + 1) / 2                                # 0 bij de gevel, 1 aan het eind
        bol = 1 + 0.05 * (1 - c.z * c.z)
        taps = 1 - 0.1 * t * max(0.0, -c.z)
        v.co = Vector((c.x * hx, c.y * hy * bol * taps, c.z * hz))
        v.co += d * 0.008 * noise.noise(c * 6.0)
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    me.shade_smooth()
    ob = bpy.data.objects.new(name, me)
    col.objects.link(ob)
    ob.location = ((UX1 - 0.3 + HIEL_X1) / 2, YC, (HIEL_Z0 + AAMBEELD_Z1) / 2)
    return put(ob, M_IJZER)


hiel = hiel_mesh("hiel")
# hardy-gat en prikgat bovenop de hiel
box("hardygat", (HIEL_X1 - 0.45, YC + 0.15, AAMBEELD_Z1 - 0.02), (0.16, 0.16, 0.06), mat_flat("gat", (0.005, 0.005, 0.005), 0.9, "ijzer"))
cyl("prikgat", (HIEL_X1 - 0.8, YC + 0.3, AAMBEELD_Z1 - 0.02), 0.045, 0.06, bpy.data.materials["gat"], verts=12)
# stalen werkvlak: een dunne plaat bovenop, buiten de gevels, met een rand
box("werkvlak", ((UX1 + HIEL_X1) / 2 - 0.08, YC, AAMBEELD_Z1 + 0.01), (HIEL_X1 - UX1 - 0.25, AY1 - AY0 - 0.05, 0.03),
    M_IJZER, bevel=0.012)

# --- Dak: dakbeschot, pannen, nokvorsten, windveren --------------------------------------------------
X_D0, X_D1 = UX0 - VERGE_L, UX1 + VERGE_R
Y_E0, Y_E1 = UY0 - OVERSTEK, UY1 + OVERSTEK
Z_EAVE = U_Z1 - OVERSTEK * math.tan(DAK_HOEK)


def dak_z(y):
    return U_Z1 + (min(y - UY0, UY1 - y)) * math.tan(DAK_HOEK)


for kant in (-1, 1):                                  # dakbeschot (onderkant donker hout)
    y_e = Y_E0 if kant < 0 else Y_E1
    vs = [(X_D0, y_e, dak_z(y_e)), (X_D1, y_e, dak_z(y_e)), (X_D1, YC, NOK_Z), (X_D0, YC, NOK_Z)]
    b = mesh_obj("beschot", vs, [[0, 1, 2, 3]], M_DAKBORD, smooth=False)
    s = b.modifiers.new("dik", "SOLIDIFY")
    s.thickness = 0.05
    s.offset = -1 if kant < 0 else 1


def pan_mesh(name, w=0.24, l=0.34, t=0.026, seed=0):
    """Leipan: recht plaatje, iets scheef en golvend, met een afgebrokkelde hoek hier en daar."""
    rnd = random.Random(seed)
    bm = bmesh.new()
    bmesh.ops.create_grid(bm, x_segments=5, y_segments=4, size=0.5)
    for v in bm.verts:
        x, y = v.co.x, v.co.y                      # -0,5 .. 0,5
        v.co.x = x * w
        v.co.y = y * l
        v.co.z = 0.003 * math.cos(math.pi * x) + rnd.uniform(-0.0025, 0.0025) - 0.006 * (y + 0.5)
        if y < -0.4 and x * (1 if seed % 2 else -1) > 0.4 and seed % 3 == 0:     # afgebroken hoekje
            v.co.y += 0.035
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    o = bpy.data.objects.new("_p", me)
    col.objects.link(o)
    s = o.modifiers.new("dik", "SOLIDIFY")
    s.thickness = t
    bv = o.modifiers.new("b", "BEVEL")
    bv.width, bv.segments = 0.004, 1
    dg = bpy.context.evaluated_depsgraph_get()
    me2 = bpy.data.meshes.new_from_object(o.evaluated_get(dg), depsgraph=dg)
    me2.name = name
    bpy.data.objects.remove(o)
    for p in me2.polygons:
        p.use_smooth = True
    me2.materials.append(M_PAN)
    return me2


PANNEN = [pan_mesh(f"pan{k}", w=0.24 * (0.92 + 0.03 * (k % 4)), seed=k) for k in range(8)]
PAN_W, PAN_L, PAN_STAP = 0.24, 0.34, 0.19
n_pannen = 0
for kant in (-1, 1):
    y_e = Y_E0 if kant < 0 else Y_E1
    helling = Vector((0, -kant * math.cos(DAK_HOEK), math.sin(DAK_HOEK)))     # van goot naar nok
    L = math.hypot(YC - y_e, NOK_Z - dak_z(y_e))
    rij = 0
    s = 0.0
    while s < L - 0.12:
        nx = int((X_D1 - X_D0) / PAN_W) + 1
        off = (rij % 2) * PAN_W / 2
        for i in range(nx + 1):
            x = X_D0 + off + i * PAN_W - PAN_W / 2 + random.uniform(-0.01, 0.01)
            if x < X_D0 + 0.02 or x > X_D1 - 0.02:
                continue
            base = Vector((x, y_e, dak_z(y_e) + 0.05)) + helling * (s + PAN_L / 2) + Vector((0, 0, 0.02))
            o = bpy.data.objects.new("pan", random.choice(PANNEN))
            col.objects.link(o)
            # lokaal: x langs het dak, y de helling op, z naar buiten; onderrand iets opgetild
            nrm = Vector((0, kant * math.sin(DAK_HOEK), math.cos(DAK_HOEK)))
            yy = helling
            xx = yy.cross(nrm).normalized()                 # rechtshandig, ook op de achterkant
            M = Matrix((xx, yy, nrm)).transposed().to_4x4()
            tilt = Matrix.Rotation(random.uniform(-0.1, -0.04), 4, "X") @ Matrix.Rotation(random.uniform(-0.03, 0.03), 4, "Z")
            o.matrix_world = Matrix.Translation(base) @ M @ tilt
            n_pannen += 1
        s += PAN_STAP
        rij += 1
# nokvorsten: halve buizen over de nok
for i in range(int((X_D1 - X_D0) / 0.36) + 1):
    x = X_D0 + 0.18 + i * 0.36
    if x > X_D1:
        break
    bpy.ops.mesh.primitive_cylinder_add(vertices=14, radius=0.13, depth=0.38, location=(x, YC, NOK_Z + 0.06),
                                        rotation=(0, math.pi / 2, 0))
    o = bpy.context.object
    o.name = "nokvorst"
    bm = bmesh.new()
    bm.from_mesh(o.data)
    bmesh.ops.delete(bm, geom=[f for f in bm.faces if f.calc_center_median().x > 0.02], context="FACES")
    bm.to_mesh(o.data)
    bm.free()
    s_ = o.modifiers.new("dik", "SOLIDIFY")
    s_.thickness = 0.02
    o.rotation_euler.x += random.uniform(-0.03, 0.03)
    o.scale = (1, 1, 1)
    put(o, M_PAN)
# windveren langs de gevels
for x in (X_D0 + 0.02, X_D1 - 0.02):
    for kant in (-1, 1):
        y_e = Y_E0 if kant < 0 else Y_E1
        balk("windveer", (x, y_e, dak_z(y_e) + 0.02), (x, YC, NOK_Z + 0.02), 0.05, 0.2, M_DAKBORD, ruw=0.005)

# --- Gras en onkruid aan de voet ----------------------------------------------------------------------
for k, (gx, gy) in enumerate(((-0.25, 0.4), (-0.2, 1.3), (0.4, -0.2), (2.45, -0.15), (2.6, 0.5), (0.95, -0.12),
                              (2.0, -0.16), (-0.3, -0.2))):
    gras_pol((gx, gy, 0.0), M_GRAS, n=60, h=0.28, r=0.18, seed=k)

# --- LOD1-proxies -----------------------------------------------------------------------------------------
lod1(box("l1_grond", ((GX0 + GX1) / 2, (GY0 + GY1) / 2, G_H / 2), (GX1 - GX0 + 0.1, GY1 - GY0 + 0.1, G_H), M_STEEN))
lod1(box("l1_verdieping", ((UX0 + UX1) / 2, (UY0 + UY1) / 2, (G_H + U_Z1) / 2), (UX1 - UX0, UY1 - UY0, U_Z1 - G_H),
         M_PLEISTER))
vs = [(X_D0, Y_E0, Z_EAVE), (X_D1, Y_E0, Z_EAVE), (X_D1, YC, NOK_Z + 0.08), (X_D0, YC, NOK_Z + 0.08),
      (X_D0, Y_E1, Z_EAVE), (X_D1, Y_E1, Z_EAVE)]
lod1(mesh_obj("l1_dak", vs, [[0, 1, 2, 3], [3, 2, 5, 4], [0, 3, 4], [1, 5, 2]], M_PAN, smooth=False))
vs = [(UX0, UY0 + 0.05, U_Z1), (UX0, UY1 - 0.05, U_Z1), (UX0, YC, NOK_Z)]
lod1(mesh_obj("l1_gevel", vs + [(UX1, UY0 + 0.05, U_Z1), (UX1, UY1 - 0.05, U_Z1), (UX1, YC, NOK_Z)],
              [[0, 2, 1], [3, 4, 5]], M_PLEISTER, smooth=False))
lod1(hiel_mesh("l1_hiel", sub=2))                 # zelfde ronde vorm, grof (een doos bakt zwart in de hoeken)
h1 = hoorn_mesh(10, 10)
h1.name = "l1_hoorn"
lod1(h1)
for (px, py) in ((GX0, GY0), (GX1, GY0), (GX0, GY1)):
    lod1(box("l1_stijl", (px, py, G_H / 2), (0.28, 0.28, G_H), M_BALK))
lod1(box("l1_balk", (3.3, (UY1 - 0.3 + BALK_Y) / 2, Z0 - 0.04), (0.17, UY1 - 0.3 - BALK_Y, 0.17), M_BALK))
lod1(box("l1_bloembak", ((x0 + x1) / 2, UY0 - 0.2, bb_z + 0.05), (x1 - x0 + 0.1, 0.26, 0.3), M_PLANK))

# --- Ankers ---------------------------------------------------------------------------------------------------
anker("deur_drempel", (DEUR_X, GY0 - 0.55, 0.0))          # looppunt voor de deur
anker("werkplek", (-1.6, -0.9, 0.0))                       # onder de hoorn: hier hamert de bouwer

# --- Alles naar het midden schuiven (spel-oorsprong) --------------------------------------------------------
for o in list(scene.objects):
    if o.parent is None:
        o.location.x -= OX
        o.location.y -= OY
if "deur" in OPTS:
    zet_deur("deur", float(OPTS["deur"]))
print("PANNEN", n_pannen)
afronden(NAAM, (-OX, -OY, 0.0), REF_PX, W_PX, H_PX)
