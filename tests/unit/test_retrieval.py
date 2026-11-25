def test_referencia_exacta_va_primero(container_indexado):
    rec = container_indexado.retrieval_service.buscar("¿qué dice el art. 9 fracción III?")
    primero = rec.resultados[0]
    assert primero.coincidencia_exacta
    assert (primero.chunk.articulo_num, primero.chunk.fraccion) == (9, "III")


def test_busqueda_lexica_encuentra_red_vial(container_indexado):
    rec = container_indexado.retrieval_service.buscar("Circuito Interior velocidad")
    assert any(r.chunk.extra.get("nombre") == "Circuito Interior" for r in rec.resultados)
    assert rec.cobertura_lexica >= 0.6


def test_inciso_inexistente_cae_a_fraccion(container_indexado):
    rec = container_indexado.retrieval_service.buscar("artículo 9 fracción I inciso z")
    assert rec.hubo_coincidencia_exacta
    assert rec.resultados[0].chunk.fraccion == "I"
