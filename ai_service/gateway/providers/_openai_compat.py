"""Shared OpenAI-compatible chat completion client for multiple vendors."""

from typing import Optional

from openai import AsyncOpenAI

from ..exceptions import ProviderAuthError, ProviderError, ProviderRateLimitError
from ..types import ProviderName


def _map_openai_error(exc: Exception, provider: ProviderName) -> ProviderError:
    status = getattr(exc, "status_code", None)
    msg = str(exc)
    lower = msg.lower()
    if status == 401 or "invalid api key" in lower or "authentication" in lower:
        return ProviderAuthError(provider.value, msg)
    if status == 429 or "rate limit" in lower:
        return ProviderRateLimitError(provider.value, msg)
    return ProviderError(msg, provider=provider.value, status_code=status, cause=exc)


async def generate_openai_compatible(
    *,
    provider: ProviderName,
    api_key: str,
    model: str,
    prompt: str,
    temperature: float,
    response_format: Optional[str],
    base_url: Optional[str] = None,
    default_headers: Optional[dict[str, str]] = None,
) -> str:
    client = AsyncOpenAI(
        api_key=api_key,
        base_url=base_url,
        default_headers=default_headers,
    )
    kwargs: dict = {
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": temperature,
    }
    if response_format == "json":
        kwargs["response_format"] = {"type": "json_object"}

    try:
        response = await client.chat.completions.create(**kwargs)
    except Exception as exc:
        raise _map_openai_error(exc, provider) from exc

    if not response.choices:
        raise ProviderError("Empty completion choices", provider=provider.value, retryable=True)

    content = response.choices[0].message.content
    if not content or not content.strip():
        raise ProviderError("Empty model response", provider=provider.value, retryable=True)
    return content.strip()
