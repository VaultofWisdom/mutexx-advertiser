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

**Run everything** walks that whole line in one pass — analysis, strategy, seed lists,
scan, copy, prepared campaign — and hands back a report of what each stage produced and
what it left out. It publishes nothing. The run ends where the app always ends: with the
work laid out for a human to send.

Several products run side by side. The switcher at the top of the sidebar moves between them;
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

**Version 0.7.** What works:

* **A Windows app** - installer, its own window, Python included, nothing else to
  install. Updates are checked at start, signed, and installed after asking
* **Claude, ChatGPT or Gemini - by API key or with your own subscription.** With a key
  for Anthropic, OpenAI or Google Gemini the app writes on its own. Without one, "via chat"
  opens Claude (web or desktop app), ChatGPT or Gemini with the request ready; you send it
  and paste the answer back, checked like an API answer
* **Mutexx account** - optional. Signed in, products and campaigns sync between your
  computers; keys and passwords never do

* **A guided interface** - a sidebar that walks the seven stages in order and ticks off
  what is done, an overview with the next sensible step, live progress for every
  background job, posting mode as a focused step-by-step view. Dark house style, works on
  a phone-sized window too
* **One-click run** - the whole chain in a single pass, with a report of what each
  stage produced. A stage that fails does not stop the others; it says which one and why
* **Product profiles** - as many as you like, with separate data per product
* **Product analysis** - reads the product page, derives keywords, guesses category and
  pricing from signals in the text and shows the passage each guess rests on. With an
  Anthropic key it adds audiences, value propositions, positioning and objections
* **Strategy engine** - 16 channels in three kinds (owned, organic, paid), scored by
  category, pricing and budget, with a phase plan, a budget split and a stated reason for
  every rejected channel
* **Assets** - nine of them, each within its channel's character limits: search ads for
  Google and Microsoft, Meta and Reddit ads, directory listings, store listing, press kit,
  SEO fields, announcement for owned channels. Plus negative keywords and the destination
  URL with UTM tagging
* **Community discovery** - Lemmy through its open API, forums and wikis including link
  harvesting and Discourse forums read through their own API, Hacker News and Lobsters
  judged by the topic's actual record there, subreddits through the Reddit API
* **Rule analysis** with a traffic light and original quotes, for rules fetched
  automatically **and** for rules you paste in yourself
* **Drafts** in five angles, English and German, filled from profile and analysis - from
  templates or written freely through the Anthropic API
* **Batch preparation** of whole campaigns with scheduling and a posting mode
* **Fully automatic publishing** to your own Discord and Mastodon channels - always
  behind a confirmation, and without ever cutting the link off a long post
* **Safety catch** against exceeding the daily limit and against repeats
* Full manual inside the interface, 22 chapters, in both languages
* 230 tests, no network needed to run them, run on every push

Stated honestly, what is missing:

* **Further channels** are not connected yet - Stack Exchange, AlternativeTo, Product
  Hunt. See [the roadmap](docs/ROADMAP.md), stage 5.
* There is **no feedback loop**. The UTM tagging is in place, but nothing reports back
  which channel actually carried, so channels are still scored by keyword density rather
  than by results.
* **The templates are plain.** They assemble only what is in the profile and invent
  nothing - deliberate, but dry without an API key.
* The **Reddit part** needs approval from Reddit, see below.
* The installer is **not code-signed**, so Windows SmartScreen warns on first start.
  The update signature is a different thing and is in place.
* Windows only for the app. From source it runs anywhere Python does.

---

## Installation

### Windows app

Download `Mutexx-Advertiser_<version>_x64-setup.exe` from
[Releases](https://github.com/VaultofWisdom/mutexx-advertiser/releases) and run it. It
installs to `C:\Program Files\Mutexx Production\Mutexx Advertiser`, next to the other
Mutexx products, and brings its own Python - nothing else to install.

SmartScreen will warn that the publisher is unknown: the installer is not code-signed.
`SHA256SUMS.txt` on the release lets you check the file is the one that was built.

**Updates** are checked quietly at every start. When there is one, the app asks; Windows
then asks for administrator rights, because the app lives under Program Files. Every
update is checked against the Mutexx signing key before anything is installed. Your data
is never touched by an update - it does not live in the program folder.

### From source

No installation either. Python 3.10 or newer is enough; no third-party libraries are
used.

**Windows:** install Python from [python.org](https://www.python.org/downloads/) (tick
*Add python.exe to PATH*), download this repository as a ZIP or clone it, and double-click
**`Start.bat`**.

**Any system:**

```bash
git clone https://github.com/VaultofWisdom/mutexx-advertiser.git
cd mutexx-advertiser
python start.py
```

From source the interface opens in your browser at `http://127.0.0.1:8777`. The server
listens on `127.0.0.1` only and is not reachable from the network.

### Where your data lives

Configuration, keys and campaign data are plain JSON files in one folder:

| Copy | Folder |
|---|---|
| Windows | `%LOCALAPPDATA%\Mutexx Production\Mutexx Advertiser` |
| macOS / Linux | `~/.local/share/mutexx-advertiser` |
| Portable | next to the app - put an empty file named `portable` there |
| Anything else | set `MUTEXX_ADVERTISER_HOME` |

A copy that already has a `config.json` next to it (every copy from before 0.4) keeps
using it. Settings shows the folder in use. `config.example.json` shows what belongs in a
configuration; the real one is never committed.

Tests run without any extra tooling, and without the network:

```bash
python -m unittest discover -s tests
```

### Building the app

The app in `desktop/` is a thin [Tauri](https://tauri.app) shell: it starts the bundled
Python on a free local port, shows it in a native window, sends every outside link to
your own browser - where you are signed in to Reddit, Lemmy or the forum - and handles
updates. The Advertiser itself is the same Python program as above.

Needs Rust, Node and Python 3.12:

```bash
cd desktop
npm install
npm run build
```

`npm run build` first downloads Python's official embeddable distribution, checks it
against a pinned SHA-256, and copies the app next to it (`scripts/prepare_runtime.py`).
Everything stays readable in the install folder; nothing is packed into an opaque
executable. Releases are built by `.github/workflows/release.yml` from a tag `v*` and land
as a draft.

---

## Mutexx account

Optional, and off until you sign in (Settings -> Mutexx account). One account for all
Mutexx apps; each app has its own compartment, and the Advertiser's is `advertiser`.

| Synced | Never synced |
|---|---|
| product profiles, seed lists, analysis, strategy, assets, communities, the prepared campaign, the history | `config.json`: the Anthropic key, the Reddit secret and password, the Mastodon token, Discord webhooks |

The history is the reason it exists. The safety catch counts against it, and a second
computer that does not know what went out yesterday would propose the same community
again.

Sync runs every few minutes in the background. When the same thing was changed on two
computers at once, the other computer's version wins and yours is kept in
`data/account/conflicts/` - nothing is lost. The history is merged instead. The session is
encrypted with Windows' DPAPI, so a copied data folder carries no usable login.

---

## Security and privacy

The app runs a small web server on your machine, and a web server on your machine is
something every page in your browser can talk to. So it does not trust them:

* **Only its own page gets in.** Requests naming any host but `127.0.0.1`/`localhost`
  (DNS rebinding) are refused, and so is every write request from another origin or
  without a JSON body - which a foreign page cannot send without the browser asking
  first, and the app never says yes.
* **Keys never reach the browser.** The Anthropic key, the Reddit secret and password,
  the Mastodon token and Discord webhook URLs stay in the configuration file. The
  interface only learns *that* one is set, and an empty field on save keeps it.
* **The page loads nothing from anywhere else** and sends no referrer, enforced by a
  content security policy.
* No account required, no telemetry. The app talks to the services you use, to the sites
  it scans - with an honest user agent, one request at a time per host - and, only if
  you sign in, to the Mutexx account server.

---

## First steps

The short way: create a product on the **Overview** (name, page, one sentence), then press
**Run everything** and read the report. The overview then always shows the next sensible
step. The long way, if you would rather watch each stage:

1. **Product** — name, URL, one-liner, category, pricing, audience and monthly budget, then
   *Save profile*.
2. **Analysis** — *Run analysis*. It reads the product page and derives the keywords
   everything later searches with.
3. **Strategy** — read the channel plan. It also says what is not worth it, and why.
4. **Assets** — generate the copy for the channels you intend to work.
5. **Seed lists** — enter subreddits and forums, or ask for suggestions.
6. **Start scan** at the top of the window.
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
| organic | Communities and forums, aggregators (Hacker News, Lobsters), directories and portals, content and search, store listing, open-source visibility, trade press, mailing list, video | the app prepares, or supplies copy |
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

## Which keywords count

Not all of them equally, and the reason is a result rather than a theory. An early full
run for a note-taking app put `!wildlifephotography`, `!cartographyanarchy` and
`!learningrustandlemmy` into its top eight communities. They were there because the product
page contained the words "graph" and "thinking", and nothing said that "note taking" —
typed in by the user — was worth more than a word the page repeated.

So each keyword carries a weight. What you entered, and what the analysis names as a search
term, count fully; terms read off the page are scaled against the strongest of their own
kind and never reach that. The weak ones still count when scoring a community that matched
on something real — five weak matches are a signal — but they are not sent out as searches
of their own, because a search for "graph" returns the whole network and every hit then has
to be fetched, read and ruled on.

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

## Hacker News and Lobsters

Neither is discovered — there is one of each — so the work is a different one: deciding
whether your product belongs there at all.

For a subreddit, size and rules say most of it. For Hacker News they say nothing. It is
enormous, and it will bury a submission that does not fit its taste without a single rule
being broken — and you only find that out afterwards, in public. So the evidence is the
record itself: through the open Algolia search the last twelve months are counted. How
many stories on your topic were posted, and what score the middle one reached.

A note-taking app gets 612 stories and a median of 3 points — a busy topic that mostly
dies quietly. A demonology reference work gets none. Those are answers, and better ones
than any channel-fit heuristic would produce. The numbers and the stories behind them are
shown; you draw the conclusion.

The middle story counts rather than the average, because one submission that reached the
front page would otherwise make a dead topic look alive.

**Lobsters** hands out accounts by invitation only. Whatever its rules permit, without an
invitation you cannot post there — so it is never green, and the entry says why. Its own
rule ("self-promo should be less than a quarter of your submissions") is read from its
about page like any other.

Neither site publishes a member count, and neither gets one invented. Their zero means
"not published" rather than "nobody is there", so they are scored on the two figures that
are real for them instead of being ranked below a forum with forty members.

A Show HN counts against the same daily limit as a Reddit post. A launch spread across
both on the same morning is the pattern people recognise as a campaign — and recognising
it is what sinks it.

## Discourse forums

A forum running Discourse answers machine-readable questions about itself, so three
guesses become facts: its real member count, its activity over the last seven days
(rather than a lifetime average that flatters a forum busy in 2014), and its rules at
`/guidelines` and `/tos` instead of whichever front-page link happens to contain the word
"rules". Nothing has to be configured — a Discourse forum in the seed list is recognised
during the scan.

One thing it changes rather than sharpens. Many forums forbid self-promotion everywhere
and then keep one category for exactly that. Read without the category list such a forum
is red and drops out of every campaign, and the honest, invited post is the one that never
gets written. With it, the verdict becomes amber and names the category.

That is the only place in this app where a heuristic makes a verdict *more* permissive, so
it is fenced in: the category's **name and its own description** must both invite sharing —
"Projects" is where people discuss projects at least as often as where they announce their
own — amber is the ceiling and never green, and the sentence the verdict rests on is shown
with it.

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
advertiser/i18n_ui.py      translation catalogue, interface shell
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
advertiser/discourse_api.py Discourse forums, read-only - figures, rules, categories
advertiser/aggregators.py  Hacker News and Lobsters, read-only - the topic's record
                           (the whole-chain run lives in server.py: _run_everything)
advertiser/publish.py      owned channels, posting assistant, safety catch
advertiser/account.py      Mutexx account: sign-in and optional sync
advertiser/server.py       local server
advertiser/ui.html         interface

tests/                     python -m unittest discover -s tests

desktop/                   the Windows app: Tauri shell, installer, updater
desktop/scripts/prepare_runtime.py   embedded Python + app copy for the installer
```

Everything is stored as readable JSON in the data folder (see *Where your data lives*), per
product in `data/products/<name>/`. No telemetry; the account is optional.

## Imprint and privacy

Inside the app under *Help & settings -> Imprint & privacy*, in German (binding) and
English. The privacy notice describes what the app itself does: it keeps everything on
your computer, connects to GitHub for the update check and to the sites a scan reads, to
the services you set up yourself, and - only if you sign in - to the Mutexx account.
The provider is [Mutexx Production](https://mutexxproduction.de/impressum).

## Licence

No licence has been chosen yet. Until one is, the default applies: all rights reserved.
