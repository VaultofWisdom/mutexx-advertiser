"""
Seed lists for the scan - per product, no longer built in.

This file used to hold the subreddits and forums of a single subject. For a tool meant
to advertise arbitrary products that is worthless: the seed list has to come out of the
product.

Three routes, in this order:
  1. What the user enters. They know their niche.
  2. What the Anthropic API suggests from the profile and the analysis.
  3. Search paths that can be built from the keywords alone.

IMPORTANT in all three cases: these are candidates, not established facts. Every entry
is checked against the real source during the scan - whatever no longer exists drops out
automatically. A language model's suggestions in particular are assertions; the
scanner's check is exactly why they can be used anyway.
"""

from __future__ import annotations

import json
import re
import urllib.parse
from typing import Any

from . import core, i18n

# ---------------------------------------------------------------------------
# Per-product seed lists
# ---------------------------------------------------------------------------

EMPTY_SEEDS: dict[str, Any] = {"subreddits": [], "forums": [], "source": "empty"}


def load_seeds(slug: str) -> dict:
    stored = core.load_product(slug, "seeds", None)
    if not isinstance(stored, dict):
        return json.loads(json.dumps(EMPTY_SEEDS))
    return {
        "subreddits": [str(name).strip().lstrip("/").removeprefix("r/")
                       for name in stored.get("subreddits", []) if str(name).strip()],
        "forums": [entry for entry in stored.get("forums", [])
                   if isinstance(entry, dict) and entry.get("url")],
        "source": stored.get("source", "manual"),
    }


def save_seeds(slug: str, data: dict) -> dict:
    cleaned = {
        "subreddits": [],
        "forums": [],
        "source": data.get("source", "manual"),
    }
    for name in data.get("subreddits", []) or []:
        handle = str(name).strip().lstrip("/").removeprefix("r/")
        if handle and handle not in cleaned["subreddits"]:
            cleaned["subreddits"].append(handle)
    seen: set[str] = set()
    for entry in data.get("forums", []) or []:
        if not isinstance(entry, dict):
            entry = {"url": str(entry)}
        url = (entry.get("url") or "").strip()
        if not url:
            continue
        if not url.startswith(("http://", "https://")):
            url = "https://" + url
        host = urllib.parse.urlparse(url).netloc.lower()
        if not host or host in seen:
            continue
        seen.add(host)
        cleaned["forums"].append({
            "url": url,
            "name": (entry.get("name") or host).strip(),
            "note": (entry.get("note") or "").strip(),
        })
    core.save_product(slug, "seeds", cleaned)
    return cleaned


# ---------------------------------------------------------------------------
# Search paths that can be built from keywords alone
# ---------------------------------------------------------------------------

_DISCORD_DIRECTORIES = [
    ("Disboard", "https://disboard.org/search?keyword={q}"),
    ("Discadia", "https://discadia.com/servers/?q={q}"),
    ("Discord Me", "https://discord.me/servers?q={q}"),
]


def discord_searches(keywords: list[str], limit: int = 8) -> list[dict]:
    """Invite links expire, so none are hard-coded here. Instead, search paths the app
    opens - the user enters any server they find once, and it is remembered."""
    out: list[dict] = []
    for keyword in keywords[:limit]:
        query = urllib.parse.quote_plus(keyword)
        label, pattern = _DISCORD_DIRECTORIES[len(out) % len(_DISCORD_DIRECTORIES)]
        out.append({"name": f"{label}: {keyword}", "url": pattern.format(q=query)})
    return out


# ---------------------------------------------------------------------------
# Generic filters. These hold for every product, so they stay here.
# ---------------------------------------------------------------------------

# Subreddits that are, in practice, nothing but advertising. Traffic from there is
# close to worthless - they are not blocked, but heavily downweighted.
LOW_VALUE_SUBS: set[str] = {
    "promote", "advertise", "AdvertiseYourVideos", "SelfPromotionForYou",
    "PromoteYourProject", "shamelessplug", "PromoteYourWebsite", "SelfPromotion",
    "PromoteYourBusiness", "IndieBiz", "SmallYoutubers",
}

# Domains where links of your own are off limits on principle (conflict of interest).
FORUM_BLOCKLIST: set[str] = {
    "wikipedia.org", "wikimedia.org", "wikidata.org",
}

# Forum software vendors and platform front pages - link harvesting turns these up
# constantly, but they are not communities.
FORUM_VENDOR_BLOCKLIST: tuple[str, ...] = (
    "phpbb.com", "phpbb.de", "discourse.org", "xenforo.com", "invisioncommunity.com",
    "simplemachines.org", "mybb.com", "proboards.com", "vbulletin.com", "tapatalk.com",
    "wordpress.org", "wordpress.com", "cloudflare.com", "godaddy.com", "wix.com",
    "squarespace.com", "google.com", "youtube.com", "facebook.com", "twitter.com",
    "x.com", "instagram.com", "discord.com", "discord.gg", "patreon.com", "amazon.com",
    "paypal.com", "github.com", "mozilla.org", "adobe.com", "linkedin.com", "tiktok.com",
)

# Heuristic for spotting real forums while harvesting links.
FORUM_URL_HINTS: tuple[str, ...] = (
    "/forum", "/forums", "/board", "/boards", "/community", "/viewforum",
    "phpbb", "smf", "xenforo", "invision", "discourse", "vbulletin", "proboards",
)


# ---------------------------------------------------------------------------
# Suggestions through the Anthropic API
# ---------------------------------------------------------------------------

_SYSTEM = """You name communities where a particular product might fit thematically.
Rules:
- Name only communities you believe actually exist. Do not guess wildly.
- No pure advertising communities, no link directories, no marketplaces.
- Forums with the full front-page URL.
- Subreddits without 'r/', just the name.
- Answer only as JSON, with no preamble and no code fence.

Format:
{"subreddits": ["name", "..."],
 "forums": [{"name": "...", "url": "https://...", "note": "half a sentence on what for"}]}"""


def suggest_with_api(product: dict, analysis_result: dict, config: dict,
                     keywords: list[str] | None = None) -> dict:
    """Has the API suggest starting points. The scanner checks them afterwards - an
    invented forum fails on the first fetch."""
    api = config.get("anthropic", {})
    key = (api.get("api_key") or "").strip()
    if not key:
        raise ValueError(i18n.t("error.no_api_key"))

    keywords = keywords or product.get("keywords", [])
    prompt = f"""PRODUCT
Name: {product.get('name')}
One-liner: {product.get('one_liner') or '(none)'}
Description: {str(product.get('description') or '(none)')[:1200]}
Audience: {product.get('audience') or '(not given)'}
Regions: {', '.join(product.get('regions') or [])}
Languages: {', '.join(product.get('languages') or [])}

Keywords: {', '.join(keywords[:25]) or '(none)'}
Audience segments: {'; '.join(seg.get('name','') for seg in analysis_result.get('audience_segments') or []) or '(none)'}

Name 12 to 20 subreddits and 6 to 12 forums or specialist communities."""

    status, raw = core.post_json(
        "https://api.anthropic.com/v1/messages",
        {
            "model": api.get("model") or "claude-opus-5",
            "max_tokens": 2000,
            "system": _SYSTEM,
            "messages": [{"role": "user", "content": prompt}],
        },
        user_agent=config.get("user_agent", "MutexxAdvertiser/0.2"),
        headers={"x-api-key": key, "anthropic-version": "2023-06-01"},
    )
    if status != 200:
        raise ValueError(i18n.t("error.api_status", status=status, detail=raw[:300]))

    payload = json.loads(raw)
    text = "".join(block.get("text", "") for block in payload.get("content", []))
    match = re.search(r"\{.*\}", text, re.S)
    if not match:
        raise ValueError(i18n.t("error.no_json"))
    parsed = json.loads(match.group(0))

    return {
        "subreddits": [str(name) for name in (parsed.get("subreddits") or [])][:30],
        "forums": [entry for entry in (parsed.get("forums") or [])
                   if isinstance(entry, dict) and entry.get("url")][:20],
        "source": "suggested",
    }
