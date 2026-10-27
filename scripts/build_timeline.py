"""Build assets/timeline.svg: an animated journey timeline.

Edit EVENTS to change it (oldest first; the last one gets the live "now" pulse).
Run:  python scripts/build_timeline.py
"""
from svgkit import (ACCENT, BG, DIM, HOT, INK, LINE, LINE2, MONO, MUTED, SANS, esc, pct, svg, wrap, write)

EVENTS = [
    ("APR 2022", "Joined GitHub", "first commits, first repos"),
    ("DEC 2024", "First hackathon + open source", "shipped a hackathon build, first PRs"),
    ("MAY 2025", "Fell into quant", "ML for markets, numerical finance"),
    ("AUG 2025", "JPMorgan Chase Forage", "Advanced Software Engineering program"),
    ("JUL 2026", "Went agentic", "MCP server, self-healing multi-agent blog"),
    ("AUG 2026", "Kaggle top 1%", "autonomous LLM agent, NewsSense newsroom"),
    ("OCT 2026", "CHRONUS · final year", "open to internships & startup collabs"),
]

T = 12.0  # seconds per loop


def build():
    W, H, pad, ly = 1200, 450, 48, 246
    n = len(EVENTS)
    xs = [pad + 70 + i * (W - 2 * pad - 140) / (n - 1) for i in range(n)]
    draw = 2.6  # seconds for the line to cross
    nodes, css = [], []
    for i, ((date, title, sub), x) in enumerate(zip(EVENTS, xs)):
        t = .3 + draw * (x - xs[0]) / (xs[-1] - xs[0])
        up = i % 2 == 0
        last = i == n - 1
        color = HOT if last else ACCENT
        d0 = ly - 150 if up else ly + 62
        lines = wrap(title, 24)[:2]
        subs = wrap(sub, 34)[:2]
        text = [f'<text x="{x:.1f}" y="{d0}" text-anchor="middle" class="date" fill="{color}">{esc(date)}</text>']
        text += [f'<text x="{x:.1f}" y="{d0 + 26 + k * 21}" text-anchor="middle" class="ttl">{esc(l)}</text>'
                 for k, l in enumerate(lines)]
        sy = d0 + 26 + len(lines) * 21 + 4
        text += [f'<text x="{x:.1f}" y="{sy + k * 18}" text-anchor="middle" class="sub">{esc(l)}</text>'
                 for k, l in enumerate(subs)]
        stem = (f'<line x1="{x:.1f}" y1="{ly - 14}" x2="{x:.1f}" y2="{ly - 40}" stroke="{LINE2}"/>' if up else
                f'<line x1="{x:.1f}" y1="{ly + 14}" x2="{x:.1f}" y2="{ly + 38}" stroke="{LINE2}"/>')
        ring = (f'<circle cx="{x:.1f}" cy="{ly}" r="9" fill="{color}" class="ping"/>' if last else "")
        nodes.append(f'<g class="e{i}">{stem}{"".join(text)}</g>'
                     f'<g class="n{i}">{ring}<circle cx="{x:.1f}" cy="{ly}" r="9" fill="{BG}" stroke="{color}" stroke-width="2.5"/>'
                     f'<circle cx="{x:.1f}" cy="{ly}" r="3.5" fill="{color}"/></g>')
        css.append(
            f".e{i} {{ animation: e{i} {T}s ease-out infinite both; }}"
            f"@keyframes e{i} {{ 0%, {pct(t, T)} {{ opacity: 0; transform: translateY({-10 if up else 10}px); }}"
            f" {pct(t + .5, T)}, 94% {{ opacity: 1; transform: none; }} 98%, 100% {{ opacity: 0; }} }}\n"
            f".n{i} {{ transform-box: fill-box; transform-origin: center; animation: n{i} {T}s cubic-bezier(.3,1.6,.5,1) infinite both; }}"
            f"@keyframes n{i} {{ 0%, {pct(t - .05, T)} {{ transform: scale(0); }} {pct(t + .35, T)}, 94% {{ transform: scale(1); opacity: 1; }}"
            f" 98%, 100% {{ opacity: 0; }} }}")
    style = f"""
.title {{ font: 700 15px {MONO}; fill: {INK}; letter-spacing: 3px; }}
.date {{ font: 800 13px {MONO}; letter-spacing: 2px; }}
.ttl {{ font: 800 17px {SANS}; fill: {INK}; }}
.sub {{ font: 500 13px {SANS}; fill: {MUTED}; }}
.track {{ stroke-dasharray: 100; animation: track {T}s cubic-bezier(.6,0,.3,1) infinite both; }}
.ping {{ animation: ping 1.8s ease-out infinite; transform-box: fill-box; transform-origin: center; }}
@keyframes track {{ 0%, {pct(.3, T)} {{ stroke-dashoffset: 100; }} {pct(.3 + draw, T)}, 94% {{ stroke-dashoffset: 0; opacity: 1; }} 98%, 100% {{ opacity: 0; }} }}
@keyframes ping {{ 0% {{ transform: scale(1); opacity: .6; }} 100% {{ transform: scale(2.8); opacity: 0; }} }}
""" + "\n".join(css)
    body = f"""
<defs><linearGradient id="trk" gradientUnits="userSpaceOnUse" x1="{xs[0]}" y1="0" x2="{xs[-1]}" y2="0">
  <stop offset="0" stop-color="{DIM}"/><stop offset=".7" stop-color="{ACCENT}"/><stop offset="1" stop-color="{HOT}"/></linearGradient></defs>
<rect x=".5" y=".5" width="{W - 1}" height="{H - 1}" rx="22" fill="{BG}" stroke="{LINE}"/>
<text x="{pad}" y="48" class="title">THE JOURNEY SO FAR</text>
<line x1="{xs[0]:.1f}" y1="{ly}" x2="{xs[-1]:.1f}" y2="{ly}" stroke="{LINE}" stroke-width="3" stroke-linecap="round"/>
<line x1="{xs[0]:.1f}" y1="{ly}" x2="{xs[-1]:.1f}" y2="{ly}" stroke="url(#trk)" stroke-width="3" stroke-linecap="round" pathLength="100" class="track"/>
{"".join(nodes)}"""
    write("timeline.svg", svg(W, H, body, "Journey: " + "; ".join(f"{d} {t}" for d, t, _ in EVENTS), style))


if __name__ == "__main__":
    build()
