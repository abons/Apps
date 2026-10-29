"""Drieluik voor de iteratie (naar ../vergelijk.py): origineel (opgeschaald, nearest) | render | concept.
python vergelijk_erf.py <origineel.png> <render.png> <uit.png> [concept.jpg] [crop=x0,y0,x1,y1] [padtop=N]"""
import sys

from PIL import Image

opts = [a for a in sys.argv[1:] if "=" in a and a.split("=")[0] in ("padtop",)]
sys.argv = [a for a in sys.argv if a not in opts]
pad = int(opts[0].split("=")[1]) if opts else 0          # canvas boven aanvullen (in pixels van het origineel)
o = Image.open(sys.argv[1]).convert("RGBA")
if pad:
    o2 = Image.new("RGBA", (o.width, o.height + pad), (0, 0, 0, 0))
    o2.alpha_composite(o, (0, pad))
    o = o2
r = Image.open(sys.argv[2]).convert("RGBA")
o = o.resize(r.size, Image.NEAREST)
bg = (200, 200, 200, 255)
delen = [o, r]
if len(sys.argv) > 4:
    c = Image.open(sys.argv[4]).convert("RGBA")
    if len(sys.argv) > 5:
        c = c.crop(tuple(int(v) for v in sys.argv[5].split(",")))
    c = c.resize((int(c.width * r.height / c.height), r.height), Image.LANCZOS)
    delen.append(c)
s = Image.new("RGBA", (sum(d.width for d in delen) + 10 * (len(delen) - 1), r.height), bg)
x = 0
for d in delen:
    s.alpha_composite(d, (x, 0))
    x += d.width + 10
s.convert("RGB").save(sys.argv[3])
