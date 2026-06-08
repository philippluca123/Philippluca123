"""
alien_guide_gen.py — GIF estático estilo arcade com os 3 tipos de alien
"""
from PIL import Image, ImageDraw
import math

OUT = "alien-guide.gif"
W, H = 520, 160
BG     = (10, 10, 15)
GREEN  = (57, 255, 20)
CYAN   = (0, 255, 255)
PURPLE = (184, 79, 255)
YELLOW = (255, 230, 0)
DARK   = (20, 40, 20)
GRAY   = (60, 60, 70)

S = 3  # pixel size — maior que o jogo pra ficar legível

A_BODY = [(3,0),(4,0),(2,1),(3,1),(4,1),(5,1),(1,2),(2,2),(3,2),(4,2),(5,2),(6,2),
          (0,3),(1,3),(2,3),(3,3),(4,3),(5,3),(6,3),(7,3),
          (0,4),(1,4),(3,4),(4,4),(6,4),(7,4),(1,6),(2,6),(5,6),(6,6)]
B_BODY = [(3,0),(4,0),(1,1),(2,1),(3,1),(4,1),(5,1),(6,1),
          (0,2),(1,2),(2,2),(3,2),(4,2),(5,2),(6,2),(7,2),
          (0,3),(1,3),(3,3),(4,3),(6,3),(7,3),(2,4),(3,4),(4,4),(5,4),(1,5),(6,5)]
C_BODY = [(2,0),(3,0),(4,0),(5,0),(1,1),(2,1),(3,1),(4,1),(5,1),(6,1),
          (0,2),(1,2),(2,2),(3,2),(4,2),(5,2),(6,2),(7,2),
          (0,3),(1,3),(2,3),(3,3),(4,3),(5,3),(6,3),(7,3),
          (0,4),(3,4),(4,4),(7,4),(1,5),(2,5),(5,5),(6,5)]
C_EYES = [(2,1),(5,1)]
AW, AH = 8, 7

def draw_alien(d, cx, cy, body, color, eyes=None, eye_color=None):
    ox = cx - AW*S//2
    oy = cy - AH*S//2
    for (c,r) in body:
        x,y = ox+c*S, oy+r*S
        d.rectangle([x,y,x+S-1,y+S-1], fill=color)
    if eyes:
        for (c,r) in eyes:
            x,y = ox+c*S, oy+r*S
            d.rectangle([x,y,x+S-1,y+S-1], fill=eye_color)

def draw_bar(d, x, y, filled, total, color):
    bw, bh = 9, 9
    gap = 3
    for i in range(total):
        col = color if i < filled else GRAY
        d.rectangle([x+i*(bw+gap), y, x+i*(bw+gap)+bw, y+bh], fill=col)

def make_frame(t):
    img = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(img)

    # scanlines
    for y in range(0, H, 4):
        d.line([(0,y+3),(W,y+3)], fill=(0,0,0))

    # linha divisória top
    d.line([(0,22),(W,22)], fill=DARK)
    d.line([(0,H-22),(W,H-22)], fill=DARK)

    # título
    font = None
    try:
        from PIL import ImageFont
        font = ImageFont.load_default()
    except: pass

    title = "// ALIEN  FIELD  MANUAL //"
    if font:
        bb = d.textbbox((0,0), title, font=font)
        tw = bb[2]-bb[0]
        d.text(((W-tw)//2, 7), title, fill=GREEN, font=font)

    # hover offset
    off = int(math.sin(t) * 3)

    # ── posições dos 3 aliens ──
    positions = [
        (W//6,       80+off, A_BODY, PURPLE, None,   None,  "GRUNT",   "0-4/sem",   "100 pts", 1, 5, PURPLE),
        (W//2,       80+off, B_BODY, CYAN,   None,   None,  "SOLDIER", "5-9/sem",   "300 pts", 3, 5, CYAN),
        (W*5//6,     80+off, C_BODY, GREEN,  C_EYES, CYAN,  "BOSS",    "10+/sem",   "800 pts", 5, 5, GREEN),
    ]

    for (cx, cy, body, color, eyes, ecol, name, commits, pts, diff, dtotal, dcol) in positions:
        draw_alien(d, cx, cy, body, color, eyes, ecol)

        if font:
            # nome
            nb = d.textbbox((0,0), name, font=font)
            nw = nb[2]-nb[0]
            d.text((cx-nw//2, cy+AH*S//2+6), name, fill=color, font=font)
            # commits
            cb2 = d.textbbox((0,0), commits, font=font)
            cw = cb2[2]-cb2[0]
            d.text((cx-cw//2, cy+AH*S//2+18), commits, fill=GRAY, font=font)
            # pontos
            pb = d.textbbox((0,0), pts, font=font)
            pw = pb[2]-pb[0]
            d.text((cx-pw//2, cy+AH*S//2+30), pts, fill=YELLOW, font=font)

        # barra de dificuldade
        bar_x = cx - (dtotal*(9+3)-3)//2
        bar_y = cy + AH*S//2 + 43
        draw_bar(d, bar_x, bar_y, diff, dtotal, dcol)

    # separadores verticais
    d.line([(W//3, 28),(W//3, H-24)], fill=DARK)
    d.line([(W*2//3, 28),(W*2//3, H-24)], fill=DARK)

    return img

FPS = 12
LOOP = 3.0
N = int(FPS * LOOP)

print("Gerando frames...", end="", flush=True)
frames = []
for fi in range(N):
    t = fi / FPS * math.pi * 2 / LOOP * 2
    frames.append(make_frame(t))
print(f" {N} frames")

print("Convertendo...", end="", flush=True)
pframes = [f.quantize(colors=32, method=Image.Quantize.MEDIANCUT, dither=0) for f in frames]
print(" OK")

pframes[0].save(OUT, save_all=True, append_images=pframes[1:],
                duration=int(1000/FPS), loop=0, optimize=False)

import os
print(f"Salvo: {OUT} ({os.path.getsize(OUT)//1024} KB)")
