"""Gedeelde bouwstenen voor melkerij_boerderij.py en kippenhok.py (Blender 5.2, headless).

Zelfde huisstijl als ../peasant_hut.py: iso-camera (yaw 225, pitch 30, ortho, 21,9 px/m op 1x),
zon + vullicht + HDRI, schaduwvanger, Poly Haven-texturen (../textures, CC0) en riet als losse halmen
(hair curves). Het bakken naar een game-glb (LOD0 + LOD1) staat onderaan: rt_bouw().

Objecten krijgen een eigenschap "rt":
  "opaak" (standaard)  -> gaat mee in de opake atlas
  "riet"               -> dakschil: krijgt de gebakken halmen (bron: de halmen zelf)
  "halm"               -> alleen bron voor het bakken (hair curves), gaat niet mee
  "weg"                -> niet in de glb (schaduwvanger, hulpvormen)
Deurdelen hangen als kind onder een leeg object (scharnier); dat wordt in de glb de draaibare deur.
"""
import math
import os
import random
import sys
import time

import bmesh
import bpy
import numpy as np
from mathutils import Matrix, Vector, noise

HERE = os.path.dirname(os.path.abspath(__file__))
MODELLEN = os.path.dirname(HERE)
TEX = os.path.join(MODELLEN, "textures")
PREVIEW = os.path.join(HERE, "preview")
PX_PER_M = 21.9                     # sprite-schaal op 1x (87,5 px/m op 4x), zoals de hut
T0 = time.time()


def log(*a):
    print(f"[erf {time.time() - T0:6.1f}s]", *a, flush=True)


def opties():
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    return {a.split("=")[0]: (a.split("=", 1)[1] if "=" in a else "1") for a in argv}


def leeg():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    return bpy.context.scene


def col():
    return bpy.context.scene.collection


# --- Node-hulpjes (uit peasant_hut.py) ---------------------------------------------
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


def coords(nt, scale=1.0, kind="Object", rand_off=0.0, stretch=(1, 1, 1)):
    tc = nt.nodes.new("ShaderNodeTexCoord")
    mp = nt.nodes.new("ShaderNodeMapping")
    mp.inputs["Scale"].default_value = (scale * stretch[0], scale * stretch[1], scale * stretch[2])
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


def ruis(nt, vec, scale, detail=4.0, rough=0.6, distort=0.0):
    n = nt.nodes.new("ShaderNodeTexNoise")
    n.inputs["Scale"].default_value = scale
    n.inputs["Detail"].default_value = detail
    n.inputs["Roughness"].default_value = rough
    n.inputs["Distortion"].default_value = distort
    if vec is not None:
        nt.links.new(vec, n.inputs["Vector"])
    return n.outputs["Fac"]


def hoogte_z(nt):
    geo = nt.nodes.new("ShaderNodeNewGeometry")
    s = nt.nodes.new("ShaderNodeSeparateXYZ")
    nt.links.new(geo.outputs["Position"], s.inputs[0])
    return s.outputs["Z"]


def holte(nt, dist=0.1, samples=8):
    ao = nt.nodes.new("ShaderNodeAmbientOcclusion")
    ao.only_local = True
    ao.samples = samples
    ao.inputs["Distance"].default_value = dist
    return math_node(nt, "SUBTRACT", 1.0, ao.outputs["AO"])


def klem(nt, v, lo=0.0, hi=1.0):
    return math_node(nt, "MINIMUM", math_node(nt, "MAXIMUM", v, lo), hi)


# --- Materialen ----------------------------------------------------------------
STRO_STOPS = [(0.0, (0.30, 0.14, 0.012)), (0.3, (0.70, 0.42, 0.06)), (0.55, (0.92, 0.64, 0.15)),
              (0.8, (1.0, 0.78, 0.28)), (1.0, (1.0, 0.88, 0.48))]


def mat_halm(name, stops=STRO_STOPS, grijs=0.0):
    """Strohalm op hair curves: kleur per bos ('bos') en per halm (Random), punten lichter.
    grijs: verweerd (grijzer en donkerder) bovenaan in de bos."""
    m, nt, b = principled(name, 0.72)
    b.inputs["Specular IOR Level"].default_value = 0.15
    hi = nt.nodes.new("ShaderNodeHairInfo")
    at = nt.nodes.new("ShaderNodeAttribute")
    at.attribute_name = "bos"
    fac = math_node(nt, "ADD", math_node(nt, "MULTIPLY", at.outputs["Fac"], 0.55),
                    math_node(nt, "MULTIPLY", hi.outputs["Random"], 0.35))
    fac = math_node(nt, "ADD", fac, math_node(nt, "MULTIPLY", hi.outputs["Intercept"], 0.18))
    r = ramp_node(nt, stops)
    nt.links.new(fac, r.inputs["Fac"])
    c = r.outputs["Color"]
    if grijs:
        tc = nt.nodes.new("ShaderNodeTexCoord")
        w = ruis(nt, tc.outputs["Object"], 0.9, 3.0)
        g = klem(nt, math_node(nt, "MULTIPLY", math_node(nt, "SUBTRACT", w, 0.42), 3.0 * grijs), 0.0, 0.75)
        c = mix_rgb(nt, g, c, (0.30, 0.27, 0.20))
        # mos: groenige plekjes, vooral op de lage (oude) halmdelen
        m2 = ruis(nt, tc.outputs["Object"], 3.5, 5.0)
        mm = math_node(nt, "MULTIPLY", math_node(nt, "SUBTRACT", m2, 0.62), 2.2 * grijs)
        mm = math_node(nt, "MULTIPLY", klem(nt, mm, 0.0, 0.6), math_node(nt, "SUBTRACT", 1.0, hi.outputs["Intercept"]))
        c = mix_rgb(nt, mm, c, (0.12, 0.13, 0.04))
    nt.links.new(c, b.inputs["Base Color"])
    return m


def mat_rietlaag(name, donker=0.45):
    """Onderlaag onder de halmen (UV in meters): Poly Haven-riet, donker, zodat gaten diepte lezen."""
    m, nt, b = principled(name, 0.92)
    tc = nt.nodes.new("ShaderNodeTexCoord")
    mp = nt.nodes.new("ShaderNodeMapping")
    mp.inputs["Scale"].default_value = (0.9, 0.7, 1)
    nt.links.new(tc.outputs["UV"], mp.inputs["Vector"])
    t = image(nt, "thatch_roof_angled", "diff", mp.outputs[0], box=False)
    v = bw(nt, t.outputs["Color"])
    r = ramp_node(nt, [(0.02, (0.05, 0.025, 0.004)), (0.3, (0.38 * donker * 2, 0.22 * donker * 2, 0.04)),
                       (0.6, (0.75, 0.50, 0.12))])
    nt.links.new(v, r.inputs["Fac"])
    nt.links.new(r.outputs["Color"], b.inputs["Base Color"])
    bump_from(nt, b, v, 0.6)
    return m


def mat_steen(name, lo=(0.03, 0.03, 0.025), hi=(0.62, 0.58, 0.42), moss=0.7, lichen=1.0):
    """Losse steen: rock_surface/mossy_rock ontkleurd, tint per steen, mos in holtes en onderaan."""
    m, nt, b = principled(name, 0.88)
    v = coords(nt, 1.2, rand_off=7.0)
    t = image(nt, "mossy_rock", "diff", v)
    rough = image(nt, "rock_surface", "rough", v)
    oi = nt.nodes.new("ShaderNodeObjectInfo")
    lum = bw(nt, t.outputs["Color"])
    f = math_node(nt, "ADD", math_node(nt, "MULTIPLY", oi.outputs["Random"], 0.6), math_node(nt, "MULTIPLY", lum, 1.6))
    tint = ramp_node(nt, [(0.15, lo), (0.55, tuple((a + c) / 2 for a, c in zip(lo, hi))), (0.95, hi)])
    nt.links.new(math_node(nt, "SUBTRACT", f, 0.2), tint.inputs["Fac"])
    col_ = tint.outputs["Color"]
    if moss:
        mt = image(nt, "mossy_rock", "diff", v)
        low = math_node(nt, "MAXIMUM", math_node(nt, "SUBTRACT", 0.5, hoogte_z(nt)), 0.0)
        mask = math_node(nt, "ADD", math_node(nt, "MULTIPLY", holte(nt, 0.08), 1.6), low)
        mask = math_node(nt, "MULTIPLY", mask, math_node(nt, "SUBTRACT", ruis(nt, None, 3.0, 6.0), 0.35))
        mask = klem(nt, math_node(nt, "MULTIPLY", mask, 2.5 * moss), 0.0, 0.85)
        col_ = mix_rgb(nt, mask, col_, mix_rgb(nt, 1.0, mt.outputs["Color"], (0.75, 0.75, 0.45), "MULTIPLY"))
    if lichen:
        lm = math_node(nt, "MULTIPLY", math_node(nt, "SUBTRACT", ruis(nt, v, 2.5, 8.0), 0.55), 3.0 * lichen)
        col_ = mix_rgb(nt, klem(nt, lm, 0.0, 0.5), col_, (0.55, 0.50, 0.30))
    nt.links.new(col_, b.inputs["Base Color"])
    nt.links.new(math_node(nt, "MAXIMUM", rough.outputs["Color"], 0.8), b.inputs["Roughness"])
    h = math_node(nt, "ADD", lum, math_node(nt, "MULTIPLY", ruis(nt, v, 18.0, 10.0, 0.7), 0.6))
    bump_from(nt, b, h, 0.9, 0.02)
    return m


def mat_specie(name, c0=(0.06, 0.055, 0.045), c1=(0.22, 0.2, 0.16)):
    m, nt, b = principled(name, 1.0)
    n = ruis(nt, None, 12.0)
    r = ramp_node(nt, [(0.3, c0), (0.7, c1)])
    nt.links.new(n, r.inputs["Fac"])
    nt.links.new(r.outputs["Color"], b.inputs["Base Color"])
    bump_from(nt, b, n, 0.8)
    return m


def mat_hout(name, tex, dark, light, scale=0.8, rand=0.0, stretch=(1, 1, 1), grijs=0.0, vuil=0.0, vuil_h=0.35):
    """Verweerd hout: Poly Haven-textuur via zijn helderheid naar de houtkleur; grijs = vergrijsd
    (zon en regen), vuil = donker onderaan (opspattende modder)."""
    m, nt, b = principled(name, 0.8)
    v = coords(nt, scale, rand_off=rand, stretch=stretch)
    t = image(nt, tex, "diff", v)
    rough = image(nt, tex, "rough", v)
    lum = bw(nt, t.outputs["Color"])
    oi = nt.nodes.new("ShaderNodeObjectInfo")
    f = math_node(nt, "ADD", math_node(nt, "MULTIPLY", lum, 2.6), math_node(nt, "MULTIPLY", oi.outputs["Random"], 0.25))
    r = ramp_node(nt, [(0.05, tuple(c * 0.4 for c in dark)), (0.35, dark), (0.75, light),
                       (1.1, tuple(min(1, c * 1.5) for c in light))])
    nt.links.new(math_node(nt, "SUBTRACT", f, 0.15), r.inputs["Fac"])
    c = r.outputs["Color"]
    if grijs:
        g = math_node(nt, "MULTIPLY", ruis(nt, v, 1.5, 3.0), grijs)
        c = mix_rgb(nt, klem(nt, g), c, mix_rgb(nt, 1.0, bw_rgb(nt, c), (0.85, 0.82, 0.78), "MULTIPLY"))
    if vuil:
        lo = klem(nt, math_node(nt, "MULTIPLY", math_node(nt, "SUBTRACT", vuil_h, hoogte_z(nt)), 1.0 / vuil_h * vuil))
        c = mix_rgb(nt, lo, c, mix_rgb(nt, 1.0, c, (0.35, 0.3, 0.25), "MULTIPLY"))
    nt.links.new(c, b.inputs["Base Color"])
    nt.links.new(math_node(nt, "MAXIMUM", rough.outputs["Color"], 0.7), b.inputs["Roughness"])
    bump_from(nt, b, math_node(nt, "ADD", lum, math_node(nt, "MULTIPLY", bw(nt, rough.outputs["Color"]), -0.5)), 1.0, 0.03)
    return m


def bw_rgb(nt, c):
    """Grijswaarde van een kleur als kleur."""
    g = bw(nt, c)
    cmb = nt.nodes.new("ShaderNodeCombineColor")
    for i in range(3):
        nt.links.new(g, cmb.inputs[i])
    return cmb.outputs[0]


def mat_pleister(name, basis=(0.78, 0.74, 0.64), vlekken=0.0, vlek_kleur=(0.03, 0.028, 0.026), vlek_schaal=1.1,
                 vuil=1.0):
    """Kalkpleister, verweerd: rock_surface als korrel, scheurtjes, vocht en modder onderaan,
    afgebladderde plekken. vlekken > 0: zwarte koeienvlekken (geschilderd, ook afgesleten)."""
    m, nt, b = principled(name, 0.92)
    v = coords(nt, 0.8)
    t = image(nt, "rock_surface", "diff", v)
    lum = bw(nt, t.outputs["Color"])
    korrel = ruis(nt, v, 25.0, 8.0, 0.7)
    tint = ramp_node(nt, [(0.0, tuple(c * 0.72 for c in basis)), (0.5, basis), (1.0, tuple(min(1, c * 1.1) for c in basis))])
    nt.links.new(math_node(nt, "ADD", math_node(nt, "MULTIPLY", lum, 1.4), -0.2), tint.inputs["Fac"])
    c = tint.outputs["Color"]
    if vlekken:
        vk = coords(nt, vlek_schaal, stretch=(1.0, 1.0, 0.75), rand_off=3.0)
        blob = ruis(nt, vk, 1.0, 2.0, 0.5, distort=0.45)
        rand = math_node(nt, "MULTIPLY", ruis(nt, vk, 9.0, 4.0), 0.12)
        vl = math_node(nt, "ADD", blob, rand)
        vl = klem(nt, math_node(nt, "MULTIPLY", math_node(nt, "SUBTRACT", vl, 0.62 - 0.1 * vlekken), 22.0))
        sleet = klem(nt, math_node(nt, "MULTIPLY", math_node(nt, "SUBTRACT", ruis(nt, v, 7.0, 8.0, 0.7), 0.56), 5.0))
        vl = math_node(nt, "MULTIPLY", vl, math_node(nt, "SUBTRACT", 1.0, math_node(nt, "MULTIPLY", sleet, 0.85)))
        verf = mix_rgb(nt, 0.25, vlek_kleur, mix_rgb(nt, 1.0, c, vlek_kleur, "MULTIPLY"))
        c = mix_rgb(nt, vl, c, verf)
        VERF = vl
    # haarscheuren: randen van een vervormd voronoi-patroon, alleen waar ruis het toelaat
    vr = nt.nodes.new("ShaderNodeTexVoronoi")
    vr.feature = "DISTANCE_TO_EDGE"
    vr.inputs["Scale"].default_value = 2.2
    nz3 = nt.nodes.new("ShaderNodeTexNoise")
    nz3.inputs["Scale"].default_value = 3.0
    nt.links.new(v, nz3.inputs["Vector"])
    vm = nt.nodes.new("ShaderNodeVectorMath")
    vm.operation = "SCALE"
    nt.links.new(nz3.outputs["Color"], vm.inputs[0])
    vm.inputs["Scale"].default_value = 0.35
    vrv = nt.nodes.new("ShaderNodeVectorMath")
    vrv.operation = "ADD"
    nt.links.new(v, vrv.inputs[0])
    nt.links.new(vm.outputs[0], vrv.inputs[1])
    nt.links.new(vrv.outputs[0], vr.inputs["Vector"])
    scheur = klem(nt, math_node(nt, "SUBTRACT", 1.0, math_node(nt, "MULTIPLY", vr.outputs["Distance"], 60.0)))
    scheur = math_node(nt, "MULTIPLY", scheur,
                       klem(nt, math_node(nt, "MULTIPLY", math_node(nt, "SUBTRACT", ruis(nt, v, 1.3, 2.0), 0.5), 6.0)))
    c = mix_rgb(nt, math_node(nt, "MULTIPLY", scheur, 0.8), c, (0.2, 0.17, 0.12))
    # afgebladderd: kale leem/steen eronder
    bl = klem(nt, math_node(nt, "MULTIPLY", math_node(nt, "SUBTRACT", ruis(nt, v, 2.2, 6.0, 0.65), 0.66), 9.0))
    c = mix_rgb(nt, bl, c, (0.42, 0.34, 0.24))
    # vocht en modder onderaan, strepen naar beneden
    if vuil:
        zv = hoogte_z(nt)
        streep = ruis(nt, coords(nt, 1.0, stretch=(6.0, 6.0, 0.4)), 1.0, 3.0)
        lo = klem(nt, math_node(nt, "MULTIPLY", math_node(nt, "SUBTRACT", math_node(nt, "ADD", 0.55, math_node(nt, "MULTIPLY", streep, 0.4)), zv), 1.6 * vuil))
        c = mix_rgb(nt, math_node(nt, "MULTIPLY", lo, 0.85), c, (0.25, 0.21, 0.15))
        c = mix_rgb(nt, math_node(nt, "MULTIPLY", holte(nt, 0.12), 0.8), c, (0.22, 0.2, 0.16))
    nt.links.new(c, b.inputs["Base Color"])
    h = math_node(nt, "ADD", math_node(nt, "MULTIPLY", lum, 0.6), math_node(nt, "MULTIPLY", korrel, 0.5))
    h = math_node(nt, "SUBTRACT", h, math_node(nt, "MULTIPLY", bl, 0.35))
    h = math_node(nt, "SUBTRACT", h, math_node(nt, "MULTIPLY", scheur, 0.25))
    if vlekken:
        h = math_node(nt, "ADD", h, math_node(nt, "MULTIPLY", VERF, 0.25))      # verf ligt er bovenop
    bump_from(nt, b, h, 0.7, 0.02)
    return m


def mat_pannen(name, tint=(0.36, 0.06, 0.42), schaal=1.2):
    """Gebakken dakpannen (clay_roof_tiles), paars gemaakt zoals de sprite, met mos en vuil."""
    m, nt, b = principled(name, 0.7)
    tc = nt.nodes.new("ShaderNodeTexCoord")
    mp = nt.nodes.new("ShaderNodeMapping")
    mp.inputs["Scale"].default_value = (schaal, schaal, 1)
    nt.links.new(tc.outputs["UV"], mp.inputs["Vector"])
    t = image(nt, "clay_roof_tiles", "diff", mp.outputs[0], box=False)
    nrm = image(nt, "clay_roof_tiles", "nor_gl", mp.outputs[0], box=False)
    rgh = image(nt, "clay_roof_tiles", "rough", mp.outputs[0], box=False)
    lum = bw(nt, t.outputs["Color"])
    r = ramp_node(nt, [(0.0, (0.02, 0.0, 0.03)), (0.35, tuple(c * 0.6 for c in tint)), (0.7, tint),
                       (1.0, tuple(min(1, c * 1.5) for c in tint))])
    nt.links.new(math_node(nt, "MULTIPLY", lum, 1.6), r.inputs["Fac"])
    c = r.outputs["Color"]
    mos = klem(nt, math_node(nt, "MULTIPLY", math_node(nt, "SUBTRACT", ruis(nt, None, 4.0, 6.0), 0.58), 4.0), 0.0, 0.6)
    c = mix_rgb(nt, mos, c, (0.16, 0.18, 0.07))
    nt.links.new(c, b.inputs["Base Color"])
    nt.links.new(rgh.outputs["Color"], b.inputs["Roughness"])
    nm = nt.nodes.new("ShaderNodeNormalMap")
    nm.inputs["Strength"].default_value = 1.4
    nt.links.new(nrm.outputs["Color"], nm.inputs["Color"])
    nt.links.new(nm.outputs["Normal"], b.inputs["Normal"])
    return m


def mat_verf(name, c, rough=0.6, sleet=0.5):
    """Geverfd (paarse rand): kleur met afgesleten plekken naar donker hout/steen."""
    m, nt, b = principled(name, rough)
    v = coords(nt, 2.0)
    s = klem(nt, math_node(nt, "MULTIPLY", math_node(nt, "SUBTRACT", ruis(nt, v, 3.0, 6.0), 0.6), 5.0 * sleet))
    k = mix_rgb(nt, s, c, (0.12, 0.1, 0.08))
    k = mix_rgb(nt, math_node(nt, "MULTIPLY", ruis(nt, v, 30.0, 4.0), 0.3), k, tuple(x * 0.6 for x in c))
    nt.links.new(k, b.inputs["Base Color"])
    bump_from(nt, b, ruis(nt, v, 40.0, 6.0), 0.3, 0.01)
    return m


def mat_flat(name, c, rough=0.8):
    m, nt, b = principled(name, rough)
    b.inputs["Base Color"].default_value = (*c, 1)
    return m


def mat_ijzer(name):
    m, nt, b = principled(name, 0.65)
    b.inputs["Metallic"].default_value = 0.8
    r = ramp_node(nt, [(0.35, (0.03, 0.028, 0.026)), (0.75, (0.18, 0.08, 0.03))])     # roest
    nt.links.new(ruis(nt, None, 30.0, 6.0), r.inputs["Fac"])
    nt.links.new(r.outputs["Color"], b.inputs["Base Color"])
    return m


def mat_gras(name, c=((0.01, 0.10, 0.01), (0.05, 0.36, 0.03), (0.22, 0.55, 0.08))):
    m, nt, b = principled(name, 0.5)
    tc = nt.nodes.new("ShaderNodeTexCoord")
    sep = nt.nodes.new("ShaderNodeSeparateXYZ")
    nt.links.new(tc.outputs["Generated"], sep.inputs[0])
    f = math_node(nt, "ADD", math_node(nt, "MULTIPLY", sep.outputs["Z"], 0.7),
                  math_node(nt, "MULTIPLY", ruis(nt, tc.outputs["Object"], 40.0), 0.5))
    r = ramp_node(nt, [(0.05, c[0]), (0.4, c[1]), (0.85, c[2])])
    nt.links.new(f, r.inputs["Fac"])
    nt.links.new(r.outputs["Color"], b.inputs["Base Color"])
    return m


def mat_grond(name, tex="farm_soil", tint=(1.0, 0.9, 0.75), schaal=0.7):
    m, nt, b = principled(name, 0.95)
    v = coords(nt, schaal)
    t = image(nt, tex, "diff", v, box=False)
    c = mix_rgb(nt, 1.0, t.outputs["Color"], tint, "MULTIPLY")
    nt.links.new(c, b.inputs["Base Color"])
    bump_from(nt, b, bw(nt, t.outputs["Color"]), 0.6)
    return m


def mat_huid(name, c=(0.80, 0.42, 0.36)):
    """Varkenshuid: roze met subsurface en modder onderaan."""
    m, nt, b = principled(name, 0.6)
    b.inputs["Subsurface Weight"].default_value = 0.25
    b.inputs["Subsurface Radius"].default_value = (0.3, 0.1, 0.08)
    lo = klem(nt, math_node(nt, "MULTIPLY", math_node(nt, "SUBTRACT", 0.25, hoogte_z(nt)), 6.0))
    k = mix_rgb(nt, math_node(nt, "MULTIPLY", ruis(nt, None, 8.0, 4.0), 0.25), c, tuple(x * 0.8 for x in c))
    k = mix_rgb(nt, lo, k, (0.2, 0.14, 0.08))
    nt.links.new(k, b.inputs["Base Color"])
    return m


# --- Geometrie ----------------------------------------------------------------------
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
    col().objects.link(ob)
    return put(ob, mat, smooth)


def box(name, loc, size, mat, rot=(0, 0, 0), bevel=0.0, jitter=0.0):
    """Balk; schaal toegepast (textuur in meters). jitter: hoeken iets scheef (handwerk)."""
    bpy.ops.mesh.primitive_cube_add(size=1, location=loc, rotation=rot if not isinstance(rot, (int, float)) else (0, 0, rot))
    o = bpy.context.object
    o.name = name
    o.scale = size
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    if jitter:
        for vv in o.data.vertices:
            vv.co += Vector((random.uniform(-jitter, jitter) for _ in range(3)))
    if bevel:
        m = o.modifiers.new("b", "BEVEL")
        m.width, m.segments = bevel, 2
        m.limit_method = "NONE"
    return put(o, mat, smooth=False)


def balk(name, p, q, dik, mat, bevel=0.012, rol=0.0):
    """Balk van p naar q (vierkante doorsnede dik of (b, h)), voor stijlen en schoren."""
    p, q = Vector(p), Vector(q)
    d = q - p
    b, h = (dik, dik) if isinstance(dik, (int, float)) else dik
    o = box(name, (p + q) / 2, (b, h, d.length), mat, bevel=bevel, jitter=0.004)
    rotq = Vector((0, 0, 1)).rotation_difference(d.normalized())
    o.rotation_mode = "QUATERNION"
    o.rotation_quaternion = rotq @ Matrix.Rotation(rol, 4, "Z").to_quaternion()
    return o


def cyl(name, loc, r, depth, mat, rot=(0, 0, 0), verts=16):
    bpy.ops.mesh.primitive_cylinder_add(vertices=verts, radius=r, depth=depth, location=loc, rotation=rot)
    o = bpy.context.object
    o.name = name
    return put(o, mat)


def bol(name, loc, r, mat, schaal=(1, 1, 1), sub=3):
    bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=sub, radius=r, location=loc)
    o = bpy.context.object
    o.name = name
    o.scale = schaal
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    return put(o, mat)


def stone_mesh(name, seed, p=6.0, bumps=0.15, cuts=5, sub=3, hf=0.06):
    """Onregelmatige steen in een eenheidskubus (uit peasant_hut.py)."""
    rnd = random.Random(seed)
    bm = bmesh.new()
    bmesh.ops.create_icosphere(bm, subdivisions=sub, radius=1.0)
    off = Vector((rnd.uniform(-50, 50), rnd.uniform(-50, 50), rnd.uniform(-50, 50)))
    planes = [(Vector((rnd.gauss(0, 1), rnd.gauss(0, 1), rnd.gauss(0, 0.4))).normalized(), rnd.uniform(0.72, 0.92))
              for _ in range(cuts)]
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


class Stenen:
    """Gedeelde steenmeshes; elke steen een eigen object (tint per steen via Object Info)."""

    def __init__(self, mat, n=10, seed=100, **kw):
        self.meshes = [stone_mesh(f"steen{seed + k}", seed + k, **kw) for k in range(n)]
        for me in self.meshes:
            me.materials.append(mat)
        self.uit = []

    def zet(self, loc, size, rot_z=0.0, tilt=(0.0, 0.0), mat=None):
        ob = bpy.data.objects.new("steen", random.choice(self.meshes))
        ob.location = loc
        ob.rotation_euler = (tilt[0], tilt[1], rot_z)
        ob.scale = (size[0] / 2, size[1] / 2, size[2] / 2)
        col().objects.link(ob)
        if mat is not None:
            ob.material_slots[0].link = "OBJECT"
            ob.material_slots[0].material = mat
        self.uit.append(ob)
        return ob

    def muur(self, p0, p1, z0, z1, dik, hs=(0.1, 0.2), ls=(0.18, 0.4), mat=None, inspring=0.0):
        """Droog gestapelde muur van p0 naar p1 (grondpunten), lagen met halfsteens verband."""
        p0, p1 = Vector((*p0, 0)), Vector((*p1, 0))
        d = p1 - p0
        L = d.length
        d.normalize()
        nrm = Vector((-d.y, d.x, 0))
        rz = math.atan2(d.y, d.x)
        z = z0
        rij = 0
        while z < z1 - 0.03:
            h = min(random.uniform(*hs), z1 - z)
            s = -random.uniform(0, ls[1]) * (rij % 2) * 0.5
            while s < L:
                l = random.uniform(*ls)
                a, e = max(s, 0.0), min(s + l, L)
                if e - a > 0.05:
                    m = (a + e) / 2
                    pos = p0 + d * m + nrm * random.uniform(-0.015, 0.015) + Vector((0, 0, z + h / 2))
                    self.zet(pos, ((e - a) * 1.08, dik * random.uniform(0.85, 1.05), h * 1.12),
                             rz + random.uniform(-0.04, 0.04), (random.uniform(-0.04, 0.04), random.uniform(-0.04, 0.04)), mat)
                s += l
            z += h
            rij += 1


def tube(name, pts, r, mat, sides=6, closed=False):
    n = len(pts)
    verts, faces = [], []
    for i, p in enumerate(pts):
        a = pts[min(i + 1, n - 1)]
        b = pts[max(i - 1, 0)]
        t = (Vector(a) - Vector(b)).normalized()
        u = t.cross(Vector((0, 0, 1)))
        if u.length < 1e-3:
            u = t.cross(Vector((1, 0, 0)))
        u.normalize()
        w = t.cross(u)
        rr = r(i / (n - 1)) if callable(r) else r
        for k in range(sides):
            th = 2 * math.pi * k / sides
            verts.append(tuple(Vector(p) + (u * math.cos(th) + w * math.sin(th)) * rr))
    for i in range(n - 1):
        for k in range(sides):
            k2 = (k + 1) % sides
            faces.append([i * sides + k, i * sides + k2, (i + 1) * sides + k2, (i + 1) * sides + k])
    return mesh_obj(name, verts, faces, mat)


def grasbos(name, x, y, mat, n=14, hgt=0.5, seed=0):
    """Waaier van sprieten (V/W) zoals de sprite."""
    rnd = random.Random(seed)
    RV = Vector((0.707, -0.707, 0))
    FV = Vector((-0.707, -0.707, 0))
    vs, fs = [], []
    for lean, hg0, fwd in ((-0.42, 1.0, 0.05), (0.05, 0.6, 0.12), (0.45, 0.9, 0.0)):
        for _ in range(n):
            le = lean * rnd.uniform(0.6, 1.2) + rnd.uniform(-0.08, 0.08)
            hg = hgt * hg0 * rnd.uniform(0.6, 1.05)
            fw = fwd + rnd.uniform(-0.1, 0.1)
            base = Vector((x, y, 0)) + RV * rnd.uniform(-0.05, 0.05) + FV * rnd.uniform(-0.04, 0.04)
            wd = rnd.uniform(0.018, 0.03)
            k0 = len(vs)
            for k in range(7):
                t = k / 6
                w = wd * (1 - t) ** 0.8 + 0.002
                c = base + RV * (le * t ** 1.6) + FV * (fw * t) + Vector((0, 0, hg * t - 0.06 * abs(le) * t ** 3))
                side = (RV * 0.7 + FV * 0.3).normalized() * w * 0.5
                vs += [tuple(c - side), tuple(c + side)]
            fs += [[k0 + 2 * k, k0 + 2 * k + 1, k0 + 2 * k + 3, k0 + 2 * k + 2] for k in range(6)]
    o = mesh_obj(name, vs, fs, mat)
    return o


# --- Riet als halmen -------------------------------------------------------------------
def strands(name, curves, mat, bos, rad):
    cv = bpy.data.hair_curves.new(name)
    cv.add_curves([len(c) for c in curves])
    cv.position_data.foreach_set("vector", [q for c in curves for p in c for q in p])
    ra = cv.attributes.new("radius", "FLOAT", "POINT")
    ra.data.foreach_set("value", [rad(i / (len(c) - 1)) for c in curves for i in range(len(c))])
    ba = cv.attributes.new("bos", "FLOAT", "CURVE")
    ba.data.foreach_set("value", bos)
    cv.materials.append(mat)
    ob = bpy.data.objects.new(name, cv)
    col().objects.link(ob)
    ob["rt"] = "halm"
    return ob


HALM_RAD = lambda u: 0.0062 - 0.0018 * u


class Dakvlak:
    """Rietdak als parametrisch vlak: P(u, s) met u langs de nok (m) en s de booglengte over het
    profiel (0 = nok, + en - de twee kanten op). prof: [(x, z)] van rand tot rand over de nok."""

    def __init__(self, prof, u0, u1, as_x=True, oorsprong=(0, 0)):
        self.u0, self.u1 = u0, u1
        self.ox, self.oy = oorsprong
        self.as_x = as_x                     # True: nok langs wereld-Y, profiel in X
        pts = [Vector(p) for p in prof]
        L = [0.0]
        for a, b in zip(pts, pts[1:]):
            L.append(L[-1] + (b - a).length)
        top = max(range(len(pts)), key=lambda i: pts[i].y)
        self.pts, self.L, self.stop = pts, L, L[top]
        self.smin, self.smax = -L[top], L[-1] - L[top]

    def prof(self, s):
        """(x, z) en buitennormaal (nx, nz) op booglengte s."""
        t = min(max(s + self.stop, 0.0), self.L[-1])
        for i in range(len(self.L) - 1):
            if t <= self.L[i + 1] or i == len(self.L) - 2:
                a, b = self.pts[i], self.pts[i + 1]
                f = (t - self.L[i]) / max(self.L[i + 1] - self.L[i], 1e-9)
                p = a.lerp(b, min(max(f, 0), 1))
                tg = (b - a).normalized()
                ex = s + self.stop - t                     # voorbij de rand: rechtdoor
                p = p + tg * ex
                return p, Vector((-tg.y, tg.x))
        return self.pts[-1], Vector((0, 1))

    def P(self, u, s, off=0.0):
        p, n = self.prof(s)
        q = p + n * off
        if self.as_x:
            return Vector((self.ox + q.x, self.oy + u, q.y))
        return Vector((self.ox + u, self.oy + q.x, q.y))

    def N(self, s):
        _, n = self.prof(s)
        return Vector((n.x, 0, n.y)) if self.as_x else Vector((0, n.x, n.y))

    def U(self):
        return Vector((0, 1, 0)) if self.as_x else Vector((1, 0, 0))

    def schil(self, name, mat, dik=0.25, du=0.1, ds=0.08, rand_dik=0.35, rafel=0.0, seed=1):
        """Gesloten dakschil: boven het vlak, onder op -dik (dikker naar de rand), met kopse kanten.
        UV in meters (u, s). rafel: onderrand per kolom willekeurig korter/langer (m)."""
        rnd = random.Random(seed)
        nu = max(2, int((self.u1 - self.u0) / du) + 1)
        ns = max(2, int((self.smax - self.smin) / ds) + 1)
        us = [self.u0 + (self.u1 - self.u0) * i / (nu - 1) for i in range(nu)]
        ss = [self.smin + (self.smax - self.smin) * j / (ns - 1) for j in range(ns)]
        verts, faces, uvs = [], [], []

        def d_at(s):
            f = abs(s) / max(abs(self.smin), self.smax)
            return dik * (1 - f) + rand_dik * f

        def idx(i, j, k):
            return (k * ns + j) * nu + i
        for k in (0, 1):
            for j, s in enumerate(ss):
                for i, u in enumerate(us):
                    ex = 0.0
                    if rafel and j in (0, ns - 1):
                        ex = rnd.uniform(-0.3, 1.0) * rafel
                    s2 = s + (ex if s > 0 else -ex)
                    verts.append(tuple(self.P(u, s2, 0.0 if k == 0 else -d_at(s))))
                    uvs.append((u, s))
        for j in range(ns - 1):
            for i in range(nu - 1):
                a, b, c, d = idx(i, j, 0), idx(i + 1, j, 0), idx(i + 1, j + 1, 0), idx(i, j + 1, 0)
                faces.append([a, b, c, d])
                faces.append([idx(i, j, 1), idx(i, j + 1, 1), idx(i + 1, j + 1, 1), idx(i + 1, j, 1)])
        for j in range(ns - 1):                         # kopse kanten langs u0 en u1
            faces.append([idx(0, j, 0), idx(0, j + 1, 0), idx(0, j + 1, 1), idx(0, j, 1)])
            faces.append([idx(nu - 1, j, 0), idx(nu - 1, j, 1), idx(nu - 1, j + 1, 1), idx(nu - 1, j + 1, 0)])
        for i in range(nu - 1):                         # onderranden
            faces.append([idx(i, 0, 0), idx(i, 0, 1), idx(i + 1, 0, 1), idx(i + 1, 0, 0)])
            faces.append([idx(i, ns - 1, 0), idx(i + 1, ns - 1, 0), idx(i + 1, ns - 1, 1), idx(i, ns - 1, 1)])
        o = mesh_obj(name, verts, faces, mat)
        uvl = o.data.uv_layers.new(name="UVMap")
        for poly in o.data.polygons:
            for li in poly.loop_indices:
                uvl.data[li].uv = uvs[o.data.loops[li].vertex_index]
        o["rt"] = "riet"
        return o

    def halmen(self, name, mat, rnd, skip=None, bos_d=0.065, per_bos=14, laag=(0.26, 0.34), lengte=(0.72, 0.9),
               hang=0.12, kant=(1, -1), dik=0.075, bult=0.0, rad=None, rommel=0.0):
        """bult: lage ruis (m) op de laagdikte, zodat het dak golft en zakt; rommel: kans dat een
        halm schuin uit de laag steekt (ruig riet)."""
        """Lagen halmen van de nok naar de rand, beide kanten; rafelige onderrand."""
        curves, bos = [], []
        nb = int((self.u1 - self.u0) / bos_d)
        for sg in kant:
            send = self.smax if sg > 0 else -self.smin
            s0 = 0.05
            while s0 < send - 0.05:
                L = rnd.uniform(*lengte)
                for b in range(nb):
                    ub = self.u0 + 0.03 + (self.u1 - self.u0 - 0.06) * (b + rnd.uniform(0, 1)) / nb
                    bv = rnd.random()
                    if skip and skip(ub, sg * (s0 + L * 0.6)):
                        continue
                    for _ in range(per_bos):
                        ui = ub + rnd.gauss(0, bos_d * 0.35)
                        si = s0 + rnd.uniform(-0.04, 0.04)
                        se = si + L * rnd.uniform(0.9, 1.05)
                        hg = 0.0
                        if se > send:
                            hg = rnd.uniform(0.0, hang) * rnd.random() ** 0.5
                            se = send
                        lift = rnd.uniform(0.0, 0.015)
                        wild = rnd.uniform(0.02, 0.09) if rnd.random() < rommel else 0.0
                        dwars = rnd.gauss(0, 0.03) if wild else 0.0
                        pts = []
                        for k in range(8):
                            f = k / 7
                            s = si + (se - si) * f
                            ug = ui + (ub - ui) * 0.3 * f + dwars * f * f
                            bl = bult * noise.noise(Vector((ug * 0.9, sg * s * 0.9 + sg * 7.0, 3.3))) if bult else 0.0
                            off = -0.025 + lift + dik * f ** 0.9 + bl + wild * f * f
                            pts.append(tuple(self.P(ug, sg * s, off)))
                        if hg:
                            p6, p7 = Vector(pts[-2]), Vector(pts[-1])
                            d = (p7 - p6).normalized()
                            pts.append(tuple(p7 + d * hg * 0.5 + Vector((0, 0, -0.1 * hg))))
                            pts.append(tuple(p7 + d * hg + Vector((0, 0, -0.3 * hg))))
                        else:
                            d = Vector(pts[-1]) - Vector(pts[-2])
                            pts += [tuple(Vector(pts[-1]) + d * 0.01), tuple(Vector(pts[-1]) + d * 0.02)]
                        curves.append(pts)
                        bos.append(bv)
                s0 += rnd.uniform(*laag)
        return strands(name, curves, mat, bos, rad or HALM_RAD)

    def nokrol(self, name, mat, rnd, breed=0.45, per_m=900, hoog=0.06, skip=None, rad=None):
        """Nokbedekking: halmen dwars over de nok gevouwen."""
        curves, bos = [], []
        n = int((self.u1 - self.u0) * per_m)
        for _ in range(n):
            u = rnd.uniform(self.u0 + 0.02, self.u1 - 0.02)
            if skip and skip(u, 0.0):
                continue
            a, b = -breed * rnd.uniform(0.8, 1.1), breed * rnd.uniform(0.8, 1.1)
            pts = []
            for k in range(9):
                f = k / 8
                s = a + (b - a) * f
                off = 0.07 + hoog * (1 - (2 * f - 1) ** 2) + rnd.uniform(0, 0.01)
                pts.append(tuple(self.P(u + rnd.gauss(0, 0.004), s, off)))
            curves.append(pts)
            bos.append(0.5 + 0.4 * rnd.random())
        return strands(name, curves, mat, bos, rad or HALM_RAD)

    def gevelrol(self, name, mat, rnd, u_rand, richting, r=0.13, per_m=700, uit=0.04, rad=None):
        """Rol riet langs de gevelrand (u = u_rand): halmen langs het profiel op een buis eromheen,
        richting = -1 / +1: de kant waar de rol over de rand hangt."""
        curves, bos = [], []
        Lb = self.smax - self.smin
        n = int(Lb * per_m)
        for _ in range(n):
            th = rnd.uniform(-0.3, math.pi * 0.85)
            rr = r * math.sqrt(rnd.uniform(0.5, 1.0))
            s0 = rnd.uniform(self.smin - 0.1, self.smax - 0.6)
            Lh = rnd.uniform(0.5, 0.8)
            pts = []
            for k in range(8):
                f = k / 7
                s = min(s0 + Lh * f, self.smax + 0.08)
                p = self.P(u_rand, s, 0.0)
                nrm = self.N(s)
                q = p + self.U() * (richting * (uit + rr * math.sin(th))) + nrm * (rr * math.cos(th) - 0.02)
                pts.append(tuple(q))
            curves.append(pts)
            bos.append(0.2 + 0.7 * rnd.random())
        return strands(name, curves, mat, bos, rad or HALM_RAD)


class Heup(Dakvlak):
    """Afgewolfd (rond) dakeinde: de +s-helft van het profiel om een verticale as gedraaid.
    u = booglengte langs de dakrand (m) van de +X-kant (u = 0) via +Y naar de -X-kant (u = pi R);
    k < 1 drukt de heup in de lengte (y) in. Sluit aan op een Dakvlak dat bij y = yh eindigt."""

    def __init__(self, prof, yh, k=1.0, ox=0.0, richting=1, vierkant=2.0):
        super().__init__(prof, 0.0, 1.0)
        self.R = max(p.x for p in self.pts)
        self.u0, self.u1 = 0.0, math.pi * self.R
        self.smin = 0.0
        self.yh, self.k, self.hx, self.rich = yh, k, ox, richting
        self.n = vierkant                  # superellips in plan: 2 = ellips, hoger = vierkanter (dekt de hoeken)

    def P(self, u, s, off=0.0):
        p, n = self.prof(max(s, 0.0))
        r = max(p.x + n.x * off, 0.0)
        z = p.y + n.y * off
        a = u / self.R
        c, sn = math.cos(a), math.sin(a)
        c = math.copysign(abs(c) ** (2 / self.n), c)
        sn = abs(sn) ** (2 / self.n)
        return Vector((self.hx + r * c, self.yh + self.rich * self.k * r * sn, z))


# --- Deuren en ankers -------------------------------------------------------------------
def anker(name, loc):
    e = bpy.data.objects.new(name, None)
    e.empty_display_type = "PLAIN_AXES"
    e.empty_display_size = 0.2
    e.location = loc
    col().objects.link(e)
    return e


def scharnier(name, delen, T):
    """Leeg object op de scharnieras (matrix T: lokaal z omhoog, x naar buiten, y langs de deur)
    met de deurdelen als kinderen. Open naar buiten = rotation_euler.z - hoek (zie zet_deur)."""
    e = bpy.data.objects.new(name, None)
    e.empty_display_type = "SINGLE_ARROW"
    col().objects.link(e)
    e.matrix_world = T
    for d in delen:
        d.parent = e
        d.matrix_parent_inverse = T.inverted()
    e["dicht"] = e.rotation_euler.z
    return e


def zet_deur(e, graden):
    """Open naar buiten = positieve graden (zoals de hut: dicht - hoek om lokaal Z)."""
    e.rotation_euler.z = e["dicht"] - math.radians(graden)


# --- Camera, licht, render ----------------------------------------------------------------
def camera(scene, res, schaal, ref_wereld, ref_px, yaw=225.0, pitch=30.0):
    """Orthografische iso-camera op de sprite: res = (b, h) op 1x, ref_wereld komt op pixel ref_px
    (1x, vanaf linksboven)."""
    W, H = res
    cam_d = bpy.data.cameras.new("cam")
    cam_d.type = "ORTHO"
    cam_d.ortho_scale = W / PX_PER_M
    cam = bpy.data.objects.new("cam", cam_d)
    col().objects.link(cam)
    yw, pt = math.radians(yaw), math.radians(pitch)
    dirv = Vector((math.cos(yw) * math.cos(pt), math.sin(yw) * math.cos(pt), math.sin(pt)))
    rot = (-dirv).to_track_quat("-Z", "Y")
    R = rot.to_matrix()
    right, up = R.col[0], R.col[1]
    P = Vector(ref_wereld)
    target = P - right * (ref_px[0] - W / 2) / PX_PER_M - up * (H / 2 - ref_px[1]) / PX_PER_M
    cam.location = target + dirv * 40
    cam.rotation_euler = rot.to_euler()
    cam_d.clip_end = 100
    scene.camera = cam
    scene.render.resolution_x = int(W * schaal)
    scene.render.resolution_y = int(H * schaal)
    return cam


def sun(name, energy, rot, color=(1, 1, 1), shadow=True, angle=2.0):
    d = bpy.data.lights.new(name, "SUN")
    d.energy, d.color, d.angle, d.use_shadow = energy, color, math.radians(angle), shadow
    o = bpy.data.objects.new(name, d)
    col().objects.link(o)
    o.rotation_euler = rot
    return o


def link_coll(name, objs, state="INCLUDE"):
    c = bpy.data.collections.new(name)
    for o in objs:
        c.objects.link(o)
        c.collection_objects[len(c.objects) - 1].light_linking.link_state = state
    return c


ZON_ROT = (math.radians(26), 0, math.radians(61))       # zoals de hut: van rechtsachter, schaduw links
WARM = (1.0, 0.9, 0.75)


def licht(scene, dak=(), zon_e=1.9, vul_e=2.2, hdri=0.45):
    """Licht als de hut: zon (schaduw op de grond alleen van de muren, niet van het dak),
    vullicht linksvoor, HDRI. Geeft de schaduwvanger terug."""
    bpy.ops.mesh.primitive_plane_add(size=40, location=(0, 0, 0))
    vanger = bpy.context.object
    vanger.name = "vanger"
    vanger.is_shadow_catcher = True
    vanger["rt"] = "weg"
    zon = sun("zon", zon_e, ZON_ROT, WARM)
    zon.light_linking.receiver_collection = link_coll("niet_vanger", [vanger], "EXCLUDE")
    zon2 = sun("zon_grond", zon_e, ZON_ROT, WARM)
    zon2.light_linking.receiver_collection = link_coll("alleen_vanger", [vanger])
    zon2.light_linking.blocker_collection = link_coll(
        "werpers", [o for o in scene.objects if o.type == "MESH" and o not in dak and o is not vanger])
    vul = sun("vul", vul_e, (math.radians(55), 0, math.radians(-115)), (0.95, 0.95, 1.0), angle=25.0)
    vul.light_linking.receiver_collection = bpy.data.collections["niet_vanger"]
    vul2 = sun("vul_grond", vul_e, (math.radians(55), 0, math.radians(-115)), (0.95, 0.95, 1.0), shadow=False)
    vul2.light_linking.receiver_collection = bpy.data.collections["alleen_vanger"]
    world = bpy.data.worlds.new("w")
    world.use_nodes = True
    wn = world.node_tree
    bg = wn.nodes["Background"]
    env = wn.nodes.new("ShaderNodeTexEnvironment")
    env.image = bpy.data.images.load(os.path.join(TEX, "qwantani_late_afternoon_1k.hdr"))
    wn.links.new(mix_rgb(wn, 1.0, env.outputs["Color"], (1.2, 1.2, 1.2), "DARKEN"), bg.inputs["Color"])
    bg.inputs["Strength"].default_value = hdri
    scene.world = world
    return vanger


def gpu(scene):
    p = bpy.context.preferences.addons["cycles"].preferences
    try:
        p.compute_device_type = "CUDA"              # OptiX faalt op deze driver
    except TypeError:
        return "CPU"
    p.get_devices()
    for d in p.devices:
        d.use = d.type == "CUDA"
    scene.cycles.device = "GPU"
    return "CUDA"


def render(scene, pad, samples=128):
    scene.render.engine = "CYCLES"
    gpu(scene)
    scene.cycles.samples = samples
    scene.cycles.use_denoising = True
    scene.cycles.max_bounces = 6
    scene.render.film_transparent = True
    scene.view_settings.view_transform = "Standard"
    scene.render.image_settings.color_mode = "RGBA"
    scene.render.filepath = pad
    t = time.time()
    bpy.ops.render.render(write_still=True)
    log("render", os.path.basename(pad), f"{time.time() - t:.0f}s")


def tel(objs=None):
    """Driehoeken (meshes) en halmen (curves) in de scene."""
    dg = bpy.context.evaluated_depsgraph_get()
    tri, halm = 0, 0
    for o in objs or bpy.context.scene.objects:
        if o.type == "MESH" and o.get("rt") != "weg":
            me = o.evaluated_get(dg).to_mesh()
            me.calc_loop_triangles()
            tri += len(me.loop_triangles)
            o.evaluated_get(dg).to_mesh_clear()
        elif o.type == "CURVES":
            halm += len(o.data.curves)
    return tri, halm


# ============================================================================================
# --- Real-time bake: hoge versie (de .blend van het bouwscript) -> glb LOD0 + LOD1 ----------
# ============================================================================================
def ontkies():
    for o in bpy.context.selected_objects:
        o.select_set(False)


def eval_mesh(ob, name=None):
    dg = bpy.context.evaluated_depsgraph_get()
    me = bpy.data.meshes.new_from_object(ob.evaluated_get(dg), preserve_all_data_layers=False, depsgraph=dg)
    me.transform(ob.matrix_world)
    me.name = name or ob.name + "_rt"
    return me


def samen(name, meshes, coll):
    bm = bmesh.new()
    for me in meshes:
        bm.from_mesh(me)
    out = bpy.data.meshes.new(name)
    bm.to_mesh(out)
    bm.free()
    o = bpy.data.objects.new(name, out)
    coll.objects.link(o)
    return o


def decimeer_obj(o, ratio):
    if ratio >= 1.0:
        return
    m = o.modifiers.new("d", "DECIMATE")
    m.ratio = ratio
    m.use_collapse_triangulate = True
    dg = bpy.context.evaluated_depsgraph_get()
    me = bpy.data.meshes.new_from_object(o.evaluated_get(dg), depsgraph=dg)
    o.modifiers.clear()
    old = o.data
    o.data = me
    bpy.data.meshes.remove(old)


def halm_buizen(ob, coll, sides=3):
    """Hair curves -> buisjes (mesh), als bakbron: een mesh-object met geometry nodes dat de curves
    via Object Info binnenhaalt (Curve to Mesh, straal = halmstraal)."""
    ng = bpy.data.node_groups.new("_buis", "GeometryNodeTree")
    ng.interface.new_socket("Geometry", in_out="INPUT", socket_type="NodeSocketGeometry")
    ng.interface.new_socket("Geometry", in_out="OUTPUT", socket_type="NodeSocketGeometry")
    go = ng.nodes.new("NodeGroupOutput")
    oi = ng.nodes.new("GeometryNodeObjectInfo")
    oi.transform_space = "RELATIVE"
    oi.inputs["Object"].default_value = ob
    c2m = ng.nodes.new("GeometryNodeCurveToMesh")
    circ = ng.nodes.new("GeometryNodeCurvePrimitiveCircle")
    circ.inputs["Resolution"].default_value = sides
    circ.inputs["Radius"].default_value = 1.0
    poly = ng.nodes.new("GeometryNodeCurveSplineType")      # catmull-rom -> poly: 10x minder vlakken
    poly.spline_type = "POLY"
    ng.links.new(oi.outputs["Geometry"], poly.inputs["Curve"])
    ng.links.new(poly.outputs["Curve"], c2m.inputs["Curve"])
    ng.links.new(circ.outputs["Curve"], c2m.inputs["Profile Curve"])
    if "Scale" in c2m.inputs:
        rad = ng.nodes.new("GeometryNodeInputRadius")
        ng.links.new(rad.outputs[0], c2m.inputs["Scale"])
    # Hair Info (Random, Intercept) bestaat niet op een mesh: als attributen hrand/hint meegeven (zoals de hut,
    # peasant_hut_realtime.mat_attr), anders bakt elke halm in dezelfde donkere kleur (2026-10-30)
    sp = ng.nodes.new("GeometryNodeSplineParameter")
    st_hint = ng.nodes.new("GeometryNodeStoreNamedAttribute")
    st_hint.data_type = "FLOAT"
    st_hint.domain = "POINT"
    st_hint.inputs["Name"].default_value = "hint"
    ng.links.new(poly.outputs["Curve"], st_hint.inputs["Geometry"])
    ng.links.new(sp.outputs["Factor"], st_hint.inputs["Value"])
    rv = ng.nodes.new("FunctionNodeRandomValue")
    rv.data_type = "FLOAT"
    rv.inputs["Seed"].default_value = 7
    st_rand = ng.nodes.new("GeometryNodeStoreNamedAttribute")
    st_rand.data_type = "FLOAT"
    st_rand.domain = "CURVE"
    st_rand.inputs["Name"].default_value = "hrand"
    ng.links.new(st_hint.outputs["Geometry"], st_rand.inputs["Geometry"])
    ng.links.new(rv.outputs[0], st_rand.inputs["Value"])
    ng.links.new(st_rand.outputs["Geometry"], c2m.inputs["Curve"])
    ng.links.new(c2m.outputs[0], go.inputs[0])
    k = bpy.data.objects.new("_buis", bpy.data.meshes.new("_buis"))
    coll.objects.link(k)
    md = k.modifiers.new("buis", "NODES")
    md.node_group = ng
    me = eval_mesh(k, ob.name + "_buis")
    bpy.data.objects.remove(k)
    o = bpy.data.objects.new(ob.name + "_buis", me)
    coll.objects.link(o)
    o.data.materials.clear()
    o.data.materials.append(mat_attr(ob.data.materials[0]))
    o.data.polygons.foreach_set("material_index", [0] * len(o.data.polygons))
    log("  buizen", ob.name, len(me.polygons))
    return o


def mat_attr(src):
    """Halmmateriaal voor een mesh: Hair Info (Random, Intercept) -> attributen hrand, hint."""
    naam = src.name + "_buis"
    if naam in bpy.data.materials:
        return bpy.data.materials[naam]
    m = src.copy()
    m.name = naam
    nt = m.node_tree
    for hi in [n for n in nt.nodes if n.type == "HAIR_INFO"]:
        for out, an in (("Random", "hrand"), ("Intercept", "hint")):
            a = nt.nodes.new("ShaderNodeAttribute")
            a.attribute_name = an
            for l in list(hi.outputs[out].links):
                nt.links.new(a.outputs["Fac"], l.to_socket)
        nt.nodes.remove(hi)
    return m


# bakbron voor de rietschil zelf: egaal stro, iets donkerder dan de halmen (diepte), zodat stralen die tussen de
# halmen door de schil raken geen bruine Poly Haven-onderlaag bakken (2026-10-30: dak bruin met gele strepen)
RIET_VUL = (0.50, 0.33, 0.09, 1)


def riet_vul_bron(o, coll):
    m = bpy.data.materials.get("_riet_vul")
    if m is None:
        m, nt, b = principled("_riet_vul", 0.85)
        b.inputs["Base Color"].default_value = RIET_VUL
    k = bpy.data.objects.new(o.name + "_vul", eval_mesh(o, o.name + "_vul"))
    k.data.materials.clear()
    k.data.materials.append(m)
    k.data.polygons.foreach_set("material_index", [0] * len(k.data.polygons))
    coll.objects.link(k)
    return k


def uv_atlas(objs, marge=0.002, gewicht=None):
    gewicht = gewicht or {}
    for o in objs:
        while o.data.uv_layers:
            o.data.uv_layers.remove(o.data.uv_layers[0])
        o.data.uv_layers.new(name="UVMap")
    ontkies()
    for o in objs:
        o.select_set(True)
    bpy.context.view_layer.objects.active = objs[0]
    bpy.context.scene.tool_settings.use_uv_select_sync = True
    bpy.ops.object.mode_set(mode="EDIT")
    bpy.ops.mesh.select_all(action="SELECT")
    log("  uv: smart project", [o.name for o in objs])
    # smart project pakt zelf (met marge); pack_islands hangt hier op duizenden eilandjes (2026-10-29)
    bpy.ops.uv.smart_project(angle_limit=math.radians(55), island_margin=marge, area_weight=0.0,
                             correct_aspect=True, scale_to_bounds=False)
    bpy.ops.object.mode_set(mode="OBJECT")
    log("  uv klaar")


BAKSOORT = {"kleur": ("DIFFUSE", {"COLOR"}, 8), "ruwheid": ("ROUGHNESS", set(), 4),
            "normaal": ("NORMAL", set(), 8), "ao": ("AO", set(), 48), "emissie": ("EMIT", set(), 4)}


def bak(lows, highs, beelden, ext, ray, coll):
    """highs -> tijdelijke samengevoegde kopie van lows (zelfde UV). Veel bronobjecten maken
    selected-to-active traag (CPU, per object per pixel): dan eerst samenvoegen tot een bron
    (de tint per steen via Object Info gaat dan verloren)."""
    sc = bpy.context.scene
    tijdelijk = None
    if len(highs) > 12:
        kh = []
        for h in highs:
            k = bpy.data.objects.new("_bron", eval_mesh(h, "_bron"))
            coll.objects.link(k)
            kh.append(k)
        ontkies()
        for k in kh:
            k.select_set(True)
        bpy.context.view_layer.objects.active = kh[0]
        bpy.ops.object.join()
        tijdelijk = bpy.context.view_layer.objects.active
        for h in highs:
            h.hide_render = True
        highs = [tijdelijk]
    kop = []
    for o in lows:
        k = o.copy()
        k.data = o.data.copy()
        coll.objects.link(k)
        kop.append(k)
    ontkies()
    for k in kop:
        k.select_set(True)
    bpy.context.view_layer.objects.active = kop[0]
    if len(kop) > 1:
        bpy.ops.object.join()
    doel = bpy.context.view_layer.objects.active
    m = bpy.data.materials.new("_bak")
    m.use_nodes = True
    tn = m.node_tree.nodes.new("ShaderNodeTexImage")
    m.node_tree.nodes.active = tn
    doel.data.materials.clear()
    doel.data.materials.append(m)
    doel.data.polygons.foreach_set("material_index", np.zeros(len(doel.data.polygons), np.int32))
    for v in ("visible_diffuse", "visible_glossy", "visible_shadow", "visible_transmission", "visible_volume_scatter"):
        setattr(doel, v, False)
    verborgen = [o for o in sc.objects if o is not doel and o not in highs and not o.hide_render
                 and o.type in ("MESH", "CURVES")]
    for o in verborgen:
        o.hide_render = True
    for h in highs:
        h.hide_render = False
    ontkies()
    for h in highs:
        h.select_set(True)
    doel.select_set(True)
    bpy.context.view_layer.objects.active = doel
    for soort, img in beelden:
        t, pf, spp = BAKSOORT[soort]
        sc.cycles.samples = spp
        tn.image = img
        t1 = time.time()
        kw = dict(type=t, use_selected_to_active=True, cage_extrusion=ext, max_ray_distance=ray, margin=8,
                  margin_type="EXTEND", use_clear=True, target="IMAGE_TEXTURES")
        if pf:
            kw["pass_filter"] = pf
        if t == "NORMAL":
            kw.update(normal_space="TANGENT", normal_r="POS_X", normal_g="POS_Y", normal_b="POS_Z")
        bpy.ops.object.bake(**kw)
        log("  bak", img.name, soort, f"{time.time() - t1:.1f}s")
    for o in verborgen:
        o.hide_render = False
    bpy.data.objects.remove(doel)
    bpy.data.materials.remove(m)
    if tijdelijk:
        bpy.data.objects.remove(tijdelijk)


def beeld(naam, w, data=False):
    img = bpy.data.images.new(naam, w, w, alpha=False)
    if data:
        img.colorspace_settings.name = "Non-Color"
    return img


def pixels(img):
    a = np.zeros(img.size[0] * img.size[1] * 4, np.float32)
    img.pixels.foreach_get(a)
    return a.reshape(img.size[1], img.size[0], 4)


def bewaar(img, pad, jpg=True):
    img.filepath_raw = pad
    img.file_format = "JPEG" if jpg else "PNG"
    if jpg:
        bpy.context.scene.render.image_settings.quality = 92
    img.save(filepath=pad, quality=92) if jpg else img.save(filepath=pad)
    data = img.colorspace_settings.name == "Non-Color"
    naam = img.name
    bpy.data.images.remove(img)
    out = bpy.data.images.load(pad, check_existing=False)
    out.name = naam
    if data:
        out.colorspace_settings.name = "Non-Color"
    return out


def orm(ao, ruw, naam):
    a, r = pixels(ao), pixels(ruw)
    out = beeld(naam, ao.size[0], data=True)
    p = np.ones_like(a)
    p[..., 0] = a[..., 0]
    p[..., 1] = r[..., 0]
    p[..., 2] = 0.0
    out.pixels.foreach_set(p.ravel())
    return out


def gltf_groep():
    g = bpy.data.node_groups.get("glTF Material Output")
    if g is None:
        g = bpy.data.node_groups.new("glTF Material Output", "ShaderNodeTree")
        g.interface.new_socket("Occlusion", in_out="INPUT", socket_type="NodeSocketFloat")
    return g


def pbr(naam, kleur, nrm=None, orm_img=None, tweezijdig=False):
    m = bpy.data.materials.new(naam)
    m.use_nodes = True
    nt = m.node_tree
    b = nt.nodes["Principled BSDF"]
    b.inputs["Specular IOR Level"].default_value = 0.3
    t = nt.nodes.new("ShaderNodeTexImage")
    t.image = kleur
    nt.links.new(t.outputs["Color"], b.inputs["Base Color"])
    if nrm:
        tn = nt.nodes.new("ShaderNodeTexImage")
        tn.image = nrm
        nm = nt.nodes.new("ShaderNodeNormalMap")
        nt.links.new(tn.outputs["Color"], nm.inputs["Color"])
        nt.links.new(nm.outputs["Normal"], b.inputs["Normal"])
    if orm_img:
        to = nt.nodes.new("ShaderNodeTexImage")
        to.image = orm_img
        sp = nt.nodes.new("ShaderNodeSeparateColor")
        nt.links.new(to.outputs["Color"], sp.inputs["Color"])
        nt.links.new(sp.outputs["Green"], b.inputs["Roughness"])
        nt.links.new(sp.outputs["Blue"], b.inputs["Metallic"])
        g = nt.nodes.new("ShaderNodeGroup")
        g.node_tree = gltf_groep()
        nt.links.new(sp.outputs["Red"], g.inputs["Occlusion"])
    m.use_backface_culling = not tweezijdig
    return m


def tris(objs):
    n = 0
    for o in objs:
        o.data.calc_loop_triangles()
        n += len(o.data.loop_triangles)
    return n


def exporteer(pad, objs):
    ontkies()
    for o in objs:
        o.select_set(True)
    bpy.ops.export_scene.gltf(filepath=pad, export_format="GLB", use_selection=True, export_apply=True,
                              export_tangents=True, export_image_format="AUTO", export_cameras=False,
                              export_lights=False, export_extras=False, export_animations=False)
    log("export", os.path.basename(pad), f"{os.path.getsize(pad) / 1e6:.1f} MB")


# bakgroepen: (cage-extrusie, max. straalafstand, kleur voor gemiste stralen, tweezijdig)
GROEPEN = {"opaak": (0.01, 0.03, None, False), "riet": (0.11, 0.25, RIET_VUL, True),
           "grond": (0.08, 0.14, (0.35, 0.24, 0.1, 1), False)}
HALM_GROEP = {"halm": "riet", "halm_grond": "grond"}     # hair curves -> bron van welke groep


def rt_bouw(naam, blend, res=2048, ratio_opaak=None, lod1_doel=7500, riet_ext=0.11, riet_ray=0.25, schil_bron=True):
    """Bak <naam>.blend naar <naam>_rt.glb (LOD0) en <naam>_rt_lod1.glb.
    ratio_opaak: {objectnaam-prefix: decimeerratio} voor zware bronnen (stenen, bolletjes).
    Atlassen per groep: 'opaak' (alles, plus de deurbladen), 'riet' (dakschillen; bron = halmen +
    onderlaag) en 'grond' (stromat; bron = strohalmen + grond). Bron en doel zijn dezelfde meshes,
    behalve bij riet en grond, waar de halmen (als buisjes) op de schil worden gebakken."""
    bpy.ops.wm.open_mainfile(filepath=blend)
    sc = bpy.context.scene
    sc.render.engine = "CYCLES"
    gpu(sc)
    texdir = os.path.join(HERE, "rt_textures")
    os.makedirs(texdir, exist_ok=True)
    RT = bpy.data.collections.new("RT")
    sc.collection.children.link(RT)
    ratio_opaak = ratio_opaak or {}
    groepen = dict(GROEPEN)
    groepen["riet"] = (riet_ext, riet_ray) + GROEPEN["riet"][2:]
    alles = [o for o in sc.objects if o.type in ("MESH", "CURVES") and o.get("rt") != "weg"]
    deuren = [o for o in sc.objects if o.type == "EMPTY" and "dicht" in o]
    ankers = [o for o in sc.objects if o.type == "EMPTY" and "dicht" not in o]

    def deur_van(o):
        p = o.parent
        while p is not None:
            if p in deuren:
                return p
            p = p.parent
        return None

    # ---- lows bouwen
    groep = {g: [] for g in groepen}
    bron = {g: [] for g in groepen}
    per_deur = {d: [] for d in deuren}
    for o in alles:
        soort = o.get("rt", "opaak")
        if o.type == "CURVES":
            if soort in HALM_GROEP:
                bron[HALM_GROEP[soort]].append(o)
            continue
        g = soort if soort in groepen else "opaak"
        me = eval_mesh(o)
        r = 1.0
        for pre, rr in ratio_opaak.items():
            if o.name.startswith(pre) or o.data.name.startswith(pre):
                r = rr
        if r < 1.0:
            t = bpy.data.objects.new("_t", me)
            RT.objects.link(t)
            decimeer_obj(t, r)
            me = t.data
            bpy.data.objects.remove(t)
        if g != "riet":
            bron[g].append(o)
        elif schil_bron:                             # schil_bron=False: alleen de halmen (schil ligt er bovenop)
            bron[g].append(riet_vul_bron(o, RT))
        d = deur_van(o)
        (per_deur[d] if d else groep[g]).append(me)
    lows = {g: samen(f"{naam}_{g}", ms, RT) for g, ms in groep.items() if ms}
    deur_lows = {d: samen(d.name + "_blad", per_deur[d], RT) for d in deuren if per_deur[d]}
    log("lows", {k: tris([v]) for k, v in lows.items()}, {d.name: tris([v]) for d, v in deur_lows.items()})
    for o in list(lows.values()) + list(deur_lows.values()):
        o.data.shade_smooth()
        o.data.set_sharp_from_angle(angle=math.radians(40))
    for g in bron:                                   # halmen als buisjes
        bron[g] = [h for h in bron[g] if h.type == "MESH"] + [halm_buizen(h, RT) for h in bron[g] if h.type == "CURVES"]
        for h in bron[g]:
            h.hide_render = False

    # ---- UV en bakken
    MAT = {}
    doel = {g: [lows[g]] + (list(deur_lows.values()) if g == "opaak" else []) for g in lows}
    for g, lw in doel.items():
        ext, ray, mis, tweez = groepen[g]
        uv_atlas(lw)
        r = res if g != "grond" else res // 2
        k, n, ru, ao = (beeld(f"{naam}_{g}_kleur", r), beeld(f"{naam}_{g}_normaal", r, True),
                        beeld(f"{naam}_{g}_ruw", r // 2, True), beeld(f"{naam}_{g}_ao", r // 2, True))
        if mis:
            k.generated_color = mis
        bak(lw, bron[g], [("kleur", k), ("normaal", n)], ext, ray, RT)
        bak(lw, bron[g], [("ruwheid", ru), ("ao", ao)], ext, ray, RT)
        o_ = orm(ao, ru, f"{naam}_{g}_orm")
        k = bewaar(k, os.path.join(texdir, f"{naam}_{g}_kleur.jpg"))
        n = bewaar(n, os.path.join(texdir, f"{naam}_{g}_normaal.png"), jpg=False)
        o_ = bewaar(o_, os.path.join(texdir, f"{naam}_{g}_orm.jpg"))
        MAT[g] = pbr(f"{naam}_{g}", k, n, o_, tweezijdig=tweez)
        for o in lw:
            o.data.materials.clear()
            o.data.materials.append(MAT[g])
    lod0 = list(lows.values()) + list(deur_lows.values())

    # ---- LOD1: zelfde atlas, gedecimeerd
    t0 = tris(lod0)
    l1 = []
    for o in lod0:
        k = o.copy()
        k.data = o.data.copy()
        k.name = o.name + "_lod1"
        k.data.name = k.name
        RT.objects.link(k)
        decimeer_obj(k, min(1.0, lod1_doel / t0))
        l1.append(k)
    # ---- opruimen, deuren ophangen
    for o in [o for o in sc.objects if o.users_collection and o.users_collection[0] is not RT and o.type in ("MESH", "CURVES", "LIGHT", "CAMERA")]:
        bpy.data.objects.remove(o)
    for d, o in deur_lows.items():
        for k in (o, bpy.data.objects[o.name + "_lod1"]):
            k.parent = d
            k.matrix_parent_inverse = d.matrix_world.inverted()
    lods = {"LOD0": lod0, "LOD1": l1}
    log("TRIS", {k: tris(v) for k, v in lods.items()})
    exporteer(os.path.join(HERE, f"{naam}_rt.glb"), lod0 + deuren + ankers)
    exporteer(os.path.join(HERE, f"{naam}_rt_lod1.glb"), l1 + deuren + ankers)
    bpy.ops.wm.save_as_mainfile(filepath=os.path.join(HERE, f"{naam}_rt.blend"), compress=True)
    return {k: tris(v) for k, v in lods.items()}


def rt_vergelijk(naam, res, schaal, ref_wereld, ref_px, pad, lod="_rt"):
    """De glb in EEVEE met de iso-camera en het licht van de beauty."""
    sc = leeg()
    bpy.ops.import_scene.gltf(filepath=os.path.join(HERE, f"{naam}{lod}.glb"))
    camera(sc, res, schaal, ref_wereld, ref_px)
    licht(sc)
    render(sc, pad, 64)
