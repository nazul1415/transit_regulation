"""Fábrica de proveedores de embeddings (patrón estrategia + fábrica)."""

from __future__ import annotations

from app.core.config import EmbeddingSettings
from app.domain.ports import EmbeddingProvider
from app.infrastructure.embeddings.hashing import HashingEmbeddings
from app.infrastructure.embeddings.openai_compatible import OpenAICompatibleEmbeddings


def crear_embeddings(cfg: EmbeddingSettings) -> EmbeddingProvider:
    if cfg.provider == "openai_compatible":
        return OpenAICompatibleEmbeddings(
            base_url=cfg.base_url,
            model=cfg.model,
            dimension=cfg.dimension,
            api_key=cfg.api_key.get_secret_value() if cfg.api_key else None,
            batch_size=cfg.batch_size,
            timeout_s=cfg.timeout_s,
            query_prefix=cfg.query_prefix,
            document_prefix=cfg.document_prefix,
        )
    if cfg.provider == "hashing":
        return HashingEmbeddings(dimension=cfg.dimension)
    raise ValueError(f"Proveedor de embeddings no soportado: {cfg.provider}")
