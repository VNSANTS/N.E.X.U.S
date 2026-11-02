"""Local-only Ollama adapter with bounded requests and cancellable streaming."""
import json
import math
from urllib.error import HTTPError, URLError
from urllib.parse import urlsplit
from urllib.request import HTTPRedirectHandler, Request, build_opener

from .base import ModelResponse
from .errors import (ProviderConfigurationError, ProviderModelNotFoundError,
                     ProviderRateLimitError, ProviderResponseError,
                     ProviderTimeoutError, ProviderUnavailableError)


class _NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


_open = build_opener(_NoRedirect()).open


class OllamaProvider:
    provider_name = "ollama"

    def __init__(self, base_url="http://127.0.0.1:11434", model=None, *,
                 num_ctx=2048, num_predict=800, temperature=0.2, timeout=120, opener=None):
        if not isinstance(base_url, str) or len(base_url) > 300:
            raise ProviderConfigurationError()
        parsed = urlsplit(base_url.rstrip("/"))
        if (parsed.scheme != "http" or parsed.hostname not in {"127.0.0.1", "localhost", "::1"}
                or parsed.username or parsed.password or parsed.query or parsed.fragment):
            raise ProviderConfigurationError()
        if model is not None and (not isinstance(model, str) or not 1 <= len(model) <= 160):
            raise ProviderConfigurationError()
        if isinstance(num_ctx, bool) or not isinstance(num_ctx, int) or not 256 <= num_ctx <= 32768:
            raise ProviderConfigurationError()
        if isinstance(num_predict, bool) or not isinstance(num_predict, int) or not 1 <= num_predict <= 8192:
            raise ProviderConfigurationError()
        if isinstance(temperature, bool) or not isinstance(temperature, (int, float)) or not math.isfinite(temperature) or not 0 <= temperature <= 2:
            raise ProviderConfigurationError()
        if isinstance(timeout, bool) or not isinstance(timeout, (int, float)) or not math.isfinite(timeout) or not 1 <= timeout <= 300:
            raise ProviderConfigurationError()
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.num_ctx = num_ctx
        self.num_predict = num_predict
        self.temperature = float(temperature)
        self.default_timeout = float(timeout)
        self.opener = opener or _open

    def _request(self, path, *, payload=None, timeout=None, stream=False):
        data = None if payload is None else json.dumps(payload).encode("utf-8")
        request = Request(self.base_url + path, data=data,
                          headers={"Accept": "application/x-ndjson" if stream else "application/json",
                                   "Content-Type": "application/json"},
                          method="GET" if payload is None else "POST")
        try:
            return self.opener(request, timeout=min(float(timeout or self.default_timeout), self.default_timeout))
        except HTTPError as exc:
            if exc.code == 404:
                raise ProviderModelNotFoundError() from None
            if exc.code == 429:
                raise ProviderRateLimitError() from None
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
        except (ProviderConfigurationError, ProviderModelNotFoundError,
                ProviderRateLimitError, ProviderResponseError,
                ProviderTimeoutError, ProviderUnavailableError):
            raise
        except Exception:
            raise ProviderUnavailableError() from None

    def check_connection(self):
        with self._request("/api/version", timeout=min(5, self.default_timeout)) as response:
            try:
                payload = json.loads(response.read(64_000).decode("utf-8"))
            except (UnicodeDecodeError, json.JSONDecodeError):
                raise ProviderResponseError() from None
        if not isinstance(payload, dict) or not isinstance(payload.get("version"), str):
            raise ProviderResponseError()
        return {"provider": self.provider_name, "available": True, "version": payload["version"],
                "loaded_models": self.loaded_models()}

    def loaded_models(self):
        with self._request("/api/ps", timeout=min(5, self.default_timeout)) as response:
            try:
                payload = json.loads(response.read(256_000).decode("utf-8"))
            except (UnicodeDecodeError, json.JSONDecodeError):
                raise ProviderResponseError() from None
        rows = payload.get("models") if isinstance(payload, dict) else None
        if not isinstance(rows, list):
            raise ProviderResponseError()
        return [row.get("name") for row in rows if isinstance(row, dict) and isinstance(row.get("name"), str)]

    def list_models(self):
        with self._request("/api/tags", timeout=min(10, self.default_timeout)) as response:
            payload = json.loads(response.read(1_000_000).decode("utf-8"))
        rows = payload.get("models") if isinstance(payload, dict) else None
        if not isinstance(rows, list):
            raise ProviderResponseError()
        result = []
        for item in rows:
            if not isinstance(item, dict) or not isinstance(item.get("name"), str):
                continue
            result.append({"id": item["name"], "name": item["name"],
                           "size": item.get("size"), "modified_at": item.get("modified_at"),
                           "capabilities": {"chat": True, "streaming": True,
                                            "tools": None, "vision": None, "embeddings": None}})
        return result

    def generate(self, messages, *, max_tokens=None, timeout=120):
        if not self.model:
            raise ProviderConfigurationError()
        if not isinstance(messages, list) or not messages or any(
            not isinstance(m, dict) or m.get("role") not in {"system", "user", "assistant"}
            or not isinstance(m.get("content"), str) for m in messages
        ):
            raise ProviderResponseError()
        output_limit = self.num_predict if max_tokens is None else max_tokens
        if isinstance(output_limit, bool) or not isinstance(output_limit, int) or not 1 <= output_limit <= 8192:
            raise ProviderConfigurationError()
        response = self._request("/api/chat", payload={
            "model": self.model, "messages": messages, "stream": False,
            "options": {"num_ctx": self.num_ctx, "num_predict": output_limit,
                        "temperature": self.temperature},
        }, timeout=timeout)
        with response:
            try:
                data = json.loads(response.read(2_000_000).decode("utf-8"))
            except (UnicodeDecodeError, json.JSONDecodeError):
                raise ProviderResponseError() from None
        message = data.get("message") if isinstance(data, dict) else None
        text = message.get("content") if isinstance(message, dict) else None
        if not isinstance(text, str) or not text:
            raise ProviderResponseError()
        return ModelResponse(text, self.provider_name, data.get("model") or self.model,
                             data.get("prompt_eval_count"), data.get("eval_count"))

    def stream_generate(self, messages, *, max_tokens=None, timeout=120, cancel_event=None):
        """Yield text deltas; closing the iterator closes the HTTP response/socket."""
        if not self.model:
            raise ProviderConfigurationError()
        output_limit = self.num_predict if max_tokens is None else max_tokens
        if isinstance(output_limit, bool) or not isinstance(output_limit, int) or not 1 <= output_limit <= 8192:
            raise ProviderConfigurationError()
        response = self._request("/api/chat", payload={
            "model": self.model, "messages": messages, "stream": True,
            "options": {"num_ctx": self.num_ctx, "num_predict": output_limit,
                        "temperature": self.temperature},
        }, timeout=timeout, stream=True)
        try:
            for raw in response:
                if cancel_event is not None and cancel_event.is_set():
                    return
                if not raw.strip():
                    continue
                try:
                    event = json.loads(raw.decode("utf-8"))
                except (UnicodeDecodeError, json.JSONDecodeError):
                    raise ProviderResponseError() from None
                if event.get("error"):
                    error = str(event["error"]).lower()
                    if "not found" in error or "does not exist" in error:
                        raise ProviderModelNotFoundError()
                    if "memory" in error or "load model" in error:
                        raise ProviderUnavailableError()
                    raise ProviderResponseError()
                message = event.get("message") or {}
                text = message.get("content")
                if text:
                    if not isinstance(text, str):
                        raise ProviderResponseError()
                    yield text
                if event.get("done"):
                    break
        finally:
            response.close()
