"""Build the hero, terminal, divider and footer SVGs.

Run:  python scripts/build_assets.py
"""
import random

from svgkit import (ACCENT, BG, DIM, HOT, INK, LINE, MONO, MUTED, PANEL, SANS, SOFT, esc, pct, svg, write)

random.seed(7)


# --------------------------------------------------------------------------- hero
def neural_net(x0, y0, w, h):
    layers = [4, 6, 6, 3]
    xs = [x0 + w * i / (len(layers) - 1) for i in range(len(layers))]
    nodes = []
    for x, n in zip(xs, layers):
        gap = h / (max(layers) - 1)
        top = y0 + (h - gap * (n - 1)) / 2
        nodes.append([(x, top + gap * j) for j in range(n)])

    base, pulses, dots = [], [], []
    for a, b in zip(nodes, nodes[1:]):
        for (x1, y1) in a:
            for (x2, y2) in b:
                base.append(f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}"/>')
                if random.random() < 0.55:
                    color = random.choice([ACCENT, ACCENT, ACCENT, HOT])
                    delay = random.uniform(0, 4)
                    pulses.append(
                        f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" pathLength="100" '
                        f'stroke="{color}" style="animation-delay:-{delay:.2f}s"/>')
    for li, layer in enumerate(nodes):
        for (x, y) in layer:
            delay = random.uniform(0, 3)
            color = [SOFT, ACCENT, ACCENT, HOT][li]
            dots.append(
                f'<circle cx="{x:.1f}" cy="{y:.1f}" r="13" fill="{color}" class="halo" '
                f'style="animation-delay:-{delay:.2f}s"/>'
                f'<circle cx="{x:.1f}" cy="{y:.1f}" r="6.5" fill="{PANEL}" stroke="{color}" stroke-width="2"/>'
                f'<circle cx="{x:.1f}" cy="{y:.1f}" r="2.4" fill="{color}"/>')
    labels = "".join(
        f'<text x="{x:.1f}" y="{y0 + h + 34:.1f}" text-anchor="middle" class="tiny">{t}</text>'
        for x, t in zip(xs, ["x", "h₁", "h₂", "ŷ"]))
    return (f'<g stroke="{LINE}" stroke-width="1">{"".join(base)}</g>'
            f'<g class="pulse" stroke-width="2.2" stroke-linecap="round" fill="none">{"".join(pulses)}</g>'
            f'{"".join(dots)}{labels}')


def ticker(y, width):
    words = ["LLM SYSTEMS", "RAG PIPELINES", "AUTONOMOUS AGENTS", "MODEL CONTEXT PROTOCOL",
             "KAGGLE TOP 1%", "QUANT RESEARCH", "FASTAPI", "REACT", "PYTORCH", "EVALS"]
    spans = "".join(f'<tspan fill="{ACCENT}">▲</tspan><tspan> {w}   </tspan>' for w in words)
    run = 1500
    copies = "".join(
        f'<text x="{i * run}" y="{y}" textLength="{run - 30}" lengthAdjust="spacing" class="tick">{spans}</text>'
        for i in range(2))
    return (f'<rect x="0" y="{y - 30}" width="{width}" height="48" fill="#0d0d0d"/>'
            f'<line x1="0" y1="{y - 30}" x2="{width}" y2="{y - 30}" stroke="{LINE}"/>'
            f'<g class="ticker">{copies}</g>')


def hero():
    W, H = 1200, 440
    style = f"""
.tiny {{ font: 500 13px {MONO}; fill: {DIM}; }}
.prompt {{ font: 500 18px {MONO}; fill: {ACCENT}; }}
.name {{ font: 800 96px {SANS}; letter-spacing: -2px; }}
.role {{ font: 600 17px {MONO}; fill: #d6d6cf; letter-spacing: 3px; animation: rise 1.2s .5s cubic-bezier(.2,.8,.2,1) both; }}
.copy {{ font: 400 18px {SANS}; fill: {MUTED}; animation: rise 1.2s .8s cubic-bezier(.2,.8,.2,1) both; }}
.pill {{ animation: rise 1.2s 1.1s cubic-bezier(.2,.8,.2,1) both; }}
.pilltext {{ font: 600 14px {MONO}; fill: {INK}; }}
.tick {{ font: 700 15px {MONO}; fill: #8a8a85; letter-spacing: 2px; }}
.ticker {{ animation: scroll 38s linear infinite; }}
.reveal {{ animation: reveal 1.4s cubic-bezier(.7,0,.2,1) both; }}
.g1 {{ fill: {ACCENT}; opacity: 0; animation: glitch1 4.5s steps(1) infinite; }}
.g2 {{ fill: {HOT}; opacity: 0; animation: glitch2 4.5s steps(1) infinite; }}
.caret {{ animation: blink 1s steps(1) infinite; }}
.live {{ animation: live 1.6s ease-out infinite; transform-box: fill-box; transform-origin: center; }}
.pulse line {{ stroke-dasharray: 9 191; stroke-dashoffset: -100; animation: signal 4s linear infinite; }}
.halo {{ opacity: .12; animation: halo 3s ease-in-out infinite; transform-box: fill-box; transform-origin: center; }}
.driftA {{ animation: driftA 14s ease-in-out infinite alternate; }}
.driftB {{ animation: driftB 18s ease-in-out infinite alternate; }}
.scan {{ animation: scan 7s linear infinite; }}
@keyframes rise {{ from {{ opacity: 0; transform: translateY(14px); }} }}
@keyframes reveal {{ from {{ clip-path: inset(0 100% 0 0); }} to {{ clip-path: inset(0 0 0 0); }} }}
@keyframes scroll {{ to {{ transform: translateX(-1500px); }} }}
@keyframes blink {{ 50% {{ opacity: 0; }} }}
@keyframes live {{ 0% {{ transform: scale(1); opacity: .7; }} 100% {{ transform: scale(3); opacity: 0; }} }}
@keyframes signal {{ 0% {{ stroke-dashoffset: 9; }} 55%, 100% {{ stroke-dashoffset: -100; }} }}
@keyframes halo {{ 50% {{ opacity: .32; transform: scale(1.35); }} }}
@keyframes driftA {{ to {{ transform: translate(120px, 60px); }} }}
@keyframes driftB {{ to {{ transform: translate(-140px, -50px); }} }}
@keyframes scan {{ from {{ transform: translateY(-140px); }} to {{ transform: translateY(460px); }} }}
@keyframes glitch1 {{
  0%, 100% {{ opacity: 0; }}
  62% {{ opacity: .85; transform: translate(-5px, 2px); clip-path: inset(10% 0 62% 0); }}
  64% {{ opacity: .85; transform: translate(4px, -1px); clip-path: inset(55% 0 20% 0); }}
  66% {{ opacity: 0; }}
  90% {{ opacity: .7; transform: translate(-3px, 0); clip-path: inset(30% 0 40% 0); }}
  91% {{ opacity: 0; }}
}}
@keyframes glitch2 {{
  0%, 100% {{ opacity: 0; }}
  63% {{ opacity: .85; transform: translate(5px, -2px); clip-path: inset(40% 0 35% 0); }}
  65% {{ opacity: .85; transform: translate(-4px, 1px); clip-path: inset(72% 0 5% 0); }}
  67% {{ opacity: 0; }}
  90.5% {{ opacity: .7; transform: translate(3px, 1px); clip-path: inset(5% 0 70% 0); }}
  91.5% {{ opacity: 0; }}
}}"""
    name = "MANAV AGHERA"
    name_attrs = 'x="72" y="214" textLength="660" lengthAdjust="spacingAndGlyphs"'
    body = f"""
<defs>
  <clipPath id="frame"><rect width="{W}" height="{H}" rx="22"/></clipPath>
  <pattern id="dots" width="26" height="26" patternUnits="userSpaceOnUse">
    <circle cx="2" cy="2" r="1.1" fill="#1e1e1c"/>
  </pattern>
  <radialGradient id="glowA"><stop offset="0" stop-color="{ACCENT}" stop-opacity=".13"/><stop offset="1" stop-color="{ACCENT}" stop-opacity="0"/></radialGradient>
  <radialGradient id="glowB"><stop offset="0" stop-color="{HOT}" stop-opacity=".10"/><stop offset="1" stop-color="{HOT}" stop-opacity="0"/></radialGradient>
  <linearGradient id="scanG" x1="0" y1="0" x2="0" y2="1">
    <stop offset="0" stop-color="{ACCENT}" stop-opacity="0"/><stop offset=".5" stop-color="{ACCENT}" stop-opacity=".045"/><stop offset="1" stop-color="{ACCENT}" stop-opacity="0"/>
  </linearGradient>
</defs>
<g clip-path="url(#frame)">
  <rect width="{W}" height="{H}" fill="{BG}"/>
  <rect width="{W}" height="{H}" fill="url(#dots)"/>
  <circle class="driftA" cx="160" cy="60" r="420" fill="url(#glowA)"/>
  <circle class="driftB" cx="1080" cy="400" r="460" fill="url(#glowB)"/>
  <rect class="scan" y="0" width="{W}" height="140" fill="url(#scanG)"/>

  <text x="72" y="104" class="prompt">~/manav $ whoami<tspan class="caret">█</tspan></text>
  <g class="reveal">
    <text {name_attrs} class="name g1">{name}</text>
    <text {name_attrs} class="name g2">{name}</text>
    <text {name_attrs} class="name"><tspan fill="{INK}">MANAV </tspan><tspan fill="{ACCENT}">AGHERA</tspan></text>
  </g>
  <text x="74" y="258" class="role">AI / ML ENGINEER  ·  LLM SYSTEMS  ·  QUANT DEV</text>
  <text x="74" y="300" class="copy">Final-year CSE student. I build AI that shows its work —</text>
  <text x="74" y="326" class="copy">RAG systems that cite sources, autonomous agents, quant tooling.</text>
  <g class="pill">
    <rect x="72" y="345" width="392" height="34" rx="17" fill="#121212" stroke="#2a2a2a"/>
    <circle cx="94" cy="362" r="5" fill="{ACCENT}" class="live"/>
    <circle cx="94" cy="362" r="5" fill="{ACCENT}"/>
    <text x="110" y="367" class="pilltext">open to internships &amp; collabs · India</text>
  </g>

  {neural_net(830, 70, 300, 230)}
  {ticker(H - 18, W)}
</g>
<rect x=".5" y=".5" width="{W - 1}" height="{H - 1}" rx="22" fill="none" stroke="#222222"/>"""
    write("hero.svg", svg(W, H, body, "Manav Aghera — AI/ML engineer, LLM systems, quant dev", style))


# ------------------------------------------------------------------------ terminal
def terminal():
    W, T = 1200, 18.0
    G, C, V, A, P, M = ACCENT, ACCENT, SOFT, HOT, HOT, MUTED
    # (kind, segments, time). kind: cmd types out, out appears; segments are (text, color)
    script = [
        ("cmd", [("whoami", INK)]),
        ("out", [("manav aghera", C), (" — ai/ml engineer · final-year cse student · india", M)]),
        ("gap", []),
        ("cmd", [("cat ", INK), ("focus.json", A)]),
        ("out", [("{", M)]),
        ("out", [('  "building"', V), (":  ", M), ('["LLM systems that cite sources", "autonomous agents"]', G)]),
        ("out", [('  "exploring"', V), (": ", M), ('["quant research", "MCP tooling", "eval pipelines"]', G)]),
        ("out", [('  "shipped"', V), (":   ", M), ('["CHRONUS", "NewsSense", "Clip Studio", "Kaggle agent"]', G)]),
        ("out", [('  "ranked"', V), (":    ", M), ('"top 1% — Kaggle Autonomous Agent Prediction"', A)]),
        ("out", [('  "status"', V), (":    ", M), ('"open to internships & startup collabs"', P)]),
        ("out", [("}", M)]),
        ("gap", []),
        ("cmd", [("./ship ", INK), ("--next-idea", A)]),
        ("bar", []),
        ("gap", []),
        ("end", []),
    ]
    x0, y0, lh = 40, 100, 29
    t, rows, css = 0.6, [], []
    for i, (kind, segs) in enumerate(script):
        y = y0 + i * lh
        if kind == "gap":
            continue
        cls = f"l{i}"
        # ASCII-only prompt, so it is exactly PROMPT_CH monospace cells wide
        prompt = (f'<tspan fill="{G}">manav@core</tspan><tspan fill="{M}">:</tspan>'
                  f'<tspan fill="{C}">~</tspan><tspan fill="{M}">$ </tspan>')
        text = "".join(f'<tspan fill="{c}">{esc(s)}</tspan>' for s, c in segs)
        if kind == "cmd":
            n = sum(len(s) for s, _ in segs)
            dur = n * 0.07
            hidden, shown_prompt = "inset(0 100% 0 0)", "inset(0 calc(100% - 14ch) 0 0)"
            rows.append(f'<text x="{x0}" y="{y}" class="t {cls}">{prompt}{text}</text>')
            css.append(f".{cls} {{ animation: k{i} {T}s linear infinite; }}\n"
                       f"@keyframes k{i} {{ 0%, {pct(t - 0.4, T)} {{ clip-path: {hidden}; }}"
                       f" {pct(t - 0.39, T)} {{ clip-path: {shown_prompt}; }}"
                       f" {pct(t, T)} {{ clip-path: {shown_prompt}; animation-timing-function: steps({n}, end); }}"
                       f" {pct(t + dur, T)}, 95% {{ clip-path: inset(0 0 0 0); }} 97%, 100% {{ clip-path: {hidden}; }} }}")
            t += dur + 0.45
        elif kind == "out":
            rows.append(f'<text x="{x0}" y="{y}" class="t {cls}">{text}</text>')
            css.append(f".{cls} {{ animation: f{i} {T}s linear infinite; }}\n"
                       f"@keyframes f{i} {{ 0%, {pct(t, T)} {{ opacity: 0; transform: translateX(-6px); }}"
                       f" {pct(t + 0.25, T)}, 95% {{ opacity: 1; transform: none; }} 97%, 100% {{ opacity: 0; }} }}")
            t += 0.18
        elif kind == "bar":
            bw, dur = 560, 2.4
            rows.append(
                f'<g class="{cls}"><rect x="{x0}" y="{y - 15}" width="{bw}" height="18" rx="4" fill="#161616" stroke="#2a2a2a"/>'
                f'<rect x="{x0}" y="{y - 15}" width="{bw}" height="18" rx="4" fill="url(#barG)" class="fill{i}"/>'
                f'<text x="{x0 + bw + 20}" y="{y}" class="t"><tspan fill="{G}">✓ deployed</tspan>'
                f'<tspan fill="{M}">  idea → prototype → production</tspan></text></g>')
            css.append(f".{cls} {{ animation: f{i} {T}s linear infinite; }}\n"
                       f"@keyframes f{i} {{ 0%, {pct(t, T)} {{ opacity: 0; }} {pct(t + 0.1, T)}, 95% {{ opacity: 1; }} 97%, 100% {{ opacity: 0; }} }}\n"
                       f".fill{i} {{ transform-box: fill-box; transform-origin: left; animation: s{i} {T}s linear infinite; }}\n"
                       f"@keyframes s{i} {{ 0%, {pct(t, T)} {{ transform: scaleX(0); animation-timing-function: cubic-bezier(.6,0,.2,1); }}"
                       f" {pct(t + dur, T)}, 100% {{ transform: scaleX(1); }} }}")
            t += dur + 0.4
        elif kind == "end":
            rows.append(f'<text x="{x0}" y="{y}" class="t {cls}">{prompt}<tspan class="caret" fill="{C}">█</tspan></text>')
            css.append(f".{cls} {{ animation: f{i} {T}s linear infinite; }}\n"
                       f"@keyframes f{i} {{ 0%, {pct(t, T)} {{ opacity: 0; }} {pct(t + 0.01, T)}, 95% {{ opacity: 1; }} 97%, 100% {{ opacity: 0; }} }}")
    assert t < T * 0.9, f"terminal script too long: {t:.1f}s"
    H = y0 + len(script) * lh + 6
    style = f"""
.t {{ font: 500 17px {MONO}; white-space: pre; }}
.title {{ font: 600 13px {MONO}; fill: {DIM}; }}
.caret {{ animation: blink 1s steps(1) infinite; }}
@keyframes blink {{ 50% {{ opacity: 0; }} }}
""" + "\n".join(css)
    body = f"""
<defs>
  <linearGradient id="barG" x1="0" x2="1"><stop offset="0" stop-color="{C}"/><stop offset=".85" stop-color="{C}"/><stop offset="1" stop-color="{P}"/></linearGradient>
  <linearGradient id="chrome" x1="0" x2="0" y1="0" y2="1"><stop offset="0" stop-color="#171717"/><stop offset="1" stop-color="#121212"/></linearGradient>
</defs>
<rect x=".5" y=".5" width="{W - 1}" height="{H - 1}" rx="16" fill="{PANEL}" stroke="#262626"/>
<path d="M16 .5 H{W - 16} a15.5 15.5 0 0 1 15.5 15.5 V46 H.5 V16 A15.5 15.5 0 0 1 16 .5z" fill="url(#chrome)"/>
<line x1="0" y1="46" x2="{W}" y2="46" stroke="#262626"/>
<circle cx="28" cy="23" r="6" fill="#2e2e2c"/><circle cx="48" cy="23" r="6" fill="#2e2e2c"/><circle cx="68" cy="23" r="6" fill="{ACCENT}"/>
<text x="{W / 2}" y="28" text-anchor="middle" class="title">manav@neural-core: ~/profile — zsh</text>
{"".join(rows)}"""
    write("terminal.svg", svg(W, H, body, "Terminal: whoami, focus areas, shipped projects and status", style))


# ------------------------------------------------------------------ divider/footer
def divider():
    W, H = 1200, 36
    style = """
.run { stroke-dasharray: 14 186; animation: run 3.2s linear infinite; }
.gem { transform: rotate(45deg); animation: gem 3.2s ease-in-out infinite; }
@keyframes run { from { stroke-dashoffset: 200; } to { stroke-dashoffset: 0; } }
@keyframes gem { 50% { transform: rotate(135deg) scale(1.3); } }"""
    body = f"""
<defs><linearGradient id="dl" gradientUnits="userSpaceOnUse" x1="40" y1="0" x2="{W - 40}" y2="0"><stop offset="0" stop-color="{INK}" stop-opacity="0"/>
<stop offset=".5" stop-color="{INK}" stop-opacity=".35"/><stop offset="1" stop-color="{INK}" stop-opacity="0"/></linearGradient></defs>
<line x1="40" y1="18" x2="{W - 40}" y2="18" stroke="url(#dl)" stroke-width="1"/>
<line x1="40" y1="18" x2="{W - 40}" y2="18" stroke="{ACCENT}" stroke-width="2" pathLength="200" class="run" stroke-linecap="round"/>
<g transform="translate({W / 2} 18)"><rect x="-6" y="-6" width="12" height="12" fill="{BG}" stroke="{ACCENT}" stroke-width="1.5" class="gem"/></g>"""
    write("divider.svg", svg(W, H, body, "divider", style))


def footer():
    W, H = 1200, 210

    def wave(amp, length, y):
        d = f"M0 {y}"
        for _ in range(int(W * 2 / length) + 2):
            d += f" q{length / 4} {-amp} {length / 2} 0 t{length / 2} 0"
        return d + f" V{H} H0z"

    style = f"""
.w1 {{ animation: slide 9s linear infinite; }}
.w2 {{ animation: slide 14s linear infinite reverse; }}
.w3 {{ animation: slide 20s linear infinite; }}
.big {{ font: 800 34px {SANS}; fill: {INK}; letter-spacing: -.5px; }}
.small {{ font: 500 15px {MONO}; fill: {MUTED}; letter-spacing: 2px; }}
@keyframes slide {{ to {{ transform: translateX(-300px); }} }}"""
    body = f"""
<defs>
  <clipPath id="fc"><rect width="{W}" height="{H}" rx="22"/></clipPath>
  <linearGradient id="fg" x1="0" x2="1"><stop offset="0" stop-color="{ACCENT}"/><stop offset="1" stop-color="{ACCENT}"/></linearGradient>
</defs>
<g clip-path="url(#fc)">
  <rect width="{W}" height="{H}" fill="{BG}"/>
  <path class="w3" d="{wave(14, 300, 140)}" fill="url(#fg)" opacity=".05"/>
  <path class="w2" d="{wave(18, 300, 158)}" fill="url(#fg)" opacity=".10"/>
  <path class="w1" d="{wave(12, 300, 176)}" fill="url(#fg)" opacity=".20"/>
  <text x="{W / 2}" y="78" text-anchor="middle" class="big">Thanks for scrolling this far.</text>
  <text x="{W / 2}" y="112" text-anchor="middle" class="small">LET'S BUILD SOMETHING THAT SHIPS → MANAVAGHERA.DEV</text>
</g>"""
    write("footer.svg", svg(W, H, body, "Thanks for scrolling. Let's build something that ships.", style))


if __name__ == "__main__":
    hero()
    terminal()
    divider()
    footer()
