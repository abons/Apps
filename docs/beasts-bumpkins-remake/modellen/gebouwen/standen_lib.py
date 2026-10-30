"""Gedeelde code voor de bouwstanden: standen snijden uit het afgewerkte (gebakken) game-model.

Gebruikt door `../peasant_hut_standen.py` (de hut, eigen indeling) en `standen.py` (de vier gebouwen, met een
configuratie per gebouw). Alles werkt op de gebakken eilanden van een `*_rt.blend` met hun eigen UV's, dus de
standen lopen gelijk door met de af-glb en gebruiken dezelfde atlassen.

- Bron: een bronmesh als bmesh met zijn losse eilanden (midden, grenzen, vlakken).
- kopie / snij / sluit / bovenkant_licht / kap: vlakken overnemen, met een vlak doorsnijden (UV's lopen mee),
  open randen dichtmaken, zwarte contactschaduw op bovenvlakken wegwerken, afdekstrook op een kern.
- hol: een dichte kern (doos) als muurschil met binnenkant en muurkop, met deuropeningen.
- Sjabloon: een balk/paal uit de af-glb als sjabloon voor nieuwe balken (dakspanten, paaltjes).
- touw, aarde (stand 1), exporteer, plaat (previewplaat van de standen naast elkaar).
"""
import math
import os
import sys

import bmesh
import bpy
import numpy as np
from mathutils import Matrix, Vector, noise

MODELLEN = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if os.path.join(MODELLEN, "natuur") not in sys.path:
    sys.path.insert(0, os.path.join(MODELLEN, "natuur"))


def log(*a):
    print("[standen]", *a, flush=True)


# --- Eilanden ----------------------------------------------------------------------------
class Bron:
    """Een bronmesh als bmesh met zijn losse eilanden (midden, grenzen, vlakken)."""

    def __init__(self, ob):
        self.ob = ob
        self.bm = bmesh.new()
        self.bm.from_mesh(ob.data)
        if ob.matrix_world != Matrix.Identity(4):        # alles in wereldcoordinaten (de hut staat al zo)
            self.bm.transform(ob.matrix_world)
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
                             "n": sum(len(g.verts) - 2 for g in fs), "co": co})


def faces(lst):
    return [f for e in lst for f in e["f"]]


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


def voeg(dst, bm):
    """bm (wordt vrijgegeven) in dst samenvoegen."""
    me = bpy.data.meshes.new("_t")
    bm.to_mesh(me)
    bm.free()
    dst.from_mesh(me)
    bpy.data.meshes.remove(me)


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
    """Open randen dicht (de af-glb snijdt soms de achterkant van een steen weg; zonder dak kijk je erin)."""
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
    """Bovenvlakken van de bovenste laag: in de af-glb lag daar de volgende laag op, dus de bake is daar
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


def kap(bm, zmin, breed=0.11, zop=0.0):
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


def in_doos(p, doos):
    lo, hi = doos
    return all(lo[i] <= p[i] <= hi[i] for i in range(3))


def gaten(bm, dozen):
    """Deuropeningen: snijd langs de randen van elke doos en gooi de vlakken met hun midden erin weg."""
    for lo, hi in dozen:
        for as_, w in ((0, lo.x), (0, hi.x), (1, lo.y), (1, hi.y), (2, hi.z)):
            no = [0, 0, 0]
            no[as_] = 1
            co = [0, 0, 0]
            co[as_] = w
            geom = bm.verts[:] + bm.edges[:] + bm.faces[:]
            bmesh.ops.bisect_plane(bm, geom=geom, plane_co=co, plane_no=no)
    weg = [f for f in bm.faces if any(in_doos(f.calc_center_median(), d) for d in dozen)]
    bmesh.ops.delete(bm, geom=weg, context="FACES")
    return len(weg)


def hol(bm, z, dik, dozen=()):
    """Een dichte kern (doos) als muurschil: boven z weg, deuropeningen eruit, dan een binnenkant (kopie naar het
    midden geschoven met `dik`, omgedraaid) en een muurkop/dagkant tussen elke open rand en zijn binnenkopie.
    UV van muurkop en dagkant: die van het buitenvlak ernaast (de kleur van de zijkant)."""
    geom = bm.verts[:] + bm.edges[:] + bm.faces[:]
    bmesh.ops.bisect_plane(bm, geom=geom, plane_co=(0, 0, z), plane_no=(0, 0, 1), clear_outer=True)
    if dozen:
        gaten(bm, dozen)
    if not bm.verts:
        return
    uv = bm.loops.layers.uv.verify()
    co = np.array([v.co[:] for v in bm.verts])
    lo, hi = co.min(0), co.max(0)
    c = (lo + hi) / 2
    half = np.maximum((hi - lo) / 2, 1e-6)
    sx, sy = max(half[0] - dik, 0.02) / half[0], max(half[1] - dik, 0.02) / half[1]
    rand = [(e.link_loops[0], e) for e in bm.edges if e.is_boundary]
    vmap = {}
    for v in list(bm.verts):
        vmap[v] = bm.verts.new((c[0] + (v.co.x - c[0]) * sx, c[1] + (v.co.y - c[1]) * sy, v.co.z))
    for f in list(bm.faces):
        vs = [vmap[v] for v in f.verts][::-1]
        uvs = [l[uv].uv.copy() for l in f.loops][::-1]
        try:
            nf = bm.faces.new(vs)
        except ValueError:
            continue
        nf.smooth = f.smooth
        for l, u in zip(nf.loops, uvs):
            l[uv].uv = u
    for l, e in rand:
        a, b = l.vert, l.link_loop_next.vert
        u = l[uv].uv.copy()
        try:
            nf = bm.faces.new([b, a, vmap[a], vmap[b]])
        except ValueError:
            continue
        nf.smooth = False
        for lp in nf.loops:
            lp[uv].uv = u


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


# --- Balken uit een sjabloon ---------------------------------------------------------------
class Sjabloon:
    """Een balk of paal uit de af-glb (as-gericht eiland) als sjabloon: langste as = lengte, de andere twee de
    doorsnede. balk() zet een geschaalde kopie (zelfde hout op de atlas) tussen p0 en p1."""

    def __init__(self, bron, eil):
        self.bron, self.f = bron, eil["f"]
        lo, hi = eil["lo"], eil["hi"]
        ext = hi - lo
        a = max(range(3), key=lambda i: ext[i])
        b, c = [i for i in range(3) if i != a]
        self.a, self.b, self.c, self.lo, self.ext, self.mid = a, b, c, lo, ext, (lo + hi) / 2

    def balk(self, dst, p0, p1, w, d, rol=0.0):
        p0, p1 = Vector(p0), Vector(p1)
        ax = (p1 - p0).normalized()
        hulp = Vector((0, 0, 1)) if abs(ax.z) < 0.95 else Vector((1, 0, 0))
        ex = ax.cross(hulp).normalized()
        ey = ax.cross(ex).normalized()
        ex, ey = (Matrix.Rotation(rol, 3, ax) @ ex), (Matrix.Rotation(rol, 3, ax) @ ey)
        L = (p1 - p0).length
        a, b, c, lo, ext, mid = self.a, self.b, self.c, self.lo, self.ext, self.mid

        def f(co):
            return (p0 + ax * ((co[a] - lo[a]) / ext[a] * L) + ex * ((co[b] - mid[b]) / max(ext[b], 1e-6) * w)
                    + ey * ((co[c] - mid[c]) / max(ext[c], 1e-6) * d))
        flip = ex.cross(ey).dot(ax) < 0
        # de winding volgt de spiegeling van de afbeelding (as-volgorde a,b,c tegenover ax,ex,ey)
        par = 1 if (b - a) % 3 == 1 else -1
        kopie(dst, self.bron, self.f, f, flip=(flip if par > 0 else not flip))


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


# --- Stand 1: bouwgrond --------------------------------------------------------------------
def aarde(coll, sd_fn, xs, ys, hoogte=0.018, rij_vast=False):
    """Aangestampte aarde (farm_soil, tegelbaar) op de voetafdruk: sd_fn(x, y) = afstand tot de rand, positief
    binnen. Het raster loopt over xs x ys; buiten de rand worden de punten op de rand gelegd (geen trapjes).
    ⚠️ rij_vast=False houdt de fout van de hut: een verschoven y liep door naar de rest van de rij (bij een
    holle voetafdruk, zoals de molen, valt dan een vleugel weg). De hut blijft zo byte-gelijk; nieuw: True."""
    import natuur_lib as L
    b = L.Bouwer()
    idx = {}

    def z_van(x, y):
        sd = sd_fn(x, y) + 0.05 * noise.noise(Vector((x * 1.7, y * 1.7, 0.3)))
        k = min(max(sd / 0.25, 0.0), 1.0)
        return k * (hoogte + 0.008 * noise.noise(Vector((x * 6, y * 6, 1.1)))) - 0.004, sd
    rand = lambda x, y: sd_fn(x, y) + 0.05 * noise.noise(Vector((x * 1.7, y * 1.7, 0.3)))
    for j, y in enumerate(ys):
        y_rij = y
        for i, x in enumerate(xs):
            if rij_vast:
                y = y_rij
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


def veelhoek_sd(P, marge):
    """Afstand tot de rand van veelhoek P (xy-punten, tegen de klok in of mee), `marge` ruimer; positief = binnen."""
    P = [tuple(p) for p in P]

    def sd(x, y):
        d, binnen = 1e9, False
        for (ax, ay), (bx, by) in zip(P, P[1:] + P[:1]):
            vx, vy, wx, wy = bx - ax, by - ay, x - ax, y - ay
            t = min(max((wx * vx + wy * vy) / (vx * vx + vy * vy), 0.0), 1.0)
            d = min(d, math.hypot(wx - t * vx, wy - t * vy))
            if (ay > y) != (by > y) and x < ax + (y - ay) * vx / vy:
                binnen = not binnen
        return (d if binnen else -d) + marge
    return sd


def uitzetten(P, marge, per_m=1.1):
    """Hoeken van het uitgezette plan (veelhoek P, `marge` naar buiten) met tussenpaaltjes; lange zijden krijgen
    er een per ~1/per_m meter."""
    n = len(P)
    rich = 1 if sum((P[(i + 1) % n][0] - P[i][0]) * (P[(i + 1) % n][1] + P[i][1]) for i in range(n)) < 0 else -1
    Q = []
    for i in range(n):
        a, b, c = Vector((*P[i - 1], 0)), Vector((*P[i], 0)), Vector((*P[(i + 1) % n], 0))
        n0 = Vector(((b - a).y, -(b - a).x, 0)).normalized() * rich
        n1 = Vector(((c - b).y, -(c - b).x, 0)).normalized() * rich
        k = (n0 + n1).normalized()
        Q.append(b + k * (marge / max(k.dot(n0), 0.3)))
    out = []
    for i in range(n):
        a, b = Q[i], Q[(i + 1) % n]
        m = max(1, round((b - a).length * per_m / 1.5))
        out += [a.lerp(b, k / m) for k in range(m)]
    return out


# --- Export en previewplaat ------------------------------------------------------------------
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


def plaat(blend, glbs, uit, weg_namen=(), procent=None, bg=(0.32, 0.36, 0.30)):
    """Previewplaat: elke glb in EEVEE met camera en licht van `blend` (meshes en halmen eruit), naast elkaar."""
    bpy.ops.wm.open_mainfile(filepath=blend)
    sc = bpy.context.scene
    for o in [o for o in sc.objects if o.type in ("MESH", "CURVES")]:
        bpy.data.objects.remove(o)
    for n in weg_namen:
        if n in sc.objects:
            bpy.data.objects.remove(sc.objects[n])
    for o in sc.objects:
        if o.type == "LIGHT":
            o.light_linking.receiver_collection = None
            o.light_linking.blocker_collection = None
    sc.render.engine = "BLENDER_EEVEE"
    sc.eevee.taa_render_samples = 64
    if procent:
        sc.render.resolution_percentage = procent
    try:
        sc.eevee.use_raytracing = True
        sc.eevee.use_shadows = True
    except AttributeError:
        pass
    sc.render.film_transparent = True
    panelen = []
    for pad in glbs:
        voor = set(sc.objects)
        bpy.ops.import_scene.gltf(filepath=pad)
        nieuw = [o for o in sc.objects if o not in voor]
        sc.render.filepath = os.path.join(bpy.app.tempdir, f"_stand_{len(panelen)}.png")
        bpy.ops.render.render(write_still=True)
        panelen.append(sc.render.filepath)
        for o in nieuw:
            bpy.data.objects.remove(o)
    rijen = []
    bg = np.array(bg)
    for p in panelen:
        img = bpy.data.images.load(p, check_existing=False)
        a = np.array(img.pixels[:], np.float32).reshape(img.size[1], img.size[0], 4)
        bpy.data.images.remove(img)
        rijen.append(a[..., :3] * a[..., 3:4] + bg * (1 - a[..., 3:4]))
    h = min(r.shape[0] for r in rijen)
    out = np.concatenate([r[:h] for r in rijen], axis=1)
    img = bpy.data.images.new(os.path.basename(uit), out.shape[1], out.shape[0])
    img.pixels.foreach_set(np.concatenate([out, np.ones((*out.shape[:2], 1))], 2).astype(np.float32).ravel())
    os.makedirs(os.path.dirname(uit), exist_ok=True)
    img.filepath_raw = uit
    img.file_format = "PNG"
    img.save()
    log("preview ->", uit)
