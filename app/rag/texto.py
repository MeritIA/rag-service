"""Normalizacion y tokenizacion de texto en espanol (con jerga tecnica en ingles)."""

from __future__ import annotations

import re
import unicodedata

_STOP = frozenset(
    """
    a al algo algun alguna ante con contra cual cuando de del desde donde el ella ellos en entre era
    es esa ese eso esta este esto fue ha han hay la las le les lo los mas me mi muy no nos o para pero
    por que se sea ser si sin sobre son su sus te tu tus un una uno unos y ya yo como cada tiene tener
    the of to and is in it for on with that this are be as at
    """.split()
)

_SUFIJOS = (
    "amientos", "imientos", "amiento", "imiento", "aciones", "uciones", "acion", "ucion",
    "mente", "adores", "adora", "ador", "ables", "ibles", "able", "ible", "ando", "iendo",
    "ados", "adas", "idos", "idas", "ado", "ada", "ido", "ida", "ar", "er", "ir", "es", "s",
)  # fmt: skip

_PALABRA = re.compile(r"[a-z0-9_+#]+")
_INVISIBLES = re.compile(r"[\u0000-\u001f\u007f-\u009f​-‏ -‮]")


def sin_acentos(texto: str) -> str:
    return "".join(c for c in unicodedata.normalize("NFKD", texto) if not unicodedata.combining(c))


def _raiz(palabra: str) -> str:
    # Un stemming ligero basta: solo hace falta que "complejidad" y "complejidades",
    # o "validar" y "validacion", caigan en el mismo cajon para BM25.
    for s in _SUFIJOS:
        if palabra.endswith(s) and len(palabra) - len(s) >= 4:
            return palabra[: -len(s)]
    return palabra


def tokenizar(texto: str) -> list[str]:
    plano = sin_acentos(unicodedata.normalize("NFKC", texto).lower())
    return [_raiz(p) for p in _PALABRA.findall(plano) if len(p) > 1 and p not in _STOP]


def condensar(texto: str, maximo: int) -> str:
    """Una sola linea, sin caracteres de control ni invisibles, cortada a `maximo`."""
    plano = re.sub(r"\s+", " ", _INVISIBLES.sub(" ", texto)).strip()
    return plano if len(plano) <= maximo else plano[: maximo - 1] + "…"
