"""Provider contract; concrete network adapters are configured separately."""
from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True)
class ModelResponse:
    text: str
    provider: str
    model: str
    input_tokens: int | None = None
    output_tokens: int | None = None


class ModelProvider(Protocol):
    def generate(self, messages, *, max_tokens=800, timeout=30) -> ModelResponse:
        """Return text only. A provider response is untrusted data."""
        ...
