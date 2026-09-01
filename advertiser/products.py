"""
Product profiles.

The Advertiser no longer works for one built-in product but for any number of
profiles you switch between. A profile is everything the later stages need in order
to work without asking anything: analysis, strategy and drafts read from here alone.

Every profile has its own data folder (data/products/<slug>/). Two campaigns must
never share a community list - otherwise the safety catch counts product A's posts
against product B's daily limit.
"""

from __future__ import annotations

import re
import time
import unicodedata
from typing import Any

from . import core, i18n

# ---------------------------------------------------------------------------
# Classification. These lists are the dials the strategy engine turns when it
# picks channels - the order here is the order shown in the interface.
#
# The values are TRANSLATION KEYS, not labels. Nothing user-visible is stored in
# German or English anywhere in the data; the interface resolves keys against the
# catalogue, which is what makes the language switch work retroactively.
# ---------------------------------------------------------------------------

CATEGORIES: dict[str, str] = {
    "software_desktop": "category.software_desktop",
    "software_web": "category.software_web",
    "app_mobile": "category.app_mobile",
    "game": "category.game",
    "dev_tool": "category.dev_tool",
    "content_site": "category.content_site",
    "shop_physical": "category.shop_physical",
    "service": "category.service",
    "creative": "category.creative",
    "other": "category.other",
}

PRICE_MODELS: dict[str, str] = {
    "free": "price.free",
    "freemium": "price.freemium",
    "one_time": "price.one_time",
    "subscription": "price.subscription",
    "ad_supported": "price.ad_supported",
    "shop": "price.shop",
    "quote": "price.quote",
}

TONES: dict[str, str] = {
    "sachlich": "tone.sachlich",
    "fachlich": "tone.fachlich",
    "locker": "tone.locker",
    "werblich": "tone.werblich",
}


def category_label(key: str, language: str = i18n.DEFAULT_LANGUAGE) -> str:
    return i18n.t(CATEGORIES.get(key, "category.other"), language)


def category_short(key: str, language: str = i18n.DEFAULT_LANGUAGE) -> str:
    """The category without its parenthetical. The bracketed platforms help you pick
    from a dropdown; printed in a press kit they become a promise nobody made."""
    return i18n.t("category.short." + (key if key in CATEGORIES else "other"), language)


def price_label(key: str, language: str = i18n.DEFAULT_LANGUAGE) -> str:
    return i18n.t(PRICE_MODELS.get(key, "price.free"), language)


def tone_label(key: str, language: str = i18n.DEFAULT_LANGUAGE) -> str:
    return i18n.t(TONES.get(key, "tone.sachlich"), language)

PRODUCT_TEMPLATE: dict[str, Any] = {
    "slug": "",
    "name": "",
    "url": "",
    "version": "",
    "one_liner": "",
    "description": "",
    "category": "other",
    "price_model": "free",
    "price_point": "",
    "audience": "",
    "regions": ["DE"],
    "languages": ["de"],
    "budget_monthly_eur": 0,
    "tone": "sachlich",
    "keywords": [],
    "links": {"repo": "", "download": "", "docs": "", "press_kit": "", "screenshots": []},
    "accounts": {"reddit_username": "", "mastodon": "", "x": "", "youtube": ""},
    "utm_source_base": "",
    "created_at": 0,
    "updated_at": 0,
}


# ---------------------------------------------------------------------------
# Slug
# ---------------------------------------------------------------------------

_SLUG_STRIP = re.compile(r"[^a-z0-9]+")

_UMLAUTS = {
    "ä": "ae", "ö": "oe", "ü": "ue",
    "Ä": "ae", "Ö": "oe", "Ü": "ue", "ß": "ss",
}


def slugify(text: str) -> str:
    """A short name safe for the file system. Umlauts are spelled out rather than
    dropped - "Bueropflege" should not become "bropflege"."""
    folded = text or ""
    for source, target in _UMLAUTS.items():
        folded = folded.replace(source, target)
    folded = unicodedata.normalize("NFKD", folded)
    folded = "".join(char for char in folded if not unicodedata.combining(char))
    return _SLUG_STRIP.sub("-", folded.lower()).strip("-")[:48] or "produkt"


def _unique_slug(base: str, taken: set[str]) -> str:
    if base not in taken:
        return base
    for suffix in range(2, 100):
        candidate = f"{base}-{suffix}"
        if candidate not in taken:
            return candidate
    return f"{base}-{int(time.time())}"


# ---------------------------------------------------------------------------
# Normalisation
# ---------------------------------------------------------------------------

def normalise(raw: dict, *, taken: set[str] | None = None) -> dict:
    """Fills a raw profile out to its full shape and tidies the free-text fields."""
    product = core._deep_merge(PRODUCT_TEMPLATE, {})
    for key, value in (raw or {}).items():
        if key in ("links", "accounts") and isinstance(value, dict):
            product[key] = core._deep_merge(product[key], value)
        elif key in product:
            product[key] = value

    product["name"] = (product["name"] or "").strip() or "Unbenanntes Produkt"
    product["url"] = _normalise_url(product["url"])
    for field in ("version", "one_liner", "description", "audience", "price_point"):
        product[field] = (product[field] or "").strip()

    if product["category"] not in CATEGORIES:
        product["category"] = "other"
    if product["price_model"] not in PRICE_MODELS:
        product["price_model"] = "free"
    if product["tone"] not in TONES:
        product["tone"] = "sachlich"

    product["keywords"] = _clean_list(product["keywords"])
    product["regions"] = _clean_list(product["regions"], upper=True) or ["DE"]
    product["languages"] = [lang.lower() for lang in _clean_list(product["languages"])] or ["de"]

    try:
        product["budget_monthly_eur"] = max(0, int(float(product["budget_monthly_eur"] or 0)))
    except (TypeError, ValueError):
        product["budget_monthly_eur"] = 0

    slug = slugify(product["slug"] or product["name"])
    if taken is not None:
        slug = _unique_slug(slug, taken - {product.get("slug") or ""})
    product["slug"] = slug

    if not product["utm_source_base"]:
        product["utm_source_base"] = slug

    now = int(time.time())
    product["created_at"] = int(product["created_at"] or now)
    product["updated_at"] = now
    return product


def _normalise_url(url: str) -> str:
    url = (url or "").strip()
    if url and not url.startswith(("http://", "https://")):
        url = "https://" + url
    return url


def _clean_list(value: Any, *, upper: bool = False) -> list[str]:
    """Takes a list or delimited free text and returns a clean list."""
    if isinstance(value, str):
        items = re.split(r"[,\n;]+", value)
    elif isinstance(value, (list, tuple)):
        items = [str(item) for item in value]
    else:
        return []
    out: list[str] = []
    for item in items:
        cleaned = item.strip().upper() if upper else item.strip()
        if cleaned and cleaned not in out:
            out.append(cleaned)
    return out


# ---------------------------------------------------------------------------
# Reading and writing the set
# ---------------------------------------------------------------------------

def all_products(config: dict) -> list[dict]:
    return list(config.get("products") or [])


def active_slug(config: dict) -> str:
    products = all_products(config)
    if not products:
        return ""
    wanted = config.get("active_product") or ""
    if any(product.get("slug") == wanted for product in products):
        return wanted
    return products[0].get("slug", "")


def active(config: dict) -> dict:
    """The active profile. Returns an empty template profile when none exists - the
    interface has to start on a fresh installation too."""
    slug = active_slug(config)
    for product in all_products(config):
        if product.get("slug") == slug:
            return product
    return normalise({})


def get(config: dict, slug: str) -> dict | None:
    for product in all_products(config):
        if product.get("slug") == slug:
            return product
    return None


def upsert(config: dict, raw: dict) -> dict:
    """Creates or updates a profile. Returns the stored profile."""
    products = all_products(config)
    taken = {product.get("slug", "") for product in products}
    product = normalise(raw, taken=taken)

    replaced = False
    for index, existing in enumerate(products):
        if existing.get("slug") == product["slug"]:
            product["created_at"] = existing.get("created_at") or product["created_at"]
            products[index] = product
            replaced = True
            break
    if not replaced:
        products.append(product)

    config["products"] = products
    if not config.get("active_product"):
        config["active_product"] = product["slug"]
    return product


def remove(config: dict, slug: str) -> bool:
    products = all_products(config)
    remaining = [product for product in products if product.get("slug") != slug]
    if len(remaining) == len(products):
        return False
    config["products"] = remaining
    if config.get("active_product") == slug:
        config["active_product"] = remaining[0]["slug"] if remaining else ""
    return True


def set_active(config: dict, slug: str) -> bool:
    if not get(config, slug):
        return False
    config["active_product"] = slug
    return True


# ---------------------------------------------------------------------------
# Migration from the old single-product configuration
# ---------------------------------------------------------------------------

LEGACY_STORES = ("communities", "queue", "history")

# From this version on the configuration knows about product profiles. The marker
# stops the migration from running again on every start.
SCHEMA_VERSION = 2


def migrate(config: dict) -> bool:
    """Carries an old config['site'] over into a profile. Returns True when something
    changed and the configuration has to be saved."""
    if int(config.get("schema_version") or 0) >= SCHEMA_VERSION:
        return False
    config["schema_version"] = SCHEMA_VERSION

    site = config.get("site") or {}
    name = (site.get("name") or "").strip()
    # The as-shipped state is not a product - no profile comes out of it.
    if not name or name == "Mein Produkt" or config.get("products"):
        config.setdefault("products", [])
        config.setdefault("active_product", "")
        return True

    product = upsert(config, {
        "name": name,
        "url": site.get("url", ""),
        "version": site.get("version", ""),
        "one_liner": site.get("one_liner", ""),
        "keywords": (config.get("discovery") or {}).get("keywords", []),
        "accounts": {"reddit_username": site.get("reddit_username", "")},
    })
    config["active_product"] = product["slug"]

    # Move the old data files into the migrated product's folder.
    for store in LEGACY_STORES:
        legacy = core.load(store, None)
        if legacy is not None:
            core.save_product(product["slug"], store, legacy)
    return True


core.register_migration(migrate)
