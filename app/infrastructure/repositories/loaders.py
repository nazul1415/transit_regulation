"""Lectura de los archivos generados por el extractor (JSONL de chunks y JSON de artículos)."""

from __future__ import annotations

import json
from collections.abc import Iterator
from pathlib import Path
from typing import Any

from app.domain.models import Chunk, TipoChunk

_CAMPOS_CHUNK = set(Chunk.model_fields) - {"extra"}


def chunk_desde_registro(registro: dict[str, Any]) -> Chunk:
    """Convierte un registro del JSONL en un Chunk. Los campos no modelados
    (p. ej. nombre de la vía, alcaldías, decreto) quedan en ``extra``."""
    datos = {k: v for k, v in registro.items() if k in _CAMPOS_CHUNK}
    datos["extra"] = {k: v for k, v in registro.items() if k not in _CAMPOS_CHUNK and k != "fuente"}
    datos.setdefault("texto_embedding", registro.get("texto", ""))
    if datos.get("tipo") == TipoChunk.ANEXO_RED_VIAL and registro.get("nombre"):
        datos["cita"] = f"{registro.get('cita', 'Anexo 2')} ({registro['nombre']})"
    if datos.get("paginas") is None:
        datos["paginas"] = []
    return Chunk.model_validate(datos)


def leer_chunks(path: Path) -> Iterator[Chunk]:
    with Path(path).open(encoding="utf-8") as f:
        for linea in f:
            linea = linea.strip()
            if linea:
                yield chunk_desde_registro(json.loads(linea))
