"""Wolf naar de Tripo-referentie: de TRELLIS-mesh vervormd tot het silhouet van een zijaanzicht-render en dat
beeld erop geprojecteerd, met het skelet en de clips van wolf_rig.py
-> spel/assets/wolf_tripo.glb + donkere_wolf_tripo.glb (Blender 5.2 headless -> Godot 4; spel.json wolf_model "tripo").

Draaien:
  blender -b -P wolf_tripo.py -- [poses] [zij] [ankers] [geen_export]
- `zij`: lokaal/tripo/wolf_tripo_zij.png (ons model van opzij naast de referentie, zelfde maat).
- `poses`: lokaal/tripo/wolf_tripo_poses.png (standen uit alle clips, grijs en donker).
- `ankers`: lokaal/tripo/wolf_tripo_ankers.png (beide contouren met de ankerparen; om ANKERS bij te stellen).
⚠️ Alles met de geprojecteerde textuur blijft lokaal (lokaal/ is gitignored): de textuur komt uit de
Tripo-render. Alleen dit script gaat in git.

Invoer (lokaal, gitignored): lokaal/trellis/wolf_trellis.glb (mesh, UV's) en lokaal/tripo/wolf_links.png
(zijaanzicht van de Tripo-wolf, 612 x 392, kop links, studio-achtergrond).

Stappen:
1. TRELLIS laden (wolf_trellis.laad: samenvoegen, schalen, centreren), géén vorm().
2. Silhouet van opzij (330 px/m) en het silhouet van de referentie (projectie.segmenteer), beide als contour.
3. ANKERS: paren (punt op de TRELLIS-vorm in m) -> (pixel in de referentie), samen met de tussenpunten langs de
   contour een thin-plate spline (y, z) -> referentiepixel. Elke vertex krijgt de referentiepositie (dus
   kop laag, lange dunne poten, hangende pluimstaart), x geschaald met de lokale oppervlaktefactor rond het
   midden van lijf of poot; daarna opnieuw schoft 0,80 m en centreren. MAAT_T gaat door dezelfde afbeelding.
4. Textuur (2048): per texel de referentiepixel (de afbeelding is lineair terug), aan beide kanten gespiegeld;
   bij scherende normalen iets naar binnen bemonsterd (geen randkleur), fijne ruis tegen strepen.
5. Skelet, gewichten, ogen (wolf_trellis.skin/extras, geen haarplukken), clips, donkere variant, export.
"""
import json
import os
import sys
import time

argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
OPTS = {a.split("=")[0]: (a.split("=", 1)[1] if "=" in a else "1") for a in argv}

import bpy  # noqa: E402
import numpy as np  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import wolf_trellis as WT  # noqa: E402  (laad, texels, skin, extras, rek, exporteer, Texen)
import wolf_rig as R  # noqa: E402
import dieren_basis as BM  # noqa: E402
import projectie as PJ  # noqa: E402

ROOT = WT.ROOT
REF = os.path.join(ROOT, "lokaal", "tripo", "wolf_links.png")
UIT = os.path.join(ROOT, "lokaal", "tripo")
GLB = {"wolf": os.path.join(WT.ASSETS, "wolf_tripo.glb"), "donker": os.path.join(WT.ASSETS, "donkere_wolf_tripo.glb")}
PPM = 330.0                     # px/m van het TRELLIS-zijaanzicht (de referentie is ~334 px/m)
TEX = 2048
SCHADUW = (222, 235, 376)       # referentie: slagschaduw onder de buik (rij vanaf, kolom van-tot) is geen wolf
LAM = 0.5                       # TPS-gladheid
STAART_BREED = 1.6              # x-factor van de staart bovenop de oppervlaktefactor
T0 = time.time()
gladstap = BM.gladstap


def log(*a):
    print(f"[wolf_tripo {time.time() - T0:6.1f}s]", *a, flush=True)


# (y, z) op de TRELLIS-vorm na laad() (m, -y = voor) -> (kolom, rij) in wolf_links.png. In contourvolgorde
# (met de klok mee in het beeld, vanaf het oor): rug, staart, achterpoot, buik, voorpoot, borst, kin, snuit.
ANKERS = [
    ((-0.535, 1.001), (79, 97)),     # oorpunt (het nabije oor)
    ((-0.415, 0.924), (140, 87)),    # achterhoofd
    ((-0.298, 0.841), (175, 83)),    # nek
    ((-0.176, 0.771), (230, 92)),    # schoft
    ((-0.030, 0.756), (315, 88)),
    ((0.119, 0.762), (375, 87)),
    ((0.268, 0.756), (451, 93)),
    ((0.405, 0.723), (496, 106)),    # kruis / staartwortel
    ((0.514, 0.632), (530, 137)),    # staart bovenkant
    ((0.562, 0.500), (548, 180)),
    ((0.621, 0.373), (558, 235)),
    ((0.747, 0.256), (557, 281)),    # staartpunt
    ((0.667, 0.217), (538, 276)),
    ((0.532, 0.259), (510, 242)),    # staart onderkant
    ((0.424, 0.346), (501, 196)),
    ((0.408, 0.382), (486, 201)),    # oksel staart/dij
    ((0.445, 0.252), (478, 251)),    # achterkant dij -> hak
    ((0.435, 0.117), (499, 287)),    # hak
    ((0.426, 0.060), (482, 330)),
    ((0.375, 0.004), (456, 351)),    # achtervoet onder
    ((0.322, 0.058), (430, 327)),    # achtervoet teen
    ((0.358, 0.184), (456, 279)),    # middenvoet voorkant
    ((0.262, 0.290), (422, 247)),    # scheen
    ((0.168, 0.399), (367, 211)),    # knie / flank
    ((0.053, 0.392), (329, 221)),    # buik
    ((-0.092, 0.377), (269, 221)),
    ((-0.183, 0.377), (234, 226)),   # elleboog achter
    ((-0.204, 0.331), (227, 253)),   # voorbeen achterkant
    ((-0.220, 0.186), (221, 309)),
    ((-0.255, 0.054), (206, 341)),   # voorvoet hiel
    ((-0.316, 0.004), (175, 355)),   # voorvoet onder
    ((-0.374, 0.011), (155, 340)),   # voorvoet teen
    ((-0.317, 0.092), (190, 312)),   # pols voor
    ((-0.309, 0.236), (191, 274)),
    ((-0.335, 0.377), (179, 229)),   # voorbeen boven
    ((-0.435, 0.478), (154, 217)),   # borst
    ((-0.502, 0.602), (117, 209)),   # keel
    ((-0.612, 0.668), (57, 204)),    # kin
    ((-0.710, 0.739), (23, 196)),    # neuspunt
    ((-0.614, 0.838), (56, 124)),    # voorhoofd
    ((-0.541, 0.949), (53, 102)),    # oorbasis voor
]


# --- Referentie en vervorming -------------------------------------------------------------------------
def referentie():
    a = BM.laad_np(REF)[..., :3]                     # sRGB-waarden, rij 0 boven
    m = PJ.segmenteer(a)
    r0, c0, c1 = SCHADUW
    m[r0:, c0:c1] = False
    m = PJ.grootste(m)
    ext, _ = PJ.uitbreiden(a, m, 40)
    log("referentie", a.shape, "wolf", int(m.sum()), "px")
    return a, m, ext


class Afbeelding:
    """TRELLIS (y, z) in m -> referentiepixel (TPS) -> nieuwe (y, z) in m (lineair, schoft 0,80 m)."""

    def __init__(self, P, T, mref):
        self.u0, self.v1 = float(P[:, 1].min()), float(P[:, 2].max())
        P2 = self.px(P[:, 1], P[:, 2])
        H = int((self.v1 - P[:, 2].min()) * PPM) + 9
        W = int((P[:, 1].max() - self.u0) * PPM) + 9
        mm = PJ.raster_masker(P2, T, H, W)
        self.cs = PJ.herbemonster(PJ.contour(mm), 2.0)
        self.cd = PJ.herbemonster(PJ.contour(mref), 2.0)
        ank = sorted((PJ.dichtst(self.cs, self.px(*a)[0]), PJ.dichtst(self.cd, b)) for a, b in ANKERS)
        self.ank = ank
        S, D = PJ.paren(self.cs, self.cd, ank)
        self.S, self.D = S, D
        self.t = PJ.tps_fit(S, D, LAM)
        det = PJ.tps_jac(self.t, P2)
        log("TPS", len(S), "paren; det min", round(float(det.min()), 3), "p50", round(float(np.median(det)), 3),
            "gevouwen", int((det <= 0).sum()))
        # lineair ref-px -> m: schoft 0,80 m zoals laad(), voeten op 0, midden tussen de voeten op y = 0
        q = PJ.tps_pas(self.t, P2)
        y, z = q[:, 0], -q[:, 1]
        z0 = z.min()
        voet = z < z0 + 0.02 * PPM
        yv, ya = y[voet & (y < np.median(y[voet]))].mean(), y[voet & (y >= np.median(y[voet]))].mean()
        band = (y > yv + 0.05 * PPM) & (y < yv + 0.15 * PPM)          # rugtop net achter de voorvoeten
        schoft = z[band].max() - z0
        log("voeten (px)", round(float(yv), 1), round(float(ya), 1), "schoft-top rij", round(float(-z[band].max()), 1))
        self.s = WT.SCHOFT / schoft
        self.yc, self.z0 = 0.5 * (yv + ya), z0
        log("ref schoft", round(float(schoft), 1), "px ->", round(self.s * PPM, 3), "x")

    def px(self, y, z):
        return np.stack([(np.asarray(y) - self.u0) * PPM + 4, (self.v1 - np.asarray(z)) * PPM + 4], -1).reshape(-1, 2)

    def naar_ref(self, y, z):
        return PJ.tps_pas(self.t, self.px(y, z))

    def ref_naar_m(self, q):
        q = np.asarray(q, float).reshape(-1, 2)
        return (q[:, 0] - self.yc) * self.s, (-q[:, 1] - self.z0) * self.s

    def m_naar_ref(self, y, z):
        return np.stack([np.asarray(y) / self.s + self.yc, -(np.asarray(z) / self.s + self.z0)], -1)

    def punt(self, y, z):
        a, b = self.ref_naar_m(self.naar_ref(y, z))
        return float(a[0]), float(b[0])

    def factor(self, y, z):
        """Lineaire schaal (x) per punt: wortel van de oppervlaktefactor, in m/m."""
        return np.sqrt(np.clip(PJ.tps_jac(self.t, self.px(y, z)), 0.05, None)) * self.s * PPM


def vervorm(o, A):
    me = o.data
    P = np.array([v.co for v in me.vertices], float)
    x, y, z = P[:, 0], P[:, 1], P[:, 2]
    k = np.clip(A.factor(y, z), 0.6, 1.5)
    # pluimstaart: van boven/achter breed (wolf_achter.png: bijna zo breed als een dij), dus x extra rond de staartlijn
    L = np.array(WT.MAAT_T["staart"], float)
    _, Ts, ds = WT._op_lijn(np.stack([y, z], 1), L)
    ws = gladstap(0.10, 0.06, ds) * gladstap(L[0][0], L[0][0] + 0.08, y) * (np.abs(x) < 0.12)
    k = k * (1 + (STAART_BREED - 1) * ws * gladstap(0.0, 1.5, Ts))
    # x-midden: lijf 0, onder de buik het midden van de poot (zelfde kant, zelfde hoogte en y)
    cx = np.zeros(len(P))
    laag = np.nonzero(z < 0.45)[0]
    for i in laag:
        m = (np.sign(x) == np.sign(x[i])) & (np.abs(y - y[i]) < 0.05) & (np.abs(z - z[i]) < 0.03)
        cx[i] = x[m].mean()
    w = gladstap(0.44, 0.32, z)
    cx = cx * w
    xn = cx + (x - cx) * k
    yn, zn = A.ref_naar_m(A.naar_ref(y, z))
    for i, v in enumerate(me.vertices):
        v.co = (xn[i], yn[i], zn[i])
    me.update()
    log("vervormd: x-factor p5/p50/p95", np.round(np.percentile(k, [5, 50, 95]), 2).tolist(),
        "maat", np.round(np.ptp(np.stack([xn, yn, zn], 1), 0), 3).tolist())


def maat(A):
    """MAAT_T (op de ruwe TRELLIS-vorm) door dezelfde afbeelding."""
    M0 = dict(WT.MAAT_T)
    M = dict(M0)
    for k in ("rug", "nek", "kop", "kaak", "staart", "voorbeen", "achterbeen"):
        M[k] = [A.punt(*p) for p in M0[k]]
    for k in ("heup", "bel"):
        M[k] = A.punt(*M0[k])
    ox, oy, oz = M0["oor"]
    ny, nz = A.punt(oy, oz)
    kx = float(A.factor(oy, oz)[0])
    M["oor"] = (ox * kx, ny, nz)
    rx, ry, rz = M0["oor_richting"]
    e = 0.03 / np.linalg.norm((rx, ry, rz))
    ty, tz = A.punt(oy + ry * e, oz + rz * e)
    M["oor_richting"] = (rx * e * kx, ty - ny, tz - nz)
    t0 = np.array(M0["oor_richting"]) * e
    M["oor_lengte"] = M0["oor_lengte"] * float(np.linalg.norm(np.array(M["oor_richting"])) / np.linalg.norm(t0))
    WT.MAAT_T.clear()
    WT.MAAT_T.update(M)
    log("MAAT: kop", np.round(M["kop"], 3).tolist(), "staart", np.round(M["staart"], 3).tolist())


# --- Textuur ----------------------------------------------------------------------------------------------
def textuur(o, A, ref_ext):
    me = o.data
    oud = me.materials[0]
    img = bpy.data.images.new("wolf_tripo_kleur", TEX, TEX)
    pos, nrm, gezet = WT.texels(img, o)
    nx = np.abs(nrm[..., 0])
    q = A.m_naar_ref(pos[..., 1].ravel(), pos[..., 2].ravel())
    # scherend: naar binnen bemonsteren (beeldnormaal = (ny, -nz)), tot 5 px
    bn = np.stack([nrm[..., 1].ravel(), -nrm[..., 2].ravel()], 1)
    bn /= np.linalg.norm(bn, axis=1, keepdims=True) + 1e-6
    q = q - bn * (5.0 * (1 - nx.ravel()) ** 2)[:, None]
    rgb = PJ.bilineair(ref_ext, q[:, 0], q[:, 1]).reshape(TEX, TEX, 3)
    # fijne ruis (vacht), sterker waar de projectie uitsmeert (boven, onder, voor, achter)
    fijn = BM.ruis(pos.reshape(-1, 3), f=(120, 60, 120), seed=3).reshape(TEX, TEX)
    rgb = rgb * (1 + (0.05 + 0.10 * (1 - nx)) * fijn)[..., None]
    rgb = np.clip(rgb, 0, 1).astype(np.float32)
    rgb, _ = PJ.uitbreiden(rgb, gezet, 6)                            # naden: kleur over de UV-rand
    # texels() rekent al in Blender-pixelvolgorde (rij 0 = v 0 = onder): niet omdraaien
    img.pixels.foreach_set(np.concatenate([rgb, np.ones((TEX, TEX, 1), np.float32)], 2).ravel())
    img.pack()
    m = bpy.data.materials.new("mat_lijf")
    m.use_nodes = True
    b = m.node_tree.nodes["Principled BSDF"]
    t = m.node_tree.nodes.new("ShaderNodeTexImage")
    t.image = img
    m.node_tree.links.new(t.outputs["Color"], b.inputs["Base Color"])
    b.inputs["Roughness"].default_value = 0.9
    b.inputs["Metallic"].default_value = 0.0
    b.inputs["Specular IOR Level"].default_value = 0.3
    m.use_backface_culling = True
    me.materials.clear()
    me.materials.append(m)
    bpy.data.materials.remove(oud)
    log("textuur", TEX, "gezet", int(gezet.sum()), "texels")
    return t, img, q.reshape(TEX, TEX, 2)


def donker(img, qref, gezet):
    """Donkere wolf: zwart met de structuur van de grijze, witte keel/borst (gebied in referentiepixels: onder
    de kaak tot tussen de voorpoten), rode ogen blijven."""
    w, h = img.size
    A = np.array(img.pixels[:], np.float32).reshape(h, w, 4)
    rgb = A[..., :3]
    lum = rgb @ np.array([0.2126, 0.7152, 0.0722], np.float32)
    rood = WT.is_rood(rgb)
    cx, cy = qref[..., 0], qref[..., 1]
    keel = gladstap(40, 70, cx) * gladstap(205, 160, cx) * gladstap(178, 196, cy) * gladstap(250, 232, cy)
    kin = gladstap(30, 50, cx) * gladstap(110, 90, cx) * gladstap(196, 203, cy)
    wit = np.clip(np.maximum(keel, kin), 0, 1)
    ln = lum / max(float(np.percentile(lum[gezet], 95)), 1e-3)
    zwart = (0.03 + 0.12 * ln)[..., None] * np.array([1.0, 0.97, 0.95], np.float32)
    licht = (0.42 + 0.40 * ln)[..., None] * np.array([1.0, 0.98, 0.95], np.float32)
    uit = zwart * (1 - wit[..., None]) + licht * wit[..., None]
    uit = np.where(rood[..., None], rgb, uit)
    D = bpy.data.images.new("donkere_wolf_tripo_kleur", w, h)
    D.pixels.foreach_set(np.concatenate([uit, A[..., 3:]], 2).astype(np.float32).ravel())
    D.pack()
    return D


# --- Previews (lokaal) -------------------------------------------------------------------------------------
def zij_vergelijk(sc, rig, ref, A):
    """Ons model orthografisch van links (kop links, camera op +x), naast de referentie op dezelfde maat."""
    WT.rust(rig)
    ppm = 1.0 / A.s
    H, W = ref.shape[:2]
    yc, zc = A.ref_naar_m(np.array([[W / 2, H / 2]]))          # beeldmidden = referentiemidden in m
    BM.studio(sc, ppm, W / ppm, H / ppm, doel=(0, float(yc[0]), float(zc[0])), yaw=0, pitch=0)
    sc.objects["cam"].data.ortho_scale = W / ppm
    a = BM.render_np(sc, os.path.join(bpy.app.tempdir, "zij_tripo.png"))
    al = a[..., 3:]
    bg = np.ones_like(a[..., :3]) * 0.3
    ons = a[..., :3] * al + bg * (1 - al)
    BM.schrijf(BM.onder(np.concatenate([ref, ons], 1)), os.path.join(UIT, "wolf_tripo_zij.png"))


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
    BM.schrijf(BM.onder(*rijen), os.path.join(UIT, "wolf_tripo_poses.png"))
    WT.rust(rig)


def ankers_beeld(A, ref):
    """Beide contouren met de ankers (zelfde kleur = paar), naast elkaar."""
    H = max(ref.shape[0], int(A.cs[:, 1].max()) + 5)
    links = np.ones((H, int(A.cs[:, 0].max()) + 5, 3), np.float32) * 0.85
    rechts = np.ones((H, ref.shape[1], 3), np.float32)
    rechts[:ref.shape[0]] = ref
    for c, img in ((A.cs, links), (A.cd, rechts)):
        for x, y in c.astype(int):
            img[np.clip(y, 0, H - 1), np.clip(x, 0, img.shape[1] - 1)] = (1, 0, 0)
    rng = np.random.default_rng(1)
    for i, j in A.ank:
        k = rng.random(3)
        for (x, y), img in ((A.cs[i], links), (A.cd[j], rechts)):
            x, y = int(x), int(y)
            img[max(y - 3, 0):y + 4, max(x - 3, 0):x + 4] = k
    BM.schrijf(np.concatenate([links, rechts], 1), os.path.join(UIT, "wolf_tripo_ankers.png"))


# --- Hoofdlijn ----------------------------------------------------------------------------------------------
def main():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    sc = bpy.context.scene
    sc.render.fps = R.FPS
    sc.frame_start = 0
    ref, mref, ref_ext = referentie()
    lijf = WT.laad()
    me = lijf.data
    P = np.array([v.co for v in me.vertices], float)
    T = []
    for p in me.polygons:
        vs = list(p.vertices)
        T += [(vs[0], vs[k], vs[k + 1]) for k in range(1, len(vs) - 1)]
    A = Afbeelding(P, np.array(T), mref)
    if "ankers" in OPTS:
        ankers_beeld(A, ref)
    vervorm(lijf, A)
    maat(A)
    WT.KOP_Z = 0.40
    tex0, img, qref = textuur(lijf, A, ref_ext)
    rig = WT.bouw_rig()
    sk = WT.skin(lijf, rig)
    tex = WT.Texen([tex0, WT.extras(lijf, rig, sk, img, haar=0.0)])
    info = R.bouw_animaties(rig)
    log("animaties", list(info))
    log("rek (p99.9 / max/2)", json.dumps(WT.rek(lijf, rig, sc)))
    _, _, gezet = WT.texels(img, lijf)
    kleuren = {"wolf": img, "donker": donker(img, qref, gezet)}
    if "geen_export" not in OPTS:
        os.makedirs(WT.ASSETS, exist_ok=True)
        tex.image = img
        WT.exporteer(GLB["wolf"])
        tex.image = kleuren["donker"]
        WT.exporteer(GLB["donker"])
        tex.image = img
    os.makedirs(UIT, exist_ok=True)
    if "zij" in OPTS:
        zij_vergelijk(sc, rig, ref, A)
    if "poses" in OPTS:
        poses(sc, rig, tex, kleuren)
    if "blend" in OPTS:
        bpy.ops.wm.save_as_mainfile(filepath=os.path.join(UIT, "wolf_tripo.blend"))
    log("KLAAR")


if __name__ == "__main__":
    main()
