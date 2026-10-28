"""Zet het origineel (opgeschaald, nearest) naast de render: python vergelijk.py <origineel.png> <render.png> <uit.png>"""
import sys
from PIL import Image
o = Image.open(sys.argv[1]).convert("RGBA")
r = Image.open(sys.argv[2]).convert("RGBA")
o = o.resize(r.size, Image.NEAREST)
bg = (200, 200, 200, 255)
s = Image.new("RGBA", (r.width * 2 + 10, r.height), bg)
s.alpha_composite(o, (0, 0))
s.alpha_composite(r, (r.width + 10, 0))
s.convert("RGB").save(sys.argv[3])
