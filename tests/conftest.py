"""Fixtures compartidas. Todo corre sin red: Qdrant en memoria, embeddings por
hashing y LLM falso, inyectados en el contenedor."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app.core.config import BASE_DIR, Settings
from app.core.container import Container
from app.infrastructure.llm.fake import FakeLLM
from app.main import create_app


@pytest.fixture(scope="session")
def settings() -> Settings:
    return Settings(
        app={"entorno": "test", "log_level": "WARNING"},
        qdrant={"location": ":memory:", "url": None, "collection": "test"},
        embeddings={"provider": "hashing", "dimension": 256},
        llm={"provider": "fake", "system_prompt_path": BASE_DIR / "config/prompts/sistema.md"},
        data={
            "chunks_path": BASE_DIR / "data/reglamento_transito_cdmx_chunks.jsonl",
            "articulos_path": BASE_DIR / "data/reglamento_transito_cdmx_articulos.json",
        },
    )


@pytest.fixture(scope="session")
def container_indexado(settings: Settings) -> Container:
    c = Container(settings)
    c.ingestion_service.ingestar(recrear=True)
    return c


@pytest.fixture
def fake_llm() -> FakeLLM:
    return FakeLLM()


@pytest.fixture
def client(container_indexado: Container) -> TestClient:
    return TestClient(create_app(container=container_indexado))
