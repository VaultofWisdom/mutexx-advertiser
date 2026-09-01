"""
Tests fuer die Ampel.

Die Regel-Analyse trifft die einzige Entscheidung dieser App, die einen echten
Schaden verhindert oder verursacht: ob in eine Community gepostet werden darf.
Ein falsches Gruen kostet die Domain, ein falsches Rot kostet nur eine Chance -
die Tests decken deshalb beide Richtungen ab, aber Gruen strenger.

Ausfuehren:  python -m unittest discover -s tests
"""

from __future__ import annotations

import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from advertiser import i18n, rules  # noqa: E402


class BansAreDetected(unittest.TestCase):
    """Cases where posting is NOT allowed."""

    def test_english_bans(self) -> None:
        for text in (
            "Rule 4: No self-promotion.",
            "No self promo of any kind.",
            "Self-promotion is not allowed here.",
            "Self promotion is prohibited.",
            "Advertising is banned in this subreddit.",
            "No soliciting.",
            "Do not post your own website.",
            "No links to your own projects.",
            "No blogspam.",
        ):
            with self.subTest(text=text):
                self.assertEqual(rules.analyse({"Regel": text})["verdict"], rules.FORBIDDEN)

    def test_german_bans(self) -> None:
        for text in (
            "Keine Werbung.",
            "Keine Eigenwerbung im Forum.",
            "Werbung ist verboten.",
            "Werbung ist nicht erlaubt.",
        ):
            with self.subTest(text=text):
                self.assertEqual(rules.analyse({"Regel": text})["verdict"], rules.FORBIDDEN)

    def test_a_ban_yields_the_original_quote(self) -> None:
        """Without evidence the traffic light is an assertion. The quote has to hit
        the right passage."""
        text = "Willkommen im Forum. Regel 7: Keine Eigenwerbung. Regel 8: Bleibt hoeflich."
        result = rules.analyse({"Regelseite": text})
        self.assertEqual(result["verdict"], rules.FORBIDDEN)
        beleg = [e for e in result["evidence"] if e["label"] == "rule.promo_forbidden"]
        self.assertTrue(beleg, "kein Beleg fuer das Verbot")
        self.assertIn("Keine Eigenwerbung", beleg[0]["quote"])
        self.assertEqual(beleg[0]["source"], "Regelseite")


class ConditionsAreDetected(unittest.TestCase):
    """Cases where posting is allowed - but only under conditions."""

    FAELLE = [
        ("No spam.", "rule.spam_ban"),
        ("Follow the 9:1 rule.", "rule.ratio"),
        ("Post it in the weekly megathread.", "rule.megathread"),
        ("Message the mods first.", "rule.mod_approval"),
        ("Moderator approval is required.", "rule.mod_approval"),
        ("Submissions must be flaired.", "rule.flair"),
        ("Text posts only.", "rule.text_only"),
        ("Minimum karma required to post.", "rule.karma"),
        ("No surveys, no crowdfunding.", "rule.no_monetisation"),
    ]

    def test_conditions(self) -> None:
        for text, label in self.FAELLE:
            with self.subTest(text=text):
                result = rules.analyse({"Regel": text})
                self.assertEqual(result["verdict"], rules.CONDITIONAL)
                self.assertIn(label, result["labels"])

    RATIO_IN_WORDS = [
        # Lobsters, word for word - the case that turned this up.
        "Self-promotion: self-promo should be less than a quarter of your submissions.",
        "No more than 10% of your posts may be your own content.",
        "Roughly 1 in 10 submissions may be your own work.",
        "At most a third of your submissions may be self-promotion.",
        "Eigenwerbung höchstens ein Viertel deiner Beiträge.",
        "Eigene Beiträge: nicht mehr als 20 Prozent.",
    ]

    def test_a_ratio_written_out_in_words_is_still_a_ratio(self) -> None:
        """Every one of these used to come back green - a promotion limit read as no
        limit at all, which is the expensive direction of this heuristic. Only the
        '9:1' notation was recognised, and most forums do not write it that way."""
        for text in self.RATIO_IN_WORDS:
            with self.subTest(text=text):
                result = rules.analyse({"Regel": text})
                self.assertEqual(result["verdict"], rules.CONDITIONAL)
                self.assertIn("rule.ratio", result["labels"])

    NOT_A_RATIO = [
        # A quantity with nothing to do with promotion.
        "No more than 3 posts per day, please.",
        "Up to 10 images per post.",
        "Threads are locked after 30 days.",
        "At most two tags per submission.",
        # A promotion word with no quantity anywhere near it.
        "Discuss your own experience with the software.",
        "Tell us about your own setup.",
    ]

    def test_a_quantity_alone_is_not_a_promotion_limit(self) -> None:
        """The other direction: both halves have to be there. A posting limit is a
        different rule, and marking every forum that counts something as a ratio
        forum would make the label meaningless."""
        for text in self.NOT_A_RATIO:
            with self.subTest(text=text):
                self.assertNotIn("rule.ratio", rules.analyse({"Regel": text})["labels"])

    def test_the_ratio_quote_shows_the_actual_limit(self) -> None:
        """The number is the whole point - a user who reads 'ratio rule' without it
        cannot tell a 9:1 forum from a one-in-four forum."""
        result = rules.analyse({"Regel": self.RATIO_IN_WORDS[0]})
        quote = next(e["quote"] for e in result["evidence"] if e["label"] == "rule.ratio")
        self.assertIn("quarter", quote)

    def test_no_spam_is_not_a_promotion_ban(self) -> None:
        """'No spam' appears in almost every rule list. Turning that red would drop
        half the list - the most common mistake in tools like this."""
        self.assertEqual(rules.analyse({"Regel": "No spam."})["verdict"], rules.CONDITIONAL)


class PermissionAndDoubt(unittest.TestCase):

    def test_explicit_permission(self) -> None:
        result = rules.analyse({"Regel": "Self-promotion is welcome here."})
        self.assertTrue(result["explicitly_allowed"])
        self.assertEqual(result["verdict"], rules.OPEN)

    def test_permission_lifts_a_blanket_spam_ban(self) -> None:
        result = rules.analyse({"Regel": "No spam. Feel free to share your own work."})
        self.assertTrue(result["explicitly_allowed"])
        self.assertEqual(result["verdict"], rules.CONDITIONAL)

    def test_permission_does_NOT_beat_a_hard_ban(self) -> None:
        """When both appear, the ban wins. When in doubt, do not post."""
        result = rules.analyse({
            "Sidebar": "Self-promotion is welcome.",
            "Regel 3": "No self-promotion.",
        })
        self.assertEqual(result["verdict"], rules.FORBIDDEN)

    def test_a_ban_beats_a_condition(self) -> None:
        result = rules.analyse({
            "Regel 1": "Submissions must be flaired.",
            "Regel 2": "No self-promotion.",
        })
        self.assertEqual(result["verdict"], rules.FORBIDDEN)

    def test_empty_rules_are_grey_not_green(self) -> None:
        """Finding nothing is not permission. Grey means: go and read them."""
        for texts in ({}, {"Regel": ""}, {"Regel": "   "}):
            with self.subTest(texts=texts):
                self.assertEqual(rules.analyse(texts)["verdict"], rules.UNKNOWN)

    def test_harmless_rules_stay_green(self) -> None:
        result = rules.analyse({"Regel": "Be excellent to each other. Stay on topic."})
        self.assertEqual(result["verdict"], rules.OPEN)
        self.assertEqual(result["labels"], [])

    def test_line_breaks_do_not_split_a_rule(self) -> None:
        """Regeltexte kommen oft umbrochen aus HTML. Das Muster muss trotzdem greifen."""
        result = rules.analyse({"Regel": "No\n   self-promotion\n   allowed"})
        self.assertEqual(result["verdict"], rules.FORBIDDEN)

    def test_labels_are_keys_not_sentences(self) -> None:
        """Nothing user-visible may be stored as prose - otherwise a community
        scanned today reads in the wrong language tomorrow."""
        result = rules.analyse({"Rules": "No self-promotion. Flair is required."})
        for label in result["labels"]:
            with self.subTest(label=label):
                self.assertTrue(label.startswith("rule."), label)
                for language in i18n.LANGUAGES:
                    satz = i18n.t(label, language)
                    self.assertNotEqual(satz, label, f"{label} missing in {language}")

    def test_evidence_is_capped(self) -> None:
        texts = {f"Regel {i}": "No spam. Flair is required. Message the mods first."
                 for i in range(30)}
        self.assertLessEqual(len(rules.analyse(texts)["evidence"]), 12)


if __name__ == "__main__":
    unittest.main()
