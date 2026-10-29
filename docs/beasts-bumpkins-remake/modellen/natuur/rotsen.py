"""Rotsen en klifranden voor de rotsboog van missie 1.

rots_1..rots_6: rotstegels van 2 x 2 m (de vormen van rock01..06 en het concept rotsen_sheet),
oorsprong midden onder, voet loopt tot de tegelrand zodat buren aansluiten.
klif_recht, klif_hoek_buiten, klif_hoek_binnen: rotsrand met een stap van 2,0 m; hoge kant +y
(binnenhoek: +y en -x, buitenhoek: alleen het kwadrant x < 0, y > 0). De randprofielen zijn bij alle
drie gelijk en het detail dooft uit naar de tegelranden, dus ze lassen in elke draaiing aan elkaar.

Hoog: hoogteveld 280 x 280 met pieken, lagen (strata), voronoi-barsten; materiaal: rock_surface
grijs gemaakt (box-projectie), mos op de vlakke delen. Laag: gedecimeerd, smart-UV, gebakken
kleur/normaal/ORM op 1k. LOD1 = verder gedecimeerd, zelfde texturen.

  blender -b -P rotsen.py -- [alleen=rots_1,klif_recht] [res=1024]
"""
import math
import os
import random
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bpy
import numpy as np
from mathutils import Vector, noise

import natuur_lib as L

RES = int(L.OPTS.get("res", 1024))
ALLE = ["rots_1", "rots_2", "rots_3", "rots_4", "rots_5", "rots_6", "klif_recht", "klif_hoek_buiten", "klif_hoek_binnen"]
ALLEEN = [n for n in L.OPTS.get("alleen", ",".join(ALLE)).split(",") if n]
N = 280
HALF = 1.0          # tegel 2 x 2 m
DOEL = {"rots": 2600, "klif": 3200}


def smooth(e0, e1, x):
    t = np.clip((x - e0) / (e1 - e0), 0, 1)
    return t * t * (3 - 2 * t)


def piek(X, Y, cx, cy, h, rx, ry, scherp=1.2, draai=0.0, vierkant=0.6):
    """Piramide-achtige piek: mix van L2 en L-oneindig in gedraaide coordinaten."""
    c, s = math.cos(draai), math.sin(draai)
    dx, dy = X - cx, Y - cy
    u, v = (c * dx + s * dy) / rx, (-s * dx + c * dy) / ry
    d = (1 - vierkant) * np.sqrt(u * u + v * v) + vierkant * np.maximum(np.abs(u), np.abs(v))
    return h * np.clip(1 - d, 0, None) ** scherp


def ruis2(X, Y, schaal, seed, octaven=4):
    out = np.zeros_like(X)
    amp, tot = 1.0, 0.0
    off = Vector((seed * 13.1, seed * 7.7, seed * 3.3))
    fx = X.ravel()
    fy = Y.ravel()
    for o in range(octaven):
        f = schaal * 2 ** o
        vals = np.fromiter((noise.noise(Vector((a * f, b * f, 0)) + off) for a, b in zip(fx, fy)), np.float32, fx.size)
        out += amp * vals.reshape(X.shape)
        tot += amp
        amp *= 0.5
    return out / tot


def barsten(X, Y, schaal, seed, platen=False):
    """Afstand tot de voronoi-rand (klein = barst); platen=True geeft ook per cel een schuin vlak
    (a*x + b*y + c), voor hoekige, gelaagde brokken in plaats van gladde ruggen."""
    off = Vector((seed * 5.3, seed * 2.1, 0))
    fx, fy = X.ravel(), Y.ravel()
    out = np.empty(fx.size, np.float32)
    vl = np.empty(fx.size, np.float32)
    for i, (a, b) in enumerate(zip(fx, fy)):
        pos = Vector((a * schaal, b * schaal, 0.0)) + off
        d, pts = noise.voronoi(pos, distance_metric="DISTANCE", exponent=2.5)
        out[i] = d[1] - d[0]
        if platen:
            p = pts[0]
            h1 = math.sin(p.x * 12.9898 + p.y * 78.233) * 43758.5453
            h2 = math.sin(p.x * 39.346 + p.y * 11.135) * 24634.6345
            h3 = math.sin(p.x * 73.156 + p.y * 52.235) * 13758.5453
            ga, gb, gc = (h1 % 1) - 0.5, (h2 % 1) - 0.5, (h3 % 1) - 0.5
            vl[i] = ga * (pos.x - p.x) + gb * (pos.y - p.y) + gc * 0.6
    if platen:
        return out.reshape(X.shape), vl.reshape(X.shape)
    return out.reshape(X.shape)


def lagen(Z, stap, kracht, warp=None):
    """Terrassen: z naar beneden afronden en zacht terugmengen; warp (m) buigt de lagen."""
    t = (Z + (warp if warp is not None else 0)) / stap
    f = np.floor(t)
    r = t - f
    trap = (f + smooth(0.55, 1.0, r)) * stap
    trap = trap - (warp if warp is not None else 0)
    return Z * (1 - kracht) + trap * kracht


# --- Vormen ---------------------------------------------------------------------------------
def vorm(naam, X, Y):
    rnd = random.Random(naam)
    sd = hash(naam) % 97
    if naam == "rots_1":       # cluster rotsblokken op een tegel (rock01, concept 1)
        Z = np.zeros_like(X)
        for cx, cy, h, r in ((-0.35, 0.3, 1.5, 0.6), (0.4, 0.45, 1.3, 0.5), (-0.5, -0.4, 0.8, 0.45),
                             (0.15, -0.2, 1.0, 0.55), (0.55, -0.55, 0.55, 0.35), (-0.05, 0.65, 0.9, 0.4)):
            Z = np.maximum(Z, piek(X, Y, cx, cy, h, r, r * rnd.uniform(0.8, 1.2), scherp=0.43, vierkant=0.3,
                                    draai=rnd.uniform(0, 3)))
        strata = (0.22, 0.25)
    elif naam == "rots_2":     # hoge spits met losse brokken (rock02)
        Z = piek(X, Y, 0.0, 0.1, 2.3, 0.75, 0.7, scherp=0.62, vierkant=0.5, draai=0.4)
        for cx, cy, h, r in ((0.6, -0.3, 0.9, 0.35), (-0.6, -0.5, 0.6, 0.35), (0.5, 0.55, 1.0, 0.35)):
            Z = np.maximum(Z, piek(X, Y, cx, cy, h, r, r, scherp=0.50, vierkant=0.4))
        strata = (0.2, 0.3)
    elif naam == "rots_3":     # brede piramide (rock03)
        Z = piek(X, Y, 0.05, 0.0, 1.6, 1.05, 1.05, scherp=0.62, vierkant=0.85, draai=0.0)
        Z = np.maximum(Z, piek(X, Y, -0.35, 0.3, 1.25, 0.6, 0.6, scherp=0.56, vierkant=0.7))
        strata = (0.24, 0.6)
    elif naam == "rots_4":     # grote piramide met lagen (rock04)
        Z = piek(X, Y, 0.0, 0.0, 2.2, 1.05, 1.05, scherp=0.62, vierkant=0.9)
        Z = np.maximum(Z, piek(X, Y, 0.35, -0.25, 1.75, 0.6, 0.55, scherp=0.56, vierkant=0.7))
        strata = (0.26, 0.65)
    elif naam == "rots_5":     # lage dubbele kam (rock05)
        Z = np.maximum(piek(X, Y, -0.35, 0.25, 1.35, 0.75, 0.7, scherp=0.62, vierkant=0.8, draai=0.3),
                       piek(X, Y, 0.4, -0.2, 1.05, 0.65, 0.65, scherp=0.62, vierkant=0.8, draai=-0.2))
        strata = (0.24, 0.6)
    else:                      # rots_6: twee toppen naast elkaar (rock06)
        Z = np.maximum(piek(X, Y, -0.4, -0.15, 1.45, 0.65, 0.75, scherp=0.65, vierkant=0.75),
                       piek(X, Y, 0.35, 0.3, 1.5, 0.65, 0.7, scherp=0.65, vierkant=0.75))
        Z = np.maximum(Z, piek(X, Y, 0.0, 0.0, 0.45, 1.0, 1.0, scherp=0.62, vierkant=0.9))
        strata = (0.24, 0.6)
    # voet tot aan de tegelrand: een lage sokkel die bij de rand naar 0 gaat
    rand = np.maximum(np.abs(X), np.abs(Y))
    sokkel = 0.25 * smooth(1.0, 0.75, rand) * smooth(0.0, 0.3, Z + 0.3)
    Z = np.maximum(Z, sokkel * (Z > -1))
    return Z, strata, sd


def klifprofiel(s):
    """Stap van 2,0 m over s (m, positief = hoge kant)."""
    z = 2.0 * smooth(-0.75, 0.35, s)
    z = z + 0.12 * np.exp(-((s + 0.25) / 0.12) ** 2)   # een richel halverwege
    return z


def klif(naam, X, Y):
    if naam == "klif_recht":
        s = Y.copy()
    elif naam == "klif_hoek_buiten":
        # hoog alleen in het kwadrant x < 0, y > 0 (afgerond)
        s = np.minimum(Y, -X)
        hoek = (X > 0) & (Y < 0)
        s[hoek] = -np.sqrt(X[hoek] ** 2 + Y[hoek] ** 2)
    else:
        s = np.maximum(Y, -X)
        hoek = (X > 0) & (Y < 0)
        s = np.where((X > -0.0) & (Y < 0.0), -np.sqrt(np.maximum(X, 0) ** 2 + np.maximum(-Y, 0) ** 2), s)
        s = np.where((X <= 0) | (Y >= 0), np.maximum(Y, -X), s)
    Z = klifprofiel(s)
    rnd = random.Random(naam)
    # rotsblokken op de rand (binnen de tegel, zodat de lasranden het gladde profiel houden)
    rand = np.maximum(np.abs(X), np.abs(Y))
    binnen = smooth(0.95, 0.6, rand)
    for k in range(5):
        cx, cy = rnd.uniform(-0.6, 0.6), rnd.uniform(-0.6, 0.6)
        # naar de rand toe schuiven: punt waar s ~ 0
        for _ in range(20):
            i = int((cy + 1.02) / 2.04 * (N - 1))
            j = int((cx + 1.02) / 2.04 * (N - 1))
            sv = s[min(N - 1, max(0, i)), min(N - 1, max(0, j))]
            if abs(sv + 0.1) < 0.15:
                break
            cx, cy = rnd.uniform(-0.6, 0.6), rnd.uniform(-0.6, 0.6)
        h = rnd.uniform(2.15, 2.45)
        r = rnd.uniform(0.6, 0.85)
        Z = np.maximum(Z, piek(X, Y, cx, cy, h, r, r * rnd.uniform(0.8, 1.2), scherp=0.45, vierkant=0.4,
                                draai=rnd.uniform(0, 3)) * binnen)
    return Z, s


def hoogteveld(naam):
    lin = np.linspace(-HALF - 0.02, HALF + 0.02, N)
    X, Y = np.meshgrid(lin, lin)
    sd = hash(naam) % 89
    if naam.startswith("rots"):
        Z, (stap, kr), sd = vorm(naam, X, Y)
        fade = 1.0
    else:
        Z, s = klif(naam, X, Y)
        stap, kr = 0.17, 0.5
        # detail dooft uit naar de tegelranden (lassen)
        rand = np.maximum(np.abs(X), np.abs(Y))
        fade = 0.3 + 0.7 * smooth(1.0, 0.7, rand)
        # op de stap meer reliëf, op het plateau en het gras minder
        fade = fade * (0.5 + 0.5 * np.exp(-((s + 0.2) / 0.6) ** 2))
    hoog = Z > 0.02
    g = ruis2(X, Y, 1.6, sd, 4)
    Z = Z + (0.28 * g + 0.06) * fade * smooth(0.0, 0.25, Z)
    g2 = ruis2(X, Y, 0.55, sd + 7, 2)
    Z = Z * (1 + 0.25 * g2 * fade)
    warp = 0.12 * ruis2(X, Y, 0.7, sd + 3, 2) + 0.08 * X - 0.05 * Y
    Z = lagen(Z, stap, kr * (0.6 if naam.startswith("rots") else 0.5), warp=warp)
    b, vl = barsten(X, Y, 2.0, sd, platen=True)
    Z = Z + 0.14 * vl * fade * smooth(0.0, 0.35, Z)          # hoekige platen
    Z = Z - 0.11 * fade * smooth(0.09, 0.0, b) * smooth(0.0, 0.3, Z)
    b2 = barsten(X * 1.0, Y * 1.0, 8.0, sd + 1)
    Z = Z - 0.018 * fade * smooth(0.05, 0.0, b2) * smooth(0.0, 0.2, Z)
    Z = np.maximum(Z, 0.0)
    # rand van de tegel net onder de grond, zodat er geen naad met het terrein is
    rand = np.maximum(np.abs(X), np.abs(Y))
    Z = Z - 0.08 * smooth(HALF - 0.02, HALF + 0.02, rand)
    # schort: de buitenste rij een eind onder de grond, zodat een losse tegel geen open rand heeft
    Z[0, :] = Z[-1, :] = Z[:, 0] = Z[:, -1] = -0.35
    return X, Y, Z


def mesh_hoogteveld(naam, X, Y, Z):
    n = X.shape[0]
    V = np.stack([X.ravel(), Y.ravel(), Z.ravel()], 1)
    idx = np.arange(n * n).reshape(n, n)
    F = np.stack([idx[:-1, :-1].ravel(), idx[:-1, 1:].ravel(), idx[1:, 1:].ravel(), idx[1:, :-1].ravel()], 1)
    me = bpy.data.meshes.new(naam)
    me.vertices.add(len(V))
    me.vertices.foreach_set("co", V.astype(np.float32).ravel())
    me.loops.add(F.size)
    me.loops.foreach_set("vertex_index", F.astype(np.int32).ravel())
    me.polygons.add(len(F))
    me.polygons.foreach_set("loop_start", (np.arange(len(F)) * 4).astype(np.int32))
    me.update(calc_edges=True)
    me.shade_smooth()
    return me


# --- Hoog-materiaal ---------------------------------------------------------------------------
def rotsmateriaal(naam, mos=0.35):
    m = bpy.data.materials.new(naam)
    m.use_nodes = True
    nt = m.node_tree
    b = nt.nodes["Principled BSDF"]
    tc = nt.nodes.new("ShaderNodeTexCoord")
    mp = nt.nodes.new("ShaderNodeMapping")
    mp.inputs["Scale"].default_value = (0.8, 0.8, 0.8)
    nt.links.new(tc.outputs["Object"], mp.inputs["Vector"])

    def tex(n, kind):
        t = nt.nodes.new("ShaderNodeTexImage")
        t.image = L.laad(os.path.join(L.TEX, f"{n}_{kind}_1k.jpg"), data=kind != "diff")
        t.projection = "BOX"
        t.projection_blend = 0.35
        nt.links.new(mp.outputs[0], t.inputs["Vector"])
        return t
    d = tex("rock_surface", "diff")
    # grijs maken: desaturatie + lichter
    hsv = nt.nodes.new("ShaderNodeHueSaturation")
    hsv.inputs["Saturation"].default_value = 0.15
    hsv.inputs["Value"].default_value = 1.75
    nt.links.new(d.outputs["Color"], hsv.inputs["Color"])
    # hoogte-variatie: donkere vlekken
    nz = nt.nodes.new("ShaderNodeTexNoise")
    nz.inputs["Scale"].default_value = 1.8
    nt.links.new(tc.outputs["Object"], nz.inputs["Vector"])
    vl = nt.nodes.new("ShaderNodeMix")
    vl.data_type = "RGBA"
    vl.blend_type = "MULTIPLY"
    mr = nt.nodes.new("ShaderNodeMapRange")
    nt.links.new(nz.outputs["Fac"], mr.inputs["Value"])
    mr.inputs["From Min"].default_value = 0.35
    mr.inputs["From Max"].default_value = 0.7
    mr.inputs["To Min"].default_value = 0.72
    mr.inputs["To Max"].default_value = 1.05
    nt.links.new(hsv.outputs["Color"], vl.inputs[6])
    nt.links.new(mr.outputs[0], vl.inputs[7])
    vl.inputs["Factor"].default_value = 1.0
    # holtes donker (pointiness)
    geo = nt.nodes.new("ShaderNodeNewGeometry")
    pr = nt.nodes.new("ShaderNodeMapRange")
    nt.links.new(geo.outputs["Pointiness"], pr.inputs["Value"])
    pr.inputs["From Min"].default_value = 0.44
    pr.inputs["From Max"].default_value = 0.53
    pr.inputs["To Min"].default_value = 0.3
    pr.inputs["To Max"].default_value = 1.25
    hol = nt.nodes.new("ShaderNodeMix")
    hol.data_type = "RGBA"
    hol.blend_type = "MULTIPLY"
    hol.inputs["Factor"].default_value = 1.0
    nt.links.new(vl.outputs[2], hol.inputs[6])
    nt.links.new(pr.outputs[0], hol.inputs[7])
    # mos op vlakke, naar boven gerichte delen
    sep = nt.nodes.new("ShaderNodeSeparateXYZ")
    nt.links.new(geo.outputs["Normal"], sep.inputs["Vector"])
    mz = nt.nodes.new("ShaderNodeTexNoise")
    mz.inputs["Scale"].default_value = 5.0
    mz.inputs["Detail"].default_value = 8.0
    nt.links.new(tc.outputs["Object"], mz.inputs["Vector"])
    som = nt.nodes.new("ShaderNodeMath")
    som.operation = "MULTIPLY_ADD"
    nt.links.new(sep.outputs["Z"], som.inputs[0])
    som.inputs[1].default_value = 0.9
    nt.links.new(mz.outputs["Fac"], som.inputs[2])
    mm = nt.nodes.new("ShaderNodeMapRange")
    nt.links.new(som.outputs[0], mm.inputs["Value"])
    mm.inputs["From Min"].default_value = 1.22 - mos * 0.35
    mm.inputs["From Max"].default_value = 1.34 - mos * 0.35
    mos_t = tex("mossy_rock", "diff")
    mk = nt.nodes.new("ShaderNodeMix")
    mk.data_type = "RGBA"
    mk.blend_type = "MULTIPLY"
    mk.inputs["Factor"].default_value = 1.0
    nt.links.new(mos_t.outputs["Color"], mk.inputs[6])
    mk.inputs[7].default_value = (0.75, 0.85, 0.35, 1)
    fin = nt.nodes.new("ShaderNodeMix")
    fin.data_type = "RGBA"
    nt.links.new(mm.outputs[0], fin.inputs["Factor"])
    nt.links.new(hol.outputs[2], fin.inputs[6])
    nt.links.new(mk.outputs[2], fin.inputs[7])
    nt.links.new(fin.outputs[2], b.inputs["Base Color"])
    rr = nt.nodes.new("ShaderNodeMapRange")
    nt.links.new(mm.outputs[0], rr.inputs["Value"])
    rr.inputs["To Min"].default_value = 0.78
    rr.inputs["To Max"].default_value = 0.95
    nt.links.new(rr.outputs[0], b.inputs["Roughness"])
    nrm = tex("rock_surface", "nor_gl")
    nm = nt.nodes.new("ShaderNodeNormalMap")
    nm.inputs["Strength"].default_value = 1.2
    nt.links.new(nrm.outputs["Color"], nm.inputs["Color"])
    nt.links.new(nm.outputs["Normal"], b.inputs["Normal"])
    return m


def bouw(naam):
    sc = L.leeg()
    X, Y, Z = hoogteveld(naam)
    hoog = L.obj(naam + "_hoog", mesh_hoogteveld(naam + "_hoog", X, Y, Z))
    hoog.data.materials.append(rotsmateriaal(naam + "_hm", mos=0.45 if naam in ("rots_1", "rots_2", "rots_3") else 0.3))
    # laag: kopie, gedecimeerd
    laag = L.obj(naam, hoog.data.copy())
    doel = DOEL["rots" if naam.startswith("rots") else "klif"]
    huidig = L.tris([laag])
    L.decimeer(laag, doel / huidig)
    # vlakke grond (z < 0.01) weg: die is terrein, behalve een smalle rand
    import bmesh
    bm = bmesh.new()
    bm.from_mesh(laag.data)
    weg = []            # (grondvlakken laten staan: weghalen gaf gaten in de voet)
    bmesh.ops.delete(bm, geom=weg, context="FACES")
    bm.to_mesh(laag.data)
    bm.free()
    laag.data.shade_smooth()
    laag.data.set_sharp_from_angle(angle=math.radians(70))
    L.uv_slim(laag, hoek=60, marge=0.006)
    mat = L.bak_set(naam, laag, [hoog], res=RES, ext=0.04, ray=0.12, ao_min=0.3)
    laag.data.materials.clear()
    laag.data.materials.append(mat)
    bpy.data.objects.remove(hoog)
    t0 = L.tris([laag])
    l1 = L.obj(naam + "_lod1", laag.data.copy())
    L.decimeer(l1, 0.25)
    l1.data.set_sharp_from_angle(angle=math.radians(70))
    t1 = L.tris([l1])
    L.exporteer(os.path.join(L.HERE, naam + ".glb"), [laag, l1])      # LOD0 + LOD1 in een glb
    L.log(naam, "LOD0", t0, "LOD1", t1)
    return {naam: t0, naam + "_lod1": t1}


if __name__ == "__main__":
    import json
    stat = {}
    for n in ALLEEN:
        stat.update(bouw(n))
    p = os.path.join(L.HERE, "_tris.json")
    oud = json.load(open(p)) if os.path.exists(p) else {}
    oud.update(stat)
    json.dump(oud, open(p, "w"), indent=1, sort_keys=True)
    L.log("KLAAR", stat)
