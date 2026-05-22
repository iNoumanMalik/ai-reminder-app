# AI Gateway (multi-provider LLM router)

Production-oriented async orchestration for reminder extraction and future AI tasks.

## Supported providers

| Provider | Env key(s) | Default model |
|----------|------------|---------------|
| OpenAI | `OPENAI_API_KEY` | `gpt-4o-mini` |
| Gemini | `GEMINI_API_KEY` | `models/gemini-2.5-flash` |
| DeepSeek | `DEEPSEEK_API_KEY` | `deepseek-chat` |
| Groq | `GROQ_API_KEY` | `llama-3.3-70b-versatile` |
| Anthropic | `ANTHROPIC_API_KEY` | `claude-3-5-haiku-20241022` |
| Ollama | `OLLAMA_BASE_URL` (optional key) | `llama3.2` |
| OpenRouter | `OPENROUTER_API_KEY` | `openai/gpt-4o-mini` |

Override models with `OPENAI_MODEL`, `GEMINI_MODEL`, etc.

## Router behavior

- **Fallback chain** via `AI_FALLBACK_CHAIN` (comma-separated), e.g.  
  `gemini,openai,deepseek,groq,ollama`
- **Per-provider retries**: `AI_MAX_RETRIES_PER_PROVIDER` (default `2`)
- **Timeout**: `AI_REQUEST_TIMEOUT_SECONDS` (default `60`)
- **Backoff**: `AI_RETRY_BACKOFF_SECONDS` (default `0.5`)

On failure, the router logs the provider + error and tries the next provider.

## Usage

```python
from gateway.factory import get_default_router

router = get_default_router()
result = await router.generate("Say hello", temperature=0)
print(result.provider, result.text)
```

## Add a new provider

1. Add enum value in `gateway/types.py` (`ProviderName`).
2. Implement `BaseLLMProvider` in `gateway/providers/your_provider.py`.
3. Register in `gateway/registry.py` (`build_provider` maps).
4. Add env keys + default model.
5. Include name in `AI_FALLBACK_CHAIN`.
