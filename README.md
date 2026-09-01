# Mutexx Advertiser

You describe your product. The tool reads the product page, works out what the product is
and who it is for, picks the marketing channels that actually suit it — with a budget or
without — and carries them as far as it responsibly can.

The difference from the usual "post everywhere" tools is deliberate: the Advertiser reads
the target community's rules before every post and **refuses to prepare anything where
self-promotion is forbidden**. It publishes automatically only in channels you own. For
everything else it prepares the work in full — a human sends it. That is the difference
between a campaign that grows and a banned domain.

A **Mutexx Production** tool.

---

## The sequence

```
Product profile  ->  Analysis  ->  Strategy  ->  Assets  ->  Campaign
(what you enter)    (what it is,  (what is      (the copy   (communities,
                     who for)      worth it,     for those    drafts, dates,
                                   at what        channels)   posting mode)
                                   budget)
```

Several products run side by side. The switcher at the top right moves between them;
communities, queue and history are kept strictly apart per product.

---

## The hard limit: no money

The tool **does not spend money** and cannot. Paid campaigns are prepared in full — ad copy
within each channel's character limits, audiences, keywords, budget split — and then handed
over. You press *activate campaign* in your own ad account.

This is the same decision that applies to posting in other people's communities, for the
same reason: the last click is the point where a human notices the damage before it
happens. With ads that click costs real money; with communities it costs the domain.

---

## Language

English is the default. German is available, and the switch in **Settings** takes effect
immediately, everywhere — including plans and assets generated weeks earlier.

That works because no translated prose is ever stored. A saved strategy plan holds the key
`channel.communities.what`, not the sentence; the interface resolves keys against a
catalogue it receives once. The language was never baked in, so it can be changed after
the fact.

One thing deliberately does **not** switch: generated marketing content. Post drafts and ad
copy follow the languages set on the *product*, because they are written for an audience,
not for you. A German product advertised in a German forum keeps its German post while you
read the interface in English.

---

## State

**Version 0.3.** What works:

* **Product profiles** — as many as you like, with separate data per product
* **Product analysis** — reads the product page, derives keywords, guesses category and
  pricing from signals in the text and shows the passage each guess rests on. With an
  Anthropic key it adds audiences, value propositions, positioning and objections
* **Strategy engine** — 16 channels in three kinds (owned, organic, paid), scored by
  category, pricing and budget, with a phase plan, a budget split and a stated reason for
  every rejected channel
* **Assets** — nine of them, each within its channel's character limits: search ads for
  Google and Microsoft, Meta and Reddit ads, directory listings, store listing, press kit,
  SEO fields, announcement for owned channels. Plus negative keywords and the destination
  URL with UTM tagging
* **Community discovery** — Lemmy through its open API, forums and wikis including link
  harvesting, subreddits through the Reddit API
* **Rule analysis** with a traffic light and original quotes, for rules fetched
  automatically **and** for rules you paste in yourself
* **Drafts** in five angles, English and German, filled from profile and analysis — from
  templates or written freely through the Anthropic API
* **Batch preparation** of whole campaigns with scheduling and a posting mode
* **Fully automatic publishing** to your own Discord and Mastodon channels
* **Safety catch** against exceeding the daily limit and against repeats
* Full manual inside the interface, 19 chapters, in both languages

Stated honestly, what is missing:

* **Further channels** are not connected yet — Hacker News and Lobsters, Discourse
  instances, Stack Exchange, AlternativeTo, Product Hunt. Lemmy is done; see
  [the roadmap](docs/ROADMAP.md), stage 5, for the rest.
* There is **no feedback loop**. The UTM tagging is in place, but nothing reports back
  which channel actually carried, so channels are still scored by keyword density rather
  than by results.
* **The templates are plain.** They assemble only what is in the profile and invent
  nothing — deliberate, but dry without an API key.
* The **Reddit part** needs approval from Reddit, see below.
* It is not yet a **downloadable Windows app**. Today it runs from source.

---

## Installation

There is none. Python 3.10 or newer is enough; no third-party libraries are used.

```bash
git clone https://github.com/VaultofWisdom/mutexx-advertiser.git
cd mutexx-advertiser
python start.py
```

On Windows, double-clicking **`Start.bat`** is enough. The interface opens in your browser
at `http://127.0.0.1:8777`. The server listens on `127.0.0.1` only and is not reachable
from the network.

On first start the app creates a `config.json`. `config.example.json` shows what belongs in
it. The real `config.json` and the `data/` folder are excluded by `.gitignore` — that is
where credentials live.

Tests run without any extra tooling (118 of them, under a second):

```bash
python -m unittest discover -s tests
```

---

## First steps

1. **Product** — name, URL, one-liner, category, pricing, audience and monthly budget, then
   *Save profile*.
2. **Analysis** — *Run analysis*. It reads the product page and derives the keywords
   everything later searches with.
3. **Strategy** — read the channel plan. It also says what is not worth it, and why.
4. **Assets** — generate the copy for the channels you intend to work.
5. **Seed lists** — enter subreddits and forums, or ask for suggestions.
6. **Start scan** at the top right.
7. **Campaign** — *Prepare campaign*, then *Start posting mode*.

The full manual is in the **Manual** tab inside the app.

---

## The traffic light

| Level | Meaning | What to do |
|---|---|---|
| green | no promotion ban found in the rules | post, but post something worth reading |
| amber | allowed with conditions: ratio, flair, collection thread, moderator approval | work the checklist |
| red | self-promotion explicitly forbidden | do not post |
| grey | rules could not be fetched | read them yourself |

For every assessment the app shows the **original quotes** it rests on. The analysis is a
heuristic, not a substitute for reading — and it is the most thoroughly tested part of the
code, because a false green here costs the domain.

---

## The channels

The strategy picks from three kinds. The column that matters is the last one: how far the
app carries the channel.

| Kind | Channels | Automation |
|---|---|---|
| owned | Owned channels, product page | the app publishes itself |
| organic | Communities and forums, directories and portals, content and search, store listing, open-source visibility, trade press, mailing list, video | the app prepares, or supplies copy |
| paid | Google search ads, Google Shopping, Meta, Reddit, Microsoft, YouTube/TikTok, sponsorship | the app prepares; you run it in your own ad account |

Channels that do not fit are not dropped quietly — they are listed under *Rejected* with a
reason. A recommendation without a counter-check is an opinion, not advice.

---

## Assets

For every channel in the strategy there is finished copy — within that channel's character
limits.

Two promises separate this from a text generator:

**The character limits are hard.** Google rejects an ad headline of 31 characters, not
"roughly". Every field shows its length; anything that had to be cut is marked. AI copy runs
through the same check — language models count characters notoriously badly.

**Nothing is invented.** The templates assemble only what is in the profile and the
analysis. Two cases turned up while building this and are now pinned down by tests: "Free
trial" on a subscription promises a trial period that may not exist, and the category label
"Desktop software (Windows, macOS, Linux)" becomes a platform promise nobody made once it
is printed in a press kit. Sentences like those go unnoticed precisely because they sound so
familiar — and they still end up published in the user's name.

---

## Angles

| Angle | For |
|---|---|
| Share a resource | green communities, direct usefulness |
| Ask for corrections | specialist communities — works best there |
| Show the project | developer and project communities |
| A question with context | communities with a ratio rule |
| Forum introduction | classic forums |

All templates follow one rule: **value first, link second.** A post that would be worth
reading without the link does not get read as advertising.

Templates cannot translate. If the target community is English-speaking and the product
copy in the profile is only German, the draft stays German — and the app says so explicitly
rather than shipping a half-German post.

---

## Lemmy

The one channel that needs nobody's approval. The API is open — no registration, no key,
no account — so the scan reaches it out of the box.

Lemmy federates: an instance knows every community it has ever exchanged posts with. A
search on a few large instances therefore reaches most of the network, which is why the
seed list holds **instances** rather than communities. Left empty it uses a default set,
two German-speaking instances included.

Two differences from Reddit change what the traffic light means there:

**There is no structured rule list.** A community's rules are in its description or
nowhere. A community that wrote nothing therefore gets grey, not green — silence is not
permission, and the instance's welcome text is not the community's answer. A ban still
counts: grey is a downgrade from green, never an upgrade from red.

**Some communities only moderators may post in.** That is red rather than amber. No
draft gets past it, however good the text is.

Size is measured against Lemmy's own ceiling. A community with 8,000 subscribers is a
large one here and a small one on Reddit; against a shared scale the ranking would always
say "go to Reddit", whatever the rules there said.

The safety catch counts Reddit and Lemmy against one daily limit rather than one each.
The damage it exists to prevent — the same link everywhere within a day — does not care
which network it happened on.

## Reddit

Reddit's *Responsible Builder Policy* has allowed no self-service access since late 2025:

> "Approval is required: You must request access and get explicit approval before accessing
> any Reddit data through our API"

Without approval the automatic subreddit search stays empty. Everything else works without
restriction, and subreddits can be added by hand — paste the sidebar rules in and they go
through exactly the same analysis. There is no workaround and there should not be one:
scraping without approval risks precisely what this tool exists to prevent.

With approval: create an app of type *script* at <https://www.reddit.com/prefs/apps>, put
the client ID and secret into Settings, and use *Test connection*. The app reads only and
has no write access whatsoever.

---

## What this tool does not do

It does not post automatically into other people's communities. That is not a missing
feature but a decision: distributing the same link across many communities is spam under
practically every platform's rules. Reddit puts it this way:

> "Apps must not engage in spamming activity through automated posts, comments, or direct
> messages. This includes posting identical or substantially similar content across
> subreddits."

The usual consequence is not a single account ban but a ban on the promoted domain — at
which point the links other people set voluntarily disappear too. The Advertiser takes
everything off your hands except the last click, and that last click is why the campaign
survives.

And it does not spend money. See above.

---

## Layout

```
Start.bat                  Windows launcher
start.py                   entry point
config.example.json        example configuration
docs/ROADMAP.md            where the tool is going

advertiser/core.py         HTTP, rate limiting, configuration, storage
advertiser/i18n.py         translation catalogue and machinery
advertiser/i18n_content.py translation catalogue, long form: channels and assets
advertiser/manual.py       the in-app manual, both languages
advertiser/products.py     product profiles and migration
advertiser/analysis.py     product analysis: read the page, keywords, guess category
advertiser/strategy.py     channel catalogue, scoring, budget split, phase plan
advertiser/assets.py       assets within channel character limits, UTM
advertiser/seeds.py        per-product seed lists
advertiser/discovery.py    community discovery and scoring
advertiser/rules.py        rule analysis and traffic light
advertiser/drafts.py       drafts and angles
advertiser/reddit_api.py   Reddit access, read-only
advertiser/lemmy_api.py    Lemmy access, read-only - open, no approval needed
advertiser/publish.py      owned channels, posting assistant, safety catch
advertiser/server.py       local server
advertiser/ui.html         interface

tests/                     python -m unittest discover -s tests
```

Everything is stored as readable JSON next to the app, per product in
`data/products/<name>/`. There is no cloud service, no account and no telemetry.
