from typing import Optional

from ..base import BaseLLMProvider
from ..types import ProviderName
from ._openai_compat import generate_openai_compatible


class OpenRouterProvider(BaseLLMProvider):
    name = ProviderName.OPENROUTER

    def is_configured(self) -> bool:
        return bool(self.api_key)

    async def generate(
        self,
        prompt: str,
        *,
        temperature: float = 0.0,
        response_format: Optional[str] = None,
        model: Optional[str] = None,
    ) -> str:
        if not self.api_key:
            from ..exceptions import ProviderAuthError

            raise ProviderAuthError(self.name.value, "OPENROUTER_API_KEY is not set")
        return await generate_openai_compatible(
            provider=self.name,
            api_key=self.api_key,
            model=model or self.model,
            prompt=prompt,
            temperature=temperature,
            response_format=response_format,
            base_url=self.base_url or "https://openrouter.ai/api/v1",
            default_headers={
                "HTTP-Referer": "https://ai-reminder-app.local",
                "X-Title": "AI Reminder App",
            },
        )
