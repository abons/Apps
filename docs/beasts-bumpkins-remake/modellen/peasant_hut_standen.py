"""Bouwstanden 1-3 van de boerenhut, gesneden uit de afgewerkte game-hut (stand 4 = peasant_hut_rt.glb).

Besluit gebruiker (2026-10-30, lokaal/concept/ronde4_log.md): de standen komen UIT het afgewerkte model, zodat
muren, raam en ronde deurbovenkanten in elke stand gelijk doorlopen. Dus geen nieuwe muren: dit script opent
peasant_hut_rt.blend (eerst `blender -b -P peasant_hut_realtime.py`) en hergebruikt de gebakken eilanden met
hun eigen UV's op de atlassen `steen` en `hout`:
- muurstenen per steen houden of weglaten (op het midden van de steen), zodat de bovenkant rafelig blijft;
- specie-kernen, palen en kozijnen met een vlak doorsnijden (bisect, UV's lopen mee), kernen afgedekt met een
  strook specie, palen en kozijnen dichtgemaakt met de kleur van hun zijkant;
- de af-hut heeft alleen stenen aan de kant die de camera ziet (hoek 100..350, aanbouw alleen de -X-gevel).
  Zonder dak kijk je over de muur naar binnen, dus de binnenkant krijgt kopieen van bestaande stenen:
  rond = gespiegeld in de kern (r' = 2 r_kern - r) en gedraaid uit vensters zonder openingen, aanbouw = de
  -X-stenen verschoven naar de +X- en +Y-muur (de deur dichtgezet met stenen van ernaast);
- dakspanten, ladder en paaltjes zijn geschaalde kopieen van een stijl (zelfde hout op de atlas), het touw
  pakt de kleur van een sjorring van het hek.
Stand 1 heeft de aangestampte aarde als eigen tegelbaar materiaal (farm_soil, zoals de akker in natuur/props.py).

Draaien (headless):
  blender -b -P peasant_hut_standen.py -- [standen=1,2,3] [preview] [alleen_preview]
Schrijft peasant_hut_stand1.glb .. peasant_hut_stand3.glb naast dit script; `preview` rendert daarna
render/hut_standen.png (stand 1 | 2 | 3 | af, EEVEE met camera en licht van peasant_hut.blend).
Oorsprong, schaal en assen zijn die van peasant_hut_rt.glb: in Godot op exact dezelfde transform wisselen.
"""
import math
import os
import random
import sys

import bmesh
import bpy
import numpy as np
from mathutils import Matrix, Vector, noise

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "natuur"))
RT_BLEND = os.path.join(HERE, "peasant_hut_rt.blend")
HUT_BLEND = os.path.join(HERE, "peasant_hut.blend")
argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
OPTS = {a.split("=")[0]: (a.split("=", 1)[1] if "=" in a else "1") for a in argv}
STANDEN = [int(s) for s in OPTS.get("standen", "1,2,3").split(",") if s]
GLB = lambda s: os.path.join(HERE, f"peasant_hut_stand{s}.glb")

# maten uit peasant_hut.py
HX, HY, HUT_R, WALL_H = 0.65, -0.05, 1.7, 1.85
AX0, AX1, AY0, AY1 = -0.4, 1.6, 0.95, 3.65
CH = (1.02, -1.59)
HAARD = (HX + 1.25 * math.cos(math.radians(284)), HY + 1.25 * math.sin(math.radians(284)))
DEUR_V, RAAM = 172.0, 288.0                       # hoeken in de ronde muur
POSTS = (148.0, 196.0, 260.0, 315.0)
H = Vector((HX, HY, 0))

SNIJ = {2: 0.72, 3: 1.92}                         # bovenkant muur per stand (kern + afdekking)
KAP_B = 0.11                                      # halve breedte van de afdekstrook op de muur


def log(*a):
    print("[standen]", *a, flush=True)


def kern_r(z):
    return HUT_R - 0.04 - 0.02 * min(max(z / (WALL_H + 0.2), 0.0), 1.0)


def hoek(p):
    return math.degrees(math.atan2(p[1] - HY, p[0] - HX)) % 360


def straal(p):
    return math.hypot(p[0] - HX, p[1] - HY)


# --- Eilanden ----------------------------------------------------------------------------
class Bron:
    """Een bronmesh als bmesh met zijn losse eilanden (midden, grenzen, vlakken)."""

    def __init__(self, ob):
        self.bm = bmesh.new()
        self.bm.from_mesh(ob.data)
        self.bm.faces.ensure_lookup_table()
        self.uv = self.bm.loops.layers.uv.active
        self.mat = ob.data.materials[0]
        gezien, self.eil = set(), []
        for f in self.bm.faces:
            if f.index in gezien:
                continue
            stapel, fs = [f], []
            gezien.add(f.index)
            while stapel:
                g = stapel.pop()
                fs.append(g)
                for e in g.edges:
                    for h in e.link_faces:
                        if h.index not in gezien:
                            gezien.add(h.index)
                            stapel.append(h)
            co = np.array([v.co[:] for v in {v for g in fs for v in g.verts}])
            self.eil.append({"f": fs, "c": Vector(co.mean(0)), "lo": Vector(co.min(0)), "hi": Vector(co.max(0)),
                             "n": sum(len(g.verts) - 2 for g in fs)})


def kopie(dst, bron, faces, f=None, flip=False):
    """Vlakken van een bron in dst, met UV; f(Vector) -> Vector op elk hoekpunt, flip draait de winding om."""
    uvd = dst.loops.layers.uv.verify()
    vmap = {}
    for fc in faces:
        vs = []
        for v in fc.verts:
            nv = vmap.get(v)
            if nv is None:
                nv = dst.verts.new(f(v.co.copy()) if f else v.co.copy())
                vmap[v] = nv
            vs.append(nv)
        uvs = [l[bron.uv].uv.copy() for l in fc.loops]
        if flip:
            vs, uvs = vs[::-1], uvs[::-1]
        try:
            nf = dst.faces.new(vs)
        except ValueError:
            continue
        nf.smooth = fc.smooth
        for l, u in zip(nf.loops, uvs):
            l[uvd].uv = u


def snij(bm, z, dicht=False):
    """Alles boven z weg; dicht = de doorsnede vullen (vlak met de UV van een buurvlak: kleur van de zijkant)."""
    geom = bm.verts[:] + bm.edges[:] + bm.faces[:]
    r = bmesh.ops.bisect_plane(bm, geom=geom, plane_co=(0, 0, z), plane_no=(0, 0, 1), clear_outer=True)
    if not dicht:
        return
    uv = bm.loops.layers.uv.verify()
    rand = [e for e in bm.edges if e.is_boundary and all(abs(v.co.z - z) < 1e-4 for v in e.verts)]
    nieuw = bmesh.ops.holes_fill(bm, edges=rand, sides=0)["faces"]
    for f in nieuw:
        buur = [l for l in f.verts[0].link_loops if l.face is not f]
        u = buur[0][uv].uv.copy() if buur else Vector((0, 0))
        for l in f.loops:
            l[uv].uv = u
        f.smooth = False


def sluit(bm):
    """Open randen dicht (de af-hut snijdt de achterkant van elke steen weg; zonder dak kijk je erin)."""
    uv = bm.loops.layers.uv.verify()
    rand = [e for e in bm.edges if e.is_boundary]
    nieuw = bmesh.ops.holes_fill(bm, edges=rand, sides=0)["faces"]
    for f in nieuw:
        buur = [l for l in f.verts[0].link_loops if l.face is not f]
        u = buur[0][uv].uv.copy() if buur else Vector((0, 0))
        for l in f.loops:
            l[uv].uv = u
    return len(nieuw)


def bovenkant_licht(bm, zmin):
    """Bovenvlakken van de bovenste laag: in de af-hut lag daar de volgende laag op, dus de bake is daar
    zwart (contactschaduw). UV per hoekpunt van een zijvlak van dezelfde steen: de kleur van de zijkant."""
    uv = bm.loops.layers.uv.verify()
    n = 0
    for f in bm.faces:
        f.normal_update()
        if f.normal.z < 0.45 or f.calc_center_median().z < zmin:
            continue
        zij = {m.face for v in f.verts for m in v.link_loops if m.face.normal.z < 0.3}
        if not zij:
            continue
        g = max(zij, key=lambda h: h.calc_area())          # midden van het grootste zijvlak
        u = sum((m[uv].uv for m in g.loops), Vector((0, 0))) / len(g.loops)
        for l in f.loops:
            l[uv].uv = u
        n += 1
    return n


def kap(bm, zmin, breed=KAP_B, zop=0.0):
    """Afdekstrook op de open bovenrand van een specie-kern: per randstuk een quad, UV van de rand zelf."""
    uv = bm.loops.layers.uv.verify()
    rand = [e for e in bm.edges if e.is_boundary and all(v.co.z > zmin for v in e.verts)]
    for e in rand:
        l = e.link_loops[0]
        a, b = l.vert, l.link_loop_next.vert
        ua, ub = l[uv].uv.copy(), l.link_loop_next[uv].uv.copy()
        d = b.co - a.co
        d.z = 0
        if d.length < 1e-6:
            continue
        n = Vector((d.y, -d.x, 0)).normalized() * breed
        z = max(a.co.z, b.co.z) + zop
        pa, pb = Vector((a.co.x, a.co.y, z)), Vector((b.co.x, b.co.y, z))
        vs = [bm.verts.new(p) for p in (pa - n, pa + n, pb + n, pb - n)]
        f = bm.faces.new(vs)
        f.normal_update()
        if f.normal.z < 0:
            f.normal_flip()
        for lp in f.loops:
            lp[uv].uv = ua if (lp.vert is vs[0] or lp.vert is vs[1]) else ub
        f.smooth = False


def naar_obj(naam, bm, mat, coll):
    me = bpy.data.meshes.new(naam)
    bm.to_mesh(me)
    me.materials.append(mat)
    o = bpy.data.objects.new(naam, me)
    coll.objects.link(o)
    return o


def tris(objs):
    n = 0
    for o in objs:
        if o.type == "MESH":
            o.data.calc_loop_triangles()
            n += len(o.data.loop_triangles)
    return n


def decimeer(o, ratio):
    m = o.modifiers.new("d", "DECIMATE")
    m.ratio = ratio
    m.use_collapse_triangulate = True
    dg = bpy.context.evaluated_depsgraph_get()
    me = bpy.data.meshes.new_from_object(o.evaluated_get(dg))
    o.modifiers.clear()
    oud, o.data = o.data, me
    bpy.data.meshes.remove(oud)


# --- Balken uit een stijl ----------------------------------------------------------------
class Stijl:
    """Een stijl van de ronde muur als sjabloon: lokaal x radiaal (0,22), y langs de muur (0,20), z 0..1,85."""

    def __init__(self, hout, eil):
        self.hout, self.f = hout, eil["f"]
        a = math.atan2(eil["c"].y - HY, eil["c"].x - HX)
        self.Mi = Matrix.Rotation(-a, 4, "Z") @ Matrix.Translation((-eil["c"].x, -eil["c"].y, 0))

    def balk(self, dst, p0, p1, w, d, rol=0.0):
        p0, p1 = Vector(p0), Vector(p1)
        ax = (p1 - p0).normalized()
        hulp = Vector((0, 0, 1)) if abs(ax.z) < 0.95 else Vector((1, 0, 0))
        ex = ax.cross(hulp).normalized()
        ey = ax.cross(ex).normalized()
        ex, ey = (Matrix.Rotation(rol, 3, ax) @ ex), (Matrix.Rotation(rol, 3, ax) @ ey)
        if ex.cross(ey).dot(ax) < 0:
            ey = -ey
        L = (p1 - p0).length
        Mi = self.Mi

        def f(co):
            l = Mi @ co
            return p0 + ax * (l.z / WALL_H * L) + ex * (l.x / 0.22 * w) + ey * (l.y / 0.20 * d)
        kopie(dst, self.hout, self.f, f)


def touw(dst, P, uv, r=0.012, zijden=4):
    """Dun touw langs P met een vaste UV (de kleur van een sjorring)."""
    uvl = dst.loops.layers.uv.verify()
    ringen = []
    for i, p in enumerate(P):
        t = (P[min(i + 1, len(P) - 1)] - P[max(i - 1, 0)]).normalized()
        x = t.cross(Vector((0, 0, 1))).normalized()
        y = t.cross(x)
        ringen.append([dst.verts.new(p + (x * math.cos(a) + y * math.sin(a)) * r)
                       for a in [2 * math.pi * k / zijden for k in range(zijden)]])
    for r0, r1 in zip(ringen, ringen[1:]):
        for k in range(zijden):
            f = dst.faces.new([r0[k], r0[(k + 1) % zijden], r1[(k + 1) % zijden], r1[k]])
            f.smooth = True
            for l in f.loops:
                l[uvl].uv = uv


# --- Bron indelen ------------------------------------------------------------------------
def indelen(st, hout, specie, gras):
    S = {k: [] for k in ("wand", "aanbouw", "kozijn", "schoorsteen", "haard", "stoep", "rots")}
    for e in st.eil:
        c, lo, hi = e["c"], e["lo"], e["hi"]
        r = straal(c)
        if e["n"] > 400:
            S["kozijn"].append(e)
        elif lo.z > 2.5:
            S["schoorsteen"].append(e)
        elif math.hypot(c.x - HAARD[0], c.y - HAARD[1]) < 0.45 and hi.z < 0.2:
            S["haard"].append(e)
        elif hi.z < 0.06 and lo.z > -0.06:
            S["stoep"].append(e)
        elif -0.5 < c.x < -0.25 and 1.0 < c.y < 3.8 and r > 1.55:
            S["aanbouw"].append(e)
        elif 1.5 < r < 1.9 and lo.z > -0.05:
            S["wand"].append(e)
        elif r > 1.95:
            S["rots"].append(e)
        # de rest (voorkant aanbouw binnen de ronde muur) valt weg
    Hd = {k: [] for k in ("stijl", "bank", "hek", "binnen")}
    for e in hout.eil:
        c, lo, hi = e["c"], e["lo"], e["hi"]
        if straal(c) > 2.5 and not (AX0 - 0.1 < c.x < AX1 + 0.1 and c.y < AY1 + 0.1):
            Hd["hek"].append(e)
        elif hi.z > 1.8 and lo.z < 0.01 and (hi - lo).x < 0.3:
            Hd["stijl"].append(e)
        elif 0.45 < lo.z < 0.55 and hi.z < 0.6:
            Hd["bank"].append(e)
        else:
            Hd["binnen"].append(e)
    Sp = {k: [] for k in ("wand", "vloer", "schoorsteen", "aanbouw")}
    for e in specie.eil:
        c, lo, hi = e["c"], e["lo"], e["hi"]
        if lo.z > 2.0:
            Sp["schoorsteen"].append(e)
        elif hi.z < 0.02:
            Sp["vloer"].append(e)
        elif straal(c) < 0.3:
            Sp["wand"].append(e)
        else:
            Sp["aanbouw"].append(e)
    G = [e for e in gras.eil if straal(e["c"]) > 2.0 and not (AX0 - 0.2 < e["c"].x < AX1 + 0.2 and e["c"].y > 0.8)]
    for naam, D in (("steen", S), ("hout", Hd), ("specie", Sp)):
        log(naam, {k: len(v) for k, v in D.items()})
    log("gras buiten", len(G), "van", len(gras.eil))
    return S, Hd, Sp, G


def faces(lst):
    return [f for e in lst for f in e["f"]]


# --- Binnenkant van de muren -------------------------------------------------------------
# vensters in de buitenstenen zonder openingen (graden) en waar ze gespiegeld binnen terechtkomen
BINNEN_ROND = [((200.5, 255.5), -58.5), ((100.0, 143.5), -3.5), ((200.5, 255.5), 40.0), ((319.5, 350.0), 95.0),
               ((100.0, 130.0), 125.5)]


def binnen_rond(dst, st, wand, ztop):
    """Gespiegelde kopieen van buitenstenen op de binnenkant van de ronde muur (hoek -58,5..155,5: daar kijk je
    in stand 2 en 3 over de muur naar binnen)."""
    n = 0
    for (a0, a1), t0 in BINNEN_ROND:
        rot = math.radians(t0 - a0)
        for e in wand:
            a = hoek(e["c"])
            if not (a0 <= a < a1) or e["c"].z > ztop:
                continue

            def f(co, rot=rot):
                dx, dy = co.x - HX, co.y - HY
                r, th = math.hypot(dx, dy), math.atan2(dy, dx) + rot
                r2 = 2 * kern_r(co.z) - r
                return Vector((HX + r2 * math.cos(th), HY + r2 * math.sin(th), co.z))
            kopie(dst, st, e["f"], f, flip=True)
            n += 1
    return n


def binnen_aanbouw(dst, st, aanbouw, ztop):
    """De -X-stenen van de aanbouw (buitenkant x = -0,34) als binnenkant van de +X- en +Y-muur."""
    x_k = AX0 + 0.06                                    # kern van de -X-muur
    bron = [(e, 0.0) for e in aanbouw if e["c"].y > 1.5]
    # deurgat (y 2,1..2,9 tot 1,5 m) dicht met de stenen van y 2,9..3,7, 0,8 m opgeschoven
    bron += [(e, -0.8) for e in aanbouw if 2.9 < e["c"].y < 3.7 and e["hi"].z < 1.55]
    n = 0
    for e, dy in bron:
        if e["c"].z > ztop:
            continue
        y = e["c"].y + dy
        if 1.45 < y < 3.5:                              # +X-muur (kern x = 1,6), binnenkant kijkt naar -X
            kopie(dst, st, e["f"], lambda co, dy=dy: Vector((co.x - x_k + AX1, co.y + dy, co.z)))
            n += 1
        xn = 3.33 - y                                   # +Y-muur (kern y = 3,62): 90 graden gedraaid
        if -0.2 < xn < 1.45:
            kopie(dst, st, e["f"], lambda co, dy=dy: Vector((3.33 - (co.y + dy), AY1 - 0.03 + (co.x - x_k), co.z)))
            n += 1
    return n


def kernen(dst, sp, Sp, z):
    """Specie van de ronde muur en de aanbouw tot z, met afdekstrook; vloer mee."""
    tmp = bmesh.new()
    kopie(tmp, sp, faces(Sp["wand"]))
    kopie(tmp, sp, faces(Sp["aanbouw"]))
    snij(tmp, z if z > WALL_H else z - 0.02)
    # aanbouwkern: dak en -Y-kant weg (die staan in de hut), en wat binnen de ronde muur valt
    for y in (1.29, 1.36):
        geom = tmp.verts[:] + tmp.edges[:] + tmp.faces[:]
        bmesh.ops.bisect_plane(tmp, geom=geom, plane_co=(0, y, 0), plane_no=(0, 1, 0))
    weg = []
    for f in tmp.faces:
        c = f.calc_center_median()
        if f.calc_area() > 0 and abs(f.normal.z) > 0.9 and c.z > 1.0:
            weg.append(f)                                # dak van de aanbouwkern / deksel van de ronde kern
        elif AX0 < c.x < AX1 + 0.05 and c.y > 0.9 and (straal(c) < kern_r(c.z) - 0.02 or abs(c.y - (AY0 + 0.03)) < 0.02):
            weg.append(f)                                # aanbouwkern binnen de ronde muur en zijn -Y-kant
    bmesh.ops.delete(tmp, geom=list(set(weg)), context="FACES")
    kap(tmp, z - 0.05 if z < WALL_H else WALL_H - 0.05, zop=-0.02 if z < WALL_H else 0.0)
    kopie(tmp, sp, faces(Sp["vloer"]))
    me = bpy.data.meshes.new("_k")
    tmp.to_mesh(me)
    tmp.free()
    dst.from_mesh(me)
    bpy.data.meshes.remove(me)


# --- Standen -----------------------------------------------------------------------------
def voetafdruk_sd(x, y):
    """Afstand tot de rand van de voetafdruk (cirkel + aanbouw, 15 cm ruim); positief = binnen."""
    d_c = HUT_R + 0.15 - math.hypot(x - HX, y - HY)
    d_r = min(x - (AX0 - 0.15), (AX1 + 0.15) - x, y - (AY0 - 0.15), (AY1 + 0.15) - y)
    return max(d_c, d_r)


def omtrek():
    """Hoeken van het uitgezette plan: aanbouwhoeken + de cirkel aan de voorkant."""
    R = HUT_R + 0.25
    x0, x1, y1 = AX0 - 0.2, AX1 + 0.2, AY1 + 0.2
    a_l = math.degrees(math.atan2(math.sqrt(R * R - (x0 - HX) ** 2), x0 - HX))   # snijpunt met x = x0
    a_r = math.degrees(math.atan2(math.sqrt(R * R - (x1 - HX) ** 2), x1 - HX))
    P = [Vector((x1, HY + math.sqrt(R * R - (x1 - HX) ** 2), 0)), Vector((x1, y1, 0)), Vector((x0, y1, 0)),
         Vector((x0, HY + math.sqrt(R * R - (x0 - HX) ** 2), 0))]
    n = 9
    for k in range(1, n):
        a = math.radians(a_l + (a_r + 360 - a_l) * k / n)
        P.append(Vector((HX + R * math.cos(a), HY + R * math.sin(a), 0)))
    return P


def aarde(coll):
    import natuur_lib as L
    b = L.Bouwer()
    stap = 0.12
    xs = np.arange(-1.5, 2.95, stap)
    ys = np.arange(-2.1, 4.1, stap)
    idx = {}

    def z_van(x, y):
        sd = voetafdruk_sd(x, y) + 0.05 * noise.noise(Vector((x * 1.7, y * 1.7, 0.3)))
        k = min(max(sd / 0.25, 0.0), 1.0)
        return k * (0.018 + 0.008 * noise.noise(Vector((x * 6, y * 6, 1.1)))) - 0.004, sd
    rand = lambda x, y: voetafdruk_sd(x, y) + 0.05 * noise.noise(Vector((x * 1.7, y * 1.7, 0.3)))
    for j, y in enumerate(ys):
        for i, x in enumerate(xs):
            sd = sd0 = rand(x, y)
            if sd < 0:                                   # buiten: op de rand leggen (geen trapjes)
                for _ in range(3):
                    gx = (rand(x + 0.01, y) - rand(x - 0.01, y)) / 0.02
                    gy = (rand(x, y + 0.01) - rand(x, y - 0.01)) / 0.02
                    g2 = gx * gx + gy * gy or 1.0
                    sd = rand(x, y)
                    x, y = x - sd * gx / g2, y - sd * gy / g2
            z, _ = z_van(x, y)
            idx[i, j] = (b.v((x, y, max(z, -0.004))), sd0)
    for j in range(len(ys) - 1):
        for i in range(len(xs) - 1):
            q = [idx[i, j], idx[i + 1, j], idx[i + 1, j + 1], idx[i, j + 1]]
            if max(s for _, s in q) < 0:
                continue
            b.f([v for v, _ in q], [(b.V[v][0] / 1.6, b.V[v][1] / 1.6) for v, _ in q], 0)
    grond = L.ph("farm_soil", "bouwgrond", factor=(0.74, 0.69, 0.62))
    o = L.obj("bouwgrond", b.mesh("bouwgrond", [grond]), coll)
    for a in [a.name for a in o.data.color_attributes]:
        o.data.color_attributes.remove(o.data.color_attributes[a])
    if "wind" in o.data.uv_layers:
        o.data.uv_layers.remove(o.data.uv_layers["wind"])
    return o


def bouw_stand(s, B, coll):
    st, hout, sp, gras = B["st"], B["hout"], B["sp"], B["gras"]
    S, Hd, Sp, G = B["S"], B["Hd"], B["Sp"], B["G"]
    stijl = Stijl(hout, [e for e in Hd["stijl"] if 1.6 < straal(e["c"]) < 1.9 and e["c"].y < 0][0])
    rnd = random.Random(40 + s)
    b_st, b_h, b_sp = bmesh.new(), bmesh.new(), bmesh.new()
    kopie(b_sp, gras, faces(G))                          # gras buiten de voetafdruk blijft staan
    touw_uv = None
    for e in Hd["hek"]:
        if 300 < e["n"] < 500:                           # sjorring
            f = e["f"][len(e["f"]) // 2]
            touw_uv = f.loops[0][hout.uv].uv.copy()
            break
    objs = []
    if s == 1:
        objs.append(aarde(coll))
        P = omtrek()
        for p in P:                                      # paaltjes, 45 cm boven de grond
            q = p + Vector((rnd.uniform(-0.02, 0.02), rnd.uniform(-0.02, 0.02), 0))
            stijl.balk(b_h, q + Vector((0, 0, -0.1)), q + Vector((rnd.uniform(-0.02, 0.02), rnd.uniform(-0.02, 0.02), 0.45)),
                       0.055, 0.05, rol=rnd.uniform(0, 3))
        for a, c in zip(P, P[1:] + P[:1]):               # touw van paal naar paal, iets doorgezakt
            pts = [a.lerp(c, t) + Vector((0, 0, 0.36 - 0.03 * math.sin(math.pi * t))) for t in np.linspace(0, 1, 6)]
            touw(b_h, pts, touw_uv)
    else:
        z = SNIJ[s]
        # buitenstenen
        for e in S["wand"] + S["aanbouw"]:
            if e["c"].z < z:
                kopie(b_st, st, e["f"])
        b_in = bmesh.new()
        n_in = binnen_rond(b_in, st, S["wand"], z) + binnen_aanbouw(b_in, st, S["aanbouw"], z)
        log("stand", s, "binnenstenen", n_in, "dichtgemaakt", sluit(b_in), "bovenkant", bovenkant_licht(b_in, z - 0.3))
        # (schoorsteen en losse stenen komen hieronder; die worden pas aan het eind dichtgemaakt)
        # kozijnen (steen) en stijlen (hout): doorsnijden op de muurhoogte, of heel in stand 3
        b_k, b_p = bmesh.new(), bmesh.new()
        kopie(b_k, st, faces(S["kozijn"]))
        kopie(b_p, hout, faces(Hd["stijl"]))
        if s == 2:
            snij(b_k, z, dicht=True)
            snij(b_p, z - 0.04, dicht=True)
        kopie(b_h, hout, faces(Hd["bank"]))
        log("stand", s, "buitenstenen dichtgemaakt", sluit(b_st), "bovenkant", bovenkant_licht(b_st, z - 0.3))
        for t, dst in ((b_k, b_st), (b_p, b_h)):
            me = bpy.data.meshes.new("_t")
            t.to_mesh(me)
            t.free()
            dst.from_mesh(me)
            bpy.data.meshes.remove(me)
        kernen(b_sp, sp, Sp, z)
        kopie(b_st, st, faces(S["rots"]))
        # losse stenen: kleinere kopieen van de rotsen rond het plan
        for k in range(5 if s == 2 else 3):
            e = S["rots"][rnd.randrange(len(S["rots"]))]
            a = math.radians(rnd.choice((205, 228, 250, 300, 330, 140, 120)) + rnd.uniform(-8, 8))
            rr = HUT_R + rnd.uniform(0.5, 1.1)
            doel = Vector((HX + rr * math.cos(a), HY + rr * math.sin(a), 0))
            sc = rnd.uniform(0.35, 0.6)
            M = (Matrix.Translation(doel) @ Matrix.Rotation(rnd.uniform(0, 6.28), 4, "Z") @ Matrix.Scale(sc, 4)
                 @ Matrix.Translation((-e["c"].x, -e["c"].y, 0)))
            kopie(b_st, st, e["f"], lambda co, M=M: M @ co)
        if s == 3:
            kopie(b_st, st, faces(S["stoep"] + S["haard"]))
            # schoorsteen half: de onderste lagen, op de muur gezet
            dz = z - 2.7
            t = bmesh.new()
            for e in S["schoorsteen"]:
                if e["c"].z < 3.4:
                    kopie(t, st, e["f"], lambda co: Vector((co.x, co.y, co.z + dz)))
            sluit(t)
            me = bpy.data.meshes.new("_t")
            t.to_mesh(me)
            t.free()
            b_st.from_mesh(me)
            bpy.data.meshes.remove(me)
            t = bmesh.new()
            kopie(t, sp, faces(Sp["schoorsteen"]))
            snij(t, 3.4)
            bmesh.ops.translate(t, verts=t.verts, vec=(0, 0, dz))
            me = bpy.data.meshes.new("_t")
            t.to_mesh(me)
            t.free()
            b_sp.from_mesh(me)
            bpy.data.meshes.remove(me)
            # dakspanten als kegel, vrij van de schoorsteen (284 graden)
            top = Vector((HX, HY, 4.05))
            for k in range(12):
                a = math.radians(284 + 15 + 30 * k)
                voet = Vector((HX + 1.68 * math.cos(a), HY + 1.68 * math.sin(a), z - 0.02))
                eind = top + (top - voet).normalized() * 0.28
                stijl.balk(b_h, voet, eind, 0.1, 0.09, rol=rnd.uniform(-0.3, 0.3))
            # gording halverwege: ring van korte balken
            zr, Rr = z + (top.z - z) * 0.45, 1.68 * 0.55 + 0.05
            for k in range(12):
                a0, a1 = math.radians(284 + 15 + 30 * k - 1), math.radians(284 + 15 + 30 * (k + 1) + 1)
                stijl.balk(b_h, Vector((HX + Rr * math.cos(a0), HY + Rr * math.sin(a0), zr)),
                           Vector((HX + Rr * math.cos(a1), HY + Rr * math.sin(a1), zr)), 0.07, 0.07)
            # ladder tegen de muur, links van het raam (voor de camera)
            a = math.radians(236)
            u = Vector((math.cos(a), math.sin(a), 0))
            t_ = Vector((-math.sin(a), math.cos(a), 0))
            voet = H + u * (HUT_R + 0.85)
            kop = H + u * (HUT_R + 0.12) + Vector((0, 0, z + 0.25))
            for zij in (-0.22, 0.22):
                stijl.balk(b_h, voet + t_ * zij, kop + t_ * zij, 0.06, 0.05)
            for k in range(1, 8):
                p = voet.lerp(kop, k / 8.3)
                stijl.balk(b_h, p - t_ * 0.25, p + t_ * 0.25, 0.04, 0.035)
        o_in = naar_obj("stenen_binnen", b_in, st.mat, coll)
        decimeer(o_in, 0.55)                             # alleen van boven gezien, over de muur
        objs.append(o_in)
    for naam, bm, mat in (("stenen", b_st, st.mat), ("hout", b_h, hout.mat), ("specie", b_sp, sp.mat)):
        if len(bm.faces):
            objs.append(naar_obj(naam, bm, mat, coll))
        bm.free()
    return objs


def exporteer(pad, objs):
    for o in bpy.context.view_layer.objects:
        o.select_set(False)
    for o in objs:
        o.select_set(True)
    bpy.ops.export_scene.gltf(filepath=pad, export_format="GLB", use_selection=True, export_apply=True,
                              export_tangents=True, export_image_format="AUTO", export_cameras=False,
                              export_lights=False, export_extras=False, export_animations=False,
                              export_vertex_color="NONE")
    log("export", os.path.basename(pad), f"{os.path.getsize(pad) / 1e6:.1f} MB", tris(objs), "tris")


def bouw():
    bpy.ops.wm.open_mainfile(filepath=RT_BLEND)
    sc = bpy.context.scene
    ob = bpy.data.objects
    B = {"st": Bron(ob["stenen"]), "hout": Bron(ob["hout"]), "sp": Bron(ob["specie"]), "gras": Bron(ob["gras"])}
    B["S"], B["Hd"], B["Sp"], B["G"] = indelen(B["st"], B["hout"], B["sp"], B["gras"])
    ankers = [ob[n] for n in ("deur_voor_drempel", "deur_aanbouw_drempel")]
    af = tris([o for o in ob if o.type == "MESH" and "lod1" not in o.name])
    for o in list(ob):
        if o.type == "MESH":
            o.name = "_bron_" + o.name                   # de namen zijn voor de standen
    for o in list(sc.objects):
        if o.type == "MESH":
            o.hide_set(True)
            o.hide_render = True
    stat = {}
    for s in STANDEN:
        coll = bpy.data.collections.new(f"stand{s}")
        sc.collection.children.link(coll)
        objs = bouw_stand(s, B, coll)
        for o in objs:
            log("   ", s, o.name, tris([o]))
        exporteer(GLB(s), objs + ankers)
        stat[s] = tris(objs)
        for o in objs:
            bpy.data.objects.remove(o)
    log("driehoeken", stat, "af-hut", af)


# --- Preview: vier standen naast elkaar ----------------------------------------------------
def preview():
    bpy.ops.wm.open_mainfile(filepath=HUT_BLEND)
    sc = bpy.context.scene
    for o in [o for o in sc.objects if o.type in ("MESH", "CURVES")]:
        bpy.data.objects.remove(o)
    for n in ("zon_grond", "vul_grond"):
        if n in sc.objects:
            bpy.data.objects.remove(sc.objects[n])
    for n in ("zon", "vul"):
        sc.objects[n].light_linking.receiver_collection = None
        sc.objects[n].light_linking.blocker_collection = None
    sc.render.engine = "BLENDER_EEVEE"
    sc.eevee.taa_render_samples = 64
    try:
        sc.eevee.use_raytracing = True
        sc.eevee.use_shadows = True
    except AttributeError:
        pass
    sc.render.film_transparent = True
    panelen = []
    for pad in [GLB(1), GLB(2), GLB(3), os.path.join(HERE, "peasant_hut_rt.glb")]:
        voor = set(sc.objects)
        bpy.ops.import_scene.gltf(filepath=pad)
        nieuw = [o for o in sc.objects if o not in voor]
        sc.render.filepath = os.path.join(bpy.app.tempdir, f"_stand_{len(panelen)}.png")
        bpy.ops.render.render(write_still=True)
        panelen.append(sc.render.filepath)
        for o in nieuw:
            bpy.data.objects.remove(o)
    rijen = []
    bg = np.array([0.32, 0.36, 0.30])
    for p in panelen:
        img = bpy.data.images.load(p, check_existing=False)
        a = np.array(img.pixels[:], np.float32).reshape(img.size[1], img.size[0], 4)
        bpy.data.images.remove(img)
        rijen.append(a[..., :3] * a[..., 3:4] + bg * (1 - a[..., 3:4]))
    h = min(r.shape[0] for r in rijen)
    out = np.concatenate([r[:h] for r in rijen], axis=1)
    img = bpy.data.images.new("hut_standen", out.shape[1], out.shape[0])
    img.pixels.foreach_set(np.concatenate([out, np.ones((*out.shape[:2], 1))], 2).astype(np.float32).ravel())
    os.makedirs(os.path.join(HERE, "render"), exist_ok=True)
    img.filepath_raw = os.path.join(HERE, "render", "hut_standen.png")
    img.file_format = "PNG"
    img.save()
    log("preview ->", img.filepath_raw)


if __name__ == "__main__":
    if "alleen_preview" not in OPTS:
        bouw()
    if "preview" in OPTS or "alleen_preview" in OPTS:
        preview()
    log("KLAAR")
