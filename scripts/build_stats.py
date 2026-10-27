"""Fetch live GitHub stats and render assets/generated/stats.svg.

Needs GITHUB_TOKEN (the Actions token is enough). Run:
    GITHUB_TOKEN=... python scripts/build_stats.py [login]
"""
import datetime as dt
import json
import os
import sys
import urllib.request
from collections import Counter

from svgkit import BG, CYAN, DIM, INK, LINE, MONO, MUTED, PANEL, SANS, VIOLET, esc, svg, write

QUERY = """
query($login: String!) {
  user(login: $login) {
    repositories(first: 100, ownerAffiliations: OWNER, isFork: false, privacy: PUBLIC) {
      totalCount
      nodes { stargazerCount languages(first: 10, orderBy: {field: SIZE, direction: DESC}) {
        edges { size node { name color } } } }
    }
    contributionsCollection { contributionCalendar { totalContributions
      weeks { contributionDays { contributionCount date } } } }
  }
}"""

HEAT = ["#0f1523", "#0c4a5a", "#0e7490", "#06b6d4", "#67e8f9"]
CYCLE = 12  # seconds; odometers and heatmap replay on this loop


def fetch(login, token):
    req = urllib.request.Request(
        "https://api.github.com/graphql",
        data=json.dumps({"query": QUERY, "variables": {"login": login}}).encode(),
        headers={"Authorization": f"bearer {token}", "Content-Type": "application/json",
                 "User-Agent": "profile-stats"})
    with urllib.request.urlopen(req, timeout=30) as resp:
        payload = json.load(resp)
    if payload.get("errors") or not payload.get("data", {}).get("user"):
        raise SystemExit(f"GitHub API error: {payload.get('errors')}")
    return payload["data"]["user"]


def summarize(user):
    repos = user["repositories"]
    langs, colors = Counter(), {}
    for repo in repos["nodes"]:
        for edge in repo["languages"]["edges"]:
            name = edge["node"]["name"]
            langs[name] += edge["size"]
            colors[name] = edge["node"]["color"] or "#64748b"
    cal = user["contributionsCollection"]["contributionCalendar"]
    days = [d for w in cal["weeks"] for d in w["contributionDays"]]
    today = dt.date.today().isoformat()
    days = [d for d in days if d["date"] <= today]
    counts = [d["contributionCount"] for d in days]

    longest = run = 0
    for c in counts:
        run = run + 1 if c else 0
        longest = max(longest, run)
    current, tail = 0, counts[:]
    if tail and tail[-1] == 0:  # today not started yet: the streak is still alive
        tail.pop()
    while tail and tail.pop():
        current += 1

    return dict(total=cal["totalContributions"], current=current, longest=longest,
                repos=repos["totalCount"], stars=sum(r["stargazerCount"] for r in repos["nodes"]),
                weeks=cal["weeks"], langs=langs, colors=colors)


def odometer(value, x, y, delay):
    """Rolling digits that land on `value`; commas stay put."""
    text, dw, dh, out = f"{value:,}", 30, 62, []
    for k, ch in enumerate(text):
        cx = x + k * dw
        if not ch.isdigit():
            out.append(f'<text x="{cx}" y="{y}" class="num">{ch}</text>')
            continue
        d = int(ch)
        column = "".join(f'<text x="{cx}" y="{y + n * dh}" class="num">{n}</text>' for n in range(10))
        out.append(f'<g class="r{d}" style="animation-delay:{delay + k * .12:.2f}s">{column}</g>')
    return "".join(out)


def roll_css():
    css = []
    for d in range(10):
        end = f"translateY({-d * 62}px)"
        css.append(f".r{d} {{ transform: {end}; animation: k{d} {CYCLE}s cubic-bezier(.2,.9,.25,1) infinite both; }}"
                   f"@keyframes k{d} {{ 0% {{ transform: translateY(0); }} 16%, 94% {{ transform: {end}; opacity: 1; }}"
                   f" 97% {{ transform: {end}; opacity: 0; }} 98%, 100% {{ transform: translateY(0); opacity: 0; }} }}")
    return "\n".join(css)


def heatmap(weeks, x0, y0, cell=15, gap=4):
    peak = max((d["contributionCount"] for w in weeks for d in w["contributionDays"]), default=0) or 1
    out, months, last_month = [], [], None
    for wi, week in enumerate(weeks):
        x = x0 + wi * (cell + gap)
        for day in week["contributionDays"]:
            date = dt.date.fromisoformat(day["date"])
            row = (date.weekday() + 1) % 7  # Sunday first, like GitHub
            c = day["contributionCount"]
            level = 0 if c == 0 else min(4, 1 + int(3 * c / peak))
            out.append(f'<rect x="{x}" y="{y0 + row * (cell + gap)}" width="{cell}" height="{cell}" rx="3.5" '
                       f'fill="{HEAT[level]}" class="cell" style="animation-delay:{wi * .035 + row * .02:.2f}s">'
                       f'<title>{c} contributions on {day["date"]}</title></rect>')
            if date.day <= 7 and date.month != last_month and row == 0:
                months.append(f'<text x="{x}" y="{y0 - 12}" class="axis">{date.strftime("%b")}</text>')
                last_month = date.month
    days = "".join(f'<text x="{x0 - 12}" y="{y0 + r * (cell + gap) + 12}" text-anchor="end" class="axis">{n}</text>'
                   for r, n in ((1, "Mon"), (3, "Wed"), (5, "Fri")))
    width = len(weeks) * (cell + gap)
    legend = "".join(f'<rect x="{x0 + width - 128 + i * 19}" y="{y0 + 7 * (cell + gap) + 10}" width="{cell}" '
                     f'height="{cell}" rx="3.5" fill="{c}"/>' for i, c in enumerate(HEAT))
    legend += (f'<text x="{x0 + width - 136}" y="{y0 + 7 * (cell + gap) + 22}" text-anchor="end" class="axis">less</text>'
               f'<text x="{x0 + width - 128 + 5 * 19 + 4}" y="{y0 + 7 * (cell + gap) + 22}" class="axis">more</text>')
    sweep = (f'<rect x="{x0}" y="{y0 - 4}" width="60" height="{7 * (cell + gap) + 4}" fill="url(#sweep)" class="sweep"/>')
    return "".join(months) + days + "".join(out) + legend + sweep, width


def languages(langs, colors, x0, y0, width):
    total = sum(langs.values()) or 1
    top = langs.most_common(6)
    rest = total - sum(v for _, v in top)
    if rest > 0:
        top.append(("Other", rest))
        colors = {**colors, "Other": "#334155"}
    bar, legend, x = [], [], x0
    for i, (name, size) in enumerate(top):
        w = width * size / total
        bar.append(f'<rect x="{x:.1f}" y="{y0}" width="{max(w - 2, 1):.1f}" height="14" fill="{colors[name]}"/>')
        x += w
        lx = x0 + (i % 4) * (width / 4)
        ly = y0 + 52 + (i // 4) * 30
        legend.append(f'<circle cx="{lx + 6:.1f}" cy="{ly - 5}" r="6" fill="{colors[name]}"/>'
                      f'<text x="{lx + 20:.1f}" y="{ly}" class="lang">{esc(name)}'
                      f'<tspan class="axis"> {100 * size / total:.1f}%</tspan></text>')
    return (f'<clipPath id="barclip"><rect x="{x0}" y="{y0}" width="{width}" height="14" rx="7"/></clipPath>'
            f'<g clip-path="url(#barclip)"><g class="bar">{"".join(bar)}</g></g>{"".join(legend)}')


def render(s, login):
    W, pad = 1200, 48
    tiles = [("CONTRIBUTIONS", s["total"], "past 12 months"),
             ("CURRENT STREAK", s["current"], "days in a row"),
             ("LONGEST STREAK", s["longest"], "days, past year"),
             ("PUBLIC REPOS", s["repos"], f"★ {s['stars']} stars earned")]
    tw = (W - 2 * pad - 3 * 20) / 4
    tile_svg = []
    for i, (label, value, sub) in enumerate(tiles):
        x = pad + i * (tw + 20)
        tile_svg.append(
            f'<rect x="{x:.1f}" y="76" width="{tw:.1f}" height="142" rx="16" fill="{PANEL}" stroke="{LINE}"/>'
            f'<text x="{x + 24:.1f}" y="108" class="label">{label}</text>'
            f'<clipPath id="t{i}"><rect x="{x + 18:.1f}" y="122" width="{tw - 36:.1f}" height="60"/></clipPath>'
            f'<g clip-path="url(#t{i})">{odometer(value, x + 24, 172, .3 + i * .25)}</g>'
            f'<text x="{x + 24:.1f}" y="200" class="sub">{esc(sub)}</text>')
    heat, hw = heatmap(s["weeks"], 0, 0)
    hx = (W - hw) / 2 + 14
    heat, _ = heatmap(s["weeks"], hx, 292)
    langs = languages(s["langs"], s["colors"], pad, 470, W - 2 * pad)
    legend_items = min(len(s["langs"]), 6) + (len(s["langs"]) > 6)
    H = 470 + 52 + 30 * ((legend_items - 1) // 4) + 36
    stamp = dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    style = f"""
.title {{ font: 700 15px {MONO}; fill: {INK}; letter-spacing: 3px; }}
.stamp {{ font: 500 12px {MONO}; fill: {DIM}; }}
.label {{ font: 700 12px {MONO}; fill: {CYAN}; letter-spacing: 2.5px; }}
.num {{ font: 800 50px {MONO}; fill: {INK}; }}
.sub {{ font: 500 14px {SANS}; fill: {MUTED}; }}
.axis {{ font: 500 11.5px {MONO}; fill: {DIM}; }}
.lang {{ font: 600 14px {SANS}; fill: #cbd5e1; }}
.dot {{ animation: blink 1.4s ease-in-out infinite; }}
.cell {{ animation: pop {CYCLE}s cubic-bezier(.2,.9,.3,1.3) infinite both; transform-box: fill-box; transform-origin: center; }}
.sweep {{ animation: sweep 6s linear infinite; }}
.bar {{ animation: bar {CYCLE}s cubic-bezier(.6,0,.2,1) infinite both; transform-origin: {pad}px 0; }}
@keyframes blink {{ 50% {{ opacity: .2; }} }}
@keyframes pop {{ 0% {{ opacity: 0; transform: scale(.2); }} 6%, 100% {{ opacity: 1; transform: none; }} }}
@keyframes sweep {{ from {{ transform: translateX(-80px); }} to {{ transform: translateX({hw + 20}px); }} }}
@keyframes bar {{ 0% {{ transform: scaleX(0); }} 14%, 100% {{ transform: scaleX(1); }} }}
{roll_css()}"""
    body = f"""
<defs>
  <linearGradient id="sweep" x1="0" x2="1"><stop offset="0" stop-color="{VIOLET}" stop-opacity="0"/>
  <stop offset=".5" stop-color="{VIOLET}" stop-opacity=".22"/><stop offset="1" stop-color="{VIOLET}" stop-opacity="0"/></linearGradient>
</defs>
<rect x=".5" y=".5" width="{W - 1}" height="{H - 1}" rx="22" fill="{BG}" stroke="{LINE}"/>
<circle cx="{pad + 6}" cy="42" r="5" fill="#34d399" class="dot"/>
<text x="{pad + 22}" y="47" class="title">LIVE TELEMETRY · @{esc(login)}</text>
<text x="{W - pad}" y="47" text-anchor="end" class="stamp">auto-updated {stamp}</text>
{"".join(tile_svg)}
<text x="{pad}" y="262" class="label">CONTRIBUTION GRID</text>
{heat}
<text x="{pad}" y="450" class="label">LANGUAGES ACROSS PUBLIC REPOS</text>
{langs}"""
    return svg(W, H, body, f"GitHub stats for {login}: {s['total']} contributions in the past year, "
                           f"{s['current']}-day current streak, {s['longest']}-day longest streak, "
                           f"{s['repos']} public repos", style)


if __name__ == "__main__":
    login = sys.argv[1] if len(sys.argv) > 1 else os.environ.get("GITHUB_REPOSITORY_OWNER", "manavaghera")
    token = os.environ.get("GITHUB_TOKEN") or sys.exit("GITHUB_TOKEN is not set")
    write("generated/stats.svg", render(summarize(fetch(login, token)), login))
