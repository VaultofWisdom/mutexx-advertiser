"""
Assets: the finished copy for the channels the strategy recommends.

The strategy says WHAT to do. This module supplies the material: ad copy within each
channel's character limits, directory descriptions in three lengths, store listings, a
press kit, SEO fields and announcements for owned channels.

Three principles separate this module from a text generator:

1. CHARACTER LIMITS ARE HARD. Google rejects an ad headline of 31 characters, not
   "roughly". Every field is checked after generation; anything too long is cut AND
   marked as cut. AI copy runs through the same check - language models count
   notoriously badly.

2. NOTHING IS INVENTED. The templates assemble only what is in the profile and the
   analysis. "No ads" appears only when it says so there. An ad with an invented
   property is not advertising, it is a false statement in the user's name.

3. CUT IS NOT WRITTEN. Candidates that fit by themselves come before ones that had to
   be trimmed. A headline chopped mid-word is worse than none at all.
"""

from __future__ import annotations

import re
import time
import urllib.parse
from typing import Any

from . import core, i18n, products

# ---------------------------------------------------------------------------
# Character limits
#
# The state of the channels when this module was built. They change; if a channel
# complains, the number here is what needs fixing, not the copy.
# ---------------------------------------------------------------------------

ASSETS: list[dict[str, Any]] = [
    {
        "id": "seo_meta", "channel": "product_page", "categories": None, "note": False,
        "fields": [
            {"key": "title", "limit": 60, "count": 3},
            {"key": "description", "limit": 155, "count": 3},
            {"key": "og_title", "limit": 60, "count": 2},
            {"key": "og_description", "limit": 110, "count": 2},
        ],
    },
    {
        "id": "directory_listing", "channel": "directories", "categories": None, "note": False,
        "fields": [
            {"key": "tagline", "limit": 80, "count": 3},
            {"key": "short", "limit": 250, "count": 2},
            {"key": "long", "limit": 1200, "count": 1},
        ],
    },
    {
        "id": "own_channel_post", "channel": "own_channels", "categories": None, "note": False,
        "fields": [
            {"key": "discord", "limit": 1900, "count": 1},
            {"key": "mastodon", "limit": 480, "count": 2},
        ],
    },
    {
        "id": "google_search_ads", "channel": "google_search_ads", "categories": None,
        "note": True,
        "fields": [
            {"key": "headlines", "limit": 30, "count": 10},
            {"key": "descriptions", "limit": 90, "count": 4},
            {"key": "paths", "limit": 15, "count": 2},
        ],
    },
    {
        "id": "microsoft_ads", "channel": "microsoft_ads", "categories": None, "note": False,
        "fields": [
            {"key": "headlines", "limit": 30, "count": 6},
            {"key": "descriptions", "limit": 90, "count": 3},
        ],
    },
    {
        "id": "meta_ads", "channel": "meta_ads", "categories": None, "note": True,
        "fields": [
            {"key": "primary_text", "limit": 125, "count": 3},
            {"key": "headline", "limit": 40, "count": 3},
            {"key": "description", "limit": 30, "count": 2},
        ],
    },
    {
        "id": "reddit_ads", "channel": "reddit_ads", "categories": None, "note": True,
        "fields": [
            {"key": "headline", "limit": 100, "count": 4},
            {"key": "body", "limit": 400, "count": 2},
        ],
    },
    {
        "id": "store_listing", "channel": "app_store", "note": False,
        "categories": ["app_mobile", "game", "software_desktop"],
        "fields": [
            {"key": "app_name", "limit": 30, "count": 2},
            {"key": "subtitle", "limit": 30, "count": 3},
            {"key": "short_description", "limit": 80, "count": 3},
            {"key": "steam_short", "limit": 300, "count": 1},
            {"key": "full_description", "limit": 4000, "count": 1},
            {"key": "keywords", "limit": 100, "count": 1},
        ],
    },
    {
        "id": "press_kit", "channel": "press", "categories": None, "note": False,
        "fields": [
            {"key": "headline", "limit": 90, "count": 2},
            {"key": "lead", "limit": 400, "count": 1},
            {"key": "body", "limit": 1600, "count": 1},
            {"key": "boilerplate", "limit": 500, "count": 1},
            {"key": "facts", "limit": 700, "count": 1},
        ],
    },
]


ASSETS_BY_ID = {asset["id"]: asset for asset in ASSETS}


def field_label_key(asset_id: str, field_key: str) -> str:
    return f"asset.{asset_id}.field.{field_key}"


def field_hint_key(asset_id: str, field_key: str) -> str:
    return f"asset.{asset_id}.hint.{field_key}"


def spec_for(asset_id: str) -> dict:
    """The specification with its translation keys attached, ready for the interface."""
    spec = ASSETS_BY_ID[asset_id]
    return {
        "id": asset_id,
        "channel": spec["channel"],
        "name_key": f"asset.{asset_id}.name",
        "what_key": f"asset.{asset_id}.what",
        "note_key": f"asset.{asset_id}.note" if spec["note"] else "",
        "fields": [
            {"key": field["key"], "limit": field["limit"], "count": field["count"],
             "label_key": field_label_key(asset_id, field["key"]),
             "hint_key": field_hint_key(asset_id, field["key"])}
            for field in spec["fields"]
        ],
    }


# ---------------------------------------------------------------------------
# Enforcing the character limits
# ---------------------------------------------------------------------------

_TRAIL = " ,;:.-–—"


def tidy(text: str) -> str:
    return re.sub(r"[ \t]+", " ", str(text or "")).strip()


def fit(text: str, limit: int) -> tuple[str, bool]:
    """Cuts to the limit and says whether it cut.

    The cut lands on a word boundary, never mid-word - a headline like "System ca" is
    worse than none. Only when the first word alone is already too long does it cut
    hard.
    """
    text = tidy(text)
    if len(text) <= limit:
        return text, False
    cut = text[:limit + 1]
    space = cut.rfind(" ")
    if space > 0:
        return cut[:space].rstrip(_TRAIL), True
    return text[:limit].rstrip(_TRAIL), True


def _pick(candidates: list[str], limit: int, count: int) -> list[dict]:
    """Picks the best candidates for one field.

    Order: what fits by itself, then what had to be cut. Duplicates drop out, so does
    anything empty.
    """
    passend: list[dict] = []
    gekuerzt: list[dict] = []
    gesehen: set[str] = set()

    for candidate in candidates:
        text, was_cut = fit(candidate, limit)
        if not text or len(text) < 3 or text.lower() in gesehen:
            continue
        gesehen.add(text.lower())
        entry = {"text": text, "length": len(text), "limit": limit,
                 "ok": len(text) <= limit, "truncated": was_cut}
        (gekuerzt if was_cut else passend).append(entry)

    return (passend + gekuerzt)[:count]


def validate(fields: dict[str, list[dict]], spec: dict) -> list[dict]:
    """Checks a finished asset against its limits. Returns translatable messages, not
    error codes - a human reads these."""
    hints: list[dict] = []
    for field in spec["fields"]:
        label = i18n.message(field_label_key(spec["id"], field["key"]))
        entries = fields.get(field["key"], [])
        if not entries:
            hints.append(i18n.message("assets.warn.empty", field=label))
            continue
        over = [e for e in entries if e["length"] > field["limit"]]
        if over:
            hints.append(i18n.message("assets.warn.too_long", field=label,
                                      count=len(over), limit=field["limit"]))
        cut = [e for e in entries if e.get("truncated")]
        if cut:
            hints.append(i18n.message("assets.warn.truncated", field=label,
                                      count=len(cut), total=len(entries)))
        if len(entries) < field["count"]:
            hints.append(i18n.message("assets.warn.few", field=label,
                                      count=len(entries), wanted=field["count"]))
    return hints


# ---------------------------------------------------------------------------
# UTM tagging
# ---------------------------------------------------------------------------

def utm_url(product: dict, channel: str, medium: str = "", campaign: str = "") -> str:
    """Appends the campaign tagging to the product URL. Without it nobody ever learns
    which channel carried - and the channel choice stays a matter of taste forever."""
    url = (product.get("url") or "").strip()
    if not url:
        return ""
    params = {
        "utm_source": channel or product.get("utm_source_base") or "advertiser",
        "utm_medium": medium or "referral",
        "utm_campaign": campaign or product.get("utm_source_base") or "start",
    }
    parts = urllib.parse.urlsplit(url)
    query = urllib.parse.parse_qsl(parts.query)
    query += [(key, value) for key, value in params.items()]
    return urllib.parse.urlunsplit(
        (parts.scheme, parts.netloc, parts.path, urllib.parse.urlencode(query), parts.fragment))


UTM_MEDIUM = {
    "google_search_ads": "cpc", "microsoft_ads": "cpc", "meta_ads": "paid_social",
    "reddit_ads": "paid_social", "video_ads": "video", "sponsoring": "sponsorship",
    "directories": "referral", "press": "referral", "own_channels": "owned",
    "app_store": "store", "newsletter": "email",
}


# ---------------------------------------------------------------------------
# Building blocks from profile and analysis
#
# From here on, only what the user entered or the analysis found gets assembled. No
# sentence comes out of nowhere.
# ---------------------------------------------------------------------------

# Calls to action per pricing model.
#
# Every one of them has to FOLLOW from the pricing model, not merely suit it. "Free
# trial" on a subscription asserts a trial period that is nowhere in the profile.
# Sentences exactly like that turn ad copy into a false statement, and they go
# unnoticed because they sound so familiar.
_CTA = {
    "de": {
        "free": ["Kostenlos nutzen", "Jetzt ansehen", "Direkt loslegen"],
        "freemium": ["Kostenlos starten", "Gratis-Version nutzen", "Jetzt ausprobieren"],
        "one_time": ["Einmal zahlen, kein Abo", "Lizenz kaufen", "Jetzt kaufen"],
        "subscription": ["Jetzt abonnieren", "Preise ansehen", "Mehr erfahren"],
        "ad_supported": ["Kostenlos nutzen", "Jetzt ansehen"],
        "shop": ["Jetzt bestellen", "Im Shop ansehen", "Direkt bestellen"],
        "quote": ["Angebot anfordern", "Unverbindlich anfragen"],
    },
    "en": {
        "free": ["Use it for free", "Take a look", "Get started"],
        "freemium": ["Start for free", "Use the free version", "Give it a try"],
        "one_time": ["Pay once, no subscription", "Buy a licence", "Buy now"],
        "subscription": ["Subscribe now", "See the plans", "Learn more"],
        "ad_supported": ["Use it for free", "Take a look"],
        "shop": ["Order now", "See it in the shop", "Buy now"],
        "quote": ["Request a quote", "Ask, no strings attached"],
    },
}

# Category lines. This used to read "For Windows, Mac and Linux" - which asserts
# three platforms for every desktop product, including a Windows-only tool. What is
# left is only what follows from the category itself. Which platforms a product runs
# on is in its description or nowhere.
_CATEGORY_PHRASE = {
    "de": {
        "software_desktop": "Für den Desktop",
        "software_web": "Läuft im Browser",
        "app_mobile": "Für das Handy",
        "game": "Jetzt spielen",
        "dev_tool": "Für Entwickler",
        "content_site": "Nachschlagen statt suchen",
        "shop_physical": "",
        "service": "",
        "creative": "Jetzt entdecken",
        "other": "",
    },
    "en": {
        "software_desktop": "For the desktop",
        "software_web": "Runs in your browser",
        "app_mobile": "For your phone",
        "game": "Play it now",
        "dev_tool": "Built for developers",
        "content_site": "Look it up, do not search",
        "shop_physical": "",
        "service": "",
        "creative": "Have a look",
        "other": "",
    },
}

def _language(product: dict) -> str:
    languages = [lang.lower() for lang in (product.get("languages") or ["de"])]
    return "de" if "de" in languages[:1] or not languages else (
        "en" if languages[0] == "en" else "de")


def _bausteine(product: dict, analysis_result: dict) -> dict[str, Any]:
    """Everything copy can be built from, collected in one place."""
    language = _language(product)
    props = [tidy(p).rstrip(".") for p in (analysis_result.get("value_props") or []) if tidy(p)]
    objections = [tidy(o) for o in (analysis_result.get("objections") or []) if tidy(o)]
    terms = [tidy(t) for t in (analysis_result.get("search_terms") or []) if tidy(t)]
    terms += [tidy(k) for k in (product.get("keywords") or []) if tidy(k)]
    terms += [item.get("term", "") for item in (analysis_result.get("keywords") or [])]

    gesehen: set[str] = set()
    stichwoerter: list[str] = []
    for term in terms:
        low = term.lower().strip()
        if low and low not in gesehen:
            gesehen.add(low)
            stichwoerter.append(low)

    beschreibung = tidy(product.get("description", ""))
    saetze = [s.strip() for s in re.split(r"(?<=[.!?])\s+", beschreibung) if s.strip()]

    return {
        "language": language,
        "price_model": product.get("price_model", "free"),
        "name": tidy(product.get("name", "")) or "Das Projekt",
        "url": tidy(product.get("url", "")),
        "domain": urllib.parse.urlsplit(product.get("url") or "").netloc.replace("www.", ""),
        "version": tidy(product.get("version", "")),
        "one_liner": tidy(product.get("one_liner", "")).rstrip("."),
        "description": beschreibung,
        "saetze": saetze,
        "props": props,
        "objections": objections,
        "stichwoerter": stichwoerter,
        "audience": tidy(product.get("audience", "")),
        "price_point": tidy(product.get("price_point", "")),
        "price_fact": products.price_label(product.get("price_model", "free"), language),
        "cta": _CTA[language].get(product.get("price_model", "free"), []),
        "category_phrase": _CATEGORY_PHRASE[language].get(product.get("category", "other"), ""),
        # The bracketed platforms in the category help you pick from a dropdown. Read
        # in a press kit they turn into a platform promise nobody made - so the short
        # form is used here.
        "category_label": products.category_short(product.get("category", "other"), language),
        "positioning": tidy(analysis_result.get("positioning", "")),
        "regions": ", ".join(product.get("regions") or []),
    }


def _gross(text: str) -> str:
    text = tidy(text)
    return text[:1].upper() + text[1:] if text else text


# ---------------------------------------------------------------------------
# Templates per asset
# ---------------------------------------------------------------------------

def _kandidaten(asset_id: str, b: dict) -> dict[str, list[str]]:
    de = b["language"] == "de"
    name, url, one_liner = b["name"], b["url"], b["one_liner"]
    props, saetze, stich = b["props"], b["saetze"], b["stichwoerter"]

    if asset_id == "seo_meta":
        titel = [f"{name} - {one_liner}" if one_liner else name, name]
        titel += [f"{_gross(term)} - {name}" for term in stich[:3]]
        besch = []
        if one_liner:
            besch.append(f"{_gross(one_liner)}. " + (props[0] + "." if props else b["price_fact"] + "."))
        if props:
            besch.append(_gross(". ".join(props[:2])) + ".")
        if saetze:
            besch.append(" ".join(saetze[:2]))
        besch.append((b["description"] or one_liner or name))
        return {
            "title": titel,
            "description": besch,
            "og_title": [name, f"{name} - {one_liner}" if one_liner else name],
            "og_description": [_gross(one_liner) + "." if one_liner else "",
                               props[0] + "." if props else b["description"]],
        }

    if asset_id == "directory_listing":
        lang_teile = [_gross(one_liner) + "." if one_liner else "", b["description"]]
        if props:
            lang_teile.append(i18n.t("listing.what_it_does", b["language"]) + "\n"
                              + "\n".join(f"- {p}" for p in props[:6]))
        if b["audience"]:
            lang_teile.append(i18n.t("listing.who_for", b["language"]) + " " + b["audience"])
        if b["price_fact"]:
            preis = b["price_fact"] + (f" ({b['price_point']})" if b["price_point"] else "")
            lang_teile.append(i18n.t("listing.pricing", b["language"]) + " " + preis + ".")
        return {
            "tagline": [one_liner, props[0] if props else "", b["category_phrase"]],
            "short": [
                (_gross(one_liner) + ". " if one_liner else "")
                + (" ".join(f"{p}." for p in props[:2]) if props else " ".join(saetze[:1])),
                b["description"] or one_liner,
            ],
            "long": ["\n\n".join(teil for teil in lang_teile if teil.strip())],
        }

    if asset_id == "own_channel_post":
        kopf = f"**{name}{(' ' + b['version']) if b['version'] else ''}**"
        punkte = "\n".join(f"* {p}" for p in props[:5])
        discord = "\n\n".join(teil for teil in [
            kopf,
            _gross(one_liner) + "." if one_liner else b["description"],
            punkte,
            url,
        ] if teil.strip())
        kurz = f"{name}{(' ' + b['version']) if b['version'] else ''}: "
        return {
            "discord": [discord],
            "mastodon": [
                kurz + (one_liner or b["description"]) + (f"\n\n{url}" if url else ""),
                (props[0] + f"\n\n{name} - {url}") if props else (kurz + one_liner),
            ],
        }

    if asset_id in ("google_search_ads", "microsoft_ads"):
        headlines = [name]
        if b["version"]:
            headlines.append(f"{name} {b['version']}")
        headlines += [_gross(term) for term in stich[:4]]
        headlines += [_gross(p) for p in props[:4]]
        headlines += b["cta"]
        headlines += [b["category_phrase"], one_liner]
        if b["price_point"]:
            headlines.append((i18n.t("assets.from_price", b["language"], price=b["price_point"])))
        beschreibungen = []
        if one_liner:
            beschreibungen.append(_gross(one_liner) + "." + (" " + b["cta"][0] + "." if b["cta"] else ""))
        for prop in props[:3]:
            beschreibungen.append(_gross(prop) + "." + (" " + b["cta"][0] + "." if b["cta"] else ""))
        if saetze:
            beschreibungen.append(saetze[0])
        return {
            "headlines": headlines,
            "descriptions": beschreibungen,
            "paths": [term.split(" ")[0] for term in stich[:2]] + [
                products.slugify(b["category_label"])[:15]],
        }

    if asset_id == "meta_ads":
        primaer = []
        if one_liner:
            primaer.append(_gross(one_liner) + "." + (" " + props[0] + "." if props else ""))
        for prop in props[:2]:
            primaer.append(_gross(prop) + "." + (" " + b["cta"][0] + "." if b["cta"] else ""))
        primaer.append(b["description"])
        return {
            "primary_text": primaer,
            "headline": [name, one_liner] + [_gross(p) for p in props[:2]] + b["cta"],
            "description": b["cta"] + [b["price_fact"], b["category_phrase"]],
        }

    if asset_id == "reddit_ads":
        # Reddit reads like a post. An objection as the hook works better here than
        # any claim about benefits.
        kopf = []
        if b["objections"]:
            kopf.append(b["objections"][0])
        kopf += [_gross(one_liner) if one_liner else "", f"{name}: {one_liner}" if one_liner else name]
        kopf += [_gross(p) for p in props[:2]]
        text = []
        if one_liner:
            text.append(_gross(one_liner) + ". "
                        + (" ".join(f"{p}." for p in props[:2]) if props else ""))
        text.append(b["description"])
        return {"headline": kopf, "body": text}

    if asset_id == "store_listing":
        kurz = [one_liner, props[0] if props else "", b["category_phrase"]]
        voll_teile = [_gross(one_liner) + "." if one_liner else "", b["description"]]
        if props:
            voll_teile.append("\n".join(f"- {p}" for p in props[:8]))
        if b["audience"]:
            voll_teile.append(("Fuer wen: " if de else "Who it is for: ") + b["audience"])
        return {
            "app_name": [name, f"{name} - {stich[0]}" if stich else name],
            "subtitle": kurz,
            "short_description": kurz,
            "steam_short": [(_gross(one_liner) + ". " if one_liner else "") + b["description"]],
            "full_description": ["\n\n".join(t for t in voll_teile if t.strip())],
            "keywords": [",".join(stich[:12])],
        }

    if asset_id == "press_kit":
        was = f"{name}{(' ' + b['version']) if b['version'] else ''}"
        kopf = [f"{was}: {one_liner}" if one_liner else was,
                i18n.t("press.available_now", b["language"], product=was)]
        vorspann = i18n.t("press.available_now", b["language"], product=was) + ". "
        vorspann += (_gross(one_liner) + ". " if one_liner else "")
        if b["audience"]:
            vorspann += i18n.t("press.aimed_at", b["language"], audience=b["audience"]) + " "
        if b["price_fact"]:
            vorspann += b["price_fact"] + (f" ({b['price_point']})" if b["price_point"] else "") + "."
        text_teile = [b["description"]]
        if props:
            text_teile.append(i18n.t("press.in_detail", b["language"]) + "\n"
                              + "\n".join(f"- {p}" for p in props[:6]))
        if b["positioning"]:
            text_teile.append(b["positioning"])
        fakten = [i18n.t("press.fact.product", b["language"]) + f": {name}"]
        if b["version"]:
            fakten.append(i18n.t("press.fact.version", b["language"]) + f": {b['version']}")
        fakten.append(i18n.t("press.fact.type", b["language"]) + f": {b['category_label']}")
        if b["price_fact"]:
            fakten.append(i18n.t("press.fact.price", b["language"]) + f": {b['price_fact']}"
                          + (f" ({b['price_point']})" if b["price_point"] else ""))
        if b["regions"]:
            fakten.append(i18n.t("press.fact.regions", b["language"]) + f": {b['regions']}")
        if url:
            fakten.append(i18n.t("press.fact.web", b["language"]) + f": {url}")
        return {
            "headline": kopf,
            "lead": [vorspann],
            "body": ["\n\n".join(t for t in text_teile if t.strip())],
            "boilerplate": [(_gross(one_liner) + ". " if one_liner else "")
                            + (b["positioning"] or b["description"])],
            "facts": ["\n".join(fakten)],
        }

    return {}


# ---------------------------------------------------------------------------
# Generation
# ---------------------------------------------------------------------------

def available(product: dict) -> list[dict]:
    """Which assets are even in question for this product."""
    category = product.get("category", "other")
    return [spec_for(asset["id"]) for asset in ASSETS
            if not asset["categories"] or category in asset["categories"]]


def build(asset_id: str, product: dict, analysis_result: dict | None = None,
          config: dict | None = None, use_api: bool | None = None) -> dict:
    """One asset. Does not raise - failures land as a note in the result."""
    if asset_id not in ASSETS_BY_ID:
        raise ValueError(i18n.t("error.unknown_asset"))
    spec = spec_for(asset_id)

    analysis_result = analysis_result or {}
    config = config or {}
    bausteine = _bausteine(product, analysis_result)
    kandidaten = _kandidaten(asset_id, bausteine)

    fields = {field["key"]: _pick(kandidaten.get(field["key"], []), field["limit"], field["count"])
              for field in spec["fields"]}
    quelle = "vorlage"
    hinweise: list[dict] = []

    if use_api is None:
        use_api = core.ai_ready(config)
    if use_api:
        try:
            geschrieben = _build_with_api(spec, product, analysis_result, bausteine, config)
            # AI copy runs through the same check. Language models count characters
            # notoriously badly, and Google counts exactly.
            for field in spec["fields"]:
                roh = geschrieben.get(field["key"])
                if roh:
                    fields[field["key"]] = _pick(roh, field["limit"], field["count"])
            quelle = core.ai_source(config)
        except Exception as error:  # noqa: BLE001 - the templates stand
            hinweise.append(i18n.message("assets.warn.api_failed", error=error))

    channel = spec["channel"]
    return {
        "asset_id": asset_id,
        "name_key": spec["name_key"],
        "what_key": spec["what_key"],
        "note_key": spec["note_key"],
        "channel": channel,
        "product_slug": product.get("slug", ""),
        "generated_at": int(time.time()),
        "generated_by": quelle,
        "language": bausteine["language"],
        "spec": spec["fields"],
        "fields": fields,
        "utm_url": utm_url(product, channel, UTM_MEDIUM.get(channel, "referral")),
        "negative_keywords": _negative_keywords(bausteine) if asset_id in
        ("google_search_ads", "microsoft_ads") else [],
        "warnings": hinweise + validate(fields, spec),
    }


# Search terms that burn money for practically every product: people looking for
# something free, second-hand or cracked do not buy.
_NEGATIVE_BASE = {
    "de": ["kostenlos", "gratis", "umsonst", "crack", "keygen", "seriennummer", "torrent",
           "gebraucht", "alternative kostenlos", "jobs", "gehalt", "erfahrungen forum",
           "wikipedia", "bedeutung", "definition"],
    "en": ["free", "crack", "keygen", "serial", "torrent", "pirated", "used", "jobs",
           "salary", "wikipedia", "meaning", "definition", "reddit free"],
}


_GRATIS_BEGRIFFE = {"kostenlos", "gratis", "umsonst", "free", "alternative kostenlos",
                    "reddit free"}


def _negative_keywords(b: dict) -> list[str]:
    negative = list(_NEGATIVE_BASE[b["language"]])
    # Someone searching for "free" is exactly the right visitor for a free or
    # ad-supported product - and the top of the funnel for freemium. Only a product
    # that purely sells excludes those searches.
    if b["price_model"] in ("free", "freemium", "ad_supported"):
        negative = [term for term in negative if term not in _GRATIS_BEGRIFFE]
    return negative


# ---------------------------------------------------------------------------
# AI copy
# ---------------------------------------------------------------------------

_SYSTEM = """You write ad copy for a particular product in a particular channel.

Rules, in this order:
1. CHARACTER LIMITS. Every field has a hard upper bound. Count. Copy over the limit is
   rejected by the channel and is worthless. Clearly shorter beats barely over.
2. INVENT NOTHING. Name only properties that appear in the product profile or the
   analysis. No numbers, no awards, no comparisons that are not evidenced there.
3. No superlatives, no exclamation marks, no agency language, no emoji.
4. Every variant must differ from the others - not the same thing rearranged.
5. Answer only as JSON, with no preamble and no code fence. Every field is a list of
   strings, even when only one is asked for."""


def _build_with_api(spec: dict, product: dict, analysis_result: dict, bausteine: dict,
                    config: dict) -> dict[str, list[str]]:
    if not core.ai_ready(config):
        raise ValueError(i18n.t("error.no_api_key"))

    language = bausteine["language"]
    feldzeilen = "\n".join(
        f'- "{field["key"]}": {field["count"]} variants, at most {field["limit"]} characters '
        f'each. {i18n.t(field["label_key"], language)} - {i18n.t(field["hint_key"], language)}'
        for field in spec["fields"])

    prompt = f"""KANAL
{i18n.t(spec['name_key'], language)}: {i18n.t(spec['what_key'], language)}
{i18n.t(spec['note_key'], language) if spec['note_key'] else ''}

PRODUKT
Name: {bausteine['name']}
URL: {bausteine['url'] or '(keine)'}
Version: {bausteine['version'] or '(keine)'}
Einzeiler: {bausteine['one_liner'] or '(keiner)'}
Beschreibung: {bausteine['description'][:1500] or '(keine)'}
Art: {bausteine['category_label']}
Preis: {bausteine['price_fact']}{' (' + bausteine['price_point'] + ')' if bausteine['price_point'] else ''}
Zielgruppe: {bausteine['audience'] or '(nicht angegeben)'}
Regionen: {bausteine['regions']}
Tone: {products.tone_label(product.get('tone'), language)}

ANALYSE
Positionierung: {bausteine['positioning'] or '(keine)'}
Nutzenversprechen: {'; '.join(bausteine['props']) or '(keine)'}
Zu erwartende Einwaende: {'; '.join(bausteine['objections']) or '(keine)'}
Suchbegriffe der Zielgruppe: {', '.join(bausteine['stichwoerter'][:20]) or '(keine)'}

FELDER
{feldzeilen}

Sprache: {'Deutsch' if bausteine['language'] == 'de' else 'Englisch'}."""

    parsed = core.ask_ai_json(config, _SYSTEM, prompt)

    out: dict[str, list[str]] = {}
    for field in spec["fields"]:
        value = parsed.get(field["key"])
        if isinstance(value, str):
            value = [value]
        if isinstance(value, list):
            sauber = [str(item).strip() for item in value if str(item).strip()]
            if sauber:
                out[field["key"]] = sauber
    return out


# ---------------------------------------------------------------------------
# Storage
# ---------------------------------------------------------------------------

def load_all(slug: str) -> dict:
    stored = core.load_product(slug, "assets", {})
    return stored if isinstance(stored, dict) else {}


def store(slug: str, asset: dict) -> dict:
    alle = load_all(slug)
    alle[asset["asset_id"]] = asset
    core.save_product(slug, "assets", alle)
    return alle
