"""Persistent, secret-safe provider selection and construction."""
import os

from .adapters import (AnthropicProvider, GeminiProvider, GroqProvider,
                       OpenAIProvider, OpenRouterProvider)
from .errors import (ProviderAuthenticationError, ProviderConfigurationError,
                     ProviderError, ProviderModelNotFoundError,
                     ProviderUnavailableError)
from .mock import MockProvider
from .ollama import OllamaProvider


PROVIDERS = {
    "ollama": {"label": "Ollama", "key": None, "model_env": "OLLAMA_MODEL"},
    "openai": {"label": "OpenAI", "key": "OPENAI_API_KEY", "model_env": "OPENAI_MODEL"},
    "anthropic": {"label": "Anthropic", "key": "ANTHROPIC_API_KEY", "model_env": "ANTHROPIC_MODEL"},
    "gemini": {"label": "Google Gemini", "key": "GEMINI_API_KEY", "model_env": "GEMINI_MODEL"},
    "openrouter": {"label": "OpenRouter", "key": "OPENROUTER_API_KEY", "model_env": "OPENROUTER_MODEL"},
    "groq": {"label": "Groq", "key": "GROQ_API_KEY", "model_env": "GROQ_MODEL"},
    "mock": {"label": "MockProvider (desenvolvimento/testes)", "key": None, "model_env": None},
}


class UnavailableProvider:
    """Keeps the app online while making a selected-provider failure explicit."""
    def __init__(self, provider_name, model, error):
        self.provider_name, self.model, self.error = provider_name, model or "unconfigured", error

    def generate(self, messages, *, max_tokens=800, timeout=30):
        raise self.error


class ProviderManager:
    def __init__(self, engine, environ=None, *, injected_provider=None):
        self.engine = engine
        self.env = os.environ if environ is None else environ
        self.injected_provider = injected_provider
        self._health_cache = {}
        with engine.db() as connection:
            connection.execute("""CREATE TABLE IF NOT EXISTS provider_settings(
                id INTEGER PRIMARY KEY CHECK(id=1),provider TEXT NOT NULL,model TEXT,
                updated_at TEXT NOT NULL)""")
            initial_provider = (getattr(injected_provider, "provider_name", "mock")
                                if injected_provider is not None else
                                self.env.get("NEXUS_PROVIDER", "mock").strip().lower())
            initial_model = getattr(injected_provider, "model", None) if injected_provider else None
            if not injected_provider:
                initial_model = self.env.get(PROVIDERS.get(initial_provider, {}).get("model_env") or "", None)
            if initial_provider not in PROVIDERS:
                initial_provider = "mock"
            connection.execute("INSERT OR IGNORE INTO provider_settings VALUES(1,?,?,?)",
                               (initial_provider, initial_model, ""))

    def default(self):
        with self.engine.db() as connection:
            row = connection.execute("SELECT provider,model FROM provider_settings WHERE id=1").fetchone()
        return dict(row)

    def _model_from_env(self, name):
        variable = PROVIDERS[name]["model_env"]
        return self.env.get(variable) if variable else None

    def _remote_enabled(self, name):
        if self.env.get("NEXUS_ENABLE_REMOTE_PROVIDER", "false").strip().lower() != "true":
            return False
        allowlist = self.env.get("NEXUS_REMOTE_PROVIDERS")
        if allowlist is None:
            return True
        allowed = {item.strip().lower() for item in allowlist.split(",") if item.strip()}
        return name in allowed

    def build(self, name, model=None):
        if name not in PROVIDERS:
            raise ProviderConfigurationError()
        if self.injected_provider is not None:
            if name != getattr(self.injected_provider, "provider_name", "mock"):
                raise ProviderConfigurationError()
            return self.injected_provider
        model = model or self._model_from_env(name)
        try:
            timeout = float(self.env.get("NEXUS_PROVIDER_TIMEOUT", "60" if name == "ollama" else "30"))
        except (TypeError, ValueError):
            raise ProviderConfigurationError() from None
        if name == "ollama":
            try:
                num_ctx = int(self.env.get("OLLAMA_NUM_CTX", "2048"))
                num_predict = int(self.env.get("OLLAMA_NUM_PREDICT", "512"))
                temperature = float(self.env.get("OLLAMA_TEMPERATURE", "0.2"))
            except (TypeError, ValueError):
                raise ProviderConfigurationError() from None
            return OllamaProvider(self.env.get("OLLAMA_BASE_URL", "http://127.0.0.1:11434"),
                                  model=model, num_ctx=num_ctx, num_predict=num_predict,
                                  temperature=temperature,
                                  timeout=timeout)
        if name == "mock":
            if self.env.get("NEXUS_ENVIRONMENT", "development").lower() == "production":
                raise ProviderConfigurationError()
            return MockProvider()
        if not self._remote_enabled(name):
            raise ProviderConfigurationError()
        key_variable = PROVIDERS[name]["key"]
        key = self.env.get(key_variable, "")
        if not key:
            raise ProviderConfigurationError()
        if name == "gemini":
            return GeminiProvider(key, model or "list-only-model",
                                  embedding_model=self.env.get("GEMINI_EMBEDDING_MODEL", "gemini-embedding-001"),
                                  timeout=timeout)
        cls = {"openai": OpenAIProvider, "anthropic": AnthropicProvider,
               "openrouter": OpenRouterProvider, "groq": GroqProvider}[name]
        return cls(key, model, timeout=timeout)

    @staticmethod
    def _default_qwen(models):
        qwen = [item for item in models if "qwen" in item["id"].lower()]
        if not qwen:
            return None
        return min(qwen, key=lambda item: item.get("size") or float("inf"))["id"]

    def selected(self):
        config = self.default()
        model = config["model"]
        if config["provider"] == "ollama" and not model:
            adapter = self.build("ollama")
            model = self._default_qwen(adapter.list_models())
            if not model:
                raise ProviderModelNotFoundError()
        if config["provider"] == "ollama" and model:
            return self.build("ollama", model)
        if not model and config["provider"] != "mock":
            raise ProviderConfigurationError()
        return self.build(config["provider"], model)

    def unavailable(self, error):
        config = self.default()
        return UnavailableProvider(config["provider"], config["model"], error)

    def list_models(self, name):
        if name not in PROVIDERS:
            raise ProviderConfigurationError()
        if name == "mock":
            if self.injected_provider is not None:
                return [{"id": getattr(self.injected_provider, "model", "test-model"),
                         "name": "Provider de teste", "capabilities": {"chat": True}}]
            return [{"id": "offline-mock", "name": "MockProvider (testes/desenvolvimento)",
                     "capabilities": {"chat": True, "streaming": False}}]
        adapter = self.build(name, self._model_from_env(name))
        return adapter.list_models()

    def check(self, name):
        if name not in PROVIDERS:
            raise ProviderConfigurationError()
        try:
            adapter = self.build(name, self.default()["model"] if name == self.default()["provider"] else None)
            if name == "mock":
                result = {"provider": name, "available": False, "reason": "development_only"}
            elif name == "ollama":
                result = adapter.check_connection()
                result["models"] = adapter.list_models()
            else:
                result = adapter.check_connection()
            self._health_cache[name] = {"availability": "available" if result.get("available") else "offline",
                                        "checked_at": __import__("datetime").datetime.now(__import__("datetime").timezone.utc).isoformat(timespec="seconds")}
            return result
        except ProviderError as exc:
            self._health_cache[name] = {"availability": exc.code,
                                        "checked_at": __import__("datetime").datetime.now(__import__("datetime").timezone.utc).isoformat(timespec="seconds")}
            raise

    def status(self):
        selected = self.default()
        rows = []
        for name, spec in PROVIDERS.items():
            configured = bool(self.injected_provider is not None and
                              name == getattr(self.injected_provider, "provider_name", "mock"))
            if self.injected_provider is None:
                configured = (name == "ollama" or name == "mock" or
                              bool(self.env.get(spec["key"], "")) if spec["key"] else True)
            remote_enabled = self._remote_enabled(name)
            remote_credential = bool(self.env.get(spec["key"], "")) if spec["key"] else True
            if name not in {"ollama", "mock"} and self.injected_provider is None:
                configured = remote_enabled and remote_credential
            row = {"id": name, "name": spec["label"], "configured": configured,
                   "credential_configured": (remote_credential if spec["key"] else None),
                   "enabled": (name in {"ollama", "mock"} or remote_enabled),
                   "selected": selected["provider"] == name,
                   "model": selected["model"] if selected["provider"] == name else self._model_from_env(name),
                   "availability": ("not_checked" if configured else
                                    "disabled" if remote_credential and name not in {"ollama", "mock"} and not remote_enabled
                                    else "not_configured")}
            if name in self._health_cache:
                row.update(self._health_cache[name])
            if name == "ollama" and configured:
                try:
                    adapter = self.build(name, row["model"])
                    connection = adapter.check_connection()
                    models = adapter.list_models()
                    row["availability"] = "available"
                    row["models_count"] = len(models)
                    row["installed_models"] = [m["id"] for m in models]
                    row["loaded_models"] = connection.get("loaded_models", [])
                    row["version"] = connection.get("version")
                    if not row["model"]:
                        row["suggested_model"] = self._default_qwen(models)
                except ProviderError as exc:
                    row["availability"] = exc.code
            rows.append(row)
        return {"default": selected, "providers": rows}

    def select(self, name, model):
        if name not in PROVIDERS or name == "mock" and self.env.get("NEXUS_ENVIRONMENT", "development").lower() == "production":
            raise ProviderConfigurationError()
        models = self.list_models(name)
        if not any(item["id"] == model for item in models):
            raise ProviderModelNotFoundError()
        from ..engine import now
        with self.engine.db() as connection:
            connection.execute("UPDATE provider_settings SET provider=?,model=?,updated_at=? WHERE id=1",
                               (name, model, now()))
        return {"provider": name, "model": model}
