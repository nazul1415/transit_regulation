def test_health(client):
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json()["chunks_indexados"] == 768


def test_consulta(client):
    r = client.post("/v1/consultas", json={"pregunta": "¿Qué dice el artículo 14, fracción I, inciso a)?"})
    assert r.status_code == 200
    body = r.json()
    assert body["encontrado"] is True
    assert body["citas"][0]["cita"] == "Art. 14, fracc. I, inciso a)"


def test_consulta_valida_entrada(client):
    assert client.post("/v1/consultas", json={"pregunta": "a"}).status_code == 422


def test_articulo_completo_y_404(client):
    r = client.get("/v1/articulos/14")
    assert r.status_code == 200 and r.json()["cita"] == "Art. 14"
    assert client.get("/v1/articulos/999").status_code == 404


def test_fragmentos_con_multas_en_pesos(client):
    r = client.get("/v1/articulos/6/fragmentos", params={"fraccion": "V"})
    assert r.status_code == 200
    frag = r.json()[0]
    assert frag["multas_en_pesos"][0]["uma_min"] == 10


def test_busqueda(client):
    r = client.get("/v1/busqueda", params={"q": "Periférico"})
    assert r.status_code == 200 and r.json()["resultados"]


def test_listado(client):
    assert len(client.get("/v1/articulos").json()) == 70
