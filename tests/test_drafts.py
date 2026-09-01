"""
Tests fuer Entwuerfe und ProductProfiles.

Der wichtigste Fall ist der langweiligste: eine Vorlage darf niemals einen
unausgefuellten Platzhalter oder eine erfundene Tatsache ausliefern. Ein Entwurf
mit "{one_liner}" im Text ist peinlich; ein Entwurf, der bei einem Bezahlprodukt
"kostenlos" behauptet, ist eine Falschaussage im eigenen Namen.

Ausfuehren:  python -m unittest discover -s tests
"""

from __future__ import annotations

import os
import re
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from advertiser import drafts, i18n, products  # noqa: E402

PLATZHALTER = re.compile(r"\{[a-z_]+\}")

COMMUNITY = {
    "id": "reddit:test", "name": "r/test", "handle": "test", "platform": "reddit",
    "title": "Test", "description": "eine Testcommunity", "subscribers": 5000,
    "analysis": {"verdict": "gruen", "labels": [], "evidence": []},
}


def produkt(**felder) -> dict:
    basis = {"name": "Testprodukt", "category": "software_desktop", "price_model": "free"}
    basis.update(felder)
    return products.normalise(basis)


class TemplatesAreAlwaysComplete(unittest.TestCase):

    def test_no_unfilled_placeholders(self) -> None:
        """Every angle, both languages, every pricing model - and once with nothing
        but a name. That is the state right after creating a profile."""
        for sprache in ("de", "en"):
            for preismodell in products.PRICE_MODELS:
                for blickwinkel in drafts.ANGLES:
                    p = produkt(price_model=preismodell, languages=[sprache])
                    entwurf = drafts.build(COMMUNITY, p, {}, blickwinkel, seed=1,
                                           language=sprache)
                    with self.subTest(sprache=sprache, preismodell=preismodell,
                                      blickwinkel=blickwinkel):
                        self.assertIsNone(PLATZHALTER.search(entwurf["title"]),
                                          f"Platzhalter im Titel: {entwurf['title']}")
                        self.assertIsNone(PLATZHALTER.search(entwurf["body"]),
                                          f"Platzhalter im Text: {entwurf['body'][:200]}")

    def test_no_empty_title_or_body(self) -> None:
        for blickwinkel in drafts.ANGLES:
            entwurf = drafts.build(COMMUNITY, produkt(), {}, blickwinkel, seed=2)
            with self.subTest(blickwinkel=blickwinkel):
                self.assertGreater(len(entwurf["title"].strip()), 8)
                self.assertGreater(len(entwurf["body"].strip()), 80)

    def test_no_triple_blank_lines(self) -> None:
        """If a block is missing - the value points, say - no gap may be left behind."""
        for blickwinkel in drafts.ANGLES:
            entwurf = drafts.build(COMMUNITY, produkt(), {}, blickwinkel, seed=3)
            with self.subTest(blickwinkel=blickwinkel):
                self.assertNotIn("\n\n\n", entwurf["body"])


class NothingInventedInDrafts(unittest.TestCase):

    def test_paid_product_is_never_called_free(self) -> None:
        for preismodell in ("one_time", "subscription", "shop"):
            for blickwinkel in drafts.ANGLES:
                p = produkt(price_model=preismodell, price_point="19,90 EUR", languages=["de"])
                entwurf = drafts.build(COMMUNITY, p, {}, blickwinkel, seed=4, language="de")
                text = (entwurf["title"] + " " + entwurf["body"]).lower()
                with self.subTest(preismodell=preismodell, blickwinkel=blickwinkel):
                    self.assertNotIn("kostenlos, ohne konto", text)
                    self.assertNotIn("free, no account", text)

    def test_no_version_line_without_a_version(self) -> None:
        entwurf = drafts.build(COMMUNITY, produkt(version=""), {}, "resource", seed=5)
        self.assertNotIn("Version", entwurf["body"])

    def test_requirements_are_keys(self) -> None:
        """The checklist has to read in the operator's language, whatever language the
        post itself is written in."""
        gesperrt = dict(COMMUNITY, analysis={"verdict": "gelb", "evidence": [],
                                             "labels": ["rule.ratio", "rule.flair"]})
        entwurf = drafts.build(gesperrt, produkt(), {})
        self.assertEqual(entwurf["requirements"],
                         ["requirement.ratio", "requirement.flair"])
        for language in i18n.LANGUAGES:
            for requirement in entwurf["requirements"]:
                with self.subTest(language=language, requirement=requirement):
                    self.assertNotEqual(i18n.t(requirement, language), requirement)

    def test_value_points_come_from_the_analysis(self) -> None:
        analyse = {"value_props": ["Laeuft ohne Installation.", "Keine Telemetrie."]}
        entwurf = drafts.build(COMMUNITY, produkt(languages=["de"]), analyse, "resource",
                               seed=6, language="de")
        self.assertIn("Laeuft ohne Installation", entwurf["body"])
        self.assertIn("Keine Telemetrie", entwurf["body"])


class LanguageAndWarning(unittest.TestCase):

    def test_german_product_in_english_community_warns(self) -> None:
        """Templates cannot translate. Rather than shipping a half-German post they
        have to say so openly - in the operator's language."""
        entwurf = drafts.build(COMMUNITY, produkt(languages=["de"]), {})
        self.assertEqual(entwurf["language"], "de")
        self.assertEqual(entwurf["community_language"], "en")
        self.assertEqual(entwurf["warning"]["key"], "draft.language_warning")
        self.assertIn("translate", i18n.render(entwurf["warning"], "en"))
        self.assertIn("uebersetzen".replace("ue", "\u00fc"),
                      i18n.render(entwurf["warning"], "de"))

    def test_a_matching_language_does_not_warn(self) -> None:
        entwurf = drafts.build(COMMUNITY, produkt(languages=["en", "de"]), {})
        self.assertEqual(entwurf["language"], "en")
        self.assertNotIn("warning", entwurf)

    def test_a_german_forum_is_recognised(self) -> None:
        forum = dict(COMMUNITY, id="forum:x.de", name="Beispielforum",
                     url="https://www.beispiel.de/forum/", platform="forum")
        self.assertEqual(drafts.community_language(forum), "de")


class RedVerdictIsVisible(unittest.TestCase):

    def test_the_warning_precedes_the_body(self) -> None:
        gesperrt = dict(COMMUNITY, analysis={"verdict": "rot", "labels": [], "evidence": []})
        entwurf = drafts.build(gesperrt, produkt(), {})
        self.assertTrue(entwurf["body"].startswith("### Diese Community verbietet"))


class ProductProfiles(unittest.TestCase):

    def test_slug_keeps_umlauts_as_letters(self) -> None:
        self.assertEqual(products.slugify("Bürosoftware für Köln"), "buerosoftware-fuer-koeln")
        self.assertEqual(products.slugify("Maß & Zahl"), "mass-zahl")

    def test_slug_is_never_empty(self) -> None:
        for name in ("", "   ", "!!!", "***"):
            with self.subTest(name=name):
                self.assertTrue(products.slugify(name))

    def test_identical_names_get_their_own_slugs(self) -> None:
        config = {"products": []}
        erste = products.upsert(config, {"name": "Mein Werkzeug"})
        zweite = products.upsert(config, {"name": "Mein Werkzeug"})
        self.assertNotEqual(erste["slug"], zweite["slug"])
        self.assertEqual(len(config["products"]), 2)

    def test_editing_creates_no_second_profile(self) -> None:
        config = {"products": []}
        erste = products.upsert(config, {"name": "Mein Werkzeug"})
        products.upsert(config, {"slug": erste["slug"], "name": "Mein Werkzeug",
                                 "one_liner": "neu"})
        self.assertEqual(len(config["products"]), 1)
        self.assertEqual(config["products"][0]["one_liner"], "neu")

    def test_free_text_lists_are_split(self) -> None:
        p = products.normalise({"name": "X", "keywords": "eins, zwei; drei",
                                "regions": "de, at", "languages": "DE, EN"})
        self.assertEqual(p["keywords"], ["eins", "zwei", "drei"])
        self.assertEqual(p["regions"], ["DE", "AT"])
        self.assertEqual(p["languages"], ["de", "en"])

    def test_nonsense_values_are_caught(self) -> None:
        p = products.normalise({"name": "X", "category": "quatsch", "price_model": "quatsch",
                                "tone": "quatsch", "budget_monthly_eur": "keine Zahl"})
        self.assertEqual(p["category"], "other")
        self.assertEqual(p["price_model"], "free")
        self.assertEqual(p["tone"], "sachlich")
        self.assertEqual(p["budget_monthly_eur"], 0)

    def test_a_negative_budget_becomes_zero(self) -> None:
        self.assertEqual(products.normalise({"name": "X", "budget_monthly_eur": -500})
                         ["budget_monthly_eur"], 0)

    def test_a_url_gets_a_scheme(self) -> None:
        self.assertEqual(products.normalise({"name": "X", "url": "beispiel.de"})["url"],
                         "https://beispiel.de")


if __name__ == "__main__":
    unittest.main()
