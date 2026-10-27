"""Shared palette, fonts and helpers for the profile's hand-built SVGs."""
from html import escape
from pathlib import Path

ASSETS = Path(__file__).resolve().parent.parent / "assets"

BG = "#05060a"
PANEL = "#0a0d14"
LINE = "#1a2233"
INK = "#e6edf7"
MUTED = "#8b93a7"
DIM = "#475569"
CYAN = "#22d3ee"
VIOLET = "#a78bfa"
PINK = "#f472b6"
GREEN = "#34d399"
AMBER = "#fbbf24"

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
