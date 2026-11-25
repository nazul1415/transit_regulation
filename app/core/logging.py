import logging


def configurar_logging(nivel: str = "INFO") -> None:
    logging.basicConfig(
        level=nivel.upper(),
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )
