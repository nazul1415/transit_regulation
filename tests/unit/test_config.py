from app.core.config import BASE_DIR, Settings


def test_yaml_y_entorno(monkeypatch):
    monkeypatch.setenv("RT_LLM__BASE_URL", "https://gpu.ejemplo/v1")
    monkeypatch.setenv("RT_LLM__API_KEY", "secreto")
    s = Settings()
    assert s.llm.base_url == "https://gpu.ejemplo/v1"  # entorno gana al YAML
    assert s.llm.model == "Qwen/Qwen3-8B"  # viene del YAML
    assert s.llm.api_key.get_secret_value() == "secreto"
    assert "secreto" not in repr(s)
    assert s.data.chunks_path == BASE_DIR / "data/reglamento_transito_cdmx_chunks.jsonl"


def test_fabricas_por_configuracion():
    from app.infrastructure.embeddings.factory import crear_embeddings
    from app.infrastructure.embeddings.hashing import HashingEmbeddings
    from app.infrastructure.llm.factory import crear_llm
    from app.infrastructure.llm.openai_compatible import OpenAICompatibleLLM

    s = Settings(embeddings={"provider": "hashing", "dimension": 64}, llm={"provider": "openai_compatible"})
    assert isinstance(crear_embeddings(s.embeddings), HashingEmbeddings)
    assert isinstance(crear_llm(s.llm), OpenAICompatibleLLM)
