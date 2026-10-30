"""Wolf uit TRELLIS (AI, beeld -> 3D) met het skelet en de clips van de procedurele wolf
-> spel/assets/wolf_trellis.glb + donkere_wolf_trellis.glb (Blender 5.2 headless -> Godot 4).

Draaien:
  blender -b -P wolf_trellis.py -- [poses] [zij] [detail] [blend] [geen_export]   (werkwijze: README.md)
- `zij`: preview/wolf_trellis_zij.png (zij- en bovenaanzicht met raster per 10 cm en het skelet erover; om
  de MAAT hieronder op de vorm te zetten). Bevat geen sprites/concept: mag in git.
- `poses`: preview/wolf_trellis_v2_poses.png (standen uit alle clips, iso + van opzij, grijs en donker).
- `detail`: preview/wolf_trellis_detail.png (zes standen groot, vervorming nakijken; lokaal).

Invoer: lokaal/trellis/wolf_trellis.glb (gitignored; TRELLIS-Space, zie README.md in deze map). Eén mesh,
6.440 driehoeken, 1024-textuur (alleen kleur). TRELLIS kijkt al naar -Y (Blender) = Godot +Z, grond op de
laagste vertex; gesplitst op UV-naden (na samenvoegen één eiland).

Stappen: samenvoegen op afstand -> losse eilandjes weg -> schalen (schoft 0,80 m, zoals wolf.py) en
centreren (midden tussen voor- en achtervoeten op y=0) -> normalen -> (decimeren alleen boven DOEL) ->
skelet: koe_rig.bouw_rig met MAAT_T (wolf_rig.MAAT verschoven naar deze vorm) -> gewichten: bone heat
(ARMATURE_AUTO) + wolf.py-correcties (gladstrijken, kop/kaak/oren star, onderbenen per bot, romp los van
de poten) -> clips van wolf_rig.py (idle, lopen, rennen, bijten, dood) -> export.
Donkere wolf: dezelfde glb met een kleurbewerkte textuur (zwart, witte borst/keel, ogen blijven rood).
"""
import json
import math
import os
import sys
import time

import bmesh
import bpy
import numpy as np
from mathutils import Matrix, Vector

HERE = os.path.dirname(os.path.abspath(__file__))
MOD = os.path.dirname(HERE)
ROOT = os.path.dirname(MOD)
sys.path.insert(0, HERE)
argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
OPTS = {a.split("=")[0]: (a.split("=", 1)[1] if "=" in a else "1") for a in argv}
sys.argv = sys.argv[:sys.argv.index("--")] if "--" in sys.argv else sys.argv   # wolf.py leest geen opties
import wolf_rig as R  # noqa: E402
import dieren_basis as BM  # noqa: E402
import koe as KO  # noqa: E402  (glad_gewichten, onderbenen, romp_los, kop_assen, Skelet)

BRON = os.path.join(ROOT, "lokaal", "trellis", "wolf_trellis.glb")
ASSETS = os.path.join(ROOT, "spel", "assets")
GLB = {"wolf": os.path.join(ASSETS, "wolf_trellis.glb"), "donker": os.path.join(ASSETS, "donkere_wolf_trellis.glb")}
PREV = os.path.join(HERE, "preview")
SCHOFT = 0.80
DOEL = 8000                     # driehoeken; TRELLIS levert 6.440, dus niet decimeren
T0 = time.time()
gladstap = BM.gladstap


def log(*a):
    print(f"[wolf_trellis {time.time() - T0:6.1f}s]", *a, flush=True)


KO.log = log

# Skelet op de TRELLIS-vorm (y, z in m na schalen; -y = voor). Afgelezen uit preview/wolf_trellis_zij.png.
MAAT_T = dict(R.MAAT)
MAAT_T.update({
    "heup": (0.40, 0.64),
    "rug": [(0.20, 0.665), (0.0, 0.675), (-0.18, 0.69), (-0.32, 0.70)],
    "nek": [(-0.36, 0.68), (-0.44, 0.78), (-0.49, 0.86)],
    "kop": [(-0.50, 0.88), (-0.71, 0.71)],                   # achter de oren -> neuspunt
    "kaak": [(-0.55, 0.78), (-0.69, 0.69)],
    "oor": (0.065, -0.50, 0.91), "oor_richting": (0.25, -0.15, 1.0), "oor_lengte": 0.09,
    "staart": [(0.44, 0.69), (0.50, 0.55), (0.57, 0.43), (0.65, 0.32), (0.74, 0.24)],
    "voor_x": 0.085,
    # schoftblad-top, schouder, elleboog, pols, bal, teen
    "voorbeen": [(-0.30, 0.68), (-0.375, 0.55), (-0.33, 0.40), (-0.35, 0.14), (-0.37, 0.03), (-0.415, 0.0)],
    "achter_x": 0.10,
    # heupgewricht, knie, hak, bal, teen
    "achterbeen": [(0.34, 0.60), (0.27, 0.42), (0.40, 0.22), (0.37, 0.03), (0.31, 0.0)],
    "bel": (-0.45, 0.62),
})


# --- Mesh ----------------------------------------------------------------------------------------------
def laad():
    bpy.ops.import_scene.gltf(filepath=BRON)
    o = [o for o in bpy.context.scene.objects if o.type == "MESH"][0]
    for x in list(bpy.context.scene.objects):
        if x is not o:
            bpy.data.objects.remove(x)
    o.parent = None
    o.matrix_world = Matrix.Identity(4)
    o.name = "lijf"
    o.data.name = "lijf"
    bm = bmesh.new()
    bm.from_mesh(o.data)
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-4)
    # losse eilandjes weg (alles behalve het grootste)
    bm.verts.ensure_lookup_table()
    eiland, n = {}, 0
    for v in bm.verts:
        if v.index in eiland:
            continue
        st = [v]
        eiland[v.index] = n
        while st:
            x = st.pop()
            for e in x.link_edges:
                w = e.other_vert(x)
                if w.index not in eiland:
                    eiland[w.index] = n
                    st.append(w)
        n += 1
    grootte = np.bincount(list(eiland.values()), minlength=n)
    groot = int(np.argmax(grootte))
    weg = [v for v in bm.verts if eiland[v.index] != groot]
    bmesh.ops.delete(bm, geom=weg, context="VERTS")
    log("eilanden", n, "weg", len(weg), "vertices")
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    # schalen + centreren
    P = np.array([v.co for v in bm.verts])
    z0 = P[:, 2].min()
    mid = np.abs(P[:, 0]) < 0.025
    # schoft = hoogste rugpunt tussen de voorpoten en het midden (achter de nek): neem de rugtop in het
    # bereik van de voorvoeten tot 1/3 naar achteren
    voet = P[:, 2] < z0 + 0.02
    yv, ya = P[voet & (P[:, 1] < 0), 1].mean(), P[voet & (P[:, 1] > 0), 1].mean()
    band = mid & (P[:, 1] > yv + 0.06) & (P[:, 1] < yv + 0.12)
    schoft = P[band, 2].max() - z0
    s = SCHOFT / schoft
    yc = 0.5 * (yv + ya)
    xc = 0.5 * (P[:, 0].min() + P[:, 0].max())
    for v in bm.verts:
        v.co = Vector(((v.co.x - xc) * s, (v.co.y - yc) * s, (v.co.z - z0) * s))
    bm.to_mesh(o.data)
    bm.free()
    nt = len(o.data.polygons)
    if nt > DOEL:
        m = o.modifiers.new("dec", "DECIMATE")
        m.ratio = DOEL / nt
        BM.ontkies()
        o.select_set(True)
        bpy.context.view_layer.objects.active = o
        bpy.ops.object.modifier_apply(modifier="dec")
    for p in o.data.polygons:
        p.use_smooth = True
    log("schaal", round(s, 3), "schoft (eenheden)", round(schoft, 3), "driehoeken", len(o.data.polygons),
        "maat", [round(float(x), 3) for x in np.ptp(np.array([v.co for v in o.data.vertices]), 0)])
    return o


HELDER, CONTRAST = 0.72, 1.35     # TRELLIS-kleur is licht en vlak (mediaan sRGB 0,44, p90 0,61): in het spel bijna wit


def toon(img):
    """Donkerder en meer contrast rond de mediaan (sRGB-waarden; rode ogen blijven verzadigd)."""
    w, h = img.size
    A = np.array(img.pixels[:], np.float32).reshape(-1, 4)
    rgb = A[:, :3]
    l = rgb @ np.array([0.2126, 0.7152, 0.0722], np.float32)
    m = float(np.median(l[l > 0.02]))
    A[:, :3] = np.clip(HELDER * (m + CONTRAST * (rgb - m)), 0, 1)
    img.pixels.foreach_set(A.ravel())
    img.pack()


def materiaal(o):
    """Eén Principled met de TRELLIS-kleurtextuur; ruw, niet metallic (TRELLIS levert verder niets bruikbaars)."""
    oud = o.data.materials[0]
    img = next(nd.image for nd in oud.node_tree.nodes if nd.type == "TEX_IMAGE" and nd.image)
    img.name = "wolf_trellis_kleur"
    toon(img)
    m = bpy.data.materials.new("mat_lijf")
    m.use_nodes = True
    b = m.node_tree.nodes["Principled BSDF"]
    t = m.node_tree.nodes.new("ShaderNodeTexImage")
    t.image = img
    m.node_tree.links.new(t.outputs["Color"], b.inputs["Base Color"])
    b.inputs["Roughness"].default_value = 0.92
    b.inputs["Metallic"].default_value = 0.0
    b.inputs["Specular IOR Level"].default_value = 0.3
    m.use_backface_culling = True
    o.data.materials.clear()
    o.data.materials.append(m)
    return m, t, img


def donkere_textuur(img, o):
    """Kleurbewerking: zwart met witte borst/keel. Borstmasker uit de mesh (texels via UV): voor de
    voorpoten, onder de nek, tussen de voorpoten tot halverwege; ogen (rood) blijven."""
    w, h = img.size
    A = np.array(img.pixels[:], np.float32).reshape(h, w, 4)
    rgb = A[..., :3]
    lum = rgb @ np.array([0.2126, 0.7152, 0.0722], np.float32)
    rood = is_rood(rgb)
    pos, nrm, gezet = texels(img, o)
    y, z = pos[..., 1], pos[..., 2]
    vb = MAAT_T["voorbeen"]
    # borst: voor de schouders, onder 0,72 m, boven de elleboog-ish; keel: onder de nek/kaak, naar voren gericht
    borst = gladstap(vb[1][0] + 0.10, vb[1][0] - 0.02, y) * gladstap(0.78, 0.66, z) * gladstap(0.30, 0.42, z)
    keel = (gladstap(-0.38, -0.47, y) * gladstap(-0.60, -0.54, y) * gladstap(0.80, 0.72, z) * gladstap(0.55, 0.62, z)
            * (nrm[..., 2] < 0.3))
    wit = np.clip(np.maximum(borst * gladstap(-0.1, -0.6, nrm[..., 1]), keel), 0, 1) * gezet
    # zwart: luminantie omlaag geperst, structuur blijft; borst licht (gebroken wit) met dezelfde structuur
    ln = lum / max(float(np.percentile(lum[gezet], 95)), 1e-3)
    zwart = (0.035 + 0.11 * ln)[..., None] * np.array([1.0, 0.97, 0.95], np.float32)
    licht = (0.45 + 0.35 * ln)[..., None] * np.array([1.0, 0.98, 0.95], np.float32)
    uit = zwart * (1 - wit[..., None]) + licht * wit[..., None]
    uit = np.where(rood[..., None], rgb, uit)
    uit = np.where(gezet[..., None] | rood[..., None], uit, rgb * 0.15)
    D = bpy.data.images.new("donkere_wolf_trellis_kleur", w, h)
    D.pixels.foreach_set(np.concatenate([uit, A[..., 3:]], 2).ravel())
    D.pack()
    return D


# --- Minder husky, meer B&B-wolf (v2) --------------------------------------------------------------
# TRELLIS levert een slanke, hoogkoppige husky/vos. De B&B-wolf (concept lokaal/concept/img/wolf.jpg, sprites
# wolf*) is ruig: kop laag en breed, dikke manen, zware pluimstaart, donker zadel, gloeiende rode ogen.
KOP_ZAK = 13.0          # graden: kop+hals draaien omlaag om de halsbasis
KOP_BREED = 1.13        # schedel/wangen breder (x)
NEK_BREED = 1.10
STAART_DIK, STAART_LANG, STAART_OP = 1.28, 1.15, 9.0   # x dikte, x lengte, graden naar achteren
OOR_KLEIN = 0.86       # oren kleiner (husky-oren zijn groot en hoog)
HALS_SPIL = (-0.34, 0.64)   # (y, z): draaipunt van de kopzak


def _kopzak_w(y):
    return gladstap(-0.36, -0.52, y)


def _draai(y, z, th):
    yp, zp = HALS_SPIL
    c, s_ = np.cos(th), np.sin(th)
    dy, dz = y - yp, z - zp
    return yp + dy * c - dz * s_, zp + dy * s_ + dz * c


def _draai_om(Q, c, th):
    """Draai punten Q (n, yz) om c met hoek th (n of scalar), zelfde zin als _draai."""
    th = np.broadcast_to(th, (len(Q),))
    co, si = np.cos(th), np.sin(th)
    d = Q - c
    return np.stack([c[0] + d[:, 0] * co - d[:, 1] * si, c[1] + d[:, 0] * si + d[:, 1] * co], 1)


def _op_lijn(Q, L):
    """Dichtstbijzijnde punt op polylijn L (yz) en de parameter (0..n-1) per punt Q (yz)."""
    best = np.full(len(Q), 1e9)
    C = np.zeros_like(Q)
    T = np.zeros(len(Q))
    for i in range(len(L) - 1):
        a, b = L[i], L[i + 1]
        ab = b - a
        t = np.clip((Q - a) @ ab / (ab @ ab), 0, 1)
        c = a + t[:, None] * ab
        d = np.linalg.norm(Q - c, axis=1)
        m = d < best
        best[m], C[m], T[m] = d[m], c[m], i + t[m]
    return C, T, best


def vorm(o):
    """Vorm aanpassen in de rustpose (vóór skelet en gewichten), en MAAT_T meeschuiven."""
    me = o.data
    P = np.array([v.co for v in me.vertices], float)
    x, y, z = P[:, 0].copy(), P[:, 1].copy(), P[:, 2].copy()
    # staart: dikker rond de staartlijn en langer vanaf de wortel
    L = np.array(MAAT_T["staart"], float)
    st = (y > L[0][0] - 0.02) & (np.abs(x) < 0.09)
    Q = np.stack([y, z], 1)
    C, T, d = _op_lijn(Q, L)
    st &= d < 0.12
    w = gladstap(0.0, 0.6, T) * st
    k = 1 + (STAART_DIK - 1) * w
    x = x * k
    Q2 = C + (Q - C) * k[:, None]
    wl = gladstap(0.0, 0.4, T) * st
    r0 = L[0]
    Q2 = r0 + (Q2 - r0) * (1 + (STAART_LANG - 1) * wl)[:, None]
    Q2 = _draai_om(Q2, r0, np.radians(STAART_OP) * wl)
    y, z = Q2[:, 0], Q2[:, 1]
    # oren kleiner naar hun basis toe (vóór de kopzak, in de oorspronkelijke maat)
    ox, oy, oz = MAAT_T["oor"]
    od = np.array(MAAT_T["oor_richting"], float)
    od /= np.linalg.norm(od)
    for sg in (1, -1):
        b0 = np.array((sg * ox, oy, oz))
        e = np.array((sg * od[0], od[1], od[2]))
        Pk = np.stack([x, y, z], 1)
        t = (Pk - b0) @ e
        r = np.linalg.norm(Pk - b0 - t[:, None] * e, axis=1)
        m = (t > -0.01) & (r < 0.06) & (np.sign(x) == sg) & (z > oz - 0.02)
        wo = gladstap(-0.01, 0.02, t) * m
        Pk = b0 + (Pk - b0) * (1 - (1 - OOR_KLEIN) * wo)[:, None]
        x, y, z = Pk[:, 0], Pk[:, 1], Pk[:, 2]
    # kop + hals omlaag, schedel en hals breder
    wk = _kopzak_w(y) * gladstap(0.42, 0.55, z)
    y, z = _draai(y, z, np.radians(KOP_ZAK) * wk)
    kb = gladstap(-0.47, -0.53, P[:, 1]) * gladstap(0.62, 0.72, P[:, 2])
    nb = gladstap(-0.28, -0.38, P[:, 1]) * gladstap(-0.58, -0.50, P[:, 1]) * gladstap(0.50, 0.62, P[:, 2])
    x = x * (1 + (KOP_BREED - 1) * kb + (NEK_BREED - 1) * nb)
    for i, v in enumerate(me.vertices):
        v.co = (x[i], y[i], z[i])
    me.update()

    # skelet mee: staart langer, kop/hals/oren gedraaid
    MAAT_T["staart"] = [tuple(_draai_om((r0 + (np.array(p) - r0) * STAART_LANG)[None], r0,
                                        np.radians(STAART_OP) * (1.0 if i else 0.0))[0])
                        for i, p in enumerate(MAAT_T["staart"])]
    MAAT_T["oor_lengte"] *= OOR_KLEIN

    def dr(p):
        th = np.radians(KOP_ZAK) * float(_kopzak_w(np.array(p[0])))
        a, b = _draai(np.array(p[0]), np.array(p[1]), th)
        return (float(a), float(b))
    MAAT_T["nek"] = [MAAT_T["nek"][0]] + [dr(p) for p in MAAT_T["nek"][1:]]
    MAAT_T["kop"] = [dr(p) for p in MAAT_T["kop"]]
    MAAT_T["kaak"] = [dr(p) for p in MAAT_T["kaak"]]
    ox, oy, oz = MAAT_T["oor"]
    oy2, oz2 = dr((oy, oz))
    MAAT_T["oor"] = (ox * KOP_BREED, oy2, oz2)
    rx_, ry_, rz_ = MAAT_T["oor_richting"]
    th = np.radians(KOP_ZAK)
    MAAT_T["oor_richting"] = (rx_, ry_ * np.cos(th) - rz_ * np.sin(th), ry_ * np.sin(th) + rz_ * np.cos(th))
    MAAT_T["bel"] = dr(MAAT_T["bel"])
    log("vorm: staart x", STAART_DIK, "/", STAART_LANG, "kop", KOP_ZAK, "gr omlaag, kop x", KOP_BREED)


_RASTER = {}


def texels(img, o):
    """Per texel 3D-positie en normaal in de rustpose (UV-driehoeken gerasteriseerd); eenmalig per mesh."""
    if "r" in _RASTER:
        return _RASTER["r"]
    w, h = img.size
    pos = np.zeros((h, w, 3), np.float32)
    nrm = np.zeros((h, w, 3), np.float32)
    gezet = np.zeros((h, w), bool)
    me = o.data
    uv = me.uv_layers.active.data
    V = np.array([v.co for v in me.vertices], np.float32)
    N = np.array([v.normal for v in me.vertices], np.float32)
    for p in me.polygons:
        li = list(p.loop_indices)
        for k in range(1, len(li) - 1):
            tri = [li[0], li[k], li[k + 1]]
            U = np.array([uv[i].uv for i in tri], np.float32) * [w, h]
            vi = [me.loops[i].vertex_index for i in tri]
            x0, y0 = np.floor(U.min(0)).astype(int)
            x1, y1 = np.ceil(U.max(0)).astype(int)
            x0, y0 = max(x0 - 1, 0), max(y0 - 1, 0)
            x1, y1 = min(x1 + 1, w - 1), min(y1 + 1, h - 1)
            xs, ys = np.meshgrid(np.arange(x0, x1 + 1) + 0.5, np.arange(y0, y1 + 1) + 0.5)
            d = (U[1, 1] - U[2, 1]) * (U[0, 0] - U[2, 0]) + (U[2, 0] - U[1, 0]) * (U[0, 1] - U[2, 1])
            if abs(d) < 1e-9:
                continue
            a = ((U[1, 1] - U[2, 1]) * (xs - U[2, 0]) + (U[2, 0] - U[1, 0]) * (ys - U[2, 1])) / d
            b = ((U[2, 1] - U[0, 1]) * (xs - U[2, 0]) + (U[0, 0] - U[2, 0]) * (ys - U[2, 1])) / d
            c = 1 - a - b
            m = (a > -0.02) & (b > -0.02) & (c > -0.02)
            if not m.any():
                continue
            iy, ix = (ys[m] - 0.5).astype(int), (xs[m] - 0.5).astype(int)
            bc = np.stack([a[m], b[m], c[m]], 1)
            pos[iy, ix] = bc @ V[vi]
            nrm[iy, ix] = bc @ N[vi]
            gezet[iy, ix] = True
    _RASTER["r"] = (pos, nrm, gezet)
    return _RASTER["r"]


def is_rood(rgb):
    return (rgb[..., 0] > 0.25) & (rgb[..., 0] > 2.2 * rgb[..., 1]) & (rgb[..., 0] > 2.2 * rgb[..., 2])


def tekening(img, o):
    """Koeler grijs (geen bruine husky-oren/-wangen), donker zadel over rug, nek en staart (gebroken door
    ruis), donkerder schedel/oren; de lichte keel/snuit blijft. Rode ogen blijven."""
    w, h = img.size
    A = np.array(img.pixels[:], np.float32).reshape(h, w, 4)
    rgb = A[..., :3]
    rood = is_rood(rgb)
    pos, nrm, gezet = texels(img, o)
    x, y, z = pos[..., 0], pos[..., 1], pos[..., 2]
    lum = rgb @ np.array([0.2126, 0.7152, 0.0722], np.float32)
    grijs = lum[..., None] * np.array([0.98, 1.0, 1.03], np.float32)
    rgb = 0.35 * rgb + 0.65 * grijs                                     # bijna ontzadigd, iets koel
    ru = BM.ruis(pos.reshape(-1, 3), f=(14, 9, 14), seed=7, octaven=3).reshape(h, w)
    boven = gladstap(0.05, 0.55, nrm[..., 2])
    zadel = boven * gladstap(-0.40, -0.28, y) * gladstap(0.50, 0.60, z) * gladstap(0.12, 0.02, np.abs(x) - 0.02 * ru)
    zadel = np.maximum(zadel, boven * gladstap(-0.42, -0.30, y) * gladstap(0.62, 0.70, z))      # schoft/rug breed
    staart = gladstap(0.42, 0.50, y) * gladstap(-0.2, 0.4, nrm[..., 2] - 0.6 * nrm[..., 1])
    staart_punt = gladstap(0.72, 0.84, y)                                                    # donkere pluim
    schedel = gladstap(-0.47, -0.53, y) * gladstap(0.80, 0.88, z)
    d = np.clip(np.maximum.reduce([zadel * (0.75 + 0.35 * ru), staart * 0.45, staart_punt * 0.8, schedel * 0.5]), 0, 1)
    d = d * gezet
    rgb = rgb * (1 - 0.55 * d[..., None])
    # fijne vachtstreping overal (ruig, niet glad)
    fijn = BM.ruis(pos.reshape(-1, 3), f=(90, 40, 90), seed=3).reshape(h, w)
    rgb = rgb * (1 + 0.10 * fijn * gezet)[..., None]
    rgb = np.where(rood[..., None], A[..., :3], np.clip(rgb, 0, 1))
    A[..., :3] = rgb
    img.pixels.foreach_set(A.ravel())
    img.pack()
    return rood


def _gewichten(o):
    me = o.data
    W = np.zeros((len(me.vertices), len(o.vertex_groups)), np.float32)
    for v in me.vertices:
        for ge in v.groups:
            W[v.index, ge.group] = ge.weight
    return W


def _oog_mat():
    m = bpy.data.materials.new("mat_oog")
    m.use_nodes = True
    b = m.node_tree.nodes["Principled BSDF"]
    c = (1.0, 0.03, 0.02, 1)
    b.inputs["Base Color"].default_value = c
    b.inputs["Roughness"].default_value = 0.2
    b.inputs["Emission Color"].default_value = c
    b.inputs["Emission Strength"].default_value = 3.0
    return m


def extras(o, rig, sk, img):
    """Na de gewichten: haarplukken (driehoeken, dubbelzijdig, kleur van het ankerpunt, gewichten van het
    ankerpunt) op nek/manen, rugkam en staart, en twee gloeiende oogbollen star aan Head. Geeft het
    haarmateriaal terug (eigen texture-node, die bij de donkere wolf mee moet wisselen)."""
    rng = np.random.default_rng(11)
    me = o.data
    pos, nrm, gezet = texels(img, o)          # eerst: daarna zitten de plukken in de mesh
    W = _gewichten(o)
    gi = {g.name: i for i, g in enumerate(o.vertex_groups)}
    V = np.array([v.co for v in me.vertices], float)
    Nv = np.array([v.normal for v in me.vertices], float)
    tris = []
    for p in me.polygons:
        li = list(p.loop_indices)
        for k in range(1, len(li) - 1):
            tris.append((li[0], li[k], li[k + 1]))
    tris = np.array(tris)
    LV = np.array([l.vertex_index for l in me.loops])
    UV = np.array([l.uv for l in me.uv_layers.active.data], float)
    TV = LV[tris]
    A, B, C = V[TV[:, 0]], V[TV[:, 1]], V[TV[:, 2]]
    opp = 0.5 * np.linalg.norm(np.cross(B - A, C - A), axis=1)
    M = (A + B + C) / 3
    Mn = Nv[TV].mean(1)
    Mn /= np.linalg.norm(Mn, axis=1, keepdims=True) + 1e-9
    som = lambda namen: sum(W[TV, gi[n]].mean(1) for n in namen if n in gi)
    tail = som(("Tail", "Tail1", "Tail2", "Tail3"))
    oor = som(("LeftEar", "RightEar"))
    kop = som(("Head", "Jaw"))
    poot = som([z_ + b for z_ in ("Left", "Right") for b in ("UpperArm", "ForeArm", "FrontCannon", "FrontHoof",
                                                           "Thigh", "Shin", "HindCannon", "HindHoof")])
    y, z = M[:, 1], M[:, 2]
    yk = MAAT_T["kop"][0][0]
    manen = (gladstap(-0.22, -0.32, y) * gladstap(yk - 0.12, yk - 0.04, y) * gladstap(0.40, 0.52, z)
             * (oor < 0.2) * (tail < 0.1) * (kop < 0.6) * (poot < 0.3))
    kam = (gladstap(-0.1, 0.4, Mn[:, 2]) * (np.abs(M[:, 0]) < 0.07) * gladstap(0.44, 0.35, y) * (manen < 0.3)
           * (tail < 0.1) * (kop < 0.1) * (y > -0.40) * (poot < 0.3))
    st = np.clip(tail, 0, 1) * (M[:, 1] > MAAT_T["staart"][0][0])
    soorten = [  # (naam, masker, dichtheid /m2, lengte, breedte)
        ("manen", manen, 4200, (0.04, 0.075), 0.042),
        ("kam", kam, 1500, (0.03, 0.05), 0.032),
        ("staart", st, 3600, (0.035, 0.065), 0.040),
    ]
    L = np.array(MAAT_T["staart"], float)
    nv, nuv, nw, nn_ = [], [], [], []
    for naam, masker, dicht, (l0, l1), br in soorten:
        n = rng.poisson(opp * masker * dicht)
        ids = np.repeat(np.arange(len(tris)), n)
        if not len(ids):
            continue
        r1, r2 = rng.random(len(ids)), rng.random(len(ids))
        sq = np.sqrt(r1)
        bc = np.stack([1 - sq, sq * (1 - r2), sq * r2], 1)
        p = (bc[:, :, None] * V[TV[ids]]).sum(1)
        nn = (bc[:, :, None] * Nv[TV[ids]]).sum(1)
        nn /= np.linalg.norm(nn, axis=1, keepdims=True) + 1e-9
        uv = (bc[:, :, None] * UV[tris[ids]]).sum(1)
        ww = (bc[:, :, None] * W[TV[ids]]).sum(1)
        if naam == "staart":
            _, T, _ = _op_lijn(p[:, 1:], L)
            i = np.clip(T.astype(int), 0, len(L) - 2)
            dyz = L[i + 1] - L[i]
            flow = np.stack([np.zeros(len(p)), dyz[:, 0], dyz[:, 1]], 1)
            uit, mee = 0.45, 0.9
        else:
            flow = np.tile(np.array([0.0, 1.0, -0.7]), (len(p), 1))
            uit, mee = (0.65, 0.75) if naam == "manen" else (0.8, 0.5)
        flow -= nn * (flow * nn).sum(1, keepdims=True)
        flow /= np.linalg.norm(flow, axis=1, keepdims=True) + 1e-9
        d = nn * uit + flow * mee + rng.normal(0, 0.18, (len(p), 3))
        d -= nn * np.minimum((d * nn).sum(1, keepdims=True) - 0.25, 0)        # nooit het lijf in
        d /= np.linalg.norm(d, axis=1, keepdims=True)
        lang = rng.uniform(l0, l1, len(p))
        zij = np.cross(d, nn)
        zij /= np.linalg.norm(zij, axis=1, keepdims=True) + 1e-9
        b = br * rng.uniform(0.7, 1.2, len(p))
        basis = p - nn * 0.006
        for j in range(len(p)):
            nv += [basis[j] - zij[j] * b[j] / 2, basis[j] + zij[j] * b[j] / 2, p[j] + d[j] * lang[j]]
            nuv += [uv[j]] * 3
            nw += [ww[j]] * 3
            nn_ += [nn[j]] * 3
        log("  haar", naam, len(p), "plukken")
    nh = len(nv) // 3
    # ogen: zwaartepunt van de rode texels per kant (rustpose)
    Aimg = np.array(img.pixels[:], np.float32).reshape(img.size[1], img.size[0], 4)
    rood = is_rood(Aimg[..., :3]) & gezet & (pos[..., 1] < MAAT_T["kop"][0][0])
    ogen = []
    for sg in (1, -1):
        m = rood & (np.sign(pos[..., 0]) == sg) & (np.abs(pos[..., 0]) > 0.01)
        if m.sum() >= 3:
            c = pos[m].mean(0).astype(float)
            n_ = nrm[m].mean(0).astype(float)
            log("  oog", sg, "uit", int(m.sum()), "rode texels", np.round(c, 3).tolist())
        else:
            d_, u_ = KO.kop_assen(sk)
            c = sk.J["Head"] + d_ * 0.07 + np.array((sg * 0.045, 0, 0)) - u_ * 0.03
            n_ = np.array((sg * 0.7, -0.7, 0.1))
            log("  oog", sg, "geschat", np.round(c, 3).tolist())
        ogen.append((c, n_ / (np.linalg.norm(n_) + 1e-9)))
    bm = bmesh.new()
    bm.from_mesh(me)
    dl = bm.verts.layers.deform.verify()
    uvlay = bm.loops.layers.uv.active
    haar = me.materials[0].copy()
    haar.name = "mat_haar"
    haar.use_backface_culling = False
    i_haar = len(me.materials)
    me.materials.append(haar)
    i_oog = len(me.materials)
    me.materials.append(_oog_mat())
    for t in range(nh):
        vs = [bm.verts.new(Vector(nv[3 * t + k])) for k in range(3)]
        for k, v in enumerate(vs):
            wk = nw[3 * t + k]
            for g in np.nonzero(wk > 0.01)[0]:
                v[dl][int(g)] = float(wk[g])
        f = bm.faces.new(vs)
        f.material_index = i_haar
        f.smooth = True
        for k, lp in enumerate(f.loops):
            lp[uvlay].uv = nuv[3 * t + k]
    h_ = gi["Head"]
    for c, n_ in ogen:
        r = 0.013
        res = bmesh.ops.create_uvsphere(bm, u_segments=10, v_segments=6, radius=r)
        a1 = np.cross(n_, (0.0, 0.0, 1.0))
        a1 /= np.linalg.norm(a1) + 1e-9
        a2 = np.cross(n_, a1)
        for v in res["verts"]:
            q = np.array(v.co) / r
            v.co = Vector(c + n_ * (0.002 + q[2] * r * 0.55) + a1 * q[0] * r * 1.25 + a2 * q[1] * r)
            v[dl][h_] = 1.0
        for f in {f for v in res["verts"] for f in v.link_faces}:
            f.material_index = i_oog
            f.smooth = True
    n_oud = len(me.polygons)
    bm.to_mesh(me)
    bm.free()
    me.update()
    # plukken krijgen de normaal van hun ankerpunt (schaduw als de vacht eronder, geen donkere zijkanten)
    CN = np.array([c.vector for c in me.corner_normals], np.float32)
    for t in range(nh):
        for li in me.polygons[n_oud + t].loop_indices:
            CN[li] = nn_[3 * t]
    me.normals_split_custom_set(CN.tolist())
    log("extras:", nh, "haarplukken, 2 ogen; driehoeken", len(me.polygons))
    return next(nd for nd in haar.node_tree.nodes if nd.type == "TEX_IMAGE")


# --- Skelet + gewichten ---------------------------------------------------------------------------------
def bouw_rig():
    rig = R.K.bouw_rig(MAAT_T, "wolf_rig")
    rig["rustpose"] = "staand, kijkt naar -Y"
    return rig


def seg_d(P, a, b):
    ab = b - a
    t = np.clip((P - a) @ ab / (ab @ ab), 0, 1)
    return np.linalg.norm(P - (a + t[:, None] * ab), axis=1)


def skin(o, rig):
    sk = KO.Skelet(rig)
    BM.ontkies()
    o.select_set(True)
    rig.select_set(True)
    bpy.context.view_layer.objects.active = rig
    bpy.ops.object.parent_set(type="ARMATURE_AUTO")
    me = o.data
    P = np.array([v.co for v in me.vertices])
    vg = {g.name: g for g in o.vertex_groups}
    leeg0 = sum(1 for v in me.vertices if not v.groups)

    def zet(mask, bot, w=None):
        ids = np.nonzero(mask)[0]
        if not len(ids):
            return
        if w is None:
            for g in o.vertex_groups:
                g.remove(ids.tolist())
            (vg.get(bot) or o.vertex_groups.new(name=bot)).add(ids.tolist(), 1.0, "REPLACE")
            return
        # zacht: bestaande gewichten x (1-w), bot krijgt w
        g = vg.get(bot) or o.vertex_groups.new(name=bot)
        vg[bot] = g
        for vi in ids:
            v = me.vertices[int(vi)]
            ww = float(w[vi])
            for ge in v.groups:
                ge.weight *= (1 - ww)
            g.add([int(vi)], ww, "ADD")

    # bone heat faalt bij een niet-gesloten mesh soms: dan per vertex het dichtstbijzijnde bot (romp/nek)
    if leeg0:
        log("  bone heat liet", leeg0, "vertices leeg: dichtstbijzijnde bot")
        botten = [b.name for b in rig.data.bones if b.use_deform]
        D = np.stack([seg_d(P, sk.J[b], sk.T[b]) for b in botten], 1)
        for vi in [v.index for v in me.vertices if not v.groups]:
            b = botten[int(np.argmin(D[vi]))]
            (vg.get(b) or o.vertex_groups.new(name=b)).add([vi], 1.0, "REPLACE")
    KO.glad_gewichten(o, 0.5, 3)
    s = sk.s
    # oren star
    for z in ("Left", "Right"):
        ea, ee = sk.J[z + "Ear"], sk.T[z + "Ear"]
        e = ee - ea
        t = np.clip((P - ea) @ e / (e @ e), -1, 2)
        dist = np.linalg.norm(P - (ea + t[:, None] * e), axis=1)
        zet((t > 0.1) & (dist < 0.06 * s) & (np.sign(P[:, 0]) == np.sign(ea[0])) & (P[:, 2] > ea[2] - 0.01), z + "Ear")
    # kop (voor de oren) star aan Head, onderkaak aan Jaw
    d, u = KO.kop_assen(sk)
    H0 = sk.J["Head"]
    tk = (P - H0) @ d
    kaak = (seg_d(P, sk.J["Jaw"], sk.T["Jaw"]) < 0.035 * s) & (((P - H0) @ u) > 0.06 * s) & (tk > 0.10 * s)
    kop = (tk > 0.04 * s) & ~kaak & (P[:, 2] > 0.62 * s) & (P[:, 1] < sk.J["Head"][1] + 0.02)
    oor = np.zeros(len(P), bool)
    for v in me.vertices:
        for ge in v.groups:
            if o.vertex_groups[ge.group].name.endswith("Ear") and ge.weight > 0.99:
                oor[v.index] = True
    zet(kop & ~oor, "Head")
    zet(kaak, "Jaw")
    # staart: alles achter het staartbegin en boven de hak hoort bij de staartketen (niet bij de dij)
    st = [sk.J[n] for n in ("Tail", "Tail1", "Tail2", "Tail3")] + [sk.T["Tail3"]]
    dst = np.min([seg_d(P, st[i], st[i + 1]) for i in range(4)], 0)
    hak = min(sk.J["LeftHindCannon"][2], sk.J["RightHindCannon"][2])
    staart = (dst < 0.09 * s) & (P[:, 1] > sk.J["Tail"][1] + 0.02) & (np.abs(P[:, 0]) < 0.10) & (P[:, 2] > hak + 0.05)
    ids = np.nonzero(staart)[0]
    namen = ["Tail", "Tail1", "Tail2", "Tail3"]
    Dt = np.stack([seg_d(P[ids], st[i], st[i + 1]) for i in range(4)], 1)
    Wt = np.exp(-(Dt / 0.03) ** 2)
    Wt /= Wt.sum(1, keepdims=True) + 1e-9
    for g in o.vertex_groups:
        g.remove(ids.tolist())
    for i, nm in enumerate(namen):
        g = vg.get(nm) or o.vertex_groups.new(name=nm)
        vg[nm] = g
        for k, vi in enumerate(ids):
            if Wt[k, i] > 1e-3:
                g.add([int(vi)], float(Wt[k, i]), "REPLACE")
    poten(o, sk)
    KO.romp_los(o, sk)
    bpy.context.view_layer.objects.active = o
    BM.ontkies()
    o.select_set(True)
    bpy.ops.object.vertex_group_limit_total(group_select_mode="ALL", limit=4)
    bpy.ops.object.vertex_group_clean(group_select_mode="ALL", limit=0.01)
    bpy.ops.object.vertex_group_normalize_all(lock_active=False)
    leeg = sum(1 for v in me.vertices if not v.groups)
    if leeg:
        log("  let op:", leeg, "vertices zonder gewicht")
    return sk


def poten(o, sk):
    """Onderbenen opnieuw (in plaats van koe.onderbenen): TRELLIS-poten zijn dikke klompjes rond het
    balgewricht en de pols/hak zit in een dik stuk been. Half aan de middenvoet en half aan de zool
    scheurt bij een galopbuiging van ~90 graden, en een overgang van 6 cm bij de pols knikt. Dus: hele
    poot aan de middenvoet met hooguit 30 % zool aan de teenkant, en pols/hak over 14 cm overvloeien."""
    me = o.data
    P = np.array([v.co for v in me.vertices])
    gi = {g.name: g for g in o.vertex_groups}
    for z in ("Left", "Right"):
        for boven, pijp, klauw in (("ForeArm", "FrontCannon", "FrontHoof"), ("Shin", "HindCannon", "HindHoof")):
            kn, ko, te = sk.J[z + pijp], sk.J[z + klauw], sk.T[z + klauw]
            sel = (P[:, 2] < kn[2] + 0.07) & (np.sign(P[:, 0]) == np.sign(ko[0])) & (seg_d(P, kn, te) < 0.10)
            ids = np.nonzero(sel)[0]
            if not len(ids):
                continue
            zp = P[ids, 2]
            richting = (te - ko) / np.linalg.norm(te - ko)
            voor = np.clip(((P[ids] - ko) @ richting) / np.linalg.norm(te - ko), 0, 1)
            wk = 0.3 * voor * gladstap(ko[2] + 0.05, ko[2], zp)
            wb = gladstap(kn[2] - 0.07, kn[2] + 0.07, zp) * (1 - wk)
            wp = 1 - wk - wb
            for g in o.vertex_groups:
                g.remove(ids.tolist())
            for nm, w in ((z + klauw, wk), (z + pijp, wp), (z + boven, wb)):
                g = gi.get(nm) or o.vertex_groups.new(name=nm)
                gi[nm] = g
                for vi, wv in zip(ids, w):
                    if wv > 1e-3:
                        g.add([int(vi)], float(wv), "REPLACE")


# --- Controle: rek per rand in de clips -----------------------------------------------------------------
def rek(o, rig, sc):
    """Max relatieve randlengte (vervormd/rust) per clip: > ~2,5 = scheur/naald."""
    E = np.zeros(len(o.data.edges) * 2, np.int64)
    o.data.edges.foreach_get("vertices", E)
    E = E.reshape(-1, 2)
    P0 = np.array([v.co for v in o.data.vertices])
    L0 = np.linalg.norm(P0[E[:, 0]] - P0[E[:, 1]], axis=1) + 1e-6
    uit = {}
    dg = bpy.context.evaluated_depsgraph_get()
    for act in ("idle", "lopen", "rennen", "bijten", "dood"):
        R.K.zet_actie(rig, act)
        a = bpy.data.actions[act]
        f0, f1 = int(a.frame_range[0]), int(a.frame_range[1])
        slechtst, waar = 0.0, ""
        for f in range(f0, f1 + 1, 2):
            sc.frame_set(f)
            ev = o.evaluated_get(dg)
            m = ev.to_mesh()
            P = np.array([v.co for v in m.vertices])
            ev.to_mesh_clear()
            r = np.linalg.norm(P[E[:, 0]] - P[E[:, 1]], axis=1) / L0
            w = max(float(np.percentile(r, 99.9)), float(r.max()) * 0.5)
            if w > slechtst:
                slechtst = w
                vi = int(E[int(np.argmax(r)), 0])
                gr = max(o.data.vertices[vi].groups, key=lambda ge: ge.weight, default=None)
                v2 = int(E[int(np.argmax(r)), 1])
                g2 = max(o.data.vertices[v2].groups, key=lambda ge: ge.weight, default=None)
                waar = (f"{o.vertex_groups[gr.group].name if gr else '-'}/{o.vertex_groups[g2.group].name if g2 else '-'}"
                        f"@{f} {np.round(P0[vi], 2).tolist()}")
        uit[act] = (round(slechtst, 2), waar)
    rust(rig)
    return uit


def rust(rig):
    rig.animation_data_create().action = None
    for b in rig.pose.bones:
        b.rotation_quaternion = (1, 0, 0, 0)
        b.location = (0, 0, 0)
    bpy.context.view_layer.update()


# --- Previews -------------------------------------------------------------------------------------------
def zij(sc, rig):
    """Zij- en bovenaanzicht, raster per 10 cm, botten als lijnen (rood = deform)."""
    rust(rig)
    ppm = 400
    rijen = []
    for yaw, pitch in ((180, 0), (180, 89.9)):
        doel = (0, -0.05, 0.55) if pitch == 0 else (0, -0.05, 0.5)
        BM.studio(sc, ppm, 1.8, 1.2 if pitch == 0 else 0.6, doel=doel, yaw=yaw, pitch=pitch)
        a = BM.render_np(sc, os.path.join(bpy.app.tempdir, f"zij_{pitch}.png"))
        H, W = a.shape[:2]
        rgb = a[..., :3] * a[..., 3:] + 0.85 * (1 - a[..., 3:])

        def px(p):   # wereld -> (rij, kolom); beeldrechts = -Y; boven = +Z (zij) of -X (boven)
            c = W / 2 - (p[1] - doel[1]) * ppm
            r = H / 2 - ((p[2] - doel[2]) if pitch == 0 else -(p[0] - doel[0])) * ppm
            return r, c
        for k in range(-10, 11):
            for val in (k * 0.1,):
                r, c = px((val, val, val))
                if 0 <= int(c) < W:
                    rgb[:, int(c)] = rgb[:, int(c)] * 0.6 + 0.4 * np.array([0.2, 0.2, 0.8]) * (1.5 if k == 0 else 1)
                if 0 <= int(r) < H:
                    rgb[int(r), :] = rgb[int(r), :] * 0.6 + 0.4 * np.array([0.2, 0.2, 0.8]) * (1.5 if k == 0 else 1)
        for b in rig.data.bones:
            h, t = b.head_local, b.tail_local
            for i in range(41):
                p = h + (t - h) * (i / 40)
                r, c = px(p)
                if 0 <= int(r) < H - 1 and 0 <= int(c) < W - 1:
                    rgb[int(r):int(r) + 2, int(c):int(c) + 2] = (1, 0.1, 0.1) if b.use_deform else (1, 1, 0)
        rijen.append(np.clip(rgb, 0, 1))
    BM.schrijf(BM.onder(*rijen), os.path.join(PREV, "wolf_trellis_zij.png"))


def poses(sc, rig, tex, kleuren):
    keuzes = [("idle", 0), ("idle", 60), ("lopen", 4), ("lopen", 17), ("rennen", 2), ("rennen", 7),
              ("bijten", 5), ("bijten", 9), ("dood", 14), ("dood", 24)]
    rijen = []
    for soort, yaw, pitch in (("wolf", 225, 30), ("wolf", 180, 6), ("donker", 225, 30)):
        tex.image = kleuren[soort]
        panelen = []
        for act, f in keuzes:
            R.K.zet_actie(rig, act)
            sc.frame_set(f)
            BM.studio(sc, 150, 2.4, 1.6, doel=(0, -0.2, 0.5), yaw=yaw, pitch=pitch)
            panelen.append(BM.bijsnijden(BM.render_np(sc, os.path.join(bpy.app.tempdir, f"p_{act}_{f}.png"))))
        rijen.append(BM.plak(panelen))
    tex.image = kleuren["wolf"]
    BM.schrijf(BM.onder(*rijen), os.path.join(PREV, "wolf_trellis_v2_poses.png"))
    rust(rig)


def detail(sc, rig, keuzes):
    """Lokaal, groot: een paar standen van dichtbij (vervorming nakijken)."""
    panelen = []
    for act, f, yaw in keuzes:
        R.K.zet_actie(rig, act)
        sc.frame_set(f)
        BM.studio(sc, 330, 2.0, 1.3, doel=(0, -0.1, 0.5), yaw=yaw, pitch=20)
        panelen.append(BM.bijsnijden(BM.render_np(sc, os.path.join(bpy.app.tempdir, f"d_{act}_{f}.png"))))
    BM.schrijf(BM.onder(BM.plak(panelen[:3]), BM.plak(panelen[3:])), os.path.join(PREV, "wolf_trellis_detail.png"))
    rust(rig)


def exporteer(pad):
    BM.ontkies()
    bpy.ops.export_scene.gltf(filepath=pad, export_format="GLB", export_animations=True,
                              export_animation_mode="ACTIONS", export_force_sampling=True, export_yup=True,
                              export_skins=True, export_def_bones=False, export_extras=True, use_selection=False,
                              export_tangents=False, export_image_format="AUTO", export_cameras=False,
                              export_lights=False)
    log("export", pad, f"{os.path.getsize(pad) / 1e6:.1f} MB")


class Texen:
    """Lijf- en haarmateriaal delen de textuur: `.image = ` zet hem in beide (grijs/donker wisselen)."""

    def __init__(self, nodes):
        self.__dict__["nodes"] = nodes

    def __setattr__(self, k, v):
        for n in self.nodes:
            setattr(n, k, v)

    def __getattr__(self, k):
        return getattr(self.nodes[0], k)


def main():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    sc = bpy.context.scene
    sc.render.fps = R.FPS
    sc.frame_start = 0
    lijf = laad()
    vorm(lijf)
    mat, tex0, img = materiaal(lijf)
    tekening(img, lijf)
    rig = bouw_rig()
    if "zij" in OPTS:
        zij(sc, rig)
    sk = skin(lijf, rig)
    tex = Texen([tex0, extras(lijf, rig, sk, img)])
    info = R.bouw_animaties(rig)
    log("animaties", list(info))
    log("rek (p99.9 / max/2)", json.dumps(rek(lijf, rig, sc)))
    donker = donkere_textuur(img, lijf)
    kleuren = {"wolf": img, "donker": donker}
    if "geen_export" not in OPTS:
        os.makedirs(ASSETS, exist_ok=True)
        tex.image = img
        exporteer(GLB["wolf"])
        tex.image = donker
        exporteer(GLB["donker"])
        tex.image = img
    os.makedirs(PREV, exist_ok=True)
    if "poses" in OPTS:
        poses(sc, rig, tex, kleuren)
    if "detail" in OPTS:
        detail(sc, rig, [("lopen", 16, 160), ("rennen", 2, 200), ("bijten", 10, 150), ("dood", 14, 200),
                         ("dood", 24, 160), ("rennen", 7, 120)])
    if "blend" in OPTS:
        bpy.ops.wm.save_as_mainfile(filepath=os.path.join(PREV, "wolf_trellis.blend"))
    log("KLAAR")


if __name__ == "__main__":
    main()
