"""Peasant hut uit Beasts & Bumpkins (House.png, 217x147) nagebouwd in 3D.

Ronde stenen hut met houten stijlen, bol rieten dak met een opgebonden nok (paarse band),
stenen schoorsteen door het dak, een aanbouw met deur, een hekje met touw en wat stenen.
Maten en posities zijn teruggerekend uit de sprite (87,5 px per meter op 4x).

Realisme (2026-10-28): riet als losse halmen (hair curves), muren als losse stenen, hout en steen
met Poly Haven-texturen (CC0, zie textures/BRON.md), HDRI als omgevingslicht.

Draaien (headless):
  blender -b -P peasant_hut.py -- [schaal] [yaw] [pitch] [ortho] [pass=a,b | all] [gpu] [voordeur=graden]
Zonder pass: peasant_hut.glb, peasant_hut.blend en peasant_hut_render.png naast dit script.
Met pass (beauty, albedo, normal, emission, door, shadow, anchors; all = alles): PNG's met alfa en
anchors.json in render/, zelfde camera en resolutie. Zie de README voor wat elke pass is.
"""
import math
import os
import random
import sys

import bmesh
import bpy
from mathutils import Matrix, Vector, noise

HERE = os.path.dirname(os.path.abspath(__file__))
TEX = os.path.join(HERE, "textures")
argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []


def getal(a):
    try:
        return float(a) is not None
    except ValueError:
        return False


OPTS = {a.split("=")[0]: (a.split("=", 1)[1] if "=" in a else "1") for a in argv if not getal(a)}
argv = [a for a in argv if getal(a)]
PASSES = set(OPTS.get("pass", "").split(",")) - {""}
if "all" in OPTS:
    PASSES = {"beauty", "albedo", "normal", "emission", "door", "shadow", "anchors"}
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


# --- Node-hulpjes ----------------------------------------------------------------
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
    """Mix-node heeft A/B per type; kies het juiste stopcontact."""
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
    """Texcoord * schaal, per object verschoven met Object Info > Random (instanties van een steen)."""
    tc = nt.nodes.new("ShaderNodeTexCoord")
    mp = nt.nodes.new("ShaderNodeMapping")
    mp.inputs["Scale"].default_value = (scale, scale, scale)
    nt.links.new(tc.outputs[kind], mp.inputs["Vector"])
    v = mp.outputs[0]
    if rand_off:
        oi = nt.nodes.new("ShaderNodeObjectInfo")
        # Random is een float: verschuif met (r, 1.37r, 1.74r) * rand_off
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


# --- Materialen ----------------------------------------------------------------
THATCH_STOPS = [(0.0, (0.30, 0.06, 0.0)), (0.3, (0.62, 0.17, 0.0)), (0.55, (0.95, 0.40, 0.02)),
                (0.8, (1.0, 0.62, 0.10)), (1.0, (1.0, 0.80, 0.30))]


def mat_halm(name, stops=THATCH_STOPS):
    """Strohalm op hair curves: kleur per bos (attribuut 'bos') en per halm (Random), punten lichter."""
    m, nt, b = principled(name, 0.7)
    b.inputs["Specular IOR Level"].default_value = 0.12
    hi = nt.nodes.new("ShaderNodeHairInfo")
    at = nt.nodes.new("ShaderNodeAttribute")
    at.attribute_name = "bos"
    fac = math_node(nt, "ADD", math_node(nt, "MULTIPLY", at.outputs["Fac"], 0.7),
                    math_node(nt, "MULTIPLY", hi.outputs["Random"], 0.28))
    fac = math_node(nt, "ADD", fac, math_node(nt, "MULTIPLY", hi.outputs["Intercept"], 0.15))
    fac = math_node(nt, "ADD", fac, 0.1)                 # de sprite is lichter: meer geel dan diep oranje
    r = ramp_node(nt, stops)
    nt.links.new(fac, r.inputs["Fac"])
    # Principled Hair (COLOR) maakt het oranje bleek; Principled BSDF houdt het sprite-oranje
    nt.links.new(r.outputs["Color"], b.inputs["Base Color"])
    return m


def mat_rietlaag(name):
    """Onderlaag onder de halmen: Poly Haven-riet, naar het oranje van de sprite getint en donker,
    zodat gaten tussen de halmen als diepte lezen."""
    m, nt, b = principled(name, 0.9)
    tc = nt.nodes.new("ShaderNodeTexCoord")
    sep = nt.nodes.new("ShaderNodeSeparateXYZ")
    nt.links.new(tc.outputs["Object"], sep.inputs[0])
    ang = math_node(nt, "ARCTAN2", sep.outputs["Y"], sep.outputs["X"])
    comb = nt.nodes.new("ShaderNodeCombineXYZ")
    nt.links.new(math_node(nt, "MULTIPLY", ang, 1.2), comb.inputs["X"])
    nt.links.new(math_node(nt, "MULTIPLY", sep.outputs["Z"], 0.7), comb.inputs["Y"])
    t = image(nt, "thatch_roof_angled", "diff", comb.outputs[0], box=False)
    v = bw(nt, t.outputs["Color"])
    r = ramp_node(nt, [(0.02, (0.06, 0.012, 0.0)), (0.25, (0.45, 0.12, 0.0)), (0.5, (0.85, 0.35, 0.02))])
    nt.links.new(v, r.inputs["Fac"])
    nt.links.new(r.outputs["Color"], b.inputs["Base Color"])
    bump_from(nt, b, v, 0.6)
    return m


def mat_steen(name, lo=(0.03, 0.03, 0.025), hi=(0.62, 0.58, 0.42), moss=0.7, lichen=1.3):
    """Losse muursteen: rock_surface ontkleurd, per steen een eigen tint (Object Info), mos in de
    holtes (AO) en onderaan."""
    m, nt, b = principled(name, 0.88)
    v = coords(nt, 1.2, rand_off=7.0)
    t = image(nt, "mossy_rock", "diff", v)                # alleen de helderheid: korrel en barsten
    rough = image(nt, "rock_surface", "rough", v)
    oi = nt.nodes.new("ShaderNodeObjectInfo")
    lum = bw(nt, t.outputs["Color"])
    # helderheid per steen + textuurdetail
    f = math_node(nt, "ADD", math_node(nt, "MULTIPLY", oi.outputs["Random"], 0.6),
                  math_node(nt, "MULTIPLY", lum, 1.6))
    tint = ramp_node(nt, [(0.15, lo), (0.55, ((lo[0] + hi[0]) / 2, (lo[1] + hi[1]) / 2, (lo[2] + hi[2]) / 2)),
                          (0.95, hi)])
    nt.links.new(math_node(nt, "SUBTRACT", f, 0.2), tint.inputs["Fac"])
    col_ = tint.outputs["Color"]
    if moss:
        mt = image(nt, "mossy_rock", "diff", v)
        ao = nt.nodes.new("ShaderNodeAmbientOcclusion")
        ao.only_local = True
        ao.samples = 8
        ao.inputs["Distance"].default_value = 0.08
        crev = math_node(nt, "SUBTRACT", 1.0, ao.outputs["AO"])
        nz = nt.nodes.new("ShaderNodeTexNoise")
        nz.inputs["Scale"].default_value = 3.0
        nz.inputs["Detail"].default_value = 6.0
        geo = nt.nodes.new("ShaderNodeNewGeometry")
        sz = nt.nodes.new("ShaderNodeSeparateXYZ")
        nt.links.new(geo.outputs["Position"], sz.inputs[0])
        low = math_node(nt, "MAXIMUM", math_node(nt, "SUBTRACT", 0.6, sz.outputs["Z"]), 0.0)
        mask = math_node(nt, "ADD", math_node(nt, "MULTIPLY", crev, 1.6), low)
        mask = math_node(nt, "MULTIPLY", mask, math_node(nt, "SUBTRACT", nz.outputs["Fac"], 0.35))
        mask = math_node(nt, "MINIMUM", math_node(nt, "MULTIPLY", mask, 2.5 * moss), 0.85)
        mask = math_node(nt, "MAXIMUM", mask, 0.0)
        col_ = mix_rgb(nt, mask, col_, mix_rgb(nt, 1.0, mt.outputs["Color"], (0.75, 0.75, 0.45), "MULTIPLY"))
    # gele korstmosvlekjes (de sprite heeft gele hooglichten op de stenen)
    ln = nt.nodes.new("ShaderNodeTexNoise")
    ln.inputs["Scale"].default_value = 2.5
    ln.inputs["Detail"].default_value = 8.0
    nt.links.new(v, ln.inputs["Vector"])
    lm = math_node(nt, "MULTIPLY", math_node(nt, "SUBTRACT", ln.outputs["Fac"], 0.55), 3.0 * lichen)
    lm = math_node(nt, "MINIMUM", math_node(nt, "MAXIMUM", lm, 0.0), 0.55)
    col_ = mix_rgb(nt, lm, col_, (0.55, 0.48, 0.2))
    nt.links.new(col_, b.inputs["Base Color"])
    nt.links.new(math_node(nt, "MAXIMUM", rough.outputs["Color"], 0.8), b.inputs["Roughness"])
    pit = nt.nodes.new("ShaderNodeTexNoise")              # putjes en korrel
    pit.inputs["Scale"].default_value = 18.0
    pit.inputs["Detail"].default_value = 10.0
    pit.inputs["Roughness"].default_value = 0.7
    nt.links.new(v, pit.inputs["Vector"])
    h = math_node(nt, "ADD", lum, math_node(nt, "MULTIPLY", pit.outputs["Fac"], 0.6))
    bump_from(nt, b, h, 0.9, 0.02)
    return m


def mat_specie(name):
    """Specie/aarde tussen de stenen: donker, mat."""
    m, nt, b = principled(name, 1.0)
    n = nt.nodes.new("ShaderNodeTexNoise")
    n.inputs["Scale"].default_value = 12.0
    r = ramp_node(nt, [(0.3, (0.02, 0.016, 0.01)), (0.7, (0.07, 0.055, 0.035))])   # aarde/leem
    nt.links.new(n.outputs["Fac"], r.inputs["Fac"])
    nt.links.new(r.outputs["Color"], b.inputs["Base Color"])
    bump_from(nt, b, n.outputs["Fac"], 0.8)
    return m


def mat_hout(name, tex, dark, light, scale=0.8, rand=0.0, rot=0.0):
    """Verweerd hout: Poly Haven-textuur, via zijn helderheid naar de houtkleur van de sprite."""
    m, nt, b = principled(name, 0.8)
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
    r = ramp_node(nt, [(0.05, (dark[0] * 0.4, dark[1] * 0.4, dark[2] * 0.4)), (0.35, dark), (0.75, light),
                       (1.1, (min(1, light[0] * 1.6), light[1] * 1.6, light[2] * 1.6))])
    nt.links.new(math_node(nt, "SUBTRACT", f, 0.15), r.inputs["Fac"])
    nt.links.new(r.outputs["Color"], b.inputs["Base Color"])
    nt.links.new(math_node(nt, "MAXIMUM", rough.outputs["Color"], 0.7), b.inputs["Roughness"])
    # nerf en scheuren: de donkere lijnen in de textuur liggen dieper
    bump_from(nt, b, math_node(nt, "ADD", lum, math_node(nt, "MULTIPLY", bw(nt, rough.outputs["Color"]), -0.5)), 1.0, 0.03)
    return m


def mat_kops(name):
    """Kopshout bovenop de palen: jaarringen met een paar radiale scheuren."""
    m, nt, b = principled(name, 0.9)
    tc = nt.nodes.new("ShaderNodeTexCoord")
    w = nt.nodes.new("ShaderNodeTexWave")
    w.wave_type = "RINGS"
    w.inputs["Scale"].default_value = 9.0
    w.inputs["Distortion"].default_value = 3.0
    w.inputs["Detail"].default_value = 4.0
    nt.links.new(tc.outputs["Object"], w.inputs["Vector"])
    r = ramp_node(nt, [(0.1, (0.22, 0.14, 0.06)), (0.6, (0.55, 0.42, 0.22)), (1.0, (0.62, 0.50, 0.28))])
    nt.links.new(w.outputs["Fac"], r.inputs["Fac"])
    nt.links.new(r.outputs["Color"], b.inputs["Base Color"])
    bump_from(nt, b, w.outputs["Fac"], 0.4)
    return m


def mat_touw(name, c, scale=60.0):
    """Touw: gedraaide strengen via een schuine golftextuur."""
    m, nt, b = principled(name, 0.75)
    b.inputs["Sheen Weight"].default_value = 0.4
    tc = nt.nodes.new("ShaderNodeTexCoord")
    w = nt.nodes.new("ShaderNodeTexWave")
    w.bands_direction = "DIAGONAL"
    w.inputs["Scale"].default_value = scale
    w.inputs["Distortion"].default_value = 2.0
    w.inputs["Detail"].default_value = 4.0
    nt.links.new(tc.outputs["Object"], w.inputs["Vector"])
    r = ramp_node(nt, [(0.0, (c[0] * 0.35, c[1] * 0.35, c[2] * 0.35)), (0.6, c)])
    nt.links.new(w.outputs["Fac"], r.inputs["Fac"])
    nt.links.new(r.outputs["Color"], b.inputs["Base Color"])
    bump_from(nt, b, w.outputs["Fac"], 0.6, 0.01)
    return m


def mat_flat(name, c, rough=0.8):
    m, nt, b = principled(name, rough)
    b.inputs["Base Color"].default_value = (*c, 1)
    return m


def mat_gras(name):
    m, nt, b = principled(name, 0.5)
    b.inputs["Subsurface Weight"].default_value = 0.0
    b.inputs["Transmission Weight"].default_value = 0.0
    tc = nt.nodes.new("ShaderNodeTexCoord")
    sep = nt.nodes.new("ShaderNodeSeparateXYZ")
    nt.links.new(tc.outputs["Generated"], sep.inputs[0])
    n = nt.nodes.new("ShaderNodeTexNoise")
    n.inputs["Scale"].default_value = 40.0
    nt.links.new(tc.outputs["Object"], n.inputs["Vector"])
    f = math_node(nt, "ADD", math_node(nt, "MULTIPLY", sep.outputs["Z"], 0.7), math_node(nt, "MULTIPLY", n.outputs["Fac"], 0.5))
    r = ramp_node(nt, [(0.05, (0.01, 0.14, 0.01)), (0.4, (0.05, 0.5, 0.04)), (0.85, (0.25, 0.75, 0.08))])
    nt.links.new(f, r.inputs["Fac"])
    nt.links.new(r.outputs["Color"], b.inputs["Base Color"])
    tr = nt.nodes.new("ShaderNodeBsdfTranslucent")                # licht door de sprieten
    nt.links.new(r.outputs["Color"], tr.inputs["Color"])
    mx = nt.nodes.new("ShaderNodeMixShader")
    mx.inputs["Fac"].default_value = 0.3
    nt.links.new(b.outputs[0], mx.inputs[1])
    nt.links.new(tr.outputs[0], mx.inputs[2])
    nt.links.new(mx.outputs[0], nt.nodes["Material Output"].inputs["Surface"])
    return m


M_HALM = mat_halm("halm")
M_KUIF = mat_halm("kuifhalm", [(0.0, (0.6, 0.2, 0.0)), (0.3, (0.95, 0.48, 0.04)), (0.65, (1.0, 0.68, 0.16)),
                               (1.0, (1.0, 0.85, 0.42))])
M_THATCH = mat_rietlaag("riet")
M_STONE = mat_steen("steen")
M_CHIM = mat_steen("schoorsteensteen", lo=(0.02, 0.02, 0.018), hi=(0.5, 0.49, 0.38), moss=0.25)
M_ROCK = mat_steen("rots", lo=(0.012, 0.012, 0.01), hi=(0.5, 0.48, 0.38), moss=1.0)
M_STEP = mat_steen("stoep", lo=(0.12, 0.12, 0.10), hi=(0.6, 0.58, 0.48), moss=0.4)
M_FRAME = mat_steen("kozijn", lo=(0.06, 0.07, 0.09), hi=(0.22, 0.25, 0.30), moss=0.0, lichen=0.0)
M_SPECIE = mat_specie("specie")
M_POST = mat_hout("stijl", "rough_wood", (0.09, 0.028, 0.01), (0.36, 0.13, 0.045), rand=5.0)
M_DOOR = mat_hout("deur", "weathered_brown_planks", (0.05, 0.018, 0.006), (0.20, 0.075, 0.025), 0.5, 5.0,
                  rot=math.pi / 2)
M_DARK = mat_flat("donker", (0.015, 0.012, 0.01))
M_UNDER = mat_flat("onderkant", (0.18, 0.05, 0.0), 0.95)
M_PURPLE = mat_touw("band", (0.08, 0.0, 0.11), 40.0)
M_ROPE = mat_touw("touw", (1.0, 0.33, 0.0))
M_GRASS = mat_gras("gras")
M_POSTTOP = mat_kops("kopshout")
M_IRON = mat_flat("ijzer", (0.02, 0.02, 0.02), 0.5)

# nachtlicht: emissie per pass aan/uit (dag, nacht), zie zet_nacht()
NACHT = []


def mat_gloed(name, base, glow, dag, nacht, rough=0.8):
    m, nt, b = principled(name, rough)
    b.inputs["Base Color"].default_value = (*base, 1)
    b.inputs["Emission Color"].default_value = (*glow, 1)
    b.inputs["Emission Strength"].default_value = dag
    NACHT.append((b.inputs["Emission Strength"], dag, nacht))
    return m


M_RUIT = mat_gloed("ruit", (0.02, 0.018, 0.015), (1.0, 0.55, 0.18), 0.0, 4.0, 0.3)   # achter het luik
M_ROOKGAT = mat_gloed("rookgat", (0.015, 0.012, 0.01), (1.0, 0.32, 0.05), 0.0, 1.2, 1.0)
M_VUUR = mat_gloed("vuur", (0.03, 0.01, 0.0), (1.0, 0.35, 0.05), 0.6, 18.0, 1.0)  # gloeiende houtskool
M_VLAM = mat_gloed("vlam", (0.9, 0.85, 0.7), (1.0, 0.62, 0.25), 0.0, 40.0, 0.5)
M_WAS = mat_flat("was", (0.75, 0.68, 0.5), 0.6)


# --- Geometrie-hulpjes -------------------------------------------------------------
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
    as. `scallop` = (ringen, n, a): de onderste ringen golven met r *= 1 + a*cos(n*hoek)."""
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
    """Balk; schaal wordt toegepast, zodat de textuur (objectcoordinaten) in meters ligt."""
    bpy.ops.mesh.primitive_cube_add(size=1, location=loc, rotation=(0, 0, rot_z))
    o = bpy.context.object
    o.name = name
    o.scale = size
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    if bevel:
        m = o.modifiers.new("b", "BEVEL")
        m.width, m.segments = bevel, 2
    return put(o, mat, smooth=False)


def cyl(name, loc, r, depth, mat, rot=(0, 0, 0), verts=16):
    bpy.ops.mesh.primitive_cylinder_add(vertices=verts, radius=r, depth=depth, location=loc, rotation=rot)
    o = bpy.context.object
    o.name = name
    return put(o, mat)


def tube(name, pts, r, mat, closed=False, sides=6, loc=(0, 0, 0), rot=(0, 0, 0)):
    """Buis langs een puntenlijst (voor touwstrengen)."""
    n = len(pts)
    verts, faces = [], []
    for i, p in enumerate(pts):
        a = pts[(i + 1) % n] if (closed or i < n - 1) else p
        b = pts[i - 1] if (closed or i > 0) else p
        t = (Vector(a) - Vector(b)).normalized()
        u = t.cross(Vector((0, 0, 1)))
        if u.length < 1e-3:
            u = t.cross(Vector((1, 0, 0)))
        u.normalize()
        w = t.cross(u)
        for k in range(sides):
            th = 2 * math.pi * k / sides
            verts.append(tuple(Vector(p) + (u * math.cos(th) + w * math.sin(th)) * r))
    for i in range(n if closed else n - 1):
        j = (i + 1) % n
        for k in range(sides):
            k2 = (k + 1) % sides
            faces.append([i * sides + k, i * sides + k2, j * sides + k2, j * sides + k])
    o = mesh_obj(name, verts, faces, mat, loc=loc)
    o.rotation_euler = rot
    return o


def rope_ring(loc, R, rot, mat, ply_r=0.013, turns=9, plies=3):
    """Touwring van drie in elkaar gedraaide strengen; lokaal vlak XY, dan gedraaid met rot."""
    out = []
    for p in range(plies):
        pts = []
        n = 72
        for i in range(n):
            t = 2 * math.pi * i / n
            th = turns * t + 2 * math.pi * p / plies
            rr = R + ply_r * 0.9 * math.cos(th)
            pts.append((rr * math.cos(t), rr * math.sin(t), ply_r * 0.9 * math.sin(th)))
        out.append(tube("touw", pts, ply_r, mat, closed=True, sides=5, loc=loc, rot=rot))
    return out


def stone_mesh(name, seed, p=6.0, bumps=0.15, cuts=5, sub=4, hf=0.06):
    """Onregelmatige steen in een eenheidskubus: afgeronde doos (superellips), lage ruis en een
    paar afgeslagen vlakken."""
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
    me.set_sharp_from_angle(angle=math.radians(35))      # afgeslagen vlakken blijven scherp
    return me


STONES = [stone_mesh(f"steen{k}", 100 + k) for k in range(14)]
for me in STONES:
    me.materials.append(M_STONE)
stones_out = []


def stone(loc, size, rot_z, mat=None, mesh=None, tilt=(0.0, 0.0)):
    me = mesh or random.choice(STONES)
    ob = bpy.data.objects.new("steen", me)
    ob.location = loc
    ob.rotation_euler = (tilt[0], tilt[1], rot_z)
    ob.scale = (size[0] / 2, size[1] / 2, size[2] / 2)
    col.objects.link(ob)
    if mat is not None:                               # materiaal per object, mesh blijft gedeeld
        ob.material_slots[0].link = "OBJECT"
        ob.material_slots[0].material = mat
    stones_out.append(ob)
    return ob


def on_wall(deg, out=0.0):
    a = math.radians(deg)
    return HX + math.cos(a) * (HUT_R + out), HY + math.sin(a) * (HUT_R + out), a


def arch_outline(w, h, z0, n=16):
    """(y, z) langs een rondboog: links omhoog, over de boog, rechts omlaag."""
    zc = z0 + h - w / 2
    pts = [(-w / 2, z0), (-w / 2, zc)]
    for k in range(1, n):
        t = math.pi * (1 - k / n)
        pts.append((w / 2 * math.cos(t), zc + w / 2 * math.sin(t)))
    return pts + [(w / 2, zc), (w / 2, z0)]


def arched_frame(name, cx, cy, z0, w, h, rot_z, depth, mat, gat=None, diep=0.0):
    """Kozijn met een ronde bovenkant. gat = (breedte, hoogte, onderkant boven z0): een open kozijn
    met een dag (neggekant) die `diep` meter de muur in loopt, zodat er achter de deur geen muur zit.
    Lokaal: x naar buiten (rot_z), y langs de muur. Onderkant 0: open naar de grond (deur)."""
    if gat is None:
        o = box(name, (cx, cy, z0 + (h - w / 2) / 2), (depth, w, h - w / 2), mat, rot_z=rot_z, bevel=0.02)
        bpy.ops.mesh.primitive_cylinder_add(vertices=24, radius=w / 2, depth=depth,
                                            location=(cx, cy, z0 + h - w / 2), rotation=(0, math.pi / 2, rot_z))
        put(bpy.context.object, mat)
        return o
    wi, hi, bi = gat
    buit = arch_outline(w, h, z0)
    bin_ = arch_outline(wi, hi - bi, z0 + bi)
    dicht = bi > 0                                    # luik: rondom dicht, ook onderlangs
    n = len(buit)
    xs = (depth / 2, -depth / 2)                      # voorkant, achterkant van het kozijn
    verts = [(x, y, z) for x in xs for lijst in (buit, bin_) for (y, z) in lijst]
    verts += [(-depth / 2 - diep, y, z) for (y, z) in bin_]   # dag door de muur, achter het kozijn
    V = lambda kant, binnen, i: kant * 2 * n + binnen * n + i
    faces, dag = [], []
    for i in range(n if dicht else n - 1):
        j = (i + 1) % n
        for kant in (0, 1):                           # voor- en achtervlak
            faces.append([V(kant, 0, i), V(kant, 0, j), V(kant, 1, j), V(kant, 1, i)])
        for binnen in (0, 1):                         # buitenrand en binnenrand
            faces.append([V(0, binnen, i), V(0, binnen, j), V(1, binnen, j), V(1, binnen, i)])
        dag.append([V(1, 1, i), V(1, 1, j), 4 * n + j, 4 * n + i])
    if not dicht:                                     # kopse kanten op de grond
        for i in (0, n - 1):
            faces.append([V(0, 0, i), V(0, 1, i), V(1, 1, i), V(1, 0, i)])
    o = mesh_obj(name, verts, faces + dag, mat, smooth=False)
    o.data.materials.append(M_SPECIE)                 # de dag is donkere leem, geen kozijnsteen
    for p in o.data.polygons[len(faces):]:
        p.material_index = 1
    o.data.transform(Matrix.Rotation(rot_z, 4, "Z"))
    o.location = (cx, cy, 0)
    m = o.modifiers.new("b", "BEVEL")
    m.width, m.segments, m.limit_method = 0.015, 2, "ANGLE"
    return o


def plank_door(name, cx, cy, z0, w, h, rot_z, n=4):
    """Deur van losse planken met een ronde bovenkant, twee klampen en een ijzeren ring."""
    rot = Matrix.Rotation(rot_z, 3, "Z")
    pw = w / n
    delen = []
    for i in range(n):
        x = -w / 2 + pw * (i + 0.5)
        top = h - w / 2 + math.sqrt(max(0.0, (w / 2) ** 2 - (abs(x) + pw * 0.3) ** 2))
        top -= random.uniform(0, 0.02)
        off = rot @ Vector((random.uniform(-0.006, 0.006), x, 0))
        delen.append(box(name, (cx + off.x, cy + off.y, z0 + top / 2), (0.05, pw - 0.012, top), M_DOOR,
                         rot_z=rot_z, bevel=0.008))
    for zz in (0.3 * h, 0.72 * h):                    # klampen
        off = rot @ Vector((0.035, 0, 0))
        delen.append(box(name, (cx + off.x, cy + off.y, z0 + zz), (0.03, w * 0.86, 0.09), M_DOOR, rot_z=rot_z,
                         bevel=0.008))
    off = rot @ Vector((0.05, w * 0.28, 0))
    bpy.ops.mesh.primitive_torus_add(major_radius=0.045, minor_radius=0.008, location=(cx + off.x, cy + off.y, z0 + h * 0.5),
                                     rotation=(0, math.pi / 2, rot_z))
    delen.append(put(bpy.context.object, M_IRON))
    return delen


DEUREN = {}


def scharnier(name, delen, cx, cy, w, rot_z):
    """Deur draaibaar maken: een leeg object op de scharnieras (binnenkant van de deur, de kant
    zonder ring) met de planken als kinderen. Lokaal x naar buiten, y langs de deur; open (naar
    buiten) met rotation_euler.z = dicht - hoek, zie zet_deur(). De planken blijven losse objecten,
    zodat hun tint per plank (Object Info > Random) gelijk blijft."""
    rot = Matrix.Rotation(rot_z, 4, "Z")
    T = Matrix.Translation((cx, cy, 0)) @ rot @ Matrix.Translation((-0.025, -w / 2, 0))
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


# --- Ronde hut -------------------------------------------------------------------
H = (HX, HY, 0)


def kern(name, r0, r1, z1, gaten, mat, seg=180):
    """Specie-kern van de ronde muur: cilinder met een dicht dak, met gaten achter deur en luik
    (hoek, halve breedte in graden, z0, z1), zodat een open deur een donker interieur toont."""
    zs = sorted({0.0, z1} | {min(max(g, 0.0), z1) for _, _, g0, g1 in gaten for g in (g0, g1)})
    verts, faces = [], []
    for z in zs:
        r = r0 + (r1 - r0) * z / z1
        verts += [(r * math.cos(2 * math.pi * i / seg), r * math.sin(2 * math.pi * i / seg), z) for i in range(seg)]
    for j in range(len(zs) - 1):
        zm = (zs[j] + zs[j + 1]) / 2
        for i in range(seg):
            am = 360.0 * (i + 0.5) / seg
            if any(abs((am - g + 180) % 360 - 180) < hw and g0 < zm < g1 for g, hw, g0, g1 in gaten):
                continue
            a, b = j * seg + i, j * seg + (i + 1) % seg
            faces.append([a, b, b + seg, a + seg])
    top = len(verts)
    verts.append((0, 0, z1))
    last = (len(zs) - 1) * seg
    faces += [[last + i, last + (i + 1) % seg, top] for i in range(seg)]
    return mesh_obj(name, verts, faces, mat, loc=H)


kern("wand", HUT_R - 0.04, HUT_R - 0.06, WALL_H + 0.2, [(172.0, 14.0, -1, 1.62), (288.0, 11.0, 0.58, 1.58)],
     M_SPECIE)

POSTS = (148.0, 196.0, 260.0, 315.0)
for deg in POSTS:
    x, y, a = on_wall(deg, 0.04)
    box("stijl", (x, y, WALL_H / 2), (0.22, 0.20, WALL_H), M_POST, rot_z=a, bevel=0.03)

# openingen in de ronde muur: (hoek, halve breedte in graden, z0, z1)
GATEN = [(172.0, 16.5, -1, 1.78), (288.0, 13.5, 0.48, 1.68)] + [(d, 4.5, -1, 9) for d in POSTS]


def ring_wall(cx, cy, R, z0, z1, a0, a1, gaten=(), depth=0.2, hs=(0.08, 0.22), ls=(0.14, 0.42), mat=None,
              rfun=None):
    """Stenen in lagen rond een as; rfun(z) geeft de straal per hoogte (schoorsteen)."""
    z = z0
    while z < z1:
        h = random.uniform(*hs)
        zc = z + h / 2
        RR = rfun(zc) if rfun else R
        a = a0 + random.uniform(0, 0.15)
        while a < a1:
            L = random.uniform(*ls)
            da = L / RR
            ad0, ad1 = math.degrees(a), math.degrees(a + da)
            vrij = True
            for g, hw, g0, g1 in gaten:
                if ad1 > g - hw and ad0 < g + hw and z + h > g0 and z < g1:
                    vrij = False
            if vrij:
                am = a + da / 2
                rr = RR + random.uniform(-0.03, 0.025)
                stone((cx + rr * math.cos(am), cy + rr * math.sin(am), zc),
                      (L * random.uniform(0.9, 1.0), depth, h * random.uniform(0.85, 0.95)),
                      am + math.pi / 2, mat, tilt=(random.uniform(-0.1, 0.1), random.uniform(-0.12, 0.12)))
            a += da + 0.006 / RR
        z += h + 0.005


# alleen de kant die de camera ziet (hoek 105..345)
ring_wall(HX, HY, HUT_R - 0.04, 0.0, 1.98, math.radians(100), math.radians(350), GATEN)

# voordeur (links-voor, tot op de grond) en een luik rechts-achter, elk met een rond grijsblauw kozijn
x, y, a = on_wall(172.0, 0.05)
arched_frame("deurkozijn", x, y, 0.0, 0.95, 1.7, a, 0.1, M_FRAME, gat=(0.70, 1.52, 0.0), diep=0.25)
x2, y2, _ = on_wall(172.0, 0.10)
scharnier("deur_voor", plank_door("voordeur", x2, y2, 0.0, 0.8, 1.6, a, n=5), x2, y2, 0.8, a)
# twee stoepstenen, half in de grond en vrij van de deur, zodat die open kan
for k, out in enumerate((0.48, 0.86)):
    x3, y3, _ = on_wall(172.0 + (k - 0.5) * 6, out)
    stone((x3, y3, 0.0), (0.34, 0.66 - 0.1 * k, 0.09), a + 0.1 * k, M_STEP)
x, y, a = on_wall(288.0, 0.05)
# het gat is iets ruimer dan het luik: 's nachts lekt er een smalle lichtrand en licht door de naden
arched_frame("kozijn", x, y, 0.55, 0.72, 1.05, a, 0.1, M_FRAME, gat=(0.60, 1.0, 0.05), diep=0.25)
x2, y2, _ = on_wall(288.0, 0.10)
plank_door("luik", x2, y2, 0.62, 0.56, 0.90, a, n=3)
x3, y3, _ = on_wall(288.0, 0.14)
box("vensterbank", (x3, y3, 0.53), (0.2, 0.9, 0.08), M_POST, rot_z=a, bevel=0.02)
x3, y3, _ = on_wall(288.0, -0.10)
box("ruit", (x3, y3, 1.07), (0.01, 0.62, 1.0), M_RUIT, rot_z=a)       # binnenruit, 's nachts verlicht

# interieur, alleen te zien door een open deur: aarden vloer, tafel met kaars, haard onder de
# schoorsteen. Geen globale random hier: die zou de stenen hierna verschuiven.
cyl("vloer", (HX, HY, 0.004), HUT_R - 0.1, 0.008, M_SPECIE, verts=48)
TAFEL = (HX - 0.95, HY + 0.45)
box("tafel", (*TAFEL, 0.72), (0.5, 0.8, 0.05), M_POST, rot_z=math.radians(-60), bevel=0.01)
for sx, sy in ((-1, -1), (-1, 1), (1, -1), (1, 1)):
    o = Matrix.Rotation(math.radians(-60), 3, "Z") @ Vector((sx * 0.2, sy * 0.33, 0))
    box("tafelpoot", (TAFEL[0] + o.x, TAFEL[1] + o.y, 0.35), (0.05, 0.05, 0.7), M_POST)
KAARS = (TAFEL[0] + 0.05, TAFEL[1] - 0.1, 0.745)
cyl("tafelkaars", (KAARS[0], KAARS[1], KAARS[2] + 0.06), 0.025, 0.12, M_WAS, verts=12)
bpy.ops.mesh.primitive_uv_sphere_add(radius=1, segments=12, ring_count=8, location=(KAARS[0], KAARS[1], KAARS[2] + 0.15))
bpy.context.object.scale = (0.014, 0.014, 0.032)
put(bpy.context.object, M_VLAM)
HAARD = (HX + 1.25 * math.cos(math.radians(284)), HY + 1.25 * math.sin(math.radians(284)))
for k in range(8):
    am = 2 * math.pi * k / 8
    stone((HAARD[0] + 0.32 * math.cos(am), HAARD[1] + 0.32 * math.sin(am), 0.06), (0.2, 0.14, 0.13),
          am + math.pi / 2, M_STEP, mesh=STONES[k])
for k in range(6):                                   # houtskool en twee blokken
    am = 2 * math.pi * k / 6
    stone((HAARD[0] + 0.12 * math.cos(am), HAARD[1] + 0.12 * math.sin(am), 0.04), (0.12, 0.09, 0.07),
          am, M_VUUR, mesh=STONES[13 - k])

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


# wenkbrauw: boven de voordeur buigt de dakrand omhoog en naar binnen, zodat de deur vrij
# onder het riet uit staat en open kan (op de sprite hangt de rand er net boven)
DOOR_DEG, BROW_W, BROW_UP, BROW_IN = 172.0, 13.0, 0.42, 0.30


def brow(a, r, z):
    d = (math.degrees(a) - DOOR_DEG + 180) % 360 - 180
    g = math.exp(-(d / BROW_W) ** 2)
    f = max(0.0, min(1.0, (2.75 - z) / 0.9))                 # alleen de onderkant van het dak
    return r - BROW_IN * g * f, z + BROW_UP * g * f


def brow_mesh(ob):
    for v in ob.data.vertices:
        a, r = math.atan2(v.co.y, v.co.x), math.hypot(v.co.x, v.co.y)
        r2, z2 = brow(a, r, v.co.z)
        k = r2 / r if r > 1e-6 else 1.0
        v.co.x, v.co.y, v.co.z = v.co.x * k, v.co.y * k, z2


dak = lathe("dak", dome_profile(), M_THATCH, seg=96, jitter=0.0, loc=H, scallop=(3, 9, 0.03))
brow_mesh(dak)
brow_mesh(lathe("dakonder", [(1.6, 2.01), (2.27, 1.84)], M_UNDER, seg=72, loc=H, scallop=(2, 9, 0.03), cap=False))

# nok: paarse band van gewikkeld touw en een kuif van schoven
nok = [lathe("band", [(0.58, 3.82), (0.58, 4.42)], M_PURPLE, seg=32, loc=H)]
zb = 3.86
while zb < 4.40:
    nok += rope_ring((HX, HY, zb), 0.615 + random.uniform(-0.005, 0.005), (random.uniform(-0.02, 0.02), 0, 0),
                     M_PURPLE, ply_r=0.02, turns=40)
    zb += 0.07

# stenen schoorsteen: tonvorm met een ronde kap en een klein rookgat
CH = (1.02, -1.59, 0)
CH_PROF = [(0.36, 2.6), (0.44, 3.0), (0.48, 3.45), (0.46, 3.75), (0.43, 3.92)]


def ch_r(z):
    for (r0, z0), (r1, z1) in zip(CH_PROF, CH_PROF[1:]):
        if z <= z1:
            return r0 + (r1 - r0) * max(0.0, (z - z0) / (z1 - z0))
    return CH_PROF[-1][0]


chim = [lathe("schoorsteen", [(r - 0.06, z) for r, z in CH_PROF] + [(0.33, 3.95), (0.30, 3.9), (0.28, 3.6)],
              M_SPECIE, seg=24, loc=CH, cap=False),
        lathe("rookgat", [(0.29, 3.62), (0.0, 3.62)], M_DARK, seg=16, loc=CH, cap=False)]
n0 = len(stones_out)
ring_wall(CH[0], CH[1], 0.4, 2.7, 3.86, 0.0, 2 * math.pi, depth=0.14, hs=(0.08, 0.13), ls=(0.13, 0.22),
          mat=M_CHIM, rfun=lambda z: ch_r(z) - 0.03)
for k in range(11):                                       # kraag van platte stenen bovenop
    am = 2 * math.pi * k / 11
    stone((CH[0] + 0.39 * math.cos(am), CH[1] + 0.39 * math.sin(am), 3.92), (0.22, 0.16, 0.08), am + math.pi / 2,
          M_CHIM)
chim += stones_out[n0:]

# --- Aanbouw achter-links (+Y), deur op de -X-kant ---------------------------------
AX0, AX1, AY0, AY1 = -0.4, 1.6, 0.95, 3.65


def aanbouw_kern(x0, x1, y0, y1, z1, gy0, gy1, gz1):
    """Specie-kern van de aanbouw als holle doos, met een gat achter de deur in de -X-kant."""
    vs = [(x, y, z) for z in (0.0, z1) for y in (y0, y1) for x in (x0, x1)]
    fs = [[0, 1, 3, 2], [4, 6, 7, 5], [0, 4, 5, 1], [2, 3, 7, 6], [1, 5, 7, 3]]   # vloer, dak, -Y, +Y, +X
    k = len(vs)
    for y in (y0, gy0, gy1, y1):                       # -X-kant in drie stukken om het gat
        vs += [(x0, y, 0.0), (x0, y, gz1), (x0, y, z1)]
    # stroken per y-vak: (onder, midden) en (midden, boven); het middelste vak alleen boven
    for i in range(3):
        a = k + 3 * i
        if i != 1:
            fs.append([a, a + 3, a + 4, a + 1])
        fs.append([a + 1, a + 4, a + 5, a + 2])
    return mesh_obj("aanbouw", vs, fs, M_SPECIE, smooth=False)


aanbouw_kern(AX0 + 0.06, AX1, AY0 + 0.03, AY1 - 0.03, WALL_H, 2.1, 2.9, 1.5)
# interieur van de aanbouw: een kist en een ton
box("kist", (0.9, 3.1, 0.25), (0.7, 0.5, 0.5), M_POST, rot_z=0.2, bevel=0.02)
cyl("ton", (0.2, 3.2, 0.4), 0.28, 0.8, M_POST, verts=20)


def flat_wall(p0, p1, z0, z1, gaten, depth=0.2):
    """Rechte muur van p0 naar p1 (x, y), stenen in lagen; gaten = (t0, t1, z0, z1) langs de muur."""
    d = Vector((p1[0] - p0[0], p1[1] - p0[1], 0))
    Lt = d.length
    d.normalize()
    ang = math.atan2(d.y, d.x)
    z = z0
    while z < z1:
        h = random.uniform(0.12, 0.2)
        t = -random.uniform(0, 0.15)
        while t < Lt:
            L = random.uniform(0.2, 0.38)
            vrij = all(not (t + L > g0 and t < g1 and z + h > h0 and z < h1) for g0, g1, h0, h1 in gaten)
            if vrij:
                tm = t + L / 2
                stone((p0[0] + d.x * tm, p0[1] + d.y * tm, z + h / 2),
                      (L * random.uniform(0.9, 1.0), depth, h * random.uniform(0.85, 0.95)), ang)
            t += L + 0.006
        z += h + 0.005


# -X-kant: deur op y=2.5, stijlen op AY0+0.3 en AY1
flat_wall((AX0 + 0.06, AY0 + 0.1), (AX0 + 0.06, AY1 - 0.05), 0.0, 1.95,
          [(2.5 - 0.48 - AY0 - 0.1, 2.5 + 0.48 - AY0 - 0.1, -1, 1.7), (0.1, 0.32, -1, 9)])
# voorkant (-Y): grotendeels achter de hut, alleen het stuk links ervan
flat_wall((AX0 + 0.1, AY0 + 0.06), (0.3, AY0 + 0.06), 0.0, 1.95, [])
for (px, py) in ((AX0, AY1), (AX0, AY0 + 0.3), (AX1, AY1)):
    box("stijl", (px, py, WALL_H / 2), (0.22, 0.22, WALL_H), M_POST, bevel=0.03)
arched_frame("deurkozijn", AX0 - 0.03, 2.5, 0.0, 0.95, 1.65, math.pi, 0.1, M_FRAME, gat=(0.66, 1.42, 0.0), diep=0.25)
scharnier("deur_aanbouw", plank_door("deur", AX0 - 0.08, 2.5, 0.0, 0.75, 1.50, math.pi, n=4), AX0 - 0.08, 2.5, 0.75,
          math.pi)
stone((AX0 - 0.48, 2.5, 0.0), (0.38, 0.72, 0.09), 0.05, M_STEP)   # vrij van de deur

# platte rieten deksel, flauw aflopend naar achter (+Y); de punt linksachter ligt het laagst.
LX0, LX1, LY0, LY1 = -0.6, 2.0, 0.6, 4.0


def lid_z(x, y):
    return 1.88 + 0.2 * (LY1 - y) + 0.04 * (x - LX0)


def lid_top(x, y):
    u, v = (x - LX0) / (LX1 - LX0), (y - LY0) / (LY1 - LY0)
    return lid_z(x, y) + 0.12 * math.sin(math.pi * min(max(u, 0), 1)) * math.sin(math.pi * min(max(v, 0), 1))


LO = (0.7, -3.0, 0.0)
nx, ny = 10, 12
vs, fs = [], []
for j in range(ny + 1):
    for i in range(nx + 1):
        u, v = i / nx, j / ny
        x, y = LX0 + (LX1 - LX0) * u, LY0 + (LY1 - LY0) * v
        vs.append((x - LO[0], y - LO[1], lid_top(x, y) - 0.04))
for j in range(ny):
    for i in range(nx):
        k = j * (nx + 1) + i
        fs.append([k, k + 1, k + nx + 2, k + nx + 1])
r = mesh_obj("aanbouwdak", vs, fs, M_THATCH, loc=LO)
s = r.modifiers.new("dik", "SOLIDIFY")
s.thickness = 0.14
bv = r.modifiers.new("rond", "BEVEL")
bv.width, bv.segments = 0.06, 3

# --- Hekje met touw, rechtsvoor (vijf palen) ----------------------------------------
FRONT = [(-3.24, -2.82), (-1.06, -2.82), (1.25, -2.82)]
CORNER, BACK = (4.0, -2.6), (4.0, -0.25)


def log(name, loc, r, length, rot, seed, sides=20, rings=24):
    """Ruwe stam/paal langs lokaal Z: straal met ruis (knoesten, kromming), afgeronde kopse kant."""
    rn = random.Random(seed)
    off = Vector((rn.uniform(-40, 40), rn.uniform(-40, 40), rn.uniform(-40, 40)))
    bow = Vector((rn.uniform(-1, 1), rn.uniform(-1, 1), 0)) * 0.015 * length
    verts, faces = [], []
    for j in range(rings + 1):
        t = j / rings
        z = -length / 2 + length * t
        c = bow * math.sin(math.pi * t)
        for i in range(sides):
            a = 2 * math.pi * i / sides
            q = Vector((math.cos(a), math.sin(a), z * 2.0))
            rr = r * (1 + 0.07 * noise.noise(q * 1.5 + off) + 0.025 * noise.noise(q * 6 + off))
            if t in (0.0, 1.0):
                rr *= 0.94                            # afgeschuinde rand
            verts.append((c.x + rr * math.cos(a), c.y + rr * math.sin(a), z))
    for j in range(rings):
        for i in range(sides):
            a, b = j * sides + i, j * sides + (i + 1) % sides
            faces.append([a, b, b + sides, a + sides])
    o = mesh_obj(name, verts, faces, M_POST, loc=loc)
    o.rotation_euler = rot
    return o


for k, (x, y) in enumerate(FRONT + [CORNER, BACK]):
    log("paal", (x, y, 0.55), 0.14, 1.1, (0, 0, 0), 500 + k)
    cyl("paalkop", (x, y, 1.1), 0.128, 0.012, M_POSTTOP, verts=20)


def rail(p, q, z, extra=0.15):
    d = Vector((q[0] - p[0], q[1] - p[1], 0))
    mid = ((p[0] + q[0]) / 2, (p[1] + q[1]) / 2, z)
    ang = math.atan2(d.y, d.x)
    log("regel", mid, 0.1, d.length + 2 * extra, (0, math.pi / 2, ang), int(z * 100), rings=60)
    for sgn in (-1, 1):                                # kopshout aan de uiteinden
        e = Vector(mid) + d.normalized() * sgn * (d.length / 2 + extra + 0.002)
        cyl("regelkop", tuple(e), 0.088, 0.006, M_POSTTOP, rot=(0, math.pi / 2, ang), verts=20)
    return ang


def lashing(x, y, z, ang):
    """Touw als een X om paal en regel: twee gedraaide touwringen, gekanteld om de regel heen."""
    for tilt in (0.7, -0.7):
        rope_ring((x, y, z), 0.16, (tilt, 0, ang), M_ROPE, ply_r=0.016, turns=22)


ang_front = rail(FRONT[0], CORNER, 0.78)
for (x, y) in FRONT:
    lashing(x, y, 0.78, ang_front + math.pi / 2)
lashing(CORNER[0], CORNER[1], 0.78, ang_front + math.pi / 2)
ang_side = rail(BACK, (4.0, -3.3), 0.9, extra=0.0)          # steekt voorbij de hoekpaal uit
for (x, y) in (CORNER, BACK):
    lashing(x, y, 0.9, ang_side + math.pi / 2)

# --- Stenen links, graspollen -------------------------------------------------------
ROCKS = [stone_mesh(f"kei{k}", 300 + k, p=2.4, bumps=0.25, cuts=3, sub=5, hf=0.07) for k in range(3)]
for me in ROCKS:
    me.materials.append(M_ROCK)
for k, (x, y, sz) in enumerate(((-1.8, 3.25, 0.36), (-1.55, 2.4, 0.25), (-2.6, 2.65, 0.16), (-2.34, 3.57, 0.12),
                                (3.4, -1.0, 0.1), (2.6, -3.4, 0.09))):
    stone((x, y, sz * 0.3), (sz * 2.5, sz * 2.0, sz * 1.5), random.uniform(0, 6.3), mesh=ROCKS[k % 3])

RV = Vector((0.707, -0.707, 0))                              # schermrechts
FV = Vector((-0.707, -0.707, 0))                             # naar de camera
for (gx, gy) in ((-0.62, 3.52), (2.99, -1.37), (-0.85, -1.57)):
    # waaier (V/W) zoals de sprite: buiten lang en uitbuigend, midden kort; elke arm is een bosje
    # smalle sprieten met eigen lengte en buiging
    vs, fs = [], []
    for lean, hgt, fwd in ((-0.42, 0.55, 0.05), (0.05, 0.32, 0.12), (0.45, 0.5, 0.0)):
        for _ in range(14):
            le = lean * random.uniform(0.6, 1.2) + random.uniform(-0.08, 0.08)
            hg = hgt * random.uniform(0.6, 1.05)
            fw = fwd + random.uniform(-0.1, 0.1)
            base = Vector((gx, gy, 0)) + RV * random.uniform(-0.05, 0.05) + FV * random.uniform(-0.04, 0.04)
            wd = random.uniform(0.018, 0.03)
            n = 6
            k0 = len(vs)
            for k in range(n + 1):
                t = k / n
                w = wd * (1 - t) ** 0.8 + 0.002
                c = base + RV * (le * t ** 1.6) + FV * (fw * t) + Vector((0, 0, hg * t - 0.06 * abs(le) * t ** 3))
                side = (RV * 0.7 + FV * 0.3).normalized() * w * 0.5
                vs += [tuple(c - side), tuple(c + side)]
            fs += [[k0 + 2 * k, k0 + 2 * k + 1, k0 + 2 * k + 3, k0 + 2 * k + 2] for k in range(n)]
    mesh_obj("gras", vs, fs, M_GRASS)

# --- Ankerpunten als lege objecten (glTF-nodes voor de game) -------------------------
def anker(name, loc):
    e = bpy.data.objects.new(name, None)
    e.empty_display_type = "PLAIN_AXES"
    e.empty_display_size = 0.2
    e.location = loc
    col.objects.link(e)
    return e


anker("rook_bron", (CH[0], CH[1], 3.95))                           # schoorsteenmond: rook
anker("deur_voor_drempel", (*on_wall(172.0, 0.10)[:2], 0.0))       # waar dorpelingen in/uit gaan
anker("deur_aanbouw_drempel", (AX0 - 0.08, 2.5, 0.0))
anker("kaars", (*on_wall(288.0, -0.05)[:2], 1.07))                 # achter het luik: nachtlicht

# --- glTF export (model zonder camera, licht en schaduwvanger) -----------------------
# De halmen (hair curves) gaan niet mee: glTF kent geen curves. Het model houdt de rietlaag eronder.
bpy.ops.export_scene.gltf(filepath=os.path.join(HERE, "peasant_hut.glb"), export_format="GLB",
                          export_apply=True)


# --- Riet als losse halmen (alleen render) --------------------------------------------
def strands(name, curves, mat, bos, rad):
    """curves: lijst puntenlijsten; bos: waarde 0..1 per curve; rad(u) straal langs de halm."""
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


def resample(path, step=0.01):
    """Polylijn (r, z) -> lijst (s, r, z, nr, nz) op gelijke booglengte; n = buitennormaal."""
    out, s = [], 0.0
    for (r0, z0), (r1, z1) in zip(path, path[1:]):
        L = math.hypot(r1 - r0, z1 - z0)
        tr, tz = (r1 - r0) / L, (z1 - z0) / L
        k = 0.0
        while k < L:
            out.append((s + k, r0 + tr * k, z0 + tz * k, -tz, tr))
            k += step
        s += L
    out.append((s, *path[-1], out[-1][3], out[-1][4]))
    return out


def at(prof, s):
    i = min(int(s / 0.01), len(prof) - 1)
    return prof[i]


rnd = random.Random(11)
pad = list(reversed(dome_profile()[2:]))                      # nok -> rand
PROF = resample(pad)
S_END = PROF[-1][0]
dome_c, dome_b = [], []
s0 = 0.0
while s0 < S_END - 0.05:
    L = rnd.uniform(0.75, 0.95)
    rmid = at(PROF, min(s0 + L / 2, S_END))[1]
    nb = int(2 * math.pi * max(rmid, 0.6) / 0.065)
    for b in range(nb):
        ab = 2 * math.pi * (b + rnd.uniform(-0.3, 0.3)) / nb
        bv_ = rnd.random()
        Lb = L * rnd.uniform(0.85, 1.1)
        lean = rnd.gauss(0, 0.012)
        for _ in range(18):
            ai = ab + rnd.gauss(0, 0.024 / max(rmid, 0.6))
            si = s0 + rnd.uniform(-0.04, 0.04)
            se = si + Lb * rnd.uniform(0.9, 1.05)
            hang = 0.0
            if se > S_END:                                   # rafelige zoom: halmen steken voorbij de rand
                hang = rnd.uniform(0.0, 0.11) ** 1.0 * rnd.random() ** 0.5
                se = S_END
            lift = rnd.uniform(0.0, 0.015)
            pts = []
            for k in range(8):
                u = k / 7
                s = si + (se - si) * u
                _, rr, zz, nr, nz = at(PROF, max(s, 0.0))
                off = -0.025 + lift + 0.075 * u ** 0.9
                rr, zz = rr + nr * off, zz + nz * off
                a = ai + lean * u * (se - si) / max(rr, 0.5) + (ai - ab) * (-0.15 * u)
                if zz < 2.06:                                 # zelfde schulp als de rand
                    rr *= 1 + 0.03 * math.cos(9 * a) * min(1.0, (2.06 - zz) / 0.1)
                rr, zz = brow(a, rr, zz)
                pts.append((HX + rr * math.cos(a), HY + rr * math.sin(a), zz))
            if hang:
                # hangend stuk: verder de laatste richting op en wat naar beneden
                p6, p7 = Vector(pts[-2]), Vector(pts[-1])
                d = (p7 - p6).normalized()
                for k, f in ((1, 0.5), (2, 1.0)):
                    q = p7 + d * hang * f + Vector((0, 0, -0.3 * hang * f * f))
                    pts.append(tuple(q))
            else:
                pts += [pts[-1], pts[-1]]
                pts[-2] = tuple(Vector(pts[-3]) + (Vector(pts[-3]) - Vector(pts[-4])) * 0.01)
                pts[-1] = tuple(Vector(pts[-3]) + (Vector(pts[-3]) - Vector(pts[-4])) * 0.02)
            dome_c.append(pts)
            dome_b.append(bv_)
    s0 += rnd.uniform(0.26, 0.34)
halm_rad = lambda u: 0.0062 - 0.0018 * u
riet = [strands("dakhalmen", dome_c, M_HALM, dome_b, halm_rad)]

# aanbouwdak: halmen in lagen de helling af (+Y), rafelig over de achterrand en over de linkerrand
lid_c, lid_b = [], []
y0 = LY0
while y0 < LY1 - 0.05:
    L = rnd.uniform(0.7, 0.9)
    nb = int((LX1 - LX0) / 0.065)
    for b in range(nb):
        xb = LX0 + 0.04 + (LX1 - LX0 - 0.04) * (b + rnd.uniform(0, 1)) / nb
        bv_ = 0.35 + 0.35 * rnd.random()            # minder verschil per bos: anders lijken het planken
        for _ in range(18):
            xi = xb + rnd.gauss(0, 0.022)
            yi = y0 + rnd.uniform(-0.04, 0.04)
            ye = yi + L * rnd.uniform(0.9, 1.05)
            hang = rnd.uniform(0, 0.12) * rnd.random() ** 0.5 if ye > LY1 else 0.0
            ye = min(ye, LY1)
            lift = rnd.uniform(0.0, 0.015)
            pts = []
            for k in range(8):
                u = k / 7
                y = yi + (ye - yi) * u
                x = xi + (xb - xi) * 0.4 * u
                pts.append((x, y, lid_top(x, y) - 0.02 + lift + 0.06 * u ** 0.9))
            for f in (0.5, 1.0) if hang else ():
                pts.append((pts[-1][0], pts[-1][1] + hang * f * 0.5, pts[-1][2] - hang * f))
            while len(pts) < 10:
                pts.append(tuple(Vector(pts[-1]) + Vector((0, 0.002, 0))))
            lid_c.append(pts)
            lid_b.append(bv_)
    y0 += rnd.uniform(0.26, 0.34)
# linkerrand: halmen dwars over de rand gekamd, naar beneden
y = LY0 + 0.1
while y < LY1 + 0.05:
    bv_ = 0.35 + 0.35 * rnd.random()
    for _ in range(11):
        yi = y + rnd.gauss(0, 0.02)
        x0 = LX0 + rnd.uniform(0.25, 0.4)
        hang = rnd.uniform(0.02, 0.14)
        pts = []
        for k in range(10):
            u = k / 9
            x = x0 + (LX0 - 0.05 - x0) * min(u / 0.75, 1.0)
            z = lid_top(max(x, LX0), yi) + 0.03 + 0.03 * u
            if u > 0.6:
                z -= (u - 0.6) / 0.4 * (0.1 + hang)
                x -= (u - 0.6) / 0.4 * 0.03
            pts.append((x, yi, z))
        lid_c.append(pts)
        lid_b.append(bv_)
    y += 0.06
riet.append(strands("aanbouwhalmen", lid_c, M_HALM, lid_b, halm_rad))

# kuif: zeven schoven die uit de band steken, buitenste naar buiten gekanteld, aren bovenaan
kuif_c, kuif_b = [], []
for k in range(7):
    if k < 6:
        a = 2 * math.pi * k / 6 + 0.3
        cx, cy, tilt = 0.40 * math.cos(a), 0.40 * math.sin(a), 0.25
    else:
        a, cx, cy, tilt = 0.0, 0.0, 0.0, 0.0
    out = Vector((math.cos(a), math.sin(a), 0))
    bv_ = rnd.random()
    for _ in range(340):
        rr, th = 0.13 * math.sqrt(rnd.random()), rnd.uniform(0, 2 * math.pi)
        base = Vector((HX + cx + rr * math.cos(th), HY + cy + rr * math.sin(th), 4.28))
        spread = Vector((math.cos(th), math.sin(th), 0)) * rr * 1.9
        hgt = rnd.uniform(0.32, 0.46) + (0.05 if k == 6 else 0.0)
        pts = []
        for j in range(7):
            u = j / 6
            p = base + spread * u * u + out * tilt * hgt * u + Vector((0, 0, hgt * u - 0.12 * (rr / 0.13) ** 2 * u * u))
            pts.append(tuple(p))
        kuif_c.append(pts)
        kuif_b.append(bv_)
riet.append(strands("kuifhalmen", kuif_c, M_KUIF, kuif_b, lambda u: 0.006 + 0.008 * u ** 3))
nok += riet[2:]

# alleen de wanden werpen schaduw op de grond (via light linking, zie de zon hieronder); het dak
# schaduwt wel zichzelf
DAK = nok + chim + [dak] + riet

# --- Schaduwvanger, camera en licht --------------------------------------------------
bpy.ops.mesh.primitive_plane_add(size=30, location=(0, 0, 0))
vanger = bpy.context.object
vanger.is_shadow_catcher = True

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


def sun(name, energy, rot, color=(1, 1, 1), shadow=True, angle=2.0):
    d = bpy.data.lights.new(name, "SUN")
    d.energy = energy
    d.color = color
    d.angle = math.radians(angle)
    d.use_shadow = shadow
    o = bpy.data.objects.new(name, d)
    col.objects.link(o)
    o.rotation_euler = rot
    return o


def link_coll(name, objs, state="INCLUDE"):
    c = bpy.data.collections.new(name)
    for o in objs:
        c.objects.link(o)
        c.collection_objects[len(c.objects) - 1].light_linking.link_state = state
    return c


ZON_ROT = (math.radians(26), 0, math.radians(61))   # 64 graden hoog, van rechtsachter: schaduw links
WARM = (1.0, 0.9, 0.75)
zon = sun("zon", 1.9, ZON_ROT, WARM)
zon.light_linking.receiver_collection = link_coll("niet_vanger", [vanger], "EXCLUDE")
zon2 = sun("zon_grond", 1.9, ZON_ROT, WARM)              # zelfde zon, alleen op de grond, alleen muren werpen
zon2.light_linking.receiver_collection = link_coll("alleen_vanger", [vanger])
zon2.light_linking.blocker_collection = link_coll(
    "werpers", [o for o in col.objects if o.type in ("MESH",) and o not in DAK and o is not vanger])

vul = sun("vul", 2.2, (math.radians(55), 0, math.radians(-115)), (0.95, 0.95, 1.0), angle=25.0)  # linksvoor
vul.light_linking.receiver_collection = bpy.data.collections["niet_vanger"]   # zachte schaduw, niet op de grond
vul2 = sun("vul_grond", 2.2, (math.radians(55), 0, math.radians(-115)), (0.95, 0.95, 1.0), shadow=False)
vul2.light_linking.receiver_collection = bpy.data.collections["alleen_vanger"]   # houdt de grondschaduw zacht

world = bpy.data.worlds.new("w")
world.use_nodes = True
wn = world.node_tree
bg = wn.nodes["Background"]
env = wn.nodes.new("ShaderNodeTexEnvironment")
env.image = bpy.data.images.load(os.path.join(TEX, "qwantani_late_afternoon_1k.hdr"))
klem = mix_rgb(wn, 1.0, env.outputs["Color"], (1.2, 1.2, 1.2), "DARKEN")   # zon uit de HDRI: geen 2e schaduw
wn.links.new(klem, bg.inputs["Color"])
bg.inputs["Strength"].default_value = 0.45
scene.world = world

scene.render.engine = "CYCLES"
scene.cycles.samples = 96 if SCALE <= 2 else 192
scene.cycles.use_denoising = True
scene.cycles.max_bounces = 6
scene.render.film_transparent = True
scene.view_settings.view_transform = "Standard"
scene.render.resolution_x = 217 * SCALE
scene.render.resolution_y = 147 * SCALE
scene.render.filepath = os.path.join(HERE, "peasant_hut_render.png")
scene.render.image_settings.color_mode = "RGBA"


# --- Nachtlampen en de zon per uur (standaard uit; alleen voor de passes) -------------
def lamp(name, loc, energy, color, radius):
    d = bpy.data.lights.new(name, "POINT")
    d.energy, d.color, d.shadow_soft_size = energy, color, radius
    o = bpy.data.objects.new(name, d)
    col.objects.link(o)
    o.location = loc
    o.hide_render = True
    return o


LAMPEN = [lamp("haardvuur", (*HAARD, 0.3), 60.0, (1.0, 0.45, 0.12), 0.15),
          lamp("kaarslicht", (KAARS[0], KAARS[1], KAARS[2] + 0.16), 6.0, (1.0, 0.6, 0.25), 0.02),
          lamp("lantaarn", (0.6, 2.6, 1.4), 15.0, (1.0, 0.55, 0.2), 0.05)]
DAGLICHT = [zon, zon2, vul, vul2]
zon_uur = sun("zon_uur", 1.9, ZON_ROT, WARM, angle=3.0)
zon_uur.hide_render = True

for naam, graden in (("deur_voor", OPTS.get("voordeur")), ("deur_aanbouw", OPTS.get("aanbouwdeur"))):
    if graden:
        zet_deur(naam, float(graden))
print("HALMEN", len(dome_c), len(lid_c), len(kuif_c), "STENEN", len(stones_out))
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(HERE, "peasant_hut.blend"))
if not PASSES:
    bpy.ops.render.render(write_still=True)
    print("KLAAR", scene.render.filepath)
    sys.exit(0)

# --- Passes voor Godot (pre-rendered sprites met lichtdata) ---------------------------
import json
import time

from bpy_extras.object_utils import world_to_camera_view

OUT = os.path.join(HERE, "render")
os.makedirs(OUT, exist_ok=True)
W, Hpx = scene.render.resolution_x, scene.render.resolution_y
if "gpu" in OPTS:
    prefs = bpy.context.preferences.addons["cycles"].preferences
    prefs.compute_device_type = "OPTIX"
    prefs.get_devices()
    for d in prefs.devices:
        d.use = d.type == "OPTIX"
    scene.cycles.device = "GPU"
scene.render.use_persistent_data = True


def pixel(p):
    v = world_to_camera_view(scene, cam, Vector(p))
    return [round(v.x * W, 1), round((1 - v.y) * Hpx, 1)]


def footprint(stap=4):
    """Grondcontour van ronde hut plus aanbouw (met stijlen): de vereniging van twee convexe vormen
    die allebei C bevatten is stervormig vanuit C, dus per straal de verste van de twee randen."""
    C = Vector((0.6, 1.2))
    R = HUT_R + 0.06
    bx0, bx1, by0, by1 = AX0 - 0.11, AX1 + 0.11, AY0, AY1 + 0.11
    pts = []
    for k in range(0, 360, stap):
        d = Vector((math.cos(math.radians(k)), math.sin(math.radians(k))))
        q = C - Vector((HX, HY))
        tc = -q.dot(d) + math.sqrt(q.dot(d) ** 2 - q.dot(q) + R * R)       # uittrede cirkel
        tb = min((b - c) / v for b, c, v in ((bx1 if d.x > 0 else bx0, C.x, d.x), (by1 if d.y > 0 else by0, C.y, d.y))
                 if abs(v) > 1e-9)                                           # uittrede rechthoek
        pts.append(C + d * max(tc, tb))
    return pts


def schrijf_ankers():
    voet = footprint()
    ank = {
        "frame": [W, Hpx], "schaal": SCALE, "px_per_m": round(W / ORTHO, 3),
        "oorsprong": pixel((0, 0, 0)),
        "schoorsteen": pixel((CH[0], CH[1], 3.95)),
        "voordeur": pixel((*on_wall(172.0, 0.10)[:2], 0.0)),
        "voordeur_buiten": pixel((*on_wall(172.0, 0.75)[:2], 0.0)),
        "aanbouwdeur": pixel((AX0 - 0.08, 2.5, 0.0)),
        "aanbouwdeur_buiten": pixel((AX0 - 0.75, 2.5, 0.0)),
        "venster": pixel((*on_wall(288.0, 0.10)[:2], 1.07)),
        "haard": pixel((*HAARD, 0.3)),
        "kaars": pixel((KAARS[0], KAARS[1], KAARS[2] + 0.15)),
        "voetafdruk": [pixel((p.x, p.y, 0.0)) for p in voet],
    }
    ank["sorteer_y"] = max(p[1] for p in ank["voetafdruk"])
    ank["wereld"] = {"schoorsteen": [CH[0], CH[1], 3.95], "venster_z": 1.07,
                     "voetafdruk": [[round(p.x, 3), round(p.y, 3)] for p in voet]}
    with open(os.path.join(OUT, "anchors.json"), "w") as f:
        json.dump(ank, f, indent=1)
    print("ANKERS", {k: v for k, v in ank.items() if k not in ("voetafdruk", "wereld")}, flush=True)


schrijf_ankers()                                        # eerst: de Godot-demo wacht erop


def wereld(name, kleur, sterkte):
    w = bpy.data.worlds.new(name)
    w.use_nodes = True
    b = w.node_tree.nodes["Background"]
    b.inputs["Color"].default_value = (*kleur, 1)
    b.inputs["Strength"].default_value = sterkte
    return w


W_WIT, W_ZWART = wereld("wit", (1, 1, 1), 1.0), wereld("zwart", (0, 0, 0), 0.0)

# normaalpass: per materiaal een emissie van de schaduwnormaal (met bump) in cameraruimte,
# R = schermrechts, G = schermomhoog, B = naar de kijker, elk * 0,5 + 0,5
cm = cam.matrix_world.to_3x3()
ASSEN = (cm.col[0].normalized(), cm.col[1].normalized(), cm.col[2].normalized())
NORMAAL = {}
for m in bpy.data.materials:
    if not m.node_tree or "Material Output" not in m.node_tree.nodes:
        continue
    nt = m.node_tree
    uit = nt.nodes["Material Output"].inputs["Surface"]
    if not uit.is_linked:
        continue
    b = nt.nodes.get("Principled BSDF")
    if b and b.inputs["Normal"].is_linked:
        nrm = b.inputs["Normal"].links[0].from_socket
    else:
        nrm = nt.nodes.new("ShaderNodeNewGeometry").outputs["Normal"]
    cmb = nt.nodes.new("ShaderNodeCombineXYZ")
    for i, as_ in enumerate(ASSEN):
        d = nt.nodes.new("ShaderNodeVectorMath")
        d.operation = "DOT_PRODUCT"
        nt.links.new(nrm, d.inputs[0])
        d.inputs[1].default_value = as_
        nt.links.new(math_node(nt, "ADD", math_node(nt, "MULTIPLY", d.outputs["Value"], 0.5), 0.5), cmb.inputs[i])
    em = nt.nodes.new("ShaderNodeEmission")
    nt.links.new(cmb.outputs[0], em.inputs["Color"])
    NORMAAL[m] = (em.outputs[0], uit.links[0].from_socket, uit)

ALLES = [o for o in scene.objects if o.type in ("MESH", "CURVES") and o is not vanger]
DEUR_DELEN = {n: d for n, (e, d) in DEUREN.items()}
ALLE_DEUREN = DEUR_DELEN["deur_voor"] + DEUR_DELEN["deur_aanbouw"]


def zon_op(uur, lat=52.0, dec=23.0):
    """Zonnestand op 52 graden NB rond de langste dag; zuiden = de huidige zon (wereldhoek -29),
    oosten links daarvan. Geeft (rotatie voor een zonlamp, hoogte, kompasazimut)."""
    Hh, la, de = math.radians(15 * (uur - 12)), math.radians(lat), math.radians(dec)
    el = math.asin(math.sin(la) * math.sin(de) + math.cos(la) * math.cos(de) * math.cos(Hh))
    az = math.degrees(math.atan2(math.sin(Hh), math.cos(Hh) * math.sin(la) - math.tan(de) * math.cos(la))) + 180
    phi = math.radians(151.0 - az)
    s = Vector((math.cos(el) * math.cos(phi), math.cos(el) * math.sin(phi), math.sin(el)))
    return (-s).to_track_quat("-Z", "Y").to_euler(), math.degrees(el), az


def zet(mode, weg=(), alleen=None):
    """Scene in de stand voor een pass: beauty, albedo, normal, emission of shadow."""
    for o in ALLES:
        o.hide_render = o in weg
        o.is_holdout = alleen is not None and o not in alleen
        o.visible_camera = mode != "shadow"
    vanger.hide_render = mode not in ("beauty", "shadow") or alleen is not None
    for l in DAGLICHT:
        l.hide_render = mode != "beauty"
    vul2.hide_render = mode not in ("beauty", "shadow")
    zon_uur.hide_render = mode != "shadow"
    for l in LAMPEN:
        l.hide_render = mode != "emission"
    scene.world = {"albedo": W_WIT, "normal": W_ZWART, "emission": W_ZWART}.get(mode, world)
    for sk, dag, nacht in NACHT:
        sk.default_value = nacht if mode == "emission" else dag
    for m, (em, orig, uit) in NORMAAL.items():
        m.node_tree.links.new(em if mode == "normal" else orig, uit)
    scene.view_settings.view_transform = "Raw" if mode == "normal" else "Standard"
    scene.render.dither_intensity = 0.0 if mode == "normal" else 1.0
    scene.cycles.use_denoising = mode != "normal"


TIJDEN = []


def render(naam, mode, samples, **kw):
    zet(mode, **kw)
    scene.cycles.samples = samples
    scene.render.filepath = os.path.join(OUT, naam + ".png")
    t = time.time()
    bpy.ops.render.render(write_still=True)
    TIJDEN.append((naam, round(time.time() - t, 1)))
    print("PASS", naam, TIJDEN[-1][1], "s", scene.view_settings.view_transform, flush=True)


hoog = SCALE > 2
if "beauty" in PASSES:
    render("beauty", "beauty", 192 if hoog else 96)
if "albedo" in PASSES:
    render("albedo", "albedo", 64 if hoog else 32)
if "normal" in PASSES:
    render("normal", "normal", 16)
if "emission" in PASSES:
    render("emission", "emission", 64 if hoog else 32)
    render("emission_dooropen", "emission", 64 if hoog else 32, weg=ALLE_DEUREN)
if "door" in PASSES:
    render("base_dooropen", "beauty", 192 if hoog else 96, weg=ALLE_DEUREN)
    if "albedo" in PASSES:
        render("albedo_dooropen", "albedo", 64 if hoog else 32, weg=ALLE_DEUREN)
    if "normal" in PASSES:
        render("normal_dooropen", "normal", 16, weg=ALLE_DEUREN)
    for naam, prefix, hoeken in (("deur_voor", "door", (0, 30, 60, 90)), ("deur_aanbouw", "annexdoor", (0, 90))):
        for g in hoeken:
            zet_deur(naam, g)
            render(f"{prefix}_{g}", "beauty", 192 if hoog else 96, alleen=DEUR_DELEN[naam])
            if "albedo" in PASSES:
                render(f"{prefix}_{g}_albedo", "albedo", 32, alleen=DEUR_DELEN[naam])
            if "normal" in PASSES:
                render(f"{prefix}_{g}_normal", "normal", 16, alleen=DEUR_DELEN[naam])
        zet_deur(naam, 0)
if "shadow" in PASSES:
    for uur in (8, 10, 12, 14, 16, 18):
        zon_uur.rotation_euler, el, az = zon_op(uur)
        print("ZON", uur, round(el, 1), round(az, 1))
        render(f"shadow_{uur:02d}", "shadow", 32)
print("TIJDEN", TIJDEN, "TOTAAL", round(sum(t for _, t in TIJDEN)), "s")
