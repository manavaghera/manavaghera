"""Render assets/generated/tokens.svg from the AI coding agents' local records:
Claude Code (its own all-time stats cache plus transcripts), OpenAI Codex's
thread database, Mimo Code and opencode message databases, and Gemini CLI chats.

Token counts only exist on this PC, so this runs locally, not in Actions.
Claude Code prunes old transcripts, so totals are kept in
assets/generated/tokens.json and the all-time number never shrinks.
Only aggregate counts leave the machine, never project names or content.
Run:  python scripts/build_tokens.py
"""
import datetime as dt
import glob
import json
import os
import sqlite3
from collections import Counter

from build_stats import odometer, roll_css
from svgkit import (ACCENT, ASSETS, BG, DIM, HOT, INK, LINE, MONO, MUTED, PANEL, SANS, esc, svg, write)

USAGE_KEYS = ("input_tokens", "cache_creation_input_tokens", "cache_read_input_tokens", "output_tokens")
CYCLE = 12


def collect(root):
    seen, days = set(), {}
    for path in glob.glob(os.path.join(root, "**", "*.jsonl"), recursive=True):
        with open(path, encoding="utf-8", errors="ignore") as fh:
            for line in fh:
                if '"usage"' not in line:
                    continue
                try:
                    rec = json.loads(line)
                except ValueError:
                    continue
                msg = rec.get("message")
                usage = msg.get("usage") if isinstance(msg, dict) else None
                stamp = rec.get("timestamp")
                if not usage or not stamp:
                    continue
                key = (msg.get("id"), rec.get("requestId"))
                if key in seen:
                    continue
                seen.add(key)
                day = dt.datetime.fromisoformat(stamp.replace("Z", "+00:00")).astimezone().date()
                rec_day = days.setdefault(day.isoformat(), Counter())
                rec_day["tokens"] += sum(usage.get(k) or 0 for k in USAGE_KEYS)
                rec_day["output"] += usage.get("output_tokens") or 0
                rec_day["requests"] += 1
    return days


def codex(db):
    """Per-thread token totals that Codex itself records."""
    if not os.path.exists(db):
        return {}
    with sqlite3.connect(f"file:{db}?mode=ro", uri=True) as con:
        rows = con.execute("select id, tokens_used, updated_at from threads where tokens_used > 0").fetchall()
    return {tid: {"tokens": n, "day": dt.date.fromtimestamp(ts).isoformat()} for tid, n, ts in rows}


def gemini(root):
    sessions = {}
    for path in glob.glob(os.path.join(root, "**", "chats", "*.json"), recursive=True):
        try:
            chat = json.load(open(path, encoding="utf-8"))
        except (OSError, ValueError):
            continue
        n = sum((m.get("tokens") or {}).get("total", 0) for m in chat.get("messages", []))
        if n:
            day = (chat.get("startTime") or "")[:10] or dt.date.today().isoformat()
            sessions[chat.get("sessionId", path)] = {"tokens": n, "day": day}
    return sessions


def claude_all_time(path):
    """Claude Code's own lifetime totals (what /stats shows); survives transcript cleanup."""
    try:
        stats = json.load(open(path, encoding="utf-8"))
    except (OSError, ValueError):
        return {}
    keys = ("inputTokens", "outputTokens", "cacheReadInputTokens", "cacheCreationInputTokens")
    n = sum(m.get(k) or 0 for m in stats.get("modelUsage", {}).values() for k in keys)
    day = (stats.get("firstSessionDate") or dt.date.today().isoformat())[:10]
    return {"all_time": {"tokens": n, "day": day}} if n else {}


def opencode_family(db):
    """Per-session totals from opencode-style stores (opencode, Mimo Code)."""
    if not os.path.exists(db):
        return {}
    sessions = {}
    with sqlite3.connect(f"file:{db}?mode=ro", uri=True) as con:
        rows = con.execute("select session_id, time_created, data from message where data like '%\"tokens\"%'")
        for sid, created, data in rows:
            try:
                msg = json.loads(data)
            except ValueError:
                continue
            t = msg.get("tokens") if msg.get("role") == "assistant" else None
            if not t:
                continue
            cache = t.get("cache") or {}
            n = sum(t.get(k) or 0 for k in ("input", "output", "reasoning")) + (cache.get("read") or 0) + (cache.get("write") or 0)
            rec = sessions.setdefault(sid, {"tokens": 0, "day": ""})
            rec["tokens"] += n
            rec["day"] = max(rec["day"], dt.date.fromtimestamp(created / 1000).isoformat())
    return sessions


def merge(ledger_path, fresh):
    """Keep the larger record per day/thread/session: logs on disk shrink as they age out."""
    ledger = json.loads(ledger_path.read_text()) if ledger_path.exists() else {}
    if ledger and "claude_days" not in ledger:  # first format: Claude Code days at the top level
        ledger = {"claude_days": ledger}
    for source, records in fresh.items():
        book = ledger.setdefault(source, {})
        for key, rec in records.items():
            if rec["tokens"] >= book.get(key, {}).get("tokens", 0):
                book[key] = dict(rec)
    ledger_path.write_text(json.dumps({k: dict(sorted(v.items())) for k, v in sorted(ledger.items())}, indent=0))
    return ledger


def short(n):
    for div, suffix in ((1e9, "B"), (1e6, "M"), (1e3, "K")):
        if n >= div:
            return f"{n / div:.2f}".rstrip("0").rstrip(".") + suffix
    return str(int(n))


def chart(daily, x0, y0, w, h, days=30):
    today = dt.date.today()
    series = [(today - dt.timedelta(days=days - 1 - i), daily.get(today - dt.timedelta(days=days - 1 - i), 0))
              for i in range(days)]
    peak = max(v for _, v in series) or 1
    gap, bw = 6, (w - 6 * (days - 1)) / days
    out = []
    for i, (day, v) in enumerate(series):
        bh = max(3, h * v / peak)
        x = x0 + i * (bw + gap)
        fill = "url(#hotbar)" if v == peak else (ACCENT if v else LINE)
        out.append(f'<rect x="{x:.1f}" y="{y0 + h - bh:.1f}" width="{bw:.1f}" height="{bh:.1f}" rx="3" fill="{fill}" '
                   f'class="bar" style="animation-delay:{.3 + i * .03:.2f}s"><title>{day}: {v:,} tokens</title></rect>')
    best_day, best = max(series, key=lambda t: t[1])
    out.append(f'<text x="{x0}" y="{y0 + h + 26}" class="axis">{series[0][0]:%b %d}</text>'
               f'<text x="{x0 + w}" y="{y0 + h + 26}" text-anchor="end" class="axis">today</text>')
    return "".join(out), best_day, best


def render(ledger):
    W, H, pad = 1200, 450, 48
    daily, per_tool = Counter(), Counter()
    for day, rec in ledger.get("claude_days", {}).items():
        daily[dt.date.fromisoformat(day)] += rec["tokens"]
        per_tool["claude"] += rec["tokens"]
    # lifetime figure from Claude Code's stats cache covers days whose transcripts are gone
    lifetime = ledger.get("claude_stats", {}).get("all_time", {})
    per_tool["claude"] = max(per_tool["claude"], lifetime.get("tokens", 0))
    for source in ("codex_threads", "mimo_sessions", "opencode_sessions", "gemini_sessions"):
        for rec in ledger.get(source, {}).values():
            daily[dt.date.fromisoformat(rec["day"])] += rec["tokens"]
            per_tool[source] += rec["tokens"]
    total = sum(per_tool.values())
    month = sum(v for k, v in daily.items() if k > dt.date.today() - dt.timedelta(days=30))
    since = min(list(daily) + ([dt.date.fromisoformat(lifetime["day"])] if lifetime else []))
    bars, best_day, best = chart(daily, 640, 130, W - pad - 640, 230)
    tiles = [("CLAUDE CODE", short(per_tool["claude"])), ("OPENAI CODEX", short(per_tool["codex_threads"])),
             ("MIMO CODE", short(per_tool["mimo_sessions"])), ("OPENCODE", short(per_tool["opencode_sessions"])),
             ("GEMINI CLI", short(per_tool["gemini_sessions"])), ("LAST 30 DAYS", short(month))]
    tile_svg = []
    for i, (label, value) in enumerate(tiles):
        x, y = pad + (i % 3) * 190, 296 + (i // 3) * 72
        tile_svg.append(f'<text x="{x}" y="{y}" class="label">{label}</text>'
                        f'<text x="{x}" y="{y + 36}" class="mid">{esc(value)}</text>')
    stamp = dt.date.today().isoformat()
    style = f"""
.title {{ font: 700 15px {MONO}; fill: {INK}; letter-spacing: 3px; }}
.stamp {{ font: 500 12px {MONO}; fill: {DIM}; }}
.label {{ font: 700 12px {MONO}; fill: {ACCENT}; letter-spacing: 2.5px; }}
.num96 {{ font: 800 96px {MONO}; fill: {INK}; }}
.unit {{ font: 800 96px {MONO}; }}
.mid {{ font: 800 30px {MONO}; fill: {INK}; }}
.sub {{ font: 500 15px {SANS}; fill: {MUTED}; }}
.axis {{ font: 500 11.5px {MONO}; fill: {DIM}; }}
.dot {{ animation: blink 1.4s ease-in-out infinite; }}
.bar {{ animation: rise {CYCLE}s cubic-bezier(.2,.9,.3,1.2) infinite both; transform-box: fill-box; transform-origin: bottom; }}
@keyframes blink {{ 50% {{ opacity: .2; }} }}
@keyframes rise {{ 0% {{ transform: scaleY(0); }} 10%, 100% {{ transform: scaleY(1); }} }}
{roll_css(96)}"""
    big = short(total)
    digits, unit = big[:-1], big[-1] if big[-1].isalpha() else ""
    body = f"""
<defs>
  <linearGradient id="hotbar" x1="0" y1="1" x2="0" y2="0"><stop offset="0" stop-color="{ACCENT}"/><stop offset="1" stop-color="{HOT}"/></linearGradient>
  <linearGradient id="unitG" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="{ACCENT}"/><stop offset="1" stop-color="{HOT}"/></linearGradient>
  <clipPath id="bigclip"><rect x="{pad - 4}" y="120" width="560" height="96"/></clipPath>
</defs>
<rect x=".5" y=".5" width="{W - 1}" height="{H - 1}" rx="22" fill="{BG}" stroke="{LINE}"/>
<circle cx="{pad + 6}" cy="42" r="5" fill="{HOT}" class="dot"/>
<text x="{pad + 22}" y="47" class="title">AI-NATIVE · TOKENS BURNED</text>
<text x="{W - pad}" y="47" text-anchor="end" class="stamp">updated {stamp}</text>
<rect x="{pad}" y="76" width="{W - 2 * pad}" height="1" fill="{PANEL}"/>
<text x="{pad}" y="108" class="label">TOKENS PROCESSED SINCE {since:%b %Y}</text>
<g clip-path="url(#bigclip)">{odometer(digits, pad, 200, .2, 96)}</g>
<text x="{pad + len(digits) * 57.6 + 8:.1f}" y="200" class="unit" fill="url(#unitG)">{unit}</text>
<text x="{pad}" y="248" class="sub">prompts, context and cache my AI coding agents chewed through.</text>
{"".join(tile_svg)}
<text x="640" y="108" class="label">DAILY BURN · LAST 30 DAYS</text>
<text x="{W - pad}" y="108" text-anchor="end" class="axis">peak {short(best)} on {best_day:%b %d}</text>
{bars}"""
    return svg(W, H, body, f"{big} tokens processed by my AI coding agents; {short(month)} in the last 30 days", style)


if __name__ == "__main__":
    home = os.path.expanduser("~")
    fresh = {"claude_days": collect(os.path.join(home, ".claude", "projects")),
             "codex_threads": codex(os.path.join(home, ".codex", "state_5.sqlite")),
             "gemini_sessions": gemini(os.path.join(home, ".gemini", "tmp")),
             "claude_stats": claude_all_time(os.path.join(home, ".claude", "stats-cache.json")),
             "mimo_sessions": opencode_family(os.path.join(home, ".local", "share", "mimocode", "mimocode.db")),
             "opencode_sessions": opencode_family(os.path.join(home, ".local", "share", "opencode", "opencode.db"))}
    write("generated/tokens.svg", render(merge(ASSETS / "generated" / "tokens.json", fresh)))
