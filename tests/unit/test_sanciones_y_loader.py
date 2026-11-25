from app.domain.models import RangoUma, Sanciones, TipoChunk
from app.domain.sanciones import multas_en_pesos
from app.infrastructure.repositories.loaders import chunk_desde_registro


def test_multas_en_pesos():
    s = Sanciones(multa_uma=[RangoUma(min=10, media=15, max=20)])
    m = multas_en_pesos(s, 100.0)[0]
    assert (m.pesos_min, m.pesos_max) == (1000.0, 2000.0)
    assert multas_en_pesos(None, 100.0) == []


def test_loader_red_vial_y_extra():
    c = chunk_desde_registro(
        {
            "id": "rt-cdmx-anexo-2-via-1",
            "tipo": "anexo_red_vial",
            "cita": "Anexo 2",
            "nombre": "Circuito Interior",
            "texto": "texto",
            "texto_embedding": "emb",
            "paginas": [105],
            "alcaldias": None,
        }
    )
    assert c.tipo is TipoChunk.ANEXO_RED_VIAL
    assert c.cita == "Anexo 2 (Circuito Interior)"
    assert c.extra["nombre"] == "Circuito Interior"
