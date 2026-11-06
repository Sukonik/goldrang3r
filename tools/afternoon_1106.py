#!/usr/bin/env python3
"""GoldRang3r afternoon summaries — Fri 2026-11-06 1:30 PM ET."""
import json, html, re
from collections import Counter
from pathlib import Path

BASE = Path.home() / "workspace" / "goldrang3r"
TODAY = "2026-11-06"
TIME = "1:30 PM"

NEW_ITEMS = [
    {
        "id": "thn-barracuda-esg-1106",
        "author": "Swati Khandelwal",
        "outlet": "The Hacker News",
        "lane": "protect",
        "headline": "Two Barracuda Email Security Gateway flaws chain to unauthenticated root — a 9.3 authorization bypass plus an 8.6 command injection",
        "url": "https://thehackernews.com/2026/11/experts-demonstrate-barracuda-email.html",
    },
    {
        "id": "thn-claude-dispatch-1106",
        "author": "Swati Khandelwal",
        "outlet": "The Hacker News",
        "lane": "protect",
        "headline": "Malicious browser extensions could use Claude Dispatch to run code on users' computers",
        "url": "https://thehackernews.com/2026/11/malicious-browser-extensions-could-use.html",
    },
    {
        "id": "theblock-elliptic-binance-1106",
        "author": None,
        "outlet": "The Block",
        "lane": "fraud",
        "headline": "Elliptic says Binance hackers swapped stolen tokens for $124M in bitcoin; $2.85B frozen as withdrawals reopen in stages",
        "url": "https://www.theblock.co/news/markets/2026-11-06-binance-hackers-swap-stolen-tokens-124-million-bitcoin-exchange-plans-withdrawal-reopenings-435930",
    },
    {
        "id": "outlookmoney-certin-craftyfalcon-1106",
        "author": None,
        "outlet": "Outlook Money",
        "lane": "fraud",
        "headline": "CERT-In cautions financial firms and crypto exchanges over AI-driven attacks by CRAFTY FALCON on payment APIs and wallet keys",
        "url": "https://www.outlookmoney.com/invest/cert-in-cautions-against-ai-driven-attacks-targeting-crypto-exchanges-financial-firms",
    },
]

NEW_CLUSTERS = [
    {
        "theme": "Root without a login, twice in one day",
        "topic": "Summary — Tech Security",
        "body": "Two different boxes, the same nightmare: root access with no credentials at all. Barracuda's Email Security Gateway can be owned by chaining a 9.3 authorization bypass — which lets an unauthenticated attacker restore a crafted configuration backup — with an 8.6 command injection that runs as root; the patch shipped Monday and the gateway is fixed in version 9.4.0.030. Hours after the SSHole disclosure, attackers were already trying the oversized-password trick against Alpine Linux honeypots and got root in under nine hours, needing only a valid account name and a password between 257 and 1,024 characters. Both fixes exist; the race now is whether admins install them before the scanners find the exposed interfaces.",
        "items": ["thn-barracuda-esg-1106", "thn-sshole-exploited-1106"],
    },
    {
        "theme": "The browser extension that drives your AI agent",
        "topic": "Summary — Tech Security",
        "body": "A browser extension that can run scripts on claude.ai could turn Claude Desktop into a remote shell, researchers at Forever Security showed: Dispatch accepted an ordinary signed-in web session, so an extension could send the desktop agent instructions as if the user had typed them — and auto-approve the prompts. Because Dispatch pairs devices by account, the same trick could reach a second computer, turning a personal browser add-on into a foothold on a work laptop. Anthropic accepted the report as valid in May but closed it as a duplicate, and says Dispatch is being retired — though the researchers warn the same trust model lives on in Claude Code Remote Control and Cowork sessions.",
        "items": ["thn-claude-dispatch-1106"],
    },
    {
        "theme": "The trust layer wobbles",
        "topic": "Summary — Tech Security",
        "body": "Three stories from three very different corners, all about trust. DigiCert began notifying customers after a February 2025 migration left an internal system on the public internet for 16 months, exposing archived records — including passports and driver's licenses for a small minority — with no count disclosed. Researchers found six addresses on the White House network serving as residential proxy exits, used 236 times by 28 proxy services, with the cause still unconfirmed and no breach claimed. And a new extortion group, Whitearmor, listed Unilever on its leak site with a $15M demand and a claimed 79GB haul the company has not confirmed. The lesson is the same from all three angles: the names people trust are the ones attackers aim at — and the ones left doing the explaining.",
        "items": ["theregister-digicert-notices-1106", "securityweek-whitehouse-proxies-1106", "assured-whitearmor-unilever-1106"],
    },
    {
        "theme": "The heist, laundered in the open",
        "topic": "Summary — Fintech Security",
        "body": "The Binance laundering operation is now measurable: Elliptic counts more than 20,000 wallets across 16 blockchains and 65,000 transactions, with about $124M in stolen altcoins already swapped into bitcoin — most of it XRP moved through THORChain — while roughly $3.11B still sits in attacker-linked addresses and $2.85B has been frozen. Chainalysis traces nearly $1B of the flow to Chinese laundering networks, about $500M of it through TRON. Binance, meanwhile, is reopening withdrawals in stages and says it has replenished virtually all customer losses — the heist is becoming a long, public accounting exercise rather than a single event.",
        "items": ["theblock-elliptic-binance-1106", "cryptonomist-binance-laundering-1106"],
    },
    {
        "theme": "India's cyber agency warns the money pipes",
        "topic": "Summary — Fintech Security",
        "body": "India's CERT-In has warned banks, payment firms, and crypto exchanges about AI-driven attacks from a group it calls CRAFTY FALCON, which it rates critical: the attackers exploit payment and disbursement APIs to push through unauthorized transactions and steal wallet keys. The advisory, issued November 4, names non-bank lenders, digital lending platforms, payment aggregators, and virtual-asset exchanges among the targets, and urges firms to isolate affected systems, rotate credentials, and report incidents. The warning lands a week after the Binance heist showed what happens when the same playbook works — the industry's pipes, not just its vaults, are the target now.",
        "items": ["outlookmoney-certin-craftyfalcon-1106"],
    },
]

LOG_CARD_BODY = (
    "Five original summaries on the Lake: two flaws hand out root without a login — Barracuda's email-gateway chain "
    "and the SSHole OpenSSH bypass, already exploited within hours; a browser extension can drive Claude Desktop to run code "
    "through Dispatch; DigiCert's 16-month lapse, proxy exits on the White House network, and Whitearmor's Unilever listing test "
    "the trust layer; and on the fintech side, Elliptic counts $124M of Binance loot swapped into bitcoin while India's CERT-In warns "
    "payment firms about AI-driven attacks. Four stories the earlier editions missed were added first: the Barracuda chain, "
    "Claude Dispatch, Elliptic's laundering update, and the CERT-In warning."
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
anchor = '<p class="feed__date">Friday, November 6, 2026</p>\n'
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
day_anchor = '<span class="day__date">2026-11-06</span>'
assert day_anchor in s
pos = s.index(day_anchor)
close = s.index("</article>", pos) + len("</article>")
card = (
    '\n            <article class="card" data-lane="protect">\n'
    '              <p class="card__meta">Log · Day 17 · Afternoon summaries</p>\n'
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
    "<p><b>Week of Nov 2–8, 2026 — after the 1:30 PM summaries on Nov 6:</b> "
    "Swati Khandelwal (The Hacker News) climbs to 4 stories with the Barracuda root chain and the Claude Dispatch flaw, "
    "while The Block staff and Outlook Money staff join the board at 1. Today's river adds 4 afternoon stories: the Barracuda "
    "Email Security Gateway flaw chain to unauthenticated root, malicious browser extensions driving Claude Desktop through "
    "Dispatch, Elliptic's $124M Binance laundering update, and CERT-In's warning on AI-driven attacks against payment firms "
    "and crypto exchanges.</p>"
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
