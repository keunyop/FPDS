from __future__ import annotations

import os
import json
import unittest
from unittest.mock import MagicMock, patch

from worker.pipeline.fpds_ai_runtime import configured_model_id, invoke_openai_json_schema


class AiRuntimeTests(unittest.TestCase):
    def test_default_model_is_gpt_5_6_luna(self) -> None:
        with patch.dict(os.environ, {}, clear=True):
            self.assertEqual(configured_model_id(), "gpt-5.6-luna")

    def test_configured_model_overrides_default(self) -> None:
        with patch.dict(os.environ, {"FPDS_LLM_MODEL": "test-model"}, clear=True):
            self.assertEqual(configured_model_id(), "test-model")

    def test_responses_request_uses_default_medium_reasoning_effort_when_omitted(self) -> None:
        response = MagicMock()
        response.read.return_value = json.dumps(
            {
                "id": "resp-test-001",
                "model": "gpt-5.6-luna",
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
        self.assertEqual(request_body["model"], "gpt-5.6-luna")
        self.assertNotIn("reasoning", request_body)
        self.assertEqual(result, {"result": "ok"})
        self.assertEqual(metadata["model_id"], "gpt-5.6-luna")


if __name__ == "__main__":
    unittest.main()
