#!/usr/bin/env python3
"""GoldRang3r afternoon summaries — Mon 2026-11-09 1:30 PM ET."""
import json, html, subprocess
from collections import Counter
from pathlib import Path

BASE = Path.home() / "workspace" / "goldrang3r"
TODAY = "2026-11-09"
TIME = "1:30 PM"

NEW_ITEMS = [
    {
        "id": "theregister-tum-breach-1109",
        "author": None,
        "outlet": "The Register",
        "lane": "protect",
        "headline": "Portal breach at Germany's top university exposes every registered user's password — attackers stole central-login passwords for all myTUM users, including a TUMonline admin, and the campus system was taken offline",
        "url": "https://www.theregister.com/cyber-crime/2026/11/09/portal-breach-at-germanys-top-university-exposes-every-registered-users-password/5308380",
    },
    {
        "id": "techmaniacs-frontline-education-1109",
        "author": None,
        "outlet": "Tech Maniacs",
        "lane": "protect",
        "headline": "Frontline Education tells Indiana regulators its August breach hit 3M+ school district staff and students",
        "url": "https://techmaniacs.com/2026/11/09/cyber-briefing-nov-9-openssh-sshole-exploit-and-react-rce-pose-urgent-patching-needs/",
    },
    {
        "id": "thehackernews-debian-apt-1109",
        "author": "Ravie Lakshmanan",
        "outlet": "The Hacker News",
        "lane": "bug",
        "headline": "Debian and Ubuntu APT flaw CVE-2026-109518 lets an attacker run code as root when installing a package under certain conditions",
        "url": "https://thehackernews.com/2026/11/weekly-recap-sshole-exploited-apt-root.html",
    },
]

NEW_CLUSTERS = [
    {
        "theme": "Four breaches, one morning",
        "topic": "Summary — Tech Security",
        "body": "Attackers stole the central-login passwords of everyone registered on the Technical University of Munich's myTUM portal — including a TUMonline administrator, whose credentials were then used against the campus management system, which the university took offline and restored Monday morning with password resets. Revolve told regulators its September attack hit more than 1.5 million people, and Iris Plaza, a Japanese homeware platform, may have exposed 7.7 million customers after a cloud-service compromise forced it to pull its online store. Frontline Education told Indiana regulators its August breach affected more than 3 million school district staff and students.",
        "items": ["theregister-tum-breach-1109", "securityweek-revolve-data-breach-1109",
                  "securityweek-iris-plaza-breach-1109", "techmaniacs-frontline-education-1109"],
    },
    {
        "theme": "Exploitation, confirmed",
        "topic": "Summary — Tech Security",
        "body": "Hackers are now actively breaching Linux systems through the OpenSSH \u201cssHole\u201d authentication bypass, CVE-2026-123158, using it to run commands, steal credentials and set up persistent access — days after the fix shipped, with SANS honeypots already logging attempts from 13 IP addresses. The same morning, CISA added a second actively exploited flaw to its catalog: CVE-2026-102895, an authentication bypass in GPUStack that gives unauthenticated attackers full administrative access, including creating persistent admin API keys, with a federal patch deadline of November 12. Both flaws share a shape — authentication that can simply be walked around — and both are already being used, not just theorized.",
        "items": ["bleepingcomputer-hackers-exploit-sshole-1109", "cisa-cisa-adds-cve-2026-102895-1109"],
    },
    {
        "theme": "The tools that bite back",
        "topic": "Summary — Tech Security",
        "body": "Fake GitHub security tools have infected more than 2,000 PCs with malware that disables defenses and steals data, Doctor Web found — a campaign that ran for two years, turning the very tools people download to stay safe into the attack. On the same day, a flaw in the APT package manager used by Debian and Ubuntu, CVE-2026-109518, was disclosed: under certain conditions it can be exploited to install a package and run code as root. The lesson of both is the same — the software you trust to protect or update your system is itself a target, and the fix in both cases is to get it from a source you can verify.",
        "items": ["cybernoz-fake-github-tools-1109", "thehackernews-debian-apt-1109"],
    },
    {
        "theme": "A bad morning for crypto custody",
        "topic": "Summary — Fintech Security",
        "body": "A flaw in Web3Auth let an attacker drain Keplr crypto wallets set up with Google or Apple sign-in, stealing at least $1 million, per GoPlus — and Web3Auth responded by emptying other at-risk wallets into recovery itself. Separately, Ankr's Ethereum bridge lost more than $303,000 after an attacker replayed a redeemed deposit receipt to bypass withdrawal checks in five unauthorized withdrawals. And California ordered crypto ATM operator CoinFlip to pay more than $4.8 million to fraud victims, mostly elderly, after its roughly 500 ATMs failed identity checks since 2021. Three different weak points — the sign-in layer, the bridge, and the ATM — and the same outcome: money gone before anyone noticed.",
        "items": ["thehackernews-web3auth-keplr-1109", "defiplanet-ankr-bridge-1109", "panews-coinflip-1109"],
    },
    {
        "theme": "Claim, deny, repeat",
        "topic": "Summary — Fintech Security",
        "body": "Binance has denied claims of a new data breach after a threat actor using the ShinyHunters handle posted allegations on a newly emerged underground forum; the exchange says there is no breach, and nothing has been independently confirmed. The same day, ransomware group N0n listed Expedia on its leak site and claimed 830 million loyalty records were stolen — also unverified, and Expedia has not confirmed a breach. Two giant claims, two denials or silences, and no evidence either way: the leak-site post is the story now, and the verification comes later, if it comes at all.",
        "items": ["bleepingcomputer-binance-denies-data-1109", "dunyadesk-expedia-ransomware-1109"],
    },
]

LOG_CARD_BODY = (
    "Five original summaries on the Lake: four breaches in one morning — TUM's stolen passwords for every myTUM user, Revolve at 1.5M, "
    "Iris Plaza at 7.7M, and Frontline Education at 3M+; the OpenSSH 'ssHole' bypass is now confirmed in live breaches while CISA adds the "
    "GPUStack auth bypass to its exploited list; fake GitHub security tools infected 2,000+ PCs and a Debian/Ubuntu APT flaw allows root code "
    "execution; a bad morning for crypto custody as Web3Auth's flaw drains Keplr wallets, Ankr's bridge loses $303K, and CoinFlip is ordered to "
    "pay $4.8M to fraud victims; and the claim-deny pattern as Binance denies a ShinyHunters breach claim while N0n claims 830M Expedia "
    "loyalty records, both unverified. Three stories the earlier editions missed were added first: the TUM university breach, the Frontline "
    "Education breach, and the Debian/Ubuntu APT root flaw."
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
      len([i for i in data["items"] if i["date"] == TODAY]),
      "| today clusters:", len([c for c in data["clusters"] if c["date"] == TODAY]))

# ---------- 2. lake.html ----------
p = BASE / "lake.html"
s = p.read_text()
anchor = '<p class="feed__date">Monday, November 9, 2026</p>\n'
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
day_anchor = '<span class="day__date">2026-11-09</span>'
assert day_anchor in s
pos = s.index(day_anchor)
close = s.index("</article>", pos) + len("</article>")
card = (
    '\n            <article class="card" data-lane="protect">\n'
    '              <p class="card__meta">Log · Day 20 · Afternoon summaries</p>\n'
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
week = [it for it in data["items"] if "2026-11-09" <= it["date"] <= "2026-11-15"]
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
note_old_start = s.index('<p><b>Week of Nov 9–15, 2026')
note_old_end = s.index("</p>", note_old_start) + len("</p>")
note_new = (
    "<p><b>Week of Nov 9–15, 2026 — after the 1:30 PM summaries on Nov 9:</b> "
    "The Neuron staff (The Neuron) still leads at 2 stories. The Register staff joins the board at 1 with the TUM university breach; "
    "Tech Maniacs staff joins at 1 with the Frontline Education breach; and Ravie Lakshmanan (The Hacker News) joins at 1 with the "
    "Debian/Ubuntu APT flaw. Today's river adds 3 afternoon stories: the TUM university breach, the Frontline Education breach, and the "
    "Debian/Ubuntu APT root flaw.</p>"
)
s = s[:note_old_start] + note_new + s[note_old_end:]
p.write_text(s)
print("leaderboards.html updated; week total:", len(week))
print("Top 5:", ranked[:5])

# ---------- 5. forbidden-word check ----------
r = subprocess.run(["grep", "-ri", "goldranger", "--include=*.html", "--include=*.json",
                    "lake.html", "leaderboards.html", "log.html", "data/news.json"],
                   capture_output=True, text=True, cwd=BASE)
print("forbidden-word hits in edited files:", repr(r.stdout) or "none")
