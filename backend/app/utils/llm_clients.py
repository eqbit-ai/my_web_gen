"""
Multi-LLM client manager.
- OpenAI (GPT) for text/content generation + planning stages
- Anthropic (Claude) for code generation + final beautification
"""

import os

from anthropic import AsyncAnthropic
from openai import AsyncOpenAI

_anthropic_client: AsyncAnthropic | None = None
_openai_client: AsyncOpenAI | None = None


def get_anthropic_client() -> AsyncAnthropic:
    global _anthropic_client
    if _anthropic_client is None:
        api_key = os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            raise RuntimeError("ANTHROPIC_API_KEY not configured")
        _anthropic_client = AsyncAnthropic(api_key=api_key)
    return _anthropic_client


def get_openai_client() -> AsyncOpenAI:
    global _openai_client
    if _openai_client is None:
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise RuntimeError("OPENAI_API_KEY not configured")
        _openai_client = AsyncOpenAI(api_key=api_key)
    return _openai_client
