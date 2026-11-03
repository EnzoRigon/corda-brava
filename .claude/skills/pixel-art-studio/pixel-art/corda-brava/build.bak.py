import sys, os
sys.path.insert(0, "/Users/pauloricardodalsoto/orca/projects/trabGb/.claude/skills/pixel-art-studio/scripts")
from pixelstudio import Sprite

# ============================================================
#  CORDA BRAVA — mascot test  (pass 2)
#  Saci (Inter) + Mosqueteiro (Gremio)
#  States: pull (strain + rope), happy, cry
# ============================================================

# Inter / Saci
SKIN="#8a5a32"; SKIN_D="#6b4426"; SKIN_L="#a06a3c"
RED="#e5050f"; RED_D="#b00008"
WHITE="#f4f4f4"; WHT_D="#cfd2d4"
HAIR="#15131c"
ROPE="#caa15a"; ROPE_D="#9c7838"

# Gremio / Mosqueteiro
BLUE="#1565b0"; BLUE_D="#0d4a86"; BLUE_L="#4fa9dc"; SKY="#9cd3f0"
FLESH="#e3b08a"; FLESH_D="#c48f68"
GHAIR="#15131c"
TAN="#b07d47"; TAN_D="#8a5f33"
STEEL="#d4d9e0"; STEEL_D="#8b93a0"
GOLD="#f2c14e"; PLUME="#f4f4f4"; PLUME_D="#cfd2d4"
MOUTH="#7a1020"

OUT="#141019"


# ============================================================
#  SACI (Inter)
# ============================================================
def build_saci():
    s = Sprite(48, 48, palette=[SKIN,SKIN_D,SKIN_L,RED,RED_D,WHITE,WHT_D,HAIR,ROPE,ROPE_D,OUT,"#ffffff","#4fa9dc","#9cd3f0"])

    def head(cx, cy, tilt=0, eyemood="normal", mouth="smile"):
        # --- soft Phrygian gorro (floppy, flops to the BACK-right, pointed tip) ---
        # headband/aba across forehead
        s.rect(cx-9, cy-9, cx+9, cy-6, RED)
        s.rect(cx-9, cy-6, cx+9, cy-5, WHITE)            # white band edge
        # rounded crown sitting low on the head
        s.ellipse(cx-9, cy-12, cx+7, cy-6, RED)
        # floppy tail drooping to the back-right (sequence of shrinking blobs)
        tail=[(cx+7,cy-11),(cx+10,cy-12),(cx+13,cy-11),(cx+15,cy-8),(cx+16,cy-4)]
        for i,(tx,ty2) in enumerate(tail):
            r = 4-i//2
            s.ellipse(tx-r, ty2-r, tx+r, ty2+r, RED)
        s.ellipse(cx+14,cy-2,cx+18,cy+2, RED)            # pom tip
        s.ellipse(cx+8,cy-11,cx+12,cy-8, RED_D, only=RED) # tail shading
        # hair peeking at back/nape (small, low)
        s.ellipse(cx+5, cy+1, cx+10, cy+7, HAIR)
        s.ellipse(cx-10, cy+1, cx-5, cy+7, HAIR)
        # round head
        s.circle(cx, cy, 9, SKIN, fill=True)
        # re-stamp band front so head doesn't cover it
        s.rect(cx-9, cy-9, cx+8, cy-6, RED, only=SKIN)
        s.rect(cx-9, cy-6, cx+8, cy-5, WHITE, only=SKIN)
        # eyes
        ey=cy-1
        if eyemood=="normal":
            s.circle(cx-4, ey, 2, "#ffffff", fill=True); s.px(cx-4, ey, HAIR)
            s.circle(cx+4, ey, 2, "#ffffff", fill=True); s.px(cx+4, ey, HAIR)
        elif eyemood=="happy":
            s.line(cx-6, ey+1, cx-3, ey-1, HAIR); s.line(cx-6, ey, cx-3, ey, HAIR)
            s.line(cx+3, ey-1, cx+6, ey+1, HAIR); s.line(cx+3, ey, cx+6, ey, HAIR)
        elif eyemood=="sad":
            s.circle(cx-4, ey, 2, "#ffffff", fill=True); s.px(cx-4, ey+1, HAIR)
            s.circle(cx+4, ey, 2, "#ffffff", fill=True); s.px(cx+4, ey+1, HAIR)
            s.px(cx-6, ey-2, HAIR); s.px(cx+6, ey-2, HAIR)
        elif eyemood=="strain":       # effort: half-closed, angry brow
            s.line(cx-6, ey, cx-2, ey, HAIR); s.line(cx+2, ey, cx+6, ey, HAIR)   # squint slits
            s.line(cx-6, ey-2, cx-3, ey-1, HAIR); s.line(cx+3, ey-1, cx+6, ey-2, HAIR)  # down-angled brows
        elif eyemood=="strain2":      # harder effort: tight shut
            s.line(cx-6, ey-1, cx-2, ey, HAIR); s.line(cx-6, ey, cx-2, ey+1, HAIR)
            s.line(cx+2, ey, cx+6, ey-1, HAIR); s.line(cx+2, ey+1, cx+6, ey, HAIR)
            s.line(cx-6, ey-3, cx-3, ey-2, HAIR); s.line(cx+3, ey-2, cx+6, ey-3, HAIR)
        # mouth
        my=cy+5
        if mouth=="smile":
            s.line(cx-3, my, cx+3, my, HAIR); s.px(cx-4, my-1, HAIR); s.px(cx+4, my-1, HAIR)
        elif mouth=="open":
            s.ellipse(cx-3, my-1, cx+3, my+3, HAIR); s.ellipse(cx-2, my, cx+2, my+2, "#ffffff")
        elif mouth=="frown":
            s.line(cx-3, my+2, cx+3, my+2, HAIR); s.px(cx-4, my+3, HAIR); s.px(cx+4, my+3, HAIR)
        elif mouth=="grit":           # clenched gritted teeth
            s.rect(cx-3, my, cx+3, my+2, HAIR); s.rect(cx-3, my, cx+3, my, "#ffffff")
            s.px(cx-1, my, HAIR); s.px(cx+1, my, HAIR)
        elif mouth=="shout":          # wide open yell
            s.ellipse(cx-3, my-1, cx+3, my+4, HAIR); s.ellipse(cx-2, my+1, cx+2, my+4, "#7a1020")

    def torso(cx, ty, tilt=0):
        s.rect(cx-7, ty, cx+7, ty+11, RED)
        s.rect(cx-7, ty-1, cx+7, ty, WHITE)
        s.circle(cx, ty+5, 3, WHITE, fill=True)
        s.circle(cx, ty+5, 3, RED_D, fill=False)
        s.px(cx, ty+5, RED)
        s.rect(cx-7, ty+11, cx+7, ty+15, WHITE)          # shorts
        s.px(cx, ty+12, RED); s.px(cx, ty+14, RED)

    def legs(cx, ty, mode="stand"):
        ly=ty+15
        if mode=="stand":   # legs TOGETHER — one short central leg + single cleat
            s.rect(cx-3, ly-1, cx+3, ly+4, SKIN)         # single leg block (wide, short, overlaps shorts)
            s.px(cx, ly, SKIN_D); s.px(cx, ly+2, SKIN_D) # faint center seam (two-leg hint)
            s.rect(cx-4, ly+4, cx+4, ly+6, WHITE)        # sock band
            s.ellipse(cx-7, ly+6, cx+7, ly+9, HAIR)      # one wide cleat
            s.px(cx+6, ly+8, "#ffffff")                  # cleat glint
        elif mode=="brace":
            s.rect(cx-3, ly-1, cx+1, ly+5, SKIN)
            s.rect(cx-4, ly+5, cx+2, ly+7, WHITE)
            s.ellipse(cx-7, ly+7, cx+3, ly+10, HAIR)

    # ---- PULL: PROFILE view, facing RIGHT (toward arena center).
    #      Body leans back-left, both hands forward-right on the rope.
    #      Rope exits the RIGHT edge at a FIXED height ROPE_Y for CSS alignment.
    #      Single support leg (profile) to match the other poses.
    ROPE_Y = 29                                          # <-- fixed hand/rope line (sprite space)
    def frame_pull(f):
        bob=f
        cx=22; fy=44; ty=27-bob
        lean=-3                                          # shoulders tip back-left
        hx=cx+lean
        ry=ROPE_Y
        # rope exits toward center (right edge), at hand height
        s.rect(cx+6, ry, 47, ry+2, ROPE); s.rect(cx+6, ry, 47, ry, ROPE_D)
        # ---- single support leg (profile), knee bent, planted
        s.rect(cx-2, fy-10, cx+3, fy-3, SKIN)            # thigh/shin (one leg)
        s.px(cx+1, fy-8, SKIN_D)                         # calf shade
        s.rect(cx-3, fy-3, cx+4, fy-1, WHITE)            # sock
        s.ellipse(cx-3, fy-1, cx+9, fy+2, HAIR)          # cleat pointing right (profile)
        s.px(cx+8, fy, "#ffffff")
        # ---- torso leaned back-left (parallelogram)
        for yy in range(ty, ty+11):
            off = round(lean*(ty+11-yy)/11)
            s.rect(cx-5+off, yy, cx+5+off, yy, RED)
        s.circle(hx, ty+5, 2, WHITE, fill=True); s.px(hx,ty+5,RED_D)   # crest (side)
        s.rect(cx-5, ty+11, cx+5, ty+15, WHITE); s.px(cx,ty+12,RED)    # shorts
        # ---- both arms reaching forward-right DOWN to the rope at ry
        s.line(hx+3, ty+3, cx+6, ry, SKIN_D)             # back arm
        s.line(hx+4, ty+3, cx+7, ry, SKIN_D)
        s.line(hx+3, ty+5, cx+6, ry+1, SKIN)             # front arm
        s.line(hx+4, ty+5, cx+7, ry+1, SKIN_L)
        s.rect(cx+5, ry-1, cx+9, ry+3, SKIN)             # fists gripping rope at ry
        # ---- head in profile facing right, leaned back
        # facial effort changes per frame -> sense of force/motion
        em, mo = ("strain","grit") if bob==0 else ("strain2","shout")
        head(hx, ty-7, eyemood=em, mouth=mo)
        s.outline(OUT, where="outside")
    frame_pull(0)
    s.add_frame(copy=False); frame_pull(1)

    # ---- HAPPY ----
    def frame_happy(bob):
        cx=24; cy=17-bob; ty=cy+11
        # arms raised out to the SIDES above the head, clearing it
        s.rect(cx-13, ty-9, cx-9, ty-1, SKIN); s.rect(cx-14, ty-12, cx-9, ty-8, SKIN)  # L arm+fist
        s.rect(cx+9, ty-9, cx+13, ty-1, SKIN); s.rect(cx+9, ty-12, cx+14, ty-8, SKIN)  # R arm+fist
        torso(cx, ty)
        legs(cx, ty, "stand")
        head(cx, cy, eyemood="happy", mouth="open")
        s.outline(OUT, where="outside")
    s.add_frame(copy=False); frame_happy(0)
    s.add_frame(copy=False); frame_happy(1)

    # ---- CRY ----
    def frame_cry(tear):
        cx=24; cy=17; ty=cy+11
        s.rect(cx-9, cy+2, cx-5, cy+7, SKIN)             # hands up at face
        s.rect(cx+5, cy+2, cx+9, cy+7, SKIN)
        torso(cx, ty)
        legs(cx, ty, "stand")
        head(cx, cy, eyemood="sad", mouth="frown")
        s.px(cx-5, cy+3+tear, BLUE_L); s.px(cx+5, cy+3+tear, BLUE_L)
        s.px(cx-5, cy+5+tear, SKY);    s.px(cx+5, cy+5+tear, SKY)
        s.outline(OUT, where="outside")
    s.add_frame(copy=False); frame_cry(0)
    s.add_frame(copy=False); frame_cry(2)

    s.set_duration(240)
    s.tag("pull",1,2); s.tag("happy",3,4); s.tag("cry",5,6)
    return s


# ============================================================
#  MOSQUETEIRO (Gremio)
# ============================================================
def build_mosq():
    s = Sprite(48, 48, palette=[BLUE,BLUE_D,BLUE_L,SKY,FLESH,FLESH_D,GHAIR,TAN,TAN_D,STEEL,STEEL_D,GOLD,PLUME,PLUME_D,ROPE,ROPE_D,OUT,"#ffffff","#7a1020"])

    def feather(cx, cy):
        # white plume sweeping LEFT off the hat, flatter arc (stays within canvas top)
        pts=[(cx-9,cy-12),(cx-12,cy-13),(cx-15,cy-15),(cx-18,cy-16),(cx-20,cy-18)]
        for (px,py) in pts:
            s.ellipse(px-2, py-2, px+2, py+2, PLUME)
        s.ellipse(cx-22,cy-19,cx-17,cy-14,PLUME)          # feather tip
        # underside shading
        s.px(cx-13,cy-11,PLUME_D); s.px(cx-17,cy-13,PLUME_D); s.px(cx-20,cy-16,PLUME_D)

    def hat(cx, cy):
        feather(cx, cy)
        s.ellipse(cx-14, cy-12, cx+14, cy-6, BLUE)      # wide brim
        s.ellipse(cx-14, cy-10, cx+14, cy-6, BLUE_D, only=BLUE)  # brim underside
        s.ellipse(cx-8, cy-18, cx+9, cy-9, BLUE)        # crown (lowered 2px for top margin)
        s.ellipse(cx-8, cy-18, cx+2, cy-11, BLUE_L, only=BLUE)   # crown highlight

    def head(cx, cy, eyemood="normal", mouth="smile"):
        s.circle(cx, cy, 8, FLESH, fill=True)
        hat(cx, cy)
        ey=cy-2
        if eyemood=="normal":
            s.px(cx-4,ey,GHAIR); s.px(cx-4,ey+1,GHAIR)
            s.px(cx+4,ey,GHAIR); s.px(cx+4,ey+1,GHAIR)
        elif eyemood=="happy":
            s.line(cx-6,ey,cx-2,ey-1,GHAIR); s.line(cx+2,ey-1,cx+6,ey,GHAIR)
        elif eyemood=="sad":
            s.px(cx-4,ey+1,GHAIR); s.px(cx+4,ey+1,GHAIR)
            s.px(cx-6,ey-1,GHAIR); s.px(cx+6,ey-1,GHAIR)  # worried brow
        elif eyemood=="strain":
            s.line(cx-5,ey,cx-2,ey,GHAIR); s.line(cx+2,ey,cx+5,ey,GHAIR)        # squint
            s.px(cx-6,ey-2,GHAIR); s.px(cx+6,ey-2,GHAIR)                        # brow
        elif eyemood=="strain2":
            s.line(cx-5,ey-1,cx-2,ey,GHAIR); s.line(cx-5,ey,cx-2,ey+1,GHAIR)    # tight shut
            s.line(cx+2,ey,cx+5,ey-1,GHAIR); s.line(cx+2,ey+1,cx+5,ey,GHAIR)
            s.px(cx-6,ey-3,GHAIR); s.px(cx+6,ey-3,GHAIR)
        # curly moustache
        s.line(cx-5,cy+2,cx-1,cy+3,GHAIR); s.px(cx-6,cy+1,GHAIR)
        s.line(cx+1,cy+3,cx+5,cy+2,GHAIR); s.px(cx+6,cy+1,GHAIR)
        # goatee
        s.rect(cx-1,cy+5,cx+1,cy+8,GHAIR); s.px(cx-2,cy+5,GHAIR); s.px(cx+2,cy+5,GHAIR)
        if mouth=="open":
            s.ellipse(cx-2,cy+3,cx+2,cy+5,MOUTH)
        elif mouth=="frown":
            s.line(cx-3,cy+4,cx+3,cy+4,GHAIR)
        elif mouth=="grit":
            s.rect(cx-2,cy+3,cx+2,cy+4,GHAIR); s.rect(cx-2,cy+3,cx+2,cy+3,"#ffffff")
        elif mouth=="shout":
            s.ellipse(cx-2,cy+3,cx+2,cy+6,MOUTH)

    def torso(cx, ty):
        s.rect(cx-8, ty, cx+8, ty+12, BLUE)
        # white cross tabard
        s.rect(cx-2, ty, cx+2, ty+12, WHITE)
        s.rect(cx-8, ty+4, cx+8, ty+7, WHITE)
        s.circle(cx, ty+9, 3, SKY, fill=True)           # crest low-center
        s.circle(cx, ty+9, 3, BLUE_D, fill=False)
        s.rect(cx-8, ty+12, cx+8, ty+13, TAN)           # belt

    def legs(cx, ty):
        ly=ty+13
        s.rect(cx-6, ly, cx-2, ly+4, BLUE_D)
        s.rect(cx+2, ly, cx+6, ly+4, BLUE_D)
        s.rect(cx-7, ly+4, cx-1, ly+9, TAN)             # boots
        s.rect(cx+1, ly+4, cx+7, ly+9, TAN)
        s.rect(cx-8, ly+9, cx-1, ly+11, TAN_D)
        s.rect(cx+1, ly+9, cx+8, ly+11, TAN_D)
        s.px(cx-6, ly+7, GOLD); s.px(cx+6, ly+7, GOLD)

    def sword_raised(cx, ty):
        # right arm up
        s.rect(cx+7, ty-5, cx+10, ty+3, FLESH)
        s.rect(cx+7, ty-7, cx+11, ty-4, TAN)            # glove
        # hilt + guard
        s.px(cx+13, ty-7, GOLD); s.rect(cx+12, ty-9, cx+14, ty-8, GOLD)
        # blade diagonal up-right
        for i in range(12):
            s.px(cx+13+i, ty-9-i, STEEL)
            if i%3==0: s.px(cx+13+i, ty-8-i, STEEL_D)
        s.px(cx+25, ty-21, "#ffffff")                   # tip gleam

    def sword_rest(cx, ty):
        # sword held diagonally across body (pull/cry) so prop still reads
        s.px(cx+9, ty-2, GOLD); s.rect(cx+8,ty-3,cx+10,ty-2,GOLD)
        for i in range(10):
            s.px(cx+10+i, ty-3-i, STEEL)

    # ---- PULL: PROFILE facing RIGHT, same fixed ROPE_Y as Saci ----
    ROPE_Y = 29
    def frame_pull(f):
        bob=f
        cx=22; fy=44; ty=27-bob
        lean=-3; hx=cx+lean; ry=ROPE_Y
        s.rect(cx+6, ry, 47, ry+2, ROPE); s.rect(cx+6, ry, 47, ry, ROPE_D)
        # single support leg (profile) with tall boot
        s.rect(cx-2, fy-11, cx+3, fy-3, BLUE_D)
        s.rect(cx-3, fy-3, cx+5, fy, TAN); s.ellipse(cx-3, fy, cx+9, fy+2, TAN_D)  # boot pointing right
        s.px(cx+6, fy-1, GOLD)
        # leaned tabard torso
        for yy in range(ty, ty+12):
            off = round(lean*(ty+12-yy)/12)
            s.rect(cx-6+off, yy, cx+6+off, yy, BLUE)
        s.rect(hx-1, ty, hx+2, ty+11, WHITE)             # white panel (side)
        s.rect(cx-4, ty+4, cx+6, ty+6, WHITE)
        s.circle(hx+1, ty+8, 2, SKY, fill=True); s.px(hx+1,ty+8,BLUE_D)
        s.rect(cx-6, ty+12, cx+6, ty+13, TAN)            # belt
        # both gloved arms forward-right to rope at ry
        s.line(hx+3, ty+4, cx+6, ry, FLESH_D); s.line(hx+4, ty+4, cx+7, ry, FLESH_D)
        s.line(hx+3, ty+6, cx+6, ry+1, FLESH); s.line(hx+4, ty+6, cx+7, ry+1, FLESH)
        s.rect(cx+5, ry-1, cx+9, ry+3, TAN)              # gloves on rope at ry
        em, mo = ("strain","grit") if bob==0 else ("strain2","shout")
        head(hx, ty-7, em, mo)
        s.outline(OUT, where="outside")
    frame_pull(0)
    s.add_frame(copy=False); frame_pull(1)

    # ---- HAPPY (sword raised) ----
    def frame_happy(bob):
        cx=24; cy=20-bob; ty=cy+10
        sword_raised(cx, ty)
        s.rect(cx-12, ty-8, cx-8, ty+1, FLESH); s.rect(cx-13, ty-11, cx-8, ty-7, TAN)  # left fist up, clear of head
        torso(cx, ty); legs(cx, ty)
        head(cx, cy, "happy", "open")
        s.outline(OUT, where="outside")
    s.add_frame(copy=False); frame_happy(0)
    s.add_frame(copy=False); frame_happy(1)

    # ---- CRY ----
    def frame_cry(tear):
        cx=24; cy=20; ty=cy+10
        s.rect(cx-9, cy+2, cx-5, cy+7, FLESH)
        s.rect(cx+5, cy+2, cx+9, cy+7, FLESH)
        sword_rest(cx, ty)                              # sword drooping across
        torso(cx, ty); legs(cx, ty)
        head(cx, cy, "sad", "frown")
        s.px(cx-5, cy+3+tear, BLUE_L); s.px(cx+5, cy+3+tear, BLUE_L)
        s.px(cx-5, cy+5+tear, SKY);    s.px(cx+5, cy+5+tear, SKY)
        s.outline(OUT, where="outside")
    s.add_frame(copy=False); frame_cry(0)
    s.add_frame(copy=False); frame_cry(2)

    s.set_duration(240)
    s.tag("pull",1,2); s.tag("happy",3,4); s.tag("cry",5,6)
    return s


if __name__ == "__main__":
    os.makedirs("out", exist_ok=True)
    saci = build_saci()
    saci.preview("out/saci_preview.png", scale=8)
    saci.save_silhouette("out/saci_sil.png", frame=1)
    saci.stats()
    for t in ("pull","happy","cry"):
        saci.save_gif(f"out/saci_{t}.gif", scale=6, tag=t, bg="#2b2f3a")

    mosq = build_mosq()
    mosq.preview("out/mosq_preview.png", scale=8)
    mosq.save_silhouette("out/mosq_sil.png", frame=1)
    mosq.stats()
    for t in ("pull","happy","cry"):
        mosq.save_gif(f"out/mosq_{t}.gif", scale=6, tag=t, bg="#2b2f3a")
    print("done")
