"""Built-in AI model catalog for runtime and API consumers."""

from __future__ import annotations

from typing import TypedDict

AUTO_MODEL_ID = "auto"


class ModelEntry(TypedDict):
    id: str
    name: str
    provider: str


MODEL_CATALOG: list[ModelEntry] = [
    # Gemini
    {"id": "gemini-2.5-flash", "name": "Gemini 2.5 Flash", "provider": "Gemini"},
    {"id": "gemini-2.5-flash-lite", "name": "Gemini 2.5 Flash Lite", "provider": "Gemini"},
    {"id": "gemini-2.5-pro", "name": "Gemini 2.5 Pro", "provider": "Gemini"},
    {"id": "gemini-2.0-flash", "name": "Gemini 2.0 Flash", "provider": "Gemini"},
    {"id": "gemini-2.0-flash-lite", "name": "Gemini 2.0 Flash Lite", "provider": "Gemini"},
    {"id": "gemini-3-flash", "name": "Gemini 3 Flash", "provider": "Gemini"},
    {"id": "gemini-3-pro", "name": "Gemini 3 Pro", "provider": "Gemini"},
    {"id": "gemini-1.5-flash", "name": "Gemini 1.5 Flash", "provider": "Gemini"},
    {"id": "gemini-1.5-pro", "name": "Gemini 1.5 Pro", "provider": "Gemini"},
    # OpenAI
    {"id": "gpt-4o", "name": "GPT-4o", "provider": "OpenAI"},
    {"id": "gpt-4o-mini", "name": "GPT-4o mini", "provider": "OpenAI"},
    {"id": "gpt-4-turbo", "name": "GPT-4 Turbo", "provider": "OpenAI"},
    {"id": "gpt-4", "name": "GPT-4", "provider": "OpenAI"},
    {"id": "o1", "name": "o1", "provider": "OpenAI"},
    {"id": "o1-mini", "name": "o1 mini", "provider": "OpenAI"},
    {"id": "o3-mini", "name": "o3 mini", "provider": "OpenAI"},
    # Claude
    {"id": "claude-3.5-sonnet", "name": "Claude 3.5 Sonnet", "provider": "Claude"},
    {"id": "claude-3.5-haiku", "name": "Claude 3.5 Haiku", "provider": "Claude"},
    {"id": "claude-3-opus", "name": "Claude 3 Opus", "provider": "Claude"},
    {"id": "claude-3-sonnet", "name": "Claude 3 Sonnet", "provider": "Claude"},
    # DeepSeek
    {"id": "deepseek-chat", "name": "DeepSeek Chat", "provider": "DeepSeek"},
    {"id": "deepseek-reasoner", "name": "DeepSeek Reasoner", "provider": "DeepSeek"},
    # Meta / Mistral / Qwen
    {"id": "llama-3.1-70b", "name": "Llama 3.1 70B", "provider": "Meta"},
    {"id": "llama-3.1-8b", "name": "Llama 3.1 8B", "provider": "Meta"},
    {"id": "mistral-large", "name": "Mistral Large", "provider": "Mistral"},
    {"id": "qwen-2.5-72b", "name": "Qwen 2.5 72B", "provider": "Qwen"},
]

DASHBOARD_MODEL_IDS = [
    "gemini-2.0-flash",
    "gemini-2.5-flash",
    "gpt-4o",
    "claude-3.5-sonnet",
    "deepseek-chat",
]

_MODEL_BY_ID = {m["id"]: m for m in MODEL_CATALOG}


def resolve_model_name(model_id: str) -> str:
    entry = _MODEL_BY_ID.get(model_id)
    return entry["name"] if entry else model_id


def dashboard_models() -> list[ModelEntry]:
    return [_MODEL_BY_ID[mid] for mid in DASHBOARD_MODEL_IDS if mid in _MODEL_BY_ID]
