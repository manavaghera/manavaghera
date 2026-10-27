"""Fetch live GitHub stats and render assets/generated/stats.svg: one clean row
of numbers, no graphs.

Needs GITHUB_TOKEN (the Actions token is enough; a PAT also counts private
work). WAKATIME_API_KEY, when set, adds a coding-time tile. Run:
    GITHUB_TOKEN=... python scripts/build_stats.py [login]
"""
import base64
import datetime as dt
import json
import os
import sys
import urllib.request

from svgkit import (ACCENT, BG, DIM, INK, LINE, MONO, MUTED, PANEL, SANS, esc, svg, write)

QUERY = """
query($login: String!) {
  user(login: $login) {
    createdAt
    repositories(first: 100, ownerAffiliations: OWNER, isFork: false) { totalCount nodes { stargazerCount } }
    contributionsCollection { contributionCalendar { weeks { contributionDays { contributionCount date } } } }
  }
}"""

CYCLE = 12  # seconds; the odometers replay on this loop


def graphql(query, variables, token):
    req = urllib.request.Request(
        "https://api.github.com/graphql",
        data=json.dumps({"query": query, "variables": variables}).encode(),
        headers={"Authorization": f"bearer {token}", "Content-Type": "application/json",
                 "User-Agent": "profile-stats"})
    with urllib.request.urlopen(req, timeout=30) as resp:
        payload = json.load(resp)
    if payload.get("errors") or not payload.get("data", {}).get("user"):
        raise SystemExit(f"GitHub API error: {payload.get('errors')}")
    return payload["data"]["user"]


def all_time_commits(login, created, token):
    """GitHub caps a contributions window at one year, so ask for each year at once."""
    years = range(int(created[:4]), dt.date.today().year + 1)
    parts = " ".join(f'y{y}: contributionsCollection(from: "{y}-01-01T00:00:00Z", to: "{y}-12-31T23:59:59Z") '
                     f"{{ totalCommitContributions }}" for y in years)
    user = graphql(f"query($login: String!) {{ user(login: $login) {{ {parts} }} }}", {"login": login}, token)
    return sum(v["totalCommitContributions"] for v in user.values())


def fetch(login, token):
    user = graphql(QUERY, {"login": login}, token)
    counts = [d["contributionCount"] for w in user["contributionsCollection"]["contributionCalendar"]["weeks"]
              for d in w["contributionDays"] if d["date"] <= dt.date.today().isoformat()]
    longest = run = 0
    for c in counts:
        run = run + 1 if c else 0
        longest = max(longest, run)
    current, tail = 0, counts[:]
    if tail and tail[-1] == 0:  # today not started yet: the streak is still alive
        tail.pop()
    while tail and tail.pop():
        current += 1
    repos = user["repositories"]
    return dict(commits=all_time_commits(login, user["createdAt"], token), current=current, longest=longest,
                repos=repos["totalCount"], stars=sum(r["stargazerCount"] for r in repos["nodes"]))


def wakatime(key):
    """Hours coded in the last 7 days, or None when WakaTime is not set up or unreachable."""
    if not key:
        return None
    auth = base64.b64encode(key.encode()).decode()
    req = urllib.request.Request("https://wakatime.com/api/v1/users/current/stats/last_7_days",
                                 headers={"Authorization": f"Basic {auth}", "User-Agent": "profile-stats"})
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = json.load(resp)["data"]
    except Exception as exc:  # a WakaTime outage must not break the GitHub stats
        print(f"wakatime skipped: {exc}")
        return None
    seconds = data.get("total_seconds_including_other_language") or data.get("total_seconds") or 0
    return round(seconds / 3600) or None


def odometer(value, x, y, delay, size=50):
    """Rolling digits that land on `value` (int or text); other characters stay put.
    Monospace digits are 0.6em wide. Needs roll_css(size) and a .num{size} rule."""
    text = f"{value:,}" if isinstance(value, int) else str(value)
    dw, dh, out = size * .6, size * 1.24, []
    for k, ch in enumerate(text):
        cx = x + k * dw
        if not ch.isdigit():
            out.append(f'<text x="{cx:.1f}" y="{y}" class="num{size}">{esc(ch)}</text>')
            continue
        column = "".join(f'<text x="{cx:.1f}" y="{y + n * dh:.1f}" class="num{size}">{n}</text>' for n in range(10))
        out.append(f'<g class="r{size}_{ch}" style="animation-delay:{delay + k * .12:.2f}s">{column}</g>')
    return "".join(out)


def roll_css(size=50, cycle=CYCLE):
    css = []
    for d in range(10):
        end = f"translateY({-d * size * 1.24:.1f}px)"
        css.append(f".r{size}_{d} {{ transform: {end}; animation: k{size}_{d} {cycle}s cubic-bezier(.2,.9,.25,1) infinite both; }}"
                   f"@keyframes k{size}_{d} {{ 0% {{ transform: translateY(0); }} 16%, 94% {{ transform: {end}; opacity: 1; }}"
                   f" 97% {{ transform: {end}; opacity: 0; }} 98%, 100% {{ transform: translateY(0); opacity: 0; }} }}")
    return "\n".join(css)


def render(s, login):
    W, H, pad, gap = 1200, 254, 48, 20
    tiles = [("COMMITS", s["commits"], "all time"),
             ("CURRENT STREAK", s["current"], "days in a row"),
             ("LONGEST STREAK", s["longest"], "days, past year"),
             ("REPOS", s["repos"], f"★ {s['stars']} stars earned")]
    if s.get("waka"):
        tiles.append(("CODING TIME", f"{s['waka']}h", "last 7 days"))
    n = len(tiles)
    tw = (W - 2 * pad - (n - 1) * gap) / n
    tile_svg = []
    for i, (label, value, sub) in enumerate(tiles):
        x = pad + i * (tw + gap)
        tile_svg.append(
            f'<rect x="{x:.1f}" y="76" width="{tw:.1f}" height="142" rx="16" fill="{PANEL}" stroke="{LINE}"/>'
            f'<text x="{x + 24:.1f}" y="108" class="label">{label}</text>'
            f'<clipPath id="t{i}"><rect x="{x + 18:.1f}" y="122" width="{tw - 36:.1f}" height="60"/></clipPath>'
            f'<g clip-path="url(#t{i})">{odometer(value, x + 24, 172, .3 + i * .25)}</g>'
            f'<text x="{x + 24:.1f}" y="200" class="sub">{esc(sub)}</text>')
    stamp = dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%d")
    style = f"""
.title {{ font: 700 15px {MONO}; fill: {INK}; letter-spacing: 3px; }}
.stamp {{ font: 500 12px {MONO}; fill: {DIM}; }}
.label {{ font: 700 12px {MONO}; fill: {ACCENT}; letter-spacing: 2.5px; }}
.num50 {{ font: 800 50px {MONO}; fill: {INK}; }}
.sub {{ font: 500 14px {SANS}; fill: {MUTED}; }}
.dot {{ animation: blink 2.4s ease-in-out infinite; }}
@keyframes blink {{ 50% {{ opacity: .25; }} }}
{roll_css()}"""
    body = f"""
<rect x=".5" y=".5" width="{W - 1}" height="{H - 1}" rx="22" fill="{BG}" stroke="{LINE}"/>
<circle cx="{pad + 6}" cy="42" r="5" fill="{ACCENT}" class="dot"/>
<text x="{pad + 22}" y="47" class="title">GITHUB · @{esc(login)}</text>
<text x="{W - pad}" y="47" text-anchor="end" class="stamp">updated {stamp}</text>
{"".join(tile_svg)}"""
    return svg(W, H, body, f"GitHub stats for {login}: {s['commits']:,} commits all time, "
                           f"{s['current']}-day current streak, {s['longest']}-day longest streak, "
                           f"{s['repos']} repos", style)


if __name__ == "__main__":
    login = sys.argv[1] if len(sys.argv) > 1 else os.environ.get("GITHUB_REPOSITORY_OWNER", "manavaghera")
    token = os.environ.get("GITHUB_TOKEN") or sys.exit("GITHUB_TOKEN is not set")
    stats = fetch(login, token)
    stats["waka"] = wakatime(os.environ.get("WAKATIME_API_KEY"))
    write("generated/stats.svg", render(stats, login))
