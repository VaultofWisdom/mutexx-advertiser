"""
Entwuerfe: erzeugt fuer jede Community einen eigenen Post - nie denselben Text zweimal.

Zwei Betriebsarten:
  * Vorlagen (Standard, offline, kostenlos) - variiert Blickwinkel, Titel und Text
    anhand der Community-Daten.
  * Anthropic-API (optional, wenn ein Schluessel hinterlegt ist) - schreibt den
    Entwurf frei auf Basis von Communitybeschreibung und Regeln.

Der Grundsatz in allen Vorlagen: zuerst Nutzen, dann Link. Ein Beitrag, der ohne
den Link noch wertvoll waere, wird nicht als Spam gelesen - und genau das ist der
Unterschied zwischen Wachstum und Domain-Sperre.
"""

from __future__ import annotations

import json
import random
import re

from . import core, rules

ANGLES = {
    "resource": "Ressource teilen",
    "feedback": "Um Korrekturen bitten",
    "showcase": "Projekt vorstellen",
    "question": "Fachfrage mit Kontext",
    "forum_intro": "Forum-Vorstellung",
}


# ---------------------------------------------------------------------------
# Vorlagen (Englisch - das ist die Sprache fast aller Zielcommunities)
# ---------------------------------------------------------------------------

_TITLES = {
    "resource": [
        "I compiled a free, ad-free reference on the {topic} - sigils, enns and sourced entries",
        "A free encyclopedia of the Ars Goetia, the Seven Princes and the Nine Divinities",
        "Free {topic} reference: 72 Goetic spirits with seals, enns and full entries",
    ],
    "feedback": [
        "I wrote long-form entries on the 72 Goetic spirits - where did I get it wrong?",
        "Looking for corrections: my write-ups on the Seven Princes and Nine Divinities",
        "Practitioners of this sub: please tear my {topic} entries apart",
    ],
    "showcase": [
        "I built a free demonology encyclopedia - no ads, no paywall, no account needed",
        "Two years of writing: a searchable reference for {topic}",
    ],
    "question": [
        "How do you handle conflicting manuscript sources on the same spirit?",
        "Which grimoire do you treat as canonical when the Goetia and the Pseudomonarchia disagree?",
    ],
    "forum_intro": [
        "Introduction - and a free reference I have been building",
    ],
}

_BODIES = {
    "resource": """Over the past while I have been putting together {site} ({url}) - a free,
ad-free reference for {topic}. It covers the Nine Divinities, the Seven Princes and all 72
spirits of the Ars Goetia, each with the traditional seal, the enn where one is attested, and
a long-form entry on manuscript origins, reported appearance, domains and traditional
correspondences.

I wrote it because most of what is online is either a two-line copy of the same Mathers
translation or hidden behind a paywall. Everything is written from scratch after reading
several sources side by side, and where traditions disagree I say so instead of picking one
silently.

No account, no ads, no tracking, nothing for sale. Version {version} just went live.

{closing}""",

    "feedback": """I have spent a long time writing long-form entries on the Goetic spirits and
the Seven Princes for {site} ({url}) - manuscript origins, reported appearance, domains,
correspondences, and the enns where they are attested.

The part I cannot check on my own is practice. I have read the sources, but this sub has
people with actual working experience, and I would rather be corrected now than keep an error
online for years.

If you have five minutes, pick any spirit you know well and tell me what is wrong, thin or
missing. Blunt is fine - I will fix it and credit the correction.

{closing}""",

    "showcase": """{site} ({url}) is a searchable encyclopedia of {topic}: Nine Divinities,
Seven Princes and the 72 Goetic spirits, each with seal, enn and a full entry.

Built as React and TypeScript on Vite with Supabase behind it. No ads, no accounts, no paywall -
it exists because the reference I wanted did not exist. Version {version} is live now.

{closing}""",

    "question": """Something I keep running into while writing reference entries: the Ars Goetia,
the Pseudomonarchia Daemonum and the Munich manual regularly disagree on rank, legions and
even the name of the same spirit.

How do you handle that in your own practice - do you follow one manuscript, average across
them, or treat each tradition as its own thing?

I have been documenting both readings side by side rather than silently picking one, over at
{site} ({url}), but I am genuinely unsure that is the right call.

{closing}""",

    "forum_intro": """Hello everyone - long-time reader, first post.

I have been building {site} ({url}), a free reference on {topic}: the Nine Divinities, the
Seven Princes and the 72 spirits of the Ars Goetia, each with seal, enn and a long-form entry
on origins, appearance, domains and correspondences.

I am here mainly to read and learn, and to have my entries corrected by people who actually
work with this material. If linking the project is not welcome here, tell me and I will edit
the link out - no hard feelings.

{closing}""",
}

_CLOSINGS = [
    "Happy to answer anything about sources or methodology in the comments.",
    "If a specific entry looks thin to you, say which one and I will expand it next.",
    "Corrections and source pointers are more useful to me than upvotes.",
    "I read every comment - if something is off, I would rather hear it here.",
]

_TOPIC_BY_HINT = [
    ("demonolatry", "demonolatry"),
    ("goet", "the Ars Goetia"),
    ("satan", "the infernal divine"),
    ("lucifer", "the infernal divine"),
    ("witch", "spirit work and traditional correspondences"),
    ("grimoire", "grimoire tradition"),
    ("magick", "ceremonial and grimoire tradition"),
    ("occult", "demonology and the grimoire tradition"),
    ("folklore", "demonic figures in folklore"),
    ("mythol", "demonic figures in myth"),
]


def _topic_for(entry: dict) -> str:
    haystack = f"{entry.get('name','')} {entry.get('title','')} {entry.get('description','')}".lower()
    for hint, topic in _TOPIC_BY_HINT:
        if hint in haystack:
            return topic
    return "demonology"


def pick_angle(entry: dict) -> str:
    analysis = entry.get("analysis", {})
    labels = analysis.get("labels", [])
    name = entry.get("handle", "").lower()

    if entry.get("platform") == "forum":
        return "forum_intro"
    if any(tag in name for tag in ("sideproject", "webdev", "internetisbeautiful",
                                   "coolgithubprojects", "somebodymakethis")):
        return "showcase"
    if "Ratio-Regel (erst beitragen, dann teilen)" in labels:
        return "question"
    if analysis.get("verdict") == rules.CONDITIONAL:
        return "feedback"
    if entry.get("subscribers", 0) > 300_000:
        return "feedback"
    return "resource"


def _requirements(entry: dict) -> list[str]:
    """Konkrete Auflagen als Checkliste - das ist der Teil, den man sonst vergisst."""
    labels = entry.get("analysis", {}).get("labels", [])
    checklist: list[str] = []
    mapping = {
        "Ratio-Regel (erst beitragen, dann teilen)":
            "Vorher mindestens 5-10 echte Kommentare in dieser Community schreiben.",
        "Nur im Sammel-/Wochen-Thread":
            "NUR im Sammel-/Wochenthread posten - eigenen Thread vermeiden.",
        "Vorherige Mod-Freigabe noetig":
            "Vorher die Moderation anschreiben und Freigabe abwarten.",
        "Flair erforderlich":
            "Beim Posten das passende Flair setzen, sonst wird der Beitrag entfernt.",
        "Nur Text-Posts erlaubt":
            "Als Textbeitrag posten, Link erst im Fliesstext.",
        "Mindest-Karma / Kontoalter":
            "Karma-/Kontoalter-Anforderung pruefen, ggf. Account erst reifen lassen.",
        "Keine Umfragen/Monetarisierung":
            "Keinen Hinweis auf Monetarisierung, Patreon o.ae. einbauen.",
        "Allgemeines Spam-Verbot":
            "Beitrag muss auch ohne den Link lesenswert sein - sonst wird er entfernt.",
    }
    for label in labels:
        if label in mapping:
            checklist.append(mapping[label])
    if entry.get("over18"):
        checklist.append("NSFW-Community: Beitrag ggf. als NSFW markieren.")
    if not checklist:
        checklist.append("Regeln in der Sidebar vor dem Posten selbst gegenlesen.")
    return checklist


def build(entry: dict, config: dict, angle: str | None = None, seed: int | None = None) -> dict:
    site = config["site"]
    angle = angle or pick_angle(entry)
    rng = random.Random(seed if seed is not None else hash(entry["id"]) & 0xFFFF)

    fields = {
        "site": site["name"],
        "url": site["url"],
        "version": site["version"],
        "topic": _topic_for(entry),
        "closing": rng.choice(_CLOSINGS),
    }
    title = rng.choice(_TITLES[angle]).format(**fields)
    body = _BODIES[angle].format(**fields).strip()

    if entry.get("analysis", {}).get("verdict") == rules.FORBIDDEN:
        body = ("### Diese Community verbietet Eigenwerbung. Der Entwurf ist nur zur Ansicht "
                "erzeugt worden - hier bitte NICHT posten.\n\n") + body

    return {
        "community_id": entry["id"],
        "community": entry["name"],
        "platform": entry.get("platform", "reddit"),
        "angle": angle,
        "angle_label": ANGLES[angle],
        "title": title,
        "body": body,
        "requirements": _requirements(entry),
        "generated_by": "vorlage",
    }


# ---------------------------------------------------------------------------
# Optional: echte KI-Entwuerfe ueber die Anthropic-API
# ---------------------------------------------------------------------------

_SYSTEM = """Du schreibst Community-Beitraege fuer ein kostenloses, werbefreies
Daemonologie-Nachschlagewerk. Regeln:
- Zuerst Nutzen, dann Link. Der Beitrag muss auch ohne den Link lesenswert sein.
- Kein Marketing-Ton, keine Superlative, keine Emojis, keine Ausrufezeichen.
- Respektvoller, sachlicher Ton gegenueber der Praxis der Community. Keine Belehrung,
  kein Spott, aber auch keine Anbiederung.
- Auf die konkrete Community zuschneiden: greife ihr Thema und ihre Sprache auf.
- Halte dich strikt an die genannten Community-Regeln.
- Erfinde keine Fakten ueber die Website.
Antworte ausschliesslich als JSON: {"title": "...", "body": "..."}"""


def build_with_api(entry: dict, config: dict, angle: str | None = None) -> dict:
    api = config.get("anthropic", {})
    key = (api.get("api_key") or "").strip()
    if not key:
        raise ValueError("Kein Anthropic-API-Schluessel hinterlegt.")

    angle = angle or pick_angle(entry)
    site = config["site"]
    analysis = entry.get("analysis", {})
    rule_text = "\n".join(f"- {r['name']}: {r['text'][:300]}" for r in entry.get("rules", [])[:12])

    prompt = f"""Community: {entry['name']} ({entry.get('platform')})
Beschreibung: {entry.get('title','')} - {entry.get('description','')[:800]}
Mitglieder: {entry.get('subscribers', 0)}
Regel-Einschaetzung: {rules.VERDICT_TEXT.get(analysis.get('verdict'), 'unbekannt')}
Erkannte Auflagen: {', '.join(analysis.get('labels', [])) or 'keine'}
Regeln im Original:
{rule_text or '(keine abrufbar)'}

Website: {site['name']} - {site['url']} (Version {site['version']})
Kurzbeschreibung: {site['one_liner']}

Gewuenschter Blickwinkel: {ANGLES[angle]}
Sprache des Beitrags: Englisch, ausser die Community ist erkennbar deutschsprachig.
Laenge: 120 bis 220 Woerter."""

    status, raw = core.post_json(
        "https://api.anthropic.com/v1/messages",
        {
            "model": api.get("model") or "claude-opus-5",
            "max_tokens": 1200,
            "system": _SYSTEM,
            "messages": [{"role": "user", "content": prompt}],
        },
        user_agent=config["user_agent"],
        headers={"x-api-key": key, "anthropic-version": "2023-06-01"},
    )
    if status != 200:
        raise ValueError(f"Anthropic-API antwortete mit {status}: {raw[:300]}")

    payload = json.loads(raw)
    text = "".join(block.get("text", "") for block in payload.get("content", []))
    match = re.search(r"\{.*\}", text, re.S)
    if not match:
        raise ValueError("Antwort der API enthielt kein verwertbares JSON.")
    parsed = json.loads(match.group(0))

    draft = build(entry, config, angle)
    draft.update({
        "title": parsed.get("title", draft["title"]),
        "body": parsed.get("body", draft["body"]),
        "generated_by": "anthropic",
    })
    return draft
