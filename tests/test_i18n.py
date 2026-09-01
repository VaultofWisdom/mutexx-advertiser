"""
Tests for the translation layer.

A half-translated interface is worse than a monolingual one: the user cannot tell
whether something is missing or merely different. These tests make the failure loud
instead of subtle.

The one that matters most is the last group: it walks everything the backend can
produce - channel plans, assets, drafts, guard reasons - and insists that every
single string resolves in every language. A key that exists nowhere renders as the
key itself, which is exactly what that check looks for.

Run:  python -m unittest discover -s tests
"""

from __future__ import annotations

import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from advertiser import (assets, drafts, i18n, products, publish,  # noqa: E402
                        rules, strategy)

LANGUAGES = list(i18n.LANGUAGES)


def looks_untranslated(text: str) -> bool:
    """A rendered string that still looks like a key. Keys are dotted, lower case and
    free of spaces - real sentences are not."""
    text = (text or "").strip()
    if not text:
        return True
    return "." in text and " " not in text and text.lower() == text


class CatalogueIsComplete(unittest.TestCase):

    def test_english_is_the_reference(self) -> None:
        self.assertEqual(i18n.DEFAULT_LANGUAGE, "en")
        self.assertIn("de", i18n.LANGUAGES)

    def test_no_missing_translations(self) -> None:
        for language, keys in i18n.missing().items():
            with self.subTest(language=language):
                self.assertEqual(keys, [], f"{len(keys)} keys missing in {language}")

    def test_placeholders_agree(self) -> None:
        """A German sentence that drops {count} silently loses the number."""
        self.assertEqual(i18n.unused_parameters(), [])

    def test_no_entry_is_empty(self) -> None:
        for language, strings in i18n.CATALOG.items():
            for key, value in strings.items():
                with self.subTest(language=language, key=key):
                    self.assertTrue(value.strip(), f"{key} is empty in {language}")

    def test_an_unknown_key_is_conspicuous(self) -> None:
        self.assertEqual(i18n.t("nope.not.here", "en"), "nope.not.here")

    def test_an_unknown_language_falls_back_to_english(self) -> None:
        self.assertEqual(i18n.t("tab.product", "fr"), i18n.t("tab.product", "en"))


class MessagesStaySwitchable(unittest.TestCase):

    def test_parameters_are_substituted(self) -> None:
        stored = i18n.message("strategy.warn.one_channel", budget=120)
        for language in LANGUAGES:
            with self.subTest(language=language):
                self.assertIn("120", i18n.render(stored, language))

    def test_nested_messages(self) -> None:
        """A language name inside a sentence has to appear in the READING language,
        not as its own endonym - otherwise German says 'Englishsprachig'."""
        stored = i18n.message("draft.language_warning",
                              community_language=i18n.message("language.en"),
                              product_language=i18n.message("language.de"))
        self.assertIn("English", i18n.render(stored, "en"))
        self.assertIn("German", i18n.render(stored, "en"))
        self.assertIn("englisch", i18n.render(stored, "de"))
        self.assertIn("deutsch", i18n.render(stored, "de"))

    def test_lists_are_joined(self) -> None:
        stored = i18n.message("list.join", items=[
            i18n.message("tab.product"), i18n.message("tab.strategy")])
        self.assertEqual(i18n.render(stored, "en"), "Product, Strategy")
        self.assertEqual(i18n.render(stored, "de"), "Produkt, Strategie")

    def test_plain_text_entries_pass_through(self) -> None:
        """Data written before this module existed must still show up."""
        self.assertEqual(i18n.render("a plain sentence", "de"), "a plain sentence")


class EveryKeyTheBackendUses(unittest.TestCase):
    """The catalogue and the code have to agree. Every key a module names must exist."""

    def _check(self, key: str, where: str) -> None:
        for language in LANGUAGES:
            with self.subTest(language=language, where=where, key=key):
                self.assertIn(key, i18n.CATALOG[language], f"{key} missing ({where})")

    def test_channel_catalogue(self) -> None:
        for channel in strategy.CHANNELS:
            for part in ("name", "what", "first_step", "risk"):
                self._check(strategy.text_key(channel["id"], part), "channel")
            self._check("effort." + channel["effort"], "effort")
            self._check("lead." + channel["lead_time"], "lead time")
            self._check("automation." + channel["automation"], "automation")
            self._check("kind.badge." + channel["kind"], "kind")

    def test_assets(self) -> None:
        for asset in assets.ASSETS:
            spec = assets.spec_for(asset["id"])
            self._check(spec["name_key"], "asset name")
            self._check(spec["what_key"], "asset description")
            if spec["note_key"]:
                self._check(spec["note_key"], "asset note")
            for field in spec["fields"]:
                self._check(field["label_key"], "asset field")
                self._check(field["hint_key"], "asset hint")

    def test_master_data(self) -> None:
        for key in products.CATEGORIES.values():
            self._check(key, "category")
        for key in products.CATEGORIES:
            self._check("category.short." + key, "category short form")
        for key in products.PRICE_MODELS.values():
            self._check(key, "pricing")
        for key in products.TONES.values():
            self._check(key, "tone")
        for key in drafts.ANGLES.values():
            self._check(key, "angle")
        for key in rules.VERDICT_TEXT.values():
            self._check(key, "verdict")
            self._check(key.replace("verdict.", "verdict.short."), "verdict short form")

    def test_rule_labels_and_requirements(self) -> None:
        for _level, label, _pattern in rules._PATTERNS:
            self._check(label, "rule label")
        for rule_key, requirement in drafts._REQUIREMENT_FOR.items():
            self._check(rule_key, "requirement source")
            self._check(requirement, "requirement")
        for key in ("requirement.nsfw", "requirement.read_rules",
                    "rule.explicitly_allowed"):
            self._check(key, "requirement")


class EverythingRendersInBothLanguages(unittest.TestCase):
    """The end-to-end check: run the machinery and insist every produced string turns
    into a real sentence in every language."""

    def _assert_readable(self, text: str, language: str, where: str) -> None:
        self.assertFalse(looks_untranslated(text),
                         f"untranslated in {language} ({where}): {text!r}")

    def test_strategy_plan(self) -> None:
        for category in products.CATEGORIES:
            product = products.normalise({"name": "Test", "category": category,
                                          "price_model": "shop",
                                          "budget_monthly_eur": 800})
            plan = strategy.build(product, {}, {}, use_api=False)
            for language in LANGUAGES:
                self._assert_readable(i18n.render(plan["summary"], language),
                                      language, "summary")
                for warning in plan["warnings"]:
                    self._assert_readable(i18n.render(warning, language),
                                          language, "warning")
                for item in plan["first_week"]:
                    self._assert_readable(i18n.render(item, language),
                                          language, "first week")
                for channel in plan["channels"]:
                    for part in ("name_key", "what_key", "first_step_key", "risk_key",
                                 "effort_key", "lead_time_key", "automation_key",
                                 "kind_key"):
                        self._assert_readable(i18n.t(channel[part], language),
                                              language, channel["id"] + "/" + part)
                    for reason in channel["why"]:
                        self._assert_readable(i18n.render(reason, language),
                                              language, "reason")
                for entry in plan["rejected"]:
                    self._assert_readable(i18n.render(entry["blocked"], language),
                                          language, "rejection")
                for phase in plan["phases"]:
                    self._assert_readable(i18n.t(phase["name_key"], language),
                                          language, "phase")
                    self._assert_readable(i18n.t(phase["note_key"], language),
                                          language, "phase note")
                for row in plan["budget_plan"]:
                    self._assert_readable(i18n.t(row["name_key"], language),
                                          language, "budget row")

    def test_assets(self) -> None:
        product = products.normalise({
            "name": "Test", "url": "https://example.com", "category": "software_desktop",
            "price_model": "freemium", "one_liner": "A tool that does one job"})
        for spec in assets.available(product):
            asset = assets.build(spec["id"], product, {}, {}, use_api=False)
            for language in LANGUAGES:
                self._assert_readable(i18n.t(asset["name_key"], language),
                                      language, "asset name")
                for warning in asset["warnings"]:
                    self._assert_readable(i18n.render(warning, language),
                                          language, "asset warning")

    def test_draft_and_requirements(self) -> None:
        product = products.normalise({"name": "Test", "one_liner": "A tool",
                                      "languages": ["de"]})
        entry = {"id": "reddit:x", "name": "r/x", "handle": "x", "platform": "reddit",
                 "description": "test", "analysis": {"verdict": "gelb", "evidence": [],
                 "labels": ["rule.ratio", "rule.flair", "rule.spam_ban"]}}
        draft = drafts.build(entry, product, {})
        for language in LANGUAGES:
            for requirement in draft["requirements"]:
                self._assert_readable(i18n.t(requirement, language),
                                      language, "requirement")
            self._assert_readable(i18n.render(draft["warning"], language),
                                  language, "language warning")
            self._assert_readable(i18n.t(draft["angle_label"], language),
                                  language, "angle")

    def test_safety_catch(self) -> None:
        config = {"safety": {"max_reddit_posts_per_day": 1,
                             "min_days_between_same_subreddit": 45}}
        entry = {"id": "reddit:x", "platform": "reddit",
                 "analysis": {"verdict": "rot"}}
        history = [{"community_id": "reddit:x", "platform": "reddit", "ts": 0}]
        guard = publish.check_guard(entry, config, history)
        self.assertFalse(guard["allowed"])
        for language in LANGUAGES:
            for reason in guard["reasons"]:
                self._assert_readable(i18n.render(reason, language), language, "guard")


class ManualFollowsTheSwitch(unittest.TestCase):

    def test_both_languages_share_the_chapters(self) -> None:
        from advertiser import manual
        english = manual.chapters("en")
        german = manual.chapters("de")
        self.assertEqual([c["id"] for c in english], [c["id"] for c in german])
        self.assertGreater(len(english), 10)

    def test_no_chapter_is_empty(self) -> None:
        from advertiser import manual
        for language in LANGUAGES:
            for chapter in manual.chapters(language):
                with self.subTest(language=language, chapter=chapter["id"]):
                    self.assertTrue(chapter["title"].strip())
                    self.assertGreater(len(chapter["html"].strip()), 120)

    def test_titles_differ_between_languages(self) -> None:
        """If the German titles were identical to the English ones, the manual was
        never actually translated."""
        from advertiser import manual
        english = {c["id"]: c["title"] for c in manual.chapters("en")}
        german = {c["id"]: c["title"] for c in manual.chapters("de")}
        same = [key for key in english if english[key] == german[key]]
        self.assertLessEqual(len(same), 2, f"untranslated chapter titles: {same}")


if __name__ == "__main__":
    unittest.main()
