from typing import Any, Optional

import httpx

from ..base import BaseLLMProvider
from ..exceptions import ProviderError
from ..types import ProviderName


class OllamaProvider(BaseLLMProvider):
    name = ProviderName.OLLAMA

    def __init__(self, *, model: str, api_key: Optional[str] = None, base_url: Optional[str] = None) -> None:
        super().__init__(model=model, api_key=api_key, base_url=base_url or "http://127.0.0.1:11434")

    def is_configured(self) -> bool:
        return bool(self.base_url and self.model)

    async def generate(
        self,
        prompt: str,
        *,
        temperature: float = 0.0,
        response_format: Optional[str] = None,
        model: Optional[str] = None,
    ) -> str:
        model_id = model or self.model
        url = f"{self.base_url.rstrip('/')}/api/chat"
        payload: dict[str, Any] = {
            "model": model_id,
            "messages": [{"role": "user", "content": prompt}],
            "stream": False,
            "options": {"temperature": temperature},
        }
        if response_format == "json":
            payload["format"] = "json"

        headers = {}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"

        try:
            async with httpx.AsyncClient(timeout=120.0) as client:
                response = await client.post(url, json=payload, headers=headers)
                response.raise_for_status()
                data = response.json()
        except Exception as exc:
            raise ProviderError(str(exc), provider=self.name.value, cause=exc) from exc

        message = data.get("message") or {}
        content = message.get("content")
        if not content or not str(content).strip():
            raise ProviderError("Empty Ollama response", provider=self.name.value, retryable=True)
        return str(content).strip()
