import sys, os, random
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from pal import *
from PIL import Image

# ---- night sky tile 64x64: wrapped dither haze + sparse stars (tiles both ways)
sky = sprite(64, 64); sky.rect(0, 0, 63, 63, C["n2"])
rnd = random.Random(7)
for _ in range(5):   # soft wrapped haze patches, checker-dithered n3
    cx, cy, rx, ry = rnd.randrange(64), rnd.randrange(64), rnd.randrange(5, 9), rnd.randrange(2, 4)
    for y in range(-ry, ry + 1):
        for x in range(-rx, rx + 1):
            if (x / rx) ** 2 + (y / ry) ** 2 <= 1 and (x + y) % 2 == 0:
                sky.px((cx + x) % 64, (cy + y) % 64, C["n3"])
for i in range(26):  # dim 1px stars
    x, y = rnd.randrange(64), rnd.randrange(64)
    sky.px(x, y, C["n5"] if i % 3 else C["a"])
for x, y in [(9, 12), (41, 7), (27, 38), (55, 50), (14, 55)]:  # bright plus stars
    sky.px(x, y, C["W"])
    for dx, dy in [(1, 0), (-1, 0), (0, 1), (0, -1)]: sky.px((x + dx) % 64, (y + dy) % 64, C["n5"])
save(sky, "bg-sky-tile-64.png")

# ---- moon 32x32 with dithered glow (glow = translucent cream so it sits on any sky)
moon = Sprite(32, 32, snap=False)
for y in range(32):
    for x in range(32):
        d = ((x - 15.5) ** 2 + (y - 15.5) ** 2) ** .5
        if 9.5 < d <= 15.5 and ((x + y) % 2 == 0 if d < 12.5 else (x % 2 == 0 and y % 2 == 0)) :
            moon.px(x, y, (255, 248, 224, 70 if d < 12.5 else 44))
moon.circle(15, 15, 9, C["o"], fill=True)
moon.circle(15, 15, 9, "#a8a2c0", fill=True)
moon.circle(14, 14, 8, C["W"], fill=True)
for x, y, r in [(18, 11, 2), (12, 18, 2), (19, 19, 1), (11, 12, 1)]:
    moon.circle(x, y, r, "#d9d2ee", fill=True, only=C["W"])
moon.px(16, 10, "#d9d2ee"); moon.px(13, 20, "#d9d2ee")
moon.ellipse(8, 18, 18, 24, "#c9c2e4", only=C["W"]) if False else None
save(moon, "bg-moon-32.png")

# ---- clouds 48x16 (night-lit: top rim lighter, flat belly)
def cloud(blobs, name):
    s = sprite(48, 16)
    for x0, y0, x1, y1 in blobs: s.ellipse(x0, y0, x1, y1, C["n4"])
    s.rect(0, 12, 47, 15, None)
    # belly shadow, then top rim highlight (shifted-shape recipe)
    s.rect(0, 10, 47, 11, C["n3"], only=C["n4"])
    top = sprite(48, 16)
    for x0, y0, x1, y1 in blobs: top.ellipse(x0, y0 + 2, x1, y1 + 2, C["n4"])
    for y in range(16):
        for x in range(48):
            a = s.get(x, y); b = top.get(x, y)
            if a and a[3] and not (b and b[3]): s.px(x, y, C["n5"])
    s.rect(0, 12, 47, 15, None)
    save(s, name); return s
c1 = cloud([(4, 6, 20, 14), (14, 2, 30, 13), (26, 5, 44, 14)], "bg-cloud-a-48x16.png")
c2 = cloud([(2, 8, 14, 14), (10, 4, 24, 13), (20, 7, 34, 14), (30, 6, 46, 13)], "bg-cloud-b-48x16.png")

# ---- stadium strip 128x48 (tileable horizontally; towers at x=24 and 88, edges equal height)
st = sprite(128, 48)
roof = 26
st.rect(0, roof, 127, 47, C["n1"])
st.rect(0, roof - 3, 127, roof, C["Z"]); st.rect(0, roof - 3, 127, roof - 3, C["z"])  # canopy
for x in range(0, 128, 8):                     # canopy struts
    st.rect(x, roof - 5, x, roof - 4, C["Z"])
st.rect(0, roof - 5, 127, roof - 4, C["Z"]) if False else None
st.rect(0, roof + 8, 127, roof + 8, C["Z"])    # stand tiers
st.rect(0, roof + 16, 127, roof + 16, C["Z"])
rnd = random.Random(3)
crowd = [C["r"], C["b"], C["a"], C["n5"], C["O"]]
for tier in (roof + 3, roof + 11, roof + 19):  # tiny crowd dots (dim: it's a silhouette)
    for x in range(1, 127, 3):
        if rnd.random() < .7: st.px(x + rnd.randrange(2), tier + rnd.randrange(2), rnd.choice(crowd))
for tx in (24, 88):                            # floodlight towers
    st.rect(tx - 1, 8, tx, roof, C["Z"]); st.rect(tx, 8, tx, roof, C["z"]); st.rect(tx - 3, 20, tx + 2, 20, C["Z"])
    st.rect(tx - 8, 1, tx + 7, 7, C["Z"]); st.rect(tx - 8, 1, tx + 7, 1, C["z"])
    for row in range(2):
        for col in range(4):
            lx, ly = tx - 7 + col * 4, 2 + row * 3
            st.rect(lx, ly, lx + 2, ly + 1, C["W"]); st.px(lx, ly, "#ffffff"); st.px(lx + 2, ly + 1, C["Y"])
    # light halo: dithered, only on empty pixels above the roof line
    for y in range(-3, 13):
        for x in range(-13, 13):
            d = (x * x / 1.6 + (y - 3) ** 2)
            if d < 200 and (x + y) % 2 == 0 and (d < 110 or x % 2 == 0) and tx + x >= 0:
                if not (st.get(tx + x, y + 3 - 0) or (0, 0, 0, 0))[3] and 0 <= y + 3 < roof and (tx + x) < 128:
                    st.px(tx + x, y + 3, (255, 240, 180, 38 if d > 70 else 66))
save(st, "bg-stadium-strip-128x48.png")

# ---- pitch strip 32x24: two mow bands (16px each -> tileable), chalk line, tufts, darker foreground
p = sprite(32, 24)
p.rect(0, 0, 15, 23, C["e"]); p.rect(16, 0, 31, 23, C["M"])   # mow bands (16px each -> tileable)
rnd = random.Random(11)
for _ in range(40):                           # grass tufts, lighter than own band
    x, y = rnd.randrange(32), rnd.randrange(24)
    p.px(x, y, C["M"] if x < 16 else C["E"])
    if rnd.random() < .5: p.px(x, y - 1, C["M"] if x < 16 else C["E"])
for y in range(18, 24):                       # foreground falls into shade (dither then solid)
    for x in range(32):
        if y >= 22 or (x + y) % 2 == 0 and y >= 20: p.px(x, y, C["N"])
p.rect(0, 6, 31, 7, C["W"])                   # chalk line
for x in range(0, 32, 4): p.px(x, 5, C["W"])  # chalk spray above, below
for x in range(2, 32, 4): p.px(x, 8, C["A"])
save(p, "bg-pitch-strip-32x24.png")

# ---- preview: sky tiled 2x2 + moon + clouds + stadium x2 + pitch tiles
pv = Image.new("RGBA", (256, 176), (0, 0, 0, 255))
sk = sky.composite()
for i in range(4):
    for j in range(3): pv.paste(sk, (i * 64, j * 64))
pv.alpha_composite(moon.composite(), (190, 8))
pv.alpha_composite(c1.composite(), (10, 18)); pv.alpha_composite(c2.composite(), (120, 40))
for i in range(2): pv.alpha_composite(st.composite(), (i * 128, 90 - 48 + 24))
for i in range(8): pv.paste(p.composite(), (i * 32, 152))
pv.crop((0, 0, 256, 176)).resize((256 * 5, 176 * 5), Image.NEAREST).save(os.path.join(HERE, "scenery", "preview.png"))
