"""
Publishing.

Two strictly separated routes:

1. FULLY AUTOMATIC - only in channels you own yourself, or where bot posts are
   explicitly allowed: your own Discord server (webhook), your own Mastodon
   account. These go out without asking.

2. ONE-CLICK ASSISTANT - for other people's communities (Reddit, foreign forums).
   The app builds the finished, pre-filled post and opens the form; a human sends
   it. That is deliberate, not a missing feature: distributing the same link
   automatically across other people's subreddits is spam under Reddit's rules and
   leads to a ban on the promoted domain - including the links other people set
   voluntarily.
"""

from __future__ import annotations

import time
import urllib.parse

from . import core, i18n


# ---------------------------------------------------------------------------
# Route 1: your own channels - genuine auto-posting
# ---------------------------------------------------------------------------

def post_discord_webhook(webhook_url: str, draft: dict, config: dict, product: dict) -> dict:
    """Posts to a Discord server you OWN. A webhook only works where someone with
    server rights created it - which is what makes this safe."""
    content = f"**{draft['title']}**\n\n{draft['body']}"
    if len(content) > 1900:
        content = content[:1890] + " ..."
    payload = {
        "content": content,
        "username": (product.get("name") or "Mutexx Advertiser")[:80],
        "allowed_mentions": {"parse": []},
    }
    status, raw = core.post_json(webhook_url, payload, user_agent=config["user_agent"])
    ok = status in (200, 204)
    return {"ok": ok, "status": status, "detail": "" if ok else raw[:400]}


def post_mastodon(config: dict, draft: dict) -> dict:
    """Posts to the Mastodon account you OWN (token from Settings)."""
    mastodon = config["auto_channels"]["mastodon"]
    instance = (mastodon.get("instance") or "").strip().rstrip("/")
    token = (mastodon.get("access_token") or "").strip()
    if not instance or not token:
        return {"ok": False, "status": 0, "detail": "Mastodon ist nicht konfiguriert."}
    if not instance.startswith("http"):
        instance = "https://" + instance

    text = f"{draft['title']}\n\n{draft['body']}"
    if len(text) > 480:
        text = text[:470] + " ..."
    status, raw = core.post_json(
        f"{instance}/api/v1/statuses",
        {"status": text, "visibility": "public"},
        user_agent=config["user_agent"],
        headers={"Authorization": f"Bearer {token}"},
    )
    ok = status in (200, 201)
    return {"ok": ok, "status": status, "detail": "" if ok else raw[:400]}


def run_auto_channels(config: dict, draft: dict, product: dict) -> list[dict]:
    """Sends a draft to every configured owned channel."""
    results: list[dict] = []
    for hook in config["auto_channels"].get("discord_webhooks", []):
        url = hook.get("url") if isinstance(hook, dict) else hook
        label = hook.get("name", "Discord") if isinstance(hook, dict) else "Discord"
        if not url:
            continue
        result = post_discord_webhook(url, draft, config, product)
        result.update({"channel": label, "kind": "discord"})
        results.append(result)

    mastodon = config["auto_channels"].get("mastodon", {})
    if mastodon.get("instance") and mastodon.get("access_token"):
        result = post_mastodon(config, draft)
        result.update({"channel": mastodon["instance"], "kind": "mastodon"})
        results.append(result)

    return results


# ---------------------------------------------------------------------------
# Route 2: one-click assistant for other people's communities
# ---------------------------------------------------------------------------

def reddit_submit_url(subreddit: str, draft: dict) -> str:
    """A pre-filled Reddit form. The human presses Post."""
    query = urllib.parse.urlencode({"title": draft["title"], "text": draft["body"]})
    return f"https://www.reddit.com/r/{urllib.parse.quote(subreddit)}/submit?selftext=true&{query}"


# ---------------------------------------------------------------------------
# Safety catch: stops a campaign from turning back into spam
# ---------------------------------------------------------------------------

# Platforms where a human submits the post into someone else's community. The
# daily limit covers all of them together, not each one separately: the damage
# the limit exists to prevent - the same link appearing everywhere within a day -
# does not care which network it happened on. Hacker News belongs in this list for
# a second reason: a Show HN and a Reddit post on the same morning is the pattern
# people recognise as a launch campaign, and recognising it is what sinks it.
# The config key still says "reddit" because renaming it would silently reset the
# number an existing user chose.
MANUAL_PLATFORMS = ("reddit", "lemmy", "hackernews", "lobsters")


def check_guard(entry: dict, config: dict, history: list[dict]) -> dict:
    """Checks the daily limit and the repeat lock per community."""
    safety = config["safety"]
    now = time.time()
    reasons: list[dict] = []

    today = [h for h in history
             if h.get("platform") in MANUAL_PLATFORMS and now - h.get("ts", 0) < 86400]
    if entry.get("platform") in MANUAL_PLATFORMS and len(today) >= safety["max_reddit_posts_per_day"]:
        reasons.append(i18n.message("guard.daily_limit", count=len(today),
                                    limit=safety["max_reddit_posts_per_day"]))

    previous = [h for h in history if h.get("community_id") == entry["id"]]
    if previous:
        newest = max(h.get("ts", 0) for h in previous)
        days = (now - newest) / 86400
        if days < safety["min_days_between_same_subreddit"]:
            reasons.append(i18n.message(
                "guard.too_soon", days=f"{days:.0f}",
                minimum=safety["min_days_between_same_subreddit"]))

    if entry.get("analysis", {}).get("verdict") == "rot":
        reasons.append(i18n.message("guard.forbidden"))

    return {"allowed": not reasons, "reasons": reasons}


def log_post(slug: str, entry: dict, draft: dict, channel: str, result: str) -> None:
    """Writes the post into THIS product's history. The history is what the safety
    catch counts against - it must never mix with another product's."""
    history = core.load_product(slug, "history", [])
    history.append({
        "ts": int(time.time()),
        "community_id": entry["id"],
        "community": entry["name"],
        "platform": entry.get("platform", "reddit"),
        "channel": channel,
        "angle": draft.get("angle"),
        "title": draft.get("title"),
        "result": result,
    })
    core.save_product(slug, "history", history)
