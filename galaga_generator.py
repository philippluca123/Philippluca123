"""
galaga_generator.py  v4  —  SVG cinemático Galaga
Fix: dois <g> aninhados por alien (entrada + hover separados)
"""
import os, math, random, requests

USERNAME = os.environ.get("GITHUB_USERNAME", "philippluca123")
GH_TOKEN = os.environ.get("GITHUB_TOKEN", "")
OUT_FILE = "galaga-contributions.svg"
HEADERS  = {"Authorization": f"Bearer {GH_TOKEN}"} if GH_TOKEN else {}

W, H      = 800, 400
BG        = "#0a0a0f"
GREEN     = "#39ff14"
CYAN      = "#00ffff"
PINK      = "#ff2d78"
YELLOW    = "#ffe600"
PURPLE    = "#b84fff"
ORANGE    = "#ff8c00"
LOOP_DUR  = 22
ENTER_END = 3.5
SHOOT_GAP = 1.1
S         = 2   # pixel size

# ── API ───────────────────────────────────────────────────────────────────
def fetch_contributions():
    q = """query($l:String!){user(login:$l){contributionsCollection{
      contributionCalendar{totalContributions
      weeks{contributionDays{contributionCount}}}}}}"""
    try:
        r = requests.post("https://api.github.com/graphql",
            json={"query":q,"variables":{"l":USERNAME}},
            headers=HEADERS, timeout=10)
        cal = r.json()["data"]["user"]["contributionsCollection"]["contributionCalendar"]
        return cal["weeks"], cal["totalContributions"]
    except Exception as e:
        print(f"API: {e}"); return [], 0

def demo_weeks():
    rng = random.Random(7)
    wks = [{"contributionDays":[{"contributionCount":rng.randint(0,14)} for _ in range(7)]} for _ in range(26)]
    return wks, sum(d["contributionCount"] for w in wks for d in w["contributionDays"])

# ── Pixel art ─────────────────────────────────────────────────────────────
def rects(pixels, fill, ox, oy):
    return "".join(f'<rect x="{ox+c*S}" y="{oy+r*S}" width="{S}" height="{S}" fill="{fill}"/>'
                   for c,r in pixels)

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
AW, AH = 8, 7   # alien width/height in pixel units

SHIP_PX = [(3,0),(4,0),(2,1),(3,1),(4,1),(5,1),(1,2),(2,2),(3,2),(4,2),(5,2),(6,2),
           (0,3),(1,3),(2,3),(3,3),(4,3),(5,3),(6,3),(7,3),(1,4),(2,4),(5,4),(6,4)]
SW, SH = 8, 5   # ship width/height in pixel units

def alien_art(cx, cy, count, max_c):
    ox = cx - AW*S//2
    oy = cy - AH*S//2
    r  = count/max_c if max_c else 0
    if r < 0.35:   return rects(A_BODY, PURPLE, ox, oy)
    elif r < 0.70: return rects(B_BODY, CYAN,   ox, oy)
    else:          return rects(C_BODY, GREEN, ox, oy) + rects(C_EYES, CYAN, ox, oy)

def ship_art(cx, cy):
    ox = cx - SW*S//2
    oy = cy - SH*S//2
    return rects(SHIP_PX, CYAN, ox, oy) + rects([(3,0),(4,0)], YELLOW, ox, oy)

def explosion(cx, cy, eid, t0):
    out = []
    for i,(col,r1) in enumerate([(YELLOW,6),(ORANGE,10),(PINK,14)]):
        t = t0 + i*0.09
        out.append(
            f'<circle cx="{cx}" cy="{cy}" r="2" fill="{col}" opacity="0">'
            f'<animate attributeName="r" values="2;{r1}" dur="0.35s" begin="{t:.2f}s" fill="freeze"/>'
            f'<animate attributeName="opacity" values="0;0.95;0" keyTimes="0;0.15;1"'
            f' dur="0.35s" begin="{t:.2f}s" fill="freeze"/></circle>')
    return "".join(out)

# ── Build ─────────────────────────────────────────────────────────────────
def build_svg(weeks, total):
    rng = random.Random(42)

    counts = [sum(d["contributionCount"] for d in w["contributionDays"]) for w in weeks[-20:]]
    while len(counts) < 5: counts.append(1)
    counts = counts[-20:]
    max_c  = max(counts) if any(counts) else 1
    N      = len(counts)
    cols   = min(N, 10)
    rows   = math.ceil(N/cols)

    pad    = 70
    ex_sp  = (W - pad*2) / max(cols-1, 1)
    ey_sp  = 46
    ey0    = 58

    pos = []
    for i,c in enumerate(counts):
        ax = int(pad + (i%cols)*ex_sp)
        ay = int(ey0 + (i//cols)*ey_sp)
        pos.append((ax, ay, c))

    SCY = H - 52

    # Stars
    stars = []
    for _ in range(55):
        x=rng.randint(2,W-2); y=rng.randint(32,H-32)
        r=rng.choice([0.5,0.8,1.0]); o=round(rng.uniform(0.2,0.7),2); d=round(rng.uniform(1.5,4),1)
        stars.append(f'<circle cx="{x}" cy="{y}" r="{r}" fill="white" opacity="{o}">'
                     f'<animate attributeName="opacity" values="{o};{round(o*0.2,2)};{o}"'
                     f' dur="{d}s" repeatCount="indefinite"/></circle>')

    # Aliens — dois <g> aninhados: outer=entrada (translate Y), inner=hover (translate Y offset)
    alien_els = []
    for idx,(ax,ay,c) in enumerate(pos):
        ed  = idx * 0.11          # enter delay
        edur = 0.5
        hb  = ed + edur           # hover begin
        hit = ENTER_END + idx*SHOOT_GAP + 0.5

        col = PURPLE if c/max_c<0.35 else (CYAN if c/max_c<0.7 else GREEN)
        art = alien_art(ax, ay, c, max_c)
        lbl_y = ay + AH*S//2 + 10

        alien_els.append(f"""
<g opacity="0">
  <!-- outer: entrada de cima -->
  <animate attributeName="opacity" values="0;1" dur="0.2s" begin="{ed:.2f}s" fill="freeze"/>
  <!-- fade ao ser destruído -->
  <animate attributeName="opacity" values="1;1;0.1;1;0.1;0"
    keyTimes="0;0.55;0.65;0.72;0.82;1"
    dur="0.5s" begin="{hit:.2f}s" fill="freeze"/>
  <g>
    <animateTransform attributeName="transform" type="translate"
      values="0,{-(ay+20)};0,0"
      dur="{edur}s" begin="{ed:.2f}s" fill="freeze"
      calcMode="spline" keySplines="0.25 0 0.4 1"/>
    <g>
      <!-- inner: hover após entrar -->
      <animateTransform attributeName="transform" type="translate"
        values="0,0;0,-4;0,0" dur="2.1s" begin="{hb:.2f}s"
        repeatCount="indefinite"
        calcMode="spline" keySplines="0.4 0 0.6 1;0.4 0 0.6 1"/>
      {art}
      <text x="{ax}" y="{lbl_y}" font-family="monospace" font-size="6"
        fill="{col}" opacity="0.55" text-anchor="middle">{c}</text>
    </g>
  </g>
</g>""")

    # Nave: keyframes X ao longo do tempo
    scx = W//2
    def kpt(x): return f"{x},{SCY}"
    kx = [kpt(scx-70), kpt(scx+70), kpt(scx)]
    kt = [0.0, ENTER_END*0.55, ENTER_END]
    for idx,(ax,ay,c) in enumerate(pos):
        ta = ENTER_END + idx*SHOOT_GAP
        kx += [kpt(ax), kpt(ax), kpt(ax)]
        kt += [ta, ta+0.35, ta+0.45]
    kx.append(kpt(scx)); kt.append(float(LOOP_DUR))

    def nt(t): return f"{t/LOOP_DUR:.4f}"
    kv = ";".join(kx)
    kts = ";".join(nt(t) for t in kt)
    ks  = ";".join("0.4 0 0.6 1" for _ in range(len(kx)-1))

    ship_el = (f'<g><animateTransform attributeName="transform" type="translate"'
               f' values="{kv}" keyTimes="{kts}" dur="{LOOP_DUR}s"'
               f' repeatCount="indefinite" calcMode="spline" keySplines="{ks}"/>'
               f'{ship_art(0, 0)}</g>')

    # Bullets
    bullets = []
    for idx,(ax,ay,c) in enumerate(pos):
        tf = ENTER_END + idx*SHOOT_GAP
        by0 = SCY - SH*S
        by1 = ay + AH*S//2
        bullets.append(
            f'<rect x="{ax-1}" y="{by0}" width="2" height="7" fill="{GREEN}" opacity="0">'
            f'<animate attributeName="opacity" values="0;1;1;0"'
            f' keyTimes="0;0.05;0.88;1" dur="0.5s" begin="{tf:.2f}s" fill="freeze"/>'
            f'<animate attributeName="y" values="{by0};{by1}"'
            f' dur="0.5s" begin="{tf:.2f}s" fill="freeze"'
            f' calcMode="spline" keySplines="0.15 0 0.35 1"/></rect>')

    # Explosions
    expls = [explosion(ax, ay, i, ENTER_END+i*SHOOT_GAP+0.5) for i,(ax,ay,c) in enumerate(pos)]

    # Lives
    lives = "".join(f'<g transform="translate({14+i*22},{H-18}) scale(0.62)">{ship_art(0,0)}</g>'
                    for i in range(3))

    score = total * 150
    hud = (f'<text x="14" y="20" font-family="monospace" font-size="8" fill="{GREEN}">CONTRIBUTIONS INVASION</text>'
           f'<text x="{W//2}" y="20" font-family="monospace" font-size="8" fill="{CYAN}" text-anchor="middle">TOTAL: {total}</text>'
           f'<text x="{W-14}" y="20" font-family="monospace" font-size="8" fill="{YELLOW}" text-anchor="end">SCORE {score:07d}</text>'
           f'<line x1="0" y1="27" x2="{W}" y2="27" stroke="{GREEN}" stroke-width="0.5" opacity="0.3"/>'
           f'<line x1="0" y1="{H-27}" x2="{W}" y2="{H-27}" stroke="{GREEN}" stroke-width="0.5" opacity="0.3"/>'
           f'<text x="{W//2}" y="{H-10}" font-family="monospace" font-size="6" fill="#333" text-anchor="middle">LAST 20 WEEKS  •  @{USERNAME}  •  WAVE 01</text>')

    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}"'
            f' viewBox="0 0 {W} {H}" style="border-radius:8px;display:block;">'
            f'<rect width="{W}" height="{H}" fill="{BG}" rx="8"/>'
            f'<pattern id="sc" width="1" height="4" patternUnits="userSpaceOnUse">'
            f'<rect y="3" width="{W}" height="1" fill="rgba(0,0,0,0.1)"/></pattern>'
            f'<rect width="{W}" height="{H}" fill="url(#sc)" rx="8"/>'
            + "".join(stars)
            + "".join(alien_els)
            + "".join(bullets)
            + "".join(expls)
            + ship_el + lives + hud + '</svg>')

def main():
    print(f"Galaga SVG para @{USERNAME}...")
    weeks, total = fetch_contributions()
    if not weeks:
        print("Modo demo."); weeks, total = demo_weeks()
    svg = build_svg(weeks, total)
    with open(OUT_FILE,"w",encoding="utf-8") as f: f.write(svg)
    print(f"OK: {OUT_FILE} ({len(svg)//1024}KB) total={total}")

if __name__ == "__main__":
    main()
