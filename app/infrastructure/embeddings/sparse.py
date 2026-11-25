"""Codificador disperso para la parte léxica de la búsqueda híbrida.

Produce frecuencias de término con índices por hashing; Qdrant aplica el IDF
(``Modifier.IDF``), así que el resultado se comporta como BM25 sin descargar modelos.
"""

from __future__ import annotations

import zlib
from collections import Counter

from app.domain.ports import SparseVector
from app.domain.referencias import tokenizar


class HashingBM25Encoder:
    def __init__(self, k1: float = 1.2) -> None:
        self._k1 = k1

    def encode(self, text: str) -> SparseVector:
        conteo = Counter(zlib.crc32(t.encode("utf-8")) for t in tokenizar(text))
        indices = sorted(conteo)
        # Saturación de la frecuencia de término al estilo BM25.
        values = [conteo[i] * (self._k1 + 1) / (conteo[i] + self._k1) for i in indices]
        return SparseVector(indices=indices, values=values)
