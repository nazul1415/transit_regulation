"""Raíz de composición: único lugar donde se eligen e instancian los adaptadores.

Los servicios reciben sus dependencias por constructor; FastAPI las obtiene del
contenedor con ``Depends`` (ver ``app/api/dependencies.py``). En pruebas se arma
un contenedor con adaptadores falsos o se usan ``dependency_overrides``.
"""

from __future__ import annotations

from dataclasses import dataclass
from functools import cached_property

from app.core.config import Settings
from app.domain.ports import (
    ArticleRepository,
    ChunkRepository,
    EmbeddingProvider,
    LLMProvider,
    SparseEncoder,
)
from app.infrastructure.embeddings.factory import crear_embeddings
from app.infrastructure.embeddings.sparse import HashingBM25Encoder
from app.infrastructure.llm.factory import crear_llm
from app.infrastructure.repositories.json_article_repository import JsonArticleRepository
from app.infrastructure.repositories.loaders import leer_chunks
from app.infrastructure.vectorstore.qdrant_repository import QdrantChunkRepository, crear_cliente_qdrant
from app.services.answer import AnswerService
from app.services.articulos import ArticleService
from app.services.context_builder import ContextBuilder
from app.services.ingestion import IngestionService
from app.services.retrieval import RetrievalService


@dataclass
class Container:
    settings: Settings
    # Permiten inyectar adaptadores alternos (pruebas, otros proveedores).
    embeddings_override: EmbeddingProvider | None = None
    llm_override: LLMProvider | None = None
    chunk_repo_override: ChunkRepository | None = None
    article_repo_override: ArticleRepository | None = None

    # -- adaptadores ------------------------------------------------------
    @cached_property
    def embeddings(self) -> EmbeddingProvider:
        return self.embeddings_override or crear_embeddings(self.settings.embeddings)

    @cached_property
    def sparse(self) -> SparseEncoder:
        return HashingBM25Encoder()

    @cached_property
    def llm(self) -> LLMProvider:
        return self.llm_override or crear_llm(self.settings.llm)

    @cached_property
    def chunk_repo(self) -> ChunkRepository:
        if self.chunk_repo_override:
            return self.chunk_repo_override
        q = self.settings.qdrant
        cliente = crear_cliente_qdrant(
            url=q.url,
            location=q.location,
            api_key=q.api_key.get_secret_value() if q.api_key else None,
            timeout_s=q.timeout_s,
        )
        return QdrantChunkRepository(cliente, q.collection)

    @cached_property
    def article_repo(self) -> ArticleRepository:
        return self.article_repo_override or JsonArticleRepository(self.settings.data.articulos_path)

    # -- servicios --------------------------------------------------------
    @cached_property
    def retrieval_service(self) -> RetrievalService:
        return RetrievalService(self.chunk_repo, self.embeddings, self.sparse, self.settings.retrieval)

    @cached_property
    def context_builder(self) -> ContextBuilder:
        return ContextBuilder(self.chunk_repo, self.article_repo, self.settings.retrieval)

    @cached_property
    def answer_service(self) -> AnswerService:
        system_prompt, plantilla = AnswerService.cargar_prompts(self.settings.llm.system_prompt_path)
        return AnswerService(
            retrieval=self.retrieval_service,
            context_builder=self.context_builder,
            llm=self.llm,
            system_prompt=system_prompt,
            user_template=plantilla,
            retrieval_cfg=self.settings.retrieval,
            answer_cfg=self.settings.answer,
            uma_cfg=self.settings.uma,
        )

    @cached_property
    def article_service(self) -> ArticleService:
        return ArticleService(self.article_repo, self.chunk_repo, self.settings.uma)

    @cached_property
    def ingestion_service(self) -> IngestionService:
        ruta = self.settings.data.chunks_path
        return IngestionService(
            fuente=lambda: leer_chunks(ruta),
            embeddings=self.embeddings,
            sparse=self.sparse,
            repo=self.chunk_repo,
        )
