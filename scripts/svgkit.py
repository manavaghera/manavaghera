"""Shared palette, fonts and helpers for the profile's hand-built SVGs."""
import os
from html import escape
from pathlib import Path

# Every graphic is built twice, once per GitHub colour mode; the README shows
# whichever matches the viewer. PROFILE_VARIANT picks which one is being built.
VARIANTS = {"dark": "mono", "light": "paper"}  # variant -> theme
VARIANT = os.environ.get("PROFILE_VARIANT", "dark")
DATA = Path(__file__).resolve().parent.parent / "assets"
ASSETS = DATA / VARIANT

# Each theme is four colours; every other shade is mixed from them.
THEME = os.environ.get("PROFILE_THEME", VARIANTS[VARIANT])
THEMES = {
    "paper":     ("#f6f6f5", "#2a2a2a", "#111111", "#2a2a2a"),  # silver-white and charcoal (light mode)
    #            background  text       accent     second accent
    "aubergine": ("#3a0f34", "#dde3e8", "#eaaa00", "#dde3e8"),  # deep aubergine, ice silver, marigold
    "mono":      ("#2a2a2a", "#c0c0c0", "#e4e4e4", "#c0c0c0"),  # charcoal and moonlit silver only
    "signal":    ("#2a2a2a", "#c0c0c0", "#e10600", "#e6e6e6"),  # charcoal, moonlit silver, signal red
    "porcelain": ("#101214", "#ecebe6", "#d6c3a1", "#a3b8a6"),  # graphite, champagne and sage
    "ember":    ("#0c0a09", "#f5efe6", "#ff6a13", "#ffc53d"),  # molten orange on charcoal
    "electric": ("#05070d", "#eef2ff", "#2f7bff", "#00e0ff"),  # electric blue
    "gold":     ("#0b1020", "#f4f1e8", "#f5c542", "#6b7cff"),  # midnight navy and gold
    "red":      ("#000000", "#ffffff", "#ff1f3d", "#8a8a8a"),  # black and racing red
    "ice":      ("#0f141c", "#e5e9f0", "#88c0d0", "#a3be8c"),  # nord
    "lime":     ("#0a0a0a", "#ededE6", "#c6ff3d", "#ff6b2c"),  # acid lime
}


def mix(a, b, t):
    """Blend hex colour a toward b by t (0..1)."""
    ca = [int(a[i:i + 2], 16) for i in (1, 3, 5)]
    cb = [int(b[i:i + 2], 16) for i in (1, 3, 5)]
    return "#" + "".join(f"{round(x + (y - x) * t):02x}" for x, y in zip(ca, cb))


def palette(theme):
    bg, ink, accent, hot = THEMES[theme]
    return dict(bg=bg, ink=ink, accent=accent, hot=hot, panel=mix(bg, ink, .04), panel2=mix(bg, ink, .07),
                line=mix(bg, ink, .12), line2=mix(bg, ink, .18), dim=mix(bg, ink, .36),
                muted=mix(bg, ink, .55), soft=mix(bg, ink, .80))


_p = palette(THEME)
BG, INK, ACCENT, HOT = _p["bg"], _p["ink"], _p["accent"], _p["hot"]
PANEL, PANEL2, LINE, LINE2 = _p["panel"], _p["panel2"], _p["line"], _p["line2"]
DIM, MUTED, SOFT = _p["dim"], _p["muted"], _p["soft"]

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
    print(f"wrote {path.relative_to(DATA.parent)} ({len(content):,} bytes)")


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
