"""Optional provider adapters implemented with the Python standard library.

No adapter retries requests or executes tools. Cancellation is not supported by
urllib; the configured socket timeout is the hard transport bound available here.
"""
import json
import math
import re
from urllib.error import HTTPError, URLError
from urllib.parse import quote
from urllib.request import HTTPRedirectHandler, Request, build_opener

from .base import ModelResponse
from .errors import (ProviderAuthenticationError, ProviderConfigurationError,
                     ProviderError, ProviderModelNotFoundError, ProviderRateLimitError, ProviderResponseError,
                     ProviderTimeoutError, ProviderUnavailableError)


MODEL_RE = re.compile(r"^[A-Za-z0-9._:/-]{1,160}$")


class _NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


_safe_open = build_opener(_NoRedirect()).open


class HTTPModelProvider:
    provider_name = "abstract"
    endpoint = ""
    key_env = ""
    model_env = ""
    compatible_chat = True
    models_endpoint = ""

    def __init__(self, api_key, model, *, timeout=30, opener=None):
        if not api_key or not isinstance(api_key, str):
            raise ProviderConfigurationError()
        if model is not None and (not isinstance(model, str) or not MODEL_RE.fullmatch(model)):
            raise ProviderConfigurationError()
        if isinstance(timeout, bool) or not isinstance(timeout, (int, float)) or not math.isfinite(timeout) or not 0 < timeout <= 120:
            raise ProviderConfigurationError()
        self._api_key = api_key
        self.model = model
        self.default_timeout = float(timeout)
        self.opener = opener or _safe_open

    def _request(self, messages, max_tokens, timeout):
        if not self.model:
            raise ProviderConfigurationError()
        if not isinstance(messages, list) or not messages or any(
            not isinstance(m, dict) or m.get("role") not in {"system", "user", "assistant"}
            or not isinstance(m.get("content"), str) for m in messages
        ):
            raise ProviderResponseError()
        if isinstance(max_tokens, bool) or not isinstance(max_tokens, int) or not 1 <= max_tokens <= 8192:
            raise ProviderConfigurationError()
        if isinstance(timeout, bool) or not isinstance(timeout, (int, float)) or not math.isfinite(timeout) or not 0 < timeout <= 120:
            raise ProviderConfigurationError()
        payload = self._payload(messages, max_tokens)
        headers = {"Content-Type": "application/json", "Accept": "application/json"}
        headers.update(self._headers())
        request = Request(self.endpoint, data=json.dumps(payload).encode("utf-8"), headers=headers, method="POST")
        try:
            with self.opener(request, timeout=float(timeout)) as response:
                raw = response.read(1_000_000)
        except HTTPError as exc:
            if exc.code in (401, 403):
                raise ProviderAuthenticationError() from None
            if exc.code == 404:
                raise ProviderModelNotFoundError() from None
            if exc.code == 429:
                retry_after = None
                try:
                    parsed_retry = float(exc.headers.get("Retry-After"))
                    if math.isfinite(parsed_retry) and parsed_retry >= 0:
                        retry_after = parsed_retry
                except (TypeError, ValueError):
                    pass
                raise ProviderRateLimitError(retry_after=retry_after) from None
            if exc.code in (408, 504):
                raise ProviderTimeoutError() from None
            if exc.code >= 500:
                raise ProviderUnavailableError() from None
            raise ProviderResponseError() from None
        except TimeoutError:
            raise ProviderTimeoutError() from None
        except URLError as exc:
            if isinstance(getattr(exc, "reason", None), TimeoutError):
                raise ProviderTimeoutError() from None
            raise ProviderUnavailableError() from None
        except ProviderError:
            raise
        except Exception:
            raise ProviderUnavailableError() from None
        try:
            parsed = json.loads(raw.decode("utf-8"))
            text, input_tokens, output_tokens = self._parse_response(parsed)
        except ProviderError:
            raise
        except (UnicodeDecodeError, json.JSONDecodeError, KeyError, IndexError, TypeError, ValueError, AttributeError):
            raise ProviderResponseError() from None
        if not isinstance(text, str):
            raise ProviderResponseError()
        return ModelResponse(text, self.provider_name, self.model, input_tokens, output_tokens)

    def _headers(self):
        return {"Authorization": "Bearer " + self._api_key}

    def _payload(self, messages, max_tokens):
        return {"model": self.model, "messages": messages, "max_tokens": max_tokens,
                "stream": False}

    def _parse_response(self, parsed):
        usage = parsed.get("usage") or {}
        return (parsed["choices"][0]["message"]["content"],
                usage.get("prompt_tokens"), usage.get("completion_tokens"))

    def generate(self, messages, *, max_tokens=800, timeout=30):
        return self._request(messages, max_tokens, min(timeout, self.default_timeout))

    def _get_json(self, endpoint):
        request = Request(endpoint, headers={"Accept": "application/json", **self._headers()}, method="GET")
        try:
            with self.opener(request, timeout=self.default_timeout) as response:
                raw = response.read(2_000_000)
        except HTTPError as exc:
            if exc.code in (401, 403): raise ProviderAuthenticationError() from None
            if exc.code == 404: raise ProviderModelNotFoundError() from None
            if exc.code == 429: raise ProviderRateLimitError() from None
            if exc.code in (408, 504): raise ProviderTimeoutError() from None
            if exc.code >= 500: raise ProviderUnavailableError() from None
            raise ProviderResponseError() from None
        except (TimeoutError,):
            raise ProviderTimeoutError() from None
        except URLError as exc:
            if isinstance(getattr(exc, "reason", None), TimeoutError): raise ProviderTimeoutError() from None
            raise ProviderUnavailableError() from None
        except Exception:
            raise ProviderUnavailableError() from None
        try:
            return json.loads(raw.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError):
            raise ProviderResponseError() from None

    def list_models(self):
        if not self.models_endpoint:
            return []
        payload = self._get_json(self.models_endpoint)
        rows = payload.get("data") if isinstance(payload, dict) else None
        if not isinstance(rows, list):
            raise ProviderResponseError()
        models = []
        for row in rows:
            if not isinstance(row, dict) or not isinstance(row.get("id"), str):
                continue
            models.append({"id": row["id"], "name": row.get("name") or row["id"],
                           "context_window": row.get("context_length") or row.get("context_window"),
                           "capabilities": {"chat": None, "streaming": None, "tools": None,
                                            "vision": None, "embeddings": None}})
        return models

    def check_connection(self):
        models = self.list_models()
        return {"provider": self.provider_name, "available": True, "model_count": len(models)}

    def stream_generate(self, messages, *, max_tokens=800, timeout=60, cancel_event=None):
        if not self.model:
            raise ProviderConfigurationError()
        if not isinstance(messages, list) or not messages:
            raise ProviderResponseError()
        payload = self._payload(messages, max_tokens)
        payload["stream"] = True
        request = Request(self.endpoint, data=json.dumps(payload).encode("utf-8"),
                          headers={"Content-Type": "application/json", "Accept": "text/event-stream",
                                   **self._headers()}, method="POST")
        try:
            response = self.opener(request, timeout=min(float(timeout), self.default_timeout))
        except HTTPError as exc:
            if exc.code in (401, 403): raise ProviderAuthenticationError() from None
            if exc.code == 404: raise ProviderModelNotFoundError() from None
            if exc.code == 429: raise ProviderRateLimitError() from None
            if exc.code in (408, 504): raise ProviderTimeoutError() from None
            if exc.code >= 500: raise ProviderUnavailableError() from None
            raise ProviderResponseError() from None
        except TimeoutError:
            raise ProviderTimeoutError() from None
        except URLError as exc:
            if isinstance(getattr(exc, "reason", None), TimeoutError): raise ProviderTimeoutError() from None
            raise ProviderUnavailableError() from None
        try:
            for raw in response:
                if cancel_event is not None and cancel_event.is_set():
                    return
                try:
                    line = raw.decode("utf-8").strip()
                except UnicodeDecodeError:
                    raise ProviderResponseError() from None
                if not line.startswith("data:"):
                    continue
                data = line[5:].strip()
                if data == "[DONE]":
                    break
                try:
                    event = json.loads(data)
                except json.JSONDecodeError:
                    raise ProviderResponseError() from None
                delta = event.get("choices", [{}])[0].get("delta", {}).get("content")
                if delta:
                    yield delta
        finally:
            response.close()


class GroqProvider(HTTPModelProvider):
    provider_name = "groq"
    endpoint = "https://api.groq.com/openai/v1/chat/completions"


class OpenRouterProvider(HTTPModelProvider):
    provider_name = "openrouter"
    endpoint = "https://openrouter.ai/api/v1/chat/completions"
    models_endpoint = "https://openrouter.ai/api/v1/models"


class OpenAIProvider(HTTPModelProvider):
    provider_name = "openai"
    endpoint = "https://api.openai.com/v1/chat/completions"
    models_endpoint = "https://api.openai.com/v1/models"


class AnthropicProvider(HTTPModelProvider):
    provider_name = "anthropic"
    endpoint = "https://api.anthropic.com/v1/messages"
    models_endpoint = "https://api.anthropic.com/v1/models"

    def _headers(self):
        return {"x-api-key": self._api_key, "anthropic-version": "2023-06-01"}

    def _payload(self, messages, max_tokens):
        system = "\n".join(m["content"] for m in messages if m["role"] == "system")
        result = {"model": self.model, "max_tokens": max_tokens,
                  "messages": [{"role": m["role"], "content": m["content"]}
                               for m in messages if m["role"] != "system"]}
        if system:
            result["system"] = system
        return result

    def _parse_response(self, parsed):
        text = "".join(block.get("text", "") for block in parsed["content"]
                       if isinstance(block, dict) and block.get("type") == "text")
        usage = parsed.get("usage") or {}
        return text, usage.get("input_tokens"), usage.get("output_tokens")

    def list_models(self):
        payload = self._get_json(self.models_endpoint)
        rows = payload.get("data") if isinstance(payload, dict) else None
        if not isinstance(rows, list):
            raise ProviderResponseError()
        return [{"id": row["id"], "name": row.get("display_name") or row["id"],
                 "context_window": row.get("context_window"),
                 "capabilities": {"chat": True, "streaming": None, "tools": None,
                                  "vision": None, "embeddings": False}}
                for row in rows if isinstance(row, dict) and isinstance(row.get("id"), str)]

    def stream_generate(self, messages, *, max_tokens=800, timeout=60, cancel_event=None):
        if not self.model:
            raise ProviderConfigurationError()
        payload = self._payload(messages, max_tokens)
        payload["stream"] = True
        request = Request(self.endpoint, data=json.dumps(payload).encode("utf-8"),
                          headers={"Content-Type": "application/json", "Accept": "text/event-stream",
                                   **self._headers()}, method="POST")
        try:
            response = self.opener(request, timeout=min(float(timeout), self.default_timeout))
        except HTTPError as exc:
            if exc.code in (401, 403): raise ProviderAuthenticationError() from None
            if exc.code == 404: raise ProviderModelNotFoundError() from None
            if exc.code == 429: raise ProviderRateLimitError() from None
            if exc.code in (408, 504): raise ProviderTimeoutError() from None
            if exc.code >= 500: raise ProviderUnavailableError() from None
            raise ProviderResponseError() from None
        except TimeoutError:
            raise ProviderTimeoutError() from None
        except URLError as exc:
            if isinstance(getattr(exc, "reason", None), TimeoutError): raise ProviderTimeoutError() from None
            raise ProviderUnavailableError() from None
        try:
            for raw in response:
                if cancel_event is not None and cancel_event.is_set():
                    return
                if not raw.startswith(b"data:"):
                    continue
                try:
                    event = json.loads(raw[5:].decode("utf-8").strip())
                except (UnicodeDecodeError, json.JSONDecodeError):
                    raise ProviderResponseError() from None
                delta = event.get("delta") or {}
                if event.get("type") == "content_block_delta" and delta.get("type") == "text_delta":
                    yield delta.get("text", "")
        finally:
            response.close()


class GeminiProvider(HTTPModelProvider):
    provider_name = "gemini"
    endpoint = "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
    compatible_chat = False

    def __init__(self, api_key, model, *, embedding_model="gemini-embedding-001", **kwargs):
        if not isinstance(model, str) or not MODEL_RE.fullmatch(model):
            raise ProviderConfigurationError()
        if not isinstance(embedding_model, str) or not MODEL_RE.fullmatch(embedding_model):
            raise ProviderConfigurationError()
        self.embedding_model = embedding_model
        self.endpoint = self.endpoint.format(model=quote(model, safe=""))
        super().__init__(api_key, model, **kwargs)

    def _headers(self):
        return {"x-goog-api-key": self._api_key}

    def _payload(self, messages, max_tokens):
        system = "\n".join(m["content"] for m in messages if m["role"] == "system")
        contents = [{"role": "model" if m["role"] == "assistant" else "user",
                     "parts": [{"text": m["content"]}]}
                    for m in messages if m["role"] != "system"]
        result = {"contents": contents, "generationConfig": {"maxOutputTokens": max_tokens}}
        if system:
            result["systemInstruction"] = {"parts": [{"text": system}]}
        return result

    def _parse_response(self, parsed):
        text = "".join(part.get("text", "") for part in parsed["candidates"][0]["content"]["parts"])
        usage = parsed.get("usageMetadata") or {}
        return text, usage.get("promptTokenCount"), usage.get("candidatesTokenCount")

    def check_connection(self):
        endpoint = "https://generativelanguage.googleapis.com/v1beta/models"
        payload = self._get_json(endpoint)
        rows = payload.get("models") if isinstance(payload, dict) else None
        if not isinstance(rows, list):
            raise ProviderResponseError()
        models = [row for row in rows if isinstance(row, dict)
                  and "generateContent" in row.get("supportedGenerationMethods", [])]
        return {"provider": self.provider_name, "available": True, "model_count": len(models)}

    def list_models(self):
        payload = self._get_json("https://generativelanguage.googleapis.com/v1beta/models")
        rows = payload.get("models") if isinstance(payload, dict) else None
        if not isinstance(rows, list):
            raise ProviderResponseError()
        return [{"id": row["name"].removeprefix("models/"), "name": row.get("displayName") or row["name"],
                 "context_window": row.get("inputTokenLimit"),
                 "capabilities": {"chat": "generateContent" in row.get("supportedGenerationMethods", []),
                                  "streaming": "streamGenerateContent" in row.get("supportedGenerationMethods", []),
                                  "tools": None, "vision": None, "embeddings": "embedContent" in row.get("supportedGenerationMethods", [])}}
                for row in rows if isinstance(row, dict) and isinstance(row.get("name"), str)
                and "generateContent" in row.get("supportedGenerationMethods", [])]

    def stream_generate(self, messages, *, max_tokens=800, timeout=60, cancel_event=None):
        if not self.model:
            raise ProviderConfigurationError()
        endpoint = self.endpoint.replace(":generateContent", ":streamGenerateContent") + "?alt=sse"
        payload = self._payload(messages, max_tokens)
        request = Request(endpoint, data=json.dumps(payload).encode("utf-8"),
                          headers={"Content-Type": "application/json", "Accept": "text/event-stream",
                                   **self._headers()}, method="POST")
        try:
            response = self.opener(request, timeout=min(float(timeout), self.default_timeout))
        except HTTPError as exc:
            if exc.code in (401, 403): raise ProviderAuthenticationError() from None
            if exc.code == 429: raise ProviderRateLimitError() from None
            if exc.code in (408, 504): raise ProviderTimeoutError() from None
            if exc.code >= 500: raise ProviderUnavailableError() from None
            raise ProviderResponseError() from None
        except TimeoutError:
            raise ProviderTimeoutError() from None
        except URLError as exc:
            if isinstance(getattr(exc, "reason", None), TimeoutError): raise ProviderTimeoutError() from None
            raise ProviderUnavailableError() from None
        try:
            for raw in response:
                if cancel_event is not None and cancel_event.is_set():
                    return
                if not raw.startswith(b"data:"):
                    continue
                try:
                    event = json.loads(raw[5:].decode("utf-8").strip())
                except (UnicodeDecodeError, json.JSONDecodeError):
                    raise ProviderResponseError() from None
                for part in event.get("candidates", [{}])[0].get("content", {}).get("parts", []):
                    if isinstance(part, dict) and isinstance(part.get("text"), str):
                        yield part["text"]
        finally:
            response.close()

    def embed(self, text, *, title=None, task_type="RETRIEVAL_QUERY", timeout=30):
        """Create an embedding using Gemini's official embedContent endpoint."""
        if not isinstance(text, str) or not text.strip() or len(text) > 12_000:
            raise ProviderConfigurationError()
        if task_type not in {"RETRIEVAL_QUERY", "RETRIEVAL_DOCUMENT", "SEMANTIC_SIMILARITY"}:
            raise ProviderConfigurationError()
        from urllib.error import HTTPError, URLError
        from urllib.request import Request
        endpoint = "https://generativelanguage.googleapis.com/v1beta/models/" + quote(self.embedding_model, safe="") + ":embedContent"
        body = {"content": {"parts": [{"text": text.strip()}]},
                "embedContentConfig": {"taskType": task_type}}
        if title and task_type == "RETRIEVAL_DOCUMENT":
            body["embedContentConfig"]["title"] = str(title)[:500]
        request = Request(endpoint, data=json.dumps(body).encode("utf-8"),
                          headers={"Content-Type": "application/json", "Accept": "application/json",
                                   "x-goog-api-key": self._api_key}, method="POST")
        try:
            with self.opener(request, timeout=min(float(timeout), self.default_timeout)) as response:
                raw = response.read(1_000_000)
        except HTTPError as exc:
            if exc.code in (401, 403): raise ProviderAuthenticationError() from None
            if exc.code == 429: raise ProviderRateLimitError() from None
            if exc.code in (408, 504): raise ProviderTimeoutError() from None
            if exc.code >= 500: raise ProviderUnavailableError() from None
            raise ProviderResponseError() from None
        except TimeoutError: raise ProviderTimeoutError() from None
        except URLError as exc:
            if isinstance(getattr(exc, "reason", None), TimeoutError): raise ProviderTimeoutError() from None
            raise ProviderUnavailableError() from None
        except Exception: raise ProviderUnavailableError() from None
        try:
            parsed = json.loads(raw.decode("utf-8"))
            values = parsed["embedding"]["values"]
            if not isinstance(values, list) or not 1 <= len(values) <= 4096:
                raise ValueError()
            vector = [float(value) for value in values]
            if any(not math.isfinite(value) for value in vector): raise ValueError()
            return vector
        except (UnicodeDecodeError, json.JSONDecodeError, KeyError, TypeError, ValueError, AttributeError):
            raise ProviderResponseError() from None


def provider_from_env(environ=None):
    """Load explicitly selected provider; default stays offline MockProvider."""
    import os
    env = os.environ if environ is None else environ
    selected = env.get("NEXUS_PROVIDER", "mock").strip().lower()
    if selected == "mock":
        from .mock import MockProvider
        return MockProvider()
    if selected == "ollama":
        from .ollama import OllamaProvider
        try:
            return OllamaProvider(env.get("OLLAMA_BASE_URL", "http://127.0.0.1:11434"),
                model=env.get("OLLAMA_MODEL") or None,
                num_ctx=int(env.get("OLLAMA_NUM_CTX", "2048")),
                num_predict=int(env.get("OLLAMA_NUM_PREDICT", "384")),
                temperature=float(env.get("OLLAMA_TEMPERATURE", "0.2")),
                timeout=float(env.get("NEXUS_PROVIDER_TIMEOUT", "120")))
        except (ValueError, TypeError):
            raise ProviderConfigurationError() from None
    if env.get("NEXUS_ENABLE_REMOTE_PROVIDER", "false").strip().lower() != "true":
        raise ProviderConfigurationError()
    config = {
        "gemini": (GeminiProvider, "GEMINI_API_KEY", "GEMINI_MODEL"),
        "groq": (GroqProvider, "GROQ_API_KEY", "GROQ_MODEL"),
        "openrouter": (OpenRouterProvider, "OPENROUTER_API_KEY", "OPENROUTER_MODEL"),
        "openai": (OpenAIProvider, "OPENAI_API_KEY", "OPENAI_MODEL"),
        "anthropic": (AnthropicProvider, "ANTHROPIC_API_KEY", "ANTHROPIC_MODEL"),
    }
    if selected not in config:
        raise ProviderConfigurationError()
    # The global remote opt-in is necessary but not sufficient when an
    # allowlist is configured. An explicitly empty list denies every remote
    # provider. Keep None distinct for older deployments that only set the
    # global opt-in; ProviderManager remains the preferred selection path.
    configured_allowlist = env.get("NEXUS_REMOTE_PROVIDERS")
    if configured_allowlist is not None:
        allowed = {item.strip().lower() for item in configured_allowlist.split(",") if item.strip()}
        if selected not in allowed:
            raise ProviderConfigurationError()
    cls, key_var, model_var = config[selected]
    try:
        timeout = float(env.get("NEXUS_PROVIDER_TIMEOUT", "30"))
    except (TypeError, ValueError):
        raise ProviderConfigurationError() from None
    if selected == "gemini":
        return cls(env.get(key_var), env.get(model_var), timeout=timeout,
                   embedding_model=env.get("GEMINI_EMBEDDING_MODEL", "gemini-embedding-001"))
    return cls(env.get(key_var), env.get(model_var), timeout=timeout)
