from typing import Optional

from ..base import BaseLLMProvider
from ..exceptions import ProviderAuthError, ProviderError
from ..types import ProviderName

try:
    from google import genai
    from google.genai import types
except ImportError:
    genai = None
    types = None


class GeminiProvider(BaseLLMProvider):
    name = ProviderName.GEMINI

    def __init__(self, *, model: str, api_key: Optional[str] = None, base_url: Optional[str] = None) -> None:
        super().__init__(model=model, api_key=api_key, base_url=base_url)
        self._client = genai.Client(api_key=api_key) if genai and api_key else None

    def is_configured(self) -> bool:
        return bool(self.api_key and self._client)

    async def generate(
        self,
        prompt: str,
        *,
        temperature: float = 0.0,
        response_format: Optional[str] = None,
        model: Optional[str] = None,
    ) -> str:
        if not self._client:
            raise ProviderAuthError(self.name.value, "GEMINI_API_KEY is not set or SDK unavailable")

        model_id = model or self.model
        config_kwargs: dict = {"temperature": temperature}
        if response_format == "json" and types:
            config_kwargs["response_mime_type"] = "application/json"

        try:
            response = await self._client.aio.models.generate_content(
                model=model_id,
                contents=prompt,
                config=types.GenerateContentConfig(**config_kwargs) if types else None,
            )
        except Exception as exc:
            msg = str(exc)
            lower = msg.lower()
            if "api key" in lower or "permission" in lower:
                raise ProviderAuthError(self.name.value, msg) from exc
            raise ProviderError(msg, provider=self.name.value, cause=exc) from exc

        if not response or not response.text:
            raise ProviderError("Empty Gemini response", provider=self.name.value, retryable=True)
        return response.text.strip()
