"""
Tests for the Discourse channel.

Discourse matters here for one reason beyond convenience: many forums forbid
self-promotion everywhere and then keep one category for exactly that. Read
without the category list, such a forum is red and drops out of every campaign -
the honest, invited post is the one that never gets written.

Turning that red into amber is the only place in this app where a verdict is made
*more* permissive by a heuristic, so it is the one pinned down hardest:

  * the name alone must never be enough ("Projects" is where people discuss
    projects at least as often as where they announce their own),
  * amber is the ceiling - a showcase category never produces green,
  * and the quote it rests on has to travel with the verdict, because a verdict
    the user cannot check is worth nothing.

No network access: core.fetch is replaced. A test that needed a real forum to be
up would be a test of that forum.

Run:  python -m unittest discover -s tests
"""

from __future__ import annotations

import json
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from advertiser import core, discourse_api, discovery, rules  # noqa: E402

UA = "MutexxAdvertiser/test"

ABOUT = {
    "about": {
        "title": "Example Forum",
        "description": "A forum about examples.",
        "version": "3.2.0",
        "stats": {"users_count": 4200, "posts_7_days": 700, "topics_7_days": 90},
    }
}


def category(name, slug, description, *, topics=10, restricted=False, cid=1):
    return {"id": cid, "name": name, "slug": slug, "description_text": description,
            "topic_count": topics, "read_restricted": restricted}


class FakeNet:
    """Stands in for core.fetch. Unlisted paths answer 404 with an HTML error page,
    which is what a non-Discourse site really does."""

    def __init__(self, routes: dict[str, tuple[int, bytes]]) -> None:
        self.routes = routes
        self.calls: list[str] = []

    def fetch(self, url, *, user_agent, **kwargs):
        self.calls.append(url)
        if url in self.routes:
            return self.routes[url]
        return 404, b"<!DOCTYPE html><html><body>Not found</body></html>"


class NetTestCase(unittest.TestCase):
    """Swaps core.fetch out for the duration of one test."""

    def use(self, routes):
        net = FakeNet(routes)
        self._real = core.fetch
        core.fetch = net.fetch
        self.addCleanup(self._restore)
        return net

    def _restore(self):
        core.fetch = self._real


class Addresses(unittest.TestCase):

    def test_any_page_leads_back_to_the_root(self) -> None:
        for value in ("https://forum.example.org/c/help/5",
                      "https://forum.example.org/",
                      "forum.example.org"):
            with self.subTest(value=value):
                self.assertEqual(discourse_api.base_of(value), "https://forum.example.org")

    def test_nonsense_yields_nothing(self) -> None:
        self.assertEqual(discourse_api.base_of(""), "")


class Identification(NetTestCase):

    def test_a_discourse_forum_reports_its_figures(self) -> None:
        self.use({"https://f.example/about.json": (200, json.dumps(ABOUT).encode())})
        profile = discourse_api.about("https://f.example/", UA)
        self.assertEqual(profile["users"], 4200)
        self.assertEqual(profile["title"], "Example Forum")

    def test_activity_is_the_last_seven_days_not_the_lifetime_average(self) -> None:
        """A forum that was busy in 2014 and quiet ever since must not look alive."""
        self.use({"https://f.example/about.json": (200, json.dumps(ABOUT).encode())})
        self.assertEqual(discourse_api.about("https://f.example/", UA)["posts_per_day"], 100.0)

    def test_a_site_that_is_not_discourse_is_not_mistaken_for_one(self) -> None:
        """Every site answers something at /about.json. Only Discourse answers JSON
        with an 'about' block that carries stats."""
        for body in (b"<!DOCTYPE html><html>404</html>",
                     json.dumps({"about": {"title": "x"}}).encode(),
                     json.dumps({"something": "else"}).encode(),
                     b"not json at all"):
            with self.subTest(body=body[:20]):
                self.use({"https://f.example/about.json": (200, body)})
                self.assertIsNone(discourse_api.about("https://f.example/", UA))

    def test_an_unreachable_forum_is_none_not_an_exception(self) -> None:
        self.use({})
        self.assertIsNone(discourse_api.about("https://f.example/", UA))


class RulePages(NetTestCase):

    def test_guidelines_and_terms_are_read_from_their_known_address(self) -> None:
        long_text = b"<html><body>" + b"House rules. " * 40 + b"</body></html>"
        self.use({"https://f.example/guidelines": (200, long_text),
                  "https://f.example/tos": (200, long_text)})
        texts = discourse_api.rule_texts("https://f.example", UA)
        self.assertEqual(sorted(texts), ["Guidelines", "Terms of service"])

    def test_an_almost_empty_page_is_not_a_rule_set(self) -> None:
        """A stub page would otherwise turn a grey verdict green - no ban found in
        forty characters of boilerplate."""
        self.use({"https://f.example/guidelines": (200, b"<html><body>Soon.</body></html>")})
        self.assertEqual(discourse_api.rule_texts("https://f.example", UA), {})


class Categories(NetTestCase):

    def routes(self, cats):
        return {"https://f.example/categories.json":
                (200, json.dumps({"category_list": {"categories": cats}}).encode())}

    def test_private_categories_are_left_out(self) -> None:
        """You cannot post where you cannot read, and proposing it wastes the user's
        time at best."""
        self.use(self.routes([category("Staff", "staff", "Internal.", restricted=True),
                              category("Help", "help", "Ask here.")]))
        names = [c["name"] for c in discourse_api.categories("https://f.example", UA)]
        self.assertEqual(names, ["Help"])

    def test_a_broken_answer_is_an_empty_list(self) -> None:
        self.use({"https://f.example/categories.json": (200, b"<html>nope</html>")})
        self.assertEqual(discourse_api.categories("https://f.example", UA), [])


class Showcase(unittest.TestCase):

    def test_an_inviting_category_is_recognised(self) -> None:
        found = discourse_api.showcase_category([
            {"name": "Share & showcase", "slug": "share", "url": "u", "topics": 40,
             "description": "Showcase your plugins, themes and workflows here."}])
        self.assertIsNotNone(found)
        self.assertIn("your plugins", found["quote"])

    def test_the_name_alone_is_never_enough(self) -> None:
        """The expensive false positive. 'Projects' is where people discuss projects
        at least as often as where they announce their own - reading that as
        permission is how a forum bans a domain."""
        for name, description in (
            ("Show and tell", "Threads moved here when they no longer fit elsewhere."),
            ("Promote", "Discussion of how companies promote their products."),
            ("Showcase", ""),
        ):
            with self.subTest(name=name):
                self.assertIsNone(discourse_api.showcase_category([
                    {"name": name, "slug": "s", "url": "u", "topics": 99,
                     "description": description}]))

    def test_a_description_alone_is_not_enough_either(self) -> None:
        self.assertIsNone(discourse_api.showcase_category([
            {"name": "General", "slug": "g", "url": "u", "topics": 99,
             "description": "Share your thoughts on the project with us."}]))

    def test_german_forums_are_covered(self) -> None:
        found = discourse_api.showcase_category([
            {"name": "Eigene Projekte", "slug": "p", "url": "u", "topics": 12,
             "description": "Zeigt hier eure eigenen Projekte und Basteleien."}])
        self.assertIsNotNone(found)

    def test_the_busier_category_wins(self) -> None:
        found = discourse_api.showcase_category([
            {"name": "Showcase (archive)", "slug": "a", "url": "u", "topics": 2,
             "description": "Show off your work. Archived."},
            {"name": "Showcase", "slug": "b", "url": "u", "topics": 300,
             "description": "Show off your work here."}])
        self.assertEqual(found["slug"], "b")


class VerdictWithShowcase(unittest.TestCase):

    def entry(self, verdict, showcase):
        return {"analysis": {"verdict": verdict, "labels": [], "evidence": [],
                             "explicitly_allowed": False},
                "showcase_category": showcase}

    SHOWCASE = {"name": "Share & showcase", "slug": "s", "url": "u", "topics": 40,
                "description": "Show off your work here.", "quote": "Show off your work here."}

    def test_a_ban_plus_an_invited_category_becomes_amber(self) -> None:
        entry = self.entry(rules.FORBIDDEN, self.SHOWCASE)
        discovery._apply_showcase(entry)
        self.assertEqual(entry["analysis"]["verdict"], rules.CONDITIONAL)
        self.assertIn("rule.showcase_category", entry["analysis"]["labels"])

    def test_the_quote_travels_with_the_verdict(self) -> None:
        """A verdict the user cannot check is worth nothing - that rule holds here
        exactly as it does for the rules fetched from the community itself."""
        entry = self.entry(rules.FORBIDDEN, self.SHOWCASE)
        discovery._apply_showcase(entry)
        self.assertEqual(entry["analysis"]["evidence"][0]["quote"], "Show off your work here.")

    def test_a_ban_without_such_a_category_stays_red(self) -> None:
        entry = self.entry(rules.FORBIDDEN, None)
        discovery._apply_showcase(entry)
        self.assertEqual(entry["analysis"]["verdict"], rules.FORBIDDEN)

    def test_amber_is_the_ceiling_never_green(self) -> None:
        """The category lifts a ban to a condition. It is not a licence: post there
        and nowhere else is still a condition the user has to keep."""
        entry = self.entry(rules.CONDITIONAL, self.SHOWCASE)
        discovery._apply_showcase(entry)
        self.assertEqual(entry["analysis"]["verdict"], rules.CONDITIONAL)

    def test_a_green_forum_is_left_alone(self) -> None:
        entry = self.entry(rules.OPEN, self.SHOWCASE)
        discovery._apply_showcase(entry)
        self.assertEqual(entry["analysis"]["verdict"], rules.OPEN)
        self.assertEqual(entry["analysis"]["labels"], [])


class ForumProbe(NetTestCase):
    """The whole path, as scan_forums walks it."""

    def test_discourse_replaces_the_guesses_with_facts(self) -> None:
        rules_page = b"<html><body>" + b"Be nice to each other. " * 30 + b"</body></html>"
        self.use({
            "https://f.example/": (200, b"<html><title>Example Forum</title><body>notes</body></html>"),
            "https://f.example/about.json": (200, json.dumps(ABOUT).encode()),
            "https://f.example/guidelines": (200, rules_page),
            "https://f.example/categories.json": (200, json.dumps(
                {"category_list": {"categories": [category("Help", "help", "Ask here.")]}}).encode()),
        })
        entry = discovery._probe_forum("https://f.example/", "Example", "", UA, ["notes"])
        self.assertEqual(entry["forum_software"], "discourse")
        self.assertEqual(entry["subscribers"], 4200)
        self.assertEqual(entry["posts_per_day"], 100.0)
        self.assertTrue(entry["rules"])

    def test_a_plain_forum_still_goes_the_old_way(self) -> None:
        """Discourse support must not cost the forums that are not Discourse - they
        are the reason the generic probe exists."""
        page = (b"<html><title>Old Board</title><body>notes "
                b"<a href=\"https://f.example/rules.php\">Rules</a></body></html>")
        self.use({
            "https://f.example/": (200, page),
            "https://f.example/rules.php": (200, b"<html><body>No self-promotion.</body></html>"),
        })
        entry = discovery._probe_forum("https://f.example/", "Old Board", "", UA, ["notes"])
        self.assertNotIn("forum_software", entry)
        self.assertTrue(entry["reachable"])
        self.assertEqual(entry["analysis"]["verdict"], rules.FORBIDDEN)

    def test_a_forum_with_a_ban_and_a_showcase_category_survives_the_scan(self) -> None:
        """The case the whole module exists for: red everywhere, one category for
        exactly this. Without it the forum drops out of the campaign entirely."""
        ban = b"<html><body>" + b"Rule 1: No self-promotion anywhere. " * 20 + b"</body></html>"
        self.use({
            "https://f.example/": (200, b"<html><title>F</title><body>notes</body></html>"),
            "https://f.example/about.json": (200, json.dumps(ABOUT).encode()),
            "https://f.example/guidelines": (200, ban),
            "https://f.example/categories.json": (200, json.dumps({"category_list": {"categories": [
                category("Share & showcase", "share", "Show off your work here.", topics=50)]}}).encode()),
        })
        entry = discovery._probe_forum("https://f.example/", "F", "", UA, ["notes"])
        self.assertEqual(entry["analysis"]["verdict"], rules.CONDITIONAL)
        self.assertEqual(entry["showcase_category"]["slug"], "share")


if __name__ == "__main__":
    unittest.main()
