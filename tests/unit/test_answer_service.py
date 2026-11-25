"""Reglas de citas: el texto sale de la BD y solo se aceptan citas del contexto."""

import json

import pytest

from app.core.container import Container
from app.infrastructure.llm.fake import FakeLLM
from app.services.answer import SalidaInvalida, parsear_salida


def _servicio(container: Container, llm: FakeLLM):
    c = Container(
        container.settings,
        embeddings_override=container.embeddings,
        chunk_repo_override=container.chunk_repo,
        article_repo_override=container.article_repo,
        llm_override=llm,
    )
    return c.answer_service, c


def test_parsear_salida_tolera_bloque_de_codigo():
    out = parsear_salida('```json\n{"encontrado": true, "respuesta": "x", "citas": ["a"]}\n```')
    assert out == {"encontrado": True, "respuesta": "x", "citas": ["a"]}
    with pytest.raises(SalidaInvalida):
        parsear_salida("sin json")


def test_texto_de_la_cita_sale_de_la_bd(container_indexado):
    svc, c = _servicio(container_indexado, FakeLLM())
    r = svc.responder("¿Qué dice el artículo 14, fracción I, inciso a)?")
    assert r.encontrado
    cita = r.citas[0]
    assert cita.cita == "Art. 14, fracc. I, inciso a)"
    assert cita.texto == c.chunk_repo.get(cita.chunk_id).texto


def test_descarta_citas_inventadas(container_indexado):
    llm = FakeLLM(json.dumps({"encontrado": True, "respuesta": "Algo.", "citas": ["rt-inventado-999"]}))
    svc, _ = _servicio(container_indexado, llm)
    r = svc.responder("artículo 14 fracción I")
    assert not r.encontrado
    assert r.citas == []
    assert any("no verificables" in a for a in r.advertencias)


def test_rechaza_articulo_fuera_de_contexto(container_indexado):
    llm = FakeLLM(
        json.dumps(
            {
                "encontrado": True,
                "respuesta": "Según el Art. 99 está prohibido.",
                "citas": ["rt-cdmx-art-14-fr-i-inc-a"],
            }
        )
    )
    svc, _ = _servicio(container_indexado, llm)
    r = svc.responder("artículo 14 fracción I inciso a")
    assert not r.encontrado


def test_sin_soporte_no_llama_al_llm(container_indexado):
    llm = FakeLLM()
    svc, _ = _servicio(container_indexado, llm)
    r = svc.responder("receta del mole poblano")
    assert not r.encontrado
    assert llm.llamadas == []


def test_modo_degradado_si_falla_el_llm(container_indexado):
    class LLMRoto(FakeLLM):
        def generate(self, system_prompt, user_prompt):
            raise RuntimeError("GPU apagada")

    svc, _ = _servicio(container_indexado, LLMRoto())
    r = svc.responder("artículo 9 fracción I")
    assert r.encontrado and r.citas
    assert r.modelo is None


def test_contexto_incluye_articulo_padre(container_indexado):
    llm = FakeLLM()
    svc, _ = _servicio(container_indexado, llm)
    svc.responder("artículo 14 fracción I inciso a")
    _, prompt = llm.llamadas[0]
    # La fracción II (con la amonestación) viaja aunque solo se pidió el inciso a).
    assert "[id=rt-cdmx-art-14-fr-ii]" in prompt
