# Changelog

## 0.7.0

* **OpenAI and Google Gemini** next to Anthropic Claude. Settings has one tab per
  provider - key, model, "Test", and a link to where the key comes from. Gemini keys from
  Google AI Studio come with a free allowance. The five modules that write never know who
  answered: one request contract, and refusals, cut-off answers and HTTP errors are reported
  the same way for all three.
* **The chat route goes to Claude, the Claude app, ChatGPT or Gemini** - with your own
  subscription. Claude (web and desktop app, via `claude://`) and ChatGPT open with the
  request already in the input field; Gemini has no such link, so there it is pasted. None
  of the three lets other apps use a subscription on someone's behalf, so the user sends it
  and pastes the answer back - checked like an API answer.
* Copy is labelled by where it came from: Claude API, OpenAI API, Gemini API, or one of
  the three chats.
* Privacy notice covers OpenAI, Google and the chat route.

## 0.6.1

* **Updates inside the app.** The native Windows dialog is gone. A new version shows up
  as a card in the app's own style, with the changes, a download progress bar and the
  installation step; a "Later" keeps it one click away in the sidebar footer. Settings
  has "Check for updates". The page and the shell talk without giving the page access
  to Tauri: the shell reports by script, the page asks through a navigation to
  `/__desktop/...` that the shell intercepts.
* **Start menu entry.** Tauri's installer creates it on a first install only and skips it
  on every update, so a missing entry never came back. The installer now makes sure it
  exists under "Mutexx Production" on every install and update, and removes it on
  uninstall.
* **Sidebar** fits at common window heights without scrolling; its scrollbar only shows
  on hover. The data folder path breaks at folder boundaries instead of mid-name.

## 0.6.0

* **Write with your Claude subscription.** "with claude.ai" buttons on the analysis, the
  strategy summary, the seed suggestions, every asset and every post draft. Anthropic does
  not let other apps use a claude.ai subscription on someone's behalf, so the route is
  manual by design: the app prepares the request, you paste it into claude.ai and paste the
  answer back. The answer goes through exactly the checks an API answer does - the
  character limits included - because it is the same code path: the request is built by
  the module that would send it, and only the sending is replaced.
* The privacy notice covers the claude.ai route.

## 0.5.1

* **Imprint and privacy notice** inside the app (Help & settings), German and English.
  The privacy notice covers what the app does: local storage, the update check with
  GitHub, the sites a scan reads, the services you set up yourself, and the optional
  Mutexx account. Linked from the account sign-in.
* The release workflow no longer rebuilds a release that already carries an installer.

## 0.5.0

**Windows app**

* Installer (NSIS) to `C:\Program Files\Mutexx Production\Mutexx Advertiser`, start menu
  group "Mutexx Production", data in `%LOCALAPPDATA%\Mutexx Production\Mutexx Advertiser`
  - including the WebView's own data, which would otherwise scatter into a folder named
  after the app identifier.
* Brings Python's official embeddable distribution (pinned SHA-256, PSF-signed); nothing
  else to install.
* Native window; every link that leaves the app - submit forms, subreddits, forums - opens
  in the user's own browser, where they are signed in.
* The Python server dies with the window, also after a crash or a kill (job object).
* One instance only; starting it again brings the open window forward.
* **Updates:** checked at every start against
  `releases/latest/download/latest.json`, verified with the Mutexx signing key (shared with
  Mutexx Notes and VocalRemover), installed only after asking. Windows asks for
  administrator rights, as the app lives under Program Files.

**Mutexx account**

* Optional sign-in with the Mutexx account (Settings, and a chip in the sidebar).
* Sync of product profiles and each product's working data - seed lists, analysis,
  strategy, assets, communities, campaign, history - in the `advertiser` compartment,
  every few minutes and on demand. Keys, secrets and webhooks are never synced.
* Same rules as the TypeScript SDK the other Mutexx apps use: server revisions, tombstones
  for deletions, payloads above 64 KB in the storage bucket. A conflict keeps the other
  device's version and saves ours under `data/account/conflicts/`; the history is merged.
* The session is encrypted with DPAPI; the interface never sees a token.

**Other**

* Tests run in GitHub Actions on Windows and Linux, Python 3.10 and 3.12; 230 tests.
* Releases are built from a tag by `.github/workflows/release.yml` into a draft release.

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
