"""Fábrica de la aplicación FastAPI."""

from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routers import articulos, consultas, health
from app.core.config import Settings, get_settings
from app.core.container import Container
from app.core.logging import configurar_logging


def create_app(settings: Settings | None = None, container: Container | None = None) -> FastAPI:
    settings = settings or (container.settings if container else get_settings())
    configurar_logging(settings.app.log_level)

    app = FastAPI(
        title=settings.app.nombre,
        version=settings.app.version,
        description=(
            "Consulta del Reglamento de Tránsito de la Ciudad de México. "
            "El texto legal siempre proviene de la base de datos; el modelo solo resume y cita."
        ),
    )
    app.state.container = container or Container(settings)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.app.cors_origins,
        allow_methods=["GET", "POST"],
        allow_headers=["*"],
    )
    app.include_router(health.router)
    app.include_router(consultas.router)
    app.include_router(articulos.router)
    return app


app = create_app()
