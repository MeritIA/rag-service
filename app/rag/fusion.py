"""Reciprocal Rank Fusion.

Se fusionan **posiciones**, no puntajes: un BM25 de 7.3 y un coseno de 0.81 no
estan en la misma escala, y mezclarlos con una media ponderada obliga a
calibrar pesos que se rompen al cambiar de modelo o de corpus. RRF solo
necesita el orden de cada recuperador.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Fusionado:
    indice: int
    puntaje: float
    rango_lexico: int | None  # 1 = el mejor; None = el recuperador no lo trajo
    rango_semantico: int | None


def fusionar_rrf(
    lexico: list[int],
    semantico: list[int],
    *,
    k: int = 60,
    peso_lexico: float = 1.0,
    peso_semantico: float = 1.0,
) -> list[Fusionado]:
    """Entradas: indices ordenados de mejor a peor. Salida: ordenada por puntaje RRF."""
    rl = {i: r for r, i in enumerate(lexico, 1)}
    rs = {i: r for r, i in enumerate(semantico, 1)}
    salida = [
        Fusionado(
            i,
            (peso_lexico / (k + rl[i]) if i in rl else 0.0)
            + (peso_semantico / (k + rs[i]) if i in rs else 0.0),
            rl.get(i),
            rs.get(i),
        )
        for i in rl.keys() | rs.keys()
    ]
    # Desempate por indice: el mismo corpus y la misma consulta dan siempre el mismo orden.
    return sorted(salida, key=lambda f: (-f.puntaje, f.indice))
