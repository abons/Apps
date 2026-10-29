"""Vogelskelet + animaties voor de kip (hen) van de Beasts & Bumpkins-remake.

Draaien (headless):
  blender -b -P kip_rig.py [-- clip ...]   -> kip_anim.json, preview/kip_rig_test.blend (alleen skelet)
                                              en de glijcontrole van de voeten in de log
Als module (de modeller, kip.py):
  import kip_rig
  rig = kip_rig.bouw_rig()
  info = kip_rig.bouw_animaties(rig)            # acties + sidecar-dict, zie CLIPS

RUSTPOSE: staand, hen van ~0,40 m tot de kam. Armatuur `kip_rig` in meters, kijkt naar Blender -Y
(glTF/Godot +Z), voeten op z=0, oorsprong tussen de voeten. Links = +X (gezien vanuit de kip).
Armatuur-object staat op identiteit.

BONEN:
  romp: Hips (wortel, van de staartkant naar voren), Spine (borst)
  hals/kop: Neck, Neck1, Head (van de nek naar de snavelpunt)
  Tail (kind van Hips, staartwaaier omhoog), {Left,Right}Wing (kind van Spine, gevouwen vleugel)
  poot: {L,R}Thigh (dij, in het lijf), {L,R}Shin (drumstick, knie -> hak), {L,R}Tarsus (loopbeen,
        hak -> bal), {L,R}Foot (bal -> middelste teen)

ANIMATIE: alles als rotatie "om wereldassen in de rustpose" (X = links, buig-as: +rx kantelt een naar
voren wijzend bot omlaag en een omhoog wijzend bot naar voren), plus de Hips-locatie. Eigen FK in
Python; de poten per frame met tweebots-IK (Shin + Tarsus, hak naar achteren) op een baldoel, en de
voet krijgt een absolute kanteling (0 = tenen plat). Een geplante voet staat dus exact stil.
Clips (24 fps): idle, lopen, pikken, zitten - alle vier een lus. Elke actie heeft custom property
`snelheid_mps`; zie ook kip_anim.json.
"""
import json
import math
import os
import sys

import bpy
from mathutils import Quaternion, Vector

HERE = os.path.dirname(os.path.abspath(__file__))
FPS = 24
ZIJDEN = (("Left", 1), ("Right", -1))
AX = {"X": Vector((1, 0, 0)), "Y": Vector((0, 1, 0)), "Z": Vector((0, 0, 1))}

# --- Maten (meters). Hen: kam ~0,40 m, snavel-staart ~0,45 m. x apart voor de poten ----------------
J = {
    "heup": (0.0, 0.040, 0.165), "rug": (0.0, -0.030, 0.180), "borst": (0.0, -0.072, 0.226),
    "nek": (0.0, -0.094, 0.278), "kopvoet": (0.0, -0.110, 0.316), "snavel": (0.0, -0.184, 0.326),
    "staart0": (0.0, 0.105, 0.215), "staart1": (0.0, 0.200, 0.330),
    "vleugel0": (0.070, -0.040, 0.232), "vleugel1": (0.066, 0.130, 0.200),
    "heupgewricht": (0.042, 0.030, 0.155), "knie": (0.042, -0.006, 0.124), "hak": (0.042, 0.030, 0.076),
    "bal": (0.042, 0.004, 0.012), "teen": (0.042, -0.046, 0.004),
}
BEEN = ["Thigh", "Shin", "Tarsus", "Foot"]


def jp(naam, sg=1):
    x, y, z = J[naam]
    return Vector((sg * x, y, z))


def botten():
    """(naam, ouder, kop, staart) in hiërarchievolgorde."""
    L = [("Hips", None, jp("heup"), jp("rug")), ("Spine", "Hips", jp("rug"), jp("borst")),
         ("Neck", "Spine", jp("borst"), jp("nek")), ("Neck1", "Neck", jp("nek"), jp("kopvoet")),
         ("Head", "Neck1", jp("kopvoet"), jp("snavel")), ("Tail", "Hips", jp("staart0"), jp("staart1"))]
    for z, sg in ZIJDEN:
        L.append((z + "Wing", "Spine", jp("vleugel0", sg), jp("vleugel1", sg)))
        pts = [jp(n, sg) for n in ("heupgewricht", "knie", "hak", "bal", "teen")]
        ouder = "Hips"
        for i, b in enumerate(BEEN):
            L.append((z + b, ouder, pts[i], pts[i + 1]))
            ouder = z + b
    return L


def bouw_rig(naam="kip_rig"):
    arm = bpy.data.armatures.new(naam)
    rig = bpy.data.objects.new(naam, arm)
    bpy.context.scene.collection.objects.link(rig)
    bpy.context.view_layer.objects.active = rig
    rig.select_set(True)
    rig["rustpose"] = "staand, kijkt naar -Y, voeten op z=0"
    bpy.ops.object.mode_set(mode="EDIT")
    eb = arm.edit_bones
    for nm, ouder, kop, staart in botten():
        b = eb.new(nm)
        b.head, b.tail = kop, staart
        b.align_roll(Vector((1, 0, 0)) if abs((staart - kop).normalized().x) < 0.9 else Vector((0, 0, 1)))
        if ouder:
            b.parent = eb[ouder]
        b.use_connect = False
    bpy.ops.object.mode_set(mode="OBJECT")
    return rig


# --- FK / IK in Python ---------------------------------------------------------------------------
class Maten:
    def __init__(self, rig):
        self.lijst = botten()
        self.ouder = {b[0]: b[1] for b in self.lijst}
        self.kop = {b[0]: b[2] for b in self.lijst}
        self.staart = {b[0]: b[3] for b in self.lijst}
        self.rr = {b.name: b.matrix_local.to_quaternion() for b in rig.data.bones}


def Q(*rots):
    """Q(('X', 10), ('Z', -5)) -> wereldas-rotatie; eerst de eerste."""
    q = Quaternion()
    for ax, g in rots:
        if g:
            q = Quaternion(AX[ax], math.radians(g)) @ q
    return q


TEKORT = {"n": 0}


def pose_frame(M, pose):
    """pose: {'T': Vector, 'rot': {bot: Quaternion (wereldassen)}, 'voet': {zijde: (bal Vector, kanteling)}}
    -> ({bot: lokale quat}, Hips-locatie lokaal, {bot: (kop, staart)} in armatuurruimte)."""
    T = Vector(pose.get("T", (0, 0, 0)))
    rot = pose.get("rot", {})
    voet = pose.get("voet", {})
    Dl, Dw, pos = {}, {}, {}

    def plaats(b, d):
        p = M.ouder[b]
        Dl[b] = d
        if p is None:
            Dw[b], pos[b] = d, M.kop[b] + T
        else:
            Dw[b], pos[b] = Dw[p] @ d, pos[p] + Dw[p] @ (M.kop[b] - M.kop[p])

    def staart(b):
        return pos[b] + Dw[b] @ (M.staart[b] - M.kop[b])

    for b, p, _, _ in M.lijst:
        if any(b.endswith(x) for x in ("Shin", "Tarsus", "Foot")):
            continue
        plaats(b, rot.get(b, Quaternion()))
    for z, sg in ZIJDEN:
        bal, kant = voet.get(z, (jp("bal", sg), 0.0))
        bal = Vector(bal)
        K = staart(z + "Thigh")
        L1 = (M.staart[z + "Shin"] - M.kop[z + "Shin"]).length
        L2 = (M.staart[z + "Tarsus"] - M.kop[z + "Tarsus"]).length
        d = bal - K
        d.x = 0.0                                   # been in het zijvlak
        a = d.length
        if a > (L1 + L2) * 0.999 or a < abs(L1 - L2) + 1e-3:
            TEKORT["n"] += 1
        a = min(max(a, abs(L1 - L2) + 1e-3), (L1 + L2) * 0.999)
        basis = math.atan2(d.z, d.y)
        hoek = math.acos(max(-1, min(1, (L1 * L1 + a * a - L2 * L2) / (2 * L1 * a))))
        kand = [Vector((0, math.cos(basis + s * hoek), math.sin(basis + s * hoek))) * L1 for s in (1, -1)]
        hak = K + max(kand, key=lambda v: v.y)      # hak naar achteren
        r0 = (M.staart[z + "Shin"] - M.kop[z + "Shin"]).normalized()
        D1 = r0.rotation_difference((hak - K).normalized())
        plaats(z + "Shin", Dw[z + "Thigh"].inverted() @ D1)
        eind = K + d.normalized() * a
        eind.x = bal.x
        r0 = (M.staart[z + "Tarsus"] - M.kop[z + "Tarsus"]).normalized()
        D2 = r0.rotation_difference((eind - staart(z + "Shin")).normalized())
        plaats(z + "Tarsus", Dw[z + "Shin"].inverted() @ D2)
        plaats(z + "Foot", Dw[z + "Tarsus"].inverted() @ Q(("X", kant)))
    qs = {b: M.rr[b].inverted() @ Dl[b] @ M.rr[b] for b in Dl}
    kops = {b: (pos[b], staart(b)) for b in Dl}
    return qs, M.rr["Hips"].inverted() @ T, kops


def schrijf_actie(rig, M, naam, poses, lus, extra):
    act = bpy.data.actions.new(naam)
    act.use_fake_user = True
    rig.animation_data_create()
    rig.animation_data.action = act
    pb = rig.pose.bones
    for b in pb:
        b.rotation_mode = "QUATERNION"
    vorige = {}
    N = len(poses) - 1
    for f, pose in enumerate(poses):
        qs, loc, _ = pose_frame(M, pose)
        for nb, q in qs.items():
            v = vorige.get(nb)
            if v is not None and v.dot(q) < 0:
                q = -q
            vorige[nb] = q.copy()
            pb[nb].rotation_quaternion = q
            pb[nb].keyframe_insert("rotation_quaternion", frame=f)
        pb["Hips"].location = loc
        pb["Hips"].keyframe_insert("location", frame=f)
    for k, v in extra.items():
        act[k] = v
    act.use_frame_range = True
    act.frame_start, act.frame_end = 0, N
    act.use_cyclic = lus
    return act


# --- Hulpjes voor de tijdlijn ---------------------------------------------------------------------
def glad(u):
    u = min(max(u, 0.0), 1.0)
    return u * u * (3 - 2 * u)


def schok(f, N, keys, ramp=3):
    """Schokkerig: waarde houdt stand tot de volgende sleutel, dan in `ramp` frames erheen (lus over N).
    keys: [(frame, (waarden...)), ...], gesorteerd, eerste op frame 0."""
    w = keys[-1][1]
    for i, (fk, vk) in enumerate(keys):
        if f >= fk:
            vorig = keys[i - 1][1] if i > 0 else keys[-1][1]
            u = glad((f - fk) / ramp) if ramp > 0 else 1.0
            w = tuple(a + (b - a) * u for a, b in zip(vorig, vk))
    return w


def golf(f, N, n=1, fase=0.0):
    return math.sin(2 * math.pi * (n * f / N + fase))


# --- Clips ---------------------------------------------------------------------------------------
def rust_voeten(dz=0.0):
    return {z: (jp("bal", sg), 0.0) for z, sg in ZIJDEN}


def kop_draai(yaw, rol, pitch, hals=0.4):
    """Kop rondkijken: yaw/rol verdeeld over Neck1 en Head, pitch op de kop."""
    return {"Neck1": Q(("Z", yaw * hals)), "Head": Q(("X", pitch), ("Y", rol), ("Z", yaw * (1 - hals)))}


def clip_idle(M):
    N = 96
    keys = [(0, (0, 0, 0)), (10, (28, 0, -4)), (22, (28, 14, -4)), (31, (-12, 0, 2)), (44, (-34, -12, 0)),
            (58, (-34, 0, 6)), (66, (8, 0, -12)), (80, (14, 18, -6)), (88, (0, 0, 0))]
    poses = []
    for f in range(N + 1):
        yaw, rol, pitch = schok(f, N, keys, 3)
        r = kop_draai(yaw, rol, pitch)
        adem = golf(f, N, 3)
        r["Spine"] = Q(("X", 1.0 * adem))
        r["Neck"] = Q(("X", -1.0 * adem))
        r["Tail"] = Q(("X", 2.0 * golf(f, N, 2, 0.1)), ("Z", 3.0 * golf(f, N, 1, 0.3)))
        poses.append({"T": (0, 0, 0.0012 * adem), "rot": r, "voet": rust_voeten()})
    return N, True, poses, {"snelheid_mps": 0.0}


V_LOPEN = 0.35


def clip_lopen(M):
    N = 12                                   # 0,5 s per cyclus, twee stappen
    T = N / FPS
    beta = 0.6                               # standfractie
    Ls = V_LOPEN * beta * T                  # standlengte (bal schuift met v naar achteren)
    til = 0.030
    poses = []
    for f in range(N + 1):
        ph = f / N
        voet, rot = {}, {}
        for z, sg in ZIJDEN:
            fz = (ph + (0.0 if sg == 1 else 0.5)) % 1.0
            b0 = jp("bal", sg)
            if fz < beta:
                s = fz / beta
                y, h, kant = b0.y - Ls / 2 + Ls * s, 0.0, 0.0
            else:
                u = (fz - beta) / (1 - beta)
                y = b0.y + Ls / 2 - Ls * glad(u)
                h = til * math.sin(math.pi * u) ** 0.8
                kant = 40.0 * math.sin(math.pi * u)            # tenen krullen in de zwaai
            voet[z] = (Vector((b0.x, y, b0.z + h)), kant)
            rot[z + "Thigh"] = Q(("X", 28.0 * (y - b0.y) / Ls))
        # kopknik per stap: de kop "staat stil" (schuift t.o.v. het lijf naar achteren), dan een stoot naar voren
        psi = (2 * ph) % 1.0
        sch = -1 + 2 * psi / 0.72 if psi < 0.72 else 1 - 2 * glad((psi - 0.72) / 0.28)
        rot["Hips"] = Q(("X", 1.5 * golf(f, N, 2, 0.25)))
        rot["Spine"] = Q(("X", 6.0))
        rot["Neck"] = Q(("X", -11.0 * sch))
        rot["Neck1"] = Q(("X", -7.0 * sch))
        rot["Head"] = Q(("X", 18.0 * sch - 6.0))
        rot["Tail"] = Q(("X", 3.0 * golf(f, N, 2, 0.4)), ("Z", 2.5 * golf(f, N, 1)))
        for z, sg in ZIJDEN:
            rot[z + "Wing"] = Q(("Y", sg * 2.0 * golf(f, N, 2, 0.1)))
        poses.append({"T": (0, 0, -0.004 + 0.0035 * golf(f, N, 2, 0.25)), "rot": rot, "voet": voet})
    return N, True, poses, {"snelheid_mps": V_LOPEN}


def pik_pose(M, p, k, rol=0.0):
    """p in [0, 1]: 0 = rechtop, 1 = snavel op de grond; k = schaal die snavel_z(1) ~ 0,012 maakt."""
    a = p * k
    return {"Hips": Q(("X", 13 * a)), "Spine": Q(("X", 10 * a)), "Neck": Q(("X", 44 * a)),
            "Neck1": Q(("X", 34 * a)), "Head": Q(("X", 62 * p - (13 + 10 + 44 + 34) * a), ("Y", rol))}


def snavel_z(M, p, k):
    _, _, kops = pose_frame(M, {"T": (0, 0, -0.012 * p), "rot": pik_pose(M, p, k), "voet": rust_voeten()})
    return kops["Head"][1].z


def clip_pikken(M):
    N = 72
    lo, hi = 0.2, 2.0
    for _ in range(40):                       # k zo dat de snavelpunt bij p=1 net de grond raakt
        k = 0.5 * (lo + hi)
        if snavel_z(M, 1.0, k) > 0.010:
            lo = k
        else:
            hi = k
    keys = [(0, 0.0), (10, 0.0), (15, 1.0), (19, 0.62), (23, 1.0), (27, 0.62), (31, 1.0), (37, 0.45), (44, 0.0)]
    poses = []
    for f in range(N + 1):
        p = keys[-1][1]
        for i in range(len(keys) - 1):
            (f0, v0), (f1, v1) = keys[i], keys[i + 1]
            if f0 <= f <= f1:
                u = (f - f0) / (f1 - f0)
                # neer = snel (versnellend), op = afremmend
                p = v0 + (v1 - v0) * (u * u if v1 > v0 else 1 - (1 - u) ** 2)
        rol = 16.0 * glad((f - 37) / 6) * (1 - glad((f - 60) / 6))     # na het pikken: schuin kijken
        yaw = 18.0 * glad((f - 40) / 4) * (1 - glad((f - 60) / 6))
        r = pik_pose(M, p, k, rol)
        r["Neck1"] = Q(("Z", yaw * 0.4)) @ r["Neck1"]
        r["Head"] = Q(("Z", yaw * 0.6)) @ r["Head"]
        r["Tail"] = Q(("X", -6 * p))
        poses.append({"T": (0, 0, -0.012 * p), "rot": r, "voet": rust_voeten()})
    return N, True, poses, {"snelheid_mps": 0.0, "pik_k": k}


def clip_zitten(M):
    N = 96
    poses = []
    for f in range(N + 1):
        adem = golf(f, N, 3)
        r = {"Hips": Q(("X", -5.0)), "Spine": Q(("X", 2.0 + 1.2 * adem)), "Neck": Q(("X", -14.0)),
             "Neck1": Q(("X", 8.0), ("Z", 12.0 * golf(f, N, 1))),
             "Head": Q(("X", 9.0), ("Y", 5.0 * golf(f, N, 1, 0.2)), ("Z", 8.0 * golf(f, N, 1))),
             "Tail": Q(("X", -10.0))}
        for z, sg in ZIJDEN:
            r[z + "Wing"] = Q(("Z", -sg * (5.0 + 1.0 * adem)), ("Y", sg * 4.0))
        poses.append({"T": (0, 0.004, -0.072 + 0.0018 * adem), "rot": r, "voet": rust_voeten()})
    return N, True, poses, {"snelheid_mps": 0.0}


CLIPS = [("idle", clip_idle), ("lopen", clip_lopen), ("pikken", clip_pikken), ("zitten", clip_zitten)]


def bouw_animaties(rig, alleen=None):
    M = Maten(rig)
    info = {}
    for naam, fn in CLIPS:
        if alleen and naam not in alleen:
            continue
        TEKORT["n"] = 0
        N, lus, poses, extra = fn(M)
        schrijf_actie(rig, M, naam, poses, lus, extra)
        if TEKORT["n"]:
            print(f"[kip_rig] {naam}: {TEKORT['n']} beendoelen buiten bereik (geklemd)")
        info[naam] = {"loop": lus, "duur_s": round(N / FPS, 4), "snelheid_mps": round(extra["snelheid_mps"], 4),
                      "impact_s": None}
    if "lopen" in info:                       # eerlijk: de snelheid uit de gebakken voeten zelf
        g = glijcontrole(rig)
        info["lopen"]["snelheid_mps"] = g["v_gemeten"]
        bpy.data.actions["lopen"]["snelheid_mps"] = g["v_gemeten"]
        print("[kip_rig] glij", json.dumps(g))
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


def glijcontrole(rig, naam="lopen"):
    """Uit de gebakken actie: per voet de standframes (bal op de grond), de gemiddelde terugloopsnelheid van
    de bal (= de grondsnelheid waarbij niets glijdt) en het restglijden t.o.v. die snelheid."""
    zet_actie(rig, naam)
    sc = bpy.context.scene
    act = bpy.data.actions[naam]
    N = int(act.frame_end)
    snel, uit = [], {}
    for z, _ in ZIJDEN:
        pts = []
        for f in range(N + 1):
            sc.frame_set(f)
            k = rig.matrix_world @ rig.pose.bones[z + "Foot"].head
            pts.append((f, k.y, k.z))
        laag = min(p[2] for p in pts)
        stand = [p for p in pts[:-1] if p[2] < laag + 0.0005]
        # standframes aaneengesloten maken over de lusgrens
        st = sorted(stand, key=lambda p: (p[0] - stand[0][0]) % N)
        segs = [(st[i + 1][1] - st[i][1]) / (((st[i + 1][0] - st[i][0]) % N) / FPS)
                for i in range(len(st) - 1) if (st[i + 1][0] - st[i][0]) % N == 1]
        v = sum(segs) / max(len(segs), 1)
        snel.append(v)
        rest = [abs(s - v) for s in segs]
        uit[z] = {"stand_frames": len(stand), "v": round(v, 4), "max_afwijking_mps": round(max(rest or [0]), 4)}
    uit["v_gemeten"] = round(sum(snel) / len(snel), 4)
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
    json.dump(info, open(os.path.join(HERE, "kip_anim.json"), "w"), indent=2)
    os.makedirs(os.path.join(HERE, "preview"), exist_ok=True)
    bpy.ops.wm.save_as_mainfile(filepath=os.path.join(HERE, "preview", "kip_rig_test.blend"))
    print("KLAAR", json.dumps(info))


if __name__ == "__main__":
    main()
