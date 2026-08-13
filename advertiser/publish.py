"""
Veroeffentlichen.

Zwei streng getrennte Wege:

1. VOLLAUTOMATISCH - nur in Kanaelen, die dir selbst gehoeren oder in denen
   Bot-Posts ausdruecklich erlaubt sind: eigene Discord-Server (Webhook),
   eigener Mastodon-Account. Diese Posts gehen ohne Rueckfrage raus.

2. EIN-KLICK-ASSISTENT - fuer fremde Communities (Reddit, fremde Foren).
   Die App baut den fertigen, vorausgefuellten Beitrag und oeffnet das
   Formular; abschicken tut ein Mensch. Das ist Absicht, kein fehlendes
   Feature: automatisiertes Verteilen desselben Links ueber fremde Subreddits
   ist Spam nach Reddits Regeln und fuehrt zur Sperre der Domain
   vaultofdemons.com - inklusive der Links, die andere freiwillig setzen.
"""

from __future__ import annotations

import time
import urllib.parse

from . import core


# ---------------------------------------------------------------------------
# Weg 1: eigene Kanaele - echtes Autoposting
# ---------------------------------------------------------------------------

def post_discord_webhook(webhook_url: str, draft: dict, config: dict) -> dict:
    """Postet in einen EIGENEN Discord-Server. Webhooks funktionieren nur dort,
    wo jemand mit Serverrechten sie eingerichtet hat - deshalb sicher."""
    site = config["site"]
    content = f"**{draft['title']}**\n\n{draft['body']}"
    if len(content) > 1900:
        content = content[:1890] + " ..."
    payload = {
        "content": content,
        "username": site["name"],
        "allowed_mentions": {"parse": []},
    }
    status, raw = core.post_json(webhook_url, payload, user_agent=config["user_agent"])
    ok = status in (200, 204)
    return {"ok": ok, "status": status, "detail": "" if ok else raw[:400]}


def post_mastodon(config: dict, draft: dict) -> dict:
    """Postet auf dem EIGENEN Mastodon-Account (Token aus den Einstellungen)."""
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


def run_auto_channels(config: dict, draft: dict) -> list[dict]:
    """Verteilt einen Entwurf an alle konfigurierten eigenen Kanaele."""
    results: list[dict] = []
    for hook in config["auto_channels"].get("discord_webhooks", []):
        url = hook.get("url") if isinstance(hook, dict) else hook
        label = hook.get("name", "Discord") if isinstance(hook, dict) else "Discord"
        if not url:
            continue
        result = post_discord_webhook(url, draft, config)
        result.update({"channel": label, "kind": "discord"})
        results.append(result)

    mastodon = config["auto_channels"].get("mastodon", {})
    if mastodon.get("instance") and mastodon.get("access_token"):
        result = post_mastodon(config, draft)
        result.update({"channel": mastodon["instance"], "kind": "mastodon"})
        results.append(result)

    return results


# ---------------------------------------------------------------------------
# Weg 2: Ein-Klick-Assistent fuer fremde Communities
# ---------------------------------------------------------------------------

def reddit_submit_url(subreddit: str, draft: dict) -> str:
    """Vorausgefuelltes Reddit-Formular. Der Mensch klickt 'Post'."""
    query = urllib.parse.urlencode({"title": draft["title"], "text": draft["body"]})
    return f"https://www.reddit.com/r/{urllib.parse.quote(subreddit)}/submit?selftext=true&{query}"


# ---------------------------------------------------------------------------
# Schutzschalter: verhindert, dass aus Kampagne wieder Spam wird
# ---------------------------------------------------------------------------

def check_guard(entry: dict, config: dict, history: list[dict]) -> dict:
    """Prueft Tageslimit und Wiederholungssperre pro Community."""
    safety = config["safety"]
    now = time.time()
    reasons: list[str] = []

    today = [h for h in history
             if h.get("platform") == "reddit" and now - h.get("ts", 0) < 86400]
    if entry.get("platform") == "reddit" and len(today) >= safety["max_reddit_posts_per_day"]:
        reasons.append(
            f"Tageslimit erreicht: heute wurden bereits {len(today)} Reddit-Beitraege "
            f"gesetzt (Limit {safety['max_reddit_posts_per_day']}). "
            "Mehrere Subreddits am selben Tag ist genau das Muster, das als Spam erkannt wird."
        )

    previous = [h for h in history if h.get("community_id") == entry["id"]]
    if previous:
        newest = max(h.get("ts", 0) for h in previous)
        days = (now - newest) / 86400
        if days < safety["min_days_between_same_subreddit"]:
            reasons.append(
                f"Hier wurde vor {days:.0f} Tagen schon gepostet - Mindestabstand ist "
                f"{safety['min_days_between_same_subreddit']} Tage."
            )

    verdict = entry.get("analysis", {}).get("verdict")
    if verdict == "rot":
        reasons.append("Diese Community verbietet Eigenwerbung ausdruecklich.")

    return {"allowed": not reasons, "reasons": reasons}


def log_post(entry: dict, draft: dict, channel: str, result: str) -> None:
    history = core.load("history", [])
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
    core.save("history", history)
