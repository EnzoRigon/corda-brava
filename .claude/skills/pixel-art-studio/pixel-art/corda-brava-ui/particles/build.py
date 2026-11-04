import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from pal import *
from PIL import Image

SPARK = [
 ["........","........","........","...YY...","...YY...","........","........","........"],
 ["........","........","...YY...","..YWWY..","..YWWY..","...YY...","........","........"],
 ["...GG...","...YY...","..YWWY..","GYWWWWYG","GYWWWWYG","..YWWY..","...YY...","...GG..."],
 ["........","...GG...","..GYYG..","..GYYG..","...GG...","........","........","........"],
 ["........","........","...GG...","..G..G..","..G..G..","...GG...","........","........"],
 ["........","........","........","...G....","....G...","........","........","........"],
]
sparks = [from_ascii(f, 8, 8) for f in SPARK]
strip(sparks, "fx-sparkle-strip-6f-8px.png")

DUST = [
 ["....WW......","...WWWW.....","...WWWWA....","...WWAAAa...","....AAaa...."],
 [".....WW.....","..WW.WWWW...",".WWWWWWWWA..",".WWWWWWWAA..","WWWWWAAAAAa.",".AAAAAAAAa..","..aaaaaaa..."],
 ["..WW....WW..",".WWWW..WWWW.","WWWWWA.WWWAA","WWWAAA.AAAAa",".AAAAAaAAAa.","..aaaaaaaa.."],
 [".AA......AA.","AAAA....AAAa","AAaA.AA.AaAa",".Aa.AAAA.aa.","..a.AaAa.a..",".....aa....."],
 [".A.........A","....A..A....","..a.....a...",".........a..","a..a.A......"],
]
dust = []
for rows in DUST:                      # bottom-align inside 12x12
    rows = [r.ljust(12, ".") for r in rows]
    dust.append(from_ascii(["." * 12] * (12 - len(rows)) + rows, 12, 12))
strip(dust, "fx-dust-strip-5f-12px.png")

CONF = [
 ["RR.R","Rrr.","...."], ["BB..","bB..","b..."],
]
PIECES = [  # (name, 4x4 rows) flat row then tilted row
 (["RRRR","rrrr"], ["RR..","RRr.",".rRR","..rr"]),
 (["BB","BB","bb","bb"], ["..BB","BBBb","bb..", "...."]),
 (["YYYY","GGGG"], [".YY.","YYG.",".GGY","..GG"]),
 (["WWWW","AAAA"], ["WW..","WWA.",".AWW","..AA"]),
]
sh = sprite(16, 8)
for i, (flat, tilt) in enumerate(PIECES):
    for rows, oy in ((flat, 0), (tilt, 4)):
        h = len(rows)
        for y, r in enumerate(rows):
            for x, ch in enumerate(r):
                if ch != ".": sh.px(i * 4 + x + (4 - len(r)) // 2, oy + y + (4 - h) // 2, C[ch])
save(sh, "fx-confetti-sheet-4x2-4px.png")

pv = Image.new("RGBA", (6 * 8 + 5 * 12 + 16 + 40, 14), (28, 34, 80, 255))
x = 2
for f in sparks: pv.alpha_composite(f.composite(), (x, 3)); x += 8
x += 4
for f in dust: pv.alpha_composite(f.composite(), (x, 1)); x += 12
pv.alpha_composite(sh.composite(), (x + 4, 3))
pv.resize((pv.width * 10, pv.height * 10), Image.NEAREST).save(os.path.join(HERE, "particles", "preview.png"))
