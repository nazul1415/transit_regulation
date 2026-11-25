"""Caso de uso principal: responder una pregunta con citas verificadas.

Garantías:
- El texto legal que se devuelve en ``citas`` sale de la base de datos, nunca del modelo.
- Solo se aceptan citas a fragmentos que estaban en el contexto.
- Si el modelo menciona un artículo que no estaba en el contexto (y ``strict_citations``
  está activo), o no hay soporte suficiente, se responde "no encontré".
- Si el LLM falla, se devuelven los fragmentos recuperados sin resumen (modo degradado).
"""

from __future__ import annotations

import json
import logging
import re
from pathlib import Path

from langchain_core.prompts import PromptTemplate

from app.core.config import AnswerSettings, RetrievalSettings, UmaSettings
from app.domain.models import Chunk, Cita, Respuesta
from app.domain.ports import LLMProvider
from app.domain.referencias import articulos_mencionados
from app.domain.sanciones import multas_en_pesos
from app.services.context_builder import ContextBuilder, Contexto
from app.services.retrieval import RetrievalService, orden_natural

logger = logging.getLogger(__name__)

_JSON = re.compile(r"\{.*\}", re.DOTALL)


class SalidaInvalida(ValueError):
    pass


def parsear_salida(texto: str) -> dict:
    """Extrae el objeto JSON de la salida del modelo (tolera ```json y texto alrededor)."""
    m = _JSON.search(texto)
    if not m:
        raise SalidaInvalida("La salida del modelo no contiene JSON")
    try:
        datos = json.loads(m.group(0))
    except json.JSONDecodeError as exc:
        raise SalidaInvalida(f"JSON inválido: {exc}") from exc
    if not isinstance(datos, dict):
        raise SalidaInvalida("La salida del modelo no es un objeto")
    citas = datos.get("citas") or []
    if not isinstance(citas, list):
        citas = [citas]
    return {
        "encontrado": bool(datos.get("encontrado", bool(citas))),
        "respuesta": str(datos.get("respuesta") or "").strip(),
        "citas": [str(c).strip() for c in citas],
    }


class AnswerService:
    def __init__(
        self,
        retrieval: RetrievalService,
        context_builder: ContextBuilder,
        llm: LLMProvider,
        system_prompt: str,
        user_template: PromptTemplate,
        retrieval_cfg: RetrievalSettings,
        answer_cfg: AnswerSettings,
        uma_cfg: UmaSettings,
    ) -> None:
        self._retrieval = retrieval
        self._context = context_builder
        self._llm = llm
        self._system_prompt = system_prompt
        self._user_template = user_template
        self._retrieval_cfg = retrieval_cfg
        self._answer_cfg = answer_cfg
        self._uma = uma_cfg

    @classmethod
    def cargar_prompts(cls, system_path: Path) -> tuple[str, PromptTemplate]:
        system_prompt = Path(system_path).read_text(encoding="utf-8").strip()
        plantilla = (Path(system_path).parent / "consulta.md").read_text(encoding="utf-8")
        return system_prompt, PromptTemplate.from_template(plantilla)

    # ------------------------------------------------------------------
    def responder(self, pregunta: str, top_k: int | None = None) -> Respuesta:
        recuperacion = self._retrieval.buscar(pregunta, top_k)
        if not recuperacion.tiene_soporte(
            self._retrieval_cfg.min_dense_score, self._retrieval_cfg.min_cobertura_lexica
        ):
            return self._no_encontrado(pregunta, "Sin fragmentos relevantes en la búsqueda.")

        contexto = self._context.construir(recuperacion.resultados)
        if not contexto.chunks:
            return self._no_encontrado(pregunta, "El contexto quedó vacío.")

        prompt = self._user_template.format(contexto=contexto.texto, pregunta=pregunta)
        try:
            salida = parsear_salida(self._llm.generate(self._system_prompt, prompt))
        except Exception as exc:  # noqa: BLE001 - cualquier fallo del LLM degrada, no rompe
            logger.warning("LLM no disponible o salida inválida: %s", exc)
            return self._degradado(pregunta, recuperacion.resultados[:3], contexto)

        return self._validar(pregunta, salida, contexto)

    # ------------------------------------------------------------------
    def _validar(self, pregunta: str, salida: dict, contexto: Contexto) -> Respuesta:
        advertencias: list[str] = []
        validas = [cid for cid in dict.fromkeys(salida["citas"]) if cid in contexto.chunks]
        invalidas = [cid for cid in salida["citas"] if cid not in contexto.chunks]
        if invalidas:
            advertencias.append(f"Se descartaron citas no verificables: {', '.join(invalidas)}")

        if not salida["encontrado"] or not validas or not salida["respuesta"]:
            return self._no_encontrado(pregunta, *advertencias)

        fuera = articulos_mencionados(salida["respuesta"]) - contexto.articulos
        if fuera:
            msg = "La respuesta mencionaba artículos que no están en el contexto: " + ", ".join(
                str(n) for n in sorted(fuera)
            )
            if self._answer_cfg.strict_citations:
                logger.warning("%s. Pregunta: %s", msg, pregunta)
                return self._no_encontrado(pregunta, msg)
            advertencias.append(msg)

        chunks = sorted((contexto.chunks[c] for c in validas), key=orden_natural)
        return Respuesta(
            pregunta=pregunta,
            encontrado=True,
            respuesta=salida["respuesta"],
            citas=[self._a_cita(c) for c in chunks],
            advertencias=advertencias,
            uma_valor_diario=self._uma.valor_diario,
            modelo=self._llm.model_name,
        )

    def _a_cita(self, chunk: Chunk) -> Cita:
        return Cita(
            chunk_id=chunk.id,
            cita=chunk.cita,
            texto=chunk.texto,
            articulo_num=chunk.articulo_num,
            fraccion=chunk.fraccion,
            inciso=chunk.inciso,
            paginas=chunk.paginas,
            ultima_reforma=chunk.ultima_reforma,
            sanciones=chunk.sanciones,
            multas_en_pesos=multas_en_pesos(chunk.sanciones, self._uma.valor_diario),
        )

    def _no_encontrado(self, pregunta: str, *advertencias: str) -> Respuesta:
        return Respuesta(
            pregunta=pregunta,
            encontrado=False,
            respuesta=self._answer_cfg.mensaje_no_encontrado,
            advertencias=[a for a in advertencias if a],
            uma_valor_diario=self._uma.valor_diario,
            modelo=self._llm.model_name,
        )

    def _degradado(self, pregunta: str, resultados, contexto: Contexto) -> Respuesta:
        chunks = [r.chunk for r in resultados]
        return Respuesta(
            pregunta=pregunta,
            encontrado=True,
            respuesta=(
                "No pude generar el resumen en este momento. "
                "Estos son los fragmentos del reglamento más relacionados con tu pregunta."
            ),
            citas=[self._a_cita(c) for c in chunks],
            advertencias=["Respuesta sin resumen del modelo (LLM no disponible)."],
            uma_valor_diario=self._uma.valor_diario,
            modelo=None,
        )
