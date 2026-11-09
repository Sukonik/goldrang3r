#!/usr/bin/env python3
"""GoldRang3r midday update — Mon 2026-11-09 12:30 PM ET."""
import json, html, re, subprocess
from collections import Counter
from pathlib import Path

BASE = Path.home() / "workspace" / "goldrang3r"
TODAY = "2026-11-09"
TIME = "12:30 PM"

NEW_ITEMS = [
    {
        "id": "leprivatebanker-google-tpu-1109",
        "author": None,
        "outlet": "The Private Banker",
        "lane": None,
        "headline": "Google unveils two new TPU variants, the confidential-computing 8tx and the dual-chip 8i Max, pressing Nvidia as Alphabet gains in premarket trading",
        "url": "https://leprivatebanker.com/2026/11/09/google-splits-its-tpu-line-into-specialized-8tx-and-8i-max-variants-pressing-nvidia-as-alphabet-gains-premarket/",
    },
    {
        "id": "dealroom-nvidia-korea-1109",
        "author": None,
        "outlet": "Dealroom",
        "lane": None,
        "headline": "Nvidia plans stakes in four Korean AI startups building LLMs and robot brains \u2014 Upstage, Motif Technologies, RealWorld and Point2 \u2014 announced at a Seoul partnership forum",
        "url": "https://dealroom.co/news/170694-nvidia-to-take-stakes-in-four-korean-ai-startups-building-llms-and-robot/",
    },
    {
        "id": "dunyadesk-expedia-ransomware-1109",
        "author": None,
        "outlet": "Dunyadesk",
        "lane": "protect",
        "headline": "Ransomware group N0n lists Expedia on its leak site and claims 830M loyalty records were stolen \u2014 unverified, and Expedia has not confirmed a breach",
        "url": "https://dunyadesk.com/article/expedia-data-breach-claim-n0n-ransomware-830-million-loyalty-records-nov-2026",
    },
    {
        "id": "thehackernews-web3auth-keplr-1109",
        "author": "Swati Khandelwal",
        "outlet": "The Hacker News",
        "lane": "fraud",
        "headline": "A Web3Auth flaw let an attacker drain Keplr crypto wallets set up with Google or Apple sign-in \u2014 at least $1M stolen, per GoPlus; Web3Auth emptied other at-risk wallets into recovery",
        "url": "http://thehackernews.com/2026/11/web3auth-flaw-exploited-to-steal-keplr.html",
    },
    {
        "id": "panews-coinflip-1109",
        "author": None,
        "outlet": "PANews",
        "lane": "fraud",
        "headline": "California orders crypto ATM operator CoinFlip to pay $4.8M+ to fraud victims \u2014 mostly elderly \u2014 after its ~500 ATMs failed identity checks since 2021",
        "url": "https://www.panews.io/articles/01a1bec9-f72e-750c-be9c-b2fcc4c926bf",
    },
    {
        "id": "defiplanet-ankr-bridge-1109",
        "author": None,
        "outlet": "DeFi Planet",
        "lane": "fraud",
        "headline": "Ankr's Ethereum bridge loses $303K+ after an attacker replays a redeemed deposit receipt to bypass withdrawal checks in five unauthorized withdrawals",
        "url": "https://defi-planet.com/2026/11/ankr-ethereum-bridge-faces-ongoing-303k-exploit/",
    },
    {
        "id": "techstartups-onodrim-1109",
        "author": None,
        "outlet": "Tech Startups",
        "lane": None,
        "headline": "Onodrim Industries leads the day's funding with a $300M Series A at a $1.3B valuation, as Mavria raises $130M for factory-built AI data centers and Boson AI $70M for voice models",
        "url": "https://techstartups.com/2026/11/09/startup-funding-news-today-november-9-2026-boson-ai-onodrim-mavria-t-therapeutics-more/",
    },
]

NEW_CLUSTERS = [
    {"theme": "Google's TPU push, Nvidia's Korea bets", "topic": "Midday edition",
     "items": ["leprivatebanker-google-tpu-1109", "dealroom-nvidia-korea-1109"]},
    {"theme": "An unverified 830M-record claim", "topic": "Midday edition",
     "items": ["dunyadesk-expedia-ransomware-1109"]},
    {"theme": "Crypto wallets, bridges and ATMs: a bad morning", "topic": "Midday edition",
     "items": ["thehackernews-web3auth-keplr-1109", "defiplanet-ankr-bridge-1109",
               "panews-coinflip-1109"]},
    {"theme": "Funding: $300M for defense manufacturing", "topic": "Midday edition",
     "items": ["techstartups-onodrim-1109"]},
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
old_hero = "Edition \u2014 Monday, November 9, 2026 \u00b7 Morning river at 7:30 AM \u2014 river below"
new_hero = "Edition \u2014 Monday, November 9, 2026 \u00b7 Midday update at 12:30 PM \u2014 river below"
assert old_hero in s
s = s.replace(old_hero, new_hero)

anchor = '<!-- RIVER:START -->\n                <p class="feed__date">Monday, November 9, 2026</p>\n        <div class="feed">\n'
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
anchor = '<p class="feed__date">Monday, November 9, 2026</p>\n'
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
week = [it for it in data["items"] if it["date"] >= "2026-11-09"]
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
note_old_start = s.index('<p><b>Week of Nov 9\u201315, 2026')
note_old_end = s.index("</p>", note_old_start) + len("</p>")
note_new = (
    "<p><b>Week of Nov 9\u201315, 2026 \u2014 after the 12:30 PM edition on Nov 9:</b> "
    "The Neuron staff still leads at 2 stories; seven new outlets join the board at 1 each, including The Hacker News with the Web3Auth/Keplr wallet theft "
    "and The Private Banker with Google's new TPU variants. "
    "Today's river adds 7 midday stories: Google's TPU 8tx and 8i Max, Nvidia's planned stakes in four Korean AI startups, the unverified Expedia ransomware "
    "claim of 830M records, the Web3Auth flaw draining Keplr wallets, California's $4.8M CoinFlip order, Ankr's $303K bridge exploit, and Onodrim's $300M Series A.</p>"
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
