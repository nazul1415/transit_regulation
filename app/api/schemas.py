"""Esquemas de entrada/salida de la API (separados de las entidades del dominio)."""

from __future__ import annotations

from pydantic import BaseModel, Field

from app.domain.models import Fraccion, MultaEnPesos, Sanciones


class ConsultaRequest(BaseModel):
    pregunta: str = Field(
        min_length=3, max_length=1000, examples=["¿Puedo circular en bicicleta por el carril del Metrobús?"]
    )
    top_k: int | None = Field(default=None, ge=1, le=20)


class FragmentoOut(BaseModel):
    chunk_id: str
    cita: str
    texto: str
    tipo: str
    articulo_num: int | None = None
    fraccion: str | None = None
    inciso: str | None = None
    paginas: list[int] = []
    sanciones: Sanciones | None = None
    multas_en_pesos: list[MultaEnPesos] = []
    score: float | None = None
    coincidencia_exacta: bool = False


class BusquedaResponse(BaseModel):
    pregunta: str
    resultados: list[FragmentoOut]


class ArticuloResumenOut(BaseModel):
    articulo_num: int
    cita: str
    titulo: str | None
    capitulo: str | None
    capitulo_nombre: str | None
    derogado: bool


class ArticuloOut(ArticuloResumenOut):
    texto: str
    texto_intro: str | None
    paginas: list[int]
    fracciones: list[Fraccion]
    sanciones: Sanciones | None
    ultima_reforma: str | None = None


class HealthResponse(BaseModel):
    estado: str
    qdrant: bool
    chunks_indexados: int
    version: str
