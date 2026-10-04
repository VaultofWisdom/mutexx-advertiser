"""
Mutexx account: sign-in and an optional sync between devices.

The same backend, the same compartment model and the same sync rules as the
TypeScript SDK every other Mutexx app uses (VaultofWisdom/MutexxAccount) -
re-implemented on the standard library, because the Advertiser's promise is that it
runs without installing anything.

WHAT IS SYNCED, AND WHAT NEVER IS

Synced, in the compartment "advertiser" and only there: product profiles and each
product's working data (seed lists, analysis, strategy, assets, communities, the
prepared campaign, the history). The history matters most - the safety catch counts
against it, and a second device that does not know what went out yesterday would
happily propose the same community again.

Never synced: config.json. It holds the Anthropic key, the Reddit secret, the
Mastodon token and the Discord webhooks, and none of those belong on a server
because they are convenient to have on a second machine.

The account is optional. Without signing in nothing leaves this computer.

HOW THE SYNC DECIDES

Every record carries a server-assigned revision. This device remembers, per record,
the hash and revision it last agreed with the server on (sync_state.json). From that:

  * changed here, not there        -> goes up
  * changed there, not here        -> comes down
  * changed on both sides          -> the server's copy wins, ours is kept in
                                      data/account/conflicts/ - nothing is lost.
                                      The history is the exception: both sides are
                                      merged, because losing an entry would loosen
                                      the safety catch.
  * removed here                   -> a tombstone goes up, so the other devices
                                      remove it too instead of bringing it back.

Payloads above 64 KB go into the storage bucket, as the SDK does.
"""

from __future__ import annotations

import base64
import ctypes
import hashlib
import json
import os
import socket
import threading
import time
import urllib.parse
from typing import Any

from . import core, i18n, products

MUTEXX_URL = "https://gvyvhsipnxbrfeirotvb.supabase.co"
# Public by design: it respects Row Level Security and opens nothing without a
# signed-in user. The same key ships in every Mutexx app.
MUTEXX_PUBLISHABLE_KEY = "sb_publishable_0Fa2ebzqIbJHJ7ERSBVihQ_FMT5wogM"
APP = "advertiser"
BUCKET = "mutexx-sync"
BLOB_THRESHOLD = 64 * 1024
PAGE = 500

# The per-product files that travel. Order matters only for readability.
DATA_FILES = ("seeds", "analysis", "strategy", "assets", "communities", "queue", "history")

_lock = threading.RLock()
_status: dict[str, Any] = {"running": False, "last": None}


class AccountError(Exception):
    """Carries a catalogue message, like every other error that reaches the UI."""

    def __init__(self, message: dict, status: str = "error") -> None:
        super().__init__(i18n.render(message))
        self.message = message
        self.status = status


# ---------------------------------------------------------------------------
# Where things live
# ---------------------------------------------------------------------------

def _folder() -> str:
    path = os.path.join(core.DATA_DIR, "account")
    os.makedirs(path, exist_ok=True)
    return path


def _path(name: str) -> str:
    return os.path.join(_folder(), name)


def _read(name: str, default: Any) -> Any:
    try:
        with open(_path(name), "r", encoding="utf-8") as handle:
            return json.load(handle)
    except (OSError, json.JSONDecodeError):
        return json.loads(json.dumps(default))


def _write(name: str, payload: Any) -> None:
    core._write_json(_path(name), payload)


# ---------------------------------------------------------------------------
# The session, protected at rest
# ---------------------------------------------------------------------------
# A refresh token is as good as the password for as long as it lives. On Windows
# it is encrypted with DPAPI - readable only by this Windows user on this machine,
# so a copied data folder carries no usable session.

class _Blob(ctypes.Structure):
    _fields_ = [("cbData", ctypes.c_ulong), ("pbData", ctypes.POINTER(ctypes.c_char))]


def _dpapi(data: bytes, protect: bool) -> bytes | None:
    if os.name != "nt":
        return None
    try:
        crypt32 = ctypes.windll.crypt32
        kernel32 = ctypes.windll.kernel32
        buffer = ctypes.create_string_buffer(data, len(data))
        source = _Blob(len(data), ctypes.cast(buffer, ctypes.POINTER(ctypes.c_char)))
        target = _Blob()
        function = crypt32.CryptProtectData if protect else crypt32.CryptUnprotectData
        if not function(ctypes.byref(source), None, None, None, None, 0x01, ctypes.byref(target)):
            return None
        try:
            return ctypes.string_at(target.pbData, target.cbData)
        finally:
            kernel32.LocalFree(target.pbData)
    except (AttributeError, OSError):
        return None


def _seal(session: dict) -> dict:
    raw = json.dumps(session).encode("utf-8")
    sealed = _dpapi(raw, protect=True)
    if sealed is not None:
        return {"dpapi": base64.b64encode(sealed).decode("ascii")}
    return {"plain": session}


def _unseal(stored: dict) -> dict | None:
    if not stored:
        return None
    if "plain" in stored:
        return stored["plain"]
    if "dpapi" in stored:
        raw = _dpapi(base64.b64decode(stored["dpapi"]), protect=False)
        if raw is None:
            return None
        try:
            return json.loads(raw.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError):
            return None
    return None


def load_session() -> dict | None:
    return _unseal(_read("session.json", {}))


def _save_session(session: dict | None) -> None:
    if session is None:
        try:
            os.remove(_path("session.json"))
        except OSError:
            pass
        return
    _write("session.json", _seal(session))


# ---------------------------------------------------------------------------
# HTTP against the backend
# ---------------------------------------------------------------------------

def _ua(config: dict | None) -> str:
    return (config or {}).get("user_agent") or "MutexxAdvertiser"


def _call(method: str, path: str, *, config: dict | None = None, token: str = "",
          body: Any = None, headers: dict | None = None, raw: bytes | None = None,
          ) -> tuple[int, Any]:
    all_headers = {"apikey": MUTEXX_PUBLISHABLE_KEY, "Accept": "application/json"}
    if token:
        all_headers["Authorization"] = f"Bearer {token}"
    data = raw
    if body is not None:
        data = json.dumps(body).encode("utf-8")
        all_headers["Content-Type"] = "application/json"
    all_headers.update(headers or {})
    try:
        status, content = core.fetch(MUTEXX_URL + path, user_agent=_ua(config), method=method,
                                     data=data, headers=all_headers, timeout=30, retries=2,
                                     polite=False)
    except core.HttpError as error:
        raise AccountError(i18n.message("account.offline", error=error), "offline") from error
    text = content.decode("utf-8", "replace")
    try:
        parsed = json.loads(text) if text.strip() else None
    except json.JSONDecodeError:
        parsed = text
    return status, parsed


def _reason(payload: Any) -> str:
    if isinstance(payload, dict):
        for field in ("error_description", "msg", "message", "error", "details", "hint"):
            if isinstance(payload.get(field), str) and payload[field].strip():
                return payload[field]
        return json.dumps(payload)[:200]
    return str(payload or "")[:200]


def _check(status: int, payload: Any) -> Any:
    if 200 <= status < 300:
        return payload
    if status in (401, 403):
        raise AccountError(i18n.message("account.unauthorized"), "unauthorized")
    if status >= 500:
        raise AccountError(i18n.message("account.offline", error=f"HTTP {status}"), "offline")
    raise AccountError(i18n.message("account.failed", error=f"HTTP {status}: {_reason(payload)}"))


def _store_tokens(payload: dict, previous: dict | None = None) -> dict:
    user = payload.get("user") or (previous or {}).get("user") or {}
    session = dict(previous or {})
    session.update({
        "access_token": payload["access_token"],
        "refresh_token": payload.get("refresh_token") or session.get("refresh_token", ""),
        "expires_at": time.time() + float(payload.get("expires_in") or 3600),
        "user": {"id": user.get("id", ""), "email": user.get("email", "")},
    })
    _save_session(session)
    return session


def _token(config: dict) -> tuple[str, dict]:
    """A valid access token, refreshed when it is about to run out."""
    session = load_session()
    if not session or not session.get("refresh_token"):
        raise AccountError(i18n.message("account.not_signed_in"), "unauthorized")
    if session.get("expires_at", 0) - 90 > time.time():
        return session["access_token"], session
    status, payload = _call("POST", "/auth/v1/token?grant_type=refresh_token", config=config,
                            body={"refresh_token": session["refresh_token"]})
    if status in (400, 401, 403):
        # A refresh token that is rejected stays rejected - waiting will not help.
        _save_session(None)
        raise AccountError(i18n.message("account.expired"), "unauthorized")
    _check(status, payload)
    session = _store_tokens(payload, session)
    return session["access_token"], session


def _rest(method: str, path: str, config: dict, *, body: Any = None,
          prefer: str = "") -> Any:
    token, _session = _token(config)
    headers = {"Accept-Profile": "mutexx", "Content-Profile": "mutexx"}
    if prefer:
        headers["Prefer"] = prefer
    status, payload = _call(method, "/rest/v1/" + path, config=config, token=token,
                            body=body, headers=headers)
    return _check(status, payload)


# ---------------------------------------------------------------------------
# Signing in and out
# ---------------------------------------------------------------------------

def _device_label() -> str:
    return (socket.gethostname() or "Windows").strip()[:60]


def sign_in(config: dict, email: str, password: str) -> dict:
    email = (email or "").strip()
    if not email or not password:
        raise AccountError(i18n.message("account.missing_fields"))
    status, payload = _call("POST", "/auth/v1/token?grant_type=password", config=config,
                            body={"email": email, "password": password})
    if status == 400:
        reason = _reason(payload).lower()
        key = "account.not_confirmed" if "confirm" in reason else "account.wrong_credentials"
        raise AccountError(i18n.message(key))
    _check(status, payload)
    session = _store_tokens(payload)
    _register_device(config, session)
    return summary()


def sign_up(config: dict, email: str, password: str, display_name: str = "") -> dict:
    email = (email or "").strip()
    if not email or not password:
        raise AccountError(i18n.message("account.missing_fields"))
    if len(password) < 8:
        raise AccountError(i18n.message("account.password_short"))
    body: dict[str, Any] = {"email": email, "password": password}
    if display_name.strip():
        body["data"] = {"display_name": display_name.strip()}
    status, payload = _call("POST", "/auth/v1/signup", config=config, body=body)
    if status in (400, 422):
        raise AccountError(i18n.message("account.signup_failed", error=_reason(payload)))
    _check(status, payload)
    if isinstance(payload, dict) and payload.get("access_token"):
        session = _store_tokens(payload)
        _register_device(config, session)
        return summary()
    # E-mail confirmation is switched on: there is no session yet, and that is
    # not an error - the next step is in the user's inbox.
    return {**summary(), "pending_confirmation": email}


def sign_out(config: dict) -> dict:
    session = load_session()
    if session and session.get("access_token"):
        try:
            _call("POST", "/auth/v1/logout", config=config, token=session["access_token"])
        except AccountError:
            pass  # Offline: the local session goes regardless.
    _save_session(None)
    # The bookmark belongs to the account, not to the device: a different account
    # on the next sign-in must start from zero, not from where this one stopped.
    _write("sync_state.json", {})
    _status["last"] = None
    return summary()


def _register_device(config: dict, session: dict) -> None:
    """Names this device in the account, so the device list says where things
    came from. A failure here costs a label, not the sign-in."""
    label = _device_label()
    try:
        found = _rest("GET", "devices?select=id,label&label=eq." + urllib.parse.quote(label),
                      config)
        if found:
            device_id = found[0]["id"]
            _rest("PATCH", "devices?id=eq." + device_id, config,
                  body={"last_seen": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())})
        else:
            created = _rest("POST", "devices?select=id", config,
                            body={"user_id": session["user"]["id"], "label": label,
                                  "platform": "windows" if os.name == "nt" else os.name},
                            prefer="return=representation")
            device_id = created[0]["id"] if created else ""
        session = load_session() or session
        session["device_id"] = device_id
        _save_session(session)
    except (AccountError, KeyError, IndexError, TypeError):
        pass


def summary() -> dict:
    """What the interface may know: who is signed in, and how the last sync went.
    Never a token."""
    session = load_session()
    return {
        "signed_in": bool(session and session.get("refresh_token")),
        "email": ((session or {}).get("user") or {}).get("email", ""),
        "device": _device_label(),
        "syncing": _status["running"],
        "last": _status["last"] or _read("last_sync.json", None),
    }


# ---------------------------------------------------------------------------
# Local records
# ---------------------------------------------------------------------------

def _canonical(payload: Any) -> str:
    return json.dumps(payload, sort_keys=True, ensure_ascii=False, separators=(",", ":"))


def hash_of(payload: Any) -> str:
    return hashlib.sha256(_canonical(payload).encode("utf-8")).hexdigest()


def local_records(config: dict) -> dict[str, dict]:
    """Everything this device would sync, as {"collection/key": record}."""
    records: dict[str, dict] = {}
    for product in products.all_products(config):
        slug = product.get("slug")
        if not slug:
            continue
        records[f"product/{slug}"] = {"collection": "product", "key": slug, "payload": product}
        for name in DATA_FILES:
            if os.path.exists(core.product_store_path(slug, name)):
                records[f"data/{slug}:{name}"] = {
                    "collection": "data", "key": f"{slug}:{name}",
                    "payload": core.load_product(slug, name, None)}
    for record in records.values():
        record["hash"] = hash_of(record["payload"])
    return records


def _apply(config: dict, collection: str, key: str, payload: Any, deleted: bool) -> None:
    """Writes one record that came from the server."""
    if collection == "product":
        current = [p for p in config.get("products", []) if p.get("slug") != key]
        if not deleted and isinstance(payload, dict):
            payload = dict(payload, slug=key)
            existing = [p.get("slug") for p in config.get("products", [])]
            if key in existing:
                current.insert(existing.index(key), payload)
            else:
                current.append(payload)
        config["products"] = current
        if deleted:
            core.forget_product(key)
        if not config.get("active_product") or config["active_product"] not in {
                p.get("slug") for p in current}:
            config["active_product"] = current[0]["slug"] if current else ""
        core.save_config(config)
        return
    slug, _, name = key.partition(":")
    if name not in DATA_FILES or not slug:
        return
    path = core.product_store_path(slug, name)
    if deleted:
        try:
            os.remove(path)
        except OSError:
            pass
    else:
        core.save_product(slug, name, payload)


def _merge_history(mine: Any, theirs: Any) -> list:
    """Both histories, each post once. Losing an entry would let the safety catch
    propose a community that was posted to yesterday on the other machine."""
    seen: dict[tuple, dict] = {}
    for entry in list(theirs or []) + list(mine or []):
        if isinstance(entry, dict):
            seen.setdefault((entry.get("ts"), entry.get("community_id"), entry.get("channel")), entry)
    return sorted(seen.values(), key=lambda entry: entry.get("ts") or 0)


def _keep_copy(collection: str, key: str, payload: Any) -> None:
    folder = os.path.join(_folder(), "conflicts")
    os.makedirs(folder, exist_ok=True)
    safe = "".join(ch if ch.isalnum() or ch in "-_." else "_" for ch in f"{collection}-{key}")
    stamp = time.strftime("%Y%m%d-%H%M%S")
    core._write_json(os.path.join(folder, f"{stamp}-{safe}.json"), payload)


# ---------------------------------------------------------------------------
# Server records
# ---------------------------------------------------------------------------

def _blob_path(user_id: str, collection: str, key: str) -> str:
    # The key's hash, not the key itself: a slug never contains "../", but the
    # rule the SDK follows costs nothing and keeps both clients on one layout.
    return f"{user_id}/{APP}/{collection}/{hashlib.sha256(key.encode()).hexdigest()}.json"


def _pull(config: dict, collection: str, since: int) -> list[dict]:
    rows: list[dict] = []
    offset = 0
    while True:
        page = _rest("GET", "items?" + urllib.parse.urlencode({
            "select": "collection,key,rev,hash,payload,deleted_at,blob_path",
            "app": f"eq.{APP}", "collection": f"eq.{collection}", "rev": f"gt.{since}",
            "order": "rev.asc", "limit": PAGE, "offset": offset}), config) or []
        rows += page
        if len(page) < PAGE:
            break
        offset += PAGE
    for row in rows:
        if row.get("blob_path") and not row.get("deleted_at"):
            token, _ = _token(config)
            status, payload = _call("GET", f"/storage/v1/object/authenticated/{BUCKET}/"
                                    + urllib.parse.quote(row["blob_path"]),
                                    config=config, token=token)
            row["payload"] = _check(status, payload)
    return rows


def _push(config: dict, session: dict, records: list[dict]) -> list[dict]:
    rows = []
    for record in records:
        payload = record.get("payload")
        blob_path = None
        size = 0
        if not record.get("deleted"):
            text = _canonical(payload)
            size = len(text.encode("utf-8"))
            if size > BLOB_THRESHOLD:
                blob_path = _blob_path(session["user"]["id"], record["collection"], record["key"])
                token, _ = _token(config)
                status, answer = _call(
                    "POST", f"/storage/v1/object/{BUCKET}/" + urllib.parse.quote(blob_path),
                    config=config, token=token, raw=text.encode("utf-8"),
                    headers={"Content-Type": "application/json", "x-upsert": "true"})
                _check(status, answer)
                payload = None
        rows.append({
            "user_id": session["user"]["id"], "app": APP,
            "collection": record["collection"], "key": record["key"],
            "hash": record.get("hash"), "payload": None if record.get("deleted") else payload,
            "blob_path": blob_path, "size_bytes": size,
            "deleted_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
            if record.get("deleted") else None,
            "device_id": session.get("device_id") or None,
        })
    written: list[dict] = []
    for start in range(0, len(rows), 100):
        written += _rest("POST", "items?on_conflict=user_id,app,collection,key"
                                 "&select=collection,key,hash,rev,deleted_at", config,
                         body=rows[start:start + 100],
                         prefer="resolution=merge-duplicates,return=representation") or []
    return written


# ---------------------------------------------------------------------------
# One sync pass
# ---------------------------------------------------------------------------

def sync(config_loader=core.load_config) -> dict:
    """Runs one pass. Never raises for network or sign-in trouble - that is in the
    result, so the interface can say "waiting for network" instead of "error"."""
    if not _lock.acquire(blocking=False):
        return {"status": "busy"}
    _status["running"] = True
    try:
        result = _sync_once(config_loader)
    except AccountError as error:
        result = {"status": error.status, "error": error.message}
    except Exception as error:  # noqa: BLE001 - the reason has to reach the interface
        result = {"status": "error", "error": i18n.message("account.failed", error=error)}
    finally:
        _status["running"] = False
        _lock.release()
    result["at"] = int(time.time())
    _status["last"] = result
    _write("last_sync.json", result)
    return result


def _sync_once(config_loader) -> dict:
    config = config_loader()
    _token_value, session = _token(config)
    if not session.get("device_id"):
        _register_device(config, session)
        session = load_session() or session
    state = _read("sync_state.json", {})
    if state.get("user") != session["user"]["id"]:
        # Another account, or the first pass: no shared history to rely on.
        state = {"user": session["user"]["id"], "cursor": {}, "known": {}}
    known: dict[str, dict] = state.setdefault("known", {})
    cursors: dict[str, int] = state.setdefault("cursor", {})

    pulled = pushed = conflicts = 0
    local = local_records(config)
    to_push: dict[str, dict] = {}

    for collection in ("product", "data"):
        for row in _pull(config, collection, int(cursors.get(collection, 0))):
            cursors[collection] = max(int(cursors.get(collection, 0)), int(row["rev"]))
            ident = f"{collection}/{row['key']}"
            deleted = bool(row.get("deleted_at"))
            mine = local.get(ident)
            base = known.get(ident)
            changed_here = (mine is None and base is not None) or (
                mine is not None and (base is None or mine["hash"] != base.get("hash")))

            if (mine is None and deleted) or (
                    mine is not None and not deleted and mine["hash"] == row.get("hash")):
                # Both sides already agree - removed on both, or the same content.
                known[ident] = {"hash": row.get("hash"), "rev": row["rev"], "deleted": deleted}
                continue
            if not changed_here or (base and base.get("rev") == row["rev"]):
                if not changed_here:
                    config = config_loader()
                    _apply(config, collection, row["key"], row.get("payload"), deleted)
                    known[ident] = {"hash": row.get("hash"), "rev": row["rev"],
                                    "deleted": deleted}
                    pulled += 1
                continue

            # Both sides moved.
            conflicts += 1
            if collection == "data" and row["key"].endswith(":history") and mine and not deleted:
                merged = _merge_history(mine["payload"], row.get("payload"))
                config = config_loader()
                _apply(config, collection, row["key"], merged, False)
                to_push[ident] = {"collection": collection, "key": row["key"],
                                  "payload": merged, "hash": hash_of(merged)}
                known[ident] = {"hash": row.get("hash"), "rev": row["rev"]}
                continue
            if mine is not None:
                _keep_copy(collection, row["key"], mine["payload"])
            config = config_loader()
            _apply(config, collection, row["key"], row.get("payload"), deleted)
            known[ident] = {"hash": row.get("hash"), "rev": row["rev"], "deleted": deleted}
            pulled += 1

    # Read again: the pull may have written files.
    config = config_loader()
    local = local_records(config)
    for ident, record in local.items():
        base = known.get(ident)
        if ident not in to_push and (base is None or base.get("hash") != record["hash"]
                                     or base.get("deleted")):
            to_push[ident] = record
    for ident, base in list(known.items()):
        if ident not in local and not base.get("deleted"):
            collection, _, key = ident.partition("/")
            to_push[ident] = {"collection": collection, "key": key, "payload": None,
                              "hash": base.get("hash"), "deleted": True}

    if to_push:
        for row in _push(config, session, list(to_push.values())):
            ident = f"{row['collection']}/{row['key']}"
            known[ident] = {"hash": row.get("hash"), "rev": row["rev"],
                            "deleted": bool(row.get("deleted_at"))}
        pushed = len(to_push)

    _write("sync_state.json", state)
    return {"status": "ok", "pulled": pulled, "pushed": pushed, "conflicts": conflicts}


# ---------------------------------------------------------------------------
# In the background
# ---------------------------------------------------------------------------

def start_background(is_busy, interval: int = 300) -> None:
    """Syncs on start and every few minutes while signed in. Skips a beat while a
    scan or a run is writing - pulling into files that are being written invites
    exactly the conflict the copies in conflicts/ exist for."""

    def loop() -> None:
        time.sleep(5)
        while True:
            if load_session() and not is_busy():
                sync()
            time.sleep(interval)

    threading.Thread(target=loop, name="mutexx-account-sync", daemon=True).start()
