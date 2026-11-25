import pytest

from app.domain.referencias import extraer_referencias, normalizar, romano_a_entero, tokenizar


@pytest.mark.parametrize(
    "texto,esperado",
    [
        ("¿Qué dice el artículo 14?", [(14, None, None)]),
        ("art. 14, fracción I, inciso a)", [(14, "I", "a")]),
        ("Art 4 fracc. XLVIII Ter", [(4, "XLVIII Ter", None)]),
        ("articulo 9 fraccion iii", [(9, "III", None)]),
        ("Arts. 5 y 6", [(5, None, None)]),
        ("no menciona nada", []),
    ],
)
def test_extraer_referencias(texto, esperado):
    refs = [(r.articulo_num, r.fraccion, r.inciso) for r in extraer_referencias(texto)]
    assert refs == esperado


def test_romanos():
    assert [romano_a_entero(r) for r in ["I", "IV", "IX", "XLIX", "LXX"]] == [1, 4, 9, 49, 70]


def test_normalizar_conserva_enie():
    assert normalizar("Peatón AÑO Vehículo") == "peaton año vehiculo"


def test_tokenizar_quita_stopwords_y_plurales():
    assert tokenizar("Las bicicletas en los carriles") == ["bicicleta", "carril"]
