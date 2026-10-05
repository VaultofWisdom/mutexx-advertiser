"""
Tests for the three AI providers behind core.ask_ai_json.

The modules that write never know which provider answered, so what has to hold is
the contract: one JSON object out, and every failure - a refusal, a cut-off answer,
an HTTP error - as a ClaudeError with a catalogue key, whichever provider it was.
No network: post_json is replaced and records what would have been sent.

Run:  python -m unittest discover -s tests
"""

from __future__ import annotations

import json
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from advertiser import core  # noqa: E402


def config(**keys: str) -> dict:
    out = {"user_agent": "test", "ai": {"provider": keys.pop("provider", "")}}
    for provider in core.AI_PROVIDERS:
        out[provider] = {"api_key": keys.get(provider, ""), "model": ""}
    return out


class Providers(unittest.TestCase):

    def setUp(self) -> None:
        self.sent: dict = {}
        self.answer = (200, "{}")
        self._post = core.post_json

        def fake(url, payload, *, user_agent, headers=None, timeout=25):
            self.sent = {"url": url, "payload": payload, "headers": headers or {}}
            return self.answer
        core.post_json = fake

    def tearDown(self) -> None:
        core.post_json = self._post

    # -- choosing ---------------------------------------------------------------

    def test_the_chosen_provider_writes_when_it_has_a_key(self) -> None:
        self.assertEqual(core.ai_provider(config(provider="gemini", gemini="g", openai="o")), "gemini")

    def test_a_chosen_provider_without_a_key_gives_way_to_one_with(self) -> None:
        self.assertEqual(core.ai_provider(config(provider="openai", gemini="g")), "gemini")

    def test_no_key_anywhere_means_not_ready(self) -> None:
        self.assertFalse(core.ai_ready(config()))
        self.assertTrue(core.ai_ready(config(openai="o")))

    def test_the_chat_route_is_ready_without_a_key(self) -> None:
        self.assertTrue(core.ai_ready(core.claude_ai_config(config(), "chatgpt")))
        self.assertEqual(core.ai_source(core.claude_ai_config(config(), "chatgpt")), "chat_chatgpt")

    # -- OpenAI -----------------------------------------------------------------

    def test_openai_request_and_answer(self) -> None:
        self.answer = (200, json.dumps({"status": "completed", "output": [
            {"type": "reasoning", "summary": []},
            {"type": "message", "content": [{"type": "output_text", "text": '{"ok": true}'}]}]}))
        self.assertEqual(core.ask_ai_json(config(openai="sk-1"), "SYS", "TASK"), {"ok": True})
        self.assertEqual(self.sent["url"], "https://api.openai.com/v1/responses")
        self.assertEqual(self.sent["headers"]["Authorization"], "Bearer sk-1")
        self.assertEqual(self.sent["payload"]["instructions"], "SYS")
        self.assertEqual(self.sent["payload"]["input"], "TASK")
        self.assertEqual(self.sent["payload"]["model"], core.AI_PROVIDERS["openai"]["model"])

    def test_openai_refusal(self) -> None:
        self.answer = (200, json.dumps({"status": "completed", "output": [
            {"type": "message", "content": [{"type": "refusal", "refusal": "no"}]}]}))
        with self.assertRaises(core.ClaudeError) as caught:
            core.ask_ai_json(config(openai="sk-1"), "s", "p")
        self.assertEqual(caught.exception.key, "error.api_refused")

    def test_openai_cut_off(self) -> None:
        self.answer = (200, json.dumps({"status": "incomplete", "output": [
            {"type": "message", "content": [{"type": "output_text", "text": '{"half": '}]}]}))
        with self.assertRaises(core.ClaudeError) as caught:
            core.ask_ai_json(config(openai="sk-1"), "s", "p")
        self.assertEqual(caught.exception.key, "error.api_truncated")

    def test_an_http_error_names_the_provider(self) -> None:
        self.answer = (401, '{"error": "bad key"}')
        with self.assertRaises(core.ClaudeError) as caught:
            core.ask_ai_json(config(openai="sk-1"), "s", "p")
        self.assertEqual(caught.exception.key, "error.ai_status")
        self.assertEqual(caught.exception.params["provider"], "OpenAI")

    # -- Gemini -----------------------------------------------------------------

    def test_gemini_request_and_answer(self) -> None:
        self.answer = (200, json.dumps({"candidates": [{"finishReason": "STOP", "content": {
            "parts": [{"text": "thinking ...", "thought": True}, {"text": '{"ok": 1}'}]}}]}))
        self.assertEqual(core.ask_ai_json(config(gemini="AIza"), "SYS", "TASK"), {"ok": 1})
        self.assertTrue(self.sent["url"].endswith(":generateContent"))
        self.assertIn(core.AI_PROVIDERS["gemini"]["model"], self.sent["url"])
        # The key goes in a header, never into the URL.
        self.assertEqual(self.sent["headers"]["x-goog-api-key"], "AIza")
        self.assertNotIn("AIza", self.sent["url"])
        self.assertEqual(self.sent["payload"]["systemInstruction"]["parts"][0]["text"], "SYS")

    def test_gemini_blocked_prompt(self) -> None:
        self.answer = (200, json.dumps({"promptFeedback": {"blockReason": "SAFETY"}}))
        with self.assertRaises(core.ClaudeError) as caught:
            core.ask_ai_json(config(gemini="AIza"), "s", "p")
        self.assertEqual(caught.exception.key, "error.api_refused")

    def test_gemini_cut_off(self) -> None:
        self.answer = (200, json.dumps({"candidates": [{"finishReason": "MAX_TOKENS",
                                                         "content": {"parts": [{"text": '{"a": '}]}}]}))
        with self.assertRaises(core.ClaudeError) as caught:
            core.ask_ai_json(config(gemini="AIza"), "s", "p")
        self.assertEqual(caught.exception.key, "error.api_truncated")

    # -- the modules do not care --------------------------------------------------

    def test_a_module_writes_with_whichever_provider_is_set_up(self) -> None:
        from advertiser import drafts
        self.answer = (200, json.dumps({"candidates": [{"content": {"parts": [
            {"text": '{"title": "From Gemini", "body": "Text"}'}]}}]}))
        entry = {"id": "x", "platform": "forum", "name": "Forum", "url": "https://f.example",
                 "analysis": {"verdict": "gruen", "labels": []}}
        product = {"slug": "p", "name": "P", "url": "https://p.example", "languages": ["en"]}
        draft = drafts.build_with_api(entry, product, config(gemini="AIza"), {})
        self.assertEqual(draft["title"], "From Gemini")
        self.assertEqual(draft["generated_by"], "gemini")


if __name__ == "__main__":
    unittest.main()
