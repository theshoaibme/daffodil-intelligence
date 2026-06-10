"""Hugging Face Inference model ids and aliases."""

from __future__ import annotations

GLM_5_1_CATALOG_ID = "glm-5.1"
GLM_5_1_HF_MODEL_ID = "zai-org/GLM-5.1"

HF_MODEL_ALIASES: dict[str, str] = {
    GLM_5_1_CATALOG_ID: GLM_5_1_HF_MODEL_ID,
    "glm-5": GLM_5_1_HF_MODEL_ID,
    GLM_5_1_HF_MODEL_ID: GLM_5_1_HF_MODEL_ID,
}


def resolve_hf_model_id(model_id: str) -> str:
    """Map catalog id to Hugging Face router model id."""
    key = (model_id or "").strip()
    if not key:
        return GLM_5_1_HF_MODEL_ID
    return HF_MODEL_ALIASES.get(key, key)


def is_hf_model(model_id: str) -> bool:
    """True when the model should be served via Hugging Face Inference."""
    mid = (model_id or "").strip().lower()
    if not mid:
        return False
    if mid in HF_MODEL_ALIASES:
        return True
    if mid.startswith("glm-"):
        return True
    if mid.startswith("zai-org/"):
        return True
    return False
