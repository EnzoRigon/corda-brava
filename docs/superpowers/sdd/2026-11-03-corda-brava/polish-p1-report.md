# Polish P1 report: original pixel asset pack

Commit: 7c21e15 (feat(art): original pixel UI asset pack). Exports (1x PNG) in `frontend/src/assets/ui/`;
build scripts in `.claude/skills/pixel-art-studio/pixel-art/corda-brava-ui/{logo,icons,particles,scenery}/build.py`,
shared palette/helpers in `corda-brava-ui/pal.py`, `contact_sheet.py` makes `contact-sheet.png` (4x).
Run: `cd <slug> && python build.py` (each writes a preview.png next to it).

## Assets (all PNG, transparent unless noted)
| File | Size | Frames / notes |
|---|---|---|
| logo-160x56.png | 160x56 | gold lettering, dark outline, extruded shadow, rope between words with red + blue ribbons and a knot |
| logo-small-96x36.png | 96x36 | same, no ribbons |
| icon-heart/star/trophy/crown/lightning/hourglass/speaker-on/speaker-off/arrow-left/check/cross/player/whistle/rope-coil/pennant-red/pennant-blue.png | 16x16 each | single frame |
| fx-sparkle-strip-6f-8px.png | 48x8 | 6 frames of 8x8, horizontal strip |
| fx-dust-strip-5f-12px.png | 60x12 | 5 frames of 12x12, horizontal strip |
| fx-confetti-sheet-4x2-4px.png | 16x8 | 4 colors (red, blue, gold, cream) x 2 poses (row 0 flat, row 1 tilted), 4x4 cells |
| bg-sky-tile-64.png | 64x64 | opaque, tiles both axes |
| bg-moon-32.png | 32x32 | dithered translucent glow |
| bg-cloud-a-48x16.png, bg-cloud-b-48x16.png | 48x16 | |
| bg-stadium-strip-128x48.png | 128x48 | tiles horizontally; transparent above the stands; two floodlight towers (dithered translucent halo) |
| bg-pitch-strip-32x24.png | 32x24 | opaque, tiles horizontally, two mow bands, chalk line at y=6-7 |

## Palette (32 colors, pal.py)
Outline K #141019, glint #ffffff; cream/gold W #fff8e0 Y #ffe27a G #f2b632 O #b8741a o #6e3f16;
red R #e23b3b r #9c1f2e q #ff8a74; blue B #2f6fd0 b #1b3f8c l #8cc4ff; steel A #cdd3e2 a #8790ad d #4a4f75;
green E #6cc65a e #2f8a46 g #b4ec8a M #3fa04f N #256b3a; skin F #e8b48a f #b9805e; rope T #d9b36a t #a67c3a;
night n1 #0a0c22 n2 #12163a n3 #1c2456 n4 #2c3778 n5 #4a58a0; stands Z #2b2347 z #3a3160.
Extra non-palette values: moon glow (cream at alpha 44/70, a translucent dither) and two crater tints.

## What I looked at and fixed
- Icons: first sheet read well; fixed detached/ugly speaker arcs (now overlay pixels beside the cone), redrew the whistle (procedural chamber + mouthpiece + ring), removed the mustache-like mouth on player.
- Particles: pass 1 sparkle/dust/confetti were noise (procedural blobs, odd rotated overlaps); redrew as hand ASCII frames, made sparkle frames symmetric.
- Scenery pass 1: haze patches too heavy and stadium did not read as a silhouette; pass 2: fewer/smaller haze, near-black stands with lighter canopy, tier lines, thicker halos; pitch bands were identical because palette snap mapped the new green to an existing one, so added M/N to the palette.
- Logo pass 1: right-edge shading and thick bevel muddied counters and the V had a stalk; pass 2: dropped right-edge shading, thinner bevel, blockier V, darker rope underside.
- Contact sheet viewed; no inconsistencies needing a fix (one outline color, one light direction top-left).

## Deviations
- Small logo is 96x36, not 96x32 (two stacked words at scale 2 need the height).
- Logo is two stacked lines with the rope between, 5x7 original block font; no club crests or mascots anywhere.
- Palette is exactly 32 colors; the translucent moon glow adds alpha values beyond that.
- Not checked: the assets inside the real app (no frontend wiring in P1); tileability judged by eye on the tiled preview.
