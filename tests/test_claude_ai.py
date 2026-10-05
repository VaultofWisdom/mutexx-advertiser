"""
Tests for the claude.ai route: writing with the user's own Claude subscription.

The app may not sign anyone in with claude.ai or spend their subscription for them,
so the route is manual by design - the request goes out through the clipboard and
the answer comes back the same way. What these tests hold on to is that it is the
SAME code path as the API: the request is built by the module that would send it,
and the pasted answer runs through the same checks as an API answer.

No network: nothing on this route is ever sent anywhere.

Run:  python -m unittest discover -s tests
"""

from __future__ import annotations

import json
import os
import shutil
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from advertiser import analysis, core, server  # noqa: E402

PRODUCT = {"slug": "notes", "name": "Mutexx Notes", "url": "", "one_liner": "Local notes.",
           "description": "Markdown notes with a graph view.", "category": "software_desktop",
           "price_model": "free", "languages": ["en"], "regions": ["DE"],
           "keywords": ["note taking"], "audience": "people who take notes"}
COMMUNITY = {"id": "lemmy:notes@lemmy.world", "platform": "lemmy", "name": "!notes@lemmy.world",
             "handle": "notes@lemmy.world", "url": "https://lemmy.world/c/notes",
             "description": "Note-taking apps", "title": "Notes", "subscribers": 900,
             "analysis": {"verdict": "gruen", "labels": [], "evidence": []}}
CONFIG = {"anthropic": {"api_key": "", "model": ""}, "user_agent": "test",
          "request_delay_seconds": 0.5}


class ClaudeAiRoute(unittest.TestCase):

    def setUp(self) -> None:
        self.home = tempfile.mkdtemp()
        self._saved = {name: getattr(core, name)
                       for name in ("HOME_DIR", "DATA_DIR", "PRODUCTS_DIR", "CONFIG_PATH")}
        core.HOME_DIR = self.home
        core.DATA_DIR = os.path.join(self.home, "data")
        core.PRODUCTS_DIR = os.path.join(core.DATA_DIR, "products")
        core.CONFIG_PATH = os.path.join(self.home, "config.json")
        core.save_product("notes", "communities", [COMMUNITY])
        # Nothing on this route may touch the network.
        self._post = core.post_json
        core.post_json = lambda *a, **k: self.fail("the claude.ai route sent a request")

    def tearDown(self) -> None:
        core.post_json = self._post
        for name, value in self._saved.items():
            setattr(core, name, value)
        shutil.rmtree(self.home, ignore_errors=True)

    def capture(self, task: str, **body) -> str:
        with self.assertRaises(core.PromptCaptured) as caught:
            with core.claude_ai_capture():
                server._claude_ai_task(task, body, dict(CONFIG), dict(PRODUCT), "notes")
        return core.claude_ai_text(caught.exception.system, caught.exception.prompt)

    def answer(self, task: str, parsed: dict, **body):
        with core.claude_ai_answer(parsed):
            return server._claude_ai_task(task, body, dict(CONFIG), dict(PRODUCT), "notes")

    # -- step one: the request ------------------------------------------------

    def test_every_task_produces_a_request_without_an_api_key(self) -> None:
        for task, body in (("draft", {"community_id": COMMUNITY["id"]}),
                           ("asset", {"asset_id": "seo_meta"}),
                           ("analysis", {}), ("strategy", {}), ("seeds", {})):
            with self.subTest(task=task):
                text = self.capture(task, **body)
                self.assertIn("Mutexx Notes", text)
                self.assertIn("JSON", text)

    def test_the_key_placeholder_never_reaches_the_stored_config(self) -> None:
        self.capture("draft", community_id=COMMUNITY["id"])
        self.assertFalse(os.path.exists(core.CONFIG_PATH))

    # -- step two: the answer -------------------------------------------------

    def test_a_pasted_draft_is_used(self) -> None:
        draft = self.answer("draft", {"title": "Notes that link themselves",
                                      "body": "A local-first note app."},
                            community_id=COMMUNITY["id"])
        self.assertEqual(draft["title"], "Notes that link themselves")
        self.assertEqual(draft["generated_by"], "chat_claudeai")

    def test_pasted_ad_copy_still_meets_the_character_limits(self) -> None:
        """The same check as for API copy - a chat answer counts characters no
        better than an API answer does."""
        asset = self.answer("asset", {"page_title": ["x" * 200], "meta_description": ["y" * 400]},
                            asset_id="seo_meta")
        self.assertEqual(asset["generated_by"], "chat_claudeai")
        for field in asset["spec"]:
            for entry in asset["fields"].get(field["key"], []):
                self.assertLessEqual(len(entry["text"]), field["limit"])

    def test_a_pasted_analysis_is_stored(self) -> None:
        self.answer("analysis", {"value_props": ["Works offline"], "search_terms": ["markdown app"],
                                 "positioning": "Notes that stay on your disk."})
        stored = analysis.load("notes")
        self.assertEqual(stored["value_props"], ["Works offline"])
        self.assertIn("markdown app", stored["search_terms"])

    def test_seed_suggestions_are_added_not_replacing(self) -> None:
        core.save_product("notes", "seeds", {"subreddits": ["ObsidianMD"], "forums": [],
                                             "lemmy_instances": []})
        saved = self.answer("seeds", {"subreddits": ["PKMS"],
                                      "forums": [{"url": "https://forum.example.org", "name": "F"}]})
        self.assertEqual(saved["subreddits"][:2], ["ObsidianMD", "PKMS"])

    # -- what comes back from a chat -----------------------------------------

    def test_a_chat_answer_with_a_code_block_and_a_sentence_is_read(self) -> None:
        text = 'Here is the JSON:\n```json\n{"title": "T", "body": "B"}\n```\nHope it helps!'
        self.assertEqual(core.parse_claude_text(text), {"title": "T", "body": "B"})

    def test_an_answer_without_json_is_refused_before_anything_is_written(self) -> None:
        with self.assertRaises(core.ClaudeError) as caught:
            core.parse_claude_text("Sorry, I can't help with that.")
        self.assertEqual(caught.exception.key, "error.no_json")

    def test_outside_the_route_nothing_changes(self) -> None:
        """Without the context the API path is the API path: no key, no request."""
        with self.assertRaises(core.ClaudeError):
            core.ask_claude_json({"anthropic": {"api_key": ""}}, "s", "p")


if __name__ == "__main__":
    unittest.main()
