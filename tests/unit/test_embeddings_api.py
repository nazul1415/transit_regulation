"""El adaptador de embeddings habla el protocolo /v1/embeddings (TEI, vLLM, OpenAI)."""

import httpx
import pytest

from app.infrastructure.embeddings.openai_compatible import EmbeddingError, OpenAICompatibleEmbeddings


def _cliente(dim: int) -> httpx.Client:
    def handler(request: httpx.Request) -> httpx.Response:
        import json

        cuerpo = json.loads(request.content)
        assert cuerpo["model"] == "BAAI/bge-m3"
        data = [{"index": i, "embedding": [0.1] * dim} for i, _ in enumerate(cuerpo["input"])]
        return httpx.Response(200, json={"data": list(reversed(data))})

    return httpx.Client(base_url="http://emb/v1", transport=httpx.MockTransport(handler))


def test_embeddings_por_lotes():
    emb = OpenAICompatibleEmbeddings("http://emb/v1", "BAAI/bge-m3", 4, batch_size=2, client=_cliente(4))
    assert len(emb.embed_documents(["a", "b", "c"])) == 3
    assert len(emb.embed_query("hola")) == 4


def test_dimension_incorrecta():
    emb = OpenAICompatibleEmbeddings("http://emb/v1", "BAAI/bge-m3", 1024, client=_cliente(4))
    with pytest.raises(EmbeddingError):
        emb.embed_query("hola")
