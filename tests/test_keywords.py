"""
Tests for keyword weighting.

This exists because of a real result. A first full run for a note-taking app put
these into the top eight communities:

    !wildlifephotography@lemmy.world
    !cartographyanarchy@lemm.ee
    !learningrustandlemmy@lemmy.ml

None of them has anything to do with note taking. They got there because the
product page contained the words "graph" and "thinking", and nothing in the scoring
said that "note taking" - which the user typed in themselves - was worth more than a
word the page happened to repeat. Every keyword counted the same.

That is not a cosmetic ranking problem. The app's one promise is that it does not
propose posting your link where it does not belong, and a campaign that opens with a
note-taking app in a wildlife photography community is the thing that gets a domain
banned. So the weighting is pinned down here, in both directions: the strong terms
have to dominate, and the weak ones have to keep counting for something, because a
community that matches five weak terms is still a community that matches.

Run:  python -m unittest discover -s tests
"""

from __future__ import annotations

import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from advertiser import analysis, discovery  # noqa: E402


PRODUCT = {"slug": "p", "keywords": ["note taking", "markdown notes"]}

# The shape analysis.py really writes: the terms the user gave come back with a high
# score, the ones read off the page with whatever their frequency earned.
RESULT = {
    "search_terms": ["personal knowledge base"],
    "keywords": [
        {"term": "note taking", "score": 99.0, "source": "profil"},
        {"term": "obsidian", "score": 15.8, "source": "seite"},
        {"term": "thinking", "score": 13.4, "source": "seite"},
        {"term": "graph", "score": 9.8, "source": "seite"},
    ],
}


class WhatAKeywordIsWorth(unittest.TestCase):

    def setUp(self) -> None:
        self.weights = analysis.keyword_weights(PRODUCT, RESULT)

    def test_what_the_user_typed_counts_fully(self) -> None:
        self.assertEqual(self.weights["note taking"], 1.0)
        self.assertEqual(self.weights["markdown notes"], 1.0)

    def test_the_analysis_own_search_terms_count_fully(self) -> None:
        self.assertEqual(self.weights["personal knowledge base"], 1.0)

    def test_a_word_off_the_page_never_outweighs_one_the_user_named(self) -> None:
        """They know what the product is. The word counter only knows what was on
        the page."""
        for term in ("obsidian", "thinking", "graph"):
            with self.subTest(term=term):
                self.assertLess(self.weights[term], 1.0)

    def test_page_terms_keep_their_order(self) -> None:
        self.assertGreater(self.weights["obsidian"], self.weights["thinking"])
        self.assertGreater(self.weights["thinking"], self.weights["graph"])

    def test_a_weak_term_still_counts_for_something(self) -> None:
        """Zeroing them would throw away the only signal a small, precisely fitting
        community often gives."""
        self.assertGreater(self.weights["graph"], 0.0)

    def test_the_user_wins_when_a_term_appears_in_both(self) -> None:
        """'note taking' is in the profile and in the analysis at once. The page
        score must not be able to pull it down."""
        self.assertEqual(self.weights["note taking"], 1.0)


class StaleFilesDoNotBreakTheScan(unittest.TestCase):
    """analysis.json is read from disk. It may have been written by an older version
    or edited by hand, and a scan that dies on it is worse than one that shrugs."""

    def test_plain_strings_instead_of_scored_terms(self) -> None:
        weights = analysis.keyword_weights(PRODUCT, {"keywords": ["obsidian", "graph"]})
        self.assertIn("obsidian", weights)

    def test_rubbish_entries_are_skipped_not_raised_on(self) -> None:
        weights = analysis.keyword_weights(
            PRODUCT, {"keywords": [None, 42, {"term": "graph", "score": "not a number"},
                                   {"no_term": True}]})
        self.assertEqual(weights["note taking"], 1.0)
        self.assertIn("graph", weights)

    def test_no_analysis_at_all(self) -> None:
        weights = analysis.keyword_weights(PRODUCT, {})
        self.assertEqual(sorted(weights), ["markdown notes", "note taking"])


class WhichTermsAreWorthSearchingFor(unittest.TestCase):

    def test_the_weak_ones_are_not_sent_out_as_searches(self) -> None:
        """A search for 'graph' comes back with the whole network, and every hit then
        has to be fetched, read and ruled on. They still count when scoring a
        community that matched on something real."""
        terms = analysis.search_terms_of(analysis.keyword_weights(PRODUCT, RESULT))
        self.assertIn("note taking", terms)
        self.assertNotIn("graph", terms)

    def test_with_nothing_strong_it_searches_anyway(self) -> None:
        """A broad search beats no search. An empty term list would make the scan
        silently find nothing, which looks exactly like a scan that found nothing."""
        weights = analysis.keyword_weights({"keywords": []},
                                           {"keywords": [{"term": "graph", "score": 3.0}]})
        self.assertTrue(analysis.search_terms_of(weights))


class TheRankingActuallyChanges(unittest.TestCase):
    """The end of the story: the same two communities, before and after."""

    RIGHT = {"name": "pkms", "title": "Personal Knowledge Management",
             "description": "note taking, markdown notes and personal knowledge base talk",
             "sidebar": ""}
    WRONG = {"name": "wildlifephotography", "title": "Wildlife Photography",
             "description": "graph your sightings, thinking about composition, graph paper "
                            "sketches, thinking out loud, graph of migrations",
             "sidebar": ""}

    def test_unweighted_the_wrong_one_can_win(self) -> None:
        """Which is exactly what happened - this is the defect, kept as a test so it
        cannot quietly come back."""
        keywords = list(analysis.keyword_weights(PRODUCT, RESULT))
        right = discovery.lemmy_fit_score(self.RIGHT, keywords)
        wrong = discovery.lemmy_fit_score(self.WRONG, keywords)
        self.assertGreaterEqual(wrong, right)

    def test_weighted_the_right_one_wins(self) -> None:
        weights = analysis.keyword_weights(PRODUCT, RESULT)
        keywords = list(weights)
        right = discovery.lemmy_fit_score(self.RIGHT, keywords, weights)
        wrong = discovery.lemmy_fit_score(self.WRONG, keywords, weights)
        self.assertGreater(right, wrong)

    def test_a_phrase_counts_for_more_than_a_word(self) -> None:
        """Two words in a row are far less of a coincidence than one."""
        weights = {"note taking": 1.0, "note": 1.0}
        phrase = discovery.lemmy_fit_score(
            {"name": "", "title": "", "description": "note taking", "sidebar": ""},
            ["note taking"], weights)
        word = discovery.lemmy_fit_score(
            {"name": "", "title": "", "description": "note", "sidebar": ""},
            ["note"], weights)
        self.assertGreater(phrase, word)

    def test_without_weights_nothing_changes(self) -> None:
        """Communities added by hand are scored through the same function with no
        weights on file. That path has to keep working exactly as before."""
        keywords = ["note taking", "graph"]
        data = {"display_name": "x", "title": "note taking", "public_description": "graph",
                "description": ""}
        self.assertGreater(discovery.fit_score(data, keywords), 0)


if __name__ == "__main__":
    unittest.main()
