"""
Tests for Hacker News and Lobsters.

These two are not found by searching - there is one of each - so the only question
worth testing is the one the rest of the scan cannot answer for them: does this
product belong there? Everywhere else that is decided by size and keyword density.
Here it is decided by the record, and the record has to be able to say no.

The case that matters most is therefore the negative one. A tool that recommends
Hacker News to every product is worth nothing, because Hacker News will bury a
submission that does not fit its taste without any rule being broken - and the
user only finds out afterwards, in public.

No network access: core.fetch is replaced.

Run:  python -m unittest discover -s tests
"""

from __future__ import annotations

import json
import os
import sys
import time
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from advertiser import aggregators, core, discovery, publish, rules  # noqa: E402

UA = "MutexxAdvertiser/test"
CONFIG = {"user_agent": UA,
          "safety": {"max_reddit_posts_per_day": 1, "min_days_between_same_subreddit": 45}}

GUIDELINES = b"<html><body>" + b"Be civil. Off-topic posts are removed. " * 20 + b"</body></html>"


def hits(count, points):
    return {"nbHits": count,
            "hits": [{"title": f"Story {i}", "points": points, "objectID": str(i),
                      "num_comments": 3} for i in range(min(count, 50))]}


class FakeNet:
    def __init__(self, routes, default=(404, b"<html>no</html>")):
        self.routes = routes
        self.default = default
        self.calls = []

    def fetch(self, url, *, user_agent, **kwargs):
        self.calls.append(url)
        for prefix, answer in self.routes.items():
            if url.startswith(prefix):
                return answer
        return self.default


class NetTestCase(unittest.TestCase):

    def use(self, routes, default=(404, b"<html>no</html>")):
        net = FakeNet(routes, default)
        real = core.fetch
        core.fetch = net.fetch
        self.addCleanup(lambda: setattr(core, "fetch", real))
        return net


class TopicRecord(NetTestCase):

    def test_a_topic_that_lands_is_counted(self) -> None:
        self.use({"https://hn.algolia.com": (200, json.dumps(hits(300, 40)).encode())})
        record = aggregators.hn_topic_record(["note taking"], UA)
        self.assertEqual(record["stories"], 300)
        self.assertEqual(record["median_points"], 40)

    def test_a_topic_nobody_posts_about_says_so(self) -> None:
        """The answer the whole module exists to be able to give."""
        self.use({"https://hn.algolia.com": (200, json.dumps(hits(0, 0)).encode())})
        record = aggregators.hn_topic_record(["grimoire encyclopedia"], UA)
        self.assertEqual(record["stories"], 0)
        self.assertEqual(record["examples"], [])

    def test_the_middle_story_counts_not_the_best_one(self) -> None:
        """One story that reached the front page must not make a dead topic look
        alive - which an average would let it do."""
        payload = hits(11, 0)
        payload["hits"][0]["points"] = 900
        self.use({"https://hn.algolia.com": (200, json.dumps(payload).encode())})
        self.assertEqual(aggregators.hn_topic_record(["x"], UA)["median_points"], 0)

    def test_the_window_is_passed_to_the_search(self) -> None:
        """Without the date filter a wave from 2019 would recommend a dead channel."""
        net = self.use({"https://hn.algolia.com": (200, json.dumps(hits(5, 5)).encode())})
        aggregators.hn_topic_record(["x"], UA, window_days=30)
        since = int(time.time()) - 30 * 86400
        self.assertTrue(any(f"created_at_i%3E{since}" in c or f"created_at_i>{since}" in c
                            for c in net.calls), net.calls)

    def test_a_search_that_fails_is_an_empty_record_not_a_crash(self) -> None:
        self.use({})
        self.assertEqual(aggregators.hn_topic_record(["x"], UA)["stories"], 0)


class HackerNewsEntry(NetTestCase):

    def routes(self, count=300, points=40):
        return {"https://hn.algolia.com": (200, json.dumps(hits(count, points)).encode()),
                "https://news.ycombinator.com/newsguidelines.html": (200, GUIDELINES),
                "https://news.ycombinator.com/showhn.html": (200, GUIDELINES)}

    def test_the_entry_points_at_the_submission_form(self) -> None:
        self.use(self.routes())
        entry = aggregators.hacker_news(["x"], UA)
        self.assertEqual(entry["submit_url"], "https://news.ycombinator.com/submit")

    def test_no_member_count_is_reported_rather_than_invented(self) -> None:
        """Hacker News publishes none. Zero here means 'not published' - see
        discovery._NO_SIZE_PLATFORMS, which is what keeps that zero from being read
        as an empty community."""
        self.use(self.routes())
        self.assertEqual(aggregators.hacker_news(["x"], UA)["subscribers"], 0)
        self.assertIn("hackernews", discovery._NO_SIZE_PLATFORMS)

    def test_unreachable_guidelines_leave_the_entry_marked_unreachable(self) -> None:
        self.use({"https://hn.algolia.com": (200, json.dumps(hits(5, 5)).encode())})
        self.assertFalse(aggregators.hacker_news(["x"], UA)["reachable"])


class LobstersEntry(NetTestCase):

    TAGS = json.dumps([
        {"tag": "python", "description": "Python programming", "active": True},
        {"tag": "rust", "description": "Rust programming", "active": True},
        {"tag": "ask", "description": "Questions for the community", "active": True},
    ]).encode()

    ABOUT = ("<html><body>Lobsters is a computing-focused community. "
             "Self-promotion: self-promo should be less than a quarter of your "
             "submissions. Be nice to each other.</body></html>").encode()

    def test_a_matching_tag_is_found(self) -> None:
        self.use({"https://lobste.rs/tags.json": (200, self.TAGS),
                  "https://lobste.rs/about": (200, self.ABOUT)})
        self.assertIn("rust", aggregators.lobsters(["rust"], UA)["matching_tags"])

    def test_a_topic_with_no_tag_gets_none(self) -> None:
        """Lobsters sorts everything by tag. No tag, no place for the topic - which
        is a fit of zero rather than a small one."""
        self.use({"https://lobste.rs/tags.json": (200, self.TAGS),
                  "https://lobste.rs/about": (200, self.ABOUT)})
        self.assertEqual(aggregators.lobsters(["crochet patterns"], UA)["matching_tags"], [])

    def test_very_short_keywords_do_not_match_everything(self) -> None:
        self.use({"https://lobste.rs/tags.json": (200, self.TAGS),
                  "https://lobste.rs/about": (200, self.ABOUT)})
        self.assertEqual(aggregators.lobsters(["a", "is"], UA)["matching_tags"], [])


class Scan(NetTestCase):

    ROUTES = {
        "https://hn.algolia.com": (200, json.dumps(hits(400, 40)).encode()),
        "https://news.ycombinator.com": (200, GUIDELINES),
        "https://lobste.rs/tags.json": (200, LobstersEntry.TAGS),
        "https://lobste.rs/about": (200, LobstersEntry.ABOUT),
    }

    def entries(self):
        self.use(self.ROUTES)
        return {e["platform"]: e for e in discovery.scan_aggregators(CONFIG, ["rust"])}

    def test_lobsters_is_never_green_because_you_may_not_have_an_account(self) -> None:
        """Accounts exist only by invitation. A green light on a site the user cannot
        post to is worse than no entry - it costs them the time to find out."""
        entry = self.entries()["lobsters"]
        self.assertEqual(entry["analysis"]["verdict"], rules.CONDITIONAL)
        self.assertIn("rule.invite_only", entry["analysis"]["labels"])

    def test_the_lobsters_ratio_rule_is_read_from_their_own_page(self) -> None:
        self.assertIn("rule.ratio", self.entries()["lobsters"]["analysis"]["labels"])

    def test_a_dead_topic_scores_zero_on_hacker_news(self) -> None:
        self.use({**self.ROUTES,
                  "https://hn.algolia.com": (200, json.dumps(hits(0, 0)).encode())})
        entries = discovery.scan_aggregators(CONFIG, ["grimoire encyclopedia"])
        hn = next(e for e in entries if e["platform"] == "hackernews")
        self.assertEqual(hn["fit_raw"], 0.0)

    def test_a_live_topic_scores_above_a_dead_one(self) -> None:
        live = self.entries()["hackernews"]["fit_raw"]
        self.use({**self.ROUTES,
                  "https://hn.algolia.com": (200, json.dumps(hits(3, 1)).encode())})
        dead = next(e for e in discovery.scan_aggregators(CONFIG, ["rust"])
                    if e["platform"] == "hackernews")["fit_raw"]
        self.assertGreater(live, dead)

    def test_many_stories_that_all_die_quietly_score_below_fewer_good_ones(self) -> None:
        """Volume alone is not interest. A topic posted constantly and ignored every
        time is a topic this audience has already answered."""
        self.use({**self.ROUTES,
                  "https://hn.algolia.com": (200, json.dumps(hits(400, 1)).encode())})
        ignored = next(e for e in discovery.scan_aggregators(CONFIG, ["rust"])
                       if e["platform"] == "hackernews")["fit_raw"]
        self.use({**self.ROUTES,
                  "https://hn.algolia.com": (200, json.dumps(hits(150, 60)).encode())})
        welcomed = next(e for e in discovery.scan_aggregators(CONFIG, ["rust"])
                        if e["platform"] == "hackernews")["fit_raw"]
        self.assertGreater(welcomed, ignored)


class Scoring(unittest.TestCase):

    def test_an_unpublished_member_count_is_not_scored_as_an_empty_community(self) -> None:
        """The zero means 'not published'. Counted as size it would push Hacker News
        below a forum with forty members."""
        hn = {"platform": "hackernews", "subscribers": 0, "fit_raw": 10,
              "posts_per_day": 2, "analysis": {"verdict": rules.OPEN}}
        tiny = {"platform": "forum", "subscribers": 40, "fit_raw": 10,
                "posts_per_day": 2, "analysis": {"verdict": rules.OPEN},
                "reachable": True}
        discovery.score_all([hn, tiny])
        self.assertGreater(hn["score"], tiny["score"])

    def test_a_ban_still_sinks_an_aggregator(self) -> None:
        hn = {"platform": "hackernews", "subscribers": 0, "fit_raw": 10,
              "posts_per_day": 2, "analysis": {"verdict": rules.FORBIDDEN}}
        other = {"platform": "hackernews", "subscribers": 0, "fit_raw": 2,
                 "posts_per_day": 1, "analysis": {"verdict": rules.OPEN}}
        discovery.score_all([hn, other])
        self.assertLess(hn["score"], other["score"])


class SafetyCatch(unittest.TestCase):

    def test_a_show_hn_counts_against_the_same_daily_limit(self) -> None:
        """A Show HN and a Reddit post on the same morning is the pattern people
        recognise as a launch campaign - and recognising it is what sinks it."""
        history = [{"platform": "reddit", "ts": int(time.time()), "community_id": "reddit:x"}]
        entry = {"id": "hackernews:showhn", "platform": "hackernews",
                 "analysis": {"verdict": rules.OPEN}}
        self.assertFalse(publish.check_guard(entry, CONFIG, history)["allowed"])


if __name__ == "__main__":
    unittest.main()
