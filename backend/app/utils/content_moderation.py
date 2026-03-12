"""
Content moderation — keyword blocklist + LLM-based safety check for user prompts.

Usage:
    result = await moderate_prompt("build me a website for ...")
    if not result["safe"]:
        return 400, result["reason"]
"""

import os
import re
import traceback

from app.utils.llm_clients import get_openai_client

# ═══════════════════════════════════════════════════════════════════════
# BLOCKED KEYWORDS BY CATEGORY
# ═══════════════════════════════════════════════════════════════════════

BLOCKED_KEYWORDS: dict[str, list[str]] = {
    # ── HIGH CONFIDENCE: these keywords are unambiguous ──
    "adult_content": [
        "porn", "pornography", "xxx",
        "escort service", "escort agency",
        "cam girl", "camgirl", "onlyfans", "sex worker",
        "strip club", "erotic website", "erotic content",
        "sex shop", "adult toy", "adult entertainment",
        "fetish website", "sexy girls", "sexy women",
        "sugar daddy", "sugar baby",
        "adult dating", "nude website",
    ],
    "illegal_services": [
        "drug dealer", "drug dealing", "sell drugs",
        "cocaine", "heroin", "methamphetamine",
        "marijuana dispensary", "cannabis shop", "weed delivery",
        "fake passport", "fake id card", "counterfeit money",
        "money laundering", "darknet", "dark web marketplace",
        "illegal weapon", "arms dealer", "firearms dealer",
        "hitman", "hack for hire",
        "stolen credit card", "carding service", "identity theft service",
        "pyramid scheme", "ponzi scheme",
        "fake certificate", "fake degree", "diploma mill",
        "spyware service", "stalkerware",
    ],
    "gambling": [
        "online casino", "casino website", "gambling site", "gambling website",
        "sports betting", "betting platform", "betting website",
        "poker site", "poker website",
        "slot machine", "roulette online", "blackjack online",
        "bet365", "crypto gambling",
    ],
    "alcohol_tobacco": [
        "liquor store", "liquor shop", "wine shop",
        "beer delivery", "alcohol delivery",
        "online liquor", "buy alcohol online",
        "vape shop", "vaping store", "e-cigarette shop",
        "tobacco shop", "cigarette shop",
    ],
    "government": [
        "government of uae", "uae government official",
        "dubai police website", "abu dhabi police website",
        "impersonate government", "fake government",
        "fake embassy", "fake consulate",
        "government website", "government portal",
        "municipality website",
    ],
    "banking": [
        "bank website", "banking website", "banking portal",
        "emirates nbd website", "mashreq bank website",
        "adcb website", "rakbank website",
        "central bank website",
    ],
    "phishing": [
        "phishing", "credential harvesting",
        "password steal", "login page clone",
        "fake login", "clone bank website",
        "steal password", "capture credentials",
        "fake paypal", "fake stripe",
        "social engineering attack", "spoof website",
        "fake checkout",
    ],
    "violence": [
        "bomb making", "how to make a bomb", "explosive device",
        "terrorist", "terrorism", "mass shooting",
        "kill people", "assassination",
        "biological weapon", "chemical weapon",
        "hate group", "white supremacy", "neo nazi",
        "jihadi",
    ],
    "crypto_scam": [
        "crypto pump", "pump and dump",
        "get rich quick", "double your bitcoin",
        "trading bot scam",
    ],
    "religious_political": [
        "anti islam", "anti muslim", "islamophobia",
        "anti christian", "anti jewish", "antisemitic",
        "propaganda site", "hate speech",
        "blasphemy", "religious defamation",
    ],
}

# Flatten for quick lookup — compile as whole-word regex patterns
_KEYWORD_PATTERNS: list[tuple[re.Pattern, str, str]] = []
for category, keywords in BLOCKED_KEYWORDS.items():
    for kw in keywords:
        pattern = re.compile(r"\b" + re.escape(kw) + r"\b", re.IGNORECASE)
        _KEYWORD_PATTERNS.append((pattern, kw, category))


# ═══════════════════════════════════════════════════════════════════════
# KEYWORD CHECK (fast, local)
# ═══════════════════════════════════════════════════════════════════════


def check_prompt_safety(prompt: str) -> dict:
    """
    Check a prompt against the keyword blocklist.
    Returns {"safe": bool, "reason": str | None, "flagged_terms": list}
    """
    flagged_terms = []
    categories_hit = set()

    for pattern, keyword, category in _KEYWORD_PATTERNS:
        if pattern.search(prompt):
            flagged_terms.append(keyword)
            categories_hit.add(category)

    CATEGORY_LABELS = {
        "adult_content": "Adult content",
        "illegal_services": "Illegal services",
        "gambling": "Gambling & betting",
        "alcohol_tobacco": "Alcohol & tobacco",
        "government": "Government websites",
        "banking": "Banking & financial institutions",
        "phishing": "Phishing & scams",
        "violence": "Violence & extremism",
        "crypto_scam": "Crypto scams",
        "religious_political": "Religious/political content",
    }
    if flagged_terms:
        labels = [CATEGORY_LABELS.get(c, c) for c in sorted(categories_hit)]
        category_str = ", ".join(labels)
        return {
            "safe": False,
            "reason": f"[RESTRICTED] {category_str} — "
            f"this type of content cannot be generated on the Meydan platform.",
            "flagged_terms": flagged_terms,
        }

    return {"safe": True, "reason": None, "flagged_terms": []}


# ═══════════════════════════════════════════════════════════════════════
# LLM CHECK (secondary, for sneaky prompts)
# ═══════════════════════════════════════════════════════════════════════

_LLM_MODERATION_SYSTEM = """You are a content moderation system for Meydan Free Zone, a business website generator in Dubai, UAE.

Your job is to determine if a user's website generation prompt is requesting prohibited content.

PROHIBITED content categories:
1. Adult/sexual content or services (porn, escorts, dating, nudity)
2. Illegal products or services (drugs, weapons, counterfeit goods, fake documents)
3. Government websites or impersonation (any government entity, ministry, police, authority)
4. Bank or financial institution websites (bank websites, central bank, official financial portals)
5. Phishing, scam, or fraud websites
6. Violence, terrorism, or weapons
7. Hate speech, discrimination, or religious/political extremism
8. Gambling and betting (casinos, sports betting, poker, any betting platform)
9. Alcohol or tobacco shops/delivery services
10. Cryptocurrency scams, pyramid schemes, get-rich-quick schemes
11. Religious or political campaign websites

ALLOWED content (do NOT flag these):
- Legitimate businesses (restaurants, tech companies, consulting, retail, etc.)
- Professional services (law firms, accounting, medical clinics, etc.)
- E-commerce for legal products
- Personal portfolios, blogs, creative work
- Non-profit organizations
- Educational content

Respond with ONLY a JSON object:
{"safe": true} or {"safe": false, "reason": "brief explanation", "category": "category_name"}

Be strict about prohibited content but do not over-flag legitimate business requests."""


async def check_prompt_safety_llm(prompt: str) -> dict:
    """
    Use GPT-4.1-mini to check if a prompt is requesting prohibited content.
    Returns {"safe": bool, "reason": str | None, "flagged_terms": list}

    This is a secondary check — only called if keyword check passes.
    Non-blocking: returns safe=True if the LLM call fails.
    """
    try:
        client = get_openai_client()
        response = await client.chat.completions.create(
            model="gpt-4.1-mini",
            temperature=0,
            messages=[
                {"role": "system", "content": _LLM_MODERATION_SYSTEM},
                {"role": "user", "content": f"Check this website generation prompt:\n\n{prompt[:1000]}"},
            ],
            max_tokens=150,
        )
        text = response.choices[0].message.content.strip()

        # Parse the JSON response
        import json

        # Strip markdown code fences if present
        text = re.sub(r"^```\w*\s*\n?", "", text)
        text = re.sub(r"\n?```\s*$", "", text)
        result = json.loads(text)

        if result.get("safe", True):
            return {"safe": True, "reason": None, "flagged_terms": []}
        else:
            llm_reason = result.get("reason", "Prohibited content detected")
            return {
                "safe": False,
                "reason": f"[RESTRICTED] {llm_reason}",
                "flagged_terms": [result.get("category", "unknown")],
            }

    except Exception as e:
        # Non-blocking: if LLM check fails, allow the prompt through
        print(f"[Moderation] LLM check failed (allowing prompt): {e}", flush=True)
        traceback.print_exc()
        return {"safe": True, "reason": None, "flagged_terms": []}


# ═══════════════════════════════════════════════════════════════════════
# COMBINED CHECK
# ═══════════════════════════════════════════════════════════════════════


async def moderate_prompt(prompt: str) -> dict:
    """
    Run keyword check first (fast), then LLM check only if keyword check passes.
    Returns {"safe": bool, "reason": str | None, "flagged_terms": list}
    """
    # Step 1: Fast keyword check
    keyword_result = check_prompt_safety(prompt)
    if not keyword_result["safe"]:
        print(f"[Moderation] Blocked by keyword filter: {keyword_result['flagged_terms']}", flush=True)
        return keyword_result

    # Step 2: LLM check (only if keyword check passed — saves tokens)
    llm_enabled = os.getenv("MODERATION_LLM_ENABLED", "true").lower() == "true"
    if llm_enabled:
        llm_result = await check_prompt_safety_llm(prompt)
        if not llm_result["safe"]:
            print(f"[Moderation] Blocked by LLM check: {llm_result['reason']}", flush=True)
            return llm_result

    return {"safe": True, "reason": None, "flagged_terms": []}
