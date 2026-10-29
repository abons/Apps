"""Sprite (nearest opgeschaald) | render | concept naast elkaar, op grijs, zelfde hoogte.
Aanpassing van ../vergelijk.py voor de gebouwen met een concept erbij.

  python vergelijk_loods_molen.py <sprite.png> <render.png> <uit.png> [concept.jpg] [overlay]
`overlay` legt de render half doorzichtig over de sprite als vierde paneel (pasvorm).
"""
import sys

from PIL import Image

sprite, render, uit = sys.argv[1:4]
concept = sys.argv[4] if len(sys.argv) > 4 and sys.argv[4] != "-" else None
overlay = "overlay" in sys.argv
bg = (200, 200, 200, 255)
r = Image.open(render).convert("RGBA")
o = Image.open(sprite).convert("RGBA").resize(r.size, Image.NEAREST)


def op_grijs(im):
    b = Image.new("RGBA", im.size, bg)
    b.alpha_composite(im)
    return b


panelen = [op_grijs(o), op_grijs(r)]
if overlay:
    m = op_grijs(o)
    rr = r.copy()
    rr.putalpha(rr.getchannel("A").point(lambda a: a * 0.55))
    m.alpha_composite(rr)
    panelen.append(m)
if concept:
    c = Image.open(concept).convert("RGBA")
    c = c.resize((int(c.width * r.height / c.height), r.height), Image.LANCZOS)
    panelen.append(op_grijs(c))
W = sum(p.width for p in panelen) + 10 * (len(panelen) - 1)
s = Image.new("RGBA", (W, r.height), bg)
x = 0
for p in panelen:
    s.alpha_composite(p, (x, 0))
    x += p.width + 10
s.convert("RGB").save(uit)
