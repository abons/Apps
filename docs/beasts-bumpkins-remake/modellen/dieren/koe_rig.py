"""Viervoeterskelet + animaties voor de koe (Beasts & Bumpkins-remake). Herbruikbaar: de wolf geeft
een eigen MAAT (andere gewrichten, schaal) en eigen gangparameters mee.

Draaien (headless):
  blender -b -P koe_rig.py [-- clip ...]   -> koe_anim.json en preview/koe_rig_test.blend (alleen skelet),
                                              plus een glijcontrole van de hoeven in de log
Als module (de modeller, koe.py):
  import koe_rig
  rig = koe_rig.bouw_rig(maat=None)            # alleen het skelet
  info = koe_rig.bouw_animaties(rig)           # acties + sidecar-dict, zie CLIPS

RUSTPOSE: staand, natuurlijke beenhoeken (geen gestrekte benen), kop iets omlaag. Armatuur `koe_rig`
in meters, kijkt naar Blender -Y (glTF/Godot +Z), hoeven op z=0, oorsprong onder het midden van de
romp. Links = +X (gezien vanuit het dier). Armatuur-object staat op identiteit.

BONEN (geen prefix; Left/Right zoals bij de bumpkin):
  romp: Hips (bekken, wortel; van staartwortel naar voren), Spine, Spine1, Spine2 (schoft)
  hals/kop: Neck, Neck1, Head (van de nek naar de snuit), Jaw (onderkaak, kind van Head),
            {Left,Right}Ear (kind van Head)
  staart: Tail, Tail1, Tail2, Tail3 (kind van Hips, hangt omlaag; Tail3 = kwast)
  voorbeen: {L,R}Scapula (kind van Spine2), {L,R}UpperArm, {L,R}ForeArm, {L,R}FrontCannon (pijp),
            {L,R}FrontHoof (kogel -> teen: koot + klauw)
  achterbeen: {L,R}Thigh (kind van Hips), {L,R}Shin, {L,R}HindCannon, {L,R}HindHoof
  socket zonder deform: `prop_bel` (kind van Neck1, kop = onderkant keel, lokale +Y = omlaag,
  lokale +Z = naar voren). Wordt per frame zo gezet dat de bel recht naar beneden hangt (alleen de
  yaw van de hals gaat mee); de bel-mesh hangt er als kind (parent_type BONE) onder.

BOTROLLEN (lokale X = buig-as, alle animatie is zuivere rotatie):
  romp, hals, kop, kaak: lokale Z = buikzijde -> +rx: punt omlaag (voorover/knikken, kaak open),
     +rz: punt naar rechts, ry = rol om de lengteas.
  benen en hoeven: lokale Z = voor -> +rx: punt naar voren (zoals de bumpkinbenen).
  staart: lokale Z = achter -> +rx: staart omhoog/naar achteren, +rz: zwiep naar rechts.
  oren: lokale Z = omhoog -> +rx: oor omhoog (beide kanten), rz: links + = naar achteren,
     rechts + = naar voren.
  Spiegelregel links/rechts: rx gelijk, ry en rz negatief.

ANIMATIES (24 fps, alleen rotaties + Hips-locatie). Benen per frame via IK uitgerekend en daarna
gewoon gekeyframed: per been een kogeldoel (dx naar buiten, dy, lift t.o.v. de rust-kogel), een
pijphoek `ca` en een hoefbuiging `hp` (graden om wereld-X; + = onderkant/teen naar achteren).
Daaruit volgt het gewricht boven de pijp (voorknie / hak), en tweebots-IK zet opperarm+onderarm
resp. dij+scheen. Een geplant been (lift 0, hp 0) staat dus exact stil op de grond.
Clips: idle, lopen, grazen, gemolken_worden, sterven, geboorte (kalf staat op; speel op een koe
met schaal ~0,5). Elke actie heeft custom property `snelheid_mps`; zie ook koe_anim.json.
"""
import json
import math
import os
import sys

import bpy
from mathutils import Euler, Quaternion, Vector

HERE = os.path.dirname(os.path.abspath(__file__))

FPS = 24
LINKS, RECHTS = "Left", "Right"
VOOR, ACHTER = Vector((0, -1, 0)), Vector((0, 1, 0))
BOVEN, ONDER = Vector((0, 0, 1)), Vector((0, 0, -1))

# --- Maten (meters, basis; alles x `schaal`) -----------------------------------------------------
# Koe: schoft 1,15 x 1,05 = 1,21 m, snuit-zitbeen 1,83 m. Uit de sprites (cowwalk zijaanzicht: 45 px
# snuit-staart, kop 1,38 m bij 21,9 px/m en cos 30) en de man van 1,37 m: een kleine, stevige koe.
# (y, z)-paren in het zijvlak, x apart per been. De wolf geeft hier zijn eigen tabel.
MAAT = {
    "schaal": 1.05,
    "heup": (0.45, 1.06),                                   # Hips-kop (bekken)
    "rug": [(0.20, 1.08), (-0.05, 1.09), (-0.30, 1.10), (-0.50, 1.12)],   # staarten Hips, Spine, Spine1, Spine2
    "nek": [(-0.46, 0.92), (-0.71, 1.04), (-0.92, 1.18)],  # Neck-kop, Neck1-kop, Neck1-staart
    "kop": [(-0.95, 1.23), (-1.17, 0.95)],                  # Head: nek (achter de oren) -> snuit
    "kaak": [(-1.01, 1.06), (-1.14, 0.91)],                 # Jaw: kaakgewricht -> kin
    "oor": (0.075, -0.98, 1.22), "oor_richting": (1.0, 0.2, -0.15), "oor_lengte": 0.19,
    "staart": [(0.58, 1.06), (0.68, 0.88), (0.70, 0.68), (0.70, 0.48), (0.69, 0.32)],
    "voor_x": 0.165,
    # schoftblad-top, schoudergewricht, elleboog, voorknie, kogel, teen
    "voorbeen": [(-0.36, 1.06), (-0.52, 0.80), (-0.38, 0.57), (-0.45, 0.31), (-0.46, 0.12), (-0.53, 0.0)],
    "achter_x": 0.155,
    # heupgewricht, knie (stifle), hak, kogel, teen
    "achterbeen": [(0.38, 0.93), (0.27, 0.60), (0.46, 0.38), (0.43, 0.12), (0.36, 0.0)],
    "bel": (-0.70, 0.82),                                   # onderkant keel, waar de halsband de bel draagt
}

VOORBEEN = ["Scapula", "UpperArm", "ForeArm", "FrontCannon", "FrontHoof"]
ACHTERBEEN = ["Thigh", "Shin", "HindCannon", "HindHoof"]
POTEN = {"LF": (LINKS, True), "RF": (RECHTS, True), "LH": (LINKS, False), "RH": (RECHTS, False)}


def _p(m, yz, x=0.0):
    s = m["schaal"]
    return Vector((x * s, yz[0] * s, yz[1] * s))


# --- Skelet -------------------------------------------------------------------------------------
def bouw_rig(maat=None, naam="koe_rig"):
    """Bouwt alleen het armatuur in de huidige scene en geeft het object terug."""
    m = dict(MAAT)
    m.update(maat or {})
    s = m["schaal"]
    arm_data = bpy.data.armatures.new(naam)
    rig = bpy.data.objects.new(naam, arm_data)
    bpy.context.scene.collection.objects.link(rig)
    bpy.context.view_layer.objects.active = rig
    rig.select_set(True)
    rig["schaal"] = s
    rig["schofthoogte"] = m["rug"][-1][1] * s
    rig["rustpose"] = "staand, kijkt naar -Y"
    bpy.ops.object.mode_set(mode="EDIT")
    eb = arm_data.edit_bones

    def bot(nm, ouder, kop, staart, roll, deform=True):
        b = eb.new(nm)
        b.head, b.tail = Vector(kop), Vector(staart)
        b.align_roll(roll)
        if ouder:
            b.parent = eb[ouder]
        b.use_connect = False
        b.use_deform = deform
        return b

    P = lambda yz, x=0.0: _p(m, yz, x)
    rug = [m["heup"]] + m["rug"]
    bot("Hips", None, P(rug[0]), P(rug[1]), ONDER)
    for i, nm in enumerate(["Spine", "Spine1", "Spine2"]):
        bot(nm, ["Hips", "Spine", "Spine1"][i], P(rug[i + 1]), P(rug[i + 2]), ONDER)
    nk = m["nek"]
    bot("Neck", "Spine2", P(nk[0]), P(nk[1]), ONDER)
    bot("Neck1", "Neck", P(nk[1]), P(nk[2]), ONDER)
    bot("Head", "Neck1", P(m["kop"][0]), P(m["kop"][1]), ONDER)
    bot("Jaw", "Head", P(m["kaak"][0]), P(m["kaak"][1]), ONDER)
    st = m["staart"]
    for i, nm in enumerate(["Tail", "Tail1", "Tail2", "Tail3"]):
        bot(nm, "Hips" if i == 0 else ["Tail", "Tail1", "Tail2"][i - 1], P(st[i]), P(st[i + 1]), ACHTER)
    o = m["oor"]
    od = Vector(m["oor_richting"]).normalized() * m["oor_lengte"] * s
    for zijde, sg in ((LINKS, 1), (RECHTS, -1)):
        kop = Vector((sg * o[0] * s, o[1] * s, o[2] * s))
        bot(zijde + "Ear", "Head", kop, kop + Vector((sg * od.x, od.y, od.z)), BOVEN)
        vb, x = m["voorbeen"], sg * m["voor_x"]
        bot(zijde + "Scapula", "Spine2", P(vb[0], x * 0.8), P(vb[1], x), VOOR)
        ouder = zijde + "Scapula"
        for i, nm in enumerate(VOORBEEN[1:]):
            bot(zijde + nm, ouder, P(vb[i + 1], x), P(vb[i + 2], x), VOOR)
            ouder = zijde + nm
        ab, x = m["achterbeen"], sg * m["achter_x"]
        ouder = "Hips"
        for i, nm in enumerate(ACHTERBEEN):
            bot(zijde + nm, ouder, P(ab[i], x), P(ab[i + 1], x), VOOR)
            ouder = zijde + nm
    b = m["bel"]
    bot("prop_bel", "Neck1", P(b), P((b[0], b[1] - 0.06)), VOOR, deform=False)
    bpy.ops.object.mode_set(mode="OBJECT")
    return rig


# --- Animatie: hulpfuncties ----------------------------------------------------------------------
def pchip(pts, x, eind_vlak):
    """(Kopie uit bumpkin_rig.py.) Monotone kubische Hermite door (x, y)-punten: geen overshoot, rustpunt op elke piek."""
    xs = [p[0] for p in pts]
    ys = [p[1] for p in pts]
    n = len(xs)
    if n == 1:
        return ys[0]
    h = [xs[i + 1] - xs[i] for i in range(n - 1)]
    d = [(ys[i + 1] - ys[i]) / h[i] for i in range(n - 1)]
    mm = [0.0] * n
    for i in range(1, n - 1):
        if d[i - 1] * d[i] <= 0:
            mm[i] = 0.0
        else:
            w1, w2 = 2 * h[i] + h[i - 1], h[i] + 2 * h[i - 1]
            mm[i] = (w1 + w2) / (w1 / d[i - 1] + w2 / d[i])
    if eind_vlak:
        mm[0] = mm[-1] = 0.0
    else:
        mm[0], mm[-1] = d[0], d[-1]
    if x <= xs[0]:
        return ys[0]
    if x >= xs[-1]:
        return ys[-1]
    i = max(j for j in range(n - 1) if xs[j] <= x)
    t = (x - xs[i]) / h[i]
    t2, t3 = t * t, t * t * t
    return ((2 * t3 - 3 * t2 + 1) * ys[i] + (t3 - 2 * t2 + t) * h[i] * mm[i]
            + (-2 * t3 + 3 * t2) * ys[i + 1] + (t3 - t2) * h[i] * mm[i + 1])


def reeks(punten, N, lus):
    """Waarden op frame 0..N uit sleutelpunten [(frame, waarde)]. Lus: periodiek, frame N = frame 0."""
    punten = sorted(p for p in punten if not (lus and p[0] >= N))
    if lus:
        ext = [(f - N, v) for f, v in punten] + punten + [(f + N, v) for f, v in punten]
        return [pchip(ext, f, False) for f in range(N + 1)]
    return [pchip(punten, f, True) for f in range(N + 1)]


def rx(g):
    return Quaternion((1, 0, 0), math.radians(g))


def rzq(g):
    return Quaternion((0, 0, 1), math.radians(g))


def eul(v):
    return Euler((math.radians(v[0]), math.radians(v[1]), math.radians(v[2])), "XYZ").to_quaternion()


def bump(f, start, duur, N=None):
    """Gladde bult 0..1..0 van frame start over duur frames (periodiek als N gegeven)."""
    u = f - start
    if N:
        u %= N
    if u < 0 or u > duur:
        return 0.0
    return math.sin(math.pi * u / duur) ** 2


def golf(f, N, n=1, fase=0.0):
    return math.sin(2 * math.pi * n * f / N + fase)


class Maten:
    """Alles wat de animatie uit het rig leest (zodat een andere MAAT meeloopt)."""

    def __init__(self, rig):
        bn = rig.data.bones
        self.rig = rig
        self.s = float(rig.get("schaal", 1.0))
        self.rr = {b.name: b.matrix_local.to_quaternion() for b in bn}
        self.ouder = {b.name: (b.parent.name if b.parent else None) for b in bn}
        self.kop = {b.name: b.head_local.copy() for b in bn}
        self.staart = {b.name: b.tail_local.copy() for b in bn}
        diep = lambda n: 0 if self.ouder[n] is None else 1 + diep(self.ouder[n])
        self.volgorde = sorted(self.ouder, key=diep)
        self.been = {}
        for poot, (zijde, voor) in POTEN.items():
            ks = [zijde + n for n in (VOORBEEN[1:] if voor else ACHTERBEEN)]
            self.been[poot] = ks
        self.boven = [b for b in self.volgorde if not any(b in ks for ks in self.been.values())
                      and b != "prop_bel"]


def ik2(wortel, doel, L1, L2, pool):
    """Tweebots-IK: richtingen van bot 1 en 2 en of het doel bereikbaar was."""
    d = doel - wortel
    afstand = d.length
    ok = afstand <= (L1 + L2) * 0.999
    ac = min(max(afstand, abs(L1 - L2) + 1e-3), (L1 + L2) * 0.999)
    richt = d.normalized()
    cosa = (L1 ** 2 + ac ** 2 - L2 ** 2) / (2 * L1 * ac)
    alfa = math.acos(max(-1.0, min(1.0, cosa)))
    p = pool - richt * pool.dot(richt)
    p.normalize()
    gewricht = wortel + richt * (L1 * math.cos(alfa)) + p * (L1 * math.sin(alfa))
    eind = wortel + richt * ac
    return (gewricht - wortel).normalized(), (eind - gewricht).normalized(), ok


TEKORT = {"n": 0}          # aantal onbereikbare IK-doelen (= glijden), voor de log


def pose_frame(M, pose):
    """pose: {'T': (x,y,z), bot: (rx,ry,rz) graden, 'LF'..: (dx, dy, lift, hp, ca)} -> lokale quats, Hips-loc."""
    rr = M.rr
    T = Vector(pose.get("T", (0, 0, 0)))
    qs, Dw, pos = {}, {}, {}
    for b in M.boven:
        q = eul(pose.get(b, (0, 0, 0)))
        qs[b] = q
        Dl = rr[b] @ q @ rr[b].inverted()
        p = M.ouder[b]
        if p is None:
            Dw[b], pos[b] = Dl, M.kop[b] + T
        else:
            Dw[b], pos[b] = Dw[p] @ Dl, pos[p] + Dw[p] @ (M.kop[b] - M.kop[p])
    for poot, ks in M.been.items():
        zijde, voor = POTEN[poot]
        sg = 1 if zijde == LINKS else -1
        dx, dy, lift, hp, ca = pose.get(poot, (0, 0, 0, 0, 0))
        b1, b2, b3, b4 = ks
        p = M.ouder[b1]
        wortel = pos[p] + Dw[p] @ (M.kop[b1] - M.kop[p])
        F = M.kop[b4] + Vector((sg * dx, dy, lift))
        Dc = rx(ca)
        C = F - Dc @ (M.kop[b4] - M.kop[b3])
        L1 = (M.kop[b2] - M.kop[b1]).length
        L2 = (M.kop[b3] - M.kop[b2]).length
        pool = Dw[p] @ (ACHTER if voor else VOOR)
        r1, r2, ok = ik2(wortel, C, L1, L2, pool)
        if not ok:
            TEKORT["n"] += 1
        D1 = (M.kop[b2] - M.kop[b1]).normalized().rotation_difference(r1)
        D2 = (M.kop[b3] - M.kop[b2]).normalized().rotation_difference(r2)
        Dh = rx(hp)
        qs[b1] = rr[b1].inverted() @ Dw[p].inverted() @ D1 @ rr[b1]
        qs[b2] = rr[b2].inverted() @ D1.inverted() @ D2 @ rr[b2]
        qs[b3] = rr[b3].inverted() @ D2.inverted() @ Dc @ rr[b3]
        qs[b4] = rr[b4].inverted() @ Dc.inverted() @ Dh @ rr[b4]
    # bel hangt recht omlaag; alleen de yaw van de hals draait mee
    f = Dw["Neck1"] @ VOOR
    yaw = math.degrees(math.atan2(-f.x, -f.y)) if f.xy.length > 1e-4 else 0.0
    qs["prop_bel"] = rr["prop_bel"].inverted() @ Dw["Neck1"].inverted() @ rzq(-yaw) @ rr["prop_bel"]
    return qs, rr["Hips"].inverted() @ T


def sleutels(keys, N, lus):
    """keys {frame: pose} -> lijst van N+1 poses (pchip per component; ontbrekend = rust)."""
    kanalen = {}
    for k in keys.values():
        for c, v in k.items():
            kanalen[c] = len(v)
    uit = [dict() for _ in range(N + 1)]
    frames = sorted(keys)
    for c, n in kanalen.items():
        for i in range(n):
            nul = 0.0
            pts = [(f, keys[f][c][i] if c in keys[f] else nul) for f in frames]
            r = reeks(pts, N, lus)
            for f in range(N + 1):
                uit[f].setdefault(c, [0.0] * n)[i] = r[f]
    return uit


def optellen(poses, extra):
    """Telt per frame de procedurele lagen (dict van kanaal -> functie(f) -> tuple) erbij op."""
    for f, p in enumerate(poses):
        for c, fn in extra.items():
            v = fn(f)
            o = p.get(c, [0.0] * len(v))
            p[c] = [a + b for a, b in zip(o, v)]
    return poses


def schrijf_actie(rig, M, naam, poses, lus, extra):
    act = bpy.data.actions.new(naam)
    act.use_fake_user = True
    if not rig.animation_data:
        rig.animation_data_create()
    rig.animation_data.action = act
    pb = rig.pose.bones
    for b in pb:
        b.rotation_mode = "QUATERNION"
    vorige = {}
    N = len(poses) - 1
    for f, pose in enumerate(poses):
        qs, loc = pose_frame(M, pose)
        for nb, q in qs.items():
            v = vorige.get(nb)
            if v is not None and v.dot(q) < 0:
                q = -q
            vorige[nb] = q.copy()
            pb[nb].rotation_quaternion = q
            pb[nb].keyframe_insert("rotation_quaternion", frame=f)
        pb["Hips"].location = loc
        pb["Hips"].keyframe_insert("location", frame=f)
    for kk, vv in extra.items():
        act[kk] = vv
    act.use_frame_range = True
    act.frame_start, act.frame_end = 0, N
    if lus:
        act.use_cyclic = True
    return act


# --- Gedeelde lagen ------------------------------------------------------------------------------
def staart_zwiep(N, n, amp=(6, 10, 15, 20), achter=(3, 1, 0, 0), fase=0.0, vertraging=0.8, extra=None):
    """Zwiepende staart: golf langs de staartbotten (later bot = later en verder)."""
    uit = {}
    for i, nm in enumerate(["Tail", "Tail1", "Tail2", "Tail3"]):
        def fn(f, i=i):
            g = golf(f, N, n, fase - vertraging * i)
            e = extra(f) if extra else 1.0
            return (achter[i], 0.0, amp[i] * g * e)
        uit[nm] = fn
    return uit


def kauwen(N, n, open_=5.0, maal=3.0):
    """Herkauwen: kaak open/dicht plus zijwaarts malen (koeien kauwen opzij)."""
    return {"Jaw": lambda f: (open_ * (0.5 - 0.5 * math.cos(2 * math.pi * n * f / N)), 0.0,
                              maal * golf(f, N, n, math.pi / 2))}


def oorflap(N, links, rechts, amp=28.0):
    """Oorflap op de gegeven frames (links/rechts lijst van startframes), plus een klein trillen."""
    def L(f):
        b = sum(bump(f, s, 7, N) for s in links)
        return (amp * b + 2 * golf(f, N, 3), 0.0, 14 * b)
    def R(f):
        b = sum(bump(f, s, 7, N) for s in rechts)
        return (amp * b + 2 * golf(f, N, 3, 1.3), 0.0, -14 * b)
    return {"LeftEar": L, "RightEar": R}


# --- Clips ---------------------------------------------------------------------------------------
def clip_idle(M):
    N = 96
    s = M.s
    poses = [dict() for _ in range(N + 1)]
    lagen = {
        "T": lambda f: (0.008 * s * golf(f, N, 1), 0.0, -0.004 * s + 0.002 * s * golf(f, N, 2)),
        "Hips": lambda f: (0.0, 0.6 * golf(f, N, 1, 0.5), 0.8 * golf(f, N, 1)),
        "Spine1": lambda f: (0.6 * golf(f, N, 2), 0.0, -0.5 * golf(f, N, 1)),
        "Neck": lambda f: (-2 * bump(f, 66, 22, N), 0.0, -7 * bump(f, 20, 40, N)),
        "Neck1": lambda f: (1.5 * golf(f, N, 2, 1.0), 0.0, -7 * bump(f, 22, 40, N)),
        "Head": lambda f: (4 * bump(f, 70, 14, N), 0.0, -5 * bump(f, 24, 38, N)),
    }
    lagen.update(kauwen(N, 8))
    lagen.update(oorflap(N, [14, 58], [36, 80]))
    lagen.update(staart_zwiep(N, 2, extra=lambda f: 0.5 + 0.5 * bump(f, 40, 40, N)))
    optellen(poses, lagen)
    return N, True, poses, {"snelheid_mps": 0.0}, None


def gang(M, N, Ls, beta, fases, A_B, lift, ca_td, ca_lo, ca_swing, hp_swing):
    """Hoefbanen voor een loop in place. Geeft {poot: functie(f) -> (dx, dy, lift, hp, ca)} en v."""
    s = M.s
    D = Ls * beta
    v = Ls * FPS / N
    uit = {}
    for poot, fase in fases.items():
        voor = POTEN[poot][1]
        a, b = A_B[voor]
        A, B = D * a, D * b
        h = lift[voor] * s
        cs, hs = ca_swing[voor], hp_swing[voor]
        td, lo = ca_td[voor], ca_lo[voor]

        def fn(f, fase=fase, A=A, B=B, h=h, cs=cs, hs=hs, td=td, lo=lo):
            u = (f / N - fase) % 1.0
            if u < beta:
                t = u / beta
                return (0.0, -A + D * t, 0.0, 0.0, td + (lo - td) * t)
            w = (u - beta) / (1 - beta)
            m = 0.35 * D * (1 - beta) / beta
            h00, h10 = 2 * w ** 3 - 3 * w ** 2 + 1, w ** 3 - 2 * w ** 2 + w
            h01, h11 = -2 * w ** 3 + 3 * w ** 2, w ** 3 - w ** 2
            y = h00 * B + h10 * m + h01 * (-A) + h11 * m
            lf = h * math.sin(math.pi * w) ** 1.3 * (1.15 - 0.3 * w)
            ca = pchip([(0, lo)] + cs + [(1, td)], w, False)
            hp = pchip([(0, 0.0)] + hs + [(1, 0.0)], w, True)
            return (0.008 * s * math.sin(math.pi * w), y, lf, hp, ca)
        uit[poot] = fn
    return uit, v


def clip_lopen(M):
    """Viertakt-stap (laterale volgorde LH, LF, RH, RF), ~0,86 m/s, 1,17 s per cyclus."""
    N = 28
    s = M.s
    Ls = 0.90 * s
    fases = {"LH": 0.0, "LF": 0.25, "RH": 0.5, "RF": 0.75}
    benen, v = gang(M, N, Ls, 0.64, fases,
                    A_B={True: (0.56, 0.44), False: (0.5, 0.5)},
                    lift={True: 0.085, False: 0.075},
                    ca_td={True: -8.0, False: -6.0}, ca_lo={True: 24.0, False: 20.0},
                    ca_swing={True: [(0.35, 66.0), (0.8, 0.0)], False: [(0.35, 32.0), (0.8, -6.0)]},
                    hp_swing={True: [(0.35, 60.0), (0.75, 8.0)], False: [(0.35, 45.0), (0.75, 6.0)]})
    poses = [dict() for _ in range(N + 1)]
    A = 0.90 * s * 0.64 * 0.56

    def scap(poot):
        return lambda f: (7.0 * -benen[poot](f)[1] / A, 0.0, 0.0)
    lagen = dict(benen)
    lagen.update({
        "T": lambda f: (0.006 * s * golf(f, N, 1, 0.6), 0.0, -0.012 * s + 0.007 * s * golf(f, N, 2, 0.4)),
        "Hips": lambda f: (0.8 * golf(f, N, 2, 1.2), 1.6 * golf(f, N, 1, 0.3), 1.5 * golf(f, N, 1)),
        "Spine": lambda f: (0.0, -0.5 * golf(f, N, 1, 0.3), -0.8 * golf(f, N, 1)),
        "Spine1": lambda f: (0.0, -0.5 * golf(f, N, 1, 0.3), -0.8 * golf(f, N, 1)),
        "Spine2": lambda f: (-0.5 * golf(f, N, 2, 1.2), -0.6 * golf(f, N, 1, 0.3 + math.pi), 0.6 * golf(f, N, 1)),
        "Neck": lambda f: (3 + 2.5 * golf(f, N, 2, 2.2), 0.0, 1.5 * golf(f, N, 1, 0.8)),
        "Neck1": lambda f: (1.5 * golf(f, N, 2, 2.6), 0.0, 1.0 * golf(f, N, 1, 1.0)),
        "Head": lambda f: (-1.5 * golf(f, N, 2, 2.6), 0.0, 0.0),
        "LeftScapula": scap("LF"), "RightScapula": scap("RF"),
    })
    lagen.update(staart_zwiep(N, 1, amp=(4, 6, 9, 12), achter=(2, 2, 1, 0)))
    lagen.update(oorflap(N, [], [], amp=0.0))
    optellen(poses, lagen)
    return N, True, poses, {"snelheid_mps": v}, None


def clip_grazen(M):
    """Kop aan de grond, rukken aan het gras, kauwen; één voorpoot een stap naar voren."""
    N = 72
    s = M.s
    poses = [dict() for _ in range(N + 1)]
    lagen = {
        "T": lambda f: (0.0, 0.0, -0.035 * s),
        "Hips": lambda f: (3.0, 0.0, 0.6 * golf(f, N, 1)),
        "Spine2": lambda f: (2.0, 0.0, 0.0),
        "Neck": lambda f: (42 + 3 * bump(f, 30, 10, N), 0.0, 5 * golf(f, N, 1)),
        "Neck1": lambda f: (36, 0.0, 4 * golf(f, N, 1, -0.4)),
        "Head": lambda f: (-30 - 10 * bump(f, 32, 8, N) - 8 * bump(f, 62, 8, N), 0.0, 3 * golf(f, N, 1, -0.8)),
        "LF": lambda f: (0.0, -0.13 * s, 0.0, 0.0, -10.0),
        "RF": lambda f: (0.0, 0.03 * s, 0.0, 0.0, 0.0),
        "LeftScapula": lambda f: (8.0, 0.0, 0.0),
    }
    lagen.update(kauwen(N, 6, open_=6.0, maal=4.0))
    lagen.update(oorflap(N, [10], [46]))
    lagen.update(staart_zwiep(N, 2, amp=(5, 8, 12, 16)))
    optellen(poses, lagen)
    return N, True, poses, {"snelheid_mps": 0.0}, None


def clip_gemolken(M):
    """Stil staan terwijl ze gemolken wordt (melker rechts): rechterachterpoot iets naar achteren,
    herkauwen, staart zwiept, één keer omkijken naar rechts."""
    N = 96
    s = M.s
    poses = [dict() for _ in range(N + 1)]
    kijk = lambda f: bump(f, 28, 44, N)
    lagen = {
        "T": lambda f: (-0.006 * s + 0.003 * s * golf(f, N, 1), 0.0, -0.006 * s + 0.002 * s * golf(f, N, 2)),
        "Hips": lambda f: (0.0, -0.8, -0.6 + 0.5 * golf(f, N, 1)),
        "Spine1": lambda f: (0.6 * golf(f, N, 2), 0.0, 2 * kijk(f)),
        "Spine2": lambda f: (0.0, 0.0, 3 * kijk(f)),
        "Neck": lambda f: (-1.0, 0.0, 10 * kijk(f)),
        "Neck1": lambda f: (0.0, 0.0, 10 * kijk(f)),
        "Head": lambda f: (2.0, -6 * kijk(f), 8 * kijk(f)),
        "RH": lambda f: (0.01 * s, 0.09 * s, 0.0, 0.0, 4.0),
    }
    lagen.update(kauwen(N, 10))
    lagen.update(oorflap(N, [10, 70], [40]))
    lagen.update(staart_zwiep(N, 3, amp=(6, 10, 16, 22), extra=lambda f: 0.6 + 0.4 * golf(f, N, 1)))
    optellen(poses, lagen)
    return N, True, poses, {"snelheid_mps": 0.0}, None


def _lig(s):
    """Ligpose (borst/buik op de grond, benen gevouwen), gedeeld door sterven en geboorte."""
    return {"T": (0.0, 0.0, -0.36 * s), "Hips": (1.0, 0.0, 0.0), "Spine2": (-2.0, 0, 0),
            "LF": (0.06 * s, 0.22 * s, -0.075 * s, 115.0, 92.0), "RF": (0.06 * s, 0.22 * s, -0.075 * s, 115.0, 92.0),
            "LH": (0.20 * s, -0.22 * s, -0.075 * s, -40.0, -88.0), "RH": (0.20 * s, -0.22 * s, -0.075 * s, -40.0, -88.0)}


def _knielen(s):
    """Op de voorknieën, achterbenen gestrekt (tussenstand bij gaan liggen en opstaan)."""
    return {"T": (0.0, 0.03 * s, -0.10 * s), "Hips": (15.0, 0.0, 0.0), "Spine2": (-3.0, 0, 0),
            "Neck": (-14.0, 0, 0), "Head": (-6.0, 0, 0),
            "LF": (0.02 * s, 0.22 * s, -0.075 * s, 115.0, 92.0), "RF": (0.02 * s, 0.22 * s, -0.075 * s, 115.0, 92.0),
            "LH": (0.0, 0.0, 0.0, 0.0, 0.0), "RH": (0.0, 0.0, 0.0, 0.0, 0.0)}


def clip_sterven(M):
    """Wankelen, door de voorknieën, achterhand zakt, ligt; kop strekt naar voren op de grond."""
    s = M.s
    N = 60
    K = {}
    K[0] = {}
    K[8] = {"T": (0.01 * s, 0, -0.02 * s), "Hips": (2, 3, 0), "Neck": (8, 0, 4), "Head": (6, 0, 0),
            "LF": (0.0, 0.03 * s, 0.0, 0, 6), "RF": (0.0, -0.02 * s, 0.0, 0, 0)}
    K[14] = {"T": (0.01 * s, 0.01 * s, -0.05 * s), "Hips": (6, 3, 0), "Neck": (4, 0, 3), "Head": (4, 0, 0),
             "LF": (0.01 * s, 0.10 * s, 0.03 * s, 50, 45), "RF": (0.0, 0.05 * s, 0.0, 0, 12)}
    kn = _knielen(s)
    K[22] = {**kn, "Neck": (-8, 0, 3), "LH": (0, 0.02 * s, 0, 0, 3), "RH": (0, -0.01 * s, 0, 0, 0)}
    K[30] = {**kn, "T": (0.01 * s, 0.03 * s, -0.16 * s), "Hips": (12, 3, 0),
             "LH": (0.04 * s, -0.08 * s, 0.0, 0, 30), "RH": (0.04 * s, -0.06 * s, 0.0, 0, 26), "Neck": (-4, 0, 0)}
    lg = _lig(s)
    K[38] = {**lg, "T": (0.02 * s, 0, -0.37 * s), "Neck": (5, 0, 0), "Head": (-4, 0, 0)}
    K[48] = {**lg, "T": (0.03 * s, 0, -0.36 * s), "Hips": (2, 10, 0), "Spine": (0, 2, 0), "Spine2": (0, 2, 0),
             "Neck": (30, 0, 6), "Neck1": (14, 0, 4), "Head": (-36, 0, 0), "Jaw": (6, 0, 0),
             "LeftEar": (-25, 0, 10), "RightEar": (-25, 0, -10),
             "Tail": (-5, 0, 6), "Tail1": (-4, 0, 8)}
    K[60] = {**K[48], "Head": (-38, 0, 0), "LeftEar": (-30, 0, 10), "RightEar": (-30, 0, -10)}
    poses = sleutels(K, N, False)
    return N, False, poses, {"snelheid_mps": 0.0}, {"impact_s": 38 / FPS, "lig_s": 48 / FPS}


def clip_geboorte(M):
    """Pasgeboren kalf staat op: ligt, achterhand omhoog (knielt voor), dan de voorbenen. Op een koe
    met schaal ~0,5 spelen; eindigt in de rustpose zodat idle erop aansluit."""
    s = M.s
    N = 72
    lg = _lig(s)
    kn = _knielen(s)
    K = {0: {**lg, "Neck": (-6, 0, 0), "Head": (6, 0, 0)},
         10: {**lg, "Neck": (-10, 0, 3), "Head": (8, 0, 0), "LeftEar": (10, 0, 0), "RightEar": (10, 0, 0)},
         20: {**lg, "T": (0, 0.01 * s, -0.32 * s), "Hips": (6, 0, 0), "Neck": (-14, 0, 0)},
         32: {**kn, "T": (0, 0.03 * s, -0.12 * s), "Hips": (18, 0, 0)},
         42: {**kn},
         52: {**kn, "T": (0, 0.0, -0.05 * s), "Hips": (8, 0, 0), "Neck": (-6, 0, 0),
              "LF": (0.0, -0.08 * s, 0.0, 0, -6),
              "RF": (0.01 * s, 0.16 * s, -0.04 * s, 80, 70)},
         60: {"T": (0.01 * s, 0, -0.02 * s), "Hips": (2, -3, 0), "LF": (0.0, -0.06 * s, 0.0, 0, -4),
              "RF": (0.0, 0.0, 0.05 * s, 30, 30), "Neck": (-3, 0, 0)},
         66: {"T": (-0.01 * s, 0, -0.01 * s), "Hips": (0, 2, 0), "LF": (0.0, -0.06 * s, 0.0, 0, -4)},
         72: {}}
    poses = sleutels(K, N, False)
    return N, False, poses, {"snelheid_mps": 0.0}, {"impact_s": None, "staat_s": 60 / FPS}


CLIPS = [("idle", clip_idle), ("lopen", clip_lopen), ("grazen", clip_grazen),
         ("gemolken_worden", clip_gemolken), ("sterven", clip_sterven), ("geboorte", clip_geboorte)]


def bouw_animaties(rig, alleen=None, clips=None):
    """Voegt de acties toe aan `rig`. Geeft het sidecar-dict {naam: {loop, duur_s, snelheid_mps, impact_s}}."""
    M = Maten(rig)
    info = {}
    for naam, fn in (clips or CLIPS):
        if alleen and naam not in alleen:
            continue
        TEKORT["n"] = 0
        N, lus, poses, extra, tijd = fn(M)
        ex = dict(extra)
        for kk, vv in (tijd or {}).items():
            if vv is not None:
                ex[kk] = vv
        schrijf_actie(rig, M, naam, poses, lus, ex)
        if TEKORT["n"]:
            print(f"[koe_rig] let op: {naam}: {TEKORT['n']} onbereikbare beendoelen")
        imp = (tijd or {}).get("impact_s")
        d = {"loop": lus, "duur_s": round(N / FPS, 4), "snelheid_mps": round(extra["snelheid_mps"], 4),
             "impact_s": round(imp, 4) if imp is not None else None}
        for kk, vv in (tijd or {}).items():
            if kk != "impact_s" and vv is not None:
                d[kk] = round(vv, 4)
        info[naam] = d
    for b in rig.pose.bones:
        b.rotation_quaternion = (1, 0, 0, 0)
        b.location = (0, 0, 0)
    rig.animation_data.action = None
    return info


def zet_actie(rig, naam):
    act = bpy.data.actions[naam]
    ad = rig.animation_data_create()
    ad.action = act
    try:
        if ad.action_slot is None and len(act.slots):
            ad.action_slot = act.slots[0]
    except AttributeError:
        pass
    return act


def glijcontrole(rig, naam="lopen", v=None):
    """Max. verschuiving (m) van elke geplante kogel in wereldruimte (hoef - v*t, voor = -Y) tijdens de stand."""
    act = zet_actie(rig, naam)
    v = act.get("snelheid_mps", 0.0) if v is None else v
    sc = bpy.context.scene
    N = int(act.frame_end)
    uit = {}
    for poot, (zijde, voor) in POTEN.items():
        nb = zijde + ("FrontHoof" if voor else "HindHoof")
        pts = []
        for f in range(N + 1):
            sc.frame_set(f)
            pb = rig.pose.bones[nb]
            kop = rig.matrix_world @ pb.head
            teen = rig.matrix_world @ pb.tail
            pts.append((f, kop.y - v * f / FPS, kop.z, teen.z))   # voor = -Y
        laag = min(p[2] for p in pts)
        stand = [p for p in pts if p[2] < laag + 0.002]
        Ls = v * N / FPS                       # stand loopt over de lusgrens: modulo de cycluslengte
        ys = [((p[1] - stand[0][1] + Ls / 2) % Ls) - Ls / 2 if Ls > 0 else p[1] for p in stand]
        uit[poot] = {"stand_frames": len(stand), "glij_m": round(max(ys) - min(ys), 4),
                     "teen_min_z": round(min(p[3] for p in pts), 4)}
    rig.animation_data.action = None
    return uit


def main():
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    alleen = [a for a in argv if not a.startswith("-")] or None
    bpy.ops.wm.read_factory_settings(use_empty=True)
    sc = bpy.context.scene
    sc.render.fps = FPS
    sc.frame_start = 0
    rig = bouw_rig()
    info = bouw_animaties(rig, alleen)
    json.dump(info, open(os.path.join(HERE, "koe_anim.json"), "w"), indent=2)
    if "lopen" in info:
        print("GLIJ", json.dumps(glijcontrole(rig)))
    os.makedirs(os.path.join(HERE, "preview"), exist_ok=True)
    bpy.ops.wm.save_as_mainfile(filepath=os.path.join(HERE, "preview", "koe_rig_test.blend"))
    print("KLAAR", json.dumps(info))


if __name__ == "__main__":
    main()
