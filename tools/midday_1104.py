import json, re, html
from pathlib import Path

root = Path('/home/hatch/workspace/goldrang3r')
news_path = root / 'data' / 'news.json'
data = json.loads(news_path.read_text())

new_items = [
    {
        "id": "thn-apt-1104", "outlet": "The Hacker News", "author": "Swati Khandelwal",
        "headline": "Debian and Ubuntu patch an APT flaw, CVE-2026-109518, that lets a man-in-the-middle swap a verified package for a malicious one that then runs as root when APT retries a failed download",
        "url": "http://thehackernews.com/2026/11/debian-and-ubuntu-apt-flaw-lets-mitm.html",
        "lane": "protect", "date": "2026-11-04", "time": "12:30 PM",
    },
    {
        "id": "thn-android-1104", "outlet": "The Hacker News", "author": "Swati Khandelwal",
        "headline": "Google's November Android bulletin patches 216 flaws, led by CVE-2026-58868, a critical zero-click Framework remote-code-execution flaw affecting Android 14 through 17; no in-the-wild exploitation reported",
        "url": "http://thehackernews.com/2026/11/google-patches-critical-android-flaw.html",
        "lane": "protect", "date": "2026-11-04", "time": "12:30 PM",
    },
    {
        "id": "thn-sonicwall-1104", "outlet": "The Hacker News", "author": "Ravie Lakshmanan",
        "headline": "SonicWall will not patch two flaws in end-of-life GMS 9.5.2 and earlier, including CVE-2026-109593, a 9.1-rated unauthenticated file-read flaw that could expose internal management files",
        "url": "http://thehackernews.com/2026/11/sonicwall-wont-patch-eol-gms-flaws-that.html",
        "lane": "protect", "date": "2026-11-04", "time": "12:30 PM",
    },
    {
        "id": "reuters-sia-1104", "outlet": "Reuters", "author": None,
        "headline": "Singapore Airlines says about 46,000 booking records may have been affected by the Amadeus breach, joining Cathay Pacific and Japan Airlines in disclosing customer data exposed",
        "url": "https://www.reuters.com/world/asia-pacific/singapore-airlines-says-46000-booking-records-affected-by-amadeus-breach-2026-11-04/",
        "lane": "protect", "date": "2026-11-04", "time": "12:30 PM",
    },
    {
        "id": "brusselssignal-arkea-1104", "outlet": "Brussels Signal", "author": None,
        "headline": "Crédit Mutuel Arkéa confirms it was hit by an attack enabling fraudulent transactions, saying the incident is now under control and retail clients face no financial impact — after ZachXBT put the suspected theft at $133M",
        "url": "https://brusselssignal.eu/2026/11/french-bank-credit-mutuel-arkea-confirms-cyber-attack-as-investigator-claims-e118-million-stolen/",
        "lane": "fraud", "date": "2026-11-04", "time": "12:30 PM",
    },
    {
        "id": "analyticsinsight-bitmart-1104", "outlet": "Analytics Insight", "author": None,
        "headline": "BitMart confirms a November 2 breach of about $391,000, with its founder acknowledging funds moved to an address linked to the Mercado Bitcoin exploit",
        "url": "https://www.analyticsinsight.net/news/crypto-news-today-bitcoin-outflow-zcash-seven-zebra-security-fixes-bitmart-hack",
        "lane": "fraud", "date": "2026-11-04", "time": "12:30 PM",
    },
    {
        "id": "techstartups-funding-1104", "outlet": "TechStartups", "author": None,
        "headline": "Traversal raises $120M for AI that diagnoses software outages as today's funding roundup totals about $1.62B across eight dollar rounds, plus Lingchuan's RMB 1B chip round",
        "url": "https://techstartups.com/2026/11/04/startup-funding-news-today-november-4-2026-fal-traversal-lingchuan-technology-more/",
        "lane": None, "date": "2026-11-04", "time": "12:30 PM",
    },
]

existing_ids = {i["id"] for i in data["items"]}
assert not (existing_ids & {i["id"] for i in new_items}), "duplicate id"
data["items"].extend(new_items)
news_path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n")

def esc(s):
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace("'", "&#x27;")

def river_item(it):
    tag = f'<span class="feed__tag" data-lane="{it["lane"]}">{it["lane"]}</span>' if it["lane"] else ""
    link = f'<a href="{it["url"]}">{esc(it["headline"])}</a>' if it["url"] else esc(it["headline"])
    return (f'      <div class="feed__item">\n'
            f'        <span class="feed__time">{it["time"]}</span>\n'
            f'        <p class="feed__body"><span class="feed__source">{esc(it["outlet"])}:</span> {link}{tag}</p>\n'
            f'      </div>')

# --- index.html ---
p = root / 'index.html'
t = p.read_text()
t = t.replace('Edition — Wednesday, November 4, 2026 · Morning river below',
              'Edition — Wednesday, November 4, 2026 · Morning river + 12:30 PM midday update below', 1)
anchor = '        <p class="feed__date">Wednesday, November 4, 2026</p>\n        <div class="feed">\n'
assert anchor in t
t = t.replace(anchor, anchor + "\n".join(river_item(i) for i in new_items) + "\n", 1)
p.write_text(t)

# --- lake.html ---
def lake_item(it):
    link = f'<a href="{it["url"]}">{esc(it["headline"])}</a>' if it["url"] else esc(it["headline"])
    return f'          <li><b>{esc(it["outlet"])}:</b> {link}</li>'

clusters = [
    ("Midday: package managers, phones, and unpatched management tools",
     ["thn-apt-1104", "thn-android-1104", "thn-sonicwall-1104"]),
    ("Midday: the Amadeus breach spreads to Singapore Airlines",
     ["reuters-sia-1104"]),
    ("Midday: Arkéa confirms, BitMart confesses",
     ["brusselssignal-arkea-1104", "analyticsinsight-bitmart-1104"]),
    ("Midday funding: Traversal's $120M and the $1.62B day",
     ["techstartups-funding-1104"]),
]
by_id = {i["id"]: i for i in new_items}
blocks = []
for title, ids in clusters:
    lis = "\n".join(lake_item(by_id[i]) for i in ids)
    blocks.append(
        f'        <article class="cluster">\n'
        f'          <p class="cluster__meta">Cluster · Midday update</p>\n'
        f'          <h2 class="cluster__title">{esc(title)}</h2>\n'
        f'          <ul class="cluster__items">\n{lis}\n          </ul>\n'
        f'        </article>\n')
p = root / 'lake.html'
t = p.read_text()
marker = '<p class="feed__date">Tuesday, November 3, 2026</p>'
assert marker in t
t = t.replace(marker, "\n".join(blocks) + "\n" + marker, 1)
p.write_text(t)

# --- news.json clusters ---
data["clusters"].append({
    "date": "2026-11-04", "theme": "Midday: package managers, phones, and unpatched management tools",
    "topic": "Midday update",
    "items": ["thn-apt-1104", "thn-android-1104", "thn-sonicwall-1104"],
})
data["clusters"].append({
    "date": "2026-11-04", "theme": "Midday: the Amadeus breach spreads to Singapore Airlines",
    "topic": "Midday update", "items": ["reuters-sia-1104"],
})
data["clusters"].append({
    "date": "2026-11-04", "theme": "Midday: Arkéa confirms, BitMart confesses",
    "topic": "Midday update",
    "items": ["brusselssignal-arkea-1104", "analyticsinsight-bitmart-1104"],
})
data["clusters"].append({
    "date": "2026-11-04", "theme": "Midday funding: Traversal's $120M and the $1.62B day",
    "topic": "Midday update", "items": ["techstartups-funding-1104"],
})
news_path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n")

# --- leaderboards.html: recount week Nov 2-8 ---
week = [i for i in data["items"] if "2026-11-02" <= i["date"] <= "2026-11-08"]
from collections import defaultdict
counts, latest = {}, {}
for i in week:
    rep = i["author"] if i["author"] else f'{i["outlet"]} staff'
    counts[rep] = counts.get(rep, 0) + 1
    key = (i["date"], i["time"])
    if rep not in latest or key >= latest[rep][0]:
        latest[rep] = (key, i)
order = sorted(counts, key=lambda r: (-counts[r], r))
rows = []
rank = 0
prev = None
for idx, rep in enumerate(order):
    c = counts[rep]
    if c != prev:
        rank = idx + 1
        prev = c
    it = latest[rep][1]
    outlet = it["outlet"]
    head = it["headline"]
    trunc = head[:50] + "…" if len(head) > 50 else head
    mmdd = it["date"][5:]
    rows.append(f'              <tr><td><b>{rank}</b></td><td><b>{esc(rep)}</b></td><td>{esc(outlet)}</td><td>{c}</td><td>{esc(trunc)} — {mmdd}</td></tr>')
tbody = "\n".join(rows)
p = root / 'leaderboards.html'
t = p.read_text()
t2 = re.sub(r'(<!-- LEADERBOARD:START -->.*?<tbody>).*?(</tbody>)',
            lambda m: m.group(1) + "\n" + tbody + "\n            " + m.group(2),
            t, flags=re.S)
assert t2 != t
note = ('<p><b>Week of Nov 2–8, 2026 — after the 12:30 PM edition on Nov 4:</b> '
        'Ravie Lakshmanan (The Hacker News) leads at 5 stories; BleepingComputer staff and Tech.eu staff follow at 3 each, '
        'and Swati Khandelwal (The Hacker News) joins the board at 2 with the APT and Android patches. '
        'Today’s river adds 19 stories: the APT29 watering-hole campaign, a hijacked cPGuard update channel, and a growing exploited-flaw list on the security side; '
        'Binance’s heist reconstruction and the newly named suspected $133M Arkea theft in fintech; plus Fal’s $1.3B round, STATION F’s record year, and Canva’s 1,271-role cut — '
        'with the midday update adding the APT package-swap flaw, Android’s 216-fix bulletin, SonicWall’s unpatched end-of-life flaws, Singapore Airlines in the Amadeus breach, '
        'Arkéa’s confirmation, BitMart’s $391K breach, and Traversal’s $120M round.</p>')
t2 = re.sub(r'<p><b>Week of Nov 2–8, 2026.*?</p>', note, t2, count=1, flags=re.S)
assert t2 != t
p.write_text(t2)
print("OK: added", len(new_items), "items; week reporters:", len(order))
print("Top:", [(r, counts[r]) for r in order[:5]])
