"""Swappable LLM wrapper (tracker.md sec.A.1): MASTER PRD names Gemini specifically,
but the user asked for a one-line-config swap between providers since we're testing on
free/low-cost tiers. Every agent goes through call_json() -- nobody imports google.genai
or openai directly, so a provider swap never touches agent code.

Deliberately does NOT bind a strict `response_schema` to the API call (Gemini's schema
binding API has shifted across SDK versions, and OpenAI's json_object mode doesn't support
one at all) -- instead: request JSON-mode output, prompt the model explicitly to only
return JSON, then parse and let the CALLER validate/clamp fields defensively. This matches
the MASTER PRD blueprint's own comment on this exact function: "never trust blindly".
"""
import json
import logging
import time

from config import Config

logger = logging.getLogger(__name__)

_DEFAULT_MODELS = {"gemini": "gemini-flash-latest", "openai": "gpt-4o-mini"}

_gemini_client = None
_openai_client = None


class LLMError(Exception):
    """The provider call succeeded but didn't yield usable JSON, or failed after retries."""


def _resolve_model():
    """Falls back to a sane per-provider default if LLM_MODEL still names the OTHER
    provider's model -- e.g. LLM_PROVIDER flipped to openai but LLM_MODEL wasn't
    updated from a gemini-* value. Avoids sending an obviously-wrong model string."""
    model = Config.LLM_MODEL
    provider = Config.LLM_PROVIDER
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
        model=_resolve_model(),
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
        model=_resolve_model(),
        messages=[{"role": "user", "content": prompt}],
        temperature=temperature,
        response_format={"type": "json_object"},
    )
    return resp.choices[0].message.content


_PROVIDERS = {"gemini": _call_gemini, "openai": _call_openai}


def call_json(prompt: str, temperature: float = 0.2, retries: int = 2) -> dict:
    """Call the configured provider, return parsed JSON. Retries on transient failures
    (network blips, an occasional non-JSON reply) with a short backoff; raises LLMError
    if every attempt fails so the caller's job-queue retry/DEAD logic takes over instead
    of silently returning garbage.
    """
    provider = Config.LLM_PROVIDER
    call_fn = _PROVIDERS.get(provider)
    if call_fn is None:
        raise LLMError(f"unknown LLM_PROVIDER: {provider!r} (expected 'gemini' or 'openai')")

    last_error = None
    for attempt in range(1, retries + 2):
        try:
            raw = call_fn(prompt, temperature)
            return json.loads(raw)
        except json.JSONDecodeError as exc:
            last_error = exc
            logger.warning("LLM call attempt %d/%d: non-JSON response: %s",
                           attempt, retries + 1, exc)
        except Exception as exc:  # noqa: BLE001 - provider SDKs raise their own exception types
            last_error = exc
            logger.warning("LLM call attempt %d/%d failed (%s): %s",
                           attempt, retries + 1, provider, exc)
        if attempt <= retries:
            time.sleep(1.5 * attempt)

    raise LLMError(f"{provider} call failed after {retries + 1} attempts: {last_error}")
