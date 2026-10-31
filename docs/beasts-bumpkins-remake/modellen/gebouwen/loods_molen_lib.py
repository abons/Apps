"""Gedeelde bouwstenen voor gereedschapsloods.py en molen.py (Cycles-bouw, zelfde stijl als
../peasant_hut.py): materialen op Poly Haven-texturen (CC0, ../textures/BRON.md), losse stenen,
planken, deuren met scharnier, ankers, de iso-camera en het licht van de hut.

Niet zelf draaien: de bouwscripts doen `from loods_molen_lib import *` als eerste regel.
"""
import math
import os
import random
import sys

import bmesh
import bpy
from mathutils import Matrix, Vector, noise

GB = os.path.dirname(os.path.abspath(__file__))
MODELLEN = os.path.dirname(GB)
TEX = os.path.join(MODELLEN, "textures")
PREVIEW = os.path.join(GB, "preview")
SC = ("C:/Users/Axel/AppData/Local/Temp/claude/E--werk-androidApps-Apps/"
      "16e99493-ac86-47c7-921f-1d215c266f51/scratchpad/")          # concept en sprites (niet in git)
PX_M = 87.5                     # pixels per meter op 4x (21,9 op 1x), zoals de hut
YAW, PITCH = 225.0, 30.0        # klassiek isometrisch

argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
OPTS = {a.split("=")[0]: (a.split("=", 1)[1] if "=" in a else "1") for a in argv}
SCALE = int(OPTS.get("schaal", 4))                                   # x de originele sprite
SNEL = "snel" in OPTS

random.seed(7)
bpy.ops.wm.read_factory_settings(use_empty=True)
scene = bpy.context.scene
col = scene.collection


# --- Node-hulpjes (uit peasant_hut.py) ------------------------------------------------
def principled(name, rough=0.85, groep="rest"):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    m["groep"] = groep                       # bakgroep voor de real-time atlas
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


def sock(node, name, kind):
    return [s for s in node.inputs if s.name == name and s.type == kind][0]


def mix_rgb(nt, fac, a, b, blend="MIX"):
    n = nt.nodes.new("ShaderNodeMix")
    n.data_type = "RGBA"
    n.blend_type = blend
    for s, v in ((n.inputs["Factor"], fac), (sock(n, "A", "RGBA"), a), (sock(n, "B", "RGBA"), b)):
        if isinstance(v, (int, float)):
            s.default_value = v
        elif isinstance(v, tuple):
            s.default_value = (*v, 1)
        else:
            nt.links.new(v, s)
    return [o for o in n.outputs if o.type == "RGBA"][0]


def image(nt, name, kind, vec, box=True):
    t = nt.nodes.new("ShaderNodeTexImage")
    t.image = bpy.data.images.load(os.path.join(TEX, f"{name}_{kind}_1k.jpg"), check_existing=True)
    if kind != "diff":
        t.image.colorspace_settings.name = "Non-Color"
    if box:
        t.projection = "BOX"
        t.projection_blend = 0.3
    nt.links.new(vec, t.inputs["Vector"])
    return t


def coords(nt, scale=1.0, kind="Object", rand_off=0.0):
    """Texcoord * schaal, per object verschoven met Object Info > Random."""
    tc = nt.nodes.new("ShaderNodeTexCoord")
    mp = nt.nodes.new("ShaderNodeMapping")
    mp.inputs["Scale"].default_value = (scale, scale, scale)
    nt.links.new(tc.outputs[kind], mp.inputs["Vector"])
    v = mp.outputs[0]
    if rand_off:
        oi = nt.nodes.new("ShaderNodeObjectInfo")
        cmb = nt.nodes.new("ShaderNodeCombineXYZ")
        for i in range(3):
            nt.links.new(math_node(nt, "MULTIPLY", oi.outputs["Random"], rand_off * (1 + 0.37 * i)), cmb.inputs[i])
        add2 = nt.nodes.new("ShaderNodeVectorMath")
        add2.operation = "ADD"
        nt.links.new(v, add2.inputs[0])
        nt.links.new(cmb.outputs[0], add2.inputs[1])
        v = add2.outputs[0]
    return v


def bump_from(nt, b, height, strength, dist=0.02):
    bump = nt.nodes.new("ShaderNodeBump")
    bump.inputs["Strength"].default_value = strength
    bump.inputs["Distance"].default_value = dist
    nt.links.new(height, bump.inputs["Height"])
    nt.links.new(bump.outputs["Normal"], b.inputs["Normal"])
    return bump


def bw(nt, color):
    n = nt.nodes.new("ShaderNodeRGBToBW")
    nt.links.new(color, n.inputs[0])
    return n.outputs[0]


def noise_tex(nt, vec, scale, detail=6.0, rough=0.55):
    n = nt.nodes.new("ShaderNodeTexNoise")
    n.inputs["Scale"].default_value = scale
    n.inputs["Detail"].default_value = detail
    n.inputs["Roughness"].default_value = rough
    if vec is not None:
        nt.links.new(vec, n.inputs["Vector"])
    return n.outputs["Fac"]


def wereld_z(nt):
    geo = nt.nodes.new("ShaderNodeNewGeometry")
    sz = nt.nodes.new("ShaderNodeSeparateXYZ")
    nt.links.new(geo.outputs["Position"], sz.inputs[0])
    return sz.outputs["Z"]


def holtes(nt, dist=0.08):
    ao = nt.nodes.new("ShaderNodeAmbientOcclusion")
    ao.only_local = True
    ao.samples = 8
    ao.inputs["Distance"].default_value = dist
    return math_node(nt, "SUBTRACT", 1.0, ao.outputs["AO"])


# --- Materialen ----------------------------------------------------------------------
def mat_steen(name, lo=(0.03, 0.03, 0.025), hi=(0.62, 0.58, 0.42), moss=0.7, lichen=1.3):
    """Losse steen: mossy_rock-korrel, per steen een eigen tint, mos in de holtes en onderaan."""
    m, nt, b = principled(name, 0.88, "steen")
    v = coords(nt, 1.2, rand_off=7.0)
    t = image(nt, "mossy_rock", "diff", v)
    rough = image(nt, "rock_surface", "rough", v)
    oi = nt.nodes.new("ShaderNodeObjectInfo")
    lum = bw(nt, t.outputs["Color"])
    f = math_node(nt, "ADD", math_node(nt, "MULTIPLY", oi.outputs["Random"], 0.6),
                  math_node(nt, "MULTIPLY", lum, 1.6))
    tint = ramp_node(nt, [(0.15, lo), (0.55, tuple((lo[i] + hi[i]) / 2 for i in range(3))), (0.95, hi)])
    nt.links.new(math_node(nt, "SUBTRACT", f, 0.2), tint.inputs["Fac"])
    col_ = tint.outputs["Color"]
    if moss:
        mt = image(nt, "mossy_rock", "diff", v)
        crev = holtes(nt)
        nz = noise_tex(nt, None, 3.0)
        low = math_node(nt, "MAXIMUM", math_node(nt, "SUBTRACT", 0.6, wereld_z(nt)), 0.0)
        mask = math_node(nt, "ADD", math_node(nt, "MULTIPLY", crev, 1.6), low)
        mask = math_node(nt, "MULTIPLY", mask, math_node(nt, "SUBTRACT", nz, 0.35))
        mask = math_node(nt, "MAXIMUM", math_node(nt, "MINIMUM", math_node(nt, "MULTIPLY", mask, 2.5 * moss), 0.85), 0.0)
        col_ = mix_rgb(nt, mask, col_, mix_rgb(nt, 1.0, mt.outputs["Color"], (0.75, 0.75, 0.45), "MULTIPLY"))
    ln = noise_tex(nt, v, 2.5, 8.0)
    lm = math_node(nt, "MULTIPLY", math_node(nt, "SUBTRACT", ln, 0.55), 3.0 * lichen)
    lm = math_node(nt, "MINIMUM", math_node(nt, "MAXIMUM", lm, 0.0), 0.55)
    col_ = mix_rgb(nt, lm, col_, (0.55, 0.48, 0.2))
    nt.links.new(col_, b.inputs["Base Color"])
    nt.links.new(math_node(nt, "MAXIMUM", rough.outputs["Color"], 0.8), b.inputs["Roughness"])
    pit = noise_tex(nt, v, 18.0, 10.0, 0.7)
    bump_from(nt, b, math_node(nt, "ADD", lum, math_node(nt, "MULTIPLY", pit, 0.6)), 0.9, 0.02)
    return m


def mat_specie(name, lo=(0.02, 0.016, 0.01), hi=(0.07, 0.055, 0.035)):
    m, nt, b = principled(name, 1.0, "steen")
    n = noise_tex(nt, None, 12.0)
    r = ramp_node(nt, [(0.3, lo), (0.7, hi)])
    nt.links.new(n, r.inputs["Fac"])
    nt.links.new(r.outputs["Color"], b.inputs["Base Color"])
    bump_from(nt, b, n, 0.8)
    return m


def mat_hout(name, tex, dark, light, scale=0.8, rand=0.0, rot=0.0, groep="hout", grijs=0.0):
    """Verweerd hout: Poly Haven-textuur via zijn helderheid naar de houtkleur; grijs = vergrauwd."""
    m, nt, b = principled(name, 0.8, groep)
    v = coords(nt, scale, rand_off=rand)
    if rot:
        mp = nt.nodes.new("ShaderNodeMapping")
        mp.inputs["Rotation"].default_value = (0, rot, 0)
        nt.links.new(v, mp.inputs["Vector"])
        v = mp.outputs[0]
    t = image(nt, tex, "diff", v)
    rough = image(nt, tex, "rough", v)
    lum = bw(nt, t.outputs["Color"])
    oi = nt.nodes.new("ShaderNodeObjectInfo")
    f = math_node(nt, "ADD", math_node(nt, "MULTIPLY", lum, 2.6), math_node(nt, "MULTIPLY", oi.outputs["Random"], 0.25))
    r = ramp_node(nt, [(0.05, tuple(c * 0.4 for c in dark)), (0.35, dark), (0.75, light),
                       (1.1, (min(1, light[0] * 1.6), light[1] * 1.6, light[2] * 1.6))])
    nt.links.new(math_node(nt, "SUBTRACT", f, 0.15), r.inputs["Fac"])
    c = r.outputs["Color"]
    if grijs:                                          # zilvergrijze verwering in vlekken
        g = noise_tex(nt, v, 1.5, 4.0)
        gm = math_node(nt, "MINIMUM", math_node(nt, "MAXIMUM", math_node(nt, "MULTIPLY",
                       math_node(nt, "SUBTRACT", g, 0.4), 3.0), 0.0), grijs)
        c = mix_rgb(nt, gm, c, mix_rgb(nt, 0.7, c, (0.16, 0.15, 0.13)))
    nt.links.new(c, b.inputs["Base Color"])
    nt.links.new(math_node(nt, "MAXIMUM", rough.outputs["Color"], 0.7), b.inputs["Roughness"])
    bump_from(nt, b, math_node(nt, "ADD", lum, math_node(nt, "MULTIPLY", bw(nt, rough.outputs["Color"]), -0.5)), 1.0, 0.03)
    return m


def mat_pleister(name, wit=(0.62, 0.6, 0.53), vuil=(0.22, 0.19, 0.14), scale=0.7, afbladder=0.66):
    """Gekalkt leempleister: white_plaster_rough_01, vuil onderaan en in strepen, afgebladderde
    plekken waar de leem doorkomt."""
    m, nt, b = principled(name, 0.92, "pleister")
    v = coords(nt, scale, rand_off=3.0)
    t = image(nt, "white_plaster_rough_01", "diff", v)
    nrm = image(nt, "white_plaster_rough_01", "nor_gl", v)
    lum = bw(nt, t.outputs["Color"])
    c = mix_rgb(nt, 1.0, t.outputs["Color"], wit, "MULTIPLY")
    c = mix_rgb(nt, 0.5, c, wit)
    # vuil: onderaan (opspattend water) en lage ruis
    z = wereld_z(nt)
    laag = math_node(nt, "MAXIMUM", math_node(nt, "SUBTRACT", 1.0, math_node(nt, "MULTIPLY", z, 1.6)), 0.0)
    n1 = noise_tex(nt, v, 2.2, 5.0)
    d = math_node(nt, "ADD", math_node(nt, "MULTIPLY", laag, 0.7), math_node(nt, "MULTIPLY",
                  math_node(nt, "SUBTRACT", n1, 0.45), 1.3))
    d = math_node(nt, "MINIMUM", math_node(nt, "MAXIMUM", d, 0.0), 0.75)
    c = mix_rgb(nt, d, c, vuil, "MIX")
    # afgebladderd: leem eronder (bruin), iets dieper
    n2 = noise_tex(nt, v, 3.0, 8.0, 0.65)
    af = math_node(nt, "GREATER_THAN", n2, afbladder)
    steen = image(nt, "rock_surface", "diff", v)
    c = mix_rgb(nt, af, c, mix_rgb(nt, 1.0, steen.outputs["Color"], (0.55, 0.45, 0.35), "MULTIPLY"))
    sc = nt.nodes.new("ShaderNodeTexVoronoi")        # haarscheurtjes
    sc.feature = "DISTANCE_TO_EDGE"
    sc.inputs["Scale"].default_value = 6.0
    nt.links.new(v, sc.inputs["Vector"])
    scheur = math_node(nt, "LESS_THAN", sc.outputs["Distance"], 0.012)
    scheur = math_node(nt, "MULTIPLY", scheur, math_node(nt, "GREATER_THAN", noise_tex(nt, v, 1.5, 2.0), 0.55))
    c = mix_rgb(nt, math_node(nt, "MULTIPLY", scheur, 0.7), c, (0.1, 0.09, 0.07))
    c = mix_rgb(nt, holtes(nt, 0.06), c, (0.08, 0.07, 0.05))
    nt.links.new(c, b.inputs["Base Color"])
    nm = nt.nodes.new("ShaderNodeNormalMap")
    nm.inputs["Strength"].default_value = 0.8
    nt.links.new(nrm.outputs["Color"], nm.inputs["Color"])
    bump = nt.nodes.new("ShaderNodeBump")
    bump.inputs["Strength"].default_value = 0.5
    bump.inputs["Distance"].default_value = 0.01
    nt.links.new(math_node(nt, "ADD", math_node(nt, "ADD", lum, math_node(nt, "MULTIPLY", af, -0.6)),
                           math_node(nt, "MULTIPLY", scheur, -0.4)), bump.inputs["Height"])
    nt.links.new(nm.outputs["Normal"], bump.inputs["Normal"])
    nt.links.new(bump.outputs["Normal"], b.inputs["Normal"])
    return m


def mat_ijzer(name, donker=(0.045, 0.045, 0.048), roest=(0.12, 0.045, 0.015)):
    """Smeedijzer: rusty_metal_02, roest in de holtes en onderkant, het werkvlak bovenop blank
    gesleten (glimmend, lichter) met krassen."""
    m, nt, b = principled(name, 0.55, "ijzer")
    v = coords(nt, 0.6)
    t = image(nt, "rusty_metal_02", "diff", v)
    rr = image(nt, "rusty_metal_02", "rough", v)
    nr = image(nt, "rusty_metal_02", "nor_gl", v)
    lum = bw(nt, t.outputs["Color"])
    geo = nt.nodes.new("ShaderNodeNewGeometry")
    sn = nt.nodes.new("ShaderNodeSeparateXYZ")
    nt.links.new(geo.outputs["Normal"], sn.inputs[0])
    boven = math_node(nt, "MINIMUM", math_node(nt, "MAXIMUM", math_node(nt, "MULTIPLY",
                      math_node(nt, "SUBTRACT", sn.outputs["Z"], 0.75), 5.0), 0.0), 1.0)
    # roestmasker uit de textuur (de oranje delen) plus holtes, minder op het werkvlak
    sat = nt.nodes.new("ShaderNodeSeparateColor")
    sat.mode = "HSV"
    nt.links.new(t.outputs["Color"], sat.inputs["Color"])
    rm = math_node(nt, "MULTIPLY", math_node(nt, "SUBTRACT", sat.outputs["Green"], 0.35), 1.2)
    rm = math_node(nt, "ADD", math_node(nt, "MAXIMUM", rm, 0.0), math_node(nt, "MULTIPLY", holtes(nt, 0.15), 1.0))
    rm = math_node(nt, "MULTIPLY", math_node(nt, "MINIMUM", rm, 1.0), math_node(nt, "SUBTRACT", 1.0, boven))
    rm = math_node(nt, "MULTIPLY", rm, 0.35)
    lr = ramp_node(nt, [(0.0, (donker[0] * 0.6, donker[1] * 0.6, donker[2] * 0.6)), (0.5, donker),
                        (1.0, (donker[0] * 4.0, donker[1] * 4.0, donker[2] * 4.2))])
    nt.links.new(lum, lr.inputs["Fac"])
    basis = lr.outputs["Color"]                      # alleen de helderheid: zwart ijzer, geen bruin
    c = mix_rgb(nt, rm, basis, mix_rgb(nt, 1.0, t.outputs["Color"], roest, "MULTIPLY"))
    # krassen: uitgerekte ruis, licht staal
    mp = nt.nodes.new("ShaderNodeMapping")
    mp.inputs["Scale"].default_value = (2.0, 40.0, 40.0)
    tc = nt.nodes.new("ShaderNodeTexCoord")
    nt.links.new(tc.outputs["Object"], mp.inputs["Vector"])
    kr = noise_tex(nt, mp.outputs[0], 3.0, 2.0)
    kras = math_node(nt, "GREATER_THAN", kr, 0.72)
    staal = (0.32, 0.31, 0.3)
    c = mix_rgb(nt, math_node(nt, "MULTIPLY", boven, 0.3), c, staal)
    c = mix_rgb(nt, math_node(nt, "MULTIPLY", kras, 0.7), c, (0.5, 0.49, 0.47))
    nt.links.new(c, b.inputs["Base Color"])
    b.inputs["Metallic"].default_value = 1.0     # donker metaal: weinig reflectie, harde glimlichten               # zwart smeedijzer met walshuid, geen chroom
    ruw = math_node(nt, "ADD", math_node(nt, "MULTIPLY", rr.outputs["Color"], 0.4), 0.2)
    ruw = math_node(nt, "ADD", ruw, math_node(nt, "MULTIPLY", rm, 0.4))
    ruw = math_node(nt, "SUBTRACT", ruw, math_node(nt, "MULTIPLY", boven, 0.15))
    nt.links.new(ruw, b.inputs["Roughness"])
    nm = nt.nodes.new("ShaderNodeNormalMap")
    nm.inputs["Strength"].default_value = 1.2
    nt.links.new(nr.outputs["Color"], nm.inputs["Color"])
    bump = nt.nodes.new("ShaderNodeBump")
    bump.inputs["Strength"].default_value = 0.45
    bump.inputs["Distance"].default_value = 0.015
    nt.links.new(math_node(nt, "ADD", noise_tex(nt, v, 3.0, 4.0), math_node(nt, "MULTIPLY", kras, -0.3)),
                 bump.inputs["Height"])
    nt.links.new(nm.outputs["Normal"], bump.inputs["Normal"])
    nt.links.new(bump.outputs["Normal"], b.inputs["Normal"])
    return m


def mat_dakpan(name, lo=(0.06, 0.008, 0.10), hi=(0.36, 0.12, 0.42)):
    """Dakpan: clay_roof_tiles als korrel, paars, per pan een eigen tint, korstmos en vuil."""
    m, nt, b = principled(name, 0.75, "dak")
    v = coords(nt, 2.0, rand_off=11.0)
    t = image(nt, "clay_roof_tiles", "diff", v)
    rough = image(nt, "clay_roof_tiles", "rough", v)
    oi = nt.nodes.new("ShaderNodeObjectInfo")
    lum = bw(nt, t.outputs["Color"])
    f = math_node(nt, "ADD", math_node(nt, "MULTIPLY", oi.outputs["Random"], 0.45), math_node(nt, "MULTIPLY", lum, 1.2))
    r = ramp_node(nt, [(0.1, lo), (0.55, tuple((lo[i] + hi[i]) / 2 for i in range(3))), (1.0, hi)])
    nt.links.new(math_node(nt, "SUBTRACT", f, 0.1), r.inputs["Fac"])
    c = r.outputs["Color"]
    # vuil aan de onderrand van elke pan (Generated z van de pan laag = onderkant)
    tc = nt.nodes.new("ShaderNodeTexCoord")
    sg = nt.nodes.new("ShaderNodeSeparateXYZ")
    nt.links.new(tc.outputs["Generated"], sg.inputs[0])
    rand_ = math_node(nt, "SUBTRACT", 1.0, sg.outputs["Y"])
    c = mix_rgb(nt, math_node(nt, "MULTIPLY", math_node(nt, "POWER", rand_, 4.0), 0.45), c, (0.05, 0.03, 0.04))
    ln = noise_tex(nt, coords(nt, 1.0, "Object"), 1.3, 8.0, 0.65)
    lm = math_node(nt, "MINIMUM", math_node(nt, "MAXIMUM", math_node(nt, "MULTIPLY",
                   math_node(nt, "SUBTRACT", ln, 0.6), 4.0), 0.0), 0.6)
    c = mix_rgb(nt, lm, c, (0.30, 0.30, 0.16))
    nt.links.new(c, b.inputs["Base Color"])
    nt.links.new(math_node(nt, "MAXIMUM", rough.outputs["Color"], 0.55), b.inputs["Roughness"])
    bump_from(nt, b, lum, 0.5, 0.01)
    return m


def mat_flat(name, c, rough=0.8, groep="rest"):
    m, nt, b = principled(name, rough, groep)
    b.inputs["Base Color"].default_value = (*c, 1)
    return m


def mat_ruit(name):
    """Oud glas: donker, wat groenig, glanzend (geen echte transmissie: binnen is het donker)."""
    m, nt, b = principled(name, 0.08, "rest")
    n = noise_tex(nt, None, 30.0, 2.0)
    r = ramp_node(nt, [(0.3, (0.012, 0.016, 0.014)), (0.8, (0.04, 0.05, 0.045))])
    nt.links.new(n, r.inputs["Fac"])
    nt.links.new(r.outputs["Color"], b.inputs["Base Color"])
    b.inputs["Specular IOR Level"].default_value = 0.8
    bump_from(nt, b, noise_tex(nt, None, 6.0, 1.0), 0.15, 0.01)
    return m


def mat_blad(name, c0=(0.02, 0.09, 0.015), c1=(0.12, 0.30, 0.04)):
    m, nt, b = principled(name, 0.55, "rest")
    oi = nt.nodes.new("ShaderNodeObjectInfo")
    r = ramp_node(nt, [(0.0, c0), (1.0, c1)])
    nt.links.new(oi.outputs["Random"], r.inputs["Fac"])
    nt.links.new(r.outputs["Color"], b.inputs["Base Color"])
    return m


def mat_doek(name, paars=(0.16, 0.0, 0.22), wit=(0.72, 0.70, 0.64), banen=8.0):
    """Zeildoek met paars-witte banen dwars op de wiek (Generated X = langs de wiek), vuil en
    weefsel."""
    m, nt, b = principled(name, 0.95, "doek")
    b.inputs["Specular IOR Level"].default_value = 0.2
    tc = nt.nodes.new("ShaderNodeTexCoord")
    sg = nt.nodes.new("ShaderNodeSeparateXYZ")
    nt.links.new(tc.outputs["Generated"], sg.inputs[0])
    w = math_node(nt, "FRACT", math_node(nt, "MULTIPLY", sg.outputs["X"], banen))
    band = math_node(nt, "GREATER_THAN", w, 0.5)
    c = mix_rgb(nt, band, paars, wit)
    vuil = noise_tex(nt, tc.outputs["Object"], 3.0, 6.0)
    c = mix_rgb(nt, math_node(nt, "MULTIPLY", math_node(nt, "MAXIMUM", math_node(nt, "SUBTRACT", vuil, 0.45), 0.0), 1.2),
                c, (0.25, 0.2, 0.14))
    nt.links.new(c, b.inputs["Base Color"])
    mp = nt.nodes.new("ShaderNodeMapping")
    mp.inputs["Scale"].default_value = (300, 300, 300)
    nt.links.new(tc.outputs["Object"], mp.inputs["Vector"])
    wv = nt.nodes.new("ShaderNodeTexChecker")
    nt.links.new(mp.outputs[0], wv.inputs["Vector"])
    bump_from(nt, b, math_node(nt, "ADD", bw(nt, wv.outputs["Color"]), math_node(nt, "MULTIPLY", vuil, 2.0)), 0.25, 0.005)
    return m


def mat_gras(name):
    m, nt, b = principled(name, 0.5, "rest")
    tc = nt.nodes.new("ShaderNodeTexCoord")
    sep = nt.nodes.new("ShaderNodeSeparateXYZ")
    nt.links.new(tc.outputs["Generated"], sep.inputs[0])
    n = noise_tex(nt, tc.outputs["Object"], 40.0)
    f = math_node(nt, "ADD", math_node(nt, "MULTIPLY", sep.outputs["Z"], 0.7), math_node(nt, "MULTIPLY", n, 0.5))
    r = ramp_node(nt, [(0.05, (0.01, 0.08, 0.01)), (0.4, (0.05, 0.28, 0.03)), (0.85, (0.22, 0.42, 0.08))])
    nt.links.new(f, r.inputs["Fac"])
    nt.links.new(r.outputs["Color"], b.inputs["Base Color"])
    return m


HALM_STOPS = [(0.0, (0.25, 0.09, 0.008)), (0.3, (0.6, 0.3, 0.03)), (0.55, (0.86, 0.52, 0.09)),
              (0.8, (0.95, 0.68, 0.2)), (1.0, (1.0, 0.82, 0.4))]          # goudgeel naar het oranje van de sprite


def mat_halm(name, stops=HALM_STOPS, verweerd=0.0):
    """Strohalm op hair curves: kleur per bos ('bos') en per halm (Random), punten lichter."""
    m, nt, b = principled(name, 0.7, "dak")
    b.inputs["Specular IOR Level"].default_value = 0.12
    hi = nt.nodes.new("ShaderNodeHairInfo")
    at = nt.nodes.new("ShaderNodeAttribute")
    at.attribute_name = "bos"
    fac = math_node(nt, "ADD", math_node(nt, "MULTIPLY", at.outputs["Fac"], 0.6),
                    math_node(nt, "MULTIPLY", hi.outputs["Random"], 0.3))
    fac = math_node(nt, "ADD", fac, math_node(nt, "MULTIPLY", hi.outputs["Intercept"], 0.15))
    fac = math_node(nt, "ADD", fac, 0.1)
    r = ramp_node(nt, stops)
    nt.links.new(fac, r.inputs["Fac"])
    c = r.outputs["Color"]
    if verweerd:                                     # grijsbruine plekken en mos, laag in de halm
        geo = nt.nodes.new("ShaderNodeNewGeometry")
        n = noise_tex(nt, geo.outputs["Position"], 0.9, 4.0, 0.6)
        vlek = math_node(nt, "MINIMUM", math_node(nt, "MAXIMUM", math_node(nt, "MULTIPLY",
                         math_node(nt, "SUBTRACT", n, 0.5), 3.0), 0.0), verweerd)
        c = mix_rgb(nt, vlek, c, mix_rgb(nt, 0.55, c, (0.16, 0.13, 0.08)))
        n2 = noise_tex(nt, geo.outputs["Position"], 2.5, 6.0, 0.7)
        mos = math_node(nt, "MULTIPLY", math_node(nt, "MAXIMUM", math_node(nt, "SUBTRACT", n2, 0.66), 0.0), 2.5)
        mos = math_node(nt, "MULTIPLY", math_node(nt, "MINIMUM", mos, 1.0),
                        math_node(nt, "SUBTRACT", 1.0, hi.outputs["Intercept"]))
        c = mix_rgb(nt, math_node(nt, "MULTIPLY", mos, 0.7), c, (0.08, 0.11, 0.03))
    nt.links.new(c, b.inputs["Base Color"])
    return m


def mat_rietlaag(name):
    """Onderlaag onder de halmen: thatch_roof_angled, donker getint zodat gaten als diepte lezen."""
    m, nt, b = principled(name, 0.9, "dak")
    v = coords(nt, 0.8)
    t = image(nt, "thatch_roof_angled", "diff", v)
    lum = bw(nt, t.outputs["Color"])
    r = ramp_node(nt, [(0.02, (0.05, 0.02, 0.0)), (0.25, (0.35, 0.18, 0.03)), (0.5, (0.75, 0.5, 0.12))])
    nt.links.new(lum, r.inputs["Fac"])
    nt.links.new(r.outputs["Color"], b.inputs["Base Color"])
    bump_from(nt, b, lum, 0.6)
    return m


# --- Geometrie-hulpjes -----------------------------------------------------------------
def put(obj, mat, smooth=True):
    obj.data.materials.append(mat)
    if smooth:
        for p in obj.data.polygons:
            p.use_smooth = True
    return obj


def mesh_obj(name, verts, faces, mat, smooth=True, loc=(0, 0, 0)):
    me = bpy.data.meshes.new(name)
    me.from_pydata([tuple(v) for v in verts], [], faces)
    me.update()
    ob = bpy.data.objects.new(name, me)
    ob.location = loc
    col.objects.link(ob)
    return put(ob, mat, smooth)


def box(name, loc, size, mat, rot=(0, 0, 0), bevel=0.0, rot_z=None):
    """Balk; schaal wordt toegepast, zodat de textuur (objectcoordinaten) in meters ligt."""
    if rot_z is not None:
        rot = (0, 0, rot_z)
    bpy.ops.mesh.primitive_cube_add(size=1, location=loc, rotation=rot)
    o = bpy.context.object
    o.name = name
    o.scale = size
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    if bevel:
        m = o.modifiers.new("b", "BEVEL")
        m.width, m.segments = bevel, 2
        m.limit_method = "ANGLE"
    return put(o, mat, smooth=False)


def balk(name, p, q, w, h, mat, bevel=0.015, rol=0.0, ruw=0.0):
    """Balk van p naar q (doorsnede w x h), met onregelmatige randen als ruw > 0 (gekapt hout)."""
    p, q = Vector(p), Vector(q)
    d = q - p
    L = d.length
    o = box(name, (0, 0, 0), (L, w, h), mat, bevel=bevel)
    if ruw:
        for vv in o.data.vertices:
            vv.co.y += random.uniform(-ruw, ruw)
            vv.co.z += random.uniform(-ruw, ruw)
    rq = d.to_track_quat("X", "Z")
    o.rotation_mode = "QUATERNION"
    o.rotation_quaternion = rq @ Matrix.Rotation(rol, 4, "X").to_quaternion()
    o.location = (p + q) / 2
    return o


def cyl(name, loc, r, depth, mat, rot=(0, 0, 0), verts=16):
    bpy.ops.mesh.primitive_cylinder_add(vertices=verts, radius=r, depth=depth, location=loc, rotation=rot)
    o = bpy.context.object
    o.name = name
    return put(o, mat)


def stone_mesh(name, seed, p=6.0, bumps=0.15, cuts=5, sub=4, hf=0.06):
    """Onregelmatige steen in een eenheidskubus (uit peasant_hut.py)."""
    rnd = random.Random(seed)
    bm = bmesh.new()
    bmesh.ops.create_icosphere(bm, subdivisions=sub, radius=1.0)
    off = Vector((rnd.uniform(-50, 50), rnd.uniform(-50, 50), rnd.uniform(-50, 50)))
    planes = []
    for _ in range(cuts):
        nrm = Vector((rnd.gauss(0, 1), rnd.gauss(0, 1), rnd.gauss(0, 0.4))).normalized()
        planes.append((nrm, rnd.uniform(0.72, 0.92)))
    for v in bm.verts:
        d = v.co.normalized()
        k = (abs(d.x) ** p + abs(d.y) ** p + abs(d.z) ** p) ** (1 / p)
        c = d / k
        c = c * (1 + bumps * noise.noise(c * 1.3 + off) + hf * noise.noise(c * 5.0 + off)
                 + hf * 0.5 * noise.noise(c * 11.0 + off))
        for nrm, h in planes:
            e = c.dot(nrm) - h
            if e > 0:
                c = c - nrm * e
        v.co = c
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    for poly in me.polygons:
        poly.use_smooth = True
    me.set_sharp_from_angle(angle=math.radians(35))
    return me


STONES = []
stones_out = []


def stenen_maken(mat, n=14, seed=100, **kw):
    global STONES
    STONES = [stone_mesh(f"steen{k}", seed + k, **kw) for k in range(n)]
    for me in STONES:
        me.materials.append(mat)


def stone(loc, size, rot_z, mat=None, mesh=None, tilt=(0.0, 0.0)):
    me = mesh or random.choice(STONES)
    ob = bpy.data.objects.new("steen", me)
    ob.location = loc
    ob.rotation_euler = (tilt[0], tilt[1], rot_z)
    ob.scale = (size[0] / 2, size[1] / 2, size[2] / 2)
    col.objects.link(ob)
    if mat is not None:
        ob.material_slots[0].link = "OBJECT"
        ob.material_slots[0].material = mat
    stones_out.append(ob)
    return ob


def flat_wall(p0, p1, z0, z1, gaten=(), depth=0.2, hs=(0.12, 0.2), ls=(0.2, 0.38), mat=None, uit=0.0,
              ztop=None):
    """Rechte muur van p0 naar p1 (x, y), stenen in lagen; gaten = (t0, t1, z0, z1) langs de muur.
    ztop(t) kapt de muur af (gevel onder een boog). uit = willekeurig naar buiten (ruwe muur)."""
    d = Vector((p1[0] - p0[0], p1[1] - p0[1], 0))
    Lt = d.length
    d.normalize()
    nrm = Vector((d.y, -d.x, 0))
    ang = math.atan2(d.y, d.x)
    z = z0
    while z < z1:
        h = random.uniform(*hs)
        t = -random.uniform(0, 0.15)
        while t < Lt:
            L = random.uniform(*ls)
            vrij = all(not (t + L > g0 and t < g1 and z + h > h0 and z < h1) for g0, g1, h0, h1 in gaten)
            tm = min(max(t + L / 2, 0.0), Lt)
            if ztop and z + h * 0.5 > ztop(tm):
                vrij = False
            if vrij:
                o = random.uniform(-uit, uit)
                stone((p0[0] + d.x * tm + nrm.x * o, p0[1] + d.y * tm + nrm.y * o, z + h / 2),
                      (L * random.uniform(0.9, 1.0), depth, h * random.uniform(0.85, 0.95)), ang, mat,
                      tilt=(random.uniform(-0.05, 0.05), random.uniform(-0.06, 0.06)))
            t += L + 0.008
        z += h + 0.006


def arch_outline(w, h, z0, n=16):
    """(y, z) langs een rondboog: links omhoog, over de boog, rechts omlaag."""
    zc = z0 + h - w / 2
    pts = [(-w / 2, z0), (-w / 2, zc)]
    for k in range(1, n):
        t = math.pi * (1 - k / n)
        pts.append((w / 2 * math.cos(t), zc + w / 2 * math.sin(t)))
    return pts + [(w / 2, zc), (w / 2, z0)]


def boog_stenen(cx, cy, rot_z, z0, w, h, dikte=0.22, diep=0.3, mat=None, n=11):
    """Rondboog van wiggen (voussoirs) plus negge-stenen langs de stijlen. Lokaal: x naar buiten,
    y langs de muur."""
    R = Matrix.Rotation(rot_z, 3, "Z")
    zc = z0 + h - w / 2
    r = w / 2 + dikte / 2
    for k in range(n):
        a = math.pi * (k + 0.5) / n
        radiaal = Vector((0, math.cos(a), math.sin(a)))
        raak = Vector((0, -math.sin(a), math.cos(a)))
        lp = Vector((0.03 + random.uniform(-0.01, 0.02), 0, zc)) + radiaal * r
        wp = R @ lp
        o = stone((cx + wp.x, cy + wp.y, wp.z), (1, 1, 1), 0.0, mat)
        M = Matrix((R @ Vector((1, 0, 0)), R @ raak, R @ radiaal)).transposed().to_4x4()
        S = Matrix.Diagonal((diep / 2, math.pi * r / n * 0.46, dikte * 0.5 * random.uniform(0.9, 1.05), 1))
        o.matrix_world = Matrix.Translation(o.location) @ M @ S
    z = z0
    while z < zc:
        hh = random.uniform(0.2, 0.3)
        for s in (-1, 1):
            Ls = random.uniform(0.18, 0.3)
            lp = Vector((0.03, s * (w / 2 + Ls / 2), z + hh / 2))
            wp = R @ lp
            stone((cx + wp.x, cy + wp.y, wp.z), (Ls, diep, hh * 0.92), rot_z + math.pi / 2, mat)
        z += hh + 0.008


DEUREN = {}


def plank_door(name, cx, cy, z0, w, h, rot_z, mat, ijzer, n=4, boog=True, dik=0.05):
    """Deur van losse planken (rondboog of recht), twee klampen, hengsels en een ring."""
    rot = Matrix.Rotation(rot_z, 3, "Z")
    pw = w / n
    delen = []
    for i in range(n):
        x = -w / 2 + pw * (i + 0.5)
        if boog:
            top = h - w / 2 + math.sqrt(max(0.0, (w / 2) ** 2 - (abs(x) + pw * 0.3) ** 2))
        else:
            top = h
        top -= random.uniform(0, 0.02)
        off = rot @ Vector((random.uniform(-0.006, 0.006), x, 0))
        delen.append(box(name, (cx + off.x, cy + off.y, z0 + top / 2), (dik, pw - 0.01, top), mat, rot_z=rot_z,
                         bevel=0.008))
    for zz in (0.22 * h, 0.68 * h):                       # klampen met ijzeren hengsels
        off = rot @ Vector((dik * 0.7, 0, 0))
        delen.append(box(name, (cx + off.x, cy + off.y, z0 + zz), (0.03, w * 0.86, 0.1), mat, rot_z=rot_z, bevel=0.008))
        off = rot @ Vector((dik * 0.7 + 0.02, -w * 0.18, 0))
        delen.append(box(name + "_hengsel", (cx + off.x, cy + off.y, z0 + zz), (0.012, w * 0.62, 0.045), ijzer,
                         rot_z=rot_z, bevel=0.004))
    off = rot @ Vector((dik + 0.02, w * 0.3, 0))
    bpy.ops.mesh.primitive_torus_add(major_radius=0.04, minor_radius=0.007, location=(cx + off.x, cy + off.y, z0 + h * 0.48),
                                     rotation=(0, math.pi / 2, rot_z))
    delen.append(put(bpy.context.object, ijzer))
    return delen


def scharnier(name, delen, cx, cy, w, rot_z, dik=0.05):
    """Leeg object op de scharnieras (kant -y lokaal) met de planken als kinderen. Open naar buiten
    met rotation_euler.z = dicht - hoek (zet_deur)."""
    rot = Matrix.Rotation(rot_z, 4, "Z")
    T = Matrix.Translation((cx, cy, 0)) @ rot @ Matrix.Translation((-dik / 2, -w / 2, 0))
    e = bpy.data.objects.new(name, None)
    e.empty_display_type = "SINGLE_ARROW"
    col.objects.link(e)
    e.matrix_world = T
    for d in delen:
        d.parent = e
        d.matrix_parent_inverse = T.inverted()
    e["dicht"] = e.rotation_euler.z
    DEUREN[name] = (e, delen)
    return e


def zet_deur(name, graden):
    e = DEUREN[name][0]
    e.rotation_euler.z = e["dicht"] - math.radians(graden)


def anker(name, loc):
    e = bpy.data.objects.new(name, None)
    e.empty_display_type = "PLAIN_AXES"
    e.empty_display_size = 0.2
    e.location = loc
    col.objects.link(e)
    return e


def lod1(o):
    """Proxy voor de LOD1-bake: niet in de render, niet in de hoge glb."""
    o["lod1"] = True
    o.hide_render = True
    return o


def strands(name, curves, mat, bos, rad):
    """Hair curves: curves = lijst puntenlijsten; bos = 0..1 per curve; rad(u) straal langs de halm."""
    cv = bpy.data.hair_curves.new(name)
    cv.add_curves([len(c) for c in curves])
    cv.position_data.foreach_set("vector", [q for c in curves for p in c for q in p])
    ra = cv.attributes.new("radius", "FLOAT", "POINT")
    ra.data.foreach_set("value", [rad(i / (len(c) - 1)) for c in curves for i in range(len(c))])
    ba = cv.attributes.new("bos", "FLOAT", "CURVE")
    ba.data.foreach_set("value", bos)
    cv.materials.append(mat)
    ob = bpy.data.objects.new(name, cv)
    col.objects.link(ob)
    return ob


def gras_pol(loc, mat, n=40, h=0.25, r=0.12, seed=0):
    """Graspol van platte sprieten (driehoekjes)."""
    rnd = random.Random(seed)
    vs, fs = [], []
    for i in range(n):
        a = rnd.uniform(0, 2 * math.pi)
        rr = r * math.sqrt(rnd.random())
        bx, by = loc[0] + rr * math.cos(a), loc[1] + rr * math.sin(a)
        hh = h * rnd.uniform(0.5, 1.2)
        lean = rnd.uniform(0.1, 0.5) * hh
        la = a + rnd.uniform(-0.6, 0.6)
        w = 0.008
        k = len(vs)
        px, py = -math.sin(la) * w, math.cos(la) * w
        vs += [(bx - px, by - py, loc[2]), (bx + px, by + py, loc[2]),
               (bx + math.cos(la) * lean * 0.5 + px * 0.5, by + math.sin(la) * lean * 0.5 + py * 0.5, loc[2] + hh * 0.6),
               (bx + math.cos(la) * lean, by + math.sin(la) * lean, loc[2] + hh)]
        fs += [[k, k + 1, k + 2], [k, k + 2, k + 3]]
    o = mesh_obj("gras", vs, fs, mat, smooth=False)
    return o


# --- Camera, licht, render ---------------------------------------------------------------
R_SCHERM = Vector((math.cos(math.radians(YAW - 90)), math.sin(math.radians(YAW - 90)), 0))   # schermrechts


def schermassen():
    yaw, pitch = math.radians(YAW), math.radians(PITCH)
    dirv = Vector((math.cos(yaw) * math.cos(pitch), math.sin(yaw) * math.cos(pitch), math.sin(pitch)))
    d = -dirv
    r = d.cross(Vector((0, 0, 1))).normalized()
    u = r.cross(d).normalized()
    return dirv, r, u


def iso_camera(ref_world, ref_px, W, H):
    """Ortho-camera (yaw 225, pitch 30) zo dat ref_world op pixel ref_px (4x-sprite) valt in een
    beeld van W x H (4x-pixels); 87,5 px per meter."""
    dirv, r, u = schermassen()
    s = PX_M
    dx, dy = ref_px[0] - W / 2, ref_px[1] - H / 2
    target = Vector(ref_world) - r * (dx / s) + u * (dy / s)
    cam_d = bpy.data.cameras.new("cam")
    cam_d.type = "ORTHO"
    cam_d.ortho_scale = max(W, H) / s
    cam = bpy.data.objects.new("cam", cam_d)
    col.objects.link(cam)
    cam.location = target + dirv * 40
    cam.rotation_euler = (target - cam.location).to_track_quat("-Z", "Y").to_euler()
    cam_d.clip_end = 100
    scene.camera = cam
    scene.render.resolution_x = int(W * SCALE / 4)
    scene.render.resolution_y = int(H * SCALE / 4)
    return cam


def sun(name, energy, rot, color=(1, 1, 1), angle=5.0):
    d = bpy.data.lights.new(name, "SUN")
    d.energy = energy
    d.color = color
    d.angle = math.radians(angle)
    o = bpy.data.objects.new(name, d)
    col.objects.link(o)
    o.rotation_euler = rot
    return o


ZON_ROT = (math.radians(35), 0, math.radians(45))   # van rechtsvoor (+X, -Y): voorgevel in de zon, schaduw links
WARM = (1.0, 0.9, 0.75)


def licht_en_wereld():
    bpy.ops.mesh.primitive_plane_add(size=40, location=(0, 0, 0))
    vanger = bpy.context.object
    vanger.name = "vanger"
    vanger.is_shadow_catcher = True
    sun("zon", 2.6, ZON_ROT, WARM)
    sun("vul", 1.6, (math.radians(55), 0, math.radians(-115)), (0.95, 0.95, 1.0), angle=25.0)
    world = bpy.data.worlds.new("w")
    world.use_nodes = True
    wn = world.node_tree
    bg = wn.nodes["Background"]
    env = wn.nodes.new("ShaderNodeTexEnvironment")
    env.image = bpy.data.images.load(os.path.join(TEX, "qwantani_late_afternoon_1k.hdr"))
    klem = mix_rgb(wn, 1.0, env.outputs["Color"], (1.2, 1.2, 1.2), "DARKEN")
    wn.links.new(klem, bg.inputs["Color"])
    bg.inputs["Strength"].default_value = 0.45
    scene.world = world
    return vanger


def gpu():
    p = bpy.context.preferences.addons["cycles"].preferences
    try:
        p.compute_device_type = "CUDA"               # OptiX faalt op deze driver
        p.get_devices()
        for d in p.devices:
            d.use = d.type == "CUDA"
        scene.cycles.device = "GPU"
        return "CUDA"
    except TypeError:
        return "CPU"


def exporteer_hoog(pad):
    """glTF van het hoge model: zonder camera, licht, vanger, halmen, LOD1-proxies en bakschillen (rt = laag)."""
    for o in bpy.context.view_layer.objects:
        o.select_set(o.type in ("MESH", "EMPTY") and not o.get("lod1") and o.get("rt") != "laag"
                     and o.name != "vanger")
    bpy.ops.export_scene.gltf(filepath=pad, export_format="GLB", use_selection=True, export_apply=True,
                              export_cameras=False, export_lights=False)


def afronden(naam, ref_world, ref_px, W, H, samples=160):
    """Camera, licht, opslaan (.blend, .glb) en de beauty naar preview/<naam>_render.png."""
    os.makedirs(PREVIEW, exist_ok=True)
    licht_en_wereld()
    iso_camera(ref_world, ref_px, W, H)
    scene.render.engine = "CYCLES"
    print("APPARAAT", gpu())
    scene.cycles.samples = 32 if SNEL else samples
    scene.cycles.use_denoising = True
    scene.cycles.max_bounces = 6
    scene.render.film_transparent = True
    scene.view_settings.view_transform = "Standard"
    scene.render.image_settings.color_mode = "RGBA"
    scene.render.filepath = os.path.join(PREVIEW, f"{naam}_render.png")
    bpy.ops.wm.save_as_mainfile(filepath=os.path.join(GB, f"{naam}.blend"), compress=True)
    if "geen_glb" not in OPTS:
        exporteer_hoog(os.path.join(GB, f"{naam}.glb"))
    if "geen_render" not in OPTS:
        bpy.ops.render.render(write_still=True)
    print("KLAAR", scene.render.filepath, "STENEN", len(stones_out))
