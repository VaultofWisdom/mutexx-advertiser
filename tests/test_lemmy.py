"""
Tests for the Lemmy channel.

Lemmy is the first channel that works without anyone's approval, which makes it
the one users will lean on hardest - so the parts that decide whether a post
happens at all are pinned down here:

  * the traffic light, including the case Reddit does not have: a community only
    moderators may post in. No draft gets past that, so it has to be red rather
    than amber.
  * the daily limit. It exists so a campaign does not turn back into spam, and
    it would be worth nothing if a second network simply escaped it.
  * the size scale. Lemmy communities are two orders of magnitude smaller than
    subreddits; measured against one shared ceiling the ranking would always
    read "go to Reddit", whatever the rules there said.

No network access. The API is replaced by a stub - a test that needed lemmy.world
to be up would be a test of lemmy.world.

Run:  python -m unittest discover -s tests
"""

from __future__ import annotations

import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from advertiser import core, discovery, lemmy_api, publish, rules  # noqa: E402


CONFIG = {
    "user_agent": "MutexxAdvertiser/test",
    "discovery": {"max_communities": 50, "deep_scan_top_n": 10,
                  "min_subscribers": 400, "lemmy_min_subscribers": 40},
    "safety": {"max_reddit_posts_per_day": 1, "min_days_between_same_subreddit": 45},
}


def view(name: str, home: str = "lemmy.world", *, title: str = "", description: str = "",
         subscribers: int = 500, mods_only: bool = False, nsfw: bool = False,
         removed: bool = False, deleted: bool = False) -> dict:
    return {
        "community": {
            "name": name,
            "title": title or name,
            "description": description,
            "actor_id": f"https://{home}/c/{name}",
            "nsfw": nsfw,
            "removed": removed,
            "deleted": deleted,
            "posting_restricted_to_mods": mods_only,
        },
        "counts": {"subscribers": subscribers, "users_active_week": 40},
    }


class InstanceNames(unittest.TestCase):

    def test_shapes_of_the_same_instance_collapse(self) -> None:
        for value in ("lemmy.world", "LEMMY.WORLD", "https://lemmy.world",
                      "https://lemmy.world/", "https://www.lemmy.world/c/x", "lemmy.world/"):
            with self.subTest(value=value):
                self.assertEqual(lemmy_api.normalise_instance(value), "lemmy.world")

    def test_empty_stays_empty(self) -> None:
        for value in ("", "   ", None):
            self.assertEqual(lemmy_api.normalise_instance(value), "")

    def test_handle_carries_the_home_instance(self) -> None:
        handle, url = lemmy_api.handle_of(view("selfhosted", "lemmy.world"))
        self.assertEqual(handle, "selfhosted@lemmy.world")
        self.assertEqual(url, "https://lemmy.world/c/selfhosted")

    def test_a_view_without_a_name_is_no_community(self) -> None:
        self.assertEqual(lemmy_api.handle_of({"community": {}}), ("", ""))


class Timestamps(unittest.TestCase):
    """Lemmy sends ISO 8601 in several shapes across versions, and the activity
    figure is silently zero if parsing fails."""

    def test_shapes_all_parse(self) -> None:
        for value in ("2026-08-01T12:00:00Z",
                      "2026-08-01T12:00:00+00:00",
                      "2026-08-01T12:00:00.123456Z",
                      "2026-08-01T12:00:00.123Z",
                      "2026-08-01T12:00:00.123456789+02:00",
                      "2026-08-01T12:00:00"):
            with self.subTest(value=value):
                self.assertGreater(discovery._timestamp(value), 0)

    def test_rubbish_is_zero_not_an_exception(self) -> None:
        for value in ("", "   ", "yesterday", None, {}):
            self.assertEqual(discovery._timestamp(value), 0.0)


class Entries(unittest.TestCase):

    def test_the_description_is_the_sidebar(self) -> None:
        """On Lemmy the rules live in the description and nowhere else. Cutting it
        to a teaser would take the rules with it."""
        text = "Rules: " + ("no self-promotion. " * 40)
        entry = discovery._lemmy_entry(view("x", description=text), [])
        self.assertIn("no self-promotion", entry["sidebar"])
        self.assertGreater(len(entry["sidebar"]), 600)

    def test_removed_and_deleted_drop_out(self) -> None:
        self.assertIsNone(discovery._lemmy_entry(view("x", removed=True), []))
        self.assertIsNone(discovery._lemmy_entry(view("x", deleted=True), []))

    def test_keywords_score_against_name_title_and_description(self) -> None:
        entry = discovery._lemmy_entry(
            view("selfhosted", title="Self-Hosting", description="notes about self-hosting"),
            ["self-hosting"])
        self.assertGreater(entry["fit_raw"], 0)


class Stub:
    """Stands in for lemmy_api during the scan."""

    def __init__(self, results: dict[str, list[dict]]) -> None:
        self.results = results
        self.DEFAULT_INSTANCES = ["lemmy.world"]
        self.normalise_instance = lemmy_api.normalise_instance
        self.handle_of = lemmy_api.handle_of
        self.site_rules_calls: list[str] = []

    def search_communities(self, instance, query, ua, limit=40):
        return self.results.get(instance, [])

    def site_rules(self, instance, ua):
        self.site_rules_calls.append(instance)
        return {}

    def posts(self, instance, name, ua, limit=50):
        return []


class Scan(unittest.TestCase):

    def setUp(self) -> None:
        self._real = discovery.lemmy_api

    def tearDown(self) -> None:
        discovery.lemmy_api = self._real

    def run_scan(self, results, keywords=("self-hosting",), instances=None):
        stub = Stub(results)
        discovery.lemmy_api = stub
        entries = discovery.scan_lemmy(CONFIG, list(keywords), instances)
        return entries, stub

    def test_the_size_floor_is_lemmys_own(self) -> None:
        """400 subscribers is a small subreddit and a large Lemmy community. Against
        the Reddit floor almost the whole network would disappear."""
        entries, _ = self.run_scan({"lemmy.world": [view("small", subscribers=120),
                                                    view("tiny", subscribers=12)]})
        handles = [entry["handle"] for entry in entries]
        self.assertIn("small@lemmy.world", handles)
        self.assertNotIn("tiny@lemmy.world", handles)

    def test_the_same_community_seen_twice_stays_one_entry(self) -> None:
        """Federation means two instances answer with the same community. Two
        entries would mean the campaign proposes posting there twice."""
        both = view("selfhosted", "lemmy.world", description="self-hosting")
        entries, _ = self.run_scan({"lemmy.world": [both], "lemm.ee": [both]},
                                   instances=["lemmy.world", "lemm.ee"])
        self.assertEqual(len(entries), 1)

    def test_moderators_only_is_red_not_amber(self) -> None:
        entries, _ = self.run_scan({"lemmy.world": [
            view("announcements", description="Everyone welcome, share your work!",
                 mods_only=True)]})
        self.assertEqual(entries[0]["analysis"]["verdict"], rules.FORBIDDEN)
        self.assertIn("rule.mods_only", entries[0]["analysis"]["labels"])

    def test_a_ban_in_the_description_is_found(self) -> None:
        entries, _ = self.run_scan({"lemmy.world": [
            view("news", description="Rule 3: No self-promotion.")]})
        self.assertEqual(entries[0]["analysis"]["verdict"], rules.FORBIDDEN)

    def test_instance_rules_are_fetched_once_per_instance(self) -> None:
        entries, stub = self.run_scan({"lemmy.world": [
            view("a", description="self-hosting"),
            view("b", description="self-hosting"),
            view("c", description="self-hosting")]})
        self.assertEqual(len(entries), 3)
        self.assertEqual(stub.site_rules_calls, ["lemmy.world"])

    def test_a_community_that_wrote_no_rules_is_grey_not_green(self) -> None:
        """The one mistake that costs the domain. A Lemmy community keeps its rules
        in the description or nowhere - silence is not permission, and the
        instance's welcome text is not the community's answer."""
        entries, _ = self.run_scan({"lemmy.world": [
            view("quiet", description="Self-hosting chat.")]})
        self.assertEqual(entries[0]["analysis"]["verdict"], rules.UNKNOWN)

    def test_silence_does_not_erase_a_ban(self) -> None:
        """Grey is a downgrade from green, never an upgrade from red - an instance
        ban applies whether the community repeats it or not."""
        entries, _ = self.run_scan({"lemmy.world": [
            view("quiet", description="No self-promotion.")]})
        self.assertEqual(entries[0]["analysis"]["verdict"], rules.FORBIDDEN)

    def test_a_real_rule_set_still_gets_a_verdict(self) -> None:
        """The downgrade must not swallow communities that did write their rules -
        otherwise every Lemmy entry would be grey and the traffic light useless."""
        text = ("Welcome to this community. Rule 1: stay on topic. Rule 2: be civil "
                "with each other. Rule 3: no reposts within a week. Rule 4: tag "
                "your posts properly so people can filter them.")
        entries, _ = self.run_scan({"lemmy.world": [view("busy", description=text)]})
        self.assertEqual(entries[0]["analysis"]["verdict"], rules.OPEN)

    def test_an_instance_that_answers_with_nothing_does_not_break_the_scan(self) -> None:
        entries, _ = self.run_scan({}, instances=["down.example"])
        self.assertEqual(entries, [])


class Scoring(unittest.TestCase):

    def test_lemmy_is_measured_against_lemmy(self) -> None:
        """A large Lemmy community must not be ranked as if it were a dead subreddit
        just because Reddit counts members differently."""
        big_lemmy = {"platform": "lemmy", "subscribers": 20000, "fit_raw": 10,
                     "posts_per_day": 5, "analysis": {"verdict": rules.OPEN}}
        small_reddit = {"platform": "reddit", "subscribers": 20000, "fit_raw": 10,
                        "posts_per_day": 5, "analysis": {"verdict": rules.OPEN}}
        discovery.score_all([big_lemmy, small_reddit])
        self.assertGreater(big_lemmy["score"], small_reddit["score"])

    def test_a_ban_still_sinks_the_entry(self) -> None:
        forbidden = {"platform": "lemmy", "subscribers": 20000, "fit_raw": 10,
                     "posts_per_day": 5, "analysis": {"verdict": rules.FORBIDDEN}}
        allowed = {"platform": "lemmy", "subscribers": 200, "fit_raw": 3,
                   "posts_per_day": 1, "analysis": {"verdict": rules.OPEN}}
        discovery.score_all([forbidden, allowed])
        self.assertLess(forbidden["score"], allowed["score"])


class SafetyCatch(unittest.TestCase):
    """The limit exists so the campaign does not turn back into spam. A second
    network that slipped past it would make it worthless."""

    def test_a_reddit_post_today_blocks_a_lemmy_post_today(self) -> None:
        import time
        history = [{"platform": "reddit", "ts": int(time.time()), "community_id": "reddit:x"}]
        entry = {"id": "lemmy:a@lemmy.world", "platform": "lemmy", "analysis": {"verdict": rules.OPEN}}
        guard = publish.check_guard(entry, CONFIG, history)
        self.assertFalse(guard["allowed"])

    def test_a_lemmy_post_today_blocks_a_reddit_post_today(self) -> None:
        import time
        history = [{"platform": "lemmy", "ts": int(time.time()), "community_id": "lemmy:a@lemmy.world"}]
        entry = {"id": "reddit:x", "platform": "reddit", "analysis": {"verdict": rules.OPEN}}
        guard = publish.check_guard(entry, CONFIG, history)
        self.assertFalse(guard["allowed"])

    def test_a_red_community_is_refused_on_lemmy_too(self) -> None:
        entry = {"id": "lemmy:a@lemmy.world", "platform": "lemmy",
                 "analysis": {"verdict": rules.FORBIDDEN}}
        guard = publish.check_guard(entry, CONFIG, [])
        self.assertFalse(guard["allowed"])


class Configuration(unittest.TestCase):

    def test_the_lemmy_floor_has_a_default(self) -> None:
        """scan_lemmy reads it with a fallback, but a config written before this
        channel existed must still produce a sane scan."""
        self.assertIn("lemmy_min_subscribers", core.DEFAULT_CONFIG["discovery"])
        self.assertLess(core.DEFAULT_CONFIG["discovery"]["lemmy_min_subscribers"],
                        core.DEFAULT_CONFIG["discovery"]["min_subscribers"])


if __name__ == "__main__":
    unittest.main()
