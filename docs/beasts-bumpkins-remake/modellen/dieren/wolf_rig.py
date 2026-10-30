"""Skelet + animaties voor de wolf (Beasts & Bumpkins-remake): het viervoeterskelet van koe_rig.py met een
eigen MAAT (digitigrade poten, lange snuit, hangende pluimstaart) en eigen clips.

Draaien (headless):
  blender -b -P wolf_rig.py [-- clip ...]   -> wolf_anim.json en preview/wolf_rig_test.blend (alleen skelet)
Als module (wolf.py):
  import wolf_rig as W
  rig = W.bouw_rig()
  info = W.bouw_animaties(rig)

Botnamen, botrollen, poseformaat en de IK-benen zijn die van koe_rig.py (zie daar). Bij de wolf is
`FrontHoof`/`HindHoof` de voetzool (bal -> teen) en `FrontCannon`/`HindCannon` de middenvoet; `prop_bel`
staat er (ongebruikt) omdat pose_frame hem verwacht. Kijkt naar Blender -Y (Godot +Z), poten op z=0.

Maat: schoft 0,80 m, snuit-zitbeen ~1,45 m, staart tot 0,28 m boven de grond. In de sprites is de wolf
even groot als de koe (zijaanzicht 47 x 33 px, cowwalk ook 47 x 33); dit is een grote wolf, kleiner dan
de koe (schoft 0,97 m) maar op het scherm van dezelfde orde. Een volwassen Bumpkin is 1,37 m.

CLIPS (24 fps; snelheid_mps per lus; het spel schaalt de afspeelsnelheid naar de sim-snelheid):
  idle    snuffelen, oren draaien, staart zwaait laag (4 s)
  lopen   viertakt stap, 0,9 m/s (spel.json wolf.zwerf_mps)
  rennen  galop (gedraaide galop), 2,7 m/s (spel.json wolf.snelheid_mps)
  bijten  uithaal: hurken, sprong naar voren, kaak dicht op impact_s = 0,42 x 0,9 s (Wolf.STRIKE_AT x slag_s), lus
  dood    door de poten zakken en op de flank rollen, 1,0 s (spel.json wolf.sterf_s), eindigt liggend
"""
import json
import math
import os
import sys

import bpy

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import koe_rig as K  # noqa: E402

K.ROMP = (-1.0, 1.0, 1.0)          # geen romp-inkorting (die is van de koe)
FPS = K.FPS
golf, bump, sleutels, optellen = K.golf, K.bump, K.sleutels, K.optellen

# (y, z) in meters, -y = voor; schaal 1
MAAT = {
    "schaal": 1.0,
    "heup": (0.42, 0.74),
    "rug": [(0.22, 0.765), (0.0, 0.775), (-0.20, 0.79), (-0.38, 0.80)],
    "nek": [(-0.36, 0.72), (-0.52, 0.80), (-0.63, 0.87)],
    "kop": [(-0.655, 0.905), (-0.905, 0.825)],                  # achter de oren -> neuspunt
    "kaak": [(-0.71, 0.845), (-0.88, 0.795)],
    "oor": (0.052, -0.675, 0.965), "oor_richting": (0.42, 0.12, 1.0), "oor_lengte": 0.095,
    "staart": [(0.46, 0.745), (0.535, 0.63), (0.565, 0.51), (0.575, 0.39), (0.575, 0.27)],
    "voor_x": 0.085,
    # schoftblad-top, schouder, elleboog, pols, bal, teen
    "voorbeen": [(-0.33, 0.79), (-0.44, 0.60), (-0.33, 0.42), (-0.40, 0.14), (-0.425, 0.035), (-0.49, 0.0)],
    "achter_x": 0.09,
    # heupgewricht, knie, hak, bal, teen
    "achterbeen": [(0.35, 0.67), (0.22, 0.46), (0.40, 0.22), (0.385, 0.035), (0.33, 0.0)],
    "bel": (-0.52, 0.62),
}


def bouw_rig(naam="wolf_rig"):
    rig = K.bouw_rig(MAAT, naam)
    rig["rustpose"] = "staand, kijkt naar -Y"
    return rig


def staart(N, n, amp, achter, fase=0.0, extra=None):
    return K.staart_zwiep(N, n, amp=amp, achter=achter, fase=fase, extra=extra)


def oren(N, links, rechts, amp=18.0):
    """Oren draaien (wolf: naar achteren/opzij, niet flappen)."""
    def L(f):
        b = sum(bump(f, s, 10, N) for s in links)
        return (-4 * b, 0.0, amp * b)
    def R(f):
        b = sum(bump(f, s, 10, N) for s in rechts)
        return (-4 * b, 0.0, amp * b)
    return {"LeftEar": L, "RightEar": R}


# --- Clips ---------------------------------------------------------------------------------------
def clip_idle(M):
    N = 96
    poses = [dict() for _ in range(N + 1)]
    snuf = lambda f: bump(f, 50, 30, N)
    lagen = {
        "T": lambda f: (0.0, 0.0, -0.005 + 0.003 * golf(f, N, 3)),
        "Spine1": lambda f: (0.8 * golf(f, N, 3), 0.0, 0.0),                       # ademen
        "Neck": lambda f: (6 * snuf(f), 0.0, -10 * bump(f, 10, 34, N) + 6 * snuf(f)),
        "Neck1": lambda f: (4 * snuf(f), 0.0, -8 * bump(f, 12, 34, N)),
        "Head": lambda f: (8 * snuf(f) + 3 * bump(f, 56, 6, N) + 3 * bump(f, 66, 6, N), 0.0,
                           -6 * bump(f, 14, 32, N)),
        "Jaw": lambda f: (2 * bump(f, 80, 10, N), 0.0, 0.0),
    }
    lagen.update(oren(N, [20, 70], [44]))
    lagen.update(staart(N, 2, amp=(4, 6, 8, 10), achter=(0, 0, 0, 0)))
    optellen(poses, lagen)
    return N, True, poses, {"snelheid_mps": 0.0}, None


def clip_lopen(M):
    """Viertakt stap (LH, LF, RH, RF), 0,9 m/s: 1 m per cyclus van 1,1 s."""
    N = 26
    Ls = 0.90 * N / FPS
    fases = {"LH": 0.0, "LF": 0.25, "RH": 0.5, "RF": 0.75}
    benen, v = K.gang(M, N, Ls, 0.62, fases,
                      A_B={True: (0.55, 0.45), False: (0.5, 0.5)},
                      lift={True: 0.07, False: 0.06},
                      ca_td={True: -10.0, False: -4.0}, ca_lo={True: 30.0, False: 24.0},
                      ca_swing={True: [(0.35, 80.0), (0.8, 0.0)], False: [(0.35, 40.0), (0.8, -6.0)]},
                      hp_swing={True: [(0.35, 50.0), (0.75, 6.0)], False: [(0.35, 40.0), (0.75, 4.0)]})
    poses = [dict() for _ in range(N + 1)]
    A = Ls * 0.62 * 0.55
    lagen = dict(benen)
    lagen.update({
        "T": lambda f: (0.004 * golf(f, N, 1, 0.6), 0.0, -0.022 + 0.006 * golf(f, N, 2, 0.4)),
        "Hips": lambda f: (0.6 * golf(f, N, 2, 1.2), 2.0 * golf(f, N, 1, 0.3), 2.0 * golf(f, N, 1)),
        "Spine1": lambda f: (0.0, -0.5 * golf(f, N, 1, 0.3), -0.8 * golf(f, N, 1)),
        "Spine2": lambda f: (-0.5 * golf(f, N, 2, 1.2), -0.6 * golf(f, N, 1, 0.3 + math.pi), 0.6 * golf(f, N, 1)),
        "Neck": lambda f: (6 + 2.5 * golf(f, N, 2, 2.2), 0.0, 1.2 * golf(f, N, 1, 0.8)),
        "Neck1": lambda f: (2 + 1.0 * golf(f, N, 2, 2.6), 0.0, 0.8 * golf(f, N, 1, 1.0)),
        "Head": lambda f: (-2 - 1.5 * golf(f, N, 2, 2.6), 0.0, 0.0),
        "LeftScapula": lambda f: (6.0 * -benen["LF"](f)[1] / A, 0.0, 0.0),
        "RightScapula": lambda f: (6.0 * -benen["RF"](f)[1] / A, 0.0, 0.0),
    })
    lagen.update(staart(N, 1, amp=(4, 6, 8, 10), achter=(4, 3, 2, 1)))
    optellen(poses, lagen)
    return N, True, poses, {"snelheid_mps": v}, None


def clip_rennen(M):
    """Gedraaide galop (LH, RH, RF, LF), 2,7 m/s; rug buigt en strekt, kop laag en vooruit."""
    N = 11
    Ls = 2.7 * N / FPS
    fases = {"LH": 0.0, "RH": 0.10, "RF": 0.50, "LF": 0.60}
    benen, v = K.gang(M, N, Ls, 0.34, fases,
                      A_B={True: (0.5, 0.5), False: (0.5, 0.5)},
                      lift={True: 0.13, False: 0.11},
                      ca_td={True: -22.0, False: -14.0}, ca_lo={True: 45.0, False: 40.0},
                      # voor: pols 62 (was 95) en zool 38 (was 70): bij 95 plooide de TRELLIS-pols tot een knik
                      ca_swing={True: [(0.3, 62.0), (0.75, -25.0)], False: [(0.3, 70.0), (0.75, -20.0)]},
                      hp_swing={True: [(0.3, 38.0), (0.7, 10.0)], False: [(0.3, 60.0), (0.7, 8.0)]})
    poses = [dict() for _ in range(N + 1)]
    # rugbuiging: gebogen (+rx = punt omlaag aan de voorkant) als de achterpoten onder het lijf komen
    buig = lambda f: golf(f, N, 1, 0.9)
    lagen = dict(benen)
    lagen.update({
        "T": lambda f: (0.0, 0.0, -0.06 + 0.03 * golf(f, N, 1, 2.2)),
        "Hips": lambda f: (-3 + 7 * buig(f), 1.5 * golf(f, N, 1, 0.3), 0.0),
        "Spine": lambda f: (-3 * buig(f), 0.0, 0.0),
        "Spine1": lambda f: (-4 * buig(f), 0.0, 0.0),
        "Spine2": lambda f: (-3 * buig(f), 0.0, 0.0),
        "Neck": lambda f: (-6 + 5 * golf(f, N, 1, 2.6), 0.0, 0.0),
        "Neck1": lambda f: (-4 + 3 * golf(f, N, 1, 2.9), 0.0, 0.0),
        "Head": lambda f: (8 - 4 * golf(f, N, 1, 3.1), 0.0, 0.0),
        "Jaw": lambda f: (6.0, 0.0, 0.0),
        "LeftEar": lambda f: (-22.0, 0.0, 8.0), "RightEar": lambda f: (-22.0, 0.0, 8.0),
        "LeftScapula": lambda f: (10 * golf(f, N, 1, 0.5), 0.0, 0.0),
        "RightScapula": lambda f: (10 * golf(f, N, 1, 0.9), 0.0, 0.0),
    })
    lagen.update(staart(N, 1, amp=(3, 4, 5, 6), achter=(22, 10, 6, 3), fase=0.5))
    optellen(poses, lagen)
    return N, True, poses, {"snelheid_mps": v}, None


BIJT_N = 22                           # 0,92 s ~ wolf.slag_s 0,9
BIJT_IMPACT = 9                       # 0,42 x 22


def clip_bijten(M):
    """Uithaal: hurken (achterhand laag, kop laag, lippen op), sprong naar voren met open bek, dicht op de
    impact, terug. Voeten blijven staan; de romp schiet ~0,2 m naar voren (T, -y)."""
    N, I = BIJT_N, BIJT_IMPACT
    K_ = {0: {"Neck": (6, 0, 0), "Head": (0, 0, 0)},
          5: {"T": (0, 0.06, -0.08), "Hips": (-4, 0, 0), "Spine2": (4, 0, 0), "Neck": (18, 0, 0), "Neck1": (4, 0, 0),
              "Head": (-16, 0, 0), "Jaw": (10, 0, 0), "LeftEar": (-28, 0, 10), "RightEar": (-28, 0, 10),
              "Tail": (16, 0, 0), "Tail1": (6, 0, 0)},
          8: {"T": (0, -0.16, -0.02), "Hips": (2, 0, 0), "Spine2": (-2, 0, 0), "Neck": (10, 0, 0), "Neck1": (-4, 0, 0),
              "Head": (-6, 0, 0), "Jaw": (34, 0, 0), "LeftEar": (-30, 0, 10), "RightEar": (-30, 0, 10),
              "Tail": (24, 0, 0), "Tail1": (10, 0, 0),
              "LF": (0.0, -0.10, 0.10, 40, 40), "RF": (0.0, -0.06, 0.07, 30, 30)},
          I: {"T": (0, -0.20, -0.05), "Hips": (3, 0, 0), "Neck": (16, 0, 0), "Neck1": (2, 0, 0), "Head": (2, 0, 0),
              "Jaw": (2, 0, 0), "LeftEar": (-30, 0, 10), "RightEar": (-30, 0, 10), "Tail": (24, 0, 0), "Tail1": (10, 0, 0),
              "LF": (0.0, -0.16, 0.0, 0, -8), "RF": (0.0, -0.10, 0.0, 0, -6)},
          12: {"T": (0, -0.17, -0.06), "Hips": (2, 0, 0), "Neck": (20, 0, -6), "Neck1": (4, 0, -4), "Head": (4, 8, 0),
               "Jaw": (4, 0, 0), "LeftEar": (-26, 0, 10), "RightEar": (-26, 0, 10), "Tail": (20, 0, 0),
               "LF": (0.0, -0.16, 0.0, 0, -8), "RF": (0.0, -0.10, 0.0, 0, -6)},
          16: {"T": (0, -0.08, -0.04), "Neck": (12, 0, 4), "Head": (0, -4, 0), "Jaw": (8, 0, 0), "Tail": (12, 0, 0),
               "LF": (0.0, -0.08, 0.05, 30, 30), "RF": (0.0, -0.05, 0.0, 0, -3)},
          20: {"T": (0, 0.0, -0.01), "Neck": (7, 0, 0), "Tail": (4, 0, 0)},
          22: {"Neck": (6, 0, 0), "Head": (0, 0, 0)}}
    poses = sleutels(K_, N, True)
    return N, True, poses, {"snelheid_mps": 0.0}, {"impact_s": I / FPS}


def clip_dood(M):
    """Wankelen, door de voorpoten zakken, achterhand zakt mee, op de rechterflank vallen; kop en staart
    komen op de grond en liggen stil. Eindigt liggend.

    De poten wisselen tijdens de val van wereld- naar lijfkader (kanaal "BL", zie koe_rig.pose_frame): eerst
    staan de voeten op de grond en knikken de poten onder het zakkende lijf, daarna draaien ze mee met de
    rol (Hips ry) en liggen ze ontspannen opzij. Vroeger bleven de doelen in de wereld terwijl het lijf 82
    graden rolde: de poten reikten dwars onder het lijf door naar hun rust-voetplek (gedraaide romp)."""
    N = 24
    rol = 90.0
    # liggend, lijfkader: dx naar buiten, dy (- = voor), lift = naar het lijf toe (dus poot iets gebogen)
    lig = {"BL": (1.0,), "T": (0.0, 0.0, -0.46), "Hips": (0, rol, 0), "Spine": (0, 0, 2), "Spine1": (0, 0, 2),
           "Spine2": (0, 0, 2), "Neck": (-14, 0, 12), "Neck1": (-6, 0, 8), "Head": (6, 0, 8), "Jaw": (8, 0, 0),
           "LeftEar": (-30, 0, 16), "RightEar": (-30, 0, 16),
           "Tail": (24, 0, -6), "Tail1": (10, 0, -6), "Tail2": (4, 0, -4),     # staart achteruit langs de grond
           # rol +90: rechts ligt onder; de linkerpoten (boven) zakken naar binnen op de onderste
           "LF": (-0.10, -0.10, 0.06, 20, 15), "RF": (0.05, -0.06, 0.06, 25, 15),
           "LH": (-0.10, 0.08, 0.05, -10, -15), "RH": (0.05, 0.04, 0.05, -10, -15)}
    K_ = {0: {"BL": (0.0,)},
          4: {"BL": (0.0,), "T": (0.0, 0.0, -0.03), "Hips": (0, 4, 0), "Neck": (12, 0, 4), "Head": (8, 0, 0),
              "LF": (0.0, 0.02, 0.0, 0, 6)},
          9: {"BL": (0.0,), "T": (0.02, -0.02, -0.20), "Hips": (-8, 10, 0), "Spine2": (4, 0, 0), "Neck": (22, 0, 6),
              "Head": (6, 0, 0), "Jaw": (6, 0, 0), "LeftEar": (-20, 0, 10), "RightEar": (-20, 0, 10),
              "LF": (0.0, 0.0, 0.0, 30, 20), "RF": (0.0, 0.0, 0.0, 30, 20),
              "LH": (0.0, 0.0, 0.0, -4, -6), "RH": (0.0, 0.0, 0.0, -4, -6), "Tail": (34, 0, 0), "Tail1": (14, 0, 0)},
          14: {"BL": (0.55,), "T": (0.06, 0.0, -0.31), "Hips": (-4, 45, 0), "Neck": (8, 0, 8), "Neck1": (0, 0, 4),
               "Head": (4, 0, 4), "Jaw": (8, 0, 0),
               "LF": (-0.05, -0.04, 0.06, 25, 20), "RF": (0.02, -0.04, 0.08, 30, 20),
               "LH": (-0.05, 0.04, 0.05, -8, -14), "RH": (0.02, 0.02, 0.06, -10, -14),
               "LeftEar": (-26, 0, 12), "RightEar": (-26, 0, 12), "Tail": (30, 0, -2), "Tail1": (12, 0, 0)},
          19: {**lig, "Hips": (0, rol + 2, 0), "T": (0.0, 0.0, -0.45), "Neck": (-10, 0, 14), "Head": (8, 0, 8)},
          24: lig}
    poses = sleutels(K_, N, False)
    return N, False, poses, {"snelheid_mps": 0.0}, {"impact_s": 19 / FPS}


CLIPS = [("idle", clip_idle), ("lopen", clip_lopen), ("rennen", clip_rennen), ("bijten", clip_bijten),
         ("dood", clip_dood)]


def bouw_animaties(rig, alleen=None):
    return K.bouw_animaties(rig, alleen, CLIPS)


def main():
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    alleen = [a for a in argv if not a.startswith("-")] or None
    bpy.ops.wm.read_factory_settings(use_empty=True)
    sc = bpy.context.scene
    sc.render.fps = FPS
    sc.frame_start = 0
    rig = bouw_rig()
    info = bouw_animaties(rig, alleen)
    json.dump(info, open(os.path.join(HERE, "wolf_anim.json"), "w"), indent=2)
    for c in ("lopen", "rennen"):
        if c in info:
            print("GLIJ", c, json.dumps(K.glijcontrole(rig, c)))
    os.makedirs(os.path.join(HERE, "preview"), exist_ok=True)
    bpy.ops.wm.save_as_mainfile(filepath=os.path.join(HERE, "preview", "wolf_rig_test.blend"))
    print("KLAAR", json.dumps(info))


if __name__ == "__main__":
    main()
