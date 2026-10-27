"""Rebuild every profile graphic in both colour modes, then the README.

    python scripts/build_all.py

Themes per mode live in svgkit.VARIANTS. Live GitHub stats also rebuild here
when GITHUB_TOKEN is set; otherwise the workflow refreshes them.
"""
import os
import re
import subprocess
import sys
from pathlib import Path

from svgkit import VARIANTS, palette

HERE = Path(__file__).resolve().parent
STEPS = ["build_assets.py", "build_cards.py", "build_stack.py", "build_timeline.py", "build_tokens.py"]


def picture(match):
    """Swap a plain asset <img> for a <picture> that follows the viewer's GitHub theme."""
    path, rest = match.group(1), match.group(2)
    return ('<picture><source media="(prefers-color-scheme: light)" srcset="assets/light/' + path + '" />'
            '<img src="assets/dark/' + path + '"' + rest + ' /></picture>')


def readme():
    """Fill theme colours for both modes and point every graphic at its per-mode copy."""
    text = (HERE / "README.template.md").read_text(encoding="utf-8")
    for prefix, variant in (("d", "dark"), ("l", "light")):
        for key, value in palette(VARIANTS[variant]).items():
            text = text.replace("{" + f"{prefix}_{key}" + "}", value.lstrip("#"))
    text = re.sub(r'<img src="assets/([^"]+\.svg)"([^>]*?)\s*/>', picture, text)
    text = re.sub(r'(<img src="(https://skillicons\.dev/icons\?i=[^"&]+)&theme=dark")',
                  r'<picture><source media="(prefers-color-scheme: light)" srcset="\2&theme=light" />\1', text)
    text = re.sub(r'(<img src="https://skillicons\.dev[^>]*?/>)', r'\1</picture>', text)
    (HERE.parent / "README.md").write_text(text, encoding="utf-8")
    print("wrote README.md")


if __name__ == "__main__":
    steps = STEPS + (["build_stats.py"] if os.environ.get("GITHUB_TOKEN") else [])
    for variant, theme in VARIANTS.items():
        print(f"== {variant}: {theme}")
        env = {**os.environ, "PROFILE_VARIANT": variant, "PROFILE_THEME": theme}
        for step in steps:
            subprocess.run([sys.executable, str(HERE / step)], check=True, env=env)
    readme()
