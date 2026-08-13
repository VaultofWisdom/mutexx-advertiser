"""
Vault Outreach Navigator - Kern: HTTP-Client, Rate-Limiting, Konfiguration, Speicher.

Bewusst OHNE externe Abhaengigkeiten (nur Python-Standardbibliothek), damit die App
ohne pip-Installation laeuft und in Jahren noch startet.
"""

from __future__ import annotations

import gzip
import io
import json
import os
import threading
import time
import urllib.error
import urllib.parse
import urllib.request
from typing import Any

# ---------------------------------------------------------------------------
# Pfade
# ---------------------------------------------------------------------------

APP_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(APP_DIR, "data")
CONFIG_PATH = os.path.join(APP_DIR, "config.json")

os.makedirs(DATA_DIR, exist_ok=True)


# ---------------------------------------------------------------------------
# Konfiguration
# ---------------------------------------------------------------------------

DEFAULT_CONFIG: dict[str, Any] = {
    # Dein Produkt. Diese Angaben landen in jedem Entwurf.
    "site": {
        "name": "Mein Produkt",
        "url": "https://example.com",
        "version": "1.0",
        "one_liner": "Kurzbeschreibung deines Produkts in einem Satz.",
        "reddit_username": "",
    },
    # Wie sich die App im Netz identifiziert. Ehrliche Kennung ist Pflicht -
    # gefaelschte Browser-User-Agents sind bei Reddit ein Regelverstoss.
    "user_agent": "MutexxAdvertiser/0.1 (Recherche-Tool; Kontakt: bitte-eigene-adresse-eintragen)",
    "request_delay_seconds": 1.3,
    "discovery": {
        "max_communities": 140,
        "deep_scan_top_n": 70,
        "min_subscribers": 400,
        "keywords": [
            "demonolatry", "demonology", "goetia", "ars goetia", "grimoire",
            "sigil", "occult", "esoteric", "esotericism", "luciferian",
            "satanism", "left hand path", "witchcraft", "spirit work",
            "ceremonial magic", "chaos magick", "theistic satanism",
            "solomonic", "daemon", "infernal",
        ],
    },
    # Kanaele, in denen die App VOLLAUTOMATISCH posten darf.
    # Nur eigene / ausdruecklich erlaubte Kanaele - siehe README.
    "auto_channels": {
        "discord_webhooks": [],
        "mastodon": {"instance": "", "access_token": ""},
    },
    # Reddit-API (nur lesend). Kostenlos unter reddit.com/prefs/apps registrieren -
    # ohne das antwortet Reddit auf Programmanfragen grundsaetzlich mit 403.
    # bot_username/bot_password nur ausfuellen, wenn Reddit das client_credentials-
    # Verfahren ablehnt. Die Daten bleiben lokal in dieser Datei.
    "reddit": {"client_id": "", "client_secret": "", "bot_username": "", "bot_password": ""},
    # Optional: echte KI-Entwuerfe statt Vorlagen.
    "anthropic": {"api_key": "", "model": "claude-opus-5"},
    "safety": {
        # Harte Bremse: nie mehr als N manuelle Reddit-Posts pro Tag vorschlagen.
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


def load_config() -> dict:
    if os.path.exists(CONFIG_PATH):
        try:
            with open(CONFIG_PATH, "r", encoding="utf-8") as handle:
                return _deep_merge(DEFAULT_CONFIG, json.load(handle))
        except (json.JSONDecodeError, OSError):
            pass
    save_config(DEFAULT_CONFIG)
    return json.loads(json.dumps(DEFAULT_CONFIG))


def save_config(config: dict) -> None:
    with open(CONFIG_PATH, "w", encoding="utf-8") as handle:
        json.dump(config, handle, indent=2, ensure_ascii=False)


# ---------------------------------------------------------------------------
# Speicher (schlichte JSON-Dateien, damit alles nachvollziehbar bleibt)
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
    with _store_lock:
        tmp = store_path(name) + ".tmp"
        with open(tmp, "w", encoding="utf-8") as handle:
            json.dump(payload, handle, indent=2, ensure_ascii=False)
        os.replace(tmp, store_path(name))


# ---------------------------------------------------------------------------
# HTTP mit Rate-Limit, Backoff und ehrlicher Kennung
# ---------------------------------------------------------------------------

class RateLimiter:
    """Serialisiert alle ausgehenden Requests pro Host mit fester Mindestpause."""

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
    """Ein HTTP-Request mit Rate-Limit und Backoff. Gibt (status, body) zurueck."""
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
                # Fehlerantworten kommen ebenfalls gzip-komprimiert - sonst steht
                # in der Meldung nur Zeichensalat statt des echten Grundes.
                if error.headers.get("Content-Encoding") == "gzip" and body:
                    body = gzip.GzipFile(fileobj=io.BytesIO(body)).read()
            except Exception:  # noqa: BLE001 - Fehlerkoerper ist optional
                pass
            # 429/5xx: hoeflich warten und erneut versuchen. 403/404: sofort aufgeben.
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
    raise HttpError(0, f"Netzwerkfehler bei {url}: {last_error}")


def fetch_json(url: str, *, user_agent: str, **kwargs: Any) -> Any:
    status, body = fetch(url, user_agent=user_agent, **kwargs)
    if status != 200:
        raise HttpError(status, url)
    try:
        return json.loads(body.decode("utf-8", "replace"))
    except json.JSONDecodeError as error:
        raise HttpError(status, f"Keine gueltige JSON-Antwort von {url}: {error}") from error


def post_json(url: str, payload: dict, *, user_agent: str, headers: dict[str, str] | None = None) -> tuple[int, str]:
    body = json.dumps(payload).encode("utf-8")
    all_headers = {"Content-Type": "application/json"}
    if headers:
        all_headers.update(headers)
    status, raw = fetch(url, user_agent=user_agent, method="POST", data=body, headers=all_headers, retries=2)
    return status, raw.decode("utf-8", "replace")
