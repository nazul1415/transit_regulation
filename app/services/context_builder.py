"""Construye el contexto para el LLM con el patrón parent document retrieval:
se buscan fracciones/incisos, pero se envían los artículos padre completos
(como lista de fragmentos con id), para no perder sanciones del final del artículo."""

from __future__ import annotations

from dataclasses import dataclass, field

from app.core.config import RetrievalSettings
from app.domain.models import Chunk, ResultadoBusqueda, TipoChunk
from app.domain.ports import ArticleRepository, ChunkFilter, ChunkRepository
from app.services.retrieval import orden_natural


@dataclass
class Contexto:
    texto: str
    chunks: dict[str, Chunk] = field(default_factory=dict)

    @property
    def articulos(self) -> set[int]:
        return {c.articulo_num for c in self.chunks.values() if c.articulo_num is not None}


def _formatear(chunk: Chunk) -> str:
    return f"[id={chunk.id}] {chunk.cita}\n{chunk.texto}"


class ContextBuilder:
    def __init__(self, chunks: ChunkRepository, articulos: ArticleRepository, cfg: RetrievalSettings) -> None:
        self._chunks = chunks
        self._articulos = articulos
        self._cfg = cfg

    def construir(self, resultados: list[ResultadoBusqueda]) -> Contexto:
        limite = self._cfg.max_context_chars
        bloques: list[str] = []
        incluidos: dict[str, Chunk] = {}
        usados = 0

        def agregar(texto: str) -> bool:
            nonlocal usados
            if usados + len(texto) > limite:
                return False
            bloques.append(texto)
            usados += len(texto) + 2
            return True

        # 1) Artículos padre de los mejores resultados, completos si caben.
        padres: list[int] = []
        for r in resultados:
            n = r.chunk.articulo_num
            if r.chunk.tipo == TipoChunk.ARTICULO and n is not None and n not in padres:
                padres.append(n)
        for num in padres[: self._cfg.max_parent_articles]:
            articulo = self._articulos.get(num)
            hijos = sorted(self._chunks.find(ChunkFilter(articulo_num=num), limit=500), key=orden_natural)
            cabecera = f"=== Artículo {num}"
            if articulo and articulo.capitulo:
                cabecera += f" ({articulo.capitulo} {articulo.capitulo_nombre or ''})".rstrip()
            cabecera += " ==="
            if articulo and articulo.texto_intro and any(h.fraccion for h in hijos):
                cabecera += f"\n{articulo.texto_intro}"
            completo = "\n\n".join([cabecera, *(_formatear(h) for h in hijos)])
            if len(completo) <= limite - usados:
                agregar(completo)
                incluidos.update({h.id: h for h in hijos})
            else:
                # Artículo demasiado largo: solo los fragmentos recuperados de ese artículo.
                propios = [r.chunk for r in resultados if r.chunk.articulo_num == num]
                partes, ids = [cabecera], []
                for c in propios:
                    candidato = "\n\n".join([*partes, _formatear(c)])
                    if len(candidato) > limite - usados:
                        break
                    partes.append(_formatear(c))
                    ids.append(c)
                if ids and agregar("\n\n".join(partes)):
                    incluidos.update({c.id: c for c in ids})

        # 2) Resto de resultados (transitorios, anexos, red vial, otros artículos) si caben.
        for r in resultados:
            if r.chunk.id in incluidos:
                continue
            if agregar(_formatear(r.chunk)):
                incluidos[r.chunk.id] = r.chunk

        relevantes = [r.chunk.id for r in resultados if r.chunk.id in incluidos][:5]
        if relevantes:
            bloques.insert(0, "Fragmentos más relevantes para la pregunta: " + ", ".join(relevantes))
        return Contexto(texto="\n\n".join(bloques), chunks=incluidos)
