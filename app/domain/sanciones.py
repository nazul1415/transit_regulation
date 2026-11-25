"""Cálculo de multas en pesos a partir de las UMA del reglamento."""

from __future__ import annotations

from app.domain.models import MultaEnPesos, Sanciones


def multas_en_pesos(sanciones: Sanciones | None, uma_valor_diario: float) -> list[MultaEnPesos]:
    if not sanciones or not sanciones.multa_uma:
        return []
    return [
        MultaEnPesos(
            uma_min=r.min,
            uma_max=r.max,
            pesos_min=round(r.min * uma_valor_diario, 2),
            pesos_max=round(r.max * uma_valor_diario, 2),
        )
        for r in sanciones.multa_uma
    ]
