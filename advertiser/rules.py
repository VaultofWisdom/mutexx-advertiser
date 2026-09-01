"""
Rule analysis: reads a community's rules and works out whether - and under what
conditions - a link of your own is welcome there at all.

IMPORTANT: this is a heuristic, not a substitute for reading. That is why the app
shows the original wording of every rule an assessment rests on.

The labels below are TRANSLATION KEYS, not sentences. A community scanned months ago
still reads correctly after a language switch, because the language was never stored.
"""

from __future__ import annotations

import re

# Verdict levels
FORBIDDEN = "rot"       # Eigenwerbung ausdruecklich verboten -> niemals posten
CONDITIONAL = "gelb"    # Erlaubt, aber mit Auflagen (Ratio, Flair, Thread, Mod-Freigabe)
OPEN = "gruen"          # Kein Promo-Verbot gefunden -> trotzdem hoeflich und wertig posten
UNKNOWN = "grau"        # Regeln nicht abrufbar


_PATTERNS: list[tuple[str, str, re.Pattern[str]]] = [
    # (verdict contribution, label, pattern)
    (FORBIDDEN, "rule.promo_forbidden", re.compile(
        r"no\s+(self[\s-]?promo\w*|advertis\w+|promotion|soliciting|shilling)"
        r"|self[\s-]?promo\w*\s+(is\s+)?(not\s+allowed|prohibited|banned|forbidden)"
        r"|keine\s+(eigen)?werbung|werbung\s+(ist\s+)?(verboten|untersagt|nicht\s+erlaubt)"
        r"|advertising\s+(is\s+)?(not\s+allowed|prohibited|banned)", re.I)),
    (FORBIDDEN, "rule.no_own_links", re.compile(
        r"no\s+(links?\s+to\s+your\s+own|blog\s?spam|blogspam|personal\s+(blogs?|websites?|projects?))"
        r"|do\s+not\s+(post|link)\s+your\s+(own\s+)?(site|website|blog|app|project)", re.I)),
    # "No spam" appears in almost every rule list and rarely means a promotion ban.
    # So it produces a condition, not a red verdict - otherwise half the list falls away.
    (CONDITIONAL, "rule.spam_ban", re.compile(
        r"no\s+spam\b|spam\s+will\s+be\s+removed|zero\s+tolerance\s+for\s+spam"
        r"|no\s+low[\s-]?effort", re.I)),
    (CONDITIONAL, "rule.ratio", re.compile(
        r"\b(9\s*[:/]\s*1|10\s*[:/]\s*1|1\s*[:/]\s*(9|10)|90\s*/\s*10)\b"
        r"|reddiquette|self[\s-]?promo\w*\s+(ratio|guidelines)", re.I)),
    (CONDITIONAL, "rule.megathread", re.compile(
        r"(mega|sticky|stickied|weekly|monthly|friday|saturday|sunday)[\s-]*(thread|post|megathread)"
        r"|self[\s-]?promo\w*\s+thread|promo\s+thread|share\s+your\s+work\s+thread", re.I)),
    (CONDITIONAL, "rule.mod_approval", re.compile(
        r"(message|contact|ask|pm)\s+(the\s+)?mod(erator)?s?\s+(first|before|for\s+(permission|approval))"
        r"|mod(erator)?\s+approval\s+(is\s+)?(required|needed)"
        r"|permission\s+from\s+the\s+mods", re.I)),
    (CONDITIONAL, "rule.flair", re.compile(
        r"(post|submission)s?\s+must\s+be\s+flaired|flair\s+(is\s+)?(required|mandatory)"
        r"|use\s+(the\s+)?(correct|appropriate)\s+flair", re.I)),
    (CONDITIONAL, "rule.text_only", re.compile(
        r"(text[\s-]?posts?\s+only|no\s+link\s+posts?|self[\s-]?posts?\s+only)", re.I)),
    (CONDITIONAL, "rule.karma", re.compile(
        r"(minimum|min\.?)\s+(karma|account\s+age)|account\s+age\s+requirement"
        r"|karma\s+(requirement|threshold)", re.I)),
    (CONDITIONAL, "rule.no_monetisation", re.compile(
        r"no\s+(surveys?|crowdfunding|patreon|merch|paywall|monetiz\w+)", re.I)),
]

# A rule that explicitly ALLOWS self-promotion lifts a red verdict.
_ALLOW_PATTERN = re.compile(
    r"self[\s-]?promo\w*\s+(is\s+)?(allowed|welcome|permitted|encouraged)"
    r"|we\s+(allow|welcome)\s+self[\s-]?promo\w*"
    r"|feel\s+free\s+to\s+share\s+your\s+(own\s+)?(work|project|site)", re.I)


def analyse(texts: dict[str, str]) -> dict:
    """
    texts: {"source": "rule text", ...} - individual subreddit rules, the sidebar
    description, the submit text.

    Returns: {"verdict", "labels": [...], "evidence": [{"source","label","quote"}]}
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
                "label": "rule.explicitly_allowed",
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

    # Explicit permission beats a blanket "no spam" - but only that.
    if explicitly_allowed and verdict == FORBIDDEN:
        hard = [e for e in evidence if e["label"] in
                ("rule.promo_forbidden", "rule.no_own_links")]
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


# Translation keys, not sentences - see i18n.py. The interface resolves them, which
# is why a community scanned months ago still reads correctly after a language switch.
VERDICT_TEXT = {
    OPEN: "verdict.gruen",
    CONDITIONAL: "verdict.gelb",
    FORBIDDEN: "verdict.rot",
    UNKNOWN: "verdict.grau",
}
