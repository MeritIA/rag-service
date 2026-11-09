"""Vectorizadores: la mitad semantica de la recuperacion hibrida.

Misma idea que `ProveedorDeModelo` del ai-service: el resto del codigo solo
conoce `Vectorizador`; cual hay detras lo decide `EMBEDDINGS`.
"""

from __future__ import annotations

import hashlib
from typing import Literal, Protocol

import numpy as np

from .texto import tokenizar

Tipo = Literal["documento", "consulta"]


class Vectorizador(Protocol):
    nombre: str

    def vectorizar(self, textos: list[str], tipo: Tipo) -> np.ndarray:
        """Matriz (n, d) con filas normalizadas (norma L2 = 1)."""
        ...


def _normalizar(m: np.ndarray) -> np.ndarray:
    norma = np.linalg.norm(m, axis=1, keepdims=True)
    return m / np.where(norma == 0, 1, norma)


class VectorizadorHash:
    """Bolsa de palabras y bigramas con hashing a dimension fija.

    No es semantico de verdad (no sabe que "lento" y "ineficiente" se parecen):
    existe para desarrollar y probar sin red ni API key. Esta prohibido en
    produccion.
    """

    def __init__(self, dimension: int = 512) -> None:
        self.nombre = f"hash-{dimension}"
        self._d = dimension

    def vectorizar(self, textos: list[str], tipo: Tipo) -> np.ndarray:
        m = np.zeros((len(textos), self._d), dtype=np.float32)
        for i, t in enumerate(textos):
            toks = tokenizar(t)
            for g in toks + [f"{a}_{b}" for a, b in zip(toks, toks[1:])]:
                h = int.from_bytes(hashlib.blake2b(g.encode(), digest_size=8).digest(), "big")
                m[i, h % self._d] += 1.0 if (h >> 63) == 0 else -1.0
        return _normalizar(m)


class VectorizadorGemini:
    def __init__(self, api_key: str, modelo: str, dimension: int, tiempo_maximo_ms: int) -> None:
        from google import genai
        from google.genai import types

        self._types = types
        self._cliente = genai.Client(
            api_key=api_key, http_options=types.HttpOptions(timeout=tiempo_maximo_ms)
        )
        self._modelo, self._d = modelo, dimension
        self.nombre = f"gemini/{modelo}-{dimension}"

    def vectorizar(self, textos: list[str], tipo: Tipo) -> np.ndarray:
        # RETRIEVAL_DOCUMENT / RETRIEVAL_QUERY: el modelo vectoriza distinto la
        # pregunta y el pasaje, y mejora la recuperacion respecto a usar uno solo.
        config = self._types.EmbedContentConfig(
            task_type="RETRIEVAL_DOCUMENT" if tipo == "documento" else "RETRIEVAL_QUERY",
            output_dimensionality=self._d,
        )
        filas: list[list[float]] = []
        for i in range(0, len(textos), 100):  # tope de la API por llamada
            r = self._cliente.models.embed_content(
                model=self._modelo, contents=textos[i : i + 100], config=config
            )
            filas.extend(e.values for e in (r.embeddings or []) if e.values is not None)
        if len(filas) != len(textos):
            raise RuntimeError("Gemini devolvio menos vectores que textos.")
        # Con dimension reducida (<3072) los vectores no vienen normalizados.
        return _normalizar(np.asarray(filas, dtype=np.float32))
