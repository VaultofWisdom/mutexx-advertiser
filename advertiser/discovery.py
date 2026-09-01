"""
Discovery: finds suitable communities and scores them.

Reddit goes through the official API (read-only, see reddit_api.py). Forums are
checked for reachability and yield further candidates through link harvesting.
"""

from __future__ import annotations

import html
import math
import re
import time
import urllib.parse
from typing import Callable

from . import core, reddit_api, rules, seeds

Progress = Callable[[str, int, int], None]


def _noop(_message: str, _done: int, _total: int) -> None:
    return None


# ---------------------------------------------------------------------------
# Reddit
# ---------------------------------------------------------------------------

REDDIT = "https://www.reddit.com"


def _search_subreddits(keyword: str, config: dict) -> list[str]:
    payload = reddit_api.get(config, "/subreddits/search",
                             {"q": keyword, "limit": 50, "include_over_18": "on"})
    if not payload:
        return []
    names = []
    for child in payload.get("data", {}).get("children", []):
        name = child.get("data", {}).get("display_name")
        if name:
            names.append(name)
    return names


def _about(name: str, config: dict) -> dict | None:
    payload = reddit_api.get(config, f"/r/{urllib.parse.quote(name)}/about")
    if not payload:
        return None
    data = payload.get("data") or {}
    if not data.get("display_name"):
        return None
    # Private or locked subs still return data but are no use.
    if data.get("subreddit_type") in ("private", "employees_only"):
        return None
    return data


def _rules(name: str, config: dict) -> list[dict]:
    payload = reddit_api.get(config, f"/r/{urllib.parse.quote(name)}/about/rules")
    if not payload:
        return []
    return payload.get("rules") or []


def _activity(name: str, config: dict) -> dict:
    """Posts per day across the last 100 submissions - a measure of real life."""
    payload = reddit_api.get(config, f"/r/{urllib.parse.quote(name)}/new", {"limit": 100})
    if not payload:
        return {"posts_per_day": 0.0, "sample": 0}
    children = payload.get("data", {}).get("children", [])
    stamps = [c.get("data", {}).get("created_utc") for c in children if c.get("data", {}).get("created_utc")]
    if len(stamps) < 2:
        return {"posts_per_day": 0.0, "sample": len(stamps)}
    span_days = max((max(stamps) - min(stamps)) / 86400.0, 0.05)
    return {"posts_per_day": round(len(stamps) / span_days, 1), "sample": len(stamps)}


_SUB_MENTION = re.compile(r"(?:^|[\s(\[/])r/([A-Za-z0-9_]{3,21})\b")


def _mentioned_subs(text: str) -> set[str]:
    return {m.group(1) for m in _SUB_MENTION.finditer(text or "")}


def fit_score(data: dict, keywords: list[str]) -> float:
    haystack = " ".join(str(data.get(field) or "") for field in
                        ("display_name", "title", "public_description", "description")).lower()
    if not haystack.strip():
        return 0.0
    hits = 0.0
    for keyword in keywords:
        occurrences = haystack.count(keyword.lower())
        if occurrences:
            # Repeated mentions count, but with diminishing returns.
            hits += min(occurrences, 4) * (1.6 if " " in keyword else 1.0)
    return hits


def _entry_from(data: dict, keywords: list[str]) -> dict:
    return {
        "platform": "reddit",
        "id": f"reddit:{data['display_name']}",
        "name": f"r/{data['display_name']}",
        "handle": data["display_name"],
        "url": f"{REDDIT}/r/{data['display_name']}/",
        "title": data.get("title") or "",
        "description": (data.get("public_description") or "")[:600],
        "sidebar": (data.get("description") or "")[:6000],
        "submit_text": (data.get("submit_text") or "")[:3000],
        "subscribers": int(data.get("subscribers") or 0),
        "over18": bool(data.get("over18")),
        "fit_raw": fit_score(data, keywords),
        "low_value": data["display_name"] in seeds.LOW_VALUE_SUBS,
    }


def scan_reddit(config: dict, keywords: list[str], seed_list: list[str] | None = None,
                progress: Progress = _noop) -> list[dict]:
    settings = config["discovery"]

    # Nothing works on Reddit without a registered app - say so, do not return empty.
    reddit_api.get_token(config)

    candidates: dict[str, None] = {name: None for name in (seed_list or [])}

    # 1) Keyword search
    for index, keyword in enumerate(keywords):
        progress(f"Reddit-Suche: {keyword}", index, len(keywords))
        for name in _search_subreddits(keyword, config):
            candidates.setdefault(name, None)

    names = list(candidates)
    progress(f"{len(names)} Subreddit-Kandidaten gefunden - lade Stammdaten", 0, len(names))

    # 2) Basic data for every candidate
    shallow: list[dict] = []
    limit = min(len(names), settings["max_communities"] * 2)
    for index, name in enumerate(names[:limit]):
        progress(f"Stammdaten r/{name}", index, limit)
        data = _about(name, config)
        if not data or int(data.get("subscribers") or 0) < settings["min_subscribers"]:
            continue
        shallow.append(_entry_from(data, keywords))

    # 3) One hop over sidebar mentions - that is how you find the small, tightly
    #    focused subs the search never surfaces.
    extra: set[str] = set()
    for entry in shallow:
        if entry["fit_raw"] >= 4:
            extra |= _mentioned_subs(entry["sidebar"])
    extra -= {e["handle"] for e in shallow}
    extra = set(sorted(extra)[:40])
    for index, name in enumerate(sorted(extra)):
        progress(f"Nachbar-Subreddit r/{name}", index, len(extra))
        data = _about(name, config)
        if not data or int(data.get("subscribers") or 0) < settings["min_subscribers"]:
            continue
        shallow.append(_entry_from(data, keywords))

    # 4) Deep scan for the most promising only - saves requests and time.
    shallow.sort(key=lambda e: e["fit_raw"], reverse=True)
    deep = shallow[: settings["deep_scan_top_n"]]
    for index, entry in enumerate(deep):
        progress(f"Regeln & Aktivitaet {entry['name']}", index, len(deep))
        rule_list = _rules(entry["handle"], config)
        texts = {f"Regel {i + 1}: {r.get('short_name') or ''}".strip():
                 f"{r.get('short_name') or ''} {r.get('description') or ''}"
                 for i, r in enumerate(rule_list)}
        texts["Sidebar"] = entry["sidebar"]
        texts["Hinweis beim Posten"] = entry["submit_text"]
        entry["rules"] = [{"name": r.get("short_name") or "", "text": (r.get("description") or "")[:1200]}
                          for r in rule_list]
        entry["analysis"] = rules.analyse(texts)
        entry.update(_activity(entry["handle"], config))

    for entry in shallow[settings["deep_scan_top_n"]:]:
        entry["rules"] = []
        entry["analysis"] = {"verdict": rules.UNKNOWN, "labels": [], "evidence": [],
                             "explicitly_allowed": False}
        entry["posts_per_day"] = 0.0
        entry["sample"] = 0

    return shallow


# ---------------------------------------------------------------------------
# Forums and wikis
# ---------------------------------------------------------------------------

_TITLE = re.compile(r"<title[^>]*>(.*?)</title>", re.I | re.S)
_LINK = re.compile(r'href=["\'](https?://[^"\'>\s]+)["\']', re.I)
_TAG = re.compile(r"<[^>]+>")


def _text_of(raw: bytes) -> str:
    text = raw.decode("utf-8", "replace")
    text = re.sub(r"<script.*?</script>|<style.*?</style>", " ", text, flags=re.I | re.S)
    return html.unescape(_TAG.sub(" ", text))


def scan_forums(config: dict, keywords: list[str], seed_list: list[dict] | None = None,
                progress: Progress = _noop) -> list[dict]:
    ua = config["user_agent"]
    seed_list = seed_list or []
    found: dict[str, dict] = {}
    harvested: dict[str, str] = {}

    for index, seed in enumerate(seed_list):
        progress(f"Forum pruefen: {seed.get('name') or seed['url']}", index, len(seed_list))
        entry = _probe_forum(seed["url"], seed.get("name") or seed["url"],
                             seed.get("note", ""), ua, keywords)
        # _harvest is a working field and has no business in the stored entry -
        # not even when the page turned out to be unreachable.
        harvest = entry.pop("_harvest", {})
        found[entry["id"]] = entry
        if entry["reachable"]:
            for url, label in harvest.items():
                harvested.setdefault(url, label)

    # One hop: from the reachable pages out to other forums.
    candidates = [(u, l) for u, l in harvested.items()
                  if not any(u.startswith(f["url"]) for f in seed_list)][:25]
    for index, (url, label) in enumerate(candidates):
        progress(f"Neues Forum pruefen: {label[:40]}", index, len(candidates))
        entry = _probe_forum(url, label, "Automatisch gefunden ueber Linkanalyse", ua, keywords)
        entry.pop("_harvest", None)
        if entry["reachable"] and entry["fit_raw"] > 0:
            found.setdefault(entry["id"], entry)

    return list(found.values())


def _probe_forum(url: str, name: str, note: str, ua: str, keywords: list[str]) -> dict:
    host = urllib.parse.urlparse(url).netloc.lower().removeprefix("www.")
    entry = {
        "platform": "forum",
        "id": f"forum:{host}",
        "name": name,
        "handle": host,
        "url": url,
        "title": "",
        "description": note,
        "note": note,
        "reachable": False,
        "status": 0,
        "fit_raw": 0.0,
        "subscribers": 0,
        "posts_per_day": 0.0,
        "rules": [],
        "analysis": {"verdict": rules.UNKNOWN, "labels": [], "evidence": [],
                     "explicitly_allowed": False},
        "_harvest": {},
    }

    if any(host.endswith(b) for b in seeds.FORUM_BLOCKLIST):
        entry["analysis"] = {"verdict": rules.FORBIDDEN, "labels": ["Interessenkonflikt - eigene Links tabu"],
                             "evidence": [], "explicitly_allowed": False}
        return entry

    try:
        status, raw = core.fetch(url, user_agent=ua, retries=2, timeout=20)
    except core.HttpError:
        return entry
    entry["status"] = status
    if status != 200 or not raw:
        return entry

    entry["reachable"] = True
    body = raw.decode("utf-8", "replace")
    title_match = _TITLE.search(body)
    if title_match:
        entry["title"] = html.unescape(_TAG.sub("", title_match.group(1))).strip()[:160]

    text = _text_of(raw)
    lowered = text.lower()
    entry["fit_raw"] = sum(min(lowered.count(k.lower()), 4) for k in keywords)

    # Read the rules or terms as well, if they are linked.
    texts = {"Startseite": text[:20000]}
    for link in _LINK.findall(body)[:400]:
        low = link.lower()
        if any(marker in low for marker in ("/rules", "/terms", "faq", "guidelines", "regeln")):
            try:
                sub_status, sub_raw = core.fetch(link, user_agent=ua, retries=1, timeout=15)
                if sub_status == 200:
                    texts["Regelseite"] = _text_of(sub_raw)[:20000]
                    entry["rules"] = [{"name": "Regelseite", "text": link}]
            except core.HttpError:
                pass
            break

    entry["analysis"] = rules.analyse(texts)

    # Harvest links to other forums.
    for link in _LINK.findall(body)[:400]:
        link_host = urllib.parse.urlparse(link).netloc.lower()
        if not link_host or link_host.endswith(host):
            continue
        bare = link_host.removeprefix("www.")
        if any(bare == v or bare.endswith("." + v) for v in seeds.FORUM_VENDOR_BLOCKLIST):
            continue
        if any(hint in link.lower() for hint in seeds.FORUM_URL_HINTS):
            root = f"{urllib.parse.urlparse(link).scheme}://{link_host}/"
            entry["_harvest"].setdefault(root, link_host)

    return entry


# ---------------------------------------------------------------------------
# Scoring and merging
# ---------------------------------------------------------------------------

def score_all(entries: list[dict]) -> list[dict]:
    max_fit = max((e.get("fit_raw", 0) for e in entries), default=1) or 1
    max_act = max((e.get("posts_per_day", 0) for e in entries), default=1) or 1

    for entry in entries:
        fit = entry.get("fit_raw", 0) / max_fit
        size = math.log10(max(entry.get("subscribers", 0), 1) + 1) / 7.0
        activity = min(entry.get("posts_per_day", 0) / max_act, 1.0)
        score = fit * 0.58 + min(size, 1.0) * 0.24 + activity * 0.18

        verdict = entry.get("analysis", {}).get("verdict", rules.UNKNOWN)
        if verdict == rules.FORBIDDEN:
            score *= 0.05           # stays visible, but right at the bottom
        elif verdict == rules.CONDITIONAL:
            score *= 0.82
        elif verdict == rules.UNKNOWN:
            score *= 0.6
        if entry.get("low_value"):
            score *= 0.15
        if entry.get("explicitly_allowed") or entry.get("analysis", {}).get("explicitly_allowed"):
            score *= 1.25

        # Unreachable pages go to the bottom - they are worthless for now.
        if entry.get("platform") == "forum" and not entry.get("reachable", True):
            score = 0.0

        entry["score"] = round(min(score, 1.0) * 100, 1)
        entry["scanned_at"] = int(time.time())

    entries.sort(key=lambda e: e["score"], reverse=True)
    return entries
