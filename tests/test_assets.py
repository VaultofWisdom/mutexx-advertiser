"""
Tests fuer die Werbemittel.

Zwei Zusagen muessen halten, sonst ist das Modul schlimmer als nutzlos:

  * Kein Text ueberschreitet seine Zeichengrenze. Google lehnt eine Ueberschrift mit
    31 Zeichen ab; wer sie trotzdem ausliefert, kostet den Nutzer einen Arbeitstag.
  * Kein Text behauptet etwas, das nicht im Profil steht. Eine Anzeige mit einer
    erfundenen Eigenschaft ist eine Falschangabe im Namen des Nutzers.

Ausfuehren:  python -m unittest discover -s tests
"""

from __future__ import annotations

import os
import sys
import unittest
import urllib.parse

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from advertiser import assets, i18n, products  # noqa: E402

ANALYSE = {
    "value_props": ["Keine Telemetrie und kein Konto noetig",
                    "Treiber laufen ueber Windows Update",
                    "Laeuft portabel ohne Installation"],
    "objections": ["Windows bringt vieles davon selbst mit"],
    "search_terms": ["autostart deaktivieren", "festplatte bereinigen"],
    "positioning": "Fuer Leute, die genau wissen wollen, was ein Wartungswerkzeug tut.",
}


def produkt(**felder) -> dict:
    basis = {
        "name": "Mutexx SystemCare", "url": "https://mutexx.de/systemcare", "version": "2.1",
        "one_liner": "Freies Wartungswerkzeug fuer Windows, Linux und macOS",
        "description": "Bereinigung, Autostart-Verwaltung und Diagnose. Kein Konto noetig.",
        "category": "software_desktop", "price_model": "freemium",
        "audience": "Leute, die ihren Rechner selbst pflegen", "languages": ["de"],
        "keywords": ["autostart", "systempflege"],
    }
    basis.update(felder)
    return products.normalise(basis)


class Truncation(unittest.TestCase):

    def test_the_limit_is_held_exactly(self) -> None:
        text = "Ein ziemlich langer Satz, der auf jeden Fall gekuerzt werden muss"
        for limit in range(5, len(text) + 5):
            with self.subTest(limit=limit):
                gekuerzt, _ = assets.fit(text, limit)
                self.assertLessEqual(len(gekuerzt), limit)

    def test_no_cut_mid_word(self) -> None:
        text = "Systempflege ohne Datensammlung"
        gekuerzt, was_cut = assets.fit(text, 20)
        self.assertTrue(was_cut)
        self.assertEqual(gekuerzt, "Systempflege ohne")
        for wort in gekuerzt.split():
            self.assertIn(wort, text.split())

    def test_fitting_text_is_left_alone(self) -> None:
        gekuerzt, was_cut = assets.fit("Kurz genug", 30)
        self.assertEqual(gekuerzt, "Kurz genug")
        self.assertFalse(was_cut)

    def test_a_single_long_word_is_cut_hard(self) -> None:
        gekuerzt, was_cut = assets.fit("Donaudampfschifffahrtsgesellschaft", 10)
        self.assertTrue(was_cut)
        self.assertEqual(len(gekuerzt), 10)

    def test_uncut_candidates_come_first(self) -> None:
        """A chopped headline is worse than a short one. So what fits by itself comes
        first."""
        gewaehlt = assets._pick(
            ["Ein viel zu langer Kandidat fuer dieses Feld", "Passt genau"], 15, 2)
        self.assertEqual(gewaehlt[0]["text"], "Passt genau")
        self.assertFalse(gewaehlt[0]["truncated"])
        self.assertTrue(gewaehlt[1]["truncated"])

    def test_duplicate_candidates_drop_out(self) -> None:
        gewaehlt = assets._pick(["Gleicher Text", "Gleicher Text", "gleicher text"], 50, 5)
        self.assertEqual(len(gewaehlt), 1)


class CharacterLimitsAlwaysHold(unittest.TestCase):

    def test_no_field_exceeds_its_limit(self) -> None:
        """Every asset, every category, every pricing model. This is the test that
        justifies the module."""
        for kategorie in products.CATEGORIES:
            for preismodell in products.PRICE_MODELS:
                p = produkt(category=kategorie, price_model=preismodell,
                            price_point="19,90 EUR")
                for spec in assets.available(p):
                    asset = assets.build(spec["id"], p, ANALYSE, {}, use_api=False)
                    for feld in asset["spec"]:
                        for eintrag in asset["fields"][feld["key"]]:
                            with self.subTest(kategorie=kategorie, preismodell=preismodell,
                                              werbemittel=spec["id"], feld=feld["key"]):
                                self.assertLessEqual(
                                    eintrag["length"], feld["limit"],
                                    f"zu lang: {eintrag['text']!r}")
                                self.assertTrue(eintrag["ok"])

    def test_an_empty_profile_breaks_nothing(self) -> None:
        p = products.normalise({"name": "Nur ein Name"})
        for spec in assets.available(p):
            asset = assets.build(spec["id"], p, {}, {}, use_api=False)
            with self.subTest(werbemittel=spec["id"]):
                self.assertEqual(asset["asset_id"], spec["id"])
                for feld in asset["spec"]:
                    for eintrag in asset["fields"][feld["key"]]:
                        self.assertLessEqual(eintrag["length"], feld["limit"])

    def test_missing_variants_are_reported(self) -> None:
        """Fewer variants than asked for is not an error - but it has to be stated."""
        asset = assets.build("google_search_ads", products.normalise({"name": "X"}), {}, {},
                             use_api=False)
        self.assertTrue(asset["warnings"])

    def test_ai_copy_runs_through_the_same_check(self) -> None:
        """Language models count characters notoriously badly. Copy that is too long
        must not get through from the API any more than from a template."""
        p = produkt()
        zu_lang = "X" * 500
        original = assets._build_with_api
        try:
            assets._build_with_api = lambda *a, **k: {"headlines": [zu_lang],
                                                      "descriptions": [zu_lang]}
            asset = assets.build("google_search_ads", p, ANALYSE, {}, use_api=True)
        finally:
            assets._build_with_api = original
        self.assertEqual(asset["generated_by"], "anthropic")
        for eintrag in asset["fields"]["headlines"]:
            self.assertLessEqual(eintrag["length"], 30)

    def test_api_failure_falls_back_to_template(self) -> None:
        p = produkt()
        original = assets._build_with_api

        def kaputt(*_a, **_k):
            raise ValueError("kein Schluessel")

        try:
            assets._build_with_api = kaputt
            asset = assets.build("seo_meta", p, ANALYSE, {}, use_api=True)
        finally:
            assets._build_with_api = original
        self.assertEqual(asset["generated_by"], "vorlage")
        self.assertTrue(asset["fields"]["title"])
        gerendert = [i18n.render(w, "en") for w in asset["warnings"]]
        self.assertTrue(any("kein Schluessel" in w for w in gerendert))


class NothingIsInvented(unittest.TestCase):

    GRATIS = ("kostenlos", "gratis", "umsonst", "free")

    def test_paid_product_is_never_called_free(self) -> None:
        for preismodell in ("one_time", "subscription", "shop", "quote"):
            p = produkt(price_model=preismodell, price_point="19,90 EUR")
            for spec in assets.available(p):
                asset = assets.build(spec["id"], p, ANALYSE, {}, use_api=False)
                alles = " ".join(e["text"] for liste in asset["fields"].values()
                                 for e in liste).lower()
                for wort in self.GRATIS:
                    with self.subTest(preismodell=preismodell, werbemittel=spec["id"],
                                      wort=wort):
                        self.assertNotIn(wort, alles)

    def test_subscription_promises_no_free_trial(self) -> None:
        """The classic: "Free trial" sounds harmless but asserts a trial period that
        appears nowhere in the profile."""
        p = produkt(price_model="subscription", price_point="9 EUR im Monat")
        asset = assets.build("google_search_ads", p, ANALYSE, {}, use_api=False)
        alles = " ".join(e["text"] for liste in asset["fields"].values()
                         for e in liste).lower()
        self.assertNotIn("kostenlos", alles)
        self.assertNotIn("gratis", alles)

    def test_no_invented_platforms(self) -> None:
        """A Windows-only tool must not be advertised as a Mac and Linux program just
        because it is desktop software."""
        p = produkt(one_liner="Wartungswerkzeug fuer Windows",
                    description="Bereinigung und Autostart-Verwaltung unter Windows.",
                    keywords=["autostart"])
        for spec in assets.available(p):
            asset = assets.build(spec["id"], p, {}, {}, use_api=False)
            alles = " ".join(e["text"] for liste in asset["fields"].values()
                             for e in liste).lower()
            for plattform in ("linux", "macos", " mac ", "ios", "android"):
                with self.subTest(werbemittel=spec["id"], plattform=plattform):
                    self.assertNotIn(plattform, alles)

    def test_no_version_appears_without_a_version(self) -> None:
        p = produkt(version="")
        asset = assets.build("press_kit", p, ANALYSE, {}, use_api=False)
        fakten = asset["fields"]["facts"][0]["text"]
        self.assertNotIn("Version:", fakten)

    def test_value_points_come_from_the_analysis(self) -> None:
        asset = assets.build("directory_listing", produkt(), ANALYSE, {}, use_api=False)
        lang = asset["fields"]["long"][0]["text"]
        self.assertIn("Keine Telemetrie", lang)


class NegativeKeywords(unittest.TestCase):

    def _liste(self, preismodell: str) -> list[str]:
        asset = assets.build("google_search_ads", produkt(price_model=preismodell),
                             ANALYSE, {}, use_api=False)
        return asset["negative_keywords"]

    def test_free_products_do_not_exclude_free_seekers(self) -> None:
        """Someone searching for "free" is the right visitor for a free product - and
        the top of the funnel for freemium."""
        for preismodell in ("free", "freemium", "ad_supported"):
            with self.subTest(preismodell=preismodell):
                self.assertNotIn("kostenlos", self._liste(preismodell))

    def test_paid_products_exclude_free_seekers(self) -> None:
        for preismodell in ("one_time", "subscription", "shop"):
            with self.subTest(preismodell=preismodell):
                self.assertIn("kostenlos", self._liste(preismodell))

    def test_piracy_terms_are_always_excluded(self) -> None:
        for preismodell in products.PRICE_MODELS:
            with self.subTest(preismodell=preismodell):
                self.assertIn("crack", self._liste(preismodell))


class CampaignTagging(unittest.TestCase):

    def test_utm_is_appended(self) -> None:
        url = assets.utm_url(produkt(), "meta_ads", "paid_social")
        query = dict(urllib.parse.parse_qsl(urllib.parse.urlsplit(url).query))
        self.assertEqual(query["utm_source"], "meta_ads")
        self.assertEqual(query["utm_medium"], "paid_social")
        self.assertTrue(query["utm_campaign"])

    def test_existing_query_parameters_survive(self) -> None:
        p = produkt(url="https://beispiel.de/seite?ref=start")
        query = dict(urllib.parse.parse_qsl(
            urllib.parse.urlsplit(assets.utm_url(p, "press")).query))
        self.assertEqual(query["ref"], "start")
        self.assertEqual(query["utm_source"], "press")

    def test_no_invented_address_without_a_product_url(self) -> None:
        self.assertEqual(assets.utm_url(products.normalise({"name": "X"}), "press"), "")

    def test_every_asset_gets_a_destination_url(self) -> None:
        p = produkt()
        for spec in assets.available(p):
            asset = assets.build(spec["id"], p, ANALYSE, {}, use_api=False)
            with self.subTest(werbemittel=spec["id"]):
                self.assertTrue(asset["utm_url"].startswith("https://"))


class AssetSelection(unittest.TestCase):

    def test_store_listing_only_where_a_store_exists(self) -> None:
        for kategorie in products.CATEGORIES:
            verfuegbar = {spec["id"] for spec in assets.available(produkt(category=kategorie))}
            with self.subTest(kategorie=kategorie):
                if kategorie in ("app_mobile", "game", "software_desktop"):
                    self.assertIn("store_listing", verfuegbar)
                else:
                    self.assertNotIn("store_listing", verfuegbar)

    def test_every_asset_points_at_a_real_channel(self) -> None:
        from advertiser import strategy
        for spec in assets.ASSETS:
            with self.subTest(werbemittel=spec["id"]):
                self.assertIn(spec["channel"], strategy.CHANNELS_BY_ID)

    def test_the_specification_carries_only_keys(self) -> None:
        """No prose in the specification - the field labels have to follow the
        language switch like everything else."""
        for spec in assets.available(produkt()):
            self.assertTrue(spec["name_key"].startswith("asset."))
            for field in spec["fields"]:
                with self.subTest(werbemittel=spec["id"], feld=field["key"]):
                    self.assertTrue(field["label_key"].startswith("asset."))
                    for language in i18n.LANGUAGES:
                        self.assertNotEqual(i18n.t(field["label_key"], language),
                                            field["label_key"])


if __name__ == "__main__":
    unittest.main()
