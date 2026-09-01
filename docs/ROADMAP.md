# Roadmap: from outreach helper to marketing tool

## Where this is going

The Advertiser is meant to be a **public tool**: a user describes their product, the tool
analyses it, derives a marketing strategy from it, and carries that strategy as far as it
responsibly can. With a budget or without — which channels make sense at all is decided
from the product profile, not from the user's gut feeling.

What existed at the start was the execution half for exactly one channel type (communities
and forums) and exactly one product (a demonology reference work). The mechanics were
product-neutral; the content was not. The rebuild consists of inserting the two missing
stages **above** the existing execution — analysis and strategy — and then widening
execution across more channels.

```
Product profile  ->  Analysis  ->  Strategy  ->  Assets  ->  Channels  ->  Execution
(user input)         (what it     (what is      (the copy)   (where       (drafts,
                      is, for      worth it,                  exactly)     dates,
                      whom)        at what                                 posting)
                                   budget)
```

## The one hard limit

The tool **spends no money**. Paid campaigns are prepared in full — ad copy within the
channel's character limits, audiences, keywords, budget split, bidding strategy — and then
handed over. A human presses "activate campaign" in their own ad account.

That is the same decision that already applies to posting in other people's communities,
for the same reason: the last click is the point at which a human notices the damage before
it happens. With ads that click costs real money; with communities it costs the domain.

## Stages

### Stage 1 — Product profile (foundation) — **done**

`config.site` knew exactly one product and had no field for anything marketing needs.
Replaced by `config.products[]` with an active profile:

* identity: name, URL, version, one-liner, full description
* classification: category, pricing model, price
* market: audience, regions, languages
* frame: monthly budget, tone
* links: repository, download, docs, press kit, screenshots

Plus data separation: `data/products/<slug>/` per product, otherwise two campaigns mix in
the same `communities.json`. Existing configurations are migrated on first start.

### Stage 2 — Product analysis — **done**

New module `analysis.py`. Without an API key: the product URL is fetched, title, meta
description and body text evaluated, keyword candidates won from frequencies and word
pairs, category guessed from signals. With an Anthropic key additionally a free analysis:
audience segments, value propositions, positioning against alternatives, objections to
expect, the audience's own search terms, suitable tone.

The result is not decoration — it feeds the keyword list of the community search and the
drafts. Before this, the user had to invent their own keywords.

### Stage 3 — Strategy engine — **done**

New module `strategy.py`. Profile and analysis produce a scored channel plan: which
channels suit this product, in what order, with what effort, what lead time, and — where
there is a budget — with what split. Each carries a reason and one concrete first step.

The channel catalogue separates three kinds:

* **owned** — your own channels, playable immediately and without anyone's permission
* **organic** — communities, forums, directories, press, content and search
* **paid** — Google Search and Shopping, Meta, Reddit, Microsoft, TikTok, YouTube

Paid channels appear only when a budget is on file *and* the product fits. Google Shopping
without physical goods is not a suggestion, it is a mistake.

### Stage 4 — De-niche the drafts — **done**

The five angles stay; their text is filled from the profile instead of from demonology. The
system prompt of the API variant became product-neutral. Templates are available in English
and German.

### Stage 5 — Channels that work without Reddit approval — open

Reddit's Responsible Builder Policy stays closed. Replacements and additions, all with an
open or readably accessible interface: Lemmy, Hacker News and Lobsters, Discourse instances
(`/faq` is machine-readable), Stack Exchange, and for software additionally AlternativeTo,
Product Hunt and download portals. A new channel only has to supply a discovery entry and
rule texts for `rules.analyse` — the architecture already carries that.

**This is the largest remaining gap.** Without it, most users' scans find only what they
enter as forums themselves.

### Stage 6 — Assets — **done**

Nine assets in `assets.py`, each within its channel's character limits: search ads for
Google and Microsoft, Meta and Reddit ads, directory and portal listings, store listing,
press kit, page title and meta description, announcement for owned channels.

Two promises that separate the module from a text generator:

* **Character limits are hard.** Every field is checked after generation; anything that had
  to be cut is marked. AI copy runs through the same check — language models count
  characters notoriously badly, and Google counts exactly.
* **Nothing is invented.** The templates assemble only what is in the profile and the
  analysis. Two cases turned up while building and are pinned down by tests: "Free trial"
  on a subscription promises a trial period that is nowhere on file, and the category label
  "Desktop software (Windows, macOS, Linux)" becomes a platform promise nobody made once it
  is printed in a press kit.

Plus per channel a list of negative keywords and the destination URL with UTM tagging.

### Stage 7 — Feedback — partial

The UTM tagging is in place (stage 6, `assets.utm_url`). What is missing is the return
direction: a report of which channel actually carried. Only then may `score_all` learn from
real numbers instead of keyword density.

### Stage 8 — Hardening — partial

94 tests cover the traffic light, the strategy promises, the draft templates, the character
limits of the assets and the completeness of the translation catalogue. The three original
defects are fixed: `one_liner` is editable, `/api/draft` no longer throws a 500 on an
unknown angle, the old branding is gone.

Open: no test for `discovery.py` and `server.py` — there is no coverage of the scan flow
against broken HTML responses and timeouts.

### Stage 9 — House style and two languages — **done**

The interface follows the Mutexx Production house style, measured off
mutexxproduction.de: ground `#0a0a0f`, panels `#121218`, an indigo-to-violet gradient
(`#9810fa` → `#4f39f6`) for primary actions, the same gradient lighter as a text fill for
headings, pill buttons, 16px panel radius, the same system font stack. The traffic-light
colours come from the same palette.

English is the default, German is the second language, and the switch in Settings applies
immediately and everywhere. The mechanism is in `i18n.py`: **no translated prose is stored
anywhere.** A saved strategy plan holds the key `channel.communities.what`, never the
sentence. The catalogue goes to the browser once and the interface resolves keys locally —
which is what makes the switch instant and, more importantly, correct for anything
generated earlier.

Deliberately excluded from the switch: generated marketing content. Drafts and ad copy
follow the languages set on the *product*, because they are written for an audience rather
than for the operator.

Still open in this stage: the Python source comments and docstrings are still largely
German. That does not affect the product, but for a public repository with an English-first
interface it is inconsistent.

### Stage 10 — Downloadable Windows 11 app — open

Today the tool runs from source. The target is a download that a non-developer can use.

The constraint that matters: the app's whole pitch is trustworthiness, and it advertises
"no dependencies, no telemetry". A packaging route that trips antivirus heuristics would
undo more than it gains. That rules out the obvious one-file bundlers as a first choice.

The route that preserves the property: a folder distribution built on Python's official
embeddable distribution plus a small launcher, zipped, and optionally wrapped in an
installer. Everything stays inspectable, nothing is packed into an opaque executable.

### Stage 11 — Browser extension — open, and worth it for exactly one job

The valuable job is narrow and real: Reddit's API is closed, so community rules have to be
pasted in by hand. An extension that reads the rules off the page you are currently looking
at and hands them to the local app — with the traffic light computed on arrival — removes
precisely that friction.

A second, smaller use: filling a community's submission form from the prepared draft
without going through the clipboard.

Anything beyond that would be a second interface to maintain for no gain. The extension
should stay a collector for the local app, not become the app.
