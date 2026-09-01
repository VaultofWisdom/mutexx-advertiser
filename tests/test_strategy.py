"""
Tests fuer die Strategie-Engine.

Geprueft wird nicht, ob die Punktzahlen "richtig" sind - das ist eine
Einschaetzungsfrage. Geprueft wird, dass die harten Zusagen halten:

  * ohne Budget kein einziger bezahlter Kanal
  * Google Shopping nur bei physischer Ware
  * kleines Budget geht in genau einen Kanal
  * das verteilte Geld uebersteigt nie das Budget
  * jeder verworfene Kanal hat eine Begruendung

Ausfuehren:  python -m unittest discover -s tests
"""

from __future__ import annotations

import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from advertiser import i18n, products, strategy  # noqa: E402


def produkt(**felder) -> dict:
    basis = {"name": "Testprodukt", "category": "software_desktop", "price_model": "freemium"}
    basis.update(felder)
    return products.normalise(basis)


def plan(**felder) -> dict:
    return strategy.build(produkt(**felder), {}, {}, use_api=False)


class PaidChannelsNeedBudget(unittest.TestCase):

    def test_no_paid_channel_without_a_budget(self) -> None:
        for kategorie in products.CATEGORIES:
            with self.subTest(kategorie=kategorie):
                result = plan(category=kategorie, budget_monthly_eur=0)
                bezahlt = [c for c in result["channels"] if c["kind"] == "bezahlt"]
                self.assertEqual(bezahlt, [], f"bezahlter Kanal ohne Budget bei {kategorie}")
                self.assertEqual(result["budget_plan"], [])

    def test_budget_below_minimum_is_rejected_with_a_reason(self) -> None:
        result = plan(category="shop_physical", price_model="shop", budget_monthly_eur=50)
        shopping = [r for r in result["rejected"] if r["id"] == "google_shopping"]
        self.assertTrue(shopping, "Google Shopping muesste bei 50 EUR wegfallen")
        for language in i18n.LANGUAGES:
            with self.subTest(language=language):
                self.assertIn("200", i18n.render(shopping[0]["blocked"], language))

    def test_every_rejected_channel_has_a_reason(self) -> None:
        for kategorie in products.CATEGORIES:
            for budget in (0, 100, 1000):
                result = plan(category=kategorie, budget_monthly_eur=budget)
                for verworfen in result["rejected"]:
                    for language in i18n.LANGUAGES:
                        with self.subTest(kategorie=kategorie, budget=budget,
                                          kanal=verworfen["id"], sprache=language):
                            self.assertTrue(
                                i18n.render(verworfen["blocked"], language).strip())


class HardExclusions(unittest.TestCase):

    def test_shopping_only_for_physical_goods(self) -> None:
        for kategorie in products.CATEGORIES:
            result = plan(category=kategorie, price_model="shop", budget_monthly_eur=1000)
            empfohlen = {c["id"] for c in result["channels"]}
            with self.subTest(kategorie=kategorie):
                if kategorie == "shop_physical":
                    self.assertIn("google_shopping", empfohlen)
                else:
                    self.assertNotIn("google_shopping", empfohlen)

    def test_open_source_needs_a_repository(self) -> None:
        ohne = plan(category="dev_tool")
        self.assertNotIn("open_source", {c["id"] for c in ohne["channels"]})

        mit = plan(category="dev_tool", links={"repo": "https://github.com/x/y"})
        self.assertIn("open_source", {c["id"] for c in mit["channels"]})


class BudgetSplit(unittest.TestCase):

    def _summe(self, result: dict) -> int:
        return sum(row["eur"] for row in result["budget_plan"])

    def test_allocated_money_never_exceeds_the_budget(self) -> None:
        for budget in (100, 120, 150, 249, 250, 400, 599, 600, 1000, 5000):
            for kategorie in ("shop_physical", "software_desktop", "dev_tool", "game"):
                result = plan(category=kategorie, price_model="shop", budget_monthly_eur=budget)
                with self.subTest(budget=budget, kategorie=kategorie):
                    self.assertLessEqual(self._summe(result), budget)

    def test_a_small_budget_goes_into_exactly_one_channel(self) -> None:
        result = plan(category="shop_physical", price_model="shop", budget_monthly_eur=200)
        kanaele = [row for row in result["budget_plan"] if row["channel"] != "_reserve"]
        self.assertEqual(len(kanaele), 1)

    def test_never_more_than_three_paid_channels(self) -> None:
        result = plan(category="shop_physical", price_model="shop", budget_monthly_eur=9000)
        kanaele = [row for row in result["budget_plan"] if row["channel"] != "_reserve"]
        self.assertLessEqual(len(kanaele), 3)

    def test_the_reserve_stays_untouched(self) -> None:
        result = plan(category="shop_physical", price_model="shop", budget_monthly_eur=1000)
        reserve = [row for row in result["budget_plan"] if row["channel"] == "_reserve"]
        self.assertTrue(reserve)
        self.assertGreater(reserve[0]["eur"], 0)

    def test_no_negative_amount(self) -> None:
        for budget in range(100, 1200, 37):
            result = plan(category="shop_physical", price_model="shop", budget_monthly_eur=budget)
            for row in result["budget_plan"]:
                with self.subTest(budget=budget, kanal=row["channel"]):
                    self.assertGreaterEqual(row["eur"], 0)


class ThePlanIsAlwaysUsable(unittest.TestCase):

    def test_every_combination_yields_channels_and_phases(self) -> None:
        for kategorie in products.CATEGORIES:
            for preismodell in products.PRICE_MODELS:
                result = plan(category=kategorie, price_model=preismodell,
                              budget_monthly_eur=500)
                with self.subTest(kategorie=kategorie, preismodell=preismodell):
                    self.assertTrue(result["channels"], "kein einziger Kanal")
                    self.assertTrue(result["phases"], "keine Phase")
                    self.assertTrue(i18n.render(result["summary"], "en").strip())
                    self.assertTrue(result["first_week"])

    def test_owned_channels_are_always_present(self) -> None:
        """Owned channels need neither permission nor money - they must not fall away
        for any kind of product."""
        for kategorie in products.CATEGORIES:
            empfohlen = {c["id"] for c in plan(category=kategorie)["channels"]}
            with self.subTest(kategorie=kategorie):
                self.assertIn("own_channels", empfohlen)
                self.assertIn("product_page", empfohlen)

    def test_without_a_budget_there_is_an_explanation(self) -> None:
        result = plan(budget_monthly_eur=0)
        schluessel = [w.get("key") for w in result["warnings"]]
        self.assertIn("strategy.warn.no_budget", schluessel)

    def test_no_channel_stores_prose(self) -> None:
        """The plan may hold keys and numbers, never finished sentences - that is what
        keeps a plan from last month readable in the other language."""
        result = plan(budget_monthly_eur=800, category="shop_physical",
                      price_model="shop")
        for kanal in result["channels"]:
            for feld in ("name_key", "what_key", "first_step_key", "risk_key"):
                with self.subTest(kanal=kanal["id"], feld=feld):
                    self.assertTrue(kanal[feld].startswith("channel."))
            for grund in kanal["why"]:
                self.assertIn("key", grund)


if __name__ == "__main__":
    unittest.main()
