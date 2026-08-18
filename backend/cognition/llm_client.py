from __future__ import annotations
"""Swappable LLM wrapper (tracker.md sec.A.1): MASTER PRD names Gemini specifically,
but the user asked for a one-line-config swap between providers since we're testing on
free/low-cost tiers. Every agent goes through call_json() -- nobody imports google.genai
or openai directly, so a provider swap never touches agent code.

Deliberately does NOT bind a strict `response_schema` to the API call (Gemini's schema
binding API has shifted across SDK versions, and OpenAI's json_object mode doesn't support
one at all) -- instead: request JSON-mode output, prompt the model explicitly to only
return JSON, then parse and let the CALLER validate/clamp fields defensively. This matches
the MASTER PRD blueprint's own comment on this exact function: "never trust blindly".

Automatic provider fallback (added 2026-08-13, tracker.md sec.A.2): the discovery
scheduler's real ICP/review/scoring call volume exhausts Gemini's 20-requests/day free
tier fast. Rather than requiring a manual .env flip mid-run, call_json() now tries the
configured LLM_PROVIDER first and, only if it exhausts its own retries, automatically
falls back to the other provider (if that provider's API key is configured) before
raising LLMError. LLM_PROVIDER still controls which one is tried FIRST.
"""
import json
import logging
import time

from config import Config

logger = logging.getLogger(__name__)

_DEFAULT_MODELS = {"gemini": "gemini-flash-latest", "openai": "gpt-5.4-mini"}
_OTHER_PROVIDER = {"gemini": "openai", "openai": "gemini"}
_API_KEYS = {"gemini": lambda: Config.GEMINI_API_KEY, "openai": lambda: Config.OPENAI_API_KEY}

_gemini_client = None
_openai_client = None


class LLMError(Exception):
    """The provider call succeeded but didn't yield usable JSON, or failed after retries
    (across both the primary and, if available, the fallback provider)."""


def _resolve_model(provider):
    """Falls back to a sane per-provider default if LLM_MODEL names the OTHER
    provider's model -- e.g. this call is running the fallback provider, or
    LLM_PROVIDER changed but LLM_MODEL wasn't updated. Avoids sending an obviously-wrong
    model string."""
    model = Config.LLM_MODEL
    if provider == "openai" and model.startswith("gemini"):
        return _DEFAULT_MODELS["openai"]
    if provider == "gemini" and model.startswith("gpt"):
        return _DEFAULT_MODELS["gemini"]
    return model


def _get_gemini_client():
    global _gemini_client
    if _gemini_client is None:
        from google import genai
        _gemini_client = genai.Client(api_key=Config.GEMINI_API_KEY)
    return _gemini_client


def _get_openai_client():
    global _openai_client
    if _openai_client is None:
        from openai import OpenAI
        _openai_client = OpenAI(api_key=Config.OPENAI_API_KEY)
    return _openai_client


def _call_gemini(prompt, temperature):
    from google.genai import types
    client = _get_gemini_client()
    resp = client.models.generate_content(
        model=_resolve_model("gemini"),
        contents=prompt,
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
            temperature=temperature,
        ),
    )
    return resp.text


def _call_openai(prompt, temperature):
    client = _get_openai_client()
    resp = client.chat.completions.create(
        model=_resolve_model("openai"),
        messages=[{"role": "user", "content": prompt}],
        temperature=temperature,
        response_format={"type": "json_object"},
    )
    return resp.choices[0].message.content


_PROVIDERS = {"gemini": _call_gemini, "openai": _call_openai}


def _call_provider(provider: str, prompt: str, temperature: float, retries: int) -> dict:
    """Retries a single provider with a short backoff. Raises LLMError if every attempt
    on THIS provider fails -- the caller decides whether to fall back to another one."""
    call_fn = _PROVIDERS.get(provider)
    if call_fn is None:
        raise LLMError(f"unknown provider: {provider!r} (expected 'gemini' or 'openai')")

    last_error = None
    for attempt in range(1, retries + 2):
        try:
            raw = call_fn(prompt, temperature)
            return json.loads(raw)
        except json.JSONDecodeError as exc:
            last_error = exc
            logger.warning("LLM call attempt %d/%d (%s): non-JSON response: %s",
                           attempt, retries + 1, provider, exc)
        except Exception as exc:  # noqa: BLE001 - provider SDKs raise their own exception types
            last_error = exc
            logger.warning("LLM call attempt %d/%d failed (%s): %s",
                           attempt, retries + 1, provider, exc)
        if attempt <= retries:
            time.sleep(1.5 * attempt)

    raise LLMError(f"{provider} call failed after {retries + 1} attempts: {last_error}")


def call_json(prompt: str, temperature: float = 0.2, retries: int = 2) -> dict:
    """Calls LLM_PROVIDER first; if it exhausts its own retries, automatically falls
    back to the other configured provider (only if that provider has an API key set)
    before raising LLMError. Raises LLMError only when every available provider has
    failed, so the caller's job-queue retry/DEAD logic takes over instead of silently
    returning garbage.
    """
    primary = Config.LLM_PROVIDER
    if primary not in _PROVIDERS:
        raise LLMError(f"unknown LLM_PROVIDER: {primary!r} (expected 'gemini' or 'openai')")

    try:
        return _call_provider(primary, prompt, temperature, retries)
    except LLMError as primary_error:
        fallback = _OTHER_PROVIDER[primary]
        if not _API_KEYS[fallback]():
            raise  # no fallback key configured -- surface the original failure as-is

        logger.warning("LLM primary provider %s exhausted, falling back to %s", primary, fallback)
        try:
            return _call_provider(fallback, prompt, temperature, retries)
        except LLMError as fallback_error:
            raise LLMError(
                f"both providers failed -- {primary}: {primary_error}; {fallback}: {fallback_error}"
            ) from fallback_error
