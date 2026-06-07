"""
galaga_generator.py  —  GIF animado estilo Galaga para GitHub README
Gera galaga-contributions.gif via Pillow (sem dependências externas além de requests).
"""
import os, math, random, requests
from PIL import Image, ImageDraw

USERNAME = os.environ.get("GITHUB_USERNAME", "philippluca123")
GH_TOKEN = os.environ.get("GITHUB_TOKEN", "")
OUT_FILE = "galaga-contributions.gif"
HEADERS  = {"Authorization": f"Bearer {GH_TOKEN}"} if GH_TOKEN else {}

# ── Canvas ─────────────────────────────────────────────────────────────────
W, H = 720, 300
FPS  = 12          # frames por segundo
LOOP = 20.0        # duração do loop em segundos
N_FRAMES = int(FPS * LOOP)

# ── Palette ────────────────────────────────────────────────────────────────
BG     = (10,  10,  15)
GREEN  = (57,  255, 20)
CYAN   = (0,   255, 255)
PINK   = (255, 45,  120)
YELLOW = (255, 230, 0)
PURPLE = (184, 79,  255)
ORANGE = (255, 140, 0)
WHITE  = (255, 255, 255)
DARK   = (20,  40,  20)

# ── GitHub API ─────────────────────────────────────────────────────────────
def fetch():
    q = """query($l:String!){user(login:$l){contributionsCollection{
      contributionCalendar{totalContributions
      weeks{contributionDays{contributionCount}}}}}}"""
    try:
        r = requests.post("https://api.github.com/graphql",
            json={"query": q, "variables": {"l": USERNAME}},
            headers=HEADERS, timeout=10)
        cal = r.json()["data"]["user"]["contributionsCollection"]["contributionCalendar"]
        return cal["weeks"], cal["totalContributions"]
    except Exception as e:
        print(f"API: {e}"); return [], 0

def demo():
    rng = random.Random(7)
    wks = [{"contributionDays": [{"contributionCount": rng.randint(0, 14)}
            for _ in range(7)]} for _ in range(26)]
    return wks, sum(d["contributionCount"] for w in wks for d in w["contributionDays"])

# ── Pixel art draw helpers ─────────────────────────────────────────────────
S = 2  # pixel size

def draw_pixels(d, pixels, color, ox, oy):
    for c, r in pixels:
        x, y = ox + c*S, oy + r*S
        d.rectangle([x, y, x+S-1, y+S-1], fill=color)

# Alien shapes
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

SHIP_PX  = [(3,0),(4,0),(2,1),(3,1),(4,1),(5,1),(1,2),(2,2),(3,2),(4,2),(5,2),(6,2),
            (0,3),(1,3),(2,3),(3,3),(4,3),(5,3),(6,3),(7,3),(1,4),(2,4),(5,4),(6,4)]
SHIP_COK = [(3,0),(4,0)]
SHIP_EXH = [(2,4),(5,4)]
SW, SH   = 8, 5

def draw_alien(d, cx, cy, count, max_c, flicker=False):
    ox = cx - AW*S//2
    oy = cy - AH*S//2
    r  = count / max_c if max_c else 0
    if flicker:
        color, eyes = WHITE, WHITE
    elif r < 0.35:
        color, eyes = PURPLE, None
    elif r < 0.70:
        color, eyes = CYAN, None
    else:
        color, eyes = GREEN, CYAN

    body = A_BODY if r < 0.35 else (B_BODY if r < 0.70 else C_BODY)
    draw_pixels(d, body, color, ox, oy)
    if eyes and not flicker:
        draw_pixels(d, C_EYES, eyes, ox, oy)

def draw_ship(d, cx, cy):
    ox = cx - SW*S//2
    oy = cy - SH*S//2
    draw_pixels(d, SHIP_PX,  CYAN,   ox, oy)
    draw_pixels(d, SHIP_COK, YELLOW, ox, oy)
    draw_pixels(d, SHIP_EXH, PINK,   ox, oy)

def draw_ship_mini(d, cx, cy, scale=0.6):
    s = int(S * scale)
    if s < 1: s = 1
    ox = cx - int(SW*s//2)
    oy = cy - int(SH*s//2)
    for c, r in SHIP_PX:
        x, y = ox+c*s, oy+r*s
        d.rectangle([x,y,x+s-1,y+s-1], fill=CYAN)

def draw_explosion(d, cx, cy, phase):
    """phase 0..1 — explosão se expande e some."""
    if phase > 1: return
    rings = [(YELLOW,4), (ORANGE,8), (PINK,12)]
    for i, (col, max_r) in enumerate(rings):
        offset = i * 0.15
        p = max(0, phase - offset) / (1 - offset) if (1-offset) > 0 else 0
        r = int(max_r * p)
        alpha = int(255 * (1 - p))
        if r > 0 and alpha > 0:
            col_a = col + (alpha,)
            d.ellipse([cx-r, cy-r, cx+r, cy+r], outline=col)

def draw_stars(d, stars):
    for x, y, brightness in stars:
        d.point((x, y), fill=(brightness, brightness, brightness))

# ── Timing helpers ─────────────────────────────────────────────────────────
ENTER_DUR = 3.5
SHOOT_GAP = 1.0

def ease_out(t):
    """t em [0,1] → valor suavizado."""
    return 1 - (1-t)**3

def lerp(a, b, t):
    return a + (b-a)*t

def smoothstep(a, b, t):
    t = max(0, min(1, t))
    t = t*t*(3-2*t)
    return lerp(a, b, t)

# ── Main build ─────────────────────────────────────────────────────────────
def build_gif(weeks, total):
    rng = random.Random(42)

    counts = [sum(d["contributionCount"] for d in w["contributionDays"]) for w in weeks[-20:]]
    while len(counts) < 5: counts.append(1)
    counts = counts[-20:]
    max_c  = max(counts) if any(counts) else 1
    N      = len(counts)
    cols   = min(N, 10)
    pad    = 70
    xsp    = (W - pad*2) / max(cols-1, 1)
    ysp    = 46
    y0     = 52

    pos = [(int(pad + (i%cols)*xsp), int(y0 + (i//cols)*ysp), c)
           for i, c in enumerate(counts)]

    SCY = H - 52   # Y fixo da nave
    SCX = W // 2

    # Estrelas fixas
    stars = [(rng.randint(4, W-4), rng.randint(30, H-30),
              rng.randint(60, 200)) for _ in range(55)]

    # Calcular posição X da nave em cada frame
    def ship_x_at(t):
        # Patrulha inicial
        if t < ENTER_DUR:
            p = t / ENTER_DUR
            # oscila entre SCX-70 e SCX+70
            return SCX + math.sin(p * math.pi * 2) * 70
        # Sequência de disparos
        for idx, (ax, ay, c) in enumerate(pos):
            ta = ENTER_DUR + idx * SHOOT_GAP
            tz = ta + 0.4
            tn = ENTER_DUR + (idx+1) * SHOOT_GAP
            if ta <= t < tz:
                # mira no alien
                prev_x = ship_x_at(ta - 0.01) if ta > 0.01 else SCX
                return smoothstep(prev_x, ax, (t-ta)/0.4)
            if tz <= t < tn:
                return ax
        return SCX

    # Estado dos aliens: alive, dead, exploding
    # Para cada alien: tempo em que morre
    alien_die_t = {idx: ENTER_DUR + idx * SHOOT_GAP + 0.48 for idx in range(N)}

    frames = []
    print(f"Gerando {N_FRAMES} frames...", end="", flush=True)

    for fi in range(N_FRAMES):
        t = fi / FPS   # tempo atual em segundos

        img = Image.new("RGB", (W, H), BG)
        d   = ImageDraw.Draw(img)

        # Scanlines sutis
        for sy in range(0, H, 4):
            d.line([(0, sy+3), (W, sy+3)], fill=(0,0,0,25))

        # Estrelas (piscando)
        for sx, sy, sb in stars:
            flicker = int(sb * (0.7 + 0.3 * math.sin(t*2.1 + sx*0.1)))
            d.point((sx, sy), fill=(flicker, flicker, flicker))

        # HUD superior
        d.line([(0,26),(W,26)], fill=DARK)
        d.line([(0,H-26),(W,H-26)], fill=DARK)

        # Aliens
        for idx, (ax, ay, c) in enumerate(pos):
            die_t = alien_die_t[idx]
            enter_t = idx * 0.11

            if t < enter_t:
                continue   # ainda não entrou

            # Posição Y de entrada
            enter_progress = min(1.0, (t - enter_t) / 0.5)
            entry_y_off = int((1 - ease_out(enter_progress)) * -(ay + 24))

            # Hover suave
            hover_off = int(math.sin((t - enter_t - 0.5) * math.pi) * 3) if enter_progress >= 1 else 0

            actual_y = ay + entry_y_off + hover_off

            if t >= die_t + 0.48:
                continue  # já morreu

            flicker = False
            if die_t <= t < die_t + 0.48:
                # Flickering antes de morrer
                flicker = int((t - die_t) * 20) % 2 == 0

            draw_alien(d, ax, actual_y, c, max_c, flicker=flicker)

        # Bullets
        for idx, (ax, ay, c) in enumerate(pos):
            tf = ENTER_DUR + idx * SHOOT_GAP
            if tf <= t < tf + 0.48:
                prog = (t - tf) / 0.48
                by0  = SCY - SH*S//2 - 4
                by1  = ay  + AH*S//2
                by   = int(lerp(by0, by1, ease_out(prog)))
                d.rectangle([ax-1, by, ax+1, by+6], fill=GREEN)

        # Explosões
        for idx, (ax, ay, c) in enumerate(pos):
            die_t = alien_die_t[idx]
            if die_t <= t < die_t + 0.55:
                phase = (t - die_t) / 0.55
                draw_explosion(d, ax, ay, phase)

        # Nave
        sx = int(ship_x_at(t))
        draw_ship(d, sx, SCY)

        # Vidas
        for li in range(3):
            draw_ship_mini(d, 18 + li*22, H-14)

        # Score / HUD text  (simples com pixels — sem fonte externa)
        score = total * 150
        hud_items = [
            (10,  8, f"WAVE 01", GREEN),
            (W//2, 8, f"TOTAL {total}", CYAN),
            (W-10, 8, f"SCORE {score:07d}", YELLOW),
        ]
        # Desenha texto simples como blocos (sem truetype)
        for tx, ty, text, col in hud_items:
            # Usa uma fonte bitmap simples do Pillow
            try:
                from PIL import ImageFont
                font = ImageFont.load_default()
                bbox = d.textbbox((0,0), text, font=font)
                tw = bbox[2]-bbox[0]
                d.text((tx - tw//2 if tx > 50 else tx, ty), text, fill=col, font=font)
            except:
                pass

        # Username footer
        try:
            from PIL import ImageFont
            font = ImageFont.load_default()
            foot = f"LAST 20 WEEKS  @{USERNAME}  WAVE 01"
            bbox = d.textbbox((0,0), foot, font=font)
            tw = bbox[2]-bbox[0]
            d.text(((W-tw)//2, H-18), foot, fill=(50,50,50), font=font)
        except:
            pass

        frames.append(img)
        if fi % 50 == 0:
            print(".", end="", flush=True)

    print(f" {N_FRAMES} frames prontos.")

    # Converte para paleta (GIF requer indexed color)
    print("Convertendo para GIF...", end="", flush=True)
    palette_frames = []
    for img in frames:
        # Quantiza para 256 cores
        pimg = img.quantize(colors=64, method=Image.Quantize.MEDIANCUT, dither=0)
        palette_frames.append(pimg)
    print(" OK")

    print(f"Salvando {OUT_FILE}...")
    palette_frames[0].save(
        OUT_FILE,
        save_all=True,
        append_images=palette_frames[1:],
        duration=int(1000/FPS),   # ms por frame
        loop=0,                   # loop infinito
        optimize=False,
    )
    size_kb = os.path.getsize(OUT_FILE) // 1024
    print(f"OK — {OUT_FILE} ({size_kb} KB)")

def main():
    print(f"Galaga GIF para @{USERNAME}...")
    weeks, total = fetch()
    if not weeks:
        print("Modo demo."); weeks, total = demo()
    build_gif(weeks, total)

if __name__ == "__main__":
    main()
