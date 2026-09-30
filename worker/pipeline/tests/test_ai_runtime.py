from __future__ import annotations

import os
import json
import unittest
from unittest.mock import MagicMock, patch

from worker.pipeline.fpds_ai_runtime import configured_model_id, invoke_openai_json_schema


class AiRuntimeTests(unittest.TestCase):
    def test_default_model_is_gpt_6_luna(self) -> None:
        with patch.dict(os.environ, {}, clear=True):
            self.assertEqual(configured_model_id(), "gpt-6-luna")

    def test_configured_model_overrides_default(self) -> None:
        with patch.dict(os.environ, {"FPDS_LLM_MODEL": "test-model"}, clear=True):
            self.assertEqual(configured_model_id(), "test-model")

    def test_responses_request_sends_explicit_medium_reasoning_effort(self) -> None:
        response = MagicMock()
        response.read.return_value = json.dumps(
            {
                "id": "resp-test-001",
                "model": "gpt-6-luna",
                "output": [{"type": "message", "content": [{"type": "output_text", "text": '{"result":"ok"}'}]}],
                "usage": {"input_tokens": 1, "output_tokens": 1},
            }
        ).encode("utf-8")

        with (
            patch.dict(os.environ, {"FPDS_LLM_PROVIDER": "openai", "FPDS_LLM_API_KEY": "test-key"}, clear=True),
            patch("worker.pipeline.fpds_ai_runtime.urllib.request.urlopen") as urlopen,
        ):
            urlopen.return_value.__enter__.return_value = response
            result, metadata = invoke_openai_json_schema(
                instructions="Return a result.",
                payload={"input": "test"},
                schema_name="test_result",
                schema={"type": "object", "additionalProperties": False, "properties": {"result": {"type": "string"}}, "required": ["result"]},
            )

        request_body = json.loads(urlopen.call_args.args[0].data.decode("utf-8"))
        self.assertEqual(request_body["model"], "gpt-6-luna")
        self.assertEqual(request_body["reasoning"], {"effort": "medium"})
        self.assertEqual(result, {"result": "ok"})
        self.assertEqual(metadata["model_id"], "gpt-6-luna")

    def test_responses_request_can_force_domain_restricted_web_search(self) -> None:
        response = MagicMock()
        response.read.return_value = json.dumps(
            {
                "id": "resp-test-002",
                "model": "test-model",
                "output": [
                    {
                        "type": "web_search_call",
                        "action": {
                            "type": "search",
                            "sources": [
                                {"url": "https://bank.example/rates", "title": "Official rates"},
                            ],
                        },
                    },
                    {
                        "type": "message",
                        "content": [
                            {
                                "type": "output_text",
                                "text": '{"result":"verified"}',
                                "annotations": [
                                    {
                                        "type": "url_citation",
                                        "url": "https://bank.example/rates",
                                        "title": "Official rates",
                                    }
                                ],
                            }
                        ],
                    },
                ],
                "usage": {"input_tokens": 10, "output_tokens": 5},
            }
        ).encode("utf-8")

        with (
            patch.dict(
                os.environ,
                {
                    "FPDS_LLM_PROVIDER": "openai",
                    "FPDS_LLM_API_KEY": "test-key",
                    "FPDS_LLM_MODEL": "test-model",
                },
                clear=True,
            ),
            patch("worker.pipeline.fpds_ai_runtime.urllib.request.urlopen") as urlopen,
        ):
            urlopen.return_value.__enter__.return_value = response
            result, metadata = invoke_openai_json_schema(
                instructions="Verify the product.",
                payload={"input": "test"},
                schema_name="test_result",
                schema={
                    "type": "object",
                    "additionalProperties": False,
                    "properties": {"result": {"type": "string"}},
                    "required": ["result"],
                },
                web_search_allowed_domains=[
                    "https://www.bank.example/products",
                    "bank.example",
                ],
                require_web_search=True,
            )

        request_body = json.loads(urlopen.call_args.args[0].data.decode("utf-8"))
        self.assertEqual(
            request_body["tools"],
            [
                {
                    "type": "web_search",
                    "search_context_size": "medium",
                    "external_web_access": True,
                    "filters": {"allowed_domains": ["bank.example"]},
                }
            ],
        )
        self.assertEqual(request_body["tool_choice"], "required")
        self.assertEqual(request_body["include"], ["web_search_call.action.sources"])
        self.assertEqual(request_body["max_tool_calls"], 4)
        self.assertFalse(request_body["store"])
        self.assertEqual(result, {"result": "verified"})
        self.assertEqual(
            metadata["web_search_sources"],
            [{"url": "https://bank.example/rates", "title": "Official rates"}],
        )

    def test_responses_request_can_force_open_web_search_without_domain_filter(self) -> None:
        response = MagicMock()
        response.read.return_value = json.dumps(
            {
                "id": "resp-test-003",
                "model": "test-model",
                "output": [
                    {"type": "web_search_call", "action": {"type": "search", "sources": []}},
                    {
                        "type": "message",
                        "content": [{"type": "output_text", "text": '{"result":"researched"}'}],
                    },
                ],
                "usage": {"input_tokens": 10, "output_tokens": 5},
            }
        ).encode("utf-8")

        with (
            patch.dict(
                os.environ,
                {
                    "FPDS_LLM_PROVIDER": "openai",
                    "FPDS_LLM_API_KEY": "test-key",
                    "FPDS_LLM_MODEL": "test-model",
                },
                clear=True,
            ),
            patch("worker.pipeline.fpds_ai_runtime.urllib.request.urlopen") as urlopen,
        ):
            urlopen.return_value.__enter__.return_value = response
            result, _metadata = invoke_openai_json_schema(
                instructions="Research the market.",
                payload={"input": "test"},
                schema_name="test_result",
                schema={
                    "type": "object",
                    "additionalProperties": False,
                    "properties": {"result": {"type": "string"}},
                    "required": ["result"],
                },
                require_web_search=True,
                max_web_search_tool_calls=12,
            )

        request_body = json.loads(urlopen.call_args.args[0].data.decode("utf-8"))
        self.assertEqual(
            request_body["tools"],
            [
                {
                    "type": "web_search",
                    "search_context_size": "medium",
                    "external_web_access": True,
                }
            ],
        )
        self.assertEqual(request_body["tool_choice"], "required")
        self.assertEqual(request_body["max_tool_calls"], 12)
        self.assertEqual(result, {"result": "researched"})

    def test_responses_request_rejects_out_of_policy_web_search_budget(self) -> None:
        with patch.dict(
            os.environ,
            {"FPDS_LLM_PROVIDER": "openai", "FPDS_LLM_API_KEY": "test-key"},
            clear=True,
        ):
            with self.assertRaisesRegex(ValueError, "between 1 and 20"):
                invoke_openai_json_schema(
                    instructions="Research the market.",
                    payload={"input": "test"},
                    schema_name="test_result",
                    schema={
                        "type": "object",
                        "additionalProperties": False,
                        "properties": {"result": {"type": "string"}},
                        "required": ["result"],
                    },
                    require_web_search=True,
                    max_web_search_tool_calls=21,
                )


    def test_responses_request_supports_explicit_efforts(self) -> None:
        for effort in ("none", "low", "medium", "high", "xhigh", "max"):
            with self.subTest(effort=effort), patch.dict(
                os.environ, {"FPDS_LLM_PROVIDER": "openai", "FPDS_LLM_API_KEY": "test-key"}, clear=True
            ), patch("worker.pipeline.fpds_ai_runtime.urllib.request.urlopen") as urlopen:
                urlopen.return_value.__enter__.return_value.read.return_value = json.dumps({
                    "output": [{"type": "message", "content": [{"type": "output_text", "text": "{}"}]}]
                }).encode()
                invoke_openai_json_schema(
                    instructions="Return JSON.", payload={}, schema_name="result",
                    schema={"type": "object"}, reasoning_effort=effort,
                    require_web_search=True, web_search_allowed_domains=["bank.example"],
                )
                request = json.loads(urlopen.call_args.args[0].data)
                self.assertEqual(request["model"], "gpt-6-luna")
                self.assertEqual(request["reasoning"], {"effort": effort})
                self.assertEqual(request["text"]["format"]["type"], "json_schema")
                self.assertEqual(request["tools"][0]["filters"]["allowed_domains"], ["bank.example"])
                self.assertEqual(request["tool_choice"], "required")

    def test_invalid_reasoning_effort_fails_before_network_request(self) -> None:
        for effort in ("", "minimal", "HIGH", None, True):
            with self.subTest(effort=effort), patch.dict(
                os.environ, {"FPDS_LLM_PROVIDER": "openai", "FPDS_LLM_API_KEY": "test-key"}, clear=True
            ), patch("worker.pipeline.fpds_ai_runtime.urllib.request.urlopen") as urlopen:
                with self.assertRaisesRegex(ValueError, "Unsupported reasoning effort"):
                    invoke_openai_json_schema(
                        instructions="Return JSON.", payload={}, schema_name="result",
                        schema={"type": "object"}, reasoning_effort=effort,
                    )
                urlopen.assert_not_called()

    def test_blank_model_uses_current_default(self) -> None:
        with patch.dict(os.environ, {"FPDS_LLM_MODEL": "  "}, clear=True):
            self.assertEqual(configured_model_id(), "gpt-6-luna")

if __name__ == "__main__":
    unittest.main()
