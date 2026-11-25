"""Línea de comandos: ``python -m app.cli ingest [--recrear]``."""

from __future__ import annotations

import argparse

from app.core.config import get_settings
from app.core.container import Container
from app.core.logging import configurar_logging


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(prog="python -m app.cli")
    sub = parser.add_subparsers(dest="comando", required=True)
    ingest = sub.add_parser("ingest", help="Indexa los chunks del reglamento en Qdrant")
    ingest.add_argument("--recrear", action="store_true", help="Borra y recrea la colección")
    args = parser.parse_args(argv)

    settings = get_settings()
    configurar_logging(settings.app.log_level)
    container = Container(settings)
    if args.comando == "ingest":
        total = container.ingestion_service.ingestar(recrear=args.recrear)
        print(f"Indexados {total} chunks en '{settings.qdrant.collection}'.")


if __name__ == "__main__":
    main()
