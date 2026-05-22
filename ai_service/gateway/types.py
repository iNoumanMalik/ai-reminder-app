from dataclasses import dataclass, field
from enum import Enum
from typing import Optional


class ProviderName(str, Enum):
    OPENAI = "openai"
    GEMINI = "gemini"
    DEEPSEEK = "deepseek"
    GROQ = "groq"
    ANTHROPIC = "anthropic"
    OLLAMA = "ollama"
    OPENROUTER = "openrouter"


@dataclass(frozen=True)
class ProviderConfig:
    name: ProviderName
    enabled: bool = True
    model: Optional[str] = None
    api_key: Optional[str] = None
    base_url: Optional[str] = None
    priority: int = 100


@dataclass
class GenerateResult:
    text: str
    provider: str
    model: str
    latency_ms: float
    attempt: int = 1
    fallback_used: bool = False


@dataclass
class RouterConfig:
    fallback_chain: list[ProviderName] = field(default_factory=list)
    timeout_seconds: float = 60.0
    max_retries_per_provider: int = 2
    retry_backoff_seconds: float = 0.5
