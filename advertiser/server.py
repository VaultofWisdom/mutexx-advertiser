"""
Local server and interface delivery.

Listens on 127.0.0.1 - this machine only, not reachable from the network - and opens
the interface in the default browser.

Every route works on the ACTIVE product profile. Communities, queue, history, analysis
and strategy are kept apart per product - see products.py.
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
from typing import Any
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

from . import (__version__, account, analysis, assets, core, discovery, drafts, i18n,
               legal, lemmy_api, manual, products, publish, reddit_api, rules, seeds, strategy)

UI_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "ui.html")

# Progress of the running background job, polled by the interface.
# The running job. "message" and "error" hold translatable messages, not sentences -
# the progress line has to follow the language switch like everything else.
JOB = {
    "running": False,
    "kind": "",
    "message": {"key": "scan.nothing_yet", "params": {}},
    "done": 0,
    "total": 0,
    "finished_at": 0,
    "error": "",
    # Filled by the full run: what worked, and what was left out and why.
    "report": {"done": [], "skipped": []},
}
_job_lock = threading.Lock()


def _progress(message: str, done: int, total: int) -> None:
    """Progress reports arrive as catalogue keys - see analysis.analyse."""
    with _job_lock:
        JOB["message"] = i18n.message(message) if isinstance(message, str) else message
        JOB["done"] = done
        JOB["total"] = total


def _start_job(kind: str) -> bool:
    """Claims the single work slot. Returns False when something is already running."""
    with _job_lock:
        if JOB["running"]:
            return False
        JOB.update({"running": True, "kind": kind,
                    "message": i18n.message("scan.starting"),
                    "done": 0, "total": 0, "error": "",
                    "report": {"done": [], "skipped": []}})
        return True


def _finish_job(message: Any = None, error: Any = None) -> None:
    with _job_lock:
        if message:
            JOB["message"] = message
        if error:
            JOB["error"] = error
        JOB["running"] = False
        JOB["finished_at"] = int(time.time())


# ---------------------------------------------------------------------------
# Background work
# ---------------------------------------------------------------------------

def _scan_keywords(product: dict) -> list[str]:
    """The scan's keyword list: profile first, then analysis. With neither it stays
    empty - and a scan without keywords would be a walk through nothing."""
    return analysis.merged_keywords(product, analysis.load(product.get("slug", "")))


def _scan_terms(product: dict) -> tuple[list[str], dict[str, float], list[str]]:
    """Everything the scan needs to know about the keywords: the full list to score
    against, what each one is worth, and the shorter list actually worth searching
    with. Worked out in one place so the ordinary scan and the full run cannot end up
    searching for different things."""
    result = analysis.load(product.get("slug", ""))
    keywords = analysis.merged_keywords(product, result)
    weights = analysis.keyword_weights(product, result)
    return keywords, weights, analysis.search_terms_of(weights)


def _run_scan(platforms: list[str], slug: str) -> None:
    config = core.load_config()
    product = products.get(config, slug) or products.active(config)
    core.set_delay(config["request_delay_seconds"])
    keywords, weights, search_terms = _scan_terms(product)
    seed_data = seeds.load_seeds(slug)
    entries: list[dict] = []
    warning: Any = ""
    try:
        if not keywords:
            raise ValueError(i18n.t("scan.no_keywords"))

        if "reddit" in platforms:
            try:
                entries += discovery.scan_reddit(config, keywords, seed_data["subreddits"],
                                                 _progress, weights, search_terms)
            except reddit_api.RedditAuthError as error:
                # Scan the forums anyway - the rest of the app stays usable.
                warning = error.message
                platforms = [p for p in platforms if p != "reddit"]
        if "lemmy" in platforms:
            # No key, no approval, no account - so no error path that could take
            # the rest of the scan down with it. An instance that is unreachable
            # is simply skipped inside scan_lemmy.
            entries += discovery.scan_lemmy(config, keywords,
                                            seed_data["lemmy_instances"], _progress,
                                            weights, search_terms)
        if "hackernews" in platforms or "lobsters" in platforms:
            # Neither is discovered - there is one of each - so there are no seeds
            # and nothing to configure. Both are asked whether this product belongs
            # there, and both answer with numbers rather than an opinion.
            entries += [entry for entry in discovery.scan_aggregators(config, keywords, _progress)
                        if entry["platform"] in platforms]
        if "forum" in platforms:
            if seed_data["forums"]:
                entries += discovery.scan_forums(config, keywords, seed_data["forums"],
                                                 _progress, weights)
            else:
                warning = warning or i18n.message("scan.no_forum_seeds")
        discovery.score_all(entries)

        # Keep communities from platforms this run did not touch.
        existing = core.load_product(slug, "communities", [])
        keep = [entry for entry in existing if entry.get("platform") not in platforms]
        merged = keep + entries
        merged.sort(key=lambda entry: entry.get("score", 0), reverse=True)
        core.save_product(slug, "communities", merged)

        _finish_job(i18n.message("scan.done", count=len(entries)), warning)
    except Exception as error:  # noqa: BLE001 - the error has to reach the interface
        traceback.print_exc()
        _finish_job(i18n.message("scan.aborted"), f"{type(error).__name__}: {error}")


def _run_analysis(slug: str, use_api: bool | None) -> None:
    try:
        config = core.load_config()
        product = products.get(config, slug)
        if not product:
            raise ValueError(i18n.t("error.product_not_found"))
        core.set_delay(config["request_delay_seconds"])
        result = analysis.analyse(product, config, _progress, use_api=use_api)
        analysis.store(slug, result)

        # The strategy hangs off the analysis - rebuild it straight away so the
        # interface is not left holding a stale plan.
        plan = strategy.build(product, result, config, use_api=use_api)
        strategy.store(slug, plan)
        _finish_job(i18n.message("analysis.done"),
                    (result.get("warnings") or [None])[0])
    except Exception as error:  # noqa: BLE001
        traceback.print_exc()
        _finish_job(i18n.message("analysis.aborted"), f"{type(error).__name__}: {error}")


def prepare_queue(config: dict, product: dict, slug: str, *,
                  verdicts: list[str] | None = None, limit: Any = None,
                  use_api: bool = False) -> list[dict]:
    """Picks the communities worth writing for, writes a draft for each, and spreads
    the dates. Used by the Campaign tab and by the full run - one implementation, so
    the safety catch cannot hold on one path and not the other."""
    entries = core.load_product(slug, "communities", [])
    history = core.load_product(slug, "history", [])
    result = analysis.load(slug)
    already = {item.get("community_id") for item in history}
    allowed = verdicts or [rules.OPEN, rules.CONDITIONAL]
    limit = max(1, int(limit or 25))

    picked = [entry for entry in entries
              if entry.get("analysis", {}).get("verdict") in allowed
              and entry["id"] not in already
              and not entry.get("low_value")
              and (entry.get("platform") != "forum" or entry.get("reachable", True))]
    picked.sort(key=lambda entry: entry.get("score", 0), reverse=True)
    picked = picked[:limit]

    # Spread the dates: communities you post into by hand strictly by the
    # daily limit, forums more loosely. Reddit and Lemmy share one counter -
    # otherwise the queue would hand out two "today" slots for a limit of one.
    per_day_manual = max(1, config["safety"]["max_reddit_posts_per_day"])
    counters = {"manual": 0, "other": 0}
    queue: list[dict] = []
    for entry in picked:
        if use_api:
            try:
                draft = drafts.build_with_api(entry, product, config, result)
            except Exception:  # noqa: BLE001 - fall back to the template
                draft = drafts.build(entry, product, result)
        else:
            draft = drafts.build(entry, product, result)

        if entry.get("platform") in publish.MANUAL_PLATFORMS:
            day = counters["manual"] // per_day_manual
            counters["manual"] += 1
            # Reddit can take title and body in the URL. Lemmy's create-post
            # route needs the community's numeric id, which we do not carry -
            # so it gets its own page, and the assistant fills the form there.
            draft["target_url"] = (publish.reddit_submit_url(entry["handle"], draft)
                                   if entry.get("platform") == "reddit"
                                   else entry.get("submit_url") or entry.get("url", ""))
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

    queue.sort(key=lambda item: (item["scheduled_for"], -item.get("score", 0)))
    core.save_product(slug, "queue", queue)
    return queue


# ---------------------------------------------------------------------------
# The whole chain in one run
# ---------------------------------------------------------------------------

# The five stages, in the only order they work in: each one feeds the next.
# The analysis produces the keywords the scan searches with; the strategy decides
# which assets are worth writing; the scan finds what the campaign is built from.
FULL_RUN_STAGES = ("analysis", "strategy", "seeds", "scan", "assets", "campaign")


def _run_everything(slug: str, use_api: bool | None, platforms: list[str]) -> None:
    """Product profile in, prepared campaign out.

    Nothing here publishes anything. The run ends exactly where the app always
    ends: with work laid out for a human to send. That is not a limitation of the
    automation, it is the thing the automation exists to protect - see the README.

    A stage that fails does not stop the run. Four working stages and one honest
    note about the fifth are worth more than an empty result, and the note says
    which stage and why rather than leaving the user to guess from a half-filled
    interface.
    """
    done: list[dict] = []
    skipped: list[dict] = []
    total = len(FULL_RUN_STAGES)

    def stage(index: int, key: str) -> None:
        _progress_stage(f"run.stage.{key}", index, total)

    try:
        config = core.load_config()
        product = products.get(config, slug)
        if not product:
            raise ValueError(i18n.t("error.product_not_found"))
        core.set_delay(config["request_delay_seconds"])
        if use_api is None:
            use_api = core.ai_ready(config)

        # 1) Analysis - everything downstream reads its keywords.
        stage(0, "analysis")
        try:
            result = analysis.analyse(product, config, _progress, use_api=use_api)
            analysis.store(slug, result)
            done.append(i18n.message("run.done.analysis",
                                     count=len(result.get("keywords") or [])))
        except Exception as error:  # noqa: BLE001
            traceback.print_exc()
            result = analysis.load(slug)
            skipped.append(i18n.message("run.skipped.analysis", error=error))

        # 2) Strategy.
        stage(1, "strategy")
        try:
            plan = strategy.build(product, result, config, use_api=use_api)
            strategy.store(slug, plan)
            done.append(i18n.message("run.done.strategy", count=len(plan.get("channels") or [])))
        except Exception as error:  # noqa: BLE001
            traceback.print_exc()
            plan = strategy.load(slug) or {}
            skipped.append(i18n.message("run.skipped.strategy", error=error))

        # 3) Seed lists - only asked for when there is nothing to scan from and a
        #    key to ask with. Never overwrites what the user entered themselves.
        stage(2, "seeds")
        seed_data = seeds.load_seeds(slug)
        if seed_data["subreddits"] or seed_data["forums"]:
            skipped.append(i18n.message("run.skipped.seeds_present"))
        elif not use_api:
            skipped.append(i18n.message("run.skipped.seeds_no_key"))
        else:
            try:
                suggested = seeds.suggest_with_api(
                    product, result, config, analysis.merged_keywords(product, result))
                saved = seeds.save_seeds(slug, {
                    "subreddits": suggested.get("subreddits", []),
                    "forums": suggested.get("forums", []),
                    "lemmy_instances": seed_data["lemmy_instances"],
                    "source": "vorschlag",
                })
                done.append(i18n.message("run.done.seeds", subs=len(saved["subreddits"]),
                                         forums=len(saved["forums"])))
            except Exception as error:  # noqa: BLE001
                traceback.print_exc()
                skipped.append(i18n.message("run.skipped.seeds", error=error))

        # 4) Scan.
        stage(3, "scan")
        keywords, weights, search_terms = _scan_terms(product)
        if not keywords:
            skipped.append(i18n.message("run.skipped.scan_no_keywords"))
        else:
            found = _scan_platforms(config, slug, keywords, platforms, skipped,
                                    weights, search_terms)
            done.append(i18n.message("run.done.scan", count=found))

        # 5) Assets - only the ones the strategy actually recommends. Writing all
        #    nine for a product with no shop would be work nobody asked for.
        stage(4, "assets")
        built = _build_recommended_assets(config, product, slug, plan, use_api, skipped)
        done.append(i18n.message("run.done.assets", count=built))

        # 6) Campaign.
        stage(5, "campaign")
        try:
            queue = prepare_queue(config, product, slug, use_api=use_api)
            done.append(i18n.message("run.done.campaign", count=len(queue)))
        except Exception as error:  # noqa: BLE001
            traceback.print_exc()
            skipped.append(i18n.message("run.skipped.campaign", error=error))

        _finish_job(i18n.message("run.finished", done=len(done), skipped=len(skipped)),
                    skipped[0] if skipped else "")
        with _job_lock:
            JOB["report"] = {"done": done, "skipped": skipped}
    except Exception as error:  # noqa: BLE001
        traceback.print_exc()
        _finish_job(i18n.message("run.aborted"), f"{type(error).__name__}: {error}")


def _scan_platforms(config: dict, slug: str, keywords: list[str],
                    platforms: list[str], skipped: list,
                    weights: dict[str, float] | None = None,
                    search_terms: list[str] | None = None) -> int:
    """The scan as the full run needs it: one platform failing costs that platform
    and nothing else."""
    seed_data = seeds.load_seeds(slug)
    entries: list[dict] = []
    touched: list[str] = []

    if "reddit" in platforms:
        try:
            entries += discovery.scan_reddit(config, keywords, seed_data["subreddits"],
                                             _progress, weights, search_terms)
            touched.append("reddit")
        except reddit_api.RedditAuthError as error:
            skipped.append(i18n.message("run.skipped.reddit", error=error.message))
    if "lemmy" in platforms:
        entries += discovery.scan_lemmy(config, keywords, seed_data["lemmy_instances"],
                                        _progress, weights, search_terms)
        touched.append("lemmy")
    if "hackernews" in platforms or "lobsters" in platforms:
        entries += [entry for entry in discovery.scan_aggregators(
                        config, search_terms or keywords, _progress)
                    if entry["platform"] in platforms]
        touched += [p for p in ("hackernews", "lobsters") if p in platforms]
    if "forum" in platforms:
        if seed_data["forums"]:
            entries += discovery.scan_forums(config, keywords, seed_data["forums"],
                                             _progress, weights)
            touched.append("forum")
        else:
            skipped.append(i18n.message("scan.no_forum_seeds"))

    discovery.score_all(entries)
    existing = core.load_product(slug, "communities", [])
    keep = [entry for entry in existing if entry.get("platform") not in touched]
    merged = keep + entries
    merged.sort(key=lambda entry: entry.get("score", 0), reverse=True)
    core.save_product(slug, "communities", merged)
    return len(entries)


def _build_recommended_assets(config: dict, product: dict, slug: str, plan: dict,
                              use_api: bool, skipped: list) -> int:
    """Writes the copy for the channels the strategy put forward, and only those."""
    wanted = {item.get("id") for item in (plan.get("channels") or [])}
    built = 0
    for spec in assets.available(product):
        # No plan (the strategy stage failed) means write everything the product
        # qualifies for - a missing plan should cost the assets nothing.
        if wanted and spec["channel"] not in wanted:
            continue
        try:
            asset = assets.build(spec["id"], product, analysis.load(slug), config,
                                 use_api=use_api)
            assets.store(slug, asset)
            built += 1
        except Exception as error:  # noqa: BLE001 - one asset is not the run
            traceback.print_exc()
            skipped.append(i18n.message("run.skipped.asset", asset=spec["id"], error=error))
    return built


def _progress_stage(key: str, index: int, total: int) -> None:
    with _job_lock:
        JOB["message"] = i18n.message(key)
        JOB["done"] = index
        JOB["total"] = total


# ---------------------------------------------------------------------------
# The claude.ai route
# ---------------------------------------------------------------------------

CLAUDE_AI_TASKS = ("draft", "asset", "analysis", "strategy", "seeds")
# The chats a request can be taken to. Which one is only recorded as the author of
# the copy - the request itself is the same for all of them.
CHAT_SERVICES = ("claudeai", "claudeapp", "chatgpt", "gemini")


def _claude_ai_task(task: str, body: dict, config: dict, product: dict, slug: str) -> Any:
    """Runs one of the five things the app writes with Claude, through exactly the
    function the API route uses. Whether that function's request is captured or
    answered is decided by the context it runs in (see core.claude_ai_capture)."""
    service = body.get("service") if body.get("service") in CHAT_SERVICES else "claudeai"
    if service == "claudeapp":
        service = "claudeai"
    config = core.claude_ai_config(config, service)
    result = analysis.load(slug)
    if task == "draft":
        entry = next((item for item in core.load_product(slug, "communities", [])
                      if item.get("id") == body.get("community_id")), None)
        if not entry:
            raise LookupError("error.not_found")
        return drafts.build_with_api(entry, product, config, result, body.get("angle") or None)
    if task == "asset":
        asset_id = body.get("asset_id", "")
        if asset_id not in assets.ASSETS_BY_ID:
            raise LookupError("error.unknown_asset")
        asset = assets.build(asset_id, product, result, config, use_api=True)
        assets.store(slug, asset)
        return asset
    if task == "analysis":
        fresh = analysis.analyse(product, config, lambda *_args: None, use_api=True)
        analysis.store(slug, fresh)
        # The strategy hangs off the analysis, as on the ordinary route - rebuilt by
        # the rules here; its own summary has its own claude.ai button.
        strategy.store(slug, strategy.build(product, fresh, config, use_api=False))
        return fresh
    if task == "strategy":
        plan = strategy.build(product, result, config, use_api=True)
        strategy.store(slug, plan)
        return plan
    if task == "seeds":
        suggested = seeds.suggest_with_api(product, result, config, _scan_keywords(product))
        existing = seeds.load_seeds(slug)
        return seeds.save_seeds(slug, {
            "subreddits": existing["subreddits"] + suggested["subreddits"],
            "forums": existing["forums"] + suggested["forums"],
            "lemmy_instances": existing["lemmy_instances"],
            "source": "vorschlag",
        })
    raise LookupError("error.unknown_path")


def _run_seed_suggestion(slug: str) -> None:
    try:
        config = core.load_config()
        product = products.get(config, slug)
        if not product:
            raise ValueError(i18n.t("error.product_not_found"))
        _progress("seeds.suggesting", 0, 2)
        suggested = seeds.suggest_with_api(product, analysis.load(slug), config,
                                           _scan_keywords(product))
        existing = seeds.load_seeds(slug)
        merged = {
            "subreddits": existing["subreddits"] + suggested["subreddits"],
            "forums": existing["forums"] + suggested["forums"],
            # Carried through unchanged: save_seeds writes the whole list, so
            # anything left out here would be silently deleted.
            "lemmy_instances": existing["lemmy_instances"],
            "source": "vorschlag",
        }
        saved = seeds.save_seeds(slug, merged)
        _finish_job(i18n.message("seeds.suggested", subs=len(saved["subreddits"]),
                                 forums=len(saved["forums"])))
    except Exception as error:  # noqa: BLE001
        traceback.print_exc()
        _finish_job(i18n.message("seeds.suggest_aborted"), f"{type(error).__name__}: {error}")


# ---------------------------------------------------------------------------
# Secrets
# ---------------------------------------------------------------------------

# Configuration values that never travel to the browser. The interface learns only
# THAT one is set; to change one, the user types a new value, and an empty field
# means "keep what is there". A page that cannot read the key cannot leak it -
# not to a browser extension, not to a screenshot, not to a shoulder.
SECRET_PATHS = (
    ("anthropic", "api_key"),
    ("openai", "api_key"),
    ("gemini", "api_key"),
    ("reddit", "client_secret"),
    ("reddit", "bot_password"),
    ("auto_channels", "mastodon", "access_token"),
)


def _get_path(data: dict, path: tuple) -> Any:
    for key in path:
        if not isinstance(data, dict):
            return None
        data = data.get(key)
    return data


def _set_path(data: dict, path: tuple, value: Any) -> None:
    for key in path[:-1]:
        data = data.setdefault(key, {})
    data[path[-1]] = value


def _drop_path(data: dict, path: tuple) -> None:
    for key in path[:-1]:
        data = data.get(key)
        if not isinstance(data, dict):
            return
    if isinstance(data, dict):
        data.pop(path[-1], None)


def mask_webhook(url: str) -> str:
    """A Discord webhook URL is a password: whoever has it can post as the server.
    Enough of it stays visible to tell two apart."""
    url = url or ""
    head, _, token = url.rpartition("/")
    if not head or len(token) < 8:
        return url[:24] + "\u2026" if len(url) > 24 else url
    return f"{head}/{token[:4]}\u2026{token[-2:]}"


def public_config(config: dict) -> dict:
    """The configuration as the browser may see it: secrets blanked, plus a map of
    which ones are set."""
    safe = json.loads(json.dumps(config))
    present: dict[str, bool] = {}
    for path in SECRET_PATHS:
        present[".".join(path)] = bool(str(_get_path(config, path) or "").strip())
        if _get_path(safe, path) is not None:
            _set_path(safe, path, "")
    hooks = ((safe.get("auto_channels") or {}).get("discord_webhooks")) or []
    safe.setdefault("auto_channels", {})["discord_webhooks"] = [
        {"name": (hook.get("name") if isinstance(hook, dict) else "") or "Discord",
         "url": mask_webhook(hook.get("url") if isinstance(hook, dict) else hook)}
        for hook in hooks]
    safe["secrets_set"] = present
    return safe


def merge_config_update(config: dict, update: dict) -> dict:
    """Applies a Settings save. Empty secrets keep the stored value; 'clear_secrets'
    removes one on purpose. Webhooks are not changed through here - they have their
    own routes, because the browser only ever holds their masked form."""
    update = json.loads(json.dumps(update or {}))
    clear = set(update.pop("clear_secrets", []) or [])
    update.pop("secrets_set", None)
    if isinstance(update.get("auto_channels"), dict):
        update["auto_channels"].pop("discord_webhooks", None)
    for path in SECRET_PATHS:
        if ".".join(path) in clear:
            _set_path(update, path, "")
        elif not str(_get_path(update, path) or "").strip():
            _drop_path(update, path)
    return core._deep_merge(config, update)


# ---------------------------------------------------------------------------
# HTTP
# ---------------------------------------------------------------------------

# The one origin the interface is served from. Everything else is refused:
#  * a Host header naming anything but this machine is a DNS-rebinding attempt -
#    a web page whose domain was re-pointed at 127.0.0.1 to read /api/state;
#  * a POST from another origin is a page in some other tab trying to drive the
#    app - start a run, rewrite the configuration, post to the owned channels.
# Requiring application/json on POST closes the last gap: browsers will not send
# that cross-origin without a preflight, and this server answers no preflight.
_LOCAL_HOSTS = ("127.0.0.1", "localhost", "[::1]")

# Nothing the interface sends comes near this; a pasted rule text is a few KB.
_MAX_BODY = 4 * 1024 * 1024

# The interface needs nothing from anywhere else, so it may load nothing from
# anywhere else.
_CSP = ("default-src 'self'; script-src 'self' 'unsafe-inline'; "
        "style-src 'self' 'unsafe-inline'; img-src 'self' data:; connect-src 'self'; "
        "frame-ancestors 'none'; base-uri 'none'; form-action 'none'")

class Handler(BaseHTTPRequestHandler):
    server_version = f"MutexxAdvertiser/{__version__}"
    sys_version = ""

    # Do not spam the console with every request
    def log_message(self, fmt: str, *args) -> None:  # noqa: A002
        return

    # -- Helpers -----------------------------------------------------------
    def _send(self, status: int, payload, content_type: str = "application/json") -> None:
        if content_type == "application/json":
            body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        else:
            body = payload if isinstance(payload, bytes) else str(payload).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", f"{content_type}; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Referrer-Policy", "no-referrer")
        if content_type == "text/html":
            self.send_header("Content-Security-Policy", _CSP)
            self.send_header("X-Frame-Options", "DENY")
        self.end_headers()
        self.wfile.write(body)

    def _port(self) -> int:
        return int(self.server.server_address[1])

    def _host_ok(self) -> bool:
        host = (self.headers.get("Host") or "").strip().lower()
        return host in {f"{name}:{self._port()}" for name in _LOCAL_HOSTS}

    def _origin_ok(self) -> bool:
        origin = (self.headers.get("Origin") or "").strip().lower()
        if not origin:
            # Same-origin fetches may omit it; a cross-site one always sends it.
            return True
        return origin in {f"http://{name}:{self._port()}" for name in _LOCAL_HOSTS}

    def _refuse(self) -> None:
        self._send(403, {"error_key": "error.forbidden_origin"})

    def _body(self) -> dict:
        try:
            length = int(self.headers.get("Content-Length") or 0)
        except ValueError:
            return {}
        if length <= 0:
            return {}
        raw = self.rfile.read(min(length, _MAX_BODY))
        if length > _MAX_BODY:
            return {}
        try:
            data = json.loads(raw.decode("utf-8"))
        except (json.JSONDecodeError, UnicodeDecodeError):
            return {}
        return data if isinstance(data, dict) else {}

    def _active(self) -> tuple[dict, dict, str]:
        """Configuration, active profile and its slug. The slug is empty while no
        product exists - products.active() then returns a template profile whose slug
        must not become a data folder."""
        config = core.load_config()
        return config, products.active(config), products.active_slug(config)

    def _community(self, slug: str, community_id: str) -> dict | None:
        for entry in core.load_product(slug, "communities", []):
            if entry.get("id") == community_id:
                return entry
        return None

    # -- GET ---------------------------------------------------------------
    def do_GET(self) -> None:  # noqa: N802
        path = self.path.split("?")[0]
        if not self._host_ok():
            self._refuse()
            return
        try:
            if path in ("/", "/index.html"):
                with open(UI_PATH, "rb") as handle:
                    self._send(200, handle.read(), "text/html")
            elif path == "/api/state":
                self._send(200, self._state())
            elif path == "/api/job/status":
                with _job_lock:
                    self._send(200, dict(JOB))
            else:
                self._send(404, {"error_key": "error.unknown_path"})
        except Exception as error:  # noqa: BLE001
            traceback.print_exc()
            self._send(500, {"error": str(error)})

    def _state(self) -> dict:
        config, product, slug = self._active()
        keywords = _scan_keywords(product) if slug else []
        return {
            "version": __version__,
            "data_dir": core.HOME_DIR,
            "config": public_config(config),
            "products": products.all_products(config),
            "active_product": slug,
            "product": product,
            "communities": core.load_product(slug, "communities", []) if slug else [],
            "queue": core.load_product(slug, "queue", []) if slug else [],
            "history": core.load_product(slug, "history", []) if slug else [],
            "analysis": analysis.load(slug) if slug else {},
            "strategy": strategy.load(slug) if slug else {},
            "seeds": seeds.load_seeds(slug) if slug else seeds.EMPTY_SEEDS,
            "assets": assets.load_all(slug) if slug else {},
            "asset_specs": assets.available(product),
            "keywords": keywords,
            "discord_searches": seeds.discord_searches(keywords),
            "catalog": i18n.catalogue(),
            "manual": {code: manual.chapters(code) for code in i18n.LANGUAGES},
            "legal": {code: legal.pages(code) for code in i18n.LANGUAGES},
            "languages": i18n.LANGUAGES,
            "ui_language": i18n.normalise(config.get("ui_language")),
            "verdict_text": rules.VERDICT_TEXT,
            "angles": drafts.ANGLES,
            "categories": products.CATEGORIES,
            "price_models": products.PRICE_MODELS,
            "tones": products.TONES,
            "has_api_key": core.ai_ready(config),
            "ai_provider": core.ai_provider(config),
            "ai_providers": {key: value["name"] for key, value in core.AI_PROVIDERS.items()},
            "account": account.summary(),
            "desktop": bool(os.environ.get("MUTEXX_ADVERTISER_DESKTOP")),
        }

    # -- POST --------------------------------------------------------------
    def do_POST(self) -> None:  # noqa: N802
        path = self.path.split("?")[0]
        content_type = (self.headers.get("Content-Type") or "").split(";")[0].strip().lower()
        # Read the body before anything else, refused or not: answering with unread
        # data still in the socket makes Windows reset the connection, and the
        # caller sees a network error instead of the 403.
        body = self._body()
        if not (self._host_ok() and self._origin_ok() and content_type == "application/json"):
            self._refuse()
            return
        try:
            handler = getattr(self, "_post_" + path.replace("/api/", "").replace("/", "_"), None)
            if handler is None:
                self._send(404, {"error_key": "error.unknown_path"})
                return
            handler(body)
        except Exception as error:  # noqa: BLE001
            traceback.print_exc()
            self._send(500, {"error": str(error)})

    # -- Products ----------------------------------------------------------
    def _post_product_save(self, body: dict) -> None:
        config = core.load_config()
        product = products.upsert(config, body.get("product") or {})
        core.save_config(config)
        self._send(200, {"ok": True, "product": product, "state": self._state()})

    def _post_product_select(self, body: dict) -> None:
        config = core.load_config()
        if not products.set_active(config, body.get("slug", "")):
            self._send(404, {"error_key": "error.product_not_found"})
            return
        core.save_config(config)
        self._send(200, {"ok": True, "state": self._state()})

    def _post_product_delete(self, body: dict) -> None:
        config = core.load_config()
        slug = body.get("slug", "")
        if not products.remove(config, slug):
            self._send(404, {"error_key": "error.product_not_found"})
            return
        core.save_config(config)
        core.forget_product(slug)
        self._send(200, {"ok": True, "state": self._state()})

    def _post_language_set(self, body: dict) -> None:
        """Stores the interface language. Nothing else has to change - no stored data
        holds a translated sentence, so the switch is purely a rendering decision."""
        config = core.load_config()
        config["ui_language"] = i18n.normalise(body.get("language"))
        core.save_config(config)
        self._send(200, {"ok": True, "ui_language": config["ui_language"]})

    # -- Analysis and strategy ---------------------------------------------
    def _post_analysis_run(self, body: dict) -> None:
        _config, _product, slug = self._active()
        if not slug:
            self._send(400, {"error_key": "error.no_product"})
            return
        if not _start_job("analyse"):
            self._send(409, {"error_key": "scan.busy"})
            return
        threading.Thread(target=_run_analysis, args=(slug, body.get("use_api")),
                         daemon=True).start()
        self._send(200, {"ok": True})

    def _post_strategy_build(self, body: dict) -> None:
        config, product, slug = self._active()
        if not slug:
            self._send(400, {"error_key": "error.no_product"})
            return
        plan = strategy.build(product, analysis.load(slug), config, use_api=body.get("use_api"))
        strategy.store(slug, plan)
        self._send(200, {"ok": True, "strategy": plan})

    # -- Assets ------------------------------------------------------------
    def _post_asset_build(self, body: dict) -> None:
        config, product, slug = self._active()
        if not slug:
            self._send(400, {"error_key": "error.no_product"})
            return
        asset_id = body.get("asset_id", "")
        if asset_id not in assets.ASSETS_BY_ID:
            self._send(404, {"error_key": "error.unknown_asset"})
            return
        asset = assets.build(asset_id, product, analysis.load(slug), config,
                             use_api=body.get("use_api"))
        assets.store(slug, asset)
        self._send(200, {"ok": True, "asset": asset})

    # -- Seed lists --------------------------------------------------------
    def _post_seeds_save(self, body: dict) -> None:
        _config, _product, slug = self._active()
        if not slug:
            self._send(400, {"error_key": "error.no_product"})
            return
        saved = seeds.save_seeds(slug, body.get("seeds") or {})
        self._send(200, {"ok": True, "seeds": saved})

    def _post_seeds_suggest(self, _body: dict) -> None:
        _config, _product, slug = self._active()
        if not slug:
            self._send(400, {"error_key": "error.no_product"})
            return
        if not _start_job("startlisten"):
            self._send(409, {"error_key": "scan.busy"})
            return
        threading.Thread(target=_run_seed_suggestion, args=(slug,), daemon=True).start()
        self._send(200, {"ok": True})

    # -- Scan --------------------------------------------------------------
    def _post_scan_start(self, body: dict) -> None:
        _config, _product, slug = self._active()
        if not slug:
            self._send(400, {"error_key": "error.no_product"})
            return
        if not _start_job("scan"):
            self._send(409, {"error_key": "scan.busy"})
            return
        platforms = body.get("platforms") or ["reddit", "lemmy", "forum",
                                              "hackernews", "lobsters"]
        threading.Thread(target=_run_scan, args=(platforms, slug), daemon=True).start()
        self._send(200, {"ok": True})

    def _post_run_all(self, body: dict) -> None:
        _config, _product, slug = self._active()
        if not slug:
            self._send(400, {"error_key": "error.no_product"})
            return
        if not _start_job("run"):
            self._send(409, {"error_key": "scan.busy"})
            return
        platforms = body.get("platforms") or ["reddit", "lemmy", "forum",
                                              "hackernews", "lobsters"]
        threading.Thread(target=_run_everything,
                         args=(slug, body.get("use_api"), platforms), daemon=True).start()
        self._send(200, {"ok": True})

    def _post_reddit_check(self, _body: dict) -> None:
        self._send(200, reddit_api.check(core.load_config()))

    def _post_lemmy_check(self, body: dict) -> None:
        config = core.load_config()
        core.set_delay(config["request_delay_seconds"])
        instance = (body.get("instance") or "").strip()
        self._send(200, lemmy_api.check(instance, config["user_agent"]))

    # -- Drafts ------------------------------------------------------------
    def _post_draft(self, body: dict) -> None:
        config, product, slug = self._active()
        entry = self._community(slug, body.get("community_id", ""))
        if not entry:
            self._send(404, {"error_key": "error.not_found"})
            return
        result = analysis.load(slug)
        angle = body.get("angle") or None
        if body.get("use_api"):
            try:
                draft = drafts.build_with_api(entry, product, config, result, angle)
            except Exception as error:  # noqa: BLE001 - fall back to the template
                draft = drafts.build(entry, product, result, angle, seed=body.get("seed"))
                draft["warning"] = i18n.message("draft.api_failed", error=error)
        else:
            draft = drafts.build(entry, product, result, angle, seed=body.get("seed"))
        self._send(200, draft)

    # -- Queue -------------------------------------------------------------
    def _post_queue_prepare(self, body: dict) -> None:
        config, product, slug = self._active()
        if not slug:
            self._send(400, {"error_key": "error.no_product"})
            return
        queue = prepare_queue(config, product, slug,
                              verdicts=body.get("verdicts"),
                              limit=body.get("limit"),
                              use_api=bool(body.get("use_api")))
        self._send(200, {"ok": True, "count": len(queue), "queue": queue})

    def _post_queue_add(self, body: dict) -> None:
        _config, _product, slug = self._active()
        queue = core.load_product(slug, "queue", [])
        item = body.get("draft") or {}
        item["status"] = "offen"
        queue = [entry for entry in queue if entry.get("community_id") != item.get("community_id")]
        queue.append(item)
        core.save_product(slug, "queue", queue)
        self._send(200, {"ok": True, "queue": queue})

    def _post_queue_remove(self, body: dict) -> None:
        _config, _product, slug = self._active()
        queue = [entry for entry in core.load_product(slug, "queue", [])
                 if entry.get("community_id") != body.get("community_id")]
        core.save_product(slug, "queue", queue)
        self._send(200, {"ok": True, "queue": queue})

    # -- Publishing --------------------------------------------------------
    def _post_assist(self, body: dict) -> None:
        config, _product, slug = self._active()
        entry = self._community(slug, body.get("community_id", ""))
        if not entry:
            self._send(404, {"error_key": "error.not_found"})
            return
        guard = publish.check_guard(entry, config, core.load_product(slug, "history", []))
        if entry.get("platform") == "reddit":
            url = publish.reddit_submit_url(entry["handle"], body.get("draft") or {})
        else:
            # Hacker News and Lobsters carry their own submission form; everything
            # else opens at the community itself.
            url = entry.get("submit_url") or entry.get("url", "")
        self._send(200, {"guard": guard, "url": url})

    def _post_publish_auto(self, body: dict) -> None:
        config, product, slug = self._active()
        draft = body.get("draft") or {}
        results = publish.run_auto_channels(config, draft, product)
        for result in results:
            publish.log_post(
                slug,
                {"id": f"auto:{result['kind']}", "name": result["channel"],
                 "platform": result["kind"]},
                draft, result["channel"],
                i18n.message("history.result.sent") if result["ok"]
                else i18n.message("history.result.failed", status=result["status"]),
            )
        self._send(200, {"results": results})

    def _post_log(self, body: dict) -> None:
        _config, _product, slug = self._active()
        entry = self._community(slug, body.get("community_id", "")) or {
            "id": body.get("community_id", "unknown"),
            "name": body.get("community", "unknown"),
            "platform": body.get("platform", "reddit"),
        }
        publish.log_post(slug, entry, body.get("draft") or {},
                         body.get("channel") or entry["name"],
                         i18n.message("history.result.posted"))
        queue = [item for item in core.load_product(slug, "queue", [])
                 if item.get("community_id") != entry["id"]]
        core.save_product(slug, "queue", queue)
        self._send(200, {"ok": True})

    # -- AI provider test ----------------------------------------------------
    def _post_ai_test(self, body: dict) -> None:
        """One tiny request to the chosen provider - key and model in one go."""
        config = core.load_config()
        provider = body.get("provider")
        if provider in core.AI_PROVIDERS:
            config.setdefault("ai", {})["provider"] = provider
            if not core._key(config, provider):
                self._send(200, {"ok": False, "detail": i18n.message("error.no_api_key")})
                return
        try:
            answer = core.ask_ai_json(config, "You answer with one JSON object and nothing else.",
                                      'Reply with exactly this JSON: {"ok": true}')
        except core.ClaudeError as error:
            self._send(200, {"ok": False, "detail": i18n.message(error.key, **error.params)})
            return
        except core.HttpError as error:
            self._send(200, {"ok": False, "detail": i18n.message("account.offline", error=error)})
            return
        used = core.ai_provider(config)
        model = (config.get(used) or {}).get("model") or core.AI_PROVIDERS[used]["model"]
        self._send(200, {"ok": bool(answer.get("ok")),
                         "detail": i18n.message("settings.ai_ok", provider=core.AI_PROVIDERS[used]["name"],
                                                model=model)})

    # -- The claude.ai route -------------------------------------------------
    def _claude_ai_context(self, body: dict) -> tuple[str, dict, dict, str] | None:
        config, product, slug = self._active()
        task = body.get("task", "")
        if not slug:
            self._send(400, {"error_key": "error.no_product"})
            return None
        if task not in CLAUDE_AI_TASKS:
            self._send(404, {"error_key": "error.unknown_path"})
            return None
        return task, config, product, slug

    def _post_claudeai_prompt(self, body: dict) -> None:
        """Step one: the finished request, for the user to paste into claude.ai."""
        context = self._claude_ai_context(body)
        if not context:
            return
        task, config, product, slug = context
        try:
            with core.claude_ai_capture():
                _claude_ai_task(task, body, config, product, slug)
        except core.PromptCaptured as captured:
            self._send(200, {"ok": True,
                             "text": core.claude_ai_text(captured.system, captured.prompt)})
            return
        except LookupError as error:
            self._send(404, {"error_key": str(error.args[0])})
            return
        # The task finished without ever asking Claude - nothing to take to claude.ai.
        self._send(409, {"error_key": "claudeai.nothing_to_ask"})

    def _post_claudeai_answer(self, body: dict) -> None:
        """Step two: the answer pasted back. Checked before anything is written - a
        half-copied answer must not replace a good analysis with an empty one."""
        context = self._claude_ai_context(body)
        if not context:
            return
        task, config, product, slug = context
        try:
            parsed = core.parse_claude_text(body.get("answer", ""))
        except core.ClaudeError as error:
            self._send(400, {"error_key": error.key})
            return
        try:
            with core.claude_ai_answer(parsed):
                result = _claude_ai_task(task, body, config, product, slug)
        except LookupError as error:
            self._send(404, {"error_key": str(error.args[0])})
            return
        except core.PromptCaptured:
            self._send(500, {"error_key": "error.no_json"})
            return
        self._send(200, {"ok": True, "result": result, "state": self._state()})

    # -- Mutexx account -----------------------------------------------------
    # The password passes through here on its way to the account server and is
    # never stored; what stays is the session, encrypted for this Windows user.
    def _account_call(self, action) -> None:
        try:
            result = action()
        except account.AccountError as error:
            self._send(400 if error.status != "offline" else 503,
                       {"error_message": error.message, "status": error.status})
            return
        self._send(200, {"ok": True, "account": result, "state": self._state()})

    def _post_account_signin(self, body: dict) -> None:
        config = core.load_config()
        self._account_call(lambda: account.sign_in(config, body.get("email", ""),
                                                   body.get("password", "")))

    def _post_account_signup(self, body: dict) -> None:
        config = core.load_config()
        self._account_call(lambda: account.sign_up(config, body.get("email", ""),
                                                   body.get("password", ""),
                                                   body.get("display_name", "")))

    def _post_account_signout(self, _body: dict) -> None:
        config = core.load_config()
        self._account_call(lambda: account.sign_out(config))

    def _post_account_sync(self, _body: dict) -> None:
        with _job_lock:
            busy = JOB["running"]
        if busy:
            self._send(409, {"error_key": "scan.busy"})
            return
        result = account.sync()
        self._send(200, {"ok": result.get("status") == "ok", "result": result,
                         "state": self._state()})

    # -- Configuration and communities -------------------------------------
    def _post_config(self, body: dict) -> None:
        config = core.load_config()
        merged = merge_config_update(config, body.get("config") or {})
        core.save_config(merged)
        core.set_delay(merged["request_delay_seconds"])
        self._send(200, {"ok": True, "config": public_config(merged)})

    def _post_webhook_add(self, body: dict) -> None:
        url = (body.get("url") or "").strip()
        if not url.startswith("https://"):
            self._send(400, {"error_key": "error.webhook_url"})
            return
        config = core.load_config()
        hooks = config["auto_channels"].setdefault("discord_webhooks", [])
        hooks.append({"name": (body.get("name") or "").strip() or "Discord", "url": url})
        core.save_config(config)
        self._send(200, {"ok": True, "config": public_config(config)})

    def _post_webhook_remove(self, body: dict) -> None:
        config = core.load_config()
        hooks = config["auto_channels"].get("discord_webhooks", [])
        index = body.get("index")
        if not isinstance(index, int) or not 0 <= index < len(hooks):
            self._send(404, {"error_key": "error.not_found"})
            return
        hooks.pop(index)
        core.save_config(config)
        self._send(200, {"ok": True, "config": public_config(config)})

    def _post_community_add(self, body: dict) -> None:
        config, product, slug = self._active()
        if not slug:
            self._send(400, {"error_key": "error.no_product"})
            return
        entries = core.load_product(slug, "communities", [])
        new = dict(body.get("community") or {})
        platform = new.get("platform") or "forum"
        handle = (new.get("handle") or "").strip().lstrip("/").removeprefix("r/")

        # A subreddit only needs its name - we build the URL and display name.
        if platform == "reddit":
            if not handle:
                self._send(400, {"error_key": "error.subreddit_missing"})
                return
            new["handle"] = handle
            new["name"] = f"r/{handle}"
            new["url"] = f"https://www.reddit.com/r/{handle}/"
            new["id"] = f"reddit:{handle}"
        elif platform == "lemmy":
            # 'community@instance', the way Lemmy itself writes it. Without the
            # instance there is nothing to point at - the same name exists on
            # dozens of them.
            handle = (new.get("handle") or "").lstrip("!")
            if "@" not in handle:
                self._send(400, {"error_key": "error.lemmy_handle"})
                return
            name, _, home = handle.partition("@")
            home = lemmy_api.normalise_instance(home)
            if not name or not home:
                self._send(400, {"error_key": "error.lemmy_handle"})
                return
            new["handle"] = f"{name}@{home}"
            new["name"] = f"!{name}@{home}"
            new["url"] = f"https://{home}/c/{name}"
            new["id"] = f"lemmy:{name}@{home}"
        elif not new.get("url"):
            self._send(400, {"error_key": "error.url_missing"})
            return
        else:
            new.setdefault("handle", new["url"])
            new.setdefault("name", new["url"])
            new.setdefault("id", f"{platform}:{new['url']}")

        # Rule text pasted in by hand goes through the same analysis as text fetched
        # through the API - same traffic light, same quotes.
        rules_text = (new.pop("rules_text", "") or "").strip()
        if rules_text:
            # The source is a catalogue key - the interface shows it in the
            # reader's language, like everything else it renders.
            new["analysis"] = rules.analyse({"communities.pasted_rules": rules_text})
            new["rules"] = [{"name": "communities.pasted_rules", "text": rules_text[:4000]}]
        else:
            new.setdefault("analysis", {"verdict": rules.UNKNOWN, "labels": [],
                                        "evidence": [], "explicitly_allowed": False})
            new.setdefault("rules", [])

        new["subscribers"] = int(new.get("subscribers") or 0)
        new.setdefault("title", "")
        new.setdefault("description", "")
        new.setdefault("posts_per_day", 0.0)
        keywords, weights, _terms = _scan_terms(product)
        new["fit_raw"] = discovery.fit_score(
            {"display_name": new["handle"], "title": new.get("title", ""),
             "public_description": new.get("description", ""), "description": rules_text},
            keywords, weights)
        new["manual"] = True

        entries = [entry for entry in entries if entry.get("id") != new["id"]]
        entries.append(new)
        discovery.score_all(entries)
        core.save_product(slug, "communities", entries)
        self._send(200, {"ok": True, "community": new})


# ---------------------------------------------------------------------------
# Startup
# ---------------------------------------------------------------------------

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
    core.load_config()  # creates config.json and migrates older versions
    # The desktop app picks the port itself and waits for it - it has to know
    # where to point its window before the server has said anything.
    wanted = os.environ.get("MUTEXX_ADVERTISER_PORT", "").strip()
    port = int(wanted) if wanted.isdigit() else _free_port()
    server = ThreadingHTTPServer(("127.0.0.1", port), Handler)
    url = f"http://127.0.0.1:{port}/"

    print("=" * 64)
    print(f"  Mutexx Advertiser {__version__}  -  a Mutexx Production tool")
    print("=" * 64)
    print(f"  Interface: {url}")
    print(f"  Data:      {core.HOME_DIR}")
    print("  To stop:   close this window or press Ctrl+C")
    print("=" * 64)

    account.start_background(lambda: JOB["running"])

    if not os.environ.get("MUTEXX_ADVERTISER_NO_BROWSER"):
        threading.Timer(1.0, lambda: webbrowser.open(url)).start()
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopped.")
        server.shutdown()
        sys.exit(0)


if __name__ == "__main__":
    main()
