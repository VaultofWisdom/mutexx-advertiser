"""
Strategy: which channels are worth it for this product - and which explicitly are not.

Product profile and analysis go in, a scored channel plan comes out. Every channel
carries what it is good for, what it costs, how long it takes and how far this tool
can carry it. Channels that do not fit are not silently dropped - they are listed with
a reason. A recommendation without a counter-check is an opinion, not advice.

THE HARD LIMIT: this module does not spend money and cannot. Paid campaigns are
prepared in full - copy, audiences, keywords, budget split - and then handed over. A
human activates them in their own ad account. That is the same decision as posting to
other people's communities, for the same reason: the last click is where a human
notices the damage before it happens.

NO PROSE IS STORED HERE. Every channel's name, description, first step and risk lives
in the translation catalogue under "channel.<id>.*". A plan saved last month reads
correctly in either language, because the language was never baked into it.
"""

from __future__ import annotations

import json
import re
import time
from typing import Any

from . import core, i18n, products

# How far this tool carries a channel.
FULL = "voll"             # the app posts by itself
PREPARED = "vorbereitet"  # the app prepares everything, a human sends it
GUIDED = "anleitung"      # the app supplies copy and instructions, the rest is by hand


# ---------------------------------------------------------------------------
# Channel catalogue
#
# Structure only. "categories" and "price_models" are fits from 0 to 1; anything not
# listed counts as DEFAULT_FIT - unknown is not the same as unsuitable.
# ---------------------------------------------------------------------------

CHANNELS: list[dict[str, Any]] = [
    # -- owned ---------------------------------------------------------------
    {
        "id": "own_channels", "kind": "eigen", "base": 0.9, "min_budget": 0,
        "effort": "niedrig", "lead_time": "sofort", "automation": FULL,
        "categories": {}, "price_models": {},
    },
    {
        "id": "product_page", "kind": "eigen", "base": 0.95, "min_budget": 0,
        "effort": "niedrig", "lead_time": "sofort", "automation": GUIDED,
        "categories": {}, "price_models": {},
    },

    # -- organic -------------------------------------------------------------
    {
        "id": "communities", "kind": "organisch", "base": 0.8, "min_budget": 0,
        "effort": "mittel", "lead_time": "Wochen", "automation": PREPARED,
        "categories": {
            "content_site": 1.0, "dev_tool": 1.0, "software_desktop": 0.9, "game": 0.9,
            "software_web": 0.8, "app_mobile": 0.7, "creative": 0.7, "service": 0.4,
            "shop_physical": 0.3, "other": 0.6,
        },
        "price_models": {"free": 1.0, "freemium": 0.9, "ad_supported": 0.7,
                         "one_time": 0.6, "subscription": 0.6, "shop": 0.3, "quote": 0.4},
    },
    {
        "id": "directories", "kind": "organisch", "base": 0.75, "min_budget": 0,
        "effort": "niedrig", "lead_time": "Tage", "automation": PREPARED,
        "categories": {
            "software_desktop": 1.0, "app_mobile": 0.9, "dev_tool": 0.9, "game": 0.9,
            "software_web": 0.8, "content_site": 0.4, "creative": 0.5,
            "service": 0.3, "shop_physical": 0.2, "other": 0.4,
        },
        "price_models": {},
    },
    {
        "id": "seo_content", "kind": "organisch", "base": 0.7, "min_budget": 0,
        "effort": "hoch", "lead_time": "Monate", "automation": GUIDED,
        "categories": {
            "content_site": 1.0, "software_web": 0.9, "shop_physical": 0.9, "service": 0.9,
            "software_desktop": 0.8, "dev_tool": 0.7, "creative": 0.6, "app_mobile": 0.5,
            "game": 0.4, "other": 0.6,
        },
        "price_models": {},
    },
    {
        "id": "app_store", "kind": "organisch", "base": 0.8, "min_budget": 0,
        "effort": "mittel", "lead_time": "Tage", "automation": GUIDED,
        "categories": {"app_mobile": 1.0, "game": 1.0, "software_desktop": 0.6, "other": 0.1},
        "price_models": {},
    },
    {
        "id": "open_source", "kind": "organisch", "base": 0.7, "min_budget": 0,
        "effort": "niedrig", "lead_time": "Tage", "automation": GUIDED,
        "categories": {"dev_tool": 1.0, "software_desktop": 0.7, "software_web": 0.5,
                       "game": 0.3, "other": 0.2},
        "price_models": {"free": 1.0, "freemium": 0.8, "one_time": 0.4,
                         "subscription": 0.4, "shop": 0.1, "quote": 0.2, "ad_supported": 0.5},
        "needs": "links.repo",
    },
    {
        "id": "press", "kind": "organisch", "base": 0.55, "min_budget": 0,
        "effort": "hoch", "lead_time": "Wochen", "automation": PREPARED,
        "categories": {"software_desktop": 0.8, "game": 0.9, "software_web": 0.7,
                       "dev_tool": 0.6, "creative": 0.7, "service": 0.5,
                       "content_site": 0.5, "shop_physical": 0.4, "other": 0.4},
        "price_models": {},
    },
    {
        "id": "newsletter", "kind": "organisch", "base": 0.6, "min_budget": 0,
        "effort": "mittel", "lead_time": "Monate", "automation": GUIDED,
        "categories": {"software_web": 0.9, "content_site": 0.9, "shop_physical": 0.8,
                       "creative": 0.8, "service": 0.7, "software_desktop": 0.6,
                       "dev_tool": 0.5, "game": 0.5, "app_mobile": 0.4, "other": 0.5},
        "price_models": {"subscription": 0.9, "shop": 0.9, "freemium": 0.8, "one_time": 0.7},
    },
    {
        "id": "video", "kind": "organisch", "base": 0.6, "min_budget": 0,
        "effort": "mittel", "lead_time": "Tage", "automation": GUIDED,
        "categories": {"game": 1.0, "software_desktop": 0.8, "app_mobile": 0.8,
                       "software_web": 0.8, "dev_tool": 0.6, "creative": 0.7,
                       "service": 0.4, "shop_physical": 0.5, "content_site": 0.3, "other": 0.4},
        "price_models": {},
    },

    # -- paid ----------------------------------------------------------------
    {
        "id": "google_search_ads", "kind": "bezahlt", "base": 0.8, "min_budget": 150,
        "effort": "mittel", "lead_time": "Tage", "automation": PREPARED,
        "categories": {"software_web": 0.9, "shop_physical": 0.9, "service": 0.9,
                       "software_desktop": 0.7, "app_mobile": 0.5, "dev_tool": 0.4,
                       "creative": 0.5, "game": 0.3, "content_site": 0.2, "other": 0.5},
        "price_models": {"subscription": 1.0, "shop": 1.0, "one_time": 0.9, "quote": 0.8,
                         "freemium": 0.6, "free": 0.15, "ad_supported": 0.2},
    },
    {
        "id": "google_shopping", "kind": "bezahlt", "base": 0.9, "min_budget": 200,
        "effort": "hoch", "lead_time": "Wochen", "automation": GUIDED,
        "categories": {"shop_physical": 1.0},
        "price_models": {"shop": 1.0},
        "hard_categories": ["shop_physical"],
    },
    {
        "id": "meta_ads", "kind": "bezahlt", "base": 0.75, "min_budget": 150,
        "effort": "mittel", "lead_time": "Tage", "automation": PREPARED,
        "categories": {"shop_physical": 1.0, "app_mobile": 0.9, "creative": 0.8, "game": 0.8,
                       "service": 0.7, "software_web": 0.6, "software_desktop": 0.4,
                       "content_site": 0.4, "dev_tool": 0.15, "other": 0.5},
        "price_models": {"shop": 1.0, "subscription": 0.8, "one_time": 0.8,
                         "freemium": 0.6, "quote": 0.6, "free": 0.2, "ad_supported": 0.3},
    },
    {
        "id": "reddit_ads", "kind": "bezahlt", "base": 0.7, "min_budget": 100,
        "effort": "niedrig", "lead_time": "Tage", "automation": PREPARED,
        "categories": {"dev_tool": 0.9, "game": 0.9, "software_desktop": 0.8,
                       "content_site": 0.8, "software_web": 0.7, "app_mobile": 0.6,
                       "creative": 0.6, "service": 0.3, "shop_physical": 0.4, "other": 0.5},
        "price_models": {},
    },
    {
        "id": "microsoft_ads", "kind": "bezahlt", "base": 0.6, "min_budget": 100,
        "effort": "niedrig", "lead_time": "Tage", "automation": PREPARED,
        "categories": {"software_desktop": 0.9, "service": 0.8, "software_web": 0.7,
                       "shop_physical": 0.6, "dev_tool": 0.4, "app_mobile": 0.3,
                       "game": 0.3, "content_site": 0.3, "other": 0.4},
        "price_models": {"one_time": 0.9, "subscription": 0.9, "quote": 0.8,
                         "shop": 0.7, "freemium": 0.6, "free": 0.15, "ad_supported": 0.2},
    },
    {
        "id": "video_ads", "kind": "bezahlt", "base": 0.5, "min_budget": 400,
        "effort": "hoch", "lead_time": "Wochen", "automation": GUIDED,
        "categories": {"game": 0.9, "app_mobile": 0.9, "shop_physical": 0.8, "creative": 0.7,
                       "software_web": 0.5, "software_desktop": 0.4, "service": 0.4,
                       "dev_tool": 0.15, "content_site": 0.3, "other": 0.4},
        "price_models": {"shop": 0.9, "subscription": 0.8, "one_time": 0.7,
                         "freemium": 0.6, "free": 0.2, "quote": 0.4, "ad_supported": 0.3},
    },
    {
        "id": "sponsoring", "kind": "bezahlt", "base": 0.6, "min_budget": 200,
        "effort": "niedrig", "lead_time": "Wochen", "automation": GUIDED,
        "categories": {"dev_tool": 0.9, "software_web": 0.8, "software_desktop": 0.7,
                       "content_site": 0.6, "service": 0.6, "creative": 0.5,
                       "game": 0.5, "app_mobile": 0.4, "shop_physical": 0.4, "other": 0.5},
        "price_models": {},
    },
]

CHANNELS_BY_ID = {channel["id"]: channel for channel in CHANNELS}

DEFAULT_FIT = 0.2  # unknown is not the same as unsuitable


def text_key(channel_id: str, part: str) -> str:
    return f"channel.{channel_id}.{part}"


# ---------------------------------------------------------------------------
# Scoring
# ---------------------------------------------------------------------------

def _fit(mapping: dict, key: str) -> float:
    if not mapping:
        return 0.8   # a channel with no restriction fits in principle
    return float(mapping.get(key, DEFAULT_FIT))


def _has(product: dict, path: str) -> bool:
    node: Any = product
    for part in path.split("."):
        if not isinstance(node, dict):
            return False
        node = node.get(part)
    return bool(node)


def score_channel(channel: dict, product: dict) -> dict:
    """Scores a channel for a product. Returns the number AND the reasoning - a number
    without a reason is worthless in marketing."""
    category = product.get("category", "other")
    price_model = product.get("price_model", "free")
    budget = int(product.get("budget_monthly_eur") or 0)

    category_fit = _fit(channel.get("categories", {}), category)
    price_fit = _fit(channel.get("price_models", {}), price_model)
    reasons: list[dict] = []
    blocked: dict | None = None

    # Hard exclusions first - those cannot be scored away.
    hard = channel.get("hard_categories")
    if hard and category not in hard:
        blocked = i18n.message(
            "blocked.hard_category",
            required=i18n.message(products.CATEGORIES[hard[0]]),
            actual=i18n.message(products.CATEGORIES.get(category, "category.other")))
    elif channel.get("needs") and not _has(product, channel["needs"]):
        blocked = i18n.message("blocked.needs_field", field=channel["needs"])
    elif channel["kind"] == "bezahlt":
        if budget <= 0:
            blocked = i18n.message("blocked.no_budget")
        elif budget < channel["min_budget"]:
            blocked = i18n.message("blocked.under_minimum",
                                   minimum=channel["min_budget"], budget=budget)

    if blocked:
        return {"id": channel["id"], "kind": channel["kind"],
                "score": 0.0, "blocked": blocked, "why": []}

    score = channel["base"] * (0.55 * category_fit + 0.25 * price_fit + 0.20)

    category_label = i18n.message(products.CATEGORIES.get(category, "category.other"))
    price_label = i18n.message(products.PRICE_MODELS.get(price_model, "price.free"))

    if category_fit >= 0.85:
        reasons.append(i18n.message("reason.category_strong", category=category_label))
    elif category_fit <= 0.35:
        reasons.append(i18n.message("reason.category_weak", category=category_label))
    if price_fit >= 0.85:
        reasons.append(i18n.message("reason.price_strong", price=price_label))
    elif price_fit <= 0.25:
        reasons.append(i18n.message("reason.price_weak", price=price_label))

    # A free product has no revenue to fund advertising out of.
    if channel["kind"] == "bezahlt" and price_model in ("free", "ad_supported"):
        score *= 0.55
        reasons.append(i18n.message("reason.free_paid"))

    if channel["kind"] == "eigen":
        reasons.append(i18n.message("reason.owned"))

    return {"id": channel["id"], "kind": channel["kind"],
            "score": round(min(score, 1.0), 3), "blocked": None, "why": reasons}


# ---------------------------------------------------------------------------
# Budget split
# ---------------------------------------------------------------------------

def split_budget(paid: list[dict], budget: int) -> list[dict]:
    """Distributes the monthly budget across the paid channels, weighted by score.

    Two rules that come from experience rather than arithmetic:
      * How many channels may run at all depends on the budget. 120 EUR across two
        channels means twice too little - neither gathers enough data to learn
        anything. A small budget goes into ONE channel.
      * A fifth stays untouched. That is the reserve for whichever channel turns out
        to be the good one.
    """
    if not paid or budget <= 0:
        return []

    if budget < 250:
        slots = 1
    elif budget < 600:
        slots = 2
    else:
        slots = 3
    chosen = paid[:slots]
    reserve = max(0, round(budget * 0.2 / 10) * 10)
    spendable = budget - reserve
    total = sum(item["score"] for item in chosen) or 1.0

    split: list[dict] = []
    assigned = 0
    for index, item in enumerate(chosen):
        if index == len(chosen) - 1:
            amount = spendable - assigned
        else:
            amount = max(10, round(spendable * item["score"] / total / 10) * 10)
        assigned += amount
        split.append({
            "channel": item["id"], "name_key": text_key(item["id"], "name"),
            "eur": max(0, amount), "share": round(max(0, amount) / budget, 2),
        })

    split.append({
        "channel": "_reserve", "name_key": "strategy.reserve",
        "eur": reserve, "share": round(reserve / budget, 2),
        "note_key": "strategy.reserve_note",
    })
    return split


# ---------------------------------------------------------------------------
# Phases
# ---------------------------------------------------------------------------

_PHASES = [
    ("phase.now", ("sofort",), "phase.now_note"),
    ("phase.weeks", ("Tage", "Wochen"), "phase.weeks_note"),
    ("phase.long", ("Monate",), "phase.long_note"),
]


def build_phases(ranked: list[dict]) -> list[dict]:
    phases = []
    for name_key, lead_times, note_key in _PHASES:
        members = [item for item in ranked
                   if CHANNELS_BY_ID[item["id"]]["lead_time"] in lead_times]
        if members:
            phases.append({"name_key": name_key, "note_key": note_key,
                           "channels": [item["id"] for item in members]})
    return phases


# ---------------------------------------------------------------------------
# The whole plan
# ---------------------------------------------------------------------------

def build(product: dict, analysis_result: dict | None = None, config: dict | None = None,
          use_api: bool | None = None) -> dict:
    """The complete channel plan. Does not raise - failures land as warnings."""
    analysis_result = analysis_result or {}
    config = config or {}
    budget = int(product.get("budget_monthly_eur") or 0)
    warnings: list[dict] = []

    scored = [score_channel(channel, product) for channel in CHANNELS]
    ranked = sorted([item for item in scored if not item["blocked"]],
                    key=lambda item: item["score"], reverse=True)
    rejected = [item for item in scored if item["blocked"]]

    # Attach the catalogue facts so the interface has to look nothing up.
    for item in ranked + rejected:
        channel = CHANNELS_BY_ID[item["id"]]
        item.update({
            "name_key": text_key(item["id"], "name"),
            "what_key": text_key(item["id"], "what"),
            "first_step_key": text_key(item["id"], "first_step"),
            "risk_key": text_key(item["id"], "risk"),
            "effort": channel["effort"],
            "effort_key": "effort." + channel["effort"],
            "lead_time": channel["lead_time"],
            "lead_time_key": "lead." + channel["lead_time"],
            "automation": channel["automation"],
            "automation_key": "automation." + channel["automation"],
            "kind_key": "kind.badge." + channel["kind"],
            "min_budget": channel["min_budget"],
        })

    paid = [item for item in ranked if item["kind"] == "bezahlt"]
    budget_plan = split_budget(paid, budget)
    for item in ranked:
        item["budget_eur"] = next((row["eur"] for row in budget_plan
                                   if row["channel"] == item["id"]), 0)

    if budget <= 0:
        warnings.append(i18n.message("strategy.warn.no_budget"))
    elif not paid:
        warnings.append(i18n.message("strategy.warn.no_paid_fit", budget=budget))
    if paid and len(budget_plan) == 2:
        warnings.append(i18n.message("strategy.warn.one_channel", budget=budget))
    if not analysis_result.get("keywords"):
        warnings.append(i18n.message("strategy.warn.no_analysis"))

    plan: dict[str, Any] = {
        "product_slug": product.get("slug", ""),
        "generated_at": int(time.time()),
        "budget_monthly_eur": budget,
        "summary": _summary(product, ranked, budget_plan, budget),
        "channels": ranked,
        "rejected": rejected,
        "phases": build_phases(ranked),
        "budget_plan": budget_plan,
        "first_week": _first_week(ranked),
        "warnings": warnings,
        "source": "regeln",
    }

    if use_api is None:
        use_api = bool((config.get("anthropic") or {}).get("api_key", "").strip())
    if use_api:
        try:
            plan.update(_refine_with_api(product, analysis_result, plan, config))
            plan["source"] = "regeln+ki"
        except Exception as error:  # noqa: BLE001 - the rule-based plan stands
            warnings.append(i18n.message("strategy.warn.api_failed", error=error))

    plan["warnings"] = warnings
    return plan


def _summary(product: dict, ranked: list[dict], budget_plan: list[dict],
             budget: int) -> dict:
    if not ranked:
        return i18n.message("strategy.summary.none")

    funded = [row for row in budget_plan if row["channel"] != "_reserve"]
    if budget <= 0:
        money = i18n.message("strategy.summary.organic")
    elif funded:
        money = i18n.message("strategy.summary.funded", budget=budget,
                             named=_named_list(funded))
    else:
        money = i18n.message("strategy.summary.unfunded", budget=budget)

    return i18n.message(
        "strategy.summary.line",
        name=product.get("name") or "",
        category=i18n.message(products.CATEGORIES.get(product.get("category"),
                                                      "category.other")),
        top=_channel_list([item["id"] for item in ranked[:3]]),
        money=money,
    )


def _channel_list(ids: list[str]) -> dict:
    return i18n.message("list.join",
                        items=[i18n.message(text_key(cid, "name")) for cid in ids])


def _named_list(rows: list[dict]) -> dict:
    return i18n.message("list.join", items=[
        i18n.message("list.item_with_amount",
                     name=i18n.message(row["name_key"]), amount=row["eur"])
        for row in rows])


def _first_week(ranked: list[dict]) -> list[dict]:
    quick = [item for item in ranked
             if CHANNELS_BY_ID[item["id"]]["lead_time"] in ("sofort", "Tage")][:4]
    return [i18n.message("list.step",
                         name=i18n.message(text_key(item["id"], "name")),
                         step=i18n.message(text_key(item["id"], "first_step")))
            for item in quick]


# ---------------------------------------------------------------------------
# Optional AI summary
# ---------------------------------------------------------------------------

_SYSTEM = """You are a plain-spoken marketing strategist. You get a product profile, an
analysis and a channel plan that has already been calculated. Your job is NOT to
overturn the plan but to explain it and make the first steps concrete.

Rules:
- No superlatives, no agency language, no exclamation marks.
- Say what has to happen first and why that first.
- Name openly what is weak about this plan. A plan without a weak spot is a lie.
- Invent no numbers and no channels that are not in the plan.
- Answer only as JSON, with no preamble and no code fence.

Format:
{"summary": "three to five sentences",
 "first_week": ["a concrete action", "..."],
 "watch_out": ["what can go wrong", "..."]}"""


def _refine_with_api(product: dict, analysis_result: dict, plan: dict, config: dict) -> dict:
    api = config.get("anthropic", {})
    key = (api.get("api_key") or "").strip()
    if not key:
        raise ValueError(i18n.t("error.no_api_key"))

    # The prompt is written in the product's language, not the interface language -
    # the model should answer in the language the operator's product speaks.
    language = (product.get("languages") or ["en"])[0]
    language = i18n.normalise(language)

    channel_lines = "\n".join(
        f"- {i18n.t(item['name_key'], language)} ({item['kind']}, score {item['score']}, "
        f"{i18n.t(item['lead_time_key'], language)}, "
        f"{i18n.t(item['automation_key'], language)}, budget {item['budget_eur']} EUR): "
        f"{' '.join(i18n.render(reason, language) for reason in item['why']) or '-'}"
        for item in plan["channels"][:8])
    rejected_lines = "\n".join(
        f"- {i18n.t(item['name_key'], language)}: {i18n.render(item['blocked'], language)}"
        for item in plan["rejected"][:8])

    prompt = f"""PRODUCT
Name: {product.get('name')}
One-liner: {product.get('one_liner') or '(none)'}
Category: {products.category_label(product.get('category'), language)}
Pricing: {products.price_label(product.get('price_model'), language)}
Audience: {product.get('audience') or '(not given)'}
Regions: {', '.join(product.get('regions') or [])}
Monthly budget: {plan['budget_monthly_eur']} EUR

ANALYSIS
Positioning: {analysis_result.get('positioning') or '(none)'}
Value propositions: {'; '.join(analysis_result.get('value_props') or []) or '(none)'}
Audience segments: {'; '.join(seg.get('name','') for seg in analysis_result.get('audience_segments') or []) or '(none)'}
Objections: {'; '.join(analysis_result.get('objections') or []) or '(none)'}

RECOMMENDED CHANNELS
{channel_lines or '(none)'}

REJECTED
{rejected_lines or '(none)'}

BUDGET SPLIT
{json.dumps(plan['budget_plan'], ensure_ascii=False) if plan['budget_plan'] else '(no budget)'}

Give 3 to 6 points for the first week and 2 to 4 warnings.
Answer in {i18n.LANGUAGES.get(language, 'English')}."""

    status, raw = core.post_json(
        "https://api.anthropic.com/v1/messages",
        {
            "model": api.get("model") or "claude-opus-5",
            "max_tokens": 2000,
            "system": _SYSTEM,
            "messages": [{"role": "user", "content": prompt}],
        },
        user_agent=config.get("user_agent", "MutexxAdvertiser/0.3"),
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

    # What the model writes is free prose in one language. It cannot be switched
    # later, so it is stored as-is and marked with the language it was written in.
    out: dict[str, Any] = {"ai_language": language}
    if str(parsed.get("summary") or "").strip():
        out["summary"] = str(parsed["summary"]).strip()
    for field in ("first_week", "watch_out"):
        value = parsed.get(field)
        if isinstance(value, list) and value:
            out[field] = [str(item).strip() for item in value if str(item).strip()][:8]
    return out


# ---------------------------------------------------------------------------
# Storage
# ---------------------------------------------------------------------------

def load(slug: str) -> dict:
    return core.load_product(slug, "strategy", {})


def store(slug: str, plan: dict) -> None:
    core.save_product(slug, "strategy", plan)
