"""Puertos (interfaces) del dominio. La infraestructura implementa estos protocolos
(adaptadores) y los servicios solo dependen de ellos."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import Protocol, runtime_checkable

from app.domain.models import Articulo, Chunk


@dataclass(frozen=True)
class SparseVector:
    indices: list[int]
    values: list[float]


@dataclass(frozen=True)
class ScoredChunk:
    chunk: Chunk
    score: float


@dataclass(frozen=True)
class ChunkFilter:
    articulo_num: int | None = None
    fraccion: str | None = None
    inciso: str | None = None
    incluir_derogados: bool = False


@runtime_checkable
class EmbeddingProvider(Protocol):
    """Genera vectores densos. Se consume por API; nunca carga modelos locales."""

    @property
    def dimension(self) -> int: ...

    @property
    def model_name(self) -> str: ...

    def embed_documents(self, texts: Sequence[str]) -> list[list[float]]: ...

    def embed_query(self, text: str) -> list[float]: ...


@runtime_checkable
class SparseEncoder(Protocol):
    """Codifica texto en un vector disperso (palabras clave) para la búsqueda híbrida."""

    def encode(self, text: str) -> SparseVector: ...


@runtime_checkable
class ChunkRepository(Protocol):
    """Almacén vectorial de chunks (Qdrant en producción)."""

    def ensure_collection(self, dimension: int, recreate: bool = False) -> None: ...

    def upsert(
        self,
        chunks: Sequence[Chunk],
        dense: Sequence[Sequence[float]],
        sparse: Sequence[SparseVector],
    ) -> None: ...

    def search_dense(
        self, vector: Sequence[float], limit: int, filtro: ChunkFilter | None = None
    ) -> list[ScoredChunk]: ...

    def search_sparse(
        self, vector: SparseVector, limit: int, filtro: ChunkFilter | None = None
    ) -> list[ScoredChunk]: ...

    def find(self, filtro: ChunkFilter, limit: int = 50) -> list[Chunk]: ...

    def get(self, chunk_id: str) -> Chunk | None: ...

    def count(self) -> int: ...

    def healthy(self) -> bool: ...


@runtime_checkable
class ArticleRepository(Protocol):
    """Fuente de verdad del texto completo de cada artículo (documento padre)."""

    def get(self, articulo_num: int) -> Articulo | None: ...

    def list(self) -> list[Articulo]: ...


@runtime_checkable
class LLMProvider(Protocol):
    """Modelo de lenguaje consumido por API (compatible con OpenAI)."""

    @property
    def model_name(self) -> str: ...

    def generate(self, system_prompt: str, user_prompt: str) -> str: ...
