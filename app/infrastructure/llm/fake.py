"""LLM falso y determinista para pruebas: cita el primer fragmento del contexto."""

from __future__ import annotations

import json
import re

_ID = re.compile(r"\[id=(?P<id>[^\]]+)\]\s*(?P<cita>[^\n]+)")
_RELEVANTES = re.compile(r"Fragmentos más relevantes para la pregunta: (?P<id>[^,\n]+)")


class FakeLLM:
    def __init__(self, respuesta_fija: str | None = None) -> None:
        self._respuesta_fija = respuesta_fija
        self.llamadas: list[tuple[str, str]] = []

    @property
    def model_name(self) -> str:
        return "fake"

    def generate(self, system_prompt: str, user_prompt: str) -> str:
        self.llamadas.append((system_prompt, user_prompt))
        if self._respuesta_fija is not None:
            return self._respuesta_fija
        rel = _RELEVANTES.search(user_prompt)
        m = None
        if rel:
            m = re.search(
                r"\[id=(?P<id>" + re.escape(rel.group("id").strip()) + r")\]\s*(?P<cita>[^\n]+)", user_prompt
            )
        m = m or _ID.search(user_prompt)
        if not m:
            return json.dumps({"encontrado": False, "respuesta": "", "citas": []})
        return json.dumps(
            {
                "encontrado": True,
                "respuesta": f"Según el {m.group('cita').strip()}, aplica lo indicado en el texto citado.",
                "citas": [m.group("id")],
            },
            ensure_ascii=False,
        )
