from __future__ import annotations

import json
import os
from typing import Any
import urllib.error
import urllib.request


def llm_provider_configured() -> bool:
    provider = os.getenv("FPDS_LLM_PROVIDER", "openai").strip().lower()
    api_key = os.getenv("FPDS_LLM_API_KEY", "").strip()
    return provider == "openai" and bool(api_key)


def configured_model_id(*, default: str = "gpt-5.4-mini") -> str:
    return os.getenv("FPDS_LLM_MODEL", default).strip() or default


def invoke_openai_json_schema(
    *,
    instructions: str,
    payload: dict[str, Any],
    schema_name: str,
    schema: dict[str, Any],
    model_id: str | None = None,
) -> tuple[dict[str, Any], dict[str, Any]]:
    provider = os.getenv("FPDS_LLM_PROVIDER", "openai").strip().lower()
    api_key = os.getenv("FPDS_LLM_API_KEY", "").strip()
    if provider != "openai" or not api_key:
        raise RuntimeError("OpenAI provider or API key was not configured.")

    request_body = {
        "model": model_id or configured_model_id(),
        "instructions": instructions,
        "input": [
            {
                "role": "user",
                "content": [
                    {
                        "type": "input_text",
                        "text": json.dumps(payload, ensure_ascii=True),
                    }
                ],
            }
        ],
        "text": {
            "format": {
                "type": "json_schema",
                "name": schema_name,
                "strict": True,
                "schema": schema,
            }
        },
    }
    request = urllib.request.Request(
        "https://api.openai.com/v1/responses",
        data=json.dumps(request_body, ensure_ascii=True).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=90) as response:
            response_payload = json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        response_body = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"OpenAI Responses API request failed with status {exc.code}: {response_body}") from exc

    response_text = _extract_response_output_text(response_payload)
    try:
        parsed = json.loads(response_text)
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"OpenAI response returned invalid JSON: {response_text}") from exc

    usage = response_payload.get("usage") or {}
    metadata = {
        "provider": "openai",
        "model_id": str(response_payload.get("model") or model_id or configured_model_id()),
        "provider_request_id": response_payload.get("id"),
        "prompt_tokens": int(usage.get("input_tokens") or 0),
        "completion_tokens": int(usage.get("output_tokens") or 0),
    }
    return parsed, metadata


def estimated_cost_usd(*, prompt_tokens: int, completion_tokens: int) -> str:
    # Placeholder conservative estimate until per-model pricing is externalized.
    estimated = ((prompt_tokens * 0.0000003) + (completion_tokens * 0.0000012))
    return f"{estimated:.6f}"


def _extract_response_output_text(response_payload: dict[str, Any]) -> str:
    for item in response_payload.get("output", []):
        if str(item.get("type")) != "message":
            continue
        for content in item.get("content", []):
            content_type = str(content.get("type") or "")
            if content_type == "refusal":
                raise RuntimeError(str(content.get("refusal") or "OpenAI refused the request."))
            if content_type == "output_text" and content.get("text"):
                return str(content["text"])
    raise RuntimeError("OpenAI response returned no text output.")
