"""Gedeeld mensskelet + animaties voor de bumpkins (Beasts & Bumpkins-remake).

Draaien (headless):
  blender -b -P bumpkin_rig.py            -> bumpkin_test.glb, bumpkin_test.blend, bumpkin_anim.json
Als module (de modeller, bumpkin_man.py):
  import bumpkin_rig
  rig = bumpkin_rig.bouw_rig(maat=None)        # alleen het skelet, geen mesh, geen acties
  bumpkin_rig.bouw_animaties(rig)              # voegt de acties toe, zie ANIMATIES hieronder

RUSTPOSE: A-pose. Armature `bumpkin_rig` in meters, staat op de oorsprong, kijkt naar Blender -Y
(glTF/Godot +Z), voeten op z=0, armen 40 graden uit de verticaal naar buiten, benen recht, handen
open. Links = +X (gezien vanuit het personage). Armatuur-object staat op identiteit.

BONEN (Mixamo-namen, geen prefix): Hips, Spine, Spine1, Spine2, Neck, Head, HeadTop_End,
{Left,Right}Shoulder/Arm/ForeArm/Hand/HandFist (HandFist = hele hand krullen, 1 bot),
{Left,Right}UpLeg/Leg/Foot/ToeBase. Sockets zonder deform: `prop_R` (kind van RightHand) en
`prop_L` (kind van LeftHand).

SOCKET-GRIJPAS (prop_R / prop_L): kop van het bot = midden van de handpalm. Lokale +Y = de greep-as,
van de handpalm naar het werkende eind (hamerkop, zwaardpunt); in rust wijst +Y naar voren (-Y wereld),
dus loodrecht op de hangende onderarm. Lokale +Z = rust omhoog (zwaard: de kant van het vlak/de lange
bladzijde, snede aan -Z; hamer: kop-as, slagvlak aan -Z, klauw aan +Z). Lokale X = Y x Z.
Props zitten als kind (parent_type BONE) onder het bot; hun oorsprong ligt in de palm.

BOTROLLEN: elk bot heeft lokale +Z naar voren (-Y wereld) (voet/teen: omhoog), dus lokale X is
de buig-as en alle animatie is zuivere rotatie. Spiegelregel links/rechts: rx gelijk, ry en rz negatief.
Teken-cheatsheet (lokale Euler, graden): romp/nek/kop: +rx buigt voorover, +ry draait naar links,
+rz kantelt naar rechts. Benen: +rx zwaait naar voren. Armen: +rx zwaait naar voren, -rz (links) /
+rz (rechts) brengt de arm naar het lijf (hangend = ongeveer 40). Onderarm: +rx buigt de elleboog.

ANIMATIES (24 fps, alleen rotaties + Hips-locatie; benen via 2-botten-IK per frame uitgerekend en
dan gewoon gekeyframed): idle, lopen, rennen, bouwen, aanval_zwaard, aanval_steen, zagen (bouwers wisselen
hameren en zagen af, prop_zaag), houweel (prop_houweel, twee handen), dragen (beide handen voor de borst; het spel legt hem als bovenlijf-blend over de
loopclips). Linker- en rechterarm kunnen in richtingsmodus (sleutels LA/RA, arm_ik legt de palm op een punt).
Elke actie heeft custom property `snelheid_mps`; zie ook bumpkin_anim.json.
"""
import json
import math
import os
import sys

import bpy
import bmesh
from mathutils import Euler, Matrix, Quaternion, Vector

HERE = os.path.dirname(os.path.abspath(__file__))
FPS = 24

# --- Maten (meters) -----------------------------------------------------------------
# Uit de sprites van het origineel (zie ref/spec.md): 1,37 m, grote kop, geen buik. De modeller
# mag hieraan draaien; animaties lopen mee via de beenlengte (SL).
MAAT = {
    "hoogte": 1.37,      # totale lengte (m)
    "kop": 0.27,         # kophoogte / lengte
    "schouder": 0.40,    # schouderbreedte tussen de armgewrichten (m)
    "buik": 0.0,         # extra buikstraal (m), alleen voor de placeholder-mesh
    "been": 0.47,        # hoogte heupgewricht / lengte
}
AARM = 40.0              # A-pose: graden van de verticaal
BASIS_H = 1.37           # maten hieronder zijn bij deze hoogte (s = hoogte / 1,37)

LINKS, RECHTS = "Left", "Right"
VOORUIT = Vector((0, -1, 0))
OMHOOG = Vector((0, 0, 1))


def geo(m):
    """Alle skeletmaten uit MAAT (armatuurruimte, meters)."""
    H = m["hoogte"]
    s = H / BASIS_H
    g = {"s": s, "H": H}
    g["zh"] = m["been"] * H                      # heupgewricht
    g["hx"] = 0.09 * s                           # heup x
    g["enkel"] = 0.08 * s                        # enkelhoogte
    g["kop_h"] = m["kop"] * H
    g["kop_basis"] = H - g["kop_h"]
    g["nek"] = 0.035 * s
    g["zn"] = g["kop_basis"] - g["nek"]          # onderkant nek = bovenkant Spine2
    g["hips_kop"] = g["zh"] + 0.03 * s
    g["hips_top"] = g["zh"] + 0.09 * s
    g["arm_z"] = g["zn"] - 0.045 * s
    g["arm_x"] = m["schouder"] / 2
    g["boven"], g["onder"], g["hand"] = 0.21 * s, 0.18 * s, 0.08 * s
    return g


# --- Skelet -----------------------------------------------------------------------------
def bouw_rig(maat=None):
    """Bouwt alleen het armatuur `bumpkin_rig` in de huidige scene en geeft het object terug."""
    m = dict(MAAT)
    m.update(maat or {})
    g = geo(m)
    s = g["s"]
    arm_data = bpy.data.armatures.new("bumpkin_rig")
    rig = bpy.data.objects.new("bumpkin_rig", arm_data)
    bpy.context.scene.collection.objects.link(rig)
    bpy.context.view_layer.objects.active = rig
    rig.select_set(True)
    rig["hoogte"] = g["H"]
    rig["rustpose"] = "A-pose, armen 40 graden, kijkt naar -Y"
    bpy.ops.object.mode_set(mode="EDIT")
    eb = arm_data.edit_bones

    def bot(naam, ouder, kop, staart, roll=VOORUIT, deform=True):
        b = eb.new(naam)
        b.head, b.tail = Vector(kop), Vector(staart)
        b.align_roll(roll)
        if ouder:
            b.parent = eb[ouder]
        b.use_connect = False
        b.use_deform = deform
        return b

    zh, hx = g["zh"], g["hx"]
    bot("Hips", None, (0, 0, g["hips_kop"]), (0, 0, g["hips_top"]))
    zs = [g["hips_top"] + (g["zn"] - g["hips_top"]) * i / 3 for i in range(4)]
    bot("Spine", "Hips", (0, 0, zs[0]), (0, 0, zs[1]))
    bot("Spine1", "Spine", (0, 0, zs[1]), (0, 0, zs[2]))
    bot("Spine2", "Spine1", (0, 0, zs[2]), (0, 0, zs[3]))
    bot("Neck", "Spine2", (0, 0, g["zn"]), (0, 0, g["kop_basis"]))
    bot("Head", "Neck", (0, 0, g["kop_basis"]), (0, 0, g["H"] - 0.05 * s))
    bot("HeadTop_End", "Head", (0, 0, g["H"] - 0.05 * s), (0, 0, g["H"]))

    a = math.radians(AARM)
    for zijde, sg in ((LINKS, 1), (RECHTS, -1)):
        z = lambda n: zijde + n
        u = Vector((sg * math.sin(a), 0, -math.cos(a)))
        kl = Vector((sg * 0.03 * s, 0, g["zn"] - 0.015 * s))
        ar = Vector((sg * g["arm_x"], 0, g["arm_z"]))
        bot(z("Shoulder"), "Spine2", kl, ar)
        el = ar + u * g["boven"]
        pols = el + u * g["onder"]
        bot(z("Arm"), z("Shoulder"), ar, el)
        bot(z("ForeArm"), z("Arm"), el, pols)
        bot(z("Hand"), z("ForeArm"), pols, pols + u * g["hand"])
        bot(z("HandFist"), z("Hand"), pols + u * g["hand"] * 0.55, pols + u * (g["hand"] + 0.05 * s))
        palm = pols + u * g["hand"] * 0.5
        bot("prop_" + zijde[0], z("Hand"), palm, palm + Vector((0, -0.05 * s, 0)), roll=OMHOOG, deform=False)
        # benen
        heup = Vector((sg * hx, 0, zh))
        enkel = Vector((sg * hx, 0, g["enkel"]))
        knie = heup + (enkel - heup) * 0.5
        bot(z("UpLeg"), "Hips", heup, knie)
        bot(z("Leg"), z("UpLeg"), knie, enkel)
        bot(z("Foot"), z("Leg"), enkel, Vector((sg * hx, -0.11 * s, 0.03 * s)), roll=OMHOOG)
        bot(z("ToeBase"), z("Foot"), Vector((sg * hx, -0.11 * s, 0.03 * s)),
            Vector((sg * hx, -0.17 * s, 0.02 * s)), roll=OMHOOG)
    bpy.ops.object.mode_set(mode="OBJECT")
    return rig


# --- Animatie: hulpfuncties ---------------------------------------------------------------
def pchip(pts, x, eind_vlak):
    """Monotone kubische Hermite door (x, y)-punten: geen overshoot, rustpunt op elke piek."""
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


def spiegel_naam(n):
    if n.startswith("Left"):
        return "Right" + n[4:]
    if n.startswith("Right"):
        return "Left" + n[5:]
    return n


def spiegel(pose):
    uit = {}
    for k, v in pose.items():
        if k == "T":
            uit[k] = (-v[0], v[1], v[2])
        elif k in ("LF", "RF"):
            uit["RF" if k == "LF" else "LF"] = (-v[0], v[1], v[2], v[3], -v[4])
        else:
            uit[spiegel_naam(k)] = (v[0], -v[1], -v[2])
    return uit


def smooth(t):
    t = max(0.0, min(1.0, t))
    return t * t * (3 - 2 * t)


class Maten:
    """Alles wat de animatie uit het rig leest (zodat een andere MAAT meeloopt)."""

    def __init__(self, rig):
        bn = rig.data.bones
        self.rig = rig
        self.rr = {b.name: b.matrix_local.to_quaternion() for b in bn}
        self.ouder = {b.name: (b.parent.name if b.parent else None) for b in bn}
        self.ouder = {b.name: (b.parent.name if b.parent else None) for b in bn}
        self.kop = {b.name: b.head_local.copy() for b in bn}
        self.staart = {b.name: b.tail_local.copy() for b in bn}
        self.s = rig["hoogte"] / BASIS_H
        self.L1 = (self.kop["LeftLeg"] - self.kop["LeftUpLeg"]).length
        self.L2 = (self.staart["LeftLeg"] - self.kop["LeftLeg"]).length
        self.enkel = self.kop["LeftFoot"].z
        self.hx = self.kop["LeftUpLeg"].x
        self.sl = (self.L1 + self.L2) / 0.564     # schaal voor passen en hoogtes
        s = self.s
        # zoolpunten (y, z) t.o.v. de enkel: hak, bal, teen
        self.zool = [(0.06 * s, -self.enkel), (-0.11 * s, -self.enkel), (-0.17 * s, -self.enkel)]

    def grond_z(self, pitch):
        p = math.radians(pitch)
        laagste = min(-y * math.sin(p) + z * math.cos(p) for y, z in self.zool)
        return -laagste


def rx(g):
    return Quaternion((1, 0, 0), math.radians(g))


def rz(g):
    return Quaternion((0, 0, 1), math.radians(g))


def eul(v):
    return Euler((math.radians(v[0]), math.radians(v[1]), math.radians(v[2])), "XYZ").to_quaternion()


def been_ik(M, zijde, T, Dh, enkel, pitch, yaw, tenen):
    """Twee-botten-IK in wereldruimte. Geeft lokale quaternions voor UpLeg, Leg, Foot, ToeBase."""
    n = lambda b: zijde + b
    hip_kop = M.kop["Hips"]
    heup = T + hip_kop + Dh @ (M.kop[n("UpLeg")] - hip_kop)
    d = enkel - heup
    afstand = d.length
    ac = min(max(afstand, abs(M.L1 - M.L2) + 1e-3), (M.L1 + M.L2) * 0.9995)
    richt = d.normalized()
    cosa = (M.L1 ** 2 + ac ** 2 - M.L2 ** 2) / (2 * M.L1 * ac)
    alfa = math.acos(max(-1.0, min(1.0, cosa)))
    pool = VOORUIT - richt * VOORUIT.dot(richt)
    pool.normalize()
    knie = heup + richt * (M.L1 * math.cos(alfa)) + pool * (M.L1 * math.sin(alfa))
    enkel_eff = heup + richt * ac
    dij = (knie - heup).normalized()
    scheen = (enkel_eff - knie).normalized()
    rust_dij = (M.staart[n("UpLeg")] - M.kop[n("UpLeg")]).normalized()
    rust_sch = (M.staart[n("Leg")] - M.kop[n("Leg")]).normalized()
    Dw_up = rust_dij.rotation_difference(dij)
    Dw_leg = rust_sch.rotation_difference(scheen)
    Dw_foot = rz(yaw) @ rx(-pitch)
    rr = M.rr
    q_up = rr[n("UpLeg")].inverted() @ Dh.inverted() @ Dw_up @ rr[n("UpLeg")]
    q_leg = rr[n("Leg")].inverted() @ Dw_up.inverted() @ Dw_leg @ rr[n("Leg")]
    q_foot = rr[n("Foot")].inverted() @ Dw_leg.inverted() @ Dw_foot @ rr[n("Foot")]
    q_toe = rr[n("ToeBase")].inverted() @ rx(-tenen) @ rr[n("ToeBase")]
    return {n("UpLeg"): q_up, n("Leg"): q_leg, n("Foot"): q_foot, n("ToeBase"): q_toe}


BOTEN_BOVEN = ["Spine", "Spine1", "Spine2", "Neck", "Head",
               "LeftShoulder", "LeftArm", "LeftForeArm", "LeftHand", "LeftHandFist",
               "RightShoulder", "RightArm", "RightForeArm", "RightHand", "RightHandFist"]
STAND_L = (0.115, 0.0, 0.0, 0.0, 8.0)       # x, y, lift, pitch, yaw (graden)
STAND_R = (-0.115, 0.0, 0.0, 0.0, -8.0)
STAND_T = (0.0, 0.0, -0.025)
RA_HANG = (-0.64, 0, -0.77, -0.64, 0, -0.77, 0, 0, 0, 0, 0, 0)   # richtingsmodus rechterarm: boven, onder, greep, omhoog


def ha(alpha, roll=0.0):
    """Greep-as en 'omhoog'-as van een hamer/zwaard dat in het zijvlak (Y-Z) draait.
    alpha 0 = voor, 90 = recht omhoog, 180 = achter; neerwaartse slag = alpha neemt af, snede/slagvlak leidt."""
    a = math.radians(alpha)
    h = Vector((0, -math.cos(a), math.sin(a)))
    up = Vector((0, math.sin(a), math.cos(a)))
    if roll:
        up = Quaternion(h, math.radians(roll)) @ up
    return (*h, *up)


def RA(u, f, alpha=None, roll=0.0):
    """Sleutel voor de rechterarm in richtingsmodus (wereldrichtingen). alpha None = hand volgt de onderarm."""
    g = ha(alpha, roll) if alpha is not None else (0,) * 6
    return tuple(u) + tuple(f) + tuple(g)
RA_HANG = (-0.64, 0, -0.77, -0.64, 0, -0.77, 0, 0, 0, 0, 0, 0)   # richtingsmodus rechterarm: boven, onder, greep, 'omhoog' van de prop
LA_HANG = (0.64, 0, -0.77, 0.64, 0, -0.77, 0, 0, 0, 0, 0, 0)     # idem linkerarm (sleutel "LA")


def ha(alpha, roll=0.0):
    """Greep-as en 'omhoog'-as van een hamer/zwaard dat in het zijvlak (Y-Z) draait.
    alpha 0 = voor, 90 = recht omhoog, 180 = achter; neerwaartse slag = alpha neemt af, snede/slagvlak leidt."""
    a = math.radians(alpha)
    h = Vector((0, -math.cos(a), math.sin(a)))
    up = Vector((0, math.sin(a), math.cos(a)))
    if roll:
        q = Quaternion(h, math.radians(roll))
        up = q @ up
    return (*h, *up)


def RA(u, f, alpha=None, roll=0.0):
    """Sleutel voor de rechterarm in richtingsmodus (wereldrichtingen). alpha None = hand volgt de onderarm."""
    g = ha(alpha, roll) if alpha is not None else (0,) * 6
    return tuple(u) + tuple(f) + tuple(g)


def sleutels_naar_reeksen(keys, N, lus, M):
    """keys: {frame: pose}. Geeft {kanaal: [waarde per frame]} voor alle kanalen."""
    frames = sorted(keys)
    out = {}

    def kan(naam, idx, default):
        pts = []
        for f in frames:
            v = keys[f].get(naam, default)
            pts.append((f, v[idx]))
        return reeks(pts, N, lus)

    for b in ["Hips"] + BOTEN_BOVEN:
        for i, ax in enumerate("xyz"):
            out[(b, ax)] = kan(b, i, (0, 0, 0))
    for i, ax in enumerate("xyz"):
        out[("T", ax)] = kan("T", i, STAND_T)
    if any("RA" in keys[f] for f in frames):
        for i in range(12):
            out[("RA", i)] = kan("RA", i, RA_HANG)
        out["dir"] = True
    if any("LA" in keys[f] for f in frames):
        for i in range(12):
            out[("LA", i)] = kan("LA", i, LA_HANG)
        out["dirL"] = True
    sl = M.sl
    for nm, st in (("LF", STAND_L), ("RF", STAND_R)):
        for i in range(5):
            default = (st[0] * sl, st[1], st[2], st[3], st[4])
            out[(nm, i)] = kan(nm, i, default)
    return out


def zet_pose_frame(rig, M, k, f):
    """Een frame uit de kanalen -> lokale quaternions + Hips-locatie."""
    q_hips = eul([k[("Hips", a)][f] for a in "xyz"])
    rr = M.rr
    Dh = rr["Hips"] @ q_hips @ rr["Hips"].inverted()
    T = Vector([k[("T", a)][f] for a in "xyz"])
    qs = {"Hips": q_hips}
    Dw = {"Hips": Dh}
    for b in BOTEN_BOVEN:
        q = eul([k[(b, a)][f] for a in "xyz"])
        qs[b] = q
        Dw[b] = Dw[M.ouder[b]] @ (rr[b] @ q @ rr[b].inverted())
    for zijde, kan_, vlag in ((RECHTS, "RA", "dir"), (LINKS, "LA", "dirL")):
        if not k.get(vlag):
            continue
        A, F, H, S = zijde + "Arm", zijde + "ForeArm", zijde + "Hand", zijde + "Shoulder"
        v = [k[(kan_, i)][f] for i in range(12)]
        u, fo = Vector(v[0:3]).normalized(), Vector(v[3:6]).normalized()
        d_arm = (M.staart[A] - M.kop[A]).normalized().rotation_difference(u)
        d_fore = (M.staart[F] - M.kop[F]).normalized().rotation_difference(fo)
        qs[A] = rr[A].inverted() @ Dw[S].inverted() @ d_arm @ rr[A]
        qs[F] = rr[F].inverted() @ d_arm.inverted() @ d_fore @ rr[F]
        h = Vector(v[6:9])
        if h.length > 1e-6:
            h.normalize()
            z = Vector(v[9:12])
            z = (z - h * z.dot(h)).normalized()
            x = h.cross(z)
            # prop: lokale Y = greep, Z = omhoog (rust: Y = -Y wereld, Z = +Z wereld)
            Rt = Matrix(((x.x, h.x, z.x), (x.y, h.y, z.y), (x.z, h.z, z.z))).to_quaternion()
            d_hand = Rt @ rr["prop_" + zijde[0]].inverted()
        else:
            d_hand = d_fore
        qs[H] = rr[H].inverted() @ d_fore.inverted() @ d_hand @ rr[H]
    for zijde, nm in ((LINKS, "LF"), (RECHTS, "RF")):
        x, y, lift, pitch, yaw = [k[(nm, i)][f] for i in range(5)]
        z = M.grond_z(pitch) + lift
        tenen = max(0.0, -pitch)
        qs.update(been_ik(M, zijde, T, Dh, Vector((x, y, z)), pitch, yaw, tenen))
    return qs, rr["Hips"].inverted() @ T


def schrijf_actie(rig, M, naam, N, lus, k, extra):
    act = bpy.data.actions.new(naam)
    act.use_fake_user = True
    if not rig.animation_data:
        rig.animation_data_create()
    rig.animation_data.action = act
    pb = rig.pose.bones
    for b in pb:
        b.rotation_mode = "QUATERNION"
    vorige = {}
    for f in range(N + 1):
        qs, loc = zet_pose_frame(rig, M, k, f)
        for naam_b, q in qs.items():
            v = vorige.get(naam_b)
            if v is not None and v.dot(q) < 0:
                q = -q
            vorige[naam_b] = q.copy()
            pb[naam_b].rotation_quaternion = q
            pb[naam_b].keyframe_insert("rotation_quaternion", frame=f)
        pb["Hips"].location = loc
        pb["Hips"].keyframe_insert("location", frame=f)
    for kk, vv in extra.items():
        act[kk] = vv
    act.use_frame_range = True
    act.frame_start, act.frame_end = 0, N
    if lus:
        act.use_cyclic = True
    return act


# --- Clips -------------------------------------------------------------------------------
def hips_z(sl, dz):
    return dz * sl


def clip_idle(M):
    N = 72
    sl = M.sl
    keys = {}
    keys[0] = {"T": (0, 0, -0.022 * sl), "Hips": (0, 0, 0),
               "LeftArm": (0, 0, -22), "RightArm": (0, 0, 22),
               "LeftForeArm": (10, 0, 0), "RightForeArm": (10, 0, 0),
               "LeftHandFist": (20, 0, 0), "RightHandFist": (20, 0, 0),
               "Head": (2, 0, 0), "Spine2": (0, 0, 0)}
    keys[18] = {"T": (0.012 * sl, 0, -0.013 * sl), "Hips": (0, 1.5, -2),
                "Spine": (0, 0, 1), "Spine2": (-1.5, 0, 1),
                "LeftShoulder": (0, -1.5, 0), "RightShoulder": (0, 1.5, 0),
                "LeftArm": (3, 0, -22), "RightArm": (-2, 0, 22),
                "LeftForeArm": (12, 0, 0), "RightForeArm": (9, 0, 0),
                "LeftHandFist": (22, 0, 0), "RightHandFist": (20, 0, 0), "Head": (0, 0, 1)}
    keys[30] = {"T": (0.01 * sl, 0, -0.017 * sl), "Hips": (0, 0.5, -1),
                "Spine2": (-3, 0, 0.5), "LeftShoulder": (0, -3, 0), "RightShoulder": (0, 3, 0),
                "LeftArm": (1, 0, -23), "RightArm": (0, 0, 23),
                "LeftForeArm": (11, 0, 0), "RightForeArm": (10, 0, 0),
                "LeftHandFist": (21, 0, 0), "RightHandFist": (20, 0, 0), "Head": (2, 0, 0)}
    keys[40] = {"T": (0, 0, -0.022 * sl), "Hips": (0, 0, 0),
                "Spine2": (-1, 0, 0), "LeftShoulder": (0, -1, 0), "RightShoulder": (0, 1, 0),
                "Head": (0, 22, 0), "Neck": (0, 6, 0), "LeftArm": (0, 0, -22), "RightArm": (0, 0, 22),
                "LeftForeArm": (10, 0, 0), "RightForeArm": (10, 0, 0),
                "LeftHandFist": (20, 0, 0), "RightHandFist": (20, 0, 0)}
    keys[50] = {"T": (-0.004 * sl, 0, -0.024 * sl), "Hips": (0, -0.5, 1),
                "Head": (-1, 22, 0), "Neck": (0, 6, 0), "Spine2": (0, 0, 0),
                "LeftArm": (0, 0, -22), "RightArm": (0, 0, 22),
                "LeftForeArm": (10, 0, 0), "RightForeArm": (10, 0, 0),
                "LeftHandFist": (20, 0, 0), "RightHandFist": (20, 0, 0)}
    keys[56] = {"T": (-0.01 * sl, 0, -0.025 * sl), "Hips": (0, -1.5, 2),
                "Spine": (0, 0, -1), "Head": (1, -6, 0), "Neck": (0, -2, 0),
                "LeftArm": (-2, 0, -22), "RightArm": (3, 0, 22),
                "LeftForeArm": (9, 0, 0), "RightForeArm": (12, 0, 0),
                "LeftHandFist": (20, 0, 0), "RightHandFist": (22, 0, 0)}
    keys[64] = {"T": (-0.006 * sl, 0, -0.024 * sl), "Hips": (0, -0.7, 1), "Head": (2, 0, 0),
                "Spine2": (-0.5, 0, 0), "LeftArm": (-1, 0, -22), "RightArm": (1, 0, 22),
                "LeftHandFist": (20, 0, 0), "RightHandFist": (20, 0, 0),
                "LeftForeArm": (10, 0, 0), "RightForeArm": (10, 0, 0)}
    k = sleutels_naar_reeksen(keys, N, True, M)
    return N, True, k, {"snelheid_mps": 0.0}, None


def loop_hips(M, N, S, contact_r, sl, hz_min, hz_max, tmin_frame, sway, roll, yaw, lean, perioden=2):
    """Hips-kanalen (T, rotatie) voor looppatronen."""
    out = {}
    for ax in "xyz":
        out[("T", ax)] = [0.0] * (N + 1)
        out[("Hips", ax)] = [0.0] * (N + 1)
    stap = N / 2.0
    for f in range(N + 1):
        bump = 0.5 - 0.5 * math.cos(2 * math.pi * (f - tmin_frame) / stap)
        out[("T", "z")][f] = (hz_min + (hz_max - hz_min) * bump) * sl
        mid_l = S / 2.0
        out[("T", "x")][f] = sway * sl * math.cos(2 * math.pi * (f - mid_l) / N)
        out[("Hips", "z")][f] = roll * math.cos(2 * math.pi * (f - mid_l) / N)
        out[("Hips", "y")][f] = -yaw * math.cos(2 * math.pi * f / N)
        out[("Hips", "x")][f] = lean
    return out


def voet_pad(M, f, contact, N, S, A, B, lift, k_swing, x_stand, yaw_stand, pitchprof):
    """Enkelpositie van een voet. Voorwaarts = -Y; stand beweegt naar achter (+Y) met grondsnelheid v."""
    sl = M.sl
    u = (f - contact) % N
    D = A + B
    v = D * FPS / S
    if u < S:
        s = u / S
        y = -A + D * s
        pitch = pitchprof(s, True)
        lf = 0.0
        x = x_stand
    else:
        w = (u - S) / (N - S)
        Tsw = (N - S) / FPS
        m = k_swing * v * Tsw
        p0, p1 = B, -A
        h00 = 2 * w ** 3 - 3 * w ** 2 + 1
        h10 = w ** 3 - 2 * w ** 2 + w
        h01 = -2 * w ** 3 + 3 * w ** 2
        h11 = w ** 3 - w ** 2
        y = h00 * p0 + h10 * m + h01 * p1 + h11 * m
        pitch = pitchprof(w, False)
        lf = lift * math.sin(math.pi * w ** 0.9)
        x = x_stand + math.copysign(0.02 * sl, x_stand) * math.sin(math.pi * w)
    return (x, y, lf, pitch, yaw_stand)


def pitch_lopen(t, stand):
    if stand:
        if t < 0.2:
            return 16 * (1 - smooth(t / 0.2))
        if t < 0.55:
            return 0.0
        return -28 * smooth((t - 0.55) / 0.45)
    return -28 + 44 * smooth(t * 1.15)


def pitch_rennen(t, stand):
    if stand:
        if t < 0.25:
            return 20 * (1 - smooth(t / 0.25))
        if t < 0.5:
            return 0.0
        return -30 * smooth((t - 0.5) / 0.5)
    return -30 + 50 * smooth(t * 1.1)


def clip_lopen(M):
    N, S = 24, 13
    sl = M.sl
    A = B = 0.23 * sl
    v = (A + B) * FPS / S
    k = {}
    half = {
        0: {"Spine": (3, 2, 0), "Spine1": (3, 3, 0), "Spine2": (3, 3, 0),
            "Head": (-8, -4, 0), "LeftShoulder": (0, 0, 0),
            "LeftArm": (-28, 0, -17), "LeftForeArm": (14, 0, 0), "LeftHandFist": (25, 0, 0),
            "RightArm": (28, 0, 17), "RightForeArm": (38, 0, 0), "RightHandFist": (25, 0, 0)},
        3: {"Spine": (4, 1, -1), "Spine1": (4, 1, -1), "Spine2": (4, 1, -1),
            "Head": (-9, -1, 0),
            "LeftArm": (-16, 0, -17), "LeftForeArm": (12, 0, 0), "LeftHandFist": (25, 0, 0),
            "RightArm": (16, 0, 17), "RightForeArm": (34, 0, 0), "RightHandFist": (25, 0, 0)},
        6: {"Spine": (3, 0, -1.5), "Spine1": (3, 0, -1.5), "Spine2": (3, 0, -1.5),
            "Head": (-8, 0, 0),
            "LeftArm": (-2, 0, -17), "LeftForeArm": (14, 0, 0), "LeftHandFist": (25, 0, 0),
            "RightArm": (2, 0, 17), "RightForeArm": (22, 0, 0), "RightHandFist": (25, 0, 0)},
        9: {"Spine": (2, -1, 0), "Spine1": (2, -2, 0), "Spine2": (2, -2, 0),
            "Head": (-7, 2, 0),
            "LeftArm": (15, 0, -17), "LeftForeArm": (30, 0, 0), "LeftHandFist": (25, 0, 0),
            "RightArm": (-16, 0, 17), "RightForeArm": (16, 0, 0), "RightHandFist": (25, 0, 0)},
    }
    keys = dict(half)
    for f, p in half.items():
        keys[f + 12] = spiegel(p)
    base = sleutels_naar_reeksen(keys, N, True, M)
    hp = loop_hips(M, N, S, 12, sl, -0.055, -0.012, 1.5, 0.04, 4.0, 5.0, 0.0)
    base.update(hp)
    # Hips lichte voorover helling, wordt in x van de rotatie gezet
    base[("Hips", "x")] = [4.0] * (N + 1)
    for nm, contact, xs, ys in (("LF", 0, M.hx + 0.025 * sl, 8.0), ("RF", 12, -(M.hx + 0.025 * sl), -8.0)):
        pad = [voet_pad(M, f, contact, N, S, A, B, 0.17 * sl, 0.7, xs, ys, pitch_lopen) for f in range(N + 1)]
        for i in range(5):
            base[(nm, i)] = [p[i] for p in pad]
    return N, True, base, {"snelheid_mps": v}, None


def clip_rennen(M):
    N, S = 16, 6
    sl = M.sl
    A = B = 0.30 * sl
    v = (A + B) * FPS / S
    half = {
        0: {"Spine": (5, 3, 0), "Spine1": (5, 4, 0), "Spine2": (5, 4, 0), "Head": (-12, -6, 0),
            "LeftShoulder": (0, 0, 0),
            "LeftArm": (-48, 0, -28), "LeftForeArm": (85, 0, 0), "LeftHandFist": (50, 0, 0),
            "RightArm": (52, 0, 28), "RightForeArm": (95, 0, 0), "RightHandFist": (50, 0, 0)},
        2: {"Spine": (7, 2, 0), "Spine1": (7, 2, -1), "Spine2": (7, 2, -1), "Head": (-14, -3, 0),
            "LeftArm": (-26, 0, -28), "LeftForeArm": (88, 0, 0), "LeftHandFist": (50, 0, 0),
            "RightArm": (30, 0, 28), "RightForeArm": (92, 0, 0), "RightHandFist": (50, 0, 0)},
        4: {"Spine": (5, 0, -1), "Spine1": (5, 0, -2), "Spine2": (5, 0, -2), "Head": (-12, 0, 0),
            "LeftArm": (4, 0, -28), "LeftForeArm": (78, 0, 0), "LeftHandFist": (50, 0, 0),
            "RightArm": (-4, 0, 28), "RightForeArm": (88, 0, 0), "RightHandFist": (50, 0, 0)},
        6: {"Spine": (5, -2, 0), "Spine1": (5, -3, 0), "Spine2": (5, -3, 0), "Head": (-12, 3, 0),
            "LeftArm": (32, 0, -28), "LeftForeArm": (95, 0, 0), "LeftHandFist": (50, 0, 0),
            "RightArm": (-30, 0, 28), "RightForeArm": (82, 0, 0), "RightHandFist": (50, 0, 0)},
    }
    keys = dict(half)
    for f, p in half.items():
        keys[f + 8] = spiegel(p)
    base = sleutels_naar_reeksen(keys, N, True, M)
    # hips: laagst midden stand (f3, f11), hoogst midden vlucht (f7, f15)
    hp = {}
    for ax in "xyz":
        hp[("T", ax)] = [0.0] * (N + 1)
        hp[("Hips", ax)] = [0.0] * (N + 1)
    for f in range(N + 1):
        bump = 0.5 - 0.5 * math.cos(2 * math.pi * (f - 3) / 8.0)
        hp[("T", "z")][f] = (-0.125 + 0.07 * bump) * sl
        hp[("T", "x")][f] = 0.03 * sl * math.cos(2 * math.pi * (f - 3) / N)
        hp[("Hips", "z")][f] = 3.0 * math.cos(2 * math.pi * (f - 3) / N)
        hp[("Hips", "y")][f] = -8.0 * math.cos(2 * math.pi * f / N)
        hp[("Hips", "x")][f] = 8.0
    base.update(hp)
    for nm, contact, xs, ys in (("LF", 0, M.hx + 0.02 * sl, 6.0), ("RF", 8, -(M.hx + 0.02 * sl), -6.0)):
        pad = [voet_pad(M, f, contact, N, S, A, B, 0.26 * sl, 0.55, xs, ys, pitch_rennen) for f in range(N + 1)]
        for i in range(5):
            base[(nm, i)] = [p[i] for p in pad]
    return N, True, base, {"snelheid_mps": v}, None


def clip_bouwen(M):
    """Hamer slaan. Frame 0 = hamer boven, frame 11 = klap, lus 30 frames (1,25 s)."""
    N, IMP = 30, 11
    sl = M.sl
    vo = {"LF": (0.135 * sl, -0.04 * sl, 0, 0, 6), "RF": (-0.135 * sl, 0.05 * sl, 0, 0, -6)}
    links = {"LeftArm": (45, 0, -14), "LeftForeArm": (62, 0, 0), "LeftHandFist": (20, 0, 0)}
    P = {
        0: dict(T=(0, 0.02 * sl, -0.03 * sl), Hips=(-3, 2, 0), Spine=(-2, 3, 0), Spine1=(-2, 3, 0), Spine2=(-3, 3, 0),
                Head=(5, 0, 0), Neck=(2, 0, 0), RightHandFist=(65, 0, 0),
                RA=RA((-0.8, -0.2, 0.55), (0.15, 0.7, 0.55), 140)),
        4: dict(T=(0, 0.03 * sl, -0.025 * sl), Hips=(-4, 2, 0), Spine=(-4, 3, 0), Spine1=(-3, 3, 0), Spine2=(-4, 3, 0),
                Head=(4, 0, 0), Neck=(2, 0, 0), RightHandFist=(65, 0, 0),
                RA=RA((-0.8, -0.1, 0.6), (0.2, 0.8, 0.45), 165)),
        8: dict(T=(0, 0.0, -0.06 * sl), Hips=(3, 0, 0), Spine=(6, 0, 0), Spine1=(6, 0, 0), Spine2=(6, 0, 0),
                Head=(8, 0, 0), Neck=(3, 0, 0), RightHandFist=(65, 0, 0),
                RA=RA((-0.6, -0.5, 0.35), (-0.1, -0.4, 0.9), 70)),
        IMP: dict(T=(0, -0.03 * sl, -0.105 * sl), Hips=(8, 0, 0), Spine=(11, 0, 0), Spine1=(11, 0, 0), Spine2=(10, 0, 0),
                  Head=(6, 0, 0), Neck=(4, 0, 0), RightHandFist=(70, 0, 0),
                  RA=RA((-0.3, -0.4, -0.85), (-0.2, -0.85, -0.5), -10)),
        14: dict(T=(0, -0.02 * sl, -0.09 * sl), Hips=(6, 0, 0), Spine=(9, 0, 0), Spine1=(9, 0, 0), Spine2=(8, 0, 0),
                 Head=(7, 0, 0), Neck=(3, 0, 0), RightHandFist=(65, 0, 0),
                 RA=RA((-0.35, -0.5, -0.55), (-0.2, -0.9, -0.1), 15)),
        20: dict(T=(0, 0.0, -0.06 * sl), Hips=(0, 1, 0), Spine=(3, 1, 0), Spine1=(3, 1, 0), Spine2=(2, 1, 0),
                 Head=(6, 0, 0), Neck=(3, 0, 0), RightHandFist=(65, 0, 0),
                 RA=RA((-0.4, -0.45, 0.1), (-0.1, -0.5, 0.85), 80)),
        26: dict(T=(0, 0.02 * sl, -0.04 * sl), Hips=(-2, 2, 0), Spine=(-1, 3, 0), Spine1=(-1, 3, 0), Spine2=(-2, 3, 0),
                 Head=(5, 0, 0), Neck=(2, 0, 0), RightHandFist=(65, 0, 0),
                 RA=RA((-0.8, -0.2, 0.55), (0.1, 0.65, 0.6), 130)),
    }
    for p in P.values():
        p.update(links)
        p.update(vo)
    k = sleutels_naar_reeksen(P, N, True, M)
    return N, True, k, {"snelheid_mps": 0.0}, {"impact_s": IMP / FPS}


def clip_zwaard(M):
    """Voetsoldaat: uithalen, slag, herstel. 24 frames (1,0 s), klap op frame 10."""
    N, IMP = 24, 10
    sl = M.sl
    LF, RF = (0.115 * sl, 0.0, 0, 0, 8), (-0.125 * sl, 0.0, 0, 0, -10)
    fist = {"RightHandFist": (75, 0, 0), "LeftHandFist": (35, 0, 0)}
    G = dict(T=(0, 0, -0.045 * sl), Hips=(0, 0, 0), Spine=(2, -4, 0), Spine1=(2, -4, 0), Spine2=(2, -4, 0),
             Head=(0, 4, 0), LeftArm=(8, 0, -40), LeftForeArm=(30, 0, 0), LF=LF, RF=RF,
             RA=RA((-0.3, -0.25, -0.85), (-0.1, -0.9, 0.25), 70), **fist)
    P = {0: G}
    P[3] = {**G, "T": (0, 0.02 * sl, -0.065 * sl), "Spine": (0, -8, 0), "Spine1": (0, -10, 0), "Spine2": (-2, -10, 0),
            "LeftArm": (14, 0, -50), "RA": RA((-0.5, -0.2, -0.2), (-0.1, -0.6, 0.8), 95)}
    P[6] = dict(T=(0, 0.06 * sl, -0.07 * sl), Hips=(-2, -8, 3), Spine=(-3, -10, 0), Spine1=(-4, -12, 0),
                Spine2=(-5, -12, 0), Head=(0, 14, 0), LeftArm=(10, 0, -55), LeftForeArm=(35, 0, 0),
                LF=(0.115 * sl, 0.02 * sl, 0, 0, 8), RF=RF, RA=RA((-0.6, 0.0, 0.75), (0.1, 0.65, 0.75), 160), **fist)
    P[8] = dict(T=(0, -0.03 * sl, -0.09 * sl), Hips=(3, 4, 0), Spine=(3, 6, 0), Spine1=(4, 8, 0), Spine2=(4, 8, 0),
                Head=(2, 4, 0), LeftArm=(14, 0, -50), LeftForeArm=(38, 0, 0),
                LF=(0.115 * sl, -0.14 * sl, 0.07 * sl, -10, 8), RF=RF, RA=RA((-0.45, -0.55, 0.55), (-0.15, -0.4, 0.9), 85), **fist)
    P[IMP] = dict(T=(0, -0.1 * sl, -0.12 * sl), Hips=(6, 14, -2), Spine=(8, 12, 0), Spine1=(8, 14, 0), Spine2=(6, 12, 0),
                  Head=(4, -6, 0), LeftArm=(-20, 0, -62), LeftForeArm=(25, 0, 0),
                  LF=(0.12 * sl, -0.25 * sl, 0, 0, 8), RF=RF, RA=RA((-0.25, -0.5, -0.8), (-0.2, -0.95, -0.2), -15), **fist)
    P[13] = {**P[IMP], "T": (0, -0.11 * sl, -0.125 * sl), "Hips": (7, 16, -2), "Spine": (9, 14, 0), "Spine1": (9, 16, 0),
             "LeftArm": (-30, 0, -66), "RA": RA((-0.2, -0.4, -0.9), (0.0, -0.8, -0.55), -45)}
    P[18] = {**G, "T": (0, -0.05 * sl, -0.08 * sl), "Hips": (3, 6, 0), "Spine": (4, 5, 0), "Spine1": (4, 5, 0),
             "Spine2": (3, 4, 0), "LF": (0.12 * sl, -0.12 * sl, 0.02 * sl, 0, 8),
             "RA": RA((-0.3, -0.3, -0.85), (-0.1, -0.9, 0.0), 40)}
    P[24] = G
    k = sleutels_naar_reeksen(P, N, False, M)
    return N, False, k, {"snelheid_mps": 0.0}, {"impact_s": IMP / FPS}


def clip_steen(M):
    """Steen oppakken en gooien (iedere bumpkin zonder gilde). 27 frames (1,125 s), loslaten op frame 16."""
    N, REL, PAK = 27, 16, 6
    sl = M.sl
    LF, RF = (0.115 * sl, 0.0, 0, 0, 8), (-0.115 * sl, 0.0, 0, 0, -8)
    S0 = dict(T=(0, 0, -0.025 * sl), Head=(2, 0, 0), LeftArm=(0, 0, -22), LeftForeArm=(10, 0, 0),
              RightHandFist=(20, 0, 0), LeftHandFist=(20, 0, 0), LF=LF, RF=RF,
              RA=RA((-0.38, 0.0, -0.92), (-0.34, -0.1, -0.93)))
    P = {0: S0}
    P[3] = dict(T=(0, -0.06 * sl, -0.14 * sl), Hips=(18, 0, 0), Spine=(8, 0, 0), Spine1=(10, 0, 0), Spine2=(10, 0, 0),
                Head=(-4, 0, 0), LeftArm=(30, 0, -30), LeftForeArm=(30, 0, 0), RightHandFist=(25, 0, 0), LF=LF, RF=RF,
                RA=RA((-0.3, -0.45, -0.85), (-0.2, -0.5, -0.85)))
    P[PAK] = dict(T=(0, -0.1 * sl, -0.235 * sl), Hips=(36, 0, 0), Spine=(18, 0, 0), Spine1=(16, 0, 0), Spine2=(14, 0, 0),
                  Head=(-12, 0, 0), LeftArm=(30, 0, -34), LeftForeArm=(30, 0, 0), LeftHandFist=(25, 0, 0),
                  RightHandFist=(25, 0, 0), LF=LF, RF=RF,
                  RA=RA((-0.2, -0.75, -0.65), (-0.1, -0.45, -0.9)))
    P[8] = {**P[PAK], "RightHandFist": (70, 0, 0)}
    P[12] = dict(T=(0, 0.03 * sl, -0.07 * sl), Hips=(-4, -6, 2), Spine=(-4, -8, 0), Spine1=(-4, -10, 0),
                 Spine2=(-5, -12, 0), Head=(0, 10, 0), RightShoulder=(0, 0, -4), RightHandFist=(70, 0, 0),
                 LeftArm=(30, 0, -50), LeftForeArm=(20, 0, 0), LeftHandFist=(30, 0, 0),
                 LF=(0.115 * sl, 0.04 * sl, 0, 0, 8), RF=RF,
                 RA=RA((-0.95, 0.1, 0.1), (-0.25, 0.2, 0.95)))
    P[14] = {**P[12], "T": (0, 0.05 * sl, -0.075 * sl), "Spine2": (-6, -14, 0),
             "RA": RA((-0.85, 0.4, 0.15), (-0.15, 0.4, 0.9))}
    P[REL] = dict(T=(0, -0.06 * sl, -0.08 * sl), Hips=(4, 10, -2), Spine=(4, 10, 0), Spine1=(6, 12, 0),
                  Spine2=(6, 10, 0), Head=(2, -4, 0), RightShoulder=(0, 0, -4), RightHandFist=(10, 0, 0),
                  LeftArm=(50, 0, -20), LeftForeArm=(30, 0, 0), LeftHandFist=(20, 0, 0),
                  LF=(0.115 * sl, -0.12 * sl, 0.0, 0, 8), RF=RF,
                  RA=RA((-0.4, -0.9, 0.3), (-0.35, -0.9, 0.3)))
    P[19] = dict(T=(0, -0.09 * sl, -0.1 * sl), Hips=(8, 16, -3), Spine=(8, 14, 0), Spine1=(9, 16, 0),
                 Spine2=(8, 14, 0), Head=(6, -8, 0), RightHandFist=(15, 0, 0),
                 LeftArm=(-10, 0, -50), LeftForeArm=(25, 0, 0), LeftHandFist=(25, 0, 0),
                 LF=(0.12 * sl, -0.18 * sl, 0.0, 0, 8), RF=RF,
                 RA=RA((0.1, -0.6, -0.8), (0.2, -0.5, -0.85)))
    P[22] = {**S0, "T": (0, -0.04 * sl, -0.06 * sl), "Hips": (3, 6, 0), "Spine": (3, 4, 0), "Spine1": (3, 4, 0),
             "Spine2": (2, 3, 0), "LF": (0.12 * sl, -0.08 * sl, 0.03 * sl, 0, 8),
             "RA": RA((-0.3, -0.25, -0.9), (-0.25, -0.5, -0.8))}
    P[27] = S0
    k = sleutels_naar_reeksen(P, N, False, M)
    return N, False, k, {"snelheid_mps": 0.0}, {"impact_s": REL / FPS, "release_s": REL / FPS, "pak_s": PAK / FPS}


def schouder_pos(M, pose, zijde):
    """Wereldpositie van het armgewricht (kop van <zijde>Arm) in een sleutelpose (FK over Hips..Shoulder)."""
    T = Vector(pose.get("T", STAND_T))
    pos, Dw = {}, {}
    vorige = None
    for b in ("Hips", "Spine", "Spine1", "Spine2", zijde + "Shoulder", zijde + "Arm"):
        q = eul(pose.get(b, (0, 0, 0)))
        if vorige is None:
            pos[b] = M.kop[b] + T
            Dw[b] = M.rr[b] @ q @ M.rr[b].inverted()
        else:
            pos[b] = pos[vorige] + Dw[vorige] @ (M.kop[b] - M.kop[vorige])
            Dw[b] = Dw[vorige] @ (M.rr[b] @ q @ M.rr[b].inverted())
        vorige = b
    return pos[zijde + "Arm"]


def arm_ik(M, pose, zijde, doel, pool, alpha=None, roll=0.0):
    """Richtingssleutel (RA/LA) die de handpalm op `doel` (wereld, m) legt; `pool` = waar de elleboog heen wijst.
    alpha/roll als bij RA (greep-as van de prop); None = hand volgt de onderarm."""
    S = schouder_pos(M, pose, zijde)
    L1 = (M.staart[zijde + "Arm"] - M.kop[zijde + "Arm"]).length
    L2 = (M.staart[zijde + "ForeArm"] - M.kop[zijde + "ForeArm"]).length +         0.5 * (M.staart[zijde + "Hand"] - M.kop[zijde + "Hand"]).length
    d = Vector(doel) - S
    ac = min(max(d.length, abs(L1 - L2) + 1e-3), (L1 + L2) * 0.999)
    r = d.normalized()
    cosa = (L1 ** 2 + ac ** 2 - L2 ** 2) / (2 * L1 * ac)
    a = math.acos(max(-1.0, min(1.0, cosa)))
    pl = Vector(pool) - r * Vector(pool).dot(r)
    pl.normalize()
    el = S + r * (L1 * math.cos(a)) + pl * (L1 * math.sin(a))
    u = (el - S).normalized()
    f = (S + r * ac - el).normalized()
    return RA(u, f, alpha, roll)


def clip_zagen(M):
    """Zagen (origineel `saw`/`vsaw`): voorovergebogen over de zaagbok, rechterhand duwt de zaag vlak heen en weer,
    linkerhand op het hout. 20 frames (0,83 s), lus; impact = einde van de duwslag (frame 10)."""
    N, IMP = 20, 10
    s, sl = M.s, M.sl
    vo = {"LF": (0.13 * sl, -0.07 * sl, 0, 0, 10), "RF": (-0.13 * sl, 0.06 * sl, 0, 0, -12)}
    terug, voor = Vector((-0.12, -0.13, 0.6)) * s, Vector((-0.10, -0.39, 0.57)) * s
    links = Vector((0.11, -0.33, 0.53)) * s
    P = {}
    for f in (0, 5, 10, 15, 20):
        t = 0.5 - 0.5 * math.cos(math.pi * f / IMP)              # 0 terug, 1 voor (frame 10), 0 terug (frame 20)
        p = dict(T=(0, -0.01 * sl * t, -0.055 * sl - 0.008 * sl * t), Hips=(6 + 1.5 * t, -3, 0),
                 Spine=(6 + 1.5 * t, -4 + 2 * t, 0), Spine1=(7 + 1.5 * t, -4 + 2 * t, 0), Spine2=(5 + t, -5 + 3 * t, 0),
                 Neck=(3, 2, 0), Head=(10, 4 - 2 * t, 0), RightShoulder=(0, 2 - 4 * t, 0),
                 RightHandFist=(65, 0, 0), LeftHandFist=(15, 0, 0), **vo)
        p["RA"] = arm_ik(M, p, RECHTS, terug.lerp(voor, t), (-0.5, 1.0, -0.4), alpha=-20)
        p["LA"] = arm_ik(M, p, LINKS, links + Vector((0, -0.01 * t, 0)) * s, (0.8, 0.3, -0.5))
        P[f] = p
    k = sleutels_naar_reeksen(P, N, True, M)
    return N, True, k, {"snelheid_mps": 0.0}, {"impact_s": IMP / FPS}


def clip_houweel(M):
    """Houweel (origineel `pick`/`vpick`): met twee handen boven de rechterschouder uithalen en de punt in de
    steenhoop/grond slaan. Rechterhand hoog op de steel (prop_R), linkerhand lager naar het eind. 24 frames (1,0 s),
    lus; impact = punt in de grond (frame 11)."""
    N, IMP = 24, 11
    s, sl = M.s, M.sl
    vo = {"LF": (0.135 * sl, -0.07 * sl, 0, 0, 8), "RF": (-0.135 * sl, 0.07 * sl, 0, 0, -8)}
    # f: (rechterpalm (x, y, z) * s, alpha greep-as, romp-pitch, T.z, T.y)
    S = {0: ((-0.10, 0.02, 1.22), 135, -7, -0.03, 0.03),
         4: ((-0.10, 0.04, 1.26), 150, -9, -0.025, 0.04),
         8: ((-0.08, -0.22, 1.02), 75, 4, -0.06, 0.0),
         IMP: ((-0.05, -0.36, 0.52), -38, 14, -0.12, -0.04),
         14: ((-0.05, -0.34, 0.56), -30, 13, -0.115, -0.035),
         18: ((-0.08, -0.22, 0.85), 50, 4, -0.07, 0.0),
         N: ((-0.10, 0.02, 1.22), 135, -7, -0.03, 0.03)}
    P = {}
    for f, (r, alpha, rp, tz, ty) in S.items():
        p = dict(T=(0, ty * sl, tz * sl), Hips=(rp * 0.5, 2, 0), Spine=(rp * 0.5, 2, 0), Spine1=(rp * 0.6, 2, 0),
                 Spine2=(rp * 0.5, 1, 0), Neck=(2, 0, 0), Head=(4 + max(0, rp) * 0.4, 0, 0),
                 RightHandFist=(70, 0, 0), LeftHandFist=(70, 0, 0), **vo)
        R = Vector(r) * s
        a = math.radians(alpha)
        h = Vector((0, -math.cos(a), math.sin(a)))
        L = R - h * (HOUWEEL_LINKS * s) + Vector((-0.10, 0, 0)) * s    # palmen liggen ~5 cm buiten het IK-doel
        p["RA"] = arm_ik(M, p, RECHTS, R, (-1.0, 0.3, -0.6), alpha=alpha)
        p["LA"] = arm_ik(M, p, LINKS, L, (0.9, 0.2, -0.6))
        P[f] = p
    k = sleutels_naar_reeksen(P, N, True, M)
    return N, True, k, {"snelheid_mps": 0.0}, {"impact_s": IMP / FPS}


def clip_dragen(M):
    """Iets voor de borst dragen (beker, zak, mand): beide handen voor de borst, ellebogen omlaag langs het lijf.
    Alleen de armen tellen in het spel (bovenlijf-blend over idle/lopen/rennen). 48 frames (2 s), lus, ademt licht."""
    N = 48
    s, sl = M.s, M.sl
    P = {}
    for f in (0, 24, 48):
        t = 0.5 - 0.5 * math.cos(2 * math.pi * f / N)
        p = dict(T=(0, 0, -0.022 * sl), Spine=(-2, 0, 0), Spine1=(-2, 0, 0), Spine2=(-2 - 1.5 * t, 0, 0), Head=(4, 0, 0),
                 RightHandFist=(30, 0, 0), LeftHandFist=(30, 0, 0))
        h = 0.8 + 0.006 * t
        p["RA"] = arm_ik(M, p, RECHTS, Vector((-0.085, -0.25, h)) * s, (-0.5, 0.3, -0.8))
        p["LA"] = arm_ik(M, p, LINKS, Vector((0.085, -0.25, h)) * s, (0.5, 0.3, -0.8))
        P[f] = p
    k = sleutels_naar_reeksen(P, N, True, M)
    return N, True, k, {"snelheid_mps": 0.0}, None


CLIPS = [("idle", clip_idle), ("lopen", clip_lopen), ("rennen", clip_rennen),
         ("bouwen", clip_bouwen), ("aanval_zwaard", clip_zwaard), ("aanval_steen", clip_steen),
         ("zagen", clip_zagen), ("dragen", clip_dragen), ("houweel", clip_houweel)]


def bouw_animaties(rig, alleen=None):
    """Voegt de acties toe aan `rig`. Geeft het sidecar-dict {naam: {loop, duur_s, snelheid_mps, impact_s}}."""
    M = Maten(rig)
    info = {}
    for naam, fn in CLIPS:
        if alleen and naam not in alleen:
            continue
        N, lus, k, extra, tijd = fn(M)
        ex = dict(extra)
        if tijd:
            ex.update(tijd)
        schrijf_actie(rig, M, naam, N, lus, k, ex)
        d = {"loop": lus, "duur_s": round(N / FPS, 4), "snelheid_mps": round(extra["snelheid_mps"], 4),
             "impact_s": round(tijd["impact_s"], 4) if tijd else None}
        if tijd:
            for kk in tijd:
                if kk != "impact_s":
                    d[kk] = round(tijd[kk], 4)
        info[naam] = d
    # rustpose terug, geen actie gekoppeld laten
    for b in rig.pose.bones:
        b.rotation_quaternion = (1, 0, 0, 0)
        b.location = (0, 0, 0)
    rig.animation_data.action = None
    return info


# --- Placeholder-body (alleen standalone) ---------------------------------------------------
class MeshBouwer:
    def __init__(self):
        self.bm = bmesh.new()
        self.groepen = {}

    def _reg(self, groep, res):
        self.groepen.setdefault(groep, []).extend(res["verts"])

    def bol(self, c, r, groep, seg=12):
        rr = r if isinstance(r, (tuple, list)) else (r, r, r)
        M = Matrix.Translation(Vector(c)) @ Matrix.Diagonal((rr[0], rr[1], rr[2], 1.0))
        self._reg(groep, bmesh.ops.create_uvsphere(self.bm, u_segments=seg, v_segments=max(6, seg // 2), radius=1.0, matrix=M))

    def kapsel(self, p0, p1, r0, r1, groep):
        p0, p1 = Vector(p0), Vector(p1)
        v = p1 - p0
        q = v.to_track_quat("Z", "Y")
        M = Matrix.Translation((p0 + p1) / 2) @ q.to_matrix().to_4x4()
        self._reg(groep, bmesh.ops.create_cone(self.bm, cap_ends=True, cap_tris=False, segments=10,
                                               radius1=r0, radius2=r1, depth=v.length, matrix=M))
        self.bol(p0, r0, groep, 10)
        self.bol(p1, r1, groep, 10)

    def doos(self, c, size, groep):
        M = Matrix.Translation(Vector(c)) @ Matrix.Diagonal((size[0], size[1], size[2], 1.0))
        self._reg(groep, bmesh.ops.create_cube(self.bm, size=1.0, matrix=M))

    def naar_object(self, naam, mat):
        bm = self.bm
        bm.verts.ensure_lookup_table()
        bm.verts.index_update()
        for f in bm.faces:
            f.smooth = True
        mesh = bpy.data.meshes.new(naam)
        idx = {g: [v.index for v in vs] for g, vs in self.groepen.items()}
        bm.to_mesh(mesh)
        bm.free()
        mesh.materials.append(mat)
        ob = bpy.data.objects.new(naam, mesh)
        bpy.context.scene.collection.objects.link(ob)
        for g, ids in idx.items():
            ob.vertex_groups.new(name=g).add(ids, 1.0, "REPLACE")
        return ob


def materiaal(naam, kleur):
    m = bpy.data.materials.new(naam)
    m.use_nodes = True
    m.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value = (*kleur, 1)
    m.node_tree.nodes["Principled BSDF"].inputs["Roughness"].default_value = 0.8
    m.diffuse_color = (*kleur, 1)
    return m


def bouw_placeholder(rig, maat=None):
    """Grove placeholder-mesh (capsules en bollen per bot, rigide gewicht) + props op de sockets."""
    m = dict(MAAT)
    m.update(maat or {})
    g = geo(m)
    s = g["s"]
    zh, hx = g["zh"], g["hx"]
    mb = MeshBouwer()
    zs = [rig.data.bones[n].head_local.z for n in ("Spine", "Spine1", "Spine2")]
    mb.bol((0, 0.0, zh + 0.05 * s), (0.15 * s, 0.12 * s, 0.10 * s), "Hips")
    mb.bol((0, -0.01 * s, zs[1] + 0.04 * s), (0.155 * s + m["buik"], 0.125 * s + m["buik"], 0.105 * s), "Spine1")
    mb.bol((0, 0.0, zs[2] + 0.05 * s), (0.175 * s, 0.13 * s, 0.10 * s), "Spine2")
    mb.kapsel((0, 0, g["zn"] - 0.01), (0, 0, g["kop_basis"] + 0.01), 0.055 * s, 0.05 * s, "Neck")
    kopc = (0, 0, g["kop_basis"] + g["kop_h"] / 2)
    mb.bol(kopc, (0.16 * s, 0.165 * s, g["kop_h"] / 2), "Head", 16)
    mb.bol((0, -0.17 * s, kopc[2] - 0.02 * s), 0.03 * s, "Head", 8)       # neus: laat zien waar voor is
    mb.bol((0, 0.02 * s, kopc[2] + 0.1 * s), (0.165 * s, 0.17 * s, 0.09 * s), "Head", 12)   # haar
    for zijde, sg in (("Left", 1), ("Right", -1)):
        bn = rig.data.bones
        b = lambda n: bn[zijde + n]
        ar = b("Arm").head_local
        mb.bol(ar, 0.06 * s, zijde + "Arm")
        mb.kapsel(ar, b("ForeArm").head_local, 0.055 * s, 0.047 * s, zijde + "Arm")
        mb.kapsel(b("ForeArm").head_local, b("Hand").head_local, 0.047 * s, 0.04 * s, zijde + "ForeArm")
        hc = (b("Hand").head_local + b("Hand").tail_local) / 2
        mb.bol(hc, 0.05 * s, zijde + "Hand")
        up = b("UpLeg").head_local
        mb.bol(up, 0.085 * s, zijde + "UpLeg")
        mb.kapsel(up, b("Leg").head_local, 0.08 * s, 0.062 * s, zijde + "UpLeg")
        mb.kapsel(b("Leg").head_local, b("Foot").head_local, 0.06 * s, 0.05 * s, zijde + "Leg")
        mb.doos((sg * hx, -0.025 * s, 0.04 * s), (0.10 * s, 0.17 * s, 0.09 * s), zijde + "Foot")
        mb.doos((sg * hx, -0.14 * s, 0.027 * s), (0.10 * s, 0.06 * s, 0.054 * s), zijde + "ToeBase")
    body = mb.naar_object("bumpkin_body", materiaal("body_grijs", (0.62, 0.62, 0.64)))
    body.parent = rig
    mod = body.modifiers.new("Armature", "ARMATURE")
    mod.object = rig

    def prop(naam, bot, bouw):
        ob = bouw(naam)
        ob.parent = rig
        ob.parent_type = "BONE"
        ob.parent_bone = bot
        blen = rig.data.bones[bot].length
        ob.location = (0, -blen, 0)       # botouder = staart; terug naar de kop (palm)
        return ob

    prop("prop_hamer", "prop_R", lambda n: maak_hamer(n))
    prop("prop_zwaard", "prop_R", lambda n: maak_zwaard(n))
    prop("prop_steen", "prop_R", lambda n: maak_steen(n))
    prop("prop_zaag", "prop_R", lambda n: maak_zaag(n))
    prop("prop_houweel", "prop_R", lambda n: maak_houweel(n))
    return body


def maak_hamer(naam):
    mb = MeshBouwer()
    mb.kapsel((0, -0.07, 0), (0, 0.30, 0), 0.016, 0.014, "hout")
    mb.doos((0, 0.29, 0), (0.06, 0.06, 0.17), "ijzer")
    mb.doos((0, 0.29, 0.115), (0.03, 0.035, 0.07), "ijzer")
    ob = mb.naar_object(naam, materiaal("hamer", (0.45, 0.42, 0.40)))
    for v in list(ob.vertex_groups):
        ob.vertex_groups.remove(v)
    return ob


def maak_zwaard(naam):
    mb = MeshBouwer()
    mb.kapsel((0, -0.07, 0), (0, 0.06, 0), 0.016, 0.016, "x")
    mb.doos((0, 0.07, 0), (0.035, 0.03, 0.20), "x")
    mb.bol((0, -0.075, 0), 0.022, "x", 8)
    bm = mb.bm
    punt = [(0.08, -0.03), (0.52, -0.03), (0.60, 0.0), (0.52, 0.03), (0.08, 0.03)]
    vv = []
    for xs in (-0.008, 0.008):
        vv.append([bm.verts.new((xs, y, z)) for y, z in punt])
    bm.faces.new(vv[0])
    bm.faces.new(list(reversed(vv[1])))
    for i in range(5):
        j = (i + 1) % 5
        bm.faces.new((vv[0][i], vv[0][j], vv[1][j], vv[1][i]))
    ob = mb.naar_object(naam, materiaal("zwaard", (0.75, 0.76, 0.8)))
    for v in list(ob.vertex_groups):
        ob.vertex_groups.remove(v)
    bmesh_fix(ob)
    return ob


def maak_zaag(naam):
    """Handzaag: houten handvat in de palm, blad langs +Y (greep-as), rug boven, tanden aan -Z; blad 0,42 m."""
    mb = MeshBouwer()
    mb.doos((0, 0.0, -0.005), (0.026, 0.11, 0.05), "hout")         # handvat (dicht blok, in de vuist)
    mb.doos((0, 0.055, -0.035), (0.03, 0.03, 0.09), "hout")        # hiel waar het blad in zit
    bm = mb.bm
    # blad: trapezium, rug op z=-0.01, tanden van z=-0.10 (hiel) tot -0.055 (punt), 2 mm dik
    prof = [(0.06, -0.008), (0.48, -0.012), (0.48, -0.055), (0.06, -0.10)]
    vv = []
    for xs in (-0.0012, 0.0012):
        vv.append([bm.verts.new((xs, y, z)) for y, z in prof])
    bm.faces.new(vv[0])
    bm.faces.new(list(reversed(vv[1])))
    for i in range(4):
        j = (i + 1) % 4
        bm.faces.new((vv[0][i], vv[0][j], vv[1][j], vv[1][i]))
    blad_v = set(v for r in vv for v in r)
    ob = mb.naar_object(naam, materiaal("zaag_hout", (0.42, 0.26, 0.13)))
    for v in list(ob.vertex_groups):
        ob.vertex_groups.remove(v)
    ob.data.materials.append(materiaal("zaag_blad", (0.72, 0.73, 0.76)))
    me = ob.data
    nb = len(blad_v)
    for poly in me.polygons:                   # het blad is het laatst aangemaakt: de laatste nb verts
        if min(poly.vertices) >= len(me.vertices) - nb:
            poly.material_index = 1
    bmesh_fix(ob)
    return ob


HOUWEEL_LINKS = 0.20   # linkerhand zoveel (m, x s) lager op de steel dan de rechter


def maak_houweel(naam):
    """Pikhouweel: steel langs +Y (greep-as) van -0,28 tot +0,37 m, ijzeren kop dwars erop langs +-Z (in het
    slagvlak), aan beide kanten taps naar een punt; kop 0,44 m."""
    mb = MeshBouwer()
    mb.kapsel((0, -0.28, 0), (0, 0.37, 0), 0.017, 0.02, "hout")
    n_hout = len(mb.bm.verts)
    mb.doos((0, 0.36, 0), (0.045, 0.06, 0.07), "ijzer")              # oog om de steel
    bm = mb.bm
    for sg in (1, -1):                                                # twee tapse armen naar een punt
        ring0 = [(-0.02, 0.34, 0.03 * sg), (0.02, 0.34, 0.03 * sg), (0.02, 0.38, 0.03 * sg), (-0.02, 0.38, 0.03 * sg)]
        ring1 = [(-0.012, 0.335, 0.13 * sg), (0.012, 0.335, 0.13 * sg), (0.012, 0.365, 0.13 * sg), (-0.012, 0.365, 0.13 * sg)]
        v0 = [bm.verts.new(c) for c in ring0]
        v1 = [bm.verts.new(c) for c in ring1]
        vp = bm.verts.new((0.0, 0.32, 0.22 * sg))
        bm.faces.new(v0)
        for i in range(4):
            j = (i + 1) % 4
            bm.faces.new((v0[i], v0[j], v1[j], v1[i]))
            bm.faces.new((v1[i], v1[j], vp))
    ob = mb.naar_object(naam, materiaal("houweel_hout", (0.42, 0.28, 0.15)))
    for v in list(ob.vertex_groups):
        ob.vertex_groups.remove(v)
    ob.data.materials.append(materiaal("houweel_ijzer", (0.40, 0.40, 0.42)))
    for poly in ob.data.polygons:                # alles na de steel is ijzer
        if min(poly.vertices) >= n_hout:
            poly.material_index = 1
    bmesh_fix(ob)
    return ob


def bmesh_fix(ob):
    bm = bmesh.new()
    bm.from_mesh(ob.data)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bm.to_mesh(ob.data)
    bm.free()


def maak_steen(naam):
    mb = MeshBouwer()
    mb.bol((0, 0.0, 0), (0.065, 0.06, 0.05), "x", 8)
    ob = mb.naar_object(naam, materiaal("steen", (0.5, 0.5, 0.48)))
    for v in list(ob.vertex_groups):
        ob.vertex_groups.remove(v)
    return ob


# --- Hoofdprogramma -----------------------------------------------------------------------
def exporteer(pad):
    kw = dict(filepath=pad, export_format="GLB", export_animations=True, export_animation_mode="ACTIONS",
              export_force_sampling=True, export_yup=True, export_skins=True, export_def_bones=False,
              export_extras=True, use_selection=False)
    bpy.ops.export_scene.gltf(**kw)


def main():
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    alleen = [a for a in argv if not a.startswith("-")] or None
    bpy.ops.wm.read_factory_settings(use_empty=True)
    sc = bpy.context.scene
    sc.render.fps = FPS
    sc.frame_start = 0
    rig = bouw_rig()
    bouw_placeholder(rig)
    info = bouw_animaties(rig, alleen)
    # props staan standaard aan; het spel schakelt zichtbaarheid
    json.dump(info, open(os.path.join(HERE, "bumpkin_anim.json"), "w"), indent=2)
    bpy.ops.wm.save_as_mainfile(filepath=os.path.join(HERE, "bumpkin_test.blend"))
    exporteer(os.path.join(HERE, "bumpkin_test.glb"))
    print("KLAAR", json.dumps(info))


if __name__ == "__main__":
    main()
