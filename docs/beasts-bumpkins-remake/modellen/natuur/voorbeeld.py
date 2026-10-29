"""Rendert glb's op het iso-gezicht (ortho, yaw 225, pitch 30) met de HDRI en de zon van de hut.

  blender -b -P voorbeeld.py -- items=den_groot,spar [px_per_m=60] [ronde=r1]
Per item: <tmp>/v_<item>[_<variant>].png. Varianten: lod0, sneeuw (met <naam>_sneeuw), lod1 (<naam>_lod1.glb),
rijp (akker). Vaste schaal in px per meter, zodat alles op dezelfde maat staat als de man (1,37 m).
"""
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bpy
from mathutils import Vector

import natuur_lib as L

ITEMS = [i for i in L.OPTS.get("items", "").split(",") if i]
PXM = float(L.OPTS.get("px_per_m", 60))
SPP = int(L.OPTS.get("spp", 96))


def render(glbs, uit, verberg=(), toon_alleen=None, pxm=None):
    glbs = [g for g in glbs if os.path.exists(g)]
    if not glbs:
        return
    sc = L.leeg()
    L.iso_scene(sc)
    sc.cycles.samples = SPP
    objs = []
    for g in glbs:
        objs += L.importeer(g)
    for o in objs:
        if any(((v[1:] not in o.name) and o.type == "MESH") if v.startswith("!") else (v in o.name) for v in verberg):
            o.hide_render = True
    zicht = [o for o in objs if o.type == "MESH" and not o.hide_render]
    cam, scale = L.iso_camera(sc, zicht, marge=1.1)
    # vaste px/m: resolutie uit de ortho-schaal
    w, h = sc.render.resolution_x, sc.render.resolution_y
    f = (pxm or PXM) * scale / max(w, h)
    sc.render.resolution_x, sc.render.resolution_y = max(16, int(w * f)), max(16, int(h * f))
    L.render_naar(sc, uit)


def rij(uit, stukken, pxm):
    """Meerdere glb's op tegelposities (x, y) en draaiing (graden) samen renderen."""
    import math
    sc = L.leeg()
    L.iso_scene(sc)
    sc.cycles.samples = SPP
    objs = []
    for naam, (x, y), rot in stukken:
        nieuw = L.importeer(os.path.join(L.HERE, naam + ".glb"))
        for o in nieuw:
            if "_lod1" in o.name or "_sneeuw" in o.name:
                o.hide_render = True
        for o in nieuw:
            if o.parent is None:
                o.location = (x, y, 0)
                o.rotation_mode = "XYZ"
                o.rotation_euler = (0, 0, math.radians(rot))
        objs += nieuw
    bpy.context.view_layer.update()
    zicht = [o for o in objs if o.type == "MESH"]
    cam, scale = L.iso_camera(sc, zicht, marge=1.05)
    w, h = sc.render.resolution_x, sc.render.resolution_y
    f = (pxm or PXM) * scale / max(w, h)
    sc.render.resolution_x, sc.render.resolution_y = max(16, int(w * f)), max(16, int(h * f))
    L.render_naar(sc, uit)


if __name__ == "__main__":
    for it in ITEMS:
        it, _, pm = it.partition("@")
        pm = float(pm) if pm else None
        naam, _, variant = it.partition(":")
        g0 = os.path.join(L.HERE, naam + ".glb")
        g1 = os.path.join(L.HERE, naam + "_lod1.glb")
        uit = os.path.join(L.STUDIO, f"v_{naam}{'_' + variant if variant else ''}.png")
        if it == "klif_rij":
            rij(uit, [("klif_recht", (4, 0), 0), ("klif_recht", (2, 0), 0), ("klif_hoek_binnen", (0, 0), 0),
                      ("klif_recht", (0, -2), 90), ("klif_recht", (0, -4), 90), ("klif_hoek_buiten", (0, -6), 0),
                      ("klif_recht", (-2, -6), 0), ("klif_recht", (-4, -6), 0)], pm)
            continue
        if it == "hek_rij":
            rij(uit, [("hek_segment", (-2, 0), 0), ("hek_segment", (0, 0), 0), ("hek_segment", (2, 0), 0),
                      ("poort", (4.5, 0), 0), ("hek_paal", (6.5, 0), 0)], pm)
            continue
        if variant == "lod1":
            render([g0], uit, verberg=("!lod1",), pxm=pm)
        elif variant == "sneeuw":
            render([g0], uit, verberg=("_lod1",), pxm=pm)
        elif variant:
            render([os.path.join(L.HERE, f"{naam}_{variant}.glb")], uit, pxm=pm)
        else:
            render([g0], uit, verberg=("_sneeuw", "_lod1"), pxm=pm)
    L.log("KLAAR")
