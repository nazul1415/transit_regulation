"""Caso de uso: consulta directa de artículos (sin LLM)."""

from __future__ import annotations

from app.core.config import UmaSettings
from app.domain.models import Articulo, Chunk, MultaEnPesos
from app.domain.ports import ArticleRepository, ChunkFilter, ChunkRepository
from app.domain.sanciones import multas_en_pesos
from app.services.retrieval import orden_natural


class ArticuloNoEncontrado(LookupError):
    pass


class ArticleService:
    def __init__(self, articulos: ArticleRepository, chunks: ChunkRepository, uma: UmaSettings) -> None:
        self._articulos = articulos
        self._chunks = chunks
        self._uma = uma

    def obtener(self, numero: int) -> Articulo:
        articulo = self._articulos.get(numero)
        if articulo is None:
            raise ArticuloNoEncontrado(f"No existe el artículo {numero}")
        return articulo

    def listar(self) -> list[Articulo]:
        return self._articulos.list()

    def fragmentos(self, numero: int, fraccion: str | None = None, inciso: str | None = None) -> list[Chunk]:
        self.obtener(numero)
        chunks = self._chunks.find(
            ChunkFilter(articulo_num=numero, fraccion=fraccion, inciso=inciso), limit=500
        )
        if not chunks:
            raise ArticuloNoEncontrado(f"No existe el fragmento solicitado del artículo {numero}")
        return sorted(chunks, key=orden_natural)

    def multas(self, chunk: Chunk) -> list[MultaEnPesos]:
        return multas_en_pesos(chunk.sanciones, self._uma.valor_diario)
