"""Build assets/ai-tools.svg: the AI tools I work with, as an animated grid.

Edit TOOLS to change it. `daily=True` marks a daily driver (gets a live dot).
Run:  python scripts/build_stack.py
"""
from svgkit import (ACCENT, BG, DIM, HOT, INK, LINE, LINE2, MONO, MUTED, PANEL, PANEL2, SANS, esc, svg, write)

TOOLS = [
    # name, monogram, what it does, daily driver
    ("Claude Code", "CC", "agentic coding", True),
    ("Cursor", "Cu", "AI-native IDE", True),
    ("GitHub Copilot", "GH", "pair programmer", False),
    ("OpenAI Codex", "Cx", "cloud coding agent", False),
    ("Gemini CLI", "Ge", "terminal agent", False),
    ("Cline", "Cl", "VS Code agent", False),
    ("Trae", "Tr", "AI IDE", False),
    ("Kimi Code", "Ki", "coding agent", False),
    ("Ollama", "Ol", "local LLMs", True),
    ("Hugging Face", "HF", "models & datasets", False),
    ("OpenRouter", "OR", "model gateway", True),
    ("Whisper", "Wh", "speech to text", False),
    ("MCP", "MC", "tool protocol", True),
    ("ChromaDB", "Ch", "vector store", False),
    ("n8n", "n8", "workflow automation", False),
    ("Streamlit", "St", "ML web apps", False),
    ("Jupyter", "Ju", "notebooks", False),
    ("Kaggle", "Kg", "competitions", False),
    ("PyTorch", "PT", "deep learning", False),
    ("FastAPI", "FA", "model serving", True),
]


def build():
    W, pad, cols, gap = 1200, 48, 4, 16
    cw, ch = (W - 2 * pad - (cols - 1) * gap) / cols, 70
    rows = -(-len(TOOLS) // cols)
    top = 96
    H = top + rows * (ch + gap) + 40
    cells = []
    for i, (name, mono, what, daily) in enumerate(TOOLS):
        x = pad + (i % cols) * (cw + gap)
        y = top + (i // cols) * (ch + gap)
        delay = .15 + (i % cols) * .08 + (i // cols) * .12
        live = (f'<circle cx="{x + cw - 18:.1f}" cy="{y + 18}" r="4" fill="{HOT}" class="ping"/>'
                f'<circle cx="{x + cw - 18:.1f}" cy="{y + 18}" r="4" fill="{HOT}"/>') if daily else ""
        cells.append(
            f'<g class="pop" style="animation-delay:{delay:.2f}s">'
            f'<rect x="{x:.1f}" y="{y}" width="{cw:.1f}" height="{ch}" rx="14" fill="{PANEL}" stroke="{LINE}"/>'
            f'<rect x="{x + 14:.1f}" y="{y + 15}" width="40" height="40" rx="10" fill="{PANEL2}" stroke="{LINE2}"/>'
            f'<text x="{x + 34:.1f}" y="{y + 41}" text-anchor="middle" class="mono">{esc(mono)}</text>'
            f'<text x="{x + 68:.1f}" y="{y + 32}" class="name">{esc(name)}</text>'
            f'<text x="{x + 68:.1f}" y="{y + 52}" class="what">{esc(what)}</text>{live}</g>')
    style = f"""
.title {{ font: 700 15px {MONO}; fill: {INK}; letter-spacing: 3px; }}
.note {{ font: 500 12px {MONO}; fill: {DIM}; }}
.mono {{ font: 800 15px {MONO}; fill: {ACCENT}; }}
.name {{ font: 700 16px {SANS}; fill: {INK}; }}
.what {{ font: 500 12.5px {MONO}; fill: {MUTED}; }}
.pop {{ animation: pop 10s cubic-bezier(.2,.9,.3,1.2) infinite both; }}
.ping {{ animation: ping 1.8s ease-out infinite; transform-box: fill-box; transform-origin: center; }}
.sweep {{ animation: sweep 5s ease-in-out infinite; }}
@keyframes pop {{ 0% {{ opacity: 0; transform: translateY(12px); }} 8%, 100% {{ opacity: 1; transform: none; }} }}
@keyframes ping {{ 0% {{ transform: scale(1); opacity: .8; }} 100% {{ transform: scale(3.2); opacity: 0; }} }}
@keyframes sweep {{ 0%, 30% {{ transform: translateX(-400px); }} 100% {{ transform: translateX({W + 200}px); }} }}"""
    body = f"""
<defs>
  <linearGradient id="sw" x1="0" x2="1"><stop offset="0" stop-color="{ACCENT}" stop-opacity="0"/>
  <stop offset=".5" stop-color="{ACCENT}" stop-opacity=".07"/><stop offset="1" stop-color="{ACCENT}" stop-opacity="0"/></linearGradient>
  <clipPath id="frame"><rect width="{W}" height="{H}" rx="22"/></clipPath>
</defs>
<rect x=".5" y=".5" width="{W - 1}" height="{H - 1}" rx="22" fill="{BG}" stroke="{LINE}"/>
<text x="{pad}" y="54" class="title">AI ARSENAL</text>
<circle cx="{W - pad - 150}" cy="50" r="4" fill="{HOT}"/>
<text x="{W - pad}" y="54" text-anchor="end" class="note">= daily driver</text>
{"".join(cells)}
<g clip-path="url(#frame)"><rect y="0" width="260" height="{H}" fill="url(#sw)" class="sweep" transform="skewX(-18)"/></g>"""
    write("ai-tools.svg", svg(W, H, body, "AI tools: " + ", ".join(t[0] for t in TOOLS), style))


if __name__ == "__main__":
    build()
