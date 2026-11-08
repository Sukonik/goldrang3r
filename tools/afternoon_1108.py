#!/usr/bin/env python3
"""GoldRang3r afternoon summaries — Sun 2026-11-08 1:30 PM ET."""
import json, html, re
from collections import Counter
from pathlib import Path

BASE = Path.home() / "workspace" / "goldrang3r"
TODAY = "2026-11-08"
TIME = "1:30 PM"

NEW_ITEMS = [
    {
        "id": "sedaily-sm-entertainment-1108",
        "author": None,
        "outlet": "Seoul Economic Daily",
        "lane": "protect",
        "headline": "SM Entertainment discloses a Nov 4 breach that leaked employee resident registration numbers, bank account numbers and contract details across SM, DearU and Dream Maker — six days after HYBE's leak",
        "url": "https://en.sedaily.com/culture/2026/11/08/sm-entertainment-says-employee-id-and-bank-data-leaked-in",
    },
    {
        "id": "bleepingcomputer-sonicwall-gms-1108",
        "author": None,
        "outlet": "BleepingComputer",
        "lane": "protect",
        "headline": "SonicWall warns two flaws in end-of-life Global Management System will never be patched — CVE-2026-109593, a 9.1 unauthenticated file read, and a 6.8 SQL injection — and tells customers to migrate",
        "url": "https://www.bleepingcomputer.com/news/security/sonicwall-warns-of-unpatched-flaws-in-end-of-life-gms-software/",
    },
    {
        "id": "frontier-binance-laundering-1108",
        "author": None,
        "outlet": "The Frontier",
        "lane": "fraud",
        "headline": "Elliptic tracks Binance hackers swapping about $50M in stolen XRP into bitcoin via THORChain as roughly $3.1B stays in linked wallets, sharpening calls for exchange security standards in crypto legislation",
        "url": "https://thefrontier.fm/article/2026/11/07/binance-hack-pushes-security-rules-focus",
    },
    {
        "id": "coindesk-mercado-bitmart-1108",
        "author": None,
        "outlet": "CoinDesk",
        "lane": "fraud",
        "headline": "Mercado Bitcoin's attacker kept emptying customer deposit addresses for four hours after the exchange said the breach was contained, Bitquery finds — and the same group hit BitMart for about $391K the same day",
        "url": "https://www.coindesk.com/business/2026/11/05/mercado-bitcoin-hack-continued-hours-after-exchange-said-attack-was-contained-report-finds",
    },
    {
        "id": "sedaily-mirae-asset-1108",
        "author": None,
        "outlet": "Seoul Economic Daily",
        "lane": "fraud",
        "headline": "Mirae Asset Securities reports a breach of about 39,000 records — the third Korean brokerage hit and the fourth Mirae Asset affiliate — days after regulators unveiled new countermeasures",
        "url": "https://en.sedaily.com/finance/2026/11/08/mirae-asset-securities-reports-data-breach-affecting-39000",
    },
]

NEW_CLUSTERS = [
    {
        "theme": "K-entertainment's second breach in a week",
        "topic": "Summary — Tech Security",
        "body": "SM Entertainment says an external attacker broke into its internal business systems around November 4 and copied stored documents — including employee names, phone numbers, addresses, bank account numbers, resident registration numbers, and contract details — before the company blocked the attack paths and rotated the compromised access keys. The breach also swept through affiliates DearU, which runs the fan-messaging app Bubble, and concert producer Dream Maker, though SM says no fan data on Bubble was touched. It is the second major Korean entertainment breach in six days, after HYBE disclosed its own internal leak on November 2, and the pattern is the same both times: the attackers went for the approval and document systems, not the customer-facing platforms. SM has not said how many people are affected, and says no secondary misuse has been confirmed so far.",
        "items": ["sedaily-sm-entertainment-1108"],
    },
    {
        "theme": "The patch that will never come",
        "topic": "Summary — Tech Security",
        "body": "SonicWall has disclosed two flaws in its Global Management System, the console that manages fleets of its firewalls — and says neither will ever be patched, because the product has reached end of life. The worse of the two, CVE-2026-109593, scores 9.1 and lets an unauthenticated attacker with network access read internal GMS files; the second, CVE-2026-109594, is a SQL injection rated 6.8 that needs high privileges but can read or change database records. Both were reported by researchers at Pentest-Tools, and SonicWall's only advice is to migrate to its replacement, Network Security Manager. There is no reported exploitation yet, but the vendor's own track record argues against waiting: CISA has added 19 SonicWall flaws to its exploited-vulnerabilities catalog in four years, 13 of them also used by ransomware gangs.",
        "items": ["bleepingcomputer-sonicwall-gms-1108"],
    },
    {
        "theme": "The laundering trail moves to bitcoin",
        "topic": "Summary — Fintech Security",
        "body": "The Binance hackers have started swapping stolen XRP into bitcoin, Elliptic told reporters, with about $50 million moved mostly through THORChain, a service that shifts assets between blockchains — a move that puts the money beyond the reach of stablecoin issuers that can freeze tokens. The laundering trail now spans more than 20,000 wallets across 16 blockchains and at least 65,000 transactions, with roughly $3.1 billion still sitting in addresses linked to the theft. The shift is also sharpening a policy fight: the stalled CLARITY Act draft lacks hot-wallet limits, insurance, and customer protections that might have limited the damage, and the CFTC chair is using the breach to argue for federal oversight of offshore exchanges. Binance says it will cover the loss and has published reserves to show it can.",
        "items": ["frontier-binance-laundering-1108"],
    },
    {
        "theme": "Contained — except it wasn't",
        "topic": "Summary — Fintech Security",
        "body": "Mercado Bitcoin's attacker kept emptying customer deposit addresses for about four hours after the exchange said the breach was contained, according to blockchain data from Bitquery, which traced $48.6 million taken across ten blockchains — above the $40 million first reported. The same attacker took about $391,000 from wallets Bitquery ties to BitMart, whose founder confirmed a November 2 hack and suspects the same group, with the BitMart transfers starting roughly 53 minutes before the first Mercado Bitcoin funds moved. Mercado Bitcoin says no customer funds were lost and about $11.2 million has been frozen with help from Tether, Circle and others, but deposits and withdrawals remain suspended with no reopening date. The two hits, hours apart and sharing an attacker address, look less like isolated incidents than one operation working down a list.",
        "items": ["coindesk-mercado-bitmart-1108"],
    },
    {
        "theme": "The fourth Mirae affiliate falls",
        "topic": "Summary — Fintech Security",
        "body": "Mirae Asset Securities, South Korea's largest broker, has confirmed a November 4–5 hack that leaked account numbers for about 3,800 customers and personal data of 35,255 current and former staff — days after regulators unveiled new countermeasures for the sector. A follow-up report puts the total at about 39,000 records and names Mirae Asset Securities as the third Korean brokerage hit, after Daishin and Hanyang, and the fourth Mirae Asset affiliate breached, after its life insurance, global investments and energy infrastructure arms. The attackers hit a mobile-web phone-authentication login service and the group's groupware a day apart, and the company says no resident registration numbers, passport numbers or financial damage have been confirmed so far. The timing is the story: the breach landed the same week the crackdown was announced, and the sector's defenses are being tested faster than they are being built.",
        "items": ["mt-mirae-asset-1108", "sedaily-mirae-asset-1108"],
    },
]

LOG_CARD_BODY = (
    "Five original summaries on the Lake: SM Entertainment discloses a Nov 4 breach leaking employee resident registration numbers and bank "
    "account numbers across SM, DearU and Dream Maker; SonicWall says two flaws in its end-of-life Global Management System will never be "
    "patched, including a 9.1 unauthenticated file read; the Binance hackers start swapping stolen XRP into bitcoin via THORChain as about "
    "$3.1B stays in linked wallets; Mercado Bitcoin's attacker kept draining deposit addresses hours after the exchange said the breach was "
    "contained, and the same group hit BitMart the same day; and Mirae Asset Securities reports a breach of about 39,000 records, the "
    "fourth Mirae Asset affiliate hit. Five stories the earlier editions missed were added first: the SM Entertainment breach, the SonicWall "
    "GMS flaws, the Binance laundering update, the Mercado Bitcoin and BitMart hacks, and the Mirae Asset follow-up."
)

def esc(s):
    return html.escape(s, quote=True)

# ---------- 1. data/news.json ----------
p = BASE / "data" / "news.json"
data = json.loads(p.read_text())
existing_ids = {it["id"] for it in data["items"]}
assert not any(it["id"] in existing_ids for it in NEW_ITEMS), "duplicate id"
for it in NEW_ITEMS:
    data["items"].append({
        "author": it["author"], "date": TODAY, "headline": it["headline"],
        "id": it["id"], "lane": it["lane"], "outlet": it["outlet"],
        "time": TIME, "url": it["url"],
    })
for c in NEW_CLUSTERS:
    data["clusters"].append({"body": c["body"], "date": TODAY, "items": c["items"],
                              "theme": c["theme"], "topic": c["topic"]})
p.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n")
print("news.json: total items now", len(data["items"]), "| today items:",
      len([i for i in data["items"] if i["date"] == TODAY]))

# ---------- 2. lake.html ----------
p = BASE / "lake.html"
s = p.read_text()
anchor = '<p class="feed__date">Sunday, November 8, 2026</p>\n'
assert anchor in s
by_id = {it["id"]: it for it in data["items"]}
clusters_html = []
for c in NEW_CLUSTERS:
    lis = []
    for iid in c["items"]:
        it = by_id[iid]
        lis.append(f'          <li><b>{esc(it["outlet"])}:</b> <a href="{it["url"]}">{esc(it["headline"])}</a></li>\n')
    clusters_html.append(
        '\n        <article class="cluster">\n'
        f'          <p class="cluster__meta">Cluster · Afternoon summaries · {esc(c["topic"])}</p>\n'
        f'          <h2 class="cluster__title">{esc(c["theme"])}</h2>\n'
        f'          <p class="cluster__body">{esc(c["body"])}</p>\n'
        '          <ul class="cluster__items">\n'
        + "".join(lis) +
        '          </ul>\n'
        '        </article>\n'
    )
s = s.replace(anchor, anchor + "".join(clusters_html), 1)
p.write_text(s)
print("lake.html updated")

# ---------- 3. log.html ----------
p = BASE / "log.html"
s = p.read_text()
day_anchor = '<span class="day__date">2026-11-08</span>'
assert day_anchor in s
pos = s.index(day_anchor)
close = s.index("</article>", pos) + len("</article>")
card = (
    '\n            <article class="card" data-lane="protect">\n'
    '              <p class="card__meta">Log · Day 19 · Afternoon summaries</p>\n'
    '              <h3>1:30 PM — the afternoon summaries</h3>\n'
    f'              <p>{esc(LOG_CARD_BODY)}</p>\n'
    '              <p class="card__foot"><a class="text-link" href="lake.html">Read the summaries →</a></p>\n'
    '            </article>'
)
s = s[:close] + card + s[close:]
p.write_text(s)
print("log.html updated")

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
    h = (h[:50].rstrip() + "…") if len(h) > 50 else h
    md = li["date"][5:].replace("-", "-")
    rows.append(
        f'              <tr><td><b>{rank}</b></td><td><b>{esc(rep)}</b></td><td>{esc(outlet)}</td>'
        f'<td>{n}</td><td>{esc(h)} — {md}</td></tr>\n'
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
note_old_start = s.index('<p><b>Week of Nov 2–8, 2026')
note_old_end = s.index("</p>", note_old_start) + len("</p>")
note_new = (
    "<p><b>Week of Nov 2–8, 2026 — after the 1:30 PM summaries on Nov 8:</b> "
    "Ravie Lakshmanan (The Hacker News) still leads at 7 stories; BleepingComputer staff climbs to 6 with the SonicWall GMS flaws, tying "
    "TechCrunch staff. Seoul Economic Daily staff joins the board at 2 with the SM Entertainment and Mirae Asset breaches, CoinDesk staff "
    "moves to 2 with the Mercado Bitcoin and BitMart hacks, and The Frontier staff joins at 1 with the Binance laundering update. Today's "
    "river adds 5 afternoon stories: the SM Entertainment breach, SonicWall's unpatched end-of-life GMS flaws, the Binance hackers' "
    "XRP-to-bitcoin laundering shift, the Mercado Bitcoin and BitMart linked hacks, and the Mirae Asset Securities breach.</p>"
)
s = s[:note_old_start] + note_new + s[note_old_end:]
p.write_text(s)
print("leaderboards.html updated; week total:", len(week))
print("Top 5:", ranked[:5])

# ---------- 5. forbidden-word check ----------
import subprocess
r = subprocess.run(["grep", "-ri", "goldranger", "--include=*.html", "--include=*.json",
                    "lake.html", "leaderboards.html", "log.html", "data/news.json"],
                   capture_output=True, text=True, cwd=BASE)
print("forbidden-word hits in edited files:", repr(r.stdout) or "none")
