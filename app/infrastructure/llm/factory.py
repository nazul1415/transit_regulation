"""Fábrica de proveedores de LLM (patrón estrategia + fábrica)."""

from __future__ import annotations

from app.core.config import LLMSettings
from app.domain.ports import LLMProvider
from app.infrastructure.llm.fake import FakeLLM
from app.infrastructure.llm.openai_compatible import OpenAICompatibleLLM


def crear_llm(cfg: LLMSettings) -> LLMProvider:
    if cfg.provider == "openai_compatible":
        return OpenAICompatibleLLM(
            base_url=cfg.base_url,
            model=cfg.model,
            api_key=cfg.api_key.get_secret_value() if cfg.api_key else None,
            temperature=cfg.temperature,
            max_tokens=cfg.max_tokens,
            timeout_s=cfg.timeout_s,
            max_retries=cfg.max_retries,
            disable_thinking=cfg.disable_thinking,
        )
    if cfg.provider == "fake":
        return FakeLLM()
    raise ValueError(f"Proveedor de LLM no soportado: {cfg.provider}")
