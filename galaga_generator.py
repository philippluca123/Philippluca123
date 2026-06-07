"""
galaga_generator.py  v5  — SVG cinemático Galaga, compatível GitHub
Fixes:
  - Nave: outer g com Y fixo, inner g com X animado (sem sumir fora do canvas)
  - Aliens: dois g aninhados para entrada + hover sem conflito SMIL
  - Bullets: coordenadas X absolutas, Y relativo ao SCY fixo
"""
import os, math, random, requests

USERNAME  = os.environ.get("GITHUB_USERNAME", "philippluca123")
GH_TOKEN  = os.environ.get("GITHUB_TOKEN", "")
OUT_FILE  = "galaga-contributions.svg"
HEADERS   = {"Authorization": f"Bearer {GH_TOKEN}"} if GH_TOKEN else {}

W, H       = 800, 400
BG         = "#0a0a0f"
GREEN      = "#39ff14"
CYAN       = "#00ffff"
PINK       = "#ff2d78"
YELLOW     = "#ffe600"
PURPLE     = "#b84fff"
ORANGE     = "#ff8c00"
LOOP_DUR   = 22.0
ENTER_DUR  = 3.5
SHOOT_GAP  = 1.1
S          = 2        # px por pixel de arte

# ── API ────────────────────────────────────────────────────────────────────
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
        print(f"API error: {e}"); return [], 0

def demo():
    rng = random.Random(7)
    wks = [{"contributionDays": [{"contributionCount": rng.randint(0, 14)}
            for _ in range(7)]} for _ in range(26)]
    return wks, sum(d["contributionCount"] for w in wks for d in w["contributionDays"])

# ── Pixel art helpers ──────────────────────────────────────────────────────
def px(pixels, fill, ox, oy):
    """Gera <rect> para cada (col,row) pixel, com escala S."""
    return "".join(
        f'<rect x="{ox+c*S}" y="{oy+r*S}" width="{S}" height="{S}" fill="{fill}"/>'
        for c, r in pixels)

# Alien shapes (col, row) — origem top-left local
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
AW, AH = 8, 7   # alien width/height em unidades de pixel

# Nave centrada em (0,0) — origem = centro da nave
SHIP_PX  = [(3,0),(4,0),(2,1),(3,1),(4,1),(5,1),(1,2),(2,2),(3,2),(4,2),(5,2),(6,2),
            (0,3),(1,3),(2,3),(3,3),(4,3),(5,3),(6,3),(7,3),(1,4),(2,4),(5,4),(6,4)]
SHIP_COK = [(3,0),(4,0)]   # cockpit amarelo
SHIP_EXH = [(2,4),(5,4)]   # exaustão rosa
SW, SH   = 8, 5            # nave width/height em unidades de pixel

def ship_art():
    """Nave pixel centrada em (0,0). O <g> pai cuida do translate."""
    ox = -(SW * S) // 2    # -8
    oy = -(SH * S) // 2    # -5
    return (px(SHIP_PX,  CYAN,   ox, oy)
          + px(SHIP_COK, YELLOW, ox, oy)
          + px(SHIP_EXH, PINK,   ox, oy))

def alien_art(cx, cy, count, max_c):
    """Alien centrado em (cx, cy)."""
    ox = cx - (AW * S) // 2
    oy = cy - (AH * S) // 2
    r  = count / max_c if max_c else 0
    if r < 0.35:
        return px(A_BODY, PURPLE, ox, oy)
    elif r < 0.70:
        return px(B_BODY, CYAN,   ox, oy)
    else:
        return px(C_BODY, GREEN, ox, oy) + px(C_EYES, CYAN, ox, oy)

def alien_color(count, max_c):
    r = count / max_c if max_c else 0
    return PURPLE if r < 0.35 else (CYAN if r < 0.70 else GREEN)

def explosion_svg(cx, cy, t0):
    out = []
    for i, (col, r1) in enumerate([(YELLOW, 5), (ORANGE, 9), (PINK, 13)]):
        t = t0 + i * 0.09
        out.append(
            f'<circle cx="{cx}" cy="{cy}" r="2" fill="{col}" opacity="0">'
            f'<animate attributeName="r" values="2;{r1}" dur="0.32s" begin="{t:.2f}s" fill="freeze"/>'
            f'<animate attributeName="opacity" values="0;1;0" keyTimes="0;0.1;1"'
            f' dur="0.32s" begin="{t:.2f}s" fill="freeze"/></circle>')
    return "".join(out)

# ── Build SVG ──────────────────────────────────────────────────────────────
def build(weeks, total):
    rng = random.Random(42)

    counts = [sum(d["contributionCount"] for d in w["contributionDays"]) for w in weeks[-20:]]
    while len(counts) < 5:
        counts.append(1)
    counts = counts[-20:]
    max_c  = max(counts) if any(counts) else 1

    N    = len(counts)
    cols = min(N, 10)
    pad  = 70
    xsp  = (W - pad * 2) / max(cols - 1, 1)
    ysp  = 46
    y0   = 60

    pos = [(int(pad + (i % cols) * xsp), int(y0 + (i // cols) * ysp), c)
           for i, c in enumerate(counts)]

    SCX = W // 2
    SCY = H - 52   # Y fixo da nave — nunca muda

    def nt(t): return f"{t / LOOP_DUR:.4f}"

    # ── Estrelas ───────────────────────────────────────────────────────────
    stars = []
    for _ in range(55):
        x = rng.randint(4, W-4); y = rng.randint(32, H-32)
        r = rng.choice([0.5, 0.8, 1.0])
        o = round(rng.uniform(0.2, 0.7), 2)
        d = round(rng.uniform(1.5, 4.0), 1)
        stars.append(
            f'<circle cx="{x}" cy="{y}" r="{r}" fill="white" opacity="{o}">'
            f'<animate attributeName="opacity" values="{o};{round(o*0.2,2)};{o}"'
            f' dur="{d}s" repeatCount="indefinite"/></circle>')

    # ── Aliens ─────────────────────────────────────────────────────────────
    # Estrutura por alien:
    #   <g opacity>            ← controla fade-in e fade-out (destruição)
    #     <g>                  ← controla entrada Y (cai do topo)
    #       [animateTransform Y]
    #       <g>                ← controla hover Y
    #         [animateTransform Y hover]
    #         [art + label]
    #       </g>
    #     </g>
    #   </g>
    alien_els = []
    for idx, (ax, ay, c) in enumerate(pos):
        ed   = idx * 0.11          # enter delay
        edur = 0.50
        hb   = ed + edur           # hover begin
        hit  = ENTER_DUR + idx * SHOOT_GAP + 0.48
        col  = alien_color(c, max_c)
        art  = alien_art(ax, ay, c, max_c)
        ly   = ay + AH * S // 2 + 10

        alien_els.append(
            f'<g opacity="0">'
              f'<animate attributeName="opacity" values="0;1"'
              f' dur="0.2s" begin="{ed:.2f}s" fill="freeze"/>'
              f'<animate attributeName="opacity" values="1;1;0.1;1;0.1;0"'
              f' keyTimes="0;0.5;0.62;0.74;0.86;1"'
              f' dur="0.48s" begin="{hit:.2f}s" fill="freeze"/>'
              f'<g>'
                f'<animateTransform attributeName="transform" type="translate"'
                f' values="0,{-(ay+24)};0,0"'
                f' dur="{edur}s" begin="{ed:.2f}s" fill="freeze"'
                f' calcMode="spline" keySplines="0.25 0 0.4 1"/>'
                f'<g>'
                  f'<animateTransform attributeName="transform" type="translate"'
                  f' values="0,0;0,-4;0,0" dur="2.0s" begin="{hb:.2f}s"'
                  f' repeatCount="indefinite"'
                  f' calcMode="spline" keySplines="0.4 0 0.6 1;0.4 0 0.6 1"/>'
                  + art +
                  f'<text x="{ax}" y="{ly}" font-family="monospace" font-size="6"'
                  f' fill="{col}" opacity="0.55" text-anchor="middle">{c}</text>'
                f'</g>'
              f'</g>'
            f'</g>')

    # ── Nave ───────────────────────────────────────────────────────────────
    # Outer g: posição Y FIXA em SCY — nave sempre visível no eixo Y correto
    # Inner g: anima apenas X (patrulha e mira)
    kx     = [SCX - 70, SCX + 70, SCX]
    ktimes = [0.0, ENTER_DUR * 0.55, ENTER_DUR]
    for idx, (ax, ay, c) in enumerate(pos):
        ta = ENTER_DUR + idx * SHOOT_GAP
        kx     += [ax, ax, ax]
        ktimes += [ta, ta + 0.3, ta + 0.4]
    kx.append(SCX);  ktimes.append(LOOP_DUR)

    kv_str = ";".join(str(x) for x in kx)
    kt_str = ";".join(nt(t) for t in ktimes)
    ks_str = ";".join("0.4 0 0.6 1" for _ in range(len(kx) - 1))

    ship_el = (
        f'<g transform="translate(0,{SCY})">'          # Y fixo
          f'<g>'                                        # X animado
            f'<animateTransform attributeName="transform" type="translate"'
            f' values="{kv_str}" keyTimes="{kt_str}"'
            f' dur="{LOOP_DUR}s" repeatCount="indefinite"'
            f' calcMode="spline" keySplines="{ks_str}"/>'
            + ship_art() +
          f'</g>'
        f'</g>')

    # ── Bullets ────────────────────────────────────────────────────────────
    # Bullet sai de (ax, SCY - topo_nave) e vai até (ax, ay + base_alien)
    bullets = []
    for idx, (ax, ay, c) in enumerate(pos):
        tf  = ENTER_DUR + idx * SHOOT_GAP
        by0 = -(SH * S // 2) - 4   # relativo ao SCY (topo da nave)
        by1 = ay + AH * S // 2     # posição absoluta do centro do alien

        # Bullet: g com translate Y=SCY, rect animado em Y relativo
        bullets.append(
            f'<g transform="translate({ax},{SCY})">'
              f'<rect x="-1" y="{by0}" width="2" height="6" fill="{GREEN}" opacity="0">'
              f'<animate attributeName="opacity" values="0;1;1;0"'
              f' keyTimes="0;0.05;0.88;1" dur="0.48s" begin="{tf:.2f}s" fill="freeze"/>'
              f'<animate attributeName="y" values="{by0};{by1 - SCY}"'
              f' dur="0.48s" begin="{tf:.2f}s" fill="freeze"'
              f' calcMode="spline" keySplines="0.15 0 0.3 1"/>'
              f'</rect>'
            f'</g>')

    # ── Explosões ──────────────────────────────────────────────────────────
    expls = [explosion_svg(ax, ay, ENTER_DUR + i * SHOOT_GAP + 0.48)
             for i, (ax, ay, c) in enumerate(pos)]

    # ── Vidas ──────────────────────────────────────────────────────────────
    lives = "".join(
        f'<g transform="translate({14 + i * 22},{H - 16}) scale(0.6)">{ship_art()}</g>'
        for i in range(3))

    # ── HUD ────────────────────────────────────────────────────────────────
    score = total * 150
    hud = (
        f'<text x="14" y="20" font-family="monospace" font-size="8" fill="{GREEN}">CONTRIBUTIONS INVASION</text>'
        f'<text x="{W//2}" y="20" font-family="monospace" font-size="8" fill="{CYAN}"'
        f' text-anchor="middle">TOTAL: {total}</text>'
        f'<text x="{W-14}" y="20" font-family="monospace" font-size="8" fill="{YELLOW}"'
        f' text-anchor="end">SCORE {score:07d}</text>'
        f'<line x1="0" y1="27" x2="{W}" y2="27" stroke="{GREEN}" stroke-width="0.5" opacity="0.3"/>'
        f'<line x1="0" y1="{H-27}" x2="{W}" y2="{H-27}" stroke="{GREEN}" stroke-width="0.5" opacity="0.3"/>'
        f'<text x="{W//2}" y="{H-10}" font-family="monospace" font-size="6" fill="#333"'
        f' text-anchor="middle">LAST 20 WEEKS  •  @{USERNAME}  •  WAVE 01</text>')

    return (
        f'<svg xmlns="http://www.w3.org/2000/svg"'
        f' width="{W}" height="{H}" viewBox="0 0 {W} {H}"'
        f' style="border-radius:8px;display:block;">'
        f'<rect width="{W}" height="{H}" fill="{BG}" rx="8"/>'
        f'<pattern id="sc" width="1" height="4" patternUnits="userSpaceOnUse">'
        f'<rect y="3" width="{W}" height="1" fill="rgba(0,0,0,0.1)"/></pattern>'
        f'<rect width="{W}" height="{H}" fill="url(#sc)" rx="8"/>'
        + "".join(stars)
        + "".join(alien_els)
        + "".join(bullets)
        + "".join(expls)
        + ship_el
        + lives
        + hud
        + '</svg>')

# ── Main ───────────────────────────────────────────────────────────────────
def main():
    print(f"Gerando Galaga SVG para @{USERNAME}...")
    weeks, total = fetch()
    if not weeks:
        print("Modo demo."); weeks, total = demo()
    svg = build(weeks, total)
    with open(OUT_FILE, "w", encoding="utf-8") as f:
        f.write(svg)
    print(f"OK — {OUT_FILE} ({len(svg)//1024} KB) | contribuições: {total}")

if __name__ == "__main__":
    main()
