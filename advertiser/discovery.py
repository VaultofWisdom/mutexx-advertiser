"""
Discovery: finds suitable communities and scores them.

Reddit goes through the official API (read-only, see reddit_api.py). Lemmy needs no
approval at all and federates, so a few instances reach most of the network.
Forums are checked for reachability and yield further candidates through link
harvesting; where a forum runs Discourse it is asked about itself instead of
guessed at (see discourse_api.py). Hacker News and Lobsters are not discovered but
known, so what is worked out for them is whether the product belongs there at all
(see aggregators.py).
"""

from __future__ import annotations

import datetime
import html
import math
import re
import time
import urllib.parse
from typing import Callable

from . import aggregators, core, discourse_api, lemmy_api, reddit_api, rules, seeds

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


def _enrich_discourse(entry: dict, profile: dict, texts: dict[str, str], ua: str) -> None:
    """Replaces the three guesses of the generic forum probe with what the forum
    says about itself: its size, its real activity, and its rules."""
    entry["forum_software"] = "discourse"
    entry["title"] = profile["title"] or entry["title"]
    if profile["description"]:
        entry["description"] = profile["description"]
    entry["subscribers"] = profile["users"]
    entry["posts_per_day"] = profile["posts_per_day"]

    rule_pages = discourse_api.rule_texts(profile["base"], ua)
    texts.update(rule_pages)
    entry["rules"] = [{"name": label, "text": text[:1200]} for label, text in rule_pages.items()]

    entry["categories"] = discourse_api.categories(profile["base"], ua)
    showcase = discourse_api.showcase_category(entry["categories"])
    entry["showcase_category"] = showcase
    if showcase:
        # Into the rule analysis as well: a category that invites you to share your
        # work is part of what this forum permits, not decoration beside it.
        texts[f"Kategorie: {showcase['name']}"] = showcase["description"]


def _apply_showcase(entry: dict) -> None:
    """A forum that forbids self-promotion everywhere and keeps one category for
    exactly that is not closed - it is a forum with one condition.

    Without this it reads as red and drops out of every campaign, which is both
    wrong and the more expensive of the two errors here: the honest, invited post
    is the one that never gets written. It stays amber rather than green, because
    the condition is real - post in that category and nowhere else - and the
    quote the category rests on travels with the verdict so the user can check it.
    """
    showcase = entry.get("showcase_category")
    analysis = entry["analysis"]
    if not showcase or analysis["verdict"] != rules.FORBIDDEN:
        return
    analysis["verdict"] = rules.CONDITIONAL
    if "rule.showcase_category" not in analysis["labels"]:
        analysis["labels"].insert(0, "rule.showcase_category")
    analysis["evidence"].insert(0, {
        "source": showcase["name"],
        "label": "rule.showcase_category",
        "quote": showcase["quote"],
    })


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

    texts = {"Startseite": text[:20000]}

    # Discourse answers questions about itself, so nothing here has to be guessed.
    # Everything below the branch is the fallback for forums that do not.
    profile = discourse_api.about(url, ua)
    if profile:
        _enrich_discourse(entry, profile, texts, ua)
    else:
        # Read the rules or terms as well, if they are linked.
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

    if profile:
        _apply_showcase(entry)

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
# Lemmy
# ---------------------------------------------------------------------------

# Below this many characters a community description is a headline, not a rule
# set - see the note in scan_lemmy on why that turns a green light grey.
MIN_RULE_TEXT = 120


def lemmy_fit_score(data: dict, keywords: list[str]) -> float:
    haystack = " ".join(str(data.get(field) or "") for field in
                        ("name", "title", "description", "sidebar")).lower()
    if not haystack.strip():
        return 0.0
    hits = 0.0
    for keyword in keywords:
        occurrences = haystack.count(keyword.lower())
        if occurrences:
            hits += min(occurrences, 4) * (1.6 if " " in keyword else 1.0)
    return hits


def _lemmy_entry(view: dict, keywords: list[str]) -> dict | None:
    data = view.get("community") or {}
    counts = view.get("counts") or {}
    handle, url = lemmy_api.handle_of(view)
    if not handle:
        return None
    if data.get("removed") or data.get("deleted"):
        return None
    description = str(data.get("description") or "")
    merged = {
        "name": data.get("name") or "",
        "title": data.get("title") or "",
        "description": description,
        "sidebar": str(data.get("sidebar") or ""),
    }
    return {
        "platform": "lemmy",
        "id": f"lemmy:{handle}",
        "name": f"!{handle}",
        "handle": handle,
        "url": url,
        "title": merged["title"],
        # On Lemmy the description IS the sidebar - the rules are in there and
        # nowhere else. So it is kept in full for rules.analyse, not cut down to
        # a teaser the way Reddit's public_description is.
        "description": description[:600],
        "sidebar": (description + "\n" + merged["sidebar"])[:6000],
        "subscribers": int(counts.get("subscribers") or 0),
        "over18": bool(data.get("nsfw")),
        # A community only moderators may post in is a red light, not a hurdle -
        # no draft in the world gets past it.
        "mods_only": bool(data.get("posting_restricted_to_mods")),
        "active_week": int(counts.get("users_active_week") or 0),
        "fit_raw": lemmy_fit_score(merged, keywords),
    }


def _timestamp(value: object) -> float:
    """Lemmy sends ISO 8601, in several shapes across versions."""
    if isinstance(value, (int, float)):
        return float(value)
    if not isinstance(value, str) or not value.strip():
        return 0.0
    text = value.strip().replace("Z", "+00:00")
    if "." in text:
        # Fractional seconds vary in length between versions; datetime wants six.
        head, _, tail = text.partition(".")
        digits = "".join(ch for ch in tail if ch.isdigit())[:6]
        rest = tail[len(digits):]
        rest = rest if rest.startswith(("+", "-")) else ""
        text = f"{head}.{digits.ljust(6, '0')}{rest}"
    try:
        parsed = datetime.datetime.fromisoformat(text)
    except ValueError:
        return 0.0
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=datetime.timezone.utc)
    return parsed.timestamp()


def _lemmy_activity(instance: str, handle: str, ua: str) -> dict:
    """Posts per day across the most recent submissions - the same measure as on Reddit."""
    items = lemmy_api.posts(instance, handle, ua, limit=50)
    stamps = []
    for item in items:
        published = ((item.get("post") or {}).get("published")) or item.get("published")
        parsed = _timestamp(published)
        if parsed:
            stamps.append(parsed)
    if len(stamps) < 2:
        return {"posts_per_day": 0.0, "sample": len(stamps)}
    span_days = max((max(stamps) - min(stamps)) / 86400.0, 0.05)
    return {"posts_per_day": round(len(stamps) / span_days, 1), "sample": len(stamps)}


def scan_lemmy(config: dict, keywords: list[str], instances: list[str] | None = None,
               progress: Progress = _noop) -> list[dict]:
    """
    Unlike Reddit this needs no approval and no key. Because Lemmy federates, a
    search on a few large instances reaches most of the network - which is why
    the seed list here holds instances, not communities.
    """
    settings = config["discovery"]
    ua = config["user_agent"]
    min_subscribers = int(settings.get("lemmy_min_subscribers", 40))

    hosts: list[str] = []
    for value in (instances or lemmy_api.DEFAULT_INSTANCES):
        host = lemmy_api.normalise_instance(value)
        if host and host not in hosts:
            hosts.append(host)

    # Which instance an entry was reached through - needed for the deep scan,
    # because a community is only readable through an instance that federates
    # with it.
    found: dict[str, dict] = {}
    via: dict[str, str] = {}
    steps = max(len(hosts) * len(keywords), 1)
    step = 0

    for host in hosts:
        for keyword in keywords:
            step += 1
            progress(f"Lemmy-Suche auf {host}: {keyword}", step, steps)
            for view in lemmy_api.search_communities(host, keyword, ua):
                entry = _lemmy_entry(view, keywords)
                if not entry or entry["subscribers"] < min_subscribers:
                    continue
                known = found.get(entry["id"])
                if known and entry["fit_raw"] <= known["fit_raw"]:
                    continue
                # The same community seen through a second instance: keep the
                # richer record, since federated copies can lag behind.
                found[entry["id"]] = entry
                via[entry["id"]] = host

    entries = sorted(found.values(), key=lambda e: e["fit_raw"], reverse=True)
    entries = entries[: settings["max_communities"]]

    # Instance rules are fetched once per instance, not once per community.
    instance_rules: dict[str, dict[str, str]] = {}

    deep = entries[: settings["deep_scan_top_n"]]
    for index, entry in enumerate(deep):
        progress(f"Regeln & Aktivitaet {entry['name']}", index, len(deep))
        home = entry["handle"].split("@", 1)[1]
        source = via.get(entry["id"], home)
        if home not in instance_rules:
            instance_rules[home] = lemmy_api.site_rules(home, ua)

        texts = {"Community-Beschreibung": entry["sidebar"]}
        texts.update(instance_rules[home])
        entry["rules"] = [{"name": "Community", "text": entry["sidebar"][:1200]}]
        entry["rules"] += [{"name": name, "text": text[:1200]}
                           for name, text in instance_rules[home].items()]
        entry["analysis"] = rules.analyse(texts)

        # A Lemmy community has no structured rule list the way a subreddit does;
        # whatever rules it has are in the description, or nowhere. So a community
        # that wrote nothing has not told us it permits anything - and the
        # instance's welcome text must not be read as its answer. Green here would
        # be the one mistake this whole app exists to prevent, so it becomes grey:
        # read the rules yourself. A ban is left standing, because an instance ban
        # applies to the community whether the community mentions it or not.
        if len(entry["sidebar"].strip()) < MIN_RULE_TEXT and \
                entry["analysis"]["verdict"] != rules.FORBIDDEN:
            entry["analysis"]["verdict"] = rules.UNKNOWN
            entry["analysis"]["explicitly_allowed"] = False

        # A community only moderators may post in is a wall, not a condition -
        # and it outranks anything the description says.
        if entry["mods_only"]:
            verdict = entry["analysis"]
            verdict["verdict"] = rules.FORBIDDEN
            if "rule.mods_only" not in verdict["labels"]:
                verdict["labels"].insert(0, "rule.mods_only")
            verdict["explicitly_allowed"] = False

        entry.update(_lemmy_activity(source, entry["handle"], ua))

    for entry in entries[settings["deep_scan_top_n"]:]:
        entry["rules"] = []
        entry["analysis"] = {"verdict": rules.UNKNOWN, "labels": [], "evidence": [],
                             "explicitly_allowed": False}
        entry["posts_per_day"] = 0.0
        entry["sample"] = 0

    return entries


# ---------------------------------------------------------------------------
# Hacker News and Lobsters
# ---------------------------------------------------------------------------

# The record on Hacker News stands in for the keyword density used everywhere
# else: 400 stories on the topic in a year is a full fit, and the median score
# discounts it, because a topic with many stories that all die at two points is
# not a topic this audience wants. The raw numbers stay on the entry so the user
# can overrule the arithmetic - which is the point of showing them.
_HN_STORIES_FOR_FULL_FIT = 400
_HN_POINTS_FOR_FULL_QUALITY = 20
_HN_FIT_CEILING = 40.0


def _hn_fit(record: dict) -> float:
    volume = min(record.get("stories", 0) / _HN_STORIES_FOR_FULL_FIT, 1.0)
    quality = min((record.get("median_points", 0) or 0) / _HN_POINTS_FOR_FULL_QUALITY, 1.0)
    # A floor under the quality term: a topic that lands quietly is still a topic
    # that lands, and zeroing it would hide the channel completely.
    return round(volume * max(quality, 0.25) * _HN_FIT_CEILING, 2)


def scan_aggregators(config: dict, keywords: list[str],
                     progress: Progress = _noop) -> list[dict]:
    """Hacker News and Lobsters. Neither is discovered - there is one of each -
    so the work is deciding whether this product belongs there."""
    ua = config["user_agent"]
    entries: list[dict] = []

    progress("Hacker News: Regeln und Themenlage", 0, 2)
    entry = aggregators.hacker_news(keywords, ua)
    entry["fit_raw"] = _hn_fit(entry["topic_record"])
    _finish_aggregator(entry)
    entries.append(entry)

    progress("Lobsters: Regeln und passende Tags", 1, 2)
    entry = aggregators.lobsters(keywords, ua)
    # Lobsters sorts everything by tag. No matching tag, no place for the topic -
    # and that is a fit of zero, not a small one.
    entry["fit_raw"] = float(len(entry["matching_tags"]) * 4)
    _finish_aggregator(entry)
    if entry["invite_only"]:
        _apply_invite_only(entry)
    entries.append(entry)

    return entries


def _finish_aggregator(entry: dict) -> None:
    texts = entry.pop("_rule_texts", {})
    entry["rules"] = [{"name": name, "text": text[:1200]} for name, text in texts.items()]
    entry["analysis"] = rules.analyse(texts)


def _apply_invite_only(entry: dict) -> None:
    """Lobsters hands out accounts by invitation only. Whatever its rules permit,
    a user without an invitation cannot post there at all - and a green light on a
    site you have no account for is worse than no entry, because it costs the user
    the time to find that out.

    It becomes a condition rather than a ban: the invitation is a real hurdle, not
    a prohibition, and someone who has one should not be told the door is shut.
    """
    analysis = entry["analysis"]
    if analysis["verdict"] == rules.FORBIDDEN:
        return
    analysis["verdict"] = rules.CONDITIONAL
    if "rule.invite_only" not in analysis["labels"]:
        analysis["labels"].insert(0, "rule.invite_only")


# ---------------------------------------------------------------------------
# Scoring and merging
# ---------------------------------------------------------------------------

# Size is measured against the platform's own ceiling, not a shared one. A
# Lemmy community with 8,000 subscribers is a large one; a subreddit with 8,000
# is small. Against one common scale every Lemmy entry would score as tiny and
# the ranking would say "go to Reddit" no matter what the rules there said.
_SIZE_SCALE = {"reddit": 7.0, "lemmy": 4.9, "forum": 7.0}

# Platforms that publish no member count at all. Their zero means "not published",
# not "nobody is there" - counting it as an empty community would push Hacker News
# below a forum with forty members. The size weight is redistributed over the two
# figures that ARE real for them instead of being scored as zero.
_NO_SIZE_PLATFORMS = frozenset({"hackernews", "lobsters"})

_W_FIT, _W_SIZE, _W_ACTIVITY = 0.58, 0.24, 0.18


def score_all(entries: list[dict]) -> list[dict]:
    max_fit = max((e.get("fit_raw", 0) for e in entries), default=1) or 1
    max_act = max((e.get("posts_per_day", 0) for e in entries), default=1) or 1

    for entry in entries:
        fit = entry.get("fit_raw", 0) / max_fit
        scale = _SIZE_SCALE.get(entry.get("platform", ""), 7.0)
        size = math.log10(max(entry.get("subscribers", 0), 1) + 1) / scale
        activity = min(entry.get("posts_per_day", 0) / max_act, 1.0)
        if entry.get("platform") in _NO_SIZE_PLATFORMS:
            share = _W_FIT + _W_ACTIVITY
            score = (fit * _W_FIT + activity * _W_ACTIVITY) / share
        else:
            score = fit * _W_FIT + min(size, 1.0) * _W_SIZE + activity * _W_ACTIVITY

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
