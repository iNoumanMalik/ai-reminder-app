from abc import ABC, abstractmethod
from typing import Optional

from .types import ProviderName


class BaseLLMProvider(ABC):
    """Unified async interface for all LLM providers."""

    name: ProviderName

    def __init__(self, *, model: str, api_key: Optional[str] = None, base_url: Optional[str] = None) -> None:
        self.model = model
        self.api_key = api_key
        self.base_url = base_url

    @abstractmethod
    async def generate(
        self,
        prompt: str,
        *,
        temperature: float = 0.0,
        response_format: Optional[str] = None,
        model: Optional[str] = None,
    ) -> str:
        """Generate text from a prompt. Raises ProviderError subclasses on failure."""

    def is_configured(self) -> bool:
        """Return True when provider has minimum credentials to run."""
        return True
