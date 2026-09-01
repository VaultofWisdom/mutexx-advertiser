"""
Hacker News and Lobsters, read-only.

These two are not discovered, they are known: there is exactly one of each. What
has to be worked out is something else, and it is the question the rest of the
scan cannot answer for them - whether this particular product has any business
being there.

For a subreddit, size and rules say most of it. For Hacker News they say nothing:
it is enormous and it will happily bury a submission that does not fit its taste,
without a rule ever being broken. So the evidence here is the record itself.
Through the Algolia search - open, no key - the last twelve months are counted:
how many stories on this topic were posted, and what score the middle one reached.
A product whose topic drew four stories at two points each has its answer, and it
is a better answer than any channel-fit heuristic could give it.

Both entries carry the same warning, because both are places where an ill-judged
submission is punished publicly and permanently.

Read-only, like every channel module here. Nothing in it can post.
"""

from __future__ import annotations

import html
import json
import re
import time
import urllib.parse

from . import core

_TAG = re.compile(r"<[^>]+>")

HN = "https://news.ycombinator.com"
ALGOLIA = "https://hn.algolia.com/api/v1"
LOBSTERS = "https://lobste.rs"

# Twelve months. Long enough that a niche topic is not judged on a quiet quarter,
# short enough that a wave from 2019 does not recommend a dead channel.
WINDOW_DAYS = 365


def _text_of(raw: bytes) -> str:
    text = raw.decode("utf-8", "replace")
    text = re.sub(r"<script.*?</script>|<style.*?</style>", " ", text, flags=re.I | re.S)
    return re.sub(r"\s+", " ", html.unescape(_TAG.sub(" ", text))).strip()


def _page(url: str, ua: str) -> str:
    try:
        status, raw = core.fetch(url, user_agent=ua, retries=1, timeout=20)
    except (core.HttpError, OSError):
        return ""
    return _text_of(raw) if status == 200 and raw else ""


def _json(url: str, ua: str) -> dict | list | None:
    try:
        status, raw = core.fetch(url, user_agent=ua, retries=1, timeout=25)
    except (core.HttpError, OSError):
        return None
    if status != 200 or not raw:
        return None
    try:
        return json.loads(raw.decode("utf-8", "replace"))
    except (json.JSONDecodeError, UnicodeDecodeError):
        return None


# ---------------------------------------------------------------------------
# Hacker News
# ---------------------------------------------------------------------------

def hn_topic_record(keywords: list[str], ua: str, window_days: int = WINDOW_DAYS) -> dict:
    """What the last twelve months of Hacker News say about this topic.

    Returns counts and a median score, never a recommendation - the numbers are
    shown to the user and they draw the conclusion. A median is used rather than an
    average because one story that reached the front page would otherwise make a
    dead topic look alive."""
    since = int(time.time()) - window_days * 86400
    stories = 0
    points: list[int] = []
    examples: list[dict] = []

    for keyword in keywords[:4]:
        params = urllib.parse.urlencode({
            "query": keyword,
            "tags": "story",
            "numericFilters": f"created_at_i>{since}",
            "hitsPerPage": 50,
        })
        payload = _json(f"{ALGOLIA}/search?{params}", ua)
        if not isinstance(payload, dict):
            continue
        hits = payload.get("hits")
        if not isinstance(hits, list):
            continue
        try:
            stories += int(payload.get("nbHits") or 0)
        except (TypeError, ValueError):
            pass
        for hit in hits:
            if not isinstance(hit, dict):
                continue
            points.append(int(hit.get("points") or 0))
            if len(examples) < 5 and hit.get("title"):
                examples.append({
                    "title": str(hit["title"])[:140],
                    "points": int(hit.get("points") or 0),
                    "url": f"{HN}/item?id={hit.get('objectID')}",
                })

    points.sort()
    return {
        "stories": stories,
        "window_days": window_days,
        "sample": len(points),
        "median_points": points[len(points) // 2] if points else 0,
        "examples": sorted(examples, key=lambda e: e["points"], reverse=True),
    }


def hacker_news(keywords: list[str], ua: str) -> dict:
    """One entry for the Show HN path. Not the front page in general - Show HN is
    the one place on Hacker News where your own work is what is being asked for."""
    guidelines = _page(f"{HN}/newsguidelines.html", ua)
    show_rules = _page(f"{HN}/showhn.html", ua)
    record = hn_topic_record(keywords, ua)

    texts = {}
    if guidelines:
        texts["Hacker News guidelines"] = guidelines[:20000]
    if show_rules:
        texts["Show HN rules"] = show_rules[:20000]

    return {
        "platform": "hackernews",
        "id": "hackernews:showhn",
        "name": "Hacker News (Show HN)",
        "handle": "showhn",
        "url": f"{HN}/show",
        "submit_url": f"{HN}/submit",
        "title": "Show HN",
        "description": "",
        # Hacker News publishes no member count. Zero here means "not published",
        # not "empty" - see discovery._SIZE_SCALE and the note on scoring.
        "subscribers": 0,
        "posts_per_day": round(record["stories"] / max(record["window_days"], 1), 2),
        "topic_record": record,
        "_rule_texts": texts,
        "reachable": bool(texts),
    }


# ---------------------------------------------------------------------------
# Lobsters
# ---------------------------------------------------------------------------

def lobsters_tags(keywords: list[str], ua: str) -> list[str]:
    """Lobsters sorts everything by tag, and the tag list is public. A topic with no
    matching tag has no place there - which is a cheaper and more honest answer than
    scraping a search page they answer with 400."""
    payload = _json(f"{LOBSTERS}/tags.json", ua)
    if not isinstance(payload, list):
        return []
    available = []
    for item in payload:
        if isinstance(item, dict) and item.get("tag") and item.get("active", True):
            available.append((str(item["tag"]).lower(),
                              str(item.get("description") or "").lower()))
    matched: list[str] = []
    for keyword in keywords:
        low = keyword.lower().strip()
        if len(low) < 3:
            continue
        for tag, description in available:
            if tag in matched:
                continue
            if tag == low or low in description or (len(tag) > 3 and tag in low):
                matched.append(tag)
    return matched[:8]


def lobsters(keywords: list[str], ua: str) -> dict:
    about = _page(f"{LOBSTERS}/about", ua)
    tags = lobsters_tags(keywords, ua)

    texts = {}
    if about:
        texts["Lobsters about"] = about[:20000]

    return {
        "platform": "lobsters",
        "id": "lobsters:lobsters",
        "name": "Lobsters",
        "handle": "lobsters",
        "url": LOBSTERS,
        "submit_url": f"{LOBSTERS}/stories/new",
        "title": "Lobsters",
        "description": "",
        "subscribers": 0,
        "posts_per_day": 0.0,
        "matching_tags": tags,
        # Not a rule but a fact about the site, and the one that decides whether any
        # of this is available to the user at all: accounts exist only by invitation.
        # A green light on a site you cannot post to is worse than no entry.
        "invite_only": True,
        "_rule_texts": texts,
        "reachable": bool(texts),
    }
