"""Conservative, metadata-driven model routing; this module never calls providers."""
from dataclasses import dataclass
import math
import re
import unicodedata


class NoRouteAvailable(ValueError):
    """No candidate satisfies the task's capability, privacy, and budget limits."""


@dataclass(frozen=True)
class ModelRoute:
    tier: str
    provider: str
    model: str
    reason: str


class ModelRouter:
    """Select only among caller-supplied candidates with verified metadata."""

    _research = re.compile(
        r"\b(pesquis|busc|fontes?|referencias?|noticias?|clim|previs|temperaturas?|cotacoes?)\w*"
        r"|\btempo\b.{0,24}\bhoje\b|\bhoje\b.{0,24}\btempo\b", re.I)
    _advanced = re.compile(r"\b(compare|avalie|analisa|analise|planej|estrateg|riscos?|alternativas?|complex[oa])\w*", re.I)

    def classify(self, text, *, research=False, advanced=False):
        if not isinstance(text, str):
            raise ValueError("task text must be a string")
        normalized = "".join(character for character in
                              unicodedata.normalize("NFKD", text.lower())
                              if not unicodedata.combining(character))
        if research or self._research.search(normalized):
            return "RESEARCH"
        if advanced or self._advanced.search(normalized) or len(text) > 2500:
            return "ADVANCED"
        if len((text or "").split()) <= 3:
            return "SIMPLE"
        return "STANDARD"

    def choose(self, text, candidates, *, estimated_context=None,
               remote_allowed=False, research=False, advanced=False):
        tier = self.classify(text, research=research, advanced=advanced)
        requested_context = (max(512, len(text) // 3 + 512)
                             if estimated_context is None else estimated_context)
        if isinstance(requested_context, bool) or not isinstance(requested_context, int) or requested_context < 1:
            raise ValueError("estimated_context must be a positive integer")
        viable = []
        for candidate in candidates:
            if not isinstance(candidate, dict) or not all(
                    isinstance(candidate.get(key), str) and candidate[key]
                    for key in ("provider", "model")):
                continue
            if candidate.get("available") is not True or candidate.get("allowed") is not True:
                continue
            if candidate.get("remote") and (not remote_allowed or candidate.get("budget_available") is not True):
                continue
            context = candidate.get("context_window")
            if (isinstance(context, bool) or not isinstance(context, int)
                    or context < requested_context):
                continue
            capabilities = candidate.get("capabilities") or {}
            if not isinstance(capabilities, dict):
                continue
            if tier == "RESEARCH" and capabilities.get("research") is not True:
                continue
            score = candidate.get("reasoning_score", 0)
            if tier == "ADVANCED" and (isinstance(score, bool)
                    or not isinstance(score, (int, float)) or score < 1):
                continue
            viable.append(candidate)
        if not viable:
            raise NoRouteAvailable("No model satisfies the task constraints.")
        selected = min(viable, key=lambda item: self._rank(item, tier))
        return ModelRoute(tier, selected["provider"], selected["model"],
                          "selected from available candidates within privacy and budget limits")

    def fallback(self, candidates, *, failed, remote, max_cost_per_1k=None,
                 estimated_context=None):
        """Choose a viable alternate only within the original local/remote trust lane."""
        failed = set(failed)
        viable = [item for item in candidates if isinstance(item, dict)
                  and isinstance(item.get("provider"), str) and item["provider"]
                  and isinstance(item.get("model"), str) and item["model"]
                  and item.get("available") is True and item.get("allowed") is True
                  and bool(item.get("remote")) is bool(remote)
                  and (not remote or item.get("budget_available") is True)
                  and (estimated_context is None or
                       isinstance(item.get("context_window"), int) and
                       not isinstance(item.get("context_window"), bool) and
                       item["context_window"] >= estimated_context)
                  and (max_cost_per_1k is None or
                       self._number(item.get("cost_per_1k")) <= max_cost_per_1k)
                  and f"{item.get('provider')}/{item.get('model')}" not in failed]
        if not viable:
            raise NoRouteAvailable("No safe fallback is available.")
        selected = min(viable, key=lambda item: self._rank(item, "STANDARD"))
        return ModelRoute("STANDARD", selected["provider"], selected["model"],
                          "same-trust-lane fallback")

    @staticmethod
    def _rank(candidate, tier):
        cost = ModelRouter._number(candidate.get("cost_per_1k"))
        latency = ModelRouter._number(candidate.get("latency_ms"))
        reasoning = ModelRouter._number(candidate.get("reasoning_score", 0))
        if tier == "ADVANCED":
            return (-reasoning, cost, latency, candidate.get("provider", ""), candidate.get("model", ""))
        return (cost, latency, candidate.get("provider", ""), candidate.get("model", ""))

    @staticmethod
    def _number(value):
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            return float("inf")
        try:
            number = float(value)
        except (OverflowError, ValueError):
            return float("inf")
        return number if math.isfinite(number) and number >= 0 else float("inf")
