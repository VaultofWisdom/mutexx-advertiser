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

### Stage 5 — Channels that work without Reddit approval — partial

Reddit's Responsible Builder Policy stays closed. Replacements and additions, all with an
open or readably accessible interface: Lemmy, Hacker News and Lobsters, Discourse instances
(`/faq` is machine-readable), Stack Exchange, and for software additionally AlternativeTo,
Product Hunt and download portals. A new channel only has to supply a discovery entry and
rule texts for `rules.analyse` — the architecture already carries that, and Lemmy
confirmed it: the whole channel is one API module plus one `scan_*` function.

**Lemmy is done** (`lemmy_api.py`, `discovery.scan_lemmy`). It needs no approval, no key
and no account. Because it federates, the seed list holds instances rather than
communities, and a search on a few large ones reaches most of the network.

**Discourse is done** (`discourse_api.py`, inside `_probe_forum`). It is not a new channel
but a sharper reading of the existing one: `/about.json` gives the real member count and
the activity of the last seven days, `/guidelines` and `/tos` give the rules at a known
address, and `/categories.json` gives something no scrape could — the category where
sharing your own work is invited. Forums that forbid promotion everywhere and keep one
category for exactly that used to read as red and drop out of every campaign.

That last part is the only heuristic in this app that makes a verdict *more* permissive,
so it is fenced in on three sides: name **and** description must both invite sharing,
amber is the ceiling, and the sentence it rests on is carried into the evidence. The tests
for it are written around the false positive, not the true one.

**Hacker News and Lobsters are done** (`aggregators.py`). They needed a different shape
from everything above: neither is discovered, because there is one of each. What has to be
worked out is whether the product belongs there — and for Hacker News, size and rules say
nothing at all about that. It is enormous and it buries what does not fit its taste without
any rule being broken.

So the evidence is the record. Through the open Algolia search the last twelve months are
counted: how many stories on this topic, and what score the middle one reached. The median
rather than the average, because one front-page story would otherwise make a dead topic
look alive; volume discounted by score, because a topic posted constantly and ignored every
time is a topic the audience has already answered. A note-taking app gets 612 stories at a
median of 3; a demonology reference work gets none. Both are answers.

This is the first thing in the app that scores a channel on evidence rather than on keyword
density, and it is a small, self-contained preview of what stage 7 wants for all of them.

Two smaller decisions came out of it:

* **Lobsters is never green.** Accounts exist by invitation only, so without one the rules
  do not matter. A green light on a site you cannot post to costs the user the time to find
  that out.
* **A member count nobody publishes is not a member count of zero.** Scored as size, that
  zero pushed Hacker News below a forum with forty members. Platforms that publish none are
  now scored on the figures that are real for them (`discovery._NO_SIZE_PLATFORMS`).

While reading Lobsters' rules a defect turned up in the traffic light itself, which is
recorded under stage 8.

Three things did not carry over from Reddit and are worth knowing before adding the next
channel, because every one of them is a decision about the traffic light rather than about
plumbing:

* **No structured rule list.** Lemmy keeps a community's rules in its description or
  nowhere. A community that wrote nothing therefore gets grey, not green — otherwise the
  app would report a green light off an instance's welcome text, which is precisely the
  false green that costs the domain.
* **Communities only moderators may post in.** Red, not amber: no draft gets past it.
* **Size does not compare across networks.** Against one shared scale every Lemmy entry
  ranks as tiny and the list always says "go to Reddit". Each platform is now measured
  against its own ceiling (`discovery._SIZE_SCALE`).

The safety catch's daily limit was widened to cover Reddit and Lemmy together, not each
separately — a second network that escaped the limit would have made it worthless.

**What remains is still the largest gap.** Without the rest, a scan for a product whose
audience is not on Reddit or Lemmy finds only the forums the user entered themselves.

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

### Stage 12 — The chain in one run — **done**

Six stages that each had to be started by hand were six chances to stop halfway, and the
order between them is not obvious from the interface: the analysis produces the keywords
the scan searches with, the strategy decides which copy is worth writing, the scan produces
what the campaign is built from. Getting that order wrong produces a plausible-looking
result built on nothing.

`_run_everything` walks all six and reports per stage what it produced. Three decisions in
it are worth keeping:

* **A stage that fails does not stop the run.** Four working stages and an honest note
  about the fifth are worth more than an empty interface the user has to diagnose. The
  analysis is the likeliest to fail — it fetches somebody else's page — and everything
  after it falls back to the analysis already on file.
* **Seed lists the user entered are never overwritten.** They are the one thing in the
  chain the app did not produce, and no other stage could recover them.
* **The campaign goes through the same `prepare_queue` as the Campaign tab.** A second
  copy would drift, and the half that drifted would be the safety catch.

It publishes nothing, and the tests hold it to that. The run is a way to reach the last
click faster, not a way around it.

### Stage 13 — Keyword weighting — **done**

Found by looking at the output of the first full run rather than by reasoning about the
code. For a note-taking app the top eight communities included `!wildlifephotography`,
`!cartographyanarchy` and `!learningrustandlemmy` — all because the product page contained
"graph" and "thinking", and `fit_score` counted every keyword the same.

That is not a ranking nicety. The app's one promise is that it does not propose posting
your link where it does not belong, and a campaign opening with a note-taking app in a
wildlife photography community is how a domain gets banned.

`analysis.keyword_weights` now returns what each term is worth: 1.0 for what the user
entered and what the analysis names as a search term, scaled and capped below that for
terms read off the page. `search_terms_of` separates the two jobs — everything is scored
against, only the strong ones are searched with, because a search for "graph" comes back
with the whole network and each hit then costs a fetch, a read and a verdict.

The defect itself is kept as a test: unweighted, the wrong community wins; weighted, the
right one does. Communities added by hand still go through the same function with no
weights, and that path is tested to be unchanged.

### Stage 7 — Feedback — partial

The UTM tagging is in place (stage 6, `assets.utm_url`). What is missing is the return
direction: a report of which channel actually carried. Only then may `score_all` learn from
real numbers instead of keyword density.

### Stage 8 — Hardening — partial

191 tests cover the traffic light, the strategy promises, the draft templates, the character
limits of the assets, the completeness of the translation catalogue, the Lemmy channel (its
verdicts, the deduplication across federated instances, the size scale and the daily limit),
the Discourse path (identification, the rule pages, and above all the showcase category that
turns a red verdict amber) and the aggregators (above all their ability to answer "not
here") and the whole-chain run (that every stage runs, that one failing does not stop
the others, that seed lists survive it, and that it never reaches the publishing code) —
all against stubbed responses rather than the live network. The keyword weighting is
covered in both directions: the strong terms must dominate, and the weak ones must keep
counting for something.

**One real defect found and fixed along the way.** The ratio rule was only recognised in
`9:1` notation. Written out — "self-promo should be less than a quarter of your
submissions", "no more than 10% of your posts", "at most a third", and the German
equivalents — it was not recognised at all, and every one of those came back **green**: a
promotion limit read as no limit. It surfaced from Lobsters' own wording, which is exactly
the shape most forums use. Both directions are pinned down now: the quantity and the
promotion word have to appear together, so "no more than 3 posts per day" stays what it
is. The three original
defects are fixed: `one_liner` is editable, `/api/draft` no longer throws a 500 on an
unknown angle, the old branding is gone.

**0.4 closed the server's boundary** (`tests/test_server.py`, 25 tests against a real
server on a free port). Before it, the app trusted every request that reached
127.0.0.1 — and every page open in the browser can reach 127.0.0.1. A hostile page could
have rewritten the configuration, started runs, posted to the owned channels and, through
DNS rebinding, read every stored key. Now a foreign Host header is refused, so is any
write from another origin or without a JSON body, and the keys no longer travel to the
browser at all: the interface learns only *that* one is set, and an empty field on save
keeps it. Writing the test turned up one more defect of its own: a refused request was
answered before its body had been read, and Windows resets such a connection — the caller
saw a network error instead of the 403.

Three smaller defects found by the first live run of 0.4, all fixed:

* Mastodon and Discord posts were cut at the character limit, and the link sits at the
  end of nearly every post — so the one part the post exists for was the part that went.
  `publish.fit_post` shortens the body and puts the link back.
* The German post templates wrote "bewaehrt", "hoere", "Loesungen" — ASCII stand-ins that
  would have gone out verbatim under the user's name.
* Scan progress messages were German literals in an English interface.

The five copies of the Anthropic request are now one (`core.ask_claude_json`): current
default model, a budget that leaves room for the model's thinking, a timeout measured in
minutes rather than the 25 seconds a forum page gets, and a refusal reported as a refusal
instead of as "no JSON found".

Open: `scan_reddit` and `scan_forums` are still untested — there is no coverage of the
scan flow against broken HTML responses and timeouts. `_probe_forum` is covered for both
branches, which is the half that was riskiest.

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

**0.4 rebuilt the interface around the workflow** instead of around a row of twelve tabs:
a sidebar that lists the seven stages in their working order and ticks off what is done,
an overview that names the next sensible step and the day's safety-catch budget, a live
progress pill for every background job, posting mode as a focused overlay, toasts and
proper dialogs instead of `alert()` and `prompt()`, and a layout that holds at phone
width. Saving one thing no longer throws the user back to the top of the page or
regenerates the open draft, and unsaved edits in the profile survive a background refresh.

Still open in this stage: the Python source comments and docstrings are still largely
German. That does not affect the product, but for a public repository with an English-first
interface it is inconsistent.

### Stage 10 — Downloadable Windows 11 app — **done in 0.5**

Built the way this stage asked for: a Tauri shell (`desktop/`) around Python's official
embeddable distribution, every file readable in the install folder, nothing packed into
an opaque executable. Installer, start menu group and data folder follow the Mutexx
folder rule; updates are signed with the Mutexx key and installed after asking. The one
thing still missing is code signing - the SmartScreen warning on first start stays until
a certificate is bought.

The original reasoning, kept for why it looks the way it does:

Today the tool runs from source. The target is a download that a non-developer can use.

The constraint that matters: the app's whole pitch is trustworthiness, and it advertises
"no dependencies, no telemetry". A packaging route that trips antivirus heuristics would
undo more than it gains. That rules out the obvious one-file bundlers as a first choice.

The route that preserves the property: a folder distribution built on Python's official
embeddable distribution plus a small launcher, zipped, and optionally wrapped in an
installer. Everything stays inspectable, nothing is packed into an opaque executable.

0.4 laid the ground for it: data no longer has to live next to the app. An installed copy
under `C:\Program Files\Mutexx Production\Mutexx Advertiser` cannot write there, so it uses
`%LOCALAPPDATA%\Mutexx Production\Mutexx Advertiser` — the folder rule every Mutexx
product follows — while copies run from source keep their existing `config.json`.

### Stage 11 — Browser extension — open, and worth it for exactly one job

The valuable job is narrow and real: Reddit's API is closed, so community rules have to be
pasted in by hand. An extension that reads the rules off the page you are currently looking
at and hands them to the local app — with the traffic light computed on arrival — removes
precisely that friction.

A second, smaller use: filling a community's submission form from the prepared draft
without going through the clipboard.

Anything beyond that would be a second interface to maintain for no gain. The extension
should stay a collector for the local app, not become the app.
