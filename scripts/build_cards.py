"""Build one animated SVG card per featured project.

Run:  python scripts/build_cards.py
"""
from svgkit import BG, DIM, INK, MONO, MUTED, SANS, esc, svg, wrap, write

PROJECTS = [
    dict(slug="chronus", name="CHRONUS", tag="RAG · DIGITAL LEGACY", color="#ff6436", glyph="clock",
         blurb="A consent-first memory archive you can talk to. Every answer cites its source, "
               "and it says “I don't know” when the archive is silent.",
         chips=["Python", "FastAPI", "React", "ChromaDB", "PyTorch"]),
    dict(slug="newssense", name="NewsSense", tag="LLM NEWSROOM", color="#8b5cf6", glyph="radar",
         blurb="AI news with visible evidence: verified claims, rapid source briefs and model "
               "comparisons, so readers see where every claim came from.",
         chips=["Python", "FastAPI", "React 19", "TypeScript"]),
    dict(slug="kaggle-agent", name="Autonomous Agent", tag="KAGGLE · TOP 1%", color="#fbbf24", glyph="bars",
         blurb="An LLM-driven agent that builds, cross-validates and submits classifiers on "
               "unseen datasets with zero human intervention.",
         chips=["Python", "LLM agents", "AutoML", "AUC 0.83+"]),
    dict(slug="clip-studio", name="Clip Studio", tag="CREATOR TOOLING", color="#a970ff", glyph="play",
         blurb="Finds the games blowing up this week, then bulk-downloads their best Twitch clips "
               "as edit-ready videos or vertical Shorts.",
         chips=["Python", "Streamlit", "Twitch API", "Shorts"]),
    dict(slug="autonomous-content", name="AutonomousContent", tag="MULTI-AGENT", color="#10b981", glyph="orbit",
         blurb="A self-healing editorial team of AI agents that researches, writes and validates, "
               "rewriting until the article clears the bar.",
         chips=["Python", "OpenRouter", "arXiv", "Agents"]),
    dict(slug="mcp-demo", name="MCP Demo", tag="MODEL CONTEXT PROTOCOL", color="#6366f1", glyph="graph",
         blurb="A CLI chatbot showing MCP end to end: a live server exposing tools, resources "
               "and prompts, and Claude deciding when to use them.",
         chips=["Python", "MCP", "Claude", "CLI"]),
]


def glyph(kind, cx, cy, c):
    if kind == "clock":
        return (f'<circle cx="{cx}" cy="{cy}" r="30" fill="none" stroke="{c}" stroke-opacity=".25" stroke-width="2"/>'
                f'<circle cx="{cx}" cy="{cy}" r="30" fill="none" stroke="{c}" stroke-width="2.5" stroke-dasharray="40 149" class="spin"/>'
                f'<line x1="{cx}" y1="{cy}" x2="{cx}" y2="{cy - 18}" stroke="{c}" stroke-width="2.5" stroke-linecap="round" class="spin slow"/>'
                f'<line x1="{cx}" y1="{cy}" x2="{cx + 12}" y2="{cy}" stroke="{c}" stroke-width="2.5" stroke-linecap="round"/>'
                f'<circle cx="{cx}" cy="{cy}" r="3.5" fill="{c}"/>')
    if kind == "radar":
        rings = "".join(f'<circle cx="{cx}" cy="{cy}" r="8" fill="none" stroke="{c}" stroke-width="2" class="ping" style="animation-delay:{d}s"/>'
                        for d in (0, 1, 2))
        return rings + f'<circle cx="{cx}" cy="{cy}" r="5" fill="{c}"/>'
    if kind == "bars":
        out = ""
        for k, h in enumerate([18, 30, 24, 44, 56]):
            out += (f'<rect x="{cx - 34 + k * 14}" y="{cy + 28 - h}" width="9" height="{h}" rx="2" fill="{c}" '
                    f'class="grow" style="animation-delay:{k * .15:.2f}s"/>')
        return out
    if kind == "play":
        return (f'<rect x="{cx - 34}" y="{cy - 24}" width="68" height="48" rx="10" fill="none" stroke="{c}" stroke-width="2.5"/>'
                f'<path d="M{cx - 8} {cy - 12} L{cx + 13} {cy} L{cx - 8} {cy + 12}z" fill="{c}" class="beat"/>'
                f'<line x1="{cx - 34}" y1="{cy + 34}" x2="{cx + 34}" y2="{cy + 34}" stroke="{c}" stroke-opacity=".3" stroke-width="3" stroke-linecap="round"/>'
                f'<line x1="{cx - 34}" y1="{cy + 34}" x2="{cx + 34}" y2="{cy + 34}" stroke="{c}" stroke-width="3" stroke-linecap="round" class="scrub"/>')
    if kind == "orbit":
        out = f'<circle cx="{cx}" cy="{cy}" r="9" fill="{c}"/><circle cx="{cx}" cy="{cy}" r="28" fill="none" stroke="{c}" stroke-opacity=".25" stroke-dasharray="3 5"/>'
        for k in range(3):
            out += (f'<g class="spin" style="animation-duration:{4 + k * 1.5}s;animation-delay:-{k}s">'
                    f'<circle cx="{cx + 28}" cy="{cy}" r="5" fill="{c}" fill-opacity="{1 - k * .25}"/></g>')
        return out
    # graph: client <-> server with tool nodes
    pts = [(cx - 30, cy), (cx + 30, cy - 22), (cx + 30, cy), (cx + 30, cy + 22)]
    lines = "".join(f'<line x1="{pts[0][0]}" y1="{pts[0][1]}" x2="{x}" y2="{y}" stroke="{c}" stroke-width="2" '
                    f'pathLength="100" class="flow" style="animation-delay:{k * .4:.1f}s"/>'
                    for k, (x, y) in enumerate(pts[1:]))
    nodes = "".join(f'<circle cx="{x}" cy="{y}" r="{8 if k == 0 else 5.5}" fill="{BG}" stroke="{c}" stroke-width="2.5"/>'
                    for k, (x, y) in enumerate(pts))
    return lines + nodes


def card(index, p):
    W, H, c = 600, 300, p["color"]
    style = f"""
.idx {{ font: 700 14px {MONO}; fill: {c}; letter-spacing: 2px; }}
.tag {{ font: 600 12px {MONO}; fill: {DIM}; letter-spacing: 2.5px; }}
.name {{ font: 800 34px {SANS}; fill: {INK}; letter-spacing: -.5px; }}
.blurb {{ font: 400 16px {SANS}; fill: {MUTED}; }}
.chip {{ font: 600 12.5px {MONO}; fill: #cbd5e1; }}
.cta {{ font: 700 13px {MONO}; fill: {c}; letter-spacing: 1px; }}
.in {{ animation: in .9s cubic-bezier(.2,.8,.2,1) both; }}
.spin {{ animation: spin 3s linear infinite; transform-box: view-box; transform-origin: 520px 74px; }}
.slow {{ animation-duration: 12s; }}
.ping {{ animation: ping 3s ease-out infinite; transform-box: fill-box; transform-origin: center; opacity: 0; }}
.grow {{ animation: grow 2.4s cubic-bezier(.6,0,.2,1) infinite alternate; transform-box: fill-box; transform-origin: bottom; }}
.beat {{ animation: beat 1.2s ease-in-out infinite; transform-box: fill-box; transform-origin: center; }}
.scrub {{ stroke-dasharray: 68; animation: scrub 4s linear infinite; }}
.flow {{ stroke-dasharray: 30 70; animation: flow 1.6s linear infinite; }}
.sheen {{ animation: sheen 6s ease-in-out infinite; }}
.arrow {{ animation: nudge 1.6s ease-in-out infinite; }}
@keyframes in {{ from {{ opacity: 0; transform: translateY(10px); }} }}
@keyframes spin {{ to {{ transform: rotate(360deg); }} }}
@keyframes ping {{ 0% {{ opacity: .9; transform: scale(1); }} 100% {{ opacity: 0; transform: scale(4.5); }} }}
@keyframes grow {{ from {{ transform: scaleY(.25); }} }}
@keyframes beat {{ 50% {{ transform: scale(1.18); }} }}
@keyframes scrub {{ from {{ stroke-dashoffset: 68; }} to {{ stroke-dashoffset: 0; }} }}
@keyframes flow {{ to {{ stroke-dashoffset: -100; }} }}
@keyframes sheen {{ 0%, 60% {{ transform: translateX(-700px); }} 100% {{ transform: translateX(700px); }} }}
@keyframes nudge {{ 50% {{ transform: translate(3px, -3px); }} }}"""
    lines = "".join(f'<text x="36" y="{158 + k * 24}" class="blurb in" style="animation-delay:.25s">{esc(t)}</text>'
                    for k, t in enumerate(wrap(p["blurb"], 60)[:3]))
    chips, x = "", 36
    for chip in p["chips"]:
        w = len(chip) * 7.8 + 24
        chips += (f'<rect x="{x}" y="{H - 60}" width="{w:.0f}" height="28" rx="14" fill="#0e1422" stroke="#222c40"/>'
                  f'<text x="{x + w / 2:.1f}" y="{H - 41}" text-anchor="middle" class="chip">{esc(chip)}</text>')
        x += w + 8
    body = f"""
<defs>
  <linearGradient id="edge" x1="0" y1="0" x2="1" y2="1">
    <stop offset="0" stop-color="{c}"/><stop offset=".45" stop-color="{c}" stop-opacity=".05"/>
    <stop offset=".55" stop-color="{c}" stop-opacity=".05"/><stop offset="1" stop-color="{c}"/>
    <animateTransform attributeName="gradientTransform" type="rotate" values="0 .5 .5;360 .5 .5" dur="8s" repeatCount="indefinite"/>
  </linearGradient>
  <radialGradient id="glow" cx="1" cy="0" r="1"><stop offset="0" stop-color="{c}" stop-opacity=".22"/><stop offset=".6" stop-color="{c}" stop-opacity="0"/></radialGradient>
  <linearGradient id="sh" x1="0" x2="1"><stop offset="0" stop-color="#fff" stop-opacity="0"/><stop offset=".5" stop-color="#fff" stop-opacity=".06"/><stop offset="1" stop-color="#fff" stop-opacity="0"/></linearGradient>
  <clipPath id="cc"><rect x="1" y="1" width="{W - 2}" height="{H - 2}" rx="20"/></clipPath>
</defs>
<g clip-path="url(#cc)">
  <rect width="{W}" height="{H}" fill="{BG}"/>
  <rect width="{W}" height="{H}" fill="url(#glow)"/>
  <rect x="0" y="0" width="260" height="{H}" fill="url(#sh)" class="sheen" transform="skewX(-20)"/>
</g>
<rect x="1" y="1" width="{W - 2}" height="{H - 2}" rx="20" fill="none" stroke="url(#edge)" stroke-width="2"/>
<text x="36" y="52" class="idx">{index:02d}</text>
<text x="72" y="52" class="tag">{esc(p["tag"])}</text>
<text x="36" y="114" class="name in">{esc(p["name"])}</text>
{lines}
{chips}
<text x="{W - 58}" y="{H - 41}" text-anchor="end" class="cta">VIEW REPO</text>
<text x="{W - 50}" y="{H - 40}" class="cta arrow">↗</text>
{glyph(p["glyph"], 520, 74, c)}"""
    write(f"cards/{p['slug']}.svg", svg(W, H, body, f"{p['name']}: {p['blurb']}", style))


if __name__ == "__main__":
    for i, project in enumerate(PROJECTS, 1):
        card(i, project)
