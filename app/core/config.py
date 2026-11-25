"""Configuración de la aplicación.

Orden de prioridad (de mayor a menor):
1. Argumentos pasados al constructor (útil en pruebas).
2. Variables de entorno (prefijo ``RT_``, anidado con ``__``; p. ej. ``RT_LLM__BASE_URL``).
3. Archivo ``.env``.
4. Archivo YAML (``config/settings.yaml`` o el que indique ``RT_CONFIG_FILE``).
5. Valores por defecto definidos aquí.

Los secretos (API keys) van en ``.env`` o en variables de entorno, nunca en el YAML.
"""

from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, Field, SecretStr, field_validator
from pydantic_settings import (
    BaseSettings,
    PydanticBaseSettingsSource,
    SettingsConfigDict,
    YamlConfigSettingsSource,
)

BASE_DIR = Path(__file__).resolve().parents[2]
DEFAULT_CONFIG_FILE = BASE_DIR / "config" / "settings.yaml"


def _resolve(path: Path) -> Path:
    """Las rutas relativas del YAML/entorno se resuelven contra la raíz del backend."""
    path = Path(path)
    return path if path.is_absolute() else BASE_DIR / path


class AppSettings(BaseModel):
    nombre: str = "API Reglamento de Tránsito CDMX"
    version: str = "0.1.0"
    entorno: Literal["local", "dev", "prod", "test"] = "local"
    log_level: str = "INFO"
    cors_origins: list[str] = Field(default_factory=lambda: ["*"])


class DataSettings(BaseModel):
    chunks_path: Path = BASE_DIR / "data" / "reglamento_transito_cdmx_chunks.jsonl"
    articulos_path: Path = BASE_DIR / "data" / "reglamento_transito_cdmx_articulos.json"

    _resolver = field_validator("chunks_path", "articulos_path")(_resolve)


class QdrantSettings(BaseModel):
    # url (p. ej. http://qdrant:6333) o location=":memory:" para pruebas/desarrollo sin servidor.
    url: str | None = "http://localhost:6333"
    location: str | None = None
    api_key: SecretStr | None = None
    collection: str = "reglamento_transito_cdmx"
    timeout_s: float = 10.0


class EmbeddingSettings(BaseModel):
    # openai_compatible: cualquier servidor con /v1/embeddings (TEI, vLLM, Infinity, OpenAI...).
    # hashing: embeddings deterministas sin red; solo para pruebas y desarrollo sin GPU.
    provider: Literal["openai_compatible", "hashing"] = "openai_compatible"
    base_url: str = "http://localhost:8081/v1"
    model: str = "BAAI/bge-m3"
    api_key: SecretStr | None = None
    dimension: int = 1024
    batch_size: int = 32
    timeout_s: float = 60.0
    # Prefijos para modelos tipo e5 ("query: " / "passage: "). bge-m3 no los necesita.
    query_prefix: str = ""
    document_prefix: str = ""


class LLMSettings(BaseModel):
    # openai_compatible: vLLM / Ollama / TGI sirviendo Qwen3 en la GPU en la nube.
    # fake: respuestas deterministas para pruebas.
    provider: Literal["openai_compatible", "fake"] = "openai_compatible"
    base_url: str = "http://localhost:8000/v1"
    model: str = "Qwen/Qwen3-8B"
    api_key: SecretStr | None = None
    temperature: float = 0.1
    max_tokens: int = 1024
    timeout_s: float = 120.0
    max_retries: int = 2
    # Qwen3: desactiva el modo "thinking" en vLLM (chat_template_kwargs).
    disable_thinking: bool = True
    system_prompt_path: Path = BASE_DIR / "config" / "prompts" / "sistema.md"

    _resolver = field_validator("system_prompt_path")(_resolve)


class RetrievalSettings(BaseModel):
    top_k: int = 8
    dense_k: int = 20
    sparse_k: int = 20
    rrf_k: int = 60
    # Umbrales de soporte: si no hay referencia exacta a un artículo, ni similitud
    # semántica >= min_dense_score, ni cobertura de palabras clave >= min_cobertura_lexica,
    # se responde "no encontré" sin llamar al LLM. Calibrar con el modelo de embeddings real.
    min_dense_score: float = 0.45
    min_cobertura_lexica: float = 0.6
    max_exact_matches: int = 40
    # Parent document retrieval: cuántos artículos completos se mandan al LLM.
    max_parent_articles: int = 3
    max_context_chars: int = 24000


class AnswerSettings(BaseModel):
    # Si el modelo menciona un artículo que no está en el contexto, se descarta la respuesta.
    strict_citations: bool = True
    mensaje_no_encontrado: str = (
        "No encontré en el Reglamento de Tránsito de la CDMX un artículo que responda "
        "a tu pregunta. Intenta reformularla o consulta directamente el artículo."
    )


class UmaSettings(BaseModel):
    # Valor diario de la UMA (INEGI). Cambia cada 1 de febrero: actualízalo en el YAML o por entorno.
    valor_diario: float = 117.31
    vigente_desde: str = "2026-02-01"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="RT_",
        env_nested_delimiter="__",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app: AppSettings = AppSettings()
    data: DataSettings = DataSettings()
    qdrant: QdrantSettings = QdrantSettings()
    embeddings: EmbeddingSettings = EmbeddingSettings()
    llm: LLMSettings = LLMSettings()
    retrieval: RetrievalSettings = RetrievalSettings()
    answer: AnswerSettings = AnswerSettings()
    uma: UmaSettings = UmaSettings()

    @classmethod
    def settings_customise_sources(
        cls,
        settings_cls: type[BaseSettings],
        init_settings: PydanticBaseSettingsSource,
        env_settings: PydanticBaseSettingsSource,
        dotenv_settings: PydanticBaseSettingsSource,
        file_secret_settings: PydanticBaseSettingsSource,
    ) -> tuple[PydanticBaseSettingsSource, ...]:
        yaml_file = Path(os.environ.get("RT_CONFIG_FILE", DEFAULT_CONFIG_FILE))
        yaml_source = YamlConfigSettingsSource(settings_cls, yaml_file=yaml_file)
        return (init_settings, env_settings, dotenv_settings, yaml_source, file_secret_settings)


@lru_cache
def get_settings() -> Settings:
    return Settings()
