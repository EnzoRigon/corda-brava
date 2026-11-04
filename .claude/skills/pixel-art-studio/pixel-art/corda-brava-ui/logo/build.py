import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from pal import *
from PIL import Image

FONT = {  # original 5x7 chunky block face
 "C": [".###.","##.##","##...","##...","##...","##.##",".###."],
 "O": [".###.","##.##","##.##","##.##","##.##","##.##",".###."],
 "R": ["####.","##.##","##.##","####.","##.##","##.##","##.##"],
 "D": ["####.","##.##","##.##","##.##","##.##","##.##","####."],
 "A": [".###.","##.##","##.##","#####","##.##","##.##","##.##"],
 "B": ["####.","##.##","##.##","####.","##.##","##.##","####."],
 "V": ["##.##","##.##","##.##","##.##","##.##",".###.",".###."],
}

def word_mask(word, s, gap):
    px = set()
    for i, ch in enumerate(word):
        for y, row in enumerate(FONT[ch]):
            for x, c in enumerate(row):
                if c == "#":
                    for dy in range(s):
                        for dx in range(s): px.add((i * (5 * s + gap) + x * s + dx, y * s + dy))
    return px, len(word) * 5 * s + (len(word) - 1) * gap

def draw_word(sp, word, s, gap, cx, y0):
    m, w = word_mask(word, s, gap)
    ox = cx - w // 2
    H = 7 * s
    face = {(ox + x, y0 + y) for x, y in m}
    ext = s                                       # extrusion depth = drop shadow block
    for (x, y) in face:
        for k in range(1, ext + 1): sp.px(x, y + k, C["o"])
    for (x, y) in face:
        yr = y - y0
        col = C["G"]
        if yr < s: col = C["W"] if yr == 0 else C["Y"]   # highlight band across the top
        elif yr < 2 * s + 1: col = C["Y"]
        elif yr >= H - s: col = C["O"]                   # bevel: bottom
        if (x - 1, y) not in face and yr >= s: col = C["Y"]      # lit left edge
        if (x + 1, y) not in face and yr >= 2 * s and yr < H - s: col = C["G"]
        sp.px(x, y, col)
    return face

def rope(sp, x0, x1, y, h):
    for x in range(x0, x1 + 1):
        for k in range(h):
            col = C["T"] if ((x + k) // 2) % 2 == 0 else C["t"]
            if k == h - 1: col = C["o"]
            if k == 0: col = C["W"] if col == C["T"] else C["T"]   # top light
            sp.px(x, y + k, col)
    return

def make(W, H, s, gap, y1, yr, y2, rope_h, ribbons):
    sp = sprite(W, H)
    rope(sp, 0, W - 1, yr, rope_h)
    if ribbons:
        for x0, a, b in [(W // 2 - 44, "R", "r"), (W // 2 + 40, "B", "b")]:
            sp.rect(x0, yr, x0 + 2, yr + rope_h - 1, C[a]); sp.rect(x0, yr + rope_h - 1, x0 + 2, yr + rope_h - 1, C[b])
        sp.ellipse(W // 2 - 4, yr - 1, W // 2 + 3, yr + rope_h, C["T"])     # knot
        sp.ellipse(W // 2 - 4, yr + 2, W // 2 + 3, yr + rope_h, C["t"], only=C["T"])
    draw_word(sp, "CORDA", s, gap, W // 2, y1)
    draw_word(sp, "BRAVA", s, gap, W // 2, y2)
    sp.outline(C["K"], where="outside")
    return sp

big = make(160, 56, 3, 4, 1, 26, 31, 4, True)
small = make(96, 36, 2, 3, 1, 17, 20, 2, False)
save(big, "logo-160x56.png"); save(small, "logo-small-96x36.png")
pv = Image.new("RGBA", (200, 110), (18, 22, 58, 255))
pv.alpha_composite(big.composite(), (20, 4)); pv.alpha_composite(small.composite(), (52, 66))
pv.resize((200 * 6, 110 * 6), Image.NEAREST).save(os.path.join(HERE, "logo", "preview.png"))
