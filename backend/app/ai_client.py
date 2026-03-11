import json
import os
from typing import Any

import httpx
from pydantic import ValidationError

from app.models import AiAssistantResponseModel, AiHistoryMessageModel


OPENROUTER_API_URL = "https://openrouter.ai/api/v1/chat/completions"
OPENROUTER_MODEL = "openai/gpt-oss-120b"
AI_TEST_PROMPT = "2+2"


class OpenRouterError(Exception):
    pass


class OpenRouterConfigError(OpenRouterError):
    pass


class OpenRouterRequestError(OpenRouterError):
    pass


class OpenRouterSchemaError(OpenRouterRequestError):
    pass


KANBAN_CHAT_SYSTEM_PROMPT = """
You are an assistant for a Kanban board application.
You receive: board JSON, conversation history, and a user question.

Return only a structured JSON object with:
- "message": user-facing reply,
- "patch": null or operations to update the board.

Rules:
- Keep stable fixed columns.
- Use operations only when an actual board change is required.
- Prefer minimal, safe changes.
- Never invent column IDs outside the existing board columns.
""".strip()

KANBAN_CHAT_JSON_SCHEMA: dict[str, Any] = {
    "name": "kanban_ai_response",
    "strict": True,
    "schema": {
        "type": "object",
        "additionalProperties": False,
        "properties": {
            "message": {"type": "string"},
            "patch": {
                "anyOf": [
                    {
                        "type": "object",
                        "additionalProperties": False,
                        "properties": {
                            "operations": {
                                "type": "array",
                                "items": {
                                    "type": "object",
                                    "additionalProperties": False,
                                    "properties": {
                                        "op": {
                                            "type": "string",
                                            "enum": [
                                                "create_card",
                                                "edit_card",
                                                "move_card",
                                            ],
                                        },
                                        "cardId": {"type": ["string", "null"]},
                                        "title": {"type": ["string", "null"]},
                                        "details": {"type": ["string", "null"]},
                                        "columnId": {"type": ["string", "null"]},
                                        "targetColumnId": {"type": ["string", "null"]},
                                        "position": {"type": ["integer", "null"]},
                                    },
                                    "required": [
                                        "op",
                                        "cardId",
                                        "title",
                                        "details",
                                        "columnId",
                                        "targetColumnId",
                                        "position",
                                    ],
                                },
                            }
                        },
                        "required": ["operations"],
                    },
                    {"type": "null"},
                ]
            },
        },
        "required": ["message", "patch"],
    },
}


def run_connectivity_test(prompt: str = AI_TEST_PROMPT) -> str:
    payload = {
        "model": OPENROUTER_MODEL,
        "messages": [{"role": "user", "content": prompt}],
    }
    response_json = _perform_openrouter_request(payload)

    return _extract_text_content(response_json)


def run_structured_kanban_chat(
    *,
    board: dict[str, Any],
    question: str,
    history: list[AiHistoryMessageModel],
) -> AiAssistantResponseModel:
    messages: list[dict[str, str]] = [{"role": "system", "content": KANBAN_CHAT_SYSTEM_PROMPT}]
    messages.append(
        {
            "role": "user",
            "content": (
                "Current board JSON:\n"
                f"{json.dumps(board, ensure_ascii=False)}"
            ),
        }
    )
    for message in history:
        messages.append({"role": message.role, "content": message.content})
    messages.append({"role": "user", "content": question})

    payload = {
        "model": OPENROUTER_MODEL,
        "messages": messages,
        "response_format": {
            "type": "json_schema",
            "json_schema": KANBAN_CHAT_JSON_SCHEMA,
        },
    }
    response_json = _perform_openrouter_request(payload)
    raw_content = _extract_text_content(response_json)

    try:
        structured_payload = json.loads(raw_content)
    except json.JSONDecodeError as error:
        raise OpenRouterSchemaError(
            "Structured response from OpenRouter is not valid JSON."
        ) from error

    try:
        return AiAssistantResponseModel.model_validate(structured_payload)
    except ValidationError as error:
        raise OpenRouterSchemaError(
            "Structured response from OpenRouter failed schema validation."
        ) from error


def _perform_openrouter_request(payload: dict[str, Any]) -> dict[str, Any]:
    api_key = os.getenv("OPENROUTER_API_KEY")
    if not api_key:
        raise OpenRouterConfigError("Missing OPENROUTER_API_KEY environment variable.")

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }

    try:
        response = httpx.post(
            OPENROUTER_API_URL,
            headers=headers,
            json=payload,
            timeout=45.0,
        )
        response.raise_for_status()
    except httpx.HTTPStatusError as error:
        detail = error.response.text.strip()
        raise OpenRouterRequestError(
            f"OpenRouter returned HTTP {error.response.status_code}: {detail or 'no details'}"
        ) from error
    except httpx.HTTPError as error:
        raise OpenRouterRequestError(f"OpenRouter request failed: {error}") from error

    try:
        return response.json()
    except ValueError as error:
        raise OpenRouterRequestError("OpenRouter returned invalid JSON response.") from error


def _extract_text_content(response_json: dict[str, Any]) -> str:
    choices = response_json.get("choices")
    if not isinstance(choices, list) or not choices:
        raise OpenRouterRequestError("OpenRouter response did not include choices.")

    first_choice = choices[0]
    if not isinstance(first_choice, dict):
        raise OpenRouterRequestError("OpenRouter response choice format is invalid.")

    message = first_choice.get("message")
    if not isinstance(message, dict):
        raise OpenRouterRequestError("OpenRouter response did not include message object.")

    content = message.get("content")
    if isinstance(content, str):
        stripped_content = content.strip()
        if stripped_content:
            return stripped_content
        raise OpenRouterRequestError("OpenRouter returned an empty message content.")

    if isinstance(content, list):
        text_parts: list[str] = []
        for item in content:
            if not isinstance(item, dict):
                continue
            if item.get("type") != "text":
                continue
            text = item.get("text")
            if isinstance(text, str):
                text_parts.append(text)

        joined_text = "".join(text_parts).strip()
        if joined_text:
            return joined_text

    raise OpenRouterRequestError("OpenRouter response did not include text content.")
