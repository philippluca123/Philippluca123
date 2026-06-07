"""
galaga_generator.py  —  SVG cinemático estilo Galaga
Coreografia completa: formação entra, nave mira, atira, alien explode, some.
Puro SMIL/CSS — sem JavaScript — compatível com GitHub.
"""

import os, math, random, requests
from datetime import datetime, timedelta

USERNAME  = os.environ.get("GITHUB_USERNAME", "philippluca123")
GH_TOKEN  = os.environ.get("GITHUB_TOKEN", "")
OUT_FILE  = "galaga-contributions.svg"
HEADERS   = {"Authorization": f"Bearer {GH_TOKEN}"} if GH_TOKEN else {}

# ── canvas ────────────────────────────────────────────────────────────────────
W, H = 800, 400

# ── palette ───────────────────────────────────────────────────────────────────
BG      = "#0a0a0f"
GREEN   = "#39ff14"
CYAN    = "#00ffff"
PINK    = "#ff2d78"
YELLOW  = "#ffe600"
PURPLE  = "#b84fff"
ORANGE  = "#ff8c00"

# ── timing helpers ────────────────────────────────────────────────────────────
# Toda a coreografia é orquestrada em segundos.
# O SVG faz loop a cada LOOP_DUR segundos.
LOOP_DUR   = 18          # duração total do loop cinemático
ENTER_END  = 3.0         # aliens terminam de entrar
SHOOT_GAP  = 1.1         # intervalo entre cada tiro/explosão
HUD_FADE   = 0.6         # fade in do HUD

# ── GitHub API ─────────────────────────────────────────────────────────────────
def fetch_contributions():
    q = """query($login:String!){user(login:$login){contributionsCollection{
      contributionCalendar{totalContributions weeks{contributionDays{
      contributionCount date}}}}}}"""
    try:
        r = requests.post("https://api.github.com/graphql",
                          json={"query": q, "variables": {"login": USERNAME}},
                          headers=HEADERS, timeout=10)
        cal = r.json()["data"]["user"]["contributionsCollection"]["contributionCalendar"]
        return cal["weeks"], cal["totalContributions"]
    except:
        return [], 0

def demo_weeks():
    rng = random.Random(7)
    weeks = []
    for _ in range(26):
        weeks.append({"contributionDays": [
            {"contributionCount": rng.randint(0,14), "date": "2024-01-01"}
            for _ in range(7)]})
    return weeks, sum(d["contributionCount"] for w in weeks for d in w["contributionDays"])

# ── pixel shapes (strings SVG inline) ─────────────────────────────────────────
def px(rects, fill, ox=0, oy=0, scale=1):
    """rects = lista de (x,y,w,h) em pixels de 2px base."""
    out = []
    for (x,y,ww,hh) in rects:
        rx = ox + x*scale
        ry = oy + y*scale
        out.append(f'<rect x="{rx}" y="{ry}" width="{ww*scale}" height="{hh*scale}" fill="{fill}"/>')
    return "".join(out)

ALIEN_A = [  # inseto — baixa contribuição
    (3,0,2,2),(2,2,4,2),(1,4,6,2),(0,6,8,2),(1,8,2,2),(5,8,2,2),
    (0,2,1,4),(7,2,1,4),
]
ALIEN_B = [  # borboleta — média
    (3,0,2,4),(1,2,6,2),(0,4,8,2),(1,6,2,2),(5,6,2,2),(2,8,4,2),
    (-1,3,2,3),(8,3,2,3),
]
ALIEN_C = [  # boss — alta contribuição
    (2,0,4,2),(1,2,6,2),(0,4,10,2),(0,6,10,2),(1,8,3,2),(6,8,3,2),
    (2,2,2,2),(6,2,2,2),   # olhos cyan
]

SHIP_RECTS = [
    (3,0,2,2),(2,2,4,2),(1,4,6,2),(0,6,8,2),(1,8,2,2),(5,8,2,2),
]

def alien_shape(ox, oy, count, max_c, aid):
    s = 2
    if count == 0:
        kind, fill, eye = ALIEN_A, PURPLE, None
    elif count / max_c < 0.45:
        kind, fill, eye = ALIEN_A, PURPLE, None
    elif count / max_c < 0.75:
        kind, fill, eye = ALIEN_B, CYAN, None
    else:
        kind, fill, eye = ALIEN_C, GREEN, CYAN

    body = px(kind, fill, ox, oy, s)
    if kind is ALIEN_C:
        # olhos em cyan separados
        eyes = px([(2,2,2,2),(6,2,2,2)], CYAN, ox, oy, s)
    else:
        eyes = ""
    return body + eyes

def ship_shape(cx, cy):
    s = 2
    ox = cx - 4*s
    oy = cy - 5*s
    body = px(SHIP_RECTS, CYAN, ox, oy, s)
    cockpit = px([(3,1,2,1)], YELLOW, ox, oy, s)
    return body + cockpit

def explosion(cx, cy, eid, begin, fill=YELLOW):
    """Explosão em 4 frames SMIL — expande e some."""
    frames = [
        (4,  4,  fill,   0.00),
        (10, 10, ORANGE, 0.08),
        (16, 16, PINK,   0.16),
        (20, 20, fill,   0.24),
    ]
    parts = []
    for i,(fw,fh,fc,offset) in enumerate(frames):
        t0 = begin + offset
        t1 = t0 + 0.18
        t2 = t1 + 0.18
        parts.append(f"""
<rect id="exp{eid}f{i}" x="{cx-fw//2}" y="{cy-fh//2}"
  width="{fw}" height="{fh}" fill="{fc}" opacity="0" rx="2">
  <animate attributeName="opacity" values="0;1;0"
    keyTimes="0;0.4;1" dur="0.4s" begin="{t0:.2f}s" fill="freeze"
    calcMode="spline" keySplines="0 0 1 1;0 0 1 1"/>
</rect>""")
    return "".join(parts)

# ── SVG builder ────────────────────────────────────────────────────────────────
def build_svg(weeks, total):
    rng = random.Random(42)

    # Pega dados das últimas 20 semanas com atividade (máx 20 aliens)
    active = []
    for w in weeks[-24:]:
        c = sum(d["contributionCount"] for d in w["contributionDays"])
        active.append(c)
    while len(active) < 4:
        active.append(0)
    active = active[-20:]
    max_c = max(active) if any(active) else 1

    N = len(active)
    cols = min(N, 10)
    rows = math.ceil(N / cols)

    # Posições finais da formação
    spacing_x = 60
    spacing_y = 46
    form_w = (cols - 1) * spacing_x
    form_start_x = (W - form_w) // 2
    form_start_y = 55

    aliens = []   # (cx, cy, count, idx)
    for i, c in enumerate(active):
        col = i % cols
        row = i // cols
        cx = form_start_x + col * spacing_x
        cy = form_start_y + row * spacing_y
        aliens.append((cx, cy, c, i))

    ship_cx = W // 2
    ship_cy = H - 48

    # ── Estrelas ──────────────────────────────────────────────────────────────
    stars_svg = []
    for _ in range(55):
        sx = rng.randint(0, W)
        sy = rng.randint(0, H)
        sr = rng.choice([0.6, 0.8, 1.0])
        so = rng.uniform(0.25, 0.8)
        sd = rng.uniform(1.2, 3.5)
        stars_svg.append(
            f'<circle cx="{sx}" cy="{sy}" r="{sr}" fill="white" opacity="{so:.2f}">'
            f'<animate attributeName="opacity" values="{so:.2f};{so*0.25:.2f};{so:.2f}" '
            f'dur="{sd:.1f}s" repeatCount="indefinite"/></circle>')

    # ── Formação de aliens entrando de cima ────────────────────────────────────
    alien_svgs = []
    for (cx, cy, count, idx) in aliens:
        delay = 0.08 * idx  # entram em cascata
        enter_dur = 0.55

        col = PURPLE if count / max_c < 0.45 else (CYAN if count / max_c < 0.75 else GREEN)

        # Entrada: vem do topo (-30) até posição final
        anim_enter = (
            f'<animateTransform attributeName="transform" type="translate" '
            f'values="0,-{cy+30};0,0" dur="{enter_dur:.2f}s" begin="{delay:.2f}s" '
            f'fill="freeze" calcMode="spline" keySplines="0.2 0 0.4 1"/>'
            # opacidade fade-in
        )
        anim_fade = (
            f'<animate attributeName="opacity" values="0;1" '
            f'dur="0.25s" begin="{delay:.2f}s" fill="freeze"/>'
        )

        # Hover suave depois que entra
        hover_begin = delay + enter_dur
        hover_anim = (
            f'<animateTransform attributeName="transform" type="translate" '
            f'values="0,0;0,-4;0,0" dur="2.2s" begin="{hover_begin:.2f}s" '
            f'repeatCount="indefinite" additive="sum" calcMode="spline" '
            f'keySplines="0.4 0 0.6 1;0.4 0 0.6 1"/>'
        )

        # Ser atingido: flash branco + sumir
        shoot_begin = ENTER_END + idx * SHOOT_GAP
        hit_begin   = shoot_begin + 0.55  # instante que o tiro chega

        flash = (
            f'<animate attributeName="opacity" values="1;1;0.2;1;0.2;1;0" '
            f'keyTimes="0;0.6;0.65;0.7;0.75;0.8;1" '
            f'dur="0.5s" begin="{hit_begin:.2f}s" fill="freeze"/>'
        )

        shape = alien_shape(0, 0, count, max_c, idx)

        alien_svgs.append(f"""
<g opacity="0" transform="translate({cx},{cy})">
  {anim_enter}{anim_fade}{hover_anim}{flash}
  {shape}
  <text x="9" y="24" font-family="monospace" font-size="6"
    fill="{col}88" text-anchor="middle">{count}</text>
</g>""")

    # ── Nave: patrulha → mira em cada alien → patrulha ──────────────────────
    # Posições x da nave ao longo do tempo
    # 0..ENTER_END: patrulha lenta
    # depois: vai até cx de cada alien em sequência
    ship_keyframes_x = []
    ship_keyframes_t = []

    # patrulha inicial
    ship_keyframes_x += [ship_cx - 60, ship_cx + 60, ship_cx]
    ship_keyframes_t += [0, ENTER_END * 0.5, ENTER_END]

    for idx, (cx, cy, count, _) in enumerate(aliens):
        t_aim  = ENTER_END + idx * SHOOT_GAP
        t_back = t_aim + 0.5
        ship_keyframes_x += [cx, cx]
        ship_keyframes_t += [t_aim, t_back]

    # volta ao centro no fim do loop
    ship_keyframes_x.append(ship_cx)
    ship_keyframes_t.append(LOOP_DUR)

    total_dur = LOOP_DUR
    def norm(t): return f"{t/total_dur:.4f}"

    kv = ";".join(str(x) for x in ship_keyframes_x)
    kt = ";".join(norm(t) for t in ship_keyframes_t)
    ks = ";".join("0.4 0 0.6 1" for _ in range(len(ship_keyframes_x)-1))

    ship_anim = (
        f'<animateTransform attributeName="transform" type="translate" '
        f'values="{kv}" keyTimes="{kt}" '
        f'dur="{total_dur}s" repeatCount="indefinite" '
        f'calcMode="spline" keySplines="{ks}" additive="replace"/>'
    )

    ship_svg_el = f"""
<g transform="translate(0,{ship_cy})">
  {ship_anim}
  {ship_shape(0, 0)}
</g>"""

    # ── Projéteis: um tiro por alien ──────────────────────────────────────────
    bullets_svg = []
    for idx, (cx, cy, count, _) in enumerate(aliens):
        t_fire = ENTER_END + idx * SHOOT_GAP
        travel = 0.55   # segundos até o alien
        dist   = ship_cy - cy - 20

        bullets_svg.append(f"""
<rect x="{cx-1}" y="{ship_cy - 18}" width="2" height="8" fill="{GREEN}" opacity="0">
  <animate attributeName="opacity" values="0;1;1;0"
    keyTimes="0;0.01;0.9;1" dur="{travel:.2f}s"
    begin="{t_fire:.2f}s" fill="freeze"/>
  <animate attributeName="y"
    values="{ship_cy-18};{cy+10}"
    dur="{travel:.2f}s" begin="{t_fire:.2f}s" fill="freeze"
    calcMode="spline" keySplines="0.2 0 0.5 1"/>
</rect>""")

    # ── Explosões ─────────────────────────────────────────────────────────────
    expl_svg = []
    for idx, (cx, cy, count, _) in enumerate(aliens):
        hit = ENTER_END + idx * SHOOT_GAP + 0.55
        col = PURPLE if count/max_c < 0.45 else (CYAN if count/max_c < 0.75 else GREEN)
        expl_svg.append(explosion(cx + 9, cy + 10, idx, hit, col))

    # ── HUD ───────────────────────────────────────────────────────────────────
    score = total * 150
    hud = f"""
<text x="12" y="20" font-family="monospace" font-size="8" fill="{GREEN}" opacity="0.85">
  CONTRIBUTIONS INVASION
  <animate attributeName="opacity" values="0;0.85" dur="{HUD_FADE}s" fill="freeze"/>
</text>
<text x="{W//2}" y="20" font-family="monospace" font-size="8" fill="{CYAN}"
  text-anchor="middle">TOTAL: {total}
  <animate attributeName="opacity" values="0;1" dur="{HUD_FADE}s" fill="freeze"/>
</text>
<text x="{W-12}" y="20" font-family="monospace" font-size="8" fill="{YELLOW}"
  text-anchor="end">SCORE {score:07d}
  <animate attributeName="opacity" values="0;1" dur="{HUD_FADE}s" fill="freeze"/>
</text>
<line x1="0" y1="28" x2="{W}" y2="28" stroke="{GREEN}" stroke-width="0.5" opacity="0.35"/>
<line x1="0" y1="{H-28}" x2="{W}" y2="{H-28}" stroke="{GREEN}" stroke-width="0.5" opacity="0.35"/>
<text x="{W//2}" y="{H-10}" font-family="monospace" font-size="6" fill="#333"
  text-anchor="middle">LAST 20 WEEKS  •  @{USERNAME}  •  WAVE 01</text>"""

    # ── Vidas (3 mini-naves) ──────────────────────────────────────────────────
    lives = ""
    for li in range(3):
        lx = 14 + li * 22
        ly = H - 22
        lives += f"""
<g transform="translate({lx},{ly}) scale(0.7)">
  {ship_shape(0, 0)}
</g>"""

    # ── Monta tudo ────────────────────────────────────────────────────────────
    svg = f"""<svg xmlns="http://www.w3.org/2000/svg"
  width="{W}" height="{H}" viewBox="0 0 {W} {H}"
  style="border-radius:8px; display:block;">

  <!-- bg -->
  <rect width="{W}" height="{H}" fill="{BG}" rx="8"/>

  <!-- scanlines -->
  <pattern id="scan" width="1" height="4" patternUnits="userSpaceOnUse">
    <rect y="3" width="{W}" height="1" fill="rgba(0,0,0,0.12)"/>
  </pattern>
  <rect width="{W}" height="{H}" fill="url(#scan)" rx="8"/>

  <!-- stars -->
  {"".join(stars_svg)}

  <!-- aliens -->
  {"".join(alien_svgs)}

  <!-- bullets -->
  {"".join(bullets_svg)}

  <!-- explosions -->
  {"".join(expl_svg)}

  <!-- ship -->
  {ship_svg_el}

  <!-- lives -->
  {lives}

  <!-- hud -->
  {hud}
</svg>"""

    return svg

# ── main ──────────────────────────────────────────────────────────────────────
def main():
    print(f"Gerando Galaga SVG cinemático para @{USERNAME}...")
    weeks, total = fetch_contributions()
    if not weeks:
        print("Sem token — usando dados demo.")
        weeks, total = demo_weeks()

    svg = build_svg(weeks, total)
    with open(OUT_FILE, "w", encoding="utf-8") as f:
        f.write(svg)
    print(f"Gerado: {OUT_FILE}  ({len(svg)//1024} KB)  |  contribuições: {total}")

if __name__ == "__main__":
    main()
