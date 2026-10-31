"""Offline provider for tests and development; makes no network requests."""
from .base import ModelResponse


class MockProvider:
    def __init__(self, response="N.E.X.U.S está pronto para receber a próxima etapa."):
        self.response = response

    def generate(self, messages, *, max_tokens=800, timeout=30):
        if max_tokens < 1 or max_tokens > 4096:
            raise ValueError("max_tokens must be between 1 and 4096")
        if timeout <= 0 or timeout > 120:
            raise ValueError("timeout must be between 0 and 120 seconds")
        return ModelResponse(self.response, "mock", "offline-mock")
