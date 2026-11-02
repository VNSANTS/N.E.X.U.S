"""Provider contract; concrete network adapters are configured separately."""
from dataclasses import dataclass, field
from typing import Protocol


@dataclass(frozen=True)
class ToolCall:
    """Provider-neutral, untrusted request to invoke a registered tool."""
    id: str
    name: str
    arguments: dict
    provider_data: dict = field(default_factory=dict, repr=False)


@dataclass(frozen=True)
class ModelResponse:
    text: str
    provider: str
    model: str
    input_tokens: int | None = None
    output_tokens: int | None = None
    tool_calls: tuple[ToolCall, ...] = field(default_factory=tuple)


class ModelProvider(Protocol):
    def generate(self, messages, *, max_tokens=800, timeout=30) -> ModelResponse:
        """Return untrusted text and optional normalized tool-call requests."""
        ...
