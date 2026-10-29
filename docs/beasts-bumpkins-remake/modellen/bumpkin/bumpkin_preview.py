"""Contactbladen per animatie (8 frames, 3/4-aanzicht + zijaanzicht) uit bumpkin_test.blend.

  blender -b -P bumpkin_preview.py -- [animatie ...]
Schrijft preview/<naam>.png (3/4) en preview/<naam>_zij.png (zijaanzicht).
"""
import math
import os
import sys

import bpy
import numpy as np
from mathutils import Vector

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "preview")
os.makedirs(OUT, exist_ok=True)
argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
W, Hh, KOLOM, AANTAL = 300, 400, 4, 8

bpy.ops.wm.open_mainfile(filepath=os.path.join(HERE, "bumpkin_test.blend"))
sc = bpy.context.scene
sc.render.engine = "BLENDER_WORKBENCH"
sc.render.resolution_x, sc.render.resolution_y = W, Hh
sc.render.film_transparent = False
sh = sc.display.shading
sh.light = "STUDIO"
sh.color_type = "MATERIAL"
sh.show_shadows = True
sh.background_type = "WORLD"
sc.world = bpy.data.worlds.new("w")
sc.world.color = (0.82, 0.86, 0.9)
rig = bpy.data.objects["bumpkin_rig"]

# vloer met streepjes elke 0,25 m
mv = bpy.data.materials.new("vloer")
mv.diffuse_color = (0.55, 0.6, 0.5, 1)
ms = bpy.data.materials.new("streep")
ms.diffuse_color = (0.25, 0.3, 0.25, 1)
bpy.ops.mesh.primitive_plane_add(size=6, location=(0, 0, -0.002))
bpy.context.object.data.materials.append(mv)
for i in range(-12, 13):
    bpy.ops.mesh.primitive_cube_add(size=1, location=(0, i * 0.25, 0.0), scale=(3, 0.01, 0.002))
    bpy.context.object.data.materials.append(ms)
    bpy.ops.mesh.primitive_cube_add(size=1, location=(i * 0.25, 0, 0.0), scale=(0.01, 3, 0.002))
    bpy.context.object.data.materials.append(ms)

cam_d = bpy.data.cameras.new("c")
cam_d.type = "ORTHO"
cam_d.ortho_scale = 2.0
cam = bpy.data.objects.new("c", cam_d)
sc.collection.objects.link(cam)
sc.camera = cam
doel = Vector((0, 0, 0.62))


def kijk(pos):
    cam.location = pos
    cam.rotation_euler = (doel - pos).to_track_quat("-Z", "Y").to_euler()


def render_blad(naam, frames, pos, pad):
    kijk(pos)
    tegels = []
    for f in frames:
        sc.frame_set(f)
        bpy.context.view_layer.update()
        tmp = os.path.join(OUT, "_t.png")
        sc.render.filepath = tmp
        bpy.ops.render.render(write_still=True)
        img = bpy.data.images.load(tmp, check_existing=False)
        buf = np.empty(W * Hh * 4, np.float32)
        img.pixels.foreach_get(buf)
        tegels.append(buf.reshape(Hh, W, 4).copy())
        bpy.data.images.remove(img)
    rijen = math.ceil(len(tegels) / KOLOM)
    blad = np.ones((rijen * Hh, KOLOM * W, 4), np.float32)
    for i, t in enumerate(tegels):
        r, c = divmod(i, KOLOM)
        y0 = (rijen - 1 - r) * Hh
        blad[y0:y0 + Hh, c * W:(c + 1) * W] = t
        blad[y0:y0 + Hh, c * W:c * W + 1] = 0.2
        blad[y0 + Hh - 1:y0 + Hh, c * W:(c + 1) * W] = 0.2
    img = bpy.data.images.new("blad", KOLOM * W, rijen * Hh)
    img.pixels.foreach_set(blad.ravel())
    img.filepath_raw = pad
    img.file_format = "PNG"
    img.save()
    bpy.data.images.remove(img)


for act in list(bpy.data.actions):
    if argv and act.name not in argv:
        continue
    rig.animation_data_create()
    rig.animation_data.action = act
    try:
        rig.animation_data.action_slot = act.slots[0]
    except Exception:
        pass
    welke = {"bouwen": "prop_hamer", "aanval_zwaard": "prop_zwaard", "aanval_steen": "prop_steen"}.get(act.name)
    for pn in ("prop_hamer", "prop_zwaard", "prop_steen"):
        bpy.data.objects[pn].hide_render = pn != welke
    n = int(act.frame_end)
    lus = bool(act.get("snelheid_mps", 0) > 0 or act.use_cyclic)
    stap = n / AANTAL if lus else n / (AANTAL - 1)
    frames = [int(round(i * stap)) for i in range(AANTAL)]
    render_blad(act.name, frames, Vector((1.9, -2.6, 1.3)), os.path.join(OUT, act.name + ".png"))
    render_blad(act.name, frames, Vector((3.2, 0.0, 0.62)), os.path.join(OUT, act.name + "_zij.png"))
    print("blad", act.name, frames)
try:
    os.remove(os.path.join(OUT, "_t.png"))
except OSError:
    pass
