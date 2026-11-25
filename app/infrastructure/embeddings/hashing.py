"""Embeddings deterministas por hashing de tokens. SOLO para pruebas y desarrollo
sin servidor de inferencia: no capturan semántica real."""

from __future__ import annotations

import math
import zlib
from collections.abc import Sequence

from app.domain.referencias import tokenizar


class HashingEmbeddings:
    def __init__(self, dimension: int = 256) -> None:
        self._dimension = dimension

    @property
    def dimension(self) -> int:
        return self._dimension

    @property
    def model_name(self) -> str:
        return f"hashing-{self._dimension}"

    def _vector(self, text: str) -> list[float]:
        v = [0.0] * self._dimension
        for tok in tokenizar(text):
            h = zlib.crc32(tok.encode("utf-8"))
            v[h % self._dimension] += 1.0 if (h >> 31) & 1 else -1.0
        norma = math.sqrt(sum(x * x for x in v)) or 1.0
        return [x / norma for x in v]

    def embed_documents(self, texts: Sequence[str]) -> list[list[float]]:
        return [self._vector(t) for t in texts]

    def embed_query(self, text: str) -> list[float]:
        return self._vector(text)
