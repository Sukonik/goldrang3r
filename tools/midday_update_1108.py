#!/usr/bin/env python3
"""GoldRang3r midday update — Sun 2026-11-08 12:30 PM ET."""
import json, html, re, subprocess
from collections import Counter
from pathlib import Path

BASE = Path.home() / "workspace" / "goldrang3r"
TODAY = "2026-11-08"
TIME = "12:30 PM"

NEW_ITEMS = [
    {
        "id": "mt-mirae-asset-1108",
        "author": None,
        "outlet": "Money Today",
        "lane": "fraud",
        "headline": "Mirae Asset Securities, South Korea's largest broker, confirms a Nov 4\u20135 hack that leaked account numbers for ~3,800 customers and personal data of 35,255 current and former staff \u2014 days after regulators unveiled new countermeasures",
        "url": "https://www.mt.co.kr/en/tech/2026/11/08/2026110811173886836",
    },
    {
        "id": "coindoo-gnosis-pay-1108",
        "author": None,
        "outlet": "Coindoo",
        "lane": "fraud",
        "headline": "Gnosis Pay's Nov 3 breach exposed a customer's home address, card number and linked wallets \u2014 the leaked card numbers die when the cards retire Dec 20, but the address and wallet data outlive them",
        "url": "https://coindoo.com/gnosis-pay-breach-risk-outlasts-the-card-shutdown/",
    },
    {
        "id": "morningstar-amplifon-1108",
        "author": None,
        "outlet": "Morningstar",
        "lane": "protect",
        "headline": "Amplifon breach exposed Social Security numbers and health records of 1.33M people, state filings show \u2014 files were taken Jan 18\u2013Feb 8 but the impact was only determined Oct 6",
        "url": "https://www.morningstar.com/news/pr-newswire/20261108ph92107/amplifon-data-breach-investigation-edelson-lechtzin-llp-probes-class-action-claims-after-social-security-numbers-and-health-records-are-exposed",
    },
    {
        "id": "technologytangle-openai-11b-1108",
        "author": None,
        "outlet": "Technology Tangle",
        "lane": None,
        "headline": "OpenAI has closed the first $11B of a funding round valuing it at $1.25T, Bloomberg reports \u2014 short of the $30B it first sought, with the round expected to reach about $20B",
        "url": "https://technologytangle.com/2026/11/08/openai-reportedly-raises-an-additional-11-billion-at-a-125-trillion-valuation",
    },
    {
        "id": "crosswalk-appliedcompute-1108",
        "author": None,
        "outlet": "Crosswalk",
        "lane": None,
        "headline": "Applied Compute raises $350M led by Elad Gil at a $3.25B valuation to train and deploy custom open-source-based AI models for enterprises",
        "url": "https://crosswalk.to/crosswalk/deals",
    },
    {
        "id": "crosswalk-seeds-1108",
        "author": None,
        "outlet": "Crosswalk",
        "lane": None,
        "headline": "Cowboy raises a $5M seed for an app store selling AI agents as locally hosted copies, Numica raises $21.4M for an AI-first accounting platform, and RadianX raises $9M for perovskite solar modules",
        "url": "https://crosswalk.to/crosswalk/deals",
    },
]

NEW_CLUSTERS = [
    {"theme": "Hacked days after the crackdown", "topic": "Midday edition",
     "items": ["mt-mirae-asset-1108"]},
    {"theme": "Two breaches, two long tails", "topic": "Midday edition",
     "items": ["coindoo-gnosis-pay-1108", "morningstar-amplifon-1108"]},
    {"theme": "OpenAI's $11B first close", "topic": "Midday edition",
     "items": ["technologytangle-openai-11b-1108"]},
    {"theme": "Midday checks: $350M for custom models, seeds for agents and accounting",
     "topic": "Midday edition",
     "items": ["crosswalk-appliedcompute-1108", "crosswalk-seeds-1108"]},
]

def esc(s):
    return html.escape(s, quote=True)

# ---------- 1. data/news.json ----------
p = BASE / "data" / "news.json"
data = json.loads(p.read_text())
existing_ids = {it["id"] for it in data["items"]}
for it in NEW_ITEMS:
    if it["id"] in existing_ids:
        continue
    data["items"].append({
        "author": it["author"], "date": TODAY, "headline": it["headline"],
        "id": it["id"], "lane": it["lane"], "outlet": it["outlet"],
        "time": TIME, "url": it["url"],
    })
existing_themes = {(c.get("date"), c.get("theme")) for c in data.get("clusters", [])}
for c in NEW_CLUSTERS:
    if (TODAY, c["theme"]) in existing_themes:
        continue
    data["clusters"].append({"date": TODAY, "items": c["items"],
                              "theme": c["theme"], "topic": c["topic"]})
p.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n")
print("news.json: total items now", len(data["items"]))

# ---------- 2. index.html ----------
p = BASE / "index.html"
s = p.read_text()
old_hero = "Edition \u2014 Sunday, November 8, 2026 \u00b7 Morning river below"
new_hero = "Edition \u2014 Sunday, November 8, 2026 \u00b7 Midday update at 12:30 PM \u2014 river below"
assert old_hero in s
s = s.replace(old_hero, new_hero)

anchor = '<!-- RIVER:START -->\n                <p class="feed__date">Sunday, November 8, 2026</p>\n        <div class="feed">\n'
assert anchor in s
blocks = []
for it in NEW_ITEMS:
    src = f"{esc(it['author'])} / {esc(it['outlet'])}:" if it["author"] else f"{esc(it['outlet'])}:"
    tag = f'<span class="feed__tag" data-lane="{it["lane"]}">{it["lane"]}</span>' if it["lane"] else ""
    blocks.append(
        '      <div class="feed__item">\n'
        f'        <span class="feed__time">{TIME}</span>\n'
        f'        <p class="feed__body"><span class="feed__source">{src}</span> <a href="{it["url"]}">{esc(it["headline"])}</a>{tag}</p>\n'
        '      </div>\n'
    )
s = s.replace(anchor, anchor + "".join(blocks), 1)
p.write_text(s)
print("index.html updated")

# ---------- 3. lake.html ----------
p = BASE / "lake.html"
s = p.read_text()
anchor = '<p class="feed__date">Sunday, November 8, 2026</p>\n'
assert anchor in s
by_id = {it["id"]: it for it in NEW_ITEMS}
clusters_html = []
for c in NEW_CLUSTERS:
    lis = []
    for iid in c["items"]:
        it = by_id[iid]
        lis.append(f'          <li><b>{esc(it["outlet"])}:</b> <a href="{it["url"]}">{esc(it["headline"])}</a></li>\n')
    clusters_html.append(
        '\n        <article class="cluster">\n'
        f'          <p class="cluster__meta">Cluster \u00b7 Midday edition</p>\n'
        f'          <h2 class="cluster__title">{esc(c["theme"])}</h2>\n'
        '          <ul class="cluster__items">\n'
        + "".join(lis) +
        '          </ul>\n'
        '        </article>\n'
    )
s = s.replace(anchor, anchor + "".join(clusters_html), 1)
p.write_text(s)
print("lake.html updated")

# ---------- 4. leaderboards.html ----------
p = BASE / "leaderboards.html"
s = p.read_text()
week = [it for it in data["items"] if "2026-11-02" <= it["date"] <= "2026-11-08"]
def reporter(it):
    return it["author"] if it["author"] else f"{it['outlet']} staff"
counts = Counter((reporter(it), it["outlet"]) for it in week)
latest = {}
for it in week:  # file order = chronological; later overwrites
    latest[(reporter(it), it["outlet"])] = it
ranked = sorted(counts.items(), key=lambda kv: (-kv[1], kv[0][0]))
rows = []
rank = 0
prev = None
for i, ((rep, outlet), n) in enumerate(ranked, 1):
    if n != prev:
        rank = i
        prev = n
    li = latest[(rep, outlet)]
    h = li["headline"]
    h = (h[:50].rstrip() + "\u2026") if len(h) > 50 else h
    md = li["date"][5:].replace("-", "-")
    rows.append(
        f'              <tr><td><b>{rank}</b></td><td><b>{esc(rep)}</b></td><td>{esc(outlet)}</td>'
        f'<td>{n}</td><td>{esc(h)} \u2014 {md}</td></tr>\n'
    )
start = s.index("<!-- LEADERBOARD:START -->")
end = s.index("<!-- LEADERBOARD:END -->")
head = s[:start]
tail = s[end:]
new_table = (
    "<!-- LEADERBOARD:START -->\n"
    '        <div class="table-wrap">\n'
    '          <table class="table">\n'
    '            <thead><tr><th>Rank</th><th>Reporter</th><th>Outlet</th><th>Stories tracked</th><th>Latest</th></tr></thead>\n'
    '            <tbody>\n'
    + "".join(rows) +
    '            </tbody>\n'
    '          </table>\n'
    '        </div>\n'
)
s = head + new_table + tail
note_old_start = s.index('<p><b>Week of Nov 2\u20138, 2026')
note_old_end = s.index("</p>", note_old_start) + len("</p>")
note_new = (
    "<p><b>Week of Nov 2\u20138, 2026 \u2014 after the 12:30 PM edition on Nov 8:</b> "
    "Ravie Lakshmanan (The Hacker News) still leads at 7 stories; Crosswalk staff climbs to 5 with the Applied Compute round and the seed-round trio. "
    "Today's river adds 6 midday stories: Mirae Asset Securities hacked days after regulators unveiled countermeasures, Gnosis Pay's breach outliving its cards, "
    "and Amplifon's 1.33M-person breach disclosed eight months late on the security side; plus OpenAI's $11B first close at a $1.25T valuation, "
    "Applied Compute's $350M round, and seed rounds for Cowboy, Numica and RadianX.</p>"
)
s = s[:note_old_start] + note_new + s[note_old_end:]
p.write_text(s)
print("leaderboards.html updated; week total:", len(week))
print("Top 5:", ranked[:5])

# ---------- 5. forbidden-word check ----------
r = subprocess.run(["grep", "-ri", "goldranger", "--include=*.html", "--include=*.json",
                    "index.html", "lake.html", "leaderboards.html", "data/news.json"],
                   capture_output=True, text=True, cwd=BASE)
print("forbidden-word hits in edited files:", repr(r.stdout) or "none")
