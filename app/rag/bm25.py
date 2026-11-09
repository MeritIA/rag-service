"""BM25 (Okapi) sin dependencias: la mitad lexica de la recuperacion hibrida."""

from __future__ import annotations

import math
from collections import Counter


class BM25:
    def __init__(self, documentos: list[list[str]], k1: float = 1.5, b: float = 0.75) -> None:
        self.k1, self.b = k1, b
        self._tf = [Counter(d) for d in documentos]
        self._largo = [len(d) for d in documentos]
        n = len(documentos)
        self._prom = (sum(self._largo) / n) if n else 0.0
        df: Counter[str] = Counter()
        for tf in self._tf:
            df.update(tf.keys())
        # IDF con +1 dentro del log: nunca negativo, aunque el termino salga en todo.
        self._idf = {t: math.log(1 + (n - f + 0.5) / (f + 0.5)) for t, f in df.items()}

    def puntuar(self, consulta: list[str]) -> list[float]:
        terminos = set(consulta)
        puntajes = [0.0] * len(self._tf)
        for i, tf in enumerate(self._tf):
            norm = self.k1 * (1 - self.b + self.b * self._largo[i] / (self._prom or 1))
            for t in terminos:
                f = tf.get(t)
                if f:
                    puntajes[i] += self._idf[t] * f * (self.k1 + 1) / (f + norm)
        return puntajes

    def buscar(self, consulta: list[str], k: int) -> list[tuple[int, float]]:
        """(indice, puntaje) de los k mejores, solo con puntaje > 0."""
        orden = sorted(enumerate(self.puntuar(consulta)), key=lambda x: -x[1])
        return [(i, s) for i, s in orden[:k] if s > 0]
