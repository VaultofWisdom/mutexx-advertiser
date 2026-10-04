"""
Tests for the local server's boundary and for what the interface is allowed to see.

The server listens on 127.0.0.1, which keeps the network out - but not the browser.
Any page open in another tab can send requests to 127.0.0.1, and a page whose domain
is re-pointed at 127.0.0.1 (DNS rebinding) can even read the answers. Before 0.4 that
meant a hostile page could rewrite the configuration, start runs, post to the owned
channels and read every stored key. These tests hold the door shut from the outside,
against a real server on a free port.

The second half covers the keys themselves: they no longer travel to the browser at
all, and a settings save with an empty key field must keep the stored one.

Run:  python -m unittest discover -s tests
"""

from __future__ import annotations

import http.client
import json
import os
import re
import shutil
import sys
import tempfile
import threading
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from advertiser import core, i18n, publish, server  # noqa: E402

UI_PATH = os.path.join(os.path.dirname(server.__file__), "ui.html")


class TempHome(unittest.TestCase):
    """Points every path in core at a throwaway folder."""

    def setUp(self) -> None:
        self.home = tempfile.mkdtemp(prefix="advertiser-test-")
        self._saved = {name: getattr(core, name)
                       for name in ("HOME_DIR", "DATA_DIR", "PRODUCTS_DIR", "CONFIG_PATH")}
        core.HOME_DIR = self.home
        core.DATA_DIR = os.path.join(self.home, "data")
        core.PRODUCTS_DIR = os.path.join(core.DATA_DIR, "products")
        core.CONFIG_PATH = os.path.join(self.home, "config.json")
        os.makedirs(core.DATA_DIR, exist_ok=True)

    def tearDown(self) -> None:
        for name, value in self._saved.items():
            setattr(core, name, value)
        shutil.rmtree(self.home, ignore_errors=True)


class ServerBoundary(TempHome):

    def setUp(self) -> None:
        super().setUp()
        self.httpd = server.ThreadingHTTPServer(("127.0.0.1", 0), server.Handler)
        self.port = self.httpd.server_address[1]
        threading.Thread(target=self.httpd.serve_forever, daemon=True).start()

    def tearDown(self) -> None:
        self.httpd.shutdown()
        self.httpd.server_close()
        super().tearDown()

    def request(self, method: str, path: str, body: bytes | None = None,
                headers: dict | None = None) -> tuple[int, dict, bytes]:
        conn = http.client.HTTPConnection("127.0.0.1", self.port, timeout=10)
        all_headers = {"Host": f"127.0.0.1:{self.port}"}
        all_headers.update(headers or {})
        conn.request(method, path, body=body, headers=all_headers)
        response = conn.getresponse()
        data = response.read()
        result = response.status, dict(response.getheaders()), data
        conn.close()
        return result

    def post(self, path: str, payload: dict, **headers: str) -> tuple[int, dict, bytes]:
        merged = {"Content-Type": "application/json"}
        merged.update({key.replace("_", "-"): value for key, value in headers.items()})
        return self.request("POST", path, json.dumps(payload).encode(), merged)

    # -- The way in ---------------------------------------------------------

    def test_the_interface_loads(self) -> None:
        status, headers, body = self.request("GET", "/")
        self.assertEqual(status, 200)
        self.assertIn(b"Mutexx Advertiser", body)
        self.assertIn("frame-ancestors 'none'", headers.get("Content-Security-Policy", ""))

    def test_localhost_is_a_valid_host_too(self) -> None:
        status, _, _ = self.request("GET", "/api/job/status",
                                    headers={"Host": f"localhost:{self.port}"})
        self.assertEqual(status, 200)

    def test_a_foreign_host_cannot_read_the_state(self) -> None:
        """DNS rebinding: the page's own domain, now resolving to 127.0.0.1."""
        status, _, body = self.request("GET", "/api/state",
                                       headers={"Host": f"attacker.example:{self.port}"})
        self.assertEqual(status, 403)
        self.assertNotIn(b"config", body)

    def test_a_foreign_origin_cannot_change_anything(self) -> None:
        status, _, _ = self.post("/api/config", {"config": {"request_delay_seconds": 9}},
                                 Origin="https://attacker.example")
        self.assertEqual(status, 403)
        self.assertNotEqual(core.load_config().get("request_delay_seconds"), 9)

    def test_a_simple_form_post_is_refused(self) -> None:
        """text/plain is what a cross-site form can send without a preflight."""
        status, _, _ = self.request("POST", "/api/config",
                                    body=b'{"config":{"request_delay_seconds":9}}',
                                    headers={"Content-Type": "text/plain"})
        self.assertEqual(status, 403)

    def test_the_own_page_may_post(self) -> None:
        status, _, body = self.post("/api/config", {"config": {"request_delay_seconds": 2.5}},
                                    Origin=f"http://127.0.0.1:{self.port}")
        self.assertEqual(status, 200)
        self.assertEqual(json.loads(body)["config"]["request_delay_seconds"], 2.5)

    # -- What the browser gets to see --------------------------------------

    def test_state_carries_no_secret(self) -> None:
        config = core.load_config()
        config["anthropic"]["api_key"] = "sk-ant-SECRET-123"
        config["reddit"]["client_secret"] = "reddit-SECRET"
        config["auto_channels"]["discord_webhooks"] = [
            {"name": "News", "url": "https://discord.com/api/webhooks/1/TOKENTOKENTOKEN99"}]
        core.save_config(config)

        status, _, body = self.request("GET", "/api/state")
        self.assertEqual(status, 200)
        for secret in (b"sk-ant-SECRET-123", b"reddit-SECRET", b"TOKENTOKENTOKEN99"):
            self.assertNotIn(secret, body)
        state = json.loads(body)
        self.assertTrue(state["config"]["secrets_set"]["anthropic.api_key"])
        self.assertFalse(state["config"]["secrets_set"]["reddit.bot_password"])

    def test_webhooks_are_managed_without_the_browser_holding_them(self) -> None:
        status, _, _ = self.post("/api/webhook/add",
                                 {"name": "News", "url": "https://discord.com/api/webhooks/1/abcdefghijk"})
        self.assertEqual(status, 200)
        self.assertEqual(len(core.load_config()["auto_channels"]["discord_webhooks"]), 1)
        status, _, _ = self.post("/api/webhook/add", {"url": "javascript:alert(1)"})
        self.assertEqual(status, 400)
        status, _, _ = self.post("/api/webhook/remove", {"index": 0})
        self.assertEqual(status, 200)
        self.assertEqual(core.load_config()["auto_channels"]["discord_webhooks"], [])


class SecretsSurviveASave(unittest.TestCase):

    BASE = {"anthropic": {"api_key": "sk-ant-keep", "model": "m"},
            "reddit": {"client_id": "id", "client_secret": "sec", "bot_username": "",
                       "bot_password": "pw"},
            "auto_channels": {"discord_webhooks": [{"name": "a", "url": "https://x/y/zzzzzzzzzz"}],
                              "mastodon": {"instance": "m.social", "access_token": "tok"}}}

    def test_an_empty_field_keeps_the_stored_key(self) -> None:
        merged = server.merge_config_update(self.BASE, {
            "anthropic": {"api_key": "", "model": "claude-opus-5-5"},
            "reddit": {"client_secret": "", "bot_password": ""}})
        self.assertEqual(merged["anthropic"]["api_key"], "sk-ant-keep")
        self.assertEqual(merged["anthropic"]["model"], "claude-opus-5-5")
        self.assertEqual(merged["reddit"]["client_secret"], "sec")
        self.assertEqual(merged["reddit"]["bot_password"], "pw")

    def test_a_new_value_replaces_it(self) -> None:
        merged = server.merge_config_update(self.BASE, {"anthropic": {"api_key": "sk-ant-new"}})
        self.assertEqual(merged["anthropic"]["api_key"], "sk-ant-new")

    def test_removing_is_explicit(self) -> None:
        merged = server.merge_config_update(self.BASE, {"clear_secrets": ["anthropic.api_key"]})
        self.assertEqual(merged["anthropic"]["api_key"], "")
        self.assertEqual(merged["reddit"]["client_secret"], "sec")

    def test_masked_webhooks_sent_back_do_not_overwrite_the_real_ones(self) -> None:
        public = server.public_config(self.BASE)
        merged = server.merge_config_update(self.BASE, {"auto_channels": public["auto_channels"]})
        self.assertEqual(merged["auto_channels"]["discord_webhooks"],
                         self.BASE["auto_channels"]["discord_webhooks"])
        self.assertEqual(merged["auto_channels"]["mastodon"]["access_token"], "tok")

    def test_public_config_does_not_touch_the_original(self) -> None:
        server.public_config(self.BASE)
        self.assertEqual(self.BASE["anthropic"]["api_key"], "sk-ant-keep")

    def test_a_masked_webhook_still_tells_two_apart(self) -> None:
        masked = server.mask_webhook("https://discord.com/api/webhooks/123/abcdefghijklmnop")
        self.assertTrue(masked.startswith("https://discord.com/api/webhooks/123/abcd"))
        self.assertNotIn("efghijklmno", masked)


class PostsKeepTheirLink(unittest.TestCase):
    """The link sits at the end of nearly every post, so cutting at the limit cut the
    one part the post exists for."""

    LINK = "https://example.com/product"

    def test_short_posts_are_untouched(self) -> None:
        self.assertEqual(publish.fit_post("Title", "Body " + self.LINK, 500, self.LINK),
                         "Title\n\nBody " + self.LINK)

    def test_a_long_post_is_shortened_but_keeps_the_link(self) -> None:
        body = ("A sentence that goes on. " * 60) + self.LINK
        text = publish.fit_post("Title", body, 480, self.LINK)
        self.assertLessEqual(len(text), 480)
        self.assertTrue(text.endswith(self.LINK))
        self.assertEqual(text.count(self.LINK), 1)

    def test_without_a_link_it_is_simply_shortened(self) -> None:
        text = publish.fit_post("Title", "word " * 400, 300)
        self.assertLessEqual(len(text), 300)


class DataHome(unittest.TestCase):

    def test_an_override_wins(self) -> None:
        saved = os.environ.get("MUTEXX_ADVERTISER_HOME")
        os.environ["MUTEXX_ADVERTISER_HOME"] = "/tmp/somewhere"
        try:
            self.assertEqual(core._home(), "/tmp/somewhere")
        finally:
            if saved is None:
                os.environ.pop("MUTEXX_ADVERTISER_HOME")
            else:
                os.environ["MUTEXX_ADVERTISER_HOME"] = saved

    def test_an_installed_copy_never_writes_next_to_itself(self) -> None:
        """With no config.json and no 'portable' marker in the app folder, the data
        goes to the user's folder - C:\\Program Files is not writable."""
        saved = (core.APP_DIR, os.environ.pop("MUTEXX_ADVERTISER_HOME", None))
        empty = tempfile.mkdtemp()
        try:
            core.APP_DIR = empty
            self.assertNotEqual(os.path.abspath(core._home()), os.path.abspath(empty))
            open(os.path.join(empty, "portable"), "w").close()
            self.assertEqual(core._home(), empty)
        finally:
            core.APP_DIR = saved[0]
            if saved[1] is not None:
                os.environ["MUTEXX_ADVERTISER_HOME"] = saved[1]
            shutil.rmtree(empty, ignore_errors=True)


class ClaudeRequest(unittest.TestCase):
    """One place builds every request to the Anthropic API. These pin what it sends
    and how it reads what comes back - without the network."""

    def setUp(self) -> None:
        self.sent: dict = {}
        self.answer: tuple[int, str] = (200, "{}")
        self._post = core.post_json

        def fake(url, payload, *, user_agent, headers=None, timeout=25):
            self.sent = {"url": url, "payload": payload, "headers": headers, "timeout": timeout}
            return self.answer
        core.post_json = fake

    def tearDown(self) -> None:
        core.post_json = self._post

    def config(self, model: str = "") -> dict:
        return {"anthropic": {"api_key": "k", "model": model}, "user_agent": "test"}

    def reply(self, text: str, stop: str = "end_turn") -> None:
        self.answer = (200, json.dumps({"stop_reason": stop,
                                        "content": [{"type": "thinking", "thinking": ""},
                                                    {"type": "text", "text": text}]}))

    def test_the_default_model_and_its_fallback(self) -> None:
        self.reply('{"ok": true}')
        self.assertEqual(core.ask_claude_json(self.config(), "sys", "prompt"), {"ok": True})
        self.assertEqual(self.sent["payload"]["model"], core.DEFAULT_MODEL)
        self.assertEqual(self.sent["payload"]["fallbacks"], "default")
        self.assertEqual(self.sent["headers"]["anthropic-beta"], "server-side-fallback-2026-07-01")
        self.assertGreaterEqual(self.sent["timeout"], 120)

    def test_other_models_get_a_plain_request(self) -> None:
        self.reply('{"ok": true}')
        core.ask_claude_json(self.config("claude-haiku-4-5"), "sys", "prompt")
        self.assertNotIn("fallbacks", self.sent["payload"])
        self.assertNotIn("anthropic-beta", self.sent["headers"])

    def test_a_refusal_says_so(self) -> None:
        self.answer = (200, json.dumps({"stop_reason": "refusal", "content": []}))
        with self.assertRaises(core.ClaudeError) as caught:
            core.ask_claude_json(self.config(), "sys", "prompt")
        self.assertEqual(caught.exception.key, "error.api_refused")

    def test_a_cut_off_answer_says_so(self) -> None:
        self.reply('{"half": ', stop="max_tokens")
        with self.assertRaises(core.ClaudeError) as caught:
            core.ask_claude_json(self.config(), "sys", "prompt")
        self.assertEqual(caught.exception.key, "error.api_truncated")

    def test_no_key_no_request(self) -> None:
        with self.assertRaises(core.ClaudeError):
            core.ask_claude_json({"anthropic": {"api_key": ""}}, "sys", "prompt")
        self.assertEqual(self.sent, {})


class InterfaceIsTranslated(unittest.TestCase):
    """Every key the interface asks for exists - in every language. A missing one shows
    up as its own name in the middle of the page."""

    def test_every_key_in_the_interface_exists(self) -> None:
        with open(UI_PATH, encoding="utf-8") as handle:
            source = handle.read()
        keys = set(re.findall(r"""\bt\(\s*'([a-z0-9_]+\.[a-z0-9_.]*[a-z0-9_])'""", source))
        keys |= set(re.findall(r'data-i18n(?:-html|-ph|-title)?="([a-z0-9_.]+)"', source))
        keys |= set(re.findall(r"label\(\$\('\w+'\), '[a-z]*', '([a-z0-9_.]+)'\)", source))
        keys |= set(re.findall(r"(?:group|kpi\('\w+',|listCard\()\s*:?\s*'([a-z0-9_]+\.[a-z0-9_.]+)'", source))
        tabs = re.search(r"const TAB_ICON = \{(.*?)\};", source, re.S).group(1)
        for tab in re.findall(r"(\w+):'", tabs):
            keys |= {f"tab.{tab}", f"page.{tab}.sub"}
        self.assertGreater(len(keys), 250)
        for language in i18n.LANGUAGES:
            missing = sorted(key for key in keys if key not in i18n.CATALOG[language])
            self.assertEqual(missing, [], f"missing in {language}")


if __name__ == "__main__":
    unittest.main()
