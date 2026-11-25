"""Caso de uso: indexar los chunks del reglamento en el almacén vectorial."""

from __future__ import annotations

import logging
from collections.abc import Callable, Iterable

from app.domain.models import Chunk
from app.domain.ports import ChunkRepository, EmbeddingProvider, SparseEncoder

logger = logging.getLogger(__name__)


class IngestionService:
    def __init__(
        self,
        fuente: Callable[[], Iterable[Chunk]],
        embeddings: EmbeddingProvider,
        sparse: SparseEncoder,
        repo: ChunkRepository,
        batch_size: int = 64,
    ) -> None:
        self._fuente = fuente
        self._embeddings = embeddings
        self._sparse = sparse
        self._repo = repo
        self._batch_size = batch_size

    def ingestar(self, recrear: bool = False) -> int:
        self._repo.ensure_collection(self._embeddings.dimension, recreate=recrear)
        lote: list[Chunk] = []
        total = 0
        for chunk in self._fuente():
            lote.append(chunk)
            if len(lote) >= self._batch_size:
                total += self._indexar(lote)
                lote = []
        if lote:
            total += self._indexar(lote)
        logger.info("Ingesta terminada: %s chunks", total)
        return total

    def _indexar(self, lote: list[Chunk]) -> int:
        textos = [c.texto_embedding for c in lote]
        densos = self._embeddings.embed_documents(textos)
        dispersos = [self._sparse.encode(t) for t in textos]
        self._repo.upsert(lote, densos, dispersos)
        return len(lote)
