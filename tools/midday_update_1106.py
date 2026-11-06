#!/usr/bin/env python3
"""GoldRang3r midday update — Fri 2026-11-06 12:30 PM ET."""
import json, html, re
from collections import Counter
from pathlib import Path

BASE = Path.home() / "workspace" / "goldrang3r"
TODAY = "2026-11-06"
TIME = "12:30 PM"

NEW_ITEMS = [
    {
        "id": "thn-sshole-exploited-1106",
        "author": "Ravie Lakshmanan",
        "outlet": "The Hacker News",
        "lane": "protect",
        "headline": "Hackers target the SSHole OpenSSH flaw within hours of disclosure, gaining root on an Alpine Linux honeypot — the musl bypass needs only an oversized password",
        "url": "http://thehackernews.com/2026/11/hackers-exploited-openssh-sshole-flaw.html",
    },
    {
        "id": "theregister-digicert-notices-1106",
        "author": None,
        "outlet": "The Register",
        "lane": "protect",
        "headline": "DigiCert begins notifying customers after a 16-month lapse left archived records exposed — passports and driver's licenses among the data, with no count disclosed yet",
        "url": "https://www.theregister.com/security/2026/11/06/digicert-admits-16-month-security-lapse-exposed-customer-information/5308097",
    },
    {
        "id": "securityweek-whitehouse-proxies-1106",
        "author": None,
        "outlet": "SecurityWeek",
        "lane": "protect",
        "headline": "Residential proxy exits found on the White House network — six addresses used by 28 services 236 times, with the cause unconfirmed",
        "url": "https://www.securityweek.com/researchers-find-residential-proxies-on-white-house-network/",
    },
    {
        "id": "dealroom-tml-5b-1106",
        "author": None,
        "outlet": "Dealroom",
        "lane": None,
        "headline": "Thinking Machines Lab nears a $5B round at a $40B pre-money valuation led by Accel, Business Insider reports — more than triple its $12B seed valuation",
        "url": "https://dealroom.co/news/170334-thinking-machines-lab-nears-5b-round-at-40b-valuation-led-by-accel/",
    },
    {
        "id": "vccafe-salesforce-rune-1106",
        "author": None,
        "outlet": "VC Cafe",
        "lane": None,
        "headline": "Salesforce agrees to buy defense-logistics startup Rune Technologies for a reported $375M",
        "url": "https://www.vccafe.com/weekly-firgun-newsletter-november-6-2026/",
    },
    {
        "id": "crosswalk-cesiumastro-1106",
        "author": None,
        "outlet": "Crosswalk",
        "lane": None,
        "headline": "CesiumAstro raises a $730M Series D led by Janus Henderson at a valuation over $4.5B for space and defense communications systems",
        "url": "https://crosswalk.to/crosswalk/deals",
    },
    {
        "id": "vccafe-brava-seed-1106",
        "author": None,
        "outlet": "VC Cafe",
        "lane": "protect",
        "headline": "Brava Security comes out of stealth with a $15M seed round to test whether a company's alarms would actually fire in a real attack",
        "url": "https://www.vccafe.com/weekly-firgun-newsletter-november-6-2026/",
    },
]

NEW_CLUSTERS = [
    {
        "theme": "SSHole, exploited within hours",
        "topic": "Summary — Tech Security",
        "body": "The patch was barely a day old when attackers moved: Previdian saw the first SSHole exploitation attempt less than nine hours after disclosure and confirmed root access on an Alpine Linux honeypot, using oversized passwords against accounts with no usable password set. The flaw, CVE-2026-123158, hits OpenSSH on musl libc with PAM disabled — Alpine's default server configuration — and the fix is OpenSSH 10.6p2, with sshd restarted after patching.",
        "items": ["thn-sshole-exploited-1106"],
    },
    {
        "theme": "DigiCert's 16-month lapse reaches customers",
        "topic": "Summary — Tech Security",
        "body": "DigiCert has begun notifying customers after a February 2025 server migration moved an internal business system onto the public internet, where an unauthorized account read archived records between June 27 and July 2, 2026. The data includes names, business emails, phone numbers and addresses — and, for a small minority, passports, driver's licenses and utility bills. The company found the accounts in June, confirmed the access on October 19, and has not said how many people are affected; its certificate authority services were not touched.",
        "items": ["theregister-digicert-notices-1106"],
    },
    {
        "theme": "Proxy exits on the White House network",
        "topic": "Summary — Tech Security",
        "body": "Layer3 Intel found six IP addresses on AS2650, the network reserved for the Executive Office of the President, serving as residential proxy exits — used by 28 proxy services 236 times between October 5 and November 3, mostly in the evening hours. Synthient traces the traffic to Windows 11 machines running the Infatica SDK. The cause is unconfirmed and no breach is claimed: the finding rests on the address registration, not an identified device — but anyone signing up to a public proxy service could route traffic through the network.",
        "items": ["securityweek-whitehouse-proxies-1106"],
    },
    {
        "theme": "Midday checks: the $5B lab and three more",
        "topic": "Summary — Tech",
        "body": "Thinking Machines Lab is near a $5B round at a $40B pre-money valuation led by Accel, Business Insider reports — more than triple the roughly $12B mark from its $2B seed last year, and the round could close within days. Salesforce agreed to buy defense-logistics startup Rune Technologies for a reported $375M, and CesiumAstro raised a $730M Series D led by Janus Henderson at a valuation over $4.5B for space and defense communications. Brava Security came out of stealth with a $15M seed to test whether a company's alarms would actually fire in a real attack.",
        "items": ["dealroom-tml-5b-1106", "vccafe-salesforce-rune-1106", "crosswalk-cesiumastro-1106", "vccafe-brava-seed-1106"],
    },
]

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
print("news.json: total items now", len(data["items"]))

# ---------- 2. index.html ----------
p = BASE / "index.html"
s = p.read_text()
old_hero = "Edition — Friday, November 6, 2026 · Morning river below"
new_hero = "Edition — Friday, November 6, 2026 · Midday update at 12:30 PM — river below"
assert old_hero in s
s = s.replace(old_hero, new_hero)

anchor = '<!-- RIVER:START -->\n        <p class="feed__date">Friday, November 6, 2026</p>\n        <div class="feed">\n'
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
anchor = '<p class="feed__date">Friday, November 6, 2026</p>\n'
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
        f'          <p class="cluster__meta">Cluster · Midday edition · {esc(c["topic"])}</p>\n'
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
    "<p><b>Week of Nov 2–8, 2026 — after the 12:30 PM edition on Nov 6:</b> "
    "Ravie Lakshmanan (The Hacker News) takes the sole lead at 6 stories; SecurityWeek staff and Dealroom staff climb to 2 each, "
    "and VC Cafe staff joins the board at 2 with the Salesforce–Rune deal and Brava's stealth exit, while The Register staff and "
    "Crosswalk staff join at 1. Today's river adds 7 midday stories: attackers exploiting the SSHole OpenSSH flaw within hours, "
    "DigiCert's customer notifications after a 16-month lapse, and residential proxy exits on the White House network on the security side; "
    "plus Thinking Machines Lab's near-$5B round at a $40B valuation, Salesforce's reported $375M Rune buy, CesiumAstro's $730M Series D, "
    "and Brava Security's $15M stealth exit.</p>"
)
s = s[:note_old_start] + note_new + s[note_old_end:]
p.write_text(s)
print("leaderboards.html updated; week total:", len(week))
print("Top 5:", ranked[:5])

# ---------- 5. forbidden-word check ----------
import subprocess
r = subprocess.run(["grep", "-ri", "goldranger", "--include=*.html", "--include=*.json",
                    "index.html", "lake.html", "leaderboards.html", "data/news.json"],
                   capture_output=True, text=True, cwd=BASE)
print("forbidden-word hits in edited files:", repr(r.stdout) or "none")
