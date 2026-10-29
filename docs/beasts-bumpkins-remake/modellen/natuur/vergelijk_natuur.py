"""Zet concept | origineel (nearest, x4) | renders naast elkaar: python vergelijk_natuur.py <groep> <uit.png>

Concept- en spritepaden komen uit NATUUR_CONCEPT en NATUUR_SPRITES (scratchpad van de conceptronde);
renders uit NATUUR_TMP (v_<item>.png van voorbeeld.py). Elke rij = een asset."""
import os
import sys

from PIL import Image, ImageDraw

CON = os.environ["NATUUR_CONCEPT"]
SPR = os.environ["NATUUR_SPRITES"]
TMP = os.environ["NATUUR_TMP"]
BG = (96, 112, 88)

# asset: (concept, (x0, y0, x1, y1) in originele pixels, sprite of None, [renders])
RIJEN = {
    "bomen": [
        ("den_groot", "dennen_sheet.jpg", (150, 30, 500, 630), "bigfir", ["den_groot", "den_groot_sneeuw", "den_groot_lod1"]),
        ("spar", "dennen_sheet.jpg", (700, 150, 900, 490), "tree10", ["spar", "spar_sneeuw", "spar_lod1"]),
        ("jonge_den", "dennen_sheet.jpg", (1050, 250, 1160, 425), "sap_fir", ["jonge_den", "jonge_den_lod1"]),
        ("stronk", "loofbomen_struiken.jpg", None, "stump", ["stronk"]),
        ("loofboom", "loofbomen_struiken.jpg", (1180, 40, 1450, 405), "tree03", ["loofboom", "loofboom_sneeuw", "loofboom_lod1"]),
        ("loofboom_jong", "loofbomen_struiken.jpg", (750, 120, 885, 360), "tree02", ["loofboom_jong", "loofboom_jong_lod1"]),
        ("struik_bloem", "loofbomen_struiken.jpg", (1515, 130, 1830, 365), None, ["struik_bloem", "struik_bloem_lod1"]),
        ("struik_klein", "loofbomen_struiken.jpg", (1900, 180, 2050, 320), None, ["struik_klein", "struik_klein_lod1"]),
    ],
    "rotsen": [
        ("rots_1", "rotsen_sheet.jpg", (25, 25, 475, 395), "rock01", ["rots_1", "rots_1_lod1"]),
        ("rots_2", "rotsen_sheet.jpg", (510, 25, 836, 395), "rock02", ["rots_2"]),
        ("rots_3", "rotsen_sheet.jpg", (880, 40, 1180, 395), "rock03", ["rots_3"]),
        ("rots_4", "rotsen_sheet.jpg", (1230, 25, 1575, 395), "rock04", ["rots_4", "rots_4_lod1"]),
        ("rots_5", "rotsen_sheet.jpg", (1648, 70, 1968, 395), "rock05", ["rots_5"]),
        ("rots_6", "rotsen_sheet.jpg", (2017, 70, 2325, 395), "rock06", ["rots_6"]),
        ("klif", "rotsrand_klif.jpg", (0, 0, 1232, 864), "rockrim", ["klif_recht", "klif_hoek_buiten", "klif_hoek_binnen", "klif_rij"]),
    ],
    "props": [
        ("zilveren_beker", "kaartprops.jpg", (100, 55, 400, 635), "gob_silv", ["zilveren_beker"]),
        ("vlag", "kaartprops.jpg", (550, 50, 910, 620), "flag", ["vlag"]),
        ("paddenstoel", "kaartprops.jpg", (985, 80, 1500, 600), None, ["paddenstoel"]),
        ("kampvuur", "dorpsprops.jpg", (55, 20, 230, 445), "campfire", ["kampvuur"]),
        ("houtstapel", "dorpsprops.jpg", (285, 115, 860, 535), "logs", ["houtstapel"]),
        ("steenhoop", "dorpsprops.jpg", (890, 35, 1710, 570), None, ["steenhoop"]),
        ("bron", "waterput.jpg", (0, 0, 1122, 945), "well", ["bron"]),
        ("hek_paal", "hek_muur_poort.jpg", (55, 115, 390, 365), "fence", ["hek_paal"]),
        ("hek_segment", "hek_muur_poort.jpg", (1245, 104, 1495, 348), "gate", ["hek_segment", "hek_rij"]),
        ("poort", "hek_muur_poort.jpg", (1600, 43, 2068, 415), None, ["poort"]),
        ("akker_kaal", "akker.jpg", (40, 170, 830, 620), "crops", ["akker_kaal"]),
        ("akker_rijp", "akker.jpg", (860, 30, 1620, 630), "wheat", ["akker_rijp"]),
    ],
}
STRONK_CROP = ("dennen_sheet.jpg", (1195, 270, 1450, 440))


def paneel(im, h):
    im = im.convert("RGBA")
    s = h / im.height
    return im.resize((max(1, int(im.width * s)), h), Image.LANCZOS)


def sprite(naam, h):
    im = Image.open(os.path.join(SPR, naam + ".png")).convert("RGBA")
    k = max(1, min(4, h // im.height))
    return im.resize((im.width * k, im.height * k), Image.NEAREST)


def bouw(groep, uit, H=360):
    rijen = []
    for naam, con, box, spr, renders in RIJEN[groep]:
        if naam == "stronk":
            con, box = STRONK_CROP
        panelen = []
        if box:
            panelen.append(("concept", paneel(Image.open(os.path.join(CON, con)).crop(box), H)))
        if spr:
            panelen.append(("origineel", sprite(spr, H)))
        for r in renders:
            p = os.path.join(TMP, f"v_{r}.png")
            if os.path.exists(p):
                im = Image.open(p).convert("RGBA")
                if im.height > H:
                    im = paneel(im, H)
                panelen.append((r, im))
        if not any(l not in ("concept", "origineel") for l, _ in panelen):
            continue
        w = sum(p[1].width for p in panelen) + 12 * (len(panelen) + 1)
        rij = Image.new("RGBA", (w, H + 26), BG + (255,))
        d = ImageDraw.Draw(rij)
        x = 12
        for lab, im in panelen:
            rij.alpha_composite(im, (x, 22 + H - im.height))
            d.text((x, 4), lab, fill=(255, 255, 210))
            x += im.width + 12
        rijen.append(rij)
    W = max(r.width for r in rijen)
    out = Image.new("RGB", (W, sum(r.height for r in rijen)), BG)
    y = 0
    for r in rijen:
        out.paste(r.convert("RGB"), (0, y))
        y += r.height
    out.save(uit)
    print("->", uit, out.size)


if __name__ == "__main__":
    bouw(sys.argv[1], sys.argv[2], H=int(sys.argv[3]) if len(sys.argv) > 3 else 360)
