# GoldRang3r news desk — automated editions

`newsdesk.py` runs the 7:30 AM morning and 12:30 PM midday editions end to end
with no agent in the loop. The 1:30 PM summaries stay a small agent pass —
see "What still needs an agent" below.

## Run it

```sh
# Morning (7:30 AM ET) — 8–12 items from the last ~24h
python3 ~/workspace/goldrang3r/tools/newsdesk.py morning

# Midday (12:30 PM ET) — 4–8 items new since 7:30 AM; exits quietly
# with "no midday update" if nothing cleared the bar
python3 ~/workspace/goldrang3r/tools/newsdesk.py midday

# Dry run against a COPY of the staging dir (writes files, never pushes)
cp -r ~/workspace/goldrang3r /tmp/g3test
python3 ~/workspace/goldrang3r/tools/newsdesk.py midday --date 2026-11-09 \
    --base /tmp/g3test --dry-run

# 1:30 PM brief for the agent pass (writes a markdown brief, touches no repo files)
python3 ~/workspace/goldrang3r/tools/newsdesk.py summaries-prep
```

Options: `--date YYYY-MM-DD` (default today, ET), `--base DIR` (default
`~/workspace/goldrang3r`), `--feeds FILE` (default `tools/feeds.json`),
`--no-push` (write files, skip push/verify). Exit codes: 0 ok (including a
midday no-op); 2 scrub failure; 3 fetch/push/verify failure or a morning
edition with nothing to publish.

## How it works

1. **Fetch** — direct RSS/Atom feeds from `feeds.json` (21 outlets) plus the
   CISA Known Exploited Vulnerabilities JSON feed. Stdlib only (`urllib` +
   `xml.etree`); no `feedparser`, no `requests`. A failed feed is logged and
   skipped, never fatal.
2. **Window** — morning: last ~24h (since yesterday 7:30 AM ET). Midday:
   today since 7:30 AM ET.
3. **Dedupe** — against every item in `data/news.json` by normalized URL
   (tracking params stripped) and headline similarity (SequenceMatcher ≥ 0.82
   or token Jaccard ≥ 0.65), plus within the batch.
4. **Rank** — recency + keyword weights (breach / CVE / zero-day / KEV /
   ransomware / funding $ / IPO / AI launch), downweights for recaps,
   roundups, opinion, webinars, podcasts. Threshold score ≥ 5. Max 3 items
   per outlet (morning) / 2 (midday).
5. **Headlines** — RSS title + first sentence of the feed description
   ("Title — summary clause"), never invented. Items link only to the URL
   the feed returned (KEV items link to the verified CISA catalog page).
   Lanes (fraud/bug/protect) from keyword rules.
6. **Clusters** — items sharing a CVE or ≥ 0.30 headline-token overlap are
   grouped; themes are plain descriptions built from shared tokens
   (e.g. "SonicWall SSL VPN flaw"), not the old hand-written voice titles.
7. **Publish** — all new file contents are computed in memory first, scrubbed
   in memory, and only then written (a crash mid-run cannot leave
   `news.json` updated while the HTML is stale). Updates `news.json`,
   `index.html` (river, max 3 days), `lake.html` (max 2 days),
   `leaderboards.html` (week Mon–Sun recount + templated note), and `log.html`
   (morning day card only). Then the forbidden-word scrub, push via the Git
   Data API (`gh_push_dir.py`), and curl-verify with Pages-lag retries.
8. **Log** — a `[script]` line is appended to `~/memory/YYYY-MM-DD.md` and a
   JSON run report is written under the goal's `hidden_files/newsdesk-runs/`.

## What still needs an agent

- **1:30 PM summaries.** The summaries must be original plain-language
  writing — a script cannot honestly write them, and extractive summaries
  would copy article sentences, which the desk rules forbid. Keep this
  edition as a small agent pass, but let `summaries-prep` do the research:
  it writes a brief (`summaries-brief-YYYY-MM-DD.md`) to `~/workspace/newsdesk-state/drafts/`
  with the day's top tech-security / fintech-security stories, links, and
  any high-scoring feed stories the earlier editions missed. The agent pass
  then only writes and publishes — no `browser.search` research.
- **Judgment calls.** The script cannot tell a genuinely new story from a
  re-report, judge whether an unverified breach claim deserves the "unverified"
  flag beyond the feed's own wording, or spot a bad feed item (e.g. a
  sponsored post slipping through). The midday no-op path covers the
  nothing-new case; anything else the script publishes should get a glance
  in the delivery message.
- **Outlets without feeds.** Reuters, Dealroom, Crosswalk, and the long tail
  of one-off outlets (MAG212 Cyber, CVETodo, Abijita, Seoul Economic Daily,
  …) have no working public RSS, so their stories only enter via the agent
  passes. Google News RSS was tested and dropped: its links stay on
  news.google.com and cannot be resolved to publisher URLs without a
  browser, which would break the verified-URL-only rule.

## Known trade-offs vs the agent-written editions

- Cluster themes and log-card bodies are plain and templated, not the
  hand-written GoldRang3r voice ("The patch that didn't patch").
- Leaderboard notes are templated from the top stories instead of
  hand-written.
- Headline summaries are the feed's own first sentence; occasionally a
  teaser rather than a crisp summary.
- Coverage narrows to the 21 feeds + KEV. The desk's long tail shrinks;
  the 1:30 agent pass is the backstop for stragglers.

## Feed health (verified 2026-11-09)

Working: The Hacker News, BleepingComputer, SecurityWeek, TechCrunch,
CoinDesk, Cointelegraph, Decrypt, The Block, Bitcoin.com, The Register,
Dark Reading, Krebs, Help Net Security, Tech.eu, The Decoder, TechStartups,
PYMNTS, SiliconANGLE, CISA KEV JSON. Flaky (logged, tolerated): Cyber
Security News (connection resets / malformed XML), GBHackers (Cloudflare
520), VentureBeat (429 rate limit). Dead: Reuters RSS (401), Dealroom
(403), Crosswalk (404).

## Proposed cron bodies (needs Nathan's approval — do not apply yet)

Thin wrappers: each cron runs the script and reports its stdout. The
reporting turn stays small — no research, no file editing by the agent.

### goldrang3r-news-0730 (7:30 AM)

> Run the GoldRang3r morning edition with the desk script — no research,
> no hand-editing. Command (from the repo staging dir):
> `python3 ~/workspace/goldrang3r/tools/newsdesk.py morning`
> Then report compactly in this chat from the script's printed JSON:
> edition date, item count, the top 3 headlines with outlets, commit SHA,
> live-check result. If the script exits non-zero, report exactly what
> failed — do not fabricate an edition, and do not hand-publish one to
> cover the failure. Hard rules still apply: only the public GoldRang3r
> identity; never write the forbidden name, team names, or repo links
> into site files (the script scrubs before pushing).

### goldrang3r-news-1230 (12:30 PM)

> Run the GoldRang3r midday update with the desk script — no research,
> no hand-editing. Command:
> `python3 ~/workspace/goldrang3r/tools/newsdesk.py midday`
> Then report compactly in this chat from the script's printed JSON:
> new item count, top 3 new headlines with outlets, commit SHA,
> live-check result. If the script prints "no midday update — nothing new
> cleared the bar", report exactly that and publish nothing. If the script
> exits non-zero, report exactly what failed — do not fabricate items.

### goldrang3r-news-1330 (1:30 PM) — agent pass, script-assisted

> First run the brief builder (no repo writes):
> `python3 ~/workspace/goldrang3r/tools/newsdesk.py summaries-prep`
> Read the brief it prints (also saved under `~/workspace/newsdesk-state/drafts/`). Then write 3–6 ORIGINAL plain-language
> summaries (2–4 sentences each, your own words — never copy article text)
> from the brief's stories, covering the day's most important TECH SECURITY
> and FINTECH SECURITY stories, and publish them exactly as the current
> 1:30 job does (Lake clusters with topics "Summary — Tech Security" /
> "Summary — Fintech Security", Log card, leaderboards if new items were
> added, push, curl-verify). If the brief's missed candidates include a
> major story the earlier editions missed, add it to `data/news.json`
> first. If there is genuinely nothing worth summarizing, report that
> instead of inventing content.

## Token savings (estimate, not measured)

Current agent-worker approach, per day: roughly 30–60k tokens per edition
(research via `browser.search`, multiple file reads/writes, verification,
plus the delivery/verification turn) — ~100–150k tokens/day across the
three editions.

Scripted approach: the 7:30 and 12:30 crons become thin wrappers (~2–5k
tokens each: run one command, read its JSON output, report it). The 1:30
agent pass keeps only the writing/publishing, with research replaced by
the prebuilt brief — roughly 10–15k tokens instead of 30–60k.

Estimated total: ~15–25k tokens/day, i.e. roughly an **80–85% reduction**
(~100k tokens/day saved). The morning/midday editions drop to near zero;
the remaining spend is the 1:30 writing pass plus the small wrapper turns.
If the 1:30 edition is ever fully automated later, the residual would be
just the wrapper turns (~5–10k/day).

## Gotchas

- Never run `python3 -m py_compile` (or any import) inside `tools/`:
  Python writes `tools/__pycache__/`, and the push script uploads
  everything under the staging dir, so the bytecode would land in the
  public repo. (Cleaned once via Git Data API tree surgery, 2026-11-09.)
  Running the script directly (`python3 tools/newsdesk.py ...`) does not
  create `__pycache__` for the `__main__` module.
- The script needs the same credential the push script uses
  (`custom.github` via the authd surrogate); it inherits it by calling
  `~/workspace/skills/github/bin/gh_push_dir.py`.
- Feed failures are tolerated, but if ALL feeds fail the run exits 3
  with no edition published — that is the correct failure mode.
