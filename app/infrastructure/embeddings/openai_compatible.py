"""Embeddings por API compatible con OpenAI (/v1/embeddings).

Funciona con Hugging Face TEI, vLLM, Infinity u OpenAI. El modelo (p. ej. bge-m3)
corre en el servidor de inferencia; este backend no carga PyTorch.
"""

from __future__ import annotations

from collections.abc import Sequence

import httpx


class EmbeddingError(RuntimeError):
    pass


class OpenAICompatibleEmbeddings:
    def __init__(
        self,
        base_url: str,
        model: str,
        dimension: int,
        api_key: str | None = None,
        batch_size: int = 32,
        timeout_s: float = 60.0,
        query_prefix: str = "",
        document_prefix: str = "",
        client: httpx.Client | None = None,
    ) -> None:
        self._model = model
        self._dimension = dimension
        self._batch_size = batch_size
        self._query_prefix = query_prefix
        self._document_prefix = document_prefix
        headers = {"Authorization": f"Bearer {api_key}"} if api_key else {}
        self._client = client or httpx.Client(
            base_url=base_url.rstrip("/"), headers=headers, timeout=timeout_s
        )

    @property
    def dimension(self) -> int:
        return self._dimension

    @property
    def model_name(self) -> str:
        return self._model

    def _embed(self, texts: Sequence[str]) -> list[list[float]]:
        vectores: list[list[float]] = []
        for i in range(0, len(texts), self._batch_size):
            lote = list(texts[i : i + self._batch_size])
            try:
                resp = self._client.post("/embeddings", json={"model": self._model, "input": lote})
                resp.raise_for_status()
            except httpx.HTTPError as exc:
                raise EmbeddingError(f"Error al pedir embeddings: {exc}") from exc
            datos = sorted(resp.json()["data"], key=lambda d: d["index"])
            for d in datos:
                if len(d["embedding"]) != self._dimension:
                    raise EmbeddingError(
                        f"El modelo devolvió dimensión {len(d['embedding'])}, se esperaba {self._dimension}"
                    )
                vectores.append(d["embedding"])
        return vectores

    def embed_documents(self, texts: Sequence[str]) -> list[list[float]]:
        return self._embed([self._document_prefix + t for t in texts])

    def embed_query(self, text: str) -> list[float]:
        return self._embed([self._query_prefix + text])[0]
