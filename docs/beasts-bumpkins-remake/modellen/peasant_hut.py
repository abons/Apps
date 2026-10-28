"""Peasant hut uit Beasts & Bumpkins (House.png, 217x147) nagebouwd in 3D.

Ronde stenen hut met houten stijlen, bol rieten dak met een opgebonden nok (paarse band),
stenen schoorsteen door het dak, een aanbouw met deur, een hekje met touw en wat stenen.
Maten en posities zijn teruggerekend uit de sprite (87,5 px per meter op 4x).

Draaien (headless):
  blender -b -P peasant_hut.py -- [schaal] [yaw] [pitch] [ortho]
Schrijft peasant_hut.glb, peasant_hut.blend en peasant_hut_render.png naast dit script.
"""
import math
import os
import random
import sys

import bpy
from mathutils import Vector

HERE = os.path.dirname(os.path.abspath(__file__))
argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
SCALE = int(argv[0]) if len(argv) > 0 else 4          # x de originele 217x147
YAW = float(argv[1]) if len(argv) > 1 else 225.0       # klassiek isometrisch: 45 graden
PITCH = float(argv[2]) if len(argv) > 2 else 30.0      # 2:1, zoals de sprite
ORTHO = float(argv[3]) if len(argv) > 3 else 9.92      # 87,5 px per meter op 4x

random.seed(7)
bpy.ops.wm.read_factory_settings(use_empty=True)
scene = bpy.context.scene
col = scene.collection

# --- Maten (meters) -----------------------------------------------------------
HX, HY = 0.65, -0.05   # middelpunt van de ronde hut
HUT_R = 1.7            # straal van de stenen wand
WALL_H = 1.85          # wand tot de dakrand


# --- Materialen ----------------------------------------------------------------
def principled(name, rough=0.85):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    b = m.node_tree.nodes["Principled BSDF"]
    b.inputs["Roughness"].default_value = rough
    return m, m.node_tree, b


def ramp_node(nt, stops):
    r = nt.nodes.new("ShaderNodeValToRGB")
    els = r.color_ramp.elements
    els[0].position, els[0].color = stops[0][0], (*stops[0][1], 1)
    els[1].position, els[1].color = stops[1][0], (*stops[1][1], 1)
    for pos, c in stops[2:]:
        e = els.new(pos)
        e.color = (*c, 1)
    return r


def math_node(nt, op, a=None, b=None):
    n = nt.nodes.new("ShaderNodeMath")
    n.operation = op
    for i, v in enumerate((a, b)):
        if v is None:
            continue
        if isinstance(v, (int, float)):
            n.inputs[i].default_value = v
        else:
            nt.links.new(v, n.inputs[i])
    return n.outputs[0]


def mat_thatch(name, grooves=9):
    """Riet: strengen die vanaf de nok naar de rand lopen. De noise krijgt (hoek, straal) als
    coordinaten, zodat de strepen radiaal liggen; een sinus op de hoek geeft de donkere groeven."""
    m, nt, b = principled(name, 0.9)
    tc = nt.nodes.new("ShaderNodeTexCoord")
    sep = nt.nodes.new("ShaderNodeSeparateXYZ")
    nt.links.new(tc.outputs["Object"], sep.inputs[0])
    ang = math_node(nt, "ARCTAN2", sep.outputs["Y"], sep.outputs["X"])
    rad = math_node(nt, "SQRT", math_node(nt, "ADD", math_node(nt, "MULTIPLY", sep.outputs["X"], sep.outputs["X"]),
                                         math_node(nt, "MULTIPLY", sep.outputs["Y"], sep.outputs["Y"])))
    comb = nt.nodes.new("ShaderNodeCombineXYZ")
    nt.links.new(math_node(nt, "MULTIPLY", ang, 90.0), comb.inputs["X"])
    nt.links.new(math_node(nt, "MULTIPLY", rad, 2.0), comb.inputs["Y"])
    nt.links.new(sep.outputs["Z"], comb.inputs["Z"])
    n = nt.nodes.new("ShaderNodeTexNoise")
    n.inputs["Scale"].default_value = 1.6
    n.inputs["Detail"].default_value = 10.0
    n.inputs["Roughness"].default_value = 0.6
    nt.links.new(comb.outputs[0], n.inputs["Vector"])
    # groeven: (1 + sin(hoek * grooves)) / 2, scherp gemaakt
    g = math_node(nt, "SINE", math_node(nt, "MULTIPLY", ang, float(grooves)))
    g = math_node(nt, "POWER", math_node(nt, "MULTIPLY", math_node(nt, "ADD", g, 1.0), 0.5), 6.0)
    fac = math_node(nt, "SUBTRACT", n.outputs["Fac"], math_node(nt, "MULTIPLY", g, 0.12))
    r = ramp_node(nt, [(0.28, (0.55, 0.11, 0.0)), (0.42, (0.85, 0.28, 0.0)), (0.55, (1.0, 0.48, 0.02)),
                       (0.68, (1.0, 0.68, 0.12)), (0.82, (1.0, 0.85, 0.35))])
    nt.links.new(fac, r.inputs["Fac"])
    nt.links.new(r.outputs["Color"], b.inputs["Base Color"])
    bump = nt.nodes.new("ShaderNodeBump")
    bump.inputs["Strength"].default_value = 0.8
    nt.links.new(fac, bump.inputs["Height"])
    nt.links.new(bump.outputs["Normal"], b.inputs["Normal"])
    return m


def mat_stone(name, scale=9.0, dark=(0.01, 0.01, 0.008), light=(0.45, 0.45, 0.32), flat=1.6, joint=0.14):
    """Veldsteen: kleine brokken met elk een eigen tint, brede zwarte voegen, sterke bump."""
    m, nt, b = principled(name, 0.9)
    tc = nt.nodes.new("ShaderNodeTexCoord")
    mp = nt.nodes.new("ShaderNodeMapping")
    mp.inputs["Scale"].default_value = (1.0, 1.0, flat)   # stenen liggen plat
    nt.links.new(tc.outputs["Object"], mp.inputs["Vector"])
    cell = nt.nodes.new("ShaderNodeTexVoronoi")
    cell.inputs["Scale"].default_value = scale
    edge = nt.nodes.new("ShaderNodeTexVoronoi")
    edge.feature = "DISTANCE_TO_EDGE"
    edge.inputs["Scale"].default_value = scale
    nt.links.new(mp.outputs["Vector"], cell.inputs["Vector"])
    nt.links.new(mp.outputs["Vector"], edge.inputs["Vector"])
    bw = nt.nodes.new("ShaderNodeRGBToBW")
    nt.links.new(cell.outputs["Color"], bw.inputs[0])
    tint = ramp_node(nt, [(0.0, dark), (1.0, light)])
    nt.links.new(bw.outputs[0], tint.inputs["Fac"])
    mortar = ramp_node(nt, [(0.04, (0.0, 0.0, 0.0)), (joint, (1.0, 1.0, 1.0))])
    nt.links.new(edge.outputs["Distance"], mortar.inputs["Fac"])
    mix = nt.nodes.new("ShaderNodeMix")
    mix.data_type = "RGBA"
    mix.blend_type = "MULTIPLY"
    mix.inputs["Factor"].default_value = 1.0
    nt.links.new(tint.outputs["Color"], mix.inputs["A"])
    nt.links.new(mortar.outputs["Color"], mix.inputs["B"])
    nt.links.new(mix.outputs["Result"], b.inputs["Base Color"])
    bump = nt.nodes.new("ShaderNodeBump")
    bump.inputs["Strength"].default_value = 1.5
    nt.links.new(edge.outputs["Distance"], bump.inputs["Height"])
    nt.links.new(bump.outputs["Normal"], b.inputs["Normal"])
    return m


def mat_rock(name):
    """Kei: gevlekt donkergrijs met lichte plekken, geen voegen."""
    m, nt, b = principled(name, 0.75)
    n = nt.nodes.new("ShaderNodeTexNoise")
    n.inputs["Scale"].default_value = 4.0
    n.inputs["Detail"].default_value = 8.0
    r = ramp_node(nt, [(0.42, (0.008, 0.008, 0.006)), (0.55, (0.07, 0.07, 0.06)), (0.66, (0.40, 0.39, 0.30))])
    nt.links.new(n.outputs["Fac"], r.inputs["Fac"])
    nt.links.new(r.outputs["Color"], b.inputs["Base Color"])
    bump = nt.nodes.new("ShaderNodeBump")
    bump.inputs["Strength"].default_value = 0.5
    nt.links.new(n.outputs["Fac"], bump.inputs["Height"])
    nt.links.new(bump.outputs["Normal"], b.inputs["Normal"])
    return m


def mat_wood(name, base, dark, grain=(1.0, 1.0, 8.0)):
    m, nt, b = principled(name, 0.8)
    tc = nt.nodes.new("ShaderNodeTexCoord")
    mp = nt.nodes.new("ShaderNodeMapping")
    mp.inputs["Scale"].default_value = grain
    n = nt.nodes.new("ShaderNodeTexNoise")
    n.inputs["Scale"].default_value = 3.0
    n.inputs["Detail"].default_value = 6.0
    r = ramp_node(nt, [(0.35, dark), (0.65, base)])
    nt.links.new(tc.outputs["Object"], mp.inputs["Vector"])
    nt.links.new(mp.outputs["Vector"], n.inputs["Vector"])
    nt.links.new(n.outputs["Fac"], r.inputs["Fac"])
    nt.links.new(r.outputs["Color"], b.inputs["Base Color"])
    return m


def mat_planks(name, base, dark, n=5.0):
    """Deur van planken: banden langs lokaal Y met donkere naden, plus wat nerf."""
    m, nt, b = principled(name, 0.8)
    tc = nt.nodes.new("ShaderNodeTexCoord")
    w = nt.nodes.new("ShaderNodeTexWave")
    w.bands_direction = "Y"
    w.inputs["Scale"].default_value = n
    w.inputs["Distortion"].default_value = 1.5
    w.inputs["Detail"].default_value = 3.0
    nt.links.new(tc.outputs["Object"], w.inputs["Vector"])
    r = ramp_node(nt, [(0.08, dark), (0.2, base), (0.8, base), (1.0, (base[0] * 1.3, base[1] * 1.3, base[2] * 1.3))])
    nt.links.new(w.outputs["Fac"], r.inputs["Fac"])
    nt.links.new(r.outputs["Color"], b.inputs["Base Color"])
    return m


def mat_flat(name, c, rough=0.8):
    m, nt, b = principled(name, rough)
    b.inputs["Base Color"].default_value = (*c, 1)
    return m


M_THATCH = mat_thatch("riet")
M_KNOT = mat_thatch("kuif", grooves=10)
M_STONE = mat_stone("steen", scale=5.0, light=(0.55, 0.52, 0.38), flat=2.4, joint=0.2)   # grove, platte brokken
M_CHIM = mat_stone("schoorsteensteen", scale=7.0, light=(0.32, 0.32, 0.24), joint=0.2)
M_ROCK = mat_rock("rots")
M_POST = mat_wood("stijl", (0.20, 0.07, 0.025), (0.08, 0.025, 0.01))        # verticale nerf (lokaal Z)
M_SHUTTER = mat_wood("luik", (0.10, 0.04, 0.01), (0.05, 0.018, 0.005), (1, 8, 1))
M_DOOR = mat_planks("deur", (0.16, 0.06, 0.02), (0.02, 0.008, 0.004))
M_STEP = mat_stone("stoep", scale=2.0, light=(0.6, 0.58, 0.48))
M_FRAME = mat_flat("kozijn", (0.16, 0.18, 0.22), 0.5)
M_DARK = mat_flat("donker", (0.015, 0.012, 0.01))
M_UNDER = mat_flat("onderkant", (0.25, 0.07, 0.0))
M_PURPLE = mat_flat("band", (0.07, 0.0, 0.10), 0.7)
M_ROPE = mat_flat("touw", (1.0, 0.35, 0.0), 0.7)
M_GRASS = mat_flat("gras", (0.03, 0.42, 0.03), 0.6)
M_POSTTOP = mat_flat("kopshout", (0.50, 0.42, 0.22))


def put(obj, mat, smooth=True):
    obj.data.materials.append(mat)
    if smooth:
        for p in obj.data.polygons:
            p.use_smooth = True
    return obj


def mesh_obj(name, verts, faces, mat, smooth=True, loc=(0, 0, 0)):
    me = bpy.data.meshes.new(name)
    me.from_pydata(verts, [], faces)
    me.update()
    ob = bpy.data.objects.new(name, me)
    ob.location = loc
    col.objects.link(ob)
    return put(ob, mat, smooth)


def lathe(name, profile, mat, seg=48, jitter=0.0, loc=(0, 0, 0), scallop=None, cap=True):
    """Omwentelingslichaam uit (r, z)-punten, van onder naar boven. Het object-origin ligt op de
    as, zodat de riettextuur (hoek, straal) rond het eigen midden rekent. `scallop` = (ringen, n, a):
    de onderste ringen golven met r *= 1 + a*cos(n*hoek)."""
    verts, faces = [], []
    for j, (r, z) in enumerate(profile):
        for i in range(seg):
            a = 2 * math.pi * i / seg
            rr = r
            if 0 < j < len(profile) - 1:
                rr *= 1 + jitter * (random.random() - 0.5)
            if scallop and j < scallop[0]:
                rr *= 1 + scallop[2] * math.cos(scallop[1] * a)
            verts.append((rr * math.cos(a), rr * math.sin(a), z))
    for j in range(len(profile) - 1):
        for i in range(seg):
            a, b = j * seg + i, j * seg + (i + 1) % seg
            faces.append([a, b, b + seg, a + seg])
    if cap:
        top = len(verts)
        verts.append((0, 0, profile[-1][1]))
        last = (len(profile) - 1) * seg
        for i in range(seg):
            faces.append([last + i, last + (i + 1) % seg, top])
    return mesh_obj(name, verts, faces, mat, loc=loc)


def box(name, loc, size, mat, rot_z=0.0, bevel=0.0):
    bpy.ops.mesh.primitive_cube_add(size=1, location=loc, rotation=(0, 0, rot_z))
    o = bpy.context.object
    o.name = name
    o.scale = size
    if bevel:
        m = o.modifiers.new("b", "BEVEL")
        m.width, m.segments = bevel, 2
    return put(o, mat, smooth=False)


def cyl(name, loc, r, depth, mat, rot=(0, 0, 0), verts=16):
    bpy.ops.mesh.primitive_cylinder_add(vertices=verts, radius=r, depth=depth, location=loc, rotation=rot)
    o = bpy.context.object
    o.name = name
    return put(o, mat)


def on_wall(deg, out=0.0):
    a = math.radians(deg)
    return HX + math.cos(a) * (HUT_R + out), HY + math.sin(a) * (HUT_R + out), a


def arched_frame(name, cx, cy, z0, w, h, rot_z, depth, mat):
    """Kozijn met een ronde bovenkant: rechthoek plus een halve cilinder erop."""
    box(name, (cx, cy, z0 + (h - w / 2) / 2), (depth, w, h - w / 2), mat, rot_z=rot_z)
    bpy.ops.mesh.primitive_cylinder_add(vertices=16, radius=w / 2, depth=depth,
                                        location=(cx, cy, z0 + h - w / 2), rotation=(0, math.pi / 2, rot_z))
    put(bpy.context.object, mat)


# --- Ronde hut -------------------------------------------------------------------
H = (HX, HY, 0)
lathe("wand", [(HUT_R + 0.05, 0.0), (HUT_R, 0.25), (HUT_R, WALL_H + 0.2)], M_STONE, seg=40, loc=H)

# vier stijlen, op de hoeken waar ze op de sprite staan
for deg in (148.0, 196.0, 260.0, 315.0):
    x, y, a = on_wall(deg, 0.04)
    box("stijl", (x, y, WALL_H / 2), (0.22, 0.20, WALL_H), M_POST, rot_z=a)

# voordeur (links-voor, tot op de grond) en een luik rechts-achter, elk met een rond grijsblauw kozijn
x, y, a = on_wall(172.0, 0.05)
arched_frame("deurkozijn", x, y, 0.0, 0.95, 1.7, a, 0.08, M_FRAME)
x2, y2, _ = on_wall(172.0, 0.10)
arched_frame("voordeur", x2, y2, 0.0, 0.8, 1.6, a, 0.05, M_DOOR)
for k, (out, dz) in enumerate(((0.32, 0.0), (0.62, -0.03))):                   # twee stoepstenen
    x3, y3, _ = on_wall(172.0 + (k - 0.5) * 6, out)
    box("stoep", (x3, y3, 0.04 + dz), (0.36, 0.62 - 0.1 * k, 0.1), M_STEP, rot_z=a + 0.1 * k, bevel=0.04)
x, y, a = on_wall(288.0, 0.05)
arched_frame("kozijn", x, y, 0.55, 0.72, 1.05, a, 0.08, M_FRAME)
x2, y2, _ = on_wall(288.0, 0.10)
arched_frame("luik", x2, y2, 0.62, 0.56, 0.90, a, 0.05, M_DOOR)
x3, y3, _ = on_wall(288.0, 0.14)
box("vensterbank", (x3, y3, 0.53), (0.2, 0.9, 0.08), M_POST, rot_z=a, bevel=0.02)

# bol rieten dak: een volle koepel (superellips) op een dikke, uitlopende, geschulpte rand die
# net boven de wand hangt, zodat de stenen wand met deur en luik eronder zichtbaar blijft
DOME_R, DOME_Z0, DOME_TOP, DOME_P = 2.36, 2.10, 3.55, 1.9   # gepast op de dakomtrek rechts


def dome_profile(n=14):
    """(r, z) van onder naar boven; r neemt vanaf de rand alleen af. Bovenin loopt het riet als
    een hals omhoog de band in."""
    pts = [(1.62, 2.02), (2.28, 1.85), (2.42, 1.93), (2.41, 2.03)]
    for k in range(1, n + 1):
        t = 0.06 + 0.94 * (k / n) ** 0.8
        r = DOME_R * (1 - t ** DOME_P) ** (1 / DOME_P)
        if r < 1.0:
            break
        pts.append((r, DOME_Z0 + (DOME_TOP - DOME_Z0) * t))
    return pts + [(0.85, 3.62), (0.70, 3.74), (0.60, 3.88)]


dak = lathe("dak", dome_profile(), M_THATCH, seg=96, jitter=0.015, loc=H, scallop=(3, 9, 0.03))
for v in dak.data.vertices:                                       # rafelige zoom: losse halmen hangen lager
    if v.co.z < 1.9:
        v.co.z -= 0.07 * random.random() ** 2
lathe("dakonder", [(1.6, 2.01), (2.27, 1.84)], M_UNDER, seg=72, loc=H, scallop=(2, 9, 0.03), cap=False)

# nok: paarse band en een platte, brede kuif met plooien naar het midden
nok = [lathe("band", [(0.61, 3.82), (0.61, 4.42)], M_PURPLE, seg=32, loc=H),
       lathe("kuifvoet", [(0.62, 4.40), (0.66, 4.46)], M_KNOT, seg=32, loc=H, cap=False)]
# kuif: een bos schoven die uit de band steekt, buitenste licht naar buiten gekanteld; van boven
# leest dat als de platte, geplooide kroon van de sprite
schoof = [(0.2, 0.0), (0.3, 0.16), (0.31, 0.3), (0.26, 0.37), (0.12, 0.4), (0.0, 0.41)]
for k in range(7):
    if k < 6:
        a = 2 * math.pi * k / 6 + 0.3
        ox, oy, tilt = 0.44 * math.cos(a), 0.44 * math.sin(a), 0.22
    else:
        a, ox, oy, tilt = 0.0, 0.0, 0.0, 0.0
    sh = lathe("schoof", schoof, M_KNOT, seg=14, jitter=0.1, loc=(HX + ox, HY + oy, 4.34 + (0.04 if k == 6 else 0.0)))
    sh.rotation_euler = (0.0, tilt, a)
    sh.rotation_mode = "ZYX"
    nok.append(sh)

# stenen schoorsteen: tonvorm met een ronde kap en een klein rookgat
CH = (1.02, -1.59, 0)
chim = [lathe("schoorsteen", [(0.36, 2.6), (0.44, 3.0), (0.48, 3.45), (0.46, 3.75), (0.43, 3.92),
                              (0.36, 3.95), (0.30, 3.9), (0.28, 3.6)], M_CHIM, seg=24, loc=CH, cap=False),
        lathe("rookgat", [(0.29, 3.62), (0.0, 3.62)], M_DARK, seg=16, loc=CH, cap=False)]

# --- Aanbouw achter-links (+Y), deur op de -X-kant ---------------------------------
AX0, AX1, AY0, AY1 = -0.4, 1.6, 0.95, 3.65
box("aanbouw", ((AX0 + AX1) / 2, (AY0 + AY1) / 2, WALL_H / 2), (AX1 - AX0, AY1 - AY0, WALL_H), M_STONE)
for (px, py) in ((AX0, AY1), (AX0, AY0 + 0.3), (AX1, AY1)):
    box("stijl", (px, py, WALL_H / 2), (0.22, 0.22, WALL_H), M_POST)
arched_frame("deurkozijn", AX0 - 0.03, 2.5, 0.0, 0.95, 1.65, 0.0, 0.08, M_FRAME)
arched_frame("deur", AX0 - 0.07, 2.5, 0.0, 0.75, 1.50, 0.0, 0.05, M_DOOR)
box("stoep", (AX0 - 0.3, 2.5, 0.04), (0.4, 0.7, 0.1), M_STEP, bevel=0.04)
# platte rieten deksel, flauw aflopend naar achter (+Y); de punt linksachter ligt het laagst.
# Een raster met een lichte bolling, dik gemaakt en afgerond. Het origin ligt ver naar voren,
# zodat de riethalmen (radiaal rond het origin) als evenwijdige strepen de helling af lopen.
LX0, LX1, LY0, LY1 = -0.6, 2.0, 0.6, 4.0


def lid_z(x, y):
    return 1.88 + 0.2 * (LY1 - y) + 0.04 * (x - LX0)


LO = (0.7, -3.0, 0.0)
nx, ny = 10, 12
vs, fs = [], []
for j in range(ny + 1):
    for i in range(nx + 1):
        u, v = i / nx, j / ny
        x, y = LX0 + (LX1 - LX0) * u, LY0 + (LY1 - LY0) * v
        vs.append((x - LO[0], y - LO[1], lid_z(x, y) + 0.12 * math.sin(math.pi * u) * math.sin(math.pi * v)))
for j in range(ny):
    for i in range(nx):
        k = j * (nx + 1) + i
        fs.append([k, k + 1, k + nx + 2, k + nx + 1])
r = mesh_obj("aanbouwdak", vs, fs, M_THATCH, loc=LO)
s = r.modifiers.new("dik", "SOLIDIFY")
s.thickness = 0.16
bv = r.modifiers.new("rond", "BEVEL")
bv.width, bv.segments = 0.07, 3

# --- Hekje met touw, rechtsvoor (vijf palen) ----------------------------------------
FRONT = [(-3.24, -2.82), (-1.06, -2.82), (1.25, -2.82)]
CORNER, BACK = (4.0, -2.6), (4.0, -0.25)
for (x, y) in FRONT + [CORNER, BACK]:
    cyl("paal", (x, y, 0.55), 0.14, 1.1, M_POST, verts=10)
    cyl("paalkop", (x, y, 1.105), 0.135, 0.02, M_POSTTOP, verts=10)


def rail(p, q, z, extra=0.15):
    d = Vector((q[0] - p[0], q[1] - p[1], 0))
    mid = ((p[0] + q[0]) / 2, (p[1] + q[1]) / 2, z)
    ang = math.atan2(d.y, d.x)
    cyl("regel", mid, 0.1, d.length + 2 * extra, M_POST, rot=(0, math.pi / 2, ang), verts=10)
    return ang


def lashing(x, y, z, ang):
    """Touw als een X om paal en regel: twee dunne ringen, gekanteld om de regel heen."""
    for tilt in (0.7, -0.7):
        bpy.ops.mesh.primitive_torus_add(major_radius=0.16, minor_radius=0.03, major_segments=20,
                                         minor_segments=6, location=(x, y, z),
                                         rotation=(tilt, 0, ang))
        put(bpy.context.object, M_ROPE)


ang_front = rail(FRONT[0], CORNER, 0.78)
for (x, y) in FRONT:
    lashing(x, y, 0.78, ang_front + math.pi / 2)
lashing(CORNER[0], CORNER[1], 0.78, ang_front + math.pi / 2)
ang_side = rail(BACK, (4.0, -3.3), 0.9, extra=0.0)          # steekt voorbij de hoekpaal uit
for (x, y) in (CORNER, BACK):
    lashing(x, y, 0.9, ang_side + math.pi / 2)

# --- Stenen links, graspollen -------------------------------------------------------
# ronde keien: een bol met een paar brede bulten (lage frequentie), plat aan de onderkant
for (x, y, sz) in ((-1.8, 3.25, 0.36), (-1.55, 2.4, 0.25), (-2.6, 2.65, 0.16), (-2.34, 3.57, 0.12),
                   (3.4, -1.0, 0.1), (2.6, -3.4, 0.09)):
    bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=3, radius=sz, location=(x, y, sz * 0.3))
    rk = bpy.context.object
    rk.scale = (1.25, 1.0, 0.75)
    ph = [random.uniform(0, 6.3) for _ in range(3)]
    for v in rk.data.vertices:
        d = v.co.normalized()
        v.co *= 1 + 0.12 * math.sin(3 * d.x + ph[0]) * math.cos(2.5 * d.y + ph[1]) + 0.07 * math.sin(4 * d.z + ph[2])
        v.co.z = max(v.co.z, -0.3 * sz)
    put(rk, M_ROCK, smooth=True)

RV = Vector((0.707, -0.707, 0))                              # schermrechts
FV = Vector((-0.707, -0.707, 0))                             # naar de camera
for (gx, gy) in ((-0.62, 3.52), (2.99, -1.37), (-0.85, -1.57)):
    # drie bladen uit een voet, als een waaier (V/W): buiten lang en uitbuigend, midden kort
    for lean, hgt, fwd in ((-0.42, 0.55, 0.05), (0.05, 0.32, 0.12), (0.45, 0.5, 0.0)):
        vs = []
        n = 5
        for k in range(n + 1):
            t = k / n
            w = 0.13 * math.sin(math.pi * min(1.0, t * 1.15)) + 0.012 * (1 - t)   # bladvorm, spitse punt
            c = Vector((gx, gy, 0)) + RV * (lean * t ** 1.6) + FV * (fwd * t) + Vector((0, 0, hgt * t))
            side = RV * w * 0.5 + Vector((0, 0, -w * 0.5 * (lean / 0.45)))       # breed in het schermvlak
            vs += [tuple(c - side), tuple(c + side)]
        fs = [[2 * k, 2 * k + 1, 2 * k + 3, 2 * k + 2] for k in range(n)]
        mesh_obj("gras", vs, fs, M_GRASS)

# --- glTF export (model zonder camera, licht en schaduwvanger) -----------------------
bpy.ops.export_scene.gltf(filepath=os.path.join(HERE, "peasant_hut.glb"), export_format="GLB",
                          export_apply=True)

# alleen de wanden werpen schaduw: op de sprite is die kort en ligt hij links van de hut
for ob in nok + chim + [dak]:
    ob.visible_shadow = False

# --- Schaduwvanger, camera en licht --------------------------------------------------
bpy.ops.mesh.primitive_plane_add(size=30, location=(0, 0, 0))
bpy.context.object.is_shadow_catcher = True

cam_d = bpy.data.cameras.new("cam")
cam_d.type = "ORTHO"
cam_d.ortho_scale = ORTHO
cam = bpy.data.objects.new("cam", cam_d)
col.objects.link(cam)
yaw, pitch = math.radians(YAW), math.radians(PITCH)
target = Vector((0.27, -0.27, 1.4))
dirv = Vector((math.cos(yaw) * math.cos(pitch), math.sin(yaw) * math.cos(pitch), math.sin(pitch)))
cam.location = target + dirv * 40
cam.rotation_euler = (target - cam.location).to_track_quat("-Z", "Y").to_euler()
scene.camera = cam

sun_d = bpy.data.lights.new("zon", "SUN")
sun_d.energy = 1.7
sun_d.angle = math.radians(2)
sun = bpy.data.objects.new("zon", sun_d)
col.objects.link(sun)
sun.rotation_euler = (math.radians(26), 0, math.radians(61))   # 64 graden hoog, van rechtsachter: schaduw links

fill_d = bpy.data.lights.new("vul", "SUN")                       # van linksvoor, zonder schaduw: de sprite
fill_d.energy = 2.9                                              # is links licht en rechts oranje
fill_d.use_shadow = False
fill = bpy.data.objects.new("vul", fill_d)
col.objects.link(fill)
fill.rotation_euler = (math.radians(55), 0, math.radians(-115))

world = bpy.data.worlds.new("w")
world.use_nodes = True
bg = world.node_tree.nodes["Background"]
bg.inputs["Color"].default_value = (0.75, 0.75, 0.8, 1)
bg.inputs["Strength"].default_value = 0.6            # weinig omgevingslicht: anders vangt de grond een brede grijze waas
scene.world = world

scene.render.engine = "CYCLES"
scene.cycles.samples = 64
scene.cycles.use_denoising = True
scene.render.film_transparent = True
scene.view_settings.view_transform = "Standard"
scene.render.resolution_x = 217 * SCALE
scene.render.resolution_y = 147 * SCALE
scene.render.filepath = os.path.join(HERE, "peasant_hut_render.png")
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(HERE, "peasant_hut.blend"))
bpy.ops.render.render(write_still=True)
print("KLAAR", scene.render.filepath)
