from langchain_core.language_models.fake_chat_models import FakeListChatModel

from app.infrastructure.llm.openai_compatible import OpenAICompatibleLLM


def test_quita_bloque_think_de_qwen3():
    chat = FakeListChatModel(responses=['<think>razonando...</think>\n{"encontrado": false}'])
    llm = OpenAICompatibleLLM(base_url="http://gpu/v1", model="Qwen/Qwen3-8B", chat_model=chat)
    assert llm.generate("sistema", "pregunta") == '{"encontrado": false}'
