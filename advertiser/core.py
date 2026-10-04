"""
Mutexx Advertiser core: HTTP client, rate limiting, configuration, storage.

Deliberately WITHOUT external dependencies - the standard library only - so the app
runs with no pip install and still starts years from now.
"""

from __future__ import annotations

import gzip
import io
import json
import re
import os
import threading
import time
import urllib.error
import urllib.parse
import urllib.request
from typing import Any

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

APP_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _home() -> str:
    """Where configuration and data live.

    Two layouts, chosen so neither existing users nor installed copies break:

    * Portable - next to the app. Used when the app folder already holds a
      config.json (every copy run from source before 0.4) or a file named
      "portable" (a deliberately portable copy on a USB stick).
    * Installed - the per-user data folder, %LOCALAPPDATA%\\Mutexx Production\\
      Mutexx Advertiser on Windows. An app under C:\\Program Files cannot write
      next to itself, and credentials belong to the user, not to the machine.

    MUTEXX_ADVERTISER_HOME overrides both.
    """
    override = os.environ.get("MUTEXX_ADVERTISER_HOME", "").strip()
    if override:
        return override
    if (os.path.exists(os.path.join(APP_DIR, "config.json"))
            or os.path.exists(os.path.join(APP_DIR, "portable"))):
        return APP_DIR
    if os.name == "nt" and os.environ.get("LOCALAPPDATA"):
        return os.path.join(os.environ["LOCALAPPDATA"], "Mutexx Production",
                            "Mutexx Advertiser")
    base = os.environ.get("XDG_DATA_HOME") or os.path.join(
        os.path.expanduser("~"), ".local", "share")
    return os.path.join(base, "mutexx-advertiser")


HOME_DIR = _home()
DATA_DIR = os.path.join(HOME_DIR, "data")
PRODUCTS_DIR = os.path.join(DATA_DIR, "products")
CONFIG_PATH = os.path.join(HOME_DIR, "config.json")

os.makedirs(DATA_DIR, exist_ok=True)


# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

DEFAULT_CONFIG: dict[str, Any] = {
    # Configuration version. Drives the one-off migration into product profiles.
    "schema_version": 0,
    # Your products. Every profile gets its own data folder; everything analysis,
    # strategy and drafts need lives there - see products.py.
    "products": [],
    "active_product": "",
    # Interface language. English by default; the switch lives in Settings.
    "ui_language": "en",
    # Deprecated: the old single-product configuration. Carried into a profile on
    # first start and never read again.
    "site": {
        "name": "Mein Produkt",
        "url": "https://example.com",
        "version": "1.0",
        "one_liner": "Kurzbeschreibung deines Produkts in einem Satz.",
        "reddit_username": "",
    },
    # How the app identifies itself on the network. An honest identifier is required -
    # faking a browser user agent breaks Reddit's rules.
    "user_agent": "MutexxAdvertiser/0.4 (research tool; contact: please-enter-your-own-address)",
    "request_delay_seconds": 1.3,
    # Limits of the scan. The keywords are NOT here but on the product - they come
    # from its profile and from the analysis (see analysis.merged_keywords).
    "discovery": {
        "max_communities": 140,
        "deep_scan_top_n": 70,
        "min_subscribers": 400,
        # Lemmy is a far smaller network. The same floor would filter out
        # practically everything there - including the specialist communities
        # that are the whole point of going.
        "lemmy_min_subscribers": 40,
    },
    # Channels the app may post to FULLY AUTOMATICALLY.
    # Only channels you own or where it is explicitly allowed - see the README.
    "auto_channels": {
        "discord_webhooks": [],
        "mastodon": {"instance": "", "access_token": ""},
    },
    # Reddit API (read-only). Register for free at reddit.com/prefs/apps - without
    # that, Reddit answers programmatic requests with 403 as a matter of course.
    # Fill in bot_username/bot_password only if Reddit rejects the client_credentials
    # flow. The data stays local in this file.
    "reddit": {"client_id": "", "client_secret": "", "bot_username": "", "bot_password": ""},
    # Optional: real AI drafts instead of templates.
    "anthropic": {"api_key": "", "model": "claude-opus-5-5"},
    "safety": {
        # Hard brake: never propose more than N manual Reddit posts per day.
        "max_reddit_posts_per_day": 1,
        "min_days_between_same_subreddit": 45,
    },
}


def _deep_merge(base: dict, override: dict) -> dict:
    out = dict(base)
    for key, value in override.items():
        if isinstance(value, dict) and isinstance(out.get(key), dict):
            out[key] = _deep_merge(out[key], value)
        else:
            out[key] = value
    return out


# Configuration changes that must run exactly once. products.py registers itself
# here - core must not import products (circular import).
_MIGRATIONS: list[Any] = []


def register_migration(func: Any) -> None:
    if func not in _MIGRATIONS:
        _MIGRATIONS.append(func)


def _apply_migrations(config: dict) -> bool:
    return any([bool(migration(config)) for migration in _MIGRATIONS])


def load_config() -> dict:
    config = json.loads(json.dumps(DEFAULT_CONFIG))
    if os.path.exists(CONFIG_PATH):
        try:
            with open(CONFIG_PATH, "r", encoding="utf-8") as handle:
                config = _deep_merge(DEFAULT_CONFIG, json.load(handle))
        except (json.JSONDecodeError, OSError):
            pass
    if _apply_migrations(config):
        save_config(config)
    elif not os.path.exists(CONFIG_PATH):
        save_config(config)
    return config


def save_config(config: dict) -> None:
    with open(CONFIG_PATH, "w", encoding="utf-8") as handle:
        json.dump(config, handle, indent=2, ensure_ascii=False)


# ---------------------------------------------------------------------------
# Storage - plain JSON files, so everything stays inspectable
# ---------------------------------------------------------------------------

_store_lock = threading.Lock()


def store_path(name: str) -> str:
    return os.path.join(DATA_DIR, f"{name}.json")


def load(name: str, default: Any) -> Any:
    path = store_path(name)
    if not os.path.exists(path):
        return json.loads(json.dumps(default))
    try:
        with open(path, "r", encoding="utf-8") as handle:
            return json.load(handle)
    except (json.JSONDecodeError, OSError):
        return json.loads(json.dumps(default))


def save(name: str, payload: Any) -> None:
    _write_json(store_path(name), payload)


def _write_json(path: str, payload: Any) -> None:
    with _store_lock:
        os.makedirs(os.path.dirname(path), exist_ok=True)
        tmp = path + ".tmp"
        with open(tmp, "w", encoding="utf-8") as handle:
            json.dump(payload, handle, indent=2, ensure_ascii=False)
        os.replace(tmp, path)


# -- Per-product storage ---------------------------------------------------
# Every product gets its own folder. Without that separation the safety catch counts
# one product's posts against the other product's daily limit.

def product_store_path(slug: str, name: str) -> str:
    return os.path.join(PRODUCTS_DIR, slug or "_ohne-produkt", f"{name}.json")


def load_product(slug: str, name: str, default: Any) -> Any:
    path = product_store_path(slug, name)
    if not os.path.exists(path):
        return json.loads(json.dumps(default))
    try:
        with open(path, "r", encoding="utf-8") as handle:
            return json.load(handle)
    except (json.JSONDecodeError, OSError):
        return json.loads(json.dumps(default))


def save_product(slug: str, name: str, payload: Any) -> None:
    _write_json(product_store_path(slug, name), payload)


def forget_product(slug: str) -> None:
    """Deletes a product's data folder. products.py clears the configuration."""
    folder = os.path.join(PRODUCTS_DIR, slug or "_ohne-produkt")
    if not slug or not os.path.isdir(folder):
        return
    for entry in os.listdir(folder):
        if entry.endswith(".json") or entry.endswith(".json.tmp"):
            os.remove(os.path.join(folder, entry))
    try:
        os.rmdir(folder)
    except OSError:
        pass


# ---------------------------------------------------------------------------
# HTTP with rate limiting, backoff and an honest identifier
# ---------------------------------------------------------------------------

class RateLimiter:
    """Serialises all outgoing requests per host with a fixed minimum pause."""

    def __init__(self, delay: float) -> None:
        self.delay = delay
        self._lock = threading.Lock()
        self._last: dict[str, float] = {}

    def wait(self, host: str) -> None:
        with self._lock:
            now = time.monotonic()
            earliest = self._last.get(host, 0.0) + self.delay
            if now < earliest:
                time.sleep(earliest - now)
            self._last[host] = time.monotonic()


_limiter = RateLimiter(DEFAULT_CONFIG["request_delay_seconds"])


def set_delay(seconds: float) -> None:
    _limiter.delay = max(0.5, float(seconds))


class HttpError(Exception):
    def __init__(self, status: int, message: str) -> None:
        super().__init__(f"HTTP {status}: {message}")
        self.status = status


def fetch(
    url: str,
    *,
    user_agent: str,
    method: str = "GET",
    data: bytes | None = None,
    headers: dict[str, str] | None = None,
    timeout: int = 25,
    retries: int = 3,
) -> tuple[int, bytes]:
    """One HTTP request with rate limiting and backoff. Returns (status, body)."""
    host = urllib.parse.urlparse(url).netloc
    base_headers = {
        "User-Agent": user_agent,
        "Accept-Encoding": "gzip",
        "Accept": "application/json, text/html;q=0.8, */*;q=0.5",
    }
    if headers:
        base_headers.update(headers)

    last_error: Exception | None = None
    for attempt in range(retries):
        _limiter.wait(host)
        request = urllib.request.Request(url, data=data, headers=base_headers, method=method)
        try:
            with urllib.request.urlopen(request, timeout=timeout) as response:
                raw = response.read()
                if response.headers.get("Content-Encoding") == "gzip":
                    raw = gzip.GzipFile(fileobj=io.BytesIO(raw)).read()
                return response.status, raw
        except urllib.error.HTTPError as error:
            body = b""
            try:
                body = error.read()
                # Error responses come gzipped too - otherwise the message is
                # nothing but mojibake instead of the actual reason.
                if error.headers.get("Content-Encoding") == "gzip" and body:
                    body = gzip.GzipFile(fileobj=io.BytesIO(body)).read()
            except Exception:  # noqa: BLE001 - the error body is optional
                pass
            # 429/5xx: wait politely and retry. 403/404: give up immediately.
            if error.code in (429, 500, 502, 503, 504) and attempt < retries - 1:
                time.sleep(min(30, 2 ** (attempt + 2)))
                last_error = error
                continue
            return error.code, body
        except (urllib.error.URLError, TimeoutError, OSError) as error:
            last_error = error
            if attempt < retries - 1:
                time.sleep(2 ** (attempt + 1))
                continue
    raise HttpError(0, f"Network error for {url}: {last_error}")


def fetch_json(url: str, *, user_agent: str, **kwargs: Any) -> Any:
    status, body = fetch(url, user_agent=user_agent, **kwargs)
    if status != 200:
        raise HttpError(status, url)
    try:
        return json.loads(body.decode("utf-8", "replace"))
    except json.JSONDecodeError as error:
        raise HttpError(status, f"No valid JSON response from {url}: {error}") from error




def post_json(url: str, payload: dict, *, user_agent: str, headers: dict[str, str] | None = None,
              timeout: int = 25) -> tuple[int, str]:
    body = json.dumps(payload).encode("utf-8")
    all_headers = {"Content-Type": "application/json"}
    if headers:
        all_headers.update(headers)
    status, raw = fetch(url, user_agent=user_agent, method="POST", data=body,
                        headers=all_headers, timeout=timeout, retries=2)
    return status, raw.decode("utf-8", "replace")


# ---------------------------------------------------------------------------
# Claude - the one place every module talks to the Anthropic API through
# ---------------------------------------------------------------------------

DEFAULT_MODEL = "claude-opus-5-5"

# Models that accept the server-side refusal fallback. On these a declined request
# is re-run on Anthropic's recommended substitute inside the same call instead of
# coming back empty. Any other model gets the plain request - sending the
# parameter to a model that does not know it would turn every call into a 400.
_FALLBACK_MODELS = {"claude-opus-5-5", "claude-opus-5", "claude-fable-5-1", "claude-sonnet-5-5"}


class ClaudeError(ValueError):
    """The API answered, but not with something usable. Carries a catalogue key."""

    def __init__(self, key: str, **params: Any) -> None:
        from . import i18n  # late: i18n is pure data, but keep core import-light
        super().__init__(i18n.t(key, **params))
        self.key = key
        self.params = params


def ask_claude_json(config: dict, system: str, prompt: str, *,
                    max_tokens: int = 16000) -> dict:
    """One request, one JSON object back.

    Raw HTTP rather than the SDK on purpose: the app's promise is that it runs on the
    standard library alone. Everything that has to be right about the request lives
    here, so five modules cannot drift apart again:

    * the model comes from Settings and defaults to the current Opus;
    * the budget is generous - current models think before they answer, and that
      thinking is drawn from max_tokens, so a tight limit cuts the JSON in half;
    * the timeout is minutes, not the 25 seconds a forum page gets;
    * a refusal is reported as one, instead of as "no JSON found".
    """
    api = config.get("anthropic") or {}
    key = (api.get("api_key") or "").strip()
    if not key:
        raise ClaudeError("error.no_api_key")
    model = (api.get("model") or "").strip() or DEFAULT_MODEL

    payload: dict[str, Any] = {
        "model": model,
        "max_tokens": max_tokens,
        "system": system,
        "messages": [{"role": "user", "content": prompt}],
    }
    headers = {"x-api-key": key, "anthropic-version": "2023-06-01"}
    if model in _FALLBACK_MODELS:
        payload["fallbacks"] = "default"
        headers["anthropic-beta"] = "server-side-fallback-2026-07-01"

    status, raw = post_json("https://api.anthropic.com/v1/messages", payload,
                            user_agent=config.get("user_agent", "MutexxAdvertiser"),
                            headers=headers, timeout=300)
    if status != 200:
        raise ClaudeError("error.api_status", status=status, detail=raw[:300])

    response = json.loads(raw)
    if response.get("stop_reason") == "refusal":
        raise ClaudeError("error.api_refused")
    text = "".join(block.get("text", "") for block in response.get("content", [])
                   if block.get("type") == "text")
    match = re.search(r"\{.*\}", text, re.S)
    if not match:
        if response.get("stop_reason") == "max_tokens":
            raise ClaudeError("error.api_truncated")
        raise ClaudeError("error.no_json")
    try:
        return json.loads(match.group(0))
    except json.JSONDecodeError as error:
        raise ClaudeError("error.no_json") from error
