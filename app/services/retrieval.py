"""Caso de uso: recuperación híbrida.

1. Referencias explícitas ("artículo 14, fracción I") → búsqueda exacta por payload.
2. Búsqueda semántica (densa) y por palabras clave (dispersa).
3. Fusión por Reciprocal Rank Fusion (RRF); las coincidencias exactas van primero.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from app.core.config import RetrievalSettings
from app.domain.models import Chunk, ResultadoBusqueda
from app.domain.ports import ChunkFilter, ChunkRepository, EmbeddingProvider, ScoredChunk, SparseEncoder
from app.domain.referencias import extraer_referencias, romano_a_entero, tokenizar


@dataclass
class ResultadoRecuperacion:
    resultados: list[ResultadoBusqueda] = field(default_factory=list)
    mejor_score_denso: float = 0.0
    hubo_coincidencia_exacta: bool = False
    cobertura_lexica: float = 0.0

    def tiene_soporte(self, min_dense_score: float, min_cobertura_lexica: float) -> bool:
        """Hay soporte si se citó un artículo existente, si la similitud semántica es
        suficiente o si el mejor resultado léxico contiene buena parte de las palabras clave."""
        if not self.resultados:
            return False
        return (
            self.hubo_coincidencia_exacta
            or self.mejor_score_denso >= min_dense_score
            or self.cobertura_lexica >= min_cobertura_lexica
        )


def orden_natural(chunk: Chunk) -> tuple:
    """Orden del reglamento: artículo, fracción (romano, Bis, Ter) e inciso."""
    fr = chunk.fraccion or ""
    partes = fr.split()
    base = romano_a_entero(partes[0]) if partes else 0
    sufijo = {"bis": 1, "ter": 2}.get(partes[1].lower(), 3) if len(partes) > 1 else 0
    return (chunk.articulo_num or 0, base, sufijo, chunk.inciso or "", chunk.id)


class RetrievalService:
    def __init__(
        self,
        repo: ChunkRepository,
        embeddings: EmbeddingProvider,
        sparse: SparseEncoder,
        cfg: RetrievalSettings,
    ) -> None:
        self._repo = repo
        self._embeddings = embeddings
        self._sparse = sparse
        self._cfg = cfg

    def buscar(self, pregunta: str, top_k: int | None = None) -> ResultadoRecuperacion:
        top_k = top_k or self._cfg.top_k
        exactos = self._exactos(pregunta)
        densos = self._repo.search_dense(self._embeddings.embed_query(pregunta), self._cfg.dense_k)
        lexicos = self._repo.search_sparse(self._sparse.encode(pregunta), self._cfg.sparse_k)

        fusion = self._rrf(densos, lexicos)
        score_denso = {s.chunk.id: s.score for s in densos}
        score_lex = {s.chunk.id: s.score for s in lexicos}

        resultados: list[ResultadoBusqueda] = []
        vistos: set[str] = set()
        for chunk in exactos:
            if chunk.id not in vistos:
                vistos.add(chunk.id)
                resultados.append(
                    ResultadoBusqueda(
                        chunk=chunk,
                        score=1.0,
                        score_denso=score_denso.get(chunk.id),
                        score_lexico=score_lex.get(chunk.id),
                        coincidencia_exacta=True,
                    )
                )
        for chunk, score in fusion:
            if chunk.id not in vistos:
                vistos.add(chunk.id)
                resultados.append(
                    ResultadoBusqueda(
                        chunk=chunk,
                        score=score,
                        score_denso=score_denso.get(chunk.id),
                        score_lexico=score_lex.get(chunk.id),
                    )
                )

        return ResultadoRecuperacion(
            resultados=resultados[: max(top_k, min(len(exactos), self._cfg.max_exact_matches))],
            mejor_score_denso=max(score_denso.values(), default=0.0),
            hubo_coincidencia_exacta=bool(exactos),
            cobertura_lexica=self._cobertura(pregunta, lexicos),
        )

    @staticmethod
    def _cobertura(pregunta: str, lexicos: list[ScoredChunk]) -> float:
        """Proporción de palabras clave de la pregunta presentes en el mejor resultado léxico."""
        consulta = set(tokenizar(pregunta))
        if not consulta or not lexicos:
            return 0.0
        return max(
            len(consulta & set(tokenizar(s.chunk.texto_embedding))) / len(consulta) for s in lexicos[:3]
        )

    def _exactos(self, pregunta: str) -> list[Chunk]:
        chunks: list[Chunk] = []
        for ref in extraer_referencias(pregunta):
            filtro = ChunkFilter(articulo_num=ref.articulo_num, fraccion=ref.fraccion, inciso=ref.inciso)
            encontrados = self._repo.find(filtro, limit=200)
            # Pidió un inciso que no existe como chunk: se cae a la fracción.
            if not encontrados and ref.inciso:
                encontrados = self._repo.find(
                    ChunkFilter(articulo_num=ref.articulo_num, fraccion=ref.fraccion), limit=200
                )
            chunks.extend(sorted(encontrados, key=orden_natural))
        return chunks

    def _rrf(self, *listas: list[ScoredChunk]) -> list[tuple[Chunk, float]]:
        k = self._cfg.rrf_k
        puntaje: dict[str, float] = {}
        por_id: dict[str, Chunk] = {}
        for lista in listas:
            for rank, s in enumerate(lista):
                puntaje[s.chunk.id] = puntaje.get(s.chunk.id, 0.0) + 1.0 / (k + rank + 1)
                por_id[s.chunk.id] = s.chunk
        return sorted(((por_id[i], p) for i, p in puntaje.items()), key=lambda x: x[1], reverse=True)
