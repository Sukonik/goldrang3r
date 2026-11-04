#!/usr/bin/env python3
"""GoldRang3r morning edition updater — 2026-11-04 (Day 15)."""
import json, re, html, os
from collections import Counter, defaultdict

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TODAY = "2026-11-04"
TODAY_LONG = "Wednesday, November 4, 2026"
TIME = "7:30 AM"

ITEMS = [
    dict(id="bleeping-apt29-1104", outlet="BleepingComputer", author=None,
         headline="Sekoia links Russia's APT29 to a watering-hole campaign using already-patched iOS and Android flaws to steal cookies, chat databases, credentials and photos from visitors to compromised sites \u2014 no click needed",
         url="https://www.bleepingcomputer.com/news/security/hackers-use-n-day-exploits-in-zero-click-attacks-on-ios-android-devices/", lane="protect"),
    dict(id="bleeping-wordpress-kev-1104", outlet="BleepingComputer", author=None,
         headline="CISA flags a high-severity WordPress Core race-condition flaw, CVE-2026-119977, as actively exploited and orders federal civilian agencies to patch by Friday",
         url="https://www.bleepingcomputer.com/news/security/cisa-flags-wordpress-rce-flaw-as-actively-exploited-in-attacks/", lane="protect"),
    dict(id="abijita-cpguard-1104", outlet="Abijita", author=None,
         headline="OPSSHIELD says attackers used stolen credentials to hijack cPGuard's update channel on November 2, pushing a backdoor and data-stealing script to versions 5.88.12\u20135.88.19; a spokesperson put affected servers at 2,946",
         url="https://www.abijita.com/cpguard-update-hijack-linux-servers/", lane="protect"),
    dict(id="f5-panos-1104", outlet="F5 Labs", author=None,
         headline="Attackers chained PHP2Shell RCE flaws with a Linux kernel privilege-escalation bug to compromise 25 PAN-OS systems, including 24 perimeter firewalls, and tunnel into a US government-affiliated environment",
         url="https://www.f5.com/labs/articles/weekly-threat-bulletin-november-4th-2026", lane="protect"),
    dict(id="threatpodium-kev-1104", outlet="ThreatPodium", author=None,
         headline="Five vulnerabilities join CISA's exploited list this week as ransomware leak sites post 255 victims in seven days, with Thegentlemen claiming the most",
         url="https://threatpodium.com/threat-intelligence-report-2026-11-04/", lane=None),
    dict(id="itsecurity-overnight-blood-1104", outlet="IT Security News", author=None,
         headline="Attackers reportedly reprogrammed French blood-service freezers from \u221230\u00b0C to 110\u00b0C, threatening critical plasma supplies, in a morning dominated by cold-chain attacks across Europe",
         url="https://www.itsecuritynews.info/it-security-news-roundup-2026-11-04-overnight/", lane="protect"),
    dict(id="fintechnews-binance-1104", outlet="Fintech News Singapore", author=None,
         headline="Binance's account of the $6.3B heist: a five-month campaign from a fake recruiter and a tampered AI tool to drained hot wallets in minutes \u2014 with 95% of stolen tokens now replenished, says co-CEO Richard Teng",
         url="https://fintechnews.sg/140431/crypto/how-the-binance-6-billion-crypto-hack-happened/", lane="fraud"),
    dict(id="coincourier-arkea-1104", outlet="CoinCourier", author=None,
         headline="On-chain investigator ZachXBT names French banking group Cr\u00e9dit Mutuel Ark\u00e9a as the suspected victim of a $133M crypto theft across Kraken, Crypto.com and OKX \u2014 a claim the bank has not confirmed beyond acknowledging fraudulent transactions",
         url="https://coincourier.io/zachxbt-french-bank-suspected-crypto-theft/", lane="fraud"),
    dict(id="itsecurity-morning-chainalysis-1104", outlet="IT Security News", author=None,
         headline="Chainalysis reports an AI-driven incident in which an external actor stole non-sensitive customer data, the latest hit in a wave of AI-powered attacks on crypto firms",
         url="https://www.itsecuritynews.info/it-security-news-roundup-2026-11-04-morning/", lane=None),
    dict(id="cognarah-fal-1104", outlet="Cognarah", author=None,
         headline="AI inference startup Fal closes a $1.3B Series F led by Bessemer, doubling its valuation to $16B as demand for AI media generation keeps climbing",
         url="https://www.cognarah.com/article/fal-raises-dollar13-billion-doubles-valuation-to-dollar16-billion-on-inference-demand-mw1rqhvz", lane=None),
    dict(id="tech-eu-stationf-1104", outlet="Tech.eu", author=None,
         headline="STATION F unveils its 2026 Future 40 \u2014 sovereign AI and physical AI lead the themes \u2014 as campus startups raise a record \u20ac2B this year",
         url="https://tech.eu/2026/11/04/station-f-startups-raise-record-2b-as-campus-unveils-2026-future-40/", lane=None),
    dict(id="yourstory-canva-1104", outlet="YourStory", author=None,
         headline="Canva cuts 1,271 roles, about 22% of its workforce, as growth slows and product work is reorganised; India's EloElo raises $80M in Series C",
         url="https://yourstory.com/2026/11/startup-news-and-updates-daily-roundup-november-4-2026", lane=None),
]

CLUSTERS = [
    ("Zero-click phones, patched flaws", ["bleeping-apt29-1104"]),
    ("Exploited flaws, from WordPress to firewalls", ["bleeping-wordpress-kev-1104", "f5-panos-1104", "threatpodium-kev-1104"]),
    ("A hijacked update channel", ["abijita-cpguard-1104"]),
    ("Blood freezers, turned to 110\u00b0C", ["itsecurity-overnight-blood-1104"]),
    ("Crypto's ledger: a heist reconstructed, a second theft named", ["fintechnews-binance-1104", "coincourier-arkea-1104", "itsecurity-morning-chainalysis-1104"]),
    ("Inference money, still flowing", ["cognarah-fal-1104"]),
    ("Paris campus, record year \u2014 and Canva cuts deep", ["tech-eu-stationf-1104", "yourstory-canva-1104"]),
]

def esc(s):
    return html.escape(s, quote=True)

def source_label(it):
    return f"{it['author']} / {it['outlet']}:" if it["author"] else f"{it['outlet']}:"

def feed_item(it):
    body = f'<span class="feed__source">{esc(source_label(it))}</span> '
    if it["url"]:
        body += f'<a href="{esc(it["url"])}">{esc(it["headline"])}</a>'
    else:
        body += esc(it["headline"])
    if it["lane"]:
        body += f'<span class="feed__tag" data-lane="{it["lane"]}">{it["lane"]}</span>'
    return (f'      <div class="feed__item">\n'
            f'        <span class="feed__time">{TIME}</span>\n'
            f'        <p class="feed__body">{body}</p>\n'
            f'      </div>\n')

def cluster_item(it):
    if it["url"]:
        return f'          <li><b>{esc(it["outlet"])}:</b> <a href="{esc(it["url"])}">{esc(it["headline"])}</a></li>\n'
    return f'          <li><b>{esc(it["outlet"])}:</b> {esc(it["headline"])}</li>\n'

# ---------- news.json ----------
nj_path = os.path.join(BASE, "data", "news.json")
data = json.load(open(nj_path))
by_id = {it["id"]: it for it in data["items"]}
for it in ITEMS:
    assert it["id"] not in by_id, f"duplicate id {it['id']}"
    data["items"].append({**it, "date": TODAY, "time": TIME})
for theme, ids in CLUSTERS:
    data["clusters"].append({"date": TODAY, "theme": theme, "topic": "Morning edition", "items": ids})
data["edition"] = TODAY
json.dump(data, open(nj_path, "w"), ensure_ascii=False, indent=2)
open(nj_path, "a").write("\n")

# ---------- index.html ----------
idx_path = os.path.join(BASE, "index.html")
idx = open(idx_path).read()
idx = re.sub(r'(<p class="hero__signal"><span class="dot">\u25cf</span> Edition \u2014 )[^<]+(</p>)',
             r'\g<1>' + TODAY_LONG + ' \u00b7 Morning river below' + r'\g<2>', idx, count=1)
idx = re.sub(r'(<h2 class="section-title" id="river-title">)[^<]+(</h2>)',
             r'\g<1>' + TODAY_LONG + r'\g<2>', idx, count=1)
start = idx.index("<!-- RIVER:START -->") + len("<!-- RIVER:START -->")
end = idx.index("<!-- RIVER:END -->")
river = idx[start:end]
# split river into day sections at each feed__date marker
parts = re.split(r'(?=<p class="feed__date">)', river)
head, days = parts[0], parts[1:]
new_day = f'        <p class="feed__date">{TODAY_LONG}</p>\n        <div class="feed">\n'
new_day += "".join(feed_item(it) for it in ITEMS)
new_day += "        </div>\n\n\n"
kept = [new_day] + days[:2]  # today + previous 2 days = max 3 days
idx = idx[:start] + head + "".join(kept) + idx[end:]
open(idx_path, "w").write(idx)

# ---------- lake.html ----------
lake_path = os.path.join(BASE, "lake.html")
lake = open(lake_path).read()
start = lake.index("<!-- LAKE:START -->") + len("<!-- LAKE:START -->")
end = lake.index("<!-- LAKE:END -->")
lake_body = lake[start:end]
parts = re.split(r'(?=<p class="feed__date">)', lake_body)
head, days = parts[0], parts[1:]
by_id2 = {it["id"]: it for it in data["items"]}
new_block = f'        <p class="feed__date">{TODAY_LONG}</p>\n\n'
for theme, ids in CLUSTERS:
    new_block += ('        <article class="cluster">\n'
                  '          <p class="cluster__meta">Cluster \u00b7 Morning edition</p>\n'
                  f'          <h2 class="cluster__title">{esc(theme)}</h2>\n'
                  '          <ul class="cluster__items">\n')
    for i in ids:
        new_block += cluster_item(by_id2[i])
    new_block += '          </ul>\n        </article>\n\n'
kept = [new_block] + days[:1]  # today + previous day = max 2 days
lake = lake[:start] + head + "".join(kept) + lake[end:]
open(lake_path, "w").write(lake)

# ---------- leaderboards.html ----------
lb_path = os.path.join(BASE, "leaderboards.html")
lb = open(lb_path).read()
week = [it for it in data["items"] if "2026-11-02" <= it["date"] <= "2026-11-08"]
counts = Counter()
latest = {}
for it in week:
    rep = it["author"] if it["author"] else f"{it['outlet']} staff"
    counts[(rep, it["outlet"])] += 1
    latest[(rep, it["outlet"])] = it  # items appended chronologically; last wins
rows = sorted(counts.items(), key=lambda kv: (-kv[1], kv[0][0]))
def trunc(h, n=50):
    return h[:n] + "\u2026" if len(h) > n else h
tbody = ""
for (rep, outlet), n in rows:
    rank = 1 + sum(1 for c in counts.values() if c > n)
    it = latest[(rep, outlet)]
    mmdd = it["date"][5:]
    tbody += (f'              <tr><td><b>{rank}</b></td><td><b>{esc(rep)}</b></td>'
              f'<td>{esc(outlet)}</td><td>{n}</td>'
              f'<td>{esc(trunc(it["headline"]))} \u2014 {mmdd}</td></tr>\n')
start = lb.index("<!-- LEADERBOARD:START -->") + len("<!-- LEADERBOARD:START -->")
end = lb.index("<!-- LEADERBOARD:END -->")
new_table = ('\n        <div class="table-wrap">\n          <table class="table">\n'
             '            <thead><tr><th>Rank</th><th>Reporter</th><th>Outlet</th><th>Stories tracked</th><th>Latest</th></tr></thead>\n'
             '            <tbody>\n' + tbody + '            </tbody>\n          </table>\n        </div>\n')
lb = lb[:start] + new_table + lb[end:]
top = rows[0]
note = (f'<p><b>Week of Nov 2\u20138, 2026 \u2014 after the 7:30 AM edition on Nov 4:</b> '
        f'{esc(top[0][0])} ({esc(top[0][1])}) leads at {top[1]} stories; '
        f'BleepingComputer staff and Tech.eu staff follow at 3 each, and IT Security News staff joins the board at 2 with the overnight and morning roundups. '
        f'Today\u2019s river adds 12 stories: the APT29 watering-hole campaign, a hijacked cPGuard update channel, and a growing exploited-flaw list on the security side; '
        f'Binance\u2019s heist reconstruction and the newly named suspected $133M Arkea theft in fintech; plus Fal\u2019s $1.3B round, STATION F\u2019s record year, and Canva\u2019s 1,271-role cut.</p>')
lb = re.sub(r'<div class="note">\s*<p>.*?</p>\s*</div>', f'<div class="note">\n          {note}\n        </div>', lb, count=1, flags=re.S)
open(lb_path, "w").write(lb)

# ---------- log.html ----------
log_path = os.path.join(BASE, "log.html")
log = open(log_path).read()
anchor = '        <div class="day">'
pos = log.index(anchor)
card = ('        <div class="day">\n'
        '          <div class="day__head">\n'
        '            <span class="day__date">2026-11-04</span>\n'
        '            <span class="day__dow">Wednesday \u00b7 Day 15</span>\n'
        '          </div>\n'
        '          <div class="grid">\n'
        '            <article class="card" data-lane="protect">\n'
        '              <p class="card__meta">Log \u00b7 Day 15 \u00b7 Publication</p>\n'
        '              <h3>7:30 AM \u2014 the morning edition is live</h3>\n'
        '              <p>Twelve stories on the river: Sekoia links Russia\u2019s APT29 to zero-click watering-hole attacks on unpatched iPhones and Androids, OPSSHIELD says a hijacked cPGuard update channel hit 2,946 servers, CISA flags an actively exploited WordPress Core flaw, and attackers chain PHP2Shell flaws to breach 25 PAN-OS systems. Fintech security: Binance reconstructs the $6.3B fake-recruiter heist while ZachXBT names Cr\u00e9dit Mutuel Ark\u00e9a as the suspected victim of a $133M theft, and Chainalysis reports an AI-driven data incident. Plus Fal\u2019s $1.3B round at a $16B valuation, STATION F\u2019s record \u20ac2B year, and Canva cutting 1,271 roles.</p>\n'
        '              <p class="card__foot"><a class="text-link" href="index.html">Read the river \u2192</a></p>\n'
        '            </article>\n\n'
        '          </div>\n'
        '        </div>\n\n')
log = log[:pos] + card + log[pos:]
open(log_path, "w").write(log)

print("items:", len(ITEMS), "| clusters:", len(CLUSTERS), "| week reporters:", len(rows))
print("top:", top)
