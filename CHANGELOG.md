# Changelog

## 0.4.0

The release that makes the tool usable by someone who did not build it.

**Interface**

* Rebuilt around the workflow: a sidebar listing the seven stages in working order with
  their state, an overview with the product, progress, key figures, the next sensible step
  and the report of the last run.
* First start without a product opens a short welcome with a three-field form instead of
  an empty profile page.
* Live progress for every background job in the header; buttons lock while one runs.
* Posting mode is a focused overlay; the campaign is grouped by day and each post opens
  in place.
* Communities: verdict filter chips with counts, score rings, a sticky detail panel; the
  draft is generated when you pick a community, not on every refresh.
* "Generate all recommended" for assets; every asset folds open on its own.
* Toasts and proper dialogs replace `alert()`, `confirm()` and `prompt()`. Publishing to
  owned channels now asks first - it is real and public.
* Saving no longer jumps to the top of the page; unsaved profile and settings edits
  survive a background refresh and are guarded on leaving.
* Works at phone width; the sidebar becomes a drawer.

**Security**

* The local server refuses foreign Host headers (DNS rebinding) and write requests from
  other origins or without a JSON body.
* Keys never reach the browser. The interface sees only whether one is set; an empty field
  keeps it, removing one is an explicit action. Discord webhook URLs are shown masked and
  managed through their own routes.
* Content security policy, no referrer, no framing, request size limit.

**Fixes**

* Mastodon and Discord posts lost their link when they were too long - the cut is now made
  in the body and the link is put back.
* German post templates used ASCII stand-ins for umlauts ("hoere", "Loesungen").
* Scan progress, Reddit errors, history results and several notices were German literals
  in the English interface; all of them are catalogue entries now.
* A refused request was answered before its body was read, which Windows turns into a
  connection reset.

**Under the hood**

* One Anthropic request helper instead of five copies: default model `claude-opus-5-5`,
  room for the model's thinking, a timeout in minutes, server-side refusal fallback, and
  refusals or cut-off answers reported as such.
* Data lives in `%LOCALAPPDATA%\Mutexx Production\Mutexx Advertiser` (or the platform
  equivalent) for new installs; existing copies keep their `config.json`. Portable mode
  and `MUTEXX_ADVERTISER_HOME` are supported.
* `Start.bat` finds Python through the `py` launcher too and checks the version.
* 220 tests (25 new for the server boundary, secrets, posting and the API helper).

## 0.3.0

From outreach helper to marketing tool: product profiles, product analysis, strategy
engine with 16 channels, nine assets within channel limits, English and German, Lemmy,
Discourse, Hacker News and Lobsters, the one-click run. See `docs/ROADMAP.md`.

## 0.1.0

First public release: community discovery, rule analysis with a traffic light, drafts,
campaign preparation, owned-channel publishing.
