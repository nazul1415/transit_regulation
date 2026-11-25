"""Entidades del dominio. No dependen de FastAPI, Qdrant ni LangChain."""

from __future__ import annotations

from enum import StrEnum
from typing import Any

from pydantic import BaseModel, Field


class TipoChunk(StrEnum):
    ARTICULO = "articulo"
    TRANSITORIO = "transitorio"
    ANEXO = "anexo"
    ANEXO_RED_VIAL = "anexo_red_vial"


class RangoUma(BaseModel):
    min: float
    media: float | None = None
    max: float


class Sanciones(BaseModel):
    multa_uma: list[RangoUma] = Field(default_factory=list)
    puntos: list[int] = Field(default_factory=list)
    deposito_vehicular: bool = False
    arresto: bool = False
    amonestacion: bool = False


class Chunk(BaseModel):
    """Unidad mínima indexada: una fracción, un inciso, un artículo sin fracciones,
    un bloque de transitorios, de anexo o una vía del Anexo 2."""

    id: str
    tipo: TipoChunk
    cita: str
    texto: str
    texto_embedding: str
    documento: str = "Reglamento de Tránsito de la Ciudad de México"
    ultima_reforma: str | None = None
    articulo: str | None = None
    articulo_num: int | None = None
    fraccion: str | None = None
    inciso: str | None = None
    titulo: str | None = None
    titulo_nombre: str | None = None
    capitulo: str | None = None
    capitulo_nombre: str | None = None
    derogado: bool = False
    paginas: list[int] = Field(default_factory=list)
    sanciones: Sanciones | None = None
    anexo: int | None = None
    extra: dict[str, Any] = Field(default_factory=dict)


class Inciso(BaseModel):
    inciso: str
    texto: str
    paginas: list[int] = Field(default_factory=list)


class Fraccion(BaseModel):
    fraccion: str
    texto: str
    incisos: list[Inciso] = Field(default_factory=list)
    paginas: list[int] = Field(default_factory=list)


class Articulo(BaseModel):
    """Artículo completo (documento padre)."""

    id: str
    articulo: str
    articulo_num: int
    texto: str
    texto_intro: str | None = None
    titulo: str | None = None
    titulo_nombre: str | None = None
    capitulo: str | None = None
    capitulo_nombre: str | None = None
    derogado: bool = False
    paginas: list[int] = Field(default_factory=list)
    fracciones: list[Fraccion] = Field(default_factory=list)
    sanciones: Sanciones | None = None

    @property
    def cita(self) -> str:
        return f"Art. {self.articulo}"


class ReferenciaLegal(BaseModel):
    """Referencia explícita a un artículo dentro de una pregunta o respuesta."""

    articulo_num: int
    fraccion: str | None = None
    inciso: str | None = None


class ResultadoBusqueda(BaseModel):
    chunk: Chunk
    score: float
    score_denso: float | None = None
    score_lexico: float | None = None
    coincidencia_exacta: bool = False


class MultaEnPesos(BaseModel):
    uma_min: float
    uma_max: float
    pesos_min: float
    pesos_max: float


class Cita(BaseModel):
    """Lo que la app muestra como respaldo. El texto SIEMPRE viene de la base de datos."""

    chunk_id: str
    cita: str
    texto: str
    articulo_num: int | None = None
    fraccion: str | None = None
    inciso: str | None = None
    paginas: list[int] = Field(default_factory=list)
    ultima_reforma: str | None = None
    sanciones: Sanciones | None = None
    multas_en_pesos: list[MultaEnPesos] = Field(default_factory=list)


class Respuesta(BaseModel):
    pregunta: str
    encontrado: bool
    respuesta: str
    citas: list[Cita] = Field(default_factory=list)
    advertencias: list[str] = Field(default_factory=list)
    uma_valor_diario: float | None = None
    modelo: str | None = None
