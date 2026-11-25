"""Adaptador de Qdrant para el puerto ChunkRepository.

La colección tiene dos vectores con nombre:
- ``dense``: embedding semántico (coseno).
- ``lexico``: vector disperso con IDF calculado por Qdrant (tipo BM25).

El payload guarda el chunk completo; el texto que se muestra al usuario sale de aquí.
"""

from __future__ import annotations

import logging
import uuid
from collections.abc import Sequence

from qdrant_client import QdrantClient, models

from app.domain.models import Chunk
from app.domain.ports import ChunkFilter, ScoredChunk, SparseVector

logger = logging.getLogger(__name__)

DENSE = "dense"
LEXICO = "lexico"
_NAMESPACE = uuid.UUID("6f1c3a52-6d0b-4c1e-9a55-2d7b8c0a1e10")


def point_id(chunk_id: str) -> str:
    """Qdrant exige UUID o entero: se deriva un UUID estable del id del chunk."""
    return str(uuid.uuid5(_NAMESPACE, chunk_id))


class QdrantChunkRepository:
    def __init__(self, client: QdrantClient, collection: str) -> None:
        self._client = client
        self._collection = collection

    # -- administración ---------------------------------------------------
    def ensure_collection(self, dimension: int, recreate: bool = False) -> None:
        existe = self._client.collection_exists(self._collection)
        if existe and not recreate:
            return
        if existe:
            self._client.delete_collection(self._collection)
        self._client.create_collection(
            collection_name=self._collection,
            vectors_config={DENSE: models.VectorParams(size=dimension, distance=models.Distance.COSINE)},
            sparse_vectors_config={LEXICO: models.SparseVectorParams(modifier=models.Modifier.IDF)},
        )
        for campo, tipo in (
            ("articulo_num", models.PayloadSchemaType.INTEGER),
            ("fraccion", models.PayloadSchemaType.KEYWORD),
            ("inciso", models.PayloadSchemaType.KEYWORD),
            ("tipo", models.PayloadSchemaType.KEYWORD),
            ("derogado", models.PayloadSchemaType.BOOL),
            ("id", models.PayloadSchemaType.KEYWORD),
        ):
            self._client.create_payload_index(self._collection, campo, field_schema=tipo)
        logger.info("Colección %s creada (dim=%s)", self._collection, dimension)

    def upsert(
        self,
        chunks: Sequence[Chunk],
        dense: Sequence[Sequence[float]],
        sparse: Sequence[SparseVector],
    ) -> None:
        puntos = [
            models.PointStruct(
                id=point_id(c.id),
                vector={
                    DENSE: list(d),
                    LEXICO: models.SparseVector(indices=s.indices, values=s.values),
                },
                payload=c.model_dump(mode="json"),
            )
            for c, d, s in zip(chunks, dense, sparse, strict=True)
        ]
        self._client.upsert(self._collection, points=puntos, wait=True)

    # -- consultas ----------------------------------------------------------
    @staticmethod
    def _filtro(filtro: ChunkFilter | None) -> models.Filter | None:
        if filtro is None:
            return None
        must: list[models.Condition] = []
        must_not: list[models.Condition] = []
        if filtro.articulo_num is not None:
            must.append(
                models.FieldCondition(key="articulo_num", match=models.MatchValue(value=filtro.articulo_num))
            )
        if filtro.fraccion is not None:
            must.append(models.FieldCondition(key="fraccion", match=models.MatchValue(value=filtro.fraccion)))
        if filtro.inciso is not None:
            must.append(models.FieldCondition(key="inciso", match=models.MatchValue(value=filtro.inciso)))
        if not filtro.incluir_derogados:
            must_not.append(models.FieldCondition(key="derogado", match=models.MatchValue(value=True)))
        return models.Filter(must=must or None, must_not=must_not or None)

    def _a_scored(self, puntos: Sequence[models.ScoredPoint]) -> list[ScoredChunk]:
        return [ScoredChunk(Chunk.model_validate(p.payload), float(p.score)) for p in puntos]

    def search_dense(
        self, vector: Sequence[float], limit: int, filtro: ChunkFilter | None = None
    ) -> list[ScoredChunk]:
        res = self._client.query_points(
            self._collection,
            query=list(vector),
            using=DENSE,
            limit=limit,
            query_filter=self._filtro(filtro or ChunkFilter()),
            with_payload=True,
        )
        return self._a_scored(res.points)

    def search_sparse(
        self, vector: SparseVector, limit: int, filtro: ChunkFilter | None = None
    ) -> list[ScoredChunk]:
        if not vector.indices:
            return []
        res = self._client.query_points(
            self._collection,
            query=models.SparseVector(indices=vector.indices, values=vector.values),
            using=LEXICO,
            limit=limit,
            query_filter=self._filtro(filtro or ChunkFilter()),
            with_payload=True,
        )
        return self._a_scored(res.points)

    def find(self, filtro: ChunkFilter, limit: int = 50) -> list[Chunk]:
        puntos, _ = self._client.scroll(
            self._collection,
            scroll_filter=self._filtro(filtro),
            limit=limit,
            with_payload=True,
            with_vectors=False,
        )
        chunks = [Chunk.model_validate(p.payload) for p in puntos]
        return sorted(chunks, key=lambda c: c.id)

    def get(self, chunk_id: str) -> Chunk | None:
        puntos = self._client.retrieve(self._collection, ids=[point_id(chunk_id)], with_payload=True)
        return Chunk.model_validate(puntos[0].payload) if puntos else None

    def count(self) -> int:
        if not self._client.collection_exists(self._collection):
            return 0
        return self._client.count(self._collection, exact=True).count

    def healthy(self) -> bool:
        try:
            self._client.get_collections()
            return True
        except Exception:  # noqa: BLE001 - cualquier fallo de red cuenta como no disponible
            return False


def crear_cliente_qdrant(
    url: str | None, location: str | None, api_key: str | None, timeout_s: float
) -> QdrantClient:
    if location:
        return QdrantClient(location=location)
    return QdrantClient(url=url, api_key=api_key, timeout=int(timeout_s))
