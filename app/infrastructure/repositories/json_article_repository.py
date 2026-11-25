"""Repositorio de artículos completos respaldado por el JSON del extractor.

Es la fuente de verdad del texto que se muestra al usuario. Para producción puede
sustituirse por otro adaptador (PostgreSQL, colección de Qdrant) sin tocar servicios.
"""

from __future__ import annotations

import json
from pathlib import Path

from app.domain.models import Articulo


class JsonArticleRepository:
    def __init__(self, path: Path) -> None:
        self._path = Path(path)
        self._articulos: dict[int, Articulo] | None = None

    def _cargar(self) -> dict[int, Articulo]:
        if self._articulos is None:
            datos = json.loads(self._path.read_text(encoding="utf-8"))
            self._articulos = {
                a["articulo_num"]: Articulo.model_validate(a) for a in datos.get("articulos", [])
            }
        return self._articulos

    def get(self, articulo_num: int) -> Articulo | None:
        return self._cargar().get(articulo_num)

    def list(self) -> list[Articulo]:
        return [self._cargar()[k] for k in sorted(self._cargar())]
