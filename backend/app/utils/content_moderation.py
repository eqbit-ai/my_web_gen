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
    "adult_content": [
        "porn", "pornography", "xxx", "adult content",
        "escort", "escorts", "escort service",
        "cam girl", "camgirl", "onlyfans", "sex worker",
        "strip club", "nude", "nudity", "erotic",
        "sex shop", "adult toy", "adult entertainment",
        "hookup", "fetish", "sexy girls", "sexy women",
        "dating site", "sugar daddy", "sugar baby",
        "massage parlor", "happy ending",
        "lingerie shop", "adult dating",
    ],
    "illegal_services": [
        "drug dealer", "drug dealing",
        "cocaine", "heroin", "meth", "methamphetamine",
        "marijuana dispensary", "cannabis shop", "weed delivery",
        "fake passport", "fake id", "counterfeit",
        "money laundering", "darknet", "dark web marketplace",
        "illegal weapon", "arms dealer", "gun shop", "firearms dealer",
        "hitman", "hack for hire",
        "stolen credit card", "carding", "identity theft service",
        "pyramid scheme", "ponzi scheme",
        "fake certificate", "fake degree", "diploma mill",
        "spy software", "spyware service", "stalkerware",
    ],
    "gambling": [
        "online casino", "casino website", "gambling site",
        "sports betting", "betting platform", "poker site",
        "slot machine", "roulette online", "blackjack online",
        "bet365", "bookmaker", "bookie",
        "crypto gambling", "binary options",
    ],
    "alcohol_tobacco": [
        "liquor store", "liquor shop", "wine shop",
        "beer delivery", "alcohol delivery",
        "online liquor", "buy alcohol online",
        "vape shop", "vaping store", "e-cigarette shop",
        "tobacco shop", "cigarette shop", "hookah shop", "shisha shop",
        "cigar shop",
    ],
    "government": [
        "government of uae", "uae government official",
        "ministry of", "dubai police", "abu dhabi police",
        "central bank of uae", "immigration authority",
        "impersonate government", "fake government",
        "fake embassy", "fake consulate",
        "royal family", "sheikh official",
        "dewa official", "rta official", "dha official",
        "government website", "government portal",
        "municipality website", "federal authority",
        "dubai municipality", "abu dhabi government",
        "sharjah government", "ajman government",
    ],
    "banking": [
        "bank website", "banking website", "banking portal",
        "emirates nbd", "mashreq bank", "adcb bank",
        "fab bank", "dib bank", "enbd",
        "rakbank", "commercial bank", "national bank",
        "central bank", "investment bank website",
        "nbd official", "banking platform",
    ],
    "phishing": [
        "phishing", "credential harvesting",
        "password steal", "login page clone",
        "fake login", "clone bank website",
        "steal password", "capture credentials",
        "fake paypal", "fake stripe",
        "social engineering attack", "spoof website",
        "man in the middle", "fake checkout",
        "clone website", "mirror site",
    ],
    "violence": [
        "bomb making", "how to make a bomb", "explosive device",
        "terrorist", "terrorism", "mass shooting",
        "kill people", "assassination",
        "biological weapon", "chemical weapon",
        "hate group", "white supremacy", "neo nazi",
        "extremist", "jihadi",
    ],
    "crypto_scam": [
        "crypto pump", "pump and dump",
        "guaranteed returns", "guaranteed profit",
        "get rich quick", "double your bitcoin",
        "forex robot", "trading bot scam",
        "investment guaranteed",
    ],
    "religious_political": [
        "anti islam", "anti muslim", "islamophobia",
        "anti christian", "anti jewish", "antisemitic",
        "political party website", "political campaign",
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
            "reason": f"Restricted content: {category_str}. "
            f"This type of content is not allowed on the Meydan platform.",
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
            return {
                "safe": False,
                "reason": result.get("reason", "Content flagged by AI moderation"),
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
