"""
galaga_generator.py
Busca contribuições do GitHub via API e gera um SVG animado estilo Galaga.
Aliens = dias com commits. Nave = defende o repositório.
"""

import os
import json
import math
import random
import requests
from datetime import datetime, timedelta

GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN", "")
USERNAME = os.environ.get("GITHUB_USERNAME", "philippluca123")
OUTPUT_FILE = "galaga-contributions.svg"

HEADERS = {"Authorization": f"Bearer {GITHUB_TOKEN}"} if GITHUB_TOKEN else {}

W, H = 800, 420
BG = "#0a0a0f"
GREEN = "#39ff14"
CYAN = "#00ffff"
PINK = "#ff2d78"
YELLOW = "#ffe600"
PURPLE = "#b84fff"


def fetch_contributions():
    """Busca os últimos 52 semanas de contribuições via GraphQL."""
    query = """
    query($login: String!) {
      user(login: $login) {
        contributionsCollection {
          contributionCalendar {
            totalContributions
            weeks {
              contributionDays {
                contributionCount
                date
              }
            }
          }
        }
      }
    }
    """
    try:
        r = requests.post(
            "https://api.github.com/graphql",
            json={"query": query, "variables": {"login": USERNAME}},
            headers=HEADERS,
            timeout=10,
        )
        data = r.json()
        cal = data["data"]["user"]["contributionsCollection"]["contributionCalendar"]
        return cal["weeks"], cal["totalContributions"]
    except Exception as e:
        print(f"Erro ao buscar contribuições: {e}")
        return [], 0


def contribution_color(count):
    if count == 0:
        return "#111820"
    elif count <= 2:
        return "#0d3320"
    elif count <= 5:
        return "#1a5c38"
    elif count <= 10:
        return "#25a244"
    else:
        return GREEN


def alien_svg(x, y, color, kind=0, size=14):
    """Retorna SVG de alien pixelado estilo Galaga."""
    s = size / 14
    if kind == 0:
        # Alien tipo inseto
        return f"""
        <g transform="translate({x},{y}) scale({s})">
          <rect x="-1" y="-7" width="2" height="14" fill="{color}"/>
          <rect x="-3" y="-5" width="6" height="2" fill="{color}"/>
          <rect x="-5" y="-3" width="10" height="2" fill="{color}"/>
          <rect x="-7" y="-1" width="14" height="4" fill="{color}"/>
          <rect x="-5" y="3" width="4" height="2" fill="{color}"/>
          <rect x="1" y="3" width="4" height="2" fill="{color}"/>
          <rect x="-3" y="5" width="2" height="2" fill="{color}"/>
          <rect x="1" y="5" width="2" height="2" fill="{color}"/>
          <rect x="-9" y="-3" width="2" height="4" fill="{color}"/>
          <rect x="7" y="-3" width="2" height="4" fill="{color}"/>
        </g>"""
    elif kind == 1:
        # Alien tipo borboleta
        return f"""
        <g transform="translate({x},{y}) scale({s})">
          <rect x="-2" y="-6" width="4" height="12" fill="{color}"/>
          <rect x="-6" y="-4" width="12" height="2" fill="{color}"/>
          <rect x="-8" y="-2" width="16" height="4" fill="{color}"/>
          <rect x="-6" y="2" width="4" height="2" fill="{color}"/>
          <rect x="2" y="2" width="4" height="2" fill="{color}"/>
          <rect x="-10" y="-2" width="2" height="2" fill="{color}"/>
          <rect x="8" y="-2" width="2" height="2" fill="{color}"/>
        </g>"""
    else:
        # Boss alien
        return f"""
        <g transform="translate({x},{y}) scale({s})">
          <rect x="-3" y="-8" width="6" height="2" fill="{color}"/>
          <rect x="-5" y="-6" width="10" height="2" fill="{color}"/>
          <rect x="-7" y="-4" width="14" height="6" fill="{color}"/>
          <rect x="-9" y="-2" width="2" height="4" fill="{color}"/>
          <rect x="7" y="-2" width="2" height="4" fill="{color}"/>
          <rect x="-5" y="2" width="10" height="2" fill="{color}"/>
          <rect x="-7" y="4" width="4" height="2" fill="{color}"/>
          <rect x="3" y="4" width="4" height="2" fill="{color}"/>
          <rect x="-3" y="-6" width="2" height="2" fill="{CYAN}"/>
          <rect x="1" y="-6" width="2" height="2" fill="{CYAN}"/>
        </g>"""


def ship_svg(x, y):
    """Nave do jogador."""
    return f"""
    <g id="ship" transform="translate({x},{y})">
      <rect x="-2" y="-12" width="4" height="4" fill="{CYAN}"/>
      <rect x="-4" y="-8" width="8" height="4" fill="{CYAN}"/>
      <rect x="-8" y="-4" width="16" height="4" fill="{CYAN}"/>
      <rect x="-10" y="0" width="20" height="4" fill="{CYAN}"/>
      <rect x="-6" y="4" width="4" height="2" fill="{GREEN}"/>
      <rect x="2" y="4" width="4" height="2" fill="{GREEN}"/>
      <rect x="-2" y="-10" width="4" height="2" fill="{YELLOW}"/>
    </g>"""


def bullet_svg(x, y, bid):
    """Projétil da nave."""
    return f"""
    <g id="bullet-{bid}">
      <rect x="{x-1}" y="{y}" width="2" height="6" fill="{GREEN}">
        <animate attributeName="y" values="{y};-20" dur="0.8s" repeatCount="indefinite"/>
        <animate attributeName="opacity" values="1;0" dur="0.8s" repeatCount="indefinite"/>
      </rect>
    </g>"""


def build_svg(weeks, total):
    """Monta o SVG completo."""
    # Coleta dias com contribuições
    active_days = []
    all_days = []
    for week in weeks:
        for day in week["contributionDays"]:
            c = day["contributionCount"]
            all_days.append(c)
            if c > 0:
                active_days.append(c)

    max_count = max(all_days) if all_days else 1

    # Seleciona até 52 aliens (um por semana ou dias ativos)
    alien_data = []
    for i, week in enumerate(weeks[-26:]):  # últimas 26 semanas
        total_week = sum(d["contributionCount"] for d in week["contributionDays"])
        if total_week > 0:
            alien_data.append((i, total_week))

    # Layout dos aliens em formação
    cols = min(len(alien_data), 13)
    rows = math.ceil(len(alien_data) / cols) if cols > 0 else 1
    rows = min(rows, 3)

    alien_spacing_x = min(56, (W - 80) // max(cols, 1))
    alien_spacing_y = 44
    start_x = (W - (cols - 1) * alien_spacing_x) // 2
    start_y = 60

    alien_elements = []
    animation_delays = []

    for idx, (week_idx, count) in enumerate(alien_data[:cols * rows]):
        col = idx % cols
        row = idx // cols
        ax = start_x + col * alien_spacing_x
        ay = start_y + row * alien_spacing_y

        intensity = min(count / max(max_count, 1), 1.0)
        if intensity > 0.7:
            color = GREEN
            kind = 2
        elif intensity > 0.4:
            color = CYAN
            kind = 1
        else:
            color = PURPLE
            kind = 0

        # Animação de hover
        delay = (idx * 0.12) % 2.0
        anim_id = f"alien-{idx}"

        alien_elements.append(f"""
        <g id="{anim_id}" opacity="0">
          <animateTransform attributeName="transform" type="translate"
            values="{ax},{ay - 8};{ax},{ay};{ax},{ay - 4};{ax},{ay}"
            dur="0.6s" begin="{delay:.2f}s" fill="freeze"/>
          <animate attributeName="opacity" values="0;1" dur="0.3s" begin="{delay:.2f}s" fill="freeze"/>
          {alien_svg(0, 0, color, kind, 13)}
          <text x="0" y="18" font-family="monospace" font-size="7" fill="{color}88"
            text-anchor="middle">{count}</text>
        </g>""")

    # Nave animada
    ship_x = W // 2
    ship_y = H - 50
    ship_patrol_dur = "4s"

    # Projéteis
    bullets = []
    for i in range(3):
        bx = ship_x
        by = ship_y - 15
        delay_b = i * 0.9
        bullets.append(f"""
        <rect x="{bx - 1}" y="{by}" width="2" height="7" fill="{GREEN}" opacity="0.9">
          <animate attributeName="y" values="{by};10" dur="1.2s" begin="{delay_b:.1f}s" repeatCount="indefinite"/>
          <animate attributeName="opacity" values="0.9;0" dur="1.2s" begin="{delay_b:.1f}s" repeatCount="indefinite"/>
        </rect>""")

    # Estrelas no fundo
    stars = []
    rng = random.Random(42)
    for _ in range(60):
        sx = rng.randint(0, W)
        sy = rng.randint(0, H)
        sr = rng.choice([0.5, 1, 1])
        so = rng.uniform(0.3, 0.9)
        sdur = rng.uniform(1.5, 3.5)
        stars.append(f"""
        <circle cx="{sx}" cy="{sy}" r="{sr}" fill="white" opacity="{so:.2f}">
          <animate attributeName="opacity" values="{so:.2f};{so*0.3:.2f};{so:.2f}"
            dur="{sdur:.1f}s" repeatCount="indefinite"/>
        </circle>""")

    # Score display
    score_display = total * 100

    svg = f"""<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}"
  viewBox="0 0 {W} {H}" style="border-radius:8px;">
  <defs>
    <style>
      @import url('https://fonts.googleapis.com/css2?family=Press+Start+2P');
    </style>
  </defs>

  <!-- Background -->
  <rect width="{W}" height="{H}" fill="{BG}" rx="8"/>

  <!-- Scanlines -->
  <pattern id="scan" width="1" height="4" patternUnits="userSpaceOnUse">
    <rect width="1" height="1" fill="rgba(0,0,0,0.15)" y="3"/>
  </pattern>
  <rect width="{W}" height="{H}" fill="url(#scan)" rx="8"/>

  <!-- Stars -->
  {"".join(stars)}

  <!-- HUD Top -->
  <text x="16" y="22" font-family="monospace" font-size="9" fill="{GREEN}" opacity="0.8">CONTRIBUTIONS INVASION</text>
  <text x="{W//2}" y="22" font-family="monospace" font-size="9" fill="{CYAN}"
    text-anchor="middle">TOTAL: {total}</text>
  <text x="{W - 16}" y="22" font-family="monospace" font-size="9" fill="{YELLOW}"
    text-anchor="end">SCORE: {score_display:07d}</text>

  <!-- Separator -->
  <line x1="0" y1="30" x2="{W}" y2="30" stroke="{GREEN}" stroke-width="0.5" opacity="0.4"/>

  <!-- Aliens -->
  {"".join(alien_elements)}

  <!-- Ground line -->
  <line x1="0" y1="{H - 62}" x2="{W}" y2="{H - 62}" stroke="{GREEN}" stroke-width="0.5" opacity="0.3"/>

  <!-- Ship -->
  <g transform="translate({ship_x},{ship_y})">
    <animateTransform attributeName="transform" type="translate"
      values="{ship_x - 80},{ship_y};{ship_x + 80},{ship_y};{ship_x},{ship_y};{ship_x - 80},{ship_y}"
      dur="{ship_patrol_dur}" repeatCount="indefinite" calcMode="spline"
      keySplines="0.4 0 0.6 1;0.4 0 0.6 1;0.4 0 0.6 1"/>
    {ship_svg(0, 0)}
  </g>

  <!-- Bullets -->
  {"".join(bullets)}

  <!-- Lives -->
  <text x="16" y="{H - 8}" font-family="monospace" font-size="8" fill="{CYAN}" opacity="0.7">
    LIVES: ♥ ♥ ♥
  </text>

  <!-- Legend -->
  <text x="{W//2}" y="{H - 8}" font-family="monospace" font-size="7" fill="#444"
    text-anchor="middle">LAST 26 WEEKS • @{USERNAME}</text>

  <!-- Wave label -->
  <text x="{W - 16}" y="{H - 8}" font-family="monospace" font-size="8" fill="{YELLOW}"
    text-anchor="end">WAVE 01</text>
</svg>"""

    return svg


def main():
    print(f"Gerando Galaga SVG para @{USERNAME}...")
    weeks, total = fetch_contributions()

    if not weeks:
        print("Sem dados de contribuição — gerando SVG demo.")
        # Gera dados de demo se a API falhar
        weeks = []
        for i in range(26):
            week = {"contributionDays": []}
            for d in range(7):
                week["contributionDays"].append({
                    "contributionCount": random.randint(0, 12),
                    "date": str(datetime.now() - timedelta(weeks=26-i, days=6-d))
                })
            weeks.append(week)
        total = sum(
            d["contributionCount"]
            for w in weeks for d in w["contributionDays"]
        )

    svg = build_svg(weeks, total)

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write(svg)

    print(f"Gerado: {OUTPUT_FILE} ({len(svg)} bytes)")
    print(f"Total de contribuições: {total}")


if __name__ == "__main__":
    main()
