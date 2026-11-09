#!/usr/bin/env python3
"""GoldRang3r news desk — automated edition runner.

Runs a morning (7:30 AM) or midday (12:30 PM) edition end-to-end with no
agent in the loop for the mechanical parts: fetches RSS feeds + the CISA KEV
catalog, dedupes against data/news.json, ranks with simple heuristics, writes
items/clusters into news.json, updates the RIVER / LAKE / LEADERBOARD / LOG
HTML sections, runs the scrub check, pushes via the Git Data API, curl-verifies
the live site, and logs the run.

The 1:30 PM summaries edition is NOT automated here: its plain-language
summaries must be original writing (never copied article text), which a script
cannot do honestly. Use `summaries-prep` mode instead — it builds a brief of
the day's top stories + missed candidates so the small agent pass only writes.

Usage:
    newsdesk.py morning [--date YYYY-MM-DD] [--base DIR] [--dry-run] [--no-push]
    newsdesk.py midday  [--date YYYY-MM-DD] [--base DIR] [--dry-run] [--no-push]
    newsdesk.py summaries-prep [--date YYYY-MM-DD] [--base DIR] [--drafts-dir DIR]

Exit codes: 0 ok (including a midday no-op); 2 scrub failure; 3 fetch/push/
verify failure or nothing cleared the bar for a morning edition.
"""
import argparse
import difflib
import email.utils
import html
import json
import os
import re
import subprocess
import sys
import urllib.error
import urllib.request
import xml.etree.ElementTree as ET
from collections import Counter, defaultdict
from datetime import datetime, timedelta, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

ET_ZONE = ZoneInfo("America/New_York")
DAY_ONE = datetime(2026, 10, 21).date()
UA = {"User-Agent": "Mozilla/5.0 (compatible; GoldRang3rDesk/1.0)"}
PUSH_SCRIPT = Path.home() / "workspace" / "skills" / "github" / "bin" / "gh_push_dir.py"
GOAL_HIDDEN = (Path.home() / "workspace" / "goals" /
               "goldranger-semi-automated-bounty-hunting-protection-platform" / "hidden_files")
RUNS_DIR = GOAL_HIDDEN / "newsdesk-runs"
DRAFTS_DIR = GOAL_HIDDEN / "newsdesk-drafts"
CISA_CATALOG_URL = "https://www.cisa.gov/known-exploited-vulnerabilities-catalog"
KEV_JSON = "https://www.cisa.gov/sites/default/files/feeds/known_exploited_vulnerabilities.json"

FORBIDDEN = [r"goldranger[^3]", r"goldensun", r"reina", r"github\.com"]
WARN_WORDS = [r"\bnate\b", r"\bdavid\b"]

STOPWORDS = set("""a an the and or of to in on for with by at from as is are was were be been
it its this that these those after before over under into out up down not no more most new
says say said will would can could should may might about than then when while who what how
why all any each per via amid among between during including using user users company companies
today yesterday week month year day days report reports source sources have has had do does
did get gets got make makes made take takes took put puts set sets one two three first second
also just only even still now he she his her they their them we you your our us him me my i
gets going goes come comes see sees look looks know known think""".split())

OUTLET_SLUGS = {
    "The Hacker News": "thn", "BleepingComputer": "bleepingcomputer",
    "SecurityWeek": "securityweek", "TechCrunch": "techcrunch",
    "CoinDesk": "coindesk", "Cointelegraph": "cointelegraph",
    "The Register": "theregister", "Dark Reading": "darkreading",
    "Krebs on Security": "krebs", "Help Net Security": "helpnetsecurity",
    "Tech.eu": "techeu", "The Decoder": "thedecoder",
    "TechStartups": "techstartups", "PYMNTS": "pymnts",
    "SiliconANGLE": "siliconangle", "The Block": "theblock",
    "Bitcoin.com": "bitcoincom", "Decrypt": "decrypt",
    "Cyber Security News": "cybersecuritynews", "GBHackers": "gbhackers",
    "VentureBeat": "venturebeat", "CISA": "cisa",
}

# ---------------------------------------------------------------- fetching

def fetch_url(url, timeout=15):
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return resp.read()


def parse_feed_xml(raw, outlet):
    """Parse RSS 2.0 / Atom. Returns [{title, link, desc, pub, author}]."""
    root = ET.fromstring(raw)
    items = []
    ns = {"dc": "http://purl.org/dc/elements/1.1/",
          "content": "http://purl.org/rss/1.0/modules/content/",
          "atom": "http://www.w3.org/2005/Atom"}
    if root.tag.endswith("feed"):  # Atom
        entries = root.findall("atom:entry", ns)
        for e in entries:
            link = None
            for l in e.findall("atom:link", ns):
                if l.get("rel") in (None, "alternate"):
                    link = l.get("href")
                    break
            title = (e.findtext("atom:title", "", ns) or "").strip()
            desc = (e.findtext("atom:summary", "", ns) or "").strip()
            pub = e.findtext("atom:updated", "", ns) or e.findtext("atom:published", "", ns)
            author_el = e.find("atom:author/atom:name", ns)
            author = author_el.text.strip() if author_el is not None and author_el.text else None
            items.append({"title": title, "link": link, "desc": desc,
                          "pub": parse_date(pub), "author": author, "outlet": outlet})
    else:  # RSS 2.0
        channel = root.find("channel")
        if channel is None:
            return items
        for it in channel.findall("item"):
            title = (it.findtext("title") or "").strip()
            link = (it.findtext("link") or "").strip() or None
            desc = (it.findtext("description") or "").strip()
            if not desc:
                desc = (it.findtext("content:encoded", "", ns) or "").strip()
            pub = it.findtext("pubDate")
            creator = it.findtext("dc:creator", "", ns)
            author = creator.strip() or None
            items.append({"title": title, "link": link, "desc": desc,
                          "pub": parse_date(pub), "author": author, "outlet": outlet})
    return items


def parse_date(s):
    if not s:
        return None
    try:
        dt = email.utils.parsedate_to_datetime(s.strip())
    except (TypeError, ValueError):
        return None
    if dt is None:
        return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt


def fetch_feeds(feeds_cfg, log):
    """Fetch every configured feed. Returns (items, failures)."""
    all_items, failures = [], []
    for feed in feeds_cfg:
        outlet, url = feed["outlet"], feed["url"]
        try:
            raw = fetch_url(url)
            got = parse_feed_xml(raw, outlet)
            for it in got:
                it["weight"] = feed.get("weight", 1)
                it["kind"] = feed.get("kind", "rss")
            all_items.extend(got)
            log.append(f"feed ok: {outlet} ({len(got)} items)")
        except Exception as exc:  # noqa: BLE001 - one bad feed must not kill the run
            failures.append(outlet)
            log.append(f"feed FAIL: {outlet} ({exc.__class__.__name__}: {exc})")
    return all_items, failures


def fetch_kev(window_start, window_end, log):
    """CISA Known Exploited Vulnerabilities added inside the window."""
    try:
        data = json.loads(fetch_url(KEV_JSON))
    except Exception as exc:  # noqa: BLE001
        log.append(f"KEV FAIL: {exc.__class__.__name__}: {exc}")
        return []
    out = []
    for v in data.get("vulnerabilities", []):
        added = v.get("dateAdded")
        if not added:
            continue
        try:
            day = datetime.strptime(added, "%Y-%m-%d").date()
        except ValueError:
            continue
        if not (window_start.date() <= day <= window_end.date()):
            continue
        cve = v.get("cveID", "")
        vendor = v.get("vendorProject", "")
        product = v.get("product", "")
        desc = (v.get("shortDescription") or "").strip()
        who = vendor if (not product or product == vendor
                     or product.startswith(vendor)) else f"{vendor} {product}"
        headline = (f"CISA adds {cve} ({who}) to its exploited-vulnerabilities "
                    f"catalog — {first_sentence(desc)}")
        out.append({"title": headline, "link": CISA_CATALOG_URL, "desc": desc,
                    "pub": datetime(day.year, day.month, day.day, 9, 0,
                                    tzinfo=ET_ZONE),
                    "author": None, "outlet": "CISA", "weight": 2, "kind": "kev",
                    "cve": cve})
        log.append(f"KEV item: {cve} ({vendor})")
    return out

# ---------------------------------------------------------------- cleaning

EMOJI_RE = re.compile(r"[\U0001F000-\U0001FAFF\u2600-\u27BF\uFE0F\u200d]+")


def clean_text(s):
    s = html.unescape(s or "")
    s = re.sub(r"<[^>]+>", " ", s)
    s = EMOJI_RE.sub("", s)
    s = re.sub(r"\s+", " ", s).strip()
    return s


def first_sentence(s):
    s = clean_text(s)
    if not s:
        return ""
    m = re.search(r"[.!?](\s|$)", s)
    if m and m.start() > 25:
        return s[:m.start() + 1]
    return s[:180].rsplit(" ", 1)[0] if len(s) > 180 else s


def norm_url(u):
    if not u:
        return ""
    u = u.strip().lower()
    u = re.sub(r"[?&#](utm_[^&]*|fbclid=[^&]*|gclid=[^&]*)", "", u)
    u = u.rstrip("/").split("#")[0]
    return u


def norm_headline(s):
    return re.sub(r"[^a-z0-9]+", " ", clean_text(s).lower()).strip()


def headline_similar(a, b):
    na, nb = norm_headline(a), norm_headline(b)
    if not na or not nb:
        return False
    if difflib.SequenceMatcher(None, na, nb).ratio() >= 0.82:
        return True
    ta, tb = set(na.split()), set(nb.split())
    if ta and tb and len(ta & tb) / len(ta | tb) >= 0.65:
        return True
    return False


def sig_tokens(text):
    toks = re.findall(r"cve-\d{4}-\d+|[a-z0-9]+(?:-[a-z0-9]+)?", clean_text(text).lower())
    return [t for t in toks if len(t) >= 4 and t not in STOPWORDS
            and not re.fullmatch(r"20\d\d", t)]

# ---------------------------------------------------------------- scoring

FRAUD_FIN = ["crypto", "exchange", "wallet", "payment", "bank", "fintech",
             "atm", "bridge", "brokerage", "bitcoin", "ethereum"]
FRAUD_ACT = ["scam", "fraud", "launder", "phish", "drain", "stolen", "breach",
             "hack", "exploit", "seized", "fine", "ordered"]
BUG_WORDS = ["cve-20", "vulnerability", "vulnerabilities", "flaw", "zero-day",
             "zero day", "rce", "exploit", "patch", "unpatched"]
PROTECT_WORDS = ["cisa", "fbi", "warn", "advisory", "guidance", "kill switch",
                 "shut down", "federal"]
DOWNWEIGHT = [("weekly recap", -8), ("recap:", -8), ("roundup", -6),
              ("this week in", -6), ("opinion", -6), ("webinar", -6),
              ("podcast", -6), ("sponsored", -6), ("how to", -4)]


def score_item(it, now_et):
    title = clean_text(it["title"]).lower()
    desc = clean_text(it.get("desc", "")).lower()
    text = title + " " + desc
    score = 0.0
    pub = it.get("pub")
    if pub:
        age_h = max(0.0, (now_et - pub.astimezone(ET_ZONE)).total_seconds() / 3600)
        score += max(0.0, 8.0 - age_h * 0.35)
    for w in ("breach", "ransomware", "zero-day", "zero day", "cve-20"):
        if w in title:
            score += 7
    for w in ("exploited", "kev", "backdoor", "stolen", "leak"):
        if w in title:
            score += 5
    for w in ("vulnerability", "flaw", "rce", "cisa", "fbi"):
        if w in title:
            score += 4
    if re.search(r"\$\s?[\d.]+[mb]\b", title) and re.search(
            r"rais|series|valuation|ipo|acqui|funding", title):
        score += 4
    if "ai" in title and re.search(r"launch|model|rais|unveil", title):
        score += 3
    if re.search(r"cve-20\d\d-\d+", desc):
        score += 2
    if it.get("kind") == "kev":
        score += 6
    score += it.get("weight", 1)
    for phrase, penalty in DOWNWEIGHT:
        if phrase in text:
            score += penalty
    return round(score, 1)


def lane_for(it):
    text = (clean_text(it["title"]) + " " + clean_text(it.get("desc", ""))).lower()
    if any(f in text for f in FRAUD_FIN) and any(a in text for a in FRAUD_ACT):
        return "fraud"
    if any(w in text for w in BUG_WORDS):
        return "bug"
    if any(w in text for w in PROTECT_WORDS):
        return "protect"
    return None


def make_headline(it):
    title = clean_text(it["title"])
    desc = first_sentence(it.get("desc", ""))
    if desc and len(desc) > 25 and norm_headline(desc) not in norm_headline(title):
        h = f"{title} — {desc}"
    else:
        h = title
    return h[:300]


def make_id(outlet, headline, date):
    slug = OUTLET_SLUGS.get(outlet) or re.sub(r"[^a-z0-9]+", "", outlet.lower().split()[0])
    words = sig_tokens(headline)[:3]
    base = f"{slug}-{'-'.join(words)}-{date[5:].replace('-', '')}"
    return re.sub(r"[^a-z0-9-]+", "", base) or f"{slug}-{date[5:].replace('-', '')}"

# ---------------------------------------------------------------- clustering

def cluster_items(items):
    """Group items sharing a CVE or strong headline token overlap."""
    n = len(items)
    parent = list(range(n))

    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    def union(a, b):
        ra, rb = find(a), find(b)
        if ra != rb:
            parent[ra] = rb

    cves = [set(re.findall(r"cve-20\d\d-\d+", (i["headline"] + " " + i.get("desc", "")).lower()))
            for i in items]
    toks = [set(sig_tokens(i["headline"])) for i in items]
    for a in range(n):
        for b in range(a + 1, n):
            if cves[a] & cves[b]:
                union(a, b)
                continue
            if toks[a] and toks[b]:
                j = len(toks[a] & toks[b]) / len(toks[a] | toks[b])
                if j >= 0.30:
                    union(a, b)
    groups = defaultdict(list)
    for i in range(n):
        groups[find(i)].append(i)

    clusters = []
    for idxs in groups.values():
        group_items = [items[i] for i in idxs]
        theme = theme_for(group_items)
        clusters.append({"theme": theme, "items": [g["id"] for g in group_items]})
    return clusters


def theme_for(group_items):
    """Plain descriptive theme from the group's shared significant tokens."""
    def title_part(h):
        return h.split(" \u2014 ")[0]

    def case_map(text):
        m = {}
        for w in re.findall(r"CVE-\d{4}-\d+|[A-Za-z0-9]+(?:-[A-Za-z0-9]+)?", text):
            m.setdefault(w.lower(), w)
        return m

    counts = Counter()
    for it in group_items:
        counts.update(set(sig_tokens(title_part(it["headline"]))))
    first = group_items[0]
    order = []
    for t in sig_tokens(title_part(first["headline"])):
        if t not in order:
            order.append(t)
    need = max(2, len(group_items) // 2 + 1)
    shared = [t for t in order if counts[t] >= need]
    if len(group_items) == 1 or not shared:
        shared = order[:4]
    themed = shared[:5]
    if len(themed) < 2 and len(order) > len(themed):
        themed = order[:2]
    cmap = case_map(first["headline"])
    return " ".join(cmap.get(t, t.capitalize()) for t in themed) or "Today's security stories"


# ---------------------------------------------------------------- site updates

def esc(s):
    return html.escape(s or "", quote=True)


def load_json(base):
    p = base / "data" / "news.json"
    return json.loads(p.read_text()), p


def save_json(p, data):
    p.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n")


def feed_item_html(it, time_label):
    src = f"{esc(it['author'])} / {esc(it['outlet'])}:" if it.get("author") else f"{esc(it['outlet'])}:"
    if it.get("url"):
        body = f'<a href="{esc(it["url"])}">{esc(it["headline"])}</a>'
    else:
        body = esc(it["headline"])
    tag = (f'<span class="feed__tag" data-lane="{it["lane"]}">{it["lane"]}</span>'
           if it.get("lane") else "")
    return (f'      <div class="feed__item">\n'
            f'        <span class="feed__time">{time_label}</span>\n'
            f'        <p class="feed__body"><span class="feed__source">{src}</span> {body}{tag}</p>\n'
            f'      </div>\n')


def cluster_html(theme, topic_label, items, by_id):
    lis = []
    for it in items:
        if it.get("url"):
            lis.append(f'          <li><b>{esc(it["outlet"])}:</b> '
                       f'<a href="{esc(it["url"])}">{esc(it["headline"])}</a></li>\n')
        else:
            lis.append(f'          <li><b>{esc(it["outlet"])}:</b> {esc(it["headline"])}</li>\n')
    return ('        <article class="cluster">\n'
            f'          <p class="cluster__meta">Cluster \u00b7 {esc(topic_label)}</p>\n'
            f'          <h2 class="cluster__title">{esc(theme)}</h2>\n'
            '          <ul class="cluster__items">\n' + "".join(lis) +
            '          </ul>\n        </article>\n\n')


def split_days(body):
    parts = re.split(r'(?=<p class="feed__date">)', body)
    return parts[0], parts[1:]


def update_index(base, items, date_long, edition, time_label):
    p = base / "index.html"
    s = p.read_text()
    hero_label = ("Morning river below" if edition == "morning"
                  else "Midday update at 12:30 PM \u2014 river below")
    s2, n = re.subn(r'(<p class="hero__signal"><span class="dot">\u25cf</span> Edition \u2014 )[^<]+(</p>)',
                    r'\g<1>' + f"{date_long} \u00b7 {hero_label}" + r'\g<2>', s, count=1)
    assert n == 1, "hero line not found in index.html"
    s = s2
    start = s.index("<!-- RIVER:START -->") + len("<!-- RIVER:START -->")
    end = s.index("<!-- RIVER:END -->")
    head, days = split_days(s[start:end])
    date_marker = f'<p class="feed__date">{date_long}</p>'
    if edition == "morning":
        assert not any(date_marker in d for d in days), f"{date_long} already in river"
        new_day = f'        {date_marker}\n        <div class="feed">\n'
        new_day += "".join(feed_item_html(it, time_label) for it in items)
        new_day += "        </div>\n\n\n"
        kept = [new_day] + days[:2]  # today + previous 2 days = max 3
        s = s[:start] + head + "".join(kept) + s[end:]
    else:
        assert any(date_marker in d for d in days), "no morning section for today in river"
        blocks = "".join(feed_item_html(it, time_label) for it in items)
        new_days = []
        for d in days:
            if date_marker in d:
                anchor = '<div class="feed">\n'
                assert anchor in d, "feed div missing in today's section"
                d = d.replace(anchor, anchor + blocks, 1)
            new_days.append(d)
        s = s[:start] + head + "".join(new_days) + s[end:]
    return s


def update_lake(base, clusters, items, date_long, topic_label, edition):
    p = base / "lake.html"
    s = p.read_text()
    by_id = {it["id"]: it for it in items}
    start = s.index("<!-- LAKE:START -->") + len("<!-- LAKE:START -->")
    end = s.index("<!-- LAKE:END -->")
    head, days = split_days(s[start:end])
    date_marker = f'<p class="feed__date">{date_long}</p>'
    new_block = f'        {date_marker}\n\n'
    for c in clusters:
        new_block += cluster_html(c["theme"], topic_label,
                                  [by_id[i] for i in c["items"]], by_id)
    if edition == "morning":
        kept = [new_block] + days[:1]  # today + previous day = max 2
        s = s[:start] + head + "".join(kept) + s[end:]
    else:
        assert any(date_marker in d for d in days), "no morning clusters for today in lake"
        new_days = []
        for d in days:
            if date_marker in d:
                d = d.replace(date_marker, date_marker + "\n" +
                              "".join(cluster_html(c["theme"], topic_label,
                                                   [by_id[i] for i in c["items"]], by_id)
                                      for c in clusters), 1)
            new_days.append(d)
        s = s[:start] + head + "".join(new_days) + s[end:]
    return s


def week_bounds(date):
    monday = date - timedelta(days=date.weekday())
    return monday, monday + timedelta(days=6)


def update_leaderboards(base, data, date, edition, time_label, new_items, date_long):
    p = base / "leaderboards.html"
    s = p.read_text()
    mon, sun = week_bounds(date)
    week = [it for it in data["items"] if mon.isoformat() <= it["date"] <= sun.isoformat()]

    def reporter(it):
        return it["author"] if it.get("author") else f"{it['outlet']} staff"
    counts = Counter((reporter(it), it["outlet"]) for it in week)
    latest = {}
    for it in week:
        latest[(reporter(it), it["outlet"])] = it
    ranked = sorted(counts.items(), key=lambda kv: (-kv[1], kv[0][0]))

    def trunc(h, n=50):
        return h[:n].rstrip() + "\u2026" if len(h) > n else h
    rows = ""
    for (rep, outlet), n in ranked:
        rank = 1 + sum(1 for c in counts.values() if c > n)
        li = latest[(rep, outlet)]
        rows += (f'              <tr><td><b>{rank}</b></td><td><b>{esc(rep)}</b></td>'
                 f'<td>{esc(outlet)}</td><td>{n}</td>'
                 f'<td>{esc(trunc(li["headline"]))} \u2014 {li["date"][5:]}</td></tr>\n')
    start = s.index("<!-- LEADERBOARD:START -->")
    end = s.index("<!-- LEADERBOARD:END -->")
    new_table = ("<!-- LEADERBOARD:START -->\n"
                 '        <div class="table-wrap">\n          <table class="table">\n'
                 '            <thead><tr><th>Rank</th><th>Reporter</th><th>Outlet</th>'
                 '<th>Stories tracked</th><th>Latest</th></tr></thead>\n'
                 '            <tbody>\n' + rows + '            </tbody>\n'
                 '          </table>\n        </div>\n')
    s = s[:start] + new_table + s[end:]

    mon_s = mon.strftime("%b %-d")
    sun_s = sun.strftime("%-d") if sun.month == mon.month else sun.strftime("%b %-d")
    top = ranked[0] if ranked else (("—", "—"), 0)
    second = [r for r in ranked[1:] if r[1] == ranked[1][1]][:2] if len(ranked) > 1 else []
    second_txt = ""
    if second:
        names = ", ".join(f"{esc(r[0][0])} ({esc(r[0][1])})" for r in second)
        second_txt = f" {names} follow at {second[0][1]} each."
    tops = "; ".join(trunc(it["headline"], 80) for it in new_items[:3])
    note = (f"<p><b>Week of {mon_s}\u2013{sun_s}, {date.year} \u2014 after the {time_label} "
            f"edition on {mon.strftime('%b %-d')}:</b> {esc(top[0][0])} ({esc(top[0][1])}) "
            f"leads at {top[1]} stories;{second_txt} Today's river adds {len(new_items)} "
            f"{'morning' if edition == 'morning' else 'midday'} stories: {esc(tops)}.</p>")
    s2, n = re.subn(r'<div class="note">\s*<p>.*?</p>\s*</div>',
                    f'<div class="note">\n          {note}\n        </div>', s, count=1, flags=re.S)
    assert n == 1, "leaderboard note div not found"
    return s2, {"week_total": len(week), "leader": top}


def update_log_morning(base, items, date, day_n, date_long):
    p = base / "log.html"
    s = p.read_text()
    weekday = date.strftime("%A")
    shorts = "; ".join(it["headline"][:110].rstrip() + ("…" if len(it["headline"]) > 110 else "")
                       for it in items[:3])
    body = (f"{len(items)} stories on the river: {shorts}.")
    card = ('        <div class="day">\n'
            '          <div class="day__head">\n'
            f'            <span class="day__date">{date.isoformat()}</span>\n'
            f'            <span class="day__dow">{weekday} \u00b7 Day {day_n}</span>\n'
            '          </div>\n'
            '          <div class="grid">\n'
            '            <article class="card" data-lane="protect">\n'
            f'              <p class="card__meta">Log \u00b7 Day {day_n} \u00b7 Publication</p>\n'
            '              <h3>7:30 AM \u2014 the morning edition is live</h3>\n'
            f'              <p>{esc(body)}</p>\n'
            '              <p class="card__foot"><a class="text-link" href="index.html">Read the river \u2192</a></p>\n'
            '            </article>\n\n'
            '          </div>\n'
            '        </div>\n\n')
    anchor = '        <div class="day">'
    pos = s.index(anchor)
    return s[:pos] + card + s[pos:]

def scrub_texts(named_texts):
    """Forbidden-pattern check on in-memory new file contents (pre-write)."""
    errors, warnings = [], []
    for name, text in named_texts:
        for pat in FORBIDDEN:
            m = re.search(pat, text, re.I)
            if m:
                i = max(0, m.start() - 60)
                errors.append(f"forbidden /{pat}/ in {name}: ...{text[i:m.start() + 60]!r}...")
        for pat in WARN_WORDS:
            m = re.search(pat, text, re.I)
            if m:
                warnings.append(f"check /{pat}/ in {name} (may be a legit reporter byline)")
    return errors, warnings


# ---------------------------------------------------------------- scrub / push / verify

def scrub(base, files, log):
    """FAIL on forbidden identity/repo-link text; WARN on team-name lookalikes."""
    errors, warnings = [], []
    for pat in FORBIDDEN:
        r = subprocess.run(["grep", "-riE", pat] + [str(f) for f in files],
                           capture_output=True, text=True, cwd=base)
        if r.stdout.strip():
            errors.append(f"forbidden /{pat}/: {r.stdout.strip()[:300]}")
    for pat in WARN_WORDS:
        r = subprocess.run(["grep", "-riE", pat] + [str(f) for f in files],
                           capture_output=True, text=True, cwd=base)
        if r.stdout.strip():
            warnings.append(f"check /{pat}/ (may be a legit reporter byline): "
                            f"{r.stdout.strip()[:200]}")
    for w in warnings:
        log.append("scrub WARN: " + w)
    return errors, warnings


def push(base, message, log):
    cmd = [sys.executable, str(PUSH_SCRIPT), "Sukonik", "goldrang3r", str(base),
           "-m", message]
    r = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
    log.append("push stdout: " + r.stdout.strip()[-500:])
    if r.returncode != 0:
        log.append("push stderr: " + r.stderr.strip()[-500:])
        raise RuntimeError(f"push failed (exit {r.returncode})")
    m = re.search(r"\b[0-9a-f]{40}\b", r.stdout)
    return m.group(0)[:7] if m else "unknown"


def verify_live(needles, log, tries=10, delay=15):
    """Wait for Pages to serve the new content. Returns (ok, lag_note)."""
    import time
    for attempt in range(1, tries + 1):
        try:
            home = html.unescape(fetch_url("https://sukonik.github.io/goldrang3r/").decode("utf-8", "replace"))
            lake = html.unescape(fetch_url("https://sukonik.github.io/goldrang3r/lake.html").decode("utf-8", "replace"))
        except Exception as exc:  # noqa: BLE001
            log.append(f"verify attempt {attempt}: fetch error {exc}")
            time.sleep(delay)
            continue
        missing = [n for n in needles if n not in home and n not in lake]
        if not missing:
            note = "live on first check" if attempt == 1 else f"live after ~{(attempt - 1) * delay}s Pages lag"
            log.append("verify: " + note)
            return True, note
        log.append(f"verify attempt {attempt}: still serving old build (missing {missing[:1]})")
        time.sleep(delay)
    return False, "Pages still serving old build after retries"

# ---------------------------------------------------------------- editions

def pick_items(cands, existing, target_min, target_max, per_outlet, log):
    """Dedupe + rank + diversity-cap. Returns picked items (dicts, scored)."""
    existing_urls = {norm_url(it.get("url")) for it in existing if it.get("url")}
    existing_heads = [it["headline"] for it in existing]
    seen_urls, seen_heads, picked = set(), [], []
    outlet_counts = Counter()
    for c in sorted(cands, key=lambda x: -x["score"]):
        url_n = norm_url(c.get("link"))
        if url_n and (url_n in existing_urls or url_n in seen_urls):
            continue
        if any(headline_similar(c["headline"], h) for h in existing_heads + seen_heads):
            continue
        if outlet_counts[c["outlet"]] >= per_outlet:
            continue
        seen_urls.add(url_n)
        seen_heads.append(c["headline"])
        outlet_counts[c["outlet"]] += 1
        picked.append(c)
        if len(picked) >= target_max:
            break
    log.append(f"picked {len(picked)} (target {target_min}–{target_max}); "
               f"outlets: {dict(outlet_counts)}")
    return picked


def build_items(picked, date_str, time_label, existing_ids):
    items = []
    for c in picked:
        headline = make_headline(c)
        base_id = make_id(c["outlet"], headline, date_str)
        item_id, suffix = base_id, 2
        while item_id in existing_ids:
            item_id = f"{base_id}-{suffix}"
            suffix += 1
        existing_ids.add(item_id)
        items.append({"author": c.get("author"), "date": date_str,
                      "headline": headline, "id": item_id,
                      "lane": lane_for(c), "outlet": c["outlet"],
                      "time": time_label, "url": c.get("link")})
    return items


def run_edition(edition, date, base, feeds_path, dry_run, no_push):
    log = []
    date_str = date.isoformat()
    date_long = date.strftime("%A, %B %-d, %Y")
    now_et = datetime.now(ET_ZONE)
    if edition == "morning":
        time_label, topic_label = "7:30 AM", "Morning edition"
        win_start = datetime.combine(date - timedelta(days=1), datetime.min.time(),
                                     tzinfo=ET_ZONE).replace(hour=7, minute=30)
        win_end = now_et
        target_min, target_max, per_outlet = 8, 12, 3
    else:
        time_label, topic_label = "12:30 PM", "Midday edition"
        win_start = datetime.combine(date, datetime.min.time(),
                                     tzinfo=ET_ZONE).replace(hour=7, minute=30)
        win_end = now_et
        target_min, target_max, per_outlet = 4, 8, 2
    log.append(f"{edition} edition {date_str} window {win_start} → {win_end} ET")

    feeds_cfg = json.loads(Path(feeds_path).read_text())["feeds"]
    raw, failures = fetch_feeds(feeds_cfg, log)
    raw += fetch_kev(win_start, win_end, log)
    log.append(f"fetched {len(raw)} feed items ({len(failures)} feeds failed)")

    data, nj_path = load_json(base)
    existing = data["items"]
    cands = []
    for it in raw:
        if not it.get("title") or not it.get("link"):
            continue
        pub = it.get("pub")
        if pub and not (win_start <= pub.astimezone(ET_ZONE) <= win_end + timedelta(minutes=30)):
            continue
        it["score"] = score_item(it, now_et)
        it["headline"] = make_headline(it)
        if it["score"] < 5:
            continue
        cands.append(it)
    log.append(f"{len(cands)} candidates scored ≥ 5 in window")
    if not cands:
        raise RuntimeError("no candidates cleared the bar")

    picked = pick_items(cands, existing, target_min, target_max, per_outlet, log)
    if edition == "morning" and len(picked) < 4:
        raise RuntimeError(f"only {len(picked)} items cleared the bar for a morning edition")
    if edition == "midday" and not picked:
        print("no midday update — nothing new cleared the bar")
        return {"edition": edition, "date": date_str, "items": 0, "noop": True, "log": log}
    if len(picked) < target_min:
        log.append(f"WARNING: only {len(picked)} items (target min {target_min}) — publishing anyway")

    items = build_items(picked, date_str, time_label, {it["id"] for it in existing})
    clusters = cluster_items(items)
    for c in clusters:
        c["date"] = date_str
        c["topic"] = topic_label
    data["items"].extend(items)
    data["clusters"].extend(clusters)
    data["edition"] = date_str
    day_n = (date - DAY_ONE).days + 1
    # Compute ALL new contents in memory first; nothing is written until
    # every update + the scrub have succeeded (a crash mid-run must not
    # leave news.json updated while the HTML is stale, or vice versa).
    new_nj = json.dumps(data, indent=2, ensure_ascii=False) + "\n"
    new_index = update_index(base, items, date_long, edition, time_label)
    new_lake = update_lake(base, clusters, items, date_long, topic_label, edition)
    new_lb, lb = update_leaderboards(base, data, date, edition, time_label, items, date_long)
    new_log = update_log_morning(base, items, date, day_n, date_long) if edition == "morning" else None
    texts = [("news.json", new_nj), ("index.html", new_index),
             ("lake.html", new_lake), ("leaderboards.html", new_lb)]
    if new_log is not None:
        texts.append(("log.html", new_log))
    errors, warns = scrub_texts(texts)
    for w in warns:
        log.append("scrub WARN: " + w)
    if errors:
        raise RuntimeError("scrub FAILED (nothing written): " + " | ".join(errors))
    # All checks passed — write everything.
    nj_path.write_text(new_nj)
    (base / "index.html").write_text(new_index)
    (base / "lake.html").write_text(new_lake)
    (base / "leaderboards.html").write_text(new_lb)
    if new_log is not None:
        (base / "log.html").write_text(new_log)

    edited = [base / "index.html", base / "lake.html", base / "leaderboards.html",
              base / "data" / "news.json"] + ([base / "log.html"] if edition == "morning" else [])
    errors, _warns = scrub(base, edited, log)  # post-write belt-and-braces check
    if errors:
        raise RuntimeError("scrub FAILED after write: " + " | ".join(errors))

    sha, verify_note = None, "skipped (dry-run / no-push)"
    if not dry_run and not no_push:
        sha = push(base, f"News {time_label} {'edition' if edition == 'morning' else 'midday update'} — {date_str}", log)
        ok, verify_note = verify_live([items[0]["headline"][:40]], log)
        if not ok:
            raise RuntimeError("live verify failed: " + verify_note)
    elif dry_run:
        log.append("dry-run: files written to base dir, push + verify skipped")

    if not dry_run:
        mem = Path.home() / "memory" / f"{date_str}.md"
        mem.parent.mkdir(exist_ok=True)
        with open(mem, "a") as f:
            f.write(f"\n[script] {now_et.strftime('%I:%M %p')} — goldrang3r-news-"
                    f"{'0730' if edition == 'morning' else '1230'} {date_str} SCRIPTED: "
                    f"{len(items)} items, {len(clusters)} clusters; commit {sha}; {verify_note}.\n")

    report = {"edition": edition, "date": date_str, "day": day_n,
              "items": len(items), "clusters": len(clusters),
              "top": [(it["outlet"], it["headline"][:100]) for it in items[:3]],
              "week_total": lb["week_total"], "leader": lb["leader"],
              "commit": sha, "verify": verify_note, "feed_failures": failures,
              "log": log}
    RUNS_DIR.mkdir(parents=True, exist_ok=True)
    (RUNS_DIR / f"run-{date_str}-{edition}.json").write_text(
        json.dumps(report, indent=2, ensure_ascii=False) + "\n")
    return report

# ---------------------------------------------------------------- summaries prep

def summaries_prep(date, base, feeds_path, drafts_dir):
    """Build the 1:30 PM brief: top stories + missed candidates. No repo writes."""
    date_str = date.isoformat()
    now_et = datetime.now(ET_ZONE)
    data, _ = load_json(base)
    today = [it for it in data["items"] if it["date"] == date_str]
    feeds_cfg = json.loads(Path(feeds_path).read_text())["feeds"]
    log = []
    raw, failures = fetch_feeds(feeds_cfg, log)
    raw += fetch_kev(datetime.combine(date, datetime.min.time(), tzinfo=ET_ZONE),
                     now_et, log)
    existing_urls = {norm_url(it.get("url")) for it in data["items"] if it.get("url")}
    existing_heads = [it["headline"] for it in data["items"]]
    missed = []
    for it in raw:
        if not it.get("title") or not it.get("link"):
            continue
        pub = it.get("pub")
        if pub and pub.astimezone(ET_ZONE).date() != date:
            continue
        if norm_url(it.get("link")) in existing_urls:
            continue
        if any(headline_similar(it["title"], h) for h in existing_heads):
            continue
        it["score"] = score_item(it, now_et)
        if it["score"] >= 8:
            missed.append(it)
    missed.sort(key=lambda x: -x["score"])

    def rank(items):
        scored = []
        for it in items:
            probe = {"title": it["headline"], "desc": "", "pub": None,
                     "weight": 1, "kind": "rss"}
            scored.append((score_item(probe, now_et), it))
        return [it for _, it in sorted(scored, key=lambda x: -x[0])]

    tech = [it for it in rank(today) if it.get("lane") in ("bug", "protect")]
    fin = [it for it in rank(today) if it.get("lane") == "fraud"]
    rest = [it for it in rank(today) if it not in tech and it not in fin]
    picks = {"tech": tech[:3], "fintech": fin[:3], "other": rest[:2]}

    lines = [f"# 1:30 PM summaries brief — {date.strftime('%A, %B %-d, %Y')}",
             "",
             "Drafts only — the agent pass rewrites these in its own words. "
             "Do NOT copy feed/article text into the Lake.",
             ""]
    for section, items in (("Tech Security", picks["tech"]),
                           ("Fintech Security", picks["fintech"]),
                           ("Also on the river", picks["other"])):
        lines.append(f"## {section}")
        for it in items:
            lines.append(f"- **{it['outlet']}**: {it['headline']}")
            if it.get("url"):
                lines.append(f"  {it['url']}")
        lines.append("")
    lines.append("## Missed candidates (in feeds today, not yet in the store)")
    for it in missed[:6]:
        lines.append(f"- **{it['outlet']}** (score {it['score']}): {clean_text(it['title'])}")
        if it.get("link"):
            lines.append(f"  {it['link']}")
        d = first_sentence(it.get("desc", ""))
        if d:
            lines.append(f"  Key facts (feed text — rewrite): {d}")
    lines.append("")
    lines.append(f"Feeds failed this run: {', '.join(failures) or 'none'}")
    text = "\n".join(lines) + "\n"
    drafts = Path(drafts_dir)
    drafts.mkdir(parents=True, exist_ok=True)
    out = drafts / f"summaries-brief-{date_str}.md"
    out.write_text(text)
    print(text)
    print(f"brief written to {out}")
    return {"date": date_str, "missed": len(missed), "brief": str(out)}

# ---------------------------------------------------------------- CLI

def main():
    ap = argparse.ArgumentParser(description="GoldRang3r news desk — automated editions")
    ap.add_argument("edition", choices=["morning", "midday", "summaries-prep"])
    ap.add_argument("--date", default=None, help="YYYY-MM-DD (default: today, ET)")
    ap.add_argument("--base", default=str(Path.home() / "workspace" / "goldrang3r"))
    ap.add_argument("--feeds", default=None, help="feeds.json (default: tools/feeds.json)")
    ap.add_argument("--dry-run", action="store_true", help="write files, skip push/verify/memory log")
    ap.add_argument("--no-push", action="store_true", help="write files, skip push/verify")
    ap.add_argument("--drafts-dir", default=str(DRAFTS_DIR))
    args = ap.parse_args()

    date = (datetime.strptime(args.date, "%Y-%m-%d").date() if args.date
            else datetime.now(ET_ZONE).date())
    base = Path(args.base)
    feeds_path = args.feeds or str(Path(__file__).resolve().parent / "feeds.json")
    try:
        if args.edition == "summaries-prep":
            rep = summaries_prep(date, base, feeds_path, args.drafts_dir)
            print(json.dumps({k: v for k, v in rep.items() if k != "log"}, indent=2))
            return 0
        rep = run_edition(args.edition, date, base, feeds_path, args.dry_run, args.no_push)
        print(json.dumps({k: v for k, v in rep.items() if k != "log"}, indent=2, ensure_ascii=False))
        for line in rep.get("log", []):
            print("  ·", line)
        return 0
    except Exception as exc:  # noqa: BLE001 - report, don't fabricate an edition
        print(f"ERROR: {exc}", file=sys.stderr)
        return 3


if __name__ == "__main__":
    raise SystemExit(main())
