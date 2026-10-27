"""Rebuild every profile graphic in the current THEME (see svgkit.py).

    python scripts/build_all.py            # static art + token card
    PROFILE_THEME=gold python scripts/build_all.py

Live GitHub stats also rebuild here when GITHUB_TOKEN is set; otherwise
the workflow refreshes them.
"""
import json
import os
import subprocess
import sys
from pathlib import Path

from svgkit import ACCENT, BG, HEAT, HOT, INK, MUTED, PANEL, THEME

HERE = Path(__file__).resolve().parent


def readme():
    """README badge and typing colours follow the theme too."""
    colors = {k: v.lstrip("#") for k, v in dict(accent=ACCENT, hot=HOT, ink=INK, panel=PANEL).items()}
    text = (HERE / "README.template.md").read_text(encoding="utf-8")
    for key, value in colors.items():
        text = text.replace("{" + key + "}", value)
    (HERE.parent / "README.md").write_text(text, encoding="utf-8")
    print("wrote README.md")


def settings_3d():
    """Colours for the 3D contribution city action, kept in step with the theme."""
    cfg = {"type": "normal", "fileName": "profile-3d.svg", "backgroundColor": BG, "foregroundColor": INK,
           "strongColor": ACCENT, "weakColor": MUTED, "radarColor": ACCENT, "growingAnimation": True,
           "contribColors": HEAT}
    (HERE / "profile-3d.json").write_text(json.dumps(cfg, indent=2) + "\n")
    print("wrote scripts/profile-3d.json")


if __name__ == "__main__":
    print(f"theme: {THEME}")
    steps = ["build_assets.py", "build_cards.py", "build_stack.py", "build_timeline.py", "build_tokens.py"]
    if os.environ.get("GITHUB_TOKEN"):
        steps.append("build_stats.py")
    for step in steps:
        subprocess.run([sys.executable, str(HERE / step)], check=True)
    settings_3d()
    readme()
