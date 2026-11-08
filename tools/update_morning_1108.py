#!/usr/bin/env python3
"""GoldRang3r morning edition updater — 2026-11-08 (Day 19)."""
import json, re, html, os
from collections import Counter

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TODAY = "2026-11-08"
TODAY_LONG = "Sunday, November 8, 2026"
TIME = "7:30 AM"

ITEMS = [
    dict(id="securityweek-sonicwall-1108", outlet="SecurityWeek", author=None,
         headline="CISA adds SonicWall's exploited SSL VPN flaw CVE-2026-19868 to its KEV catalog \u2014 it lets alternate-method credentials bypass SAML and SAML-enforced MFA, with a Nov 20 federal patch deadline",
         url="https://www.securityweek.com/sonicwall-patches-exploited-sonicos-bug-that-weakens-vpn-logins/", lane="protect"),
    dict(id="thn-paint-rce-1108", outlet="The Hacker News", author="Swati Khandelwal",
         headline="Microsoft Paint's remote-code-execution flaw CVE-2026-83844 is fixed only via a Microsoft Store update \u2014 Windows Update won't deliver build 11.2609.401.0",
         url="https://thehackernews.com/2026/11/microsoft-paint-rce-fix-now-available.html", lane="protect"),
    dict(id="thn-gpt6cyber-1108", outlet="The Hacker News", author="Ravie Lakshmanan",
         headline="OpenAI launches GPT-6 Cyber, a security model it rates Critical \u2014 it helped find 81 previously unknown Firefox flaws and built working exploits for 948 Linux kernel bugs",
         url="http://thehackernews.com/2026/11/openai-launches-gpt-6-cyber-after-ai.html", lane="protect"),
    dict(id="sulat-claudecode-1108", outlet="Sulat News", author="JP Caparas",
         headline="Claude Code's 'Don't Ask Again' saved approved commands \u2014 passwords and keys included \u2014 into .claude/settings.local.json; Apiiro found 2,539 secrets across 1,994 public GitHub repos",
         url="https://news.sulat.com/2026/11/08/claude-code-dont-ask-again-settings-secrets-github/", lane="bug"),
    dict(id="tokenpost-chainalysis-1108", outlet="TokenPost", author=None,
         headline="Chainalysis restores Reactor, KYT and Address Screening after disclosing that names, password hashes and live tokens for all users were exposed \u2014 Data Solutions and Chain (Beta) still offline",
         url="https://www.tokenpost.com/news/technology/51371", lane="protect"),
    dict(id="hispion-digicert-1108", outlet="Hispion News", author=None,
         headline="DigiCert confirms a breach after a server migration left an internal archive exposed \u2014 customer contact data plus some passports and driver's licenses were accessed June 27\u2013July 2",
         url="https://www.hispion.com/en/news/2026/11/06/digicert-discloses-breach-exposing-identity-documents-and-customer-data/", lane="protect"),
    dict(id="crowdstrike-killswitch-1108", outlet="CrowdStrike", author=None,
         headline="CrowdStrike ships an AI Kill Switch in Falcon Guardian to stop rogue agents at runtime, and agrees to buy Fiddler AI (reported ~$400M) and Dreadnode to watch and test them",
         url="https://www.crowdstrike.com/en-us/press-releases/crowdstrike-delivers-ai-security-safety-for-the-enterprise/", lane="protect"),
    dict(id="msft-artex-1108", outlet="Microsoft Security Blog", author=None,
         headline="Storm-3358, a Cambodia-based financially motivated group, is running the ARTEX agentic AI framework against financial firms in Southeast Asia, exploiting file-upload and SSRF flaws to plant RATs",
         url="https://www.microsoft.com/en-us/security/blog/2026/11/06/artex-abuse-expands-as-cybercriminals-target-financial-sector/", lane="fraud"),
    dict(id="hindu-craftyfalcon-1108", outlet="The Hindu BusinessLine", author=None,
         headline="India's CERT-In warns banks, NBFCs and fintechs that the AI-assisted 'CRAFTY FALCON' campaign is stealing funds through victims' own payment APIs at machine speed",
         url="https://www.thehindubusinessline.com/money-and-banking/central-cyber-security-agency-warns-banks-fintech-firms-of-ai-powered-frauds/article71667190.ece/amp/", lane="fraud"),
    dict(id="thedecoder-anthropic-ipo-1108", outlet="The Decoder", author=None,
         headline="Anthropic presses ahead with its pre-Thanksgiving IPO despite the tech selloff, accepting a $1.25\u20131.75T valuation \u2014 below the $2T once hoped for \u2014 with the roadshow starting next week",
         url="https://the-decoder.com/anthropic-pushes-ahead-with-pre-thanksgiving-ipo-despite-tech-selloff-accepts-lower-valuation/", lane=None),
    dict(id="crosswalk-shieldai-1108", outlet="Crosswalk", author=None,
         headline="Shield AI raises $1B Series H at a $28.8B valuation, part of a $2.5B financing to fund its up-to-$5.3B acquisition of radar maker Echodyne",
         url="https://crosswalk.to/crosswalk/deals/2026-11-08", lane=None),
    dict(id="crosswalk-zipline-1108", outlet="Crosswalk", author=None,
         headline="Zipline raises $1.5B at a $21.5B valuation for its autonomous drone delivery network, as Northwood Space lands a $375M Series C at $2B",
         url="https://crosswalk.to/crosswalk/deals/2026-11-08", lane=None),
]

CLUSTERS = [
    ("SAML, MFA, and the VPN that skipped both", ["securityweek-sonicwall-1108"]),
    ("The fix that only the Store delivers", ["thn-paint-rce-1108"]),
    ("AI that finds the bugs \u2014 and the one that leaked the keys", ["thn-gpt6cyber-1108", "sulat-claudecode-1108"]),
    ("Two breaches, widening disclosures", ["tokenpost-chainalysis-1108", "hispion-digicert-1108"]),
    ("A kill switch for rogue agents", ["crowdstrike-killswitch-1108"]),
    ("ARTEX goes after the banks", ["msft-artex-1108", "hindu-craftyfalcon-1108"]),
    ("The IPO that met the rout \u2014 and the funding that didn't blink", ["thedecoder-anthropic-ipo-1108", "crosswalk-shieldai-1108", "crosswalk-zipline-1108"]),
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
    latest[(rep, it["outlet"])] = it
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
second = [r for r in rows[1:] if r[1] == rows[1][1]][:2] if len(rows) > 1 else []
second_txt = ""
if second:
    names = ", ".join(f"{esc(r[0][0])} ({esc(r[0][1])})" for r in second)
    second_txt = f" {names} follow at {second[0][1]} each."
note = (f'<p><b>Week of Nov 2\u20138, 2026 \u2014 after the 7:30 AM edition on Nov 8:</b> '
        f'{esc(top[0][0])} ({esc(top[0][1])}) leads at {top[1]} stories;{second_txt} '
        f'Today\u2019s river adds 12 stories: CISA\u2019s KEV listing for SonicWall\u2019s exploited SAML-bypass flaw, a Store-only fix for a Paint RCE, OpenAI\u2019s GPT-6 Cyber, and Claude Code leaking secrets to public repos on the security side; '
        f'Chainalysis and DigiCert widening their breach disclosures; CrowdStrike\u2019s AI Kill Switch; ARTEX and CRAFTY FALCON targeting the financial sector; plus Anthropic\u2019s IPO pressing on at a lower valuation and $1B-plus rounds for Shield AI and Zipline.</p>')
lb = re.sub(r'<div class="note">\s*<p>.*?</p>\s*</div>', f'<div class="note">\n          {note}\n        </div>', lb, count=1, flags=re.S)
open(lb_path, "w").write(lb)

# ---------- log.html ----------
log_path = os.path.join(BASE, "log.html")
log = open(log_path).read()
anchor = '        <div class="day">'
pos = log.index(anchor)
card = ('        <div class="day">\n'
        '          <div class="day__head">\n'
        '            <span class="day__date">2026-11-08</span>\n'
        '            <span class="day__dow">Sunday \u00b7 Day 19</span>\n'
        '          </div>\n'
        '          <div class="grid">\n'
        '            <article class="card" data-lane="protect">\n'
        '              <p class="card__meta">Log \u00b7 Day 19 \u00b7 Publication</p>\n'
        '              <h3>7:30 AM \u2014 the morning edition is live</h3>\n'
        '              <p>Twelve stories on the river: CISA adds SonicWall\u2019s exploited SSL VPN flaw CVE-2026-19868 to its KEV catalog, Microsoft Paint\u2019s RCE fix arrives only through the Store, OpenAI launches GPT-6 Cyber after it helped find 81 Firefox flaws, and Claude Code\u2019s \u201cDon\u2019t Ask Again\u201d left 2,539 secrets in public repos. Fintech security: Chainalysis restores services after its all-users credential exposure, DigiCert confirms a breach touching passports and driver\u2019s licenses, and India\u2019s CERT-In warns of the AI-assisted CRAFTY FALCON campaign while Microsoft tracks ARTEX hitting banks. Plus CrowdStrike\u2019s AI Kill Switch, Anthropic\u2019s IPO at a lower valuation, and $1B-plus rounds for Shield AI and Zipline.</p>\n'
        '              <p class="card__foot"><a class="text-link" href="index.html">Read the river \u2192</a></p>\n'
        '            </article>\n\n'
        '          </div>\n'
        '        </div>\n\n')
log = log[:pos] + card + log[pos:]
open(log_path, "w").write(log)

print("items:", len(ITEMS), "| clusters:", len(CLUSTERS), "| week reporters:", len(rows))
print("top:", top)
print("total items in store:", len(data["items"]))
