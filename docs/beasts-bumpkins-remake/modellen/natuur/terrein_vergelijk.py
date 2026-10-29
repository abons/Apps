"""Concept-vlak | onze textuur 2 x 2 herhaald (naadcontrole) | normaal: python terrein_vergelijk.py <uit.png>"""
import os
import sys

from PIL import Image, ImageDraw

HERE = os.path.dirname(os.path.abspath(__file__))
CON = os.path.join(os.environ["NATUUR_CONCEPT"], "terreintexturen.jpg")
VAK = {"gras": (15, 15, 412, 412), "bosgrond": (433, 15, 830, 412), "rots": (852, 15, 1249, 412),
       "zand": (15, 433, 412, 830), "water_rand": (433, 433, 830, 830)}
S = 300
out = Image.new("RGB", (S * 4 + 50, (S + 24) * len(VAK)), (60, 60, 60))
d = ImageDraw.Draw(out)
c = Image.open(CON).convert("RGB")
for i, (naam, box) in enumerate(VAK.items()):
    y = i * (S + 24) + 20
    out.paste(c.crop(box).resize((S, S)), (10, y))
    k = Image.open(os.path.join(HERE, "textures", f"terrein_{naam}_kleur.jpg")).convert("RGB").resize((S, S))
    t = Image.new("RGB", (S * 2, S * 2))
    for dx in (0, S):
        for dy in (0, S):
            t.paste(k, (dx, dy))
    out.paste(t.crop((0, S // 2, S * 2, S // 2 + S)), (S + 20, y))
    n = Image.open(os.path.join(HERE, "textures", f"terrein_{naam}_normaal.jpg")).convert("RGB").resize((S, S))
    out.paste(n, (S * 3 + 30, y))
    d.text((10, y - 16), f"{naam}: concept | 2x2 herhaald (naad in het midden) | normaal", fill=(255, 255, 200))
out.save(sys.argv[1])
print("->", sys.argv[1])
