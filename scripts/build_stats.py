"""Fetch live GitHub stats and render assets/generated/stats.svg.

Needs GITHUB_TOKEN (the Actions token is enough). Run:
    GITHUB_TOKEN=... python scripts/build_stats.py [login]
"""
import base64
import datetime as dt
import json
import os
import sys
import urllib.request
from collections import Counter

from svgkit import (ACCENT, BG, DIM, HEAT, INK, LINE, MONO, MUTED, PANEL, RAMP, SANS, SOFT, esc, svg, write)

QUERY = """
query($login: String!) {
  user(login: $login) {
    repositories(first: 100, ownerAffiliations: OWNER, isFork: false) {
      totalCount
      nodes { stargazerCount languages(first: 10, orderBy: {field: SIZE, direction: DESC}) {
        edges { size node { name } } } }
    }
    contributionsCollection { contributionCalendar { totalContributions
      weeks { contributionDays { contributionCount date } } } }
  }
}"""

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
    langs = Counter()
    for repo in repos["nodes"]:
        for edge in repo["languages"]["edges"]:
            langs[edge["node"]["name"]] += edge["size"]
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
                weeks=cal["weeks"], langs=langs)


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


def languages(langs, x0, y0, width):
    total = sum(langs.values()) or 1
    top = langs.most_common(6)
    rest = total - sum(v for _, v in top)
    if rest > 0:
        top.append(("Other", rest))
    bar, legend, x = [], [], x0
    for i, (name, size) in enumerate(top):
        w = width * size / total
        color = RAMP[i]
        bar.append(f'<rect x="{x:.1f}" y="{y0}" width="{max(w - 2, 1):.1f}" height="14" fill="{color}"/>')
        x += w
        lx = x0 + (i % 4) * (width / 4)
        ly = y0 + 52 + (i // 4) * 30
        legend.append(f'<circle cx="{lx + 6:.1f}" cy="{ly - 5}" r="6" fill="{color}"/>'
                      f'<text x="{lx + 20:.1f}" y="{ly}" class="lang">{esc(name)}'
                      f'<tspan class="axis"> {100 * size / total:.1f}%</tspan></text>')
    return (f'<clipPath id="barclip"><rect x="{x0}" y="{y0}" width="{width}" height="14" rx="7"/></clipPath>'
            f'<g clip-path="url(#barclip)"><g class="bar">{"".join(bar)}</g></g>{"".join(legend)}')


def wakatime(key):
    """Last-7-days coding stats, or None when WakaTime is not set up or unreachable."""
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
    langs = [(l["name"], l["percent"]) for l in data.get("languages", []) if l["percent"] >= 1][:5]
    total = data.get("human_readable_total_including_other_language") or data.get("human_readable_total")
    if not total or not langs:
        return None
    return dict(total=total, daily=data.get("human_readable_daily_average", ""), langs=langs)


def wakatime_band(w, x0, y0, width):
    out = [f'<text x="{x0}" y="{y0}" class="label">CODING TIME · LAST 7 DAYS</text>',
           f'<text x="{x0}" y="{y0 + 58}" class="big">{esc(w["total"])}</text>',
           f'<text x="{x0}" y="{y0 + 86}" class="sub">{esc(w["daily"])} a day on average, tracked by WakaTime</text>']
    bx, track = x0 + 470, width - 470 - 150
    top = max(p for _, p in w["langs"]) or 1
    for i, (name, p) in enumerate(w["langs"]):
        y = y0 + 4 + i * 24
        out.append(f'<text x="{bx}" y="{y + 12}" class="lang">{esc(name)}</text>'
                   f'<rect x="{bx + 140}" y="{y + 2}" width="{track}" height="10" rx="5" fill="{PANEL}"/>'
                   f'<rect x="{bx + 140}" y="{y + 2}" width="{track * p / top:.1f}" height="10" rx="5" fill="{RAMP[i]}" '
                   f'class="grow" style="animation-delay:{.4 + i * .12:.2f}s"/>'
                   f'<text x="{bx + 150 + track}" y="{y + 12}" class="axis">{p:.1f}%</text>')
    return "".join(out)


def render(s, login):
    W, pad = 1200, 48
    tiles = [("CONTRIBUTIONS", s["total"], "past 12 months"),
             ("CURRENT STREAK", s["current"], "days in a row"),
             ("LONGEST STREAK", s["longest"], "days, past year"),
             ("REPOS", s["repos"], f"★ {s['stars']} stars earned")]
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
    langs = languages(s["langs"], pad, 470, W - 2 * pad)
    legend_items = min(len(s["langs"]), 6) + (len(s["langs"]) > 6)
    H = 470 + 52 + 30 * ((legend_items - 1) // 4) + 36
    waka = ""
    if s.get("waka"):
        waka = wakatime_band(s["waka"], pad, H + 18, W - 2 * pad)
        H += 150
    stamp = dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    style = f"""
.title {{ font: 700 15px {MONO}; fill: {INK}; letter-spacing: 3px; }}
.stamp {{ font: 500 12px {MONO}; fill: {DIM}; }}
.label {{ font: 700 12px {MONO}; fill: {ACCENT}; letter-spacing: 2.5px; }}
.num50 {{ font: 800 50px {MONO}; fill: {INK}; }}
.sub {{ font: 500 14px {SANS}; fill: {MUTED}; }}
.axis {{ font: 500 11.5px {MONO}; fill: {DIM}; }}
.lang {{ font: 600 14px {SANS}; fill: {SOFT}; }}
.dot {{ animation: blink 1.4s ease-in-out infinite; }}
.big {{ font: 800 40px {MONO}; fill: {INK}; }}
.grow {{ animation: grow {CYCLE}s cubic-bezier(.6,0,.2,1) infinite both; transform-box: fill-box; transform-origin: left; }}
@keyframes grow {{ 0% {{ transform: scaleX(0); }} 14%, 100% {{ transform: scaleX(1); }} }}
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
  <linearGradient id="sweep" x1="0" x2="1"><stop offset="0" stop-color="{ACCENT}" stop-opacity="0"/>
  <stop offset=".5" stop-color="{ACCENT}" stop-opacity=".16"/><stop offset="1" stop-color="{ACCENT}" stop-opacity="0"/></linearGradient>
</defs>
<rect x=".5" y=".5" width="{W - 1}" height="{H - 1}" rx="22" fill="{BG}" stroke="{LINE}"/>
<circle cx="{pad + 6}" cy="42" r="5" fill="{ACCENT}" class="dot"/>
<text x="{pad + 22}" y="47" class="title">LIVE TELEMETRY · @{esc(login)}</text>
<text x="{W - pad}" y="47" text-anchor="end" class="stamp">auto-updated {stamp}</text>
{"".join(tile_svg)}
<text x="{pad}" y="262" class="label">CONTRIBUTION GRID</text>
{heat}
<text x="{pad}" y="450" class="label">LANGUAGES ACROSS MY REPOS</text>
{langs}
{waka}"""
    return svg(W, H, body, f"GitHub stats for {login}: {s['total']} contributions in the past year, "
                           f"{s['current']}-day current streak, {s['longest']}-day longest streak, "
                           f"{s['repos']} public repos", style)


if __name__ == "__main__":
    login = sys.argv[1] if len(sys.argv) > 1 else os.environ.get("GITHUB_REPOSITORY_OWNER", "manavaghera")
    token = os.environ.get("GITHUB_TOKEN") or sys.exit("GITHUB_TOKEN is not set")
    stats = summarize(fetch(login, token))
    stats["waka"] = wakatime(os.environ.get("WAKATIME_API_KEY"))
    write("generated/stats.svg", render(stats, login))
