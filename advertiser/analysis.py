"""
Product analysis.

From a profile and - where a URL is on file - the product page itself, this works out
what the product actually is, who it suits, and what words its audience searches with.
The result is not decoration: it feeds the keyword list of the community search, the
channel selection of the strategy, and the drafts.

Two modes, as everywhere in this app:

  * without an API key: the page is fetched and evaluated statistically - title, meta
    description, word frequencies, word pairs, signals for category and pricing. Free,
    inspectable offline, but blunt.
  * with an Anthropic key, additionally a free analysis: audience segments, value
    propositions, positioning, objections to expect, search terms.

The statistical evaluation runs ALWAYS, even when the AI analysis joins it. That keeps
it traceable which part came off the page and which part the model contributed.
"""

from __future__ import annotations

import html
import json
import re
import time
from collections import Counter
from typing import Any, Callable

from . import core, i18n, products

Progress = Callable[[str, int, int], None]


def _noop(_message: str, _done: int, _total: int) -> None:
    return None


# ---------------------------------------------------------------------------
# Reading the page
# ---------------------------------------------------------------------------

_TAG = re.compile(r"<[^>]+>")
_TITLE = re.compile(r"<title[^>]*>(.*?)</title>", re.I | re.S)
_LANG = re.compile(r"<html[^>]*\blang=[\"']([a-zA-Z-]+)[\"']", re.I)
_META = re.compile(
    r"<meta\s+[^>]*?(?:name|property)=[\"']([^\"']+)[\"'][^>]*?content=[\"']([^\"']*)[\"']",
    re.I)
_META_REVERSED = re.compile(
    r"<meta\s+[^>]*?content=[\"']([^\"']*)[\"'][^>]*?(?:name|property)=[\"']([^\"']+)[\"']",
    re.I)
_HEADING = re.compile(r"<h([1-3])[^>]*>(.*?)</h\1>", re.I | re.S)


def read_site(url: str, user_agent: str) -> dict:
    """Fetches the product page and breaks it into the parts that say something."""
    result: dict[str, Any] = {
        "url": url, "reachable": False, "status": 0, "title": "", "description": "",
        "lang": "", "headings": [], "word_count": 0, "text": "", "meta": {}, "error": "",
    }
    if not url:
        result["error"] = i18n.message("analysis.no_url")
        return result

    try:
        status, raw = core.fetch(url, user_agent=user_agent, retries=2, timeout=20)
    except core.HttpError as error:
        result["error"] = str(error)
        return result

    result["status"] = status
    if status != 200 or not raw:
        result["error"] = i18n.message("analysis.warn.http", status=status)
        return result

    body = raw.decode("utf-8", "replace")
    result["reachable"] = True

    match = _TITLE.search(body)
    if match:
        result["title"] = _plain(match.group(1))[:200]

    match = _LANG.search(body)
    if match:
        result["lang"] = match.group(1).lower().split("-")[0]

    meta: dict[str, str] = {}
    for name, content in _META.findall(body):
        meta.setdefault(name.lower(), html.unescape(content).strip())
    for content, name in _META_REVERSED.findall(body):
        meta.setdefault(name.lower(), html.unescape(content).strip())
    result["meta"] = meta
    result["description"] = (meta.get("description") or meta.get("og:description") or "")[:600]

    result["headings"] = [_plain(text)[:160] for _level, text in _HEADING.findall(body)][:25]

    text = re.sub(r"<script.*?</script>|<style.*?</style>|<!--.*?-->", " ", body,
                  flags=re.I | re.S)
    text = html.unescape(_TAG.sub(" ", text))
    text = re.sub(r"\s+", " ", text).strip()
    result["text"] = text[:40000]
    result["word_count"] = len(text.split())
    return result


def _plain(fragment: str) -> str:
    return re.sub(r"\s+", " ", html.unescape(_TAG.sub(" ", fragment))).strip()


# ---------------------------------------------------------------------------
# Keywords
# ---------------------------------------------------------------------------

# Deliberately short: these are the words that top EVERY text and therefore say
# nothing about the product. Technical terms do not belong in here.
_STOPWORDS = {
    # German
    "aber", "alle", "allem", "allen", "aller", "alles", "als", "also", "am", "an",
    "auch", "auf", "aus", "bei", "bin", "bis", "bist", "da", "damit", "dann", "das",
    "dass", "dein", "deine", "dem", "den", "der", "des", "dessen", "dich", "die",
    "dies", "diese", "diesem", "diesen", "dieser", "dieses", "dir", "doch", "dort",
    "du", "durch", "ein", "eine", "einem", "einen", "einer", "eines", "er", "es",
    "euer", "eure", "fuer", "für", "gegen", "gewesen", "hab", "habe", "haben", "hat",
    "hatte", "hatten", "hier", "hin", "ich", "ihr", "ihre", "im", "in", "ins", "ist",
    "ja", "jede", "jedem", "jeden", "jeder", "jedes", "kann", "kein", "keine", "koennen",
    "können", "man", "mehr", "mein", "meine", "mit", "muss", "nach", "nicht", "nichts",
    "noch", "nun", "nur", "ob", "oder", "ohne", "schon", "sehr", "sein", "seine",
    "selbst", "sich", "sie", "sind", "so", "soll", "sollte", "sondern", "über", "ueber",
    "um", "und", "uns", "unser", "unter", "vom", "von", "vor", "war", "waren", "was",
    "wenn", "werden", "wie", "wieder", "wir", "wird", "wirst", "wo", "wurde", "zu",
    "zum", "zur", "zwar", "zwischen", "mehr", "alle", "beim", "seit", "etwa",
    # English
    "a", "about", "above", "after", "again", "all", "also", "am", "an", "and", "any",
    "are", "as", "at", "be", "because", "been", "before", "being", "below", "between",
    "both", "but", "by", "can", "did", "do", "does", "doing", "down", "during", "each",
    "few", "for", "from", "further", "had", "has", "have", "having", "he", "her",
    "here", "hers", "him", "his", "how", "i", "if", "in", "into", "is", "it", "its",
    "just", "me", "more", "most", "my", "no", "nor", "not", "now", "of", "off", "on",
    "once", "only", "or", "other", "our", "out", "over", "own", "same", "she", "should",
    "so", "some", "such", "than", "that", "the", "their", "them", "then", "there",
    "these", "they", "this", "those", "through", "to", "too", "under", "until", "up",
    "very", "was", "we", "were", "what", "when", "where", "which", "while", "who",
    "why", "will", "with", "would", "you", "your", "yours",
    # Web furniture that sits on every page
    "home", "startseite", "impressum", "datenschutz", "kontakt", "contact", "privacy",
    "cookie", "cookies", "menu", "menue", "login", "anmelden", "registrieren", "newsletter",
    "copyright", "rights", "reserved", "toggle", "skip", "content", "javascript",
}

_WORD = re.compile(r"[A-Za-zÀ-ÿ][A-Za-zÀ-ÿ0-9'-]{2,}")


def _tokens(text: str) -> list[str]:
    return [word.lower() for word in _WORD.findall(text or "")]


def extract_keywords(site: dict, product: dict, limit: int = 30) -> list[dict]:
    """Keyword candidates from page and profile, sorted by weight.

    Title, headings and meta description count for more than body text: what an author
    puts in a heading is the subject; what recurs in body text is often just filler.
    """
    weighted: Counter[str] = Counter()

    def feed(text: str, weight: float) -> None:
        words = [word for word in _tokens(text) if word not in _STOPWORDS and len(word) > 2]
        for word in words:
            weighted[word] += weight
        # Word pairs catch what means nothing alone ("system" + "care").
        for first, second in zip(words, words[1:]):
            weighted[f"{first} {second}"] += weight * 0.75

    feed(product.get("name", ""), 6.0)
    feed(product.get("one_liner", ""), 5.0)
    feed(product.get("description", ""), 3.0)
    feed(product.get("audience", ""), 3.0)
    feed(site.get("title", ""), 5.0)
    feed(site.get("description", ""), 4.0)
    feed(" ".join(site.get("headings", [])), 3.0)
    feed(site.get("meta", {}).get("keywords", ""), 3.0)
    feed(site.get("text", "")[:12000], 0.6)

    # The product name is not one of the audience's search terms - anyone who knows
    # it has already arrived. It drops out so the community search does not run dry.
    own = set(_tokens(product.get("name", "")))
    scored = [
        {"term": term, "score": round(score, 2), "source": "seite"}
        for term, score in weighted.most_common(limit * 4)
        if not (set(term.split()) <= own)
    ]

    # What the user entered always comes first - they know their own product.
    manual = [{"term": term.lower(), "score": 99.0, "source": "profil"}
              for term in product.get("keywords", [])]
    seen = {item["term"] for item in manual}
    merged = manual + [item for item in scored if item["term"] not in seen]
    return merged[:limit]


# ---------------------------------------------------------------------------
# Signals: guessing category and pricing off the page
# ---------------------------------------------------------------------------

# (category, weight, pattern). Multiple hits add up.
_CATEGORY_SIGNALS: list[tuple[str, float, re.Pattern[str]]] = [
    ("software_desktop", 3.0, re.compile(r"\.exe\b|\.msi\b|\.dmg\b|\.appimage\b|installer|setup herunterladen", re.I)),
    ("software_desktop", 2.0, re.compile(r"\b(windows|macos|mac os|linux)\b.{0,40}\b(download|herunterladen|version)\b", re.I)),
    ("software_desktop", 1.5, re.compile(r"systemvoraussetzungen|system requirements|portable version", re.I)),
    ("app_mobile", 3.0, re.compile(r"app\s?store|google\s?play|testflight|f-droid|\bapk\b", re.I)),
    ("app_mobile", 1.5, re.compile(r"\b(ios|android)\b.{0,30}\b(app|laden|download)\b", re.I)),
    ("game", 3.0, re.compile(r"\bsteam\b|itch\.io|epic games|wishlist|gameplay|early access", re.I)),
    ("game", 1.5, re.compile(r"\b(spieler|players|level|singleplayer|multiplayer)\b", re.I)),
    ("software_web", 2.5, re.compile(r"\b(kostenlos testen|free trial|start free|jetzt registrieren|sign up free)\b", re.I)),
    ("software_web", 2.0, re.compile(r"\b(dashboard|workspace|cloud|saas|self[- ]hosted)\b", re.I)),
    ("dev_tool", 3.0, re.compile(r"\b(npm install|pip install|cargo add|go get|docker pull)\b", re.I)),
    ("dev_tool", 2.0, re.compile(r"github\.com/|api[- ]dokumentation|api docs|sdk|endpoint|open source", re.I)),
    ("shop_physical", 3.5, re.compile(r"\b(warenkorb|in den warenkorb|add to cart|checkout|zur kasse)\b", re.I)),
    ("shop_physical", 2.0, re.compile(r"\b(versand|versandkosten|shipping|lieferzeit|r(ue|ü)cksendung|returns)\b", re.I)),
    ("content_site", 2.0, re.compile(r"\b(nachschlagewerk|enzyklop(ae|ä)die|encyclopedia|wiki|lexikon|artikel|blog)\b", re.I)),
    ("service", 2.5, re.compile(r"\b(beratung|dienstleistung|angebot anfordern|request a quote|termin vereinbaren|consulting)\b", re.I)),
    ("creative", 2.0, re.compile(r"\b(taschenbuch|paperback|h(oe|ö)rbuch|audiobook|album|soundtrack|onlinekurs|online course)\b", re.I)),
]

_PRICE_SIGNALS: list[tuple[str, float, re.Pattern[str]]] = [
    ("subscription", 3.0, re.compile(r"\b(pro monat|monatlich|per month|/mo\b|/month|j(ae|ä)hrlich|per year|abo|subscription)\b", re.I)),
    ("freemium", 3.0, re.compile(r"\b(kostenlos testen|free trial|free plan|kostenlose version|upgrade auf pro|pro version|premium)\b", re.I)),
    ("one_time", 2.5, re.compile(r"\b(einmalig|einmalzahlung|one[- ]time|lifetime|lizenz kaufen|buy (now|license))\b", re.I)),
    ("shop", 3.0, re.compile(r"\b(warenkorb|add to cart|zur kasse|checkout)\b", re.I)),
    ("ad_supported", 2.0, re.compile(r"\b(werbefinanziert|ad[- ]supported|adsense|werbung schalten)\b", re.I)),
    ("quote", 2.0, re.compile(r"\b(preis auf anfrage|angebot anfordern|request a quote|kontaktieren sie uns f(ue|ü)r)\b", re.I)),
    ("free", 2.0, re.compile(r"\b(v(oe|ö)llig kostenlos|komplett kostenlos|completely free|free forever|kein abo|no paywall|werbefrei)\b", re.I)),
]


def _guess(signals: list[tuple[str, float, re.Pattern[str]]], haystack: str,
           fallback: str) -> dict:
    scores: Counter[str] = Counter()
    reasons: list[dict] = []
    for key, weight, pattern in signals:
        match = pattern.search(haystack)
        if not match:
            continue
        scores[key] += weight
        if len(reasons) < 8:
            reasons.append({"key": key, "quote": _around(haystack, match.start(), match.end())})
    if not scores:
        return {"key": fallback, "confidence": 0.0, "reasons": [],
                "note_key": "analysis.no_signals"}
    best, best_score = scores.most_common(1)[0]
    total = sum(scores.values())
    return {
        "key": best,
        "confidence": round(best_score / total, 2),
        "reasons": [reason for reason in reasons if reason["key"] == best][:4],
        "note_key": "",
    }


def _around(text: str, start: int, end: int, pad: int = 70) -> str:
    left = max(0, start - pad)
    right = min(len(text), end + pad)
    return ("..." if left else "") + text[left:right].strip() + ("..." if right < len(text) else "")


# ---------------------------------------------------------------------------
# The whole analysis
# ---------------------------------------------------------------------------

def analyse(product: dict, config: dict, progress: Progress = _noop,
            use_api: bool | None = None) -> dict:
    """A complete analysis of a product profile. Does not raise - failures land as
    warnings in the result, so the interface always has something to show."""
    user_agent = config.get("user_agent", "MutexxAdvertiser/0.2")
    warnings: list[dict] = []

    progress("analysis.step.fetch", 0, 3)
    site = read_site(product.get("url", ""), user_agent)
    if not site["reachable"] and site["error"]:
        # The error is itself a message, so it stays switchable inside the warning.
        warnings.append(i18n.message("analysis.warn.unreachable", error=site["error"]))

    progress("analysis.step.keywords", 1, 3)
    haystack = " ".join([
        site.get("title", ""), site.get("description", ""),
        " ".join(site.get("headings", [])), site.get("text", "")[:20000],
        product.get("description", ""), product.get("one_liner", ""),
    ])
    keywords = extract_keywords(site, product)
    category = _guess(_CATEGORY_SIGNALS, haystack, product.get("category", "other"))
    price = _guess(_PRICE_SIGNALS, haystack, product.get("price_model", "free"))

    result: dict[str, Any] = {
        "product_slug": product.get("slug", ""),
        "generated_at": int(time.time()),
        "source": "profil" if not site["reachable"] else "seite",
        "site": {key: value for key, value in site.items() if key != "text"},
        "keywords": keywords,
        "category_guess": category,
        "price_guess": price,
        "audience_segments": [],
        "value_props": [],
        "positioning": "",
        "objections": [],
        "search_terms": [],
        "tone_hint": "",
        "warnings": warnings,
    }

    if use_api is None:
        use_api = bool((config.get("anthropic") or {}).get("api_key", "").strip())
    if use_api:
        progress("analysis.step.api", 2, 3)
        try:
            result.update(_analyse_with_api(product, site, keywords, config))
            result["source"] = "seite+ki" if site["reachable"] else "profil+ki"
        except Exception as error:  # noqa: BLE001 - the statistical part stays valid
            warnings.append(i18n.message("analysis.warn.api_failed", error=error))

    progress("analysis.step.done", 3, 3)
    result["warnings"] = warnings
    return result


_SYSTEM = """Du bist ein nuechterner Marketing-Analyst. Du bekommst ein Produktprofil
und den Text der Produktseite und leitest daraus ab, was sich VERKAUFEN laesst -
nicht, was der Hersteller gern haette.

Regeln:
- Erfinde nichts. Was nicht aus Profil oder Seitentext hervorgeht, laesst du weg.
- Keine Superlative, keine Agentursprache, keine Fuellsaetze.
- Suchbegriffe sind die Worte der ZIELGRUPPE, nicht die des Herstellers. Der
  Produktname selbst ist kein Suchbegriff.
- Einwaende sind echte Gruende, das Produkt NICHT zu nehmen. Sei unbequem.
- Antworte ausschliesslich als JSON, ohne Vorrede und ohne Codeblock.

Format:
{"audience_segments": [{"name": "...", "why": "...", "where": "..."}],
 "value_props": ["..."],
 "positioning": "ein bis zwei Saetze",
 "objections": ["..."],
 "search_terms": ["..."],
 "tone_hint": "ein Satz",
 "category": "einer der vorgegebenen Schluessel",
 "price_model": "einer der vorgegebenen Schluessel"}"""


def _analyse_with_api(product: dict, site: dict, keywords: list[dict], config: dict) -> dict:
    api = config.get("anthropic", {})
    key = (api.get("api_key") or "").strip()
    if not key:
        raise ValueError(i18n.t("error.no_api_key"))

    prompt = f"""PRODUKTPROFIL
Name: {product.get('name')}
URL: {product.get('url') or '(keine)'}
Version: {product.get('version') or '(keine)'}
Einzeiler: {product.get('one_liner') or '(keiner)'}
Beschreibung: {product.get('description') or '(keine)'}
Self-declared category: {products.category_label(product.get('category'))}
Self-declared pricing: {products.price_label(product.get('price_model'))}
Preis: {product.get('price_point') or '(nicht angegeben)'}
Zielgruppe laut Nutzer: {product.get('audience') or '(nicht angegeben)'}
Regionen: {', '.join(product.get('regions') or [])}
Sprachen: {', '.join(product.get('languages') or [])}
Monatsbudget: {product.get('budget_monthly_eur', 0)} EUR

PRODUKTSEITE
Erreichbar: {'ja' if site.get('reachable') else 'nein'}
Titel: {site.get('title') or '(keiner)'}
Meta-Beschreibung: {site.get('description') or '(keine)'}
Ueberschriften: {' | '.join(site.get('headings') or []) or '(keine)'}
Textauszug:
{(site.get('text') or '(nicht abrufbar)')[:9000]}

HAEUFIGSTE BEGRIFFE (statistisch, ungefiltert)
{', '.join(item['term'] for item in keywords[:25]) or '(keine)'}

ALLOWED CATEGORY KEYS: {', '.join(products.CATEGORIES)}
ALLOWED PRICING KEYS: {', '.join(products.PRICE_MODELS)}

Liefere 2 bis 4 Zielgruppensegmente, 3 bis 5 Nutzenversprechen, 3 bis 5 Einwaende
und 8 bis 15 Suchbegriffe."""

    status, raw = core.post_json(
        "https://api.anthropic.com/v1/messages",
        {
            "model": api.get("model") or "claude-opus-5",
            "max_tokens": 3000,
            "system": _SYSTEM,
            "messages": [{"role": "user", "content": prompt}],
        },
        user_agent=config.get("user_agent", "MutexxAdvertiser/0.2"),
        headers={"x-api-key": key, "anthropic-version": "2023-06-01"},
    )
    if status != 200:
        raise ValueError(i18n.t("error.api_status", status=status, detail=raw[:300]))

    payload = json.loads(raw)
    text = "".join(block.get("text", "") for block in payload.get("content", []))
    match = re.search(r"\{.*\}", text, re.S)
    if not match:
        raise ValueError(i18n.t("error.no_json"))
    parsed = json.loads(match.group(0))

    out: dict[str, Any] = {
        "audience_segments": _dicts(parsed.get("audience_segments"), ("name", "why", "where")),
        "value_props": _strings(parsed.get("value_props")),
        "positioning": str(parsed.get("positioning") or "").strip(),
        "objections": _strings(parsed.get("objections")),
        "search_terms": _strings(parsed.get("search_terms")),
        "tone_hint": str(parsed.get("tone_hint") or "").strip(),
    }
    # The model's category call only counts when it is a valid key - otherwise we
    # would rather keep guessing statistically.
    if parsed.get("category") in products.CATEGORIES:
        out["category_ai"] = parsed["category"]
    if parsed.get("price_model") in products.PRICE_MODELS:
        out["price_model_ai"] = parsed["price_model"]
    return out


def _strings(value: Any, limit: int = 20) -> list[str]:
    if not isinstance(value, list):
        return []
    return [str(item).strip() for item in value if str(item).strip()][:limit]


def _dicts(value: Any, fields: tuple[str, ...], limit: int = 8) -> list[dict]:
    if not isinstance(value, list):
        return []
    out = []
    for item in value[:limit]:
        if isinstance(item, dict):
            out.append({field: str(item.get(field) or "").strip() for field in fields})
        elif str(item).strip():
            out.append({fields[0]: str(item).strip(), **{f: "" for f in fields[1:]}})
    return out


# ---------------------------------------------------------------------------
# Storing and feeding back the result
# ---------------------------------------------------------------------------

def load(slug: str) -> dict:
    return core.load_product(slug, "analysis", {})


def store(slug: str, result: dict) -> None:
    core.save_product(slug, "analysis", result)


def merged_keywords(product: dict, result: dict, limit: int = 40) -> list[str]:
    """The keyword list the community search works from: what the user entered first,
    then the AI's search terms, then the statistical finds."""
    out: list[str] = []
    for term in product.get("keywords", []):
        if term.lower() not in out:
            out.append(term.lower())
    for term in result.get("search_terms", []):
        if term.lower() not in out:
            out.append(term.lower())
    for item in result.get("keywords", []):
        term = item.get("term", "").lower()
        if term and term not in out:
            out.append(term)
    return out[:limit]
