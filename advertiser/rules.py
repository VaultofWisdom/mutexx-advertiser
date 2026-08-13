"""
Regel-Analyse: liest die Regeltexte einer Community und leitet daraus ab,
ob und unter welchen Bedingungen ein eigener Link dort ueberhaupt erwuenscht ist.

WICHTIG: Das ist eine Heuristik, kein Ersatz fuers Selberlesen. Die App zeigt
deshalb bei jeder Community die Originaltexte der ausschlaggebenden Regeln mit an.
"""

from __future__ import annotations

import re

# Verdikt-Stufen
FORBIDDEN = "rot"       # Eigenwerbung ausdruecklich verboten -> niemals posten
CONDITIONAL = "gelb"    # Erlaubt, aber mit Auflagen (Ratio, Flair, Thread, Mod-Freigabe)
OPEN = "gruen"          # Kein Promo-Verbot gefunden -> trotzdem hoeflich und wertig posten
UNKNOWN = "grau"        # Regeln nicht abrufbar


_PATTERNS: list[tuple[str, str, re.Pattern[str]]] = [
    # (Verdikt-Beitrag, Label, Muster)
    (FORBIDDEN, "Eigenwerbung verboten", re.compile(
        r"no\s+(self[\s-]?promo\w*|advertis\w+|promotion|soliciting|shilling)"
        r"|self[\s-]?promo\w*\s+(is\s+)?(not\s+allowed|prohibited|banned|forbidden)"
        r"|keine\s+(eigen)?werbung|werbung\s+(ist\s+)?(verboten|untersagt|nicht\s+erlaubt)"
        r"|advertising\s+(is\s+)?(not\s+allowed|prohibited|banned)", re.I)),
    (FORBIDDEN, "Keine Links zu eigenen Projekten", re.compile(
        r"no\s+(links?\s+to\s+your\s+own|blog\s?spam|blogspam|personal\s+(blogs?|websites?|projects?))"
        r"|do\s+not\s+(post|link)\s+your\s+(own\s+)?(site|website|blog|app|project)", re.I)),
    # "No spam" steht in fast jeder Regelliste und meint selten ein Werbeverbot.
    # Deshalb nur eine Auflage, kein rotes Verdikt - sonst faellt die halbe Liste raus.
    (CONDITIONAL, "Allgemeines Spam-Verbot", re.compile(
        r"no\s+spam\b|spam\s+will\s+be\s+removed|zero\s+tolerance\s+for\s+spam"
        r"|no\s+low[\s-]?effort", re.I)),
    (CONDITIONAL, "Ratio-Regel (erst beitragen, dann teilen)", re.compile(
        r"\b(9\s*[:/]\s*1|10\s*[:/]\s*1|1\s*[:/]\s*(9|10)|90\s*/\s*10)\b"
        r"|reddiquette|self[\s-]?promo\w*\s+(ratio|guidelines)", re.I)),
    (CONDITIONAL, "Nur im Sammel-/Wochen-Thread", re.compile(
        r"(mega|sticky|stickied|weekly|monthly|friday|saturday|sunday)[\s-]*(thread|post|megathread)"
        r"|self[\s-]?promo\w*\s+thread|promo\s+thread|share\s+your\s+work\s+thread", re.I)),
    (CONDITIONAL, "Vorherige Mod-Freigabe noetig", re.compile(
        r"(message|contact|ask|pm)\s+(the\s+)?mod(erator)?s?\s+(first|before|for\s+(permission|approval))"
        r"|mod(erator)?\s+approval\s+(is\s+)?(required|needed)"
        r"|permission\s+from\s+the\s+mods", re.I)),
    (CONDITIONAL, "Flair erforderlich", re.compile(
        r"(post|submission)s?\s+must\s+be\s+flaired|flair\s+(is\s+)?(required|mandatory)"
        r"|use\s+(the\s+)?(correct|appropriate)\s+flair", re.I)),
    (CONDITIONAL, "Nur Text-Posts erlaubt", re.compile(
        r"(text[\s-]?posts?\s+only|no\s+link\s+posts?|self[\s-]?posts?\s+only)", re.I)),
    (CONDITIONAL, "Mindest-Karma / Kontoalter", re.compile(
        r"(minimum|min\.?)\s+(karma|account\s+age)|account\s+age\s+requirement"
        r"|karma\s+(requirement|threshold)", re.I)),
    (CONDITIONAL, "Keine Umfragen/Monetarisierung", re.compile(
        r"no\s+(surveys?|crowdfunding|patreon|merch|paywall|monetiz\w+)", re.I)),
]

# Wenn eine Regel Eigenwerbung ausdruecklich ERLAUBT, hebt das ein rotes Verdikt auf.
_ALLOW_PATTERN = re.compile(
    r"self[\s-]?promo\w*\s+(is\s+)?(allowed|welcome|permitted|encouraged)"
    r"|we\s+(allow|welcome)\s+self[\s-]?promo\w*"
    r"|feel\s+free\s+to\s+share\s+your\s+(own\s+)?(work|project|site)", re.I)


def analyse(texts: dict[str, str]) -> dict:
    """
    texts: {"Quelle": "Regeltext", ...} - z.B. einzelne Subreddit-Regeln,
    die Sidebar-Beschreibung und der submit_text.

    Rueckgabe: {"verdict", "labels": [...], "evidence": [{"source","label","quote"}]}
    """
    if not texts or not any(t.strip() for t in texts.values()):
        return {"verdict": UNKNOWN, "labels": [], "evidence": [],
                "explicitly_allowed": False}

    evidence: list[dict] = []
    labels: list[str] = []
    verdict = OPEN
    explicitly_allowed = False

    for source, text in texts.items():
        if not text:
            continue
        flat = re.sub(r"\s+", " ", text)

        if _ALLOW_PATTERN.search(flat):
            explicitly_allowed = True
            match = _ALLOW_PATTERN.search(flat)
            evidence.append({
                "source": source,
                "label": "Eigenwerbung ausdruecklich erlaubt",
                "quote": _snippet(flat, match.start(), match.end()),
            })

        for level, label, pattern in _PATTERNS:
            match = pattern.search(flat)
            if not match:
                continue
            if label not in labels:
                labels.append(label)
                evidence.append({
                    "source": source,
                    "label": label,
                    "quote": _snippet(flat, match.start(), match.end()),
                })
            if level == FORBIDDEN:
                verdict = FORBIDDEN
            elif level == CONDITIONAL and verdict != FORBIDDEN:
                verdict = CONDITIONAL

    # Ausdrueckliche Erlaubnis schlaegt ein pauschales "no spam" - aber nur das.
    if explicitly_allowed and verdict == FORBIDDEN:
        hard = [e for e in evidence if e["label"] in
                ("Eigenwerbung verboten", "Keine Links zu eigenen Projekten")]
        verdict = FORBIDDEN if hard else CONDITIONAL

    return {
        "verdict": verdict,
        "labels": labels,
        "evidence": evidence[:12],
        "explicitly_allowed": explicitly_allowed,
    }


def _snippet(text: str, start: int, end: int, pad: int = 90) -> str:
    left = max(0, start - pad)
    right = min(len(text), end + pad)
    prefix = "..." if left > 0 else ""
    suffix = "..." if right < len(text) else ""
    return f"{prefix}{text[left:right].strip()}{suffix}"


VERDICT_TEXT = {
    OPEN: "Kein Promo-Verbot gefunden",
    CONDITIONAL: "Erlaubt, aber mit Auflagen",
    FORBIDDEN: "Eigenwerbung verboten - nicht posten",
    UNKNOWN: "Regeln nicht abrufbar - manuell pruefen",
}
