import io
import json
import unittest
from urllib.error import HTTPError

from nexus_learning.providers.adapters import (AnthropicProvider, GeminiProvider, GroqProvider,
    OpenAIProvider, provider_from_env)
from nexus_learning.providers.errors import (ProviderAuthenticationError,
    ProviderConfigurationError, ProviderRateLimitError, ProviderResponseError)


class ProvidersHTTPTests(unittest.TestCase):
    def test_gemini_adapter_maps_roles_and_uses_header_credential(self):
        seen = {}
        def opener(request, timeout):
            seen["request"] = request
            seen["payload"] = json.loads(request.data)
            seen["timeout"] = timeout
            return io.BytesIO(json.dumps({"candidates": [{"content": {"parts": [{"text": "ok"}]}}],
                                          "usageMetadata": {"promptTokenCount": 3, "candidatesTokenCount": 1}}).encode())
        provider = GeminiProvider("fake-key", "gemini-test", opener=opener)
        response = provider.generate([{"role": "system", "content": "safe"},
                                      {"role": "user", "content": "question"}], timeout=4)
        self.assertEqual(response.text, "ok")
        self.assertEqual(response.provider, "gemini")
        self.assertEqual(response.input_tokens, 3)
        self.assertEqual(seen["request"].get_header("X-goog-api-key"), "fake-key")
        self.assertNotIn("fake-key", seen["request"].full_url)
        self.assertEqual(seen["payload"]["contents"][0]["role"], "user")
        self.assertEqual(seen["timeout"], 4.0)

    def test_gemini_connection_check_only_lists_models(self):
        seen=[]
        def opener(request,timeout):
            seen.append(request)
            return io.BytesIO(json.dumps({"models":[
                {"name":"models/gemini-test","supportedGenerationMethods":["generateContent"]},
                {"name":"models/embed-test","supportedGenerationMethods":["embedContent"]}
            ]}).encode())
        provider=GeminiProvider("fake-key","gemini-test",opener=opener)
        result=provider.check_connection()
        self.assertEqual(result,{"provider":"gemini","available":True,"model_count":1})
        self.assertEqual(seen[0].method,"GET")
        self.assertEqual(seen[0].full_url,"https://generativelanguage.googleapis.com/v1beta/models")
        self.assertEqual(seen[0].get_header("X-goog-api-key"),"fake-key")

    def test_gemini_embedding_uses_official_endpoint_and_validates_vectors(self):
        seen={}
        def opener(request,timeout):
            seen['request']=request; seen['payload']=json.loads(request.data)
            return io.BytesIO(json.dumps({'embedding':{'values':[0.1,-0.2,0.3]}}).encode())
        provider=GeminiProvider('fake-key','gemini-test',opener=opener)
        vector=provider.embed('retrieval text',title='Memory title',task_type='RETRIEVAL_DOCUMENT')
        self.assertEqual(vector,[0.1,-0.2,0.3])
        self.assertTrue(seen['request'].full_url.endswith('models/gemini-embedding-001:embedContent'))
        self.assertEqual(seen['payload']['embedContentConfig']['taskType'],'RETRIEVAL_DOCUMENT')
        self.assertEqual(seen['payload']['embedContentConfig']['title'],'Memory title')
        self.assertEqual(seen['request'].get_header('X-goog-api-key'),'fake-key')

    def test_http_errors_are_normalized_without_body_leakage(self):
        def rate_limited(request, timeout):
            raise HTTPError(request.full_url, 429, "", {"Retry-After": "2.5"}, io.BytesIO(b"secret body"))
        provider = GroqProvider("fake-key", "fake-model", opener=rate_limited)
        with self.assertRaises(ProviderRateLimitError) as caught:
            provider.generate([{"role": "user", "content": "hi"}])
        self.assertEqual(caught.exception.retry_after, 2.5)

        def denied(request, timeout):
            raise HTTPError(request.full_url, 401, "", {}, io.BytesIO(b"secret body"))
        provider.opener = denied
        with self.assertRaises(ProviderAuthenticationError) as caught:
            provider.generate([{"role": "user", "content": "hi"}])
        self.assertNotIn("secret", str(caught.exception))

    def test_external_configuration_requires_explicit_provider_credentials(self):
        self.assertEqual(type(provider_from_env({})).__name__, "MockProvider")
        with self.assertRaises(ProviderConfigurationError):
            provider_from_env({"NEXUS_PROVIDER": "groq"})
        with self.assertRaises(ProviderConfigurationError):
            provider_from_env({"NEXUS_PROVIDER": "groq", "GROQ_API_KEY": "fake",
                               "GROQ_MODEL": "model-test"})
        configured = provider_from_env({"NEXUS_PROVIDER": "groq", "GROQ_API_KEY": "fake",
                                        "GROQ_MODEL": "model-test",
                                        "NEXUS_ENABLE_REMOTE_PROVIDER": "true"})
        self.assertEqual(configured.provider_name, "groq")

    def test_gemini_and_openai_env_adapters_require_explicit_remote_allowlist(self):
        for provider, key_name, model_name, adapter in (
            ("gemini", "GEMINI_API_KEY", "GEMINI_MODEL", GeminiProvider),
            ("openai", "OPENAI_API_KEY", "OPENAI_MODEL", OpenAIProvider),
        ):
            base = {"NEXUS_PROVIDER": provider, key_name: "test-only-key",
                    model_name: "test-model", "NEXUS_ENABLE_REMOTE_PROVIDER": "true"}
            with self.subTest(provider=provider, case="allowlisted"):
                configured = provider_from_env({**base, "NEXUS_REMOTE_PROVIDERS": provider})
                self.assertIsInstance(configured, adapter)
            for allowlist in ("", "ollama"):
                with self.subTest(provider=provider, allowlist=allowlist):
                    with self.assertRaises(ProviderConfigurationError):
                        provider_from_env({**base, "NEXUS_REMOTE_PROVIDERS": allowlist})

    def test_gemini_streaming_parses_events_and_closes_response(self):
        class Stream(io.BytesIO):
            closed_by_adapter = False
            def close(self):
                self.closed_by_adapter = True
                super().close()

        seen = {}
        def opener(request, timeout):
            seen["request"] = request
            seen["timeout"] = timeout
            seen["response"] = Stream(
                b'event: message\ndata: {"candidates":[{"content":{"parts":[{"text":"Oi"}]}}]}\n\n'
            )
            return seen["response"]

        provider = GeminiProvider("test-only-key", "gemini-test", opener=opener)
        self.assertEqual(list(provider.stream_generate([{"role": "user", "content": "oi"}])), ["Oi"])
        self.assertTrue(seen["request"].full_url.endswith("streamGenerateContent?alt=sse"))
        self.assertEqual(seen["request"].get_header("X-goog-api-key"), "test-only-key")
        self.assertTrue(seen["response"].closed_by_adapter)

    def test_openai_streaming_parses_sse_and_closes_response(self):
        class Stream(io.BytesIO):
            closed_by_adapter = False
            def close(self):
                self.closed_by_adapter = True
                super().close()

        seen = {}
        def opener(request, timeout):
            seen["request"] = request
            seen["payload"] = json.loads(request.data)
            seen["response"] = Stream(
                b'data: {"choices":[{"delta":{"content":"Hello"}}]}\n\n'
                b'data: [DONE]\n\n'
            )
            return seen["response"]

        provider = OpenAIProvider("test-only-key", "gpt-test", opener=opener)
        self.assertEqual(list(provider.stream_generate([{"role": "user", "content": "hi"}])), ["Hello"])
        self.assertEqual(seen["request"].get_header("Authorization"), "Bearer test-only-key")
        self.assertTrue(seen["payload"]["stream"])
        self.assertTrue(seen["response"].closed_by_adapter)

    def test_malformed_usage_payload_is_normalized(self):
        def opener(request, timeout):
            payload = {"choices": [{"message": {"content": "ok"}}], "usage": ["malformed"]}
            return io.BytesIO(json.dumps(payload).encode())
        provider = GroqProvider("fake", "model", opener=opener)
        with self.assertRaises(ProviderResponseError):
            provider.generate([{"role": "user", "content": "hi"}])

    def test_openai_model_discovery_and_chat_are_secret_safe(self):
        seen = []
        def opener(request, timeout):
            seen.append(request)
            if request.method == "GET":
                return io.BytesIO(json.dumps({"data": [{"id": "gpt-test", "context_length": 8192}]}).encode())
            return io.BytesIO(json.dumps({"choices": [{"message": {"content": "hello"}}]}).encode())
        provider = OpenAIProvider("fake-openai-key", None, opener=opener)
        self.assertEqual(provider.list_models()[0]["id"], "gpt-test")
        provider.model = "gpt-test"
        response = provider.generate([{"role": "user", "content": "hi"}])
        self.assertEqual(response.provider, "openai")
        self.assertEqual(seen[0].get_header("Authorization"), "Bearer fake-openai-key")
        self.assertNotIn("fake-openai-key", seen[0].full_url)

    def test_anthropic_headers_payload_and_server_sent_stream(self):
        seen = {}
        def opener(request, timeout):
            seen["request"] = request
            seen["payload"] = json.loads(request.data)
            if seen["payload"].get("stream"):
                return io.BytesIO(b'event: content_block_delta\ndata: {"type":"content_block_delta","delta":{"type":"text_delta","text":"Oi"}}\n\n')
            return io.BytesIO(json.dumps({"content": [{"type": "text", "text": "Oi"}],
                                          "usage": {"input_tokens": 2, "output_tokens": 1}}).encode())
        provider = AnthropicProvider("fake-anthropic-key", "claude-test", opener=opener)
        result = provider.generate([{"role": "system", "content": "context"},
                                    {"role": "user", "content": "hi"}])
        self.assertEqual(result.text, "Oi")
        self.assertEqual(result.input_tokens, 2)
        self.assertEqual(seen["payload"]["system"], "context")
        self.assertEqual(seen["request"].get_header("X-api-key"), "fake-anthropic-key")
        self.assertEqual(list(provider.stream_generate([{"role": "user", "content": "hi"}])), ["Oi"])


if __name__ == "__main__":
    unittest.main()
