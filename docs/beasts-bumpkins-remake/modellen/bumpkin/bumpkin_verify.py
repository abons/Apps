"""Leest bumpkin_test.glb terug in een lege scene en controleert botnamen, animaties en sockets.
  blender -b -P bumpkin_verify.py"""
import os

import bpy

HERE = os.path.dirname(os.path.abspath(__file__))
VERWACHT_BOTEN = ["Hips", "Spine", "Spine1", "Spine2", "Neck", "Head", "HeadTop_End",
                  "LeftShoulder", "LeftArm", "LeftForeArm", "LeftHand", "RightShoulder", "RightArm", "RightForeArm",
                  "RightHand", "LeftUpLeg", "LeftLeg", "LeftFoot", "LeftToeBase", "RightUpLeg", "RightLeg",
                  "RightFoot", "RightToeBase", "prop_R", "prop_L"]
VERWACHT_ANIM = ["idle", "lopen", "rennen", "bouwen", "aanval_zwaard", "aanval_steen"]

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=os.path.join(HERE, "bumpkin_test.glb"))
arms = [o for o in bpy.data.objects if o.type == "ARMATURE"]
print("ARMATUREN", [o.name for o in arms])
namen = {b.name for a in arms for b in a.data.bones}
print("ONTBREEKT", [b for b in VERWACHT_BOTEN if b not in namen])
print("EXTRA", sorted(namen - set(VERWACHT_BOTEN)))
acts = sorted(a.name for a in bpy.data.actions)
print("ACTIES", acts)
for a in bpy.data.actions:
    print(" ", a.name, "frames", tuple(a.frame_range), "extras", {k: a[k] for k in a.keys() if not k.startswith("_")})
print("ANIM ONTBREEKT", [n for n in VERWACHT_ANIM if not any(x == n or x.startswith(n) for x in acts)])
for o in bpy.data.objects:
    if o.name.startswith("prop_") or o.type == "MESH":
        print("OBJ", o.name, o.type, "parent", o.parent.name if o.parent else None, o.parent_type, o.parent_bone,
              "wereld", tuple(round(c, 3) for c in o.matrix_world.translation))
