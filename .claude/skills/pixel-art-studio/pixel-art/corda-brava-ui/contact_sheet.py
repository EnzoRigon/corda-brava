"""Contact sheet: every exported asset at 4x on a dark background (reads frontend/src/assets/ui)."""
import os
from PIL import Image
from pal import OUT, HERE
S = 4
def L(n): return Image.open(os.path.join(OUT, n)).convert("RGBA")
rows = [
 ["logo-160x56.png", "logo-small-96x36.png"],
 [f"icon-{k}.png" for k in "heart star trophy crown lightning hourglass speaker-on speaker-off".split()],
 [f"icon-{k}.png" for k in "arrow-left check cross player whistle rope-coil pennant-red pennant-blue".split()],
 ["fx-sparkle-strip-6f-8px.png", "fx-dust-strip-5f-12px.png", "fx-confetti-sheet-4x2-4px.png"],
 ["bg-sky-tile-64.png", "bg-moon-32.png", "bg-cloud-a-48x16.png", "bg-cloud-b-48x16.png", "bg-pitch-strip-32x24.png"],
 ["bg-stadium-strip-128x48.png"],
]
pad = 6
ims = [[L(n) for n in r] for r in rows]
W = max(sum(i.width + pad for i in r) for r in ims) + pad
H = sum(max(i.height for i in r) + pad for r in ims) + pad
sheet = Image.new("RGBA", (W, H), (22, 26, 58, 255))
y = pad
for r in ims:
    x = pad
    for im in r:
        sheet.alpha_composite(im, (x, y)); x += im.width + pad
    y += max(i.height for i in r) + pad
sheet.resize((W * S, H * S), Image.NEAREST).save(os.path.join(HERE, "contact-sheet.png"))
print(W, H)
