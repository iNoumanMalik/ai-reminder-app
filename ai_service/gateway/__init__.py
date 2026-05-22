"""Multi-provider LLM gateway with fallback orchestration."""

from .exceptions import (
    AllProvidersFailedError,
    ProviderAuthError,
    ProviderError,
    ProviderRateLimitError,
    ProviderTimeoutError,
)
from .router import AIRouter
from .types import GenerateResult, ProviderName

__all__ = [
    "AIRouter",
    "AllProvidersFailedError",
    "GenerateResult",
    "ProviderAuthError",
    "ProviderError",
    "ProviderName",
    "ProviderRateLimitError",
    "ProviderTimeoutError",
]
