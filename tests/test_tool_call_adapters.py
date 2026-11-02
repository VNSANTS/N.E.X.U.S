import io
import json
import unittest

from nexus_learning.providers.adapters import OpenAIProvider, GeminiProvider, AnthropicProvider
from nexus_learning.providers.ollama import OllamaProvider
from nexus_learning.providers.errors import ProviderResponseError


TOOLS = [{"type": "function", "function": {
    "name": "memory.search", "description": "Search memory",
    "parameters": {"type": "object", "properties": {"query": {"type": "string"}},
                   "required": ["query"], "additionalProperties": False}}}]


class ToolCallAdapterTests(unittest.TestCase):
    def test_openai_compatible_request_and_response_normalization(self):
        seen = {}
        def opener(request, timeout):
            seen["payload"] = json.loads(request.data)
            return io.BytesIO(json.dumps({"choices": [{"message": {
                "content": None, "tool_calls": [{"id": "call-1", "type": "function",
                    "function": {"name": "memory.search", "arguments": "{\"query\":\"x\"}"}}]}}],
                "usage": {"prompt_tokens": 3, "completion_tokens": 1}}).encode())
        provider = OpenAIProvider("offline-test", "model-test", opener=opener)
        response = provider.generate([{"role": "user", "content": "find"}], tools=TOOLS)
        self.assertEqual(seen["payload"]["tool_choice"], "auto")
        self.assertEqual(response.tool_calls[0].name, "memory.search")
        self.assertEqual(response.tool_calls[0].arguments, {"query": "x"})

    def test_ollama_request_and_response_normalization(self):
        seen = {}
        class Response(io.BytesIO):
            pass
        def opener(request, timeout):
            seen["payload"] = json.loads(request.data)
            return Response(json.dumps({"model": "qwen-test", "message": {
                "role": "assistant", "content": "", "tool_calls": [{"function": {
                    "name": "memory.search", "arguments": {"query": "x"}}}]}}).encode())
        provider = OllamaProvider(model="qwen-test", opener=opener)
        response = provider.generate([{"role": "user", "content": "find"}], tools=TOOLS)
        self.assertEqual(seen["payload"]["tools"], TOOLS)
        self.assertEqual(response.tool_calls[0].arguments, {"query": "x"})

    def test_ollama_generates_unique_ids_for_calls_across_turns(self):
        def opener(request, timeout):
            return io.BytesIO(json.dumps({"model": "qwen-test", "message": {
                "role": "assistant", "content": "", "tool_calls": [{"function": {
                    "name": "memory.search", "arguments": {"query": "x"}}}]}}).encode())
        provider = OllamaProvider(model="qwen-test", opener=opener)
        message = [{"role": "user", "content": "find"}]
        first = provider.generate(message, tools=TOOLS).tool_calls[0]
        second = provider.generate(message, tools=TOOLS).tool_calls[0]
        self.assertNotEqual(first.id, second.id)

    def test_gemini_and_anthropic_expose_native_tools(self):
        self.assertTrue(GeminiProvider("fake", "gemini-test").supports_tools)
        self.assertTrue(AnthropicProvider("fake", "claude-test").supports_tools)

    def test_malformed_provider_arguments_are_rejected(self):
        def opener(request, timeout):
            return io.BytesIO(json.dumps({"choices": [{"message": {"content": None,
                "tool_calls": [{"id": "x", "function": {"name": "memory.search",
                                        "arguments": "[]"}}]}}]}).encode())
        with self.assertRaises(ProviderResponseError):
            OpenAIProvider("fake", "model", opener=opener).generate(
                [{"role": "user", "content": "x"}], tools=TOOLS)

    def test_anthropic_tool_call_preserves_original_assistant_blocks_on_continuation(self):
        seen=[]
        def opener(request, timeout):
            payload=json.loads(request.data); seen.append(payload)
            if len(seen)==1:
                return io.BytesIO(json.dumps({"content":[{"type":"text","text":"Searching"},
                    {"type":"tool_use","id":"use-1","name":"memory.search","input":{"query":"x"}}],
                    "stop_reason":"tool_use"}).encode())
            return io.BytesIO(json.dumps({"content":[{"type":"text","text":"Done"}]}).encode())
        provider=AnthropicProvider("test-key","claude-test",opener=opener)
        first=provider.generate([{"role":"user","content":"find"}],tools=TOOLS)
        self.assertEqual(first.tool_calls[0].provider_data["anthropic_content"][0]["text"],"Searching")
        messages=[{"role":"user","content":"find"},
                  {"role":"assistant","content":first.text,"tool_calls":[
                    {"id":first.tool_calls[0].id,"name":"memory.search","arguments":{"query":"x"}}],
                   "provider_data":first.tool_calls[0].provider_data},
                  {"role":"tool","tool_call_id":"use-1","name":"memory.search","content":"result"}]
        provider.generate(messages,tools=TOOLS)
        self.assertEqual(seen[1]["messages"][1]["content"][0]["type"],"text")
        self.assertEqual(seen[1]["messages"][1]["content"][1]["type"],"tool_use")
        self.assertEqual(seen[1]["messages"][2]["content"][0]["tool_use_id"],"use-1")
        self.assertEqual(seen[1]["tools"][0]["input_schema"],TOOLS[0]["function"]["parameters"])

    def test_gemini_tool_call_preserves_original_model_parts_on_continuation(self):
        seen=[]
        signature={"functionCall":{"name":"memory.search","args":{"query":"x"}},
                   "thoughtSignature":"opaque-signature"}
        def opener(request, timeout):
            payload=json.loads(request.data); seen.append(payload)
            if len(seen)==1:
                body={"candidates":[{"content":{"role":"model","parts":[{"text":"Searching"},signature]}}]}
            else:
                body={"candidates":[{"content":{"role":"model","parts":[{"text":"Done"}]}}]}
            return io.BytesIO(json.dumps(body).encode())
        provider=GeminiProvider("test-key","gemini-test",opener=opener)
        first=provider.generate([{"role":"user","content":"find"}],tools=TOOLS)
        self.assertEqual(first.tool_calls[0].provider_data["gemini_content"][1]["thoughtSignature"],
                         "opaque-signature")
        messages=[{"role":"user","content":"find"},
                  {"role":"assistant","content":first.text,"tool_calls":[
                    {"id":first.tool_calls[0].id,"name":"memory.search","arguments":{"query":"x"}}],
                   "provider_data":first.tool_calls[0].provider_data},
                  {"role":"tool","tool_call_id":first.tool_calls[0].id,
                   "name":"memory.search","content":"result"}]
        provider.generate(messages,tools=TOOLS)
        self.assertEqual(seen[1]["contents"][1]["parts"][1]["thoughtSignature"],"opaque-signature")
        response=seen[1]["contents"][2]["parts"][0]["functionResponse"]
        self.assertEqual(response["name"],"memory.search")
        self.assertEqual(response["response"]["result"],"result")
        declaration=seen[0]["tools"][0]["functionDeclarations"][0]
        self.assertEqual(declaration["name"],"memory.search")


if __name__ == "__main__":
    unittest.main()
