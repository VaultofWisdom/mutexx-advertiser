"""
Lokaler Server + GUI-Auslieferung.

Startet auf 127.0.0.1 (nur dieser Rechner, nicht im Netzwerk erreichbar) und
oeffnet die Oberflaeche im Standardbrowser.
"""

from __future__ import annotations

import json
import os
import socket
import sys
import threading
import time
import traceback
import webbrowser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

from . import core, discovery, drafts, publish, reddit_api, rules, seeds

UI_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "ui.html")

# Fortschritt des laufenden Scans (von der GUI abgefragt)
SCAN = {
    "running": False,
    "message": "Noch kein Scan gelaufen.",
    "done": 0,
    "total": 0,
    "finished_at": 0,
    "error": "",
}
_scan_lock = threading.Lock()


def _progress(message: str, done: int, total: int) -> None:
    with _scan_lock:
        SCAN["message"] = message
        SCAN["done"] = done
        SCAN["total"] = total


def _run_scan(platforms: list[str]) -> None:
    config = core.load_config()
    core.set_delay(config["request_delay_seconds"])
    entries: list[dict] = []
    warning = ""
    try:
        if "reddit" in platforms:
            try:
                entries += discovery.scan_reddit(config, _progress)
            except reddit_api.RedditAuthError as error:
                # Foren trotzdem scannen - der Rest der App bleibt nutzbar.
                warning = str(error)
                platforms = [p for p in platforms if p != "reddit"]
        if "forum" in platforms:
            entries += discovery.scan_forums(config, _progress)
        discovery.score_all(entries)

        # Bereits vorhandene Communities anderer Plattformen erhalten.
        existing = core.load("communities", [])
        keep = [e for e in existing if e.get("platform") not in platforms]
        merged = keep + entries
        merged.sort(key=lambda e: e.get("score", 0), reverse=True)
        core.save("communities", merged)

        with _scan_lock:
            SCAN["message"] = f"Fertig - {len(entries)} Communities bewertet."
            SCAN["error"] = warning
    except Exception as error:  # noqa: BLE001 - Fehler muss in der GUI landen
        with _scan_lock:
            SCAN["error"] = f"{type(error).__name__}: {error}"
            SCAN["message"] = "Scan abgebrochen."
        traceback.print_exc()
    finally:
        with _scan_lock:
            SCAN["running"] = False
            SCAN["finished_at"] = int(time.time())


class Handler(BaseHTTPRequestHandler):
    server_version = "MutexxAdvertiser/0.1"

    # Zugriffe nicht in die Konsole spammen
    def log_message(self, fmt: str, *args) -> None:  # noqa: A002
        return

    # -- Hilfen ------------------------------------------------------------
    def _send(self, status: int, payload, content_type: str = "application/json") -> None:
        if content_type == "application/json":
            body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        else:
            body = payload if isinstance(payload, bytes) else str(payload).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", f"{content_type}; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def _body(self) -> dict:
        length = int(self.headers.get("Content-Length") or 0)
        if not length:
            return {}
        try:
            return json.loads(self.rfile.read(length).decode("utf-8"))
        except json.JSONDecodeError:
            return {}

    def _community(self, community_id: str) -> dict | None:
        for entry in core.load("communities", []):
            if entry.get("id") == community_id:
                return entry
        return None

    # -- Routen ------------------------------------------------------------
    def do_GET(self) -> None:  # noqa: N802
        path = self.path.split("?")[0]
        try:
            if path in ("/", "/index.html"):
                with open(UI_PATH, "rb") as handle:
                    self._send(200, handle.read(), "text/html")
            elif path == "/api/state":
                self._send(200, {
                    "config": core.load_config(),
                    "communities": core.load("communities", []),
                    "queue": core.load("queue", []),
                    "history": core.load("history", []),
                    "discord_searches": seeds.DISCORD_SEARCH_URLS,
                    "verdict_text": rules.VERDICT_TEXT,
                    "angles": drafts.ANGLES,
                })
            elif path == "/api/scan/status":
                with _scan_lock:
                    self._send(200, dict(SCAN))
            else:
                self._send(404, {"error": "Unbekannter Pfad"})
        except Exception as error:  # noqa: BLE001
            traceback.print_exc()
            self._send(500, {"error": str(error)})

    def do_POST(self) -> None:  # noqa: N802
        path = self.path.split("?")[0]
        body = self._body()
        try:
            if path == "/api/scan/start":
                with _scan_lock:
                    if SCAN["running"]:
                        self._send(409, {"error": "Es laeuft bereits ein Scan."})
                        return
                    SCAN.update({"running": True, "message": "Start ...", "done": 0,
                                 "total": 0, "error": ""})
                platforms = body.get("platforms") or ["reddit", "forum"]
                threading.Thread(target=_run_scan, args=(platforms,), daemon=True).start()
                self._send(200, {"ok": True})

            elif path == "/api/reddit/check":
                self._send(200, reddit_api.check(core.load_config()))

            elif path == "/api/draft":
                entry = self._community(body.get("community_id", ""))
                if not entry:
                    self._send(404, {"error": "Community nicht gefunden."})
                    return
                config = core.load_config()
                angle = body.get("angle") or None
                if body.get("use_api"):
                    try:
                        draft = drafts.build_with_api(entry, config, angle)
                    except Exception as error:  # noqa: BLE001 - Fallback auf Vorlage
                        draft = drafts.build(entry, config, angle, seed=body.get("seed"))
                        draft["warning"] = f"KI-Entwurf fehlgeschlagen ({error}); Vorlage verwendet."
                else:
                    draft = drafts.build(entry, config, angle, seed=body.get("seed"))
                self._send(200, draft)

            elif path == "/api/queue/prepare":
                config = core.load_config()
                entries = core.load("communities", [])
                history = core.load("history", [])
                already = {h.get("community_id") for h in history}
                allowed = body.get("verdicts") or [rules.OPEN, rules.CONDITIONAL]
                limit = max(1, int(body.get("limit") or 25))
                use_api = bool(body.get("use_api"))

                picked = [e for e in entries
                          if e.get("analysis", {}).get("verdict") in allowed
                          and e["id"] not in already
                          and not e.get("low_value")
                          and (e.get("platform") != "forum" or e.get("reachable", True))]
                picked.sort(key=lambda e: e.get("score", 0), reverse=True)
                picked = picked[:limit]

                # Termine verteilen: Reddit streng nach Tageslimit, Foren lockerer.
                per_day_reddit = max(1, config["safety"]["max_reddit_posts_per_day"])
                counters = {"reddit": 0, "other": 0}
                queue: list[dict] = []
                for entry in picked:
                    if use_api:
                        try:
                            draft = drafts.build_with_api(entry, config)
                        except Exception:  # noqa: BLE001 - Vorlage als Rueckfallebene
                            draft = drafts.build(entry, config)
                    else:
                        draft = drafts.build(entry, config)

                    if entry.get("platform") == "reddit":
                        day = counters["reddit"] // per_day_reddit
                        counters["reddit"] += 1
                        draft["target_url"] = publish.reddit_submit_url(entry["handle"], draft)
                    else:
                        day = counters["other"] // 3
                        counters["other"] += 1
                        draft["target_url"] = entry.get("url", "")

                    draft["status"] = "offen"
                    draft["score"] = entry.get("score", 0)
                    draft["verdict"] = entry.get("analysis", {}).get("verdict", "grau")
                    draft["scheduled_for"] = time.strftime(
                        "%Y-%m-%d", time.localtime(time.time() + day * 86400))
                    queue.append(draft)

                queue.sort(key=lambda q: (q["scheduled_for"], -q.get("score", 0)))
                core.save("queue", queue)
                self._send(200, {"ok": True, "count": len(queue), "queue": queue})

            elif path == "/api/queue/add":
                queue = core.load("queue", [])
                item = body.get("draft") or {}
                item["status"] = "offen"
                queue = [q for q in queue if q.get("community_id") != item.get("community_id")]
                queue.append(item)
                core.save("queue", queue)
                self._send(200, {"ok": True, "queue": queue})

            elif path == "/api/queue/remove":
                queue = [q for q in core.load("queue", [])
                         if q.get("community_id") != body.get("community_id")]
                core.save("queue", queue)
                self._send(200, {"ok": True, "queue": queue})

            elif path == "/api/assist":
                entry = self._community(body.get("community_id", ""))
                if not entry:
                    self._send(404, {"error": "Community nicht gefunden."})
                    return
                config = core.load_config()
                guard = publish.check_guard(entry, config, core.load("history", []))
                url = ""
                if entry.get("platform") == "reddit":
                    url = publish.reddit_submit_url(entry["handle"], body.get("draft") or {})
                else:
                    url = entry.get("url", "")
                self._send(200, {"guard": guard, "url": url})

            elif path == "/api/publish/auto":
                config = core.load_config()
                draft = body.get("draft") or {}
                results = publish.run_auto_channels(config, draft)
                for result in results:
                    publish.log_post(
                        {"id": f"auto:{result['kind']}", "name": result["channel"],
                         "platform": result["kind"]},
                        draft, result["channel"],
                        "erfolgreich" if result["ok"] else f"Fehler {result['status']}",
                    )
                self._send(200, {"results": results})

            elif path == "/api/log":
                entry = self._community(body.get("community_id", "")) or {
                    "id": body.get("community_id", "unbekannt"),
                    "name": body.get("community", "unbekannt"),
                    "platform": body.get("platform", "reddit"),
                }
                publish.log_post(entry, body.get("draft") or {},
                                 body.get("channel", "manuell"),
                                 body.get("result", "gepostet"))
                queue = [q for q in core.load("queue", [])
                         if q.get("community_id") != entry["id"]]
                core.save("queue", queue)
                self._send(200, {"ok": True})

            elif path == "/api/config":
                config = core.load_config()
                merged = core._deep_merge(config, body.get("config") or {})
                core.save_config(merged)
                core.set_delay(merged["request_delay_seconds"])
                self._send(200, {"ok": True, "config": merged})

            elif path == "/api/community/add":
                config = core.load_config()
                entries = core.load("communities", [])
                new = dict(body.get("community") or {})
                platform = new.get("platform") or "forum"
                handle = (new.get("handle") or "").strip().lstrip("/").removeprefix("r/")

                # Subreddits brauchen nur den Namen - URL und Anzeigename bauen wir.
                if platform == "reddit":
                    if not handle:
                        self._send(400, {"error": "Subreddit-Name fehlt."})
                        return
                    new["handle"] = handle
                    new["name"] = f"r/{handle}"
                    new["url"] = f"https://www.reddit.com/r/{handle}/"
                    new["id"] = f"reddit:{handle}"
                elif not new.get("url"):
                    self._send(400, {"error": "URL fehlt."})
                    return
                else:
                    new.setdefault("handle", new["url"])
                    new.setdefault("name", new["url"])
                    new.setdefault("id", f"{platform}:{new['url']}")

                # Selbst eingefuegter Regeltext wird genauso analysiert wie ein
                # per API geholter - dieselbe Ampel, dieselben Zitate.
                rules_text = (new.pop("rules_text", "") or "").strip()
                if rules_text:
                    new["analysis"] = rules.analyse({"Eingefuegte Regeln": rules_text})
                    new["rules"] = [{"name": "Von Hand eingefuegt", "text": rules_text[:4000]}]
                else:
                    new.setdefault("analysis", {"verdict": rules.UNKNOWN, "labels": [],
                                                "evidence": [], "explicitly_allowed": False})
                    new.setdefault("rules", [])

                new["subscribers"] = int(new.get("subscribers") or 0)
                new.setdefault("title", "")
                new.setdefault("description", "Von Hand aufgenommen")
                new.setdefault("posts_per_day", 0.0)
                new["fit_raw"] = discovery._fit_score(
                    {"display_name": new["handle"], "title": new.get("title", ""),
                     "public_description": new.get("description", ""), "description": rules_text},
                    config["discovery"]["keywords"])
                new["manual"] = True

                entries = [e for e in entries if e.get("id") != new["id"]]
                entries.append(new)
                discovery.score_all(entries)
                core.save("communities", entries)
                self._send(200, {"ok": True, "community": new})

            else:
                self._send(404, {"error": "Unbekannter Pfad"})
        except Exception as error:  # noqa: BLE001
            traceback.print_exc()
            self._send(500, {"error": str(error)})


def _free_port(preferred: int = 8777) -> int:
    for port in range(preferred, preferred + 25):
        with socket.socket() as probe:
            try:
                probe.bind(("127.0.0.1", port))
                return port
            except OSError:
                continue
    return 0


def main() -> None:
    core.load_config()  # legt config.json beim ersten Start an
    port = _free_port()
    server = ThreadingHTTPServer(("127.0.0.1", port), Handler)
    url = f"http://127.0.0.1:{port}/"

    print("=" * 64)
    print("  Mutexx Advertiser  -  ein Produkt von Mutexx Production")
    print("=" * 64)
    print(f"  Oberflaeche: {url}")
    print("  Beenden:     dieses Fenster schliessen oder Strg+C")
    print("=" * 64)

    threading.Timer(1.0, lambda: webbrowser.open(url)).start()
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nBeendet.")
        server.shutdown()
        sys.exit(0)


if __name__ == "__main__":
    main()
