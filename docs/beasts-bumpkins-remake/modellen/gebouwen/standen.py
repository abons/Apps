"""Bouwstanden 1-3 van de gebouwen, gesneden uit de afgewerkte game-glb (stand 4 = <naam>_rt.glb).

Zelfde besluit als de hut (2026-10-30): de standen komen UIT het afgewerkte model, zodat muren, ramen en
deuren in elke stand gelijk doorlopen. Het script opent <naam>_rt.blend en hergebruikt de gebakken eilanden met
hun eigen UV's op de atlassen van de af-glb (gedeelde code: standen_lib.py, ook gebruikt door de hut).

Welk eiland wat is: de rt-meshes zijn samengevoegd, dus elk los eiland krijgt de naam van het bronobject in
<naam>.blend waarvan de bbox het best past (`stijl`, `kern`, `pan`, ...). Per gebouw zegt CFG per naam wat
er in stand 2 en 3 mee gebeurt:
- `weg`: niet in deze stand; `heel`: ongewijzigd;
- `auto`: kleine eilanden (stenen, latjes) heel of weg op hun midden, zodat de muurkop rafelig blijft; grote
  (planken, palen, pleister) doorgesneden op de muurhoogte en dichtgemaakt met de kleur van hun zijkant;
- `hol`: een dichte kern (doos) wordt een muurschil met binnenkant en muurkop, met de deuropeningen;
- `steen@z` / `snij@z`: als auto, maar op een eigen hoogte (halve schoorsteen).
Stand 1 is de bouwgrond (veelhoek `voet`) met paaltjes en touw; stand 3 krijgt dakspanten en gordingen die de
onderkant van het dak volgen (doorsnedes van de dakmesh, `spanten`). Deurbladen en wieken (meshes onder een
scharnier) zitten in geen enkele stand; alle ankers (lege nodes) gaan mee, op dezelfde plek.

Draaien (headless, eerst de rt-stap van het gebouw):
  blender -b -P standen.py -- naam=molen [standen=1,2,3] [preview] [alleen_preview]
Schrijft <naam>_stand1.glb .. _stand3.glb naast dit script; `preview` rendert ../render/<naam>_standen.png
(stand 1 | 2 | 3 | af, EEVEE met camera en licht van <naam>.blend). Oorsprong, schaal en assen zijn die van
<naam>_rt.glb: in Godot op exact dezelfde transform wisselen.
"""
import math
import os
import random
import re
import sys

import bmesh
import bpy
import numpy as np
from mathutils import Vector

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import standen_lib as L                          # noqa: E402

argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
OPTS = {a.split("=")[0]: (a.split("=", 1)[1] if "=" in a else "1") for a in argv}
NAAM = OPTS.get("naam", "molen")
STANDEN = [int(s) for s in OPTS.get("standen", "1,2,3").split(",") if s]
GLB = lambda s: os.path.join(HERE, f"{NAAM}_stand{s}.glb")

# --- Configuratie per gebouw -----------------------------------------------------------------------
# rollen: naam -> (stand 2, stand 3); `standaard` voor de rest. voet: veelhoek van het plan (xy).
# spanten: (as van het snijvlak, posities, bereik op de andere horizontale as, breedte, dikte);
# de doorsnede van de dakmesh (eilanden met een naam uit `dak`) geeft de lijn langs de onderkant van het dak.
WEG = ("weg", "weg")
CFG = {
    "gereedschapsloods": dict(
        z2=0.7, dik=0.22, standaard=("auto", "heel"),
        rollen={**{n: WEG for n in ("pan", "beschot", "nokvorst", "bloembak", "bakdrager", "bakaarde", "steel",
                                     "Icosphere", "Sphere", "hoorn", "hiel", "lijf", "werkvlak", "hardygat",
                                     "prikgat")},
                "kern": ("hol", "hol@99"), "deurgat": WEG, "gras": ("heel", "heel")},
        voet=[(-1.75, -1.25), (0.85, -1.25), (0.85, 0.95), (-1.75, 0.95)], marge=0.3,
        dak=("pan", "beschot"), sjabloon="stijl", touw="dorpel", gras=("gras",),
        spanten=[("x", np.arange(-2.05, 2.1, 0.5), (-1.6, 1.6), 0.09, 0.08),
                 ("y", (-1.05, -0.55, 0.0, 0.55, 1.05), (-2.25, 2.1), 0.08, 0.08)],
    ),
    "molen": dict(
        z2=0.7, dik=0.2, standaard=("auto", "heel"),
        rollen={**{n: WEG for n in ("dak", "rank", "blad", "zak", "kapdakplank", "boeiplank")},
                "kern": ("hol", "heel"), "voetkern": ("weg", "heel"), "deurgat": ("weg", "heel"),
                "gevelgat": ("weg", "heel"), "gras": ("heel", "heel")},
        rek={"voetkern": (2.45, 1.8)},                 # de stenen voet staat in de af-molen op het riet
        voet=[(-2.85, -0.9), (1.15, -0.9), (1.15, -2.2), (2.85, -2.2), (2.85, 2.2), (-2.85, 2.2)], marge=0.3,
        dak=("dak",), sjabloon="hoekstijl", touw="zak", gras=("gras",),
        spanten=[("x", np.arange(-2.75, 1.0, 0.5), (-1.4, 2.7), 0.09, 0.08),
                 ("y", np.arange(-2.5, -0.6, 0.5), (0.6, 3.3), 0.09, 0.08),
                 ("y", (-0.3, 0.65, 1.6), (-3.3, 1.1), 0.08, 0.08),
                 ("x", (1.5, 2.0, 2.5), (-2.7, -0.6), 0.08, 0.08)],
    ),
    "melkerij_boerderij": dict(
        z2=0.7, dik=0.06, standaard=("auto", "heel"),
        rollen={**{n: WEG for n in ("rietschil", "rietschil_heup", "bloembak", "aarde", "blad", "bloem", "varken",
                                     "kapeldak", "kapelnok", "kapelkern", "kapelraam", "kapelstijl", "schoorsteenmond")},
                "binnen": ("hol", "heel"), "schoorsteenkern": ("weg", "snij@3.5"),
                "gras": ("heel", "heel"), "voetgras": ("heel", "heel")},
        gebied={"schoorsteen": ((-0.9, 1.15, 2.1), (0.9, 2.9, 6.0), ("weg", "steen@3.5")),
                "dakkapel": ((0.3, -2.8, 2.5), (2.4, -0.8, 6.0), WEG)},
        voet=[(-1.85, -2.9), (1.85, -2.9), (1.85, 2.9), (-1.85, 2.9)], marge=0.3,
        dak=("rietschil", "rietschil_heup"), sjabloon="stijl", touw="muurplank", gras=("gras",),
        spanten=[("y", np.arange(-3.0, 3.1, 0.5), (-2.3, 2.3), 0.1, 0.09),
                 ("x", (-1.55, -0.85, 0.0, 0.85, 1.55), (-3.3, 3.3), 0.09, 0.09)],
    ),
    "kippenhok": dict(
        z2=None, dik=0.04, standaard=("weg", "heel"),
        rollen={**{n: WEG for n in ("rietschil", "ei", "korrel", "binnen")},
                **{n: ("heel", "heel") for n in ("steen", "voetkern", "hoekstijl", "dakregel", "gevelstijl",
                                                  "kozijn", "latei", "strogrond", "takje")}},
        voet=[(-0.1, -0.08), (0.79, -0.08), (0.79, 0.8), (-0.1, 0.8)], marge=0.14, paal=0.28,
        dak=("rietschil",), sjabloon="hoekstijl", touw="plank", gras=(), spanten_in=(2, 3),
        spanten=[("x", (-0.18, 0.12, 0.42, 0.72), (-0.4, 1.1), 0.035, 0.03),
                 ("y", (0.0, 0.36, 0.72), (-0.35, 1.0), 0.03, 0.03)],
    ),
}
C = CFG[NAAM]


def basis(naam):
    return re.sub(r"[._]?\d+$", "", naam)


# --- Namen van de eilanden ---------------------------------------------------------------------------
def bron_dozen():
    """bbox (wereld) van elk bronobject in <naam>.blend, met zijn basisnaam."""
    bpy.ops.wm.open_mainfile(filepath=os.path.join(HERE, f"{NAAM}.blend"))
    dg = bpy.context.evaluated_depsgraph_get()
    D = []
    for o in bpy.context.scene.objects:
        if o.type != "MESH" or o.get("rt") == "weg" or o.get("lod1") or o.name.startswith("l1_") or o.name == "vanger":
            continue
        me = o.evaluated_get(dg).to_mesh()
        co = np.zeros(len(me.vertices) * 3, np.float32)
        me.vertices.foreach_get("co", co)
        o.evaluated_get(dg).to_mesh_clear()
        if not len(co):
            continue
        co = co.reshape(-1, 3) @ np.array(o.matrix_world)[:3, :3].T + np.array(o.matrix_world)[:3, 3]
        D.append((basis(o.name), co.min(0), co.max(0)))
    L.log("bronobjecten", len(D))
    return D


def benoem(bron, D, tol=0.04):
    """Elk eiland de naam van het bronobject dat het omvat en het best past (som van de bbox-verschillen)."""
    lo_D = np.array([d[1] for d in D])
    hi_D = np.array([d[2] for d in D])
    for e in bron.eil:
        lo, hi = np.array(e["lo"][:]), np.array(e["hi"][:])
        past = np.all(lo_D <= lo + tol, 1) & np.all(hi_D >= hi - tol, 1)
        score = np.abs(lo_D - lo).sum(1) + np.abs(hi_D - hi).sum(1)
        score = np.where(past, score, score + 100)
        e["naam"] = D[int(score.argmin())][0]


# --- Doen per eiland -----------------------------------------------------------------------------
def actie(e, s):
    """Wat er in stand s met eiland e gebeurt: (soort, hoogte)."""
    a = C["rollen"].get(e["naam"], C["standaard"])[s - 2]
    for lo, hi, aa in C.get("gebied", {}).values():       # losse stenen in een gebied (schoorsteen)
        if e["naam"] == "steen" and L.in_doos(e["c"], (Vector(lo), Vector(hi))):
            a = aa[s - 2]
    z = C["z2"] if s == 2 else None
    if "@" in a:
        a, z = a.split("@")[0], float(a.split("@")[1])
    if a in ("auto", "steen", "snij", "hol") and z is None:
        return "heel", None
    if a == "auto":
        ext = e["hi"] - e["lo"]
        a = "steen" if ext.z < 0.4 and max(ext.x, ext.y) < 0.7 else "snij"
    return a, z


def deur_dozen(ob):
    """Deuropeningen: bbox van de meshes onder elk scharnier (behalve de wieken), dwars op het blad verlengd."""
    dozen = []
    for d in ob:
        if d.type != "EMPTY" or "dicht" not in d:
            continue
        kids = [k for k in d.children_recursive if k.type == "MESH" and "lod1" not in k.name]
        if not kids:
            continue
        P = np.array([k.matrix_world @ Vector(c) for k in kids for c in k.bound_box])
        lo, hi = P.min(0), P.max(0)
        dun = int(np.argmin((hi - lo)[:2]))
        lo[dun] -= 0.5
        hi[dun] += 0.5
        lo[2] = -0.2
        dozen.append((Vector(lo), Vector(hi)))
    return dozen


def stuk(dst, bron, e, a, z, dozen):
    """Een eiland volgens zijn actie in dst."""
    rek = C.get("rek", {}).get(e["naam"])
    f = (lambda co: Vector((co.x, co.y, z1 if co.z < z0 else co.z))) if rek else None
    if rek:
        z0, z1 = rek
    if a == "heel":
        L.kopie(dst, bron, e["f"], f)
        return
    if a == "steen":
        if e["c"].z < z and not any(L.in_doos(e["c"], d) for d in dozen):
            t = bmesh.new()
            L.kopie(t, bron, e["f"], f)
            L.sluit(t)
            L.bovenkant_licht(t, z - 0.3)
            L.voeg(dst, t)
        return
    if e["lo"].z >= z:
        return
    t = bmesh.new()
    L.kopie(t, bron, e["f"], f)
    if a == "hol":
        L.hol(t, z, C["dik"], dozen)
    else:
        L.snij(t, z, dicht=True)
        if dozen and any(L.in_doos(e["c"], (lo - Vector((0.3, 0.3, 0)), hi + Vector((0.3, 0.3, 0)))) for lo, hi in dozen):
            L.gaten(t, dozen)
    L.voeg(dst, t)


# --- Dakgeraamte -------------------------------------------------------------------------------------
def doorsnede(dak_bm, as_, pos, bereik):
    """Lijn langs de onderkant van het dak in het vlak <as_> = pos: per 8 cm de laagste snijpunt-z."""
    t = dak_bm.copy()
    no = (1, 0, 0) if as_ == "x" else (0, 1, 0)
    co = (pos, 0, 0) if as_ == "x" else (0, pos, 0)
    r = bmesh.ops.bisect_plane(t, geom=t.verts[:] + t.edges[:] + t.faces[:], plane_co=co, plane_no=no)
    u_i = 1 if as_ == "x" else 0
    pts = [v.co.copy() for v in r["geom_cut"] if isinstance(v, bmesh.types.BMVert)]
    t.free()
    bak = {}
    for p in pts:
        if bereik[0] <= p[u_i] <= bereik[1]:
            k = int(math.floor(p[u_i] / 0.08))
            if k not in bak or p.z < bak[k].z:
                bak[k] = p
    ks = sorted(bak)
    lijnen, cur = [], []
    for k in ks:
        if cur and k - cur[-1][0] > 3:
            lijnen.append(cur)
            cur = []
        cur.append((k, bak[k]))
    if cur:
        lijnen.append(cur)
    out = []
    for ln in lijnen:
        P = [p for _, p in ln]
        if len(P) < 4:
            continue
        stap = max(1, len(P) // max(2, round((P[-1] - P[0]).length / 0.45)))
        Q = P[::stap]
        if Q[-1] is not P[-1]:
            Q.append(P[-1])
        out.append(Q)
    return out


def geraamte(dst, sjab, dak_bm):
    n = 0
    for as_, posities, bereik, w, d in C["spanten"]:
        for pos in posities:
            for Q in doorsnede(dak_bm, as_, float(pos), bereik):
                Q = [q - Vector((0, 0, d * 0.6 + 0.02)) for q in Q]
                for a, b in zip(Q, Q[1:]):
                    rich = (b - a).normalized()
                    sjab.balk(dst, a - rich * 0.03, b + rich * 0.03, w, d)
                    n += 1
    return n


# --- Bouwen ------------------------------------------------------------------------------------------
def bouw():
    D = bron_dozen()
    bpy.ops.wm.open_mainfile(filepath=os.path.join(HERE, f"{NAAM}_rt.blend"))
    sc = bpy.context.scene
    ob = bpy.data.objects
    ankers = [o for o in ob if o.type == "EMPTY"]
    scharnier_kids = {k for a in ankers for k in a.children_recursive}
    rt = [o for o in ob if o.type == "MESH" and "lod1" not in o.name and not o.name.endswith("_buis")
          and o not in scharnier_kids and o.data.uv_layers]
    af = tris([o for o in ob if o.type == "MESH" and "lod1" not in o.name and not o.name.endswith("_buis")])
    dozen = deur_dozen(ob)
    L.log("rt-meshes", [o.name for o in rt], "deuren", len(dozen))
    B = []
    for o in rt:
        b = L.Bron(o)
        benoem(b, D)
        tel = {}
        for e in b.eil:
            tel[e["naam"]] = tel.get(e["naam"], 0) + 1
        L.log(o.name, len(b.eil), "eilanden", dict(sorted(tel.items())))
        B.append((o.name, b))
    alle = [e for _, b in B for e in b.eil]
    sj_e = max((e for e in alle if e["naam"] == C["sjabloon"]), key=lambda e: (e["hi"] - e["lo"]).length)
    sj_b = next(b for _, b in B if sj_e in b.eil)
    sjab = L.Sjabloon(sj_b, sj_e)
    t_e = [e for e in alle if e["naam"] == C["touw"]]
    t_b = next(b for _, b in B if t_e[0] in b.eil)
    touw_uv = t_e[0]["f"][len(t_e[0]["f"]) // 2].loops[0][t_b.uv].uv.copy()
    dak_bm = bmesh.new()
    for _, b in B:
        for e in b.eil:
            if e["naam"] in C["dak"]:
                L.kopie(dak_bm, b, e["f"])
    for o in list(ob):
        if o.type == "MESH":
            o.name = "_bron_" + o.name
            o.hide_set(True)
            o.hide_render = True
    sd = L.veelhoek_sd(C["voet"], 0.15)
    stat = {}
    for s in STANDEN:
        coll = bpy.data.collections.new(f"stand{s}")
        sc.collection.children.link(coll)
        objs = []
        per = {naam: bmesh.new() for naam, _ in B}
        hout = per[next(n for n, b in B if b is sj_b)]
        hout_t = per[next(n for n, b in B if b is t_b)]
        if s == 1:
            xs = np.arange(min(p[0] for p in C["voet"]) - 0.6, max(p[0] for p in C["voet"]) + 0.6, 0.12)
            ys = np.arange(min(p[1] for p in C["voet"]) - 0.6, max(p[1] for p in C["voet"]) + 0.6, 0.12)
            objs.append(L.aarde(coll, sd, xs, ys, rij_vast=True))
            rnd = random.Random(40)
            hoog = C.get("paal", 0.45)
            P = L.uitzetten(C["voet"], C["marge"], per_m=1.1 if hoog > 0.3 else 3.0)
            dw = hoog / 0.45
            for p in P:
                q = p + Vector((rnd.uniform(-0.02, 0.02), rnd.uniform(-0.02, 0.02), 0)) * dw
                sjab.balk(hout, q + Vector((0, 0, -0.1 * dw)),
                          q + Vector((rnd.uniform(-0.02, 0.02) * dw, rnd.uniform(-0.02, 0.02) * dw, hoog)),
                          0.055 * dw, 0.05 * dw, rol=rnd.uniform(0, 3))
            for a, c in zip(P, P[1:] + P[:1]):
                pts = [a.lerp(c, t) + Vector((0, 0, hoog * 0.8 - 0.03 * dw * math.sin(math.pi * t)))
                       for t in np.linspace(0, 1, 6)]
                L.touw(hout_t, pts, touw_uv, r=0.012 * max(dw, 0.6))
            for naam, b in B:
                for e in b.eil:
                    if e["naam"] in C["gras"] and sd(e["c"].x, e["c"].y) < 0:
                        L.kopie(per[naam], b, e["f"])
        else:
            for naam, b in B:
                for e in b.eil:
                    a, z = actie(e, s)
                    if a != "weg":
                        stuk(per[naam], b, e, a, z, dozen)
            if s in C.get("spanten_in", (3,)):
                L.log("stand", s, "balken in het dakgeraamte", geraamte(hout, sjab, dak_bm))
        for naam, b in B:
            bm = per[naam]
            if len(bm.faces):
                o = L.naar_obj(naam, bm, b.mat, coll)
                o.data.set_sharp_from_angle(angle=math.radians(40))
                objs.append(o)
            bm.free()
        for o in objs:
            L.log("   ", s, o.name, tris([o]))
        L.exporteer(GLB(s), objs + ankers)
        stat[s] = tris(objs)
        for o in objs:
            bpy.data.objects.remove(o)
    L.log("driehoeken", stat, "af", af)


tris = L.tris


def preview():
    L.plaat(os.path.join(HERE, f"{NAAM}.blend"), [GLB(1), GLB(2), GLB(3), os.path.join(HERE, f"{NAAM}_rt.glb")],
            os.path.join(os.path.dirname(HERE), "render", f"{NAAM}_standen.png"), weg_namen=("vanger",),
            procent=int(OPTS.get("procent", 50)))


if __name__ == "__main__":
    if "alleen_preview" not in OPTS:
        bouw()
    if "preview" in OPTS or "alleen_preview" in OPTS:
        preview()
    L.log("KLAAR")
