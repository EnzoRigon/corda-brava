# Polish: rope alignment fix

Measurements (controller, Pillow): pull/happy/defeat/cry GIFs are all 384x448 (masters are 48x48 PNG, used only for idle/waiting). Sprite rope exits the right edge as a band y=280..303 (24px): light #CAA15A top 2/3, dark #9C7838 bottom 1/3.

Approach: `Mascot` no longer sets a height (width = size, `height:auto`), so the aspect is kept. `.rope-scene` defines `--mascot-w` (160px) and derives `--mascot-h = w*448/384`, `--rope-top = w*280/384`, `--rope-th = w*24/384`. `.rope` has height `--mascot-h`; `.rope-line` sits at `--rope-top` with a hard-stop two-tone gradient; knot is centered on the line (horizontal formula unchanged). Scene uses `align-items:flex-start`, no gap. Push scale uses transform-origin `100% 65%` (Inter) / `0% 65%` (Gremio) so the rope exit stays put.

Visual check (new tab, running match on localhost:5173): screenshot shows the rope continuous from both sprites' hands at the same height. The zoom tool did not magnify, so geometry was confirmed with getBoundingClientRect: imgs 40..200 and 824..984 at top 193.6; line 200..824 (exact edges, no gap/overlap), top 310.3 = 193.6 + 116.7, thickness 10 = 160*24/384. Knot centered on the line.

Caveat: idle sprites (48x48 master) are square, so they are not aligned in the scene; the scene uses straining/win/lose GIFs only.
