"""
Offizieller Reddit-API-Zugang (nur lesend).

Reddit hat die alten oeffentlichen .json-Endpunkte 2023 dichtgemacht - sie
antworten fuer Programme mit 403. Der vorgesehene Weg ist eine eigene, kostenlos
registrierte App. Wir nutzen das "application-only"-Verfahren: die App weist sich
mit ihren eigenen Zugangsdaten aus, ohne dass du dich mit deinem Konto anmeldest.
Es wird ausschliesslich gelesen - dieses Modul kann nichts posten.

Registrierung (einmalig, ca. 2 Minuten):
  1. https://www.reddit.com/prefs/apps  ->  ganz unten "create another app..."
  2. Typ: "script"
  3. name: MutexxAdvertiser
     redirect uri: http://localhost:8777
  4. "create app" -> die ID steht klein UNTER dem App-Namen, das "secret" daneben
  5. Beides in der App unter Einstellungen -> Reddit-API eintragen
"""

from __future__ import annotations

import base64
import json
import time
import urllib.parse

from . import core

TOKEN_URL = "https://www.reddit.com/api/v1/access_token"
API = "https://oauth.reddit.com"

_token: dict = {"value": "", "expires": 0.0, "key": ""}


class RedditAuthError(Exception):
    pass


NO_CREDENTIALS = (
    "Kein Reddit-API-Zugang hinterlegt. Reddit beantwortet Anfragen ohne "
    "registrierte App seit 2023 mit 403. Lege unter https://www.reddit.com/prefs/apps "
    "eine kostenlose App vom Typ 'script' an und trage Client-ID und Secret in den "
    "Einstellungen ein. Dauert zwei Minuten und ist der von Reddit vorgesehene Weg."
)


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
                errors.append(f"{label}: kein Token in der Antwort ({body[:120]})")
                continue
            _token.update({"value": token,
                           "expires": time.time() + float(payload.get("expires_in", 3600)),
                           "key": cache_key, "mode": label})
            return token
        errors.append(f"{label}: HTTP {status} {body[:120]}")

    hint = ""
    if any("401" in e for e in errors):
        if not bot_user:
            hint = (" Reddit verlangt fuer Script-Apps inzwischen meist ein eigenes Bot-Konto. "
                    "Lege ein separates Reddit-Konto an, trage es bei der App unter prefs/apps "
                    "als Developer ein und hinterlege es hier unter 'Bot-Konto'.")
        else:
            hint = (" Pruefe: Client-ID (steht klein UNTER dem App-Namen), Secret, und ob das "
                    "Bot-Konto bei der App als Developer eingetragen ist. Bei aktiver "
                    "Zwei-Faktor-Anmeldung muss das Passwort als 'passwort:2facode' angegeben werden.")
    raise RedditAuthError("Reddit hat kein Token ausgestellt." + hint + " Details: " + " | ".join(errors))


def get(config: dict, path: str, params: dict | None = None) -> dict | None:
    """Ein GET gegen die Reddit-API. Gibt None zurueck, wenn es die Quelle nicht gibt."""
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
        # Token abgelaufen oder zurueckgezogen - einmal neu holen.
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
    """Verbindungstest fuer die Einstellungen-Seite."""
    try:
        get_token(config)
    except RedditAuthError as error:
        return {"ok": False, "detail": str(error)}
    payload = get(config, "/r/test/about")
    if not payload:
        return {"ok": False, "detail": "Token erhalten, aber kein Lesezugriff. Bitte App-Typ 'script' pruefen."}
    return {"ok": True,
            "detail": f"Verbindung zur Reddit-API steht (Verfahren: {_token.get('mode', 'unbekannt')})."}
