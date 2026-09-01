"""
Discourse forums, read-only.

Discourse runs a large share of the forums that still matter, and unlike a random
phpBB board it answers machine-readable questions about itself. That turns three
guesses in scan_forums into facts:

  * /about.json - the real member count and real activity, instead of the zero a
    scraped front page leaves behind. A forum with no numbers always ranks last,
    however well it fits.
  * /guidelines and /tos - the rules at a known address, instead of hoping a link
    on the front page happens to contain the word "rules".
  * /categories.json - and this is the one that changes an answer rather than
    sharpening it. Many forums forbid self-promotion everywhere and then keep one
    category for exactly that. Without the category list the forum reads as red
    and drops out; with it, it is a forum you may post in, in one place, if you
    follow the rule.

Read-only, like every other channel module here. Nothing in it can post.
"""

from __future__ import annotations

import html
import json
import re
import urllib.parse

from . import core

_TAG = re.compile(r"<[^>]+>")


def base_of(url: str) -> str:
    parts = urllib.parse.urlparse(url if "//" in url else "https://" + url)
    if not parts.netloc:
        return ""
    return f"{parts.scheme or 'https'}://{parts.netloc}"


def _text_of(raw: bytes) -> str:
    text = raw.decode("utf-8", "replace")
    text = re.sub(r"<script.*?</script>|<style.*?</style>", " ", text, flags=re.I | re.S)
    return re.sub(r"\s+", " ", html.unescape(_TAG.sub(" ", text))).strip()


def _json(url: str, ua: str, timeout: int = 15) -> dict | None:
    try:
        status, raw = core.fetch(url, user_agent=ua, retries=1, timeout=timeout)
    except (core.HttpError, OSError):
        return None
    if status != 200 or not raw:
        return None
    try:
        payload = json.loads(raw.decode("utf-8", "replace"))
    except (json.JSONDecodeError, UnicodeDecodeError):
        # A non-Discourse site answers /about.json with its 404 page, and that
        # page is HTML. Not an error - just not a Discourse forum.
        return None
    return payload if isinstance(payload, dict) else None


def about(url: str, ua: str) -> dict | None:
    """Identifies a Discourse forum and reads its figures. None means: not Discourse
    (or not answering), and the caller falls back to the ordinary forum probe."""
    root = base_of(url)
    if not root:
        return None
    payload = _json(f"{root}/about.json", ua)
    data = (payload or {}).get("about")
    if not isinstance(data, dict) or "stats" not in data:
        return None
    stats = data.get("stats") or {}

    def number(field: str) -> int:
        try:
            return int(stats.get(field) or 0)
        except (TypeError, ValueError):
            return 0

    return {
        "base": root,
        "title": str(data.get("title") or "")[:160],
        "description": str(data.get("description") or "")[:600],
        "version": str(data.get("version") or ""),
        "users": number("users_count"),
        # Posts per day from the last seven days. The lifetime average would flatter
        # a forum that was busy in 2014 and has been quiet ever since.
        "posts_per_day": round(number("posts_7_days") / 7.0, 1),
        "topics_7_days": number("topics_7_days"),
    }


# Both paths hold the same document on most instances; /faq redirects to
# /guidelines. Fetching both is one wasted request at most, and skipping the wrong
# one costs the rules entirely.
_RULE_PATHS = (("Guidelines", "/guidelines"), ("Terms of service", "/tos"))


def rule_texts(root: str, ua: str) -> dict[str, str]:
    texts: dict[str, str] = {}
    for label, path in _RULE_PATHS:
        try:
            status, raw = core.fetch(root + path, user_agent=ua, retries=1, timeout=15)
        except (core.HttpError, OSError):
            continue
        if status != 200 or not raw:
            continue
        text = _text_of(raw)
        if len(text) > 200:
            texts[label] = text[:20000]
    return texts


def categories(root: str, ua: str) -> list[dict]:
    payload = _json(f"{root}/categories.json", ua, timeout=20)
    raw_list = ((payload or {}).get("category_list") or {}).get("categories")
    if not isinstance(raw_list, list):
        return []
    out: list[dict] = []
    for item in raw_list:
        if not isinstance(item, dict) or item.get("read_restricted"):
            continue
        slug = str(item.get("slug") or "")
        name = str(item.get("name") or "")
        if not slug or not name:
            continue
        description = str(item.get("description_text") or item.get("description") or "")
        out.append({
            "name": name,
            "slug": slug,
            "url": f"{root}/c/{slug}/{item.get('id')}",
            "description": _text_of(description.encode("utf-8"))[:600],
            "topics": int(item.get("topic_count") or 0),
        })
    return out


# A category is only treated as an invitation when its NAME says so and its own
# description says so as well. The name alone is not enough: "Projects" is where
# people discuss projects at least as often as it is where they announce their own,
# and reading the wrong one as permission is how a forum bans a domain.
_SHOWCASE_NAME = re.compile(
    r"show\s*(and|&|n)?\s*tell|showcase|share\s+your|self[\s-]?promo\w*|"
    r"promote|advertis\w+|made\s+(this|with)|built\s+with|"
    r"eigene\s+projekte|zeig|vorstell\w*|werbung",
    re.I)

_SHOWCASE_INVITE = re.compile(
    r"(show|share|post|present|announce|showcase)\s+(off\s+)?(your|the\s+things\s+you)"
    r"|your\s+(own\s+)?(project|work|app|plugin|theme|site|website|tool|creation)s?"
    r"|(zeig|teil|stell)\w*\s+(hier\s+)?(eure|deine|dein|euer)"
    r"|selbst\s*(gebaut|geschrieben|entwickelt)",
    re.I)


def showcase_category(category_list: list[dict]) -> dict | None:
    """The category where sharing your own work is invited - or None.

    Returns the category together with the sentence it rests on, because a verdict
    the user cannot check is worth nothing here."""
    best: dict | None = None
    for category in category_list:
        if not _SHOWCASE_NAME.search(category["name"]):
            continue
        match = _SHOWCASE_INVITE.search(category["description"])
        if not match:
            continue
        quote = category["description"]
        start = max(match.start() - 60, 0)
        snippet = quote[start:match.end() + 90].strip()
        candidate = dict(category)
        candidate["quote"] = ("..." if start else "") + snippet
        # More topics means the category is actually used, not just declared.
        if best is None or candidate["topics"] > best["topics"]:
            best = candidate
    return best
