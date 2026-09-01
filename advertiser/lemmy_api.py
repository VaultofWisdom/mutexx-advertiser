"""
Lemmy access, read-only.

Lemmy is the answer to the gap Reddit left behind. The API is open: no app
registration, no key, no approval, no account. Anyone may read, and the network
says so itself - every instance publishes its own terms under /api/*/site.

Two properties matter for the scan:

  * Federation. An instance knows not only its own communities but every one it
    has ever federated with. A search on one large instance therefore returns a
    large part of the network, which is why a handful of seed instances is
    enough and a crawl over hundreds is not needed.

  * Version drift. Lemmy 1.0 moved the API from /api/v3 to /api/v4, and both
    versions are live in the wild at the same time. _api_base probes once per
    instance and remembers what answered - so an instance that has not upgraded
    yet stays usable.

This module reads and nothing else. There is no write path in it, on purpose:
the same rule applies here as everywhere in this app - other people's
communities get a prepared draft, not an automatic post.
"""

from __future__ import annotations

import urllib.parse

from . import core

# Instances the search starts from. Large and well federated, plus two
# German-speaking ones - a German product needs to find German communities.
DEFAULT_INSTANCES = [
    "lemmy.world",
    "lemmy.ml",
    "programming.dev",
    "sh.itjust.works",
    "lemm.ee",
    "feddit.org",
    "discuss.tchncs.de",
]

# Probed once per instance: which API version answered. "" means unreachable.
_api_versions: dict[str, str] = {}

_VERSIONS = ("v4", "v3")


class LemmyError(Exception):
    pass


def normalise_instance(value: str) -> str:
    """'https://Lemmy.World/' and 'lemmy.world' are the same instance."""
    text = (value or "").strip().lower()
    if not text:
        return ""
    if "//" in text:
        text = urllib.parse.urlparse(text).netloc or text.split("//", 1)[1]
    return text.strip("/").split("/")[0].removeprefix("www.")


def forget_versions() -> None:
    """Drop the probe cache - used by the tests and after a settings change."""
    _api_versions.clear()


def _request(instance: str, version: str, path: str, params: dict, ua: str):
    url = f"https://{instance}/api/{version}/{path.lstrip('/')}"
    if params:
        url += "?" + urllib.parse.urlencode(params)
    return core.fetch_json(url, user_agent=ua, retries=2, timeout=20)


def _api_base(instance: str, ua: str) -> str:
    """Probe the API version once per instance. Returns '' if nothing answered."""
    if instance in _api_versions:
        return _api_versions[instance]
    for version in _VERSIONS:
        try:
            _request(instance, version, "site", {}, ua)
        except (core.HttpError, OSError):
            continue
        _api_versions[instance] = version
        return version
    _api_versions[instance] = ""
    return ""


def get(instance: str, path: str, params: dict, ua: str) -> dict | None:
    """One read. Returns None instead of raising - an instance that is down must
    not take the whole scan with it."""
    version = _api_base(instance, ua)
    if not version:
        return None
    try:
        payload = _request(instance, version, path, params, ua)
    except (core.HttpError, OSError):
        return None
    return payload if isinstance(payload, dict) else None


def check(instance: str, ua: str) -> dict:
    """Settings -> Test connection. Reports what the instance is and whether it
    answers at all."""
    host = normalise_instance(instance)
    if not host:
        return {"ok": False, "instance": "", "reason": "empty"}
    forget_versions()
    payload = get(host, "site", {}, ua)
    if not payload:
        return {"ok": False, "instance": host, "reason": "unreachable"}
    site = (payload.get("site_view") or {}).get("site") or {}
    return {
        "ok": True,
        "instance": host,
        "api": _api_versions.get(host, ""),
        "title": site.get("name") or host,
        "users": int(((payload.get("site_view") or {}).get("counts") or {}).get("users") or 0),
    }


def _community_views(payload: dict) -> list[dict]:
    """v3 and v4 both answer with a list of community views, but not always under
    the same key."""
    for key in ("communities", "results"):
        value = payload.get(key)
        if isinstance(value, list):
            return [item for item in value if isinstance(item, dict)]
    return []


def search_communities(instance: str, query: str, ua: str, limit: int = 40) -> list[dict]:
    payload = get(instance, "search", {
        "q": query,
        "type_": "Communities",
        "listing_type": "All",
        "sort": "TopAll",
        "limit": max(1, min(limit, 50)),
    }, ua)
    if not payload:
        return []
    return _community_views(payload)


def community(instance: str, name: str, ua: str) -> dict | None:
    """name is 'community@home-instance' or a plain local name."""
    payload = get(instance, "community", {"name": name}, ua)
    if not payload:
        return None
    view = payload.get("community_view")
    return view if isinstance(view, dict) else None


def posts(instance: str, name: str, ua: str, limit: int = 50) -> list[dict]:
    payload = get(instance, "post/list", {
        "community_name": name,
        "sort": "New",
        "limit": max(1, min(limit, 50)),
    }, ua)
    if not payload:
        return []
    for key in ("posts", "results"):
        value = payload.get(key)
        if isinstance(value, list):
            return [item for item in value if isinstance(item, dict)]
    return []


def site_rules(instance: str, ua: str) -> dict[str, str]:
    """Instance-level terms. A community may permit what its instance forbids -
    then the instance wins, and this is where that text comes from."""
    payload = get(instance, "site", {}, ua)
    if not payload:
        return {}
    site = (payload.get("site_view") or {}).get("site") or {}
    texts = {}
    for field, source in (("description", "Instance description"),
                          ("sidebar", "Instance sidebar"),
                          ("legal_information", "Instance terms")):
        text = site.get(field)
        if isinstance(text, str) and text.strip():
            texts[source] = text[:8000]
    return texts


def handle_of(view: dict) -> tuple[str, str]:
    """('community@instance', 'https://instance/c/community') from a community view."""
    data = view.get("community") or {}
    name = str(data.get("name") or "").strip()
    actor = str(data.get("actor_id") or "").strip()
    if not name:
        return "", ""
    home = normalise_instance(actor) if actor else ""
    if not home:
        return name, ""
    return f"{name}@{home}", actor or f"https://{home}/c/{name}"
