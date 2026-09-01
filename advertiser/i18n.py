"""
Translation catalogue.

English is the default. German is the second language. The switch lives in Settings
and takes effect immediately, everywhere.

HOW THIS WORKS, AND WHY IT WORKS THAT WAY

The backend never stores translated prose. A saved strategy plan holds the key
"channel.communities.what", not the sentence. The whole catalogue is handed to the
browser once, and the interface resolves keys locally. That is what makes the switch
instant and, more importantly, what makes it correct for things generated earlier:
a plan written last week flips language along with everything else, because the
language was never baked into it.

WHAT IS *NOT* TRANSLATED BY THIS SWITCH

Generated marketing content - post drafts and ad copy - follows the PRODUCT, not the
interface. A German product advertised in a German forum keeps its German post when
you read the interface in English. Those texts are written for an audience, not for
the operator, and silently rewriting them would be wrong.
"""

from __future__ import annotations

import re
from typing import Any

LANGUAGES = {"en": "English", "de": "Deutsch"}
DEFAULT_LANGUAGE = "en"

_PARAM = re.compile(r"\{(\w+)\}")


def normalise(language: str | None) -> str:
    return language if language in LANGUAGES else DEFAULT_LANGUAGE


def t(key: str, language: str = DEFAULT_LANGUAGE, **params: Any) -> str:
    """One string. Falls back to English, then to the key itself - a missing
    translation should look conspicuous, not blank."""
    language = normalise(language)
    text = CATALOG.get(language, {}).get(key)
    if text is None:
        text = CATALOG[DEFAULT_LANGUAGE].get(key, key)
    if params:
        for name, value in params.items():
            text = text.replace("{" + name + "}", str(value))
    return text


def message(key: str, **params: Any) -> dict:
    """A translatable message with its parameters, ready to be stored.

    Runtime warnings carry numbers and names; storing the finished sentence would
    freeze the language. Storing key plus parameters keeps it switchable.
    """
    return {"key": key, "params": params}


def render(entry: Any, language: str = DEFAULT_LANGUAGE) -> str:
    """Turns a stored message back into a sentence. Plain strings pass through, so
    data written before this module existed still shows up.

    Parameters may themselves be messages. A sentence like "the community is
    {community_language}-speaking" needs that language name in the READING language,
    not as its own endonym - otherwise the German version says "Englishsprachig".
    """
    if isinstance(entry, dict) and "key" in entry:
        params = {}
        for name, value in (entry.get("params") or {}).items():
            if isinstance(value, dict):
                params[name] = render(value, language)
            elif isinstance(value, list):
                # A list of fragments - "Google ads (160 EUR), Reddit ads (160 EUR)".
                # The separator belongs to the language, not to the caller.
                params[name] = t("list.separator", language).join(
                    render(item, language) for item in value)
            else:
                params[name] = value
        return t(entry["key"], language, **params)
    return str(entry)


def render_all(entries: Any, language: str = DEFAULT_LANGUAGE) -> list[str]:
    return [render(entry, language) for entry in (entries or [])]


def catalogue() -> dict:
    """The whole dictionary, for the interface to resolve keys without a round trip."""
    return CATALOG


def missing() -> dict[str, list[str]]:
    """Keys present in English but absent in another language. Used by the tests -
    a half-translated interface is worse than a monolingual one."""
    reference = set(CATALOG[DEFAULT_LANGUAGE])
    return {language: sorted(reference - set(strings))
            for language, strings in CATALOG.items() if language != DEFAULT_LANGUAGE}


def unused_parameters() -> list[str]:
    """Keys whose translations do not agree on placeholders. A German sentence that
    drops {count} silently loses the number."""
    problems: list[str] = []
    for key, english in CATALOG[DEFAULT_LANGUAGE].items():
        expected = set(_PARAM.findall(english))
        for language, strings in CATALOG.items():
            if language == DEFAULT_LANGUAGE or key not in strings:
                continue
            if set(_PARAM.findall(strings[key])) != expected:
                problems.append(f"{language}:{key}")
    return problems


# ===========================================================================
# ENGLISH
# ===========================================================================

EN: dict[str, str] = {
    # -- Shell ---------------------------------------------------------------
    "app.name": "Mutexx Advertiser",
    "app.tagline": "Product analysis, marketing strategy and campaign control",
    "app.by": "A Mutexx Production tool",

    # Language names as read IN that language's own interface. The endonyms in
    # LANGUAGES name the option in the picker; these name a language inside a sentence.
    "language.en": "English",
    "language.de": "German",

    "list.separator": ", ",
    "list.join": "{items}",
    "list.item_with_amount": "{name} ({amount} EUR)",
    "list.step": "{name}: {step}",

    "tab.product": "Product",
    "tab.analysis": "Analysis",
    "tab.strategy": "Strategy",
    "tab.assets": "Assets",
    "tab.communities": "Communities",
    "tab.seeds": "Seed lists",
    "tab.campaign": "Campaign",
    "tab.channels": "Auto channels",
    "tab.history": "History",
    "tab.manual": "Manual",
    "tab.settings": "Settings",

    "action.scan": "Start scan",
    "action.save": "Save",
    "action.cancel": "Cancel",
    "action.copy": "Copy",
    "action.copied": "copied",
    "action.remove": "Remove",
    "action.open": "Open",
    "status.ready": "ready",
    "status.running": "working ...",
    "status.saved": "saved",
    "status.none": "nothing yet",
    "common.no_selection": "Nothing selected.",
    "common.no_product": "No product set up yet.",
    "common.optional": "optional",
    "common.of": "of",
    "common.characters": "characters",
    "common.per_month": "per month",
    "common.eur_month": "EUR per month",

    # -- Product -------------------------------------------------------------
    "product.title": "Product profile",
    "product.intro": "Everything this tool does comes out of these fields. The one-liner and "
                     "the description end up verbatim in your posts, so write them for a "
                     "stranger, not for yourself.",
    "product.name": "Name",
    "product.url": "URL",
    "product.version": "Version",
    "product.one_liner": "One-liner",
    "product.one_liner_hint": "What it does, in one sentence. No superlatives.",
    "product.description": "Description",
    "product.description_hint": "What it does, who for, and what it deliberately does not do.",
    "product.category": "Category",
    "product.price_model": "Pricing",
    "product.price_point": "Price",
    "product.audience": "Audience",
    "product.audience_hint": "Who exactly. \"Everyone\" is not an audience.",
    "product.regions": "Regions",
    "product.languages": "Languages",
    "product.budget": "Monthly budget",
    "product.tone": "Tone",
    "product.keywords": "Keywords",
    "product.keywords_hint": "Comma separated. What would your audience type into a search "
                             "box? Not your product name.",
    "product.repo": "Repository",
    "product.download": "Download",
    "product.save": "Save profile",
    "product.new": "Add a product",
    "product.new_prompt": "Name of the new product?",
    "product.delete": "Delete this product",
    "product.delete_confirm": "Delete \"{name}\" along with its communities, queue and "
                              "history? This cannot be undone.",
    "product.needs_name": "It needs a name.",
    "product.created": "Created. Now fill in the fields and save.",
    "product.switcher": "Active product",
    "product.none": "-- no product yet --",

    # -- Categories ----------------------------------------------------------
    "category.software_desktop": "Desktop software (Windows, macOS, Linux)",
    "category.software_web": "Web application / SaaS",
    "category.app_mobile": "Mobile app",
    "category.game": "Game",
    "category.dev_tool": "Developer tool, library or API",
    "category.content_site": "Content site, reference work or blog",
    "category.shop_physical": "Online shop with physical goods",
    "category.service": "Service, consulting or agency",
    "category.creative": "Creative work (book, music, film, course)",
    "category.other": "Something else",

    # Short forms. The parenthetical above helps you pick from a dropdown; printed in
    # a press kit it turns into a platform promise nobody made.
    "category.short.software_desktop": "Desktop software",
    "category.short.software_web": "Web application",
    "category.short.app_mobile": "Mobile app",
    "category.short.game": "Game",
    "category.short.dev_tool": "Developer tool",
    "category.short.content_site": "Content site",
    "category.short.shop_physical": "Online shop",
    "category.short.service": "Service",
    "category.short.creative": "Creative work",
    "category.short.other": "Product",

    # -- Pricing -------------------------------------------------------------
    "price.free": "Free",
    "price.freemium": "Free with a paid tier",
    "price.one_time": "One-time purchase",
    "price.subscription": "Subscription",
    "price.ad_supported": "Ad-supported",
    "price.shop": "Retail",
    "price.quote": "Price on request",

    # -- Tone ----------------------------------------------------------------
    "tone.sachlich": "Plain and factual",
    "tone.fachlich": "Technical, for people who know the field",
    "tone.locker": "Relaxed and direct",
    "tone.werblich": "Promotional, but without superlatives",

    # -- Traffic light -------------------------------------------------------
    "verdict.gruen": "No promotion ban found",
    "verdict.gelb": "Allowed, with conditions",
    "verdict.rot": "Self-promotion forbidden - do not post",
    "verdict.grau": "Rules unavailable - check yourself",
    "verdict.short.gruen": "green",
    "verdict.short.gelb": "amber",
    "verdict.short.rot": "red",
    "verdict.short.grau": "grey",

    "rule.promo_forbidden": "Self-promotion forbidden",
    "rule.no_own_links": "No links to your own projects",
    "rule.spam_ban": "General spam ban",
    "rule.ratio": "Ratio rule (contribute before you share)",
    "rule.megathread": "Collection or weekly thread only",
    "rule.mod_approval": "Prior moderator approval required",
    "rule.flair": "Flair required",
    "rule.text_only": "Text posts only",
    "rule.karma": "Minimum karma or account age",
    "rule.no_monetisation": "No surveys or monetisation",
    "rule.mods_only": "Only moderators may post here",
    "rule.showcase_category": "One category invites you to share your own work",
    "rule.explicitly_allowed": "Self-promotion explicitly allowed",

    "requirement.ratio": "Write at least 5-10 genuine comments in this community first.",
    "requirement.megathread": "Post ONLY in the collection or weekly thread - no separate thread.",
    "requirement.mod_approval": "Message the moderators first and wait for approval.",
    "requirement.flair": "Set the right flair when posting, or the post gets removed.",
    "requirement.text_only": "Post as a text submission, link inside the body.",
    "requirement.karma": "Check the karma or account-age requirement; let the account age if needed.",
    "requirement.no_monetisation": "Do not mention monetisation, Patreon or similar.",
    "requirement.spam_ban": "The post has to be worth reading without the link, or it gets removed.",
    "requirement.nsfw": "NSFW community: mark the post accordingly.",
    "requirement.read_rules": "Read the sidebar rules yourself before posting.",

    # -- Analysis ------------------------------------------------------------
    "analysis.title": "Analysis",
    "analysis.run": "Run analysis",
    "analysis.use_api": "also analyse with AI",
    "analysis.intro": "Without a key the product page is fetched and evaluated statistically. "
                      "With a key you also get audiences, value propositions, positioning and "
                      "objections.",
    "analysis.empty": "No analysis yet. It reads the product page, derives keywords and guesses "
                      "category and pricing from what the page actually says.",
    "analysis.page": "Product page",
    "analysis.fetched": "Fetched",
    "analysis.yes_http": "yes, HTTP {status}",
    "analysis.title_tag": "Title",
    "analysis.meta": "Meta description",
    "analysis.extent": "Extent",
    "analysis.words": "{count} words",
    "analysis.category_guess": "Category according to the page: {value}",
    "analysis.price_guess": "Pricing according to the page: {value}",
    "analysis.confidence": "Confidence {percent}% - the profile says {profile}",
    "analysis.no_evidence": "No evidence on the page.",
    "analysis.positioning": "Positioning",
    "analysis.positioning_empty": "AI analysis only. Without a key this stays empty.",
    "analysis.tone_hint": "Tone: {value}",
    "analysis.value_props": "Value propositions",
    "analysis.segments": "Audience segments",
    "analysis.segment_where": "Where: {value}",
    "analysis.objections": "Objections to expect",
    "analysis.keywords": "Keywords",
    "analysis.keywords_statistical": "Derived statistically from the page:",
    "analysis.no_url": "No product URL in the profile.",
    "analysis.no_signals": "No usable signals found on the page.",
    "analysis.warn.unreachable": "{error} The analysis falls back to the profile alone.",
    "analysis.warn.http": "The page answered with HTTP {status}.",
    "analysis.warn.api_failed": "AI analysis failed ({error}). The statistical part stands.",
    "analysis.done": "Analysis and strategy are ready.",
    "analysis.aborted": "Analysis aborted.",
    "analysis.step.fetch": "Fetching the product page",
    "analysis.step.keywords": "Evaluating keywords",
    "analysis.step.api": "Free analysis via the Anthropic API",
    "analysis.step.done": "Analysis finished",

    # -- Strategy ------------------------------------------------------------
    "strategy.title": "Strategy",
    "strategy.build": "Build strategy",
    "strategy.use_api": "AI summary",
    "strategy.empty": "No strategy yet. It picks from the channel catalogue whatever fits this "
                      "product's category, pricing and budget - and says why each rejected "
                      "channel falls away.",
    "strategy.no_money": "This tool does not spend money.",
    "strategy.no_money_body": "Paid campaigns are prepared in full and then handed over. A human "
                              "activates them in their own ad account - for the same reason the "
                              "last click before posting is yours.",
    "strategy.summary": "The picture",
    "strategy.first_week": "First week",
    "strategy.watch_out": "What to watch out for",
    "strategy.budget": "Budget: {amount} EUR per month",
    "strategy.channels_detail": "Channels one by one",
    "strategy.rejected": "Rejected - and why",
    "strategy.rejected_intro": "A recommendation without a counter-check is an opinion, not advice.",
    "strategy.first_step": "First step",
    "strategy.risk": "Risk",
    "strategy.effect": "Takes effect: {value}",
    "strategy.reserve": "Reserve",
    "strategy.reserve_note": "Stays untouched until four weeks in, when it is clear which channel "
                             "carries. Then it all goes there.",
    "strategy.col_channel": "Channel",
    "strategy.col_month": "Month",
    "strategy.col_share": "Share",

    "kind.eigen": "Owned",
    "kind.organisch": "Organic",
    "kind.bezahlt": "Paid",
    "kind.badge.eigen": "Owned channel",
    "kind.badge.organisch": "Organic",
    "kind.badge.bezahlt": "Paid",

    "effort.niedrig": "little effort",
    "effort.mittel": "moderate effort",
    "effort.hoch": "a lot of effort",
    "lead.sofort": "immediately",
    "lead.Tage": "days",
    "lead.Wochen": "weeks",
    "lead.Monate": "months",

    "automation.voll": "The app publishes this itself",
    "automation.vorbereitet": "The app prepares everything, a human sends it",
    "automation.anleitung": "The app supplies copy and instructions, you do the rest",

    "phase.now": "Right now",
    "phase.now_note": "What you can do today without waiting for anyone.",
    "phase.weeks": "First weeks",
    "phase.weeks_note": "The core of the campaign. This is where it is decided whether the "
                        "product gets traction.",
    "phase.long": "The long game",
    "phase.long_note": "Pays off after months, then keeps paying without running costs. Start "
                       "now, not when it is urgent.",

    # Strategy reasoning
    "reason.category_strong": "A very good fit for {category}.",
    "reason.category_weak": "Weak for {category} - only worth it once the stronger channels run.",
    "reason.price_strong": "Works with {price} pricing.",
    "reason.price_weak": "With {price} pricing, paid placement rarely pays for itself - there is "
                         "nothing to fund the click.",
    "reason.free_paid": "Free product: nobody pays back a paid click. Worth it as a short push at "
                        "launch, not as a running channel.",
    "reason.owned": "Your own channel - no foreign rules, usable today.",

    "blocked.hard_category": "Requires {required}. This product is set up as {actual}.",
    "blocked.needs_field": "Needs an entry under '{field}' in the product profile. Without it the "
                           "channel cannot be worked.",
    "blocked.no_budget": "No monthly budget set. Paid channels appear once the profile has one.",
    "blocked.under_minimum": "Needs at least {minimum} EUR a month to rise above the noise - the "
                             "profile says {budget} EUR. Below that threshold the algorithm "
                             "learns nothing and the money is gone.",

    "strategy.warn.no_budget": "Without a budget only organic channels remain. That is not a "
                               "shortcoming - most products get further that way than with a "
                               "budget that is too small.",
    "strategy.warn.no_paid_fit": "The profile has {budget} EUR, but no paid channel fits this "
                                 "product. The reasons are under the rejected channels. That "
                                 "money is better spent on content.",
    "strategy.warn.one_channel": "{budget} EUR is enough for exactly one paid channel. Split "
                                 "across two, neither gathers enough data to show whether it works.",
    "strategy.warn.no_analysis": "No product analysis has run yet. The channel selection rests on "
                                 "the profile's self-assessment alone.",
    "strategy.warn.api_failed": "AI summary failed ({error}). The rule-based plan stands.",
    "strategy.summary.none": "No channel fits this profile. That almost always means the category "
                             "or the pricing is set wrong.",
    "strategy.summary.line": "{name} is set up as {category}. The three most viable channels are "
                             "{top}. {money}",
    "strategy.summary.organic": "Without a budget everything runs organically.",
    "strategy.summary.funded": "Of {budget} EUR a month, {named} go to work, a fifth stays in reserve.",
    "strategy.summary.unfunded": "The {budget} EUR on file find no suitable paid channel.",

    # -- Assets --------------------------------------------------------------
    "assets.title": "Assets",
    "assets.use_api": "write with AI",
    "assets.intro": "The finished copy for the channels the strategy picked - each within that "
                    "channel's character limits. <b>The limits are hard:</b> Google rejects a "
                    "headline of 31 characters, not \"roughly\". Every field is checked after "
                    "generation; anything that had to be cut is marked.",
    "assets.intro2": "Without a key the templates assemble only what is in the profile and the "
                     "analysis - nothing is invented. That makes the copy plain, but true. With "
                     "a key it is written freely and then checked just the same.",
    "assets.build": "Generate copy",
    "assets.rebuild": "Generate again",
    "assets.generated": "generated via {source}, {date}",
    "assets.channel_recommended": "Channel recommended",
    "assets.channel_not_planned": "Channel not in the plan",
    "assets.nothing": "nothing generated - the profile lacks the fields for it",
    "assets.limit_hint": "at most {limit} characters.",
    "assets.truncated": "cut",
    "assets.too_long": "too long",
    "assets.negative_keywords": "Negative keywords",
    "assets.negative_intro": "Without these, any search campaign burns money on queries that have "
                             "nothing to do with the product. A starting point, not a substitute "
                             "for the search-terms report after two weeks.",
    "assets.utm": "Destination with campaign tagging",
    "assets.from_price": "From {price}",
    "assets.source.vorlage": "template",
    "assets.source.anthropic": "AI",

    "assets.warn.empty": "{field}: nothing generated. The profile lacks the fields this would be "
                         "assembled from.",
    "assets.warn.too_long": "{field}: {count} entries over the {limit} character limit. Shorten "
                            "before you paste them in.",
    "assets.warn.truncated": "{field}: {count} of {total} entries had to be cut - please read "
                             "them over, a sentence chopped mid-thought looks sloppy.",
    "assets.warn.few": "{field}: only {count} of {wanted} variants. More value propositions in "
                       "the profile or the analysis yield more variants.",
    "assets.warn.api_failed": "AI copy failed ({error}). The templates stand.",

    # -- Communities ---------------------------------------------------------
    "communities.search": "Search ...",
    "communities.shown": "{shown} of {total} shown",
    "communities.empty": "No data yet. Use <b>Start scan</b> at the top right, add communities by "
                         "hand - or read the <a href=\"#\" id=\"emptyHelp\">manual</a> first.",
    "communities.add": "Add a community by hand",
    "communities.platform": "Platform",
    "communities.handle": "Name",
    "communities.members": "Members",
    "communities.rules_text": "Paste the rules here",
    "communities.added": "Added - verdict:",
    "communities.need_handle": "Give a name or a URL.",
    "communities.checking": "checking ...",
    "communities.evidence": "The rule texts this rests on",
    "communities.showcase": "The category where sharing is invited",
    "communities.showcase_only": "post there and nowhere else on this forum",
    "communities.no_evidence": "No relevant rule texts found.",
    "communities.do_not_post": "<b>Do not post.</b> This community forbids self-promotion. A post "
                               "here costs you the account and possibly the domain.",
    "communities.draft": "Post draft",
    "communities.generate": "Generate draft",
    "communities.variant": "Variant",
    "communities.angle": "Angle: {angle}",
    "communities.via": "generated via {source}",
    "communities.checklist": "Do this before posting",
    "communities.to_queue": "Add to campaign",
    "communities.open_form": "Open the form",
    "communities.mark_posted": "Mark as posted",
    "communities.queued": "Added to the campaign.",
    "communities.logged": "Recorded in the history.",
    "communities.form_opened": "Form opened. You send it yourself.",
    "communities.guard": "<b>Safety catch:</b>",
    "communities.force": "Open anyway",

    "angle.resource": "Share a resource",
    "angle.feedback": "Ask for corrections",
    "angle.showcase": "Show the project",
    "angle.question": "A question with context",
    "angle.forum_intro": "Forum introduction",

    # -- Seeds ---------------------------------------------------------------
    "seeds.title": "Starting points for the scan",
    "seeds.intro": "These are candidates, not facts. Every entry is checked against the real "
                   "source during the scan - whatever no longer exists drops out. That is exactly "
                   "why suggestions from a language model are usable here: the scanner pushes back.",
    "seeds.subreddits": "Subreddits",
    "seeds.subreddits_hint": "one per line, without r/",
    "seeds.forums": "Forums and communities",
    "seeds.forums_hint": "one per line: URL | name | note",
    "seeds.lemmy": "Lemmy instances",
    "seeds.lemmy_hint": "one per line, e.g. lemmy.world - leave empty for the default set",
    "seeds.lemmy_note": "Instances, not communities. Lemmy federates: a search on a few large "
                        "instances reaches most of the network, and the communities are found "
                        "through them.",
    "seeds.save": "Save seed lists",
    "seeds.suggest": "Suggest some (AI)",
    "seeds.needs_key": "That needs an Anthropic key in Settings.",
    "seeds.keywords": "The keywords the scan works with",
    "seeds.keywords_note": "They come from the product profile and the analysis. If they are "
                           "empty the scan finds nothing - run the analysis first.",
    "seeds.keywords_empty": "No keywords yet. Fill in the profile or run the analysis.",
    "seeds.suggesting": "asking for suggestions ...",
    "seeds.suggested": "{subs} subreddits and {forums} forums stored as candidates. The scan will "
                       "check them.",
    "seeds.suggest_aborted": "Suggestion aborted.",

    # -- Scan ----------------------------------------------------------------
    "scan.starting": "Starting ...",
    "scan.done": "Done - {count} communities rated.",
    "scan.aborted": "Scan aborted.",
    "scan.busy": "Something is already running.",
    "scan.no_keywords": "No keywords available. Add some to the product profile or run the "
                        "analysis first - a scan without keywords is a walk through nothing.",
    "platform.lemmy": "Lemmy",
    "scan.lemmy_none": "Lemmy searched, nothing above the size floor found. That is a result "
                       "too - the network is small, and not every subject has a community there yet.",
    "scan.no_forum_seeds": "No forum seed list for this product. Add some under Seed lists or ask "
                           "for suggestions.",
    "scan.nothing_yet": "Nothing has run yet.",

    # -- Campaign ------------------------------------------------------------
    "campaign.prepare": "Prepare campaign",
    "campaign.limit": "At most",
    "campaign.green_only": "green communities only",
    "campaign.writing": "Writing drafts ...",
    "campaign.ready": "{count} posts prepared.",
    "campaign.queue_empty": "The queue is empty - use \"Prepare campaign\" above.",
    "campaign.start_mode": "Start posting mode",
    "campaign.exit": "Leave posting mode",
    "campaign.step": "Step {current} of {total}: {community}",
    "campaign.scheduled": "scheduled: {date}",
    "campaign.too_early": "This post is scheduled for a later date. Several in one day is exactly "
                          "the pattern that reads as spam.",
    "campaign.copy_open": "Copy the text and open the form",
    "campaign.posted_next": "Posted - next",
    "campaign.skip": "Skip",
    "campaign.clipboard": "The text is on your clipboard. Read it over in the form and send it.",
    "campaign.note": "Note: {reasons}",
    "campaign.finished": "Queue finished.",

    # -- Auto channels -------------------------------------------------------
    "channels.title": "Channels the app may publish to on its own",
    "channels.intro": "Only channels you own. A Discord webhook works only where someone with "
                      "server rights created it, and the Mastodon token is yours.",
    "channels.webhook_name": "Name",
    "channels.webhook_url": "Webhook URL",
    "channels.add_hook": "Add webhook",
    "channels.no_hook": "No webhook set up yet.",
    "channels.mastodon": "Mastodon",
    "channels.instance": "Instance",
    "channels.token": "Access token",
    "channels.test_post": "Send a test post to all owned channels",
    "channels.no_auto": "No owned channels configured.",
    "channels.sent": "sent",
    "channels.error": "Error {status} {detail}",
    "channels.discord_search": "Where to find Discord servers",

    # -- History -------------------------------------------------------------
    "history.empty": "Nothing posted yet.",
    "history.date": "Date",
    "history.community": "Community",
    "history.channel": "Channel",
    "history.post_title": "Title",
    "history.result": "Result",

    # -- Settings ------------------------------------------------------------
    "settings.title": "Settings",
    "settings.language": "Language",
    "settings.language_hint": "Applies immediately, everywhere. Post drafts and ad copy are not "
                              "affected - those follow the languages set on the product, because "
                              "they are written for an audience, not for you.",
    "settings.reddit": "Reddit API (required for the Reddit part)",
    "settings.reddit_hint": "Reddit answers programmatic requests without a registered app with "
                            "403. On reddit.com/prefs/apps, at the very bottom, \"create another "
                            "app\" - type <b>script</b>, name <b>MutexxAdvertiser</b>, redirect "
                            "uri <b>http://localhost:8777</b>. The client ID is printed small "
                            "<i>underneath</i> the app name. Free, read-only.",
    "settings.client_id": "Client ID",
    "settings.client_secret": "Client secret",
    "settings.lemmy": "Lemmy",
    "settings.lemmy_note": "No key, no approval, no account - Lemmy reads openly. The test only says whether an instance answers and which API version it speaks.",
    "settings.lemmy_instance": "Instance to test",
    "settings.lemmy_ok": "{title} answers ({api}, {users} accounts).",
    "settings.lemmy_fail": "{instance} does not answer.",
    "settings.bot_hint": "<b>Bot account</b> - only fill this in if the connection test above "
                         "fails with 401. Reddit now usually wants a <i>separate</i> account for "
                         "script apps, registered as the developer under prefs/apps. It stays "
                         "local in <code>config.json</code> on this machine.",
    "settings.bot_user": "Bot username",
    "settings.bot_pass": "Bot password",
    "settings.test_connection": "Test connection",
    "settings.scan_limits": "Scan limits",
    "settings.scan_limits_hint": "The keywords live on the product, not here - see the "
                                 "<b>Product</b> and <b>Seed lists</b> tabs.",
    "settings.max_communities": "Max. communities",
    "settings.deep_scan": "Deep scan top N",
    "settings.min_members": "Minimum members",
    "settings.delay": "Pause between requests (s)",
    "settings.safety": "Safety catch",
    "settings.max_per_day": "Max. Reddit posts per day",
    "settings.min_days": "Minimum days between posts to the same community",
    "settings.anthropic": "Anthropic API (optional)",
    "settings.anthropic_hint": "Without a key the app works from templates. With a key, analysis, "
                               "strategy summaries, drafts and ad copy are written freely.",
    "settings.api_key": "API key",
    "settings.model": "Model",
    "settings.save": "Save settings",

    # -- Guard ---------------------------------------------------------------
    "guard.daily_limit": "Daily limit reached: {count} Reddit posts already went out today "
                         "(limit {limit}). Several subreddits on one day is exactly the pattern "
                         "that reads as spam.",
    "guard.too_soon": "You posted here {days} days ago - the minimum gap is {minimum} days.",
    "guard.forbidden": "This community explicitly forbids self-promotion.",

    # -- Drafts --------------------------------------------------------------
    "draft.language_warning": "The target community is clearly {community_language}-speaking, "
                              "while the product copy in the profile is {product_language}. "
                              "Templates cannot translate - use the AI draft for a post in the "
                              "community's language, or keep the one-liner and description in "
                              "both languages in the profile.",
    "draft.forbidden_banner": "### This community forbids self-promotion. This draft was produced "
                              "for reference only - do NOT post it here.",
    "draft.api_failed": "AI draft failed ({error}); the template was used instead.",

    # -- Errors --------------------------------------------------------------
    "error.unknown_path": "Unknown path",
    "error.not_found": "Community not found.",
    "error.no_product": "No product set up.",
    "error.product_not_found": "Product not found.",
    "error.unknown_asset": "Unknown asset.",
    "error.subreddit_missing": "Subreddit name missing.",
    "error.url_missing": "URL missing.",
    "error.lemmy_handle": "A Lemmy community needs the form community@instance, e.g. selfhosted@lemmy.world - the same name exists on dozens of instances.",
    "error.no_api_key": "No Anthropic API key on file.",
    "error.api_status": "The Anthropic API answered with {status}: {detail}",
    "error.no_json": "The API response contained no usable JSON.",
}


# ===========================================================================
# GERMAN
# ===========================================================================

DE: dict[str, str] = {
    # -- Rahmen --------------------------------------------------------------
    "app.name": "Mutexx Advertiser",
    "app.tagline": "Produktanalyse, Marketingstrategie und Kampagnensteuerung",
    "app.by": "Ein Werkzeug von Mutexx Production",

    "language.en": "englisch",
    "language.de": "deutsch",

    "list.separator": ", ",
    "list.join": "{items}",
    "list.item_with_amount": "{name} ({amount} EUR)",
    "list.step": "{name}: {step}",

    "tab.product": "Produkt",
    "tab.analysis": "Analyse",
    "tab.strategy": "Strategie",
    "tab.assets": "Werbemittel",
    "tab.communities": "Communities",
    "tab.seeds": "Startlisten",
    "tab.campaign": "Kampagne",
    "tab.channels": "Auto-Kanäle",
    "tab.history": "Verlauf",
    "tab.manual": "Anleitung",
    "tab.settings": "Einstellungen",

    "action.scan": "Scan starten",
    "action.save": "Speichern",
    "action.cancel": "Abbrechen",
    "action.copy": "Kopieren",
    "action.copied": "kopiert",
    "action.remove": "Entfernen",
    "action.open": "Öffnen",
    "status.ready": "bereit",
    "status.running": "läuft ...",
    "status.saved": "gespeichert",
    "status.none": "noch nichts",
    "common.no_selection": "Keine Auswahl.",
    "common.no_product": "Noch kein Produkt angelegt.",
    "common.optional": "optional",
    "common.of": "von",
    "common.characters": "Zeichen",
    "common.per_month": "im Monat",
    "common.eur_month": "EUR im Monat",

    # -- Produkt -------------------------------------------------------------
    "product.title": "Produktprofil",
    "product.intro": "Alles, was dieses Werkzeug tut, stammt aus diesen Feldern. Der Einzeiler "
                     "und die Beschreibung landen wörtlich in deinen Beiträgen - schreib sie für "
                     "einen Fremden, nicht für dich.",
    "product.name": "Name",
    "product.url": "URL",
    "product.version": "Version",
    "product.one_liner": "Einzeiler",
    "product.one_liner_hint": "Was es tut, in einem Satz. Ohne Superlative.",
    "product.description": "Beschreibung",
    "product.description_hint": "Was es tut, für wen, und was es bewusst nicht tut.",
    "product.category": "Kategorie",
    "product.price_model": "Preismodell",
    "product.price_point": "Preis",
    "product.audience": "Zielgruppe",
    "product.audience_hint": "Wer genau. „Alle\" ist keine Zielgruppe.",
    "product.regions": "Regionen",
    "product.languages": "Sprachen",
    "product.budget": "Monatsbudget",
    "product.tone": "Tonalität",
    "product.keywords": "Stichwörter",
    "product.keywords_hint": "Komma-getrennt. Was würde deine Zielgruppe in ein Suchfeld tippen? "
                             "Nicht den Produktnamen.",
    "product.repo": "Repository",
    "product.download": "Download",
    "product.save": "Profil speichern",
    "product.new": "Produkt anlegen",
    "product.new_prompt": "Name des neuen Produkts?",
    "product.delete": "Dieses Produkt löschen",
    "product.delete_confirm": "„{name}\" mitsamt Communities, Warteschlange und Verlauf löschen? "
                              "Das lässt sich nicht rückgängig machen.",
    "product.needs_name": "Ein Name muss sein.",
    "product.created": "Angelegt. Jetzt die Felder ausfüllen und speichern.",
    "product.switcher": "Aktives Produkt",
    "product.none": "-- noch kein Produkt --",

    # -- Kategorien ----------------------------------------------------------
    "category.software_desktop": "Desktop-Software (Windows, macOS, Linux)",
    "category.software_web": "Web-Anwendung / SaaS",
    "category.app_mobile": "Mobile App",
    "category.game": "Spiel",
    "category.dev_tool": "Entwicklerwerkzeug, Bibliothek oder API",
    "category.content_site": "Inhaltsseite, Nachschlagewerk oder Blog",
    "category.shop_physical": "Onlineshop mit physischer Ware",
    "category.service": "Dienstleistung, Beratung oder Agentur",
    "category.creative": "Kreativwerk (Buch, Musik, Film, Kurs)",
    "category.other": "Etwas anderes",

    "category.short.software_desktop": "Desktop-Software",
    "category.short.software_web": "Web-Anwendung",
    "category.short.app_mobile": "Mobile App",
    "category.short.game": "Spiel",
    "category.short.dev_tool": "Entwicklerwerkzeug",
    "category.short.content_site": "Inhaltsseite",
    "category.short.shop_physical": "Onlineshop",
    "category.short.service": "Dienstleistung",
    "category.short.creative": "Kreativwerk",
    "category.short.other": "Produkt",

    # -- Preismodelle --------------------------------------------------------
    "price.free": "Kostenlos",
    "price.freemium": "Kostenlos mit Bezahlversion",
    "price.one_time": "Einmalkauf",
    "price.subscription": "Abonnement",
    "price.ad_supported": "Werbefinanziert",
    "price.shop": "Warenverkauf",
    "price.quote": "Preis auf Anfrage",

    # -- Tonalität -----------------------------------------------------------
    "tone.sachlich": "Sachlich und nüchtern",
    "tone.fachlich": "Fachlich, für Kenner der Materie",
    "tone.locker": "Locker und direkt",
    "tone.werblich": "Werblich, aber ohne Superlative",

    # -- Ampel ---------------------------------------------------------------
    "verdict.gruen": "Kein Werbeverbot gefunden",
    "verdict.gelb": "Erlaubt, aber mit Auflagen",
    "verdict.rot": "Eigenwerbung verboten - nicht posten",
    "verdict.grau": "Regeln nicht abrufbar - selbst prüfen",
    "verdict.short.gruen": "grün",
    "verdict.short.gelb": "gelb",
    "verdict.short.rot": "rot",
    "verdict.short.grau": "grau",

    "rule.promo_forbidden": "Eigenwerbung verboten",
    "rule.no_own_links": "Keine Links zu eigenen Projekten",
    "rule.spam_ban": "Allgemeines Spam-Verbot",
    "rule.ratio": "Ratio-Regel (erst beitragen, dann teilen)",
    "rule.megathread": "Nur im Sammel- oder Wochenthread",
    "rule.mod_approval": "Vorherige Mod-Freigabe nötig",
    "rule.flair": "Flair erforderlich",
    "rule.text_only": "Nur Text-Beiträge erlaubt",
    "rule.karma": "Mindest-Karma oder Kontoalter",
    "rule.no_monetisation": "Keine Umfragen oder Monetarisierung",
    "rule.mods_only": "Hier dürfen nur Moderatoren posten",
    "rule.showcase_category": "Eine Kategorie lädt ausdrücklich dazu ein, Eigenes zu zeigen",
    "rule.explicitly_allowed": "Eigenwerbung ausdrücklich erlaubt",

    "requirement.ratio": "Vorher mindestens 5-10 echte Kommentare in dieser Community schreiben.",
    "requirement.megathread": "NUR im Sammel- oder Wochenthread posten - keinen eigenen Thread.",
    "requirement.mod_approval": "Vorher die Moderation anschreiben und Freigabe abwarten.",
    "requirement.flair": "Beim Posten das passende Flair setzen, sonst wird der Beitrag entfernt.",
    "requirement.text_only": "Als Textbeitrag posten, Link erst im Fließtext.",
    "requirement.karma": "Karma- oder Kontoalter-Anforderung prüfen, ggf. den Account reifen lassen.",
    "requirement.no_monetisation": "Keinen Hinweis auf Monetarisierung, Patreon o. Ä. einbauen.",
    "requirement.spam_ban": "Der Beitrag muss auch ohne den Link lesenswert sein, sonst wird er "
                            "entfernt.",
    "requirement.nsfw": "NSFW-Community: Beitrag entsprechend markieren.",
    "requirement.read_rules": "Regeln in der Sidebar vor dem Posten selbst gegenlesen.",

    # -- Analyse -------------------------------------------------------------
    "analysis.title": "Analyse",
    "analysis.run": "Analyse starten",
    "analysis.use_api": "zusätzlich per KI auswerten",
    "analysis.intro": "Ohne Schlüssel wird die Produktseite geladen und statistisch ausgewertet. "
                      "Mit Schlüssel kommen Zielgruppen, Nutzenversprechen, Positionierung und "
                      "Einwände dazu.",
    "analysis.empty": "Noch keine Analyse gelaufen. Sie liest die Produktseite, leitet Stichwörter "
                      "ab und rät Kategorie und Preismodell aus dem, was dort tatsächlich steht.",
    "analysis.page": "Produktseite",
    "analysis.fetched": "Abgerufen",
    "analysis.yes_http": "ja, HTTP {status}",
    "analysis.title_tag": "Titel",
    "analysis.meta": "Meta-Beschreibung",
    "analysis.extent": "Umfang",
    "analysis.words": "{count} Wörter",
    "analysis.category_guess": "Kategorie laut Seite: {value}",
    "analysis.price_guess": "Preismodell laut Seite: {value}",
    "analysis.confidence": "Sicherheit {percent}% - im Profil steht {profile}",
    "analysis.no_evidence": "Keine Belege auf der Seite.",
    "analysis.positioning": "Positionierung",
    "analysis.positioning_empty": "Nur mit KI-Analyse. Ohne Schlüssel bleibt das leer.",
    "analysis.tone_hint": "Ton: {value}",
    "analysis.value_props": "Nutzenversprechen",
    "analysis.segments": "Zielgruppensegmente",
    "analysis.segment_where": "Wo: {value}",
    "analysis.objections": "Zu erwartende Einwände",
    "analysis.keywords": "Stichwörter",
    "analysis.keywords_statistical": "Statistisch aus der Seite gewonnen:",
    "analysis.no_url": "Keine Produkt-URL im Profil hinterlegt.",
    "analysis.no_signals": "Keine verwertbaren Merkmale auf der Seite gefunden.",
    "analysis.warn.unreachable": "{error} Die Analyse stützt sich nur auf das Profil.",
    "analysis.warn.http": "Die Seite antwortete mit HTTP {status}.",
    "analysis.warn.api_failed": "KI-Analyse fehlgeschlagen ({error}). Die statistische Auswertung "
                                "steht.",
    "analysis.done": "Analyse und Strategie stehen.",
    "analysis.aborted": "Analyse abgebrochen.",
    "analysis.step.fetch": "Produktseite laden",
    "analysis.step.keywords": "Stichwörter auswerten",
    "analysis.step.api": "Freie Analyse über die Anthropic-API",
    "analysis.step.done": "Analyse fertig",

    # -- Strategie -----------------------------------------------------------
    "strategy.title": "Strategie",
    "strategy.build": "Strategie berechnen",
    "strategy.use_api": "Zusammenfassung per KI",
    "strategy.empty": "Noch keine Strategie berechnet. Sie wählt aus dem Kanalkatalog, was zu "
                      "Kategorie, Preismodell und Budget dieses Produkts passt - und sagt bei "
                      "jedem verworfenen Kanal, warum er wegfällt.",
    "strategy.no_money": "Dieses Werkzeug gibt kein Geld aus.",
    "strategy.no_money_body": "Bezahlte Kampagnen werden vollständig vorbereitet und dann "
                              "übergeben. Aktivieren tut ein Mensch im eigenen Werbekonto - aus "
                              "demselben Grund, aus dem der letzte Klick beim Posten bei dir liegt.",
    "strategy.summary": "Lagebild",
    "strategy.first_week": "Erste Woche",
    "strategy.watch_out": "Worauf zu achten ist",
    "strategy.budget": "Budget: {amount} EUR im Monat",
    "strategy.channels_detail": "Kanäle im Einzelnen",
    "strategy.rejected": "Verworfen - und warum",
    "strategy.rejected_intro": "Ein Vorschlag ohne Gegenprobe ist kein Rat, sondern eine Meinung.",
    "strategy.first_step": "Erster Schritt",
    "strategy.risk": "Risiko",
    "strategy.effect": "Wirkt: {value}",
    "strategy.reserve": "Reserve",
    "strategy.reserve_note": "Bleibt liegen, bis nach vier Wochen feststeht, welcher Kanal trägt. "
                             "Dann wandert sie komplett dorthin.",
    "strategy.col_channel": "Kanal",
    "strategy.col_month": "Monat",
    "strategy.col_share": "Anteil",

    "kind.eigen": "Eigen",
    "kind.organisch": "Organisch",
    "kind.bezahlt": "Bezahlt",
    "kind.badge.eigen": "Eigener Kanal",
    "kind.badge.organisch": "Organisch",
    "kind.badge.bezahlt": "Bezahlt",

    "effort.niedrig": "wenig Aufwand",
    "effort.mittel": "mittlerer Aufwand",
    "effort.hoch": "viel Aufwand",
    "lead.sofort": "sofort",
    "lead.Tage": "Tage",
    "lead.Wochen": "Wochen",
    "lead.Monate": "Monate",

    "automation.voll": "Die App veröffentlicht selbst",
    "automation.vorbereitet": "Die App bereitet alles vor, abschicken tut ein Mensch",
    "automation.anleitung": "Die App liefert Texte und Anleitung, ausgeführt wird von Hand",

    "phase.now": "Sofort",
    "phase.now_note": "Was heute geht, ohne auf irgendjemanden zu warten.",
    "phase.weeks": "Erste Wochen",
    "phase.weeks_note": "Der Kern der Kampagne. Hier entscheidet sich, ob das Produkt Zug bekommt.",
    "phase.long": "Langer Atem",
    "phase.long_note": "Trägt erst nach Monaten, dafür dauerhaft und ohne laufende Kosten. Jetzt "
                       "anfangen, nicht wenn es brennt.",

    "reason.category_strong": "Passt ausgesprochen gut zu {category}.",
    "reason.category_weak": "Für {category} eher schwach - nur sinnvoll, wenn die stärkeren Kanäle "
                            "schon laufen.",
    "reason.price_strong": "Trägt bei Preismodell {price}.",
    "reason.price_weak": "Bei {price} rechnet sich bezahlte Ausspielung selten - es gibt nichts, "
                         "was den Klick bezahlt.",
    "reason.free_paid": "Kostenloses Produkt: bezahlte Klicks zahlt niemand zurück. Nur sinnvoll "
                        "als kurzer Schub zum Start, nicht als Dauerbetrieb.",
    "reason.owned": "Eigener Kanal - keine fremden Regeln, sofort bespielbar.",

    "blocked.hard_category": "Setzt {required} voraus. Dieses Produkt ist als {actual} eingeordnet.",
    "blocked.needs_field": "Braucht einen Eintrag unter „{field}\" im Produktprofil. Ohne den ist "
                           "der Kanal nicht bespielbar.",
    "blocked.no_budget": "Kein Monatsbudget hinterlegt. Bezahlte Kanäle erscheinen erst, wenn im "
                         "Profil eines steht.",
    "blocked.under_minimum": "Braucht mindestens {minimum} EUR im Monat, um über das Rauschen zu "
                             "kommen - hinterlegt sind {budget} EUR. Unterhalb dieser Schwelle "
                             "lernt der Algorithmus nichts und das Geld ist weg.",

    "strategy.warn.no_budget": "Ohne Budget bleiben ausschließlich organische Kanäle. Das ist kein "
                               "Mangel - die meisten Produkte kommen so weiter als mit einem zu "
                               "kleinen Werbebudget.",
    "strategy.warn.no_paid_fit": "Im Profil stehen {budget} EUR, aber kein bezahlter Kanal passt "
                                 "zu diesem Produkt. Die Begründungen stehen unter den verworfenen "
                                 "Kanälen. Das Geld ist in Inhalten besser aufgehoben.",
    "strategy.warn.one_channel": "{budget} EUR reichen für genau einen bezahlten Kanal. Auf zwei "
                                 "verteilt sammelt keiner der beiden genug Daten, um zu zeigen, "
                                 "ob er taugt.",
    "strategy.warn.no_analysis": "Noch keine Produktanalyse gelaufen. Die Kanalauswahl stützt sich "
                                 "allein auf die Selbsteinschätzung im Profil.",
    "strategy.warn.api_failed": "KI-Zusammenfassung fehlgeschlagen ({error}). Der Regelplan steht.",
    "strategy.summary.none": "Kein Kanal passt zu diesem Profil. Das ist fast immer ein Zeichen "
                             "dafür, dass Kategorie oder Preismodell falsch eingetragen sind.",
    "strategy.summary.line": "{name} ist als {category} eingeordnet. Die drei tragfähigsten Kanäle "
                             "sind {top}. {money}",
    "strategy.summary.organic": "Ohne Budget läuft alles organisch.",
    "strategy.summary.funded": "Von {budget} EUR im Monat gehen {named} an den Start, ein Fünftel "
                               "bleibt in Reserve.",
    "strategy.summary.unfunded": "Die hinterlegten {budget} EUR finden keinen passenden bezahlten "
                                 "Kanal.",

    # -- Werbemittel ---------------------------------------------------------
    "assets.title": "Werbemittel",
    "assets.use_api": "per KI schreiben lassen",
    "assets.intro": "Die fertigen Texte zu den Kanälen aus der Strategie - jeweils in den "
                    "Zeichengrenzen des Kanals. <b>Die Grenzen sind hart:</b> Google lehnt eine "
                    "Überschrift mit 31 Zeichen ab, nicht „ungefähr\". Jedes Feld wird nach dem "
                    "Erzeugen geprüft; was gekürzt werden musste, ist gekennzeichnet.",
    "assets.intro2": "Ohne Schlüssel setzen die Vorlagen ausschließlich zusammen, was im Profil "
                     "und in der Analyse steht - nichts wird erfunden. Das macht die Texte brav, "
                     "aber wahr. Mit Schlüssel werden sie frei geschrieben und danach genauso "
                     "geprüft.",
    "assets.build": "Texte erzeugen",
    "assets.rebuild": "Neu erzeugen",
    "assets.generated": "erzeugt per {source}, {date}",
    "assets.channel_recommended": "Kanal empfohlen",
    "assets.channel_not_planned": "Kanal nicht im Plan",
    "assets.nothing": "nichts erzeugt - im Profil fehlen die Angaben dafür",
    "assets.limit_hint": "höchstens {limit} Zeichen.",
    "assets.truncated": "gekürzt",
    "assets.too_long": "zu lang",
    "assets.negative_keywords": "Auszuschließende Suchbegriffe",
    "assets.negative_intro": "Ohne die verbrennt jede Suchkampagne Geld an Anfragen, die nichts "
                             "mit dem Produkt zu tun haben. Ein Anfang, kein Ersatz für den "
                             "Suchbegriffsbericht nach zwei Wochen.",
    "assets.utm": "Zieladresse mit Kampagnenkennzeichnung",
    "assets.from_price": "Ab {price}",
    "assets.source.vorlage": "Vorlage",
    "assets.source.anthropic": "KI",

    "assets.warn.empty": "{field}: nichts erzeugt. Im Profil fehlen die Angaben, aus denen sich "
                         "das zusammensetzen ließe.",
    "assets.warn.too_long": "{field}: {count} Einträge über der Grenze von {limit} Zeichen. Vor "
                            "dem Einspielen kürzen.",
    "assets.warn.truncated": "{field}: {count} von {total} Einträgen mussten gekürzt werden - "
                             "bitte gegenlesen, abgeschnittene Sätze wirken schlampig.",
    "assets.warn.few": "{field}: nur {count} von {wanted} Varianten. Mehr Nutzenpunkte im Profil "
                       "oder in der Analyse ergeben mehr Varianten.",
    "assets.warn.api_failed": "KI-Texte fehlgeschlagen ({error}). Die Vorlagen stehen.",

    # -- Communities ---------------------------------------------------------
    "communities.search": "Suchen ...",
    "communities.shown": "{shown} von {total} angezeigt",
    "communities.empty": "Noch keine Daten. Oben rechts <b>Scan starten</b>, Communities von Hand "
                         "aufnehmen - oder erst die <a href=\"#\" id=\"emptyHelp\">Anleitung</a> "
                         "lesen.",
    "communities.add": "Community von Hand aufnehmen",
    "communities.platform": "Plattform",
    "communities.handle": "Name",
    "communities.members": "Mitglieder",
    "communities.rules_text": "Regeln hier einfügen",
    "communities.added": "Aufgenommen - Einstufung:",
    "communities.need_handle": "Name oder URL angeben.",
    "communities.checking": "wird geprüft ...",
    "communities.evidence": "Ausschlaggebende Regeltexte",
    "communities.showcase": "Die Kategorie, in der Zeigen erwünscht ist",
    "communities.showcase_only": "dort posten und sonst nirgends in diesem Forum",
    "communities.no_evidence": "Keine einschlägigen Regeltexte gefunden.",
    "communities.do_not_post": "<b>Nicht posten.</b> Diese Community verbietet Eigenwerbung. Ein "
                               "Beitrag hier kostet dich den Account und möglicherweise die Domain.",
    "communities.draft": "Beitragsentwurf",
    "communities.generate": "Entwurf erzeugen",
    "communities.variant": "Variante",
    "communities.angle": "Blickwinkel: {angle}",
    "communities.via": "erzeugt per {source}",
    "communities.checklist": "Vor dem Posten erledigen",
    "communities.to_queue": "In Kampagne übernehmen",
    "communities.open_form": "Formular öffnen",
    "communities.mark_posted": "Als gepostet markieren",
    "communities.queued": "In die Kampagne übernommen.",
    "communities.logged": "Im Verlauf vermerkt.",
    "communities.form_opened": "Formular geöffnet. Abschicken machst du selbst.",
    "communities.guard": "<b>Schutzschalter:</b>",
    "communities.force": "Trotzdem öffnen",

    "angle.resource": "Ressource teilen",
    "angle.feedback": "Um Korrekturen bitten",
    "angle.showcase": "Projekt vorstellen",
    "angle.question": "Fachfrage mit Kontext",
    "angle.forum_intro": "Forum-Vorstellung",

    # -- Startlisten ---------------------------------------------------------
    "seeds.title": "Startpunkte für den Scan",
    "seeds.intro": "Das sind Kandidaten, keine Fakten. Jeder Eintrag wird beim Scan gegen die "
                   "echte Quelle geprüft - was es nicht mehr gibt, fliegt raus. Genau deshalb "
                   "sind auch Vorschläge eines Sprachmodells hier brauchbar: der Scanner hält "
                   "dagegen.",
    "seeds.subreddits": "Subreddits",
    "seeds.subreddits_hint": "einer pro Zeile, ohne r/",
    "seeds.forums": "Foren und Communities",
    "seeds.forums_hint": "eine pro Zeile: URL | Name | Notiz",
    "seeds.lemmy": "Lemmy-Instanzen",
    "seeds.lemmy_hint": "eine pro Zeile, z. B. lemmy.world - leer lassen für den Standardsatz",
    "seeds.lemmy_note": "Instanzen, keine Communities. Lemmy föderiert: Eine Suche auf wenigen "
                        "großen Instanzen erreicht den größten Teil des Netzes, und die "
                        "Communities werden darüber gefunden.",
    "seeds.save": "Startlisten speichern",
    "seeds.suggest": "Vorschlagen lassen (KI)",
    "seeds.needs_key": "Dafür braucht es einen Anthropic-Schlüssel in den Einstellungen.",
    "seeds.keywords": "Stichwörter, mit denen der Scan arbeitet",
    "seeds.keywords_note": "Sie stammen aus dem Produktprofil und aus der Analyse. Sind sie leer, "
                           "findet der Scan nichts - dann erst die Analyse laufen lassen.",
    "seeds.keywords_empty": "Noch keine Stichwörter. Erst das Profil ausfüllen oder die Analyse "
                            "laufen lassen.",
    "seeds.suggesting": "wird vorgeschlagen ...",
    "seeds.suggested": "{subs} Subreddits und {forums} Foren als Kandidaten hinterlegt. Der Scan "
                       "prüft sie.",
    "seeds.suggest_aborted": "Vorschlag abgebrochen.",

    # -- Scan ----------------------------------------------------------------
    "scan.starting": "Start ...",
    "scan.done": "Fertig - {count} Communities bewertet.",
    "scan.aborted": "Scan abgebrochen.",
    "scan.busy": "Es läuft bereits etwas.",
    "scan.no_keywords": "Keine Stichwörter vorhanden. Trage im Produktprofil welche ein oder lass "
                        "zuerst die Analyse laufen - ein Scan ohne Stichwörter wäre ein Rundgang "
                        "durchs Nichts.",
    "platform.lemmy": "Lemmy",
    "scan.lemmy_none": "Lemmy durchsucht, nichts oberhalb der Größenschwelle gefunden. Auch das "
                       "ist ein Ergebnis - das Netz ist klein, und nicht zu jedem Thema gibt es "
                       "dort schon eine Community.",
    "scan.no_forum_seeds": "Keine Foren-Startliste für dieses Produkt. Unter Startlisten welche "
                           "eintragen oder vorschlagen lassen.",
    "scan.nothing_yet": "Noch nichts gelaufen.",

    # -- Kampagne ------------------------------------------------------------
    "campaign.prepare": "Kampagne vorbereiten",
    "campaign.limit": "Höchstens",
    "campaign.green_only": "nur grüne Communities",
    "campaign.writing": "Entwürfe werden geschrieben ...",
    "campaign.ready": "{count} Beiträge fertig vorbereitet.",
    "campaign.queue_empty": "Die Warteschlange ist leer - oben „Kampagne vorbereiten\".",
    "campaign.start_mode": "Posting-Modus starten",
    "campaign.exit": "Posting-Modus verlassen",
    "campaign.step": "Schritt {current} von {total}: {community}",
    "campaign.scheduled": "geplant: {date}",
    "campaign.too_early": "Dieser Beitrag ist erst für ein späteres Datum eingeplant. Mehrere an "
                          "einem Tag ist das Muster, das als Spam erkannt wird.",
    "campaign.copy_open": "Text kopieren und Formular öffnen",
    "campaign.posted_next": "Gepostet - weiter",
    "campaign.skip": "Überspringen",
    "campaign.clipboard": "Der Text liegt in der Zwischenablage. Im Formular gegenlesen und "
                          "abschicken.",
    "campaign.note": "Hinweis: {reasons}",
    "campaign.finished": "Warteschlange abgearbeitet.",

    # -- Auto-Kanäle ---------------------------------------------------------
    "channels.title": "Kanäle, in denen die App selbst veröffentlichen darf",
    "channels.intro": "Nur Kanäle, die dir gehören. Ein Discord-Webhook funktioniert nur dort, wo "
                      "jemand mit Serverrechten ihn eingerichtet hat, und der Mastodon-Token ist "
                      "deiner.",
    "channels.webhook_name": "Name",
    "channels.webhook_url": "Webhook-URL",
    "channels.add_hook": "Webhook hinzufügen",
    "channels.no_hook": "Noch kein Webhook hinterlegt.",
    "channels.mastodon": "Mastodon",
    "channels.instance": "Instanz",
    "channels.token": "Zugriffstoken",
    "channels.test_post": "Testbeitrag an alle eigenen Kanäle senden",
    "channels.no_auto": "Keine eigenen Kanäle konfiguriert.",
    "channels.sent": "gesendet",
    "channels.error": "Fehler {status} {detail}",
    "channels.discord_search": "Wo sich Discord-Server finden lassen",

    # -- Verlauf -------------------------------------------------------------
    "history.empty": "Noch nichts gepostet.",
    "history.date": "Datum",
    "history.community": "Community",
    "history.channel": "Kanal",
    "history.post_title": "Titel",
    "history.result": "Ergebnis",

    # -- Einstellungen -------------------------------------------------------
    "settings.title": "Einstellungen",
    "settings.language": "Sprache",
    "settings.language_hint": "Gilt sofort und überall. Beitragsentwürfe und Werbetexte sind "
                              "davon nicht betroffen - die folgen den Sprachen am Produkt, denn "
                              "sie sind für ein Publikum geschrieben, nicht für dich.",
    "settings.reddit": "Reddit-API (Pflicht für den Reddit-Teil)",
    "settings.reddit_hint": "Reddit beantwortet Programmanfragen ohne registrierte App mit 403. "
                            "Auf reddit.com/prefs/apps ganz unten „create another app\" - Typ "
                            "<b>script</b>, Name <b>MutexxAdvertiser</b>, redirect uri "
                            "<b>http://localhost:8777</b>. Die Client-ID steht danach klein "
                            "<i>unter</i> dem App-Namen. Kostenlos, nur Lesezugriff.",
    "settings.client_id": "Client-ID",
    "settings.client_secret": "Client-Secret",
    "settings.lemmy": "Lemmy",
    "settings.lemmy_note": "Kein Schlüssel, keine Freigabe, kein Konto - Lemmy liest sich offen. Der Test sagt nur, ob eine Instanz antwortet und welche API-Version sie spricht.",
    "settings.lemmy_instance": "Instanz zum Testen",
    "settings.lemmy_ok": "{title} antwortet ({api}, {users} Konten).",
    "settings.lemmy_fail": "{instance} antwortet nicht.",
    "settings.bot_hint": "<b>Bot-Konto</b> - nur ausfüllen, wenn der Verbindungstest oben mit 401 "
                         "fehlschlägt. Reddit verlangt für Script-Apps inzwischen meist ein "
                         "<i>eigenes</i> Konto, das bei der App unter prefs/apps als Developer "
                         "eingetragen ist. Die Daten bleiben lokal in <code>config.json</code> "
                         "auf diesem Rechner.",
    "settings.bot_user": "Bot-Benutzername",
    "settings.bot_pass": "Bot-Passwort",
    "settings.test_connection": "Verbindung testen",
    "settings.scan_limits": "Grenzen des Scans",
    "settings.scan_limits_hint": "Die Stichwörter stehen am Produkt, nicht hier - siehe die Tabs "
                                 "<b>Produkt</b> und <b>Startlisten</b>.",
    "settings.max_communities": "Max. Communities",
    "settings.deep_scan": "Tiefenscan Top-N",
    "settings.min_members": "Mindest-Mitglieder",
    "settings.delay": "Pause zwischen Anfragen (s)",
    "settings.safety": "Schutzschalter",
    "settings.max_per_day": "Max. Reddit-Beiträge pro Tag",
    "settings.min_days": "Mindestabstand je Community (Tage)",
    "settings.anthropic": "Anthropic-API (optional)",
    "settings.anthropic_hint": "Ohne Schlüssel arbeitet die App mit Vorlagen. Mit Schlüssel werden "
                               "Analyse, Strategie-Zusammenfassung, Entwürfe und Werbetexte frei "
                               "geschrieben.",
    "settings.api_key": "API-Schlüssel",
    "settings.model": "Modell",
    "settings.save": "Einstellungen speichern",

    # -- Schutzschalter ------------------------------------------------------
    "guard.daily_limit": "Tageslimit erreicht: heute wurden bereits {count} Reddit-Beiträge "
                         "gesetzt (Limit {limit}). Mehrere Subreddits am selben Tag ist genau das "
                         "Muster, das als Spam erkannt wird.",
    "guard.too_soon": "Hier wurde vor {days} Tagen schon gepostet - Mindestabstand ist {minimum} "
                      "Tage.",
    "guard.forbidden": "Diese Community verbietet Eigenwerbung ausdrücklich.",

    # -- Entwürfe ------------------------------------------------------------
    "draft.language_warning": "Die Zielcommunity ist erkennbar {community_language}sprachig, die "
                              "Produkttexte im Profil sind {product_language}. Vorlagen können "
                              "nicht übersetzen - für einen Beitrag in der Sprache der Community "
                              "den KI-Entwurf verwenden oder Einzeiler und Beschreibung im Profil "
                              "in beiden Sprachen pflegen.",
    "draft.forbidden_banner": "### Diese Community verbietet Eigenwerbung. Der Entwurf ist nur zur "
                              "Ansicht erzeugt worden - hier bitte NICHT posten.",
    "draft.api_failed": "KI-Entwurf fehlgeschlagen ({error}); Vorlage verwendet.",

    # -- Fehler --------------------------------------------------------------
    "error.unknown_path": "Unbekannter Pfad",
    "error.not_found": "Community nicht gefunden.",
    "error.no_product": "Kein Produkt angelegt.",
    "error.product_not_found": "Produkt nicht gefunden.",
    "error.unknown_asset": "Unbekanntes Werbemittel.",
    "error.subreddit_missing": "Subreddit-Name fehlt.",
    "error.url_missing": "URL fehlt.",
    "error.lemmy_handle": "Eine Lemmy-Community braucht die Form community@instanz, z. B. selfhosted@lemmy.world - denselben Namen gibt es auf Dutzenden Instanzen.",
    "error.no_api_key": "Kein Anthropic-API-Schlüssel hinterlegt.",
    "error.api_status": "Die Anthropic-API antwortete mit {status}: {detail}",
    "error.no_json": "Die Antwort der API enthielt kein verwertbares JSON.",
}


# The channel catalogue and the asset specifications live in their own file so both
# stay readable. They belong to the same dictionary.
from .i18n_content import DE_CONTENT, EN_CONTENT  # noqa: E402

EN.update(EN_CONTENT)
DE.update(DE_CONTENT)

CATALOG: dict[str, dict[str, str]] = {"en": EN, "de": DE}
