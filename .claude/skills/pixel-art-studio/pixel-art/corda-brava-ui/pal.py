"""Shared palette + helpers for the Corda Brava UI asset pack (32-colour budget). Original art only."""
import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "scripts")))
from pixelstudio import Sprite

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.abspath(os.path.join(HERE, "..", "..", "..", "..", "..", "frontend", "src", "assets", "ui"))
os.makedirs(OUT, exist_ok=True)

C = dict(
    K="#141019", w="#ffffff",  # outline, white glint
    W="#fff8e0", Y="#ffe27a", G="#f2b632", O="#b8741a", o="#6e3f16",  # cream + gold ramp
    R="#e23b3b", r="#9c1f2e", q="#ff8a74",   # team red ramp
    B="#2f6fd0", b="#1b3f8c", l="#8cc4ff",   # team blue ramp
    A="#cdd3e2", a="#8790ad", d="#4a4f75",   # steel / slate
    E="#6cc65a", e="#2f8a46", g="#b4ec8a", M="#3fa04f", N="#256b3a",  # green ramp
    F="#e8b48a", f="#b9805e",                # skin
    T="#d9b36a", t="#a67c3a",                # rope
    n1="#0a0c22", n2="#12163a", n3="#1c2456", n4="#2c3778", n5="#4a58a0",  # night ramp
    Z="#2b2347", z="#3a3160",   # wood / stadium dark
)

def sprite(w, h):
    return Sprite(w, h, palette=list(C.values()) + ["#00000000"], snap=True)

def from_ascii(rows, w=16, h=16, remap=None):
    """rows may be narrower than w; the art is centred. '.' = transparent."""
    rows = [r.replace(" ", ".") for r in rows]
    mw = max(len(r) for r in rows)
    s = sprite(w, h)
    ox, oy = (w - mw) // 2, (h - len(rows)) // 2
    for y, r in enumerate(rows):
        r = r.ljust(mw, ".")
        for x, ch in enumerate(r):
            if remap: ch = remap.get(ch, ch)
            if ch != ".":
                s.px(ox + x, oy + y, C[ch])
    return s

def save(s, name, frame=None):
    s.save_png(os.path.join(OUT, name), frame=frame)

def strip(frames, name):
    """Compose same-size Sprites into a horizontal strip PNG at 1x."""
    from PIL import Image
    w, h = frames[0].w, frames[0].h
    im = Image.new("RGBA", (w * len(frames), h), (0, 0, 0, 0))
    for i, f in enumerate(frames):
        im.paste(f.composite(), (i * w, 0))
    im.save(os.path.join(OUT, name)); print("strip ->", name, im.size)
    return im
