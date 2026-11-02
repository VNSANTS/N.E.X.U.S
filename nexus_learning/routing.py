"""Runtime bridge between the pure model policy and verified provider adapters."""
from dataclasses import dataclass
import json
import math
import time

from .model_router import ModelRoute, ModelRouter, NoRouteAvailable
from .providers.errors import ProviderError


@dataclass(frozen=True)
class RoutingResult:
    mode: str
    route: ModelRoute
    provider: object
    candidate_count: int


class FallbackProvider:
    """Bounded provider chain. Streaming retries only before exposing any output."""
    supports_task_tracking = True
    budget_managed = True

    def __init__(self, providers):
        if not providers:
            raise ValueError("at least one provider is required")
        self.providers = tuple(providers)
        self.active = self.providers[0]

    @property
    def provider_name(self):
        return getattr(self.active, "provider_name", "unknown")

    @property
    def model(self):
        return getattr(self.active, "model", "unknown")

    @property
    def num_predict(self):
        return getattr(self.active, "num_predict", 800)

    @property
    def default_timeout(self):
        return getattr(self.active, "default_timeout", 60)

    def generate(self, messages, *, max_tokens=800, timeout=60, task_id=None):
        last_error = None
        for index, provider in enumerate(self.providers):
            self.active = provider
            kwargs = {"max_tokens": max_tokens, "timeout": timeout}
            if getattr(provider, "supports_task_tracking", False):
                kwargs["task_id"] = task_id
            try:
                return provider.generate(messages, **kwargs)
            except ProviderError as exc:
                last_error = exc
                if not exc.retryable or index == len(self.providers) - 1:
                    raise
        raise last_error

    def stream_generate(self, messages, *, max_tokens=800, timeout=60,
                        task_id=None, cancel_event=None):
        last_error = None
        for index, provider in enumerate(self.providers):
            self.active = provider
            stream = getattr(provider, "stream_generate", None)
            if not callable(stream):
                raise NoRouteAvailable("A fallback candidate does not support streaming.")
            kwargs = {"max_tokens": max_tokens, "timeout": timeout,
                      "cancel_event": cancel_event}
            if getattr(provider, "supports_task_tracking", False):
                kwargs["task_id"] = task_id
            emitted = False
            try:
                for chunk in stream(messages, **kwargs):
                    emitted = True
                    yield chunk
                return
            except ProviderError as exc:
                last_error = exc
                if emitted or not exc.retryable or index == len(self.providers) - 1:
                    raise
        if last_error:
            raise last_error


class ModelRoutingService:
    """Resolve explicitly configured candidates against live model/health APIs."""
    MAX_CANDIDATES = 12
    CACHE_SECONDS = 30
    _candidate_keys = {"provider", "model", "context_window", "reasoning_score",
                       "latency_ms", "capabilities"}
    _capability_keys = {"chat", "streaming", "research", "reasoning"}

    def __init__(self, manager, budget, *, env=None, router=None, wrap_provider=None):
        self.manager = manager
        self.budget = budget
        self.env = env if env is not None else manager.env
        self.router = router or ModelRouter()
        self.wrap_provider = wrap_provider or (lambda provider: provider)
        self._cache = {}

    def mode(self):
        value = self.env.get("NEXUS_ROUTING_MODE", "manual").strip().lower()
        if value not in {"manual", "automatic"}:
            raise NoRouteAvailable("Model routing mode is invalid.")
        return value

    def summary(self):
        try:
            mode = self.mode()
        except NoRouteAvailable:
            mode = "invalid"
        try:
            count = len(self._candidate_specs()) if mode == "automatic" else 0
        except NoRouteAvailable:
            count = 0
        return {"mode": mode, "configured_candidates": count,
                "remote_budget_enabled": bool(self.budget.settings().get("enabled"))}

    def resolve(self, text, messages, *, streaming=False):
        mode = self.mode()
        if mode == "manual":
            provider = self.manager.selected()
            route = ModelRoute(self.router.classify(text),
                               getattr(provider, "provider_name", "mock"),
                               getattr(provider, "model", "test-model"),
                               "manual provider selection")
            return RoutingResult(mode, route, provider, 1)

        candidates = self._verified_candidates(messages, streaming=streaming)
        estimated_context = max(512, sum(len(item["content"]) for item in messages) // 3 + 512)
        remote_allowed = self.env.get("NEXUS_ENABLE_REMOTE_PROVIDER", "false").strip().lower() == "true"
        route = self.router.choose(text, candidates, estimated_context=estimated_context,
                                   remote_allowed=remote_allowed)
        selected = next(item for item in candidates
                        if item["provider"] == route.provider and item["model"] == route.model)
        primary = selected["adapter"]
        lane_remote = selected["remote"]
        wrapped = [self.wrap_provider(primary)]
        failed = {f"{route.provider}/{route.model}"}
        eligible = [item for item in candidates
                    if item["remote"] is lane_remote
                    and (route.tier != "ADVANCED" or item["reasoning_score"] >= 1)
                    and (route.tier != "RESEARCH" or item["capabilities"].get("research") is True)]
        for _ in range(len(eligible) - 1):
            try:
                fallback = self.router.fallback(
                    eligible, failed=failed, remote=lane_remote,
                    max_cost_per_1k=selected["cost_per_1k"],
                    estimated_context=estimated_context)
            except NoRouteAvailable:
                break
            item = next(candidate for candidate in eligible
                        if candidate["provider"] == fallback.provider
                        and candidate["model"] == fallback.model)
            wrapped.append(self.wrap_provider(item["adapter"]))
            failed.add(f"{fallback.provider}/{fallback.model}")
        provider = wrapped[0] if len(wrapped) == 1 else FallbackProvider(wrapped)
        return RoutingResult(mode, route, provider, len(candidates))

    def _candidate_specs(self):
        raw = self.env.get("NEXUS_ROUTER_CANDIDATES", "").strip()
        if not raw or len(raw) > 16_384:
            raise NoRouteAvailable("Automatic routing has no valid candidate catalog.")
        try:
            values = json.loads(raw)
        except (json.JSONDecodeError, TypeError):
            raise NoRouteAvailable("Automatic routing has no valid candidate catalog.") from None
        if not isinstance(values, list) or not 1 <= len(values) <= self.MAX_CANDIDATES:
            raise NoRouteAvailable("Automatic routing has no valid candidate catalog.")
        return values

    def _verified_candidates(self, messages, *, streaming):
        raw_catalog = self.env.get("NEXUS_ROUTER_CANDIDATES", "")
        cache_key = (raw_catalog, streaming)
        cached = self._cache.get(cache_key)
        if cached and time.monotonic() - cached[0] < self.CACHE_SECONDS:
            candidates = cached[1]
        else:
            candidates = self._discover_candidates(self._candidate_specs(), streaming=streaming)
            self._cache = {cache_key: (time.monotonic(), candidates)}
        input_estimate = sum(len(item["content"]) for item in messages)
        output_estimate = int(self.env.get("NEXUS_ROUTER_MAX_OUTPUT_TOKENS", "800"))
        prepared = []
        for item in candidates:
            candidate = dict(item)
            if candidate["remote"]:
                candidate["budget_available"] = self.budget.can_reserve(
                    candidate["adapter"], input_estimate, output_estimate)
            prepared.append(candidate)
        return prepared

    def _discover_candidates(self, specs, *, streaming):
        discovered = []
        for spec in specs:
            if not isinstance(spec, dict) or set(spec) - self._candidate_keys:
                continue
            provider_name, model = spec.get("provider"), spec.get("model")
            context_window = spec.get("context_window")
            if (not isinstance(provider_name, str) or not isinstance(model, str)
                    or not provider_name or not model
                    or isinstance(context_window, bool) or not isinstance(context_window, int)
                    or not 512 <= context_window <= 2_000_000):
                continue
            caps = spec.get("capabilities")
            if not isinstance(caps, dict) or set(caps) - self._capability_keys:
                continue
            if caps.get("chat") is not True or streaming and caps.get("streaming") is not True:
                continue
            score = spec.get("reasoning_score", 0)
            latency = spec.get("latency_ms")
            if (isinstance(score, bool) or not isinstance(score, (int, float))
                    or score < 0 or score > 5
                    or isinstance(score, float) and not math.isfinite(score)
                    or latency is not None and (isinstance(latency, bool)
                        or not isinstance(latency, (int, float)) or latency < 0
                        or isinstance(latency, float) and not math.isfinite(latency))):
                continue
            remote = provider_name not in {"ollama", "mock"}
            try:
                adapter = self.manager.build(provider_name, model)
                listed = self.manager.list_models(provider_name)
                live = next((row for row in listed if row.get("id") == model), None)
                if live is None:
                    continue
                health = self.manager.check(provider_name)
                if health.get("available") is not True:
                    continue
                live_caps = live.get("capabilities") or {}
                if not isinstance(live_caps, dict):
                    continue
                if live_caps.get("chat") is False or streaming and live_caps.get("streaming") is False:
                    continue
                if streaming and not callable(getattr(adapter, "stream_generate", None)):
                    continue
                actual_context = live.get("context_window")
                effective_context = (min(context_window, actual_context)
                    if isinstance(actual_context, int) and not isinstance(actual_context, bool)
                    else context_window)
                budget_settings = self.budget.settings()
            except (ProviderError, KeyError, TypeError, ValueError):
                continue
            cost = 0.0
            if remote:
                # Ranking uses the configured, provider-wide estimate; reserve() remains the hard gate.
                budget_settings = self.budget.settings()
                cost = (budget_settings.get("input_usd_per_million", 0)
                        + budget_settings.get("output_usd_per_million", 0)) / 1000
            prepared = {"provider": provider_name, "model": model, "available": True,
                "allowed": not remote or self.manager._remote_enabled(provider_name),
                "remote": remote, "budget_available": not remote or budget_settings.get("enabled") is True,
                "context_window": effective_context, "reasoning_score": score,
                "latency_ms": latency, "cost_per_1k": cost,
                "capabilities": {**caps, "research": caps.get("research") is True
                    and self.env.get("NEXUS_TAVILY_ENABLED", "false").lower() == "true"
                    and bool(self.env.get("TAVILY_API_KEY"))}, "adapter": adapter}
            discovered.append(prepared)
        return discovered
