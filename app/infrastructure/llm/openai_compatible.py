"""LLM por API compatible con OpenAI usando LangChain (ChatOpenAI).

Apunta al servidor de inferencia en la GPU en la nube (vLLM con Qwen3, Ollama, TGI...).
"""

from __future__ import annotations

import re

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI

_THINK = re.compile(r"<think>.*?</think>", re.DOTALL)


class LLMError(RuntimeError):
    pass


class OpenAICompatibleLLM:
    def __init__(
        self,
        base_url: str,
        model: str,
        api_key: str | None = None,
        temperature: float = 0.1,
        max_tokens: int = 1024,
        timeout_s: float = 120.0,
        max_retries: int = 2,
        disable_thinking: bool = True,
        chat_model: ChatOpenAI | None = None,
    ) -> None:
        self._model = model
        # vLLM lee chat_template_kwargs; Ollama lee reasoning_effort. Cada servidor ignora el otro.
        extra_body = (
            {"chat_template_kwargs": {"enable_thinking": False}, "reasoning_effort": "none"}
            if disable_thinking
            else None
        )
        self._chat = chat_model or ChatOpenAI(
            base_url=base_url,
            model=model,
            api_key=api_key or "sin-clave",
            temperature=temperature,
            max_tokens=max_tokens,
            timeout=timeout_s,
            max_retries=max_retries,
            extra_body=extra_body,
        )

    @property
    def model_name(self) -> str:
        return self._model

    def generate(self, system_prompt: str, user_prompt: str) -> str:
        try:
            msg = self._chat.invoke([SystemMessage(system_prompt), HumanMessage(user_prompt)])
        except Exception as exc:  # noqa: BLE001 - se normaliza el error del proveedor
            raise LLMError(f"Error al llamar al LLM: {exc}") from exc
        contenido = msg.content if isinstance(msg.content, str) else str(msg.content)
        return _THINK.sub("", contenido).strip()
