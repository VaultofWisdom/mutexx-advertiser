"""
Drafts: writes a separate post for every community - never the same text twice.

Everything in a draft comes from the product profile and the analysis. There is no
built-in product text any more; the templates are scaffolding, not content.

Two modes:
  * templates (default, offline, free) - varies angle, title and body from profile,
    analysis and community data.
  * Anthropic API (optional) - writes the draft freely from profile, analysis,
    community description and rules.

The principle in every template: value first, link second. A post that would still be
worth something without the link does not read as spam - and that is exactly the
difference between growth and a banned domain.
"""

from __future__ import annotations

import random
import re
from typing import Any

from . import core, i18n, products, rules

# Translation keys - see i18n.py.
ANGLES = {
    "resource": "angle.resource",
    "feedback": "angle.feedback",
    "showcase": "angle.showcase",
    "question": "angle.question",
    "forum_intro": "angle.forum_intro",
}


# ---------------------------------------------------------------------------
# Templates
#
# The placeholders are filled in _fields() and are ALWAYS set - with a fallback phrase
# if need be. A template must never produce an empty sentence.
# ---------------------------------------------------------------------------

_TEMPLATES: dict[str, dict[str, dict[str, Any]]] = {
    "de": {
        "resource": {
            "titles": [
                "{name} - {one_liner}",
                "Ich habe {name} gebaut: {one_liner}",
                "{topic_title}: {name} - {one_liner_lower_short}",
            ],
            "body": """Ich arbeite seit einer Weile an {name} ({url}) - {one_liner_lower}

{benefits}

{why_built}

{price_line}{version_line}

{closing}""",
        },
        "feedback": {
            "titles": [
                "{name}: wo liegt der Denkfehler?",
                "Bitte zerlegt {name} - ich suche die Schwachstellen",
                "Feedback erbeten zu {name} ({topic})",
            ],
            "body": """Ich habe {name} ({url}) gebaut - {one_liner_lower}

{benefits}

Was ich allein nicht prüfen kann, ist die Praxis. Ihr arbeitet täglich mit {topic},
und ich hätte lieber jetzt Widerspruch als in einem Jahr einen Fehler, den alle
mitschleppen.

Wenn ihr fünf Minuten habt: sucht euch die Stelle, die euch am dünnsten vorkommt,
und sagt mir, was daran nicht stimmt. Deutlich ist willkommen.

{closing}""",
        },
        "showcase": {
            "titles": [
                "{name} - {one_liner}",
                "Projektvorstellung: {name}",
                "{topic_title}: {name}, {one_liner_lower_short}",
            ],
            "body": """{name} ({url}) ist {one_liner_lower}

{benefits}

{why_built}

{price_line}{version_line}

{closing}""",
        },
        "question": {
            "titles": [
                "{topic_title}: welcher Weg hat sich bei euch bewährt?",
                "Frage aus der Praxis zu {topic}",
                "Ein Einwand, an dem ich hänge - wie seht ihr das?",
            ],
            "body": """Ein Punkt, an dem ich beim Bauen dauernd hänge:

{pain}

{context}

Wie handhabt ihr das? Ich habe für mich einen Weg gewählt und ihn in {name} ({url})
umgesetzt, bin mir aber nicht sicher, dass es der richtige ist.

{closing}""",
        },
        "forum_intro": {
            "titles": [
                "Vorstellung - und ein Projekt, an dem ich sitze",
                "Neu hier, dazu {name}",
            ],
            "body": """Hallo zusammen - lange mitgelesen, erster Beitrag.

Ich baue {name} ({url}), {one_liner_lower}

{benefits}

Ich bin vor allem hier, um mitzulesen und dazuzulernen. Falls ein Link auf das eigene
Projekt hier nicht gern gesehen ist, sagt Bescheid, dann nehme ich ihn raus.

{closing}""",
        },
    },
    "en": {
        "resource": {
            "titles": [
                "{name} - {one_liner}",
                "I built {name}: {one_liner}",
                "{topic_title}: {name} - {one_liner_lower_short}",
            ],
            "body": """I have been working on {name} ({url}) for a while - {one_liner_lower}

{benefits}

{why_built}

{price_line}{version_line}

{closing}""",
        },
        "feedback": {
            "titles": [
                "{name}: where did I get this wrong?",
                "Please tear {name} apart - I am looking for the weak spots",
                "Looking for feedback on {name} ({topic})",
            ],
            "body": """I built {name} ({url}) - {one_liner_lower}

{benefits}

The part I cannot check on my own is practice. You work with {topic} every day, and I
would rather be contradicted now than keep an error in there for a year.

If you have five minutes: pick whatever looks thinnest to you and tell me what is wrong
with it. Blunt is fine.

{closing}""",
        },
        "showcase": {
            "titles": [
                "{name} - {one_liner}",
                "Project showcase: {name}",
                "{topic_title}: {name}, {one_liner_lower_short}",
            ],
            "body": """{name} ({url}) is {one_liner_lower}

{benefits}

{why_built}

{price_line}{version_line}

{closing}""",
        },
        "question": {
            "titles": [
                "{topic_title}: which approach has actually worked for you?",
                "A practical question about {topic}",
                "An objection I keep running into - how do you see it?",
            ],
            "body": """Something I keep running into while building:

{pain}

{context}

How do you handle this? I picked one way and built it into {name} ({url}), but I am not
convinced it is the right one.

{closing}""",
        },
        "forum_intro": {
            "titles": [
                "Introduction - and a project I have been working on",
                "New here, plus {name}",
            ],
            "body": """Hello everyone - long-time reader, first post.

I build {name} ({url}), {one_liner_lower}

{benefits}

I am mainly here to read and learn. If linking your own project is not welcome here,
say so and I will edit the link out.

{closing}""",
        },
    },
}

_CLOSINGS = {
    "de": [
        "Fragen zu Aufbau oder Vorgehen beantworte ich gern in den Kommentaren.",
        "Wenn euch eine Stelle zu dünn vorkommt, sagt welche - die nehme ich mir als nächstes vor.",
        "Korrekturen und Hinweise sind mir mehr wert als Zustimmung.",
        "Ich lese jeden Kommentar - wenn etwas nicht stimmt, höre ich das lieber hier.",
    ],
    "en": [
        "Happy to answer anything about how it works in the comments.",
        "If something looks thin to you, say which part and I will take that on next.",
        "Corrections and pointers are worth more to me than upvotes.",
        "I read every comment - if something is off, I would rather hear it here.",
    ],
}

_PRICE_LINE = {
    "de": {
        "free": "Kostenlos, ohne Konto, ohne Werbung.",
        "freemium": "Der Grundumfang ist kostenlos, eine Bezahlversion gibt es zusätzlich.",
        "one_time": "Einmalkauf{price}, kein Abo.",
        "subscription": "Als Abo{price}.",
        "ad_supported": "Kostenlos nutzbar, finanziert über Werbung.",
        "shop": "Direkt bestellbar{price}.",
        "quote": "Preis auf Anfrage.",
    },
    "en": {
        "free": "Free, no account, no ads.",
        "freemium": "The core is free, there is a paid version on top.",
        "one_time": "One-time purchase{price}, no subscription.",
        "subscription": "Available as a subscription{price}.",
        "ad_supported": "Free to use, funded by ads.",
        "shop": "Available to order{price}.",
        "quote": "Price on request.",
    },
}

_WHY_BUILT = {
    "de": "Entstanden ist es, weil ich das, was ich brauchte, nirgends in dieser Form gefunden habe.",
    "en": "It exists because the thing I needed did not exist in this form anywhere.",
}

_VERSION_LINE = {"de": " Aktuell ist Version {version}.", "en": " Version {version} is current."}

_FALLBACK_ONE_LINER = {
    "de": "ein Werkzeug, das eine Sache erledigt und dabei nicht im Weg steht",
    "en": "a tool that does one job and stays out of the way",
}

_FALLBACK_PAIN = {
    "de": "Die vorhandenen Lösungen wollen entweder zu viel oder können zu wenig.",
    "en": "The existing options either do too much or not enough.",
}


# ---------------------------------------------------------------------------
# Filling the fields
# ---------------------------------------------------------------------------

def community_language(entry: dict) -> str:
    """The target community's language, as far as name and address reveal it."""
    haystack = " ".join(str(entry.get(field) or "") for field in
                        ("name", "handle", "url", "title", "description")).lower()
    if re.search(r"\.de/|\.de$|\.at/|\.ch/|deutsch|german|\bgermany\b", haystack):
        return "de"
    return "en"


def _language_for(entry: dict, product: dict) -> tuple[str, str]:
    """The draft's language - and the warning if it does not match the community.

    Templates cannot translate. The one-liner and the description sit in the profile in
    exactly one language; dropping them into an English frame yields a half-German post.
    So a template draft follows the PRODUCT's language and says openly when the
    community speaks a different one.
    """
    wanted = community_language(entry)
    available = [lang for lang in (product.get("languages") or ["de"]) if lang in _TEMPLATES]
    if not available:
        available = ["de"]
    if wanted in available:
        return wanted, ""

    chosen = available[0]
    return chosen, i18n.message(
        "draft.language_warning",
        community_language=i18n.message("language." + wanted),
        product_language=i18n.message("language." + chosen),
    )


def _sentences(text: str, count: int = 2) -> str:
    parts = re.split(r"(?<=[.!?])\s+", (text or "").strip())
    return " ".join(part for part in parts[:count] if part).strip()


def _lower_first(text: str) -> str:
    text = (text or "").strip()
    if not text:
        return ""
    # Lower-case the first letter only, and only when a second capital does not
    # follow - otherwise "PDF tool" becomes "pDF tool".
    if len(text) > 1 and text[1].isupper():
        return text
    return text[0].lower() + text[1:]


def _strip_period(text: str) -> str:
    return (text or "").strip().rstrip(".").strip()


def _topic_for(entry: dict, product: dict, analysis_result: dict, language: str) -> str:
    """The subject the community will file the product under.

    Prefers a keyword that occurs in both the product and the community - that is the
    bridge a post hangs on. Otherwise the product's own umbrella term.
    """
    haystack = " ".join(str(entry.get(field) or "") for field in
                        ("name", "title", "description", "sidebar")).lower()
    candidates = [item.get("term", "") for item in analysis_result.get("keywords", [])]
    candidates += [term.lower() for term in product.get("keywords", [])]
    for term in candidates:
        if term and len(term) > 3 and term in haystack:
            return term
    for term in candidates:
        if term and len(term) > 3:
            return term
    label = products.CATEGORIES.get(product.get("category", "other"), "")
    if language == "de" and label:
        return label.split(" (")[0].lower()
    return "this" if language == "en" else "das Thema"


def _pain_for(product: dict, analysis_result: dict, language: str) -> str:
    """The problem the post starts from. Objections out of the analysis serve best -
    they are the reason anyone is searching in the first place."""
    for source in (analysis_result.get("objections", []), analysis_result.get("value_props", [])):
        for item in source:
            cleaned = (item or "").strip()
            if 12 < len(cleaned) < 200:
                # It stands as its own sentence - capital and full stop stay.
                return cleaned if cleaned.endswith((".", "?", "!")) else cleaned + "."
    return _FALLBACK_PAIN[language]


def _benefits(product: dict, analysis_result: dict, language: str) -> str:
    """The value points as a list. They come from the analysis; without it the product
    description is used, and without that the block stays empty - better no paragraph
    than an empty one."""
    props = [_strip_period(prop) for prop in analysis_result.get("value_props", []) if prop.strip()]
    if props:
        return "\n".join(f"* {prop}" for prop in props[:5])
    description = _sentences(product.get("description", ""), 3)
    if description:
        return description
    return ""


def _fields(entry: dict, product: dict, analysis_result: dict, language: str,
            rng: random.Random) -> dict[str, str]:
    one_liner = product.get("one_liner", "").strip() or _sentences(product.get("description", ""), 1)
    one_liner = _strip_period(one_liner) or _FALLBACK_ONE_LINER[language]

    price_model = product.get("price_model", "free")
    price_point = product.get("price_point", "").strip()
    price_line = _PRICE_LINE[language].get(price_model, "").format(
        price=f" ({price_point})" if price_point else "")

    version = product.get("version", "").strip()
    version_line = _VERSION_LINE[language].format(version=version) if version else ""

    audience = product.get("audience", "").strip()
    context_parts = [part for part in (
        _sentences(product.get("description", ""), 2),
        f"Zielgruppe: {audience}" if audience and language == "de" else
        (f"Who it is for: {audience}" if audience else ""),
    ) if part]

    topic = _topic_for(entry, product, analysis_result, language)
    one_liner_lower = _lower_first(one_liner)

    return {
        "name": product.get("name", "").strip() or "das Projekt",
        "url": product.get("url", "").strip() or "(noch keine Adresse hinterlegt)",
        "version": version,
        "one_liner": one_liner,
        "one_liner_lower": one_liner_lower + ".",
        # For titles: no full stop and trimmed, so the line does not run away.
        "one_liner_lower_short": one_liner_lower[:80].rstrip(" ,-"),
        "topic": topic,
        "topic_title": topic[:1].upper() + topic[1:],
        "pain": _pain_for(product, analysis_result, language),
        "benefits": _benefits(product, analysis_result, language),
        "why_built": _WHY_BUILT[language],
        "price_line": price_line,
        "version_line": version_line,
        "context": "\n\n".join(context_parts),
        "closing": rng.choice(_CLOSINGS[language]),
    }


def _tidy(text: str) -> str:
    """Clears up the gaps that placeholders left empty leave behind."""
    text = re.sub(r"[ \t]+\n", "\n", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


# ---------------------------------------------------------------------------
# Choosing the angle
# ---------------------------------------------------------------------------

def pick_angle(entry: dict, product: dict | None = None) -> str:
    analysis = entry.get("analysis", {})
    labels = analysis.get("labels", [])
    name = entry.get("handle", "").lower()

    if entry.get("platform") == "forum":
        return "forum_intro"
    if any(tag in name for tag in ("sideproject", "webdev", "internetisbeautiful",
                                   "coolgithubprojects", "somebodymakethis", "opensource")):
        return "showcase"
    if "Ratio-Regel (erst beitragen, dann teilen)" in labels:
        return "question"
    if analysis.get("verdict") == rules.CONDITIONAL:
        return "feedback"
    if entry.get("subscribers", 0) > 300_000:
        return "feedback"
    return "resource"


# Which rule turns into which instruction. Both sides are translation keys: the
# checklist has to read in the operator's language, whatever language the post is in.
_REQUIREMENT_FOR = {
    "rule.ratio": "requirement.ratio",
    "rule.megathread": "requirement.megathread",
    "rule.mod_approval": "requirement.mod_approval",
    "rule.flair": "requirement.flair",
    "rule.text_only": "requirement.text_only",
    "rule.karma": "requirement.karma",
    "rule.no_monetisation": "requirement.no_monetisation",
    "rule.spam_ban": "requirement.spam_ban",
}


def _requirements(entry: dict) -> list[str]:
    """The conditions as a checklist - the part everyone forgets. Returns keys."""
    checklist: list[str] = []
    for label in entry.get("analysis", {}).get("labels", []):
        requirement = _REQUIREMENT_FOR.get(label)
        if requirement and requirement not in checklist:
            checklist.append(requirement)
    if entry.get("over18"):
        checklist.append("requirement.nsfw")
    if not checklist:
        checklist.append("requirement.read_rules")
    return checklist


# ---------------------------------------------------------------------------
# Template draft
# ---------------------------------------------------------------------------

def build(entry: dict, product: dict, analysis_result: dict | None = None,
          angle: str | None = None, seed: int | None = None,
          language: str | None = None) -> dict:
    analysis_result = analysis_result or {}
    angle = angle if angle in ANGLES else pick_angle(entry, product)
    if language in _TEMPLATES:
        warning = ""
    else:
        language, warning = _language_for(entry, product)
    rng = random.Random(seed if seed is not None else hash(entry.get("id", "")) & 0xFFFF)

    fields = _fields(entry, product, analysis_result, language, rng)
    template = _TEMPLATES[language][angle]
    title = _tidy(rng.choice(template["titles"]).format(**fields))
    body = _tidy(template["body"].format(**fields))

    if entry.get("analysis", {}).get("verdict") == rules.FORBIDDEN:
        # The banner sits inside the post text, so it follows the DRAFT language -
        # you read it in the same place you would paste the post.
        body = i18n.t("draft.forbidden_banner", language) + "\n\n" + body

    draft = {
        "community_id": entry.get("id", ""),
        "community": entry.get("name", ""),
        "platform": entry.get("platform", "reddit"),
        "product_slug": product.get("slug", ""),
        "angle": angle,
        "angle_label": ANGLES[angle],
        "language": language,
        "community_language": community_language(entry),
        "title": title,
        "body": body,
        "requirements": _requirements(entry),
        "generated_by": "vorlage",
    }
    if warning:
        draft["warning"] = warning
    return draft


# ---------------------------------------------------------------------------
# Optional: real AI drafts through the Anthropic API
# ---------------------------------------------------------------------------

_SYSTEM = """You write a post for a community in which a product is to be introduced.
Rules:
- Value first, link second. The post has to be worth reading without the link.
- No marketing tone, no superlatives, no emoji, no exclamation marks.
- A respectful, matter-of-fact tone towards the community. No lecturing, no mockery,
  and no ingratiation either.
- Tailor it to this specific community: pick up its subject and its language.
- Follow the stated community rules strictly.
- Invent no properties of the product. What is not in the profile does not exist.
Answer only as JSON: {"title": "...", "body": "..."}"""


def build_with_api(entry: dict, product: dict, config: dict,
                   analysis_result: dict | None = None, angle: str | None = None,
                   language: str | None = None) -> dict:
    if not core.ai_ready(config):
        raise ValueError(i18n.t("error.no_api_key"))

    analysis_result = analysis_result or {}
    angle = angle if angle in ANGLES else pick_angle(entry, product)
    # The API can translate - so here the community's language applies.
    language = language if language in _TEMPLATES else community_language(entry)
    entry_analysis = entry.get("analysis", {})
    rule_text = "\n".join(f"- {rule.get('name','')}: {str(rule.get('text',''))[:300]}"
                          for rule in entry.get("rules", [])[:12])

    prompt = f"""COMMUNITY
Name: {entry.get('name')} ({entry.get('platform')})
Beschreibung: {entry.get('title','')} - {str(entry.get('description',''))[:800]}
Mitglieder: {entry.get('subscribers', 0)}
Rule assessment: {i18n.t(rules.VERDICT_TEXT.get(entry_analysis.get('verdict'), 'verdict.grau'), language)}
Conditions detected: {', '.join(i18n.t(l, language) for l in entry_analysis.get('labels', [])) or 'none'}
Regeln im Original:
{rule_text or '(keine abrufbar)'}

PRODUKT
Name: {product.get('name')}
URL: {product.get('url') or '(keine)'}
Version: {product.get('version') or '(keine)'}
Einzeiler: {product.get('one_liner') or '(keiner)'}
Beschreibung: {str(product.get('description') or '(keine)')[:1500]}
Category: {products.category_label(product.get('category'), language)}
Pricing: {products.price_label(product.get('price_model'), language)}
Preis: {product.get('price_point') or '(nicht angegeben)'}
Zielgruppe: {product.get('audience') or '(nicht angegeben)'}
Tone: {products.tone_label(product.get('tone'), language)}

ANALYSE
Positionierung: {analysis_result.get('positioning') or '(keine)'}
Nutzenversprechen: {'; '.join(analysis_result.get('value_props') or []) or '(keine)'}
Zu erwartende Einwände: {'; '.join(analysis_result.get('objections') or []) or '(keine)'}

Angle: {i18n.t(ANGLES[angle], language)}
Sprache des Beitrags: {'Deutsch' if language == 'de' else 'Englisch'}
Länge: 120 bis 220 Wörter."""

    parsed = core.ask_ai_json(config, _SYSTEM, prompt)

    draft = build(entry, product, analysis_result, angle, language=language)
    draft.update({
        "title": str(parsed.get("title") or draft["title"]).strip(),
        "body": str(parsed.get("body") or draft["body"]).strip(),
        "generated_by": core.ai_source(config),
    })
    return draft
