"""Voetvolkgilde (footman's guild) uit Beasts & Bumpkins nagebouwd in 3D.

Ronde stenen toren met een overkragende borstwering en kantelen; bovenop een dakterras van paars-lila
tegels (dambord) met een trapgat en een RECHTE houten trap naar beneden (besluit gebruiker 2026-10-30:
geen wenteltrap). Aan de voet een portaal met een rondboogdeur (-X), een rond stenen hutje met een rieten
koepel (-Y), twee kleine uitbouwen met rieten kapjes op halve hoogte (links en rechts van de camera), een bank
met een beker, twee paars-wit gevierendeelde schilden en een banier aan de muur. Maten teruggerekend uit
fguild.png (118x129, 87,5 px per meter op 4x) en het goedgekeurde concept (voetsoldatengilde.jpg, v3).

Assen: toren-as op de oorsprong; -X is linksvoor in beeld (deur), -Y rechtsvoor (hutje), de camera kijkt
van (-X, -Y). Draaien (headless):
  blender -b -P voetvolkgilde.py -- [schaal=4] [snel] [geen_glb] [geen_render] [deur=graden]
Schrijft voetvolkgilde.blend en .glb naast dit script en preview/voetvolkgilde_render.png.
Game-glb daarna: blender -b -P loods_molen_rt.py -- naam=voetvolkgilde res=1024 vergelijk
"""
import math
import os
import random
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from loods_molen_lib import *  # noqa: E402,F401,F403
from mathutils import Matrix, Vector  # noqa: E402

NAAM = "voetvolkgilde"
SPRITE = SC + "bb_original/fguild.png"
W_PX, H_PX = 472, 516                  # 4x-sprite (118 x 129)
REF_PX = (264, 432)                    # voet van de toren-as in de sprite (4x)

# --- Maten (meters) ----------------------------------------------------------------------------
R = 1.76                               # schacht (buitenkant van de stenen)
Z_TERRAS = 3.55                        # vloer van het dakterras (sprite: midden paars op ~3,7 m)
R_KRAAG = R + 0.16                     # overkragende borstwering
Z_KRAAG = 3.15                         # begin van de kraag
Z_BORST = 3.9                          # bovenkant borstwering
Z_KANTEEL = 4.38                       # bovenkant kantelen (sprite: ~4,35 m achteraan)
GAT_C = Vector((0.42, 0.1))            # trapgat (midden, xy): sprite rechts van het midden
GAT_R = 0.78
DEUR_B, DEUR_H = 0.86, 1.62            # rondboogdeur in het portaal (-X)
P_X0, P_X1, P_Y = -2.12, -1.35, 0.78   # portaal: voorvlak, tot in de toren, halve breedte
P_H0, P_H1 = 2.2, 2.55                 # portaal: hoogte voor, tegen de toren
HUT_C = Vector((0.08, -2.04))          # rond hutje met rieten koepel (-Y)
HUT_R, HUT_H = 0.56, 1.62              # sprite: koepelrand op ~1,65 m, koepel 0,63 m straal
UITBOUW = [(math.radians(156), 2.2), (math.radians(-50), 2.25)]     # (richting, hoogte kap): links, rechts in beeld

# --- Materialen --------------------------------------------------------------------------------
M_STEEN = mat_steen("steen", lo=(0.17, 0.17, 0.155), hi=(0.68, 0.66, 0.6), moss=0.4, lichen=0.45)
M_KANT = mat_steen("kantsteen", lo=(0.15, 0.15, 0.135), hi=(0.72, 0.7, 0.64), moss=0.3, lichen=0.4)
M_SPECIE = mat_specie("specie", (0.22, 0.21, 0.19), (0.4, 0.38, 0.34))
# de ronde muren (schacht, borstwering, hutje, uitbouwen) bakken op een eigen atlas ("muur"): hun stenen zijn alleen
# bron voor een gladde schil (schil(), rt = laag), anders krijgen die schillen een postzegel tussen duizend steeneilandjes
M_MUUR = mat_steen("muursteen", lo=(0.17, 0.17, 0.155), hi=(0.68, 0.66, 0.6), moss=0.4, lichen=0.45)
M_MUUR["groep"] = "muur"
M_MUURSPECIE = mat_specie("muurspecie", (0.22, 0.21, 0.19), (0.4, 0.38, 0.34))
M_MUURSPECIE["groep"] = "muur"
M_DONKER = mat_flat("donker", (0.012, 0.01, 0.008), 0.95)
M_PLANK = mat_hout("plank", "weathered_brown_planks", (0.12, 0.07, 0.035), (0.48, 0.32, 0.17), 0.5, 5.0,
                   rot=math.pi / 2)
M_TREDE = mat_hout("trede", "weathered_brown_planks", (0.14, 0.08, 0.04), (0.55, 0.37, 0.2), 0.6, 4.0)
M_BALK = mat_hout("balk", "rough_wood", (0.10, 0.06, 0.03), (0.42, 0.29, 0.17), rand=5.0, grijs=0.4)
M_BESLAG = mat_flat("beslag", (0.02, 0.02, 0.02), 0.45, "ijzer")
M_ZILVER = mat_flat("zilver", (0.62, 0.62, 0.6), 0.3, "ijzer")
M_ZILVER.node_tree.nodes["Principled BSDF"].inputs["Metallic"].default_value = 1.0
M_GRAS = mat_gras("gras")
M_HALM = mat_halm("halm", [(0.0, (0.3, 0.11, 0.01)), (0.3, (0.7, 0.36, 0.04)), (0.55, (0.9, 0.55, 0.1)),
                           (0.8, (0.97, 0.68, 0.22)), (1.0, (1.0, 0.8, 0.4))], verweerd=0.3)
M_RIET = mat_rietlaag("riet")
M_TOUW = mat_hout("touw", "rough_wood", (0.2, 0.13, 0.05), (0.45, 0.33, 0.15), 6.0, 2.0)
M_TOUW["groep"] = "dak"


def mat_tegels(name, a=(0.36, 0.12, 0.5), b_=(0.15, 0.035, 0.25), maat=0.42):
    """Dambord van paars-lila tegels (wereld-assen, in iso lezen ze als ruiten) met voegen en vuil."""
    m, nt, b = principled(name, 0.75, "rest")
    tc = nt.nodes.new("ShaderNodeTexCoord")
    mp = nt.nodes.new("ShaderNodeMapping")
    mp.inputs["Scale"].default_value = (1 / maat, 1 / maat, 1 / maat)
    nt.links.new(tc.outputs["Object"], mp.inputs["Vector"])
    ch = nt.nodes.new("ShaderNodeTexChecker")
    ch.inputs["Scale"].default_value = 1.0
    ch.inputs["Color1"].default_value = (*a, 1)
    ch.inputs["Color2"].default_value = (*b_, 1)
    nt.links.new(mp.outputs[0], ch.inputs["Vector"])
    br = nt.nodes.new("ShaderNodeTexBrick")
    br.offset = 0.0
    br.squash = 1.0
    br.inputs["Scale"].default_value = 1.0
    br.inputs["Brick Width"].default_value = 1.0
    br.inputs["Row Height"].default_value = 1.0
    br.inputs["Mortar Size"].default_value = 0.035
    br.inputs["Mortar Smooth"].default_value = 0.3
    nt.links.new(mp.outputs[0], br.inputs["Vector"])
    voeg = br.outputs["Fac"]
    n = noise_tex(nt, tc.outputs["Object"], 4.0, 6.0)
    c = mix_rgb(nt, math_node(nt, "MULTIPLY", math_node(nt, "MAXIMUM", math_node(nt, "SUBTRACT", n, 0.45), 0.0), 1.1),
                ch.outputs["Color"], (0.16, 0.13, 0.1))
    fijn = noise_tex(nt, tc.outputs["Object"], 25.0, 8.0)
    c = mix_rgb(nt, math_node(nt, "MULTIPLY", fijn, 0.25), c, (0.02, 0.01, 0.03))
    c = mix_rgb(nt, voeg, c, (0.12, 0.11, 0.1))
    nt.links.new(c, b.inputs["Base Color"])
    bump_from(nt, b, math_node(nt, "ADD", math_node(nt, "MULTIPLY", voeg, -1.0), math_node(nt, "MULTIPLY", fijn, 0.3)),
              0.5, 0.01)
    return m


def mat_kwartier(name, paars=(0.22, 0.02, 0.32), wit=(0.78, 0.76, 0.72), groep="doek"):
    """Gevierendeeld paars-wit (schild, banier): kwadranten op Object X en Z rond de oorsprong."""
    m, nt, b = principled(name, 0.6, groep)
    tc = nt.nodes.new("ShaderNodeTexCoord")
    sg = nt.nodes.new("ShaderNodeSeparateXYZ")
    nt.links.new(tc.outputs["Object"], sg.inputs[0])
    gx = math_node(nt, "GREATER_THAN", sg.outputs["X"], 0.0)
    gz = math_node(nt, "GREATER_THAN", sg.outputs["Z"], 0.0)
    k = math_node(nt, "ABSOLUTE", math_node(nt, "SUBTRACT", gx, gz))
    c = mix_rgb(nt, k, paars, wit)
    vuil = noise_tex(nt, tc.outputs["Object"], 6.0, 6.0)
    c = mix_rgb(nt, math_node(nt, "MULTIPLY", math_node(nt, "MAXIMUM", math_node(nt, "SUBTRACT", vuil, 0.5), 0.0), 1.0),
                c, (0.25, 0.2, 0.14))
    nt.links.new(c, b.inputs["Base Color"])
    bump_from(nt, b, vuil, 0.15, 0.005)
    return m


M_TEGEL = mat_tegels("tegel")
M_SCHILD = mat_kwartier("schild")
M_BANIER = mat_kwartier("banier")
stenen_maken(M_STEEN, n=16, p=12.0, bumps=0.04, hf=0.03, cuts=4, sub=3)   # gekapte blokken (concept), geen kussens


# --- Hulpjes ------------------------------------------------------------------------------------
def ronde_muur(cx, cy, r, z0, z1, depth=0.22, hs=(0.17, 0.23), ls=(0.3, 0.46), mat=None, uit=0.006,
               boog=None, vrij=None, rt=None):
    """Stenen in lagen rond (cx, cy) met buitenstraal r. boog = (a0, a1): alleen dat stuk van de cirkel.
    vrij(a, z) -> False laat een steen weg. rt="bron": de steen is alleen bakbron voor een schil (schil())."""
    z = z0
    a_lo, a_hi = boog if boog else (0.0, 2 * math.pi)
    while z < z1 - 0.04:
        h = min(random.uniform(*hs), z1 - z)
        s = -random.uniform(0, 0.2)                # booglengte langs de omtrek
        Lt = (a_hi - a_lo) * (r - depth / 2)
        while s < Lt:
            L = random.uniform(*ls)
            sm = min(max(s + L / 2, 0.0), Lt)
            a = a_lo + sm / (r - depth / 2)
            if vrij is None or vrij(a, z + h / 2):
                rr = r - depth / 2 + random.uniform(-uit, uit)
                o = stone((cx + rr * math.cos(a), cy + rr * math.sin(a), z + h / 2),
                          (L * random.uniform(0.92, 1.0), depth, h * random.uniform(0.9, 0.97)), a + math.pi / 2, mat,
                          tilt=(random.uniform(-0.015, 0.015), random.uniform(-0.02, 0.02)))
                if rt:
                    o["rt"] = rt
            s += L + 0.01
        z += h + 0.008


def schil(name, cx, cy, r, z0, z1, mat, n=48, rijen=4):
    """Open cilinder (buitenkant van een ronde stenen muur) als laag model voor de rt-bake: loods_molen_rt.py
    bakt de stenen met rt="bron" erop en laat ze zelf weg (rt="laag": niet in de render, niet in de bronnen)."""
    vs, fs = [], []
    for j in range(rijen + 1):
        z = z0 + (z1 - z0) * j / rijen
        for i in range(n):
            a = 2 * math.pi * i / n
            vs.append((cx + r * math.cos(a), cy + r * math.sin(a), z))
    for j in range(rijen):
        for i in range(n):
            k, k2 = j * n + i, j * n + (i + 1) % n
            fs.append([k, k2, k2 + n, k + n])
    o = mesh_obj(name, vs, fs, mat)
    o["rt"] = "laag"
    o.hide_render = True
    return o


def wand_schil(name, p0, p1, z0, z1, off, mat, gat=None, rt="laag"):
    """Vlakke muur van p0 naar p1 (xy), off m naar binnen vanaf die lijn (normaal naar buiten zoals flat_wall), met
    optioneel een rondboogopening gat = (t_midden, breedte, hoogte) langs de muur. rt = laag: bakschil (zie schil());
    rt = bron: specie in de voegen erachter."""
    d = Vector((p1[0] - p0[0], p1[1] - p0[1], 0))
    Lt = d.length
    d.normalize()
    n = Vector((d.y, -d.x, 0))
    P = lambda t, z: (p0[0] + d.x * t - n.x * off, p0[1] + d.y * t - n.y * off, z)
    vs, fs = [], []

    def quad(a, b, c, e):
        k = len(vs)
        vs.extend([P(*a), P(*b), P(*c), P(*e)])
        fs.append([k, k + 1, k + 2, k + 3])
    if gat is None:
        quad((0, z0), (Lt, z0), (Lt, z1), (0, z1))
    else:
        tm, w, h = gat
        quad((0, z0), (tm - w / 2, z0), (tm - w / 2, z1), (0, z1))
        quad((tm + w / 2, z0), (Lt, z0), (Lt, z1), (tm + w / 2, z1))
        ol = [(tm + y, z) for (y, z) in arch_outline(w, h, z0, n=12)]
        for (ta, za), (tb, zb) in zip(ol, ol[1:]):
            if tb - ta > 1e-4:
                quad((ta, za), (tb, zb), (tb, z1), (ta, z1))
    o = mesh_obj(name, vs, fs, mat, smooth=False)
    bm_ = bmesh.new()
    bm_.from_mesh(o.data)
    bmesh.ops.remove_doubles(bm_, verts=bm_.verts, dist=1e-4)
    bm_.to_mesh(o.data)
    bm_.free()
    o["rt"] = rt
    o.hide_render = rt == "laag"
    return o


def schijf_ring(name, r_uit, r_in, c_in, z0, z1, mat, n=64):
    """Dichte schijf (r_uit om de oorsprong) met een rond gat (r_in om c_in), van z0 tot z1."""
    vs, fs = [], []
    for i in range(n):
        a = 2 * math.pi * i / n
        o = (r_uit * math.cos(a), r_uit * math.sin(a))
        g = (c_in.x + r_in * math.cos(a), c_in.y + r_in * math.sin(a))
        vs += [(o[0], o[1], z0), (o[0], o[1], z1), (g[0], g[1], z1), (g[0], g[1], z0)]
    for i in range(n):
        j = (i + 1) % n
        a, b = 4 * i, 4 * j
        fs += [[a, b, b + 1, a + 1], [a + 1, b + 1, b + 2, a + 2], [a + 2, b + 2, b + 3, a + 3], [a + 3, b + 3, b, a]]
    return mesh_obj(name, vs, fs, mat, smooth=False)


def koepel(name, cx, cy, z0, r, h, mat, n=40, m=14, dik=0.07):
    """Rieten koepel: halve bol (ellipsoide), rand iets uitlopend over de muur."""
    vs, fs = [(cx, cy, z0 + h)], []
    for j in range(1, m + 1):
        t = j / m * (math.pi / 2)
        for i in range(n):
            a = 2 * math.pi * i / n
            rr = r * math.sin(t)
            vs.append((cx + rr * math.cos(a), cy + rr * math.sin(a), z0 + h * math.cos(t)))
    for i in range(n):
        fs.append([0, 1 + i, 1 + (i + 1) % n])
    for j in range(m - 1):
        for i in range(n):
            a, b = 1 + j * n + i, 1 + j * n + (i + 1) % n
            fs.append([a, a + n, b + n, b])
    o = mesh_obj(name, vs, fs, mat)
    s = o.modifiers.new("dik", "SOLIDIFY")
    s.thickness = dik
    s.offset = -1.0
    return o


rnd = random.Random(11)
halm_c, halm_b = [], []
PER_BOS = 10 if not SNEL else 4


def koepel_halmen(cx, cy, z0, r, h, banden=(0.45, 0.78)):
    """Halmen van de top naar de rand over de koepel, in lagen (zoals gelegd riet), punten iets afhangend,
    en touwbanden rond de koepel."""
    def punt(a, t, lift):
        rr = (r + lift) * math.sin(t)
        return Vector((cx + rr * math.cos(a), cy + rr * math.sin(a), z0 + (h + lift) * math.cos(t)))
    lagen = 3
    for laag in range(lagen):
        t_top = (laag / lagen) * (math.pi / 2) * 0.85
        t_end = min(math.pi / 2 * (0.62 + 0.42 * (laag + 1) / lagen), math.pi / 2 * 1.06)
        omtrek = 2 * math.pi * r * math.sin(max(t_end, 0.3))
        nb = int(omtrek / (0.05 if not SNEL else 0.1))
        for k in range(nb):
            a0 = 2 * math.pi * (k + rnd.random() * 0.5) / nb
            bos = rnd.random()
            lift0 = rnd.uniform(0.0, 0.02) + 0.012 * laag
            for _ in range(PER_BOS):
                a = a0 + rnd.gauss(0, 0.02)
                tt = t_top + rnd.uniform(-0.05, 0.05)
                te = t_end + rnd.uniform(-0.05, 0.08)
                pts = []
                for q in range(8):
                    u = q / 7
                    t = tt + (te - tt) * u
                    pts.append(punt(a + rnd.gauss(0, 0.004) * u, min(t, math.pi / 2), lift0 + 0.04 * u ** 0.8))
                if te > math.pi / 2 * 0.98:                       # onderste laag: punten hangen iets over de rand
                    d7 = (pts[-1] - pts[-2]).normalized()
                    pts.append(pts[-1] + d7 * 0.03 + Vector((0, 0, -0.04 * rnd.random())))
                else:
                    pts.append(pts[-1] + (pts[-1] - pts[-2]) * 0.02)
                halm_c.append([tuple(p) for p in pts])
                halm_b.append(bos)
    for tb in banden:                                    # touwbanden
        t = math.pi / 2 * tb
        z = z0 + (h + 0.07) * math.cos(t)
        rr = (r + 0.07) * math.sin(t)
        bpy.ops.mesh.primitive_torus_add(major_radius=rr, minor_radius=0.014, major_segments=48, minor_segments=6,
                                         location=(cx, cy, z))
        put(bpy.context.object, M_TOUW)
        bpy.context.object.name = "touw"


# --- Toren: kern, stenen schacht, kraag, borstwering, kantelen ----------------------------------------
# kern net achter de stenen: specie in de voegen (render en bake; de bakstralen reiken 0,1 m diep)
cyl("kern", (0, 0, 1.0), R - 0.065, 2.0, M_MUURSPECIE, verts=64)
schijf_ring("kern_boven", R - 0.065, GAT_R + 0.06, GAT_C, 2.0, Z_TERRAS - 0.03, M_MUURSPECIE)
ronde_muur(0, 0, R, 0.0, Z_KRAAG, mat=M_MUUR, rt="bron")
schil("schacht_schil", 0, 0, R - 0.008, 0.0, Z_KRAAG, M_MUUR, n=64, rijen=6)
# kraag: een laag uitkragende consolestenen, dan de borstwering op de grotere straal
ronde_muur(0, 0, R + 0.07, Z_KRAAG, Z_KRAAG + 0.17, depth=0.3, hs=(0.15, 0.17), ls=(0.2, 0.3), mat=M_KANT)
ronde_muur(0, 0, R_KRAAG, Z_KRAAG + 0.17, Z_BORST, depth=0.24, mat=M_MUUR, rt="bron")
schil("borst_schil", 0, 0, R_KRAAG - 0.008, Z_KRAAG + 0.17, Z_BORST - 0.02, M_MUUR, n=64, rijen=2)
schijf_ring("kern_kraag", R + 0.02, GAT_R + 0.06, GAT_C, Z_KRAAG - 0.02, Z_KRAAG + 0.17, M_SPECIE)
schijf_ring("kern_borst", R_KRAAG - 0.065, GAT_R + 0.06, GAT_C, Z_KRAAG + 0.17, Z_TERRAS - 0.03, M_MUURSPECIE)
# kantelen: zeven merlons rondom, niet allemaal even breed (zoals het concept)
KANTELEN = [(0.15, 0.55), (0.95, 1.35), (1.8, 2.15), (2.62, 3.05), (3.55, 3.95), (4.45, 4.85), (5.35, 5.75)]
for a0, a1 in KANTELEN:
    ronde_muur(0, 0, R_KRAAG, Z_BORST, Z_KANTEEL, depth=0.24, hs=(0.19, 0.24), ls=(0.3, 0.42), mat=M_KANT,
               boog=(a0, a1))
    am = (a0 + a1) / 2                               # kern, zodat er tussen de blokken geen lucht is
    box("kanteel_kern", ((R_KRAAG - 0.12) * math.cos(am), (R_KRAAG - 0.12) * math.sin(am), (Z_BORST + Z_KANTEEL) / 2 - 0.03),
        ((a1 - a0) * (R_KRAAG - 0.12) - 0.08, 0.16, Z_KANTEEL - Z_BORST - 0.06), M_SPECIE, rot_z=am + math.pi / 2)
# afdekstenen op de borstwering tussen de kantelen (vlak, iets breder)
for i in range(64):
    a = 2 * math.pi * (i + 0.5) / 64
    if any(a0 - 0.02 < a < a1 + 0.02 for a0, a1 in KANTELEN):
        continue
    rr = R_KRAAG - 0.12
    stone((rr * math.cos(a), rr * math.sin(a), Z_BORST + 0.04), (0.2, 0.28, 0.09), a + math.pi / 2, M_KANT)
# binnenkant borstwering: gladde specie-ring, zodat je vanaf het terras geen gaten ziet
bpy.ops.mesh.primitive_cylinder_add(vertices=64, radius=R_KRAAG - 0.08, depth=Z_BORST - Z_TERRAS + 0.05,
                                    location=(0, 0, (Z_BORST + Z_TERRAS - 0.05) / 2))
bi = bpy.context.object
bi.name = "borst_binnen"
bm_ = bmesh.new()
bm_.from_mesh(bi.data)
bmesh.ops.delete(bm_, geom=[f for f in bm_.faces if abs(f.normal.z) > 0.5], context="FACES")
bm_.to_mesh(bi.data)
bm_.free()
s_ = bi.modifiers.new("dik", "SOLIDIFY")
s_.thickness = 0.185                                 # binnenvlak op R_KRAAG - 0,265 (voegen van de binnenstenen)
put(bi, M_SPECIE)
schil("borst_voeg", 0, 0, R_KRAAG - 0.065, Z_TERRAS - 0.05, Z_BORST, M_MUURSPECIE, n=64, rijen=1)   # voegen buiten
bpy.data.objects["borst_voeg"]["rt"] = "bron"
bpy.data.objects["borst_voeg"].hide_render = False
# binnenkant van de borstwering ook stenen (concept), van het terras tot de afdekking
ronde_muur(0, 0, R_KRAAG - 0.12, Z_TERRAS - 0.02, Z_BORST, depth=0.17, hs=(0.15, 0.2), ls=(0.28, 0.42), mat=M_STEEN)

# --- Dakterras: tegels met een trapgat, rechte trap ----------------------------------------------------
schijf_ring("terras", R_KRAAG - 0.2, GAT_R, GAT_C, Z_TERRAS - 0.05, Z_TERRAS, M_TEGEL)
# rand van het trapgat: een ring van smalle stenen
for i in range(22):
    a = 2 * math.pi * i / 22
    stone((GAT_C.x + (GAT_R + 0.06) * math.cos(a), GAT_C.y + (GAT_R + 0.06) * math.sin(a), Z_TERRAS + 0.005),
          (0.2, 0.13, 0.05), a + math.pi / 2, M_KANT)
# schacht onder het gat (donker), met een vloer op de verdieping
bpy.ops.mesh.primitive_cylinder_add(vertices=40, radius=GAT_R + 0.02, depth=Z_TERRAS - 1.9,
                                    location=(GAT_C.x, GAT_C.y, (Z_TERRAS + 1.9) / 2 - 0.02))
sch = bpy.context.object
sch.name = "schacht"
bm_ = bmesh.new()
bm_.from_mesh(sch.data)
bmesh.ops.delete(bm_, geom=[f for f in bm_.faces if f.normal.z > 0.5], context="FACES")
bmesh.ops.reverse_faces(bm_, faces=bm_.faces[:])
bm_.to_mesh(sch.data)
bm_.free()
put(sch, M_DONKER)
# rechte trap: van de rand van het gat aan de schermlinkerkant (-X+Y) recht naar beneden naar +X-Y,
# treden tussen twee bomen (trapbomen); de bovenste trede ligt op het terras
T_DIR = Vector((math.cos(math.radians(-45)), math.sin(math.radians(-45)), 0))
T_DWARS = Vector((-T_DIR.y, T_DIR.x, 0))
T_START = Vector((GAT_C.x, GAT_C.y, 0)) - T_DIR * (GAT_R - 0.04)
T_B = 0.58
for k in range(7):
    p = T_START + T_DIR * (0.07 + 0.2 * k) + Vector((0, 0, Z_TERRAS - 0.03 - 0.22 * k))
    box("trede", tuple(p), (0.26, T_B, 0.05), M_TREDE, rot_z=math.atan2(T_DIR.y, T_DIR.x), bevel=0.008)
for s in (-1, 1):
    a = T_START + T_DWARS * s * (T_B / 2 + 0.03) + Vector((0, 0, Z_TERRAS - 0.02))
    b = a + T_DIR * 1.45 + Vector((0, 0, -1.6))
    balk("trapboom", tuple(a), tuple(b), 0.06, 0.16, M_BALK, ruw=0.006)

# --- Portaal met rondboogdeur (-X) -------------------------------------------------------------------------
box("portaal_kern", ((P_X0 + 0.3 + P_X1) / 2, 0, P_H0 / 2), (P_X1 - P_X0 - 0.3, 2 * P_Y - 0.25, P_H0), M_SPECIE)
ZC = DEUR_H - DEUR_B / 2
t_d0, t_d1 = P_Y - DEUR_B / 2 - 0.05, P_Y + DEUR_B / 2 + 0.05
LAGEN = dict(depth=0.22, uit=0.01, hs=(0.13, 0.2), ls=(0.22, 0.4))
n_st = len(stones_out)
flat_wall((P_X0 + 0.11, P_Y), (P_X0 + 0.11, -P_Y), 0.0, P_H0,
          [(t_d0, t_d1, -1, DEUR_H + 0.3), (t_d0 - 0.3, t_d1 + 0.3, -1, ZC + 0.05)], mat=M_MUUR, **LAGEN)
GAT = (P_Y, DEUR_B + 0.08, DEUR_H + 0.08)            # binnenrand van de boog (de boogstenen blijven echt)
wand_schil("portaal_schil", (P_X0 + 0.11, P_Y), (P_X0 + 0.11, -P_Y), 0.0, P_H0, -0.11 + 0.008, M_MUUR, GAT)
wand_schil("portaal_voeg", (P_X0 + 0.11, P_Y), (P_X0 + 0.11, -P_Y), 0.0, P_H0, -0.11 + 0.065, M_MUURSPECIE, GAT, "bron")
for s in (-1, 1):                                    # zijmuren van het portaal, tot in de toren
    y = s * (P_Y - 0.11)
    a_, b_ = ((P_X1, y), (P_X0 + 0.02, y)) if s > 0 else ((P_X0 + 0.02, y), (P_X1, y))
    flat_wall(a_, b_, 0.0, P_H0, [], mat=M_MUUR, **LAGEN)
    a_, b_ = ((P_X1, y), (P_X0 - 0.0, y)) if s > 0 else ((P_X0 - 0.0, y), (P_X1, y))
    wand_schil("portaal_schil", a_, b_, 0.0, P_H0 - 0.02, -0.11 + 0.008, M_MUUR)
    wand_schil("portaal_voeg", a_, b_, 0.0, P_H0, -0.11 + 0.065, M_MUURSPECIE, rt="bron")
for o in stones_out[n_st:]:                          # de muurstenen van het portaal: alleen bakbron
    o["rt"] = "bron"
boog_stenen(P_X0 + 0.11, 0.0, math.pi, 0.0, DEUR_B + 0.08, DEUR_H + 0.08, dikte=0.22, diep=0.28, mat=M_KANT)
box("deurgat", (P_X0 + 0.24, 0.0, DEUR_H / 2), (0.05, DEUR_B + 0.06, DEUR_H), M_DONKER)
# afdekking: platte stenen schuin van de voorkant (P_H0) omhoog tegen de toren (P_H1)
helling = math.atan2(P_H1 - P_H0, P_X1 - P_X0)
box("portaal_dak", ((P_X0 + P_X1) / 2 + 0.05, 0, (P_H0 + P_H1) / 2 - 0.04),
    (P_X1 - P_X0 + 0.1, 2 * P_Y, 0.12), M_SPECIE, rot=(0, -helling, 0))
x = P_X0 - 0.05
while x < P_X1 - 0.05:
    L = random.uniform(0.28, 0.4)
    y = -P_Y - 0.04
    while y < P_Y + 0.04:
        w = random.uniform(0.3, 0.5)
        xm = x + L / 2
        z = P_H0 + (xm - P_X0) / (P_X1 - P_X0) * (P_H1 - P_H0) + 0.05
        o = stone((xm, min(y + w / 2, P_Y), z), (L, min(w, P_Y + 0.06 - y), 0.11), math.pi / 2 + random.uniform(-0.05, 0.05),
                  M_KANT, tilt=(random.uniform(-0.04, 0.04), -helling + random.uniform(-0.05, 0.05)))
        y += w + 0.01
    x += L + 0.01
delen = plank_door("deurplank", P_X0 + 0.16, 0.0, 0.0, DEUR_B, DEUR_H, math.pi, M_PLANK, M_BESLAG, n=5)
scharnier("deur", delen, P_X0 + 0.16, 0.0, DEUR_B, math.pi)
stone((P_X0 - 0.3, 0.0, 0.0), (0.5, 1.0, 0.12), 0.05, M_KANT)          # drempelsteen

# --- Rond hutje met rieten koepel (-Y) -----------------------------------------------------------------------
cyl("hut_kern", (HUT_C.x, HUT_C.y, HUT_H / 2), HUT_R - 0.06, HUT_H, M_MUURSPECIE, verts=40)
ronde_muur(HUT_C.x, HUT_C.y, HUT_R, 0.0, HUT_H, depth=0.2, hs=(0.13, 0.2), ls=(0.2, 0.34), mat=M_MUUR,
           vrij=lambda a, z: math.hypot(HUT_C.x + HUT_R * math.cos(a), HUT_C.y + HUT_R * math.sin(a)) > R - 0.05,
           rt="bron")
schil("hut_schil", HUT_C.x, HUT_C.y, HUT_R - 0.008, 0.0, HUT_H - 0.1, M_MUUR, n=40, rijen=3)
# een donker kijkgat in het hutje (concept: spleet naast de bank)
box("hutgat", (HUT_C.x - 0.5, HUT_C.y - 0.3, 0.95), (0.05, 0.12, 0.34), M_DONKER, rot_z=math.radians(-60))
koepel("hut_riet", HUT_C.x, HUT_C.y, HUT_H - 0.12, HUT_R + 0.08, 0.55, M_RIET)
koepel_halmen(HUT_C.x, HUT_C.y, HUT_H - 0.12, HUT_R + 0.08, 0.55)

# --- Twee uitbouwen met rieten kapjes op halve hoogte ---------------------------------------------------------
for i, (a, zk) in enumerate(UITBOUW):
    c = Vector((math.cos(a), math.sin(a))) * (R - 0.02)
    ru = 0.45
    cyl("uitbouw_kern", (c.x, c.y, zk / 2), ru - 0.06, zk, M_MUURSPECIE, verts=32)
    ronde_muur(c.x, c.y, ru, 0.0, zk, depth=0.18, hs=(0.13, 0.19), ls=(0.18, 0.3), mat=M_MUUR,
               vrij=lambda b, z, c=c, ru=ru: math.hypot(c.x + ru * math.cos(b), c.y + ru * math.sin(b)) > R - 0.06,
               rt="bron")
    schil("uitbouw_schil", c.x, c.y, ru - 0.008, 0.0, zk - 0.1, M_MUUR, n=32, rijen=3)
    koepel("kap_riet", c.x, c.y, zk - 0.1, ru + 0.12, 0.62, M_RIET, n=28, m=10, dik=0.06)
    koepel_halmen(c.x, c.y, zk - 0.1, ru + 0.12, 0.62, banden=(0.6,))

riet = strands("dakhalmen", halm_c, M_HALM, halm_b, lambda u: 0.0058 - 0.0018 * u)

# --- Banier en speer aan de muur (links in beeld, boven de linker uitbouw) -------------------------------------
a_b = math.radians(200)                              # sprite: tussen de linker uitbouw en het midden
voet = Vector((math.cos(a_b) * (R - 0.05), math.sin(a_b) * (R - 0.05), 2.3))
uit = Vector((math.cos(a_b), math.sin(a_b), 0))
langs = Vector((-uit.y, uit.x, 0))
top = voet + uit * 0.55 + Vector((0, 0, 0.75))
balk("banierstok", tuple(voet), tuple(top), 0.035, 0.035, M_BALK, bevel=0.005)
balk("dwarslat", tuple(top - langs * 0.25 + Vector((0, 0, -0.04))), tuple(top + langs * 0.25 + Vector((0, 0, -0.04))),
     0.025, 0.025, M_BALK, bevel=0.004)
bw_, bh_ = 0.46, 0.62
vs = []
fs = []
nn = 8
for j in range(nn + 1):                              # doek met een lichte golf, onderrand in een punt
    for i in range(5):
        u = i / 4 - 0.5
        v = j / nn
        zz = -v * bh_ - (0.12 * (1 - abs(u) * 2) if j == nn else 0.0)
        vs.append((u * bw_, 0.015 * math.sin(v * 5 + u * 3), zz))
for j in range(nn):
    for i in range(4):
        k = j * 5 + i
        fs.append([k, k + 1, k + 6, k + 5])
ban = mesh_obj("banier", [(x_, y_, z_ + bh_ / 2) for (x_, y_, z_) in vs], fs, M_BANIER)
s_ = ban.modifiers.new("dik", "SOLIDIFY")
s_.thickness = 0.01
ban.rotation_euler = (0, 0, math.atan2(langs.y, langs.x))
ban.location = top + Vector((0, 0, -0.06 - bh_ / 2)) + uit * 0.03
# speer schuin erachter
sp0 = voet + langs * 0.35 + Vector((0, 0, -0.5))
sp1 = sp0 + uit * 0.45 + langs * -0.4 + Vector((0, 0, 1.25))
balk("speer", tuple(sp0), tuple(sp1), 0.028, 0.028, M_BALK, bevel=0.004)
bpy.ops.mesh.primitive_cone_add(vertices=4, radius1=0.04, depth=0.18, location=tuple(sp1 + (sp1 - sp0).normalized() * 0.08))
pk = bpy.context.object
pk.name = "speerpunt"
pk.rotation_mode = "QUATERNION"
pk.rotation_quaternion = (sp1 - sp0).to_track_quat("Z", "Y")
put(pk, M_BESLAG)

# --- Bank, beker, schilden, losse steen ---------------------------------------------------------------------------
a_bank = math.radians(-128)
bc = Vector((math.cos(a_bank), math.sin(a_bank), 0)) * (R + 0.24)
bt = Vector((-math.sin(a_bank), math.cos(a_bank), 0))
rb = math.atan2(bt.y, bt.x)
box("bankblad", (bc.x, bc.y, 0.53), (1.15, 0.34, 0.06), M_PLANK, rot_z=rb, bevel=0.01)
for s in (-1, 1):
    for d in (-1, 1):
        p = bc + bt * s * 0.45 + Vector((math.cos(a_bank), math.sin(a_bank), 0)) * d * 0.11
        balk("bankpoot", (p.x, p.y, 0.0), (p.x + bt.x * s * 0.04, p.y + bt.y * s * 0.04, 0.51), 0.06, 0.06, M_BALK)
    p = bc + bt * s * 0.45
    balk("bankregel", (p.x - 0.11 * math.cos(a_bank), p.y - 0.11 * math.sin(a_bank), 0.18),
         (p.x + 0.11 * math.cos(a_bank), p.y + 0.11 * math.sin(a_bank), 0.18), 0.04, 0.05, M_BALK)
# beker op de bank
gp = bc - bt * 0.3
vs, fs = [], []
prof = [(0.0, 0.0), (0.04, 0.0), (0.04, 0.008), (0.008, 0.02), (0.008, 0.07), (0.03, 0.085), (0.042, 0.13),
        (0.038, 0.135), (0.026, 0.09), (0.0, 0.085)]
nn = 16
for (r_, z_) in prof:
    for i in range(nn):
        a = 2 * math.pi * i / nn
        vs.append((gp.x + r_ * math.cos(a), gp.y + r_ * math.sin(a), 0.56 + z_))
for j in range(len(prof) - 1):
    for i in range(nn):
        k = j * nn + i
        fs.append([k, j * nn + (i + 1) % nn, (j + 1) * nn + (i + 1) % nn, (j + 1) * nn + i])
mesh_obj("beker", vs, fs, M_ZILVER)


def schild(name, loc, rot_z, kantel, w=0.5, h=0.62):
    """Heraldisch schild (recht boven, rond toelopend naar een punt), licht bol, met een rand."""
    vs, fs = [], []
    nu, nv = 8, 10
    for j in range(nv + 1):
        v = j / nv                                     # 0 boven, 1 punt
        hw = w / 2 * (1.0 if v < 0.45 else math.cos((v - 0.45) / 0.55 * math.pi / 2) ** 0.7)
        for i in range(nu + 1):
            u = (i / nu - 0.5) * 2
            x = u * max(hw, 0.004)
            vs.append((x, -0.05 * (1 - u * u), h / 2 - v * h))
    for j in range(nv):
        for i in range(nu):
            k = j * (nu + 1) + i
            fs.append([k, k + nu + 1, k + nu + 2, k + 1])
    o = mesh_obj(name, vs, fs, M_SCHILD)
    s = o.modifiers.new("dik", "SOLIDIFY")
    s.thickness = 0.025
    o.location = loc
    o.rotation_euler = (kantel, 0, rot_z)
    return o


# tegen de linkerflank van het hutje (sprite: onderkant op ~(-0,5, -2,0))
schild("schild", (HUT_C.x - 0.66, HUT_C.y + 0.12, 0.26), math.radians(-60), math.radians(-14), w=0.42, h=0.52)
schild("schild", (HUT_C.x - 0.5, HUT_C.y - 0.28, 0.25), math.radians(-35), math.radians(-12), w=0.4, h=0.5)
stone((bc.x - 0.5, bc.y - 0.55, 0.07), (0.32, 0.18, 0.14), 0.4, M_KANT)        # losse bouwsteen voor de bank

# --- Gras aan de voet -----------------------------------------------------------------------------------------------
for k in range(12):
    a = 2 * math.pi * k / 12 + 0.2
    gras_pol(((R + 0.08) * math.cos(a), (R + 0.08) * math.sin(a), 0.0), M_GRAS, n=40, h=0.22, r=0.14, seed=k)

# --- LOD1-proxies -----------------------------------------------------------------------------------------------------
l1 = cyl("l1_toren", (0, 0, Z_KRAAG / 2), R, Z_KRAAG, M_STEEN, verts=16)
lod1(l1)
l1b = cyl("l1_borst", (0, 0, (Z_KRAAG + Z_BORST) / 2), R_KRAAG, Z_BORST - Z_KRAAG, M_STEEN, verts=16)
bm_ = bmesh.new()                                    # open buis: een dichte deksel bakt het terras zwart
bm_.from_mesh(l1b.data)
bmesh.ops.delete(bm_, geom=[f for f in bm_.faces if abs(f.normal.z) > 0.5], context="FACES")
bm_.to_mesh(l1b.data)
bm_.free()
s_ = l1b.modifiers.new("dik", "SOLIDIFY")
s_.thickness = 0.22
lod1(l1b)
lod1(schijf_ring("l1_terras", R_KRAAG - 0.2, GAT_R, GAT_C, Z_TERRAS - 0.05, Z_TERRAS + 0.005, M_TEGEL, n=16))
for a0, a1 in KANTELEN:
    am = (a0 + a1) / 2
    lod1(box("l1_kanteel", (R_KRAAG * 0.92 * math.cos(am), R_KRAAG * 0.92 * math.sin(am), (Z_BORST + Z_KANTEEL) / 2),
             ((a1 - a0) * R_KRAAG, 0.3, Z_KANTEEL - Z_BORST), M_STEEN, rot_z=am + math.pi / 2))
lod1(box("l1_portaal", ((P_X0 + P_X1) / 2, 0, P_H0 / 2), (P_X1 - P_X0, 2 * P_Y, P_H0), M_STEEN))
lod1(cyl("l1_hut", (HUT_C.x, HUT_C.y, HUT_H / 2), HUT_R, HUT_H, M_STEEN, verts=12))
for nm, (cx_, cy_, z0_, r_, h_) in (("l1_hutriet", (HUT_C.x, HUT_C.y, HUT_H - 0.12, HUT_R + 0.08, 0.55)),):
    lod1(koepel(nm, cx_, cy_, z0_, r_, h_, M_RIET, n=12, m=4))
for a, zk in UITBOUW:
    c = Vector((math.cos(a), math.sin(a))) * (R - 0.02)
    lod1(koepel("l1_kap", c.x, c.y, zk - 0.1, 0.57, 0.62, M_RIET, n=10, m=3))
lod1(box("l1_bank", (bc.x, bc.y, 0.28), (1.15, 0.34, 0.56), M_PLANK, rot_z=rb))

# de muurspecie (kernen achter de schillen) is alleen bakbron: in de game zit de schil ervoor
for o in bpy.data.objects:
    if o.type == "MESH" and o.material_slots and o.material_slots[0].material is M_MUURSPECIE:
        o["rt"] = "bron"

# --- Ankers -------------------------------------------------------------------------------------------------------------
anker("deur_drempel", (P_X0 - 0.55, 0.0, 0.0))          # looppunt voor de deur
anker("oefenplek", (-2.6, -2.6, 0.0))                     # voor de bank: hier oefenen de soldaten
anker("wachtpost", (GAT_C.x - 0.9, GAT_C.y + 0.4, Z_TERRAS))  # op het dakterras ("terras" is al de tegelvloer)

if "deur" in OPTS:
    zet_deur("deur", float(OPTS["deur"]))
print("HALMEN", len(halm_c))
afronden(NAAM, (0.0, 0.0, 0.0), REF_PX, W_PX, H_PX)
