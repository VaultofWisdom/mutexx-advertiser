"""
Tests for the whole-chain run.

The run is where the app stops being six tools and becomes one. That makes it the
place where two things can go wrong that are invisible everywhere else:

  * A stage that fails quietly takes the rest of the run with it. Four working
    stages and an honest note about the fifth are worth more than an empty
    interface the user has to diagnose, so every stage is tested for surviving the
    one before it going down.

  * The run could quietly become a way around the rules the app exists to keep. It
    must not publish, and its campaign must go through the same preparation the
    Campaign tab uses - not a second copy that drifts out of step with the safety
    catch. That is why prepare_queue is one function, and it is checked here.

No network access: the stages are replaced.

Run:  python -m unittest discover -s tests
"""

from __future__ import annotations

import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from advertiser import i18n, server  # noqa: E402


class Recorder:
    """Replaces one stage. Records that it ran; raises when told to."""

    def __init__(self, result=None, error: Exception | None = None):
        self.result = result
        self.error = error
        self.calls = 0

    def __call__(self, *args, **kwargs):
        self.calls += 1
        if self.error:
            raise self.error
        return self.result


class RunTestCase(unittest.TestCase):
    """Swaps every outward-facing stage for a recorder."""

    PRODUCT = {"slug": "p", "name": "Product", "url": "https://example.com",
               "category": "software_desktop", "keywords": ["thing"]}
    CONFIG = {"request_delay_seconds": 0.5, "anthropic": {"api_key": ""},
              "safety": {"max_reddit_posts_per_day": 1,
                         "min_days_between_same_subreddit": 45},
              "user_agent": "test",
              "discovery": {"max_communities": 10, "deep_scan_top_n": 5,
                            "min_subscribers": 400, "lemmy_min_subscribers": 40}}

    def setUp(self) -> None:
        self.saved: dict[str, object] = {}
        self.stubs: dict[str, Recorder] = {}

        self.patch(server.core, "load_config", Recorder(dict(self.CONFIG)))
        self.patch(server.core, "set_delay", Recorder(None))
        self.patch(server.products, "get", Recorder(dict(self.PRODUCT)))

        self.stubs["analysis"] = self.patch(
            server.analysis, "analyse", Recorder({"keywords": ["thing", "widget"]}))
        self.patch(server.analysis, "store", Recorder(None))
        # The realistic shape: analysis keywords are scored terms, and that score is
        # what the weighting reads.
        self.patch(server.analysis, "load", Recorder(
            {"keywords": [{"term": "thing", "score": 90.0},
                          {"term": "widget", "score": 12.0}]}))
        self.patch(server.analysis, "merged_keywords", Recorder(["thing", "widget"]))

        self.stubs["strategy"] = self.patch(
            server.strategy, "build", Recorder({"channels": [{"id": "communities"}]}))
        self.patch(server.strategy, "store", Recorder(None))
        self.patch(server.strategy, "load", Recorder({}))

        self.patch(server.seeds, "load_seeds", Recorder(
            {"subreddits": ["a"], "forums": [], "lemmy_instances": []}))
        self.stubs["seed_suggest"] = self.patch(
            server.seeds, "suggest_with_api", Recorder({"subreddits": [], "forums": []}))

        self.stubs["scan"] = self.patch(server, "_scan_platforms", Recorder(7))
        self.stubs["assets"] = self.patch(server, "_build_recommended_assets", Recorder(3))
        self.stubs["queue"] = self.patch(server, "prepare_queue", Recorder([{"a": 1}, {"b": 2}]))

    def patch(self, module, name, replacement):
        original = getattr(module, name)
        setattr(module, name, replacement)
        self.addCleanup(lambda m=module, n=name, o=original: setattr(m, n, o))
        return replacement

    def run_all(self, use_api=False, platforms=("reddit",)):
        server._run_everything("p", use_api, list(platforms))
        return dict(server.JOB)

    def messages(self, job, key="done"):
        return [i18n.render(m, "en") for m in (job.get("report") or {}).get(key, [])]


class TheChainRuns(RunTestCase):

    def test_every_stage_runs_in_order(self) -> None:
        self.run_all()
        for name in ("analysis", "strategy", "scan", "assets", "queue"):
            with self.subTest(stage=name):
                self.assertEqual(self.stubs[name].calls, 1)

    def test_the_report_says_what_each_stage_produced(self) -> None:
        """A run that says only 'done' leaves the user to go and look. The numbers
        are the point: two drafts and forty is the difference between a campaign and
        a rounding error."""
        done = self.messages(self.run_all())
        self.assertTrue(any("7 communities" in line for line in done), done)
        self.assertTrue(any("2 drafts" in line for line in done), done)

    def test_the_job_ends_not_running(self) -> None:
        self.assertFalse(self.run_all()["running"])


class OneStageFallingOverDoesNotStopTheRest(RunTestCase):

    def test_a_failed_analysis_leaves_the_later_stages_running(self) -> None:
        """The stage most likely to fail: it fetches somebody else's web page. If it
        took the run with it, a product page behind Cloudflare would mean no
        campaign at all - although everything after it works from the analysis
        already on file."""
        self.patch(server.analysis, "analyse", Recorder(error=RuntimeError("403")))
        job = self.run_all()
        self.assertEqual(self.stubs["scan"].calls, 1)
        self.assertEqual(self.stubs["queue"].calls, 1)
        self.assertTrue(any("Analysis failed" in line
                            for line in self.messages(job, "skipped")))

    def test_a_failed_strategy_still_writes_the_assets(self) -> None:
        self.patch(server.strategy, "build", Recorder(error=RuntimeError("boom")))
        self.run_all()
        self.assertEqual(self.stubs["assets"].calls, 1)

    def test_a_failed_campaign_is_reported_rather_than_swallowed(self) -> None:
        self.patch(server, "prepare_queue", Recorder(error=RuntimeError("boom")))
        job = self.run_all()
        self.assertFalse(job["running"])
        self.assertTrue(any("Campaign preparation failed" in line
                            for line in self.messages(job, "skipped")))

    def test_no_keywords_skips_the_scan_and_says_why(self) -> None:
        """Silently scanning nothing looks identical to scanning and finding nothing.
        The user has to be told which of the two happened."""
        self.patch(server.analysis, "merged_keywords", Recorder([]))
        job = self.run_all()
        self.assertEqual(self.stubs["scan"].calls, 0)
        self.assertTrue(any("no keywords" in line
                            for line in self.messages(job, "skipped")))


class SeedListsAreNotOverwritten(RunTestCase):

    def test_seeds_the_user_entered_are_left_alone(self) -> None:
        """Their list is the one thing in the chain the app did not produce. A run
        that quietly replaced it would destroy work no other stage can recover."""
        job = self.run_all(use_api=True)
        self.assertEqual(self.stubs["seed_suggest"].calls, 0)
        self.assertTrue(any("already there" in line
                            for line in self.messages(job, "skipped")))

    def test_without_a_key_the_run_says_what_to_do_instead(self) -> None:
        self.patch(server.seeds, "load_seeds", Recorder(
            {"subreddits": [], "forums": [], "lemmy_instances": []}))
        job = self.run_all(use_api=False)
        self.assertEqual(self.stubs["seed_suggest"].calls, 0)
        self.assertTrue(any("Anthropic key" in line
                            for line in self.messages(job, "skipped")))

    def test_an_empty_list_and_a_key_produces_a_suggestion(self) -> None:
        self.patch(server.seeds, "load_seeds", Recorder(
            {"subreddits": [], "forums": [], "lemmy_instances": []}))
        saved = self.patch(server.seeds, "save_seeds", Recorder(
            {"subreddits": ["x"], "forums": []}))
        self.run_all(use_api=True)
        self.assertEqual(self.stubs["seed_suggest"].calls, 1)
        self.assertEqual(saved.calls, 1)


class TheRunIsNotAWayAroundTheRules(RunTestCase):

    def test_it_publishes_nothing(self) -> None:
        """The whole point of the app is that the last click stays with a human. An
        automation that ended in a post would undo it - so the run must never reach
        the publishing code, however convenient that would be."""
        posted = self.patch(server.publish, "to_channels", Recorder(None)) \
            if hasattr(server.publish, "to_channels") else None
        logged = self.patch(server.publish, "log_post", Recorder(None))
        self.run_all()
        self.assertEqual(logged.calls, 0)
        if posted is not None:
            self.assertEqual(posted.calls, 0)

    def test_the_campaign_goes_through_the_shared_preparation(self) -> None:
        """Not a second copy of it. A duplicate would drift, and the half that
        drifted would be the safety catch - which is exactly the half that must
        hold on both paths."""
        self.run_all()
        self.assertEqual(self.stubs["queue"].calls, 1)


class Catalogue(unittest.TestCase):

    def test_every_stage_and_note_has_both_languages(self) -> None:
        keys = ["run.stage." + stage for stage in server.FULL_RUN_STAGES]
        keys += ["run.done.analysis", "run.done.scan", "run.done.campaign",
                 "run.skipped.analysis", "run.skipped.seeds_present",
                 "run.skipped.seeds_no_key", "run.skipped.scan_no_keywords",
                 "run.finished", "run.aborted", "tab.run"]
        for key in keys:
            with self.subTest(key=key):
                self.assertIn(key, i18n.EN)
                self.assertIn(key, i18n.DE)


if __name__ == "__main__":
    unittest.main()
