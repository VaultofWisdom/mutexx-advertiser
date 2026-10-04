"""
Official Reddit API access, read-only.

Reddit closed the old public .json endpoints in 2023 - they answer programs with 403.
The intended route is your own, freely registered app. This module uses the
"application-only" flow: the app identifies itself with its own credentials, without
you signing in with your account. It reads and nothing else - this module cannot post.

Registration (once, about two minutes):
  1. https://www.reddit.com/prefs/apps  ->  at the very bottom, "create another app..."
  2. Type: "script"
  3. name: MutexxAdvertiser
     redirect uri: http://localhost:8777
  4. "create app" -> the ID is printed small UNDER the app name, the secret beside it
  5. Enter both in the app under Settings -> Reddit API
"""

from __future__ import annotations

import base64
import json
import time
import urllib.parse

from . import core, i18n

TOKEN_URL = "https://www.reddit.com/api/v1/access_token"
API = "https://oauth.reddit.com"

_token: dict = {"value": "", "expires": 0.0, "key": ""}


class RedditAuthError(Exception):
    """Carries a catalogue message, so the reason reaches the interface in the
    reader's language. str() gives the English sentence for logs."""

    def __init__(self, message: dict) -> None:
        super().__init__(i18n.render(message))
        self.message = message


NO_CREDENTIALS = i18n.message("reddit.no_credentials")


def _credentials(config: dict) -> tuple[str, str, str, str]:
    reddit = config.get("reddit", {})
    return ((reddit.get("client_id") or "").strip(),
            (reddit.get("client_secret") or "").strip(),
            (reddit.get("bot_username") or "").strip(),
            (reddit.get("bot_password") or "").strip())


def has_credentials(config: dict) -> bool:
    return bool(_credentials(config)[0])


def _request_token(config: dict, form: dict, basic: str) -> tuple[int, str]:
    status, raw = core.fetch(
        TOKEN_URL,
        user_agent=config["user_agent"],
        method="POST",
        data=urllib.parse.urlencode(form).encode(),
        headers={"Authorization": f"Basic {basic}",
                 "Content-Type": "application/x-www-form-urlencoded"},
        retries=2,
    )
    return status, raw.decode("utf-8", "replace")


def get_token(config: dict) -> str:
    """
    Holt ein Zugangstoken. Zwei Verfahren, in dieser Reihenfolge:

      1. password  - wenn ein Bot-Konto hinterlegt ist. Das ist der Weg, den Reddit
                     fuer Apps vom Typ "script" vorsieht. Das Konto muss bei der App
                     unter prefs/apps als Developer eingetragen sein.
      2. client_credentials - App-only, ohne Konto. Funktioniert bei aelteren
                     Registrierungen; bei neuen Apps antwortet Reddit oft mit 401.
    """
    client_id, client_secret, bot_user, bot_pass = _credentials(config)
    if not client_id:
        raise RedditAuthError(NO_CREDENTIALS)

    cache_key = f"{client_id}:{len(client_secret)}:{bot_user}"
    if _token["value"] and _token["expires"] > time.time() + 60 and _token["key"] == cache_key:
        return _token["value"]

    basic = base64.b64encode(f"{client_id}:{client_secret}".encode()).decode()

    attempts: list[tuple[str, dict]] = []
    if bot_user and bot_pass:
        attempts.append(("password", {"grant_type": "password",
                                      "username": bot_user, "password": bot_pass}))
    if client_secret:
        attempts.append(("client_credentials", {"grant_type": "client_credentials"}))
    else:
        attempts.append(("installed_client",
                         {"grant_type": "https://oauth.reddit.com/grants/installed_client",
                          "device_id": "DO_NOT_TRACK_THIS_DEVICE"}))

    errors: list[str] = []
    for label, form in attempts:
        status, body = _request_token(config, form, basic)
        if status == 200:
            try:
                payload = json.loads(body)
            except json.JSONDecodeError as error:
                errors.append(f"{label}: unlesbare Antwort ({error})")
                continue
            token = payload.get("access_token")
            if not token:
                errors.append(f"{label}: no token in the response ({body[:120]})")
                continue
            _token.update({"value": token,
                           "expires": time.time() + float(payload.get("expires_in", 3600)),
                           "key": cache_key, "mode": label})
            return token
        errors.append(f"{label}: HTTP {status} {body[:120]}")

    key = "reddit.no_token"
    if any("401" in e for e in errors):
        key = "reddit.no_token_check" if bot_user else "reddit.no_token_need_bot"
    raise RedditAuthError(i18n.message(key, details=" | ".join(errors)))


def get(config: dict, path: str, params: dict | None = None) -> dict | None:
    """One GET against the Reddit API. Returns None when the source does not exist."""
    token = get_token(config)
    url = API + path
    if params:
        url += "?" + urllib.parse.urlencode(params)

    status, raw = core.fetch(
        url,
        user_agent=config["user_agent"],
        headers={"Authorization": f"bearer {token}"},
        retries=3,
    )
    if status in (403, 404, 451):
        return None
    if status == 401:
        # Token expired or revoked - fetch a new one, once.
        _token.update({"value": "", "expires": 0.0})
        token = get_token(config)
        status, raw = core.fetch(url, user_agent=config["user_agent"],
                                 headers={"Authorization": f"bearer {token}"}, retries=2)
        if status != 200:
            return None
    if status != 200:
        return None
    try:
        return json.loads(raw.decode("utf-8", "replace"))
    except json.JSONDecodeError:
        return None


def check(config: dict) -> dict:
    """Connection test for the Settings page."""
    try:
        get_token(config)
    except RedditAuthError as error:
        return {"ok": False, "detail": error.message}
    payload = get(config, "/r/test/about")
    if not payload:
        return {"ok": False, "detail": i18n.message("reddit.no_read_access")}
    return {"ok": True,
            "detail": i18n.message("reddit.connected", mode=_token.get("mode", "?"))}
