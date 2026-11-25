"""Proveedores de dependencias para FastAPI. Los routers solo conocen servicios."""

from __future__ import annotations

from typing import Annotated

from fastapi import Depends, Request

from app.core.container import Container
from app.services.answer import AnswerService
from app.services.articulos import ArticleService
from app.services.retrieval import RetrievalService


def get_container(request: Request) -> Container:
    return request.app.state.container


ContainerDep = Annotated[Container, Depends(get_container)]


def get_answer_service(container: ContainerDep) -> AnswerService:
    return container.answer_service


def get_retrieval_service(container: ContainerDep) -> RetrievalService:
    return container.retrieval_service


def get_article_service(container: ContainerDep) -> ArticleService:
    return container.article_service


AnswerServiceDep = Annotated[AnswerService, Depends(get_answer_service)]
RetrievalServiceDep = Annotated[RetrievalService, Depends(get_retrieval_service)]
ArticleServiceDep = Annotated[ArticleService, Depends(get_article_service)]
