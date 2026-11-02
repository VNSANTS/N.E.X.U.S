"""Model provider adapters. Providers are optional and never execute tools."""
from .base import ModelProvider, ModelResponse
from .errors import (
    ProviderAuthenticationError,
    ProviderConfigurationError,
    ProviderError,
    ProviderRateLimitError,
    ProviderResponseError,
    ProviderTimeoutError,
    ProviderUnavailableError,
)
from .mock import MockProvider
from .adapters import AnthropicProvider, GeminiProvider, GroqProvider, OpenAIProvider, OpenRouterProvider
from .ollama import OllamaProvider
from .manager import ProviderManager

__all__ = [
    "ModelProvider",
    "ModelResponse",
    "MockProvider",
    "OllamaProvider",
    "OpenAIProvider",
    "AnthropicProvider",
    "GeminiProvider",
    "OpenRouterProvider",
    "GroqProvider",
    "ProviderManager",
    "ProviderError",
    "ProviderConfigurationError",
    "ProviderAuthenticationError",
    "ProviderRateLimitError",
    "ProviderTimeoutError",
    "ProviderUnavailableError",
    "ProviderResponseError",
]
