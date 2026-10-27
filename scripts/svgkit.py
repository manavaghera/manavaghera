"""Shared palette, fonts and helpers for the profile's hand-built SVGs."""
from html import escape
from pathlib import Path

ASSETS = Path(__file__).resolve().parent.parent / "assets"

BG = "#0a0a0a"        # ink black
PANEL = "#111111"
LINE = "#222222"
INK = "#ededE6"        # bone white
SOFT = "#bdbdb5"
MUTED = "#8a8a85"
DIM = "#55554f"
ACCENT = "#c6ff3d"     # acid lime: the only loud colour
HOT = "#ff6b2c"        # signal orange, used sparingly

SANS = "'Segoe UI', 'Inter', 'Helvetica Neue', Arial, sans-serif"
MONO = "'JetBrains Mono', 'Fira Code', 'Cascadia Code', Consolas, 'SF Mono', Menlo, monospace"

# Every element's resting style is its final, visible state; animations only
# describe how it gets there. Turning motion off therefore leaves a finished image.
REDUCED_MOTION = """
@media (prefers-reduced-motion: reduce) {
  *, *::before, *::after { animation: none !important; }
}"""


def esc(text):
    return escape(str(text), quote=True)


def svg(width, height, body, label, style=""):
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" '
        f'viewBox="0 0 {width} {height}" role="img" aria-label="{esc(label)}">\n'
        f"<title>{esc(label)}</title>\n"
        f"<style>{style}{REDUCED_MOTION}</style>\n{body}\n</svg>\n"
    )


def write(name, content):
    path = ASSETS / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    print(f"wrote {path.relative_to(ASSETS.parent)} ({len(content):,} bytes)")


def pct(seconds, total):
    return f"{max(0.0, min(100.0, seconds / total * 100)):.3f}%"


def wrap(text, width):
    lines, line = [], ""
    for word in text.split():
        candidate = f"{line} {word}".strip()
        if len(candidate) > width and line:
            lines.append(line)
            line = word
        else:
            line = candidate
    if line:
        lines.append(line)
    return lines
